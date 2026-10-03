"""Independent replay of three saved construction TEST models; no responses.

Only HF data reading is shared. Native indices, boundary unions, plane-strain
parameters and the nine-point tensor Simpson Q1 operators are derived here.
This checker never imports native_project, project, TMCModel or the kernel.
"""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
sys.path.insert(0, str(REPO / "hf_repo/src"))
from hf_eval.data import canonical_hash, load_geometry

INVENTORY_SHA = "6d47cdee2afb40068cf91706c2e68e13b872c32d9d7cad03be4664f07f3aca1f"
PINS = {
    "inverter_canonical": (
        "23adf44ea8164fb103998ab97363747540a11ef7bb589ae81aa2fde23ff57eee",
        "1911362efaa5b6c5104af0cecf95310f262b129f3e0cd2a1c648cf550b756132",
        "2e2bb3466ade06f920dfbb92577ccbe46106acec430837bac8e1a30b8083527a",
        "5d488f275515b77e37c07ef57c3ebda71f706ba498cec20f72261400408bfe65"),
    "gripper_canonical": (
        "8d831fd3f1a034a3cd1948415c3f9758a2c6b94507973b7dc8c409266fec78e6",
        "f7b23e8d16aedb0ebb5b7dc3954b7b59a80f99b6d3859046aa16904a610d6282",
        "d4e82cfd629e37f7d0c85aed672ab5df228314147cf5db59aeabb279cee5d91d",
        "67d21a63898b2f31962f3e930bc2cb17e36b2813671dfa413c85c7834e6c9b63"),
    "gripper_native_fine": (
        "dbab7567c98e18174d198318f025184b3545c3681c060fa77d9435122bb0f32c",
        "92ff8918ae7502c3f8bfb99398b654ea1521549e7ff3ce0e8b24a9b4fa720d21",
        "62dd40a9ed8a41a6a2deb55927982c7f409d63bfedbf96079b2ee032e816da8d",
        "3638394a88ab8def0324c1e1fc58c7c6d63963296cc5d47c696aefbdac8fd78b"),
}
MASKS = ("solid", "design", "passive_solid", "passive_void")
LEGACY_SHA = {
    "project.py": "593c7c8ad8ce8da45306d29f87d0aa6ac080d4f551a251e505060db5f6dacabd",
    "tmc.py": "b2a1d4d449886667821e805cddeaf7bab3073d2d7a6cc1baeddfed05f407f025",
    "tmc_kernel.py": "dba45df22b36e2bf03bec4589d35ab6a37d151bf0c7d89b01fe6763964dfefd0",
}


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def closed_nodes(points, grid):
    ny, nx = grid["shape_yx"]
    logical = (np.asarray(points) - grid["origin_mm"]) / grid["cell_size_mm"]
    indices = np.rint(logical).astype(np.int64)
    np.testing.assert_array_equal(logical, indices)
    assert np.all(indices >= 0) and np.all(indices <= [nx, ny])
    varying, = np.flatnonzero(indices[0] != indices[1])
    step = 1 if indices[1, varying] > indices[0, varying] else -1
    values = range(int(indices[0, varying]), int(indices[1, varying]) + step, step)
    return np.array([indices[0, 1] * (nx + 1) + v if varying == 0
                     else v * (nx + 1) + indices[0, 0] for v in values], dtype=np.int64)


def dofs(nodes, components):
    return np.array(sorted({2 * int(n) + c for n in nodes for c in components}), dtype=np.int64)


def q1_operators(hx, hy, thickness):
    """Differentiate N_a=(1+s_x*xi)*(1+s_y*eta)/4 analytically."""
    signs = ((-1, -1), (1, -1), (1, 1), (-1, 1))
    points = np.array([(xi, eta) for xi in (-1., 0., 1.) for eta in (-1., 0., 1.)])
    grad = np.array([[(sx * (1 + sy * eta) / (2 * hx),
                       sy * (1 + sx * xi) / (2 * hy)) for sx, sy in signs]
                     for xi, eta in points], dtype=np.float64)
    hessian = np.zeros((4, 2, 2), dtype=np.float64)
    for a, (sx, sy) in enumerate(signs):
        hessian[a, 0, 1] = hessian[a, 1, 0] = sx * sy / (hx * hy)
    weights = np.array([a * b * (hx * hy * thickness / 36)
                        for a in (1., 4., 1.) for b in (1., 4., 1.)])
    return dict(grad=grad, hessian=hessian, weights=weights, points=points)


