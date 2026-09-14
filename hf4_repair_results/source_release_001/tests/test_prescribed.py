"""Affine Dirichlet algebra/failure tests and tiny homogeneous compression.

Manufactured spring systems isolate the controller from the constitutive kernel.
Only the final two tests call actual TMC mechanics; no HF-4 contact path is run.
"""
import os

os.environ["JAX_ENABLE_X64"] = "true"
os.environ["JAX_PLATFORMS"] = "cpu"

import numpy as np
import pytest
from scipy import sparse

import hf_eval.prescribed as prescribed
from hf_eval.prescribed import PrescribedSettings, solve_prescribed_path
from hf_eval.tmc import TMCError, rectangular_model
from hf_eval.tmc_kernel import KernelError


def model_and_motion():
    fixed = [0, 2, 4, 6, 8, 10, 1, 3, 9, 11]
    model = rectangular_model(1, 2, 1, 2, E=1, nu=.3, alpha=1e-6, fixed_dofs=fixed)
    base, direction, top = np.zeros(12), np.zeros(12), np.zeros(12)
    direction[[1, 3]], top[[9, 11]] = 1., 1.
    return model, base, direction, {"bottom_platen": direction.copy(), "top_platen": top}


def install_springs(monkeypatch, model, *, cubic=0., invalid_above=None, singular=False, nonsymmetric=False):
    """Two independent chains; exact bottom-to-top stiffnesses 1.6 and 1.875."""
    edges = [(1, 5, 2.), (5, 9, 8.), (3, 7, 3.), (7, 11, 5.)]
    initial = np.zeros((12, 12))
    for a, b, k in edges:
        v = np.zeros(12)
        v[a], v[b] = 1., -1.
        initial += k * np.outer(v, v)
    if nonsymmetric:
        # Deliberately nonconservative manufactured force. Its exact free
        # solution is [10/21,4/7]*d; no physical-contact interpretation is made.
        initial[5, :] = 0.
        initial[7, :] = 0.
        initial[5, [1, 5, 7]] = [-2., 3., 1.]
        initial[7, [3, 7]] = [-4., 7.]
    if singular:
        initial[:] = 0.
    counts = np.bincount(model.edofs.ravel(), minlength=model.ndof)

    def assemble(actual_model, u, tangent=True):
        assert actual_model is model
        if invalid_above is not None and u[1] > invalid_above:
            raise KernelError("manufactured invalid determinant", code="invalid_J", details={"u1": float(u[1])})
        force = initial @ u
        tangent_matrix = initial.copy()
        energy = .5 * float(u @ initial @ u)
        for a, b, _ in edges:
            v = np.zeros(12)
            v[a], v[b] = 1., -1.
            stretch = u[a] - u[b]
            force += cubic * stretch**3 * v
            tangent_matrix += 3 * cubic * stretch**2 * np.outer(v, v)
            energy += .25 * cubic * stretch**4
        local_force = force[model.edofs] / counts[model.edofs]
        fields = {"residual": local_force, "material_residual": .8 * local_force,
                  "regularization_residual": .2 * local_force, "J": np.ones((model.ne, 9)),
                  "F": np.broadcast_to(np.eye(2), (model.ne, 9, 2, 2)).copy(),
                  "material_energy": np.full(model.ne, energy / model.ne),
                  "timing_seconds": {"kernel_and_transfer": 0., "assembly": 0.}}
        return sparse.csc_matrix(tangent_matrix) if tangent else None, force, fields

    monkeypatch.setattr(prescribed, "assemble", assemble)
    return initial


def run(model, base, direction, groups, targets, **kwargs):
    return solve_prescribed_path(model, base, direction, targets,
        reaction_groups=groups, force_scale_per_length=1., **kwargs)


def test_affine_nonzero_prescribed_values_predict_free_solution_and_reactions(monkeypatch):
    model, base, direction, groups = model_and_motion()
    install_springs(monkeypatch, model)
    base[[1, 3]] = .025
    result = run(model, base, direction, groups, [0., .1, .2])
    assert result["status"] == "success"
    assert result["reference_state"] == "prescribed_base_at_zero_target"
    for state in result["accepted_steps"]:
        total_motion = .025 + state["d"]
        np.testing.assert_allclose(state["u"][[5, 7]], [.2*total_motion, .375*total_motion], rtol=1e-12, atol=1e-14)
        np.testing.assert_array_equal(state["u"][model.fixed_dofs], (base + state["d"]*direction)[model.fixed_dofs])
        assert state["prescribed_displacement_error_max"] == 0
        assert state["drive_force"] == pytest.approx(3.475 * total_motion, rel=1e-12)
        assert state["group_reactions"]["bottom_platen"]["constraint_force"] > 0
        assert state["group_reactions"]["top_platen"]["constraint_force"] == pytest.approx(-state["drive_force"], rel=1e-12)
        assert state["drive_force_model_on_device"] == -state["drive_force"]
        assert state["relative_residual"] <= 1e-9
    predictor = [r for r in result["linear_solve_diagnostics"] if r["phase"] == "predictor"]
    assert len(predictor) == 2
    assert max(r["relative_linear_residual"] for r in predictor) < 1e-12


