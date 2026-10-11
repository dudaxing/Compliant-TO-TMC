"""M-VOLUME1: three selected NPZ reads and two saved rounded-P diagnostics."""
from time import perf_counter
STARTED = perf_counter()
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import psutil

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--repo", type=Path, required=True)
parser.add_argument("--protocol", type=Path, required=True)
parser.add_argument("--time-limit", type=float, required=True)
args = parser.parse_args()
repo, protocol_file = args.repo.resolve(), args.protocol.resolve()
read = lambda path: json.loads(path.read_text(encoding="utf-8"))
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
protocol = read(protocol_file)
output = repo/protocol["output_directory"]
process, peak = psutil.Process(), 0
calls = dict(NPZ_read_started=0, NPZ_read_completed=0, selected_array_fields=0,
             volume_started=0, volume_completed=0, PNG_writes=0)
MODEL_FIELDS = ("coordinates", "connectivity", "points", "grad", "weights")


def checkpoint():
    global peak
    peak = max(peak, process.memory_info().rss)
    if (perf_counter()-STARTED > args.time_limit or peak > protocol["sampled_RSS_bytes"]
            or (protocol_file.parent/"stop_requested.txt").exists()):
        raise RuntimeError("M-VOLUME1 cooperative resource/stop boundary reached")


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")


def selected_arrays(path, descriptor, names):
    if sha(path) != descriptor["sha256"]:
        raise ValueError("Saved NPZ archive differs from its original descriptor")
    checkpoint()
    calls["NPZ_read_started"] += 1
    arrays = {}
    with np.load(path, allow_pickle=False) as archive:
        for name in names:
            array, recorded = archive[name], descriptor["fields"][name]
            if (array.dtype.name != recorded["dtype"] or list(array.shape) != recorded["shape"]
                    or hashlib.sha256(array.tobytes(order="C")).hexdigest() != recorded["sha256"]):
                raise ValueError("Saved selected field differs: "+name)
            arrays[name] = array
            calls["selected_array_fields"] += 1
            checkpoint()
    calls["NPZ_read_completed"] += 1
    return arrays


def vector_fields(prefix, values):
    return {prefix+"_F"+axis+"_N": values[index] for index, axis in enumerate("xy")}


def csv_identity(row):
    return dict(index=int(row["index"]), original_target_index=int(row["original_target_index"]),
                leg=row["leg"], d_mm=float(row["d_mm"]), state_sha256=row["state_sha256"])


def read_support_cells(path):
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 1444:
        raise ValueError("Require the preserved M-SUPPORT1 1444-cell table")
    selected = {}
    for row in rows:
        key = (int(row["index"]), int(row["cell_id"]))
        if key[0] not in (6, 13) or key[1] not in (10406, 10407):
            continue
        if key in selected or int(row["selected_local_node_count"]) != 2:
            raise ValueError("Selected original support cells must occur once with two body nodes")
        selected[key] = dict(identity=csv_identity(row), cell_id=key[1], group=row["group"],
            node_ids=json.loads(row["node_ids"]), selected_local_indices=json.loads(row["selected_local_indices"]),
            selected_body_node_ids=json.loads(row["selected_body_node_ids"]),
            force_on_body_N=[float(row["body_material_F"+axis+"_N"]) for axis in "xy"])
    if set(selected) != {(state, cell) for state in (6, 13) for cell in (10406, 10407)}:
        raise ValueError("Require exactly the four original selected M-SUPPORT1 cell records")
    return selected


