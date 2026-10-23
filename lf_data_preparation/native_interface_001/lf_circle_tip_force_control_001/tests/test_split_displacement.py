"""Independent port algebra, split arithmetic, rollback, and a tiny real Q1 case.

The injected residuals isolate controller algebra; they are not TMC material
examples. The final test uses the NumPy constitutive kernel and a scalar
homogeneous-stretch root instead of another finite-element solver.
"""
from fractions import Fraction
import os
import struct

# Match the existing displacement tests before importing the shared JAX module.
os.environ["JAX_ENABLE_X64"] = "true"
os.environ["JAX_PLATFORMS"] = "cpu"

import numpy as np
import pytest
from scipy import sparse
from scipy.optimize import brentq

import hf_eval.split_displacement as control
from hf_eval.displacement import DisplacementSettings
from hf_eval.split_displacement import (
    solve_split_displacement_path, split_average_measurement,
)
from hf_eval.split_state import SplitDisplacement
from hf_eval.tmc import rectangular_model
from hf_eval.tmc_kernel import KernelError


def one_cell():
    model = rectangular_model(1, 1, 1., 1., E=1., alpha=0.,
                              fixed_dofs=[0, 1, 4, 5])
    port = np.zeros(model.ndof)
    port[[2, 6]] = .5
    return model, port


def synthetic(model, *, cubic=0., nonsymmetric=False, invalid_above=None,
              reject_trials=False):
    matrix = np.diag([1., 1., 2., 3., 1., 1., 8., 5.])
    if nonsymmetric:
        matrix[2, 6] = 1.

    def assemble(actual_model, state, *, tangent=True):
        assert actual_model is model
        assert isinstance(state, SplitDisplacement)
        # Ordinary-sized synthetic states permit this display conversion; the
        # exact two-array measurement tests below do not use this fixture.
        u = state.lift + state.fluctuation
        if ((invalid_above is not None and u[2] > invalid_above)
                or (reject_trials and not tangent)):
            raise KernelError("injected inadmissible trial", code="invalid_J")
        force = matrix @ u + cubic * u**3
        tangent_matrix = matrix + np.diag(3 * cubic * u**2)
        local = force[model.edofs]
        return (sparse.csc_matrix(tangent_matrix) if tangent else None), force, {
            "residual": local, "material_residual": .8 * local,
            "regularization_residual": .2 * local, "J": np.ones((1, 9)),
            "material_energy": np.array([
                .5 * u @ matrix @ u + cubic / 4 * np.sum(u**4)]),
            "timing_seconds": {"kernel_and_transfer": 0., "assembly": 0.},
        }

    return matrix, assemble


def physical(record):
    return record["u_lift"] + record["u_fluctuation"]


def test_average_port_keeps_unequal_node_motion_and_actuator_sign():
    model, port = one_cell()
    _, assembler = synthetic(model)
    result = solve_split_displacement_path(
        model, port, port, [0., .1, .2], assembler=assembler,
        force_scale_per_length=20.)
    assert result["status"] == "success"
    final = result["target_metrics"]
    np.testing.assert_allclose(physical(final)[[2, 6]], [.32, .08],
                               rtol=1e-12, atol=1e-14)
    assert final["R_input"] == pytest.approx(1.28, rel=1e-12)
    assert final["q_in"] == pytest.approx(.2)
    assert final["physical_mean_target_mm"] == .2
    # Binding both nodes to .2 would give R=2 and a different deformation.
    assert abs(final["R_input"] - 2.) > .5
    np.testing.assert_allclose(final["input_force"], port * final["R_input"])
    np.testing.assert_allclose(final["material_internal_force"]
                               + final["regularization_internal_force"],
                               final["internal_force"], atol=1e-14)
    for record in result["accepted_steps"]:
        assert abs(record["constraint_residual"]) <= record["constraint_bound"]
        assert record["relative_residual"] <= 1e-9


