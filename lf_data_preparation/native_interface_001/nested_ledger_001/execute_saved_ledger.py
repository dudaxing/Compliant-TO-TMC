"""Frozen M-LEDGER1 source; separate card execution authorization required; not executed."""
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

def checkpoint():
    global peak
    peak = max(peak,process.memory_info().rss)
    if perf_counter()-STARTED > args.time_limit or peak > protocol["sampled_RSS_bytes"] or (protocol_file.parent/"stop_requested.txt").exists():
        raise RuntimeError("M-LEDGER1 cooperative resource/stop boundary reached")

def write_json(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")

def render(ledger):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    names,parts = ledger["categories"],("total","material","regularization")
    colors = dict(zip(names,plt.get_cmap("tab10").colors))
    peak_state = next(state for state in ledger["states"] if state["identity"]["index"] == 13)
    fig,ax = plt.subplots(figsize=(9,6))
    for name in names:
        nodes = [row for row in peak_state["nodes"] if row["ledger_category"] == name]
        ax.scatter([float(row["x_mm"]) for row in nodes],[float(row["y_mm"]) for row in nodes],
            s=18,c=[colors[name]],label=name+" ("+str(len(nodes))+")")
    ax.plot([62,62,80,80],[40,31,31,40],color="black",linewidth=.8)
    ax.plot([62,80],[40,40],"k--",linewidth=.8)
    ax.set(aspect="equal",xlabel="Reference x (mm)",ylabel="Reference y (mm)",title="Fixed-body node categories; no corner allocation")
    ax.legend(fontsize=8,loc="upper left",bbox_to_anchor=(1,1))
    fig.tight_layout()
    fig.savefig(output/"positions.png",dpi=150)
    plt.close(fig)
    calls["PNG_writes"] += 1
    checkpoint()
    fig,axes = plt.subplots(2,1,figsize=(11,7),sharex=True)
    for axis,ax in enumerate(axes):
        for offset,part in enumerate(parts):
            values = [peak_state["categories"][name]["force_on_body_N"][part][axis] for name in names]
            ax.bar([index+(offset-1)*.24 for index in range(len(names))],values,width=.24,label="Hu" if part == "regularization" else part)
        ax.axhline(0,color="black",linewidth=.5)
        ax.set_ylabel("Signed F"+"xy"[axis]+" (N)")
        ax.legend()
    labels = ("bottom","left","right","physical corner","physical/cut","cut interior","body interior")
    axes[-1].set_xticks(range(len(names)),labels,rotation=20,ha="right",fontsize=8)
    fig.suptitle("Saved loading1.2 mm category weak loads: total / material / Hu")
    fig.tight_layout()
    fig.savefig(output/"component_bars.png",dpi=150)
    plt.close(fig)
    calls["PNG_writes"] += 1
    checkpoint()
    fig,axes = plt.subplots(2,3,figsize=(13,7),sharex=True)
    labels = [str(state["identity"]["index"])+":"+state["identity"]["leg"]+" "+str(state["identity"]["d_mm"]) for state in ledger["states"]]
    for axis in (0,1):
        for column,part in enumerate(parts):
            ax = axes[axis,column]
            for name in names:
                values = [state["categories"][name]["force_on_body_N"][part][axis] for state in ledger["states"]]
                ax.plot(range(len(labels)),values,"o-",color=colors[name],label=name)
            ax.axhline(0,color="black",linewidth=.5)
            ax.set(title=part+" F"+"xy"[axis]+" (N)")
            ax.set_xticks(range(len(labels)),labels,rotation=20,ha="right",fontsize=7)
    axes[0,0].legend(fontsize=7)
    fig.suptitle("Four cached states only; connecting lines are guides, not the full cycle")
    fig.tight_layout()
    fig.savefig(output/"selected_state_categories.png",dpi=150)
    plt.close(fig)
    calls["PNG_writes"] += 1
    checkpoint()

def run():
    if protocol["schema_version"] != "saved-fixed-square-ledger-card-1.0" or args.time_limit != 180. or tuple(protocol["selected_state_indices"]) != (0,8,13,23):
        raise ValueError("This first ledger card requires180s and exactly0/8/13/23")
    checkpoint()
    for name,pin in protocol["bindings"].items():
        if sha(repo/name) != pin:
            raise ValueError("Bound input/source changed: "+name)
    linked = read(repo/protocol["linked_response_file"])
    view = read(repo/protocol["view_summary_file"])
    result = read(repo/linked["identity"]["result"]["path"])
    model = read(repo/linked["identity"]["model"]["path"])
    body_metadata = dict(linked["physics"],canonical_body_node_ids=model["region_metadata"]["workpiece"]["nodes"])
    if len(view["rows"]) != result["accepted_states"] or result["accepted_states"] != 24:
        raise ValueError("Require the closed24-state view/result identity source")
    for index,row in enumerate(view["rows"]):
        state = result["states"][index]
        if (row["index"],row["original_target_index"],row["leg"],row["d_mm"],row["state_sha256"]) != (
            index,state["original_target_index"],state["leg"],state["d"],state["state_sha256"]):
            raise ValueError("Original view/result state identity differs")
    records = {index:dict(identity=view["rows"][index],nodal=read(repo/protocol["nodal_files"][str(index)])) for index in (0,8,13,23)}
    sys.path.insert(0,str(repo/"hf_repo/src"))
    from hf_eval.saved_workpiece_loads import summarize_saved_workpiece_node_ledger
    calls["ledger_started"] += 1
    ledger = summarize_saved_workpiece_node_ledger(repo/protocol["nodes_csv_file"],body_metadata,recorded_states=records,selected_states=(0,8,13,23))
    calls["ledger_completed"] += 1
    checkpoint()
    with (output/"selected_nodes.csv").open("w",newline="",encoding="utf-8") as stream:
        writer = csv.DictWriter(stream,fieldnames=ledger["original_columns"]+["ledger_category"])
        writer.writeheader()
        for state in ledger["states"]:
            writer.writerows(state["nodes"])
    with (output/"category_loads.csv").open("w",newline="",encoding="utf-8") as stream:
        columns = list(ledger["states"][0]["identity"])+["category","node_count"]+ledger["force_columns"]
        writer = csv.DictWriter(stream,fieldnames=columns)
        writer.writeheader()
        for state in ledger["states"]:
            for name,group in state["categories"].items():
                forces = {part+"_F"+axis+"_N":group["force_on_body_N"][part][index] for part in ("total","material","regularization") for index,axis in enumerate("xy")}
                writer.writerow(dict(state["identity"],category=name,node_count=group["node_count"],**forces))
    write_json(output/"ledger.json",ledger)
    render(ledger)
    for name,pin in protocol["bindings"].items():
        if sha(repo/name) != pin:
            raise ValueError("Original input/source changed: "+name)
    checkpoint()
    return dict(status="pass",calls=calls,selected_states=[0,8,13,23],protocol_sha256=sha(protocol_file),all_bindings_unchanged=True,
        elapsed_seconds=perf_counter()-STARTED,sampled_peak_RSS_bytes=peak,output_SHA256={path.name:sha(path) for path in output.iterdir()},
        source_scope="New selected-table ledger and3Matplotlib diagnostics only; no NPZ/F/T/HP/model/solve/new observer/pressure/full24 qualification",mechanical_hooks_monitored=False)

def main():
    output.mkdir(parents=True,exist_ok=False)
    try:
        receipt = run()
    except BaseException as error:
        write_json(output/"execution_receipt.json",dict(status="not_pass",error=repr(error),calls=calls,
            elapsed_seconds=perf_counter()-STARTED,sampled_peak_RSS_bytes=peak))
        raise
    write_json(output/"execution_receipt.json",receipt)
    print(json.dumps(dict(status="pass",calls=calls)),flush=True)

if __name__ == "__main__":
    main()
