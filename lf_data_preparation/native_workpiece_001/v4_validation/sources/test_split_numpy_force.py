"""Analytic forces and runtime independence for the NumPy candidate entry."""
import numpy as np
import pytest

from hf_eval import split_kernel_invariants_hu as kernel
from hf_eval.split_state import SplitDisplacement
from hf_eval.tmc import rectangular_model
from hf_eval.tmc_kernel import KernelError, operators


XY = np.array([[0., 0.], [1., 0.], [1., 1.], [0., 1.]])


@pytest.fixture(autouse=True)
def forbid_compilation(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("NumPy force entry invoked compiled work")
    for name in ("_runtime", "_batch_with_tangent", "_batch_without_tangent"):
        monkeypatch.setattr(kernel, name, forbidden)


def evaluate(w, *, lift=None, lam=2., mu=3., kr=0.):
    w = np.asarray(w).reshape(-1, 8)
    lift = np.zeros_like(w) if lift is None else np.asarray(lift).reshape(w.shape)
    return kernel.batch_response_split_numpy(lift, w, operators(1., 1.), lam, mu, kr)


def test_identity_and_analytic_shear():
    identity = evaluate(np.zeros(8), kr=1./8)
    for name in ("residual", "material_residual", "regularization_residual",
                 "stress_first_piola", "stress_second_piola", "material_energy"):
        np.testing.assert_array_equal(identity[name], 0.)
    a = 1./16
    w = np.column_stack((a*XY[:, 1], np.zeros(4))).ravel()
    out = evaluate(w)
    expected = np.array([-1., -1., -1., 1., 1., 1., 1., -1.])*3*a/2
    np.testing.assert_allclose(out["residual"][0], expected, rtol=2e-15, atol=2e-17)
    np.testing.assert_array_equal(out["regularization_residual"], 0.)
    np.testing.assert_allclose(out["material_energy"], 3*a*a/2, rtol=2e-15)


def test_nonzero_hessian_regularization_has_analytic_force():
    # u_x=a*x*y gives J=1+a*y and Hu_x,xy=Hu_x,yx=a.
    a, kr = 1./32, 1./8
    w = np.column_stack((a*XY[:, 0]*XY[:, 1], np.zeros(4))).ravel()
    out = evaluate(w, lam=0., mu=0., kr=kr)
    ops = operators(1., 1.)
    J = 1 + a*(ops["points"][:, 1]+1)/2
    scale = kr*np.sum(ops["weights"]*np.exp(-5*J))
    expected = scale*np.array([2*a, 0., -2*a, 0., 2*a, 0., -2*a, 0.])
    np.testing.assert_allclose(out["regularization_residual"][0], expected, rtol=2e-15, atol=1e-19)
    np.testing.assert_array_equal(out["material_residual"], 0.)


def test_mixed_branches_batch_and_scalar_coefficients():
    w = np.stack([np.zeros(8), (0.125*XY).ravel()])
    out = evaluate(w, lam=np.array([2., 4.]), mu=np.array([3., 5.]), kr=1./8)
    np.testing.assert_array_equal(out["small_branch"], [[1.]*9, [0.]*9])
    for i, (lam, mu) in enumerate(((2., 3.), (4., 5.))):
        single = evaluate(w[i], lam=lam, mu=mu, kr=1./8)
        for name in out:
            assert out[name].dtype == np.float64
            np.testing.assert_array_equal(out[name][i], single[name][0])
    np.testing.assert_array_equal(out["arithmetic_supported"], [1., 1.])
    assert "tangent" not in out


def test_shared_nodes_assemble_analytic_shear():
    model = rectangular_model(2, 1, 2., 1., E=7.8, nu=.3, alpha=0.)
    a = 1./16
    w = np.column_stack((a*model.coordinates[:, 1], np.zeros(len(model.coordinates)))).ravel()
    matrix, force, fields = kernel.assemble_split_numpy(model, SplitDisplacement(np.zeros_like(w), w))
    # Integral of constant P_xy=P_yx=mu*a: shared vertical edge cancels;
    # bottom/top y-normal edges distribute the x traction to both cells.
    expected = (model.mu[0]*a/2)*np.array([-1., -1., -2., 0., -1., 1., 1., -1., 2., 0., 1., 1.])
    np.testing.assert_allclose(force, expected, rtol=3e-15, atol=2e-17)
    assert matrix is None and "tangent" not in fields


@pytest.mark.parametrize("w,code", [
    (np.zeros(7), "invalid_shape"),
    (np.full(8, np.nan), "nonfinite"),
    (np.full(8, 2.**500), "unsupported_arithmetic_range"),
    (np.column_stack((-2*XY[:, 0], np.zeros(4))).ravel(), "invalid_J"),
])
def test_invalid_states_keep_existing_error_codes(w, code):
    with pytest.raises(KernelError) as error:
        kernel.batch_response_split_numpy(np.zeros_like(w).reshape(1, -1),
                                         w.reshape(1, -1), operators(1., 1.), 2., 3., 0.)
    assert error.value.code == code
