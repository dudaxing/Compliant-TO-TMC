"""F-CPU-CLEAN1: one authorized 180-second synthetic-supervision window, no retries.

Only preparation, twenty-one synthetic tests, and evidence preservation may run.
All phase limits include cleanup; this runner never imports scientific code.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import traceback
import xml.etree.ElementTree as ET

import psutil
import windows_owned_process as supervisor
from windows_owned_process import run_owned


CARD = "docs/HF4_C2_S0_PREPARATION_RESULT_20260928.md"
PROTOCOL = "F-CPU-CLEAN1"
RUN_ID = "cpu_cleanup_contract_001"
DIAGNOSTIC_FOCUS = "instance_termination_coverage"
LIMITS = {"P0": 15., "P1": 135., "P2": 15., "shared": 15.}
SUPERVISOR_SHA = "9f3da2f22bec869d069278058aa8502bd5f73c4b977b01ec5daa7b26ff1aec32"
CANDIDATE_SHA = "b5f149e1cd3d6d9b4ad392123e410b786606f120f2e078139b7bacc97f2d9499"
SUBPROCESS_SHA = "970207fdd712c92f7dc14d1623d2574f7e0910ceb0b5c37652a7a0850f35a396"
CONTRACT_TESTS = (
    "test_active_zero_with_history_gap_fails_closed",
    "test_duplicate_identity_does_not_inflate_coverage",
    "test_reused_pid_with_new_creation_time_is_bound",
    "test_wrong_job_cannot_fill_coverage",
    "test_open_failure_is_recorded_without_false_coverage",
    "test_creation_time_failure_releases_opened_handle",
    "test_wait_failure_does_not_prove_termination",
    "test_close_failure_does_not_skip_other_handles",
    "test_timeout_with_exit_code_125_is_not_termination",
    "test_capacity_exhaustion_fails_closed",
    "test_multiple_handles_share_one_cleanup_deadline",
    "test_signaled_handle_is_released_before_accounting",
)
RUNTIME_FILES = {
    "__init__.py": (92363, "7b6a0675824eb1fa2ff0cb1eb36e358dc454703e51dfa4e9a0e6ccd26a159f0c"),
    "_pswindows.py": (36466, "0bbd52dcb214735be4168d11a2ae192d5bc7265c8cf72c611179476479687f54"),
    "_psutil_windows.pyd": (70656, "0035450801bd7d938e9e146c5ec28e619cb5a5f4a18cdc53ac7e9734c7f94f78"),
}
RSS_LIMIT = 8 * 1024**3
CLEANUP_GUARD = 5.25
EXPECTED_TESTS = {
    ("test_windows_owned_process.py", "test_exit[0]"),
    ("test_windows_owned_process.py", "test_exit[7]"),
    ("test_windows_owned_process.py", "test_timeout"),
    ("test_windows_owned_process.py", "test_resource_trigger"),
    ("test_windows_owned_process.py", "test_orphan_grandchild"),
    ("test_windows_owned_cpu.py", "test_busy_sleep_and_exited_descendant_keep_cumulative_cpu"),
    ("test_windows_owned_cpu.py", "test_timeout_preserves_partial_samples_and_cleans_job"),
    ("test_windows_owned_cpu.py", "test_observation_failure_stops_and_independent_cleanup_survives[query]"),
    ("test_windows_owned_cpu.py", "test_observation_failure_stops_and_independent_cleanup_survives[write]"),
}
EXPECTED_TESTS.update(("test_windows_cleanup_contract.py", name) for name in CONTRACT_TESTS)
FATAL = {"rss_limit", "global_deadline", "phase_timeout", "supervision_error", "cleanup_failure"}


def utc():
    return datetime.now(timezone.utc).isoformat()


def extended(value):
    value = str(Path(value).resolve())
    if os.name == "nt" and not value.startswith("\\\\?\\"):
        value = "\\\\?\\UNC\\" + value[2:] if value.startswith("\\\\") else "\\\\?\\" + value
    return Path(value)


def sha(filename):
    with Path(filename).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(filename):
    return json.loads(Path(filename).read_text(encoding="utf-8"))


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


class StopCampaign(RuntimeError):
    def __init__(self, status, detail):
        super().__init__(detail)
        self.status = status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    repo, root = extended(args.repo), extended(args.root)
    if root.exists():
        raise RuntimeError("Refuse to reuse or reset a campaign directory")
    if root == repo or repo.is_relative_to(root):
        raise RuntimeError("Evidence root must not contain the repository")
    if root != repo / "hf4_c2_stable_f_validation" / RUN_ID:
        raise RuntimeError("Evidence root differs from the authorized unique directory")

    start = time.monotonic()
    deadline = start + 180.
    root.mkdir(parents=True)
    for name in ("events", "logs", "results"):
        (root / name).mkdir()
    phases, attempted = [], set()
    status, error = "running", None
    supervision_uncertain = False
    aux = root / "aux/hf_repo/scripts"
    original_worker = repo / "hf_repo/scripts/cpu_supervision_evidence.py"
    worker_sha = sha(original_worker)
    supervisor_sha = sha(supervisor.__file__)
    if supervisor_sha != SUPERVISOR_SHA:
        raise RuntimeError("Authorized supervisor source differs")
    candidate_sha = sha(repo / "hf_repo/scripts/windows_owned_process_sup2.py")
    if candidate_sha != CANDIDATE_SHA:
        raise RuntimeError("Reviewed SUP2 candidate source differs")
    parent_identity = dict(version="SUP1", path=str(aux / "windows_owned_process.py"), sha256=supervisor_sha)
    candidate_identity = dict(version="SUP2", path=str(aux / "windows_owned_process_sup2.py"), sha256=candidate_sha)
    loaded_parent = dict(version="SUP1", path=str(extended(supervisor.__file__)), sha256=supervisor_sha)
    worker_dependencies = {name:sha(original_worker.parent / name) for name in
                           ("s0_event_log.py",)}
    source_manifest = root / "input_manifest.json"
    selected = None
    manifest_hash = harness_hash = None
    ledger = dict(schema="hf-cpu-supervision-campaign-1", protocol=PROTOCOL, status=status,
        run_id=RUN_ID, diagnostic_focus=DIAGNOSTIC_FOCUS, cleanup_contract="not_evaluated",
        contract="CPU-CLEAN1", parent_supervisor=parent_identity, candidate_supervisor=candidate_identity,
        loaded_parent_supervisor=loaded_parent,
        started_utc=utc(), start_monotonic=start, deadline_monotonic=deadline,
        seconds=180., rss_limit_bytes=RSS_LIMIT, limits_seconds=LIMITS,
        cleanup_and_poll_guard_seconds=CLEANUP_GUARD, final_binding_reserved_seconds=5.,
        boot_time_estimate=psutil.boot_time(), phases=phases, scientific_admission=False,
        force_executed=False, force_call_limit=0, new_equilibrium_paths=0, new_hp_evaluations=0)
    dump(root / "plan.json", dict(ledger, repo=str(repo), python=sys.version,
        card_sha256=sha(repo / CARD), evidence_worker_sha256=worker_sha,
        evidence_worker_dependency_sha256=worker_dependencies,
        supervisor_sha256=candidate_sha, supervisor_sha256_role="candidate",
        runner_sha256=sha(__file__),
        telemetry_interval_seconds=0.05, telemetry_scope="synthetic Job CPU; observer CPU excluded",
        prior_campaign="cpu_pid_diagnostic_001", expected_test_cases=sorted(EXPECTED_TESTS),
        subject="windows_job_supervision", version="SUP2", harness_id="CPU-CLEAN1",
        non_seal_active_deadline=deadline-25.25, seal_active_deadline=deadline-10.25))
    plan_hash = sha(root / "plan.json")
    dump(root / "ledger.json", ledger)
    env = os.environ.copy()
    env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONUNBUFFERED="1", PYTHONNOUSERSITE="1",
        PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", JAX_ENABLE_X64="true", JAX_TRACEBACK_FILTERING="off",
        JAX_ENABLE_COMPILATION_CACHE="false", JAX_PLATFORMS="cpu", OMP_NUM_THREADS="1",
        OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", MPLBACKEND="Agg",
        MPLCONFIGDIR=str(root / "matplotlib-cache"))

    def shared_elapsed():
        return time.monotonic()-start-sum(p["elapsed_seconds"] for p in phases)

    def save_ledger():
        ledger.update(status=status, elapsed_seconds=time.monotonic()-start,
            consumed_phase_seconds={key:sum(p["elapsed_seconds"] for p in phases if p["bucket"] == key)
                for key in ("P0", "P1", "P2")}, shared_elapsed_seconds=shared_elapsed())
        replace(root / "ledger.json", ledger)

    def execute(name, bucket, command):
        nonlocal supervision_uncertain, status, error
        if name in attempted:
            raise StopCampaign("execution_failure", "No phase may run twice: " + name)
        if bucket != "P2" and shared_elapsed() > 10.:
            raise StopCampaign("resource_stop", "Pre-seal shared allowance exhausted")
        if bucket == "P2" and shared_elapsed() > 10.:
            # Sealing may preserve a failure, but cannot turn a spent final
            # binding reserve into a passing campaign.
            error = dict(prior=error, pre_seal_shared_overrun_seconds=shared_elapsed())
            status = "resource_stop"
            replace(root / "resources.json", dict(phases=phases, status=status, error=error,
                total_elapsed_seconds=time.monotonic()-start,
                plot_scope="before P2 seal; final receipt includes P2"))
        begin = time.monotonic()
        active_seconds = LIMITS[bucket] - CLEANUP_GUARD
        absolute = deadline - (10.25 if bucket == "P2" else 25.25)
        active_deadline = min(begin+active_seconds, absolute)
        if active_deadline <= begin:
            raise StopCampaign("resource_stop", "No active/cleanup time remains for " + name)
        attempted.add(name)
        runenv = env.copy()
        runenv.update(PYTHONPATH=str(aux),
            HF_S0_EVENT_FILE=str(root / "events" / (name + ".ndjson")),
            HF_S0_PHASE=name, HF_S0_VERSION="SUP2", HF_S0_SOURCE_MANIFEST_SHA=manifest_hash or plan_hash,
            HF_HARNESS_ID="CPU-CLEAN1", HF_HARNESS_MANIFEST_SHA=harness_hash or plan_hash,
            HF_CPU_S1_ACTIVE_DEADLINE=repr(active_deadline),
            HF_CPU_S1_RESULT_DIR=str(root / "results/P1_tests"),
            HF_CLEAN1_CANDIDATE_SHA=candidate_sha, HF_CLEAN1_PARENT_SHA=supervisor_sha,
            HF_CLEAN1_PARENT_PATH=loaded_parent["path"])
        print(json.dumps(dict(phase=name, started_utc=utc(),
            remaining_campaign_seconds=deadline-begin, active_seconds_limit=active_deadline-begin)), flush=True)
        if sha(supervisor.__file__) != supervisor_sha:
            raise StopCampaign("source_not_pass", "Loaded supervisor source changed")
        try:
            receipt = run_owned(command, cwd=str(root), env=runenv,
                log=root / "logs" / (name + ".log"), deadline=active_deadline,
                seconds=active_seconds, rss_limit=RSS_LIMIT)
        except BaseException:
            supervision_uncertain = True
            raise
        receipt["owned_elapsed_seconds"] = receipt["elapsed_seconds"]
        receipt["elapsed_seconds"] = time.monotonic() - begin
        receipt.update(name=name, bucket=bucket, inclusive_phase_limit_seconds=LIMITS[bucket],
            elapsed_scope="parent phase entry through owned-process cleanup; includes WinAPI/setup",
            active_deadline_monotonic=active_deadline, source_version="SUP1",
            active_limit_kind="phase_inclusive_limit" if begin+active_seconds <= absolute else "campaign_seal_reserve",
            source_manifest_sha256=manifest_hash or plan_hash,
            harness_id="CPU-CLEAN1", harness_manifest_sha256=harness_hash or plan_hash)
        receipt.update(parent_supervisor=parent_identity, candidate_supervisor=candidate_identity,
                       loaded_parent_supervisor=loaded_parent, supervisor_sha256_role="parent")
        phases.append(receipt)
        save_ledger()
        print(json.dumps(dict(phase=name, reason=receipt["reason"], returncode=receipt["returncode"],
            seconds=receipt["elapsed_seconds"], peak_rss_bytes=receipt["peak_tree_rss_bytes"],
            cleanup_verified=receipt["cleanup_verified"])), flush=True)
        if receipt["reason"] in FATAL or not receipt["cleanup_verified"]:
            raise StopCampaign("resource_or_supervision_stop", name + ": " + receipt["reason"])
        if receipt["elapsed_seconds"] > LIMITS[bucket]:
            raise StopCampaign("resource_stop", name + " exceeded its inclusive phase limit")
        if receipt["returncode"] != 0:
            raise StopCampaign("execution_failure", name + " returned " + str(receipt["returncode"]))
        return receipt

    def worker_command(action, *, frozen=True):
        def matches(candidate):
            files = {candidate.name:worker_sha, **worker_dependencies}
            return all((candidate.parent / name).is_file() and sha(candidate.parent / name) == digest
                       for name, digest in files.items())
        candidate = aux / "cpu_supervision_evidence.py" if frozen else original_worker
        if not matches(candidate):
            if action != "seal" or not matches(original_worker):
                raise StopCampaign("source_not_pass", "Evidence worker identity changed or missing")
            candidate = original_worker  # P0 partial failure: approved stdlib preservation only.
        return [sys.executable, "-u", "-B", str(candidate), "--root", str(root),
                "--repo", str(repo), "--action", action]

    def verify_frozen_inputs():
        if sha(source_manifest) != manifest_hash or harness_hash != manifest_hash:
            raise StopCampaign("source_not_pass", "Input/harness manifest identity changed")
        manifest = read(source_manifest)
        if (manifest.get("schema") != "hf-cpu-supervision-inputs-1"
                or manifest.get("protocol") != PROTOCOL or manifest.get("run_id") != RUN_ID
                or manifest.get("diagnostic_focus") != DIAGNOSTIC_FOCUS
                or manifest.get("subject") != "windows_job_supervision"
                or manifest.get("version") != "SUP2" or manifest.get("harness_id") != "CPU-CLEAN1"
                or manifest.get("supervisor_sha256") != candidate_sha
                or manifest.get("supervisor_sha256_role") != "candidate"
                or manifest.get("loaded_parent_supervisor") != loaded_parent
                or manifest.get("parent_supervisor") != parent_identity
                or manifest.get("candidate_supervisor") != candidate_identity):
            raise StopCampaign("source_not_pass", "Synthetic subject/harness identity differs")
        current = read(root / "selected_source.json")
        if (current != selected or current.get("version") != "SUP2"
                or current.get("protocol") != PROTOCOL or current.get("run_id") != RUN_ID
                or current.get("diagnostic_focus") != DIAGNOSTIC_FOCUS
                or current.get("parent_supervisor") != parent_identity
                or current.get("candidate_supervisor") != candidate_identity
                or extended(current["source"]) != root / "aux/hf_repo"
                or extended(current["source_manifest"]) != source_manifest
                or current["source_manifest_sha256"] != manifest_hash
                or current["harness"] != dict(id="CPU-CLEAN1", version="SUP2", manifest_sha256=manifest_hash)):
            raise StopCampaign("source_not_pass", "Selected source differs")
        names = set()
        for row in manifest["files"]:
            frozen = extended(root / row["path"])
            if row["path"] in names or not frozen.is_relative_to(root):
                raise StopCampaign("source_not_pass", "Duplicate or escaping input path")
            names.add(row["path"])
            for actual in (frozen, extended(row["source"])):
                if actual.stat().st_size != row["bytes"] or sha(actual) != row["sha256"]:
                    raise StopCampaign("source_not_pass", "Input source or frozen copy changed: " + row["path"])
        if sha(aux / "windows_owned_process.py") != SUPERVISOR_SHA:
            raise StopCampaign("source_not_pass", "Frozen supervisor changed")
        if sha(aux / "windows_owned_process_sup2.py") != candidate_sha:
            raise StopCampaign("source_not_pass", "Frozen SUP2 candidate changed")
        inheritance = manifest["inheritance_manifest"]
        inheritance_path = extended(root / inheritance["path"])
        if not inheritance_path.is_relative_to(root) or sha(inheritance_path) != inheritance["sha256"]:
            raise StopCampaign("source_not_pass", "Derived inheritance manifest changed")
        for row in manifest["science_identity_checks"]:
            actual = extended(row["path"])
            if (actual != extended(repo / row["repo_relative_path"])
                    or actual.stat().st_size != row["bytes"] or sha(actual) != row["sha256"]):
                raise StopCampaign("source_not_pass", "Scientific context changed during synthetic tests")
        runtime_rows = manifest["runtime_file_checks"]
        if (len(runtime_rows) != 3 or len({r["package_relative_path"] for r in runtime_rows}) != 3
                or {r["package_relative_path"] for r in runtime_rows} != set(RUNTIME_FILES)):
            raise StopCampaign("source_not_pass", "Cleanup runtime inventory differs")
        runtime_root = extended(Path(psutil.__file__).parent)
        for row in runtime_rows:
            name = row["package_relative_path"]
            size, digest = RUNTIME_FILES[name]
            actual = extended(row["path"])
            if (row.get("package") != "psutil" or actual != runtime_root / name
                    or (row["bytes"], row["sha256"]) != (size, digest)
                    or actual.stat().st_size != size or sha(actual) != digest):
                raise StopCampaign("source_not_pass", "Cleanup runtime file changed: " + name)
        if psutil.__version__ != "7.2.2":
            raise StopCampaign("source_not_pass", "Loaded psutil version differs")
        stdlib_rows = manifest["stdlib_file_checks"]
        if len(stdlib_rows) != 1:
            raise StopCampaign("source_not_pass", "Expected one pinned subprocess source")
        row = stdlib_rows[0]
        actual = extended(row["path"])
        if (actual != extended(supervisor.subprocess.__file__) or row["bytes"] != 91718
                or row["sha256"] != SUBPROCESS_SHA or actual.stat().st_size != 91718
                or sha(actual) != SUBPROCESS_SHA):
            raise StopCampaign("source_not_pass", "Popen handle owner implementation changed")

    def pytest_command():
        folder = root / "results/P1_tests"
        folder.mkdir(parents=True)
        tests = root / "aux/hf_repo/tests"
        return [sys.executable, "-u", "-B", "-m", "pytest", "-x", "--maxfail=1", "-vv", "--tb=long",
            "-p", "no:cacheprovider", "-p", "hf_s0_pytest_events", "-o", "xfail_strict=true",
            str(tests / "test_windows_cleanup_contract.py"),
            str(tests / "test_windows_owned_process.py"), str(tests / "test_windows_owned_cpu.py"),
            "--rootdir="+str(tests.parent), "--basetemp="+str(folder / "synthetic-temp"),
            "--junitxml="+str(folder / "pytest.xml")]

    def verify_tests():
        event_path = root / "events/P1_tests.ndjson"
        raw = event_path.read_bytes()
        if not raw.endswith(b"\n"):
            raise StopCampaign("evidence_failure", "Incomplete pytest event line")
        rows = [json.loads(line) for line in raw.splitlines()]
        for i, row in enumerate(rows, 1):
            if (row.get("schema") != "hf-s0-event-1" or row.get("sequence") != i or row.get("phase") != "P1_tests" or row.get("version") != "SUP2"
                    or row.get("source_manifest_sha256") != manifest_hash or row.get("harness_id") != "CPU-CLEAN1"
                    or row.get("harness_manifest_sha256") != harness_hash):
                raise StopCampaign("evidence_failure", "Pytest event identity differs")
        collections = [r for r in rows if r.get("event") == "collection_finish"]
        sessions = [r for r in rows if r.get("event") == "session_finish"]
        reports = [r for r in rows if r.get("event") == "test_report"]
        if (len(collections) != 1 or collections[0].get("outcome") != "passed"
                or len(sessions) != 1 or sessions[0].get("exitstatus") != 0
                or sessions[0].get("testsfailed") != 0):
            raise StopCampaign("evidence_failure", "Incomplete or failed pytest session")
        expected = EXPECTED_TESTS
        def node_key(nodeid):
            parts = nodeid.replace("\\", "/").split("::", 1)
            return (parts[0].rsplit("/", 1)[-1], parts[1]) if len(parts) == 2 else None
        if set(map(node_key, collections[0]["nodeids"])) != expected:
            raise StopCampaign("evidence_failure", "Collected node identities differ")
        actual = set()
        for r in reports:
            key = node_key(r["nodeid"])
            if key not in expected or r.get("outcome") != "passed":
                raise StopCampaign("evidence_failure", "Unexpected test or non-pass report")
            expected_path = extended(root / "aux/hf_repo/tests" / key[0])
            if extended(r["test_file_path"]) != expected_path:
                raise StopCampaign("evidence_failure", "Test imported from unexpected path")
            identity = (*key, r["when"])
            if identity in actual:
                raise StopCampaign("evidence_failure", "Duplicate test report")
            actual.add(identity)
        wanted = {(*key, when) for key in expected for when in ("setup", "call", "teardown")}
        if (actual != wanted or collections[0].get("collected") != len(expected)
                or sessions[0].get("testscollected") != len(expected)
                or len(set(collections[0]["nodeids"])) != len(expected)
                or any(r.get("event") in ("pytest_internal_error", "pytest_interrupted") for r in rows)):
            raise StopCampaign("evidence_failure", "Test coverage/session records differ")
        tree = ET.parse(root / "results/P1_tests/pytest.xml")
        cases = list(tree.iter("testcase"))
        if len(cases) != len(expected) or any(
                child.tag in ("failure", "error", "skipped") for case in cases for child in case):
            raise StopCampaign("evidence_failure", "JUnit testcase count or outcomes differ")
        xml_keys = [(c.get("classname", "").rsplit(".", 1)[-1] + ".py", c.get("name")) for c in cases]
        if len(set(xml_keys)) != len(expected) or set(xml_keys) != expected:
            raise StopCampaign("evidence_failure", "JUnit exact node identities differ")
        runtime_identities = {}
        for filename, testname in (
                ("runtime_identity_contract.json", "test_windows_cleanup_contract.py"),
                ("runtime_identity_process.json", "test_windows_owned_process.py"),
                ("runtime_identity.json", "test_windows_owned_cpu.py")):
            identity_path = root / "results/P1_tests" / filename
            identities = read(identity_path)
            if (extended(identities["supervisor_path"]) != aux / "windows_owned_process_sup2.py"
                    or identities["supervisor_sha256"] != candidate_sha
                    or identities.get("supervisor_sha256_role") != "candidate"
                    or extended(identities["test_path"]) != root / "aux/hf_repo/tests" / testname
                    or identities["test_sha256"] != sha(root / "aux/hf_repo/tests" / testname)
                    or identities["source_manifest_sha256"] != manifest_hash
                    or identities["harness_manifest_sha256"] != harness_hash
                    or identities["version"] != "SUP2" or identities["harness_id"] != "CPU-CLEAN1"
                    or identities.get("parent_supervisor") != parent_identity
                    or identities.get("candidate_supervisor") != candidate_identity
                    or identities.get("loaded_parent_supervisor") != loaded_parent):
                raise StopCampaign("evidence_failure", "Actual loaded synthetic sources differ: " + filename)
            runtime_identities[filename] = dict(sha256=sha(identity_path), record=identities)
        dump(root / "results/P1_tests/verification.json", dict(status="pass", count=len(expected),
            protocol=PROTOCOL, run_id=RUN_ID, diagnostic_focus=DIAGNOSTIC_FOCUS,
            subject="windows_job_supervision", version="SUP2", contract="CPU-CLEAN1",
            expected=sorted(expected), event_sha256=sha(event_path),
            xml_sha256=sha(root / "results/P1_tests/pytest.xml"), supervisor_sha256=candidate_sha,
            supervisor_sha256_role="candidate", parent_supervisor=parent_identity,
            candidate_supervisor=candidate_identity, loaded_parent_supervisor=loaded_parent,
            source_manifest_sha256=manifest_hash, harness_manifest_sha256=harness_hash,
            loaded_sources={name:value["record"] for name,value in runtime_identities.items()},
            loaded_sources_sha256={name:value["sha256"] for name,value in runtime_identities.items()},
            force_executed=False, scientific_admission=False))

    try:
        execute("P0_prepare", "P0", worker_command("prepare", frozen=False))
        manifest_hash = harness_hash = sha(source_manifest)
        selected = read(root / "selected_source.json")
        verify_frozen_inputs()
        execute("P1_tests", "P1", pytest_command())
        verify_tests()
        verify_frozen_inputs()
        status = "synthetic_supervision_pass_no_force"
    except StopCampaign as problem:
        status, error = problem.status, dict(type=type(problem).__name__, message=str(problem))
    except BaseException as problem:
        status, error = "parent_exception", dict(type=type(problem).__name__, message=str(problem),
                                                traceback=traceback.format_exc())
    finally:
        # No further scientific calls are possible here, even after partial P0.
        dump(root / "resources.json", dict(phases=phases, status=status, error=error,
            total_elapsed_seconds=time.monotonic()-start, plot_scope="before P2 seal; final receipt includes P2"))
        clean = not supervision_uncertain and all(p["cleanup_verified"] for p in phases)
        if clean and time.monotonic() < deadline-10.25:
            try:
                execute("P2_seal", "P2", worker_command("seal"))
                cleanup_contract = read(root / "cleanup_contract.json")
                if (cleanup_contract.get("protocol") != PROTOCOL
                        or cleanup_contract.get("run_id") != RUN_ID
                        or cleanup_contract.get("diagnostic_focus") != DIAGNOSTIC_FOCUS
                        or cleanup_contract.get("parent_supervisor") != parent_identity
                        or cleanup_contract.get("candidate_supervisor") != candidate_identity):
                    raise StopCampaign("evidence_failure", "Cleanup contract report identity differs")
                ledger["cleanup_contract"] = cleanup_contract["status"]
                if status == "synthetic_supervision_pass_no_force" and (
                        cleanup_contract["status"] != "verified_all_instances"
                        or cleanup_contract.get("real_case_count") != 9
                        or cleanup_contract.get("control_case_count") != 12
                        or cleanup_contract.get("proof_count") != 10
                        or cleanup_contract.get("issues") != []
                        or cleanup_contract.get("force_executed") is not False
                        or cleanup_contract.get("scientific_admission") is not False):
                    raise StopCampaign("evidence_failure", "Passing tests lack complete instance cleanup evidence")
            except BaseException as problem:
                error = dict(prior=error, seal_error=dict(type=type(problem).__name__, message=str(problem)))
                status = problem.status if isinstance(problem, StopCampaign) else "seal_failure"
        else:
            error = dict(prior=error, seal_error="No safe cleanup/time margin for P2 seal")
            if status == "synthetic_supervision_pass_no_force":
                status = "resource_stop"
        if time.monotonic() > deadline or shared_elapsed() > LIMITS["shared"]:
            status = "resource_stop"
        ledger.update(status=status, error=error, finished_utc=utc(), elapsed_seconds=time.monotonic()-start,
            selected_source=selected, source_manifest_sha256=manifest_hash, harness_manifest_sha256=harness_hash,
            shared_elapsed_seconds=shared_elapsed(), scientific_admission=False)
        replace(root / "ledger.json", ledger)
        dump(root / "execution_receipt.json", ledger)
        optional_sha = lambda name: sha(root / name) if (root / name).is_file() else None
        binding = dict(schema="hf-cpu-supervision-receipt-binding-1",
            protocol=PROTOCOL, run_id=RUN_ID, diagnostic_focus=DIAGNOSTIC_FOCUS,
            plan_sha256=plan_hash, input_manifest_sha256=optional_sha("input_manifest.json"),
            harness_manifest_sha256=optional_sha("input_manifest.json"),
            selected_source_sha256=optional_sha("selected_source.json"),
            receipt_sha256=sha(root / "execution_receipt.json"),
            output_manifest_sha256=optional_sha("output_sha256.json"),
            test_coverage_sha256=optional_sha("test_coverage.json"),
            synthetic_lifecycle_sha256=optional_sha("synthetic_lifecycle.json"),
            cleanup_contract_sha256=optional_sha("cleanup_contract.json"),
            seal_event_sha256=optional_sha("events/P2_seal.ndjson"), seal_log_sha256=optional_sha("logs/P2_seal.log"),
            sealed_utc=utc(), elapsed_campaign_seconds=time.monotonic()-start,
            diagnostic_only=True, force_executed=False, scientific_admission=False)
        dump(root / "receipt_binding.json", binding)
        # The final fsync and payload hashes are inside the budget too. A late
        # finalization is never allowed to return a success code or receipt.
        after_binding = time.monotonic()
        final_shared = shared_elapsed()
        if after_binding > deadline or final_shared > LIMITS["shared"]:
            status = "resource_stop"
            error = dict(prior=error, tail_budget_overrun=True,
                observed_elapsed_seconds=after_binding-start, observed_shared_seconds=final_shared)
            ledger.update(status=status, error=error, finished_utc=utc(),
                elapsed_seconds=after_binding-start, shared_elapsed_seconds=final_shared)
            # One bounded best-effort failure record only; no retry loop or
            # scientific work follows this terminal budget observation.
            replace(root / "ledger.json", ledger)
            replace(root / "execution_receipt.json", ledger)
            binding.update(receipt_sha256=sha(root / "execution_receipt.json"),
                status=status, tail_budget_overrun=True, sealed_utc=utc(),
                elapsed_campaign_seconds=time.monotonic()-start)
            replace(root / "receipt_binding.json", binding)
        print(json.dumps(dict(status=status, seconds=time.monotonic()-start, error=error)), flush=True)
    return 0 if status == "synthetic_supervision_pass_no_force" else 1


if __name__ == "__main__":
    raise SystemExit(main())
