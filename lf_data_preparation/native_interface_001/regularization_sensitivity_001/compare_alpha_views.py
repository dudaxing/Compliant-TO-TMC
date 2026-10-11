"""Future saved-state alpha comparison, after the new production succeeds.

Runs in a fresh child so the unchanged viewer retains its pure import closure.
Original targets are matched explicitly; extra accepted bisections remain in
the raw view. No mechanics, pressure reconstruction or qualification upgrade.
"""
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
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def matched_originals(result, summary, table_path, prefix):
    """Check CSV/JSON identity and return the declared original-target subset."""
    assert result["status"] == summary["production_status"] == "success"
    states = result["states"]
    with table_path.open(encoding="utf-8", newline="") as stream:
        table = list(csv.DictReader(stream))
    assert len(states) == result["accepted_states"] == summary["accepted_states"] == len(summary["rows"]) == len(table)
    matched = {}
    for index, (state, derived, row) in enumerate(zip(states, summary["rows"], table)):
        assert derived["index"] == int(row["index"]) == index
        assert derived["state_sha256"] == row["state_sha256"] == state["state_sha256"]
        assert derived["original_target_index"] == int(row["original_target_index"]) == state["original_target_index"]
        assert derived["leg"] == row["leg"] == state["leg"]
        assert derived["d_mm"] == float(row["d_mm"]) == state["d"]
        assert all(derived[name] == float(row[name]) for name in METRICS)
        if not state["is_original_target"] or state["original_target_index"] >= len(prefix):
            continue
        target_index = state["original_target_index"]
        leg = "origin" if target_index == 0 else "loading" if prefix[target_index] > prefix[target_index-1] else "unloading"
        assert state["d"] == state["original_target_displacement"] == prefix[target_index]
        assert state["leg"] == leg and target_index not in matched
        matched[target_index] = dict(index=index, state_sha256=state["state_sha256"], leg=leg,
                                     d_mm=state["d"], **{name: derived[name] for name in METRICS})
    assert set(matched) == set(range(len(prefix)))
    return matched


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--time-limit", type=float, required=True,
                        help="Remaining enclosing helper time; never adds a window")
    args = parser.parse_args()
    root = args.repo.resolve()
    protocol_file = args.protocol.resolve()
    protocol = read(protocol_file)
    view = root / protocol["view_directory"]
    stop = protocol_file.parent / "stop_requested.txt"
    viewer = root / protocol["viewer_source"]
    candidate = root / protocol["candidate_directory"]
    limit = min(protocol["view_seconds"], args.time_limit)
    assert limit > 0
    assert not view.exists()
    assert all(sha256((root/name).read_bytes()).hexdigest() == pin for name, pin in protocol["bindings"].items())
    original_argv = sys.argv[:]
    try:
        sys.argv = [str(viewer), "--repo", str(root/"hf_repo"), "--protocol", str(protocol_file),
                    "--output", str(view), "--case", "alpha_half=" + str(candidate),
                    "--stop-file", str(stop), "--time-limit", str(limit)]
        runpy.run_path(str(viewer), run_name="__main__")
    finally:
        sys.argv = original_argv
    raw = read(view/"view.json")
    assert raw["status"] == "pass" and raw["new_F_T_model_solver_HP_calls"] == 0
    actual = read(candidate/"result.json")
    n = actual["accepted_states"]
    assert all(raw[key] == n for key in ("geometry_started", "geometry_completed", "nodal_started", "nodal_completed"))

    import psutil
    process = psutil.Process()

    def checkpoint():
        assert perf_counter()-STARTED <= limit and not stop.exists(), "View window closed"
        assert max(process.memory_info().rss, getattr(process.memory_info(), "peak_wset", 0)) <= protocol["sampled_RSS_bytes"]

    checkpoint()
    prefix = protocol["targets_mm"]
    baseline = matched_originals(read(root/protocol["baseline_result"]), read(root/protocol["baseline_summary"]),
                                 root/protocol["baseline_csv"], prefix)
    changed = matched_originals(actual, read(view/"alpha_half/summary.json"), view/"alpha_half/states.csv", prefix)
    assert actual["targets_mm"] == prefix and actual["path_kind"] == "ordered_cycle"
    rows = []
    for target_index in range(len(prefix)):
        first, second = baseline[target_index], changed[target_index]
        row = dict(original_target_index=target_index, leg=first["leg"], d_mm=first["d_mm"],
                   baseline_index=first["index"], candidate_index=second["index"],
                   baseline_state_sha256=first["state_sha256"], candidate_state_sha256=second["state_sha256"])
        row.update({label+"_"+name: source[name] for label, source in (("baseline", first), ("candidate", second)) for name in METRICS})
        row.update({"candidate_minus_baseline_"+name: second[name]-first[name] for name in METRICS})
        rows.append(row)
    with (view/"alpha_comparison.csv").open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    write(view/"alpha_comparison.json", dict(status="matched_saved_original_targets", rows=rows,
          baseline_alpha=1e-6, candidate_alpha=5e-7, matched_original_targets=len(prefix),
          baseline_observer_calls=0, new_mechanical_calls=0, stability_qualified=False,
          scope="Single-factor two-value sensitivity, common 15-target prefix; extra accepted states in raw view only"))
    import matplotlib.pyplot as plt
    plots = (("R_input_N", "Input reaction [N]"), ("total_body_Fy_N", "Lower-body signed Fy [N]"),
             ("q_out_mm", "Weighted output displacement [mm]"),
             ("tip_to_bottom_mm", "Unsigned finite tip-to-bottom distance [mm]"),
             ("medium_min_J", "Free-medium minimum integration-point J"),
             ("medium_max_abs_Hu_per_mm", "Free-medium max absolute Hu component [1/mm]"))
    fig, axes = plt.subplots(2, 3, figsize=(15, 8), layout="constrained")
    for ax, (name, title) in zip(axes.flat, plots):
        checkpoint()
        if name == "medium_min_J":
            assert all(row[label+"_"+name] > 0 for row in rows for label in ("baseline", "candidate"))
            ax.set_yscale("log")
        for label, colour, text in (("baseline", "#457b9d", "alpha=1e-6"), ("candidate", "#c43b21", "alpha=5e-7")):
            for leg, style, marker in (("loading", "-", "o"), ("unloading", "--", "v")):
                selected = [row for row in rows if row["leg"] == leg or (leg == "loading" and row["leg"] == "origin")]
                if leg == "unloading":
                    selected.insert(0, rows[13])
                ax.plot([row["d_mm"] for row in selected], [row[label+"_"+name] for row in selected],
                        color=colour, linestyle=style, marker=marker, markersize=3, label=text+" "+leg)
        ax.set(title=title, xlabel="Mean input displacement [mm]", ylabel=title)
        ax.grid(alpha=.2)
        ax.legend(fontsize=7)
    fig.suptitle("Same h=0.5 mm task | alpha only | original targets | one unloading step; sensitivity only")
    fig.savefig(view/"alpha_response_comparison.png", dpi=150)
    plt.close(fig)
    checkpoint()
    assert all(sha256((root/name).read_bytes()).hexdigest() == pin for name, pin in protocol["bindings"].items())
    write(view/"alpha_view_receipt.json", dict(status="pass", accepted_states=n,
          matched_original_targets=len(prefix), actual_observation_counts={key:raw[key] for key in (
              "geometry_started", "geometry_completed", "nodal_started", "nodal_completed")},
          raw_viewer_sha256=sha256(viewer.read_bytes()).hexdigest(), protocol_sha256=sha256(protocol_file.read_bytes()).hexdigest(),
          all_bindings_unchanged=True, elapsed_seconds=perf_counter()-STARTED,
          elapsed_scope="Before final success receipt write; enclosing helper and outer include child completion",
          new_mechanical_calls=0, new_baseline_observer_calls=0,
          mechanical_hooks_monitored=False, stability_pressure_clamp_HF5_qualified=False))


if __name__ == "__main__":
    main()