def test_nonsymmetric_kkt_and_rank_one_output_spring_match_dense_equations():
    model, port = one_cell()
    matrix, assembler = synthetic(model, nonsymmetric=True)
    output = np.zeros(model.ndof)
    output[[2, 6]] = [.25, .75]
    stiffness, target = 5., .2
    free = model.free
    total = matrix + stiffness * np.outer(output, output)
    augmented = np.block([
        [total[np.ix_(free, free)], -port[free, None]],
        [port[None, free], np.zeros((1, 1))],
    ])
    expected = np.linalg.solve(augmented, np.r_[np.zeros(len(free)), target])
    result = solve_split_displacement_path(
        model, port, output, [0., target], stiffness, assembler=assembler,
        force_scale_per_length=20.)
    assert result["status"] == "success"
    final = result["target_metrics"]
    np.testing.assert_allclose(physical(final)[free], expected[:-1],
                               rtol=1e-12, atol=1e-14)
    assert final["R_input"] == pytest.approx(expected[-1], rel=1e-12)
    q_out = float(output @ physical(final))
    np.testing.assert_allclose(final["spring_force_on_structure"],
                               -stiffness * output * q_out, atol=1e-14)
    assert final["output_spring_energy"] == pytest.approx(.5 * stiffness * q_out**2)
    individual = matrix + stiffness * np.diag(output**2)
    wrong = augmented.copy()
    wrong[:-1, :-1] = individual[np.ix_(free, free)]
    assert np.linalg.norm(np.linalg.solve(wrong, np.r_[np.zeros(len(free)), target])
                          - expected) > .05
    for diagnostic in result["linear_solve_diagnostics"]:
        assert diagnostic["relative_force_block_residual"] < 1e-12


def test_nonzero_lift_predictor_does_not_advance_the_physical_mean_twice():
    model, port = one_cell()
    _, assembler = synthetic(model, nonsymmetric=True)
    output = np.zeros(model.ndof)
    output[[2, 6]] = [.25, .75]
    shape = np.zeros(model.ndof)
    shape[[2, 3, 6, 7]] = [.8, .3, 1.2, -.5]
    common = dict(assembler=assembler, force_scale_per_length=20.)
    ordinary = solve_split_displacement_path(model, port, output, [0., .1, .2], 5., **common)
    lifted = solve_split_displacement_path(
        model, port, output, [0., .1, .2], 5., lift_shape=shape, **common)
    assert ordinary["status"] == lifted["status"] == "success"
    for left, right in zip(ordinary["accepted_steps"], lifted["accepted_steps"]):
        np.testing.assert_allclose(physical(right), physical(left),
                                   rtol=1e-12, atol=2e-14)
        np.testing.assert_array_equal(right["u_lift"], right["d"] * shape)
        assert right["R_input"] == pytest.approx(left["R_input"], rel=1e-12, abs=1e-14)
        assert abs(right["constraint_residual"]) <= right["constraint_bound"]
        # A linear problem must pass its first base check after prediction.
        # Eventual Newton recovery alone would conceal a wrong spring/lift RHS.
        assert left["newton_checks"] == right["newton_checks"] == 1


@pytest.mark.parametrize("lift,fluctuation,weights,offsets", [
    ([3., -.3], [0., 0.], [.1, 1.], ()),
    ([1., 0.], [2.**-55, 0.], [1., 0.], (-1.,)),
])
def test_split_weighted_mean_retains_product_error_and_hidden_fluctuation(
        lift, fluctuation, weights, offsets):
    state = SplitDisplacement(lift, fluctuation)
    expected = sum((Fraction.from_float(float(b))
                    * (Fraction.from_float(float(l)) + Fraction.from_float(float(w)))
                    for b, l, w in zip(weights, lift, fluctuation)), Fraction())
    expected += sum((Fraction.from_float(x) for x in offsets), Fraction())
    measured = split_average_measurement(state, np.array(weights), *offsets)
    assert measured == float(expected)
    assert measured != 0.
    naive = float(np.dot(weights, state.u_display)) + sum(offsets)
    assert naive != measured


