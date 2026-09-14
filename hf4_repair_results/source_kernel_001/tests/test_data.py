from copy import deepcopy
from hashlib import sha256
import json

import numpy as np
import pytest

from hf_eval.data import ARRAY_NAMES, GeometryError, canonical_hash, geometry_id, load_geometry, write_geometry


def marker():
    solid = np.array([[1, 1, 0, 0], [1, 0, 0, 0], [1, 1, 1, 0]], dtype=np.uint8)
    arrays = {"solid": solid, "design": np.ones_like(solid),
              "passive_solid": np.zeros_like(solid), "passive_void": np.zeros_like(solid)}
    metadata = {
        "schema_version": "hf-geometry-1.0", "case_family": "synthetic",
        "grid": {"shape_yx": [3, 4], "origin_mm": [10, 20], "cell_size_mm": [2, 3],
                 "extent_mm": [8, 9], "axes": [[1, 0], [0, 1]],
                 "array_order": "C_yx_bottom_up", "value_location": "cell"},
        "thickness_mm": 5, "model_extent": {"kind": "full"},
        "region_tags": {
            "support": {"points_mm": [[10, 20], [10, 29]], "components": [0, 1]},
            "input": {"points_mm": [[10, 20], [14, 20]], "direction": [0, 1],
                      "averaging": "normalized_reference_arclength_trapezoid"},
            "output": {"points_mm": [[10, 29], [16, 29]], "direction": [0, -1],
                       "averaging": "normalized_reference_arclength_trapezoid"},
        }, "source_record_ids": ["archive-a"], "processing": {"existing_threshold": 0.5},
    }
    return metadata, arrays


def resign(path, mutation):
    metadata = json.loads(path.read_text(encoding="utf-8"))
    mutation(metadata)
    metadata.pop("descriptor_sha256", None)
    metadata["descriptor_sha256"] = canonical_hash(metadata)
    path.write_text(json.dumps(metadata), encoding="utf-8")


def test_round_trip_preserves_authority_and_inputs(tmp_path):
    metadata, arrays = marker()
    before = deepcopy(metadata)
    path = write_geometry(tmp_path / "package", metadata, arrays)
    loaded = load_geometry(path)
    assert metadata == before
    assert loaded.path == path
    for name in ARRAY_NAMES:
        np.testing.assert_array_equal(loaded.arrays[name], arrays[name])
        assert loaded.arrays[name].dtype == np.uint8
        assert not loaded.arrays[name].flags.writeable
    assert loaded.grid["origin_mm"] == [10.0, 20.0]
    assert loaded.geometry_id == geometry_id(metadata, arrays)
    assert loaded.metadata["arrays"]["path"] == "geometry.npz"
    # Authority survives moving the whole package and an unrelated source path.
    relocated = tmp_path / "relocated"
    path.parent.rename(relocated)
    assert load_geometry(relocated).geometry_id == loaded.geometry_id


def test_hashes_distinguish_shapes_scale_and_direction_without_including_source(tmp_path):
    metadata, arrays = marker()
    baseline = geometry_id(metadata, arrays)
    equivalent = deepcopy(metadata)
    for name in ("origin_mm", "cell_size_mm", "extent_mm"):
        equivalent["grid"][name] = [float(v) for v in equivalent["grid"][name]]
    equivalent["thickness_mm"] = 5.0
    equivalent["source_record_ids"] = ["another-run"]
    equivalent["processing"] = {"inert_source_path": "Z:/not-present/source.py"}
    assert geometry_id(equivalent, arrays) == baseline
    scaled = deepcopy(metadata)
    scaled["grid"]["cell_size_mm"] = [4, 6]
    scaled["grid"]["extent_mm"] = [16, 18]
    assert geometry_id(scaled, arrays) != baseline
    flipped = {name: array[::-1] for name, array in arrays.items()}
    assert geometry_id(metadata, flipped) != baseline
    transposed = deepcopy(metadata)
    transposed["grid"]["shape_yx"] = [4, 3]
    transposed["grid"]["extent_mm"] = [6, 12]
    assert geometry_id(transposed, {name: a.T for name, a in arrays.items()}) != baseline
    p1 = write_geometry(tmp_path / "one", metadata, arrays)
    tagged = deepcopy(metadata)
    tagged["region_tags"]["output"]["direction"] = [1, 0]
    p2 = write_geometry(tmp_path / "two", tagged, arrays)
    g1, g2 = load_geometry(p1), load_geometry(p2)
    assert g1.geometry_id == g2.geometry_id
    assert g1.metadata["descriptor_sha256"] != g2.metadata["descriptor_sha256"]


