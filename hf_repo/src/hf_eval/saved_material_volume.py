"""Saved rounded-P volume contraction on two outside bottom-owner cells.

Ordinary NumPy arrays only. This diagnostic does not reconstruct the original
compensated force path, call a material kernel, or qualify contact pressure.
"""
from __future__ import annotations

from math import fsum
import numpy as np


def _vector_sum(values):
    return [fsum(float(value[axis]) for value in values) for axis in (0, 1)]


def observe_saved_bottom_owner_material_volume(model, forces, body_metadata, *,
        identity, material_trace, saved_support_cells, selected_cell_ids,
        thickness_mm):
    """Explain saved bottom support with the nine already exported P samples.

    Q1 nodes are BL, BR, TR, TL. Selecting TR/TL gives the basis sum
    chi=(1+eta)/2, whose physical gradient is (0,1/hy). Negative
    volume contraction is ON-body material force. Saved element weak forces
    are copied from the original compensated contraction and compared exactly
    to M-SUPPORT1; rounded-P contraction is a separate diagnostic.

    Only regrouping the same nine computed q terms has a new arithmetic gate:
    8*eps*sum(abs(q terms)), no absolute floor. Geometric C_eta expressions and
    differences from the saved edge trace/weak force are descriptive only.
    """
    xy, points = np.asarray(model["coordinates"], dtype=float), np.asarray(model["points"], dtype=float)
    conn, grad, weights = np.asarray(model["connectivity"]), np.asarray(model["grad"], dtype=float), np.asarray(model["weights"], dtype=float)
    P, element = np.asarray(forces["stress_first_piola"], dtype=float), np.asarray(forces["element_material_force"], dtype=float)
    expected_points = np.array([(xi, eta) for xi in (-1., 0., 1.) for eta in (-1., 0., 1.)])
    cells = list(map(int, selected_cell_ids))
    if (xy.ndim != 2 or xy.shape[1] != 2 or conn.ndim != 2 or conn.shape[1] != 4
            or conn.dtype.kind not in "iu" or P.shape != (len(conn), 9, 2, 2)
            or element.shape != (len(conn), 8) or grad.shape != (9, 4, 2) or weights.shape != (9,)
            or not np.array_equal(points, expected_points) or len(cells) != 2 or len(set(cells)) != 2
            or any(cell < 0 or cell >= len(conn) for cell in cells)
            or not all(np.isfinite(array).all() for array in (xy, P, element, grad, weights))
            or thickness_mm != 20. or material_trace["identity"] != identity):
        raise ValueError("Require the saved finite native nine-point arrays, two cells and original identity")
    body_nodes, body_cells = set(body_metadata["nodes"]), set(body_metadata["cells"])
    body_lower_y = float(xy[list(body_nodes), 1].min())
    edges = {int(edge["outer_cell_id"]): edge for edge in material_trace["edges"]}
    support = {int(row["cell_id"]): row for row in saved_support_cells}
    records = []
    for cell in cells:
        quad = xy[conn[cell]]
        lo, hi = quad[0], quad[2]
        hx, hy = float(hi[0]-lo[0]), float(hi[1]-lo[1])
        if (hx != .5 or hy != .5 or not np.array_equal(quad, np.array([lo, [hi[0], lo[1]], hi, [lo[0], hi[1]]]))
                or hi[1] != body_lower_y or cell in body_cells
                or [local for local, node in enumerate(conn[cell]) if int(node) in body_nodes] != [2, 3]):
            raise ValueError("Require aligned h0.5 outside bottom owners with exactly the original TR/TL body nodes")
        xi, eta = points[:, 0], points[:, 1]
        expected_grad = np.empty((9, 4, 2), dtype=float)
        expected_grad[:, :, 0] = np.column_stack((eta-1, 1-eta, 1+eta, -1-eta))/(2*hx)
        expected_grad[:, :, 1] = np.column_stack((xi-1, -1-xi, 1+xi, 1-xi))/(2*hy)
        expected_weights = np.outer([1., 4., 1.], [1., 4., 1.]).ravel()*(hx*hy*thickness_mm/36)
        gchi = grad[:, 2, :]+grad[:, 3, :]
        if (not np.array_equal(grad, expected_grad) or not np.array_equal(weights, expected_weights)
                or not np.array_equal(gchi, np.tile([0., 1/hy], (9, 1)))):
            raise ValueError("Saved gradients/volume weights differ from the original NumPy operators expression")
        edge, old = edges[cell], support[cell]
        if (edge["face"] != "bottom" or edge["outer_local_face"] != "top"
                or edge["outer_node_ids"] != conn[cell].tolist()
                or edge["node_ids"] != sorted(map(int, conn[cell, [2, 3]]))
                or edge["body_outward_normal"] != [0., -1.] or edge["reference_length_mm"] != hx
                or old["group"] != "bottom_owner" or old["node_ids"] != conn[cell].tolist()
                or old["selected_local_indices"] != [2, 3]
                or old["selected_body_node_ids"] != conn[cell, [2, 3]].tolist()):
            raise ValueError("Original edge owner/body pair or saved support selection differs")
        for q, sample in zip((2, 5, 8), edge["samples"]):
            if (sample["point_index"] != q or sample["reference_point"] != points[q].tolist()
                    or sample["coordinates_mm"] != ((lo+hi)/2+points[q]*(hi-lo)/2).tolist()
                    or sample["P_MPa"] != P[cell, q].tolist()
                    or sample["PN_MPa"] != (-P[cell, q, :, 1]).tolist()):
                raise ValueError("Nine-point top P/PN differs from the already saved owner-specific trace samples")
        if len(edge["samples"]) != 3:
            raise ValueError("Require the three original top-edge samples")
        original_local = element[cell].reshape(4, 2)
        saved_weak = [-fsum(float(original_local[local, axis]) for local in (2, 3)) for axis in (0, 1)]
        if saved_weak != old["force_on_body_N"]:
            raise ValueError("Original TR/TL element-local material force differs from M-SUPPORT1 exactly")
        q_terms = [[-float(weights[q])*float(P[cell, q, axis, 1])*float(gchi[q, 1])
                    for axis in (0, 1)] for q in range(9)]
        direct = _vector_sum(q_terms)
        samples = [dict(point_index=q, reference_point=points[q].tolist(),
            coordinates_mm=((lo+hi)/2+points[q]*(hi-lo)/2).tolist(), P_normal_column_MPa=P[cell, q, :, 1].tolist(),
            saved_volume_weight_mm3=float(weights[q]), selected_basis_gradient_per_mm=gchi[q].tolist(),
            rounded_P_volume_contribution_on_body_N=q_terms[q]) for q in range(9)]
        depths = []
        for depth, eta_value in enumerate((-1., 0., 1.)):
            q = [depth, depth+3, depth+6]
            C = [-thickness_mm*hx/6*fsum(s*float(P[cell, point, axis, 1])
                    for s, point in zip((1., 4., 1.), q)) for axis in (0, 1)]
            Q = _vector_sum([q_terms[point] for point in q])
            depths.append(dict(eta=eta_value, point_indices=q, C_eta_on_body_N=C,
                regrouped_same_q_terms_on_body_N=Q,
                geometric_depth_contribution_on_body_N=[(1., 4., 1.)[depth]*v/6 for v in C]))
        regrouped = _vector_sum([row["regrouped_same_q_terms_on_body_N"] for row in depths])
        errors = [a-b for a, b in zip(regrouped, direct)]
        bounds = [8*2.**-52*fsum(abs(term[axis]) for term in q_terms) for axis in (0, 1)]
        if any(abs(error) > bound for error, bound in zip(errors, bounds)):
            raise ValueError("Same rounded-P q-term regrouping exceeds 8eps q-term L1")
        C = [row["C_eta_on_body_N"] for row in depths]
        geometry = [fsum((C[0][axis], 4*C[1][axis], C[2][axis]))/6 for axis in (0, 1)]
        geometry_gap = [fsum((C[0][axis], 4*C[1][axis], -5*C[2][axis]))/6 for axis in (0, 1)]
        top = list(edge["material_line_estimate_on_body_N"])
        records.append(dict(cell_id=cell, node_ids=conn[cell].tolist(), selected_local_indices=[2, 3],
            selected_body_node_ids=conn[cell, [2, 3]].tolist(), reference_coordinates_mm=quad.tolist(),
            original_local_internal_material_force_N=original_local.tolist(),
            saved_weak_material_on_body_N=saved_weak, saved_top_material_line_on_body_N=top,
            samples=samples, depths=depths, rounded_P_direct_volume_on_body_N=direct,
            regrouped_same_q_terms_on_body_N=regrouped,
            same_q_term_regrouping=dict(error_N=errors, roundoff_bound_N=bounds, passed=True,
                bound_source="8*eps*sum(abs(the same nine computed q terms)); no absolute floor"),
            geometric_three_depth_volume_on_body_N=geometry,
            geometric_depth_gap_on_body_N=geometry_gap,
            descriptive_differences_N=dict(saved_weak_minus_rounded_P_volume=[a-b for a, b in zip(saved_weak, direct)],
                geometric_volume_minus_direct=[a-b for a, b in zip(geometry, direct)],
                geometric_top_C_minus_saved_top_line=[a-b for a, b in zip(C[2], top)],
                direct_volume_minus_saved_top_line=[a-b for a, b in zip(direct, top)],
                geometric_depth_gap_minus_geometric_volume_minus_geometric_top=[a-(b-c) for a, b, c in zip(geometry_gap, geometry, C[2])],
                saved_weak_minus_saved_top_line=[a-b for a, b in zip(saved_weak, top)],
                geometric_depth_gap_minus_direct_volume_minus_saved_top_line=[a-(b-c) for a, b, c in zip(geometry_gap, direct, top)])))
    return dict(schema_version="saved-bottom-owner-material-volume-1.0", identity=dict(identity), cells=records,
        counts=dict(samples=18, depths=6, cells=2), units="P: MPa; forces: N; original thickness20mm included once",
        operator_binding="Exact saved NumPy operator expressions; xi slow, eta fast; original TR/TL basis sum gradient (0,2/mm)",
        contraction_scope="Independent ordinary float64 contraction of rounded exported P; original compensated weak force retained separately",
        depth_scope="C_eta is a sample-layer comparison. Direct volume uses all nine q terms; the original top trace is copied, not newly integrated.",
        qualification="Same-term algebra regrouping and descriptive saved material diagnosis only; no new kernel, Hu boundary, pressure, effective-grip or equilibrium qualification")