def test_warm_start_is_independently_checked_and_failure_preserves_two_arrays_and_R():
    model, port = one_cell()
    _, assembler = synthetic(model, invalid_above=.4)
    origin = np.zeros(model.ndof)
    origin[[2, 6]] = [.1, -.1]
    origin[1] = -0.
    displacement = np.zeros(model.ndof)
    displacement[[2, 6]] = [.32, .08]
    initial = SplitDisplacement(origin, displacement - origin)
    initial_R = 1.28
    settings = DisplacementSettings(max_bisections=0)
    result = solve_split_displacement_path(
        model, port, port, [0., .1], lift_origin=origin, target_origin=.2,
        initial_state=initial, initial_R=initial_R, settings=settings,
        assembler=assembler, force_scale_per_length=20.)
    assert result["status"] == "failed"
    assert result["failure"]["code"] == "invalid_J"
    assert result["target_metrics"] is None
    assert len(result["accepted_steps"]) == 1
    last = result["last_accepted_state"]
    np.testing.assert_array_equal(last["u_lift"].view(np.uint64), initial.lift.view(np.uint64))
    np.testing.assert_array_equal(last["u_fluctuation"].view(np.uint64),
                                   initial.fluctuation.view(np.uint64))
    assert struct.pack("d", result["R_input"]) == struct.pack("d", initial_R)
    assert result["failed_attempts"][-1]["rollback_bitwise_equal"]
    assert last["physical_mean_target_mm"] == .2
    # A warm state with the wrong actuator force cannot bypass parameter-zero
    # equilibrium by being declared an accepted handoff.
    wrong_reaction = solve_split_displacement_path(
        model, port, port, [0.], lift_origin=origin, target_origin=.2,
        initial_state=initial, initial_R=0.,
        settings=DisplacementSettings(max_checks=1, max_bisections=0),
        assembler=assembler, force_scale_per_length=20.)
    assert wrong_reaction["status"] == "failed"
    assert wrong_reaction["failure"]["code"] == "newton_limit"
    assert wrong_reaction["accepted_steps"] == []
    assert wrong_reaction["last_accepted_state"] is None

    # Successful continuation uses the existing two-array state and a new
    # nonzero lift shape; its physical result matches a cold path to the same
    # final mean within the original numerical tolerance.
    _, valid_assembler = synthetic(model)
    shape = np.zeros(model.ndof)
    shape[[2, 3, 6, 7]] = [.8, .3, 1.2, -.5]
    continued = solve_split_displacement_path(
        model, port, port, [0., .1], lift_origin=origin, lift_shape=shape,
        target_origin=.2, initial_state=initial, initial_R=initial_R,
        assembler=valid_assembler, force_scale_per_length=20.)
    cold = solve_split_displacement_path(
        model, port, port, [0., .2, .2 + .1], assembler=valid_assembler,
        force_scale_per_length=20.)
    assert continued["status"] == cold["status"] == "success"
    np.testing.assert_allclose(physical(continued["target_metrics"]),
                               physical(cold["target_metrics"]), rtol=1e-12, atol=2e-14)
    assert continued["R_input"] == pytest.approx(cold["R_input"], rel=1e-12)
    np.testing.assert_array_equal(continued["target_metrics"]["u_lift"], origin + .1 * shape)
    assert continued["target_metrics"]["newton_checks"] == 1
    assert abs(continued["target_metrics"]["constraint_residual"]) <= continued["target_metrics"]["constraint_bound"]


