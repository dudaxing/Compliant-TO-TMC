"""Review genuine terminal M-ALPHA1 records; ordinary bytes/JSON/CSV only.

Never imports HF, opens NPZ fields, recomputes mechanics/differences or renders.
Source preparation alone creates no execution PASS. Run only after root reports
actual terminal completion; a failed execution is explicitly reported as failed.
"""
import argparse
import csv
from datetime import datetime, timezone
from hashlib import sha256
import json
from math import isfinite
from pathlib import Path
import struct
import subprocess

REL = "lf_data_preparation/native_interface_001/regularization_sensitivity_001"
SOURCE = "64a19f7d990d294d09f16145eae946e0edfa1580"
PROTOCOL_SHA = "430137c7e81cb12281937a6201519235fcc161de0503323684541c1c72b94d11"
ORIGIN = "https://github.com/dudaxing/Compliant-TO-TMC.git"
METRICS = ("R_input_N", "q_out_mm", "total_body_Fy_N", "material_body_Fy_N",
    "regularization_body_Fy_N", "cached_two_sided_normal_magnitude_sum_N", "tip_x_mm",
    "tip_y_mm", "tip_to_bottom_mm", "tip_to_left_mm", "tip_to_right_mm", "solid_min_J",
    "medium_min_J", "medium_max_abs_Hu_per_mm")


def read(path):
    return json.loads(path.read_bytes())


def optional(path):
    return read(path) if path.is_file() else None


def sha(path):
    value = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024*1024), b""):
            value.update(block)
    return value.hexdigest()


