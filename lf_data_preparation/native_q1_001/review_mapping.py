"""Independent native Q1 preparation replay; geometry and port algebra only.

This checker imports neither the mapping author, LF, project nor TMC. Native
coordinates, counterclockwise cells, incidence and regions are derived here.
"""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
PREVIOUS = REPO / "lf_data_preparation/v2_adapter_001"
sys.path.insert(0, str(REPO / "hf_repo/src"))
from hf_eval.data import canonical_hash, load_geometry

PINS = {
    "inverter_canonical": (
        "23adf44ea8164fb103998ab97363747540a11ef7bb589ae81aa2fde23ff57eee",
        "1911362efaa5b6c5104af0cecf95310f262b129f3e0cd2a1c648cf550b756132",
        "2e2bb3466ade06f920dfbb92577ccbe46106acec430837bac8e1a30b8083527a"),
    "gripper_canonical": (
        "8d831fd3f1a034a3cd1948415c3f9758a2c6b94507973b7dc8c409266fec78e6",
        "f7b23e8d16aedb0ebb5b7dc3954b7b59a80f99b6d3859046aa16904a610d6282",
        "d4e82cfd629e37f7d0c85aed672ab5df228314147cf5db59aeabb279cee5d91d"),
    "gripper_native_fine": (
        "dbab7567c98e18174d198318f025184b3545c3681c060fa77d9435122bb0f32c",
        "92ff8918ae7502c3f8bfb99398b654ea1521549e7ff3ce0e8b24a9b4fa720d21",
        "62dd40a9ed8a41a6a2deb55927982c7f409d63bfedbf96079b2ee032e816da8d"),
}
MASKS = ("solid", "design", "passive_solid", "passive_void")
REGIONS = ("support_nodes", "support_solid_nodes", "symmetry_nodes", "symmetry_solid_nodes",
           "input_nodes", "output_nodes", "background_source_nodes", "background_source_solid_nodes")
LEGACY_PROJECT_SHA = "593c7c8ad8ce8da45306d29f87d0aa6ac080d4f551a251e505060db5f6dacabd"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def closed_nodes(points, grid):
    """Endpoint indices from physical coordinates; both endpoints included."""
    ny, nx = grid["shape_yx"]
    logical = (np.asarray(points) - grid["origin_mm"]) / grid["cell_size_mm"]
    indices = np.rint(logical).astype(np.int64)
    np.testing.assert_array_equal(logical, indices)
    assert np.all(indices >= 0) and np.all(indices <= [nx, ny])
    changed = np.flatnonzero(indices[0] != indices[1])
    assert len(changed) == 1
    varying = changed[0]
    step = 1 if indices[1, varying] > indices[0, varying] else -1
    values = np.arange(indices[0, varying], indices[1, varying] + step, step, dtype=np.int64)
    return (indices[0, 1] * (nx + 1) + values if varying == 0
            else values * (nx + 1) + indices[0, 0])


def derive(geometry):
    grid, tags = geometry.grid, geometry.metadata["region_tags"]
    ny, nx = grid["shape_yx"]
    x0, y0 = grid["origin_mm"]
    hx, hy = grid["cell_size_mm"]
    coordinates = np.array([(x0 + i * hx, y0 + j * hy)
                            for j in range(ny + 1) for i in range(nx + 1)], dtype=np.float64)
    connectivity = np.array([(j * (nx + 1) + i, j * (nx + 1) + i + 1,
                              (j + 1) * (nx + 1) + i + 1, (j + 1) * (nx + 1) + i)
                             for j in range(ny) for i in range(nx)], dtype=np.int64)
    incident = np.zeros((ny + 1, nx + 1), dtype=bool)
    for j, i in ((0, 0), (0, 1), (1, 0), (1, 1)):
        incident[j:j + ny, i:i + nx] |= geometry.solid.astype(bool)
    expected = dict(coordinates_mm=coordinates, connectivity=connectivity,
                    solid_incident=incident.ravel().astype(np.uint8), **geometry.arrays)
    for prefix, tag_name in (("support", "support"), ("symmetry", "symmetry")):
        selected = closed_nodes(tags[tag_name]["points_mm"], grid)
        expected[prefix + "_nodes"] = selected
        expected[prefix + "_solid_nodes"] = selected[incident.ravel()[selected]]
    for name in ("input", "output"):
        tag = tags[name]
        selected = closed_nodes(tag["points_mm"], grid)
        weights = np.ones(len(selected), dtype=np.float64) / (len(selected) - 1)
        weights[[0, -1]] *= .5  # Uniform reference arclength on this native grid.
        vector = np.zeros(2 * len(coordinates), dtype=np.float64).reshape(-1, 2)
        vector[selected] = weights[:, None] * np.asarray(tag["direction"])
        expected.update({name + "_nodes": selected, name + "_weights": weights,
                         name + "_vector": vector.ravel()})
    background = geometry.metadata["provenance"]["lf_v2"]["descriptor"]["regions_mm"]["symmetry_background"]
    selected = np.array([], dtype=np.int64)
    if background is not None:
        assert background["kind"] == "complement_on_line" and background["interval"] == "open_closed"
        assert background["line"] == {"axis": "y", "value_mm": 40.}
        assert background["start_exclusive_mm"] == 60. and background["end_inclusive_mm"] == 80.
        selected = np.flatnonzero((coordinates[:, 1] == background["line"]["value_mm"])
                    & (coordinates[:, 0] > background["start_exclusive_mm"])
                    & (coordinates[:, 0] <= background["end_inclusive_mm"])).astype(np.int64)
        assert not np.any(coordinates[selected, 0] == 60.)
        assert len(np.intersect1d(selected, expected["symmetry_nodes"])) == 0
    expected["background_source_nodes"] = selected
    expected["background_source_solid_nodes"] = selected[incident.ravel()[selected]]
    np.testing.assert_array_equal(np.union1d(selected, expected["symmetry_nodes"]),
                                 ny * (nx + 1) + np.arange(nx + 1))
    return expected, background