def test_group_virtual_work_components_and_duplicate_measurements_do_not_double_balance(monkeypatch):
    model, base, direction, groups = model_and_motion()
    install_springs(monkeypatch, model)
    groups["duplicate_bottom"] = groups["bottom_platen"].copy()
    result = run(model, base, direction, groups, [.1])
    state = result["target_metrics"]
    assert result["status"] == "success"
    for item in state["group_reactions"].values():
        assert item["model_force"] == -item["constraint_force"]
        assert item["virtual_work_generalized_force"] == pytest.approx(item["constraint_force"], rel=1e-12, abs=1e-14)
        assert item["material_constraint_force"] == pytest.approx(.8 * item["constraint_force"], rel=1e-12)
        assert item["regularization_constraint_force"] == pytest.approx(.2 * item["constraint_force"], rel=1e-12)
        assert item["material_virtual_work_generalized_force"] == pytest.approx(item["material_constraint_force"], rel=1e-12)
        assert item["regularization_virtual_work_generalized_force"] == pytest.approx(item["regularization_constraint_force"], rel=1e-12)
    assert state["group_reactions"]["duplicate_bottom"] == state["group_reactions"]["bottom_platen"]
    np.testing.assert_allclose(state["global_force_balance"], 0., atol=1e-14)
    np.testing.assert_allclose(state["material_internal_force"]+state["regularization_internal_force"], state["internal_force"], atol=1e-14)
    assert state["element_regularization_force"].shape == (2, 8)


def test_direction_is_not_normalized_and_model_on_device_sign_is_opposite(monkeypatch):
    model, base, direction, groups = model_and_motion()
    install_springs(monkeypatch, model)
    direction *= -2
    result = run(model, base, direction, groups, [.1])
    state = result["target_metrics"]
    assert result["status"] == "success"
    np.testing.assert_array_equal(state["u"][[1, 3]], [-.2, -.2])
    assert state["group_reactions"]["bottom_platen"]["constraint_force"] == pytest.approx(-.2*3.475)
    assert state["drive_force"] == pytest.approx(4*.1*3.475)
    assert state["drive_force_model_on_device"] == -state["drive_force"]


def test_nonsymmetric_free_matrix_and_predictor_sign(monkeypatch):
    model, base, direction, groups = model_and_motion()
    install_springs(monkeypatch, model, nonsymmetric=True)
    result = run(model, base, direction, groups, [.1])
    assert result["status"] == "success"
    np.testing.assert_allclose(result["u"][[5, 7]], .1*np.array([10/21, 4/7]), rtol=1e-12, atol=1e-14)
    assert result["linear_solve_diagnostics"][0]["relative_tangent_asymmetry"] > 0
    assert result["linear_solve_diagnostics"][0]["symmetrized"] is False


def test_zero_state_scale_and_fixed_scale_armijo_with_prescribed_values(monkeypatch):
    model, base, direction, groups = model_and_motion()
    install_springs(monkeypatch, model, cubic=100.)
    result = run(model, base, direction, groups, [0., .05, .1])
    assert result["status"] == "success"
    zero = result["accepted_steps"][0]
    assert zero["relative_residual"] == 0
    assert zero["residual_scale"] == 1e-8 * 1e-6
    assert result["trials"]
    for state in result["accepted_steps"]:
        expected = max(np.linalg.norm(state["internal_force"][model.free]),
                       np.linalg.norm(state["internal_force"][model.fixed_dofs]),
                       1e-8*max(abs(state["d"]), 1e-6))
        assert state["residual_scale"] == expected
    for trial in result["trials"]:
        if trial["accepted"]:
            assert trial["phi"] <= (1-2e-4*trial["factor"])*trial["base_phi"]
            assert trial["prescribed_displacement_error_max"] == 0.
    assert any(abs(t["fixed_residual_scale"]-t["recomputed_trial_scale"]) > 1e-6
               for t in result["trials"] if t["accepted"])


