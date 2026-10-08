"""Read-only B-VIEW2 closure: JSON/CSV, opaque file SHA, PNG/GIF structure; no science."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import argparse
import csv
import json
import struct

PRODUCTION = "lf_data_preparation/native_interface_001/batch_forward_001"
REFERENCE = "lf_data_preparation/native_interface_001/batch_reference_v2_001"
STAGE = "lf_data_preparation/native_interface_001/batch_saved_view_v2_001"
PROTOCOL_PIN = "116c22dab40635d5b144a99a6ebe57cf13963935d987cdbe2b6bc9ddd4f30866"
ZERO = ("force_calls", "tangent_calls", "solver_calls", "HP_calls", "model_constructions")
sha = lambda path: sha256(path.read_bytes()).hexdigest()
read = lambda path: json.loads(path.read_bytes())


def media_header(path):
    raw = path.read_bytes()
    if path.suffix == ".png":
        assert raw[:8] == b"\x89PNG\r\n\x1a\n" and raw[12:16] == b"IHDR"
        return dict(pixels=list(struct.unpack(">II", raw[16:24])), frames=1)
    assert raw[:6] in (b"GIF87a", b"GIF89a")
    pixels, packed, position, frames = list(struct.unpack("<HH", raw[6:10])), raw[10], 13, 0
    if packed & 128:
        position += 3 * (2 ** ((packed & 7) + 1))

    def skip_blocks(position):
        while True:
            size = raw[position]
            position += 1
            if size == 0:
                return position
            position += size
            assert position <= len(raw)

    while position < len(raw):
        tag = raw[position]
        if tag == 0x3B:
            assert position == len(raw) - 1
            return dict(pixels=pixels, frames=frames)
        if tag == 0x21:
            position = skip_blocks(position + 2)
        else:
            assert tag == 0x2C
            left, top, width, height = struct.unpack("<HHHH", raw[position + 1:position + 9])
            assert width > 0 and height > 0 and left + width <= pixels[0] and top + height <= pixels[1]
            packed = raw[position + 9]
            position += 10
            if packed & 128:
                position += 3 * (2 ** ((packed & 7) + 1))
            position = skip_blocks(position + 1)  # Skip LZW minimum size, then compressed blocks unchanged.
            frames += 1
    raise AssertionError("GIF trailer missing")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--prior-review", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root, output = args.repo.resolve(), args.output.resolve()
    assert not output.is_relative_to(root)
    checked, report = {}, dict(schema_version="native-batch-saved-view-v2-closure-review-1.0",
        status="closed_not_pass", reviewed_utc=datetime.now(timezone.utc).isoformat(), blocking_findings=[], cases={},
        original_production_unchanged=False, references_unchanged=False, prior_raw_identity_unchanged=False,
        activities=dict(candidate_imports=0, HF_imports=0, NPZ_loads=0, scientific_calculations=0,
                        F=0, T=0, HP=0, solver=0, model=0, geometry=0, render=0, launcher=0, formal_writes=0))

    def pin(name, expected=None):
        actual = sha(root / name)
        assert expected is None or actual == expected, name
        assert name not in checked or checked[name] == actual, name
        checked[name] = actual
        return actual

    def pins(mapping, prefix=""):
        for name, expected in mapping.items():
            pin(prefix + name, expected)

    try:
        protocol_name = STAGE + "/view_protocol.json"
        assert pin(protocol_name) == PROTOCOL_PIN
        protocol = read(root / protocol_name)
        launch_name, receipt_name = STAGE + "/view_launch.json", PRODUCTION + "/run_001/view_execution_receipt.json"
        launch, receipt = read(root / launch_name), read(root / receipt_name)
        pin(launch_name)
        pin(receipt_name)
        assert launch["phase"] == "view" and launch["status"] == receipt["status"] == "pass"
        assert launch["invocations"] == receipt["invocations"] == 1 and launch["exit_code"] == 0 and launch["stop_reason"] is None
        assert launch["protocol_sha256"] == receipt["protocol_sha256"] == PROTOCOL_PIN
        assert launch["all_bindings_unchanged"] is receipt["all_bindings_unchanged"] is True
        limits = protocol["phases"]["view"]
        assert limits["helper_seconds"] == 120 and limits["outer_seconds"] == 150 and protocol["sampled_RSS_bytes"] == 8*1024**3
        assert receipt["elapsed_seconds"] <= 120 and launch["elapsed_seconds"] <= 150
        assert receipt["peak_sampled_RSS_bytes"] <= 8*1024**3 and launch["peak_sampled_tree_RSS_bytes"] <= 8*1024**3
        assert launch["argv"][1] == "-B" and launch["argv"][2:] == limits["argv"]
        assert launch["bindings"] == protocol["bindings"] and not (root / STAGE / "stop_requested.txt").exists()
        assert len(protocol["bindings"]) == 245 and len(receipt["outputs"]) == 19
        pins(protocol["bindings"])
        pins(receipt["outputs"])
        assert all(receipt[key] == 0 for key in ZERO)
        report["view_terminal"] = dict(worker_status=receipt["status"], outer_status=launch["status"], invocations=1,
            helper_seconds=receipt["elapsed_seconds"], outer_seconds=launch["elapsed_seconds"],
            worker_peak_sampled_RSS_bytes=receipt["peak_sampled_RSS_bytes"], outer_peak_sampled_tree_RSS_bytes=launch["peak_sampled_tree_RSS_bytes"],
            protocol_bindings=len(protocol["bindings"]), saved_outputs=len(receipt["outputs"]), elapsed_scope=receipt["elapsed_scope"])
        production, original = read(root / PRODUCTION / "production_protocol.json"), read(root / PRODUCTION / "run_001/execution_receipt.json")
        assert original["status"] == "pass" and len(production["bindings"]) == 52 and len(original["outputs"]) == 54
        pins(production["bindings"])
        pins(original["outputs"])
        report["original_production_unchanged"] = True
        report["production_hash_counts"] = dict(bindings=52, outputs=54)
        prior = read(args.prior_review.resolve())
        assert prior["status"] == "pass_saved_only" and prior["unique_raw_files_checked"] == len(prior["raw_identity_sha256"]) == 290
        pins(prior["raw_identity_sha256"])
        report["prior_raw_identity_unchanged"] = True
        report["prior_review"] = dict(path=str(args.prior_review.resolve()), sha256=sha(args.prior_review.resolve()), raw_pins_checked=290)
        failed = read(root / PRODUCTION / "run_001/audit/canonical/execution_receipt.json")
        assert failed["status"] == "not_pass" and failed["HP_calls_started"] == failed["HP_calls_completed"] == 0
        report["V1_failed_reference_preserved"] = dict(status=failed["status"], HP_calls_started=0, HP_calls_completed=0)
        view = PRODUCTION + "/run_001/view"
        manifest_name = view + "/manifest.json"
        manifest = read(root / manifest_name)
        manifest_pin = pin(manifest_name)
        assert manifest["status"] == "pass" and all(manifest[key] == 0 for key in ZERO)
        assert [case["label"] for case in manifest["cases"]] == ["canonical", "native_fine"]
        pins(manifest["outputs"], view + "/")
        pins(manifest["input_source_bindings"])
        assert {path.relative_to(root / view).as_posix() for path in (root / view).rglob("*") if path.is_file()} == set(manifest["outputs"]) | {"manifest.json"}
        for plan, manifest_case in zip(protocol["cases"], manifest["cases"]):
            label, base = plan["label"], PRODUCTION + "/run_001/" + plan["label"]
            result = read(root / plan["result_file"])
            model = read(root / base / result["model"]["descriptor_path"])
            audit = read(root / plan["audit_file"])
            raw_name = REFERENCE + "/run_001/audit/" + label + "/summary.json"
            raw = read(root / raw_name)
            reference_receipt = read(root / REFERENCE / "run_001/audit" / label / "execution_receipt.json")
            reference_launch = read(root / REFERENCE / ("reference_" + label + "_launch.json"))
            assert reference_receipt["status"] == reference_launch["status"] == "pass" and reference_launch["exit_code"] == 0
            assert reference_receipt["accepted_states"] == len(result["states"]) == 4
            assert reference_receipt["HP_calls_started"] == reference_receipt["HP_calls_completed"] == audit["HP_calls_started"] == audit["HP_calls_completed"] == 8
            assert audit["status"] == raw["status"] == "pass" and audit["case_label"] == label
            assert reference_receipt["summary_sha256"] == pin(raw_name) and reference_receipt["qualified_summary_sha256"] == pin(plan["audit_file"])
            assert audit["original_summary"] == dict(path="summary.json", sha256=pin(raw_name))
            assert all(audit[key] == value for key, value in raw.items() if key not in ("alias", "qualification"))
            assert len(audit["source_bindings"]) == 35
            pins(audit["source_bindings"])
            pins(audit["input_bindings"])
            metadata_name, summary_name = view + "/" + label + "/view_metadata.json", view + "/" + label + "/summary.json"
            metadata, summary = read(root / metadata_name), read(root / summary_name)
            assert receipt["cases"][label]["status"] == "pass" and all(receipt["cases"][label][key] == 0 for key in ZERO)
            assert metadata["case_label"] == manifest_case["label"] == label
            assert metadata["result_sha256"] == audit["result_sha256"] == reference_receipt["result_sha256"] == pin(plan["result_file"])
            assert metadata["audit_summary_sha256"] == pin(plan["audit_file"]) and metadata["original_audit_summary"] == audit["original_summary"]
            assert metadata["task_sha256"] == result["task_sha256"] == model["task_sha256"]
            assert metadata["geometry_id"] == model["source_geometry"]["geometry_id"] == result["source_geometry"]["geometry_id"]
            assert metadata["grid"] == result["grid"] == model["grid"] and metadata["counts"] == result["counts"]
            assert manifest_case["task"] == model["task"] and manifest_case["model_sha256"] == model["arrays"]["sha256"]
            assert manifest_case["saved_accepted_states"] == manifest_case["observed_states"] == summary["accepted_states"] == plan["accepted_states"] == 4
            assert summary["production_status"] == manifest_case["production_status"] == result["status"] == "success"
            assert metadata["viewer_sha256"] == pin(view + "/" + label + "/plot_native_mean_frozen.py") == pin(protocol["viewer_file"])
            assert metadata["adapter_sha256"] == pin(view + "/" + label + "/cached_view_adapter_frozen.py") == pin(protocol["adapter_file"])
            assert metadata["frozen_helpers_sha256"]["helpers/data.py"] == pin(view + "/" + label + "/helpers/data.py") == pin("hf_repo/src/hf_eval/data.py")
            pins(metadata["input_files_sha256"])
            assert metadata["audit_source_bindings"] == audit["source_bindings"]
            rows, saved, checked_audits = metadata["numerical_states"], result["states"], audit["states"]
            assert len(rows) == len(summary["rows"]) == len(metadata["audit_states"]) == 4 and metadata["final_numbers"] == rows[-1]
            scalar_keys = dict(target_mm="d", q_in_mm="q_in", R_input_N="R_input", q_out_mm="q_out", minimum_J="minimum_J",
                               relative_residual="relative_residual", constraint_residual_mm="constraint_residual",
                               relative_global_force_balance="relative_global_force_balance")
            for index, (row, state, audit_row, summary_row) in enumerate(zip(rows, saved, checked_audits, summary["rows"])):
                assert row["index"] == summary_row["index"] == audit_row["index"] == index
                assert summary_row == dict(row, state_sha256=state["state_sha256"], d_mm=state["d"])
                assert audit_row["state_sha256"] == state["state_sha256"] and audit_row["target_mm"] == state["d"] and audit_row["HP_calls"] == 2
                assert metadata["audit_states"][index] == {key: audit_row[key] for key in ("index", "state_sha256", "target_mm", "status", "metrics")}
                assert all(row[key] == state[value] for key, value in scalar_keys.items())
                assert row["hp_relative_residual"] == float(audit_row["metrics"]["independent_relative_residual"])
                assert row["hp_relative_constraint"] == float(audit_row["metrics"]["relative_constraint"]) and row["hp_relative_force_balance"] == float(audit_row["metrics"]["relative_force_balance"])
            csv_name = view + "/" + label + "/numeric_states.csv"
            assert pin(csv_name) == metadata["numeric_states_csv_sha256"]
            with (root / csv_name).open(encoding="utf-8", newline="") as stream:
                csv_rows = list(csv.DictReader(stream))
            assert len(csv_rows) == 4 and all(set(saved_row) == set(row) and all(float(saved_row[key]) == value for key, value in row.items()) for saved_row, row in zip(csv_rows, rows))
            port, display = model["region_metadata"]["ports"]["input"], metadata["display"]
            assert metadata["input_nodes"] == [dof // 2 for dof in port["nonzero_dofs"]] == display["input_arrow_nodes"]
            assert len(metadata["input_nodes"]) == plan["input_node_count"] == dict(canonical=3, native_fine=5)[label]
            assert metadata["input_weights"] == port["weights"] and port["direction"] == [1., 0.]
            assert display["geometry_scale"] == 1. and display["supplementary_displacement_scale"] == 40. and display["supplementary_force_arrows"] is False
            assert display["actual_frame_count"] == 4 and display["interpolated_frames"] == 0 and display["all_element_J_colored"] is True
            media = {}
            for name in ("native_mean_path.png", "native_mean_path.gif"):
                path_name = view + "/" + label + "/" + name
                actual = dict(sha256=pin(path_name), **media_header(root / path_name))
                assert actual == metadata["media"][name]
                assert actual["frames"] == (4 if name.endswith(".gif") else 1)
                assert manifest["outputs"][label + "/" + name] == receipt["outputs"][path_name] == actual["sha256"]
                media[name] = actual
            assert all(metadata[key] == 0 for key in ZERO)
            assert metadata["independent_saved_state_audit_passed"] is metadata["task_target_executed"] is metadata["native_grid_saved_state_viewed"] is True
            assert all(metadata[key] is False for key in ("mesh_convergence_qualified", "HF5_qualified", "contact_clamping_claim", "half_model_quantities_doubled"))
            response = read(root / plan["qualified_response_file"])
            identity, reference, views = response["identity"], response["independent_reference"], response["views"]
            assert identity["result"]["path"] == plan["result_file"] and identity["result"]["sha256"] == pin(plan["result_file"])
            assert identity["model"]["sha256"] == result["model"]["descriptor_file_sha256"]
            assert response["path"]["accepted_states"] == 4 and response["path"]["completed"] is response["path"]["task_target_executed"] is True
            assert reference["status"] == "matched" and reference["accepted_reference_pass"] is reference["full_path_reference_pass"] is reference["source_bindings_verified"] is True
            assert reference["report"]["path"] == plan["audit_file"] and reference["report"]["sha256"] == pin(plan["audit_file"])
            assert all(reference[key] is False for key in ("HP_all_columns_qualified", "contact_qualified", "clamp_qualified", "pressure_qualified", "HF5_qualified"))
            assert all(value is False for value in response["producer_flags"].values())
            assert views["status"] == "matched" and views["case_label"] == label and views["manifest"]["path"] == manifest_name and views["manifest"]["sha256"] == manifest_pin
            assert {link["path"] for link in views["links"]} == {view + "/" + label + "/" + name for name in media} and len(views["links"]) == 2
            assert all(link["path_scope"] == "repo_relative" and link["sha256"] == pin(link["path"]) for link in views["links"])
            assert response["target_response"]["state_sha256"] == saved[-1]["state_sha256"] and response["target_response"]["d_mm"] == .025
            assert all(response["target_response"][key] == rows[-1][key] for key in ("R_input_N", "q_in_mm", "q_out_mm", "minimum_J"))
            report["cases"][label] = dict(status="pass_saved_only", actual_accepted_states=4, actual_GIF_frames=media["native_mean_path.gif"]["frames"], input_nodes=len(metadata["input_nodes"]),
                reference_HP_started=8, reference_HP_completed=8, source_count=35, media=media,
                qualified_response_sha256=pin(plan["qualified_response_file"]), view_metadata_sha256=pin(metadata_name),
                result_sha256=pin(plan["result_file"]), qualified_audit_sha256=pin(plan["audit_file"]), raw_audit_sha256=pin(raw_name),
                final_cached_numbers=dict(target_mm=rows[-1]["target_mm"], R_input_N=rows[-1]["R_input_N"], q_out_mm=rows[-1]["q_out_mm"], minimum_J=rows[-1]["minimum_J"]),
                scope="Actual saved records and media only; numerical values matched, not recomputed; both own PNG/GIF links verified; no mesh/contact/pressure/HF5 upgrade")
        pins(receipt["original_responses_sha256"])
        assert len(receipt["original_responses_sha256"]) == 2
        report.update(status="pass_saved_only", references_unchanged=True, scientific_recheck_performed=False,
                      visual_inspection="Root separately inspects actual PNGs; this report verifies bytes/media structure and recorded associations only")
    except BaseException as error:
        report["blocking_findings"].append(dict(exception_class=type(error).__name__, reason=str(error)))
    report.update(unique_files_checked=len(checked), checked_files_sha256=checked, review_recipe_sha256=sha(Path(__file__)))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("status", "blocking_findings", "unique_files_checked", "cases")}, ensure_ascii=False))
    if report["blocking_findings"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
