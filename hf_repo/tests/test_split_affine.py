"""Independent spring laws exercise affine split stages without an FE solve."""
from math import fsum

import numpy as np
import pytest
from scipy import sparse

from hf_eval import split_affine as control
from hf_eval.prescribed import PrescribedSettings
from hf_eval.split_state import SplitDisplacement
from hf_eval.tmc import rectangular_model, TMCError
from hf_eval.tmc_kernel import KernelError


def problem(monkeypatch, *, cubic=0., invalid_above=None, nonsymmetric=False):
    fixed = [0, 2, 4, 6, 8, 10, 1, 3, 9, 11]
    model = rectangular_model(1, 2, 1, 2, E=1., fixed_dofs=fixed)
    motion = np.zeros(12)
    motion[[1, 3]] = 1.
    shape = motion.copy()
    shape[[5, 7]] = [.75, .25]
    top = np.zeros(12)
    top[[9, 11]] = 1.
    edges = [(1, 5, 2.), (5, 9, 8.), (3, 7, 3.), (7, 11, 5.)]
    matrix = np.zeros((12, 12))
    for a, b, stiffness in edges:
        vector = np.zeros(12)
        vector[a], vector[b] = 1., -1.
        matrix += stiffness*np.outer(vector, vector)
    if nonsymmetric:
        matrix[5, :], matrix[7, :] = 0., 0.
        matrix[5, [1, 5, 7]] = [-2., 3., 1.]
        matrix[7, [3, 7]] = [-4., 7.]
    counts = np.bincount(model.edofs.ravel(), minlength=model.ndof)
    calls = []

    def assembled(actual_model, state, tangent=True):
        assert actual_model is model
        calls.append((state.copy(), tangent))
        if invalid_above is not None and state.lift[1] > invalid_above:
            raise KernelError("independent injected inadmissible state", code="invalid_J")
        # The manufactured force is defined from both stored components, with
        # an analytic spring tangent. The production FE kernel is never called.
        force = matrix@state.lift + matrix@state.fluctuation
        stiffness = matrix.copy()
        for a, b, _ in edges:
            v = np.zeros(12)
            v[a], v[b] = 1., -1.
            stretch = fsum((state.lift[a], state.fluctuation[a], -state.lift[b], -state.fluctuation[b]))
            force += cubic*stretch**3*v
            stiffness += 3*cubic*stretch**2*np.outer(v, v)
        local = force[model.edofs]/counts[model.edofs]
        fields = dict(residual=local, material_residual=local,
                      regularization_residual=np.zeros_like(local),
                      J=np.ones((model.ne, 9)), material_energy=np.zeros(model.ne),
                      timing_seconds=dict(kernel_and_transfer=0., assembly=0.))
        return sparse.csc_matrix(stiffness) if tangent else None, force, fields

    monkeypatch.setattr(control, "assemble_split", assembled)
    return dict(model=model, direction=motion, shape=shape,
                groups={"bottom": motion.copy(), "top": top}, calls=calls)


def run(data, targets, *, origin=None, base=None, initial_state=None, shape=None,
        direction=None, **kwargs):
    ndof = data["model"].ndof
    return control.solve_split_affine_path(
        data["model"], np.zeros(ndof) if base is None else base,
        data["direction"] if direction is None else direction,
        np.zeros(ndof) if origin is None else origin,
        data["shape"] if shape is None else shape, targets,
        initial_state=initial_state, reaction_groups=data["groups"],
        force_scale_per_length=1., **kwargs)


def result_state(result):
    return SplitDisplacement(result["u_lift"], result["u_fluctuation"])


def physical(state):
    return np.array([fsum(pair) for pair in zip(state.lift, state.fluctuation)])


