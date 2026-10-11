"""Saved material weak-load basis support; no force-kernel or equilibrium calls.

Ordinary arrays only. Replaying the original C-order scatter checks saved data;
new local fsum comparisons use 8*eps*selected-local L1, with no absolute floor.
Owner groups describe basis support, not face traction or contact pressure.
"""
from __future__ import annotations

from math import fsum
import numpy as np

GROUPS = ("body", "bottom_owner", "left_owner", "right_owner", "corner_only")


def _vector(values):
    return [fsum(float(value[axis]) for value in values) for axis in (0, 1)]


def _closure(actual, original, local_values):
    errors = [a-b for a, b in zip(actual, original)]
    bounds = [8*2.**-52*fsum(abs(float(value[axis])) for value in local_values) for axis in (0, 1)]
    if any(abs(error) > bound for error, bound in zip(errors, bounds)):
        raise ValueError("Local material regrouping exceeds its selected-local force L1 roundoff bound")
    return dict(error_N=errors, roundoff_bound_N=bounds, passed=True,
                bound_source="8*eps*sum(abs(selected original element-local material force)); no absolute floor")


def observe_saved_workpiece_material_support(model, forces, body_metadata, *, identity, material_trace):
    """Project saved element-local material forces onto fixed workpiece nodes.

    model provides coordinates/connectivity/edofs/workpiece_nodes. Body cell,
    node, DOF and complete fixed-DOF IDs come from original model JSON metadata.
    material_trace supplies the selected identity and already saved outside
    face-owner IDs. Each element-local body-node occurrence occurs once; ON-body
    force is minus its internal force, in N with original thickness included.
    Original material np.bincount assembly is replayed once in C-order and must
    reproduce the saved full global vector exactly. Nodes/whole are separately
    recomposed with fsum, using their selected-local L1 bounds only.
    """
    xy = np.asarray(model["coordinates"], dtype=float)
    conn, edofs = np.asarray(model["connectivity"]), np.asarray(model["edofs"])
    nodes, body_cells = np.asarray(model["workpiece_nodes"]), np.asarray(body_metadata["cells"])
    body_dofs, fixed = np.asarray(body_metadata["dofs"]), np.asarray(body_metadata["fixed_dofs"])
    element = np.asarray(forces["element_material_force"], dtype=float)
    global_force = np.asarray(forces["global_material_force"], dtype=float)
    if (xy.ndim != 2 or xy.shape[1] != 2 or conn.ndim != 2 or conn.shape[1] != 4
            or any(array.dtype.kind not in "iu" for array in (conn, edofs, nodes, body_cells, body_dofs, fixed))
            or any(array.ndim != 1 for array in (nodes, body_cells, body_dofs, fixed))
            or not len(nodes) or not len(body_cells) or len(np.unique(nodes)) != len(nodes)
            or len(np.unique(body_cells)) != len(body_cells)
            or np.any(conn < 0) or np.any(conn >= len(xy))
            or np.any(body_cells < 0) or np.any(body_cells >= len(conn))
            or element.shape != (len(conn), 8) or global_force.shape != (2*len(xy),)
            or not np.isfinite(xy).all() or not np.isfinite(element).all() or not np.isfinite(global_force).all()
            or not np.array_equal(edofs, (2*conn[:, :, None]+np.arange(2)).reshape(-1, 8))):
        raise ValueError("Require finite saved Q1 material arrays with original interleaved element DOFs")
    expected_dofs = (2*nodes[:, None]+np.arange(2)).ravel()
    if (not np.array_equal(nodes, body_metadata["nodes"])
            or not np.array_equal(np.sort(nodes), np.unique(conn[body_cells]))
            or not np.array_equal(np.sort(body_dofs), np.sort(expected_dofs))
            or not np.all(np.isin(expected_dofs, fixed)) or material_trace["identity"] != identity):
        raise ValueError("Saved workpiece metadata, fixed components or trace identity differ")
    replay = np.bincount(edofs.ravel(order="C"), weights=element.ravel(order="C"), minlength=2*len(xy))
    if not np.array_equal(replay, global_force):
        raise ValueError("Original C-order material scatter does not reproduce the saved global vector exactly")
    locations = np.argwhere(np.isin(conn, nodes))
    support_cells = np.unique(locations[:, 0])
    assigned = {int(cell): "body" for cell in body_cells}
    for edge in material_trace["edges"]:
        cell, face = int(edge["outer_cell_id"]), edge["face"]
        if face not in ("bottom", "left", "right") or cell in assigned or cell not in support_cells:
            raise ValueError("Saved outside face owners must be distinct nonbody support cells")
        if (not np.array_equal(conn[cell], edge["outer_node_ids"])
                or not np.array_equal(np.sort(conn[cell][np.isin(conn[cell], nodes)]), edge["node_ids"])):
            raise ValueError("Saved outside owner connectivity/body-node pair differs from the original trace edge")
        assigned[cell] = face+"_owner"
    lower, upper = xy[nodes].min(axis=0), xy[nodes].max(axis=0)
    for cell in support_cells:
        if int(cell) in assigned:
            continue
        selected = conn[cell][np.isin(conn[cell], nodes)]
        if (len(selected) != 1 or xy[selected[0], 1] != lower[1]
                or xy[selected[0], 0] not in (lower[0], upper[0])):
            raise ValueError("Remaining support cells must meet only one physical bottom corner node")
        assigned[int(cell)] = "corner_only"
    occurrences, by_cell, by_node = [], {}, {int(node): [] for node in nodes}
    local = element.reshape(-1, 4, 2)
    for cell, local_node in locations:
        node = int(conn[cell, local_node])
        row = dict(cell_id=int(cell), local_node_index=int(local_node), node_id=node, group=assigned[int(cell)],
            coordinates_mm=xy[node].tolist(), internal_material_force_N=local[cell, local_node].tolist(),
            force_on_body_N=(-local[cell, local_node]).tolist())
        occurrences.append(row)
        by_cell.setdefault(int(cell), []).append(row)
        by_node[node].append(row)
    cells = [dict(cell_id=cell, group=assigned[cell], node_ids=conn[cell].tolist(),
        selected_local_indices=[row["local_node_index"] for row in rows],
        selected_body_node_ids=[row["node_id"] for row in rows], selected_local_node_count=len(rows),
        force_on_body_N=_vector([row["force_on_body_N"] for row in rows])) for cell, rows in by_cell.items()]
    node_rows = []
    for node, rows in by_node.items():
        if len(rows) > 4:
            raise ValueError("The local regrouping bound requires at most four element-local occurrences per body node")
        values = [row["force_on_body_N"] for row in rows]
        regrouped, original = _vector(values), (-global_force[2*node:2*node+2]).tolist()
        node_rows.append(dict(node_id=node, coordinates_mm=xy[node].tolist(), selected_local_occurrences=len(rows),
            support_cell_ids=[row["cell_id"] for row in rows], regrouped_local_force_on_body_N=regrouped,
            saved_global_force_on_body_N=original, closure=_closure(regrouped, original, values)))
    groups = {name: dict(cell_count=sum(row["group"] == name for row in cells),
        local_occurrence_count=sum(row["group"] == name for row in occurrences),
        force_on_body_N=_vector([row["force_on_body_N"] for row in occurrences if row["group"] == name])) for name in GROUPS}
    values = [row["force_on_body_N"] for row in occurrences]
    local_whole = _vector(values)
    saved_whole = _vector([row["saved_global_force_on_body_N"] for row in node_rows])
    whole = dict(regrouped_local_force_on_body_N=local_whole, saved_global_force_on_body_N=saved_whole,
        closure=_closure(local_whole, saved_whole, values))
    return dict(schema_version="saved-fixed-square-material-support-1.0", identity=dict(identity),
        occurrences=occurrences, cells=cells, nodes=node_rows, groups=groups, whole=whole,
        counts=dict(local_occurrences=len(occurrences), support_cells=len(cells), body_nodes=len(node_rows)),
        max_local_occurrences_per_node=max(len(rows) for rows in by_node.values()),
        global_replay=dict(calls=1, original_C_order_bincount_exact=True),
        units="N, original thickness already included; reference positions in mm",
        grouping_scope="Element basis support on body nodes; saved exterior owners name three groups, not faces of pressure",
        qualification="Saved material assembly replay and local regrouping only; no new force-kernel, Hu boundary, pressure, effective-grip or equilibrium qualification")
