"""Prepare one x82 HF domain/model and mapped PORT direction; no mechanics."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from time import perf_counter

STARTED = perf_counter()
import argparse
import json
import sys

BASELINE = "abf62b04d0a384f3c9cfa352dd6232ad1d4ab3d1"
OLD = "lf_data_preparation/native_workpiece_001/enlarged_square_projection_001"
CONTROL = "lf_data_preparation/native_workpiece_001/right_margin_preparation_001"
VALIDATION = "lf_data_preparation/native_workpiece_001/right_margin_validation_001"
RSS_LIMIT = 8 * 1024**3
ADAPTER = "hf_repo/src/hf_eval/analysis_domain.py"
CLI = "hf_repo/scripts/prepare_analysis_domain.py"
TEST = "hf_repo/tests/test_analysis_domain.py"
ADAPTER_SHA = "f0929fb8949ca3155b32badf8eabe4b6a563a2541a220a6616c96efc26f179e6"
CLI_SHA = "15c7dfd12cdaaa95ec0c6639ef54335eeb2898537f15283aeaf9b3f02bbf9a06"
TEST_SHA = "56d42ba7829bb413efbe564ff2065feeb83f5a2e864cd188619d0ddb0b2c6de9"
INPUTS = ["run_001/task.json", "run_001/result/model/model.json", "run_001/result/model/model.npz",
    "run_001/result/model/source_geometry/geometry.json", "run_001/result/model/source_geometry/geometry.npz",
    "run_001/direction.npz", "run_001/source_freeze.json", "run_001/execution_receipt.json",
    "run_001/result/result.json", "production_protocol.json", "production_launch.json",
    "reference_protocol.json", "reference_launch.json", "reference/summary.json"]
PROOFS = ["adapter_test_protocol.json", "tests_launch.json", "run_001/test_receipt.json"]
RAW_FIELDS = {"grad", "hessian", "weights", "points", "kr", "hx", "hy", "thickness", "k_out", "force_scale_per_length"}
read = lambda p: json.loads(p.read_text(encoding="utf-8"))
digest = lambda p: sha256(p.read_bytes()).hexdigest()


def write(path, value):
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write("\n")


def checked_inputs(root):
    """Validate actual small-test proof and selected predecessor; transfer no equilibrium."""
    v = root / VALIDATION
    protocol, launch, proof = (read(v / p) for p in PROOFS)
    assert proof["schema_version"] == "right-margin-adapter-test-receipt-1.0" and proof["status"] == "pass"
    assert proof["pytest_exit_code"] == 0 and proof["tests_collected"] == proof["tests_passed"] == 5
    assert proof["constructor_invocations"] == 2 and proof["all_bindings_unchanged"]
    assert all(proof[k] == 0 for k in ("new_force_calls", "new_tangent_calls", "new_equilibrium_calls", "new_HP_calls"))
    assert proof["elapsed_seconds"] <= 120
    assert launch["status"] == "pass" and launch["exit_code"] == 0 and launch["invocations"] == 1
    assert launch["stop_reason"] is None and launch["all_bindings_unchanged"]
    assert launch["elapsed_seconds"] <= 150 and launch["peak_sampled_tree_RSS_bytes"] <= RSS_LIMIT
    assert launch["protocol_sha256"] == digest(v / PROOFS[0]) and launch["bindings"] == protocol["bindings"]
    assert protocol["test_file"] == TEST
    assert protocol["phases"]["tests"]["helper_seconds"] == 120 and protocol["phases"]["tests"]["outer_seconds"] == 150
    assert protocol["sampled_RSS_bytes"] == RSS_LIMIT
    for name, pin in ((ADAPTER, ADAPTER_SHA), (CLI, CLI_SHA), (TEST, TEST_SHA)):
        assert protocol["bindings"][name] == digest(root / name) == pin
    assert all(digest(root / p) == pin for p, pin in protocol["bindings"].items())
    old = root / OLD
    task, model = (read(old / p) for p in INPUTS[:2])
    result, reference = read(old / "run_001/result/result.json"), read(old / "reference/summary.json")
    receipt = read(old / "run_001/execution_receipt.json")
    assert task == model["task"] and task["third_medium"] == {"gamma": 1e-6}
    assert task["regularization"] == dict(alpha=1e-6, length_mm=80.)
    assert task["material"] == dict(E_MPa=1., nu=.3, formulation="plane_strain")
    assert task["workpiece"] == dict(kind="fixed_rigid", shape="square", center_mm=[71., 40.], side_mm=18., fixed_components=[0, 1])
    assert result["status"] == "success" and receipt["status"] == reference["status"] == "pass" and receipt["path_completed"]
    assert result["accepted_states"] == reference["accepted_states"] == receipt["accepted_states"] == 24
    assert reference["result_sha256"] == digest(old / "run_001/result/result.json")
    assert reference["HP_calls_started"] == reference["HP_calls_completed"] == 48
    for phase in ("production", "reference"):
        launch = read(old / (phase + "_launch.json"))
        assert launch["status"] == "pass" and launch["exit_code"] == 0 and launch["invocations"] == 1
        assert launch["stop_reason"] is None and launch["all_bindings_unchanged"]
        assert launch["protocol_sha256"] == digest(old / (phase + "_protocol.json"))
    assert model["arrays"]["sha256"] == digest(old / "run_001/result/model/model.npz")
    return task, model


def compare_models(np, old, new, old_meta, new_meta):
    """Compare saved physical subdomains; stored indices use the new row strides."""
    assert set(old.files) == set(new.files) and len(new.files) == 27
    assert all(old[k].dtype == new[k].dtype for k in old.files)
    assert new["coordinates"].shape == (3403, 2) and new["connectivity"].shape == (3280, 4)
    assert new["edofs"].shape == (3280, 8) and new["b_in"].shape == new["b_out"].shape == (6806,)
    assert all(new[k].shape == (3280,) for k in ("solid", "lam", "mu", "gamma"))
    cell_map = (np.arange(40, dtype=np.int64)[:, None] * 82 + np.arange(80, dtype=np.int64)).ravel()
    node_map = (np.arange(41, dtype=np.int64)[:, None] * 83 + np.arange(81, dtype=np.int64)).ravel()
    dof_map = (2 * node_map[:, None] + np.arange(2, dtype=np.int64)).ravel()
    added_cells = (np.arange(40, dtype=np.int64)[:, None] * 82 + np.array([80, 81])).ravel()
    added_dofs = np.setdiff1d(np.arange(6806), dof_map)
    same = lambda a, b: a.dtype == b.dtype and a.shape == b.shape and a.tobytes() == b.tobytes()
    for name in RAW_FIELDS:
        assert same(new[name], old[name]), name
    assert same(new["coordinates"][node_map], old["coordinates"])
    assert same(new["connectivity"][cell_map], node_map[old["connectivity"]])
    assert same(new["edofs"][cell_map], dof_map[old["edofs"]])
    for name in ("solid", "lam", "mu", "gamma"):
        assert same(new[name][cell_map], old[name]), name
    assert not new["solid"][added_cells].any()
    for name in ("lam", "mu", "gamma"):
        assert np.all(new[name][added_cells] == old[name][~old["solid"]][0]), name
    for name in ("solid_nodes", "workpiece_nodes"):
        assert same(new[name], node_map[old[name]]), name
    for name in ("solid_dofs", "workpiece_dofs", "workpiece_background_symmetry_overlap_dofs"):
        assert same(new[name], dof_map[old[name]]), name
    assert same(new["workpiece_cells"], cell_map[old["workpiece_cells"]])
    extra_top_uy = 2 * np.array([40 * 83 + 81, 40 * 83 + 82], dtype=np.int64) + 1
    assert same(new["fixed_dofs"], np.union1d(dof_map[old["fixed_dofs"]], extra_top_uy))
    assert same(new["free_dofs"], np.setdiff1d(np.arange(6806, dtype=np.int64), new["fixed_dofs"]))
    assert len(new["fixed_dofs"]) == 450 and len(new["free_dofs"]) == 6356
    for name in ("b_in", "b_out"):
        assert same(new[name][dof_map], old[name]) and not new[name][added_dofs].any(), name
    for name in ("support", "entity_symmetry"):
        a, b = old_meta["region_metadata"][name], new_meta["region_metadata"][name]
        for key in a:
            if key in ("selected_nodes", "attached_nodes", "excluded_unattached_nodes"):
                assert b[key] == node_map[np.asarray(a[key], dtype=np.int64)].tolist()
            elif key == "dofs":
                assert b[key] == dof_map[np.asarray(a[key], dtype=np.int64)].tolist()
            else:
                assert b[key] == a[key]
    for name in ("input", "output"):
        a, b = old_meta["region_metadata"]["ports"][name], new_meta["region_metadata"]["ports"][name]
        assert b == {**a, "nodes": node_map[a["nodes"]].tolist(), "nonzero_dofs": dof_map[a["nonzero_dofs"]].tolist()}
    body = new_meta["region_metadata"]["workpiece"]
    assert (body["selected_cells"], body["incident_nodes"], body["fixed_dofs"]) == (162, 190, 380)
    assert len(new["workpiece_background_symmetry_overlap_dofs"]) == 19
    fields = {k: dict(old_shape=list(old[k].shape), new_shape=list(new[k].shape), dtype=new[k].dtype.name,
        old_array_sha256=sha256(old[k].tobytes()).hexdigest(), new_array_sha256=sha256(new[k].tobytes()).hexdigest(),
        raw_equal=same(new[k], old[k]), physical_comparison="pass") for k in sorted(new.files)}
    return dict(cell_map=cell_map, node_map=node_map, dof_map=dof_map), dict(total_fields=27,
        raw_equal_fields=sorted(k for k, v in fields.items() if v["raw_equal"]),
        physically_mapped_fields=sorted(set(fields) - RAW_FIELDS), fields=fields,
        new_top_uy_dofs=extra_top_uy.tolist(), parent_physical_subdomain_byte_exact=True)


def main():
    started = STARTED
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    args = parser.parse_args()
    root, protocol_file = args.repo.resolve(), args.protocol.resolve()
    control, output = root / CONTROL, root / CONTROL / "run_001"
    protocol = read(protocol_file)
    assert protocol_file == control / "preparation_protocol.json" and not output.exists()
    assert protocol["baseline_commit"] == BASELINE and protocol["sampled_RSS_bytes"] == RSS_LIMIT
    assert protocol["phases"]["prepare"]["helper_seconds"] == 120
    assert all(digest(root / p) == pin for p, pin in protocol["bindings"].items())
    old_task, old_model = checked_inputs(root)
    import psutil
    process, peak = psutil.Process(), 0

    def checkpoint():
        nonlocal peak
        peak = max(peak, process.memory_info().rss)
        assert not (control / "stop_requested.txt").exists(), "Supervisor requested stop"
        assert perf_counter() - started <= 120 and peak <= RSS_LIMIT, "Preparation resource limit"

    checkpoint()
    output.mkdir()
    receipt = dict(schema_version="right-margin-preparation-receipt-1.0", status="running", invocations=1,
        geometry_constructions=0, geometry_constructions_completed=0, geometry_writes=0, model_constructions=0,
        model_constructions_completed=0, model_writes=0, direction_writes=0,
        force_calls=0, tangent_calls=0, solver_calls=0, HP_calls=0, JIT_calls=0, LF_imports=0,
        qualification="Preparation and physical mapping only; no equilibrium, contact or force qualification.")
    try:
        sys.path.insert(0, str(root / "hf_repo/src"))
        import numpy as np
        from hf_eval.analysis_domain import write_right_medium_geometry
        from hf_eval.native_project import build_native_project, write_native_project
        parent = root / OLD / "run_001/result/model/source_geometry/geometry.json"
        receipt["geometry_constructions"] = receipt["geometry_writes"] = 1
        geometry = write_right_medium_geometry(parent, output / "geometry", 2)
        receipt["geometry_constructions_completed"] = 1
        checkpoint()
        descriptor, old_geometry = read(geometry), read(parent)
        assert descriptor["grid"]["shape_yx"] == [40, 82] and descriptor["grid"]["extent_mm"] == [82., 40.]
        assert descriptor["region_tags"] == old_geometry["region_tags"] and descriptor["model_extent"] == old_geometry["model_extent"]
        assert descriptor["provenance"]["lf_v2"] == old_geometry["provenance"]["lf_v2"]
        with np.load(geometry.with_suffix(".npz"), allow_pickle=False) as new_g, np.load(parent.with_suffix(".npz"), allow_pickle=False) as old_g:
            for k in old_g.files:
                assert new_g[k][:, :80].tobytes() == old_g[k].tobytes()
                assert np.all(new_g[k][:, 80:] == (1 if k == "passive_void" else 0))
        task = deepcopy(old_task)
        task["geometry"] = {k: descriptor[k] for k in ("geometry_id", "descriptor_sha256")}
        assert task["background_symmetry"]["points_mm"] == [[0., 40.], [80., 40.]]
        task["background_symmetry"]["points_mm"][1][0] = 82.
        task.update(task_id="EXPLORATORY_fixed_square_x71_side18_E1_gamma1em6_rightmargin2_1p2mm",
            purpose="right_medium_margin_single_factor_contact_force_exploration",
            parameter_origin="Derived HF analysis domain adds two right passive-medium columns; original LF physical subdomain and all other physics retained.",
            description="Fixed side18 square center(71,40), right face80, 2mm right medium margin; native h1, E1, gamma1e-6, alpha1e-6, Lr80 and original ports unchanged. Fresh zero-start 24-target 0-1.2-0mm cycle requires its own reference.")
        assert {k for k in task if task[k] != old_task[k]} == {"geometry", "background_symmetry", "task_id", "purpose", "parameter_origin", "description"}
        write(output / "task.json", task)
        receipt["model_constructions"] = 1
        project = build_native_project(geometry, task)
        receipt["model_constructions_completed"] = 1
        checkpoint()
        receipt["model_writes"] = 1
        model_file = write_native_project(project, output / "model")
        metadata = read(model_file)
        assert metadata["region_metadata"]["counts"] == dict(cells=3280, nodes=3403, dofs=6806, solid_cells=1086, medium_cells=2194, solid_incident_nodes=1337, fixed_dofs=450, free_dofs=6356)
        with np.load(model_file.with_suffix(".npz"), allow_pickle=False) as new, np.load(root / OLD / "run_001/result/model/model.npz", allow_pickle=False) as old:
            maps, comparison = compare_models(np, old, new, old_model, metadata)
            direction = new["b_in"] / abs(new["b_in"]).max()
            assert not direction[new["fixed_dofs"]].any()
            with np.load(root / OLD / "run_001/direction.npz", allow_pickle=False) as previous:
                assert direction[maps["dof_map"]].tobytes() == previous["direction"].tobytes()
            np.savez_compressed(output / "direction.npz", direction=direction)
            receipt["direction_writes"] = 1
            np.savez_compressed(output / "mapping.npz", **maps)
        for filename in ("geometry.json", "geometry.npz"):
            assert digest(model_file.parent / "source_geometry" / filename) == digest(geometry.parent / filename)
        write(output / "model_comparison.json", comparison)
        freeze = dict(schema_version="right-margin-preparation-source-freeze-1.0", baseline_commit=BASELINE,
            sources=protocol["sources"], inputs=protocol["input_bindings"], helpers=protocol["helper_bindings"],
            protocol_sha256=digest(protocol_file), capsule_policy="Bind unchanged baseline and current core in place; no old states or duplicate historical capsules.")
        write(output / "source_freeze.json", freeze)
        inventory = dict(schema_version="right-margin-preparation-inputs-1.0", baseline_commit=BASELINE,
            geometry_file=geometry.relative_to(root).as_posix(), parent_geometry_file=parent.relative_to(root).as_posix(),
            task_file=(output / "task.json").relative_to(root).as_posix(), task_sha256=project.task_hash,
            model_file=model_file.relative_to(root).as_posix(), model_sha256=digest(model_file.with_suffix(".npz")),
            direction_file=(output / "direction.npz").relative_to(root).as_posix(), direction_file_sha256=digest(output / "direction.npz"),
            direction_array_sha256=sha256(direction.tobytes()).hexdigest(), direction_definition="PORT = b_in / max(abs(b_in)); rebuilt at6806 DOFs",
            mapping_file=(output / "mapping.npz").relative_to(root).as_posix(), mapping_sha256=digest(output / "mapping.npz"),
            model_comparison=comparison, actual_counts=metadata["region_metadata"]["counts"],
            cells=3280, nodes=3403, DOFs=6806, initial_guess="port_projection", targets_mm=task["path"]["targets_mm"],
            source_freeze_sha256=digest(output / "source_freeze.json"), qualification=receipt["qualification"])
        write(output / "input_inventory.json", inventory)
        assert all(digest(root / p) == pin for p, pin in protocol["bindings"].items())
        outputs = {p.relative_to(output).as_posix(): digest(p) for p in output.rglob("*") if p.is_file()}
        checkpoint()
        receipt.update(status="pass", outputs=outputs, model_comparison=comparison,
            actual_counts=inventory["actual_counts"], model_sha256=inventory["model_sha256"],
            task_sha256=project.task_hash, inputs_and_sources_unchanged=True, final_resource_check_passed=True)
    except Exception as error:
        receipt.update(status="failed", error=dict(type=type(error).__name__, message=str(error)))
        raise
    finally:
        receipt.update(elapsed_seconds=perf_counter() - started, peak_sampled_helper_RSS_bytes=peak,
            helper_seconds=120, sampled_RSS_limit_bytes=RSS_LIMIT)
        write(output / "preparation_receipt.json", receipt)
    print(json.dumps(receipt, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
