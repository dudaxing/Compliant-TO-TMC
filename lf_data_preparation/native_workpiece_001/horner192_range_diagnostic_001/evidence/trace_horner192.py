"""Trace isolated Horner192 on the same complete F16 input; no repair or qualification.

The first unsupported DD return is observed, not replaced. Its executed
branch may later be unselected. The original outer range exception must also
recur. Budget: cooperative 60 s / sampled 8 GiB, separate outer window 90 s;
neither this script nor that contract claims an OS hard limit or forced cleanup.
Run only after this new, independent diagnostic phase has been frozen.
"""
from __future__ import annotations

from time import perf_counter
STARTED = perf_counter()
from pathlib import Path
import argparse
import hashlib
import inspect
import json
import shutil
import sys
import traceback

SECONDS, RSS_LIMIT, OUTER_SECONDS = 60.0, 8 * 1024**3, 90.0
STAGE_REL = "lf_data_preparation/native_workpiece_001/coarse_square_cycle_003"
MODEL_REL = "lf_data_preparation/native_workpiece_001/models/gripper_coarse_square/model.npz"
OVERLAP = ("edofs", "coordinates", "connectivity", "lam", "mu", "kr", "hx", "hy",
           "thickness", "solid", "fixed_dofs", "grad", "hessian", "weights")
