"""Prepare a new x72 boundary-touch square and native model, without FE response."""
from pathlib import Path
from time import perf_counter
from datetime import datetime, timezone
from hashlib import sha256
from copy import deepcopy
import argparse
import json
import shutil
import subprocess
import sys

STARTED = perf_counter()
RSS_LIMIT = 8 * 1024**3
INTRINSIC = {"coordinates", "connectivity", "solid", "lam", "mu", "gamma", "edofs",
    "solid_nodes", "solid_dofs", "b_in", "b_out", "grad", "hessian", "weights", "points",
    "kr", "hx", "hy", "thickness", "k_out", "force_scale_per_length"}
OVERLAY = {"fixed_dofs", "free_dofs", "workpiece_cells", "workpiece_nodes", "workpiece_dofs",
    "workpiece_background_symmetry_overlap_dofs"}
read = lambda p: json.loads(p.read_text(encoding="utf-8"))
digest = lambda p: sha256(p.read_bytes()).hexdigest()


def model_delta(saved, original):
    """Compare stored fields only; no response, operators or model reconstruction."""
    assert set(saved) == set(original) == INTRINSIC | OVERLAY
    return sorted(k for k in saved if saved[k].dtype != original[k].dtype
        or saved[k].shape != original[k].shape or saved[k].tobytes() != original[k].tobytes())


def write(path, value):
    with path.open("x", encoding="utf-8") as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write("\n")


