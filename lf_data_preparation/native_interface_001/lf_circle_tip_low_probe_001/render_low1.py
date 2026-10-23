"""One pure low-input cache display and exact-common-q comparison; no HF imports."""
from __future__ import annotations

import argparse
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path
from time import monotonic

STARTED = monotonic()

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection, PolyCollection
from matplotlib.colors import LogNorm, Normalize
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator
from PIL import Image


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+"\n", encoding="utf-8")


def boundary_edges(connectivity, cells):
    """Reference member topology only; deformed positions never reselect cells."""
    counts = {}
    for quad in connectivity[cells]:
        for a, b in zip(quad, np.roll(quad, -1)):
            pair = tuple(sorted((int(a), int(b))))
            counts[pair] = counts.get(pair, 0)+1
    return np.asarray([pair for pair, count in counts.items() if count == 1], dtype=int)


def cross(a, b):
    return a[..., 0]*b[..., 1]-a[..., 1]*b[..., 0]


def nearest_point(point, segments):
    a, step = segments[:, 0], segments[:, 1]-segments[:, 0]
    squared = np.sum(step*step, axis=1)
    t = np.clip(np.sum((point-a)*step, axis=1)/np.where(squared == 0, 1., squared), 0., 1.)
    projected = a+t[:, None]*step
    distances = np.sum((projected-point)**2, axis=1)
    index = int(np.argmin(distances))
    return float(np.sqrt(distances[index])), projected[index], index


def vertices_to_edges(vertices, edges):
    best = (float("inf"), None, None)
    a, step = edges[:, 0], edges[:, 1]-edges[:, 0]
    squared = np.sum(step*step, axis=1)
    for start in range(0, len(vertices), 256):
        points = vertices[start:start+256]
        t = np.clip(np.sum((points[:, None]-a)*step, axis=2)/np.where(squared == 0, 1., squared), 0., 1.)
        projected = a+t[:, :, None]*step
        squared_distance = np.sum((points[:, None]-projected)**2, axis=2)
        index = np.unravel_index(int(np.argmin(squared_distance)), squared_distance.shape)
        distance = float(np.sqrt(squared_distance[index]))
        if distance < best[0]:
            best = distance, points[index[0]].copy(), projected[index].copy()
    return best


def closest_boundaries(left, right):
    """Segment distance and intersection in displayed binary64 geometry only."""
    hit, proper = None, False
    for start in range(0, len(left), 256):
        a, da = left[start:start+256, 0, None], (left[start:start+256, 1]-left[start:start+256, 0])[:, None]
        b, db = right[None, :, 0], (right[:, 1]-right[:, 0])[None]
        denominator = cross(da, db)
        nonparallel = denominator != 0
        safe = np.where(nonparallel, denominator, 1.)
        t, u = cross(b-a, db)/safe, cross(b-a, da)/safe
        intersects = nonparallel & (t >= 0) & (t <= 1) & (u >= 0) & (u <= 1)
        proper = proper or bool(np.any(intersects & (t > 0) & (t < 1) & (u > 0) & (u < 1)))
        if hit is None and np.any(intersects):
            i, j = np.argwhere(intersects)[0]
            hit = a[i, 0]+t[i, j]*da[i, 0]
    if hit is not None:
        return dict(distance_mm=0., first_point_mm=hit.tolist(), second_point_mm=hit.tolist(),
                    nonparallel_boundary_intersection=True, proper_segment_crossing=proper)
    first = vertices_to_edges(left.reshape(-1, 2), right)
    second = vertices_to_edges(right.reshape(-1, 2), left)
    if second[0] < first[0]:
        first = second[0], second[2], second[1]
    return dict(distance_mm=first[0], first_point_mm=first[1].tolist(), second_point_mm=first[2].tolist(),
                nonparallel_boundary_intersection=False, proper_segment_crossing=False)


def inside_any_convex_cell(points, polygons):
    """Strict interior observation; boundary equality is not counted inside."""
    found = np.zeros(len(points), dtype=bool)
    for start in range(0, len(points), 128):
        selected = points[start:start+128]
        edges = np.roll(polygons, -1, axis=1)-polygons
        signed = cross(edges[None], selected[:, None, None]-polygons[None])
        found[start:start+128] = np.any(np.all(signed > 0, axis=2) | np.all(signed < 0, axis=2), axis=1)
    return int(found.sum())


