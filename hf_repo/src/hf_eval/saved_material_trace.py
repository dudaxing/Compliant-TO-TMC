"""One-sided saved material Piola traces on a fixed lower-half Q1 square.

Only ordinary arrays and NumPy; no file reads, constitutive/force-kernel/
equilibrium calls or plotting. P is in MPa, before thickness. Independent
reference Simpson line estimates are an
explanation aid, not total Hu traction, pressure or a weak-force equality test.
"""
from __future__ import annotations

import numpy as np

FACE_NAMES = ("bottom", "right", "top", "left")
FACES = {
    "bottom": ((0., -1.), (1., 0.), "top", (2, 5, 8)),
    "left": ((-1., 0.), (0., 1.), "right", (6, 7, 8)),
    "right": ((1., 0.), (0., 1.), "left", (0, 1, 2)),
}


def observe_saved_workpiece_material_trace(model, stress_first_piola, *, identity,
                                          symmetry_y_mm, thickness_mm):
    """Preserve each physical edge's outside owner and three saved samples.

    model supplies coordinates/connectivity/solid/workpiece_cells/points.
    Native Q1 nodes are BL, BR, TR, TL; points use xi-slow, eta-fast Simpson
    order. Normals point outward from the body; P_outer @ N_body is the signed
    nominal material traction ON the body. Sampling tangents increase x on
    bottom, y on both vertical sides; they are not an oriented closed contour.
    Shared endpoints retain each edge/owner value without averaging. The top
    symmetry cut is excluded. The caller binds saved state and array identity.
    """
    xy = np.asarray(model["coordinates"], dtype=float)
    conn, body = np.asarray(model["connectivity"]), np.asarray(model["workpiece_cells"])
    solid, points = np.asarray(model["solid"]), np.asarray(model["points"], dtype=float)
    P = np.asarray(stress_first_piola, dtype=float)
    expected_points = np.array([(xi, eta) for xi in (-1., 0., 1.) for eta in (-1., 0., 1.)])
    if (xy.ndim != 2 or xy.shape[1] != 2 or conn.ndim != 2 or conn.shape[1] != 4
            or conn.dtype.kind not in "iu" or body.dtype.kind not in "iu"
            or body.ndim != 1 or not len(body) or len(np.unique(body)) != len(body)
            or solid.shape != (len(conn),) or solid.dtype.kind != "b"
            or np.any(conn < 0) or np.any(conn >= len(xy))
            or np.any(body < 0) or np.any(body >= len(conn))
            or P.shape != (len(conn), 9, 2, 2) or not np.isfinite(P).all()
            or not np.isfinite(xy).all() or not np.array_equal(points, expected_points)
            or not np.isfinite([symmetry_y_mm, thickness_mm]).all() or thickness_mm <= 0.):
        raise ValueError("Require finite native Q1 arrays, saved nine-point P and positive thickness")
    body_set = set(map(int, body))
    body_xy = xy[np.unique(conn[body])]
    lower, upper = body_xy.min(axis=0), body_xy.max(axis=0)
    contained = np.all((xy[conn] >= lower) & (xy[conn] <= upper), axis=(1, 2))
    if (upper[1] != symmetry_y_mm or upper[0]-lower[0] != 2*(upper[1]-lower[1])
            or upper[1] <= lower[1] or not np.array_equal(np.sort(body), np.flatnonzero(contained))
            or np.any(solid[body])):
        raise ValueError("Require a complete aligned lower-half square over original-medium cells")
    owners = {}
    for cell, nodes in enumerate(conn):
        for face in range(4):
            pair = tuple(sorted((int(nodes[face]), int(nodes[(face+1) % 4]))))
            owners.setdefault(pair, []).append((cell, face))
    edges, cut = [], []
    for pair, adjacent in sorted(owners.items()):
        inside = [(cell, face) for cell, face in adjacent if cell in body_set]
        if len(inside) != 1:
            continue
        endpoints = xy[list(pair)]
        if np.all(endpoints[:, 1] == symmetry_y_mm):
            cut.append(list(pair))
            continue
        face = ("bottom" if np.all(endpoints[:, 1] == lower[1]) else
                "left" if np.all(endpoints[:, 0] == lower[0]) else
                "right" if np.all(endpoints[:, 0] == upper[0]) else None)
        outside = [(cell, local) for cell, local in adjacent if cell not in body_set]
        if face is None or len(adjacent) != 2 or len(outside) != 1:
            raise ValueError("Each physical body edge needs exactly one outside cell")
        body_cell, body_local = inside[0]
        outer_cell, outer_local = outside[0]
        normal, tangent, outer_face, q = FACES[face]
        if FACE_NAMES[body_local] != face or FACE_NAMES[outer_local] != outer_face:
            raise ValueError("Body/outside local faces disagree with aligned square ownership")
        quad = xy[conn[outer_cell]]
        lo, hi = quad[0], quad[2]
        if not (np.all(hi > lo) and np.array_equal(quad, np.array([lo, [hi[0], lo[1]], hi, [lo[0], hi[1]]]))):
            raise ValueError("Outside cell must be a positively oriented aligned Q1 rectangle")
        sample_xy = (lo+hi)/2 + points[list(q)]*(hi-lo)/2
        saved_P = P[outer_cell, list(q)].copy()
        PN = saved_P @ np.asarray(normal)
        length = float(np.linalg.norm(endpoints[1]-endpoints[0]))
        line_weights = np.array([1., 4., 1.])*length/6
        samples = [dict(point_index=int(point), reference_point=points[point].tolist(),
            coordinates_mm=location.tolist(), P_MPa=matrix.tolist(), PN_MPa=traction.tolist(),
            nominal_compression_MPa=float(-traction @ normal),
            sampling_tangent_shear_MPa=float(traction @ tangent), line_weight_mm=float(weight))
            for point, location, matrix, traction, weight in zip(q, sample_xy, saved_P, PN, line_weights)]
        edges.append(dict(node_ids=list(pair), face=face, body_cell_id=int(body_cell),
            body_local_face=FACE_NAMES[body_local], outer_cell_id=int(outer_cell),
            outer_local_face=outer_face, outer_phase="mechanism_solid" if solid[outer_cell] else "third_medium",
            outer_node_ids=conn[outer_cell].tolist(), body_outward_normal=list(normal),
            sampling_tangent=list(tangent), reference_length_mm=length, samples=samples,
            material_line_estimate_on_body_N=(thickness_mm*(line_weights @ PN)).tolist()))
    sides = {name: dict(edge_count=sum(edge["face"] == name for edge in edges),
        material_line_estimate_on_body_N=np.sum([edge["material_line_estimate_on_body_N"]
            for edge in edges if edge["face"] == name], axis=0).tolist()) for name in FACES}
    return dict(schema_version="saved-fixed-square-material-trace-1.0", identity=dict(identity),
        physical_node_pairs=[edge["node_ids"] for edge in edges], cut_node_pairs=cut, edges=edges,
        sides=sides, material_line_estimate_on_body_N=np.sum(
            [edge["material_line_estimate_on_body_N"] for edge in edges], axis=0).tolist(),
        thickness_mm=float(thickness_mm), traction_units="MPa = N/mm^2, per reference area",
        integration="Independent reference L/6*[1,4,1] line weights times thickness once; not volume weights",
        scope="One-sided saved material P; owner-specific endpoints retained; symmetry cut excluded",
        qualification="Saved trace and interpretive material line estimates only; no Hu total traction, pressure, effective-grip or weak-force equality qualification")
