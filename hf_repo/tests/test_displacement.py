"""Analytic KKT, bounded failure, and tiny real-kernel displacement checks.

Synthetic constitutive functions isolate the controller's algebra; they are
not claimed to represent the TMC material.  No candidate or C-shape is solved.
"""
import os

os.environ["JAX_ENABLE_X64"] = "true"
os.environ["JAX_PLATFORMS"] = "cpu"

import numpy as np
import pytest
from scipy import sparse

import hf_eval.displacement as control
from hf_eval.displacement import DisplacementSettings, solve_displacement_path, solve_initial_tangent
from hf_eval.tmc import TMCError, rectangular_model
from hf_eval.tmc_kernel import KernelError


def one_cell():
    model = rectangular_model(1, 1, 1, 1, E=1, alpha=0, fixed_dofs=[0, 1, 4, 5])
    b = np.zeros(model.ndof)
    b[[2, 6]] = .5
    return model, b


def synthetic(monkeypatch, model, *, cubic=0., nonsymmetric=False, invalid_above=None,
              singular=False):
    """One-cell algebra fixture, global interleaved ordering retained exactly."""
    M = np.diag([1., 1., 2., 3., 1., 1., 8., 5.])
    if nonsymmetric:
        M[2, 6] = 1.
    if singular:
        M[:] = 0

    def fake_assemble(actual_model, u, tangent=True):
        assert actual_model is model
        if invalid_above is not None and u[2] > invalid_above:
            raise KernelError("synthetic invalid determinant", code="invalid_J", details={"u2": float(u[2])})
        r = M @ u + cubic * u**3
        K = M + np.diag(3 * cubic * u**2)
        local = r[model.edofs]
        return (sparse.csc_matrix(K) if tangent else None), r, {
            "residual": local, "material_residual": .8 * local,
            "regularization_residual": .2 * local, "J": np.ones((1, 9)),
            "material_energy": np.array([.5 * u @ M @ u + cubic / 4 * np.sum(u**4)]),
            "timing_seconds": {"kernel_and_transfer": 0., "assembly": 0.},
        }

    monkeypatch.setattr(control, "assemble", fake_assemble)
    return M


def test_analytic_average_keeps_port_deformation_and_actuator_sign(monkeypatch):
    model, b = one_cell()
    synthetic(monkeypatch, model)
    reference = solve_initial_tangent(model, b, b)
    np.testing.assert_allclose(reference["u"][[2, 6]], [1.6, .4], rtol=1e-12, atol=1e-14)
    assert reference["R_input"] == pytest.approx(6.4, rel=1e-12)
    assert reference["q_in"] == pytest.approx(1.)
    assert reference["matrix_diagnostics"]["symmetrized"] is False
    result = solve_displacement_path(model, b, b, [.1, .2], force_scale_per_length=20.)
    assert result["status"] == "success"
    final = result["target_metrics"]
    np.testing.assert_allclose(final["u"][[2, 6]], [.32, .08], rtol=1e-12, atol=1e-14)
    assert final["R_input"] == pytest.approx(1.28, rel=1e-12)
    # A rigid binding would give u2=u6=.2 and R=(2+8)*.2=2, a different problem.
    assert abs(final["R_input"] - 2.) > .5
    assert abs(final["u"][2] - final["u"][6]) > .2
    np.testing.assert_allclose(final["input_force"], b * final["R_input"])
    for state in result["accepted_steps"]:
        assert abs(state["constraint_residual"]) <= state["constraint_bound"]
        assert state["relative_residual"] <= 1e-9
        np.testing.assert_allclose(state["material_internal_force"] + state["regularization_internal_force"],
                                   state["internal_force"], rtol=1e-14, atol=1e-14)


