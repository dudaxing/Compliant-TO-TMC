"""Numerical-only C2 readback with explicit external historical provenance.

This new entry point preserves the frozen numerical evaluator, tolerances and
prefix logic. It is never an execution-admission audit. Only the two exact
historical MATLAB source identities below may be absent from the admission
manifest; present files and every other input must still verify.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath

REPO = Path(__file__).resolve().parents[1]
PROTOCOL_SHA256 = "b17c8328dd1e350563b70305c0b311c8d38c9c0ef68c08b85fac5f13604d0b4d"
FROZEN_AUDITOR_SHA256 = "50bcbe18d67d62ea1bce621c9bfd2c1c6247dbe2b095a965dab42c00bc47e543"
SCHEMA_VERSION = "contact-c2-numerical-readback-1.0"
EXTERNAL_HISTORICAL_SOURCES = {
    "hf0_audit/tmc/assembleKtFi.m.numbered.txt": "56e6759471a87b1d32e75c3e8a3ba8a0a439d5dc3a959d27eed3d7e3a4d5285c",
    "hf0_audit/tmc/initializeFEA.m.numbered.txt": "ca0ead10a18ff35373c82f0b967876a19976adf6fca3afa06d22129515209ef0",
}
HISTORICAL_SOURCE_SCOPE = {
    "purpose": "Historical MATLAB formula-source review only; these numbered text files are not numerical-evaluation inputs.",
    "chain": ["hf4_c2_diagnostics/formulation_review/review_receipt.json",
              "hf4_c2_diagnostics/saved_field_admission_r3.json",
              "original audit.json input_and_helper_sha256"],
    "meaning": "Expected identities are bound by the unchanged v3 admission manifest and this entry point. A declared expected hash does not reverify absent source bytes.",
}
# Verify the frozen code before importing it, then bind it again during load.
if hashlib.sha256((REPO/"scripts/audit_contact_c2.py").read_bytes()).hexdigest() != FROZEN_AUDITOR_SHA256:
    raise ValueError("frozen C2 auditor changed")
from audit_contact_c2 import (
    CASES, C1_AUDITOR_SHA256, MEASUREMENT_SEMANTICS, THRESHOLDS,
    audit_state, bind, bind_completion, bind_manifest, classify_prefix,
    confined, load_controller, portable_bindings, read_json, read_npz,
    require, sha, validate_model, validate_protocol, write_new,
)


def bind_historical_admission(root, manifest, bindings):
    """No exception applies to implementation, production, model or state files."""
    require(isinstance(manifest, dict) and len(manifest) == 166,
            "frozen admission must contain exactly 166 source identities")
    for name, expected in EXTERNAL_HISTORICAL_SOURCES.items():
        require(manifest.get(name) == expected, "external historical identity changed: " + name)
    records = []
    for name, expected in manifest.items():
        require(isinstance(expected, str) and len(expected) == 64
                and all(character in "0123456789abcdef" for character in expected),
                "saved-field admission contains an invalid SHA-256")
        path = confined(root, name)
        require(str(path) not in bindings or bindings[str(path)] == expected,
                "conflicting pre-existing verified binding: " + name)
        # A dangling symlink is present evidence, not an absent original.
        present = path.exists() or (Path(root)/name).is_symlink()
        if name in EXTERNAL_HISTORICAL_SOURCES and not present:
            require(str(path) not in bindings, "absent historical source polluted verified bindings")
            records.append(dict(path=name, expected_sha256=expected,
                                status="not_reverified_external_source", actual_sha256=None))
        else:
            actual = bind(path, bindings, expected)
            if name in EXTERNAL_HISTORICAL_SOURCES:
                records.append(dict(path=name, expected_sha256=expected,
                                    status="verified", actual_sha256=actual))
    require(len(records) == 2, "historical source inventory changed")
    return sorted(records, key=lambda record: record["path"])


def historical_status(records):
    return ("verified" if all(record["status"] == "verified" for record in records)
            else "not_reverified_external_source")


def load_run(run, protocol_path, bindings):
    protocol_path = Path(protocol_path).resolve()
    require(protocol_path.is_relative_to(REPO), "protocol must reside in the portable repository tree")
    bind(REPO/"scripts/audit_contact_c2.py", bindings, FROZEN_AUDITOR_SHA256)
    bind(protocol_path, bindings, PROTOCOL_SHA256)
    protocol = read_json(protocol_path)
    validate_protocol(protocol)
    bind(protocol_path, bindings)
    bind(REPO/"configs/contact_c1_v1.json", bindings)
    if "implementation_sha256" in protocol:
        bind_manifest(REPO, protocol["implementation_sha256"], bindings, "frozen implementation manifest")
    gate_spec = protocol["saved_field_admission"]
    require(isinstance(gate_spec["path"], str) and "\\" not in gate_spec["path"]
            and ":" not in gate_spec["path"] and not PurePosixPath(gate_spec["path"]).is_absolute(),
            "admission path must be protocol-relative POSIX")
    gate = (protocol_path.parent/gate_spec["path"]).resolve()
    require(gate.is_relative_to(REPO.parent), "admission escapes repository/results tree")
    bind(gate, bindings, gate_spec["sha256"])
    admission = read_json(gate)
    require(admission.get("status") == "pass", "saved-field admission did not pass")
    historical_sources = bind_historical_admission(
        REPO.parent, admission["input_sha256_from_workspace_root"], bindings)
    meta = read_json(run/"metadata.json")
    bind(run/"metadata.json", bindings)
    require(meta.get("schema") == "contact_c2_run_v1" and meta.get("kind") == "TMC"
            and meta.get("mode") == "uniform" and meta.get("case_id") in CASES
            and meta.get("protocol") == protocol and meta.get("protocol_sha256") == sha(protocol_path),
            "run metadata is not bound to frozen C2 protocol")
    sources = meta.get("source_sha256")
    required = {"src/hf_eval/contact_c2.py", "src/hf_eval/split_affine.py", "src/hf_eval/split_kernel.py",
                "src/hf_eval/split_state.py", "scripts/run_contact_c2.py", "scripts/run_contact_c1_r2.py",
                "scripts/hf4_common.py"}
    require(isinstance(sources, dict) and required <= set(sources), "production source manifest is incomplete")
    for name, expected in sources.items():
        bind(confined(REPO, name), bindings, expected)
    require(sha(REPO/"scripts/audit_contact_c1.py") == C1_AUDITOR_SHA256, "frozen C1 audit prototype changed")
    for name in ("audit_contact_c2.py", "audit_contact_c1.py", "audit_contact_reference_a0.py",
                 "hf4_split_precision_reference.py", "hf2_precision_reference.py"):
        bind(REPO/"scripts"/name, bindings)
    complete = (run/"completion.json").exists()
    top_result = None
    if complete:
        _, top_result = bind_completion(run, "stages/index.json", bindings)
        top_rows = read_json(run/"stages/index.json")["stages"]
        require(top_result["stages"] == top_rows and len(top_rows) == 1
                and top_rows[0]["phase_id"] == "uniform_tmc"
                and top_rows[0]["directory"] == "stages/uniform_tmc", "run stage inventory differs")
    else:
        top_rows = None
        for name in ("result.json", "stages/index.json", "exception.json"):
            if (run/name).exists():
                bind(run/name, bindings)
    stage = run/"stages/uniform_tmc"
    require(stage.is_dir() and {p.name for p in (run/"stages").iterdir() if p.is_dir()} == {"uniform_tmc"},
            "missing or unindexed stage directory")
    require((stage/"completion.json").exists(),
            "interrupted stage lacks full-controller/completion inventory; standalone NPZ/record data remain readable but prefix certification is outside this audit scope")
    completion, compact = bind_completion(stage, "steps/index.json", bindings)
    if complete:
        require(top_result["status"] == top_rows[0]["status"] == completion["status"], "run/stage statuses disagree")
    stage_meta = read_json(stage/"metadata.json")
    require(stage_meta.get("source_initialization") == dict(type="geometric_zero"), "undeclared initialization source")
    bind(stage/"model.npz", bindings, stage_meta["model_sha256"])
    bind(stage/"initial_state.npz", bindings, stage_meta["initial_state_sha256"])
    model = read_npz(stage/"model.npz")
    groups = validate_model(model, stage_meta, meta, protocol)
    index = read_json(stage/"steps/index.json")
    full, inventory = load_controller(stage, compact, completion, index, model, groups, bindings)
    paths = []
    for entry in index["steps"]:
        name = entry["file"]
        require(isinstance(name, str) and PurePosixPath(name).name == name and name.endswith(".npz"),
                "state must use an NPZ basename")
        path = confined(stage/"steps", name)
        bind(path, bindings, entry["sha256"])
        paths.append(path)
    require(set(paths) == {p.resolve() for p in (stage/"steps").glob("*.npz")}, "unindexed or missing state NPZ")
    return dict(protocol=protocol, metadata=meta, stage_metadata=stage_meta, model=model, groups=groups,
                completed=complete, top_result=top_result, full=full, inventory=inventory,
                entries=index["steps"], paths=paths, historical_sources=historical_sources)


def audit(run, output, protocol_path):
    run, output = Path(run).resolve(), Path(output).resolve()
    require(not output.exists(), "audit output already exists")
    require(output.name != "audit.json", "numerical readback must use a distinct output name")
    # Re-audits select a new output stem and hence an independent detail tree.
    detail_directory = run/("audit_states" if output.name == "audit.json" else output.stem+"_states")
    require(not detail_directory.exists(), "audit detail directory already exists")
    bindings, detail_bindings, compact_states, stages = {}, {}, [], []
    data = load_run(run, protocol_path, bindings)
    bind(Path(__file__), bindings)
    detail_directory.mkdir()
    valid_prefix, passed_checks, total_checks = True, 0, 0
    for entry, record, path in zip(data["entries"], data["full"]["accepted_steps"], data["paths"]):
        print(f"Auditing uniform_tmc:{entry['index']} d={entry['d']} at 80/120 digits", flush=True)
        try:
            row = audit_state(data["model"], read_npz(path), entry, record, data["stage_metadata"],
                              data["groups"], data["protocol"], (80, 120))
        except (ValueError, KeyError, IndexError, ArithmeticError) as error:
            row = dict(state_id=f"uniform_tmc:{entry['index']}", phase_id="uniform_tmc", index=entry["index"],
                       parameter_s=entry["d"], status="not_pass", normal_force_raw=None,
                       error_type=type(error).__name__, error=str(error), checks=[])
        row["kind"] = "TMC"
        valid_prefix &= row["status"] == "pass"
        row["valid_prefix_comparable"] = valid_prefix
        total_checks += len(row["checks"])
        passed_checks += sum(check["status"] == "pass" for check in row["checks"])
        detail = detail_directory/f"state_{entry['index']:03d}.json"
        write_new(detail, row)
        relative = detail.relative_to(run).as_posix()
        digest = sha(detail)
        detail_bindings[relative] = digest
        keys = ("state_id", "phase_id", "kind", "index", "parameter_s", "status", "physical_mean_drive",
                "normal_force_raw", "is_original_target", "original_target_parameter", "bisection_depth",
                "valid_prefix_comparable")
        compact_states.append({**{key: row[key] for key in keys if key in row},
                               "detail_file": relative, "detail_sha256": digest,
                               "checks_count": len(row["checks"]),
                               "passed_checks": sum(check["status"] == "pass" for check in row["checks"])})
        del row
    prefix = classify_prefix(compact_states)
    stage_passed = data["inventory"]["status"] == "pass" and all(row["status"] == "pass" for row in compact_states)
    stages.append(dict(phase_id="uniform_tmc", status="pass" if stage_passed else "not_pass",
                       inventory=data["inventory"], initialization=dict(type="geometric_zero", split_arrays_verified=True),
                       state_ids=[row["state_id"] for row in compact_states]))
    passed = data["completed"] and data["top_result"]["status"] == "success" and stage_passed
    require(all(sha(Path(path)) == digest for path, digest in bindings.items()), "input/helper changed during audit")
    require(all(sha(run/name) == digest for name, digest in detail_bindings.items()), "detail output changed during audit")
    result = dict(schema_version=SCHEMA_VERSION, status="numerical_pass" if passed else "numerical_not_pass",
        numerical_status="pass" if passed else "not_pass", valid_for_execution_admission=False,
        historical_source_status=historical_status(data["historical_sources"]),
        historical_sources=data["historical_sources"], historical_source_scope=HISTORICAL_SOURCE_SCOPE,
        frozen_auditor_sha256=FROZEN_AUDITOR_SHA256, physical_protocol_sha256=PROTOCOL_SHA256,
        created_utc=datetime.now(timezone.utc).isoformat(), run=str(run), kind="TMC", mode="uniform",
        case_id=data["metadata"]["case_id"], case=data["metadata"]["case"], h=data["metadata"]["h"],
        measurement_precision=80, precision_digits=[80, 120], verification_precision_pair=[80, 120],
        measurement_semantics=MEASUREMENT_SEMANTICS,
        thresholds=THRESHOLDS, source_bindings=data["metadata"]["source_sha256"],
        prototype=dict(path="hf_repo/scripts/audit_contact_c1.py", sha256=C1_AUDITOR_SHA256,
            copied_function="audit_state", changes=["require 80/120", "outer-free whole mean is observational",
                                                    "add explicit weak-reaction aliases without changing values"]),
        input_and_helper_sha256=portable_bindings(run, bindings), detail_output_sha256=detail_bindings,
        states=compact_states, stages=stages, prefix=prefix,
        summary=dict(accepted_states=len(compact_states), passed_states=sum(row["status"] == "pass" for row in compact_states),
                     failed_states=[row["state_id"] for row in compact_states if row["status"] != "pass"],
                     independent_checks=total_checks, independent_checks_passed=passed_checks,
                     stage_count=1, planned_stage_count=1,
                     scope="uniform one-factor diagnostic; node reactions are not verified contact pressures"))
    output.parent.mkdir(parents=True, exist_ok=True)
    write_new(output, result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--protocol", required=True, type=Path)
    args = parser.parse_args(argv)
    if args.output.exists() or args.output.name == "audit.json":
        parser.error("select a new non-audit.json output; preserve prior evidence")
    try:
        result = audit(args.run, args.output, args.protocol)
    except (ValueError, KeyError, IndexError, OSError, ArithmeticError) as error:
        result = dict(schema_version=SCHEMA_VERSION, status="numerical_not_pass",
                      numerical_status="not_pass", valid_for_execution_admission=False,
                      historical_source_status="not_assessed_due_to_input_error", historical_sources=[],
                      historical_source_scope=HISTORICAL_SOURCE_SCOPE,
                      frozen_auditor_sha256=FROZEN_AUDITOR_SHA256, physical_protocol_sha256=PROTOCOL_SHA256,
                      run=str(args.run.resolve()), error_type=type(error).__name__, error=str(error), states=[])
        if not args.output.exists():
            args.output.parent.mkdir(parents=True, exist_ok=True)
            write_new(args.output, result)
    print(json.dumps({key: result[key] for key in
        ("status", "numerical_status", "historical_source_status", "summary", "error") if key in result}), flush=True)
    return 0 if result["numerical_status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
