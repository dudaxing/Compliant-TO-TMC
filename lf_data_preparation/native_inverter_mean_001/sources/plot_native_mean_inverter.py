"""Render saved native mean-control evidence with frozen source provenance.

This reader supports the two canonical coarse families. Historical sources
are verified in their production/audit capsules; current source drift is
reported separately. No mechanics, solver or precision reference is imported.
"""
from __future__ import annotations

import argparse
import csv
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection, PolyCollection
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D
from matplotlib.ticker import ScalarFormatter
import numpy as np
from PIL import Image

ROOT = next(p for p in Path(__file__).resolve().parents if (p/"hf_repo/src/hf_eval/data.py").is_file())
DATA_SHA = "ac922927c343172760a032c3b16c16f265e75cf0e8c50e091b23b155aaa69812"
FORCES = ("support_reaction", "input_force", "spring_force_on_structure")
COLORS = ("#216a9b", "#b84b23", "#8856a7")


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def archive(path, declaration):
    require(digest(path) == declaration["sha256"], path.name+": saved SHA differs")
    with np.load(path, allow_pickle=False) as saved:
        values = {key: saved[key].copy() for key in saved.files}
    require(set(values) == set(declaration["fields"]), path.name+": fields differ")
    for name, array in values.items():
        actual = dict(dtype=array.dtype.name, shape=list(array.shape), sha256=sha256(array.tobytes(order="C")).hexdigest())
        require(actual == declaration["fields"][name], path.name+": "+name+" differs")
    return values


