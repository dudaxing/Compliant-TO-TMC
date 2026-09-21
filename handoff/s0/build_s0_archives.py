"""Build, duplicate, and independently restore immutable HF4-C2-S0 evidence.

Uses only the Python standard library. All output files/directories are new;
existing outputs are refused. No scientific code or baseline file is modified.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import sys
import zipfile

CHUNK = 1024 * 1024
EXPECTED_COMMIT = "552350cd3202432d483b4a5aa7697afbe08db12a"
EXPECTED_MANIFEST = "4a2e6836f160a32aa67fe9a9b6fb8a99dad72e796d71610436dd83a934d2c2d6"
RELEASE = "hf4-c2-s0-evidence-v1"
BASE_URL = "https://github.com/dudaxing/Compliant-TO-TMC/releases/download/" + RELEASE


def digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for data in iter(lambda: stream.read(CHUNK), b""):
            result.update(data)
    return result.hexdigest()


def safe(root: Path, rel: str) -> Path:
    posix = PurePosixPath(rel)
    if (not rel or "\\" in rel or ":" in rel or posix.is_absolute()
            or any(part in ("", ".", "..") for part in rel.split("/"))
            or rel != posix.as_posix()):
        raise ValueError(f"Unsafe member: {rel!r}")
    result = root.joinpath(*posix.parts)
    if not result.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Path escapes root: {rel!r}")
    return result


def record_matches(path: Path, record: dict) -> None:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Not a regular source file: {path}")
    if path.stat().st_size != record["bytes"] or digest(path) != record["sha256"]:
        raise ValueError(f"File identity mismatch: {path}")


def json_new(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def verify_archive(path: Path, records: list[dict], expected_archive: dict | None = None) -> dict:
    if expected_archive is not None:
        record_matches(path, expected_archive)
    expected = {row["path"]: row for row in records}
    verified = []
    with zipfile.ZipFile(path, "r") as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or set(names) != set(expected):
            raise ValueError(f"Archive member set mismatch: {path}")
        for info in archive.infolist():
            row = expected[info.filename]
            safe(path.parent, info.filename)
            if info.is_dir() or info.file_size != row["bytes"]:
                raise ValueError(f"Archive member metadata mismatch: {info.filename}")
            result = hashlib.sha256()
            size = 0
            with archive.open(info, "r") as stream:
                for block in iter(lambda: stream.read(CHUNK), b""):
                    size += len(block)
                    result.update(block)
            if size != row["bytes"] or result.hexdigest() != row["sha256"]:
                raise ValueError(f"Archive member byte mismatch: {info.filename}")
            verified.append(info.filename)
    return {"path": str(path), "bytes": path.stat().st_size,
            "sha256": digest(path), "verified_member_count": len(verified),
            "verified_uncompressed_bytes": sum(row["bytes"] for row in records),
            "exact_member_set": True, "all_member_size_sha256_match": True}


def build_archive(source: Path, destination: Path, rows: list[dict]) -> dict:
    with zipfile.ZipFile(destination, "x", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=6, allowZip64=True) as archive:
        for row in rows:
            path = safe(source, row["path"])
            record_matches(path, row)
            # Fixed ZIP metadata makes the artifact deterministic. Payload bytes
            # are copied verbatim, including JSON formatting and all NPZ arrays.
            info = zipfile.ZipInfo(row["path"], date_time=(2026, 9, 21, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            info._compresslevel = 6
            result = hashlib.sha256()
            count = 0
            with path.open("rb") as src, archive.open(info, "w", force_zip64=True) as dst:
                for block in iter(lambda: src.read(CHUNK), b""):
                    count += len(block)
                    result.update(block)
                    dst.write(block)
            if count != row["bytes"] or result.hexdigest() != row["sha256"]:
                raise ValueError(f"Source changed during archive creation: {path}")
    return verify_archive(destination, rows)


def restore_archive(archive_path: Path, destination: Path, rows: list[dict]) -> dict:
    with zipfile.ZipFile(archive_path, "r") as archive:
        for row in rows:
            target = safe(destination, row["path"])
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(row["path"], "r") as src, target.open("xb") as dst:
                shutil.copyfileobj(src, dst, CHUNK)
            record_matches(target, row)
    return {"restored_files": len(rows), "restored_bytes": sum(row["bytes"] for row in rows),
            "all_restored_size_sha256_match": True}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--inventory", required=True, type=Path)
    parser.add_argument("--copy-one", required=True, type=Path)
    parser.add_argument("--copy-two", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.source = args.source.resolve()
    args.inventory = args.inventory.resolve()
    args.copy_one = args.copy_one.resolve()
    args.copy_two = args.copy_two.resolve()
    args.output = args.output.resolve()
    restore = args.output / "restored_payload"
    for target in (args.copy_one, args.copy_two, args.output):
        if target == args.source or target.is_relative_to(args.source):
            raise ValueError("Output cannot be inside baseline source")
    if len({args.copy_one, args.copy_two, restore}) != 3:
        raise ValueError("Copies and restore root must be distinct")
    for target in (args.copy_one, args.copy_two, restore):
        if target.exists():
            raise FileExistsError(f"Refusing existing output directory: {target}")
    args.output.mkdir(parents=True, exist_ok=True)
    for pattern in ("group-*.json", "build_receipt.json", "s0_assets.json", "events.jsonl"):
        if list(args.output.glob(pattern)):
            raise FileExistsError(f"Refusing existing receipt in {args.output}: {pattern}")
    inventory = json.loads(args.inventory.read_text(encoding="utf-8-sig"))
    head = subprocess.check_output(["git", "-C", str(args.source), "rev-parse", "HEAD"], text=True).strip()
    status = subprocess.check_output(["git", "-C", str(args.source), "status", "--porcelain"], text=True)
    manifest_path = args.source / "handoff/repository_manifest.json"
    if (head != EXPECTED_COMMIT or inventory["baseline_commit"] != head or status
            or digest(manifest_path) != EXPECTED_MANIFEST
            or inventory["baseline_manifest_sha256"] != EXPECTED_MANIFEST):
        raise ValueError("Baseline commit, cleanliness, or manifest identity mismatch")
    original_records = json.loads(manifest_path.read_text(encoding="utf-8"))["files"]
    original = {row["path"]: row for row in original_records}
    if len(original) != len(original_records):
        raise ValueError("Duplicate baseline manifest record")
    groups = inventory["groups"]
    expected_groups = {"c1_runs", "c2_runs", "c2_readback_details", "historical_repair_details", "historical_hf4_details", "c0_runs"}
    if set(groups) != expected_groups:
        raise ValueError("Unexpected group set")
    all_paths = []
    all_bytes = 0
    for group, bundle in groups.items():
        rows = bundle["files"]
        if len(rows) != bundle["file_count"] or sum(row["bytes"] for row in rows) != bundle["bytes"]:
            raise ValueError(f"Group accounting mismatch: {group}")
        for row in rows:
            safe(args.source, row["path"])
            if row != original.get(row["path"]):
                raise ValueError(f"Inventory record does not match baseline: {row['path']}")
            all_paths.append(row["path"])
            all_bytes += row["bytes"]
    if len(all_paths) != 1099 or len(set(all_paths)) != 1099 or all_bytes != 1115101240:
        raise ValueError("Aggregate inventory mismatch")
    for target in (args.copy_one, args.copy_two, restore):
        target.mkdir(parents=True, exist_ok=False)
    events = (args.output / "events.jsonl").open("x", encoding="utf-8", newline="\n")

    def event(kind: str, **data: object) -> None:
        value = {"utc": datetime.now(timezone.utc).isoformat(), "event": kind, **data}
        events.write(json.dumps(value, ensure_ascii=False) + "\n")
        events.flush()
        print(json.dumps(value, ensure_ascii=False), flush=True)

    event("baseline_verified", commit=head, inventory_sha256=digest(args.inventory), files=len(all_paths), bytes=all_bytes)
    receipts = []
    assets = []
    dependency_groups = {"c2_runs": ["c1_runs"], "c2_readback_details": ["c2_runs"]}
    for group, bundle in groups.items():
        rows = bundle["files"]
        name = f"hf4-c2-s0-{group}-v1.zip"
        event("group_start", group=group, files=len(rows), bytes=bundle["bytes"])
        first = args.copy_one / name
        first_receipt = build_archive(args.source, first, rows)
        event("first_copy_verified", group=group, **first_receipt)
        second = args.copy_two / name
        with first.open("rb") as src, second.open("xb") as dst:
            shutil.copyfileobj(src, dst, CHUNK)
        second_receipt = verify_archive(second, rows, first_receipt)
        event("second_copy_verified", group=group, **second_receipt)
        restore_receipt = restore_archive(second, restore, rows)
        event("independent_restore_verified", group=group, **restore_receipt)
        group_receipt = {"group": group, "status": "pass", "first_copy": first_receipt,
                         "second_copy": second_receipt, "restored_root": str(restore),
                         "restore": restore_receipt, "files": rows}
        json_new(args.output / f"group-{group}.json", group_receipt)
        receipts.append(group_receipt)
        assets.append({"name": name, "url": f"{BASE_URL}/{name}",
                       "bytes": first_receipt["bytes"], "sha256": first_receipt["sha256"],
                       "mode": "restore_relative_files", "release_tag": RELEASE,
                       "group": group, "requires": [f"hf4-c2-s0-{dep}-v1.zip" for dep in dependency_groups.get(group, [])],
                       "files": rows})
    restored_paths = sorted(path.relative_to(restore).as_posix() for path in restore.rglob("*") if path.is_file())
    if restored_paths != sorted(all_paths):
        raise ValueError("Restored tree member set mismatch")
    for bundle in groups.values():
        for row in bundle["files"]:
            record_matches(safe(args.source, row["path"]), row)
            record_matches(safe(restore, row["path"]), row)
    final_head = subprocess.check_output(["git", "-C", str(args.source), "rev-parse", "HEAD"], text=True).strip()
    final_status = subprocess.check_output(["git", "-C", str(args.source), "status", "--porcelain"], text=True)
    if final_head != head or final_status or digest(manifest_path) != EXPECTED_MANIFEST:
        raise ValueError("Baseline changed during build")
    json_new(args.output / "s0_assets.json", assets)
    receipt = {"schema": "hf4-c2-s0-archive-build-1.0", "status": "pass",
               "created_utc": datetime.now(timezone.utc).isoformat(),
               "command_argv": sys.argv, "python_version": sys.version,
               "script_sha256": digest(Path(__file__)), "source_root": str(args.source),
               "baseline_commit": head, "baseline_manifest_sha256": EXPECTED_MANIFEST,
               "candidate_inventory_path": str(args.inventory), "candidate_inventory_sha256": digest(args.inventory),
               "file_count": len(all_paths), "original_bytes": all_bytes,
               "archive_bytes_per_copy": sum(asset["bytes"] for asset in assets),
               "first_copy_root": str(args.copy_one), "second_copy_root": str(args.copy_two),
               "restore_root": str(restore), "exact_restored_member_set": True,
               "source_original_bytes_reverified_at_end": True, "baseline_git_clean_at_end": True,
               "all_copies_member_hashes_verified": True,
               "execution": {"files_moved": False, "files_deleted": False, "science_source_changed": False,
                             "pytest_run": False, "new_FE": False, "new_HP": False, "git_commit": False, "upload": False},
               "groups": [{key: value for key, value in row.items() if key != "files"} for row in receipts],
               "asset_index_path": str(args.output / "s0_assets.json"),
               "asset_index_sha256": digest(args.output / "s0_assets.json")}
    json_new(args.output / "build_receipt.json", receipt)
    event("completed", status="pass", files=len(all_paths), original_bytes=all_bytes,
          archive_bytes_per_copy=receipt["archive_bytes_per_copy"], receipt=str(args.output / "build_receipt.json"))
    events.close()


if __name__ == "__main__":
    main()
