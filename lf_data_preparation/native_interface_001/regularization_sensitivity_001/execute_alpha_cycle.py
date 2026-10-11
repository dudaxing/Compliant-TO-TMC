"""Future M-ALPHA1: one alpha-only ordered prefix and its saved-state views.

The original native solver owns line search, trial rollback and bisection.
This wrapper observes calls/accepted caches; it never retries a terminal run.
"""
from time import perf_counter
STARTED = perf_counter()
from pathlib import Path
from hashlib import sha256
from math import fsum
import argparse
import json
import subprocess
import sys

STAGE = "lf_data_preparation/native_interface_001/regularization_sensitivity_001"
KINDS = ("batch", "api", "model", "solve", "force", "tangent", "save", "summary", "view_child")
MECHANICAL_COUNTS = ("force_started", "force_completed", "tangent_started", "tangent_completed")


def sha(path):
    digest = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024*1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    args = parser.parse_args()
    root, protocol_file = args.repo.resolve(), args.protocol.resolve()
    protocol = read(protocol_file)
    stage, run = root/STAGE, root/STAGE/"run_001"
    limits, pins = protocol["phases"]["production"], protocol["bindings"]
    manifest_file = root/protocol["manifest_file"]
    manifest = read(manifest_file)
    assert protocol_file.parent == stage and len(manifest["cases"]) == 1
    case, options = manifest["cases"][0], manifest["options"]
    candidate, view = root/protocol["candidate_directory"], root/protocol["view_directory"]
    assert case["label"] == "alpha_half" and candidate == root/case["output"] == run/"alpha_half"
    assert view == run/"view" and limits["helper_seconds"] == 9600 and limits["outer_seconds"] == 9660
    assert protocol["view_seconds"] == 600 and protocol["sampled_RSS_bytes"] == 8*1024**3
    assert all(sha(root/name) == expected for name, expected in pins.items())
    authorization = read(stage/"author/authorization.json")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    assert authorization["authorized"] is True and authorization["card"] == "M-ALPHA1"
    assert authorization["protocol_sha256"] == sha(protocol_file) and authorization["approved_source_commit"] == head
    evidence_file = stage/"author/direct_human_reply.json"
    evidence = read(evidence_file)
    assert authorization["authorization_from_direct_human_reply"] is True
    assert evidence["authorization_from_direct_human_reply"] is True and evidence["card"] == "M-ALPHA1"
    assert isinstance(evidence["direct_human_answer"], str) and evidence["direct_human_answer"].strip() and evidence["reply_context"]
    assert evidence["approved_source_commit"] == head and authorization["direct_human_answer"] == evidence["direct_human_answer"]
    assert authorization["human_evidence_sha256"] == sha(evidence_file)
    baseline_file = root/protocol["baseline_result"]
    baseline, model = read(baseline_file), read(baseline_file.parent/"model/model.json")
    original, task = model["task"], read(root/case["task"])
    targets = protocol["targets_mm"]
    assert targets == original["path"]["targets_mm"][:15] and len(targets) == 15
    assert task["path"] == dict(kind="ordered_cycle", targets_mm=targets)
    assert original["regularization"] == dict(alpha=1e-6, length_mm=80.)
    assert task["regularization"] == dict(alpha=5e-7, length_mm=80.)
    ignored = {"task_id", "purpose", "parameter_origin", "description", "path", "regularization"}
    assert {k:v for k,v in task.items() if k not in ignored} == {k:v for k,v in original.items() if k not in ignored}
    assert task["third_medium"]["gamma"] == 1e-6
    geometry = read(root/case["geometry"])
    assert {k:geometry[k] for k in ("geometry_id", "descriptor_sha256")} == task["geometry"]
    assert sha(root/case["geometry"]) == model["source_geometry"]["descriptor_file_sha256"]
    settings = options["settings"]
    assert settings["time_limit_seconds"] == 9000.
    assert {k:v for k,v in settings.items() if k != "time_limit_seconds"} == {k:v for k,v in baseline["settings"].items() if k != "time_limit_seconds"}
    assert (options["response_mode"], options["tangent_mode"], options["initial_guess"]) == ("mechanical", "chunk256", "port_projection")
    gates = protocol["gates"]
    assert {k:float(v) for k,v in gates.items()} == dict(production_residual=1e-9, average_constraint=1e-10, global_force_balance=1e-6, fixed_displacement_mm=8e-11)
    assert not run.exists() and not (stage/"stop_requested.txt").exists()
    run.mkdir()
    receipt_file, progress = run/"execution_receipt.json", run/"accepted_progress.jsonl"
    counts = {kind+suffix:0 for kind in KINDS for suffix in ("_started", "_completed")}
    receipt = dict(schema_version="native-alpha-prefix-execution-1.0", status="running",
        protocol_sha256=sha(protocol_file), approved_source_commit=head,
        authorization_sha256=sha(stage/"author/authorization.json"), human_evidence_sha256=authorization["human_evidence_sha256"],
        counts=counts, accepted_states=0, HP_calls=0, JIT_calls=0,
        single_factor=dict(parameter="regularization.alpha", baseline=1e-6, candidate=5e-7),
        path_scope="Original 15-target prefix: load to 1.20 mm, one unload to 1.15 mm; fresh zero start",
        qualification_scope="Production and saved-state sensitivity only; no new independent reference, stability, pressure, clamp or HF5 qualification")
    write(receipt_file, receipt)
    peak, error = 0, None
    try:
        import psutil
        process = psutil.Process()

        def checkpoint():
            nonlocal peak
            memory = process.memory_info()
            peak = max(peak, memory.rss, getattr(memory, "peak_wset", memory.rss))
            if (stage/"stop_requested.txt").exists():
                raise RuntimeError("external_stop_requested")
            if peak > protocol["sampled_RSS_bytes"] or perf_counter()-STARTED > limits["helper_seconds"]:
                raise RuntimeError("whole_helper_resource_limit")

        def observed(delegate, kind):
            def call(*values, **keywords):
                checkpoint()
                counts[kind+"_started"] += 1
                before = tuple(counts[key] for key in MECHANICAL_COUNTS)
                try:
                    value = delegate(*values, **keywords)
                except BaseException:
                    checkpoint()
                    raise  # Preserve recoverable force errors for the original controller.
                counts[kind+"_completed"] += 1
                if kind in ("save", "summary"):
                    assert before == tuple(counts[key] for key in MECHANICAL_COUNTS)
                    receipt[kind+"_extra_force_tangent_calls"] = 0
                checkpoint()
                return value
            return call

        checkpoint()
        sys.path.insert(0, str(root/"hf_repo/src"))
        from hf_eval import native_batch, native_evaluate, native_mean
        native_mean._assemble_mechanical_force = observed(native_mean._assemble_mechanical_force, "force")
        native_mean._tangent_chunked = observed(native_mean._tangent_chunked, "tangent")
        original_model = native_mean.build_native_project

        def checked_model(*values, **keywords):
            project = original_model(*values, **keywords)
            actual, material = project.model, model["material"]
            expected = material | dict(alpha=5e-7, kr_MPa_mm2=material["kr_MPa_mm2"]*0.5)
            assert project.task == task and project.material == expected and actual.kr == expected["kr_MPa_mm2"]
            assert (actual.hx, actual.hy, actual.thickness, project.k_out) == (*model["grid"]["cell_size_mm"], material["thickness_mm"], original["output"]["spring_N_per_mm"])
            regions, original_regions = project.region_metadata, model["region_metadata"]
            excluded = {"source_geometry", "effective_boundary"}
            assert {k:v for k,v in regions.items() if k not in excluded} == {k:v for k,v in original_regions.items() if k not in excluded}
            assert regions["source_geometry"] == model["source_geometry"]
            assert {k:v for k,v in regions["effective_boundary"].items() if k != "task_sha256"} == {k:v for k,v in original_regions["effective_boundary"].items() if k != "task_sha256"}
            assert regions["effective_boundary"]["task_sha256"] == project.task_sha256
            assert counts["force_started"] == counts["tangent_started"] == 0
            receipt["constructor_single_factor_checked_before_first_force"] = True
            return project

        native_mean.build_native_project = observed(checked_model, "model")
        native_batch.evaluate_native = observed(native_batch.evaluate_native, "api")
        native_evaluate.write_native_mean = observed(native_evaluate.write_native_mean, "save")
        native_evaluate.summarize_saved_native_result = observed(native_evaluate.summarize_saved_native_result, "summary")
        original_solve = native_evaluate.solve_native_mean

        def solve(*values, **keywords):
            prior = keywords.get("on_accept")

            def accepted(snapshot):
                if prior is not None:
                    prior(snapshot)
                row = {key:snapshot.record[key] for key in ("d", "R_input", "q_in", "q_out", "relative_residual", "state_sha256", "leg", "original_target_index")}
                row.update(index=receipt["accepted_states"], elapsed_seconds=perf_counter()-STARTED)
                with progress.open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps(row, allow_nan=False)+"\n")
                receipt["accepted_states"] += 1
                checkpoint()

            keywords["on_accept"] = accepted
            result = observed(original_solve, "solve")(*values, **keywords)
            rows = [snapshot.record for snapshot in result.accepted]
            minimum_J = min((float(snapshot.arrays["J"].min()) for snapshot in result.accepted), default=None)
            fixed = max((abs(fsum((float(snapshot.state.lift[i]), float(snapshot.state.fluctuation[i])))) for snapshot in result.accepted for i in result.project.model.fixed_dofs), default=0.)
            cached = dict(actual_accepted_states=len(rows), minimum_J=minimum_J,
                maximum_relative_residual=max((row["relative_residual"] for row in rows), default=0.),
                maximum_abs_constraint_residual_mm=max((abs(row["constraint_residual"]) for row in rows), default=0.),
                native_constraint_bound_pass=all(abs(row["constraint_residual"]) <= row["constraint_bound"] for row in rows),
                maximum_relative_global_force_balance=max((row["relative_global_force_balance"] for row in rows), default=0.),
                maximum_fixed_split_sum_mm=fixed)
            cached["passed"] = bool(rows) and minimum_J > 0 and cached["maximum_relative_residual"] <= float(gates["production_residual"]) and cached["native_constraint_bound_pass"] and cached["maximum_relative_global_force_balance"] <= float(gates["global_force_balance"]) and fixed <= float(gates["fixed_displacement_mm"])
            receipt["cached_production_gates"] = cached
            return result  # The original writer preserves a normal partial controller return.

        native_evaluate.solve_native_mean = solve
        index = observed(native_batch.evaluate_native_batch, "batch")(manifest_file, run/"batch", repo_root=root)
        receipt.update(batch_status=index["status"], failure_case=index["failure_case"], batch_calls=counts["batch_started"])
        if index["status"] != "success":
            raise RuntimeError("Batch terminal non-success: "+str(index["failure_case"]))
        assert all(counts[kind+suffix] == 1 for kind in ("batch", "api", "model", "solve", "save", "summary") for suffix in ("_started", "_completed"))
        result, response = read(candidate/"result.json"), read(candidate/"response.json")
        assert result["status"] == "success" and result["path_completed"] and result["task_target_executed"]
        assert result["target_origin"] == 0. and result["loading_peak_reached"] and result["unload_endpoint_reached"]
        assert result["targets_mm"] == targets and result["settings"] == settings
        assert result["counts"] == model["region_metadata"]["counts"]
        assert receipt["accepted_states"] == result["accepted_states"] == len(result["states"])
        originals = [row for row in result["states"] if row["is_original_target"]]
        assert [row["original_target_index"] for row in originals] == list(range(15))
        for i, row in enumerate(originals):
            leg = "origin" if i == 0 else "loading" if targets[i] > targets[i-1] else "unloading"
            assert row["d"] == row["original_target_displacement"] == targets[i] and row["leg"] == leg
        assert receipt["cached_production_gates"]["passed"] and all(value is False for value in response["producer_flags"].values())
        assert response["independent_reference"]["status"] == response["views"]["status"] == "not_provided"
        for kind in ("force", "tangent"):
            assert counts[kind+"_started"] == result["call_counts"][kind+"_calls"]
            assert counts[kind+"_completed"] == result["call_counts"][kind+"_calls_completed"]
        assert result["call_counts"]["HP_calls"] == result["call_counts"]["JIT_calls"] == 0
        receipt.update(call_counts=result["call_counts"], requested_targets_mm=targets,
            original_target_states=len(originals), additional_bisection_states=len(result["states"])-len(originals))
        checkpoint()
        remaining = min(protocol["view_seconds"], limits["helper_seconds"]-(perf_counter()-STARTED))
        child_argv = [sys.executable, "-B", str(stage/"compare_alpha_views.py"), "--repo", str(root), "--protocol", str(protocol_file), "--time-limit", str(remaining)]
        observed(subprocess.run, "view_child")(child_argv, cwd=root, check=True)
        view_receipt = read(view/"alpha_view_receipt.json")
        assert view_receipt["status"] == "pass" and view_receipt["accepted_states"] == result["accepted_states"]
        receipt.update(view_receipt_file=(view/"alpha_view_receipt.json").relative_to(root).as_posix(),
            view_child_seconds_upper_bound=remaining, view_child_mechanical_hooks_monitored=False)
    except BaseException as exception:
        error = exception
        receipt["exception"] = dict(exception_class=type(exception).__name__, reason=str(exception))
    finally:
        try:
            receipt["outputs"] = {path.relative_to(root).as_posix():sha(path) for path in run.rglob("*") if path.is_file() and path != receipt_file}
            receipt["all_bindings_unchanged"] = all(sha(root/name) == expected for name, expected in pins.items())
            assert receipt["all_bindings_unchanged"]
            if "checkpoint" in locals():
                checkpoint()
        except BaseException as exception:
            receipt["finalization_exception"] = dict(exception_class=type(exception).__name__, reason=str(exception))
            error = error or exception
        receipt.update(status="pass" if error is None else "not_pass", elapsed_seconds=perf_counter()-STARTED,
            peak_sampled_RSS_bytes=peak, elapsed_scope="Imports, one native batch/API prefix, cached persistence, fresh saved-state view child and final hashing; receipt write and child exit included by outer")
        write(receipt_file, receipt)
        print(json.dumps({k:receipt[k] for k in ("status", "accepted_states", "elapsed_seconds", "peak_sampled_RSS_bytes")}), flush=True)
    if error is not None:
        raise error


if __name__ == "__main__":
    main()
