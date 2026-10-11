"""M-PTRACE1 source only: five selected NPZ reads, two saved material traces."""
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
             trace_started=0, trace_completed=0, PNG_writes=0)
MODEL_FIELDS = ("coordinates", "connectivity", "solid", "workpiece_cells", "points", "thickness")
IDENTITY = ("index", "original_target_index", "leg", "d_mm", "state_sha256")


def checkpoint():
    global peak
    peak = max(peak, process.memory_info().rss)
    if (perf_counter()-STARTED > args.time_limit or peak > protocol["sampled_RSS_bytes"]
            or (protocol_file.parent/"stop_requested.txt").exists()):
        raise RuntimeError("M-PTRACE1 cooperative resource/stop boundary reached")


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")


def selected_arrays(path, descriptor, names):
    """One archive open; decode only explicitly named existing fields."""
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


def render(traces, displays):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    from matplotlib.colors import Normalize
    from matplotlib.lines import Line2D
    values = [sample["nominal_compression_MPa"] for trace in traces for edge in trace["edges"] for sample in edge["samples"]]
    # A zero-only fallback affects display normalization only, never saved values.
    limit = max(abs(value) for value in values) or 1.
    norm = Normalize(-limit, limit)
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    for column, (trace, display) in enumerate(zip(traces, displays)):
        sample_xy = np.array([sample["coordinates_mm"] for edge in trace["edges"] for sample in edge["samples"]])
        compression = [sample["nominal_compression_MPa"] for edge in trace["edges"] for sample in edge["samples"]]
        for row in (0, 1):
            ax = axes[row, column]
            ax.add_collection(LineCollection(display["mechanism_segments_mm"], colors="0.35", linewidths=.7, label="actual mechanism boundary"))
            ax.add_collection(LineCollection(display["body_segments_mm"], colors="black", linewidths=1.2, label="fixed physical body boundary"))
            ax.add_collection(LineCollection(display["cut_segments_mm"], colors="0.5", linewidths=.8, linestyles="dashed", label="symmetry cut: excluded from trace"))
            scatter = ax.scatter(sample_xy[:, 0], sample_xy[:, 1], c=compression, cmap="coolwarm", norm=norm, s=10 if row == 0 else 22, zorder=3)
            ax.set(xlim=display["full_xlim_mm"] if row == 0 else (60., 84.),
                   ylim=display["full_ylim_mm"] if row == 0 else (28., 40.), xlabel="x (mm)", ylabel="y (mm)")
            ax.set_aspect("equal", adjustable="box")
            ax.set_title("state "+str(trace["identity"]["index"])+" / d="+str(trace["identity"]["d_mm"])+" mm / "+("full actual view" if row == 0 else "body detail"))
    fig.legend(handles=axes[0, 0].get_legend_handles_labels()[0], labels=axes[0, 0].get_legend_handles_labels()[1], loc="lower center", ncol=3, fontsize=8)
    fig.suptitle("Saved actual X + lift + fluct; fixed-body one-sided material traces (no Hu total pressure)")
    fig.subplots_adjust(left=.06, right=.86, top=.91, bottom=.1, hspace=.3, wspace=.23)
    fig.colorbar(scatter, cax=fig.add_axes([.89, .22, .018, .58]), label="signed nominal compression -N·(P N), MPa")
    fig.text(.5, .035, "Shared endpoints retain owner values; coincident markers may overlap. Reference/current body positions coincide.", ha="center", fontsize=8)
    fig.savefig(output/"actual_material_trace.png", dpi=150)
    plt.close(fig)
    calls["PNG_writes"] += 1
    checkpoint()
    fig, axes = plt.subplots(2, 3, figsize=(15, 8), sharey="row")
    colors = ("tab:blue", "tab:orange")
    for column, face in enumerate(("bottom", "left", "right")):
        coordinate = 0 if face == "bottom" else 1
        for trace, color in zip(traces, colors):
            for edge in trace["edges"]:
                if edge["face"] != face:
                    continue
                x = [sample["coordinates_mm"][coordinate] for sample in edge["samples"]]
                marker = "x" if edge["outer_phase"] == "mechanism_solid" else "o"
                for row, key in enumerate(("nominal_compression_MPa", "sampling_tangent_shear_MPa")):
                    axes[row, column].plot(x, [sample[key] for sample in edge["samples"]], color=color, marker=marker, markersize=3, linewidth=.8)
        for row in (0, 1):
            axes[row, column].axhline(0., color="black", linewidth=.5)
            axes[row, column].set(title=face, xlabel="reference "+"xy"[coordinate]+" (mm)", ylabel=("signed compression -N·PN" if row == 0 else "signed sampling shear T·PN")+" (MPa)")
    handles = [Line2D([0], [0], color=color, label="state "+str(trace["identity"]["index"])+", d="+str(trace["identity"]["d_mm"])+" mm") for trace, color in zip(traces, colors)]
    handles += [Line2D([0], [0], color="black", marker=marker, linestyle="", label=phase) for phase, marker in (("outside third medium", "o"), ("outside mechanism solid", "x"))]
    fig.legend(handles=handles, loc="lower center", ncol=4, fontsize=8)
    fig.suptitle("One-sided saved material P at three exact Simpson edge points; signed MPa, common row axes")
    fig.tight_layout(rect=(0., .13, 1., .94))
    fig.text(.5, .055, "T=(+1,0) bottom; T=(0,+1) left/right. Each owner edge is drawn separately; no endpoint averaging or interpolation.", ha="center", fontsize=8)
    fig.savefig(output/"nominal_material_profiles.png", dpi=150)
    plt.close(fig)
    calls["PNG_writes"] += 1
    checkpoint()


