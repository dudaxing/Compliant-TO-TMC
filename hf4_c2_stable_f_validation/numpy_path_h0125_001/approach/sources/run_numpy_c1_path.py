"""Small opt-in C1 equilibrium stages using the NumPy force and Jacobian.

Approach starts from zero. Compression explicitly inherits the two stored
arrays at .21875 mm. Original solver gates are retained; saved HP curves are
physical comparisons, not an independent precision audit of newly solved states.
"""
import argparse
import json
from pathlib import Path
import shutil
import sys
from time import perf_counter

import numpy as np
import psutil

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from hf_eval.contact_c1 import build_problem
from hf_eval.prescribed import PrescribedSettings
from hf_eval.split_affine import solve_split_affine_path
from hf_eval.split_numpy_tangent import assemble_split_numpy
from hf_eval.split_prescribed import split_linear_measurement
from hf_eval.split_state import SplitDisplacement
from hf_eval import split_kernel_invariants_hu as force_kernel
from run_numpy_force_comparison import load_npz, read, sha, write


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--reference", type=Path, help="Original C1 run directory")
    source.add_argument("--task-input", type=Path, help="Compact ordinary C1 task files")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--initial", type=Path, help="Explicit approach last_state.npz for compression")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "states").mkdir()
    metadata_path = (args.task_input if args.task_input else args.reference) / "metadata.json"
    metadata = read(metadata_path)
    model_path = (args.task_input / "model.npz" if args.task_input else
                  args.reference / "stages/uniform_tmc/model.npz")
    original = load_npz(model_path)
    problem = build_problem("TMC", metadata["h"], "uniform_tmc")
    model = problem.model
    for key in ("coordinates", "connectivity", "lam", "mu", "solid", "fixed_dofs", "kr"):
        np.testing.assert_array_equal(getattr(model, key), original[key])
    for key in ("grad", "hessian", "weights"):
        np.testing.assert_array_equal(model.ops[key], original[key])
    for key in ("base", "direction", "lift_origin", "lift_shape", "measure_bottom_body", "measure_bottom_total"):
        np.testing.assert_array_equal(getattr(problem, key), original[key])
    for key, value in problem.reaction_groups.items():
        np.testing.assert_array_equal(value, original["group_" + key])
    settings = PrescribedSettings(**metadata["protocol"]["solver"])
    initial = None
    base, origin = problem.base.copy(), problem.lift_origin.copy()
    phase = "approach"
    targets = [0., .125, .21875]
    if args.initial:
        saved = load_npz(args.initial)
        initial = SplitDisplacement(saved["u_lift"], saved["u_fluctuation"])
        assert split_linear_measurement(initial, problem.measure_bottom_body) == .21875
        origin = initial.lift.copy()
        base[model.fixed_dofs] = origin[model.fixed_dofs]
        phase, targets = "compression", [0., .03125, .0625, .15625, .28125]
    np.savez_compressed(args.output / "model.npz", **original)
    np.savez_compressed(args.output / "initial_state.npz", u_lift=origin,
                        u_fluctuation=np.zeros(model.ndof) if initial is None else initial.fluctuation)
    records = []
    if args.task_input:
        curve = read(args.task_input / "baseline_curve.json")
        baseline_curve, audit_sha = curve["states"], curve["original_audit_sha256"]
    else:
        audit_path = args.reference / "audit.json"
        baseline_curve = [dict(d=s["physical_mean_drive"], normal_force_N=float(s["measurements"]["normal_force"]))
                          for s in read(audit_path)["states"]]
        audit_sha = sha(audit_path)
    (args.output / "sources").mkdir()
    paths = [Path(__file__), Path(__file__).with_name("run_numpy_force_comparison.py"),
             *[Path(__file__).parents[1] / "src/hf_eval" / name for name in
             ("split_kernel_invariants_hu.py", "split_numpy_tangent.py", "split_affine.py", "contact_c1.py",
              "compensated_invariants.py", "compensated_kinematics.py", "split_state.py",
              "split_kernel_compensated.py", "split_kernel.py", "displacement.py",
              "split_prescribed.py", "prescribed.py", "tmc.py", "tmc_kernel.py")]]
    for path in paths:
        shutil.copyfile(path, args.output / "sources" / path.name)
    source_bindings = [dict(name=p.name, sha256=sha(p)) for p in paths]
    input_paths = [model_path, metadata_path]
    if args.task_input:
        input_paths.extend(args.task_input / n for n in ("baseline_curve.json", "bindings.json"))
    if args.initial:
        input_paths.append(args.initial)
    input_bindings = [dict(path=p.as_posix(), sha256=sha(p)) for p in input_paths]
    def forbidden(*args, **kwargs):
        raise RuntimeError("Compiled execution is outside this NumPy path")
    force_kernel._runtime = force_kernel._batch_with_tangent = force_kernel._batch_without_tangent = forbidden
    process = psutil.Process()
    def accepted(row):
        state = SplitDisplacement(row["u_lift"], row["u_fluctuation"])
        drive = split_linear_measurement(state, problem.measure_bottom_body)
        normal = -row["group_reactions"]["top"]["constraint_force"]
        body_top = np.flatnonzero((model.coordinates[:, 1] == 1.) &
                                 (model.coordinates[:, 0] >= 0.) & (model.coordinates[:, 0] <= 2.))
        y = model.coordinates[body_top, 1] + state.u_display[2*body_top+1]
        name = f"states/state_{len(records):03d}.npz"
        np.savez_compressed(args.output / name, **{key: row[key] for key in
                            ("u_lift", "u_fluctuation", "internal_force", "material_internal_force",
                             "regularization_internal_force", "J", "F")})
        records.append(dict(path=name, parameter_s=row["d"], physical_drive_mm=drive,
                            normal_force_N=normal, bottom_force_N=row["group_reactions"]["bottom"]["constraint_force"],
                            bottom_body_force_N=row["group_reactions"]["bottom_body"]["constraint_force"],
                            bottom_outer_force_N=row["group_reactions"]["bottom_outer"]["constraint_force"],
                            relative_residual=row["relative_residual"], minimum_J=row["minimum_J"],
                            constraint_error_max_mm=row["prescribed_displacement_error_max"],
                            body_gap_display_min_mm=float((1.25-y).min()),
                            newton_checks=row["newton_checks"], state_sha256=row["state_sha256"]))
        print(f"accepted {phase}: d={drive:.8g} mm, N={normal:.9g}, residual={row['relative_residual']:.3g}, Jmin={row['minimum_J']:.3g}", flush=True)
        if process.memory_info().rss > 8*1024**3:
            raise RuntimeError("NumPy path sampled RSS exceeds 8 GiB")
    begin = perf_counter()
    result = solve_split_affine_path(model, base, problem.direction, origin, problem.lift_shape, targets,
                                    initial_state=initial, reaction_groups=problem.reaction_groups,
                                    settings=settings, force_scale_per_length=100., on_accept=accepted,
                                    assembler=assemble_split_numpy)
    elapsed = perf_counter()-begin
    if result["target_reached"]:
        np.savez_compressed(args.output / "last_state.npz", u_lift=result["u_lift"], u_fluctuation=result["u_fluctuation"])
    def encode(value):
        if isinstance(value, (np.ndarray, np.generic)):
            return value.tolist()
        raise TypeError(type(value).__name__)
    # Iteration diagnostics remain readable; dense element arrays are in NPZs.
    diagnostics = {key: result[key] for key in ("status", "target_reached", "failure", "newton_history",
                    "trials", "failed_attempts", "linear_solve_diagnostics", "timing_seconds", "maximum_bisection_depth")}
    (args.output / "solver_diagnostics.json").write_text(json.dumps(diagnostics, indent=2, default=encode,
                                                       allow_nan=False)+"\n", encoding="utf-8")
    summary = dict(status=result["status"], target_reached=result["target_reached"], phase=phase,
                   targets_parameter_s=targets, settings=vars(settings), elapsed_seconds=elapsed,
                   h_mm=metadata["h"], elements=model.ne, dofs=model.ndof,
                   states=records, baseline_curve=baseline_curve, original_audit_sha256=audit_sha,
                   new_state_independent_HP_audited=False, compiled_work_executed=False,
                   normal_force_semantics="minus full top constraint reaction; includes background medium",
                   deformation_scale=1, initial_source=None if args.initial is None else args.initial.as_posix(),
                   process_peak_working_set_bytes=getattr(process.memory_info(), "peak_wset", process.memory_info().rss),
                   inputs=input_bindings, sources=source_bindings)
    for row in source_bindings:
        assert sha(args.output / "sources" / row["name"]) == row["sha256"]
    for row in input_bindings:
        assert sha(Path(row["path"])) == row["sha256"]
    write(args.output / "summary.json", summary)
    print("finished", phase, result["status"], "elapsed", elapsed, flush=True)
    return 0 if result["target_reached"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
