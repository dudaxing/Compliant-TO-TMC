"""Saved convex Q1 regions and finite-face rays, in mm; no mechanics.

Binary64 geometry diagnostics are not certified contact or penetration tests.
Closed cell unions include a symmetry cut for region classification only.
"""
from __future__ import annotations

import numpy as np

from .boundary_geometry import boundary_distances, exposed_q1_edges


def _tolerance(xy):
    return 32*np.finfo(float).eps*max(1., float(np.max(np.abs(xy))))


def _cross(a, b):
    return a[..., 0]*b[..., 1]-a[..., 1]*b[..., 0]


def _indices(values):
    indices = np.asarray(values)
    if indices.size and indices.dtype.kind not in "iu":
        raise ValueError("Cell and node IDs must be integers")
    return indices.astype(np.int64, copy=False)


def _invalid_quads(xy, conn, selected, tolerance):
    invalid = []
    for cell in selected:
        points = xy[conn[cell]]
        edges = np.roll(points, -1, axis=0)-points
        lengths = np.linalg.norm(edges, axis=1)
        turns = _cross(edges, np.roll(edges, -1, axis=0))
        area_tolerance = tolerance*max(1., float(lengths.max()))
        if (not np.isfinite(lengths).all() or not np.isfinite(turns).all()
                or np.any(lengths <= tolerance) or np.any(turns <= area_tolerance)):
            invalid.append(dict(cell_id=int(cell), points_mm=points.tolist(),
                edge_lengths_mm=[float(v) if np.isfinite(v) else str(float(v)) for v in lengths],
                consecutive_cross_products_mm2=[float(v) if np.isfinite(v) else str(float(v)) for v in turns],
                reason="Expected nondegenerate, strictly convex, positively oriented Q1 quad"))
    return invalid


def region_overlap(coordinates, connectivity, mechanism_cells, workpiece_cells):
    """Check cross-region interior overlap of complete convex Q1 cell unions.

For every unit edge-normal axis, gap=max(minA,minB)-min(maxA,maxB).
A negative maximum gap means raw interior overlap, not penetration depth.
Complete set containment and mechanism self-overlap are not tested.
"""
    xy, conn = np.asarray(coordinates, float), _indices(connectivity)
    mechanism, body = _indices(mechanism_cells), _indices(workpiece_cells)
    if (xy.ndim != 2 or xy.shape[1] != 2 or not np.isfinite(xy).all()
            or conn.ndim != 2 or conn.shape[1] != 4):
        raise ValueError("Expected finite coordinates and four-node connectivity")
    if np.any(conn < 0) or np.any(conn >= len(xy)):
        raise ValueError("Connectivity contains an invalid node ID")
    for selected in (mechanism, body):
        if (selected.ndim != 1 or len(np.unique(selected)) != len(selected)
                or np.any(selected < 0) or np.any(selected >= len(conn))):
            raise ValueError("Expected unique, valid cell IDs")
    tolerance = _tolerance(xy)
    invalid = _invalid_quads(xy, conn, np.unique(np.r_[mechanism, body]), tolerance)
    report = dict(geometry_valid=not invalid, invalid_cells=invalid,
        roundoff_tolerance_mm=tolerance, region_overlap_tested=False,
        raw_interior_overlap=None, strict_interior_overlap=None, roundoff_ambiguous=None,
        set_containment_tested=False, mechanism_self_overlap_tested=False,
        mechanism_cell_count=len(mechanism), workpiece_cell_count=len(body),
        candidate_cell_pairs=0, pair_observations=[], boundary_intersections=None,
        projection_gap_definition="max(minA,minB)-min(maxA,maxB) on each unit edge-normal; mm; not penetration depth")
    if invalid:
        return report
    report.update(region_overlap_tested=True, raw_interior_overlap=False,
                  strict_interior_overlap=False, roundoff_ambiguous=False)
    quads = xy[conn]
    other = quads[body]
    other_lo, other_hi = other.min(axis=1), other.max(axis=1)
    for cell in mechanism:
        first = quads[cell]
        # A closed AABB expanded only by the numerical uncertainty band.
        candidates = np.all(other_hi >= first.min(axis=0)-tolerance, axis=1)
        candidates &= np.all(other_lo <= first.max(axis=0)+tolerance, axis=1)
        for other_cell, second in zip(body[candidates], other[candidates]):
            report["candidate_cell_pairs"] += 1
            edges = np.r_[np.roll(first, -1, axis=0)-first,
                          np.roll(second, -1, axis=0)-second]
            axes = np.column_stack((-edges[:, 1], edges[:, 0]))/np.linalg.norm(edges, axis=1)[:, None]
            # A common origin avoids cancellation from the world-coordinate offset.
            a, b = (first-first[0])@axes.T, (second-first[0])@axes.T
            gaps = np.maximum(a.min(axis=0), b.min(axis=0))-np.minimum(a.max(axis=0), b.max(axis=0))
            maximum = float(gaps.max())
            raw = maximum < 0.
            strict = maximum < -tolerance
            ambiguous = abs(maximum) <= tolerance
            kind = ("strict_interior_overlap" if strict else "raw_zero_touch" if maximum == 0.
                    else "roundoff_ambiguous" if ambiguous else "separated")
            report["raw_interior_overlap"] |= raw
            report["strict_interior_overlap"] |= strict
            report["roundoff_ambiguous"] |= ambiguous
            report["pair_observations"].append(dict(mechanism_cell=int(cell), workpiece_cell=int(other_cell),
                unit_axes=axes.tolist(), projection_gaps_mm=gaps.tolist(), maximum_projection_gap_mm=maximum,
                raw_interior_overlap=raw, strict_interior_overlap=strict, classification=kind))
    closed_mechanism = exposed_q1_edges(conn, mechanism, xy)
    closed_body = exposed_q1_edges(conn, body, xy)
    report["boundary_intersections"] = boundary_distances(xy, closed_mechanism, closed_body)
    report["boundary_scope"] = "Topologically exposed closed-region edges including any symmetry cut; self-overlap not tested; not physical contact boundaries"
    return report


