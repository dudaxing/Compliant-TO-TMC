"""Independent Decimal reference for the HF-3 average-displacement task.

The existing HF-2 reference recomputes the material/HuHu internal force from
actual binary64 primitives. This adapter separately forms the port means,
rank-one spring, input multiplier, constraint, reactions, and project scales
in Decimal. It imports no production kernel, solver, MATLAB, or LF code.

Float outputs are convenience views. Authoritative ``*_decimal`` outputs are
Decimal scalars/lists; an output mean is never promoted from a float dot product.
The reference retains the existing HF-2 kinematics; 50/80-digit checks, rather
than an assumed error bound, must certify any near-zero state of interest.
"""
from __future__ import annotations

from decimal import Decimal, localcontext
from functools import lru_cache
import importlib.util
from pathlib import Path

import numpy as np


def _real(value, name, shape=None):
    raw = np.asarray(value)
    if raw.dtype.kind not in "iuf" or np.iscomplexobj(raw):
        raise ValueError(f"{name} must contain real binary64-compatible numbers")
    result = np.array(raw, dtype=np.float64, copy=True)
    if not np.all(np.isfinite(result)):
        raise ValueError(f"{name} must be finite")
    if shape is not None and result.shape != shape:
        raise ValueError(f"{name} must have shape {shape}")
    return result


def _d(value):
    return Decimal.from_float(float(value))


def _norm(values):
    return sum((value*value for value in values), Decimal(0)).sqrt()


def _dot(left, right):
    if len(left) != len(right):
        raise ValueError("dot-product lengths differ")
    return sum((a*b for a, b in zip(left, right)), Decimal(0))


