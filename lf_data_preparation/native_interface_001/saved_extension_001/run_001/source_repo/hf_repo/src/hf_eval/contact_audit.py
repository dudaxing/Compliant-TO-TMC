"""Limited geometry and path-validity diagnostics, with no mechanics imports.

The geometry audit intersects straight-sided, strictly counterclockwise convex
Q4 cells with one axis-aligned rigid rectangle. It does not test self-contact,
solid/solid intersection, or the accuracy of a contact force. Coordinates are
the explicitly supplied binary64 geometry; callers using split displacement
must separately account for any rounding when producing these coordinates.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
import math

import numpy as np


def _finite_scalar(value, name):
    raw = np.asarray(value)
    if raw.shape != () or raw.dtype.kind not in "iuf":
        raise ValueError(f"{name} must be a finite real scalar")
    number = float(raw)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be a finite real scalar")
    return number


def _tolerance(value, name):
    number = _finite_scalar(value, name)
    if number < 0:
        raise ValueError(f"{name} must be nonnegative")
    return number


def _cross(a, b):
    return float(a[0] * b[1] - a[1] * b[0])


def _signed_area(points):
    """Triangle fan around the first vertex avoids a global shoelace subtraction."""
    if len(points) < 3:
        return 0.0
    edges = points[1:] - points[0]
    terms = [_cross(a, b) for a, b in zip(edges[:-1], edges[1:])]
    if not all(math.isfinite(x) for x in terms):
        raise ArithmeticError("nonfinite area arithmetic")
    area = 0.5 * math.fsum(terms)
    if not math.isfinite(area):
        raise ArithmeticError("nonfinite area arithmetic")
    return area


def _quad_local(quad, length_tolerance, area_tolerance):
    local = quad - quad[0]
    edges = np.roll(local, -1, axis=0) - local
    if not np.all(np.isfinite(local)) or not np.all(np.isfinite(edges)):
        return None, None, "nonfinite_geometry_arithmetic"
    lengths = np.hypot(edges[:, 0], edges[:, 1])
    if not np.all(np.isfinite(lengths)):
        return None, None, "nonfinite_geometry_arithmetic"
    if np.any(lengths <= length_tolerance):
        return None, None, "short_or_repeated_edge"
    turns = np.array([_cross(a, b) for a, b in zip(edges, np.roll(edges, -1, axis=0))])
    if not np.all(np.isfinite(turns)):
        return None, None, "nonfinite_geometry_arithmetic"
    if np.all(turns < -area_tolerance):
        return None, None, "clockwise_orientation"
    if np.any(np.abs(turns) <= area_tolerance):
        return None, None, "degenerate_or_collinear_corner"
    if not np.all(turns > area_tolerance):
        return None, None, "nonconvex_or_self_intersecting"
    area = _signed_area(local)
    if area <= area_tolerance:
        return None, None, "degenerate_area"
    return local, area, None


def _clip_halfplane(points, axis, bound, keep_above):
    if not len(points):
        return points
    output = []
    previous = points[-1]
    previous_inside = previous[axis] >= bound if keep_above else previous[axis] <= bound
    for current in points:
        inside = current[axis] >= bound if keep_above else current[axis] <= bound
        if inside != previous_inside:
            denominator = current[axis] - previous[axis]
            ratio = (bound - previous[axis]) / denominator
            crossing = (1.0 - ratio) * previous + ratio * current
            crossing[axis] = bound
            if not math.isfinite(float(ratio)) or not np.all(np.isfinite(crossing)):
                raise ArithmeticError("nonfinite clipping arithmetic")
            output.append(crossing)
        if inside:
            output.append(current.copy())
        previous, previous_inside = current, inside
    return np.asarray(output, dtype=np.float64).reshape(-1, 2)


def audit_rectangle_overlap(coordinates, connectivity, solid_mask, rectangle, *,
                            length_tolerance, area_tolerance, overlap_tolerance):
    """Audit supplied Q4 geometry against ``(xmin, xmax, ymin, ymax)``.

    ``length_tolerance`` bounds short edges; ``area_tolerance`` bounds polygon
    area and corner cross-products (twice signed triangle area). A cell must be
    strictly CCW and convex. ``overlap_tolerance`` bounds the sum of intersection
    areas. All three tolerances are mandatory, finite, nonnegative, and in the
    coordinate units or their square. The rectangle is NOT expanded by them.

    Bad input schemas/nonfinite inputs raise ValueError. Invalid solid cells or
    nonfinite geometric arithmetic instead yield ``evaluable=False`` and None
    for overall validity/area, never a zero-overlap pass. Per-cell evidence is
    retained. The total is a SUM over cells, not a union: overlapping solids can
    be counted twice because self-intersection is outside this audit's scope.
    """
    lt = _tolerance(length_tolerance, "length_tolerance")
    at = _tolerance(area_tolerance, "area_tolerance")
    ot = _tolerance(overlap_tolerance, "overlap_tolerance")
    xy = np.asarray(coordinates)
    if xy.dtype != np.dtype(np.float64) or xy.ndim != 2 or xy.shape[1:] != (2,) or len(xy) < 4:
        raise ValueError("coordinates must have binary64 shape (n, 2), n >= 4")
    if not np.all(np.isfinite(xy)):
        raise ValueError("coordinates must be finite")
    cells = np.asarray(connectivity)
    if cells.dtype.kind not in "iu" or cells.ndim != 2 or cells.shape[1:] != (4,):
        raise ValueError("connectivity must have integer shape (ne, 4)")
    if np.any(cells < 0) or np.any(cells >= len(xy)):
        raise ValueError("connectivity contains an out-of-range node index")
    solid = np.asarray(solid_mask)
    if solid.dtype.kind != "b" or solid.shape != (len(cells),):
        raise ValueError("solid_mask must be boolean with one entry per cell")
    bounds = np.asarray(rectangle)
    if bounds.shape != (4,) or bounds.dtype.kind not in "iuf":
        raise ValueError("rectangle must be (xmin, xmax, ymin, ymax)")
    bounds = bounds.astype(np.float64)
    if not np.all(np.isfinite(bounds)):
        raise ValueError("rectangle must be finite")
    xmin, xmax, ymin, ymax = bounds
    if not (xmin < xmax and ymin < ymax):
        raise ValueError("rectangle must have positive width and height")

    records = []
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        for index in np.flatnonzero(solid):
            nodes = cells[index]
            record = dict(element_id=int(index), evaluable=False, reason=None,
                          cell_area=None, overlap_area=None)
            if len(set(int(n) for n in nodes)) != 4:
                record["reason"] = "repeated_node_index"
                records.append(record)
                continue
            quad = xy[nodes]
            try:
                local, area, reason = _quad_local(quad, lt, at)
                record["reason"] = reason
                if reason is None:
                    disjoint = (quad[:, 0].max() <= xmin or quad[:, 0].min() >= xmax
                                or quad[:, 1].max() <= ymin or quad[:, 1].min() >= ymax)
                    clipped = local
                    if not disjoint:
                        local_bounds = bounds - quad[0, [0, 0, 1, 1]]
                        if not np.all(np.isfinite(local_bounds)):
                            raise ArithmeticError("nonfinite clipping arithmetic")
                        for axis, bound, above in ((0, local_bounds[0], True), (0, local_bounds[1], False),
                                                   (1, local_bounds[2], True), (1, local_bounds[3], False)):
                            clipped = _clip_halfplane(clipped, axis, bound, above)
                    intersection = 0.0 if disjoint else _signed_area(clipped)
                    if intersection < 0:
                        raise ArithmeticError("negative clipped orientation")
                    record.update(evaluable=True, cell_area=area, overlap_area=intersection)
            except (ArithmeticError, OverflowError):
                record["reason"] = "nonfinite_or_invalid_geometry_arithmetic"
            records.append(record)

    evaluable = all(r["evaluable"] for r in records)
    total = maximum = None
    aggregate_reason = None
    if evaluable:
        areas = [r["overlap_area"] for r in records]
        try:
            total = math.fsum(areas)
            if not math.isfinite(total):
                raise ArithmeticError("nonfinite total")
            maximum = max(areas, default=0.0)
        except (ArithmeticError, OverflowError):
            evaluable, total = False, None
            aggregate_reason = "nonfinite_total_overlap"
    return dict(scope="solid_cells_against_rigid_rectangle_only", evaluable=evaluable,
                geometry_valid=(total <= ot) if evaluable else None,
                total_overlap_area=total, max_element_overlap_area=maximum,
                n_solid_cells=len(records), cells=records, aggregate_reason=aggregate_reason,
                rectangle=bounds.tolist(), length_tolerance=lt, area_tolerance=at,
                overlap_tolerance=ot)


def strict_valid_prefix(states):
    """Classify accepted states in supplied chronological order, without sorting.

    Each mapping requires a unique nonempty string or integer ``id``, finite
    scalar ``d``, and explicit boolean ``solver_valid``, ``geometry_valid`` and
    ``reference_valid``. Optional ``value`` is a finite scalar or None. The
    physical prefix ends at the first false gate, including inserted states;
    subsequent recovery never restores scoring. Missing/None values remain
    unknown rather than zero, but do not themselves invalidate geometry.

    The caller must supply ALL accepted states. This utility cannot discover
    omitted states or verify the mechanics underlying the three supplied gates.
    Nonmonotone d is permitted: path order, not displacement order, is authoritative.
    """
    if not isinstance(states, Sequence) or isinstance(states, (str, bytes)):
        raise ValueError("states must be an ordered sequence of mappings")
    gates = ("solver_valid", "geometry_valid", "reference_valid")
    required = {"id", "d", *gates}
    checked, ids = [], set()
    for state in states:
        if not isinstance(state, Mapping) or not required.issubset(state):
            raise ValueError("each state requires id, d, solver_valid, geometry_valid, reference_valid")
        identifier = state["id"]
        if (type(identifier) not in (str, int) or (isinstance(identifier, str) and not identifier.strip())
                or identifier in ids):
            raise ValueError("state id must be a unique nonempty string or integer")
        ids.add(identifier)
        if any(type(state[g]) is not bool for g in gates):
            raise ValueError("validity gates must be explicit booleans")
        d = _finite_scalar(state["d"], "state d")
        value = state.get("value")
        if value is not None:
            value = _finite_scalar(value, "state value")
        checked.append(dict(id=identifier, d=d, **{g: state[g] for g in gates},
                            value=value, value_provided="value" in state))

    first_invalid = None
    records = []
    for index, state in enumerate(checked):
        failed = [g for g in gates if not state[g]]
        if failed and first_invalid is None:
            first_invalid = index
        comparable = first_invalid is None
        if not comparable:
            reason = "invalid_state" if index == first_invalid else "after_first_invalid"
        elif not state["value_provided"]:
            reason = "value_not_provided"
        elif state["value"] is None:
            reason = "unknown_value"
        else:
            reason = None
        records.append(dict(**state, local_valid=not failed, comparable=comparable,
                            failed_checks=failed, score=state["value"] if comparable else None,
                            score_reason=reason))
    count = len(checked) if first_invalid is None else first_invalid
    return dict(states=records, prefix_length=count,
                prefix_end_id=checked[count - 1]["id"] if count else None,
                prefix_end_d=checked[count - 1]["d"] if count else None,
                first_invalid_index=first_invalid,
                first_invalid_id=checked[first_invalid]["id"] if first_invalid is not None else None)
