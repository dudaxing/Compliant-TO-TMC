"""Independent Decimal audit of the HF-4 prescribed-motion problem.

The material and HuHu forces are recomputed by the independent HF-2 reference
from the supplied, actual binary64 primitives. This adapter forms prescribed
motions, fixed-DOF reactions, force groups and normalizations in Decimal. It
imports no production kernel, solver or task adapter. Decimal outputs are
authoritative; float arrays are convenience views rounded only afterwards.
"""
from __future__ import annotations

from collections.abc import Mapping
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
    spec = importlib.util.spec_from_file_location("hf2_reference_for_prescribed_precision", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.DecimalQ1Reference


def evaluate_prescribed_state(fixture, u, d, base, direction, reaction_groups,
                              force_scale_per_length, precision=50, *,
                              tangent_direction=None):
    """Evaluate a saved state without solving or replacing its displacement.

    Required fixture primitives are ``grad, hessian, weights, lam, mu, kr,
    connectivity, fixed_dofs``. The optional ``solid`` mask enables energy/J
    partitions. Any fixture ``F0`` is ignored: this problem has no applied
    nodal force, so ``residual = internal``. Fixed DOFs must be unique.

    ``base`` and ``direction`` are full-ndof vectors, zero on free DOFs.
    Prescribed motion is D(base) + D(d)*D(direction), recomputed before float
    rounding. It is compared with D(u) on fixed DOFs; forces are evaluated at
    the actual D(u), including any saved constraint error.

    ``reaction_groups`` maps nonempty names to full-ndof virtual-motion
    vectors supported only on fixed DOFs. Overlap between groups is allowed;
    each group's force is its own v.T*reaction, never added to global balance.
    Reaction is internal force on fixed DOFs and zero elsewhere. The drive
    force is direction.T*reaction. These are constraint-on-model forces; no
    sign reversal, magnitude operation or symmetry factor is implicit.

    SF = max(norm(internal_free), norm(internal_fixed),
             1e-8*D(force_scale_per_length)*max(abs(D(d)), 1e-6)).
    Constraint error is the maximum fixed-DOF displacement error divided by
    max(abs(D(d)), 1e-6). Global balance sums the two Cartesian components of
    the fixed reaction and uses SF as denominator. The constants 1e-8/1e-6
    are exact decimal specification values, not promoted float expressions.

    ``tangent_direction`` optionally requests the analytic internal-force
    derivative J*v with d/base/direction held fixed. It is a perturbation
    vector, distinct from the prescribed-motion ``direction``. The constraint
    derivative is v on fixed DOFs and zero elsewhere. HuHu remains the source
    weak residual, whose Jacobian is not claimed to be an energy Hessian.

    This function does not decide pass/fail, mutate inputs or write files.
    """
    if isinstance(precision, bool) or not isinstance(precision, int) or precision < 30:
        raise ValueError("precision must be an integer of at least 30 digits")
    if not isinstance(fixture, Mapping):
        raise ValueError("fixture must be a mapping of ordinary numeric primitives")
    uu = _real(u, "u")
    if uu.ndim != 1 or uu.size == 0 or uu.size % 2:
        raise ValueError("u must be a nonempty even-length vector")
    ndof = len(uu)
    bb = _real(base, "base", (ndof,))
    motion = _real(direction, "direction", (ndof,))
    level = float(_real(d, "d", ()))
    stiffness_scale = float(_real(force_scale_per_length, "force_scale_per_length", ()))
    if stiffness_scale <= 0:
        raise ValueError("force_scale_per_length must be positive")
    vv = None if tangent_direction is None else _real(tangent_direction, "tangent_direction", (ndof,))
    if not isinstance(reaction_groups, Mapping) or not reaction_groups:
        raise ValueError("reaction_groups must be a nonempty mapping")
    groups = {}
    for name, vector in reaction_groups.items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError("reaction group names must be nonempty strings")
        groups[name] = _real(vector, f"reaction_groups[{name!r}]", (ndof,))
        if not np.any(groups[name] != 0):
            raise ValueError(f"reaction_groups[{name!r}] must be nonzero")

    # Do not retain an unrelated force-control load or its diagnostic unit SF.
    primitives = dict(fixture)
    primitives["F0"] = np.zeros(ndof, dtype=np.float64)
    reference = _reference_class()(primitives, precision=precision)
    fixed, free = reference.fixed, reference.free
    if len(fixed) == 0:
        raise ValueError("prescribed motion requires at least one fixed DOF")
    for name, vector in (("base", bb), ("direction", motion), *groups.items()):
        if np.any(vector[free] != 0):
            raise ValueError(f"{name} must be zero on free DOFs")
    solid = None
    if "solid" in fixture:
        raw_solid = np.asarray(fixture["solid"])
        if (raw_solid.shape != (reference.ne,) or raw_solid.dtype.kind not in "biu"
                or not np.all((raw_solid == 0) | (raw_solid == 1))):
            raise ValueError("solid must be a boolean/binary integer vector in canonical element order")
        solid = raw_solid.astype(bool, copy=True)

    hp = reference.evaluate(uu, 0.0, direction=vv)
    with localcontext() as context:
        context.prec = precision
        zero = Decimal(0)
        du, db, dv_motion = ([_d(x) for x in array] for array in (uu, bb, motion))
        dd, scale_per_length = _d(level), _d(stiffness_scale)
        dgroups = {name: [_d(x) for x in vector] for name, vector in groups.items()}
        prescribed = [b+dd*v for b, v in zip(db, dv_motion)]
        constraint = [zero]*ndof
        for index in fixed:
            constraint[index] = du[index]-prescribed[index]
        constraint_error = max((abs(constraint[i]) for i in fixed), default=zero)
        d_scale = max(abs(dd), Decimal("1e-6"))

        internal = hp["internal_decimal"]
        material = hp["material_internal_decimal"]
        regularization = hp["regularization_internal_decimal"]
        reaction, material_reaction, regularization_reaction = ([zero]*ndof for _ in range(3))
        for index in fixed:
            reaction[index] = internal[index]
            material_reaction[index] = material[index]
            regularization_reaction[index] = regularization[index]
        force_norms = dict(internal_free=_norm([internal[i] for i in free]),
                           internal_fixed=_norm([internal[i] for i in fixed]),
                           floor=Decimal("1e-8")*scale_per_length*d_scale)
        force_scale = max(force_norms.values())
        residual_norm = force_norms["internal_free"]
        group_forces = {name: _dot(vector, reaction) for name, vector in dgroups.items()}
        group_material = {name: _dot(vector, material_reaction) for name, vector in dgroups.items()}
        group_regularization = {name: _dot(vector, regularization_reaction) for name, vector in dgroups.items()}
        drive_force = _dot(dv_motion, reaction)
        balance = [sum((reaction[i] for i in range(component, ndof, 2)), zero)
                   for component in (0, 1)]
        balance_norm = _norm(balance)
        minimum_J = min(value for row in hp["J_decimal"] for value in row)
        energy = hp["material_energy_decimal"]
        energy_solid = energy_medium = min_solid = min_medium = None
        if solid is not None:
            energy_solid = sum((value for value, selected in zip(energy, solid) if selected), zero)
            energy_medium = sum((value for value, selected in zip(energy, solid) if not selected), zero)
            min_solid = min((value for row, selected in zip(hp["J_decimal"], solid)
                             if selected for value in row), default=None)
            min_medium = min((value for row, selected in zip(hp["J_decimal"], solid)
                              if not selected for value in row), default=None)

        result = dict(schema_version="hf4-prescribed-precision-1.0", precision_digits=precision,
            prescribed_level_decimal=dd, force_scale_per_length_decimal=scale_per_length,
            prescribed_displacement_decimal=prescribed, constraint_decimal=constraint,
            constraint_error_decimal=constraint_error, relative_constraint_decimal=constraint_error/d_scale,
            d_scale_decimal=d_scale, internal_decimal=internal, residual_decimal=list(internal),
            external_decimal=[zero]*ndof, material_internal_decimal=material,
            regularization_internal_decimal=regularization, support_reaction_decimal=reaction,
            material_support_reaction_decimal=material_reaction,
            regularization_support_reaction_decimal=regularization_reaction,
            group_reactions_decimal=group_forces, group_material_reactions_decimal=group_material,
            group_regularization_reactions_decimal=group_regularization,
            drive_force_decimal=drive_force, drive_material_force_decimal=_dot(dv_motion, material_reaction),
            drive_regularization_force_decimal=_dot(dv_motion, regularization_reaction),
            force_scale_decimal=force_scale, force_scale_components_decimal=force_norms,
            free_residual_norm_decimal=residual_norm, relative_residual_decimal=residual_norm/force_scale,
            force_balance_decimal=balance, force_balance_norm_decimal=balance_norm,
            force_balance_scale_decimal=force_scale, relative_force_balance_decimal=balance_norm/force_scale,
            J_decimal=hp["J_decimal"], minimum_J_decimal=minimum_J, positive_J=minimum_J > 0,
            minimum_J_solid_decimal=min_solid, minimum_J_medium_decimal=min_medium,
            material_energy_decimal=energy, solid_material_energy_decimal=energy_solid,
            medium_material_energy_decimal=energy_medium, fixed_dofs=fixed.copy(), free_dofs=free.copy(),
            solid=solid, relative_residual=str(residual_norm/force_scale), minimum_J=str(minimum_J))
        vector_names = ("prescribed_displacement", "constraint", "internal", "residual", "external",
                        "material_internal", "regularization_internal", "support_reaction",
                        "material_support_reaction", "regularization_support_reaction", "force_balance",
                        "J", "material_energy")
        scalar_names = ("prescribed_level", "force_scale_per_length", "constraint_error", "relative_constraint",
                        "d_scale", "drive_force", "drive_material_force", "drive_regularization_force",
                        "force_scale", "free_residual_norm", "force_balance_norm", "force_balance_scale",
                        "relative_force_balance")
        for name in vector_names:
            result[name] = np.asarray(result[name+"_decimal"], dtype=np.float64)
        for name in scalar_names:
            result[name] = float(result[name+"_decimal"])
        for name in ("group_reactions", "group_material_reactions", "group_regularization_reactions",
                     "force_scale_components"):
            result[name] = {key: float(value) for key, value in result[name+"_decimal"].items()}
        for name in ("solid_material_energy", "medium_material_energy", "minimum_J_solid", "minimum_J_medium"):
            result[name] = None if result[name+"_decimal"] is None else float(result[name+"_decimal"])

        if vv is not None:
            internal_action = hp["tangent_action_decimal"]
            reaction_action, constraint_action = ([zero]*ndof for _ in range(2))
            for index in fixed:
                reaction_action[index] = internal_action[index]
                constraint_action[index] = _d(vv[index])
            result.update(tangent_action_decimal=internal_action,
                internal_tangent_action_decimal=internal_action, residual_tangent_action_decimal=list(internal_action),
                material_tangent_action_decimal=hp["material_tangent_action_decimal"],
                regularization_tangent_action_decimal=hp["regularization_tangent_action_decimal"],
                support_reaction_tangent_action_decimal=reaction_action,
                constraint_tangent_action_decimal=constraint_action,
                group_reaction_tangent_actions_decimal={name: _dot(vector, reaction_action)
                                                       for name, vector in dgroups.items()},
                drive_force_tangent_action_decimal=_dot(dv_motion, reaction_action),
                dJ_decimal=hp["dJ_decimal"], det_dF_decimal=hp["det_dF_decimal"])
            for name in ("tangent_action", "internal_tangent_action", "residual_tangent_action",
                         "material_tangent_action", "regularization_tangent_action",
                         "support_reaction_tangent_action", "constraint_tangent_action"):
                result[name] = np.asarray(result[name+"_decimal"], dtype=np.float64)
            result["group_reaction_tangent_actions"] = {
                name: float(value) for name, value in result["group_reaction_tangent_actions_decimal"].items()}
            result["drive_force_tangent_action"] = float(result["drive_force_tangent_action_decimal"])
        return result