@pytest.mark.parametrize("bad", [0.5, 256, -1, np.nan, np.inf])
def test_writer_rejects_nonbinary_before_cast(tmp_path, bad):
    metadata, arrays = marker()
    arrays["solid"] = arrays["solid"].astype(float)
    arrays["solid"][0, 0] = bad
    with pytest.raises(GeometryError, match="non-binary|non-finite"):
        write_geometry(tmp_path / "bad", metadata, arrays)
    assert not (tmp_path / "bad").exists()


@pytest.mark.parametrize("violation", ["partition", "passive_solid", "passive_void", "shape", "object"])
def test_writer_rejects_invalid_masks(tmp_path, violation):
    metadata, arrays = marker()
    if violation == "partition":
        arrays["design"][0, 0] = 0
    elif violation == "passive_solid":
        arrays["design"][0, 2] = 0
        arrays["passive_solid"][0, 2] = 1
    elif violation == "passive_void":
        arrays["design"][0, 0] = 0
        arrays["passive_void"][0, 0] = 1
    elif violation == "shape":
        arrays["solid"] = arrays["solid"].T
    else:
        arrays["solid"] = arrays["solid"].astype(object)
    with pytest.raises(GeometryError):
        write_geometry(tmp_path / "bad", metadata, arrays)


@pytest.mark.parametrize("field,value", [
    ("thickness_mm", -1), ("thickness_mm", np.inf),
    ("length_unit", "m"), ("schema_version", "legacy-unknown"),
])
def test_writer_rejects_invalid_physics(tmp_path, field, value):
    metadata, arrays = marker()
    metadata[field] = value
    with pytest.raises(GeometryError):
        write_geometry(tmp_path / "bad", metadata, arrays)


@pytest.mark.parametrize("field,value", [
    ("axes", [[1, 0], [0, -1]]), ("array_order", "top_down"),
    ("shape_yx", [3.0, 4.0]), ("extent_mm", [9, 8]),
    ("origin_mm", [float("nan"), 0]), ("cell_size_mm", [0, 1]),
])
def test_writer_rejects_inconsistent_grid(tmp_path, field, value):
    metadata, arrays = marker()
    metadata["grid"][field] = value
    with pytest.raises(GeometryError):
        write_geometry(tmp_path / "bad", metadata, arrays)


def test_descriptor_tampering_detected_before_unsafe_read(tmp_path):
    metadata, arrays = marker()
    path = write_geometry(tmp_path, metadata, arrays)
    raw = json.loads(path.read_text())
    raw["region_tags"]["input"]["direction"] = [1, 0]
    path.write_text(json.dumps(raw))
    with pytest.raises(GeometryError, match="descriptor_sha256"):
        load_geometry(path)


@pytest.mark.parametrize("escape", ["../outside.npz", "/outside.npz", "C:\\outside.npz", "sub/geometry.npz"])
def test_signed_nonportable_reference_rejected(tmp_path, escape):
    metadata, arrays = marker()
    path = write_geometry(tmp_path, metadata, arrays)
    resign(path, lambda meta: meta["arrays"].update(path=escape))
    with pytest.raises(GeometryError, match="relative file name"):
        load_geometry(path)


def test_corrupt_npz_and_signed_invalid_npz(tmp_path):
    metadata, arrays = marker()
    path = write_geometry(tmp_path, metadata, arrays)
    (tmp_path / "geometry.npz").write_bytes(b"broken archive")
    with pytest.raises(GeometryError, match="NPZ file sha256"):
        load_geometry(path)
    resign(path, lambda meta: meta["arrays"].update(sha256=sha256(b"broken archive").hexdigest()))
    with pytest.raises(GeometryError, match="Cannot read geometry"):
        load_geometry(path)


