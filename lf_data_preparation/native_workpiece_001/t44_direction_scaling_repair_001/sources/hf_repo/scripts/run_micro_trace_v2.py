"""F-TRACE2: one 180-second unchanged micrograph observation window.

The parent owns budgets, fixed SUP1/SUP2 cleanup and saved-source bindings.
Importing this file exposes standard-library classification functions only;
main is the sole campaign entry and never runs during authoring or controls.
"""
from __future__ import annotations

import time

_ENTRY_START = time.monotonic()

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
import ntpath
import os
from pathlib import Path
import stat
import sys
import traceback

PROTOCOL = "F-TRACE2"
RUN_ID = "micro_trace_002"
SUBJECT = "micro_native_observation"
SUCCESS = "runtime_native_trace_observed"
CARD = "docs/HF4_C2_S0_PREPARATION_RESULT_20260928.md"
DRIVER = "run_micro_trace_v2.py"
PROBE = "probe_micro_trace_v2.py"
EVIDENCE = "micro_trace_v2_evidence.py"
DOCS = ("docs/CURRENT_STATUS.md", CARD)
LIMITS = {"P0": 25., "P1": 105., "P3": 25., "shared": 25.}
SECONDS = 180.
RSS_LIMIT = 8 * 1024**3
GUARD = 5.25
SUP1_SHA = "9f3da2f22bec869d069278058aa8502bd5f73c4b977b01ec5daa7b26ff1aec32"
SUP2_SHA = "b5f149e1cd3d6d9b4ad392123e410b786606f120f2e078139b7bacc97f2d9499"
PROOF_SHA = "2d378c64705461d58fa966528a347b6e411431402877663fd546f3fec8912f45"
PRIOR_BINDING_SHA = "ea89c28be4d1acfff1a11fba8f1a51b139cf6625101f5df98e5951eec8d53cf7"
PATH_BINDING_SHA = "71f85687db21f5d4ce4f1b7aecf2013e3492ddf187d1591f55398e3e04e706e3"
HELPERS = ("windows_owned_process.py", "windows_owned_process_sup2.py",
    "cpu_supervision_evidence.py", "probe_s0_preparation.py",
    "s0_preparation_evidence.py", "s0_event_log.py", "s0_ad_exception.py",
    "force_cost_evidence.py", "micro_trace_evidence.py")
EXCLUSIONS = ("output_sha256.json", "receipt_binding.json", "execution_receipt.json",
    "ledger.json", "events/P3_seal.ndjson", "logs/P3_seal.log")
EXPECTED_COUNTS = dict(graph_count=1, trace=1, lower=1, compile=1, compiled_call=2,
    output_synchronization=2, ready_only=1, input_ready=1, micro_leaf_count=24,
    profiler_start=1, profiler_stop=1, annotations=5,
    warmup=0, retries=0, force_calls=0, ad_calls=0)
ACTUAL_COUNTS = dict(EXPECTED_COUNTS)
STAGES = ("trace_controls", "source_binding", "environment_snapshot", "runtime_import",
    "kernel_import", "harness_import", "input_prepare", "input_ready",
    "micro.trace", "micro.export_jaxpr", "micro.lower", "micro.export_stablehlo",
    "micro.compile", "micro.export_optimized_hlo", "profiler_binding", "profiler.start",
    "micro_first.call", "micro_first.synchronize", "micro_first.ready_only",
    "micro_first.transfer", "micro_first.save_output", "micro_first.compare",
    "micro_repeat.call", "micro_repeat.synchronize", "micro_repeat.transfer",
    "micro_repeat.save_output", "micro_repeat.compare", "profiler.stop",
    "native.collect", "native.analyze", "source_preservation")
ARTIFACTS = {"trace_controls.json", "environment.json", "runtime_config.json",
    "native_inventory.json", "native_analysis.json", "micro_first.npz", "micro_repeat.npz",
    "micro_raw_jaxpr.txt", "micro_stablehlo.mlir", "micro_optimized_hlo.txt"}
TARGETS = ("plan.json", "input_manifest.json", "selected_source.json", "R1/source_manifest.json",
    "HR1/manifest.json", "H1/manifest.json", "inheritance_manifest.json", "loaded_supervisors.json",
    "resources.json", "execution_receipt.json", "output_sha256.json", "results/prepare/summary.json",
    "results/trace/summary.json", "results/trace/trace_controls.json", "results/trace/environment.json",
    "results/trace/runtime_config.json", "results/trace/micro_raw_jaxpr.txt",
    "results/trace/micro_stablehlo.mlir", "results/trace/micro_optimized_hlo.txt",
    "results/trace/micro_first.npz", "results/trace/micro_repeat.npz",
    "results/trace/native_inventory.json", "results/trace/native_analysis.json",
    "results/P1_supervision/request.json", "results/P1_supervision/receipt.json",
    "results/P1_supervision/instances.ndjson", "events/P1_trace_cpu.ndjson", "events/P1_trace.ndjson",
    "supervision_proof.json", "cpu_observation.json", "artifact_status.json",
    "diagnostic_verification.json", "numerical_verification.json", "source_preservation.json", "native_manifest.json",
    "trace_analysis.json", "hlo_mapping.json", "results/seal/summary.json",
    "stages.svg", "resources.svg", "coverage.svg", "events/P3_seal.ndjson", "logs/P3_seal.log")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def extended(value):
    normalized = ntpath.normpath(os.fspath(value)) if os.name == "nt" else str(Path(value).resolve())
    if os.name == "nt" and not normalized.startswith("\\\\?\\"):
        normalized = "\\\\?\\UNC\\" + normalized[2:] if normalized.startswith("\\\\") else "\\\\?\\" + normalized
    return Path(normalized)


