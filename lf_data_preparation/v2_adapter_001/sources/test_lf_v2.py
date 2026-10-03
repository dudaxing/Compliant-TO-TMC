"""Lossless native-grid conversion of the three frozen LF v2 examples.

Only ordinary JSON/NPZ data is consumed. No LF or HF mechanics is imported.
Counterexamples are copies; the source evidence packages remain unchanged.
"""
from hashlib import sha256
import json
from pathlib import Path
import shutil

import numpy as np
import pytest

from hf_eval.data import ARRAY_NAMES, GeometryError, load_geometry
from hf_eval.lf_v2 import convert_lf_v2
from hf_eval.regions import node_coordinates, port_vector


ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / "lf_data_preparation" / "v2_adapter_001"
SOURCE_KEYS = {"solid": "solid", "design": "design_domain",
               "passive_solid": "passive_solid", "passive_void": "passive_void"}


def source_package(alias):
    descriptor = STAGE / "inputs" / alias / "design.json"
    source = json.loads(descriptor.read_text(encoding="utf-8"))
    with np.load(descriptor.with_name("design.npz"), allow_pickle=False) as archive:
        arrays = {name: archive[name].copy() for name in archive.files}
    inventory = json.loads((STAGE / "source_inventory.json").read_text(encoding="utf-8"))
    pin = next(item for item in inventory["selected"] if item["alias"] == alias)
    return descriptor, source, arrays, pin


def assert_lossless_provenance(geometry, descriptor, source, arrays, pin):
    provenance = geometry.metadata["provenance"]["lf_v2"]
    assert provenance["descriptor"] == source
    assert provenance["descriptor_sha256"] == pin["descriptor_sha256"] == sha256(descriptor.read_bytes()).hexdigest()
    assert provenance["array_file_sha256"] == pin["NPZ_sha256"] == sha256(descriptor.with_name("design.npz").read_bytes()).hexdigest()
    assert provenance["geometry_id"] == source["geometry_id"]
    assert provenance["design_id"] == source["design_id"]
    for key, original in (("descriptor_path", descriptor), ("array_path", descriptor.with_name("design.npz"))):
        assert (geometry.path.parent / provenance[key]).read_bytes() == original.read_bytes()
    for name in ARRAY_NAMES:
        assert arrays[SOURCE_KEYS[name]].dtype == np.dtype(bool)
        assert geometry.arrays[name].dtype == np.dtype("uint8")
        np.testing.assert_array_equal(geometry.arrays[name], arrays[SOURCE_KEYS[name]])
    processing = geometry.metadata["processing"]
    assert processing["source_native_grid_preserved"] is True
    assert processing["lossless_bool_to_uint8"] is True
    assert processing["new_threshold_or_cleanup_applied"] is False
    assert processing["background_boundary_applied"] is False
    assert processing["support_attachment"] == "solid_incident"


@pytest.mark.parametrize("family", ["inverter", "gripper"])
def test_canonical_masks_authority_and_regions_are_identical(family, tmp_path):
    descriptor, source, arrays, pin = source_package(family + "_canonical")
    converted = load_geometry(convert_lf_v2(descriptor, tmp_path / family,
                              expected_descriptor_sha256=pin["descriptor_sha256"]))
    canonical = load_geometry(ROOT / "geometry_dataset" / "canonical" / family)
    assert_lossless_provenance(converted, descriptor, source, arrays, pin)
    assert source["grid"]["analysis_mesh"] == [160, 80]
    assert converted.grid == canonical.grid
    assert converted.grid["shape_yx"] == [40, 80]  # Native cells, not the LF analysis mesh.
    assert converted.metadata["thickness_mm"] == canonical.metadata["thickness_mm"]
    assert converted.metadata["model_extent"] == canonical.metadata["model_extent"]
    assert converted.metadata["region_tags"] == canonical.metadata["region_tags"]
    assert converted.geometry_id == canonical.geometry_id
    for name in ARRAY_NAMES:
        np.testing.assert_array_equal(converted.arrays[name], canonical.arrays[name])


