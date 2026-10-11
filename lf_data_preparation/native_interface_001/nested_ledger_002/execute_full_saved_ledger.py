"""M-LEDGER2 candidate source only; full saved-table scope requires a new card."""
from time import perf_counter
STARTED = perf_counter()
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys
import psutil

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--repo",type=Path,required=True)
parser.add_argument("--protocol",type=Path,required=True)
parser.add_argument("--time-limit",type=float,required=True)
args = parser.parse_args()
repo,protocol_file = args.repo.resolve(),args.protocol.resolve()
read = lambda path:json.loads(path.read_text(encoding="utf-8"))
sha = lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
protocol = read(protocol_file)
output = repo/protocol["output_directory"]
process,peak = psutil.Process(),0
calls = dict(ledger_started=0,ledger_completed=0,PNG_writes=0)
PARTS = ("total","material","regularization")

def checkpoint():
    global peak
    peak = max(peak,process.memory_info().rss)
    if perf_counter()-STARTED > args.time_limit or peak > protocol["sampled_RSS_bytes"] or (protocol_file.parent/"stop_requested.txt").exists():
        raise RuntimeError("M-LEDGER2 cooperative resource/stop boundary reached")

def write_json(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")

def force_cells(forces):
    return {part+"_F"+axis+"_N":forces[part][index] for part in PARTS for index,axis in enumerate("xy")}

def paired_rows(ledger):
    baseline = {state["identity"]["d_mm"]:state for state in ledger["states"] if state["identity"]["leg"] in ("origin","loading")}
    unloading = {state["identity"]["d_mm"]:state for state in ledger["states"] if state["identity"]["leg"] == "unloading"}
    common = [d for d in baseline if d in unloading]
    if common != [0.,.25,.5,.65,.75,.8,.9,1.,1.1,1.15]:
        raise ValueError("Require the ten recorded exact-stroke pairs; no interpolation or synthetic unloading peak")
    identities = [dict(d_mm=d,baseline_index=baseline[d]["identity"]["index"],baseline_leg=baseline[d]["identity"]["leg"],
        baseline_state_sha256=baseline[d]["identity"]["state_sha256"],unloading_index=unloading[d]["identity"]["index"],
        unloading_leg=unloading[d]["identity"]["leg"],unloading_state_sha256=unloading[d]["identity"]["state_sha256"]) for d in common]
    if identities != protocol["paired_states"]:
        raise ValueError("Exact-stroke pair identities differ from the frozen protocol")
    rows = []
    for d in common:
        base,end = baseline[d],unloading[d]
        identity = {prefix+"_"+key:state["identity"][key] for prefix,state in (("baseline",base),("unloading",end))
            for key in ("index","original_target_index","leg","state_sha256")}
        for name in ledger["categories"]:
            before,after = (force_cells(state["categories"][name]["force_on_body_N"]) for state in (base,end))
            values = {prefix+"_"+key:value for prefix,vector in (("baseline",before),("unloading",after)) for key,value in vector.items()}
            values.update({"delta_unloading_minus_baseline_"+key:after[key]-before[key] for key in before})
            rows.append(dict(d_mm=d,category=name,**identity,baseline_node_count=base["categories"][name]["node_count"],
                unloading_node_count=end["categories"][name]["node_count"],**values))
    return rows

def render(ledger,pairs):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    states,names = ledger["states"],ledger["categories"]
    colors = dict(zip(names,plt.get_cmap("tab10").colors))
    fig,axes = plt.subplots(2,3,figsize=(14,8),sharex=True)
    branches = (("origin+loading",[s for s in states if s["identity"]["leg"] in ("origin","loading")],"-"),
        ("unloading",[s for s in states if s["identity"]["leg"] == "unloading"],"--"))
    for axis in (0,1):
        for column,part in enumerate(PARTS):
            ax = axes[axis,column]
            for label,branch,style in branches:
                for name in names:
                    ax.plot([s["identity"]["d_mm"] for s in branch],[s["categories"][name]["force_on_body_N"][part][axis] for s in branch],
                        marker="o",markersize=3,linestyle=style,color=colors[name],label=name if label == "origin+loading" else None)
            ax.axhline(0,color="black",linewidth=.5)
            ax.set(title=("Hu" if part == "regularization" else part)+" signed F"+"xy"[axis]+" (N)",xlabel="Mean input d (mm)")
    handles = [Line2D([0],[0],color=colors[name],label=name) for name in names]
    handles += [Line2D([0],[0],color="black",linestyle=style,label=label) for label,branch,style in branches]
    fig.legend(handles=handles,loc="lower center",ncol=3,fontsize=8)
    fig.suptitle("24 saved states: seven exclusive weak-load categories; actual branches, no interpolated states")
    fig.tight_layout(rect=(0,.12,1,.96))
    fig.savefig(output/"path_branches.png",dpi=150)
    plt.close(fig)
    calls["PNG_writes"] += 1
    checkpoint()
    fig,axes = plt.subplots(2,2,figsize=(16,8),sharex="col")
    indices = [s["identity"]["index"] for s in states]
    right = [next(row for row in s["nodes"] if int(row["node_id"]) == 10638) for s in states]
    for axis,ax in enumerate(axes[:,0]):
        for name in ("bottom_side_interior","physical_corner"):
            ax.plot(indices,[s["categories"][name]["force_on_body_N"]["regularization"][axis] for s in states],"o-",color=colors[name],markersize=3,label=name)
        ax.plot(indices,[float(row["regularization_F"+"xy"[axis]+"_N"]) for row in right],"o:",color="red",markersize=3,label="right-bottom node10638: SUBSET of physical_corner")
        ax.plot(indices,[s["whole"]["force_on_body_N"]["regularization"][axis] for s in states],"--",color="grey",label="whole-body net Hu (reference)")
        ax.axhline(0,color="black",linewidth=.5)
        ax.axvline(13,color="black",linestyle=":",linewidth=.8)
        ax.set(title="Original saved-target order",ylabel="Signed Hu F"+"xy"[axis]+" (N)")
        ax.legend(fontsize=7)
        delta_ax = axes[axis,1]
        for name in names:
            rows = [row for row in pairs if row["category"] == name]
            delta_ax.plot([row["d_mm"] for row in rows],[row["delta_unloading_minus_baseline_regularization_F"+"xy"[axis]+"_N"] for row in rows],"o-",markersize=3,color=colors[name],label=name)
        delta_ax.axhline(0,color="black",linewidth=.5)
        delta_ax.set(title="Exact-stroke pairs only: Hu unloading - baseline",ylabel="Signed delta Hu F"+"xy"[axis]+" (N)")
    axes[0,1].legend(fontsize=7)
    axes[1,0].set_xticks(indices,[str(i)+":"+s["identity"]["leg"][0]+" "+str(s["identity"]["d_mm"]) for i,s in zip(indices,states)],rotation=60,ha="right",fontsize=7)
    axes[1,0].set_xlabel("Original index:leg initial d(mm); peak13 loading, unloading starts14")
    common = [row["d_mm"] for row in pairs if row["category"] == names[0]]
    axes[1,1].set_xticks(common,["0(origin)" if d == 0 else str(d) for d in common],rotation=30,ha="right",fontsize=7)
    axes[1,1].set_xlabel("Mean input d(mm): zero baseline is origin; others loading; six deltas in CSV")
    fig.suptitle("Hu paths / exact pairs: node10638 is a physical_corner subset; do not add them or the whole net")
    fig.tight_layout()
    fig.savefig(output/"hu_target_path.png",dpi=150)
    plt.close(fig)
    calls["PNG_writes"] += 1
    checkpoint()

def run():
    if protocol["schema_version"] != "saved-fixed-square-full-ledger-card-1.0" or args.time_limit != 180. or protocol["selected_state_indices"] != list(range(24)):
        raise ValueError("M-LEDGER2 requires180s and original indices0..23")
    checkpoint()
    for name,pin in protocol["bindings"].items():
        if sha(repo/name) != pin:
            raise ValueError("Bound input/source changed: "+name)
    linked,view = read(repo/protocol["linked_response_file"]),read(repo/protocol["view_summary_file"])
    result,model = (read(repo/linked["identity"][key]["path"]) for key in ("result","model"))
    body_metadata = dict(linked["physics"],canonical_body_node_ids=model["region_metadata"]["workpiece"]["nodes"])
    if len(view["rows"]) != result["accepted_states"] or result["accepted_states"] != 24:
        raise ValueError("Require the closed24-state view/result identity source")
    for index,row in enumerate(view["rows"]):
        state = result["states"][index]
        if (row["index"],row["original_target_index"],row["leg"],row["d_mm"],row["state_sha256"]) != (
            index,state["original_target_index"],state["leg"],state["d"],state["state_sha256"]):
            raise ValueError("Original view/result state identity differs")
    records = {index:dict(identity=view["rows"][index],nodal=read(repo/protocol["nodal_files"][str(index)])) for index in range(24)}
    sys.path.insert(0,str(repo/"hf_repo/src"))
    from hf_eval.saved_workpiece_loads import summarize_saved_workpiece_node_ledger
    calls["ledger_started"] += 1
    ledger = summarize_saved_workpiece_node_ledger(repo/protocol["nodes_csv_file"],body_metadata,recorded_states=records,selected_states=None)
    calls["ledger_completed"] += 1
    checkpoint()
    previous = read(repo/protocol["reference_ledger_file"])
    if previous["selected_states"] != [0,8,13,23] or any(ledger[key] != previous[key] for key in ("schema_version","original_columns","force_columns","categories","units","force_scope","qualification")):
        raise ValueError("Closed M-LEDGER1 reference metadata differs")
    for old in previous["states"]:
        if ledger["states"][old["identity"]["index"]] != old:
            raise ValueError("Shared saved identity/rows/derived loads differ from closed M-LEDGER1")
    pairs = paired_rows(ledger)
    ledger["processing_scope"] = "All24 saved-table states,16872 original node rows,168 category rows; preserved module qualification is not a new full24 mechanics qualification"
    ledger["shared_MLEDGER1_comparison"] = dict(indices=[0,8,13,23],all_saved_states_exactly_equal=True,second_classification_calls=0)
    ledger["paired_branch_scope"] = "Ten exact-stroke pairs including origin baseline;70 category rows; signed unloading-minus-baseline differences, no interpolation"
    with (output/"all_nodes.csv").open("w",newline="",encoding="utf-8") as stream:
        writer = csv.DictWriter(stream,fieldnames=ledger["original_columns"]+["ledger_category"])
        writer.writeheader()
        for state in ledger["states"]:
            writer.writerows(state["nodes"])
    with (output/"category_loads.csv").open("w",newline="",encoding="utf-8") as stream:
        writer = csv.DictWriter(stream,fieldnames=list(ledger["states"][0]["identity"])+["category","node_count"]+ledger["force_columns"])
        writer.writeheader()
        for state in ledger["states"]:
            for name,group in state["categories"].items():
                writer.writerow(dict(state["identity"],category=name,node_count=group["node_count"],**force_cells(group["force_on_body_N"])))
    with (output/"paired_branch_differences.csv").open("w",newline="",encoding="utf-8") as stream:
        writer = csv.DictWriter(stream,fieldnames=list(pairs[0]))
        writer.writeheader()
        writer.writerows(pairs)
    write_json(output/"ledger.json",ledger)
    render(ledger,pairs)
    output_hashes = {path.name:sha(path) for path in output.iterdir()}
    for name,pin in protocol["bindings"].items():
        if sha(repo/name) != pin:
            raise ValueError("Original input/source changed: "+name)
    checkpoint()
    return dict(status="pass",calls=calls,selected_states=list(range(24)),shared_MLEDGER1_exact=True,paired_strokes=10,paired_category_rows=len(pairs),
        protocol_sha256=sha(protocol_file),all_bindings_unchanged=True,elapsed_seconds=perf_counter()-STARTED,sampled_peak_RSS_bytes=peak,output_SHA256=output_hashes,
        source_scope="All24 saved-table ledger, signed exact-stroke differences and2Matplotlib diagnostics only; no NPZ/F/T/HP/model construction/equilibrium/new observer/pressure or new mechanics qualification",mechanical_hooks_monitored=False)

def main():
    output.mkdir(parents=True,exist_ok=False)
    try:
        receipt = run()
    except BaseException as error:
        write_json(output/"execution_receipt.json",dict(status="not_pass",error=repr(error),calls=calls,elapsed_seconds=perf_counter()-STARTED,sampled_peak_RSS_bytes=peak))
        raise
    write_json(output/"execution_receipt.json",receipt)
    print(json.dumps(dict(status="pass",calls=calls)),flush=True)

if __name__ == "__main__":
    main()
