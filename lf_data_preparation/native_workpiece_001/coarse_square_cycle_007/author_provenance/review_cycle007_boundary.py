"""Read saved cycle007 boundary identities; no geometry/mechanics imports."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC")
STAGE = ROOT / "functional_views/native_workpiece_cycle007_20261004/boundary_saved_001"
RESULT = ROOT / "lf_data_preparation/native_workpiece_001/coarse_square_cycle_007/result"
OUTPUT = Path("D:/hf-native-workpiece-cycle007-author-20261004/cycle007_actual_boundary_identity_review.json")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


protocol_file = STAGE / "protocol.json"
protocol = read(protocol_file)
receipt = read(STAGE / "measurement_receipt.json")
launch = read(STAGE / "measure_launch.json")
measurement_file = STAGE / "measurement_001/boundary_measurements.json"
measurement = read(measurement_file)
production = read(RESULT / "result.json")
before = {rel: sha(ROOT / rel) for rel in protocol["bindings"]}
require(len(before) == 49 and before == protocol["bindings"], "49 protocol byte pins")
require(launch["bindings"] == before, "launch/protocol binding equality")
require(launch["protocol_sha256"] == sha(protocol_file), "launch protocol SHA")
require(receipt["measurement_sha256"] == sha(measurement_file), "saved measurement SHA")
require(receipt["status"] == launch["status"] == "pass", "actual terminal pass")
require(launch["exit_code"] == 0 and receipt["invocations"] == launch["invocations"] == 1, "unique terminal invocation")
require(receipt["all_bindings_unchanged"] and launch["all_bindings_unchanged"], "end-pin assertions")
require(receipt["geometry_calls_started"] == receipt["geometry_calls_completed"] == protocol["expected_geometry_calls"] == 7, "7/7 measurement calls")
require(receipt["hook_restored"] and launch["stop_reason"] is None, "hook restoration/no stop")
require(launch["outer_seconds"] == protocol["phases"]["measure"]["outer_seconds"] == 120, "outer120")
require(receipt["elapsed_seconds"] < 120 and launch["elapsed_seconds"] < 120, "actual time within card")
require(launch["sampled_RSS_limit_bytes"] == protocol["sampled_RSS_bytes"] == 8 * 1024 ** 3, "sampled8GiB")
require(max(receipt["peak_sampled_RSS_bytes"], launch["peak_sampled_tree_RSS_bytes"]) < protocol["sampled_RSS_bytes"], "actual sampled RSS")
for obj in (receipt, measurement):
    require(all(obj[name] == 0 for name in ("force_calls", "tangent_calls", "solver_calls", "HP_calls")), "no mechanical calls")
require(measurement["input_files_unchanged"], "measurement input end pins")
inputs = {}
for name, expected in measurement["input_files_sha256"].items():
    path = Path(name)
    rel = path.relative_to(ROOT).as_posix()
    require(sha(path) == expected and before[rel] == expected, "measurement input " + rel)
    inputs[rel] = expected
require(len(inputs) == 12, "12 source/data input bindings")
capsules = {}
for name in ("__init__.py", "boundary_geometry.py", "measure_native_workpiece_boundaries.py"):
    original = ROOT / ("hf_repo/scripts" if name.startswith("measure_") else "hf_repo/src/hf_eval") / name
    capsule = STAGE / "sources" / name
    require(sha(original) == sha(capsule) == before[original.relative_to(ROOT).as_posix()], "source capsule " + name)
    capsules[name] = sha(capsule)
require(measurement["production_status"] == production["status"] == "success", "saved production status")
require(measurement["task_sha256"] == production["task_sha256"], "effective task semantic pin")
require(len(measurement["accepted_states"]) == len(production["states"]) == 7, "seven actual accepted states")
rows = []
for index, (saved, state) in enumerate(zip(measurement["accepted_states"], production["states"])):
    require(saved["accepted_index"] == index and saved["original_target_index"] == state["original_target_index"] == index, "actual unique index")
    require(saved["d_mm"] == state["d"] and saved["leg"] == state["leg"] and saved["state_sha256"] == state["state_sha256"], "actual state identity")
    require(saved["node_window_clearance_mm"] == state["workpiece"]["node_window_clearance_mm"], "saved node-window proxy")
    geometry = saved["geometry"]
    require(len(geometry["mechanism_edges"]) == 496 and len(geometry["workpiece_edges"]) == 32, "saved edge counts")
    require(geometry["symmetry_cut_excluded"] == {"axis": "y", "reference_offset_mm": 40.0, "applies_to": "both boundaries"}, "excluded y40 cut declaration")
    require(geometry["containment_tested"] is False, "containment not tested")
    require(geometry["contact_pressure_qualification"] is False and geometry["contact_or_clamping_qualification"] is False, "no contact qualification")
    require(all(geometry[name] == 0 for name in ("force_calls", "tangent_calls", "solver_calls", "HP_calls")), "geometry mechanical counts zero")
    group_rows = {}
    for name, body_count in (("all_exposed", 32), ("bottom", 16), ("left", 8)):
        group = geometry["groups"][name]
        require(group["mechanism_edge_count"] == 496 and group["workpiece_edge_count"] == body_count, "boundary group counts")
        require(group["minimum_boundary_distance_mm"] > 0, "positive saved unsigned distance")
        require(group["intersections"] == [] and group["intersects"] is False and group["roundoff_near_touch"] is False and group["containment_tested"] is False, "saved crossing/near-touch/containment status")
        group_rows[name] = {key: group[key] for key in ("minimum_boundary_distance_mm", "closest_pair", "intersects", "roundoff_near_touch", "containment_tested")}
    require(geometry["mechanism_edges"] == measurement["accepted_states"][0]["geometry"]["mechanism_edges"], "same mechanism topology")
    require(geometry["workpiece_edges"] == measurement["accepted_states"][0]["geometry"]["workpiece_edges"], "same fixed-body topology")
    rows.append({"index": index, "d_mm": state["d"], "leg": state["leg"], "state_sha256": state["state_sha256"], "node_window_proxy_mm": saved["node_window_clearance_mm"], "groups": group_rows})
after = {rel: sha(ROOT / rel) for rel in before}
require(after == before, "all protocol pins unchanged during independent review")
review = {
    "schema_version": "cycle007-actual-boundary-readonly-review-1.0",
    "status": "pass", "reviewed_utc": datetime.now(timezone.utc).isoformat(), "qualification": False,
    "protocol_sha256": sha(protocol_file), "protocol_bindings_verified": len(before),
    "input_file_bindings_verified": len(inputs), "source_capsules_verified": len(capsules),
    "source_capsule_sha256": capsules, "before_after_bindings_equal": True,
    "measurement_sha256": sha(measurement_file), "receipt_sha256": sha(STAGE / "measurement_receipt.json"),
    "launch_sha256": sha(STAGE / "measure_launch.json"), "actual_geometry_calls": {"started": 7, "completed": 7, "hook_restored": True},
    "formal_helper": {"elapsed_seconds": receipt["elapsed_seconds"], "sampled_peak_RSS_bytes": receipt["peak_sampled_RSS_bytes"], "seconds_limit": 120},
    "formal_launch": {key: launch[key] for key in ("invocations", "status", "exit_code", "elapsed_seconds", "peak_sampled_tree_RSS_bytes", "outer_seconds", "sampled_RSS_limit_bytes", "stop_reason")},
    "saved_states_verified": rows,
    "limits": ["Unsigned Euclidean straight-Q1 exterior distances of saved binary64 coordinates, with roundoff tolerance; no signed penetration or certified geometry", "Containment was not tested; false crossing/near-touch flags are not a complete non-overlap/contact proof", "Left nearest pair is to the body lower corner, not a horizontal normal-gap measurement", "Source node-window bounds are saved proxies, not Q1 boundary distance", "Positive remaining distance and weak-form third-medium body force do not prove clamping or pressure qualification", "Fresh reference was running separately and is not reviewed or qualified by this geometry receipt"],
    "new_calls": {name: 0 for name in ("geometry", "force", "tangent", "consumer", "assembly", "solver", "HP", "test", "plot")},
    "scope": "Independent saved SHA/identity/counter/scalar status checks only; no boundary extraction, distance remeasurement, or physics replay",
}
with OUTPUT.open("x", encoding="utf-8") as stream:
    json.dump(review, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
print(json.dumps({"status": "pass", "output": str(OUTPUT), "sha256": sha(OUTPUT), "states": len(rows), "pins": len(before)}))
