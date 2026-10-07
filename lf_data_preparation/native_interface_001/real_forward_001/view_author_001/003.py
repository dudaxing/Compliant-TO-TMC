"""Freeze one reviewed saved view only after real production and fresh reference pass."""
from pathlib import Path
import argparse
import ast
import hashlib
import json

CONTROL = "lf_data_preparation/native_interface_001/real_forward_001"
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
    stage = root/CONTROL
    assert not author.is_relative_to(root)
    files = [author/"execute_saved_api_view.py", Path(__file__).resolve()]
    reports = [args.root_review.resolve(), args.peer_review.resolve()]
    for source in files:
        compile(ast.parse(source.read_text(encoding="utf-8")), str(source), "exec")
    for report_file in reports:
        report = read(report_file)
        assert report["status"] == "pass_static_only" and not report["blocking_findings"]
        for source in files:
            pins = {pin for name, pin in report["source_sha256"].items() if Path(name).name == source.name}
            assert pins == {sha(source)}
    run = stage/"run_001"
    result_file = run/"result/result.json"
    result, model = read(result_file), read(run/"result/model/model.json")
    audit_file = run/"audit/summary.json"
    audit = read(audit_file)
    n = len(result["states"])
    assert result["status"] == "success" and result["task_target_executed"] is True
    assert audit["status"] == "pass" and audit["result_sha256"] == sha(result_file)
    assert audit["accepted_states"] == len(audit["states"]) == n
    assert audit["HP_calls_started"] == audit["HP_calls_completed"] == 2*n
    assert audit["full_element_and_DOF_coverage"] is True
    assert all(row["index"] == i and row["status"] == "pass" and row["HP_calls"] == 2
        and row["state_sha256"] == state["state_sha256"] and row["target_mm"] == state["d"]
        for i, (row, state) in enumerate(zip(audit["states"], result["states"])))
    prerequisites = {
        "production": dict(protocol_file=CONTROL+"/production_protocol.json",
            launch_file=CONTROL+"/production_launch.json",
            receipt_file=CONTROL+"/run_001/execution_receipt.json", receipt_RSS_field="peak_sampled_RSS_bytes"),
        "reference": dict(protocol_file=CONTROL+"/reference_protocol.json",
            launch_file=CONTROL+"/reference_launch.json",
            receipt_file=CONTROL+"/run_001/audit/execution_receipt.json", receipt_RSS_field="peak_sampled_RSS_bytes")}
    bindings = {}
    for role, dependency in prerequisites.items():
        control = read(root/dependency["protocol_file"])
        launch, receipt = read(root/dependency["launch_file"]), read(root/dependency["receipt_file"])
        limits = control["phases"][role]
        assert launch["status"] == receipt["status"] == "pass"
        assert launch["invocations"] == 1 and launch["exit_code"] == 0 and launch["stop_reason"] is None
        assert launch["all_bindings_unchanged"] is receipt["all_bindings_unchanged"] is True
        assert launch["protocol_sha256"] == receipt["protocol_sha256"] == sha(root/dependency["protocol_file"])
        assert launch["elapsed_seconds"] <= limits["outer_seconds"]
        assert receipt["elapsed_seconds"] <= limits["helper_seconds"]
        assert max(launch["peak_sampled_tree_RSS_bytes"], receipt[dependency["receipt_RSS_field"]]) <= control["sampled_RSS_bytes"]
        assert all(sha(root/name) == pin for name, pin in control["bindings"].items())
        bindings.update(control["bindings"])
        for name in ("protocol_file", "launch_file", "receipt_file"):
            logical = dependency[name]
            bindings[logical] = sha(root/logical)
    reference_receipt = read(root/prerequisites["reference"]["receipt_file"])
    assert reference_receipt["result_sha256"] == sha(result_file)
    assert reference_receipt["summary_sha256"] == sha(audit_file)
    assert reference_receipt["accepted_states"] == n
    assert reference_receipt["HP_calls_started"] == reference_receipt["HP_calls_completed"] == 2*n
    assert all(reference_receipt[name] == 0 for name in
               ("candidate_force_calls", "candidate_tangent_calls", "solver_calls", "model_constructions"))
    for mapping in (audit["source_bindings"], audit["input_bindings"]):
        for name, pin in mapping.items():
            assert sha(root/name) == pin
            bindings[name] = pin
    # Saved file SHA verification only, not array loading or any scientific evaluation.
    for path in (run/"result").rglob("*"):
        if path.is_file():
            bindings[path.relative_to(root).as_posix()] = sha(path)
    bindings[audit_file.relative_to(root).as_posix()] = sha(audit_file)
    for path in [stage/"view_protocol.json", stage/"view_launch.json", stage/"view_stdout.log",
                 run/"view", run/"qualified_response.json", run/"view_execution_receipt.json", stage/"view_author_001"]:
        assert not path.exists(), path
    viewer = root/"hf_repo/scripts/plot_native_mean.py"
    assert sha(viewer) == "0f6e3ae5e5c94d640f97c840a676eaf929180abd7eea5e0729e57eb0644bc7d1"
    launcher = stage/"launch_pose.py"
    assert sha(launcher) == "f3a96681afc474e42ae19875579d748237235dce90f21892b016b3b3af862477"
    archive_directory = stage/"view_author_001"
    selections = [files[0], viewer, files[1], author/"README.md", author/"author_checks.json",
                  author/"author_note.json", author/"source_additions.diff", *reports]
    assert all(path.is_file() for path in selections)
    archive_directory.mkdir()
    archive = {}
    for i, source in enumerate(selections, 1):
        destination = archive_directory/f"{i:03d}{source.suffix}"
        destination.write_bytes(source.read_bytes())
        logical = destination.relative_to(root).as_posix()
        bindings[logical] = sha(destination)
        archive[destination.name] = dict(source_name=str(source), path=logical, sha256=sha(destination))
    bindings[CONTROL+"/launch_pose.py"] = sha(launcher)
    for name in ["hf_repo/src/hf_eval/native_response.py", "hf_repo/src/hf_eval/data.py", "hf_repo/src/hf_eval/__init__.py"]:
        bindings[name] = sha(root/name)
    protocol = dict(schema_version="native-real-api-view-protocol-1.0", bindings=bindings,
        sampled_RSS_bytes=8*1024**3,
        phases=dict(view=dict(helper_seconds=60, outer_seconds=90,
            argv=[CONTROL+"/view_author_001/001.py", "--repo", ".", "--protocol", CONTROL+"/view_protocol.json"])),
        prerequisites=prerequisites, input_directory=CONTROL+"/run_001",
        viewer_file=CONTROL+"/view_author_001/002.py", actual_accepted_states=n,
        reference_HP_calls=2*n, display=dict(geometry_scale=1., supplementary_displacement_scale=1000.),
        scope="Original saved-cache viewer and new saved-only qualified response; zero new F/T/solver/model/HP",
        resource_basis="Historical same coarse2-state savedview6.699972sec;60/90sec8GiB once; only actualN is frozen",
        stop_policy="One invocation; no retry/force; complete output hashing included")
    write(stage/"view_protocol.json", protocol)
    write(stage/"view_installation_receipt.json", dict(status="installed_not_executed", archive=archive,
        protocol_sha256=sha(stage/"view_protocol.json"), bindings_count=len(bindings),
        actual_accepted_states=n, new_force_calls=0, new_tangent_calls=0,
        new_solver_calls=0, new_model_constructions=0, new_HP_calls=0))
    (archive_directory/"INDEX.md").write_text(
        "Selected saved-view source candidates/reviews; raw original viewer002.py. "
        "Author paths are provenance, not runtime dependencies. No scientific archives duplicated.\n\n"+
        "\n".join(f"- [{name}]({name}): {record['source_name']} | {record['sha256']}" for name, record in archive.items())+"\n",
        encoding="utf-8")
    print(json.dumps(dict(status="installed_not_executed", actual_accepted_states=n, bindings=len(bindings))))


if __name__ == "__main__":
    main()
