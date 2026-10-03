"""Fixed-workpiece construction and legacy storage; no mechanics evaluation."""
from copy import deepcopy
import json
from pathlib import Path

import numpy as np
import pytest

from hf_eval.native_project import build_native_project, write_native_project
from hf_eval.project import ProjectError
from hf_eval import tmc, tmc_kernel
from test_native_project import inputs


ROOT = Path(__file__).resolve().parents[2]
MODEL_STAGE = ROOT/"lf_data_preparation/native_model_001/models"


@pytest.fixture(autouse=True)
def no_mechanics(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Workpiece construction invoked mechanics evaluation")
    monkeypatch.setattr(tmc, "assemble", forbidden)
    for name in ("_runtime", "batch_response"):
        monkeypatch.setattr(tmc_kernel, name, forbidden)


def body_task(alias, shape="square"):
    source, task, _ = inputs(alias)
    task = deepcopy(task)
    task.update(schema_version="hf-native-project-task-1.1", task_id="TEST_fixed_workpiece_"+alias+"_"+shape,
                purpose="workpiece_construction_test_only", path=dict(kind="ordered_cycle", targets_mm=[0., .1, 0.]))
    task["input"]["target_mm"] = .1
    task["workpiece"] = dict(kind="fixed_rigid", shape=shape, center_mm=[70., 40.], fixed_components=[0, 1])
    task["workpiece"]["side_mm" if shape=="square" else "radius_mm"] = 16. if shape=="square" else 8.
    return source, task


@pytest.mark.parametrize("alias,shape,cells,nodes,fixed,overlap", [
    ("gripper_canonical", "square", 128, 153, 376, 17),
    ("gripper_native_fine", "square", 512, 561, 1258, 33),
    ("gripper_native_fine", "circle", 406, 455, 1046, 33),
])
def test_actual_geometry_fixed_overlay_preserves_source_material_and_ports(alias, shape, cells, nodes, fixed, overlap, tmp_path):
    source, task = body_task(alias, shape)
    original_task = deepcopy(task)
    source_bytes = source.read_bytes(), source.with_name("geometry.npz").read_bytes()
    project = build_native_project(source, task)
    assert task == original_task and project.task == original_task
    model, group = project.model, project.region_metadata["workpiece"]
    assert (group["selected_cells"], group["incident_nodes"], len(model.fixed_dofs)) == (cells, nodes, fixed)
    assert len(group["background_symmetry_overlap_dofs"]) == overlap
    assert group["initial_gaps_mm"] == {"left": 2., "bottom": 2.}
    assert group["definition"] == task["workpiece"]
    cell_ids, node_ids, dofs = (np.asarray(group[name], dtype=np.int64) for name in ("cells", "nodes", "dofs"))
    assert np.all(project.geometry.arrays["passive_void"].ravel()[cell_ids])
    assert not np.intersect1d(node_ids, project.solid_nodes).size
    assert np.all(np.isin(model.edofs[cell_ids].ravel(), model.fixed_dofs))
    assert len(dofs) == 2*nodes
    for name in ("support", "input", "output"):
        selected = (project.region_metadata["support"]["attached_nodes"] if name=="support"
                    else project.region_metadata["ports"][name]["nodes"])
        assert not np.intersect1d(node_ids, selected).size
    old_meta = json.loads((MODEL_STAGE/alias/"model.json").read_text(encoding="utf-8"))
    assert project.material == old_meta["material"]
    assert project.qualification == old_meta["qualification"]
    for name in ("support", "entity_symmetry", "background_symmetry", "ports"):
        assert project.region_metadata[name] == old_meta["region_metadata"][name]
    descriptor = write_native_project(project, tmp_path/"saved")
    saved = json.loads(descriptor.read_text(encoding="utf-8"))
    assert saved["schema_version"] == "hf-native-project-model-1.1"
    assert saved["native_geometry_preserved"] is True
    assert saved["region_metadata"]["effective_boundary"]["workpiece_constraint_overlay"] is True
    with np.load(MODEL_STAGE/alias/"model.npz", allow_pickle=False) as old, np.load(descriptor.parent/"model.npz", allow_pickle=False) as new:
        added = {"workpiece_cells", "workpiece_nodes", "workpiece_dofs", "workpiece_background_symmetry_overlap_dofs"}
        assert set(new.files) == set(old.files) | added
        for name in old.files:
            if name not in ("fixed_dofs", "free_dofs"):
                np.testing.assert_array_equal(new[name], old[name], err_msg=name)
        np.testing.assert_array_equal(new["fixed_dofs"], np.union1d(old["fixed_dofs"], dofs))
        np.testing.assert_array_equal(new["free_dofs"], np.setdiff1d(np.arange(model.ndof), new["fixed_dofs"]))
        for name in added:
            assert new[name].dtype == np.int64
            np.testing.assert_array_equal(new[name], group[name.removeprefix("workpiece_")])
    snapshot = descriptor.parent/"source_geometry"
    assert (snapshot/"geometry.json").read_bytes() == source_bytes[0]
    assert (snapshot/"geometry.npz").read_bytes() == source_bytes[1]
    assert source.read_bytes() == source_bytes[0] and source.with_name("geometry.npz").read_bytes() == source_bytes[1]


def test_legacy_1_0_model_metadata_and_all_23_arrays_remain_identical(tmp_path):
    alias = "gripper_canonical"
    source, task, _ = inputs(alias)
    project = build_native_project(source, task)
    descriptor = write_native_project(project, tmp_path/"legacy")
    saved, previous = (json.loads(p.read_text(encoding="utf-8")) for p in (descriptor, MODEL_STAGE/alias/"model.json"))
    assert saved == previous
    assert "path" not in project.task and "workpiece" not in project.region_metadata
    assert len(project.model.fixed_dofs) == 87
    with np.load(descriptor.parent/"model.npz", allow_pickle=False) as current, np.load(MODEL_STAGE/alias/"model.npz", allow_pickle=False) as old:
        assert len(current.files) == 23 and current.files == old.files
        for name in old.files:
            np.testing.assert_array_equal(current[name], old[name], err_msg=name)


def test_passive_void_cells_that_share_mechanism_nodes_are_rejected():
    source, task = body_task("gripper_native_fine")
    task["workpiece"]["side_mm"] = 20.  # Fills the passive window but touches the original x60/y30 mechanism boundary.
    with pytest.raises(ProjectError, match="shares nodes with the original mechanism"):
        build_native_project(source, task)


@pytest.mark.parametrize("targets,kind,message", [
    ([0., .1, .05], "load_only", "load_only path must strictly increase"),
    ([0., .1, 0., .1], "ordered_cycle", "ordered_cycle must descend and finish below"),
])
def test_explicit_path_kind_and_peak_have_physical_meaning(targets, kind, message):
    source, task = body_task("gripper_canonical")
    task["path"] = dict(kind=kind, targets_mm=targets)
    with pytest.raises(ProjectError, match=message):
        build_native_project(source, task)


def test_workpiece_requires_explicit_matching_background_symmetry():
    source, task = body_task("gripper_canonical")
    task["background_symmetry"] = None
    with pytest.raises(ProjectError, match="explicit background y-symmetry"):
        build_native_project(source, task)
