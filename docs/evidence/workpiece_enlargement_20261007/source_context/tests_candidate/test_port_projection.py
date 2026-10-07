"""Independent algebra tests for the optional mean-port displacement guess.

The injected cubic residual is a controller fixture, not a TMC material model.
These tests do not certify contact or the native workpiece's physical response.
"""
from copy import deepcopy

import numpy as np
import pytest
from scipy.optimize import brentq

from test_split_displacement import one_cell, physical, synthetic
from test_native_force import small_native, forbid_legacy_or_compiled_work
from test_native_mean import settings as small_settings
import hf_eval.split_displacement as control
from hf_eval import native_mean
from hf_eval.displacement import DisplacementSettings


def cubic_equilibrium(mean, cubic):
    """Eliminate only the mean constraint, then solve unequal-node force balance."""
    left = brentq(lambda u: 2*u+cubic*u**3
                  - (8*(2*mean-u)+cubic*(2*mean-u)**3),
                  0., 2*mean, xtol=1e-14)
    return np.array([left, 2*mean-left]), 2*(2*left+cubic*left**3)


def test_port_guess_avoids_invalid_predictor_and_reaches_independent_cubic_root(monkeypatch):
    model, port = one_cell()
    _, assemble = synthetic(model, cubic=1000., invalid_above=.15)
    settings = DisplacementSettings(max_bisections=0)
    common = dict(assembler=assemble, settings=settings, force_scale_per_length=20.)
    default = control.solve_split_displacement_path(model, port, port, [0., .1], **common)
    assert default["status"] == "failed" and default["failure"]["code"] == "invalid_J"
    assert len(default["accepted_steps"]) == 1 and default["maximum_bisection_depth"] == 0
    np.testing.assert_array_equal(physical(default["last_accepted_state"]), 0.)
    assert default["failed_attempts"][-1]["rollback_bitwise_equal"]

    original_lu, solves, bases = control._linear_solve, [], []

    def observe_lu(*args, **kwargs):
        step, reaction, row = original_lu(*args, **kwargs)
        solves.append((kwargs["phase"], step.copy(), reaction))
        return step, reaction, row

    def observe_base(actual_model, state, *, tangent=True):
        if tangent:
            bases.append((state.lift+state.fluctuation).copy())
        return assemble(actual_model, state, tangent=tangent)

    monkeypatch.setattr(control, "_linear_solve", observe_lu)
    projected = control.solve_split_displacement_path(
        model, port, port, [0., .1], assembler=observe_base, settings=settings,
        force_scale_per_length=20., initial_guess="port_projection")
    assert projected["status"] == "success" and projected["initial_guess"] == "port_projection"
    assert projected["failed_attempts"] == [] and projected["maximum_bisection_depth"] == 0
    # A real KKT LU still computes the inadmissible linear displacement and dR.
    assert solves[0][0] == "predictor"
    linear_guess = np.zeros(model.ndof); linear_guess[model.free] = solves[0][1]
    np.testing.assert_allclose(linear_guess[[2, 6]], [.16, .04], rtol=0., atol=1e-14)
    # Only the initial displacement distribution changes; dR is actually used.
    np.testing.assert_allclose(bases[1][[2, 6]], [.1, .1], rtol=0., atol=1e-14)
    first = next(row for row in projected["newton_history"] if row["d"] == .1)
    assert first["R_input"] == pytest.approx(solves[0][2], rel=0., abs=1e-14)
    expected, reaction = cubic_equilibrium(.1, 1000.)
    final = projected["target_metrics"]
    np.testing.assert_allclose(physical(final)[[2, 6]], expected, rtol=1e-10, atol=2e-12)
    assert abs(expected[0]-expected[1]) > .001  # The mean does not tie both nodes.
    assert expected[0] < .15 and final["R_input"] == pytest.approx(reaction, rel=1e-10)
    assert final["q_in"] == pytest.approx(.1, rel=0., abs=1e-14)
    np.testing.assert_array_equal(physical(final)[model.fixed_dofs], 0.)
    assert final["relative_residual"] <= settings.tolerance
    assert abs(final["constraint_residual"]) <= final["constraint_bound"]
    predictor = next(row for row in projected["linear_solve_diagnostics"] if row["phase"] == "predictor")
    assert predictor["displacement_mode"] == "port_projection"
    assert predictor["applied_dw"] is False and predictor["applied_dR"] is True
    assert predictor["factorization"] == "general sparse LU" and predictor["symmetrized"] is False
    assert predictor["relative_force_block_residual"] < 1e-12


def test_nonzero_lift_and_ordered_unloading_match_independent_dense_equilibrium():
    model, port = one_cell()
    matrix, assemble = synthetic(model, nonsymmetric=True)
    output, shape = np.zeros(model.ndof), np.zeros(model.ndof)
    output[[2, 6]] = [.25, .75]
    shape[[2, 3, 6, 7]] = [.8, .3, 1.2, -.5]
    free, stiffness = model.free, 5.
    total = matrix+stiffness*np.outer(output, output)
    kkt = np.block([[total[np.ix_(free, free)], -port[free, None]],
                    [port[None, free], np.zeros((1, 1))]])
    targets = [0., .1, .2, .1, 0.]
    result = control.solve_split_displacement_path(
        model, port, output, targets, stiffness, lift_shape=shape,
        assembler=assemble, force_scale_per_length=20., path_mode="ordered_cycle",
        initial_guess="port_projection")
    assert result["status"] == "success" and result["path_completed"] and result["unload_endpoint_reached"]
    assert [row["d"] for row in result["accepted_steps"]] == targets
    assert [row["leg"] for row in result["accepted_steps"]] == ["origin", "loading", "loading", "unloading", "unloading"]
    for row, target in zip(result["accepted_steps"], targets):
        expected = np.linalg.solve(kkt, np.r_[np.zeros(len(free)), target])
        np.testing.assert_allclose(physical(row)[free], expected[:-1], rtol=1e-11, atol=3e-14)
        np.testing.assert_array_equal(row["u_lift"], target*shape)
        np.testing.assert_array_equal(physical(row)[model.fixed_dofs], 0.)
        assert row["R_input"] == pytest.approx(expected[-1], rel=1e-11, abs=3e-14)
        assert abs(row["constraint_residual"]) <= row["constraint_bound"]
    predictors = [r for r in result["linear_solve_diagnostics"] if r["phase"] == "predictor"]
    assert len(predictors) == len(targets)-1
    assert all(r["displacement_mode"] == "port_projection" and r["applied_dw"] is False
               and r["applied_dR"] is True for r in predictors)
    assert abs(physical(result["accepted_steps"][2])[2]-physical(result["accepted_steps"][2])[6]) > .01


