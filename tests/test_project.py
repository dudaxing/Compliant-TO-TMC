"""Project mapping tests: no nonlinear solve or dependence on an LF checkout."""
from copy import deepcopy
import json

import numpy as np
import pytest

from hf_eval.data import canonical_hash, load_geometry, write_geometry
from hf_eval.project import BACKGROUND_DIAGNOSTIC, ProjectError, build_project
from hf_eval.regions import active_nodes, element_connectivity, node_coordinates


def task(family="inverter"):
    return {
        "schema_version": "hf-project-task-1.0", "task_id": f"synthetic_{family}_pilot_v1",
        "case_family": family, "units": {"length": "mm", "force": "N", "stress": "MPa", "energy": "N mm"},
        "material": {"E_MPa": 1.0, "nu": 0.3, "formulation": "plane_strain"},
        "third_medium": {"gamma": 1e-6}, "regularization": {"alpha": 1e-6, "length_mm": 80.0},
        "input": {"tag": "input", "control": "average_displacement", "target_mm": 1.0},
        "output": {"tag": "output", "spring_N_per_mm": 0.0},
        "constraints": [{"tag": "support", "components": [0, 1]}, {"tag": "symmetry", "components": [1]}],
        "support_selection": "solid_incident_nodes_only",
        "background_symmetry": {"points_mm": [[0.0, 40.0], [80.0, 40.0]], "components": [1]},
        "diagnostic_variant": "none", "input_auxiliary_spring_N_per_mm": 0.0,
        "workpiece": None, "reference_state": "undeformed",
        "qualification_criteria": {"max_design_volume_fraction": None, "min_feature_mm": None},
    }


def candidate(tmp_path, family="inverter", *, change_metadata=None, change_solid=None):
    """Connected artificial marker on the pilot grid; never an optimized candidate."""
    solid = np.zeros((40, 80), dtype=np.uint8)
    support_cells = 3 if family == "inverter" else 2
    solid[:support_cells, :3] = 1
    solid[:, 2] = 1
    solid[38:40, :3] = 1
    entity_end = 80 if family == "inverter" else 60
    solid[39, :entity_end] = 1
    output_y = 38 if family == "inverter" else 28
    solid[output_y:output_y+2, 79] = 1
    solid[output_y, 2:] = 1
    if change_solid:
        change_solid(solid)
    metadata = {
        "schema_version": "hf-geometry-1.0", "case_family": family,
        "grid": {"shape_yx": [40, 80], "origin_mm": [0, 0], "cell_size_mm": [1, 1],
                 "extent_mm": [80, 40], "axes": [[1, 0], [0, 1]],
                 "array_order": "C_yx_bottom_up", "value_location": "cell"},
        "thickness_mm": 20,
        "model_extent": {"kind": "lower_half", "symmetry_axis": {"normal": [0, 1], "offset_mm": 40}},
        "region_tags": {
            "support": {"points_mm": [[0, 0], [0, 8]], "components": [0, 1]},
            "symmetry": {"points_mm": [[0, 40], [entity_end, 40]], "components": [1]},
            "input": {"points_mm": [[0, 38], [0, 40]], "direction": [1, 0], "averaging": "normalized_reference_arclength_trapezoid"},
            "output": {"points_mm": [[80, output_y], [80, output_y+2]],
                       "direction": [-1, 0] if family == "inverter" else [0, 1],
                       "averaging": "normalized_reference_arclength_trapezoid"},
        },
        "processing": {"source_symmetry_policy": "full_midline", "source_symmetry_points_mm": [[0, 40], [80, 40]],
                       "source_spring_metrics": {"kin": 10.0, "kout": 1000.0}},
    }
    if change_metadata:
        change_metadata(metadata)
    arrays = {"solid": solid, "design": np.ones_like(solid),
              "passive_solid": np.zeros_like(solid), "passive_void": np.zeros_like(solid)}
    return write_geometry(tmp_path, metadata, arrays)