def tables(volumes):
    samples, depths, cells = [], [], []
    for volume in volumes:
        for cell in volume["cells"]:
            base = dict(volume["identity"], cell_id=cell["cell_id"])
            for row in cell["samples"]:
                P = row["P_normal_column_MPa"]
                samples.append(dict(base, point_index=row["point_index"], xi=row["reference_point"][0], eta=row["reference_point"][1],
                    x_mm=row["coordinates_mm"][0], y_mm=row["coordinates_mm"][1], P_xy_MPa=P[0], P_yy_MPa=P[1],
                    saved_volume_weight_mm3=row["saved_volume_weight_mm3"],
                    selected_basis_gradient_x_per_mm=row["selected_basis_gradient_per_mm"][0],
                    selected_basis_gradient_y_per_mm=row["selected_basis_gradient_per_mm"][1],
                    **vector_fields("rounded_P_volume_contribution", row["rounded_P_volume_contribution_on_body_N"])))
            for row in cell["depths"]:
                depths.append(dict(base, eta=row["eta"], point_indices=json.dumps(row["point_indices"]),
                    **vector_fields("C_eta", row["C_eta_on_body_N"]),
                    **vector_fields("regrouped_same_q_terms", row["regrouped_same_q_terms_on_body_N"]),
                    **vector_fields("geometric_depth_contribution", row["geometric_depth_contribution_on_body_N"])))
            comparison = dict(base, node_ids=json.dumps(cell["node_ids"]), selected_local_indices=json.dumps(cell["selected_local_indices"]),
                selected_body_node_ids=json.dumps(cell["selected_body_node_ids"]))
            for local, values in enumerate(cell["original_local_internal_material_force_N"]):
                comparison.update(vector_fields("original_local_"+str(local)+"_internal_material", values))
            for prefix, name in (("saved_weak_material", "saved_weak_material_on_body_N"), ("saved_top_material_line", "saved_top_material_line_on_body_N"),
                    ("rounded_P_direct_volume", "rounded_P_direct_volume_on_body_N"), ("regrouped_same_q_terms", "regrouped_same_q_terms_on_body_N"),
                    ("geometric_three_depth_volume", "geometric_three_depth_volume_on_body_N"), ("geometric_depth_gap", "geometric_depth_gap_on_body_N")):
                comparison.update(vector_fields(prefix, cell[name]))
            comparison.update(vector_fields("same_q_term_regrouping_error", cell["same_q_term_regrouping"]["error_N"]))
            comparison.update(vector_fields("same_q_term_regrouping_roundoff_bound", cell["same_q_term_regrouping"]["roundoff_bound_N"]))
            for name, values in cell["descriptive_differences_N"].items():
                comparison.update(vector_fields(name, values))
            cells.append(comparison)
    for name, rows in (("samples.csv", samples), ("depths.csv", depths), ("cell_comparisons.csv", cells)):
        with (output/name).open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    return dict(samples_total=len(samples), depth_rows_total=len(depths), cells_total=len(cells))


