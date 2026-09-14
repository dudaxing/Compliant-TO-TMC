"""Plane-strain Q1 TMC element residual and its unsymmetrized Jacobian.

The material is the P26 logarithmic compressible Neo-Hookean model. HuHu is
added to the weak residual, including its exp(-5 J) deformation scaling; it
is not obtained from a substitute total energy. No configuration is changed
at import: callers explicitly enable JAX float64 and select its CPU backend.
"""

from __future__ import annotations

import jax
import jax.numpy as jnp
import numpy as np

KERNEL_VERSION = "p26_q1_incremental_piola_huhu_v3"


class KernelError(ValueError):
    """A kernel input or numerical validity failure."""

    def __init__(self, message, *, code="invalid_input", details=None):
        super().__init__(message)
        self.code = code
        self.details = {} if details is None else details


def _array(value, name):
    raw = np.asarray(value)
    if np.iscomplexobj(raw):
        raise KernelError(f"{name} must be real.", code="invalid_input")
    try:
        result = np.asarray(raw, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise KernelError(f"{name} must be numeric.", code="invalid_input") from exc
    if not np.all(np.isfinite(result)):
        raise KernelError(f"{name} must be finite.", code="nonfinite")
    return result


def _positive(value, name):
    number = _array(value, name)
    if number.shape != () or float(number) <= 0:
        raise KernelError(f"{name} must be a positive scalar.")
    return float(number)


def operators(hx, hy, thickness=1.0):
    """Build reference operators; xi varies slowly, eta varies quickly.

    Nodes are BL, BR, TR, TL. grad[q,a,J] uses physical reference derivatives.
    hessian[a,J,K] includes both xy and yx. Weights already include reference
    area Jacobian and thickness; sum(weights) = hx*hy*thickness.
    This preparation is NumPy float64 and does not initialize the JAX runtime.
    """
    hx, hy, thickness = (_positive(v, n) for v, n in (
        (hx, "hx"), (hy, "hy"), (thickness, "thickness")))
    points = np.array([(xi, eta) for xi in (-1., 0., 1.) for eta in (-1., 0., 1.)])
    xi, eta = points[:, 0], points[:, 1]
    grad = np.empty((9, 4, 2), dtype=np.float64)
    grad[:, :, 0] = np.column_stack((eta-1, 1-eta, 1+eta, -1-eta)) / (2*hx)
    grad[:, :, 1] = np.column_stack((xi-1, -1-xi, 1+xi, 1-xi)) / (2*hy)
    hessian = np.zeros((4, 2, 2), dtype=np.float64)
    hessian[:, 0, 1] = np.array([1., -1., 1., -1.]) / (hx*hy)
    hessian[:, 1, 0] = hessian[:, 0, 1]
    weights = np.outer([1., 4., 1.], [1., 4., 1.]).ravel() * (hx*hy*thickness/36)
    result = {"grad": grad, "hessian": hessian, "weights": weights, "points": points}
    for value in result.values():
        if not np.all(np.isfinite(value)):
            raise KernelError("Reference operators overflowed.", code="nonfinite")
        value.setflags(write=False)
    return result


def _ops(ops):
    shapes = {"grad": (9, 4, 2), "hessian": (4, 2, 2), "weights": (9,), "points": (9, 2)}
    if not isinstance(ops, dict) or set(ops) != set(shapes):
        raise KernelError("ops must contain exactly grad, hessian, weights and points.")
    validated = {}
    for name, shape in shapes.items():
        value = _array(ops[name], f"ops.{name}")
        if value.shape != shape:
            raise KernelError(f"ops.{name} must have shape {shape}.", code="invalid_shape")
        validated[name] = value
    if np.any(validated["weights"] <= 0):
        raise KernelError("Quadrature weights must be positive.")
    return validated


def _displacements(ue, *, single=False):
    result = _array(ue, "displacement")
    if single:
        if result.shape != (8,):
            raise KernelError("An element displacement must have shape (8,).", code="invalid_shape")
    elif result.ndim != 2 or result.shape[1] != 8 or result.shape[0] == 0:
        raise KernelError("Batch displacement must have shape (ne,8), ne>0.", code="invalid_shape")
    return result


def _determinants(ue, grad):
    with np.errstate(over="ignore", invalid="ignore"):
        F = np.eye(2) + np.einsum("eai,qaj->eqij", ue.reshape(-1, 4, 2), grad)
        J = F[:, :, 0, 0]*F[:, :, 1, 1] - F[:, :, 0, 1]*F[:, :, 1, 0]
    if not np.all(np.isfinite(F)) or not np.all(np.isfinite(J)):
        raise KernelError("Deformation gradient or determinant is nonfinite.", code="nonfinite")
    return J


def determinants(ue, ops):
    """Evaluate J without any logarithm or inverse; nonpositive J is returned.

    Response calls use this inexpensive NumPy check before entering JAX. A
    nonlinear outer solver may also use it to reject a proposed trial early.
    """
    values = _array(ue, "displacement")
    single = values.shape == (8,)
    values = _displacements(values, single=single)
    reference = _ops(ops)
    J = _determinants(values.reshape(-1, 8), reference["grad"])
    return J[0] if single else J


def _runtime():
    if not jax.config.x64_enabled:
        raise KernelError("JAX float64 must be explicitly enabled before kernel use.", code="runtime_configuration")
    if jax.default_backend() != "cpu":
        raise KernelError("The HF-2 kernel requires the CPU backend.", code="runtime_configuration")


def _coefficient(value, name, count):
    result = _array(value, name)
    if result.shape == ():
        return np.full(count, float(result), dtype=np.float64)
    if result.shape != (count,):
        raise KernelError(f"{name} must be scalar or have shape ({count},).", code="invalid_shape")
    return result


def _residual_with_aux(u, grad, hessian, weights, lam, mu, kr):
    """Pure differentiable weak residual; validated inputs only."""
    nodal_u = u.reshape(4, 2)
    G = jnp.einsum("ai,qaj->qij", nodal_u, grad)
    F = jnp.eye(2, dtype=u.dtype) + G
    direct_J = F[:, 0, 0]*F[:, 1, 1] - F[:, 0, 1]*F[:, 1, 0]
    near_identity = jnp.max(jnp.abs(G), axis=(-1, -2)) <= 0.01
    delta = G[:, 0, 0]+G[:, 1, 1]+G[:, 0, 0]*G[:, 1, 1]-G[:, 0, 1]*G[:, 1, 0]
    safe_delta = jnp.where(near_identity, delta, 0.0)
    J = jnp.where(near_identity, 1.0+safe_delta, direct_J)
    inverse_transpose = jnp.stack((
        jnp.stack((F[:, 1, 1], -F[:, 1, 0]), axis=-1),
        jnp.stack((-F[:, 0, 1], F[:, 0, 0]), axis=-1),
    ), axis=-2) / J[:, None, None]
    log_J = jnp.where(near_identity, jnp.log1p(safe_delta), jnp.log(J))
    coefficient = lam*log_J-mu
    # Equivalent source weak form, without the ill-conditioned det(F.T @ F).
    direct_P = mu*F + coefficient[:, None, None]*inverse_transpose
    # (F F.T-I) F^-T = F-F^-T, formed from the displacement gradient.
    G_near = jnp.where(near_identity[:, None, None], G, 0.0)
    T_near = jnp.where(near_identity[:, None, None], inverse_transpose, jnp.eye(2, dtype=u.dtype))
    log_near = jnp.log1p(safe_delta)
    B = G_near+jnp.swapaxes(G_near, -1, -2)+jnp.einsum("qik,qjk->qij", G_near, G_near)
    incremental_P = mu*jnp.einsum("qik,qkj->qij", B, T_near) + lam*log_near[:, None, None]*T_near
    P = jnp.where(near_identity[:, None, None], incremental_P, direct_P)
    # Second Piola stress is auxiliary; it does not feed the material force.
    inverse_C = jnp.einsum("qki,qkj->qij", inverse_transpose, inverse_transpose)
    direct_S = mu*jnp.eye(2, dtype=u.dtype) + coefficient[:, None, None]*inverse_C
    S = jnp.where(near_identity[:, None, None], jnp.einsum("qki,qkj->qij", T_near, incremental_P), direct_S)
    material = jnp.einsum("q,qaj,qij->ai", weights, grad, P).reshape(8)
    Hu = jnp.einsum("ai,ajk->ijk", nodal_u, hessian)
    hessian_force = jnp.einsum("ajk,ijk->ai", hessian, Hu).reshape(8)
    regularization = kr*jnp.sum(weights*jnp.exp(-5*J))*hessian_force
    residual = material + regularization
    trace_C = jnp.sum(F*F, axis=(-1, -2))
    direct_energy = 0.5*(lam*log_J**2 + mu*(trace_C-2-2*log_J))
    remainder = jnp.zeros_like(safe_delta)
    for power in range(14, 1, -1):
        remainder = remainder*safe_delta + (-1.0)**power/power
    remainder = safe_delta**2*remainder  # delta-log(1+delta), stable near zero.
    shear_deviator = (G_near[:, 0, 0]-G_near[:, 1, 1])**2+(G_near[:, 0, 1]+G_near[:, 1, 0])**2
    incremental_energy = 0.5*(lam*log_near**2+mu*(shear_deviator+2*remainder))
    energy_density = jnp.where(near_identity, incremental_energy, direct_energy)
    return residual, {
        "residual": residual,
        "material_residual": material,
        "regularization_residual": regularization,
        "J": J, "F": F, "stress_second_piola": S,
        "material_energy": jnp.sum(weights*energy_density),
    }


_jacobian_with_aux = jax.jacfwd(_residual_with_aux, argnums=0, has_aux=True)


def _response_with_tangent(u, grad, hessian, weights, lam, mu, kr):
    tangent, fields = _jacobian_with_aux(u, grad, hessian, weights, lam, mu, kr)
    return {**fields, "tangent": tangent}


def _response_without_tangent(u, grad, hessian, weights, lam, mu, kr):
    return _residual_with_aux(u, grad, hessian, weights, lam, mu, kr)[1]


_batch_with_tangent = jax.jit(jax.vmap(_response_with_tangent, in_axes=(0, None, None, None, 0, 0, None)))
_batch_without_tangent = jax.jit(jax.vmap(_response_without_tangent, in_axes=(0, None, None, None, 0, 0, None)))


def batch_response(ue, ops, lam, mu, kr, *, tangent=True):
    """Return NumPy batch fields; reject invalid J before log or inverse.

    Lamé coefficients already include each element's material multiplier.
    kr is a scalar based on solid parameters and the task's reference Lx,
    with no further material interpolation applied inside this function.
    """
    if not isinstance(tangent, (bool, np.bool_)):
        raise KernelError("tangent must be boolean.")
    values = _displacements(ue)
    reference = _ops(ops)
    count = len(values)
    lam_values, mu_values = _coefficient(lam, "lam", count), _coefficient(mu, "mu", count)
    kr_value = _array(kr, "kr")
    if kr_value.shape != () or float(kr_value) < 0:
        raise KernelError("kr must be a nonnegative scalar.")
    if np.any(mu_values < 0) or np.any(lam_values+2*mu_values/3 < 0):
        raise KernelError("Material shear and bulk moduli must be nonnegative.")
    J = _determinants(values, reference["grad"])
    if np.any(J <= 0):
        raise KernelError("Nonpositive deformation determinant rejected before log/inverse.", code="invalid_J", details={
            "min_J": float(J.min()), "invalid_count": int(np.count_nonzero(J <= 0)),
            "first_invalid_element_quadrature_indices": np.argwhere(J <= 0)[:8].tolist(),
        })
    _runtime()
    function = _batch_with_tangent if tangent else _batch_without_tangent
    fields = function(values, reference["grad"], reference["hessian"], reference["weights"],
                      lam_values, mu_values, float(kr_value))
    result = {}
    for name, value in fields.items():
        array = np.asarray(value)  # Synchronizes CPU work before returning.
        if array.dtype != np.dtype("float64"):
            raise KernelError("Kernel output is not float64.", code="runtime_configuration", details={"field": name, "dtype": str(array.dtype)})
        if not np.all(np.isfinite(array)):
            raise KernelError("Kernel output is nonfinite.", code="nonfinite", details={"field": name})
        result[name] = array
    # JAX evaluates the same kinematics independently. Reject any discrepancy
    # crossing the legal domain rather than exposing a nonphysical response.
    if np.any(result["J"] <= 0):
        raise KernelError("Evaluated determinant is nonpositive.", code="invalid_J")
    return result


def element_response(u, ops, lam, mu, kr, *, tangent=True):
    """Single element response, with no singleton batch dimension."""
    values = _displacements(u, single=True)
    for name, value in (("lam", lam), ("mu", mu)):
        if _array(value, name).shape != ():
            raise KernelError(f"Single-element {name} must be scalar.", code="invalid_shape")
    result = batch_response(values[None, :], ops, lam, mu, kr, tangent=tangent)
    return {name: value[0] for name, value in result.items()}