def replay_case(alias, pins, previous, production):
    source = PREVIOUS / "converted" / alias / "geometry.json"
    source_npz = source.with_name("geometry.npz")
    assert digest(source) == pins[0] == previous["descriptor_sha256"]
    assert digest(source_npz) == pins[1] == previous["array_sha256"]
    assert previous["status"] == "pass" and previous["invocations"] == 1
    geometry = load_geometry(source)
    assert geometry.geometry_id == pins[2] == previous["HF_geometry_id"]
    expected, background = derive(geometry)
    output = ROOT / "mapped" / alias
    metadata = read(output / "map.json")
    assert production["status"] == "pass" and production["invocations"] == 1
    assert production["map_descriptor"] == "mapped/" + alias + "/map.json"
    assert digest(output / "map.json") == production["descriptor_sha256"]
    assert digest(output / "map.npz") == production["array_sha256"]
    assert production["HF_geometry_id"] == geometry.geometry_id
    assert metadata["schema_version"] == "hf-native-geometry-map-1.0"
    assert metadata["descriptor_sha256"] == canonical_hash({k: v for k, v in metadata.items() if k != "descriptor_sha256"})
    assert metadata["source_geometry_id"] == geometry.geometry_id
    assert metadata["source_geometry_file_sha256"] == pins[0]
    assert metadata["source_geometry_descriptor_sha256"] == geometry.metadata["descriptor_sha256"]
    assert metadata["source_geometry_npz_sha256"] == pins[1]
    assert metadata["geometry_metadata"] == geometry.metadata
    for key in ("grid", "thickness_mm", "model_extent"):
        assert metadata[key] == geometry.metadata[key]
    assert metadata["background_source"] == background
    assert metadata["element_node_order"] == ["BL", "BR", "TR", "TL"]
    assert metadata["dof_order"] == "interleaved ux,uy; dof = 2*node + component"
    assert metadata["native_geometry_preserved"] is True
    assert metadata["background_source_role"] == "source-only candidate nodes; no applied constraint"
    assert metadata["candidate_node_role"] == "support/symmetry subsets describe geometry attachment only; no fixed/free DOFs are created"
    assert metadata["source_provenance_path_context"] == "Paths inside geometry_metadata provenance belong to the original source context; they are not resolved or read by this map"
    assert metadata["constraints_applied"] is False and metadata["material_assigned"] is False
    assert metadata["task_created"] is False and metadata["analysis_grid_policy"] == "not_selected"
    snapshot = metadata["source_geometry_snapshot"]
    assert snapshot == {"descriptor_path": "source_geometry/geometry.json", "array_path": "source_geometry/geometry.npz"}
    assert (output / snapshot["descriptor_path"]).read_bytes() == source.read_bytes()
    assert (output / snapshot["array_path"]).read_bytes() == source_npz.read_bytes()
    copied = load_geometry(output / snapshot["descriptor_path"])
    assert copied.geometry_id == geometry.geometry_id and copied.metadata == geometry.metadata
    declaration = metadata["arrays"]
    assert declaration["path"] == "map.npz" and digest(output / "map.npz") == declaration["sha256"]
    with np.load(output / "map.npz", allow_pickle=False) as archive:
        assert len(archive.files) == len(expected) == 19 and set(archive.files) == set(expected)
        actual = {key: archive[key].copy() for key in archive.files}
    assert set(declaration["fields"]) == set(expected)
    for key, reference in expected.items():
        value = actual[key]
        assert value.dtype == reference.dtype and value.shape == reference.shape, key
        np.testing.assert_array_equal(value, reference, err_msg=key)
        assert declaration["fields"][key] == dict(dtype=value.dtype.name, shape=list(value.shape),
                                                  sha256=sha256(value.tobytes(order="C")).hexdigest())
    counts = dict(elements=len(expected["connectivity"]), nodes=len(expected["coordinates_mm"]),
                  dofs=2 * len(expected["coordinates_mm"]),
                  **{key + "_cells": int(expected[key].sum()) for key in MASKS},
                  **{key: len(expected[key]) for key in REGIONS})
    assert metadata["counts"] == counts
    if alias == "gripper_native_fine":
        assert (counts["elements"], counts["nodes"], counts["dofs"]) == (12800, 13041, 26082)
    cells = actual["coordinates_mm"][actual["connectivity"]]
    signed_area = .5 * np.sum(cells[:, :, 0] * np.roll(cells[:, :, 1], -1, axis=1)
                            - cells[:, :, 1] * np.roll(cells[:, :, 0], -1, axis=1), axis=1)
    hx, hy = geometry.grid["cell_size_mm"]
    assert np.all(signed_area == hx * hy) and np.all(signed_area > 0.)
    # Dyadic coefficients make these affine/virtual-work identities exact for
    # the selected 1 mm/.5 mm grids and three/five-node trapezoid weights.
    affine_gradient = np.array([[.125, -.25], [.5, .0625]])
    affine_origin = np.array([.03125, -.015625])
    displacement = actual["coordinates_mm"] @ affine_gradient.T + affine_origin
    port_checks = {}
    for name in ("input", "output"):
        tag = geometry.metadata["region_tags"][name]
        midpoint = np.asarray(tag["points_mm"]).mean(axis=0)
        reference = float(np.asarray(tag["direction"]) @ (affine_gradient @ midpoint + affine_origin))
        vector = actual[name + "_vector"]
        mean = float(vector @ displacement.ravel())
        nodal_work = float((.75 * vector) @ displacement.ravel())
        assert mean == reference and nodal_work == .75 * reference
        assert float(actual[name + "_weights"].sum()) == 1.
        port_checks[name] = dict(nodes=actual[name + "_nodes"].tolist(),
            weights=actual[name + "_weights"].tolist(), affine_mean=mean, virtual_work=nodal_work,
            affine_average_identity=True, virtual_work_identity=True)
    return dict(alias=alias, source_geometry_id=geometry.geometry_id,
        map_file_sha256=digest(output / "map.json"), map_array_sha256=digest(output / "map.npz"),
        fields_exactly_equal=19, four_masks_changed_cells={key: 0 for key in MASKS}, counts=counts,
        all_cells_positive_signed_area=True, signed_cell_area_mm2=float(signed_area[0]),
        support_solid_nodes=actual["support_solid_nodes"].tolist(), ports=port_checks,
        background_source_nodes=actual["background_source_nodes"].tolist(),
        background_preserved_not_applied=True, no_material_task_or_fixed_free=True)