def test_rank_one_output_spring_is_not_individual_node_springs(monkeypatch):
    model, b = one_cell()
    M = synthetic(monkeypatch, model)
    stiffness = 5.
    reference = solve_initial_tangent(model, b, b, stiffness)
    np.testing.assert_allclose(reference["K_total"].toarray(), M + stiffness * np.outer(b, b), atol=1e-14)
    np.testing.assert_allclose(reference["u"][[2, 6]], [1.6, .4], rtol=1e-12)
    assert reference["R_input"] == pytest.approx(6.4 + stiffness, rel=1e-12)
    result = solve_displacement_path(model, b, b, [.2], stiffness, force_scale_per_length=20.)
    final = result["target_metrics"]
    assert result["status"] == "success"
    assert final["R_input"] == pytest.approx((6.4 + stiffness) * .2, rel=1e-12)
    np.testing.assert_allclose(final["spring_force_on_structure"], -stiffness * b * .2, atol=1e-14)
    assert final["output_spring_generalized_force"] == pytest.approx(-1.)
    assert final["output_spring_energy"] == pytest.approx(.1)
    independent = M + np.diag(stiffness * b**2)
    independent_u = np.linalg.solve(independent, b)
    independent_u /= b @ independent_u
    assert np.linalg.norm(independent_u - reference["u"]) > .1


def test_actual_unsymmetric_jacobian_is_used(monkeypatch):
    model, b = one_cell()
    synthetic(monkeypatch, model, nonsymmetric=True)
    reference = solve_initial_tangent(model, b, b)
    np.testing.assert_allclose(reference["u"][[2, 6]], [14/9, 4/9], rtol=1e-12)
    assert reference["R_input"] == pytest.approx(64/9, rel=1e-12)
    assert reference["matrix_diagnostics"]["relative_tangent_asymmetry"] > 0
    result = solve_displacement_path(model, b, b, [.1], force_scale_per_length=1.)
    assert result["status"] == "success"
    np.testing.assert_allclose(result["u"], .1 * reference["u"], atol=1e-14, rtol=1e-12)
    assert result["linear_solve_diagnostics"][0]["relative_force_block_residual"] < 1e-12


def test_fixed_scale_armijo_and_feasible_newton_corrections(monkeypatch):
    model, b = one_cell()
    synthetic(monkeypatch, model, cubic=100.)
    result = solve_displacement_path(model, b, b, [.05, .1], force_scale_per_length=20.)
    assert result["status"] == "success"
    assert result["trials"]
    for trial in result["trials"]:
        if trial["accepted"]:
            assert trial["phi"] <= (1 - 2e-4 * trial["factor"]) * trial["base_phi"]
            assert abs(trial["constraint_residual"]) <= 1e-10 * trial["target_displacement"]
    assert any(abs(t["fixed_residual_scale"] - t["recomputed_trial_scale"]) > 1e-5
               for t in result["trials"] if t["accepted"])
    for solve in result["linear_solve_diagnostics"]:
        assert abs(solve["constraint_block_residual"]) < 1e-12
        if solve["phase"] == "corrector":
            assert abs(solve["mean_correction"]) < 1e-12


def test_scale_uses_internal_actuator_and_spring_with_explicit_nonzero_floor(monkeypatch):
    model, b = one_cell()
    synthetic(monkeypatch, model)
    result = solve_displacement_path(model, b, b, [0., .1], 5., force_scale_per_length=20.)
    assert result["status"] == "success"
    zero, loaded = result["accepted_steps"]
    assert zero["residual_scale"] == pytest.approx(1e-8 * 20 * 1e-6)
    assert zero["relative_residual"] == 0
    assert zero["R_input"] == 0
    for state in (zero, loaded):
        expected = max(np.linalg.norm(state["internal_force"][model.free]),
                       np.linalg.norm(state["input_force"][model.free]),
                       np.linalg.norm(state["spring_force_on_structure"][model.free]),
                       1e-8 * 20 * max(abs(state["d"]), 1e-6))
        assert state["residual_scale"] == expected


def test_failed_target_keeps_previous_u_and_reaction_and_null_target(monkeypatch):
    model, b = one_cell()
    synthetic(monkeypatch, model, invalid_above=.25)
    result = solve_displacement_path(model, b, b, [.1, .3], settings=DisplacementSettings(max_bisections=0),
                                     force_scale_per_length=20.)
    assert result["status"] == "failed" and result["target_metrics"] is None
    assert result["failure"]["code"] == "invalid_J"
    assert result["reached_displacement"] == .1
    assert result["R_input"] == result["last_accepted_state"]["R_input"]
    np.testing.assert_array_equal(result["u"], result["accepted_steps"][-1]["u"])
    assert result["failed_attempts"][-1]["rollback_bitwise_equal"]


