"""Package the HF4 partial stage, then verify every archived payload hash.

Run only after the independent HF repository has been committed. Historical
large evidence archives and LF source data deliberately remain separate.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
from datetime import datetime, timezone
import zipfile


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / "hf_repo"
ARCHIVE = ROOT / "deliverables/HF4_AB_partial_evaluator_and_evidence.zip"
CONTENT = ROOT / "HF4_CONTENT_MANIFEST.json"
RELEASE = ROOT / "deliverables/HF4_AB_release_manifest.json"
WHEEL = REPO / "dist/independent_hf_evaluator-0.4.0-py3-none-any.whl"
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", "build", "results"}


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def allowed(path: Path, base: Path) -> bool:
    parts = path.relative_to(base).parts
    return not any(p in SKIP_DIRS or p.startswith(".venv") or p.endswith(".egg-info")
                   for p in parts) and path.suffix not in {".pyc", ".pyo"}


def main() -> None:
    if ARCHIVE.exists() or CONTENT.exists() or RELEASE.exists():
        raise SystemExit("Refusing to overwrite an existing release.")
    status = subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO, text=True)
    if status.strip():
        raise SystemExit("Commit the independent repository before packaging.")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    freeze_path = ROOT / "hf4_results/production_source_freeze.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    for relative, expected in freeze["files"].items():
        if sha(REPO / relative) != expected:
            raise SystemExit(f"Production source changed: {relative}")
    with zipfile.ZipFile(WHEEL) as wheel:
        for relative, expected in freeze["files"].items():
            if hashlib.sha256(wheel.read(relative.removeprefix("src/"))).hexdigest() != expected:
                raise SystemExit(f"Wheel source mismatch: {relative}")
    summary = json.loads((ROOT / "hf4_results/acceptance_summary.json").read_text(encoding="utf-8"))
    if summary["status"] != "partial" or summary["stage_B"] != "3_of_4_paths_passed":
        raise SystemExit("Unexpected stage status.")

    members = [ROOT / "README.md", ROOT / "HF4_EVIDENCE_README.md", WHEEL]
    for base in [REPO, ROOT / "hf4_results", ROOT / "docs"]:
        for path in base.rglob("*"):
            if not path.is_file() or not allowed(path, base):
                continue
            if base == REPO and "dist" in path.relative_to(base).parts:
                continue
            if base == ROOT / "docs" and path.suffix != ".md":
                continue
            if path.is_symlink():
                raise SystemExit(f"Unexpected symlink: {path}")
            members.append(path)
    members = sorted(set(members), key=lambda p: p.relative_to(ROOT).as_posix())
    entries = [{"path": p.relative_to(ROOT).as_posix(), "bytes": p.stat().st_size, "sha256": sha(p)}
               for p in members]
    manifest = {
        "schema_version": "hf4-content-manifest-1.0",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "version": "0.4.0", "git_commit": commit, "status": "partial",
        "stage_A": summary["stage_A"], "stage_B": summary["stage_B"],
        "production_freeze_sha256": sha(freeze_path),
        "spec_sha256": sha(REPO / "configs/hf4/validation_spec.json"),
        "wheel_sha256": sha(WHEEL),
        "manifest_scope": "Every payload member; this manifest excludes itself to avoid self-reference.",
        "historical_large_evidence": "Not included; historical documents retain links to separate prior releases.",
        "files": entries,
    }
    write_json(CONTENT, manifest)
    with zipfile.ZipFile(ARCHIVE, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in members + [CONTENT]:
            archive.write(path, path.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(ARCHIVE) as archive:
        expected_names = {e["path"] for e in entries} | {CONTENT.name}
        if len(archive.namelist()) != len(expected_names) or set(archive.namelist()) != expected_names:
            raise SystemExit("Archive inventory mismatch or duplicate member.")
        if archive.testzip() is not None:
            raise SystemExit("Archive CRC verification failed.")
        for entry in entries:
            with archive.open(entry["path"]) as stream:
                if hashlib.file_digest(stream, "sha256").hexdigest() != entry["sha256"]:
                    raise SystemExit(f"Archive payload mismatch: {entry['path']}")
        if archive.read(CONTENT.name) != CONTENT.read_bytes():
            raise SystemExit("Archived content manifest differs.")
    write_json(RELEASE, {
        "schema_version": "hf4-release-manifest-1.0", "version": "0.4.0",
        "git_commit": commit, "status": "partial", "stage_A": summary["stage_A"],
        "stage_B": summary["stage_B"], "stage_C": "not_started", "stage_D": "not_started",
        "zip_path": ARCHIVE.relative_to(ROOT).as_posix(), "zip_sha256": sha(ARCHIVE),
        "zip_bytes": ARCHIVE.stat().st_size, "entries": len(entries) + 1,
        "content_manifest_sha256": sha(CONTENT), "wheel_sha256": sha(WHEEL),
        "all_member_hashes_verified": True, "wheel_matches_frozen_production_sources": True,
        "accepted_HP_states": summary["total_hp_checked_states"],
        "test_unique_passed": summary["tests"]["unique_pass"],
        "test_unique_skipped": summary["tests"]["unique_skip"],
        "test_count_method": summary["tests"]["method"],
        "isolated_checks": summary["isolated_checks"],
        "no_tolerance_or_physical_parameter_change": True,
    })
    print(RELEASE.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
