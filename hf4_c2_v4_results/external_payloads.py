"""Keep the large lossless payloads of a v4 run outside Git in a hash-verified archive, and restore them byte-exactly.

The frozen v4 protocol (`storage`) lets per-state NPZ, per-state controller records, the full controller gzip and the
per-state audit details live outside Git in a hash-verified archive with a manifest (relative path, bytes, SHA-256,
archive location, restore method), after one original-byte restore check into an empty directory. The members are
exactly the files whose SHA-256 the committed run records bind (steps/index.json, the stage result.json, audit.json);
each must match its binding. Every other file of the run stays in Git and must be small.

build:   python hf4_c2_v4_results/external_payloads.py build --run <run directory> --archive <new zip outside the repository>
             --manifest <new json in the repository>      (also writes manifest.json next to the archive)
restore: python hf4_c2_v4_results/external_payloads.py restore --manifest <json> --archive <zip> --into <directory>
             [--empty-target] [--compare-with <directory>] [--receipt <new json>]
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "hf-local-evidence-archive-v2"
RESTORE_SCHEMA = "hf-local-evidence-restore-check-1"
KEEP_IN_GIT_LIMIT = 1 << 20
FIXED_TIME = (1980, 1, 1, 0, 0, 0)
CHUNK = 1 << 20


class PayloadError(Exception):
    pass


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(CHUNK), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_new_json(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(record, stream, indent=2, ensure_ascii=False)
        stream.write("\n")


def bindings(run):
    """Run-relative payload path -> (bound SHA-256, run-relative record that binds it)."""
    bound = {}
    for stage in load_json(run / "stages/index.json")["stages"]:
        directory = stage["directory"]
        result = load_json(run / directory / "result.json")
        bound[f"{directory}/controller_full.json.gz"] = (result["controller_full_sha256"], f"{directory}/result.json")
        for step in load_json(run / directory / "steps/index.json")["steps"]:
            bound[f"{directory}/steps/{step['file']}"] = (step["sha256"], f"{directory}/steps/index.json")
            bound[f"{directory}/steps/{step['record_file']}"] = (step["record_sha256"], f"{directory}/steps/index.json")
    for state in load_json(run / "audit.json")["states"]:
        bound[state["detail_file"]] = (state["detail_sha256"], "audit.json")
    return bound


def checked_member_path(name):
    path = PurePosixPath(name)
    if not name or "\\" in name or path.is_absolute() or any(part in ("", ".", "..") for part in name.split("/")) or ":" in name:
        raise PayloadError(f"unsafe member path: {name!r}")
    return path


def build(run, archive, manifest, root=ROOT):
    run, archive, manifest = run.resolve(), archive.resolve(), manifest.resolve()
    if not run.is_relative_to(root) or not (run / "audit.json").is_file():
        raise PayloadError("the run directory must be an audited run inside the repository")
    if archive.is_relative_to(root):
        raise PayloadError("the archive must be outside the repository")
    external_manifest = archive.parent / "manifest.json"
    for path in (archive, manifest, external_manifest):
        if path.exists():
            raise PayloadError(f"{path.name} already exists; outputs are write-once")
    prefix = run.relative_to(root).as_posix()
    bound = bindings(run)
    members = []
    for relative, (expected, bound_by) in sorted(bound.items()):
        path = run / relative
        if not path.is_file():
            raise PayloadError(f"bound payload missing: {relative}")
        actual = sha256_file(path)
        if actual != expected:
            raise PayloadError(f"{relative} does not match the SHA-256 bound in {bound_by}")
        checked_member_path(f"{prefix}/{relative}")
        members.append(dict(path=f"{prefix}/{relative}", bytes=path.stat().st_size, sha256=actual, bound_by=f"{prefix}/{bound_by}"))
    kept = []
    for path in sorted(p for p in run.rglob("*") if p.is_file()):
        relative = path.relative_to(run).as_posix()
        if relative in bound:
            continue
        if path.stat().st_size > KEEP_IN_GIT_LIMIT:
            raise PayloadError(f"unbound file larger than {KEEP_IN_GIT_LIMIT} bytes would go into Git: {relative}")
        kept.append(dict(path=f"{prefix}/{relative}", bytes=path.stat().st_size, sha256=sha256_file(path)))
    archive.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive, "x") as bundle:
        for member in members:
            info = zipfile.ZipInfo(member["path"], date_time=FIXED_TIME)
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, (root / member["path"]).read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
    with zipfile.ZipFile(archive) as bundle:
        if bundle.namelist() != [m["path"] for m in members]:
            raise PayloadError("archive read-back: member list differs")
        for member in members:
            data = bundle.read(member["path"])
            if len(data) != member["bytes"] or sha256_bytes(data) != member["sha256"]:
                raise PayloadError(f"archive read-back: {member['path']} differs")
    receipts = {action: load_json(run.parent / f"{run.name}.{action}.receipt.json") for action in ("solve", "audit")}
    manifest_relative = manifest.relative_to(root).as_posix() if manifest.is_relative_to(root) else manifest.name
    classes = {}
    for member in members:
        name = PurePosixPath(member["path"]).name
        kind = ("full controller record (gzip JSON)" if name == "controller_full.json.gz" else
                "per-state controller record (gzip JSON)" if name.endswith(".record.json.gz") else
                "per-state arrays (NPZ)" if name.endswith(".npz") else "per-state audit details (JSON)")
        classes.setdefault(kind, dict(count=0, bytes=0))
        classes[kind]["count"] += 1
        classes[kind]["bytes"] += member["bytes"]
    record = dict(
        schema=SCHEMA, created_utc=datetime.now(timezone.utc).isoformat(),
        archive=archive.name, archive_bytes=archive.stat().st_size, archive_sha256=sha256_file(archive),
        location=("outside Git: the owner's local evidence folder Compliant-TO-TMC-evidence/" + archive.parent.name
                  + " (publishing it as a release asset is the owner's decision)"),
        run=prefix, protocol_sha256=receipts["solve"]["protocol_sha256"], audit_sha256=receipts["audit"]["audit_sha256"],
        rule=("frozen v4 protocol, storage: lightweight records stay in Git; the large lossless payloads whose SHA-256 the "
              "committed run records bind are kept in this archive"),
        member_classes=classes, member_count=len(members), member_bytes=sum(m["bytes"] for m in members), members=members,
        kept_in_git_count=len(kept), kept_in_git=kept,
        cross_check=("every member hashes to the SHA-256 bound in the committed record named in bound_by; after writing, "
                     "the archive was read back member by member"),
        restore=dict(
            command=(f"python hf4_c2_v4_results/external_payloads.py restore --manifest {manifest_relative} "
                     f"--archive <path to {archive.name}> --into <repository root>"),
            behaviour=("checks the archive SHA-256 and that its entries are exactly the listed members, extracts each member "
                       "to its repository-relative path, refuses unsafe paths and existing files with different bytes, and "
                       "verifies bytes and SHA-256 of every restored member"),
            manual="any unzip tool into the repository root (member paths are repository-relative), then compare with this manifest"))
    write_new_json(manifest, record)
    external_manifest.write_bytes(manifest.read_bytes())
    return record


def restore(manifest_path, archive, into, empty_target=False, compare_with=None):
    manifest = load_json(manifest_path)
    if manifest.get("schema") != SCHEMA:
        raise PayloadError("not an external-payload manifest")
    if archive.stat().st_size != manifest["archive_bytes"] or sha256_file(archive) != manifest["archive_sha256"]:
        raise PayloadError("the archive does not match the manifest")
    into = into.resolve()
    was_empty = not into.exists() or not any(into.iterdir())
    if empty_target and not was_empty:
        raise PayloadError("the restore-check target must be an empty or new directory")
    members = {m["path"]: m for m in manifest["members"]}
    for name in members:
        checked_member_path(name)
    restored, present = [], []
    with zipfile.ZipFile(archive) as bundle:
        names = bundle.namelist()
        if sorted(names) != sorted(members) or len(names) != len(set(names)):
            raise PayloadError("archive entries differ from the manifest members")
        for name in names:
            member = members[name]
            target = into.joinpath(*PurePosixPath(name).parts)
            if not target.resolve().is_relative_to(into):
                raise PayloadError(f"member escapes the target: {name}")
            data = bundle.read(name)
            if len(data) != member["bytes"] or sha256_bytes(data) != member["sha256"]:
                raise PayloadError(f"archived bytes of {name} differ from the manifest")
            if target.exists():
                if target.stat().st_size != member["bytes"] or sha256_file(target) != member["sha256"]:
                    raise PayloadError(f"refusing to overwrite a different existing file: {name}")
                present.append(name)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            partial = target.with_name(target.name + ".partial")
            with partial.open("xb") as stream:
                stream.write(data)
            os.replace(partial, target)
            restored.append(name)
    mismatches = [name for name, m in members.items()
                  if (into / name).stat().st_size != m["bytes"] or sha256_file(into / name) != m["sha256"]]
    against = None
    if compare_with is not None:
        compare_with = compare_with.resolve()
        against = [name for name in members if (into / name).read_bytes() != (compare_with / name).read_bytes()]
    return dict(target_was_empty=was_empty, members=len(members), restored=len(restored), already_present=len(present),
                member_mismatches=mismatches, byte_mismatches_against_originals=against)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    make = commands.add_parser("build")
    make.add_argument("--run", type=Path, required=True)
    make.add_argument("--archive", type=Path, required=True)
    make.add_argument("--manifest", type=Path, required=True)
    back = commands.add_parser("restore")
    back.add_argument("--manifest", type=Path, required=True)
    back.add_argument("--archive", type=Path, required=True)
    back.add_argument("--into", type=Path, required=True)
    back.add_argument("--empty-target", action="store_true")
    back.add_argument("--compare-with", type=Path)
    back.add_argument("--receipt", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "build":
            record = build(args.run, args.archive, args.manifest)
            print(json.dumps({k: record[k] for k in ("archive", "archive_bytes", "archive_sha256", "member_count", "member_bytes",
                                                    "kept_in_git_count", "member_classes")}, indent=1, ensure_ascii=False))
            return 0
        if args.receipt is not None and args.receipt.exists():
            raise PayloadError("the receipt must be a new file")
        outcome = restore(args.manifest, args.archive, args.into, args.empty_target, args.compare_with)
    except PayloadError as error:
        print(f"refused: {error}", file=sys.stderr)
        return 2
    passed = (not outcome["member_mismatches"] and outcome["restored"] + outcome["already_present"] == outcome["members"]
              and (outcome["byte_mismatches_against_originals"] in (None, [])) and (outcome["target_was_empty"] or not args.empty_target))
    if args.receipt is not None:
        manifest = args.manifest.resolve()
        write_new_json(args.receipt.resolve(), dict(
            schema=RESTORE_SCHEMA, created_utc=datetime.now(timezone.utc).isoformat(),
            manifest=manifest.relative_to(ROOT).as_posix() if manifest.is_relative_to(ROOT) else manifest.name,
            manifest_sha256=sha256_file(manifest), archive=args.archive.name, archive_sha256_verified=True,
            target=("an empty directory outside the repository" if args.empty_target else "an existing directory"),
            compared_with=("the working-tree originals in the repository" if args.compare_with is not None else None),
            **outcome, status="pass" if passed else "not_pass"))
    print(json.dumps(dict(outcome, status="pass" if passed else "not_pass"), indent=1))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