def test_failed_target_rolls_back_and_keeps_latest_verified_substep(monkeypatch):
    model, base, direction, groups = model_and_motion()
    install_springs(monkeypatch, model, invalid_above=.21)
    result = run(model, base, direction, groups, [0., .1, .3],
                 settings=PrescribedSettings(max_bisections=2, minimum_increment=.001))
    assert result["status"] == "failed" and result["target_metrics"] is None
    assert result["failure"]["code"] == "invalid_J"
    assert result["reached_displacement"] == pytest.approx(.2)
    assert result["last_accepted_state"]["original_target_displacement"] == .3
    assert result["last_accepted_state"]["is_original_target"] is False
    np.testing.assert_array_equal(result["u"], result["last_accepted_state"]["u"])
    assert all(r["rollback_bitwise_equal"] for r in result["failed_attempts"])


def test_singular_prediction_has_null_force_without_accepted_state(monkeypatch):
    model, base, direction, groups = model_and_motion()
    install_springs(monkeypatch, model, singular=True)
    result = run(model, base, direction, groups, [.1], settings=PrescribedSettings(max_bisections=0))
    assert result["failure"]["code"] == "singular_tangent"
    assert result["target_metrics"] is result["last_accepted_state"] is result["drive_force"] is None
    np.testing.assert_array_equal(result["u"], 0.)


def test_newton_limit_and_backtracking_failure_do_not_change_boundary_of_saved_state(monkeypatch):
    model, base, direction, groups = model_and_motion()
    install_springs(monkeypatch, model, cubic=100.)
    limited = run(model, base, direction, groups, [0., .05],
                  settings=PrescribedSettings(max_checks=1, max_bisections=0))
    assert limited["failure"]["code"] == "newton_limit"
    assert limited["reached_displacement"] == 0.
    np.testing.assert_array_equal(limited["u"], 0.)
    ordinary = prescribed.assemble

    def reject_trials(actual_model, u, tangent=True):
        if not tangent:
            raise KernelError("injected inadmissible trial", code="invalid_J")
        return ordinary(actual_model, u, tangent=tangent)

    monkeypatch.setattr(prescribed, "assemble", reject_trials)
    failed = run(model, base, direction, groups, [.05],
                 settings=PrescribedSettings(max_backtracks=2, max_bisections=0))
    assert failed["failure"]["code"] == "backtracking_failed"
    assert len(failed["trials"]) == 3 and not any(t["accepted"] for t in failed["trials"])
    np.testing.assert_array_equal(failed["u"], 0.)


def test_callback_arrays_and_nested_groups_are_isolated_and_oserror_preserves_acceptance(monkeypatch):
    model, base, direction, groups = model_and_motion()
    install_springs(monkeypatch, model, cubic=100.)
    ordinary = run(model, base, direction, groups, [.05, .1])

    def mutate(state):
        state["u"][:] = 999
        state["J"][:] = -1
        state["group_reactions"]["bottom_platen"]["constraint_force"] = 999

    observed = run(model, base, direction, groups, [.05, .1], on_accept=mutate)
    np.testing.assert_array_equal(ordinary["u"], observed["u"])
    assert ordinary["drive_force"] == observed["drive_force"]
    assert observed["accepted_steps"][0]["group_reactions"]["bottom_platen"]["constraint_force"] != 999

    def cannot_write(state):
        raise OSError("mock unavailable storage")

    failed = run(model, base, direction, groups, [.05, .1], on_accept=cannot_write)
    assert failed["failure"]["code"] == "persistence_failure"
    assert failed["reached_displacement"] == .05
    assert failed["last_accepted_state"] is not None and failed["target_metrics"] is None


def test_timeout_returns_failure_before_kernel(monkeypatch):
    model, base, direction, groups = model_and_motion()
    ticks = iter(range(100))
    monkeypatch.setattr(prescribed, "perf_counter", lambda: next(ticks))
    result = run(model, base, direction, groups, [.1], settings=PrescribedSettings(time_limit_seconds=.01))
    assert result["failure"]["code"] == "time_limit"
    assert result["timing_seconds"]["kernel_calls"] == 0
    assert result["target_metrics"] is result["last_accepted_state"] is None


@pytest.mark.parametrize("field,value", [("tolerance", np.nan), ("constraint_tolerance", 0),
    ("max_checks", 35.), ("max_backtracks", True), ("max_bisections", -1),
    ("minimum_increment", 0), ("time_limit_seconds", np.inf)])
