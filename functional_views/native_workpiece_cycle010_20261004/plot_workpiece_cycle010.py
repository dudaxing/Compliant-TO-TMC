"""Read a complete saved cycle010 and its hash-bound fresh mechanical reference.

Raw production qualification flags remain false; this view records the external
force/Jv/equilibrium/body-projection evidence, without pressure or energy claims.

Install within the repository before use. No force, tangent, solve, HP, action
consumer or boundary measurement is evaluated. The old helper is used only
for pure numeric-row formatting, never its 17-field cycle loader or render.
"""
from time import perf_counter
STARTED = perf_counter()
import argparse
import csv
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
from textwrap import fill
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D
from matplotlib.ticker import ScalarFormatter
import numpy as np
import psutil

ROOT = next(p for p in Path(__file__).resolve().parents if (p/"hf_repo").is_dir())
HELPER = ROOT/"functional_views/native_workpiece_cycle_20261004/plot_workpiece_cycle.py"
HELPER_SHA = "d256fe2b1541505cd5315f45c4a50462670a09436ceb91ecc8d01bbb25554169"
PEAK = 0
TARGETS = [0., .5, 1., 1.5, 1.75, 1.8, 1.75, 1.5, 1., .5, 0.]
TANGENT_EXECUTION = dict(mode="chunk256", element_block_size=256, global_selector_scope="full_batch")
sha = lambda p: sha256(p.read_bytes()).hexdigest()


