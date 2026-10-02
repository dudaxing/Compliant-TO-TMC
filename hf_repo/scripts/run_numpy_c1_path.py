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

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from hf_eval.contact_c1 import build_problem
from hf_eval.prescribed import PrescribedSettings
from hf_eval.split_affine import solve_split_affine_path
from hf_eval.split_numpy_tangent import assemble_split_numpy
from hf_eval.split_prescribed import split_linear_measurement
from hf_eval.split_state import SplitDisplacement
from run_numpy_force_comparison import load_npz, read, sha, write


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--initial", type=Path, help="Explicit approach last_state.npz for compression")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "states").mkdir()
    problem = build_problem("TMC", .25, "uniform_tmc")
    model = problem.model
    original = load_npz(args.reference / "stages/uniform_tmc/model.npz")
    for key in ("coordinates", "connectivity", "lam", "mu", "solid", "fixed_dofs"):
        np.testing.assert_array_equal(getattr(model, key), original[key])
    metadata = read(args.reference / "metadata.json")
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
    np.savez_compressed(args.output / "model.npz", coordinates=model.coordinates,
                        connectivity=model.connectivity, solid=model.solid, fixed_dofs=model.fixed_dofs,
                        top_nodes=problem.top_nodes, **{"group_"+k: v for k, v in problem.reaction_groups.items()})
    np.savez_compressed(args.output / "initial_state.npz", u_lift=origin,
                        u_fluctuation=np.zeros(model.ndof) if initial is None else initial.fluctuation)
    records = []
    audit_path = args.reference / "audit.json"
    audit = read(audit_path)
    baseline_curve = [dict(d=s["physical_mean_drive"], normal_force_N=float(s["measurements"]["normal_force"]))
                      for s in audit["states"]]
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
                   states=records, baseline_curve=baseline_curve, original_audit_sha256=sha(audit_path),
                   new_state_independent_HP_audited=False, compiled_work_executed=False,
                   normal_force_semantics="minus full top constraint reaction; includes background medium",
                   deformation_scale=1, initial_source=None if args.initial is None else args.initial.as_posix())
    (args.output / "sources").mkdir()
    paths = [Path(__file__), *[Path(__file__).parents[1] / "src/hf_eval" / name for name in
             ("split_kernel_invariants_hu.py", "split_numpy_tangent.py", "split_affine.py", "contact_c1.py")]]
    for path in paths:
        shutil.copyfile(path, args.output / "sources" / path.name)
    summary["sources"] = [dict(name=p.name, sha256=sha(p)) for p in paths]
    write(args.output / "summary.json", summary)
    print("finished", phase, result["status"], "elapsed", elapsed, flush=True)
    return 0 if result["target_reached"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
