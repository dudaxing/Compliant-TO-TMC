"""Copy a prepared C2 payload, independently audit two cases, compare all evidence.

Run only after the final freeze/prepare readiness instruction. This creates an
exclusive temporary tree; it never audits or modifies the source/publication
trees, never calls production FE, and never stages, commits or pushes Git.
"""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import prepare_c2_sync as sync


def require(condition, message):
    sync.require(condition, message)


def payload_records(root, manifest):
    return [sync.record(sync.safe(root, row["path"]), row["path"]) for row in manifest["files"]]


def evidence_inventory(root):
    return {p.relative_to(root).as_posix(): sync.sha(p)
            for p in sorted(root.rglob("*")) if p.is_file()
            and not any(part in sync.SKIP_DIRS for part in p.relative_to(root).parts)
            and p.suffix not in sync.SKIP_SUFFIXES}


def require_bindings(run, summary, copy_root):
    for field in ("input_and_helper_sha256", "detail_output_sha256"):
        entries = summary[field]
        require(isinstance(entries, dict) and entries, "Empty audit binding map: " + field)
        for relative, digest in entries.items():
            require(isinstance(relative, str) and "\\" not in relative and ":" not in relative
                    and not Path(relative).is_absolute(), "Nonportable audit binding")
            path = (run/relative).resolve()
            limit = run if field == "detail_output_sha256" else copy_root
            require(path.is_relative_to(limit), "Relocated audit binding escapes copy: " + relative)
            require(sync.sha(path) == digest, "Relocated audit binding changed: " + relative)


