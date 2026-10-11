"""Owner-resolved saved Q1 Hu vertex actions, without mechanics or recovery.

Original element_regularization_force is authoritative. Adjacent owner endpoint
actions can cancel for common translation while assembled edge-node actions do
not vanish. These covectors are in N, including thickness; they are not pressure.
"""
from __future__ import annotations

from math import fsum
import numpy as np

ROLES = ("body", "bottom_owner", "left_owner", "right_owner", "corner_only")
LOCAL_NAMES = ("BL", "BR", "TR", "TL")
SIGNS = (1., -1., 1., -1.)


def _vector(values):
    return [fsum(float(value[axis]) for value in values) for axis in (0, 1)]


def _closure(actual, original, values, source):
    errors = [a-b for a, b in zip(actual, original)]
    bounds = [8*2.**-52*fsum(abs(float(value[axis])) for value in values) for axis in (0, 1)]
    if any(abs(error) > bound for error, bound in zip(errors, bounds)):
        raise ValueError(source+" regrouping exceeds its original-force L1 roundoff bound")
    return dict(error_N=errors, roundoff_bound_N=bounds, passed=True, bound_source=source+"; 8eps times L1, no floor")


def observe_saved_q1_hu_boundary(element_regularization_force, saved_support_cells, original_nodes,
                                 body_metadata, grid, *, identity, original_whole_regularization_N,
                                 selected_endpoint_cell_ids, global_fixed_dofs):
    """Associate original Hu weak covectors with preserved support topology.

    The caller supplies parsed M-SUPPORT1 cell topology, original M-LEDGER2 node
    strings, and original ordinary model/state metadata. Only the 722 support
    cells are observed. A compact 1406-DOF bincount preserves original ascending
    cell/local/component C order before negating internal forces. It must match
    every original body-node Hu vector numerically exactly (not signed-zero or
    byte equality). New fsum regrouping uses selected-local L1; the existing
    node-L1 whole comparison remains separate. No full-domain scatter is made.
    """
    element = np.asarray(element_regularization_force)
    if (element.dtype != np.dtype("float64") or element.shape != (13440, 8)
            or grid["shape_yx"] != [80, 168] or grid["cell_size_mm"] != [.5, .5]
            or grid["origin_mm"] != [0., 0.] or grid["axes"] != [[1., 0.], [0., 1.]]
            or grid["array_order"] != "C_yx_bottom_up" or selected_endpoint_cell_ids != [10371, 10407, 10408]):
        raise ValueError("Require the preserved h0.5 native grid, Hu field and selected endpoint cells")
    body_nodes, body_cells = body_metadata["nodes"], set(body_metadata["cells"])
    if (len(body_nodes) != 703 or len(body_cells) != 648 or body_nodes != sorted(set(body_nodes))
            or sorted(body_metadata["dofs"]) != [2*node+axis for node in body_nodes for axis in (0, 1)]
            or body_metadata["fixed_dofs"] != 1406
            or not set(body_metadata["dofs"]).issubset(global_fixed_dofs)):
        raise ValueError("Require the original complete fixed-body metadata")
    node_rows = sorted(original_nodes, key=lambda row: int(row["node_id"]))
    supports = sorted(saved_support_cells, key=lambda row: row["cell_id"])
    if (len(supports) != 722 or len({row["cell_id"] for row in supports}) != 722
            or [int(row["node_id"]) for row in node_rows] != body_nodes
            or any(row["identity"] != identity for row in supports)):
        raise ValueError("Original selected support/node identities or coverage differ")
    body_set, position = set(body_nodes), {node: index for index, node in enumerate(body_nodes)}

    def coordinates(node):
        y, x = divmod(node, 169)
        return [x*.5, y*.5]

    for row in node_rows:
        row_identity = dict(index=int(row["index"]), original_target_index=int(row["original_target_index"]),
            leg=row["leg"], d_mm=float(row["d_mm"]), state_sha256=row["state_sha256"])
        if row_identity != identity or coordinates(int(row["node_id"])) != [float(row["x_mm"]), float(row["y_mm"])]:
            raise ValueError("Original node identity or grid-derived reference coordinates differ")
    local = element.reshape(13440, 4, 2)
    cells, selected_endpoints, compact_dofs, internal_values = [], [], [], []
    by_node = {node: [] for node in body_nodes}
    by_role = {role: [] for role in ROLES}
    role_indices = {"body": [0, 1, 2, 3], "bottom_owner": [2, 3], "left_owner": [1, 2], "right_owner": [0, 3]}
    for support in supports:
        cell, role = support["cell_id"], support["group"]
        if not 0 <= cell < 13440 or role not in ROLES:
            raise ValueError("Invalid original support cell or role")
        y, x = divmod(cell, 168)
        bl = y*169+x
        nodes = [bl, bl+1, bl+170, bl+169]
        selected = [index for index, node in enumerate(nodes) if node in body_set]
        if (nodes != support["node_ids"] or selected != support["selected_local_indices"]
                or [nodes[index] for index in selected] != support["selected_body_node_ids"]
                or len(selected) != support["selected_local_node_count"]
                or ((cell in body_cells) != (role == "body"))
                or (role != "corner_only" and selected != role_indices[role])
                or (role == "corner_only" and (cell, selected) not in ((10371, [2]), (10408, [3])))):
            raise ValueError("Preserved support role/connectivity/body selection differs")
        original = local[cell]
        expected = np.asarray(SIGNS)[:, None]*original[0]
        if not np.isfinite(original).all() or not np.array_equal(original, expected):
            raise ValueError("Original selected Hu covector does not have the Q1 +,-,+,- pattern")
        on_body = [(-original[index]).tolist() for index in selected]
        for index, value in zip(selected, on_body):
            node = nodes[index]
            by_node[node].append(value)
            by_role[role].append(value)
            for axis in (0, 1):
                compact_dofs.append(2*position[node]+axis)
                internal_values.append(original[index, axis])
        cells.append(dict(cell_id=cell, group=role, node_ids=nodes, selected_local_indices=selected,
            selected_body_node_ids=[nodes[index] for index in selected], selected_local_node_count=len(selected),
            original_local_internal_Hu_force_N=original.tolist(), original_BL_internal_Hu_N=original[0].tolist(),
            Q1_sign_pattern=SIGNS, Q1_pattern_numeric_exact=True, force_on_body_N=_vector(on_body)))
        if cell in selected_endpoint_cell_ids:
            for index, node in enumerate(nodes):
                selected_endpoints.append(dict(cell_id=cell, group=role, local_node_index=index,
                    local_node_name=LOCAL_NAMES[index], node_id=node, coordinates_mm=coordinates(node),
                    selected_body_node=index in selected, original_internal_Hu_force_N=original[index].tolist(),
                    negative_local_Hu_covector_N=(-original[index]).tolist(),
                    covector_scope="ON-body only if selected_body_node; otherwise negative local covector, not an applied physical load"))
    expected_counts = {"body": 648, "bottom_owner": 36, "left_owner": 18, "right_owner": 18, "corner_only": 2}
    if ({role: sum(cell["group"] == role for cell in cells) for role in ROLES} != expected_counts
            or sum(len(values) for values in by_node.values()) != 2738
            or any(not values or len(values) > 4 for values in by_node.values())
            or len(selected_endpoints) != 12):
        raise ValueError("Original support incidence counts differ")
    scatter = -np.bincount(compact_dofs, weights=internal_values, minlength=1406).reshape(703, 2)
    original_node_values = [[float(row["regularization_F"+axis+"_N"]) for axis in "xy"] for row in node_rows]
    if not np.array_equal(scatter, original_node_values):
        raise ValueError("Original C-order compact body Hu scatter differs from saved nodes")
    nodes = []
    for row, original in zip(node_rows, original_node_values):
        node = int(row["node_id"])
        regrouped = _vector(by_node[node])
        nodes.append(dict(original_node_record=dict(row), node_id=node, selected_local_occurrences=len(by_node[node]),
            regrouped_local_Hu_on_body_N=regrouped, original_Hu_on_body_N=original,
            local_regrouping=_closure(regrouped, original, by_node[node], "selected original local Hu forces")))
    values = [value for node in body_nodes for value in by_node[node]]
    local_whole, node_whole = _vector(values), _vector(original_node_values)
    old_whole = list(original_whole_regularization_N)
    groups = {role: dict(cell_count=expected_counts[role], local_occurrence_count=len(by_role[role]),
        force_on_body_N=_vector(by_role[role])) for role in ROLES}
    corners = [cell for cell in cells if cell["group"] == "corner_only"]
    corner_whole = _vector([cell["force_on_body_N"] for cell in corners])
    role_whole = _vector([groups[role]["force_on_body_N"] for role in ROLES])
    whole = dict(regrouped_local_Hu_on_body_N=local_whole, original_node_Hu_on_body_N=node_whole,
        original_state_Hu_on_body_N=old_whole, corner_only_Hu_on_body_N=corner_whole,
        original_node_L1_comparison=_closure(node_whole, old_whole, original_node_values, "original node Hu forces"),
        selected_local_L1_comparison=_closure(local_whole, node_whole, values, "selected original local Hu forces"),
        descriptive_differences_N=dict(local_minus_original_state=[a-b for a, b in zip(local_whole, old_whole)],
            local_minus_corner_only=[a-b for a, b in zip(local_whole, corner_whole)],
            regrouped_five_roles_minus_local=[a-b for a, b in zip(role_whole, local_whole)]))
    return dict(schema_version="saved-fixed-square-Q1-Hu-boundary-1.0", identity=dict(identity), cells=cells,
        groups=groups, whole=whole, nodes=nodes, corner_only_cells=corners, selected_endpoints=selected_endpoints,
        counts=dict(cells=722, local_occurrences=2738, groups=5, whole=1, nodes=703, selected_endpoints=12),
        original_Hu_pattern=dict(support_cells_checked=722, numeric_exact=True, byte_or_signed_zero_gate=False),
        original_body_scatter=dict(calls=1, body_DOFs=1406, numeric_exact=True,
            order="Ascending original cell/local/component C order; internal bincount then negate; body DOFs only"),
        units="N, original thickness included; reference coordinates mm",
        interpretation="Original Q1 Hu weak vertex covectors. Adjacent side pairs cancel for common translation; assembled side-node actions need not vanish. Preserve corner owners; no unique allocation to incident pressure faces.",
        qualification="Saved support/vertex interpretation and original body scatter only; no Hu reconstruction, hyperstress recovery, force-kernel, tangent, HP, equilibrium, energy-gradient, pressure or effective-grip qualification")
