"""Manufactured algebra/constitutive checks for C2; never solves equilibrium.

Exact Fraction identities are mandatory. Decimal and production comparisons
are diagnostic-only and do not modify any frozen C1 acceptance threshold.
"""
from __future__ import annotations

from decimal import Decimal, localcontext
from fractions import Fraction
from pathlib import Path
import hashlib
import json
import platform
import random
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "hf_repo"
OUT = Path(__file__).resolve().parent / "results.json"
SEED = 20260921
EXACT_PATCH_CASES = 8
HP_DIGITS = (80, 120)
HP_LIMIT = Decimal("1e-45")
PRODUCTION_LIMIT = Decimal("1e-12")
LAM = 100*.3/((1+.3)*(1-2*.3))
MU = 100/(2*(1+.3))
KR = 1e-6*2**2*(100/(3*(1-2*.3))+4*MU/3)
SIGNS = (1, -1, 1, -1)
NODES = ((-1, -1), (1, -1), (1, 1), (-1, 1))
Q = ((-1, 1), (0, 4), (1, 1))
DERIVATIVE = ((Fraction(-3, 2), Fraction(2), Fraction(-1, 2)),
              (Fraction(-1, 2), Fraction(0), Fraction(1, 2)),
              (Fraction(1, 2), Fraction(-2), Fraction(3, 2)))
SOURCES = ["hf_repo/src/hf_eval/split_kernel.py", "hf_repo/src/hf_eval/tmc_kernel.py",
           "hf_repo/src/hf_eval/tmc.py", "hf_repo/src/hf_eval/contact_c1.py",
           "hf_repo/scripts/hf4_split_precision_reference.py", "hf_repo/scripts/hf2_precision_reference.py",
           "hf_repo/scripts/contact_c2_sbp.py",
           "docs/PAPER_FORMULATION_AUDIT.md", "docs/TMC_SOURCE_AUDIT.md", "docs/HF0_REPORT.md",
           "hf0_audit/tmc/assembleKtFi.m.numbered.txt", "hf0_audit/tmc/initializeFEA.m.numbered.txt"]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dec(x):
    if isinstance(x, Fraction):
        return Decimal(x.numerator)/Decimal(x.denominator)
    return Decimal.from_float(float(x))


def norm(v):
    return sum((x*x for x in v), Decimal(0)).sqrt()


def relative(a, b):
    return norm([x-y for x, y in zip(a, b)])/max(norm(b), Decimal(1))


def plain(x):
    if isinstance(x, (Decimal, Fraction)):
        return str(x)
    if isinstance(x, dict):
        return {str(k): plain(v) for k, v in x.items()}
    if isinstance(x, (tuple, list)):
        return [plain(v) for v in x]
    if isinstance(x, np.ndarray):
        return plain(x.tolist())
    if isinstance(x, np.generic):
        return x.item()
    return x


def operators(hx=Fraction(1), hy=Fraction(1)):
    n, grad, weights = [], [], []
    for xi, wx in Q:
        for eta, wy in Q:
            n.append([Fraction((1+sx*xi)*(1+sy*eta), 4) for sx, sy in NODES])
            grad.append([[Fraction(sx*(1+sy*eta), 2)/hx, Fraction(sy*(1+sx*xi), 2)/hy] for sx, sy in NODES])
            weights.append(hx*hy*wx*wy/36)
    hessian = [[[Fraction(0), s/(hx*hy)], [s/(hx*hy), Fraction(0)]] for s in SIGNS]
    return n, grad, hessian, weights


