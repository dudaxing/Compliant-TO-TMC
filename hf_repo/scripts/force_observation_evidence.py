"""Read/copy/hash-only evidence for the separately authorized F-OBS-1 card.

No scientific imports, subprocesses, test execution or candidate mutation.
verify_snapshot is a read-only entry point used by the single force probe.
The parent owns all deadlines, process-tree limits and final receipt binding.
"""
from __future__ import annotations

import argparse
import hashlib
from html import escape
import json
import os
from pathlib import Path
import sys
import time
import traceback

from s0_event_log import EventLog
from s0_preparation_evidence import (
    INPUT_SHA, JAX_FILES, append, bound, checked, copy_row, path, read,
    relative, require, sha, utc, write,
)

OLD_ROOT = "hf4_c2_stable_f_validation/jit_ad_ready_001"
OLD_BINDING_SHA = "487842e3ca0af7b7c6fff87ca72a4a730aa1ca2e4414e93c451d5b553b8875f6"
OLD_INPUT_SHA = "16831ce332badba05dc07cfa8f6069d5ab5e7a1736ebde3c658542d49834ef9c"
OLD_H1_SHA = "0999cf0e0270aa08c630569a7cb7136655910370b80a6e0fc6f68382fbadf358"
OLD_C1_SHA = "384708b23842d9d4c9d3324d57c854911772ca3eb9ab15ac9edb7efd6a1c4564"
ARITHMETIC = "src/hf_eval/compensated_invariants.py"
ARITHMETIC_SHA = "6a0144a92bf323951594a0d677b7558cf2a6501667f4b076dd13e2df6bba3897"
KERNEL = "src/hf_eval/split_kernel_invariants_hu.py"
KERNEL_SHA = "88d57ed77565963d8cc367c18398b11b30f8f1e0e335c7dcdbc3d68702ecb6bf"
TEST = "tests/test_compensated_invariants.py"
H1_TEST = "H1/" + TEST
H1_TEST_SHA = "15a81049f3fadcf0a0391f702db8444c33856f1116055d26e6ffca686821e946"
H1_MANIFEST = "H1/manifest.json"
PROVENANCE = "provenance/jit_ad_ready_001/"
RUNTIME_FILES = dict(JAX_FILES, **{
    "_src/pjit.py": "fc0f6e9a373ddb517391631bf65245f47829cb7339fd44d90bf4939622256734",
    "_src/stages.py": "9d5f1befad87a29605f342e9e1db4c83b9ddca5327d991f091bc2c740bff87aa",
    "_src/core.py": "5e10211a3602dc689bedb9eb3215009969ef4a8e8d6d698eb4af2949a8828976",
    "_src/interpreters/pxla.py": "998a14f7bd1ef00870f5c98463780a8c57bf81a2064c1f831b612550648a6370",
})
AUX_FILES = (
    "hf_repo/scripts/run_force_observation.py",
    "hf_repo/scripts/probe_force_observation.py",
    "hf_repo/scripts/force_observation_evidence.py",
    "hf_repo/scripts/probe_s0_preparation.py",
    "hf_repo/scripts/s0_preparation_evidence.py",
    "hf_repo/scripts/s0_event_log.py",
    "hf_repo/scripts/s0_ad_exception.py",
    "hf_repo/scripts/windows_owned_process.py",
    "docs/HF4_C2_S0_PREPARATION_RESULT_20260928.md",
    "docs/CURRENT_STATUS.md",
)
UNCHANGED_AUX = (
    "hf_repo/scripts/probe_s0_preparation.py",
    "hf_repo/scripts/s0_preparation_evidence.py",
    "hf_repo/scripts/s0_event_log.py",
    "hf_repo/scripts/s0_ad_exception.py",
    "hf_repo/scripts/windows_owned_process.py",
)
HISTORY_FILES = (
    "plan.json", "input_manifest.json", "output_sha256.json", "execution_receipt.json",
    "receipt_binding.json", "selected_source.json", "source_preservation.json",
    "failure_classification.json", "sync_started.json", "sync_journal.ndjson", "sync_receipt.json",
    "H1/manifest.json", "H1/proof.json", "H1/patch.diff",
    "C1/source_manifest.json", "C1/repair_proof.json", "C1/patch.diff",
    "events/A1_tests.ndjson", "logs/A1_tests.log", "results/A1_tests/pytest.xml",
    "events/A4_arithmetic.ndjson", "logs/A4_arithmetic.log", "results/A4_arithmetic/pytest.xml",
    "events/A5_force.ndjson", "logs/A5_force.log", "results/force/summary.json",
    "events/A7_seal.ndjson", "logs/A7_seal.log", "stage_timings.json", "resources.json",
)
FORCE_STAGES = (
    "source_binding", "runtime_import_and_prepare", "kernel_import", "input_transfer",
    "force.trace", "force.export_jaxpr", "force.lower", "force.export_stablehlo",
    "force.compile", "force.export_optimized_hlo", "force.call", "force.synchronize",
    "force.transfer", "force.save_output",
)
FORCE_ARTIFACTS = ("force_raw_jaxpr.txt", "force_stablehlo.mlir", "force_optimized_hlo.txt", "outputs.npz")


