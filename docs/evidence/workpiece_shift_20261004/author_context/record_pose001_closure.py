"""Read actual saved receipts only and retain closed-card interpretation."""
from pathlib import Path
from hashlib import sha256
import json

root=Path("D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC")
stage=root/"lf_data_preparation/native_workpiece_001/shift_square_pose_001"
read=lambda p:json.loads(p.read_text(encoding="utf-8"))
result=read(stage/"run_001/result/result.json")
receipt=read(stage/"run_001/execution_receipt.json")
launch=read(stage/"production_launch.json")
assert result["status"]=="failed" and result["failure"]["code"]=="time_limit"
data=dict(status="closed_failed_full_task", qualification=False,
    actual_accepted_displacements_mm=[s["d"] for s in result["states"]],
    original_targets_mm=result["targets_mm"], peak_reached=True, returned_zero=False,
    production_counts=result["call_counts"], failed_attempts=result["path_diagnostics"]["failed_attempts"],
    helper_seconds=receipt["elapsed_seconds"], outer_seconds=launch["elapsed_seconds"],
    tree_RSS_bytes=launch["peak_sampled_tree_RSS_bytes"],
    all_bindings_unchanged=launch["all_bindings_unchanged"],
    numerical_calls_for_this_interpretation=dict(F=0,T=0,model=0,solver=0,HP=0),
    interpretation=["Six invalid_J first-base predictor rejections are original controlled rollback/bisection, not finite accepted-state failures.",
        "Terminal unfinished T58 arose from helper time_limit after F108 completed; no range capture exists.",
        "Saved peak and first return are production-only preliminary states, not a qualified complete cycle.",
        "No independent HP executed. No retry, extension or old-prefix qualification permitted on this closed card."],
    next_independent_card=dict(stage="shift_square_pose_002", zero_start=True,
        full_original_targets=True, helper_seconds=1500, outer_seconds=1560, RSS_bytes=8*1024**3,
        unchanged="Task, producer, physical parameters, original controller and numerical gates; explicit time setting only."),
    bindings={p.relative_to(root).as_posix():sha256(p.read_bytes()).hexdigest() for p in
        [stage/"production_protocol.json",stage/"production_launch.json",stage/"run_001/execution_receipt.json",stage/"run_001/result/result.json"]})
with (stage/"CLOSURE.json").open("x",encoding="utf-8") as f:
    json.dump(data,f,indent=2,ensure_ascii=False,allow_nan=False);f.write("\n")
print(json.dumps({k:data[k] for k in ("status","actual_accepted_displacements_mm","helper_seconds","outer_seconds")}))
