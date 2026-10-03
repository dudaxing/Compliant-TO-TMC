"""Plot two saved directional tangent actions without evaluating mechanics.

Directions are dimensionless nodal shapes. The plotted CSC actions K v are
internal-force derivatives in N/mm, with lift fixed; no step is applied.
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
from matplotlib.colors import LogNorm, Normalize
import numpy as np
from scipy import sparse

ROOT = next(parent for parent in Path(__file__).resolve().parents
            if (parent / "hf_repo/src/hf_eval/data.py").is_file())
sys.path.insert(0, str(ROOT / "hf_repo/src"))
from hf_eval.data import canonical_hash, load_geometry

COMPONENTS = ("material", "regularization", "total")
DIRECTIONS = ("vx_stripe", "vy_checker")


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_arrays(path, declaration):
    require(digest(path) == declaration["sha256"], path.name + ": SHA differs")
    with np.load(path, allow_pickle=False) as saved:
        require(set(saved.files) == set(declaration["fields"]), path.name + ": fields differ")
        arrays = {key: saved[key].copy() for key in saved.files}
    for key, values in arrays.items():
        field = dict(dtype=values.dtype.name, shape=list(values.shape), sha256=sha256(values.tobytes(order="C")).hexdigest())
        require(field == declaration["fields"][key], path.name + ": " + key + " differs")
    return arrays


def load_saved(stage):
    inventory_path, production_path = stage / "input_inventory.json", stage / "execution_receipt.json"
    inventory, production = read_json(inventory_path), read_json(production_path)
    require(production["status"] == "pass" and production["invocations"] == production["force_calls"]
            == production["tangent_calls"] == 1 and production["solver_calls"] == 0, "One completed tangent test is required")
    require(digest(inventory_path) == production["input_inventory_sha256"] and len(inventory["cases"]) == 1, "Inventory differs")
    row = inventory["cases"][0]
    require(row["alias"] == "gripper_canonical" and row["state_name"] == "checker"
            and [item["name"] for item in row["directions"]] == list(DIRECTIONS), "Declared coarse two-direction scope differs")
    directory = stage / row["result_directory"]
    result_path = directory / "result.json"
    result = read_json(result_path)
    require(digest(result_path) == production["result_sha256"]
            and canonical_hash({key: value for key, value in result.items() if key != "descriptor_sha256"})
            == result["descriptor_sha256"], "Tangent result identity differs")
    require(result["schema_version"] == "hf-native-tangent-result-1.0" and result["backend"] == "numpy"
            and result["matrix_units"] == "N/mm" and result["scope"] == "supplied_displacement_test_only"
            and result["fixed_DOF_rows_columns_retained"] is True and result["matrices_symmetrized"] is False
            and result["equilibrium_qualified"] is False and result["task_target_executed"] is False
            and result["fixed_displacement_compatible"] is True, "Saved tangent scope differs")
    model_path = directory / result["model"]["descriptor_path"]
    model_metadata = read_json(model_path)
    require(digest(model_path) == result["model"]["descriptor_file_sha256"]
            and canonical_hash({key: value for key, value in model_metadata.items() if key != "descriptor_sha256"})
            == model_metadata["descriptor_sha256"] == result["model"]["descriptor_sha256"], "Saved model identity differs")
    model_npz = directory / result["model"]["arrays_path"]
    model = read_arrays(model_npz, model_metadata["arrays"])
    require(digest(model_npz) == result["model"]["arrays_sha256"] == production["model_sha256"], "Model payload differs")
    state_path, tangent_path = directory / result["state"]["path"], directory / result["tangents"]["path"]
    state, tangents = read_arrays(state_path, result["state"]), read_arrays(tangent_path, result["tangents"])
    require(digest(state_path) == production["state_sha256"] and digest(tangent_path) == production["tangents_sha256"], "State/tensor binding differs")
    require(set(state) == {"lift", "fluctuation"} and set(tangents) == {name+"_tangent" for name in COMPONENTS}, "State/tensor fields differ")
    state_hash = sha256(b"split_displacement_v1")
    state_hash.update(np.asarray([row["dofs"]], dtype="<i8").tobytes())
    for name in ("lift", "fluctuation"):
        state_hash.update(np.asarray(state[name], dtype="<f8").tobytes())
    require(state_hash.hexdigest() == result["state_sha256"], "Exact split state identity differs")
    original_state = ROOT / row["state_file"]
    require(digest(original_state) == row["state_file_sha256"], "Original state differs")
    with np.load(original_state, allow_pickle=False) as saved:
        require(all(saved[name].tobytes(order="C") == state[name].tobytes(order="C") for name in state), "State components were changed")
    task_path = ROOT / row["task_file"]
    task = read_json(task_path)
    require(digest(task_path) == row["task_file_sha256"] and task == model_metadata["task"]
            and canonical_hash(task) == result["task_sha256"] == model_metadata["task_sha256"], "Task binding differs")
    source_path = directory / result["source_geometry"]["snapshot"]["descriptor"]
    source_npz = directory / result["source_geometry"]["snapshot"]["arrays"]
    geometry = load_geometry(source_path)
    require(digest(source_path) == row["geometry_file_sha256"] == result["source_geometry"]["descriptor_file_sha256"]
            and digest(source_npz) == row["geometry_npz_sha256"] == result["source_geometry"]["arrays_sha256"]
            and geometry.geometry_id == row["geometry_id"] == result["source_geometry"]["geometry_id"], "Source snapshot differs")
    require(np.array_equal(model["solid"], geometry.solid.ravel().astype(bool)), "Source structure differs")
    require(np.all(state["lift"][model["fixed_dofs"]] == -state["fluctuation"][model["fixed_dofs"]]), "Fixed-state compatibility differs")
    matrix_files = []
    for component in COMPONENTS:
        declaration = result["matrices"][component]
        path = directory / declaration["path"]
        require(digest(path) == declaration["sha256"] == production["matrix_sha256"][component], component + ": CSC identity differs")
        matrix = sparse.load_npz(path)
        require(matrix.format == declaration["format"] == "csc" and matrix.shape == (row["dofs"], row["dofs"]), component + ": full CSC shape differs")
        for field in ("data", "indices", "indptr"):
            values = getattr(matrix, field)
            actual = dict(dtype=values.dtype.name, shape=list(values.shape), sha256=sha256(values.tobytes(order="C")).hexdigest())
            require(actual == declaration["fields"][field], component + ": CSC storage differs")
        statistics = result["matrix_statistics"][component]
        require(statistics["shape"] == list(matrix.shape) and statistics["nnz"] == matrix.nnz,
                component + ": stored matrix dimensions differ")
        matrix_files.append(path)
    audit_path = stage / "audit/summary.json"
    audit = read_json(audit_path)
    require(audit["schema_version"] == "native-tangent-independent-audit-1.0" and audit["status"] == "pass"
            and audit["full_element_and_global_direction_coverage"] is True
            and audit["HP_matrix_columns_exhaustively_checked"] is False
            and audit["equilibrium_qualified"] is False and audit["task_target_executed"] is False, "Passing saved two-direction audit is required")
    require(audit["matrix_statistics"] == result["matrix_statistics"] and audit["elements"] == row["elements"]
            and audit["dofs"] == row["dofs"] and audit["full_local_matrix_entries_assembly_checked"] == row["elements"]*64*3, "Audit matrix coverage differs")
    require(audit["HP_calls_started"] == audit["HP_calls_completed"]
            == 2*sum(item["exact_input_classes"] for item in row["directions"]), "Audit class coverage differs")
    for name, pin in production["sources"].items():
        require(digest(ROOT / name) == pin == digest(stage / "sources" / Path(name).name), "Frozen/current source differs: "+name)
    for name, pin in audit["source_bindings"].items():
        require(digest(ROOT / name) == pin == production["sources"][name], "Audited source differs: "+name)
    for name, pin in audit["input_bindings"].items():
        require(digest(ROOT / name) == pin, "Audited input differs: "+name)
    audit_rows = {item["name"]: item for item in audit["directions"]}
    require(set(audit_rows) == set(DIRECTIONS), "Audit direction names differ")
    cases, action_files = [], []
    for item in row["directions"]:
        name, checked = item["name"], audit_rows[item["name"]]
        require(checked["status"] == "pass" and checked["elements_compared"] == row["elements"]
                and checked["local_action_entries_compared"] == row["elements"]*8*3
                and checked["global_DOF_entries_compared"] == checked["CSC_DOF_entries_compared"] == row["dofs"]*3
                and checked["exact_input_classes"] == item["exact_input_classes"], name + ": directional coverage differs")
        for gate in ("local_worst", "global_checks", "csc_checks"):
            require({entry["component"] for entry in checked[gate]} == set(COMPONENTS)
                    and all(entry["pass_gate"] is True for entry in checked[gate]), name + ": component gate differs")
        path = stage / "audit" / checked["actions"]["path"]
        require(digest(path) == checked["actions"]["sha256"], name + ": saved actions differ")
        with np.load(path, allow_pickle=False) as saved:
            actions = {key: saved[key].copy() for key in saved.files}
        direction_path = ROOT / item["file"]
        require(digest(direction_path) == item["sha256"], name + ": direction file differs")
        with np.load(direction_path, allow_pickle=False) as saved:
            require(saved[name].tobytes() == actions["direction"].tobytes()
                    and sha256(saved[name].tobytes()).hexdigest() == item["array_sha256"], name + ": direction array differs")
        require(not np.any(actions["direction"][model["fixed_dofs"]]), name + ": fixed direction is not zero")
        action_files.extend((path, direction_path))
        record = dict(name=name, direction_units=item["units"], action_units="N/mm",
            direction_array_sha256=item["array_sha256"], exact_input_classes=item["exact_input_classes"],
            local_worst=checked["local_worst"], global_checks=checked["global_checks"], csc_checks=checked["csc_checks"],
            elements_compared=checked["elements_compared"], global_DOF_entries_compared=checked["global_DOF_entries_compared"],
            CSC_DOF_entries_compared=checked["CSC_DOF_entries_compared"],
            max_nodal_action_norm_N_per_mm={component: float(np.linalg.norm(actions["csc_"+component+"_action"].reshape(-1, 2), axis=1).max()) for component in COMPONENTS})
        cases.append(dict(name=name, direction=actions["direction"],
            actions={component: actions["csc_"+component+"_action"].reshape(-1, 2) for component in COMPONENTS}, record=record))
    files = [inventory_path, production_path, audit_path, result_path, model_path, model_npz, state_path, tangent_path,
             original_state, task_path, source_path, source_npz, *matrix_files, *action_files]
    metadata = dict(alias=row["alias"], state_name=row["state_name"], geometry_id=geometry.geometry_id,
        task_sha256=result["task_sha256"], state_sha256=result["state_sha256"], counts=result["counts"], grid=geometry.grid,
        material=model_metadata["material"], matrix_statistics=result["matrix_statistics"],
        relative_asymmetry_definition=result["relative_asymmetry_definition"], linearization=result["linearization"],
        audit=dict(summary_sha256=digest(audit_path), HP_calls_completed=audit["HP_calls_completed"],
            full_local_matrix_entries_assembly_checked=audit["full_local_matrix_entries_assembly_checked"],
            HP_matrix_columns_exhaustively_checked=False, full_element_and_global_direction_coverage=True,
            input_bindings=audit["input_bindings"], source_bindings=audit["source_bindings"]),
        input_files_sha256={path.relative_to(ROOT).as_posix(): digest(path) for path in files})
    return geometry, model, cases, metadata


def background(ax, geometry):
    x0, y0 = geometry.grid["origin_mm"]
    width, height = geometry.grid["extent_mm"]
    ax.imshow(geometry.solid, cmap="Greys", vmin=0., vmax=1., alpha=.25, interpolation="nearest",
        origin="lower", extent=(x0, x0+width, y0, y0+height), zorder=0)
    ny, nx = geometry.grid["shape_yx"]
    hx, hy = geometry.grid["cell_size_mm"]
    ax.contour(x0+(np.arange(nx)+.5)*hx, y0+(np.arange(ny)+.5)*hy,
        geometry.solid.astype(float), levels=[.5], colors="#888888", linewidths=.45, zorder=1)
    ax.set_aspect("equal")
    ax.set_xlim(x0, x0+width)
    ax.set_ylim(y0, y0+height)
    ax.set_xlabel("x [mm]")
    ax.set_ylabel("y [mm]")
    ax.tick_params(labelsize=8)


def plot_actions(geometry, model, cases, metadata, output):
    coordinates = model["coordinates"]
    ny, nx = geometry.grid["shape_yx"]
    sample = np.array([j*(nx+1)+i for j in range(0, ny+1, 7) for i in range(0, nx+1, 7)])
    magnitudes = {case["name"]: {name: np.linalg.norm(case["actions"][name], axis=1) for name in COMPONENTS} for case in cases}
    limits = {}
    for name in COMPONENTS:
        values = np.concatenate([magnitudes[case["name"]][name] for case in cases])
        positive = values[values > 0.]
        require(len(positive), name + ": no positive logarithmic action magnitude")
        limits[name] = [float(positive.min()), float(positive.max())]
    maximum_action = max(pair[1] for pair in limits.values())
    action_scale = maximum_action/4.
    fig, axes = plt.subplots(2, 4, figsize=(19, 9.2), layout="constrained")
    fig.suptitle("Saved coarse gripper checker state: two directional internal-force derivatives, lift held fixed\n"
        "Dimensionless directions v; full unsymmetrized CSC actions K v [N/mm]. No displacement step or equilibrium solve.", fontsize=13)
    handles = []
    for row, case in enumerate(cases):
        direction = case["direction"].reshape(-1, 2)
        row_handles = []
        for col in range(4):
            ax = axes[row, col]
            background(ax, geometry)
            if col == 0:
                values = np.linalg.norm(direction, axis=1)
                mesh = ax.scatter(coordinates[:, 0], coordinates[:, 1], c=values, s=4, cmap="Blues", norm=Normalize(0., 1.), linewidths=0., rasterized=True)
                vectors, arrow_scale = direction, 1./3.
                label = "Direction shape v, dimensionless"
                title = f"{case['name']}\n{label}"
            else:
                name = COMPONENTS[col-1]
                values = np.ma.masked_equal(magnitudes[case["name"]][name], 0.)
                mesh = ax.scatter(coordinates[:, 0], coordinates[:, 1], c=values, s=4,
                    cmap="viridis", norm=LogNorm(*limits[name]), linewidths=0., rasterized=True)
                vectors, arrow_scale = case["actions"][name], action_scale
                title = f"{name} K v [N/mm]\nmax node norm={values.max():.9g} N/mm"
            ax.quiver(coordinates[sample, 0], coordinates[sample, 1], vectors[sample, 0], vectors[sample, 1],
                angles="xy", scale_units="xy", scale=arrow_scale, color="#b94b26", width=.0025, minlength=0., zorder=3)
            ax.set_title(title, fontsize=9)
            row_handles.append(mesh)
        error = max(float(item["normalized_error"]) for item in case["record"]["csc_checks"])
        axes[row, 0].text(0., -.29, f"All {len(coordinates)} nodes colored; arrow stride 7.\n"
            f"Direction arrows: unit shape = 3 display mm.\nFull CSC action audit: max normalized error={error:.3e}.",
            transform=axes[row, 0].transAxes, fontsize=8, va="top",
            bbox=dict(facecolor="white", edgecolor="none", alpha=1., pad=2.))
        handles = row_handles
    for col in range(4):
        label = "|v|, dimensionless" if col == 0 else COMPONENTS[col-1]+" |K v| [N/mm], log"
        fig.colorbar(handles[col], ax=axes[:, col].tolist(), shrink=.75, label=label)
    asymmetry = "; ".join(f"{name}={metadata['matrix_statistics'][name]['relative_asymmetry']:.6g}" for name in COMPONENTS)
    fig.supxlabel(f"Relative Frobenius asymmetry ||K-K.T||/||K||: {asymmetry}\n"
        f"Common action-arrow scale: {maximum_action:.9g} N/mm = 4 display mm. Multiply K v by a small parameter step [mm] for a force increment.\n"
        "HP checks cover these two declared directions. Internal derivatives are not contact reactions; no task actuation or half-model doubling.", fontsize=9)
    fig.savefig(output / "native_tangent_directional_actions.png", dpi=160)
    plt.close(fig)
    return dict(geometry_scale=1., direction_color_range=[0., 1.], direction_units="dimensionless",
        direction_arrow_scale_display_mm_per_unit=3., action_units="N/mm", action_log_color_ranges=limits,
        common_action_arrow_scale_N_per_mm_per_display_mm=action_scale, maximum_action_N_per_mm=maximum_action,
        maximum_action_arrow_length_display_mm=4., arrow_logical_stride=7, arrow_nodes=sample.tolist(),
        all_node_magnitudes_colored=True, exact_zero_action_display="Uncolored; no artificial floor")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "lf_data_preparation/native_tangent_001")
    parser.add_argument("--output", type=Path, required=True, help="New directory")
    args = parser.parse_args()
    geometry, model, cases, metadata = load_saved(args.input.resolve())
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    metadata.update(display=plot_actions(geometry, model, cases, metadata, output))
    frozen = output / "plot_native_tangent_frozen.py"
    frozen.write_bytes(Path(__file__).read_bytes())
    helper = output / "helpers/data.py"
    helper.parent.mkdir()
    helper.write_bytes((ROOT / "hf_repo/src/hf_eval/data.py").read_bytes())
    metadata.update(schema_version="native-tangent-view-1.0", input_layout="result/result.json; directions.npz; audit/<direction>/actions.npz",
        scope="Saved native tangent directional actions only; no force/tangent/HP/solver/model construction",
        directions=[case["record"] for case in cases], force_calls=0, tangent_calls=0, HP_calls=0, solver_calls=0,
        equilibrium_qualified=False, task_target_executed=False, displacement_step_applied=False,
        full_fixed_DOF_matrix_rows_columns_retained=True, matrices_symmetrized=False, fine_model_checked=False,
        half_model_quantities_doubled=False, workpiece_present=False,
        viewer_sha256=digest(frozen), frozen_helpers_sha256={"helpers/data.py": digest(helper)},
        media_sha256={path.name: digest(path) for path in sorted(output.glob("*.png"))})
    (output / "view_metadata.json").write_text(json.dumps(metadata, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps(dict(output=str(output), saved_directions=len(cases), force_calls=0, tangent_calls=0, HP_calls=0, solver_calls=0)))


if __name__ == "__main__":
    main()
