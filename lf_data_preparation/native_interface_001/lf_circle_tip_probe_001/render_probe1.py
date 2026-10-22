"""One pure display pass over the new guided-probe cache; no HF imports."""
from __future__ import annotations

import argparse
from hashlib import sha256
from io import BytesIO
import json
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", required=True)
    parser.add_argument("--result", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    protocol_file, result_file, output = Path(args.protocol).resolve(), Path(args.result).resolve(), Path(args.output).resolve()
    protocol = json.loads(protocol_file.read_bytes())
    observer_file = Path(protocol["observer_definition_path"])
    observer = json.loads(observer_file.read_bytes())
    result_bytes = result_file.read_bytes()
    result = json.loads(result_bytes)
    rows = result["accepted_steps"]
    if result["schema_version"] != "hf-native-guided-probe-1.0" or result["status"] != "success" or not 2 <= len(rows) <= 5:
        raise ValueError("Pure display requires this successful new probe result and 2..5 actual states")
    output.mkdir(parents=True, exist_ok=False)

    def checkpoint(phase):
        if monotonic()-STARTED >= protocol["viewer_seconds"]:
            raise TimeoutError("Pure viewer shared deadline reached")
        write_json(output/"renderer_checkpoint.json", dict(phase=phase, elapsed_seconds=monotonic()-STARTED,
            result_file=result_file.as_posix(), scientific_calls=0))

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
    fig.suptitle("Guided rigid +x probe: actual x1 geometry; mean input held at 1.06 mm\n"
                 f"Dotted mechanism / dashed body = reference; force arrows {force_scale:.5g} mm/N at drawing anchors (not traction).", fontsize=12)
    axes[0, 0].legend(handles=[Line2D([], [], color="#454f5b", lw=5, label="mechanism"),
        Line2D([], [], color="#2364aa", lw=5, label="moving raster body"),
        Line2D([], [], color="#b44842", label="actual free right boundary"),
        Line2D([], [], marker="o", color="#b63559", label="tip / nearest body edge")], loc="lower right", fontsize=8)
    fig.savefig(output/"01_actual_geometry.png", dpi=160)
    plt.close(fig)

    checkpoint("force_convergence_png")
    fig, axes = plt.subplots(2, 3, figsize=(16., 9.), constrained_layout=True)
    colors = dict(total="#173e6c", material="#27845d", regularization="#ac5a20")
    for name, color in colors.items():
        axes[0, 0].plot(q, [-row["force_on_body_N"][name][0] for row in rows], "o-", color=color, label=name if name != "regularization" else "Hu")
        axes[0, 1].plot(q, [row["force_on_body_N"][name][1] for row in rows], "o-", color=color, label=name if name != "regularization" else "Hu")
    axes[0, 0].set_title("Signed half-model Q drive (N)")
    axes[0, 0].text(.02, .98, f"Q(0)={rows[0]['Q_drive_half_N']:.8g} N\nDelta Q(end)={table[-1]['delta_Q_from_q0_N']:.8g} N\nComponent sum tail(end)={table[-1]['component_sum_minus_total_Q_N']:.3g} N (descriptive)", transform=axes[0, 0].transAxes, va="top", fontsize=9)
    axes[0, 1].set_title("ON-body Fy, half model (N)")
    axes[0, 2].plot(q, [row["R_input_N"] for row in rows], "o-", color="#a96512")
    axes[0, 2].set_title("Separate input actuator R (N)")
    axes[1, 0].plot(range(len(rows)), q, "o-", color="#173e6c", label="actual body q (mm)")
    twin = axes[1, 0].twinx()
    held = float(result["probe_task"]["held_input_mean_mm"])
    twin.plot(range(len(rows)), [row["input_mean_mm"]-held for row in rows], "s--", color="#a96512", label="input mean - held")
    bound = result["settings"]["constraint_tolerance"]*max(abs(held), result["settings"]["displacement_scale_floor"])
    twin.axhspan(-bound, bound, color="#a96512", alpha=.09)
    twin.set_ylabel("input mean - 1.06 (mm)", color="#a96512")
    axes[1, 0].set_title("Independent body q / held input")
    axes[1, 0].set_xlabel("actual accepted index")
    history = result["newton_history"]
    ordinal = np.arange(1, len(history)+1)
    axes[1, 1].plot(ordinal, [row["relative_residual"] for row in history], ".-", color="#173e6c")
    axes[1, 1].set_yscale("symlog", linthresh=1e-16)
    axes[1, 1].axhline(result["settings"]["tolerance"], color="#ac3b37", ls="--", label="original 1e-9 gate")
    axes[1, 1].set_title("All Newton base checks / free residual")
    axes[1, 1].set_xlabel("all checks in execution order")
    axes[1, 2].plot(ordinal, [row["minimum_J"] for row in history], ".-", color="#27845d", label="minimum J")
    axes[1, 2].set_yscale("log")
    axes[1, 2].set_title("All Newton base checks / positive J")
    axes[1, 2].set_xlabel("all checks in execution order")
    for axis in axes.flat:
        axis.grid(alpha=.2)
    for axis in axes[0]:
        axis.set_xlabel("body q (mm)")
    axes[0, 0].legend(fontsize=8)
    axes[0, 1].legend(fontsize=8)
    axes[1, 1].legend(fontsize=8)
    fig.suptitle("Preserved signs and q0 preload; no pressure / friction / load-capacity qualification\n"
        f"Half-model N already include 20 mm thickness; full symmetric axial conversion = 2Q only. Accepted={len(rows)}, checks={len(history)}, trials={len(result['trials'])}.", fontsize=12)
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
            axis.set_title(f"q={summary['body_q_mm']:.6g}\n480 fixed reference cells", fontsize=9)
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
        "Right members stay reference columns 178..183; right boundary has free ux. J is retained without clipping; Hu is Q1 cell-constant.", fontsize=12)
    fig.savefig(output/"03_right_medium.png", dpi=160)
    plt.close(fig)

    frames = []
    for index, state in enumerate(states):
        checkpoint(f"actual_animation_frame_{index:03d}")
        fig, axes = plt.subplots(1, 2, figsize=(13., 4.5), constrained_layout=True)
        draw_geometry(axes[0], state, arrows=True)
        draw_geometry(axes[1], state, close=True)
        fig.suptitle(f"L-CTIPPROBE1 actual accepted state {index+1}/{len(states)}; x1; held input 1.06 mm; no interpolated frames", fontsize=11)
        fig.canvas.draw()
        frames.append(Image.fromarray(np.asarray(fig.canvas.buffer_rgba()).copy()).convert("RGB"))
        plt.close(fig)
    frames[0].save(output/"animation.gif", save_all=True, append_images=frames[1:], duration=1100, loop=0, disposal=2, optimize=False)
    with Image.open(output/"animation.gif") as animation:
        actual_gif_frames = animation.n_frames
    if actual_gif_frames != len(states):
        raise ValueError("New GIF does not retain every actual accepted state")
    checkpoint("ordinary_tables_and_receipt")
    state_table = dict(schema_version="hf-ctipprobe1-state-table-1", accepted_states=len(rows), states=table,
        newton_history=result["newton_history"], trials=result["trials"], failed_attempts=result["failed_attempts"],
        linear_solve_diagnostics=result["linear_solve_diagnostics"], call_counts=result["call_counts"],
        source_result=dict(path=result_file.as_posix(), sha256=sha256(result_bytes).hexdigest()),
        observer_file=dict(path=observer_file.as_posix(), sha256=sha256(observer_file.read_bytes()).hexdigest()),
        geometry_scope="Actual cached positions and unchanged reference topology; physical proximity excludes reference y=40 symmetry-cut edges; complete lower-half outlines retained in drawings. Binary64 display observations, not contact qualification",
        symmetry_cut_excluded_reference_y_mm=cut_y,
        boundary_topology_counts=dict(body_full_edges=len(body_edges), body_physical_edges=len(body_physical_edges),
            solid_full_edges=len(solid_edges), solid_physical_edges=len(solid_physical_edges)),
        J_location="Original nine Simpson samples: xi slow / eta fast, Q1 interpolation of actual cached positions",
        Hu_location="Q1 Hu is cell-constant; marker uses actual cell centroid, not an invented quadrature sample",
        scientific_calls=0, independent_HP_qualified=False, effective_grasp_qualified=False, release_qualified=False)
    write_json(output/"state_table.json", state_table)
    lines = ["# L-CTIPPROBE1 保存态显示", "", "仅显示本次新接受态；全部结构图为实际×1，无插值帧。没有新增F/T、HP或平衡求解。", "",
        "半模型N已含20 mm厚度；Q=−ON-body Fx，q0预载保留。R是机构输入反力。右界ux自由，不能画成夹紧墙。几何距离与physical-boundary节点观察排除参考y=40对称切边；绘图保留完整半模型轮廓。", "",
        "|态|q mm|input mean mm|Q half N|ΔQ N|R N|tip/body mm|body/right mm|min J|right min J|", "|---|---|---|---|---|---|---|---|---|---|"]
    for row in table:
        lines.append(f"|{row['accepted_index']}|{row['body_q_mm']:.9g}|{row['input_mean_mm']:.12g}|{row['Q_drive_half_N']:.10g}|{row['delta_Q_from_q0_N']:.10g}|{row['R_input_N']:.10g}|{row['tip_to_body_boundary_mm']:.10g}|{row['body_to_right_boundary']['distance_mm']:.10g}|{row['minimum_J']:.10g}|{row['right_medium']['minimum_J']:.10g}|")
    lines += ["", "实际最近边界、严格内部节点和交叉只是保存坐标的几何观察，不授接触、压力、抗拔、释放或稳定性资格。Hu定位为cell-centroid；J定位为原九点样本。箭头只以明确mm/N尺度显示合力，放置点不是牵引分布。", "",
        "![实际结构](01_actual_geometry.png)", "", "![力与收敛](02_force_and_convergence.png)", "", "![右侧介质](03_right_medium.png)", "", "![本次实际接受态动画](animation.gif)", ""]
    (output/"REVIEW.md").write_text("\n".join(lines), encoding="utf-8")
    files = [dict(path=path.relative_to(output).as_posix(), bytes=path.stat().st_size, sha256=sha256(path.read_bytes()).hexdigest())
        for path in (output/"01_actual_geometry.png", output/"02_force_and_convergence.png", output/"03_right_medium.png", output/"animation.gif", output/"state_table.json", output/"REVIEW.md")]
    receipt = dict(status="rendered_pending_visual_check", accepted_states=len(rows), archives_decoded=len(accesses),
        fields_decoded=2*len(accesses), new_png_count=3, gif_frame_count=actual_gif_frames, new_gif_metadata_reads=1, scientific_calls=0,
        files=files, field_accesses=accesses, elapsed_seconds=monotonic()-STARTED,
        media_scope="Only newly rendered media; no old media content read", independent_HP_qualified=False,
        effective_grasp_qualified=False, release_qualified=False)
    write_json(output/"renderer_receipt.json", receipt)
    checkpoint("complete")


if __name__ == "__main__":
    main()
