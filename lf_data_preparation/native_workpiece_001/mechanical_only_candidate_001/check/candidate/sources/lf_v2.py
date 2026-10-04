"""Prepare ordinary LF v2 files as native HF geometry, without mechanics.

Source boundary and LF reference records are provenance. This conversion does
not create an HF task or apply the source background symmetry constraint.
"""
from __future__ import annotations

from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path

import numpy as np

from .data import Geometry, GeometryError, geometry_id as hf_geometry_id, write_geometry
from .regions import port_vector, region_nodes


LF_SCHEMA = "dmftd.hf_export.v2"
LF_ARRAY_NAMES = ("solid", "passive_solid", "passive_void", "design_domain")
AXES = "+x right, +y up; array index [j, i] = [row from bottom, column from left]"


def _require(condition, message):
    if not condition:
        raise GeometryError("LF v2: " + message)


def _json_object(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, "duplicate JSON key: " + key)
        result[key] = value
    return result


def _segment(regions, name, points, *, components=None, direction=None):
    tag = regions[name]
    _require(tag.get("kind") == "segment_mm" and tag.get("interval") == "closed",
             name + " must be a closed segment_mm interval")
    _require(tag.get("points") == points, name + " points differ from the supported physical region")
    result = {"points_mm": tag["points"]}
    if components is not None:
        _require(tag.get("components") == components, name + " components differ")
        result["components"] = [{"ux": 0, "uy": 1}[value] for value in components]
    else:
        _require(tag.get("direction_reference") == direction, name + " direction_reference differs")
        _require(tag.get("averaging") == "normalized_reference_arclength_trapezoid",
                 name + " averaging rule differs")
        result.update(direction=tag["direction_reference"], averaging=tag["averaging"])
    return result


