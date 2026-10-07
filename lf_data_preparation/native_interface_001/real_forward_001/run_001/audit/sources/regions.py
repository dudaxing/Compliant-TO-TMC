"""Physical grid regions, generalized ports, and diagnostic qualification."""

from __future__ import annotations

from collections import deque
from copy import deepcopy

import numpy as np

from .data import Geometry, GeometryError


def node_coordinates(geometry: Geometry) -> np.ndarray:
    ny, nx = geometry.grid["shape_yx"]
    x0, y0 = geometry.grid["origin_mm"]
    dx, dy = geometry.grid["cell_size_mm"]
    xx, yy = np.meshgrid(x0 + np.arange(nx + 1) * dx, y0 + np.arange(ny + 1) * dy)
    return np.column_stack((xx.ravel(), yy.ravel()))


def element_connectivity(geometry: Geometry) -> np.ndarray:
    ny, nx = geometry.grid["shape_yx"]
    jj, ii = np.meshgrid(np.arange(ny), np.arange(nx), indexing="ij")
    bl = (jj * (nx + 1) + ii).ravel()
    return np.column_stack((bl, bl + 1, bl + nx + 2, bl + nx + 1))


def active_nodes(geometry: Geometry) -> np.ndarray:
    ny, nx = geometry.grid["shape_yx"]
    active = np.zeros((ny + 1) * (nx + 1), dtype=bool)
    active[element_connectivity(geometry)[geometry.solid.ravel().astype(bool)].ravel()] = True
    return active


def region_nodes(geometry: Geometry, tag: dict) -> np.ndarray:
    try:
        points = np.asarray(tag["points_mm"], dtype=float)
    except (KeyError, TypeError, ValueError) as error:
        raise GeometryError("Region must have numeric points_mm") from error
    if points.shape != (2, 2) or not np.all(np.isfinite(points)):
        raise GeometryError("Region requires two finite points_mm")
    difference = points[1] - points[0]
    if np.count_nonzero(difference) != 1:
        raise GeometryError("Only nonzero axis-aligned segments are supported")
    ny, nx = geometry.grid["shape_yx"]
    logical = (points - geometry.grid["origin_mm"]) / geometry.grid["cell_size_mm"]
    nearest = np.rint(logical)
    # This only absorbs binary64 arithmetic, never a geometric nearest-node move.
    tolerance = 64 * np.finfo(float).eps * max(nx, ny, 1)
    if np.any(np.abs(logical - nearest) > tolerance):
        raise GeometryError("Region endpoints must coincide with grid nodes; snapping is not supported")
    if np.any(nearest < 0) or np.any(nearest > np.array([nx, ny])):
        raise GeometryError("Region lies outside the geometry grid")
    start, stop = nearest.astype(np.int64)
    varying = 0 if difference[0] != 0 else 1
    sign = 1 if stop[varying] > start[varying] else -1
    values = np.arange(start[varying], stop[varying] + sign, sign)
    if varying == 0:
        return start[1] * (nx + 1) + values
    return values * (nx + 1) + start[0]


