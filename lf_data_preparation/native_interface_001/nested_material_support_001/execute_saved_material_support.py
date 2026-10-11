"""M-SUPPORT1 source only: saved material assembly and basis-support diagnosis."""
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
             support_started=0, support_completed=0, global_replay=0, PNG_writes=0)
MODEL_FIELDS = ("coordinates", "connectivity", "edofs", "workpiece_nodes")


def checkpoint():
    global peak
    peak = max(peak, process.memory_info().rss)
    if (perf_counter()-STARTED > args.time_limit or peak > protocol["sampled_RSS_bytes"]
            or (protocol_file.parent/"stop_requested.txt").exists()):
        raise RuntimeError("M-SUPPORT1 cooperative resource/stop boundary reached")


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


def render(supports, model, traces):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection, LineCollection
    from matplotlib.colors import Normalize
    from matplotlib.lines import Line2D
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    xy, conn = model["coordinates"], model["connectivity"]
    for axis in (0, 1):
        limit = max(abs(cell["force_on_body_N"][axis]) for support in supports for cell in support["cells"]) or 1.
        norm = Normalize(-limit, limit)  # zero-only fallback is display normalization, not force clipping
        for column, support in enumerate(supports):
            ax, trace = axes[axis, column], traces[column]
            ids = [cell["cell_id"] for cell in support["cells"]]
            collection = PolyCollection(xy[conn[ids]], array=np.array([cell["force_on_body_N"][axis] for cell in support["cells"]]), cmap="coolwarm", norm=norm, edgecolors="0.75", linewidths=.2)
            ax.add_collection(collection)
            ax.add_collection(LineCollection(xy[np.asarray(trace["physical_node_pairs"], dtype=int)], colors="black", linewidths=1.2))
            ax.add_collection(LineCollection(xy[np.asarray(trace["cut_node_pairs"], dtype=int)], colors="0.4", linestyles="dashed", linewidths=1.))
            corners = [cell["cell_id"] for cell in support["cells"] if cell["group"] == "corner_only"]
            centers = xy[conn[corners]].mean(axis=1)
            ax.scatter(centers[:, 0], centers[:, 1], marker="D", facecolors="none", edgecolors="magenta", s=55, zorder=3)
            ax.set(xlim=(60.5, 81.5), ylim=(29.5, 40.5), xlabel="reference x (mm)", ylabel="reference y (mm)")
            ax.set_aspect("equal", adjustable="box")
            ax.set_title("state "+str(support["identity"]["index"])+", d="+str(support["identity"]["d_mm"])+" mm: material F"+"xy"[axis])
        fig.colorbar(collection, cax=fig.add_axes([.9, .57 if axis == 0 else .16, .018, .29]), label="signed cell body-node F"+"xy"[axis]+" contribution (N)")
    handles = [Line2D([0], [0], color="black", label="fixed body physical edges"), Line2D([0], [0], color="0.4", linestyle="--", label="symmetry cut"), Line2D([0], [0], color="magenta", marker="D", markerfacecolor="none", linestyle="", label="corner_only basis support: phase not read")]
    fig.legend(handles=handles, loc="lower center", ncol=3, fontsize=8)
    fig.suptitle("Reference material basis-support cells; signed body-node contributions, not face pressure or actual deformation")
    fig.subplots_adjust(left=.06, right=.85, top=.92, bottom=.1, wspace=.25, hspace=.28)
    fig.savefig(output/"reference_support_map.png", dpi=150)
    plt.close(fig)
    calls["PNG_writes"] += 1
    checkpoint()
    names = ("body", "bottom_owner", "left_owner", "right_owner", "corner_only")
    labels = ("body support", "bottom-owner support", "left-owner support", "right-owner support", "corner-only support", "saved P line estimate", "saved global weak")
    fig, axes = plt.subplots(2, 2, figsize=(14, 9), sharey="row")
    for column, support in enumerate(supports):
        for axis in (0, 1):
            values = [support["groups"][name]["force_on_body_N"][axis] for name in names]
            values += [support["saved_trace_material_line_N"][axis], support["whole"]["saved_global_force_on_body_N"][axis]]
            ax = axes[axis, column]
            ax.bar(range(7), values, color=list(plt.get_cmap("Set2").colors[:5])+["0.65", "0.2"])
            ax.axhline(0., color="black", linewidth=.6)
            ax.set_xticks(range(7), labels, rotation=35, ha="right", fontsize=8)
            ax.set(title="state "+str(support["identity"]["index"])+", d="+str(support["identity"]["d_mm"])+" mm", ylabel="signed material F"+"xy"[axis]+" (N)")
    fig.suptitle("Basis-support partition and separate saved trace/weak comparisons; no face-pressure interpretation")
    fig.tight_layout(rect=(0., .12, 1., .94))
    fig.text(.5, .04, "Only the first five bars partition local body-node support. Trace and saved global weak bars are comparisons; do not add them.", ha="center", fontsize=8)
    fig.savefig(output/"material_support_comparison.png", dpi=150)
    plt.close(fig)
    calls["PNG_writes"] += 1
    checkpoint()


