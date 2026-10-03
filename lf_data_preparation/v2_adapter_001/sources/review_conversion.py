"""Independently replay three LF v2 to HF conversions as ordinary data.

No LF or author converter is imported. Identity and physical-region arithmetic
follow the original LF v1 hash and v2 interval contracts, without mechanics.
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
from hf_eval.data import load_geometry
from hf_eval.regions import active_nodes, port_vector, region_nodes

CASES = {
    "inverter_canonical": dict(
        design_id="inverter__sweep__kin_1e+01__kout_1e-01", family="inverter", mesh=[80, 40],
        descriptor_sha="7afa92b2e3618562349741458cb48b92b69a076b332c5cc4fbb06f12e2b6c301",
        array_sha="cb28e2013a837083cc4a2b1f5bf45085e315c51db29e677eae72499815375b64",
        hf_id="2e2bb3466ade06f920dfbb92577ccbe46106acec430837bac8e1a30b8083527a",
        support_nodes=[405, 486, 567, 648], entity_count=81, background_count=0),
    "gripper_canonical": dict(
        design_id="gripper__sweep__kin_1e+01__kout_1e+00", family="gripper", mesh=[80, 40],
        descriptor_sha="6daaf44e9f691fc1791881743765c27266ef658f60d58ca7fb3050d4a176c6e7",
        array_sha="fd1e4e15791aa75d7c0411c5442dfad5f4c868967dee13a3e8c9321be90d70f3",
        hf_id="d4e82cfd629e37f7d0c85aed672ab5df228314147cf5db59aeabb279cee5d91d",
        support_nodes=[486, 567, 648], entity_count=61, background_count=20),
    "gripper_native_fine": dict(
        design_id="gripper__refine__kin_1e+00__kout_1e+00__random", family="gripper", mesh=[160, 80],
        descriptor_sha="05aa71c6d3a77d4a221fe16453f06e7e19b45325a4aff824a951c95d4fd1a443",
        array_sha="8ce4f2114f96b2ffd596f889ccdfa9e7eb2a8a2c87ce6000ac4a35f9c9f6fbf6",
        support_nodes=[2093, 2254, 2415, 2576], entity_count=121, background_count=40),
}
FIELDS = {"solid": "solid", "design_domain": "design",
          "passive_solid": "passive_solid", "passive_void": "passive_void"}
AXES = "+x right, +y up; array index [j, i] = [row from bottom, column from left]"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def original_nodes(points, grid):
    """Closed LF physical segment, mapped independently to native C_yx nodes."""
    nx, ny = grid["native_mesh"]
    logical = (np.asarray(points) - grid["origin_mm"]) / grid["cell_mm"]
    rounded = np.rint(logical).astype(int)
    np.testing.assert_array_equal(logical, rounded)
    assert np.all(rounded >= 0) and np.all(rounded <= [nx, ny])
    changed = np.flatnonzero(rounded[1] != rounded[0])
    assert len(changed) == 1
    axis = changed[0]
    step = 1 if rounded[1, axis] > rounded[0, axis] else -1
    indices = np.arange(rounded[0, axis], rounded[1, axis] + step, step)
    return (rounded[0, 1] * (nx + 1) + indices if axis == 0
            else indices * (nx + 1) + rounded[0, 0])


def replay_case(alias, expected, inventory):
    source_dir, output = ROOT / "inputs" / alias, ROOT / "converted" / alias
    source = read(source_dir / "design.json")
    grid, regions = source["grid"], source["regions_mm"]
    assert digest(source_dir / "design.json") == expected["descriptor_sha"]
    assert digest(source_dir / "design.npz") == expected["array_sha"] == source["arrays"]["sha256"]
    assert source["schema"] == "dmftd.hf_export.v2"
    assert source["case"] == expected["family"] and source["design_id"] == expected["design_id"]
    assert grid["native_mesh"] == expected["mesh"] and grid["axes"] == AXES
    nx, ny = grid["native_mesh"]
    assert grid["domain_mm"] == [80., 40.] and grid["origin_mm"] == [0., 0.]
    assert grid["thickness_mm"] == 20. and grid["cell_mm"] == [80. / nx, 40. / ny]
    assert grid["model_extent"] == "lower half model; mirror plane y = 40 mm"
    assert inventory["design_id"] == source["design_id"] and inventory["case"] == source["case"]
    assert inventory["descriptor_sha256"] == expected["descriptor_sha"]
    assert inventory["NPZ_sha256"] == expected["array_sha"]
    prefix = "Diversity-TO-Compliant-O-main/research/hf_export_v2/" + source["design_id"]
    assert inventory["descriptor_member"] == prefix + "/design.json"
    assert inventory["NPZ_member"] == prefix + "/design.npz"
    with np.load(source_dir / "design.npz", allow_pickle=False) as archive:
        assert len(archive.files) == 4 and set(archive.files) == set(FIELDS)
        arrays = {name: archive[name].copy() for name in FIELDS}
    assert all(x.dtype == np.dtype(bool) and x.shape == (ny, nx) for x in arrays.values())
    assert np.all(sum(arrays[k].astype(np.uint8) for k in ("design_domain", "passive_solid", "passive_void")) == 1)
    assert not np.any(arrays["passive_solid"] & ~arrays["solid"])
    assert not np.any(arrays["passive_void"] & arrays["solid"])
    header = (f"dmftd.hf_export.v1|{source['case']}|nx={nx}|ny={ny}|"
              f"domain={grid['domain_mm'][0]:g}x{grid['domain_mm'][1]:g}|t={grid['thickness_mm']:g}|"
              "arrays=solid,passive_solid,passive_void|").encode()
    identity = sha256(header)
    for name in ("solid", "passive_solid", "passive_void"):
        identity.update(np.ascontiguousarray(arrays[name], dtype=np.uint8).tobytes())
    assert identity.hexdigest() == source["geometry_id"] == inventory["LF_geometry_id"]
    geometry = load_geometry(output / "geometry.json")
    metadata = geometry.metadata
    assert metadata["case_family"] == source["case"]
    assert geometry.grid == dict(shape_yx=[ny, nx], origin_mm=[0., 0.], cell_size_mm=grid["cell_mm"],
        axes=[[1., 0.], [0., 1.]], extent_mm=[80., 40.], array_order="C_yx_bottom_up", value_location="cell")
    assert metadata["thickness_mm"] == 20.
    assert metadata["model_extent"] == dict(kind="lower_half", symmetry_axis=dict(normal=[0., 1.], offset_mm=40.))
    differences = {target: int(np.count_nonzero(arrays[name] != geometry.arrays[target])) for name, target in FIELDS.items()}
    assert not any(differences.values())
    provenance = metadata["provenance"]["lf_v2"]
    assert provenance["descriptor"] == source and provenance["schema"] == source["schema"]
    assert provenance["design_id"] == source["design_id"] and provenance["geometry_id"] == source["geometry_id"]
    assert provenance["descriptor_sha256"] == expected["descriptor_sha"]
    assert provenance["array_file_sha256"] == expected["array_sha"]
    for key, name in (("descriptor_path", "design.json"), ("array_path", "design.npz")):
        assert provenance[key] == "sources/" + name
        assert (output / provenance[key]).read_bytes() == (source_dir / name).read_bytes()
    assert metadata["source_record_ids"] == [source["design_id"]]
    processing = metadata["processing"]
    assert processing["source_kind"] == "ordinary_LF_v2_package"
    assert processing["source_native_grid_preserved"] is True and processing["lossless_bool_to_uint8"] is True
    assert processing["new_threshold_or_cleanup_applied"] is False and processing["background_boundary_applied"] is False
    assert processing["support_attachment"] == regions["support"]["attachment"] == "solid_incident"
    assert processing["source_symmetry_policy"] == source["source"]["symmetry_policy"]
    assert processing["task_policy"] == "Source boundary metadata is provenance; no HF task or applied constraints are created"
    assert {p.name for p in output.iterdir()} == {"geometry.json", "geometry.npz", "sources"}
    assert {p.name for p in (output / "sources").iterdir()} == {"design.json", "design.npz"}
    tags = metadata["region_tags"]
    assert set(tags) == {"support", "symmetry", "input", "output"}
    for name, original in (("support", "support"), ("symmetry", "symmetry_solid")):
        tag = regions[original]
        assert tag["kind"] == "segment_mm" and tag["interval"] == "closed"
        components = [{"ux": 0, "uy": 1}[c] for c in tag["components"]]
        assert tags[name] == dict(points_mm=tag["points"], components=components)
        np.testing.assert_array_equal(region_nodes(geometry, tags[name]), original_nodes(tag["points"], grid))
    incident = np.zeros((ny + 1, nx + 1), dtype=bool)
    for y, x in ((0, 0), (0, 1), (1, 0), (1, 1)):
        incident[y:y + ny, x:x + nx] |= arrays["solid"]
    np.testing.assert_array_equal(active_nodes(geometry), incident.ravel())
    support = original_nodes(regions["support"]["points"], grid)
    attached = support[incident.ravel()[support]]
    np.testing.assert_array_equal(attached, expected["support_nodes"])
    entity = original_nodes(regions["symmetry_solid"]["points"], grid)
    background = regions["symmetry_background"]
    background_nodes = np.array([], dtype=int)
    if source["case"] == "gripper":
        assert background["kind"] == "complement_on_line" and background["interval"] == "open_closed"
        assert background["line"] == {"axis": "y", "value_mm": 40.}
        assert background["start_exclusive_mm"] == 60. and background["end_inclusive_mm"] == 80.
        assert background["x_range_mm"] == [60., 80.] and background["components"] == ["uy"]
        assert background["source_policy"] == "full_midline"
        first = 60. + grid["cell_mm"][0]
        assert background["first_native_node_mm"] == first
        assert background["v1_segment_points"] == [[first, 40.], [80., 40.]]
        xx = np.arange(nx + 1) * grid["cell_mm"][0]
        background_nodes = ny * (nx + 1) + np.flatnonzero((xx > 60.) & (xx <= 80.))
        assert ny * (nx + 1) + round(60. / grid["cell_mm"][0]) not in background_nodes
    else:
        assert background is None
    assert len(entity) == expected["entity_count"] and len(background_nodes) == expected["background_count"]
    assert len(np.intersect1d(entity, background_nodes)) == 0
    np.testing.assert_array_equal(np.union1d(entity, background_nodes), ny * (nx + 1) + np.arange(nx + 1))
    ports = {}
    for name in ("input", "output"):
        tag = regions[name + "_port"]
        assert tag["kind"] == "segment_mm" and tag["interval"] == "closed"
        assert tags[name] == dict(points_mm=tag["points"], direction=tag["direction_reference"], averaging=tag["averaging"])
        selected = original_nodes(tag["points"], grid)
        weights = np.ones(len(selected)) / (len(selected) - 1)
        weights[[0, -1]] *= .5
        vector, actual, actual_weights = port_vector(geometry, tags[name])
        np.testing.assert_array_equal(actual, selected)
        np.testing.assert_array_equal(actual_weights, weights)
        np.testing.assert_array_equal(tag["native_weights_example"], weights)
        expected_vector = np.zeros_like(vector).reshape(-1, 2)
        expected_vector[selected] = weights[:, None] * np.array(tag["direction_reference"])
        np.testing.assert_array_equal(vector, expected_vector.ravel())
        assert np.all(incident.ravel()[selected])
        ports[name] = dict(nodes=selected.tolist(), weights=weights.tolist(), direction=tag["direction_reference"])
    assert "analysis_mesh" not in geometry.grid and provenance["descriptor"]["grid"]["analysis_mesh"] == grid["analysis_mesh"]
    old_id = None
    if "hf_id" in expected:
        old = load_geometry(REPO / "geometry_dataset/canonical" / source["case"] / "geometry.json")
        assert old.geometry_id == geometry.geometry_id == expected["hf_id"]
        for name in FIELDS.values():
            np.testing.assert_array_equal(old.arrays[name], geometry.arrays[name])
        old_id = old.geometry_id
    return dict(alias=alias, design_id=source["design_id"], case_family=source["case"],
        LF_geometry_id_recomputed=identity.hexdigest(), HF_geometry_id=geometry.geometry_id,
        original_canonical_HF_id_equal=old_id, descriptor_sha256=expected["descriptor_sha"],
        NPZ_sha256=expected["array_sha"], converted_descriptor_sha256=digest(output / "geometry.json"),
        native_mesh_xy=grid["native_mesh"], source_analysis_mesh_xy=grid["analysis_mesh"],
        mask_changed_cells=differences, support_selected_nodes=support.tolist(), support_solid_incident_nodes=attached.tolist(),
        entity_symmetry_node_count=len(entity), source_background_nodes=background_nodes.tolist(),
        background_preserved_not_applied=True, analysis_mesh_source_only=True, ports=ports)


def main():
    output = ROOT / "independent_review.json"
    if output.exists() and read(output).get("status") == "pass":
        raise FileExistsError("Successful independent review is immutable")
    receipt = dict(schema_version="lf-v2-conversion-independent-review-1.0",
        created_utc=datetime.now(timezone.utc).isoformat(), review_source_sha256=digest(Path(__file__)),
        scope="Three selected ordinary packages only; scientific data identity and semantics, not formal HF qualification or all1800/all30 validation",
        LF_imports=0, author_converter_imports=0, FE_calls=0, force_calls=0, HP_calls=0, solver_calls=0)
    try:
        inventory = read(ROOT / "source_inventory.json")
        assert inventory["source_archive_name"] == "Diversity-TO-Compliant-O-main (10).zip"
        assert inventory["source_archive_sha256"] == "79c44fbf2570651539137d74299714823c8046d13efd9c3bad6eb32bc389745e"
        selected = {row["alias"]: row for row in inventory["selected"]}
        assert set(selected) == set(CASES)
        receipt["cases"] = [replay_case(alias, expected, selected[alias]) for alias, expected in CASES.items()]
        receipt.update(status="pass", source_inventory_sha256=digest(ROOT / "source_inventory.json"),
            sources={name: digest(REPO / "hf_repo/src/hf_eval" / name) for name in ("data.py", "regions.py", "lf_v2.py")})
    except Exception as error:
        receipt.update(status="failed_review", failure_type=type(error).__name__, failure=str(error))
        output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        raise
    output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(dict(status=receipt["status"], cases=len(receipt["cases"]), mask_changed_cells=0)))


if __name__ == "__main__":
    main()
