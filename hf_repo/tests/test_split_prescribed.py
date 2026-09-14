"""Controller-specific checks with an independent two-chain linear problem."""
import numpy as np
import pytest
from scipy import sparse

from hf_eval import split_prescribed as control
from hf_eval.prescribed import PrescribedSettings
from hf_eval.split_state import SplitDisplacement
from hf_eval.tmc import rectangular_model, TMCError
from hf_eval.tmc_kernel import KernelError


def problem(monkeypatch, invalid_above=None):
    fixed = [0, 2, 4, 6, 8, 10, 1, 3, 9, 11]
    m = rectangular_model(1, 2, 1, 2, E=1, fixed_dofs=fixed)
    base = np.zeros(12)
    motion = np.zeros(12)
    motion[[1, 3]] = 1
    shape = motion.copy()
    shape[[5, 7]] = [.75, .25]
    top = np.zeros(12)
    top[[9, 11]] = 1
    K = np.zeros((12, 12))
    for a, b, stiffness in [(1, 5, 2.), (5, 9, 8.), (3, 7, 3.), (7, 11, 5.)]:
        v = np.zeros(12)
        v[a], v[b] = 1, -1
        K += stiffness * np.outer(v, v)
    counts = np.bincount(m.edofs.ravel(), minlength=12)
    calls = []

    def assembled(model, state, tangent=True):
        assert model is m
        calls.append((state.copy(), tangent))
        if invalid_above is not None and state.lift[1] > invalid_above:
            raise KernelError("injected illegal trial", code="invalid_J")
        # Separate linear action defines this manufactured force law. This
        # test does not use the nonlinear production kernel to define truth.
        f = K @ state.lift + K @ state.fluctuation
        local = f[m.edofs] / counts[m.edofs]
        fields = dict(residual=local, material_residual=local,
                      regularization_residual=np.zeros_like(local),
                      J=np.ones((2, 9)), material_energy=np.zeros(2),
                      timing_seconds=dict(kernel_and_transfer=0., assembly=0.))
        return sparse.csc_matrix(K) if tangent else None, f, fields

    monkeypatch.setattr(control, "assemble_split", assembled)
    return m, base, motion, shape, {"bottom":motion.copy(), "top":top}, calls


def run(data, targets, **kw):
    m, base, motion, shape, groups, _ = data
    return control.solve_split_prescribed_path(m, base, motion, shape, targets,
        reaction_groups=groups, force_scale_per_length=1., **kw)


def test_full_lift_predictor_does_not_double_rebase_and_preserves_group_sign(monkeypatch):
    data = problem(monkeypatch)
    out = run(data, [0., .125, .25])
    assert out["status"] == "success"
    # Analytic equilibrium of the two separate chains: 2/(2+8), 3/(3+5).
    for row in out["accepted_steps"]:
        d = row["d"]
        np.testing.assert_allclose(row["u_lift"][[5,7]] + row["u_fluctuation"][[5,7]],
                                   [.2*d,.375*d], rtol=0, atol=2e-16)
        np.testing.assert_allclose(row["u_fluctuation"][[5,7]], [-.55*d,.125*d], rtol=0, atol=2e-16)
        assert row["group_reactions"]["bottom"]["constraint_force"] == pytest.approx((1.6+1.875)*d)
        assert row["group_reactions"]["top"]["constraint_force"] == pytest.approx(-(1.6+1.875)*d)
        assert np.all(row["u_fluctuation"][data[0].fixed_dofs] == 0)
    assert not any(r["phase"] == "corrector" for r in out["linear_solve_diagnostics"])
    assert out["target_metrics"]["d"] == .25


def test_changing_free_lift_extension_leaves_the_solved_linear_physical_state(monkeypatch):
    data = problem(monkeypatch)
    first = run(data, [0., .25])
    other = list(data)
    other[3] = data[3].copy()
    other[3][[5,7]] = [-.25, 1.25]
    second = run(other, [0., .25])
    assert first["status"] == second["status"] == "success"
    np.testing.assert_allclose(first["u_display"], second["u_display"], atol=2e-16, rtol=0)
    assert not np.array_equal(first["u_fluctuation"], second["u_fluctuation"])


def test_failed_target_restores_both_components_and_does_not_fabricate_metrics(monkeypatch):
    data = problem(monkeypatch, invalid_above=.125)
    out = run(data, [0., .125, .25], settings=PrescribedSettings(max_bisections=0))
    assert out["status"] == "failed" and out["target_metrics"] is None
    assert out["reached_displacement"] == .125
    last = out["last_accepted_state"]
    for key in ("u_lift", "u_fluctuation", "u_display"):
        np.testing.assert_array_equal(out[key], last[key])
    assert out["last_attempt_candidate"]["d"] == .25
    assert out["failed_attempts"][-1]["rollback_bitwise_equal"]
    assert out["failure"]["code"] == "invalid_J"


def test_callback_cannot_mutate_solver_or_stored_components(monkeypatch):
    def tamper(row):
        row["u_lift"][:] = 900
        row["u_fluctuation"][:] = -800
        row["u_display"][:] = 100
    out = run(problem(monkeypatch), [0., .125], on_accept=tamper)
    assert out["status"] == "success"
    assert np.max(np.abs(out["u_lift"])) <= .125
    assert np.max(np.abs(out["u_fluctuation"])) < .125


def test_conflicting_fixed_lift_is_rejected(monkeypatch):
    data = list(problem(monkeypatch))
    data[3][1] = 2
    with pytest.raises(TMCError, match="lift shape"):
        run(data, [0., .125])


def test_measurement_retains_small_component_after_cancelling_large_offset():
    state = SplitDisplacement(np.array([0., .125]), np.array([0., 2.**-60]))
    assert control.split_linear_measurement(state, [0.,1.], offset=-.125) == 2.**-60
    assert state.u_display[1] - .125 == 0


def test_schema_hash_binds_each_component_not_just_display():
    a = SplitDisplacement(np.array([0., .125]), np.array([0., 2.**-60]))
    b = SplitDisplacement(np.array([0., .125]), np.zeros(2))
    assert np.array_equal(a.u_display,b.u_display)
    assert control.state_hash(a) != control.state_hash(b)


def test_candidate_overflow_retains_last_accepted_state(monkeypatch):
    data = list(problem(monkeypatch))
    data[3][5] = np.finfo(float).max
    out = run(data, [0., 2.], settings=PrescribedSettings(max_bisections=0))
    assert out["status"] == "failed" and out["failure"]["code"] == "nonfinite"
    assert out["target_metrics"] is None and out["reached_displacement"] == 0
    assert np.all(out["u_lift"] == 0) and np.all(out["u_fluctuation"] == 0)


def test_new_failed_base_does_not_inherit_previous_corrector(monkeypatch):
    data = problem(monkeypatch)
    original = control.assemble_split

    def wrong_tangent(model, state, tangent=True):
        K, f, fields = original(model, state, tangent)
        return 2*K if tangent else None, f, fields

    monkeypatch.setattr(control, "assemble_split", wrong_tangent)
    # A mismatched predictor alone still gives the exact homogeneous linear
    # direction. Suppress its starting K by a prescribed nonzero base at d=0.
    data = list(data)
    data[1][[1,3]] = .125
    out = run(data, [0.], settings=PrescribedSettings(max_checks=2, max_bisections=0))
    assert out["status"] == "failed" and out["failure"]["code"] == "newton_limit"
    assert out["last_attempt_candidate"]["newton_check"] == 2
    assert out["last_corrector"] is None
