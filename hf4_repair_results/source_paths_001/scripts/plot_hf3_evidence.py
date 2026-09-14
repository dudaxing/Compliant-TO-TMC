"""Render existing HF-3 evidence; array reductions and sparse matvec only.

No production HF modules, material evaluation, assembly, or equilibrium solver
are imported. Every input is hashed and checked again after plotting. Output
must be a new directory outside all supplied evidence directories.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.colors import LogNorm
import numpy as np
from scipy import sparse


FAMILIES = ("inverter", "gripper")
QUALIFIER = "Modeled lower half; qualification pending (not certified); no workpiece or validated contact-force claim"
COLORS = {"solid": "#465b73", "medium": "#f1e4cd", "support": "#b13b3f",
          "entity": "#087f8c", "background": "#8552a3", "input": "#d050a0", "output": "#17865a"}


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def jsonable(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {key: jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    return value


def write_json(path, value):
    Path(path).write_text(json.dumps(jsonable(value), ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")


class Sources:
    def __init__(self):
        self.records = {}

    def bind(self, path, expected=None):
        path = Path(path).resolve()
        sha = digest(path)
        if expected is not None and sha != expected:
            raise ValueError(f"Input does not match its archived hash: {path}")
        if str(path) in self.records and self.records[str(path)]["sha256"] != sha:
            raise ValueError(f"Input changed while plotting: {path}")
        self.records[str(path)] = {"path_record_only": str(path), "bytes": path.stat().st_size, "sha256": sha}
        return path

    def json(self, path):
        return json.loads(self.bind(path).read_text(encoding="utf-8-sig"))

    def arrays(self, path):
        with np.load(self.bind(path), allow_pickle=False) as arrays:
            result = {name: arrays[name].copy() for name in arrays.files}
        if any(value.dtype.kind not in "biuf" or not np.all(np.isfinite(value)) for value in result.values()):
            raise ValueError(f"Expected finite ordinary numeric arrays: {path}")
        return result

    def matrix(self, path, expected):
        matrix = sparse.load_npz(self.bind(path, expected)).tocsc()
        if not np.all(np.isfinite(matrix.data)):
            raise ValueError(f"Nonfinite sparse matrix: {path}")
        return matrix

    def finish(self):
        for path, record in self.records.items():
            if digest(path) != record["sha256"]:
                raise ValueError(f"Read-only evidence changed: {path}")


def contained(directory, member):
    if not isinstance(member, str) or not member:
        raise ValueError("Missing relative evidence member")
    path = (directory/member).resolve()
    if Path(member).is_absolute() or not path.is_relative_to(directory.resolve()):
        raise ValueError("Evidence member leaves its run directory")
    return path


def save_figure(fig, path):
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def draw_cells(axis, coordinates, connectivity, solid, *, edge=False):
    polygons = coordinates[connectivity]
    axis.add_collection(PolyCollection(polygons[~solid], facecolors=COLORS["medium"],
        edgecolors="#ddd0bb" if edge else "none", linewidths=.25))
    axis.add_collection(PolyCollection(polygons[solid], facecolors=COLORS["solid"],
        edgecolors="#8190a2" if edge else "none", linewidths=.25))


def bounds(axis, coordinates, pad=2):
    low, high = np.min(coordinates, axis=0), np.max(coordinates, axis=0)
    axis.set(xlim=(low[0]-pad, high[0]+pad), ylim=(low[1]-pad, high[1]+pad), xlabel="x [mm]", ylabel="y [mm]")
    axis.set_aspect("equal", adjustable="box")


def mark_regions(axis, coordinates, regions, *, port_labels=False, large=False):
    support = np.array(regions["support"]["attached_nodes"], dtype=int)
    entity = np.array(regions["entity_symmetry"]["attached_nodes"], dtype=int)
    background = np.array(regions["background_symmetry"]["selected_nodes"], dtype=int)
    size = 50 if large else 22
    axis.scatter(*coordinates[support].T, marker="s", s=size, color=COLORS["support"], zorder=5,
                 label=f"solid support ux=uy=0 ({len(support)} nodes)")
    axis.scatter(*coordinates[entity].T, marker="o", s=size, facecolors="none", edgecolors=COLORS["entity"], zorder=6,
                 label="solid-attached entity symmetry uy=0")
    axis.scatter(*coordinates[background].T, marker="+", s=size*.7, color=COLORS["background"], zorder=7,
                 label="background top line uy=0 (all nodes)")
    for name in ("input", "output"):
        port = regions["ports"][name]
        nodes = np.array(port["nodes"], dtype=int)
        xy = coordinates[nodes]
        direction = np.asarray(port["direction"], dtype=float)
        axis.scatter(*xy.T, s=size*.65, facecolors="white", edgecolors=COLORS[name], zorder=8, label=f"{name} reference port")
        axis.quiver(xy[:, 0], xy[:, 1], np.full(3, direction[0]*2.0), np.full(3, direction[1]*2.0),
                    angles="xy", scale_units="xy", scale=1, color=COLORS[name], width=.006, zorder=9)
        if port_labels:
            for point, weight in zip(xy, port["weights"]):
                axis.annotate(f"w={weight:g}", point, xytext=(6, 2), textcoords="offset points", fontsize=8,
                              color=COLORS[name], zorder=10)


def constraints_figure(bridge, output, sources, references):
    fig, axes = plt.subplots(2, 4, figsize=(20, 9), gridspec_kw={"width_ratios": [2.8, 1, 1, 1]})
    raw = {}
    for row, family in enumerate(FAMILIES):
        arrays, report = references[family]
        xy, conn, solid = arrays["coordinates"], arrays["connectivity"].astype(int), arrays["solid"].astype(bool)
        regions = report["regions"]
        overlap = regions["intersections"]["entity_symmetry__background_symmetry"]
        for col, axis in enumerate(axes[row]):
            draw_cells(axis, xy, conn, solid, edge=col != 0)
            mark_regions(axis, xy, regions, port_labels=col in (2, 3), large=col != 0)
            axis.set_aspect("equal", adjustable="box")
            axis.set(xlabel="x [mm]", ylabel="y [mm]")
        bounds(axes[row, 0], xy)
        axes[row, 0].set_title(f"{family}: native solid / third medium\n{len(overlap)} entity/background DOFs shared; each fixed DOF counted once", fontsize=11)
        axes[row, 1].set(xlim=(-1, 5), ylim=(-1, 9), title="Solid support detail")
        for col, name in ((2, "input"), (3, "output")):
            nodes = np.array(regions["ports"][name]["nodes"], dtype=int)
            center = xy[nodes].mean(axis=0)
            axes[row, col].set(xlim=(center[0]-3, center[0]+5), ylim=(center[1]-4, center[1]+4), title=f"{name} port; reference direction")
        raw[family] = {"geometry_id": report["geometry_id"], "regions": regions,
                       "source_full_midline_note": "Historical full_midline is inert; the task separately declares the full background top boundary"}
        np.savez_compressed(output/f"{family}_constraints_data.npz", coordinates=xy, connectivity=conn, solid=solid,
            support_nodes=np.array(regions["support"]["attached_nodes"]),
            entity_symmetry_nodes=np.array(regions["entity_symmetry"]["attached_nodes"]),
            background_nodes=np.array(regions["background_symmetry"]["selected_nodes"]),
            fixed_dofs=np.array(regions["fixed_dofs"]), entity_background_shared_dofs=np.array(overlap),
            input_nodes=np.array(regions["ports"]["input"]["nodes"]), input_weights=np.array(regions["ports"]["input"]["weights"]),
            output_nodes=np.array(regions["ports"]["output"]["nodes"]), output_weights=np.array(regions["ports"]["output"]["weights"]))
    handles, labels = axes[0, 0].get_legend_handles_labels()
    # The support count differs by family and is stated separately in raw data.
    counts = {family: len(references[family][1]["regions"]["support"]["attached_nodes"]) for family in FAMILIES}
    labels[0] = f"solid-attached support ux=uy=0: inverter {counts['inverter']} / gripper {counts['gripper']} nodes"
    fig.legend(handles, labels, loc="lower center", ncol=3, fontsize=9, bbox_to_anchor=(.5, -.01))
    fig.suptitle("HF-3 physical constraints and original weighted ports\n"+QUALIFIER, fontsize=13)
    fig.text(.5, .045, "Arrows show directions, not displacement or force magnitudes. Labels are normalized reference weights.\n"
             "Historical source full_midline supplies no implicit runtime constraints; overlapping circles and + symbols denote deduplicated DOFs.", ha="center", fontsize=9)
    fig.subplots_adjust(top=.86, bottom=.17, wspace=.32, hspace=.38)
    save_figure(fig, output/"regions_and_background_constraints.png")
    write_json(output/"constraints_plot_data.json", {"cases": raw, "sources": list(sources.records.values())})


def ratio(numerator, denominator):
    return None if denominator == 0 else float(numerator/denominator)


def initial_bias(bridge, output, sources, references):
    names = ("solid_material", "medium_material", "HuHu")
    files = ("K0_solid_material_full", "K0_medium_material_full", "K0_HuHu_full")
    values = {}
    for family in FAMILIES:
        arrays, report = references[family]
        folder = bridge/family/"linear"
        u = arrays["K0_u"]
        matrices = {name: sources.matrix(folder/(file+".npz"), report["matrix_files"][file]["sha256"])
                    for name, file in zip(names, files)}
        total = sources.matrix(folder/"K0_full.npz", report["matrix_files"]["K0_full"]["sha256"])
        if total.shape != (len(u), len(u)):
            raise ValueError("K0 response/matrix shape mismatch")
        quadratic = {name: float(u @ (matrix @ u)) for name, matrix in matrices.items()}
        total_quadratic = float(u @ (total @ u))
        if total_quadratic == 0 or not np.isfinite(total_quadratic):
            raise ValueError("Zero/nonfinite K0 quadratic reference cannot define contribution fractions")
        fractions = {name: value/total_quadratic for name, value in quadratic.items()}
        R, Rsolid = float(arrays["K0_R"]), float(arrays["solid_3x3_R"])
        q, qsolid = float(arrays["K0_q"]), float(arrays["solid_3x3_q"])
        values[family] = {
            "reference_displacement_mm": 1.0, "reference_displacement_is_linear_derivative_only": True,
            "quadratic_forms_N_mm": quadratic, "total_quadratic_form_N_mm": total_quadratic,
            "fraction_of_uTK0u": fractions, "equivalent_input_stiffness_contribution_N_per_mm": quadratic,
            "stiffness_normalization": "Each quadratic form divided by (1 mm)^2; input reference force divided by 1 mm",
            "sum_components_minus_total_N_mm": sum(quadratic.values())-total_quadratic,
            "relative_decomposition_gap": (sum(quadratic.values())-total_quadratic)/abs(total_quadratic),
            "input_stiffness_N_per_mm": R, "solid_only_input_stiffness_N_per_mm": Rsolid,
            "quadratic_stiffness_minus_input_stiffness_N_per_mm": total_quadratic-R,
            "input_stiffness_K0_over_solid": ratio(R, Rsolid),
            "output_gain_K0": q, "output_gain_solid": qsolid, "output_gain_K0_over_solid": ratio(q, qsolid),
            "largest_absolute_quadratic_contributor": max(names, key=lambda name: abs(quadratic[name])),
            "HuHu_over_material_quadratic_ratio": ratio(quadratic["HuHu"], quadratic["solid_material"]+quadratic["medium_material"]),
            "existing_model_bias_assessment": report["A_vs_B_model_bias"],
            "interpretation": "Contributions are evaluated on the same stored K0_u, not Frobenius matrix norms or separately re-solved mechanisms. HuHu is an initial-tangent quadratic form, not nonlinear stored energy; no new dominance cutoff is imposed.",
        }
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8), constrained_layout=True)
    x = np.arange(2)
    bottom = np.zeros(2)
    for name, color in zip(names, (COLORS["solid"], "#c79746", "#b95750")):
        heights = np.array([100*values[family]["fraction_of_uTK0u"][name] for family in FAMILIES])
        axes[0].bar(x, heights, bottom=bottom, color=color, label=name.replace("_", " "))
        bottom += heights
    axes[0].set(xticks=x, xticklabels=FAMILIES, ylabel="Share of uᵀK₀u [%]", title="Actual K0 response contributions")
    axes[0].legend(fontsize=8)
    for axis, main_key, solid_key, title, unit in (
        (axes[1], "input_stiffness_N_per_mm", "solid_only_input_stiffness_N_per_mm", "Input stiffness", "R / d [N/mm]"),
        (axes[2], "output_gain_K0", "output_gain_solid", "Signed output gain", "q_out / d [dimensionless]")):
        axis.bar(x-.18, [values[f][main_key] for f in FAMILIES], width=.36, color=COLORS["solid"], label="full TMC K0")
        axis.bar(x+.18, [values[f][solid_key] for f in FAMILIES], width=.36, color="#969da5", label="solid only")
        axis.set(xticks=x, xticklabels=FAMILIES, title=title, ylabel=unit)
        axis.axhline(0, color="black", linewidth=.5)
        axis.legend(fontsize=8)
    fig.suptitle("HF-3 model components: existing unit linear responses, no re-solve\n"+QUALIFIER, fontsize=12)
    save_figure(fig, output/"initial_model_components_and_bias.png")

    diagnostic_folder = bridge/"gripper/background_diagnostic"
    diagnostic_report = sources.json(diagnostic_folder/"summary.json")
    diagnostic = sources.arrays(diagnostic_folder/"unit_response.npz")
    baseline = values["gripper"]
    released = diagnostic["released_dofs"].astype(int)
    bg_values = {"scope": "one initial-tangent boundary diagnostic; no nonlinear variant run",
        "released_dofs": released, "released_node_coordinates_mm": references["gripper"][0]["coordinates"][released//2],
        "main_R_per_d_N_per_mm": baseline["input_stiffness_N_per_mm"], "released_R_per_d_N_per_mm": float(diagnostic["R"]),
        "main_q_per_d": baseline["output_gain_K0"], "released_q_per_d": float(diagnostic["q"]),
        "input_stiffness_release_over_main": ratio(float(diagnostic["R"]), baseline["input_stiffness_N_per_mm"]),
        "output_gain_release_over_main": ratio(float(diagnostic["q"]), baseline["output_gain_K0"]),
        "archived_comparisons": diagnostic_report["comparison_to_main_background"]}
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5), constrained_layout=True)
    for axis, main_key, release_key, unit, title in (
        (axes[0], "main_R_per_d_N_per_mm", "released_R_per_d_N_per_mm", "R / d [N/mm]", "Input stiffness"),
        (axes[1], "main_q_per_d", "released_q_per_d", "q_out / d", "Signed output gain")):
        axis.bar([0, 1], [bg_values[main_key], bg_values[release_key]], color=[COLORS["background"], "#a9a9a9"])
        axis.set(xticks=[0, 1], xticklabels=["Main: full top uy=0", "Release background x>60"], ylabel=unit, title=title)
        axis.tick_params(axis="x", labelsize=8)
        axis.axhline(0, color="black", linewidth=.5)
    fig.suptitle(f"Gripper: effect of releasing {len(released)} background uy DOFs; entity tags unchanged\n"+QUALIFIER, fontsize=11)
    save_figure(fig, output/"gripper_background_effect.png")
    write_json(output/"initial_model_components_and_bias.json", {"cases": values, "gripper_background_effect": bg_values,
        "operation": "stored vectors, reductions and sparse matvec only; no stiffness assembly or solve", "sources": list(sources.records.values())})


def cell_J_collection(axis, polygons, values, label, cmap):
    if not len(values):
        axis.text(.5, .5, "No cells in this region", ha="center", transform=axis.transAxes)
        return
    low, high = float(values.min()), float(values.max())
    if low <= 0:
        raise ValueError("Cannot render a purported accepted state with nonpositive J")
    if low == high:
        low, high = .99*low, 1.01*high
    collection = PolyCollection(polygons, array=values, cmap=cmap, norm=LogNorm(low, high), edgecolors="none")
    axis.add_collection(collection)
    axis.figure.colorbar(collection, ax=axis, shrink=.75, label=label)


def full_path_figures(run, output, sources, references, index):
    result = sources.json(run/"result.json")
    sources.json(run/"metadata.json")
    target = output/f"path_{index:02d}"
    target.mkdir()
    state = {"source_run_record_only": str(run), "numerics": result["numerics"], "qualification": result["qualification"],
             "task_id": result.get("task_id"), "geometry_id": result.get("geometry_id")}
    if not result["path"].get("model_file") or not result["path"].get("arrays_file"):
        write_json(target/"plot_data.json", {**state, "status": "no_mapped_path_available", "sources": list(sources.records.values())})
        return state
    model = sources.arrays(contained(run, result["path"]["model_file"]))
    arrays = sources.arrays(contained(run, result["path"]["arrays_file"]))
    d = arrays["d"]
    if not len(d):
        write_json(target/"plot_data.json", {**state, "status": "no_accepted_states", "sources": list(sources.records.values())})
        return state
    xy, conn, solid = model["coordinates"], model["connectivity"].astype(int), model["solid"].astype(bool)
    free = model["free_dofs"].astype(int)
    if arrays["J"].shape != (len(d), len(conn), 9) or arrays["u"].shape != (len(d), 2*len(xy)):
        raise ValueError("Path geometry/array shape mismatch")
    if len(d) != result["path"]["accepted_step_count"] or np.any(np.diff(d) <= 0) or np.any(arrays["J"] <= 0):
        raise ValueError("Inconsistent accepted-state path")
    Jsolid = np.min(arrays["J"][:, solid], axis=(1, 2)) if np.any(solid) else None
    Jmedium = np.min(arrays["J"][:, ~solid], axis=(1, 2)) if np.any(~solid) else None
    energies = arrays["material_energy"]
    derived = {"d_mm": d, "q_out_mm": arrays["q_out"], "R_input_N": arrays["R_input"],
        "is_original_target": arrays["is_original_target"], "solid_material_energy_N_mm": energies[:, solid].sum(axis=1),
        "medium_material_energy_N_mm": energies[:, ~solid].sum(axis=1),
        "material_full_force_norm_N": np.linalg.norm(arrays["material_internal_force"], axis=1),
        "material_free_force_norm_N": np.linalg.norm(arrays["material_internal_force"][:, free], axis=1),
        "HuHu_full_force_norm_N": np.linalg.norm(arrays["regularization_internal_force"], axis=1),
        "HuHu_free_force_norm_N": np.linalg.norm(arrays["regularization_internal_force"][:, free], axis=1),
        "production_relative_force_residual": arrays["relative_residual"],
        "production_relative_global_force_balance": arrays["relative_global_force_balance"],
        "relative_mean_constraint_error": np.abs(arrays["constraint_residual"])/arrays["displacement_scale"],
        "terminal_deformed_coordinates_mm": xy+arrays["u"][-1].reshape(-1, 2),
        "terminal_min_quadrature_J_per_cell": arrays["J"][-1].min(axis=1)}
    if Jsolid is not None:
        derived["solid_min_J"] = Jsolid
    if Jmedium is not None:
        derived["medium_min_J"] = Jmedium
    np.savez_compressed(target/"plot_arrays.npz", **derived)
    family = result.get("task_config", {}).get("case_family", "project")
    original = arrays["is_original_target"].astype(bool)
    fig, axes = plt.subplots(2, 3, figsize=(14, 8), constrained_layout=True)
    for axis, values, ylabel in ((axes[0, 0], arrays["q_out"], "q_out [mm]"), (axes[0, 1], arrays["R_input"], "R_input [N]")):
        axis.plot(d, values, color=COLORS["solid"], linewidth=1.4, label="all accepted states")
        axis.scatter(d[original], values[original], s=12, color=COLORS["solid"], label="original targets")
        if np.any(~original):
            axis.scatter(d[~original], values[~original], marker="x", s=18, color="#c55", label="bisection substeps")
        axis.set_ylabel(ylabel)
    if family in references and result.get("task_sha256") == references[family][1]["task_sha256"]:
        linear = references[family][0]
        axes[0, 0].plot(d, d*float(linear["K0_q"]), "--", color="0.5", label="own initial tangent")
        axes[0, 1].plot(d, d*float(linear["K0_R"]), "--", color="0.5", label="own initial tangent")
    for values, label, color in ((Jsolid, "solid", COLORS["solid"]), (Jmedium, "third medium", "#b77d24")):
        if values is not None:
            axes[0, 2].plot(d, values, label=label, color=color)
    axes[0, 2].set(ylabel="Minimum quadrature J", yscale="log")
    axes[1, 0].plot(d, derived["solid_material_energy_N_mm"], label="solid material")
    axes[1, 0].plot(d, derived["medium_material_energy_N_mm"], label="third-medium material")
    axes[1, 0].set(ylabel="Material energy [N mm]", title="HuHu has no stored nonlinear potential")
    axes[1, 0].set_yscale("symlog", linthresh=1e-16)
    axes[1, 1].plot(d, derived["material_free_force_norm_N"], label="material ||f_free||")
    axes[1, 1].plot(d, derived["HuHu_free_force_norm_N"], label="HuHu ||f_free||")
    axes[1, 1].set(ylabel="Assembled component force norm [N]")
    axes[1, 1].set_yscale("symlog", linthresh=1e-12)
    axes[1, 2].plot(d, derived["production_relative_force_residual"], label="free force residual")
    axes[1, 2].plot(d, derived["production_relative_global_force_balance"], label="global force balance")
    axes[1, 2].plot(d, derived["relative_mean_constraint_error"], label="mean constraint error")
    axes[1, 2].set(ylabel="Production normalized diagnostics")
    axes[1, 2].set_yscale("symlog", linthresh=1e-16)
    for axis in axes.flat:
        axis.set_xlabel("Prescribed mean input d [mm]")
        axis.grid(True, alpha=.2)
        axis.legend(fontsize=7)
    status = result["numerics"]["status"]
    qualification = result["qualification"]["status"]
    fig.suptitle(f"{family}: archived {status}; qualification {qualification}; no independent HP claim from this plot\n"
                 "Modeled half, no automatic doubling; no workpiece or validated contact-force claim", fontsize=12)
    save_figure(fig, target/"accepted_path_diagnostics.png")

    deformed = derived["terminal_deformed_coordinates_mm"]
    polygons = deformed[conn]
    fig, axes = plt.subplots(1, 3, figsize=(15, 5), constrained_layout=True)
    axes[0].add_collection(PolyCollection(xy[conn][solid], facecolors="none", edgecolors="#9b9b9b", linewidths=.35, label="reference solid"))
    axes[0].add_collection(PolyCollection(polygons[solid], facecolors=COLORS["solid"], edgecolors="none", alpha=.75, label="deformed solid"))
    axes[0].set_title(f"Last accepted d={float(d[-1]):.6g} mm\nDisplacement display scale = 1")
    axes[0].legend(fontsize=8)
    Jcell = derived["terminal_min_quadrature_J_per_cell"]
    cell_J_collection(axes[1], polygons[solid], Jcell[solid], "Solid: min J in each cell", "viridis")
    cell_J_collection(axes[2], polygons[~solid], Jcell[~solid], "Third medium: min J in each cell", "magma")
    axes[1].set_title("Solid J on deformed cells")
    axes[2].set_title("Third-medium J on deformed cells")
    for axis in axes:
        bounds(axis, np.vstack((xy, deformed)))
    fig.suptitle(f"{family}: actual-scale accepted-state geometry; separate J color scales\n"
                 f"Production status {status}; qualification {qualification}; J>0 does not establish contact accuracy", fontsize=12)
    save_figure(fig, target/"last_accepted_deformation_and_J.png")
    state.update(status="plotted_accepted_states", accepted_count=len(d), reached_input_mm=float(d[-1]),
                 displacement_display_scale=1, J_plot_value="minimum of nine stored quadrature determinants per cell",
                 force_norm_scope="both full and free material/HuHu norms saved; free component norms plotted",
                 independent_precision="not_assessed_by_plotting", sources=list(sources.records.values()))
    write_json(target/"plot_data.json", state)
    return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bridge", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--path", type=Path, action="append", default=[], help="Repeat for existing public project result directories")
    args = parser.parse_args()
    bridge, output = args.bridge.resolve(), args.output.resolve()
    paths = [path.resolve() for path in args.path]
    if any(output.is_relative_to(source) for source in [bridge, *paths]):
        parser.error("--output must be outside all input evidence directories")
    output.mkdir(parents=True, exist_ok=False)
    sources = Sources()
    sources.bind(Path(__file__))
    try:
        references = {}
        for family in FAMILIES:
            folder = bridge/family/"linear"
            references[family] = (sources.arrays(folder/"unit_responses.npz"), sources.json(folder/"reference_summary.json"))
        constraints_figure(bridge, output, sources, references)
        initial_bias(bridge, output, sources, references)
        path_reports = [full_path_figures(path, output, sources, references, i) for i, path in enumerate(paths, start=1)]
        sources.finish()
        artifacts = [{"path": path.relative_to(output).as_posix(), "sha256": digest(path), "bytes": path.stat().st_size}
                     for path in sorted(output.rglob("*")) if path.is_file()]
        write_json(output/"evidence_manifest.json", {"status": "complete", "schema_version": "hf3-evidence-plots-1.0",
            "operation": "read-only arrays and sparse quadratic forms; no assembly, material evaluation, or linear/nonlinear solve",
            "sources_unchanged": True, "sources": list(sources.records.values()), "files": artifacts,
            "optional_paths": path_reports, "physical_contact_accuracy": "not_validated", "qualification_promoted": False})
        return 0
    except (ValueError, OSError, KeyError, RuntimeError, ArithmeticError) as error:
        write_json(output/"plot_failure.json", {"status": "incomplete", "type": type(error).__name__, "message": str(error),
                    "sources_read": list(sources.records.values()), "note": "Existing output artifacts retained; input evidence never changed"})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
