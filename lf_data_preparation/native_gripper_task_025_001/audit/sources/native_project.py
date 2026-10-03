"""Explicit native-grid project construction and portable model storage.

Construction prepares Q1 reference operators, material arrays and displacement
sets only. It does not evaluate forces, assemble a tangent or solve the stored
input target. Source LF background metadata never supplies applied constraints.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path

import numpy as np

from .data import canonical_hash
from .native_map import prepare_native_geometry
from .project import Project, UNITS, _dofs, _number, _object, _readonly, _require
from .regions import qualify_geometry, region_nodes
from .tmc import TMCModel


TASK_SCHEMA = "hf-native-project-task-1.0"
MODEL_SCHEMA = "hf-native-project-model-1.0"


def _validate_task(task_dict):
    _require(isinstance(task_dict, dict)
             and task_dict.get("analysis_grid") == {"policy": "native"},
             "analysis_grid policy must be explicitly native")
    required = {
        "schema_version", "task_id", "case_family", "units", "geometry", "analysis_grid",
        "material", "third_medium", "regularization", "input", "output", "constraints",
        "support_selection", "background_symmetry", "input_auxiliary_spring_N_per_mm",
        "workpiece", "reference_state", "qualification_criteria",
    }
    _object(task_dict, "task", required, {"purpose", "parameter_origin", "description"})
    task = deepcopy(task_dict)
    _require(task["schema_version"] == TASK_SCHEMA, f"Expected {TASK_SCHEMA}")
    _require(isinstance(task["task_id"], str) and bool(task["task_id"].strip()), "task_id must be nonempty")
    _require(isinstance(task["case_family"], str) and task["case_family"] in {"inverter", "gripper"},
             "Unsupported native port profile")
    _require(task["units"] == UNITS, "Project units must be mm, N, MPa and N mm")
    binding = _object(task["geometry"], "geometry", {"geometry_id", "descriptor_sha256"})
    _require(all(isinstance(value, str) and len(value) == 64
                 and all(c in "0123456789abcdef" for c in value) for value in binding.values()),
             "geometry must bind geometry_id and descriptor_sha256 SHA256 strings")
    material = _object(task["material"], "material", {"E_MPa", "nu", "formulation"})
    _require(material["formulation"] == "plane_strain", "Only plane strain is supported")
    E = _number(material["E_MPa"], "E_MPa", positive=True)
    nu = _number(material["nu"], "nu")
    _require(0 <= nu < 0.5, "nu must satisfy 0 <= nu < 0.5")
    medium = _object(task["third_medium"], "third_medium", {"gamma"})
    gamma = _number(medium["gamma"], "third_medium.gamma", positive=True)
    _require(gamma <= 1, "third_medium.gamma must satisfy 0 < gamma <= 1")
    regularization = _object(task["regularization"], "regularization", {"alpha", "length_mm"})
    alpha = _number(regularization["alpha"], "regularization.alpha")
    _require(alpha >= 0, "regularization.alpha must be nonnegative")
    length = _number(regularization["length_mm"], "regularization.length_mm", positive=True)
    inlet = _object(task["input"], "input", {"tag", "control", "target_mm"})
    _require(inlet["tag"] == "input" and inlet["control"] == "average_displacement",
             "Input must use the input tag and average displacement control")
    _number(inlet["target_mm"], "input.target_mm", positive=True)
    outlet = _object(task["output"], "output", {"tag", "spring_N_per_mm"})
    _require(outlet["tag"] == "output", "Output must use the output tag")
    kout = _number(outlet["spring_N_per_mm"], "output.spring_N_per_mm")
    auxiliary = _number(task["input_auxiliary_spring_N_per_mm"], "input_auxiliary_spring_N_per_mm")
    _require(kout == auxiliary == 0, "Native preparation supports free output and no input auxiliary spring")
    _require(task["workpiece"] is None and task["reference_state"] == "undeformed",
             "Native preparation requires no workpiece and an undeformed reference")
    _require(task["support_selection"] == "solid_incident_nodes_only",
             "Solid constraints must select solid-incident nodes only")
    constraints = task["constraints"]
    _require(isinstance(constraints, list) and len(constraints) == 2,
             "Declare support and symmetry constraints separately")
    declared = {}
    for constraint in constraints:
        _object(constraint, "constraint", {"tag", "components"})
        tag, components = constraint["tag"], constraint["components"]
        _require(isinstance(tag, str) and tag not in declared, "Constraint tags must be distinct strings")
        _require(isinstance(components, list) and all(type(c) is int for c in components),
                 "Constraint components must be integer lists")
        declared[tag] = components
    _require(declared == {"support": [0, 1], "symmetry": [1]},
             "Unsupported solid constraint components or tags")
    background = task["background_symmetry"]
    if background is not None:
        _object(background, "background_symmetry", {"points_mm", "components"})
        _require(background["components"] == [1] and all(type(c) is int for c in background["components"]),
                 "background_symmetry components must be [1]")
        points = background["points_mm"]
        _require(isinstance(points, list) and len(points) == 2
                 and all(isinstance(p, list) and len(p) == 2 for p in points),
                 "background_symmetry requires two points_mm")
        for point in points:
            for value in point:
                _number(value, "background_symmetry.points_mm")
    criteria = _object(task["qualification_criteria"], "qualification_criteria",
                       {"max_design_volume_fraction", "min_feature_mm"})
    _require(all(value is None for value in criteria.values()), "Research qualification thresholds remain pending")
    canonical_hash(task)
    return task, E, nu, gamma, alpha, length, kout


def build_native_project(geometry_file, task_dict: dict) -> Project:
    """Construct a model on the explicitly selected, unchanged native HF grid.

    ``case_family`` declares the supported port direction profile. Geometry ID
    binds the four masks and physical grid; descriptor SHA also binds regions
    and provenance. Material regularization length stays in physical mm across
    grids. All quantities refer to the modeled extent without half-model doubling.
    """
    task, E, nu, medium, alpha, length, kout = _validate_task(task_dict)
    mapping = prepare_native_geometry(geometry_file)
    geometry, arrays = mapping.geometry, mapping.arrays
    _require(task["geometry"] == dict(geometry_id=geometry.geometry_id,
                                      descriptor_sha256=geometry.metadata["descriptor_sha256"]),
             "Task geometry binding differs from source geometry", code="invalid_geometry")
    _require(geometry.metadata["case_family"] == task["case_family"],
             "Task family differs from geometry", code="invalid_geometry")
    tags = geometry.metadata["region_tags"]
    _require("symmetry" in tags, "The entity symmetry tag is required", code="invalid_geometry")
    incident = arrays["solid_incident"].astype(bool)
    groups, regions = {}, {}
    for source, tag_name, components in (("support", "support", [0, 1]), ("entity_symmetry", "symmetry", [1])):
        _require(tags[tag_name].get("components") == components,
                 f"Geometry {tag_name} components differ from task", code="invalid_geometry")
        selected, nodes = arrays[tag_name + "_nodes"], arrays[tag_name + "_solid_nodes"]
        _require(len(nodes) >= (2 if source == "support" else 1),
                 f"No adequate solid attachment for {tag_name}", code="invalid_geometry")
        groups[source] = _dofs(nodes, components)
        regions[source] = dict(tag=tag_name, points_mm=deepcopy(tags[tag_name]["points_mm"]),
            components=components, selection="solid_incident_nodes_only", selected_nodes=selected.tolist(),
            attached_nodes=nodes.tolist(), excluded_unattached_nodes=selected[~incident[selected]].tolist(),
            dofs=groups[source].tolist())
    background = task["background_symmetry"]
    background_nodes = (region_nodes(geometry, background) if background is not None
                        else np.empty(0, dtype=np.int64))
    groups["background_symmetry"] = _dofs(background_nodes, [1])
    regions["background_symmetry"] = dict(points_mm=deepcopy(background["points_mm"]) if background else None,
        components=[1], selection="all_full_domain_nodes_on_segment" if background else "disabled",
        selected_nodes=background_nodes.tolist(), solid_incident_nodes=background_nodes[incident[background_nodes]].tolist(),
        medium_only_nodes=background_nodes[~incident[background_nodes]].tolist(), dofs=groups["background_symmetry"].tolist())
    fixed = np.unique(np.concatenate(list(groups.values())))
    ports, vectors = {}, {}
    for name, direction in (("input", [1.0, 0.0]),
                            ("output", [-1.0, 0.0] if task["case_family"] == "inverter" else [0.0, 1.0])):
        _require(tags[name].get("direction") == direction,
                 f"Unsupported {name} reference direction", code="invalid_geometry")
        vector, nodes, weights = (arrays[name + suffix] for suffix in ("_vector", "_nodes", "_weights"))
        _require(np.all(incident[nodes]), f"Every original {name} port node must attach to solid", code="invalid_geometry")
        _require(not np.any(vector[fixed]), f"The {name} direction intersects a fixed displacement DOF", code="constraint_conflict")
        vectors[name] = vector
        ports[name] = dict(tag=name, points_mm=deepcopy(tags[name]["points_mm"]), direction=direction,
            nodes=nodes.tolist(), weights=weights.tolist(), averaging=tags[name]["averaging"],
            nonzero_dofs=np.flatnonzero(vector).tolist())
    solid = geometry.solid.ravel(order="C").astype(bool)
    factors = np.where(solid, 1.0, medium)
    lam = E * nu / ((1 + nu) * (1 - 2 * nu))
    mu = E / (2 * (1 + nu))
    kappa = E / (3 * (1 - 2 * nu))
    kr = alpha * length**2 * (kappa + 4 * mu / 3)
    hx, hy = geometry.grid["cell_size_mm"]
    thickness = geometry.metadata["thickness_mm"]
    model = TMCModel(arrays["coordinates_mm"], arrays["connectivity"], lam * factors,
                     mu * factors, kr, hx, hy, thickness, solid, fixed)
    active = np.flatnonzero(incident)
    names = list(groups)
    source = dict(geometry_id=geometry.geometry_id, descriptor_sha256=geometry.metadata["descriptor_sha256"],
        descriptor_file_sha256=mapping.metadata["source_geometry_file_sha256"],
        arrays_sha256=mapping.metadata["source_geometry_npz_sha256"],
        snapshot=dict(descriptor="source_geometry/geometry.json", arrays="source_geometry/"+geometry.metadata["arrays"]["path"]))
    regions.update(units=deepcopy(UNITS), ports=ports, fixed_dofs=fixed.tolist(),
        solid_constraint_dofs=np.union1d(groups["support"], groups["entity_symmetry"]).tolist(),
        intersections={left+"__"+right: np.intersect1d(groups[left], groups[right]).tolist()
                       for i, left in enumerate(names) for right in names[i+1:]},
        counts=dict(cells=model.ne, nodes=len(model.coordinates), dofs=model.ndof,
                    solid_cells=int(solid.sum()), medium_cells=int((~solid).sum()),
                    solid_incident_nodes=len(active), fixed_dofs=len(fixed), free_dofs=len(model.free)),
        source_geometry=source, source_background=deepcopy(mapping.metadata["background_source"]),
        source_background_role="provenance only; applied background comes exclusively from task.background_symmetry",
        reaction_accounting="Use merged fixed DOFs once; intersecting groups are not separate contact forces",
        force_energy_extent=geometry.metadata["model_extent"]["kind"]+" modeled geometry; no automatic doubling")
    material = dict(E_MPa=E, nu=nu, formulation="plane_strain", lambda_s_MPa=lam, mu_s_MPa=mu,
        kappa_s_MPa=kappa, thickness_mm=thickness, third_medium_gamma=medium, alpha=alpha,
        regularization_length_mm=length, kr_MPa_mm2=kr, kr_material_factor_applied=False,
        force_scale_per_length=E * thickness)
    return Project(geometry, model, vectors["input"], vectors["output"], task, canonical_hash(task), regions,
                   qualify_geometry(geometry, task["qualification_criteria"]), _readonly(factors, float),
                   _readonly(active, np.int64), _readonly(_dofs(active, [0, 1]), np.int64), material, kout)


def write_native_project(project: Project, output_directory) -> Path:
    """Save a new ordinary model package and a byte-exact, loadable HF source."""
    source = project.region_metadata["source_geometry"]
    descriptor_bytes = project.geometry.path.read_bytes()
    array_name = project.geometry.metadata["arrays"]["path"]
    array_bytes = project.geometry.path.with_name(array_name).read_bytes()
    _require(sha256(descriptor_bytes).hexdigest() == source["descriptor_file_sha256"],
             "Source geometry descriptor changed after construction", code="invalid_geometry")
    _require(sha256(array_bytes).hexdigest() == source["arrays_sha256"],
             "Source geometry NPZ changed after construction", code="invalid_geometry")
    model = project.model
    arrays = dict(coordinates=model.coordinates, connectivity=model.connectivity, solid=model.solid,
        lam=model.lam, mu=model.mu, gamma=project.gamma, edofs=model.edofs, fixed_dofs=model.fixed_dofs,
        free_dofs=model.free, solid_nodes=project.solid_nodes, solid_dofs=project.solid_dofs,
        b_in=project.bin, b_out=project.bout, **model.ops)
    arrays.update({name: np.asarray(value, dtype=np.float64) for name, value in
                   dict(kr=model.kr, hx=model.hx, hy=model.hy, thickness=model.thickness, k_out=project.k_out,
                        force_scale_per_length=project.material["force_scale_per_length"]).items()})
    buffer = BytesIO()
    np.savez_compressed(buffer, **arrays)
    payload = buffer.getvalue()
    regions = deepcopy(project.region_metadata)
    regions.pop("source_geometry")
    metadata = dict(schema_version=MODEL_SCHEMA, task=deepcopy(project.task), task_sha256=project.task_hash,
        source_geometry=deepcopy(source), grid=deepcopy(project.geometry.grid),
        model_extent=deepcopy(project.geometry.metadata["model_extent"]), units=deepcopy(UNITS),
        analysis_grid_policy="native", native_geometry_preserved=True, element_node_order=["BL", "BR", "TR", "TL"],
        dof_order="interleaved ux,uy; dof = 2*node + component", quadrature="tensor_product_9_point_Simpson",
        material=deepcopy(project.material), region_metadata=regions, qualification=deepcopy(project.qualification),
        constraints_applied=True, material_assigned=True, task_created=True, response_evaluated=False,
        stored_input_target_role="task instruction only; not executed by construction",
        source_provenance_path_context="Paths inside the source geometry provenance belong to the original source context; no external LF data are read",
        arrays=dict(path="model.npz", sha256=sha256(payload).hexdigest(), fields={
            name: dict(dtype=array.dtype.name, shape=list(array.shape), sha256=sha256(array.tobytes(order="C")).hexdigest())
            for name, array in arrays.items()}))
    metadata["descriptor_sha256"] = canonical_hash(metadata)
    text = json.dumps(metadata, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=False)
    snapshot = output / "source_geometry"
    snapshot.mkdir()
    (snapshot / "geometry.json").write_bytes(descriptor_bytes)
    (snapshot / array_name).write_bytes(array_bytes)
    (output / "model.npz").write_bytes(payload)
    (output / "model.json").write_text(text, encoding="utf-8")
    return (output / "model.json").resolve()
