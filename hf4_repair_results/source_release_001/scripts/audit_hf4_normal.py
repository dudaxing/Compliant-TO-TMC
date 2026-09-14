"""Independent saved-state HP and two-reference audit; never calls production FE.

Every accepted state, including bisections, is checked. State files are bound
by hash, and completed audits can resume only with the same files/spec/helpers.
"""
from pathlib import Path
import argparse
from decimal import Decimal, localcontext

import numpy as np

from hf4_common import read_json, read_npz, write_json, sha, timestamp
from hf4_normal_reference import evaluate_normal_reference
from hf4_precision_reference import evaluate_prescribed_state


def D(x):
    return Decimal.from_float(float(x))


def norm(v):
    return sum((x*x for x in v), Decimal(0)).sqrt()


def validate_state_inventory(entries, result, targets, scalars):
    """Reject incomplete, reordered or mislabeled evidence even if status says success."""
    declared = result["accepted_steps"]
    if len(entries) != len(declared) or len(scalars) != len(entries):
        raise ValueError("result/index/state counts disagree")
    original = []
    ds = []
    for i, (entry, state, reported) in enumerate(zip(entries, scalars, declared)):
        if entry["index"] != i or state["index"] != i or entry["d"] != state["d"] or state["d"] != reported["d"]:
            raise ValueError("index/state/result ordering or target disagrees")
        for field in ("is_original_target", "original_target_displacement", "bisection_depth"):
            if state[field] != reported[field]:
                raise ValueError("original/substep identity differs from production result")
        if state["is_original_target"]:
            if state["d"] != state["original_target_displacement"]:
                raise ValueError("original target flag is inconsistent")
            original.append(state["d"])
        elif state["original_target_displacement"] not in targets or state["original_target_displacement"] <= state["d"]:
            raise ValueError("substep must precede a declared original target")
        ds.append(state["d"])
    if len(ds) and (not np.all(np.isfinite(ds)) or any(b<=a for a,b in zip(ds,ds[1:]))):
        raise ValueError("state inputs must be finite and strictly increasing")
    if result["status"] == "success" and (original != targets or not result["target_reached"]
            or result["reached_displacement"] != targets[-1] or result["target_metrics"] is None
            or result["target_metrics"].get("d") != targets[-1]):
        raise ValueError("successful result does not cover all original targets")
    if result["status"] != "success" and (result["target_reached"] or result["target_metrics"] is not None):
        raise ValueError("failed result cannot claim target metrics")


