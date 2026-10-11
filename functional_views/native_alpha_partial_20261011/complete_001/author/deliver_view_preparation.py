"""Incremental M-AVIEW1 source preparation delivery; ordinary metadata only.

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

BASE = "9e2e37cce7f0441af042337d1c26c50ae660acc0"
REL = "functional_views/native_alpha_partial_20261011/complete_001"
MANIFEST = "handoff/repository_manifest.json"
CONFIG = REL+"/author/preparation_delivery_config.json"
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
    assert proof["execution_status"] == "not_pass" and proof["execution_closed"] is True
    raw = git(root,"show",BASE+":"+MANIFEST)
    assert digest(raw) == proof["manifest_sha256"]
    old = json.loads(raw)
    entries = {row["path"]:row for row in old["files"]}
    assert len(entries) == len(old["files"]) == proof["ordinary_manifest_files"]
    assert sum(row["bytes"] for row in entries.values()) == proof["ordinary_manifest_bytes"]
    assert old["science_version"] == "0.5.0"
    assert not any(name.startswith(REL+"/") for name in entries)
    return raw,old,entries


def preparation_checks(root,external,config,entries):
    stage = root/REL
    protocol_file = stage/"protocol.json"
    assert entries[REL+"/protocol.json"]["sha256"] == config["protocol_sha256"]
    protocol = read(protocol_file)
    assert protocol["card"] == "M-AVIEW1" and protocol["prepared"] is True
    assert protocol["authorized"] is False and protocol["executed"] is False
    assert protocol["bindings"] == config["binding_pins"]
    assert all(entries[name]["sha256"] == pin for name,pin in config["binding_pins"].items())
    assert not (stage/"run_001").exists()
    forbidden = {"authorization.json","direct_human_reply.json","stop_requested.txt",
        "view_launch.json","view_stdout.log","view_stderr.log","alpha_partial_view_receipt.json"}
    assert not any(path.name in forbidden for path in stage.rglob("*"))
    assert {path.relative_to(root).as_posix() for path in stage.rglob("*") if path.is_file()} == {
        name for name in entries if name.startswith(REL+"/")}
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
    assert final["authorized"] is False and final["executed"] is False
    expected_reviewed = (set(config["allowed_delta_paths"])-{final_name}) | set(config["binding_pins"])
    assert expected_reviewed <= final["reviewed_repository_SHA256"].keys()
    assert final_name not in final["reviewed_repository_SHA256"]
    assert final["reviewed_external_SHA256"]["deliver_view_preparation.py"] == sha(external/"deliver_view_preparation.py")
    for name,pin in final["reviewed_external_SHA256"].items():
        path = (external/name).resolve(); path.relative_to(external)
        assert sha(path) == pin
    for name,pin in final["reviewed_repository_SHA256"].items():
        assert entries[name]["sha256"] == pin
    assert entries[REL+"/author/deliver_view_preparation.py"]["sha256"] == sha(external/"deliver_view_preparation.py")
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
    delta_path = external/"preparation_delivery_delta_verify.json"
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
        protocol = preparation_checks(root,external,config,entries)
        manifest = dict(old,created_utc=datetime.now(timezone.utc).isoformat(),previous_delivery_commit=BASE,
            storage_stage="alpha_partial_saved_views_prepared_001",files=[entries[name] for name in sorted(paths)])
        raw = (json.dumps(manifest,ensure_ascii=False,indent=2,allow_nan=False)+"\n").encode("utf-8")
        (root/MANIFEST).write_bytes(raw)
        receipt = dict(status="incremental_preparation_delivery_pass",previous_delivery_commit=BASE,
            manifest_sha256=digest(raw),config_sha256=sha(root/CONFIG),ordinary_manifest_files=len(paths),
            ordinary_manifest_bytes=sum(row["bytes"] for row in entries.values()),delta_files=delta,
            delta_bytes=sum(row["bytes"] for row in delta),new_files=len(new),changed_old_files=2,
            unchanged_manifest_entries_exactly_inherited=len(old_entries)-2,protocol_sha256=config["protocol_sha256"],
            binding_count=len(protocol["bindings"]),front_history=config["front_history"],
            previous_publication_receipt=config["previous_publication_receipt"],prepared_card="M-AVIEW1",
            prepared=True,authorized=False,executed=False,new_full_source_scan=False,
            new_NPZ_decodes_or_HF_calls_or_plots=0,original_science_and_qualification_unchanged=True,whole_HF5_complete=False)
        write_new(delta_path,receipt)
    else:
        source = read(delta_path)
        assert source["status"] == "incremental_preparation_delivery_pass" and source["config_sha256"] == sha(root/CONFIG)
        assert source["prepared_card"] == "M-AVIEW1" and source["authorized"] is False and source["executed"] is False
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
        protocol = preparation_checks(restore,external,config,entries)
        assert source["protocol_sha256"] == config["protocol_sha256"] and source["front_history"] == config["front_history"]
        receipt = dict(status="published_and_incrementally_restored_pass",created_utc=datetime.now(timezone.utc).isoformat(),
            published_commit=commit,previous_delivery_commit=BASE,branch="main",origin=ORIGIN,
            remote_main_confirmed_equal=True,source_and_restore_clean=True,restore_root=str(restore),
            manifest_sha256=source["manifest_sha256"],ordinary_manifest_files=len(entries),
            ordinary_manifest_bytes=source["ordinary_manifest_bytes"],delta_files_restored_and_hashed=len(allowed),
            delta_bytes=source["delta_bytes"],unchanged_manifest_entries_inherited=len(unchanged),
            protocol_sha256=config["protocol_sha256"],binding_count=len(protocol["bindings"]),
            front_history=config["front_history"],previous_publication_receipt=config["previous_publication_receipt"],
            prepared_card="M-AVIEW1",prepared=True,authorized=False,executed=False,
            original_science_and_qualification_unchanged=True,new_full_source_or_restore_scan=False,
            new_NPZ_decodes_or_HF_calls_or_plots=0,whole_HF5_complete=False)
        write_new(external/"publication_receipt.json",receipt)
    print(json.dumps({key:value for key,value in receipt.items() if key not in ("delta_files","front_history")},ensure_ascii=False))


if __name__ == "__main__":
    main()
