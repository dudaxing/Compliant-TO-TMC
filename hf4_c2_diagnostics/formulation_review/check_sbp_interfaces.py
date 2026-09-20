"""Exact polynomial integration oracle for the frozen C2 SBP helper.

Two rectangular cells, prescribed stress polynomials, no constitutive evaluation
or equilibrium solve. Expected values use Fraction monomial antiderivatives,
not Lobatto differentiation or the helper's edge quadrature implementation.
"""
from decimal import Decimal, localcontext
from fractions import Fraction as F
from pathlib import Path
import hashlib
import json
import platform
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / "hf_repo/scripts/contact_c2_sbp.py"
OUT = Path(__file__).with_name("interface_results.json")
PRECISIONS = (80, 120)
LIMIT = Decimal("1e-45")
HX, HY = F(1, 2), F(1, 4)
COORDS = [(F(i, 2), F(j, 4)) for j in range(2) for i in range(3)]
CONN = [[0, 1, 4, 3], [1, 2, 5, 4]]
TOP = [3, 4, 5]
Q = (-1, 0, 1)
W = (1, 4, 1)
SIGNS = ((-1, -1), (1, -1), (1, 1), (-1, 1))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def add(a, b):
    out = dict(a)
    for key, value in b.items():
        out[key] = out.get(key, F(0)) + value
    return {key: value for key, value in out.items() if value}


def mul(a, b):
    out = {}
    for (i, j), x in a.items():
        for (k, l), y in b.items():
            key = (i+k, j+l)
            out[key] = out.get(key, F(0)) + x*y
    return out


def derivative(p, axis):
    return {(i-1 if axis == 0 else i, j-1 if axis == 1 else j): v*(i if axis == 0 else j)
            for (i, j), v in p.items() if (i if axis == 0 else j)}


def value(p, x, y):
    return sum((v*x**i*y**j for (i, j), v in p.items()), F(0))


def integral(p, x0, x1, y0, y1):
    return sum((v*(x1**(i+1)-x0**(i+1))/(i+1)*(y1**(j+1)-y0**(j+1))/(j+1)
                for (i, j), v in p.items()), F(0))


def edge_integral(p, axis, fixed, low, high):
    return sum((v*(fixed**i*(high**(j+1)-low**(j+1))/(j+1) if axis == 0
                   else fixed**j*(high**(i+1)-low**(i+1))/(i+1)) for (i, j), v in p.items()), F(0))


def shape(x0, y0, sx, sy):
    # Standard bilinear shape expanded in global physical coordinates.
    px = {(0, 0): -x0/HX if sx == 1 else 1+x0/HX, (1, 0): sx/HX}
    py = {(0, 0): -y0/HY if sy == 1 else 1+y0/HY, (0, 1): sy/HY}
    return mul(px, py)


def dc(x):
    return Decimal(x.numerator)/Decimal(x.denominator)


def norm(v):
    return sum((x*x for x in v), Decimal(0)).sqrt()


