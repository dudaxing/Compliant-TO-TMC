"""Saved Q1 boundary geometry only; no mechanics or contact qualification.

Q1 edges are straight lines between the actual deformed nodes. Distances are
unsigned boundary distances, not signed gaps or penetration. A fitted analytic
circle and display magnification never enter these measurements.
"""
from __future__ import annotations

import numpy as np


def exposed_q1_edges(connectivity, cells, coordinates, *, symmetry_y_mm=None):
    """Return unique node pairs incident to exactly one selected Q1 cell.

The native BL/BR/TR/TL order defines cell edges. Remove a lower-half symmetry
cut by its reference endpoints, before any deformation is applied.
"""
    conn = np.asarray(connectivity)
    cells = np.asarray(cells, dtype=np.int64)
    xy = np.asarray(coordinates, dtype=float)
    if conn.ndim != 2 or conn.shape[1] != 4 or xy.ndim != 2 or xy.shape[1] != 2:
        raise ValueError("Expected Q1 connectivity (ne,4) and coordinates (nn,2)")
    if cells.ndim != 1 or len(np.unique(cells)) != len(cells):
        raise ValueError("Selected cell IDs must be a unique one-dimensional set")
    if not len(cells):
        return np.empty((0, 2), dtype=np.int64)
    selected = conn[cells]
    pairs = np.stack((selected, np.roll(selected, -1, axis=1)), axis=-1).reshape(-1, 2)
    pairs, counts = np.unique(np.sort(pairs, axis=1), axis=0, return_counts=True)
    outer = pairs[counts == 1].astype(np.int64, copy=False)
    if symmetry_y_mm is not None:
        outer = outer[~np.all(xy[outer, 1] == symmetry_y_mm, axis=1)]
    return outer


def _cross(a, b):
    return a[..., 0]*b[..., 1]-a[..., 1]*b[..., 0]


def _project(point, a, b):
    direction = b-a
    length2 = np.sum(direction*direction, axis=-1)
    parameter = np.divide(np.sum((point-a)*direction, axis=-1), length2,
                          out=np.zeros_like(length2), where=length2 != 0.)
    return a+np.clip(parameter, 0., 1.)[..., None]*direction


def _pairs_to_segment(segments, body_segment, tolerance_mm):
    """Vectorized nearest points and intersection records for one body edge."""
    a, b = segments[:, 0], segments[:, 1]
    c, d = body_segment
    count = len(segments)
    ca, cb = np.broadcast_to(c, a.shape), np.broadcast_to(d, a.shape)
    first = np.stack((a, b, _project(ca, a, b), _project(cb, a, b)), axis=1)
    second = np.stack((_project(a, ca, cb), _project(b, ca, cb), ca, cb), axis=1)
    distances2 = np.sum((first-second)**2, axis=-1)
    closest = distances2.argmin(axis=1)
    index = np.arange(count)
    pa, pb = first[index, closest].copy(), second[index, closest].copy()
    distances = np.sqrt(distances2[index, closest])

    u, v, w = b-a, d-c, c-a
    denominator = _cross(u, v)
    nonparallel = denominator != 0.
    s = np.divide(_cross(w, v), denominator, out=np.zeros(count), where=nonparallel)
    t = np.divide(_cross(w, u), denominator, out=np.zeros(count), where=nonparallel)
    crossing = nonparallel & (s >= 0.) & (s <= 1.) & (t >= 0.) & (t <= 1.)
    pa[crossing] = a[crossing]+s[crossing, None]*u[crossing]
    pb[crossing] = pa[crossing]
    distances[crossing] = 0.

    intersections = []
    for i in np.flatnonzero(distances <= tolerance_mm):
        item = dict(mechanism_edge_index=int(i), closest_mechanism_point_mm=pa[i].tolist(),
                    closest_workpiece_point_mm=pb[i].tolist(), separation_mm=float(distances[i]))
        if distances[i] > 0.:
            item.update(kind="roundoff_near_touch", intersection_point_mm=((pa[i]+pb[i])/2).tolist())
            intersections.append(item)
            continue
        u2, v2 = float(u[i]@u[i]), float(v@v)
        collinear = (u2 > 0. and v2 > 0. and denominator[i] == 0.
                     and _cross(w[i], u[i]) == 0.)
        if collinear:
            parameters = np.asarray([(c-a[i])@u[i], (d-a[i])@u[i]])/u2
            lower, upper = max(0., parameters.min()), min(1., parameters.max())
            if lower <= upper:
                ends = a[i]+np.asarray([lower, upper])[:, None]*u[i]
                item.update(kind="collinear_overlap" if upper > lower else "endpoint_touch",
                            intersection_segment_mm=ends.tolist())
            else:
                item.update(kind="roundoff_near_touch", intersection_point_mm=((pa[i]+pb[i])/2).tolist())
        else:
            kind = ("crossing" if crossing[i] and 0. < s[i] < 1. and 0. < t[i] < 1.
                    else "degenerate_touch" if u2 == 0. or v2 == 0.
                    else "endpoint_touch" if distances[i] == 0. else "roundoff_near_touch")
            item.update(kind=kind, intersection_point_mm=((pa[i]+pb[i])/2).tolist())
        intersections.append(item)
    return distances, pa, pb, intersections


