"""Read-only spatial diagnosis of the frozen C2 fine-mesh force-gate failure.

Uses archived production/HP force arrays and saved J, never imports mechanics,
AD or solvers. Selected NumPy kinematics are illustrative arithmetic probes,
not claimed to reproduce XLA operation order or to repair the failed state.
"""
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import hashlib
import json
from pathlib import Path
import platform

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT/"hf4_c2_diagnostics/experiments/mesh_h00625"
OUT = ROOT/"hf4_c2_diagnostics/mesh_force_failure_diagnosis.json"
STATE_INDEX = 20
READBACK_TOLERANCE = Decimal("1e-60")
ZERO, ONE = Decimal(0), Decimal(1)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def dec(v):
    return Decimal.from_float(float(v))


def norm(v):
    return sum((x*x for x in v), ZERO).sqrt()


def plain(v):
    if isinstance(v, Decimal):
        return str(v)
    if isinstance(v, dict):
        return {str(k): plain(x) for k, x in v.items()}
    if isinstance(v, (tuple, list)):
        return [plain(x) for x in v]
    if isinstance(v, np.ndarray):
        return plain(v.tolist())
    if isinstance(v, np.generic):
        return v.item()
    return v


def main():
    if OUT.exists():
        raise FileExistsError("preserve existing failure diagnosis")
    bindings = {}
    def bind(path, expected=None):
        path = Path(path).resolve()
        assert path.is_relative_to(ROOT)
        digest = sha(path)
        assert expected is None or digest == expected, path
        bindings[path.relative_to(ROOT).as_posix()] = digest
        return path
    def read(path, expected=None):
        return json.loads(bind(path, expected).read_text(encoding="utf-8-sig"))
    audit = read(RUN/"audit.json")
    assert audit["status"] == "not_pass"
    for name, digest in audit["input_and_helper_sha256"].items():
        bind(RUN/name, digest)
    for name, digest in audit["detail_output_sha256"].items():
        bind(RUN/name, digest)
    compact = audit["states"][STATE_INDEX]
    row = read(RUN/compact["detail_file"], compact["detail_sha256"])
    assert row["state_id"] == "uniform_tmc:20" and row["parameter_s"] == .5 and row["status"] == "not_pass"
    failures = [c for c in row["checks"] if c["status"] != "pass"]
    assert len(failures) == 1 and failures[0]["name"] == "production_vs_hp80_total_force"
    stage = RUN/"stages/uniform_tmc"
    meta = read(stage/"metadata.json")
    entry = read(stage/"steps/index.json")["steps"][STATE_INDEX]
    with np.load(bind(stage/"model.npz", meta["model_sha256"]), allow_pickle=False) as f:
        model = dict(f)
    with np.load(bind(stage/"steps"/entry["file"], entry["sha256"]), allow_pickle=False) as f:
        arrays = dict(f)
    for action in ("solve", "audit"):
        receipt = read(RUN.parent/f"{RUN.name}.{action}.receipt.json")
        bind(RUN.parent/f"{RUN.name}.{action}.log", receipt["log_sha256"])
        assert receipt["timed_out"] is False
        assert receipt["returncode"] == (0 if action == "solve" else 1)
        if action == "audit":
            bind(RUN/"audit.json", receipt["audit_sha256"])
    xy, conn = model["coordinates"], model["connectivity"]
    fixed = set(map(int, model["fixed_dofs"]))
    adjacent = [[] for _ in xy]
    for e, ids in enumerate(conn):
        for n in ids:
            adjacent[int(n)].append(e)
    with localcontext() as ctx:
        ctx.prec = 120
        hp = {p: row["precision_evidence_decimal"][str(p)] for p in (80, 120)}
        component_names = {"total": ("internal_force", "internal_decimal"),
                           "material": ("material_internal_force", "material_internal_decimal"),
                           "regularization": ("regularization_internal_force", "regularization_internal_decimal")}
        vectors, components = {}, {}
        for name, (archive, authority) in component_names.items():
            exact_prod = list(map(dec, arrays[archive]))
            h80 = list(map(Decimal, hp[80][authority]))
            h120 = list(map(Decimal, hp[120][authority]))
            error = [a-b for a, b in zip(exact_prod, h80)]
            precision_error = [a-b for a, b in zip(h80, h120)]
            observed = row["measurements"]["component_precision"][name+"_force"]
            n, cross = norm(error), norm(precision_error)
            assert abs(n-Decimal(observed["absolute_error"])) <= READBACK_TOLERANCE*max(n, ONE)
            assert abs(cross-Decimal(observed["cross_precision_absolute_error"])) <= READBACK_TOLERANCE
            vectors[name] = dict(production=exact_prod, hp80=h80, hp120=h120, error=error, precision_error=precision_error)
            components[name] = dict(production_minus_HP80_norm_N=n, HP80_minus_HP120_norm_N=cross,
                production_minus_HP80_max_abs_N=max(map(abs, error)), reference_norm_N=norm(h80),
                frozen_relative_error=observed["relative_error"], frozen_denominator_N=observed["denominator"])
        e = vectors["total"]["error"]
        square_norm = sum((x*x for x in e), ZERO)
        sf = Decimal(hp[80]["force_scale_decimal"])
        relative = square_norm.sqrt()/sf
        assert relative == Decimal(row["measurements"]["component_precision"]["total_force"]["relative_error"])
        limit = Decimal(failures[0]["limit"])
        assert relative > limit
        partitions = {"component": {}, "constraint": {}, "reference_y_band": {}, "reference_x_span": {}}
        for i, error in enumerate(e):
            x, y = xy[i//2]
            labels = dict(component="x" if i%2 == 0 else "y", constraint="fixed" if i in fixed else "free",
                reference_y_band="below_body_top" if y < 1 else "body_top_level" if y == 1 else "gap_interior" if y < 1.25 else "numerical_top",
                reference_x_span="within_initial_body_span" if 0 <= x <= 2 else "outside_initial_body_span")
            for partition, label in labels.items():
                item = partitions[partition].setdefault(label, dict(dof_count=0, squared_error_N2=ZERO, signed_error_sum_N=ZERO))
                item["dof_count"] += 1
                item["squared_error_N2"] += error*error
                item["signed_error_sum_N"] += error
        for groups in partitions.values():
            for item in groups.values():
                item["error_norm_N"] = item["squared_error_N2"].sqrt()
                item["squared_norm_fraction"] = item["squared_error_N2"]/square_norm
        order = sorted(range(len(e)), key=lambda i: abs(e[i]), reverse=True)
        largest = []
        for i in order[:40]:
            n = i//2
            largest.append(dict(dof=i, component="x" if i%2 == 0 else "y", node=n,
                reference_coordinate_mm=xy[n], fixed=i in fixed, adjacent_elements=adjacent[n],
                adjacent_minimum_HP80_J=min(Decimal(v) for a in adjacent[n] for v in hp[80]["J_decimal"][a]),
                production_force_N=vectors["total"]["production"][i], HP80_force_N=vectors["total"]["hp80"][i],
                total_error_N=e[i], material_error_N=vectors["material"]["error"][i], regularization_error_N=vectors["regularization"]["error"][i]))
        joins = [vectors["total"]["production"][i]-vectors["material"]["production"][i]-vectors["regularization"]["production"][i] for i in range(len(e))]
        hp_join = [vectors["total"]["hp80"][i]-vectors["material"]["hp80"][i]-vectors["regularization"]["hp80"][i] for i in range(len(e))]
        top = list(map(int, model["top_nodes"]))
        net_error = -sum((e[2*n+1] for n in top), ZERO)
        hp_net = -sum((vectors["total"]["hp80"][2*n+1] for n in top), ZERO)
        net = dict(HP80_top_on_plane_N=hp_net, production_top_on_plane_error_N=net_error,
                   abs_net_error_relative_to_HP_net=abs(net_error)/abs(hp_net),
                   interpretation="Full-vector admission failed even if signed global errors cancel; net force cannot override its gate.")
        Jrows = []
        Jerrors = []
        for element, (prod, exact, other) in enumerate(zip(arrays["J"], hp[80]["J_decimal"], hp[120]["J_decimal"])):
            for q, (a, b, c) in enumerate(zip(prod, exact, other)):
                authoritative = Decimal(b)
                error = dec(a)-authoritative
                Jerrors.append(error)
                Jrows.append(dict(element=element, q=q, reference_centroid_mm=xy[conn[element]].mean(axis=0),
                    solid=bool(model["solid"][element]), production_J=dec(a), HP80_J=authoritative,
                    error=error, relative_error=error/authoritative, HP80_minus_HP120=authoritative-Decimal(c)))
        Jrows.sort(key=lambda x: abs(x["relative_error"]), reverse=True)
        selected_elements = sorted({r["element"] for r in Jrows[:12]} | {a for row0 in largest[:4] for a in row0["adjacent_elements"]})
        probes = []
        for element in selected_elements:
            ids = conn[element]
            lift = arrays["u_lift"].reshape(-1, 2)[ids]
            fluctuation = arrays["u_fluctuation"].reshape(-1, 2)[ids]
            GL = np.einsum("ai,qaj->qij", lift, model["grad"])
            Gw = np.einsum("ai,qaj->qij", fluctuation, model["grad"])
            fnumpy = (np.eye(2)+GL)+Gw
            for q in (0, 4, 8):
                exact_GL = [[sum((dec(lift[a, i])*dec(model["grad"][q, a, j]) for a in range(4)), ZERO) for j in (0, 1)] for i in (0, 1)]
                exact_Gw = [[sum((dec(fluctuation[a, i])*dec(model["grad"][q, a, j]) for a in range(4)), ZERO) for j in (0, 1)] for i in (0, 1)]
                exact_F = [[(ONE if i == j else ZERO)+exact_GL[i][j]+exact_Gw[i][j] for j in (0, 1)] for i in (0, 1)]
                exact_J = exact_F[0][0]*exact_F[1][1]-exact_F[0][1]*exact_F[1][0]
                assert abs(exact_J-Decimal(hp[120]["J_decimal"][element][q])) <= READBACK_TOLERANCE
                ynumerator = abs(ONE+exact_GL[1][1])+abs(exact_Gw[1][1])
                probes.append(dict(element=element, q=q, reference_centroid_mm=xy[ids].mean(axis=0),
                    exact_GL=exact_GL, exact_Gw=exact_Gw, exact_F=exact_F, exact_J=exact_J,
                    archived_production_J=dec(arrays["J"][element, q]),
                    numpy_reconstruction_F=fnumpy[q], numpy_F_error=[[dec(fnumpy[q, i, j])-exact_F[i][j] for j in (0, 1)] for i in (0, 1)],
                    Fyy_final_addition_cancellation_ratio=ynumerator/abs(exact_F[1][1]),
                    interpretation="NumPy is an illustrative float64 arithmetic path, not a replay of the production XLA kernel."))
        report = dict(schema="contact_c2_fine_mesh_fixed_state_force_failure_v1", created_utc=datetime.now(timezone.utc).isoformat(),
            status="diagnosis_completed_original_failure_preserved", no_new_FE=True, no_threshold_change=True,
            run=RUN.relative_to(ROOT).as_posix(), state_id=row["state_id"], d_mm=.5,
            original_run_status=audit["status"], original_failed_check=failures[0],
            original_audit_counts=audit["summary"], components=components,
            force_gate=dict(absolute_error_N=square_norm.sqrt(), force_scale_N=sf, relative_error=relative, limit=limit,
                            threshold_utilization=relative/limit, exceedance_fraction=relative/limit-ONE),
            all_gate_statuses={c["name"]:c["status"] for c in row["checks"]}, net_force_error=net,
            partitions=partitions, largest_error_dofs=largest,
            largest_12_squared_error_fraction=sum((e[i]**2 for i in order[:12]), ZERO)/square_norm,
            total_minus_separate_component_assembly=dict(production_norm_N=norm(joins), HP80_norm_N=norm(hp_join),
                interpretation="Difference of globally archived total versus separately assembled material+regularization; does not isolate element-local material evaluation from material assembly."),
            full_error_vectors_N={name: item["error"] for name, item in vectors.items()},
            J_diagnostics=dict(production_minus_HP80_norm=norm(Jerrors), maximum_absolute_error=max(map(abs,Jerrors)),
                               maximum_relative_error=abs(Jrows[0]["relative_error"]), largest_relative_errors=Jrows[:30]),
            selected_exact_split_kinematic_probes=probes,
            supported_findings=[
                "The saved total-force norm failure is independently reproduced without any FE/material reevaluation.",
                "The force discrepancy is almost wholly in the material vector; regularization and HP80/120 discrepancies are many orders smaller.",
                "Most force error lies in vertical free DOFs of the strongly compressed background gap; saved J has relative errors amplified from sub-femtoscale absolute errors.",
                "Exact selected split kinematics exhibit subtraction of order-one lift and fluctuation gradients to obtain order-1e-5 Fyy; this is a concrete conditioning mechanism, not yet an isolated production instruction-level cause."],
            falsifiable_followups=[
                "At the bound fixed state, compare production per-element F/J/P/force against exact-component kinematics and HP before global assembly, without Newton updates; disappearance after exact kinematics would locate the dominant error upstream of material law evaluation.",
                "Hold saved float64 F/J fixed and evaluate Piola at high precision; separate determinant/gradient input error from float64 logarithm/inverse/constitutive arithmetic.",
                "Accumulate the same production per-element material forces in Decimal to isolate global assembly rounding; then compare a cancellation-resistant gradient/F representation in a new version against the original strict gate, retaining this failure."],
            limitations=["Saved NPZ does not archive production F, P or element-local material forces; spatial correlation alone cannot distinguish each arithmetic stage.",
                         "NumPy probes are not proof of the production compiler's operation ordering.",
                         "A small net-force difference, valid geometry or small equilibrium residual cannot substitute for the failed full-vector evaluation gate.",
                         "No new state has been accepted or made comparable by this diagnosis."],
            readback_tolerance=READBACK_TOLERANCE, arithmetic_digits=120,
            input_sha256=bindings, script_sha256=sha(__file__), environment=dict(python=platform.python_version(), numpy=np.__version__))
    bind(__file__)
    assert all(sha(ROOT/name) == digest for name,digest in bindings.items())
    with OUT.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(plain(report), stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps(plain(dict(status=report["status"], force_gate=report["force_gate"],
        component_error_norms={k:v["production_minus_HP80_norm_N"]for k,v in components.items()},
        partitions=partitions, net_force_error=net,
        global_component_assembly_difference=report["total_minus_separate_component_assembly"],
        maximum_J_relative_error=report["J_diagnostics"]["maximum_relative_error"],
        maximum_selected_Fyy_cancellation_ratio=max(p["Fyy_final_addition_cancellation_ratio"]for p in probes),
        output_sha256=sha(OUT),script_sha256=sha(__file__))), indent=2))


if __name__ == "__main__":
    main()