def native_arrays(geometry):
    grid, tags = geometry.grid, geometry.metadata["region_tags"]
    ny, nx = grid["shape_yx"]
    hx, hy = grid["cell_size_mm"]
    x0, y0 = grid["origin_mm"]
    coordinates = np.array([(x0 + i * hx, y0 + j * hy)
                            for j in range(ny + 1) for i in range(nx + 1)], dtype=np.float64)
    connectivity = np.array([(j * (nx + 1) + i, j * (nx + 1) + i + 1,
                              (j + 1) * (nx + 1) + i + 1, (j + 1) * (nx + 1) + i)
                             for j in range(ny) for i in range(nx)], dtype=np.int64)
    incident = np.zeros((ny + 1, nx + 1), dtype=bool)
    for j, i in ((0, 0), (0, 1), (1, 0), (1, 1)):
        incident[j:j + ny, i:i + nx] |= geometry.solid.astype(bool)
    native = dict(coordinates_mm=coordinates, connectivity=connectivity,
                  solid_incident=incident.ravel().astype(np.uint8), **geometry.arrays)
    for name in ("support", "symmetry"):
        nodes = closed_nodes(tags[name]["points_mm"], grid)
        native[name + "_nodes"] = nodes
        native[name + "_solid_nodes"] = nodes[incident.ravel()[nodes]]
    for name in ("input", "output"):
        nodes = closed_nodes(tags[name]["points_mm"], grid)
        weights = np.ones(len(nodes)) / (len(nodes) - 1)
        weights[[0, -1]] *= .5
        vector = np.zeros((len(coordinates), 2))
        vector[nodes] = weights[:, None] * np.asarray(tags[name]["direction"])
        native.update({name + "_nodes": nodes, name + "_weights": weights,
                       name + "_vector": vector.ravel()})
    source = geometry.metadata["provenance"]["lf_v2"]["descriptor"]["regions_mm"]["symmetry_background"]
    nodes = np.empty(0, dtype=np.int64)
    if source is not None:
        assert source["interval"] == "open_closed" and source["kind"] == "complement_on_line"
        assert source["line"] == {"axis": "y", "value_mm": 40.}
        nodes = np.flatnonzero((coordinates[:, 1] == 40.) & (coordinates[:, 0] > 60.)
                              & (coordinates[:, 0] <= 80.)).astype(np.int64)
    native["background_source_nodes"] = nodes
    native["background_source_solid_nodes"] = nodes[incident.ravel()[nodes]]
    assert len(native) == 19
    return native


