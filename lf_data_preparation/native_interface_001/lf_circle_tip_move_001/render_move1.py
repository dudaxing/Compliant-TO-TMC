"""Pure single-PNG MOVE1 viewer: reads only newly generated ordinary JSON.

No HF import, scientific array cache, force evaluation, or equilibrium solve.
The x1 geometry panel always uses the actual saved positions.
"""
from __future__ import annotations

import hashlib
from itertools import groupby
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection


BASE = Path(__file__).resolve().parent
RUN = BASE / "run_001"


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_new(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, allow_nan=False, indent=2)
        stream.write("\n")


def polygon_rows(points, connectivity, indices):
    return [[points[node] for node in connectivity[element]] for element in indices]


def finite_series(states, name):
    values = [float(state[name]) for state in states]
    if not all(math.isfinite(value) for value in values):
        raise ValueError("nonfinite saved scalar: " + name)
    return values


def main():
    png = RUN / "move1_actual.png"
    if png.exists() or (RUN / "render.json").exists():
        raise FileExistsError("the single viewer cannot overwrite a previous rendering")
    index = read_json(RUN / "artifacts" / "index.json")
    result_path = Path(index["probe_result_file"]).resolve()
    result_path.relative_to(BASE)
    if "candidate" in [part.casefold() for part in result_path.parts]:
        raise ValueError("viewer can read new result only, never candidate source")
    result_bytes = result_path.read_bytes()
    result = json.loads(result_bytes)
    if result.get("schema_version") != "hf-native-guided-probe-1.0":
        raise ValueError("wrong new probe result schema")
    if result.get("status") != "success" or result.get("target_reached") is not True:
        raise ValueError("viewer is limited to the successful new probe")
    states = result["accepted_steps"]
    if not states or len(states) < 3:
        raise ValueError("the successful probe must contain q0 and two nonzero targets")
    model = result["model"]
    reference = model["coordinates_mm"]
    connectivity = model["connectivity"]
    solid = model["solid"]
    body_nodes = model["body_nodes"]
    actual = states[-1]["positions_mm"]
    if len(reference) != 25 or len(connectivity) != 16 or len(actual) != 25:
        raise ValueError("viewer is restricted to the authorized 16-cell/50DOF fixture")
    if not body_nodes:
        raise ValueError("body membership missing")
    body_set = set(body_nodes)
    body_elements = [i for i, conn in enumerate(connectivity) if set(conn) <= body_set]
    solid_elements = [i for i, value in enumerate(solid) if bool(value)]
    medium_elements = [i for i, value in enumerate(solid) if not bool(value) and i not in body_elements]
    q = finite_series(states, "body_q_mm")
    input_mean = finite_series(states, "input_mean_mm")
    r = finite_series(states, "R_input_N")
    drive = finite_series(states, "Q_drive_half_N")
    residual = finite_series(states, "relative_residual")
    minimum_j = finite_series(states, "minimum_J")
    d_hold = float(result["probe_task"]["held_input_mean_mm"])
    on_body = [float(state["force_on_body_N"]["total"][0]) for state in states]
    material_drive = [-float(state["force_on_body_N"]["material"][0]) for state in states]
    hu_drive = [-float(state["force_on_body_N"]["regularization"][0]) for state in states]
    if not all(math.isfinite(value) for values in (on_body, material_drive, hu_drive) for value in values):
        raise ValueError("nonfinite saved body force component")
    fig, axes = plt.subplots(2, 3, figsize=(15, 8.5), layout="constrained")
    geometry, controls, force, motion, convergence, jacobian = axes.flat

    geometry.add_collection(PolyCollection(polygon_rows(reference, connectivity, range(16)),
        facecolors="none", edgecolors="#a3a3a3", linewidths=.7, linestyles="dashed"))
    for ids, color, label in ((medium_elements, "#e8eef3", "medium"),
                             (solid_elements, "#66859a", "solid"),
                             (body_elements, "#e28e39", "moving body")):
        geometry.add_collection(PolyCollection(polygon_rows(actual, connectivity, ids),
            facecolors=color, edgecolors="#324455", linewidths=.8, label=label))
    geometry.scatter([reference[n][0] for n in body_nodes], [reference[n][1] for n in body_nodes],
                     s=28, marker="o", facecolors="none", edgecolors="#9b4d13", label="body reference")
    geometry.scatter([actual[n][0] for n in body_nodes], [actual[n][1] for n in body_nodes],
                     s=13, marker="x", color="#731f10", label="body actual")
    geometry.autoscale_view()
    geometry.set_aspect("equal")
    geometry.margins(.07)
    geometry.set(title="Saved geometry: actual displacement x1", xlabel="x [mm]", ylabel="y [mm]")
    geometry.legend(fontsize=7, loc="lower right")
    geometry.text(.02, .98, "Small motion may overlap reference at x1.\nNo deformation magnification.",
                  transform=geometry.transAxes, va="top", fontsize=7,
                  bbox=dict(facecolor="white", alpha=.88, edgecolor="none"))

    q_um = [value * 1000 for value in q]
    controls.plot(q_um, [value * 1000 for value in input_mean], "o-", color="#24627a", label="input mean")
    controls.axhline(d_hold * 1000, color="#d87d2c", ls="--", label="held target")
    controls.set(title="Mechanism input remains held", xlabel="body q [um]", ylabel="input mean [um]")
    controls.legend(fontsize=8)
    controls.ticklabel_format(axis="y", style="plain", useOffset=False)
    controls.text(.02, .04, "max |mean - hold| = %.3g mm" % max(abs(v-d_hold) for v in input_mean),
                  transform=controls.transAxes, fontsize=8)

    force.plot(q_um, drive, "o-", label="body drive Q total", color="#c26720")
    force.plot(q_um, material_drive, "^-", label="Q material", color="#467b4e")
    force.plot(q_um, hu_drive, "v-", label="Q Hu", color="#85649b")
    force.plot(q_um, on_body, "s--", label="ON body Fx total", color="#934b79")
    input_axis = force.twinx()
    input_axis.plot(q_um, r, "D:", markersize=4, label="input R (right axis)", color="#236984")
    input_axis.set_ylabel("input R [N] (right scale)", color="#236984", fontsize=8)
    input_axis.tick_params(axis="y", labelsize=7, colors="#236984")
    input_axis.ticklabel_format(axis="y", style="sci", scilimits=(-2, 2), useOffset=False)
    force.ticklabel_format(axis="y", style="sci", scilimits=(-2, 2), useOffset=False)
    force.axhline(0, color="#999999", lw=.6)
    force.set(title="Saved signed forces: two separate scales", xlabel="body q [um]", ylabel="body force [N] (left scale)")
    force_lines, force_labels = force.get_legend_handles_labels()
    input_lines, input_labels = input_axis.get_legend_handles_labels()
    force.legend(force_lines+input_lines, force_labels+input_labels, fontsize=6.8, ncol=2, loc="upper left")
    force.text(.02, .04, "Q = -ON body Fx; both axes are half-model N.\n"
               "t = 2 mm is included; left/right scales differ.",
               transform=force.transAxes, fontsize=6.8,
               bbox=dict(facecolor="white", alpha=.85, edgecolor="none"))

    for node in body_nodes:
        delta = [(state["positions_mm"][node][0] - reference[node][0]) * 1000 for state in states]
        motion.plot(q_um, delta, "o-", markersize=3, lw=.9, label="node %d" % node)
    motion.plot(q_um, q_um, "k--", lw=1., label="prescribed q")
    motion.set(title="Actual rigid-body movement (coordinate difference)", xlabel="prescribed q [um]", ylabel="saved node dx [um]")
    motion.legend(fontsize=7, ncol=2)

    # Zero is rendered at the positive machine plotting floor only; recorded
    # JSON values are unchanged. This floor is not a mechanical acceptance gate.
    floor = 1e-30
    checks_plotted = 0
    history = result["newton_history"]
    for stage_q, group in groupby(history, key=lambda row: float(row["d"])):
        checks = list(group)
        values = [float(row["relative_residual"]) for row in checks]
        if not all(math.isfinite(v) and v >= 0 for v in values):
            raise ValueError("invalid saved Newton residual")
        if values:
            convergence.semilogy(list(range(checks_plotted, checks_plotted+len(values))),
                                 [max(v, floor) for v in values], "o-", ms=3,
                                 label="q %.3g um" % (stage_q*1000))
            checks_plotted += len(values)
    if not checks_plotted:
        raise ValueError("saved Newton checks are required for the convergence panel")
    convergence.axhline(1e-9, color="#ad6e28", ls="--", label="relative residual gate")
    convergence.set(title="Saved Newton history (all attempts)", xlabel="global saved check index", ylabel="relative free residual")
    convergence.legend(fontsize=7)
    convergence.text(.02, .02, "zero shown at 1e-30 for log display only", transform=convergence.transAxes, fontsize=7)

    jacobian.plot(q_um, minimum_j, "o-", color="#467b4e")
    jacobian.axhline(0, color="#999999", lw=.6)
    jacobian.set(title="Saved minimum J at accepted states", xlabel="body q [um]", ylabel="min det(F)")
    for ax in axes.flat:
        ax.grid(alpha=.18)
        ax.tick_params(labelsize=8)
    fig.suptitle("L-CTIPMOVE1 | 16-cell interface fixture | saved observations only\n"
                 "Guided displacement probe; this is not a grasp-capacity or release result", fontsize=13)
    fig.savefig(png, dpi=170)
    plt.close(fig)
    raw = png.read_bytes()
    write_new(RUN / "render.json", dict(schema="hf-move1-render-1", status="rendered_pending_visual_check",
        source=dict(path=str(result_path), sha256=hashlib.sha256(result_bytes).hexdigest()),
        output=dict(path=str(png), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()),
        accepted_state_count=len(states), newton_checks_plotted=checks_plotted,
        scientific_calls=0, source_array_reads=0, new_png_count=1,
        geometry_scale=1, force_unit="N for half-model; includes fixture thickness 2mm",
        plot_only_zero_floor=floor, production_installations=0))


if __name__ == "__main__":
    main()
