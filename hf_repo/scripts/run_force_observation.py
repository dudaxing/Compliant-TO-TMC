"""F-OBS-1: one authorized 300-second fixed-force observation, no retries.

Only auxiliary preparation, one cold force process, and preservation may run.
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

import psutil
from windows_owned_process import run_owned


CARD = "docs/HF4_C2_S0_PREPARATION_RESULT_20260928.md"
LIMITS = {"F0": 15., "F1": 245., "F2": 25., "shared": 15.}
RSS_LIMIT = 8 * 1024**3
CLEANUP_GUARD = 5.25
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

    start = time.monotonic()
    deadline = start + 300.
    root.mkdir(parents=True)
    for name in ("events", "logs", "results"):
        (root / name).mkdir()
    phases, attempted = [], set()
    status, error = "running", None
    supervision_uncertain = False
    source = root / "C1/source/hf_repo"
    aux = root / "aux/hf_repo/scripts"
    original_worker = repo / "hf_repo/scripts/force_observation_evidence.py"
    worker_sha = sha(original_worker)
    worker_dependencies = {name:sha(original_worker.parent / name) for name in
                           ("s0_preparation_evidence.py", "s0_event_log.py")}
    source_manifest = root / "input_manifest.json"
    harness_manifest = root / "H1/manifest.json"
    selected = None
    manifest_hash = harness_hash = None
    ledger = dict(schema="hf-force-observation-campaign-1", protocol="F-OBS-1", status=status,
        started_utc=utc(), start_monotonic=start, deadline_monotonic=deadline,
        seconds=300., rss_limit_bytes=RSS_LIMIT, limits_seconds=LIMITS,
        cleanup_and_poll_guard_seconds=CLEANUP_GUARD, final_binding_reserved_seconds=5.,
        boot_time_estimate=psutil.boot_time(), phases=phases, scientific_admission=False,
        force_call_limit=1, new_equilibrium_paths=0, new_hp_evaluations=0)
    dump(root / "plan.json", dict(ledger, repo=str(repo), python=sys.version,
        card_sha256=sha(repo / CARD), evidence_worker_sha256=worker_sha,
        evidence_worker_dependency_sha256=worker_dependencies,
        supervisor_sha256=sha(repo / "hf_repo/scripts/windows_owned_process.py"),
        runner_sha256=sha(__file__), prior_campaign="jit_ad_ready_001",
        science_version="C1", harness_version="H1", representative="unit__near_rotation",
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
                for key in ("F0", "F1", "F2")}, shared_elapsed_seconds=shared_elapsed())
        replace(root / "ledger.json", ledger)

    def execute(name, bucket, command):
        nonlocal supervision_uncertain
        if name in attempted:
            raise StopCampaign("execution_failure", "No phase may run twice: " + name)
        if bucket != "F2" and shared_elapsed() > 10.:
            raise StopCampaign("resource_stop", "Pre-seal shared allowance exhausted")
        begin = time.monotonic()
        active_seconds = LIMITS[bucket] - CLEANUP_GUARD
        absolute = deadline - (10.25 if bucket == "F2" else 35.25)
        active_deadline = min(begin+active_seconds, absolute)
        if active_deadline <= begin:
            raise StopCampaign("resource_stop", "No active/cleanup time remains for " + name)
        attempted.add(name)
        runenv = env.copy()
        runenv.update(PYTHONPATH=str(source / "src")+os.pathsep+str(aux),
            HF_S0_EVENT_FILE=str(root / "events" / (name + ".ndjson")),
            HF_S0_PHASE=name, HF_S0_VERSION="C1", HF_S0_SOURCE_MANIFEST_SHA=manifest_hash or plan_hash,
            HF_HARNESS_ID="H1", HF_HARNESS_MANIFEST_SHA=harness_hash or plan_hash,
            HF_FOBS_HARNESS_MANIFEST=str(harness_manifest), HF_FOBS_HARNESS_SHA=harness_hash or plan_hash,
            HF_FOBS_HARNESS_TEST=str(root / "H1/tests/test_compensated_invariants.py"))
        print(json.dumps(dict(phase=name, started_utc=utc(),
            remaining_campaign_seconds=deadline-begin, active_seconds_limit=active_deadline-begin)), flush=True)
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
            active_deadline_monotonic=active_deadline, source_version="C1",
            active_limit_kind="phase_inclusive_limit" if begin+active_seconds <= absolute else "campaign_seal_reserve",
            source_manifest_sha256=manifest_hash or plan_hash,
            harness_id="H1", harness_manifest_sha256=harness_hash or plan_hash)
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
        candidate = aux / "force_observation_evidence.py" if frozen else original_worker
        if not matches(candidate):
            if action != "seal" or not matches(original_worker):
                raise StopCampaign("source_not_pass", "Evidence worker identity changed or missing")
            candidate = original_worker  # F0 partial failure: approved stdlib preservation only.
        return [sys.executable, "-u", "-B", str(candidate), "--root", str(root),
                "--repo", str(repo), "--action", action]

    def check_selection():
        if sha(source_manifest) != manifest_hash or sha(harness_manifest) != harness_hash:
            raise StopCampaign("source_not_pass", "Frozen input or H1 manifest changed")
        if (selected["version"] != "C1" or extended(selected["source"]) != source
                or extended(selected["source_manifest"]) != source_manifest
                or selected["source_manifest_sha256"] != manifest_hash
                or selected["harness"]["version"] != "H1"
                or extended(selected["harness"]["manifest_path"]) != harness_manifest
                or selected["harness"]["manifest_sha256"] != harness_hash):
            raise StopCampaign("source_not_pass", "Selected science/H1 identity differs")

    try:
        execute("F0_prepare", "F0", worker_command("prepare", frozen=False))
        manifest_hash, harness_hash = sha(source_manifest), sha(harness_manifest)
        selected = read(root / "selected_source.json")
        check_selection()
        execute("F1_force", "F1", [sys.executable, "-u", "-B", str(aux / "probe_force_observation.py"),
                "--root", str(root), "--source", str(source)])
        check_selection()
        summary = read(root / "results/force/summary.json")
        if (summary["schema"] != "hf-force-observation-probe-1" or summary["status"] != "pass"
                or summary["source_manifest_sha256"] != manifest_hash
                or extended(summary["source"]) != source or summary["harness"] != selected["harness"]):
            raise StopCampaign("evidence_failure", "Force summary identity/outcome differs")
        status = "fixed_force_complete_no_scientific_admission"
    except StopCampaign as problem:
        status, error = problem.status, dict(type=type(problem).__name__, message=str(problem))
    except BaseException as problem:
        status, error = "parent_exception", dict(type=type(problem).__name__, message=str(problem),
                                                traceback=traceback.format_exc())
    finally:
        # No further scientific calls are possible here, even after partial F0.
        dump(root / "resources.json", dict(phases=phases, status=status, error=error,
            total_elapsed_seconds=time.monotonic()-start, plot_scope="before F2; final receipt includes F2"))
        clean = not supervision_uncertain and all(p["cleanup_verified"] for p in phases)
        if clean and time.monotonic() < deadline-10.25:
            try:
                execute("F2_seal", "F2", worker_command("seal"))
            except BaseException as problem:
                error = dict(prior=error, seal_error=dict(type=type(problem).__name__, message=str(problem)))
                status = problem.status if isinstance(problem, StopCampaign) else "seal_failure"
        else:
            error = dict(prior=error, seal_error="No safe cleanup/time margin for F2")
            if status == "fixed_force_complete_no_scientific_admission":
                status = "resource_stop"
        if time.monotonic() > deadline or shared_elapsed() > LIMITS["shared"]:
            status = "resource_stop"
        ledger.update(status=status, error=error, finished_utc=utc(), elapsed_seconds=time.monotonic()-start,
            selected_source=selected, source_manifest_sha256=manifest_hash, harness_manifest_sha256=harness_hash,
            shared_elapsed_seconds=shared_elapsed(), scientific_admission=False)
        replace(root / "ledger.json", ledger)
        dump(root / "execution_receipt.json", ledger)
        optional_sha = lambda name: sha(root / name) if (root / name).is_file() else None
        binding = dict(schema="hf-force-observation-receipt-binding-1",
            plan_sha256=plan_hash, input_manifest_sha256=optional_sha("input_manifest.json"),
            harness_manifest_sha256=optional_sha("H1/manifest.json"),
            selected_source_sha256=optional_sha("selected_source.json"),
            receipt_sha256=sha(root / "execution_receipt.json"),
            output_manifest_sha256=optional_sha("output_sha256.json"),
            seal_event_sha256=optional_sha("events/F2_seal.ndjson"), seal_log_sha256=optional_sha("logs/F2_seal.log"),
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
    return 0 if status == "fixed_force_complete_no_scientific_admission" else 1


if __name__ == "__main__":
    raise SystemExit(main())