def comparison_scalars(row):
    """Signed original observations; increments never replace raw preload."""
    values = dict(Q_total_N=row["Q_drive_half_N"], R_input_N=row["R_input_N"],
        input_mean_mm=row["input_mean_mm"], tip_to_body_boundary_mm=row["tip_to_body_boundary_mm"],
        mechanism_to_body_boundary_mm=row["mechanism_to_body_boundary"]["distance_mm"],
        body_to_right_boundary_mm=row["body_to_right_boundary"]["distance_mm"],
        global_minimum_J=row["minimum_J"], global_maximum_abs_Hu_per_mm=row["max_abs_Hu_per_mm"],
        nonbody_medium_minimum_J=row["medium"]["minimum_J"],
        nonbody_medium_maximum_abs_Hu_per_mm=row["medium"]["maximum_abs_Hu_per_mm"],
        right480_minimum_J=row["right_medium"]["minimum_J"],
        right480_maximum_abs_Hu_per_mm=row["right_medium"]["maximum_abs_Hu_per_mm"],
        relative_residual=row["relative_residual"], constraint_residual=row["constraint_residual"],
        constraint_bound=row["constraint_bound"], relative_global_force_balance=row["relative_global_force_balance"],
        max_abs_prescribed_error_mm=row["max_abs_prescribed_error_mm"])
    for name, label in (("total", "total"), ("material", "material"), ("regularization", "Hu")):
        values["Q_"+label+"_N"] = -row["force_on_body_N"][name][0]
        for axis, component in enumerate(("Fx", "Fy")):
            values["ON_body_"+component+"_"+label+"_N"] = row["force_on_body_N"][name][axis]
    for name, vector in row["ledger"].items():
        for axis, component in enumerate(("x", "y")):
            values["ledger_"+name+"_"+component] = vector[axis]
    return values


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", required=True)
    parser.add_argument("--parent", required=True)
    parser.add_argument("--result", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    protocol_file, parent_file = Path(args.protocol).resolve(), Path(args.parent).resolve()
    result_file, output = Path(args.result).resolve(), Path(args.output).resolve()
    protocol = json.loads(protocol_file.read_bytes())
    viewer_deadline = min(STARTED+float(protocol["viewer_seconds"]),
        float(os.environ["LOW1_HELPER_DEADLINE"]), float(os.environ["LOW1_VIEWER_DEADLINE"]))
    observer_file = Path(protocol["observer_definition_path"])
    observer_bytes = observer_file.read_bytes()
    observer = json.loads(observer_bytes)
    parent_bytes = parent_file.read_bytes()
    parent = json.loads(parent_bytes)
    result_bytes = result_file.read_bytes()
    result = json.loads(result_bytes)
    high_file = Path(protocol["high_state_table_path"])
    high_bytes = high_file.read_bytes()
    if sha256(high_bytes).hexdigest() != protocol["high_state_table_sha256"]:
        raise ValueError("Bound high-input ordinary table identity differs")
    high = json.loads(high_bytes)
    rows = result["accepted_steps"]
    if (result["schema_version"] != "hf-native-guided-probe-1.0" or result["status"] != "success"
            or not result["target_reached"] or not 2 <= len(rows) <= 17
            or result["probe_task"]["held_input_mean_mm"] != .5
            or result["probe_task"]["body_q_targets_mm"] != [0., .025]
            or parent["status"] != "success" or not all(parent[key] is True for key in
                ("path_completed", "target_reached", "loading_peak_reached"))
            or parent["targets_mm"] != [0., .25, .5]
            or [row["d"] for row in parent["states"] if row["is_original_target"]] != [0., .25, .5]
            or rows[0]["body_q_mm"] != 0. or rows[-1]["body_q_mm"] != .025
            or any(b["body_q_mm"] <= a["body_q_mm"] for a, b in zip(rows, rows[1:]))):
        raise ValueError("Pure display requires both successful authorized new paths and 2..17 actual probe states")
    last_parent = parent["states"][-1]
    if (last_parent["d"] != .5 or last_parent["is_original_target"] is not True
            or result["source"]["parent_result"]["sha256"] != sha256(parent_bytes).hexdigest()
            or result["source"]["selected_state"]["accepted_index"] != len(parent["states"])-1
            or rows[0]["state_sha256"] != last_parent["state_sha256"]
            or np.float64(rows[0]["R_input_N"]).tobytes() != np.float64(last_parent["R_input"]).tobytes()
            or rows[0]["newton_checks"] != 1):
        raise ValueError("New probe q0 is not the identity-matched genuine new parent terminal state")
    if (high["schema_version"] != "hf-ctipprobe1-state-table-1" or high["accepted_states"] != len(high["states"])
            or any(row["input_mean_mm"] != 1.06 for row in high["states"])
            or high["states"][0]["body_q_mm"] != 0.):
        raise ValueError("High-input ordinary table has a different comparison definition")
    output.mkdir(parents=True, exist_ok=False)

    def checkpoint(phase):
        if monotonic() >= viewer_deadline:
            raise TimeoutError("Pure viewer shared deadline reached")
        write_json(output/"renderer_checkpoint.json", dict(phase=phase, elapsed_seconds=monotonic()-STARTED,
            parent_file=parent_file.as_posix(), result_file=result_file.as_posix(), scientific_calls=0))

    coordinates = np.asarray(result["model"]["coordinates_mm"], dtype=float)
    connectivity = np.asarray(result["model"]["connectivity"], dtype=int)
    solid = np.asarray(result["model"]["solid"], dtype=bool)
    body_cells, body_nodes = np.asarray(observer["body_cells"], int), np.asarray(observer["body_nodes"], int)
    right_cells = np.asarray(observer["right_medium_cells"], int)
    right_nodes = np.asarray(observer["right_boundary_nodes"], int)
    right_nodes = right_nodes[np.argsort(coordinates[right_nodes, 1])]
    right_edges = np.column_stack((right_nodes[:-1], right_nodes[1:]))
    tip_node = int(observer["tip_node"])
    input_nodes = np.asarray(observer["input_nodes"], int)
    input_weights = np.asarray(observer["input_weights"], float)
    if (body_nodes.tolist() != result["model"]["body_nodes"] or len(right_cells) != 480
            or np.any(solid[right_cells]) or np.intersect1d(right_cells, body_cells).size
            or set(np.unique(connectivity[body_cells]).tolist()) != set(body_nodes.tolist())):
        raise ValueError("New-model reference members differ from the frozen observer")
    medium_mask = ~solid.copy()
    medium_mask[body_cells] = False
    medium_cells, solid_cells = np.flatnonzero(medium_mask), np.flatnonzero(solid)
    body_edges = boundary_edges(connectivity, body_cells)
    solid_edges = boundary_edges(connectivity, solid_cells)
    cut_y = float(observer["reference_domain_extent_mm"][1])
    body_physical_edges = body_edges[~np.all(coordinates[body_edges, 1] == cut_y, axis=1)]
    solid_physical_edges = solid_edges[~np.all(coordinates[solid_edges, 1] == cut_y, axis=1)]
    quadrature = np.asarray(observer["simpson_points"], float)
    xi, eta = quadrature[:, 0], quadrature[:, 1]
    shape = np.column_stack(((1-xi)*(1-eta), (1+xi)*(1-eta), (1+xi)*(1+eta), (1-xi)*(1+eta)))/4.
    states, table, accesses = [], [], []
    for index, row in enumerate(rows):
        checkpoint(f"read_new_state_{index:03d}")
        positions = np.asarray(row["positions_mm"], float)
        if positions.shape != coordinates.shape or not np.isfinite(positions).all():
            raise ValueError("New displayed positions differ from the ordinary model shape")
        field_file = (result_file.parent/row["fields"]["path"]).resolve()
        field_file.relative_to(result_file.parent)
        payload = field_file.read_bytes()
        if sha256(payload).hexdigest() != row["fields"]["sha256"]:
            raise ValueError("New accepted archive byte identity differs")
        fields = {}
        with np.load(BytesIO(payload), allow_pickle=False) as archive:
            for name in ("J", "Hu"):
                value, declared = archive[name], row["fields"]["fields"][name]
                if (value.dtype.name != declared["dtype"] or list(value.shape) != declared["shape"]
                        or sha256(value.tobytes(order="C")).hexdigest() != declared["sha256"]):
                    raise ValueError("New displayed field identity differs: "+name)
                fields[name] = value.copy()
        J, Hu = fields["J"], fields["Hu"]
        if J.shape != (len(connectivity), 9) or Hu.shape != (len(connectivity), 2, 2, 2) or not np.isfinite(J).all() or not np.isfinite(Hu).all() or np.any(J <= 0):
            raise ValueError("New observation fields violate their declared display contract")
        cell_J, cell_Hu = J.min(axis=1), np.abs(Hu).max(axis=(1, 2, 3))
        minimum_cell = int(medium_cells[np.argmin(cell_J[medium_cells])])
        minimum_sample = int(np.argmin(J[minimum_cell]))
        Hu_cell = int(medium_cells[np.argmax(cell_Hu[medium_cells])])
        actual_minimum_point = shape[minimum_sample] @ positions[connectivity[minimum_cell]]
        Hu_point = positions[connectivity[Hu_cell]].mean(axis=0)
        tip_distance, tip_nearest, tip_edge = nearest_point(positions[tip_node], positions[body_physical_edges])
        proximity = closest_boundaries(positions[solid_physical_edges], positions[body_physical_edges])
        right_gap = closest_boundaries(positions[body_physical_edges], positions[right_edges])
        solid_inside = inside_any_convex_cell(positions[np.unique(solid_physical_edges)], positions[connectivity[body_cells]])
        body_inside = inside_any_convex_cell(positions[np.unique(body_physical_edges)], positions[connectivity[solid_cells]])
        right_minimum = int(right_cells[np.argmin(cell_J[right_cells])])
        right_Hu = int(right_cells[np.argmax(cell_Hu[right_cells])])
        component_tail = [row["force_on_body_N"]["material"][axis]+row["force_on_body_N"]["regularization"][axis]
                          -row["force_on_body_N"]["total"][axis] for axis in (0, 1)]
        summary = dict(accepted_index=index, **{key: row[key] for key in
            ("body_q_mm", "input_mean_mm", "R_input_N", "Q_drive_half_N", "force_on_body_N", "ledger", "relative_residual",
             "constraint_residual", "constraint_bound", "relative_global_force_balance", "minimum_J", "max_abs_Hu_per_mm",
             "max_abs_prescribed_error_mm", "newton_checks", "is_original_target", "original_target_index", "bisection_depth", "state_sha256")},
            delta_Q_from_q0_N=row["Q_drive_half_N"]-rows[0]["Q_drive_half_N"],
            component_sum_minus_total_on_body_N=component_tail,
            component_sum_minus_total_Q_N=-component_tail[0],
            tip_node=tip_node, tip_position_mm=positions[tip_node].tolist(), tip_to_body_boundary_mm=tip_distance,
            tip_nearest_body_point_mm=tip_nearest.tolist(), tip_nearest_reference_edge=body_physical_edges[tip_edge].tolist(),
            mechanism_to_body_boundary=proximity, body_to_right_boundary=right_gap,
            strict_containment_counts=dict(solid_boundary_nodes_inside_body=solid_inside, body_boundary_nodes_inside_solid=body_inside),
            geometric_overlap_observed=bool(proximity["proper_segment_crossing"] or solid_inside or body_inside),
            body_actual_bbox_mm=[positions[body_nodes].min(axis=0).tolist(), positions[body_nodes].max(axis=0).tolist()],
            right_boundary_actual_bbox_mm=[positions[right_nodes].min(axis=0).tolist(), positions[right_nodes].max(axis=0).tolist()],
            medium=dict(cells=len(medium_cells), minimum_J=float(cell_J[minimum_cell]), minimum_J_cell=minimum_cell,
                minimum_J_sample=minimum_sample, minimum_J_reference_point=quadrature[minimum_sample].tolist(),
                minimum_J_actual_point_mm=actual_minimum_point.tolist(), maximum_abs_Hu_per_mm=float(cell_Hu[Hu_cell]),
                maximum_Hu_cell=Hu_cell, maximum_Hu_actual_cell_centroid_mm=Hu_point.tolist()),
            right_medium=dict(cells=len(right_cells), minimum_J=float(cell_J[right_minimum]), minimum_J_cell=right_minimum,
                maximum_abs_Hu_per_mm=float(cell_Hu[right_Hu]), maximum_Hu_cell=right_Hu))
        states.append(dict(row=row, xy=positions, cell_J=cell_J, cell_Hu=cell_Hu, summary=summary))
        table.append(summary)
        accesses.append(dict(path=field_file.as_posix(), sha256=row["fields"]["sha256"], fields=["J", "Hu"]))
    q = np.array([row["body_q_mm"] for row in rows])
    force_scale = 4./max(max(abs(row["R_input_N"]), np.linalg.norm(row["force_on_body_N"]["total"])) for row in rows)
    high_by_q = {row["body_q_mm"]: row for row in high["states"]}
    low_by_q = {row["body_q_mm"]: row for row in table}
    if len(high_by_q) != len(high["states"]) or len(low_by_q) != len(table):
        raise ValueError("Exact-common-q table requires unique actual q in each condition")
    common_q = sorted(high_by_q.keys() & low_by_q.keys())
    if not 0. in common_q or not .025 in common_q:
        raise ValueError("Authorized q endpoints are not both actual common states")
    high_zero, low_zero = comparison_scalars(high_by_q[0.]), comparison_scalars(low_by_q[0.])
    paired = []
    for value in common_q:
        high_row, low_row = high_by_q[value], low_by_q[value]
        high_values, low_values = comparison_scalars(high_row), comparison_scalars(low_row)
        high_increment = {name: high_values[name]-high_zero[name] for name in ("Q_total_N", "Q_material_N", "Q_Hu_N")}
        low_increment = {name: low_values[name]-low_zero[name] for name in high_increment}
        paired.append(dict(body_q_mm=value, high_state=high_row, low_state=low_row,
            high_raw=high_values, low_raw=low_values,
            low_minus_high_raw={name: low_values[name]-high_values[name] for name in high_values},
            high_Q_increment_from_own_q0_N=high_increment, low_Q_increment_from_own_q0_N=low_increment,
            low_minus_high_Q_increment_N={name: low_increment[name]-high_increment[name] for name in high_increment}))

    def draw_geometry(axis, state, *, close=False, arrows=False):
        xy, summary = state["xy"], state["summary"]
        axis.add_collection(PolyCollection(xy[connectivity[solid_cells]], facecolor="#454f5b", edgecolor="none"))
        axis.add_collection(PolyCollection(xy[connectivity[body_cells]], facecolor="#bee3f8", edgecolor="none"))
        axis.add_collection(LineCollection(coordinates[solid_edges], colors="#b7c1cc", linewidths=.55, linestyles="dotted"))
        axis.add_collection(LineCollection(coordinates[body_edges], colors="#2364aa", linewidths=.7, linestyles="dashed"))
        axis.add_collection(LineCollection(xy[body_edges], colors="#2364aa", linewidths=1.))
        axis.add_collection(LineCollection(xy[right_edges], colors="#b44842", linewidths=1.))
        tip, nearest = xy[tip_node], np.asarray(summary["tip_nearest_body_point_mm"])
        axis.plot(*tip, "o", color="#b63559", ms=4, zorder=6)
        axis.plot([tip[0], nearest[0]], [tip[1], nearest[1]], color="#b63559", lw=1.2, zorder=5)
        if close:
            midpoint = (tip+nearest)/2
            axis.set_xlim(midpoint[0]-1.5, midpoint[0]+1.5)
            axis.set_ylim(midpoint[1]-1.25, midpoint[1]+1.25)
            axis.set_title(f"Actual x1 tip / q={summary['body_q_mm']:.6g} mm\ndistance={summary['tip_to_body_boundary_mm']:.8g} mm", fontsize=10)
        else:
            axis.set_xlim(-1., 93.)
            axis.set_ylim(-1., 41.)
            axis.set_title(f"Actual x1 / q={summary['body_q_mm']:.6g} mm; input mean={summary['input_mean_mm']:.12g} mm", fontsize=10)
        if arrows:
            center = xy[body_nodes].mean(axis=0)
            inlet = input_weights @ xy[input_nodes]
            for anchor, force, color in ((center, np.array(summary["force_on_body_N"]["total"]), "#135f9a"),
                                         (inlet, np.array([summary["R_input_N"], 0.]), "#a96512")):
                axis.annotate("", xy=anchor+force_scale*force, xytext=anchor,
                              arrowprops=dict(arrowstyle="->", color=color, lw=1.3))
        axis.set_aspect("equal", adjustable="box")
        axis.set_xlabel("x (mm)")
        axis.set_ylabel("y (mm)")
        axis.grid(alpha=.15)

    checkpoint("geometry_png")
    fig, axes = plt.subplots(2, 2, figsize=(15., 9.), constrained_layout=True)
    for col, state in enumerate((states[0], states[-1])):
        draw_geometry(axes[0, col], state, arrows=True)
        draw_geometry(axes[1, col], state, close=True)
    fig.suptitle("Low-input guided +x probe: actual x1 geometry; mean input held at 0.50 mm\n"
                 f"Dotted mechanism / dashed body = zero reference; q0 is new parent terminal geometry. Force arrows {force_scale:.5g} mm/N (not traction).", fontsize=12)
    axes[0, 0].legend(handles=[Line2D([], [], color="#454f5b", lw=5, label="mechanism"),
        Line2D([], [], color="#2364aa", lw=5, label="moving raster body"),
        Line2D([], [], color="#b44842", label="actual free right boundary"),
        Line2D([], [], marker="o", color="#b63559", label="tip / nearest body edge")], loc="lower right", fontsize=8)
    fig.savefig(output/"01_actual_geometry.png", dpi=160)
    plt.close(fig)

    checkpoint("force_convergence_png")
    fig, axes = plt.subplots(3, 3, figsize=(16., 12.), constrained_layout=True)
    colors = dict(total="#173e6c", material="#27845d", regularization="#ac5a20")
    for name, color in colors.items():
        axes[0, 0].plot(q, [-row["force_on_body_N"][name][0] for row in rows], "o-", color=color, label=name if name != "regularization" else "Hu")
        axes[0, 1].plot(q, [row["force_on_body_N"][name][1] for row in rows], "o-", color=color, label=name if name != "regularization" else "Hu")
    axes[0, 0].set_title("Signed half-model Q drive (N)")
    axes[0, 1].set_title("ON-body Fy, half model (N)")
    axes[0, 2].plot(q, [row["R_input_N"] for row in rows], "o-", color="#a96512")
    axes[0, 2].set_title("Separate input actuator R (N)")
    axes[1, 0].plot([row["d"] for row in parent["states"]], [row["R_input"] for row in parent["states"]], "o-", color="#a96512")
    axes[1, 0].set_title("Fresh zero-start parent: actuator R")
    axes[1, 0].set_xlabel("parent mean input (mm)")
    axes[1, 0].set_ylabel("R input (N)")
    axes[1, 1].plot(range(len(rows)), q, "o-", color="#173e6c", label="actual body q (mm)")
    axes[1, 1].set_ylabel("body q (mm)", color="#173e6c")
    twin = axes[1, 1].twinx()
    held = float(result["probe_task"]["held_input_mean_mm"])
    twin.plot(range(len(rows)), [row["input_mean_mm"]-held for row in rows], "s--", color="#a96512", label="input mean - held")
    bound = result["settings"]["constraint_tolerance"]*max(abs(held), result["settings"]["displacement_scale_floor"])
    twin.axhspan(-bound, bound, color="#a96512", alpha=.09)
    twin.set_ylabel("input mean - 0.50 (mm)", color="#a96512")
    axes[1, 1].set_title("Independent body q / held input")
    axes[1, 1].set_xlabel("actual accepted probe index")
    axes[1, 1].xaxis.set_major_locator(MaxNLocator(integer=True))
    history = result["newton_history"]
    parent_history = parent["path_diagnostics"]["newton_history"]
    split = len(parent_history)
    for records, start, color, label in ((parent_history, 1, "#a96512", "fixed parent"),
            (history, split+1, "#173e6c", "guided probe")):
        ordinal = np.arange(start, start+len(records))
        axes[1, 2].plot(ordinal, [row["relative_residual"] for row in records], ".-", color=color, label=label)
        axes[2, 0].plot(ordinal, [row["minimum_J"] for row in records], ".-", color=color, label=label)
    for axis in (axes[1, 2], axes[2, 0]):
        axis.axvline(split+.5, color="#777777", ls=":", lw=1.)
        axis.set_xlabel("all base checks in execution order")
        axis.legend(fontsize=8)
    axes[1, 2].set_yscale("symlog", linthresh=1e-16)
    axes[1, 2].axhline(result["settings"]["tolerance"], color="#ac3b37", ls="--", lw=1.)
    axes[1, 2].set_title("All parent / probe free residuals; gate 1e-9")
    axes[2, 0].set_yscale("log")
    axes[2, 0].set_title("All parent / probe base-check positive J")
    parent_trials = parent["path_diagnostics"]["trials"]
    all_trials = parent_trials+result["trials"]
    for index, record in enumerate(all_trials, 1):
        parent_phase = index <= len(parent_trials)
        accepted = record["accepted"]
        axes[2, 1].plot(index, record["factor"], marker="o" if accepted else "x",
            color=("#a96512" if parent_phase else "#173e6c") if accepted else "#b23043", ms=4.)
    axes[2, 1].axvline(len(parent_trials)+.5, color="#777777", ls=":", lw=1.)
    axes[2, 1].set_title("All line-search trials: circle accept / x reject")
    axes[2, 1].set_xlabel("parent trials then probe trials")
    axes[2, 1].set_ylabel("original backtrack factor")
    axes[2, 1].set_yscale("log")
    axes[2, 2].axis("off")
    axes[2, 2].text(.02, .98,
        f"Probe Q(q0) = {rows[0]['Q_drive_half_N']:.9g} N\n"
        f"Probe Delta Q(end) = {table[-1]['delta_Q_from_q0_N']:.9g} N\n"
        f"Material + Hu - total tail(end)\n  = {table[-1]['component_sum_minus_total_Q_N']:.3g} N (descriptive)\n\n"
        f"Parent: {len(parent['states'])} accepted, {len(parent_history)} checks,\n"
        f"  {len(parent_trials)} trials, {len(parent['path_diagnostics']['failed_attempts'])} failed attempts\n"
        f"Probe: {len(rows)} accepted, {len(history)} checks,\n"
        f"  {len(result['trials'])} trials, {len(result['failed_attempts'])} failed attempts\n\n"
        "Original internal backtracking / bisection retained.\n"
        "All attempts and solver diagnostics remain in JSON.\n"
        "Q0 preload is retained; Hu is not pressure.\n"
        "Half-model N already include 20 mm thickness.\n"
        "Only axial full-symmetry conversion is 2Q.",
        transform=axes[2, 2].transAxes, va="top", fontsize=9, linespacing=1.35)
    for axis in axes.flat:
        axis.grid(alpha=.2)
    for axis in axes[0]:
        axis.set_xlabel("body q (mm)")
    axes[0, 0].legend(fontsize=8)
    axes[0, 1].legend(fontsize=8)
    fig.suptitle("Low-input fixed-parent loading and held-input probe: signed forces and all convergence records\n"
        "Q = -ON-body Fx; original q0 preload retained; no pressure / friction / load-capacity qualification.", fontsize=12)
    fig.savefig(output/"02_force_and_convergence.png", dpi=160)
    plt.close(fig)

    checkpoint("right_medium_png")
    endpoints = (states[0], states[-1])
    jmin = min(float(state["cell_J"][right_cells].min()) for state in states)
    jmax = max(float(state["cell_J"][right_cells].max()) for state in states)
    hmax = max(float(state["cell_Hu"][right_cells].max()) for state in states)
    Jnorm = LogNorm(jmin, jmax) if jmax > jmin else Normalize(.5*jmin, 1.5*jmin)
    Hnorm = Normalize(0., hmax if hmax > 0 else 1.)
    fig = plt.figure(figsize=(16., 10.), constrained_layout=True)
    grid = fig.add_gridspec(2, 3, width_ratios=(.8, .8, 2.1))
    for row_index, state in enumerate(endpoints):
        xy, summary = state["xy"], state["summary"]
        for col, name, norm, label in ((0, "cell_J", Jnorm, "cell min J (log color)"),
                                       (1, "cell_Hu", Hnorm, "max |Hu component| (1/mm)")):
            axis = fig.add_subplot(grid[row_index, col])
            collection = PolyCollection(xy[connectivity[right_cells]], array=state[name][right_cells],
                cmap="viridis" if col == 0 else "magma", norm=norm, edgecolor="#626c77", linewidth=.18)
            axis.add_collection(collection)
            axis.add_collection(LineCollection(xy[right_edges], colors="#39a6ba", linewidth=1.))
            actual = xy[connectivity[right_cells]].reshape(-1, 2)
            axis.set_xlim(actual[:, 0].min()-.25, actual[:, 0].max()+.25)
            axis.set_ylim(actual[:, 1].min()-.25, actual[:, 1].max()+.25)
            axis.set_aspect("equal", adjustable="box")
            axis.set_title(f"q={summary['body_q_mm']:.6g}", fontsize=9)
            limits = axis.get_xlim()
            axis.set_xticks([limits[0]+.25, limits[1]-.25])
            axis.set_xticklabels([f"{value:.3f}" for value in (limits[0]+.25, limits[1]-.25)],
                rotation=65, ha="right", fontsize=8)
            axis.set_xlabel("actual x (mm)")
            axis.set_ylabel("actual y (mm)")
            fig.colorbar(collection, ax=axis, label=label, fraction=.045, pad=.025)
        axis = fig.add_subplot(grid[row_index, 2])
        draw_geometry(axis, state)
        minimum = summary["medium"]["minimum_J_actual_point_mm"]
        maximum = summary["medium"]["maximum_Hu_actual_cell_centroid_mm"]
        axis.plot(*minimum, "x", color="#e63340", ms=9, mew=1.5, label="global nonbody-medium min J sample")
        axis.plot(*maximum, "+", color="#b52db7", ms=10, mew=1.5, label="global max |Hu| cell centroid")
        a, b = summary["body_to_right_boundary"]["first_point_mm"], summary["body_to_right_boundary"]["second_point_mm"]
        axis.plot([a[0], b[0]], [a[1], b[1]], color="#39a6ba", lw=1.2)
        axis.set_title(f"Nonbody medium: min J={summary['medium']['minimum_J']:.7g} at cell {summary['medium']['minimum_J_cell']} / sample {summary['medium']['minimum_J_sample']}\n"
            f"max |Hu|={summary['medium']['maximum_abs_Hu_per_mm']:.7g} at cell {summary['medium']['maximum_Hu_cell']}; body/right boundary distance={summary['body_to_right_boundary']['distance_mm']:.7g} mm", fontsize=9)
        axis.legend(loc="lower right", fontsize=8)
    fig.suptitle("Actual right-side medium mesh and global extreme locations: x1, q0 vs final\n"
        "All 480 members stay reference columns 178..183; right boundary ux is free. J has no clipping; Hu is Q1 cell-constant; standard x/y and equal aspect.", fontsize=11)
    fig.savefig(output/"03_right_medium.png", dpi=160)
    plt.close(fig)

    checkpoint("same_q_comparison_png")
    paired_q = np.asarray(common_q)
    fig, axes = plt.subplots(3, 3, figsize=(17., 12.), constrained_layout=True)
    for condition, prefix, style in (("low", "low: held .50", "o-"), ("high", "high: held 1.06", "s--")):
        for key, name, color in (("Q_total_N", "total", colors["total"]),
                ("Q_material_N", "material", colors["material"]), ("Q_Hu_N", "Hu", colors["regularization"])):
            axes[0, 0].plot(paired_q, [row[condition+"_raw"][key] for row in paired], style,
                color=color, label=prefix+" / "+name, ms=4.)
            axes[0, 1].plot(paired_q, [row[condition+"_Q_increment_from_own_q0_N"][key] for row in paired], style,
                color=color, label=prefix+" / "+name, ms=4.)
            fy_key = "ON_body_Fy_"+name+"_N"
            axes[2, 1].plot(paired_q, [row[condition+"_raw"][fy_key] for row in paired], style,
                color=color, label=prefix+" / "+name, ms=4.)
        single_color = "#173e6c" if condition == "low" else "#a96512"
        for axis, key in ((axes[0, 2], "R_input_N"), (axes[1, 0], "tip_to_body_boundary_mm"),
                (axes[1, 1], "body_to_right_boundary_mm")):
            axis.plot(paired_q, [row[condition+"_raw"][key] for row in paired], style,
                color=single_color, label=prefix, ms=4.)
        for group, label, color in (("global", "global", "#50657c"),
                ("nonbody_medium", "nonbody medium", "#317848"), ("right480", "right 480", "#963958")):
            axes[1, 2].plot(paired_q, [row[condition+"_raw"][group+"_minimum_J"] for row in paired], style,
                color=color, label=prefix+" / "+label, ms=4.)
            axes[2, 0].plot(paired_q, [row[condition+"_raw"][group+"_maximum_abs_Hu_per_mm"] for row in paired], style,
                color=color, label=prefix+" / "+label, ms=4.)
    titles = ("Raw signed Q half (N); preload retained", "Each condition Q(q)-Q(0) (N)", "Separate input R (N)",
        "Tip / physical raster-body distance (mm)", "Body / actual free right-boundary distance (mm)",
        "Minimum J: original / nonbody / right 480", "Maximum |Hu component| (1/mm)", "Signed ON-body Fy half (N)")
    for axis, title in zip(list(axes.flat)[:8], titles):
        axis.set_title(title, fontsize=10)
        axis.set_xlabel("exact common actual q (mm)")
        axis.grid(alpha=.18)
        axis.legend(fontsize=7.3, loc="best")
    axes[1, 0].set_yscale("symlog", linthresh=1e-6)
    axes[1, 2].set_yscale("log")
    axes[2, 2].axis("off")
    final_pair = paired[-1]
    axes[2, 2].text(.01, .98,
        f"Exact common q = {common_q} mm\n"
        f"Low/high actual states = {len(table)} / {len(high['states'])}\n"
        "Unmatched states remain in JSON; no interpolation.\n\n"
        f"At q={final_pair['body_q_mm']:.6g} mm:\n"
        f"  low Q = {final_pair['low_raw']['Q_total_N']:.9g} N\n"
        f"  high Q = {final_pair['high_raw']['Q_total_N']:.9g} N\n"
        f"  low - high Q = {final_pair['low_minus_high_raw']['Q_total_N']:.9g} N\n"
        f"  low - high Delta Q = {final_pair['low_minus_high_Q_increment_N']['Q_total_N']:.9g} N\n\n"
        "Half-model N include 20 mm thickness.\n"
        "Q = -ON-body Fx; material / Hu signs retained.\n"
        "Different held inputs change the equilibrium.\n"
        "Neither raw difference nor increment difference\n"
        "is automatically pure contact or friction.\n"
        "No HP / capacity / release qualification.",
        transform=axes[2, 2].transAxes, va="top", fontsize=9, linespacing=1.35)
    fig.suptitle("Actual matched-q response under two held input conditions: low 0.50 mm vs high 1.06 mm\n"
        "Only exact shared accepted q; raw forces and each condition's own q0 increments are both preserved.", fontsize=12)
    fig.savefig(output/"04_same_q_comparison.png", dpi=160)
    plt.close(fig)

    frames = []
    for index, state in enumerate(states):
        checkpoint(f"actual_animation_frame_{index:03d}")
        fig, axes = plt.subplots(1, 2, figsize=(13., 4.5), constrained_layout=True)
        draw_geometry(axes[0], state, arrows=True)
        draw_geometry(axes[1], state, close=True)
        fig.suptitle(f"L-CTIPLOW1 actual accepted state {index+1}/{len(states)}; x1; held input 0.50 mm; no interpolated frames", fontsize=11)
        fig.canvas.draw()
        frames.append(Image.fromarray(np.asarray(fig.canvas.buffer_rgba()).copy()).convert("RGB"))
        plt.close(fig)
    frames[0].save(output/"animation.gif", save_all=True, append_images=frames[1:], duration=1100, loop=0, disposal=2, optimize=False)
    with Image.open(output/"animation.gif") as animation:
        actual_gif_frames = animation.n_frames
    if actual_gif_frames != len(states):
        raise ValueError("New GIF does not retain every actual accepted state")
    checkpoint("ordinary_tables_and_receipt")
    state_table = dict(schema_version="hf-ctiplow1-state-table-1", accepted_states=len(rows), states=table,
        newton_history=result["newton_history"], trials=result["trials"], failed_attempts=result["failed_attempts"],
        linear_solve_diagnostics=result["linear_solve_diagnostics"], call_counts=result["call_counts"],
        parent=dict(states=parent["states"], path_diagnostics=parent["path_diagnostics"],
            call_counts=parent["call_counts"], status=parent["status"], targets_mm=parent["targets_mm"],
            source_result=dict(path=parent_file.as_posix(), sha256=sha256(parent_bytes).hexdigest()),
            display_scope="Reference model coordinates and identity-matched new probe q0 show zero reference and genuine parent terminal only; no parent intermediate deformation arrays read"),
        source_result=dict(path=result_file.as_posix(), sha256=sha256(result_bytes).hexdigest()),
        observer_file=dict(path=observer_file.as_posix(), sha256=sha256(observer_bytes).hexdigest()),
        geometry_scope="Actual cached positions and unchanged reference topology; physical proximity excludes reference y=40 symmetry-cut edges; complete lower-half outlines retained in drawings. Binary64 display observations, not contact qualification",
        symmetry_cut_excluded_reference_y_mm=cut_y,
        boundary_topology_counts=dict(body_full_edges=len(body_edges), body_physical_edges=len(body_physical_edges),
            solid_full_edges=len(solid_edges), solid_physical_edges=len(solid_physical_edges)),
        J_location="Original nine Simpson samples: xi slow / eta fast, Q1 interpolation of actual cached positions",
        Hu_location="Q1 Hu is cell-constant; marker uses actual cell centroid, not an invented quadrature sample",
        scientific_calls=0, independent_HP_qualified=False, effective_grasp_qualified=False, release_qualified=False)
    write_json(output/"state_table.json", state_table)
    comparison = dict(schema_version="hf-ctiplow1-same-q-comparison-1", exact_common_q_mm=common_q,
        paired_states=paired, high_actual_states=high["states"], low_actual_states=table,
        high_unmatched_q_mm=sorted(high_by_q.keys()-low_by_q.keys()),
        low_unmatched_q_mm=sorted(low_by_q.keys()-high_by_q.keys()),
        high_histories={name: high[name] for name in
            ("newton_history", "trials", "failed_attempts", "linear_solve_diagnostics", "call_counts")},
        low_histories={name: result[name] for name in
            ("newton_history", "trials", "failed_attempts", "linear_solve_diagnostics", "call_counts")},
        high_source=dict(path=high_file.as_posix(), bytes=len(high_bytes), sha256=sha256(high_bytes).hexdigest()),
        low_source=dict(path=result_file.as_posix(), sha256=sha256(result_bytes).hexdigest()),
        held_input_mm=dict(high=1.06, low=.5), interpolation=False, scientific_calls=0,
        sign_scope="Q=-ON-body Fx; modeled half N already include 20 mm thickness; raw preload and own-q0 Q increments both retained",
        difference_scope="Low minus high control-condition response, not pure contact/friction/load capacity; no newly granted gates or qualification",
        independent_HP_qualified=False, effective_grasp_qualified=False, release_qualified=False)
    write_json(output/"comparison.json", comparison)
    lines = ["# L-CTIPLOW1 保存态显示与同q对照", "", "只显示本次新低输入探针实际接受态；全部结构图为实际×1，无插值帧。没有新增F/T、HP或平衡求解。", "",
        "机构输入从零短父加载0→0.25→0.50 mm；父任务完整成功后的真实末态迁移为探针q0，状态与有符号R身份一致。随后机构平均输入保持0.50 mm，仅推进工件q。图中参考轮廓来自新probe model坐标，父末态是身份一致的q0；未读取或伪造父中间变形。", "",
        "半模型N已含20 mm厚度；Q=−ON-body Fx，q0预载保留。R是机构输入反力。右界ux自由，不能画成夹紧墙。几何距离与physical-boundary节点观察排除参考y=40对称切边；绘图保留完整半模型轮廓。", "",
        "|态|q mm|input mean mm|Q half N|ΔQ N|R N|tip/body mm|body/right mm|min J|right min J|", "|---|---|---|---|---|---|---|---|---|---|"]
    for row in table:
        lines.append(f"|{row['accepted_index']}|{row['body_q_mm']:.9g}|{row['input_mean_mm']:.12g}|{row['Q_drive_half_N']:.10g}|{row['delta_Q_from_q0_N']:.10g}|{row['R_input_N']:.10g}|{row['tip_to_body_boundary_mm']:.10g}|{row['body_to_right_boundary']['distance_mm']:.10g}|{row['minimum_J']:.10g}|{row['right_medium']['minimum_J']:.10g}|")
    lines += ["", "## 高低输入精确共同q", "", "不插值、不删额外内部态、不用增量替代原始预载。差值方向统一为low−high。", "",
        "|q mm|low Q N|high Q N|low ΔQ N|high ΔQ N|ΔQ的low−high N|", "|---|---|---|---|---|---|"]
    for pair in paired:
        lines.append(f"|{pair['body_q_mm']:.9g}|{pair['low_raw']['Q_total_N']:.11g}|{pair['high_raw']['Q_total_N']:.11g}|{pair['low_Q_increment_from_own_q0_N']['Q_total_N']:.11g}|{pair['high_Q_increment_from_own_q0_N']['Q_total_N']:.11g}|{pair['low_minus_high_Q_increment_N']['Q_total_N']:.11g}|")
    lines += ["", f"高输入额外实际q：{comparison['high_unmatched_q_mm']} mm；低输入额外实际q：{comparison['low_unmatched_q_mm']} mm。完整原力／材料／Hu、各自增量、Fy／导向账本、位移、介质、全部历史与原态对象保留于[comparison.json](comparison.json)及[state_table.json](state_table.json)。", "",
        "输入不同会改变整体平衡。low−high原力差或增量差都不能直接称为纯接触力、摩擦力或抗拔承载；低输入也没有被预先认定为无接触。实际最近边界、严格内部节点和交叉只是保存坐标的几何观察，不授接触、压力、抗拔、释放或稳定性资格。Hu定位为cell-centroid；J定位为原九点样本。箭头只以明确mm/N尺度显示合力，放置点不是牵引分布。", "",
        "![实际结构](01_actual_geometry.png)", "", "![力与全部父／probe收敛](02_force_and_convergence.png)", "", "![右侧介质与全非body介质极值](03_right_medium.png)", "", "![高低输入同q对照](04_same_q_comparison.png)", "", "![本次实际接受态动画](animation.gif)", ""]
    (output/"REVIEW.md").write_text("\n".join(lines), encoding="utf-8")
    files = [dict(path=path.relative_to(output).as_posix(), bytes=path.stat().st_size, sha256=sha256(path.read_bytes()).hexdigest())
        for path in (output/"01_actual_geometry.png", output/"02_force_and_convergence.png", output/"03_right_medium.png",
            output/"04_same_q_comparison.png", output/"animation.gif", output/"state_table.json", output/"comparison.json", output/"REVIEW.md")]
    receipt = dict(status="rendered_pending_visual_check", accepted_states=len(rows), archives_decoded=len(accesses),
        fields_decoded=2*len(accesses), maximum_archives=17, maximum_fields=34,
        new_png_count=4, gif_frame_count=actual_gif_frames, new_gif_metadata_reads=1, scientific_calls=0,
        files=files, field_accesses=accesses, elapsed_seconds=monotonic()-STARTED,
        ordinary_reads=[dict(path=path.as_posix(), bytes=len(payload), sha256=sha256(payload).hexdigest())
            for path, payload in ((protocol_file, protocol_file.read_bytes()), (observer_file, observer_bytes),
                (parent_file, parent_bytes), (result_file, result_bytes), (high_file, high_bytes))],
        exact_common_q_mm=common_q, parent_accepted_states=len(parent["states"]),
        all_parent_checks=len(parent_history), all_probe_checks=len(history),
        media_scope="Only newly rendered low media; high input reads its single bound ordinary table, no old media or scientific arrays", independent_HP_qualified=False,
        effective_grasp_qualified=False, release_qualified=False)
    write_json(output/"renderer_receipt.json", receipt)
    checkpoint("complete")


if __name__ == "__main__":
    main()