def expected_model(geometry, task):
    native = native_arrays(geometry)
    assert task["schema_version"] == "hf-native-project-task-1.0"
    assert task["purpose"] == "construction_test_only" and task["task_id"].startswith("TEST_")
    assert task["geometry"] == {"geometry_id": geometry.geometry_id,
                                "descriptor_sha256": geometry.metadata["descriptor_sha256"]}
    assert task["analysis_grid"] == {"policy": "native"}
    assert task["case_family"] == geometry.metadata["case_family"]
    assert task["material"] == {"E_MPa": 1., "nu": .3, "formulation": "plane_strain"}
    assert task["third_medium"] == {"gamma": 1e-6}
    assert task["regularization"] == {"alpha": 1e-6, "length_mm": 80.}
    assert task["input"] == {"tag": "input", "control": "average_displacement", "target_mm": .025}
    assert task["output"] == {"tag": "output", "spring_N_per_mm": 0.}
    assert task["input_auxiliary_spring_N_per_mm"] == 0. and task["workpiece"] is None
    assert task["reference_state"] == "undeformed" and task["support_selection"] == "solid_incident_nodes_only"
    assert task["constraints"] == [{"tag": "support", "components": [0, 1]},
                                  {"tag": "symmetry", "components": [1]}]
    assert task["background_symmetry"] == {"points_mm": [[0., 40.], [80., 40.]], "components": [1]}
    assert task["units"] == {"length": "mm", "force": "N", "stress": "MPa", "energy": "N mm"}
    assert all(v is None for v in task["qualification_criteria"].values())
    groups = dict(support=dofs(native["support_solid_nodes"], [0, 1]),
                  entity_symmetry=dofs(native["symmetry_solid_nodes"], [1]),
                  background_symmetry=dofs(closed_nodes(task["background_symmetry"]["points_mm"], geometry.grid), [1]))
    fixed = np.array(sorted(set().union(*(set(a.tolist()) for a in groups.values()))), dtype=np.int64)
    ndof = 2 * len(native["coordinates_mm"])
    fixed_set = set(fixed.tolist())
    free = np.array([d for d in range(ndof) if d not in fixed_set], dtype=np.int64)
    solid_nodes = np.flatnonzero(native["solid_incident"]).astype(np.int64)
    solid = geometry.solid.ravel().astype(bool)
    E, nu = task["material"]["E_MPa"], task["material"]["nu"]
    lam = E * nu / ((1 + nu) * (1 - 2 * nu))
    mu = E / (2 * (1 + nu))
    kappa = E / (3 * (1 - 2 * nu))
    alpha, length = task["regularization"]["alpha"], task["regularization"]["length_mm"]
    kr = alpha * length**2 * (kappa + 4 * mu / 3)
    gamma = np.where(solid, 1., task["third_medium"]["gamma"])
    hx, hy = geometry.grid["cell_size_mm"]
    thickness = geometry.metadata["thickness_mm"]
    edofs = np.array([[2 * int(n) + component for n in cell for component in (0, 1)]
                     for cell in native["connectivity"]], dtype=np.int64)
    expected = dict(coordinates=native["coordinates_mm"], connectivity=native["connectivity"],
        solid=solid, lam=lam * gamma, mu=mu * gamma, gamma=gamma, edofs=edofs,
        fixed_dofs=fixed, free_dofs=free, solid_nodes=solid_nodes, solid_dofs=dofs(solid_nodes, [0, 1]),
        b_in=native["input_vector"], b_out=native["output_vector"],
        kr=np.array(kr), hx=np.array(hx), hy=np.array(hy), thickness=np.array(thickness), k_out=np.array(0.),
        force_scale_per_length=np.array(E * thickness),
        **q1_operators(hx, hy, thickness))
    assert len(expected) == 23
    assert not np.any(expected["b_in"][fixed]) and not np.any(expected["b_out"][fixed])
    assert np.all(native["solid_incident"][native["input_nodes"]])
    assert np.all(native["solid_incident"][native["output_nodes"]])
    return expected, native, groups