def audit(run, output, spec_path, source_freeze):
    from hf4_input_audit import validate_inputs
    run, output = Path(run).resolve(), Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    spec, meta = read_json(spec_path), read_json(run/"metadata.json")
    if meta["spec_sha256"] != sha(spec_path) or meta["spec"] != spec:
        raise ValueError("spec differs from production run")
    index = read_json(run/"steps/index.json")
    entries = index["steps"]
    assert len(entries) == index["accepted_count"]
    paths = [run/"model.npz", run/"metadata.json", run/"steps/index.json", run/"result.json", Path(spec_path), Path(source_freeze)]
    paths += [Path(__file__), Path(__file__).with_name("hf4_precision_reference.py"),
              Path(__file__).with_name("hf2_precision_reference.py"), Path(__file__).with_name("hf4_normal_reference.py"),
              Path(__file__).with_name("hf4_common.py"), Path(__file__).with_name("hf4_input_audit.py")]
    for e in entries:
        for field, digest in (("file","arrays_sha256"),("metadata","metadata_sha256")):
            p = (run/"steps"/e[field]).resolve()
            if p.parent != run/"steps" or sha(p) != e[digest]:
                raise ValueError("state path or hash invalid")
            paths.append(p)
    result = read_json(run/"result.json")
    validate_state_inventory(entries, result, spec["targets_mm"],
                             [read_json(run/"steps"/e["metadata"]) for e in entries])
    bindings = {str(p):sha(p) for p in paths}
    if (output/"bindings.json").exists():
        if read_json(output/"bindings.json") != bindings:
            raise ValueError("resume inputs or audit code changed")
    else:
        write_json(output/"bindings.json", bindings)
    m = read_npz(run/"model.npz")
    input_audit = validate_inputs(spec, meta, m, read_json(source_freeze))
    write_json(output/"input_audit.json", input_audit)
    groups = {k[len("group_"):]:v for k,v in m.items() if k.startswith("group_")}
    model = dict(m, F0=np.zeros(len(m["base"])))
    rows = []
    for entry in entries:
        state_path = output/f"state_{entry['index']:04d}.json"
        commit_path = output/f"commit_{entry['index']:04d}.json"
        if state_path.exists():
            commitment = read_json(commit_path)
            required = {state_path.name, f"hp50_{entry['index']:04d}.json", f"reference_{entry['index']:04d}.json"}
            if entry["d"] == spec["targets_mm"][-1]:
                required.add(f"hp80_{entry['index']:04d}.json")
            if set(commitment) != required:
                raise ValueError("cached commitment does not cover all state evidence")
            for name, digest in commitment.items():
                file = (output/name).resolve()
                if file.parent != output or sha(file) != digest:
                    raise ValueError("cached HP evidence is missing or altered")
            cached = read_json(state_path)
            if cached["index"] != entry["index"] or cached["d"] != entry["d"]:
                raise ValueError("cached state identity differs")
            if any((Decimal(q["value"]) <= Decimal(q["bound"])) != (q["status"] == "pass") for q in cached["checks"]):
                raise ValueError("cached comparison status differs from saved values")
            rows.append(cached)
            continue
        a, r = read_npz(run/"steps"/entry["file"]), read_json(run/"steps"/entry["metadata"])
        ndof = len(m["base"])
        for field in ("u", "internal_force", "material_internal_force", "regularization_internal_force", "support_reaction"):
            if a[field].shape != (ndof,):
                raise ValueError(f"archived {field} shape differs from model DOFs")
        hp = evaluate_prescribed_state(model, a["u"], r["d"], m["base"], m["direction"], groups,
                                      meta["force_scale_per_length"], precision=spec["precision_digits"])
        if a["J"].shape != (len(m["connectivity"]), 9):
            raise ValueError("archived J shape differs from the model")
        ref = evaluate_normal_reference(**meta["reference_inputs"], d=r["d"], precision=spec["precision_digits"])
        checks = []

        def check(name, value, bound, kind="numerical"):
            checks.append(dict(name=name, kind=kind, value=str(value), bound=str(bound),
                               status="pass" if value <= bound else "not_pass"))

        with localcontext() as ctx:
            ctx.prec = spec["crosscheck_precision_digits"]
            c, mc = spec["numerical_criteria"], spec["model_criteria"]
            sf = hp["force_scale_decimal"]
            dims = meta["task"]["geometry"]
            EA = D(meta["task"]["material"]["E_MPa"])*D(dims["width_mm"])*D(dims["thickness_mm"])
            g0 = D(dims["gap_mm"])
            H1, H2 = D(dims["lower_height_mm"]), D(dims["upper_height_mm"])
            height = H1+H2+g0
            d = D(r["d"])
            check("hp_free_balance", hp["relative_residual_decimal"], Decimal(c["hp_relative_residual"]))
            check("hp_prescribed_values", hp["relative_constraint_decimal"], Decimal(c["hp_relative_constraint"]))
            check("hp_global_balance", hp["relative_force_balance_decimal"], Decimal(c["relative_global_balance"]))
            if not hp["positive_J"] or np.min(a["J"]) <= 0:
                check("positive_J", Decimal(1), Decimal(0))
            else:
                check("positive_J", Decimal(0), Decimal(0))
            for field, hpfield in (("internal_force","internal_decimal"),
                                   ("material_internal_force","material_internal_decimal"),
                                   ("regularization_internal_force","regularization_internal_decimal"),
                                   ("support_reaction","support_reaction_decimal")):
                error = norm([D(v)-w for v,w in zip(a[field],hp[hpfield])])/sf
                check("evaluation_"+field, error, Decimal(c["force_evaluation_relative_budget"]))
            finite, hard = ref["finite_gamma"], ref["hard_contact"]
            Fref, Gref = Decimal(finite["force_N"]), Decimal(finite["gap_mm"])
            Fhard, Ghard = Decimal(hard["force_N"]), Decimal(hard["gap_mm"])
            force_bound = Decimal(c["reference_force_absolute_over_EA"])*EA + Decimal(c["reference_force_relative"])*abs(Fref)
            force = D(r["drive_force"])
            check("force_vs_finite_medium_reference", abs(force-Fref), force_bound)
            check("hp_force_vs_finite_medium_reference", abs(hp["drive_force_decimal"]-Fref), force_bound)
            check("reference_length_equation", Decimal(finite["normalized_length_residual"]), Decimal(c["reference_equation_relative"]))
            check("reference_traction_equation", Decimal(finite["normalized_traction_residual"]), Decimal(c["reference_equation_relative"]))
            # Gap reconstructed from actual coordinates plus u, not archived float gap.
            reg = meta["regions"]
            upper = reg["upper_interface_nodes"]
            lower = reg["lower_interface_nodes"]
            gap = sum((D(w)*(D(m["coordinates"][i,1])+D(a["u"][2*i+1])
                             -D(m["coordinates"][j,1])-D(a["u"][2*j+1]))
                       for w,i,j in zip(reg["interface_weights"],upper,lower)), Decimal(0))
            check("gap_vs_finite_medium_reference", abs(gap-Gref), Decimal(c["reference_gap_absolute_over_g0"])*g0)
            check("archived_gap", abs(D(r["gap_mm"])-gap), Decimal(c["reference_gap_absolute_over_g0"])*g0)
            ss, sv = Decimal(finite["s_s"]), Decimal(finite["s_v"])
            errors = []
            for i, (_, raw_y) in enumerate(m["coordinates"]):
                y = D(raw_y)
                if y <= H1:
                    expected = d+(ss-1)*y
                elif y <= H1+g0:
                    expected = d+(ss-1)*H1+(sv-1)*(y-H1)
                else:
                    expected = (1-ss)*(height-y)
                errors.extend([abs(D(a["u"][2*i])), abs(D(a["u"][2*i+1])-expected)])
            check("displacement_vs_affine_reference", max(errors), Decimal(c["reference_displacement_absolute_over_total_height"])*height)
            side_bound = Decimal(c["side_force_consistency_absolute_over_EA"])*EA + Decimal(c["side_force_consistency_relative"])*abs(Fref)
            for name, sign in (("bottom_platen",1),("top_platen",-1)):
                group = r["group_reactions"][name]
                check(name+"_force", abs(D(group["constraint_force"])-sign*Fref), force_bound)
                check(name+"_hp_group_force", abs(D(group["constraint_force"])-hp["group_reactions_decimal"][name]), side_bound)
                check(name+"_virtual_work", abs(D(group["virtual_work_generalized_force"])-sign*Fref), side_bound)
                check(name+"_action_reaction", abs(D(group["model_force"])+D(group["constraint_force"])), side_bound)
            check("uniform_HuHu", norm(hp["regularization_internal_decimal"]), Decimal(c["uniform_HuHu_force_absolute_over_EA"])*EA)
            cross = None
            if r["d"] == spec["targets_mm"][-1]:
                hp80 = evaluate_prescribed_state(model, a["u"], r["d"], m["base"], m["direction"], groups,
                                                meta["force_scale_per_length"], precision=spec["crosscheck_precision_digits"])
                diff = norm([x-y for x,y in zip(hp["internal_decimal"], hp80["internal_decimal"])])/sf
                check("precision_50_80", diff, Decimal(c["precision_crosscheck_relative"]))
                write_json(output/f"hp80_{entry['index']:04d}.json", hp80)
                cross = str(diff)
            if d <= D(mc["preclosure_max_d_mm"]):
                phase = "preclosure"
                check("preclosure_leak_force", abs(force)/EA, Decimal(mc["preclosure_force_over_EA"]), "model")
                check("preclosure_gap_error", abs(gap-Ghard)/g0, Decimal(mc["preclosure_gap_error_over_g0"]), "model")
            elif d == g0:
                phase = "nominal_closure"
                check("closure_force", abs(force)/EA, Decimal(mc["closure_force_over_EA"]), "model")
                check("closure_gap", abs(gap)/g0, Decimal(mc["closure_gap_over_g0"]), "model")
            elif d >= D(mc["postclosure_min_d_mm"]):
                phase = "postclosure"
                check("postclosure_force", abs(force-Fhard)/abs(Fhard), Decimal(mc["postclosure_force_relative_hard"]), "model")
                check("postclosure_gap", abs(gap)/g0, Decimal(mc["postclosure_gap_over_g0"]), "model")
            else:
                phase = "bisection_transition_model_measurement_only"
            row = dict(index=entry["index"], d=r["d"], phase=phase,
                       force_N=str(force), gap_mm=str(gap), finite_force_N=str(Fref), finite_gap_mm=str(Gref),
                       hard_force_N=str(Fhard), hard_gap_mm=str(Ghard), minimum_J=str(hp["minimum_J_decimal"]),
                       force_scale_N=str(sf), hp_relative_residual=str(hp["relative_residual_decimal"]),
                       crosscheck_relative=cross, checks=checks,
                       numerical_status="pass" if all(q["status"]=="pass" for q in checks if q["kind"]=="numerical") else "not_pass",
                       model_status=("measurement_only" if not any(q["kind"]=="model" for q in checks) else
                                     "pass" if all(q["status"]=="pass" for q in checks if q["kind"]=="model") else "not_pass"))
            row["status"] = "pass" if row["numerical_status"] == "pass" and row["model_status"] in ("pass", "measurement_only") else "not_pass"
        write_json(output/f"hp50_{entry['index']:04d}.json", hp)
        write_json(output/f"reference_{entry['index']:04d}.json", ref)
        write_json(state_path, row)
        committed = [state_path, output/f"hp50_{entry['index']:04d}.json", output/f"reference_{entry['index']:04d}.json"]
        if cross is not None:
            committed.append(output/f"hp80_{entry['index']:04d}.json")
        write_json(commit_path, {p.name:sha(p) for p in committed})
        rows.append(row)
        write_json(output/"summary.json", dict(status="incomplete", states_completed=len(rows), rows=rows))
        print({"state":entry["index"], "d":r["d"], "status":row["status"]}, flush=True)
        if row["status"] != "pass":
            break
    result = read_json(run/"result.json")
    complete = len(rows)==len(entries) and result["status"]=="success"
    summary = dict(schema_version="hf4-normal-audit-1.0", created_utc=timestamp(),
                   status="pass" if complete and all(r["status"]=="pass" for r in rows) else "not_pass",
                   states_completed=len(rows), accepted_count=len(entries), production_status=result["status"], rows=rows,
                   source_run=str(run), scope="uniform normal task only; no nonuniform or cylinder validation")
    write_json(output/"summary.json", summary)
    return summary


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--spec", type=Path, required=True)
    p.add_argument("--source-freeze", type=Path, required=True)
    a = p.parse_args()
    summary = audit(a.run, a.output, a.spec, a.source_freeze)
    raise SystemExit(0 if summary["status"] == "pass" else 2)