def no_reparse(filename):
    info = Path(filename).lstat()
    require(not stat.S_ISLNK(info.st_mode)
            and not getattr(info, "st_file_attributes", 0) & 0x400,
            "reparse/symlink source refused: " + str(filename))
    return info


def sha(filename, deadline=None):
    no_reparse(filename)
    value = hashlib.sha256()
    with Path(filename).open("rb") as stream:
        while True:
            if deadline is not None:
                require(time.monotonic() < deadline, "source/binding deadline exhausted")
            chunk = stream.read(1024**2)
            if not chunk:
                break
            value.update(chunk)
    return value.hexdigest()


def checked(filename, expected, size=None, deadline=None):
    require(Path(filename).is_file(), "missing pinned file: " + str(filename))
    if size is not None:
        require(no_reparse(filename).st_size == size, "pinned file size changed: " + str(filename))
    require(sha(filename, deadline) == expected, "pinned file changed: " + str(filename))


def read(filename):
    def invalid(value):
        raise ValueError("nonfinite JSON token refused: " + value)
    return json.loads(Path(filename).read_text(encoding="utf-8"), parse_constant=invalid)


def dump(filename, value):
    filename = Path(filename)
    filename.parent.mkdir(parents=True, exist_ok=True)
    with filename.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def replace(filename, value):
    pending = Path(filename).with_suffix(".pending.json")
    dump(pending, value)
    os.replace(pending, filename)


def utc():
    return datetime.now(timezone.utc).isoformat()


def failure(error):
    return dict(type=type(error).__name__, module=type(error).__module__,
                message=str(error), traceback=traceback.format_exc())


def complete_error(value):
    return (isinstance(value, dict)
            and all(isinstance(value.get(key), str) for key in ("type", "module", "message", "traceback")))


def write_receipt(filename, value, *, replace_existing=False):
    """Bind the exact successfully written small receipt without a late rehash.

    This is final consistency bookkeeping only. It does not grant an expired
    campaign further execution time or permit a phase, payload hash or retry.
    """
    filename = Path(filename)
    data = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+"\n").encode("utf-8")
    target = filename.with_suffix(".pending.json") if replace_existing else filename
    with target.open("xb") as stream:
        require(stream.write(data) == len(data), "short final receipt write")
        stream.flush()
        os.fsync(stream.fileno())
    if replace_existing:
        os.replace(target, filename)
    return dict(path=filename.name, bytes=len(data), sha256=hashlib.sha256(data).hexdigest())


def exact_counts(actual, expected):
    return (isinstance(actual, dict) and set(actual) == set(expected)
            and all(type(actual[key]) is int and actual[key] == value for key,value in expected.items()))


def complete_payload(summary):
    """Saved complete original micro contract; scientific qualification stays false."""
    if not exact_counts(summary.get("completed_counts"), ACTUAL_COUNTS):
        return False
    steps = summary.get("steps")
    if (not isinstance(steps, list) or len(steps) != len(STAGES)
            or any(not isinstance(row, dict) for row in steps)
            or [row.get("stage") for row in steps] != list(STAGES)
            or any(row.get("status") != "pass" for row in steps)):
        return False
    artifacts = summary.get("artifacts")
    if (not isinstance(artifacts, dict) or set(artifacts) != ARTIFACTS
            or any(not isinstance(row, dict) or row.get("status") != "complete" for row in artifacts.values())):
        return False
    comparisons = summary.get("comparisons")
    if not isinstance(comparisons, dict) or list(comparisons) != ["micro_first", "micro_repeat"]:
        return False
    for comparison in comparisons.values():
        if not isinstance(comparison, dict) or comparison.get("status") != "pass" or type(comparison.get("field_count")) is not int or comparison["field_count"] != 24:
            return False
        fields = comparison.get("fields")
        if (not isinstance(fields, dict) or len(fields) != 24
                or any(not isinstance(row, dict) or row.get("status") != "pass" or row.get("signed_zero_checked") is not True for row in fields.values())):
            return False
        kinds = [row.get("dtype") for row in fields.values()]
        if kinds.count("float64") != 18 or kinds.count("bool") != 6:
            return False
    control_table, inventory = summary.get("trace_controls"), summary.get("native_inventory")
    if not isinstance(control_table, dict) or not isinstance(inventory, dict):
        return False
    controls, inventory_result = control_table.get("result"), inventory.get("result")
    return (summary.get("numerical_contract_pass") is True
            and isinstance(controls, dict) and controls.get("status") == "pass"
            and type(controls.get("count")) is int and controls["count"] == 16
            and controls.get("synthetic") is True
            and isinstance(inventory_result, dict) and inventory_result.get("status") == "complete")


