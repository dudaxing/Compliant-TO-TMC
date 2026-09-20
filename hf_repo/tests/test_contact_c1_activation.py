"""Boundary activation properties on manufactured states; no FE solve."""
import numpy as np
import pytest

from hf_eval.contact_c1 import build_problem
from hf_eval.contact_c1_activation import prepare_closed_initial
from hf_eval.split_prescribed import state_hash
from hf_eval.split_state import SplitDisplacement


def source(h=.25, top_value=6.779e-32):
    problem = build_problem("A0", h, "uniform_precontact")
    lift = np.zeros(problem.model.ndof)
    lift[1::2] = .25
    lift[::2] = -0.0
    fluctuation = np.zeros_like(lift)
    fluctuation[2 * problem.top_nodes + 1] = top_value
    # Preserve ordinary and sub-ulp free DOFs and signed-zero old constraints.
    fluctuation[::2] = -.125
    fluctuation[3] = 2.0**-100
    fluctuation[problem.model.fixed_dofs] = -0.0
    interior = np.flatnonzero((problem.model.coordinates[:, 1] > 0)
                             & (problem.model.coordinates[:, 1] < 1))[0]
    fluctuation[2 * interior + 1] = 2.0**-100
    return problem, SplitDisplacement(lift, fluctuation)


@pytest.mark.parametrize("h", [.25, .125])
@pytest.mark.parametrize("top_value", [6.779e-32, -6.779e-32, 0., -0., 1e-12, -1e-12])
def test_only_new_constraints_change_and_receipt_records_exact_removed_component(h, top_value):
    problem, original = source(h, top_value)
    before = (original.lift.tobytes(), original.fluctuation.tobytes())
    projected, receipt = prepare_closed_initial(original, h)
    new_fixed = 2 * problem.top_nodes + 1
    unchanged = np.ones(problem.model.ndof, dtype=bool)
    unchanged[new_fixed] = False
    assert projected.lift.tobytes() == before[0]
    assert projected.fluctuation[unchanged].tobytes() == original.fluctuation[unchanged].tobytes()
    assert not np.any(projected.fluctuation[new_fixed].view(np.uint64))
    assert (original.lift.tobytes(), original.fluctuation.tobytes()) == before
    assert not np.shares_memory(projected.lift, original.lift)
    assert not np.shares_memory(projected.fluctuation, original.fluctuation)
    assert receipt["new_fixed_dofs"] == new_fixed.tolist()
    removed = np.asarray(receipt["removed_fluctuation_mm"])
    assert removed.tobytes() == original.fluctuation[new_fixed].tobytes()
    assert receipt["maximum_projection_mm"] == abs(top_value)
    assert receipt["projection_limit_mm"] == 1e-12
    assert receipt["source_state_sha256"] == state_hash(original)
    assert receipt["projected_state_sha256"] == state_hash(projected)
    assert receipt["unchanged_components_bitwise"] is True
    assert receipt["policy"] == "explicit_new_fixed_projection_v1"
    # Existing closed builder accepts this state without any relaxation.
    closed = build_problem("A0", h, "uniform_closed", projected)
    assert closed.initial_state.fluctuation.tobytes() == projected.fluctuation.tobytes()


def test_projection_measures_sub_ulp_change_without_rounded_display_authority():
    problem, original = source()
    projected, receipt = prepare_closed_initial(original, .25)
    top = 2 * problem.top_nodes + 1
    np.testing.assert_array_equal(original.u_display[top], projected.u_display[top])
    assert receipt["maximum_projection_mm"] == 6.779e-32 > 0
    assert receipt["source_state_sha256"] != receipt["projected_state_sha256"]


@pytest.mark.parametrize("value", [np.nextafter(1e-12, np.inf), -np.nextafter(1e-12, np.inf), 1e-6])
def test_excess_projection_is_rejected_without_mutating_source(value):
    _, original = source(top_value=value)
    before = state_hash(original)
    with pytest.raises(ValueError, match="exceeds"):
        prepare_closed_initial(original, .25)
    assert state_hash(original) == before


@pytest.mark.parametrize("limit", [0., 1e-13, 2e-12, float("nan"), float("inf"), True, "1e-12"])
def test_projection_limit_is_frozen(limit):
    _, original = source()
    with pytest.raises(ValueError, match="frozen"):
        prepare_closed_initial(original, .25, projection_limit_mm=limit)


def test_nonzero_old_fixed_fluctuation_is_never_projected():
    problem, original = source()
    values = original.fluctuation.copy()
    values[problem.model.fixed_dofs[0]] = 1e-40
    with pytest.raises(ValueError, match="old fixed"):
        prepare_closed_initial(SplitDisplacement(original.lift, values), .25)


@pytest.mark.parametrize("location", ["bottom", "anchor", "top"])
def test_incorrect_lift_is_not_rebased(location):
    problem, original = source()
    values = original.lift.copy()
    index = {"bottom": 2 * problem.bottom_nodes[0] + 1,
             "anchor": problem.model.fixed_dofs[problem.model.fixed_dofs % 2 == 0][0],
             "top": 2 * problem.top_nodes[0] + 1}[location]
    values[index] = np.nextafter(values[index], np.inf)
    with pytest.raises(ValueError, match="lift"):
        prepare_closed_initial(SplitDisplacement(values, original.fluctuation), .25)


def test_wrong_state_type_or_shape_is_rejected():
    _, original = source()
    for invalid in (original.u_display, SplitDisplacement(np.zeros(4), np.zeros(4))):
        with pytest.raises(ValueError):
            prepare_closed_initial(invalid, .25)


@pytest.mark.parametrize("part,value", [("lift", np.nan), ("fluctuation", np.inf)])
def test_even_manually_corrupted_state_with_nonfinite_component_is_rejected(part, value):
    _, original = source()
    corrupted = getattr(original, part).copy()
    corrupted[0] = value
    object.__setattr__(original, part, corrupted)
    with pytest.raises(ValueError, match="finite"):
        prepare_closed_initial(original, .25)