def test_pickle_arrays_and_internal_hash_mismatch_rejected(tmp_path):
    metadata, arrays = marker()
    path = write_geometry(tmp_path, metadata, arrays)
    bad = dict(arrays)
    bad["solid"] = arrays["solid"].astype(object)
    np.savez(tmp_path / "geometry.npz", **bad)
    resign(path, lambda meta: meta["arrays"].update(sha256=sha256((tmp_path / "geometry.npz").read_bytes()).hexdigest()))
    with pytest.raises(GeometryError, match="allow_pickle=False"):
        load_geometry(path)
    path = write_geometry(tmp_path, metadata, arrays)
    resign(path, lambda meta: meta["arrays"]["fields"]["solid"].update(sha256="0" * 64))
    with pytest.raises(GeometryError, match="content hash"):
        load_geometry(path)
    path = write_geometry(tmp_path, metadata, arrays)
    resign(path, lambda meta: meta.update(geometry_id="0" * 64))
    with pytest.raises(GeometryError, match="geometry_id mismatch"):
        load_geometry(path)


def test_nan_and_duplicate_json_keys_rejected(tmp_path):
    metadata, arrays = marker()
    metadata["processing"]["invalid"] = float("nan")
    with pytest.raises(GeometryError, match="Non-finite"):
        write_geometry(tmp_path, metadata, arrays)
    path = tmp_path / "duplicate.json"
    path.write_text('{"schema_version":"a","schema_version":"b"}')
    with pytest.raises(GeometryError, match="Duplicate JSON key"):
        load_geometry(path)


def test_reader_rejects_wrong_stored_dtype_even_after_file_hash_update(tmp_path):
    metadata, arrays = marker()
    path = write_geometry(tmp_path, metadata, arrays)
    modified = {name: array.astype(np.uint16) for name, array in arrays.items()}
    np.savez(tmp_path / "geometry.npz", **modified)
    resign(path, lambda meta: meta["arrays"].update(sha256=sha256((tmp_path / "geometry.npz").read_bytes()).hexdigest()))
    with pytest.raises(GeometryError, match="stored as uint8"):
        load_geometry(path)


def test_descriptor_symlink_cannot_introduce_external_dependency(tmp_path):
    metadata, arrays = marker()
    external = write_geometry(tmp_path / "external", metadata, arrays)
    package = tmp_path / "package"
    package.mkdir()
    link = package / "geometry.json"
    try:
        link.symlink_to(external)
    except OSError as error:
        pytest.skip(f"Platform does not permit creating a symlink: {error}")
    with pytest.raises(GeometryError, match="symbolic link"):
        load_geometry(link)


def half_marker():
    metadata, arrays = marker()
    metadata["model_extent"] = {
        "kind": "lower_half", "symmetry_axis": {"normal": [0, 1], "offset_mm": 29},
    }
    metadata["region_tags"]["symmetry"] = {"points_mm": [[10, 29], [14, 29]], "components": [1]}
    return metadata, arrays


def test_lower_half_accepts_partial_entity_symmetry_segment(tmp_path):
    metadata, arrays = half_marker()
    geometry = load_geometry(write_geometry(tmp_path, metadata, arrays))
    assert geometry.metadata["region_tags"]["symmetry"]["points_mm"] == [[10.0, 29.0], [14.0, 29.0]]


@pytest.mark.parametrize("violation", ["missing", "interior", "wrong_component", "mixed_components", "port", "off_grid", "outside"])
def test_lower_half_rejects_invalid_symmetry_definition(tmp_path, violation):
    metadata, arrays = half_marker()
    symmetry = metadata["region_tags"]["symmetry"]
    if violation == "missing":
        del metadata["region_tags"]["symmetry"]
    elif violation == "interior":
        symmetry["points_mm"] = [[10, 26], [14, 26]]
    elif violation == "wrong_component":
        symmetry["components"] = [0]
    elif violation == "mixed_components":
        symmetry["components"] = [0, 1]
    elif violation == "port":
        symmetry["direction"] = [1, 0]
        symmetry["averaging"] = "normalized_reference_arclength_trapezoid"
    elif violation == "off_grid":
        symmetry["points_mm"][1][0] = 13
    else:
        symmetry["points_mm"][1][0] = 20
    with pytest.raises(GeometryError, match="lower_half"):
        write_geometry(tmp_path, metadata, arrays)


def test_signed_descriptor_cannot_hide_missing_half_symmetry(tmp_path):
    metadata, arrays = half_marker()
    path = write_geometry(tmp_path, metadata, arrays)
    resign(path, lambda meta: meta["region_tags"].pop("symmetry"))
    with pytest.raises(GeometryError, match="lower_half"):
        load_geometry(path)