def qualified_prerequisites(root):
    """Read complete predecessor identity/cost only; never borrow shifted-state qualification."""
    proofs = {}
    for label, name in (("pose002", "shift_square_pose_002"), ("soft001", "shift_square_soft_001")):
        control = root/"lf_data_preparation/native_workpiece_001"/name
        run = control/"run_001"
        files = [control/n for n in ("production_protocol.json", "production_launch.json", "reference_contract.json",
            "reference_protocol.json", "reference_launch.json", "reference/summary.json", "reference/lifecycle.json")]
        files += [run/n for n in ("task.json", "input_inventory.json", "source_freeze.json", "preparation_receipt.json",
            "execution_receipt.json", "result/result.json", "result/model/model.json", "result/model/model.npz")]
        result, production, summary, lifecycle = (read(p) for p in (run/"result/result.json", run/"execution_receipt.json",
            control/"reference/summary.json", control/"reference/lifecycle.json"))
        for phase in ("production", "reference"):
            terminal = read(control/(phase+"_launch.json"))
            assert terminal["status"] == "pass" and terminal["exit_code"] == 0 and terminal["invocations"] == 1
            assert terminal["stop_reason"] is None and terminal["all_bindings_unchanged"]
            assert terminal["protocol_sha256"] == digest(control/(phase+"_protocol.json"))
        assert result["status"] == "success" and all(result[k] for k in ("path_completed", "task_target_executed", "unload_endpoint_reached"))
        assert production["status"] == summary["status"] == lifecycle["status"] == "pass"
        result_file = run/"result/result.json"
        assert summary["result_sha256"] == production["result_sha256"] == digest(result_file)
        count = len(result["states"])
        assert summary["accepted_states"] == lifecycle["accepted_states_completed"] == result["accepted_states"] == count
        assert summary["HP_calls_started"] == summary["HP_calls_completed"] == lifecycle["HP_calls_completed"] == 2*count
        assert [r["state_sha256"] for r in summary["states"]] == [r["state_sha256"] for r in result["states"]]
        task = read(run/"task.json")
        assert task["workpiece"]["center_mm"] == [71., 40.] and task["workpiece"]["side_mm"] == 16.
        assert task["material"]["E_MPa"] == (1. if label == "pose002" else .5)
        model_file, task_file, summary_file = run/"result/model/model.npz", run/"task.json", control/"reference/summary.json"
        proofs[label] = dict(stage=control.relative_to(root).as_posix(), run_stage=run.relative_to(root).as_posix(), files={p.relative_to(root).as_posix():digest(p) for p in files},
            model_file=model_file.relative_to(root).as_posix(), model_sha256=digest(model_file),
            task_file=task_file.relative_to(root).as_posix(), task_file_sha256=digest(task_file),
            result_file=result_file.relative_to(root).as_posix(), result_sha256=digest(result_file),
            summary_file=summary_file.relative_to(root).as_posix(), summary_sha256=digest(summary_file),
            accepted_states=count, HP_calls=summary["HP_calls_completed"],
            production_helper_seconds=production["elapsed_seconds"], production_outer_seconds=read(control/"production_launch.json")["elapsed_seconds"],
            reference_helper_seconds=summary["elapsed_seconds"], reference_outer_seconds=read(control/"reference_launch.json")["elapsed_seconds"],
            scope="Completed x71 predecessor identity and choice/cost evidence only; no x72 model or accepted-state qualification.")
    return proofs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--task", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--baseline", required=True)
    for role in ("protocol", "launch", "receipt"):
        parser.add_argument("--repair-"+role, type=Path, required=True)
    args = parser.parse_args()
    root, stage, task_file = args.repo.resolve(), args.output.resolve(), args.task.resolve()
    own = Path(__file__).resolve()
    own.relative_to(root); task_file.relative_to(root); stage.relative_to(root)
    assert not stage.exists(), "A preparation run requires a new output directory"
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip() == args.baseline
    import psutil
    process, peak = psutil.Process(), 0

    def checkpoint():
        nonlocal peak
        memory = process.memory_info()
        peak = max(peak, memory.rss, getattr(memory, "peak_wset", memory.rss))
        if perf_counter()-STARTED > 120 or peak > RSS_LIMIT or (stage/"stop_requested.txt").exists() or (stage.parent/"stop_requested.txt").exists():
            raise RuntimeError("Preparation resource window closed")

    previous = root/"lf_data_preparation/native_workpiece_001/coarse_square_cycle_010"
    reference = root/"lf_data_preparation/native_workpiece_001/coarse_square_cycle010_ref_003"
    qualified = qualified_prerequisites(root)
    cost_files = [root/name for item in qualified.values() for name in item["files"]]
    old, result = read(previous/"input_inventory.json"), read(previous/"result/result.json")
    receipt, original_reference = read(previous/"execution_receipt.json"), read(reference/"reference/summary.json")
    for directory, phase in ((previous, "production"), (reference, "reference")):
        launch = read(directory/(phase+"_launch.json"))
        assert launch["status"] == "pass" and launch["exit_code"] == 0 and launch["invocations"] == 1
        assert launch["stop_reason"] is None and launch["all_bindings_unchanged"]
    previous_result_sha = digest(previous/"result/result.json")
    assert receipt["status"] == original_reference["status"] == "pass" and result["status"] == "success"
    assert original_reference["result_sha256"] == receipt["result_sha256"] == previous_result_sha
    assert original_reference["accepted_states"] == len(result["states"]) == result["accepted_states"]
    assert original_reference["HP_calls_started"] == original_reference["HP_calls_completed"] == 2*len(result["states"])
    assert [r["state_sha256"] for r in original_reference["states"]] == [r["state_sha256"] for r in result["states"]]
    task, original_task = read(task_file), read(previous/"task.json")
    allowed = {"task_id", "purpose", "parameter_origin", "description", "workpiece"}
    assert {k:v for k,v in task.items() if k not in allowed} == {k:v for k,v in original_task.items() if k not in allowed}
    assert task["workpiece"] == dict(original_task["workpiece"], center_mm=[72., 40.])
    assert (task["material"]["E_MPa"], task["third_medium"]["gamma"], task["regularization"]["alpha"]) == (1., 1e-6, 1e-6)
    expected_changed = sorted(OVERLAY)
    old_row = old["case"]
    inputs = {p.relative_to(root).as_posix(): digest(p) for p in [
        task_file, previous/"task.json", previous/"input_inventory.json", previous/"source_freeze.json",
        previous/"execution_receipt.json", previous/"production_launch.json", previous/"result/result.json",
        reference/"protocol.json", reference/"reference_launch.json", reference/"reference/lifecycle.json",
        reference/"reference/summary.json", root/old_row["geometry_file"], root/old_row["geometry_npz_file"],
        root/old_row["prior_task_file"], root/old_row["prior_model_file"], root/old_row["workpiece_model_file"],
        (root/old_row["workpiece_model_file"]).with_suffix(".json"), previous/"direction.npz"]}
    inputs.update({p.relative_to(root).as_posix(): digest(p) for p in cost_files})
    for key, pin_key in (("geometry_file", "geometry_file_sha256"), ("geometry_npz_file", "geometry_npz_sha256"),
            ("workpiece_model_file", "workpiece_model_sha256"), ("prior_model_file", "prior_model_sha256")):
        assert digest(root/old_row[key]) == old_row[pin_key]
    inherited = read(previous/"source_freeze.json")["sources"]
    assert len(inherited) == 68
    tangent_key = "hf_repo/src/hf_eval/split_numpy_tangent.py"
    repair_files = [args.repair_protocol.resolve(), args.repair_launch.resolve(), args.repair_receipt.resolve()]
    for file in repair_files:
        file.relative_to(root)
        inputs[file.relative_to(root).as_posix()] = digest(file)
    protocol, launch, repair = (read(file) for file in repair_files)
    transition = protocol["source_transition"]
    current_tangent = digest(root/tangent_key)
    assert transition == dict(path=tangent_key, previous_sha256=inherited[tangent_key], current_sha256=current_tangent)
    assert current_tangent != inherited[tangent_key] and protocol["bindings"][tangent_key] == current_tangent
    assert protocol["schema_version"] == "t44-direction-scaling-repair-1.0"
    assert protocol["phases"]["validation"]["helper_seconds"] == 300 and protocol["phases"]["validation"]["outer_seconds"] == 360
    assert protocol["sampled_RSS_bytes"] == RSS_LIMIT
    assert launch["status"] == "pass" and launch["exit_code"] == 0 and launch["invocations"] == 1
    assert launch["stop_reason"] is None and launch["all_bindings_unchanged"]
    assert launch["protocol_sha256"] == digest(repair_files[0]) and launch["outer_seconds"] == 360
    assert launch["elapsed_seconds"] <= 360 and launch["sampled_RSS_limit_bytes"] == RSS_LIMIT
    assert launch["peak_sampled_tree_RSS_bytes"] <= RSS_LIMIT
    assert repair["status"] == "pass" and repair["pytest_invocations"] == 1 and repair["pytest_exit_code"] == 0
    assert repair["tests"]["tests"] > 0 and all(repair["tests"][key] == 0 for key in ("errors", "failures", "skipped"))
    assert repair["cached_tangent_started"] == repair["cached_tangent_completed"] == 2
    assert repair["HP_calls_started"] == repair["HP_calls_completed"] == 2
    assert repair["full_chunk_all_tensors_byte_equal"] and repair["local_and_global_checks"] == 9603
    assert repair["all_cells"] == 3200 and repair["all_DOFs"] == 6642 and repair["all_bindings_unchanged"]
    assert repair["production_force_changed"] is False and repair["range_guards_changed"] is False
    assert repair["elapsed_seconds"] <= 300 and repair["peak_sampled_RSS_bytes"] <= RSS_LIMIT
    assert repair["cached_force_calls"] == repair["formal_solver_calls"] == repair["formal_physical_path_runs"] == 0
    sources = dict(inherited)
    for name, pin in inherited.items():
        assert digest(previous/"sources"/Path(name).name) == pin
        if name != tangent_key:
            assert digest(root/name) == pin
    sources[tangent_key] = current_tangent
    historical_tangent = previous/"sources"/Path(tangent_key).name
    inputs[historical_tangent.relative_to(root).as_posix()] = inherited[tangent_key]
    source_transition = {tangent_key: dict(previous_sha256=inherited[tangent_key], current_sha256=current_tangent,
        previous_capsule_file=historical_tangent.relative_to(root).as_posix(), previous_capsule_sha256=inherited[tangent_key],
        qualification_protocol_file=repair_files[0].relative_to(root).as_posix(), qualification_protocol_sha256=digest(repair_files[0]),
        qualification_launch_file=repair_files[1].relative_to(root).as_posix(), qualification_launch_sha256=digest(repair_files[1]),
        qualification_receipt_file=repair_files[2].relative_to(root).as_posix(), qualification_receipt_sha256=digest(repair_files[2]),
        scope="Bounded captured T44 derivative support/action proof only; shifted equilibrium requires its own fresh reference.")}
    for file in (own, own.with_name("execute_shift_pose.py")):
        sources[file.relative_to(root).as_posix()] = digest(file)
    assert len(sources) == 70 == len(inherited)+2 == len({Path(p).name for p in sources})
    checkpoint()
    stage.mkdir(parents=True)
    shutil.copyfile(task_file, stage/"task.json")
    shutil.copyfile(previous/"direction.npz", stage/"direction.npz")
    sys.path.insert(0, str(root/"hf_repo/src"))
    import numpy as np
    from hf_eval.native_project import build_native_project, write_native_project
    project = build_native_project(root/old_row["geometry_file"], task)
    descriptor = write_native_project(project, stage/"fixture/model")
    fixture = descriptor.with_suffix(".npz")
    with np.load(fixture, allow_pickle=False) as saved, np.load(root/old_row["workpiece_model_file"], allow_pickle=False) as original:
        delta = model_delta(saved, original)
        assert delta == expected_changed
        assert np.array_equal(saved["workpiece_cells"], original["workpiece_cells"]+2)
        assert np.array_equal(saved["workpiece_nodes"], original["workpiece_nodes"]+2)
        for key in ("workpiece_dofs", "workpiece_background_symmetry_overlap_dofs"):
            assert np.array_equal(saved[key], original[key]+4)
        with np.load(root/qualified["pose002"]["model_file"], allow_pickle=False) as pose:
            pose_delta = model_delta(saved, pose)
            assert pose_delta == expected_changed
            assert all(saved[k].dtype == pose[k].dtype and saved[k].shape == pose[k].shape
                and saved[k].tobytes() == pose[k].tobytes() for k in INTRINSIC)
        with np.load(stage/"direction.npz", allow_pickle=False) as direction:
            assert not np.any(direction["direction"][saved["fixed_dofs"]])
            assert direction["direction"].tobytes() == (saved["b_in"]/abs(saved["b_in"]).max()).tobytes()
    assert (project.model.ne, project.model.ndof, len(project.model.fixed_dofs), len(project.model.free)) == (3200, 6642, 376, 6266)
    body = project.region_metadata["workpiece"]
    assert (body["selected_cells"], body["incident_nodes"], body["fixed_dofs"], len(body["background_symmetry_overlap_dofs"])) == (128, 153, 306, 17)
    row = dict(old_row, alias="gripper_coarse_square_x72_tip", targets_mm=task["path"]["targets_mm"])
    for key, file in (("task", stage/"task.json"), ("direction", stage/"direction.npz")):
        row[key+"_file"] = file.relative_to(root).as_posix(); row[key+"_file_sha256"] = digest(file)
    row.update(workpiece_model_file=fixture.relative_to(root).as_posix(), workpiece_model_sha256=digest(fixture),
        comparison_model_file=old_row["workpiece_model_file"], comparison_model_sha256=old_row["workpiece_model_sha256"],
        expected_model_changed_fields=expected_changed, unchanged_model_fields=sorted(INTRINSIC),
        qualified_pose_model_file=qualified["pose002"]["model_file"], qualified_pose_model_sha256=qualified["pose002"]["model_sha256"])
    for file in [stage/"task.json", stage/"direction.npz", descriptor, fixture,
            descriptor.parent/"source_geometry/geometry.json", descriptor.parent/"source_geometry/geometry.npz"]:
        inputs[file.relative_to(root).as_posix()] = digest(file)
    capsules = stage/"sources"; capsules.mkdir()
    for name, pin in sources.items():
        shutil.copyfile(root/name, capsules/Path(name).name)
        assert digest(capsules/Path(name).name) == pin
    freeze = stage/"source_freeze.json"
    write(freeze, dict(schema_version="native-workpiece-cycle-source-freeze-1.0", baseline_commit=args.baseline,
        sources=sources, inherited_source_freeze_sha256=digest(previous/"source_freeze.json"), source_transition=source_transition,
        scope="Original010 historical capsules remain exact; only the independently qualified tangent source transitions, plus two new wrappers."))
    inventory = {k:deepcopy(old[k]) for k in ("schema_version", "settings", "gates", "units", "path_kind",
        "minimum_increment_basis", "direction_definition", "state_authority", "stop_policy", "response_mode",
        "response_contract", "auxiliary_material_energy", "range_observation_rule", "tangent_execution")}
    inventory["settings"]["time_limit_seconds"] = 1800.0
    inventory.update(baseline_commit=args.baseline, case=row, source_count=len(sources), source_freeze_sha256=digest(freeze),
        source_transition=source_transition, input_bindings=inputs, execution_limits=dict(production_seconds=1800, production_outer_seconds=1860,
            sampled_RSS_bytes=RSS_LIMIT, preparation_seconds=120, preparation_outer_seconds=150),
        model_comparison=dict(total_fields=27, unchanged_fields=row["unchanged_model_fields"],
            actual_changed_fields=delta, parameter_case="pose_only"),
        prerequisite_reference=dict(stage=reference.relative_to(root).as_posix(), summary_sha256=digest(reference/"reference/summary.json"),
            scope="Original accepted-state predecessor only; no new-state or failedT qualification."),
        qualification="New x72 boundary-touch model constructed only; no response/HP/clamp/pressure qualification.",
        qualified_prerequisites=qualified,
        pose_model_comparison=dict(total_fields=27, unchanged_fields=sorted(INTRINSIC), actual_changed_fields=pose_delta,
            scope="New x72 model versus qualified x71/E1: intrinsic identity only; workpiece coverages are distinct."),
        boundary_placement=dict(body_box_mm=[64., 80., 32., 40.], right_outer_boundary_mm=80., right_medium_margin_mm=0.,
            workpiece_touches_analysis_boundary=True, scope="New boundary-touch task; no right-side surrounding medium or inherited embedded-body qualification."),
        budget_evidence=dict(predecessor_production_seconds={name:item["production_helper_seconds"] for name,item in qualified.items()},
            scope="Complete x71/E1 cost1413.35s and x71/E.5 cost1193.07s inform a new1800/1860s E1 card; unknown tip compression cost, no extension or prefix reuse."),
        reference_plan="No reference source/counter contract is inherited; future card must use actual fresh trace and every accepted index.")
    checkpoint()
    assert all(digest(root/p) == pin for p,pin in {**inputs, **sources}.items())
    assert all(digest(previous/"sources"/Path(p).name) == pin for p,pin in inherited.items())
    write(stage/"input_inventory.json", inventory)
    checkpoint()
    write(stage/"preparation_receipt.json", dict(status="pass", invocations=1, model_constructions=1,
        source_count=len(sources), input_count=len(inputs), source_transition=source_transition,
        model_sha256=digest(fixture), task_sha256=project.task_hash,
        model_comparison=inventory["model_comparison"], actual_counts=project.region_metadata["counts"],
        workpiece=body, force_calls=0, tangent_calls=0, solver_calls=0, HP_calls=0,
        zero_call_basis="Only native_project constructor and writer called; no response/assembly/solver API evaluated.",
        inputs_and_sources_unchanged=all(digest(root/p) == pin for p,pin in {**inputs,**sources}.items()),
        elapsed_seconds=perf_counter()-STARTED, sampled_peak_RSS_bytes=peak,
        completed_utc=datetime.now(timezone.utc).isoformat()))
    print(json.dumps(dict(status="prepared_only", sources=len(sources), model_changed_fields=delta,
        input_target_mm=task["input"]["target_mm"], targets_mm=row["targets_mm"])))


if __name__ == "__main__":
    main()