def test_fine_grid_ports_and_open_closed_background_remain_native(tmp_path):
    descriptor, source, arrays, pin = source_package("gripper_native_fine")
    geometry = load_geometry(convert_lf_v2(descriptor, tmp_path / "fine",
                             expected_descriptor_sha256=pin["descriptor_sha256"]))
    assert_lossless_provenance(geometry, descriptor, source, arrays, pin)
    assert geometry.grid["shape_yx"] == [80, 160]
    assert geometry.grid["cell_size_mm"] == [.5, .5]
    assert geometry.grid["extent_mm"] == [80., 40.]
    coordinates = node_coordinates(geometry)
    for port, x, y0 in (("input", 0., 38.), ("output", 80., 28.)):
        vector, nodes, weights = port_vector(geometry, geometry.metadata["region_tags"][port])
        np.testing.assert_array_equal(weights, [.125, .25, .25, .25, .125])
        np.testing.assert_array_equal(coordinates[nodes], np.column_stack((np.full(5, x), y0 + .5 * np.arange(5))))
        direction = geometry.metadata["region_tags"][port]["direction"]
        np.testing.assert_array_equal(vector.reshape(-1, 2)[nodes], weights[:, None] * direction)
    assert geometry.metadata["region_tags"]["output"]["direction"] == [0., 1.]
    assert set(geometry.metadata["region_tags"]) == {"support", "symmetry", "input", "output"}
    assert geometry.metadata["region_tags"]["symmetry"]["points_mm"] == [[0., 40.], [60., 40.]]
    background = geometry.metadata["provenance"]["lf_v2"]["descriptor"]["regions_mm"]["symmetry_background"]
    assert background == source["regions_mm"]["symmetry_background"]
    assert (background["interval"], background["start_exclusive_mm"], background["end_inclusive_mm"]) == ("open_closed", 60., 80.)
    assert background["first_native_node_mm"] == 60.5


@pytest.mark.parametrize("fault, message", [
    ("descriptor_sha", "descriptor SHA256 mismatch"),
    ("npz_sha", "NPZ SHA256 mismatch"),
    ("geometry_id", "geometry_id mismatch"),
    ("shape", "solid shape differs from native_mesh"),
    ("dtype", "solid dtype must be bool"),
    ("partition", "design/passive masks must partition every native cell"),
    ("passive", "passive masks contradict solid"),
    ("direction", "output_port direction_reference differs"),
    ("port_interval", "input_port must be a closed segment_mm interval"),
    ("background_interval", "background interval or policy differs"),
    ("attachment", "support attachment must be solid_incident"),
    ("bool_origin", r"grid\.origin_mm must be a finite number"),
    ("string_cell", r"grid\.cell_size_mm must be a finite number"),
])
def test_bad_source_rejected_at_the_specific_contract(fault, message, tmp_path):
    descriptor, source, arrays, _ = source_package("gripper_canonical")
    copied = tmp_path / "input"
    shutil.copytree(descriptor.parent, copied)
    if fault == "npz_sha":
        payload = bytearray((copied / "design.npz").read_bytes())
        payload[-1] ^= 1
        (copied / "design.npz").write_bytes(payload)
    elif fault == "geometry_id":
        source["geometry_id"] = "0" * 64
    elif fault == "shape":
        arrays["solid"] = arrays["solid"][:-1]
    elif fault == "dtype":
        arrays["solid"] = arrays["solid"].astype(np.uint8)
    elif fault == "partition":
        cell = tuple(np.argwhere(arrays["passive_void"])[0])
        arrays["design_domain"][cell] = True
    elif fault == "passive":
        cell = tuple(np.argwhere(arrays["passive_solid"])[0])
        arrays["solid"][cell] = False
    elif fault == "direction":
        source["regions_mm"]["output_port"]["direction_reference"] = [0., -1.]
    elif fault == "port_interval":
        source["regions_mm"]["input_port"]["interval"] = "open_closed"
    elif fault == "background_interval":
        source["regions_mm"]["symmetry_background"]["interval"] = "closed"
    elif fault == "attachment":
        source["regions_mm"]["support"]["attachment"] = "all_segment_nodes"
    elif fault == "bool_origin":
        source["grid"]["origin_mm"] = [False, 0.]
    elif fault == "string_cell":
        source["grid"]["cell_mm"] = ["1.0", 1.]
    if fault in {"shape", "dtype", "partition", "passive"}:
        np.savez_compressed(copied / "design.npz", **arrays)
        source["arrays"]["sha256"] = sha256((copied / "design.npz").read_bytes()).hexdigest()
    (copied / "design.json").write_text(json.dumps(source, allow_nan=False), encoding="utf-8")
    expected = "0" * 64 if fault == "descriptor_sha" else sha256((copied / "design.json").read_bytes()).hexdigest()
    output = tmp_path / "output"
    # Matching the diagnostic is essential: stale geometry_id cannot stand in
    # for a shape/partition/type/physical-region validation failure.
    with pytest.raises(GeometryError, match=message):
        if fault in {"bool_origin", "string_cell"}:
            convert_lf_v2(copied / "design.json", output)
        else:
            convert_lf_v2(copied / "design.json", output, expected_descriptor_sha256=expected)
    assert not output.exists()
