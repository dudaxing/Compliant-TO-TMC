"""Incremental M-ALPHA1 execution delivery; ordinary bytes only, no commit/push.

Only three old fronts may change. All other delta files are genuine new files;
old manifest entries are inherited without rescanning the old science archive.
Metadata delivery pass and actual execution pass/not_pass remain separate.
"""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess

BASE = "64a19f7d990d294d09f16145eae946e0edfa1580"
REL = "lf_data_preparation/native_interface_001/regularization_sensitivity_001"
M = "handoff/repository_manifest.json"
PROTOCOL_SHA = "430137c7e81cb12281937a6201519235fcc161de0503323684541c1c72b94d11"
PROOF = REL + "/author/M_ALPHA1_source_publication_receipt.json"
PROOF_SHA = "60f125e01524728632020d10c3541b8e7a200ff3a55e0b2a39a83940b86ab83a"
CONFIG = REL + "/author/execution_delivery_config.json"
FINAL = REL + "/author/execution_final_delivery_static_review.json"
FRONTS = {"docs/CURRENT_STATUS.md", "docs/RESUME_DEVELOPMENT.md", REL + "/README.md"}
ORIGIN = "https://github.com/dudaxing/Compliant-TO-TMC.git"
TOOLS = ("deliver_execution.py", "configure_execution_delivery.py", "close_execution_docs.py")
ROOT_DEFAULT = Path("D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC")
read = lambda p: json.loads(p.read_bytes())
git = lambda root, *args: subprocess.check_output(["git", "-c", "gc.auto=0", *args], cwd=root)
names = lambda data: {n.decode("utf-8") for n in data.split(b"\0") if n}


def sha(path):
    value = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024*1024), b""):
            value.update(block)
    return value.hexdigest()