def vector_fields(prefix, values):
    return {prefix+"_F"+axis+"_N": values[index] if values is not None else None for index, axis in enumerate("xy")}


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def csv_identity(row):
    return dict(index=int(row["index"]), original_target_index=int(row["original_target_index"]),
                leg=row["leg"], d_mm=float(row["d_mm"]), state_sha256=row["state_sha256"])


def csv_vector(row, prefix):
    return [float(row[prefix+"_F"+axis+"_N"]) for axis in "xy"]


def tables(supports):
    occurrences, cells, nodes, groups, whole = [], [], [], [], []
    for support in supports:
        identity = support["identity"]
        for row in support["occurrences"]:
            occurrences.append(dict(identity, cell_id=row["cell_id"], local_node_index=row["local_node_index"], node_id=row["node_id"], group=row["group"], x_mm=row["coordinates_mm"][0], y_mm=row["coordinates_mm"][1], **vector_fields("original_local_internal_material", row["internal_material_force_N"]), **vector_fields("body_material", row["force_on_body_N"])))
        for row in support["cells"]:
            cells.append(dict(identity, cell_id=row["cell_id"], group=row["group"], selected_local_node_count=row["selected_local_node_count"], node_ids=json.dumps(row["node_ids"]), selected_local_indices=json.dumps(row["selected_local_indices"]), selected_body_node_ids=json.dumps(row["selected_body_node_ids"]), **vector_fields("body_material", row["force_on_body_N"])))
        for row in support["nodes"]:
            nodes.append(dict(identity, node_id=row["node_id"], x_mm=row["coordinates_mm"][0], y_mm=row["coordinates_mm"][1], selected_local_occurrences=row["selected_local_occurrences"], support_cell_ids=json.dumps(row["support_cell_ids"]), **vector_fields("regrouped_local_body_material", row["regrouped_local_force_on_body_N"]), **vector_fields("saved_global_body_material", row["saved_global_force_on_body_N"]), **vector_fields("local_regrouping_error", row["closure"]["error_N"]), **vector_fields("local_roundoff_bound", row["closure"]["roundoff_bound_N"])))
        for name, row in support["groups"].items():
            groups.append(dict(identity, group=name, cell_count=row["cell_count"], local_occurrence_count=row["local_occurrence_count"], **vector_fields("body_material", row["force_on_body_N"]), **vector_fields("saved_side_material_line", row["saved_side_material_line_N"]), **vector_fields("support_minus_saved_side_line", row["support_minus_saved_side_line_N"])))
        record = support["whole"]
        whole.append(dict(identity, **vector_fields("regrouped_local_body_material", record["regrouped_local_force_on_body_N"]), **vector_fields("saved_global_body_material", record["saved_global_force_on_body_N"]), **vector_fields("local_regrouping_error", record["closure"]["error_N"]), **vector_fields("local_roundoff_bound", record["closure"]["roundoff_bound_N"]), **vector_fields("saved_trace_material_line", support["saved_trace_material_line_N"]), **vector_fields("saved_trace_line_minus_weak", support["saved_trace_line_minus_weak_N"])))
    counts = dict(occurrences_total=len(occurrences), cells_total=len(cells), nodes_total=len(nodes), groups_total=len(groups), whole_total=len(whole))
    for filename, rows in (("occurrences.csv", occurrences), ("cells.csv", cells), ("nodes.csv", nodes), ("groups.csv", groups), ("whole_material_comparison.csv", whole)):
        with (output/filename).open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    return counts