def compare_summaries(original, new, run):
    """Permit only displayed root/time and explicit detail-directory relocation."""
    require(len(original["states"]) == len(new["states"]), "Audited state count changed")
    original_normalized, new_normalized = deepcopy(original), deepcopy(new)
    for summary in (original_normalized, new_normalized):
        summary.pop("created_utc", None)
        summary.pop("run", None)
    details = []
    for old, current, old_norm, new_norm in zip(original["states"], new["states"],
            original_normalized["states"], new_normalized["states"]):
        require(old["state_id"] == current["state_id"], "Audited state identity changed")
        old_path = sync.safe(run, old["detail_file"])
        new_path = sync.safe(run, current["detail_file"])
        require(sync.sha(old_path) == old["detail_sha256"], "Copied original detail hash changed")
        require(sync.sha(new_path) == current["detail_sha256"], "New detail hash differs from summary")
        require(sync.read(old_path) == sync.read(new_path), "Scientific state detail differs: " + old["state_id"])
        require(old["detail_sha256"] == current["detail_sha256"], "Exact serialized detail bytes differ")
        old_norm["detail_file"] = new_norm["detail_file"] = old["state_id"]
        details.append(dict(state_id=old["state_id"], sha256=current["detail_sha256"],
                            original=old["detail_file"], recomputed=current["detail_file"]))
    for summary in (original_normalized, new_normalized):
        require(summary["detail_output_sha256"] == {
            row["detail_file"]: row["detail_sha256"] for row in
            (original["states"] if summary is original_normalized else new["states"])},
            "Detail output map differs from state inventory")
        summary["detail_output_sha256"] = {row["state_id"]: row["detail_sha256"] for row in summary["states"]}
    require(original_normalized == new_normalized, "Scientific audit summary differs after narrow normalization")
    return details


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--prepared-receipt", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    args = parser.parse_args()
    plan, prepared = sync.read(args.plan), sync.read(args.prepared_receipt)
    require(plan["schema"] == "c2-publication-freeze-1.0", "Not a frozen C2 plan")
    require(prepared["schema"] == "c2-publication-prepared-1.0"
            and prepared["frozen_plan_sha256"] == sync.sha(args.plan), "Prepared receipt is not bound to plan")
    require(plan["baseline_commit"] == sync.BASE, "Publication baseline differs")
    copy_parent = args.output_root.resolve()
    require(copy_parent.is_relative_to(sync.ROOT/".github_handoff") and not copy_parent.exists(),
            "Require a new temporary directory under .github_handoff")
    manifest_path = sync.DEST/sync.MANIFEST
    manifest = sync.read(manifest_path)
    before_publication = payload_records(sync.DEST, manifest)
    require(before_publication == manifest["files"], "Prepared payload differs from its manifest")
    before_manifest_sha = sync.sha(manifest_path)
    before_source_evidence = evidence_inventory(sync.ROOT/"hf4_c2_diagnostics")
    before_publication_evidence = evidence_inventory(sync.DEST/"hf4_c2_diagnostics")
    before_sources = {row["path"]: sync.record(Path(row["source"]), row["path"]) for row in plan["files"]}
    require(all(before_sources[row["path"]] == {k:row[k] for k in ("path", "bytes", "sha256")}
                for row in plan["files"]), "Frozen source changed before portable read-back")
    copy_parent.mkdir()
    copied = copy_parent/"publication"
    copied.mkdir()
    for row in manifest["files"]:
        dest = sync.safe(copied, row["path"])
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(sync.safe(sync.DEST, row["path"]), dest)
    (copied/sync.MANIFEST).parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(manifest_path, copied/sync.MANIFEST)
    require(payload_records(copied, manifest) == before_publication, "Temporary copy differs bytewise")
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8",
               OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    results, error_text = [], None
    try:
        for case, expected in (("padding_2p5", "pass"), ("mesh_h00625", "not_pass")):
            run = copied/"hf4_c2_diagnostics/experiments"/case
            output = copied/"review_runs"/(case+"_portability_audit.json")
            command = [sys.executable, "-B", str(copied/"hf_repo/scripts/audit_contact_c2.py"),
                       "--run", str(run), "--output", str(output),
                       "--protocol", str(copied/"hf_repo/configs/contact_c2_v3.json")]
            log = copy_parent/(case+".audit.log")
            print("Independent relocated audit: "+case+"; expected="+expected, flush=True)
            start = time.monotonic()
            with log.open("x", encoding="utf-8") as stream:
                process = subprocess.run(command, cwd=copy_parent, env=env, stdout=stream,
                                         stderr=subprocess.STDOUT, timeout=1200)
            recomputed, original = sync.read(output), sync.read(run/"audit.json")
            require(process.returncode == (0 if expected == "pass" else 1), "Unexpected independent audit exit code")
            require(original["status"] == recomputed["status"] == expected, "Relocated audit status differs")
            require_bindings(run, original, copied)
            require_bindings(run, recomputed, copied)
            details = compare_summaries(original, recomputed, run)
            result = dict(case=case, expected_status=expected, status=recomputed["status"],
                          returncode=process.returncode, elapsed_seconds=time.monotonic()-start,
                          summary=recomputed["summary"], audit_sha256=sync.sha(output),
                          log_sha256=sync.sha(log), details=details,
                          input_binding_count=len(recomputed["input_and_helper_sha256"]),
                          exact_scientific_summary_and_detail_match=True)
            results.append(result)
            sync.write_new(copy_parent/(case+".receipt.json"), result)
            print(json.dumps({k:result[k] for k in ("case", "status", "returncode", "elapsed_seconds")}), flush=True)
    except Exception as error:
        error_text = type(error).__name__+": "+str(error)
    unchanged = (payload_records(sync.DEST, manifest) == before_publication
                 and sync.sha(manifest_path) == before_manifest_sha
                 and evidence_inventory(sync.ROOT/"hf4_c2_diagnostics") == before_source_evidence
                 and evidence_inventory(sync.DEST/"hf4_c2_diagnostics") == before_publication_evidence
                 and all(sync.record(Path(row["source"]), row["path"]) == before_sources[row["path"]]
                         for row in plan["files"]))
    receipt = dict(schema="c2-relocated-independent-audit-1.0", status="pass" if error_text is None and unchanged else "not_pass",
                   created_utc=datetime.now(timezone.utc).isoformat(), cases=results, error=error_text,
                   source_and_publication_unchanged=unchanged, frozen_plan_sha256=sync.sha(args.plan),
                   prepared_receipt_sha256=sync.sha(args.prepared_receipt), copied_payload_files=len(manifest["files"]),
                   foreign_cwd=str(copy_parent), copied_tree=str(copied), production_FE_executed=False,
                   scope="Same host, different directory; independent saved-state read-back, not cross-platform validation",
                   expected_mechanical_status="partial; mesh original NOT_PASS must remain unchanged")
    sync.write_new(copy_parent/"receipt.json", receipt)
    print(json.dumps({k:receipt[k] for k in ("status", "error", "source_and_publication_unchanged")}), flush=True)
    return 0 if receipt["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
