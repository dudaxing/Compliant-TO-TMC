"""Render each newly audited batch cache once; no mechanics or model construction."""
from time import perf_counter
STARTED = perf_counter()
from datetime import datetime, timezone
from pathlib import Path
import argparse
import csv
import gc
import hashlib
import importlib.util
import json
import sys

ZERO_CALLS = dict(force_calls=0, tangent_calls=0, solver_calls=0, HP_calls=0, model_constructions=0)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def module_from(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    args = parser.parse_args()
    root = args.repo.resolve()
    protocol_file = (args.protocol if args.protocol.is_absolute() else root / args.protocol).resolve()
    protocol = read(protocol_file)
    stage, limits = protocol_file.parent, protocol["phases"]["view"]
    pins = protocol["bindings"]
    assert all(sha(root / name) == pin for name, pin in pins.items())
    run = root / protocol["input_directory"]
    reference_run = root / protocol["reference_run"]
    assert run == root / "lf_data_preparation/native_interface_001/batch_forward_001/run_001"
    assert reference_run == root / "lf_data_preparation/native_interface_001/batch_reference_v2_001/run_001"
    view = root / protocol["view_directory"]
    assert view == run / "view" and not view.exists()
    receipt_file = run / "view_execution_receipt.json"
    assert not receipt_file.exists() and not (stage / "stop_requested.txt").exists()
    plans = protocol["cases"]
    assert [case["label"] for case in plans] == ["canonical", "native_fine"]
    assert protocol["display"] == dict(geometry_scale=1., supplementary_displacement_scale=40.)
    original_responses = {}
    for case in plans:
        label = case["label"]
        assert root / case["result_file"] == run / label / "result.json"
        assert root / case["audit_file"] == reference_run / "audit" / label / "qualified_summary.json"
        assert root / case["output_directory"] == view / label
        assert root / case["qualified_response_file"] == run / ("qualified_response_" + label + ".json")
        assert not (root / case["qualified_response_file"]).exists()
        result, audit = read(root / case["result_file"]), read(root / case["audit_file"])
        n = len(result["states"])
        assert result["status"] == "success" and result["task_target_executed"] is True
        assert result["accepted_states"] == audit["accepted_states"] == len(audit["states"]) == case["accepted_states"] == n
        assert audit["status"] == "pass" and audit["case_label"] == label
        assert audit["result_sha256"] == sha(root / case["result_file"])
        assert audit["HP_calls_started"] == audit["HP_calls_completed"] == 2*n
        assert result["targets_mm"] == case["targets_mm"] and result["task_target_mm"] == case["task_target_mm"]
        assert case["input_node_count"] == dict(canonical=3, native_fine=5)[label]
        original_response = (root / case["result_file"]).parent / "response.json"
        original_responses[original_response.relative_to(root).as_posix()] = sha(original_response)
    for role, dependency in protocol["prerequisites"].items():
        launch, receipt = read(root / dependency["launch_file"]), read(root / dependency["receipt_file"])
        control = read(root / dependency["protocol_file"])
        phase = control["phases"][dependency.get("phase", role)]
        assert launch["status"] == receipt["status"] == "pass"
        assert launch["invocations"] == 1 and launch["exit_code"] == 0 and launch["stop_reason"] is None
        assert launch["all_bindings_unchanged"] is receipt["all_bindings_unchanged"] is True
        assert launch["protocol_sha256"] == receipt["protocol_sha256"] == sha(root / dependency["protocol_file"])
        assert launch["elapsed_seconds"] <= phase["outer_seconds"]
        assert launch["peak_sampled_tree_RSS_bytes"] <= control["sampled_RSS_bytes"]
        assert receipt["elapsed_seconds"] <= phase["helper_seconds"]
        assert receipt[dependency["receipt_RSS_field"]] <= control["sampled_RSS_bytes"]
        if role.startswith("reference_"):
            label = role[len("reference_"):]
            case = next(case for case in plans if case["label"] == label)
            assert control["schema_version"] == "native-batch-case-reference-protocol-2.0"
            assert receipt["schema_version"] == "native-batch-case-reference-execution-2.0"
            assert control["case_label"] == label
            assert control["actual_accepted_states"] == case["accepted_states"]
            assert control["fresh_HP_calls_required"] == 2*case["accepted_states"]
            assert root / dependency["protocol_file"] == reference_run.parent / ("reference_protocol_" + label + ".json")
            assert root / dependency["launch_file"] == reference_run.parent / ("reference_" + label + "_launch.json")
            assert root / dependency["receipt_file"] == reference_run / "audit" / label / "execution_receipt.json"
            audit_file = root / case["audit_file"]
            audit = read(audit_file)
            assert receipt["case_label"] == label and receipt["accepted_states"] == case["accepted_states"]
            assert receipt["HP_calls_started"] == receipt["HP_calls_completed"] == 2*case["accepted_states"]
            assert receipt["qualified_summary_sha256"] == sha(audit_file)
            assert receipt["summary_sha256"] == audit["original_summary"]["sha256"]
            assert receipt["result_sha256"] == sha(root / case["result_file"])
    assert set(protocol["prerequisites"]) == {"production", "reference_canonical", "reference_native_fine"}
    receipt = dict(schema_version="native-batch-saved-view-execution-1.0", status="running",
        started_utc=datetime.now(timezone.utc).isoformat(), protocol_sha256=sha(protocol_file),
        seconds_limit=limits["helper_seconds"], sampled_RSS_limit_bytes=protocol["sampled_RSS_bytes"],
        invocations=1, cases={}, **ZERO_CALLS,
        scope="Current batch saved caches and each fresh passing all-state reference; original drawing mathematics with declared case paths/cardinality/captions only")
    write(receipt_file, receipt)
    peak, exception, manifest, outputs, current = 0, None, None, {}, "startup"
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
            elif perf_counter() - STARTED > limits["helper_seconds"]:
                receipt["stop_reason"] = "whole_helper_elapsed_limit"
            if receipt.get("stop_reason"):
                raise RuntimeError(receipt["stop_reason"])

        checkpoint()
        viewer_file, adapter_file = root / protocol["viewer_file"], root / protocol["adapter_file"]
        viewer = module_from(viewer_file, "fresh_batch_saved_viewer")
        adapter = module_from(adapter_file, "fresh_batch_cached_view_adapter")
        checkpoint()
        view.mkdir()
        cases, all_inputs = [], {}
        for case in plans:
            label, output = case["label"], root / case["output_directory"]
            current, began = label + ":load_saved", perf_counter()
            case_started = began
            report = receipt["cases"][label] = dict(status="running", accepted_states=case["accepted_states"], **ZERO_CALLS)
            checkpoint()
            model, metadata, result, states, audit, files = adapter.load_saved(viewer, root, case, checkpoint)
            checkpoint()
            report["load_seconds"] = perf_counter() - began
            current, began = label + ":numerical_rows", perf_counter()
            rows, input_dofs = adapter.numerical_rows(viewer, model, states, case["input_node_count"])
            checkpoint()
            report["cached_numeric_seconds"] = perf_counter() - began
            output.mkdir()
            h = metadata["grid"]["cell_size_mm"]
            caption = f"{label} native gripper; h=({h[0]:g},{h[1]:g}) mm; original lower half, free output."
            current, began = label + ":render", perf_counter()
            checkpoint()
            display = adapter.render(viewer, model, metadata, states, rows, input_dofs, output,
                protocol["display"]["supplementary_displacement_scale"], label, caption)
            checkpoint()
            report["render_seconds"] = perf_counter() - began
            with (output / "numeric_states.csv").open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
            frozen = output / "plot_native_mean_frozen.py"
            frozen.write_bytes(viewer_file.read_bytes())
            frozen_adapter = output / "cached_view_adapter_frozen.py"
            frozen_adapter.write_bytes(adapter_file.read_bytes())
            helper = output / "helpers/data.py"
            helper.parent.mkdir()
            helper.write_bytes((root / "hf_repo/src/hf_eval/data.py").read_bytes())
            media = {}
            for name in ("native_mean_path.png", "native_mean_path.gif"):
                path = output / name
                with viewer.Image.open(path) as image:
                    media[name] = dict(sha256=sha(path), pixels=list(image.size), frames=getattr(image, "n_frames", 1))
            n = case["accepted_states"]
            assert len(rows) == len(states) == display["actual_frame_count"] == media["native_mean_path.gif"]["frames"] == n
            assert display["geometry_scale"] == 1. and display["supplementary_displacement_scale"] == 40.
            assert display["interpolated_frames"] == 0 and display["supplementary_force_arrows"] is False
            view_metadata = dict(schema_version="native-batch-case-view-1.0", case_label=label,
                scope="Saved accepted states and this case's fresh independent saved-state audit only",
                geometry_id=metadata["source_geometry"]["geometry_id"], task_sha256=result["task_sha256"],
                grid=metadata["grid"], counts=result["counts"], material=metadata["material"],
                input_nodes=(input_dofs//2).tolist(), input_weights=model["b_in"][input_dofs].tolist(),
                output_direction=[0., 1.], display=display, numerical_states=rows, final_numbers=rows[-1],
                result_sha256=sha(root / case["result_file"]), audit_summary_sha256=sha(root / case["audit_file"]),
                original_audit_summary=dict(audit["original_summary"]), input_files_sha256=files,
                audit_source_bindings=audit["source_bindings"], units=dict(length="mm", force="N", J="dimensionless"),
                audit_states=[{k: s["audit"][k] for k in ("index", "state_sha256", "target_mm", "status", "metrics")} for s in states],
                independent_saved_state_audit_passed=True, task_target_executed=True,
                task_scope=f"{label}: actual native-grid free-output TEST targets {result['targets_mm']} mm",
                native_grid_saved_state_viewed=True, mesh_convergence_qualified=False,
                HF5_qualified=False, contact_clamping_claim=False, half_model_quantities_doubled=False,
                viewer_sha256=sha(frozen), adapter_sha256=sha(frozen_adapter),
                frozen_helpers_sha256={"helpers/data.py": sha(helper)}, media=media,
                numeric_states_csv_sha256=sha(output / "numeric_states.csv"), **ZERO_CALLS)
            write(output / "view_metadata.json", view_metadata)
            summary_rows = [dict(numbers, state_sha256=state["state_sha256"], d_mm=state["d"])
                            for state, numbers in zip(result["states"], rows)]
            write(output / "summary.json", dict(production_status=result["status"], accepted_states=n,
                rows=summary_rows, scope="Original cached renderer measurements; every actual accepted state of this case"))
            for name, pin in files.items():
                assert name not in all_inputs or all_inputs[name] == pin
                all_inputs[name] = pin
            cases.append(dict(label=label, production_status=result["status"], model_sha256=metadata["arrays"]["sha256"],
                task=metadata["task"], saved_accepted_states=n, observed_states=len(rows)))
            report.update(status="pass", elapsed_seconds=perf_counter() - case_started,
                          result_sha256=view_metadata["result_sha256"], audit_summary_sha256=view_metadata["audit_summary_sha256"],
                          observed_states=len(rows), GIF_frames=media["native_mean_path.gif"]["frames"])
            del model, states  # Do not carry the first case's saved arrays into the next case.
            checkpoint()
            gc.collect()
            checkpoint()
        current = "view_manifest"
        view_outputs = {path.relative_to(view).as_posix(): sha(path) for path in view.rglob("*") if path.is_file()}
        manifest = dict(schema_version="native-batch-saved-view-1.0", status="pass",
            input_source_bindings=all_inputs, outputs=view_outputs, cases=cases, **ZERO_CALLS,
            scope="Existing saved-cache drawing mathematics; each actual native design separately, no mesh/contact/pressure/HF5/ranking qualification")
        write(view / "manifest.json", manifest)
        checkpoint()
        sys.path.insert(0, str(root / "hf_repo/src"))
        from hf_eval.native_response import summarize_saved_native_result, write_native_response
        for case in plans:
            label = case["label"]
            current = label + ":saved_response"
            checkpoint()
            response = summarize_saved_native_result(root / case["result_file"], repo_root=root,
                reference_file=root / case["audit_file"], view_manifest=view / "manifest.json")
            checkpoint()
            assert response["independent_reference"]["accepted_reference_pass"] is True
            assert response["independent_reference"]["full_path_reference_pass"] is True
            assert response["views"]["status"] == "matched" and response["views"]["case_label"] == label
            assert len(response["views"]["links"]) == 2
            assert all(response["independent_reference"][name] is False for name in
                       ("HP_all_columns_qualified", "contact_qualified", "clamp_qualified", "pressure_qualified", "HF5_qualified"))
            assert all(value is False for value in response["producer_flags"].values())
            write_native_response(response, root / case["qualified_response_file"])
            checkpoint()
            receipt["cases"][label]["qualified_response_file"] = case["qualified_response_file"]
        assert all(sha(root / name) == pin for name, pin in original_responses.items())
    except BaseException as error:
        exception = error
        receipt["exception"] = dict(stage=current, exception_class=type(error).__name__, reason=str(error))
        label = current.split(":", 1)[0]
        if label in receipt["cases"] and receipt["cases"][label]["status"] == "running":
            receipt["cases"][label]["status"] = "failed"
    finally:
        try:
            outputs = {path.relative_to(root).as_posix(): sha(path) for path in view.rglob("*") if path.is_file()}
            for case in plans:
                path = root / case["qualified_response_file"]
                if path.is_file():
                    outputs[path.relative_to(root).as_posix()] = sha(path)
            unchanged = all(sha(root / name) == pin for name, pin in pins.items())
            assert unchanged and all(sha(root / name) == pin for name, pin in original_responses.items())
            if "checkpoint" in locals():
                checkpoint()
        except BaseException as error:
            receipt["finalization_exception"] = dict(exception_class=type(error).__name__, reason=str(error))
            if exception is None:
                exception = error
        if exception is not None and manifest is not None:
            manifest.update(status="failed", failure_scope="Whole saved-view phase failed; saved responses are attempted artifacts")
            write(view / "manifest.json", manifest)
            outputs[(view / "manifest.json").relative_to(root).as_posix()] = sha(view / "manifest.json")
        receipt.update(status="pass" if exception is None else "failed", outputs=outputs,
            all_bindings_unchanged=locals().get("unchanged", False), original_responses_sha256=original_responses,
            elapsed_seconds=perf_counter() - STARTED, peak_sampled_RSS_bytes=peak,
            elapsed_scope="Whole helper through imports, saved-cache loading/rendering, saved-response exports and final hashing/checkpoint; excludes final receipt write covered by outer monitor",
            completed_utc=datetime.now(timezone.utc).isoformat())
        write(receipt_file, receipt)
        print(json.dumps({key: receipt[key] for key in ("status", "elapsed_seconds", "peak_sampled_RSS_bytes")}), flush=True)
    if exception is not None:
        raise exception


if __name__ == "__main__":
    main()
