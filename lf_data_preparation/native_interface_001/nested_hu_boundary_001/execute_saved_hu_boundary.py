"""M-BOUND1: two saved Hu fields, preserved owner/node records and two views."""
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
             hu_boundary_started=0, hu_boundary_completed=0, PNG_writes=0)


def checkpoint():
    global peak
    peak = max(peak, process.memory_info().rss)
    if (perf_counter()-STARTED > args.time_limit or peak > protocol["sampled_RSS_bytes"]
            or (protocol_file.parent/"stop_requested.txt").exists()):
        raise RuntimeError("M-BOUND1 cooperative resource/stop boundary reached")


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")


def selected_array(path, descriptor):
    if sha(path) != descriptor["sha256"]:
        raise ValueError("Saved Hu NPZ archive differs from its original descriptor")
    checkpoint()
    calls["NPZ_read_started"] += 1
    with np.load(path, allow_pickle=False) as archive:
        array, recorded = archive["element_regularization_force"], descriptor["fields"]["element_regularization_force"]
        if (array.dtype.name != recorded["dtype"] or list(array.shape) != recorded["shape"]
                or hashlib.sha256(array.tobytes(order="C")).hexdigest() != recorded["sha256"]):
            raise ValueError("Saved element Hu field differs from its original descriptor")
        calls["selected_array_fields"] += 1
        checkpoint()
    calls["NPZ_read_completed"] += 1
    return array


def csv_identity(row):
    return dict(index=int(row["index"]), original_target_index=int(row["original_target_index"]),
        leg=row["leg"], d_mm=float(row["d_mm"]), state_sha256=row["state_sha256"])


def selected_csv(path):
    with path.open(newline="", encoding="utf-8") as stream:
        return [dict(row) for row in csv.DictReader(stream) if int(row["index"]) in (6, 13)]


def vector_fields(prefix, values):
    return {prefix+"_F"+axis+"_N": values[index] for index, axis in enumerate("xy")}


def write_csv(name, rows):
    with (output/name).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def tables(observations, categories):
    cells, groups, whole, nodes, endpoints = [], [], [], [], []
    for observation in observations:
        base = observation["identity"]
        for cell in observation["cells"]:
            row = dict(base, cell_id=cell["cell_id"], group=cell["group"], node_ids=json.dumps(cell["node_ids"]),
                selected_local_indices=json.dumps(cell["selected_local_indices"]), selected_body_node_ids=json.dumps(cell["selected_body_node_ids"]),
                selected_local_node_count=cell["selected_local_node_count"], Q1_pattern_numeric_exact=cell["Q1_pattern_numeric_exact"])
            for index, value in enumerate(cell["original_local_internal_Hu_force_N"]):
                row.update(vector_fields("original_"+str(index)+"_internal_Hu", value))
            row.update(vector_fields("selected_body_Hu", cell["force_on_body_N"]))
            cells.append(row)
        for name, group in observation["groups"].items():
            groups.append(dict(base, group=name, cell_count=group["cell_count"], local_occurrence_count=group["local_occurrence_count"],
                **vector_fields("selected_body_Hu", group["force_on_body_N"])))
        row = dict(base)
        for name in ("regrouped_local_Hu_on_body_N", "original_node_Hu_on_body_N", "original_state_Hu_on_body_N", "corner_only_Hu_on_body_N"):
            row.update(vector_fields(name.removesuffix("_N"), observation["whole"][name]))
        for name in ("original_node_L1_comparison", "selected_local_L1_comparison"):
            row.update(vector_fields(name+"_error", observation["whole"][name]["error_N"]))
            row.update(vector_fields(name+"_roundoff_bound", observation["whole"][name]["roundoff_bound_N"]))
        for name, value in observation["whole"]["descriptive_differences_N"].items():
            row.update(vector_fields(name, value))
        whole.append(row)
        for node in observation["nodes"]:
            nodes.append(dict(node["original_node_record"], selected_local_occurrences=node["selected_local_occurrences"],
                **vector_fields("regrouped_local_Hu", node["regrouped_local_Hu_on_body_N"]),
                **vector_fields("local_regrouping_error", node["local_regrouping"]["error_N"]),
                **vector_fields("local_regrouping_roundoff_bound", node["local_regrouping"]["roundoff_bound_N"])))
        for endpoint in observation["selected_endpoints"]:
            endpoints.append(dict(base, cell_id=endpoint["cell_id"], group=endpoint["group"],
                local_node_index=endpoint["local_node_index"], local_node_name=endpoint["local_node_name"], node_id=endpoint["node_id"],
                x_mm=endpoint["coordinates_mm"][0], y_mm=endpoint["coordinates_mm"][1], selected_body_node=endpoint["selected_body_node"],
                **vector_fields("original_internal_Hu", endpoint["original_internal_Hu_force_N"]),
                **vector_fields("negative_local_Hu_covector", endpoint["negative_local_Hu_covector_N"]), covector_scope=endpoint["covector_scope"]))
    for name, rows in (("cells.csv", cells), ("groups.csv", groups), ("whole.csv", whole), ("nodes.csv", nodes),
                       ("selected_endpoints.csv", endpoints), ("node_categories.csv", categories)):
        write_csv(name, rows)
    return dict(cells_total=len(cells), group_rows_total=len(groups), whole_rows_total=len(whole), nodes_total=len(nodes),
        selected_endpoint_rows_total=len(endpoints), node_category_rows_total=len(categories))


