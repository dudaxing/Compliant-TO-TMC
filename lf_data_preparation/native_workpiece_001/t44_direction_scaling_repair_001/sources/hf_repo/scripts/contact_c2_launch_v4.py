"""Fail-closed launch guard for the v4 kernel-repair re-test (one path: mesh_h00625).

Standard library only. Reuses P1's generic parts (strict JSON, byte binding, path confinement, receipt
style); P1 itself is unchanged and still guards only the historical v3 contract.

Identity layering (no cycle): the v4 protocol's implementation manifest binds the runner, audit, contract
module, kernels and all mechanics they import, but NOT this guard. This guard pins the protocol's SHA-256
(set once, after the protocol is frozen); its own bytes, the isolated entry and the reused P1 module are
listed in the launch identity file (configs/contact_c2_v4_launch_identity.json, written after this constant)
and are re-checked and recorded in every launch plan and receipt. The parent validates everything before
creating a directory, writing a log or dispatching; the private child repeats the whole plan before it
imports a backend. This is an integrity and anti-misuse check, not a security boundary against someone
who can edit the code and evidence.

Stopping semantics are the v3 ones: one solve, then one independent audit only after a successful solve;
no automatic retry of a path or an audit; failed or timed-out artifacts are preserved as they are.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import runpy
import subprocess
import sys
import time

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO / "scripts"))
from contact_c2_launch_p1 import (  # noqa: E402  (P1 generic parts, reused unchanged)
    Bindings, ContractError, _digest, _number, _run_name, _timestamp, _write_new, confined, exact, require, sha,
    strict_json,
)
import contact_c2_v4_contract as contract  # noqa: E402

# Set exactly once, after configs/contact_c2_v4.json is frozen. While None the guard refuses every launch.
PROTOCOL_SHA256 = "8d2a4f718e6c36cc61d9838e0df1eba9f116ad5d7b8d4bdffbfbfd512170ba6b"
PLAN_SCHEMA = "contact_c2_launch_plan_v4"
RECEIPT_SCHEMA = "contact_c2_external_receipt_v4"
IDENTITY_SCHEMA = "contact_c2_v4_launch_identity"
IDENTITY_FILE = "configs/contact_c2_v4_launch_identity.json"
SEQUENCE = contract.SEQUENCE
LAUNCH_FILES = contract.LAUNCH_FILES
BACKENDS = {"solve": "scripts/run_contact_c2_v4.py", "audit": "scripts/audit_contact_c2_v4.py"}


def validate_protocol(protocol_path, bindings):
    """Pin all bytes before trusting any source path, numerical value or budget."""
    require(PROTOCOL_SHA256 is not None, "v4 protocol identity is not frozen in the launch guard")
    _digest(PROTOCOL_SHA256, "pinned v4 protocol SHA-256")
    protocol_path = Path(protocol_path).resolve()
    require(protocol_path.is_relative_to(REPO), "protocol must reside in this repository")
    protocol = bindings.json(protocol_path, PROTOCOL_SHA256)
    require(protocol_path == (REPO / contract.PROTOCOL_PATH).resolve(), "v4 protocol must be the frozen configs file")
    v3 = bindings.json(REPO / contract.V3_PROTOCOL_PATH, contract.V3_PROTOCOL_SHA256)
    c1 = bindings.json(REPO / contract.C1_PROTOCOL_PATH, contract.C1_PROTOCOL_SHA256)
    try:
        contract.validate_protocol(protocol, v3, c1)
    except contract.V4ContractError as error:
        raise ContractError(str(error)) from error
    budget = protocol["budget"]
    for name in ("maximum_paths", "subprocess_wall_seconds", "maximum_total_solve_seconds",
                 "maximum_audit_seconds_per_path", "maximum_total_audit_seconds"):
        _number(budget[name], "budget." + name, positive=True)
    require(budget["maximum_paths"] == len(SEQUENCE), "path cap differs")
    bindings.manifest(REPO, protocol["implementation_sha256"], "v4 implementation manifest")
    workspace = REPO.parent
    gate_spec = protocol["saved_field_admission"]
    gate = bindings.json(confined(protocol_path.parent, gate_spec["path"], limit=workspace, parents=True), gate_spec["sha256"])
    require(type(gate) is dict and gate.get("schema") == "contact_c2_saved_field_admission_v1"
            and gate.get("status") == "pass" and gate.get("valid_for_execution_admission", True) is True,
            "saved-field execution admission is absent")
    bindings.manifest(workspace, gate.get("input_sha256_from_workspace_root"), "saved-field admission input manifest")
    require(type(protocol["baseline_audits"]) is list and len(protocol["baseline_audits"]) == 2, "two baseline audits are required")
    for item in protocol["baseline_audits"]:
        baseline = bindings.json(confined(protocol_path.parent, item["path"], limit=workspace, parents=True), item["sha256"])
        require(type(baseline) is dict and baseline.get("schema_version") == "contact-c1-independent-audit-1.0"
                and baseline.get("status") == "pass", "baseline audit did not pass")
    evidence_spec = protocol["stable_f_evidence"]
    evidence = bindings.json(confined(protocol_path.parent, evidence_spec["path"], limit=workspace, parents=True),
                             evidence_spec["sha256"])
    require(type(evidence) is dict and evidence.get("schema") == evidence_spec["schema"]
            and evidence.get("saved_all_c2_and_c1", {}).get("candidate_pass") == evidence.get("saved_all_c2_and_c1", {}).get("states"),
            "stable-F no-solve evidence is absent or not all saved states passed")
    # Launch-layer identity lives outside the protocol: recorded here, compared with the identity file.
    identity = bindings.json(REPO / IDENTITY_FILE)
    require(type(identity) is dict and identity.get("schema") == IDENTITY_SCHEMA
            and identity.get("protocol_path") == contract.PROTOCOL_PATH
            and identity.get("protocol_sha256") == PROTOCOL_SHA256, "launch identity file does not name the pinned v4 protocol")
    files = identity.get("launch_files")
    require(type(files) is dict and set(files) == set(LAUNCH_FILES), "launch identity must list exactly the launch-layer files")
    for name in LAUNCH_FILES:
        bindings.file(confined(REPO, name), files[name])
    mismatches = contract.environment_mismatches(protocol["environment"])
    require(not mismatches, "interpreter differs from the locked v4 environment: " + str(mismatches))
    return protocol


def _receipt(path, action, protocol, bindings, static_bindings):
    value = bindings.json(path)
    require(type(value) is dict and value.get("schema") == RECEIPT_SCHEMA, "unsupported subprocess receipt")
    name = _run_name(value.get("run_name"))
    require(path.name == name + "." + action + ".receipt.json", "receipt filename differs from run")
    require(value.get("action") == action and value.get("case_id") in SEQUENCE, "receipt action or case differs")
    require(value.get("protocol_sha256") == PROTOCOL_SHA256, "receipt protocol identity differs")
    require(type(value.get("returncode")) is int and value["returncode"] == 0 and value.get("timed_out") is False,
            "prior subprocess failed or timed out")
    _number(value.get("elapsed_seconds"), "receipt elapsed_seconds")
    _number(value.get("timeout_seconds"), "receipt timeout_seconds", positive=True)
    cap = protocol["budget"]["subprocess_wall_seconds" if action == "solve" else "maximum_audit_seconds_per_path"]
    require(value["timeout_seconds"] <= cap, "receipt exceeds per-action wall budget")
    _digest(value.get("log_sha256"), "receipt log_sha256")
    bindings.file(path.parent / (name + "." + action + ".log"), value["log_sha256"])
    _digest(value.get("launch_plan_sha256"), "receipt launch_plan_sha256")
    old_plan = bindings.json(path.parent / (name + "." + action + ".v4-plan.json"), value["launch_plan_sha256"])
    require(type(old_plan) is dict and old_plan.get("schema") == PLAN_SCHEMA and old_plan.get("action") == action
            and old_plan.get("case_id") == value["case_id"] and old_plan.get("protocol_sha256") == PROTOCOL_SHA256
            and confined(REPO.parent, old_plan.get("run")) == (path.parent / name).resolve(),
            "receipt launch plan identity differs")
    bindings.manifest(REPO.parent, old_plan.get("input_sha256"), "prior launch plan inputs")
    require(all(old_plan["input_sha256"].get(key) == digest for key, digest in static_bindings.items()),
            "prior launch plan lacks the same complete static contract/source bindings")
    return value


def _run_metadata(run, case_id, protocol, bindings):
    metadata = bindings.json(run / "metadata.json")
    require(type(metadata) is dict and metadata.get("schema") == contract.RUN_SCHEMA
            and metadata.get("kind") == "TMC" and metadata.get("mode") == "uniform"
            and metadata.get("case_id") == case_id and metadata.get("protocol_sha256") == PROTOCOL_SHA256
            and metadata.get("kernel") == contract.KERNEL, "saved run metadata has a different identity")
    exact(metadata.get("protocol"), protocol, "saved run protocol")
    return metadata


def plan_launch(action, run, case_id, protocol_path, *, _worker=False):
    """Read-only launch planning. No mkdir, no imports of mechanics, no dispatch."""
    require(action in ("solve", "audit"), "unsupported action")
    require(case_id in SEQUENCE, "undeclared case: v4 re-tests only the frozen fine-mesh case")
    run, protocol_path = Path(run).resolve(), Path(protocol_path).resolve()
    root = run.parent
    require(root.is_relative_to(REPO.parent) and not root.is_relative_to(REPO),
            "experiment root must be in the workspace and outside hf_repo")
    _run_name(run.name)
    bindings = Bindings()
    protocol = validate_protocol(protocol_path, bindings)
    log = root / (run.name + "." + action + ".log")
    receipt = root / (run.name + "." + action + ".receipt.json")
    launch_file = root / (run.name + "." + action + ".v4-plan.json")
    require(not receipt.exists(), "refusing to overwrite a subprocess receipt")
    if _worker:
        require(log.is_file() and launch_file.is_file(), "private worker requires its parent's artifacts")
    else:
        require(not log.exists() and not launch_file.exists(), "refusing to overwrite launch evidence")
    require(not root.exists() or root.is_dir(), "experiment root is not a directory")
    static_bindings = dict(bindings.values)
    solves = [_receipt(p, "solve", protocol, bindings, static_bindings) for p in sorted(root.glob("*.solve.receipt.json"))]
    audits = [_receipt(p, "audit", protocol, bindings, static_bindings) for p in sorted(root.glob("*.audit.receipt.json"))]
    require(len(solves) <= len(SEQUENCE) and [row["case_id"] for row in solves] == SEQUENCE[:len(solves)],
            "solve history is not a contiguous frozen prefix")
    by_name = {row["run_name"]: row for row in solves}
    require(len(by_name) == len(solves), "duplicate run in solve history")
    audit_names = [row["run_name"] for row in audits]
    require(len(set(audit_names)) == len(audit_names) and set(audit_names) <= set(by_name), "duplicate or orphan audit receipt")
    expected_entries = set()
    for row in solves:
        name = row["run_name"]
        expected_entries.update({name, name + ".solve.log", name + ".solve.receipt.json", name + ".solve.v4-plan.json"})
    for row in audits:
        name = row["run_name"]
        expected_entries.update({name + ".audit.log", name + ".audit.receipt.json", name + ".audit.v4-plan.json"})
    if _worker:
        expected_entries.update({log.name, launch_file.name})
    require(not root.exists() or {p.name for p in root.iterdir()} <= expected_entries,
            "unreceipted or unrecognized evidence exists; preserve it and investigate")
    solve_elapsed = sum(row["elapsed_seconds"] for row in solves)
    audit_elapsed = sum(row["elapsed_seconds"] for row in audits)
    budget = protocol["budget"]
    if action == "solve":
        require(solve_elapsed < budget["maximum_total_solve_seconds"], "cumulative solve budget exhausted")
        require(not run.exists() and len(solves) < budget["maximum_paths"], "new path required within path cap")
        require(case_id == SEQUENCE[len(solves)], "case differs from frozen serial order")
        timeout = min(budget["subprocess_wall_seconds"], budget["maximum_total_solve_seconds"] - solve_elapsed)
    else:
        require(audit_elapsed < budget["maximum_total_audit_seconds"], "cumulative audit budget exhausted")
        require(solves and case_id == solves[-1]["case_id"] and by_name.get(run.name) is not None,
                "audit must follow the latest successful solve")
        require(run.name not in audit_names, "automatic audit retry is forbidden")
        _run_metadata(run, case_id, protocol, bindings)
        require(not (run / "audit.json").exists(), "refusing to overwrite an existing audit")
        timeout = min(budget["maximum_audit_seconds_per_path"], budget["maximum_total_audit_seconds"] - audit_elapsed)
    _number(timeout, "remaining timeout", positive=True)
    return dict(schema=PLAN_SCHEMA, scope="v4 kernel-repair re-test launch plan; not a scientific result",
                action=action, case_id=case_id, run=run.relative_to(REPO.parent).as_posix(),
                protocol_path=protocol_path.relative_to(REPO.parent).as_posix(), protocol_sha256=PROTOCOL_SHA256,
                launch_identity={name: bindings.values[(REPO / name).resolve().relative_to(REPO.parent).as_posix()]
                                 for name in LAUNCH_FILES},
                timeout_seconds=timeout, input_sha256=dict(sorted(bindings.values.items())))


def _invoke_backend(plan):
    """Private lazy boundary; unit tests replace this whole function."""
    scripts = str(REPO / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    run = confined(REPO.parent, plan["run"])
    protocol_path = confined(REPO.parent, plan["protocol_path"])
    script = REPO / BACKENDS[plan["action"]]
    if plan["action"] == "solve":
        arguments = ["--output", str(run), "--case", plan["case_id"], "--protocol", str(protocol_path)]
    else:
        arguments = ["--run", str(run), "--output", str(run / "audit.json"), "--protocol", str(protocol_path)]
    old_argv = sys.argv
    try:
        sys.argv = [str(script), *arguments]
        try:
            runpy.run_path(str(script), run_name="__main__")
        except SystemExit as error:
            return error.code
        return 0
    finally:
        sys.argv = old_argv


def worker(launch_file, expected_sha):
    """Internal child handshake; not a supported standalone execution API."""
    launch_file = Path(launch_file).resolve()
    _digest(expected_sha, "parent plan digest")
    require(sha(launch_file) == expected_sha, "parent launch plan changed")
    saved = strict_json(launch_file)
    require(type(saved) is dict and saved.get("schema") == PLAN_SCHEMA, "invalid parent plan")
    run = confined(REPO.parent, saved["run"])
    require(launch_file == run.parent / (run.name + "." + saved["action"] + ".v4-plan.json"),
            "private launch plan is in the wrong location")
    repeated = plan_launch(saved["action"], run, saved["case_id"], confined(REPO.parent, saved["protocol_path"]), _worker=True)
    exact(repeated, saved, "revalidated parent plan")
    require(sha(launch_file) == expected_sha, "parent launch plan changed during validation")
    return _invoke_backend(repeated)


def launch(action, run, case_id, protocol_path):
    """The only public execution route: validate first, then bound the child."""
    plan = plan_launch(action, run, case_id, protocol_path)
    run = confined(REPO.parent, plan["run"])
    log = run.parent / (run.name + "." + action + ".log")
    receipt = run.parent / (run.name + "." + action + ".receipt.json")
    launch_file = run.parent / (run.name + "." + action + ".v4-plan.json")
    run.parent.mkdir(parents=True, exist_ok=True)
    _write_new(launch_file, plan)
    plan_digest = sha(launch_file)
    command = [sys.executable, "-B", str(REPO / "scripts/run_contact_c2_v4_isolated.py"),
               "--_worker-plan", str(launch_file), "--_worker-sha256", plan_digest]
    environment = dict(os.environ)
    environment.update(JAX_ENABLE_X64="true", JAX_PLATFORMS="cpu", OMP_NUM_THREADS="1",
                       OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", PYTHONDONTWRITEBYTECODE="1")
    start, started, timed_out, code, failure = time.perf_counter(), _timestamp(), False, None, None
    with log.open("x", encoding="utf-8") as stream:
        try:
            done = subprocess.run(command, cwd=run.parent, env=environment, stdout=stream,
                                  stderr=subprocess.STDOUT, timeout=plan["timeout_seconds"])
            code = done.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
        except OSError as error:
            failure = dict(type=type(error).__name__, message=str(error))
    payload = dict(schema=RECEIPT_SCHEMA, action=action, case_id=case_id, run_name=run.name,
                   command=command, started_utc=started, finished_utc=_timestamp(),
                   elapsed_seconds=time.perf_counter() - start, timeout_seconds=plan["timeout_seconds"],
                   returncode=code, timed_out=timed_out, protocol_sha256=PROTOCOL_SHA256,
                   log_sha256=sha(log), launch_plan_sha256=plan_digest, launch_identity=plan["launch_identity"],
                   launch_failure=failure)
    if action == "audit" and (run / "audit.json").is_file():
        payload["audit_sha256"] = sha(run / "audit.json")
    _write_new(receipt, payload)
    return 124 if timed_out else (125 if failure else code)


def cli(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--_worker-plan", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--_worker-sha256", help=argparse.SUPPRESS)
    parser.add_argument("--action", choices=("solve", "audit"))
    parser.add_argument("--run", type=Path)
    parser.add_argument("--case", dest="case_id")
    parser.add_argument("--protocol", type=Path)
    args = parser.parse_args(argv)
    try:
        if args._worker_plan is not None or args._worker_sha256 is not None:
            require(args._worker_plan is not None and args._worker_sha256 is not None
                    and all(getattr(args, key) is None for key in ("action", "run", "case_id", "protocol")),
                    "private worker arguments cannot be mixed with public launch arguments")
            return worker(args._worker_plan, args._worker_sha256)
        require(all(getattr(args, key) is not None for key in ("action", "run", "case_id", "protocol")),
                "action/run/case/protocol are required")
        return launch(args.action, args.run, args.case_id, args.protocol)
    except (ContractError, OSError, KeyError, TypeError) as error:
        parser.error(str(error))
