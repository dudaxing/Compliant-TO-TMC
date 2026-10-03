"""Opt-in NumPy mechanical Jacobian of the split TMC weak residual.

Lift is fixed. This differentiates the physical shadow fields analytically,
including the deformation-dependent Hu regularization, rather than an energy
or the floating-point bookkeeping. No JAX execution or symmetrization occurs.
"""
from __future__ import annotations

from time import perf_counter

import numpy as np
from scipy import sparse

from . import compensated_invariants as ci
from .split_kernel_invariants_hu import (_divide_by_J, _scaled_mul, _small_product_branch, batch_response_split_numpy,
                                        assemble_split_numpy as _assemble_force)
from .split_state import SplitDisplacement
from .tmc import TMCError, TMCModel
from .tmc_kernel import KernelError, _coefficient, _ops


TANGENT_VERSION = "p26_q1_split_numpy_shadow_jacobian_v4"


def _take(pair, item):
    return tuple(value[item] for value in pair)


def _reshape(pair, shape):
    return tuple(value.reshape(shape) for value in pair)


def _tangent(fields, reference, lam, mu, kr):
    """DD action for all eight element directions; axes are (e, direction, force)."""
    count = len(fields["residual"])
    grad, hessian, weights = (reference[name] for name in ("grad", "hessian", "weights"))
    near = fields["small_branch"].astype(bool)
    small_products = _small_product_branch((fields["G_hi"], fields["G_lo"]), near,
                                           (grad, hessian, weights, lam, mu, kr))
    mul = lambda a, b: _scaled_mul(a, b, small_products)
    pairs = {name: (fields[name + "_hi"], fields[name + "_lo"])
             for name in ("F", "J", "Hu", "delta")}
    F, J, Hu, delta = (pairs[name] for name in ("F", "J", "Hu", "delta"))
    # Each direction changes one nodal fluctuation component, leaving lift fixed.
    dF = np.zeros((8, 9, 2, 2), dtype=np.float64)
    dHu = np.zeros((8, 2, 2, 2), dtype=np.float64)
    for node in range(4):
        for component in range(2):
            dF[2*node + component, :, component, :] = grad[:, node, :]
            dHu[2*node + component, component, :, :] = hessian[node]
    # The derivative is linear in its direction. Retain a common scale through
    # every directional term and contraction before restoring the full tensors.
    direction_scale = ci.dd_const(np.where(small_products, 2.0**128, 1.0))
    inverse_direction_scale = ci.dd_const(np.where(small_products, 2.0**-128, 1.0))
    dF, dHu = (mul(ci.dd_from(value), direction_scale) for value in (dF, dHu))
    cof = ci.dd_cofactor(F)
    dJ = ci.dd_sum(mul(_take(cof, (slice(None), None)), dF), (-2, -1))
    J_direction = _take(J, (slice(None), None))
    ratio = _divide_by_J(dJ, J_direction, near[:, None, :])
    T = _divide_by_J(cof, _take(J, (..., None, None)), near[..., None, None])
    T_direction = _take(T, (slice(None), None))
    # The 2D cofactor is linear, so d(cof F) = cof(dF).
    dT = ci.dd_sub(_divide_by_J(ci.dd_cofactor(dF), _take(J_direction, (..., None, None)),
                              near[:, None, :, None, None]),
                   mul(T_direction, _take(ratio, (..., None, None))))
    safe_delta = ci.dd_where(near, delta, ci.dd_const(0.))
    log_J = ci.dd_where(near, ci.dd_log1p(safe_delta), ci.dd_log(J))
    lam_q = ci.dd_from(lam[:, None])
    mu_q = ci.dd_from(mu[:, None])
    coefficient = ci.dd_sub(mul(lam_q, log_J), mu_q)
    dP = ci.dd_add(mul(ci.dd_from(mu[:, None, None, None, None]), dF),
                   mul(_take(mul(ci.dd_from(lam[:, None, None]), ratio),
                                   (..., None, None)), T_direction))
    dP = ci.dd_add(dP, mul(_take(coefficient, (slice(None), None, slice(None), None, None)), dT))
    stress_grad = mul(_take(dP, (..., None, slice(None), slice(None))),
                            ci.dd_from(grad[:, :, None, :]))
    material = ci.dd_sum(mul(ci.dd_from(weights[:, None, None]),
                                 ci.dd_sum(stress_grad, -1)), -3)
    material = _reshape(material, (count, 8, 8))
    action = _reshape(ci.hessian_action_pair(Hu, hessian), (count, 8))
    d_action = _reshape(ci.hessian_action_pair(dHu, hessian), (8, 8))
    weighted_exp = mul(ci.dd_from(weights), ci.dd_exp(mul(ci.dd_const(-5.), J)))
    scale = mul(ci.dd_const(kr), ci.dd_sum(weighted_exp, -1))
    d_scale = mul(mul(ci.dd_const(-5.), ci.dd_const(kr)),
                        ci.dd_sum(mul(_take(weighted_exp, (slice(None), None)), dJ), -1))
    regularization = ci.dd_add(mul(_take(scale, (..., None, None)), d_action),
                              mul(_take(d_scale, (..., None)),
                                        _take(action, (slice(None), None))))
    components = dict(total_tangent=ci.dd_add(material, regularization),
                      material_tangent=material, regularization_tangent=regularization)
    components = {name: mul(value, inverse_direction_scale) for name, value in components.items()}
    for name, value in components.items():
        if not bool(ci.pair_supported(value)):
            raise KernelError("NumPy tangent exceeded the declared compensated arithmetic support range",
                              code="unsupported_arithmetic_range", details={"field": name})
    return {name: np.swapaxes(ci.dd_value(value), 1, 2) for name, value in components.items()}