def exact_patch_cases():
    rng = random.Random(SEED)
    cases = []
    hx, hy, nx, ny = Fraction(1, 2), Fraction(1, 4), 3, 2
    for case in range(EXACT_PATCH_CASES):
        values = [[Fraction(rng.randrange(-16, 17), 64) for _ in (0, 1)] for _ in range((nx+1)*(ny+1))]
        # These positive rational integrals stand for arbitrary element values
        # of integral(kr*exp(-5J)); the cancellation holds for every such value.
        coefficients = [Fraction(rng.randrange(1, 17), 128) for _ in range(nx*ny)]
        force = [[Fraction(0), Fraction(0)] for _ in values]
        rows = []
        for j in range(ny):
            for i in range(nx):
                ids = [j*(nx+1)+i, j*(nx+1)+i+1, (j+1)*(nx+1)+i+1, (j+1)*(nx+1)+i]
                c = coefficients[j*nx+i]
                d = [sum(SIGNS[a]*values[k][component] for a, k in enumerate(ids))/(hx*hy) for component in (0, 1)]
                _, _, hess, _ = operators(hx, hy)
                local = []
                for a, node in enumerate(ids):
                    term = [c*(hess[a][0][1]+hess[a][1][0])*d[k] for k in (0, 1)]
                    expected = [2*c*SIGNS[a]*d[k]/(hx*hy) for k in (0, 1)]
                    assert term == expected
                    local.append(term)
                    force[node] = [force[node][k]+term[k] for k in (0, 1)]
                assert all(local[2][k]+local[3][k] == 0 for k in (0, 1))
                rows.append(dict(connectivity=ids, integrated_coefficient=c, mixed_derivative=d, local_force=local))
        top = list(range(ny*(nx+1), (ny+1)*(nx+1)))
        total = [sum((force[a][k] for a in top), Fraction(0)) for k in (0, 1)]
        assert total == [0, 0]
        assert any(force[a][1] != 0 for a in top)
        cases.append(dict(case=case, node_values=values, elements=rows, assembled_force=force,
                          top_nodes=top, top_sum=total, first_top_node_force=force[top[0]],
                          exact_identity_pass=True))
    return dict(seed=SEED, nx=nx, ny=ny, hx=hx, hy=hy, cases=cases,
                interpretation="algebraic identities for arbitrary positive element coefficient, not equilibrium/contact samples")


def response(un, vector, precision):
    n, grad, hessian, weights = operators()
    with localcontext() as ctx:
        ctx.prec = precision
        zero, one = Decimal(0), Decimal(1)
        u = [[dec(v) for v in row] for row in un]
        v = [[dec(v) for v in row] for row in vector]
        g = [[[dec(x) for x in row] for row in q] for q in grad]
        H = [[[dec(x) for x in row] for row in a] for a in hessian]
        # Match the archived binary64 volume rule. Its tensor factor differs
        # slightly from an ideal rational physical-area weight.
        w = [dec(float(x)) for x in weights]
        hu = [sum((u[a][i]*H[a][0][1] for a in range(4)), zero) for i in (0, 1)]
        hv = [sum((v[a][i]*H[a][0][1] for a in range(4)), zero) for i in (0, 1)]
        material, reg, dm, dr = ([zero]*8 for _ in range(4))
        stress, jacobians = [], []
        integrated_c = zero
        for q in range(9):
            F = [[(one if i == j else zero)+sum((u[a][i]*g[q][a][j] for a in range(4)), zero) for j in (0, 1)] for i in (0, 1)]
            V = [[sum((v[a][i]*g[q][a][j] for a in range(4)), zero) for j in (0, 1)] for i in (0, 1)]
            J = F[0][0]*F[1][1]-F[0][1]*F[1][0]
            assert J > 0
            jacobians.append(J)
            T = [[F[1][1]/J, -F[1][0]/J], [-F[0][1]/J, F[0][0]/J]]
            coefficient = dec(LAM)*J.ln()-dec(MU)
            P = [[dec(MU)*F[i][j]+coefficient*T[i][j] for j in (0, 1)] for i in (0, 1)]
            stress.append(P)
            dJ = F[1][1]*V[0][0]+F[0][0]*V[1][1]-F[0][1]*V[1][0]-F[1][0]*V[0][1]
            dT = [[-sum((T[i][k]*V[l][k]*T[l][j] for k in (0, 1) for l in (0, 1)), zero) for j in (0, 1)] for i in (0, 1)]
            dP = [[dec(MU)*V[i][j]+dec(LAM)*dJ/J*T[i][j]+coefficient*dT[i][j] for j in (0, 1)] for i in (0, 1)]
            c = dec(KR)*w[q]*(-5*J).exp()
            integrated_c += c
            for a in range(4):
                for i in (0, 1):
                    k = 2*a+i
                    material[k] += w[q]*sum(P[i][j]*g[q][a][j] for j in (0, 1))
                    dm[k] += w[q]*sum(dP[i][j]*g[q][a][j] for j in (0, 1))
                    reg[k] += 2*c*H[a][0][1]*hu[i]
                    dr[k] += 2*c*H[a][0][1]*(hv[i]-5*dJ*hu[i])
        # The nine stress values define the bicomplete degree-(2,2) P^I.
        projected_div = []
        for ix in range(3):
            for iy in range(3):
                projected_div.append([sum((2*dec(DERIVATIVE[ix][b])*stress[3*b+iy][i][0]
                                          +2*dec(DERIVATIVE[iy][b])*stress[3*ix+b][i][1] for b in range(3)), zero) for i in (0, 1)])
        body = [sum((w[q]*dec(n[q][a])*projected_div[q][i] for q in range(9)), zero) for a in range(4) for i in (0, 1)]
        edges = {}
        for label, indices, normal in (("bottom", (0, 3, 6), (0, -1)), ("right", (6, 7, 8), (1, 0)),
                                       ("top", (2, 5, 8), (0, 1)), ("left", (0, 1, 2), (-1, 0))):
            edges[label] = [sum((6*w[0]*qw*dec(n[q][a])*sum(stress[q][i][j]*normal[j] for j in (0, 1))
                                for q, (_, qw) in zip(indices, Q)), zero) for a in range(4) for i in (0, 1)]
        all_edges = [sum((value[i] for value in edges.values()), zero) for i in range(8)]
        sbp_error = relative(material, [a-b for a, b in zip(all_edges, body)])
        corner = [2*integrated_c*SIGNS[a]*hu[i] for a in range(4) for i in (0, 1)]
        return dict(material=material, regularization=reg, material_Jv=dm, regularization_Jv=dr,
            P=stress, J=jacobians, mixed_Hu=hu, integrated_regularization_coefficient=integrated_c,
            edge_internal_projection=edges, stress_interpolant_divergence=projected_div,
            projected_div_volume_term=body, material_sbp_relative_error=sbp_error,
            corner_force_relative_error=relative(reg, corner), full_top_regularization_sum=reg[5]+reg[7],
            full_top_regularization_Jv_sum=dr[5]+dr[7])