@pytest.mark.parametrize("family,support_count", [("inverter", 4), ("gripper", 3)])
def test_full_domain_preserves_geometry_and_scales_material_in_project_units(tmp_path, family, support_count):
    path = candidate(tmp_path, family)
    original = load_geometry(path)
    configured = task(family)
    copied_task = deepcopy(configured)
    before = {name: values.copy() for name, values in original.arrays.items()}
    project = build_project(path, configured)
    assert project.model.ne == 3200 and project.model.ndof == 6642
    assert project.model.coordinates.shape == (3321, 2)
    np.testing.assert_array_equal(project.model.coordinates, node_coordinates(original))
    np.testing.assert_array_equal(project.model.connectivity, element_connectivity(original))
    np.testing.assert_array_equal(project.model.solid, original.solid.ravel())
    for name, values in before.items():
        np.testing.assert_array_equal(project.geometry.arrays[name], values)
    assert project.geometry.geometry_id == original.geometry_id
    assert configured == copied_task and project.task is not configured
    assert project.task_hash == project.task_sha256 == canonical_hash(configured)
    assert project.model.thickness == 20
    assert project.model.ops["weights"].sum() == pytest.approx(20.0)
    lam, mu = 0.3 / (1.3 * 0.4), 1.0 / 2.6
    expected_gamma = np.where(original.solid.ravel(), 1.0, 1e-6)
    np.testing.assert_array_equal(project.gamma, expected_gamma)
    np.testing.assert_allclose(project.model.lam, lam * expected_gamma, rtol=1e-15)
    np.testing.assert_allclose(project.model.mu, mu * expected_gamma, rtol=1e-15)
    assert project.model.kr == pytest.approx(1e-6 * 80**2 * (1 / 1.2 + 4 * mu / 3), rel=1e-15)
    assert project.material["kr_material_factor_applied"] is False
    assert project.k_out == 0  # Arbitrary old spring provenance has no runtime effect.
    regions = project.region_metadata
    assert len(regions["support"]["selected_nodes"]) == 9
    assert len(regions["support"]["attached_nodes"]) == support_count
    np.testing.assert_array_equal(project.solid_nodes, np.flatnonzero(active_nodes(original)))
    assert project.qualification["status"] == "pending"
    json.dumps(regions, allow_nan=False)  # No NumPy arrays or NumPy scalars leak into metadata.
    assert not project.bin.flags.writeable and not project.gamma.flags.writeable


@pytest.mark.parametrize("family,output_direction", [("inverter", [-1, 0]), ("gripper", [0, 1])])
def test_reference_ports_keep_weights_direction_and_work_conjugacy(tmp_path, family, output_direction):
    project = build_project(candidate(tmp_path, family), task(family))
    for name, vector in (("input", project.bin), ("output", project.bout)):
        port = project.region_metadata["ports"][name]
        assert port["weights"] == [0.25, 0.5, 0.25]
        assert port["direction"] == ([1, 0] if name == "input" else output_direction)
        u = np.zeros(project.model.ndof)
        nodes = np.array(port["nodes"])
        values = np.array([2.0, 6.0, 10.0])
        for component in (0, 1):
            u[2 * nodes + component] = values * port["direction"][component]
        assert vector @ u == 6.0
        assert (7.0 * vector) @ u == 7.0 * (vector @ u)
        assert not np.any(vector[project.model.fixed_dofs])


