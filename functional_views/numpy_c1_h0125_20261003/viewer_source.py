"""Show accepted NumPy C1 states and the saved historical HP curve; no solve."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.colors import LogNorm
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
    parser.add_argument("--comparison", type=Path, help="Previous NumPy path root; saved curves are physical comparisons only")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    records, states, phases, summaries = [], [], [], []
    input_files, state_files = [], []
    displayed_files, model_files = [], []
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
        displayed_files.extend(directory / name for name in ("summary.json", "model.npz"))
        model_files.append(directory / "model.npz")
        for record in summary["states"]:
            state = load_npz(directory / record["path"])
            if state_sha256(state) != record["state_sha256"]:
                raise ValueError("Displayed two-array state differs from its saved identity")
            records.append(record)
            states.append(state)
            phases.append(summary["phase"])
            state_files.append(dict(phase=summary["phase"], state_sha256=record["state_sha256"],
                                   **file_metadata(directory / record["path"])))
            displayed_files.append(directory / record["path"])
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
    component_normal = {name: np.array([-model["group_top"] @ s[key] for s in states])
                        for name, key in (("material", "material_internal_force"),
                                          ("regularization", "regularization_internal_force"))}
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
    body_top = np.flatnonzero((xy[:, 1] == 1.) & (xy[:, 0] >= 0.) & (xy[:, 0] <= 2.))
    body_top = body_top[np.argsort(xy[body_top, 0])]
    medium_cells = (~solid) & (xy[cells].mean(axis=1)[:, 1] > 1.)
    medium_j = [np.min(s["J"], axis=1) for s in states]
    j_norm = LogNorm(vmin=min(float(j[medium_cells].min()) for j in medium_j),
                     vmax=max(1., max(float(j[medium_cells].max()) for j in medium_j)))
    grid_x = np.unique(xy[:, 0])
    mesh_h = float(np.min(np.diff(grid_x)))
    comparison_curve = []
    comparison_sources = []
    comparison_label = None
    if args.comparison:
        comparison_model = load_npz(args.comparison / "approach/model.npz")
        comparison_h = float(np.min(np.diff(np.unique(comparison_model["coordinates"][:, 0]))))
        comparison_label = f"Previous NumPy h={comparison_h:g} mm (comparison only)"
        comparison_sources.append(file_metadata(args.comparison / "approach/model.npz"))
        for phase in ("approach", "compression"):
            path = args.comparison / phase / "summary.json"
            comparison_curve.extend(json.loads(path.read_text(encoding="utf-8"))["states"])
            comparison_sources.append(file_metadata(path))
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
        # The state identity binds lift and fluctuation. File hashes also bind the
        # displayed forces, J arrays, model and stage summaries to this audit.
        root = Path(__file__).resolve().parents[2]
        bound = {(Path(row["path"]) if Path(row["path"]).is_absolute() else root / row["path"]).resolve(): row["sha256"]
                 for row in audit["inputs_and_sources"]}
        for path in displayed_files:
            if bound.get(path.resolve()) != file_metadata(path)["sha256"]:
                if path in model_files:
                    # The first coarse audit bound its complete input model,
                    # rather than the smaller visualization model. Compare every
                    # displayed model array with that unchanged audited copy.
                    audited_model = args.audit.parent / "inputs/model.npz"
                    if file_metadata(audited_model)["sha256"] not in bound.values():
                        raise ValueError("Audited model copy differs from its saved source")
                    full_model, shown_model = load_npz(audited_model), load_npz(path)
                    for key in shown_model:
                        np.testing.assert_array_equal(shown_model[key], full_model[key])
                    continue
                raise ValueError("Displayed model, summary or state file is not bound to this audit")
        independently_audited = True
    audit_label = ("New states passed independent HP80/120 audit." if independently_audited else
                   "New states are NOT independently HP audited.")
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    args.output.mkdir(parents=True, exist_ok=False)
    frames = []

    def mesh(ax, position, colors):
        collection = PolyCollection(position[cells], facecolors=colors,
                                    edgecolors="#87939c", linewidths=.35)
        ax.add_collection(collection)
        ax.axhline(top_plane, color="#52616b", linewidth=.8, linestyle="--")
        ax.set(xlim=(lo[0], hi[0]), ylim=(lo[1], hi[1]), xlabel="x [mm]", ylabel="y [mm]")
        ax.set_aspect("equal", adjustable="box")
        return collection

    def medium_zoom(ax, position, index):
        """Actual coordinates, independently scaled axes to make the gap visible."""
        local = position.copy()
        local[:, 1] -= top_plane
        collection = PolyCollection(local[cells[medium_cells]], edgecolors="#87939c", linewidths=.45,
                                    cmap="magma_r", norm=j_norm)
        collection.set_array(medium_j[index][medium_cells])
        ax.add_collection(collection)
        ax.plot(local[body_top, 0], local[body_top, 1], ".-", color="#009E73", linewidth=1.3,
                markersize=3, label="Deformed solid boundary")
        ax.axhline(0., color="#263b50", linewidth=1.2, label="Fixed top plane")
        visible_gap = top_plane - float(position[body_top, 1].min())
        body_x = local[body_top, 0]
        x_padding = .01 * float(np.ptp(body_x))
        ax.set(xlim=(float(body_x.min()) - x_padding, float(body_x.max()) + x_padding),
               ylim=(-1.08 * visible_gap, .12 * visible_gap),
               xlabel="x [mm]", ylabel="y minus fixed top plane [mm]",
               title=f"Thin-medium detail: minimum gap {gaps[index]:.4g} mm\nActual coordinates; different x / y display scales")
        ax.ticklabel_format(axis="y", style="sci", scilimits=(-3, 3), useOffset=False)
        ax.legend(fontsize=7, loc="lower right")
        return collection

    for index, (position, u, reaction, record, phase) in enumerate(zip(positions, displacement, reactions, records, phases)):
        fig, axes = plt.subplots(2, 4, figsize=(20, 9), layout="constrained")
        fig.suptitle(f"New NumPy C1 equilibrium | h={mesh_h:g} mm | accepted state {index + 1}/{len(states)} | {phase} | drive {drive[index]:.8g} mm", fontsize=15)
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
        collection = medium_zoom(axes[0, 3], position, index)
        fig.colorbar(collection, ax=axes[0, 3], label="Minimum J per medium cell", shrink=.7)
        ax = axes[1, 0]
        ax.plot(baseline_drive, baseline_force, "x--", color="#63727c", markersize=4, linewidth=1,
                label="Historical HP80 path (comparison only)")
        ax.plot(drive, normal, "o-", color="#0072B2", markersize=3, label="New: minus full top reaction")
        ax.plot(drive, body, "s--", color="#009E73", markersize=3, label="New: bottom body support nodes*")
        ax.plot(drive, outer, ".--", color="#D55E00", markersize=4, label="New: bottom outer support nodes*")
        if comparison_curve:
            ax.plot([r["physical_drive_mm"] for r in comparison_curve],
                    [r["normal_force_N"] for r in comparison_curve], ":", color="#CC79A7", linewidth=1.3,
                    label=comparison_label)
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
        ax.plot(drive, normal, "o-", color="#0072B2", markersize=3, label="Total")
        ax.plot(drive, component_normal["material"], "s--", color="#009E73", markersize=3, label="Material")
        ax.plot(drive, component_normal["regularization"], ".--", color="#D55E00", markersize=4, label="Regularization")
        ax.axvline(drive[index], color="#b6bfc5", linewidth=.7)
        ax.set_yscale("symlog", linthresh=1e-3)
        ax.set(xlabel="Physical mean drive [mm]", ylabel="Minus full top reaction [N]",
               title="Weak-force components at the full top boundary\nBoth components include the background medium")
        ax.legend(fontsize=8)
        ax.grid(alpha=.2, which="both")
        ax = axes[1, 3]
        ax.axis("off")
        text = (f"Actual accepted state: {phase}\n\n"
                f"Physical mean drive: {drive[index]:.9g} mm\n"
                f"Minus full top reaction: {normal[index]:.10g} N\n"
                f"Full bottom reaction: {record['bottom_force_N']:.10g} N\n"
                f"Bottom body support-node group: {body[index]:.10g} N\n"
                f"Bottom outer support-node group: {outer[index]:.10g} N\n"
                f"Minimum J: {jacobian[index]:.7g}\n"
                f"Minimum displayed body gap: {gaps[index]:.7g} mm\n"
                f"Relative residual: {record['relative_residual']:.3e}\n"
                f"Constraint error: {record['constraint_error_max_mm']:.3e} mm\n"
                f"Newton checks: {record['newton_checks']}\n\n"
                "Length mm; force N; thickness 1 mm.\n"
                "Full reaction includes background medium.\n"
                "* Shared interface nodes split equally between groups.\n"
                "Groups are not contact / material partitions.\n"
                "Nodal reactions are not contact pressure.\n"
                "This synthetic benchmark is not LF clamping force.\n\n"
                f"{audit_label}\n"
                "Historical HP80 curve is not an audit of new states.\n"
                "Display uses rounded lift + fluctuation.\n"
                "Frames use accepted states only; no interpolation.")
        ax.text(0, 1, text, va="top", fontsize=8.5, linespacing=1.3)
        fig.canvas.draw()
        frames.append(Image.fromarray(np.asarray(fig.canvas.buffer_rgba())[:, :, :3].copy()))
        if index == len(states) - 1:
            fig.savefig(args.output / "numpy_path.png", dpi=150)
        plt.close(fig)
    durations = [350] * len(frames)
    durations[0], durations[-1] = 800, 1500
    frames[0].save(args.output / "numpy_path.gif", save_all=True, append_images=frames[1:],
                   loop=0, duration=durations, optimize=False)
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5), layout="constrained")
    collection = medium_zoom(axes[0], positions[-1], len(states) - 1)
    fig.colorbar(collection, ax=axes[0], label="Minimum J per medium cell", shrink=.8)
    local_gap = top_plane - positions[-1][body_top, 1]
    axes[1].plot(positions[-1][body_top, 0], local_gap, "o-", color="#009E73", markersize=4)
    axes[1].set(xlabel="Deformed body boundary x [mm]", ylabel="Displayed body / top-plane gap [mm]",
                title="Actual terminal body gap at mesh nodes\nRounded lift + fluctuation; no contact-pressure inference")
    axes[1].ticklabel_format(axis="y", style="sci", scilimits=(-3, 3), useOffset=False)
    axes[1].grid(alpha=.2)
    fig.suptitle(f"NumPy C1 h={mesh_h:g} mm | drive {drive[-1]:.8g} mm | displacement scale = 1\n{audit_label}")
    fig.savefig(args.output / "numpy_medium_zoom.png", dpi=180)
    plt.close(fig)
    shutil.copyfile(Path(__file__), args.output / "viewer_source.py")
    metadata = dict(viewer_source=file_metadata(Path(__file__)), model_and_stage_sources=input_files,
                    frozen_viewer_source=file_metadata(args.output / "viewer_source.py"),
                    state_sources=state_files, independent_audit_source=file_metadata(args.audit) if args.audit else None,
                    frames=len(frames), unique_two_array_states=len({r["state_sha256"] for r in records}),
                    displacement_scale=1., fixed_arrow_mm_per_N=arrow_mm_per_N,
                    fixed_displacement_color_max_mm=maximum_u, length_unit="mm", force_unit="N",
                    thickness_mm=1., normal_force_sign="minus full top constraint reaction",
                    mesh_h_mm=mesh_h, thin_medium_axes_isometric=False,
                    thin_medium_coordinates="actual deformed x; actual y minus fixed top-plane height",
                    previous_curve_sources=comparison_sources,
                    final_state=dict(physical_drive_mm=float(drive[-1]), full_top_normal_force_N=float(normal[-1]),
                                     material_top_normal_force_N=float(component_normal["material"][-1]),
                                     regularization_top_normal_force_N=float(component_normal["regularization"][-1]),
                                     minimum_J=float(jacobian[-1]), minimum_displayed_body_gap_mm=float(gaps[-1])),
                    full_reaction_includes_background_medium=True, historical_HP_curve="comparison only",
                    bottom_groups_semantics="Boundary support-node bookkeeping; shared interface nodes split equally; not contact/material partitions",
                    new_state_independent_HP_audited=independently_audited,
                    scope="Actual accepted-state display only; no new force, tangent, equilibrium, or HP calculation",
                    images=[file_metadata(args.output / name) for name in ("numpy_path.png", "numpy_path.gif", "numpy_medium_zoom.png")])
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(dict(output=str(args.output.resolve()), frames=len(frames),
                          final_drive_mm=float(drive[-1]), final_normal_force_N=float(normal[-1]),
                          displacement_scale=1., fixed_arrow_mm_per_N=arrow_mm_per_N,
                          new_state_independent_HP_audited=independently_audited)))


if __name__ == "__main__":
    main()