def tables(traces):
    edge_rows, sample_rows, side_rows, whole_rows = [], [], [], []
    for trace in traces:
        identity = trace["identity"]
        for edge_index, edge in enumerate(trace["edges"]):
            base = dict(identity, edge_index=edge_index, face=edge["face"], node_a=edge["node_ids"][0], node_b=edge["node_ids"][1], body_cell_id=edge["body_cell_id"], body_local_face=edge["body_local_face"], outer_cell_id=edge["outer_cell_id"], outer_local_face=edge["outer_local_face"], outer_phase=edge["outer_phase"], N_x=edge["body_outward_normal"][0], N_y=edge["body_outward_normal"][1], T_x=edge["sampling_tangent"][0], T_y=edge["sampling_tangent"][1])
            edge_rows.append(dict(base, reference_length_mm=edge["reference_length_mm"], material_line_Fx_N=edge["material_line_estimate_on_body_N"][0], material_line_Fy_N=edge["material_line_estimate_on_body_N"][1]))
            for sample in edge["samples"]:
                sample_rows.append(dict(base, point_index=sample["point_index"], xi=sample["reference_point"][0], eta=sample["reference_point"][1], x_mm=sample["coordinates_mm"][0], y_mm=sample["coordinates_mm"][1], P_xx_MPa=sample["P_MPa"][0][0], P_xy_MPa=sample["P_MPa"][0][1], P_yx_MPa=sample["P_MPa"][1][0], P_yy_MPa=sample["P_MPa"][1][1], PN_x_MPa=sample["PN_MPa"][0], PN_y_MPa=sample["PN_MPa"][1], nominal_compression_MPa=sample["nominal_compression_MPa"], sampling_tangent_shear_MPa=sample["sampling_tangent_shear_MPa"], line_weight_mm=sample["line_weight_mm"]))
        for face, side in trace["sides"].items():
            side_rows.append(dict(identity, face=face, edge_count=side["edge_count"], material_line_Fx_N=side["material_line_estimate_on_body_N"][0], material_line_Fy_N=side["material_line_estimate_on_body_N"][1]))
        whole_rows.append(dict(identity, **{name+"_F"+axis+"_N": values[i] for name, values in (("material_line", trace["material_line_estimate_on_body_N"]), ("saved_weak_material_body", trace["saved_weak_material_body_N"]), ("line_minus_saved_weak", trace["line_minus_saved_weak_N"])) for i, axis in enumerate("xy")}))
    for filename, rows in (("samples.csv", sample_rows), ("edges.csv", edge_rows), ("sides.csv", side_rows), ("whole_material_comparison.csv", whole_rows)):
        with (output/filename).open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    return dict(samples_total=len(sample_rows), edges_total=len(edge_rows), sides_total=len(side_rows), whole_total=len(whole_rows))


