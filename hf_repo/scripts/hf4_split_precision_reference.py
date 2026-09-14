"""Independent Decimal reference for explicit split-displacement authority.

New adapter: U = D(lift) + D(fluctuation); an optional ideal offset perturbs
only fluctuation. No production mechanics or AD imports. The independent
HF-2 formulas are retained explicitly below; old helper bytes are untouched.
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


class DecimalSplitQ1Reference(_reference_class()):
    """Independent two-component Q1 force and analytic direction reference.

    The frozen HF-2 class provides primitive validation/copying only. Its force
    evaluator is not called. This evaluator retains the independent Decimal
    material/HuHu formulas with an explicit two-component input and separate
    fluctuation perturbation. Fixture keys/shapes match DecimalQ1Reference;
    F0 supplies ndof but is ignored as a load in this no-external-force task.

    G/F shape (ne,9,2,2), Hu shape (ne,2,2,2), J shape (ne,9). Hu is element
    interior and is not replicated along quadrature. *_decimal are authority.
    A physical input is formed exactly before the declared-precision formula
    evaluation; its individual Decimal values are never cast back to float.
    """

    def evaluate(self, lift, fluctuation, *, tangent_direction=None,
                 fluctuation_offset=0.0, derivative=True):
        left = _real(lift, "lift", (self.ndof,))
        right = _real(fluctuation, "fluctuation", (self.ndof,))
        offset = _real(fluctuation_offset, "fluctuation_offset", ())
        if not isinstance(derivative, (bool, np.bool_)):
            raise ValueError("derivative must be boolean")
        if tangent_direction is None and float(offset) != 0:
            raise ValueError("nonzero fluctuation_offset requires tangent_direction")
        v = None if tangent_direction is None else _real(tangent_direction, "tangent_direction", (self.ndof,))
        # 3000 digits cover the exact sum/product of any finite binary64
        # operands (including subnormals). The mechanics uses self.precision.
        with localcontext() as exact_context:
            exact_context.prec = 3000
            step = _d(offset)
            physical = [_d(a)+_d(b)+(step*_d(v[i]) if v is not None else Decimal(0))
                        for i, (a,b) in enumerate(zip(left,right))]
        with localcontext() as context:
            context.prec = self.precision
            zero, one, two = Decimal(0),Decimal(1),Decimal(2)
            du = physical
            dv = None if v is None else [_d(x) for x in v]
            action_direction = dv if derivative else None
            material, regularization = [zero]*self.ndof,[zero]*self.ndof
            dmaterial, dregularization = [zero]*self.ndof,[zero]*self.ndof
            all_J, all_dJ, all_det_dF, energy = [],[],[],[]
            all_G, all_F, all_Hu = [], [], []
            for e, conn in enumerate(self.connectivity):
                un = [[du[2*a+i] for i in range(2)] for a in conn]
                vn = None if action_direction is None else [[action_direction[2*a+i] for i in range(2)] for a in conn]
                Hu = [[[sum((un[a][i]*self.dh[a][j][k] for a in range(4)),zero)
                        for k in range(2)] for j in range(2)] for i in range(2)]
                Au = [[sum((self.dh[a][j][k]*Hu[i][j][k] for j in range(2) for k in range(2)),zero)
                       for i in range(2)] for a in range(4)]
                if vn is not None:
                    Hv = [[[sum((vn[a][i]*self.dh[a][j][k] for a in range(4)),zero)
                            for k in range(2)] for j in range(2)] for i in range(2)]
                    Av = [[sum((self.dh[a][j][k]*Hv[i][j][k] for j in range(2) for k in range(2)),zero)
                           for i in range(2)] for a in range(4)]
                ej, edj, edet = [],[],[]
                element_G, element_F = [], []
                all_Hu.append(Hu)
                energy_e = zero
                for q in range(9):
                    grad = self.dg[q]
                    G = [[sum((un[a][i]*grad[a][j] for a in range(4)),zero)
                          for j in range(2)] for i in range(2)]
                    F = [[(one if i==j else zero)+G[i][j] for j in range(2)] for i in range(2)]
                    element_G.append(G)
                    element_F.append(F)
                    J = F[0][0]*F[1][1]-F[0][1]*F[1][0]
                    if not J.is_finite() or J <= 0:
                        raise ValueError(f'Nonpositive or nonfinite J at element {e}, quadrature {q}')
                    ej.append(J)
                    T = [[F[1][1]/J,-F[1][0]/J],[-F[0][1]/J,F[0][0]/J]]
                    logJ = J.ln()
                    c = self.dlam[e]*logJ-self.dmu[e]
                    P = [[self.dmu[e]*F[i][j]+c*T[i][j] for j in range(2)] for i in range(2)]
                    reg = self.dk*self.dw[q]*(-5*J).exp()
                    energy_e += self.dw[q]*(self.dlam[e]*logJ**2+self.dmu[e]*(sum((x*x for row in F for x in row),zero)-two-two*logJ))/two
                    if vn is not None:
                        dF = [[sum((vn[a][i]*grad[a][j] for a in range(4)),zero)
                               for j in range(2)] for i in range(2)]
                        dJ = F[1][1]*dF[0][0]+F[0][0]*dF[1][1]-F[1][0]*dF[0][1]-F[0][1]*dF[1][0]
                        det_dF = dF[0][0]*dF[1][1]-dF[0][1]*dF[1][0]
                        dT = [[-sum((T[i][k]*dF[l][k]*T[l][j] for k in range(2) for l in range(2)),zero)
                               for j in range(2)] for i in range(2)]
                        dP = [[self.dmu[e]*dF[i][j]+self.dlam[e]*dJ/J*T[i][j]+c*dT[i][j]
                               for j in range(2)] for i in range(2)]
                        edj.append(dJ)
                        edet.append(det_dF)
                    for a, node in enumerate(conn):
                        for i in range(2):
                            dof = 2*node+i
                            material[dof] += self.dw[q]*sum((P[i][j]*grad[a][j] for j in range(2)),zero)
                            regularization[dof] += reg*Au[a][i]
                            if vn is not None:
                                dmaterial[dof] += self.dw[q]*sum((dP[i][j]*grad[a][j] for j in range(2)),zero)
                                dregularization[dof] += reg*(Av[a][i]-5*dJ*Au[a][i])
                all_J.append(ej)
                all_G.append(element_G)
                all_F.append(element_F)
                energy.append(energy_e)
                if vn is not None:
                    all_dJ.append(edj)
                    all_det_dF.append(edet)
            internal = [a+b for a,b in zip(material,regularization)]
            external = [zero]*self.ndof
            residual = list(internal)
            result = dict(internal=np.array(internal,dtype=np.float64),residual=np.array(residual,dtype=np.float64),
                J=np.array(all_J,dtype=np.float64),material_energy=np.array(energy,dtype=np.float64),
                minimum_J=str(min(x for row in all_J for x in row)),
                internal_decimal=internal,residual_decimal=residual,external_decimal=external,
                material_internal=np.array(material,dtype=np.float64),regularization_internal=np.array(regularization,dtype=np.float64),
                material_internal_decimal=material,regularization_internal_decimal=regularization,
                J_decimal=all_J,material_energy_decimal=energy,
                G_decimal=all_G,F_decimal=all_F,Hu_decimal=all_Hu,
                G=np.array(all_G,dtype=np.float64),F=np.array(all_F,dtype=np.float64),
                Hu=np.array(all_Hu,dtype=np.float64),physical_displacement_decimal=physical,
                state_representation="split_displacement_v1",
                fluctuation_offset_decimal=_d(fluctuation_offset))
            if vn is not None:
                action = [a+b for a,b in zip(dmaterial,dregularization)]
                result.update(tangent_action=np.array(action,dtype=np.float64),
                    material_tangent_action=np.array(dmaterial,dtype=np.float64),regularization_tangent_action=np.array(dregularization,dtype=np.float64),
                    tangent_action_decimal=action,material_tangent_action_decimal=dmaterial,
                    regularization_tangent_action_decimal=dregularization,
                    dJ_decimal=all_dJ,det_dF_decimal=all_det_dF)
            return result


def evaluate_split_prescribed_state(fixture, u_lift, u_fluctuation, d, base, direction, reaction_groups,
                                    force_scale_per_length, precision=50, *, tangent_direction=None,
                                    fluctuation_offset=0.0, derivative=True):
    """HF-4 measurements of D(lift)+D(w), without a collapsed float state.

    Signature/forces/constraints and normalization match the frozen HF-4
    independent adapter. tangent_direction perturbs only w. Nonzero
    fluctuation_offset is for diagnostic ideal finite differences and requires
    a direction; use derivative=False to skip Jv. Accepted-state audits must
    use offset=0. Physical forces are formed from the exact sum of the two
    saved arrays, never from a display u. No production imports or file writes.
    """
    if isinstance(precision, bool) or not isinstance(precision, int) or precision < 30:
        raise ValueError("precision must be an integer of at least 30 digits")
    if not isinstance(fixture, Mapping):
        raise ValueError("fixture must be a mapping of ordinary numeric primitives")
    ll = _real(u_lift, "u_lift")
    uu = _real(u_fluctuation, "u_fluctuation")
    if uu.ndim != 1 or uu.size == 0 or uu.size % 2:
        raise ValueError("u must be a nonempty even-length vector")
    ndof = len(uu)
    if ll.shape != (ndof,):
        raise ValueError("u_lift and u_fluctuation shapes must agree")
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
    reference = DecimalSplitQ1Reference(primitives, precision=precision)
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

    hp = reference.evaluate(ll, uu, tangent_direction=vv,
                            fluctuation_offset=fluctuation_offset, derivative=derivative)
    with localcontext() as context:
        context.prec = precision
        zero = Decimal(0)
        du = hp["physical_displacement_decimal"]
        db, dv_motion = ([_d(x) for x in array] for array in (bb, motion))
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

        result = dict(schema_version="hf4-split-prescribed-precision-1.0", precision_digits=precision,
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

        if vv is not None and derivative:
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
        for name in ("G", "F", "Hu", "physical_displacement"):
            result[name+"_decimal"] = hp[name+"_decimal"]
            if name != "physical_displacement":
                result[name] = hp[name]
        result.update(state_representation="split_displacement_v1",
                      lift_decimal=[_d(x) for x in ll], fluctuation_decimal=[_d(x) for x in uu],
                      fluctuation_offset_decimal=hp["fluctuation_offset_decimal"],
                      derivative_requested=bool(vv is not None and derivative))
        return result
