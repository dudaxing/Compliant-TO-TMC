"""Small analytic checks for the optional invariant/Hu candidate.

These are synthetic unit tests, not a claim that the declared 69+63 scientific
matrix passed. No production value is reused as the reference force/Jv.
"""
import jax
import jax.numpy as jnp
import numpy as np
import pytest

from hf_eval import compensated_invariants as ci
from hf_eval import split_kernel_invariants_hu as kernel
from hf_eval.split_state import SplitDisplacement
from hf_eval.tmc import TMCModel
from hf_eval.tmc_kernel import KernelError, operators


XY = np.array([[0., 0.], [1., 0.], [1., 1.], [0., 1.]])


@pytest.fixture(autouse=True)
def explicit_runtime():
    assert jax.default_backend() == "cpu"
    with jax.enable_x64(True):
        yield


def response(w, *, lift=None, lam=2., mu=3., kr=0., tangent=True):
    w = np.asarray(w).reshape(-1, 8)
    lift = np.zeros_like(w) if lift is None else np.asarray(lift).reshape(w.shape)
    return kernel.batch_response_split(lift, w, operators(1., 1.), lam, mu, kr, tangent=tangent)


def shear(a):
    return np.column_stack((a*XY[:, 1], np.zeros(4))).ravel()


def test_undeformed_force_energy_stress_and_linear_tangent():
    out = response(np.zeros(8), kr=1./8)
    for name in ("residual", "material_residual", "regularization_residual",
                 "stress_first_piola", "stress_second_piola", "material_energy"):
        np.testing.assert_array_equal(out[name], 0.)
    v = shear(1.)
    # At identity a unit simple shear has dP_xy=dP_yx=mu=3;
    # its affine Hessian vanishes, so regularization contributes no action.
    expected = np.array([-1., -1., -1., 1., 1., 1., 1., -1.])*1.5
    np.testing.assert_allclose(out["tangent"][0]@v, expected, atol=2e-14, rtol=2e-14)


def test_simple_shear_closed_form_stress_energy_force_and_split():
    a, mu = 1./16, 3.
    w = shear(a)
    out = response(w)
    P = np.array([[0., mu*a], [mu*a, 0.]])
    S = np.array([[-mu*a*a, mu*a], [mu*a, 0.]])
    expected_force = np.array([-1., -1., -1., 1., 1., 1., 1., -1.])*mu*a/2
    np.testing.assert_allclose(out["stress_first_piola"][0], np.broadcast_to(P, (9, 2, 2)), atol=2e-17, rtol=2e-15)
    np.testing.assert_allclose(out["stress_second_piola"][0], np.broadcast_to(S, (9, 2, 2)), atol=2e-17, rtol=2e-15)
    np.testing.assert_allclose(out["material_residual"][0], expected_force, atol=2e-17, rtol=2e-15)
    np.testing.assert_allclose(out["material_energy"], mu*a*a/2, atol=2e-18, rtol=2e-15)
    np.testing.assert_allclose(out["F"]@out["stress_second_piola"], out["stress_first_piola"], atol=2e-17, rtol=2e-15)
    np.testing.assert_array_equal(out["small_branch"], 1.)
    equivalent = response(shear(a/2), lift=shear(a/2), tangent=False)
    for name in ("residual", "material_residual", "regularization_residual", "material_energy"):
        np.testing.assert_array_equal(equivalent[name], out[name])


