"""Small ordinary Q1 average-port task, saved-state HP audit and physical plots.

The six-element tensile block demonstrates the split average-port controller.
It is not a mechanism, contact benchmark or workpiece clamping task. Solve,
independent audit and rendering are separate invocations; old evidence is never
overwritten. The audit promotes both saved arrays separately to Decimal.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, localcontext
import gzip
import json
from pathlib import Path
import shutil
import sys
from time import perf_counter

import numpy as np
import psutil
from scipy import sparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from hf_eval.tmc import TMCModel, rectangular_model
from hf_eval.split_state import SplitDisplacement
from hf_eval.displacement import DisplacementSettings
from hf4_split_precision_reference import DecimalSplitQ1Reference
from audit_numpy_c1_path import (candidate, sha, state_hash, NAMES, HP_KEYS,
                                HP_HASHES, D, norm)

GATES = dict(production_residual="1e-9", independent_residual="1e-8",
             force_evaluation="1e-9", average_constraint="1e-10",
             global_force_balance="1e-6", fixed_displacement_mm="8e-11",
             hp80_hp120="1e-40", total_force="1e-11", material_force="1e-9",
             regularization_force="1e-9", total_tangent="1e-10",
             material_tangent="1e-9", regularization_tangent="1e-9",
             augmented_force_tangent="1e-10", augmented_constraint_tangent="1e-10")


def plain(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (np.ndarray, np.generic)):
        return plain(value.tolist())
    if isinstance(value, dict):
        return {key: plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [plain(item) for item in value]
    return value


def write(path, value):
    path.write_text(json.dumps(plain(value), ensure_ascii=False, indent=2,
                               allow_nan=False) + "\n", encoding="utf-8")


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def npz(path):
    with np.load(path, allow_pickle=False) as archive:
        return {name: archive[name].copy() for name in archive.files}


def fixture():
    fixed = (2 * np.array([0, 4, 8])[:, None] + [0, 1]).ravel()
    model = rectangular_model(3, 2, 3., 2., E=100., nu=.3, alpha=1e-6,
                              fixed_dofs=fixed, thickness=1.)
    b_in, b_out, lift_shape = (np.zeros(model.ndof) for _ in range(3))
    b_in[2 * np.array([3, 7, 11])] = [.125, .25, .625]
    b_out[2 * np.array([9, 10, 11]) + 1] = [.25, .5, .25]
    lift_shape[0::2] = model.coordinates[:, 0] / 3.
    values = {name: getattr(model, name) for name in
              ("coordinates", "connectivity", "lam", "mu", "kr", "hx", "hy",
               "thickness", "solid", "fixed_dofs")}
    direction = np.linspace(-.25, .5, model.ndof)
    direction[fixed] = 0.
    values.update(**{name: model.ops[name] for name in ("grad", "hessian", "weights")},
                  F0=np.zeros(model.ndof), b_in=b_in, b_out=b_out, lift_shape=lift_shape,
                  tangent_direction=direction, tangent_multiplier_direction=np.array(.75))
    return model, values


def model_from(values):
    model = TMCModel(*[values[key] for key in ("coordinates", "connectivity", "lam", "mu")],
                     float(values["kr"]), float(values["hx"]), float(values["hy"]),
                     float(values["thickness"]), values["solid"], values["fixed_dofs"])
    for name in ("grad", "hessian", "weights"):
        np.testing.assert_array_equal(model.ops[name], values[name])
    return model


def snapshot(output, names):
    directory = output / "sources"
    directory.mkdir()
    records = []
    for path in names:
        path = Path(path)
        shutil.copyfile(path, directory / path.name)
        records.append(dict(name=path.name, sha256=sha(path)))
    return records


def source_paths(include_controller=False):
    scripts = Path(__file__).parent
    source = scripts.parent / "src/hf_eval"
    names = [Path(__file__), scripts / "audit_numpy_c1_path.py",
             scripts / "hf4_split_precision_reference.py", scripts / "hf2_precision_reference.py"]
    names += [source / name for name in ("tmc.py", "tmc_kernel.py", "displacement.py",
              "split_state.py", "split_kernel_invariants_hu.py", "split_numpy_tangent.py",
              "compensated_invariants.py", "compensated_kinematics.py", "split_kernel_compensated.py",
              "split_affine.py", "split_prescribed.py", "split_kernel.py", "prescribed.py")]
    if include_controller:
        names.append(source / "split_displacement.py")
    return names


def solve(args):
    from hf_eval.split_displacement import solve_split_displacement_path
    from hf_eval.split_numpy_tangent import assemble_split_numpy
    from hf_eval import split_kernel_invariants_hu as force_kernel
    args.output.mkdir(parents=True, exist_ok=False)
    model, values = fixture()
    np.savez_compressed(args.output / "model.npz", **values)
    sources = snapshot(args.output, source_paths(include_controller=True))
    settings = DisplacementSettings(time_limit_seconds=args.time_limit)
    targets = [0., .025, .05, .1]
    protocol = dict(schema_version="split-average-demo-1.0", task="3x2 Q1 tensile block",
                    scope="Ordinary controller demonstration; no contact or clamping qualification",
                    units=dict(length="mm", force="N", stress="MPa", energy="N mm"),
                    E_MPa=100., nu=.3, thickness_mm=1., alpha=1e-6,
                    input_nodes=[3, 7, 11], input_direction="+x", input_weights=[.125, .25, .625],
                    output_nodes=[9, 10, 11], output_direction="+y", output_weights=[.25, .5, .25],
                    prescribed_individual_port_displacements=False,
                    targets_mm=targets, output_spring_N_per_mm=[0., 10.], settings=vars(settings),
                    budget_scope="Each of two production paths separately bounded; later HP audit is separate",
                    sampled_RSS_limit_bytes=8 * 1024**3, gates=GATES, model_sha256=sha(args.output / "model.npz"),
                    extra_augmented_gates="Equation-identity directional checks using inherited force/tangent budgets; HF3 equilibrium gates unchanged",
                    sources=sources)
    write(args.output / "protocol.json", protocol)
    write(args.output / "lifecycle.json", dict(status="prepared", case_count=2,
          continuous_seconds_per_case=args.time_limit, execution_policy="One path per spring; first final failure stops"))
    def forbidden(*unused, **unused_kwargs):
        raise RuntimeError("Compiled execution is outside this NumPy path")
    force_kernel._runtime = force_kernel._batch_with_tangent = force_kernel._batch_without_tangent = forbidden
    cases = []
    process = psutil.Process()
    for stiffness in (0., 10.):
        case = args.output / f"spring_{int(stiffness)}"
        case.mkdir(); (case / "states").mkdir()
        records = []
        write(args.output / "lifecycle.json", dict(status="running", active_case=case.name,
              completed_cases=len(cases), continuous_seconds_per_case=args.time_limit))
        def accepted(row):
            path = f"states/state_{len(records):03d}.npz"
            arrays = {key: row[key] for key in ("u_lift", "u_fluctuation", "internal_force",
                      "material_internal_force", "regularization_internal_force", "support_reaction",
                      "input_force", "spring_force_on_structure", "J")}
            np.savez_compressed(case / path, **arrays)
            scalar = {key: value for key, value in row.items() if not isinstance(value, np.ndarray)}
            scalar.update(path=path, file_sha256=sha(case / path), state_sha256=state_hash(arrays))
            records.append(plain(scalar))
            print(f"spring {stiffness:g}: d={row['d']:.8g} mm R={row['R_input']:.9g} N "
                  f"qout={row['q_out']:.9g} mm residual={row['relative_residual']:.3g}", flush=True)
            if process.memory_info().rss > 8 * 1024**3:
                raise RuntimeError("Sampled RSS exceeds 8 GiB")
        result = solve_split_displacement_path(model, values["b_in"], values["b_out"], targets,
                    k_out=stiffness, lift_shape=values["lift_shape"], settings=settings,
                    force_scale_per_length=100., assembler=assemble_split_numpy, on_accept=accepted)
        diagnostics = {key: value for key, value in result.items() if key not in
                       ("accepted_steps", "target_metrics", "last_accepted_state") and not isinstance(value, np.ndarray)}
        write(case / "solver_diagnostics.json", diagnostics)
        summary = dict(status=result["status"], target_reached=result["target_reached"], k_out_N_per_mm=stiffness,
                       states=records, new_state_independent_HP_audited=False,
                       compiled_work_executed=False, failure=result["failure"], timing_seconds=result["timing_seconds"])
        write(case / "summary.json", summary)
        cases.append(dict(path=case.name, **summary))
        write(args.output / "summary.json", dict(status="pass" if all(c["target_reached"] for c in cases) else "not_pass",
              all_cases_completed=len(cases) == 2, cases=cases, sources=sources,
              process_peak_working_set_bytes=getattr(process.memory_info(), "peak_wset", process.memory_info().rss)))
        if not result["target_reached"]:
            write(args.output / "lifecycle.json", dict(status="stopped", reason=result["failure"], completed_cases=len(cases)))
            return 1
    for path, record in zip(source_paths(include_controller=True), sources):
        assert sha(path) == record["sha256"] == sha(args.output / "sources" / record["name"])
    write(args.output / "lifecycle.json", dict(status="finished", completed_cases=len(cases),
          process_peak_working_set_bytes=getattr(process.memory_info(), "peak_wset", process.memory_info().rss)))
    return 0


def measurements(hp, values, row, stiffness):
    """HF3 mean/force/spring scales applied to the exact new two-array state."""
    with localcontext() as exact:
        exact.prec = 3000
        displacement = hp["physical_displacement_decimal"]
        b_in, b_out = (list(map(D, values[key])) for key in ("b_in", "b_out"))
        qin, qout = (sum((b * u for b, u in zip(vector, displacement)), Decimal(0)) for vector in (b_in, b_out))
        physical_target = D(row["target_origin"]) + D(row["d"])
        constraint = qin - physical_target
    with localcontext() as context:
        context.prec = 120
        internal = hp["internal_decimal"]
        actuator = [b * D(row["R_input"]) for b in b_in]
        spring = [D(stiffness) * b * qout for b in b_out]
        residual = [fi + fs - fe for fi, fs, fe in zip(internal, spring, actuator)]
        fixed = set(map(int, values["fixed_dofs"]))
        free = [i for i in range(len(displacement)) if i not in fixed]
        dscale = max(abs(physical_target), Decimal("1e-6"))
        scale = max(*[norm([part[i] for i in free]) for part in (internal, actuator, spring)],
                    Decimal("1e-8") * Decimal(100) * dscale)
        support = [residual[i] if i in fixed else Decimal(0) for i in range(len(displacement))]
        balance = [sum((support[i] + actuator[i] - spring[i] for i in range(c, len(displacement), 2)), Decimal(0)) for c in (0, 1)]
        balance_scale = max(norm(support) + norm(actuator) + norm(spring), scale)
        direction = list(map(D, values["tangent_direction"]))
        dqout = sum((b * v for b, v in zip(b_out, direction)), Decimal(0))
        dg = sum((b * v for b, v in zip(b_in, direction)), Decimal(0))
        augmented = [a + D(stiffness) * b * dqout - bi * D(values["tangent_multiplier_direction"])
                     for a, b, bi in zip(hp["tangent_action_decimal"], b_out, b_in)]
        return dict(q_in=qin, q_out=qout, force_scale=scale, displacement_scale=dscale,
                    relative_residual=norm([residual[i] for i in free]) / scale,
                    relative_constraint=abs(constraint) / dscale,
                    relative_force_balance=norm(balance) / balance_scale,
                    fixed_error_mm=max(abs(displacement[i]) for i in fixed),
                    min_J=min(x for items in hp["J_decimal"] for x in items),
                    support=support, spring_force=[-s for s in spring], actuator=actuator,
                    augmented_force=augmented, augmented_constraint=dg, free=free)


def audit(args):
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "references").mkdir()
    (args.output / "matrices").mkdir()
    started = perf_counter()
    protocol = read(args.input / "protocol.json")
    assert protocol["gates"] == GATES and protocol["E_MPa"] == 100. and protocol["thickness_mm"] == 1.
    for name, expected in HP_HASHES.items():
        assert sha(Path(__file__).with_name(name)) == expected
    values = npz(args.input / "model.npz")
    assert sha(args.input / "model.npz") == protocol["model_sha256"]
    model = model_from(values)
    sources = snapshot(args.output, source_paths())
    from hf_eval import split_kernel_invariants_hu as force_kernel
    def forbidden(*unused, **unused_kwargs):
        raise RuntimeError("Compiled execution is outside this NumPy audit")
    force_kernel._runtime = force_kernel._batch_with_tangent = force_kernel._batch_without_tangent = forbidden
    inputs = [args.input / "protocol.json", args.input / "model.npz", args.input / "summary.json"]
    initial_hashes = {path: sha(path) for path in inputs}
    rows = []
    hp_attempted, hp_completed = 0, 0
    write(args.output / "lifecycle.json", dict(status="running", continuous_seconds=args.time_limit,
          sampled_RSS_limit_bytes=8 * 1024**3, stop_policy="First error or failed gate stops; no solve or repair"))
    def checkpoint():
        if perf_counter() - started > args.time_limit:
            raise RuntimeError("Independent audit time limit exceeded")
        if psutil.Process().memory_info().rss > 8 * 1024**3:
            raise RuntimeError("Independent audit sampled RSS exceeds 8 GiB")
    def check(checks, name, value, limit):
        value, limit = Decimal(value), Decimal(limit)
        checks.append(dict(name=name, value=str(value), limit=str(limit), pass_gate=value.is_finite() and value <= limit))
    try:
        solve_summary = read(args.input / "summary.json")
        assert solve_summary["status"] == "pass" and solve_summary["all_cases_completed"]
        assert len(solve_summary["cases"]) == 2
        assert [c["k_out_N_per_mm"] for c in solve_summary["cases"]] == [0., 10.]
        for case in solve_summary["cases"]:
            summary_path = args.input / case["path"] / "summary.json"
            inputs.append(summary_path)
            initial_hashes[summary_path] = sha(summary_path)
            summary = read(summary_path)
            assert summary["target_reached"]
            stiffness = summary["k_out_N_per_mm"]
            for index, row in enumerate(summary["states"]):
                checkpoint()
                state_path = args.input / case["path"] / row["path"]
                inputs.append(state_path)
                initial_hashes[state_path] = sha(state_path)
                assert sha(state_path) == row["file_sha256"]
                state = npz(state_path)
                assert state_hash(state) == row["state_sha256"]
                actual = candidate(model, state, values["tangent_direction"])
                checkpoint()
                for name, key in zip(NAMES[:3], ("internal_force", "material_internal_force", "regularization_internal_force")):
                    np.testing.assert_array_equal(actual[name], state[key])
                hp, measured, reference_files = {}, {}, []
                for precision in (80, 120):
                    checkpoint()
                    hp_attempted += 1
                    hp[precision] = DecimalSplitQ1Reference(values, precision=precision).evaluate(
                        state["u_lift"], state["u_fluctuation"], tangent_direction=values["tangent_direction"])
                    hp_completed += 1
                    checkpoint()
                    measured[precision] = measurements(hp[precision], values, row, stiffness)
                    reference_path = args.output / "references" / f"{case['path']}__{index:03d}__hp{precision}.json.gz"
                    with gzip.open(reference_path, "wt", encoding="utf-8") as stream:
                        json.dump(plain(dict(mechanics=hp[precision], task=measured[precision])), stream, allow_nan=False)
                    checkpoint()
                    reference_files.append(dict(path=reference_path.relative_to(args.output).as_posix(), sha256=sha(reference_path)))
                checks = []
                with localcontext() as context:
                    context.prec = 120
                    sf = measured[80]["force_scale"]
                    for name, key in zip(NAMES, HP_KEYS):
                        target = hp[80][key]
                        denominator = sf if name == "total_force" else max(norm(target), (Decimal("1e-12") * sf if "force" in name else Decimal("1e-10")))
                        check(checks, name, norm([D(a) - b for a, b in zip(actual[name], target)]) / denominator, GATES[name])
                        check(checks, name + "__hp80_hp120", norm([a - b for a, b in zip(hp[80][key], hp[120][key])]) / denominator, GATES["hp80_hp120"])
                    check(checks, "force_evaluation", norm([D(a) - b for a, b in zip(state["internal_force"], hp[80]["internal_decimal"])]) / sf, GATES["force_evaluation"])
                    for stored, target in (("input_force", "actuator"), ("spring_force_on_structure", "spring_force"),
                                           ("support_reaction", "support")):
                        check(checks, "saved_" + stored, norm([D(a) - b for a, b in zip(state[stored], measured[80][target])]) / sf,
                              GATES["force_evaluation"])
                    for name in ("q_in", "q_out"):
                        check(checks, "reported_" + name, abs(D(row[name]) - measured[80][name]) / measured[80]["displacement_scale"],
                              GATES["average_constraint"])
                    for precision in (80, 120):
                        for key, gate in (("relative_residual", "independent_residual"), ("relative_constraint", "average_constraint"),
                                          ("relative_force_balance", "global_force_balance"), ("fixed_error_mm", "fixed_displacement_mm")):
                            check(checks, f"hp{precision}__{key}", measured[precision][key], GATES[gate])
                        checks.append(dict(name=f"hp{precision}__positive_J", value=str(measured[precision]["min_J"]), pass_gate=measured[precision]["min_J"] > 0))
                    check(checks, "production_residual", str(row["relative_residual"]), GATES["production_residual"])
                    checks.append(dict(name="support_zero_on_free_dofs", pass_gate=bool(np.all(state["support_reaction"][model.free] == 0.))))
                    stored_balance = [sum((D(state["support_reaction"][i]) + measured[80]["actuator"][i] + measured[80]["spring_force"][i]
                                       for i in range(c, model.ndof, 2)), Decimal(0)) for c in (0, 1)]
                    balance_scale = max(norm(list(map(D, state["support_reaction"]))) + norm(measured[80]["actuator"]) + norm(measured[80]["spring_force"]), sf)
                    check(checks, "stored_support_balance", norm(stored_balance) / balance_scale, GATES["global_force_balance"])
                    v, b_in, b_out = (values[key] for key in ("tangent_direction", "b_in", "b_out"))
                    total_path = args.output / "matrices" / f"{case['path']}__{index:03d}__total.npz"
                    sparse.save_npz(total_path, actual["total_matrix"])
                    spring_matrix = sparse.csc_matrix(stiffness * np.outer(b_out, b_out))
                    free_matrix = (actual["total_matrix"] + spring_matrix)[model.free][:, model.free]
                    column = sparse.csc_matrix(b_in[model.free, None])
                    augmented_matrix = sparse.bmat([[free_matrix, -column], [column.T, None]], format="csc")
                    augmented_path = args.output / "matrices" / f"{case['path']}__{index:03d}__augmented.npz"
                    sparse.save_npz(augmented_path, augmented_matrix)
                    augmented = augmented_matrix @ np.r_[v[model.free], float(values["tangent_multiplier_direction"])]
                    reference_action = measured[80]["augmented_force"]
                    check(checks, "augmented_force_tangent", norm([D(a) - reference_action[i] for a, i in zip(augmented[:-1], model.free)]) /
                          max(norm([reference_action[i] for i in model.free]), Decimal("1e-10")), GATES["augmented_force_tangent"])
                    check(checks, "augmented_constraint_tangent", abs(D(augmented[-1]) - measured[80]["augmented_constraint"]) /
                          max(abs(measured[80]["augmented_constraint"]), Decimal("1e-6")), GATES["augmented_constraint_tangent"])
                    check(checks, "augmented_force_tangent__hp80_hp120", norm([a - b for a, b in zip(measured[80]["augmented_force"], measured[120]["augmented_force"])]) /
                          max(norm(reference_action), Decimal("1e-10")), GATES["hp80_hp120"])
                record = dict(case=case["path"], index=index, state_sha256=row["state_sha256"], d_mm=row["d"],
                              status="pass" if all(c["pass_gate"] for c in checks) else "not_pass", checks=checks,
                              metrics=measured[80], references=reference_files,
                              matrices=[dict(path=p.relative_to(args.output).as_posix(), sha256=sha(p)) for p in (total_path, augmented_path)])
                rows.append(plain(record))
                write(args.output / "summary.json", dict(status="running", states=rows, sources=sources))
                checkpoint()
                print(f"HP audit {case['path']} state {index}: {record['status']}", flush=True)
                if record["status"] != "pass":
                    raise RuntimeError("First saved-state audit failure")
        checkpoint()
        for path, expected in initial_hashes.items():
            assert sha(path) == expected
        for path, record in zip(source_paths(), sources):
            assert sha(path) == record["sha256"] == sha(args.output / "sources" / record["name"])
        bindings = [dict(path=path.relative_to(args.input).as_posix(), sha256=initial_hashes[path]) for path in inputs]
        checkpoint()
        status, failure = "pass", None
    except (ValueError, RuntimeError, ArithmeticError, AssertionError) as error:
        status, failure = "not_pass", str(error)
    bindings = [dict(path=path.relative_to(args.input).as_posix(), sha256=initial_hashes[path]) for path in inputs]
    memory = psutil.Process().memory_info()
    write(args.output / "summary.json", dict(status=status, states=rows, checks_completed=sum(len(row["checks"]) for row in rows),
          new_state_independent_HP_audited=status == "pass", fresh_HP_evaluations=hp_completed,
          fresh_HP_evaluations_attempted=hp_attempted, process_peak_working_set_bytes=getattr(memory, "peak_wset", memory.rss),
          gates=GATES, elapsed_seconds=perf_counter() - started, time_limit_seconds=args.time_limit,
          input_bindings=bindings, sources=sources, failure=failure,
          scope="Saved small tensile-block states only; no contact, workpiece or LF batch qualification"))
    write(args.output / "lifecycle.json", dict(status="finished" if status == "pass" else "stopped",
          continuous_seconds=args.time_limit, elapsed_seconds=perf_counter() - started, failure=failure))
    return 0 if status == "pass" else 1


def plot(args):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    from matplotlib.colors import Normalize
    from matplotlib.animation import PillowWriter
    args.output.mkdir(parents=True, exist_ok=False)
    audit_summary = read(args.audit / "summary.json")
    assert audit_summary["status"] == "pass"
    for binding in audit_summary["input_bindings"]:
        assert sha(args.input / binding["path"]) == binding["sha256"]
    values = npz(args.input / "model.npz")
    cases = read(args.input / "summary.json")["cases"]
    curves = [read(args.input / c["path"] / "summary.json") for c in cases]
    assert [(c["path"], r["state_sha256"]) for c, curve in zip(cases, curves) for r in curve["states"]] == [
           (r["case"], r["state_sha256"]) for r in audit_summary["states"]]
    saved_paths = [[npz(args.input / c["path"] / row["path"]) for row in curve["states"]]
                   for c, curve in zip(cases, curves)]
    final = [states[-1] for states in saved_paths]
    max_force = max(float(np.linalg.norm(state[key].reshape(-1, 2), axis=1).max()) for state in final
                    for key in ("support_reaction", "input_force", "spring_force_on_structure"))
    arrow_scale = .7 / max(max_force, 1e-12)
    color_norm = Normalize(min(float(s["J"].min()) for states in saved_paths for s in states),
                           max(float(s["J"].max()) for states in saved_paths for s in states))
    coords, conn = values["coordinates"], values["connectivity"]
    input_nodes, input_weights = np.array([3, 7, 11]), np.array([.125, .25, .625])
    colors = ("#2274a5", "#cc5c2c")
    def draw_geometry(axis, state, scalar):
        displacement = state["u_lift"] + state["u_fluctuation"]  # rounded display only
        deformed = coords + displacement.reshape(-1, 2)
        polygons = PolyCollection(deformed[conn], array=state["J"].mean(axis=1),
                                  cmap="viridis", norm=color_norm, edgecolors="black", linewidths=.8)
        axis.add_collection(polygons)
        for cell in coords[conn]:
            closed = np.vstack((cell, cell[0]))
            axis.plot(*closed.T, color=".6", linestyle="--", linewidth=.6)
        for key, color, label in (("support_reaction", "#2274a5", "support"),
                  ("input_force", "#cc5c2c", "actuator"), ("spring_force_on_structure", "#9255a0", "output spring")):
            force = state[key].reshape(-1, 2)
            selected = np.linalg.norm(force, axis=1) > 1e-14
            if selected.any():
                axis.quiver(*deformed[selected].T, *(force[selected] * arrow_scale).T,
                            angles="xy", scale_units="xy", scale=1., color=color, width=.007, label=label)
        axis.scatter(*deformed[input_nodes].T, color="#cc5c2c", s=25, zorder=4)
        axis.set(xlim=(-1., 4.), ylim=(-.8, 2.8), aspect="equal", xlabel="x [mm]", ylabel="y [mm]",
                 title=f"Actual geometry x1; d={scalar['d']:.3g} mm; min J={scalar['minimum_J']:.6g}")
        axis.legend(fontsize=8, loc="lower left")
        return polygons
    figure, axes = plt.subplots(2, 4, figsize=(20, 8), constrained_layout=True)
    for index, (case, curve, state) in enumerate(zip(cases, curves, final)):
        row = curve["states"][-1]
        polygons = draw_geometry(axes[index, 0], state, row)
        figure.colorbar(polygons, ax=axes[index, 0], label="element mean J", shrink=.7)
        levels = [r["d"] for r in curve["states"]]
        axes[index, 1].plot(levels, [r["R_input"] for r in curve["states"]], "o-", color=colors[index], label="input multiplier")
        axes[index, 1].plot(levels, [-curve["k_out_N_per_mm"] * r["q_out"] for r in curve["states"]], "s--", color="#9255a0", label="output spring force")
        axes[index, 1].set(xlabel="prescribed input mean [mm]", ylabel="generalized force [N]",
                           title=f"k_out={curve['k_out_N_per_mm']:g} N/mm; fresh HP audit PASS")
        axes[index, 1].grid(alpha=.25); axes[index, 1].legend(fontsize=8)
        axes[index, 2].plot(levels, [r["q_out"] for r in curve["states"]], "o-", color=colors[index])
        axes[index, 2].axhline(0., color=".5", linestyle=":", linewidth=.8)
        axes[index, 2].set(xlabel="prescribed input mean [mm]", ylabel="output weighted y mean [mm]",
                           title=f"Final output mean = {row['q_out']:.8g} mm")
        axes[index, 2].grid(alpha=.25)
        for node, weight in zip(input_nodes, input_weights):
            nodal = [float(saved["u_lift"][2 * node] + saved["u_fluctuation"][2 * node]) for saved in saved_paths[index]]
            axes[index, 3].plot(levels, nodal, "o-", label=f"y={coords[node,1]:g} mm, weight={weight:g}")
        axes[index, 3].plot(levels, levels, color="black", linestyle=":", label="prescribed weighted mean")
        axes[index, 3].set(xlabel="prescribed input mean [mm]", ylabel="individual input ux [mm]",
                           title="Port nodes remain free to deform differently")
        axes[index, 3].grid(alpha=.25); axes[index, 3].legend(fontsize=8)
    figure.suptitle(f"Split average-port ordinary six-element block | geometry x1 | force arrows {arrow_scale:.6g} mm/N\n"
                    "E=100 MPa, nu=0.3, thickness=1 mm; left fixed. No contact or workpiece clamping claim.")
    figure.savefig(args.output / "split_average_demo.png", dpi=180)
    plt.close(figure)
    frame_figure, frame_axes = plt.subplots(1, 2, figsize=(10, 4), constrained_layout=True)
    writer = PillowWriter(fps=1)
    with writer.saving(frame_figure, str(args.output / "split_average_demo.gif"), dpi=150):
        for frame in range(max(len(c["states"]) for c in curves)):
            for index, (case, curve) in enumerate(zip(cases, curves)):
                scalar = curve["states"][min(frame, len(curve["states"]) - 1)]
                saved = npz(args.input / case["path"] / scalar["path"])
                frame_axes[index].clear()
                draw_geometry(frame_axes[index], saved, scalar)
                frame_axes[index].text(.02, .96, f"k={curve['k_out_N_per_mm']:g} N/mm; R={scalar['R_input']:.6g} N",
                                       transform=frame_axes[index].transAxes, va="top", fontsize=9)
            frame_figure.suptitle(f"Average-port deformation x1; common force arrows {arrow_scale:.6g} mm/N | fresh HP PASS")
            writer.grab_frame()
    plt.close(frame_figure)
    shutil.copyfile(Path(__file__), args.output / "viewer_source.py")
    from PIL import Image
    artifacts = []
    for name in ("split_average_demo.png", "split_average_demo.gif"):
        path = args.output / name
        with Image.open(path) as artifact:
            artifacts.append(dict(path=name, sha256=sha(path), bytes=path.stat().st_size,
                                  width=artifact.width, height=artifact.height, frames=getattr(artifact, "n_frames", 1)))
    final_numbers = []
    for case, curve in zip(cases, curves):
        row = curve["states"][-1]
        hp_metrics = [s["metrics"] for s in audit_summary["states"] if s["case"] == case["path"]][-1]
        final_numbers.append(dict(case=case["path"], k_out_N_per_mm=curve["k_out_N_per_mm"], d_mm=row["d"],
              R_input_N=row["R_input"], q_in_mm=row["q_in"], q_out_mm=row["q_out"],
              production_relative_residual=row["relative_residual"], constraint_residual_mm=row["constraint_residual"],
              production_relative_constraint=abs(row["constraint_residual"]) / row["displacement_scale"], minimum_J=row["minimum_J"],
              spring_generalized_force_N=row["output_spring_generalized_force"],
              spring_force_magnitude_N=abs(row["output_spring_generalized_force"]), spring_energy_N_mm=row["output_spring_energy"],
              independent_HP_relative_residual=hp_metrics["relative_residual"],
              independent_HP_relative_constraint=hp_metrics["relative_constraint"],
              independent_HP_minimum_J=hp_metrics["min_J"]))
    write(args.output / "metadata.json", dict(deformation_scale=1., force_arrow_mm_per_N=arrow_scale,
          audit_sha256=sha(args.audit / "summary.json"), model_sha256=sha(args.input / "model.npz"),
          source_sha256=sha(Path(__file__)), state_count=sum(len(c["states"]) for c in curves),
          input_bindings=audit_summary["input_bindings"], artifacts=artifacts,
          J_color_range=[color_norm.vmin, color_norm.vmax], final_numbers=final_numbers,
          note="Force arrows are support/actuator/output-spring actions; deformed geometry uses rounded display only"))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("solve", "audit", "plot"))
    parser.add_argument("--input", type=Path)
    parser.add_argument("--audit", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--time-limit", type=float)
    args = parser.parse_args()
    if args.mode in ("audit", "plot") and args.input is None:
        parser.error("audit/plot requires --input")
    if args.mode == "plot" and args.audit is None:
        parser.error("plot requires --audit")
    if args.time_limit is None:
        args.time_limit = 60. if args.mode == "solve" else 180.
    return dict(solve=solve, audit=audit, plot=plot)[args.mode](args)


if __name__ == "__main__":
    raise SystemExit(main())