def test_nonzero_free_origin_is_equilibrated_at_stage_zero(monkeypatch):
    data = problem(monkeypatch)
    base = .125*data["direction"]
    origin = .125*data["shape"]
    origin[[5, 7]] = [2., -3.]
    accepted = []
    out = run(data, [0., .125], base=base, origin=origin, on_accept=accepted.append)
    assert out["status"] == "success"
    assert accepted[0]["d"] == 0 and accepted[0]["newton_checks"] > 1
    assert out["linear_solve_diagnostics"][0]["phase"] == "corrector"
    np.testing.assert_array_equal(data["calls"][0][0].lift, origin)
    np.testing.assert_array_equal(data["calls"][0][0].fluctuation, 0.)
    np.testing.assert_allclose(physical(result_state(out))[[5, 7]], [.05, .09375], atol=2e-15, rtol=0)
    assert out["drive_force"] == pytest.approx((1.6+1.875)*.25)
    assert out["accepted_steps"][0]["relative_residual"] <= 1e-9


def test_two_stages_from_nonzero_state_match_monolithic_two_chain_solution(monkeypatch):
    data = problem(monkeypatch)
    full = run(data, [0., .125, .1875, .25])
    first = run(data, [0., .125])
    initial = result_state(first)
    initial_hash = control.state_hash(initial)
    second = run(data, [0., .0625, .125], origin=initial.lift,
                 base=.125*data["direction"], initial_state=initial)
    assert full["status"] == first["status"] == second["status"] == "success"
    assert second["initial_state_sha256"] == initial_hash
    assert second["accepted_steps"][0]["state_sha256"] == initial_hash
    assert second["accepted_steps"][0]["newton_checks"] == 1
    assert second["timing_seconds"]["predictors"] == 2
    for row in second["accepted_steps"]:
        total = .125+row["d"]
        np.testing.assert_allclose(physical(SplitDisplacement(row["u_lift"], row["u_fluctuation"]))[[5, 7]],
                                   [.2*total, .375*total], atol=2e-16, rtol=0)
        assert row["drive_force"] == pytest.approx(3.475*total)
    np.testing.assert_array_equal(second["u_lift"], full["u_lift"])
    np.testing.assert_allclose(second["u_fluctuation"], full["u_fluctuation"], atol=2e-16, rtol=0)
    assert control.state_hash(initial) == initial_hash
    assert second["state_sha256"] == control.state_hash(result_state(second))
    assert not any(item["phase"] == "corrector" for item in second["linear_solve_diagnostics"])


def test_new_stage_can_change_direction_and_free_lift_extension_without_rebase(monkeypatch):
    data = problem(monkeypatch)
    first = run(data, [0., .125])
    initial = result_state(first)
    direction = data["direction"].copy()
    direction[[1, 3]] = [-.5, 2.]
    shape = direction.copy()
    shape[[5, 7]] = [-1., 3.]
    out = run(data, [0., .0625], base=.125*data["direction"], origin=initial.lift,
              initial_state=initial, direction=direction, shape=shape)
    assert out["status"] == "success"
    assert out["accepted_steps"][0]["state_sha256"] == control.state_hash(initial)
    left, right = .125-.5*.0625, .125+2*.0625
    np.testing.assert_allclose(physical(result_state(out))[[5, 7]], [.2*left, .375*right], atol=2e-16, rtol=0)
    assert out["drive_force"] == pytest.approx(-.5*1.6*left+2*1.875*right)
    assert out["reaction_groups"]["bottom"].shape == (12,)
    assert out["target_metrics"]["group_reactions"]["bottom"]["constraint_force"] == pytest.approx(1.6*left+1.875*right)


def test_initial_state_is_not_trusted_as_equilibrated(monkeypatch):
    data = problem(monkeypatch)
    origin = .125*data["shape"]
    w = np.zeros(12)
    w[[5, 7]] = [.25, -.5]
    initial = SplitDisplacement(origin, w)
    before = control.state_hash(initial)
    out = run(data, [0.], base=.125*data["direction"], origin=origin, initial_state=initial)
    assert out["status"] == "success" and len(out["accepted_steps"]) == 1
    assert out["accepted_steps"][0]["newton_checks"] > 1
    assert out["initial_state_sha256"] == before != out["state_sha256"]
    np.testing.assert_allclose(physical(result_state(out))[[5, 7]], [.025, .046875], atol=2e-16, rtol=0)
    assert control.state_hash(initial) == before