def main():
    global PEAK
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("stage", "output", "protocol", "reference"): parser.add_argument("--"+name, required=True, type=Path)
    parser.add_argument("--measurements", type=Path, help="Optional saved unsigned Q1 boundary measurements; never recomputed")
    args = parser.parse_args(); stage, output = args.stage.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    report = dict(status="running", scientific_reference_qualified=False,
        new_calls=dict(force=0, tangent=0, solver=0, HP=0, action_consumer=0, geometry_measurement=0))
    pins = {}
    def bind(path, expected=None):
        actual = sha(path); assert expected is None or actual == expected, "Saved file SHA differs: "+path.name
        pins[path.resolve()] = actual; return actual
    def checkpoint():
        global PEAK
        info = psutil.Process().memory_info(); PEAK = max(PEAK, info.rss, getattr(info, "peak_wset", info.rss))
        if perf_counter()-STARTED > 120 or PEAK > 8*1024**3 or any((p/"stop_requested.txt").exists() for p in (stage, output.parent)):
            raise RuntimeError("Saved cycle010 view resource window closed; no retry")
    try:
        protocol_file = args.protocol.resolve(); bind(protocol_file)
        protocol = json.loads(protocol_file.read_text(encoding="utf-8"))
        for name, pin in protocol["bindings"].items(): bind(ROOT/name, pin)
        assert pins[Path(__file__).resolve()] == sha(Path(__file__)) and bind(HELPER, HELPER_SHA) == HELPER_SHA
        spec = importlib.util.spec_from_file_location("cycle010_numeric_rows", HELPER)
        helper = importlib.util.module_from_spec(spec); spec.loader.exec_module(helper)
        def read(path, expected=None, descriptor=False):
            bind(path, expected); value = json.loads(path.read_text(encoding="utf-8"))
            if descriptor: assert helper.semantic_hash({k:v for k,v in value.items() if k != "descriptor_sha256"}) == value["descriptor_sha256"]
            return value
        def archive(path, declaration, matrix=False):
            bind(path, declaration["sha256"])
            with np.load(path, allow_pickle=False) as data: arrays = {k:data[k].copy() for k in data.files}
            assert matrix or set(arrays) == set(declaration["fields"])
            for name, item in declaration["fields"].items():
                a = arrays[name]; assert dict(dtype=a.dtype.name, shape=list(a.shape), sha256=sha256(a.tobytes()).hexdigest()) == item
            if matrix: assert set(arrays) == {"data","indices","indptr","shape","format"} and arrays["format"].item() == b"csc" and arrays["shape"].tolist() == declaration["shape"] and len(arrays["data"]) == declaration["nnz"]
            return arrays
        receipt = read(stage/"execution_receipt.json")
        inventory = read(stage/"input_inventory.json", receipt["input_inventory_sha256"])
        assert stage.name == "coarse_square_cycle_010" and inventory["case"]["alias"] == "gripper_coarse_square"
        freeze = read(stage/"source_freeze.json", inventory["source_freeze_sha256"])
        assert receipt["sources"] == freeze["sources"] and receipt["inputs"] == inventory["input_bindings"]
        for name, pin in freeze["sources"].items(): bind(stage/"sources"/Path(name).name, pin)
        for name, pin in inventory["input_bindings"].items(): bind(ROOT/name, pin)
        directory = stage/inventory["case"]["result_directory"]
        result = read(directory/"result.json", receipt["result_sha256"], True)
        availability = dict(response_mode="mechanical", response_contract="split-numpy-mechanical-1.0",
            force_kernel_version="p26_q1_split_mechanical_numpy_aux_omitted_candidate1", auxiliary_material_energy=dict(status="not_evaluated", qualified=False, field_present=False))
        assert result["schema_version"] == "hf-native-mean-result-1.2" and result["status"] == "success" and result["path_kind"] == "ordered_cycle"
        assert receipt["status"] == "pass" and result["failure"] is None
        assert all(result[k] is True for k in ("production_converged","target_reached","task_target_executed","path_completed","loading_peak_reached","unload_endpoint_reached"))
        assert result["tangent_execution"] == TANGENT_EXECUTION
        assert all(result[k] == v and receipt[k] == v for k,v in availability.items())
        assert result["independent_HP_qualified"] is result["equilibrium_qualified"] is result["HF_qualified"] is False
        model_file = directory/result["model"]["descriptor_path"]
        metadata = read(model_file, result["model"]["descriptor_file_sha256"], True)
        model = archive(model_file.parent/metadata["arrays"]["path"], metadata["arrays"])
        assert metadata["schema_version"] == "hf-native-project-model-1.1" and len(model) == 27
        assert metadata["descriptor_sha256"] == result["model"]["descriptor_sha256"] and metadata["arrays"]["sha256"] == result["model"]["arrays_sha256"] == receipt["model_sha256"]
        task = metadata["task"]; targets = task["path"]["targets_mm"]
        assert targets == result["targets_mm"] == inventory["case"]["targets_mm"] == TARGETS and helper.semantic_hash(task) == metadata["task_sha256"] == result["task_sha256"] == receipt["task_sha256"]
        assert task["case_family"] == "gripper" and task["workpiece"]["kind"] == "fixed_rigid" and task["workpiece"]["shape"] == "square"
        source = metadata["source_geometry"]; geometry_file = model_file.parent/source["snapshot"]["descriptor"]
        geometry = read(geometry_file, source["descriptor_file_sha256"], True)
        masks = archive(geometry_file.parent/geometry["arrays"]["path"], geometry["arrays"])
        assert geometry["geometry_id"] == task["geometry"]["geometry_id"] == source["geometry_id"] and geometry["descriptor_sha256"] == task["geometry"]["descriptor_sha256"] == source["descriptor_sha256"] and geometry["arrays"]["sha256"] == source["arrays_sha256"]
        assert np.array_equal(model["solid"], masks["solid"].ravel().astype(bool)) and metadata["region_metadata"]["ports"]["output"]["direction"] == [0.,1.]
        body = metadata["region_metadata"]["workpiece"]; assert result["workpiece"] == body and body["definition"] == task["workpiece"]
        for key in ("cells","nodes","dofs","background_symmetry_overlap_dofs"): assert np.array_equal(model["workpiece_"+key], body[key])
        assert not np.any(model["solid"][model["workpiece_cells"]]) and np.all(np.isin(model["workpiece_dofs"],model["fixed_dofs"]))
        states = []; previous = -1
        for row in result["states"]:
            stored = read(directory/row["descriptor_path"], row["descriptor_file_sha256"], True)
            assert stored == {k:v for k,v in row.items() if k not in ("descriptor_path","descriptor_file_sha256")}
            assert all(row[k] == v for k,v in availability.items()) and row["tangent_execution"] == TANGENT_EXECUTION
            state = archive(directory/row["state"]["path"], row["state"]); forces = archive(directory/row["forces"]["path"], row["forces"])
            tensors = archive(directory/row["tangents"]["path"], row["tangents"]); archive(directory/row["matrix"]["path"], row["matrix"], True)
            identity = sha256(b"split_displacement_v1"+np.asarray(len(model["b_in"]),dtype="<i8").tobytes()+state["lift"].astype("<f8",copy=False).tobytes()+state["fluctuation"].astype("<f8",copy=False).tobytes()).hexdigest()
            index = row["original_target_index"]; leg = "origin" if index == 0 else "loading" if targets[index] > targets[index-1] else "unloading"
            assert identity == row["state_sha256"] == row["assembler_state_sha256"] and set(state) == {"lift","fluctuation"}
            assert len(forces) == 16 and "material_energy" not in forces and len(tensors) == 3 and not np.any(state["lift"]) and not np.any(state["fluctuation"][model["fixed_dofs"]]) and np.all(forces["J"] > 0.)
            assert index >= previous and row["leg"] == leg and row["original_target_displacement"] == targets[index] and row["is_original_target"] == (row["d"] == targets[index])
            assert row["matrix"]["shape"] == [len(model["b_in"])]*2 and row["matrix"]["units"] == "N/mm" and row["matrix"]["symmetrized"] is False
            states.append(dict(record=row,state=state,forces=forces)); previous = index
        assert len(states) == result["accepted_states"] == receipt["accepted_states"] and states and states[0]["record"]["d"] == 0.
        assert len(states) >= len(TARGETS) and states[-1]["record"]["original_target_index"] == len(targets)-1 and states[-1]["record"]["d"] == targets[-1] == 0.
        originals = [s["record"] for s in states if s["record"]["is_original_target"]]
        assert [s["original_target_index"] for s in originals] == list(range(len(TARGETS))) and [s["d"] for s in originals] == TARGETS
        reference_file = args.reference.resolve()
        reference_pin = protocol["bindings"][reference_file.relative_to(ROOT).as_posix()]
        reference = read(reference_file, reference_pin)
        assert reference["schema_version"] == "native-workpiece-cycle-independent-audit-1.0" and reference["status"] == "pass"
        assert reference["alias"] == "gripper_coarse_square" and reference["source_alias"] == "gripper_canonical" and reference["case_family"] == "gripper"
        assert reference["result_sha256"] == receipt["result_sha256"] and reference["audited_targets_mm"] == TARGETS and reference["path_kind"] == "ordered_cycle" and reference["workpiece"] == task["workpiece"]
        assert reference["source_bindings"] == freeze["sources"] and reference["gates"] == inventory["gates"] and reference["tangent_execution"] == TANGENT_EXECUTION
        assert reference["accepted_states"] == len(reference["states"]) == len(states) and reference["HP_calls_started"] == reference["HP_calls_completed"] == 2*len(states)
        assert reference["full_element_and_DOF_coverage"] is True and reference["HP_matrix_columns_exhaustively_checked"] is False
        assert all(reference[k] is False for k in ("contact_qualified","clamp_qualified","pressure_qualified")) and all(reference[k] == v for k,v in availability.items())
        for index,(checked,saved) in enumerate(zip(reference["states"],states)):
            assert checked["status"] == "pass" and checked["index"] == index and checked["HP_calls"] == 2
            assert checked["state_sha256"] == saved["record"]["state_sha256"] and checked["target_mm"] == saved["record"]["d"] and all(checked[k] == saved["record"][k] for k in ("leg","original_target_index"))
            assert checked["elements_compared"] == len(model["connectivity"]) and checked["global_DOFs_compared"] == len(model["b_in"])
        report.update(scientific_reference_qualified=True, reference_summary_sha256=reference_pin,
            external_reference_scope=reference["qualification"], fresh_HP_calls=reference["HP_calls_completed"],
            raw_production_qualification={k:result[k] for k in ("independent_HP_qualified","equilibrium_qualified","HF_qualified")})
        progress_file = stage/"accepted_progress.jsonl"; bind(progress_file)
        progress = [json.loads(line) for line in progress_file.read_text(encoding="utf-8").splitlines()]
        assert len(progress) == len(states)
        for i,(item,saved) in enumerate(zip(progress,states)):
            assert item["index"] == i and all(item[k] == saved["record"][k] for k in ("d","R_input","q_in","q_out","relative_residual","state_sha256","leg","original_target_index"))
            assert item["workpiece"] == saved["record"]["workpiece"]["force_on_lower_body_N"] and all(item[k] == v for k,v in availability.items())
        rows, inlet = helper.numerical_rows(model,states); boundary = None
        if args.measurements:
            measurement = read(args.measurements.resolve())
            assert measurement["schema_version"] == "native-workpiece-boundary-path-1.0" and measurement["production_status"] == result["status"] and measurement["task_sha256"] == result["task_sha256"] and measurement["input_files_unchanged"] is True
            assert all(measurement[k] == 0 for k in ("force_calls","tangent_calls","solver_calls","HP_calls"))
            mapped = set()
            for name,pin in measurement["input_files_sha256"].items():
                normal = name.replace("\\", "/")
                path = stage/"sources"/Path(normal.split("/hf_repo/",1)[1]).name if "/hf_repo/" in normal else directory/normal.rsplit("/result/",1)[1]
                bind(path,pin); mapped.add(path.resolve())
            expected = {directory/"result.json",model_file,model_file.parent/metadata["arrays"]["path"],*(directory/saved["record"]["state"]["path"] for saved in states),*(stage/"sources"/name for name in ("boundary_geometry.py","measure_native_workpiece_boundaries.py"))}
            assert mapped == {path.resolve() for path in expected}
            boundary = measurement["accepted_states"]; assert len(boundary) == len(states)
            for index,(item,saved,row) in enumerate(zip(boundary,states,rows)):
                assert item["accepted_index"] == index and all(item[k] == saved["record"][k] for k in ("state_sha256","leg","original_target_index")) and item["d_mm"] == row["d_mm"]
                geometry = item["geometry"]
                assert geometry["containment_tested"] is geometry["contact_pressure_qualification"] is geometry["contact_or_clamping_qualification"] is False and geometry["symmetry_cut_excluded"] == dict(axis="y",reference_offset_mm=40.,applies_to="both boundaries")
                for name,group in geometry["groups"].items():
                    row["boundary_"+name+"_distance_mm"] = group["minimum_boundary_distance_mm"]
                    row["boundary_"+name+"_intersects"] = group["intersects"]; row["boundary_"+name+"_near_touch"] = group["roundoff_near_touch"]
        checkpoint()
        coords,conn,solid = (model[k] for k in ("coordinates","connectivity","solid"))
        body_cells = model["workpiece_cells"]; medium = ~solid.copy(); medium[body_cells] = False
        u = [(s["state"]["lift"]+s["state"]["fluctuation"]).reshape(-1,2) for s in states]
        colors = [np.linalg.norm(v,axis=1)[conn].mean(axis=1) for v in u]; norm = Normalize(0.,max(max(float(v.max()) for v in colors),1e-30))
        support = np.asarray(metadata["region_metadata"]["support"]["attached_nodes"],dtype=int)
        out_nodes = np.asarray(metadata["region_metadata"]["ports"]["output"]["nodes"],dtype=int)
        max_force = max(float(np.linalg.norm(s["forces"][k].reshape(-1,2),axis=1).max()) for s in states for k in ("input_force","support_reaction"))
        max_body = max(float(np.linalg.norm(s["record"]["workpiece"]["force_on_lower_body_N"]["total"])) for s in states)
        arrow_N = max(max_force,max_body,1e-30); force_scale = arrow_N/4.
        peak = max(range(len(rows)),key=lambda i:rows[i]["d_mm"])
        last = len(rows)-1; path_label = "COMPLETE / RETURN ZERO REACHED"
        fig = plt.figure(figsize=(22,21),layout="constrained"); grid = fig.add_gridspec(5,3,height_ratios=[1.,.13,.55,.55,.75])
        def structure(ax,index,scale):
            moved = coords+scale*u[index]
            ax.add_collection(PolyCollection(moved[conn[medium]],array=colors[index][medium],cmap="Oranges",norm=norm,edgecolors="none"))
            field = PolyCollection(moved[conn[solid]],array=colors[index][solid],cmap="viridis",norm=norm,edgecolors="none"); ax.add_collection(field)
            ax.add_collection(PolyCollection(coords[conn[solid]],facecolors="none",edgecolors="#999999",linewidths=.15))
            ax.add_collection(PolyCollection(coords[conn[body_cells]],facecolors="#cccccc",edgecolors="#555555",linewidths=.2))
            for nodes,marker,c in ((support,"^","#183a53"),(inlet//2,"o","#b84b23"),(out_nodes,"D","#8856a7")):
                ax.scatter(*moved[nodes].T,marker=marker,s=32,facecolors="none",edgecolors=c,zorder=5)
            if scale == 1:
                for key,nodes,c in (("input_force",inlet//2,"#b84b23"),("support_reaction",support,"#216a9b")):
                    values = states[index]["forces"][key].reshape(-1,2)[nodes]
                    ax.quiver(*moved[nodes].T,*values.T,angles="xy",scale_units="xy",scale=force_scale,color=c,width=.004,minlength=0.,zorder=6)
                centre = coords[model["workpiece_nodes"]].mean(axis=0)
                ax.quiver(*centre,*states[index]["record"]["workpiece"]["force_on_lower_body_N"]["total"],angles="xy",scale_units="xy",scale=force_scale,color="#7b3294",width=.006,minlength=0.,zorder=6)
            if scale == 1 and boundary and index == peak:
                for name,c,offset in (("bottom","#009ca6",(6,-22)),("left","#cf4ca0",(6,14))):
                    group = boundary[index]["geometry"]["groups"][name]; pair = group["closest_pair"]
                    points = np.asarray([pair["mechanism_point_mm"],pair["workpiece_point_mm"]])
                    ax.plot(*points.T,"x--",color=c,lw=1.3,ms=5,zorder=8)
                    ax.annotate(f"{name} unsigned: {group['minimum_boundary_distance_mm']:.5g} mm",points.mean(axis=0),xytext=offset,textcoords="offset points",fontsize=8.5,bbox=dict(facecolor="white",alpha=.9,edgecolor="none"),zorder=9)
            ax.set(xlim=(-4,84) if scale == 1 else (54,84),ylim=(-4,44) if scale == 1 else (22,44),aspect="equal",xlabel="x [mm]",ylabel="y [mm]",title=f"Accepted {index}: {rows[index]['leg']}, d={rows[index]['d_mm']:g} mm\n"+("ACTUAL x1; reference outline grey" if scale == 1 else "DISPLAY ONLY x4 displacement; no force arrows"))
            return field
        panels = [fig.add_subplot(grid[0,i]) for i in range(3)]
        field = structure(panels[0],peak,1); structure(panels[1],last,1); structure(panels[2],peak,4)
        panels[1].set_title(panels[1].get_title()+"\nLAST ACCEPTED RETURN ZERO")
        for artist,label in ((field,"Mechanism mean nodal |u| [mm]"),(plt.cm.ScalarMappable(norm=norm,cmap="Oranges"),"Third-medium mean nodal |u| [mm]")):
            bar = fig.colorbar(artist,ax=panels,fraction=.013,pad=.01); bar.set_label(label)
            bar.formatter = ScalarFormatter(useOffset=False); bar.update_ticks()
        legend = fig.add_subplot(grid[1,:]); legend.axis("off")
        handles = [Line2D([],[],marker=m,color=c,linestyle="none",label=l) for m,c,l in [("^","#183a53","attached support / reaction ON model"),("o","#b84b23","free mean-input nodes / actuator ON model"),("D","#8856a7","free +y output measurement (not a force)"),("s","#777777","fixed square / purple force ON lower body")]]
        if boundary: handles += [Line2D([],[],marker="x",color=c,ls="--",label=l) for c,l in (("#009ca6","saved bottom closest pair (not force)"),("#cf4ca0","saved left-boundary pair; corner may be closest"))]
        legend.legend(handles=handles,loc="center",ncol=2,fontsize=10.5)
        def curve(ax,key,title,unit):
            ax.plot(range(len(rows)),[r[key] for r in rows],"o-"); ax.set(title=title,xlabel="Actual accepted index (chronological)",ylabel=unit); ax.grid(alpha=.2)
        for i,(key,title,unit) in enumerate((("R_input_N","Actuator R input","N"),("q_out_mm","Free +y output mean (physical uy)","mm"))): curve(fig.add_subplot(grid[2,i]),key,title,unit)
        j_ax = fig.add_subplot(grid[2,2]); curve(j_ax,"minimum_J","Saved minimum J and max |Hu component|","J [dimensionless]")
        hu_ax = j_ax.twinx(); hu_ax.plot(range(len(rows)),[r["maximum_Hu_per_mm"] for r in rows],"s--",color="#b45b19",label="max |Hu|")
        hu_ax.set_ylabel("Maximum |Hu component| [1/mm]",color="#b45b19"); hu_ax.tick_params(axis="y",colors="#b45b19")
        for i,axis in enumerate("xy"):
            ax = fig.add_subplot(grid[3,i])
            for name,c in (("total","#222222"),("material","#2475aa"),("regularization","#b45b19")): ax.plot(range(len(rows)),[r[f"lower_body_{name}_F{axis}_N"] for r in rows],"o-",label=name,color=c)
            ax.set(title="Force ON lower body: F"+axis,xlabel="Actual accepted index (chronological)",ylabel="N"); ax.legend(); ax.grid(alpha=.2)
        ax = fig.add_subplot(grid[3,2])
        if boundary:
            for name in ("all_exposed","bottom","left"): ax.plot(range(len(rows)),[r["boundary_"+name+"_distance_mm"] for r in rows],"o-",label=name+" boundary")
            ax.set(title="SAVED unsigned Q1 exterior distances\nLeft may be a corner; not signed/contact",ylabel="mm"); ax.legend(fontsize=9)
        else:
            ax.plot(range(len(rows)),[r["two_sided_normal_magnitude_sum_N"] for r in rows],"o-",color="#7b3294")
            ax.set(title="Mirrored scalar sum: 2|Fy|\nNot net force or a clamp conclusion",ylabel="N")
        ax.set_xlabel("Actual accepted index"); ax.grid(alpha=.2)
        history = result["path_diagnostics"]["newton_history"]; trials = result["path_diagnostics"]["trials"]
        base_ax,trial_ax,text_ax = [fig.add_subplot(grid[4,i]) for i in range(3)]
        starts = [i for i,r in enumerate(history) if r["newton_check"] == 1]+[len(history)]
        for a,b in zip(starts,starts[1:]): base_ax.semilogy(range(a+1,b+1),[r["relative_residual"] or np.nan for r in history[a:b]],"o-",label=f"attempt d={history[a]['d']:g}")
        base_ax.axhline(result["settings"]["tolerance"],color="red",ls="--",label="Original residual gate")
        base_ax.set(title="Completed Newton BASE chronology\nNot accepted-state observations; exact zeros omitted",xlabel="Saved completed base index",ylabel="Relative residual"); base_ax.legend(fontsize=8); base_ax.grid(alpha=.2)
        for accepted,marker,c in ((True,"o","#00875f"),(False,"x","#c62828")):
            selected = [(i+1,t) for i,t in enumerate(trials) if t["accepted"] == accepted]
            trial_ax.scatter([i for i,t in selected],[t["factor"] for i,t in selected],marker=marker,color=c,label=("accepted trials" if accepted else "rejected trials")+f": {len(selected)}")
        trial_ax.set(yscale="log",title="Actual line-search factors\nTrial acceptance is not path-state acceptance",xlabel="Saved trial index",ylabel="Dimensionless factor"); trial_ax.legend(fontsize=9); trial_ax.grid(alpha=.2)
        counts = result["call_counts"]; text_ax.axis("off")
        lines = ["COMPLETE PATH / FRESH MECHANICAL HP PASS",f"External fresh HP80/120 calls={reference['HP_calls_completed']}; 2 per actual state", "All elements/DOFs; force, PORT Jv, equilibrium and body projection.", "PORT is one direction, not all matrix columns.", "Raw production HP/equilibrium/HF flags remain false.",f"Status={result['status']}; failure={result['failure']}",f"Requested targets={targets} mm",f"Actual accepted count={len(rows)}; no deduplication",f"Path={path_label}; formal phase={receipt['status']}",f"Unload endpoint={result['unload_endpoint_reached']}","Energy NOT EVALUATED; 16 force fields; schema1.2",f"F started/completed={counts['force_calls']}/{counts['force_calls_completed']}",f"T started/completed={counts['tangent_calls']}/{counts['tangent_calls_completed']}",f"COMMON arrows: {arrow_N:.8g} N = 4 display mm",f"Peak: #{peak}, d={rows[peak]['d_mm']:g} mm; minJ={rows[peak]['minimum_J']:.8g}",f"Last: #{last}, {rows[last]['leg']}, d={rows[last]['d_mm']:g} mm", "Every accepted index is retained in curves and CSV.","ON body = negative model holding reaction.","Mirrored upper: (Fx,-Fy); net: (2Fx,0).","2|Fy| is a scalar sum, not full net force.","Unsigned boundary distance is not signed penetration.","Left boundary may be nearest at a corner.","Node-window proxies remain separate CSV quantities.",f"Peak/return max |Hu|={rows[peak]['maximum_Hu_per_mm']:.8g}/{rows[last]['maximum_Hu_per_mm']:.8g} 1/mm", "No pressure/contact/clamp/energy/stress-HP qualification."]
        text_ax.text(0,1,"\n".join(fill(line,width=54) for line in lines),va="top",fontsize=9.3,linespacing=1.35)
        fig.suptitle("Cycle010 mechanical saved path: "+path_label+" / EXTERNAL FRESH MECHANICAL HP PASS\nActual x1 peak/return; all accepted states retained; no contact/clamp/energy qualification",fontsize=16,color="#176b4a")
        checkpoint(); fig.savefig(output/"cycle010_saved_path.png",dpi=150); plt.close(fig)
        with (output/"accepted_numeric_states.csv").open("x",encoding="utf-8",newline="") as stream:
            writer = csv.DictWriter(stream,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
        (output/"plot_cycle010_saved_frozen.py").write_bytes(Path(__file__).read_bytes())
        checkpoint(); assert all(sha(p) == pin for p,pin in pins.items()), "Saved input changed during view"
        report.update(status="rendered_saved_complete_reference_path",production_status=result["status"],production_phase_status=receipt["status"],failure=result["failure"],accepted_states=len(rows),accepted_d_mm=[r["d_mm"] for r in rows],requested_targets_mm=targets,call_counts=counts,actual_peak_index=peak,last_accepted_index=last,path_display_status=path_label,
            response_contract=availability,full_path_completed=result["path_completed"],initial_and_return_zero_kept_by_index=True,return_zero_present=bool(len(rows)>1 and rows[-1]["d_mm"] == targets[-1] and rows[-1]["original_target_index"] == len(targets)-1),
            display=dict(actual_geometry_scale=1,supplementary_displacement_scale=4,supplementary_force_arrows=False,force_scale_N_per_display_mm=force_scale,displacement_color_range_mm=[norm.vmin,norm.vmax],displacement_colormaps=dict(solid="viridis",third_medium="Oranges"),arrows_shown="input nodes, attached support nodes, lower-body resultant; other fixed groups in CSV",interpolated_states=0,animation_frames=0,source_node_windows_not_boundary_distance=True),
            units=dict(length="mm",force="N",tangent="N/mm",J="dimensionless",Hu="1/mm"),input_files_sha256={(("stage/"+p.relative_to(stage).as_posix()) if p.is_relative_to(stage) else ("repo/"+p.relative_to(ROOT).as_posix())):pin for p,pin in pins.items()},inputs_unchanged=True,source_sha256=sha(Path(__file__)),helper_sha256=HELPER_SHA,protocol_sha256=pins[protocol_file],
            boundary_measurements_loaded=boundary is not None,boundary_scope="Saved unsigned Q1 exterior distances/closest points only; no new geometry, signed penetration or containment test; node-window proxies separate in CSV",reference_scope="Hash-bound same-stage fresh HP80/120 summary: all accepted states/elements/DOFs, original force, PORT Jv, equilibrium and body-projection gates; no new reference evaluation, energy/stress-HP/contact/clamp/pressure/all-column qualification.")
    except Exception as error:
        report.update(status="failed_saved_view",error=repr(error)); raise
    finally:
        report.update(elapsed_seconds=perf_counter()-STARTED,peak_sampled_RSS_bytes=PEAK,outputs_sha256={p.name:sha(p) for p in output.iterdir() if p.is_file()})
        (output/"view_metadata.json").write_text(json.dumps(report,indent=2,allow_nan=False)+"\n",encoding="utf-8")


if __name__ == "__main__":
    main()