def binary_write(filename, data):
    filename.parent.mkdir(parents=True, exist_ok=True)
    with filename.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    checked(filename, hashlib.sha256(data).hexdigest(), len(data))


def inventory(directory):
    return {p.relative_to(directory).as_posix() for p in directory.rglob("*")
            if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"}


def verify_history(old):
    """Verify immutable old payloads, NEVER their obsolete row.source paths."""
    checked(old / "receipt_binding.json", OLD_BINDING_SHA)
    binding = read(old / "receipt_binding.json")
    expected = {
        "plan.json": binding["plan_sha256"], "input_manifest.json": binding["input_manifest_sha256"],
        "execution_receipt.json": binding["receipt_sha256"], "output_sha256.json": binding["output_manifest_sha256"],
        "C1/source_manifest.json": binding["selected_source_manifest_sha256"],
        "H1/manifest.json": binding["harness_manifest_sha256"],
        "events/A7_seal.ndjson": binding["seal_event_sha256"], "logs/A7_seal.log": binding["seal_log_sha256"],
        "receipt_binding.json": OLD_BINDING_SHA,
    }
    require(expected["input_manifest.json"] == OLD_INPUT_SHA and expected["H1/manifest.json"] == OLD_H1_SHA
            and expected["C1/source_manifest.json"] == OLD_C1_SHA, "old authority identity differs")
    for name, digest in expected.items():
        checked(bound(old, name), digest)
    outputs = read(old / "output_sha256.json")
    require(isinstance(outputs, dict) and len(outputs) == 190, "old payload inventory differs")
    total = 0
    for name, digest in outputs.items():
        checked(bound(old, name), digest)
        total += (old / name).stat().st_size
        if name in expected:
            require(expected[name] == digest, "old binding and output identities disagree")
        expected[name] = digest
    old_input = read(old / "input_manifest.json")
    for row in old_input["files"]:
        checked(bound(old, row["path"]), row["sha256"], row["bytes"])
        require(expected[row["path"]] == row["sha256"], "old frozen input and output identities disagree")
    for manifest_name in ("H1/manifest.json", "C1/source_manifest.json"):
        manifest = read(old / manifest_name)
        for row in manifest["files"]:
            checked(bound(old, row["path"]), row["sha256"], row["bytes"])
            require(expected[row["path"]] == row["sha256"], "old derived payload identity differs")
        for name, digest in manifest["proof_artifacts"].items():
            checked(bound(old, name), digest)
            require(expected[name] == digest, "old proof and output identities disagree")
    sync = read(old / "sync_receipt.json")
    selected = read(old / "selected_source.json")
    require(sync["status"] == "pass" and sync["selected"] == selected and selected["version"] == "C1"
            and selected["source_manifest_sha256"] == OLD_C1_SHA
            and selected["harness"]["manifest_sha256"] == OLD_H1_SHA, "old selected/sync identity differs")
    checked(old / "sync_journal.ndjson", sync["journal_sha256"])
    checked(old / "events/A4_arithmetic.ndjson", sync["A4_event_sha256"])
    require(read(old / "execution_receipt.json")["status"] == "resource_or_supervision_stop",
            "old terminal receipt differs")
    return dict(status="pass", binding_sha256=OLD_BINDING_SHA, payload_files=len(outputs), payload_bytes=total,
                immutable_input_files=len(old_input["files"]), old_live_sources_checked=False), expected


def harness_metadata(root):
    manifest = read(root / H1_MANIFEST)
    require(manifest["version"] == "H1" and manifest["test_path"] == H1_TEST
            and manifest["test_sha256"] == H1_TEST_SHA and manifest["upstream_manifest_sha256"] == OLD_H1_SHA,
            "relocated H1 identity differs")
    checked(root / H1_TEST, H1_TEST_SHA)
    return dict(version="H1", manifest_path=str(root / H1_MANIFEST), manifest_sha256=sha(root / H1_MANIFEST),
                test_path=str(root / H1_TEST), test_sha256=H1_TEST_SHA)


def selected_metadata(root):
    return dict(schema="hf-force-observation-selected-source-1", version="C1",
        source=str(root / "C1/source/hf_repo"), source_manifest=str(root / "input_manifest.json"),
        source_manifest_sha256=sha(root / "input_manifest.json"), harness=harness_metadata(root),
        original_science_manifest_sha256=OLD_C1_SHA, scientific_admission=False)


def prepare(root, repo, events):
    require(not any((root / name).exists() for name in ("input_manifest.json", "C1", "H1", "selected_source.json")),
            "preparation is write-once")
    old = repo / OLD_ROOT
    history, authorities = verify_history(old)
    events.emit("historical_payloads_verified", **history)
    rows = []
    for name in HISTORY_FILES:
        require(name in authorities, "required historical authority is not bound: " + name)
        rows.append(copy_row(root, old / name, PROVENANCE + name, expected=authorities[name],
                             role="historical_frozen_authority"))
    c1 = read(old / "C1/source_manifest.json")
    require(len(c1["files"]) == 32, "C1 source inventory differs")
    require(inventory(old / "C1/source/hf_repo") == {r["path"].removeprefix("C1/source/hf_repo/") for r in c1["files"]},
            "old C1 source contains missing or unmanifested files")
    for row in c1["files"]:
        require(row["path"].startswith("C1/source/hf_repo/"), "C1 source path is unexpected")
        rows.append(copy_row(root, bound(old, row["path"]), row["path"], expected=row["sha256"], size=row["bytes"],
                             role="unchanged_C1_science_and_historical_H0"))
    for name in (H1_TEST, "H1/proof.json", "H1/patch.diff"):
        rows.append(copy_row(root, old / name, name, expected=authorities[name], role="unchanged_H1_test_or_proof"))
    checked(root / H1_TEST, H1_TEST_SHA)
    h1_row = next(r for r in rows if r["path"] == H1_TEST)
    write(root / H1_MANIFEST, dict(schema="hf-force-observation-harness-1", version="H1", test_path=H1_TEST,
        test_sha256=H1_TEST_SHA, relocation_only=True, test_bytes_changed=False,
        upstream_manifest_path=PROVENANCE + "H1/manifest.json", upstream_manifest_sha256=OLD_H1_SHA,
        inherited_test_count=9, tests_executed_in_this_card=False, files=[h1_row],
        proof_artifacts={name:sha(root/name) for name in ("H1/proof.json","H1/patch.diff")}))
    for name in ("data/inputs.npz", "data/input_freeze.json", "data/original_output_sha256.json"):
        rows.append(copy_row(root, old / name, name, expected=authorities[name], role="original_unit_input_authority"))
    checked(root / "data/inputs.npz", INPUT_SHA)
    freeze = read(root / "data/input_freeze.json")
    require(freeze["case"] == "unit__near_rotation" and freeze["input_sha256"] == INPUT_SHA,
            "original unit freeze differs")
    original_outputs = read(root / "data/original_output_sha256.json")
    require(original_outputs["unit__near_rotation/inputs.npz"] == INPUT_SHA
            and original_outputs["unit__near_rotation/input_freeze.json"] == sha(root / "data/input_freeze.json"),
            "original input output authority differs")
    for name in AUX_FILES:
        digest = authorities["aux/"+name] if name in UNCHANGED_AUX else None
        rows.append(copy_row(root, repo/name, "aux/"+name, expected=digest,
                             role="unchanged_auxiliary" if digest else "new_auxiliary"))
    installed = path(sys.executable).parent.parent / "Lib/site-packages/jax"
    for name,digest in RUNTIME_FILES.items():
        if name not in ("_src/core.py", "_src/interpreters/pxla.py"):
            require(authorities["aux/runtime/jax/"+name] == digest, "inherited runtime source identity differs")
        rows.append(copy_row(root, installed/name, "aux/runtime/jax/"+name, expected=digest,
                             role="installed_primary_JAX_source"))
    canonical = {}
    source = root / "C1/source/hf_repo"
    science_src = inventory(source / "src")
    require(len(science_src) == 29 and inventory(repo / "hf_repo/src") == science_src,
            "canonical science source inventory differs")
    for name in sorted(science_src):
        relative_name = "src/"+name
        digest = sha(source/relative_name)
        canonical[relative_name] = dict(path=str(repo / "hf_repo" / relative_name), sha256=digest)
        checked(repo / "hf_repo" / relative_name, digest)
    canonical[TEST] = dict(path=str(repo / "hf_repo" / TEST), sha256=H1_TEST_SHA)
    checked(repo / "hf_repo" / TEST, H1_TEST_SHA)
    checked(source / ARITHMETIC, ARITHMETIC_SHA)
    checked(source / KERNEL, KERNEL_SHA)
    upstream_input = read(old / "input_manifest.json")
    require(sys.version == upstream_input["python"]["version"], "Python runtime version differs")
    write(root / "input_manifest.json", dict(schema="hf-force-observation-inputs-1", protocol="F-OBS-1",
        created_utc=utc(), repo=str(repo), files=rows,
        science=dict(version="C1", source=str(source), upstream_manifest_sha256=OLD_C1_SHA,
                     upstream_manifest_path=PROVENANCE+"C1/source_manifest.json",
                     arithmetic_sha256=ARITHMETIC_SHA, kernel_sha256=KERNEL_SHA),
        harness=harness_metadata(root), canonical_files=canonical,
        original_authority=dict(root=str(old), binding_sha256=OLD_BINDING_SHA, verification=history,
                                current_live_historical_source_paths_checked=False),
        original_input=dict(case="unit__near_rotation", direction=0, input_sha256=INPUT_SHA),
        python=dict(executable=sys.executable, version=sys.version), scientific_admission=False,
        inherited_test_result="C1+H1 original nine passed; no tests repeated; no completed old force output"))
    write(root / "selected_source.json", selected_metadata(root))
    result = verify_snapshot(root, repo)
    events.emit("preparation_complete", input_manifest_sha256=sha(root/"input_manifest.json"),
                selected=read(root/"selected_source.json"))
    return dict(status="pass", files=len(rows), copied_bytes=sum(r["bytes"] for r in rows),
                source_verification=result, scientific_admission=False)


def verify_snapshot(root, repo=None, *, require_live=True):
    """Pure stdlib, read-only verification; never creates any file or cache."""
    root = path(root)
    manifest = read(root / "input_manifest.json")
    require(manifest["schema"] == "hf-force-observation-inputs-1" and manifest["protocol"] == "F-OBS-1",
            "input manifest schema/protocol differs")
    repo = path(repo if repo is not None else manifest["repo"])
    require(repo == path(manifest["repo"]), "canonical repository identity differs")
    names = set()
    for row in manifest["files"]:
        require(row["path"] not in names, "duplicate current input path")
        names.add(row["path"])
        checked(bound(root,row["path"]),row["sha256"],row["bytes"])
        if require_live:
            checked(row["source"],row["sha256"],row["bytes"])
    science = manifest["science"]
    require(science["version"] == "C1" and path(science["source"]) == root / "C1/source/hf_repo"
            and science["upstream_manifest_sha256"] == OLD_C1_SHA, "science source identity differs")
    checked(root / PROVENANCE / "C1/source_manifest.json",OLD_C1_SHA)
    checked(root / PROVENANCE / "H1/manifest.json",OLD_H1_SHA)
    checked(root / PROVENANCE / "receipt_binding.json",OLD_BINDING_SHA)
    source = root / "C1/source/hf_repo"
    expected_source_names = {r["path"].removeprefix("C1/source/hf_repo/") for r in manifest["files"]
                             if r["path"].startswith("C1/source/hf_repo/")}
    require(inventory(source) == expected_source_names and len(expected_source_names) == 32,
            "frozen C1 source inventory changed")
    checked(source / ARITHMETIC,ARITHMETIC_SHA)
    checked(source / KERNEL,KERNEL_SHA)
    h1 = read(root/H1_MANIFEST)
    require(manifest["harness"] == harness_metadata(root) and h1["relocation_only"]
            and not h1["test_bytes_changed"], "H1 relocation binding differs")
    for row in h1["files"]:
        checked(bound(root,row["path"]),row["sha256"],row["bytes"])
    for name,digest in h1["proof_artifacts"].items():
        checked(bound(root,name),digest)
    require(read(root/"selected_source.json") == selected_metadata(root), "selected source identity differs")
    if require_live:
        for name,row in manifest["canonical_files"].items():
            require(path(row["path"]) == repo/"hf_repo"/name, "canonical path escaped declared repository")
            checked(row["path"],row["sha256"])
        require(inventory(repo/"hf_repo/src") == inventory(source/"src"), "canonical source inventory changed")
    return dict(status="pass", input_files=len(names), input_bytes=sum(r["bytes"] for r in manifest["files"]),
        C1_files=32, H1_test_files=1, canonical_files=len(manifest["canonical_files"]),
        missing=0, mismatches=0, live_new_sources_checked=bool(require_live),
        obsolete_historical_live_sources_checked=False, input_manifest_sha256=sha(root/"input_manifest.json"),
        harness_manifest_sha256=sha(root/H1_MANIFEST), upstream_science_manifest_sha256=OLD_C1_SHA,
        scientific_admission=False)


def best_effort_preservation(root, repo, error):
    """Preserve incomplete preparation or a mismatch without inventing success."""
    result = dict(status="evidence_failure", error=dict(type=type(error).__name__,message=str(error)),
                  copied_records=[], journal_complete=None, problems=[], scientific_admission=False)
    manifest_path = root/"input_manifest.json"
    rows = []
    if manifest_path.exists():
        try:
            manifest = read(manifest_path)
            rows = manifest["files"]
            result["input_manifest_sha256"] = sha(manifest_path)
        except Exception as problem:
            result["problems"].append(dict(path="input_manifest.json",error=str(problem)))
    journal = root/"prepare_journal.ndjson"
    if journal.exists():
        raw = journal.read_bytes()
        result["journal_sha256"] = sha(journal)
        result["journal_complete"] = raw.endswith(b"\n")
        if not rows:
            for line in raw.splitlines(keepends=True):
                if not line.endswith(b"\n"):
                    break
                try:
                    row = json.loads(line)
                    if row.get("event") == "copy_verified":
                        rows.append(row)
                except Exception as problem:
                    result["problems"].append(dict(path="prepare_journal.ndjson",error=str(problem)))
                    break
    for row in rows:
        observation = dict(path=row["path"], expected_sha256=row["sha256"],expected_bytes=row["bytes"])
        for side,filename in (("copy",bound(root,row["path"])),("source",path(row["source"]))):
            try:
                observation[side] = dict(exists=filename.is_file(),sha256=sha(filename) if filename.is_file() else None,
                    bytes=filename.stat().st_size if filename.is_file() else None)
                checked(filename,row["sha256"],row["bytes"])
                observation[side]["matches"] = True
            except Exception as problem:
                observation.setdefault(side,{})["matches"] = False
                observation[side]["error"] = str(problem)
        result["copied_records"].append(observation)
    recorded_names = {row["path"] for row in rows}
    result["uncommitted_input_files"] = []
    for folder in ("C1","H1","data","aux","provenance"):
        directory = root/folder
        if not directory.exists():
            continue
        for filename in sorted(directory.rglob("*")):
            if filename.is_file() and filename.relative_to(root).as_posix() not in recorded_names:
                result["uncommitted_input_files"].append(dict(
                    path=filename.relative_to(root).as_posix(),bytes=filename.stat().st_size,sha256=sha(filename),
                    status="not_in_verified_copy_records", expected_source_identity=None))
    result["uncommitted_scope"] = (
        "Actual F0 input files absent from available verified-copy rows; may include interrupted copies "
        "or generated binding metadata. Payload hashes alone establish no accepted source identity.")
    result["canonical_actual"] = {}
    for name in (ARITHMETIC,KERNEL,TEST):
        filename = repo/"hf_repo"/name
        result["canonical_actual"][name] = dict(exists=filename.is_file(),sha256=sha(filename) if filename.is_file() else None)
    result["limitation"] = "partial preparation/mismatches are preserved, not an accepted source state"
    return result


def read_probe(root):
    filename = root/"results/force/summary.json"
    if not filename.exists():
        return None, None
    try:
        return read(filename), None
    except Exception as error:
        return None, dict(type=type(error).__name__,message=str(error),path="results/force/summary.json")


def artifact_observations(root, summary):
    directory = root/"results/force"
    rows, problems, declared = [], [], set()
    for name,record in (summary or {}).get("artifacts",{}).items():
        try:
            filename = bound(directory,record.get("path",name))
            declared.add(filename.relative_to(directory).as_posix())
            state = record.get("status","uncommitted")
            item = dict(path=filename.relative_to(root).as_posix(),declared_status=state,
                        exists=filename.is_file(),status="partial")
            if filename.is_file():
                item.update(bytes=filename.stat().st_size,sha256=sha(filename))
            if state == "complete":
                checked(filename,record["sha256"],record["bytes"])
                item["status"] = "complete"
            rows.append(item)
        except Exception as error:
            problems.append(dict(artifact=name,error=type(error).__name__+": "+str(error)))
    if directory.exists():
        for filename in sorted(directory.rglob("*")):
            if not filename.is_file() or filename.name in ("summary.json","summary.pending.json"):
                continue
            name = filename.relative_to(directory).as_posix()
            if name not in declared:
                rows.append(dict(path=filename.relative_to(root).as_posix(),status="partial_uncommitted",
                                 exists=True,bytes=filename.stat().st_size,sha256=sha(filename)))
    return dict(schema="hf-force-observation-artifacts-1",artifacts=rows,problems=problems,
                limitation="complete bytes do not establish a completed scientific force or passed stage")


def stage_timings(root, resources, summary, summary_error):
    cutoff = None
    try:
        cutoff = read(root/"plan.json")["start_monotonic"] + resources["total_elapsed_seconds"]
    except (OSError,ValueError,KeyError,TypeError):
        pass
    events_path = root/"events/F1_force.ndjson"
    starts, bindings, event_issues = {}, {}, []
    if (root/"results/force/summary.json").exists():
        bindings["results/force/summary.json"] = sha(root/"results/force/summary.json")
    if events_path.exists():
        bindings["events/F1_force.ndjson"] = sha(events_path)
        lines = events_path.read_bytes().splitlines(keepends=True)
        if lines and not lines[-1].endswith(b"\n"):
            lines.pop()
            event_issues.append("partial final event retained in raw file but not timing")
        for line in lines:
            try:
                event = json.loads(line)
                if event.get("event") == "stage_started":
                    starts[event["stage"]] = event["monotonic"]
            except (ValueError,KeyError,TypeError) as error:
                event_issues.append(str(error))
    steps = {row["stage"]:row for row in (summary or {}).get("steps",[])}
    rows = []
    for name in list(FORCE_STAGES) + [n for n in steps if n not in FORCE_STAGES]:
        row = steps.get(name,{})
        state = row.get("status","not_reached")
        if state in ("pass","failed") and "elapsed_seconds" in row:
            seconds,basis = row["elapsed_seconds"],"complete saved record"
        elif name in starts and cutoff is not None:
            state,seconds,basis = "open_at_stop",max(0.,cutoff-starts[name]),"upper observation interval includes cleanup/dispatch; NOT completed duration"
        else:
            seconds,basis = None,"no completed saved duration"
        rows.append(dict(stage=name,status=state,seconds=seconds,timing_basis=basis))
    return dict(schema="hf-force-observation-stage-timings-1",rows=rows,source_sha256=bindings,
        observation_cutoff_monotonic=cutoff,call_to_synchronize=(summary or {}).get("call_to_synchronize"),
        summary_error=summary_error,event_issues=event_issues,
        scope="F1 saved observations only; call may include work; synchronization is readiness, not pure kernel time")


def verify_complete_force(root, summary):
    """Validate saved observations only, without importing arrays or a kernel."""
    require(isinstance(summary,dict) and summary["schema"] == "hf-force-observation-probe-1"
            and summary["protocol"] == "F-OBS-1" and summary["mode"] == "force"
            and summary["source_version"] == "C1" and summary["status"] == "pass"
            and not summary["errors"] and not summary["scientific_admission"],
            "force terminal summary does not support completion")
    selected = read(root/"selected_source.json")
    require(path(summary["source"]) == root/"C1/source/hf_repo"
            and summary["source_manifest_sha256"] == selected["source_manifest_sha256"]
            and summary["harness"] == selected["harness"], "force terminal identity differs")
    require(summary["expected_stages"] == list(FORCE_STAGES)
            and [s["stage"] for s in summary["steps"]] == list(FORCE_STAGES)
            and all(s["status"] == "pass" and s["elapsed_seconds"] >= 0 for s in summary["steps"]),
            "force fixed stage sequence is incomplete or repeated")
    contract = summary["execution_contract"]
    require(all(contract[n] == 1 for n in ("trace","lower","compile","compiled_call","output_synchronization"))
            and contract["warmup"] == contract["retries"] == 0, "force execution contract differs")
    require(set(summary["artifacts"]) == set(FORCE_ARTIFACTS), "force artifact inventory differs")
    for name in FORCE_ARTIFACTS:
        record = summary["artifacts"][name]
        require(record["status"] == "complete" and record["path"] == name and record["bytes"] > 0,
                "required force artifact is incomplete")
        checked(root/"results/force"/name,record["sha256"],record["bytes"])
    validation = summary["output_validation"]
    require(validation["status"] == "pass" and validation["finite_binary64"]
            and validation["positive_J"] and validation["arithmetic_supported"] and validation["min_J"] > 0
            and set(validation["fields"]) == set(contract["force_output_fields"])
            and len(validation["fields"]) == 26 and all(v["dtype"] == "float64" for v in validation["fields"].values()),
            "force original output gates were not recorded as passed")
    require(summary["source_preservation"]["status"] == "pass"
            and summary["source_preservation"]["input_manifest_sha256"] == sha(root/"input_manifest.json"),
            "force final source preservation is absent or mismatched")
    interval = summary["call_to_synchronize"]
    require(interval["status"] == "complete" and interval["call_returned"]
            and interval["start_monotonic"] <= interval["call_return_monotonic"] <= interval["end_monotonic"]
            and interval["elapsed_seconds"] == interval["end_monotonic"]-interval["start_monotonic"],
            "force continuous call/synchronization interval is incomplete")
    filename = root/"events/F1_force.ndjson"
    raw = filename.read_bytes()
    require(raw.endswith(b"\n"), "complete force event stream is truncated")
    rows = [json.loads(line) for line in raw.splitlines()]
    for index,row in enumerate(rows,1):
        require(row["schema"] == "hf-s0-event-1" and row["sequence"] == index and row["phase"] == "F1_force"
                and row["version"] == "C1" and row["source_manifest_sha256"] == sha(root/"input_manifest.json"),
                "force event identity or sequence differs")
    require(rows and rows[0]["event"] == "probe_started" and rows[-1]["event"] == "probe_finished"
            and rows[-1]["outcome"] == "pass" and rows[-1]["mode"] == "force"
            and sum(r["event"] == "probe_started" for r in rows) == 1
            and sum(r["event"] == "probe_finished" for r in rows) == 1
            and not any(r["event"] in ("stage_failed","probe_failed") for r in rows),
            "force event terminal outcome is incomplete")
    starts = [(i,r) for i,r in enumerate(rows) if r["event"] == "stage_started"]
    ends = [(i,r) for i,r in enumerate(rows) if r["event"] == "stage_finished"]
    require([r["stage"] for _,r in starts] == list(FORCE_STAGES)
            and [r["stage"] for _,r in ends] == list(FORCE_STAGES)
            and all(r["outcome"] == "pass" for _,r in ends), "force event stages differ")
    for index,((start,_),(end,_)) in enumerate(zip(starts,ends)):
        require(start < end and (index == len(starts)-1 or end < starts[index+1][0]),
                "force stage event ordering differs")
    artifact_events = [(i,r) for i,r in enumerate(rows) if r["event"] == "artifact_complete"]
    require([r["artifact"] for _,r in artifact_events] == list(FORCE_ARTIFACTS),
            "complete force artifact events differ")
    for (index,row),stage in zip(artifact_events,("force.export_jaxpr","force.export_stablehlo",
                                                "force.export_optimized_hlo","force.save_output")):
        artifact = summary["artifacts"][row["artifact"]]
        stage_index = FORCE_STAGES.index(stage)
        require(starts[stage_index][0] < index < ends[stage_index][0]
                and row["artifact_status"] == "complete"
                and all(row[k] == artifact[k] for k in ("path","bytes","sha256")),
                "force artifact event and saved bytes differ")
    return dict(status="complete_fixed_force_no_scientific_admission",stages=14,artifacts=4,
                event_sha256=sha(filename),summary_sha256=sha(root/"results/force/summary.json"),
                scientific_admission=False)


def resource_svg(resources):
    rows = resources.get("phases",[])
    height = 90+42*len(rows)
    time_max = max([r.get("elapsed_seconds",0) for r in rows]+[1.])
    rss_max = max([r.get("peak_tree_rss_bytes",0) for r in rows]+[1.])
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="{height}">',
        '<rect width="100%" height="100%" fill="white"/><g font-family="Arial,sans-serif" font-size="12">',
        '<text x="20" y="24">F-OBS-1 phases BEFORE F2; final parent receipt includes F2; no scientific admission</text>',
        '<text x="390" y="52">Wall seconds</text><text x="790" y="52">Sampled process-tree RSS (MiB)</text>']
    for index,row in enumerate(rows):
        y = 75+42*index
        seconds,rss = row.get("elapsed_seconds",0),row.get("peak_tree_rss_bytes",0)
        clean = row.get("cleanup_verified",False)
        state = "exit0/clean" if row.get("returncode") == 0 and clean else row.get("reason","unknown")
        color = "#356c9b" if row.get("returncode") == 0 and clean else "#a84040"
        parts.extend((f'<text x="20" y="{y+12}">{escape(row["name"])} | {escape(state)}</text>',
            f'<rect x="390" y="{y}" width="{280*seconds/time_max:.3f}" height="15" fill="{color}"/>',
            f'<text x="680" y="{y+12}">{seconds:.3f}</text>',
            f'<rect x="790" y="{y}" width="{230*rss/rss_max:.3f}" height="15" fill="#497f65"/>',
            f'<text x="1040" y="{y+12}">{rss/1024**2:.2f}</text>'))
    return "".join(parts)+'</g></svg>\n'