def render(observations, categories):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 3, figsize=(16, 10), layout="constrained")
    for state_index, observation in enumerate(observations):
        for column, cell_id in enumerate(protocol["selected_endpoint_cell_ids"]):
            endpoints = [row for row in observation["selected_endpoints"] if row["cell_id"] == cell_id]
            xy = np.asarray([row["coordinates_mm"] for row in endpoints])
            vectors = np.asarray([row["negative_local_Hu_covector_N"] for row in endpoints])
            maximum = float(np.max(np.abs(vectors)))
            scale = .16/maximum if maximum else 1.  # display length only; values are unchanged
            selected = np.asarray([row["selected_body_node"] for row in endpoints])
            ax = axes[state_index, column]
            closed = np.vstack((xy, xy[:1]))
            ax.plot(*closed.T, color="0.5", linewidth=1.)
            ax.quiver(*xy.T, *(vectors*scale).T, color=["#c43b21" if value else "#6c7c8c" for value in selected],
                angles="xy", scale_units="xy", scale=1., width=.006, minlength=0, minshaft=1)
            ax.scatter(*xy.T, c=["#c43b21" if value else "#6c7c8c" for value in selected], s=30, zorder=4)
            for row in endpoints:
                x, y = row["coordinates_mm"]
                vx, vy = row["negative_local_Hu_covector_N"]
                dx = -.22 if row["local_node_index"] in (0, 3) else .04
                dy = -.10 if row["local_node_index"] in (0, 1) else .04
                ax.text(x+dx, y+dy, f"{row['local_node_name']} node {row['node_id']}\n({'ON-body' if row['selected_body_node'] else 'local only'})\nFx {vx:+.5e}\nFy {vy:+.5e}", fontsize=7)
            ax.set(xlim=(xy[:, 0].min()-.4, xy[:, 0].max()+.4), ylim=(xy[:, 1].min()-.3, xy[:, 1].max()+.3),
                xlabel="reference x (mm)", ylabel="reference y (mm)",
                title=f"state {observation['identity']['index']} / cell {cell_id} / {endpoints[0]['group']}\nIndependent arrow scale: {scale:.5e} mm/N")
            ax.set_aspect("equal")
    fig.suptitle("Saved Q1 Hu negative local covectors (N), including original thickness\nRed selected vertices act ON-body; blue-grey other vertices are local covectors, not applied body loads. Reference geometry; no pressure recovery.")
    fig.savefig(output/"Q1_Hu_endpoint_actions.png", dpi=150)
    plt.close(fig)
    calls["PNG_writes"] += 1
    checkpoint()
    fig, axes = plt.subplots(2, 2, figsize=(16, 12), layout="constrained")
    for row_index, observation in enumerate(observations):
        corners = observation["corner_only_cells"]
        node_groups = [row for row in categories if int(row["index"]) == observation["identity"]["index"]]
        labels = list(observation["groups"])+["corner cell "+str(cell["cell_id"]) for cell in corners]+["original whole"]
        labels += ["node: "+row["category"] for row in node_groups]
        for axis in (0, 1):
            values = [group["force_on_body_N"][axis] for group in observation["groups"].values()]
            values += [cell["force_on_body_N"][axis] for cell in corners]
            values += [observation["whole"]["original_state_Hu_on_body_N"][axis]]
            values += [float(row["regularization_F"+"xy"[axis]+"_N"]) for row in node_groups]
            ax = axes[row_index, axis]
            bars = ax.bar(range(len(values)), values, color=["#547a9b"]*5+["#e49a54"]*2+["#313f4b"]+["#75a87c"]*7)
            ax.bar_label(bars, fmt="%+.5e", fontsize=6, padding=3, rotation=90)
            ax.axhline(0., color="black", linewidth=.6)
            ax.axvline(4.5, color="0.4", linestyle=":")
            ax.axvline(7.5, color="0.4", linestyle=":")
            ax.margins(y=.35)
            ax.set_xticks(range(len(labels)), labels, rotation=65, ha="right", fontsize=7)
            ax.set(title=f"state {observation['identity']['index']} / d={observation['identity']['d_mm']} mm / independent panel scale",
                ylabel="signed Hu F"+"xy"[axis]+" (N)")
    fig.suptitle("Five owner-role columns partition local Hu; last seven columns are preserved node-category observations\nTwo corner columns and original whole are comparisons. Never add across partitions. Side-pair zero net does not imply zero edge-node Hu.")
    fig.savefig(output/"Hu_owner_node_comparison.png", dpi=150)
    plt.close(fig)
    calls["PNG_writes"] += 1
    checkpoint()


