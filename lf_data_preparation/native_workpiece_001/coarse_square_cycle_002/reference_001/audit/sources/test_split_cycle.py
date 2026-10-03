"""Ordered load/unload controller tests with independent linear port algebra.

The injected one-cell residual is a controller TEST fixture, not a TMC material
or contact qualification. The dense equations include every free DOF and the
actuator multiplier; returning to zero is part of the path rather than a reset.
"""
import numpy as np
import pytest

from hf_eval.displacement import DisplacementSettings
from hf_eval.split_displacement import solve_split_displacement_path
from hf_eval.tmc import TMCError
from hf_eval.tmc_kernel import KernelError
from test_split_displacement import one_cell, physical, synthetic


def dense_port_solution(model, matrix, port, target):
    free = model.free
    augmented = np.block([
        [matrix[np.ix_(free, free)], -port[free, None]],
        [port[None, free], np.zeros((1, 1))],
    ])
    solution = np.linalg.solve(augmented, np.r_[np.zeros(len(free)), target])
    displacement = np.zeros(model.ndof)
    displacement[free] = solution[:-1]
    return displacement, solution[-1]


def test_ordered_cycle_keeps_mean_port_state_and_repeated_target_identity():
    model, port = one_cell()
    matrix, assembler = synthetic(model)
    targets = [0., .15625, .3125, .15625, 0.]
    shape = np.zeros(model.ndof)
    shape[[2, 6]] = [.5, .25]
    observed = []
    result = solve_split_displacement_path(
        model, port, port, targets, lift_shape=shape, assembler=assembler,
        force_scale_per_length=20., path_mode="ordered_cycle",
        on_accept=lambda row: observed.append(row))
    assert result["status"] == "success" and result["path_completed"]
    assert result["loading_peak_reached"] and result["unload_endpoint_reached"]
    assert result["target_displacement"] == result["reached_displacement"] == 0.
    records = result["accepted_steps"]
    assert [row["d"] for row in records] == targets
    assert [row["original_target_index"] for row in records] == list(range(5))
    assert [row["leg"] for row in records] == [
        "origin", "loading", "loading", "unloading", "unloading"]
    assert [row["original_target_index"] for row in observed] == list(range(5))
    for target, row in zip(targets, records):
        expected, reaction = dense_port_solution(model, matrix, port, target)
        np.testing.assert_allclose(physical(row), expected, rtol=1e-12, atol=1e-14)
        np.testing.assert_array_equal(row["u_lift"], target * shape)
        np.testing.assert_array_equal(physical(row)[model.fixed_dofs], 0.)
        assert row["R_input"] == pytest.approx(reaction, rel=1e-12, abs=1e-14)
        assert row["q_in"] == pytest.approx(target, abs=1e-14)
        assert row["newton_checks"] == 1
        assert row["is_original_target"]
    # The unequal stiffness permits different node motion at the same mean.
    assert records[2]["u_display"][2] != records[2]["u_display"][6]
    assert result["timing_seconds"]["kernel_calls"] == len(targets)
    assert [row["stage_parameter"] for row in result["linear_solve_diagnostics"]] == targets[1:]
    np.testing.assert_array_equal(result["u_display"], 0.)
    assert result["R_input"] == 0.


def test_descending_failure_bisects_and_retains_original_unloading_leg():
    model, port = one_cell()
    matrix, assembler = synthetic(model)
    peak_seen, failure_injected = False, False

    def accepted(row):
        nonlocal peak_seen
        peak_seen |= row["d"] == .3125

    def fail_once(actual_model, state, *, tangent=True):
        nonlocal failure_injected
        if peak_seen and not failure_injected and state.u_display[2] == 0.:
            failure_injected = True
            raise KernelError("injected descending endpoint failure", code="invalid_J")
        return assembler(actual_model, state, tangent=tangent)

    result = solve_split_displacement_path(
        model, port, port, [0., .3125, 0.], assembler=fail_once,
        force_scale_per_length=20., path_mode="ordered_cycle", on_accept=accepted,
        settings=DisplacementSettings(minimum_increment=.125, max_bisections=1))
    assert failure_injected and result["status"] == "success"
    assert result["path_completed"] and result["unload_endpoint_reached"]
    assert result["loading_peak_reached"] and result["maximum_bisection_depth"] == 1
    records = result["accepted_steps"]
    assert [row["d"] for row in records] == [0., .3125, .15625, 0.]
    assert [row["original_target_index"] for row in records] == [0, 1, 2, 2]
    assert [row["leg"] for row in records] == ["origin", "loading", "unloading", "unloading"]
    assert [row["is_original_target"] for row in records] == [True, True, False, True]
    assert records[2]["original_target_displacement"] == 0.
    for row in records:
        expected, reaction = dense_port_solution(model, matrix, port, row["d"])
        np.testing.assert_allclose(physical(row), expected, atol=1e-14)
        assert row["R_input"] == pytest.approx(reaction, abs=1e-14)
    failure, = result["failed_attempts"]
    assert failure["from_displacement"] == .3125 and failure["attempted_displacement"] == 0.
    assert failure["from_R_input"] == records[1]["R_input"]
    assert failure["rollback_bitwise_equal"]
    # A continued cached tangent needs one evaluation per accepted state plus
    # the injected failure, including both halves of the descending segment.
    assert result["timing_seconds"]["kernel_calls"] == len(records) + 1


def test_default_loading_contract_is_unchanged_and_cycle_bounds_are_explicit():
    model, port = one_cell()
    _, assembler = synthetic(model)
    kwargs = dict(assembler=assembler, force_scale_per_length=20.)
    with pytest.raises(TMCError, match="strictly increase"):
        solve_split_displacement_path(model, port, port, [0., .3125, 0.], **kwargs)
    for targets in ([.1, 0.], [0., -.1], [0., .1, .1]):
        with pytest.raises(TMCError, match="nonnegative and have no adjacent duplicates"):
            solve_split_displacement_path(model, port, port, targets,
                                          path_mode="ordered_cycle", **kwargs)
    for targets in ([0.], [0., .1], [0., .1, 0., .1]):
        with pytest.raises(TMCError, match="include unloading and end below its loading peak"):
            solve_split_displacement_path(model, port, port, targets,
                                          path_mode="ordered_cycle", **kwargs)
    result = solve_split_displacement_path(model, port, port, [0., .15625], **kwargs)
    assert result["status"] == "success"
    assert not {"path_mode", "path_completed", "loading_peak_reached", "unload_endpoint_reached"} & result.keys()
    assert all("original_target_index" not in row and "leg" not in row
               for row in result["accepted_steps"])
