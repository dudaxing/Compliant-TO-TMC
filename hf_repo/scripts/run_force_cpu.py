"""F-REUSE2: one authorized 620-second fixed-R1 validation, no retries.

Only preparation, the fixed local contract, one cold force, and preservation may run.
All phase limits include cleanup; this runner never imports scientific code.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import traceback

import psutil
import windows_owned_process as supervisor


CARD = "docs/HF4_C2_S0_PREPARATION_RESULT_20260928.md"
PROTOCOL = "F-REUSE2"
RUN_ID = "force_reuse_002"
LIMITS = {"P0": 25., "P1": 300., "P2": 245., "P3": 25., "shared": 25.}
RSS_LIMIT = 8 * 1024**3
CLEANUP_GUARD = 5.25
PARENT_SHA = "9f3da2f22bec869d069278058aa8502bd5f73c4b977b01ec5daa7b26ff1aec32"
CANDIDATE_SHA = "b5f149e1cd3d6d9b4ad392123e410b786606f120f2e078139b7bacc97f2d9499"
PROOF_HELPER_SHA = "2d378c64705461d58fa966528a347b6e411431402877663fd546f3fec8912f45"
CLEAN_BINDING_SHA = "8c5b75b26d3968ac0eca93b71752e5d68dc079e2df39992774edfc9ce9902fc5"
REUSE_BINDING_SHA = "c4cd4303e584eea5d5579496f0fc123e47b51aad05f2ed9be72be683f6df6eb8"
R1_KERNEL_SHA = "630babc9c299ef2336835df18a50521f51d439dc09e3353ae6d0776d91937970"
HR1_TEST_SHA = "28e696175d572379527e6a021365dacf445fa4dd28f73cb381925d95bfb383d5"
HR1_NATIVE_PROTOCOL = "F-REUSE1"
HR1_NATIVE_RUN_ID = "force_reuse_001"
FATAL = {"rss_limit", "global_deadline", "phase_timeout", "supervision_error", "cleanup_failure"}
MICRO_GROUPS = ("valid_first_three", "valid_last_three", "original_mixed", "mixed_negative_J",
                "mixed_large_input", "mixed_nan_input", "mixed_large_coefficient", "mixed_nan_coefficient")
PAIR_FIELDS = ("F", "G", "Hu", "J", "B", "delta")
OUTPUT_FIELDS = {"residual", "material_residual", "regularization_residual", "material_energy",
                 "stress_first_piola", "stress_second_piola", "small_branch", "arithmetic_supported",
                 *PAIR_FIELDS, *(name+suffix for name in PAIR_FIELDS for suffix in ("_hi", "_lo"))}


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
    deadline = start + 620.
    root.mkdir(parents=True)
    for name in ("events", "logs", "results"):
        (root / name).mkdir()
    phases, attempted = [], set()
    status, error = "running", None
    supervision_uncertain = False
    source = root / "R1/source/hf_repo"
    aux = root / "aux/hf_repo/scripts"
    original_worker = repo / "hf_repo/scripts/force_cpu_evidence.py"
    worker_sha = sha(original_worker)
    supervisor_sha = sha(supervisor.__file__)
    parent_identity = dict(version="SUP1", path=str(aux / "windows_owned_process.py"), sha256=PARENT_SHA)
    candidate_identity = dict(version="SUP2", path=str(aux / "windows_owned_process_sup2.py"), sha256=CANDIDATE_SHA)
    loaded_parent = dict(version="SUP1", path=str(extended(supervisor.__file__)), sha256=supervisor_sha)
    candidate = None
    frozen_worker = None
    worker_dependencies = {name:sha(original_worker.parent / name) for name in
                           ("force_observation_evidence.py", "s0_preparation_evidence.py", "s0_event_log.py",
                            "cpu_supervision_evidence.py")}
    source_manifest = root / "input_manifest.json"
    harness_manifest = root / "HR1/manifest.json"
    arithmetic_manifest = root / "H1/manifest.json"
    candidate_manifest = root / "R1/source_manifest.json"
    selected = None
    manifest_hash = harness_hash = None
    arithmetic_hash = candidate_manifest_hash = None
    ledger = dict(schema="hf-force-cpu-campaign-1", protocol=PROTOCOL, campaign_protocol=PROTOCOL,
        run_id=RUN_ID, status=status, parent_supervisor=parent_identity, candidate_supervisor=candidate_identity,
        loaded_parent_supervisor=loaded_parent, loaded_candidate_supervisor=None,
        started_utc=utc(), start_monotonic=start, deadline_monotonic=deadline,
        seconds=620., rss_limit_bytes=RSS_LIMIT, limits_seconds=LIMITS,
        cleanup_and_poll_guard_seconds=CLEANUP_GUARD, final_binding_reserved_seconds=5.,
        boot_time_estimate=psutil.boot_time(), phases=phases, scientific_admission=False,
        force_call_limit=1, force_process_attempted=False, new_equilibrium_paths=0, new_hp_evaluations=0,
        P1_status="not_reached", local_contract_process_attempted=False,
        local_structure_equivalence_pass=False, fixed_force_three_reference_gates_pass=False,
        arithmetic_harness_version="H1", supervision_proof_status="not_reached",
        new_patch_applications=0, inherited_candidate_file_count=32,
        local_pre_force_supervision_proof=None)
    dump(root / "plan.json", dict(ledger, repo=str(repo), python=sys.version,
        card_sha256=sha(repo / CARD), evidence_worker_sha256=worker_sha,
        evidence_worker_dependency_sha256=worker_dependencies,
        supervisor_sha256=CANDIDATE_SHA, supervisor_sha256_role="P1_P2_candidate",
        runner_sha256=sha(__file__),
        telemetry_interval_seconds=1.0, telemetry_scope="owned Job CPU; parent CPU excluded",
        prior_campaign="force_reuse_001", prior_binding_sha256=REUSE_BINDING_SHA,
        native_harness_protocol=HR1_NATIVE_PROTOCOL, native_harness_run_id=HR1_NATIVE_RUN_ID,
        inherited_supervision_campaign="cpu_cleanup_contract_001",
        inherited_supervision_binding_sha256=CLEAN_BINDING_SHA, local_tests_scheduled=True,
        inherited_arithmetic_harness_version="H1", inherited_arithmetic_tests_rerun=False,
        science_version="R1", harness_version="HR1", representative="unit__near_rotation",
        non_seal_active_deadline=deadline-35.25, seal_active_deadline=deadline-10.25))
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
                for key in ("P0", "P1", "P2", "P3")}, shared_elapsed_seconds=shared_elapsed())
        replace(root / "ledger.json", ledger)

    def execute(name, bucket, command):
        nonlocal supervision_uncertain, status, error
        if name in attempted:
            raise StopCampaign("execution_failure", "No phase may run twice: " + name)
        if shared_elapsed() > 20.:
            raise StopCampaign("resource_stop", "Pre-seal shared allowance exhausted")
        begin = time.monotonic()
        active_seconds = LIMITS[bucket] - CLEANUP_GUARD
        absolute = deadline - (10.25 if bucket == "P3" else 35.25)
        active_deadline = min(begin+active_seconds, absolute)
        if active_deadline <= begin:
            raise StopCampaign("resource_stop", "No active/cleanup time remains for " + name)
        attempted.add(name)
        runenv = env.copy()
        runenv.update(PYTHONPATH=str(source / "src")+os.pathsep+str(aux),
            HF_S0_EVENT_FILE=str(root / "events" / (name + ".ndjson")),
            HF_S0_PHASE=name, HF_S0_VERSION="R1", HF_S0_SOURCE_MANIFEST_SHA=manifest_hash or plan_hash,
            HF_HARNESS_ID="HR1", HF_HARNESS_MANIFEST_SHA=harness_hash or plan_hash,
            HF_FOBS_HARNESS_MANIFEST=str(harness_manifest), HF_FOBS_HARNESS_SHA=harness_hash or plan_hash,
            HF_FOBS_HARNESS_TEST=str(root / "aux/hf_repo/tests/test_force_reuse_contract.py"),
            HF_ARITHMETIC_HARNESS_ID="H1",
            HF_FCPU_CAMPAIGN_PROTOCOL=PROTOCOL, HF_FCPU_RUN_ID=RUN_ID)
        print(json.dumps(dict(phase=name, started_utc=utc(),
            remaining_campaign_seconds=deadline-begin, active_seconds_limit=active_deadline-begin)), flush=True)
        if sha(supervisor.__file__) != supervisor_sha:
            raise StopCampaign("source_not_pass", "Loaded supervisor source changed")
        observe = {}
        runner = supervisor.run_owned
        if bucket in {"P1", "P2"}:
            if (candidate is None or extended(candidate.__file__) != aux / "windows_owned_process_sup2.py"
                    or sha(candidate.__file__) != CANDIDATE_SHA):
                raise StopCampaign("source_not_pass", "Scientific-phase candidate was not loaded from the verified frozen file")
            identity = dict(campaign_protocol=PROTOCOL, run_id=RUN_ID, phase=name,
                version="R1", science_version="R1", source_version="R1",
                source_manifest_sha256=manifest_hash, harness_id="HR1", harness_manifest_sha256=harness_hash,
                arithmetic_harness_id="H1",
                candidate_supervisor=candidate_identity, supervisor_version="SUP2", supervisor_sha256_role="P1_P2_candidate")
            request = dict(schema="hf-force-cpu-supervision-request-1", campaign_protocol=PROTOCOL,
                run_id=RUN_ID, identity=identity, command=list(command), cwd=str(root),
                deadline_monotonic=active_deadline, seconds=active_seconds, rss_limit_bytes=RSS_LIMIT,
                telemetry_interval_seconds=1.0 if bucket == "P2" else None,
                telemetry_enabled=bucket == "P2", candidate_supervisor=candidate_identity,
                parent_supervisor=parent_identity, loaded_parent_supervisor=loaded_parent)
            dump(root / "results" / (bucket + "_supervision") / "request.json", request)
            runner = candidate.run_owned
            observe = dict(instance_log_path=root / "results" / (bucket + "_supervision") / "instances.ndjson",
                instance_identity=identity)
            if bucket == "P2":
                observe.update(telemetry_path=root / "events/P2_force_cpu.ndjson",
                    telemetry_interval_seconds=1.0, telemetry_identity=identity)
                ledger["force_process_attempted"] = True
            else:
                ledger["local_contract_process_attempted"] = True
                ledger["P1_status"] = "running"
        try:
            raw_receipt = runner(command, cwd=str(root), env=runenv,
                log=root / "logs" / (name + ".log"), deadline=active_deadline,
                seconds=active_seconds, rss_limit=RSS_LIMIT, **observe)
        except BaseException:
            supervision_uncertain = True
            raise
        # Capture ownership uncertainty before the first fallible persistence
        # operation, even if there is no phase row yet.
        if not isinstance(raw_receipt, dict) or raw_receipt.get("cleanup_verified") is not True:
            supervision_uncertain = True
        if bucket in {"P1", "P2"} and (
                raw_receipt.get("protocol") != "F-CPU-CLEAN1"
                or raw_receipt.get("cleanup_contract") != "CPU-CLEAN1"
                or raw_receipt.get("candidate_supervisor") != candidate_identity
                or raw_receipt.get("supervisor_sha256") != CANDIDATE_SHA):
            supervision_uncertain = True
        if bucket not in {"P1", "P2"} and raw_receipt.get("supervisor_sha256") != PARENT_SHA:
            supervision_uncertain = True
        if bucket in {"P1", "P2"}:
            # Preserve the native SUP2 protocol, identity and timing before any
            # parent bookkeeping. The probe independently owns results/force.
            dump(root / "results" / (bucket + "_supervision") / "receipt.json", raw_receipt)
        receipt = dict(raw_receipt)
        receipt["owned_elapsed_seconds"] = receipt["elapsed_seconds"]
        receipt["elapsed_seconds"] = time.monotonic() - begin
        receipt.update(name=name, bucket=bucket, inclusive_phase_limit_seconds=LIMITS[bucket],
            elapsed_scope="parent phase entry through owned-process cleanup; includes WinAPI/setup",
            active_deadline_monotonic=active_deadline, source_version="SUP2" if bucket in {"P1", "P2"} else "SUP1",
            active_limit_kind="phase_inclusive_limit" if begin+active_seconds <= absolute else "campaign_seal_reserve",
            source_manifest_sha256=manifest_hash or plan_hash,
            harness_id="HR1", harness_manifest_sha256=harness_hash or plan_hash,
            arithmetic_harness_id="H1",
            science_version="R1", campaign_protocol=PROTOCOL, run_id=RUN_ID,
            supervisor_version="SUP2" if bucket in {"P1", "P2"} else "SUP1",
            supervisor_sha256_role="P1_P2_candidate" if bucket in {"P1", "P2"} else "parent_control",
            parent_supervisor=parent_identity, candidate_supervisor=candidate_identity,
            loaded_parent_supervisor=loaded_parent)
        if bucket in {"P1", "P2"}:
            receipt["native_receipt_sha256"] = sha(root / "results" / (bucket + "_supervision") / "receipt.json")
            if (raw_receipt.get("protocol") != "F-CPU-CLEAN1"
                    or raw_receipt.get("cleanup_contract") != "CPU-CLEAN1"
                    or raw_receipt.get("candidate_supervisor") != candidate_identity
                    or raw_receipt.get("supervisor_sha256") != CANDIDATE_SHA):
                supervision_uncertain = True
                receipt["cleanup_verified"] = False
                receipt["parent_identity_error"] = "Scientific-phase native supervisor identity differs"
        phases.append(receipt)
        save_ledger()
        print(json.dumps(dict(phase=name, reason=receipt["reason"], returncode=receipt["returncode"],
            seconds=receipt["elapsed_seconds"], peak_rss_bytes=receipt["peak_tree_rss_bytes"],
            cleanup_verified=receipt["cleanup_verified"])), flush=True)
        if receipt["reason"] in FATAL or not receipt["cleanup_verified"]:
            raise StopCampaign("resource_or_supervision_stop", name + ": " + receipt["reason"])
        if supervision_uncertain:
            raise StopCampaign("resource_or_supervision_stop", name + ": supervisor identity or ownership uncertain")
        if receipt["elapsed_seconds"] > LIMITS[bucket]:
            raise StopCampaign("resource_stop", name + " exceeded its inclusive phase limit")
        if bucket == "P2" and receipt.get("telemetry_status") != "complete":
            raise StopCampaign("evidence_failure", "Force telemetry is incomplete")
        if bucket == "P1" and receipt.get("telemetry_status") != "disabled":
            raise StopCampaign("evidence_failure", "Local contract unexpectedly collected CPU telemetry")
        if receipt["returncode"] != 0:
            raise StopCampaign("execution_failure", name + " returned " + str(receipt["returncode"]))
        return receipt

    def worker_command(action, *, frozen=True):
        def matches(candidate):
            files = {candidate.name:worker_sha, **worker_dependencies}
            return all((candidate.parent / name).is_file() and sha(candidate.parent / name) == digest
                       for name, digest in files.items())
        candidate = aux / "force_cpu_evidence.py" if frozen else original_worker
        if not matches(candidate):
            if action != "seal" or not matches(original_worker):
                raise StopCampaign("source_not_pass", "Evidence worker identity changed or missing")
            candidate = original_worker  # F0 partial failure: approved stdlib preservation only.
        return [sys.executable, "-u", "-B", str(candidate), "--root", str(root),
                "--repo", str(repo), "--action", action]

    def check_selection():
        if (sha(source_manifest) != manifest_hash or sha(harness_manifest) != harness_hash
                or sha(arithmetic_manifest) != arithmetic_hash
                or sha(candidate_manifest) != candidate_manifest_hash):
            raise StopCampaign("source_not_pass", "Frozen input or HR1 manifest changed")
        if (read(root / "selected_source.json") != selected
                or selected.get("protocol") != PROTOCOL or selected.get("campaign_protocol") != PROTOCOL
                or selected.get("run_id") != RUN_ID
                or selected.get("parent_supervisor") != parent_identity
                or selected.get("candidate_supervisor") != candidate_identity
                or selected.get("loaded_parent_supervisor") != loaded_parent
                or selected["version"] != "R1" or extended(selected["source"]) != source
                or extended(selected["source_manifest"]) != source_manifest
                or selected["source_manifest_sha256"] != manifest_hash
                or selected["harness"]["version"] != "HR1"
                or extended(selected["harness"]["manifest_path"]) != harness_manifest
                or selected["harness"]["manifest_sha256"] != harness_hash
                or selected["arithmetic_harness"]["version"] != "H1"
                or extended(selected["arithmetic_harness"]["manifest_path"]) != arithmetic_manifest
                or selected["arithmetic_harness"]["manifest_sha256"] != arithmetic_hash):
            raise StopCampaign("source_not_pass", "Selected science/HR1 identity differs")

    def load_evidence_reader():
        """Load only the frozen stdlib reader; no science or child process runs."""
        nonlocal frozen_worker
        filename = aux / "force_cpu_evidence.py"
        if sha(filename) != worker_sha:
            raise StopCampaign("source_not_pass", "Frozen evidence reader changed")
        if frozen_worker is None:
            name = "_frozen_force_cpu_evidence_reader"
            if name in sys.modules:
                raise StopCampaign("source_not_pass", "Evidence reader was loaded before admission")
            sys.path.insert(0, str(aux))
            spec = importlib.util.spec_from_file_location(name, filename)
            if spec is None or spec.loader is None:
                raise StopCampaign("source_not_pass", "Frozen evidence reader cannot be loaded")
            frozen_worker = importlib.util.module_from_spec(spec)
            sys.modules[name] = frozen_worker
            spec.loader.exec_module(frozen_worker)
        if extended(frozen_worker.__file__) != filename or sha(frozen_worker.__file__) != worker_sha:
            raise StopCampaign("source_not_pass", "Actual evidence reader identity differs")
        for name in ("force_observation_evidence.py", "s0_preparation_evidence.py", "s0_event_log.py"):
            module = sys.modules.get(name.removesuffix(".py"))
            if (module is None or extended(module.__file__) != aux / name
                    or sha(module.__file__) != worker_dependencies[name]):
                raise StopCampaign("source_not_pass", "Reader dependency outside frozen aux: " + name)
        return frozen_worker

    def check_native_binding(summary, record_key, filename, native_filename, phase, native_schema, expected_status):
        """Bind an unchanged native HR1 declaration to this actual execution."""
        record = summary[record_key]
        target, native_path = root / filename, root / native_filename
        if (extended(root / record["path"]) != target or record["bytes"] != target.stat().st_size
                or record["sha256"] != sha(target) or record["status"] != expected_status):
            raise StopCampaign("evidence_failure", "HR1 outer binding record differs")
        native = read(native_path)
        envelope = read(target)
        expected_native = dict(protocol=HR1_NATIVE_PROTOCOL, run_id=HR1_NATIVE_RUN_ID,
            schema=native_schema, path=native_filename, bytes=native_path.stat().st_size,
            sha256=sha(native_path), status=expected_status)
        expected = dict(schema="hf-force-reuse-harness-binding-1", protocol=PROTOCOL,
            campaign_protocol=PROTOCOL, run_id=RUN_ID, phase=phase, source_version="R1",
            source=str(source), source_manifest_sha256=manifest_hash,
            harness=selected["harness"], arithmetic_harness=selected["arithmetic_harness"],
            status=expected_status, scientific_admission=False, native=expected_native)
        if envelope != expected or any(native.get(k) != expected_native[k]
                                      for k in ("protocol", "run_id", "schema", "status")):
            raise StopCampaign("evidence_failure", "Current campaign or fixed native HR1 identity differs")
        return native

    def verify_frozen_inputs():
        check_selection()
        manifest = read(source_manifest)
        if (manifest.get("schema") != "hf-force-cpu-inputs-1"
                or manifest.get("protocol") != PROTOCOL or manifest.get("campaign_protocol") != PROTOCOL
                or manifest.get("run_id") != RUN_ID or len(manifest["files"]) != 347
                or manifest.get("parent_supervisor") != parent_identity
                or manifest.get("candidate_supervisor") != candidate_identity
                or manifest.get("loaded_parent_supervisor") != loaded_parent):
            raise StopCampaign("source_not_pass", "New source inventory or supervisor roles differ")
        names = set()
        for row in manifest["files"]:
            frozen = extended(root / row["path"])
            if row["path"] in names or not frozen.is_relative_to(root):
                raise StopCampaign("source_not_pass", "Duplicate or escaping manifest path")
            names.add(row["path"])
            for actual in (frozen, extended(row["source"])):
                if actual.stat().st_size != row["bytes"] or sha(actual) != row["sha256"]:
                    raise StopCampaign("source_not_pass", "Input source or frozen copy changed: " + row["path"])
        derived = manifest.get("derived_files")
        inherited = manifest.get("inherited_candidate_files", [])
        candidate_record = read(candidate_manifest)
        if (derived != [] or len(inherited) != 32 or candidate_record.get("files") != inherited
                or manifest.get("new_patch_applications") != 0
                or candidate_record.get("new_patch_applications") != 0
                or candidate_record.get("inherited_candidate_files") != 32
                or candidate_record.get("schema") != "hf-force-reuse-candidate-relocation-1"
                or candidate_record.get("version") != "R1"
                or extended(candidate_record["source"]) != source):
            raise StopCampaign("source_not_pass", "Inherited R1 inventory or zero-patch identity differs")
        inherited_names = set()
        for row in inherited:
            frozen = extended(root / row["path"])
            if (row["path"] not in names or row["path"] in inherited_names or not frozen.is_relative_to(source)
                    or frozen.stat().st_size != row["bytes"] or sha(frozen) != row["sha256"]):
                raise StopCampaign("source_not_pass", "Inherited R1 frozen source changed: " + row["path"])
            inherited_names.add(row["path"])
        if (sha(source / "src/hf_eval/split_kernel_invariants_hu.py") != R1_KERNEL_SHA
                or sha(root / "aux/hf_repo/tests/test_force_reuse_contract.py") != HR1_TEST_SHA):
            raise StopCampaign("source_not_pass", "Fixed R1 or HR1 bytes differ")
        for key in ("patch", "proof", "upstream_manifest"):
            row = candidate_record[key]
            frozen = extended(root / row["path"])
            if not frozen.is_relative_to(root) or sha(frozen) != row["sha256"]:
                raise StopCampaign("source_not_pass", "R1 derivation proof or patch differs")
        for section, count in (("runtime_file_checks", 3), ("stdlib_file_checks", 1)):
            rows = manifest[section]
            if len(rows) != count:
                raise StopCampaign("source_not_pass", "Pinned runtime inventory differs: " + section)
            for row in rows:
                filename = extended(row["path"])
                if filename.stat().st_size != row["bytes"] or sha(filename) != row["sha256"]:
                    raise StopCampaign("source_not_pass", "Runtime source changed: " + str(filename))
        for row in manifest["canonical_files"].values():
            if sha(extended(row["path"])) != row["sha256"]:
                raise StopCampaign("source_not_pass", "Canonical science or H1 changed")
        for name, digest in (("windows_owned_process.py", PARENT_SHA),
                             ("windows_owned_process_sup2.py", CANDIDATE_SHA),
                             ("cpu_supervision_evidence.py", PROOF_HELPER_SHA)):
            if sha(aux / name) != digest:
                raise StopCampaign("source_not_pass", "Fixed auxiliary bytes differ: " + name)
        reader = load_evidence_reader()
        if reader.verify_snapshot(root, repo).get("status") != "pass":
            raise StopCampaign("source_not_pass", "Frozen relocation/mapping contract did not pass")

    def load_candidate():
        nonlocal candidate
        filename = aux / "windows_owned_process_sup2.py"
        if candidate is not None or "windows_owned_process_sup2" in sys.modules:
            raise StopCampaign("source_not_pass", "Candidate module already loaded before its single permitted load")
        if not sys.dont_write_bytecode or sha(filename) != CANDIDATE_SHA:
            raise StopCampaign("source_not_pass", "Candidate identity or no-bytecode execution differs")
        spec = importlib.util.spec_from_file_location("windows_owned_process_sup2", filename)
        if spec is None or spec.loader is None:
            raise StopCampaign("source_not_pass", "Cannot resolve the frozen SUP2 module")
        candidate = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = candidate
        spec.loader.exec_module(candidate)
        loaded = dict(version="SUP2", path=str(extended(candidate.__file__)), sha256=sha(candidate.__file__))
        if loaded != candidate_identity:
            raise StopCampaign("source_not_pass", "Actually loaded candidate source differs")
        ledger["loaded_candidate_supervisor"] = loaded
        dump(root / "loaded_supervisors.json", dict(campaign_protocol=PROTOCOL, run_id=RUN_ID,
            parent_supervisor=parent_identity, candidate_supervisor=candidate_identity,
            loaded_parent_supervisor=loaded_parent, loaded_candidate_supervisor=loaded,
            source_manifest_sha256=manifest_hash, harness_manifest_sha256=harness_hash))

    try:
        if (supervisor_sha != PARENT_SHA or extended(supervisor.__file__) != repo / "hf_repo/scripts/windows_owned_process.py"
                or sha(repo / "hf_repo/scripts/windows_owned_process_sup2.py") != CANDIDATE_SHA
                or worker_dependencies["cpu_supervision_evidence.py"] != PROOF_HELPER_SHA):
            raise StopCampaign("source_not_pass", "Authorized fixed supervisors or proof helper differ")
        execute("P0_prepare", "P0", worker_command("prepare", frozen=False))
        manifest_hash, harness_hash = sha(source_manifest), sha(harness_manifest)
        arithmetic_hash, candidate_manifest_hash = sha(arithmetic_manifest), sha(candidate_manifest)
        selected = read(root / "selected_source.json")
        verify_frozen_inputs()
        load_candidate()
        execute("P1_local", "P1", [sys.executable, "-u", "-B", str(aux / "probe_force_cpu.py"),
                "--root", str(root), "--source", str(source), "--mode", "local"])
        verify_frozen_inputs()
        local = read(root / "results/local/summary.json")
        if (local.get("schema") != "hf-force-reuse-local-1" or local.get("status") != "pass"
                or local.get("protocol") != PROTOCOL or local.get("run_id") != RUN_ID
                or local.get("local_structure_equivalence_pass") is not True
                or local.get("source_manifest_sha256") != manifest_hash
                or extended(local["source"]) != source or local.get("harness") != selected["harness"]
                or local.get("arithmetic_harness") != selected["arithmetic_harness"]):
            raise StopCampaign("evidence_failure", "Local contract identity/outcome differs")
        local_record = local["contract_record"]
        contract_path = root / "results/local/contract.json"
        if (extended(root / local_record["path"]) != contract_path
                or contract_path.stat().st_size != local_record["bytes"]
                or sha(contract_path) != local_record["sha256"]
                or local_record["status"] != "local_structure_equivalence_pass"):
            raise StopCampaign("evidence_failure", "Local contract report binding differs")
        contract = check_native_binding(local, "contract_binding_record", "results/local/contract_binding.json",
            "results/local/contract.json", "P1_local", "hf-force-reuse-contract-1",
            "local_structure_equivalence_pass")
        expected_micro_stages = ["local."+version+"."+operation
            for version in ("C1", "R1") for operation in ("trace", "lower", "compile")]
        expected_micro_stages += ["local."+group+"."+version+"."+operation
            for group in MICRO_GROUPS for version in ("C1", "R1") for operation in ("call", "synchronize")]
        micro_stages = [step for step in local["steps"]
            if step["stage"].startswith("local.")
            and step["stage"].rsplit(".", 1)[-1] in {"trace", "lower", "compile", "call", "synchronize"}]
        numeric = contract.get("numpy", {})
        micro = contract.get("micro", {})
        if (contract.get("schema") != "hf-force-reuse-contract-1"
                or contract.get("status") != "local_structure_equivalence_pass"
                or contract.get("local_structure_equivalence_pass") is not True
                or contract.get("source_manifest_sha256") != manifest_hash
                or contract.get("harness") != selected["harness"]
                or contract.get("arithmetic_harness") != selected["arithmetic_harness"]
                or contract.get("static", {}).get("status") != "pass"
                or numeric.get("status") != "pass" or len(numeric.get("rows", [])) != 7
                or not all(row.get("status") == "pass" and set(row["fields"]) == OUTPUT_FIELDS
                           and all(field.get("status") == "pass" for field in row["fields"].values())
                           for row in numeric["rows"])
                or numeric.get("material_rejection", {}).get("status") != "pass"
                or contract.get("selector", {}).get("status") != "pass"
                or contract["selector"].get("extra_jit_count") != 0
                or len(contract["selector"].get("rows", [])) != 4
                or not all(row.get("status") == "pass" for row in contract["selector"]["rows"])
                or contract.get("reference", {}).get("status") != "pass"
                or len(contract["reference"].get("reference_checks", [])) != 3
                or not all(row.get("pass") is True for row in contract["reference"]["reference_checks"])
                or micro.get("status") != "pass"
                or (micro.get("micro_graph_count"), micro.get("micro_call_count"), micro.get("group_count")) != (2, 16, 8)
                or tuple(row["name"] for row in micro.get("groups", [])) != MICRO_GROUPS
                or not all(row.get("status") == "pass" and all(v.get("status") == "pass" for v in row["fields"].values())
                           for row in micro["groups"])
                or [step["stage"] for step in micro_stages] != expected_micro_stages
                or not all(step["status"] == "pass" for step in local["steps"])):
            raise StopCampaign("evidence_failure", "Local contract lacks its complete fixed numerical coverage")
        reader = load_evidence_reader()
        if reader.verify_local_contract(root).get("status") != "local_structure_equivalence_pass":
            raise StopCampaign("evidence_failure", "Full current local event/array contract did not pass")
        local_proof = reader.supervision_phase(root, repo, {"phases": phases}, "P1_local")
        if local_proof.get("status") != "verified_all_instances":
            supervision_uncertain = True
            raise StopCampaign("resource_or_supervision_stop", "P1 raw same-instance cleanup proof failed")
        ledger["local_pre_force_supervision_proof"] = local_proof
        ledger.update(P1_status="local_structure_equivalence_pass", local_structure_equivalence_pass=True)
        save_ledger()
        execute("P2_force", "P2", [sys.executable, "-u", "-B", str(aux / "probe_force_cpu.py"),
                "--root", str(root), "--source", str(source), "--mode", "force"])
        verify_frozen_inputs()
        summary = read(root / "results/force/summary.json")
        if (summary["schema"] != "hf-force-cpu-probe-1" or summary["status"] != "pass"
                or summary.get("protocol") != PROTOCOL or summary.get("run_id") != RUN_ID
                or summary["source_manifest_sha256"] != manifest_hash
                or extended(summary["source"]) != source or summary["harness"] != selected["harness"]
                or summary.get("arithmetic_harness") != selected["arithmetic_harness"]):
            raise StopCampaign("evidence_failure", "Force summary identity/outcome differs")
        force_record = summary["force_reference_gates"]
        force_path = root / "results/force/three_force_gates.json"
        force_checks = check_native_binding(summary, "force_reference_gates_binding",
            "results/force/three_force_gates_binding.json", "results/force/three_force_gates.json",
            "P2_force", "hf-force-reuse-reference-gates-1", "fixed_force_three_reference_gates_pass")
        if (extended(root / force_record["path"]) != force_path
                or force_path.stat().st_size != force_record["bytes"]
                or sha(force_path) != force_record["sha256"]
                or force_record["status"] != "fixed_force_three_reference_gates_pass"
                or force_checks.get("status") != "fixed_force_three_reference_gates_pass"
                or len(force_checks.get("checks", [])) != 3
                or {row["name"] for row in force_checks["checks"]} != {"total_force", "material_force", "regularization_force"}
                or not all(row.get("pass") is True for row in force_checks["checks"])):
            raise StopCampaign("evidence_failure", "Force reference gates binding/outcome differs")
        if load_evidence_reader().verify_force_reference_report(root, summary).get("status") != "fixed_force_three_reference_gates_pass":
            raise StopCampaign("evidence_failure", "Original Decimal force-gate contract did not pass")
        ledger["fixed_force_three_reference_gates_pass"] = True
        status = "fixed_force_three_reference_gates_pass_no_scientific_admission"
    except StopCampaign as problem:
        status, error = problem.status, dict(type=type(problem).__name__, message=str(problem))
    except BaseException as problem:
        status, error = "parent_exception", dict(type=type(problem).__name__, message=str(problem),
                                                traceback=traceback.format_exc())
    finally:
        # No further scientific calls are possible here, even after partial P0/P1.
        if ledger["P1_status"] == "running":
            ledger["P1_status"] = "stopped_or_failed"
        dump(root / "resources.json", dict(phases=phases, status=status, error=error,
            total_elapsed_seconds=time.monotonic()-start, plot_scope="before P3; final receipt includes P3"))
        clean = not supervision_uncertain and all(p["cleanup_verified"] for p in phases)
        if clean and shared_elapsed() <= 20. and time.monotonic() < deadline-10.25:
            try:
                execute("P3_seal", "P3", worker_command("seal"))
                proof = read(root / "supervision_proof.json")
                if (proof.get("protocol") != PROTOCOL or proof.get("campaign_protocol") != PROTOCOL
                        or proof.get("run_id") != RUN_ID
                        or proof.get("parent_supervisor") != parent_identity
                        or proof.get("candidate_supervisor") != candidate_identity
                        or proof.get("loaded_parent_supervisor") != loaded_parent):
                    raise StopCampaign("evidence_failure", "Scientific-phase supervision proof report identity differs")
                ledger["supervision_proof_status"] = proof["status"]
                seal_summary = read(root / "results/seal/summary.json")
                if status == "fixed_force_three_reference_gates_pass_no_scientific_admission" and (
                        proof["status"] != "verified_all_instances"
                        or proof.get("complete_two_phases") is not True
                        or seal_summary.get("status") != "pass"
                        or seal_summary.get("force_observation", {}).get("status")
                            != "complete_fixed_force_no_scientific_admission"):
                    raise StopCampaign("evidence_failure", "Fixed force completion lacks full sealed proof")
            except BaseException as problem:
                error = dict(prior=error, seal_error=dict(type=type(problem).__name__, message=str(problem)))
                status = problem.status if isinstance(problem, StopCampaign) else "seal_failure"
        else:
            error = dict(prior=error, seal_error="No safe cleanup/time margin for P3")
            if status == "fixed_force_three_reference_gates_pass_no_scientific_admission":
                status = "resource_stop"
        if time.monotonic() > deadline or shared_elapsed() > LIMITS["shared"]:
            status = "resource_stop"
        ledger.update(status=status, error=error, finished_utc=utc(), elapsed_seconds=time.monotonic()-start,
            selected_source=selected, source_manifest_sha256=manifest_hash, harness_manifest_sha256=harness_hash,
            shared_elapsed_seconds=shared_elapsed(), scientific_admission=False)
        replace(root / "ledger.json", ledger)
        dump(root / "execution_receipt.json", ledger)
        optional_sha = lambda name: sha(root / name) if (root / name).is_file() else None
        binding = dict(schema="hf-force-cpu-receipt-binding-1",
            protocol=PROTOCOL, campaign_protocol=PROTOCOL, run_id=RUN_ID,
            plan_sha256=plan_hash, input_manifest_sha256=optional_sha("input_manifest.json"),
            harness_manifest_sha256=optional_sha("HR1/manifest.json"),
            arithmetic_harness_manifest_sha256=optional_sha("H1/manifest.json"),
            selected_source_sha256=optional_sha("selected_source.json"),
            receipt_sha256=sha(root / "execution_receipt.json"),
            output_manifest_sha256=optional_sha("output_sha256.json"),
            cpu_observation_sha256=optional_sha("cpu_observation.json"),
            cpu_trace_sha256=optional_sha("events/P2_force_cpu.ndjson"),
            supervision_receipt_sha256=optional_sha("results/P2_supervision/receipt.json"),
            instance_trace_sha256=optional_sha("results/P2_supervision/instances.ndjson"),
            supervision_proof_sha256=optional_sha("supervision_proof.json"),
            loaded_supervisors_sha256=optional_sha("loaded_supervisors.json"),
            local_supervision_receipt_sha256=optional_sha("results/P1_supervision/receipt.json"),
            local_instance_trace_sha256=optional_sha("results/P1_supervision/instances.ndjson"),
            local_contract_sha256=optional_sha("results/local/summary.json"),
            local_contract_details_sha256=optional_sha("results/local/contract.json"),
            local_contract_binding_sha256=optional_sha("results/local/contract_binding.json"),
            force_reference_checks_sha256=optional_sha("results/force/three_force_gates.json"),
            force_reference_binding_sha256=optional_sha("results/force/three_force_gates_binding.json"),
            candidate_derivation_sha256=optional_sha("provenance/force_reuse_001/R1/proof.json"),
            candidate_manifest_sha256=optional_sha("R1/source_manifest.json"),
            inheritance_manifest_sha256=optional_sha("inheritance_manifest.json"),
            seal_event_sha256=optional_sha("events/P3_seal.ndjson"), seal_log_sha256=optional_sha("logs/P3_seal.log"),
            sealed_utc=utc(), elapsed_campaign_seconds=time.monotonic()-start,
            diagnostic_only=True, scientific_admission=False)
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
    return 0 if status == "fixed_force_three_reference_gates_pass_no_scientific_admission" else 1


if __name__ == "__main__":
    raise SystemExit(main())
