"""Fail-closed launch validation for the unchanged historical C2 v3 contract.

This module is stdlib-only. A successful plan authenticates a historical
contract, not a new scientific admission or permission to run a repaired
kernel. Both public entry points use the same bounded coordinator. The private
child repeats the complete read-only plan before importing a legacy backend.
The parent plan is an integrity/checkpoint mechanism, not an access-control
boundary against a user able to alter Python code or manufacture evidence.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import time


REPO = Path(__file__).resolve().parents[1]
PROTOCOL_SHA256 = "b17c8328dd1e350563b70305c0b311c8d38c9c0ef68c08b85fac5f13604d0b4d"
C1_PROTOCOL_SHA256 = "5b30bafc226cb97038ae1b0d08e745f9f7df2a049333a8019cdf03cc48fe5308"
PLAN_SCHEMA = "contact_c2_launch_plan_p1_v1"
RECEIPT_SCHEMA = "contact_c2_external_receipt_p1_v1"
P1_FILES = ("scripts/contact_c2_launch_p1.py", "scripts/run_contact_c2_p1.py",
            "scripts/run_contact_c2_p1_isolated.py")
SEQUENCE = ["padding_2p5", "outer_free", "mesh_h00625"]


class ContractError(ValueError):
    """A launch was rejected before any execution side effect."""


def require(condition, message):
    if not condition:
        raise ContractError(message)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _pairs(pairs):
    result = {}
    for name, value in pairs:
        require(name not in result, "duplicate JSON key: " + name)
        result[name] = value
    return result


def _constant(value):
    raise ContractError("nonfinite JSON constant: " + value)


def _float(value):
    number = float(value)
    require(math.isfinite(number), "nonfinite JSON number: " + value)
    return number


def strict_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"),
                          object_pairs_hook=_pairs, parse_constant=_constant, parse_float=_float)
    except ContractError:
        raise
    except (UnicodeError, ValueError) as error:
        raise ContractError("invalid JSON: " + str(path)) from error


def exact(actual, expected, label):
    """Equality also distinguishes booleans, integer counts and float values."""
    require(type(actual) is type(expected), label + " has a different JSON type")
    if isinstance(expected, dict):
        require(set(actual) == set(expected), label + " keys differ")
        for key in expected:
            exact(actual[key], expected[key], label + "." + key)
    elif isinstance(expected, list):
        require(len(actual) == len(expected), label + " length differs")
        for i, value in enumerate(expected):
            exact(actual[i], value, label + "[" + str(i) + "]")
    else:
        require(actual == expected, label + " differs from the frozen contract")


def _digest(value, label):
    require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None,
            label + " is not a lowercase SHA-256")


def _number(value, label, positive=False):
    require(type(value) in (int, float) and (type(value) is int or math.isfinite(value))
            and (value > 0 if positive else value >= 0), label + " must be finite and nonnegative")


def confined(base, name, limit=None, parents=False):
    require(isinstance(name, str) and name and "\\" not in name and ":" not in name,
            "binding must be a relative POSIX path")
    relative = PurePosixPath(name)
    require(not relative.is_absolute() and relative.as_posix() == name,
            "binding must be canonical and relative")
    require(parents or ".." not in relative.parts, "binding contains parent traversal")
    path = (Path(base) / name).resolve()
    boundary = Path(limit if limit is not None else base).resolve()
    require(path.is_relative_to(boundary), "binding escapes its allowed tree: " + name)
    return path


class Bindings:
    def __init__(self):
        self.values = {}

    def file(self, path, expected=None):
        path = Path(path).resolve()
        if expected is not None:
            _digest(expected, "expected digest")
        digest = sha(path)
        require(expected is None or digest == expected, "file hash changed: " + str(path))
        require(path.is_relative_to(REPO.parent), "bound file is outside this workspace")
        name = path.relative_to(REPO.parent).as_posix()
        prior = self.values.get(name)
        require(prior is None or prior == digest, "file changed during validation: " + str(path))
        self.values[name] = digest
        return digest

    def json(self, path, expected=None):
        self.file(path, expected)
        value = strict_json(path)
        self.file(path, expected)
        return value

    def manifest(self, base, mapping, label, limit=None, parents=False):
        require(type(mapping) is dict and mapping, label + " must be nonempty")
        destinations = set()
        for name, digest in mapping.items():
            _digest(digest, label + " digest")
            path = confined(base, name, limit=limit, parents=parents)
            require(path not in destinations, label + " has duplicate resolved paths")
            destinations.add(path)
            self.file(path, digest)


def validate_protocol(protocol_path, bindings):
    """Pin all bytes before trusting any source path, numerical value or budget."""
    protocol_path = Path(protocol_path).resolve()
    require(protocol_path.is_relative_to(REPO), "protocol must reside in this repository")
    protocol = bindings.json(protocol_path, PROTOCOL_SHA256)
    require(type(protocol) is dict, "protocol must be an object")
    # The independently pinned reference authenticates all keys/types, including
    # explanatory semantics and source manifests, without a self-declared SHA.
    reference_path = REPO / "configs/contact_c2_v3.json"
    reference = bindings.json(reference_path, PROTOCOL_SHA256)
    exact(protocol, reference, "protocol")
    c1 = bindings.json(REPO / "configs/contact_c1_v1.json", C1_PROTOCOL_SHA256)
    for section in ("geometry", "material", "solver"):
        exact(protocol[section], c1[section], section)
    exact(protocol["schema"], "contact_c2_uniform_diagnostic_v1", "schema")
    exact(protocol["run_sequence"], SEQUENCE, "run_sequence")
    exact(protocol["audit"]["precisions"], [80, 120], "audit.precisions")
    # Hash identity already protects every field. Explicit domain checks make
    # malformed synthetic fixtures fail for the same reasons as real inputs.
    for group in ("geometry", "material", "solver", "audit", "budget"):
        for name, value in protocol[group].items():
            if isinstance(value, bool):
                raise ContractError(group + "." + name + " must not be boolean")
            if type(value) in (int, float):
                _number(value, group + "." + name, positive=True)
    for name in ("max_checks", "max_backtracks", "max_bisections"):
        require(type(protocol["solver"][name]) is int, "solver count must be an integer")
    require(type(protocol["budget"]["maximum_paths"]) is int
            and protocol["budget"]["maximum_paths"] == len(SEQUENCE), "path cap differs")
    bindings.manifest(REPO, protocol["implementation_sha256"], "implementation manifest")
    workspace = REPO.parent
    gate_spec = protocol["saved_field_admission"]
    gate_path = confined(protocol_path.parent, gate_spec["path"], limit=workspace, parents=True)
    gate = bindings.json(gate_path, gate_spec["sha256"])
    require(type(gate) is dict and gate.get("schema") == "contact_c2_saved_field_admission_v1"
            and gate.get("status") == "pass"
            and gate.get("valid_for_execution_admission", True) is True,
            "saved-field execution admission is absent")
    bindings.manifest(workspace, gate.get("input_sha256_from_workspace_root"),
                      "saved-field admission input manifest")
    require(type(protocol["baseline_audits"]) is list and len(protocol["baseline_audits"]) == 2,
            "two baseline audits are required")
    for item in protocol["baseline_audits"]:
        baseline = bindings.json(confined(protocol_path.parent, item["path"],
                                         limit=workspace, parents=True), item["sha256"])
        require(type(baseline) is dict and baseline.get("schema_version") == "contact-c1-independent-audit-1.0"
                and baseline.get("status") == "pass", "baseline audit did not pass")
    for name in P1_FILES:
        bindings.file(confined(REPO, name))
    return protocol


def _run_name(name):
    require(isinstance(name, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", name) is not None,
            "run name must be a simple filename")
    return name


def _receipt(path, action, protocol, bindings, static_bindings):
    value = bindings.json(path)
    require(type(value) is dict and value.get("schema") in
            ("contact_c2_external_receipt_v1", RECEIPT_SCHEMA), "unsupported subprocess receipt")
    name = _run_name(value.get("run_name"))
    require(path.name == name + "." + action + ".receipt.json", "receipt filename differs from run")
    require(value.get("action") == action and value.get("case_id") in SEQUENCE,
            "receipt action or case differs")
    require(value.get("protocol_sha256") == PROTOCOL_SHA256, "receipt protocol identity differs")
    require(type(value.get("returncode")) is int and value["returncode"] == 0
            and value.get("timed_out") is False, "prior subprocess failed or timed out")
    _number(value.get("elapsed_seconds"), "receipt elapsed_seconds")
    _number(value.get("timeout_seconds"), "receipt timeout_seconds", positive=True)
    cap = protocol["budget"]["subprocess_wall_seconds" if action == "solve"
                              else "maximum_audit_seconds_per_path"]
    require(value["timeout_seconds"] <= cap, "receipt exceeds per-action wall budget")
    _digest(value.get("log_sha256"), "receipt log_sha256")
    bindings.file(path.parent / (name + "." + action + ".log"), value["log_sha256"])
    if value["schema"] == RECEIPT_SCHEMA:
        _digest(value.get("launch_plan_sha256"), "receipt launch_plan_sha256")
        old_plan = bindings.json(path.parent / (name + "." + action + ".p1-plan.json"),
                                 value["launch_plan_sha256"])
        require(type(old_plan) is dict and old_plan.get("schema") == PLAN_SCHEMA and old_plan.get("action") == action
                and old_plan.get("case_id") == value["case_id"]
                and old_plan.get("protocol_sha256") == PROTOCOL_SHA256
                and confined(REPO.parent, old_plan.get("run")) == (path.parent / name).resolve(),
                "receipt launch plan identity differs")
        bindings.manifest(REPO.parent, old_plan.get("input_sha256"), "prior launch plan inputs")
        require(all(old_plan["input_sha256"].get(key) == digest for key, digest in static_bindings.items()),
                "prior launch plan lacks the same complete static contract/source bindings")
    return value


def _admitted_run(root, solve, audit, protocol, bindings):
    name, case_id = solve["run_name"], solve["case_id"]
    require(audit["run_name"] == name and audit["case_id"] == case_id,
            "prior solve and audit identities differ")
    run = (root / name).resolve()
    require(run.is_relative_to(root), "run directory escapes its experiment root")
    _run_metadata(run, case_id, protocol, bindings)
    _digest(audit.get("audit_sha256"), "receipt audit_sha256")
    saved = bindings.json(run / "audit.json", audit["audit_sha256"])
    require(type(saved) is dict and saved.get("schema_version") == "contact-c2-independent-audit-1.0"
            and saved.get("status") == "pass" and saved.get("case_id") == case_id,
            "prior path was not independently admitted")
    bindings.manifest(run, saved.get("input_and_helper_sha256"), "previous audit inputs",
                      limit=REPO.parent, parents=True)
    bindings.manifest(run, saved.get("detail_output_sha256"), "previous audit details")


def _run_metadata(run, case_id, protocol, bindings):
    metadata = bindings.json(run / "metadata.json")
    require(type(metadata) is dict and metadata.get("schema") == "contact_c2_run_v1"
            and metadata.get("kind") == "TMC" and metadata.get("mode") == "uniform"
            and metadata.get("case_id") == case_id
            and metadata.get("protocol_sha256") == PROTOCOL_SHA256,
            "saved run metadata has a different identity")
    exact(metadata.get("protocol"), protocol, "saved run protocol")
    return metadata


def plan_launch(action, run, case_id, protocol_path, *, _worker=False):
    """Read-only launch planning. No mkdir, imports of mechanics, or dispatch."""
    require(action in ("solve", "audit"), "unsupported action")
    require(case_id in SEQUENCE, "undeclared case; baseline is preflight only")
    run, protocol_path = Path(run).resolve(), Path(protocol_path).resolve()
    root = run.parent
    require(root.is_relative_to(REPO.parent) and not root.is_relative_to(REPO),
            "experiment root must be in the workspace and outside hf_repo")
    _run_name(run.name)
    bindings = Bindings()
    protocol = validate_protocol(protocol_path, bindings)
    log = root / (run.name + "." + action + ".log")
    receipt = root / (run.name + "." + action + ".receipt.json")
    launch_file = root / (run.name + "." + action + ".p1-plan.json")
    require(not receipt.exists(), "refusing to overwrite a subprocess receipt")
    if _worker:
        require(log.is_file() and launch_file.is_file(), "private worker requires its parent's artifacts")
    else:
        require(not log.exists() and not launch_file.exists(), "refusing to overwrite launch evidence")
    require(not root.exists() or root.is_dir(), "experiment root is not a directory")
    static_bindings = dict(bindings.values)
    solves = [_receipt(p, "solve", protocol, bindings, static_bindings)
              for p in sorted(root.glob("*.solve.receipt.json"))]
    audits = [_receipt(p, "audit", protocol, bindings, static_bindings)
              for p in sorted(root.glob("*.audit.receipt.json"))]
    by_case, by_name = {}, {}
    for row in solves:
        require(row["case_id"] not in by_case and row["run_name"] not in by_name,
                "duplicate case or run in solve history")
        by_case[row["case_id"]], by_name[row["run_name"]] = row, row
    require(set(by_case) == set(SEQUENCE[:len(solves)]) and len(solves) <= len(SEQUENCE),
            "solve history is not a contiguous frozen prefix")
    audit_by_name = {}
    for row in audits:
        require(row["run_name"] not in audit_by_name and row["run_name"] in by_name,
                "duplicate or orphan audit receipt")
        audit_by_name[row["run_name"]] = row
    expected_entries = set()
    for row in solves:
        name = row["run_name"]
        expected_entries.update({name, name + ".solve.log", name + ".solve.receipt.json"})
        if row["schema"] == RECEIPT_SCHEMA:
            expected_entries.add(name + ".solve.p1-plan.json")
    for row in audits:
        name = row["run_name"]
        expected_entries.update({name + ".audit.log", name + ".audit.receipt.json"})
        if row["schema"] == RECEIPT_SCHEMA:
            expected_entries.add(name + ".audit.p1-plan.json")
    if _worker:
        expected_entries.update({log.name, launch_file.name})
    require(not root.exists() or {p.name for p in root.iterdir()} <= expected_entries,
            "unreceipted or unrecognized evidence exists; preserve it and investigate")
    solve_elapsed = sum(row["elapsed_seconds"] for row in solves)
    audit_elapsed = sum(row["elapsed_seconds"] for row in audits)
    budget = protocol["budget"]
    if action == "solve":
        require(solve_elapsed < budget["maximum_total_solve_seconds"], "cumulative solve budget exhausted")
        require(audit_elapsed < budget["maximum_total_audit_seconds"], "cumulative audit budget exhausted")
        require(not run.exists() and len(solves) < budget["maximum_paths"], "new path required within path cap")
        require(case_id == SEQUENCE[len(solves)], "case differs from frozen serial order")
        require(set(audit_by_name) == set(by_name), "every prior solve requires a successful audit")
        for row in solves:
            _admitted_run(root, row, audit_by_name[row["run_name"]], protocol, bindings)
        timeout = min(budget["subprocess_wall_seconds"], budget["maximum_total_solve_seconds"] - solve_elapsed)
    else:
        require(audit_elapsed < budget["maximum_total_audit_seconds"], "cumulative audit budget exhausted")
        require(solves and case_id == SEQUENCE[len(solves) - 1]
                and case_id in by_case and by_case[case_id]["run_name"] == run.name,
                "audit must follow the latest successful solve")
        require(run.name not in audit_by_name, "automatic audit retry is forbidden")
        require(set(audit_by_name) == set(by_name) - {run.name}, "earlier solve lacks an admitted audit")
        for row in solves:
            if row["run_name"] != run.name:
                _admitted_run(root, row, audit_by_name[row["run_name"]], protocol, bindings)
        _run_metadata(run, case_id, protocol, bindings)
        require(not (run / "audit.json").exists(), "refusing to overwrite an existing audit")
        timeout = min(budget["maximum_audit_seconds_per_path"], budget["maximum_total_audit_seconds"] - audit_elapsed)
    _number(timeout, "remaining timeout", positive=True)
    return dict(schema=PLAN_SCHEMA, scope="historical v3 contract validation; not a new scientific admission",
                action=action, case_id=case_id, run=run.relative_to(REPO.parent).as_posix(),
                protocol_path=protocol_path.relative_to(REPO.parent).as_posix(),
                protocol_sha256=PROTOCOL_SHA256, timeout_seconds=timeout,
                input_sha256=dict(sorted(bindings.values.items())))


def _write_new(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def _timestamp():
    return datetime.now(timezone.utc).isoformat()


def _invoke_backend(plan):
    """Private lazy boundary; unit tests replace this whole function."""
    scripts = str(REPO / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    run = confined(REPO.parent, plan["run"])
    protocol_path = confined(REPO.parent, plan["protocol_path"])
    # The original CLI retains its exception.json and exit-code behavior.
    import runpy
    old_argv = sys.argv
    try:
        if plan["action"] == "solve":
            script = REPO / "scripts/run_contact_c2.py"
            sys.argv = [str(script), "--output", str(run), "--case", plan["case_id"],
                        "--protocol", str(protocol_path)]
        else:
            script = REPO / "scripts/audit_contact_c2.py"
            sys.argv = [str(script), "--run", str(run), "--output", str(run / "audit.json"),
                        "--protocol", str(protocol_path)]
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
    require(launch_file == run.parent / (run.name + "." + saved["action"] + ".p1-plan.json"),
            "private launch plan is in the wrong location")
    repeated = plan_launch(saved["action"], run, saved["case_id"],
                           confined(REPO.parent, saved["protocol_path"]), _worker=True)
    exact(repeated, saved, "revalidated parent plan")
    require(sha(launch_file) == expected_sha, "parent launch plan changed during validation")
    return _invoke_backend(repeated)


def launch(action, run, case_id, protocol_path):
    """The only public execution route: validate first, then bound the child."""
    plan = plan_launch(action, run, case_id, protocol_path)
    run = confined(REPO.parent, plan["run"])
    log = run.parent / (run.name + "." + action + ".log")
    receipt = run.parent / (run.name + "." + action + ".receipt.json")
    launch_file = run.parent / (run.name + "." + action + ".p1-plan.json")
    run.parent.mkdir(parents=True, exist_ok=True)
    _write_new(launch_file, plan)
    plan_digest = sha(launch_file)
    command = [sys.executable, "-B", str(REPO / "scripts/run_contact_c2_p1_isolated.py"),
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
                   log_sha256=sha(log), launch_plan_sha256=plan_digest, launch_failure=failure)
    if action == "audit" and (run / "audit.json").is_file():
        payload["audit_sha256"] = sha(run / "audit.json")
    _write_new(receipt, payload)
    return 124 if timed_out else (125 if failure else code)


def cli(argv=None, *, direct=False):
    parser = argparse.ArgumentParser(description=__doc__)
    if not direct:
        parser.add_argument("--_worker-plan", type=Path, help=argparse.SUPPRESS)
        parser.add_argument("--_worker-sha256", help=argparse.SUPPRESS)
    parser.add_argument("--action", choices=("solve", "audit"), default="solve" if direct else None)
    parser.add_argument("--output" if direct else "--run", dest="run", type=Path)
    parser.add_argument("--case", dest="case_id")
    parser.add_argument("--protocol", type=Path)
    args = parser.parse_args(argv)
    try:
        if not direct and (args._worker_plan is not None or args._worker_sha256 is not None):
            require(args._worker_plan is not None and args._worker_sha256 is not None
                    and all(getattr(args, key) is None for key in ("action", "run", "case_id", "protocol")),
                    "private worker arguments cannot be mixed with public launch arguments")
            return worker(args._worker_plan, args._worker_sha256)
        require(all(getattr(args, key) is not None for key in ("action", "run", "case_id", "protocol")),
                "action/run/case/protocol are required")
        return launch(args.action, args.run, args.case_id, args.protocol)
    except (ContractError, OSError, KeyError, TypeError) as error:
        parser.error(str(error))
