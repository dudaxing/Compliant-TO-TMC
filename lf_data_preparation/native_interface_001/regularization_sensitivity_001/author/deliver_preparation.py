"""Incremental M-ALPHA1 preparation publication; ordinary metadata/bytes only.

Config: protocol_sha256, binding_count, allowed_delta_paths (manifest excluded),
review_pins (passing JSON), record_pins, documentation_files. The config must be
copied unchanged to author/preparation_delivery_config.json before staging.
Existing file identities come from the prior verified manifest; only the new
stage and two front documents are rehashed. This script never commits/pushes.
"""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import argparse
import json
import subprocess

BASE = "5af8b5eb3d6780065075b8a331b774d8dad57d67"
REL = "lf_data_preparation/native_interface_001/regularization_sensitivity_001"
MANIFEST = "handoff/repository_manifest.json"
FRONTS = {"docs/CURRENT_STATUS.md", "docs/RESUME_DEVELOPMENT.md"}
PREVIOUS = REL + "/author/M_BOUND1_execution_publication_receipt.json"
CONFIG = REL + "/author/preparation_delivery_config.json"
ORIGIN = "https://github.com/dudaxing/Compliant-TO-TMC.git"
TARGETS = [0., .25, .5, .65, .75, .8, .85, .9, .95, 1., 1.05, 1.1, 1.15, 1.2, 1.15]


def read(path):
    return json.loads(path.read_bytes())


def git(root, *args):
    return subprocess.check_output(["git", "-c", "gc.auto=0", *args], cwd=root)


def names(data):
    return {n.decode("utf-8") for n in data.split(b"\0") if n}


def digest(data):
    return sha256(data).hexdigest()


def identity(root, name):
    path = (root/name).resolve()
    path.relative_to(root)
    return dict(path=name, bytes=path.stat().st_size, sha256=digest(path.read_bytes()))


