"""Analytic native Q1 region/ray examples; no FE or constitutive evaluator."""
import math

import numpy as np
import pytest

from hf_eval.native_region_geometry import (
    finite_face_ray_hit, measure_native_workpiece_regions, region_overlap,
)


def box(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def regions(mechanism, body):
    polygons = mechanism + body
    xy = np.asarray(polygons, dtype=float).reshape(-1, 2)
    conn = np.arange(len(xy), dtype=np.int64).reshape(-1, 4)
    return region_overlap(xy, conn, np.arange(len(mechanism)),
                          np.arange(len(mechanism), len(polygons)))


@pytest.mark.parametrize("face,normal,rectangle", [
    ([(4., 4.), (8., 4.)], [0., -1.], box(4., 0., 8., 2.)),
    ([(4., 4.), (4., 8.)], [-1., 0.], box(0., 4., 2., 8.)),
])
def test_aligned_finite_body_faces_have_two_mm_clearance(face, normal, rectangle):
    xy = np.asarray(rectangle)
    edges = np.asarray([[0, 1], [1, 2], [2, 3], [3, 0]])
    result = finite_face_ray_hit(xy, edges, *np.asarray(face), np.asarray(normal))
    assert result["minimum_first_ray_hit_mm"] == pytest.approx(2., abs=1e-14)
    hit = result["closest_hit"]
    assert np.asarray(hit["edge_point_mm"]) - np.asarray(hit["face_point_mm"]) == pytest.approx(
        2. * np.asarray(normal), abs=1e-14)


def test_finite_face_rejects_remote_edge_and_retains_an_exact_corner():
    xy = np.asarray([(3., -1.), (4., -1.), (2., -1.), (3., -2.)])
    face = np.asarray([(0., 1.), (2., 1.)])
    normal = np.asarray([0., -1.])
    nohit = finite_face_ray_hit(xy, np.asarray([[0, 1]]), *face, normal)
    assert nohit["minimum_first_ray_hit_mm"] is None
    assert nohit["closest_hit"] is None
    corner = finite_face_ray_hit(xy, np.asarray([[2, 3]]), *face, normal)
    assert corner["minimum_first_ray_hit_mm"] == pytest.approx(2., abs=1e-14)
    assert corner["closest_hit"]["face_parameter"] == 1.
    assert corner["closest_hit"]["corner_hit"] is True
    assert corner["closest_hit"]["face_point_mm"] == pytest.approx([2., 1.])
    assert corner["closest_hit"]["edge_point_mm"] == pytest.approx([2., -1.])


def test_rotated_face_ray_uses_its_normal_not_an_axis_gap():
    xy = np.asarray([(1., -1.), (3., 1.)])
    normal = np.asarray([1., -1.]) / math.sqrt(2.)
    result = finite_face_ray_hit(xy, np.asarray([[0, 1]]),
                                 np.asarray([0., 0.]), np.asarray([2., 2.]), normal)
    assert result["minimum_first_ray_hit_mm"] == pytest.approx(math.sqrt(2.), abs=2e-14)
    assert np.asarray(result["closest_hit"]["edge_point_mm"]) - np.asarray(
        result["closest_hit"]["face_point_mm"]) == pytest.approx([1., -1.], abs=2e-14)


@pytest.mark.parametrize("mechanism,body,overlap", [
    ([box(0., 0., 1., 1.)], [box(2., 0., 3., 1.)], False),
    ([box(0., 0., 10., 10.)], [box(2., 2., 3., 3.)], True),
    ([box(0., 0., 4., 1.), box(0., 3., 4., 4.),
      box(0., 1., 1., 3.), box(3., 1., 4., 3.)], [box(1.5, 1.5, 2.5, 2.5)], False),
    ([box(0., 0., 1., 1.), box(3., 0., 4., 1.)], [box(1.5, 0., 2.5, 1.)], False),
    ([box(0., 0., 1., 1.)], [box(1., 1., 2., 2.)], False),
])
def test_actual_cells_distinguish_nesting_hole_components_and_diagonal_touch(
        mechanism, body, overlap):
    result = regions(mechanism, body)
    assert result["geometry_valid"] is True
    assert result["raw_interior_overlap"] is overlap
    assert result["strict_interior_overlap"] is overlap
    assert result["set_containment_tested"] is False
    if mechanism == [box(0., 0., 10., 10.)]:
        assert any(pair["classification"] == "strict_interior_overlap"
                   for pair in result["pair_observations"])
        assert not result["boundary_intersections"]["intersects"]


@pytest.mark.parametrize("sign,raw", [(-1., True), (1., False)])
def test_raw_and_roundoff_strict_overlap_remain_distinct(sign, raw):
    delta = 2. ** -49
    result = regions([box(0., 0., 1., 1.)],
                     [box(1. + sign * delta, 0., 2., 1.)])
    assert result["geometry_valid"] is True
    assert result["raw_interior_overlap"] is raw
    assert result["strict_interior_overlap"] is False
    assert result["roundoff_ambiguous"] is True


@pytest.mark.parametrize("invalid", [
    [(0., 0.), (2., 0.), (.5, .5), (0., 2.)],
    [(0., 0.), (1., 1.), (0., 1.), (1., 0.)],
    [(0., 0.), (1., 0.), (2., 0.), (0., 0.)],
])
def test_nonconvex_self_crossing_or_degenerate_quads_are_not_valid_geometry(invalid):
    result = regions([invalid], [box(3., 3., 4., 4.)])
    assert result["geometry_valid"] is False
    assert result["region_overlap_tested"] is False
    assert result["invalid_cells"]


@pytest.mark.parametrize("other,kind", [
    (box(1., -1., 2., 3.), "crossing"),
    (box(3., 2., 4., 3.), "endpoint_touch"),
    (box(3., 0., 4., 2.), "collinear_overlap"),
])
def test_boundary_crossing_endpoint_and_collinear_touch_are_distinct(other, kind):
    result = regions([box(0., 0., 3., 2.)], [other])
    assert result["geometry_valid"] is True
    assert result["raw_interior_overlap"] is (kind == "crossing")
    assert kind in {item["kind"] for item in result["boundary_intersections"]["intersections"]}
    if kind != "crossing":
        assert result["pair_observations"][0]["classification"] == "raw_zero_touch"
        assert result["roundoff_ambiguous"] is True


def test_parallel_edges_keep_continuous_minimizers_exact_ties_and_near_ties():
    delta = 2. ** -49
    xy = np.asarray([(-1., -2.), (3., -2.), (0., -2.), (2., -2.),
                     (0., -2.-delta), (2., -2.-delta)])
    result = finite_face_ray_hit(xy, np.asarray([[0, 1], [2, 3], [4, 5]]),
                                 np.asarray([0., 0.]), np.asarray([2., 0.]), np.asarray([0., -1.]))
    assert result["minimum_first_ray_hit_mm"] == 2.
    assert len(result["minimum_hits"]) == 2
    first = result["minimum_hits"][0]
    assert first["minimizing_edge_parameter_interval"] == [.25, .75]
    assert first["minimizing_face_parameter_interval"] == [0., 1.]
    assert first["mechanism_nodes"] == [0, 1]
    assert len(result["roundoff_near_minimum_hits"]) == 1
    assert result["roundoff_near_minimum_hits"][0]["distance_mm"] == 2.+delta


def test_small_positive_hit_is_not_tolerance_snapped_to_zero():
    delta = 2. ** -49
    result = finite_face_ray_hit(np.asarray([(0., -delta), (2., -delta)]),
                                 np.asarray([[0, 1]]), np.asarray([0., 0.]),
                                 np.asarray([2., 0.]), np.asarray([0., -1.]))
    assert 0. < result["minimum_first_ray_hit_mm"] == delta < result["roundoff_tolerance_mm"]
    assert result["closest_hit"]["raw_reconstructed_normal_projection_mm"] == delta
    assert result["closest_hit"]["analytic_forward_plane_root"] is False


def test_continuous_face_endpoint_minimum_and_interior_plane_root():
    # The endpoint minimizer is an edge-interior point, not an input node.
    endpoint = finite_face_ray_hit(np.asarray([(-1., -3.), (3., -1.)]),
        np.asarray([[0, 1]]), np.asarray([0., 0.]), np.asarray([2., 0.]), np.asarray([0., -1.]))
    assert endpoint["minimum_first_ray_hit_mm"] == 1.5
    assert endpoint["closest_hit"]["edge_parameter"] == .75
    assert endpoint["closest_hit"]["face_point_mm"] == [2., 0.]
    # y changes from-.1 to+.2: the exact binary64 values have a1:2 ratio.
    # Its zero-plane point x=1/6 and finite-face parameter7/18 are not sampled.
    plane = finite_face_ray_hit(np.asarray([(-.5, -.1), (1.5, .2)]),
        np.asarray([[0, 1]]), np.asarray([-1., 0.]), np.asarray([2., 0.]), np.asarray([0., -1.]))
    hit = plane["closest_hit"]
    assert plane["minimum_first_ray_hit_mm"] == 0.
    assert hit["face_parameter"] == pytest.approx(7./18, abs=2e-15)
    assert hit["face_point_mm"] == pytest.approx([1./6, 0.], abs=2e-15)
    assert hit["analytic_forward_plane_root"] is True
    assert abs(hit["raw_reconstructed_normal_projection_mm"]) <= plane["roundoff_tolerance_mm"]
    assert hit["witness_residual_mm"] <= plane["roundoff_tolerance_mm"]


@pytest.mark.parametrize("start,end,normal", [
    ([0., 0.], [1., 0.], [1., 0.]),
    ([0., 0.], [1., 0.], [0., 0.]),
    ([0., math.nan], [1., 0.], [0., -1.]),
    ([0., 0.], [1., 0.], [0., math.nan]),
    ([0., 0.], [1., 0.], [0., -1., 0.]),
    ([0., 0.], [1., 0.], [0., -1e308]),
])
def test_ray_rejects_invalid_face_or_normal(start, end, normal):
    with pytest.raises(ValueError):
        finite_face_ray_hit(np.asarray([(0., -1.), (1., -1.)]), np.asarray([[0, 1]]),
                            np.asarray(start), np.asarray(end), np.asarray(normal))


def square_half_model():
    # Complete Cartesian4x4 grid, h2mm, lower-half square[4,8]x[38,40].
    xy = np.asarray([(2.*i, 32.+2.*j) for j in range(5) for i in range(5)])
    conn = np.asarray([(i+5*j, i+1+5*j, i+1+5*(j+1), i+5*(j+1))
                       for j in range(4) for i in range(4)], dtype=np.int64)
    solid = np.zeros(16, dtype=bool); solid[[6, 7, 12]] = True
    model = dict(coordinates=xy, connectivity=conn, solid=solid,
                 workpiece_cells=np.asarray([14, 15], dtype=np.int64))
    metadata = dict(element_node_order=["BL", "BR", "TR", "TL"],
        grid=dict(shape_yx=[4, 4], origin_mm=[0., 32.], cell_size_mm=[2., 2.],
                  axes=[[1., 0.], [0., 1.]], array_order="C_yx_bottom_up"),
        model_extent=dict(kind="lower_half", symmetry_axis=dict(normal=[0., 1.], offset_mm=40.)),
        task=dict(workpiece=dict(kind="fixed_rigid", shape="square", center_mm=[6., 40.],
                                 side_mm=4., fixed_components=[0, 1])))
    return model, metadata


def test_complete_square_closed_cut_is_classified_but_physical_ray_excludes_it():
    model, metadata = square_half_model()
    result = measure_native_workpiece_regions(model, metadata, np.zeros(50), np.zeros(50))
    assert result["geometry_valid"] is result["complete_fixed_half_square"] is True
    assert result["regions"]["raw_interior_overlap"] is False
    assert result["faces"]["bottom"]["minimum_first_ray_hit_mm"] == 2.
    assert result["faces"]["left"]["minimum_first_ray_hit_mm"] == 2.
    closed = result["regions"]["boundary_intersections"]
    # Cut edges remain mathematical region boundaries; they are absent from rays.
    physical = np.asarray(result["physical_mechanism_edges"])
    assert not np.any(np.all(model["coordinates"][physical, 1] == 40., axis=1))
    assert closed["mechanism_edge_count"] == len(physical)+1
    assert result["set_containment_tested"] is result["signed_penetration_tested"] is False
    assert result["contact_pressure_qualification"] is result["contact_or_clamping_qualification"] is False



def test_near_corner_hit_keeps_its_interior_face_location():
    delta = 2. ** -49
    result = finite_face_ray_hit(np.asarray([(2.-delta, -1.), (3., -2.)]),
        np.asarray([[0, 1]]), np.asarray([0., 1.]), np.asarray([2., 1.]), np.asarray([0., -1.]))
    hit = result["closest_hit"]
    assert result["minimum_first_ray_hit_mm"] == 2.
    assert hit["face_parameter"] == (2.-delta)/2. < 1.
    assert hit["corner_hit"] is False and hit["near_corner_hit"] is True


@pytest.mark.parametrize("target,ids", [
    ("conn", [[0, 1, 2, -1]]), ("conn", [[0, 1, 2, 4]]),
    ("conn", [[0, 1, 2, .5]]),
    ("edge", [[0, -1]]), ("edge", [[0, 4]]), ("edge", [[0, .5]]),
])
def test_node_ids_do_not_wrap_truncate_or_read_outside_coordinates(target, ids):
    xy = np.asarray(box(0., 0., 1., 1.))
    with pytest.raises(ValueError):
        if target == "conn":
            region_overlap(xy, np.asarray(ids), np.asarray([0]), np.asarray([], dtype=int))
        else:
            finite_face_ray_hit(xy, np.asarray(ids), np.asarray([0., 2.]),
                                np.asarray([1., 2.]), np.asarray([0., -1.]))


def test_cell_ids_do_not_wrap_to_the_last_quad():
    with pytest.raises(ValueError, match="cell IDs"):
        region_overlap(np.asarray(box(0., 0., 1., 1.)), np.asarray([[0, 1, 2, 3]]),
                       np.asarray([-1]), np.asarray([], dtype=int))


def test_reference_grid_hole_cannot_masquerade_as_a_complete_body():
    model, metadata = square_half_model()
    model["connectivity"] = model["connectivity"][:-1]
    model["solid"] = model["solid"][:-1]
    model["workpiece_cells"] = np.asarray([14], dtype=np.int64)
    with pytest.raises(ValueError, match="complete declared native Cartesian reference grid"):
        measure_native_workpiece_regions(model, metadata, np.zeros(50), np.zeros(50))


@pytest.mark.parametrize("case", ["missing_body_cell", "moved_body"])
def test_incomplete_or_moving_body_is_rejected_before_region_and_ray_measurement(case):
    model, metadata = square_half_model(); fluctuation = np.zeros(50)
    if case == "missing_body_cell":
        model["workpiece_cells"] = np.asarray([14], dtype=np.int64)
    else:
        fluctuation[2*model["connectivity"][14, 0]] = .125
    result = measure_native_workpiece_regions(model, metadata, np.zeros(50), fluctuation)
    assert result["geometry_valid"] is result["complete_fixed_half_square"] is False
    assert result["regions"] is None and result["faces"] == {}
    assert result["model_failure"] == "Workpiece is not the complete, fixed lower-half square"


def test_cut_endpoint_touch_is_kept_as_math_not_a_physical_cut_edge():
    model, metadata = square_half_model()
    model["solid"][13] = True  # Side-touching component also reaches the bottom face corner.
    result = measure_native_workpiece_regions(model, metadata, np.zeros(50), np.zeros(50))
    assert result["geometry_valid"] is True
    assert result["regions"]["raw_interior_overlap"] is False
    assert result["regions"]["roundoff_ambiguous"] is True
    assert result["faces"]["bottom"]["minimum_first_ray_hit_mm"] == 0.
    assert result["faces"]["bottom"]["closest_hit"]["corner_hit"] is True
    intersections = result["regions"]["boundary_intersections"]["intersections"]
    assert any(item.get("intersection_point_mm") == [4., 40.] for item in intersections)
    physical = np.asarray(result["physical_mechanism_edges"])
    assert not np.any(np.all(model["coordinates"][physical, 1] == 40., axis=1))
    assert result["faces"]["bottom"]["separation_interpretation"] == "not_a_separation_gap"
