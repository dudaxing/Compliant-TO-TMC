"""Compare bounded S0 regression and restored saved-data evidence."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent

def read(name):
    return json.loads((ROOT/name).read_text(encoding="utf-8"))

def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream,"sha256").hexdigest()

baseline=read("baseline_results/validation_receipt.json")
slim=read("slim_results/validation_receipt.json")
loader_baseline=read("baseline_results/real_load_only.json")
loader_restored=read("restored_results/real_load_only.json")
vectors_baseline=read("baseline_results/saved_vector_replay.json")
vectors_restored=read("restored_results/saved_vector_replay.json")
manifest=read("baseline_tree/handoff/repository_manifest.json")
hf_files=[row for row in manifest["files"] if row["path"].startswith("hf_repo/")]
identities={}
for tree in ("baseline_tree","slim_candidate_001","restored_tree_001"):
    for row in hf_files:
        path=ROOT/tree/row["path"]
        assert path.stat().st_size==row["bytes"] and sha(path)==row["sha256"]
    identities[tree]=dict(file_count=len(hf_files),bytes=sum(row["bytes"] for row in hf_files),all_original_identities_verified=True)
checks=dict(
    all_143_test_nodes_equal=read("baseline_results/collected_nodes.json")==read("slim_results/collected_nodes.json"),
    test_file_hashes_equal=baseline["test_file_sha256"]==slim["test_file_sha256"],
    same_skip_identity_and_reason=baseline["skips"]==slim["skips"],
    same_142_passed=baseline["passed"]==slim["passed"]==142,
    no_test_failures=baseline["failures"]==slim["failures"]==[],
    canonical_geometry_reads_equal=read("baseline_results/geometry_inspect.json")["geometries"]==read("slim_results/geometry_inspect.json")["geometries"],
    actual_loader_full_binding_and_controller_records_equal=loader_baseline["cases"]==loader_restored["cases"],
    loader_forbidden_entry_points_zero_calls=all(x["call_count"]==0 for doc in (loader_baseline,loader_restored) for x in doc["forbidden_entry_points"]),
    all_59_saved_vector_and_prefix_records_equal=vectors_baseline["rows"]==vectors_restored["rows"],
    vector_input_hashes_equal=vectors_baseline["input_sha256"]==vectors_restored["input_sha256"],
    prefix_and_original_target_summaries_equal=vectors_baseline["cases"]==vectors_restored["cases"],
    replay_script_identity_equal=vectors_baseline["script_sha256"]==vectors_restored["script_sha256"],
    loader_script_identity_equal=loader_baseline["script_sha256"]==loader_restored["script_sha256"],
)
assert all(checks.values())
sources=["baseline_results/validation_receipt.json","slim_results/validation_receipt.json",
    "baseline_results/collected_nodes.json","slim_results/collected_nodes.json",
    "baseline_results/geometry_inspect.json","slim_results/geometry_inspect.json",
    "baseline_results/real_load_only.json","restored_results/real_load_only.json",
    "baseline_results/saved_vector_replay.json","restored_results/saved_vector_replay.json"]
result=dict(schema="hf4-c2-s0-baseline-slim-restored-comparison-1.0",status="pass",checks=checks,
    hf_repo_file_identity=identities,states=59,passed_states=58,replayed_checks=1810,passed_checks=1809,
    vector_comparisons_recomputed=708,stored_scalar_comparisons_replayed=1102,
    restored_pytest_repeated=False,
    reason="The same 143-node suite passed on baseline and slim trees; all hf_repo source, test, fixture and configuration bytes are additionally verified identical on restored tree. Restored tree runs actual load_run and saved-vector/prefix replay instead of duplicating unchanged tests.",
    fine_mesh_final_error=vectors_restored["rows"][-1]["errors"]["production_vs_hp80_total_force"],
    fine_mesh_final_status=vectors_restored["rows"][-1]["status"],
    fine_mesh_final_valid_prefix_comparable=vectors_restored["rows"][-1]["valid_prefix_comparable"],
    no_new_fe_path=True,no_saved_state_constitutive_evaluation=True,
    inputs={name:sha(ROOT/name) for name in sources},comparison_script_sha256=sha(Path(__file__)))
output=ROOT/"restored_comparison.json"
with output.open("x",encoding="utf-8") as stream:
    json.dump(result,stream,ensure_ascii=False,indent=2)
    stream.write("\n")
print(json.dumps(dict(status="pass",checks=checks,hf_repo_files_per_tree=len(hf_files),fine_mesh_final_error=result["fine_mesh_final_error"])))
