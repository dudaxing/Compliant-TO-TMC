"""Discrete material summation-by-parts from already reconstructed Q1 stresses.

No constitutive evaluation, production mechanics, solver or file I/O. P^I is
the degree-(2,2) interpolant of the nine supplied Lobatto stress samples. Its
divergence is not asserted to be the true nonlinear constitutive divergence.
"""
from decimal import Decimal, localcontext
from fractions import Fraction

import numpy as np


ZERO = Decimal(0)
ONE = Decimal(1)
Q = (Decimal(-1), ZERO, ONE)
W = (1, 4, 1)
D = ((Decimal("-1.5"), Decimal(2), Decimal("-.5")),
     (Decimal("-.5"), ZERO, Decimal(".5")),
     (Decimal(".5"), Decimal(-2), Decimal("1.5")))
NODES = ((-1, -1), (1, -1), (1, 1), (-1, 1))
EDGES = (("bottom", (0, 1), (0, 3, 6), (0, -1)),
         ("right", (1, 2), (6, 7, 8), (1, 0)),
         ("top", (3, 2), (2, 5, 8), (0, 1)),
         ("left", (0, 3), (0, 1, 2), (-1, 0)))


def dec(value):
    return Decimal.from_float(float(value))


def _norm(values):
    return sum((v*v for v in values), ZERO).sqrt()


def _check(a, b, limit):
    error = _norm([x-y for x, y in zip(a, b)])
    denominator = max(_norm(b), ONE)
    return dict(absolute_error_N=error, scale_N=denominator, normalized_error=error/denominator,
                limit=Decimal(limit), passed=error/denominator <= Decimal(limit))