def write_new(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def branch_origin(root):
    assert git(root, "branch", "--show-current").decode().strip() == "main"
    assert git(root, "remote", "get-url", "origin").decode().strip() == ORIGIN
    assert git(root, "remote", "get-url", "--push", "origin").decode().strip() == ORIGIN


def preparation_checks(root, config, entries, old_fronts):
    """Use manifest identities for old pins, actual delta identities for new pins."""
    protocol_path = REL + "/protocol.json"
    assert entries[protocol_path]["sha256"] == config["protocol_sha256"]
    p = read(root/protocol_path)
    assert p["schema_version"] == "same-task-alpha-prefix-card-1.0" and p["card"] == "M-ALPHA1"
    assert p["prepared"] is True and p["authorized"] is False and p["executed"] is False
    assert p["preparation_baseline_commit"] == BASE
    assert p["targets_mm"] == TARGETS and p["expected_original_targets"] == 15
    assert p["view_seconds"] == 600 and p["sampled_RSS_bytes"] == 8589934592
    assert p["phases"]["production"]["helper_seconds"] == 9600
    assert p["phases"]["production"]["outer_seconds"] == 9660
    assert len(p["bindings"]) == config["binding_count"]
    assert all(entries[n]["sha256"] == pin for n, pin in p["bindings"].items())
    stage = root/REL
    assert not (stage/"run_001").exists()
    forbidden = {"authorization.json", "direct_human_reply.json", "stop_requested.txt",
                 "production_launch.json", "production_stdout.log", "production_stderr.log"}
    assert not any(path.name in forbidden for path in stage.rglob("*"))
    assert {path.relative_to(root).as_posix() for path in stage.rglob("*") if path.is_file()} == {
        n for n in entries if n.startswith(REL + "/")}
    prep = read(stage/"author/preparation_receipt.json")
    assert prep["status"] == "ordinary_candidate_prepared_not_authorized_not_executed"
    assert prep["authorized"] is False and prep["executed"] is False
    assert prep["protocol_sha256"] == config["protocol_sha256"]
    assert prep["bindings_checked"] == config["binding_count"]
    assert prep["task_sha256"] == entries[REL + "/task.json"]["sha256"]
    assert prep["manifest_sha256"] == entries[REL + "/manifest.json"]["sha256"]
    actions = prep["actual_scientific_actions"]
    assert {"HF_imports", "NPZ_decodes", "models", "API", "force_tangent",
            "equilibrium", "HP", "new_renders"} <= actions.keys()
    assert all(v == 0 for v in actions.values())
    for name, pin in config["record_pins"].items():
        assert entries[name]["sha256"] == pin and (root/name).is_file(), name
    assert config["review_pins"]
    for name, pin in config["review_pins"].items():
        assert name.startswith(REL + "/author/") and entries[name]["sha256"] == pin
        assert read(root/name)["status"].startswith("pass"), name
    assert FRONTS | {REL + "/README.md"} <= set(config["documentation_files"])
    assert all((root/n).is_file() and n in entries for n in config["documentation_files"])
    doc_name = REL + "/author/documentation_receipt.json"
    doc = read(root/doc_name)
    assert config["record_pins"][doc_name] == entries[doc_name]["sha256"]
    assert doc["status"] == "pass_preparation_documentation_no_execution"
    assert doc["source_baseline_commit"] == BASE and doc["protocol_sha256"] == config["protocol_sha256"]
    assert doc["authorized"] is False and doc["executed"] is False
    assert doc["report_sha256"] == entries[REL + "/PREPARATION_RESULTS.md"]["sha256"]
    assert doc["README_sha256"] == entries[REL + "/README.md"]["sha256"]
    assert {"new_HF_imports", "new_NPZ_decodes", "new_models", "new_F_T",
            "new_solves", "new_HP", "new_renders"} <= doc["actions"].keys()
    assert all(v == 0 for v in doc["actions"].values())
    for name in ("input_scope_static_review.json", "physics_static_review.json"):
        path = REL + "/author/" + name
        assert doc["peer_reports"][name] == config["review_pins"][path] == entries[path]["sha256"]
    histories = []
    for name in sorted(FRONTS):
        prior, current = old_fronts[name], (root/name).read_bytes()
        assert current.count(prior) == 1, (name, "original bytes must occur intact once")
        offset = current.index(prior)
        histories.append(dict(path=name, old_bytes=len(prior), old_sha256=digest(prior),
            history_start_byte=offset, history_end_byte_exclusive=offset + len(prior),
            new_sha256=entries[name]["sha256"]))
    assert {r["path"] for r in doc["front_history"]} == FRONTS and len(doc["front_history"]) == 2
    declared = {r["path"]: r for r in doc["front_history"]}
    assert all(declared[r["path"]]["old_body_preserved_exactly"] is True
               and all(declared[r["path"]][k] == v for k, v in r.items()) for r in histories)
    return p, histories


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("finalize", "verify"))
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--restore", type=Path, default=Path("D:/hf-restore-20260930"))
    parser.add_argument("--external-base", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    root, restore, external = args.repo.resolve(), args.restore.resolve(), args.external_base.resolve()
    config_file = external/"preparation_delivery_config.json"
    config = read(config_file)
    assert (root/CONFIG).read_bytes() == config_file.read_bytes()
    previous = read(root/PREVIOUS)
    assert previous["status"] == "published_and_incrementally_restored_pass"
    assert previous["published_commit"] == BASE and previous["source_and_restore_clean"]
    assert previous["authorized"] is True and previous["executed"] is True and previous["execution_closed"]
    oldraw = git(root, "show", BASE + ":" + MANIFEST)
    assert digest(oldraw) == previous["manifest_sha256"]
    old = json.loads(oldraw)
    old_entries = {e["path"]: e for e in old["files"]}
    assert len(old_entries) == len(old["files"]) == previous["ordinary_manifest_files"] == 18621
    assert sum(e["bytes"] for e in old_entries.values()) == previous["ordinary_manifest_bytes"] == 9296256238
    assert old["science_version"] == "0.5.0"
    old_fronts = {n: git(root, "show", BASE + ":" + n) for n in FRONTS}
    delta_path = external/"preparation_delivery_delta_verify.json"
    allowed = set(config["allowed_delta_paths"])
    assert FRONTS <= allowed and MANIFEST not in allowed
    assert all(n in FRONTS or n.startswith(REL + "/") for n in allowed)

    if args.mode == "finalize":
        assert not delta_path.exists() and git(root, "rev-parse", "HEAD").decode().strip() == BASE
        branch_origin(root)
        assert (root/MANIFEST).read_bytes() == oldraw
        assert not git(root, "diff", "--name-only")
        assert not git(root, "ls-files", "--others", "--exclude-standard", "-z")
        paths = names(git(root, "ls-files", "-z")) - {MANIFEST}
        changed = names(git(root, "diff", "--cached", "--name-only", "-z", BASE))
        new = paths - old_entries.keys()
        assert not (old_entries.keys() - paths) and changed == allowed == FRONTS | new
        assert all(n.startswith(REL + "/") for n in new)
        delta = [identity(root, n) for n in sorted(allowed)]
        entries = dict(old_entries, **{e["path"]: e for e in delta})
        p, histories = preparation_checks(root, config, entries, old_fronts)
        manifest = dict(old, created_utc=datetime.now(timezone.utc).isoformat(),
            storage_stage="same_task_alpha_prefix_prepared_001", previous_delivery_commit=BASE,
            files=[entries[n] for n in sorted(paths)])
        raw = (json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
        (root/MANIFEST).write_bytes(raw)
        receipt = dict(status="incremental_preparation_delivery_pass", previous_delivery_commit=BASE,
            manifest_sha256=digest(raw), ordinary_manifest_files=len(paths),
            ordinary_manifest_bytes=sum(e["bytes"] for e in entries.values()), delta_files=delta,
            delta_bytes=sum(e["bytes"] for e in delta), new_files=len(new), changed_old_files=2,
            unchanged_manifest_entries_exactly_inherited=len(old_entries)-2,
            protocol_sha256=config["protocol_sha256"], binding_count=len(p["bindings"]),
            review_pins=config["review_pins"], config_sha256=digest(config_file.read_bytes()),
            front_history=histories, prepared=True, authorized=False, executed=False,
            new_full_source_scan=False, new_NPZ_decodes_or_HF_calls_or_plots=0,
            inherited_restoration_receipt=PREVIOUS, whole_HF5_complete=False)
        write_new(delta_path, receipt)
    else:
        source = read(delta_path)
        assert source["status"] == "incremental_preparation_delivery_pass"
        assert source["authorized"] is False and source["executed"] is False
        assert source["config_sha256"] == digest(config_file.read_bytes())
        commit = git(root, "rev-parse", "HEAD").decode().strip()
        assert commit != BASE and git(root, "rev-parse", "HEAD^").decode().strip() == BASE
        assert git(root, "ls-remote", "--heads", "origin", "main").decode().split() == [commit, "refs/heads/main"]
        for tree in (root, restore):
            branch_origin(tree)
            assert git(tree, "rev-parse", "HEAD").decode().strip() == commit
            assert not git(tree, "status", "--porcelain")
        assert (root/MANIFEST).read_bytes() == (restore/MANIFEST).read_bytes()
        assert digest((restore/MANIFEST).read_bytes()) == source["manifest_sha256"]
        assert (restore/CONFIG).read_bytes() == config_file.read_bytes()
        manifest = read(restore/MANIFEST)
        entries = {e["path"]: e for e in manifest["files"]}
        assert len(entries) == len(manifest["files"]) == source["ordinary_manifest_files"]
        assert sum(e["bytes"] for e in entries.values()) == source["ordinary_manifest_bytes"]
        for tree in (root, restore):
            assert names(git(tree, "ls-files", "-z")) == entries.keys() | {MANIFEST}
        assert names(git(root, "diff", "--name-only", "-z", BASE, commit)) == allowed | {MANIFEST}
        delta = source["delta_files"]
        assert {e["path"] for e in delta} == allowed
        assert all(identity(tree, e["path"]) == e == entries[e["path"]] for tree in (root, restore) for e in delta)
        unchanged = old_entries.keys() - allowed
        assert len(unchanged) == source["unchanged_manifest_entries_exactly_inherited"]
        assert all(entries[n] == old_entries[n] for n in unchanged)
        assert manifest["science_version"] == old["science_version"] == "0.5.0"
        assert manifest["science_baseline_commit"] == old["science_baseline_commit"]
        p, histories = preparation_checks(restore, config, entries, old_fronts)
        assert histories == source["front_history"]
        receipt = dict(status="published_and_incrementally_restored_pass", created_utc=datetime.now(timezone.utc).isoformat(),
            published_commit=commit, previous_delivery_commit=BASE, branch="main", origin=ORIGIN,
            remote_main_confirmed_equal=True, source_and_restore_clean=True, restore_root=str(restore),
            manifest_sha256=source["manifest_sha256"], ordinary_manifest_files=len(entries),
            ordinary_manifest_bytes=source["ordinary_manifest_bytes"], delta_files_restored_and_hashed=len(delta),
            delta_bytes=source["delta_bytes"], unchanged_manifest_entries_inherited=len(unchanged),
            protocol_sha256=config["protocol_sha256"], binding_count=len(p["bindings"]),
            peer_reviews=config["review_pins"], front_history=histories, prepared=True, authorized=False, executed=False,
            inherited_restoration_receipt=PREVIOUS, original_science_and_qualification_unchanged=True,
            new_full_source_or_restore_scan=False, new_NPZ_decodes_or_HF_calls_or_plots=0, whole_HF5_complete=False)
        write_new(external/"publication_receipt.json", receipt)
    print(json.dumps({k:v for k,v in receipt.items() if k not in ("delta_files", "front_history", "review_pins", "peer_reviews")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
