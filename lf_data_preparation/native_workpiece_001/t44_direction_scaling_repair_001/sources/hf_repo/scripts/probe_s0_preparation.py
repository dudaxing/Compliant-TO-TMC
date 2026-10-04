"""Frozen-source S0 controls and one saved-element execution-cost probe.

Scientific imports occur only after the first durable event. This program is
not a benchmark retry loop, HP evaluator, or scientific admission test. The
parent owns its process, wall/RSS limits and the single shared deadline.
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

from s0_event_log import EventLog, EventLogError


STRICT_OPTIONS = {"xla_cpu_enable_fast_math": False, "xla_cpu_ftz": False}
CONTROL_OPERATIONS = ("primal", "jvp", "vjp_construct", "pullback",
                      "closed_form", "duality", "linearized_jaxpr")


class NumericalCheckFailure(AssertionError):
    pass


class SourceFailure(RuntimeError):
    pass


class ProbeFailure(RuntimeError):
    pass


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def require(value, message, kind=ProbeFailure):
    if not value:
        raise kind(message)


def write_text(path, body):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(body)
        stream.flush()
        os.fsync(stream.fileno())


def dump(path, value):
    body = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    write_text(path, body)


class Probe:
    def __init__(self, root, source, mode, log):
        self.root, self.source, self.mode, self.log = root, source, mode, log
        self.output = root / "results" / mode
        self.output.mkdir(parents=True, exist_ok=False)
        self.started = time.monotonic()
        self.summary = dict(schema="hf-s0-preparation-probe-1", mode=mode,
            status="running", source=str(source),
            source_manifest_sha256=os.environ.get("HF_S0_SOURCE_MANIFEST_SHA"),
            events_file=os.environ.get("HF_S0_EVENT_FILE"), started_utc=utc(),
            steps=[], errors=[], artifacts={}, mechanical_admission=False,
            new_equilibrium_paths=0, new_hp_evaluations=0)
        self.checkpoint()

    def checkpoint(self):
        path = self.output / "summary.json"
        temporary = self.output / "summary.pending.json"
        dump(temporary, self.summary)
        os.replace(temporary, path)

    def artifact(self, path):
        path = Path(path)
        result = dict(path=path.relative_to(self.output).as_posix(),
                      bytes=path.stat().st_size, sha256=sha(path))
        self.summary["artifacts"][result["path"]] = result
        return result

    def step(self, stage, function, *, destination=None, describe=None,
             allow_diagnostic_error=False):
        row = dict(stage=stage, status="running", started_utc=utc())
        self.summary["steps"].append(row)
        if destination is not None:
            destination.clear()
            destination.update(row)
        self.checkpoint()
        self.log.emit("stage_started", stage=stage, outcome="running")
        begin = time.monotonic()
        try:
            value = function()
            record = dict(status="pass", elapsed_seconds=time.monotonic()-begin,
                          finished_utc=utc())
            if describe is not None:
                record["value"] = describe(value)
        except EventLogError:
            raise
        except Exception as error:
            detail = dict(type=type(error).__name__, message=str(error),
                          traceback=traceback.format_exc(), stage=stage)
            record = dict(status="failed", elapsed_seconds=time.monotonic()-begin,
                          finished_utc=utc(), error=detail)
            row.update(record)
            if destination is not None:
                destination.update(record)
            self.summary["errors"].append(detail)
            self.checkpoint()
            self.log.emit("stage_failed", stage=stage, outcome="error",
                          exception_type=detail["type"], traceback=detail["traceback"],
                          message=detail["message"], duration=record["elapsed_seconds"])
            # Only predeclared VJP construction/pullback interface exceptions
            # are observations. A numerical failure is never swallowed.
            if (allow_diagnostic_error and isinstance(error, AssertionError)
                    and not isinstance(error, NumericalCheckFailure)):
                return False, None
            raise
        row.update(record)
        if destination is not None:
            destination.update(record)
        self.checkpoint()
        self.log.emit("stage_finished", stage=stage, outcome="pass",
                      duration=record["elapsed_seconds"])
        return True, value

    def finish(self, status):
        self.summary.update(status=status, finished_utc=utc(),
                            elapsed_seconds=time.monotonic()-self.started)
        self.checkpoint()
        self.log.emit("probe_finished", mode=self.mode, outcome=status,
                      duration=self.summary["elapsed_seconds"])


def runtime(probe):
    # main has durably emitted probe_started before any scientific import.
    sys.dont_write_bytecode = True
    os.environ["JAX_TRACEBACK_FILTERING"] = "off"
    sys.path.insert(0, str(probe.source / "src"))
    import numpy as np
    import jax
    import jax.numpy as jnp
    import jaxlib
    from hf_eval import compensated_invariants as arithmetic
    require(Path(arithmetic.__file__).resolve().is_relative_to(probe.source / "src"),
            "arithmetic import escaped declared frozen source", SourceFailure)
    require(arithmetic.COMPILER_OPTIONS == STRICT_OPTIONS,
            "frozen arithmetic compiler options differ", SourceFailure)
    require(jax.config.x64_enabled, "JAX float64 must be enabled by the parent")
    require(jax.default_backend() == "cpu", "CPU backend required")
    probe.summary["runtime"] = dict(python=sys.version, executable=sys.executable,
        numpy=np.__version__, jax=jax.__version__, jaxlib=jaxlib.__version__,
        backend=jax.default_backend(), x64=bool(jax.config.x64_enabled),
        compiler_options=arithmetic.COMPILER_OPTIONS,
        traceback_filtering=jax.config.jax_traceback_filtering,
        arithmetic_source=str(Path(arithmetic.__file__).resolve()),
        arithmetic_sha256=sha(arithmetic.__file__))
    return np, jax, jnp, arithmetic


def controls(probe, np, jax, jnp):
    probe.summary["controls"] = {
        name: {mode: {op: dict(status="not_run") for op in CONTROL_OPERATIONS}
               for mode in ("eager", "jit")} for name in ("none", "joint", "separate")}
    probe.summary["control_contract"] = dict(function="x*x", x=1.25,
        direction=.75, cotangent=-.5, expected_primal=1.5625,
        expected_derivative=2.5, expected_jvp=1.875, expected_pullback=-1.25,
        expected_duality=-.9375, numerical_comparison="exact dyadic binary64 equality")
    x, direction, cotangent = (jnp.asarray(v, dtype=jnp.float64) for v in (1.25, .75, -.5))

    def scalar(value):
        jax.block_until_ready(value)
        return float(np.asarray(value))

    def check(value, expected, label):
        actual = scalar(value)
        require(np.isfinite(actual) and actual == expected,
                f"{label}: actual={actual!r}; expected={expected!r}", NumericalCheckFailure)
        return actual

    def make_control(kind):
        @jax.custom_jvp
        def square(value):
            return value*value

        @square.defjvp
        def square_jvp(primals, tangents):
            (value,), (tangent,) = primals, tangents
            coefficient = 2.*value
            if kind == "joint":
                coefficient, tangent = jax.lax.optimization_barrier((coefficient, tangent))
            elif kind == "separate":
                coefficient = jax.lax.optimization_barrier(coefficient)
                tangent = jax.lax.optimization_barrier(tangent)
            derivative = coefficient*tangent
            if kind != "none":
                derivative = jax.lax.optimization_barrier(derivative)
            return square(value), derivative
        return square

    for kind in ("none", "joint", "separate"):
        square = make_control(kind)
        for mode in ("eager", "jit"):
            function = square if mode == "eager" else jax.jit(square, compiler_options=STRICT_OPTIONS)
            rows = probe.summary["controls"][kind][mode]
            prefix = f"controls.{kind}.{mode}."
            _, primal = probe.step(prefix+"primal", lambda: check(function(x), 1.5625, prefix+"primal"),
                                   destination=rows["primal"], describe=lambda value: value)

            def do_jvp():
                y, action = jax.jvp(function, (x,), (direction,))
                return dict(primal=check(y, 1.5625, prefix+"JVP primal"),
                            tangent=check(action, 1.875, prefix+"JVP tangent"))
            _, action = probe.step(prefix+"jvp", do_jvp, destination=rows["jvp"], describe=lambda value: value)

            def closed_form():
                derivative = action["tangent"]/.75
                require(primal == 1.5625 and derivative == 2.5,
                        "closed-form primal/JVP derivative mismatch", NumericalCheckFailure)
                return dict(primal=primal, derivative=derivative,
                            scope="primal and JVP; pullback checked separately")
            probe.step(prefix+"closed_form", closed_form,
                       destination=rows["closed_form"], describe=lambda value: value)

            def construct_vjp():
                y, pullback = jax.vjp(function, x)
                check(y, 1.5625, prefix+"VJP primal")
                return y, pullback
            success, vjp = probe.step(prefix+"vjp_construct", construct_vjp,
                destination=rows["vjp_construct"], describe=lambda value: dict(primal=scalar(value[0])),
                allow_diagnostic_error=kind != "none")
            if success:
                def pull():
                    (gradient,) = vjp[1](cotangent)
                    return check(gradient, -1.25, prefix+"pullback")
                success, pullback_value = probe.step(prefix+"pullback", pull,
                    destination=rows["pullback"], describe=lambda value: value,
                    allow_diagnostic_error=kind != "none")
                if success:
                    def duality():
                        forward = action["tangent"]*(-.5)
                        reverse = .75*pullback_value
                        require(forward == reverse == -.9375,
                                "closed-form JVP/VJP duality mismatch", NumericalCheckFailure)
                        return dict(cotangent_dot_jvp=forward, direction_dot_pullback=reverse)
                    probe.step(prefix+"duality", duality,
                               destination=rows["duality"], describe=lambda value: value)

            def linear_graph():
                y, linear = jax.linearize(function, x)
                check(y, 1.5625, prefix+"linearize primal")
                graph = jax.make_jaxpr(linear)(direction)
                path = probe.output / f"{kind}_{mode}_linearized.jaxpr.txt"
                write_text(path, str(graph)+"\n")
                return probe.artifact(path)
            probe.step(prefix+"linearized_jaxpr", linear_graph,
                       destination=rows["linearized_jaxpr"], describe=lambda value: value)
    return "diagnostic_observation" if probe.summary["errors"] else "pass"


def read_element(probe, np, jax, jnp):
    path = probe.root / "data" / "inputs.npz"
    probe.summary["input"] = dict(path=str(path), sha256=sha(path), bytes=path.stat().st_size,
                                 case="unit__near_rotation", direction=0)
    with np.load(path, allow_pickle=False) as payload:
        data = {name: payload[name].copy() for name in payload.files}
    cells = np.asarray(data["connectivity"])
    require(cells.shape == (1, 4), "probe requires exactly one saved element", SourceFailure)
    require(np.issubdtype(cells.dtype, np.integer) and np.array_equal(np.sort(cells[0]), np.arange(4)),
            "saved one-element connectivity must be a permutation of its four global nodes", SourceFailure)
    require(data["u_lift"].shape == data["u_fluctuation"].shape == data["direction_0"].shape == (8,),
            "saved split components/direction have wrong shape", SourceFailure)
    # Match TMCModel.edofs exactly: saved displacements/direction are global,
    # whereas the unchanged grad/hessian use the connectivity's local order.
    edofs = (2*cells[:, :, None]+np.arange(2)).reshape(1, 8)
    probe.summary["input"]["indexing"] = dict(connectivity=cells.tolist(), edofs=edofs.tolist(),
        saved_vectors="global node-major x/y DOFs", gathered_vectors="element-local connectivity order",
        mapping="(2*connectivity[...,None]+arange(2)).reshape(1,8)",
        unchanged_operators="grad/hessian/quadrature remain in their saved local order")
    probe.summary["output_indexing"] = dict(residual="element-local DOFs", tangent="element-local row/column DOFs",
        quadrature_fields="saved quadrature/local operator order", direction_0_element="saved global direction_0[edofs]",
        global_assembly_performed=False)
    arguments = (data["u_lift"][edofs], data["u_fluctuation"][edofs],
                 data["grad"], data["hessian"], data["weights"], data["lam"], data["mu"], data["kr"])
    require(all(np.asarray(value).dtype == np.float64 and np.all(np.isfinite(value))
                for value in (*arguments, data["direction_0"])),
            "saved scientific arguments must be finite binary64", SourceFailure)
    args = tuple(jnp.asarray(value, dtype=jnp.float64) for value in arguments)
    direction = jnp.asarray(data["direction_0"][edofs], dtype=jnp.float64)
    jax.block_until_ready((args, direction))
    return args, direction


def staged_call(probe, label, function, args, np, jax):
    _, traced = probe.step(label+".trace", lambda: function.trace(*args))
    _, lowered = probe.step(label+".lower", lambda: traced.lower())
    _, compiled = probe.step(label+".compile", lambda: lowered.compile(compiler_options=STRICT_OPTIONS))

    def execute():
        result = compiled(*args)
        jax.block_until_ready(result)
        return result
    _, result = probe.step(label+".execute_synchronized", execute)

    def transfer():
        return jax.tree.map(lambda value: np.asarray(value), result)
    _, transferred = probe.step(label+".transfer", transfer)

    return transferred, lowered, compiled


def export_ir(probe, label, lowered, compiled):
    def write_ir():
        stable = lowered.as_text(dialect="stablehlo")
        optimized = compiled.as_text()
        require(isinstance(stable, str) and isinstance(optimized, str), "IR text unavailable; no recompile fallback")
        stable_path = probe.output / (label+"_stablehlo.mlir")
        optimized_path = probe.output / (label+"_optimized_hlo.txt")
        write_text(stable_path, stable)
        write_text(optimized_path, optimized)
        return dict(stablehlo=probe.artifact(stable_path), optimized_hlo=probe.artifact(optimized_path))
    probe.step(label+".export_ir", write_ir, describe=lambda value: value)


def element_probe(probe, np, jax, jnp):
    def import_kernel():
        from hf_eval import split_kernel_invariants_hu as kernel
        require(Path(kernel.__file__).resolve().is_relative_to(probe.source / "src"),
                "kernel import escaped frozen source", SourceFailure)
        require(kernel.COMPILER_OPTIONS == STRICT_OPTIONS, "kernel strict options differ", SourceFailure)
        probe.summary["kernel"] = dict(version=kernel.KERNEL_VERSION, path=str(Path(kernel.__file__).resolve()),
                                       sha256=sha(kernel.__file__), compiler_options=kernel.COMPILER_OPTIONS)
        return kernel
    _, kernel = probe.step("kernel_import", import_kernel)
    _, inputs = probe.step("input_transfer", lambda: read_element(probe, np, jax, jnp))
    args, direction = inputs
    function = kernel._batch_without_tangent if probe.mode == "force" else kernel._batch_with_tangent
    result, lowered, compiled = staged_call(probe, probe.mode, function, args, np, jax)

    def save_output():
        require(isinstance(result, dict), "kernel output must be a field mapping")
        path = probe.output / "outputs.npz"
        with path.open("xb") as stream:
            np.savez(stream, **result)
            stream.flush(); os.fsync(stream.fileno())
        artifact = probe.artifact(path)
        require(all(value.dtype == np.float64 and np.all(np.isfinite(value)) for value in result.values()),
                "kernel output contains nonfinite or non-binary64 fields", NumericalCheckFailure)
        require(np.all(result["J"] > 0) and np.all(result["arithmetic_supported"] == 1.),
                "representative state failed physical/arithmetic domain", NumericalCheckFailure)
        return dict(artifact=artifact, fields={name:list(value.shape) for name,value in result.items()},
                    min_J=float(np.min(result["J"])), scientific_admission=False)
    probe.step(probe.mode+".save_output", save_output, describe=lambda value: value)
    export_ir(probe, probe.mode, lowered, compiled)
    if probe.mode == "tangent":
        def action(L, w, grad, hessian, weights, lam, mu, kr, v):
            def actual_residual(varied):
                fields = jax.vmap(kernel._without_tangent,
                    in_axes=(0, 0, None, None, None, 0, 0, None))(
                        L, varied, grad, hessian, weights, lam, mu, kr)
                return fields["residual"]
            return jax.jvp(actual_residual, (w,), (v,))[1]
        jvp_function = jax.jit(action, compiler_options=STRICT_OPTIONS)
        jvp, lowered_jvp, compiled_jvp = staged_call(probe, "residual_jvp", jvp_function, (*args, direction), np, jax)

        def save_jvp():
            path = probe.output / "jvp.npz"
            tangent_action = np.einsum("eij,ej->ei", result["tangent"], np.asarray(direction))
            with path.open("xb") as stream:
                np.savez(stream, residual_jvp=jvp, tangent_action=tangent_action,
                         direction_0_element=np.asarray(direction),
                         edofs=np.asarray(probe.summary["input"]["indexing"]["edofs"], dtype=np.int64))
                stream.flush(); os.fsync(stream.fileno())
            artifact = probe.artifact(path)
            require(jvp.dtype == np.float64 and np.all(np.isfinite(jvp)) and np.all(np.isfinite(tangent_action)),
                    "actual residual JVP or K@v is nonfinite/non-binary64", NumericalCheckFailure)
            return dict(artifact=artifact,
                        scope="raw actual residual JVP and K@v; no HP or new accuracy gate")
        probe.step("residual_jvp.save_output", save_jvp, describe=lambda value: value)
        export_ir(probe, "residual_jvp", lowered_jvp, compiled_jvp)
    require(sha(probe.root/"data/inputs.npz") == probe.summary["input"]["sha256"],
            "input bytes changed during probe", SourceFailure)
    return "pass"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--mode", choices=("controls", "force", "tangent"), required=True)
    args = parser.parse_args()
    with EventLog() as log:
        log.emit("probe_started", mode=args.mode, outcome="running", scientific_imports_started=False)
        probe = Probe(args.root.resolve(), args.source.resolve(), args.mode, log)
        try:
            _, loaded = probe.step("runtime_import_and_prepare", lambda: runtime(probe))
            np, jax, jnp, _ = loaded
            status = controls(probe, np, jax, jnp) if args.mode == "controls" else element_probe(probe, np, jax, jnp)
        except EventLogError:
            raise
        except Exception as error:
            detail = dict(type=type(error).__name__, message=str(error), traceback=traceback.format_exc(), stage="probe")
            probe.summary["errors"].append(detail)
            log.emit("probe_failed", stage="probe", outcome="error", exception_type=detail["type"],
                     traceback=detail["traceback"], message=detail["message"])
            status = "failed"
        probe.finish(status)
        # Captured predeclared diagnostic exceptions are not a numeric pass;
        # only the parent's separate evidence classification may permit repair.
        return 0 if status in ("pass", "diagnostic_observation") else 1


if __name__ == "__main__":
    raise SystemExit(main())
