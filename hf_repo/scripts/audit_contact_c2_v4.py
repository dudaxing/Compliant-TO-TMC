"""Independent 80/120-digit audit of a v4 kernel-repair run; no production FE, solver or AD imports.

The numerical evaluator, gates, geometry checks, controller/record inventory and prefix logic are the
frozen v3 C2 audit's own functions (scripts/audit_contact_c2.py, verified by its original bytes before it
is imported and reused unchanged). Only the identity-loading layer is replaced: the v4 protocol content is
checked against the frozen v3/C1 contracts, the run must carry the v4 run schema and kernel identity, and
the required production sources are the compensated kernel, its arithmetic module, the one-line-difference
path solver and the v4 runner. A v4 result never re-labels the v3 history, which stays NOT_PASS.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath

REPO = Path(__file__).resolve().parents[1]
FROZEN_AUDITOR_SHA256 = "50bcbe18d67d62ea1bce621c9bfd2c1c6247dbe2b095a965dab42c00bc47e543"
# Verify the frozen code before importing it, then bind it again during load.
if hashlib.sha256((REPO/"scripts/audit_contact_c2.py").read_bytes()).hexdigest() != FROZEN_AUDITOR_SHA256:
    raise ValueError("frozen C2 auditor changed")
from audit_contact_c2 import (  # noqa: E402
    C1_AUDITOR_SHA256, MEASUREMENT_SEMANTICS, THRESHOLDS,
    audit_state, bind, bind_completion, bind_manifest, classify_prefix,
    confined, load_controller, portable_bindings, read_json, read_npz,
    require, sha, validate_model, write_new,
)
import contact_c2_v4_contract as contract  # noqa: E402

REQUIRED_RUN_SOURCES = {
    "src/hf_eval/contact_c2.py", "src/hf_eval/split_affine_compensated.py", "src/hf_eval/split_kernel_compensated.py",
    "src/hf_eval/compensated_kinematics.py", "src/hf_eval/split_state.py", "scripts/run_contact_c2_v4.py",
    "scripts/contact_c2_v4_contract.py", "scripts/hf4_common.py",
}


def validate_protocol_v4(protocol):
    v3 = read_json(REPO/contract.V3_PROTOCOL_PATH)
    c1 = read_json(REPO/contract.C1_PROTOCOL_PATH)
    require(sha(REPO/contract.V3_PROTOCOL_PATH) == contract.V3_PROTOCOL_SHA256, "frozen v3 protocol changed")
    require(sha(REPO/contract.C1_PROTOCOL_PATH) == contract.C1_PROTOCOL_SHA256, "frozen C1 protocol changed")
    try:
        contract.validate_protocol(protocol, v3, c1)
    except contract.V4ContractError as error:
        raise ValueError(str(error)) from error
    # The frozen numerical gates themselves are asserted against the frozen audit's thresholds too.
    require(protocol["audit"].get("precisions") == [80, 120], "C2 requires 80/120 arithmetic")


def load_run(run, protocol_path, bindings):
    protocol_path = Path(protocol_path).resolve()
    require(protocol_path.is_relative_to(REPO), "protocol must reside in the portable repository tree")
    bind(REPO/"scripts/audit_contact_c2.py", bindings, FROZEN_AUDITOR_SHA256)
    protocol = read_json(protocol_path)
    validate_protocol_v4(protocol)
    bind(protocol_path, bindings)
    bind(REPO/contract.V3_PROTOCOL_PATH, bindings, contract.V3_PROTOCOL_SHA256)
    bind(REPO/contract.C1_PROTOCOL_PATH, bindings, contract.C1_PROTOCOL_SHA256)
    bind_manifest(REPO, protocol["implementation_sha256"], bindings, "frozen v4 implementation manifest")
    gate_spec = protocol["saved_field_admission"]
    require(isinstance(gate_spec["path"], str) and "\\" not in gate_spec["path"]
            and ":" not in gate_spec["path"] and not PurePosixPath(gate_spec["path"]).is_absolute(),
            "admission path must be protocol-relative POSIX")
    gate = (protocol_path.parent/gate_spec["path"]).resolve()
    require(gate.is_relative_to(REPO.parent), "admission escapes repository/results tree")
    bind(gate, bindings, gate_spec["sha256"])
    admission = read_json(gate)
    require(admission.get("status") == "pass", "saved-field admission did not pass")
    if "input_sha256_from_workspace_root" in admission:
        bind_manifest(REPO.parent, admission["input_sha256_from_workspace_root"], bindings,
                      "saved-field admission input manifest")
    evidence = (protocol_path.parent/protocol["stable_f_evidence"]["path"]).resolve()
    require(evidence.is_relative_to(REPO.parent), "stable-F evidence escapes repository/results tree")
    bind(evidence, bindings, protocol["stable_f_evidence"]["sha256"])
    meta = read_json(run/"metadata.json")
    bind(run/"metadata.json", bindings)
    require(meta.get("schema") == contract.RUN_SCHEMA and meta.get("kind") == "TMC"
            and meta.get("mode") == "uniform" and meta.get("case_id") == contract.CASE_ID
            and meta.get("protocol") == protocol and meta.get("protocol_sha256") == sha(protocol_path)
            and meta.get("kernel") == contract.KERNEL,
            "run metadata is not bound to the frozen v4 protocol and kernel")
    sources = meta.get("source_sha256")
    require(isinstance(sources, dict) and REQUIRED_RUN_SOURCES <= set(sources), "production source manifest is incomplete")
    for name, expected in sources.items():
        bind(confined(REPO, name), bindings, expected)
    require(sha(REPO/"scripts/audit_contact_c1.py") == C1_AUDITOR_SHA256, "frozen C1 audit prototype changed")
    for name in ("audit_contact_c2_v4.py", "audit_contact_c1.py", "audit_contact_reference_a0.py",
                 "hf4_split_precision_reference.py", "hf2_precision_reference.py", "contact_c2_v4_contract.py"):
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
                entries=index["steps"], paths=paths)


def audit(run, output, protocol_path):
    run, output = Path(run).resolve(), Path(output).resolve()
    require(not output.exists(), "audit output already exists")
    detail_directory = run/("audit_states" if output.name == "audit.json" else output.stem+"_states")
    require(not detail_directory.exists(), "audit detail directory already exists")
    bindings, detail_bindings, compact_states, stages = {}, {}, [], []
    data = load_run(run, protocol_path, bindings)
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
    result = dict(schema_version=contract.AUDIT_SCHEMA, status="pass" if passed else "not_pass",
        created_utc=datetime.now(timezone.utc).isoformat(),
        run=run.relative_to(REPO.parent).as_posix() if run.is_relative_to(REPO.parent) else str(run), kind="TMC", mode="uniform",
        case_id=data["metadata"]["case_id"], case=data["metadata"]["case"], h=data["metadata"]["h"],
        kernel=data["metadata"]["kernel"], relation_to_v3=data["protocol"]["relation_to_v3"],
        measurement_precision=80, precision_digits=[80, 120], verification_precision_pair=[80, 120],
        measurement_semantics=MEASUREMENT_SEMANTICS, prefix_semantics=data["protocol"]["prefix_semantics"],
        thresholds=THRESHOLDS, source_bindings=data["metadata"]["source_sha256"],
        prototype=dict(path="hf_repo/scripts/audit_contact_c2.py", sha256=FROZEN_AUDITOR_SHA256,
            reused_functions=["audit_state", "validate_model", "load_controller", "bind_completion", "classify_prefix"],
            changes=["v4 protocol/run identity loading", "compensated-kernel production sources required"]),
        input_and_helper_sha256=portable_bindings(run, bindings), detail_output_sha256=detail_bindings,
        states=compact_states, stages=stages, prefix=prefix,
        summary=dict(accepted_states=len(compact_states), passed_states=sum(row["status"] == "pass" for row in compact_states),
                     failed_states=[row["state_id"] for row in compact_states if row["status"] != "pass"],
                     independent_checks=total_checks, independent_checks_passed=passed_checks,
                     stage_count=1, planned_stage_count=1,
                     scope="v4 kernel-repair re-test of the single fine-mesh uniform path; node reactions are not verified contact pressures"))
    output.parent.mkdir(parents=True, exist_ok=True)
    write_new(output, result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--protocol", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists; preserve prior evidence")
    try:
        result = audit(args.run, args.output, args.protocol)
    except (ValueError, KeyError, IndexError, OSError, ArithmeticError) as error:
        result = dict(schema_version=contract.AUDIT_SCHEMA, status="not_pass",
                      run=str(args.run.resolve()), error_type=type(error).__name__, error=str(error), states=[])
        if not args.output.exists():
            args.output.parent.mkdir(parents=True, exist_ok=True)
            write_new(args.output, result)
    print(json.dumps({key: result[key] for key in ("status", "summary", "error") if key in result}), flush=True)
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
