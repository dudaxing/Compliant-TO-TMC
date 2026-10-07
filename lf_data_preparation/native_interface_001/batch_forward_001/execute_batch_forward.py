"""One real sequential native batch call with counted delegates and original gates."""
from time import perf_counter
STARTED = perf_counter()  # Whole helper clock starts before scientific imports.
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import argparse
import gc
import hashlib
import json
import os
import subprocess
import sys
import tempfile

ONCE = ("evaluate_native", "native_solve", "project_builder", "constructor",
        "controller", "cached_writer", "formatter", "response_writer")
SCALARS = ("state_sha256", "d", "R_input", "q_in", "q_out", "minimum_J",
           "relative_residual", "constraint_residual", "constraint_bound",
           "relative_global_force_balance")
F_T = ("force_calls", "force_calls_completed", "tangent_calls", "tangent_calls_completed")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                    encoding="utf-8")


def failure(error, stage):
    return dict(stage=stage, exception_class=type(error).__name__,
                code=getattr(error, "code", None), reason=str(error))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    args = parser.parse_args()
    root = args.repo.resolve()
    protocol_file = (args.protocol if args.protocol.is_absolute() else root / args.protocol).resolve()
    stage = protocol_file.parent
    protocol = read(protocol_file)
    phase = protocol["phases"]["production"]
    pins = protocol["bindings"]
    assert all(sha(root / name) == pin for name, pin in pins.items())
    baseline = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, check=True,
                              capture_output=True, text=True).stdout.strip()
    assert baseline == protocol["baseline_commit"]
    run = (root / protocol["run_directory"]).resolve()
    batch_directory = (root / protocol["batch_directory"]).resolve()
    manifest_file = (root / protocol["manifest_file"]).resolve()
    manifest = read(manifest_file)
    assert run.is_relative_to(stage) and batch_directory == run / "batch"
    assert manifest["options"] == protocol["options"]
    assert manifest["options"]["targets"] == protocol["targets_mm"]
    plans = manifest["cases"]
    assert [case["label"] for case in plans] == ["canonical", "native_fine"]
    assert all((root / case["output"]).resolve() == run / case["label"] for case in plans)
    assert set(protocol["expected_counts"]) == {case["label"] for case in plans}
    assert not run.exists() and not (stage / "stop_requested.txt").exists()
    run.mkdir()
    receipt_file = run / "execution_receipt.json"
    progress_file = run / "accepted_progress.jsonl"
    receipt = dict(schema_version="native-real-batch-execution-1.0", status="running",
        started_utc=datetime.now(timezone.utc).isoformat(), baseline_commit=baseline,
        protocol_sha256=sha(protocol_file), bindings=dict(pins),
        manifest_file=manifest_file.relative_to(root).as_posix(), manifest_sha256=sha(manifest_file),
        run_directory=run.relative_to(root).as_posix(), batch_directory=batch_directory.relative_to(root).as_posix(),
        seconds_limit=phase["helper_seconds"], outer_seconds=phase["outer_seconds"],
        sampled_RSS_limit_bytes=protocol["sampled_RSS_bytes"], batch_invocations=0,
        production_gates=dict(protocol["gates"]), options=dict(protocol["options"]),
        qualification_scope="Actual batch/API transport and original production gates only; no inherited HP/contact/pressure/HF5 or mesh qualification",
        prefix_scope="Existing accepted scalars after original native capture; an escaping resource error may leave only a prefix and partial batch index",
        fixed_gate_scope="Original cached lift+fluctuation check on existing fixed DOFs at cached writer; no additional force/tangent/geometry/field kernel")
    cases = {plan["label"]: dict(label=plan["label"], attempted=False, status="not_run",
        output=plan["output"], counts={}, observed_F_T=dict.fromkeys(F_T, 0),
        accepted_scalar_prefix=[], original_result_metadata=None, returned_response=None,
        production_gate_status="not_checked", production_gate_rows=[],
        result_file=None, response_file=None) for plan in plans}
    receipt["cases"] = cases
    write(receipt_file, receipt)
    peak, current_stage, writing, active = 0, "startup", False, None
    patches, outputs, batch_index, exception = [], {}, None, None
    try:
        import psutil
        process = psutil.Process()

        def checkpoint():
            nonlocal peak
            memory = process.memory_info()
            peak = max(peak, memory.rss, getattr(memory, "peak_wset", memory.rss))
            if (stage / "stop_requested.txt").exists():
                receipt["stop_reason"] = "external_stop_requested"
            elif peak > protocol["sampled_RSS_bytes"]:
                receipt["stop_reason"] = "sampled_RSS_limit"
            elif perf_counter() - STARTED > phase["helper_seconds"]:
                receipt["stop_reason"] = "whole_helper_elapsed_limit"
            if receipt.get("stop_reason"):
                raise RuntimeError(receipt["stop_reason"])

        def after_error_checkpoint():
            # Preserve the original scientific/resource exception if the final sample also fails.
            try:
                checkpoint()
            except Exception as error:
                receipt["checkpoint_during_exception"] = failure(error, current_stage)

        checkpoint()
        sys.path.insert(0, str(root / "hf_repo/src"))
        from hf_eval import native_batch, native_evaluate, native_mean, native_project
        checkpoint()

        constructor_class = native_project.TMCModel
        def count_for(label):
            assert active is not None, "A real case delegate ran outside the batch case call"
            return active["counts"].setdefault(label, dict(started=0, completed=0, elapsed_seconds=0.))

        def install(module, name, label, *, prepare=None, before=None, after=None, final=None):
            original = getattr(module, name)
            def delegated(*positional, **keywords):
                nonlocal current_stage
                current_stage = active["label"] + ":" + label
                checkpoint()
                if prepare is not None:
                    positional, keywords = prepare(positional, keywords)
                context = before(positional, keywords) if before is not None else None
                checkpoint()
                count = count_for(label)
                count["started"] += 1
                began = perf_counter()
                try:
                    value = original(*positional, **keywords)
                    count["completed"] += 1
                except BaseException:
                    after_error_checkpoint()
                    raise
                finally:
                    count["elapsed_seconds"] += perf_counter() - began
                    if final is not None:
                        final()
                if after is not None:
                    after(value, positional, keywords, context)
                checkpoint()  # Actual delegate returned; completion is counted before this guard.
                return value
            patches.append((module, name, original))
            setattr(module, name, delegated)

        def constructor(value, positional, keywords, context):
            active["constructor_result_type"] = type(value).__module__ + "." + type(value).__name__
            assert type(value) is constructor_class

        def controller(positional, keywords):
            callback = keywords["on_accept"]
            case = active
            def accepted(measured):
                nonlocal current_stage
                current_stage = case["label"] + ":accepted_callback"
                checkpoint()
                count = count_for("accepted_callback")
                count["started"] += 1
                began = perf_counter()
                try:
                    callback(measured)  # Original accepted-cache capture first; no new mechanics.
                    count["completed"] += 1
                except BaseException:
                    after_error_checkpoint()
                    raise
                finally:
                    count["elapsed_seconds"] += perf_counter() - began
                row = {name: measured[name] for name in SCALARS}
                row.update(label=case["label"], case_index=len(case["accepted_scalar_prefix"]),
                           elapsed_seconds=perf_counter() - STARTED,
                           case_elapsed_seconds=perf_counter() - STARTED - case["started_helper_seconds"],
                           observed_F_T=dict(case["observed_F_T"]))
                case["accepted_scalar_prefix"].append(row)
                with progress_file.open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps(row, allow_nan=False) + "\n")
                print(json.dumps(row, allow_nan=False), flush=True)
                checkpoint()
            return positional, dict(keywords, on_accept=accepted)

        def solved(value, positional, keywords, context):
            # Metadata is plain dict/scalars. Never retain a NativeMeanResult between cases.
            active["original_result_metadata"] = deepcopy(value.metadata)

        def cached_before(positional, keywords):
            nonlocal writing
            result = positional[0]
            gates = protocol["gates"]
            rows = []
            for snapshot in result.accepted:
                record = snapshot.record
                fixed_max = max((abs(float(snapshot.state.lift[i]) + float(snapshot.state.fluctuation[i]))
                                 for i in result.project.model.fixed_dofs), default=0.)
                rows.append(dict(**{name: record[name] for name in SCALARS},
                    fixed_max_abs_displacement_mm=fixed_max,
                    positive_J=record["minimum_J"] > 0,
                    production_residual_pass=record["relative_residual"] <= float(gates["production_residual"]),
                    native_constraint_bound_pass=abs(record["constraint_residual"]) <= record["constraint_bound"],
                    global_force_balance_pass=record["relative_global_force_balance"] <= float(gates["global_force_balance"]),
                    fixed_displacement_pass=fixed_max <= float(gates["fixed_displacement_mm"])))
            active["production_gate_rows"] = rows
            active["production_gate_status"] = "checked" if rows else "not_checked"
            before = (dict(active["observed_F_T"]), dict(result.metadata["call_counts"]))
            writing = True
            return before

        def cached_after(value, positional, keywords, context):
            assert active["observed_F_T"] == context[0]
            assert positional[0].metadata["call_counts"] == context[1]
            active["cached_write_F_T_delta"] = dict(force_calls=0, tangent_calls=0)

        def cached_final():
            nonlocal writing
            writing = False

        def physical(module, name, kind):
            original = getattr(module, name)
            def delegated(*positional, **keywords):
                nonlocal current_stage
                current_stage = active["label"] + ":" + kind
                checkpoint()
                assert not writing, "Cached persistence attempted a new physical evaluation"
                observed = active["observed_F_T"]
                observed[kind + "_calls"] += 1
                began = perf_counter()
                try:
                    value = original(*positional, **keywords)
                    observed[kind + "_calls_completed"] += 1
                except BaseException:
                    after_error_checkpoint()
                    raise
                finally:
                    active.setdefault("F_T_seconds", dict(force=0., tangent=0.))[kind] += perf_counter() - began
                checkpoint()
                return value
            patches.append((module, name, original))
            setattr(module, name, delegated)

        install(native_project, "TMCModel", "constructor", after=constructor)
        install(native_mean, "build_native_project", "project_builder")
        install(native_mean, "solve_split_displacement_path", "controller", prepare=controller)
        install(native_evaluate, "solve_native_mean", "native_solve", after=solved)
        install(native_evaluate, "write_native_mean", "cached_writer", before=cached_before,
                after=cached_after, final=cached_final)
        install(native_evaluate, "summarize_saved_native_result", "formatter")
        install(native_evaluate, "write_native_response", "response_writer")
        install(native_mean, "_assemble_tangent", "tangent_assembly")
        physical(native_mean, "_assemble_force", "force")
        physical(native_mean, "_tangent", "tangent")

        def validate_success(case, response):
            metadata = case["original_result_metadata"]
            assert metadata is not None and metadata["status"] == "success"
            assert metadata["targets_mm"] == protocol["targets_mm"]
            assert metadata["task_target_executed"] is True
            assert metadata["accepted_states"] == len(case["accepted_scalar_prefix"])
            assert metadata["counts"] == protocol["expected_counts"][case["label"]]
            assert metadata["settings"] == response["invocation"]["settings"] == protocol["settings"]
            assert metadata["settings"]["tolerance"] == float(protocol["gates"]["production_residual"])
            assert metadata["settings"]["constraint_tolerance"] == float(protocol["gates"]["average_constraint"])
            for key in ("minimum_increment", "time_limit_seconds"):
                assert metadata["settings"][key] == protocol["options"][key]
            assert case["observed_F_T"] == {name: metadata["call_counts"][name] for name in F_T}
            assert metadata["call_counts"]["solver_invocations"] == 1
            assert metadata["call_counts"]["HP_calls"] == metadata["call_counts"]["JIT_calls"] == 0
            assert metadata["save_force_calls"] == metadata["save_tangent_calls"] == 0
            assert case["production_gate_status"] == "checked"
            assert len(case["production_gate_rows"]) == metadata["accepted_states"]
            assert all(row[name] for row in case["production_gate_rows"] for name in
                       ("positive_J", "production_residual_pass", "native_constraint_bound_pass",
                        "global_force_balance_pass", "fixed_displacement_pass"))
            assert all(response["options"][name]["value"] == protocol["options"][name]
                       for name in ("response_mode", "tangent_mode", "initial_guess"))
            assert response["target_response"]["d_mm"] == metadata["task_target_mm"]
            assert response["requested_endpoint_response"]["d_mm"] == protocol["targets_mm"][-1]
            assert response["path"]["task_target_executed"] is True
            assert response["target_response"]["workpiece"] is None
            assert all(flag is False for flag in response["producer_flags"].values())
            assert response["independent_reference"]["status"] == "not_provided"
            assert all(value is False for name, value in response["independent_reference"].items()
                       if name.endswith("_pass") or name.endswith("_qualified"))
            assert response["views"]["status"] == "not_provided"
            assert response["views"]["manifest"] is None and not response["views"]["links"]
            output = root / case["output"]
            assert read(output / "response.json") == response
            assert sha(output / "result.json") == response["identity"]["result"]["sha256"]
            saved = read(output / "result.json")
            model = read(output / saved["model"]["descriptor_path"])
            assert len(model["arrays"]["fields"]) == protocol["expected_model_fields"]
            assert saved["call_counts"] == metadata["call_counts"]
            assert saved["task_target_executed"] is True
            case["result_sha256"] = sha(output / "result.json")
            case["response_sha256"] = sha(output / "response.json")
            case["production_pass"] = True

        original_case_api = native_batch.evaluate_native
        def case_api(*positional, **keywords):
            nonlocal active, current_stage
            output = Path(positional[2]).resolve()
            label = next(plan["label"] for plan in plans if (root / plan["output"]).resolve() == output)
            active = cases[label]
            assert not active["attempted"]
            active.update(attempted=True, status="running", started_helper_seconds=perf_counter() - STARTED)
            current_stage = label + ":evaluate_native"
            count = count_for("evaluate_native")
            began = perf_counter()
            try:
                checkpoint()
                count["started"] += 1
                value = original_case_api(*positional, **keywords)  # One unchanged real API call.
                count["completed"] += 1
                active["returned_response"] = deepcopy(value)
                active["status"] = value["status"]
                checkpoint()
                released_at = perf_counter()
                active["cache_release"] = dict(invocations=1)
                gc.collect()  # Release unreachable recursive-controller/capture closures before the next case.
                active["cache_release"]["elapsed_seconds"] = perf_counter() - released_at
                checkpoint()
                if value["status"] == "success":
                    current_stage = label + ":case_validation"
                    validate_success(active, value)
                checkpoint()
                return value
            except BaseException as error:
                active.update(status="error", exception=failure(error, current_stage))
                after_error_checkpoint()
                raise
            finally:
                count["elapsed_seconds"] += perf_counter() - began
                active["elapsed_seconds"] = perf_counter() - began
                for name in ("result", "response"):
                    path = output / (name + ".json")
                    if path.is_file():
                        active[name + "_file"] = path.relative_to(root).as_posix()
                active = None  # Only scalar/JSON metadata remains before the next case starts.
        patches.append((native_batch, "evaluate_native", original_case_api))
        native_batch.evaluate_native = case_api

        original_cwd = Path.cwd()
        with tempfile.TemporaryDirectory(prefix="hf_real_native_batch_") as caller:
            caller_directory = Path(caller).resolve()
            assert not caller_directory.is_relative_to(root)
            receipt.update(caller_cwd=str(caller_directory), explicit_repo_root=str(root))
            try:
                os.chdir(caller_directory)
                current_stage = "evaluate_native_batch"
                checkpoint()
                receipt["batch_invocations"] = 1
                batch_index = native_batch.evaluate_native_batch(protocol["manifest_file"],
                    protocol["batch_directory"], repo_root=root)
                checkpoint()
            finally:
                os.chdir(original_cwd)
        assert receipt["batch_invocations"] == 1
        assert batch_index["status"] == "success", batch_index.get("failure_case")
        assert read(batch_directory / "index.json") == batch_index
        assert [entry["label"] for entry in batch_index["cases"]] == list(cases)
        assert batch_index["options"] == dict(protocol["options"], settings=None)
        assert batch_index["HF5_qualified"] is False and batch_index["ranking_qualified"] is False
        for entry in batch_index["cases"]:
            case = cases[entry["label"]]
            assert case["attempted"] and case["status"] == entry["status"] == "success"
            assert all(case["counts"][label]["started"] == case["counts"][label]["completed"] == 1 for label in ONCE)
            assert entry["output"]["path"] == case["output"]
            assert entry["response"]["path"] == case["response_file"]
            assert entry["response"]["sha256"] == case["response_sha256"]
            assert entry["call_counts"] == case["original_result_metadata"]["call_counts"]
            assert entry["path"]["task_target_executed"] is True
        assert cases["canonical"]["original_result_metadata"]["settings"] == cases["native_fine"]["original_result_metadata"]["settings"]
    except BaseException as error:
        exception = error
        receipt["exception"] = failure(error, current_stage)
    finally:
        for module, name, original in reversed(patches):
            setattr(module, name, original)
        try:
            outputs = {path.relative_to(root).as_posix(): sha(path)
                       for path in run.rglob("*") if path.is_file() and path != receipt_file}
            unchanged = all(sha(root / name) == pin for name, pin in pins.items())
            assert unchanged
            assert sha(protocol_file) == receipt["protocol_sha256"]
            assert sha(manifest_file) == receipt["manifest_sha256"]
            if "checkpoint" in locals():
                checkpoint()  # Whole-helper budget includes output and binding hashing.
        except BaseException as error:
            receipt["finalization_exception"] = failure(error, "finalization")
            if exception is None:
                exception = error
        index_file = batch_directory / "index.json"
        receipt.update(status="pass" if exception is None else "failed", cases=cases,
            outputs=outputs, batch_returned=batch_index,
            batch_index_file=index_file.relative_to(root).as_posix() if index_file.is_file() else None,
            elapsed_seconds=perf_counter() - STARTED, peak_sampled_RSS_bytes=peak,
            elapsed_scope="Whole helper through imports, all case delegates, index and final hashing/checkpoint; excludes this final receipt write, covered by the outer child monitor",
            all_bindings_unchanged=locals().get("unchanged", False),
            completed_utc=datetime.now(timezone.utc).isoformat(),
            callback_scope="Stage-only existing accepted scalars after original capture; original fixed-DOF cached gate is the sole inherited array check",
            retained_result_scope="No NativeMeanResult collection or cross-case retained result reference; only original metadata, responses, counters and scalar prefixes")
        write(receipt_file, receipt)
        print(json.dumps({key: receipt[key] for key in ("status", "elapsed_seconds", "peak_sampled_RSS_bytes", "batch_index_file")}), flush=True)
    if exception is not None:
        raise exception


if __name__ == "__main__":
    main()
