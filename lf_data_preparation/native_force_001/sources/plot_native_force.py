"""Visualize saved native supplied-state forces; no mechanics evaluation.

All colors use actual saved values. Displacement magnification and the common
internal-force glyph scale are display conventions, never physical solutions.
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
from matplotlib.collections import LineCollection
from matplotlib.colors import LogNorm, Normalize
from matplotlib.ticker import FormatStrFormatter
import numpy as np

ROOT = next(parent for parent in Path(__file__).resolve().parents
            if (parent / "hf_repo/src/hf_eval/data.py").is_file())
sys.path.insert(0, str(ROOT / "hf_repo/src"))
from hf_eval.data import canonical_hash, load_geometry

ALIASES = ("inverter_canonical", "gripper_canonical", "gripper_native_fine")
COMPONENTS = ("material", "regularization", "total")
AMPLIFICATION = 200.


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_archive(path, declaration):
    require(digest(path) == declaration["sha256"], path.name + ": NPZ SHA differs")
    with np.load(path, allow_pickle=False) as saved:
        require(set(saved.files) == set(declaration["fields"]), path.name + ": declarations differ")
        arrays = {name: saved[name].copy() for name in saved.files}
    for name, values in arrays.items():
        actual = dict(dtype=values.dtype.name, shape=list(values.shape), sha256=sha256(values.tobytes(order="C")).hexdigest())
        require(actual == declaration["fields"][name], path.name + ": " + name + " differs")
    return arrays


def load_case(stage, row, production):
    directory = stage / row["result_directory"]
    path = directory / "result.json"
    result = read_json(path)
    label = row["alias"] + "/" + row["state_name"]
    require(production["status"] == "pass" and production["invocations"] == 1
            and digest(path) == production["result_sha256"], label + ": production binding differs")
    require(result["schema_version"] == "hf-native-force-result-1.0"
            and canonical_hash({k: v for k, v in result.items() if k != "descriptor_sha256"}) == result["descriptor_sha256"], label + ": result identity differs")
    require(result["scope"] == "supplied_displacement_test_only" and result["force_only"] is True
            and result["equilibrium_qualified"] is False and result["task_target_executed"] is False
            and result["fixed_displacement_compatible"] is True
            and result["tangent_calls"] == result["solver_calls"] == 0, label + ": force-only scope differs")
    force_path, state_path = directory / result["forces"]["path"], directory / result["state"]["path"]
    forces, state = read_archive(force_path, result["forces"]), read_archive(state_path, result["state"])
    require(digest(force_path) == production["forces_sha256"] and digest(state_path) == production["state_sha256"], label + ": saved payload differs")
    source_state = ROOT / row["state_file"]
    require(digest(source_state) == row["state_file_sha256"], label + ": original state differs")
    with np.load(source_state, allow_pickle=False) as original:
        require(set(original.files) == set(state) == {"lift", "fluctuation"}, label + ": state fields differ")
        for name in state:
            require(np.array_equal(state[name], original[name]), label + ": exact state component differs")
    state_hash = sha256(b"split_displacement_v1")
    state_hash.update(np.asarray([len(state["lift"])], dtype="<i8").tobytes())
    for name in ("lift", "fluctuation"):
        state_hash.update(np.asarray(state[name], dtype="<f8").tobytes())
    require(state_hash.hexdigest() == result["state_sha256"], label + ": split-state identity differs")
    model_path = directory / result["model"]["descriptor_path"]
    require(digest(model_path) == result["model"]["descriptor_file_sha256"], label + ": model identity differs")
    model_metadata = read_json(model_path)
    require(canonical_hash({k: v for k, v in model_metadata.items() if k != "descriptor_sha256"})
            == model_metadata["descriptor_sha256"] == result["model"]["descriptor_sha256"], label + ": semantic model differs")
    model_npz = directory / result["model"]["arrays_path"]
    model = read_archive(model_npz, model_metadata["arrays"])
    require(digest(model_npz) == result["model"]["arrays_sha256"] == production["model_sha256"], label + ": model arrays differ")
    task_path = ROOT / row["task_file"]
    task = read_json(task_path)
    require(digest(task_path) == row["task_file_sha256"] and task == model_metadata["task"]
            and canonical_hash(task) == result["task_sha256"] == model_metadata["task_sha256"], label + ": task differs")
    source_path = directory / result["source_geometry"]["snapshot"]["descriptor"]
    source_npz = directory / result["source_geometry"]["snapshot"]["arrays"]
    geometry = load_geometry(source_path)
    require(digest(source_path) == result["source_geometry"]["descriptor_file_sha256"] == row["geometry_file_sha256"]
            and digest(source_npz) == result["source_geometry"]["arrays_sha256"] == row["geometry_npz_sha256"]
            and geometry.geometry_id == result["source_geometry"]["geometry_id"] == row["geometry_id"], label + ": source differs")
    require(np.array_equal(model["solid"], geometry.solid.ravel().astype(bool)), label + ": plotted structure differs")
    require(np.all(state["lift"][model["fixed_dofs"]] == -state["fluctuation"][model["fixed_dofs"]]), label + ": fixed compatibility differs")
    require(np.all(forces["J"] > 0.), label + ": J must be physically positive")
    displacement = (state["lift"] + state["fluctuation"]).reshape(-1, 2)  # Rounded display only.
    magnitudes = {name: np.linalg.norm(forces["global_"+name+"_force"].reshape(-1, 2), axis=1) for name in COMPONENTS}
    require(result["metrics"]["min_J"] == float(forces["J"].min())
            and result["metrics"]["max_abs_Hu_per_mm"] == float(np.abs(forces["Hu"]).max())
            and result["metrics"]["max_abs_global_total_force_N"] == float(np.abs(forces["global_total_force"]).max()), label + ": saved metrics differ")
    files = (path, force_path, state_path, source_state, model_path, model_npz, source_path, source_npz, task_path)
    record = dict(alias=row["alias"], state_name=row["state_name"], geometry_id=geometry.geometry_id,
        task_sha256=result["task_sha256"], state_sha256=result["state_sha256"], grid=geometry.grid,
        metrics=result["metrics"], internal_nodal_force_norm_max_N={key: float(value.max()) for key, value in magnitudes.items()},
        fixed_displacement_compatible=True, task_target_executed=False, equilibrium_qualified=False,
        supplied_amplitude_mm=row["displacement_amplitude_mm"], exact_input_classes=row["exact_input_classes"],
        material=model_metadata["material"], input_files_sha256={p.relative_to(ROOT).as_posix(): digest(p) for p in files})
    return dict(row=row, geometry=geometry, model=model, state=state, forces=forces, displacement=displacement, magnitudes=magnitudes, record=record)


def bind_audit(stage, inventory, production, cases):
    path = stage / "audit/summary.json"
    audit = read_json(path)
    require(audit["schema_version"] == "native-force-independent-audit-1.0" and audit["status"] == "pass"
            and audit["full_element_and_global_coverage"] is True, "Passing full saved-force audit is required")
    require(audit["equilibrium_qualified"] is False and audit["task_target_executed"] is False,
            "Force audit scope differs")
    require(audit["HP_calls_started"] == audit["HP_calls_completed"]
            == 2*sum(row["exact_input_classes"] for row in inventory["cases"]), "Audit reference coverage differs")
    for name, pin in production["sources"].items():
        require(digest(ROOT / name) == pin == digest(stage / "sources" / Path(name).name), "Frozen/current source differs: "+name)
    for name, pin in audit["source_bindings"].items():
        require(digest(ROOT / name) == pin == production["sources"][name], "Audited source differs: "+name)
    for name, pin in audit["input_bindings"].items():
        require(digest(ROOT / name) == pin, "Audited input differs: "+name)
    audit_rows = {(row["alias"], row["state_name"]): row for row in audit["cases"]}
    require(set(audit_rows) == {(row["alias"], row["state_name"]) for row in inventory["cases"]}, "Audit six-state scope differs")
    for case in cases:
        row = case["row"]
        checked = audit_rows[row["alias"], row["state_name"]]
        require(checked["status"] == "pass" and checked["elements_compared"] == row["elements"]
                and checked["scalar_local_force_entries_compared"] == row["elements"]*8*3
                and checked["global_DOF_entries_compared"] == row["dofs"]*3
                and checked["exact_input_classes"] == row["exact_input_classes"]
                and checked["metrics"] == case["record"]["metrics"], "Audit display coverage differs")
        for checks in (checked["local_worst"], checked["global_checks"]):
            require({item["component"] for item in checks} == set(COMPONENTS)
                    and all(item["pass_gate"] is True for item in checks), "Audit component gate differs")
        case["record"]["audit"] = {name: checked[name] for name in ("elements_compared", "scalar_local_force_entries_compared",
            "global_DOF_entries_compared", "exact_input_classes", "HP_calls", "local_worst", "global_checks")}
    return dict(summary_sha256=digest(path), status="pass", HP_calls_completed=audit["HP_calls_completed"],
        full_element_and_global_coverage=True, input_bindings=audit["input_bindings"], source_bindings=audit["source_bindings"],
        scope="Saved independent force comparison; does not qualify equilibrium or execute task actuation")


def axes_geometry(ax, case):
    geometry = case["geometry"]
    x0, y0 = geometry.grid["origin_mm"]
    width, height = geometry.grid["extent_mm"]
    ax.imshow(geometry.solid, origin="lower", interpolation="nearest", cmap="Greys", vmin=0, vmax=1,
              alpha=.26, extent=(x0, x0+width, y0, y0+height), zorder=0)
    ax.set_xlim(x0, x0+width)
    ax.set_ylim(y0, y0+height)
    ax.set_aspect("equal")
    ax.set_xlabel("x [mm]")
    ax.set_ylabel("y [mm]")
    ax.tick_params(labelsize=8)


def material_outline(ax, case):
    geometry = case["geometry"]
    ny, nx = geometry.grid["shape_yx"]
    hx, hy = geometry.grid["cell_size_mm"]
    x0, y0 = geometry.grid["origin_mm"]
    ax.contour(x0+(np.arange(nx)+.5)*hx, y0+(np.arange(ny)+.5)*hy,
               geometry.solid.astype(float), levels=[.5], colors="#777777", linewidths=.45)


def displacement_detail(ax, case):
    """Reference Q1 edges and supplied displacement x200 in a marked inset."""
    model, u = case["model"], case["displacement"]
    nodes = model["coordinates"][model["connectivity"]]
    chosen = (nodes[:, :, 0].min(axis=1) >= 38.) & (nodes[:, :, 0].max(axis=1) <= 40.)
    chosen &= (nodes[:, :, 1].min(axis=1) >= 18.) & (nodes[:, :, 1].max(axis=1) <= 20.)
    conn = model["connectivity"][chosen]
    original = model["coordinates"][conn]
    displaced = (model["coordinates"] + AMPLIFICATION*u)[conn]
    inset = ax.inset_axes([.60, .07, .36, .38])
    for values, color, width in ((original, "#b5b5b5", .5), (displaced, "#185b9c", .65)):
        closed = np.concatenate((values, values[:, :1]), axis=1)
        inset.add_collection(LineCollection(closed, colors=color, linewidths=width))
    inset.set_xlim(37.9, 40.25)
    inset.set_ylim(17.9, 20.1)
    inset.set_aspect("equal")
    inset.set_title("Q1 zoom: displacement x200\ngray=reference, blue=supplied", fontsize=6)
    inset.tick_params(labelsize=5)
    inset.set_facecolor("white")


def field_summary(checker, stripe):
    cm, sm = checker["record"]["metrics"], stripe["record"]["metrics"]
    return (f"checker: min J={cm['min_J']:.9g}; max |Hu|={cm['max_abs_Hu_per_mm']:.9g} /mm\n"
            f"stripe: max |Hu|={sm['max_abs_Hu_per_mm']:g} /mm; max |f_reg|={stripe['record']['internal_nodal_force_norm_max_N']['regularization']:g} N\n"
            f"Audit: all {checker['row']['elements']} elements / {checker['row']['dofs']} DOFs, 3 force components passed")


def plot_fields(by_case, output):
    all_cases = list(by_case.values())
    ux_max = max(float(np.abs(c["displacement"][:, 0]).max()) for c in all_cases)*1000
    j_min = min(float(c["forces"]["J"].min()) for c in all_cases)
    j_max = max(float(c["forces"]["J"].max()) for c in all_cases)
    hu_max = max(float(np.abs(c["forces"]["Hu"]).max()) for c in all_cases)
    norms = (Normalize(0., ux_max), Normalize(j_min, j_max), Normalize(0., hu_max))
    fig, axes = plt.subplots(3, 3, figsize=(16, 10.5), layout="constrained")
    fig.suptitle("Manufactured checker displacement: stored fields on the actual native geometry x1\n"
                 "No actuation, equilibrium or contact claim; only the marked Q1 inset magnifies displacement x200", fontsize=13)
    handles = []
    for row, alias in enumerate(ALIASES):
        case, stripe = by_case[alias, "checker"], by_case[alias, "stripe"]
        ny, nx = case["geometry"].grid["shape_yx"]
        coordinates = case["model"]["coordinates"].reshape(ny+1, nx+1, 2)
        j_cell = case["forces"]["J"].min(axis=1).reshape(ny, nx)
        hu_cell = np.abs(case["forces"]["Hu"]).max(axis=(1, 2, 3)).reshape(ny, nx)
        x0, y0 = case["geometry"].grid["origin_mm"]
        hx, hy = case["geometry"].grid["cell_size_mm"]
        edge_x, edge_y = x0+np.arange(nx+1)*hx, y0+np.arange(ny+1)*hy
        row_handles = []
        for col in range(3):
            ax = axes[row, col]
            axes_geometry(ax, case)
            if col == 0:
                values = case["displacement"][:, 0].reshape(ny+1, nx+1)*1000
                mesh = ax.pcolormesh(coordinates[:, :, 0], coordinates[:, :, 1], values, shading="nearest", cmap="Blues", norm=norms[col], alpha=.8)
                displacement_detail(ax, case)
            else:
                mesh = ax.pcolormesh(edge_x, edge_y, j_cell if col == 1 else hu_cell,
                    shading="flat", cmap="coolwarm" if col == 1 else "magma", norm=norms[col], alpha=.86)
            material_outline(ax, case)
            row_handles.append(mesh)
            title = ("Nodal ux [micrometres]", "Minimum quadrature J per element", "Maximum |Hu component| per element [1/mm]")[col]
            ax.set_title(alias+"\n"+title, fontsize=9)
        handles = row_handles
        axes[row, 0].text(0., -.31, field_summary(case, stripe), transform=axes[row, 0].transAxes, fontsize=8, va="top")
    for col, title in enumerate(("Stored ux [micrometres]", "J, dimensionless; not pressure", "|Hu| [1/mm]")):
        colorbar = fig.colorbar(handles[col], ax=axes[:, col].tolist(), shrink=.85, label=title)
        if col == 1:
            colorbar.formatter = FormatStrFormatter("%.6f")
            colorbar.update_ticks()
    fig.supxlabel("The fine gripper is another original design; these supplied-state tests do not establish mesh convergence.", fontsize=9)
    fig.savefig(output / "native_force_fields.png", dpi=160)
    plt.close(fig)
    return dict(ux_micrometres=[0., ux_max], J=[j_min, j_max], max_abs_Hu_per_mm=[0., hu_max],
        J_reduction="minimum of the 9 actual quadrature values in each element", Hu_reduction="maximum absolute tensor component in each element")


def plot_components(by_case, output):
    all_cases = list(by_case.values())
    limits = {}
    for component in COMPONENTS:
        values = np.concatenate([c["magnitudes"][component] for c in all_cases])
        positive = values[values > 0.]
        require(len(positive) > 0, component + ": no positive force magnitude for logarithmic color scale")
        limits[component] = [float(positive.min()), float(positive.max())]
    max_force = max(limits[name][1] for name in COMPONENTS)
    force_scale = max_force/4.  # N per displayed mm, identical in all panels.
    fig, axes = plt.subplots(3, 3, figsize=(16, 10.2), layout="constrained")
    fig.suptitle("Internal nodal weak-force residuals at the supplied checker displacement [N]\n"
                 "Log colors include every node; exact zero is uncolored. Arrows are sampled internal-force vectors, not reactions or a solution", fontsize=13)
    arrow_records, handles = {}, []
    for row, alias in enumerate(ALIASES):
        case = by_case[alias, "checker"]
        xy = case["model"]["coordinates"]
        ny, nx = case["geometry"].grid["shape_yx"]
        stride = 13 if case["row"]["alias"].endswith("fine") else 7
        sample = np.array([j*(nx+1)+i for j in range(0, ny+1, stride) for i in range(0, nx+1, stride)])
        arrow_records[alias] = dict(log_color_nodes=len(xy), arrow_nodes=sample.tolist(), logical_grid_stride=stride,
                                   selection="Every stride-th native node along each axis; odd stride retains both checker parities")
        row_handles = []
        for col, component in enumerate(COMPONENTS):
            ax = axes[row, col]
            axes_geometry(ax, case)
            norm = LogNorm(*limits[component])
            values = np.ma.masked_equal(case["magnitudes"][component], 0.)
            scatter = ax.scatter(xy[:, 0], xy[:, 1], c=values, s=4 if stride == 7 else 1.4,
                                 cmap="viridis", norm=norm, linewidths=0., rasterized=True)
            force = case["forces"]["global_"+component+"_force"].reshape(-1, 2)
            ax.quiver(xy[sample, 0], xy[sample, 1], force[sample, 0], force[sample, 1],
                angles="xy", scale_units="xy", scale=force_scale, color="#b94b26", width=.0025, minlength=0., zorder=4)
            max_norm = case["magnitudes"][component].max()
            ax.set_title(f"{alias}\n{component}: max nodal norm={max_norm:.9g} N", fontsize=9)
            row_handles.append(scatter)
        handles = row_handles
        axes[row, 0].text(0., -.26, f"All {len(xy)} node norms shown; arrows on logical stride {stride}.\n"
            f"Sum material energy={case['record']['metrics']['sum_material_energy_N_mm']:.9g} N mm.\n"
            f"Max global audit error={max(float(c['normalized_error']) for c in case['record']['audit']['global_checks']):.3e}; all 3 components passed.",
            transform=axes[row, 0].transAxes, fontsize=8, va="top")
    for col, component in enumerate(COMPONENTS):
        fig.colorbar(handles[col], ax=axes[:, col].tolist(), shrink=.85, label=component+" internal nodal norm [N], log scale")
    fig.supxlabel(f"Common force-arrow scale: {max_force:.9g} N = 4 displayed mm. Geometry x1; no half-model doubling.\n"
                 "The fine gripper is another original design; material energy is not a potential for the total regularized residual.", fontsize=9)
    fig.savefig(output / "native_force_components.png", dpi=160)
    plt.close(fig)
    return dict(log_color_range_N=limits, exact_zero_display="Uncolored; no artificial force floor", norm_uses="Both saved ux/uy force components at every node",
        arrow_scale_N_per_display_mm=force_scale, maximum_force_N=max_force, maximum_arrow_length_mm=4., arrows=arrow_records)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "lf_data_preparation/native_force_001")
    parser.add_argument("--output", type=Path, required=True, help="New directory")
    args = parser.parse_args()
    stage, output = args.input.resolve(), args.output.resolve()
    inventory = read_json(stage / "input_inventory.json")
    production = read_json(stage / "execution_receipt.json")
    require(production["status"] == "pass" and production["force_calls"] == 6,
            "Six completed force-only production states are required")
    require(digest(stage / "input_inventory.json") == production["input_inventory_sha256"], "Input inventory differs")
    require([(row["alias"], row["state_name"]) for row in inventory["cases"]]
            == [(alias, state) for alias in ALIASES for state in ("stripe", "checker")], "Six-state scope differs")
    produced = {(row["alias"], row["state_name"]): row for row in production["cases"]}
    cases = [load_case(stage, row, produced[row["alias"], row["state_name"]]) for row in inventory["cases"]]
    audit = bind_audit(stage, inventory, production, cases)
    by_case = {(case["row"]["alias"], case["row"]["state_name"]): case for case in cases}
    for alias in ALIASES:
        stripe = by_case[alias, "stripe"]
        require(not np.any(stripe["forces"]["Hu"]) and not np.any(stripe["forces"]["global_regularization_force"]), alias+": stripe Hu control differs")
    output.mkdir(parents=True, exist_ok=False)
    field_scales = plot_fields(by_case, output)
    force_scales = plot_components(by_case, output)
    frozen = output / "plot_native_force_frozen.py"
    frozen.write_bytes(Path(__file__).read_bytes())
    helper = output / "helpers/data.py"
    helper.parent.mkdir()
    helper.write_bytes((ROOT / "hf_repo/src/hf_eval/data.py").read_bytes())
    metadata = dict(schema_version="native-force-view-1.0", input_layout="results/<alias>/<state>/result.json",
        scope="Six saved supplied-displacement tests; no force/HP/assembly/tangent/solver evaluation by viewer",
        input_inventory_sha256=digest(stage / "input_inventory.json"), execution_receipt_sha256=digest(stage / "execution_receipt.json"),
        cases=[case["record"] for case in cases], audit=audit, geometry_scale=1., displacement_inset_scale=AMPLIFICATION,
        displacement_inset_reference_box_mm=[[38., 18.], [40., 20.]], fields=field_scales, force_display=force_scales,
        equilibrium_qualified=False, task_target_executed=False, internal_force_not_reaction=True,
        Hu_regularization_not_material_energy_gradient=True, workpiece_present=False, half_model_quantities_doubled=False,
        fine_is_another_design=True, mesh_convergence_claim=False, viewer_sha256=digest(frozen),
        frozen_helpers_sha256={"helpers/data.py": digest(helper)},
        media_sha256={path.name: digest(path) for path in sorted(output.glob("*.png"))})
    (output / "view_metadata.json").write_text(json.dumps(metadata, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps(dict(output=str(output), saved_states=len(cases), force_calls=0, HP_calls=0, solver_calls=0)))


if __name__ == "__main__":
    main()
