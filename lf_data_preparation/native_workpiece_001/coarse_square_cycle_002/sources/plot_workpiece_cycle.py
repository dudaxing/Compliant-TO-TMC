"""Plot a saved fixed-workpiece cycle, including an honestly labelled partial path.

Only JSON/NPZ packages and cached observations are read. No mechanics, model,
solver, tangent or precision-reference module is imported or evaluated.
"""
from __future__ import annotations

import argparse
import csv
from hashlib import sha256
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection, PolyCollection
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D
from matplotlib.ticker import ScalarFormatter
import numpy as np
from PIL import Image

ROOT = next(p for p in Path(__file__).resolve().parents if (p/"hf_repo").is_dir())
DEFAULT = ROOT/"lf_data_preparation/native_workpiece_001/coarse_square_cycle_001"
COMPONENTS = ("total", "material", "regularization")
COLORS = dict(total="#7b3294", material="#1b7837", regularization="#c76926")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    if isinstance(value, dict):
        return {key: canonical(part) for key, part in value.items()}
    if isinstance(value, list):
        return [canonical(part) for part in value]
    if isinstance(value, float):
        require(np.isfinite(value), "Nonfinite descriptor number")
        return (0. if value == 0. else value).hex()
    return value


def semantic_hash(record):
    payload = json.dumps(canonical(record), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return sha256(payload.encode("utf-8")).hexdigest()


def load_saved(input_directory):
    directory = input_directory if (input_directory/"result.json").is_file() else input_directory/"result"
    stage, pins, current_sources = directory.parent, {}, {}

    def bind(path, expected=None):
        path = path.resolve()
        actual = digest(path)
        require(expected is None or actual == expected, "File SHA differs: "+path.name)
        pins[path] = actual
        return actual

    def read(path, expected=None, descriptor=False):
        bind(path, expected)
        record = json.loads(path.read_text(encoding="utf-8"))
        if descriptor:
            require(semantic_hash({k: v for k, v in record.items() if k != "descriptor_sha256"})
                    == record["descriptor_sha256"], "Descriptor identity differs: "+path.name)
        return record

    def archive(path, declaration, matrix=False):
        bind(path, declaration["sha256"])
        with np.load(path, allow_pickle=False) as saved:
            arrays = {name: saved[name].copy() for name in saved.files}
        require(matrix or set(arrays) == set(declaration["fields"]), "NPZ field set differs: "+path.name)
        for name, item in declaration["fields"].items():
            array = arrays[name]
            require(dict(dtype=array.dtype.name, shape=list(array.shape), sha256=sha256(array.tobytes(order="C")).hexdigest()) == item,
                    "NPZ field differs: "+path.name+"/"+name)
        if matrix:
            require(set(arrays) == {"data", "indices", "indptr", "shape", "format"}
                    and arrays["format"].item() == b"csc" and arrays["shape"].tolist() == declaration["shape"]
                    and len(arrays["data"]) == declaration["nnz"], "Saved full CSC declaration differs")
        return arrays

    result = read(directory/"result.json", descriptor=True)
    receipt = read(stage/"execution_receipt.json")
    inventory = read(stage/"input_inventory.json", receipt["input_inventory_sha256"])
    freeze = read(stage/"source_freeze.json", inventory["source_freeze_sha256"])
    require(receipt["sources"] == freeze["sources"] and receipt["inputs"] == inventory["input_bindings"], "Stage bindings differ")
    for name, expected in freeze["sources"].items():
        bind(stage/"sources"/Path(name).name, expected)
        live = ROOT/name
        actual = digest(live) if live.is_file() else None
        current_sources[name] = dict(historical_sha256=expected, current_sha256=actual, matches_historical=actual == expected)
    for name, expected in inventory["input_bindings"].items():
        bind(ROOT/name, expected)
    require(receipt["result_sha256"] == pins[(directory/"result.json").resolve()]
            and result["schema_version"] == "hf-native-mean-result-1.1"
            and result["path_kind"] == "ordered_cycle" and result["status"] in ("success", "failed"), "Saved cycle/result binding differs")
    require(result["independent_HP_qualified"] is result["equilibrium_qualified"] is result["HF_qualified"] is False,
            "Production result qualification differs")
    model_file = directory/result["model"]["descriptor_path"]
    metadata = read(model_file, result["model"]["descriptor_file_sha256"], descriptor=True)
    model = archive(model_file.parent/metadata["arrays"]["path"], metadata["arrays"])
    require(metadata["schema_version"] == "hf-native-project-model-1.1" and len(model) == 27
            and metadata["descriptor_sha256"] == result["model"]["descriptor_sha256"]
            and metadata["arrays"]["sha256"] == result["model"]["arrays_sha256"] == receipt["model_sha256"], "Workpiece model binding differs")
    task = metadata["task"]
    require(task["schema_version"] == "hf-native-project-task-1.1" and task["workpiece"]["shape"] == "square"
            and task["workpiece"]["kind"] == "fixed_rigid" and task["case_family"] == "gripper"
            and semantic_hash(task) == metadata["task_sha256"] == result["task_sha256"] == receipt["task_sha256"], "Declared fixed-square task differs")
    targets = task["path"]["targets_mm"]
    require(targets == result["targets_mm"] == inventory["case"]["targets_mm"]
            and targets[0] == 0. and max(targets) == result["task_target_mm"] == task["input"]["target_mm"], "Declared ordered targets differ")
    source = metadata["source_geometry"]
    geometry_file = model_file.parent/source["snapshot"]["descriptor"]
    geometry = read(geometry_file, source["descriptor_file_sha256"], descriptor=True)
    masks = archive(geometry_file.parent/geometry["arrays"]["path"], geometry["arrays"])
    require(geometry["geometry_id"] == task["geometry"]["geometry_id"] == source["geometry_id"]
            and geometry["descriptor_sha256"] == task["geometry"]["descriptor_sha256"] == source["descriptor_sha256"]
            and geometry["arrays"]["sha256"] == source["arrays_sha256"]
            and np.array_equal(model["solid"], masks["solid"].ravel().astype(bool)), "Original geometry/solid identity differs")
    body = metadata["region_metadata"]["workpiece"]
    require(result["workpiece"] == body and body["definition"] == task["workpiece"], "Saved workpiece overlay differs")
    for key in ("cells", "nodes", "dofs", "background_symmetry_overlap_dofs"):
        require(np.array_equal(model["workpiece_"+key], body[key]), "Workpiece index binding differs: "+key)
    require(not np.any(model["solid"][model["workpiece_cells"]]) and np.all(np.isin(model["workpiece_dofs"], model["fixed_dofs"])),
            "Fixed workpiece must remain an original-medium constraint overlay")
    states = []
    previous_index = -1
    for index, row in enumerate(result["states"]):
        stored = read(directory/row["descriptor_path"], row["descriptor_file_sha256"], descriptor=True)
        require(stored == {k: v for k, v in row.items() if k not in ("descriptor_path", "descriptor_file_sha256")}, "Accepted descriptor differs")
        state = archive(directory/row["state"]["path"], row["state"])
        forces = archive(directory/row["forces"]["path"], row["forces"])
        archive(directory/row["tangents"]["path"], row["tangents"])
        archive(directory/row["matrix"]["path"], row["matrix"], matrix=True)
        identity = sha256(b"split_displacement_v1"+np.asarray(len(model["b_in"]), dtype="<i8").tobytes()
                          +state["lift"].astype("<f8", copy=False).tobytes()+state["fluctuation"].astype("<f8", copy=False).tobytes()).hexdigest()
        original = row["original_target_index"]
        leg = "origin" if original == 0 else "loading" if targets[original] > targets[original-1] else "unloading"
        require(identity == row["state_sha256"] == row["assembler_state_sha256"] and set(state) == {"lift", "fluctuation"}
                and len(forces) == 17 and not np.any(state["lift"]) and not np.any(state["fluctuation"][model["fixed_dofs"]])
                and np.all(forces["J"] > 0.) and original >= previous_index and row["leg"] == leg
                and row["original_target_displacement"] == targets[original]
                and row["is_original_target"] == (row["d"] == targets[original]), "Accepted state/index/leg/fixed/J identity differs")
        require(row["matrix"]["shape"] == [len(model["b_in"])]*2 and row["matrix"]["units"] == "N/mm"
                and row["matrix"]["symmetrized"] is False, "Full tangent storage differs")
        states.append(dict(record=row, state=state, forces=forces))
        previous_index = original
    require(len(states) == result["accepted_states"] == receipt["accepted_states"] and len(states) > 0
            and states[0]["record"]["d"] == 0., "Accepted chronology/count differs")
    if result["path_completed"]:
        require(result["status"] == "success" and result["loading_peak_reached"] and result["unload_endpoint_reached"]
                and result["task_target_executed"] and states[-1]["record"]["original_target_index"] == len(targets)-1
                and states[-1]["record"]["d"] == targets[-1], "Complete cycle endpoint flags differ")
    bind(Path(__file__))
    return model, metadata, result, receipt, states, pins, current_sources


def edges(connectivity):
    counts = {}
    for cell in connectivity:
        for a, b in zip(cell, np.roll(cell, -1)):
            edge = tuple(sorted((int(a), int(b))))
            counts[edge] = counts.get(edge, 0)+1
    return np.asarray([edge for edge, count in counts.items() if count == 1], dtype=int).reshape(-1, 2)


def numerical_rows(model, states):
    rows = []
    inlet = np.flatnonzero(model["b_in"])
    for index, saved in enumerate(states):
        record, fields, body = saved["record"], saved["forces"], saved["record"]["workpiece"]
        u = saved["state"]["lift"]+saved["state"]["fluctuation"]
        row = dict(index=index, original_target_index=record["original_target_index"], leg=record["leg"],
            is_original_target=record["is_original_target"], bisection_depth=record["bisection_depth"],
            d_mm=record["d"], q_in_mm=record["q_in"], q_out_mm=record["q_out"], physical_output_mean_uy_mm=record["q_out"],
            R_input_N=record["R_input"], minimum_J=record["minimum_J"], maximum_Hu_per_mm=record["max_abs_Hu_per_mm"],
            relative_residual=record["relative_residual"], constraint_residual_mm=record["constraint_residual"],
            relative_global_force_balance=record["relative_global_force_balance"],
            balance_x_N=float(fields["global_force_balance"][0]), balance_y_N=float(fields["global_force_balance"][1]),
            maximum_display_displacement_mm=float(np.linalg.norm(u.reshape(-1, 2), axis=1).max()),
            two_sided_normal_magnitude_sum_N=body["two_sided_normal_magnitude_sum_N"],
            clearance_bottom_mm=body["node_window_clearance_mm"]["bottom"], clearance_left_mm=body["node_window_clearance_mm"]["left"])
        for name in COMPONENTS:
            row.update({f"lower_body_{name}_F{axis}_N": body["force_on_lower_body_N"][name][component] for component, axis in enumerate("xy")})
        for name in ("holding_reaction_on_model_N", "mirrored_upper_force_N", "full_workpiece_net_force_N", "overlapping_background_holding_reaction_N"):
            row.update({name.replace("_N", "_F"+axis+"_N"): value for axis, value in zip("xy", body[name])})
        for group, values in body["fixed_holding_reaction_partition_N"].items():
            row.update({f"holding_partition_{group}_F{axis}_N": value for axis, value in zip("xy", values)})
        row.update({"fixed_body_"+key: value for key, value in body["fixed_body_fields"].items()})
        row.update({f"input_node_{dof//2}_ux_mm": float(u[dof]) for dof in inlet})
        rows.append(row)
    return rows, inlet


def render(model, metadata, result, receipt, states, rows, inlet, output, magnification):
    coords, conn, solid = (model[key] for key in ("coordinates", "connectivity", "solid"))
    body_cells, body_nodes = model["workpiece_cells"], model["workpiece_nodes"]
    medium = ~solid.copy(); medium[body_cells] = False
    solid_edges, body_edges = edges(conn[solid]), edges(conn[body_cells])
    actual_u = [(saved["state"]["lift"]+saved["state"]["fluctuation"]).reshape(-1, 2) for saved in states]
    displacements = [np.linalg.norm(u, axis=1)[conn].mean(axis=1) for u in actual_u]
    maximum_u = max(float(values.max()) for values in displacements)
    norm = Normalize(0., maximum_u if maximum_u > 0. else 1e-15)
    support = np.asarray(metadata["region_metadata"]["support"]["attached_nodes"], dtype=int)
    out_nodes = np.asarray(metadata["region_metadata"]["ports"]["output"]["nodes"], dtype=int)
    other = np.setdiff1d(np.unique(model["fixed_dofs"]//2), np.union1d(support, body_nodes))[::3]
    reactions = np.union1d(support, other)
    maximum_force = max([float(np.linalg.norm(saved["forces"][key].reshape(-1, 2), axis=1).max())
                         for saved in states for key in ("support_reaction", "input_force")]
                        +[float(np.linalg.norm(saved["record"]["workpiece"]["force_on_lower_body_N"]["total"])) for saved in states])
    force_scale = max(maximum_force, 1e-30)/4.
    body_centre = coords[body_nodes].mean(axis=0)
    lower, upper = coords[body_nodes].min(axis=0), coords[body_nodes].max(axis=0)
    detail = [(lower[0]-12., upper[0]+2.), (lower[1]-10., upper[1]+2.)]
    extent = [(coords[:, j].min()-4., coords[:, j].max()+4.) for j in (0, 1)]
    representative = int(np.argmax([row["d_mm"] for row in rows]))
    handles = [Line2D([], [], color="#888888", linestyle="--", label="original mechanism outline"),
               Line2D([], [], color="#164e75", label="accepted mechanism outline"),
               Line2D([], [], color="#e3a45b", linewidth=5, label="third medium: actual displacement color"),
               Line2D([], [], color="#666666", linewidth=6, label="fixed lower-half workpiece overlay"),
               Line2D([], [], marker="^", color="#183a53", linestyle="none", label="attached support"),
               Line2D([], [], marker="o", color="#b84b23", linestyle="none", label="mean-input nodes / actuator force"),
               Line2D([], [], marker="D", markerfacecolor="none", color="#8856a7", linestyle="none", label="free +y output measurement nodes"),
               Line2D([], [], color="#216a9b", label="model constraint reactions: support + other fixed stride 3"),
               Line2D([], [], color=COLORS["total"], label="medium/model on lower body: total resultant")]

    def structure(ax, index, *, detail_view=False, amplified=False):
        points = coords+(magnification if amplified else 1.)*actual_u[index]
        medium_field = PolyCollection(points[conn[medium]], array=displacements[index][medium], cmap="Oranges", norm=norm, edgecolors="none")
        ax.add_collection(medium_field)
        field = PolyCollection(points[conn[solid]], array=displacements[index][solid], cmap="viridis", norm=norm, edgecolors="none", zorder=2)
        ax.add_collection(field)
        ax.add_collection(PolyCollection(coords[conn[body_cells]], facecolors="#c6c6c6", edgecolors="none", zorder=3))
        ax.add_collection(LineCollection(coords[solid_edges], colors="#888888", linestyles="--", linewidths=.6, zorder=4))
        ax.add_collection(LineCollection(points[solid_edges], colors="#164e75", linewidths=.75, zorder=5))
        ax.add_collection(LineCollection(coords[body_edges], colors="#4b4b4b", linewidths=1.1, zorder=5))
        ax.scatter(*points[support].T, marker="^", color="#183a53", s=26, zorder=8)
        ax.scatter(*points[inlet//2].T, color="#b84b23", s=24, zorder=8)
        ax.scatter(*points[out_nodes].T, marker="D", facecolors="none", edgecolors="#8856a7", s=34, zorder=8)
        if not amplified:
            for key, nodes, color in (("support_reaction", reactions, "#216a9b"), ("input_force", inlet//2, "#b84b23")):
                values = states[index]["forces"][key].reshape(-1, 2)[nodes]
                ax.quiver(*points[nodes].T, *values.T, angles="xy", scale_units="xy", scale=force_scale, color=color, width=.004, minlength=0., zorder=7)
            body_force = states[index]["record"]["workpiece"]["force_on_lower_body_N"]["total"]
            ax.quiver(*body_centre, *body_force, angles="xy", scale_units="xy", scale=force_scale, color=COLORS["total"], width=.008, minlength=0., zorder=9)
        bounds = detail if detail_view else extent
        ax.set(xlim=bounds[0], ylim=bounds[1], aspect="equal", xlabel="x [mm]", ylabel="y [mm]",
               title=f"DISPLAY ONLY: displacement ×{magnification:g}; no forces" if amplified else "Actual deformation ×1"+("; workpiece detail" if detail_view else ""))
        if detail_view:
            ax.text(.02, .02, "Fixed body stays at its source position.\nDisplay overlap is not contact evidence." if amplified else "Lower-half fixed square; original medium below/left.\nPurple arrow is force ON body, not holding reaction.",
                    transform=ax.transAxes, fontsize=8, va="bottom", bbox=dict(facecolor="white", edgecolor="none", alpha=.95))
        return field, medium_field

    def status_text():
        return f"Saved production: {result['status']}; wrapper: {receipt['status']}; path completed={result['path_completed']}"

    figure = plt.figure(figsize=(19, 9.5), layout="constrained")
    grid = figure.add_gridspec(3, 3, height_ratios=[1., .16, .47])
    fields = structure(figure.add_subplot(grid[0, 0]), representative)
    structure(figure.add_subplot(grid[0, 1]), representative, detail_view=True)
    structure(figure.add_subplot(grid[0, 2]), representative, detail_view=True, amplified=True)
    panels = figure.axes[:3]
    for phase, field in zip(("mechanism", "third medium"), fields):
        bar = figure.colorbar(field, ax=panels, shrink=.66, fraction=.018, pad=.02)
        bar.set_label(phase+" element mean nodal |u| [mm]")
        bar.formatter = ScalarFormatter(useOffset=False); bar.update_ticks()
    legend = figure.add_subplot(grid[1, :]); legend.axis("off"); legend.legend(handles=handles, loc="center", ncol=3, fontsize=8, framealpha=1.)
    tables = [figure.add_subplot(grid[2, j]) for j in range(3)]
    selected, last = rows[representative], rows[-1]
    body = states[representative]["record"]["workpiece"]
    text = [
        ["REAL ACCEPTED CHRONOLOGY (not sorted by displacement)", *[f"{r['index']:3d}  {r['leg']:9s} d={r['d_mm']:.7g} mm  original={r['original_target_index']}  depth={r['bisection_depth']}" for r in rows],
         f"Stored original targets: {result['targets_mm']} mm", f"Peak reached={result['loading_peak_reached']}; unloading endpoint={result['unload_endpoint_reached']}",
         "Returned zero uses continued state/R; no visual reset."],
        [f"SHOWN STATE {representative}: d={selected['d_mm']:.9g} mm", f"R={selected['R_input_N']:.9g} N; q_out (+y)={selected['q_out_mm']:.9g} mm",
         *[f"Lower-body {name}: Fx={body['force_on_lower_body_N'][name][0]:.9g}, Fy={body['force_on_lower_body_N'][name][1]:.9g} N" for name in COMPONENTS],
         f"Full mirrored net = ({body['full_workpiece_net_force_N'][0]:.9g}, 0) N",
         f"Two-sided normal magnitude sum = {body['two_sided_normal_magnitude_sum_N']:.9g} N",
         "These two mirrored quantities measure different things."],
        [f"FINAL ACCEPTED {last['index']}: d={last['d_mm']:.9g} mm", f"min J={last['minimum_J']:.10g}; max |Hu|={last['maximum_Hu_per_mm']:.5g} 1/mm",
         f"Relative residual={last['relative_residual']:.3e}; balance={last['relative_global_force_balance']:.3e}",
         f"ΣFx={last['balance_x_N']:.3e}, ΣFy={last['balance_y_N']:.3e} N", f"Failure: {result['failure']}",
         "Node-window clearances are raster diagnostics, not surface gaps.", "J is not pressure; pressure is undefined in this view.",
         "No contact onset, clamping or independent HF qualification claim."]]
    for ax, lines in zip(tables, text):
        ax.axis("off"); ax.text(0., 1., "\n".join(lines), transform=ax.transAxes, va="top", fontsize=8.4, linespacing=1.45,
                               bbox=dict(facecolor="white", edgecolor="none"))
    figure.suptitle("Fixed-workpiece ordered cycle: actual mechanism / original third medium / fixed square\n"+status_text()
        +f"; shared arrow scale {maximum_force:.8g} N = 4 display mm. No contact/clamping claim.", fontsize=12)
    figure.savefig(output/"workpiece_cycle_physical.png", dpi=160); plt.close(figure)

    figure, axes = plt.subplots(3, 3, figsize=(18, 13), layout="constrained")
    d, order = np.asarray([r["d_mm"] for r in rows]), np.arange(len(rows))

    def curve(ax, y, label, color=None, x=d):
        ax.plot(x, y, "o-", label=label, color=color, markersize=4)
        for i in range(1, len(x)):
            ax.annotate("", xy=(x[i], y[i]), xytext=(x[i-1], y[i-1]), arrowprops=dict(arrowstyle="->", color=color or "#777777", lw=.8))

    curve(axes[0, 0], [r["R_input_N"] for r in rows], "actuator R", "#b84b23")
    axes[0, 0].set(title="Input actuator multiplier", ylabel="R [N]")
    for j, axis in enumerate("xy", start=1):
        for name in COMPONENTS:
            curve(axes[0, j], [r[f"lower_body_{name}_F{axis}_N"] for r in rows], name if name != "regularization" else "Hu regularization", COLORS[name])
        axes[0, j].set(title=f"Medium/model on fixed LOWER body: F{axis}", ylabel=f"F{axis} [N]"); axes[0, j].legend(fontsize=8)
    curve(axes[1, 0], [r["full_workpiece_net_force_Fx_N"] for r in rows], "mirrored net Fx = 2Fx; net Fy = 0", "#7b3294")
    curve(axes[1, 0], [r["two_sided_normal_magnitude_sum_N"] for r in rows], "normal magnitude sum = 2|Fy|", "#176a80")
    axes[1, 0].set(title="Mirror-derived quantities; neither is pressure", ylabel="force [N]"); axes[1, 0].legend(fontsize=8)
    for name, color in (("bottom", "#176a80"), ("left", "#b84b23")):
        values = [r[f"clearance_{name}_mm"] if r[f"clearance_{name}_mm"] is not None else np.nan for r in rows]
        curve(axes[1, 1], values, name+" source node window", color, x=order)
    axes[1, 1].set(title="Raster node-window clearance; NOT surface gap", ylabel="diagnostic clearance [mm]", xlabel="accepted index (chronology)"); axes[1, 1].legend(fontsize=8)
    curve(axes[1, 2], [r["q_out_mm"] for r in rows], "+y reference mean = physical mean uy", "#8856a7")
    axes[1, 2].set(title="Free-output measurement; zero spring", ylabel="q_out [mm]")
    for dof in inlet:
        curve(axes[2, 0], [r[f"input_node_{dof//2}_ux_mm"] for r in rows], f"node {dof//2}, weight {model['b_in'][dof]:g}", x=order)
    curve(axes[2, 0], [r["q_in_mm"] for r in rows], "actual weighted mean", "#000000", x=order)
    axes[2, 0].set(title="Input nodes remain free to differ", xlabel="accepted index (chronology)", ylabel="actual ux [mm]"); axes[2, 0].legend(fontsize=8)
    for key, label, color in (("relative_residual", "production relative residual", "#7b3294"), ("relative_global_force_balance", "relative external balance", "#176a80")):
        values = [r[key] if r[key] > 0. else np.nan for r in rows]
        axes[2, 1].semilogy(order, values, "o-", label=label, color=color)
    exact_zeros = [(r["index"], k) for r in rows for k in ("relative_residual", "relative_global_force_balance") if r[k] == 0.]
    axes[2, 1].set(title=f"Saved numerical stopping metrics; exact zeros: {exact_zeros}", xlabel="accepted index (chronology)", ylabel="dimensionless (positive values only)"); axes[2, 1].legend(fontsize=8)
    table = axes[2, 2]; table.axis("off")
    lines = ["FIXED-BODY DIAGNOSTICS — SAVED, NOT RECOMPUTED", "index  max|F−I|  max|J−1|  max|Hu| [1/mm]"]
    lines += [f"{r['index']:3d}  {r['fixed_body_max_abs_F_minus_I']:.2e}  {r['fixed_body_max_abs_J_minus_1']:.2e}  {r['fixed_body_max_abs_Hu_per_mm']:.2e}" for r in rows]
    lines += ["max over accepted states:", f"|P|={max(r['fixed_body_max_abs_first_piola_MPa'] for r in rows):.4e} MPa",
              f"|local body force|={max(r['fixed_body_max_abs_local_force_N'] for r in rows):.4e} N",
              "Holding reaction on model is opposite to force on body.", "Reaction partition: workpiece first; overlaps counted once.",
              "All scalar values and component/partition forces are in CSV.", "No new force, tangent, solver or HP calls in this viewer."]
    table.text(0., 1., "\n".join(lines), va="top", fontsize=8.3, linespacing=1.5, bbox=dict(facecolor="white", edgecolor="none"))
    for ax in axes.flat:
        if ax is not table:
            ax.grid(alpha=.23)
            if ax not in (axes[1, 1], axes[2, 0], axes[2, 1]): ax.set_xlabel("input weighted mean target d [mm]; arrows follow chronology")
    figure.suptitle("Fixed-workpiece force response: saved accepted states; loading and unloading are kept in order\n"+status_text()
        +". Force on body = negative weak-form holding reaction; no contact threshold or pressure.", fontsize=12)
    figure.savefig(output/"workpiece_cycle_response.png", dpi=160); plt.close(figure)

    frames = []
    figure = plt.figure(figsize=(14, 7.5), layout="constrained")
    grid = figure.add_gridspec(2, 2, height_ratios=[1., .23])
    panels = [figure.add_subplot(grid[0, j]) for j in range(2)]
    legend = figure.add_subplot(grid[1, :]); legend.axis("off"); legend.legend(handles=handles, loc="center", ncol=3, fontsize=7.5)
    for index, row in enumerate(rows):
        for ax in panels: ax.clear()
        structure(panels[0], index); structure(panels[1], index, detail_view=True)
        figure.suptitle(f"REAL accepted frame {index+1}/{len(rows)}; {row['leg']}; original index {row['original_target_index']}; d={row['d_mm']:.9g} mm\n"
            +f"R={row['R_input_N']:.8g} N; lower Fx,Fy=({row['lower_body_total_Fx_N']:.8g},{row['lower_body_total_Fy_N']:.8g}) N; "
            +f"min J={row['minimum_J']:.9g}\n"+status_text()+". Actual ×1 only; no interpolation/contact claim.", fontsize=10)
        figure.set_dpi(130); figure.canvas.draw()
        frames.append(Image.fromarray(np.asarray(figure.canvas.buffer_rgba()).copy()).convert("RGB"))
    plt.close(figure)
    palette_source = Image.new("RGB", (frames[0].width, frames[0].height*len(frames)))
    for index, frame in enumerate(frames): palette_source.paste(frame, (0, index*frame.height))
    palette = palette_source.quantize(colors=256)
    frames = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    frames[0].save(output/"workpiece_cycle_actual.gif", save_all=True, append_images=frames[1:], duration=1200, loop=0, optimize=False)
    return dict(representative_accepted_index=representative, geometry_scale=1., actual_GIF_scale=1.,
        supplementary_displacement_scale=magnification, supplementary_force_arrows=False,
        fixed_body_display="Saved native overlay cells; original material mask remains unchanged", pressure_defined=False,
        displacement_color="Element mean of four actual nodal |lift+fluctuation| values [mm]; mechanism viridis / third medium Oranges; same range",
        displacement_color_range_mm=[0., maximum_u], force_arrow_scale_N_per_display_mm=force_scale,
        maximum_shown_force_N=maximum_force, maximum_arrow_display_mm=4., force_scale_shared_over_all_states=True,
        body_arrow="Total medium/model force ON lower body, at lower-body centroid; no mirror factor",
        reaction_arrow_nodes=reactions.tolist(), body_nodal_reaction_arrows=False,
        reaction_sampling="All attached support; remaining non-workpiece fixed nodes at stride 3",
        input_marker_nodes=(inlet//2).tolist(), output_measurement_marker_nodes=out_nodes.tolist(),
        actual_frame_count=len(states), interpolated_frames=0, legend_location="External dedicated strip",
        actual_all_quadrature_J_range=[min(float(s['forces']['J'].min()) for s in states), max(float(s['forces']['J'].max()) for s in states)])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT, help="Saved cycle stage or its result directory")
    parser.add_argument("--output", type=Path, required=True, help="New exclusive output directory")
    parser.add_argument("--magnification", type=float, default=20., help="Supplementary displacement display only")
    args = parser.parse_args()
    require(np.isfinite(args.magnification) and args.magnification > 1., "Supplementary magnification must exceed one")
    model, metadata, result, receipt, states, pins, current_sources = load_saved(args.input.resolve())
    rows, inlet = numerical_rows(model, states)
    output = args.output.resolve(); output.mkdir(parents=True, exist_ok=False)
    display = render(model, metadata, result, receipt, states, rows, inlet, output, args.magnification)
    with (output/"numeric_states.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    frozen = output/"plot_workpiece_cycle_frozen.py"; frozen.write_bytes(Path(__file__).read_bytes())
    require(all(digest(path) == pin for path, pin in pins.items()), "Saved inputs/source changed during display")
    media = {}
    for name in ("workpiece_cycle_physical.png", "workpiece_cycle_response.png", "workpiece_cycle_actual.gif"):
        with Image.open(output/name) as image:
            media[name] = dict(sha256=digest(output/name), pixels=list(image.size), frames=getattr(image, "n_frames", 1))
    require(media["workpiece_cycle_actual.gif"]["frames"] == len(states), "GIF must preserve every actual accepted frame")
    report = dict(schema_version="native-workpiece-cycle-view-1.0", case_family=metadata["task"]["case_family"],
        scope="Saved declared fixed-square native ordered-cycle path only; no independent mechanics qualification",
        production_status=result["status"], wrapper_status=receipt["status"], failure=result["failure"],
        requested_targets_mm=result["targets_mm"], accepted_targets_mm=[row["d_mm"] for row in rows],
        path_completed=result["path_completed"], loading_peak_reached=result["loading_peak_reached"],
        unload_endpoint_reached=result["unload_endpoint_reached"], task_target_executed=result["task_target_executed"],
        geometry_id=metadata["source_geometry"]["geometry_id"], task_sha256=result["task_sha256"],
        grid=metadata["grid"], counts=result["counts"], model_extent=metadata["model_extent"], workpiece=result["workpiece"],
        force_sign=result["workpiece_force_sign"], mirror_convention="Lower (Fx,Fy), upper (Fx,-Fy), full net (2Fx,0); separate normal magnitude sum 2|Fy|",
        clearance_scope=states[0]["record"]["workpiece"]["clearance_scope"], display=display, numerical_states=rows,
        input_files_sha256={path.relative_to(ROOT).as_posix(): pin for path, pin in pins.items()}, input_pins_unchanged_after_plot=True,
        historical_sources=receipt["sources"], current_source_observations=current_sources,
        source_scope="Historical source capsule bytes checked; live source observations are informational only",
        units=dict(length="mm", force="N", stress="MPa", Hu="1/mm", J="dimensionless"),
        force_calls=0, tangent_calls=0, solver_calls=0, HP_calls=0, model_constructions=0,
        contact_clamping_claim=False, independent_HP_qualification_claim=False, HF_qualification_claim=False,
        mirrored_quantities="Only explicitly labelled cached mirror diagnostics; all model fields/actuator/support arrows remain lower-half quantities",
        viewer_sha256=digest(frozen), media=media, numeric_states_csv_sha256=digest(output/"numeric_states.csv"))
    (output/"view_metadata.json").write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps(dict(accepted_frames=len(states), production_status=result["status"], output=str(output), new_mechanics_calls=0)))


if __name__ == "__main__":
    main()
