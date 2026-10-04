"""Resumable independent HP audit of saved HF-3 project states; never solves.

Use repeated --run arguments for completed public-wrapper directories. A new
output binds all inputs, the frozen spec, this script and both HP helpers.
--resume requires those exact content hashes again (paths may be relocated).
--max-states limits newly completed state audits in this invocation. Each
reference and state decision is atomically committed, so a process deadline
loses at most an in-flight evaluation. The caller enforces the shared 600-second
HP bucket and <=300-second process limit; this script does not run a monitor.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from time import perf_counter

import numpy as np


SCHEMA = "hf3-saved-state-audit-1.0"
SPEC_VALUES = {
    "internal_relative_force_tolerance": "1e-9", "external_relative_force_tolerance": "1e-8",
    "force_evaluation_relative_budget": "1e-9", "constraint_relative_tolerance": "1e-10",
    "displacement_scale_floor_mm": "1e-6", "force_scale_floor_factor": "1e-8",
    "precision_layer_tolerance": "1e-30", "force_balance_relative_tolerance": "1e-6",
    "fixed_displacement_tolerance_mm": "8e-11",
}
UNITS = {"length": "mm", "force": "N", "stress": "MPa", "energy": "N mm"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def plain(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, np.ndarray):
        return plain(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [plain(v) for v in value]
    return value


def content_hash(value):
    encoded = json.dumps(plain(value), sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path, value):
    path = Path(path)
    temporary = path.with_name(path.name+".tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            json.dump(plain(value), stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def read_npz(path):
    with np.load(path, allow_pickle=False) as archive:
        arrays = {name: archive[name] for name in archive.files}
    require(all(a.dtype.kind in "biuf" and np.all(np.isfinite(a)) for a in arrays.values()),
            f"Nonfinite, object or non-real array in {path}")
    return arrays


def contained(root, relative):
    require(isinstance(relative, str) and relative and not Path(relative).is_absolute(), "artifact paths must be relative")
    result = (root/relative).resolve()
    require(result.is_relative_to(root.resolve()), "artifact path leaves its run directory")
    return result


def norm(values):
    return sum((x*x for x in values), Decimal(0)).sqrt()


def D(value):
    return Decimal.from_float(float(value))


def load_reference():
    path = Path(__file__).with_name("hf3_precision_reference.py")
    spec = importlib.util.spec_from_file_location("hf3_reference_for_state_audit", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.evaluate_project_state


def validate_spec(path):
    spec = read_json(path)
    require(spec["schema_version"] == "hf3-validation-1.0", "unsupported HF3 validation schema")
    require(spec["precision_digits"] == 50 and spec["crosscheck_precision_digits"] == 80,
            "precision layers must remain 50 and 80 digits")
    for key, expected in SPEC_VALUES.items():
        require(Decimal(str(spec[key])) == Decimal(expected), f"frozen HF3 criterion differs: {key}")
    require(spec["resource_limits"]["category_seconds"]["hp"] == 600 and
            spec["resource_limits"]["small_process_seconds"] == 300,
            "HF3 HP resource declarations differ from this auditor's intended scope")
    return spec


def prepare_run(path, index, spec):
    root = Path(path).resolve()
    model = read_npz(root/"model.npz")
    meta, result = read_json(root/"metadata.json"), read_json(root/"result.json")
    require(meta["schema_version"] == result["schema_version"] == "hf-project-result-1.0", "expected public project output")
    require(meta["units"] == result["units"] == UNITS, "project units differ from HF3")
    identity_fields = ("evaluation_id", "geometry_id", "geometry_descriptor_sha256", "task_sha256", "solver_sha256", "implementation")
    require(all(meta[k] == result[k] for k in identity_fields), "metadata/result identity mismatch")
    require(meta["task_config"].get("diagnostic_variant", "none") == "none", "initial-tangent boundary variant is not a nonlinear path")
    settings = result["effective_settings"]
    for name, key in (("tolerance", "internal_relative_force_tolerance"), ("constraint_tolerance", "constraint_relative_tolerance"),
                      ("displacement_scale_floor", "displacement_scale_floor_mm"), ("force_scale_floor_factor", "force_scale_floor_factor")):
        require(Decimal(str(settings[name])) == Decimal(str(spec[key])), f"production setting differs: {name}")
    E = meta["material"]["E_MPa"]
    require(E == meta["task_config"]["material"]["E_MPa"] and np.isfinite(E) and E > 0, "material E mismatch")
    require(float(model["thickness"]) == meta["material"]["thickness_mm"], "actual thickness differs from metadata")
    require(float(model["k_out"]) == meta["task_config"]["output"]["spring_N_per_mm"], "spring metadata mismatch")
    index_data = read_json(root/"steps/index.json")
    steps = index_data["steps"]
    require(index_data["accepted_step_count"] == len(steps) == result["path"]["accepted_step_count"], "accepted counts/index disagree")
    require(len(result["path"]["accepted_steps"]) == len(steps), "scalar state count differs")
    state_inputs = []
    files = {name: sha256(root/name) for name in ("model.npz", "metadata.json", "result.json", "steps/index.json")}
    last_d = -1.0
    original_levels = []
    for position, entry in enumerate(steps):
        require(entry["state_index"] == position, "step indices must form a complete ordered sequence")
        scalar_path, array_path = contained(root, entry["metadata_file"]), contained(root, entry["arrays_file"])
        scalar = read_json(scalar_path)
        digest = sha256(array_path)
        require(digest == entry["arrays_sha256"] == scalar["arrays_sha256"], "step NPZ checksum mismatch")
        require(scalar["arrays_file"] == entry["arrays_file"], "step scalar points to another array file")
        brief = {k: v for k, v in scalar.items() if k not in ("arrays_file", "arrays_sha256")}
        require(brief == result["path"]["accepted_steps"][position], "step scalar/result history disagreement")
        require(scalar["d"] == entry["d_mm"] and scalar["d"] > last_d, "invalid state displacement order")
        last_d = scalar["d"]
        require(type(scalar["is_original_target"]) is bool and
                scalar["is_original_target"] == (scalar["d"] == scalar["original_target_displacement"]) and
                scalar["original_target_displacement"] in model["targets_mm"], "invalid substep/original-target identity")
        if scalar["is_original_target"]:
            original_levels.append(scalar["d"])
        for artifact in (scalar_path, array_path):
            files[artifact.relative_to(root).as_posix()] = sha256(artifact)
        state_inputs.append(dict(state_index=position, d_mm=scalar["d"], R_input=scalar["R_input"],
            is_original_target=scalar["is_original_target"], original_target_displacement=scalar["original_target_displacement"],
            scalar_file=scalar_path.relative_to(root).as_posix(), arrays_file=array_path.relative_to(root).as_posix(),
            scalar_sha256=sha256(scalar_path), arrays_sha256=digest))
    complete = (result["numerics"]["status"] == "success" and result["numerics"]["target_reached"] is True and
                np.array_equal(original_levels, model["targets_mm"]))
    binding = dict(run_key=f"run_{index:03d}", **{k: meta[k] for k in identity_fields},
        input_files=files, states=state_inputs, original_production_numerics=result["numerics"],
        production_original_targets_complete=bool(complete), qualification=result["qualification"],
        functionality=result["functionality"], E_MPa=E)
    return dict(root=root, model=model, metadata=meta, result=result, binding=binding, states=state_inputs)


def decode_decimal(value):
    if isinstance(value, str):
        number = Decimal(value)
        require(number.is_finite(), "cached Decimal must be finite")
        return number
    if isinstance(value, list):
        return [decode_decimal(x) for x in value]
    if isinstance(value, dict):
        return {k: decode_decimal(v) for k, v in value.items()}
    return value


def reference_cache(path, inputs, digits, compute):
    """A complete reference may survive interruption before final state commit."""
    if path.exists():
        cached = read_json(path)
        require(cached["binding"] == inputs and cached["precision_digits"] == digits and cached["status"] == "computed",
                "cached reference input/implementation identity differs")
        require(content_hash(cached["reference"]) == cached["reference_sha256"], "cached reference checksum mismatch")
        data = cached["reference"]
        return {k: decode_decimal(v) if k.endswith("_decimal") else v for k, v in data.items()}, True
    hp = compute(digits)
    keep = {k: v for k, v in hp.items() if k.endswith("_decimal") or k in ("precision_digits", "fixed_dofs", "free_dofs", "positive_J")}
    write_json(path, dict(schema_version=SCHEMA, status="computed", binding=inputs, precision_digits=digits,
                         reference=keep, reference_sha256=content_hash(keep)))
    return keep, False


def force_errors(actual, hp, scale, free):
    actual = np.asarray(actual)
    require(actual.ndim == 1 and len(actual) == len(hp), "production/reference force shapes differ")
    with localcontext() as context:
        context.prec = 100
        difference = [D(a)-b for a, b in zip(actual, hp)]
        return {"full_relative_error_decimal": norm(difference)/scale,
                "free_relative_error_decimal": norm([difference[i] for i in free])/scale}


def compare_layers(lower, higher):
    free = higher["free_dofs"]
    with localcontext() as context:
        context.prec = 100
        difference = [a-b for a, b in zip(lower["internal_decimal"], higher["internal_decimal"])]
        residual_difference = [a-b for a, b in zip(lower["residual_decimal"], higher["residual_decimal"])]
        scale = higher["force_scale_decimal"]
        return dict(full_relative_error_decimal=norm(difference)/scale,
            free_relative_error_decimal=norm([difference[i] for i in free])/scale,
            augmented_force_free_relative_difference_decimal=norm([residual_difference[i] for i in free])/scale,
            mean_constraint_relative_difference_decimal=abs(lower["constraint_decimal"]-higher["constraint_decimal"])/higher["d_scale_decimal"])


def audit_one(run, state, output, spec, binding_sha, cross80, evaluate):
    started = perf_counter()
    directory = output/run["binding"]["run_key"]
    directory.mkdir(exist_ok=True)
    name = f"state_{state['state_index']+1:04d}"
    inputs = dict(audit_binding_sha256=binding_sha, state=state, run_key=run["binding"]["run_key"])
    source = read_npz(contained(run["root"], state["arrays_file"]))
    scalar = read_json(contained(run["root"], state["scalar_file"]))
    model = run["model"]
    require(source["d"].shape == source["R_input"].shape == () and
            float(source["d"]) == state["d_mm"] and float(source["R_input"]) == state["R_input"] and
            bool(source["is_original_target"]) == state["is_original_target"], "state scalar/NPZ mismatch")
    def compute(digits):
        return evaluate(model, source["u"], float(source["R_input"]), float(source["d"]),
                        model["bin"], model["bout"], float(model["k_out"]), run["binding"]["E_MPa"],
                        float(model["thickness"]), precision=digits)
    record = dict(schema_version=SCHEMA, status="complete", binding=inputs, source_index=state["state_index"],
                  d_mm=state["d_mm"], checks={}, precision_crosscheck={"status": "not_requested"})
    try:
        reference50 = directory/(name+".reference50.json")
        hp, reused50 = reference_cache(reference50, inputs, 50, compute)
        error = force_errors(source["internal_force"], hp["internal_decimal"], hp["force_scale_decimal"], hp["free_dofs"])
        thresholds = {k: Decimal(str(v)) for k, v in spec.items() if k in SPEC_VALUES}
        with localcontext() as context:
            context.prec = 100
            checks = dict(
                independent_equilibrium=hp["relative_residual_decimal"] <= thresholds["external_relative_force_tolerance"],
                evaluation_full=error["full_relative_error_decimal"] <= thresholds["force_evaluation_relative_budget"],
                evaluation_free=error["free_relative_error_decimal"] <= thresholds["force_evaluation_relative_budget"],
                average_constraint=hp["constraint_error_decimal"] <= thresholds["constraint_relative_tolerance"]*hp["d_scale_decimal"],
                positive_J=hp["minimum_J_decimal"] > 0 and bool(np.all(source["J"] > 0)),
                fixed_displacement=hp["fixed_displacement_max_decimal"] <= thresholds["fixed_displacement_tolerance_mm"],
                global_force_balance=hp["relative_force_balance_decimal"] <= thresholds["force_balance_relative_tolerance"],
                production_internal_stopping=Decimal(str(scalar["relative_residual"])) <= thresholds["internal_relative_force_tolerance"])
            stored_support = [D(x) for x in source["support_reaction"]]
            balance = [sum((stored_support[i]+hp["external_decimal"][i] for i in range(c, len(stored_support), 2)), Decimal(0)) for c in (0, 1)]
            balance_scale = max(norm(stored_support)+norm(hp["input_force_decimal"])+norm(hp["spring_force_decimal"]), hp["force_scale_decimal"])
            stored_balance_relative = norm(balance)/balance_scale
            checks["stored_support_balance"] = stored_balance_relative <= thresholds["force_balance_relative_tolerance"]
            checks["support_zero_on_free_dofs"] = all(source["support_reaction"][i] == 0 for i in hp["free_dofs"])
            diagnostics = dict(stored_support_balance_relative_decimal=stored_balance_relative,
                stored_q_in_error_over_dscale_decimal=abs(D(scalar["q_in"])-hp["q_in_decimal"])/hp["d_scale_decimal"],
                stored_q_out_error_over_dscale_decimal=abs(D(scalar["q_out"])-hp["q_out_decimal"])/hp["d_scale_decimal"])
        record.update(checks={k: bool(v) for k, v in checks.items()}, evaluation_error=error, diagnostics=diagnostics,
            reference50_file=reference50.relative_to(output).as_posix(), reference50_sha256=sha256(reference50),
            reference50_cache_reused=reused50,
            metrics={k: hp[k] for k in ("relative_residual_decimal", "constraint_error_decimal", "d_scale_decimal",
                "force_scale_decimal", "force_scale_components_decimal", "minimum_J_decimal", "minimum_J_solid_decimal",
                "minimum_J_medium_decimal", "fixed_displacement_max_decimal", "relative_force_balance_decimal",
                "solid_material_energy_decimal", "medium_material_energy_decimal", "q_in_decimal", "q_out_decimal")})
        if cross80 and state["state_index"] == len(run["states"])-1:
            reference80 = directory/(name+".reference80.json")
            higher, reused80 = reference_cache(reference80, inputs, 80, compute)
            comparison = compare_layers(hp, higher)
            passed = max(comparison["full_relative_error_decimal"], comparison["free_relative_error_decimal"]) <= thresholds["precision_layer_tolerance"]
            record["precision_crosscheck"] = dict(status="pass" if passed else "fail", digits=[50, 80],
                tolerance_decimal=thresholds["precision_layer_tolerance"], reference80_file=reference80.relative_to(output).as_posix(),
                reference80_sha256=sha256(reference80), reference80_cache_reused=reused80, **comparison)
            record["checks"]["precision_50_vs_80"] = bool(passed)
        record["numerical_status"] = "pass" if all(record["checks"].values()) else "fail"
    except (ValueError, OSError, KeyError, TypeError, RuntimeError, ArithmeticError) as error:
        record.update(numerical_status="fail", exception_type=type(error).__name__, exception=str(error))
    record["wall_seconds"] = perf_counter()-started
    record["decision_sha256"] = content_hash(record)
    write_json(directory/(name+".json"), record)
    return plain(record)


def load_completed(path, expected_binding, output):
    state = read_json(path)
    require(state["decision_sha256"] == content_hash({k: v for k, v in state.items() if k != "decision_sha256"}),
            "completed state decision checksum mismatch")
    require(state["status"] == "complete" and state["binding"] == expected_binding, "completed state belongs to different inputs")
    require(state["numerical_status"] in ("pass", "fail"), "invalid completed state decision")
    for prefix in ("reference50",):
        if prefix+"_file" in state:
            require(sha256(contained(output, state[prefix+"_file"])) == state[prefix+"_sha256"], "completed reference checksum mismatch")
    cross = state["precision_crosscheck"]
    if "reference80_file" in cross:
        require(sha256(contained(output, cross["reference80_file"])) == cross["reference80_sha256"], "completed 80-digit reference checksum mismatch")
    if state["numerical_status"] == "pass":
        require(state["checks"] and all(v is True for v in state["checks"].values()), "cached pass contradicts saved checks")
    return state


def summarize(runs, completed, output, binding_sha, invocation, *, reason):
    run_rows = []
    expected_total = sum(len(run["states"]) for run in runs)
    all_records = []
    for run in runs:
        key = run["binding"]["run_key"]
        records = [completed[(key, s["state_index"])] for s in run["states"] if (key, s["state_index"]) in completed]
        all_records.extend(records)
        complete = len(records) == len(run["states"])
        passed = complete and all(r["numerical_status"] == "pass" for r in records)
        run_rows.append(dict(run_key=key, evaluation_id=run["binding"]["evaluation_id"],
            geometry_id=run["binding"]["geometry_id"], task_sha256=run["binding"]["task_sha256"],
            expected_states=len(run["states"]), completed_states=len(records), audit_coverage_complete=complete,
            accepted_state_audit_status="pass" if passed else "fail" if any(r["numerical_status"] == "fail" for r in records) else "incomplete",
            original_production_numerics=run["binding"]["original_production_numerics"],
            original_targets_complete=run["binding"]["production_original_targets_complete"],
            failures=[dict(source_index=r["source_index"], d_mm=r["d_mm"], checks=r["checks"], exception=r.get("exception")) for r in records if r["numerical_status"] != "pass"],
            qualification={"status": "not_evaluated", "recorded_production_status": run["binding"]["qualification"]},
            functionality={"status": "not_evaluated", "recorded_production_status": run["binding"]["functionality"]}))
    coverage = len(all_records) == expected_total
    failed = any(r["numerical_status"] != "pass" for r in all_records)
    original_complete = all(run["binding"]["production_original_targets_complete"] for run in runs)
    numerical_status = "not_pass" if failed or (coverage and not original_complete) else "pass" if coverage else "incomplete"
    maxima = {}
    for name, container in (("relative_residual_decimal", "metrics"), ("full_relative_error_decimal", "evaluation_error"),
                            ("free_relative_error_decimal", "evaluation_error"), ("relative_force_balance_decimal", "metrics")):
        values = [Decimal(r[container][name]) for r in all_records if container in r and name in r[container]]
        maxima[name] = str(max(values)) if values else None
    summary = dict(schema_version=SCHEMA, binding_sha256=binding_sha, status=numerical_status,
        numerics={"status": numerical_status, "all_saved_states_covered": coverage, "all_requested_paths_complete": original_complete},
        qualification={"status": "not_evaluated"}, functionality={"status": "not_evaluated"},
        expected_states=expected_total, completed_states=len(all_records), failed_states=sum(r["numerical_status"] != "pass" for r in all_records),
        scope="Independent arithmetic/equilibrium audit of these saved states only; no functionality, contact, stability or stage-wide approval",
        runs=run_rows, maxima=maxima, last_invocation=invocation, progress_reason=reason,
        committed_states=[dict(run_key=key, source_index=index,
            decision_file=f"{key}/state_{index+1:04d}.json",
            decision_file_sha256=sha256(output/key/f"state_{index+1:04d}.json")) for key, index in completed],
        completion_policy="All actual accepted substeps are included; a partial batch is never a complete PASS",
        budget_policy="External shared monitor: HP cumulative <=600s, each process <=300s; failures and resume work count")
    write_json(output/"summary.json", summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--run", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--max-states", type=int)
    parser.add_argument("--cross80", action="store_true")
    args = parser.parse_args()
    if args.max_states is not None and args.max_states < 1:
        parser.error("--max-states must be positive")
    started = perf_counter()
    completed = {}
    new_count = 0
    try:
        spec = validate_spec(args.spec)
        runs = [prepare_run(path, index, spec) for index, path in enumerate(args.run, 1)]
        require(len({r["binding"]["evaluation_id"] for r in runs}) == len(runs), "duplicate run evaluation_id")
        script_paths = [Path(__file__), Path(__file__).with_name("hf3_precision_reference.py"), Path(__file__).with_name("hf2_precision_reference.py")]
        binding = dict(schema_version=SCHEMA, spec_sha256=sha256(args.spec),
            implementation_sha256={p.name: sha256(p) for p in script_paths}, cross80=args.cross80,
            runs=[run["binding"] for run in runs])
        binding_sha = content_hash(binding)
        if args.resume:
            require(args.output.is_dir(), "--resume requires an existing audit output")
            require(read_json(args.output/"binding.json")["binding"] == binding, "resume input/spec/implementation hashes differ")
            require(sha256(args.output/"validation_spec_used.json") == binding["spec_sha256"], "copied frozen spec changed")
        else:
            args.output.mkdir(parents=True, exist_ok=False)
            write_json(args.output/"binding.json", dict(binding=binding, binding_sha256=binding_sha,
                origin_paths_record_only=[str(p.resolve()) for p in args.run]))
            (args.output/"validation_spec_used.json").write_bytes(args.spec.read_bytes())
        invocation_directory = args.output/"invocations"
        invocation_directory.mkdir(exist_ok=True)
        invocation_number = len(list(invocation_directory.glob("*.json")))+1
        invocation = dict(number=invocation_number, started_at_utc=datetime.now(timezone.utc).isoformat(),
                          max_states=args.max_states, resumed=args.resume, newly_completed_states=0)
        for run in runs:
            key = run["binding"]["run_key"]
            for state in run["states"]:
                path = args.output/key/f"state_{state['state_index']+1:04d}.json"
                if path.exists():
                    expected = dict(audit_binding_sha256=binding_sha, state=state, run_key=key)
                    completed[(key, state["state_index"])] = load_completed(path, expected, args.output)
        summarize(runs, completed, args.output, binding_sha, invocation, reason="running")
        evaluate = load_reference()
        for run in runs:
            key = run["binding"]["run_key"]
            for state in run["states"]:
                state_key = (key, state["state_index"])
                if state_key in completed:
                    continue
                if args.max_states is not None and new_count >= args.max_states:
                    break
                completed[state_key] = audit_one(run, state, args.output, spec, binding_sha, args.cross80, evaluate)
                new_count += 1
                invocation.update(newly_completed_states=new_count, wall_seconds=perf_counter()-started)
                write_json(invocation_directory/f"invocation_{invocation_number:04d}.json", invocation)
                summarize(runs, completed, args.output, binding_sha, invocation, reason="running")
                print(f"HF3 HP {key} state {state['state_index']+1}: {completed[state_key]['numerical_status']}; "
                      f"{len(completed)} total committed, {perf_counter()-started:.2f}s this invocation", flush=True)
            if args.max_states is not None and new_count >= args.max_states:
                break
        # Detect changed inputs/helpers even if an external process edits them
        # while this audit is running; historical paths are never rewritten.
        for run in runs:
            for name, digest in run["binding"]["input_files"].items():
                require(sha256(contained(run["root"], name)) == digest, "run input changed during audit")
        require(sha256(args.spec) == binding["spec_sha256"], "spec changed during audit")
        require(all(sha256(p) == binding["implementation_sha256"][p.name] for p in script_paths), "auditor/helper changed during audit")
        invocation.update(newly_completed_states=new_count, wall_seconds=perf_counter()-started, status="finished")
        write_json(invocation_directory/f"invocation_{invocation_number:04d}.json", invocation)
        summary = summarize(runs, completed, args.output, binding_sha, invocation,
                            reason="batch_limit" if len(completed) < sum(len(r["states"]) for r in runs) else "complete")
        print(json.dumps({k: summary[k] for k in ("status", "expected_states", "completed_states", "failed_states", "maxima")}, indent=2), flush=True)
        return 1 if summary["status"] == "not_pass" else 0
    except (ValueError, OSError, KeyError, TypeError, RuntimeError, ArithmeticError) as error:
        # An invalid resume never overwrites any existing binding, state or
        # summary. Completed state files remain the restart authority.
        failure = dict(schema_version=SCHEMA, status="incomplete", error_type=type(error).__name__,
                       reason=str(error), wall_seconds=perf_counter()-started, newly_completed_states=new_count)
        print(json.dumps(failure, indent=2), flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