def test_solid_and_background_constraints_are_separate_and_deduplicated(tmp_path):
    project = build_project(candidate(tmp_path, "gripper"), task("gripper"))
    regions = project.region_metadata
    entity = np.array(regions["entity_symmetry"]["dofs"])
    background = np.array(regions["background_symmetry"]["dofs"])
    support = np.array(regions["support"]["dofs"])
    assert len(background) == 81
    np.testing.assert_array_equal(regions["intersections"]["entity_symmetry__background_symmetry"], entity)
    np.testing.assert_array_equal(project.model.fixed_dofs, np.unique(np.r_[support, entity, background]))
    assert len(project.model.fixed_dofs) < len(support) + len(entity) + len(background)
    for dof in entity:
        assert regions["fixed_dof_sources"][str(dof)] == ["entity_symmetry", "background_symmetry"]
    assert all(project.model.coordinates[dof // 2, 1] == 40 for dof in background)


def test_gripper_diagnostic_releases_only_twenty_background_dofs(tmp_path):
    path = candidate(tmp_path, "gripper")
    primary = build_project(path, task("gripper"))
    diagnostic_task = task("gripper")
    diagnostic_task["diagnostic_variant"] = BACKGROUND_DIAGNOSTIC
    diagnostic_task["task_id"] += "_background_diagnostic"
    diagnostic = build_project(path, diagnostic_task)
    removed = np.setdiff1d(primary.model.fixed_dofs, diagnostic.model.fixed_dofs)
    assert len(removed) == 20 and np.all(removed % 2 == 1)
    np.testing.assert_array_equal(primary.model.coordinates[removed // 2, 0], np.arange(61, 81))
    assert primary.region_metadata["entity_symmetry"] == diagnostic.region_metadata["entity_symmetry"]
    assert primary.geometry.geometry_id == diagnostic.geometry.geometry_id
    np.testing.assert_array_equal(primary.model.solid, diagnostic.model.solid)
    assert primary.task_hash != diagnostic.task_hash
    assert diagnostic.region_metadata["background_symmetry"]["declared_points_mm"] == [[0, 40], [80, 40]]
    assert diagnostic.region_metadata["background_symmetry"]["points_mm"] == [[0, 40], [60, 40]]
    assert diagnostic.region_metadata["background_variant_scope"] == "initial_tangent_diagnostic_only"


@pytest.mark.parametrize("section,key,value", [
    ("units", "length", "m"), ("units", "force", "source_force"),
    ("material", "formulation", "plane_stress"), ("material", "E_MPa", 100),
    ("material", "nu", True), ("third_medium", "gamma", 0),
    ("regularization", "alpha", 1e-5), ("regularization", "length_mm", 1),
    ("input", "control", "nodal_displacement"), ("input", "target_mm", 0),
    ("input", "target_mm", float("nan")), ("output", "spring_N_per_mm", 10),
    ("qualification_criteria", "max_design_volume_fraction", 0.35),
])
def test_unsupported_tasks_fail_before_geometry_access(section, key, value):
    configured = task()
    configured[section][key] = value
    with pytest.raises(ProjectError):
        build_project("missing_geometry_is_not_opened.json", configured)


def test_positive_short_target_accepted_without_modifying_main_task(tmp_path):
    configured = task()
    configured["input"]["target_mm"] = 1e-5
    project = build_project(candidate(tmp_path), configured)
    assert project.task["input"]["target_mm"] == 1e-5


def test_unknown_task_fields_and_unapproved_diagnostic_rejected():
    configured = task()
    configured["kin"] = 10
    with pytest.raises(ProjectError, match="unsupported fields"):
        build_project("missing.json", configured)
    configured = task()
    configured["diagnostic_variant"] = BACKGROUND_DIAGNOSTIC
    with pytest.raises(ProjectError, match="only defined for the gripper"):
        build_project("missing.json", configured)


def test_input_fixed_dof_conflict_is_not_silently_reweighted(tmp_path):
    def move_input(metadata):
        metadata["region_tags"]["input"]["points_mm"] = [[0, 0], [0, 2]]
    path = candidate(tmp_path, change_metadata=move_input)
    with pytest.raises(ProjectError) as error:
        build_project(path, task())
    assert error.value.code == "constraint_conflict"


def test_detached_port_node_rejected_without_dropping_its_weight(tmp_path):
    def detach_first_input_node(solid):
        solid[37:39, 0] = 0
    path = candidate(tmp_path, change_solid=detach_first_input_node)
    with pytest.raises(ProjectError, match="Every original input port node"):
        build_project(path, task())


def test_geometry_thickness_and_family_must_match_pilot(tmp_path):
    path = candidate(tmp_path, change_metadata=lambda metadata: metadata.update(thickness_mm=1.0))
    with pytest.raises(ProjectError, match="20 mm thick"):
        build_project(path, task())
    path = candidate(tmp_path / "family", "inverter")
    with pytest.raises(ProjectError, match="Task family"):
        build_project(path, task("gripper"))
