"""Strict public-payload numerical read-back with two explicit source exclusions.

This is a separate check from the preserved full-provenance relocation failure.
It never creates source placeholders, reads or redistributes the two external
MATLAB texts, changes frozen evidence, executes FE, or writes Git state.
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
from verify_c2_portability import compare_summaries, evidence_inventory, payload_records, require_bindings

EXTERNAL = {
    "hf0_audit/tmc/assembleKtFi.m.numbered.txt": "56e6759471a87b1d32e75c3e8a3ba8a0a439d5dc3a959d27eed3d7e3a4d5285c",
    "hf0_audit/tmc/initializeFEA.m.numbered.txt": "ca0ead10a18ff35373c82f0b967876a19976adf6fca3afa06d22129515209ef0",
}
READBACK = "hf_repo/scripts/audit_contact_c2_readback.py"
READBACK_TEST = "hf_repo/tests/test_contact_c2_readback.py"
NEW_FIELDS = {"numerical_status", "valid_for_execution_admission", "historical_source_status",
              "historical_sources", "historical_source_scope", "frozen_auditor_sha256", "physical_protocol_sha256"}


def require(condition, message):
    sync.require(condition, message)


def compare_numerical_readback(original, new, run, copied):
    """Allow only the declared scope metadata and exactly two omitted bindings."""
    require(set(new) == set(original) | NEW_FIELDS, "Unexpected numerical read-back summary fields")
    require(new["schema_version"] == "contact-c2-numerical-readback-1.0", "Wrong numerical schema")
    require(new["numerical_status"] == original["status"], "Original numerical status changed")
    require(new["status"] == "numerical_"+original["status"], "Misleading overall status")
    require(new["valid_for_execution_admission"] is False, "Read-back must not authorize FE")
    require(new["frozen_auditor_sha256"] == "50bcbe18d67d62ea1bce621c9bfd2c1c6247dbe2b095a965dab42c00bc47e543",
            "Frozen numerical evaluator identity changed")
    require(new["physical_protocol_sha256"] == "b17c8328dd1e350563b70305c0b311c8d38c9c0ef68c08b85fac5f13604d0b4d",
            "Frozen physical protocol identity changed")
    require(new["historical_source_status"] == "not_reverified_external_source",
            "Public copy cannot claim complete historical-source validation")
    require(isinstance(new["historical_source_scope"], (str, dict)) and bool(new["historical_source_scope"]),
            "Historical source purpose and chain must be explicit")
    rows = new["historical_sources"]
    require(isinstance(rows, list) and len(rows) == 2 and {row["path"] for row in rows} == set(EXTERNAL),
            "Historical exclusion inventory differs")
    for row in rows:
        require(row["expected_sha256"] == EXTERNAL[row["path"]]
                and row["status"] == "not_reverified_external_source" and row["actual_sha256"] is None,
                "Historical source declared hash/status differs")
        require(not sync.safe(copied, row["path"]).exists(), "External copyright source unexpectedly copied")

    # Verify every original binding except the two explicitly unprovided texts.
    adapted_original = deepcopy(original)
    old_bindings = adapted_original["input_and_helper_sha256"]
    missing = {}
    for relative, digest in list(old_bindings.items()):
        require(isinstance(relative, str) and "\\" not in relative and ":" not in relative
                and not Path(relative).is_absolute(), "Original binding is not portable")
        path = (run/relative).resolve()
        require(path.is_relative_to(copied), "Original binding escapes copy")
        name = path.relative_to(copied).as_posix()
        if name in EXTERNAL:
            require(digest == EXTERNAL[name], "Original historical source declaration changed")
            require(not path.exists(), "Missing-source comparison requires public payload only")
            missing[name] = digest
            del old_bindings[relative]
        else:
            require(sync.sha(path) == digest, "Original numerical/code/protocol binding differs: "+name)
    require(missing == EXTERNAL, "Original audit lacks exactly the declared historical source pair")
    adapter = sync.safe(copied, READBACK)
    relative_adapter = Path(os.path.relpath(adapter, run)).as_posix()
    require(relative_adapter not in old_bindings, "Adapter unexpectedly existed in original frozen audit")
    old_bindings[relative_adapter] = sync.sha(adapter)
    require(new["input_and_helper_sha256"] == old_bindings,
            "Binding delta must be exactly two historical exclusions and the new read-back adapter")
    require_bindings(run, new, copied)
    new_for_comparison = deepcopy(new)
    for key in NEW_FIELDS:
        del new_for_comparison[key]
    new_for_comparison["schema_version"] = original["schema_version"]
    new_for_comparison["status"] = original["status"]
    details = compare_summaries(adapted_original, new_for_comparison, run)
    return details, rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publication-manifest-sha256", required=True)
    parser.add_argument("--source-freeze-plan", required=True, type=Path)
    parser.add_argument("--adapter-source", required=True, type=Path)
    parser.add_argument("--adapter-test", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    args = parser.parse_args()
    manifest_path = sync.DEST/sync.MANIFEST
    require(sync.sha(manifest_path) == args.publication_manifest_sha256, "Final publication manifest SHA differs")
    manifest = sync.read(manifest_path)
    plan = sync.read(args.source_freeze_plan)
    require(isinstance(plan["files"], list) and plan["files"], "Missing final source freeze")
    before_sources = {row["path"]: sync.record(Path(row["source"]), row["path"]) for row in plan["files"]}
    require(all(before_sources[row["path"]] == {k:row[k] for k in ("path", "bytes", "sha256")}
                for row in plan["files"]), "Final source freeze differs")
    before_publication = payload_records(sync.DEST, manifest)
    require(before_publication == manifest["files"], "Publication differs from manifest")
    require(all(row["path"] not in EXTERNAL for row in manifest["files"]), "External text entered public payload")
    adapters = {READBACK: args.adapter_source.resolve(), READBACK_TEST: args.adapter_test.resolve()}
    adapter_records = {}
    for name, source in adapters.items():
        require(source == (sync.ROOT/name).resolve() and source.is_file(), "Unexpected explicit adapter source")
        require(not sync.safe(sync.DEST, name).exists(), "Adapter must be a new unpublished increment")
        adapter_records[name] = sync.record(source, name)
    before_source_evidence = evidence_inventory(sync.ROOT/"hf4_c2_diagnostics")
    before_publication_evidence = evidence_inventory(sync.DEST/"hf4_c2_diagnostics")
    parent = args.output_root.resolve()
    require(parent.is_relative_to(sync.ROOT/".github_handoff") and not parent.exists(), "Use a new handoff temporary tree")
    parent.mkdir()
    copied = parent/"publication"
    copied.mkdir()
    for row in manifest["files"]:
        target = sync.safe(copied, row["path"])
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(sync.safe(sync.DEST, row["path"]), target)
    (copied/sync.MANIFEST).parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(manifest_path, copied/sync.MANIFEST)
    require(payload_records(copied, manifest) == before_publication, "Copied publication is not byte-identical")
    for name, source in adapters.items():
        target = sync.safe(copied, name)
        require(not target.exists(), "Adapter cannot overwrite a copied file")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        require(sync.record(target, name) == adapter_records[name], "Copied adapter differs from explicit source")
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8",
               OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    results, error_text = [], None
    try:
        for case, expected in (("padding_2p5", "pass"), ("mesh_h00625", "not_pass")):
            run = copied/"hf4_c2_diagnostics/experiments"/case
            output = copied/"review_runs"/(case+"_numerical_readback.json")
            command = [sys.executable, "-B", str(copied/READBACK), "--run", str(run), "--output", str(output),
                       "--protocol", str(copied/"hf_repo/configs/contact_c2_v3.json")]
            log = parent/(case+".audit.log")
            print("Relocated numerical read-back: "+case+"; expected="+expected, flush=True)
            start = time.monotonic()
            with log.open("x", encoding="utf-8") as stream:
                process = subprocess.run(command, cwd=parent, env=env, stdout=stream,
                                         stderr=subprocess.STDOUT, timeout=1200)
            require(process.returncode == (0 if expected == "pass" else 1), "Unexpected numerical read-back exit code")
            new, old = sync.read(output), sync.read(run/"audit.json")
            require(old["status"] == expected, "Original expected status differs")
            details, external = compare_numerical_readback(old, new, run, copied)
            result = dict(case=case, numerical_status=expected, readback_status=new["status"],
                          historical_source_status=new["historical_source_status"], historical_sources=external,
                          valid_for_execution_admission=False, returncode=process.returncode,
                          elapsed_seconds=time.monotonic()-start, summary=new["summary"],
                          audit_sha256=sync.sha(output), log_sha256=sync.sha(log), details=details,
                          input_binding_count=len(new["input_and_helper_sha256"]),
                          exact_scientific_summary_and_detail_match=True)
            results.append(result)
            sync.write_new(parent/(case+".receipt.json"), result)
            print(json.dumps({k:result[k] for k in ("case", "numerical_status", "elapsed_seconds")}), flush=True)
    except Exception as error:
        error_text = type(error).__name__+": "+str(error)
    unchanged = (payload_records(sync.DEST, manifest) == before_publication
                 and sync.sha(manifest_path) == args.publication_manifest_sha256
                 and evidence_inventory(sync.ROOT/"hf4_c2_diagnostics") == before_source_evidence
                 and evidence_inventory(sync.DEST/"hf4_c2_diagnostics") == before_publication_evidence
                 and all(sync.record(Path(row["source"]), row["path"]) == before_sources[row["path"]]
                         for row in plan["files"])
                 and all(sync.record(source, name) == adapter_records[name]
                         and sync.record(sync.safe(copied, name), name) == adapter_records[name]
                         for name, source in adapters.items()))
    receipt = dict(schema="c2-relocated-numerical-readback-1.0",
                   status="pass" if error_text is None and unchanged else "not_pass",
                   created_utc=datetime.now(timezone.utc).isoformat(), cases=results, error=error_text,
                   source_and_publication_unchanged=unchanged, source_freeze_plan_sha256=sync.sha(args.source_freeze_plan),
                   publication_manifest_sha256=args.publication_manifest_sha256,
                   copied_payload_files=len(manifest["files"]), foreign_cwd=str(parent), copied_tree=str(copied),
                   additional_adapter_files=list(adapter_records.values()),
                   total_copied_files_excluding_manifest=len(manifest["files"])+len(adapter_records),
                   production_FE_executed=False, historical_source_status="not_reverified_external_source",
                   external_source_sha256=EXTERNAL, valid_for_execution_admission=False,
                   scope="Same-host numerical saved-state read-back; two external historical source texts not reverified; not cross-platform or complete-provenance validation",
                   expected_mechanical_status="partial; original failed mesh endpoint preserved")
    sync.write_new(parent/"receipt.json", receipt)
    print(json.dumps({k:receipt[k] for k in ("status", "error", "source_and_publication_unchanged")}), flush=True)
    return 0 if receipt["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
