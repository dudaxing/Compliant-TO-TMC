"""Bounded two-component arithmetic for an opt-in invariants/Hu candidate.

A DD is a normalized ``(hi, lo)`` pair of binary64 arrays representing the
real shadow value hi + lo. This is not an arbitrary-precision implementation.
Every public arithmetic primitive checks its operands and normalized result;
unsupported entries become NaN, never a clipped physical value. See
docs/HF4_C2_INVARIANTS_HU_ARITHMETIC.md for the range and physical-JVP contract.
No runtime configuration is changed on import.
"""
from __future__ import annotations

from functools import partial
from math import prod

import jax
import jax.numpy as jnp
import numpy as np


ARITHMETIC_VERSION = "split_invariants_hu_dd_v1"
COMPILER_OPTIONS = {"xla_cpu_enable_fast_math": False, "xla_cpu_ftz": False}
OPERAND_MIN = 2.0**-400
OPERAND_MAX = 2.0**400
TEMPORARY_MAX = 2.0**900
SPLITTER = float(2**27 + 1)
B_THRESHOLD = 2.0**-4
DELTA_THRESHOLD = 2.0**-6
EXP_ARGUMENT_MAX = 256.0


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


def _component_supported(value, xp):
    magnitude = xp.abs(value)
    return xp.isfinite(value) & ((magnitude == 0) | (
        (magnitude >= OPERAND_MIN) & (magnitude <= OPERAND_MAX)))


def operand_domain(*values, xp=np):
    """Scalar verdict for raw binary64 operands; zeros are admitted."""
    valid = xp.asarray(True)
    for value in values:
        valid = valid & xp.all(_component_supported(xp.asarray(value), xp))
    return valid


def _pair_mask(a, xp):
    # All constructors normalize. This additionally rejects grossly
    # overlapping hand-constructed pairs, not just nonfinite components.
    return (_component_supported(a[0], xp) & _component_supported(a[1], xp)
            & (xp.abs(a[1]) <= _mul(2.0**-52, xp.abs(a[0]), xp)))


def pair_supported(a, xp=np):
    """Scalar verdict; callers must use normalized pairs from this module."""
    return xp.all(_pair_mask(a, xp))


def _two_sum(a, b, xp):
    total = _add(a, b, xp)
    b_virtual = _sub(total, a, xp)
    a_virtual = _sub(total, b_virtual, xp)
    return total, _add(_sub(a, a_virtual, xp), _sub(b, b_virtual, xp), xp)


def _split(value, xp):
    scaled = _mul(value, SPLITTER, xp)
    large = _sub(scaled, value, xp)
    high = _sub(scaled, large, xp)
    return high, _sub(value, high, xp)


def _two_product(a, b, xp):
    """Internal EFT; caller has sanitized each operand to the stated range."""
    product = _mul(a, b, xp)
    ah, al = _split(a, xp)
    bh, bl = _split(b, xp)
    error = _sub(product, _mul(ah, bh, xp), xp)
    error = _sub(error, _mul(al, bh, xp), xp)
    error = _sub(error, _mul(ah, bl, xp), xp)
    return product, _sub(_mul(al, bl, xp), error, xp)


def _finish(high, low, valid, xp):
    # Products may temporarily reach 2**800. The temporary bound protects
    # TwoSum before the stricter normalized-pair output check is applied.
    temporary = (xp.isfinite(high) & xp.isfinite(low)
                 & (xp.abs(high) <= TEMPORARY_MAX)
                 & (xp.abs(low) <= TEMPORARY_MAX))
    high = xp.where(temporary, high, 0.0)
    low = xp.where(temporary, low, 0.0)
    high, low = _two_sum(high, low, xp)
    valid = valid & temporary & _pair_mask((high, low), xp)
    return xp.where(valid, high, xp.nan), xp.where(valid, low, xp.nan)


def dd_from(value, xp=np):
    """Construct a checked pair from binary64 primitives, with zero low part."""
    value = xp.asarray(value, dtype=xp.float64)
    valid = _component_supported(value, xp)
    return xp.where(valid, value, xp.nan), xp.where(valid, xp.zeros_like(value), xp.nan)


def dd_const(value, xp=np):
    return dd_from(value, xp)


