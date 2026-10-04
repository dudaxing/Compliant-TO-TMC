"""Plot saved NumPy / HP force comparisons, without constitutive evaluation."""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
import numpy as np


KINDS = ("total", "material", "regularization")
LABELS = ("Total force", "Material force", "Regularization force")
BLUE, ORANGE, GREEN = "#0072B2", "#D55E00", "#009E73"
DEFAULT_TITLE = "NumPy complete force vs. saved HP reference | prescribed near-rotation state, not an equilibrium solve"


def plot(arrays, output, title=DEFAULT_TITLE):
    with np.load(arrays, allow_pickle=False) as saved:
        data = {name: saved[name].copy() for name in saved.files}
    xy, cells = data["coordinates"], data["connectivity"]
    displacement = (data["u_lift"] + data["u_fluctuation"]).reshape(xy.shape)
    deformed = xy + displacement
    errors, limits = data["normalized_error"], data["thresholds"]
    candidate = [data[k + "_force"].reshape(xy.shape) for k in KINDS]
    reference = [data["reference_" + k + "_force"].reshape(xy.shape) for k in KINDS]
    difference = [data["difference_" + k + "_force"].reshape(xy.shape) for k in KINDS]
    if xy.ndim != 2 or xy.shape[1] != 2 or cells.ndim != 2 or cells.shape[1] != 4:
        raise ValueError("Require 2D nodes and Q1 connectivity")
    if errors.shape != (3,) or limits.shape != (3,) or np.any(limits <= 0):
        raise ValueError("Require three saved normalized errors and positive thresholds")
    if not all(np.all(np.isfinite(value)) for value in (xy, deformed, errors, limits, *candidate, *reference, *difference)):
        raise ValueError("Require finite saved force / geometry / comparison arrays")
    extent = np.concatenate((xy, deformed))
    span = max(float(np.ptp(extent[:, 0])), float(np.ptp(extent[:, 1])))
    if span <= 0:
        raise ValueError("Require a nonzero geometry extent")
    lo, hi = extent.min(axis=0) - .35 * span, extent.max(axis=0) + .35 * span
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    fig = plt.figure(figsize=(18, 13), layout="constrained")
    grid = fig.add_gridspec(4, 3, height_ratios=(1.1, 1.1, .8, .75))
    fig.suptitle(title, fontsize=16)

    def mesh(ax):
        ax.add_collection(PolyCollection(xy[cells], facecolors="none", edgecolors="#aeb6bd", linewidths=.8, linestyles="--"))
        ax.add_collection(PolyCollection(deformed[cells], facecolors="#edf1f4", edgecolors="#53616b", linewidths=.9))
        ax.scatter(deformed[:, 0], deformed[:, 1], s=13, color="#53616b", zorder=3)
        if len(xy) <= 16:
            for index, position in enumerate(deformed):
                ax.annotate(str(index), position, xytext=(4, 4), textcoords="offset points", fontsize=8)
        ax.set(xlim=(lo[0], hi[0]), ylim=(lo[1], hi[1]), xlabel="x [mm]", ylabel="y [mm]")
        ax.set_aspect("equal", adjustable="box")

    def arrows(ax, vectors, scale, color, width, outline=False):
        # Convert to display mm before quiver forms coordinate differences.
        # Adding forces as small as 1e-40 to mm coordinates would round to zero.
        shown = vectors / scale
        return ax.quiver(deformed[:, 0], deformed[:, 1], shown[:, 0], shown[:, 1],
                         angles="xy", scale_units="xy", scale=1, width=width,
                         color="none" if outline else color, edgecolor=color if outline else "none",
                         linewidth=.8 if outline else 0, zorder=4 if outline else 5)

    for column, label in enumerate(LABELS):
        ax = fig.add_subplot(grid[0, column])
        mesh(ax)
        force_max = max(float(np.linalg.norm(candidate[column], axis=1).max()),
                        float(np.linalg.norm(reference[column], axis=1).max()))
        scale = force_max / (.28 * span) if force_max else 1.
        arrows(ax, reference[column], scale, BLUE, .007, outline=True)
        arrows(ax, candidate[column], scale, ORANGE, .0035)
        ax.plot([], [], color=BLUE, linewidth=2, label="Saved HP reference (outline)")
        ax.plot([], [], color=ORANGE, linewidth=2, label="NumPy candidate (filled)")
        ax.legend(fontsize=8, loc="lower left")
        ax.set_title(f"{label}: nodal vectors\nGeometry x1; arrow scale {scale:.3e} N/mm", fontsize=11)

        ax = fig.add_subplot(grid[1, column])
        mesh(ax)
        difference_max = float(np.linalg.norm(difference[column], axis=1).max())
        delta_scale = difference_max / (.28 * span) if difference_max else 1.
        arrows(ax, difference[column], delta_scale, GREEN, .005)
        ax.set_title(f"Candidate - reference: independently scaled\nArrow scale {delta_scale:.3e} N/mm; max |delta f_node| = {difference_max:.3e} N", fontsize=10)
        if difference_max == 0:
            ax.text(.5, .1, "Saved binary64 differences are exactly zero", transform=ax.transAxes,
                    ha="center", fontsize=8, color=GREEN)

        ax = fig.add_subplot(grid[2, column])
        component = difference[column].ravel()
        dofs = np.arange(len(component))
        ax.axhline(0, color="#69757e", linewidth=.7)
        ax.plot(dofs, component, "o-", color=GREEN, markersize=3, linewidth=1)
        if len(component) <= 32:
            ax.set_xticks(dofs, [f"{index // 2}{'x' if index % 2 == 0 else 'y'}" for index in dofs])
        ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 0), useOffset=False)
        dof_label = "Global node / component (zero-based)" if len(component) <= 32 else "Global DOF index (zero-based)"
        ax.set(xlabel=dof_label, ylabel="Candidate - reference [N]",
               title=f"All {len(component)} force components; signed difference")
        ax.grid(alpha=.2)

    ax = fig.add_subplot(grid[3, :2])
    positions = np.arange(3)
    positive_errors = errors[errors > 0]
    floor = min(float(limits.min()), float(positive_errors.min()) if len(positive_errors) else float(limits.min())) / 10
    plotted = np.where(errors > 0, errors, floor)
    ax.scatter(positions, plotted, s=65, color=ORANGE, label="Saved normalized error", zorder=3)
    ax.scatter(positions, limits, marker="_", s=1100, color=BLUE, linewidths=2.5, label="Original acceptance threshold")
    for index, (value, limit) in enumerate(zip(errors, limits)):
        passed = value <= limit
        ax.annotate(f"{value:.3e} | {'PASS' if passed else 'FAIL'}", (index, plotted[index]),
                    xytext=(0, 9), textcoords="offset points", ha="center", fontsize=10,
                    color=GREEN if passed else ORANGE)
    ax.set(yscale="log", xticks=positions, xticklabels=LABELS, xlim=(-.6, 2.6),
           ylim=(min(floor, float(plotted.min())) / 3, max(float(limits.max()), float(plotted.max())) * 8),
           ylabel="Saved normalized force error", title="Unchanged acceptance scale / thresholds (log axis)")
    ax.legend(fontsize=9, loc="upper right")
    ax.grid(axis="y", alpha=.2, which="both")
    if np.any(errors == 0):
        ax.text(.01, .02, f"For visibility only, exact zeros are plotted at {floor:.1e}; labels give actual values.",
                transform=ax.transAxes, fontsize=8)

    ax = fig.add_subplot(grid[3, 2])
    ax.axis("off")
    lines = ["Saved comparison values", "", "Force residuals: N; coordinates: mm.",
             "Reference geometry dashed; deformed geometry x1.",
             "Force / difference arrows have separate scales.",
             "Display displacement = lift + fluctuation.",
             "Small roundoff differences are displayed explicitly.", ""]
    for name, err, limit in zip(LABELS, errors, limits):
        lines.append(f"{name}: {err:.6e} / {limit:.1e}")
    lines += ["", "Saved arrays only; no material or equilibrium solve."]
    ax.text(0, 1, "\n".join(lines), va="top", fontsize=10, linespacing=1.3)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=100)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arrays", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--title", default=DEFAULT_TITLE)
    args = parser.parse_args()
    plot(args.arrays, args.output, args.title)
    print(str(args.output.resolve()))


if __name__ == "__main__":
    main()
