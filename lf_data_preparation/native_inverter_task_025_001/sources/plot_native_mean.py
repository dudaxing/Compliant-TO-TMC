"""Show an audited native mean-driven path from saved data only.

The main geometry is actual x1. Explicit displacement magnification is only a
display supplement. No force, tangent, model, solver or HP entry is imported.
"""
from __future__ import annotations

import argparse
import csv
from hashlib import sha256
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import PillowWriter
from matplotlib.collections import LineCollection, PolyCollection
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D
from matplotlib.ticker import ScalarFormatter
import numpy as np
from PIL import Image

ROOT = next(parent for parent in Path(__file__).resolve().parents
            if (parent/"hf_repo/src/hf_eval/data.py").is_file())
sys.path.insert(0, str(ROOT/"hf_repo/src"))
from hf_eval.data import canonical_hash

FORCE_KEYS = ("support_reaction", "input_force", "spring_force_on_structure")
FORCE_COLORS = ("#216a9b", "#b84b23", "#8856a7")


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_archive(path, declaration):
    require(digest(path) == declaration["sha256"], path.name+": saved SHA differs")
    with np.load(path, allow_pickle=False) as archive:
        values = {key: archive[key].copy() for key in archive.files}
    require(set(values) == set(declaration["fields"]), path.name+": fields differ")
    for name, array in values.items():
        actual = dict(dtype=array.dtype.name, shape=list(array.shape),
                      sha256=sha256(array.tobytes(order="C")).hexdigest())
        require(actual == declaration["fields"][name], path.name+": "+name+" differs")
    return values


def check_descriptor(descriptor):
    require(canonical_hash({k: v for k, v in descriptor.items() if k != "descriptor_sha256"})
            == descriptor["descriptor_sha256"], "Saved descriptor identity differs")


def boundary_edges(connectivity):
    counts = {}
    for cell in connectivity:
        for left, right in zip(cell, np.roll(cell, -1)):
            edge = tuple(sorted((int(left), int(right))))
            counts[edge] = counts.get(edge, 0)+1
    return np.asarray([edge for edge, count in counts.items() if count == 1], dtype=int).reshape(-1, 2)


def load_saved(stage):
    directory = stage/"result"
    result = read_json(directory/"result.json")
    check_descriptor(result)
    audit = read_json(stage/"audit/summary.json")
    require(result["schema_version"] == "hf-native-mean-result-1.0" and result["production_converged"] is True
            and result["status"] == "success" and audit["status"] == "pass",
            "A converged path and passing saved-state audit are required")
    require(result["equilibrium_qualified"] is False and result["independent_HP_qualified"] is False
            and result["call_counts"]["HP_calls"] == result["call_counts"]["JIT_calls"] == 0,
            "Production scope differs from independent qualification")
    require(audit["schema_version"] == "native-mean-independent-audit-1.0"
            and audit["result_sha256"] == digest(directory/"result.json")
            and audit["full_element_and_DOF_coverage"] is True
            and audit["HP_matrix_columns_exhaustively_checked"] is False,
            "Independent native mean audit scope or result binding differs")
    files = {p.relative_to(ROOT).as_posix(): digest(p)
             for p in (directory/"result.json", stage/"audit/summary.json")}
    for bindings in (audit["input_bindings"], audit["source_bindings"]):
        for relative, expected in bindings.items():
            require(digest(ROOT/relative) == expected, relative+": audit binding differs")
            files[relative] = expected
    model_file = directory/result["model"]["descriptor_path"]
    require(digest(model_file) == result["model"]["descriptor_file_sha256"], "Model JSON SHA differs")
    model_metadata = read_json(model_file)
    check_descriptor(model_metadata)
    model_file_arrays = directory/result["model"]["arrays_path"]
    model = read_archive(model_file_arrays, model_metadata["arrays"])
    require(model_metadata["descriptor_sha256"] == result["model"]["descriptor_sha256"]
            and digest(model_file_arrays) == result["model"]["arrays_sha256"], "Model binding differs")
    require(model_metadata["task"]["case_family"] == "gripper" and model["k_out"] == 0.,
            "This viewer shows the free-output gripper TEST prefix")
    require(result["task_target_mm"] == model_metadata["task"]["input"]["target_mm"] == .001
            and result["targets_mm"] == [0., .001] and result["target_reached"] is True
            and result["task_target_executed"] is True,
            "Ordinary [0,0.001] mm task target differs")
    require(model_metadata["task_sha256"] == result["task_sha256"]
            and model_metadata["source_geometry"]["geometry_id"] == result["source_geometry"]["geometry_id"],
            "Model source/task identity differs")
    require(np.array_equal(model["b_out"].reshape(-1, 2).sum(axis=0), [0., 1.]),
            "Saved output reference direction differs")
    require(len(result["states"]) == len(audit["states"]) and len(result["states"]) >= 2,
            "Accepted-state audit coverage differs")
    states = []
    for row, checked in zip(result["states"], audit["states"]):
        require(checked["status"] == "pass" and checked["state_sha256"] == row["state_sha256"],
                "Accepted-state audit identity differs")
        state_file = directory/row["descriptor_path"]
        require(digest(state_file) == row["descriptor_file_sha256"], "Accepted JSON SHA differs")
        state_record = read_json(state_file)
        check_descriptor(state_record)
        require(state_record == {k: v for k, v in row.items()
                                 if k not in ("descriptor_path", "descriptor_file_sha256")},
                "Accepted JSON/flat record differs")
        state = read_archive(directory/row["state"]["path"], row["state"])
        forces = read_archive(directory/row["forces"]["path"], row["forces"])
        state_hash = sha256(b"split_displacement_v1")
        state_hash.update(np.asarray([len(state["lift"])], dtype="<i8").tobytes())
        for key in ("lift", "fluctuation"):
            state_hash.update(np.asarray(state[key], dtype="<f8").tobytes())
        require(state_hash.hexdigest() == row["state_sha256"], "Split state SHA differs")
        require(not np.any(state["lift"]) and not np.any(state["fluctuation"][model["fixed_dofs"]])
                and np.all(forces["J"] > 0.), "Zero-lift/fixed-zero/positive-J path differs")
        for key in ("tangents", "matrix"):
            require(digest(directory/row[key]["path"]) == row[key]["sha256"], key+": saved SHA differs")
        require(row["matrix"]["format"] == "csc" and row["matrix"]["units"] == "N/mm"
                and row["matrix"]["shape"] == [len(model["b_in"])]*2
                and row["matrix"]["symmetrized"] is False,
                "Full unsymmetrized accepted CSC differs")
        for path in (state_file, *(directory/row[key]["path"] for key in ("state", "forces", "tangents", "matrix"))):
            files[path.relative_to(ROOT).as_posix()] = digest(path)
        states.append(dict(row=row, state=state, forces=forces, audit=checked))
    return model, model_metadata, result, states, audit, files


