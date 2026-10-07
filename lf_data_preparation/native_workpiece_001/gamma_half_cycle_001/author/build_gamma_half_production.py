"""Freeze one fresh gamma-half production card after preparation; do not run it."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import argparse
import json
import shutil
import subprocess

BASELINE = "16ee4ebb67161e2c8bc9a27d8e44285308778171"
PREFIX = "lf_data_preparation/native_workpiece_001/"
PREP = PREFIX + "gamma_half_preparation_001"
OLD = PREFIX + "enlarged_square_projection_001"
CONTROL = PREFIX + "gamma_half_cycle_001"
WORKER_SHA = "57d18bfea972c09db4c0866bdee3413088342327e32d3926be9eaa1bdbab466a"
LAUNCHER_SHA = "f3a96681afc474e42ae19875579d748237235dce90f21892b016b3b3af862477"
CHANGED = ["gamma", "lam", "mu"]
RSS_LIMIT = 8 * 1024**3
read = lambda p: json.loads(p.read_text(encoding="utf-8"))
digest = lambda p: sha256(p.read_bytes()).hexdigest()


def write(path, value):
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    args = parser.parse_args()
    root, author = args.repo.resolve(), Path(__file__).resolve().parent
    prep, old, control = root / PREP, root / OLD, root / CONTROL
    prepared = prep / "run_001"
    assert not control.exists(), "Fresh production control required; no overwrite or retry"
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip() == BASELINE
    proof = read(prep / "preparation_protocol.json")
    launch = read(prep / "prepare_launch.json")
    receipt = read(prepared / "preparation_receipt.json")
    assert launch["status"] == receipt["status"] == "pass" and launch["exit_code"] == 0
    assert launch["invocations"] == receipt["invocations"] == 1 and launch["stop_reason"] is None
    assert launch["all_bindings_unchanged"] and receipt["inputs_and_sources_unchanged"]
    assert launch["protocol_sha256"] == digest(prep / "preparation_protocol.json")
    assert receipt["model_constructions"] == receipt["model_constructions_completed"] == receipt["model_writes"] == 1
    assert all(receipt[k] == 0 for k in ("force_calls", "tangent_calls", "solver_calls", "HP_calls", "JIT_calls", "LF_imports"))
    comparison = receipt["model_comparison"]
    assert comparison["total_fields"] == 27 and len(comparison["unchanged_fields"]) == 24
    assert comparison["changed_fields"] == CHANGED and comparison["medium_factor"] == .5
    assert comparison["solid_values_byte_exact"]
    assert comparison["comparison_model_file"] == OLD + "/run_001/result/model/model.npz"
    assert all(digest(root / p) == pin for p, pin in proof["bindings"].items())
    assert not (prep / "stop_requested.txt").exists()
    task = read(prepared / "task.json")
    model = read(prepared / "model/model.json")
    prepared_inventory = read(prepared / "input_inventory.json")
    frozen = read(prepared / "source_freeze.json")
    assert digest(prepared / "source_freeze.json") == prepared_inventory["source_freeze_sha256"]
    assert frozen["protocol_sha256"] == digest(prep / "preparation_protocol.json")
    assert frozen["sources"] == proof["sources"]
    assert model["task"] == task and task["third_medium"] == {"gamma": 5e-7}
    assert task["input"]["target_mm"] == 1.2 and len(task["path"]["targets_mm"]) == 24
    assert model["task_sha256"] == receipt["task_sha256"] == prepared_inventory["task_sha256"]
    assert digest(prepared / "model/model.npz") == model["arrays"]["sha256"] == receipt["model_sha256"]
    baseline = read(old / "run_001/input_inventory.json")
    baseline_row = baseline["case"]
    direction = root / baseline_row["direction_file"]
    assert digest(direction) == baseline_row["direction_file_sha256"]
    assert digest(author / "execute_shift_pose.py") == digest(old / "author/execute_shift_pose.py") == WORKER_SHA
    assert digest(old / "launch_pose.py") == LAUNCHER_SHA

    control.mkdir()
    installed, run = control / "author", control / "run_001"
    installed.mkdir(); run.mkdir()
    selected = [author / name for name in ("build_gamma_half_production.py", "execute_shift_pose.py",
        "prepare_shift_pose.py", "README.md", "author_note.json")]
    selected += sorted(author.glob("*review*.json"))
    for file in selected:
        shutil.copyfile(file, installed / file.name)
        assert digest(file) == digest(installed / file.name)
    shutil.copyfile(old / "launch_pose.py", control / "launch_pose.py")
    shutil.copyfile(prepared / "task.json", run / "task.json")
    shutil.copyfile(direction, run / "direction.npz")
    shutil.copytree(prepared / "model", run / "fixture/model")
    assert digest(run / "task.json") == digest(prepared / "task.json")
    assert all(digest(p) == digest(run / "fixture/model" / p.relative_to(prepared / "model"))
        for p in (prepared / "model").rglob("*") if p.is_file())
    sources = dict(frozen["sources"])
    assert len(sources) == 24 and all(digest(root / p) == pin for p, pin in sources.items())
    for name in ("execute_shift_pose.py", "prepare_shift_pose.py"):
        sources[CONTROL + "/author/" + name] = digest(installed / name)
    assert len(sources) == len({Path(p).name for p in sources}) == 26
    capsules = run / "sources"; capsules.mkdir()
    for name, pin in sources.items():
        shutil.copyfile(root / name, capsules / Path(name).name)
        assert digest(capsules / Path(name).name) == pin
    freeze = run / "source_freeze.json"
    write(freeze, dict(schema_version="gamma-half-cycle-source-freeze-1.0", baseline_commit=BASELINE,
        sources=sources, preparation_source_freeze_sha256=digest(prepared / "source_freeze.json"),
        scope="Current24 native core plus original worker and raw model_delta compatibility module; no historical70-source inheritance."))
    model_file = run / "fixture/model/model.npz"
    geometry = run / "fixture/model/source_geometry/geometry.json"
    counts = model["region_metadata"]["counts"]
    row = dict(alias="gripper_coarse_square_x71_side18_gamma_half", source_alias=baseline_row["source_alias"],
        geometry_id=task["geometry"]["geometry_id"], elements=counts["cells"], dofs=counts["dofs"],
        fixed_DOFs=counts["fixed_dofs"], free_DOFs=counts["free_dofs"], result_directory="result",
        targets_mm=task["path"]["targets_mm"], direction_array_sha256=baseline_row["direction_array_sha256"],
        expected_model_changed_fields=CHANGED, unchanged_model_fields=comparison["unchanged_fields"], tangent_mode="chunk256")
    for key, file in (("task", run / "task.json"), ("direction", run / "direction.npz"), ("geometry", geometry),
            ("geometry_npz", geometry.with_suffix(".npz")), ("workpiece_model", model_file),
            ("comparison_model", old / "run_001/result/model/model.npz")):
        row[key + "_file"] = file.relative_to(root).as_posix()
        row[key + ("_file_sha256" if key in ("task", "direction", "geometry") else "_sha256")] = digest(file)
    inputs = {}
    extra = [prep / "preparation_protocol.json", prep / "prepare_launch.json", prepared / "preparation_receipt.json",
        prepared / "input_inventory.json", prepared / "source_freeze.json", old / "run_001/input_inventory.json",
        old / "run_001/result/model/model.npz", direction,
        old / "author/execute_shift_pose.py", old / "author/prepare_shift_pose.py", old / "launch_pose.py"]
    extra += [p for p in run.rglob("*") if p.is_file() and "sources" not in p.relative_to(run).parts]
    inputs.update({p.relative_to(root).as_posix(): digest(p) for p in extra})
    keys = ("schema_version", "settings", "gates", "units", "path_kind", "minimum_increment_basis",
        "direction_definition", "state_authority", "stop_policy", "response_mode", "response_contract",
        "auxiliary_material_energy", "range_observation_rule", "tangent_execution", "predictor_initialization")
    inventory = {key: deepcopy(baseline[key]) for key in keys}
    inventory["settings"]["time_limit_seconds"] = 4500.
    inventory.update(baseline_commit=BASELINE, case=row, source_count=len(sources), source_freeze_sha256=digest(freeze),
        input_bindings=inputs, initial_guess="port_projection",
        execution_limits=dict(production_seconds=4500, production_outer_seconds=4560, sampled_RSS_bytes=RSS_LIMIT),
        model_comparison=dict(total_fields=27, actual_changed_fields=CHANGED, unchanged_fields=comparison["unchanged_fields"],
            parameter_case="gamma_only", medium_factor=.5, solid_values_byte_exact=True),
        qualification="New prepared input only. Fresh zero-start production; no inherited accepted states, HP or clamp qualification.")
    write(run / "input_inventory.json", inventory)
    helpers = {p.relative_to(root).as_posix(): digest(p) for p in installed.iterdir() if p.is_file()}
    helpers[CONTROL + "/launch_pose.py"] = digest(control / "launch_pose.py")
    bindings = {**inputs, **sources, **helpers, (run / "input_inventory.json").relative_to(root).as_posix(): digest(run / "input_inventory.json")}
    assert all(digest(root / p) == pin for p, pin in bindings.items())
    protocol = control / "production_protocol.json"
    write(protocol, dict(schema_version="gamma-half-production-card-1.0", baseline_commit=BASELINE,
        bindings=bindings, sampled_RSS_bytes=RSS_LIMIT, phases=dict(production=dict(helper_seconds=4500, outer_seconds=4560,
            argv=[CONTROL + "/author/execute_shift_pose.py", "--repo", ".", "--input", CONTROL + "/run_001"])),
        initial_guess="port_projection", original_targets_mm=task["path"]["targets_mm"],
        scope="One fresh zero-start24-target gamma-only cycle. Original worker/core/physics/Newton gates; no old accepted states, HP/reference/view phase or pressure/clamp qualification.",
        stop_file_contract="Original launcher writes control/stop_requested.txt; original worker checks control and run_001 before further work.",
        stop_policy="Single production invocation; first failure closes card, no retry, extension or force."))
    print(json.dumps(dict(status="frozen_only_not_executed", protocol_file=protocol.relative_to(root).as_posix(),
        protocol_sha256=digest(protocol), source_count=len(sources), binding_count=len(bindings))), flush=True)


if __name__ == "__main__":
    main()
