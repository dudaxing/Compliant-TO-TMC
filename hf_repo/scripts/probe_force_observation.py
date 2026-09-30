"""F-OBS-1: one unchanged C1 force call, with durable pre-call graph evidence.

Only standard-library helpers are imported before the first event. The parent
owns the single deadline and Windows Job. This probe never retries, warms up,
changes a scientific source, or evaluates a tangent/HP/equilibrium problem.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import time

import probe_s0_preparation as shared
import s0_ad_exception as ad_evidence
import s0_event_log as event_module
from s0_event_log import EventLog, EventLogError


SCHEMA = "hf-force-observation-probe-1"
PROTOCOL = "F-OBS-1"
STAGES = (
    "source_binding", "runtime_import_and_prepare", "kernel_import", "input_transfer",
    "force.trace", "force.export_jaxpr", "force.lower", "force.export_stablehlo",
    "force.compile", "force.export_optimized_hlo", "force.call", "force.synchronize",
    "force.transfer", "force.save_output",
)
PAIR_FIELDS = ("F", "G", "Hu", "J", "B", "delta")
OUTPUT_FIELDS = frozenset((
    "residual", "material_residual", "regularization_residual", "material_energy",
    "stress_first_piola", "stress_second_piola", "small_branch", "arithmetic_supported",
    *PAIR_FIELDS, *(name + suffix for name in PAIR_FIELDS for suffix in ("_hi", "_lo")),
))
ARITHMETIC_SHA = "6a0144a92bf323951594a0d677b7558cf2a6501667f4b076dd13e2df6bba3897"
KERNEL_SHA = "88d57ed77565963d8cc367c18398b11b30f8f1e0e335c7dcdbc3d68702ecb6bf"
INPUT_SHA = "2ba110b878186e52996c25f4aad44cb81858be15303c21579c4f5e8ccc013448"
H1_TEST_SHA = "15a81049f3fadcf0a0391f702db8444c33856f1116055d26e6ffca686821e946"
UPSTREAM_C1_SHA = "384708b23842d9d4c9d3324d57c854911772ca3eb9ab15ac9edb7efd6a1c4564"
TEXT_CHUNK_CHARS = 1024 * 1024


class ObservationFailure(shared.ProbeFailure):
    """The requested observation was unavailable; this is not a numeric verdict."""


def resolved(value):
    return event_module.long_path(value).resolve()


class ForceObservationProbe(shared.Probe):
    def __init__(self, root, source, log):
        super().__init__(root, source, "force", log)
        self.summary.update(schema=SCHEMA, protocol=PROTOCOL,
            source_version=os.environ.get("HF_S0_VERSION"),
            expected_stages=list(STAGES), scientific_admission=False,
            execution_contract=dict(trace=1, lower=1, compile=1, compiled_call=1,
                output_synchronization=1, warmup=0, retries=0,
                force_output_fields=sorted(OUTPUT_FIELDS),
                input_ready="one existing block_until_ready in shared.read_element"),
            call_to_synchronize=dict(status="not_reached",
                timing_basis="force.call start marker through return of output synchronization; "
                             "includes intervening event/checkpoint I/O, not pure kernel time"))
        self.checkpoint()

    def step(self, stage, function, *, describe=None):
        index = len(self.summary["steps"])
        shared.require(index < len(STAGES) and STAGES[index] == stage,
                       "unexpected or repeated F-OBS-1 stage", ObservationFailure)
        started = time.monotonic()
        row = dict(stage=stage, status="running", started_utc=shared.utc(),
                   started_monotonic=started)
        self.summary["steps"].append(row)
        if stage == "force.call":
            self.summary["call_to_synchronize"].update(
                status="running", started_utc=row["started_utc"], start_monotonic=started)
        self.checkpoint()
        self.log.emit("stage_started", stage=stage, outcome="running",
                      stage_start_monotonic=started)
        begin = time.monotonic()
        try:
            value = function()
            ended = time.monotonic()
            record = dict(status="pass", elapsed_seconds=ended-begin,
                          execution_start_monotonic=begin, completed_monotonic=ended,
                          finished_utc=shared.utc())
            if describe is not None:
                record["value"] = describe(value)
        except EventLogError:
            raise
        except Exception as error:
            detail = ad_evidence.exception_details(error)
            detail["stage"] = stage
            record = dict(status="failed", elapsed_seconds=time.monotonic()-begin,
                          finished_utc=shared.utc(), error=detail)
            row.update(record)
            self.summary["errors"].append(detail)
            interval = self.summary["call_to_synchronize"]
            if interval["status"] == "running":
                interval.update(status="failed", failed_stage=stage)
            self.checkpoint()
            self.log.emit("stage_failed", stage=stage, outcome="error",
                exception_type=detail["type"], exception=detail,
                traceback=detail["traceback"], duration=record["elapsed_seconds"])
            raise
        row.update(record)
        if stage == "force.call":
            self.summary["call_to_synchronize"].update(
                call_returned=True, call_return_monotonic=ended,
                call_body_seconds=record["elapsed_seconds"])
        elif stage == "force.synchronize":
            interval = self.summary["call_to_synchronize"]
            interval.update(status="complete", end_monotonic=ended,
                elapsed_seconds=ended-interval["start_monotonic"],
                synchronization_body_seconds=record["elapsed_seconds"],
                finished_utc=record["finished_utc"])
        self.checkpoint()
        self.log.emit("stage_finished", stage=stage, outcome="pass",
            duration=record["elapsed_seconds"], completed_monotonic=ended)
        return value

    def start_artifact(self, name):
        final, partial = self.output/name, self.output/(name+".partial")
        shared.require(name not in self.summary["artifacts"] and not final.exists()
                       and not partial.exists(), "artifact path already used", ObservationFailure)
        record = dict(path=partial.relative_to(self.output).as_posix(), final_path=name,
                      status="partial", phase="awaiting_render_or_write", file_created=False,
                      bytes=None, sha256=None, started_utc=shared.utc())
        self.summary["artifacts"][name] = record
        self.checkpoint()
        self.log.emit("artifact_started", artifact=name, partial_path=record["path"],
                      artifact_status="partial")
        return final, partial, record

    def complete_artifact(self, final, partial, record):
        # Hash the flushed, closed partial file before the atomic name change.
        digest, size = shared.sha(partial), partial.stat().st_size
        shared.require(not final.exists(), "complete artifact already exists", ObservationFailure)
        os.rename(partial, final)
        record.update(path=final.relative_to(self.output).as_posix(), status="complete",
                      phase="complete", file_created=True, bytes=size, sha256=digest,
                      completed_utc=shared.utc())
        self.checkpoint()
        self.log.emit("artifact_complete", artifact=record["final_path"],
                      path=record["path"], bytes=size, sha256=digest,
                      artifact_status="complete")
        return dict(record)

    def export_text(self, name, render):
        final, partial, record = self.start_artifact(name)
        with partial.open("x", encoding="utf-8", newline="\n") as stream:
            stream.flush()
            os.fsync(stream.fileno())
            record.update(file_created=True, phase="rendering")
            self.checkpoint()
            body = render()
            shared.require(isinstance(body, str) and bool(body),
                           "IR text unavailable; no alternate interface or recompile fallback",
                           ObservationFailure)
            record["phase"] = "writing"
            self.checkpoint()
            # The public API creates one whole string. Chunked encoding avoids
            # additionally holding a whole UTF-8 copy; it is not a memory cap.
            for start in range(0, len(body), TEXT_CHUNK_CHARS):
                stream.write(body[start:start+TEXT_CHUNK_CHARS])
            del body
            stream.flush()
            os.fsync(stream.fileno())
        return self.complete_artifact(final, partial, record)


def verify_sources(probe, *, initial):
    # This worker API is standard-library-only and strictly read-only.
    import force_observation_evidence as evidence

    expected_aux = probe.root/"aux/hf_repo/scripts"
    for module, name in ((shared, "probe_s0_preparation.py"),
                         (ad_evidence, "s0_ad_exception.py"),
                         (event_module, "s0_event_log.py"),
                         (evidence, "force_observation_evidence.py")):
        shared.require(resolved(module.__file__) == resolved(expected_aux/name),
                       "helper import escaped frozen auxiliary directory: "+name, shared.SourceFailure)
    shared.require(resolved(__file__) == resolved(expected_aux/"probe_force_observation.py"),
                   "probe is not the frozen auxiliary copy", shared.SourceFailure)
    manifest_path = probe.root/"input_manifest.json"
    shared.require(shared.sha(manifest_path) == probe.summary["source_manifest_sha256"],
                   "new input manifest identity differs", shared.SourceFailure)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    science, harness = manifest["science"], manifest["harness"]
    shared.require(probe.summary["source_version"] == science["version"] == "C1"
                   and resolved(science["source"]) == probe.source
                   and probe.source == resolved(probe.root/"C1/source/hf_repo")
                   and science["upstream_manifest_sha256"] == UPSTREAM_C1_SHA,
                   "scientific C1 identity differs", shared.SourceFailure)
    shared.require(harness["version"] == "H1"
                   and resolved(harness["manifest_path"]) == resolved(probe.root/"H1/manifest.json")
                   and resolved(harness["test_path"]) == resolved(probe.root/"H1/tests/test_compensated_invariants.py")
                   and harness["test_sha256"] == H1_TEST_SHA
                   and shared.sha(harness["test_path"]) == H1_TEST_SHA
                   and shared.sha(harness["manifest_path"]) == harness["manifest_sha256"],
                   "historical H1 identity differs", shared.SourceFailure)
    shared.require(os.environ.get("HF_HARNESS_ID") == "H1"
                   and os.environ.get("HF_HARNESS_MANIFEST_SHA") == harness["manifest_sha256"]
                   and os.environ.get("HF_FOBS_HARNESS_SHA") == harness["manifest_sha256"]
                   and resolved(os.environ["HF_FOBS_HARNESS_MANIFEST"]) == resolved(harness["manifest_path"])
                   and resolved(os.environ["HF_FOBS_HARNESS_TEST"]) == resolved(harness["test_path"]),
                   "declared harness environment differs", shared.SourceFailure)
    fixed = ((probe.source/"src/hf_eval/compensated_invariants.py", ARITHMETIC_SHA),
             (probe.source/"src/hf_eval/split_kernel_invariants_hu.py", KERNEL_SHA),
             (probe.root/"data/inputs.npz", INPUT_SHA))
    for filename, digest in fixed:
        shared.require(shared.sha(filename) == digest, "fixed F-OBS-1 bytes differ: "+str(filename),
                       shared.SourceFailure)
    verified = evidence.verify_snapshot(probe.root, require_live=True)
    if initial:
        probe.summary["harness"] = harness
        probe.summary["source_verification"] = verified
        probe.summary["auxiliary"] = dict(path=str(resolved(__file__)), sha256=shared.sha(__file__),
            reused_helper_path=str(resolved(shared.__file__)), reused_helper_sha256=shared.sha(shared.__file__))
    else:
        shared.require(harness == probe.summary["harness"], "H1 changed during force observation", shared.SourceFailure)
        probe.summary["source_preservation"] = verified
    return dict(status="pass", science=science, harness=harness, verification=verified)


def load_runtime(probe):
    shared.require(os.environ.get("JAX_ENABLE_COMPILATION_CACHE", "").lower() == "false",
                   "parent must disable persistent compilation caching", shared.SourceFailure)
    shared.require(all(os.environ.get(name) == "1" for name in
                       ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")),
                   "declared thread environment differs", shared.SourceFailure)
    loaded = shared.runtime(probe)
    _, jax, _, arithmetic = loaded
    shared.require(not jax.config.jax_enable_compilation_cache,
                   "persistent compilation cache must remain disabled", shared.SourceFailure)
    shared.require(resolved(arithmetic.__file__) == resolved(probe.source/"src/hf_eval/compensated_invariants.py")
                   and shared.sha(arithmetic.__file__) == ARITHMETIC_SHA,
                   "actual arithmetic import identity differs", shared.SourceFailure)
    shared.require(probe.summary["runtime"]["numpy"] == "2.4.6"
                   and probe.summary["runtime"]["jax"] == probe.summary["runtime"]["jaxlib"] == "0.11.0",
                   "declared numerical dependency versions differ", shared.SourceFailure)
    probe.summary["runtime"]["persistent_compilation_cache"] = False
    return loaded


def import_kernel(probe):
    from hf_eval import split_kernel_invariants_hu as kernel
    shared.require(resolved(kernel.__file__) == resolved(probe.source/"src/hf_eval/split_kernel_invariants_hu.py")
                   and shared.sha(kernel.__file__) == KERNEL_SHA,
                   "actual kernel import identity differs", shared.SourceFailure)
    shared.require(kernel.COMPILER_OPTIONS == shared.STRICT_OPTIONS,
                   "kernel strict compiler options differ", shared.SourceFailure)
    probe.summary["kernel"] = dict(version=kernel.KERNEL_VERSION, path=str(resolved(kernel.__file__)),
        sha256=shared.sha(kernel.__file__), compiler_options=kernel.COMPILER_OPTIONS)
    return kernel


def save_output(probe, result, np):
    shared.require(isinstance(result, dict), "kernel output must be a field mapping", ObservationFailure)
    final, partial, record = probe.start_artifact("outputs.npz")
    with partial.open("xb") as stream:
        record.update(file_created=True, phase="writing")
        probe.checkpoint()
        np.savez(stream, **result)
        stream.flush()
        os.fsync(stream.fileno())
    artifact = probe.complete_artifact(final, partial, record)
    # Preserve all returned arrays before checking the unchanged output gates.
    shared.require(set(result) == OUTPUT_FIELDS, "the complete 26-field force mapping differs", ObservationFailure)
    shared.require(all(value.dtype == np.float64 and np.all(np.isfinite(value)) for value in result.values()),
                   "kernel output contains nonfinite or non-binary64 fields", shared.NumericalCheckFailure)
    shared.require(np.all(result["J"] > 0) and np.all(result["arithmetic_supported"] == 1.),
                   "representative state failed physical/arithmetic domain", shared.NumericalCheckFailure)
    validation = dict(status="pass", fields={name:dict(shape=list(value.shape), dtype=str(value.dtype))
        for name, value in result.items()}, finite_binary64=True, positive_J=True,
        arithmetic_supported=True, min_J=float(np.min(result["J"])), scientific_admission=False)
    probe.summary["output_validation"] = validation
    verify_sources(probe, initial=False)
    return dict(artifact=artifact, validation=validation,
                source_preservation=probe.summary["source_preservation"])


def observe(probe):
    probe.step("source_binding", lambda: verify_sources(probe, initial=True), describe=lambda value:value)
    np, jax, jnp, _ = probe.step("runtime_import_and_prepare", lambda: load_runtime(probe))
    kernel = probe.step("kernel_import", lambda: import_kernel(probe))
    args, _direction = probe.step("input_transfer", lambda: shared.read_element(probe, np, jax, jnp))
    function = kernel._batch_without_tangent
    traced = probe.step("force.trace", lambda: function.trace(*args))
    probe.step("force.export_jaxpr", lambda: probe.export_text("force_raw_jaxpr.txt", lambda:str(traced.jaxpr)),
               describe=lambda value:value)
    lowered = probe.step("force.lower", lambda: traced.lower())
    probe.step("force.export_stablehlo", lambda: probe.export_text("force_stablehlo.mlir",
        lambda:lowered.as_text(dialect="stablehlo", debug_info=False)), describe=lambda value:value)
    compiled = probe.step("force.compile", lambda: lowered.compile(compiler_options=shared.STRICT_OPTIONS))
    probe.step("force.export_optimized_hlo", lambda: probe.export_text("force_optimized_hlo.txt", compiled.as_text),
               describe=lambda value:value)
    # No inspection, host transfer, or extra wait between this single call and
    # its finished event. This remains the very same compiled object.
    result = probe.step("force.call", lambda: compiled(*args))
    probe.step("force.synchronize", lambda: jax.block_until_ready(result))
    transferred = probe.step("force.transfer", lambda: jax.tree.map(np.asarray, result))
    probe.step("force.save_output", lambda: save_output(probe, transferred, np), describe=lambda value:value)
    return "pass"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    with EventLog() as log:
        log.emit("probe_started", protocol=PROTOCOL, mode="force", outcome="running",
                 scientific_imports_started=False, scientific_admission=False)
        root, source = resolved(args.root), resolved(args.source)
        shared.require(root.is_dir() and (root/"input_manifest.json").is_file(),
                       "prepared observation root/input manifest is absent", shared.SourceFailure)
        probe = ForceObservationProbe(root, source, log)
        try:
            status = observe(probe)
        except EventLogError:
            raise
        except Exception as error:
            detail = ad_evidence.exception_details(error)
            detail["stage"] = "probe"
            probe.summary["errors"].append(detail)
            probe.summary["failure_classification"] = (
                "source_not_pass" if isinstance(error, shared.SourceFailure)
                else "numerical_not_pass" if isinstance(error, shared.NumericalCheckFailure)
                else "observation_failure")
            log.emit("probe_failed", stage="probe", outcome="error", exception=detail,
                     exception_type=detail["type"], traceback=detail["traceback"])
            status = "failed"
        probe.finish(status)
        return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