def run():
    if (protocol["schema_version"] != "saved-fixed-square-material-support-card-1.0" or args.time_limit != 180.
            or [item["index"] for item in protocol["selected_states"]] != [6, 13]):
        raise ValueError("M-SUPPORT1 requires180s and recorded indices6/13")
    for name, pin in protocol["bindings"].items():
        if sha(repo/name) != pin:
            raise ValueError("Bound source/input changed: "+name)
        checkpoint()
    metadata, result = read(repo/protocol["model_file"]), read(repo/protocol["result_file"])
    if (metadata["task_sha256"] != result["task_sha256"] or metadata["arrays"]["sha256"] != result["model"]["arrays_sha256"]
            or sha(repo/protocol["model_file"]) != result["model"]["descriptor_file_sha256"]
            or metadata["element_node_order"] != ["BL", "BR", "TR", "TL"]
            or metadata["task"]["workpiece"]["center_mm"] != [71., 40.] or metadata["task"]["workpiece"]["side_mm"] != 18.
            or metadata["task"]["workpiece"]["kind"] != "fixed_rigid" or metadata["task"]["workpiece"]["fixed_components"] != [0, 1]
            or metadata["task"]["workpiece"]["shape"] != "square" or metadata["model_extent"]["kind"] != "lower_half"
            or metadata["model_extent"]["symmetry_axis"] != {"normal": [0., 1.], "offset_mm": 40.}
            or metadata["grid"]["cell_size_mm"] != [.5, .5] or metadata["material"]["thickness_mm"] != 20.):
        raise ValueError("Require the preserved model identity and fixed h0.5 lower-half side18 task")
    model = selected_arrays((repo/protocol["model_file"]).parent/metadata["arrays"]["path"], metadata["arrays"], MODEL_FIELDS)
    body = dict(metadata["region_metadata"]["workpiece"], fixed_dofs=metadata["region_metadata"]["fixed_dofs"])
    trace_records = read(repo/protocol["material_trace_file"])["states"]
    traces = {record["identity"]["index"]: record for record in trace_records}
    side_rows, whole_rows = read_csv(repo/protocol["material_trace_sides_file"]), read_csv(repo/protocol["material_trace_whole_file"])
    saved_sides = {(int(row["index"]), row["face"]): row for row in side_rows}
    saved_whole = {int(row["index"]): row for row in whole_rows}
    if (len(side_rows) != 6 or set(saved_sides) != {(item["index"], face) for item in protocol["selected_states"] for face in ("bottom", "left", "right")}
            or len(whole_rows) != 2 or set(saved_whole) != {item["index"] for item in protocol["selected_states"]}):
        raise ValueError("Require the six original side CSV rows and two original whole comparison rows")
    sys.path.insert(0, str(repo/"hf_repo/src"))
    from hf_eval.saved_material_support import observe_saved_workpiece_material_support
    supports, selected_traces = [], []
    for identity in protocol["selected_states"]:
        index, key = identity["index"], str(identity["index"])
        state, original = read(repo/protocol["state_files"][key]), result["states"][index]
        for record in (state, original):
            if dict(index=index, original_target_index=record["original_target_index"], leg=record["leg"], d_mm=record["d"], state_sha256=record["state_sha256"]) != identity:
                raise ValueError("Selected identity differs from its original state/result record")
        trace, nodal = traces[index], read(repo/protocol["nodal_files"][key])
        if (trace["identity"] != identity or trace["physical_node_pairs"] != nodal["edges"]["physical"] or trace["cut_node_pairs"] != nodal["edges"]["cut"]):
            raise ValueError("Selected trace identity or original physical/cut edge binding differs")
        for face in ("bottom", "left", "right"):
            row, side = saved_sides[(index, face)], trace["sides"][face]
            if (csv_identity(row) != identity or int(row["edge_count"]) != side["edge_count"]
                    or csv_vector(row, "material_line") != side["material_line_estimate_on_body_N"]):
                raise ValueError("Saved side CSV identity/vector differs from the original trace JSON")
        whole_row = saved_whole[index]
        if (csv_identity(whole_row) != identity
                or csv_vector(whole_row, "material_line") != trace["material_line_estimate_on_body_N"]
                or csv_vector(whole_row, "saved_weak_material_body") != trace["saved_weak_material_body_N"]
                or csv_vector(whole_row, "line_minus_saved_weak") != trace["line_minus_saved_weak_N"]):
            raise ValueError("Saved whole CSV identity/vectors differ from the original trace JSON")
        base = (repo/protocol["state_files"][key]).parent.parent.parent
        forces = selected_arrays(base/state["forces"]["path"], state["forces"], ("element_material_force", "global_material_force"))
        calls["support_started"] += 1
        support = observe_saved_workpiece_material_support(model, forces, body, identity=identity, material_trace=trace)
        calls["support_completed"] += 1
        calls["global_replay"] += support["global_replay"]["calls"]  # completed API replay reports, not runtime-hook monitoring
        counts = support["counts"]
        if (counts != {"local_occurrences": protocol["expected_counts"]["occurrences_per_state"], "support_cells": protocol["expected_counts"]["cells_per_state"], "body_nodes": protocol["expected_counts"]["nodes_per_state"]}
                or {name: group["cell_count"] for name, group in support["groups"].items()} != protocol["expected_counts"]["group_cell_counts"]):
            raise ValueError("Saved support coverage differs from the frozen count contract")
        whole = support["whole"]["saved_global_force_on_body_N"]
        if ([row["node_id"] for row in support["nodes"]] != nodal["node_ids"]
                or [row["coordinates_mm"] for row in support["nodes"]] != nodal["coordinates_mm"]
                or [row["saved_global_force_on_body_N"] for row in support["nodes"]] != nodal["forces_on_body_N"]["material"]
                or whole != nodal["summary"]["force_on_lower_body_N"]["material"]
                or whole != state["workpiece"]["force_on_lower_body_N"]["material"]
                or whole != trace["saved_weak_material_body_N"]):
            raise ValueError("Original body-node/global/whole material records do not agree exactly")
        support["saved_trace_material_line_N"] = trace["material_line_estimate_on_body_N"]
        support["saved_trace_line_minus_weak_N"] = trace["line_minus_saved_weak_N"]
        for name, group in support["groups"].items():
            side_line = csv_vector(saved_sides[(index, name[:-6])], "material_line") if name.endswith("_owner") else None
            group["saved_side_material_line_N"] = side_line
            group["support_minus_saved_side_line_N"] = [a-b for a, b in zip(group["force_on_body_N"], side_line)] if side_line is not None else None
        support["side_comparison_scope"] = "Three saved owner-side line vectors and signed support-minus-side differences; descriptive only, no equality gate. Body/corner_only have no side-line allocation."
        support["comparison_scope"] = "Saved PTRACE line-versus-weak difference copied unchanged; no new equality science gate or Hu substitution"
        supports.append(support)
        selected_traces.append(trace)
        del forces
        checkpoint()
    counts = tables(supports)
    if counts != {name: protocol["expected_counts"][name] for name in counts}:
        raise ValueError("Saved support table row counts differ from the frozen protocol")
    write_json(output/"support.json", dict(schema_version="saved-two-state-material-support-1.0", states=supports, counts=counts,
        reference_map_scope="Original reference mesh only; not actual deformation. Actual state views remain in M-PTRACE1."))
    render(supports, model, selected_traces)
    if calls != protocol["expected_calls"]:
        raise ValueError("Saved support read/API/replay/PNG counts differ from the frozen protocol")
    for name, pin in protocol["bindings"].items():
        if sha(repo/name) != pin:
            raise ValueError("Original source/input changed: "+name)
        checkpoint()
    output_hashes = {path.name: sha(path) for path in output.iterdir()}
    checkpoint()
    elapsed, rss = perf_counter()-STARTED, peak
    return dict(status="pass", calls=calls, counts=counts, protocol_sha256=sha(protocol_file), all_bindings_unchanged=True,
        elapsed_seconds=elapsed, sampled_peak_RSS_bytes=rss, output_SHA256=output_hashes,
        source_scope="Three saved archives/eight fields, two material support APIs/exact numeric C-order global replays, local fsum regrouping, existing trace CSV association/side comparisons and two reference/support PNGs only; no P/lift/fluct NPZ array decode, constitutive/force-kernel/tangent/solver/HP call or new physics qualification", mechanical_hooks_monitored=False)


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
