"""JIT/AD-1: raw AD under the outer strict compilation boundary.

Only standard-library helpers are imported before the durable first event.
The parent alone owns the approved serial deadline and process-tree budget.
This probe never repairs a source, creates H1, or opens another execution window.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import time

import probe_s0_preparation as shared
from s0_ad_exception import exception_details, is_declared_transpose
from s0_event_log import EventLog, EventLogError


SCHEMA = "hf-jit-ad-preparation-probe-1"
KINDS = ("none", "joint", "separate")
EAGER_STEPS = ("primal", "jvp", "vjp_construct", "pullback", "closed_form", "duality")
STRICT_STAGES = ("trace", "lower", "compile", "execute_synchronized", "transfer", "check")
DIAGNOSTIC_STAGES = frozenset((
    "controls.joint.eager.vjp_construct",
    "controls.joint.eager.pullback",
    "controls.joint.strict.reverse.trace",
))
H1_MANIFEST = "H1/manifest.json"
H1_TEST = "H1/tests/test_compensated_invariants.py"


class JitAdProbe(shared.Probe):
    """Reuse persistence; narrow every observation to an actual bound AD frame."""

    def __init__(self, root, source, mode, log):
        super().__init__(root, source, mode, log)
        self.summary.update(schema=SCHEMA, protocol="JIT/AD-1",
                            source_version=os.environ.get("HF_S0_VERSION"))
        self.checkpoint()

    def step(self, stage, function, *, destination=None, describe=None,
             allow_diagnostic_error=False):
        row = dict(stage=stage, status="running", started_utc=shared.utc())
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
                          finished_utc=shared.utc())
            if describe is not None:
                record["value"] = describe(value)
        except EventLogError:
            raise
        except Exception as error:
            detail = exception_details(error)
            detail["stage"] = stage
            observed = (allow_diagnostic_error and stage in DIAGNOSTIC_STAGES
                        and is_declared_transpose(detail))
            record = dict(status="failed", elapsed_seconds=time.monotonic()-begin,
                          finished_utc=shared.utc(), error=detail,
                          declared_transpose_observation=bool(observed))
            row.update(record)
            if destination is not None:
                destination.update(record)
            self.summary["errors"].append(detail)
            self.checkpoint()
            self.log.emit("stage_failed", stage=stage, outcome="error",
                          exception_type=detail["type"], exception=detail,
                          traceback=detail["traceback"],
                          declared_transpose_observation=bool(observed),
                          duration=record["elapsed_seconds"])
            if observed:
                return False, None
            raise
        row.update(record)
        if destination is not None:
            destination.update(record)
        self.checkpoint()
        self.log.emit("stage_finished", stage=stage, outcome="pass",
                      duration=record["elapsed_seconds"])
        return True, value


def bind_harness(probe):
    """Read existing frozen H1 identity; no test import or source generation."""
    root, source = probe.root, probe.source
    version = probe.summary["source_version"]
    shared.require(version in ("B0", "C1"), "unknown scientific source version", shared.SourceFailure)
    shared.require(source == (root/version/"source/hf_repo").resolve(),
                   "scientific source path does not match declared version", shared.SourceFailure)
    if probe.mode == "controls":
        shared.require(version == "B0", "A2 controls require the immutable B0 source", shared.SourceFailure)
    manifest_path, test_path = root/H1_MANIFEST, root/H1_TEST
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    shared.require(manifest["version"] == "H1" and manifest["test_path"] == H1_TEST,
                   "H1 manifest identity or test path differs", shared.SourceFailure)
    shared.require(test_path.is_file() and shared.sha(test_path) == manifest["test_sha256"],
                   "H1 test bytes differ from its manifest", shared.SourceFailure)
    shared.require(Path(shared.__file__).resolve() == Path(__file__).with_name("probe_s0_preparation.py").resolve(),
                   "shared probe helper escaped the frozen auxiliary directory", shared.SourceFailure)
    harness = dict(version="H1", manifest_path=str(manifest_path),
                   manifest_sha256=shared.sha(manifest_path), test_path=str(test_path),
                   test_sha256=manifest["test_sha256"])
    probe.summary["harness"] = harness
    probe.summary["auxiliary"] = dict(path=str(Path(__file__).resolve()),
        sha256=shared.sha(__file__), reused_helper_path=str(Path(shared.__file__).resolve()),
        reused_helper_sha256=shared.sha(shared.__file__))
    return harness


def recheck_harness(probe):
    harness = probe.summary["harness"]
    shared.require(shared.sha(harness["manifest_path"]) == harness["manifest_sha256"]
                   and shared.sha(harness["test_path"]) == harness["test_sha256"],
                   "H1 identity changed during the probe", shared.SourceFailure)
    return dict(status="pass", **harness)


def load_runtime(probe):
    # Explicitly disable the persistent compilation cache before importing JAX.
    # In-memory caches are fresh in each supervised child process.
    os.environ["JAX_ENABLE_COMPILATION_CACHE"] = "false"
    loaded = shared.runtime(probe)
    _, jax, _, _ = loaded
    shared.require(not jax.config.jax_enable_compilation_cache,
                   "persistent compilation cache must remain disabled", shared.SourceFailure)
    probe.summary["runtime"]["persistent_compilation_cache"] = False
    return loaded


def fresh_rows(names):
    return {name: dict(status="not_run") for name in names}


def strict_control(probe, label, raw_function, arguments, rows, check, np, jax,
                   *, allow_transpose=False):
    """One trace, its lower, its compile and one full synchronous execution."""
    function = jax.jit(raw_function, compiler_options=shared.STRICT_OPTIONS)
    success, traced = probe.step(label+".trace", lambda: function.trace(*arguments),
        destination=rows["trace"], allow_diagnostic_error=allow_transpose)
    if not success:
        # Only joint reverse.trace is allowed to reach this return. All
        # dependent stages stay not_run, while its independent raw graph runs.
        return False, None
    _, lowered = probe.step(label+".lower", lambda: traced.lower(), destination=rows["lower"])
    _, compiled = probe.step(label+".compile",
        lambda: lowered.compile(compiler_options=shared.STRICT_OPTIONS), destination=rows["compile"])

    def execute():
        result = compiled(*arguments)
        jax.block_until_ready(result)
        return result
    _, result = probe.step(label+".execute_synchronized", execute,
                           destination=rows["execute_synchronized"])
    _, transferred = probe.step(label+".transfer", lambda: jax.tree.map(np.asarray, result),
                               destination=rows["transfer"])
    _, checked = probe.step(label+".check", lambda: check(transferred),
                           destination=rows["check"], describe=lambda value: value)
    return True, checked


def controls(probe, np, jax, jnp):
    probe.summary["controls"] = {
        kind: dict(eager=fresh_rows(EAGER_STEPS),
                   strict={**{name: fresh_rows(STRICT_STAGES) for name in ("primal", "forward", "reverse")},
                           **fresh_rows(("closed_form", "duality"))},
                   linearized_jaxpr=dict(status="not_run")) for kind in KINDS}
    probe.summary["control_contract"] = dict(function="x*x", x=1.25, direction=.75,
        cotangent=-.5, expected_primal=1.5625, expected_derivative=2.5,
        expected_jvp=1.875, expected_pullback=-1.25, expected_duality=-.9375,
        numerical_comparison="exact dyadic binary64 equality", order=list(KINDS),
        strict_boundary="raw primal or full raw AD+array pullback result under outermost strict JIT",
        raw_linearized_graphs_per_kind=1, eager_vjp_construct_and_pullback_separate=True)
    probe.checkpoint()
    x, direction, cotangent = (jnp.asarray(value, dtype=jnp.float64) for value in (1.25, .75, -.5))

    def check_scalar(value, expected, label):
        jax.block_until_ready(value)
        array = np.asarray(value)
        shared.require(array.dtype == np.dtype("float64") and array.shape == (),
                       label+": result is not scalar binary64", shared.NumericalCheckFailure)
        actual = float(array)
        shared.require(np.isfinite(actual) and actual == expected,
                       f"{label}: actual={actual!r}, expected={expected!r}", shared.NumericalCheckFailure)
        return actual

    def check_forward(value, label):
        y, tangent = value
        return dict(primal=check_scalar(y, 1.5625, label+" primal"),
                    tangent=check_scalar(tangent, 1.875, label+" JVP"))

    def check_reverse(value, label):
        y, pullback = value
        return dict(primal=check_scalar(y, 1.5625, label+" primal"),
                    pullback=check_scalar(pullback, -1.25, label+" pullback"))

    def closed_form(primal, forward):
        derivative = forward["tangent"]/.75
        shared.require(primal == forward["primal"] == 1.5625 and derivative == 2.5,
                       "closed-form primal/JVP derivative mismatch", shared.NumericalCheckFailure)
        return dict(primal=primal, derivative=derivative,
                    scope="primal and JVP; VJP numeric value checked independently")

    def duality(forward, reverse):
        left, right = -.5*forward["tangent"], .75*reverse
        shared.require(left == right == -.9375, "closed-form JVP/VJP duality mismatch",
                       shared.NumericalCheckFailure)
        return dict(cotangent_dot_jvp=left, direction_dot_pullback=right)

    def make_control(kind):
        @jax.custom_jvp
        def raw(value):
            return value*value

        @raw.defjvp
        def raw_jvp(primals, tangents):
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
            return raw(value), derivative
        return raw

    for kind in KINDS:
        raw = make_control(kind)
        rows = probe.summary["controls"][kind]
        eager = rows["eager"]
        prefix = "controls."+kind+".eager."
        _, eager_primal = probe.step(prefix+"primal", lambda: check_scalar(raw(x), 1.5625, prefix+"primal"),
                                    destination=eager["primal"], describe=lambda value: value)
        _, eager_forward = probe.step(prefix+"jvp",
            lambda: check_forward(jax.jvp(raw, (x,), (direction,)), prefix+"jvp"),
            destination=eager["jvp"], describe=lambda value: value)
        probe.step(prefix+"closed_form", lambda: closed_form(eager_primal, eager_forward),
                   destination=eager["closed_form"], describe=lambda value: value)

        def construct_vjp():
            y, pullback = jax.vjp(raw, x)
            return check_scalar(y, 1.5625, prefix+"VJP primal"), pullback
        success, vjp = probe.step(prefix+"vjp_construct", construct_vjp,
            destination=eager["vjp_construct"], describe=lambda value: dict(primal=value[0]),
            allow_diagnostic_error=kind == "joint")
        if success:
            def pullback_action():
                (gradient,) = vjp[1](cotangent)
                return check_scalar(gradient, -1.25, prefix+"pullback")
            success, eager_reverse = probe.step(prefix+"pullback", pullback_action,
                destination=eager["pullback"], describe=lambda value: value,
                allow_diagnostic_error=kind == "joint")
            if success:
                probe.step(prefix+"duality", lambda: duality(eager_forward, eager_reverse),
                           destination=eager["duality"], describe=lambda value: value)

        strict = rows["strict"]
        prefix = "controls."+kind+".strict."
        _, strict_primal = strict_control(probe, prefix+"primal", raw, (x,), strict["primal"],
            lambda value: check_scalar(value, 1.5625, prefix+"primal"), np, jax)

        def forward_action(z, v):
            return jax.jvp(raw, (z,), (v,))
        _, strict_forward = strict_control(probe, prefix+"forward", forward_action, (x, direction),
            strict["forward"], lambda value: check_forward(value, prefix+"forward"), np, jax)
        probe.step(prefix+"closed_form", lambda: closed_form(strict_primal, strict_forward),
                   destination=strict["closed_form"], describe=lambda value: value)

        def reverse_action(z, c):
            y, pullback = jax.vjp(raw, z)
            return y, pullback(c)[0]
        success, strict_reverse = strict_control(probe, prefix+"reverse", reverse_action, (x, cotangent),
            strict["reverse"], lambda value: check_reverse(value, prefix+"reverse"), np, jax,
            allow_transpose=kind == "joint")
        if success:
            probe.step(prefix+"duality", lambda: duality(strict_forward, strict_reverse["pullback"]),
                       destination=strict["duality"], describe=lambda value: value)

        # Independent of VJP success: precisely one raw linear graph per kind.
        # Neither raw nor its returned linear callable carries strict-JIT options.
        def linear_graph():
            y, linear = jax.linearize(raw, x)
            check_scalar(y, 1.5625, kind+" raw linearization primal")
            graph = jax.make_jaxpr(linear)(direction)
            output = probe.output/(kind+"_raw_linearized.jaxpr.txt")
            shared.write_text(output, str(graph)+"\n")
            return probe.artifact(output)
        probe.step("controls."+kind+".linearized_jaxpr", linear_graph,
                   destination=rows["linearized_jaxpr"], describe=lambda value: value)

    return "diagnostic_observation" if probe.summary["errors"] else "pass"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--mode", choices=("controls", "force", "tangent"), required=True)
    args = parser.parse_args()
    with EventLog() as log:
        log.emit("probe_started", protocol="JIT/AD-1", mode=args.mode,
                 outcome="running", scientific_imports_started=False)
        probe = JitAdProbe(args.root.resolve(), args.source.resolve(), args.mode, log)
        try:
            probe.step("harness_binding", lambda: bind_harness(probe), describe=lambda value: value)
            _, loaded = probe.step("runtime_import_and_prepare", lambda: load_runtime(probe))
            np, jax, jnp, _ = loaded
            status = controls(probe, np, jax, jnp) if args.mode == "controls" else shared.element_probe(probe, np, jax, jnp)
            probe.step("harness_preservation", lambda: recheck_harness(probe), describe=lambda value: value)
        except EventLogError:
            raise
        except Exception as error:
            detail = exception_details(error)
            detail["stage"] = "probe"
            probe.summary["errors"].append(detail)
            log.emit("probe_failed", stage="probe", outcome="error", exception=detail,
                     exception_type=detail["type"], traceback=detail["traceback"])
            status = "failed"
        probe.finish(status)
        # Only the separate frozen classifier may authorize C1. An observed
        # joint transpose exception remains a failed step, never a test pass.
        return 0 if status in ("pass", "diagnostic_observation") else 1


if __name__ == "__main__":
    raise SystemExit(main())