def render(volumes):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import Normalize
    cases = [(volume["identity"], cell) for volume in volumes for cell in volume["cells"]]
    fig, axes = plt.subplots(4, 2, figsize=(14, 16), layout="constrained")
    for row, (identity, cell) in enumerate(cases):
        for axis in (0, 1):
            values = np.array([sample["P_normal_column_MPa"][axis] for sample in cell["samples"]]).reshape(3, 3).T
            limit = float(np.max(np.abs(values))) or 1.  # display normalization only; no saved-value change
            ax = axes[row, axis]
            image = ax.imshow(values, origin="lower", cmap="coolwarm", norm=Normalize(-limit, limit), extent=(-1.5, 1.5, -1.5, 1.5))
            for eta in range(3):
                for xi in range(3):
                    ax.text(xi-1, eta-1, f"{values[eta, xi]:+.5e}", ha="center", va="center", fontsize=8,
                        color="white" if abs(values[eta, xi]) > .55*limit else "black")
            ax.set(xticks=(-1., 0., 1.), yticks=(-1., 0., 1.), xlabel="reference xi", ylabel="reference eta",
                title=f"state {identity['index']}, d={identity['d_mm']} mm / cell {cell['cell_id']} / P_{'xy'[axis]}Y")
            fig.colorbar(image, ax=ax, label="signed saved P_iY (MPa)", shrink=.8)
    fig.suptitle("Nine saved rounded material P samples per cell; independent signed scales in every panel")
    fig.savefig(output/"nine_point_material_P.png", dpi=150)
    plt.close(fig)
    calls["PNG_writes"] += 1
    checkpoint()
    fig, axes = plt.subplots(4, 2, figsize=(14, 16), layout="constrained")
    labels = ("Q eta=-1", "Q eta=0", "Q eta=+1", "rounded P volume", "saved weak W", "saved top trace T")
    for row, (identity, cell) in enumerate(cases):
        for axis in (0, 1):
            values = [depth["regrouped_same_q_terms_on_body_N"][axis] for depth in cell["depths"]]
            values += [cell[name][axis] for name in ("rounded_P_direct_volume_on_body_N", "saved_weak_material_on_body_N", "saved_top_material_line_on_body_N")]
            ax = axes[row, axis]
            bars = ax.bar(range(6), values, color=("tab:blue", "tab:orange", "tab:green", "tab:purple", "0.6", "0.2"))
            ax.bar_label(bars, fmt="%+.5e", padding=3, fontsize=7)
            ax.axhline(0., color="black", linewidth=.6)
            ax.margins(y=.25)
            ax.set_xticks(range(6), labels, rotation=22, ha="right", fontsize=8)
            ax.set(title=f"state {identity['index']}, d={identity['d_mm']} mm / cell {cell['cell_id']}", ylabel="signed material F"+"xy"[axis]+" (N)")
    fig.suptitle("Three Q depth contributions partition rounded-P volume; V / original weak W / saved edge T are comparisons\nEvery panel has its own signed scale; add only the first three Q columns")
    fig.savefig(output/"material_depth_volume_comparison.png", dpi=150)
    plt.close(fig)
    calls["PNG_writes"] += 1
    checkpoint()