def test_exact_selector_equal_adjacent_and_low_part_boundaries():
    # A selector test supplies its arguments directly, independent of mesh
    # arithmetic. Both signs of delta and all matrix entries are exercised.
    for field, bound in (("B", 1./16), ("delta", 1./64)):
        for sign in (-1., 1.):
            center = sign*bound
            magnitudes = [np.nextafter(bound, 0.), bound, np.nextafter(bound, np.inf)]
            B = np.zeros((3, 2, 2)); delta = np.zeros(3)
            if field == "B":
                B[:, 0, 1] = sign*np.array(magnitudes)
            else:
                delta[:] = sign*np.array(magnitudes)
            compiled = jax.jit(lambda b, d: kernel._small_invariant_branch(ci.dd_from(b, jnp), ci.dd_from(d, jnp), jnp),
                               compiler_options=kernel.COMPILER_OPTIONS)
            expected = [True, True, False]
            np.testing.assert_array_equal(kernel._small_invariant_branch(ci.dd_from(B, np), ci.dd_from(delta, np), np), expected)
            np.testing.assert_array_equal(np.asarray(compiled(B, delta)), expected)
            # A positive magnitude low part beyond an exactly equal high part
            # must not disappear when selecting the arithmetic branch.
            if field == "B":
                high = np.zeros((2, 2)); low = np.zeros_like(high)
                high[0, 1], low[0, 1] = center, sign*2.**-60
                assert not bool(kernel._small_invariant_branch((high, low), ci.dd_const(0., np), np))
            else:
                assert not bool(kernel._small_invariant_branch(ci.dd_from(np.zeros((2, 2)), np),
                                                              (np.asarray(center), np.asarray(sign*2.**-60)), np))


def test_mixed_branch_batch_force_only_tangent_and_numpy_identity():
    w = np.stack([shear(1./32), shear(1./8), np.column_stack((XY[:, 0]/32, np.zeros(4))).ravel()])
    a = response(w, tangent=True)
    b = response(w, tangent=False)
    np.testing.assert_array_equal(a["small_branch"][:, 0], [1., 0., 0.])
    for name in ("residual", "material_residual", "regularization_residual", "F", "J", "Hu", "B", "delta"):
        np.testing.assert_allclose(a[name], b[name], rtol=2e-15, atol=1e-30)
    ops = operators(1., 1.)
    _, numpy_result = kernel._response(np.zeros_like(w), w, ops["grad"], ops["hessian"],
                                       ops["weights"], np.full(3, 2.), np.full(3, 3.), 0., np)
    for name in ("F_hi", "F_lo", "J_hi", "J_lo", "Hu_hi", "Hu_lo", "B_hi", "B_lo", "delta_hi", "delta_lo", "small_branch"):
        np.testing.assert_array_equal(a[name].view(np.uint64), numpy_result[name].view(np.uint64))


@pytest.mark.parametrize("direction", ["affine", "bilinear"])
def test_huhu_closed_form_and_exponential_direction_derivative(direction):
    a, b, kr = 1./8, -1./16, 1./4
    x, y = XY.T
    w = np.column_stack((a*x*y, b*x*y)).ravel()
    out = response(w, lam=0., mu=0., kr=kr)
    ops = operators(1., 1.)
    qx, qy = ((ops["points"]+1.)/2.).T
    J = 1+a*qy+b*qx
    Au = (np.array([1., -1., 1., -1.])[:, None]*np.array([2*a, 2*b])).ravel()
    expected = kr*np.sum(ops["weights"]*np.exp(-5*J))*Au
    if direction == "affine":
        v = np.column_stack((x, np.zeros(4))).ravel()
        dJ = 1+b*qx
        dAu = np.zeros(8)
    else:
        v = np.column_stack((x*y, np.zeros(4))).ravel()
        dJ = qy
        dAu = (np.array([1., -1., 1., -1.])[:, None]*np.array([2., 0.])).ravel()
    expected_action = kr*np.sum(ops["weights"][:, None]*np.exp(-5*J)[:, None]
                                *(dAu[None]-5*dJ[:, None]*Au[None]), axis=0)
    np.testing.assert_allclose(out["regularization_residual"][0], expected, rtol=3e-14, atol=1e-17)
    np.testing.assert_allclose(out["tangent"][0]@v, expected_action, rtol=3e-13, atol=1e-16)
    args = (jnp.zeros(8), jnp.asarray(ops["grad"]), jnp.asarray(ops["hessian"]), jnp.asarray(ops["weights"]))
    function = lambda z: kernel._residual_with_aux(args[0], z, *args[1:], 0., 0., kr)[0]
    action = jax.jvp(function, (jnp.asarray(w),), (jnp.asarray(v),))[1]
    np.testing.assert_allclose(action, expected_action, rtol=3e-13, atol=1e-16)
    assert np.linalg.norm(out["tangent"][0]-out["tangent"][0].T) > 1e-5