def frozen_data(path):
    require(digest(path) == DATA_SHA, "Frozen pure data helper differs")
    spec = importlib.util.spec_from_file_location("_native_mean_view_capsule_data", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def bind_saved_records(record, directory, files):
    if isinstance(record, dict):
        if "path" in record and "sha256" in record:
            path = directory/record["path"]
            require(digest(path) == record["sha256"], "Saved audit payload SHA differs: "+record["path"])
            files[path.relative_to(ROOT).as_posix()] = record["sha256"]
        for value in record.values():
            bind_saved_records(value, directory, files)
    elif isinstance(record, list):
        for value in record:
            bind_saved_records(value, directory, files)


def load_saved(stage):
    directory, audit_root = stage/"result", stage/"audit"
    result, audit, receipt = read(directory/"result.json"), read(audit_root/"summary.json"), read(stage/"execution_receipt.json")
    sources = audit["source_bindings"]
    require(receipt["status"] == audit["status"] == "pass" and receipt["sources"] == sources,
            "Production/audit source closure differs")
    files, current = {}, {}
    for logical, expected in sources.items():
        for capsule in (stage/"sources"/Path(logical).name, audit_root/"sources"/Path(logical).name):
            require(digest(capsule) == expected, logical+": frozen source differs")
            files[capsule.relative_to(ROOT).as_posix()] = expected
        live = ROOT/logical
        actual = digest(live) if live.is_file() else None
        current[logical] = dict(historical_sha256=expected, current_sha256=actual, matches_historical=actual == expected)
    for relative, expected in audit["input_bindings"].items():
        if relative in sources:
            require(expected == sources[relative], relative+": historical source declaration differs")
        else:
            require(digest(ROOT/relative) == expected, relative+": saved data/reference binding differs")
            files[relative] = expected
    helper = audit_root/"sources/data.py"
    require(sources["hf_repo/src/hf_eval/data.py"] == DATA_SHA, "Historical data helper pin differs")
    data = frozen_data(helper)

    def identity(record):
        require(data.canonical_hash({k: v for k, v in record.items() if k != "descriptor_sha256"})
                == record["descriptor_sha256"], "Saved descriptor identity differs")

    identity(result)
    require(result["schema_version"] == "hf-native-mean-result-1.0" and result["status"] == "success"
            and result["production_converged"] is result["task_target_executed"] is True,
            "The ordinary task target must have converged")
    require(result["equilibrium_qualified"] is result["independent_HP_qualified"] is result["HF_qualified"] is False
            and result["call_counts"]["HP_calls"] == result["call_counts"]["JIT_calls"] == 0,
            "Production/independent qualification scope differs")
    result_sha = digest(directory/"result.json")
    require(receipt["result_sha256"] == audit["result_sha256"] == result_sha
            and audit["schema_version"] == "native-mean-independent-audit-1.0"
            and audit["full_element_and_DOF_coverage"] is True
            and audit["HP_matrix_columns_exhaustively_checked"] is False, "Saved audit coverage/result binding differs")
    model_file = directory/result["model"]["descriptor_path"]
    require(digest(model_file) == result["model"]["descriptor_file_sha256"], "Model JSON SHA differs")
    model_meta = read(model_file)
    identity(model_meta)
    model_arrays = directory/result["model"]["arrays_path"]
    model = archive(model_arrays, model_meta["arrays"])
    require(model_meta["descriptor_sha256"] == result["model"]["descriptor_sha256"]
            and digest(model_arrays) == result["model"]["arrays_sha256"] == receipt["model_sha256"], "Model binding differs")
    family = model_meta["task"]["case_family"]
    require(family in ("inverter", "gripper") and audit["alias"] == family+"_canonical", "Actual family/audit alias differs")
    geometry_file = model_file.parent/model_meta["source_geometry"]["snapshot"]["descriptor"]
    geometry = read(geometry_file)
    identity(geometry)
    require(geometry["case_family"] == family and model_meta["task_sha256"] == result["task_sha256"]
            and model_meta["source_geometry"]["geometry_id"] == result["source_geometry"]["geometry_id"], "Task/source family identity differs")
    direction = model["b_out"].reshape(-1, 2).sum(axis=0)
    expected = [-1., 0.] if family == "inverter" else [0., 1.]
    require(np.array_equal(direction, expected) and np.array_equal(direction, geometry["region_tags"]["output"]["direction"])
            and model["k_out"] == 0., "Actual free-output reference differs")
    require(result["targets_mm"] == [0., .001] and result["task_target_mm"] == model_meta["task"]["input"]["target_mm"] == .001,
            "Only the ordinary [0,0.001] mm TEST prefix is supported")
    require(result["accepted_states"] == audit["accepted_states"] == len(result["states"]) == len(audit["states"])
            and len(result["states"]) >= 2, "Actual accepted-state audit coverage differs")
    states = []
    for index, (row, checked) in enumerate(zip(result["states"], audit["states"])):
        require(checked["index"] == index and checked["status"] == "pass"
                and checked["state_sha256"] == row["state_sha256"] and checked["target_mm"] == row["d"], "Accepted-state audit differs")
        bind_saved_records(checked, audit_root, files)
        state_json = directory/row["descriptor_path"]
        require(digest(state_json) == row["descriptor_file_sha256"], "Accepted JSON SHA differs")
        record = read(state_json)
        identity(record)
        require(record == {k: v for k, v in row.items() if k not in ("descriptor_path", "descriptor_file_sha256")}, "Accepted flat/JSON record differs")
        state, forces = (archive(directory/row[key]["path"], row[key]) for key in ("state", "forces"))
        state_sha = sha256(b"split_displacement_v1")
        state_sha.update(np.asarray([len(state["lift"])], dtype="<i8").tobytes())
        for key in ("lift", "fluctuation"): state_sha.update(np.asarray(state[key], dtype="<f8").tobytes())
        require(state_sha.hexdigest() == row["state_sha256"] and not np.any(state["lift"])
                and not np.any(state["fluctuation"][model["fixed_dofs"]]) and np.all(forces["J"] > 0.), "Saved split state/fixed-zero/J differs")
        for key in ("tangents", "matrix"):
            path = directory/row[key]["path"]
            require(digest(path) == row[key]["sha256"], key+": saved SHA differs")
            files[path.relative_to(ROOT).as_posix()] = row[key]["sha256"]
        require(row["matrix"]["format"] == "csc" and row["matrix"]["units"] == "N/mm"
                and row["matrix"]["shape"] == [len(model["b_in"])]*2 and row["matrix"]["symmetrized"] is False, "Full accepted CSC differs")
        states.append(dict(row=row, state=state, forces=forces, audit=checked))
    for path in (directory/"result.json", audit_root/"summary.json", stage/"execution_receipt.json", model_file, model_arrays):
        files[path.relative_to(ROOT).as_posix()] = digest(path)
    return model, model_meta, result, states, audit, files, current, helper, family, direction


def boundary_edges(connectivity):
    counts = {}
    for cell in connectivity:
        for left, right in zip(cell, np.roll(cell, -1)):
            edge = tuple(sorted((int(left), int(right))))
            counts[edge] = counts.get(edge, 0)+1
    return np.asarray([edge for edge, count in counts.items() if count == 1], dtype=int).reshape(-1, 2)


def observations(model, states, family):
    inlet = np.flatnonzero(model["b_in"])
    require(len(inlet) == 3 and np.all(inlet % 2 == 0), "Canonical three-node x input differs")
    rows = []
    for index, state in enumerate(states):
        record, forces, hp = state["row"], state["forces"], state["audit"]["metrics"]
        u = state["state"]["lift"]+state["state"]["fluctuation"]
        row = dict(index=index, target_mm=record["d"], q_in_mm=record["q_in"], q_out_mm=record["q_out"],
            R_input_N=record["R_input"], minimum_J=record["minimum_J"], relative_residual=record["relative_residual"],
            constraint_residual_mm=record["constraint_residual"], relative_global_force_balance=record["relative_global_force_balance"],
            balance_x_N=float(forces["global_force_balance"][0]), balance_y_N=float(forces["global_force_balance"][1]),
            solid_minimum_J=float(forces["J"][model["solid"]].min()), medium_minimum_J=float(forces["J"][~model["solid"]].min()),
            maximum_displacement_mm=float(np.linalg.norm(u.reshape(-1, 2), axis=1).max()),
            hp_relative_residual=float(hp["independent_relative_residual"]), hp_relative_constraint=float(hp["relative_constraint"]),
            hp_relative_force_balance=float(hp["relative_force_balance"]))
        row.update({f"input_node_{j}_ux_mm": float(u[dof]) for j, dof in enumerate(inlet)})
        row["physical_output_mean_ux_mm" if family == "inverter" else "physical_output_mean_uy_mm"] = -row["q_out_mm"] if family == "inverter" else row["q_out_mm"]
        rows.append(row)
    return rows, inlet


def render(model, model_meta, states, rows, inlet, output, family, magnification):
    coords, conn, solid = (model[key] for key in ("coordinates", "connectivity", "solid"))
    actual = [coords+s["state"]["fluctuation"].reshape(-1, 2) for s in states]
    enlarged = [coords+magnification*s["state"]["fluctuation"].reshape(-1, 2) for s in states]
    edges = boundary_edges(conn[solid])
    fixed = np.unique(model["fixed_dofs"]//2)
    support = np.asarray(model_meta["region_metadata"]["support"]["attached_nodes"], dtype=int)
    reaction_nodes = np.union1d(support, np.setdiff1d(fixed, support)[::3])
    maximum_force = max(float(np.linalg.norm(s["forces"][key].reshape(-1, 2), axis=1).max()) for s in states for key in FORCES)
    force_scale = max(maximum_force, 1e-30)/4.
    ranges = {name: [min(float(s["forces"]["J"][selection].min()) for s in states), max(float(s["forces"]["J"][selection].max()) for s in states)]
              for name, selection in (("solid", solid), ("medium", ~solid))}
    norms = {name: Normalize(low if low != high else low-1e-6, high if low != high else high+1e-6) for name, (low, high) in ranges.items()}
    margin = .08*float(np.ptp(coords[:, 0]))
    positions_all = np.concatenate([coords, *actual, *enlarged])
    bounds = [((p[:, 0].min()-margin, p[:, 0].max()+margin), (p[:, 1].min()-margin, p[:, 1].max()+margin)) for p in (np.concatenate([coords, *actual]), positions_all)]
    label, component = ("−x", "ux") if family == "inverter" else ("+y", "uy")
    handles = [Line2D([], [], color="#888888", linestyle="--", label="source solid outline"),
               Line2D([], [], color="#174e75", label="accepted solid outline")]
    handles += [Line2D([], [], color=color, label=text) for color, text in zip(COLORS,
                ("constraint reactions: all support; other fixed stride 3", "input actuator on model", "free output: spring zero"))]

    def structure(ax, index, *, zoom=False, colorbars=False):
        points = enlarged[index] if zoom else actual[index]
        ax.add_collection(PolyCollection(coords[conn[solid]], facecolors="#bdbdbd", alpha=.2, edgecolors="none"))
        for name, selected, palette, alpha in (("medium", ~solid, "Oranges", .4), ("solid", solid, "Blues", .95)):
            collection = PolyCollection(points[conn[selected]], array=states[index]["forces"]["J"][selected].mean(axis=1),
                cmap=palette, norm=norms[name], alpha=alpha, edgecolors="none", zorder=1 if name == "medium" else 2)
            ax.add_collection(collection)
            if colorbars:
                bar = ax.figure.colorbar(collection, ax=ax, shrink=.7, fraction=.04, pad=.015)
                bar.set_label(name+" mean J", fontsize=8); bar.ax.tick_params(labelsize=7)
                bar.formatter = ScalarFormatter(useOffset=False); bar.formatter.set_scientific(False); bar.update_ticks()
        ax.add_collection(LineCollection(coords[edges], colors="#888888", linewidths=.6, linestyles="--", zorder=3))
        ax.add_collection(LineCollection(points[edges], colors="#174e75", linewidths=.7, zorder=4))
        ax.scatter(*points[inlet//2].T, color=COLORS[1], s=16, zorder=5)
        ax.scatter(*points[fixed].T, marker="s", facecolors="none", edgecolors="#34485e", s=8, linewidths=.3, zorder=5)
        if not zoom:
            for key, color in zip(FORCES, COLORS):
                force = states[index]["forces"][key].reshape(-1, 2)
                selected = reaction_nodes if key == "support_reaction" else np.flatnonzero(np.any(force != 0., axis=1))
                ax.quiver(*points[selected].T, *force[selected].T, angles="xy", scale_units="xy", scale=force_scale,
                          color=color, width=.004, minlength=0., zorder=6)
        xlim, ylim = bounds[int(zoom)]
        ax.set(xlim=xlim, ylim=ylim, aspect="equal", xlabel="x [mm]", ylabel="y [mm]",
               title=f"SUPPLEMENT: displacement ×{magnification:g}; no force arrows" if zoom else "Actual accepted deformation ×1")

    fig = plt.figure(figsize=(18, 11.5), layout="constrained")
    grid = fig.add_gridspec(3, 3, height_ratios=[1., .19, 1.])
    final = len(states)-1
    structure(fig.add_subplot(grid[0, 0]), final, colorbars=True)
    structure(fig.add_subplot(grid[0, 1]), final, zoom=True)
    legend = fig.add_subplot(grid[1, :2]); legend.axis("off"); legend.legend(handles=handles, loc="center", ncol=2, fontsize=8, framealpha=1.)
    d = np.asarray([r["target_mm"] for r in rows])*1000.
    force_axis, input_axis, output_axis, table = [fig.add_subplot(grid[position]) for position in ((0, 2), (2, 0), (2, 1), (2, 2))]
    force_axis.plot(d, [r["R_input_N"] for r in rows], "o-", color=COLORS[1])
    force_axis.set(xlabel="input weighted mean target [µm]", ylabel="input actuator R [N]", title=f"Saved input multiplier: {len(rows)} accepted samples")
    output_axis.plot(d, [1000*r["q_out_mm"] for r in rows], "s-", color="#176a80")
    output_axis.set(xlabel="input weighted mean target [µm]", ylabel=f"q_out along {label} [µm]", title=f"Free-output reference mean ({label}); no second sign flip")
    for j, dof in enumerate(inlet):
        input_axis.plot(d, [1000*r[f"input_node_{j}_ux_mm"] for r in rows], "o-",
                        label=f"node {dof//2}, y={coords[dof//2,1]:g} mm, weight={model['b_in'][dof]:g}")
    input_axis.plot(d, [1000*r["q_in_mm"] for r in rows], "k:", linewidth=2, label="actual weighted mean")
    input_axis.set(xlabel="input weighted mean target [µm]", ylabel="actual input ux [µm]", title="Input nodes remain free to differ")
    input_axis.legend(fontsize=8)
    for ax in (force_axis, input_axis, output_axis): ax.grid(alpha=.25)
    last = rows[-1]; table.axis("off")
    physical = last[f"physical_output_mean_{component}_mm"]
    lines = [f"FINAL {family.upper()} TEST STATE; output reference {label}",
        f"d={last['target_mm']:.9g} mm; R={last['R_input_N']:.9g} N", f"q_in={last['q_in_mm']:.9g} mm; q_out={last['q_out_mm']:.9g} mm",
        f"Physical output mean {component} = {'−q_out' if family == 'inverter' else 'q_out'} = {physical:.9g} mm",
        f"solid / medium min J = {last['solid_minimum_J']:.10g} / {last['medium_minimum_J']:.10g}",
        f"production / HP residual = {last['relative_residual']:.3e} / {last['hp_relative_residual']:.3e}",
        f"mean error = {last['constraint_residual_mm']:.3e} mm; HP relative = {last['hp_relative_constraint']:.3e}",
        f"external balance (relative) = {last['relative_global_force_balance']:.3e}; HP={last['hp_relative_force_balance']:.3e}",
        f"external ΣFx,ΣFy = {last['balance_x_N']:.3e}, {last['balance_y_N']:.3e} N", "", "d [mm]     min J         relative residual / balance"]
    lines += [f"{r['target_mm']:.4g}        {r['minimum_J']:.9g}     {r['relative_residual']:.2e} / {r['relative_global_force_balance']:.2e}" for r in rows]
    lines += ["", "Saved-state independent audit PASS; small coarse TEST.", f"All {len(conn)} element J colors are actual quadrature means.",
              "Numeric minimum uses all quadrature points; J is not pressure.", "No workpiece/contact/clamping or full-stroke claim.",
              "Original modeled lower half; no doubling or interpolated states."]
    table.text(0., 1., "\n".join(lines), va="top", transform=table.transAxes, fontsize=8.5, linespacing=1.5,
               bbox=dict(facecolor="white", edgecolor="none", pad=3))
    fig.suptitle(f"Native {family} average-input TEST: actual ×1; supplementary displacement ×{magnification:g}\n"
                 f"Common external-force arrow scale: {maximum_force:.9g} N = 4 display mm over the whole accepted path", fontsize=12)
    fig.savefig(output/"native_mean_path.png", dpi=160); plt.close(fig)
    frames = []
    frame = plt.figure(figsize=(12, 6.3), layout="constrained")
    frame_grid = frame.add_gridspec(2, 2, height_ratios=[1., .23])
    panels = [frame.add_subplot(frame_grid[0, j]) for j in range(2)]
    strip = frame.add_subplot(frame_grid[1, :]); strip.axis("off"); strip.legend(handles=handles, loc="center", ncol=2, fontsize=8)
    for index, row in enumerate(rows):
        for ax in panels: ax.clear()
        structure(panels[0], index); structure(panels[1], index, zoom=True)
        frame.suptitle(f"{family}: actual accepted state {index+1}/{len(rows)}; d={row['target_mm']:.9g} mm; R={row['R_input_N']:.9g} N\n"
                      f"q_out along {label}={row['q_out_mm']:.9g} mm; saved-state audit PASS. No interpolation; J is not pressure.", fontsize=11)
        frame.set_dpi(140); frame.canvas.draw()
        frames.append(Image.fromarray(np.asarray(frame.canvas.buffer_rgba()).copy()).convert("RGB"))
    plt.close(frame)
    # One common palette prevents force class colors changing between frames.
    palette_source = Image.new("RGB", (frames[0].width, len(frames)*frames[0].height))
    for index, image in enumerate(frames): palette_source.paste(image, (0, index*image.height))
    palette = palette_source.quantize(colors=256)
    quantized = [image.quantize(palette=palette, dither=Image.Dither.NONE) for image in frames]
    quantized[0].save(output/"native_mean_path.gif", save_all=True, append_images=quantized[1:], duration=1000, loop=0)
    return dict(geometry_scale=1., supplementary_displacement_scale=magnification, supplementary_force_arrows=False,
        force_arrow_scale_N_per_display_mm=force_scale, maximum_nodal_external_force_N=maximum_force, maximum_arrow_display_mm=4.,
        force_scale_shared_over_all_states_and_components=True, support_arrow_nodes=reaction_nodes.tolist(),
        support_arrow_sampling="All attached support nodes; other fixed nodes at stride 3", input_arrow_nodes=(inlet//2).tolist(),
        legend_location="Dedicated external strip; never over structural coordinates", R_and_q_out_separate_axes=True,
        all_element_J_colored=True, J_display="Element quadrature mean; minimum over all quadrature points", actual_J_ranges=ranges,
        actual_frame_count=len(rows), interpolated_frames=0, GIF_shared_palette=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT/"lf_data_preparation/native_inverter_mean_001")
    parser.add_argument("--output", type=Path, required=True, help="New output directory")
    parser.add_argument("--magnification", type=float, default=1000.)
    args = parser.parse_args()
    require(np.isfinite(args.magnification) and args.magnification > 1., "Supplementary magnification must exceed one")
    model, model_meta, result, states, audit, files, current, helper, family, direction = load_saved(args.input.resolve())
    rows, inlet = observations(model, states, family)
    output = args.output.resolve(); output.mkdir(parents=True, exist_ok=False)
    display = render(model, model_meta, states, rows, inlet, output, family, args.magnification)
    with (output/"numeric_states.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    frozen = output/"plot_native_mean_inverter_frozen.py"; frozen.write_bytes(Path(__file__).read_bytes())
    helper_file = output/"helpers/data.py"; helper_file.parent.mkdir(); helper_file.write_bytes(helper.read_bytes())
    media = {}
    for name in ("native_mean_path.png", "native_mean_path.gif"):
        with Image.open(output/name) as image: media[name] = dict(sha256=digest(output/name), pixels=list(image.size), frames=getattr(image, "n_frames", 1))
    metadata = dict(schema_version="native-mean-family-view-1.0", case_family=family, scope="Saved audited canonical [0,0.001] mm TEST prefix only",
        geometry_id=model_meta["source_geometry"]["geometry_id"], task_sha256=result["task_sha256"], grid=model_meta["grid"],
        counts=result["counts"], material=model_meta["material"], input_nodes=(inlet//2).tolist(), input_weights=model["b_in"][inlet].tolist(),
        output_reference_direction=direction.tolist(), output_reference_label="−x" if family == "inverter" else "+y",
        output_sign_rule="q_out is saved b_out dot u; physical mean ux=-q_out" if family == "inverter" else "q_out is saved b_out dot u; physical mean uy=q_out",
        display=display, numerical_states=rows, final_numbers=rows[-1], input_files_sha256=files,
        historical_source_expectations=audit["source_bindings"], current_source_observations=current,
        source_verification_scope="Historical SHA verified in both production/audit capsules; current source matching is informational only",
        audit_summary_sha256=digest(args.input/"audit/summary.json"), audit_states=[{k:s["audit"][k] for k in ("index", "state_sha256", "target_mm", "status", "metrics")} for s in states],
        force_calls=0, tangent_calls=0, solver_calls=0, HP_calls=0, model_constructions=0,
        independent_saved_state_audit_passed=True, full_stroke_qualified=False, contact_clamping_claim=False,
        fine_model_checked=False, half_model_quantities_doubled=False, units=dict(length="mm", force="N", J="dimensionless"),
        viewer_sha256=digest(frozen), frozen_helpers_sha256={"helpers/data.py":digest(helper_file)}, media=media,
        numeric_states_csv_sha256=digest(output/"numeric_states.csv"))
    (output/"view_metadata.json").write_text(json.dumps(metadata, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps(dict(output=str(output), case_family=family, accepted_frames=len(rows), force_calls=0, tangent_calls=0, solver_calls=0, HP_calls=0)))


if __name__ == "__main__":
    main()
