"""Show accepted NumPy C1 states and the saved historical HP curve; no solve."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
import numpy as np
from PIL import Image


def load_npz(path):
    with np.load(path, allow_pickle=False) as saved:
        return {key: saved[key].copy() for key in saved.files}


def state_sha256(state):
    digest = hashlib.sha256(b"split_displacement_v1")
    digest.update(np.asarray([len(state["u_lift"])], dtype="<i8").tobytes())
    for name in ("u_lift", "u_fluctuation"):
        digest.update(np.asarray(state[name], dtype="<f8").tobytes())
    return digest.hexdigest()


def file_metadata(path):
    path = path.resolve()
    root = Path(__file__).resolve().parents[2]
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return dict(path=path.relative_to(root).as_posix() if path.is_relative_to(root) else str(path),
                bytes=path.stat().st_size, sha256=digest)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approach", type=Path, required=True)
    parser.add_argument("--compression", type=Path)
    parser.add_argument("--audit", type=Path, help="Explicit passed new-state HP80/120 audit summary")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    records, states, phases, summaries = [], [], [], []
    input_files, state_files = [], []
    model = load_npz(args.approach / "model.npz")
    for directory in (args.approach, args.compression):
        if directory is None:
            continue
        summary = json.loads((directory / "summary.json").read_text(encoding="utf-8"))
        other_model = load_npz(directory / "model.npz")
        for key in ("coordinates", "connectivity", "solid", "fixed_dofs"):
            if not np.array_equal(model[key], other_model[key]):
                raise ValueError("Stages use different model arrays")
        summaries.append(summary)
        input_files.extend(file_metadata(directory / name) for name in ("summary.json", "model.npz"))
        for record in summary["states"]:
            state = load_npz(directory / record["path"])
            if state_sha256(state) != record["state_sha256"]:
                raise ValueError("Displayed two-array state differs from its saved identity")
            records.append(record)
            states.append(state)
            phases.append(summary["phase"])
            state_files.append(dict(phase=summary["phase"], state_sha256=record["state_sha256"],
                                   **file_metadata(directory / record["path"])))
    if not states:
        raise ValueError("No accepted states to display")
    xy, cells, solid = model["coordinates"], model["connectivity"], model["solid"]
    fixed = model["fixed_dofs"].astype(int)
    nodes = np.unique(fixed // 2)
    displacement = [(s["u_lift"] + s["u_fluctuation"]).reshape(xy.shape) for s in states]
    positions = [xy + u for u in displacement]
    reactions = []
    for state in states:
        force = np.zeros(xy.size)
        force[fixed] = state["internal_force"][fixed]
        reactions.append(force.reshape(xy.shape))
    drive = np.array([r["physical_drive_mm"] for r in records])
    normal = np.array([r["normal_force_N"] for r in records])
    body = np.array([r["bottom_body_force_N"] for r in records])
    outer = np.array([r["bottom_outer_force_N"] for r in records])
    jacobian = np.array([r["minimum_J"] for r in records])
    gaps = np.array([r["body_gap_display_min_mm"] for r in records])
    if np.any(jacobian <= 0) or np.any(gaps <= 0):
        raise ValueError("Log curves require positive saved J and body gaps")
    baseline = summaries[0]["baseline_curve"]
    baseline_drive = np.array([float(row["d"]) for row in baseline])
    baseline_force = np.array([row["normal_force_N"] for row in baseline])
    maximum_u = max(float(np.linalg.norm(u, axis=1).max()) for u in displacement)
    maximum_r = max(float(np.linalg.norm(r[nodes], axis=1).max()) for r in reactions)
    extent = np.concatenate([xy] + positions)
    span = float(np.ptp(extent[:, 0]))
    arrow_mm_per_N = .12 * span / maximum_r if maximum_r else 1.
    lo, hi = extent.min(axis=0) - .12 * span, extent.max(axis=0) + .12 * span
    top_plane = float(np.mean(xy[model["top_nodes"], 1]))
    independently_audited = False
    if args.audit:
        audit = json.loads(args.audit.read_text(encoding="utf-8"))
        if (audit["status"] != "pass" or audit["precision_pair"] != [80, 120] or
                not audit["new_references_computed"] or audit["historical_HP_substituted"]):
            raise ValueError("Require a passed independent new-state HP80/120 audit")
        audited_records = audit["records"]
        if not all(r["status"] == "pass" and r["checks"] and all(c["pass_gate"] for c in r["checks"])
                   for r in audited_records):
            raise ValueError("New-state audit contains missing or failed checks")
        covered = Counter((r["phase"], r["state_sha256"], float(r["parameter_s"])) for r in audited_records)
        expected = Counter((phase, r["state_sha256"], float(r["parameter_s"])) for phase, r in zip(phases, records))
        if any(covered[key] < count for key, count in expected.items()):
            raise ValueError("New-state audit does not cover every displayed stage / state record")
        independently_audited = True
    audit_label = ("New states passed independent HP80/120 audit." if independently_audited else
                   "New states are NOT independently HP audited.")
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    args.output.mkdir(parents=True, exist_ok=True)
    frames = []

    def mesh(ax, position, colors):
        collection = PolyCollection(position[cells], facecolors=colors,
                                    edgecolors="#87939c", linewidths=.35)
        ax.add_collection(collection)
        ax.axhline(top_plane, color="#52616b", linewidth=.8, linestyle="--")
        ax.set(xlim=(lo[0], hi[0]), ylim=(lo[1], hi[1]), xlabel="x [mm]", ylabel="y [mm]")
        ax.set_aspect("equal", adjustable="box")
        return collection

    for index, (position, u, reaction, record, phase) in enumerate(zip(positions, displacement, reactions, records, phases)):
        fig, axes = plt.subplots(2, 3, figsize=(15, 9), layout="constrained")
        fig.suptitle(f"New NumPy C1 equilibrium | accepted state {index + 1}/{len(states)} | {phase} | drive {drive[index]:.8g} mm", fontsize=15)
        ax = axes[0, 0]
        mesh(ax, xy, np.where(solid[:, None], [.35, .43, .48, .75], [.86, .91, .94, .35]))
        ax.add_collection(PolyCollection(position[cells[solid]], facecolors="none", edgecolors="#D55E00", linewidths=1.2))
        ax.scatter(xy[nodes, 0], xy[nodes, 1], marker="^", s=10, color="#253545")
        ax.set_title("Solid / background medium + actual solid outline\nOrange: deformed; displacement scale = 1")
        ax = axes[0, 1]
        collection = mesh(ax, position, "#dddddd")
        collection.set_array(np.linalg.norm(u, axis=1)[cells].mean(axis=1))
        collection.set_cmap("viridis")
        collection.set_clim(0, maximum_u if maximum_u else 1.)
        ax.add_collection(PolyCollection(position[cells[solid]], facecolors="none", edgecolors="#263b50", linewidths=.7))
        fig.colorbar(collection, ax=ax, label="Mean nodal |u| per cell [mm]", shrink=.7)
        ax.set_title("Actual deformed mesh; displacement magnitude\nOne fixed color range for every accepted state")
        ax = axes[0, 2]
        mesh(ax, position, np.where(solid[:, None], [.50, .62, .67, .65], [.86, .91, .94, .3]))
        shown = reaction[nodes] * arrow_mm_per_N
        ax.quiver(position[nodes, 0], position[nodes, 1], shown[:, 0], shown[:, 1],
                  angles="xy", scale_units="xy", scale=1, color="#D55E00", width=.005)
        ax.set_title(f"Constraint reactions: apparatus on model\nFixed arrow scale {arrow_mm_per_N:.5g} mm/N")
        ax = axes[1, 0]
        ax.plot(baseline_drive, baseline_force, "x--", color="#63727c", markersize=4, linewidth=1,
                label="Historical HP80 path (comparison only)")
        ax.plot(drive, normal, "o-", color="#0072B2", markersize=3, label="New: minus full top reaction")
        ax.plot(drive, body, "s--", color="#009E73", markersize=3, label="New: bottom solid-body group")
        ax.plot(drive, outer, ".--", color="#D55E00", markersize=4, label="New: bottom outer-medium group")
        ax.scatter(drive[index], normal[index], s=80, facecolors="none", edgecolors="#0072B2", zorder=5)
        ax.axvline(drive[index], color="#b6bfc5", linewidth=.7)
        ax.set_yscale("symlog", linthresh=1e-3)
        all_forces = np.concatenate((normal, body, outer, baseline_force))
        ax.set_ylim(min(0., float(all_forces.min()) * 1.2), max(float(all_forces.max()) * 1.2, 1e-3))
        ax.set(xlabel="Physical mean drive [mm]", ylabel="Force [N] (symlog; linear below 1e-3)",
               title="Force / drive history; all actual accepted states")
        ax.legend(fontsize=8, loc="upper left")
        ax.grid(alpha=.2, which="both")
        ax = axes[1, 1]
        ax.semilogy(drive, jacobian, "o-", color="#0072B2", markersize=3, label="Minimum J")
        ax.set(xlabel="Physical mean drive [mm]", ylabel="Minimum J [dimensionless]",
               title="Compression and displayed body / plane gap")
        gap_ax = ax.twinx()
        gap_ax.semilogy(drive, gaps, "s--", color="#D55E00", markersize=3, label="Minimum body gap (display)")
        gap_ax.set_ylabel("Minimum body / top-plane gap [mm]", color="#D55E00")
        ax.axvline(drive[index], color="#b6bfc5", linewidth=.7)
        handles, labels = ax.get_legend_handles_labels()
        extra_handles, extra_labels = gap_ax.get_legend_handles_labels()
        ax.legend(handles + extra_handles, labels + extra_labels, fontsize=8, loc="lower left")
        ax.grid(alpha=.2, which="both")
        ax = axes[1, 2]
        ax.axis("off")
        text = (f"Actual accepted state: {phase}\n\n"
                f"Physical mean drive: {drive[index]:.9g} mm\n"
                f"Minus full top reaction: {normal[index]:.10g} N\n"
                f"Full bottom reaction: {record['bottom_force_N']:.10g} N\n"
                f"Bottom solid-body group: {body[index]:.10g} N\n"
                f"Bottom outer-medium group: {outer[index]:.10g} N\n"
                f"Minimum J: {jacobian[index]:.7g}\n"
                f"Minimum displayed body gap: {gaps[index]:.7g} mm\n"
                f"Relative residual: {record['relative_residual']:.3e}\n"
                f"Constraint error: {record['constraint_error_max_mm']:.3e} mm\n"
                f"Newton checks: {record['newton_checks']}\n\n"
                "Length mm; force N; thickness 1 mm.\n"
                "Full reaction includes background medium.\n"
                "Nodal reactions are not contact pressure.\n"
                "This synthetic benchmark is not LF clamping force.\n\n"
                f"{audit_label}\n"
                "Historical HP80 curve is not an audit of new states.\n"
                "Display uses rounded lift + fluctuation.\n"
                "Frames use accepted states only; no interpolation.")
        ax.text(0, 1, text, va="top", fontsize=9, linespacing=1.3)
        fig.canvas.draw()
        frames.append(Image.fromarray(np.asarray(fig.canvas.buffer_rgba())[:, :, :3].copy()))
        if index == len(states) - 1:
            fig.savefig(args.output / "numpy_path.png", dpi=150)
        plt.close(fig)
    durations = [350] * len(frames)
    durations[0], durations[-1] = 800, 1500
    frames[0].save(args.output / "numpy_path.gif", save_all=True, append_images=frames[1:],
                   loop=0, duration=durations, optimize=False)
    metadata = dict(viewer_source=file_metadata(Path(__file__)), model_and_stage_sources=input_files,
                    state_sources=state_files, independent_audit_source=file_metadata(args.audit) if args.audit else None,
                    frames=len(frames), unique_two_array_states=len({r["state_sha256"] for r in records}),
                    displacement_scale=1., fixed_arrow_mm_per_N=arrow_mm_per_N,
                    fixed_displacement_color_max_mm=maximum_u, length_unit="mm", force_unit="N",
                    thickness_mm=1., normal_force_sign="minus full top constraint reaction",
                    full_reaction_includes_background_medium=True, historical_HP_curve="comparison only",
                    new_state_independent_HP_audited=independently_audited,
                    scope="Actual accepted-state display only; no new force, tangent, equilibrium, or HP calculation",
                    images=[file_metadata(args.output / name) for name in ("numpy_path.png", "numpy_path.gif")])
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(dict(output=str(args.output.resolve()), frames=len(frames),
                          final_drive_mm=float(drive[-1]), final_normal_force_N=float(normal[-1]),
                          displacement_scale=1., fixed_arrow_mm_per_N=arrow_mm_per_N,
                          new_state_independent_HP_audited=independently_audited)))


if __name__ == "__main__":
    main()
