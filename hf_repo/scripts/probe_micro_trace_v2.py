"""F-TRACE2: one unchanged HR1 micrograph and one native profiler session.

Only standard-library helpers load before the explicit runtime stage. The parent
owns the single deadline/RSS/Job window. No warmup, fallback, retry, new physics,
AD, full force, profiler server, or external conversion is used.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
import os
import re
from pathlib import Path
import sys
import threading
import time

# Fixed and author helpers are imported only by main, after all frozen helper
# bytes and actual file positions have been pinned using the standard library.
ad_evidence = event_module = EventLog = EventLogError = None
FIXED_HELPERS = (
    "windows_owned_process.py", "windows_owned_process_sup2.py",
    "cpu_supervision_evidence.py", "probe_s0_preparation.py",
    "s0_preparation_evidence.py", "s0_event_log.py", "s0_ad_exception.py",
    "force_cost_evidence.py", "micro_trace_evidence.py",
)
AUTHOR_HELPERS = ("run_micro_trace_v2.py", "probe_micro_trace_v2.py", "micro_trace_v2_evidence.py")


def early_path(value):
    text = os.path.abspath(os.fspath(value))
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        text = "\\\\?\\" + text
    return Path(text).resolve()


def bootstrap_helpers(root):
    global ad_evidence, event_module, EventLog, EventLogError
    manifest_path = root/"input_manifest.json"
    with manifest_path.open("rb") as stream:
        manifest_digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if manifest_digest != os.environ.get("HF_S0_SOURCE_MANIFEST_SHA"):
        raise RuntimeError("bootstrap input manifest does not match parent source identity")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = {row["path"]:row for row in manifest["files"]}
    folder = root/"aux/hf_repo/scripts"
    for filename in (*FIXED_HELPERS, *AUTHOR_HELPERS):
        relative = "aux/hf_repo/scripts/"+filename
        row = rows[relative]
        actual = folder/filename
        info = actual.lstat()
        if actual.is_symlink() or info.st_file_attributes & 0x400:
            raise RuntimeError("bootstrap helper is a reparse path: "+filename)
        with actual.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if info.st_size != row["bytes"] or digest != row["sha256"]:
            raise RuntimeError("bootstrap helper source bytes differ: "+filename)
    if early_path(__file__) != early_path(folder/"probe_micro_trace_v2.py"):
        raise RuntimeError("probe entry is not the frozen new author file")
    sys.path.insert(0, str(folder))
    import s0_ad_exception as actual_ad
    import s0_event_log as actual_events
    import micro_trace_v2_evidence as evidence
    for module, filename in ((actual_ad,"s0_ad_exception.py"),
                            (actual_events,"s0_event_log.py"),
                            (evidence,"micro_trace_v2_evidence.py")):
        row = rows["aux/hf_repo/scripts/"+filename]
        if early_path(module.__file__) != early_path(folder/filename):
            raise RuntimeError("actual bootstrap module position differs: "+filename)
        with early_path(module.__file__).open("rb") as stream:
            digest = hashlib.file_digest(stream,"sha256").hexdigest()
        if digest != row["sha256"]:
            raise RuntimeError("actual bootstrap module SHA differs: "+filename)
    ad_evidence, event_module = actual_ad, actual_events
    EventLog, EventLogError = actual_events.EventLog, actual_events.EventLogError
    return evidence


SCHEMA = "hf-micro-trace-probe-1"
PROTOCOL = "F-TRACE2"
RUN_ID = "micro_trace_002"
STRICT_OPTIONS = {"xla_cpu_enable_fast_math": False, "xla_cpu_ftz": False}
ARITHMETIC_SHA = "6a0144a92bf323951594a0d677b7558cf2a6501667f4b076dd13e2df6bba3897"
KERNEL_SHA = "630babc9c299ef2336835df18a50521f51d439dc09e3353ae6d0776d91937970"
HR1_SHA = "28e696175d572379527e6a021365dacf445fa4dd28f73cb381925d95bfb383d5"
INPUT_SHA = "2ba110b878186e52996c25f4aad44cb81858be15303c21579c4f5e8ccc013448"
REFERENCE_SHA = "ee053018a911b45e78e9f821d9bf25f870fb9a81e3b17ee72dc4d27ae3868d4e"
ENVIRONMENT_NAMES = (
    "XLA_FLAGS", "JAX_DEBUG_NANS", "JAX_DEBUG_INFS", "JAX_DISABLE_JIT",
    "JAX_ENABLE_PGLE", "JAX_PGLE_PROFILING_RUNS", "JAX_CPU_ENABLE_ASYNC_DISPATCH",
    "JAX_ENABLE_X64", "JAX_ENABLE_COMPILATION_CACHE", "JAX_PLATFORMS",
    "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
    "JAX_TRACEBACK_FILTERING", "PYTHONDONTWRITEBYTECODE",
)
STAGES = (
    "trace_controls", "source_binding", "environment_snapshot", "runtime_import",
    "kernel_import", "harness_import", "input_prepare", "input_ready",
    "micro.trace", "micro.export_jaxpr", "micro.lower", "micro.export_stablehlo",
    "micro.compile", "micro.export_optimized_hlo", "profiler_binding", "profiler.start",
    "micro_first.call", "micro_first.synchronize", "micro_first.ready_only",
    "micro_first.transfer", "micro_first.save_output", "micro_first.compare",
    "micro_repeat.call", "micro_repeat.synchronize", "micro_repeat.transfer",
    "micro_repeat.save_output", "micro_repeat.compare", "profiler.stop",
    "native.collect", "native.analyze", "source_preservation",
)
ANNOTATION_STAGES = ("micro_first.call", "micro_first.synchronize", "micro_first.ready_only",
                     "micro_repeat.call", "micro_repeat.synchronize")
ANNOTATIONS = {stage:PROTOCOL+":"+stage for stage in ANNOTATION_STAGES}
EXECUTION_CONTRACT = dict(
    graph_count=1, trace=1, lower=1, compile=1, compiled_call=2,
    output_synchronization=2, ready_only=1, input_ready=1, micro_leaf_count=24,
    profiler_start=1, profiler_stop=1, annotations=5,
    warmup=0, retries=0, force_calls=0, ad_calls=0,
)
OUTPUT_ORDER = ("micro_first", "micro_repeat")
PROFILER_PINS = {
    "jax/profiler.py": (1324, "efc7b40958bb005fc2ce10c75fd934cdb61b6cd3744291572f5653a490462596"),
    "jax/_src/profiler.py": (19711, "abb2a2b16a34a060d581dccc0acecd655b20d60313377af3f727cce50a9c2a83"),
    "jax/_src/lib/__init__.py": (7333, "9438b64103846020c1414a01c2b83f00b80ea35e16032646b3f3850e8ceb8868"),
    "jaxlib/_profiler.pyd": (8704, "8469b4201e97fe42c8f9c01ad41f3c829db3462b991f33a9e3c2b2e097d04dea"),
    "jaxlib/_profile_data.pyd": (8704, "346df67a860c13b64236e7f817ba630ab09f34dab5155e787006a23490396e5e"),
    "jaxlib/jax_common.dll": (237296640, "cb392e3e87d292dc1db7cc88efd41f2f5b44ab0bb025cb5644b1eb1842e6ee14"),
}

TEXT_CHUNK_CHARS = 1024 * 1024


class TraceObservationFailure(RuntimeError):
    pass


class ObservabilityFailure(TraceObservationFailure):
    def __init__(self, message, *, kind="native_interface"):
        super().__init__(message)
        self.kind = kind


def require(condition, message):
    if not condition:
        raise TraceObservationFailure(message)


def resolved(path):
    return event_module.long_path(path).resolve()


def sha(path):
    with resolved(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def retain_error(probe, error, stage, *, kind="execution"):
    """Evidence failure cannot replace the already latched exception object.

    This is a recording boundary only. It never invokes a scientific operation,
    a native operation or another persistence attempt.
    """
    if probe.first_exception is None:
        probe.first_exception = error
    elif error is not probe.first_exception and probe.summary.get("first_error") is None:
        primary = probe.first_exception
        primary_kind = (primary.kind if isinstance(primary, ObservabilityFailure) else
            "native_interface" if primary is probe.native_start_exception or primary is probe.native_stop_exception else
            "recording" if isinstance(primary, EventLogError) else "execution")
        retain_error(probe, primary, stage+".retained_primary", kind=primary_kind)
    detail = None
    try:
        detail = probe.remember_error(error, stage, kind=kind)
    except BaseException as record_error:
        try:
            detail = dict(type=type(error).__name__, message="exception evidence unavailable",
                          traceback=None, stage=stage, evidence_status="partial")
            if probe.summary["first_error"] is None:
                probe.summary.update(first_error=detail, first_error_kind=kind)
            probe.summary["secondary_record_errors"].append(dict(
                type=type(record_error).__name__, message="exception materialization failed",
                stage=stage+".exception_materialization"))
        except BaseException:
            # The retained Python exception object remains authoritative even
            # when the evidence channel cannot materialize any detail at all.
            pass
    return detail


def retain_secondary_record_error(probe, error, stage):
    detail = retain_error(probe, error, stage, kind="recording")
    try:
        probe.summary["secondary_record_errors"].append(dict(
            type=type(error).__name__, message="recording failed", stage=stage))
    except BaseException:
        pass
    return detail


def retain_shutdown_record_error(probe, error, stage):
    """Retain a stop-wrapper error independently without replacing its primary."""
    detail = retain_secondary_record_error(probe, error, stage)
    try:
        life = probe.summary["profiler"]
        if probe.native_stop_exception is not None:
            native_detail = retain_error(probe, probe.native_stop_exception, "profiler.stop", kind="native_interface")
            life.update(native_stop_error=native_detail, stop_error=native_detail)
            if life["shutdown_error"] is None:
                life["shutdown_error"] = native_detail
        life["shutdown_errors"].append(detail)
        if life["shutdown_error"] is None:
            life["shutdown_error"] = detail
        life["shutdown_failure_kind"] = (
            "native_and_evidence" if probe.native_stop_exception is not None else "evidence_only")
    except BaseException:
        pass


class TraceProbe:
    def __init__(self, root, source, log):
        self.root, self.source, self.log = root, source, log
        self.output = root/"results/trace"
        self.output.mkdir(parents=True, exist_ok=False)
        self.started = time.monotonic()
        self.selected = None
        self.manifest = None
        self.profiler_module = None
        self.native_start_exception = None
        self.native_stop_exception = None
        self.first_exception = None
        self.error_details_by_id = {}
        self.error_objects_by_id = {}
        self.active_deadline = float(os.environ["HF_TRACE2_ACTIVE_DEADLINE"])
        require(math.isfinite(self.active_deadline) and self.active_deadline > time.monotonic(),
                "parent P1 active deadline is absent or already expired")
        self.summary = dict(
            schema=SCHEMA, protocol=PROTOCOL, campaign_protocol=PROTOCOL,
            run_id=RUN_ID, mode="trace", phase="P1_trace", source_version="R1",
            subject="micro_native_observation",
            identity=json.loads((root/"results/P1_supervision/request.json").read_text(encoding="utf-8"))["identity"],
            source=str(source), source_manifest_sha256=log.source_manifest_sha256,
            events_file=str(log.path), started_utc=utc(), status="running",
            runtime_native_trace_observed=False, scientific_admission=False,
            force_executed=False, new_hp_evaluations=0, new_equilibrium_paths=0,
            numerical_contract_pass=False,
            expected_stages=list(STAGES), execution_contract=dict(EXECUTION_CONTRACT),
            steps=[], errors=[], artifacts={}, comparisons={}, first_error=None,
            first_error_kind=None, secondary_record_errors=[], exception_materialization=[],
            active_deadline_monotonic=self.active_deadline,
            annotations=ANNOTATIONS,
            profiler=dict(start_attempts=0, start_returned=False, start_status="not_reached",
                stop_attempts=0, stop_returned=False, stop_status="not_reached",
                first_error=None, shutdown_error=None, shutdown_errors=[],
                native_start_error=None, native_stop_error=None,
                start_error=None, body_error=None, stop_error=None, pre_body_error=None,
                body_attempts=0, body_returned=False,
                shutdown_failure_kind="not_reached",
                requested_options=None, effective_defaults="native_not_exposed",
                create_perfetto_link=False, create_perfetto_trace=False,
                log_dir="native"),
            observation_order=list(OUTPUT_ORDER),
            timing_basis="completed function body excludes checkpoint/event I/O; "
                         "open stage marker is not a recorded actual function entry",
        )
        self.checkpoint()

    def checkpoint(self):
        temporary = self.output/"summary.pending.json"
        write_json(temporary, self.summary)
        os.replace(temporary, self.output/"summary.json")

    def emit(self, event, **fields):
        return self.log.emit(event, protocol=PROTOCOL, campaign_protocol=PROTOCOL,
            run_id=RUN_ID, mode="trace", harness_id=os.environ.get("HF_HARNESS_ID"),
            harness_manifest_sha256=os.environ.get("HF_HARNESS_MANIFEST_SHA"), **fields)

    def remember_error(self, error, stage, *, kind="execution"):
        previous = self.error_details_by_id.get(id(error))
        if previous is not None:
            return previous
        if self.first_exception is None:
            self.first_exception = error
        begin = time.monotonic()
        try:
            detail = ad_evidence.exception_details(error)
        except BaseException as materialization_error:
            detail = dict(type=type(error).__name__, message=str(error), traceback=None,
                materialization_error=dict(type=type(materialization_error).__name__,
                                           message=str(materialization_error)))
        ended = time.monotonic()
        detail["stage"] = stage
        self.error_objects_by_id[id(error)] = error
        self.error_details_by_id[id(error)] = detail
        self.summary["exception_materialization"].append(dict(stage=stage,
            start_monotonic=begin, end_monotonic=ended, elapsed_seconds=ended-begin))
        self.summary["errors"].append(detail)
        if self.summary["first_error"] is None:
            self.summary.update(first_error=detail, first_error_kind=kind)
        return detail

    def secondary_record_error(self, error, stage):
        detail = dict(type=type(error).__name__, message=str(error), stage=stage)
        self.summary["secondary_record_errors"].append(detail)
        return detail

    def step(self, stage, function, *, describe=None):
        index = len(self.summary["steps"])
        require(index < len(STAGES) and STAGES[index] == stage,
                "unexpected or repeated trace stage: "+stage)
        started = time.monotonic()
        row = dict(stage=stage, status="running", started_utc=utc(), started_monotonic=started)
        self.summary["steps"].append(row)
        begin = started
        measurement = None
        try:
            self.checkpoint()
            self.emit("stage_started", stage=stage, outcome="running", stage_start_monotonic=started)
            begin = time.monotonic()
            if stage in ANNOTATIONS:
                require(self.profiler_module is not None and self.summary["profiler"]["start_returned"],
                        "annotated call requires the sole active profiler session")
                measurement = dict(annotation_name=ANNOTATIONS[stage], pid=os.getpid(),
                    native_tid=threading.get_native_id(), annotation_outer_start_monotonic=time.monotonic())
                try:
                    with self.profiler_module.TraceAnnotation(ANNOTATIONS[stage], graph="jit_reused",
                            phase="P1_trace", protocol=PROTOCOL, run_id=RUN_ID):
                        if stage.endswith(".call"):
                            # Last durable checkpoint is above. No checkpoint or
                            # event I/O separates this gate and the actual call.
                            remaining = self.active_deadline-time.monotonic()
                            row["call_admission"] = dict(remaining_seconds=remaining,
                                minimum_remaining_seconds=20.0, active_deadline_monotonic=self.active_deadline)
                            require(remaining >= 20.0, "less than 20 seconds remain before compiled call")
                        measurement["thread_time_ns_start"] = time.thread_time_ns()
                        measurement["process_time_ns_start"] = time.process_time_ns()
                        begin = time.monotonic()
                        measurement["monotonic_start"] = begin
                        try:
                            value = function()
                        finally:
                            ended = time.monotonic()
                            measurement["monotonic_end"] = ended
                            measurement["process_time_ns_end"] = time.process_time_ns()
                            measurement["thread_time_ns_end"] = time.thread_time_ns()
                finally:
                    measurement["annotation_outer_end_monotonic"] = time.monotonic()
                    row["value"] = dict(function_measurement=measurement)
            else:
                value = function()
                ended = time.monotonic()
            record = dict(status="pass", elapsed_seconds=ended-begin,
                execution_start_monotonic=begin, completed_monotonic=ended, finished_utc=utc())
            if describe is not None:
                require(measurement is None, "annotated outputs cannot be inspected by a describer")
                record["value"] = describe(value)
            if stage in ("micro.trace", "micro.compile"):
                record["compiler_options"] = dict(STRICT_OPTIONS)
                record["compiler_options_executed"] = True
                record["options_interface"] = "jax.jit" if stage == "micro.trace" else "lowered.compile"
            row.update(record)
            self.checkpoint()
            extra = {} if measurement is None else dict(function_measurement=measurement)
            self.emit("stage_finished", stage=stage, outcome="pass", duration=record["elapsed_seconds"],
                      execution_start_monotonic=begin, completed_monotonic=ended, **extra)
            return value
        except BaseException as error:
            kind = (error.kind if isinstance(error, ObservabilityFailure) else
                    "native_interface" if error is self.native_start_exception or error is self.native_stop_exception else
                    "recording" if isinstance(error, EventLogError) else
                    "source" if stage in ("source_binding", "source_preservation", "profiler_binding") else
                    "numerical" if stage.endswith(".compare") else "execution")
            detail = self.remember_error(error, stage, kind=kind)
            row.update(status="failed", elapsed_seconds=time.monotonic()-begin,
                       finished_utc=utc(), error=detail)
            try:
                self.checkpoint()
                self.emit("stage_failed", stage=stage, outcome="error", exception=detail,
                          exception_type=detail["type"], traceback=detail.get("traceback"),
                          duration=row["elapsed_seconds"])
            except BaseException as record_error:
                self.secondary_record_error(record_error, stage+".failure_record")
            raise

    def start_artifact(self, name):
        final, partial = self.output/name, self.output/(name+".partial")
        require(name not in self.summary["artifacts"] and not final.exists()
                and not partial.exists(), "artifact already exists: "+name)
        record = dict(status="partial", path=partial.relative_to(self.root).as_posix(),
            final_path=final.relative_to(self.root).as_posix(), bytes=None,
            sha256=None, file_created=False, started_utc=utc())
        self.summary["artifacts"][name] = record
        self.checkpoint()
        self.emit("artifact_started", artifact=name, path=record["path"],
                  artifact_status="partial")
        return final, partial, record

    def complete_artifact(self, final, partial, record):
        digest, size = sha(partial), partial.stat().st_size
        require(not final.exists(), "artifact final path already exists")
        os.rename(partial, final)
        record.update(status="complete", path=final.relative_to(self.root).as_posix(),
                      bytes=size, sha256=digest, file_created=True, completed_utc=utc())
        self.checkpoint()
        self.emit("artifact_complete", artifact=final.name, path=record["path"],
                  bytes=size, sha256=digest, artifact_status="complete")
        return dict(record)

    def save_json(self, name, value):
        final, partial, record = self.start_artifact(name)
        write_json(partial, value)
        return self.complete_artifact(final, partial, record)

    def save_arrays(self, np, name, arrays):
        final, partial, record = self.start_artifact(name)
        with partial.open("xb") as stream:
            stream.flush()
            os.fsync(stream.fileno())
            record["file_created"] = True
            self.checkpoint()
            np.savez(stream, **arrays)
            stream.flush()
            os.fsync(stream.fileno())
        return self.complete_artifact(final, partial, record)

    def export_text(self, name, render):
        final, partial, record = self.start_artifact(name)
        with partial.open("x", encoding="utf-8", newline="\n") as stream:
            stream.flush()
            os.fsync(stream.fileno())
            record["file_created"] = True
            self.checkpoint()
            body = render()
            require(isinstance(body, str) and bool(body),
                    "IR text unavailable; no alternate interface or compilation fallback")
            for start in range(0, len(body), TEXT_CHUNK_CHARS):
                stream.write(body[start:start+TEXT_CHUNK_CHARS])
            stream.flush()
            os.fsync(stream.fileno())
        return self.complete_artifact(final, partial, record)

    def finish(self, status):
        self.summary.update(status=status, finished_utc=utc(),
                            elapsed_seconds=time.monotonic()-self.started)
        self.checkpoint()
        self.emit("probe_finished", outcome=status,
            runtime_native_trace_observed=self.summary["runtime_native_trace_observed"],
            duration=self.summary["elapsed_seconds"], scientific_admission=False)


def frozen_path(probe, value):
    require(isinstance(value, str) and bool(value), "missing selected source path")
    path = resolved(probe.root/value)
    require(path.is_relative_to(probe.root), "selected source path escaped root")
    return path


def trace_controls(probe):
    import micro_trace_v2_evidence as evidence
    require(resolved(evidence.__file__) == resolved(probe.root/"aux/hf_repo/scripts/micro_trace_v2_evidence.py"),
            "trace analysis helper escaped frozen aux")
    result = evidence.trace_controls(probe.root)
    record = probe.save_json("trace_controls.json", result)
    probe.summary["trace_controls"] = dict(result=result, artifact=record)
    probe.summary["controls_passed"] = len(result.get("cases", [])) if result.get("status") == "pass" else 0
    probe.checkpoint()
    require(result.get("status") == "pass" and len(result.get("cases", [])) == 16,
            "sixteen groups of actual path/classifier/trace parser controls did not pass")
    return dict(status="pass", case_count=16, artifact=record)


def verify_sources(probe, *, initial):
    import micro_trace_v2_evidence as evidence
    aux = probe.root/"aux/hf_repo/scripts"
    for module, filename in ((event_module, "s0_event_log.py"),
            (ad_evidence, "s0_ad_exception.py"), (evidence, "micro_trace_v2_evidence.py")):
        require(resolved(module.__file__) == resolved(aux/filename),
                "helper import escaped frozen aux: "+filename)
    require(resolved(__file__) == resolved(aux/"probe_micro_trace_v2.py"), "probe must be frozen aux")
    require(probe.log.phase == "P1_trace" and probe.log.version == "R1",
            "event source phase/version mismatch")
    manifest_path = probe.root/"input_manifest.json"
    require(sha(manifest_path) == probe.summary["source_manifest_sha256"], "manifest hash mismatch")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    selected = json.loads((probe.root/"selected_source.json").read_text(encoding="utf-8"))
    require(manifest.get("protocol") == PROTOCOL and manifest.get("run_id") == RUN_ID,
            "input manifest campaign identity mismatch")
    require(selected["input_manifest_sha256"] == sha(manifest_path)
            and frozen_path(probe, selected["source"]) == probe.source
            and probe.source == resolved(probe.root/"R1/source/hf_repo"),
            "selected source identity mismatch")
    paths = {key:frozen_path(probe, selected[key]) for key in
             ("hr1_test", "reference_npz", "fixture")}
    require(paths["hr1_test"] == resolved(probe.root/"aux/hf_repo/tests/test_force_reuse_contract.py")
            and paths["fixture"] == resolved(probe.root/"data/inputs.npz"), "fixed input location mismatch")
    for path, digest in ((paths["hr1_test"], HR1_SHA), (paths["reference_npz"], REFERENCE_SHA),
            (paths["fixture"], INPUT_SHA),
            (probe.source/"src/hf_eval/compensated_invariants.py", ARITHMETIC_SHA),
            (probe.source/"src/hf_eval/split_kernel_invariants_hu.py", KERNEL_SHA)):
        require(sha(path) == digest, "fixed source/reference bytes differ: "+str(path))
    verification = evidence.verify_inputs(probe.root, include_live=True)
    require(verification["status"] == "verified"
            and verification["input_manifest_sha256"] == sha(manifest_path), "input verification failed")
    ast_check = evidence.assert_micro_ast(paths["hr1_test"], resolved(__file__))
    require(ast_check["status"] == "pass", "nested reused AST differs from HR1")
    harness, arithmetic_harness = selected["harness"], selected["arithmetic_harness"]
    require(harness["version"] == "HR1" and arithmetic_harness["version"] == "H1"
            and resolved(harness["test_path"]) == paths["hr1_test"]
            and harness["test_sha256"] == HR1_SHA,
            "historical harness metadata differs")
    require(os.environ.get("HF_HARNESS_ID") == "HR1"
            and os.environ.get("HF_HARNESS_MANIFEST_SHA") == harness["manifest_sha256"],
            "event harness identity differs")
    roles = {name:manifest[name] for name in
             ("parent_supervisor", "candidate_supervisor", "loaded_parent_supervisor")}
    if initial:
        probe.selected, probe.manifest = selected, manifest
        probe.summary.update(harness=harness, arithmetic_harness=arithmetic_harness,
            source_verification=verification, micro_ast=ast_check, **roles)
        probe.summary["references"] = {name:dict(path=path.relative_to(probe.root).as_posix(),
            bytes=path.stat().st_size, sha256=sha(path)) for name,path in paths.items()}
    else:
        require(selected == probe.selected and manifest == probe.manifest,
                "source declarations changed during observation")
        probe.summary["source_preservation"] = verification
    probe.summary["loaded_helpers"] = evidence.record_loaded_helpers(probe.root)
    probe.checkpoint()
    return dict(status="pass", verification=verification, micro_ast=ast_check)


def environment_snapshot(probe):
    require(not any(name == "jax" or name.startswith("jax.") or name == "numpy"
                    or name.startswith("numpy.") for name in sys.modules),
            "scientific module was imported before the environment snapshot")
    value = dict(schema="hf-micro-trace-environment-1", protocol=PROTOCOL, run_id=RUN_ID,
        captured_utc=utc(), captured_monotonic=time.monotonic(), scientific_imports_started=False,
        variables={name:dict(present=name in os.environ, value=os.environ.get(name))
                   for name in ENVIRONMENT_NAMES}, interpretation="present raw strings, not effective config")
    record = probe.save_json("environment.json", value)
    probe.summary["environment"] = dict(artifact=record, **value)
    probe.checkpoint()
    previous_path = frozen_path(probe, "provenance/micro_trace_001/results/trace/environment.json")
    previous = json.loads(previous_path.read_text(encoding="utf-8"))
    require(previous.get("protocol") == "F-TRACE1" and previous.get("run_id") == "micro_trace_001"
            and set(previous.get("variables", {})) == set(ENVIRONMENT_NAMES),
            "frozen F-TRACE1 raw environment reference differs")
    require(value["variables"] == previous["variables"],
            "raw environment differs from the fixed F-TRACE1 observation; no setters or fallback")
    probe.summary["environment_reference"] = dict(path=previous_path.relative_to(probe.root).as_posix(),
        bytes=previous_path.stat().st_size, sha256=sha(previous_path),
        variable_count=len(ENVIRONMENT_NAMES), exact_raw_variables_match=True)
    probe.checkpoint()
    require(os.environ.get("JAX_ENABLE_COMPILATION_CACHE", "").lower() == "false"
            and os.environ.get("JAX_ENABLE_X64", "").lower() == "true"
            and os.environ.get("JAX_PLATFORMS") == "cpu"
            and all(os.environ.get(name) == "1" for name in
                    ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")),
            "parent fixed CPU/x64/cache/BLAS environment mismatch")
    return record


def load_runtime(probe):
    # No environment/config update: actual values are observations of this process.
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(probe.source/"src"))
    import numpy as np
    import jax
    import jax.numpy as jnp
    import jaxlib
    from hf_eval import compensated_invariants as arithmetic
    actual = dict(
        jax_cpu_enable_async_dispatch=jax.config.read("jax_cpu_enable_async_dispatch"),
        jax_debug_nans=jax.config.jax_debug_nans,
        jax_debug_infs=jax.config.jax_debug_infs,
        jax_disable_jit=jax.config.jax_disable_jit,
        jax_enable_pgle=jax.config.jax_enable_pgle,
        jax_pgle_profiling_runs=jax.config.jax_pgle_profiling_runs,
        jax_enable_x64=jax.config.x64_enabled,
        jax_enable_compilation_cache=jax.config.jax_enable_compilation_cache,
        jax_traceback_filtering=jax.config.jax_traceback_filtering,
        backend=jax.default_backend(), compiler_options=arithmetic.COMPILER_OPTIONS,
    )
    runtime = dict(schema="hf-micro-trace-runtime-1", protocol=PROTOCOL, run_id=RUN_ID,
        python=sys.version, executable=sys.executable, numpy=np.__version__,
        jax=jax.__version__, jaxlib=jaxlib.__version__, actual_config=actual,
        arithmetic=dict(path=str(resolved(arithmetic.__file__)), sha256=sha(arithmetic.__file__)),
        config_mutations=0, environment_mutations=0)
    record = probe.save_json("runtime_config.json", runtime)
    probe.summary["runtime"] = runtime
    probe.summary["runtime_config_record"] = record
    probe.checkpoint()
    require(actual["backend"] == "cpu" and actual["jax_enable_x64"] is True
            and actual["jax_cpu_enable_async_dispatch"] is True
            and actual["jax_enable_compilation_cache"] is False
            and actual["jax_disable_jit"] is False
            and actual["jax_enable_pgle"] is False
            and actual["jax_debug_nans"] is False and actual["jax_debug_infs"] is False
            and arithmetic.COMPILER_OPTIONS == STRICT_OPTIONS,
            "actual runtime violates fixed CPU/x64/cache/strict/no-extra-compilation contract")
    require(np.__version__ == "2.4.6" and jax.__version__ == jaxlib.__version__ == "0.11.0",
            "numerical dependency versions differ")
    require(resolved(arithmetic.__file__) == resolved(probe.source/"src/hf_eval/compensated_invariants.py")
            and sha(arithmetic.__file__) == ARITHMETIC_SHA, "arithmetic imported from wrong source")
    return np, jax, jnp, arithmetic


def load_kernel(probe, arithmetic):
    from hf_eval import split_kernel_invariants_hu as r1
    require(resolved(r1.__file__) == resolved(probe.source/"src/hf_eval/split_kernel_invariants_hu.py")
            and sha(r1.__file__) == KERNEL_SHA and r1.ci is arithmetic
            and r1.COMPILER_OPTIONS == STRICT_OPTIONS, "R1 actual source/compiler identity differs")
    probe.summary["kernel"] = dict(path=str(resolved(r1.__file__)), sha256=sha(r1.__file__),
                                   version=r1.KERNEL_VERSION, compiler_options=r1.COMPILER_OPTIONS)
    return r1


def checked_runtime(probe):
    result = load_runtime(probe)
    previous = json.loads((probe.root/"provenance/micro_trace_001/results/trace/runtime_config.json").read_text(encoding="utf-8"))
    require(probe.summary["runtime"]["actual_config"] == previous["actual_config"],
            "actual CPU/x64/async/debug/PGLE/cache/strict config differs from frozen F-TRACE1")
    require(all(probe.summary["runtime"][name] == previous[name]
                for name in ("python", "executable", "numpy", "jax", "jaxlib")),
            "actual Python or package identity differs from frozen F-TRACE1")
    import micro_trace_v2_evidence as evidence
    probe.summary["loaded_helpers"] = evidence.record_loaded_helpers(probe.root)
    return result


def load_harness(probe):
    path = frozen_path(probe, probe.selected["hr1_test"])
    name = "_frozen_trace_hr1"
    require(name not in sys.modules, "HR1 must load once")
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, "HR1 loader unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    require(resolved(module.__file__) == path and sha(path) == HR1_SHA
            and module.PROTOCOL == "F-REUSE1" and module.RUN_ID == "force_reuse_001",
            "actual HR1 bytes/native identity differ")
    probe.summary["runtime_identity"] = dict(R1=probe.summary["kernel"],
        arithmetic=probe.summary["runtime"]["arithmetic"],
        harness=dict(path=str(path), sha256=sha(path), native_protocol=module.PROTOCOL,
                     native_run_id=module.RUN_ID, globals_changed=False))
    return module


def prepare_inputs(probe, np, jnp, r1, hr1):
    fixture = hr1.read_fixture(probe.root, np)
    # All host rows are constructed by unmodified HR1, only row zero is evaluated.
    micro_host = hr1.micro_inputs(np, r1, fixture)[0]
    reference_path = frozen_path(probe, probe.selected["reference_npz"])
    with np.load(reference_path, allow_pickle=False) as archive:
        require(len(archive.files) == 48, "historical micro reference member count differs")
        expected = {name.removeprefix("R1__"):archive[name].copy()
                    for name in archive.files if name.startswith("R1__")}
    require(len(expected) == 24, "historical R1 reference does not contain all 24 leaves")
    device = tuple(jnp.asarray(value) for value in micro_host)
    probe.summary["input_contract"] = dict(group="valid_first_three",
        cases=["identity", "shear_1_32", "shear_1_8"],
        shapes=[list(value.shape) for value in micro_host],
        dtypes=[str(value.dtype) for value in micro_host], kr=0,
        reference=probe.summary["references"]["reference_npz"], micro_leaf_count=24,
        unused_host_rows_evaluated=False)
    probe.checkpoint()
    return device, expected


def micro_function(jax, jnp, r1):
    def reused(L,w,g,h,weights,lam,mu,kr):
        batch=r1._kinematics(L,w,g,h,jnp)
        fields=jax.vmap(lambda values:values,in_axes=(r1._kinematics_vmap_axes(),))(batch)
        valid=batch["supported"] & jnp.all(batch["J"]>0) & r1._coefficient_support(weights,lam,mu,kr,jnp)
        return dict(fields=fields,global_supported=batch["supported"],valid=valid)
    return reused





def compile_graph(probe, jax, name, function, args):
    fn = jax.jit(function, compiler_options=STRICT_OPTIONS)
    traced = probe.step(name+".trace", lambda:fn.trace(*args))
    probe.step(name+".export_jaxpr", lambda:probe.export_text(name+"_raw_jaxpr.txt",
               lambda:str(traced.jaxpr)), describe=lambda value:value)
    lowered = probe.step(name+".lower", traced.lower)
    probe.step(name+".export_stablehlo", lambda:probe.export_text(name+"_stablehlo.mlir",
               lambda:lowered.as_text(dialect="stablehlo", debug_info=False)), describe=lambda value:value)
    compiled = probe.step(name+".compile", lambda:lowered.compile(compiler_options=STRICT_OPTIONS))
    probe.step(name+".export_optimized_hlo", lambda:probe.export_text(name+"_optimized_hlo.txt",
               compiled.as_text), describe=lambda value:value)
    return compiled


def compare_output(probe, np, hr1, name, arrays, expected, artifact):
    # The complete actual arrays were fsynced, hashed and checkpointed first.
    comparison = dict(status="running", artifact=artifact, fields={},
                      expected_kind="historical_R1_24_leaves")
    probe.summary["comparisons"][name] = comparison
    probe.checkpoint()
    require(set(arrays) == set(expected) and len(arrays) == 24,
            name+": complete original leaf mapping differs")
    for key in sorted(expected):
        comparison["fields"][key] = hr1.compare_array(np, arrays[key], expected[key],
            name+"/"+key, finite_required=True)
    require(arrays["global_supported"].shape == arrays["valid"].shape == ()
            and bool(arrays["global_supported"]) and bool(arrays["valid"]),
            name+": valid first group was rejected")
    comparison.update(status="pass", field_count=len(comparison["fields"]))
    probe.checkpoint()
    return comparison


def observe_output(probe, np, jax, hr1, name, compiled, args, expected, *, ready_only):
    value = probe.step(name+".call", lambda:compiled(*args))
    probe.step(name+".synchronize", lambda:jax.block_until_ready(value))
    if ready_only:
        # The identical complete object, before any flatten/transfer/inspection.
        probe.step(name+".ready_only", lambda:jax.block_until_ready(value))
    transferred = probe.step(name+".transfer", lambda:jax.tree.map(np.asarray, value))
    arrays = hr1.flatten_arrays(transferred)
    artifact = probe.step(name+".save_output", lambda:probe.save_arrays(np, name+".npz", arrays),
                          describe=lambda record:record)
    probe.step(name+".compare", lambda:compare_output(probe, np, hr1, name, arrays, expected, artifact),
               describe=lambda record:record)


def completed_contract(probe):
    steps = probe.summary["steps"]
    require([row["stage"] for row in steps] == list(STAGES)
            and all(row["status"] == "pass" for row in steps), "incomplete fixed stage sequence")
    names = [row["stage"] for row in steps]
    counts = dict(graph_count=names.count("micro.trace"), trace=names.count("micro.trace"),
        lower=names.count("micro.lower"), compile=names.count("micro.compile"),
        compiled_call=sum(name.endswith(".call") for name in names),
        output_synchronization=sum(name.endswith(".synchronize") for name in names),
        ready_only=sum(name.endswith(".ready_only") for name in names),
        input_ready=names.count("input_ready"), micro_leaf_count=24,
        profiler_start=probe.summary["profiler"]["start_attempts"],
        profiler_stop=probe.summary["profiler"]["stop_attempts"],
        annotations=sum("function_measurement" in row.get("value", {}) for row in steps),
        warmup=0, retries=0, force_calls=0, ad_calls=0)
    require(all(counts[key] == EXECUTION_CONTRACT[key] for key in counts), "actual counts differ")
    require(list(probe.summary["comparisons"]) == list(OUTPUT_ORDER)
            and all(row["status"] == "pass" and row["field_count"] == 24
                    for row in probe.summary["comparisons"].values()), "comparisons incomplete")
    expected_artifacts = {"trace_controls.json", "environment.json", "runtime_config.json",
        "native_inventory.json", "native_analysis.json", *(name+".npz" for name in OUTPUT_ORDER),
        *("micro"+suffix for suffix in ("_raw_jaxpr.txt", "_stablehlo.mlir", "_optimized_hlo.txt"))}
    require(set(probe.summary["artifacts"]) == expected_artifacts
            and all(row["status"] == "complete" for row in probe.summary["artifacts"].values()),
            "required artifacts incomplete")
    profile = probe.summary["profiler"]
    require(profile["start_returned"] is True and profile["body_returned"] is True
            and profile["stop_returned"] is True and profile["body_attempts"] == 1
            and all(profile.get(name) is None for name in ("first_error", "shutdown_error",
                "start_error", "body_error", "stop_error", "pre_body_error", "native_start_error", "native_stop_error"))
            and probe.summary["first_error"] is None and not probe.summary["secondary_record_errors"]
            and probe.summary["controls_passed"] == 16, "native lifecycle did not close without errors")
    probe.summary["compiler_options_execution"] = dict(jax_jit=dict(STRICT_OPTIONS), lowered_compile=dict(STRICT_OPTIONS),
        jax_jit_returned=True, lowered_compile_returned=True, frozen_ast_verified=True)
    probe.summary["completed_counts"] = counts
    probe.summary["numerical_contract_pass"] = True
    probe.summary["runtime_native_trace_observed"] = (
        probe.summary["native_analysis"]["result"]["status"] == "runtime_native_trace_observed")


def load_profiler(probe):
    # These are the real installed interfaces; no ProfileOptions object, server,
    # alternate collector, or native capability trial is created here.
    import jax.profiler as public
    from jax._src import profiler as internal
    from jax._src import lib
    import micro_trace_v2_evidence as evidence
    site = resolved(Path(sys.prefix)/"Lib/site-packages")
    modules = {
        "jax/profiler.py": public, "jax/_src/profiler.py": internal,
        "jax/_src/lib/__init__.py": lib, "jaxlib/_profiler.pyd": lib._profiler,
        "jaxlib/_profile_data.pyd": lib._profile_data,
    }
    identities = {}
    for relative, module in modules.items():
        path = resolved(module.__file__)
        size, digest = PROFILER_PINS[relative]
        require(path == resolved(site/relative) and path.stat().st_size == size and sha(path) == digest,
                "actual profiler import differs from the fixed installed file: "+relative)
        identities[relative] = dict(path=str(path), bytes=size, sha256=digest,
                                   module=module.__name__, actual_import=True)
    binary_path = resolved(site/"jaxlib/jax_common.dll")
    size, digest = PROFILER_PINS["jaxlib/jax_common.dll"]
    require(binary_path.stat().st_size == size and sha(binary_path) == digest,
            "installed common profiler binary differs")
    verification = evidence.verify_inputs(probe.root, include_live=True)
    require(verification["status"] == "verified", "pre-profiler source verification failed")
    require(public.start_trace is internal.start_trace and public.stop_trace is internal.stop_trace
            and public.TraceAnnotation is internal.TraceAnnotation,
            "public profiler is not the pinned implementation")
    require(internal._profile_state.profile_session is None,
            "this process already has a profiler session; no adoption or retry")
    with (probe.output/"micro_optimized_hlo.txt").open("r", encoding="utf-8") as stream:
        first_line = stream.readline(65537)
    match = re.match(r"^HloModule ([^,\s]+),", first_line)
    require(match is not None and match.group(1) == "jit_reused", "fixed micro HLO module identity unavailable")
    probe.summary["micro_hlo_module"] = match.group(1)
    probe.summary["profiler_runtime"] = dict(
        installed_modules=identities,
        installed_binary=dict(path=str(binary_path), bytes=size, sha256=digest,
            copied=False, interpretation="installed file pin; not a loaded-DLL enumeration"),
        source_verification=verification, preexisting_session=False,
        options_requested=None, effective_defaults="native_not_exposed",
        extra_native_sessions=0, options_mutated=False)
    probe.profiler_module = public
    probe.checkpoint()
    return public


def start_profile(probe, profiler):
    import micro_trace_v2_evidence as evidence
    lifecycle = probe.summary["profiler"]
    require(lifecycle["start_attempts"] == 0 and lifecycle["stop_attempts"] == 0,
            "profiler session may be started only once")
    plan = json.loads((probe.root/"plan.json").read_text(encoding="utf-8"))
    argument = evidence.actual_native_path(probe.root, plan, create=True)
    lifecycle["path_evidence"] = dict(argument=argument, characters=len(argument), evidence_path="native",
        ordinary_drive_absolute=True, samefile_verified=True, ancestors_no_reparse=True,
        plugins_precreated=False, fallback=False)
    probe.checkpoint()
    remaining = probe.active_deadline-time.monotonic()
    lifecycle["start_admission"] = dict(remaining_seconds=remaining, minimum_remaining_seconds=20.0,
                                       active_deadline_monotonic=probe.active_deadline)
    require(remaining >= 20.0, "less than 20 seconds remain before unique profiler start")
    begin = time.monotonic()
    lifecycle.update(start_attempts=1, start_status="not_returned", start_requested_monotonic=begin)
    # The only real start call. No fallible log/checkpoint is between gate and API.
    try:
        profiler.start_trace(argument, create_perfetto_link=False,
                             create_perfetto_trace=False, profiler_options=None)
    except BaseException as error:
        probe.native_start_exception = error
        if probe.first_exception is None:
            probe.first_exception = error
        ended = time.monotonic()
        lifecycle.update(start_status="raised", start_api_end_monotonic=ended,
                         start_api_elapsed_seconds=ended-begin)
        detail = probe.remember_error(error, "profiler.start", kind="native_interface")
        lifecycle.update(native_start_error=detail, start_error=detail)
        raise
    # Latch immediately on the actual return, before any persistence operation.
    lifecycle["start_returned"] = True
    ended = time.monotonic()
    lifecycle.update(start_status="returned", start_returned_monotonic=ended,
                     start_api_end_monotonic=ended, start_api_elapsed_seconds=ended-begin)
    return dict(start_attempts=1, start_returned=True, log_dir="native", native_argument=argument,
                requested_options=None, effective_defaults="native_not_exposed")


def stop_profile_once(probe, profiler):
    """One real stop; its two stage events are written after the API ends.

    The start event contains the in-memory actual request time. EventLog's own
    monotonic clock is the real later write time, not a forged prior event.
    Exception materialization is timed separately from the native API interval.
    """
    lifecycle = probe.summary["profiler"]
    require(lifecycle["start_returned"] and lifecycle["stop_attempts"] == 0,
            "shutdown requires the sole returned start and zero prior attempts")
    requested = time.monotonic()
    lifecycle.update(stop_attempts=1, stop_status="not_returned", stop_requested_monotonic=requested)
    native_error = None
    begin = time.monotonic()
    # No event, checkpoint, traceback conversion or file I/O precedes the stop.
    try:
        profiler.stop_trace()
    except BaseException as error:
        native_error = error
        probe.native_stop_exception = error
        if probe.first_exception is None:
            probe.first_exception = error
        ended = time.monotonic()
        lifecycle["stop_status"] = "raised"
    else:
        lifecycle["stop_returned"] = True
        ended = time.monotonic()
        lifecycle["stop_status"] = "returned"
    lifecycle.update(stop_completed_monotonic=ended, stop_api_start_monotonic=begin,
                     stop_api_end_monotonic=ended, stop_api_elapsed_seconds=ended-begin)
    detail = None
    if native_error is not None:
        detail = probe.remember_error(native_error, "profiler.stop", kind="native_interface")
        lifecycle.update(native_stop_error=detail, stop_error=detail, shutdown_error=detail,
                         shutdown_failure_kind="native_only")
        lifecycle["shutdown_errors"].append(detail)
    else:
        lifecycle["shutdown_failure_kind"] = "none"
    row = dict(stage="profiler.stop", status="failed" if native_error is not None else "pass",
        started_monotonic=requested, started_utc=None, recorded_utc=utc(), elapsed_seconds=ended-begin,
        execution_start_monotonic=begin, completed_monotonic=ended, finished_utc=utc(),
        after_body_failure=lifecycle["first_error"] is not None,
        stage_events_written_after_native_completion=True,
        value=dict(stop_attempts=1, stop_returned=lifecycle["stop_returned"]))
    if detail is not None:
        row["error"] = detail
    probe.summary["steps"].append(row)
    record_error = None
    try:
        probe.checkpoint()
        probe.emit("stage_started", stage="profiler.stop", outcome="running", stage_start_monotonic=requested,
                   actual_api_start_monotonic=begin, actual_api_end_monotonic=ended,
                   written_after_native_completion=True)
        if native_error is None:
            probe.emit("stage_finished", stage="profiler.stop", outcome="pass", duration=ended-begin,
                       execution_start_monotonic=begin, completed_monotonic=ended,
                       written_after_native_completion=True)
        else:
            probe.emit("stage_failed", stage="profiler.stop", outcome="error", exception=detail,
                       exception_type=detail["type"], traceback=detail.get("traceback"), duration=ended-begin,
                       execution_start_monotonic=begin, completed_monotonic=ended,
                       written_after_native_completion=True)
        probe.checkpoint()
    except BaseException as error:
        record_error = error
        record_detail = probe.remember_error(error, "profiler.stop.persistence")
        probe.secondary_record_error(error, "profiler.stop.persistence")
        lifecycle["shutdown_errors"].append(record_detail)
        if lifecycle["shutdown_error"] is None:
            lifecycle["shutdown_error"] = record_detail
        lifecycle["shutdown_failure_kind"] = "native_and_evidence" if native_error is not None else "evidence_only"
        row.update(status="failed", error=lifecycle["shutdown_error"])
    return native_error if native_error is not None else record_error


def collect_native(probe):
    import micro_trace_v2_evidence as evidence
    lifecycle = probe.summary["profiler"]
    require(lifecycle["start_returned"] and lifecycle["stop_returned"],
            "native collection requires a returned stop/export")
    result = evidence.collect_native(probe.root, frozen_path(probe, lifecycle["log_dir"]),
                                     deadline=probe.active_deadline)
    record = probe.save_json("native_inventory.json", result)
    probe.summary["native_inventory"] = dict(result=result, artifact=record)
    probe.checkpoint()
    if result.get("status") != "complete":
        raise ObservabilityFailure("native export is incomplete or outside the bounded acceptance contract")
    return dict(status=result["status"], artifact=record)


def analyze_native(probe):
    import micro_trace_v2_evidence as evidence
    result = evidence.analyze_native(probe.root, probe.summary["native_inventory"]["result"], probe.summary)
    record = probe.save_json("native_analysis.json", result)
    probe.summary["native_analysis"] = dict(result=result, artifact=record)
    probe.checkpoint()
    require(result.get("status") in ("runtime_native_trace_observed", "observability_not_pass"),
            "native parser did not return a declared observation outcome")
    if result["status"] != "runtime_native_trace_observed":
        raise ObservabilityFailure("saved native trace does not satisfy the fixed internal source and annotation gates",
                                   kind="observability")
    return dict(status=result["status"], artifact=record)


def observe(probe):
    probe.step("trace_controls", lambda:trace_controls(probe), describe=lambda value:value)
    probe.step("source_binding", lambda:verify_sources(probe, initial=True), describe=lambda value:value)
    probe.step("environment_snapshot", lambda:environment_snapshot(probe), describe=lambda value:value)
    np, jax, jnp, arithmetic = probe.step("runtime_import", lambda:checked_runtime(probe))
    r1 = probe.step("kernel_import", lambda:load_kernel(probe, arithmetic))
    hr1 = probe.step("harness_import", lambda:load_harness(probe))
    args, expected = probe.step("input_prepare", lambda:prepare_inputs(probe, np, jnp, r1, hr1))
    probe.step("input_ready", lambda:jax.block_until_ready(args))
    micro = compile_graph(probe, jax, "micro", micro_function(jax, jnp, r1), args)
    profiler = probe.step("profiler_binding", lambda:load_profiler(probe), describe=lambda _:probe.summary["profiler_runtime"])
    first_error = None
    try:
        probe.step("profiler.start", lambda:start_profile(probe, profiler), describe=lambda value:value)
        probe.summary["profiler"]["body_attempts"] = 1
        observe_output(probe, np, jax, hr1, "micro_first", micro, args, expected, ready_only=True)
        observe_output(probe, np, jax, hr1, "micro_repeat", micro, args, expected, ready_only=False)
        probe.summary["profiler"]["body_returned"] = True
        probe.summary["numerical_contract_pass"] = True
    except BaseException as error:
        first_error = probe.first_exception if probe.first_exception is not None else error
        detail = retain_error(probe, first_error, "profiler.body",
            kind="native_interface" if first_error is probe.native_start_exception else "execution")
        try:
            life = probe.summary["profiler"]
            life["first_error"] = detail
            if life["body_attempts"]:
                life["body_error"] = detail
            elif life["start_returned"]:
                life["pre_body_error"] = detail
        except BaseException as record_error:
            retain_secondary_record_error(probe, record_error, "profiler.body.record")
    finally:
        shutdown_error = None
        try:
            if probe.summary["profiler"]["start_returned"]:
                shutdown_error = stop_profile_once(probe, profiler)
        except BaseException as record_error:
            # stop_profile_once may have performed the sole real stop already.
            # Never re-enter it. Its later utc/materialization/row/write failure
            # remains secondary to a body error or the latched native error.
            shutdown_error = record_error
            if probe.first_exception is None:
                probe.first_exception = (probe.native_stop_exception
                    if probe.native_stop_exception is not None else record_error)
            retain_shutdown_record_error(probe, record_error, "profiler.stop.wrapper")
    primary = probe.first_exception if probe.first_exception is not None else first_error
    if primary is None:
        primary = shutdown_error
    if primary is not None:
        if shutdown_error is not None and shutdown_error is not primary:
            raise primary from shutdown_error
        raise primary
    probe.step("native.collect", lambda:collect_native(probe), describe=lambda value:value)
    probe.step("native.analyze", lambda:analyze_native(probe), describe=lambda value:value)
    probe.step("source_preservation", lambda:verify_sources(probe, initial=False), describe=lambda value:value)
    completed_contract(probe)


def failure_status(probe, error):
    """Classify the actual first exception; bookkeeping never becomes native."""
    if isinstance(error, ObservabilityFailure):
        return "observability_not_pass"
    if error is probe.native_start_exception:
        return "observability_not_pass"
    if error is probe.native_stop_exception:
        return "observability_not_pass"
    return "failed"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path)
    args = parser.parse_args()
    prepared_root = early_path(args.root)
    bootstrap_helpers(prepared_root)
    log = EventLog()
    probe = None
    primary = None
    try:
        log.emit("probe_started", protocol=PROTOCOL, campaign_protocol=PROTOCOL,
                 run_id=RUN_ID, mode="trace", outcome="running", scientific_imports_started=False,
                 scientific_admission=False, harness_id=os.environ.get("HF_HARNESS_ID"),
                 harness_manifest_sha256=os.environ.get("HF_HARNESS_MANIFEST_SHA"))
        root, source = resolved(args.root), resolved(args.source)
        require(root.is_dir() and (root/"input_manifest.json").is_file(), "prepared root is absent")
        probe = TraceProbe(root, source, log)
        try:
            observe(probe)
        except BaseException as error:
            primary = probe.first_exception if probe.first_exception is not None else error
            retain_error(probe, primary, "probe")
            try:
                probe.finish(failure_status(probe, primary))
            except BaseException as record_error:
                retain_secondary_record_error(probe, record_error, "probe.finish")
            raise primary
        if not probe.summary["runtime_native_trace_observed"]:
            probe.finish("observability_not_pass")
            raise SystemExit(2)
        probe.finish("runtime_native_trace_observed")
    except BaseException as error:
        primary = (probe.first_exception if probe is not None and probe.first_exception is not None else error)
        if probe is not None:
            retain_error(probe, primary, "probe.main")
    finally:
        try:
            log.close()
        except BaseException as close_error:
            if primary is None:
                primary = (probe.first_exception if probe is not None and probe.first_exception is not None else close_error)
            if probe is not None:
                retain_secondary_record_error(probe, close_error, "probe.event_log.close")
    if primary is not None:
        raise primary


if __name__ == "__main__":
    main()
