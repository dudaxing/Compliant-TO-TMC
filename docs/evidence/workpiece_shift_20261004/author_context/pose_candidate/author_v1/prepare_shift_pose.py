"""Prepare one explicit x71 square task and its own native model, without FE response."""
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--task", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--baseline", required=True)
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
        if perf_counter()-STARTED > 120 or peak > RSS_LIMIT or (stage/"stop_requested.txt").exists():
            raise RuntimeError("Preparation resource window closed")

    previous = root/"lf_data_preparation/native_workpiece_001/coarse_square_cycle_010"
    reference = root/"lf_data_preparation/native_workpiece_001/coarse_square_cycle010_ref_003"
    old, result = read(previous/"input_inventory.json"), read(previous/"result/result.json")
    receipt, qualified = read(previous/"execution_receipt.json"), read(reference/"reference/summary.json")
    for directory, phase in ((previous, "production"), (reference, "reference")):
        launch = read(directory/(phase+"_launch.json"))
        assert launch["status"] == "pass" and launch["exit_code"] == 0 and launch["invocations"] == 1
        assert launch["stop_reason"] is None and launch["all_bindings_unchanged"]
    previous_result_sha = digest(previous/"result/result.json")
    assert receipt["status"] == qualified["status"] == "pass" and result["status"] == "success"
    assert qualified["result_sha256"] == receipt["result_sha256"] == previous_result_sha
    assert qualified["accepted_states"] == len(result["states"]) == result["accepted_states"]
    assert qualified["HP_calls_started"] == qualified["HP_calls_completed"] == 2*len(result["states"])
    assert [r["state_sha256"] for r in qualified["states"]] == [r["state_sha256"] for r in result["states"]]
    task, original_task = read(task_file), read(previous/"task.json")
    allowed = {"task_id", "purpose", "parameter_origin", "description", "workpiece",
        "material", "third_medium", "regularization"}
    assert {k:v for k,v in task.items() if k not in allowed} == {k:v for k,v in original_task.items() if k not in allowed}
    assert task["workpiece"] == dict(original_task["workpiece"], center_mm=[71., 40.])
    assert task["material"] == dict(original_task["material"], E_MPa=task["material"]["E_MPa"])
    assert task["regularization"] == dict(original_task["regularization"], alpha=task["regularization"]["alpha"])
    parameters = (task["material"]["E_MPa"], task["third_medium"]["gamma"], task["regularization"]["alpha"])
    assert parameters in ((1., 1e-6, 1e-6), (.5, 2e-6, 2e-6)), "Only the declared pose or future softened parameter case"
    assert task["third_medium"] == {"gamma": parameters[1]}
    material_changed = set() if parameters == (1., 1e-6, 1e-6) else {"lam", "mu", "gamma", "kr", "force_scale_per_length"}
    expected_changed = sorted(OVERLAY | material_changed)
    old_row = old["case"]
    inputs = {p.relative_to(root).as_posix(): digest(p) for p in [
        task_file, previous/"task.json", previous/"input_inventory.json", previous/"source_freeze.json",
        previous/"execution_receipt.json", previous/"production_launch.json", previous/"result/result.json",
        reference/"protocol.json", reference/"reference_launch.json", reference/"reference/lifecycle.json",
        reference/"reference/summary.json", root/old_row["geometry_file"], root/old_row["geometry_npz_file"],
        root/old_row["prior_task_file"], root/old_row["prior_model_file"], root/old_row["workpiece_model_file"],
        (root/old_row["workpiece_model_file"]).with_suffix(".json"), previous/"direction.npz"]}
    for key, pin_key in (("geometry_file", "geometry_file_sha256"), ("geometry_npz_file", "geometry_npz_sha256"),
            ("workpiece_model_file", "workpiece_model_sha256"), ("prior_model_file", "prior_model_sha256")):
        assert digest(root/old_row[key]) == old_row[pin_key]
    inherited = read(previous/"source_freeze.json")["sources"]
    sources = dict(inherited)
    for name in sources:
        assert digest(root/name) == sources[name] == digest(previous/"sources"/Path(name).name)
    for file in (own, own.with_name("execute_shift_pose.py")):
        sources[file.relative_to(root).as_posix()] = digest(file)
    assert len(sources) == len(inherited)+2 == len({Path(p).name for p in sources})
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
        assert np.array_equal(saved["workpiece_cells"], original["workpiece_cells"]+1)
        assert np.array_equal(saved["workpiece_nodes"], original["workpiece_nodes"]+1)
        for key in ("workpiece_dofs", "workpiece_background_symmetry_overlap_dofs"):
            assert np.array_equal(saved[key], original[key]+2)
        with np.load(stage/"direction.npz", allow_pickle=False) as direction:
            assert not np.any(direction["direction"][saved["fixed_dofs"]])
            assert direction["direction"].tobytes() == (saved["b_in"]/abs(saved["b_in"]).max()).tobytes()
    assert (project.model.ne, project.model.ndof, len(project.model.fixed_dofs), len(project.model.free)) == (3200, 6642, 376, 6266)
    body = project.region_metadata["workpiece"]
    assert (body["selected_cells"], body["incident_nodes"], body["fixed_dofs"], len(body["background_symmetry_overlap_dofs"])) == (128, 153, 306, 17)
    row = dict(old_row, alias="gripper_coarse_square_x71", targets_mm=task["path"]["targets_mm"])
    for key, file in (("task", stage/"task.json"), ("direction", stage/"direction.npz")):
        row[key+"_file"] = file.relative_to(root).as_posix(); row[key+"_file_sha256"] = digest(file)
    row.update(workpiece_model_file=fixture.relative_to(root).as_posix(), workpiece_model_sha256=digest(fixture),
        comparison_model_file=old_row["workpiece_model_file"], comparison_model_sha256=old_row["workpiece_model_sha256"],
        expected_model_changed_fields=expected_changed, unchanged_model_fields=sorted(INTRINSIC-material_changed))
    for file in [stage/"task.json", stage/"direction.npz", descriptor, fixture,
            descriptor.parent/"source_geometry/geometry.json", descriptor.parent/"source_geometry/geometry.npz"]:
        inputs[file.relative_to(root).as_posix()] = digest(file)
    capsules = stage/"sources"; capsules.mkdir()
    for name, pin in sources.items():
        shutil.copyfile(root/name, capsules/Path(name).name)
        assert digest(capsules/Path(name).name) == pin
    freeze = stage/"source_freeze.json"
    write(freeze, dict(schema_version="native-workpiece-cycle-source-freeze-1.0", baseline_commit=args.baseline,
        sources=sources, inherited_source_freeze_sha256=digest(previous/"source_freeze.json"),
        scope="Original010 sources are byte-bound context; only new preparation/producer execute. No kernel/API change."))
    inventory = {k:deepcopy(old[k]) for k in ("schema_version", "settings", "gates", "units", "path_kind",
        "minimum_increment_basis", "direction_definition", "state_authority", "stop_policy", "response_mode",
        "response_contract", "auxiliary_material_energy", "range_observation_rule", "tangent_execution")}
    inventory.update(baseline_commit=args.baseline, case=row, source_count=len(sources), source_freeze_sha256=digest(freeze),
        input_bindings=inputs, execution_limits=dict(production_seconds=900, production_outer_seconds=960,
            sampled_RSS_bytes=RSS_LIMIT, preparation_seconds=120, preparation_outer_seconds=150),
        model_comparison=dict(total_fields=27, unchanged_fields=row["unchanged_model_fields"],
            actual_changed_fields=delta, parameter_case="pose_only" if not material_changed else "explicit_softened_parameters"),
        prerequisite_reference=dict(stage=reference.relative_to(root).as_posix(), summary_sha256=digest(reference/"reference/summary.json"),
            scope="Original accepted-state predecessor only; no new-state or failedT qualification."),
        qualification="New shifted model constructed only; no response/HP/clamp/pressure qualification.",
        reference_plan="No reference source/counter contract is inherited; future card must use actual fresh trace and every accepted index.")
    checkpoint()
    assert all(digest(root/p) == pin for p,pin in inputs.items())
    write(stage/"input_inventory.json", inventory)
    write(stage/"preparation_receipt.json", dict(status="pass", invocations=1, model_constructions=1,
        source_count=len(sources), input_count=len(inputs), model_sha256=digest(fixture), task_sha256=project.task_hash,
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