def replay_case(row, production, previous):
    alias, pins = row["alias"], PINS[row["alias"]]
    source, task_file = REPO / row["geometry_file"], REPO / row["task_file"]
    source_npz = source.with_name("geometry.npz")
    assert digest(source) == pins[0] == row["geometry_file_sha256"]
    assert digest(source_npz) == pins[1] == row["geometry_npz_sha256"]
    assert digest(task_file) == pins[3] == row["task_file_sha256"]
    geometry, task = load_geometry(source), read(task_file)
    assert geometry.geometry_id == pins[2] == row["geometry_id"]
    assert geometry.metadata["descriptor_sha256"] == row["geometry_descriptor_sha256"]
    expected, native, groups = expected_model(geometry, task)
    prior = REPO / "lf_data_preparation/native_q1_001/mapped" / alias
    assert digest(prior / "map.json") == previous["map_file_sha256"]
    assert digest(prior / "map.npz") == previous["map_array_sha256"]
    prior_metadata = read(prior / "map.json")
    assert all(prior_metadata[k] is False for k in ("constraints_applied", "material_assigned", "task_created"))
    assert prior_metadata["analysis_grid_policy"] == "not_selected"
    with np.load(prior / "map.npz", allow_pickle=False) as archive:
        assert set(archive.files) == set(native)
        for name, values in native.items():
            np.testing.assert_array_equal(archive[name], values, err_msg=name)
    output = ROOT / "models" / alias
    metadata = read(output / "model.json")
    assert production["status"] == "pass" and production["invocations"] == 1
    assert production["model_descriptor"] == "models/" + alias + "/model.json"
    assert digest(output / "model.json") == production["model_descriptor_sha256"]
    assert digest(output / "model.npz") == production["model_npz_sha256"]
    assert metadata["schema_version"] == "hf-native-project-model-1.0"
    assert metadata["descriptor_sha256"] == canonical_hash({k: v for k, v in metadata.items() if k != "descriptor_sha256"})
    assert metadata["task"] == task and metadata["task_sha256"] == canonical_hash(task) == production["task_sha256"]
    binding = dict(geometry_id=geometry.geometry_id, descriptor_sha256=geometry.metadata["descriptor_sha256"],
        descriptor_file_sha256=pins[0], arrays_sha256=pins[1],
        snapshot=dict(descriptor="source_geometry/geometry.json", arrays="source_geometry/geometry.npz"))
    assert metadata["source_geometry"] == binding and production["geometry_id"] == geometry.geometry_id
    for name in ("grid", "model_extent"):
        assert metadata[name] == geometry.metadata[name]
    assert metadata["units"] == task["units"] and metadata["analysis_grid_policy"] == "native"
    assert metadata["native_geometry_preserved"] is True and metadata["quadrature"] == "tensor_product_9_point_Simpson"
    assert metadata["element_node_order"] == ["BL", "BR", "TR", "TL"]
    assert metadata["dof_order"] == "interleaved ux,uy; dof = 2*node + component"
    assert all(metadata[k] is True for k in ("constraints_applied", "material_assigned", "task_created"))
    assert metadata["response_evaluated"] is False
    assert metadata["stored_input_target_role"] == "task instruction only; not executed by construction"
    assert metadata["source_provenance_path_context"] == "Paths inside the source geometry provenance belong to the original source context; no external LF data are read"
    snapshot = output / binding["snapshot"]["descriptor"]
    assert snapshot.read_bytes() == source.read_bytes()
    assert (output / binding["snapshot"]["arrays"]).read_bytes() == source_npz.read_bytes()
    copied = load_geometry(snapshot)
    assert copied.metadata == geometry.metadata and copied.geometry_id == geometry.geometry_id
    for name in MASKS:
        np.testing.assert_array_equal(copied.arrays[name], geometry.arrays[name], err_msg=name)
    declaration = metadata["arrays"]
    assert declaration["path"] == "model.npz" and digest(output / "model.npz") == declaration["sha256"]
    with np.load(output / "model.npz", allow_pickle=False) as archive:
        assert set(archive.files) == set(expected) == set(declaration["fields"])
        actual = {name: archive[name].copy() for name in archive.files}
    for name, reference in expected.items():
        value = actual[name]
        assert value.dtype == reference.dtype and value.shape == reference.shape, name
        np.testing.assert_array_equal(value, reference, err_msg=name)
        assert declaration["fields"][name] == dict(dtype=value.dtype.name, shape=list(value.shape),
                                                  sha256=sha256(value.tobytes(order="C")).hexdigest())
    regions = metadata["region_metadata"]
    incident = native["solid_incident"].astype(bool)
    for group, tag, components in (("support", "support", [0, 1]), ("entity_symmetry", "symmetry", [1])):
        selected, attached = native[tag + "_nodes"], native[tag + "_solid_nodes"]
        assert regions[group] == dict(tag=tag, points_mm=geometry.metadata["region_tags"][tag]["points_mm"],
            components=components, selection="solid_incident_nodes_only", selected_nodes=selected.tolist(),
            attached_nodes=attached.tolist(), excluded_unattached_nodes=selected[~incident[selected]].tolist(),
            dofs=groups[group].tolist())
    background = closed_nodes(task["background_symmetry"]["points_mm"], geometry.grid)
    assert regions["background_symmetry"] == dict(points_mm=task["background_symmetry"]["points_mm"], components=[1],
        selection="all_full_domain_nodes_on_segment", selected_nodes=background.tolist(),
        solid_incident_nodes=background[incident[background]].tolist(),
        medium_only_nodes=background[~incident[background]].tolist(), dofs=groups["background_symmetry"].tolist())
    assert regions["fixed_dofs"] == actual["fixed_dofs"].tolist()
    assert regions["solid_constraint_dofs"] == sorted(set(groups["support"]) | set(groups["entity_symmetry"]))
    names = list(groups)
    assert regions["intersections"] == {left + "__" + right: sorted(set(groups[left]) & set(groups[right]))
                                       for i, left in enumerate(names) for right in names[i + 1:]}
    counts = dict(cells=len(actual["connectivity"]), nodes=len(actual["coordinates"]), dofs=len(actual["b_in"]),
        solid_cells=int(actual["solid"].sum()), medium_cells=int((~actual["solid"]).sum()),
        solid_incident_nodes=len(actual["solid_nodes"]), fixed_dofs=len(actual["fixed_dofs"]), free_dofs=len(actual["free_dofs"]))
    assert regions["counts"] == counts
    for name, key in (("cells", "cells"), ("nodes", "nodes"), ("dofs", "dofs"), ("fixed_dofs", "fixed_dofs"), ("free_dofs", "free_dofs")):
        assert production[name] == counts[key]
    assert len(actual["fixed_dofs"]) == {"inverter_canonical": 89, "gripper_canonical": 87, "gripper_native_fine": 169}[alias]
    for name, vector_name in (("input", "b_in"), ("output", "b_out")):
        tag = geometry.metadata["region_tags"][name]
        assert regions["ports"][name] == dict(tag=name, points_mm=tag["points_mm"], direction=tag["direction"],
            nodes=native[name + "_nodes"].tolist(), weights=native[name + "_weights"].tolist(),
            averaging=tag["averaging"], nonzero_dofs=np.flatnonzero(actual[vector_name]).tolist())
    source_background = geometry.metadata["provenance"]["lf_v2"]["descriptor"]["regions_mm"]["symmetry_background"]
    assert regions["source_background"] == source_background
    assert regions["source_background_role"] == "provenance only; applied background comes exclusively from task.background_symmetry"
    assert regions["reaction_accounting"] == "Use merged fixed DOFs once; intersecting groups are not separate contact forces"
    assert regions["force_energy_extent"] == "lower_half modeled geometry; no automatic doubling"
    material = metadata["material"]
    E, nu = task["material"]["E_MPa"], task["material"]["nu"]
    assert material == dict(E_MPa=E, nu=nu, formulation="plane_strain", lambda_s_MPa=E * nu / ((1 + nu) * (1 - 2 * nu)),
        mu_s_MPa=E / (2 * (1 + nu)), kappa_s_MPa=E / (3 * (1 - 2 * nu)), thickness_mm=20., third_medium_gamma=1e-6,
        alpha=1e-6, regularization_length_mm=80., kr_MPa_mm2=float(actual["kr"]), kr_material_factor_applied=False, force_scale_per_length=20.)
    assert metadata["qualification"]["criteria"] == task["qualification_criteria"]
    assert metadata["qualification"]["checks"]["design_volume_fraction"]["status"] == "pending"
    assert metadata["qualification"]["checks"]["min_feature"]["status"] == "pending"
    old_model = REPO / row["old_model_file"]
    old_task = REPO / row["old_parameter_task_file"]
    assert digest(old_model) == row["old_model_sha256"] and digest(old_task) == row["old_parameter_task_file_sha256"]
    former = read(old_task)
    for name in ("material", "third_medium", "regularization", "constraints", "support_selection", "background_symmetry", "output", "input_auxiliary_spring_N_per_mm", "workpiece", "reference_state", "units"):
        assert task[name] == former[name], name
    compared = ("coordinates", "connectivity", "solid", "lam", "mu", "kr", "hx", "hy", "thickness", "fixed_dofs",
                "grad", "hessian", "weights", "b_in", "b_out", "k_out", "force_scale_per_length")
    with np.load(old_model, allow_pickle=False) as old:
        if alias != "gripper_native_fine":
            for name in compared:
                assert actual[name].dtype == old[name].dtype and actual[name].shape == old[name].shape, name
                np.testing.assert_array_equal(actual[name], old[name], err_msg=name)
        else:
            assert (counts["cells"], counts["nodes"], counts["dofs"]) == (12800, 13041, 26082)
            np.testing.assert_array_equal(actual["grad"], 2 * old["grad"])
            np.testing.assert_array_equal(actual["hessian"], 4 * old["hessian"])
            np.testing.assert_array_equal(actual["weights"], old["weights"] / 4)
            assert float(actual["kr"]) == float(old["kr"]) and float(actual["force_scale_per_length"]) == 20.
            for name in ("input", "output"):
                np.testing.assert_array_equal(native[name + "_weights"], [.125, .25, .25, .25, .125])
    np.testing.assert_array_equal(actual["grad"].sum(axis=1), np.zeros((9, 2)))
    np.testing.assert_array_equal(actual["hessian"].sum(axis=0), np.zeros((2, 2)))
    corner = actual["coordinates"][actual["connectivity"][0]]
    np.testing.assert_array_equal(np.einsum("aI,qaJ->qIJ", corner, actual["grad"]), np.tile(np.eye(2), (9, 1, 1)))
    np.testing.assert_allclose(actual["weights"].sum(), float(actual["hx"] * actual["hy"] * actual["thickness"]), rtol=5e-16, atol=0.)
    return dict(alias=alias, geometry_id=geometry.geometry_id, task_sha256=metadata["task_sha256"],
        model_descriptor_sha256=digest(output / "model.json"), model_npz_sha256=digest(output / "model.npz"),
        prior_native_fields_exactly_equal=19, model_fields_exactly_equal=23, source_four_masks_changed_cells={name: 0 for name in MASKS},
        counts=counts, fixed_groups={name: values.tolist() for name, values in groups.items()},
        original_model_intrinsic_fields_exactly_equal=17 if alias != "gripper_native_fine" else None,
        fine_operator_scaling_passed=alias == "gripper_native_fine", fine_reference_role=row["old_model_role"] if alias == "gripper_native_fine" else None,
        analytical_Q1_operators_exact=True, rigid_translation_and_affine_gradient_identities=True,
        source_background_is_provenance_only=True, material_and_boundary_construction_only=True, stored_target_executed=False)


