"""F-COST1: one 240-second diagnostic window; immutable R1/HR1/H1/SUPs.

The parent owns supervision and byte bindings, never scientific evaluation.
Authoring/static review must finish before this entry point runs once.
"""
from __future__ import annotations

import time

_ENTRY_START = time.monotonic()

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import traceback

import psutil
import windows_owned_process as supervisor

PROTOCOL = "F-COST1"
RUN_ID = "force_cost_001"
CARD = "docs/HF4_C2_S0_PREPARATION_RESULT_20260928.md"
LIMITS = {"P0": 25., "P1": 165., "P3": 25., "shared": 25.}
SECONDS = 240.
RSS_LIMIT = 8 * 1024**3
GUARD = 5.25
PARENT_SHA = "9f3da2f22bec869d069278058aa8502bd5f73c4b977b01ec5daa7b26ff1aec32"
CANDIDATE_SHA = "b5f149e1cd3d6d9b4ad392123e410b786606f120f2e078139b7bacc97f2d9499"
PROOF_HELPER_SHA = "2d378c64705461d58fa966528a347b6e411431402877663fd546f3fec8912f45"
PRIOR_BINDING_SHA = "b223ad7b85c9b3f561ffcb609fd8155866cee9e4f368dc4cd2dde3da00f4f856"
EXCLUSIONS = ("output_sha256.json", "receipt_binding.json", "execution_receipt.json",
              "ledger.json", "events/P3_seal.ndjson", "logs/P3_seal.log")
EXPECTED_COUNTS = dict(graph_count=2, trace=2, lower=2, compile=2, compiled_call=4,
    output_synchronization=4, ready_only=2, input_ready=1, micro_leaf_count=24,
    warmup=0, retries=0, force_calls=0, ad_calls=0)


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


