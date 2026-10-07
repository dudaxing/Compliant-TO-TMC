"""Install a reviewed, fresh one-call real native API card; never execute it."""
from pathlib import Path
import argparse
import ast
import hashlib
import json
import subprocess

HEAD = "8330b821af1f9ab58bdd9f51c85eb2e7d3cdcb37"
STAGE = "lf_data_preparation/native_interface_001/real_forward_001"
BASE = "lf_data_preparation/native_mean_001"
FUNCTIONAL = "lf_data_preparation/native_interface_001/api_validation_001/functional_protocol.json"
LAUNCHER = "lf_data_preparation/native_workpiece_001/right_margin4_cycle_001/launch_pose.py"
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
read = lambda path: json.loads(path.read_bytes())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--root-review", type=Path, required=True)
    parser.add_argument("--peer-review", type=Path, required=True)
    args = parser.parse_args()
    root, author = args.repo.resolve(), Path(__file__).resolve().parent
    assert not author.is_relative_to(root)
    assert subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip() == HEAD
    assert subprocess.check_output(["git", "-C", str(root), "branch", "--show-current"], text=True).strip() == "main"
    stage = root/STAGE
    assert not stage.exists()
    worker = author/"execute_real_api.py"
    for source in [worker, Path(__file__)]:
        compile(ast.parse(source.read_text(encoding="utf-8")), str(source), "exec")
    reports = [args.root_review.resolve(), args.peer_review.resolve()]
    for path in reports:
        review = read(path)
        assert review["status"] == "pass_static_only" and not review["blocking_findings"]
        for source in [worker, Path(__file__)]:
            pins = {pin for name, pin in review["source_sha256"].items() if Path(name).name == source.name}
            assert pins == {sha(source)}
    functional = read(root/FUNCTIONAL)
    sources = {name: pin for name, pin in functional["bindings"].items() if name.startswith("hf_repo/src/")}
    assert len(sources) == 27 and all(sha(root/name) == pin for name, pin in sources.items())
    inventory, old_result = read(root/BASE/"input_inventory.json"), read(root/BASE/"result/result.json")
    old_receipt = read(root/BASE/"execution_receipt.json")
    case = inventory["case"]
    task_file, geometry_file = root/case["task_file"], root/case["geometry_file"]
    task = read(task_file)
    assert task["input"]["target_mm"] == .001 and task["workpiece"] is None and "path" not in task
    assert task["task_id"] == "TEST_native_mean_gripper_0001_20261003"
    assert case["targets_mm"] == old_result["targets_mm"] == [0., .001]
    assert old_result["task_target_executed"] is True and old_receipt["status"] == "pass"
    inputs = {name:sha(root/name) for name in [case["task_file"], case["geometry_file"],
        case["geometry_npz_file"], BASE+"/input_inventory.json", BASE+"/result/result.json", BASE+"/execution_receipt.json"]}
    assert inputs[case["task_file"]] == case["task_file_sha256"]
    assert inputs[case["geometry_file"]] == case["geometry_file_sha256"]
    assert inputs[case["geometry_npz_file"]] == case["geometry_npz_sha256"]
    launcher = root/LAUNCHER
    assert sha(launcher) == "f3a96681afc474e42ae19875579d748237235dce90f21892b016b3b3af862477"
    selections = [worker, Path(__file__).resolve(), author/"README.md", author/"author_note.json",
                  author/"author_checks.json", author/"source_additions.diff",
                  author/"context/001.json", author/"context/002.md", author/"context/index.json",
                  author/"absent_view_gate_delta.diff",
                  *sorted((author/"pre_view_gate_001").iterdir()), *reports]
    assert all(path.is_file() for path in selections)
    # Everything above is file/JSON/hash/AST and read-only Git. No imports or scientific calls.
    stage.mkdir(parents=True)
    (stage/"author").mkdir()
    bindings = dict(sources, **inputs)
    archive = {}
    for index, source in enumerate(selections, 1):
        short = f"{index:03d}{source.suffix}"
        destination = stage/"author"/short
        destination.write_bytes(source.read_bytes())
        logical = destination.relative_to(root).as_posix()
        bindings[logical] = sha(destination)
        archive[short] = dict(source_name=str(source), path=logical, sha256=sha(destination))
        if source == worker:
            worker_file = logical
    (stage/"launch_pose.py").write_bytes(launcher.read_bytes())
    bindings[STAGE+"/launch_pose.py"] = sha(stage/"launch_pose.py")
    protocol = dict(schema_version="native-real-api-protocol-1.0", baseline_commit=HEAD,
        bindings=bindings, sampled_RSS_bytes=8*1024**3,
        phases=dict(production=dict(helper_seconds=180, outer_seconds=210,
            argv=[worker_file, "--repo", ".", "--protocol", STAGE+"/production_protocol.json"])),
        geometry_file=case["geometry_file"], task_file=case["task_file"],
        run_directory=STAGE+"/run_001", result_directory=STAGE+"/run_001/result",
        targets_mm=[0., .001], settings=inventory["settings"], gates=inventory["gates"],
        expected_counts=old_result["counts"], expected_model_fields=23,
        options=dict(response_mode="complete", tangent_mode="full", initial_guess="tangent"),
        actual_call_rule="One API; real builder/constructor/controller/solve/cachedwriter/formatter/responsewriter once; actual F/T started/completed retained",
        resource_basis=dict(historical_helper_seconds=old_receipt["elapsed_seconds"],
            estimated_seconds=old_receipt["elapsed_seconds"]*1.5+30,
            role="Cost estimate only; old state/HP/mechanics qualification is not inherited"),
        prefix_scope="Returned controller failure keeps original cached save; resource RuntimeError can leave only accepted scalar NDJSON and null result/response paths",
        science_scope="One actual coarse ordinary mean-displacement evaluation; no workpiece, HP, JIT, LF call, new observation or visualization",
        stop_policy="One invocation; first error closes, no retry/repair/force; cooperative force/tangent entry and final checks plus original F3 monitor",
        inherited_gate_scope="Original production gates retained; independent reference gates recorded only and not evaluated here")
    write(stage/"production_protocol.json", protocol)
    assert all(sha(root/name) == pin for name, pin in bindings.items())
    write(stage/"installation_receipt.json", dict(status="installed_not_executed", baseline_commit=HEAD,
        protocol_sha256=sha(stage/"production_protocol.json"), archive=archive,
        current_source_closure=sources, reused_task_sha256=inputs[case["task_file"]],
        bindings_count=len(bindings), formal_source_changes=0, scientific_calls=0))
    (stage/"author/INDEX.md").write_text(
        "Selected real API source-only candidates and static reviews. Historical source facts/costs are context, not new qualification. "
        "Original absolute author paths are provenance only; runtime inputs are repository-relative.\n\n"+
        "\n".join(f"- [{name}]({name}): {record['source_name']} | SHA {record['sha256']}" for name, record in archive.items())+"\n",
        encoding="utf-8")
    print(json.dumps(dict(status="installed_not_executed", stage=STAGE, bindings=len(bindings))))


if __name__ == "__main__":
    main()
