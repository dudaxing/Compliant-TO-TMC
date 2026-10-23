"""Independent ordinary LOW1 evidence audit; no science or media decoding.

Read only new ordinary JSON, frozen source bytes, one opaque whole ZIP identity,
and its central-directory names/sizes. Write only into this author directory.
"""
import hashlib
import json
import math
from pathlib import Path
import zipfile

AUTHOR = Path(__file__).resolve().parent
BASE = Path("D:/hlo1_001")
READS = []


def pin(path):
    raw = path.read_bytes()
    return dict(path=path.as_posix(), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def ordinary(relative):
    path = BASE / relative
    raw = path.read_bytes()
    READS.append(dict(path=path.as_posix(), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))
    return json.loads(raw)


def require(condition, reason):
    if not condition:
        raise ValueError("Ordinary evidence mismatch: " + reason)


def gates(row, target, mean_name):
    bound = 1e-10 * max(abs(target), 1e-6)
    return (abs(row[mean_name] - target) <= bound
            and abs(row["constraint_residual"]) <= row["constraint_bound"] == bound
            and 0 <= row["relative_residual"] <= 1e-9
            and row["minimum_J"] > 0
            and 0 <= row["relative_global_force_balance"] <= 1e-6)


protocol = ordinary("protocol.json")
require(pin(BASE / "protocol.json")["sha256"] == "e4148293f4bbb1d800d3dec73b8bee3afa3fe8ae1b72c9d9fe98463f5b4ba1d8", "original reviewed protocol identity")
binding_mismatches = []
for entry in protocol["bindings"]:
    actual = pin(Path(entry["path"]))
    if actual["bytes"] != entry["bytes"] or actual["sha256"] != entry["sha256"]:
        binding_mismatches.append(entry["path"])
require(len(protocol["bindings"]) == 67 and not binding_mismatches, "all67 frozen bindings")
candidate = Path(protocol["candidate_source"])
formal = Path(protocol["root_repository"]) / "hf_repo/src"
source_files = sorted(candidate.rglob("*.py"))
production_mismatches = [path.as_posix() for path in source_files
                         if path.read_bytes() != (formal / path.relative_to(candidate)).read_bytes()]
require(len(source_files) == 55 and not production_mismatches, "all55 production source bytes unchanged")

parent = ordinary("run_001/parent_fixed/result.json")
probe = ordinary("run_001/probe_low/result.json")
parent_child = ordinary("run_001/parent_child_receipt.json")
probe_child = ordinary("run_001/probe_child_receipt.json")
parent_validation = ordinary("run_001/parent_validation.json")
probe_validation = ordinary("run_001/probe_validation.json")
helper = ordinary("run_001/helper_receipt.json")
launch = ordinary("run_001/launch_receipt.json")
root_start = ordinary("root_outer_start.json")
renderer = ordinary("run_001/view/renderer_receipt.json")
table = ordinary("run_001/view/state_table.json")
comparison = ordinary("run_001/view/comparison.json")
high = ordinary("high_state_table.json")
seal = ordinary("seal_receipt.json")
manifest = ordinary("EVIDENCE_MANIFEST.json")

require(parent["status"] == probe["status"] == "success", "both actual phases successful")
require(parent["failure"] is None and probe["failure"] is None, "no terminal phase failure")
require(parent["path_kind"] == "load_only" and parent["targets_mm"] == [0., .25, .5]
        and parent["task_target_mm"] == .5 and "continuation" not in parent
        and parent["target_origin"] == 0 and parent["lift_origin_zero"] is True
        and parent["lift_shape_zero"] is True, "real zero-start short father")
require(all(parent[key] is True for key in ("path_completed", "target_reached", "loading_peak_reached",
    "task_target_executed", "production_converged")), "all parent completion flags")
require(len(parent["states"]) == 3 and [row["d"] for row in parent["states"]] == [0., .25, .5]
        and all(row["is_original_target"] for row in parent["states"]), "three actual original parent states")
require(parent["settings"] == probe["settings"] == protocol["parent_settings"]
        and parent["response_mode"] == probe["response_mode"] == "mechanical"
        and parent["tangent_execution"]["mode"] == probe["tangent_mode"] == "chunk256"
        and parent["initial_guess"] == probe["initial_guess"] == "port_projection", "settings and execution modes")
require(all(gates(row, row["physical_mean_target_mm"], "q_in") for row in parent["states"]), "all parent saved gates")
cache = parent_child["cached_production_gates"]
require(cache["passed"] is True and cache["maximum_fixed_split_sum_mm"] == 0.
        and cache["actual_accepted_states"] == 3, "original returned-cache fixed/J gate")
require(parent_child["api_call_attempts"] == parent_child["solve_call_attempts"]
        == parent_child["solve_calls_completed"] == 1 and parent_child["api_returned"] is True,
        "one parent public API and original solver call")
require(parent["call_counts"]["force_calls"] == parent["call_counts"]["force_calls_completed"] == 27
        and parent["call_counts"]["tangent_calls"] == parent["call_counts"]["tangent_calls_completed"] == 15,
        "actual parent27F15T")

rows = probe["accepted_steps"]
peak, anchor = parent["states"][-1], rows[0]
require(len(rows) == 2 and [row["body_q_mm"] for row in rows] == [0., .025]
        and probe["target_reached"] is True
        and probe["probe_task"]["held_input_mean_mm"] == .5, "two actual authorized probe q states")
require(probe_child["api_call_attempts"] == 1 and probe_child["api_returned"] is True
        and probe_child["selected_parent_state_index"] == 2, "one probe API and real dynamic parent index")
require(probe["source"]["selected_state"]["accepted_index"] == 2
        and anchor["fresh_anchor"] is True and anchor["newton_checks"] == 1
        and anchor["state_sha256"] == peak["state_sha256"]
        and float(anchor["R_input_N"]).hex() == float(peak["R_input"]).hex()
        and anchor["state"]["fields"] == peak["state"]["fields"], "fresh q0 identity and signed R, no repair")
require(all(gates(row, .5, "input_mean_mm") and row["max_abs_prescribed_error_mm"] == 0.
            and row["Q_drive_half_N"] == -row["force_on_body_N"]["total"][0] for row in rows),
        "all probe original gates, held mean and signed Q")
require(probe["call_counts"]["force_calls"] == probe["call_counts"]["force_calls_completed"] == 10
        and probe["call_counts"]["tangent_calls"] == probe["call_counts"]["tangent_calls_completed"] == 6,
        "actual probe10F6T")
require(parent["call_counts"]["solver_invocations"] == probe["call_counts"]["solver_invocations"] == 1
        and parent["call_counts"]["HP_calls"] == probe["call_counts"]["HP_calls"] == 0
        and parent["save_force_calls"] == parent["save_tangent_calls"]
        == probe["call_counts"]["save_force_calls"] == probe["call_counts"]["save_tangent_calls"] == 0,
        "one solver each, no HP or save F/T")
ph = parent["path_diagnostics"]
require(not ph["failed_attempts"] and not probe["failed_attempts"], "no failed attempts in either low phase")
require([len(ph[name]) for name in ("newton_history", "trials", "linear_solve_diagnostics")] == [15, 12, 14]
        and [len(probe[name]) for name in ("newton_history", "trials", "linear_solve_diagnostics")] == [6, 4, 5],
        "full original histories retained")
require(parent_validation["status"] == probe_validation["status"] == "pass"
        and helper["status"] == launch["status"] == "ready_for_visual_check"
        and [helper[key] for key in ("parent_process_launches", "probe_process_launches", "viewer_process_launches")] == [1,1,1],
        "recorded unique sequential phase outcomes")

supervision = []
for phase, relative in (("outer", "root_outer_supervision.json"), ("helper", "run_001/helper_supervision.json"),
    ("parent", "run_001/parent_supervision.json"), ("probe", "run_001/probe_supervision.json"),
    ("viewer", "run_001/viewer_supervision.json")):
    record = ordinary(relative)
    proof = record["cleanup_proof"]
    require(record["reason"] == "normal_exit" and record["returncode"] == 0
            and record["cleanup_verified"] is True
            and all(proof[key] is True for key in ("pass", "coverage_verified", "termination_verified",
                "observation_handles_closed", "root_wait_completed", "root_handle_close_verified", "job_handle_closed"))
            and proof["final_accounting"]["ActiveProcesses"] == 0
            and proof["signaled_identity_count"] == proof["unique_bound_identity_count"]
            and all(row["signaled"] is True and row["handle_closed"] is True for row in proof["identities"]),
            "same-instance normal exit and full member/handle cleanup: " + phase)
    supervision.append(dict(phase=phase, elapsed_seconds=record["elapsed_seconds"],
        peak_sampled_tree_rss_bytes=record["peak_tree_rss_bytes"], identity_count=proof["unique_bound_identity_count"],
        pass_same_instance=True, sampled_memory_limit_bytes=record["rss_limit_bytes"]))
require(supervision[0]["elapsed_seconds"] < 9060 and launch["elapsed_since_root_seconds"] < 9000
        and seal["elapsed_seconds_from_outer_start"] < 9000, "all original resource windows")

require(renderer["accepted_states"] == renderer["archives_decoded"] == renderer["gif_frame_count"] == 2
        and renderer["fields_decoded"] == 4 and renderer["new_png_count"] == 4
        and renderer["scientific_calls"] == 0 and renderer["new_gif_metadata_reads"] == 1
        and renderer["exact_common_q_mm"] == [0., .025], "pure viewer actual metadata counts")
require(table["parent"]["states"] == parent["states"]
        and table["parent"]["path_diagnostics"] == ph
        and all(table[name] == probe[name] for name in ("newton_history", "trials", "failed_attempts",
            "linear_solve_diagnostics", "call_counts")), "all parent/probe histories retained in ordinary display table")
require(comparison["exact_common_q_mm"] == [0., .025] and comparison["interpolation"] is False
        and comparison["high_actual_states"] == high["states"]
        and comparison["low_actual_states"] == table["states"]
        and comparison["high_unmatched_q_mm"] == [.0125] and comparison["low_unmatched_q_mm"] == [],
        "same-q exact pairing, raw objects and unmatched actual state retained")
for pair in comparison["paired_states"]:
    for key in pair["high_raw"]:
        require(pair["low_minus_high_raw"][key] == pair["low_raw"][key] - pair["high_raw"][key], "same-q signed raw arithmetic")
    for key in ("Q_total_N", "Q_material_N", "Q_Hu_N"):
        for side in ("high", "low"):
            own_zero = comparison["paired_states"][0][side + "_raw"][key]
            require(pair[side + "_Q_increment_from_own_q0_N"][key] == pair[side + "_raw"][key] - own_zero,
                    "own-zero increment retains raw preload")
        require(pair["low_minus_high_Q_increment_N"][key] == pair["low_Q_increment_from_own_q0_N"][key]
                - pair["high_Q_increment_from_own_q0_N"][key], "increment difference arithmetic")

archive = BASE / "execution_evidence.zip"
digest = hashlib.sha256()
with archive.open("rb") as stream:
    while chunk := stream.read(1024 * 1024):
        digest.update(chunk)
archive_identity = dict(path=archive.as_posix(), bytes=archive.stat().st_size, sha256=digest.hexdigest())
require(archive_identity["bytes"] == 70914947
        and archive_identity["sha256"] == "c5e1e6c58ebe20b2a214be9d2519b50e875343f1ad53d8c7630d5065d1cb577e"
        and {key: archive_identity[key] for key in ("bytes", "sha256")} ==
            {key: manifest["archive"][key] for key in ("bytes", "sha256")}, "opaque whole ZIP identity")
with zipfile.ZipFile(archive) as zipped:
    central = zipped.infolist()
    require(len(central) == len(manifest["members"]) == seal["members"] == 133,
            "133 original archive members")
    actual_names_sizes = {item.filename: item.file_size for item in central}
require(actual_names_sizes == {item["path"]: item["bytes"] for item in manifest["members"]},
        "central-directory names and uncompressed sizes match manifest, without member decoding")
require(seal["status"] == "pass" and seal["attempts"] == 1 and seal["outer_pass"] is True
        and seal["evidence_completeness"] == "normal_exit", "one original-window byte seal")

report = dict(schema_version="hf-ctiplow1-actual-delivery-review-1", date="2026-10-23",
    reviewer="/root/low_supervision", status="PASS_ORDINARY_ACTUAL_EVIDENCE", blocking_findings=[],
    scope="Independent new ordinary JSON/source bytes/whole ZIP identity and central metadata only; not HP or pixel review.",
    protocol=pin(BASE / "protocol.json"), runner=pin(BASE / "run_low1.py"),
    bound_files_checked=67, binding_mismatches=binding_mismatches,
    production_python_files_checked=55, production_mismatches=production_mismatches,
    parent=dict(status=parent["status"], accepted_states=3, original_targets_mm=[0., .25, .5],
        calls=parent["call_counts"], cache_gates=cache, newton_checks=15, line_trials=12,
        linear_solves=14, failed_attempts=0, final_R_input_N=peak["R_input"]),
    probe=dict(status=probe["status"], accepted_states=2, original_q_mm=[0., .025], held_input_mm=.5,
        calls=probe["call_counts"], newton_checks=6, line_trials=4, linear_solves=5, failed_attempts=0,
        q0_hash_preserved=True, q0_signed_R_preserved=True, q0_fresh_checks=1,
        max_relative_residual=max(row["relative_residual"] for row in rows),
        min_J=min(row["minimum_J"] for row in rows), max_prescribed_error_mm=0.,
        max_relative_global_force_balance=max(row["relative_global_force_balance"] for row in rows),
        states=[{key: row[key] for key in ("body_q_mm", "input_mean_mm", "R_input_N", "Q_drive_half_N",
            "minimum_J", "relative_residual", "relative_global_force_balance", "newton_checks")} for row in rows]),
    supervision=supervision, seal=seal, archive=archive_identity,
    archive_member_count=133, member_names_and_sizes_matched=True,
    zip_members_decompressed=0, scientific_array_fields_decoded=0, image_or_GIF_bytes_read=0,
    scientific_functions_called=0, tests_run=0, render_calls=0, installations=0,
    display=dict(new_PNGs_declared=4, actual_GIF_frames_declared=2, new_archives_decoded_by_original_viewer=2,
        new_fields_decoded_by_original_viewer=4, exact_common_q_mm=[0., .025], high_unmatched_q_mm=[.0125],
        interpolation=False, scientific_calls_by_original_viewer=0,
        pixel_quality="Not inspected by this reviewer; root's one-pass FIGURE_QA is separate."),
    descriptive_same_q=dict(low_terminal_Q_N=rows[-1]["Q_drive_half_N"],
        low_delta_Q_N=rows[-1]["Q_drive_half_N"]-rows[0]["Q_drive_half_N"],
        high_delta_Q_N=comparison["paired_states"][-1]["high_Q_increment_from_own_q0_N"]["Q_total_N"],
        low_minus_high_delta_Q_N=comparison["paired_states"][-1]["low_minus_high_Q_increment_N"]["Q_total_N"],
        low_terminal_Hu_fraction=(-rows[-1]["force_on_body_N"]["regularization"][0])/rows[-1]["Q_drive_half_N"],
        low_tip_gap_mm=[row["tip_to_body_boundary_mm"] for row in table["states"]]),
    ordinary_inputs=READS,
    limitations="Actual ordinary consistency only. No independent HP, pressure, pure contact/friction force, free-body capacity, grasp/release/stability or parameter/domain qualification is granted. Pixel QA and publication/restore remain root responsibilities.")
(AUTHOR / "ACTUAL_DELIVERY_REVIEW.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")
print(json.dumps({key: report[key] for key in ("status", "bound_files_checked", "production_python_files_checked",
    "archive_member_count", "archive", "descriptive_same_q")}, indent=2))