def test_nonfinite_component_force_cannot_enter_an_accepted_record():
    model, port = one_cell()
    _, ordinary = synthetic(model)

    def corrupt_component(actual_model, state, *, tangent=True):
        matrix, force, fields = ordinary(actual_model, state, tangent=tangent)
        if split_average_measurement(state, port) > .05:
            fields["material_residual"][0, 0] = np.nan
        return matrix, force, fields

    stopped = solve_split_displacement_path(
        model, port, port, [0., .1], assembler=corrupt_component,
        settings=DisplacementSettings(max_bisections=0), force_scale_per_length=20.)
    assert stopped["status"] == "failed"
    assert stopped["failure"]["code"] == "nonfinite"
    assert stopped["target_metrics"] is None
    assert len(stopped["accepted_steps"]) == 1
    np.testing.assert_array_equal(physical(stopped["last_accepted_state"]), 0.)
    assert np.isfinite(stopped["last_accepted_state"]["material_internal_force"]).all()


def test_nonlinear_armijo_and_bounded_trial_rejection_keep_last_accepted_state():
    model, port = one_cell()
    _, assembler = synthetic(model, cubic=100.)
    result = solve_split_displacement_path(
        model, port, port, [0., .05, .1], assembler=assembler,
        force_scale_per_length=20.)
    assert result["status"] == "success" and result["trials"]
    for trial in result["trials"]:
        if trial["accepted"]:
            assert trial["phi"] <= (1 - 2e-4 * trial["factor"]) * trial["base_phi"]
            assert abs(trial["constraint_residual"]) <= 1e-10 * trial["target_displacement"]
    _, reject = synthetic(model, cubic=100., reject_trials=True)
    stopped = solve_split_displacement_path(
        model, port, port, [0., .05], assembler=reject,
        settings=DisplacementSettings(max_backtracks=2, max_bisections=0),
        force_scale_per_length=20.)
    assert stopped["status"] == "failed"
    assert stopped["failure"]["code"] == "backtracking_failed"
    assert len(stopped["trials"]) == 3 and not any(t["accepted"] for t in stopped["trials"])
    assert stopped["target_metrics"] is None
    assert stopped["R_input"] == 0.
    np.testing.assert_array_equal(physical(stopped["last_accepted_state"]), 0.)


def test_actual_numpy_q1_port_path_matches_homogeneous_axial_stretch(monkeypatch):
    from hf_eval.split_numpy_tangent import assemble_split_numpy

    model = rectangular_model(2, 1, 2., 1., E=7.8, nu=.3, alpha=0.,
                              fixed_dofs=(0, 6, 1, 3, 5))
    port, output = np.zeros(model.ndof), np.zeros(model.ndof)
    port[[4, 10]] = .5
    output[[7, 9, 11]] = 1. / 3.
    shape = np.zeros(model.ndof)
    shape[0::2] = model.coordinates[:, 0] / 2.

    def forbidden(*args, **kwargs):
        raise AssertionError("opt-in path called the default compiled assembler")

    monkeypatch.setattr(control, "assemble_split", forbidden)
    result = solve_split_displacement_path(
        model, port, output, [0., .02], lift_shape=shape,
        assembler=assemble_split_numpy, force_scale_per_length=7.8,
        settings=DisplacementSettings(time_limit_seconds=15.))
    assert result["status"] == "success"
    axial = 1.01
    lam, mu = model.lam[0], model.mu[0]
    transverse = brentq(lambda c: mu*(c*c - 1) + lam*np.log(axial*c),
                        .9, 1.1, xtol=1e-14)
    expected_u = np.zeros(model.ndof)
    expected_u[0::2] = (axial - 1) * model.coordinates[:, 0]
    expected_u[1::2] = (transverse - 1) * model.coordinates[:, 1]
    final = result["target_metrics"]
    np.testing.assert_allclose(physical(final), expected_u, atol=2e-12, rtol=2e-10)
    expected_Pxx = mu*(axial - 1./axial) + lam*np.log(axial*transverse)/axial
    assert final["R_input"] == pytest.approx(expected_Pxx, rel=2e-10, abs=2e-12)
    assert final["q_out"] == pytest.approx(transverse - 1, abs=2e-12)
    assert final["relative_global_force_balance"] < 1e-9
    assert final["minimum_J"] == pytest.approx(axial * transverse, rel=2e-11)
