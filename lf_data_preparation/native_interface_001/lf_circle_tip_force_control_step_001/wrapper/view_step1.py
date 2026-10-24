"""One FSTEP1 display from four ordinary JSON files; no HF or NPZ input."""
import time
START = time.monotonic()

from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from textwrap import fill

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import PillowWriter
from matplotlib.collections import PolyCollection
from matplotlib.patches import Patch
import numpy as np


BASE = Path(__file__).resolve().parent
RUN = BASE/"run_001"
VIEW = RUN/"view"
MAX_SECONDS = 510.
PNG_NAMES = ("01_actual_geometry.png", "02_P_q_continuation.png",
             "03_force_components_and_R.png", "04_tip_right_geometry_global_J_Hu.png",
             "05_convergence_and_gates.png")
COLORS = dict(solid="#527b92", medium="#e1e8eb", body="#e4af59",
              reference="#8b969e", force="#b84632", blue="#32769b", hu="#79588d")


def clock():
    if time.monotonic()-START >= MAX_SECONDS:
        raise TimeoutError("Original viewer generation limit reached; no repair or rerender")


def read_json(path):
    raw = path.read_bytes()
    return json.loads(raw), dict(path=str(path), bytes=len(raw), sha256=sha256(raw).hexdigest())


def identity(path):
    raw = path.read_bytes()
    return dict(path=str(path), bytes=len(raw), sha256=sha256(raw).hexdigest())


