"""Arithmetic and derivative checks for the new opt-in stable-F candidate.

These small manufactured checks do not run an equilibrium path. Fraction
oracles are used only in tests for exact input arithmetic, never production.
The full force/HP/Jv admission is a separate frozen validation job.
"""
from fractions import Fraction

import jax
import jax.numpy as jnp
import numpy as np
import pytest

from hf_eval import compensated_kinematics as ck
from hf_eval import split_kernel_compensated as kernel
from hf_eval.tmc_kernel import KernelError, operators


@pytest.fixture(autouse=True)
def explicit_runtime():
    assert jax.default_backend() == "cpu"
    with jax.enable_x64(True):
        yield


def exact(value):
    return Fraction.from_float(float(value))


def compiled(function):
    return jax.jit(function, compiler_options=ck.COMPILER_OPTIONS)


@pytest.mark.parametrize("a,b", [
    (1. + 2.**-27, 1. - 2.**-27),
    (.1, .3), (-1.7, 3.1),
    (2.**400, 2.**400), (2.**-400, 2.**-400),
    (np.nextafter(2.**-400, np.inf), np.nextafter(2.**400, 0.)),
    (0., 2.**400),
])
def test_product_residual_is_exact_numpy_and_jit(a, b):
    function = compiled(lambda x, y: ck.two_product(x, y, jnp))
    for product, residual in (ck.two_product(np.float64(a), np.float64(b)), function(a, b)):
        assert exact(product) + exact(residual) == exact(a)*exact(b)


@pytest.mark.parametrize("a,b", [(1., 2.**-54), (-1., 1. + 2.**-52), (.1, .3),
                                    (2.**800, 2.**-904), (-2.**800, 2.**800)])
def test_sum_residual_is_exact_numpy_and_jit(a, b):
    function = compiled(lambda x, y: ck.two_sum(x, y, jnp))
    for total, residual in (ck.two_sum(np.float64(a), np.float64(b)), function(a, b)):
        assert exact(total) + exact(residual) == exact(a) + exact(b)


def test_identity_and_product_residual_share_one_accumulator():
    a = np.array([-(1. + 2.**-27)])
    b = np.array([1. - 2.**-27])
    assert float(1. + a[0]*b[0]) == 0.
    function = compiled(lambda x, y: ck.dot2(x, y, 1., xp=jnp))
    assert float(ck.dot2(a, b, 1.)) == 2.**-54
    assert float(function(a, b)) == 2.**-54


def test_affine_identity_cancel_keeps_product_residual():
    lift = np.zeros(8)
    lift[0] = -(1. + 2.**-27)
    fluctuation = np.zeros(8)
    grad = np.zeros((9, 4, 2))
    grad[:, 0, 0] = 1. - 2.**-27
    function = compiled(lambda left, right, g: ck.affine_gradient(
        left, right, g, identity=True, xp=jnp))
    numpy_value = ck.affine_gradient(lift, fluctuation, grad, identity=True)
    jax_value = np.asarray(function(lift, fluctuation, grad))
    assert np.all(numpy_value[:, 0, 0] == 2.**-54)
    np.testing.assert_array_equal(jax_value.view(np.uint64), numpy_value.view(np.uint64))


@pytest.mark.parametrize("identity", [True, False])
@pytest.mark.parametrize("sizes", [(1., 1.), (.1, .3), (.17, .29)])
def test_compiled_numpy_affine_and_exact_input_oracle(identity, sizes):
    rng = np.random.default_rng(20260921)
    lift = rng.uniform(-1., 1., (3, 8))
    fluctuation = rng.uniform(-.03125, .03125, (3, 8))
    grad = operators(*sizes)["grad"]
    function = compiled(lambda left, right, g: ck.affine_gradient(
        left, right, g, identity=identity, xp=jnp))
    numpy_value = ck.affine_gradient(lift, fluctuation, grad, identity=identity)
    jax_value = np.asarray(function(lift, fluctuation, grad))
    np.testing.assert_array_equal(jax_value.view(np.uint64), numpy_value.view(np.uint64))
    # Dot2 has a bounded error, not a global correctly-rounded guarantee.
    # These independently specified moderate inputs should be within 2 ulp.
    for element, q, i, j in np.ndindex(numpy_value.shape):
        reference = Fraction(int(identity and i == j))
        for nodal in (lift, fluctuation):
            for node in range(4):
                reference += exact(nodal[element, 2*node+i])*exact(grad[q, node, j])
        rounded = float(reference)
        assert abs(numpy_value[element, q, i, j] - rounded) <= 2*abs(np.spacing(rounded))


