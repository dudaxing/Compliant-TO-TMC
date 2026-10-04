"""Storage-only C2 summary revision; science and plots reuse the frozen helper.

Manifest entries are calculated before its file is opened. The amendment mode
records the original manifest defect without changing any original bytes.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

import summarize_contact_c2 as original


def write_output_manifest(out: Path) -> dict[str, str]:
    destination = out / "output_sha256.json"
    if destination.exists():
        raise FileExistsError("refusing to overwrite output manifest")
    # Complete both enumeration and hashing BEFORE creating the destination.
    entries = {p.name: original.digest(p) for p in sorted(out.iterdir()) if p.is_file()}
    assert destination.name not in entries
    with destination.open("x", encoding="utf-8") as stream:
        json.dump(entries, stream, indent=2)
        stream.write("\n")
    verify_output_manifest(out)
    return entries


def verify_output_manifest(out: Path) -> None:
    manifest = out / "output_sha256.json"
    entries = json.loads(manifest.read_text(encoding="utf-8"))
    if manifest.name in entries:
        raise ValueError("manifest must not contain itself")
    actual_names = {p.name for p in out.iterdir() if p.is_file() and p != manifest}
    if set(entries) != actual_names:
        raise ValueError("manifest inventory mismatch")
    for name, expected in entries.items():
        if original.digest(out / name) != expected:
            raise ValueError("output hash mismatch: " + name)


def amend_existing(root: Path, old: Path, out: Path) -> dict:
    root, old, out = root.resolve(), old.resolve(), out.resolve()
    if out.exists():
        raise FileExistsError("refusing to overwrite amendment directory")
    manifest = old / "output_sha256.json"
    entries = json.loads(manifest.read_text(encoding="utf-8"))
    empty_sha = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    if entries.get(manifest.name) != empty_sha:
        raise ValueError("not the documented empty-file self-entry defect")
    files = sorted(p for p in old.iterdir() if p.is_file())
    if set(entries) != {p.name for p in files}:
        raise ValueError("old manifest inventory mismatch")
    checked = []
    for path in files:
        if path != manifest:
            if original.digest(path) != entries[path.name]:
                raise ValueError("old scientific output hash mismatch: " + path.name)
            checked.append(path.name)
    sources = [Path(original.__file__).resolve(), Path(__file__).resolve(),
               root / "hf_repo/tests/test_summarize_contact_c2_r2.py"]
    bindings = {p.relative_to(root).as_posix(): original.digest(p) for p in files + sources}
    report = dict(
        schema="contact_c2_summary_manifest_amendment_v1",
        created_utc=datetime.now(timezone.utc).isoformat(), status="pass",
        scope="Storage manifest only: no scientific values, old source, or old output bytes changed; no FE and no scientific summary rerun.",
        original_manifest=manifest.relative_to(root).as_posix(),
        original_self_entry=entries[manifest.name], actual_original_manifest_sha256=original.digest(manifest),
        defect="The original main opened output_sha256.json with mode x before enumerating and hashing the directory. The new, empty file was therefore included with the SHA256 of empty bytes. That self entry is invalid; it is preserved as historical evidence.",
        correction="This supplementary binding hashes the actual original manifest and every original summary output. Future r2 manifests enumerate and hash all output files before opening their own destination.",
        verified_original_nonself_entries=checked,
        input_and_original_output_sha256=bindings,
        excluded_from_supplementary_input_map=["this amendment.json", "this amendment directory's output_sha256.json"],
    )
    out.mkdir(parents=True)
    with (out / "amendment.json").open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write("\n")
    # Detect source/output changes during this storage-only operation.
    for rel, expected in bindings.items():
        if original.digest(root / rel) != expected:
            raise ValueError("bound file changed during amendment: " + rel)
    write_output_manifest(out)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--protocol", type=Path)
    mode.add_argument("--amend-existing-manifest", type=Path)
    args = parser.parse_args(argv)
    out = args.output.resolve()
    if args.amend_existing_manifest:
        report = amend_existing(args.root, args.amend_existing_manifest, out)
        print(json.dumps(dict(status=report["status"], operation="manifest amendment only", output=str(out))))
        return 0
    if out.exists():
        raise FileExistsError("refusing to overwrite summary directory")
    payload, reader = original.make_summary(args.root, args.protocol)
    reader.bind(Path(__file__))  # make_summary already binds the frozen helper.
    payload["input_and_helper_sha256"] = reader.bindings
    out.mkdir(parents=True)
    with (out / "summary.json").open("x", encoding="utf-8") as stream:
        json.dump(original.plain(payload), stream, indent=2, allow_nan=False)
        stream.write("\n")
    original.plots(payload, out)
    for name, expected in reader.bindings.items():
        if original.digest(reader.root / name) != expected:
            raise ValueError("input changed during summary: " + name)
    write_output_manifest(out)
    print(json.dumps(dict(status=payload["status"], counts=payload["counts"], output=str(out))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
