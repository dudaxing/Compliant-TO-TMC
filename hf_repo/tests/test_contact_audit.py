"""Geometric counterexamples and strict path semantics; no finite-element solves."""
from copy import deepcopy

import numpy as np
import pytest

from hf_eval.contact_audit import audit_rectangle_overlap, strict_valid_prefix


def audit(xy, rectangle=(0., 1., 0., 1.), **kwargs):
    options = dict(length_tolerance=1e-12, area_tolerance=1e-14, overlap_tolerance=1e-10)
    options.update(kwargs)
    return audit_rectangle_overlap(np.array(xy, dtype=np.float64), np.array([[0, 1, 2, 3]]),
                                   np.array([True]), rectangle, **options)


def test_nodes_outside_obstacle_do_not_exclude_an_edge_overlap():
    diamond = np.array([[-1., 0.], [0., -1.], [1., 0.], [0., 1.]])
    rectangle = (.25, 1., .25, 1.)
    assert not np.any((diamond[:, 0] >= .25) & (diamond[:, 1] >= .25))
    result = audit(diamond, rectangle)
    assert result["evaluable"] and result["geometry_valid"] is False
    assert result["total_overlap_area"] == pytest.approx(.125)


@pytest.mark.parametrize("xy, expected", [
    ([[-1., 0.], [0., 0.], [0., 1.], [-1., 1.]], 0.),  # edge contact
    ([[-1., -1.], [0., -1.], [0., 0.], [-1., 0.]], 0.),  # corner contact
    ([[2., 0.], [3., 0.], [3., 1.], [2., 1.]], 0.),  # separated
    ([[-2., -2.], [2., -2.], [2., 2.], [-2., 2.]], 1.),  # obstacle enclosed
    ([[.25, .25], [.75, .25], [.75, .75], [.25, .75]], .25),  # cell enclosed
    ([[0., 0.], [1., 0.], [1., 1.], [0., 1.]], 1.),
])
def test_exact_intersections_and_contact_are_distinguished(xy, expected):
    result = audit(xy)
    assert result["evaluable"]
    assert result["total_overlap_area"] == pytest.approx(expected, abs=1e-14)
    assert result["geometry_valid"] is (expected == 0.)


def test_rigid_translation_and_uniform_scaling_preserve_the_audit():
    xy = np.array([[-1., 0.], [0., -1.], [1., 0.], [0., 1.]])
    rect = np.array([.25, 1., .25, 1.])
    reference = audit(xy, rect)
    shifted = audit(xy + [1024., -2048.], rect + [1024., 1024., -2048., -2048.])
    assert shifted["total_overlap_area"] == reference["total_overlap_area"]
    for scale in (.125, 16.):
        scaled = audit(xy * scale, rect * scale, length_tolerance=1e-12 * scale,
                       area_tolerance=1e-14 * scale**2, overlap_tolerance=1e-10 * scale**2)
        assert scaled["total_overlap_area"] == pytest.approx(reference["total_overlap_area"] * scale**2)
        assert scaled["geometry_valid"] == reference["geometry_valid"]


@pytest.mark.parametrize("xy, reason", [
    ([[0., 0.], [0., 1.], [1., 1.], [1., 0.]], "clockwise_orientation"),
    ([[0., 0.], [1., 1.], [0., 1.], [1., 0.]], "nonconvex_or_self_intersecting"),
    ([[0., 0.], [1., 0.], [.25, .25], [0., 1.]], "nonconvex_or_self_intersecting"),
    ([[0., 0.], [.5, 0.], [1., 0.], [0., 1.]], "degenerate_or_collinear_corner"),
    ([[0., 0.], [0., 0.], [1., 1.], [0., 1.]], "short_or_repeated_edge"),
])
def test_illegal_quad_is_not_a_zero_overlap_pass_even_when_far_from_obstacle(xy, reason):
    result = audit(xy, (10., 11., 10., 11.))
    assert result["evaluable"] is False
    assert result["geometry_valid"] is None
    assert result["total_overlap_area"] is None
    assert result["max_element_overlap_area"] is None
    assert result["cells"][0]["reason"] == reason


def test_cell_sums_mask_and_maximum_are_explicit():
    xy = np.array([[0., 0.], [1., 0.], [1., 1.], [0., 1.], [2., 0.], [2., 1.]])
    cells = np.array([[0, 1, 2, 3], [1, 4, 5, 2], [0, 0, 0, 0]])
    options = dict(length_tolerance=0., area_tolerance=0., overlap_tolerance=0.)
    result = audit_rectangle_overlap(xy, cells, np.array([True, True, False]), (.5, 1.25, 0., 1.), **options)
    assert result["n_solid_cells"] == 2
    assert result["total_overlap_area"] == .75
    assert result["max_element_overlap_area"] == .5
    invalid = audit_rectangle_overlap(xy, cells, np.array([True, True, True]), (.5, 1.25, 0., 1.), **options)
    assert invalid["total_overlap_area"] is None
    assert invalid["cells"][0]["overlap_area"] == .5  # good-cell evidence retained
    assert invalid["cells"][2]["reason"] == "repeated_node_index"