def numerical_rows(model, states):
    input_dofs = np.flatnonzero(model["b_in"])
    require(len(input_dofs) == 3 and np.all(input_dofs % 2 == 0), "Canonical input port differs")
    rows = []
    for index, accepted in enumerate(states):
        record, forces = accepted["row"], accepted["forces"]
        u = accepted["state"]["lift"]+accepted["state"]["fluctuation"]
        row = dict(index=index, target_mm=float(record["d"]), q_in_mm=float(record["q_in"]),
            R_input_N=float(record["R_input"]), q_out_mm=float(record["q_out"]),
            minimum_J=float(record["minimum_J"]), relative_residual=float(record["relative_residual"]),
            constraint_residual_mm=float(record["constraint_residual"]),
            relative_global_force_balance=float(record["relative_global_force_balance"]),
            balance_x_N=float(forces["global_force_balance"][0]),
            balance_y_N=float(forces["global_force_balance"][1]),
            solid_minimum_J=float(forces["J"][model["solid"]].min()),
            medium_minimum_J=float(forces["J"][~model["solid"]].min()),
            maximum_displacement_mm=float(np.linalg.norm(u.reshape(-1, 2), axis=1).max()))
        row.update({f"input_node_{j}_ux_mm": float(u[dof]) for j, dof in enumerate(input_dofs)})
        hp = accepted["audit"]["metrics"]
        row.update(hp_relative_residual=float(hp["independent_relative_residual"]),
                   hp_relative_constraint=float(hp["relative_constraint"]),
                   hp_relative_force_balance=float(hp["relative_force_balance"]))
        rows.append(row)
    return rows, input_dofs


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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT/"lf_data_preparation/native_mean_001")
    parser.add_argument("--output", type=Path, required=True, help="New output directory")
    parser.add_argument("--magnification", type=float, default=1000.)
    args = parser.parse_args()
    require(np.isfinite(args.magnification) and args.magnification > 1., "Supplementary magnification must exceed one")
    model, model_metadata, result, states, audit, files = load_saved(args.input.resolve())
    rows, input_dofs = numerical_rows(model, states)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    display = render(model, model_metadata, states, rows, input_dofs, output, args.magnification)
    with (output/"numeric_states.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    frozen = output/"plot_native_mean_frozen.py"
    frozen.write_bytes(Path(__file__).read_bytes())
    helper = output/"helpers/data.py"
    helper.parent.mkdir()
    helper.write_bytes((ROOT/"hf_repo/src/hf_eval/data.py").read_bytes())
    media = {}
    for name in ("native_mean_path.png", "native_mean_path.gif"):
        path = output/name
        with Image.open(path) as image:
            media[name] = dict(sha256=digest(path), pixels=list(image.size), frames=getattr(image, "n_frames", 1))
    metadata = dict(schema_version="native-mean-view-1.0", scope="Saved accepted states and saved independent audit only",
        geometry_id=model_metadata["source_geometry"]["geometry_id"], task_sha256=result["task_sha256"],
        grid=model_metadata["grid"], counts=result["counts"], material=model_metadata["material"],
        input_nodes=(input_dofs//2).tolist(), input_weights=model["b_in"][input_dofs].tolist(),
        output_direction=[0., 1.], display=display, numerical_states=rows, final_numbers=rows[-1],
        audit_summary_sha256=digest(args.input/"audit/summary.json"), input_files_sha256=files,
        audit_source_bindings=audit["source_bindings"], units=dict(length="mm", force="N", J="dimensionless"),
        audit_states=[{k: s["audit"][k] for k in ("index", "state_sha256", "target_mm", "status", "metrics")} for s in states],
        force_calls=0, tangent_calls=0, HP_calls=0, solver_calls=0, model_constructions=0,
        independent_saved_state_audit_passed=True, task_scope="[0,0.001] mm coarse native average-displacement TEST prefix",
        full_stroke_qualified=False, contact_clamping_claim=False, fine_model_checked=False,
        half_model_quantities_doubled=False, viewer_sha256=digest(frozen),
        frozen_helpers_sha256={"helpers/data.py": digest(helper)}, media=media,
        numeric_states_csv_sha256=digest(output/"numeric_states.csv"))
    (output/"view_metadata.json").write_text(json.dumps(metadata, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps(dict(output=str(output), accepted_frames=len(rows), force_calls=0, tangent_calls=0, HP_calls=0, solver_calls=0)))


if __name__ == "__main__":
    main()
