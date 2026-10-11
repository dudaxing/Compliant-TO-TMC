"""Incremental M-RESUME1 completed saved-start delivery; ordinary metadata only.

Stage every allowed delta before finalize. This tool only writes the manifest
and exclusive external receipts; commit, push and restore are separate actions.
Old archive entries are inherited, while only new-stage/two-front bytes are hashed.
"""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

BASE = "8b456dcdc2c0566fb2e927175a781712dd5e78ec"
REL = "lf_data_preparation/native_interface_001/saved_continuation_001"
MANIFEST = "handoff/repository_manifest.json"
CONFIG = REL+"/author/execution_delivery_config.json"
FRONTS = {"docs/CURRENT_STATUS.md", "docs/RESUME_DEVELOPMENT.md"}
ORIGIN = "https://github.com/dudaxing/Compliant-TO-TMC.git"
read = lambda path: json.loads(path.read_bytes())
git = lambda root,*args: subprocess.check_output(["git","-c","gc.auto=0",*args],cwd=root)
names = lambda raw: {part.decode("utf-8") for part in raw.split(b"\0") if part}
digest = lambda raw: sha256(raw).hexdigest()


def sha(path):
    value = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda:stream.read(1024*1024),b""):
            value.update(block)
    return value.hexdigest()


def identity(root,name):
    path = (root/name).resolve()
    path.relative_to(root)
    assert path.relative_to(root).as_posix() == name
    return dict(path=name,bytes=path.stat().st_size,sha256=sha(path))


def write_new(path,value):
    with path.open("x",encoding="utf-8",newline="\n") as stream:
        stream.write(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+"\n")


def branch_origin(root):
    assert git(root,"branch","--show-current").decode().strip() == "main"
    assert git(root,"remote","get-url","origin").decode().strip() == ORIGIN
    assert git(root,"remote","get-url","--push","origin").decode().strip() == ORIGIN


def previous_manifest(root,config):
    record = config["previous_publication_receipt"]
    assert record["path"].startswith(REL+"/author/")
    proof = read(root/record["path"])
    assert sha(root/record["path"]) == record["sha256"]
    assert proof["status"] == "published_and_incrementally_restored_pass" and proof["published_commit"] == BASE
    assert proof["source_and_restore_clean"] is True and proof["remote_main_confirmed_equal"] is True
    assert proof["prepared_card"] == "M-RESUME1" and proof["prepared"] is True
    assert proof["authorized"] is False and proof["executed"] is False
    raw = git(root,"show",BASE+":"+MANIFEST)
    assert digest(raw) == proof["manifest_sha256"]
    old = json.loads(raw)
    entries = {row["path"]:row for row in old["files"]}
    assert len(entries) == len(old["files"]) == proof["ordinary_manifest_files"]
    assert sum(row["bytes"] for row in entries.values()) == proof["ordinary_manifest_bytes"]
    assert old["science_version"] == "0.5.0"
    assert len(entries) == 18915 and sum(row["bytes"] for row in entries.values()) == 9657472556
    assert len([name for name in entries if name.startswith(REL+"/")]) == 43
    return raw,old,entries