def _clip_nonnegative(lower, upper, value, slope):
    if slope == 0.:
        return None if value < 0. else (lower, upper)
    root = -value/slope
    if slope > 0.:
        lower = max(lower, root)
    else:
        upper = min(upper, root)
    return None if lower > upper else (lower, upper)


def finite_face_ray_hit(coordinates, mechanism_edges, face_start, face_end, outward_normal):
    """Minimum first outward boundary hit over a continuous, finite face.

Clip each edge analytically to the face's tangential strip and t>=0.
The minimum over all admissible hits equals the minimum of first hits over
face positions. A positive hit can be an exit when the origin is inside solid.
"""
    xy = np.asarray(coordinates, float)
    edges = _indices(mechanism_edges).reshape(-1, 2)
    start, end, normal = map(lambda p: np.asarray(p, float), (face_start, face_end, outward_normal))
    if (xy.ndim != 2 or xy.shape[1] != 2 or any(p.shape != (2,) for p in (start, end, normal))
            or not np.isfinite(np.r_[start, end, normal]).all()):
        raise ValueError("Expected finite two-dimensional coordinates, face endpoints and normal")
    if np.any(edges < 0) or np.any(edges >= len(xy)):
        raise ValueError("Ray boundary contains an invalid node ID")
    delta = end-start
    length, normal_length = float(np.linalg.norm(delta)), float(np.linalg.norm(normal))
    if (not np.isfinite(xy).all() or not np.isfinite([length, normal_length]).all()
            or length <= 0. or normal_length <= 0.):
        raise ValueError("Expected finite coordinates and a nonzero face/normal")
    tangent, normal = delta/length, normal/normal_length
    tolerance = _tolerance(np.r_[xy, start[None], end[None]])
    if abs(float(tangent@normal)) > 32*np.finfo(float).eps:
        raise ValueError("Outward normal must be perpendicular to the finite face")
    hits = []
    for edge_index, nodes in enumerate(edges):
        first, last = xy[nodes]
        along = np.asarray([(first-start)@tangent, (last-start)@tangent])
        distance = np.asarray([(first-start)@normal, (last-start)@normal])
        da, dt = float(along[1]-along[0]), float(distance[1]-distance[0])
        interval = (0., 1.)
        for value, slope in ((along[0], da), (length-along[0], -da), (distance[0], dt)):
            interval = _clip_nonnegative(*interval, float(value), slope)
            if interval is None:
                break
        if interval is None:
            continue
        lower, upper = interval
        parameter = lower if dt >= 0. else upper
        point = first+parameter*(last-first)
        def face_coordinate_at(u):
            if da != 0. and u == -along[0]/da:
                return 0.
            if da != 0. and u == (length-along[0])/da:
                return length
            return float(along[0]+u*da)

        raw_face_coordinate = float(along[0]+parameter*da)
        face_coordinate = face_coordinate_at(parameter)
        raw_distance = float(distance[0]+parameter*dt)
        forward_root = dt != 0. and parameter == -distance[0]/dt
        # This is an analytic clipping-plane intersection, not tolerance snapping.
        measured = 0. if forward_root else raw_distance
        if measured < 0.:
            raise ValueError("Ray clipping produced a negative forward distance")
        face_point = start+face_coordinate*tangent
        residual = float(np.linalg.norm(point-face_point-measured*normal))
        if residual > tolerance:
            raise ValueError("Ray witness reconstruction exceeds the coordinate roundoff band")
        corner = face_coordinate == 0. or face_coordinate == length
        hit = dict(distance_mm=measured, face_point_mm=face_point.tolist(), edge_point_mm=point.tolist(),
            edge_index=edge_index, mechanism_nodes=nodes.tolist(), edge_parameter=parameter,
            face_parameter=face_coordinate/length, corner_hit=corner,
            near_corner_hit=not corner and min(abs(face_coordinate), abs(length-face_coordinate)) <= tolerance,
            raw_reconstructed_normal_projection_mm=raw_distance,
            raw_reconstructed_tangential_coordinate_mm=raw_face_coordinate,
            analytic_face_endpoint_root=bool(da != 0. and (parameter == -along[0]/da
                                            or parameter == (length-along[0])/da)),
            analytic_forward_plane_root=bool(forward_root), witness_residual_mm=residual,
            minimizing_edge_parameter_interval=[lower, upper] if dt == 0. else [parameter, parameter],
            minimizing_face_parameter_interval=sorted([face_coordinate_at(u)/length
                                                for u in ((lower, upper) if dt == 0. else (parameter, parameter))]))
        hits.append(hit)
    minimum = min((h["distance_mm"] for h in hits), default=None)
    tied = [h for h in hits if h["distance_mm"] == minimum]
    nearby = [h for h in hits if minimum is not None and 0. < h["distance_mm"]-minimum <= tolerance]
    return dict(minimum_first_ray_hit_mm=minimum, no_outward_ray_hit=minimum is None,
        closest_hit=tied[0] if tied else None, minimum_hits=tied, roundoff_near_minimum_hits=nearby,
        admissible_edge_count=len(hits), roundoff_tolerance_mm=tolerance,
        face_start_mm=start.tolist(), face_end_mm=end.tolist(), outward_normal=normal.tolist(),
        method="Analytic finite tangential-strip and forward-halfplane clipping; no dense sampling",
        scope="Directional boundary-hit diagnostic; not signed penetration or contact pressure")