@lru_cache(maxsize=1)
def _reference_class():
    path = Path(__file__).with_name("hf2_precision_reference.py")
    spec = importlib.util.spec_from_file_location("hf2_reference_for_project_precision", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.DecimalQ1Reference


def evaluate_project_state(fixture, u, R, d, bin, bout, kout, E, thickness,
                           precision=50, *, direction=None, dR=0.0):
    """Evaluate the project's force residual and mean constraint independently.

    ``fixture`` requires actual ``grad, hessian, weights, lam, mu, kr,
    connectivity, fixed_dofs, solid``. Its optional ``F0`` is deliberately not
    used: this task's external force is recomputed from the supplied port data.
    All physical scalars, port vectors, displacement and direction values are
    promoted with Decimal.from_float. Frozen normalization constants 1e-8 and
    1e-6 are exact decimal specification values.

    r = fint + kout*bout*(bout.T*u) - bin*R; g = bin.T*u - d.
    SF = max(norm(fint_free), norm((bin*R)_free), norm(spring_free),
             1e-8*E*thickness*max(abs(d), 1e-6)).

    Support reaction is r on the deduplicated fixed DOFs and zero elsewhere.
    Its global balance includes input force +bin*R and spring force -spring.
    Balance scale is max(norm(support)+norm(input)+norm(spring), SF).

    Optional ``direction`` and ``dR`` give an augmented directional derivative:
    dr = J_internal*v + kout*bout*(bout.T*v) - bin*dR; dg = bin.T*v.
    Force/constraint actions are returned separately because they have different
    units. The concatenated augmented view must not be given an unscaled norm.
    This function does not decide pass/fail, solve, write files, or alter inputs.
    """
    if isinstance(precision, bool) or not isinstance(precision, int) or precision < 30:
        raise ValueError("precision must be an integer of at least 30 digits")
    uu = _real(u, "u")
    if uu.ndim != 1 or uu.size == 0 or uu.size % 2:
        raise ValueError("u must be a nonempty even-length vector")
    ndof = len(uu)
    bin_array = _real(bin, "bin", (ndof,))
    bout_array = _real(bout, "bout", (ndof,))
    scalars = {name: float(_real(value, name, ())) for name, value in
               (("R", R), ("d", d), ("kout", kout), ("E", E), ("thickness", thickness), ("dR", dR))}
    if scalars["kout"] < 0 or scalars["E"] <= 0 or scalars["thickness"] <= 0:
        raise ValueError("kout must be nonnegative; E and thickness must be positive")
    vv = None if direction is None else _real(direction, "direction", (ndof,))
    if vv is None and scalars["dR"] != 0:
        raise ValueError("dR requires an explicit displacement direction (which may be zero)")
    # Zero F0 prevents accidental reuse of a force-controlled source problem.
    # The helper's unit-scale diagnostic residual is discarded below.
    primitives = dict(fixture)
    primitives["F0"] = np.zeros(ndof, dtype=np.float64)
    reference = _reference_class()(primitives, precision=precision)
    solid = np.asarray(fixture["solid"])
    if solid.shape != (reference.ne,) or solid.dtype.kind not in "biu" or not np.all((solid == 0) | (solid == 1)):
        raise ValueError("solid must be a boolean/binary integer vector in canonical element order")
    solid = solid.astype(bool, copy=True)
    fixed, free = reference.fixed, reference.free
    if not np.any(bin_array[free] != 0):
        raise ValueError("bin must have a nonzero component on a free degree of freedom")
    hp = reference.evaluate(uu, 0.0, direction=vv)
    with localcontext() as context:
        context.prec = precision
        zero = Decimal(0)
        du, dbin, dbout = ([_d(x) for x in array] for array in (uu, bin_array, bout_array))
        dR_value, dd, dk, dE, dt = (_d(scalars[name]) for name in ("R", "d", "kout", "E", "thickness"))
        qin, qout = _dot(dbin, du), _dot(dbout, du)
        constraint = qin-dd
        spring = [dk*b*qout for b in dbout]
        input_force = [b*dR_value for b in dbin]
        external = [a-b for a, b in zip(input_force, spring)]
        internal = hp["internal_decimal"]
        residual = [fi+fs-fe for fi, fs, fe in zip(internal, spring, input_force)]
        d_scale = max(abs(dd), Decimal("1e-6"))
        force_norms = dict(
            internal_free=_norm([internal[i] for i in free]),
            input_free=_norm([input_force[i] for i in free]),
            spring_free=_norm([spring[i] for i in free]),
            floor=Decimal("1e-8")*dE*dt*d_scale)
        force_scale = max(force_norms.values())
        residual_norm = _norm([residual[i] for i in free])
        relative_residual = residual_norm/force_scale
        reaction = [zero]*ndof
        for index in fixed:
            reaction[index] = residual[index]
        balance = [sum((reaction[i]+external[i] for i in range(component, ndof, 2)), zero)
                   for component in (0, 1)]
        external_norms = dict(support_reaction=_norm(reaction), input=_norm(input_force), spring=_norm(spring))
        balance_scale = max(sum(external_norms.values(), zero), force_scale)
        balance_norm = _norm(balance)
        energy = hp["material_energy_decimal"]
        energy_solid = sum((e for e, selected in zip(energy, solid) if selected), zero)
        energy_medium = sum((e for e, selected in zip(energy, solid) if not selected), zero)
        min_solid = min((x for values, selected in zip(hp["J_decimal"], solid) if selected for x in values), default=None)
        min_medium = min((x for values, selected in zip(hp["J_decimal"], solid) if not selected for x in values), default=None)
        minimum_J = min(x for values in hp["J_decimal"] for x in values)
        fixed_error = max((abs(du[i]) for i in fixed), default=zero)
        result = dict(schema_version="hf3-project-precision-1.0", precision_digits=precision,
            input_multiplier_decimal=dR_value, prescribed_mean_decimal=dd,
            output_stiffness_decimal=dk, young_modulus_decimal=dE, thickness_decimal=dt,
            internal_decimal=internal, residual_decimal=residual, external_decimal=external,
            input_force_decimal=input_force, spring_internal_decimal=spring,
            spring_force_decimal=[-x for x in spring], support_reaction_decimal=reaction,
            force_balance_decimal=balance, q_in_decimal=qin, q_out_decimal=qout,
            constraint_decimal=constraint, constraint_error_decimal=abs(constraint),
            relative_constraint_decimal=abs(constraint)/d_scale, d_scale_decimal=d_scale,
            force_scale_decimal=force_scale, force_scale_components_decimal=force_norms,
            free_residual_norm_decimal=residual_norm, relative_residual_decimal=relative_residual,
            external_action_norms_decimal=external_norms, force_balance_norm_decimal=balance_norm,
            force_balance_scale_decimal=balance_scale, relative_force_balance_decimal=balance_norm/balance_scale,
            fixed_displacement_max_decimal=fixed_error, minimum_J_decimal=minimum_J,
            minimum_J_solid_decimal=min_solid, minimum_J_medium_decimal=min_medium,
            positive_J=minimum_J > 0, material_energy_decimal=energy,
            solid_material_energy_decimal=energy_solid, medium_material_energy_decimal=energy_medium,
            J_decimal=hp["J_decimal"], material_internal_decimal=hp["material_internal_decimal"],
            regularization_internal_decimal=hp["regularization_internal_decimal"],
            fixed_dofs=fixed.copy(), free_dofs=free.copy(), solid=solid,
            relative_residual=str(relative_residual), minimum_J=str(minimum_J))
        for name in ("internal", "residual", "external", "input_force", "spring_internal", "spring_force",
                     "support_reaction", "force_balance", "material_energy", "J", "material_internal", "regularization_internal"):
            result[name] = np.asarray(result[name+"_decimal"], dtype=np.float64)
        for name in ("q_in", "q_out", "constraint", "constraint_error", "relative_constraint", "d_scale",
                     "force_scale", "free_residual_norm", "force_balance_norm", "force_balance_scale",
                     "relative_force_balance", "fixed_displacement_max", "solid_material_energy", "medium_material_energy"):
            result[name] = float(result[name+"_decimal"])
        result["force_scale_components"] = {key: float(value) for key, value in force_norms.items()}
        result["external_action_norms"] = {key: float(value) for key, value in external_norms.items()}
        result["minimum_J_solid"] = None if min_solid is None else float(min_solid)
        result["minimum_J_medium"] = None if min_medium is None else float(min_medium)
        if vv is not None:
            dv = [_d(x) for x in vv]
            dqout = _dot(dbout, dv)
            dg = _dot(dbin, dv)
            spring_action = [dk*b*dqout for b in dbout]
            multiplier_action = [-b*_d(scalars["dR"]) for b in dbin]
            internal_action = hp["tangent_action_decimal"]
            force_action = [a+b+c for a, b, c in zip(internal_action, spring_action, multiplier_action)]
            result.update(internal_tangent_action_decimal=internal_action,
                residual_tangent_action_decimal=force_action, spring_tangent_action_decimal=spring_action,
                multiplier_tangent_action_decimal=multiplier_action, constraint_tangent_action_decimal=dg,
                output_tangent_action_decimal=dqout, augmented_tangent_action_decimal=force_action+[dg],
                material_tangent_action_decimal=hp["material_tangent_action_decimal"],
                regularization_tangent_action_decimal=hp["regularization_tangent_action_decimal"],
                dJ_decimal=hp["dJ_decimal"], det_dF_decimal=hp["det_dF_decimal"])
            for name in ("internal_tangent_action", "residual_tangent_action", "spring_tangent_action",
                         "multiplier_tangent_action", "augmented_tangent_action", "material_tangent_action",
                         "regularization_tangent_action"):
                result[name] = np.asarray(result[name+"_decimal"], dtype=np.float64)
            result["constraint_tangent_action"] = float(dg)
            result["output_tangent_action"] = float(dqout)
        return result
