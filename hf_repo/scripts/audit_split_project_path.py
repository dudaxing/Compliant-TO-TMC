"""Fresh HP80/120 audit of one saved canonical split average-port prefix.

The original 1 mm task and the executed [0, .001, .025] mm prefix are separate
identities. This script never solves, repairs states or substitutes old HP data.
Every candidate action and reference needed to replay the gates is persisted.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, localcontext
import gzip
import json
from pathlib import Path
from time import perf_counter

import numpy as np
import psutil
from scipy import sparse

from run_split_average_demo import (GATES, model_from, npz, plain, read,
                                    snapshot, source_paths, write)
from audit_numpy_c1_path import (D, HP_HASHES, HP_KEYS, NAMES, candidate,
                                 norm, sha, state_hash)
from hf4_split_precision_reference import DecimalSplitQ1Reference

PREFIX = [0., .001, .025]
RSS_LIMIT = 8 * 1024**3
CANONICAL_HASHES = {
    "geometry.json": "dd5e28cd1dff05a96b1599be9084ae3809ae8c96c79f45432e05bb5b1fb00b7f",
    "geometry.npz": "1911362efaa5b6c5104af0cecf95310f262b129f3e0cd2a1c648cf550b756132",
    "task.json": "93a80ed3c7b717773684a3c255dabe76a622835a25560ea2e6ed361f31c2cb36",
    "validation_spec.json": "44eb35fef2e6988bf66c3935b76559531e40f0f567bd5438fe7db2afb7bd583e",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def exact_means(state, values, row):
    """Promote both components and coefficient products before any rounding."""
    with localcontext() as context:
        context.prec = 3000
        displacement = [D(a) + D(b) for a, b in
                        zip(state["u_lift"], state["u_fluctuation"])]
        b_in, b_out = (list(map(D, values[key])) for key in ("b_in", "b_out"))
        q_in, q_out = (sum((b*u for b, u in zip(vector, displacement)), Decimal(0))
                       for vector in (b_in, b_out))
        target = D(row["target_origin"]) + D(row["d"])
        return displacement, b_in, b_out, q_in, q_out, target, q_in-target


def measurements(hp, state, values, row):
    """Independent task equation using saved Et, ports, multiplier and state."""
    displacement, b_in, b_out, q_in, q_out, target, constraint = exact_means(state, values, row)
    with localcontext() as context:
        context.prec = 120
        internal = hp["internal_decimal"]
        stiffness = D(values["k_out"])
        actuator = [b*D(row["R_input"]) for b in b_in]
        spring = [stiffness*b*q_out for b in b_out]
        residual = [fi+fs-fe for fi, fs, fe in zip(internal, spring, actuator)]
        fixed = set(map(int, values["fixed_dofs"]))
        free = [i for i in range(len(displacement)) if i not in fixed]
        dscale = max(abs(target), Decimal("1e-6"))
        floor = Decimal("1e-8")*D(values["force_scale_per_length"])*dscale
        scale = max(*[norm([part[i] for i in free]) for part in (internal, actuator, spring)], floor)
        support = [residual[i] if i in fixed else Decimal(0) for i in range(len(displacement))]
        balance = [sum((support[i]+actuator[i]-spring[i]
                        for i in range(c, len(displacement), 2)), Decimal(0)) for c in (0, 1)]
        balance_scale = max(norm(support)+norm(actuator)+norm(spring), scale)
        direction = list(map(D, values["tangent_direction"]))
        dq_out = sum((b*v for b, v in zip(b_out, direction)), Decimal(0))
        dg = sum((b*v for b, v in zip(b_in, direction)), Decimal(0))
        dR = D(values["tangent_multiplier_direction"])
        augmented = [a+stiffness*b*dq_out-bi*dR
                     for a, b, bi in zip(hp["tangent_action_decimal"], b_out, b_in)]
        return dict(q_in=q_in, q_out=q_out, physical_mean_target_mm=target,
                    constraint_residual=constraint, force_scale=scale, force_scale_floor=floor,
                    displacement_scale=dscale, relative_residual=norm([residual[i] for i in free])/scale,
                    relative_constraint=abs(constraint)/dscale,
                    relative_force_balance=norm(balance)/balance_scale,
                    fixed_error_mm=max((abs(displacement[i]) for i in fixed), default=Decimal(0)),
                    min_J=min(x for items in hp["J_decimal"] for x in items),
                    support=support, actuator=actuator, spring_force=[-x for x in spring],
                    force_residual=residual, balance=balance, balance_scale=balance_scale,
                    augmented_force=augmented, augmented_constraint=dg, free=free)


def saved_equation(state, values, row):
    """Reconstruct production stopping from saved force arrays, independently."""
    displacement, _, _, _, _, target, constraint = exact_means(state, values, row)
    with localcontext() as context:
        context.prec = 120
        internal, actuator, spring_on_model = (list(map(D, state[key])) for key in
                       ("internal_force", "input_force", "spring_force_on_structure"))
        support = list(map(D, state["support_reaction"]))
        residual = [fi-fe-fs for fi, fe, fs in zip(internal, actuator, spring_on_model)]
        fixed = set(map(int, values["fixed_dofs"]))
        free = [i for i in range(len(displacement)) if i not in fixed]
        dscale = max(abs(target), Decimal("1e-6"))
        scale = max(*[norm([part[i] for i in free]) for part in
                     (internal, actuator, spring_on_model)],
                    Decimal("1e-8")*D(values["force_scale_per_length"])*dscale)
        balance = [sum((support[i]+actuator[i]+spring_on_model[i]
                        for i in range(c, len(displacement), 2)), Decimal(0)) for c in (0, 1)]
        balance_scale = max(norm(support)+norm(actuator)+norm(spring_on_model), scale)
        return dict(relative_residual=norm([residual[i] for i in free])/scale,
                    residual_scale=scale, relative_constraint=abs(constraint)/dscale,
                    relative_force_balance=norm(balance)/balance_scale,
                    force_residual=residual, balance=balance, balance_scale=balance_scale)


def sources():
    scripts = Path(__file__).parent
    paths = [Path(__file__), *source_paths(include_controller=True),
             scripts/"run_split_project_path.py"]
    source = scripts.parent/"src/hf_eval"
    paths.extend(source/name for name in ("project.py", "regions.py", "data.py"))
    return list(dict.fromkeys(paths))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--time-limit", type=float, default=300.)
    args = parser.parse_args()
    require(np.isfinite(args.time_limit) and 0 < args.time_limit <= 300.,
            "Time limit must be positive and at most the approved 300 seconds")
    args.output.mkdir(parents=True, exist_ok=False)
    for name in ("references", "matrices", "candidate_vectors"):
        (args.output/name).mkdir()
    started, process = perf_counter(), psutil.Process()
    rows, inputs, source_records = [], {}, []
    bindings = []
    hp_attempted = hp_completed = 0

    def checkpoint():
        if perf_counter()-started > args.time_limit:
            raise RuntimeError("Independent canonical audit time limit exceeded")
        if process.memory_info().rss > RSS_LIMIT:
            raise RuntimeError("Independent canonical audit sampled RSS exceeds 8 GiB")

    def bind(path, expected=None):
        digest = sha(path)
        require(expected is None or digest == expected, "Input hash mismatch: "+str(path))
        inputs[path] = digest

    def check(checks, name, value, gate):
        value, limit = Decimal(value), Decimal(gate)
        checks.append(dict(name=name, value=str(value), limit=str(limit),
                           pass_gate=value.is_finite() and value <= limit))

    def file_record(path):
        return dict(path=path.relative_to(args.output).as_posix(), sha256=sha(path))

    write(args.output/"lifecycle.json", dict(status="running", continuous_seconds=args.time_limit,
          sampled_RSS_limit_bytes=RSS_LIMIT, stop_policy="First error or failed gate stops; no solve or repair"))
    try:
        checkpoint()
        for name in ("protocol.json", "model.npz", "summary.json"):
            bind(args.input/name)
        protocol, summary = (read(args.input/name) for name in ("protocol.json", "summary.json"))
        require(protocol["schema_version"] == "split-project-prefix-1.0", "Wrong prefix schema")
        require(protocol["case_family"] == "inverter" and protocol["targets_mm"] == PREFIX,
                "Only the declared canonical inverter prefix is in scope")
        require(protocol["parent_task_target_mm"] == 1. and protocol["force_scale_per_length"] == 20.
                and protocol["k_out_N_per_mm"] == 0. and protocol["gates"] == GATES,
                "Parent target, Et, spring or original gates changed")
        require(summary["status"] == "success" and summary["target_reached"], "Production prefix did not finish")
        require(summary["k_out_N_per_mm"] == 0., "Production spring changed")
        require(summary["protocol_sha256"] == inputs[args.input/"protocol.json"]
                and summary["model_sha256"] == inputs[args.input/"model.npz"], "Production identity changed")
        states = summary["states"]
        require(states and [row["d"] for row in states if row["is_original_target"]] == PREFIX,
                "Saved states do not cover exactly the three declared original targets")
        require(states[0]["d"] == 0. and states[-1]["d"] == PREFIX[-1]
                and all(a["d"] < b["d"] for a, b in zip(states, states[1:])),
                "Saved path is not a complete ordered prefix")
        require(all(row["target_origin"] == 0. and row["physical_mean_target_mm"] == row["d"]
                    for row in states), "This canonical prefix has no warm target offset")
        values = npz(args.input/"model.npz")
        require(inputs[args.input/"model.npz"] == protocol["model_sha256"], "Model identity changed")
        require(float(values["force_scale_per_length"]) == 20. and float(values["k_out"]) == 0.
                and float(values["thickness"]) == 20. and float(values["hx"]) == float(values["hy"]) == 1.,
                "Persisted model is outside the original task")
        model = model_from(values)
        require(model.ne == 3200 and model.ndof == 6642, "Canonical original grid changed")
        require(np.all(values["tangent_direction"][model.fixed_dofs] == 0.), "Tangent must not change fixed DOFs")
        for name, direction in (("input", [1., 0.]), ("output", [-1., 0.])):
            port = protocol["region_metadata"]["ports"][name]
            require(port["direction"] == direction and port["weights"] == [.25, .5, .25],
                    "Canonical port meaning changed")
            vector = np.zeros(model.ndof)
            for node, weight in zip(port["nodes"], port["weights"]):
                vector[2*node:2*node+2] = weight*np.asarray(direction)
            np.testing.assert_array_equal(vector, values["b_in" if name == "input" else "b_out"])
        for name, expected in CANONICAL_HASHES.items():
            bind(args.input/"inputs"/name, expected)
        require(protocol["validation_spec_sha256"] == CANONICAL_HASHES["validation_spec.json"],
                "Frozen HF3 specification identity changed")
        specification = read(args.input/"inputs/validation_spec.json")
        for field, original in (("tolerance", "internal_relative_force_tolerance"),
                                ("constraint_tolerance", "constraint_relative_tolerance"),
                                ("displacement_scale_floor", "displacement_scale_floor_mm"),
                                ("force_scale_floor_factor", "force_scale_floor_factor"),
                                ("max_checks", "max_checks"), ("max_backtracks", "max_backtracks"),
                                ("max_bisections", "max_bisections"), ("armijo_c", "armijo_c")):
            require(protocol["settings"][field] == specification[original], "Original HF3 setting changed: "+field)
        require(protocol["minimum_increment_rule"] == specification["minimum_increment_rule"]
                == "initial target increment / 16" and protocol["settings"]["minimum_increment"] == .001/16,
                "Original minimum-increment rule changed")
        task = read(args.input/"inputs/task.json")
        require(task["input"]["target_mm"] == 1. and task["material"]["E_MPa"] == 1.
                and task["output"]["spring_N_per_mm"] == 0. and task["workpiece"] is None,
                "The original parent task must remain the 1 mm free-output task without a workpiece")
        # Pure geometry/task reconstruction verifies the saved constitutive and
        # boundary primitives; this invokes no force, tangent or equilibrium.
        from hf_eval.project import build_project
        project = build_project(args.input/"inputs/geometry.json", task)
        for name in ("coordinates", "connectivity", "lam", "mu", "kr", "hx", "hy",
                     "thickness", "solid", "fixed_dofs"):
            np.testing.assert_array_equal(values[name], getattr(project.model, name))
        for name in ("grad", "hessian", "weights"):
            np.testing.assert_array_equal(values[name], project.model.ops[name])
        for name, expected in (("b_in", project.bin), ("b_out", project.bout)):
            np.testing.assert_array_equal(values[name], expected)
        require(project.geometry.geometry_id == protocol["geometry_id"]
                and project.task_hash == protocol["task_sha256"], "Original geometry/task identity changed")
        expected_shape = np.zeros(model.ndof)
        expected_shape[np.flatnonzero(project.bin)] = 1.
        np.testing.assert_array_equal(values["lift_shape"], expected_shape)
        for source in protocol["sources"]:
            bind(args.input/"sources"/source["name"], source["sha256"])
        driver_record = next(s for s in protocol["sources"] if s["name"] == "run_split_project_path.py")
        require(sha(Path(__file__).with_name("run_split_project_path.py")) == driver_record["sha256"],
                "Driver differs from the production snapshot")
        for name, expected in HP_HASHES.items():
            require(sha(Path(__file__).with_name(name)) == expected, "Independent reference changed: "+name)
        source_records = snapshot(args.output, sources())
        checkpoint()
        from hf_eval import split_kernel_invariants_hu as force_kernel
        def forbidden(*unused, **unused_kwargs):
            raise RuntimeError("Compiled execution is outside this NumPy audit")
        force_kernel._runtime = force_kernel._batch_with_tangent = force_kernel._batch_without_tangent = forbidden
        for index, row in enumerate(states):
            checkpoint()
            state_path = args.input/row["path"]
            bind(state_path, row["file_sha256"])
            state = npz(state_path)
            require(state_hash(state) == row["state_sha256"], "Saved two-array state identity changed")
            expected_lift = np.zeros(model.ndof) if row["d"] == 0. else row["d"]*values["lift_shape"]
            np.testing.assert_array_equal(state["u_lift"].view(np.uint64), expected_lift.view(np.uint64))
            require(np.all(state["u_lift"][model.fixed_dofs] == 0.)
                    and np.all(state["u_fluctuation"][model.fixed_dofs] == 0.), "Fixed split components changed")
            actual = candidate(model, state, values["tangent_direction"])
            checkpoint()
            for name, key in zip(NAMES[:3], ("internal_force", "material_internal_force", "regularization_internal_force")):
                np.testing.assert_array_equal(actual[name].view(np.uint64), state[key].view(np.uint64))
            np.testing.assert_array_equal(actual["J"], state["J"])
            total_path = args.output/"matrices"/f"state_{index:03d}__total.npz"
            sparse.save_npz(total_path, actual["total_matrix"])
            b_in, b_out = values["b_in"], values["b_out"]
            output_column = sparse.csc_matrix(b_out[:, None])
            spring_matrix = float(values["k_out"])*(output_column@output_column.T)
            free_matrix = (actual["total_matrix"]+spring_matrix)[model.free][:, model.free]
            column = sparse.csc_matrix(b_in[model.free, None])
            augmented_matrix = sparse.bmat([[free_matrix, -column], [column.T, None]], format="csc")
            augmented_path = args.output/"matrices"/f"state_{index:03d}__augmented.npz"
            sparse.save_npz(augmented_path, augmented_matrix)
            augmented = augmented_matrix@np.r_[values["tangent_direction"][model.free],
                                                float(values["tangent_multiplier_direction"])]
            vector_path = args.output/"candidate_vectors"/f"state_{index:03d}.npz"
            np.savez_compressed(vector_path, **{name: actual[name] for name in NAMES},
                                augmented_force_action=augmented[:-1], augmented_constraint_action=np.array(augmented[-1]),
                                tangent_direction=values["tangent_direction"],
                                tangent_multiplier_direction=values["tangent_multiplier_direction"])
            checkpoint()
            hp, measured, references = {}, {}, []
            for precision in (80, 120):
                checkpoint()
                hp_attempted += 1
                hp[precision] = DecimalSplitQ1Reference(values, precision=precision).evaluate(
                    state["u_lift"], state["u_fluctuation"], tangent_direction=values["tangent_direction"])
                hp_completed += 1
                checkpoint()
                measured[precision] = measurements(hp[precision], state, values, row)
                reference_path = args.output/"references"/f"state_{index:03d}__hp{precision}.json.gz"
                with gzip.open(reference_path, "wt", encoding="utf-8") as stream:
                    json.dump(plain(dict(mechanics=hp[precision], task=measured[precision])), stream, allow_nan=False)
                references.append(file_record(reference_path))
                checkpoint()
            checks = []
            with localcontext() as context:
                context.prec = 120
                sf = measured[80]["force_scale"]
                for name, key in zip(NAMES, HP_KEYS):
                    target = hp[80][key]
                    denominator = sf if name == "total_force" else max(norm(target),
                                      Decimal("1e-12")*sf if "force" in name else Decimal("1e-10"))
                    check(checks, name, norm([D(a)-b for a, b in zip(actual[name], target)])/denominator, GATES[name])
                    check(checks, name+"__hp80_hp120", norm([a-b for a, b in zip(hp[80][key], hp[120][key])])/denominator,
                          GATES["hp80_hp120"])
                check(checks, "force_evaluation", norm([D(a)-b for a, b in zip(state["internal_force"], hp[80]["internal_decimal"])])/sf,
                      GATES["force_evaluation"])
                for stored, target in (("input_force", "actuator"), ("spring_force_on_structure", "spring_force"),
                                       ("support_reaction", "support")):
                    check(checks, "saved_"+stored, norm([D(a)-b for a, b in zip(state[stored], measured[80][target])])/sf,
                          GATES["force_evaluation"])
                for name in ("q_in", "q_out"):
                    check(checks, "reported_"+name, abs(D(row[name])-measured[80][name])/measured[80]["displacement_scale"],
                          GATES["average_constraint"])
                for precision in (80, 120):
                    for key, gate in (("relative_residual", "independent_residual"), ("relative_constraint", "average_constraint"),
                                      ("relative_force_balance", "global_force_balance"), ("fixed_error_mm", "fixed_displacement_mm")):
                        check(checks, f"hp{precision}__{key}", measured[precision][key], GATES[gate])
                    checks.append(dict(name=f"hp{precision}__positive_J", value=str(measured[precision]["min_J"]),
                                       pass_gate=measured[precision]["min_J"].is_finite() and measured[precision]["min_J"] > 0))
                saved = saved_equation(state, values, row)
                for key, gate in (("relative_residual", "production_residual"), ("relative_constraint", "average_constraint"),
                                  ("relative_force_balance", "global_force_balance")):
                    check(checks, "saved_equation__"+key, saved[key], GATES[gate])
                check(checks, "reported_production_residual", str(row["relative_residual"]), GATES["production_residual"])
                check(checks, "reported_residual_difference", abs(D(row["relative_residual"])-saved["relative_residual"]),
                      GATES["force_evaluation"])
                checks.append(dict(name="support_zero_on_free_dofs", pass_gate=bool(np.all(state["support_reaction"][model.free] == 0.))))
                reference_action = [measured[80]["augmented_force"][i] for i in model.free]
                denominator = max(norm(reference_action), Decimal("1e-10"))
                check(checks, "augmented_force_tangent", norm([D(a)-b for a, b in zip(augmented[:-1], reference_action)])/denominator,
                      GATES["augmented_force_tangent"])
                check(checks, "augmented_constraint_tangent", abs(D(augmented[-1])-measured[80]["augmented_constraint"])/
                      max(abs(measured[80]["augmented_constraint"]), Decimal("1e-6")), GATES["augmented_constraint_tangent"])
                check(checks, "augmented_force_tangent__hp80_hp120", norm([measured[80]["augmented_force"][i]-
                      measured[120]["augmented_force"][i] for i in model.free])/denominator, GATES["hp80_hp120"])
            record = dict(index=index, state_sha256=row["state_sha256"], d_mm=row["d"],
                          status="pass" if all(c["pass_gate"] for c in checks) else "not_pass", checks=checks,
                          metrics=measured[80], saved_equation_metrics=saved, references=references,
                          matrices=[file_record(path) for path in (total_path, augmented_path)],
                          candidate_vectors=file_record(vector_path))
            rows.append(plain(record))
            write(args.output/"summary.json", dict(status="running", states=rows, sources=source_records))
            checkpoint()
            print(f"Canonical HP audit state {index} d={row['d']:.9g}: {record['status']}", flush=True)
            if record["status"] != "pass":
                raise RuntimeError("First saved-state audit gate failure")
        require(len(rows) == len(states), "Not every new accepted state was independently audited")
        for path, expected in inputs.items():
            require(sha(path) == expected, "Bound input changed during audit")
        for path, record in zip(sources(), source_records):
            require(sha(path) == record["sha256"] == sha(args.output/"sources"/record["name"]),
                    "Source changed during audit")
        bindings = [dict(path=path.relative_to(args.input).as_posix(), sha256=digest)
                    for path, digest in inputs.items()]
        checkpoint()
        status, failure = "pass", None
    except (OSError, ValueError, RuntimeError, ArithmeticError, AssertionError, KeyError, StopIteration) as error:
        status, failure = "not_pass", type(error).__name__+": "+str(error)
    memory = process.memory_info()
    if not bindings:
        bindings = [dict(path=path.relative_to(args.input).as_posix(), sha256=digest)
                    for path, digest in inputs.items()]
    write(args.output/"summary.json", dict(schema_version="split-project-prefix-audit-1.0", status=status, states=rows,
          checks_completed=sum(len(row["checks"]) for row in rows), new_state_independent_HP_audited=status == "pass",
          fresh_HP_evaluations=hp_completed, fresh_HP_evaluations_attempted=hp_attempted,
          process_peak_working_set_bytes=getattr(memory, "peak_wset", memory.rss), gates=GATES,
          elapsed_seconds=perf_counter()-started, time_limit_seconds=args.time_limit,
          input_bindings=bindings,
          sources=source_records, failure=failure, parent_task_target_mm=1., audited_prefix_targets_mm=PREFIX,
          scope="Canonical native 80x40 inverter prefix only; parent 1 mm path, contact, workpiece and LF batches unqualified"))
    write(args.output/"lifecycle.json", dict(status="finished" if status == "pass" else "stopped",
          continuous_seconds=args.time_limit, elapsed_seconds=perf_counter()-started, failure=failure))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
