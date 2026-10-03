"""Q1 plane-strain TMC for an explicit two-component displacement state.

This opt-in kernel preserves the previous weak form and its nonsymmetric
Jacobian. It never constructs a rounded nodal sum. Small G is retained for
the increment-based material formula; F is formed as (I + grad(lift)) +
grad(fluctuation) for compression. The lift is fixed during differentiation.
No runtime configuration is changed at import or during evaluation.
"""
from __future__ import annotations

from time import perf_counter

import jax
import jax.numpy as jnp
import numpy as np
from scipy import sparse

from .split_state import SplitDisplacement
from .tmc import TMCError, TMCModel
from .tmc_kernel import KernelError, _array, _coefficient, _ops, _runtime


KERNEL_VERSION = "p26_q1_split_displacement_v1"


def _component(value, name, *, single=False):
    raw = np.asarray(value)
    if raw.dtype.kind not in "iuf":
        raise KernelError(f"{name} must be real numeric values", code="invalid_input")
    values = _array(raw, name)
    if single:
        valid = values.shape == (8,)
    else:
        valid = values.ndim == 2 and values.shape[1] == 8 and values.shape[0] > 0
    if not valid:
        raise KernelError(f"{name} must have shape {'(8,)' if single else '(ne,8), ne>0'}", code="invalid_shape")
    return values


def _kinematics(lift, fluctuation, grad, hessian, xp):
    """The same explicit operation order for one element or a NumPy batch."""
    shape = lift.shape[:-1] + (4, 2)
    L, w = lift.reshape(shape), fluctuation.reshape(shape)
    GL = xp.einsum("...ai,qaj->...qij", L, grad)
    Gw = xp.einsum("...ai,qaj->...qij", w, grad)
    G = GL + Gw
    F_left = xp.eye(2, dtype=lift.dtype) + GL
    if xp is jnp:
        # Parentheses alone do not define an optimization boundary for XLA.
        # The primitive has identity JVP/batching rules; no stop_gradient.
        F_left = jax.lax.optimization_barrier(F_left)
    F = F_left + Gw
    HL = xp.einsum("...ai,ajk->...ijk", L, hessian)
    Hw = xp.einsum("...ai,ajk->...ijk", w, hessian)
    Hu = HL + Hw
    near = xp.max(xp.abs(G), axis=(-1, -2)) <= 0.01
    delta = G[..., 0, 0] + G[..., 1, 1] + G[..., 0, 0]*G[..., 1, 1] - G[..., 0, 1]*G[..., 1, 0]
    near_delta = xp.where(near, delta, 0.0)
    direct_J = F[..., 0, 0]*F[..., 1, 1] - F[..., 0, 1]*F[..., 1, 0]
    J = xp.where(near, 1.0 + near_delta, direct_J)
    return dict(G=G, F=F, Hu=Hu, J=J, near=near, near_delta=near_delta)


def _numpy_kinematics(lift, fluctuation, ops):
    with np.errstate(over="ignore", invalid="ignore"):
        values = _kinematics(lift, fluctuation, ops["grad"], ops["hessian"], np)
    if any(not np.all(np.isfinite(values[key])) for key in ("G", "F", "Hu", "J")):
        raise KernelError("total split kinematics are nonfinite", code="nonfinite")
    return values


def determinants_split(lift_e, fluctuation_e, ops):
    """Return raw total J without logs/inverses, including nonpositive values.

    Both components must be (8,) or both (ne,8). Lift-only J is irrelevant.
    Nonfinite kinematics are rejected instead of returning a domain verdict.
    """
    single = np.shape(lift_e) == (8,)
    lift = _component(lift_e, "lift_e", single=single)
    fluctuation = _component(fluctuation_e, "fluctuation_e", single=single)
    if lift.shape != fluctuation.shape:
        raise KernelError("split element component shapes differ", code="invalid_shape")
    reference = _ops(ops)
    return _numpy_kinematics(lift, fluctuation, reference)["J"]