def run():
    if (protocol["schema_version"] != "saved-Q1-Hu-boundary-card-1.0" or args.time_limit != 180.
            or [item["index"] for item in protocol["selected_states"]] != [6, 13]
            or protocol["selected_endpoint_cell_ids"] != [10371, 10407, 10408]):
        raise ValueError("M-BOUND1 requires180s, original states6/13 and three preserved endpoint cells")
    for name, pin in protocol["bindings"].items():
        if sha(repo/name) != pin:
            raise ValueError("Bound source/input changed: "+name)
        checkpoint()
    metadata, result = read(repo/protocol["model_file"]), read(repo/protocol["result_file"])
    if (metadata["task_sha256"] != result["task_sha256"] or metadata["arrays"]["sha256"] != result["model"]["arrays_sha256"]
            or sha(repo/protocol["model_file"]) != result["model"]["descriptor_file_sha256"]
            or metadata["schema_version"] != "hf-native-project-model-1.1" or metadata["element_node_order"] != ["BL", "BR", "TR", "TL"]
            or metadata["task"]["workpiece"] != dict(kind="fixed_rigid", shape="square", center_mm=[71., 40.], side_mm=18., fixed_components=[0, 1])
            or metadata["grid"]["cell_size_mm"] != [.5, .5] or metadata["material"]["thickness_mm"] != 20.):
        raise ValueError("Require the preserved h0.5 fixed-square task and original result/model identity")
    support_rows = selected_csv(repo/protocol["material_support_cells_file"])
    original_nodes = selected_csv(repo/protocol["ledger_nodes_file"])
    original_categories = selected_csv(repo/protocol["ledger_categories_file"])
    if len(support_rows) != 1444 or len(original_nodes) != 1406 or len(original_categories) != 14:
        raise ValueError("Selected original topology/node/category record counts differ")
    sys.path.insert(0, str(repo/"hf_repo/src"))
    from hf_eval.saved_q1_hu_boundary import observe_saved_q1_hu_boundary
    observations = []
    for identity in protocol["selected_states"]:
        index, key = identity["index"], str(identity["index"])
        state, original = read(repo/protocol["state_files"][key]), result["states"][index]
        for record in (state, original):
            if dict(index=index, original_target_index=record["original_target_index"], leg=record["leg"], d_mm=record["d"], state_sha256=record["state_sha256"]) != identity:
                raise ValueError("Selected identity differs from the original state/result record")
        if state != {name: value for name, value in original.items() if name not in ("descriptor_path", "descriptor_file_sha256")}:
            raise ValueError("Selected original state descriptor and result record differ")
        cells = []
        for row in support_rows:
            if int(row["index"]) == index:
                cells.append(dict(identity=csv_identity(row), cell_id=int(row["cell_id"]), group=row["group"],
                    selected_local_node_count=int(row["selected_local_node_count"]), node_ids=json.loads(row["node_ids"]),
                    selected_local_indices=json.loads(row["selected_local_indices"]), selected_body_node_ids=json.loads(row["selected_body_node_ids"])))
        nodes = [row for row in original_nodes if int(row["index"]) == index]
        categories = [row for row in original_categories if int(row["index"]) == index]
        expected_categories = ("bottom_side_interior", "left_side_interior", "right_side_interior", "physical_corner", "physical_and_cut", "cut_interior", "body_interior")
        if len(categories) != 7 or tuple(row["category"] for row in categories) != expected_categories or any(csv_identity(row) != identity for row in categories):
            raise ValueError("Preserved seven node categories or their identities differ")
        base = (repo/protocol["state_files"][key]).parent.parent.parent
        force = selected_array(base/state["forces"]["path"], state["forces"])
        calls["hu_boundary_started"] += 1
        observation = observe_saved_q1_hu_boundary(force, cells, nodes, metadata["region_metadata"]["workpiece"], metadata["grid"],
            identity=identity, original_whole_regularization_N=state["workpiece"]["force_on_lower_body_N"]["regularization"],
            selected_endpoint_cell_ids=protocol["selected_endpoint_cell_ids"], global_fixed_dofs=metadata["region_metadata"]["fixed_dofs"])
        calls["hu_boundary_completed"] += 1
        if observation["counts"] != dict(cells=722, local_occurrences=2738, groups=5, whole=1, nodes=703, selected_endpoints=12):
            raise ValueError("Hu support observation counts differ from the frozen contract")
        observations.append(observation)
        del force
        checkpoint()
    counts = tables(observations, original_categories)
    if counts != protocol["expected_counts"]:
        raise ValueError("Hu boundary table counts differ from the frozen protocol")
    write_json(output/"hu_boundary.json", dict(schema_version="saved-two-state-Q1-Hu-boundary-1.0", states=observations,
        original_node_categories=original_categories, counts=counts,
        actual_deformation_view=protocol["actual_deformation_view"], geometry_scope="Reference grid only; reuse original actual-deformation view"))
    render(observations, original_categories)
    if calls != protocol["expected_calls"]:
        raise ValueError("Hu boundary read/API/PNG counts differ from the frozen protocol")
    for name, pin in protocol["bindings"].items():
        if sha(repo/name) != pin:
            raise ValueError("Original source/input changed: "+name)
        checkpoint()
    if {path.name for path in output.iterdir()} != set(protocol["expected_output_files"])-{"execution_receipt.json"}:
        raise ValueError("Hu boundary output filenames differ from the frozen contract")
    output_hashes = {path.name: sha(path) for path in output.iterdir()}
    checkpoint()
    return dict(status="pass", calls=calls, counts=counts, protocol_sha256=sha(protocol_file), all_bindings_unchanged=True,
        elapsed_seconds=perf_counter()-STARTED, sampled_peak_RSS_bytes=peak, output_SHA256=output_hashes,
        source_scope="Two saved Hu fields, preserved support topology and original node/category strings; two ordinary APIs, original body-only C-order scatter, selected-local fsum and two reference PNGs. No Hu/J/P/kinematics reconstruction, old ledger call, new force-kernel/tangent/HP/equilibrium/energy-gradient call, pressure or effective-grip qualification", mechanical_hooks_monitored=False)


def main():
    output.mkdir(parents=True, exist_ok=False)
    try:
        receipt = run()
    except BaseException as error:
        write_json(output/"execution_receipt.json", dict(status="not_pass", error=repr(error), calls=calls,
            elapsed_seconds=perf_counter()-STARTED, sampled_peak_RSS_bytes=peak))
        raise
    write_json(output/"execution_receipt.json", receipt)
    print(json.dumps(dict(status="pass", calls=calls)), flush=True)


if __name__ == "__main__":
    main()
