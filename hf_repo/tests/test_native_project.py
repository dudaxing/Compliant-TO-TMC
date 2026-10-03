"""Five focused construction tests; no force, assembly or equilibrium calls.

Old NPZ files are SHA-bound snapshots for intrinsic fields and reference
operators only. Their F0/lift/path directions confer no response qualification.
"""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
import pytest

from hf_eval.data import ARRAY_NAMES, load_geometry
from hf_eval.native_project import build_native_project, write_native_project
from hf_eval.project import ProjectError


ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / "lf_data_preparation/native_model_001"


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def inputs(alias):
    inventory = json.loads((STAGE / "input_inventory.json").read_text(encoding="utf-8"))
    row = next(item for item in inventory["cases"] if item["alias"] == alias)
    source, task_file = ROOT / row["geometry_file"], ROOT / row["task_file"]
    assert digest(source) == row["geometry_file_sha256"]
    assert digest(source.with_name("geometry.npz")) == row["geometry_npz_sha256"]
    assert digest(task_file) == row["task_file_sha256"]
    assert digest(ROOT / row["old_model_file"]) == row["old_model_sha256"]
    assert digest(ROOT / row["old_parameter_task_file"]) == row["old_parameter_task_file_sha256"]
    return source, json.loads(task_file.read_text(encoding="utf-8")), row


def assert_model_groups(project, fixed_count):
    model, regions = project.model, project.region_metadata
    groups = [np.asarray(regions[name]["dofs"], dtype=int)
              for name in ("support", "entity_symmetry", "background_symmetry")]
    np.testing.assert_array_equal(model.fixed_dofs, np.unique(np.concatenate(groups)))
    assert len(model.fixed_dofs) == fixed_count
    np.testing.assert_array_equal(model.free, np.setdiff1d(np.arange(model.ndof), model.fixed_dofs))
    expected_edofs = (2*model.connectivity[..., None] + [0, 1]).reshape(model.ne, 8)
    np.testing.assert_array_equal(model.edofs, expected_edofs)
    # Weighted mean control is a separate scalar equation. Its node ux values
    # are not independently placed in the Dirichlet set; output is free along b.
    assert not np.any(project.bin[model.fixed_dofs])
    assert not np.any(project.bout[model.fixed_dofs])
    assert project.task["input"]["control"] == "average_displacement"
    assert project.task["input"]["target_mm"] == .025
    assert project.k_out == project.task["input_auxiliary_spring_N_per_mm"] == 0.
    assert project.task["workpiece"] is None


@pytest.mark.parametrize("alias,fixed_count", [("inverter_canonical", 89), ("gripper_canonical", 87)])
def test_coarse_intrinsics_operators_and_actual_groups_match_saved_model(alias, fixed_count, tmp_path):
    source, task, row = inputs(alias)
    original = deepcopy(task)
    project = build_native_project(source, task)
    assert task == original and project.task == original
    model = project.model
    assert model.ne == 3200 and model.ndof == 6642
    with np.load(ROOT / row["old_model_file"], allow_pickle=False) as old:
        for name in ("coordinates", "connectivity", "solid", "lam", "mu", "kr", "hx", "hy", "thickness", "fixed_dofs"):
            np.testing.assert_array_equal(getattr(model, name), old[name], err_msg=name)
        for name in ("grad", "hessian", "weights"):
            np.testing.assert_array_equal(model.ops[name], old[name], err_msg=name)
        np.testing.assert_array_equal(project.bin, old["b_in"])
        np.testing.assert_array_equal(project.bout, old["b_out"])
        assert project.k_out == float(old["k_out"])
        assert project.material["force_scale_per_length"] == float(old["force_scale_per_length"])
        np.testing.assert_array_equal(model.free, np.setdiff1d(np.arange(model.ndof), old["fixed_dofs"]))
    np.testing.assert_array_equal(model.ops["points"], [(xi, eta) for xi in (-1., 0., 1.) for eta in (-1., 0., 1.)])
    assert_model_groups(project, fixed_count)
    assert len(project.region_metadata["support"]["attached_nodes"]) == (4 if alias.startswith("inverter") else 3)
    assert len(project.region_metadata["entity_symmetry"]["attached_nodes"]) == (13 if alias.startswith("inverter") else 14)
    assert len(project.region_metadata["background_symmetry"]["selected_nodes"]) == 81
    descriptor = write_native_project(project, tmp_path / alias)
    saved = json.loads(descriptor.read_text(encoding="utf-8"))
    assert saved["task"] == project.task
    assert saved["task_sha256"] == project.task_sha256
    snapshot = descriptor.parent / saved["source_geometry"]["snapshot"]["descriptor"]
    copied = load_geometry(snapshot)
    assert copied.geometry_id == project.geometry.geometry_id
    assert snapshot.read_bytes() == source.read_bytes()
    for name in ARRAY_NAMES:
        np.testing.assert_array_equal(copied.arrays[name], project.geometry.arrays[name])
    with np.load(descriptor.parent / saved["arrays"]["path"], allow_pickle=False) as archive:
        np.testing.assert_array_equal(archive["fixed_dofs"], model.fixed_dofs)
        np.testing.assert_array_equal(archive["free_dofs"], model.free)
        np.testing.assert_array_equal(archive["edofs"], model.edofs)
        np.testing.assert_array_equal(archive["b_in"], project.bin)
        np.testing.assert_array_equal(archive["b_out"], project.bout)