def stages_svg(timings):
    rows = timings["rows"]
    height = 108+29*len(rows)
    maximum = max([r["seconds"] for r in rows if r["seconds"] is not None]+[1.])
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="{height}">',
        '<rect width="100%" height="100%" fill="white"/><g font-family="Arial,sans-serif" font-size="12">',
        '<text x="20" y="24">F-OBS-1 saved F1 stages; no completed-force or scientific claim from an open interval</text>',
        '<text x="20" y="46">Orange includes cleanup/dispatch to checkpoint; call and synchronization are not pure kernel timings.</text>']
    for index,row in enumerate(rows):
        y = 70+29*index
        parts.append(f'<text x="20" y="{y+11}">{escape(row["stage"])}</text>')
        value = row["seconds"]
        color = "#ca842e" if row["status"] == "open_at_stop" else ("#a84040" if row["status"] == "failed" else "#356c9b")
        if value is not None:
            parts.append(f'<rect x="390" y="{y}" width="{400*value/maximum:.3f}" height="14" fill="{color}"/>')
        shown = "n/a" if value is None else f"{value:.6f} s"
        parts.append(f'<text x="810" y="{y+11}">{shown} | {escape(row["status"])}</text>')
    return "".join(parts)+'</g></svg>\n'


def seal(root, repo, events):
    try:
        preservation = verify_snapshot(root,repo)
    except Exception as error:
        preservation = best_effort_preservation(root,repo,error)
    write(root/"source_preservation.json",preservation)
    try:
        resources = read(root/"resources.json")
    except Exception as error:
        resources = dict(phases=[],resource_record_error=str(error))
    summary, summary_error = read_probe(root)
    artifacts = artifact_observations(root,summary)
    write(root/"artifact_status.json",artifacts)
    timings = stage_timings(root,resources,summary,summary_error)
    write(root/"stage_timings.json",timings)
    binary_write(root/"resources.svg",resource_svg(resources).encode())
    binary_write(root/"stages.svg",stages_svg(timings).encode())
    phase = os.environ["HF_S0_PHASE"]
    excluded = {"output_sha256.json","receipt_binding.json","execution_receipt.json","ledger.json",
                "logs/"+phase+".log","events/"+phase+".ndjson"}
    force_completion = dict(status="not_claimed_parent_stopped",parent_status=resources.get("status"),
                            scientific_admission=False)
    complete = preservation["status"] == "pass" and not artifacts["problems"]
    complete = complete and "resource_record_error" not in resources
    if resources.get("status") == "fixed_force_complete_no_scientific_admission":
        try:
            force_completion = verify_complete_force(root,summary)
        except Exception as error:
            complete = False
            force_completion = dict(status="completion_not_supported",scientific_admission=False,
                                    error=dict(type=type(error).__name__,message=str(error)))
    result = dict(schema="hf-force-observation-evidence-worker-1",action="seal",
        status="pass" if complete else "evidence_failure",payload_sealed=True,scientific_admission=False,
        source_preservation=preservation,artifact_status_path="artifact_status.json",force_observation=force_completion,
        resources_scope="before F2 only; parent receipt includes F2 after cleanup",
        excluded_live_or_final_bindings=sorted(excluded),
        limitation="sealing intact or partial payloads is not a completed force or scientific pass")
    write(root/"results/seal/summary.json",result)
    files = {f.relative_to(root).as_posix():sha(f) for f in sorted(root.rglob("*"))
             if f.is_file() and f.relative_to(root).as_posix() not in excluded}
    write(root/"output_sha256.json",files)
    events.emit("seal_complete",status=result["status"],output_manifest_sha256=sha(root/"output_sha256.json"))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--repo",type=Path,required=True)
    parser.add_argument("--action",choices=("prepare","seal"),required=True)
    args = parser.parse_args()
    root,repo = path(args.root),path(args.repo)
    require(root != repo and not repo.is_relative_to(root),"evidence root must not contain repository")
    root.mkdir(parents=True,exist_ok=True)
    output = root/"results"/args.action
    events,begin = EventLog(),time.perf_counter()
    try:
        require(not output.exists(),"worker action cannot be repeated")
        events.emit("worker_started",action=args.action)
        if args.action == "seal":
            result = seal(root,repo,events)
            return 0 if result["status"] == "pass" else 2
        result = prepare(root,repo,events)
        write(output/"summary.json",dict(schema="hf-force-observation-evidence-worker-1",action=args.action,
            elapsed_seconds=time.perf_counter()-begin,**result))
        events.emit("worker_finished",action=args.action,status=result["status"])
        return 0
    except Exception as error:
        failure = dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc())
        if not (output/"summary.json").exists():
            write(output/"summary.json",dict(schema="hf-force-observation-evidence-worker-1",action=args.action,
                status="evidence_failure",elapsed_seconds=time.perf_counter()-begin,scientific_admission=False,error=failure))
        events.emit("worker_failed",action=args.action,**failure)
        return 2
    finally:
        events.close()


if __name__ == "__main__":
    raise SystemExit(main())
