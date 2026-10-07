"""Freeze a fresh right-medium-margin production card after actual preparation."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import argparse
import json
import shutil
import subprocess

BASELINE = "abf62b04d0a384f3c9cfa352dd6232ad1d4ab3d1"
PREFIX = "lf_data_preparation/native_workpiece_001/"
PREP = PREFIX + "right_margin_preparation_001"
OLD = PREFIX + "enlarged_square_projection_001"
RAW_ORIGIN = PREFIX + "gamma_half_cycle_001/author"
CONTROL = PREFIX + "right_margin_cycle_001"
WORKER_SHA = "57d18bfea972c09db4c0866bdee3413088342327e32d3926be9eaa1bdbab466a"
SHIM_SHA = "fbb3e1975a7054599eb7d9fde5bf771805a698fe54015ac3d934e43cba2262ac"
LAUNCHER_SHA = "f3a96681afc474e42ae19875579d748237235dce90f21892b016b3b3af862477"
RSS_LIMIT = 8 * 1024**3
read = lambda p: json.loads(p.read_text(encoding="utf-8"))
digest = lambda p: sha256(p.read_bytes()).hexdigest()


def write(path, value):
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True, help="actual Git repository root")
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
    assert launch["all_bindings_unchanged"] and receipt["inputs_and_sources_unchanged"] and receipt["final_resource_check_passed"]
    assert launch["protocol_sha256"] == digest(prep / "preparation_protocol.json") and launch["bindings"] == proof["bindings"]
    assert receipt["elapsed_seconds"] <= 120 and launch["elapsed_seconds"] <= 150
    assert receipt["peak_sampled_helper_RSS_bytes"] <= RSS_LIMIT and launch["peak_sampled_tree_RSS_bytes"] <= RSS_LIMIT
    assert receipt["geometry_constructions"] == receipt["geometry_constructions_completed"] == receipt["geometry_writes"] == 1
    assert receipt["model_constructions"] == receipt["model_constructions_completed"] == receipt["model_writes"] == receipt["direction_writes"] == 1
    assert all(receipt[k] == 0 for k in ("force_calls", "tangent_calls", "solver_calls", "HP_calls", "JIT_calls", "LF_imports"))
    assert all(digest(root / p) == pin for p, pin in proof["bindings"].items())
    assert all(digest(prepared / p) == pin for p, pin in receipt["outputs"].items())
    assert not (prep / "stop_requested.txt").exists()
    inventory_prepared = read(prepared / "input_inventory.json")
    comparison = read(prepared / "model_comparison.json")
    assert comparison == receipt["model_comparison"] == inventory_prepared["model_comparison"]
    assert comparison["total_fields"] == len(comparison["fields"]) == 27 and comparison["parent_physical_subdomain_byte_exact"]
    changed = sorted(k for k, row in comparison["fields"].items() if not row["raw_equal"])
    unchanged = sorted(k for k, row in comparison["fields"].items() if row["raw_equal"])
    assert unchanged == comparison["raw_equal_fields"] and len(unchanged) == 10 and len(changed) == 17
    assert all(row["physical_comparison"] == "pass" for row in comparison["fields"].values())
    task, model = read(prepared / "task.json"), read(prepared / "model/model.json")
    frozen = read(prepared / "source_freeze.json")
    assert digest(prepared / "source_freeze.json") == inventory_prepared["source_freeze_sha256"]
    assert frozen["protocol_sha256"] == digest(prep / "preparation_protocol.json") and frozen["sources"] == proof["sources"]
    assert model["task"] == task and task["third_medium"] == {"gamma": 1e-6}
    assert task["regularization"] == dict(alpha=1e-6, length_mm=80.) and task["material"] == dict(E_MPa=1., nu=.3, formulation="plane_strain")
    assert task["background_symmetry"]["points_mm"] == [[0.,40.],[82.,40.]] and model["grid"]["shape_yx"] == [40,82]
    assert task["input"]["target_mm"] == 1.2 and task["path"]["targets_mm"] == read(old / "run_001/task.json")["path"]["targets_mm"]
    assert model["task_sha256"] == receipt["task_sha256"] == inventory_prepared["task_sha256"]
    assert digest(prepared / "model/model.npz") == model["arrays"]["sha256"] == receipt["model_sha256"]
    counts = model["region_metadata"]["counts"]
    assert counts == inventory_prepared["actual_counts"] == receipt["actual_counts"]
    assert counts == dict(cells=3280,nodes=3403,dofs=6806,solid_cells=1086,medium_cells=2194,solid_incident_nodes=1337,fixed_dofs=450,free_dofs=6356)
    direction = prepared / "direction.npz"
    assert digest(direction) == inventory_prepared["direction_file_sha256"]
    assert digest(prepared / "mapping.npz") == inventory_prepared["mapping_sha256"]
    for name, pin in (("execute_shift_pose.py", WORKER_SHA), ("prepare_shift_pose.py", SHIM_SHA)):
        assert digest(author / name) == digest(root / RAW_ORIGIN / name) == pin
    assert digest(old / "launch_pose.py") == LAUNCHER_SHA
    baseline = read(old / "run_001/input_inventory.json")
    baseline_row = baseline["case"]
    selected = [author / name for name in ("build_right_margin_production.py", "execute_shift_pose.py", "prepare_shift_pose.py", "README.md", "author_note.json", "source_author_delta.diff")]
    reviews = sorted(author.glob("*review*.json"))
    assert reviews, "Production peer review required before freeze"
    selected += reviews
    control.mkdir()
    installed, run = control / "author", control / "run_001"
    installed.mkdir(); run.mkdir()
    for file in selected:
        shutil.copyfile(file, installed / file.name)
        assert digest(file) == digest(installed / file.name)
    shutil.copyfile(old / "launch_pose.py", control / "launch_pose.py")
    shutil.copyfile(prepared / "task.json", run / "task.json")
    shutil.copyfile(direction, run / "direction.npz")
    shutil.copytree(prepared / "model", run / "fixture/model")
    assert digest(run / "task.json") == digest(prepared / "task.json")
    assert all(digest(p) == digest(run / "fixture/model" / p.relative_to(prepared / "model")) for p in (prepared / "model").rglob("*") if p.is_file())
    sources = {p: pin for p, pin in frozen["sources"].items() if p.startswith("hf_repo/src/hf_eval/")}
    assert len(sources) == 25 and all(digest(root / p) == pin for p,pin in sources.items())
    for name in ("execute_shift_pose.py", "prepare_shift_pose.py"):
        sources[CONTROL + "/author/" + name] = digest(installed / name)
    assert len(sources) == len({Path(p).name for p in sources}) == 27
    capsules = run / "sources"; capsules.mkdir()
    for name,pin in sources.items():
        shutil.copyfile(root / name, capsules / Path(name).name)
        assert digest(capsules / Path(name).name) == pin
    freeze = run / "source_freeze.json"
    write(freeze, dict(schema_version="right-margin-cycle-source-freeze-1.0", baseline_commit=BASELINE,
        sources=sources, preparation_source_freeze_sha256=digest(prepared / "source_freeze.json"),
        scope="Current25 hf_eval sources including derived-domain adapter plus original worker/raw model_delta shim; no70-source historical inheritance."))
    model_file = run / "fixture/model/model.npz"
    geometry = run / "fixture/model/source_geometry/geometry.json"
    row = dict(alias="gripper_coarse_square_x71_side18_right_margin2", source_alias=baseline_row["source_alias"],
        geometry_id=task["geometry"]["geometry_id"], elements=counts["cells"], dofs=counts["dofs"],
        fixed_DOFs=counts["fixed_dofs"], free_DOFs=counts["free_dofs"], result_directory="result",
        targets_mm=task["path"]["targets_mm"], direction_array_sha256=inventory_prepared["direction_array_sha256"],
        expected_model_changed_fields=changed, unchanged_model_fields=unchanged, tangent_mode="chunk256")
    for key,file in (("task",run/"task.json"),("direction",run/"direction.npz"),("geometry",geometry),
            ("geometry_npz",geometry.with_suffix(".npz")),("workpiece_model",model_file),
            ("comparison_model",old/"run_001/result/model/model.npz")):
        row[key+"_file"] = file.relative_to(root).as_posix()
        row[key+("_file_sha256" if key in ("task","direction","geometry") else "_sha256")] = digest(file)
    inputs = dict(proof["bindings"])
    extra = [prep/"preparation_protocol.json",prep/"prepare_launch.json",prepared/"preparation_receipt.json",
        prepared/"input_inventory.json",prepared/"source_freeze.json",prepared/"model_comparison.json",prepared/"mapping.npz",
        old/"run_001/input_inventory.json",old/"run_001/result/model/model.npz",direction,
        root/RAW_ORIGIN/"execute_shift_pose.py",root/RAW_ORIGIN/"prepare_shift_pose.py",old/"launch_pose.py"]
    extra += [p for p in run.rglob("*") if p.is_file() and "sources" not in p.relative_to(run).parts]
    inputs.update({p.relative_to(root).as_posix():digest(p) for p in extra})
    keys = ("schema_version","settings","gates","units","path_kind","minimum_increment_basis",
        "direction_definition","state_authority","stop_policy","response_mode","response_contract",
        "auxiliary_material_energy","range_observation_rule","tangent_execution","predictor_initialization")
    inventory = {key:deepcopy(baseline[key]) for key in keys}
    inventory["settings"]["time_limit_seconds"] = 4500.
    inventory.update(baseline_commit=BASELINE,case=row,source_count=len(sources),source_freeze_sha256=digest(freeze),
        input_bindings=inputs,initial_guess="port_projection",
        execution_limits=dict(production_seconds=4500,production_outer_seconds=4560,sampled_RSS_bytes=RSS_LIMIT),
        model_comparison=dict(total_fields=27,actual_changed_fields=changed,unchanged_fields=unchanged,
            parameter_case="right_medium_domain_margin",parent_physical_subdomain_byte_exact=True,
            preparation_comparison_file=PREP+"/run_001/model_comparison.json",preparation_comparison_sha256=digest(prepared/"model_comparison.json"),
            physical_mapping_file=PREP+"/run_001/mapping.npz",physical_mapping_sha256=digest(prepared/"mapping.npz")),
        qualification="Prepared inputs only. Fresh zero-start production; no inherited accepted states, HP or clamp qualification.")
    write(run/"input_inventory.json",inventory)
    helpers = {p.relative_to(root).as_posix():digest(p) for p in installed.iterdir() if p.is_file()}
    helpers[CONTROL+"/launch_pose.py"] = digest(control/"launch_pose.py")
    bindings = {**inputs,**sources,**helpers,(run/"input_inventory.json").relative_to(root).as_posix():digest(run/"input_inventory.json")}
    assert all(digest(root/p)==pin for p,pin in bindings.items())
    protocol = control/"production_protocol.json"
    write(protocol,dict(schema_version="right-margin-production-card-1.0",baseline_commit=BASELINE,
        bindings=bindings,sampled_RSS_bytes=RSS_LIMIT,phases=dict(production=dict(helper_seconds=4500,outer_seconds=4560,
            argv=[CONTROL+"/author/execute_shift_pose.py","--repo",".","--input",CONTROL+"/run_001"])),
        initial_guess="port_projection",original_targets_mm=task["path"]["targets_mm"],
        scope="One fresh zero-start24-target right-medium-margin cycle; raw worker/core/Newton gates unchanged. No old state seeds, HP/reference/view phase or pressure/clamp qualification.",
        stop_file_contract="Original launcher writes control/stop_requested.txt; original worker checks control and run_001 before further work.",
        stop_policy="Single production invocation; first failure closes card, no retry, extension or force."))
    print(json.dumps(dict(status="frozen_only_not_executed",protocol_file=protocol.relative_to(root).as_posix(),
        protocol_sha256=digest(protocol),source_count=len(sources),binding_count=len(bindings))),flush=True)


if __name__ == "__main__":
    main()
