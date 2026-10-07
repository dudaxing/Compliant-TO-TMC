"""Render an audited real API cache once and export a separate saved response."""
from time import perf_counter
STARTED = perf_counter()
from datetime import datetime, timezone
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import sys

sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
read = lambda path: json.loads(path.read_bytes())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    args = parser.parse_args()
    root = args.repo.resolve()
    protocol_file = (args.protocol if args.protocol.is_absolute() else root/args.protocol).resolve()
    protocol = read(protocol_file)
    stage = protocol_file.parent
    row = protocol["phases"]["view"]
    assert all(sha(root/name) == pin for name, pin in protocol["bindings"].items())
    input_directory = root/protocol["input_directory"]
    view_directory = input_directory/"view"
    qualified_file = input_directory/"qualified_response.json"
    receipt_file = input_directory/"view_execution_receipt.json"
    assert not view_directory.exists() and not qualified_file.exists() and not receipt_file.exists()
    result_file = input_directory/"result/result.json"
    result = read(result_file)
    model = read(result_file.parent/result["model"]["descriptor_path"])
    audit_file = input_directory/"audit/summary.json"
    audit = read(audit_file)
    n = len(result["states"])
    assert result["status"] == "success" and result["task_target_executed"] is True
    assert audit["status"] == "pass" and audit["result_sha256"] == sha(result_file)
    assert audit["accepted_states"] == len(audit["states"]) == n
    assert audit["HP_calls_started"] == audit["HP_calls_completed"] == 2*n
    for role, dependency in protocol["prerequisites"].items():
        launch, receipt = read(root/dependency["launch_file"]), read(root/dependency["receipt_file"])
        control = read(root/dependency["protocol_file"])
        limits = control["phases"][role]
        assert launch["status"] == receipt["status"] == "pass"
        assert launch["invocations"] == 1 and launch["exit_code"] == 0 and launch["stop_reason"] is None
        assert launch["all_bindings_unchanged"] is receipt["all_bindings_unchanged"] is True
        assert launch["protocol_sha256"] == receipt["protocol_sha256"] == sha(root/dependency["protocol_file"])
        assert launch["elapsed_seconds"] <= limits["outer_seconds"]
        assert launch["peak_sampled_tree_RSS_bytes"] <= control["sampled_RSS_bytes"]
        assert receipt["elapsed_seconds"] <= limits["helper_seconds"]
        assert receipt[dependency["receipt_RSS_field"]] <= control["sampled_RSS_bytes"]
    original_response_file = result_file.parent/"response.json"
    original_response_pin = sha(original_response_file)
    receipt = dict(schema_version="native-real-api-view-execution-1.0", status="running",
        started_utc=datetime.now(timezone.utc).isoformat(), protocol_sha256=sha(protocol_file),
        seconds_limit=row["helper_seconds"], sampled_RSS_limit_bytes=protocol["sampled_RSS_bytes"],
        invocations=1, accepted_states=n, force_calls=0, tangent_calls=0, solver_calls=0,
        HP_calls=0, model_constructions=0,
        scope="Original audited saved-cache renderer and stdlib response only; no new mechanics")
    write(receipt_file, receipt)
    peak, exception, manifest, outputs = 0, None, None, {}
    try:
        import psutil
        process = psutil.Process()

        def checkpoint():
            nonlocal peak
            memory = process.memory_info()
            peak = max(peak, memory.rss, getattr(memory, "peak_wset", memory.rss))
            if ((stage/"stop_requested.txt").exists() or peak > protocol["sampled_RSS_bytes"]
                    or perf_counter()-STARTED > row["helper_seconds"]):
                raise RuntimeError("Saved view cooperative resource limit")

        checkpoint()
        viewer_file = root/protocol["viewer_file"]
        spec = importlib.util.spec_from_file_location("real_api_saved_viewer", viewer_file)
        viewer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(viewer)
        before_argv = sys.argv
        try:
            sys.argv = [str(viewer_file), "--input", str(input_directory),
                        "--output", str(view_directory/"real_api"), "--magnification", "1000"]
            viewer.main()
        finally:
            sys.argv = before_argv
        checkpoint()
        metadata_file = view_directory/"real_api/view_metadata.json"
        metadata = read(metadata_file)
        assert metadata["audit_summary_sha256"] == sha(audit_file)
        assert metadata["geometry_id"] == model["source_geometry"]["geometry_id"]
        assert metadata["task_sha256"] == result["task_sha256"]
        assert metadata["display"]["geometry_scale"] == 1.
        assert metadata["display"]["supplementary_displacement_scale"] == 1000.
        assert len(metadata["numerical_states"]) == len(metadata["audit_states"]) == n
        assert metadata["media"]["native_mean_path.gif"]["frames"] == n
        assert all(metadata[name] == 0 for name in
                   ("force_calls", "tangent_calls", "solver_calls", "HP_calls", "model_constructions"))
        rows = []
        for i, (state, numbers) in enumerate(zip(result["states"], metadata["numerical_states"])):
            assert numbers["index"] == i and numbers["target_mm"] == state["d"]
            rows.append(dict(numbers, state_sha256=state["state_sha256"], d_mm=state["d"]))
        write(view_directory/"real_api/summary.json",
              dict(production_status=result["status"], accepted_states=n, rows=rows,
                   scope="Original cached renderer measurements; all actual accepted states"))
        view_outputs = {path.relative_to(view_directory).as_posix(): sha(path)
                        for path in (view_directory/"real_api").rglob("*") if path.is_file()}
        manifest = dict(schema_version="native-single-case-saved-view-1.0", status="pass",
            input_source_bindings=metadata["input_files_sha256"], outputs=view_outputs,
            cases=[dict(label="real_api", production_status=result["status"],
                model_sha256=model["arrays"]["sha256"], task=model["task"],
                saved_accepted_states=n, observed_states=len(rows))],
            force_calls=0, tangent_calls=0, solver_calls=0, HP_calls=0, model_constructions=0,
            scope="Existing saved visualization; no contact/pressure/HF5 qualification")
        assert manifest["input_source_bindings"][result_file.relative_to(root).as_posix()] == sha(result_file)
        write(view_directory/"manifest.json", manifest)
        checkpoint()
        sys.path.insert(0, str(root/"hf_repo/src"))
        from hf_eval.native_response import summarize_saved_native_result, write_native_response
        response = summarize_saved_native_result(result_file, repo_root=root,
            reference_file=audit_file, view_manifest=view_directory/"manifest.json")
        assert response["independent_reference"]["accepted_reference_pass"] is True
        assert response["independent_reference"]["full_path_reference_pass"] is True
        assert response["views"]["status"] == "matched" and len(response["views"]["links"]) == 2
        assert all(response["independent_reference"][name] is False for name in
                   ("HP_all_columns_qualified", "contact_qualified", "clamp_qualified", "pressure_qualified", "HF5_qualified"))
        assert all(value is False for value in response["producer_flags"].values())
        write_native_response(response, qualified_file)
        assert sha(original_response_file) == original_response_pin
    except Exception as error:
        exception = error
        receipt["exception"] = dict(exception_class=type(error).__name__, reason=str(error))
    finally:
        try:
            outputs = {path.relative_to(root).as_posix(): sha(path)
                       for path in view_directory.rglob("*") if path.is_file()}
            if qualified_file.exists():
                outputs[qualified_file.relative_to(root).as_posix()] = sha(qualified_file)
            unchanged = all(sha(root/name) == pin for name, pin in protocol["bindings"].items())
            assert unchanged and sha(original_response_file) == original_response_pin
            if "checkpoint" in locals():
                checkpoint()  # Covers all output/input hashing, not just rendering.
        except Exception as error:
            receipt["finalization_exception"] = dict(exception_class=type(error).__name__, reason=str(error))
            if exception is None:
                exception = error
        if exception is not None and manifest is not None:
            manifest["status"] = "failed"
            manifest["failure_scope"] = "Whole saved-view phase did not pass; any saved response is an attempted artifact"
            write(view_directory/"manifest.json", manifest)
            outputs[(view_directory/"manifest.json").relative_to(root).as_posix()] = sha(view_directory/"manifest.json")
        receipt.update(status="pass" if exception is None else "failed", outputs=outputs,
            all_bindings_unchanged=locals().get("unchanged", False),
            elapsed_seconds=perf_counter()-STARTED, peak_sampled_RSS_bytes=peak,
            original_response_sha256=original_response_pin,
            qualified_response_file=qualified_file.relative_to(root).as_posix() if qualified_file.exists() else None,
            completed_utc=datetime.now(timezone.utc).isoformat())
        write(receipt_file, receipt)
        print(json.dumps({key:receipt[key] for key in ("status", "accepted_states", "elapsed_seconds",
                                                      "peak_sampled_RSS_bytes")}), flush=True)
    if exception is not None:
        raise exception


if __name__ == "__main__":
    main()
