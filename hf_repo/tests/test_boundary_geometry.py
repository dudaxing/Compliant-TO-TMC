"""Analytic Q1 boundary examples; no FE solver or precision reference."""
import numpy as np
import pytest

from hf_eval.boundary_geometry import boundary_distances, exposed_q1_edges, measure_native_workpiece_boundaries


@pytest.mark.parametrize("a,b,expected,kind", [
    ([[0., 0.], [2., 0.]], [[0., 3.], [2., 3.]], 3., None),
    ([[0., 0.], [2., 2.]], [[0., 2.], [2., 0.]], 0., "crossing"),
    ([[0., 0.], [1., 0.]], [[1., 0.], [2., 1.]], 0., "endpoint_touch"),
    ([[0., 0.], [3., 0.]], [[1., 0.], [2., 0.]], 0., "collinear_overlap"),
    ([[1., 1.], [1., 1.]], [[0., 1.], [2., 1.]], 0., "degenerate_touch"),
    ([[0., 1.], [2., 1.]], [[1., 1.], [1., 1.]], 0., "degenerate_touch"),
    ([[1., 1.], [1., 1.]], [[1., 1.], [1., 1.]], 0., "degenerate_touch"),
    ([[1., 2.], [1., 2.]], [[0., 0.], [2., 0.]], 2., None),
])
def test_known_segment_pair(a, b, expected, kind):
    points = np.asarray(a+b)
    result = boundary_distances(points, [[0, 1]], [[2, 3]])
    assert result["minimum_boundary_distance_mm"] == pytest.approx(expected, abs=1e-14)
    pair = result["closest_pair"]
    assert np.linalg.norm(np.asarray(pair["mechanism_point_mm"])-pair["workpiece_point_mm"]) == pytest.approx(expected, abs=1e-14)
    assert result["intersects"] is (kind is not None)
    assert not result["roundoff_near_touch"]
    if kind is not None:
        assert result["intersections"][0]["kind"] == kind


def test_shared_cell_edges_and_symmetry_cut_are_not_exterior_edges():
    coordinates = np.array([[0., 0.], [1., 0.], [2., 0.], [0., 1.], [1., 1.], [2., 1.]])
    connectivity = np.array([[0, 1, 4, 3], [1, 2, 5, 4]])
    edges = exposed_q1_edges(connectivity, [0, 1], coordinates, symmetry_y_mm=1.)
    assert set(map(tuple, edges.tolist())) == {(0, 1), (1, 2), (0, 3), (2, 5)}


@pytest.mark.parametrize("second", [
    [[0., 1e-15], [2., 1e-15]],
    [[1., 1e-15], [1., 1e-15]],
])
def test_positive_distance_below_roundoff_tolerance_is_not_an_intersection(second):
    points = np.array([[0., 0.], [2., 0.]]+second)
    result = boundary_distances(points, [[0, 1]], [[2, 3]])
    assert 0. < result["minimum_boundary_distance_mm"] < result["roundoff_tolerance_mm"]
    assert result["minimum_boundary_distance_mm"] == pytest.approx(1e-15, rel=1e-15, abs=0.)
    assert not result["intersects"]
    assert result["roundoff_near_touch"]
    assert result["intersections"][0]["kind"] == "roundoff_near_touch"


def test_small_angle_crossing_keeps_one_actual_intersection_point():
    epsilon = np.finfo(float).eps
    points = np.array([[0., 0.], [2., 0.], [0., -epsilon], [2., epsilon]])
    result = boundary_distances(points, [[0, 1]], [[2, 3]])
    assert result["minimum_boundary_distance_mm"] == 0.
    assert result["intersects"] and not result["roundoff_near_touch"]
    hit = result["intersections"][0]
    assert hit["kind"] == "crossing"
    np.testing.assert_array_equal(hit["intersection_point_mm"], [1., 0.])
    assert "intersection_segment_mm" not in hit


def test_native_distances_use_saved_lift_plus_fluctuation_and_fixed_square_sides():
    coordinates = np.array([[0., 0.], [1., 0.], [1., 1.], [0., 1.],
                            [0., 3.], [1., 3.], [1., 4.], [0., 4.]])
    model = dict(coordinates=coordinates, connectivity=np.array([[0, 1, 2, 3], [4, 5, 6, 7]]),
                 solid=np.array([True, False]), workpiece_cells=np.array([1]))
    metadata = dict(element_node_order=["BL", "BR", "TR", "TL"],
        model_extent=dict(kind="lower_half", symmetry_axis=dict(normal=[0., 1.], offset_mm=4.)),
        task=dict(workpiece=dict(kind="fixed_rigid", shape="square")))
    lift, fluctuation = np.zeros((8, 2)), np.zeros((8, 2))
    lift[:4, 1] = .2
    fluctuation[:4, 1] = .3
    result = measure_native_workpiece_boundaries(model, metadata, lift.ravel(), fluctuation.ravel())
    assert result["groups"]["bottom"]["minimum_boundary_distance_mm"] == pytest.approx(1.5)
    assert result["groups"]["all_exposed"]["minimum_boundary_distance_mm"] == pytest.approx(1.5)
    assert len(result["workpiece_edges"]) == 3
    assert result["force_calls"] == result["tangent_calls"] == result["solver_calls"] == result["HP_calls"] == 0
    assert not result["contact_or_clamping_qualification"]


def test_circle_measures_staircase_edges_instead_of_an_analytic_fit():
    coordinates = np.array([[0., 0.], [1., 0.], [1., 1.], [0., 1.],
                            [0., 3.], [1., 3.], [1., 4.], [0., 4.]])
    model = dict(coordinates=coordinates, connectivity=np.array([[0, 1, 2, 3], [4, 5, 6, 7]]),
                 solid=np.array([True, False]), workpiece_cells=np.array([1]))
    metadata = dict(element_node_order=["BL", "BR", "TR", "TL"],
        model_extent=dict(kind="lower_half", symmetry_axis=dict(normal=[0., 1.], offset_mm=4.)),
        task=dict(workpiece=dict(kind="fixed_rigid", shape="circle")))
    result = measure_native_workpiece_boundaries(model, metadata, np.zeros(16), np.zeros(16))
    assert set(result["groups"]) == {"all_exposed"}
    assert len(result["workpiece_edges"]) == 3
    assert result["groups"]["all_exposed"]["minimum_boundary_distance_mm"] == 2.
    assert result["circle_representation"] == "native cell staircase; no analytic circle fit"