def test_exactly_equivalent_split_redistribution():
    grad = operators(.1, .3)["grad"]
    lift = np.arange(8, dtype=float)/16
    fluctuation = np.arange(7, -1, -1, dtype=float)/64
    shift = np.array([1., -2., 3., -1., 1., -1., 2., -2.])/128
    for index in range(8):
        assert exact(lift[index])+exact(fluctuation[index]) == (
            exact(lift[index]+shift[index])+exact(fluctuation[index]-shift[index]))
    for identity in (True, False):
        before = ck.affine_gradient(lift, fluctuation, grad, identity=identity)
        after = ck.affine_gradient(lift+shift, fluctuation-shift, grad, identity=identity)
        np.testing.assert_array_max_ulp(before, after, maxulp=2)


def test_custom_jvp_matches_physical_bilinear_rule_and_transpose():
    grad = operators(.1, .3)["grad"]
    lift = np.arange(8, dtype=float)/16
    fluctuation = np.arange(7, -1, -1, dtype=float)/64
    direction = np.array([1., -2., 3., -1., -2., 4., -3., -1.])/8
    dg = np.arange(72, dtype=float).reshape(9, 4, 2)/1024
    function = lambda left, right, g: ck.affine_gradient(left, right, g, identity=True, xp=jnp)
    _, actual = compiled(lambda l, w, g, v, gdot: jax.jvp(
        function, (l, w, g), (v, -2*v, gdot)))(lift, fluctuation, grad, direction, dg)
    expected = (-np.einsum("ai,qaj->qij", direction.reshape(4, 2), grad)
                + np.einsum("ai,qaj->qij", lift.reshape(4, 2), dg)
                + np.einsum("ai,qaj->qij", fluctuation.reshape(4, 2), dg))
    np.testing.assert_allclose(actual, expected, rtol=5e-15, atol=1e-14)
    fixed = lambda varied: function(jnp.asarray(lift), varied, jnp.asarray(grad))
    jacobian = np.asarray(compiled(jax.jacfwd(fixed))(fluctuation))
    action = np.asarray(compiled(lambda w, v: jax.jvp(fixed, (w,), (v,))[1])(fluctuation, direction))
    np.testing.assert_allclose(np.einsum("qija,a->qij", jacobian, direction), action,
                               rtol=5e-15, atol=1e-14)
    cotangent = np.arange(36, dtype=float).reshape(9, 2, 2)/32
    transpose = np.asarray(compiled(lambda w, c: jax.vjp(fixed, w)[1](c)[0])(fluctuation, cotangent))
    np.testing.assert_allclose(np.dot(transpose, direction), np.sum(cotangent*action),
                               rtol=5e-15, atol=1e-14)


@pytest.mark.parametrize("value", [np.nextafter(ck.OPERAND_MIN, 0.),
                                    np.nextafter(ck.OPERAND_MAX, np.inf),
                                    -np.nextafter(ck.OPERAND_MAX, np.inf)])
def test_unsupported_operand_rejected_before_kernel(value):
    lift = np.zeros((1, 8))
    lift[0, 0] = value
    with pytest.raises(KernelError) as failure:
        kernel.batch_response_split(lift, np.zeros_like(lift), operators(1., 1.), 2., 3., .125)
    assert failure.value.code == "unsupported_kinematics_range"


def test_operand_domain_includes_signed_zero_and_endpoints():
    assert bool(ck.operand_domain(np.array([0., -0., ck.OPERAND_MIN, -ck.OPERAND_MAX])))
    assert not bool(ck.operand_domain(np.array([np.inf])))
    assert not bool(ck.operand_domain(np.array([np.nan])))


def test_nonpositive_total_J_still_rejected():
    lift = np.array([0., 0., 0., 0., 0., -1., 0., -1.])[None]
    with pytest.raises(KernelError) as failure:
        kernel.batch_response_split(lift, np.zeros_like(lift), operators(1., 1.), 2., 3., .125)
    assert failure.value.code == "invalid_J"


def test_strict_compiler_options_and_barrier_lowering_are_explicit():
    assert kernel.COMPILER_OPTIONS == {"xla_cpu_enable_fast_math": False, "xla_cpu_ftz": False}
    function = compiled(lambda a, b: ck.dot2(a, b, 1., xp=jnp))
    lowered = function.lower(np.array([.1]), np.array([.3]))
    assert "stablehlo.optimization_barrier" in str(lowered.compiler_ir(dialect="stablehlo"))
    # Compilation must accept the requested options; no option-removal retry.
    executable = lowered.compile()
    assert np.isfinite(np.asarray(executable(np.array([.1]), np.array([.3]))))
