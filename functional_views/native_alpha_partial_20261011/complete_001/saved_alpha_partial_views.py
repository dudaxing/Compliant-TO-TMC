"""M-AVIEW1: observe saved failed alpha loading states, never resume mechanics.

Reuse the unchanged pure square viewer once. Compare existing baseline records,
and copy two actual GIF frames for direct loading-state inspection.
"""
from time import perf_counter
STARTED = perf_counter()
import argparse
import csv
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import sys

METRICS = ("R_input_N", "q_out_mm", "total_body_Fy_N", "material_body_Fy_N",
    "regularization_body_Fy_N", "cached_two_sided_normal_magnitude_sum_N", "tip_x_mm",
    "tip_y_mm", "tip_to_bottom_mm", "tip_to_left_mm", "tip_to_right_mm", "solid_min_J",
    "medium_min_J", "medium_max_abs_Hu_per_mm")


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    value = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024*1024), b""):
            value.update(block)
    return value.hexdigest()


def write(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+"\n")


def matched_originals(result, summary, table_path, prefix):
    """Match ordinary saved rows without changing failed production status."""
    assert result["status"] == summary["production_status"]
    with table_path.open(encoding="utf-8",newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert result["accepted_states"] == summary["accepted_states"] == len(result["states"]) == len(summary["rows"]) == len(rows)
    matched = {}
    for index,(state,derived,row) in enumerate(zip(result["states"],summary["rows"],rows)):
        assert derived["index"] == int(row["index"]) == index
        assert state["state_sha256"] == derived["state_sha256"] == row["state_sha256"]
        assert state["original_target_index"] == derived["original_target_index"] == int(row["original_target_index"])
        assert state["leg"] == derived["leg"] == row["leg"] and state["d"] == derived["d_mm"] == float(row["d_mm"])
        assert all(derived[name] == float(row[name]) for name in METRICS)
        target = state["original_target_index"]
        if not state["is_original_target"] or target >= len(prefix):
            continue
        assert target not in matched and state["d"] == state["original_target_displacement"] == prefix[target]
        assert state["leg"] == ("origin" if target == 0 else "loading")
        matched[target] = dict(index=index,state_sha256=state["state_sha256"],leg=state["leg"],d_mm=state["d"],
                               **{name:derived[name] for name in METRICS})
    assert set(matched) == set(range(len(prefix)))
    return matched


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo",type=Path,required=True)
    parser.add_argument("--protocol",type=Path,required=True)
    args = parser.parse_args()
    root, protocol_file = args.repo.resolve(), args.protocol.resolve()
    protocol = read(protocol_file)
    stage = protocol_file.parent
    auth, reply = read(stage/"author/authorization.json"), read(stage/"author/direct_human_reply.json")
    head = subprocess.check_output(["git","rev-parse","HEAD"],cwd=root,text=True).strip()
    assert auth["authorized"] is True and auth["card"] == reply["card"] == "M-AVIEW1"
    assert auth["approved_source_commit"] == reply["approved_source_commit"] == head
    assert auth["protocol_sha256"] == sha(protocol_file) and auth["human_evidence_sha256"] == sha(stage/"author/direct_human_reply.json")
    assert auth["authorization_from_direct_human_reply"] is True and reply["authorization_from_direct_human_reply"] is True
    assert auth["direct_human_answer"] == reply["direct_human_answer"] and reply["direct_human_answer"].strip() and reply["reply_context"]
    proof_file = stage/"author/M_AVIEW1_source_publication_receipt.json"
    proof = read(proof_file)
    assert sha(proof_file) == auth["source_publication_receipt_sha256"] and proof["published_commit"] == head
    assert proof["status"] == "published_and_incrementally_restored_pass" and proof["prepared_card"] == "M-AVIEW1"
    assert proof["authorized"] is False and proof["executed"] is False
    assert all(sha(root/name) == pin for name,pin in protocol["bindings"].items())
    candidate, out = root/protocol["candidate_directory"], root/protocol["view_directory"]
    actual, prefix = read(candidate/"result.json"), protocol["targets_mm"]
    assert len(prefix) == actual["accepted_states"] == len(actual["states"]) == 14
    assert actual["status"] == "failed" and actual["failure"]["code"] == "time_limit"
    assert actual["path_kind"] == "ordered_cycle" and actual["targets_mm"][:14] == prefix
    assert actual["loading_peak_reached"] is True
    assert actual["path_completed"] is False and actual["unload_endpoint_reached"] is False and actual["task_target_executed"] is False
    assert all(flag is False for flag in (actual["independent_HP_qualified"],actual["equilibrium_qualified"],actual["HF_qualified"]))
    for i,state in enumerate(actual["states"]):
        assert state["is_original_target"] and state["original_target_index"] == i and state["d"] == state["original_target_displacement"] == prefix[i]
        assert state["leg"] == ("origin" if i == 0 else "loading")
    assert prefix[6] == .85 and prefix[13] == 1.20 and not out.exists()
    stop = stage/"stop_requested.txt"
    limit = protocol["phases"]["view"]["helper_seconds"]
    import psutil
    process = psutil.Process()
    peak_rss = 0

    def checkpoint():
        nonlocal peak_rss
        memory = process.memory_info()
        peak_rss = max(peak_rss,memory.rss,getattr(memory,"peak_wset",memory.rss))
        assert perf_counter()-STARTED <= limit and not stop.exists(), "Saved view window closed"
        assert peak_rss <= protocol["sampled_RSS_bytes"], "Sampled view memory bound exceeded"

    checkpoint()
    viewer = root/protocol["viewer_source"]
    original_argv = sys.argv[:]
    try:
        sys.argv = [str(viewer),"--repo",str(root/"hf_repo"),"--protocol",str(protocol_file),
            "--output",str(out),"--case","alpha_half="+str(candidate),
            "--stop-file",str(stop),"--time-limit",str(limit-(perf_counter()-STARTED))]
        runpy.run_path(str(viewer),run_name="__main__")
    finally:
        sys.argv = original_argv
    raw = read(out/"view.json")
    counts = {key:raw[key] for key in ("geometry_started","geometry_completed","nodal_started","nodal_completed")}
    assert raw["status"] == "pass" and all(value == 14 for value in counts.values())
    assert raw["new_F_T_model_solver_HP_calls"] == 0 and raw["mechanical_hooks_monitored"] is False
    assert len(raw["cases"]) == 1
    case = raw["cases"][0]
    assert case["label"] == "alpha_half" and case["saved_accepted_states"] == case["observed_states"] == 14
    assert case["production_status"] == "failed" and case["reference_available"] is False
    assert case["production_path_completed"] is False and case["unload_endpoint_reached"] is False
    checkpoint()
    baseline = matched_originals(read(root/protocol["baseline_result"]),read(root/protocol["baseline_summary"]),root/protocol["baseline_csv"],prefix)
    summary = read(out/"alpha_half/summary.json")
    changed = matched_originals(actual,summary,out/"alpha_half/states.csv",prefix)
    assert summary["reference_available"] is False
    rows = []
    for index in range(14):
        first, second = baseline[index], changed[index]
        row = dict(original_target_index=index,leg=second["leg"],d_mm=second["d_mm"],
            baseline_index=first["index"],candidate_index=second["index"],
            baseline_state_sha256=first["state_sha256"],candidate_state_sha256=second["state_sha256"])
        row.update({label+"_"+name:source[name] for label,source in (("baseline",first),("candidate",second)) for name in METRICS})
        row.update({"candidate_minus_baseline_"+name:second[name]-first[name] for name in METRICS})
        rows.append(row)
    with (out/"alpha_comparison.csv").open("x",encoding="utf-8",newline="") as stream:
        writer = csv.DictWriter(stream,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    write(out/"alpha_comparison.json",dict(status="matched_partial_saved_original_loading_targets",rows=rows,
        baseline_alpha=1e-6,candidate_alpha=5e-7,matched_original_targets=14,
        original_production_status=actual["status"],original_failure=actual["failure"],original_path_completed=False,
        baseline_observer_calls=0,new_mechanical_calls=0,stability_qualified=False,
        candidate_cached_workpiece_observations=[dict(index=i,state_sha256=s["state_sha256"],workpiece=s["workpiece"]) for i,s in enumerate(actual["states"])],
        scope="14 common original origin/loading targets; signed saved values and differences only. Lower-body weak forces, holding/mirror/net/magnitude retain their existing distinct meanings; no unload or pressure/clamp qualification."))
    import matplotlib.pyplot as plt
    plots = (("R_input_N","Input reaction [N]"),("total_body_Fy_N","Lower-body signed Fy [N]"),
        ("q_out_mm","Weighted output displacement [mm]"),("tip_to_bottom_mm","Unsigned finite tip-to-bottom distance [mm]"),
        ("medium_min_J","Free-medium minimum integration-point J"),("medium_max_abs_Hu_per_mm","Free-medium max absolute Hu component [1/mm]"))
    fig,axes = plt.subplots(2,3,figsize=(15,8),layout="constrained")
    for ax,(name,title) in zip(axes.flat,plots):
        checkpoint()
        if name == "medium_min_J":
            assert all(row[label+"_"+name] > 0 for row in rows for label in ("baseline","candidate"))
            ax.set_yscale("log")
        for label,colour,text in (("baseline","#457b9d","alpha=1e-6"),("candidate","#c43b21","alpha=5e-7 (partial failed path)")):
            ax.plot([row["d_mm"] for row in rows],[row[label+"_"+name] for row in rows],color=colour,marker="o",markersize=3,label=text)
        ax.set(title=title,xlabel="Mean input displacement [mm]",ylabel=title); ax.grid(alpha=.2); ax.legend(fontsize=7)
    fig.suptitle("Same h=0.5 mm task | alpha only | 14 accepted origin/loading states | sensitivity only")
    fig.savefig(out/"alpha_response_comparison.png",dpi=150); plt.close(fig)
    from PIL import Image
    snapshots = []
    with Image.open(out/"alpha_half/actual_states.gif") as gif:
        assert gif.n_frames == 14
        for index,name in ((6,"loading_085_forces.png"),(13,"loading_120_forces.png")):
            checkpoint(); gif.seek(index)
            frame = gif.copy().convert("RGB"); frame.save(out/name); frame.close()
            snapshots.append(dict(path=name,source="alpha_half/actual_states.gif",frame_index=index,
                original_target_index=index,leg=changed[index]["leg"],d_mm=changed[index]["d_mm"],state_sha256=changed[index]["state_sha256"],
                method="Copied decoded GIF frame pixels; existing three-component title/glyph scale retained, no new observation or rerender"))
    checkpoint()
    assert all(sha(root/name) == pin for name,pin in protocol["bindings"].items())
    final_output_hashes = {p.relative_to(out).as_posix():sha(p) for p in out.rglob("*") if p.is_file()}
    checkpoint()
    write(out/"alpha_partial_view_receipt.json",dict(status="pass",scope="Saved-state display/comparison only; original M-ALPHA1 execution remains not_pass",
        accepted_states=14,matched_original_targets=14,actual_observation_counts=counts,gif_frames=14,gif_snapshots=snapshots,
        original_production_status=actual["status"],original_failure=actual["failure"],original_path_completed=False,original_unload_endpoint_reached=False,
        protocol_sha256=sha(protocol_file),raw_viewer_sha256=sha(viewer),all_bindings_unchanged=True,
        outputs=final_output_hashes,
        elapsed_seconds=perf_counter()-STARTED,peak_sampled_RSS_bytes=peak_rss,
        elapsed_scope="Before final receipt write; outer includes complete helper/exit. Cooperative limits and RSS samples are not hard OS caps.",
        new_mechanical_calls=0,new_baseline_observer_calls=0,mechanical_hooks_monitored=False,
        stability_pressure_clamp_HF5_qualified=False))
    checkpoint()
    print(json.dumps(dict(status="pass",accepted_states=14,elapsed_seconds=perf_counter()-STARTED,peak_sampled_RSS_bytes=peak_rss)))


if __name__ == "__main__":
    main()