def port_vector(geometry: Geometry, tag: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    nodes = region_nodes(geometry, tag)
    if tag.get("averaging") != "normalized_reference_arclength_trapezoid":
        raise GeometryError("Unsupported port averaging rule")
    direction = np.asarray(tag.get("direction"), dtype=float)
    if direction.shape != (2,) or not np.all(np.isfinite(direction)) or not np.isclose(
        np.linalg.norm(direction), 1.0, rtol=0.0, atol=1e-12
    ):
        raise GeometryError("Port direction must be a finite unit vector")
    coordinates = node_coordinates(geometry)
    interval_lengths = np.linalg.norm(np.diff(coordinates[nodes], axis=0), axis=1)
    weights = np.zeros(len(nodes))
    weights[:-1] += interval_lengths / 2.0
    weights[1:] += interval_lengths / 2.0
    weights /= interval_lengths.sum()
    vector = np.zeros(2 * len(coordinates))
    vector[2 * nodes] = weights * direction[0]
    vector[2 * nodes + 1] = weights * direction[1]
    return vector, nodes, weights


def _components(solid: np.ndarray, diagonal: bool = False) -> tuple[np.ndarray, int]:
    labels = np.zeros(solid.shape, dtype=np.int32)
    neighbors = ((-1, 0), (1, 0), (0, -1), (0, 1))
    if diagonal:
        neighbors += ((-1, -1), (-1, 1), (1, -1), (1, 1))
    ny, nx = solid.shape
    count = 0
    for j, i in np.argwhere(solid):
        if labels[j, i]:
            continue
        count += 1
        labels[j, i] = count
        queue = deque([(int(j), int(i))])
        while queue:
            y, x = queue.popleft()
            for dj, di in neighbors:
                y2, x2 = y + dj, x + di
                if 0 <= y2 < ny and 0 <= x2 < nx and solid[y2, x2] and not labels[y2, x2]:
                    labels[y2, x2] = count
                    queue.append((y2, x2))
    return labels, count


def qualify_geometry(geometry: Geometry, criteria: dict | None = None) -> dict:
    criteria = deepcopy(criteria) if criteria is not None else {}
    if not isinstance(criteria, dict) or set(criteria) - {"max_design_volume_fraction", "min_feature_mm"}:
        raise GeometryError("Unsupported qualification criteria")
    for name, limit in criteria.items():
        if limit is not None and (
            isinstance(limit, bool) or not isinstance(limit, (int, float)) or not np.isfinite(limit)
            or (name == "max_design_volume_fraction" and not 0 <= limit <= 1)
            or (name == "min_feature_mm" and limit <= 0)
        ):
            raise GeometryError(f"Invalid qualification criterion {name}")
    solid = geometry.solid.astype(bool)
    labels, count4 = _components(solid)
    _, count8 = _components(solid, diagonal=True)
    a, b, c, d = solid[:-1, :-1], solid[:-1, 1:], solid[1:, :-1], solid[1:, 1:]
    diagonals = (a & d & ~b & ~c) | (b & c & ~a & ~d)
    diagonal_locations = np.argwhere(diagonals).tolist()
    arrays = geometry.arrays
    design = arrays["design"].astype(bool)
    nsolid, ndesign = int(solid.sum()), int(design.sum())
    ndesign_solid = int((solid & design).sum())
    dx, dy = geometry.grid["cell_size_mm"]
    area = dx * dy
    thickness = geometry.metadata["thickness_mm"]
    fraction = ndesign_solid / ndesign if ndesign else None
    measurements = {
        "solid_cells": nsolid, "design_cells": ndesign, "design_solid_cells": ndesign_solid,
        "passive_solid_cells": int(arrays["passive_solid"].sum()),
        "passive_void_cells": int(arrays["passive_void"].sum()),
        "solid_area_mm2": nsolid * area, "solid_volume_mm3": nsolid * area * thickness,
        "design_area_mm2": ndesign * area, "design_solid_area_mm2": ndesign_solid * area,
        "design_volume_fraction": fraction, "envelope_volume_fraction": nsolid / solid.size,
        "components_4": count4, "components_8": count8,
        "local_diagonal_only_patterns": len(diagonal_locations),
        "diagonal_pattern_lower_left_cells_yx": diagonal_locations,
        "min_feature_mm": None,
    }
    checks = {
        "shared_edge_connectivity": {
            "status": "pass" if count4 == 1 else "fail", "components": count4,
            "requirement": "one shared-edge-connected mechanism body; separate workpieces are not part of solid",
        }
    }
    connectivity = element_connectivity(geometry)
    active = active_nodes(geometry)
    node_components = [set() for _ in active]
    for cell in np.flatnonzero(solid.ravel()):
        component = int(labels.ravel()[cell])
        for node in connectivity[cell]:
            node_components[node].add(component)
    regions = {}
    tags = geometry.metadata["region_tags"]
    for name in ("support", "input", "output"):
        try:
            if name not in tags:
                raise GeometryError(f"Missing region tag {name}")
            if name in ("input", "output"):
                _, selected, weights = port_vector(geometry, tags[name])
            else:
                selected = region_nodes(geometry, tags[name])
                weights = None
            attached = selected[active[selected]]
            components = sorted(set().union(*(node_components[node] for node in attached)))
            entry = {
                "selected_node_count": len(selected), "attached_node_count": len(attached),
                "selected_nodes": selected.tolist(), "attached_nodes": attached.tolist(),
                "component_ids_4": components,
            }
            if weights is not None:
                entry["weights"] = weights.tolist()
            regions[name] = entry
            valid = len(attached) >= 2 if name == "support" else len(attached) == len(selected)
            checks[f"{name}_attachment"] = {
                "status": "pass" if valid else "fail",
                "requirement": "at least two attached distinct nodes for interface smoke only" if name == "support" else "all original weighted port nodes attached to solid",
            }
        except GeometryError as error:
            regions[name] = {"error": str(error), "component_ids_4": []}
            checks[f"{name}_attachment"] = {"status": "fail", "reason": str(error)}
    shared = set(regions["support"]["component_ids_4"])
    for name in ("input", "output"):
        shared.intersection_update(regions[name]["component_ids_4"])
    measurements["common_support_port_component_ids_4"] = sorted(shared)
    checks["port_support_component_link"] = {"status": "pass" if shared else "fail"}
    maximum = criteria.get("max_design_volume_fraction")
    checks["design_volume_fraction"] = {
        "status": "pending" if maximum is None or fraction is None else ("pass" if fraction <= maximum else "fail"),
        "value": fraction, "maximum": maximum,
    }
    checks["min_feature"] = {
        "status": "pending", "minimum_mm": criteria.get("min_feature_mm"),
        "reason": "No validated minimum-feature measurement in HF-1; connectivity is not manufacturing qualification",
    }
    statuses = [check["status"] for check in checks.values()]
    status = "fail" if "fail" in statuses else ("pending" if "pending" in statuses else "pass")
    return {"status": status, "measurements": measurements, "criteria": criteria, "checks": checks, "regions": regions}