def valid_summary(summary, expected):
    """Pure stdlib; used unchanged by saved synthetic controls and real parent."""
    if not isinstance(summary, dict) or not isinstance(expected, dict):
        return False
    if (summary.get("schema") != "hf-micro-trace-probe-1"
            or summary.get("protocol") != PROTOCOL or summary.get("campaign_protocol") != PROTOCOL
            or summary.get("run_id") != RUN_ID or summary.get("subject") != SUBJECT
            or summary.get("identity") != expected
            or summary.get("phase") != "P1_trace" or summary.get("source_version") != "R1"
            or summary.get("source_manifest_sha256") != expected.get("source_manifest_sha256")
            or summary.get("scientific_admission") is not False or summary.get("force_executed") is not False
            or summary.get("expected_stages") != list(STAGES)
            or not exact_counts(summary.get("execution_contract"), EXPECTED_COUNTS)):
        return False
    life = summary.get("profiler")
    if not isinstance(life, dict):
        return False
    start_count, body_count, stop_count = (life.get(key) for key in ("start_attempts", "body_attempts", "stop_attempts"))
    start, body, stop = (life.get(key) for key in ("start_returned", "body_returned", "stop_returned"))
    if (any(type(value) is not int or value not in (0, 1) for value in (start_count, body_count, stop_count))
            or any(not isinstance(value, bool) for value in (start, body, stop))):
        return False
    # Check SUCCESS first: no partial lifecycle can be admitted by failure branches.
    if summary.get("status") == SUCCESS:
        analysis = summary.get("native_analysis")
        if not isinstance(analysis, dict) or not isinstance(analysis.get("result"), dict):
            return False
        return (start_count == body_count == stop_count == 1 and start and body and stop
                and all(life.get(key) is None for key in ("first_error", "shutdown_error", "native_start_error", "native_stop_error", "start_error", "body_error", "stop_error", "pre_body_error"))
                and life.get("shutdown_errors") == [] and summary.get("first_error") is None
                and summary.get("errors") == []
                and summary.get("first_error_kind") is None and summary.get("secondary_record_errors") == []
                and life.get("requested_options") is None
                and life.get("create_perfetto_link") is False and life.get("create_perfetto_trace") is False
                and life.get("log_dir") == "native"
                and summary.get("runtime_native_trace_observed") is True
                and analysis["result"].get("status") == SUCCESS
                and complete_payload(summary))
    if summary.get("runtime_native_trace_observed") is not False:
        return False
    first, errors = summary.get("first_error"), summary.get("errors")
    if (not complete_error(first) or not isinstance(errors, list) or not errors
            or first not in errors or any(not complete_error(error) for error in errors)):
        return False
    for key in ("first_error", "shutdown_error", "native_start_error", "native_stop_error",
                "start_error", "body_error", "stop_error", "pre_body_error"):
        if life.get(key) is not None and not complete_error(life[key]):
            return False
    if life.get("first_error") is not None and life.get("first_error") != first:
        return False
    if start_count == 0:
        return (body_count == stop_count == 0 and not start and not body and not stop
                and all(life.get(key) is None for key in ("native_start_error", "native_stop_error",
                    "start_error", "body_error", "stop_error", "pre_body_error")))
    if not start:
        return (body_count == stop_count == 0 and not body and not stop
                and complete_error(life.get("native_start_error"))
                and life.get("native_start_error") == life.get("start_error")
                and life.get("native_stop_error") is None
                and first == life.get("start_error")
                and life.get("first_error") == first)
    if stop_count != 1 or life.get("native_start_error") is not None or life.get("start_error") is not None:
        return False
    if body_count == 0:
        if body or life.get("body_error") is not None or not isinstance(life.get("pre_body_error"), dict):
            return False
        if first != life.get("pre_body_error") or life.get("first_error") != first:
            return False
    elif body != (life.get("body_error") is None):
        return False
    elif not body and (first != life.get("body_error") or life.get("first_error") != first):
        return False
    if not stop:
        stop_error = life.get("stop_error")
        if (not complete_error(stop_error) or stop_error != life.get("shutdown_error")
                or life.get("native_stop_error") != stop_error):
            return False
        # Earlier body/pre-body failure remains primary; an independent native
        # shutdown failure is secondary. A sole shutdown failure is the first.
        return not body or first == stop_error
    return (life.get("native_stop_error") is None and life.get("stop_error") is None
            and life.get("shutdown_error") is None)


def classify(raw, summary, expected, *, source_ok, proof_ok, resource_ok=True):
    """The only phase classifier: raw nonzero never grants observed success."""
    raw = raw if isinstance(raw, dict) else {}
    outcome = dict(status="execution_failure", passed=False, raw_reason=raw.get("reason"),
        raw_returncode=raw.get("returncode"), first_error=summary.get("first_error") if isinstance(summary, dict) else None,
        first_error_kind=summary.get("first_error_kind") if isinstance(summary, dict) else None,
        probe_status=summary.get("status") if isinstance(summary, dict) else None)
    cleanup = raw.get("cleanup_proof")
    if (raw.get("cleanup_verified") is not True or not isinstance(cleanup, dict)
            or cleanup.get("pass") is not True or not proof_ok):
        outcome["status"] = "cleanup_not_pass"
    elif (raw.get("reason") == "supervision_error" or raw.get("errors") or raw.get("supervision_error")
            or raw.get("telemetry_status") != "complete" or raw.get("telemetry_first_error") is not None):
        outcome["status"] = "supervision_not_pass"
    elif not resource_ok or raw.get("reason") in ("global_deadline", "phase_timeout", "rss_limit"):
        outcome["status"] = "resource_stop"
    elif (not source_ok or raw.get("protocol") != "F-CPU-CLEAN1"
            or raw.get("cleanup_contract") != "CPU-CLEAN1"):
        outcome["status"] = "source_or_identity_not_pass"
    elif (not isinstance(expected, dict) or raw.get("candidate_supervisor") != expected.get("candidate_supervisor")
            or raw.get("supervisor_sha256") != SUP2_SHA or not valid_summary(summary, expected)):
        pass
    elif (raw.get("reason") == "normal_exit" and type(raw.get("returncode")) is int
            and raw["returncode"] == 0 and summary["status"] == SUCCESS):
        outcome.update(status=SUCCESS, passed=True)
    elif (raw.get("reason") == "nonzero_exit" and type(raw.get("returncode")) is int
            and raw["returncode"] != 0 and summary["status"] == "observability_not_pass"
            and summary.get("first_error_kind") in ("native_interface", "observability")):
        # Fully preserved native/observation failure is not a resource label.
        outcome["status"] = "observability_not_pass"
    return outcome