def test_bisection_retains_verified_substep_without_claiming_original_target(monkeypatch):
    model, b = one_cell()
    synthetic(monkeypatch, model, invalid_above=.35)
    settings = DisplacementSettings(max_bisections=2, minimum_increment=.001)
    result = solve_displacement_path(model, b, b, [.1, .3], settings=settings, force_scale_per_length=20.)
    assert result["status"] == "failed" and result["target_metrics"] is None
    assert result["target_displacement"] == .3
    assert result["reached_displacement"] == pytest.approx(.2)
    last = result["last_accepted_state"]
    assert last["original_target_displacement"] == .3 and not last["is_original_target"]
    assert last["bisection_depth"] == 1
    assert all(record["rollback_bitwise_equal"] for record in result["failed_attempts"])


def test_singular_tangent_returns_no_false_accepted_state(monkeypatch):
    model, b = one_cell()
    synthetic(monkeypatch, model, singular=True)
    result = solve_displacement_path(model, b, b, [.1], settings=DisplacementSettings(max_bisections=0),
                                     force_scale_per_length=20.)
    assert result["status"] == "failed"
    assert result["failure"]["code"] == "singular_tangent"
    assert result["target_metrics"] is None and result["last_accepted_state"] is None
    np.testing.assert_array_equal(result["u"], 0)
    assert result["R_input"] == result["reached_displacement"] == 0.


def test_backtracking_failure_preserves_zero_state(monkeypatch):
    model, b = one_cell()
    synthetic(monkeypatch, model, cubic=100.)
    ordinary_assemble = control.assemble

    def reject_all_line_search_trials(actual_model, u, tangent=True):
        if not tangent:
            raise KernelError("injected inadmissible trial", code="invalid_J")
        return ordinary_assemble(actual_model, u, tangent=tangent)

    monkeypatch.setattr(control, "assemble", reject_all_line_search_trials)
    settings = DisplacementSettings(max_backtracks=2, max_bisections=0)
    result = solve_displacement_path(model, b, b, [.05], settings=settings, force_scale_per_length=20.)
    assert result["status"] == "failed"
    assert result["failure"]["code"] == "backtracking_failed"
    assert len(result["trials"]) == 3
    assert not any(record["accepted"] for record in result["trials"])
    assert result["target_metrics"] is None
    np.testing.assert_array_equal(result["u"], 0)


def test_callback_has_deep_copies_and_persistence_failure_keeps_verified_state(monkeypatch):
    model, b = one_cell()
    synthetic(monkeypatch, model, cubic=10.)
    ordinary = solve_displacement_path(model, b, b, [.05, .1], force_scale_per_length=20.)

    def mutate(record):
        for value in record.values():
            if isinstance(value, np.ndarray):
                value[:] = -999
        record["d"] = -999

    observed = solve_displacement_path(model, b, b, [.05, .1], on_accept=mutate, force_scale_per_length=20.)
    np.testing.assert_array_equal(observed["u"], ordinary["u"])
    assert observed["R_input"] == ordinary["R_input"]
    assert np.all(observed["accepted_steps"][0]["J"] == 1)

    def cannot_save(record):
        raise OSError("test storage unavailable")

    failed = solve_displacement_path(model, b, b, [.05, .1], on_accept=cannot_save, force_scale_per_length=20.)
    assert failed["status"] == "failed" and failed["failure"]["code"] == "persistence_failure"
    assert failed["reached_displacement"] == .05 and failed["last_accepted_state"] is not None
    assert failed["target_metrics"] is None


def test_timeout_is_failure_with_null_metrics_without_numerical_call(monkeypatch):
    model, b = one_cell()
    ticks = iter(np.arange(100, dtype=float))
    monkeypatch.setattr(control, "perf_counter", lambda: next(ticks))
    result = solve_displacement_path(model, b, b, [.1], settings=DisplacementSettings(time_limit_seconds=.01),
                                     force_scale_per_length=20.)
    assert result["failure"]["code"] == "time_limit"
    assert result["target_metrics"] is None and result["last_accepted_state"] is None
    assert result["timing_seconds"]["kernel_calls"] == 0


