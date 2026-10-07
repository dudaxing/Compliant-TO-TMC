def render(model, metadata, states, rows, input_dofs, output, magnification):
    coordinates, connectivity, solid = (model[key] for key in ("coordinates", "connectivity", "solid"))
    positions = [coordinates+(s["state"]["lift"]+s["state"]["fluctuation"]).reshape(-1, 2) for s in states]
    enlarged = [coordinates+magnification*(p-coordinates) for p in positions]
    boundary = boundary_edges(connectivity[solid])
    nodes = np.unique(model["fixed_dofs"]//2)
    support_nodes = np.asarray(metadata["region_metadata"]["support"]["attached_nodes"], dtype=int)
    sample_support = np.union1d(support_nodes, np.setdiff1d(nodes, support_nodes)[::3])
    port_nodes = input_dofs//2
    force_maximum = max(float(np.linalg.norm(s["forces"][key].reshape(-1, 2), axis=1).max())
                        for s in states for key in FORCE_KEYS)
    force_scale = max(force_maximum, 1e-30)/4.
    j_ranges = {name: [min(float(s["forces"]["J"][selection].min()) for s in states),
                       max(float(s["forces"]["J"][selection].max()) for s in states)]
                for name, selection in (("solid", solid), ("medium", ~solid))}
    normalizations = {name: Normalize(low if low != high else low-1e-6,
                                    high if low != high else high+1e-6)
                      for name, (low, high) in j_ranges.items()}
    all_points = np.concatenate([coordinates, *positions, *enlarged])
    width = float(np.ptp(coordinates[:, 0]))
    margin = .08*width
    actual_limits = ((coordinates[:, 0].min()-margin, coordinates[:, 0].max()+margin),
                     (coordinates[:, 1].min()-margin, coordinates[:, 1].max()+margin))
    zoom_limits = ((all_points[:, 0].min()-margin, all_points[:, 0].max()+margin),
                   (all_points[:, 1].min()-margin, all_points[:, 1].max()+margin))

    def draw(ax, index, *, zoom=False, colorbars=False):
        positions_now = enlarged[index] if zoom else positions[index]
        ax.add_collection(PolyCollection(coordinates[connectivity[solid]], facecolors="#bdbdbd",
                                         alpha=.2, edgecolors="none", zorder=0))
        for name, selected, palette, alpha in (("medium", ~solid, "Oranges", .4), ("solid", solid, "Blues", .95)):
            collection = PolyCollection(positions_now[connectivity[selected]],
                array=states[index]["forces"]["J"][selected].mean(axis=1), cmap=palette,
                norm=normalizations[name], alpha=alpha, edgecolors="none", zorder=1 if name == "medium" else 2)
            ax.add_collection(collection)
            if colorbars:
                bar = ax.figure.colorbar(collection, ax=ax, shrink=.7, pad=.015, fraction=.04)
                bar.set_label(name+" mean J", fontsize=8)
                bar.ax.tick_params(labelsize=7)
                bar.formatter = ScalarFormatter(useOffset=False)
                bar.formatter.set_scientific(False)
                bar.update_ticks()
        ax.add_collection(LineCollection(coordinates[boundary], colors="#888888", linewidths=.6,
                                        linestyles="--", zorder=3))
        ax.add_collection(LineCollection(positions_now[boundary], colors="#174e75", linewidths=.7, zorder=4))
        ax.scatter(*positions_now[port_nodes].T, color=FORCE_COLORS[1], s=16, zorder=5)
        ax.scatter(*positions_now[nodes].T, marker="s", facecolors="none", edgecolors="#34485e", s=8, linewidths=.3, zorder=5)
        handles = [Line2D([], [], color="#888888", linestyle="--", label="source solid outline"),
                   Line2D([], [], color="#174e75", label="accepted solid outline")]
        if not zoom:
            for key, color, label in zip(FORCE_KEYS, FORCE_COLORS,
                    ("constraint reactions: support all; other stride 3", "input actuator on model", "output spring (zero)")):
                force = states[index]["forces"][key].reshape(-1, 2)
                selected = sample_support if key == "support_reaction" else np.flatnonzero(np.any(force != 0., axis=1))
                ax.quiver(*positions_now[selected].T, *force[selected].T, angles="xy", scale_units="xy",
                          scale=force_scale, color=color, width=.004, minlength=0., zorder=6)
                handles.append(Line2D([], [], color=color, label=label))
        xlim, ylim = zoom_limits if zoom else actual_limits
        ax.set(xlim=xlim, ylim=ylim, aspect="equal", xlabel="x [mm]", ylabel="y [mm]")
        ax.set_title((f"SUPPLEMENT: displacement ×{magnification:g}; no force arrows" if zoom else
                      "Actual accepted deformation ×1"), fontsize=10)
        ax.legend(handles=handles, loc="lower left", fontsize=7, framealpha=1.)

    fig, axes = plt.subplots(2, 3, figsize=(18, 10.5), layout="constrained")
    final = len(states)-1
    draw(axes[0, 0], final, colorbars=True)
    draw(axes[0, 1], final, zoom=True)
    d = np.asarray([r["target_mm"] for r in rows])*1000.
    axes[0, 2].plot(d, [r["R_input_N"] for r in rows], "o-", color=FORCE_COLORS[1], label="input multiplier R")
    output_axis = axes[0, 2].twinx()
    output_axis.plot(d, [1000*r["q_out_mm"] for r in rows], "s--", color="#176a80", label="output reference mean +y")
    axes[0, 2].set(xlabel="input weighted mean target [µm]", ylabel="input actuator R [N]", title="TEST small prefix: force and free-output mean")
    output_axis.set_ylabel("q_out (+y) [µm]", color="#176a80")
    handles, labels = axes[0, 2].get_legend_handles_labels()
    other, other_labels = output_axis.get_legend_handles_labels()
    axes[0, 2].legend(handles+other, labels+other_labels, fontsize=8)
    axes[0, 2].grid(alpha=.25)
    for j, dof in enumerate(input_dofs):
        axes[1, 0].plot(d, [1000*r[f"input_node_{j}_ux_mm"] for r in rows], "o-",
            label=f"node {dof//2}, y={coordinates[dof//2,1]:g} mm, weight={model['b_in'][dof]:g}")
    axes[1, 0].plot(d, [1000*r["q_in_mm"] for r in rows], "k:", linewidth=2., label="actual weighted mean")
    axes[1, 0].set(xlabel="input weighted mean target [µm]", ylabel="actual input ux [µm]", title="Individual input nodes remain free to differ")
    axes[1, 0].legend(fontsize=8); axes[1, 0].grid(alpha=.25)
    axes[1, 1].plot(d, [r["minimum_J"] for r in rows], "o-", color="#176a80", label="min J over all quadrature points")
    errors_axis = axes[1, 1].twinx()
    for key, label, color in (("relative_residual", "free-force residual", "#b84b23"),
                              ("relative_global_force_balance", "external force balance", "#8856a7")):
        values = np.asarray([r[key] for r in rows])
        nonzero = values > 0.
        errors_axis.semilogy(d[nonzero], values[nonzero], "s--", color=color, label=label)
    axes[1, 1].set(xlabel="input weighted mean target [µm]", ylabel="actual min J, dimensionless", title="Positive J and convergence diagnostics; zero errors omitted")
    axes[1, 1].yaxis.set_major_formatter(ScalarFormatter(useOffset=False))
    errors_axis.set_ylabel("normalized error, log")
    handles, labels = axes[1, 1].get_legend_handles_labels()
    other, other_labels = errors_axis.get_legend_handles_labels()
    axes[1, 1].legend(handles+other, labels+other_labels, fontsize=8); axes[1, 1].grid(alpha=.25)
    last = rows[-1]
    axes[1, 2].axis("off")
    lines = ["FINAL ACCEPTED TEST STATE", f"d = {last['target_mm']:.9g} mm; R = {last['R_input_N']:.9g} N",
        f"q_in = {last['q_in_mm']:.9g} mm; q_out (+y) = {last['q_out_mm']:.9g} mm",
        f"solid min J = {last['solid_minimum_J']:.10g}", f"medium min J = {last['medium_minimum_J']:.10g}",
        f"free-force relative residual = {last['relative_residual']:.3e}",
        f"independent HP relative residual = {last['hp_relative_residual']:.3e}",
        f"HP relative mean/balance = {last['hp_relative_constraint']:.3e}, {last['hp_relative_force_balance']:.3e}",
        f"mean constraint residual = {last['constraint_residual_mm']:.3e} mm",
        f"relative external balance = {last['relative_global_force_balance']:.3e}",
        f"external ΣFx,ΣFy = {last['balance_x_N']:.3e}, {last['balance_y_N']:.3e} N", "",
        "Production converged + saved-state independent audit PASS.",
        f"All {len(connectivity)} element J colors use actual accepted values.",
        "Color: quadrature mean; numeric min: all quadrature points.",
        "J = det(F), dimensionless; it is not pressure.", "",
        "Native coarse gripper; original lower half, free output.",
        "No workpiece/contact/clamping or full-stroke claim.",
        "No half-model doubling; no interpolated states."]
    axes[1, 2].text(0., 1., "\n".join(lines), transform=axes[1, 2].transAxes, va="top", fontsize=9,
                       linespacing=1.5, bbox=dict(facecolor="white", edgecolor="none", pad=3))
    fig.suptitle(f"Native average-input TEST | main geometry ×1; supplementary displacement ×{magnification:g}\n"
        f"Common external-force arrow scale: {force_maximum:.9g} N = 4 display mm, fixed over the accepted path", fontsize=12)
    fig.savefig(output/"native_mean_path.png", dpi=160)
    plt.close(fig)
    frame, frame_axes = plt.subplots(1, 2, figsize=(12, 5.5), layout="constrained")
    writer = PillowWriter(fps=1)
    with writer.saving(frame, str(output/"native_mean_path.gif"), dpi=140):
        for index, row in enumerate(rows):
            for ax in frame_axes: ax.clear()
            draw(frame_axes[0], index)
            draw(frame_axes[1], index, zoom=True)
            frame.suptitle(f"Actual accepted state {index+1}/{len(rows)}; d={row['target_mm']:.9g} mm; "
                f"R={row['R_input_N']:.9g} N; q_out (+y)={row['q_out_mm']:.9g} mm\n"
                "Saved-state independent audit PASS. No interpolation; J is not pressure.", fontsize=11)
            writer.grab_frame()
    plt.close(frame)
    return dict(geometry_scale=1., supplementary_displacement_scale=magnification,
        supplementary_force_arrows=False, force_arrow_scale_N_per_display_mm=force_scale,
        maximum_nodal_external_force_N=force_maximum, maximum_arrow_display_mm=4.,
        force_scale_shared_over_all_states_and_components=True, support_arrow_sampling="All attached support nodes; other fixed nodes at stride 3",
        support_arrow_nodes=sample_support.tolist(), input_arrow_nodes=port_nodes.tolist(),
        all_element_J_colored=True, J_display="Element quadrature mean; min J is over all quadrature points",
        actual_J_ranges=j_ranges, actual_frame_count=len(rows), interpolated_frames=0)