def load_module(name, filename, expected):
    require(name not in sys.modules and sys.dont_write_bytecode, "module already loaded or bytecode enabled: " + name)
    checked(filename, expected)
    spec = importlib.util.spec_from_file_location(name, filename)
    require(spec is not None and spec.loader is not None, "cannot load pinned module: " + name)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    require(extended(module.__file__) == extended(filename), "actual module loaded from another location: " + name)
    checked(module.__file__, expected)
    return module


class StopCampaign(RuntimeError):
    def __init__(self, status, detail):
        super().__init__(detail)
        self.status = status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    require(os.name == "nt", "authorized card requires the fixed Windows environment")
    plain_repo, plain_root = ntpath.normpath(os.fspath(args.repo)), ntpath.normpath(os.fspath(args.root))
    for value in (plain_repo, plain_root):
        drive, tail = ntpath.splitdrive(value)
        require(len(drive) == 2 and drive[1] == ":" and tail.startswith("\\")
                and not value.startswith("\\\\"), "parent needs an ordinary drive-absolute path")
    repo, root = extended(plain_repo), extended(plain_root)
    require(root == repo/"hf4_c2_stable_f_validation"/RUN_ID and not root.exists(),
            "refuse another, existing, or reset campaign root")
    require(extended(__file__) == repo/"hf_repo/scripts"/DRIVER, "driver from another repository")
    require(root != repo and not repo.is_relative_to(root), "evidence root cannot contain repository")
    old = repo/"hf4_c2_stable_f_validation/micro_trace_001"
    old_path = repo/"hf4_c2_stable_f_validation/native_path_001"
    checked(old/"receipt_binding.json", PRIOR_BINDING_SHA)
    old_binding = read(old/"receipt_binding.json")
    require(old_binding.get("protocol") == "F-TRACE1" and old_binding.get("run_id") == "micro_trace_001", "F-TRACE1 old identity differs")
    pinned_manifest = old_binding["records"]["input_manifest.json"]
    checked(old/"input_manifest.json", pinned_manifest["sha256"], pinned_manifest["bytes"])
    prior = read(old/"input_manifest.json")
    checked(old_path/"receipt_binding.json", PATH_BINDING_SHA)
    path_binding = read(old_path/"receipt_binding.json")
    require(path_binding.get("protocol") == "F-PATH1" and path_binding.get("status") == "native_path_interface_pass", "F-PATH1 old identity differs")
    indexed = {row["path"]:row for row in prior["files"]}
    helper_hashes = {name:indexed["aux/hf_repo/scripts/"+name]["sha256"] for name in HELPERS}
    for name in HELPERS:
        checked(repo/"hf_repo/scripts"/name, helper_hashes[name])
    require(helper_hashes[HELPERS[0]] == SUP1_SHA and helper_hashes[HELPERS[1]] == SUP2_SHA
            and helper_hashes[HELPERS[2]] == PROOF_SHA, "fixed supervisors or proof helper differ")
    # Pin every carried installed runtime source before SUP1 can import psutil.
    require(len(prior["runtime_files"]) == 20, "fixed runtime set differs")
    for row in prior["runtime_files"]:
        checked(extended(row["path"]), row["sha256"], row["bytes"])
    for row in prior["installed_binary_checks"]:
        checked(extended(row["path"]), row["sha256"], row["bytes"])
    supervisor = load_module("_ftrace2_sup1", repo/"hf_repo/scripts/windows_owned_process.py", SUP1_SHA)
    runtime_index = {extended(row["path"]):row for row in prior["runtime_files"]}
    for name in ("psutil", "psutil._pswindows", "psutil._psutil_windows", "subprocess"):
        module = sys.modules.get(name)
        require(module is not None and getattr(module, "__file__", None), "expected SUP1 imported runtime absent: " + name)
        actual = extended(module.__file__)
        require(actual in runtime_index, "actual SUP1 imported runtime outside pins: " + name)
        checked(actual, runtime_index[actual]["sha256"], runtime_index[actual]["bytes"])
    start, deadline = _ENTRY_START, _ENTRY_START+SECONDS
    author = {name:sha(repo/name) for name in ("hf_repo/scripts/"+DRIVER,
              "hf_repo/scripts/"+PROBE, "hf_repo/scripts/"+EVIDENCE, *DOCS)}
    require(time.monotonic() < deadline-35.25, "entry preflight consumed permitted window")
    root.mkdir(parents=True)
    for name in ("events", "logs", "results"):
        (root/name).mkdir()
    source, aux = root/"R1/source/hf_repo", root/"aux/hf_repo/scripts"
    parent_identity = dict(version="SUP1", path=str(aux/HELPERS[0]), sha256=SUP1_SHA)
    candidate_identity = dict(version="SUP2", path=str(aux/HELPERS[1]), sha256=SUP2_SHA)
    loaded_parent = dict(version="SUP1", path=str(extended(supervisor.__file__)), sha256=SUP1_SHA)
    phases, attempted = [], set()
    status, error, uncertain = "running", None, False
    candidate = reader = None
    manifest_hash = harness_hash = None
    ledger = dict(schema="hf-micro-trace-campaign-1", protocol=PROTOCOL, campaign_protocol=PROTOCOL,
        run_id=RUN_ID, subject=SUBJECT, status=status, started_utc=utc(), start_monotonic=start,
        deadline_monotonic=deadline, seconds=SECONDS, rss_limit_bytes=RSS_LIMIT,
        limits_seconds=LIMITS, cleanup_and_poll_guard_seconds=GUARD,
        final_binding_reserved_seconds=5., phases=phases, scientific_admission=False, force_executed=False,
        runtime_native_trace_observed=False,
        parent_supervisor=parent_identity, candidate_supervisor=candidate_identity,
        loaded_parent_supervisor=loaded_parent, loaded_candidate_supervisor=None,
        P1_status="not_reached", supervision_proof_status="not_reached", trace_session=None,
        force_calls=0, ad_calls=0, new_equilibrium_paths=0, new_hp_evaluations=0,
        new_patch_applications=0, execution_contract=EXPECTED_COUNTS, first_stop=None)
    dump(root/"plan.json", dict(ledger, repo=str(repo), plain_repo=plain_repo, plain_root=plain_root,
        python=sys.version, card_sha256=author[CARD], runner_sha256=author["hf_repo/scripts/"+DRIVER],
        author_sha256=author, helper_sha256=helper_hashes, evidence_worker_sha256=author["hf_repo/scripts/"+EVIDENCE],
        evidence_worker_dependency_sha256=helper_hashes,
        prior_campaign="micro_trace_001", prior_binding_sha256=PRIOR_BINDING_SHA,
        path_campaign="native_path_001", path_binding_sha256=PATH_BINDING_SHA,
        science_version="R1", harness_version="HR1", arithmetic_harness_version="H1",
        supervisor_sha256=SUP2_SHA, supervisor_sha256_role="P1_candidate",
        telemetry_interval_seconds=1., telemetry_scope="owned Job CPU; parent CPU excluded",
        original_tests_rerun=False, non_seal_active_deadline=deadline-35.25,
        seal_active_deadline=deadline-10.25, output_manifest_exclusions=list(EXCLUSIONS)))
    plan_hash = sha(root/"plan.json")
    dump(root/"ledger.json", ledger)
    env = os.environ.copy()
    env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONUNBUFFERED="1", PYTHONNOUSERSITE="1",
        PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", JAX_ENABLE_X64="true", JAX_TRACEBACK_FILTERING="off",
        JAX_ENABLE_COMPILATION_CACHE="false", JAX_PLATFORMS="cpu", OMP_NUM_THREADS="1",
        OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", MPLBACKEND="Agg",
        MPLCONFIGDIR=str(root/"matplotlib-cache"))

    def shared():
        return time.monotonic()-start-sum(row["elapsed_seconds"] for row in phases)

    def save_ledger():
        ledger.update(status=status, error=error, elapsed_seconds=time.monotonic()-start,
            shared_elapsed_seconds=shared(), supervision_uncertain=uncertain,
            runtime_native_trace_observed=status == SUCCESS,
            consumed_phase_seconds={key:sum(row["elapsed_seconds"] for row in phases if row["bucket"] == key)
                                    for key in ("P0", "P1", "P3")})
        replace(root/"ledger.json", ledger)

    def worker_command(action):
        filename = aux/EVIDENCE if action == "seal" else repo/"hf_repo/scripts"/EVIDENCE
        def matches(path):
            return (path.is_file() and sha(path) == author["hf_repo/scripts/"+EVIDENCE]
                    and all((path.parent/name).is_file() and sha(path.parent/name) == digest
                            for name,digest in helper_hashes.items()))
        if not matches(filename):
            if action != "seal" or not matches(repo/"hf_repo/scripts"/EVIDENCE):
                raise StopCampaign("source_or_identity_not_pass", "Evidence worker or pinned dependencies changed")
            # A partial P0 copied file is not a worker; select one whole pinned
            # canonical worker before the sole P3 launch. Never retry a child.
            filename = repo/"hf_repo/scripts"/EVIDENCE
        return filename, [sys.executable, "-u", "-B", str(filename), "--root", str(root),
                          "--repo", str(repo), "--action", action]

    def execute(name, bucket, command, worker):
        nonlocal uncertain
        if name in attempted:
            raise StopCampaign("execution_failure", "A phase cannot run twice: " + name)
        if shared() > 20.:
            raise StopCampaign("resource_stop", "Preseal shared allowance exhausted")
        begin = time.monotonic()
        active_seconds = LIMITS[bucket]-GUARD
        reserve_deadline = deadline-(10.25 if bucket == "P3" else 35.25)
        active_deadline = min(begin+active_seconds, reserve_deadline)
        if active_deadline <= begin:
            raise StopCampaign("resource_stop", "No permitted active/cleanup interval remains")
        attempted.add(name)
        runenv = env.copy()
        runenv.update(PYTHONPATH=str(source/"src")+os.pathsep+str(aux),
            HF_TRACE2_ACTIVE_DEADLINE=repr(active_deadline),
            HF_S0_EVENT_FILE=str(root/"events"/(name+".ndjson")), HF_S0_PHASE=name,
            HF_S0_VERSION="R1", HF_S0_SOURCE_MANIFEST_SHA=manifest_hash or plan_hash,
            HF_HARNESS_ID="HR1", HF_HARNESS_MANIFEST_SHA=harness_hash or plan_hash,
            HF_ARITHMETIC_HARNESS_ID="H1", HF_FCPU_CAMPAIGN_PROTOCOL=PROTOCOL, HF_FCPU_RUN_ID=RUN_ID)
        checked(supervisor.__file__, SUP1_SHA)
        if extended(supervisor.__file__) != repo/"hf_repo/scripts/windows_owned_process.py":
            raise StopCampaign("source_or_identity_not_pass", "Actual loaded parent source differs")
        run_owned, observe = supervisor.run_owned, {}
        if bucket == "P1":
            if candidate is None or extended(candidate.__file__) != aux/"windows_owned_process_sup2.py":
                raise StopCampaign("source_or_identity_not_pass", "P1 candidate is not pinned frozen SUP2")
            checked(candidate.__file__, SUP2_SHA)
            identity = dict(campaign_protocol=PROTOCOL, run_id=RUN_ID, subject=SUBJECT, phase=name, version="R1",
                science_version="R1", source_version="R1", source_manifest_sha256=manifest_hash,
                harness_id="HR1", harness_manifest_sha256=harness_hash, arithmetic_harness_id="H1",
                candidate_supervisor=candidate_identity, supervisor_version="SUP2", supervisor_sha256_role="P1_candidate")
            dump(root/"results/P1_supervision/request.json", dict(schema="hf-micro-trace-supervision-request-1",
                campaign_protocol=PROTOCOL, run_id=RUN_ID, subject=SUBJECT, identity=identity,
                command=list(command), cwd=str(root), deadline_monotonic=active_deadline,
                seconds=active_seconds, rss_limit_bytes=RSS_LIMIT, telemetry_enabled=True,
                telemetry_interval_seconds=1., candidate_supervisor=candidate_identity,
                parent_supervisor=parent_identity, loaded_parent_supervisor=loaded_parent))
            run_owned = candidate.run_owned
            observe = dict(instance_log_path=root/"results/P1_supervision/instances.ndjson",
                instance_identity=identity, telemetry_path=root/"events/P1_trace_cpu.ndjson",
                telemetry_interval_seconds=1., telemetry_identity=identity)
            ledger["P1_status"] = "running"
        print(json.dumps(dict(phase=name, started_utc=utc(), active_seconds_limit=active_deadline-begin)), flush=True)
        try:
            raw = run_owned(command, cwd=str(root), env=runenv, log=root/"logs"/(name+".log"),
                deadline=active_deadline, seconds=active_seconds, rss_limit=RSS_LIMIT, **observe)
        except BaseException:
            uncertain = True
            raise
        # Ownership uncertainty is latched before fallible persistence/hash work.
        if not isinstance(raw, dict) or raw.get("cleanup_verified") is not True:
            uncertain = True
        require(isinstance(raw, dict), "supervisor returned a non-dictionary receipt")
        if bucket == "P1":
            dump(root/"results/P1_supervision/receipt.json", raw)
        row = dict(raw, owned_elapsed_seconds=raw["elapsed_seconds"], elapsed_seconds=time.monotonic()-begin,
            name=name, bucket=bucket, worker_path=str(worker), inclusive_phase_limit_seconds=LIMITS[bucket],
            phase_start_monotonic=begin, phase_return_monotonic=time.monotonic(),
            active_deadline_monotonic=active_deadline, science_version="R1", harness_id="HR1",
            active_limit_kind="phase_inclusive_limit" if begin+active_seconds <= reserve_deadline else "campaign_seal_reserve",
            arithmetic_harness_id="H1", campaign_protocol=PROTOCOL, run_id=RUN_ID,
            source_manifest_sha256=manifest_hash or plan_hash, harness_manifest_sha256=harness_hash or plan_hash,
            supervisor_version="SUP2" if bucket == "P1" else "SUP1",
            supervisor_sha256_role="P1_candidate" if bucket == "P1" else "parent_control",
            elapsed_scope="parent phase entry through setup, raw persistence and owned-process cleanup",
            parent_supervisor=parent_identity, candidate_supervisor=candidate_identity,
            loaded_parent_supervisor=loaded_parent)
        if bucket == "P1":
            row["native_receipt_sha256"] = sha(root/"results/P1_supervision/receipt.json")
        phases.append(row)
        save_ledger()
        print(json.dumps(dict(phase=name, reason=row["reason"], returncode=row["returncode"],
            elapsed_seconds=row["elapsed_seconds"], peak_rss_bytes=row["peak_tree_rss_bytes"], cleanup_verified=row["cleanup_verified"])), flush=True)
        # P1 raw nonzero/resource receipts must still reach the real classifier
        # after proof/source/summary read errors are independently materialized.
        if bucket != "P1":
            if uncertain or not raw.get("cleanup_verified"):
                raise StopCampaign("cleanup_not_pass", name+": cleanup did not close")
            if row["elapsed_seconds"] > LIMITS[bucket]:
                raise StopCampaign("resource_stop", name+": inclusive phase limit exceeded")
            if row.get("supervisor_sha256") != SUP1_SHA:
                raise StopCampaign("source_or_identity_not_pass", name+": supervisor source differs")
            if (row.get("reason") == "supervision_error" or row.get("errors") or row.get("supervision_error")
                    or row.get("telemetry_status") != "disabled"):
                raise StopCampaign("supervision_not_pass", name+": "+str(row.get("reason")))
            if row.get("reason") in ("global_deadline", "phase_timeout", "rss_limit"):
                raise StopCampaign("resource_stop", name+": "+str(row.get("reason")))
            if row.get("reason") != "normal_exit" or type(row.get("returncode")) is not int or row["returncode"] != 0:
                raise StopCampaign("execution_failure", name+": "+str(row.get("reason")))
        return raw

    try:
        worker, command = worker_command("prepare")
        execute("P0_prepare", "P0", command, worker)
        for name in HELPERS:
            checked(aux/name, helper_hashes[name])
        for name in (DRIVER, PROBE, EVIDENCE):
            checked(aux/name, author["hf_repo/scripts/"+name])
        sys.path.insert(0, str(aux))
        reader = load_module("_frozen_micro_trace_v2_evidence", aux/EVIDENCE, author["hf_repo/scripts/"+EVIDENCE])
        reader.verify_inputs(root, include_live=True, deadline=deadline-35.25)
        selected = read(root/"selected_source.json")
        manifest_hash, harness_hash = sha(root/"input_manifest.json"), sha(root/"HR1/manifest.json")
        candidate = load_module("_ftrace2_sup2", aux/"windows_owned_process_sup2.py", SUP2_SHA)
        loaded_candidate = dict(version="SUP2", path=str(extended(candidate.__file__)), sha256=SUP2_SHA)
        require(loaded_candidate == candidate_identity, "loaded candidate identity differs")
        ledger["loaded_candidate_supervisor"] = loaded_candidate
        loaded_helpers = reader.record_loaded_helpers(root)
        dump(root/"loaded_supervisors.json", dict(campaign_protocol=PROTOCOL, protocol=PROTOCOL, run_id=RUN_ID,
            subject=SUBJECT, parent_supervisor=parent_identity, candidate_supervisor=candidate_identity,
            loaded_parent_supervisor=loaded_parent, loaded_candidate_supervisor=loaded_candidate,
            source_manifest_sha256=manifest_hash, harness_manifest_sha256=harness_hash,
            loaded_helpers=loaded_helpers))
        worker = aux/PROBE
        checked(worker, author["hf_repo/scripts/"+PROBE])
        command = [sys.executable, "-u", "-B", str(worker), "--root", str(root), "--source", str(source)]
        raw = execute("P1_trace", "P1", command, worker)
        proof_ok = source_ok = False
        try:
            proof = reader.verify_supervision(root)
            dump(root/"supervision_proof.json", proof)
            ledger["supervision_proof_status"] = proof["status"]
            proof_ok = proof["status"] == "verified_all_instances"
        except BaseException as exc:
            ledger["supervision_proof_status"] = "not_pass"
            ledger["proof_error"] = failure(exc)
            uncertain = True
        try:
            source_check = reader.verify_inputs(root, include_live=True, deadline=deadline-35.25)
            source_ok = source_check["status"] == "verified"
        except BaseException as exc:
            ledger["source_error"] = failure(exc)
        try:
            ledger["loaded_helpers_post_p1"] = reader.record_loaded_helpers(root)
        except BaseException as exc:
            source_ok = False
            ledger["loaded_helper_error"] = failure(exc)
        try:
            filename = root/"results/trace/summary.json"
            summary = read(filename) if filename.is_file() else None
        except BaseException as exc:
            summary = None
            ledger["summary_error"] = failure(exc)
        if isinstance(summary, dict):
            ledger.update(P1_status=summary.get("status", "not_complete"), probe_first_errors=summary.get("errors", []),
                probe_first_error=summary.get("first_error"), probe_first_error_kind=summary.get("first_error_kind"),
                trace_session=summary.get("profiler"), probe_runtime_native_trace_observed=summary.get("runtime_native_trace_observed", False))
        # This request was created before SUP2; retain its identity even when a
        # later disk read fails, and never skip classification on a read error.
        expected = dict(campaign_protocol=PROTOCOL, run_id=RUN_ID, subject=SUBJECT, phase="P1_trace", version="R1",
            science_version="R1", source_version="R1", source_manifest_sha256=manifest_hash,
            harness_id="HR1", harness_manifest_sha256=harness_hash, arithmetic_harness_id="H1",
            candidate_supervisor=candidate_identity, supervisor_version="SUP2", supervisor_sha256_role="P1_candidate")
        outcome = classify(raw, summary, expected, source_ok=source_ok, proof_ok=proof_ok,
                           resource_ok=phases[-1]["elapsed_seconds"] <= LIMITS["P1"])
        ledger["classification"] = outcome
        if not outcome["passed"]:
            raise StopCampaign(outcome["status"], "P1_trace: "+str(outcome["first_error"] or outcome["raw_reason"]))
        status = SUCCESS
    except BaseException as exc:
        status = exc.status if isinstance(exc, StopCampaign) else "execution_failure"
        error = failure(exc)
        ledger["first_stop"] = dict(status=status, error=error, monotonic=time.monotonic())
    finally:
        if ledger["P1_status"] == "running":
            ledger["P1_status"] = "not_complete"
        save_ledger()
        dump(root/"resources.json", dict(schema="hf-micro-trace-resources-1", protocol=PROTOCOL, run_id=RUN_ID,
            status=status, parent_status=status, total_elapsed_seconds=time.monotonic()-start,
            elapsed_seconds=time.monotonic()-start, scope="preseal", phases=phases,
            peak_tree_rss_bytes=max((row["peak_tree_rss_bytes"] for row in phases), default=0),
            rss_limit_bytes=RSS_LIMIT, shared_elapsed_seconds=shared()))
        safe_seal = not uncertain and all(row.get("cleanup_verified") is True for row in phases)
        if safe_seal and shared() <= 20. and time.monotonic() < deadline-10.25:
            try:
                worker, command = worker_command("seal")
                execute("P3_seal", "P3", command, worker)
                seal = read(root/"results/seal/summary.json")
                if seal.get("status") != "pass" or (status == SUCCESS and seal.get("diagnostic_status") != SUCCESS):
                    raise StopCampaign("evidence_failure", "Preservation did not pass")
            except BaseException as exc:
                ledger["seal_error"] = failure(exc)
                if status == SUCCESS:
                    status, error = "evidence_failure", ledger["seal_error"]
        else:
            ledger["seal_skipped"] = "ownership uncertain or shared/final reserve exhausted"
            if status == SUCCESS:
                status, error = "evidence_failure", ledger["seal_skipped"]
        if time.monotonic() >= deadline or shared() > LIMITS["shared"]:
            status, error = "resource_stop", "Campaign/shared allowance exhausted during final preservation"
        if status != SUCCESS and ledger["first_stop"] is None:
            ledger["first_stop"] = dict(status=status, error=error, monotonic=time.monotonic())
        require(len(TARGETS) == 43 and len(set(TARGETS)) == 43, "43 binding targets differ")
        # Both campaign and shared allowances constrain payload hashing. Once
        # either is spent, stop reading large files. Existing unverified targets
        # are explicit partial records, not null records pretending unreached.
        binding_deadline = min(deadline, start+LIMITS["shared"]+sum(row["elapsed_seconds"] for row in phases))
        records, binding_issues, hash_allowed = {}, [], True
        for relative in TARGETS:
            if relative == "execution_receipt.json":
                continue  # Written and bound once from its exact bytes below.
            filename = root/relative
            try:
                info = filename.lstat()
            except FileNotFoundError:
                records[relative] = None
                continue
            except BaseException as exc:
                item = dict(path=relative, bytes=None, sha256=None, status="partial",
                            reason="target_stat_not_verified", error=failure(exc))
                records[relative] = item
                binding_issues.append(item)
                hash_allowed = False
                continue
            item = dict(path=relative, bytes=info.st_size, sha256=None, status="partial")
            if not hash_allowed or time.monotonic() >= binding_deadline:
                hash_allowed = False
                item["reason"] = "binding_allowance_exhausted" if time.monotonic() >= binding_deadline else "hashing_stopped_after_first_binding_error"
            else:
                try:
                    no_reparse(filename)
                    require(stat.S_ISREG(info.st_mode), "binding target is not a regular file")
                    digest = sha(filename, binding_deadline)
                    records[relative] = dict(path=relative, bytes=info.st_size, sha256=digest)
                    continue
                except BaseException as exc:
                    hash_allowed = False
                    item.update(reason="binding_allowance_exhausted" if time.monotonic() >= binding_deadline else "target_hash_not_verified",
                                error=failure(exc))
            records[relative] = item
            binding_issues.append(item)
        if binding_issues:
            ledger["binding_issues"] = binding_issues
            if time.monotonic() >= binding_deadline:
                status, error = "resource_stop", "Campaign/shared allowance exhausted during final binding"
            elif status == SUCCESS:
                status, error = "evidence_failure", "Final target hash could not be verified"
        if status != SUCCESS and ledger["first_stop"] is None:
            ledger["first_stop"] = dict(status=status, error=error, monotonic=time.monotonic())
        save_ledger()
        # These small consistency writes materialize the terminal state even
        # when already late. Their actual lateness is reported as resource_stop;
        # no expired allowance is used for another phase or large-file rehash.
        receipt_record = write_receipt(root/"execution_receipt.json", read(root/"ledger.json"))
        records["execution_receipt.json"] = receipt_record
        binding = dict(schema="hf-micro-trace-receipt-binding-1", protocol=PROTOCOL, run_id=RUN_ID,
            subject=SUBJECT, status=status, scientific_admission=False, force_executed=False,
            records={relative:records[relative] for relative in TARGETS}, prior_binding_sha256=PRIOR_BINDING_SHA,
            path_binding_sha256=PATH_BINDING_SHA, output_manifest_exclusions=list(EXCLUSIONS),
            target_hashing_complete=not binding_issues, target_hashing_deadline_monotonic=binding_deadline,
            existing_unhashed_targets=sum(isinstance(value,dict) and value.get("status") == "partial" for value in records.values()),
            binding_completion_monotonic=time.monotonic(), elapsed_before_binding_seconds=time.monotonic()-start)
        dump(root/"receipt_binding.json", binding)
        if time.monotonic() >= deadline or shared() > LIMITS["shared"]:
            # One minimal consistency rewrite, with no payload read/hash. Never
            # leave an earlier success binding pointing to a changed receipt.
            status, error = "resource_stop", "Final binding completed outside authorized allowance"
            if ledger["first_stop"] is None:
                ledger["first_stop"] = dict(status=status, error=error, monotonic=time.monotonic())
            save_ledger()
            receipt_record = write_receipt(root/"execution_receipt.json", read(root/"ledger.json"), replace_existing=True)
            binding.update(status=status, binding_completion_monotonic=time.monotonic(),
                elapsed_before_binding_seconds=time.monotonic()-start)
            binding["records"]["execution_receipt.json"] = receipt_record
            replace(root/"receipt_binding.json", binding)
        print(json.dumps(dict(protocol=PROTOCOL, run_id=RUN_ID, status=status, error=error,
            elapsed_seconds=time.monotonic()-start, root=str(root), scientific_admission=False, force_executed=False)), flush=True)
    return 0 if status == SUCCESS else 1


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
