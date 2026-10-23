"""Draw a conceptual control diagram; no FE data, geometry or solver is read."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Arc, FancyArrowPatch, Polygon, Rectangle, Wedge

HERE = Path(__file__).resolve().parent
NAVY = "#17324d"
BLUE = "#1f6da8"
TEAL = "#087f8c"
ORANGE = "#b96014"
LIGHT = "#eef6fa"
GREY = "#526676"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "svg.fonttype": "none",
    "savefig.facecolor": "white",
})


def arrow(ax, start, end, color=TEAL, lw=2.5, style="-|>"):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle=style,
                                 mutation_scale=16, linewidth=lw,
                                 color=color, zorder=6))


def mechanism(ax, force_control):
    """Every coordinate below is an illustration coordinate, never an FE node."""
    ax.set(xlim=(0, 10), ylim=(0, 6.3), aspect="equal")
    ax.axis("off")
    ax.add_patch(Rectangle((0.12, 0.15), 9.76, 6.0, facecolor="white",
                           edgecolor="#cfdae2", linewidth=1.2))
    title = "B  Planned force control" if force_control else "A  Existing displacement probe"
    ax.text(0.5, 5.72, title, color=NAVY, fontsize=17, fontweight="bold")
    if force_control:
        ax.text(0.5, 5.25, r"Given $P_{\rm half}$  $\longrightarrow$  solve unknown $q$", color=TEAL, fontsize=14)
    else:
        ax.text(0.5, 5.25, r"Given $q$  $\longrightarrow$  measure $Q_{\rm half}$", color=BLUE, fontsize=14)

    # The illustrative domain includes the third medium up to a free right edge.
    ax.add_patch(Rectangle((0.7, 1.55), 8.2, 3.05, facecolor=LIGHT,
                           edgecolor="#b6d1df", linewidth=0.9))
    ax.text(0.9, 1.75, "Third medium retained", color=BLUE, fontsize=11)
    ax.plot([0.7, 8.9], [3.8, 3.8], linestyle="--", color=GREY, linewidth=1)
    ax.text(3.25, 3.94, "Symmetry plane", color=GREY, fontsize=10)

    # A stylized gripper approaches the workpiece with a visible gap. No contact
    # state, contact point or deformation is implied by this drawing.
    gripper = [(0.7, 2.15), (2.05, 2.15), (3.0, 2.65), (4.02, 2.87),
               (3.85, 3.1), (2.88, 2.95), (1.9, 2.5), (0.7, 2.5)]
    ax.add_patch(Polygon(gripper, closed=True, facecolor="#8ba6bb",
                         edgecolor=NAVY, linewidth=1.6))
    ax.text(1.0, 3.35, "Gripper", color=NAVY, fontsize=12)
    arrow(ax, (1.0, 4.12), (2.15, 4.12), color=NAVY)
    ax.text(0.85, 4.35, r"Mean input held: $d_{\rm hold}=0.50$ mm", color=NAVY, fontsize=10.7)

    center = (6.25, 3.8)
    ax.add_patch(Wedge(center, 1.3, 180, 360, facecolor="#f7dfb1",
                       edgecolor=ORANGE, linewidth=1.7))
    ax.text(6.25, 3.13, "Guided\nworkpiece", ha="center", va="center", color=NAVY, fontsize=12)
    ax.text(6.25, 2.17, r"$u_y=0$, rotation $=0$", ha="center", color=NAVY, fontsize=11)

    if force_control:
        arrow(ax, (5.5, 4.12), (7.08, 4.12), color=TEAL)
        ax.text(6.25, 4.35, r"Applied $+P_{\rm half}$", color=TEAL, ha="center", fontsize=11)
        ax.text(6.25, 1.72, r"$q$ is unknown; not prescribed", color=TEAL, ha="center", fontsize=11, fontweight="bold")
    else:
        arrow(ax, (5.5, 4.12), (7.08, 4.12), color=BLUE)
        ax.text(6.25, 4.35, r"Imposed $q$ along $+x$", color=BLUE, ha="center", fontsize=11)
        ax.text(6.25, 1.72, r"Read required drive $Q_{\rm half}$", color=BLUE, ha="center", fontsize=11)

    # Internal weak force ON the workpiece has the opposite axial sign.
    arrow(ax, (5.55, 2.72), (4.35, 2.72), color=ORANGE)
    ax.text(4.3, 2.3, r"$F_{{\rm on},x}=-Q_{\rm half}$", color=ORANGE, ha="center", fontsize=10.5)
    # The guide supports vertical reaction and a moment, while q remains axial.
    arrow(ax, (7.7, 2.55), (7.7, 3.3), color=GREY, lw=1.8)
    ax.add_patch(Arc((7.7, 3.45), 0.62, 0.52, theta1=30, theta2=300,
                     linewidth=1.4, color=GREY))
    ax.text(8.1, 2.8, "Guide:\n$F_y$, $M_z$", color=GREY, fontsize=9.8)

    ax.plot([8.9, 8.9], [1.55, 4.6], color=BLUE, linestyle=(0, (3, 2)), linewidth=1.7)
    arrow(ax, (8.56, 4.0), (9.28, 4.0), color=BLUE, lw=1.5, style="<->")
    ax.text(9.18, 3.55, "Right edge\n$u_x$ free", color=BLUE, fontsize=9.5, ha="center")
    arrow(ax, (8.1, 1.17), (9.0, 1.17), color=NAVY, lw=1.5)
    ax.text(9.1, 1.17, "+x", color=NAVY, fontsize=10, va="center")

    ax.text(0.55, 0.65,
            r"$Q_{\rm half}=\sum_{a\in\mathrm{body}} f_{{\rm int},a,x}=-F_{{\rm on},x}$",
            color=NAVY, fontsize=12.6)
    if force_control:
        ax.text(0.55, 0.28, r"New equilibrium equation: $Q_{\rm half}-P_{\rm half}=0$", color=TEAL, fontsize=11.5)
    else:
        ax.text(0.55, 0.28, "Reaction is an output; q is an imposed input.", color=BLUE, fontsize=11.5)


def main():
    fig = plt.figure(figsize=(17.6, 11.6), facecolor="white")
    fig.text(0.04, 0.955, "Guided axial workpiece control", color=NAVY,
             fontsize=25, fontweight="bold")
    fig.text(0.04, 0.915, "Same physics and guided motion; change which axial quantity is prescribed.",
             color=GREY, fontsize=14)
    left = fig.add_axes([0.035, 0.30, 0.46, 0.58])
    right = fig.add_axes([0.505, 0.30, 0.46, 0.58])
    mechanism(left, False)
    mechanism(right, True)

    fig.patches.append(Rectangle((0.04, 0.105), 0.92, 0.165,
                                 transform=fig.transFigure,
                                 facecolor="#f3f7f9", edgecolor="#cddbe3"))
    fig.text(0.06, 0.235,
             r"Load convention: half-model N already includes thickness (20 mm).  $P_{\rm full}=2P_{\rm half}$; same $q$.",
             fontsize=13, color=NAVY)
    fig.text(0.06, 0.193,
             r"Nonzero preload anchor: $q_0=0$,  $P_0=3.68642113\times10^{-5}$ N (half model).",
             fontsize=13, color=NAVY)
    fig.text(0.06, 0.151,
             r"Future endpoint load: $P_1=4.32723069\times10^{-5}$ N, from the existing low-input $q=0.025$ mm reaction.",
             fontsize=12.3, color=NAVY)
    fig.text(0.04, 0.068, "Concept only: not to scale; no actual geometry, deformation or tip contact is asserted.",
             fontsize=11, color=GREY)
    fig.text(0.04, 0.036, "NEW FORCE-CONTROL IMPLEMENTATION AND SMALL-MODEL TESTS: NOT RUN", fontsize=12.5,
             color=ORANGE, fontweight="bold")
    fig.savefig(HERE / "control_schematic.svg")
    svg = HERE / "control_schematic.svg"
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text(encoding="utf-8").splitlines()) + "\n", encoding="utf-8", newline="\n")
    fig.savefig(HERE / "control_schematic.png", dpi=100)
    plt.close(fig)


if __name__ == "__main__":
    main()
