"""Opt-in split small-invariant/Hu arithmetic candidate, not a new model.

High/low pairs remain authoritative through stress and both weak-force
contractions. The final arrays are binary64 observations. Mechanical AD fixes
lift and differentiates the actual residual, including exp(-5 J); its matrix
is never symmetrized. No default kernel or runtime configuration is changed.
"""
from __future__ import annotations

from time import perf_counter

import jax
import jax.numpy as jnp
import numpy as np
from scipy import sparse

from . import compensated_invariants as ci
from .compensated_kinematics import COMPILER_OPTIONS
from .split_kernel_compensated import _component, _reject_J
from .split_state import SplitDisplacement
from .tmc import TMCError, TMCModel
from .tmc_kernel import KernelError, _array, _coefficient, _ops, _runtime


KERNEL_VERSION = "p26_q1_split_invariants_hu_v1"
B_LIMIT = 1.0 / 16
DELTA_LIMIT = 1.0 / 64
PAIR_FIELDS = ("F", "G", "Hu", "J", "B", "delta")


def _index(pair, key):
    return pair[0][key], pair[1][key]


def _reshape(pair, shape):
    return pair[0].reshape(shape), pair[1].reshape(shape)


def _small_invariant_branch(B, delta, xp=np):
    """Coordinate-dependent arithmetic selector, not a material invariant."""
    return xp.all(ci.dd_abs_le(B, B_LIMIT, xp), axis=(-2, -1)) & ci.dd_abs_le(delta, DELTA_LIMIT, xp)


def _kinematics(lift, fluctuation, grad, hessian, xp):
    pairs = ci.kinematics_pairs(lift, fluctuation, grad, hessian, xp)
    values = {name: ci.dd_value(pairs[name], xp) for name in PAIR_FIELDS}
    values.update(near=_small_invariant_branch(pairs["B"], pairs["delta"], xp),
                  pairs=pairs, supported=pairs["supported"])
    return values


def _range_error(source):
    return KernelError(source + " exceeded the declared compensated arithmetic support range",
                       code="unsupported_arithmetic_range")


def _numpy_kinematics(lift, fluctuation, ops):
    with np.errstate(over="ignore", invalid="ignore", divide="ignore", under="ignore"):
        values = _kinematics(lift, fluctuation, ops["grad"], ops["hessian"], np)
    if not bool(values["supported"]) or any(not np.all(np.isfinite(values[k])) for k in PAIR_FIELDS):
        raise _range_error("NumPy kinematics")
    return values


def determinants_split(lift_e, fluctuation_e, ops):
    """Total raw J, including nonpositive J; no logarithm or inverse."""
    single = np.shape(lift_e) == (8,)
    lift = _component(lift_e, "lift_e", single=single)
    fluctuation = _component(fluctuation_e, "fluctuation_e", single=single)
    if lift.shape != fluctuation.shape:
        raise KernelError("split element component shapes differ", code="invalid_shape")
    return _numpy_kinematics(lift, fluctuation, _ops(ops))["J"]


def _pair_finite(pair, xp):
    return ci.pair_supported(pair, xp)


def _coefficient_support(weights, lam, mu, kr, xp):
    valid = xp.asarray(True)
    for value in (weights, lam, mu, kr):
        valid = valid & _pair_finite(ci.dd_from(value, xp), xp)
    return valid