def write_json(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def polygons(ax, positions, cells, colors, *, reference=False, linewidth=.22):
    collection = PolyCollection(positions[cells],
        facecolors="none" if reference else colors,
        edgecolors=COLORS["reference"] if reference else "#617883",
        linewidths=linewidth, linestyles="dotted" if reference else "solid",
        rasterized=True)
    ax.add_collection(collection)
    return collection


def setup_geometry(ax, limits, title):
    ax.set(xlim=limits[0], ylim=limits[1], xlabel="x (mm)", ylabel="y (mm)", title=title)
    ax.set_aspect("equal", adjustable="box")
    ax.grid(alpha=.15)


def save_figure(fig, name):
    clock()
    fig.savefig(VIEW/name, dpi=130)
    plt.close(fig)
    clock()


def boundary_edges(cells):
    """Original raster-body boundary; the symmetry cut is filtered below."""
    counts = Counter(tuple(sorted((int(a), int(b))))
        for cell in cells for a, b in zip(cell, np.roll(cell, -1)))
    return np.asarray([edge for edge, count in counts.items() if count == 1], dtype=int)


def closest_tip_segment(positions, tip_node, edges):
    point = positions[tip_node]
    a, b = positions[edges[:, 0]], positions[edges[:, 1]]
    direction = b-a
    squared = np.einsum("ij,ij->i", direction, direction)
    if np.any(squared <= 0):
        raise ValueError("Saved body boundary contains a zero-length segment")
    fraction = np.clip(np.einsum("ij,ij->i", point-a, direction)/squared, 0., 1.)
    closest = a+fraction[:, None]*direction
    distances = np.linalg.norm(closest-point, axis=1)
    index = int(np.argmin(distances))
    return dict(unsigned_tip_boundary_distance_mm=float(distances[index]),
        tip_node=int(tip_node), tip_position_mm=point.tolist(),
        closest_reference_edge=edges[index].tolist(), closest_position_mm=closest[index].tolist())


def positive_for_log(values, floor):
    """Only exact zero gets a display floor; saved input values never change."""
    values = np.asarray(values, dtype=float)
    if np.any(values < 0):
        raise ValueError("Residual/error magnitude is negative")
    return np.where(values == 0, floor, values)


def main():
    clock()
    protocol, protocol_id = read_json(BASE/"protocol.json")
    observer, observer_id = read_json(BASE/"observer_binding.json")
    result, result_id = read_json(RUN/"force/result.json")
    check, check_id = read_json(RUN/"continuation_check.json")
    if result["status"] != "success" or check["status"] != "pass":
        raise ValueError("Display requires numerical success and ordinary continuation check pass")
    rows = result["accepted_steps"]
    if not 2 <= len(rows) <= 5:
        raise ValueError("Expected saved nonzero anchor and actual states within inherited Nmin bound")
    if result["force_task"]["body_load_targets_half_N"] != protocol["loads_half_N"]:
        raise ValueError("Force targets differ from the frozen full three-load prefix")
    if result["force_task"]["held_input_mean_mm"] != observer["held_input_mean_mm"] or observer["held_input_mean_mm"] != 1.06:
        raise ValueError("Observer is not bound to the held 1.06 mm task")
    coords = np.asarray(result["model"]["coordinates_mm"], dtype=float)
    cells = np.asarray(result["model"]["connectivity"], dtype=int)
    solid = np.asarray(result["model"]["solid"], dtype=bool)
    body_nodes = np.asarray(observer["body_nodes"], dtype=int)
    body_cells = np.asarray(observer["body_cells"], dtype=int)
    right_cells = np.asarray(observer["right_medium_cells"], dtype=int)
    right_nodes = np.asarray(observer["right_boundary_nodes"], dtype=int)
    tip = int(observer["tip_node"])
    if (coords.shape != (14985, 2) or cells.shape != (14720, 4)
            or solid.shape != (14720,) or len(body_nodes) != 565 or len(body_cells) != 510
            or len(right_cells) != 480 or len(right_nodes) != 81
            or result["model"]["body_nodes"] != observer["body_nodes"]
            or result["model"]["region_metadata"]["workpiece"]["cells"] != observer["body_cells"]
            or np.any(solid[right_cells]) or np.intersect1d(right_cells, body_cells).size):
        raise ValueError("Original observer membership or right-medium phase differs")
    positions = [np.asarray(row["positions_mm"], dtype=float) for row in rows]
    if any(array.shape != coords.shape or not np.isfinite(array).all() for array in positions):
        raise ValueError("Accepted positions must be finite cached whole-model coordinates")
    body_flag = np.zeros(len(cells), dtype=bool); body_flag[body_cells] = True
    facecolors = np.where(body_flag, COLORS["body"],
        np.where(solid, COLORS["solid"], COLORS["medium"])).tolist()
    edges = boundary_edges(cells[body_cells])
    symmetry_cut = ((coords[edges[:, 0], 1] == 40.)
                    & (coords[edges[:, 1], 1] == 40.))
    edges = edges[~symmetry_cut]
    if not len(edges):
        raise ValueError("Original physical body boundary must exclude only the y40 symmetry cut")
    metrics = [closest_tip_segment(pos, tip, edges) | dict(accepted_index=i,
        P_target_half_N=rows[i]["P_target_half_N"], body_q_mm=rows[i]["body_q_mm"])
        for i, pos in enumerate(positions)]
    old_history = protocol["history"]["old_given_q_reference"]
    reference_history = old_history["reference_history_steps"]
    reference_failures = old_history["reference_failed_attempts"]
    reference_calls = old_history["reference_call_counts"]
    parent_context = protocol["history"]["immediate_force_parent"]["scalar_rows"]
    segment = protocol["segment_loads_half_N"]
    continuation = result["continuation"]
    if (result["schema_version"] != "hf-native-guided-force-1.1"
            or continuation["requested_segment_targets_half_N"] != segment
            or continuation["global_original_target_offset"] != 1
            or [r["original_target_index"] for r in rows if r["is_original_target"]] != [1, 2]
            or [r["P_target_half_N"] for r in parent_context] != protocol["loads_half_N"][:2]
            or [r["body_q_mm"] for r in reference_history] != [0., .0125, .025]):
        raise ValueError("Saved-segment global indices, parent context or old history differs")
    historical_middle = [row for row in reference_history if not row["is_original_target"]]
    P = np.asarray([row["P_target_half_N"] for row in rows])
    Q = np.asarray([row["generalized_body_internal_force_half_N"] for row in rows])
    q = np.asarray([row["body_q_mm"] for row in rows])
    final, final_positions = rows[-1], positions[-1]
    limits = ((float(min(coords[:, 0].min(), *(p[:, 0].min() for p in positions)))-1.,
               float(max(coords[:, 0].max(), *(p[:, 0].max() for p in positions)))+1.),
              (float(min(coords[:, 1].min(), *(p[:, 1].min() for p in positions)))-1.,
               float(max(coords[:, 1].max(), *(p[:, 1].max() for p in positions)))+1.))
    VIEW.mkdir(exist_ok=False)
    plt.rcParams.update({"font.size": 10, "axes.titlesize": 12, "axes.labelsize": 10,
        "figure.facecolor": "white", "axes.grid": True, "grid.alpha": .18})
    phase_legend = [Patch(facecolor=COLORS[name], label=label) for name, label in
        (("solid", "Mechanism solid"), ("body", "Guided rigid body"), ("medium", "Third medium"))]

    fig, axes = plt.subplots(1, 2, figsize=(19, 9), layout="constrained",
        gridspec_kw={"width_ratios": [1.65, 1.]})
    polygons(axes[0], final_positions, cells, facecolors)
    polygons(axes[0], coords, cells, facecolors, reference=True, linewidth=.18)
    setup_geometry(axes[0], limits, "Whole model: actual geometry x1 / dotted undeformed grid")
    axes[0].legend(handles=phase_legend, loc="lower left", fontsize=9)
    axes[0].text(.02, .98, f'Held input mean = {final["input_mean_mm"]:.12g} mm\n'
        f'Applied P_half = {final["P_target_half_N"]:.12g} N\n'
        f'Independently solved q = {final["body_q_mm"]:.12g} mm\n'
        f'Input actuator R = {final["R_input_N"]:.12g} N',
        transform=axes[0].transAxes, va="top", fontsize=10,
        bbox=dict(facecolor="white", alpha=.9, edgecolor="none"))
    near = np.flatnonzero(np.any(np.isin(cells, body_nodes), axis=1)
        | np.any(np.linalg.norm(coords[cells]-coords[tip], axis=2) < 5., axis=1))
    polygons(axes[1], final_positions, cells[near], [facecolors[i] for i in near], linewidth=.45)
    polygons(axes[1], coords, cells[near], [facecolors[i] for i in near], reference=True, linewidth=.3)
    axes[1].plot(positions[0][body_nodes, 0], positions[0][body_nodes, 1], ".", ms=1.8,
        color=COLORS["reference"], label="Fresh force anchor body nodes")
    setup_geometry(axes[1], ((70., 91.), (27., 41.)), "Body / tip vicinity: actual geometry x1")
    axes[1].legend(loc="lower left", fontsize=8)
    fig.suptitle("L-CTIPFSTEP1 | Saved nonzero-q axial force continuation\n"
        "r9 / center(80,40) / right92 / Lr80; alpha=2.5e-7. No displacement magnification.", fontsize=15)
    save_figure(fig, PNG_NAMES[0])

    fig, axes = plt.subplots(1, 2, figsize=(19, 8), layout="constrained")
    axes[0].plot([r["body_q_mm"] for r in parent_context],
        [r["P_target_half_N"]*1e6 for r in parent_context], "s--", mfc="none",
        color=COLORS["reference"], label="Completed HIGH1 P0/P1: scalar context only")
    axes[0].plot([r["body_q_mm"] for r in historical_middle],
        [r["P_target_half_N"]*1e6 for r in historical_middle], "^", mfc="none",
        color=COLORS["reference"], ms=8, label="Old probe q=.0125: HISTORY ONLY, unpaired")
    axes[0].plot(q, P*1e6, "o-", color=COLORS["force"], label="New segment: actual saved-anchor / solved states")
    axes[0].annotate("Fresh P1 anchor (not q=0)", (q[0], P[0]*1e6),
        xytext=(12, -26), textcoords="offset points", fontsize=9,
        arrowprops=dict(arrowstyle="->", color=COLORS["force"]))
    axes[0].set(xlabel="Absolute body q (mm)", ylabel="Signed half-model axial load (microN)",
        title="Only [P1,P2] computed now; full prefix [P0,P1,P2] retained")
    axes[0].legend(loc="upper left", fontsize=9)
    axes[1].plot(P*1e6, [r["generalized_force_scale_half_N"]*1e6 for r in rows],
        "o-", color=COLORS["force"], label="Actual SP from original formula")
    axes[1].axhline(protocol["loads_half_N"][0]*1e6, color=COLORS["blue"], ls="--",
        label="Original root P0 retained (not reset)")
    axes[1].axhline(segment[0]*1e6, color=COLORS["hu"], ls=":",
        label="Segment P1; distinct from original root P0")
    axes[1].set(xlabel="Absolute P_half (microN)", ylabel="Force magnitude / scale (microN)",
        title="SP = max(abs(P), abs(root P0), Ffloor)")
    axes[1].legend(loc="upper left", fontsize=9)
    axes[1].text(.04, .08, "New P2: NO given-q or HP reference.\n"
        "No reference-error bars or invented zero errors.\n"
        "This positive increasing segment has SP=P;\n"
        "its numeric scales alone cannot distinguish root rebasing.",
        transform=axes[1].transAxes, va="bottom", fontsize=10,
        bbox=dict(facecolor="white", alpha=.95, edgecolor="#d7dfe4"))
    fig.suptitle("Force continuation from nonzero q1/P1/R1 | q2 independently solved, never prescribed\n"
        "Source P0/P1 context is not a new path or reference; half N includes thickness, full axial load 2P, q unchanged.", fontsize=14)
    save_figure(fig, PNG_NAMES[1])

    fig, axes = plt.subplots(2, 2, figsize=(18, 11), layout="constrained")
    ax = axes[0, 0]
    for name, label, marker, color in (("total", "Internal total Q", "o", COLORS["force"]),
        ("material", "Material part", "s", COLORS["blue"]),
        ("regularization", "Hu part", "^", COLORS["hu"])):
        values = Q if name == "total" else np.asarray([-r["force_on_body_N"][name][0] for r in rows])
        ax.plot(P*1e6, values*1e6, marker+"-", label=label, color=color)
    ax.plot(P*1e6, P*1e6, ":", color="#555555", label="Applied P")
    ax.set(xlabel="Absolute signed P_half (microN)", ylabel="Internal generalized axial force (microN)",
        title="Nonzero preload; total contains material and Hu")
    ax.legend(fontsize=9)
    ax = axes[0, 1]
    ax.plot(P*1e6, [r["R_input_N"] for r in rows], "o-", color=COLORS["hu"], label="Input actuator R")
    ax.plot([r["P_target_half_N"]*1e6 for r in parent_context], [r["R_input_N"] for r in parent_context],
        "s", mfc="none", color=COLORS["reference"], label="Completed HIGH1 R: scalar context only")
    ax.plot([r["P_target_half_N"]*1e6 for r in historical_middle],
        [r["R_input_N"] for r in historical_middle], "^", mfc="none",
        color=COLORS["reference"], label="Old internal midpoint: HISTORY ONLY")
    ax.set(xlabel="Absolute signed P_half (microN)", ylabel="Input R (N)",
        title="Separate input reaction; mean remains 1.06 mm")
    ax.ticklabel_format(axis="y", style="plain", useOffset=False)
    ax.legend(fontsize=9)
    ax = axes[1, 0]
    index = np.arange(3)
    vectors = np.asarray([final["force_on_body_N"][name] for name in ("total", "material", "regularization")])
    ax.bar(index-.18, vectors[:, 0]*1e6, .36, label="ON-body Fx", color=COLORS["force"])
    ax.bar(index+.18, vectors[:, 1]*1e6, .36, label="ON-body Fy", color=COLORS["blue"])
    ax.axhline(0., color="#777777", lw=.7)
    ax.set(xticks=index, xticklabels=["Total", "Material", "Hu"], ylabel="Signed ON-body weak force (microN)",
        title="Final lower-half components; Fx is opposite external P")
    ax.legend(fontsize=9)
    ax = axes[1, 1]; ax.axis("off")
    ledger = final["ledger"]
    table_rows = [(label, ledger[key]) for label, key in
        (("Input actuator", "input_actuator_N"), ("Explicit axial P", "body_axial_load_N"),
         ("Body-y guide", "body_y_guide_N"), ("Other zero supports", "zero_support_N"),
         ("External balance", "global_force_balance_N"))]
    table = ax.table(cellText=[[label, f'{vector[0]:.9g}', f'{vector[1]:.9g}'] for label, vector in table_rows],
        colLabels=["Disjoint external ledger", "x (N)", "y (N)"], loc="center", cellLoc="center",
        colWidths=[.42, .29, .29])
    table.auto_set_font_size(False); table.set_fontsize(10); table.scale(1., 1.75)
    ax.set_title("No old body-x prescribed drive is added again")
    ax.text(.5, .07, "Half-model N already includes 20 mm thickness.\n"
        "Nodal weak forces / Hu contributions are not contact pressure or capacity.",
        ha="center", transform=ax.transAxes, fontsize=10)
    fig.suptitle("Actual force components, input reaction and external ledger", fontsize=15)
    save_figure(fig, PNG_NAMES[2])

    fig = plt.figure(figsize=(19, 11), layout="constrained")
    grid = fig.add_gridspec(2, 3, width_ratios=[1.25, .65, 1.25])
    ax_tip, ax_right = fig.add_subplot(grid[:, 0]), fig.add_subplot(grid[:, 1])
    polygons(ax_tip, final_positions, cells[near], [facecolors[i] for i in near], linewidth=.5)
    polygons(ax_tip, coords, cells[near], [facecolors[i] for i in near], reference=True, linewidth=.3)
    witness = metrics[-1]
    point, closest = witness["tip_position_mm"], witness["closest_position_mm"]
    ax_tip.plot([point[0], closest[0]], [point[1], closest[1]], "o--", ms=5,
        color=COLORS["force"], label=f'Unsigned node-to-segment distance\n{witness["unsigned_tip_boundary_distance_mm"]:.9g} mm')
    setup_geometry(ax_tip, ((70., 91.), (27., 41.)), "Actual x1 tip / original raster-body boundary")
    ax_tip.legend(loc="lower left", fontsize=9)
    midpoint = (np.asarray(point)+np.asarray(closest))/2.
    zoom = ax_tip.inset_axes([.08, .59, .84, .31])
    polygons(zoom, final_positions, cells[near], [facecolors[i] for i in near], linewidth=.7)
    zoom.plot([point[0], closest[0]], [point[1], closest[1]], "o--", ms=4,
        color=COLORS["force"])
    zoom.set(xlim=(midpoint[0]-.08, midpoint[0]+.08),
        ylim=(midpoint[1]-.08, midpoint[1]+.08), xlabel="x (mm)", ylabel="y (mm)",
        title="Coordinate zoom around closest tip pair\nActual geometry x1; no displacement magnification")
    zoom.set_aspect("equal", adjustable="box")
    zoom.ticklabel_format(axis="both", style="plain", useOffset=False)
    zoom.tick_params(labelsize=8)
    zoom.xaxis.label.set_size(8); zoom.yaxis.label.set_size(8)
    zoom.title.set_size(9)
    ax_tip.indicate_inset_zoom(zoom, edgecolor=COLORS["force"], alpha=.55)
    polygons(ax_right, final_positions, cells[right_cells], [COLORS["medium"]]*len(right_cells), linewidth=.3)
    polygons(ax_right, final_positions, cells[body_cells], [COLORS["body"]]*len(body_cells), linewidth=.3)
    ax_right.plot(coords[right_nodes, 0], coords[right_nodes, 1], ":", color=COLORS["reference"], lw=1.)
    ax_right.plot(final_positions[right_nodes, 0], final_positions[right_nodes, 1], "-", color=COLORS["blue"], lw=1.)
    setup_geometry(ax_right, ((88., 94.), (-.5, 40.5)), "Right medium\n480 fixed cells\nActual geometry x1")
    ax_right.set_xticks([89., 92.]); ax_right.tick_params(axis="x", labelrotation=45)
    ax_right.text(.5, -.12, "Blue: actual free right edge\nDotted: original x=92\nGeometric strip only",
        transform=ax_right.transAxes, ha="center", va="top", fontsize=8)
    ax = fig.add_subplot(grid[0, 2])
    ax.plot(P*1e6, [r["minimum_J"] for r in rows], "o-", color=COLORS["blue"], label="Whole-model min J")
    ax.set(xlabel="Absolute P_half (microN)", ylabel="Saved minimum J", title="Whole-model saved scalars; no local field map")
    twin = ax.twinx()
    twin.plot(P*1e6, [r["max_abs_Hu_per_mm"] for r in rows], "^--", color=COLORS["hu"])
    twin.set_ylabel("Saved global maximum |Hu| (1/mm)", color=COLORS["hu"]); twin.grid(False)
    ax.legend(loc="upper left", fontsize=9)
    ax = fig.add_subplot(grid[1, 2])
    ax.plot(P*1e6, [m["unsigned_tip_boundary_distance_mm"] for m in metrics], "o-", color=COLORS["force"])
    ax.set(xlabel="Absolute P_half (microN)", ylabel="Unsigned tip-to-boundary distance (mm)",
        title="Tip node 11260; nearest original boundary segment")
    fig.suptitle("Actual geometry and cached global medium response\n"
        "Fixed reference membership; no remask, local J/Hu arrays, pressure or contact threshold.", fontsize=14)
    save_figure(fig, PNG_NAMES[3])

    fig, axes = plt.subplots(2, 3, figsize=(22, 12), layout="constrained")
    history = result["newton_history"]
    checks = np.arange(1, len(history)+1)
    ax = axes[0, 0]
    for key, label, style in (("relative_residual", "Free-force rho_F", "o-"),
        ("relative_generalized_force_residual", "Body-load rho_P", "s--")):
        ax.semilogy(checks, positive_for_log([r[key] for r in history], 1e-18), style, label=label, ms=4)
    ax.axhline(1e-9, color=COLORS["force"], ls=":", label="Each residual bound")
    ax.set(xlabel="Actual sequential Newton base check", ylabel="Separate relative residuals",
        title="All actual base checks; exact zeros displayed at 1e-18")
    ax.legend(fontsize=9)
    ax = axes[0, 1]
    ax.semilogy(checks, positive_for_log([abs(r["constraint_residual"]) for r in history], 1e-22), "o-", label="Compensated mean error")
    ax.semilogy(checks, [r["constraint_bound"] for r in history], "--", color=COLORS["force"], label="Original mean bound")
    ax.set(xlabel="Actual sequential Newton base check", ylabel="Absolute mean residual (mm)",
        title="Two split components measured before rounding; zero at 1e-22 mm")
    ax.legend(fontsize=9)
    trials = result["trials"]
    ax = axes[0, 2]
    trial_indices = np.arange(1, len(trials)+1)
    merit_indices, merit_ratios, invalid_indices = [], [], []
    for i, trial in enumerate(trials, 1):
        if "phi" in trial and trial["base_phi"] > 0.:
            merit_indices.append(i)
            merit_ratios.append(trial["phi"]/trial["base_phi"])
        else:
            invalid_indices.append(i)
    if len(trials):
        ax.semilogy(merit_indices, positive_for_log(merit_ratios, 1e-22),
            "o", ms=3.5, color=COLORS["blue"], label="Actual trial phi / fixed base phi")
        ax.plot(trial_indices, [1-2*result["settings"]["armijo_c"]*r["factor"] for r in trials],
            ":", color=COLORS["force"], label="Original Armijo bound")
        if invalid_indices:
            ax.plot(invalid_indices, [.03]*len(invalid_indices), "x", color=COLORS["hu"],
                transform=ax.get_xaxis_transform(), label="No valid merit: x at plot bottom")
        rejected = [i for i, r in enumerate(trials, 1) if not r["accepted"] and "phi" in r and r["base_phi"] > 0.]
        if rejected:
            ax.plot(rejected, [trials[i-1]["phi"]/trials[i-1]["base_phi"] for i in rejected],
                "rx", ms=6, label="Rejected finite-merit trial")
        ax.legend(fontsize=8)
    else:
        ax.text(.5, .5, "No line-search trial was needed", ha="center", va="center", transform=ax.transAxes)
    ax.set(xlabel="Actual sequential line-search trial", ylabel="Trial merit / its fixed-base merit",
        title="All actual trials; zero ratios displayed at 1e-22")
    accepted = np.arange(len(rows))
    ax = axes[1, 0]
    ax.semilogy(accepted, positive_for_log([r["relative_global_force_balance"] for r in rows], 1e-20), "o-", label="Disjoint global balance")
    ax.axhline(1e-6, color=COLORS["force"], ls="--", label="Original global bound")
    ax.set(xlabel="Actual accepted-state index", ylabel="Relative external balance",
        title="Accepted states including all internal subdivisions; zero at 1e-20")
    ax.legend(fontsize=9)
    ax = axes[1, 1]
    ax.bar(accepted, [r["newton_checks"] for r in rows], color=COLORS["medium"], edgecolor=COLORS["blue"], label="Base checks per accepted state")
    ax.set(xlabel="Actual accepted-state index", ylabel="Newton base checks",
        title="Rigid/zero error is separate from iteration count")
    twin = ax.twinx()
    twin.semilogy(accepted, positive_for_log([r["max_abs_prescribed_error_mm"] for r in rows], 1e-22),
        "o", color=COLORS["hu"], label="Rigid/zero error")
    twin.axhline(8e-11, color=COLORS["force"], ls="--")
    twin.set_ylabel("Rigid/zero absolute error (mm); zero at 1e-22"); twin.grid(False)
    ax.legend(loc="upper left", fontsize=8); twin.legend(loc="upper right", fontsize=8)
    ax = axes[1, 2]
    ax.axis("off")
    failures_by_code = dict(Counter(row["code"] for row in result["failed_attempts"]))
    old_failures_by_code = dict(Counter(row["code"] for row in reference_failures))
    calls = result["call_counts"]
    summary = (f'NEW FORCE SEGMENT: {len(rows)} actual accepted states\n'
        f'{len(history)} base checks; {len(trials)} line-search trials\n'
        f'F completed / attempted: {calls["force_calls_completed"]} / {calls["force_calls"]}\n'
        f'T completed / attempted: {calls["tangent_calls_completed"]} / {calls["tangent_calls"]}\n'
        f'New failed attempts retained: {len(result["failed_attempts"])}\n'
        +fill(f'Codes: {failures_by_code}', width=55)+'\n'
        f'F floor = {rows[0]["force_scale_floor_half_N"]:.12g} N\n'
        f'Mean bound = {rows[0]["constraint_bound"]:.12g} mm\n\n'
        'OLD GIVEN-q HISTORY, NOT NEW FORCE STATES\n'
        'q = [0, .0125, .025] mm; all HISTORY ONLY\n'
        +fill(f'Old failures retained: {old_failures_by_code}', width=55)+'\n'
        f'Old F completed / attempted: {reference_calls["force_calls_completed"]} / {reference_calls["force_calls"]}\n'
        f'Old T completed / attempted: {reference_calls["tangent_calls_completed"]} / {reference_calls["tangent_calls"]}\n'
        'Old .0125 is internal history; no interpolation/pairing.\n'
        'P2 has no given-q / HP reference or new error bars.\n'
        'All original attempts remain in the ordinary records.')
    ax.text(.02, .97, summary, transform=ax.transAxes, va="top", fontsize=9.2, linespacing=1.35,
        bbox=dict(facecolor="#f5f7f8", edgecolor="#d7dfe4", boxstyle="round,pad=.5"))
    fig.suptitle(f'Original numerical gates plus independent body-load gate | {len(rows)} accepted states, '
        f'{len(result["trials"])} trials, {len(result["failed_attempts"])} recorded internal failures\n'
        "Held mean=1.06 mm; old invalid_J / internal subdivision history remains separate.", fontsize=14)
    save_figure(fig, PNG_NAMES[4])

    clock()
    fig, ax = plt.subplots(figsize=(12, 6.5), layout="constrained")
    mesh = polygons(ax, positions[0], cells, facecolors, linewidth=.16)
    polygons(ax, coords, cells, facecolors, reference=True, linewidth=.12)
    setup_geometry(ax, limits, "Actual accepted continuation segment only; geometry x1")
    label = ax.text(.01, .99, "", transform=ax.transAxes, va="top", fontsize=10,
        bbox=dict(facecolor="white", alpha=.9, edgecolor="none"))
    writer = PillowWriter(fps=2)
    gif = VIEW/"actual_force_states.gif"
    written_frames = 0
    with writer.saving(fig, str(gif), dpi=90):
        for i, (row, pos) in enumerate(zip(rows, positions)):
            clock()
            mesh.set_verts(pos[cells])
            label.set_text(f'Actual accepted state {i+1}/{len(rows)}; '
                f'{"requested target" if row["is_original_target"] else "internal subdivision"}\n'
                f'P_half={row["P_target_half_N"]:.10g} N; unknown q={row["body_q_mm"]:.10g} mm\n'
                f'Held mean={row["input_mean_mm"]:.10g} mm; input R={row["R_input_N"]:.10g} N\n'
                'Frame order is numerical path order, not physical time; no interpolation.')
            writer.grab_frame()
            written_frames += 1
    plt.close(fig)
    clock()
    write_json(VIEW/"geometry_metrics.json", dict(stage="L-CTIPFSTEP1", rows=metrics,
        scope="New cached JSON positions only; unsigned tip-node to original physical raster-body boundary segments excluding y40 symmetry cut; not pressure/contact qualification",
        right_medium_phase_check=dict(cell_count=480, all_original_nonbody_medium=True,
            source="new result.model.solid and original fixed IDs; no remask or scientific field read"),
        local_J_Hu_fields_read=False, new_force_tangent_HP_or_equilibrium_calls=0))
    receipt = dict(stage="L-CTIPFSTEP1", status="rendered_pending_root_visual_check",
        source_json_files=[protocol_id, observer_id, result_id, check_id],
        distinct_source_JSON_files=4, new_png_count=5,
        images=[identity(VIEW/name) for name in PNG_NAMES], animation=identity(gif),
        actual_animation_frames=written_frames, expected_animation_frames=len(rows),
        actual_geometry_scale=1, displacement_magnification=1,
        animation_frame_order="Only this segment all actual accepted states; old parent/probe scalars never animated; no interpolation or physical time claim",
        frame_count_basis="One successful writer.grab_frame per accepted state; no GIF decoding or frame-count reopening; renderer hashes final raw GIF bytes once.",
        scientific_calls=0, NPZ_fields_decoded=0, old_media_reads=0,
        full_body_load_targets_half_N=protocol["loads_half_N"],
        actual_segment_targets_half_N=segment,
        global_original_target_indices=[r["original_target_index"] for r in rows],
        source_selected_state_sha256=protocol["source_selected"]["state_sha256"],
        immediate_force_parent_identity=observer["immediate_force_parent_identity"],
        original_fixed_observer_identity_role="Historical observation authority only; not the direct force parent",
        new_target_reference_status="not_available_no_P2_reference",
        q_reference_error_mm=None, full_DOF_reference_error_mm=None, R_reference_error_N=None,
        parent_force_scalar_context_rows=parent_context,
        old_reference_accepted_count=len(reference_history),
        old_reference_failed_attempts=reference_failures,
        old_internal_reference_role="HISTORY ONLY; never an additional new force request or an intermediate pairing",
        root_scale_limit="Original root P0 retained; positive increasing P makes actual SP=P and does not alone distinguish rebasing",
        all_actual_Newton_base_checks=len(history), all_actual_line_search_trials=len(trials),
        invalid_trials_without_computed_merit=len(invalid_indices),
        local_J_Hu_fields_read=False, schematic_source_used_as_FE_geometry=False,
        display_only_zero_floors=dict(relative_residual=1e-18, mean_mm=1e-22, global_balance=1e-20, rigid_mm=1e-22,
            trial_merit_ratio=1e-22),
        geometry_metrics=identity(VIEW/"geometry_metrics.json"),
        generated_elapsed_seconds=time.monotonic()-START, generation_limit_seconds=MAX_SECONDS,
        created_utc=datetime.now(timezone.utc).isoformat(),
        qualification="Guided TMC total-force path only; no pressure, pure contact, capacity, release or stability qualification")
    clock()
    write_json(VIEW/"renderer_receipt.json", receipt)
    print(json.dumps(dict(status=receipt["status"],images=[str(VIEW/name) for name in PNG_NAMES],
        actual_animation_frames=written_frames)), flush=True)


if __name__ == "__main__":
    main()