def run():
    if (protocol["schema_version"] != "saved-fixed-square-material-trace-card-1.0" or args.time_limit != 180.
            or [item["index"] for item in protocol["selected_states"]] != [6, 13]):
        raise ValueError("M-PTRACE1 requires180s and the two recorded indices6/13")
    for name, pin in protocol["bindings"].items():
        if sha(repo/name) != pin:
            raise ValueError("Bound source/input changed: "+name)
        checkpoint()
    metadata = read(repo/protocol["model_file"])
    result, view = read(repo/protocol["result_file"]), read(repo/protocol["view_summary_file"])
    if (metadata["task_sha256"] != result["task_sha256"] or metadata["arrays"]["sha256"] != result["model"]["arrays_sha256"]
            or sha(repo/protocol["model_file"]) != result["model"]["descriptor_file_sha256"]):
        raise ValueError("Saved model identity differs from its original result")
    if (metadata["schema_version"] != "hf-native-project-model-1.1" or metadata["element_node_order"] != ["BL", "BR", "TR", "TL"]
            or metadata["quadrature"] != "tensor_product_9_point_Simpson" or metadata["task"]["workpiece"]["center_mm"] != [71., 40.]
            or metadata["task"]["workpiece"]["side_mm"] != 18. or metadata["grid"]["cell_size_mm"] != [.5, .5]
            or metadata["material"]["thickness_mm"] != 20. or metadata["model_extent"]["kind"] != "lower_half"
            or metadata["task"]["workpiece"]["kind"] != "fixed_rigid" or metadata["task"]["workpiece"]["shape"] != "square"
            or metadata["task"]["workpiece"]["fixed_components"] != [0, 1]
            or metadata["model_extent"]["symmetry_axis"] != {"normal": [0., 1.], "offset_mm": 40.}):
        raise ValueError("Require the recorded fixed h0.5 lower-half side18 square")
    model = selected_arrays((repo/protocol["model_file"]).parent/metadata["arrays"]["path"], metadata["arrays"], MODEL_FIELDS)
    if float(model["thickness"]) != metadata["material"]["thickness_mm"]:
        raise ValueError("Saved thickness differs from model metadata")
    sys.path.insert(0, str(repo/"hf_repo/src"))
    from hf_eval.saved_material_trace import observe_saved_workpiece_material_trace
    traces, displays = [], []
    for identity in protocol["selected_states"]:
        key = str(identity["index"])
        state = read(repo/protocol["state_files"][key])
        saved_identity = dict(index=identity["index"], original_target_index=state["original_target_index"], leg=state["leg"], d_mm=state["d"], state_sha256=state["state_sha256"])
        original = result["states"][identity["index"]]
        result_identity = dict(index=identity["index"], original_target_index=original["original_target_index"], leg=original["leg"], d_mm=original["d"], state_sha256=original["state_sha256"])
        if (saved_identity != identity or result_identity != identity
                or {name: view["rows"][identity["index"]][name] for name in IDENTITY} != identity):
            raise ValueError("Selected identity differs from original state/result/view row")
        base = (repo/protocol["state_files"][key]).parent.parent.parent
        fields = selected_arrays(base/state["forces"]["path"], state["forces"], ("stress_first_piola",))
        display_state = selected_arrays(base/state["state"]["path"], state["state"], ("lift", "fluctuation"))
        calls["trace_started"] += 1
        trace = observe_saved_workpiece_material_trace(model, fields["stress_first_piola"], identity=identity, symmetry_y_mm=40., thickness_mm=20.)
        calls["trace_completed"] += 1
        nodal, geometry = read(repo/protocol["nodal_files"][key]), read(repo/protocol["geometry_files"][key])
        if (trace["physical_node_pairs"] != nodal["edges"]["physical"] or trace["cut_node_pairs"] != nodal["edges"]["cut"]
                or len(trace["edges"]) != protocol["expected_counts"]["physical_edges_per_state"]
                or len(trace["cut_node_pairs"]) != protocol["expected_counts"]["cut_edges_per_state"]
                or len(geometry["physical_mechanism_edges"]) != protocol["expected_counts"]["physical_mechanism_edges_per_state"]):
            raise ValueError("New trace edge identity/count differs from the preserved physical/cut edges")
        trace["saved_weak_material_body_N"] = state["workpiece"]["force_on_lower_body_N"]["material"]
        trace["line_minus_saved_weak_N"] = [a-b for a, b in zip(trace["material_line_estimate_on_body_N"], trace["saved_weak_material_body_N"])]
        trace["comparison_scope"] = "Side-excluded-cut material P line estimate versus saved complete body-node weak material load; descriptive difference only, no numerical equality gate"
        actual = model["coordinates"] + display_state["lift"].reshape(-1, 2) + display_state["fluctuation"].reshape(-1, 2)
        if not np.isfinite(actual).all() or not np.array_equal(actual[nodal["node_ids"]], model["coordinates"][nodal["node_ids"]]):
            raise ValueError("Require finite saved display coordinates with the body still fixed")
        traces.append(trace)
        displays.append(dict(mechanism_segments_mm=actual[np.asarray(geometry["physical_mechanism_edges"], dtype=int)], body_segments_mm=actual[np.asarray(trace["physical_node_pairs"], dtype=int)], cut_segments_mm=actual[np.asarray(trace["cut_node_pairs"], dtype=int)], full_xlim_mm=(0., 84.), full_ylim_mm=(0., 40.)))
        del fields, display_state
        checkpoint()
    counts = tables(traces)
    if counts != {name: protocol["expected_counts"][name] for name in counts}:
        raise ValueError("Recorded trace-table row count differs from the frozen protocol")
    write_json(output/"material_trace.json", dict(schema_version="saved-two-state-material-trace-1.0", states=traces, counts=counts, display_coordinate_definition="coordinates + lift.reshape(-1,2) + fluctuation.reshape(-1,2), same left-associative saved-viewer expression; display only"))
    render(traces, displays)
    for name, pin in protocol["bindings"].items():
        if sha(repo/name) != pin:
            raise ValueError("Original source/input changed: "+name)
        checkpoint()
    output_hashes = {path.name: sha(path) for path in output.iterdir()}
    checkpoint()
    elapsed, rss = perf_counter()-STARTED, peak
    return dict(status="pass", calls=calls, counts=counts, protocol_sha256=sha(protocol_file), all_bindings_unchanged=True,
        elapsed_seconds=elapsed, sampled_peak_RSS_bytes=rss, output_SHA256=output_hashes,
        source_scope="Five selected saved archives/twelve fields, two saved material trace APIs, reference line estimates, saved display coordinates and two PNGs only; no constitutive/force/tangent/solver/HP evaluation, total Hu traction, Cauchy conversion or new mechanics qualification", mechanical_hooks_monitored=False)


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
