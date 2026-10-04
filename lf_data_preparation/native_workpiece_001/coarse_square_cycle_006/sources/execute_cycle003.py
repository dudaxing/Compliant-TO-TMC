"""Execute the new-core [0,.5,0] path; retain every actual accepted state."""
from pathlib import Path
from time import perf_counter
from datetime import datetime, timezone
import hashlib
import json
import sys
STARTED = perf_counter()
ROOT = Path(__file__).resolve().parents[3]
STAGE = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+"\n", encoding="utf-8")

def main():
    inventory_file = STAGE/"input_inventory.json"
    inventory = json.loads(inventory_file.read_text(encoding="utf-8"))
    freeze_file = STAGE/"source_freeze.json"
    assert sha(freeze_file) == inventory["source_freeze_sha256"]
    sources = json.loads(freeze_file.read_text(encoding="utf-8"))["sources"]
    inputs = inventory["input_bindings"]
    assert all(sha(ROOT/p) == pin and sha(STAGE/"sources"/Path(p).name) == pin for p, pin in sources.items())
    assert all(sha(ROOT/p) == pin for p, pin in inputs.items())
    receipt_file = STAGE/"execution_receipt.json"
    assert not receipt_file.exists() and not (STAGE/"result").exists()
    receipt = dict(schema_version="native-mean-execution-1.0", status="running",
        baseline_commit=inventory["baseline_commit"], input_inventory_sha256=sha(inventory_file),
        source_freeze_sha256=sha(freeze_file), sources=sources, inputs=inputs, invocations=0,
        HP_calls=0, JIT_calls=0, LF_imports=0, accepted_states=0,
        force_calls=None, tangent_calls=None, solver_calls=None, save_force_calls=None, save_tangent_calls=None,
        seconds_limit=inventory["execution_limits"]["production_seconds"],
        sampled_RSS_limit_bytes=inventory["execution_limits"]["sampled_RSS_bytes"],
        started_utc=datetime.now(timezone.utc).isoformat(),
        budget_mode="Whole-helper/API clocks and sampled process peak_wset; cooperative outer tree monitor, no OS hard cap/force",
        stop_policy=inventory["stop_policy"])
    write(receipt_file, receipt)
    import psutil
    sys.path.insert(0, str(ROOT/"hf_repo/src"))
    from hf_eval.displacement import DisplacementSettings
    from hf_eval import native_mean
    from hf_eval.native_mean import solve_native_mean, write_native_mean
    from hf_eval.native_force import _state_hash
    from hf_eval.tmc import TMCError
    from hf_eval.tmc_kernel import KernelError
    import numpy as np
    process = psutil.Process()
    peak = 0
    def accepted(snapshot):
        nonlocal peak
        memory = process.memory_info()
        peak = max(peak, memory.rss, getattr(memory, "peak_wset", memory.rss))
        if peak > receipt["sampled_RSS_limit_bytes"]:
            raise RuntimeError("Sampled RSS bound exceeded")
        row = {k: snapshot.record[k] for k in ("d","R_input","q_in","q_out","relative_residual","state_sha256","leg","original_target_index")}
        row.update(index=receipt["accepted_states"], elapsed_seconds=perf_counter()-STARTED,
                   workpiece=snapshot.record["workpiece"]["force_on_lower_body_N"])
        with (STAGE/"accepted_progress.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row)+"\n")
        receipt["accepted_states"] += 1
        print(json.dumps(row), flush=True)
    original_force = native_mean._assemble_force
    observed_calls, captured = 0, None
    def observed_force(model, state):
        nonlocal observed_calls, captured
        observed_calls += 1
        if (STAGE/"stop_requested.txt").exists():
            raise RuntimeError("External resource observation requested stage stop")
        if perf_counter()-STARTED > receipt["seconds_limit"]:
            raise KernelError("Whole-helper time budget exhausted", code="time_limit")
        try:
            return original_force(model, state)
        except (KernelError, TMCError) as error:
            if error.code == "unsupported_arithmetic_range" and captured is None:
                try:
                    directory = STAGE/"first_force_range_input"
                    directory.mkdir()
                    arrays = dict(lift=state.lift, fluctuation=state.fluctuation,
                        edofs=model.edofs, coordinates=model.coordinates, connectivity=model.connectivity,
                        lam=model.lam, mu=model.mu, kr=np.asarray(model.kr),
                        hx=np.asarray(model.hx), hy=np.asarray(model.hy), thickness=np.asarray(model.thickness),
                        solid=model.solid, fixed_dofs=model.fixed_dofs,
                        **{name:model.ops[name] for name in ("grad", "hessian", "weights")})
                    np.savez_compressed(directory/"input.npz", **arrays)
                    captured = dict(schema_version="native-force-range-input-1.0",
                        scope="First actual force range exception; base/trial classification requires chronology; tangent exceptions not observed",
                        force_call_ordinal=observed_calls, state_sha256=_state_hash(state),
                        exception_type=type(error).__name__, code=error.code, message=str(error), details=error.details,
                        elapsed_seconds=perf_counter()-STARTED, input_npz_sha256=sha(directory/"input.npz"),
                        fields={name:dict(shape=list(value.shape),dtype=str(value.dtype),
                            sha256=hashlib.sha256(value.tobytes()).hexdigest()) for name,value in arrays.items()},
                        source_freeze_sha256=sha(freeze_file), input_inventory_sha256=sha(inventory_file),
                        extra_force_calls=0, extra_tangent_calls=0, extra_solver_calls=0, HP_calls=0)
                    write(directory/"observation.json", captured)
                    print(json.dumps(dict(observation="first_force_range_input", force_call_ordinal=observed_calls,
                        state_sha256=captured["state_sha256"], elapsed_seconds=captured["elapsed_seconds"])), flush=True)
                except Exception as persistence_error:
                    raise RuntimeError("First force range input could not be saved") from persistence_error
            raise
    native_mean._assemble_force = observed_force
    try:
        row = inventory["case"]
        task = json.loads((ROOT/row["task_file"]).read_text(encoding="utf-8"))
        receipt["invocations"] = 1
        write(receipt_file, receipt)
        result = solve_native_mean(ROOT/row["geometry_file"], task, row["targets_mm"],
            settings=DisplacementSettings(**inventory["settings"]), on_accept=accepted)
        descriptor = write_native_mean(result, STAGE/row["result_directory"])
        metadata = result.metadata
        with np.load(STAGE/"result/model/model.npz", allow_pickle=False) as saved, np.load(ROOT/row["workpiece_model_file"], allow_pickle=False) as original:
            assert len(saved.files) == len(original.files) == 27 and set(saved.files) == set(original.files)
            assert all(saved[name].dtype == original[name].dtype and saved[name].shape == original[name].shape
                and saved[name].tobytes() == original[name].tobytes() for name in original.files), "Original 27 model arrays changed"
        receipt.update(model_arrays_compared=27, original_workpiece_model_arrays_equal=True,
            original_workpiece_model_sha256=sha(ROOT/row["workpiece_model_file"]),
            **{name: metadata[name] for name in ("target_reached","path_completed","loading_peak_reached","unload_endpoint_reached","task_target_executed")})
        receipt.update(status="pass" if metadata["status"] == "success" else "not_pass",
            returned_status=metadata["status"], call_counts=metadata["call_counts"],
            force_calls=metadata["call_counts"]["force_calls"], tangent_calls=metadata["call_counts"]["tangent_calls"],
            solver_calls=metadata["call_counts"]["solver_invocations"],
            save_force_calls=metadata["save_force_calls"], save_tangent_calls=metadata["save_tangent_calls"],
            accepted_states=len(result.accepted), state_sha256=[s.record["state_sha256"] for s in result.accepted],
            result_sha256=sha(descriptor), model_sha256=sha(STAGE/"result/model/model.npz"),
            task_sha256=result.project.task_hash, failure=metadata["failure"])
        if perf_counter()-STARTED > receipt["seconds_limit"]:
            raise RuntimeError("Production wall-time bound exceeded; saved states retained")
        if receipt["status"] != "pass":
            raise RuntimeError("Production path not completed: "+str(metadata["failure"]))
    except Exception as error:
        receipt.update(status="not_pass", error=repr(error))
        raise
    finally:
        native_mean._assemble_force = original_force
        receipt.update(observed_force_calls=observed_calls, first_force_range_input=captured)
        memory = process.memory_info()
        peak = max(peak, memory.rss, getattr(memory, "peak_wset", memory.rss))
        receipt.update(elapsed_seconds=perf_counter()-STARTED, sampled_peak_RSS_bytes=peak,
            sources_unchanged=all(sha(ROOT/p)==pin and sha(STAGE/"sources"/Path(p).name)==pin for p,pin in sources.items()),
            inputs_unchanged=all(sha(ROOT/p)==pin for p,pin in inputs.items()),
            completed_utc=datetime.now(timezone.utc).isoformat())
        if (peak > receipt["sampled_RSS_limit_bytes"] or receipt["elapsed_seconds"] > receipt["seconds_limit"]
                or not receipt["sources_unchanged"] or not receipt["inputs_unchanged"]):
            receipt.update(status="not_pass", error="Final resource or source/input binding check failed")
        write(receipt_file, receipt)
    if receipt["status"] != "pass":
        raise RuntimeError(receipt["error"])
    print(json.dumps({k:receipt[k] for k in ("status","call_counts","accepted_states","elapsed_seconds","sampled_peak_RSS_bytes")}), flush=True)

if __name__ == "__main__":
    main()