def dd_value(a, xp=np):
    """Round the represented value once, at an explicit output boundary."""
    return _add(a[0], a[1], xp)


def dd_neg(a):
    return -a[0], -a[1]


def dd_getitem(a, item):
    return a[0][item], a[1][item]


def dd_where(condition, a, b, xp=np):
    return xp.where(condition, a[0], b[0]), xp.where(condition, a[1], b[1])


def dd_transpose(a, axes=None, xp=np):
    return xp.transpose(a[0], axes), xp.transpose(a[1], axes)


def dd_swapaxes(a, first, second, xp=np):
    return xp.swapaxes(a[0], first, second), xp.swapaxes(a[1], first, second)


def _safe_pair(a, valid, xp):
    return xp.where(valid, a[0], 0.0), xp.where(valid, a[1], 0.0)


def _dd_add_primal(a, b, xp):
    valid = _pair_mask(a, xp) & _pair_mask(b, xp)
    a, b = _safe_pair(a, valid, xp), _safe_pair(b, valid, xp)
    high, error = _two_sum(a[0], b[0], xp)
    low, tail = _two_sum(a[1], b[1], xp)
    error = _add(error, low, xp)
    high, error = _two_sum(high, error, xp)
    return _finish(high, _add(error, tail, xp), valid, xp)


def _dd_product_primal(a, b, xp):
    a, b = xp.asarray(a, dtype=xp.float64), xp.asarray(b, dtype=xp.float64)
    valid = _component_supported(a, xp) & _component_supported(b, xp)
    high, low = _two_product(xp.where(valid, a, 0.0), xp.where(valid, b, 0.0), xp)
    return _finish(high, low, valid, xp)


def _dd_mul_primal(a, b, xp):
    # Include all four products, including lo*lo. Each product has its own
    # executable EFT range check and each addition checks its output range.
    result = _dd_product_primal(a[0], b[0], xp)
    for i, j in ((0, 1), (1, 0), (1, 1)):
        result = _dd_add_primal(result, _dd_product_primal(a[i], b[j], xp), xp)
    valid = _pair_mask(a, xp) & _pair_mask(b, xp)
    return _finish(result[0], result[1], valid, xp)


def _positive(a, xp):
    return (a[0] > 0) | ((a[0] == 0) & (a[1] > 0))


def _dd_div_primal(a, b, xp):
    valid = _pair_mask(a, xp) & _pair_mask(b, xp) & (b[0] != 0)
    a = _safe_pair(a, valid, xp)
    b = (xp.where(valid, b[0], 1.0), xp.where(valid, b[1], 0.0))
    quotient = dd_from(_barrier(a[0] / b[0], xp), xp)
    # Two residual corrections; no claim of correctly rounded DD division.
    for _ in range(2):
        residual = _dd_add_primal(a, dd_neg(_dd_mul_primal(quotient, b, xp)), xp)
        correction = dd_from(_barrier(residual[0] / b[0], xp), xp)
        quotient = _dd_add_primal(quotient, correction, xp)
    return _finish(quotient[0], quotient[1], valid, xp)


def _dd_log_primal(a, xp):
    valid = _pair_mask(a, xp) & _positive(a, xp)
    high, low = xp.where(valid, a[0], 1.0), xp.where(valid, a[1], 0.0)
    # log(hi+lo)=log(hi)+log1p(lo/hi). The base libm log error remains.
    result = _dd_add_primal(dd_from(xp.log(high), xp),
                            dd_from(xp.log1p(low / high), xp), xp)
    return _finish(result[0], result[1], valid, xp)


