"""F-COST1: two fixed graphs, four calls and two already-ready observations.

The parent owns the sole wall/RSS budget and Job. Imports above the explicit
runtime stage are standard-library-only. This is a runtime observation, not a
full force, AD, HP, or equilibrium qualification. No warmup or retry is used.
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

import s0_ad_exception as ad_evidence
import s0_event_log as event_module
from s0_event_log import EventLog, EventLogError


SCHEMA = "hf-force-cost-probe-1"
PROTOCOL = "F-COST1"
RUN_ID = "force_cost_001"
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
    "interval_controls", "source_binding", "environment_snapshot", "runtime_import",
    "kernel_import", "harness_import", "input_prepare", "input_ready",
    "tiny.trace", "tiny.export_jaxpr", "tiny.lower", "tiny.export_stablehlo",
    "tiny.compile", "tiny.export_optimized_hlo",
    "micro.trace", "micro.export_jaxpr", "micro.lower", "micro.export_stablehlo",
    "micro.compile", "micro.export_optimized_hlo",
    "tiny_before.call", "tiny_before.synchronize", "tiny_before.ready_only",
    "tiny_before.transfer", "tiny_before.save_output", "tiny_before.compare",
    "micro_first.call", "micro_first.synchronize", "micro_first.ready_only",
    "micro_first.transfer", "micro_first.save_output", "micro_first.compare",
    "micro_repeat.call", "micro_repeat.synchronize", "micro_repeat.transfer",
    "micro_repeat.save_output", "micro_repeat.compare",
    "tiny_after.call", "tiny_after.synchronize", "tiny_after.transfer",
    "tiny_after.save_output", "tiny_after.compare", "source_preservation",
)
EXECUTION_CONTRACT = dict(
    graph_count=2, trace=2, lower=2, compile=2, compiled_call=4,
    output_synchronization=4, ready_only=2, input_ready=1, micro_leaf_count=24,
    warmup=0, retries=0, force_calls=0, ad_calls=0,
)
OUTPUT_ORDER = ("tiny_before", "micro_first", "micro_repeat", "tiny_after")
TEXT_CHUNK_CHARS = 1024 * 1024


class CostObservationFailure(RuntimeError):
    pass


def require(condition, message):
    if not condition:
        raise CostObservationFailure(message)


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


class CostProbe:
    def __init__(self, root, source, log):
        self.root, self.source, self.log = root, source, log
        self.output = root/"results/cost"
        self.output.mkdir(parents=True, exist_ok=False)
        self.started = time.monotonic()
        self.selected = None
        self.manifest = None
        self.summary = dict(
            schema=SCHEMA, protocol=PROTOCOL, campaign_protocol=PROTOCOL,
            run_id=RUN_ID, mode="cost", phase="P1_cost", source_version="R1",
            source=str(source), source_manifest_sha256=log.source_manifest_sha256,
            events_file=str(log.path), started_utc=utc(), status="running",
            runtime_cost_diagnostic_complete=False, scientific_admission=False,
            force_executed=False, new_hp_evaluations=0, new_equilibrium_paths=0,
            expected_stages=list(STAGES), execution_contract=dict(EXECUTION_CONTRACT),
            steps=[], errors=[], artifacts={}, comparisons={},
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
            run_id=RUN_ID, mode="cost", harness_id=os.environ.get("HF_HARNESS_ID"),
            harness_manifest_sha256=os.environ.get("HF_HARNESS_MANIFEST_SHA"), **fields)

    def step(self, stage, function, *, describe=None):
        index = len(self.summary["steps"])
        require(index < len(STAGES) and STAGES[index] == stage,
                "unexpected or repeated cost stage: "+stage)
        started = time.monotonic()
        row = dict(stage=stage, status="running", started_utc=utc(),
                   started_monotonic=started)
        self.summary["steps"].append(row)
        self.checkpoint()
        self.emit("stage_started", stage=stage, outcome="running",
                  stage_start_monotonic=started)
        begin = time.monotonic()
        try:
            value = function()
            ended = time.monotonic()
            record = dict(status="pass", elapsed_seconds=ended-begin,
                execution_start_monotonic=begin, completed_monotonic=ended,
                finished_utc=utc())
            if describe is not None:
                record["value"] = describe(value)
        except EventLogError:
            raise
        except Exception as error:
            detail = ad_evidence.exception_details(error)
            detail["stage"] = stage
            row.update(status="failed", elapsed_seconds=time.monotonic()-begin,
                       finished_utc=utc(), error=detail)
            self.summary["errors"].append(detail)
            self.checkpoint()
            self.emit("stage_failed", stage=stage, outcome="error", exception=detail,
                      exception_type=detail["type"], traceback=detail["traceback"],
                      duration=row["elapsed_seconds"])
            raise
        row.update(record)
        self.checkpoint()
        self.emit("stage_finished", stage=stage, outcome="pass",
            duration=record["elapsed_seconds"], execution_start_monotonic=begin,
            completed_monotonic=ended)
        return value

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
            runtime_cost_diagnostic_complete=self.summary["runtime_cost_diagnostic_complete"],
            duration=self.summary["elapsed_seconds"], scientific_admission=False)


def frozen_path(probe, value):
    require(isinstance(value, str) and bool(value), "missing selected source path")
    path = resolved(probe.root/value)
    require(path.is_relative_to(probe.root), "selected source path escaped root")
    return path


def interval_controls(probe):
    import force_cost_evidence as evidence
    require(resolved(evidence.__file__) == resolved(probe.root/"aux/hf_repo/scripts/force_cost_evidence.py"),
            "CPU analysis helper escaped frozen aux")
    result = evidence.interval_controls()
    record = probe.save_json("interval_controls.json", result)
    probe.summary["interval_controls"] = dict(result=result, artifact=record)
    probe.checkpoint()
    require(result.get("status") == "pass" and len(result.get("cases", [])) == 4,
            "the four controls of the actual CPU analysis did not pass")
    return dict(status="pass", case_count=4, artifact=record)


def verify_sources(probe, *, initial):
    import force_cost_evidence as evidence
    aux = probe.root/"aux/hf_repo/scripts"
    for module, filename in ((event_module, "s0_event_log.py"),
            (ad_evidence, "s0_ad_exception.py"), (evidence, "force_cost_evidence.py")):
        require(resolved(module.__file__) == resolved(aux/filename),
                "helper import escaped frozen aux: "+filename)
    require(resolved(__file__) == resolved(aux/"probe_force_cost.py"), "probe must be frozen aux")
    require(probe.log.phase == "P1_cost" and probe.log.version == "R1",
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
    probe.checkpoint()
    return dict(status="pass", verification=verification, micro_ast=ast_check)


def environment_snapshot(probe):
    require(not any(name == "jax" or name.startswith("jax.") or name == "numpy"
                    or name.startswith("numpy.") for name in sys.modules),
            "scientific module was imported before the environment snapshot")
    value = dict(schema="hf-force-cost-environment-1", protocol=PROTOCOL, run_id=RUN_ID,
        captured_utc=utc(), captured_monotonic=time.monotonic(), scientific_imports_started=False,
        variables={name:dict(present=name in os.environ, value=os.environ.get(name))
                   for name in ENVIRONMENT_NAMES}, interpretation="present raw strings, not effective config")
    record = probe.save_json("environment.json", value)
    probe.summary["environment"] = dict(artifact=record, **value)
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
    runtime = dict(schema="hf-force-cost-runtime-1", protocol=PROTOCOL, run_id=RUN_ID,
        python=sys.version, executable=sys.executable, numpy=np.__version__,
        jax=jax.__version__, jaxlib=jaxlib.__version__, actual_config=actual,
        arithmetic=dict(path=str(resolved(arithmetic.__file__)), sha256=sha(arithmetic.__file__)),
        config_mutations=0, environment_mutations=0)
    record = probe.save_json("runtime_config.json", runtime)
    probe.summary["runtime"] = runtime
    probe.summary["runtime_config_record"] = record
    probe.checkpoint()
    require(actual["backend"] == "cpu" and actual["jax_enable_x64"] is True
            and actual["jax_enable_compilation_cache"] is False
            and actual["jax_disable_jit"] is False
            and actual["jax_enable_pgle"] is False
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


def load_harness(probe):
    path = frozen_path(probe, probe.selected["hr1_test"])
    name = "_frozen_cost_hr1"
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
    # HR1 constructs all eight host rows; only its unchanged first row is sent
    # to the device. The other seven are neither evaluated nor qualified here.
    micro_host = hr1.micro_inputs(np, r1, fixture)[0]
    reference_path = frozen_path(probe, probe.selected["reference_npz"])
    with np.load(reference_path, allow_pickle=False) as archive:
        require(len(archive.files) == 48, "historical micro reference member count differs")
        expected = {name.removeprefix("R1__"):archive[name].copy()
                    for name in archive.files if name.startswith("R1__")}
    require(len(expected) == 24, "historical R1 reference does not contain all 24 leaves")
    tiny_host = np.full((3,8), 1.25, dtype=np.float64)
    device = dict(tiny=(jnp.asarray(tiny_host),),
                  micro=tuple(jnp.asarray(value) for value in micro_host))
    probe.summary["input_contract"] = dict(group="valid_first_three",
        cases=["identity", "shear_1_32", "shear_1_8"],
        shapes=[list(value.shape) for value in micro_host],
        dtypes=[str(value.dtype) for value in micro_host], kr=0,
        reference=probe.summary["references"]["reference_npz"], micro_leaf_count=24,
        tiny_shape=[3,8], tiny_input=1.25, tiny_expected=2.5,
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


def tiny_function(x):
    return x+x


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
    # All actual bytes were durably saved, hashed and checkpointed first.
    comparison = dict(status="running", artifact=artifact, fields={},
                      expected_kind="historical_R1_24_leaves" if name.startswith("micro") else "exact_dyadic")
    probe.summary["comparisons"][name] = comparison
    probe.checkpoint()
    if name.startswith("micro"):
        require(set(arrays) == set(expected) and len(arrays) == 24,
                name+": complete original leaf mapping differs")
        for key in sorted(expected):
            comparison["fields"][key] = hr1.compare_array(np, arrays[key], expected[key],
                name+"/"+key, finite_required=True)
        require(arrays["global_supported"].shape == arrays["valid"].shape == ()
                and bool(arrays["global_supported"]) and bool(arrays["valid"]),
                name+": valid first group was rejected")
    else:
        require(set(arrays) == {"value"}, name+": tiny output keys differ")
        target = np.full((3,8), 2.5, dtype=np.float64)
        comparison["fields"]["value"] = hr1.compare_array(np, arrays["value"], target,
                                                          name, finite_required=True)
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
    arrays = hr1.flatten_arrays(transferred) if name.startswith("micro") else {"value":transferred}
    artifact = probe.step(name+".save_output", lambda:probe.save_arrays(np, name+".npz", arrays),
                          describe=lambda record:record)
    probe.step(name+".compare", lambda:compare_output(probe, np, hr1, name, arrays, expected, artifact),
               describe=lambda record:record)


def completed_contract(probe):
    steps = probe.summary["steps"]
    require([row["stage"] for row in steps] == list(STAGES)
            and all(row["status"] == "pass" for row in steps), "incomplete fixed stage sequence")
    names = [row["stage"] for row in steps]
    counts = dict(graph_count=sum(name.endswith(".trace") for name in names),
        trace=sum(name.endswith(".trace") for name in names),
        lower=sum(name.endswith(".lower") for name in names),
        compile=sum(name.endswith(".compile") for name in names),
        compiled_call=sum(name.endswith(".call") for name in names),
        output_synchronization=sum(name.endswith(".synchronize") for name in names),
        ready_only=sum(name.endswith(".ready_only") for name in names),
        input_ready=names.count("input_ready"), micro_leaf_count=24)
    require(all(counts[key] == EXECUTION_CONTRACT[key] for key in counts), "actual call counts differ")
    require(list(probe.summary["comparisons"]) == list(OUTPUT_ORDER)
            and all(row["status"] == "pass" and row["field_count"] == (24 if name.startswith("micro") else 1)
                    for name,row in probe.summary["comparisons"].items()), "comparisons incomplete")
    expected_artifacts = {"interval_controls.json", "environment.json", "runtime_config.json",
        *(name+".npz" for name in OUTPUT_ORDER),
        *(name+suffix for name in ("tiny", "micro") for suffix in
          ("_raw_jaxpr.txt", "_stablehlo.mlir", "_optimized_hlo.txt"))}
    require(set(probe.summary["artifacts"]) == expected_artifacts
            and all(row["status"] == "complete" for row in probe.summary["artifacts"].values()),
            "required artifacts incomplete")
    probe.summary["completed_counts"] = counts
    probe.summary["runtime_cost_diagnostic_complete"] = True


def observe(probe):
    probe.step("interval_controls", lambda:interval_controls(probe), describe=lambda value:value)
    probe.step("source_binding", lambda:verify_sources(probe, initial=True), describe=lambda value:value)
    probe.step("environment_snapshot", lambda:environment_snapshot(probe), describe=lambda value:value)
    np, jax, jnp, arithmetic = probe.step("runtime_import", lambda:load_runtime(probe))
    r1 = probe.step("kernel_import", lambda:load_kernel(probe, arithmetic))
    hr1 = probe.step("harness_import", lambda:load_harness(probe))
    device, expected = probe.step("input_prepare", lambda:prepare_inputs(probe, np, jnp, r1, hr1))
    probe.step("input_ready", lambda:jax.block_until_ready(device))
    tiny = compile_graph(probe, jax, "tiny", tiny_function, device["tiny"])
    micro = compile_graph(probe, jax, "micro", micro_function(jax, jnp, r1), device["micro"])
    observe_output(probe, np, jax, hr1, "tiny_before", tiny, device["tiny"], expected, ready_only=True)
    observe_output(probe, np, jax, hr1, "micro_first", micro, device["micro"], expected, ready_only=True)
    observe_output(probe, np, jax, hr1, "micro_repeat", micro, device["micro"], expected, ready_only=False)
    observe_output(probe, np, jax, hr1, "tiny_after", tiny, device["tiny"], expected, ready_only=False)
    probe.step("source_preservation", lambda:verify_sources(probe, initial=False), describe=lambda value:value)
    completed_contract(probe)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path)
    args = parser.parse_args()
    with EventLog() as log:
        log.emit("probe_started", protocol=PROTOCOL, campaign_protocol=PROTOCOL,
                 run_id=RUN_ID, mode="cost", outcome="running", scientific_imports_started=False,
                 scientific_admission=False, harness_id=os.environ.get("HF_HARNESS_ID"),
                 harness_manifest_sha256=os.environ.get("HF_HARNESS_MANIFEST_SHA"))
        root, source = resolved(args.root), resolved(args.source)
        require(root.is_dir() and (root/"input_manifest.json").is_file(), "prepared root is absent")
        probe = CostProbe(root, source, log)
        try:
            observe(probe)
        except EventLogError:
            raise
        except Exception as error:
            detail = ad_evidence.exception_details(error)
            detail["stage"] = "probe"
            probe.summary["errors"].append(detail)
            probe.finish("failed")
            raise
        probe.finish("runtime_cost_diagnostic_complete")


if __name__ == "__main__":
    main()