def run():
    if (protocol["schema_version"] != "saved-bottom-material-volume-card-1.0" or args.time_limit != 180.
            or [item["index"] for item in protocol["selected_states"]] != [6, 13]
            or protocol["selected_cell_ids"] != [10406, 10407]):
        raise ValueError("M-VOLUME1 requires180s, original states6/13 and cells10406/10407")
    for name, pin in protocol["bindings"].items():
        if sha(repo/name) != pin:
            raise ValueError("Bound source/input changed: "+name)
        checkpoint()
    metadata, result = read(repo/protocol["model_file"]), read(repo/protocol["result_file"])
    if (metadata["task_sha256"] != result["task_sha256"] or metadata["arrays"]["sha256"] != result["model"]["arrays_sha256"]
            or sha(repo/protocol["model_file"]) != result["model"]["descriptor_file_sha256"]
            or metadata["schema_version"] != "hf-native-project-model-1.1" or metadata["element_node_order"] != ["BL", "BR", "TR", "TL"]
            or metadata["quadrature"] != "tensor_product_9_point_Simpson" or metadata["task"]["workpiece"]["center_mm"] != [71., 40.]
            or metadata["task"]["workpiece"]["side_mm"] != 18. or metadata["task"]["workpiece"]["kind"] != "fixed_rigid"
            or metadata["task"]["workpiece"]["shape"] != "square" or metadata["task"]["workpiece"]["fixed_components"] != [0, 1]
            or metadata["model_extent"]["kind"] != "lower_half" or metadata["model_extent"]["symmetry_axis"] != {"normal": [0., 1.], "offset_mm": 40.}
            or metadata["grid"]["cell_size_mm"] != [.5, .5] or metadata["material"]["thickness_mm"] != 20.):
        raise ValueError("Require the preserved h0.5 lower-half fixed-square task and result/model identity")
    model = selected_arrays((repo/protocol["model_file"]).parent/metadata["arrays"]["path"], metadata["arrays"], MODEL_FIELDS)
    support = read_support_cells(repo/protocol["material_support_cells_file"])
    traces = {row["identity"]["index"]: row for row in read(repo/protocol["material_trace_file"])["states"]}
    if set(traces) != {6, 13}:
        raise ValueError("Require the two original material trace states")
    sys.path.insert(0, str(repo/"hf_repo/src"))
    from hf_eval.saved_material_volume import observe_saved_bottom_owner_material_volume
    volumes = []
    for identity in protocol["selected_states"]:
        index, key = identity["index"], str(identity["index"])
        state, original = read(repo/protocol["state_files"][key]), result["states"][index]
        for record in (state, original):
            if dict(index=index, original_target_index=record["original_target_index"], leg=record["leg"], d_mm=record["d"], state_sha256=record["state_sha256"]) != identity:
                raise ValueError("Selected identity differs from its original state/result record")
        saved_cells = [support[(index, cell)] for cell in protocol["selected_cell_ids"]]
        if traces[index]["identity"] != identity or any(row["identity"] != identity for row in saved_cells):
            raise ValueError("Original trace/support cell identities differ from the selected state")
        base = (repo/protocol["state_files"][key]).parent.parent.parent
        forces = selected_arrays(base/state["forces"]["path"], state["forces"], ("stress_first_piola", "element_material_force"))
        calls["volume_started"] += 1
        volume = observe_saved_bottom_owner_material_volume(model, forces, metadata["region_metadata"]["workpiece"],
            identity=identity, material_trace=traces[index], saved_support_cells=saved_cells,
            selected_cell_ids=protocol["selected_cell_ids"], thickness_mm=20.)
        calls["volume_completed"] += 1
        if volume["counts"] != dict(samples=18, depths=6, cells=2):
            raise ValueError("Saved rounded-P volume coverage differs from the frozen contract")
        volumes.append(volume)
        del forces
        checkpoint()
    counts = tables(volumes)
    if counts != protocol["expected_counts"]:
        raise ValueError("Saved rounded-P volume table counts differ from the frozen protocol")
    write_json(output/"material_volume.json", dict(schema_version="saved-two-state-bottom-owner-material-volume-1.0", states=volumes, counts=counts))
    render(volumes)
    if calls != protocol["expected_calls"]:
        raise ValueError("Saved rounded-P volume read/API/PNG counts differ from the frozen protocol")
    for name, pin in protocol["bindings"].items():
        if sha(repo/name) != pin:
            raise ValueError("Original source/input changed: "+name)
        checkpoint()
    if {path.name for path in output.iterdir()} != set(protocol["expected_output_files"])-{"execution_receipt.json"}:
        raise ValueError("Saved rounded-P volume output filenames differ from the frozen contract")
    output_hashes = {path.name: sha(path) for path in output.iterdir()}
    checkpoint()
    elapsed, rss = perf_counter()-STARTED, peak
    return dict(status="pass", calls=calls, counts=counts, protocol_sha256=sha(protocol_file), all_bindings_unchanged=True,
        elapsed_seconds=elapsed, sampled_peak_RSS_bytes=rss, output_SHA256=output_hashes,
        source_scope="Three saved archives/nine fields, two ordinary NumPy APIs on four selected cells; nine-point rounded-P volume, same-term regrouping and geometric C sample-layer diagnosis, original trace/support association and two signed PNGs only; no original DD force replay, F/Hu reconstruction, DivP, constitutive/force-kernel/tangent/HP/equilibrium call or new mechanics qualification", mechanical_hooks_monitored=False)


def main():
    output.mkdir(parents=True, exist_ok=False)
    try:
        receipt = run()
    except BaseException as error:
        write_json(output/"execution_receipt.json", dict(status="not_pass", error=repr(error), calls=calls, elapsed_seconds=perf_counter()-STARTED, sampled_peak_RSS_bytes=peak))
        raise
    write_json(output/"execution_receipt.json", receipt)
    print(json.dumps(dict(status="pass", calls=calls)), flush=True)


if __name__ == "__main__":
    main()