def _dd_log1p_primal(a, xp):
    one_plus = _dd_add_primal(dd_from(1.0, xp), a, xp)
    valid = _pair_mask(a, xp) & _pair_mask(one_plus, xp) & _positive(one_plus, xp)
    # A normalized pair (-1, positive_low) can represent a legal argument
    # even though log1p(hi) is singular. Use log of the retained 1+a there,
    # and sanitize the unselected log1p branch before calling libm.
    base_valid = valid & (a[0] > -1.0)
    high, low = xp.where(base_valid, a[0], 0.0), xp.where(base_valid, a[1], 0.0)
    denominator = _dd_add_primal(dd_from(1.0, xp), dd_from(high, xp), xp)
    # This correction is passed to binary64 log1p below. A full DD Newton
    # division can reject negligible isolated correction products even when
    # the input and final ratio lie in the declared domain. Use the same
    # binary64 low-part correction boundary as _dd_log_primal; keep all range
    # checks and the retained one_plus fallback.
    ratio = dd_from(_barrier(low / dd_value(denominator, xp), xp), xp)
    ratio_value = dd_value(ratio, xp)
    ratio_valid = _pair_mask(ratio, xp) & (ratio_value > -1.0)
    result = _dd_add_primal(dd_from(xp.log1p(high), xp),
                            dd_from(xp.log1p(xp.where(ratio_valid, ratio_value, 0.0)), xp), xp)
    result = dd_where(base_valid, result, _dd_log_primal(one_plus, xp), xp)
    return _finish(result[0], result[1], valid & (~base_valid | ratio_valid), xp)


def _dd_exp_primal(a, xp):
    valid = _pair_mask(a, xp) & dd_abs_le(a, EXP_ARGUMENT_MAX, xp)
    high, low = xp.where(valid, a[0], 0.0), xp.where(valid, a[1], 0.0)
    base = dd_from(xp.exp(high), xp)
    correction = _dd_mul_primal(base, dd_from(xp.expm1(low), xp), xp)
    result = _dd_add_primal(base, correction, xp)
    return _finish(result[0], result[1], valid, xp)


def _binary_primal(a, b, operation, xp):
    if operation == "add":
        return _dd_add_primal(a, b, xp)
    if operation == "sub":
        return _dd_add_primal(a, dd_neg(b), xp)
    if operation == "mul":
        return _dd_mul_primal(a, b, xp)
    if operation == "div":
        return _dd_div_primal(a, b, xp)
    raise ValueError(f"unknown DD operation: {operation}")


def _unary_primal(a, operation, xp):
    if operation == "log":
        return _dd_log_primal(a, xp)
    if operation == "log1p":
        return _dd_log1p_primal(a, xp)
    if operation == "exp":
        return _dd_exp_primal(a, xp)
    raise ValueError(f"unknown DD operation: {operation}")


def _derivative_mul(coefficient, direction):
    # Preserve a known primal coefficient during tangent transposition.
    coefficient = _barrier(coefficient, jnp)
    direction = _barrier(direction, jnp)
    return _barrier(coefficient * direction, jnp)


def _linear_pair(coefficient, direction):
    # Both primal components enter the physical derivative coefficient.
    return _add(_derivative_mul(coefficient[0], direction),
                _derivative_mul(coefficient[1], direction), jnp)


@partial(jax.custom_jvp, nondiff_argnums=(2,))
def _jax_binary(a, b, operation):
    return _binary_primal(a, b, operation, jnp)


@_jax_binary.defjvp
def _jax_binary_jvp(operation, primals, tangents):
    a, b = primals
    da, db = (dd_value(value, jnp) for value in tangents)
    primal = _jax_binary(a, b, operation)
    if operation == "add":
        tangent = _add(da, db, jnp)
    elif operation == "sub":
        tangent = _sub(da, db, jnp)
    elif operation == "mul":
        tangent = _add(_linear_pair(a, db), _linear_pair(b, da), jnp)
    else:
        reciprocal = _dd_div_primal(dd_from(1.0, jnp), b, jnp)
        tangent = _linear_pair(reciprocal, _sub(da, _linear_pair(primal, db), jnp))
    return primal, (tangent, jnp.zeros_like(tangent))


@partial(jax.custom_jvp, nondiff_argnums=(1,))
def _jax_unary(a, operation):
    return _unary_primal(a, operation, jnp)


@_jax_unary.defjvp
def _jax_unary_jvp(operation, primals, tangents):
    (a,), (da,) = primals, tangents
    primal = _jax_unary(a, operation)
    if operation == "exp":
        coefficient = primal
    else:
        denominator = a if operation == "log" else _dd_add_primal(dd_from(1.0, jnp), a, jnp)
        coefficient = _dd_div_primal(dd_from(1.0, jnp), denominator, jnp)
    tangent = _linear_pair(coefficient, dd_value(da, jnp))
    return primal, (tangent, jnp.zeros_like(tangent))


