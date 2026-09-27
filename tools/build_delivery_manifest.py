"""Build the current delivery manifest from the Git index's tracked paths only.

Stage every intended new delivery file before running this tool. The bytes hashed
are the current ordinary worktree files, not the staged blobs. Untracked files,
including locally restored evidence, never enter the manifest. This is a file
identity record; it neither runs mechanics nor grants scientific admission.

Example: python tools/build_delivery_manifest.py --worktree .
The generated handoff/repository_manifest.json must be staged after generation.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import tempfile

MANIFEST = "handoff/repository_manifest.json"
SCIENCE_BASELINE = "b1334bb6a83ba9a0efab7bdba7bd39722146f024"
PREVIOUS_DELIVERY = "2def941ddc94823ea0686bbd63ddbafa20f4b101"
STORAGE_STAGE = "main-consolidation-20260927"


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root)


def decode_names(data):
    if data and not data.endswith(b"\0"):
        raise ValueError("Git did not return a NUL-terminated path list")
    return [part.decode("utf-8") for part in data.split(b"\0") if part]


def confined_regular_path(root, name, *, missing_ok=False):
    relative = PurePosixPath(name)
    if (not isinstance(name, str) or not name or relative.is_absolute()
            or relative.as_posix() != name or ".." in relative.parts
            or "\\" in name or ":" in name):
        raise ValueError(f"Unsafe repository path: {name!r}")
    path = root.joinpath(*relative.parts)
    if not path.resolve().is_relative_to(root):
        raise ValueError(f"Path escapes repository: {name}")
    for parent in path.parents:
        if parent == root:
            break
        if parent.is_symlink():
            raise ValueError(f"Symbolic-link parent is not an ordinary delivery path: {name}")
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError:
        if missing_ok:
            return path
        raise ValueError(f"Tracked file is missing: {name}") from None
    if not stat.S_ISREG(mode):
        raise ValueError(f"Not an ordinary file: {name}")
    return path


def index_snapshot(root):
    # --cached alone defines membership; --stage is used only to reject conflicts
    # and non-regular Git modes, never to add paths to that membership.
    cached = git(root, "ls-files", "--cached", "-z")
    staged = git(root, "ls-files", "--cached", "--stage", "-z")
    names = decode_names(cached)
    stage_names = []
    for entry in decode_names(staged):
        metadata, name = entry.split("\t", 1)
        mode, _object_id, stage = metadata.split()
        if stage != "0":
            raise ValueError(f"Unresolved index conflict: {name}")
        if mode not in ("100644", "100755"):
            raise ValueError(f"Non-regular Git index entry ({mode}): {name}")
        stage_names.append(name)
    if len(names) != len(set(names)):
        raise ValueError("Duplicate tracked paths in Git index")
    if sorted(names) != sorted(stage_names):
        raise ValueError("Git index changed while reading tracked paths")
    return cached, staged, names


def file_record(root, name):
    path = confined_regular_path(root, name)
    before = path.stat()
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    after = path.stat()
    if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
        raise ValueError(f"File changed while hashing: {name}")
    return {"path": name, "bytes": after.st_size, "sha256": digest}


def build_manifest(root, *, previous_delivery_commit=PREVIOUS_DELIVERY, storage_stage=STORAGE_STAGE):
    """Return the manifest and an exclusion report without writing any file."""
    root = Path(root).resolve()
    if Path(git(root, "rev-parse", "--show-toplevel").decode("utf-8").strip()).resolve() != root:
        raise ValueError("--worktree must name the Git repository root")
    if not re.fullmatch(r"[0-9a-f]{40}", previous_delivery_commit):
        raise ValueError("previous_delivery_commit must be a full lowercase commit ID")
    if not isinstance(storage_stage, str) or not storage_stage.strip():
        raise ValueError("storage_stage must be a nonempty string")
    cached, staged, names = index_snapshot(root)
    files = [file_record(root, name) for name in sorted(names) if name != MANIFEST]
    # Validate the excluded output too, so it cannot redirect the final write.
    confined_regular_path(root, MANIFEST, missing_ok=True)
    if index_snapshot(root)[:2] != (cached, staged):
        raise ValueError("Git index changed while building the manifest")
    untracked = sorted(decode_names(git(root, "ls-files", "--others", "--exclude-standard", "-z")))
    record = {
        "schema_version": "github-handoff-repository-1.0",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "science_version": "0.5.0",
        "science_baseline_commit": SCIENCE_BASELINE,
        "storage_stage": storage_stage,
        "previous_delivery_commit": previous_delivery_commit,
        "scope": ("Current ordinary worktree bytes for Git-index tracked paths only, excluding this manifest. "
                  "New delivery files must be staged before generation. External evidence is restored through "
                  "evidence_assets.json when required. Per-file SHA-256 is file identity, not scientific admission."),
        "files": files,
    }
    report = {
        "manifest_files": len(files),
        "tracked_file_count": len(names),
        "manifest_already_tracked": MANIFEST in names,
        "excluded_nonignored_untracked_files": untracked,
        "ignored_files": "not enumerated and never included",
        "mechanics_run": False,
        "high_precision_run": False,
    }
    return record, report


def write_manifest(root, record):
    root = Path(root).resolve()
    destination = confined_regular_path(root, MANIFEST, missing_ok=True)
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Write beside the destination then atomically replace only this delivery
    # manifest. Historical manifests and scientific records are never touched.
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n",
                                     prefix="repository_manifest.", suffix=".tmp",
                                     dir=destination.parent, delete=False) as stream:
        json.dump(record, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
        temporary = Path(stream.name)
    confined_regular_path(root, MANIFEST, missing_ok=True)
    os.replace(temporary, destination)
    return file_record(root, MANIFEST)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worktree", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--previous-delivery-commit", default=PREVIOUS_DELIVERY)
    parser.add_argument("--storage-stage", default=STORAGE_STAGE)
    args = parser.parse_args()
    record, report = build_manifest(args.worktree, previous_delivery_commit=args.previous_delivery_commit,
                                    storage_stage=args.storage_stage)
    report["manifest"] = write_manifest(args.worktree, record)
    report["next_step"] = "Stage handoff/repository_manifest.json, then run tools/handoff.py verify."
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