def measure_native_workpiece_regions(model, metadata, lift, fluctuation):
    """Inspect one saved native fixed lower-half square without new mechanics."""
    xy, conn = np.asarray(model["coordinates"], float), _indices(model["connectivity"])
    solid, body_cells = np.asarray(model["solid"], bool), _indices(model["workpiece_cells"])
    extent, body = metadata["model_extent"], metadata["task"]["workpiece"]
    if (extent["kind"] != "lower_half" or extent["symmetry_axis"]["normal"] != [0., 1.]
            or body["kind"] != "fixed_rigid" or body["shape"] != "square"
            or metadata["element_node_order"] != ["BL", "BR", "TR", "TL"]):
        raise ValueError("Expected native BL/BR/TR/TL, fixed lower-half square")
    lift, fluctuation = np.asarray(lift, float), np.asarray(fluctuation, float)
    if lift.shape != (xy.size,) or fluctuation.shape != (xy.size,) or solid.shape != (len(conn),):
        raise ValueError("Saved vectors/mask differ from the native model size")
    if (body_cells.ndim != 1 or not len(body_cells) or len(np.unique(body_cells)) != len(body_cells)
            or np.any(body_cells < 0) or np.any(body_cells >= len(conn)) or np.any(solid[body_cells])):
        raise ValueError("Workpiece overlay must select original-medium cells")
    grid = metadata["grid"]
    ny, nx = grid["shape_yx"]
    origin, spacing = np.asarray(grid["origin_mm"], float), np.asarray(grid["cell_size_mm"], float)
    xx, yy = np.meshgrid(origin[0]+np.arange(nx+1)*spacing[0], origin[1]+np.arange(ny+1)*spacing[1])
    expected_xy = np.column_stack((xx.ravel(), yy.ravel()))
    jj, ii = np.meshgrid(np.arange(ny), np.arange(nx), indexing="ij")
    bl = (jj*(nx+1)+ii).ravel()
    expected_conn = np.column_stack((bl, bl+1, bl+nx+2, bl+nx+1))
    if (grid["axes"] != [[1., 0.], [0., 1.]] or grid["array_order"] != "C_yx_bottom_up"
            or np.any(spacing <= 0.) or not np.array_equal(xy, expected_xy)
            or not np.array_equal(conn, expected_conn)):
        raise ValueError("Expected the complete declared native Cartesian reference grid")
    symmetry = float(extent["symmetry_axis"]["offset_mm"])
    center, side = np.asarray(body["center_mm"], float), float(body["side_mm"])
    lower, upper = center-side/2, np.asarray([center[0]+side/2, symmetry])
    reference_inside = np.all((xy[conn] >= lower)&(xy[conn] <= upper), axis=(1, 2))
    complete_square = center[1] == symmetry and side > 0. and np.array_equal(
        np.sort(body_cells), np.flatnonzero(reference_inside))
    body_reference = xy[np.unique(conn[body_cells])]
    complete_square &= np.array_equal(body_reference.min(axis=0), lower) and np.array_equal(
        body_reference.max(axis=0), upper)
    actual = xy+lift.reshape(-1, 2)+fluctuation.reshape(-1, 2)
    nodes = np.unique(conn[body_cells])
    fixed = not np.any((lift+fluctuation).reshape(-1, 2)[nodes] != 0.)
    report = dict(schema_version="native-workpiece-region-geometry-1.0", geometry_valid=False,
        actual_coordinate_definition="coordinates + lift + fluctuation; binary64 millimetres; scale one",
        regions=None, faces={}, complete_fixed_half_square=bool(complete_square and fixed),
        invalid_cells=[],
        model_failure=None if complete_square and fixed else "Workpiece is not the complete, fixed lower-half square",
        symmetry_cut_scope="Included for closed region classification; excluded from physical face-ray edges",
        set_containment_tested=False, signed_penetration_tested=False,
        force_calls=0, tangent_calls=0, solver_calls=0, HP_calls=0,
        contact_pressure_qualification=False, contact_or_clamping_qualification=False)
    if not complete_square or not fixed:
        return report
    regions = region_overlap(actual, conn, np.flatnonzero(solid), body_cells)
    report.update(regions=regions, geometry_valid=regions["geometry_valid"], invalid_cells=regions["invalid_cells"])
    if not regions["geometry_valid"]:
        return report
    physical_edges = exposed_q1_edges(conn, np.flatnonzero(solid), xy, symmetry_y_mm=symmetry)
    face_specs = {"bottom": (lower, [upper[0], lower[1]], [0., -1.]),
                  "left": (lower, [lower[0], upper[1]], [-1., 0.])}
    report["physical_mechanism_edges"] = physical_edges.tolist()
    for name, (start, end, normal) in face_specs.items():
        face = finite_face_ray_hit(actual, physical_edges, start, end, normal)
        face["separation_interpretation"] = ("not_a_separation_gap" if regions["raw_interior_overlap"]
            or regions["roundoff_ambiguous"] else "directional_separation_diagnostic_only")
        report["faces"][name] = face
    return report