FIELDS = {*OVERLAP, "lift", "fluctuation"}
RUNTIME_REL = "lf_data_preparation/native_workpiece_001/horner192_candidate_001/runtime"
FAILED_REL = "lf_data_preparation/native_workpiece_001/horner192_requalification_001/check/candidate"
FAILED_STAGE_REL = "lf_data_preparation/native_workpiece_001/horner192_requalification_001"
CANDIDATE_SHA = "1d18a5512396649200de908cc5106c17d7c9a9f7c3fa62ba518cbe7d5659517e"
BASELINE_SHA = "7fff354270a276764445b45a281a5924fd9f0356236b89e0dbd4f00088b383ce"
ORIGIN_SHA = "4b5bfefe86624065b1c6c80bb91970a961798fea0ae79c31ee46e56cfdc2d3d0"
FAILED_RESULT_SHA = "658cff6edc8efb7334dcb74a20bc7c868eb5a516a36333b81cb53f8211e41ed7"
FAILED_FREEZE_SHA = "3e0ae71af1e8e8f5a784385e4e507caa3341ce6dff57a2558a9ee054bf5d7c2a"
FAILED_LAUNCH_SHA = "20cd13bd33baa0ecfbe8963868a31cb64f107258321225f2c4f5a8551a9fb4f2"
PARAMETERS = ("a", "b", "numerator", "denominator", "near", "selected", "small_products",
              "small_delta", "remainder", "power", "horner_scaled", "energy_scale", "inverse_energy_scale")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root, output = args.repo.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    report = dict(schema_version="horner192-force-range-primitive-diagnostic-1.0",
        status="running", qualification=False, force_started=0, force_completed=0,
        tangent_calls=0, solver_calls=0, HP_calls=0, JIT_calls=0, LF_imports=0,
        global_assembly_calls=0, raw_response=None, raw_response_returned=False, seconds_limit=SECONDS, outer_seconds=OUTER_SECONDS,
        sampled_RSS_limit_bytes=RSS_LIMIT,
        scope="Isolated1d18 first executed unsupported DD return on original full3200-cell F16 plus original outer range exception; no retry qualification",
        budget_mode="Cooperative checks and sampled process-tree RSS; no kill/force or OS hard cap",
        stop_policy="One original force call; first error stops; no repair, retries or changed support bounds")
    bindings, first_bad, peak = {}, None, 0
    first_arrays, originals = {}, {}
    ci = process = kernel = None
    write(output / "result.json", report)
    try:
        import numpy as np
        import psutil
        process = psutil.Process()
        next_sample = 0.0

        def checkpoint():
            nonlocal peak, next_sample
            now = perf_counter()
            if now - STARTED > SECONDS:
                raise RuntimeError("Diagnostic cooperative time limit exceeded")
            if now >= next_sample:
                members = [process, *process.children(recursive=True)]
                memory = 0
                for member in members:
                    try:
                        info = member.memory_info()
                        memory += max(info.rss, getattr(info, "peak_wset", info.rss))
                    except psutil.NoSuchProcess:
                        pass
                peak = max(peak, memory)
                next_sample = now + 0.1
                if peak > RSS_LIMIT:
                    raise RuntimeError("Diagnostic sampled process-tree memory limit exceeded")
                if (output / "stop_requested.txt").exists() or (output.parent / "stop_requested.txt").exists() or (root / STAGE_REL / "stop_requested.txt").exists():
                    raise RuntimeError("External observation requested diagnostic stop")

        checkpoint()
        stage = root / STAGE_REL
        inventory_file, freeze_file = stage / "input_inventory.json", stage / "source_freeze.json"
        observation_file = stage / "first_force_range_input/observation.json"
        input_file = stage / "first_force_range_input/input.npz"
        inventory = json.loads(inventory_file.read_text(encoding="utf-8"))
        observation = json.loads(observation_file.read_text(encoding="utf-8"))
        sources = json.loads(freeze_file.read_text(encoding="utf-8"))["sources"]
        assert len(sources) == 63 and len(inventory["input_bindings"]) == 25
        assert sha(freeze_file) == inventory["source_freeze_sha256"] == observation["source_freeze_sha256"]
        assert sha(inventory_file) == observation["input_inventory_sha256"]
        assert sha(input_file) == observation["input_npz_sha256"]
        assert observation["code"] == "unsupported_arithmetic_range"
        assert set(observation["fields"]) == FIELDS
        for relative, pin in sources.items():
            bindings[relative] = pin
            capsule = (stage / "sources" / Path(relative).name).relative_to(root).as_posix()
            bindings[capsule] = pin
        bindings.update(inventory["input_bindings"])
        for path in (inventory_file, freeze_file, observation_file, input_file):
            bindings[path.relative_to(root).as_posix()] = sha(path)
        assert MODEL_REL in bindings
        runtime = root / RUNTIME_REL
        origin_file = runtime.parent / "runtime_origin.json"
        assert sha(origin_file) == ORIGIN_SHA
        origin = json.loads(origin_file.read_text(encoding="utf-8"))
        assert origin["schema_version"] == "isolated-horner192-runtime-1.0"
        assert origin["source_count"] == len(origin["original_sources"]) == len(origin["candidate_sources"]) == 42
        assert origin["original_sources"]["hf_repo/src/hf_eval/split_kernel_invariants_hu.py"] == BASELINE_SHA
        assert origin["candidate_kernel_sha256"] == CANDIDATE_SHA
        bindings[origin_file.relative_to(root).as_posix()] = ORIGIN_SHA
        for relative, original_pin in origin["original_sources"].items():
            expected = CANDIDATE_SHA if relative == "hf_repo/src/hf_eval/split_kernel_invariants_hu.py" else original_pin
            assert origin["candidate_sources"][relative] == expected
            assert sha(root / relative) == original_pin
            bindings[(runtime / relative).relative_to(root).as_posix()] = expected
        failed_dir = root / FAILED_REL
        failed_file = failed_dir / "result.json"
        failed_freeze_file = root / FAILED_STAGE_REL / "source_freeze.json"
        failed_launch_file = root / FAILED_STAGE_REL / "candidate_launch.json"
        assert sha(failed_file) == FAILED_RESULT_SHA and sha(failed_freeze_file) == FAILED_FREEZE_SHA
        assert sha(failed_launch_file) == FAILED_LAUNCH_SHA
        failed = json.loads(failed_file.read_text(encoding="utf-8"))
        failed_freeze = json.loads(failed_freeze_file.read_text(encoding="utf-8"))
        assert failed["status"] == "fail" and failed["mode"] == "candidate"
        assert failed["kernel_source_sha256"] == CANDIDATE_SHA
        assert failed["call_counts"] == dict(force_started=1,force_completed=0,tangent_started=0,tangent_completed=0,
            HP_started=0,HP_completed=0,action_consumer_started=0,action_consumer_completed=0,solver_calls=0,JIT_calls=0)
        assert (failed["error"]["type"],failed["error"]["code"],failed["error"]["message"],failed["error"]["details"]) == (
            observation["exception_type"],observation["code"],observation["message"],observation["details"])
        for source_map in (failed["bindings"],failed_freeze["sources"]):
            for relative,pin in source_map.items():
                assert relative not in bindings or bindings[relative] == pin
                bindings[relative] = pin
        for name,pin in failed["source_bindings"].items():
            bindings[(failed_dir / "sources" / name).relative_to(root).as_posix()] = pin
        for path,pin in ((failed_file,FAILED_RESULT_SHA),(failed_freeze_file,FAILED_FREEZE_SHA),
                         (failed_launch_file,FAILED_LAUNCH_SHA),(failed_dir / failed["fixture"]["path"],failed["fixture"]["sha256"])):
            bindings[path.relative_to(root).as_posix()] = pin
        for name,key in (("input_state.npz","input_sha256"),("model_snapshot.npz","model_source_sha256"),
                         ("direction_snapshot.npz","direction_source_sha256"),("witness_direction_snapshot.npz","witness_direction_source_sha256"),
                         ("diagnostic_result.json","diagnostic_result_sha256"),("diagnostic_first_bad.npz","diagnostic_payload_sha256")):
            bindings[(failed_dir / name).relative_to(root).as_posix()] = failed[key]
        assert all(sha(root / relative) == pin for relative, pin in bindings.items())
        with np.load(input_file, allow_pickle=False) as archive:
            arrays = {name: archive[name] for name in archive.files}
        with np.load(root / MODEL_REL, allow_pickle=False) as archive:
            model = {name: archive[name] for name in (*OVERLAP, "points")}

        def field(value):
            return dict(shape=list(value.shape), dtype=str(value.dtype),
                        sha256=hashlib.sha256(value.tobytes()).hexdigest())

        assert set(arrays) == FIELDS
        assert {name: field(value) for name, value in arrays.items()} == observation["fields"]
        assert all(field(arrays[name]) == field(model[name]) for name in OVERLAP)
        assert model["points"].dtype == np.dtype("float64") and model["points"].shape == (9, 2)
        with np.load(failed_dir / failed["fixture"]["path"], allow_pickle=False) as archive:
            failed_fixture = {name:archive[name] for name in archive.files}
        assert {name:field(value) for name,value in failed_fixture.items()} == failed["fixture"]["fields"]
        assert all(field(arrays[name]) == field(failed_fixture[name]) for name in FIELDS)
        assert field(model["points"]) == field(failed_fixture["points"])
        assert observation["force_call_ordinal"] == 16 and arrays["edofs"].shape == (3200,8)
        assert arrays["lift"].shape == arrays["fluctuation"].shape == (6642,)
        assert failed["captured_state_sha256"] == observation["state_sha256"]
        digest = hashlib.sha256(b"split_displacement_v1")
        digest.update(np.asarray([len(arrays["lift"])], dtype="<i8").tobytes())
        for name in ("lift", "fluctuation"):
            digest.update(np.asarray(arrays[name], dtype="<f8").tobytes())
        assert digest.hexdigest() == observation["state_sha256"]
        report.update(input_bindings=bindings, author_source_sha256=sha(Path(__file__)),
            original_observation=observation, original_model=MODEL_REL,
            source_count=len(sources), production_input_count=len(inventory["input_bindings"]),
            isolated_runtime=RUNTIME_REL, isolated_source_count=42, isolated_kernel_sha256=CANDIDATE_SHA,
            predecessor_candidate_result_sha256=FAILED_RESULT_SHA, failed_fixture_sha256=failed["fixture"]["sha256"],
            failed_candidate_source_capsule_count=len(failed["source_bindings"]),
            diagnostic_scope="New independent first-root observation only; failed qualification remains closed",
            runtime=dict(python=sys.version, numpy=np.__version__, psutil=psutil.__version__),
            overlapping_model_fields_byte_equal=list(OVERLAP), supplied_points=field(model["points"]))
        for original, name in ((input_file, "input.npz"), (observation_file, "observation.json"),
                               (root / MODEL_REL, "source_model.npz"), (Path(__file__), "trace_horner192.py")):
            shutil.copyfile(original, output / name)
            assert sha(original) == sha(output / name)
        sys.path.insert(0, str(runtime / "hf_repo/src"))
        from hf_eval import compensated_invariants as ci
        from hf_eval.split_kernel_invariants_hu import batch_response_split_numpy
        from hf_eval.tmc_kernel import KernelError
        for module_name in ("compensated_invariants", "split_kernel_invariants_hu", "tmc_kernel"):
            module_file = Path(sys.modules["hf_eval."+module_name].__file__).resolve()
            assert module_file == (runtime / "hf_repo/src/hf_eval" / (module_name+".py")).resolve()
            assert sha(module_file) == origin["candidate_sources"]["hf_repo/src/hf_eval/"+module_name+".py"]
        kernel = sys.modules["hf_eval.split_kernel_invariants_hu"]
        originals = {"_finish": ci._finish, "dd_from": ci.dd_from, "_response": kernel._response}

        def capture(kind, result, caller, values):
            nonlocal first_bad
            if first_bad is not None or all(np.isfinite(part).all() for part in result):
                return
            first_bad = dict(kind=kind, caller=caller.f_code.co_name, caller_line=caller.f_lineno,
                elapsed_seconds=perf_counter()-STARTED,
                parameter_scope="Existing frame locals, including public DD arguments before primal sanitization when present",
                branch_scope="Chronologically first unsupported return; not proof that this branch contributes to selected output",
                selectors=[], parameters=[], stack=[])

            def retain(name, value):
                if isinstance(value, tuple) and len(value) == 2:
                    return [retain(name + "_hi", value[0]), retain(name + "_lo", value[1])]
                if isinstance(value, (np.ndarray, np.generic, float, int, bool)):
                    copied = np.array(value, copy=True)
                    if copied.dtype.kind in "bifu":
                        first_arrays[name] = copied
                        return name
                return None

            for name, value in {**values, "result_hi": result[0], "result_lo": result[1]}.items():
                retain(name, value)
            first_arrays["invalid_indices"] = np.argwhere(~np.isfinite(result[0]) | ~np.isfinite(result[1]))
            frame, index = caller, 0
            while frame is not None:
                filename = Path(frame.f_code.co_filename).resolve()
                try:
                    relative = filename.relative_to(root).as_posix()
                except ValueError:
                    relative = filename.name
                first_bad["stack"].append(dict(file=relative, line=frame.f_lineno, function=frame.f_code.co_name))
                if filename.name in ("compensated_invariants.py", "split_kernel_invariants_hu.py"):
                    for name in PARAMETERS:
                        if name in frame.f_locals:
                            key = retain(f"frame{index}_{name}", frame.f_locals[name])
                            if key is not None:
                                first_bad["parameters"].append(dict(function=frame.f_code.co_name, name=name, arrays=key))
                                value = np.asarray(frame.f_locals[name]) if name in ("near", "selected", "small_products") else None
                                if value is not None and value.shape == () and value.dtype.kind == "b":
                                    first_bad["selectors"].append(dict(function=frame.f_code.co_name, name=name, value=bool(value)))
                frame, index = frame.f_back, index + 1

        def finish(high, low, valid, xp):
            result = originals["_finish"](high, low, valid, xp)
            if xp is np:
                capture("_finish", result, inspect.currentframe().f_back,
                        dict(high=high, low=low, valid=valid))
                checkpoint()
            return result

        def from_value(value, xp=np):
            result = originals["dd_from"](value, xp)
            if xp is np:
                capture("dd_from", result, inspect.currentframe().f_back, dict(value=value))
                checkpoint()
            return result

        def response_observer(*args, **kwargs):
            result = originals["_response"](*args, **kwargs)
            report["raw_response_returned"] = True
            raw = {name: np.array(value, copy=True) for name,value in result[1].items()}
            path = output / "raw_response.npz"
            np.savez_compressed(path, **raw)
            report["raw_response"] = dict(payload=path.name, payload_sha256=sha(path),
                fields={name: field(value) for name,value in raw.items()},
                finite_counts={name: dict(finite=int(np.isfinite(value).sum()),
                    nonfinite=int((~np.isfinite(value)).sum())) for name,value in raw.items()},
                scope="Terminal raw response observations only; no new gate or HP qualification")
            return result

        report["arithmetic_bounds"] = {name: getattr(ci, name) for name in (
            "OPERAND_MIN", "OPERAND_MAX", "TEMPORARY_MAX", "SPLITTER", "EXP_ARGUMENT_MAX")}
        checkpoint()
        ci._finish, ci.dd_from, kernel._response = finish, from_value, response_observer
        report["force_started"] = 1
        write(output / "result.json", report)
        try:
            batch_response_split_numpy(arrays["lift"][arrays["edofs"]],
                arrays["fluctuation"][arrays["edofs"]],
                {name: arrays[name] for name in ("grad", "hessian", "weights")} | {"points": model["points"]},
                arrays["lam"], arrays["mu"], float(arrays["kr"]))
            report["force_completed"] = 1
            raise RuntimeError("Saved failed force unexpectedly returned; no retry")
        except KernelError as error:
            report["exception"] = dict(type=type(error).__name__, code=error.code, message=str(error), details=error.details)
            assert (type(error).__name__, error.code, str(error), error.details) == (
                observation["exception_type"], observation["code"], observation["message"], observation["details"])
            assert first_bad is not None, "Original range error reproduced but first primitive was not located"
        finally:
            ci._finish, ci.dd_from = originals["_finish"], originals["dd_from"]
            kernel._response = originals["_response"]
        checkpoint()
        report["status"] = "diagnostic_captured"
    except Exception as error:
        report.update(status="failed", error=repr(error), traceback=traceback.format_exc())
        raise
    finally:
        if ci is not None and originals:
            ci._finish, ci.dd_from = originals["_finish"], originals["dd_from"]
            kernel._response = originals["_response"]
        if first_bad is not None:
            import numpy as np
            payload = output / "first_bad_primitive.npz"
            np.savez_compressed(payload, **first_arrays)
            first_bad.update(payload=payload.name, payload_sha256=sha(payload),
                             fields={name: field(value) for name, value in first_arrays.items()})
        if process is not None:
            memory = 0
            for member in [process, *process.children(recursive=True)]:
                try:
                    info = member.memory_info()
                    memory += max(info.rss, getattr(info, "peak_wset", info.rss))
                except psutil.NoSuchProcess:
                    pass
            peak = max(peak, memory)
        report.update(first_bad_primitive=first_bad, elapsed_seconds=perf_counter()-STARTED,
            sampled_peak_RSS_bytes=peak,
            bindings_unchanged=bool(bindings) and all(sha(root / relative) == pin for relative, pin in bindings.items()),
            author_source_unchanged=sha(Path(__file__)) == report.get("author_source_sha256"),
            observation_hooks_restored=bool(originals) and ci._finish is originals["_finish"] and ci.dd_from is originals["dd_from"]
                and kernel._response is originals["_response"])
        if (not report["bindings_unchanged"] or not report["author_source_unchanged"]
                or report["elapsed_seconds"] > SECONDS or peak > RSS_LIMIT):
            report.update(status="failed", final_gate_error="Input/source identity or resource gate failed")
        write(output / "result.json", report)
    if report["status"] != "diagnostic_captured":
        raise RuntimeError("Diagnostic did not complete within its independent contract")
    print(json.dumps({name: report[name] for name in ("status", "force_started", "force_completed",
        "tangent_calls", "solver_calls", "HP_calls", "elapsed_seconds", "sampled_peak_RSS_bytes")}), flush=True)


if __name__ == "__main__":
    main()