def test_stage_zero_preserves_signed_zeros_and_sub_ulp_fluctuation(monkeypatch):
    data = problem(monkeypatch)
    origin = .125*data["direction"]
    origin[[5, 7]] = [.025, .046875]
    origin[0] = -0.
    w = np.zeros(12)
    w[0], w[5] = -0., 2.**-60
    initial = SplitDisplacement(origin, w)
    assert initial.u_display[5] == origin[5]
    out = run(data, [0.], base=.125*data["direction"], origin=origin, initial_state=initial)
    assert out["status"] == "success"
    assert out["initial_state_sha256"] == out["state_sha256"] == control.state_hash(initial)
    assert out["u_lift"].tobytes() == initial.lift.tobytes()
    assert out["u_fluctuation"].tobytes() == initial.fluctuation.tobytes()
    assert data["calls"][0][0].lift.tobytes() == initial.lift.tobytes()


def test_failed_increment_rolls_back_to_accepted_warm_start(monkeypatch):
    data = problem(monkeypatch, invalid_above=.125)
    first = run(data, [0., .125])
    initial = result_state(first)
    out = run(data, [0., .125], base=.125*data["direction"], origin=initial.lift,
              initial_state=initial, settings=PrescribedSettings(max_bisections=0))
    assert out["status"] == "failed" and out["failure"]["code"] == "invalid_J"
    assert out["target_metrics"] is None and out["reached_displacement"] == 0
    assert out["last_accepted_state"]["state_sha256"] == control.state_hash(initial)
    assert out["state_sha256"] == control.state_hash(initial)
    assert all(row["rollback_bitwise_equal"] for row in out["failed_attempts"])


def test_failed_stage_zero_preserves_input_and_reports_no_accepted_state(monkeypatch):
    data = problem(monkeypatch, invalid_above=.1)
    origin = .125*data["shape"]
    initial = SplitDisplacement(origin, np.zeros(12))
    out = run(data, [0., .125], base=.125*data["direction"], origin=origin, initial_state=initial)
    assert out["status"] == "failed" and out["failure"]["code"] == "invalid_J"
    assert out["accepted_steps"] == []
    assert out["target_metrics"] is out["last_accepted_state"] is out["drive_force"] is None
    assert out["state_sha256"] == out["initial_state_sha256"] == control.state_hash(initial)
    assert out["maximum_bisection_depth"] == 0


def test_bisection_keeps_latest_accepted_substep_on_failure(monkeypatch):
    data = problem(monkeypatch, invalid_above=.26)
    first = run(data, [0., .125])
    initial = result_state(first)
    out = run(data, [0., .2], base=.125*data["direction"], origin=initial.lift,
              initial_state=initial, settings=PrescribedSettings(max_bisections=2, minimum_increment=.001))
    assert out["status"] == "failed"
    assert out["reached_displacement"] == pytest.approx(.1)
    assert len(out["accepted_steps"]) == 2
    last = out["last_accepted_state"]
    assert not last["is_original_target"] and last["original_target_displacement"] == .2
    assert last["bisection_depth"] == 1
    assert out["state_sha256"] == last["state_sha256"]
    assert all(row["rollback_bitwise_equal"] for row in out["failed_attempts"])