def test_physical_invalid_j_distinct_from_unsupported_and_nonfinite_inputs():
    inversion = np.column_stack((-2*XY[:, 0], np.zeros(4))).ravel()
    np.testing.assert_array_equal(kernel.determinants_split(np.zeros(8), inversion, operators(1., 1.)), -1.)
    with pytest.raises(KernelError) as invalid:
        response(inversion)
    assert invalid.value.code == "invalid_J"
    huge = np.full(8, 2.**401)
    with pytest.raises(KernelError) as unsupported:
        response(huge)
    assert unsupported.value.code == "unsupported_arithmetic_range"
    with pytest.raises(KernelError) as nonfinite:
        response(np.full(8, np.nan))
    assert nonfinite.value.code == "nonfinite"
    # Valid J=100 but exp(-5J) lies outside the explicitly bounded exp domain.
    with pytest.raises(KernelError) as exponent:
        response(np.column_stack((99*XY[:, 0], np.zeros(4))).ravel())
    assert exponent.value.code == "unsupported_arithmetic_range"


def test_compiled_guard_rejects_invalid_j_before_material_response():
    ops = operators(1., 1.)
    inversion = np.column_stack((-2*XY[:, 0], np.zeros(4))).ravel()[None]
    fields = kernel._batch_without_tangent(
        jnp.zeros((1, 8)), jnp.asarray(inversion), jnp.asarray(ops["grad"]),
        jnp.asarray(ops["hessian"]), jnp.asarray(ops["weights"]),
        jnp.asarray([2.]), jnp.asarray([3.]), 1./8)
    np.testing.assert_array_equal(np.asarray(fields["J"]), -1.)
    np.testing.assert_array_equal(np.asarray(fields["arithmetic_supported"]), 0.)
    assert np.isnan(np.asarray(fields["residual"])).all()


def test_assembly_keeps_fixed_dofs_and_true_unsymmetric_matrix():
    a, b = 1./8, -1./16
    w = np.column_stack((a*XY[:, 0]*XY[:, 1], b*XY[:, 0]*XY[:, 1])).ravel()
    model = TMCModel(XY, np.array([[0, 1, 2, 3]]), np.array([0.]), np.array([0.]),
                     1./4, 1., 1., fixed_dofs=np.array([0, 1]))
    state = SplitDisplacement(np.zeros(8), w)
    K, force, fields = kernel.assemble_split(model, state)
    assert K.shape == (8, 8) and force.shape == (8,)
    np.testing.assert_array_equal(force, fields["residual"][0])
    np.testing.assert_array_equal(K.toarray(), fields["tangent"][0])
    assert force[0] != 0 and np.linalg.norm(K.toarray()-K.toarray().T) > 1e-5


def test_shear_energy_direction_derivative_is_material_virtual_work():
    # J=1 for this entire shear direction, so the auxiliary r-polynomial is
    # exactly zero; dW/da=mu*a is an exact analytic target, not an FD estimate.
    a, mu = 1./32, 3.
    ops = operators(1., 1.)
    energy = lambda amplitude: kernel._without_tangent(
        jnp.zeros(8), amplitude*jnp.asarray(shear(1.)), jnp.asarray(ops["grad"]),
        jnp.asarray(ops["hessian"]), jnp.asarray(ops["weights"]), 2., mu, 0.)["material_energy"]
    _, derivative = jax.jvp(energy, (jnp.asarray(a),), (jnp.asarray(1.),))
    out = response(shear(a), tangent=False)
    np.testing.assert_allclose(derivative, mu*a, rtol=3e-14, atol=1e-16)
    np.testing.assert_allclose(out["material_residual"][0]@shear(1.), mu*a, rtol=3e-14, atol=1e-16)