def _response(lift, fluctuation, grad, hessian, weights, lam, mu, kr, xp):
    """Validated element response, sharing the NumPy/JAX operation order."""
    values = _kinematics(lift, fluctuation, grad, hessian, xp)
    pairs, near = values["pairs"], values["near"]
    F, G, Hu, J, B, delta = (pairs[name] for name in PAIR_FIELDS)
    c = lambda number: ci.dd_const(number, xp)
    add = lambda a, b: ci.dd_add(a, b, xp)
    sub = lambda a, b: ci.dd_sub(a, b, xp)
    mul = lambda a, b: ci.dd_mul(a, b, xp)
    eye = ci.dd_from(xp.eye(2, dtype=lift.dtype), xp)
    T = ci.dd_div(ci.dd_cofactor(F, xp), _index(J, (..., None, None)), xp)
    # Unselected log1p receives zero: a compressed direct-branch state must
    # not evaluate log1p(delta) after its rounded delta has become -1.
    small_delta = ci.dd_where(near, delta, c(0.0), xp)
    log_small = ci.dd_log1p(small_delta, xp)
    log_J = ci.dd_where(near, log_small, ci.dd_log(J, xp), xp)
    lambda_pair = _index(ci.dd_from(lam, xp), (..., None))
    mu_pair = _index(ci.dd_from(mu, xp), (..., None))
    mu_matrix = _index(mu_pair, (..., None, None))
    coefficient = sub(mul(lambda_pair, log_J), mu_pair)
    direct_P = add(mul(mu_matrix, F), mul(_index(coefficient, (..., None, None)), T))
    small_B = ci.dd_where(near[..., None, None], B, c(0.0), xp)
    incremental_tensor = add(mul(mu_matrix, small_B),
                             mul(_index(mul(lambda_pair, log_small), (..., None, None)), eye))
    small_P = ci.dd_matmul(incremental_tensor, T, xp)
    P = ci.dd_where(near[..., None, None], small_P, direct_P, xp)
    axes = tuple(range(T[0].ndim-2)) + (T[0].ndim-1, T[0].ndim-2)
    S = ci.dd_matmul(ci.dd_transpose(T, axes, xp), P, xp)

    # Keep product residuals in the quadrature and gradient contractions.
    stress_grad = mul(_index(P, (..., None, slice(None), slice(None))),
                      ci.dd_from(grad[:, :, None, :], xp))
    element_material = ci.dd_sum(stress_grad, -1, xp)
    weighted_material = mul(ci.dd_from(weights[:, None, None], xp), element_material)
    force_shape = lift.shape[:-1] + (8,)
    material_pair = _reshape(ci.dd_sum(weighted_material, -3, xp), force_shape)
    action_pair = _reshape(ci.hessian_action_pair(Hu, hessian, xp), force_shape)
    exponential = ci.dd_exp(mul(c(-5.0), J), xp)
    scale = mul(ci.dd_from(kr, xp), ci.dd_sum(mul(ci.dd_from(weights, xp), exponential), -1, xp))
    regularization_pair = mul(_index(scale, (..., None)), action_pair)
    residual_pair = add(material_pair, regularization_pair)

    # r(delta) = delta-log1p(delta), truncated only in the auxiliary energy.
    # Its gradient is NOT used for P or the residual Jacobian.
    remainder = c(1.0 / 14)
    for power in range(13, 1, -1):
        remainder = add(mul(remainder, small_delta), c((-1.0)**power / power))
    remainder = mul(mul(small_delta, small_delta), remainder)
    G_small = ci.dd_where(near[..., None, None], G, c(0.0), xp)
    diagonal = sub(_index(G_small, (..., 0, 0)), _index(G_small, (..., 1, 1)))
    shear = add(_index(G_small, (..., 0, 1)), _index(G_small, (..., 1, 0)))
    shear_deviator = add(mul(diagonal, diagonal), mul(shear, shear))
    small_energy = mul(c(0.5), add(mul(lambda_pair, mul(log_small, log_small)),
                                 mul(mu_pair, add(shear_deviator, mul(c(2.0), remainder)))))
    trace_C = ci.dd_sum(ci.dd_sum(mul(F, F), -1, xp), -1, xp)
    direct_energy = mul(c(0.5), add(mul(lambda_pair, mul(log_J, log_J)),
                                  mul(mu_pair, sub(sub(trace_C, c(2.0)), mul(c(2.0), log_J)))))
    density = ci.dd_where(near, small_energy, direct_energy, xp)
    energy_pair = ci.dd_sum(mul(ci.dd_from(weights, xp), density), -1, xp)
    output_pairs = dict(residual=residual_pair, material_residual=material_pair,
                        regularization_residual=regularization_pair,
                        stress_first_piola=P, stress_second_piola=S, material_energy=energy_pair)
    supported = values["supported"] & _coefficient_support(weights, lam, mu, kr, xp)
    for value in (*output_pairs.values(), T, log_J, exponential, action_pair):
        supported = supported & _pair_finite(value, xp)
    result = {name: ci.dd_value(value, xp) for name, value in output_pairs.items()}
    for name in PAIR_FIELDS:
        result[name] = values[name]
        result[name + "_hi"], result[name + "_lo"] = pairs[name]
    result["small_branch"] = near.astype(xp.float64)
    result["arithmetic_supported"] = supported.astype(xp.float64)
    return result["residual"], result