def plain(x):
    if isinstance(x, (Decimal, F)):
        return str(x)
    if isinstance(x, dict):
        return {str(k): plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [plain(v) for v in x]
    if isinstance(x, np.ndarray):
        return plain(x.tolist())
    return x


def constant(a, b, c, d):
    return [[{(0, 0): F(a)}, {(0, 0): F(b)}], [{(0, 0): F(c)}, {(0, 0): F(d)}]]


def main():
    if OUT.exists():
        raise FileExistsError("preserve the previous diagnostic output")
    frozen = sha(HELPER)
    assert frozen == "fd85bf4c6ba19f4365198f5b3cbca9ab1247344c585a6d8e74ab53dff687fc21"
    sys.path.insert(0, str(HELPER.parent))
    from contact_c2_sbp import decompose_material
    weights = np.array([float(HX*HY*wx*wy/36) for wx in W for wy in W])
    factor = F.from_float(float(weights[0]))*36/(HX*HY)
    grad = np.array([[[float(sx*(1+sy*eta)/(2*HX)), float(sy*(1+sx*xi)/(2*HY))]
                     for sx, sy in SIGNS] for xi in Q for eta in Q])
    fixture = dict(coordinates=np.array(COORDS, dtype=float), connectivity=np.array(CONN),
                   top_nodes=np.array(TOP), grad=grad, weights=weights)
    affine = [[{(1, 0): F(1)}, {(0, 1): F(2)}], [{(1, 0): F(3)}, {(0, 1): F(4)}]]
    biquad = [[{(2, 1): F(3, 2), (0, 2): F(-1, 4)}, {(1, 2): F(2), (2, 0): F(1, 2)}],
              [{(2, 2): F(-3), (1, 0): F(5)}, {(2, 1): F(7, 4), (0, 1): F(-2)}]]
    cases = {"continuous_constant": [constant(2, 3, 5, 7)]*2,
             "constant_jump": [constant(2, 3, 5, 7), constant(11, 13, 17, 19)],
             "continuous_affine_divergence": [affine]*2,
             "biquadratic_jump_divergence": [biquad, affine]}
    output = []
    maxima = []
    for name, stresses in cases.items():
        expected = {key: [F(0)]*12 for key in ("material_N", "top_edge_consistent_N",
            "top_edge_physical_simpson_N", "other_external_edge_consistent_N",
            "internal_interface_jump_N", "minus_projected_div_N")}
        local_values = []
        stress_samples = []
        for e, (conn, P) in enumerate(zip(CONN, stresses)):
            x0, y0 = COORDS[conn[0]]
            x1, y1 = x0+HX, y0+HY
            local = []
            stress_samples.append([[[value(P[i][j], x0+HX*F(xi+1, 2), y0+HY*F(eta+1, 2))
                                    for j in (0, 1)] for i in (0, 1)] for xi in Q for eta in Q])
            for a, node in enumerate(conn):
                N = shape(x0, y0, *SIGNS[a])
                row = []
                for i in (0, 1):
                    material = factor*integral(add(mul(P[i][0], derivative(N, 0)), mul(P[i][1], derivative(N, 1))), x0, x1, y0, y1)
                    row.append(material)
                    expected["material_N"][2*node+i] += material
                    divP = add(derivative(P[i][0], 0), derivative(P[i][1], 1))
                    expected["minus_projected_div_N"][2*node+i] -= factor*integral(mul(N, divP), x0, x1, y0, y1)
                    for label, axis, fixed, low, high, sign in (
                            ("left", 0, x0, y0, y1, -1), ("right", 0, x1, y0, y1, 1),
                            ("bottom", 1, y0, x0, x1, -1), ("top", 1, y1, x0, x1, 1)):
                        edge = sign*edge_integral(mul(N, P[i][axis]), axis, fixed, low, high)
                        internal = (e == 0 and label == "right") or (e == 1 and label == "left")
                        key = "internal_interface_jump_N" if internal else "top_edge_consistent_N" if label == "top" else "other_external_edge_consistent_N"
                        expected[key][2*node+i] += factor*edge
                        if label == "top":
                            expected["top_edge_physical_simpson_N"][2*node+i] += edge
                local.append(row)
            local_values.append(local)
        expected["top_weight_correction_N"] = [x-y for x, y in zip(expected["top_edge_consistent_N"], expected["top_edge_physical_simpson_N"])]
        if name == "continuous_constant":
            assert expected["internal_interface_jump_N"] == [0]*12
            assert expected["minus_projected_div_N"] == [0]*12
        if name == "constant_jump":
            assert [expected["internal_interface_jump_N"][2*n+i] for n in (1, 4) for i in (0, 1)] == [factor*HY*F(-9, 2), factor*HY*F(-12, 2)]*2
            assert expected["minus_projected_div_N"] == [0]*12
        if name == "continuous_affine_divergence":
            assert expected["internal_interface_jump_N"] == [0]*12
        checks = []
        hp = {}
        for precision in PRECISIONS:
            with localcontext() as context:
                context.prec = precision
                elements = [dict(element=e, connectivity=conn, material_internal_N=[[dc(v) for v in row] for row in local_values[e]],
                                 quadrature=[dict(xi=Decimal(xi), eta=Decimal(eta), P=[[dc(v) for v in row] for row in p])
                                             for p, (xi, eta) in zip(stress_samples[e], ((x, y) for x in Q for y in Q))])
                            for e, conn in enumerate(CONN)]
                actual = decompose_material(fixture, elements, precision=precision)
                assert actual["status"] == "pass"
                hp[precision] = actual
                for key, exact in expected.items():
                    denominator = max(norm([dc(v) for v in exact]), Decimal(1))
                    error = norm([v-dc(w) for v, w in zip(actual["fields"][key], exact)])/denominator
                    assert error <= LIMIT
                    maxima.append(error)
                    checks.append(dict(precision=precision, field=key, normalized_error=error, limit=LIMIT, passed=True))
        output.append(dict(name=name, stress_global_polynomial_coefficients=stresses,
                           expected_exact_fraction=expected, hp=hp, checks=checks))
    assert sha(HELPER) == frozen
    report = dict(schema="contact_c2_sbp_exact_polynomial_interface_checks_v1", status="pass", no_equilibrium_solve=True,
        method="Fraction monomial antiderivatives in physical coordinates; arbitrary prescribed stress polynomials, not material equilibrium",
        precisions=PRECISIONS, threshold=LIMIT, scale="max(exact vector norm,1 N)", fixture=fixture,
        effective_thickness_exact_fraction=factor, cases=output, maximum_normalized_error=max(maxima),
        source_sha256={str(HELPER.relative_to(ROOT)).replace('\\', '/'): frozen}, script_sha256=sha(__file__),
        environment=dict(python=platform.python_version(), numpy=np.__version__))
    with OUT.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(plain(report), stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps(plain(dict(status="pass", cases=len(cases), component_checks=len(maxima),
        maximum_normalized_error=max(maxima), helper_unchanged=True, script_sha256=sha(__file__), output_sha256=sha(OUT))), indent=2))


if __name__ == "__main__":
    main()