def convert_lf_v2(source_descriptor: Path, output_directory: Path, *, expected_descriptor_sha256=None) -> Path:
    """Validate one JSON/NPZ package and write a new, self-contained HF package.

    Both original files and the complete LF descriptor are retained. Native
    cells are copied without resampling, cleanup, thresholding or reordering.
    The optional expected SHA256 binds the original JSON file bytes. An existing
    output directory is never reused.
    """
    source_descriptor, output_directory = Path(source_descriptor), Path(output_directory)
    descriptor_bytes = source_descriptor.read_bytes()
    descriptor_sha = sha256(descriptor_bytes).hexdigest()
    if expected_descriptor_sha256 is not None:
        _require(descriptor_sha == expected_descriptor_sha256, "descriptor SHA256 mismatch")
    source = json.loads(descriptor_bytes, object_pairs_hook=_json_object)
    _require(isinstance(source, dict) and source.get("schema") == LF_SCHEMA, "unsupported schema")
    family = source.get("case")
    _require(family in {"inverter", "gripper"}, "unsupported case")
    _require(isinstance(source.get("design_id"), str) and bool(source["design_id"]), "missing design_id")
    grid = source["grid"]
    mesh = grid["native_mesh"]
    _require(isinstance(mesh, list) and len(mesh) == 2 and all(type(n) is int and n > 0 for n in mesh),
             "native_mesh must contain two positive integers")
    nx, ny = mesh
    cell = np.asarray(grid["cell_mm"], dtype=float)
    _require(cell.shape == (2,) and np.all(np.isfinite(cell)) and np.all(cell > 0), "invalid cell_mm")
    _require(grid["domain_mm"] == [80., 40.] and grid["origin_mm"] == [0., 0.], "domain or origin differs")
    _require(np.allclose(cell * [nx, ny], [80., 40.], rtol=1e-12, atol=0.), "native_mesh and cell_mm disagree")
    _require(grid["axes"] == AXES, "axes or bottom-up array order differs")
    _require(grid["model_extent"] == "lower half model; mirror plane y = 40 mm"
             and grid["thickness_mm"] == 20., "model extent or thickness differs")
    definition = source["arrays"]
    _require(definition.get("file") == "design.npz", "arrays.file must be same-directory design.npz")
    _require(set(definition.get("keys", {})) == set(LF_ARRAY_NAMES), "array declarations differ")
    array_bytes = source_descriptor.with_name("design.npz").read_bytes()
    array_sha = sha256(array_bytes).hexdigest()
    _require(array_sha == definition.get("sha256"), "NPZ SHA256 mismatch")
    with np.load(BytesIO(array_bytes), allow_pickle=False) as archive:
        _require(len(archive.files) == 4 and set(archive.files) == set(LF_ARRAY_NAMES), "NPZ fields differ")
        arrays = {}
        for name in LF_ARRAY_NAMES:
            array = archive[name]
            _require(array.dtype == np.dtype(bool), name + " dtype must be bool")
            _require(array.shape == (ny, nx), name + " shape differs from native_mesh")
            arrays[name] = np.array(array, dtype=np.uint8, order="C", copy=True)
    partition = arrays["design_domain"] + arrays["passive_solid"] + arrays["passive_void"]
    _require(np.all(partition == 1), "design/passive masks must partition every native cell")
    _require(not np.any(arrays["passive_solid"] > arrays["solid"])
             and not np.any(arrays["passive_void"] & arrays["solid"]), "passive masks contradict solid")
    # V2 deliberately inherits V1's three-array identity; design_domain is bound
    # by the original NPZ SHA and by the new HF four-array geometry identity.
    header = (f"dmftd.hf_export.v1|{family}|nx={nx}|ny={ny}|domain=80x40|t=20|"
              "arrays=solid,passive_solid,passive_void|").encode()
    digest = sha256(header)
    for name in ("solid", "passive_solid", "passive_void"):
        digest.update(arrays[name].tobytes(order="C"))
    _require(digest.hexdigest() == source.get("geometry_id"), "geometry_id mismatch")
    regions = source["regions_mm"]
    _require(regions["support"].get("attachment") == "solid_incident", "support attachment must be solid_incident")
    entity_end = 80. if family == "inverter" else 60.
    tags = {
        "support": _segment(regions, "support", [[0., 0.], [0., 8.]], components=["ux", "uy"]),
        "symmetry": _segment(regions, "symmetry_solid", [[0., 40.], [entity_end, 40.]], components=["uy"]),
        "input": _segment(regions, "input_port", [[0., 38.], [0., 40.]], direction=[1., 0.]),
        "output": _segment(regions, "output_port", [[80., 38.], [80., 40.]] if family == "inverter"
                           else [[80., 28.], [80., 30.]], direction=[-1., 0.] if family == "inverter" else [0., 1.]),
    }
    background = regions["symmetry_background"]
    if family == "inverter":
        _require(background is None, "inverter must not declare a background complement")
    else:
        _require(isinstance(background, dict) and background.get("kind") == "complement_on_line"
                 and background.get("interval") == "open_closed"
                 and background.get("line") == {"axis": "y", "value_mm": 40.}
                 and background.get("start_exclusive_mm") == 60. and background.get("end_inclusive_mm") == 80.
                 and background.get("x_range_mm") == [60., 80.] and background.get("components") == ["uy"]
                 and background.get("source_policy") == "full_midline", "background interval or policy differs")
        _require(background.get("first_native_node_mm") == 60. + cell[0]
                 and background.get("v1_segment_points") == [[60. + cell[0], 40.], [80., 40.]],
                 "background native-node provenance differs")
    policy = (background["source_policy"] if background is not None else
              source.get("source", {}).get("symmetry_policy", source.get("generation", {}).get("symmetry_policy")))
    hf_arrays = {"solid": arrays["solid"], "design": arrays["design_domain"],
                 "passive_solid": arrays["passive_solid"], "passive_void": arrays["passive_void"]}
    metadata = dict(schema_version="hf-geometry-1.0", case_family=family,
        grid=dict(shape_yx=[ny, nx], origin_mm=grid["origin_mm"], cell_size_mm=grid["cell_mm"],
                  axes=[[1., 0.], [0., 1.]], extent_mm=grid["domain_mm"], array_order="C_yx_bottom_up", value_location="cell"),
        thickness_mm=grid["thickness_mm"], model_extent=dict(kind="lower_half", symmetry_axis=dict(normal=[0., 1.], offset_mm=40.)),
        region_tags=tags, source_record_ids=[source["design_id"]],
        processing=dict(source_kind="ordinary_LF_v2_package", source_native_grid_preserved=True,
            lossless_bool_to_uint8=True, new_threshold_or_cleanup_applied=False,
            support_attachment="solid_incident", source_symmetry_policy=policy, background_boundary_applied=False,
            task_policy="Source boundary metadata is provenance; no HF task or applied constraints are created"),
        provenance=dict(lf_v2=dict(schema=LF_SCHEMA, design_id=source["design_id"], geometry_id=source["geometry_id"],
            descriptor_sha256=descriptor_sha, array_file_sha256=array_sha,
            descriptor_path="sources/design.json", array_path="sources/design.npz", descriptor=source)))
    hf_geometry_id(metadata, hf_arrays)  # Validate all metadata before creating any output.
    geometry = Geometry(metadata, hf_arrays, source_descriptor)
    for tag in tags.values():
        region_nodes(geometry, tag)
    for name in ("input", "output"):
        _, _, weights = port_vector(geometry, tags[name])
        example = np.asarray(regions[name + "_port"]["native_weights_example"], dtype=float)
        _require(example.shape == weights.shape and np.allclose(example, weights, rtol=0., atol=32*np.finfo(float).eps),
                 name + " native_weights_example disagrees with reference arclength averaging")
    output_directory.mkdir(parents=True, exist_ok=False)
    source_directory = output_directory / "sources"
    source_directory.mkdir()
    (source_directory / "design.json").write_bytes(descriptor_bytes)
    (source_directory / "design.npz").write_bytes(array_bytes)
    return write_geometry(output_directory, metadata, hf_arrays)
