"""One NumPy split-average prefix of an unchanged canonical HF3 project.

The parent task still declares 1 mm. This stage solves only [0,.001,.025] mm,
retains the original geometry/material/ports and never qualifies the parent
task, contact or a workpiece. Independent saved-state HP acceptance is separate.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import shutil
import sys
from time import perf_counter

import numpy as np
import psutil

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from hf_eval.project import build_project
from hf_eval.displacement import DisplacementSettings
from hf_eval.split_displacement import solve_split_displacement_path
from hf_eval.split_numpy_tangent import assemble_split_numpy
from hf_eval import split_kernel_invariants_hu as force_kernel
from hf_eval.tmc import TMCError
from run_split_average_demo import read, write, sha, snapshot, source_paths, state_hash, GATES

SCHEMA = "split-project-prefix-1.0"
TARGETS = [0., .001, .025]
CASES = {
    "inverter": dict(
        geometry_id="2e2bb3466ade06f920dfbb92577ccbe46106acec430837bac8e1a30b8083527a",
        fixed_dof_count=89, output_dofs=[6316, 6478, 6640], output_direction=[-1., 0.],
        input_hashes={
            "geometry.json": "dd5e28cd1dff05a96b1599be9084ae3809ae8c96c79f45432e05bb5b1fb00b7f",
            "geometry.npz": "1911362efaa5b6c5104af0cecf95310f262b129f3e0cd2a1c648cf550b756132",
            "task.json": "93a80ed3c7b717773684a3c255dabe76a622835a25560ea2e6ed361f31c2cb36",
            "validation_spec.json": "44eb35fef2e6988bf66c3935b76559531e40f0f567bd5438fe7db2afb7bd583e"}),
    "gripper": dict(
        geometry_id="d4e82cfd629e37f7d0c85aed672ab5df228314147cf5db59aeabb279cee5d91d",
        fixed_dof_count=87, output_dofs=[4697, 4859, 5021], output_direction=[0., 1.],
        input_hashes={
            "geometry.json": "1aad84d50119d5d3c4d2b75c782d6b5d1466895e7df7b4496fde1e61adb7355f",
            "geometry.npz": "f7b23e8d16aedb0ebb5b7dc3954b7b59a80f99b6d3859046aa16904a610d6282",
            "task.json": "0a5d9d1ba3a64d1a715f1b05128da8f2047ad69b82ed9d527aae18f9a693c38b",
            "validation_spec.json": "44eb35fef2e6988bf66c3935b76559531e40f0f567bd5438fe7db2afb7bd583e"}),
}
RSS_LIMIT = 8 * 1024**3


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geometry", type=Path, required=True)
    parser.add_argument("--task", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--time-limit", type=float, default=300.)
    args = parser.parse_args()
    if not np.isfinite(args.time_limit) or args.time_limit <= 0 or args.time_limit > 300.:
        parser.error("time limit must be positive and at most the approved 300 seconds")
    family = read(args.task)["case_family"]
    if family not in CASES:
        parser.error("Only the canonical inverter and gripper tasks are supported")
    case = CASES[family]
    input_hashes = case["input_hashes"]
    original_inputs = {"geometry.json": args.geometry, "geometry.npz": args.geometry.with_name("geometry.npz"),
                       "task.json": args.task,
                       "validation_spec.json": Path(__file__).parents[1] / "configs/hf3/validation_spec.json"}
    for name, path in original_inputs.items():
        assert sha(path) == input_hashes[name], "Canonical input identity differs: " + name
    args.output.mkdir(parents=True, exist_ok=False)
    started = perf_counter()
    process = psutil.Process()
    inputs = args.output / "inputs"
    inputs.mkdir(); (args.output / "states").mkdir()
    for name, path in original_inputs.items():
        shutil.copyfile(path, inputs / name)
        assert sha(inputs / name) == input_hashes[name]
    dependency_paths = source_paths(include_controller=True) + [Path(__file__)]
    dependency_paths += [Path(__file__).parents[1] / "src/hf_eval" / name for name in ("project.py", "data.py", "regions.py")]
    sources = snapshot(args.output, dependency_paths)
    input_bindings = [dict(path="inputs/" + name, sha256=input_hashes[name]) for name in original_inputs]
    started_utc = datetime.now(timezone.utc).isoformat()
    write(args.output / "lifecycle.json", dict(status="prepared", started_utc=started_utc,
          process_id=process.pid, continuous_seconds=args.time_limit, sampled_RSS_limit_bytes=RSS_LIMIT,
          execution_policy="One fixed prefix, first final failure stops, no stage retry"))

    project = build_project(inputs / "geometry.json", read(inputs / "task.json"))
    model = project.model
    assert project.geometry.geometry_id == case["geometry_id"] and project.task["case_family"] == family
    assert project.task["input"]["target_mm"] == 1. and project.k_out == 0.
    assert project.material["E_MPa"] * model.thickness == 20.
    assert (model.ne, model.ndof, len(model.fixed_dofs)) == (3200, 6642, case["fixed_dof_count"])
    input_dofs = np.flatnonzero(project.bin)
    np.testing.assert_array_equal(input_dofs, [6156, 6318, 6480])
    np.testing.assert_array_equal(project.bin[input_dofs], [.25, .5, .25])
    output_dofs = np.flatnonzero(project.bout)
    np.testing.assert_array_equal(output_dofs, case["output_dofs"])
    output_sign = sum(case["output_direction"])
    np.testing.assert_array_equal(project.bout[output_dofs], output_sign * np.array([.25, .5, .25]))
    np.testing.assert_array_equal(project.region_metadata["ports"]["input"]["direction"], [1., 0.])
    np.testing.assert_array_equal(project.region_metadata["ports"]["output"]["direction"], case["output_direction"])
    lift_shape = np.zeros(model.ndof)
    lift_shape[input_dofs] = 1.
    assert project.bin @ lift_shape == 1. and not np.any(lift_shape[model.fixed_dofs])
    tangent_direction = np.linspace(-.25, .5, model.ndof)
    tangent_direction[model.fixed_dofs] = 0.
    tangent_direction /= np.linalg.norm(tangent_direction)
    model_arrays = {name: getattr(model, name) for name in ("coordinates", "connectivity", "lam", "mu", "kr",
                    "hx", "hy", "thickness", "solid", "fixed_dofs")}
    model_arrays.update(**{name: model.ops[name] for name in ("grad", "hessian", "weights")},
                        F0=np.zeros(model.ndof), b_in=project.bin, b_out=project.bout, lift_shape=lift_shape,
                        tangent_direction=tangent_direction, tangent_multiplier_direction=np.array(.75),
                        force_scale_per_length=np.array(20.), k_out=np.array(project.k_out))
    np.savez_compressed(args.output / "model.npz", **model_arrays)
    specification = read(inputs / "validation_spec.json")
    assert specification["minimum_increment_rule"] == "initial target increment / 16"
    settings = DisplacementSettings(tolerance=specification["internal_relative_force_tolerance"],
          constraint_tolerance=specification["constraint_relative_tolerance"],
          displacement_scale_floor=specification["displacement_scale_floor_mm"],
          force_scale_floor_factor=specification["force_scale_floor_factor"], max_checks=specification["max_checks"],
          max_backtracks=specification["max_backtracks"], max_bisections=specification["max_bisections"],
          armijo_c=specification["armijo_c"], minimum_increment=.001 / 16, time_limit_seconds=args.time_limit)
    protocol = dict(schema_version=SCHEMA, case_family=family, units=project.task["units"],
          output_reference_direction=case["output_direction"],
          parent_task_target_mm=1., targets_mm=TARGETS, force_scale_per_length=20., k_out_N_per_mm=0.,
          prefix_policy="Original .001 mm bridge amplitude and first .025 mm full-path target; parent 1 mm task remains incomplete",
          scope=f"Canonical ordinary {family} numerical prefix; independent HP is separate; no contact or clamping qualification",
          geometry_id=project.geometry.geometry_id, geometry_descriptor_sha256=project.geometry.metadata["descriptor_sha256"],
          geometry_file_sha256=input_hashes["geometry.json"], geometry_array_sha256=input_hashes["geometry.npz"],
          task_sha256=project.task_hash, task_file_sha256=input_hashes["task.json"], task_config=project.task,
          geometry_metadata=project.geometry.metadata, material=project.material, region_metadata=project.region_metadata,
          qualification=project.qualification, settings=vars(settings),
          validation_spec_sha256=input_hashes["validation_spec.json"],
          minimum_increment_rule="initial target increment / 16", minimum_increment_derivation=".001 mm / 16 = .0000625 mm",
          lift_policy="Only the three original input ux lift_shape entries equal one; free fluctuations are never tied",
          tangent_direction_policy="linspace(-.25,.5,ndof), fixed entries zero, normalized to unit Euclidean norm",
          force_energy_extent="modeled lower half; no automatic doubling",
          sampled_RSS_limit_bytes=RSS_LIMIT, continuous_seconds=args.time_limit,
          budget_policy="Cooperative checks before/after each NumPy assembly, at acceptance and before success; not a hard process deadline",
          gates=GATES, extra_augmented_gates="Additional equation-identity checks; HF3 physical and equilibrium gates unchanged",
          model_sha256=sha(args.output / "model.npz"), input_bindings=input_bindings, sources=sources,
          origin_paths_record_only={name: str(path.resolve()) for name, path in original_inputs.items()})
    write(args.output / "protocol.json", protocol)
    protocol_sha = sha(args.output / "protocol.json")

    def forbidden(*unused, **unused_kwargs):
        raise RuntimeError("Compiled execution is outside this NumPy prefix")
    force_kernel._runtime = force_kernel._batch_with_tangent = force_kernel._batch_without_tangent = forbidden
    def checkpoint():
        if perf_counter() - started > args.time_limit:
            raise TMCError("Cooperative prefix time limit exceeded", code="time_limit")
        if process.memory_info().rss > RSS_LIMIT:
            raise RuntimeError("Prefix sampled RSS exceeds 8 GiB")
    def numpy_assembler(model, state, *, tangent=True):
        checkpoint()
        result = assemble_split_numpy(model, state, tangent=tangent)
        checkpoint()
        return result
    records = []
    def accepted(row):
        path = f"states/state_{len(records):03d}.npz"
        arrays = {key: row[key] for key in ("u_lift", "u_fluctuation", "internal_force", "material_internal_force",
                  "regularization_internal_force", "support_reaction", "input_force", "spring_force_on_structure", "J")}
        np.savez_compressed(args.output / path, **arrays)
        scalar = {key: value for key, value in row.items() if not isinstance(value, np.ndarray)}
        scalar.update(path=path, file_sha256=sha(args.output / path), state_sha256=state_hash(arrays))
        records.append(scalar)
        write(args.output / "accepted_states.json", dict(states=records))
        print(f"{family} prefix: d={row['d']:.8g} mm R={row['R_input']:.9g} N "
              f"qout={row['q_out']:.9g} mm residual={row['relative_residual']:.3g} Jmin={row['minimum_J']:.9g}", flush=True)
        checkpoint()

    write(args.output / "lifecycle.json", dict(status="running", started_utc=started_utc, process_id=process.pid,
          continuous_seconds=args.time_limit, sampled_RSS_limit_bytes=RSS_LIMIT, source_count=len(sources)))
    result, exception = None, None
    try:
        checkpoint()
        result = solve_split_displacement_path(model, project.bin, project.bout, TARGETS, k_out=project.k_out,
                    lift_shape=lift_shape, settings=settings, force_scale_per_length=20.,
                    assembler=numpy_assembler, on_accept=accepted)
        checkpoint()
        for path, binding in zip(dependency_paths, sources):
            assert sha(path) == binding["sha256"] == sha(args.output / "sources" / binding["name"]), "Source identity changed: " + binding["name"]
        for name, path in original_inputs.items():
            assert sha(path) == input_hashes[name] == sha(inputs / name), "Input identity changed: " + name
        assert sha(args.output / "model.npz") == protocol["model_sha256"], "Saved model identity changed"
        assert sha(args.output / "protocol.json") == protocol_sha, "Saved protocol identity changed"
        checkpoint()
    except (ValueError, RuntimeError, OSError, ArithmeticError, AssertionError) as error:
        exception = dict(type=type(error).__name__, reason=str(error))
    success = result is not None and result["target_reached"] and exception is None
    diagnostics = ({key: result[key] for key in ("status", "target_reached", "failure", "newton_history", "trials",
                    "failed_attempts", "linear_solve_diagnostics", "timing_seconds", "maximum_bisection_depth")}
                   if result is not None else dict(unavailable_due_to_exception=exception))
    write(args.output / "solver_diagnostics.json", diagnostics)
    memory = process.memory_info()
    failure = exception if exception is not None else (result["failure"] if result is not None else None)
    summary = dict(schema_version=SCHEMA, status="success" if success else "failed", target_reached=success,
          case_family=family, output_reference_direction=case["output_direction"],
          k_out_N_per_mm=0., force_scale_per_length=20., parent_task_target_mm=1., targets_mm=TARGETS,
          states=records, failure=failure, timing_seconds=result["timing_seconds"] if result is not None else None,
          invocation_elapsed_seconds=perf_counter() - started, process_peak_working_set_bytes=getattr(memory, "peak_wset", memory.rss),
          model_sha256=protocol["model_sha256"], protocol_sha256=protocol_sha, input_bindings=input_bindings, sources=sources,
          new_state_independent_HP_audited=False, compiled_work_executed=False,
          parent_task_complete=False, qualification=project.qualification["status"],
          scope=f"Only this canonical {family} prefix; parent full stroke and independent acceptance remain incomplete")
    write(args.output / "summary.json", summary)
    write(args.output / "lifecycle.json", dict(status="finished" if success else "stopped", started_utc=started_utc,
          process_id=process.pid, invocation_elapsed_seconds=perf_counter() - started, failure=failure,
          completed_accepted_states=len(records), source_and_input_identity_checked=exception is None))
    print(f"prefix finished: {summary['status']}; {len(records)} accepted states; "
          f"{summary['invocation_elapsed_seconds']:.3f}s", flush=True)
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
