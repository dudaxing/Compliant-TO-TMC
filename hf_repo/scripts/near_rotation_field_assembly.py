"""Independent Decimal weak-force assembly from already selected field arrays.

This diagnostic adapter does not reconstruct geometry, displacement, F, or J.
In particular, its cofactor is divided by the supplied J even when that J is
inconsistent with det(F): such a combination is a controlled arithmetic
counterfactual, not a new physical state. There are no production/AD imports,
equilibrium solves, tangent calculations, or file operations in this module.
"""
from collections.abc import Mapping
from decimal import Decimal, DecimalException, ROUND_HALF_EVEN, localcontext
import math
from numbers import Integral, Real


def _sequence(value, name):
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{name} must be a nested list or tuple")
    return value


def _shaped(value, shape, name, leaf):
    if not shape:
        return leaf(value, name)
    sequence = _sequence(value, name)
    if len(sequence) != shape[0]:
        raise ValueError(f"{name} must have shape {shape}")
    return [_shaped(item, shape[1:], f"{name}[{index}]", leaf)
            for index, item in enumerate(sequence)]


def _field_decimal(value, name):
    if not isinstance(value, Decimal) or not value.is_finite():
        raise ValueError(f"{name} must be a finite Decimal")
    return value


def _binary64_decimal(value, name):
    # Decimal(str(value)) would change the authority of the saved primitives.
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must contain real binary64-compatible numbers")
    try:
        binary = float(value)
    except (ValueError, TypeError, OverflowError) as error:
        raise ValueError(f"{name} is not binary64-compatible") from error
    if not math.isfinite(binary):
        raise ValueError(f"{name} must be finite")
    return Decimal.from_float(binary)


def _integer(value, name):
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise ValueError(f"{name} must contain integers")
    return int(value)


def _primitive(fixture, key, *, integer=False):
    try:
        value = fixture[key]
    except KeyError as error:
        raise ValueError(f"missing fixture primitive: {key}") from error
    # NPZ numeric arrays expose dtype and tolist; no NumPy import is needed.
    if hasattr(value, "dtype"):
        permitted = "iu" if integer else "iuf"
        if value.dtype.kind not in permitted:
            raise ValueError(f"{key} has an unsupported numeric dtype")
    return value.tolist() if hasattr(value, "tolist") else value


def assemble_fields(fixture, F, J, Hu, *, precision):
    """Return complete material, regularization, and total Decimal force lists.

    ``fixture`` holds the saved binary64 quadrature/material primitives,
    connectivity, F0 (for ndof only), and fixed_dofs (validated, never removed
    from the force vectors). F/J/Hu are Decimal nested lists with shapes
    (ne, 9, 2, 2), (ne, 9), and (ne, 2, 2, 2), respectively. Precision is 80 or
    120 digits with ROUND_HALF_EVEN. Supplied fields and primitives are not
    mutated. No externally applied force is subtracted.
    """
    if type(precision) is not int or precision not in (80, 120):
        raise ValueError("precision must be the integer 80 or 120")
    if not isinstance(fixture, Mapping):
        raise ValueError("fixture must be a mapping of saved numeric primitives")

    force0 = _sequence(_primitive(fixture, "F0"), "F0")
    ndof = len(force0)
    if ndof == 0 or ndof % 2:
        raise ValueError("F0 must be a nonempty even-length vector")
    _shaped(force0, (ndof,), "F0", _binary64_decimal)

    connectivity_raw = _sequence(_primitive(fixture, "connectivity", integer=True), "connectivity")
    ne = len(connectivity_raw)
    if ne == 0:
        raise ValueError("connectivity must contain at least one element")
    connectivity = _shaped(connectivity_raw, (ne, 4), "connectivity", _integer)
    if any(node < 0 or node >= ndof // 2 for cell in connectivity for node in cell):
        raise ValueError("connectivity contains an out-of-range node")
    if any(len(set(cell)) != 4 for cell in connectivity):
        raise ValueError("each Q1 element must have four distinct nodes")
    fixed_raw = _sequence(_primitive(fixture, "fixed_dofs", integer=True), "fixed_dofs")
    fixed = _shaped(fixed_raw, (len(fixed_raw),), "fixed_dofs", _integer)
    if len(set(fixed)) != len(fixed) or any(dof < 0 or dof >= ndof for dof in fixed):
        raise ValueError("fixed_dofs contains repeated or out-of-range indices")

    grad = _shaped(_primitive(fixture, "grad"), (9, 4, 2), "grad", _binary64_decimal)
    hessian = _shaped(_primitive(fixture, "hessian"), (4, 2, 2), "hessian", _binary64_decimal)
    weights = _shaped(_primitive(fixture, "weights"), (9,), "weights", _binary64_decimal)
    lam = _shaped(_primitive(fixture, "lam"), (ne,), "lam", _binary64_decimal)
    mu = _shaped(_primitive(fixture, "mu"), (ne,), "mu", _binary64_decimal)
    kr = _shaped(_primitive(fixture, "kr"), (), "kr", _binary64_decimal)
    field_F = _shaped(F, (ne, 9, 2, 2), "F", _field_decimal)
    field_J = _shaped(J, (ne, 9), "J", _field_decimal)
    field_Hu = _shaped(Hu, (ne, 2, 2, 2), "Hu", _field_decimal)
    if any(weight <= 0 for weight in weights):
        raise ValueError("quadrature weights must be positive")
    if kr < 0:
        raise ValueError("kr must be nonnegative")
    if any(value <= 0 for row in field_J for value in row):
        raise ValueError("supplied J must be positive")

    try:
        with localcontext() as context:
            context.prec = precision
            context.rounding = ROUND_HALF_EVEN
            zero = Decimal(0)
            if any(shear < 0 or first_lame + Decimal(2)*shear/Decimal(3) < 0
                   for first_lame, shear in zip(lam, mu)):
                raise ValueError("material shear and bulk moduli must be nonnegative")
            material, regularization = [zero]*ndof, [zero]*ndof
            for element, cell in enumerate(connectivity):
                # Hu is element-interior, with no quadrature axis.
                hessian_action = [[sum((hessian[a][j][k]*field_Hu[element][i][j][k]
                                        for j in range(2) for k in range(2)), zero)
                                   for i in range(2)] for a in range(4)]
                for q in range(9):
                    f, determinant = field_F[element][q], field_J[element][q]
                    # Deliberately DO NOT recompute determinant from f here.
                    inverse_transpose = [[f[1][1]/determinant, -f[1][0]/determinant],
                                         [-f[0][1]/determinant, f[0][0]/determinant]]
                    coefficient = lam[element]*determinant.ln() - mu[element]
                    stress = [[mu[element]*f[i][j] + coefficient*inverse_transpose[i][j]
                               for j in range(2)] for i in range(2)]
                    reg = kr*weights[q]*(Decimal(-5)*determinant).exp()
                    for local_node, node in enumerate(cell):
                        for component in range(2):
                            dof = 2*node + component
                            material[dof] += weights[q]*sum(
                                (stress[component][j]*grad[q][local_node][j] for j in range(2)), zero)
                            regularization[dof] += reg*hessian_action[local_node][component]
            total = [left + right for left, right in zip(material, regularization)]
            if not all(value.is_finite() for values in (material, regularization, total) for value in values):
                raise ValueError("nonfinite assembled force")
            return {"total_force": total, "material_force": material,
                    "regularization_force": regularization}
    except DecimalException as error:
        raise ValueError("Decimal field assembly failed") from error