def test_fine_test_contract_has_physical_h_scaling_and_no_hidden_constraints():
    source, task, row = inputs("gripper_native_fine")
    project = build_native_project(source, task)
    model = project.model
    assert task["purpose"] == "construction_test_only"
    assert task["analysis_grid"] == {"policy": "native"}
    assert (model.ne, len(model.coordinates), model.ndof) == (12800, 13041, 26082)
    assert model.hx == model.hy == .5 and model.thickness == 20.
    assert_model_groups(project, 169)
    assert len(model.free) == 25913
    assert len(project.region_metadata["support"]["attached_nodes"]) == 4
    assert len(project.region_metadata["entity_symmetry"]["attached_nodes"]) == 24
    assert len(project.region_metadata["background_symmetry"]["selected_nodes"]) == 161
    for name in ("input", "output"):
        np.testing.assert_array_equal(project.region_metadata["ports"][name]["weights"], [.125, .25, .25, .25, .125])
    with np.load(ROOT / row["old_model_file"], allow_pickle=False) as coarse:
        np.testing.assert_array_equal(model.ops["grad"], 2*coarse["grad"])
        np.testing.assert_array_equal(model.ops["hessian"], 4*coarse["hessian"])
        np.testing.assert_array_equal(model.ops["weights"], .25*coarse["weights"])
        assert model.kr == float(coarse["kr"])
    assert task["regularization"]["length_mm"] == project.material["regularization_length_mm"] == 80.
    assert project.material["kr_material_factor_applied"] is False
    E, nu = task["material"]["E_MPa"], task["material"]["nu"]
    gamma = np.where(model.solid, 1., task["third_medium"]["gamma"])
    np.testing.assert_array_equal(project.gamma, gamma)
    np.testing.assert_array_equal(model.lam, E*nu/((1+nu)*(1-2*nu))*gamma)
    np.testing.assert_array_equal(model.mu, E/(2*(1+nu))*gamma)
    assert model.ops["weights"].sum() == pytest.approx(5., rel=2e-15)
    assert model.ne*model.ops["weights"].sum() == pytest.approx(80.*40.*20., rel=2e-15)
    # Manufactured affine nodal data checks derivative units and local order,
    # without calling a deformation, material, force or tangent evaluator.
    gradient = np.array([[.125, -.25], [.5, .0625]])
    local = model.coordinates[model.connectivity[0]] @ gradient.T + [.03125, -.015625]
    reconstructed = np.einsum("ai,qaj->qij", local, model.ops["grad"])
    np.testing.assert_array_equal(reconstructed, np.broadcast_to(gradient, (9, 2, 2)))
    np.testing.assert_array_equal(np.einsum("ai,ajk->ijk", local, model.ops["hessian"]), np.zeros((2, 2, 2)))


def test_explicitly_disabled_background_does_not_apply_lf_source_midline():
    source, task, _ = inputs("gripper_canonical")
    changed = deepcopy(task)
    changed["task_id"] += "_no_background_TEST"
    changed["background_symmetry"] = None
    project = build_native_project(source, changed)
    assert_model_groups(project, 20)  # Six support DOFs plus fourteen entity uy.
    background = project.region_metadata["background_symmetry"]
    assert not background["selected_nodes"] and not background["dofs"]
    assert project.geometry.metadata["provenance"]["lf_v2"]["descriptor"]["regions_mm"]["symmetry_background"] is not None
    x, y = project.model.coordinates.T
    source_background_nodes = np.flatnonzero((x > 60.) & (x <= 80.) & (y == 40.))
    assert len(source_background_nodes) == 20
    assert not np.intersect1d(2*source_background_nodes+1, project.model.fixed_dofs).size
    assert task["background_symmetry"] is not None


def test_analysis_grid_policy_is_required_and_not_inferred_from_lf():
    source, task, _ = inputs("gripper_native_fine")
    changed = deepcopy(task)
    del changed["analysis_grid"]
    with pytest.raises(ProjectError, match="analysis_grid policy must be explicitly native"):
        build_native_project(source, changed)