def write_new(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def identity(root, name):
    path = (root/name).resolve()
    path.relative_to(root)
    return dict(path=name, bytes=path.stat().st_size, sha256=sha(path))


def source_metadata(root):
    proof = read(root/PROOF)
    assert sha(root/PROOF) == PROOF_SHA
    assert proof["status"] == "published_and_incrementally_restored_pass"
    assert proof["published_commit"] == BASE and proof["source_and_restore_clean"] and proof["remote_main_confirmed_equal"]
    assert proof["authorized"] is False and proof["executed"] is False
    raw = git(root, "show", BASE + ":" + M)
    assert sha256(raw).hexdigest() == proof["manifest_sha256"]
    old = json.loads(raw)
    entries = {e["path"]: e for e in old["files"]}
    assert len(entries) == len(old["files"]) == proof["ordinary_manifest_files"] == 18651
    assert sum(e["bytes"] for e in entries.values()) == proof["ordinary_manifest_bytes"] == 9296517834
    assert old["science_version"] == "0.5.0"
    return raw, old, entries


def terminal_metadata(root, terminal_path):
    """Read already-reviewed actual snapshots, never execute the reader again."""
    stage = root/REL
    protocol, terminal = read(stage/"protocol.json"), read(terminal_path)
    assert sha(stage/"protocol.json") == PROTOCOL_SHA
    assert protocol["card"] == "M-ALPHA1" and protocol["prepared"] is True
    assert protocol["authorized"] is False and protocol["executed"] is False
    assert len(protocol["bindings"]) == 57
    assert all(sha(root/n) == pin for n,pin in protocol["bindings"].items())
    assert terminal["status"].startswith("pass_terminal_record_review_execution_")
    status = terminal["execution_status"]
    assert status in ("pass", "not_pass") and terminal["source_commit"] == BASE
    assert terminal["protocol_sha256"] == PROTOCOL_SHA
    auth, reply = read(stage/"author/authorization.json"), read(stage/"author/direct_human_reply.json")
    assert auth["authorized"] is True and auth["card"] == reply["card"] == "M-ALPHA1"
    assert auth["approved_source_commit"] == reply["approved_source_commit"] == BASE
    assert auth["protocol_sha256"] == PROTOCOL_SHA
    assert auth["authorization_from_direct_human_reply"] is True and reply["authorization_from_direct_human_reply"] is True
    assert auth["human_evidence_sha256"] == sha(stage/"author/direct_human_reply.json")
    assert auth["source_publication_receipt_sha256"] == sha(root/PROOF) == PROOF_SHA
    assert auth["direct_human_answer"] == reply["direct_human_answer"] and reply["direct_human_answer"].strip() and reply["reply_context"]
    outer = read(stage/"production_launch.json")
    helper_path = stage/"run_001/execution_receipt.json"
    helper = read(helper_path) if helper_path.is_file() else None
    assert outer["status"] in ("pass", "not_pass") and outer["completed_utc"]
    assert outer["invocations"] == 1 and outer["protocol_sha256"] == PROTOCOL_SHA
    assert terminal["actual_launch"] == outer and terminal["actual_helper"] == helper
    if status == "pass":
        assert outer["status"] == helper["status"] == "pass" and terminal["success_record_checks"] is not None
    else:
        assert outer["status"] == "not_pass" or helper is not None and helper["status"] == "not_pass"
        assert terminal["success_record_checks"] is None
    return protocol, terminal


def closed_documentation(root):
    stage = root/REL
    doc = read(stage/"author/execution_documentation_receipt.json")
    protocol, terminal = terminal_metadata(root, stage/"author/execution_terminal_review.json")
    assert doc["status"] == "pass_actual_execution_documentation_closed" and doc["execution_closed"] is True
    assert doc["source_commit"] == BASE and doc["protocol_sha256"] == PROTOCOL_SHA
    assert doc["execution_status"] == terminal["execution_status"]
    assert doc["result_sha256"] == sha(stage/"RESULTS.md") and doc["next_step_sha256"] == sha(stage/"NEXT_STEP_REVIEW.md")
    assert all(v == 0 for v in doc["actions"].values())
    assert all(v is False for v in doc["qualification"].values())
    for name,pin in doc["archived_source_and_review_SHA256"].items():
        assert sha(root/name) == pin, name
    assert {row["path"] for row in doc["front_history"]} == FRONTS
    for row in doc["front_history"]:
        prior, current = git(root, "show", BASE + ":" + row["path"]), (root/row["path"]).read_bytes()
        assert current.count(prior) == 1 and len(prior) == row["old_bytes"]
        assert sha256(prior).hexdigest() == row["old_sha256"]
        assert current[row["history_start_byte"]:row["history_end_byte_exclusive"]] == prior
        assert sha(root/row["path"]) == row["new_sha256"]
    for name in FRONTS | {REL + "/RESULTS.md", REL + "/NEXT_STEP_REVIEW.md"}:
        text = (root/name).read_text(encoding="utf-8").split("<details>", 1)[0]
        assert "\ufffd" not in text
        for target in re.findall(r"\]\(([^)]+)\)", text):
            if "://" in target or target.startswith("#"):
                continue
            path = ((root/name).parent/target.split("#")[0]).resolve()
            path.relative_to(root)
            assert path.exists(), (name,target)
    return protocol, terminal, doc


def delivery_checks(root, external, config, entries):
    protocol, terminal, doc = closed_documentation(root)
    assert config["source_commit"] == BASE and config["protocol_sha256"] == PROTOCOL_SHA and config["binding_count"] == 57
    assert config["execution_status"] == terminal["execution_status"]
    for name,pin in config["record_pins"].items():
        assert entries[name]["sha256"] == pin, (name,"record")
    for name,pin in config["review_pins"].items():
        assert entries[name]["sha256"] == pin
    inventory = terminal["actual_run_file_inventory"]
    actual_run = {p.relative_to(root).as_posix() for p in (root/REL/"run_001").rglob("*") if p.is_file()}
    assert actual_run == set(inventory)
    assert all(entries[name]["sha256"] == item["sha256"] and entries[name]["bytes"] == item["bytes"] for name,item in inventory.items())
    final = read(root/FINAL)
    assert final["status"].startswith("pass_actual_results_documentation_and_incremental_delivery_static_review")
    assert final["config_sha256"] == sha(external/"execution_delivery_config.json")
    assert set(TOOLS) <= final["reviewed_external_SHA256"].keys()
    for name,pin in final["reviewed_external_SHA256"].items():
        assert sha(external/name) == pin
    for name,pin in final["reviewed_repository_SHA256"].items():
        assert entries[name]["sha256"] == pin
    for name in TOOLS:
        assert entries[REL+"/author/"+name]["sha256"] == sha(external/name)
    return protocol, terminal, doc


def branch_origin(root):
    assert git(root, "branch", "--show-current").decode().strip() == "main"
    assert git(root, "remote", "get-url", "origin").decode().strip() == ORIGIN
    assert git(root, "remote", "get-url", "--push", "origin").decode().strip() == ORIGIN


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("finalize", "verify"))
    parser.add_argument("--repo", type=Path, default=ROOT_DEFAULT)
    parser.add_argument("--restore", type=Path, default=Path("D:/hf-restore-20260930"))
    parser.add_argument("--external-base", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    root, restore, external = args.repo.resolve(), args.restore.resolve(), args.external_base.resolve()
    config_path = external/"execution_delivery_config.json"
    config = read(config_path)
    assert (root/CONFIG).read_bytes() == config_path.read_bytes()
    oldraw, old, old_entries = source_metadata(root)
    allowed = set(config["allowed_delta_paths"])
    assert FRONTS <= allowed and M not in allowed
    assert all(n in FRONTS or n.startswith(REL+"/") for n in allowed)
    delta_path = external/"execution_delivery_delta_verify.json"
    if args.mode == "finalize":
        assert not delta_path.exists() and git(root, "rev-parse", "HEAD").decode().strip() == BASE
        branch_origin(root)
        assert (root/M).read_bytes() == oldraw
        assert not git(root, "diff", "--name-only") and not git(root, "ls-files", "--others", "--exclude-standard", "-z")
        paths = names(git(root, "ls-files", "-z")) - {M}
        changed = names(git(root, "diff", "--cached", "--name-only", "-z", BASE))
        new = paths - old_entries.keys()
        assert not (old_entries.keys()-paths) and changed == allowed == FRONTS | new
        delta = [identity(root,n) for n in sorted(allowed)]
        entries = dict(old_entries, **{e["path"]:e for e in delta})
        protocol, terminal, doc = delivery_checks(root, external, config, entries)
        manifest = dict(old, created_utc=datetime.now(timezone.utc).isoformat(), previous_delivery_commit=BASE,
            storage_stage="alpha_prefix_execution_closed_001", files=[entries[n] for n in sorted(paths)])
        raw = (json.dumps(manifest,ensure_ascii=False,indent=2,allow_nan=False)+"\n").encode("utf-8")
        (root/M).write_bytes(raw)
        receipt = dict(status="incremental_execution_delivery_pass", previous_delivery_commit=BASE,
            manifest_sha256=sha256(raw).hexdigest(), config_sha256=sha(config_path),
            ordinary_manifest_files=len(paths), ordinary_manifest_bytes=sum(e["bytes"] for e in entries.values()),
            delta_files=delta, delta_bytes=sum(e["bytes"] for e in delta), new_files=len(new), changed_old_files=3,
            unchanged_manifest_entries_exactly_inherited=len(old_entries)-3, protocol_sha256=PROTOCOL_SHA,
            binding_count=57, execution_status=terminal["execution_status"], front_history=doc["front_history"],
            authorized=True, executed=True, execution_closed=True, new_full_source_scan=False,
            new_NPZ_decodes_or_HF_calls_or_renders=0, original_science_and_qualification_unchanged=True, whole_HF5_complete=False)
        write_new(delta_path,receipt)
    else:
        source = read(delta_path)
        assert source["status"] == "incremental_execution_delivery_pass" and source["execution_closed"]
        assert source["config_sha256"] == sha(config_path)
        commit = git(root,"rev-parse","HEAD").decode().strip()
        assert commit != BASE and git(root,"rev-parse","HEAD^").decode().strip() == BASE
        assert git(root,"ls-remote","--heads","origin","main").decode().split() == [commit,"refs/heads/main"]
        for tree in (root,restore):
            branch_origin(tree)
            assert git(tree,"rev-parse","HEAD").decode().strip() == commit and not git(tree,"status","--porcelain")
        assert (root/M).read_bytes() == (restore/M).read_bytes() and sha(restore/M) == source["manifest_sha256"]
        assert (restore/CONFIG).read_bytes() == config_path.read_bytes()
        manifest = read(restore/M)
        entries = {e["path"]:e for e in manifest["files"]}
        assert len(entries) == len(manifest["files"]) == source["ordinary_manifest_files"]
        assert sum(e["bytes"] for e in entries.values()) == source["ordinary_manifest_bytes"]
        for tree in (root,restore):
            assert names(git(tree,"ls-files","-z")) == entries.keys() | {M}
        assert names(git(root,"diff","--name-only","-z",BASE,commit)) == allowed | {M}
        assert {e["path"] for e in source["delta_files"]} == allowed
        assert all(identity(tree,e["path"]) == e == entries[e["path"]] for tree in (root,restore) for e in source["delta_files"])
        unchanged = old_entries.keys()-allowed
        assert len(unchanged) == source["unchanged_manifest_entries_exactly_inherited"]
        assert all(entries[n] == old_entries[n] for n in unchanged)
        assert manifest["science_version"] == old["science_version"] == "0.5.0"
        assert manifest["science_baseline_commit"] == old["science_baseline_commit"]
        protocol, terminal, doc = delivery_checks(restore,external,config,entries)
        assert terminal["execution_status"] == source["execution_status"] and doc["front_history"] == source["front_history"]
        receipt = dict(status="published_and_incrementally_restored_pass", created_utc=datetime.now(timezone.utc).isoformat(),
            published_commit=commit, previous_delivery_commit=BASE, branch="main", origin=ORIGIN,
            remote_main_confirmed_equal=True, source_and_restore_clean=True, restore_root=str(restore),
            manifest_sha256=source["manifest_sha256"], ordinary_manifest_files=len(entries),
            ordinary_manifest_bytes=source["ordinary_manifest_bytes"], delta_files_restored_and_hashed=len(allowed),
            delta_bytes=source["delta_bytes"], unchanged_manifest_entries_inherited=len(unchanged),
            protocol_sha256=PROTOCOL_SHA, binding_count=57, execution_status=source["execution_status"],
            authorized=True, executed=True, execution_closed=True, front_history=doc["front_history"],
            new_full_source_or_restore_scan=False, new_NPZ_decodes_or_HF_calls_or_renders=0,
            original_science_and_qualification_unchanged=True, whole_HF5_complete=False)
        write_new(external/"execution_publication_receipt.json",receipt)
    print(json.dumps({k:v for k,v in receipt.items() if k not in ("delta_files","front_history")},ensure_ascii=False))


if __name__ == "__main__":
    main()