def test_default_tangent_path_stays_exact_and_projection_keeps_positive_J_gate():
    model, port = one_cell()
    _, assemble = synthetic(model, cubic=100.)
    common = dict(assembler=assemble, force_scale_per_length=20.)
    implicit = control.solve_split_displacement_path(model, port, port, [0., .05, .1], **common)
    explicit = control.solve_split_displacement_path(
        model, port, port, [0., .05, .1], initial_guess="tangent", **common)
    assert implicit["status"] == explicit["status"] == "success"
    assert "initial_guess" not in implicit and "initial_guess" not in explicit
    assert implicit["linear_solve_diagnostics"] == explicit["linear_solve_diagnostics"]
    assert implicit["trials"] == explicit["trials"]
    assert implicit["failed_attempts"] == explicit["failed_attempts"]
    for left, right in zip(implicit["accepted_steps"], explicit["accepted_steps"]):
        np.testing.assert_array_equal(left["u_lift"].view(np.uint64), right["u_lift"].view(np.uint64))
        np.testing.assert_array_equal(left["u_fluctuation"].view(np.uint64), right["u_fluctuation"].view(np.uint64))
        assert left["state_sha256"] == right["state_sha256"] and left["R_input"] == right["R_input"]
    assert all("displacement_mode" not in r and "applied_dw" not in r and "applied_dR" not in r
               for r in implicit["linear_solve_diagnostics"] if r["phase"] == "predictor")

    def nonpositive_J(actual_model, state, *, tangent=True):
        matrix, force, fields = assemble(actual_model, state, tangent=tangent)
        if port @ (state.lift+state.fluctuation) > 0.:
            fields["J"] = np.zeros_like(fields["J"])
        return matrix, force, fields

    blocked = control.solve_split_displacement_path(
        model, port, port, [0., .1], assembler=nonpositive_J,
        settings=DisplacementSettings(max_bisections=0), force_scale_per_length=20.,
        initial_guess="port_projection")
    assert blocked["status"] == "failed" and blocked["failure"]["code"] == "invalid_J"
    assert len(blocked["accepted_steps"]) == 1 and blocked["target_metrics"] is None
    assert blocked["failed_attempts"][-1]["rollback_bitwise_equal"]
    np.testing.assert_array_equal(physical(blocked["last_accepted_state"]), 0.)


def test_native_mean_forwards_port_guess_on_real_16_element_numpy_case(small_native):
    source, original_task = small_native
    task, target = deepcopy(original_task), .001
    task["purpose"] = "average_displacement_test_only"
    task["input"]["target_mm"] = target
    settings = small_settings(target)  # Existing 8-second API window and gates.
    default = native_mean.solve_native_mean(source, task, [0., target], settings=settings)
    projected = native_mean.solve_native_mean(
        source, task, [0., target], settings=settings, initial_guess="port_projection")
    assert default.path["status"] == projected.path["status"] == "success"
    assert "initial_guess" not in default.path and "initial_guess" not in default.metadata
    assert projected.path["initial_guess"] == projected.metadata["initial_guess"] == "port_projection"
    model = projected.project.model
    assert model.ne == 16 and model.ndof == 50
    ordinary, changed = default.accepted[-1], projected.accepted[-1]
    np.testing.assert_allclose(changed.state.lift+changed.state.fluctuation,
                               ordinary.state.lift+ordinary.state.fluctuation,
                               rtol=settings.tolerance, atol=settings.tolerance*target)
    assert changed.record["R_input"] == pytest.approx(ordinary.record["R_input"], rel=settings.tolerance)
    for result in (default, projected):
        assert result.metadata["task_target_executed"] and result.metadata["production_converged"]
        counts = result.metadata["call_counts"]
        assert counts["HP_calls"] == counts["JIT_calls"] == 0 and counts["solver_invocations"] == 1
        for accepted in result.accepted:
            np.testing.assert_array_equal(accepted.state.lift[model.fixed_dofs], 0.)
            np.testing.assert_array_equal(accepted.state.fluctuation[model.fixed_dofs], 0.)
            assert abs(accepted.record["constraint_residual"]) <= accepted.record["constraint_bound"]
            assert accepted.record["relative_residual"] <= settings.tolerance
            assert np.all(accepted.arrays["J"] > 0.)
    predictors = [r for r in projected.path["linear_solve_diagnostics"] if r["phase"] == "predictor"]
    assert len(predictors) == 1
    row = predictors[0]
    assert row["displacement_mode"] == "port_projection"
    assert row["applied_dw"] is False and row["applied_dR"] is True
    assert row["factorization"] == "general sparse LU" and row["symmetrized"] is False
    assert row["relative_force_block_residual"] <= settings.tolerance
