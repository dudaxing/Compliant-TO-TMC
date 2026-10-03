"""Portable binary-cell geometry records, independent of any geometry producer."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from typing import Any
from zipfile import BadZipFile

import numpy as np


ARRAY_NAMES = ("solid", "design", "passive_solid", "passive_void")
SCHEMA_VERSION = "hf-geometry-1.0"


class GeometryError(ValueError):
    """A geometry record is invalid, unsupported, or fails integrity checks."""


@dataclass(frozen=True)
class Geometry:
    metadata: dict
    arrays: dict[str, np.ndarray]
    path: Path

    @property
    def solid(self) -> np.ndarray:
        return self.arrays["solid"]

    @property
    def grid(self) -> dict:
        return self.metadata["grid"]

    @property
    def geometry_id(self) -> str:
        return self.metadata["geometry_id"]


def _canonical(value: Any) -> Any:
    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            raise GeometryError("JSON object keys must be strings")
        return {key: _canonical(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_canonical(item) for item in value]
    if isinstance(value, (float, np.floating)):
        number = float(value)
        if not np.isfinite(number):
            raise GeometryError("Non-finite numeric metadata is not allowed")
        return (0.0 if number == 0.0 else number).hex()
    if isinstance(value, np.integer):
        return int(value)
    if value is None or isinstance(value, (str, int, bool)):
        return value
    raise GeometryError(f"Unsupported metadata value type: {type(value).__name__}")


def _canonical_bytes(obj: Any) -> bytes:
    return json.dumps(
        _canonical(obj), sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False,
    ).encode("utf-8")


def canonical_hash(obj: Any) -> str:
    """SHA256 of sorted compact UTF-8 JSON with floats encoded by float.hex."""
    return sha256(_canonical_bytes(obj)).hexdigest()


def _number(value: Any, label: str, *, positive: bool = False) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(
        value, (int, float, np.integer, np.floating)
    ):
        raise GeometryError(f"{label} must be a finite number")
    result = float(value)
    if not np.isfinite(result) or (positive and result <= 0.0):
        raise GeometryError(f"{label} must be finite" + (" and positive" if positive else ""))
    return 0.0 if result == 0.0 else result


def _vector(value: Any, label: str, *, positive: bool = False) -> list[float]:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise GeometryError(f"{label} must have exactly two components")
    return [_number(item, label, positive=positive) for item in value]


def _normalize_metadata(metadata: dict) -> dict:
    if not isinstance(metadata, dict):
        raise GeometryError("Geometry metadata must be an object")
    result = deepcopy(metadata)
    if result.get("schema_version") != SCHEMA_VERSION:
        raise GeometryError(f"Unsupported schema_version; expected {SCHEMA_VERSION}")
    if not isinstance(result.get("case_family"), str) or not result["case_family"]:
        raise GeometryError("case_family must be a nonempty string")
    if result.get("length_unit", "mm") != "mm":
        raise GeometryError("Only millimetre geometry units are supported")
    grid = result.get("grid")
    if not isinstance(grid, dict):
        raise GeometryError("grid must be an object")
    shape = grid.get("shape_yx")
    if not isinstance(shape, (list, tuple)) or len(shape) != 2:
        raise GeometryError("grid.shape_yx must contain two positive integers")
    if any(isinstance(n, (bool, np.bool_)) or not isinstance(n, (int, np.integer)) or n <= 0 for n in shape):
        raise GeometryError("grid.shape_yx must contain two positive integers")
    grid["shape_yx"] = [int(n) for n in shape]
    grid["origin_mm"] = _vector(grid.get("origin_mm"), "grid.origin_mm")
    grid["cell_size_mm"] = _vector(grid.get("cell_size_mm"), "grid.cell_size_mm", positive=True)
    grid["extent_mm"] = _vector(grid.get("extent_mm"), "grid.extent_mm", positive=True)
    axes = grid.get("axes")
    if not isinstance(axes, (list, tuple)) or len(axes) != 2:
        raise GeometryError("grid.axes must be [[1,0],[0,1]]")
    axes = [_vector(axis, "grid.axes") for axis in axes]
    if axes != [[1.0, 0.0], [0.0, 1.0]]:
        raise GeometryError("Only +x right, +y up geometry axes are supported")
    grid["axes"] = axes
    if grid.get("array_order") != "C_yx_bottom_up" or grid.get("value_location") != "cell":
        raise GeometryError("Geometry must use C_yx_bottom_up order and cell values")
    ny, nx = grid["shape_yx"]
    dx, dy = grid["cell_size_mm"]
    expected = np.array([nx * dx, ny * dy])
    if not np.allclose(grid["extent_mm"], expected, rtol=1e-12, atol=0.0):
        raise GeometryError("grid.extent_mm disagrees with shape_yx and cell_size_mm")
    result["thickness_mm"] = _number(result.get("thickness_mm"), "thickness_mm", positive=True)
    extent = result.get("model_extent")
    if not isinstance(extent, dict) or extent.get("kind") not in {"full", "lower_half"}:
        raise GeometryError("model_extent.kind must be full or lower_half in v1")
    if extent["kind"] == "lower_half":
        axis = extent.get("symmetry_axis")
        if not isinstance(axis, dict):
            raise GeometryError("lower_half geometry requires symmetry_axis")
        axis["normal"] = _vector(axis.get("normal"), "symmetry_axis.normal")
        axis["offset_mm"] = _number(axis.get("offset_mm"), "symmetry_axis.offset_mm")
        if axis["normal"] != [0.0, 1.0] or not np.isclose(
            axis["offset_mm"], grid["origin_mm"][1] + expected[1], rtol=0.0, atol=1e-12 * dy
        ):
            raise GeometryError("lower_half symmetry axis must be the top horizontal grid boundary")
    elif "symmetry_axis" in extent:
        raise GeometryError("full geometry must not declare an implicit symmetry axis")
    tags = result.get("region_tags")
    if not isinstance(tags, dict):
        raise GeometryError("region_tags must be an object")
    for name, tag in tags.items():
        if not isinstance(name, str) or not isinstance(tag, dict):
            raise GeometryError("region_tags entries must be named objects")
        points = tag.get("points_mm")
        if not isinstance(points, (list, tuple)) or len(points) != 2:
            raise GeometryError(f"Region {name} must contain two points_mm")
        points = [_vector(point, f"{name}.points_mm") for point in points]
        delta = np.subtract(points[1], points[0])
        if np.count_nonzero(delta) != 1:
            raise GeometryError(f"Region {name} must be a nonzero axis-aligned segment")
        tag["points_mm"] = points
        if "direction" in tag:
            tag["direction"] = _vector(tag["direction"], f"{name}.direction")
            if not np.isclose(np.linalg.norm(tag["direction"]), 1.0, rtol=0.0, atol=1e-12):
                raise GeometryError(f"Port {name} direction must be a unit vector")
            if tag.get("averaging") != "normalized_reference_arclength_trapezoid":
                raise GeometryError(f"Port {name} has unsupported averaging")
        elif "components" in tag:
            components = tag["components"]
            if not isinstance(components, list) or not components or any(
                isinstance(c, bool) or not isinstance(c, int) or c not in (0, 1) for c in components
            ) or len(set(components)) != len(components):
                raise GeometryError(f"Region {name} components must be unique entries from [0,1]")
        else:
            raise GeometryError(f"Region {name} requires direction or components")
    if extent["kind"] == "lower_half":
        symmetry = tags.get("symmetry")
        if not isinstance(symmetry, dict) or symmetry.get("components") != [1] or "direction" in symmetry:
            raise GeometryError("lower_half requires a symmetry constraint tag with components [1]")
        symmetry_points = np.asarray(symmetry["points_mm"])
        top = extent["symmetry_axis"]["offset_mm"]
        if not np.allclose(symmetry_points[:, 1], top, rtol=0.0, atol=1e-12 * dy):
            raise GeometryError("lower_half symmetry tag must lie on the declared top symmetry axis")
        logical_x = (symmetry_points[:, 0] - grid["origin_mm"][0]) / dx
        rounded_x = np.rint(logical_x)
        if np.any(np.abs(logical_x - rounded_x) > 64 * np.finfo(float).eps * max(nx, ny, 1)) or np.any(
            (rounded_x < 0) | (rounded_x > nx)
        ):
            raise GeometryError("lower_half symmetry endpoints must coincide with in-domain grid nodes")
    _canonical_bytes(result)  # Also reject non-finite values hidden in provenance.
    return result


def _validated_arrays(arrays: dict, shape: list[int], *, require_uint8: bool = False) -> dict[str, np.ndarray]:
    if not isinstance(arrays, dict) or set(arrays) != set(ARRAY_NAMES):
        raise GeometryError(f"Exactly these arrays are required: {ARRAY_NAMES}")
    clean = {}
    for name in ARRAY_NAMES:
        array = np.asarray(arrays[name])
        if array.shape != tuple(shape):
            raise GeometryError(f"Array {name} has shape {array.shape}; expected {tuple(shape)}")
        if array.dtype.kind not in "buif" or (require_uint8 and array.dtype != np.dtype("uint8")):
            raise GeometryError(f"Array {name} must contain binary numeric values" + (" stored as uint8" if require_uint8 else ""))
        if not np.all(np.isfinite(array)) or not np.all((array == 0) | (array == 1)):
            raise GeometryError(f"Array {name} contains non-binary or non-finite values")
        clean[name] = np.array(array, dtype=np.uint8, order="C", copy=True)
    partition = clean["design"] + clean["passive_solid"] + clean["passive_void"]
    if not np.all(partition == 1):
        raise GeometryError("design/passive_solid/passive_void must partition every cell exactly once")
    if np.any(clean["passive_solid"] > clean["solid"]) or np.any(clean["passive_void"] & clean["solid"]):
        raise GeometryError("Passive masks contradict solid geometry")
    return clean


def _authority_header(metadata: dict) -> dict:
    grid = metadata["grid"]
    return {
        "schema_version": metadata["schema_version"],
        "grid": {name: grid[name] for name in (
            "shape_yx", "origin_mm", "cell_size_mm", "axes", "extent_mm", "array_order", "value_location"
        )},
        "thickness_mm": metadata["thickness_mm"],
        "model_extent": metadata["model_extent"],
    }


def _geometry_hash(metadata: dict, arrays: dict) -> str:
    digest = sha256(b"hf-geometry-1.0\x00")
    header = _canonical_bytes(_authority_header(metadata))
    digest.update(len(header).to_bytes(8, "big"))
    digest.update(header)
    for name in ARRAY_NAMES:
        payload = arrays[name].tobytes(order="C")
        digest.update(name.encode("ascii") + b"\x00")
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


def geometry_id(metadata: dict, arrays: dict) -> str:
    """Identity of the immutable authority grid, excluding tags and provenance."""
    normalized = _normalize_metadata(metadata)
    binary = _validated_arrays(arrays, normalized["grid"]["shape_yx"])
    return _geometry_hash(normalized, binary)


def _field_info(array: np.ndarray) -> dict:
    return {"shape": list(array.shape), "dtype": "uint8", "sha256": sha256(array.tobytes(order="C")).hexdigest()}


def write_geometry(directory: str | Path, metadata: dict, arrays: dict) -> Path:
    """Write a validated self-contained descriptor and ordinary NPZ array file."""
    normalized = _normalize_metadata(metadata)
    binary = _validated_arrays(arrays, normalized["grid"]["shape_yx"])
    normalized.pop("descriptor_sha256", None)
    normalized["geometry_id"] = _geometry_hash(normalized, binary)
    buffer = BytesIO()
    np.savez_compressed(buffer, **binary)
    payload = buffer.getvalue()
    normalized["arrays"] = {
        "path": "geometry.npz", "sha256": sha256(payload).hexdigest(),
        "fields": {name: _field_info(binary[name]) for name in ARRAY_NAMES},
    }
    normalized["descriptor_sha256"] = canonical_hash(normalized)
    try:
        serialized = json.dumps(normalized, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    except (TypeError, ValueError) as error:
        raise GeometryError(f"Metadata is not ordinary JSON: {error}") from error
    target = Path(directory)
    target.mkdir(parents=True, exist_ok=True)
    array_path = target / "geometry.npz"
    descriptor_path = target / "geometry.json"
    if array_path.is_symlink() or descriptor_path.is_symlink():
        raise GeometryError("Writer does not overwrite symbolic links")
    array_path.write_bytes(payload)
    descriptor_path.write_text(serialized, encoding="utf-8")
    return descriptor_path.resolve()


def _json_object(pairs: list[tuple]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise GeometryError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _array_path(descriptor: Path, value: Any) -> Path:
    # V1 deliberately permits only a file name next to geometry.json.
    if not isinstance(value, str) or value in ("", ".", "..") or any(c in value for c in "/\\:"):
        raise GeometryError("arrays.path must be a same-directory relative file name")
    result = descriptor.parent / value
    if result.resolve().parent != descriptor.parent.resolve():
        raise GeometryError("Array path resolves outside the geometry package")
    return result


def load_geometry(path: str | Path) -> Geometry:
    descriptor = Path(path)
    if descriptor.is_dir():
        descriptor = descriptor / "geometry.json"
    if descriptor.is_symlink():
        raise GeometryError("Geometry descriptor must be a regular local file, not a symbolic link")
    descriptor = descriptor.resolve()
    try:
        metadata = json.loads(descriptor.read_text(encoding="utf-8"), object_pairs_hook=_json_object)
        if not isinstance(metadata, dict):
            raise GeometryError("Geometry descriptor must be an object")
        supplied_descriptor_hash = metadata.get("descriptor_sha256")
        unsigned = {key: value for key, value in metadata.items() if key != "descriptor_sha256"}
        if supplied_descriptor_hash != canonical_hash(unsigned):
            raise GeometryError("descriptor_sha256 mismatch")
        normalized = _normalize_metadata(metadata)
        definition = normalized.get("arrays")
        if not isinstance(definition, dict) or not isinstance(definition.get("fields"), dict):
            raise GeometryError("arrays must declare path, sha256, and fields")
        array_path = _array_path(descriptor, definition.get("path"))
        payload = array_path.read_bytes()
        if sha256(payload).hexdigest() != definition.get("sha256"):
            raise GeometryError("NPZ file sha256 mismatch")
        with np.load(BytesIO(payload), allow_pickle=False) as archive:
            if set(archive.files) != set(ARRAY_NAMES) or len(archive.files) != len(ARRAY_NAMES):
                raise GeometryError("NPZ field names do not match the four authority arrays")
            arrays = _validated_arrays(
                {name: archive[name] for name in ARRAY_NAMES}, normalized["grid"]["shape_yx"], require_uint8=True,
            )
        if set(definition["fields"]) != set(ARRAY_NAMES):
            raise GeometryError("Array field declarations do not match authority arrays")
        for name in ARRAY_NAMES:
            if definition["fields"][name] != _field_info(arrays[name]):
                raise GeometryError(f"Array {name} content hash or declaration mismatch")
        if normalized.get("geometry_id") != _geometry_hash(normalized, arrays):
            raise GeometryError("geometry_id mismatch")
    except GeometryError:
        raise
    except (OSError, ValueError, TypeError, KeyError, EOFError, BadZipFile) as error:
        raise GeometryError(f"Cannot read geometry {descriptor}: {error}") from error
    for array in arrays.values():
        array.setflags(write=False)
    return Geometry(normalized, arrays, descriptor)