def test_nonlinear_independent_springs_retain_original_fixed_scale_armijo(monkeypatch):
    data = problem(monkeypatch, cubic=100.)
    out = run(data, [0., .05, .1])
    assert out["status"] == "success" and out["trials"]
    for trial in out["trials"]:
        if trial["accepted"]:
            assert trial["phi"] <= (1-2e-4*trial["factor"])*trial["base_phi"]
    for row in out["accepted_steps"]:
        assert row["relative_residual"] <= 1e-9
        assert row["prescribed_displacement_error_max"] <= 1e-10*max(abs(row["d"]), 1e-6)
    assert any(t["fixed_residual_scale"] != t["recomputed_trial_scale"] for t in out["trials"])


def test_unsymmetric_linear_tangent_uses_general_lu(monkeypatch):
    data = problem(monkeypatch, nonsymmetric=True)
    origin = .125*data["shape"]
    out = run(data, [0., .125], base=.125*data["direction"], origin=origin)
    assert out["status"] == "success"
    np.testing.assert_allclose(physical(result_state(out))[[5, 7]], .25*np.array([10/21, 4/7]), atol=2e-16, rtol=0)
    assert all(row["factorization"] == "general sparse LU" and not row["symmetrized"] for row in out["linear_solve_diagnostics"])
    assert all(row["relative_tangent_asymmetry"] > 0 for row in out["linear_solve_diagnostics"])


def test_callback_and_returned_arrays_cannot_mutate_input_state(monkeypatch):
    data = problem(monkeypatch)
    first = run(data, [0., .125])
    initial = result_state(first)
    before = control.state_hash(initial)
    def tamper(row):
        row["u_lift"][:] = 99
        row["u_fluctuation"][:] = -99
        row["group_reactions"]["bottom"]["constraint_force"] = -999
    out = run(data, [0., .125], base=.125*data["direction"], origin=initial.lift,
              initial_state=initial, on_accept=tamper)
    assert out["status"] == "success" and out["drive_force"] > 0
    assert out["accepted_steps"][0]["state_sha256"] == before
    out["initial_u_lift"][:] = 100
    out["initial_u_fluctuation"][:] = 100
    assert control.state_hash(initial) == before


def test_persistence_failure_preserves_newly_accepted_state(monkeypatch):
    data = problem(monkeypatch)
    def fail_write(row):
        raise OSError("independent injected storage failure")
    out = run(data, [0., .125], on_accept=fail_write)
    assert out["failure"]["code"] == "persistence_failure"
    assert len(out["accepted_steps"]) == 1 and out["last_accepted_state"]["d"] == 0
    assert out["target_metrics"] is None


def test_bounded_backtracking_rejection_retains_unequilibrated_start(monkeypatch):
    data = problem(monkeypatch, cubic=100.)
    original = control.assemble_split
    def reject_trials(model, state, tangent=True):
        if not tangent:
            raise KernelError("injected illegal line-search state", code="invalid_J")
        return original(model, state, tangent=tangent)
    monkeypatch.setattr(control, "assemble_split", reject_trials)
    origin = .125*data["shape"]
    initial = SplitDisplacement(origin, np.zeros(12))
    out = run(data, [0., .125], origin=origin, base=.125*data["direction"], initial_state=initial,
              settings=PrescribedSettings(max_backtracks=2, max_bisections=0))
    assert out["failure"]["code"] == "backtracking_failed"
    assert len(out["trials"]) == 3 and not any(row["accepted"] for row in out["trials"])
    assert out["accepted_steps"] == [] and out["target_metrics"] is None
    assert out["state_sha256"] == out["initial_state_sha256"] == control.state_hash(initial)


def test_timeout_before_first_assembly_preserves_initial_state(monkeypatch):
    data = problem(monkeypatch)
    ticks = iter(range(100))
    monkeypatch.setattr(control, "perf_counter", lambda: next(ticks))
    out = run(data, [0., .1], settings=PrescribedSettings(time_limit_seconds=.01))
    assert out["failure"]["code"] == "time_limit"
    assert data["calls"] == [] and out["accepted_steps"] == []
    assert out["state_sha256"] == out["initial_state_sha256"]