@jax.custom_jvp
def _jax_product(a, b):
    return _dd_product_primal(a, b, jnp)


@_jax_product.defjvp
def _jax_product_jvp(primals, tangents):
    a, b = primals
    da, db = tangents
    primal = _jax_product(a, b)
    tangent = _add(_derivative_mul(a, db), _derivative_mul(b, da), jnp)
    return primal, (tangent, jnp.zeros_like(tangent))


def dd_product(a, b, xp=np):
    """Exact-product expansion of two checked binary64 operands."""
    return _jax_product(a, b) if xp is jnp else _dd_product_primal(a, b, xp)


def dd_add(a, b, xp=np):
    return _jax_binary(a, b, "add") if xp is jnp else _dd_add_primal(a, b, xp)


def dd_sub(a, b, xp=np):
    return _jax_binary(a, b, "sub") if xp is jnp else _dd_add_primal(a, dd_neg(b), xp)


def dd_mul(a, b, xp=np):
    return _jax_binary(a, b, "mul") if xp is jnp else _dd_mul_primal(a, b, xp)


def dd_div(a, b, xp=np):
    return _jax_binary(a, b, "div") if xp is jnp else _dd_div_primal(a, b, xp)


def dd_log(a, xp=np):
    return _jax_unary(a, "log") if xp is jnp else _dd_log_primal(a, xp)


def dd_log1p(a, xp=np):
    return _jax_unary(a, "log1p") if xp is jnp else _dd_log1p_primal(a, xp)


def dd_exp(a, xp=np):
    return _jax_unary(a, "exp") if xp is jnp else _dd_exp_primal(a, xp)


def dd_abs_le(a, bound, xp=np):
    """Compare a normalized pair against an exactly represented bound."""
    upper = (a[0] < bound) | ((a[0] == bound) & (a[1] <= 0))
    lower = (a[0] > -bound) | ((a[0] == -bound) & (a[1] >= 0))
    return _pair_mask(a, xp) & upper & lower


def near_invariants(B, delta, xp=np):
    return xp.all(dd_abs_le(B, B_THRESHOLD, xp), axis=(-2, -1)) & dd_abs_le(delta, DELTA_THRESHOLD, xp)


def dd_sum(a, axis=None, xp=np, *, keepdims=False):
    """Fixed-order reduction, composing the physical JVP of DD addition."""
    ndim = a[0].ndim
    axes = tuple(range(ndim)) if axis is None else ((axis,) if isinstance(axis, int) else tuple(axis))
    if any(not isinstance(item, int) or not -ndim <= item < ndim for item in axes):
        raise ValueError("DD reduction axis is invalid")
    axes = tuple(item % ndim for item in axes)
    if len(set(axes)) != len(axes):
        raise ValueError("DD reduction axes must be unique")
    if not axes:
        return a
    remaining = tuple(index for index in range(ndim) if index not in axes)
    reduced = dd_transpose(a, remaining + axes, xp)
    shape = tuple(a[0].shape[index] for index in remaining)
    length = prod(a[0].shape[index] for index in axes)
    reduced = tuple(item.reshape(shape + (length,)) for item in reduced)
    result = dd_from(xp.zeros(shape, dtype=xp.float64), xp)
    for index in range(length):
        result = dd_add(result, dd_getitem(reduced, (..., index)), xp)
    if keepdims:
        target = tuple(1 if index in axes else a[0].shape[index] for index in range(ndim))
        result = tuple(item.reshape(target) for item in result)
    return result


def dd_matmul(a, b, xp=np):
    """Broadcast (...,row,inner,column), then reduce inner in fixed order."""
    if a[0].ndim < 2 or b[0].ndim < 2 or a[0].shape[-1] != b[0].shape[-2]:
        raise ValueError("DD matmul requires matching final matrix axes")
    products = dd_mul(tuple(value[..., :, :, None] for value in a),
                      tuple(value[..., None, :, :] for value in b), xp)
    return dd_sum(products, -2, xp)