def main():
    destination = ROOT / "independent_review.json"
    if destination.exists() and read(destination).get("status") == "pass":
        raise FileExistsError("Successful independent model review is immutable")
    record = dict(schema_version="native-model-independent-review-1.0", created_utc=datetime.now(timezone.utc).isoformat(),
        review_source_sha256=digest(Path(__file__)), scope="Three explicit construction TEST models only; not H2/H3 study decisions or numerical response qualification",
        author_native_project_imports=0, project_imports=0, TMCModel_imports=0, kernel_imports=0,
        LF_imports=0, mechanics_assembly_calls=0, force_calls=0, HP_calls=0, solver_calls=0)
    try:
        inventory_file = ROOT / "input_inventory.json"
        assert digest(inventory_file) == INVENTORY_SHA
        inventory = read(inventory_file)
        assert inventory["baseline_commit"] == "a0b009dfafef7c2dcbb6aa817f9428cd7e9461f5"
        assert [c["alias"] for c in inventory["cases"]] == list(PINS)
        production = read(ROOT / "execution_receipt.json")
        assert production["status"] == "pass" and production["completed_cases"] == 3
        assert production["input_inventory_sha256"] == INVENTORY_SHA
        assert production["sources"]["lf_data_preparation/native_model_001/review_models.py"] == record["review_source_sha256"]
        assert len(production["sources"]) == 13
        for name, pin in production["sources"].items():
            assert digest(REPO / name) == pin == digest(ROOT / "sources" / Path(name).name), name
        for name, pin in production["inputs"].items():
            assert digest(REPO / name) == pin, name
        for name, pin in LEGACY_SHA.items():
            assert digest(REPO / "hf_repo/src/hf_eval" / name) == pin, name
        prior_file = REPO / "lf_data_preparation/native_q1_001/independent_review.json"
        assert digest(prior_file) == "5c49e2cae54a5560515184e5de6a4907437a6655c205697d53eae8b40246c056"
        prior = read(prior_file)
        assert prior["status"] == "pass"
        previous = {c["alias"]: c for c in prior["cases"]}
        produced = {c["alias"]: c for c in production["cases"]}
        assert set(produced) == set(previous) == set(PINS)
        record["cases"] = [replay_case(row, produced[row["alias"]], previous[row["alias"]]) for row in inventory["cases"]]
        assert not any(n.startswith(("hf_eval.native_project", "hf_eval.project", "hf_eval.tmc", "jax", "dmftd")) for n in sys.modules)
        record.update(status="pass", input_inventory_sha256=INVENTORY_SHA,
            execution_receipt_sha256=digest(ROOT / "execution_receipt.json"), prior_native_review_sha256=digest(prior_file),
            sources=production["sources"], inputs=production["inputs"])
    except Exception as error:
        record.update(status="failed_review", failure_type=type(error).__name__, failure=str(error))
        destination.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        raise
    destination.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(dict(status=record["status"], cases=3, model_fields_exactly_equal=23, prior_native_fields_exactly_equal=19)))


if __name__ == "__main__":
    main()
