"""Candidate W-API1: one real batch/API call with cooperative observations only."""
from time import perf_counter
STARTED = perf_counter()
from pathlib import Path
import argparse
import hashlib
import json
import sys
from math import fsum

STAGE = "lf_data_preparation/native_interface_001/workpiece_forward_001"
MANIFEST = "hf_repo/configs/native/fixed_square_cycle.json"
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
read = lambda path: json.loads(path.read_bytes())


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    args = parser.parse_args()
    root = args.repo.resolve()
    protocol_file = (args.protocol if args.protocol.is_absolute() else root / args.protocol).resolve()
    protocol = read(protocol_file)
    assert {key: protocol["gates"][key] for key in ("production_residual", "global_force_balance", "fixed_displacement_mm")} == dict(production_residual="1e-9", global_force_balance="1e-6", fixed_displacement_mm="8e-11")
    stage, run, limits = root / STAGE, root / STAGE / "run_001", protocol["phases"]["production"]
    assert protocol_file.parent == stage and protocol["manifest_file"] == MANIFEST
    assert limits["helper_seconds"] == 4500 and limits["outer_seconds"] == 4560 and protocol["sampled_RSS_bytes"] == 8*1024**3
    pins, manifest = protocol["bindings"], read(root / MANIFEST)
    assert all(sha(root / name) == pin for name, pin in pins.items())
    assert len(manifest["cases"]) == 1 and manifest["cases"][0]["output"] == STAGE + "/run_001/fixed_square"
    assert manifest["options"]["response_mode"] == "mechanical" and manifest["options"]["tangent_mode"] == "chunk256" and manifest["options"]["initial_guess"] == "port_projection"
    assert not run.exists() and not (stage / "stop_requested.txt").exists()
    run.mkdir()
    receipt_file, progress = run / "execution_receipt.json", run / "accepted_progress.jsonl"
    counts = dict(batch_calls=0, **{kind + suffix: 0 for kind in ("api", "model", "solve", "force", "tangent", "save", "summary") for suffix in ("_started", "_completed")})
    receipt = dict(schema_version="native-workpiece-api-forward-execution-1.0", status="running",
        protocol_sha256=sha(protocol_file), counts=counts, accepted_states=0, HP_calls=0, JIT_calls=0,
        qualification_scope="New production transport only; no independent reference/view/contact/pressure/HF5 qualification")
    write(receipt_file, receipt)
    peak, error = 0, None
    try:
        import psutil
        process = psutil.Process()

        def checkpoint():
            nonlocal peak
            memory = process.memory_info()
            peak = max(peak, memory.rss, getattr(memory, "peak_wset", memory.rss))
            if (stage / "stop_requested.txt").exists():
                raise RuntimeError("external_stop_requested")
            if peak > protocol["sampled_RSS_bytes"]:
                raise RuntimeError("sampled_RSS_limit")
            if perf_counter() - STARTED > limits["helper_seconds"]:
                raise RuntimeError("whole_helper_elapsed_limit")

        checkpoint()
        sys.path.insert(0, str(root / "hf_repo/src"))
        from hf_eval import native_batch, native_evaluate, native_mean
        checkpoint()

        def observed(delegate, kind):
            def call(*values, **options):
                checkpoint()
                counts[kind + "_started"] += 1
                before = tuple(counts[key] for key in ("force_started", "force_completed", "tangent_started", "tangent_completed")) if kind in ("save", "summary") else None
                try:
                    value = delegate(*values, **options)
                except BaseException:
                    checkpoint()
                    raise  # Preserve the original recoverable trial error for the controller.
                counts[kind + "_completed"] += 1
                if kind in ("save", "summary"):
                    assert before == tuple(counts[key] for key in ("force_started", "force_completed", "tangent_started", "tangent_completed"))
                    receipt[kind + "_extra_force_tangent_calls"] = 0
                checkpoint()
                return value
            return call

        native_mean._assemble_mechanical_force = observed(native_mean._assemble_mechanical_force, "force")
        native_mean._tangent_chunked = observed(native_mean._tangent_chunked, "tangent")
        native_mean.build_native_project = observed(native_mean.build_native_project, "model")
        native_batch.evaluate_native = observed(native_batch.evaluate_native, "api")
        native_evaluate.write_native_mean = observed(native_evaluate.write_native_mean, "save")
        native_evaluate.summarize_saved_native_result = observed(native_evaluate.summarize_saved_native_result, "summary")
        original_solve = native_evaluate.solve_native_mean

        def solve(*values, **options):
            prior = options.get("on_accept")

            def accepted(snapshot):
                if prior is not None:
                    prior(snapshot)
                row = {key: snapshot.record[key] for key in ("d", "R_input", "q_in", "q_out", "relative_residual", "state_sha256", "leg", "original_target_index")}
                row.update(index=receipt["accepted_states"], elapsed_seconds=perf_counter() - STARTED)
                with progress.open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps(row, allow_nan=False) + "\n")
                receipt["accepted_states"] += 1
                checkpoint()  # Flush original captured acceptance before any resource escape.

            options["on_accept"] = accepted
            result = observed(original_solve, "solve")(*values, **options)
            rows, gates = [snapshot.record for snapshot in result.accepted], protocol["gates"]
            minimum_J = min((float(snapshot.arrays["J"].min()) for snapshot in result.accepted), default=None)
            fixed = max((abs(fsum((float(snapshot.state.lift[i]), float(snapshot.state.fluctuation[i])))) for snapshot in result.accepted for i in result.project.model.fixed_dofs), default=0.)
            cached = dict(actual_accepted_states=len(rows), minimum_J=minimum_J,
                maximum_relative_residual=max((row["relative_residual"] for row in rows), default=0.),
                maximum_abs_constraint_residual_mm=max((abs(row["constraint_residual"]) for row in rows), default=0.),
                native_constraint_bound_pass=all(abs(row["constraint_residual"]) <= row["constraint_bound"] for row in rows),
                maximum_relative_global_force_balance=max((row["relative_global_force_balance"] for row in rows), default=0.), maximum_fixed_split_sum_mm=fixed)
            cached["passed"] = bool(rows) and minimum_J > 0 and cached["maximum_relative_residual"] <= float(gates["production_residual"]) and cached["native_constraint_bound_pass"] and cached["maximum_relative_global_force_balance"] <= float(gates["global_force_balance"]) and fixed <= float(gates["fixed_displacement_mm"])
            receipt["cached_production_gates"] = cached
            checkpoint()
            return result  # Even a normal controller partial return proceeds to the existing cached writer.

        native_evaluate.solve_native_mean = solve
        checkpoint()
        counts["batch_calls"] += 1
        index = native_batch.evaluate_native_batch(root / MANIFEST, run / "batch", repo_root=root)
        checkpoint()
        receipt.update(batch_status=index["status"], failure_case=index["failure_case"])
        if index["status"] != "success":
            raise RuntimeError("Batch terminal non-success: " + str(index["failure_case"]))
        assert counts["batch_calls"] == 1 and all(counts[kind + suffix] == 1 for kind in ("api", "model", "solve", "save", "summary") for suffix in ("_started", "_completed"))
        result = read(run / "fixed_square/result.json")
        assert result["status"] == "success" and result["task_target_executed"] is True
        assert receipt["accepted_states"] == result["accepted_states"] == len(result["states"])
        task, response = read(root / manifest["cases"][0]["task"]), read(run / "fixed_square/response.json")
        assert result["targets_mm"] == task["path"]["targets_mm"] and result["task_target_mm"] == task["input"]["target_mm"] and result["path_completed"] is True
        assert result["settings"] == manifest["options"]["settings"] and result["response_mode"] == "mechanical" and result["tangent_execution"]["mode"] == "chunk256" and result["initial_guess"] == "port_projection"
        assert response["path"]["requested_targets_mm"] == task["path"]["targets_mm"] and all(value is False for value in response["producer_flags"].values())
        assert response["independent_reference"]["status"] == response["views"]["status"] == "not_provided" and receipt["cached_production_gates"]["passed"]
        for kind in ("force", "tangent"):
            assert counts[kind + "_started"] == result["call_counts"][kind + "_calls"]
            assert counts[kind + "_completed"] == result["call_counts"][kind + "_calls_completed"]
        receipt["call_counts"] = result["call_counts"]
        assert result["call_counts"]["HP_calls"] == result["call_counts"]["JIT_calls"] == 0
        receipt["requested_targets_mm"] = result["targets_mm"]
    except BaseException as exception:
        error = exception
        receipt["exception"] = dict(exception_class=type(exception).__name__, reason=str(exception))
    finally:
        try:
            receipt["outputs"] = {path.relative_to(root).as_posix(): sha(path) for path in run.rglob("*") if path.is_file() and path != receipt_file}
            receipt["all_bindings_unchanged"] = all(sha(root / name) == pin for name, pin in pins.items())
            assert receipt["all_bindings_unchanged"]
            if "checkpoint" in locals():
                checkpoint()
        except BaseException as exception:
            receipt["finalization_exception"] = dict(exception_class=type(exception).__name__, reason=str(exception))
            error = error or exception
        receipt.update(status="pass" if error is None else "not_pass", elapsed_seconds=perf_counter() - STARTED,
            peak_sampled_RSS_bytes=peak, elapsed_scope="Imports, one batch/API path, cached persistence and final hashing/checkpoint; final receipt write covered by outer child termination")
        write(receipt_file, receipt)
        print(json.dumps({key: receipt[key] for key in ("status", "accepted_states", "elapsed_seconds", "peak_sampled_RSS_bytes")}), flush=True)
    if error is not None:
        raise error


if __name__ == "__main__":
    main()