@pytest.mark.parametrize("targets", [[], [.1], [0., 0.], [0., -.1], [0., np.inf], [0., np.nan], [[0.]]])
def test_invalid_targets_rejected_before_assembly(monkeypatch, targets):
    data = problem(monkeypatch)
    with pytest.raises(TMCError):
        run(data, targets)
    assert data["calls"] == []


@pytest.mark.parametrize("which,bad", [("origin", np.ones(11)), ("origin", np.full(12, np.nan)),
                                       ("shape", np.ones(13)), ("shape", np.full(12, np.inf)),
                                       ("origin", np.zeros(12, dtype=complex)),
                                       ("shape", np.zeros(12, dtype=bool))])
def test_invalid_origin_or_shape_rejected_before_assembly(monkeypatch, which, bad):
    data = problem(monkeypatch)
    with pytest.raises(TMCError):
        run(data, [0.], **{which: bad})
    assert data["calls"] == []


@pytest.mark.parametrize("which", ["origin", "shape"])
def test_fixed_origin_and_shape_must_match_prescribed_contract(monkeypatch, which):
    data = problem(monkeypatch)
    bad = np.zeros(12) if which == "origin" else data["shape"].copy()
    bad[1] += 1
    with pytest.raises(TMCError, match="match prescribed"):
        run(data, [0.], **{which: bad})
    assert data["calls"] == []


@pytest.mark.parametrize("initial", [np.zeros(12), {"lift": np.zeros(12)},
                                     SplitDisplacement(np.zeros(2), np.zeros(2))])
def test_invalid_initial_state_type_or_size_rejected(monkeypatch, initial):
    data = problem(monkeypatch)
    with pytest.raises(TMCError, match="SplitDisplacement"):
        run(data, [0.], initial_state=initial)
    assert data["calls"] == []


def test_initial_state_cannot_be_implicitly_rebased_even_if_display_is_identical(monkeypatch):
    data = problem(monkeypatch)
    lift, w = np.zeros(12), np.zeros(12)
    lift[5], w[5] = .125, -.125
    initial = SplitDisplacement(lift, w)
    assert np.all(initial.u_display == 0)
    with pytest.raises(TMCError, match="bit for bit"):
        run(data, [0.], initial_state=initial)
    assert data["calls"] == []


def test_initial_lift_signed_zero_difference_is_not_bitwise_equal(monkeypatch):
    data = problem(monkeypatch)
    origin = np.zeros(12)
    origin[5] = -0.
    with pytest.raises(TMCError, match="bit for bit"):
        run(data, [0.], origin=origin, initial_state=SplitDisplacement(np.zeros(12), np.zeros(12)))


def test_initial_fixed_fluctuation_must_be_exactly_zero(monkeypatch):
    data = problem(monkeypatch)
    w = np.zeros(12)
    w[1] = np.nextafter(0., 1.)
    with pytest.raises(TMCError, match="zero on fixed"):
        run(data, [0.], initial_state=SplitDisplacement(np.zeros(12), w))


def test_corrupted_state_component_type_is_rejected_before_casting(monkeypatch):
    data = problem(monkeypatch)
    initial = SplitDisplacement(np.zeros(12), np.zeros(12))
    object.__setattr__(initial, "lift", np.zeros(12, dtype=np.int64))
    with pytest.raises(TMCError, match="remain binary64"):
        run(data, [0.], initial_state=initial)
    assert data["calls"] == []


def test_overflow_during_lift_advance_preserves_last_accepted_state(monkeypatch):
    data = problem(monkeypatch)
    shape = data["shape"].copy()
    shape[5] = np.finfo(float).max
    out = run(data, [0., 2.], shape=shape, settings=PrescribedSettings(max_bisections=0))
    assert out["failure"]["code"] == "nonfinite" and out["reached_displacement"] == 0
    assert out["target_metrics"] is None
    assert out["state_sha256"] == out["accepted_steps"][0]["state_sha256"]
