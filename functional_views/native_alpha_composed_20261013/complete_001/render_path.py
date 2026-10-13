"""Future two-PNG renderer of composed plain rows; no saved arrays or GIFs."""
from pathlib import Path
import argparse
import json


def render_path(data: dict, output_directory: Path, checkpoint=lambda: None) -> list[Path]:
    if data["schema_version"] != "mpath1-composed-observations-1.0":
        raise ValueError("Require composed saved observations")
    checkpoint()
    # Deferred imports: the caller starts and controls the whole plotting window.
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    checkpoint()
    rows = data["unique_rows"]
    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)
    paths = [output/"path_ports.png", output/"path_workpiece.png"]
    if any(path.exists() for path in paths): raise FileExistsError("Use new PNG outputs")
    branches, previous, current_leg = [], None, None
    for entry in rows:
        leg = entry["result_state"]["leg"]
        if leg == "origin": leg = "loading"
        if leg not in ("loading", "unloading"):
            raise ValueError("Unexpected chronological leg: " + leg)
        if leg != current_leg:
            branches.append((leg, [] if previous is None else [previous]))
            current_leg = leg
        branches[-1][1].append(entry)
        previous = entry
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    try:
        for leg, branch in branches:
            checkpoint()
            x = [r["observations"]["d_mm"] for r in branch]
            for ax, key, ylabel in zip(axes, ("R_input_N", "q_out_mm"), ("Signed input R [N]", "Weighted output qout [mm]")):
                ax.plot(x, [r["observations"][key] for r in branch], "o-" if leg == "loading" else "s--", markersize=3, label=leg)
                ax.set(xlabel="Recorded mean input d [mm]", ylabel=ylabel)
                ax.grid(alpha=.25); ax.legend()
        fig.suptitle("Saved path order across separate sources; original loading and unloading legs")
        fig.tight_layout(); checkpoint(); fig.savefig(paths[0], dpi=150); checkpoint()
    finally:
        plt.close(fig)
    fig, axes = plt.subplots(3, 2, figsize=(13, 11))
    try:
        x = [r["unique_index"] for r in rows]
        colors = dict(total="#1864ab", material="#e67700", regularization="#9c36b5")
        for ax, axis in zip(axes[0], ("x", "y")):
            checkpoint()
            for component, color in colors.items():
                if axis == "y" and component == "regularization": continue
                label = "Hu" if component == "regularization" else component
                ax.plot(x, [r["observations"][component+"_body_F"+axis+"_N"] for r in rows], "o-", markersize=3, color=color, label=label)
            ax.set(ylabel="Signed lower-workpiece F"+axis+" [N]", xlabel="Chronological unique accepted index")
            ax.grid(alpha=.25); ax.legend()
        hu, bottom = axes[1]
        hu.plot(x, [r["observations"]["regularization_body_Fy_N"] for r in rows], "o-", markersize=3, color=colors["regularization"])
        hu.set(ylabel="Signed Hu lower-workpiece Fy [N]", xlabel="Chronological unique accepted index", title="Hu Fy uses its own linear force scale")
        bottom.plot(x, [r["observations"]["tip_to_bottom_mm"] for r in rows], "o-", markersize=3, color="#2b8a3e")
        bottom.set_yscale("symlog", linthresh=.001)
        bottom.set(ylabel="Unsigned tip-to-bottom finite distance [mm]", xlabel="Chronological unique accepted index", title="Bottom distance: symlog, linear within 0.001 mm")
        sides, inputs = axes[2]
        for key, label in (("tip_to_left_mm", "left"), ("tip_to_right_mm", "right")):
            sides.plot(x, [r["observations"][key] for r in rows], "o-", markersize=3, label=label)
        sides.set(ylabel="Unsigned finite side distances [mm]", xlabel="Chronological unique accepted index", title="Side distances use their own linear scale")
        sides.legend()
        inputs.plot(x, [r["observations"]["d_mm"] for r in rows], "o-", markersize=3, color=".25")
        inputs.set(ylabel="Recorded mean input d [mm]", xlabel="Chronological unique accepted index", title="Original loading/unloading order")
        for ax in axes.flat: ax.grid(alpha=.25)
        transitions = [rows[i-1] for i in range(1, len(rows)) if rows[i]["result_state"]["leg"] == "unloading" and rows[i-1]["result_state"]["leg"] in ("origin", "loading")]
        for entry in transitions:
            for ax in axes.flat:
                ax.axvline(entry["unique_index"], color=".45", linestyle="--", alpha=.55,
                           label="Loading peak / global " + str(entry["result_state"]["original_target_index"]))
            axes[0,1].legend()
        fig.suptitle("Original saved workpiece components and finite distances; pressure/clamp qualification unchanged")
        fig.tight_layout(); checkpoint(); fig.savefig(paths[1], dpi=150); checkpoint()
    finally:
        plt.close(fig)
    return paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    args = parser.parse_args()
    if args.input.suffix.lower() != ".json": raise ValueError("Input must be ordinary JSON")
    render_path(json.loads(args.input.read_text(encoding="utf-8")), args.output_directory)


if __name__ == "__main__": main()