def main():
    output = ROOT / "independent_review.json"
    if output.exists() and read(output).get("status") == "pass":
        raise FileExistsError("Successful independent mapping review is immutable")
    receipt = dict(schema_version="native-q1-independent-review-1.0", created_utc=datetime.now(timezone.utc).isoformat(),
        review_source_sha256=digest(Path(__file__)), scope="Three native geometry preparations and synthetic port algebra only; no applied task, selected H2 policy or H3 workpiece qualification",
        author_mapping_imports=0, LF_imports=0, FE_calls=0, force_calls=0, HP_calls=0, solver_calls=0,
        synthetic_affine_gradient=[[.125, -.25], [.5, .0625]], synthetic_affine_origin=[.03125, -.015625],
        virtual_generalized_load=.75)
    try:
        previous = read(PREVIOUS / "execution_receipt.json")
        assert previous["status"] == "pass" and previous["completed_cases"] == 3
        cases = {case["alias"]: case for case in previous["cases"]}
        assert set(cases) == set(PINS)
        production = read(ROOT / "execution_receipt.json")
        assert production["status"] == "pass" and production["completed_cases"] == 3
        assert production["sources"]["lf_data_preparation/native_q1_001/review_mapping.py"] == receipt["review_source_sha256"]
        assert len(production["sources"]) == 9
        for name, pin in production["sources"].items():
            assert digest(REPO / name) == pin == digest(ROOT / "sources" / Path(name).name), name
        produced = {case["alias"]: case for case in production["cases"]}
        assert set(produced) == set(PINS)
        assert digest(REPO / "hf_repo/src/hf_eval/project.py") == LEGACY_PROJECT_SHA
        receipt["cases"] = [replay_case(alias, pins, cases[alias], produced[alias]) for alias, pins in PINS.items()]
        receipt.update(status="pass", previous_execution_receipt_sha256=digest(PREVIOUS / "execution_receipt.json"),
                       mapping_execution_receipt_sha256=digest(ROOT / "execution_receipt.json"),
                       mapping_sources=production["sources"],
                       legacy_project_sha256=LEGACY_PROJECT_SHA, data_helper_sha256=digest(REPO / "hf_repo/src/hf_eval/data.py"))
    except Exception as error:
        receipt.update(status="failed_review", failure_type=type(error).__name__, failure=str(error))
        output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        raise
    output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(dict(status=receipt["status"], cases=len(receipt["cases"]), fields_exactly_equal=19)))


if __name__ == "__main__":
    main()