def decompose_material(fixture, elements, *, precision=80, thickness=1.0, identity_limit="1e-45"):
    """Return flattened global two-component Decimal force vectors, internal sign.

    Required fixture arrays: coordinates, connectivity, top_nodes, grad, weights.
    Elements are ordered records returned by contact_c2_fields.reconstruct:
    {element,connectivity,material_internal_N[4][2],quadrature[9]:{xi,eta,P[2][2]}}.
    Both physical thickness and the effective thickness implied by the saved
    binary64 volume weights are explicit. No scalar force is reclassified as
    contact pressure, and no high-order edge quadrature is claimed by this SBP.
    """
    if precision not in (80, 120) or not np.isfinite(thickness) or thickness <= 0:
        raise ValueError("undeclared precision or invalid physical thickness")
    xy = np.asarray(fixture["coordinates"])
    conn = np.asarray(fixture["connectivity"])
    grads = np.asarray(fixture["grad"])
    weights = np.asarray(fixture["weights"])
    if (xy.ndim != 2 or xy.shape[1] != 2 or conn.shape != (len(elements), 4)
            or conn.dtype.kind not in "iu" or weights.shape != (9,) or grads.shape != (9, 4, 2)
            or not np.all(np.isfinite(xy)) or not np.all(np.isfinite(weights)) or np.any(weights <= 0)):
        raise ValueError("invalid rectangular fixture")
    fw = [Fraction.from_float(float(w)) for w in weights]
    if any(fw[3*i+j] != fw[0]*W[i]*W[j] for i in range(3) for j in range(3)):
        raise ValueError("saved weights do not factor exactly as c times [1,4,1] tensor [1,4,1]")
    top = set(map(int, fixture["top_nodes"]))
    ndof = 2*len(xy)
    with localcontext() as ctx:
        ctx.prec = precision
        fields = {key: [ZERO]*ndof for key in (
            "material_N", "top_edge_consistent_N", "top_edge_physical_simpson_N",
            "other_external_edge_consistent_N", "internal_interface_jump_N", "minus_projected_div_N")}
        dw = [dec(w) for w in weights]
        incidence = {}
        element_rows = []
        shape = [[(ONE+sx*xi)*(ONE+sy*eta)/4 for sx, sy in NODES] for xi in Q for eta in Q]
        for e, (row, cn) in enumerate(zip(elements, conn)):
            cn = list(map(int, cn))
            if row["element"] != e or list(row["connectivity"]) != cn:
                raise ValueError("element identity/order differs from fixture")
            corners = xy[cn]
            hx, hy = dec(corners[1, 0])-dec(corners[0, 0]), dec(corners[3, 1])-dec(corners[0, 1])
            expected = np.array([[corners[0, 0], corners[0, 1]], [corners[1, 0], corners[0, 1]],
                                 [corners[1, 0], corners[3, 1]], [corners[0, 0], corners[3, 1]]])
            if hx <= 0 or hy <= 0 or not np.array_equal(corners, expected):
                raise ValueError("SBP requires canonical BL BR TR TL rectangular cells")
            for q, (xi, eta) in enumerate((x, y) for x in Q for y in Q):
                for a, (sx, sy) in enumerate(NODES):
                    if (dec(grads[q, a, 0]) != sx*(ONE+sy*eta)/(2*hx)
                            or dec(grads[q, a, 1]) != sy*(ONE+sx*xi)/(2*hy)):
                        raise ValueError("saved gradients differ from exact rectangle gradients")
            points = row["quadrature"]
            if len(points) != 9 or any((p["xi"], p["eta"]) != (Q[q//3], Q[q%3]) for q, p in enumerate(points)):
                raise ValueError("quadrature ordering must be xi slow, eta fast")
            P = [p["P"] for p in points]
            if any(not isinstance(v, Decimal) or not v.is_finite() for p in P for r in p for v in r):
                raise ValueError("stress authority must be finite Decimal")
            div = []
            for ix in range(3):
                for iy in range(3):
                    div.append([sum((2/hx*D[ix][b]*P[3*b+iy][i][0]+2/hy*D[iy][b]*P[3*ix+b][i][1]
                                     for b in range(3)), ZERO) for i in (0, 1)])
            body = [[-sum((dw[q]*shape[q][a]*div[q][i] for q in range(9)), ZERO) for i in (0, 1)] for a in range(4)]
            volume = [[sum((dw[q]*sum((P[q][i][j]*dec(grads[q, a, j]) for j in (0, 1)), ZERO)
                            for q in range(9)), ZERO) for i in (0, 1)] for a in range(4)]
            local_edges = [[ZERO]*2 for _ in range(4)]
            for label, ends, samples, normal in EDGES:
                # Factor-compatible weights reproduce the saved volume rule;
                # the separately named physical rule uses declared thickness.
                factor = 6*dw[0]/(hy if label in ("top", "bottom") else hx)
                physical_factor = dec(thickness)*(hx if label in ("top", "bottom") else hy)/6
                edge = [[sum((factor*W[k]*shape[q][a]*sum((P[q][i][j]*normal[j] for j in (0, 1)), ZERO)
                              for k, q in enumerate(samples)), ZERO) for i in (0, 1)] for a in range(4)]
                physical = [[sum((physical_factor*W[k]*shape[q][a]*sum((P[q][i][j]*normal[j] for j in (0, 1)), ZERO)
                                  for k, q in enumerate(samples)), ZERO) for i in (0, 1)] for a in range(4)]
                for a in range(4):
                    for i in (0, 1):
                        local_edges[a][i] += edge[a][i]
                ids = [cn[a] for a in ends]
                incidence.setdefault(tuple(sorted(ids)), []).append(dict(element=e, side=label, node_ids=ids,
                    consistent_N=[edge[a] for a in ends], physical_N=[physical[a] for a in ends]))
            direct = [v for r in volume for v in r]
            reconstructed = [local_edges[a][i]+body[a][i] for a in range(4) for i in (0, 1)]
            recorded = [v for r in row["material_internal_N"] for v in r]
            local_checks = dict(sbp_identity=_check(direct, reconstructed, identity_limit),
                                supplied_volume_identity=_check(recorded, direct, identity_limit))
            for a, node in enumerate(cn):
                for i in (0, 1):
                    fields["material_N"][2*node+i] += recorded[2*a+i]
                    fields["minus_projected_div_N"][2*node+i] += body[a][i]
            element_rows.append(dict(element=e, effective_thickness_mm=36*dw[0]/(hx*hy),
                physical_thickness_mm=dec(thickness), relative_weight_scale_error=36*dw[0]/(hx*hy*dec(thickness))-ONE,
                stress_interpolant_divergence=div, checks=local_checks))
        edge_rows = []
        for key, contributions in sorted(incidence.items()):
            if len(contributions) not in (1, 2):
                raise ValueError("nonmanifold edge in rectangular mesh")
            external = len(contributions) == 1
            top_edge = external and set(key) <= top and contributions[0]["side"] == "top"
            destination = "top_edge_consistent_N" if top_edge else "other_external_edge_consistent_N" if external else "internal_interface_jump_N"
            accum = {n: [ZERO, ZERO] for n in key}
            for row in contributions:
                for node, consistent, physical in zip(row["node_ids"], row["consistent_N"], row["physical_N"]):
                    for i in (0, 1):
                        fields[destination][2*node+i] += consistent[i]
                        accum[node][i] += consistent[i]
                        if top_edge:
                            fields["top_edge_physical_simpson_N"][2*node+i] += physical[i]
            edge_rows.append(dict(node_ids=list(key), classification="external_top" if top_edge else "external_other" if external else "internal_jump",
                                  adjacent_elements=[r["element"] for r in contributions], consistent_N=[accum[n] for n in key]))
        fields["top_weight_correction_N"] = [a-b for a, b in zip(fields["top_edge_consistent_N"], fields["top_edge_physical_simpson_N"])]
        fields["material_minus_top_consistent_N"] = [a-b for a, b in zip(fields["material_N"], fields["top_edge_consistent_N"])]
        fields["material_minus_top_physical_N"] = [a-b for a, b in zip(fields["material_N"], fields["top_edge_physical_simpson_N"])]
        rhs = [a+b+c for a, b, c in zip(fields["other_external_edge_consistent_N"], fields["internal_interface_jump_N"], fields["minus_projected_div_N"])]
        checks = dict(global_consistent_identity=_check(fields["material_minus_top_consistent_N"], rhs, identity_limit),
                      global_physical_identity=_check(fields["material_minus_top_physical_N"],
                                                     [a+b for a, b in zip(rhs, fields["top_weight_correction_N"])], identity_limit))
        passed = all(c["passed"] for c in checks.values()) and all(c["passed"] for e in element_rows for c in e["checks"].values())
        return dict(schema="contact_c2_material_sbp_v1", precision_digits=precision, status="pass" if passed else "not_pass",
            sign="internal force on model; negate every term together for model-on-plane display", fields=fields,
            elements=element_rows, edges=edge_rows, checks=checks,
            identity="material - consistent_top = other_external + internal_jump - projected_div_volume",
            physical_identity="material - physical_Simpson_top = other_external + internal_jump - projected_div_volume + top_weight_correction",
            interpretation="P^I is the elementwise biquadratic Lobatto-sample stress interpolant; its divergence is a discrete diagnostic, not continuum stress equilibrium")
