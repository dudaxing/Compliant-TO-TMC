"""Small analytic and force-direction checks for the NumPy mechanical Jacobian."""
import numpy as np
import pytest

from hf_eval import split_kernel_invariants_hu as force
from hf_eval.split_numpy_tangent import (batch_tangent_split_numpy, assemble_tangent_split_numpy,
                                        assemble_split_numpy, batch_tangent_components_split_numpy)
from hf_eval.split_state import SplitDisplacement
from hf_eval.tmc import rectangular_model
from hf_eval.tmc_kernel import KernelError, operators


XY = np.array([[0., 0.], [1., 0.], [1., 1.], [0., 1.]])


@pytest.fixture(autouse=True)
def forbid_compilation(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("NumPy tangent invoked compiled work")
    for name in ("_runtime", "_batch_with_tangent", "_batch_without_tangent"):
        monkeypatch.setattr(force, name, forbidden)


def tangent(w, *, lift=None, lam=2., mu=3., kr=0.):
    w = np.asarray(w).reshape(-1, 8)
    lift = np.zeros_like(w) if lift is None else np.asarray(lift).reshape(w.shape)
    return batch_tangent_split_numpy(lift, w, operators(1., 1.), lam, mu, kr)


@pytest.mark.parametrize("a", [0., 1./16])
def test_identity_and_shear_have_analytic_shear_action(a):
    v = np.column_stack((XY[:, 1], np.zeros(4))).ravel()
    K = tangent(a*v, kr=1./8)[0]
    expected = 1.5*np.array([-1., -1., -1., 1., 1., 1., 1., -1.])
    np.testing.assert_allclose(K@v, expected, rtol=3e-15, atol=2e-15)
    for translation in (np.tile([1., 0.], 4), np.tile([0., 1.], 4)):
        np.testing.assert_allclose(K@translation, 0., atol=2e-15)
    if a == 0.:
        np.testing.assert_allclose(K, K.T, atol=2e-15)
    components = batch_tangent_components_split_numpy(np.zeros((1, 8)), (a*v)[None],
                                                      operators(1., 1.), 2., 3., 1./8)
    for name, value in components.items():
        assert value.shape == (1, 8, 8) and value.dtype == np.float64
        assert np.all(np.isfinite(value))
    np.testing.assert_array_equal(components["total_tangent"][0], K)


@pytest.mark.parametrize("direction", ["affine", "bilinear"])
def test_nonzero_hu_regularization_derivative_and_nonsymmetry(direction):
    x, y = XY.T
    a, b, kr = 1./8, -1./16, 1./4
    w = np.column_stack((a*x*y, b*x*y)).ravel()
    K = tangent(w, lam=0., mu=0., kr=kr)[0]
    ops = operators(1., 1.)
    qx, qy = ((ops["points"]+1.)/2.).T
    J = 1+a*qy+b*qx
    action = (np.array([1., -1., 1., -1.])[:, None]*np.array([2*a, 2*b])).ravel()
    if direction == "affine":
        v = np.column_stack((x, np.zeros(4))).ravel()
        dJ = 1+b*qx
        d_action = np.zeros(8)
    else:
        v = np.column_stack((x*y, np.zeros(4))).ravel()
        dJ = qy
        d_action = (np.array([1., -1., 1., -1.])[:, None]*np.array([2., 0.])).ravel()
    expected = kr*np.sum(ops["weights"][:, None]*np.exp(-5*J)[:, None]
                         *(d_action[None]-5*dJ[:, None]*action[None]), axis=0)
    np.testing.assert_allclose(K@v, expected, rtol=3e-14, atol=2e-17)
    assert np.linalg.norm(K-K.T) > 1e-5


def test_actual_force_direction_difference_converges_with_fixed_lift():
    x, y = XY.T
    lift = np.column_stack((.02*x, -.01*y)).ravel()
    w = np.column_stack((.05*x+.03*x*y, -.03*y+.02*x*y)).ravel()
    v = np.array([.1, -.3, .2, .4, -.2, .1, -.4, .2])
    K = tangent(w, lift=lift, kr=1./8)[0]
    ops = operators(1., 1.)
    def residual(z):
        return force.batch_response_split_numpy(lift[None], z[None], ops, 2., 3., 1./8)["residual"][0]
    errors = []
    for h in (1e-2, 5e-3, 2.5e-3):
        estimate = (residual(w+h*v)-residual(w-h*v))/(2*h)
        errors.append(np.linalg.norm(estimate-K@v))
    assert errors[1] < .4*errors[0] and errors[2] < .4*errors[1]


def test_batch_with_individual_coefficients_and_global_shared_nodes():
    model = rectangular_model(2, 1, 2., 1., E=7.8, nu=.3, alpha=.001, fixed_dofs=(0, 1))
    x, y = model.coordinates.T
    w = np.column_stack((.05*x+.02*x*y, -.02*y)).ravel()
    state = SplitDisplacement(np.zeros_like(w), w)
    batch = batch_tangent_split_numpy(state.lift[model.edofs], state.fluctuation[model.edofs],
                                     model.ops, model.lam, model.mu, model.kr)
    for e in range(model.ne):
        single = batch_tangent_split_numpy(state.lift[model.edofs[e]][None],
                                          state.fluctuation[model.edofs[e]][None],
                                          model.ops, model.lam[e], model.mu[e], model.kr)
        np.testing.assert_array_equal(batch[e], single[0])
    K = assemble_tangent_split_numpy(model, state)
    combined_K, internal, fields = assemble_split_numpy(model, state)
    np.testing.assert_array_equal(combined_K.toarray(), K.toarray())
    matrix, force_only, no_tangent = assemble_split_numpy(model, state, tangent=False)
    np.testing.assert_array_equal(force_only, internal)
    assert matrix is None and "tangent" not in no_tangent
    assert fields["timing_seconds"]["kernel_and_transfer"] > 0.
    v = np.linspace(-.3, .4, model.ndof)
    def residual(z):
        return force.assemble_split_numpy(model, SplitDisplacement(state.lift, z))[1]
    h = 1e-4
    estimate = (residual(w+h*v)-residual(w-h*v))/(2*h)
    np.testing.assert_allclose(K@v, estimate, rtol=2e-7, atol=2e-8)
    assert K.shape == (model.ndof, model.ndof) and np.linalg.norm(K.toarray()[0]) > 0.


@pytest.mark.parametrize("w,code", [
    (np.full(8, np.nan), "nonfinite"),
    (np.column_stack((-2*XY[:, 0], np.zeros(4))).ravel(), "invalid_J"),
    (np.full(8, 2.**500), "unsupported_arithmetic_range"),
])
def test_invalid_state_rejection_inherits_force_contract(w, code):
    with pytest.raises(KernelError) as error:
        tangent(w)
    assert error.value.code == code