def dd_cofactor(F, xp=np):
    if F[0].shape[-2:] != (2, 2):
        raise ValueError("DD cofactor is defined here for 2 by 2 matrices")
    return tuple(xp.stack((xp.stack((value[..., 1, 1], -value[..., 1, 0]), axis=-1),
                           xp.stack((-value[..., 0, 1], value[..., 0, 0]), axis=-1)), axis=-2)
                 for value in F)


def _nodal(value, xp):
    value = xp.asarray(value, dtype=xp.float64)
    if value.ndim >= 2 and value.shape[-2:] == (4, 2):
        return value
    if value.ndim >= 1 and value.shape[-1] == 8:
        return value.reshape(value.shape[:-1] + (4, 2))
    raise ValueError("split fields must end in (8,) or (4,2)")


def kinematics_pairs(lift, w, grad, hessian, xp=np):
    """Checked single-element or batched fields, with no log or inverse.

    Keys F/G/B have shape (...,9,2,2), J/delta (...,9), Hu (...,2,2,2).
    Each field is a DD pair. ``supported`` is a scalar range verdict and
    ``near`` is the per-quadrature two-threshold selector. Raw J is computed
    directly from retained F, including in strongly compressed states.
    """
    lift, w = _nodal(lift, xp), _nodal(w, xp)
    grad, hessian = xp.asarray(grad, dtype=xp.float64), xp.asarray(hessian, dtype=xp.float64)
    if lift.shape != w.shape or grad.shape != (9, 4, 2) or hessian.shape != (4, 2, 2):
        raise ValueError("split components/reference operators have incompatible shapes")
    batch = lift.shape[:-2]
    G = dd_from(xp.zeros(batch + (9, 2, 2), dtype=xp.float64), xp)
    F = dd_from(xp.broadcast_to(xp.eye(2, dtype=xp.float64), batch + (9, 2, 2)), xp)
    Hu = dd_from(xp.zeros(batch + (2, 2, 2), dtype=xp.float64), xp)
    for nodal in (lift, w):
        for node in range(4):
            product = dd_product(nodal[..., node, None, :, None], grad[:, node, None, :], xp)
            G = dd_add(G, product, xp)
            F = dd_add(F, product, xp)
            Hu = dd_add(Hu, dd_product(nodal[..., node, :, None, None], hessian[node, None, :, :], xp), xp)
    transpose_G = dd_swapaxes(G, -1, -2, xp)
    B = dd_add(dd_add(G, transpose_G, xp), dd_matmul(G, transpose_G, xp), xp)
    g00, g11, g01, g10 = (dd_getitem(G, (..., i, j)) for i, j in ((0, 0), (1, 1), (0, 1), (1, 0)))
    delta = dd_add(dd_add(g00, g11, xp), dd_sub(dd_mul(g00, g11, xp), dd_mul(g01, g10, xp), xp), xp)
    J = dd_sub(dd_mul(dd_getitem(F, (..., 0, 0)), dd_getitem(F, (..., 1, 1)), xp),
               dd_mul(dd_getitem(F, (..., 0, 1)), dd_getitem(F, (..., 1, 0)), xp), xp)
    fields = dict(F=F, G=G, Hu=Hu, J=J, B=B, delta=delta)
    supported = operand_domain(lift, w, grad, hessian, xp=xp)
    for value in fields.values():
        supported = supported & pair_supported(value, xp)
    return {**fields, "supported": supported, "near": near_invariants(B, delta, xp)}


def hessian_action_pair(Hu, hessian, xp=np):
    """Retain Hu low parts through H-transpose Hu; output (...,4,2)."""
    hessian = xp.asarray(hessian, dtype=xp.float64)
    if Hu[0].shape[-3:] != (2, 2, 2) or hessian.shape != (4, 2, 2):
        raise ValueError("Hu/hessian shapes are incompatible")
    nodes = []
    for node in range(4):
        value = dd_from(xp.zeros(Hu[0].shape[:-2], dtype=xp.float64), xp)
        for first in range(2):
            for second in range(2):
                value = dd_add(value, dd_mul(dd_getitem(Hu, (..., first, second)),
                                             dd_from(hessian[node, first, second], xp), xp), xp)
        nodes.append(value)
    return tuple(xp.stack([value[component] for value in nodes], axis=-2) for component in (0, 1))
