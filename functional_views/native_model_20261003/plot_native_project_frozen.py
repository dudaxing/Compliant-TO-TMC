"""Inspect saved native TEST models, materials and actual constraint groups.

Only model.json/NPZ, saved task JSON and HF geometry snapshots are read. No
project constructor, TMC, force, deformation evaluator or solver is imported.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np

ROOT = next(parent for parent in Path(__file__).resolve().parents
            if (parent / "hf_repo/src/hf_eval/data.py").is_file())
sys.path.insert(0, str(ROOT / "hf_repo/src"))
from hf_eval.data import canonical_hash, load_geometry

ALIASES = ("inverter_canonical", "gripper_canonical", "gripper_native_fine")
GROUP_COLORS = {"support": "#218053", "entity_symmetry": "#7262a3", "background_symmetry": "#2668a5"}
PORT_COLORS = {"input": "#137d99", "output": "#a83c79"}


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_saved(stage, row):
    alias = row["alias"]
    path = stage / "models" / alias / "model.json"
    metadata = read_json(path)
    require(metadata["schema_version"] == "hf-native-project-model-1.0", alias + ": schema differs")
    require(metadata["response_evaluated"] is False and all(metadata[name] is True for name in
            ("constraints_applied", "material_assigned", "task_created")), alias + ": saved construction flags differ")
    require(canonical_hash({k: v for k, v in metadata.items() if k != "descriptor_sha256"})
            == metadata["descriptor_sha256"], alias + ": model descriptor hash differs")
    npz = path.parent / metadata["arrays"]["path"]
    require(digest(npz) == metadata["arrays"]["sha256"], alias + ": NPZ hash differs")
    with np.load(npz, allow_pickle=False) as archive:
        require(set(archive.files) == set(metadata["arrays"]["fields"]), alias + ": array declarations differ")
        arrays = {name: archive[name].copy() for name in archive.files}
    for name, values in arrays.items():
        field = dict(dtype=values.dtype.name, shape=list(values.shape), sha256=sha256(values.tobytes(order="C")).hexdigest())
        require(field == metadata["arrays"]["fields"][name], alias + ": " + name + " declaration differs")
    source = metadata["source_geometry"]
    source_path = path.parent / source["snapshot"]["descriptor"]
    source_npz = path.parent / source["snapshot"]["arrays"]
    require(digest(source_path) == source["descriptor_file_sha256"] == row["geometry_file_sha256"]
            and digest(source_npz) == source["arrays_sha256"] == row["geometry_npz_sha256"], alias + ": source snapshot differs")
    geometry = load_geometry(source_path)
    require(geometry.geometry_id == source["geometry_id"] == row["geometry_id"]
            and geometry.metadata["descriptor_sha256"] == source["descriptor_sha256"], alias + ": source identity differs")
    task_path = stage / "tasks" / (alias + ".json")
    task = read_json(task_path)
    require(digest(task_path) == row["task_file_sha256"] and task == metadata["task"]
            and canonical_hash(task) == metadata["task_sha256"], alias + ": configured task differs")
    require(task["purpose"] == "construction_test_only" and task["analysis_grid"] == {"policy": "native"}, alias + ": TEST scope differs")
    require(task["input"]["control"] == "average_displacement" and task["workpiece"] is None
            and task["output"]["spring_N_per_mm"] == float(arrays["k_out"]) == 0., alias + ": control differs")
    require(np.array_equal(arrays["solid"], geometry.solid.ravel().astype(bool)), alias + ": source solid cells differ")
    regions = metadata["region_metadata"]
    groups = {name: np.asarray(regions[name]["dofs"], dtype=int) for name in GROUP_COLORS}
    require(np.array_equal(np.unique(np.concatenate(list(groups.values()))), arrays["fixed_dofs"]), alias + ": merged constraints differ")
    require(not np.any(arrays["b_in"][arrays["fixed_dofs"]]) and not np.any(arrays["b_out"][arrays["fixed_dofs"]]), alias + ": port direction is fixed")
    require(float(arrays["force_scale_per_length"]) == task["material"]["E_MPa"]*float(arrays["thickness"]), alias + ": reference scale differs")
    files = (path, npz, source_path, source_npz, task_path)
    ports = {}
    for name in ("input", "output"):
        port = regions["ports"][name]
        nodes = np.asarray(port["nodes"], dtype=int)
        ports[name] = dict(nodes=nodes.tolist(), coordinates_mm=arrays["coordinates"][nodes].tolist(),
            weights=port["weights"], direction_reference=port["direction"],
            nonzero_dofs=np.flatnonzero(arrays["b_in" if name == "input" else "b_out"]).tolist())
    record = dict(alias=alias, geometry_id=geometry.geometry_id, task_sha256=metadata["task_sha256"],
        model_counts=dict(elements=len(arrays["connectivity"]), nodes=len(arrays["coordinates"]), dofs=len(arrays["b_in"]),
                          fixed_dofs=len(arrays["fixed_dofs"]), free_dofs=len(arrays["free_dofs"])),
        material=metadata["material"], grid=geometry.grid, configured_input_mm=task["input"]["target_mm"], target_executed=False,
        groups={name: dict(nodes=np.unique(dofs//2).tolist(), dofs=dofs.tolist()) for name, dofs in groups.items()},
        intersections=regions["intersections"], ports=ports, output_spring_N_per_mm=float(arrays["k_out"]),
        source_background=geometry.metadata.get("provenance", {}).get("lf_v2", {}).get("descriptor", {}).get("regions_mm", {}).get("symmetry_background"),
        input_files_sha256={p.relative_to(stage).as_posix(): digest(p) for p in files})
    return dict(alias=alias, arrays=arrays, metadata=metadata, geometry=geometry, task=task, groups=groups, record=record)


def draw_material(ax, case):
    geometry = case["geometry"]
    x, y = geometry.grid["origin_mm"]
    width, height = geometry.grid["extent_mm"]
    colors = np.empty((*geometry.solid.shape, 3))
    colors[:] = [220/255, 235/255, 248/255]
    colors[geometry.solid.astype(bool)] = [35/255, 61/255, 89/255]
    ax.imshow(colors, origin="lower", interpolation="nearest", extent=(x, x+width, y, y+height))
    ax.set_aspect("equal")
    ax.set_xlabel("x [mm]")
    ax.set_ylabel("y [mm]")


def draw_bcs(ax, case):
    coordinates = case["arrays"]["coordinates"]
    # Groups come from the constructed task, not the LF source candidate sets.
    for name in ("background_symmetry", "entity_symmetry", "support"):
        nodes = np.unique(case["groups"][name]//2)
        xy = coordinates[nodes]
        color = GROUP_COLORS[name]
        if name == "background_symmetry":
            ax.scatter(xy[:, 0], xy[:, 1], s=18, facecolors="none", edgecolors=color, lw=.8, zorder=3)
        else:
            ax.scatter(xy[:, 0], xy[:, 1], s=8 if name == "entity_symmetry" else 23,
                       marker="o" if name == "entity_symmetry" else "s", color=color, zorder=4)
    for name in ("input", "output"):
        port = case["record"]["ports"][name]
        xy = np.asarray(port["coordinates_mm"])
        direction = np.asarray(port["direction_reference"])
        ax.scatter(xy[:, 0], xy[:, 1], s=22, color=PORT_COLORS[name], zorder=6)
        ax.annotate("", xy=xy.mean(axis=0)+5*direction, xytext=xy.mean(axis=0),
                    arrowprops=dict(arrowstyle="->", color=PORT_COLORS[name], lw=1.5), zorder=6)
    background = case["record"]["source_background"]
    if background is not None:
        ax.plot([background["start_exclusive_mm"], background["end_inclusive_mm"]], [40., 40.],
                color="#aa806d", lw=.8, ls="--", zorder=1)
        ax.text(70, 43, "LF (60,80] provenance only", ha="center", fontsize=8, color="#8d6b5a")
    ax.set_xlim(-3, 88)
    ax.set_ylim(-2, 46)


def configuration_text(case):
    task, record = case["task"], case["record"]
    counts = record["model_counts"]
    lines = ["Explicit construction TEST; no response evaluated", f"Native {case['geometry'].grid['shape_yx']} cells (ny,nx)",
        f"{counts['elements']} elements / {counts['nodes']} nodes / {counts['dofs']} DOFs",
        f"Merged fixed: {counts['fixed_dofs']}; free: {counts['free_dofs']}", "", "Applied homogeneous Dirichlet groups:"]
    for name, label in (("support", "support ux=uy=0"), ("entity_symmetry", "entity uy=0"), ("background_symmetry", "task background uy=0")):
        group = record["groups"][name]
        lines.append(f"  {label}: {len(group['nodes'])} nodes / {len(group['dofs'])} DOFs")
    overlap = len(set(record["groups"]["entity_symmetry"]["dofs"]) & set(record["groups"]["background_symmetry"]["dofs"]))
    lines += [f"Entity/background overlap: {overlap} DOFs; merged once", "",
        f"Configured input: sum(w_i ux_i) = {task['input']['target_mm']:g} mm",
        "Individual port ux values are not prescribed separately", "Stored target has not been executed",
        "Output: free along reference direction; k_out=0", "", f"E={task['material']['E_MPa']:g} MPa; nu={task['material']['nu']:g}; plane strain",
        f"t={float(case['arrays']['thickness']):g} mm; medium gamma={task['third_medium']['gamma']:g}",
        f"alpha={task['regularization']['alpha']:g}; Lr={task['regularization']['length_mm']:g} mm",
        f"kr={float(case['arrays']['kr']):.10g} MPa mm^2 (not gamma-scaled)", "H2/H3 study decisions remain pending; workpiece=None"]
    if case["alias"] == "gripper_native_fine":
        lines.append("Different original design; not a coarse/fine convergence pair")
    return "\n".join(lines)


def plot_models(cases, output):
    fig, axes = plt.subplots(3, 2, figsize=(14, 13.5), layout="constrained", gridspec_kw={"width_ratios": [1.5, 1]})
    fig.suptitle("Configured native TEST models: physical geometry x1 and task-selected boundary conditions\n"
                 "Stored average input and free output; arrows are reference directions, no force or deformation", fontsize=13)
    for row, case in enumerate(cases):
        draw_material(axes[row, 0], case)
        draw_bcs(axes[row, 0], case)
        axes[row, 0].set_title(case["alias"] + " | explicit native construction TEST", fontsize=10)
        axes[row, 1].axis("off")
        axes[row, 1].text(0., 1., configuration_text(case), transform=axes[row, 1].transAxes, va="top", fontsize=9, linespacing=1.35)
    legend = [Patch(color="#233d59", label="Solid material"), Patch(color="#dcebf8", label="Third medium"),
        Line2D([], [], ls="", marker="s", color=GROUP_COLORS["support"], label="Applied support ux,uy=0"),
        Line2D([], [], ls="", marker="o", color=GROUP_COLORS["entity_symmetry"], label="Applied entity uy=0"),
        Line2D([], [], ls="", marker="o", markerfacecolor="none", color=GROUP_COLORS["background_symmetry"], label="Explicit task background uy=0"),
        Line2D([], [], ls="--", color="#aa806d", label="LF source background provenance")]
    fig.legend(handles=legend, loc="outside lower center", ncol=3, fontsize=9)
    fig.savefig(output / "native_model_applied_bcs.png", dpi=150)
    plt.close(fig)


def plot_ports(cases, output):
    fig, axes = plt.subplots(3, 2, figsize=(12, 11.5), layout="constrained")
    fig.suptitle("Weighted mean input and free output: configured equations on native nodes\n"
                 "Node values are unsolved. Zero inactive components below refer to actual fixed DOFs", fontsize=13)
    for row, case in enumerate(cases):
        coordinates, fixed = case["arrays"]["coordinates"], set(case["arrays"]["fixed_dofs"].tolist())
        dx, dy = case["geometry"].grid["cell_size_mm"]
        for col, name in enumerate(("input", "output")):
            ax = axes[row, col]
            draw_material(ax, case)
            port = case["record"]["ports"][name]
            nodes = port["nodes"]
            xy = coordinates[nodes]
            direction = port["direction_reference"]
            component = 0 if direction[0] else 1
            other = 1-component
            color = PORT_COLORS[name]
            ax.scatter(xy[:, 0], xy[:, 1], s=35, color=color, zorder=5)
            for node, point, weight in zip(nodes, xy, port["weights"]):
                inactive = ("uy" if other else "ux") + ("=0" if 2*node+other in fixed else " unconstrained")
                value = weight*direction[component]
                label = f"w={weight:g}; b_{'ux' if component==0 else 'uy'}={value:g}\n{inactive}"
                ax.annotate(label, point, xytext=(8, 0), textcoords="offset points", fontsize=8, color=color, va="center",
                            bbox=dict(facecolor="white", edgecolor="none", alpha=.9, pad=1.5))
            condition = f"sum(w ux)={case['task']['input']['target_mm']:g} mm stored; values unsolved" if name == "input" else "free along reference; k_out=0"
            ax.set_title(f"{case['alias']} | {name}\n{condition}\n{len(nodes)} nodes, sum(w)=1, reference {direction}", fontsize=9)
            ax.set_xlim(xy[:, 0].min()-1.2*dx, xy[:, 0].max()+5.5*dx)
            ax.set_ylim(xy[:, 1].min()-.8*dy, xy[:, 1].max()+.8*dy)
            ax.tick_params(labelsize=8)
            ax.grid(alpha=.14)
    fig.savefig(output / "native_model_port_equations.png", dpi=150)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "lf_data_preparation/native_model_001")
    parser.add_argument("--output", type=Path, required=True, help="New directory")
    args = parser.parse_args()
    stage, output = args.input.resolve(), args.output.resolve()
    inventory_path = stage / "input_inventory.json"
    inventory = read_json(inventory_path)
    by_alias = {row["alias"]: row for row in inventory["cases"]}
    require(set(by_alias) == set(ALIASES), "Expected three explicit TEST cases")
    cases = [load_saved(stage, by_alias[alias]) for alias in ALIASES]
    output.mkdir(parents=True, exist_ok=False)
    plot_models(cases, output)
    plot_ports(cases, output)
    frozen = output / "plot_native_project_frozen.py"
    frozen.write_bytes(Path(__file__).read_bytes())
    helper = output / "helpers" / "data.py"
    helper.parent.mkdir()
    helper.write_bytes((ROOT / "hf_repo/src/hf_eval/data.py").read_bytes())
    metadata = dict(schema_version="native-project-model-view-1.0", input_layout="models/<alias>/model.json", scope="Saved TEST model configuration only; no construction/response/force/assembly/HP/solver",
        input_inventory_sha256=digest(inventory_path), cases=[case["record"] for case in cases], geometry_scale=1., reference_arrow_length_mm=5.,
        arrows_meaning="reference direction only", target_executed=False, force_evaluated=False, workpiece_present=False,
        study_H2_H3_decisions="pending", fine_is_another_design=True, mesh_convergence_claim=False, half_model_quantities_doubled=False,
        viewer_sha256=digest(frozen), frozen_helpers_sha256={"helpers/data.py": digest(helper)},
        media_sha256={path.name: digest(path) for path in sorted(output.glob("*.png"))})
    (output / "view_metadata.json").write_text(json.dumps(metadata, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps(dict(output=str(output), cases=3, configured_fixed_dofs=[case["record"]["model_counts"]["fixed_dofs"] for case in cases], response_calls=0)))


if __name__ == "__main__":
    main()
