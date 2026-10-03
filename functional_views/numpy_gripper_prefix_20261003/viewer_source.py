"""Render an audited split project prefix from saved ordinary data only.

No HF mechanics, LF, solver or precision-reference module is imported. Actual
deformation and nodal external actions use the modeled half without doubling.
The supplementary magnification is a display transformation, not a new state.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import shutil

import numpy as np


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def arrays(path):
    with np.load(path, allow_pickle=False) as saved:
        return {key: saved[key].copy() for key in saved.files}


def state_hash(state):
    digest = hashlib.sha256(b"split_displacement_v1")
    digest.update(np.asarray([len(state["u_lift"])], dtype="<i8").tobytes())
    for key in ("u_lift", "u_fluctuation"):
        digest.update(np.asarray(state[key], dtype="<f8").tobytes())
    return digest.hexdigest()


def boundary_edges(connectivity):
    """Return material-boundary edges once, including boundaries of holes."""
    counts = {}
    for cell in connectivity:
        for left, right in zip(cell, np.roll(cell, -1)):
            edge = tuple(sorted((int(left), int(right))))
            counts[edge] = counts.get(edge, 0)+1
    return np.asarray([edge for edge, count in counts.items() if count == 1], dtype=int).reshape(-1, 2)


def scalar_check(audited, name):
    check = next((item for item in audited["checks"] if item["name"] == name), None)
    return float(check["value"]) if check is not None and "value" in check else None


def evidence(input_root, audit_root):
    protocol = read(input_root/"protocol.json")
    summary = read(input_root/"summary.json")
    audited = read(audit_root/"summary.json")
    assert summary["status"] == "success" and summary["target_reached"]
    assert audited["status"] == "pass" and audited["new_state_independent_HP_audited"]
    bindings = audited["input_bindings"]
    for binding in bindings:
        assert sha(input_root/binding["path"]) == binding["sha256"], binding["path"]
    model = arrays(input_root/"model.npz")
    rows = summary["states"]
    assert len(rows) == len(audited["states"]) and rows
    states = []
    bound_paths = {binding["path"] for binding in bindings}
    assert {"protocol.json", "summary.json", "model.npz"} <= bound_paths
    for index, (row, check) in enumerate(zip(rows, audited["states"])):
        assert check["index"] == index and check["status"] == "pass"
        path = row["path"]
        assert path in bound_paths
        assert sha(input_root/path) == row["file_sha256"]
        state = arrays(input_root/path)
        assert state_hash(state) == row["state_sha256"] == check["state_sha256"]
        assert np.isfinite(state["J"]).all() and (state["J"] > 0).all()
        states.append(state)
    assert protocol["case_family"] == summary["case_family"] == protocol["task_config"]["case_family"]
    return model, rows, states, audited, bindings, protocol


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--magnification", type=float, default=100.)
    args = parser.parse_args()
    if not np.isfinite(args.magnification) or args.magnification <= 1.:
        parser.error("supplementary magnification must be finite and greater than one")
    model, rows, states, audit, bindings, protocol = evidence(args.input, args.audit)
    coords, conn, solid = [model[key] for key in ("coordinates", "connectivity", "solid")]
    solid = solid.astype(bool)
    b_in, b_out = model["b_in"], model["b_out"]
    family = protocol["case_family"]
    assert family in ("inverter", "gripper")
    output_direction = b_out.reshape(-1, 2).sum(axis=0)
    np.testing.assert_array_equal(output_direction, protocol["region_metadata"]["ports"]["output"]["direction"])
    output_direction_label = {(-1., 0.): "−x", (0., 1.): "+y"}[tuple(output_direction)]
    inlet_dofs = np.flatnonzero(b_in)
    assert len(inlet_dofs) == 3 and np.all(inlet_dofs % 2 == 0), "This viewer expects the canonical three-node x input"
    inlet_nodes, inlet_weights = inlet_dofs//2, b_in[inlet_dofs]
    fixed_nodes = np.unique(model["fixed_dofs"]//2)
    displaced = [coords+(s["u_lift"]+s["u_fluctuation"]).reshape(-1, 2) for s in states]
    magnified = [coords+args.magnification*(s["u_lift"]+s["u_fluctuation"]).reshape(-1, 2) for s in states]
    boundary = boundary_edges(conn[solid])
    force_keys = ("support_reaction", "input_force", "spring_force_on_structure")
    maximum_force = max(float(np.linalg.norm(s[key].reshape(-1, 2), axis=1).max())
                        for s in states for key in force_keys)
    arrow_scale = 4./max(maximum_force, 1e-12)
    j_ranges = {}
    for name, selected in (("solid", solid), ("third_medium", ~solid)):
        if selected.any():
            j_ranges[name] = [min(float(s["J"][selected].min()) for s in states),
                              max(float(s["J"][selected].max()) for s in states)]
    numerical = []
    for index, (row, state, checked) in enumerate(zip(rows, states, audit["states"])):
        u = (state["u_lift"]+state["u_fluctuation"]).reshape(-1, 2)
        q_out, d = float(row["q_out"]), float(row["physical_mean_target_mm"])
        external = sum((state[key] for key in force_keys), np.zeros(len(b_in))).reshape(-1, 2).sum(axis=0)
        numerical.append(dict(index=index, input_mean_target_mm=d, R_input_N=float(row["R_input"]),
            q_in_mm=float(row["q_in"]), q_out_reference_direction_mm=q_out,
            q_out_over_d=None if d == 0. else q_out/d,
            input_node_0_ux_mm=float(u[inlet_nodes[0], 0]),
            input_node_1_ux_mm=float(u[inlet_nodes[1], 0]),
            input_node_2_ux_mm=float(u[inlet_nodes[2], 0]),
            solid_minimum_J=float(state["J"][solid].min()) if solid.any() else None,
            medium_minimum_J=float(state["J"][~solid].min()) if (~solid).any() else None,
            minimum_J=float(state["J"].min()), production_relative_residual=float(row["relative_residual"]),
            production_constraint_residual_mm=float(row["constraint_residual"]),
            independent_HP_relative_residual=scalar_check(checked, "hp80__relative_residual"),
            independent_HP_relative_constraint=scalar_check(checked, "hp80__relative_constraint"),
            independent_HP_relative_force_balance=scalar_check(checked, "hp80__relative_force_balance"),
            output_spring_generalized_force_N=float(row["output_spring_generalized_force"]),
            output_spring_energy_N_mm=float(row["output_spring_energy"]),
            external_balance_x_N=float(external[0]), external_balance_y_N=float(external[1]),
            maximum_displacement_mm=float(np.linalg.norm(u, axis=1).max())))
    args.output.mkdir(parents=True, exist_ok=False)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.animation import PillowWriter
    from matplotlib.collections import LineCollection, PolyCollection
    from matplotlib.colors import LogNorm, Normalize
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    from matplotlib.ticker import ScalarFormatter
    from PIL import Image

    plt.rcParams.update({"font.size": 10, "axes.titlesize": 11, "axes.labelsize": 10})
    palettes = dict(solid="Blues", third_medium="Oranges")
    norms = {}
    for name, (low, high) in j_ranges.items():
        if low == high:
            low, high = low*(1.-1e-6), high*(1.+1e-6)
        norms[name] = LogNorm(low, high) if high/low > 5. else Normalize(low, high)
    def limits(positions):
        all_points = np.concatenate([coords, *positions])
        span = np.ptp(coords, axis=0)
        margin = max(float(span.max())*.08, 2.)
        return (all_points[:, 0].min()-margin, all_points[:, 0].max()+margin), (
                all_points[:, 1].min()-margin, all_points[:, 1].max()+margin)
    actual_limits, magnified_limits = limits(displaced), limits(magnified)
    colors = dict(support_reaction="#266fb1", input_force="#cf4b23", spring_force_on_structure="#8b4ba8")
    labels = dict(support_reaction="support on model", input_force="actuator on model",
                  spring_force_on_structure="output spring on model")

    def draw(axis, index, *, enlarged=False, colorbars=False):
        state = states[index]
        points = magnified[index] if enlarged else displaced[index]
        original = PolyCollection(coords[conn[solid]], facecolors="#b3b3b3", alpha=.18,
                                  edgecolors="none", zorder=0)
        axis.add_collection(original)
        for name, selected in (("third_medium", ~solid), ("solid", solid)):
            if not selected.any():
                continue
            collection = PolyCollection(points[conn[selected]], array=state["J"][selected].mean(axis=1),
                cmap=palettes[name], norm=norms[name], edgecolors="none",
                alpha=.4 if name == "third_medium" else .95, zorder=1 if name == "third_medium" else 2)
            axis.add_collection(collection)
            if colorbars:
                colorbar = axis.figure.colorbar(collection, ax=axis, shrink=.6, pad=.015, fraction=.035)
                colorbar.ax.tick_params(labelsize=7)
                colorbar.set_label(("solid" if name == "solid" else "medium")+" mean J", fontsize=8)
                colorbar.formatter = ScalarFormatter(useOffset=False)
                colorbar.formatter.set_scientific(False)
                colorbar.update_ticks()
        axis.add_collection(LineCollection(coords[boundary], colors="#777777", linewidths=.6,
                                          linestyles="--", zorder=3))
        axis.add_collection(LineCollection(points[boundary], colors="#174e75", linewidths=.7, zorder=4))
        axis.scatter(*points[inlet_nodes].T, color=colors["input_force"], s=16, zorder=6)
        axis.scatter(*points[fixed_nodes].T, marker="s", facecolors="none", edgecolors="#34485e", s=9, linewidths=.35, zorder=5)
        handles = [Patch(facecolor="#5796c1", label="solid"), Patch(facecolor="#eebd87", label="third medium"),
                   Line2D([], [], color="#777777", linestyle="--", label="original solid outline")]
        if not enlarged:
            for key in force_keys:
                force = state[key].reshape(-1, 2)
                selected = np.linalg.norm(force, axis=1) > max(maximum_force*1e-14, 1e-18)
                if selected.any():
                    axis.quiver(*points[selected].T, *(arrow_scale*force[selected]).T, angles="xy",
                                scale_units="xy", scale=1., width=.005, color=colors[key], zorder=7)
                handles.append(Line2D([], [], color=colors[key], linewidth=2, label=labels[key]))
        xlim, ylim = magnified_limits if enlarged else actual_limits
        axis.set(xlim=xlim, ylim=ylim, aspect="equal", xlabel="x [mm]", ylabel="y [mm]",
            title=(f"SUPPLEMENT: displacement ×{args.magnification:g}; no force arrows\nJ colors remain the actual accepted-state values" if enlarged else
                   f"Actual deformation ×1; input mean {numerical[index]['input_mean_target_mm']:.5g} mm"))
        axis.legend(handles=handles, loc="lower left", fontsize=7, ncol=2, framealpha=.88)

    figure, axes = plt.subplots(2, 3, figsize=(20, 11.5), constrained_layout=True)
    last = len(rows)-1
    draw(axes[0, 0], last, colorbars=True)
    draw(axes[0, 1], last, enlarged=True)
    levels = [r["input_mean_target_mm"] for r in numerical]
    axes[0, 2].plot(levels, [r["R_input_N"] for r in numerical], "o-", color="#cf4b23", label="input actuator R")
    axes[0, 2].plot(levels, [r["output_spring_generalized_force_N"] for r in numerical], "s--", color="#8b4ba8", label="output spring")
    axes[0, 2].set(xlabel="prescribed input weighted mean [mm]", ylabel="generalized force [N]",
                   title="Modeled lower half; fresh saved-state HP audit PASS")
    axes[0, 2].grid(alpha=.25); axes[0, 2].legend(fontsize=8)
    axes[1, 0].plot(levels, [r["q_out_reference_direction_mm"] for r in numerical], "o-", label="q_out = b_out·u", color="#176a80")
    ratio_axis = axes[1, 0].twinx()
    nonzero = [r for r in numerical if r["input_mean_target_mm"] != 0.]
    ratio_axis.plot([r["input_mean_target_mm"] for r in nonzero], [r["q_out_over_d"] for r in nonzero], "s--", color="#8b4ba8", label="q_out / d; zero excluded")
    ratio_axis.set_ylabel("dimensionless q_out / d", color="#8b4ba8")
    axes[1, 0].set(xlabel="prescribed input weighted mean [mm]", ylabel="output reference mean [mm]",
                   title=f"Output sign follows saved b_out ({family} reference: {output_direction_label})")
    handles, text = axes[1, 0].get_legend_handles_labels()
    handles2, text2 = ratio_axis.get_legend_handles_labels()
    axes[1, 0].legend(handles+handles2, text+text2, fontsize=8); axes[1, 0].grid(alpha=.25)
    for j, (node, weight) in enumerate(zip(inlet_nodes, inlet_weights)):
        axes[1, 1].plot(levels, [r[f"input_node_{j}_ux_mm"] for r in numerical], "o-",
                        label=f"node {node}, y={coords[node,1]:g} mm, weight={weight:g}")
    axes[1, 1].plot(levels, [r["q_in_mm"] for r in numerical], "k:", linewidth=2, label="weighted mean")
    axes[1, 1].set(xlabel="prescribed input weighted mean [mm]", ylabel="individual input ux [mm]",
                   title="Three input nodes remain free to move differently")
    axes[1, 1].grid(alpha=.25); axes[1, 1].legend(fontsize=8)
    axes[1, 2].axis("off")
    final = numerical[-1]
    info = ["FINAL STATE — original modeled lower half",
            f"d = {final['input_mean_target_mm']:.9g} mm; R = {final['R_input_N']:.9g} N",
            f"q_out = {final['q_out_reference_direction_mm']:.9g} mm; q_out/d = {final['q_out_over_d']:.9g}",
            f"solid min J = {final['solid_minimum_J']:.10g}",
            f"medium min J = {final['medium_minimum_J']:.10g}",
            f"production residual / S_F = {final['production_relative_residual']:.3e}",
            f"HP80 residual / S_F = {final['independent_HP_relative_residual']:.3e}",
            f"HP80 relative constraint = {final['independent_HP_relative_constraint']:.3e}",
            f"HP80 relative force balance = {final['independent_HP_relative_force_balance']:.3e}",
            f"Σ external Fx,Fy = {final['external_balance_x_N']:.3e}, {final['external_balance_y_N']:.3e} N",
            "", "d [mm]       production residual      actual min J"]
    info += [f"{r['input_mean_target_mm']:8.5g}     {r['production_relative_residual']:.3e}           {r['minimum_J']:.8g}" for r in numerical]
    info += ["", "J is dimensionless det(F), not contact pressure.",
             "No contact/clamping or full-stroke qualification.",
             "No force/energy doubling; no interpolated states."]
    axes[1, 2].text(0., .98, "\n".join(info), transform=axes[1, 2].transAxes, va="top", fontsize=9, linespacing=1.45)
    figure.suptitle(f"Canonical {family} prefix | split average-port control | force arrows {arrow_scale:.6g} mm/N, constant over all states\n"
                   "Main geometry ×1; magnified geometry is explicitly supplemental. Solid and third-medium J use separate color ranges.", fontsize=13)
    figure.savefig(args.output/"split_project_path.png", dpi=180)
    plt.close(figure)
    frame, frame_axes = plt.subplots(1, 2, figsize=(12, 5), constrained_layout=True)
    writer = PillowWriter(fps=1)
    with writer.saving(frame, str(args.output/"split_project_path.gif"), dpi=140):
        for index, row in enumerate(numerical):
            for axis in frame_axes:
                axis.clear()
            draw(frame_axes[0], index)
            frame_axes[1].axis("off")
            frame_axes[1].text(.02, .9, "\n".join((f"{family.capitalize()}: accepted state {index+1}/{len(rows)} — actual ×1",
                f"input mean d = {row['input_mean_target_mm']:.8g} mm", f"input actuator R = {row['R_input_N']:.8g} N",
                f"output q_out ({output_direction_label}) = {row['q_out_reference_direction_mm']:.8g} mm",
                f"solid min J = {row['solid_minimum_J']:.9g}", f"medium min J = {row['medium_minimum_J']:.9g}",
                f"production residual = {row['production_relative_residual']:.3e}",
                "Saved-state independent HP audit PASS", "", "Modeled lower half; no force doubling.",
                "No contact/clamping claim. J is not pressure.", "No interpolation between accepted states.")),
                transform=frame_axes[1].transAxes, va="top", fontsize=11, linespacing=1.5)
            frame.suptitle(f"Actual accepted deformation ×1 | constant force arrows {arrow_scale:.6g} mm/N", fontsize=12)
            writer.grab_frame()
    plt.close(frame)
    with (args.output/"numeric_states.csv").open("w", encoding="utf-8", newline="") as stream:
        output = csv.DictWriter(stream, fieldnames=list(numerical[0]))
        output.writeheader(); output.writerows(numerical)
    shutil.copyfile(Path(__file__), args.output/"viewer_source.py")
    artifacts = []
    for name in ("split_project_path.png", "split_project_path.gif", "numeric_states.csv", "viewer_source.py"):
        path = args.output/name
        item = dict(path=name, sha256=sha(path), bytes=path.stat().st_size)
        if path.suffix in (".png", ".gif"):
            with Image.open(path) as media:
                item.update(width=media.width, height=media.height, frames=getattr(media, "n_frames", 1))
        artifacts.append(item)
    metadata = dict(schema_version="split-project-view-1.0", rendering_only=True,
        case_family=family, output_reference_direction=output_direction.tolist(),
        output_reference_direction_label=output_direction_label,
        force_kernel_calls=0, solver_calls=0, fresh_HP_calls=0,
        accepted_state_count=len(rows), deformation_scale_main=1.,
        supplementary_deformation_scale=args.magnification, supplementary_force_arrows=False,
        force_arrow_mm_per_N=arrow_scale, maximum_nodal_force_N=maximum_force,
        arrow_display_threshold_N=max(maximum_force*1e-14, 1e-18),
        arrow_scale_scope="Common maximum over every accepted state and all three external force fields",
        actual_J_ranges_over_all_states=j_ranges, J_display="Element quadrature mean; region minimum J in numeric table is over all quadrature points",
        solid_cmap=palettes["solid"], third_medium_cmap=palettes["third_medium"],
        input_nodes=inlet_nodes.tolist(), input_weights=inlet_weights.tolist(),
        output_nonzero_dofs=np.flatnonzero(b_out).tolist(), output_weights=b_out[b_out != 0].tolist(),
        protocol_sha256=sha(args.input/"protocol.json"),
        model_sha256=sha(args.input/"model.npz"), solve_summary_sha256=sha(args.input/"summary.json"),
        audit_summary_sha256=sha(args.audit/"summary.json"), viewer_source_sha256=sha(Path(__file__)),
        input_bindings=bindings, artifacts=artifacts, numeric_states=numerical, final_numbers=final,
        units=dict(length="mm", force="N", energy="N mm", J="dimensionless"),
        limitations="Audited small input prefix, original modeled lower half; no contact/clamping, no LF execution, no doubling, no interpolation")
    (args.output/"metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps(dict(output=str(args.output), accepted_frames=len(rows), final_numbers=final)))


if __name__ == "__main__":
    main()
