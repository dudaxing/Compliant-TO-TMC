"""Hash Git-index paths while preserving the scientific baseline header."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", required=True)
    parser.add_argument("--previous-delivery-commit", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    manifest = root / "handoff/repository_manifest.json"
    record = json.loads(manifest.read_text(encoding="utf-8"))
    paths = subprocess.check_output(
        ["git", "ls-files", "-z"], cwd=root
    ).decode("utf-8").split("\0")
    files = []
    for name in paths:
        if not name or name == "handoff/repository_manifest.json":
            continue
        path = root / name
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        files.append(dict(path=name, bytes=path.stat().st_size,
                          sha256=digest.hexdigest()))
    record.update(created_utc=datetime.now(timezone.utc).isoformat(),
                  storage_stage=args.stage,
                  previous_delivery_commit=args.previous_delivery_commit,
                  files=files)
    manifest.write_bytes((json.dumps(record, ensure_ascii=False, indent=2)
                          + "\n").encode("utf-8"))
    print(json.dumps(dict(status="manifest_built", files=len(files),
                         sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),
                         science_baseline_commit=record["science_baseline_commit"])))


if __name__ == "__main__":
    main()
