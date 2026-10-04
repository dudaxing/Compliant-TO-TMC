"""Read saved native Q1 states and measure regions; no mechanics evaluation.

--repo names the hf_repo directory. Output is exclusive and preserves partial
records on the first invalid quad/error. Mechanical zero counts derive from
the pinned pure import closure, not from instrumentation of mechanical calls.
"""
from __future__ import annotations

import argparse
import ast
from hashlib import sha256
import json
from pathlib import Path
import sys
from time import perf_counter

STARTED = perf_counter()
import numpy as np


def file_sha(path):
    return sha256(path.read_bytes()).hexdigest()


def canonical(value):
    if isinstance(value, dict):
        return {key: canonical(item) for key, item in value.items()}
    if isinstance(value, list):
        return [canonical(item) for item in value]
    if isinstance(value, float):
        if not np.isfinite(value):
            raise ValueError("Non-finite descriptor number")
        return (0.0 if value == 0.0 else value).hex()
    return value


def descriptor_sha(value):
    value = {key: item for key, item in value.items() if key != "descriptor_sha256"}
    return sha256(json.dumps(canonical(value), sort_keys=True, separators=(",", ":"),
                            ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def pure_sources(repo):
    """Inspect the complete allowed hf_eval import closure before importing it."""
    package = repo / "src/hf_eval"
    files = {"src/hf_eval/__init__.py": package / "__init__.py"}
    pending = ["native_region_geometry"]
    allowed = {"native_region_geometry", "boundary_geometry"}
    while pending:
        name = pending.pop()
        key = f"src/hf_eval/{name}.py"
        if key in files:
            continue
        path = package / f"{name}.py"
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                if any(item.name.split(".")[0] not in {"numpy"} | sys.stdlib_module_names for item in node.names):
                    raise ValueError("Unexpected import in pure geometry closure")
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    if node.level != 1 or node.module not in allowed:
                        raise ValueError("Unexpected hf_eval dependency in pure geometry closure")
                    pending.append(node.module)
                elif (node.module or "").split(".")[0] not in {"numpy", "__future__"} | sys.stdlib_module_names:
                    raise ValueError("Unexpected import in pure geometry closure")
        files[key] = path
    # Package init has an unused legacy evaluate() with a lazy import. No
    # module-level imports/expressions may execute that legacy path here.
    init = ast.parse(files["src/hf_eval/__init__.py"].read_text(encoding="utf-8"))
    if any(not isinstance(node, (ast.Expr, ast.Assign, ast.FunctionDef)) for node in init.body):
        raise ValueError("Unexpected package-init execution structure")
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True, help="hf_repo directory containing src/hf_eval")
    parser.add_argument("--input", type=Path, required=True, help="Saved result directory or result.json")
    parser.add_argument("--output", type=Path, required=True, help="New exclusive output directory")
    parser.add_argument("--boundary-comparison", type=Path, help="Optional saved unsigned boundary JSON/directory")
    parser.add_argument("--time-limit", type=float, default=120.0, help="Cooperative helper seconds including imports")
    parser.add_argument("--stop-file", type=Path, help="Optional outer launcher's cooperative stop flag")
    args = parser.parse_args()
    if not np.isfinite(args.time_limit) or args.time_limit <= 0:
        parser.error("--time-limit must be positive and finite")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    result_file = args.input.resolve()
    result_file = result_file if result_file.is_file() else result_file / "result.json"
    directory = result_file.parent
    pins, input_pins, sources, rows = {}, {}, {}, []
    started = completed = 0
    failure = None
    current_index = None
    result = None
    comparison = None
    loaded_modules = []
    current_identity = None
    closure = {}
    mechanical_scope_verified = False

    def checkpoint():
        if perf_counter() - STARTED > args.time_limit:
            raise RuntimeError("Geometry helper time limit exceeded")
        if args.stop_file is not None and args.stop_file.exists():
            raise RuntimeError("Outer launcher requested stop")

    def bind(path, expected=None, *, role=None):
        path = path.resolve()
        value = file_sha(path)
        if expected is not None and value != expected:
            raise ValueError("Saved identity differs: " + path.name)
        pins[path] = value
        if role is not None:
            input_pins[role] = value
        return value

    def read(path, expected=None, *, role=None):
        bind(path, expected, role=role)
        return json.loads(path.read_text(encoding="utf-8"))

    def archive(path, declaration, role):
        bind(path, declaration["sha256"], role=role)
        with np.load(path, allow_pickle=False) as saved:
            if set(saved.files) != set(declaration["fields"]):
                raise ValueError("Saved NPZ field set differs: " + role)
            arrays = {name: saved[name].copy() for name in saved.files}
        for name, value in arrays.items():
            actual = dict(dtype=str(value.dtype), shape=list(value.shape),
                          sha256=sha256(value.tobytes(order="C")).hexdigest())
            if actual != declaration["fields"][name]:
                raise ValueError("Saved NPZ field identity differs: " + role + "/" + name)
        return arrays

    def module_check():
        actual = sorted(name for name in sys.modules if name == "hf_eval" or name.startswith("hf_eval."))
        if set(actual) - {"hf_eval", "hf_eval.native_region_geometry", "hf_eval.boundary_geometry"}:
            raise ValueError("A non-geometry hf_eval module was imported")
        for name in actual:
            role = "src/hf_eval/" + ("__init__.py" if name == "hf_eval" else name.split(".")[-1] + ".py")
            if Path(sys.modules[name].__file__).resolve() != closure[role].resolve():
                raise ValueError("Imported geometry source differs from --repo")
        return actual

    try:
        checkpoint()
        closure = pure_sources(args.repo.resolve())
        closure["scripts/measure_native_workpiece_regions.py"] = Path(__file__).resolve()
        (output / "sources").mkdir()
        for role, path in closure.items():
            value = bind(path)
            snapshot = output / "sources" / path.name
            snapshot.write_bytes(path.read_bytes())
            if file_sha(snapshot) != value:
                raise ValueError("Source snapshot identity differs")
            sources[role] = dict(sha256=value, snapshot_path=snapshot.relative_to(output).as_posix())
        sys.path.insert(0, str(args.repo.resolve() / "src"))
        from hf_eval.native_region_geometry import measure_native_workpiece_regions
        loaded_modules = module_check()
        result = read(result_file, role="input/result.json")
        if descriptor_sha(result) != result["descriptor_sha256"]:
            raise ValueError("Result semantic descriptor SHA differs")
        model_file = directory / result["model"]["descriptor_path"]
        metadata = read(model_file, result["model"]["descriptor_file_sha256"], role="input/" + model_file.relative_to(directory).as_posix())
        if (descriptor_sha(metadata) != metadata["descriptor_sha256"] or
                metadata["descriptor_sha256"] != result["model"]["descriptor_sha256"] or
                metadata["task_sha256"] != result["task_sha256"] or
                descriptor_sha(metadata["task"]) != metadata["task_sha256"] or
                metadata["arrays"]["sha256"] != result["model"]["arrays_sha256"]):
            raise ValueError("Saved model/result semantic bindings differ")
        model_file_npz = model_file.parent / metadata["arrays"]["path"]
        model = archive(model_file_npz, metadata["arrays"], "input/" + model_file_npz.relative_to(directory).as_posix())
        if len(model) != 27:
            raise ValueError("Expected the saved fixed-workpiece model's 27 arrays")
        if result["accepted_states"] != len(result["states"]):
            raise ValueError("Accepted-state count differs from the saved path")
        if args.boundary_comparison is not None:
            comparison_file = args.boundary_comparison.resolve()
            if comparison_file.is_dir():
                comparison_file /= "boundary_measurements.json"
            comparison = read(comparison_file, role="comparison/boundary_measurements.json")
            if (comparison["schema_version"] != "native-workpiece-boundary-path-1.0" or
                    comparison["task_sha256"] != result["task_sha256"] or
                    len(comparison["accepted_states"]) != len(result["states"])):
                raise ValueError("Unsigned comparison path identity differs")
            for index, (old, record) in enumerate(zip(comparison["accepted_states"], result["states"])):
                expected = dict(accepted_index=index, original_target_index=record["original_target_index"],
                                d_mm=record["d"], leg=record["leg"], state_sha256=record["state_sha256"])
                if any(old[key] != value for key, value in expected.items()):
                    raise ValueError("Unsigned comparison accepted-state identity differs")
            (output / "boundary_comparison.json").write_bytes(comparison_file.read_bytes())
        for index, record in enumerate(result["states"]):
            current_index = index
            current_identity = dict(accepted_index=index, original_target_index=record["original_target_index"],
                                    d_mm=record["d"], leg=record["leg"], state_sha256=record["state_sha256"])
            checkpoint()
            state_json_file = directory / record["descriptor_path"]
            saved_record = read(state_json_file, record["descriptor_file_sha256"], role="input/" + record["descriptor_path"])
            expected_record = {key: value for key, value in record.items() if key not in ("descriptor_path", "descriptor_file_sha256")}
            if saved_record != expected_record or descriptor_sha(saved_record) != saved_record["descriptor_sha256"]:
                raise ValueError("Accepted-state descriptor differs")
            state = archive(directory / record["state"]["path"], record["state"], "input/" + record["state"]["path"])
            if set(state) != {"lift", "fluctuation"} or state["lift"].shape != state["fluctuation"].shape or state["lift"].ndim != 1:
                raise ValueError("Expected two saved split-displacement vectors")
            digest = sha256(b"split_displacement_v1")
            digest.update(np.asarray([state["lift"].size], dtype="<i8").tobytes())
            for name in ("lift", "fluctuation"):
                digest.update(np.asarray(state[name], dtype="<f8").tobytes(order="C"))
            if digest.hexdigest() != record["state_sha256"]:
                raise ValueError("Accepted split-state SHA differs")
            row = current_identity.copy()
            if comparison is not None:
                old = comparison["accepted_states"][index]
                row["boundary_comparison"] = dict(scope="Previously saved unsigned distances; not remeasured or renamed as normal gaps",
                    groups={name: {key: group[key] for key in ("minimum_boundary_distance_mm", "closest_pair", "intersects", "roundoff_near_touch", "containment_tested")}
                            for name, group in old["geometry"]["groups"].items()})
            started += 1
            geometry = measure_native_workpiece_regions(model, metadata, state["lift"], state["fluctuation"])
            completed += 1
            row["geometry"] = geometry
            rows.append(row)
            loaded_modules = module_check()
            if geometry["geometry_valid"] is not True:
                raise ValueError("Invalid saved quad/body geometry; full region/face results not evaluated")
            checkpoint()
    except (OSError, ValueError, RuntimeError, KeyError, TypeError, IndexError) as error:
        failure = dict(type=type(error).__name__, message=str(error), accepted_index=current_index,
                       state_identity=current_identity)
    try:
        if closure:
            loaded_modules = module_check()
            mechanical_scope_verified = "hf_eval.native_region_geometry" in loaded_modules
        unchanged = all(file_sha(path) == value for path, value in pins.items())
        if not unchanged:
            raise ValueError("Input/source changed during measurement")
        checkpoint()
    except (OSError, ValueError, RuntimeError) as error:
        unchanged = False if isinstance(error, (OSError, ValueError)) else unchanged
        if failure is None:
            failure = dict(type=type(error).__name__, message=str(error), accepted_index=current_index,
                           state_identity=current_identity)
    report = dict(schema_version="native-workpiece-region-path-1.0", status="failed" if failure else "pass",
        production_status=None if result is None else result["status"], task_sha256=None if result is None else result["task_sha256"],
        declared_accepted_states=None if result is None else len(result["states"]), accepted_states=rows,
        geometry_calls_started=started, geometry_calls_completed=completed, failure=failure,
        input_files_sha256=input_pins, sources=sources, inputs_and_sources_unchanged=unchanged,
        loaded_hf_eval_modules=loaded_modules, mechanical_call_count_basis="Pinned inspected pure import closure and loaded hf_eval-module exclusion; no mechanical hooks were invoked or monitored",
        mechanical_hooks_monitored=False, mechanical_scope_verified=mechanical_scope_verified,
        force_calls=0 if mechanical_scope_verified else None, tangent_calls=0 if mechanical_scope_verified else None,
        solver_calls=0 if mechanical_scope_verified else None, HP_calls=0 if mechanical_scope_verified else None,
        consumer_calls=0 if mechanical_scope_verified else None,
        boundary_comparison=None if comparison is None else dict(path="boundary_comparison.json", sha256=input_pins["comparison/boundary_measurements.json"]),
        elapsed_seconds=perf_counter() - STARTED, helper_seconds_limit=args.time_limit,
        scope="Saved Q1 cell-union interior overlap and finite square outward first-ray diagnostics only; no complete set containment or mechanics/contact/clamping/pressure qualification")
    with (output / "regions_measurements.json").open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
    print(json.dumps(dict(status=report["status"], geometry_calls_started=started,
                         geometry_calls_completed=completed, saved_states=len(rows), output=str(output))))
    return 1 if failure else 0


if __name__ == "__main__":
    raise SystemExit(main())