def _residual_with_aux(lift, fluctuation, grad, hessian, weights, lam, mu, kr):
    return _response(lift, fluctuation, grad, hessian, weights, lam, mu, kr, jnp)


_jacobian_with_aux = jax.jacfwd(_residual_with_aux, argnums=1, has_aux=True)


def _with_tangent(lift, fluctuation, grad, hessian, weights, lam, mu, kr):
    tangent, values = _jacobian_with_aux(lift, fluctuation, grad, hessian, weights, lam, mu, kr)
    return {**values, "tangent": tangent}


def _without_tangent(lift, fluctuation, grad, hessian, weights, lam, mu, kr):
    return _residual_with_aux(lift, fluctuation, grad, hessian, weights, lam, mu, kr)[1]


def _guarded_batch(lift, fluctuation, grad, hessian, weights, lam, mu, kr, *, tangent):
    kinematics = _kinematics(lift, fluctuation, grad, hessian, jnp)
    valid = kinematics["supported"] & jnp.all(kinematics["J"] > 0)
    valid = valid & _coefficient_support(weights, lam, mu, kr, jnp)

    def evaluate(_):
        function = _with_tangent if tangent else _without_tangent
        return jax.vmap(function, in_axes=(0, 0, None, None, None, 0, 0, None))(
            lift, fluctuation, grad, hessian, weights, lam, mu, kr)

    def reject(_):
        count, dtype = lift.shape[0], lift.dtype
        invalid = lambda shape: jnp.full(shape, jnp.nan, dtype=dtype)
        result = dict(residual=invalid((count, 8)), material_residual=invalid((count, 8)),
                      regularization_residual=invalid((count, 8)), material_energy=invalid((count,)),
                      stress_first_piola=invalid((count, 9, 2, 2)),
                      stress_second_piola=invalid((count, 9, 2, 2)),
                      small_branch=kinematics["near"].astype(dtype),
                      arithmetic_supported=jnp.zeros((count,), dtype=dtype))
        for name in PAIR_FIELDS:
            result[name] = kinematics[name]
            result[name + "_hi"], result[name + "_lo"] = kinematics["pairs"][name]
        if tangent:
            result["tangent"] = invalid((count, 8, 8))
        return result

    # Scalar cond outside vmap prevents rejected logs/inverses from executing.
    return jax.lax.cond(valid, evaluate, reject, operand=None)


_batch_with_tangent = jax.jit(lambda *args: _guarded_batch(*args, tangent=True),
                            compiler_options=COMPILER_OPTIONS)
_batch_without_tangent = jax.jit(lambda *args: _guarded_batch(*args, tangent=False),
                               compiler_options=COMPILER_OPTIONS)


def _numpy_response(lift_e, fluctuation_e, ops, lam, mu, kr):
    """Shared input checks and complete force evaluation, before any JAX work."""
    lift, fluctuation = _component(lift_e, "lift_e"), _component(fluctuation_e, "fluctuation_e")
    if lift.shape != fluctuation.shape:
        raise KernelError("split element component shapes differ", code="invalid_shape")
    reference, count = _ops(ops), len(lift)
    lam_values, mu_values = _coefficient(lam, "lam", count), _coefficient(mu, "mu", count)
    kr_value = _array(kr, "kr")
    if kr_value.shape != () or float(kr_value) < 0:
        raise KernelError("kr must be a nonnegative scalar")
    if np.any(mu_values < 0) or np.any(lam_values + 2*mu_values/3 < 0):
        raise KernelError("material shear and bulk moduli must be nonnegative")
    kin = _numpy_kinematics(lift, fluctuation, reference)
    _reject_J(kin["J"], "NumPy")
    if not bool(_coefficient_support(reference["weights"], lam_values, mu_values, kr_value, np)):
        raise _range_error("NumPy coefficients")
    # A broadcast NumPy evaluation rejects unsupported intermediate ranges
    # before any compiled constitutive work. It uses the identical DD formulas.
    with np.errstate(over="ignore", invalid="ignore", divide="ignore", under="ignore"):
        _, checked = _response(lift, fluctuation, reference["grad"], reference["hessian"],
                               reference["weights"], lam_values, mu_values, float(kr_value), np)
        if checked["arithmetic_supported"] != 1.0:
            raise _range_error("NumPy response")
    args = (lift, fluctuation, reference["grad"], reference["hessian"], reference["weights"],
            lam_values, mu_values, float(kr_value))
    checked["arithmetic_supported"] = np.full(count, 1.0, dtype=np.float64)
    return args, checked


