"""Binary64 error-compensated split affine gradients, without an HP oracle.

The primal uses Dekker TwoProduct and Knuth TwoSum in an identity-inclusive
Dot2 accumulator. It improves accuracy but does not promise correct rounding
for every input. The declared nonzero operand range [2**-400, 2**400] keeps
Split's intermediates finite and every possible nonzero product residual
above binary64's normal minimum: operand significand quanta are >=2**-452,
so exact product quanta are >=2**-904. Zero operands are allowed.

The JVP is the derivative of the physical affine/bilinear expression, with
fixed reference operators in the mechanical use. It does not differentiate
the compensating floating-point error bookkeeping. All critical operations
are explicit and separated by compiler barriers in the JAX implementation.
No JAX configuration is changed on import or during evaluation.
"""
from functools import partial

import jax
import jax.numpy as jnp
import numpy as np


OPERAND_MIN = 2.0**-400
OPERAND_MAX = 2.0**400
SPLITTER = float(2**27 + 1)
ARITHMETIC_VERSION = "split_affine_dot2_dekker_v1"
COMPILER_OPTIONS = {"xla_cpu_enable_fast_math": False, "xla_cpu_ftz": False}


def operand_domain(*values, xp=np):
    """Scalar condition for the declared EFT operand domain (zero allowed)."""
    valid = xp.asarray(True)
    for value in values:
        magnitude = xp.abs(value)
        valid = valid & xp.all(xp.isfinite(value))
        valid = valid & xp.all((magnitude == 0) | ((magnitude >= OPERAND_MIN) & (magnitude <= OPERAND_MAX)))
    return valid


def _barrier(value, xp):
    return jax.lax.optimization_barrier(value) if xp is jnp else value


def _add(a, b, xp):
    a, b = _barrier((a, b), xp)
    return _barrier(a + b, xp)


def _sub(a, b, xp):
    a, b = _barrier((a, b), xp)
    return _barrier(a - b, xp)


def _mul(a, b, xp):
    a, b = _barrier((a, b), xp)
    return _barrier(a * b, xp)


def two_sum(a, b, xp=np):
    """Return rounded sum and its exact residual in the declared domain."""
    total = _add(a, b, xp)
    b_virtual = _sub(total, a, xp)
    a_virtual = _sub(total, b_virtual, xp)
    a_error = _sub(a, a_virtual, xp)
    b_error = _sub(b, b_virtual, xp)
    return total, _add(a_error, b_error, xp)


def _split(value, xp):
    scaled = _mul(value, SPLITTER, xp)
    large = _sub(scaled, value, xp)
    high = _sub(scaled, large, xp)
    return high, _sub(value, high, xp)


def two_product(a, b, xp=np):
    """Return rounded product and its exact residual in the declared domain."""
    product = _mul(a, b, xp)
    a_hi, a_lo = _split(a, xp)
    b_hi, b_lo = _split(b, xp)
    error = _sub(product, _mul(a_hi, b_hi, xp), xp)
    error = _sub(error, _mul(a_lo, b_hi, xp), xp)
    error = _sub(error, _mul(a_hi, b_lo, xp), xp)
    error = _sub(_mul(a_lo, b_lo, xp), error, xp)
    return product, error


def dot2(a, b, initial=0.0, *, xp=np):
    """Fixed last-axis Dot2 with an initial affine constant.

    a and b must have the same last-axis length; other axes broadcast. This
    low-level routine assumes the caller has validated its operand domain.
    """
    if a.shape[-1] != b.shape[-1]:
        raise ValueError("dot2 operand lengths differ")
    total = xp.asarray(initial, dtype=xp.float64)
    correction = xp.zeros_like(total)
    for index in range(a.shape[-1]):
        product, product_error = two_product(a[..., index], b[..., index], xp)
        total, sum_error = two_sum(total, product, xp)
        correction = _add(correction, _add(sum_error, product_error, xp), xp)
    return _add(total, correction, xp)


def _affine_primal(lift, fluctuation, grad, identity, xp):
    shape = lift.shape[:-1] + (4, 2)
    left, right = lift.reshape(shape), fluctuation.reshape(shape)
    output_shape = left.shape[:-2] + (grad.shape[0], 2, 2)
    initial = xp.eye(2, dtype=lift.dtype) if identity else xp.zeros((2, 2), dtype=lift.dtype)
    total = xp.broadcast_to(initial, output_shape)
    correction = xp.zeros_like(total)
    for nodal in (left, right):
        for node in range(4):
            product, product_error = two_product(
                nodal[..., node, None, :, None], grad[:, node, None, :], xp)
            total, sum_error = two_sum(total, product, xp)
            correction = _add(correction, _add(sum_error, product_error, xp), xp)
    return _add(total, correction, xp)


def _linear_gradient(nodal, grad):
    values = nodal.reshape(nodal.shape[:-1] + (4, 2))
    return jnp.einsum("...ai,qaj->...qij", values, grad)


@partial(jax.custom_jvp, nondiff_argnums=(3,))
def affine_gradient_jax(lift, fluctuation, grad, identity):
    return _affine_primal(lift, fluctuation, grad, identity, jnp)


@affine_gradient_jax.defjvp
def _affine_gradient_jvp(identity, primals, tangents):
    lift, fluctuation, grad = primals
    d_lift, d_fluctuation, d_grad = tangents
    primal = affine_gradient_jax(lift, fluctuation, grad, identity)
    # Include operator perturbations for a complete bilinear derivative.
    # The mechanics fixes grad and lift, leaving only grad(d_fluctuation).
    tangent = (_linear_gradient(d_lift, grad) + _linear_gradient(d_fluctuation, grad)
               + _linear_gradient(lift, d_grad) + _linear_gradient(fluctuation, d_grad))
    return primal, tangent


def affine_gradient(lift, fluctuation, grad, *, identity, xp=np):
    if xp is jnp:
        return affine_gradient_jax(lift, fluctuation, grad, identity)
    return _affine_primal(lift, fluctuation, grad, identity, np)
