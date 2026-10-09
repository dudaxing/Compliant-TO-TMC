"""Observe only the saved fine cycle; compare already derived coarse values."""
from time import perf_counter
STARTED = perf_counter()
from pathlib import Path
from hashlib import sha256
import argparse
import csv
import json
import runpy
import sys

METRICS = ("R_input_N", "q_out_mm", "total_body_Fy_N", "material_body_Fy_N",
           "regularization_body_Fy_N", "cached_two_sided_normal_magnitude_sum_N",
           "tip_x_mm", "tip_y_mm", "tip_to_bottom_mm", "tip_to_left_mm",
           "tip_to_right_mm", "solid_min_J", "medium_min_J",
           "medium_max_abs_Hu_per_mm")


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")


def matched_rows(result, summary, csv_file):
    """Join stored derivations to original target identities, without observers."""
    assert summary["production_status"] == result["status"] == "success"
    assert summary["accepted_states"] == result["accepted_states"] == 24
    assert len(summary["rows"]) == len(result["states"]) == 24
    with csv_file.open(encoding="utf-8", newline="") as stream:
        table = list(csv.DictReader(stream))
    assert len(table) == 24
    rows = {}
    for index, (state, derived, row) in enumerate(zip(result["states"], summary["rows"], table)):
        assert state["is_original_target"] is True
        identity = (state["original_target_index"], state["leg"], state["is_original_target"])
        assert identity not in rows and state["original_target_index"] == index
        assert derived["index"] == int(row["index"]) == index
        assert derived["state_sha256"] == row["state_sha256"] == state["state_sha256"]
        assert derived["original_target_index"] == int(row["original_target_index"]) == identity[0]
        assert derived["leg"] == row["leg"] == identity[1]
        assert derived["d_mm"] == float(row["d_mm"]) == state["d"] == result["targets_mm"][index]
        assert all(float(row[name]) == derived[name] for name in METRICS)
        rows[identity] = dict(index=index, state_sha256=state["state_sha256"], d_mm=state["d"],
                              **{name: derived[name] for name in METRICS})
    return rows


def compare(coarse_result, coarse_summary, coarse_csv, fine_result, fine_summary, fine_csv,
            output, checkpoint):
    import matplotlib.pyplot as plt
    coarse = matched_rows(coarse_result, coarse_summary, coarse_csv)
    fine = matched_rows(fine_result, fine_summary, fine_csv)
    assert coarse.keys() == fine.keys() and coarse_result["targets_mm"] == fine_result["targets_mm"]
    rows, table = [], []
    for identity, first in coarse.items():
        second = fine[identity]
        assert first["d_mm"] == second["d_mm"]
        rows.append(dict(original_target_index=identity[0], leg=identity[1], is_original_target=True,
                         d_mm=first["d_mm"], coarse=first, fine=second,
                         fine_minus_coarse={name: second[name]-first[name] for name in METRICS}))
        flat = dict(original_target_index=identity[0], leg=identity[1], is_original_target=True,
                    d_mm=first["d_mm"], coarse_index=first["index"], fine_index=second["index"],
                    coarse_state_sha256=first["state_sha256"], fine_state_sha256=second["state_sha256"])
        flat.update({mesh+"_"+name: values[name] for mesh, values in (("coarse", first), ("fine", second)) for name in METRICS})
        flat.update({"fine_minus_coarse_"+name: second[name]-first[name] for name in METRICS})
        table.append(flat)
    write(output/"mesh_comparison.json", dict(schema_version="same-design-saved-view-comparison-1.0",
          status="matched_saved_values", matched_original_targets=24, rows=rows,
          coarse_observer_calls=0, new_mechanical_calls=0, independent_reference="not_provided",
          mesh_convergence_qualified=False, contact_pressure_clamping_qualified=False,
          scope="Two-grid sensitivity of saved observations; unsigned finite tip distances, weak body forces; no pressure, HP or convergence qualification"))
    with (output/"mesh_comparison.csv").open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(table[0]))
        writer.writeheader()
        writer.writerows(table)
    checkpoint()
    plots = (("R_input_N", "Input reaction [N]"), ("total_body_Fy_N", "Lower-body signed Fy [N]"),
             ("q_out_mm", "Weighted output displacement [mm]"),
             ("tip_to_bottom_mm", "Unsigned finite tip-to-bottom distance [mm]"),
             ("medium_min_J", "Free-medium minimum integration-point J"),
             ("medium_max_abs_Hu_per_mm", "Free-medium max absolute Hu component [1/mm]"))
    fig, axes = plt.subplots(2, 3, figsize=(15, 8), layout="constrained")
    for ax, (name, title) in zip(axes.flat, plots):
        checkpoint()
        if name == "medium_min_J":
            assert all(row[mesh][name] > 0 for row in rows for mesh in ("coarse", "fine"))
            ax.set_yscale("log")
        for mesh, colour in (("coarse", "#457b9d"), ("fine", "#c43b21")):
            for leg, style, marker in (("loading", "-", "o"), ("unloading", "--", "v")):
                selected = [row for row in rows if row["leg"] == leg or (leg == "loading" and row["leg"] == "origin")]
                ax.plot([row["d_mm"] for row in selected], [row[mesh][name] for row in selected],
                        color=colour, linestyle=style, marker=marker, markersize=3,
                        label=("h=1 mm" if mesh == "coarse" else "h=0.5 mm")+" "+leg)
        ax.set(xlabel="Mean input displacement [mm]", ylabel=title, title=title)
        ax.grid(alpha=.2)
        ax.legend(fontsize=7)
    fig.suptitle("Same geometry and physical task | original targets only | production observations; two-grid sensitivity")
    fig.savefig(output/"mesh_response_comparison.png", dpi=150)
    plt.close(fig)
    checkpoint()
    return dict(matched_original_targets=24, coarse_observer_calls=0,
                table="mesh_comparison.csv", data="mesh_comparison.json", image="mesh_response_comparison.png")