def _residual_with_aux(lift, fluctuation, grad, hessian, weights, lam, mu, kr):
    """Actual weak residual on the positive-J branch, with fixed lift."""
    values = _kinematics(lift, fluctuation, grad, hessian, jnp)
    G, F, Hu, J = (values[key] for key in ("G", "F", "Hu", "J"))
    near, delta = values["near"], values["near_delta"]
    inverse_transpose = jnp.stack((
        jnp.stack((F[:, 1, 1], -F[:, 1, 0]), axis=-1),
        jnp.stack((-F[:, 0, 1], F[:, 0, 0]), axis=-1),
    ), axis=-2) / J[:, None, None]
    log_J = jnp.where(near, jnp.log1p(delta), jnp.log(J))
    coefficient = lam*log_J - mu
    direct_P = mu*F + coefficient[:, None, None]*inverse_transpose
    G_near = jnp.where(near[:, None, None], G, 0.0)
    T_near = jnp.where(near[:, None, None], inverse_transpose, jnp.eye(2, dtype=lift.dtype))
    log_near = jnp.log1p(delta)
    B = G_near + jnp.swapaxes(G_near, -1, -2) + jnp.einsum("qik,qjk->qij", G_near, G_near)
    incremental_P = mu*jnp.einsum("qik,qkj->qij", B, T_near) + lam*log_near[:, None, None]*T_near
    P = jnp.where(near[:, None, None], incremental_P, direct_P)
    inverse_C = jnp.einsum("qki,qkj->qij", inverse_transpose, inverse_transpose)
    direct_S = mu*jnp.eye(2, dtype=lift.dtype) + coefficient[:, None, None]*inverse_C
    S = jnp.where(near[:, None, None], jnp.einsum("qki,qkj->qij", T_near, incremental_P), direct_S)
    material = jnp.einsum("q,qaj,qij->ai", weights, grad, P).reshape(8)
    hessian_force = jnp.einsum("ajk,ijk->ai", hessian, Hu).reshape(8)
    regularization = kr*jnp.sum(weights*jnp.exp(-5*J))*hessian_force
    residual = material + regularization
    trace_C = jnp.sum(F*F, axis=(-1, -2))
    direct_energy = 0.5*(lam*log_J**2 + mu*(trace_C - 2 - 2*log_J))
    remainder = jnp.zeros_like(delta)
    for power in range(14, 1, -1):
        remainder = remainder*delta + (-1.0)**power/power
    remainder = delta**2*remainder
    shear_deviator = (G_near[:, 0, 0] - G_near[:, 1, 1])**2 + (G_near[:, 0, 1] + G_near[:, 1, 0])**2
    incremental_energy = 0.5*(lam*log_near**2 + mu*(shear_deviator + 2*remainder))
    energy_density = jnp.where(near, incremental_energy, direct_energy)
    return residual, dict(residual=residual, material_residual=material,
                          regularization_residual=regularization, G=G, F=F, Hu=Hu,
                          J=J, stress_second_piola=S,
                          material_energy=jnp.sum(weights*energy_density))


_jacobian_with_aux = jax.jacfwd(_residual_with_aux, argnums=1, has_aux=True)


def _with_tangent(lift, fluctuation, grad, hessian, weights, lam, mu, kr):
    tangent, values = _jacobian_with_aux(lift, fluctuation, grad, hessian, weights, lam, mu, kr)
    return {**values, "tangent": tangent}


def _without_tangent(lift, fluctuation, grad, hessian, weights, lam, mu, kr):
    return _residual_with_aux(lift, fluctuation, grad, hessian, weights, lam, mu, kr)[1]


def _guarded_batch(lift, fluctuation, grad, hessian, weights, lam, mu, kr, *, tangent):
    # A scalar condition outside vmap is important: vmap of per-element cond
    # can turn it into select, evaluating an invalid branch's log/inverse.
    kinematics = _kinematics(lift, fluctuation, grad, hessian, jnp)
    valid = jnp.all(kinematics["J"] > 0)
    for key in ("G", "F", "Hu", "J"):
        valid = valid & jnp.all(jnp.isfinite(kinematics[key]))

    def evaluate(_):
        function = _with_tangent if tangent else _without_tangent
        return jax.vmap(function, in_axes=(0, 0, None, None, None, 0, 0, None))(
            lift, fluctuation, grad, hessian, weights, lam, mu, kr)

    def reject(_):
        count, dtype = lift.shape[0], lift.dtype
        invalid = lambda shape: jnp.full(shape, jnp.nan, dtype=dtype)
        result = dict(residual=invalid((count, 8)), material_residual=invalid((count, 8)),
                      regularization_residual=invalid((count, 8)), material_energy=invalid((count,)),
                      stress_second_piola=invalid((count, 9, 2, 2)),
                      **{key: kinematics[key] for key in ("G", "F", "Hu", "J")})
        if tangent:
            result["tangent"] = invalid((count, 8, 8))
        return result

    return jax.lax.cond(valid, evaluate, reject, operand=None)