def test_invalid_settings_rejected(field, value):
    with pytest.raises(TMCError):
        PrescribedSettings(**{field: value})


@pytest.mark.parametrize("targets", [[], [-.1], [.1, .1], [.2, .1], [np.nan], [.1+1j]])
def test_invalid_target_vectors_rejected(targets):
    model, base, direction, groups = model_and_motion()
    with pytest.raises(TMCError):
        run(model, base, direction, groups, targets)


def test_nonzero_base_requires_explicit_zero_state_and_free_dofs_cannot_be_prescribed():
    model, base, direction, groups = model_and_motion()
    base[1] = .01
    with pytest.raises(TMCError, match="first target zero"):
        run(model, base, direction, groups, [.1])
    base[5] = .01
    with pytest.raises(TMCError, match="free DOFs"):
        run(model, base, direction, groups, [0., .1])


def test_invalid_group_or_motion_is_rejected_without_silent_normalization():
    model, base, direction, groups = model_and_motion()
    free_group = np.zeros(12)
    free_group[5] = 1
    for bad in ({"bad": free_group}, {"": direction}, {"zero": np.zeros(12)}, {"bad": direction + 1j}):
        with pytest.raises(TMCError):
            run(model, base, direction, bad, [.1])
    with pytest.raises(TMCError):
        run(model, base, np.zeros(12), groups, [.1])
    with pytest.raises(TMCError):
        solve_prescribed_path(model, base, direction, [.1], force_scale_per_length=0.)
    with pytest.raises(TypeError):
        solve_prescribed_path(model, base, direction, [.1])


def test_missing_support_has_no_accepted_state():
    model = rectangular_model(1, 2, 1, 2, E=1, fixed_dofs=[1, 3])
    base, direction = np.zeros(12), np.zeros(12)
    direction[[1, 3]] = 1
    result = solve_prescribed_path(model, base, direction, [.1], force_scale_per_length=1.)
    assert result["failure"]["code"] == "insufficient_support"
    assert result["last_accepted_state"] is None and result["target_metrics"] is None


def test_fully_prescribed_homogeneous_cell_matches_analytic_force_without_free_lu():
    model = rectangular_model(1, 1, 1, 1, E=1, nu=.3, alpha=1e-6, thickness=2,
                              fixed_dofs=np.arange(8))
    base, direction, top = np.zeros(8), np.zeros(8), np.zeros(8)
    direction[[1, 3]], top[[5, 7]] = 1, 1
    result = solve_prescribed_path(model, base, direction, [0., .05, .1],
        reaction_groups={"bottom": direction, "top": top}, force_scale_per_length=2.)
    assert result["status"] == "success"
    lam, mu = model.lam[0], model.mu[0]
    for state in result["accepted_steps"]:
        stretch = 1-state["d"]
        pressure = mu*(1/stretch-stretch)-lam*np.log(stretch)/stretch
        assert state["drive_force"] == pytest.approx(2*pressure, rel=1e-11, abs=1e-13)
        assert state["group_reactions"]["top"]["constraint_force"] == pytest.approx(-2*pressure, rel=1e-11, abs=1e-13)
        np.testing.assert_allclose(state["J"], stretch, rtol=0, atol=1e-14)
        assert np.linalg.norm(state["regularization_internal_force"]) < 1e-18
        assert state["relative_residual"] == 0.
    assert all(r["factorization"] == "no free DOFs" for r in result["linear_solve_diagnostics"])


def test_homogeneous_free_interior_analytic_compression_and_A_B_A():
    model, base, direction, groups = model_and_motion()
    first = run(model, base, direction, groups, [0., .05, .1])
    other = run(model, base, direction, groups, [.15])
    repeat = run(model, base, direction, groups, [0., .05, .1])
    assert first["status"] == other["status"] == repeat["status"] == "success"
    np.testing.assert_array_equal(first["u"], repeat["u"])
    assert first["drive_force"] == repeat["drive_force"]
    assert not np.array_equal(first["u"], other["u"])
    expected_u = np.zeros(12)
    expected_u[1::2] = .1*(1-model.coordinates[:, 1]/2)
    np.testing.assert_allclose(first["u"], expected_u, rtol=1e-11, atol=1e-13)
    stretch = 1-.1/2
    pressure = model.mu[0]*(1/stretch-stretch)-model.lam[0]*np.log(stretch)/stretch
    assert first["drive_force"] == pytest.approx(pressure, rel=1e-11)
    assert first["target_metrics"]["relative_global_force_balance"] < 1e-11