def main():
    parser = argparse.ArgumentParser(add_help=False)
    for name in ("repo", "protocol", "output", "stop-file"):
        parser.add_argument("--"+name, type=Path, required=True)
    parser.add_argument("--time-limit", type=float, required=True)
    args, _ = parser.parse_known_args()
    root, output = args.repo.resolve().parent, args.output.resolve()
    protocol_file = args.protocol.resolve()
    protocol = read(protocol_file)
    assert protocol_file.parent == Path(__file__).resolve().parent
    assert output == root/protocol["output_directory"] and not output.exists()
    assert args.time_limit == protocol["phases"]["view"]["helper_seconds"] == 600
    assert protocol["phases"]["view"]["outer_seconds"] == 660 and protocol["sampled_RSS_bytes"] == 8*1024**3
    import psutil
    process = psutil.Process()
    peak, saved, failure, comparison = 0, {}, None, None
    bindings_unchanged = False
    comparison_started = comparison_completed = 0

    def checkpoint():
        nonlocal peak
        memory = process.memory_info()
        peak = max(peak, memory.rss, getattr(memory, "peak_wset", memory.rss))
        assert perf_counter()-STARTED <= 600 and peak <= protocol["sampled_RSS_bytes"], "Saved-view helper time/RSS budget"
        assert not args.stop_file.exists(), "Saved-view supervisor requested stop"

    try:
        checkpoint()
        fine_result = read(root/protocol["fine_result"])
        response = read(root/protocol["fine_response"])
        fine_model = read(root/protocol["fine_model"])
        coarse_result = read(root/protocol["coarse_result"])
        coarse_model = read(root/protocol["coarse_model"])
        coarse_view = read(root/protocol["coarse_view"])
        assert fine_result["status"] == "success" and fine_result["path_completed"] and fine_result["unload_endpoint_reached"]
        assert fine_result["accepted_states"] == len(fine_result["states"]) == protocol["expected_observations_each"] == 24
        assert fine_result["counts"] == fine_model["region_metadata"]["counts"] == protocol["expected_fine_counts"]
        assert response["independent_reference"]["status"] == response["views"]["status"] == "not_provided" and all(x is False for x in response["producer_flags"].values())
        assert coarse_view["schema_version"] == "saved-shifted-workpiece-views-1.0" and coarse_view["status"] == "pass"
        coarse_base = (root/protocol["coarse_view"]).parent
        assert coarse_view["input_source_bindings"][protocol["coarse_result"]] == protocol["bindings"][protocol["coarse_result"]]
        for field in ("coarse_summary", "coarse_csv"):
            relative = (root/protocol[field]).relative_to(coarse_base).as_posix()
            assert coarse_view["outputs"][relative] == protocol["bindings"][protocol[field]]
        nonphysical = {"task_id", "geometry", "purpose", "parameter_origin", "description"}
        assert {k:v for k,v in coarse_model["task"].items() if k not in nonphysical} == {k:v for k,v in fine_model["task"].items() if k not in nonphysical}
        assert coarse_model["grid"]["extent_mm"] == fine_model["grid"]["extent_mm"] == [84., 40.]
        viewer = root/protocol["viewer_source"]
        original_argv = sys.argv[:]
        try:
            sys.argv = [str(viewer), *original_argv[1:]]
            runpy.run_path(str(viewer), run_name="__main__")
        finally:
            sys.argv = original_argv
        saved = read(output/"view.json")
        assert saved["status"] == "pass" and saved["new_F_T_model_solver_HP_calls"] == 0
        assert all(saved[key] == 24 for key in ("geometry_started", "geometry_completed", "nodal_started", "nodal_completed"))
        assert len(saved["cases"]) == 1 and saved["cases"][0]["label"] == "fixed_square"
        checkpoint()
        comparison_started = 1
        comparison = compare(coarse_result, read(root/protocol["coarse_summary"]), root/protocol["coarse_csv"],
                             fine_result, read(output/"fixed_square/summary.json"), output/"fixed_square/states.csv",
                             output, checkpoint)
        comparison_completed = 1
        checkpoint()
        bindings_unchanged = all(sha256((root/name).read_bytes()).hexdigest() == pin for name, pin in protocol["bindings"].items())
        assert bindings_unchanged
        checkpoint()
    except BaseException as error:
        failure = repr(error)
        raise
    finally:
        if output.exists():
            outputs = {p.relative_to(output).as_posix(): sha256(p.read_bytes()).hexdigest() for p in output.rglob("*") if p.is_file()}
            late_error, previous_failure = None, failure
            try:
                checkpoint()
            except Exception as error:
                late_error = error
                failure = failure or repr(error)
            write(output/"phase_view.json", dict(schema_version="nested-fine-saved-view-phase-1.0",
                  status="pass" if failure is None else "failed", failure=failure,
                  protocol_sha256=sha256(protocol_file.read_bytes()).hexdigest(), all_bindings_unchanged=bindings_unchanged,
                  raw_viewer_source=protocol["viewer_source"], raw_viewer_sha256=protocol["bindings"][protocol["viewer_source"]],
                  raw_view_manifest_sha256=sha256((output/"view.json").read_bytes()).hexdigest() if (output/"view.json").exists() else None,
                  fine_observation_counts={key:saved.get(key) for key in ("geometry_started", "geometry_completed", "nodal_started", "nodal_completed")},
                  coarse_observer_calls=0, comparison_started=comparison_started, comparison_completed=comparison_completed,
                  comparison=comparison, new_CLI_API_model_solver_F_T_HP_JIT_LF_calls=0 if saved.get("new_F_T_model_solver_HP_calls") == 0 else None,
                  mechanical_hooks_monitored=False, zero_mechanics_basis="Unchanged pinned pure saved viewer and scalar CSV/JSON comparison; no mechanical imports or callbacks",
                  elapsed_seconds=perf_counter()-STARTED, sampled_peak_helper_RSS_bytes=peak,
                  final_resource_check_passed=late_error is None, outputs=outputs,
                  qualification_scope="Production saved observations and two-grid sensitivity only; original response/reference flags unchanged"))
            if late_error is not None and previous_failure is None:
                raise late_error


if __name__ == "__main__":
    main()