def _check_output(result, source):
    # Nonpositive physical J has its own code; supported arithmetic is separate.
    if not np.all(np.isfinite(result["J"])):
        raise _range_error(source + " kinematics")
    _reject_J(result["J"], source)
    if not np.all(result["arithmetic_supported"] == 1.0):
        raise _range_error(source + " response")
    for name, value in result.items():
        if value.dtype != np.dtype("float64"):
            raise KernelError("split output is not float64", code="runtime_configuration", details={"field": name})
        if not np.all(np.isfinite(value)):
            raise KernelError("split output is nonfinite", code="nonfinite", details={"field": name})
    return result


def batch_response_split_numpy(lift_e, fluctuation_e, ops, lam, mu, kr):
    """Complete force-only response for (ne,8) split arrays, using NumPy.

    Returns material, regularization and total element forces with stresses,
    energy and retained kinematic pairs, in the same shapes as the compiled
    force-only entry. Positive J and the declared arithmetic range are checked.
    No JAX runtime, compilation or tangent evaluation is invoked.
    """
    _, result = _numpy_response(lift_e, fluctuation_e, ops, lam, mu, kr)
    return _check_output(result, "NumPy")


def batch_response_split(lift_e, fluctuation_e, ops, lam, mu, kr, *, tangent=True):
    """Validated binary64 observations and the actual residual Jacobian."""
    if not isinstance(tangent, (bool, np.bool_)):
        raise KernelError("tangent must be boolean", code="invalid_input")
    args, _ = _numpy_response(lift_e, fluctuation_e, ops, lam, mu, kr)
    _runtime()
    function = _batch_with_tangent if tangent else _batch_without_tangent
    result = {key: np.asarray(value) for key, value in function(*args).items()}
    return _check_output(result, "JAX")


def _assemble_split(model, state, *, tangent, numpy=False):
    if not isinstance(model, TMCModel):
        raise TMCError("model must be TMCModel", code="invalid_model")
    if not isinstance(state, SplitDisplacement) or state.ndof != model.ndof:
        raise TMCError("state must be a matching SplitDisplacement", code="invalid_displacement")
    begin = perf_counter()
    args = (state.lift[model.edofs], state.fluctuation[model.edofs],
            model.ops, model.lam, model.mu, model.kr)
    fields = batch_response_split_numpy(*args) if numpy else batch_response_split(*args, tangent=tangent)
    kernel_time = perf_counter() - begin
    begin_assembly = perf_counter()
    internal = np.bincount(model.edofs.ravel(), weights=fields["residual"].ravel(), minlength=model.ndof)
    matrix = None
    if tangent:
        matrix = sparse.coo_matrix((fields["tangent"].ravel(), (model._rows, model._cols)),
                                   shape=(model.ndof, model.ndof)).tocsc()
        matrix.sum_duplicates()
    if not np.all(np.isfinite(internal)) or (matrix is not None and not np.all(np.isfinite(matrix.data))):
        raise TMCError("split assembled values are nonfinite", code="nonfinite")
    fields["timing_seconds"] = {"kernel_and_transfer": kernel_time, "assembly": perf_counter() - begin_assembly}
    return matrix, internal, fields


def assemble_split_numpy(model, state):
    """Return (None, global internal force, fields) without a tangent or JIT."""
    return _assemble_split(model, state, tangent=False, numpy=True)


def assemble_split(model, state, *, tangent=True):
    return _assemble_split(model, state, tangent=tangent)
