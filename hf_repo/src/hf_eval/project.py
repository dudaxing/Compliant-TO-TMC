"""HF-3 project geometry adapter in mm, N and MPa; no equilibrium solve.

This explicit pilot interface keeps solid-attached constraints separate from
the full-domain third-medium symmetry condition. It never reads LF spring
metadata or changes geometry authority arrays, qualification, or the TMC kernel.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from numbers import Real
from pathlib import Path

import numpy as np

from .data import Geometry, canonical_hash, load_geometry
from .regions import (
    active_nodes, element_connectivity, node_coordinates, port_vector,
    qualify_geometry, region_nodes,
)
from .tmc import TMCModel


TASK_SCHEMA = "hf-project-task-1.0"
UNITS = {"length": "mm", "force": "N", "stress": "MPa", "energy": "N mm"}
BACKGROUND_DIAGNOSTIC = "gripper_release_background_beyond_entity"


class ProjectError(ValueError):
    """Invalid project task or physical mapping, before any nonlinear solve."""

    def __init__(self, message, *, code="unsupported_configuration"):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class Project:
    geometry: Geometry
    model: TMCModel
    bin: np.ndarray
    bout: np.ndarray
    task: dict
    task_hash: str
    region_metadata: dict
    qualification: dict
    gamma: np.ndarray
    solid_nodes: np.ndarray
    solid_dofs: np.ndarray
    material: dict
    k_out: float

    @property
    def task_sha256(self):
        return self.task_hash


def _require(condition, message, *, code="unsupported_configuration"):
    if not condition:
        raise ProjectError(message, code=code)


def _number(value, name, *, positive=False):
    _require(isinstance(value, Real) and not isinstance(value, (bool, np.bool_)),
             f"{name} must be a real number")
    value = float(value)
    _require(np.isfinite(value) and (not positive or value > 0),
             f"{name} must be finite" + (" and positive" if positive else ""))
    return value


def _object(value, name, required, optional=()):
    _require(isinstance(value, dict), f"{name} must be an object")
    _require(set(required) <= value.keys() and not (value.keys() - set(required) - set(optional)),
             f"{name} has missing or unsupported fields")
    return value


def _readonly(value, dtype):
    result = np.array(value, dtype=dtype, copy=True)
    result.setflags(write=False)
    return result


def _dofs(nodes, components):
    return np.unique((2 * np.asarray(nodes, dtype=np.int64)[:, None]
                      + np.asarray(components, dtype=np.int64)).ravel())


def _validate_task(task_dict):
    required = {
        "schema_version", "task_id", "case_family", "units", "material",
        "third_medium", "regularization", "input", "output", "constraints",
        "support_selection", "background_symmetry", "input_auxiliary_spring_N_per_mm",
        "workpiece", "reference_state", "qualification_criteria",
    }
    _object(task_dict, "task", required,
            {"diagnostic_variant", "purpose", "parameter_origin", "description"})
    task = deepcopy(task_dict)
    _require(task["schema_version"] == TASK_SCHEMA, f"Expected {TASK_SCHEMA}")
    _require(isinstance(task["task_id"], str) and bool(task["task_id"].strip()), "task_id must be nonempty")
    _require(isinstance(task["case_family"], str) and task["case_family"] in {"inverter", "gripper"},
             "Only the two HF-3 project families are supported")
    _require(task["units"] == UNITS, "Project units must be mm, N, MPa and N mm")
    material = _object(task["material"], "material", {"E_MPa", "nu", "formulation"})
    _require(material["formulation"] == "plane_strain", "Only plane strain is supported")
    E = _number(material["E_MPa"], "E_MPa", positive=True)
    nu = _number(material["nu"], "nu")
    _require(E == 1.0 and nu == 0.3, "HF-3 pilot material is frozen at E=1 MPa and nu=0.3")
    medium = _object(task["third_medium"], "third_medium", {"gamma"})
    gamma = _number(medium["gamma"], "third_medium.gamma", positive=True)
    _require(gamma == 1e-6, "HF-3 third-medium factor is frozen at 1e-6")
    regularization = _object(task["regularization"], "regularization", {"alpha", "length_mm"})
    alpha = _number(regularization["alpha"], "regularization.alpha", positive=True)
    length = _number(regularization["length_mm"], "regularization.length_mm", positive=True)
    _require(alpha == 1e-6 and length == 80.0, "HF-3 regularization uses alpha=1e-6 and Lr=80 mm")
    inlet = _object(task["input"], "input", {"tag", "control", "target_mm"})
    _require(inlet["tag"] == "input" and inlet["control"] == "average_displacement",
             "Input must use the reference input tag and average displacement control")
    _number(inlet["target_mm"], "input.target_mm", positive=True)
    outlet = _object(task["output"], "output", {"tag", "spring_N_per_mm"})
    _require(outlet["tag"] == "output", "Output must use the reference output tag")
    kout = _number(outlet["spring_N_per_mm"], "output.spring_N_per_mm")
    auxiliary = _number(task["input_auxiliary_spring_N_per_mm"], "input_auxiliary_spring_N_per_mm")
    _require(kout == auxiliary == 0.0, "The project pilot has free output and no input auxiliary spring")
    _require(task["workpiece"] is None and task["reference_state"] == "undeformed",
             "HF-3 has no workpiece and starts from the undeformed state")
    _require(task["support_selection"] == "solid_incident_nodes_only",
             "Solid constraints must select solid-incident nodes only")
    constraints = task["constraints"]
    _require(isinstance(constraints, list) and len(constraints) == 2, "Declare support and symmetry constraints separately")
    declared = {}
    for constraint in constraints:
        _object(constraint, "constraint", {"tag", "components"})
        tag = constraint["tag"]
        _require(isinstance(tag, str) and tag not in declared, "Constraint tags must be distinct strings")
        components = constraint["components"]
        _require(isinstance(components, list) and all(type(c) is int for c in components),
                 "Constraint components must be integer lists")
        declared[tag] = components
    _require(declared == {"support": [0, 1], "symmetry": [1]}, "Unsupported solid constraint components or tags")
    background = _object(task["background_symmetry"], "background_symmetry", {"points_mm", "components"})
    _require(background["points_mm"] == [[0.0, 40.0], [80.0, 40.0]]
             and background["components"] == [1]
             and all(type(c) is int for c in background["components"]),
             "Declare the complete y=40 mm background uy symmetry line explicitly")
    variant = task.get("diagnostic_variant", "none")
    _require(isinstance(variant, str) and variant in {"none", BACKGROUND_DIAGNOSTIC}, "Unsupported boundary diagnostic variant")
    _require(variant == "none" or task["case_family"] == "gripper", "The background-release diagnostic is only defined for the gripper")
    criteria = _object(task["qualification_criteria"], "qualification_criteria",
                       {"max_design_volume_fraction", "min_feature_mm"})
    _require(all(value is None for value in criteria.values()), "Research qualification thresholds remain pending in this pilot")
    canonical_hash(task)  # Reject non-JSON/nonfinite inert metadata as well.
    return task, E, nu, gamma, alpha, length, kout, variant


def build_project(geometry_file: str | Path, task_dict: dict) -> Project:
    """Map one portable geometry and explicit HF-3 task to a full-domain model.

    ``task_hash`` is ``data.canonical_hash`` of the validated, copied task as
    supplied. ``region_metadata`` is ordinary JSON, including the separate DOF
    sets, their intersections and the merged fixed DOFs. Forces and energy refer
    to the modeled lower half, without automatic doubling. No loads are solved.
    The one gripper boundary variant is marked for initial-tangent diagnosis;
    the runner must not use it for a complete nonlinear pilot path.
    """
    task, E, nu, medium, alpha, length, kout, variant = _validate_task(task_dict)
    geometry = load_geometry(geometry_file)
    _require(geometry.metadata["case_family"] == task["case_family"], "Task family differs from geometry", code="invalid_geometry")
    grid = geometry.grid
    _require(grid["shape_yx"] == [40, 80] and grid["origin_mm"] == [0.0, 0.0]
             and grid["cell_size_mm"] == [1.0, 1.0] and grid["extent_mm"] == [80.0, 40.0]
             and geometry.metadata["thickness_mm"] == 20.0
             and geometry.metadata["model_extent"]["kind"] == "lower_half",
             "HF-3 requires the unchanged native 80 by 40 mm, 1 mm grid, 20 mm thick lower half", code="invalid_geometry")
    coordinates = node_coordinates(geometry)
    connectivity = element_connectivity(geometry)
    attached = active_nodes(geometry)
    tags = geometry.metadata["region_tags"]
    _require({"support", "symmetry", "input", "output"} <= tags.keys(), "Required geometry regions are missing", code="invalid_geometry")
    entity_end = 80.0 if task["case_family"] == "inverter" else 60.0
    _require(tags["symmetry"]["points_mm"] == [[0.0, 40.0], [entity_end, 40.0]],
             "Geometry entity symmetry segment differs from the archived HF-1 meaning", code="invalid_geometry")
    region_metadata = {}
    groups = {}
    for source, tag_name, components in (("support", "support", [0, 1]), ("entity_symmetry", "symmetry", [1])):
        tag = tags[tag_name]
        _require(tag.get("components") == components, f"Geometry {tag_name} components differ from the task", code="invalid_geometry")
        selected = region_nodes(geometry, tag)
        nodes = selected[attached[selected]]
        _require(len(nodes) >= (2 if source == "support" else 1), f"No adequate solid attachment for {tag_name}", code="invalid_geometry")
        dofs = _dofs(nodes, components)
        groups[source] = dofs
        region_metadata[source] = {
            "tag": tag_name, "points_mm": deepcopy(tag["points_mm"]), "components": components,
            "selection": "solid_incident_nodes_only", "selected_nodes": selected.tolist(),
            "attached_nodes": nodes.tolist(), "excluded_unattached_nodes": selected[~attached[selected]].tolist(),
            "dofs": dofs.tolist(),
        }
    background = deepcopy(task["background_symmetry"])
    if variant == BACKGROUND_DIAGNOSTIC:
        background["points_mm"][1][0] = entity_end
    background_nodes = region_nodes(geometry, background)
    groups["background_symmetry"] = _dofs(background_nodes, [1])
    region_metadata["background_symmetry"] = {
        "declared_points_mm": deepcopy(task["background_symmetry"]["points_mm"]),
        "points_mm": background["points_mm"], "components": [1],
        "selection": "all_full_domain_nodes_on_segment", "selected_nodes": background_nodes.tolist(),
        "solid_incident_nodes": background_nodes[attached[background_nodes]].tolist(),
        "medium_only_nodes": background_nodes[~attached[background_nodes]].tolist(),
        "dofs": groups["background_symmetry"].tolist(), "diagnostic_variant": variant,
    }
    fixed = np.unique(np.concatenate(list(groups.values())))
    solid_constraint_dofs = np.union1d(groups["support"], groups["entity_symmetry"])
    ports = {}
    vectors = {}
    for name, direction in (("input", [1.0, 0.0]), ("output", [-1.0, 0.0] if task["case_family"] == "inverter" else [0.0, 1.0])):
        _require(tags[name].get("direction") == direction, f"Unsupported {name} reference direction", code="invalid_geometry")
        vector, nodes, weights = port_vector(geometry, tags[name])
        _require(len(nodes) == 3 and np.array_equal(weights, [0.25, 0.5, 0.25]),
                 "Native project ports must retain all three original trapezoid weights", code="invalid_geometry")
        _require(np.all(attached[nodes]), f"Every original {name} port node must attach to solid", code="invalid_geometry")
        _require(not np.any(vector[fixed]), f"The {name} direction intersects a fixed displacement DOF", code="constraint_conflict")
        vectors[name] = _readonly(vector, float)
        ports[name] = {"tag": name, "points_mm": deepcopy(tags[name]["points_mm"]),
                       "direction": direction, "nodes": nodes.tolist(), "weights": weights.tolist(),
                       "averaging": tags[name]["averaging"], "nonzero_dofs": np.flatnonzero(vector).tolist()}
    solid = geometry.solid.ravel(order="C").astype(bool)
    factors = np.where(solid, 1.0, medium)
    lam = E * nu / ((1.0 + nu) * (1.0 - 2.0 * nu))
    mu = E / (2.0 * (1.0 + nu))
    kappa = E / (3.0 * (1.0 - 2.0 * nu))
    kr = alpha * length**2 * (kappa + 4.0 * mu / 3.0)
    model = TMCModel(coordinates, connectivity, lam * factors, mu * factors, kr,
                     1.0, 1.0, 20.0, solid, fixed)
    intersections = {}
    names = list(groups)
    for i, left in enumerate(names):
        for right in names[i+1:]:
            intersections[left+"__"+right] = np.intersect1d(groups[left], groups[right]).tolist()
    sources = {str(int(dof)): [name for name, dofs in groups.items() if dof in dofs] for dof in fixed}
    active = np.flatnonzero(attached)
    region_metadata.update({
        "units": deepcopy(UNITS), "ports": ports, "intersections": intersections,
        "fixed_dof_sources": sources, "fixed_dofs": fixed.tolist(),
        "solid_constraint_dofs": solid_constraint_dofs.tolist(),
        "counts": {"cells": model.ne, "nodes": len(coordinates), "dofs": model.ndof,
                   "solid_cells": int(solid.sum()), "medium_cells": int((~solid).sum()),
                   "solid_incident_nodes": len(active), "fixed_dofs": len(fixed)},
        "background_variant_scope": "main_pilot" if variant == "none" else "initial_tangent_diagnostic_only",
        "source_full_midline_history": {
            "policy": geometry.metadata.get("processing", {}).get("source_symmetry_policy"),
            "points_mm": deepcopy(geometry.metadata.get("processing", {}).get("source_symmetry_points_mm")),
            "role": "inert provenance; runtime background constraints come only from this task",
        },
        "reaction_accounting": "Use merged fixed DOFs once; intersecting tags do not define separate contact forces",
        "force_energy_extent": "modeled lower half; no automatic doubling",
    })
    material_metadata = {"E_MPa": E, "nu": nu, "formulation": "plane_strain", "lambda_s_MPa": lam,
                         "mu_s_MPa": mu, "kappa_s_MPa": kappa, "thickness_mm": 20.0,
                         "third_medium_gamma": medium, "alpha": alpha, "regularization_length_mm": length,
                         "kr_MPa_mm2": kr, "kr_material_factor_applied": False}
    return Project(geometry, model, vectors["input"], vectors["output"], task, canonical_hash(task),
                   region_metadata, qualify_geometry(geometry, task["qualification_criteria"]),
                   _readonly(factors, float), _readonly(active, np.int64),
                   _readonly(_dofs(active, [0, 1]), np.int64), material_metadata, kout)