def batch_tangent_components_split_numpy(lift_e, fluctuation_e, ops, lam, mu, kr):
    """Return total/material/regularization unsymmetrized (ne,8,8) Jacobians."""
    fields = batch_response_split_numpy(lift_e, fluctuation_e, ops, lam, mu, kr)
    reference = _ops(ops)
    count = len(fields["residual"])
    with np.errstate(over="ignore", invalid="ignore", divide="ignore", under="ignore"):
        return _tangent(fields, reference, _coefficient(lam, "lam", count),
                        _coefficient(mu, "mu", count), float(kr))


def batch_tangent_split_numpy(lift_e, fluctuation_e, ops, lam, mu, kr):
    """Return the actual unsymmetrized (ne,8,8) mechanical Jacobian, using NumPy."""
    return batch_tangent_components_split_numpy(lift_e, fluctuation_e, ops, lam, mu, kr)["total_tangent"]


def assemble_tangent_split_numpy(model, state):
    """Assemble a full-DOF CSC Jacobian, retaining supported and fixed DOFs."""
    if not isinstance(model, TMCModel):
        raise TMCError("model must be TMCModel", code="invalid_model")
    if not isinstance(state, SplitDisplacement) or state.ndof != model.ndof:
        raise TMCError("state must be a matching SplitDisplacement", code="invalid_displacement")
    values = batch_tangent_split_numpy(state.lift[model.edofs], state.fluctuation[model.edofs],
                                       model.ops, model.lam, model.mu, model.kr)
    return _assemble_tangent(model, values)


def _assemble_tangent(model, values):
    matrix = sparse.coo_matrix((values.ravel(), (model._rows, model._cols)),
                               shape=(model.ndof, model.ndof)).tocsc()
    matrix.sum_duplicates()
    if not np.all(np.isfinite(matrix.data)):
        raise TMCError("NumPy assembled tangent is nonfinite", code="nonfinite")
    return matrix


def assemble_split_numpy(model, state, *, tangent=True):
    """Force and optional mechanical Jacobian, sharing one NumPy force evaluation."""
    if not isinstance(tangent, (bool, np.bool_)):
        raise KernelError("tangent must be boolean", code="invalid_input")
    _, internal, fields = _assemble_force(model, state)
    matrix = None
    if tangent:
        begin = perf_counter()
        with np.errstate(over="ignore", invalid="ignore", divide="ignore", under="ignore"):
            values = _tangent(fields, model.ops, model.lam, model.mu, model.kr)["total_tangent"]
        fields["tangent"] = values
        fields["timing_seconds"]["kernel_and_transfer"] += perf_counter() - begin
        begin = perf_counter()
        matrix = _assemble_tangent(model, values)
        fields["timing_seconds"]["assembly"] += perf_counter() - begin
    return matrix, internal, fields
