"""Freeze entry integration with explicit transitions after closed chunk001."""
from hashlib import sha256
import json
from pathlib import Path
import shutil

STAGE = Path(__file__).resolve().parent
ROOT = STAGE.parents[2]
sha = lambda p: sha256(p.read_bytes()).hexdigest()
assert not (STAGE/"protocol.json").exists()
prior = ROOT/"lf_data_preparation/native_workpiece_001/numpy_tangent_chunk_001"
proof = json.loads((prior/"comparison_receipt.json").read_text(encoding="utf-8"))
assert proof["status"] == "pass" and proof["candidate_cost_gate_passed"]
assert proof["force_calls"] == proof["force_calls_completed"] == 3
assert proof["tangent_calls"] == proof["tangent_calls_completed"] == 9
assert json.loads((prior/"comparison_launch.json").read_text())["status"] == "pass"
names = [p.relative_to(ROOT).as_posix() for p in sorted((ROOT/"hf_repo/src/hf_eval").glob("*.py"))]
names += ["hf_repo/scripts/solve_native_mean.py", "hf_repo/pyproject.toml"]
names += ["hf_repo/tests/"+n for n in ("test_native_force.py", "test_native_mean.py",
         "test_native_mean_mechanical.py", "test_split_numpy_tangent_chunked.py")]
names += [(prior/n).relative_to(ROOT).as_posix() for n in
          ("protocol.json", "tests_receipt.json", "tests_launch.json",
           "comparison_receipt.json", "comparison_launch.json")]
names += [(STAGE/n).relative_to(ROOT).as_posix() for n in
          ("build_protocol.py", "run_tests_once.py", "launch_phase.py")]
bindings = {name: sha(ROOT/name) for name in names}
caps = {}
for name in names:
    if not name.endswith(".py"):
        continue
    compile((ROOT/name).read_text(encoding="utf-8"), name, "exec")
    destination = STAGE/"sources"/name
    destination.parent.mkdir(parents=True, exist_ok=True)
    assert not destination.exists()
    shutil.copyfile(ROOT/name, destination)
    caps[destination.relative_to(ROOT).as_posix()] = sha(destination)
bindings.update(caps)
old = json.loads((prior/"protocol.json").read_text())["bindings"]
transitions = {name: dict(previous_sha256=old.get(name), current_sha256=pin)
               for name,pin in bindings.items() if name in old and old[name] != pin}
assert set(transitions) == {"hf_repo/src/hf_eval/native_mean.py"}
# CLI was not in the prior diagnostic closure; its old identity is bound separately.
cli = "hf_repo/scripts/solve_native_mean.py"
transitions[cli] = dict(previous_sha256="01f6f1277d0d596138f024706fca996984222769925679896c4a01e4461fc52b",
                       current_sha256=bindings[cli])
protocol = dict(schema_version="native-mean-chunk-integration-card-1.0", bindings=bindings,
    sampled_RSS_bytes=8*1024**3, baseline_commit="97b7e0eecd07aee0bd16c61961dedb360202641c",
    source_transition_after_closed_chunk001=transitions, expected_passed_tests=10,
    scope="New explicit chunk256 API/CLI and small temporary load/return/partial paths; no formal workpiece path or HP",
    failure_policy="First failure closes card; one invocation, no retry/repair/force/extension",
    phases=dict(tests=dict(helper_seconds=120, outer_seconds=150,
        argv=[(STAGE/"run_tests_once.py").relative_to(ROOT).as_posix()])))
(STAGE/"protocol.json").write_text(json.dumps(protocol, indent=2)+"\n", encoding="utf-8")
print(json.dumps(dict(protocol_sha256=sha(STAGE/"protocol.json"), pins=len(bindings),
                     caps=len(caps), expected_tests=10, source_transitions=transitions)))