def execution_checks(root,external,config,entries):
    """Bind a completed outer and actual saved records; never replay science."""
    stage = root/REL
    status = config["execution_status"]
    assert config["source_commit"] == BASE and status in ("pass","not_pass")
    assert config["authorized"] is config["executed"] is config["execution_closed"] is True
    protocol_file = stage/"protocol.json"
    assert entries[REL+"/protocol.json"]["sha256"] == config["protocol_sha256"]
    protocol = read(protocol_file)
    assert protocol["card"] == "M-RESUME1" and protocol["prepared"] is True
    assert protocol["authorized"] is protocol["executed"] is False
    assert len(protocol["bindings"]) == 100 and protocol["bindings"] == config["binding_pins"]
    assert all(entries[name]["sha256"] == pin for name,pin in config["binding_pins"].items())
    assert {path.relative_to(root).as_posix() for path in stage.rglob("*") if path.is_file()} == {
        name for name in entries if name.startswith(REL+"/")}
    auth,reply = read(stage/"author/authorization.json"),read(stage/"author/direct_human_reply.json")
    assert auth["authorized"] is True and auth["card"] == reply["card"] == "M-RESUME1"
    assert auth["approved_source_commit"] == reply["approved_source_commit"] == BASE
    assert auth["protocol_sha256"] == config["protocol_sha256"]
    assert auth["authorization_from_direct_human_reply"] is reply["authorization_from_direct_human_reply"] is True
    assert auth["human_evidence_sha256"] == entries[REL+"/author/direct_human_reply.json"]["sha256"]
    assert auth["source_publication_receipt_sha256"] == config["previous_publication_receipt"]["sha256"]
    assert auth["direct_human_answer"] == reply["direct_human_answer"] and reply["direct_human_answer"].strip() and reply["reply_context"]
    outer_name = REL+"/production_launch.json"
    outer = read(root/outer_name)
    assert outer["status"] == status and outer["completed_utc"] and outer["phase"] == "production" and outer["invocations"] == 1
    assert outer["protocol_sha256"] == config["protocol_sha256"] and outer["bindings"] == protocol["bindings"]
    terminal_name = config["terminal_review_path"]
    assert terminal_name in config["review_pins"]
    terminal = read(root/terminal_name)
    assert terminal["status"].startswith("pass") and terminal["execution_status"] == status
    assert terminal["outer_sha256"] == entries[outer_name]["sha256"]
    # NOT_PASS may lack a completed helper or complete result/view. Preserve real
    # files and the independent terminal classification, rather than invent them.
    run = stage/"run_001"
    helper_file = run/"execution_receipt.json"
    if status == "pass":
        helper = read(helper_file)
        assert outer["exit_code"] == 0 and outer["stop_reason"] is None and outer["all_bindings_unchanged"] is True
        assert helper is not None and helper["status"] == "pass" and helper["all_bindings_unchanged"] is True
        assert helper["protocol_sha256"] == config["protocol_sha256"] and helper["approved_source_commit"] == BASE
        assert helper["cached_production_gates"]["passed"] is True
        assert helper["HP_calls"] == helper["JIT_calls"] == 0
        N = helper["accepted_states"]
        assert 2 <= N <= 9 and all(helper["counts"][kind+suffix] == 1
            for kind in ("focused_tests","api","model","solve","save","summary","view_child") for suffix in ("_started","_completed"))
        tests = read(run/"focused_test_receipt.json")
        assert tests["status"] == "pass" and tests["collected_nodeids"] == protocol["focused_test_nodeids"]
        result = read(root/protocol["candidate_directory"]/"result.json")
        assert result["status"] == "success" and result["path_completed"] is True and result["unload_endpoint_reached"] is True
        assert result["accepted_states"] == len(result["states"]) == N and result["targets_mm"] == [1.2,1.15]
        assert result["task_target_executed"] is result["full_original_path_completed"] is False
        continuation = result["continuation"]
        assert continuation["segment_completed"] is continuation["anchor_revalidated"] is continuation["anchor_identity_preserved"] is True
        assert continuation["parent_status"] == "failed" and continuation["parent_failure"]["code"] == "time_limit"
        assert continuation["parent_path_completed"] is continuation["parent_task_target_executed"] is continuation["parent_unload_endpoint_reached"] is False
        assert continuation["full_original_path_executed_by_child"] is False and continuation["original_target_indices"] == [13,14]
        originals = [row for row in result["states"] if row["is_original_target"]]
        assert [(row["d"],row["original_target_index"],row["leg"]) for row in originals] == [(1.2,13,"resume_origin"),(1.15,14,"unloading")]
        assert all(result[flag] is False for flag in ("independent_HP_qualified","equilibrium_qualified","HF_qualified"))
        views = read(root/protocol["view_directory"]/"view.json")
        assert views["status"] == "pass" and all(views[key] == N for key in ("geometry_started","geometry_completed","nodal_started","nodal_completed"))
        assert views["new_F_T_model_solver_HP_calls"] == 0 and views["contact_pressure_clamping_qualified"] is False
        assert helper["actual_PNGs"] == 3 and helper["actual_GIF_frames"] == N
        assert helper["production_selected_NPZ_files"] == 2 and helper["production_selected_fields"] == 6
        assert helper["original_parent_full_path_still_NOT_PASS"] is True and helper["new_HP_pressure_clamp_stability_HF5_qualified"] is False
        output_names = {path.relative_to(root).as_posix() for path in run.rglob("*") if path.is_file()}
        assert output_names == helper["outputs"].keys() | {helper_file.relative_to(root).as_posix()}
        assert all(entries[name]["sha256"] == pin for name,pin in helper["outputs"].items())
        assert helper["executed_source_package_unchanged"] is True
        assert all(entries[name]["sha256"] == pin for name,pin in helper["executed_source_package_SHA256"].items())
    else:
        assert outer["exit_code"] != 0 or outer["stop_reason"] is not None or outer["all_bindings_unchanged"] is False
        # A partial/missing/malformed helper is preserved as raw evidence and
        # classified by the independent terminal review, not parsed as success.
    assert len(config["review_pins"]) >= 3 and all(entries[name]["sha256"] == pin for name,pin in config["review_pins"].items())
    doc_name = config["documentation_receipt_path"]
    assert doc_name.startswith(REL+"/author/")
    doc = read(root/doc_name)
    assert doc["status"] == "pass_actual_execution_documentation_closed" and doc["execution_closed"] is True
    assert doc["source_commit"] == BASE and doc["protocol_sha256"] == config["protocol_sha256"] and doc["execution_status"] == status
    assert doc["result_sha256"] == entries[REL+"/RESULTS.md"]["sha256"] and doc["next_step_sha256"] == entries[REL+"/NEXT_STEP_REVIEW.md"]["sha256"]
    assert doc["front_history"] == config["front_history"]
    assert doc["actions"] and all(value == 0 for value in doc["actions"].values())
    assert doc["qualification"] and all(value is False for value in doc["qualification"].values())
    assert {row["path"] for row in config["front_history"]} == FRONTS and len(config["front_history"]) == 2
    for row in config["front_history"]:
        prior,current = git(root,"show",BASE+":"+row["path"]),(root/row["path"]).read_bytes()
        assert current.count(prior) == 1 and len(prior) == row["old_bytes"]
        assert digest(prior) == row["old_sha256"] and entries[row["path"]]["sha256"] == row["new_sha256"]
        assert row["history_end_byte_exclusive"] == row["history_start_byte"]+len(prior)
        assert current[row["history_start_byte"]:row["history_end_byte_exclusive"]] == prior
        assert row["old_body_preserved_exactly"] is True
    final_name = config["final_review_path"]
    assert final_name.startswith(REL+"/author/") and final_name in config["allowed_delta_paths"]
    final = read(root/final_name)
    assert final["status"].startswith("pass") and final["config_sha256"] == sha(root/CONFIG)
    assert final["authorized"] is final["executed"] is final["execution_closed"] is True and final["execution_status"] == status
    expected_reviewed = (set(config["allowed_delta_paths"])-{final_name}) | set(config["binding_pins"])
    assert expected_reviewed <= final["reviewed_repository_SHA256"].keys() and final_name not in final["reviewed_repository_SHA256"]
    assert final["reviewed_external_SHA256"]["deliver_execution.py"] == sha(external/"deliver_execution.py")
    for name,pin in final["reviewed_external_SHA256"].items():
        path = (external/name).resolve(); path.relative_to(external)
        assert sha(path) == pin
    for name,pin in final["reviewed_repository_SHA256"].items():
        assert entries[name]["sha256"] == pin
    assert entries[REL+"/author/deliver_execution.py"]["sha256"] == sha(external/"deliver_execution.py")
    return protocol


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=("finalize","verify"))
    parser.add_argument("--repo",type=Path,required=True)
    parser.add_argument("--restore",type=Path,default=Path("D:/hf-restore-20260930"))
    parser.add_argument("--external-base",type=Path,default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    root,restore,external = args.repo.resolve(),args.restore.resolve(),args.external_base.resolve()
    config = read(root/CONFIG)
    oldraw,old,old_entries = previous_manifest(root,config)
    allowed = set(config["allowed_delta_paths"])
    assert len(allowed) == len(config["allowed_delta_paths"]) and FRONTS <= allowed and MANIFEST not in allowed
    assert all(name in FRONTS or name.startswith(REL+"/") for name in allowed)
    assert CONFIG in allowed
    delta_path = external/"execution_delivery_delta_verify.json"
    if args.mode == "finalize":
        assert not delta_path.exists() and git(root,"rev-parse","HEAD").decode().strip() == BASE
        branch_origin(root)
        assert (root/MANIFEST).read_bytes() == oldraw
        assert not git(root,"diff","--name-only") and not git(root,"ls-files","--others","--exclude-standard","-z")
        paths = names(git(root,"ls-files","-z"))-{MANIFEST}
        changed = names(git(root,"diff","--cached","--name-only","-z",BASE))
        new = paths-old_entries.keys()
        assert not (old_entries.keys()-paths) and changed == allowed == FRONTS|new
        assert all(name.startswith(REL+"/") for name in new)
        delta = [identity(root,name) for name in sorted(allowed)]
        entries = dict(old_entries,**{row["path"]:row for row in delta})
        protocol = execution_checks(root,external,config,entries)
        manifest = dict(old,created_utc=datetime.now(timezone.utc).isoformat(),previous_delivery_commit=BASE,
            storage_stage="saved_native_continuation_execution_closed_001",files=[entries[name] for name in sorted(paths)])
        raw = (json.dumps(manifest,ensure_ascii=False,indent=2,allow_nan=False)+"\n").encode("utf-8")
        (root/MANIFEST).write_bytes(raw)
        receipt = dict(status="incremental_execution_delivery_pass",previous_delivery_commit=BASE,
            manifest_sha256=digest(raw),config_sha256=sha(root/CONFIG),ordinary_manifest_files=len(paths),
            ordinary_manifest_bytes=sum(row["bytes"] for row in entries.values()),delta_files=delta,
            delta_bytes=sum(row["bytes"] for row in delta),new_files=len(new),changed_old_files=2,
            unchanged_manifest_entries_exactly_inherited=len(old_entries)-2,protocol_sha256=config["protocol_sha256"],
            binding_count=len(protocol["bindings"]),front_history=config["front_history"],
            previous_publication_receipt=config["previous_publication_receipt"],executed_card="M-RESUME1",
            execution_status=config["execution_status"],authorized=True,executed=True,execution_closed=True,new_full_source_scan=False,
            new_NPZ_decodes_or_HF_calls_or_plots=0,original_science_and_qualification_unchanged=True,whole_HF5_complete=False)
        write_new(delta_path,receipt)
    else:
        source = read(delta_path)
        assert source["status"] == "incremental_execution_delivery_pass" and source["config_sha256"] == sha(root/CONFIG)
        assert source["executed_card"] == "M-RESUME1" and source["execution_status"] == config["execution_status"]
        assert source["authorized"] is True and source["executed"] is True and source["execution_closed"] is True
        commit = git(root,"rev-parse","HEAD").decode().strip()
        assert commit != BASE and git(root,"rev-parse","HEAD^").decode().strip() == BASE
        assert git(root,"ls-remote","--heads","origin","main").decode().split() == [commit,"refs/heads/main"]
        for tree in (root,restore):
            branch_origin(tree)
            assert git(tree,"rev-parse","HEAD").decode().strip() == commit and not git(tree,"status","--porcelain")
        assert (root/MANIFEST).read_bytes() == (restore/MANIFEST).read_bytes() and sha(restore/MANIFEST) == source["manifest_sha256"]
        assert (root/CONFIG).read_bytes() == (restore/CONFIG).read_bytes()
        manifest = read(restore/MANIFEST)
        entries = {row["path"]:row for row in manifest["files"]}
        assert len(entries) == len(manifest["files"]) == source["ordinary_manifest_files"]
        assert sum(row["bytes"] for row in entries.values()) == source["ordinary_manifest_bytes"]
        for tree in (root,restore):
            assert names(git(tree,"ls-files","-z")) == entries.keys()|{MANIFEST}
        assert names(git(root,"diff","--name-only","-z",BASE,commit)) == allowed|{MANIFEST}
        assert {row["path"] for row in source["delta_files"]} == allowed
        assert all(identity(tree,row["path"]) == row == entries[row["path"]] for tree in (root,restore) for row in source["delta_files"])
        unchanged = old_entries.keys()-allowed
        assert len(unchanged) == source["unchanged_manifest_entries_exactly_inherited"]
        assert all(entries[name] == old_entries[name] for name in unchanged)
        assert manifest["science_version"] == old["science_version"] == "0.5.0"
        assert manifest["science_baseline_commit"] == old["science_baseline_commit"]
        protocol = execution_checks(restore,external,config,entries)
        assert source["protocol_sha256"] == config["protocol_sha256"] and source["front_history"] == config["front_history"]
        receipt = dict(status="published_and_incrementally_restored_pass",created_utc=datetime.now(timezone.utc).isoformat(),
            published_commit=commit,previous_delivery_commit=BASE,branch="main",origin=ORIGIN,
            remote_main_confirmed_equal=True,source_and_restore_clean=True,restore_root=str(restore),
            manifest_sha256=source["manifest_sha256"],ordinary_manifest_files=len(entries),
            ordinary_manifest_bytes=source["ordinary_manifest_bytes"],delta_files_restored_and_hashed=len(allowed),
            delta_bytes=source["delta_bytes"],unchanged_manifest_entries_inherited=len(unchanged),
            protocol_sha256=config["protocol_sha256"],binding_count=len(protocol["bindings"]),
            front_history=config["front_history"],previous_publication_receipt=config["previous_publication_receipt"],
            executed_card="M-RESUME1",execution_status=config["execution_status"],authorized=True,executed=True,execution_closed=True,
            original_science_and_qualification_unchanged=True,new_full_source_or_restore_scan=False,
            new_NPZ_decodes_or_HF_calls_or_plots=0,whole_HF5_complete=False)
        write_new(external/"execution_publication_receipt.json",receipt)
    print(json.dumps({key:value for key,value in receipt.items() if key not in ("delta_files","front_history")},ensure_ascii=False))


if __name__ == "__main__":
    main()
