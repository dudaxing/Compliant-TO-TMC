"""Display saved C1 mechanics; no constitutive, FE, JAX, or HP evaluation."""
import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
import numpy as np
from PIL import Image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("model", "result", "audit", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    result = json.loads(args.result.read_text(encoding="utf-8"))
    audit = json.loads(args.audit.read_text(encoding="utf-8"))
    steps, audited = result["accepted_steps"], audit["states"]
    with np.load(args.model, allow_pickle=False) as model:
        xy, cells = model["coordinates"].copy(), model["connectivity"].copy()
        solid, fixed = model["solid"].copy(), model["fixed_dofs"].copy()
    if audit["status"] != "pass" or len(steps) != len(audited):
        raise ValueError("Require a matching saved, audited path")
    drive = np.array([s["d"] for s in steps])
    if not np.allclose(drive, [float(s["parameter_s"]) for s in audited], rtol=0, atol=0):
        raise ValueError("Saved production and audit states differ")
    displacement = [np.array(s["u_lift"]) + np.array(s["u_fluctuation"]) for s in steps]
    displacement = [u.reshape(xy.shape) for u in displacement]
    deformed = [xy + u for u in displacement]
    reaction = [np.array(s["support_reaction"]).reshape(xy.shape) for s in steps]
    hp_force = np.array([float(s["measurements"]["normal_force"]) for s in audited])
    prod_force = np.array([-s["group_reactions"]["top"]["constraint_force"] for s in steps])
    body_force = np.array([s["group_reactions"]["bottom_body"]["constraint_force"] for s in steps])
    gaps = np.array([[float(s["measurements"]["body_top_gap_" + k]) for k in ("min", "max")]
                     for s in audited])
    if np.any(gaps <= 0):
        raise ValueError("This log view requires strictly positive saved body gaps")
    nodes = np.unique(fixed // 2)
    maximum_u = max(np.linalg.norm(u, axis=1).max() for u in displacement)
    maximum_r = max(np.linalg.norm(r[nodes], axis=1).max() for r in reaction)
    arrow_mm_per_N = 0.35 / maximum_r if maximum_r else 1.0
    all_xy = np.concatenate([xy] + deformed)
    lower, upper = all_xy.min(axis=0) - 0.45, all_xy.max(axis=0) + 0.45
    args.output.mkdir(parents=True, exist_ok=True)
    frames = []
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})

    def mesh(ax, positions, colors, linewidth=0.35):
        polygons = PolyCollection(positions[cells], facecolors=colors,
                                  edgecolors="#7c8991", linewidths=linewidth)
        ax.add_collection(polygons)
        ax.set(xlim=(lower[0], upper[0]), ylim=(lower[1], upper[1]), xlabel="x [mm]", ylabel="y [mm]")
        ax.set_aspect("equal", adjustable="box")
        return polygons

    for index, (position, u, r) in enumerate(zip(deformed, displacement, reaction)):
        fig, axes = plt.subplots(2, 3, figsize=(15, 8), layout="constrained")
        fig.suptitle(f"Saved C1 TMC baseline | state {index + 1}/{len(steps)} | drive {drive[index]:.6g} mm", fontsize=16)
        ax = axes[0, 0]
        mesh(ax, xy, np.where(solid[:, None], [0.28, 0.36, 0.42, 0.65], [0.85, 0.9, 0.93, 0.35]))
        ax.add_collection(PolyCollection(position[cells[solid]], facecolors="none", edgecolors="#e57821", linewidths=1.3))
        ax.scatter(xy[nodes, 0], xy[nodes, 1], marker="^", s=12, color="#1f2937")
        ax.set_title("Reference solid/medium + actual solid outline\nOrange: deformed; displacement scale = 1")
        ax = axes[0, 1]
        collection = mesh(ax, position, "#dddddd")
        collection.set_array(np.linalg.norm(u, axis=1)[cells].mean(axis=1))
        collection.set_cmap("viridis")
        collection.set_clim(0, maximum_u)
        ax.add_collection(PolyCollection(position[cells[solid]], facecolors="none", edgecolors="#172b4d", linewidths=0.8))
        fig.colorbar(collection, ax=ax, label="Mean nodal |u| per cell [mm]", shrink=0.8)
        ax.set_title("Actual deformed mesh + saved displacement\nFixed color range for all 15 frames")
        ax = axes[0, 2]
        mesh(ax, position, np.where(solid[:, None], [0.50, 0.62, 0.66, 0.65], [0.85, 0.9, 0.93, 0.25]))
        ax.quiver(position[nodes, 0], position[nodes, 1], r[nodes, 0], r[nodes, 1],
                  angles="xy", scale_units="xy", scale=1 / arrow_mm_per_N, color="#c84325", width=0.007)
        ax.set_title(f"Constraint reactions: apparatus on model\nArrow scale: {arrow_mm_per_N:.4g} mm/N (fixed)")
        ax = axes[1, 0]
        ax.plot(drive, prod_force, "-", color="#263b50", label="Production: minus full top reaction")
        ax.plot(drive, hp_force, "o", color="#e57821", markersize=4, label="Saved independent HP80 normal force")
        ax.plot(drive, body_force, "--", color="#58866c", label="Production: bottom body group")
        ax.scatter(drive[index], hp_force[index], s=85, facecolors="none", edgecolors="#e57821", zorder=5)
        ax.axvline(drive[index], color="#aaa", linewidth=0.7)
        ax.set(xlabel="Physical mean drive [mm]", ylabel="Force [N]", title="Saved force-displacement history")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.2)
        ax = axes[1, 1]
        ax.semilogy(drive, gaps[:, 0], "-o", markersize=3, label="HP80 body top gap: minimum")
        ax.semilogy(drive, gaps[:, 1], "--o", markersize=3, label="HP80 body top gap: maximum")
        ax.axvline(drive[index], color="#aaa", linewidth=0.7)
        ax.set(xlabel="Physical mean drive [mm]", ylabel="Gap [mm]", title="Actual saved solid-to-plane gaps (log)",
               ylim=(gaps.min() / 2, gaps.max() * 2))
        ax.legend(fontsize=8)
        ax.grid(alpha=0.2, which="both")
        ax = axes[1, 2]
        ax.axis("off")
        groups = steps[index]["group_reactions"]
        text = (f"Saved values at this state\n\nFull bottom: {groups['bottom']['constraint_force']:.8g} N\n"
                f"Bottom body: {body_force[index]:.8g} N\n"
                f"Bottom outer medium: {groups['bottom_outer']['constraint_force']:.8g} N\n"
                f"HP80 normal force: {hp_force[index]:.8g} N\n"
                f"Body gap range: {gaps[index, 0]:.5g} - {gaps[index, 1]:.5g} mm\n\n"
                "Length: mm; force: N; thickness: 1 mm.\n"
                "Full top/bottom forces include background medium.\n"
                "These are constraint reactions, not contact pressure.\n\n"
                "Historical audited C1 compression benchmark.\n"
                "Not an LF mechanism or new-candidate qualification.\n"
                "Display uses rounded lift + fluctuation; no FE/HP solve.")
        ax.text(0, 1, text, va="top", fontsize=10, linespacing=1.45)
        fig.canvas.draw()
        frames.append(Image.fromarray(np.asarray(fig.canvas.buffer_rgba())[:, :, :3].copy()))
        if index == len(steps) - 1:
            fig.savefig(args.output / "saved_mechanics.png", dpi=150)
        plt.close(fig)
    frames[0].save(args.output / "compression.gif", save_all=True, append_images=frames[1:], loop=0,
                   duration=[800] + [350] * (len(frames) - 2) + [1400], optimize=False)
    repo_root = Path(__file__).resolve().parents[2]
    metadata = {"case": "historical C1 TMC_h025_uniform_r2", "source_sha256": {
        name: {"path": str(getattr(args, name).resolve()),
               "project_relative_path": getattr(args, name).resolve().relative_to(repo_root).as_posix()
               if getattr(args, name).resolve().is_relative_to(repo_root) else None,
               "bytes": getattr(args, name).stat().st_size,
               "sha256": hashlib.sha256(getattr(args, name).read_bytes()).hexdigest()}
        for name in ("model", "result", "audit")}, "frames": len(frames), "nodes": len(xy), "elements": len(cells),
        "deformation_scale": 1.0, "reaction_arrow_mm_per_N": arrow_mm_per_N,
        "length_unit": "mm", "force_unit": "N", "thickness_mm": 1.0,
        "production_constraint_force_sign": "apparatus_on_model", "normal_force_includes_background_medium": True,
        "displacement_display": "rounded sum of stored lift and fluctuation; not scientific state authority",
        "production_vs_hp80_max_abs_normal_force_difference_N": float(np.max(np.abs(prod_force - hp_force))),
        "saved_points": [{"drive_mm": float(d), "production_normal_force_N": float(p), "hp80_normal_force_N": float(h),
                          "body_top_gap_min_mm": float(g[0]), "body_top_gap_max_mm": float(g[1])}
                         for d, p, h, g in zip(drive, prod_force, hp_force, gaps)],
        "scope": "Saved audited C1 baseline display; no constitutive, FE, HP, JAX, or gzip processing"}
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output.resolve()), "frames": len(frames), "final_hp80_force_N": float(hp_force[-1])}))


if __name__ == "__main__":
    main()
