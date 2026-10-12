"""Native Q1 geometry and port preparation; no material, task or applied BCs."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
import json
from numbers import Real
from pathlib import Path

import numpy as np

from .data import ARRAY_NAMES, Geometry, GeometryError, canonical_hash, load_geometry
from .regions import active_nodes, element_connectivity, node_coordinates, port_vector, region_nodes


SCHEMA_VERSION = "hf-native-geometry-map-1.0"


@dataclass(frozen=True)
class NativeGeometryMap:
    geometry: Geometry
    arrays: dict[str, np.ndarray]
    metadata: dict


def _require(condition, message):
    if not condition:
        raise GeometryError("Native geometry map: " + message)


def _background_source(geometry, coordinates):
    lf = geometry.metadata.get("provenance", {}).get("lf_v2")
    if lf is None:
        return None, np.empty(0, dtype=np.int64)
    _require(isinstance(lf, dict) and lf.get("schema") == "dmftd.hf_export.v2", "invalid LF v2 provenance")
    background = lf["descriptor"]["regions_mm"]["symmetry_background"]
    if background is None:
        return None, np.empty(0, dtype=np.int64)
    _require(isinstance(background, dict) and background.get("kind") == "complement_on_line"
             and background.get("interval") == "open_closed", "unsupported background source interval")
    line = background["line"]
    _require(line.get("axis") in {"x", "y"}, "background source line must be axis-aligned")
    fixed_axis = {"x": 0, "y": 1}[line["axis"]]
    varying_axis = 1 - fixed_axis
    start, end, value = background["start_exclusive_mm"], background["end_inclusive_mm"], line["value_mm"]
    _require(all(isinstance(v, Real) and not isinstance(v, bool) and np.isfinite(v) for v in (start, end, value))
             and start < end, "invalid background source endpoints")
    points = np.zeros((2, 2))
    points[:, fixed_axis] = value
    points[:, varying_axis] = [start, end]
    closed_nodes = region_nodes(geometry, {"points_mm": points.tolist()})
    # Source start is open. Native helper coordinates are provenance only.
    nodes = closed_nodes[coordinates[closed_nodes, varying_axis] > start]
    return deepcopy(background), nodes.astype(np.int64)


def prepare_native_geometry(geometry_file) -> NativeGeometryMap:
    """Read an HF package and describe its unchanged native cell/node mapping."""
    descriptor = Path(geometry_file)
    if descriptor.is_dir():
        descriptor = descriptor / "geometry.json"
    descriptor_bytes = descriptor.read_bytes()
    geometry = load_geometry(descriptor)
    _require(descriptor_bytes == geometry.path.read_bytes(), "source descriptor changed while reading")
    array_name = geometry.metadata["arrays"]["path"]
    array_bytes = geometry.path.with_name(array_name).read_bytes()
    _require(sha256(array_bytes).hexdigest() == geometry.metadata["arrays"]["sha256"], "source NPZ changed while reading")
    coordinates = node_coordinates(geometry).astype(np.float64, copy=False)
    connectivity = element_connectivity(geometry).astype(np.int64, copy=False)
    incident = active_nodes(geometry)
    tags = geometry.metadata["region_tags"]
    _require({"support", "input", "output"} <= tags.keys(), "support/input/output region tags are required")
    arrays = dict(coordinates_mm=coordinates, connectivity=connectivity,
                  **{name: geometry.arrays[name] for name in ARRAY_NAMES}, solid_incident=incident.astype(np.uint8))
    for name in ("support", "symmetry"):
        nodes = region_nodes(geometry, tags[name]).astype(np.int64, copy=False) if name in tags else np.empty(0, dtype=np.int64)
        arrays[name + "_nodes"] = nodes
        arrays[name + "_solid_nodes"] = nodes[incident[nodes]]
    for name in ("input", "output"):
        vector, nodes, weights = port_vector(geometry, tags[name])
        nodes = nodes.astype(np.int64, copy=False)
        arrays.update({name + "_vector": vector, name + "_nodes": nodes, name + "_weights": weights})
    background, nodes = _background_source(geometry, coordinates)
    arrays.update(background_source_nodes=nodes, background_source_solid_nodes=nodes[incident[nodes]])
    for array in arrays.values():
        array.setflags(write=False)
    counts = dict(elements=len(connectivity), nodes=len(coordinates), dofs=2*len(coordinates),
                  **{name + "_cells": int(geometry.arrays[name].sum()) for name in ARRAY_NAMES})
    for name in ("support_nodes", "support_solid_nodes", "symmetry_nodes", "symmetry_solid_nodes",
                 "input_nodes", "output_nodes", "background_source_nodes", "background_source_solid_nodes"):
        counts[name] = len(arrays[name])
    metadata = dict(schema_version=SCHEMA_VERSION, geometry_metadata=deepcopy(geometry.metadata),
        source_geometry_id=geometry.geometry_id, source_geometry_file_sha256=sha256(descriptor_bytes).hexdigest(),
        source_geometry_descriptor_sha256=geometry.metadata["descriptor_sha256"],
        source_geometry_npz_sha256=sha256(array_bytes).hexdigest(),
        source_geometry_snapshot=dict(descriptor_path="source_geometry/geometry.json", array_path="source_geometry/"+array_name),
        source_provenance_path_context="Paths inside geometry_metadata provenance belong to the original source context; they are not resolved or read by this map",
        counts=counts, grid=deepcopy(geometry.grid), thickness_mm=geometry.metadata["thickness_mm"],
        model_extent=deepcopy(geometry.metadata["model_extent"]), element_node_order=["BL", "BR", "TR", "TL"],
        dof_order="interleaved ux,uy; dof = 2*node + component", native_geometry_preserved=True,
        background_source=background, background_source_role="source-only candidate nodes; no applied constraint",
        candidate_node_role="support/symmetry subsets describe geometry attachment only; no fixed/free DOFs are created",
        constraints_applied=False, material_assigned=False, task_created=False, analysis_grid_policy="not_selected")
    return NativeGeometryMap(geometry, arrays, metadata)


def write_native_geometry_map(mapping: NativeGeometryMap, output_directory) -> Path:
    """Save a new map package with an independently loadable HF source snapshot."""
    descriptor_bytes = mapping.geometry.path.read_bytes()
    array_name = mapping.geometry.metadata["arrays"]["path"]
    array_bytes = mapping.geometry.path.with_name(array_name).read_bytes()
    _require(sha256(descriptor_bytes).hexdigest() == mapping.metadata["source_geometry_file_sha256"],
             "source descriptor changed after preparation")
    _require(sha256(array_bytes).hexdigest() == mapping.metadata["source_geometry_npz_sha256"],
             "source NPZ changed after preparation")
    buffer = BytesIO()
    np.savez_compressed(buffer, **mapping.arrays)
    payload = buffer.getvalue()
    metadata = deepcopy(mapping.metadata)
    metadata["arrays"] = dict(path="map.npz", sha256=sha256(payload).hexdigest(),
        fields={name: dict(dtype=array.dtype.name, shape=list(array.shape), sha256=sha256(array.tobytes(order="C")).hexdigest())
                for name, array in mapping.arrays.items()})
    metadata["descriptor_sha256"] = canonical_hash(metadata)
    descriptor_text = json.dumps(metadata, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=False)
    source = output / "source_geometry"
    source.mkdir()
    (source / "geometry.json").write_bytes(descriptor_bytes)
    (source / array_name).write_bytes(array_bytes)
    (output / "map.npz").write_bytes(payload)
    (output / "map.json").write_text(descriptor_text, encoding="utf-8")
    return (output / "map.json").resolve()