def main():
    if OUT.exists():
        raise FileExistsError("preserve earlier manufactured evidence")
    before = {p: digest(ROOT/p) for p in SOURCES}
    sys.path.insert(0, str(REPO/"src"))
    sys.path.insert(0, str(REPO/"scripts"))
    import jax
    jax.config.update("jax_enable_x64", True)
    from hf_eval import split_kernel, tmc_kernel
    from hf4_split_precision_reference import DecimalSplitQ1Reference
    from contact_c2_sbp import decompose_material
    assert jax.default_backend() == "cpu"
    exact = exact_patch_cases()
    n, grad, hess, weights = operators()
    ops = tmc_kernel.operators(1., 1.)
    for key, expected in (("grad", grad), ("hessian", hess), ("weights", weights)):
        assert np.array_equal(ops[key], np.array(expected, dtype=np.float64))
    # Explicit coefficient tuples (a,b,c,d) for u=a+b*x+c*y+d*x*y.
    fields = {
        "identity": ((0, 0, 0, 0), (0, 0, 0, 0)),
        "affine_compressed_shear_counterexample": ((0, 0, Fraction(1, 8), 0), (0, 0, Fraction(-1, 64), 0)),
        "bilinear": ((0, Fraction(-1, 8), 0, Fraction(1, 16)), (0, Fraction(1, 32), Fraction(-1, 4), Fraction(1, 8))),
        "near_identity": ((0, Fraction(1, 2048), Fraction(1, 1024), Fraction(1, 4096)), (0, 0, Fraction(-1, 1024), Fraction(1, 2048))),
    }
    coords = ((0, 0), (1, 0), (1, 1), (0, 1))
    vector = [[Fraction(k, 16) for k in pair] for pair in ((1, -2), (3, 1), (-1, 4), (2, -3))]
    output = []
    for name, coefficients in fields.items():
        un = [[a+b*x+c*y+d*x*y for a, b, c, d in coefficients] for x, y in coords]
        hp = {p: response(un, vector, p) for p in HP_DIGITS}
        with localcontext() as ctx:
            ctx.prec = 120
            checks = {"material_sbp": hp[120]["material_sbp_relative_error"],
                      "regularization_corner": hp[120]["corner_force_relative_error"]}
            for key in ("material", "regularization", "material_Jv", "regularization_Jv"):
                checks["hp80_vs_hp120_"+key] = relative(hp[80][key], hp[120][key])
            checks["full_top_reg_sum"] = abs(hp[120]["full_top_regularization_sum"])
            checks["full_top_reg_Jv_sum"] = abs(hp[120]["full_top_regularization_Jv_sum"])
            assert all(v <= HP_LIMIT for v in checks.values())
            lift = np.array(un, dtype=np.float64).reshape(1, 8)
            zero = np.zeros_like(lift)
            prod = split_kernel.batch_response_split(lift, zero, ops, LAM, MU, KR, tangent=True)
            old = tmc_kernel.batch_response(lift, ops, LAM, MU, KR, tangent=True)
            fixture = dict(connectivity=np.array([[0, 1, 2, 3]]), coordinates=np.array(coords,dtype=float),
                           top_nodes=np.array([2,3]), fixed_dofs=np.array([],dtype=np.int64),
                           F0=np.zeros(8), lam=np.array([LAM]), mu=np.array([MU]),
                           kr=np.asarray(KR), grad=ops["grad"], hessian=ops["hessian"], weights=ops["weights"])
            v = np.array(vector, dtype=np.float64).ravel()
            existing = DecimalSplitQ1Reference(fixture, precision=120).evaluate(lift.ravel(), zero.ravel(), tangent_direction=v)
            for key, saved in (("material", "material_internal_decimal"), ("regularization", "regularization_internal_decimal"),
                               ("material_Jv", "material_tangent_action_decimal"), ("regularization_Jv", "regularization_tangent_action_decimal")):
                checks["existing_HP_"+key] = relative(existing[saved], hp[120][key])
                assert checks["existing_HP_"+key] <= HP_LIMIT
            element = dict(element=0,connectivity=[0,1,2,3],material_internal_N=[hp[120]["material"][2*a:2*a+2] for a in range(4)],
                quadrature=[dict(xi=Decimal(xi),eta=Decimal(eta),P=P) for P,(xi,eta) in zip(hp[120]["P"],((x,y) for x,_ in Q for y,_ in Q))])
            sbp = decompose_material(fixture,[element],precision=120)
            assert sbp["status"] == "pass"
            production_checks = {}
            for key, field in (("material", "material_residual"), ("regularization", "regularization_residual")):
                for tag, values in (("split", prod), ("unsplit", old)):
                    production_checks[tag+"_"+key] = relative([dec(x) for x in values[field][0]], hp[120][key])
            total_action = prod["tangent"][0]@v
            production_checks["split_full_Jv"] = relative([dec(x) for x in total_action],
                [a+b for a, b in zip(hp[120]["material_Jv"], hp[120]["regularization_Jv"])])
            P_from_FS = np.einsum("qij,qjk->qik", prod["F"][0], prod["stress_second_piola"][0])
            production_checks["first_Piola_equals_F_second_Piola"] = relative([dec(x) for x in P_from_FS.ravel()],
                [x for P in hp[120]["P"] for row in P for x in row])
            assert all(v <= PRODUCTION_LIMIT for v in production_checks.values())
            counterexample = None
            if name == "affine_compressed_shear_counterexample":
                projected = [-hp[120]["edge_internal_projection"]["top"][i] for i in (5, 7)]
                nodal = [-hp[120]["material"][i] for i in (5, 7)]
                assert all(v > 0 for v in projected) and nodal[0] < 0
                counterexample = dict(top_nodes_TR_TL_direct_plane_force=projected, top_nodes_TR_TL_nodal_plane_force=nodal,
                    positive_J=min(hp[120]["J"]), all_Hu_zero=hp[120]["mixed_Hu"] == [0, 0],
                    explanation="right/left side shear accounts for the difference; manufactured field is not a C1 equilibrium solution")
            output.append(dict(name=name,coefficients=coefficients,node_values=un,tangent_direction=vector,
                               hp=hp,identity_checks=checks,production_checks=production_checks,counterexample=counterexample,
                               sbp_helper=sbp))
    assert all(digest(ROOT/p) == h for p, h in before.items())
    report = dict(schema="hf4_c2_formulation_manufactured_checks_v1", status="pass", no_equilibrium_solve=True,
        comparison_scales="norm differences divided by max(reference norm,1); exact Fraction identities require equality",
        thresholds=dict(hp_decimal=HP_LIMIT, production=PRODUCTION_LIMIT), precision_digits=HP_DIGITS,
        material=dict(lam_exact_binary64=dec(LAM), mu_exact_binary64=dec(MU), kr_exact_binary64=dec(KR)),
        exact_patch=exact, manufactured_fields=output, source_sha256=before,script_sha256=digest(__file__),
        environment=dict(python=platform.python_version(),numpy=np.__version__,jax=jax.__version__,backend=jax.default_backend()),
        limitations=["No claim that manufactured fields satisfy the frozen C1 free-boundary equilibrium.",
            "The P^I divergence is an explicit quadrature-sample interpolant derivative, not the continuous nonlinear stress derivative.",
            "These diagnostic thresholds do not replace or relax any C1 acceptance threshold."])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(plain(report), stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps(plain(dict(status="pass",exact_patch_cases=EXACT_PATCH_CASES,manufactured_fields=len(output),
        maximum_HP_identity_error=max(v for case in output for v in case["identity_checks"].values()),
        maximum_production_error=max(v for case in output for v in case["production_checks"].values()),
        results_sha256=digest(OUT), script_sha256=digest(__file__))),indent=2))


if __name__ == "__main__":
    main()
