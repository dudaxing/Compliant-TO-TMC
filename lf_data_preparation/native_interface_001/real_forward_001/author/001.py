"""One real native API call, counted delegates and cooperative resource limits."""
from time import perf_counter
STARTED = perf_counter()
from datetime import datetime, timezone
from pathlib import Path
import argparse
import hashlib
import json
import os
import sys
import tempfile

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
    protocol_file = args.protocol if args.protocol.is_absolute() else root/args.protocol
    protocol_file = protocol_file.resolve()
    stage = protocol_file.parent
    protocol = read(protocol_file)
    phase = protocol["phases"]["production"]
    assert all(sha(root/name) == pin for name, pin in protocol["bindings"].items())
    run = root/protocol["run_directory"]
    assert not run.exists()
    run.mkdir()
    receipt_file = run/"execution_receipt.json"
    result_directory = run/"result"
    receipt = dict(schema_version="native-real-api-execution-1.0", status="running",
        started_utc=datetime.now(timezone.utc).isoformat(), protocol_sha256=sha(protocol_file),
        seconds_limit=phase["helper_seconds"], sampled_RSS_limit_bytes=protocol["sampled_RSS_bytes"],
        baseline_commit=protocol["baseline_commit"], invocations=0, HP_calls=0, JIT_calls=0, LF_imports=0,
        qualification="Actual API transport and production gates only; no independent HP/contact/pressure/HF5 qualification",
        prefix_scope="Accepted scalar callback after original capture; resource exceptions may leave no cached result/response")
    write(receipt_file, receipt)
    counters = {}
    observed = dict(force_calls=0, force_calls_completed=0, tangent_calls=0, tangent_calls_completed=0)
    prefix, patches = [], []
    peak, current_stage, writing = 0, "startup", False
    native_result = response = exception = None
    outputs = {}
    try:
        import psutil
        sys.path.insert(0, str(root/"hf_repo/src"))
        from hf_eval import native_evaluate, native_mean, native_project
        process = psutil.Process()

        def checkpoint():
            nonlocal peak
            memory = process.memory_info()
            peak = max(peak, memory.rss, getattr(memory, "peak_wset", memory.rss))
            if (stage/"stop_requested.txt").exists():
                receipt["stop_reason"] = "external_stop_requested"
            elif peak > protocol["sampled_RSS_bytes"]:
                receipt["stop_reason"] = "sampled_RSS_limit"
            elif perf_counter()-STARTED > phase["helper_seconds"]:
                receipt["stop_reason"] = "whole_helper_elapsed_limit"
            if receipt.get("stop_reason"):
                raise RuntimeError(receipt["stop_reason"])

        def install(module, name, label, custom=None):
            original = getattr(module, name)
            count = counters[label] = dict(started=0, completed=0)
            def delegated(*positional, **keywords):
                nonlocal current_stage
                current_stage = label
                checkpoint()
                count["started"] += 1
                value = original(*positional, **keywords) if custom is None else custom(original, positional, keywords)
                count["completed"] += 1
                return value
            patches.append((module, name, original))
            setattr(module, name, delegated)

        def constructor(original, positional, keywords):
            value = original(*positional, **keywords)
            assert type(value) is original
            receipt["constructor_result_type"] = type(value).__module__+"."+type(value).__name__
            return value

        def controller(original, positional, keywords):
            callback = keywords["on_accept"]
            def accepted(measured):
                callback(measured)  # Original cache capture first; no extra physical evaluation.
                row = {name: measured[name] for name in (
                    "state_sha256", "d", "R_input", "q_in", "q_out", "minimum_J",
                    "relative_residual", "constraint_residual", "relative_global_force_balance")}
                row.update(index=len(prefix), elapsed_seconds=perf_counter()-STARTED,
                           observed_force_calls=dict(observed))
                prefix.append(row)
                with (run/"accepted_progress.jsonl").open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps(row, allow_nan=False)+"\n")
                print(json.dumps(row, allow_nan=False), flush=True)
                checkpoint()
            return original(*positional, **dict(keywords, on_accept=accepted))

        def solved(original, positional, keywords):
            nonlocal native_result
            native_result = original(*positional, **keywords)
            return native_result

        def cached_write(original, positional, keywords):
            nonlocal writing
            before = dict(observed)
            native_before = dict(positional[0].metadata["call_counts"])
            writing = True
            try:
                value = original(*positional, **keywords)
            finally:
                writing = False
            assert observed == before and positional[0].metadata["call_counts"] == native_before
            receipt["cached_write_F_T_delta"] = dict(force_calls=0, tangent_calls=0)
            return value

        def physical(module, name, kind):
            original = getattr(module, name)
            def delegated(*positional, **keywords):
                nonlocal current_stage
                current_stage = kind
                checkpoint()
                assert not writing, "Cached persistence attempted a new physical evaluation"
                observed[kind+"_calls"] += 1
                value = original(*positional, **keywords)
                observed[kind+"_calls_completed"] += 1
                return value
            patches.append((module, name, original))
            setattr(module, name, delegated)

        install(native_project, "TMCModel", "constructor", constructor)
        install(native_mean, "build_native_project", "project_builder")
        install(native_mean, "solve_split_displacement_path", "controller", controller)
        install(native_evaluate, "solve_native_mean", "native_solve", solved)
        install(native_evaluate, "write_native_mean", "cached_writer", cached_write)
        install(native_evaluate, "summarize_saved_native_result", "formatter")
        install(native_evaluate, "write_native_response", "response_writer")
        physical(native_mean, "_assemble_force", "force")
        physical(native_mean, "_tangent", "tangent")
        checkpoint()
        original_cwd = Path.cwd()
        with tempfile.TemporaryDirectory(prefix="hf_real_native_api_") as caller:
            caller_directory = Path(caller).resolve()
            assert not caller_directory.is_relative_to(root)
            receipt["caller_cwd"] = str(caller_directory)
            receipt["explicit_repo_root"] = str(root)
            try:
                os.chdir(caller_directory)
                receipt["invocations"] = 1
                response = native_evaluate.evaluate_native(protocol["geometry_file"], protocol["task_file"],
                    protocol["result_directory"], repo_root=root)
            finally:
                os.chdir(original_cwd)
        assert receipt["invocations"] == 1
        assert all(row == dict(started=1, completed=1) for row in counters.values())
        assert response["status"] == "success", response.get("failure")
        assert native_result is not None and native_result.metadata["status"] == "success"
        metadata = native_result.metadata
        assert metadata["targets_mm"] == protocol["targets_mm"] == [0., .001]
        assert metadata["task_target_executed"] is True and metadata["accepted_states"] == len(prefix) == 2
        assert metadata["settings"] == response["invocation"]["settings"] == protocol["settings"]
        assert metadata["counts"] == protocol["expected_counts"]
        assert observed == {name: metadata["call_counts"][name] for name in observed}
        assert metadata["call_counts"]["solver_invocations"] == 1
        assert metadata["call_counts"]["HP_calls"] == metadata["call_counts"]["JIT_calls"] == 0
        assert metadata["save_force_calls"] == metadata["save_tangent_calls"] == 0
        assert all(response["options"][name]["value"] == value for name, value in
                   dict(response_mode="complete", tangent_mode="full", initial_guess="tangent").items())
        assert response["target_response"]["d_mm"] == response["requested_endpoint_response"]["d_mm"] == .001
        assert response["target_response"]["workpiece"] is None
        assert all(flag is False for flag in response["producer_flags"].values())
        assert response["independent_reference"]["status"] == "not_provided"
        assert all(value is False for name, value in response["independent_reference"].items()
                   if name.endswith("_pass") or name.endswith("_qualified"))
        assert response["views"]["status"] == "not_provided"
        assert response["views"]["manifest"] is None and not response["views"]["links"]
        gates = protocol["gates"]
        for snapshot in native_result.accepted:
            row = snapshot.record
            assert row["minimum_J"] > 0 and row["relative_residual"] <= float(gates["production_residual"])
            assert abs(row["constraint_residual"]) <= row["constraint_bound"]
            assert row["relative_global_force_balance"] <= float(gates["global_force_balance"])
            fixed_max = max((abs(float(snapshot.state.lift[i])+float(snapshot.state.fluctuation[i]))
                             for i in native_result.project.model.fixed_dofs), default=0.)
            assert fixed_max <= float(gates["fixed_displacement_mm"])
        saved = read(result_directory/"result.json")
        model = read(result_directory/saved["model"]["descriptor_path"])
        assert len(model["arrays"]["fields"]) == 23
        assert sha(result_directory/"result.json") == response["identity"]["result"]["sha256"]
        assert read(result_directory/"response.json") == response
        receipt.update(result_sha256=sha(result_directory/"result.json"),
            response_sha256=sha(result_directory/"response.json"),
            accepted_states=metadata["accepted_states"], task_target_executed=True,
            call_counts=metadata["call_counts"], last_accepted=response["last_accepted"],
            evaluation_elapsed_seconds=response["evaluation_elapsed_seconds"],
            evaluation_elapsed_scope=response["evaluation_elapsed_scope"])
    except Exception as error:
        exception = error
        receipt["exception"] = dict(stage=current_stage, exception_class=type(error).__name__,
                                    code=getattr(error, "code", None), reason=str(error))
        if response is not None:
            receipt["returned_API_failure"] = response.get("failure")
    finally:
        for module, name, original in reversed(patches):
            setattr(module, name, original)
        if native_result is not None:
            receipt.update(call_counts=dict(native_result.metadata["call_counts"]),
                accepted_states=native_result.metadata["accepted_states"],
                task_target_executed=native_result.metadata["task_target_executed"])
        else:
            receipt.update(call_counts=None, accepted_states=None, task_target_executed=None)
        try:
            outputs = {path.relative_to(root).as_posix(): sha(path)
                       for path in result_directory.rglob("*") if path.is_file()}
            progress_file = run/"accepted_progress.jsonl"
            if progress_file.exists():
                outputs[progress_file.relative_to(root).as_posix()] = sha(progress_file)
            unchanged = all(sha(root/name) == pin for name, pin in protocol["bindings"].items())
            assert unchanged
            if "checkpoint" in locals():
                checkpoint()  # Includes final output/input hashing, no new physical call.
        except Exception as error:
            receipt["finalization_exception"] = dict(exception_class=type(error).__name__, reason=str(error))
            if exception is None:
                exception = error
        receipt.update(status="pass" if exception is None else "failed", counts=counters,
            observed_F_T=observed, accepted_scalar_prefix=prefix, outputs=outputs,
            result_file=(result_directory/"result.json").relative_to(root).as_posix()
                if (result_directory/"result.json").is_file() else None,
            response_file=(result_directory/"response.json").relative_to(root).as_posix()
                if (result_directory/"response.json").is_file() else None,
            elapsed_seconds=perf_counter()-STARTED, peak_sampled_RSS_bytes=peak,
            completed_utc=datetime.now(timezone.utc).isoformat(),
            all_bindings_unchanged=locals().get("unchanged", False),
            callback_scope="Stage-only existing accepted scalars after original capture; no extra F/T/array/geometry observation")
        write(receipt_file, receipt)
        print(json.dumps({key:receipt[key] for key in ("status", "elapsed_seconds", "peak_sampled_RSS_bytes",
                                                      "result_file", "response_file")}), flush=True)
    if exception is not None:
        raise exception


if __name__ == "__main__":
    main()