def test_overlap_tolerance_does_not_expand_or_zero_the_geometry():
    xy = [[0., 0.], [1., 0.], [1., 1.], [0., 1.]]
    result = audit(xy, (.75, 1.5, 0., 1.), overlap_tolerance=.25)
    assert result["geometry_valid"] is True
    assert result["total_overlap_area"] == .25
    assert audit(xy, (.75, 1.5, 0., 1.), overlap_tolerance=.249)["geometry_valid"] is False


@pytest.mark.parametrize("field, value", [
    ("coordinates", np.array([[0., 0.], [1., 0.], [1., np.nan], [0., 1.]])),
    ("coordinates", np.zeros((4, 2), dtype=np.float32)),
    ("connectivity", np.array([[0., 1., 2., 3.]])),
    ("connectivity", np.array([[0, 1, 2, 4]])),
    ("solid_mask", np.array([1])),
    ("rectangle", (0., np.inf, 0., 1.)),
    ("rectangle", (1., 0., 0., 1.)),
    ("length_tolerance", -1.),
    ("area_tolerance", float("nan")),
    ("overlap_tolerance", float("inf")),
])
def test_malformed_inputs_and_nonfinite_values_are_rejected(field, value):
    arguments = dict(coordinates=np.array([[0., 0.], [1., 0.], [1., 1.], [0., 1.]]),
                     connectivity=np.array([[0, 1, 2, 3]]), solid_mask=np.array([True]),
                     rectangle=(0., 1., 0., 1.), length_tolerance=0., area_tolerance=0., overlap_tolerance=0.)
    arguments[field] = value
    with pytest.raises(ValueError):
        audit_rectangle_overlap(**arguments)


def test_finite_inputs_with_overflowing_geometry_cannot_pass():
    huge = 1e308
    result = audit([[-huge, -huge], [huge, -huge], [huge, huge], [-huge, huge]])
    assert not result["evaluable"]
    assert result["geometry_valid"] is None and result["total_overlap_area"] is None


def state(identifier, d, value=None, **flags):
    return dict(id=identifier, d=d, value=value,
                **{**dict(solver_valid=True, geometry_valid=True, reference_valid=True), **flags})


def test_inserted_invalid_state_locks_prefix_even_after_geometric_recovery():
    inputs = [state("zero", 0., 0.), state("inserted", .25, 3., geometry_valid=False), state("target", .5, 4.)]
    original = deepcopy(inputs)
    result = strict_valid_prefix(inputs)
    assert inputs == original
    assert result["prefix_length"] == 1 and result["first_invalid_id"] == "inserted"
    assert result["prefix_end_id"] == "zero" and result["prefix_end_d"] == 0.
    rows = result["states"]
    assert rows[0]["score"] == 0.
    assert rows[1]["score"] is None and rows[1]["value"] == 3.
    assert rows[2]["local_valid"] and not rows[2]["comparable"]
    assert rows[2]["score"] is None and rows[2]["score_reason"] == "after_first_invalid"


def test_unknown_and_missing_values_are_distinct_from_genuine_zero():
    missing = state("missing", .5)
    del missing["value"]
    result = strict_valid_prefix([state("unknown", 0.), missing, state("zero", 1., 0.)])
    assert result["prefix_length"] == 3 and result["first_invalid_id"] is None
    assert [r["score"] for r in result["states"]] == [None, None, 0.]
    assert [r["score_reason"] for r in result["states"]] == ["unknown_value", "value_not_provided", None]


@pytest.mark.parametrize("gate", ["solver_valid", "geometry_valid", "reference_valid"])
def test_each_gate_can_end_the_prefix(gate):
    result = strict_valid_prefix([state("bad", 1., 2., **{gate: False})])
    assert result["prefix_length"] == 0 and result["prefix_end_id"] is None
    assert result["states"][0]["failed_checks"] == [gate]


@pytest.mark.parametrize("field", ["id", "d", "solver_valid", "geometry_valid", "reference_valid"])
def test_all_acceptance_fields_are_required(field):
    row = state("valid", 0., 0.)
    del row[field]
    with pytest.raises(ValueError, match="requires"):
        strict_valid_prefix([row])


@pytest.mark.parametrize("field, value", [
    ("d", float("nan")), ("d", float("inf")), ("value", float("inf")),
    ("solver_valid", 1), ("geometry_valid", None), ("reference_valid", "true"),
    ("id", ""), ("id", True), ("id", float("nan")),
])
def test_prefix_rejects_nonfinite_values_and_implicit_validity(field, value):
    row = state("valid", 0., 0.)
    row[field] = value
    with pytest.raises(ValueError):
        strict_valid_prefix([row])


def test_duplicate_ids_are_rejected_and_path_order_is_not_sorted_by_displacement():
    with pytest.raises(ValueError, match="unique"):
        strict_valid_prefix([state("same", 0.), state("same", 1.)])
    result = strict_valid_prefix([state("load", 1., 2.), state("failed", 2., 3., reference_valid=False),
                                  state("unload", .5, 1.)])
    assert result["prefix_length"] == 1
    assert result["states"][-1]["score"] is None
    assert strict_valid_prefix([])["prefix_length"] == 0