_batch_with_tangent = jax.jit(lambda *args: _guarded_batch(*args, tangent=True))
_batch_without_tangent = jax.jit(lambda *args: _guarded_batch(*args, tangent=False))


def _reject_J(J, source):
    if not np.all(np.isfinite(J)):
        raise KernelError(f"{source} total J is nonfinite", code="nonfinite")
    if np.any(J <= 0):
        raise KernelError(f"{source} total J must be positive", code="invalid_J", details={
            "kinematic_guard": source, "min_J": float(np.min(J)),
            "invalid_count": int(np.count_nonzero(J <= 0)),
            "first_invalid_element_quadrature_indices": np.argwhere(J <= 0)[:8].tolist()})


def batch_response_split(lift_e, fluctuation_e, ops, lam, mu, kr, *, tangent=True):
    """Return binary64 element fields and d(residual)/d(fluctuation).

    Component inputs are (ne,8); coefficients are scalar or (ne,). kr has the
    same solid-derived, full-domain meaning as the old kernel. Both guards
    use total kinematics; an invalid J is never clipped into a valid response.
    CPU and JAX float64 must be selected explicitly by the calling program.
    """
    if not isinstance(tangent, (bool, np.bool_)):
        raise KernelError("tangent must be boolean", code="invalid_input")
    lift = _component(lift_e, "lift_e")
    fluctuation = _component(fluctuation_e, "fluctuation_e")
    if lift.shape != fluctuation.shape:
        raise KernelError("split element component shapes differ", code="invalid_shape")
    reference = _ops(ops)
    count = len(lift)
    lam_values, mu_values = _coefficient(lam, "lam", count), _coefficient(mu, "mu", count)
    kr_value = _array(kr, "kr")
    if kr_value.shape != () or float(kr_value) < 0:
        raise KernelError("kr must be a nonnegative scalar")
    if np.any(mu_values < 0) or np.any(lam_values + 2*mu_values/3 < 0):
        raise KernelError("material shear and bulk moduli must be nonnegative")
    _reject_J(_numpy_kinematics(lift, fluctuation, reference)["J"], "NumPy")
    _runtime()
    function = _batch_with_tangent if tangent else _batch_without_tangent
    values = function(lift, fluctuation, reference["grad"], reference["hessian"], reference["weights"],
                      lam_values, mu_values, float(kr_value))
    result = {key: np.asarray(value) for key, value in values.items()}
    # The JAX invalid branch returns raw J and sentinels. Check its domain
    # before other fields so a rejected state has an explicit failure reason.
    _reject_J(result["J"], "JAX")
    for name, value in result.items():
        if value.dtype != np.dtype("float64"):
            raise KernelError("split output is not float64", code="runtime_configuration", details={"field": name})
        if not np.all(np.isfinite(value)):
            raise KernelError("split output is nonfinite", code="nonfinite", details={"field": name})
    return result


def assemble_split(model, state, *, tangent=True):
    """Return (K or None, full internal force, fields with assembly timing).

    ``state`` must be explicit; no ndarray or display-array fallback exists.
    The old model's DOF maps and sparse ordering are reused without modifying
    them. The actual element Jacobians are assembled without symmetrization.
    """
    if not isinstance(model, TMCModel):
        raise TMCError("model must be TMCModel", code="invalid_model")
    if not isinstance(state, SplitDisplacement) or state.ndof != model.ndof:
        raise TMCError("state must be a matching SplitDisplacement", code="invalid_displacement")
    begin = perf_counter()
    fields = batch_response_split(state.lift[model.edofs], state.fluctuation[model.edofs],
                                  model.ops, model.lam, model.mu, model.kr, tangent=tangent)
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