def table(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def matching_saved_rows(result, summary, rows):
    assert result["accepted_states"] == summary["accepted_states"] == len(result["states"]) == len(summary["rows"]) == len(rows)
    originals = {}
    for i, (state, derived, row) in enumerate(zip(result["states"], summary["rows"], rows)):
        assert derived["index"] == int(row["index"]) == i
        assert state["state_sha256"] == derived["state_sha256"] == row["state_sha256"]
        assert state["original_target_index"] == derived["original_target_index"] == int(row["original_target_index"])
        assert state["leg"] == derived["leg"] == row["leg"] and state["d"] == derived["d_mm"] == float(row["d_mm"])
        assert all(derived[k] == float(row[k]) and isfinite(derived[k]) for k in METRICS)
        if state["is_original_target"]:
            index = state["original_target_index"]
            assert index not in originals
            originals[index] = dict(derived, accepted_index=i)
    return originals


def check_success(root, protocol, helper, launch, hashes):
    run = root/REL/"run_001"
    candidate, view = root/protocol["candidate_directory"], root/protocol["view_directory"]
    result, response, model = read(candidate/"result.json"), read(candidate/"response.json"), read(candidate/"model/model.json")
    task, manifest = read(root/REL/"task.json"), read(root/protocol["manifest_file"])
    assert helper["all_bindings_unchanged"] and launch["all_bindings_unchanged"]
    assert launch["exit_code"] == 0 and launch["stop_reason"] is None
    assert not (root/REL/"stop_requested.txt").exists()
    assert "exception" not in helper and "finalization_exception" not in helper
    assert helper["constructor_single_factor_checked_before_first_force"] is True
    counts = helper["counts"]
    for kind in ("batch", "api", "model", "solve", "save", "summary", "view_child"):
        assert counts[kind+"_started"] == counts[kind+"_completed"] == 1
    for kind in ("force", "tangent"):
        assert counts[kind+"_started"] == result["call_counts"][kind+"_calls"]
        assert counts[kind+"_completed"] == result["call_counts"][kind+"_calls_completed"]
        assert counts[kind+"_started"] >= counts[kind+"_completed"] > 0
    assert helper["HP_calls"] == helper["JIT_calls"] == result["call_counts"]["HP_calls"] == result["call_counts"]["JIT_calls"] == 0
    assert helper["save_extra_force_tangent_calls"] == helper["summary_extra_force_tangent_calls"] == result["save_force_calls"] == result["save_tangent_calls"] == 0
    assert result["status"] == response["status"] == "success" and result["path_completed"] and result["unload_endpoint_reached"]
    assert result["loading_peak_reached"] and result["task_target_executed"] and result["target_origin"] == 0
    assert result["targets_mm"] == task["path"]["targets_mm"] == protocol["targets_mm"]
    assert result["settings"] == manifest["options"]["settings"] and result["counts"] == protocol["expected_counts"]
    assert response["call_counts"] == result["call_counts"]
    assert model["task"] == task and model["task_sha256"] == result["task_sha256"]
    assert response["identity"]["result"]["sha256"] == hashes[(candidate/"result.json").relative_to(root).as_posix()]
    assert response["identity"]["model"]["sha256"] == hashes[(candidate/"model/model.json").relative_to(root).as_posix()]
    assert response["identity"]["task_sha256"] == result["task_sha256"]
    assert all(v is False for v in response["producer_flags"].values())
    assert response["independent_reference"]["status"] == response["views"]["status"] == "not_provided"
    batch = read(run/"batch/index.json")
    assert batch["status"] == helper["batch_status"] == "success" and batch["failure_case"] is None
    assert len(batch["cases"]) == 1 and batch["cases"][0]["label"] == "alpha_half"
    assert batch["cases"][0]["status"] == "success" and batch["HF5_qualified"] is False
    states = result["states"]
    assert len(states) == helper["accepted_states"] == result["accepted_states"]
    originals = [state for state in states if state["is_original_target"]]
    assert [state["original_target_index"] for state in originals] == list(range(15))
    assert helper["original_target_states"] == 15 and helper["additional_bisection_states"] == len(states)-15
    cached = helper["cached_production_gates"]
    assert cached["passed"] is True and cached["actual_accepted_states"] == len(states) and cached["minimum_J"] > 0
    assert cached["maximum_relative_residual"] <= float(protocol["gates"]["production_residual"])
    assert cached["native_constraint_bound_pass"] is True
    assert cached["maximum_relative_global_force_balance"] <= float(protocol["gates"]["global_force_balance"])
    assert cached["maximum_fixed_split_sum_mm"] <= float(protocol["gates"]["fixed_displacement_mm"])
    progress = [json.loads(line) for line in (run/"accepted_progress.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(progress) == len(states)
    for i, state in enumerate(states):
        descriptor = candidate/state["descriptor_path"]
        assert read(descriptor) == {k:v for k,v in state.items() if k not in ("descriptor_path", "descriptor_file_sha256")}
        assert hashes[descriptor.relative_to(root).as_posix()] == state["descriptor_file_sha256"]
        assert state["minimum_J"] > 0 and state["relative_residual"] <= float(protocol["gates"]["production_residual"])
        assert abs(state["constraint_residual"]) <= state["constraint_bound"]
        assert state["relative_global_force_balance"] <= float(protocol["gates"]["global_force_balance"])
        assert progress[i]["index"] == i and all(progress[i][k] == state[k] for k in ("d", "R_input", "q_in", "q_out", "relative_residual", "state_sha256", "leg", "original_target_index"))
        for name in ("state", "forces", "tangents", "matrix"):
            assert hashes[(candidate/state[name]["path"]).relative_to(root).as_posix()] == state[name]["sha256"]
    for i, state in enumerate(originals):
        assert state["d"] == state["original_target_displacement"] == protocol["targets_mm"][i]
        assert state["leg"] == ("origin" if i == 0 else "loading" if i < 14 else "unloading")
    raw, vr = read(view/"view.json"), read(view/"alpha_view_receipt.json")
    assert raw["status"] == vr["status"] == "pass" and vr["accepted_states"] == len(states)
    assert raw["new_F_T_model_solver_HP_calls"] == vr["new_mechanical_calls"] == vr["new_baseline_observer_calls"] == 0
    assert raw["mechanical_hooks_monitored"] is False and vr["mechanical_hooks_monitored"] is False
    assert helper["view_child_mechanical_hooks_monitored"] is False
    assert vr["matched_original_targets"] == 15 and vr["all_bindings_unchanged"]
    assert vr["protocol_sha256"] == PROTOCOL_SHA and vr["raw_viewer_sha256"] == protocol["bindings"][protocol["viewer_source"]]
    for key in ("geometry_started", "geometry_completed", "nodal_started", "nodal_completed"):
        assert raw[key] == vr["actual_observation_counts"][key] == len(states)
    assert 0 < vr["elapsed_seconds"] <= helper["view_child_seconds_upper_bound"] <= 600
    assert vr["stability_pressure_clamp_HF5_qualified"] is False
    assert all(hashes[(view/n).relative_to(root).as_posix()] == pin for n,pin in raw["outputs"].items())
    baseline = matching_saved_rows(read(root/protocol["baseline_result"]), read(root/protocol["baseline_summary"]), table(root/protocol["baseline_csv"]))
    changed = matching_saved_rows(result, read(view/"alpha_half/summary.json"), table(view/"alpha_half/states.csv"))
    comparison, rows = read(view/"alpha_comparison.json"), table(view/"alpha_comparison.csv")
    assert comparison["status"] == "matched_saved_original_targets" and len(rows) == len(comparison["rows"]) == 15
    assert comparison["baseline_alpha"] == 1e-6 and comparison["candidate_alpha"] == 5e-7
    assert comparison["matched_original_targets"] == 15 and comparison["baseline_observer_calls"] == comparison["new_mechanical_calls"] == 0
    assert comparison["stability_qualified"] is False
    for i,(record,row) in enumerate(zip(comparison["rows"],rows)):
        assert record["original_target_index"] == int(row["original_target_index"]) == i
        for label, saved in (("baseline", baseline[i]), ("candidate", changed[i])):
            assert record[label+"_index"] == int(row[label+"_index"]) == saved["accepted_index"]
            assert record[label+"_state_sha256"] == row[label+"_state_sha256"] == saved["state_sha256"]
            assert record["d_mm"] == float(row["d_mm"]) == saved["d_mm"] and record["leg"] == row["leg"] == saved["leg"]
            assert all(record[label+"_"+k] == float(row[label+"_"+k]) == saved[k] for k in METRICS)
        assert all(record["candidate_minus_baseline_"+k] == float(row["candidate_minus_baseline_"+k]) for k in METRICS)
    pngs = {path.relative_to(view).as_posix() for path in view.rglob("*.png")}
    assert pngs == {"comparison.png", "distances_forces.png", "peak_fields.png", "alpha_response_comparison.png"}
    images = {}
    for name in sorted(pngs):
        with (view/name).open("rb") as stream:
            header = stream.read(24)
        assert header[:8] == b"\x89PNG\r\n\x1a\n" and header[12:16] == b"IHDR"
        images[name] = dict(IHDR_dimensions_descriptive_only=list(struct.unpack(">II", header[16:24])))
    gif = view/"alpha_half/actual_states.gif"
    with gif.open("rb") as stream:
        assert stream.read(6) in (b"GIF87a", b"GIF89a")
    return dict(actual_accepted_states=len(states), original_targets=15, additional_bisection_states=len(states)-15,
        counts=counts, cached_gates=cached, PNGs=images, actual_states_GIF=gif.relative_to(root).as_posix(),
        qualification="New alpha production and saved-view sensitivity only; no own HP/pressure/clamp/stability/HF5",
        GIF_frame_scope="Count inherited from unchanged successful raw viewer; reviewer checks signature/hash, no GIF decode")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--publication", type=Path, default=Path(__file__).resolve().parent.parent/"MSTAB1_preparation_001/publication_receipt.json")
    args = parser.parse_args()
    root, out = args.repo.resolve(), args.output.resolve()
    stage, run = root/REL, root/REL/"run_001"
    contract = read(Path(__file__).resolve().parent/"terminal_review_contract.json")
    assert contract["reviewer_sha256"] == sha(Path(__file__))
    for name,pin in contract["actual_auth_files_pinned_at_source_preparation"].items():
        assert sha(stage/name) == pin
    protocol, auth, reply = read(stage/"protocol.json"), read(stage/"author/authorization.json"), read(stage/"author/direct_human_reply.json")
    launch = read(stage/"production_launch.json")
    assert launch["status"] in ("pass", "not_pass") and "completed_utc" in launch
    assert sha(stage/"protocol.json") == PROTOCOL_SHA and len(protocol["bindings"]) == 57
    assert protocol["prepared"] is True and protocol["authorized"] is False and protocol["executed"] is False
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip() == SOURCE
    assert subprocess.check_output(["git", "branch", "--show-current"], cwd=root, text=True).strip() == "main"
    assert subprocess.check_output(["git", "remote", "get-url", "origin"], cwd=root, text=True).strip() == ORIGIN
    publication = read(args.publication)
    archived = stage/"author/M_ALPHA1_source_publication_receipt.json"
    assert archived.read_bytes() == args.publication.read_bytes()
    assert publication["status"] == "published_and_incrementally_restored_pass" and publication["published_commit"] == SOURCE
    assert publication["protocol_sha256"] == PROTOCOL_SHA and publication["binding_count"] == 57
    assert publication["authorized"] is False and publication["executed"] is False
    assert publication["remote_main_confirmed_equal"] and publication["source_and_restore_clean"]
    for name,pin in publication["peer_reviews"].items():
        assert sha(root/name) == pin
    assert auth["authorized"] is True and auth["approved_source_commit"] == reply["approved_source_commit"] == SOURCE
    assert auth["card"] == reply["card"] == "M-ALPHA1" and auth["protocol_sha256"] == PROTOCOL_SHA
    assert auth["authorization_from_direct_human_reply"] is True and reply["authorization_from_direct_human_reply"] is True
    assert auth["human_evidence_sha256"] == sha(stage/"author/direct_human_reply.json")
    assert auth["source_publication_receipt_sha256"] == sha(archived)
    assert auth["direct_human_answer"] == reply["direct_human_answer"] and isinstance(reply["direct_human_answer"],str) and reply["direct_human_answer"].strip()
    assert reply["reply_context"] and reply["question"] and reply["question_item_id"]
    assert datetime.fromisoformat(reply["recorded_utc"]) < datetime.fromisoformat(launch["started_utc"])
    assert datetime.fromisoformat(publication["created_utc"]) < datetime.fromisoformat(reply["recorded_utc"])
    assert (auth["controller_seconds"], auth["helper_seconds"], auth["outer_seconds"], auth["sampled_RSS_bytes"], auth["invocations_allowed"]) == (9000,9600,9660,8589934592,1)
    assert launch["phase"] == "production" and launch["invocations"] == 1 and launch["protocol_sha256"] == PROTOCOL_SHA
    assert launch["bindings"] == protocol["bindings"] and launch["outer_seconds"] == 9660 and launch["sampled_RSS_limit_bytes"] == 8589934592
    assert launch["argv"][1:] == ["-B", *protocol["phases"]["production"]["argv"]]
    mismatches = [n for n,pin in protocol["bindings"].items() if sha(root/n) != pin]
    helper = optional(run/"execution_receipt.json")
    inventory = {path.relative_to(root).as_posix(): dict(bytes=path.stat().st_size, sha256=sha(path))
                 for path in run.rglob("*") if path.is_file()}
    hashes = {name: item["sha256"] for name,item in inventory.items()
              if name != REL+"/run_001/execution_receipt.json"}
    mismatched_outputs, missing_declared_outputs = [], []
    if helper:
        assert helper["protocol_sha256"] == PROTOCOL_SHA and helper["approved_source_commit"] == SOURCE
        assert helper["authorization_sha256"] == sha(stage/"author/authorization.json")
        assert helper["human_evidence_sha256"] == auth["human_evidence_sha256"]
        assert helper["status"] in ("pass", "not_pass", "running")
        if launch["status"] == "pass":
            assert helper["status"] == "pass"
        for name,pin in helper.get("outputs",{}).items():
            path=(root/name).resolve();path.relative_to(run)
            if name not in hashes:
                missing_declared_outputs.append(name)
            elif hashes[name] != pin:
                mismatched_outputs.append(name)
    lines = (stage/"production_stdout.log").read_text(encoding="utf-8").splitlines()
    parsed, other = [], []
    for i,line in enumerate(lines,1):
        try:
            parsed.append(dict(line_number=i, record=json.loads(line)))
        except json.JSONDecodeError:
            other.append(dict(line_number=i, text=line))
    successful = launch["status"] == "pass" and helper is not None and helper["status"] == "pass"
    success = None
    if successful:
        assert not mismatches and not mismatched_outputs and not missing_declared_outputs
        assert set(helper["outputs"]) == {path.relative_to(root).as_posix() for path in run.rglob("*") if path.is_file() and path != run/"execution_receipt.json"}
        assert 0 < helper["elapsed_seconds"] <= 9600 and 0 < launch["elapsed_seconds"] <= 9660
        assert 0 < helper["peak_sampled_RSS_bytes"] <= 8589934592 and 0 < launch["peak_sampled_tree_RSS_bytes"] <= 8589934592
        expected = {k:helper[k] for k in ("status", "accepted_states", "elapsed_seconds", "peak_sampled_RSS_bytes")}
        assert len([row for row in parsed if row["record"] == expected]) == 1
        success = check_success(root, protocol, helper, launch, hashes)
    else:
        assert launch["status"] == "not_pass" or helper["status"] == "not_pass"
    report = dict(schema_version="M-ALPHA1-terminal-record-review-1.0",
        status="pass_terminal_record_review_execution_pass" if successful else "pass_terminal_record_review_execution_not_pass",
        execution_status="pass" if successful else "not_pass", source_commit=SOURCE, protocol_sha256=PROTOCOL_SHA,
        created_utc=datetime.now(timezone.utc).isoformat(), actual_launch=launch, actual_helper=helper,
        same_57_binding_mismatches=mismatches, actual_output_files_hashed=len(hashes), output_hash_mismatches=mismatched_outputs,
        actual_run_file_inventory=inventory, declared_output_files_missing=missing_declared_outputs,
        actual_files_not_declared_by_helper=sorted(set(hashes)-set(helper.get("outputs",{}))) if helper else sorted(hashes),
        helper_snapshot_scope="Initial running persistence is not dynamic counts or a helper terminal result" if helper and helper["status"] == "running" else "Saved terminal helper receipt" if helper else "No helper receipt survived",
        stdout_JSON_records=parsed, stdout_other_lines=other, success_record_checks=success,
        resource_scope="Helper/view success receipt elapsed snapshots precede their final receipt writes; outer includes full tree terminal. RSS sampling schedules differ; no hard OS cap.",
        mechanical_hook_scope="Parent wrapper counts batch/API/model/solve/F/T/save/summary; fresh view explicitly hook=false. Ordinary reviewer runs no hooks or mechanics.",
        reviewer_actions=dict(HF_imports=0,NPZ_field_decodes=0,new_force_tangent_HP_solver=0,new_scientific_sums_or_differences=0,new_renders=0),
        limits="Saved scalar gates and identity evidence only; no independent numeric-array/HP audit or visual inspection. Warnings retained, no new stdout/PNG-size gate. Failed or incomplete outputs are not production success.")
    with (out/"terminal_execution_review.json").open("x",encoding="utf-8",newline="\n") as stream:
        stream.write(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+"\n")
    print(json.dumps(dict(status=report["status"],execution_status=report["execution_status"],report_sha256=sha(out/"terminal_execution_review.json"))))


if __name__ == "__main__":
    main()