def boundary_distances(coordinates, mechanism_edges, workpiece_edges):
    """Measure finite segment pairs, retaining every crossing/touch pair.

Near-touch classification uses 32 eps times the coordinate magnitude in mm.
It is a floating-point geometry tolerance, not a physical contact threshold.
The reported unsigned nearest distance is never tolerance-clipped.
"""
    xy = np.asarray(coordinates, dtype=float)
    mechanism = np.asarray(mechanism_edges, dtype=np.int64).reshape(-1, 2)
    body = np.asarray(workpiece_edges, dtype=np.int64).reshape(-1, 2)
    if not np.all(np.isfinite(xy)):
        raise ValueError("Actual nodal coordinates must be finite")
    tolerance = 32.*np.finfo(float).eps*max(1., float(np.max(np.abs(xy))))
    report = dict(mechanism_edge_count=len(mechanism), workpiece_edge_count=len(body),
                  roundoff_tolerance_mm=tolerance, minimum_boundary_distance_mm=None,
                  closest_pair=None, intersections=[], intersects=False,
                  roundoff_near_touch=False, containment_tested=False,
                  intersection_semantics="Crossing or raw zero-distance touch/overlap; positive roundoff near-touch is separate")
    if not len(mechanism) or not len(body):
        return report
    best = np.inf
    for j, pair in enumerate(body):
        distances, first, second, hits = _pairs_to_segment(xy[mechanism], xy[pair], tolerance)
        i = int(distances.argmin())
        if distances[i] < best:
            best = float(distances[i])
            report["closest_pair"] = dict(mechanism_edge_index=i, workpiece_edge_index=j,
                mechanism_nodes=mechanism[i].tolist(), workpiece_nodes=pair.tolist(),
                mechanism_point_mm=first[i].tolist(), workpiece_point_mm=second[i].tolist())
        for hit in hits:
            i = hit["mechanism_edge_index"]
            hit.update(workpiece_edge_index=j, mechanism_nodes=mechanism[i].tolist(),
                       workpiece_nodes=pair.tolist())
            report["intersections"].append(hit)
    report["minimum_boundary_distance_mm"] = best
    report["intersects"] = any(hit["kind"] != "roundoff_near_touch" for hit in report["intersections"])
    report["roundoff_near_touch"] = any(hit["kind"] == "roundoff_near_touch" for hit in report["intersections"])
    return report


def measure_native_workpiece_boundaries(model, metadata, lift, fluctuation):
    """Measure a saved lower-half native fixed workpiece from actual L+w.

Required arrays are coordinates, connectivity, solid and workpiece_cells.
Reference geometry chooses external edges and square side groups; the actual
saved coordinates determine all distances and intersection positions.
"""
    xy = np.asarray(model["coordinates"], dtype=float)
    conn = np.asarray(model["connectivity"])
    solid = np.asarray(model["solid"], dtype=bool)
    cells = np.asarray(model["workpiece_cells"], dtype=np.int64)
    extent = metadata["model_extent"]
    body = metadata["task"]["workpiece"]
    if (extent["kind"] != "lower_half" or extent["symmetry_axis"]["normal"] != [0., 1.]
            or body["kind"] != "fixed_rigid" or body["shape"] not in ("square", "circle")):
        raise ValueError("Expected a native lower-half fixed square or circle")
    if metadata["element_node_order"] != ["BL", "BR", "TR", "TL"]:
        raise ValueError("Expected native BL/BR/TR/TL Q1 node order")
    lift, fluctuation = np.asarray(lift, dtype=float), np.asarray(fluctuation, dtype=float)
    if lift.shape != (xy.size,) or fluctuation.shape != (xy.size,) or solid.shape != (len(conn),):
        raise ValueError("Saved split vectors or solid mask differ from the model size")
    if not len(cells) or np.any(solid[cells]):
        raise ValueError("Workpiece overlay must select nonempty original-medium cells")
    symmetry = float(extent["symmetry_axis"]["offset_mm"])
    mechanism_edges = exposed_q1_edges(conn, np.flatnonzero(solid), xy, symmetry_y_mm=symmetry)
    body_edges = exposed_q1_edges(conn, cells, xy, symmetry_y_mm=symmetry)
    actual = xy+lift.reshape(-1, 2)+fluctuation.reshape(-1, 2)
    groups = {"all_exposed": body_edges}
    if body["shape"] == "square":
        lower = xy[np.unique(conn[cells])].min(axis=0)
        groups.update(bottom=body_edges[np.all(xy[body_edges, 1] == lower[1], axis=1)],
                      left=body_edges[np.all(xy[body_edges, 0] == lower[0], axis=1)])
    return dict(schema_version="native-workpiece-boundary-geometry-1.0", shape=body["shape"],
        actual_coordinate_definition="coordinates + lift + fluctuation; millimetres; scale one",
        method="Unsigned Euclidean distances of actual straight Q1 outer edges; no signed penetration",
        symmetry_cut_excluded=dict(axis="y", reference_offset_mm=symmetry, applies_to="both boundaries"),
        mechanism_edges=mechanism_edges.tolist(), workpiece_edges=body_edges.tolist(),
        groups={name: boundary_distances(actual, mechanism_edges, edges) for name, edges in groups.items()},
        circle_representation="native cell staircase; no analytic circle fit" if body["shape"] == "circle" else None,
        containment_tested=False, force_calls=0, tangent_calls=0, solver_calls=0, HP_calls=0,
        contact_pressure_qualification=False, contact_or_clamping_qualification=False)
