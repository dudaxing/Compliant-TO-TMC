"""Execute one declared native fixed-workpiece cycle and save cached states."""
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
        seconds_limit=inventory["execution_limits"]["production_seconds"],
        sampled_RSS_limit_bytes=inventory["execution_limits"]["sampled_RSS_bytes"],
        started_utc=datetime.now(timezone.utc).isoformat(),
        budget_mode="Cooperative API time and sampled RSS; external timeout; not OS memory hard cap",
        stop_policy=inventory["stop_policy"])
    write(receipt_file, receipt)
    import psutil
    sys.path.insert(0, str(ROOT/"hf_repo/src"))
    from hf_eval.displacement import DisplacementSettings
    from hf_eval.native_mean import solve_native_mean, write_native_mean
    process = psutil.Process()
    peak = 0
    def accepted(snapshot):
        nonlocal peak
        memory = process.memory_info()
        peak = max(peak, memory.rss, getattr(memory, "peak_wset", memory.rss))
        if peak > receipt["sampled_RSS_limit_bytes"]:
            raise RuntimeError("Sampled RSS bound exceeded")
        row = {k: snapshot.record[k] for k in ("d","R_input","q_in","q_out","relative_residual","state_sha256","leg")}
        row.update(index=receipt["accepted_states"], elapsed_seconds=perf_counter()-STARTED,
                   workpiece=snapshot.record["workpiece"]["force_on_lower_body_N"])
        with (STAGE/"accepted_progress.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row)+"\n")
        receipt["accepted_states"] += 1
        print(json.dumps(row), flush=True)
    try:
        row = inventory["case"]
        task = json.loads((ROOT/row["task_file"]).read_text(encoding="utf-8"))
        receipt["invocations"] = 1
        write(receipt_file, receipt)
        result = solve_native_mean(ROOT/row["geometry_file"], task, row["targets_mm"],
            settings=DisplacementSettings(**inventory["settings"]), on_accept=accepted)
        descriptor = write_native_mean(result, STAGE/row["result_directory"])
        metadata = result.metadata
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