def utc():
    return datetime.now(timezone.utc).isoformat()


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
    if root != repo / "hf4_c2_stable_f_validation" / RUN_ID or root.exists():
        raise RuntimeError("Refuse another, existing, or reset campaign directory")
    if root == repo or repo.is_relative_to(root):
        raise RuntimeError("Evidence root cannot contain the repository")

    source, aux = root / "R1/source/hf_repo", root / "aux/hf_repo/scripts"
    worker_original = repo / "hf_repo/scripts/force_cost_evidence.py"
    worker_sha = sha(worker_original)
    dependencies = {name: sha(worker_original.parent / name) for name in (
        "cpu_supervision_evidence.py", "s0_preparation_evidence.py", "s0_event_log.py",
        "probe_s0_preparation.py", "s0_ad_exception.py", "windows_owned_process.py",
        "windows_owned_process_sup2.py")}
    parent_identity = dict(version="SUP1", path=str(aux / "windows_owned_process.py"), sha256=PARENT_SHA)
    candidate_identity = dict(version="SUP2", path=str(aux / "windows_owned_process_sup2.py"), sha256=CANDIDATE_SHA)
    loaded_parent = dict(version="SUP1", path=str(extended(supervisor.__file__)), sha256=sha(supervisor.__file__))
    # Read-only preflight; no preparation, test, science import or root exists.
    if (loaded_parent["sha256"] != PARENT_SHA
            or extended(supervisor.__file__) != repo / "hf_repo/scripts/windows_owned_process.py"
            or dependencies["windows_owned_process_sup2.py"] != CANDIDATE_SHA
            or dependencies["cpu_supervision_evidence.py"] != PROOF_HELPER_SHA):
        raise RuntimeError("Authorized fixed supervisors/helper differ before launch")
    card_hash, runner_hash = sha(repo / CARD), sha(__file__)
    # The single clock includes parent imports/preflight and starts before all
    # directory/preparation mutations; never restart it after a phase.
    start = _ENTRY_START
    deadline = start + SECONDS
    root.mkdir(parents=True)
    for name in ("events", "logs", "results"):
        (root / name).mkdir()
    phases, attempted = [], set()
    status, error, uncertain = "running", None, False
    candidate = reader = None
    selected = None
    manifest_hash = harness_hash = None
    ledger = dict(schema="hf-force-cost-campaign-1", protocol=PROTOCOL, campaign_protocol=PROTOCOL,
        run_id=RUN_ID, status=status, started_utc=utc(), start_monotonic=start,
        deadline_monotonic=deadline, seconds=SECONDS, rss_limit_bytes=RSS_LIMIT,
        limits_seconds=LIMITS, cleanup_and_poll_guard_seconds=GUARD,
        final_binding_reserved_seconds=5., phases=phases, scientific_admission=False,
        parent_supervisor=parent_identity, candidate_supervisor=candidate_identity,
        loaded_parent_supervisor=loaded_parent, loaded_candidate_supervisor=None,
        P1_status="not_reached", supervision_proof_status="not_reached",
        force_calls=0, ad_calls=0, new_equilibrium_paths=0, new_hp_evaluations=0,
        new_patch_applications=0, execution_contract=EXPECTED_COUNTS)
    ledger["first_stop"] = None
    dump(root / "plan.json", dict(ledger, repo=str(repo), python=sys.version,
        card_sha256=card_hash, runner_sha256=runner_hash,
        evidence_worker_sha256=worker_sha, evidence_worker_dependency_sha256=dependencies,
        boot_time_estimate=psutil.boot_time(), prior_campaign="force_reuse_002",
        prior_binding_sha256=PRIOR_BINDING_SHA, science_version="R1", harness_version="HR1",
        arithmetic_harness_version="H1", supervisor_sha256=CANDIDATE_SHA,
        supervisor_sha256_role="P1_candidate", telemetry_interval_seconds=1.,
        telemetry_scope="owned Job CPU; parent CPU excluded", original_tests_rerun=False,
        non_seal_active_deadline=deadline-35.25, seal_active_deadline=deadline-10.25,
        output_manifest_exclusions=list(EXCLUSIONS)))
    plan_hash = sha(root / "plan.json")
    dump(root / "ledger.json", ledger)
    env = os.environ.copy()
    env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONUNBUFFERED="1", PYTHONNOUSERSITE="1",
        PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", JAX_ENABLE_X64="true", JAX_TRACEBACK_FILTERING="off",
        JAX_ENABLE_COMPILATION_CACHE="false", JAX_PLATFORMS="cpu", OMP_NUM_THREADS="1",
        OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", MPLBACKEND="Agg",
        MPLCONFIGDIR=str(root / "matplotlib-cache"))

    def shared():
        return time.monotonic()-start-sum(row["elapsed_seconds"] for row in phases)

    def save_ledger():
        ledger.update(status=status, error=error, elapsed_seconds=time.monotonic()-start,
            shared_elapsed_seconds=shared(), supervision_uncertain=uncertain,
            consumed_phase_seconds={key: sum(row["elapsed_seconds"] for row in phases if row["bucket"] == key)
                                    for key in ("P0", "P1", "P3")})
        replace(root / "ledger.json", ledger)

    def worker_command(action, frozen=True):
        filename = aux / "force_cost_evidence.py" if frozen else worker_original
        def matches(path):
            return all((path.parent / name).is_file() and sha(path.parent / name) == digest
                       for name, digest in {"force_cost_evidence.py": worker_sha, **dependencies}.items())
        if not matches(filename):
            if action != "seal" or not matches(worker_original):
                raise StopCampaign("source_not_pass", "Evidence worker or its pinned dependencies changed")
            filename = worker_original  # Partial P0 failure: stdlib preservation, no science.
        return [sys.executable, "-u", "-B", str(filename), "--root", str(root), "--repo", str(repo), "--action", action]

    def execute(name, bucket, command):
        nonlocal uncertain
        if name in attempted:
            raise StopCampaign("execution_failure", "A phase cannot run twice: " + name)
        if shared() > 20.:
            raise StopCampaign("resource_stop", "Pre-seal shared allowance exhausted")
        begin = time.monotonic()
        active_seconds = LIMITS[bucket] - GUARD
        reserve_deadline = deadline - (10.25 if bucket == "P3" else 35.25)
        active_deadline = min(begin+active_seconds, reserve_deadline)
        if active_deadline <= begin:
            raise StopCampaign("resource_stop", "No permitted active/cleanup interval remains")
        attempted.add(name)
        runenv = env.copy()
        runenv.update(PYTHONPATH=str(source / "src")+os.pathsep+str(aux),
            HF_S0_EVENT_FILE=str(root / "events" / (name + ".ndjson")), HF_S0_PHASE=name,
            HF_S0_VERSION="R1", HF_S0_SOURCE_MANIFEST_SHA=manifest_hash or plan_hash,
            HF_HARNESS_ID="HR1", HF_HARNESS_MANIFEST_SHA=harness_hash or plan_hash,
            HF_ARITHMETIC_HARNESS_ID="H1", HF_FCPU_CAMPAIGN_PROTOCOL=PROTOCOL, HF_FCPU_RUN_ID=RUN_ID)
        print(json.dumps(dict(phase=name, started_utc=utc(), active_seconds_limit=active_deadline-begin)), flush=True)
        if loaded_parent != dict(version="SUP1", path=str(extended(supervisor.__file__)), sha256=sha(supervisor.__file__)):
            raise StopCampaign("source_not_pass", "Loaded parent source changed")
        observe = {}
        run_owned = supervisor.run_owned
        if bucket == "P1":
            if candidate is None or extended(candidate.__file__) != aux / "windows_owned_process_sup2.py" or sha(candidate.__file__) != CANDIDATE_SHA:
                raise StopCampaign("source_not_pass", "P1 candidate is not the pinned frozen SUP2")
            identity = dict(campaign_protocol=PROTOCOL, run_id=RUN_ID, phase=name, version="R1",
                science_version="R1", source_version="R1", source_manifest_sha256=manifest_hash,
                harness_id="HR1", harness_manifest_sha256=harness_hash, arithmetic_harness_id="H1",
                candidate_supervisor=candidate_identity, supervisor_version="SUP2", supervisor_sha256_role="P1_candidate")
            dump(root / "results/P1_supervision/request.json", dict(schema="hf-force-cost-supervision-request-1",
                campaign_protocol=PROTOCOL, run_id=RUN_ID, identity=identity, command=list(command), cwd=str(root),
                deadline_monotonic=active_deadline, seconds=active_seconds, rss_limit_bytes=RSS_LIMIT,
                telemetry_enabled=True, telemetry_interval_seconds=1., candidate_supervisor=candidate_identity,
                parent_supervisor=parent_identity, loaded_parent_supervisor=loaded_parent))
            run_owned = candidate.run_owned
            observe = dict(instance_log_path=root / "results/P1_supervision/instances.ndjson",
                instance_identity=identity, telemetry_path=root / "events/P1_cost_cpu.ndjson",
                telemetry_interval_seconds=1., telemetry_identity=identity)
            ledger["P1_status"] = "running"
        try:
            raw = run_owned(command, cwd=str(root), env=runenv, log=root / "logs" / (name + ".log"),
                deadline=active_deadline, seconds=active_seconds, rss_limit=RSS_LIMIT, **observe)
        except BaseException:
            uncertain = True
            raise
        # Lock ownership uncertainty before any fallible disk/hash operation.
        if not isinstance(raw, dict) or raw.get("cleanup_verified") is not True:
            uncertain = True
        if bucket == "P1" and (raw.get("protocol") != "F-CPU-CLEAN1" or raw.get("cleanup_contract") != "CPU-CLEAN1"
                or raw.get("candidate_supervisor") != candidate_identity or raw.get("supervisor_sha256") != CANDIDATE_SHA):
            uncertain = True
        if bucket != "P1" and raw.get("supervisor_sha256") != PARENT_SHA:
            uncertain = True
        if bucket == "P1":
            dump(root / "results/P1_supervision/receipt.json", raw)
        row = dict(raw, owned_elapsed_seconds=raw["elapsed_seconds"], elapsed_seconds=time.monotonic()-begin,
            name=name, bucket=bucket, inclusive_phase_limit_seconds=LIMITS[bucket],
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
            row["native_receipt_sha256"] = sha(root / "results/P1_supervision/receipt.json")
        phases.append(row)
        save_ledger()
        print(json.dumps(dict(phase=name, reason=row["reason"], returncode=row["returncode"],
            elapsed_seconds=row["elapsed_seconds"], peak_rss_bytes=row["peak_tree_rss_bytes"], cleanup_verified=row["cleanup_verified"])), flush=True)
        if uncertain or row["reason"] != "normal_exit" or not row["cleanup_verified"]:
            raise StopCampaign("resource_or_supervision_stop", name + ": " + row["reason"])
        if row["elapsed_seconds"] > LIMITS[bucket]:
            raise StopCampaign("resource_stop", name + " exceeded its inclusive limit")
        if row.get("telemetry_status") != ("complete" if bucket == "P1" else "disabled"):
            raise StopCampaign("evidence_failure", name + " telemetry contract differs")
        if row["returncode"] != 0:
            raise StopCampaign("execution_failure", name + " exit=" + str(row["returncode"]))
        return row

    def load_frozen(name, filename, digest):
        if name in sys.modules or sha(filename) != digest or not sys.dont_write_bytecode:
            raise StopCampaign("source_not_pass", "Module previously loaded or bytes changed: " + name)
        spec = importlib.util.spec_from_file_location(name, filename)
        if spec is None or spec.loader is None:
            raise StopCampaign("source_not_pass", "Cannot load pinned frozen module")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        if extended(module.__file__) != filename or sha(module.__file__) != digest:
            raise StopCampaign("source_not_pass", "Actual loaded module differs")
        return module

    try:
        if loaded_parent["sha256"] != PARENT_SHA or extended(supervisor.__file__) != repo / "hf_repo/scripts/windows_owned_process.py" or dependencies["windows_owned_process_sup2.py"] != CANDIDATE_SHA or dependencies["cpu_supervision_evidence.py"] != PROOF_HELPER_SHA:
            raise StopCampaign("source_not_pass", "Fixed supervisor/helper identity differs")
        execute("P0_prepare", "P0", worker_command("prepare", frozen=False))
        sys.path.insert(0, str(aux))
        reader = load_frozen("_frozen_force_cost_evidence", aux / "force_cost_evidence.py", worker_sha)
        reader.verify_inputs(root, include_live=True)
        selected = read(root / "selected_source.json")
        manifest_hash = sha(root / "input_manifest.json")
        harness_hash = sha(root / "HR1/manifest.json")
        candidate = load_frozen("windows_owned_process_sup2", aux / "windows_owned_process_sup2.py", CANDIDATE_SHA)
        loaded_candidate = dict(version="SUP2", path=str(extended(candidate.__file__)), sha256=sha(candidate.__file__))
        if loaded_candidate != candidate_identity:
            raise StopCampaign("source_not_pass", "Loaded SUP2 identity differs")
        ledger["loaded_candidate_supervisor"] = loaded_candidate
        dump(root / "loaded_supervisors.json", dict(campaign_protocol=PROTOCOL, run_id=RUN_ID,
            parent_supervisor=parent_identity, candidate_supervisor=candidate_identity,
            loaded_parent_supervisor=loaded_parent, loaded_candidate_supervisor=loaded_candidate,
            source_manifest_sha256=manifest_hash, harness_manifest_sha256=harness_hash))
        execute("P1_cost", "P1", [sys.executable, "-u", "-B", str(aux / "probe_force_cost.py"),
            "--root", str(root), "--source", str(source)])
        reader.verify_inputs(root, include_live=True)
        try:
            proof = reader.verify_supervision(root)
        except BaseException:
            uncertain = True
            raise
        dump(root / "supervision_proof.json", proof)
        ledger["supervision_proof_status"] = "verified_all_instances"
        probe = read(root / "results/cost/summary.json")
        if probe.get("schema") != "hf-force-cost-probe-1" or probe.get("status") != "runtime_cost_diagnostic_complete" or probe.get("runtime_cost_diagnostic_complete") is not True or probe.get("protocol") != PROTOCOL or probe.get("run_id") != RUN_ID or probe.get("execution_contract") != EXPECTED_COUNTS:
            raise StopCampaign("evidence_failure", "Diagnostic probe contract/status differs")
        ledger["P1_status"] = "runtime_cost_diagnostic_complete"
        status = "runtime_cost_diagnostic_complete"
    except StopCampaign as exc:
        status, error = exc.status, str(exc)
    except BaseException as exc:
        status, error = "evidence_or_execution_failure", type(exc).__name__ + ": " + str(exc)
        traceback.print_exc()
    finally:
        # Partial outcomes stay partial. No later seal may erase the first stop.
        if status != "runtime_cost_diagnostic_complete":
            ledger["first_stop"] = dict(status=status, error=error, monotonic=time.monotonic())
        if ledger["P1_status"] == "running":
            ledger["P1_status"] = "not_complete"
        save_ledger()
        resources = dict(schema="hf-force-cost-resources-1", protocol=PROTOCOL, run_id=RUN_ID,
            status=status, parent_status=status, total_elapsed_seconds=time.monotonic()-start,
            elapsed_seconds=time.monotonic()-start, scope="preseal", phases=phases,
            peak_tree_rss_bytes=max((row["peak_tree_rss_bytes"] for row in phases), default=0),
            rss_limit_bytes=RSS_LIMIT, shared_elapsed_seconds=shared())
        dump(root / "resources.json", resources)
        safe_seal = not uncertain and all(row.get("cleanup_verified") is True for row in phases)
        if safe_seal and shared() <= 20. and time.monotonic() < deadline-10.25:
            try:
                execute("P3_seal", "P3", worker_command("seal"))
                seal = read(root / "results/seal/summary.json")
                if (seal.get("status") != "pass" or (status == "runtime_cost_diagnostic_complete"
                        and seal.get("diagnostic_status") != "runtime_cost_diagnostic_complete")):
                    raise StopCampaign("evidence_failure", "Preservation did not pass")
            except BaseException as exc:
                if status == "runtime_cost_diagnostic_complete":
                    status, error = "evidence_failure", "Seal: " + type(exc).__name__ + ": " + str(exc)
                else:
                    ledger["seal_error"] = type(exc).__name__ + ": " + str(exc)
        else:
            ledger["seal_skipped"] = "ownership uncertain or shared/final reserve exhausted"
            if status == "runtime_cost_diagnostic_complete":
                status, error = "evidence_failure", ledger["seal_skipped"]
        if time.monotonic() >= deadline or shared() > LIMITS["shared"]:
            status, error = "resource_stop", "Campaign or shared allowance exhausted during final preservation"
        if status != "runtime_cost_diagnostic_complete" and ledger["first_stop"] is None:
            ledger["first_stop"] = dict(status=status, error=error, monotonic=time.monotonic())
        save_ledger()
        # The same frozen parent receipt binds final status; no recomputation.
        dump(root / "execution_receipt.json", read(root / "ledger.json"))
        def record(rel):
            filename = root / rel
            return dict(path=rel, bytes=filename.stat().st_size, sha256=sha(filename)) if filename.is_file() else None
        targets = ("plan.json", "input_manifest.json", "selected_source.json", "R1/source_manifest.json",
            "HR1/manifest.json", "H1/manifest.json", "inheritance_manifest.json", "loaded_supervisors.json",
            "resources.json", "execution_receipt.json", "output_sha256.json", "results/prepare/summary.json",
            "results/cost/summary.json", "results/cost/interval_controls.json", "results/cost/environment.json",
            "results/cost/runtime_config.json", "results/cost/tiny_raw_jaxpr.txt",
            "results/cost/tiny_stablehlo.mlir", "results/cost/tiny_optimized_hlo.txt",
            "results/cost/micro_raw_jaxpr.txt", "results/cost/micro_stablehlo.mlir",
            "results/cost/micro_optimized_hlo.txt", "results/cost/tiny_before.npz",
            "results/cost/micro_first.npz", "results/cost/micro_repeat.npz", "results/cost/tiny_after.npz",
            "results/P1_supervision/request.json", "results/P1_supervision/receipt.json",
            "results/P1_supervision/instances.ndjson", "events/P1_cost_cpu.ndjson", "events/P1_cost.ndjson",
            "supervision_proof.json", "cpu_observation.json", "artifact_status.json",
            "diagnostic_verification.json", "source_preservation.json", "results/seal/summary.json",
            "events/P3_seal.ndjson", "logs/P3_seal.log")
        binding = dict(schema="hf-force-cost-receipt-binding-1", protocol=PROTOCOL, run_id=RUN_ID,
            status=status, scientific_admission=False, records={rel:record(rel) for rel in targets},
            prior_binding_sha256=PRIOR_BINDING_SHA, output_manifest_exclusions=list(EXCLUSIONS),
            binding_completion_monotonic=time.monotonic(), elapsed_before_binding_seconds=time.monotonic()-start)
        dump(root / "receipt_binding.json", binding)
        if time.monotonic() >= deadline or shared() > LIMITS["shared"]:
            # One bounded failure receipt rewrite, no phase/science retry.
            status, error = "resource_stop", "Final binding completed outside authorized allowance"
            if ledger["first_stop"] is None:
                ledger["first_stop"] = dict(status=status, error=error, monotonic=time.monotonic())
            save_ledger()
            replace(root / "execution_receipt.json", read(root / "ledger.json"))
            binding.update(status=status, binding_completion_monotonic=time.monotonic(),
                elapsed_before_binding_seconds=time.monotonic()-start)
            binding["records"]["execution_receipt.json"] = record("execution_receipt.json")
            replace(root / "receipt_binding.json", binding)
        print(json.dumps(dict(protocol=PROTOCOL, run_id=RUN_ID, status=status, error=error,
            elapsed_seconds=time.monotonic()-start, root=str(root), scientific_admission=False)), flush=True)
    return 0 if status == "runtime_cost_diagnostic_complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