@pytest.mark.parametrize("field,value", [("tolerance", np.nan), ("constraint_tolerance", 0),
                                       ("max_checks", 25.), ("max_backtracks", True),
                                       ("max_bisections", -1), ("time_limit_seconds", np.inf),
                                       ("displacement_scale_floor", -1), ("armijo_c", .5),
                                       ("minimum_increment", 1j)])
def test_invalid_settings_rejected(field, value):
    with pytest.raises(TMCError):
        DisplacementSettings(**{field: value})


@pytest.mark.parametrize("targets", [[], [-.1], [.1, .1], [.2, .1], [np.nan], [.1 + 1j]])
def test_invalid_targets_rejected_without_solving(targets):
    model, b = one_cell()
    with pytest.raises(TMCError):
        solve_displacement_path(model, b, b, targets, force_scale_per_length=20.)


@pytest.mark.parametrize("scale", [0., -1., np.inf, np.nan, 1j, True, "20"])
def test_explicit_force_per_length_scale_is_required_and_validated(scale):
    model, b = one_cell()
    with pytest.raises(TMCError):
        solve_displacement_path(model, b, b, [.1], force_scale_per_length=scale)


def test_port_fixed_conflict_and_invalid_port_and_spring_rejected():
    model, b = one_cell()
    fixed = np.zeros(model.ndof)
    fixed[0] = 1.
    with pytest.raises(TMCError, match="no free DOF"):
        solve_displacement_path(model, fixed, b, [.1], force_scale_per_length=20.)
    for bad in (b.astype(complex) + 1j, np.full(model.ndof, np.nan), b[:-1]):
        with pytest.raises(TMCError):
            solve_displacement_path(model, bad, b, [.1], force_scale_per_length=20.)
    with pytest.raises(TMCError):
        solve_initial_tangent(model, b, b, k_out=-1)
    with pytest.raises(TypeError):
        solve_displacement_path(model, b, b, [.1])


def test_missing_physical_support_is_explicit_failure():
    model = rectangular_model(1, 1, 1, 1, E=1)
    b = np.zeros(model.ndof)
    b[[2, 6]] = .5
    result = solve_displacement_path(model, b, b, [.1], force_scale_per_length=20.)
    assert result["failure"]["code"] == "insufficient_support"
    assert result["target_metrics"] is None


def test_real_tmc_small_path_tangent_limit_and_A_B_A():
    model = rectangular_model(2, 1, 2, 1, E=1, alpha=1e-6, thickness=20,
                              fixed_dofs=[0, 1, 6, 7])
    b_in, b_out = np.zeros(model.ndof), np.zeros(model.ndof)
    b_in[[4, 10]] = .5
    b_out[[4, 10]] = -.5
    linear = solve_initial_tangent(model, b_in, b_out)
    settings = DisplacementSettings(minimum_increment=1e-5/16)
    first = solve_displacement_path(model, b_in, b_out, [1e-5], settings=settings, force_scale_per_length=20.)
    other = solve_displacement_path(model, b_in, b_out, [2e-5], settings=settings, force_scale_per_length=20.)
    repeat = solve_displacement_path(model, b_in, b_out, [1e-5], settings=settings, force_scale_per_length=20.)
    assert first["status"] == other["status"] == repeat["status"] == "success"
    np.testing.assert_array_equal(first["u"], repeat["u"])
    assert first["R_input"] == repeat["R_input"]
    assert not np.array_equal(first["u"], other["u"])
    np.testing.assert_allclose(first["u"]/1e-5, linear["u"], rtol=1e-4, atol=1e-6)
    assert first["R_input"]/1e-5 == pytest.approx(linear["R_input"], rel=1e-4)
    final = first["target_metrics"]
    assert final["minimum_J"] > 0 and final["relative_residual"] <= 1e-9
    assert abs(final["constraint_residual"]) <= 1e-15
    assert final["relative_global_force_balance"] <= 1e-6
    np.testing.assert_array_equal(first["u"][model.fixed_dofs], 0)
