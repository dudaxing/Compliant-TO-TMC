"""Actual saved square paths: geometry/nodal observations and plots, no mechanics."""
from time import perf_counter
STARTED = perf_counter()
from pathlib import Path
from hashlib import sha256
import argparse, csv, json, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from PIL import Image

PARTS = ("total", "material", "regularization")
GROUPS = ("physical_only", "cut_only", "physical_and_cut", "interior")

def plain(x):
    if isinstance(x, dict): return {k:plain(v) for k,v in x.items()}
    if isinstance(x, (tuple,list)): return [plain(v) for v in x]
    return x.tolist() if isinstance(x,np.ndarray) else x

def write(path, value):
    with path.open("x",encoding="utf-8") as f:
        json.dump(plain(value),f,indent=2,allow_nan=False); f.write("\n")

def point_segment(point, a, b):
    delta=b-a; t=np.clip((point-a)@delta/(delta@delta),0.,1.); nearest=a+t*delta
    return dict(distance_mm=float(np.linalg.norm(point-nearest)),point_mm=nearest.tolist())

def draw(ax, case, index, component=None, scale=1., zoom=False):
    row=case["cache"][index]; model=case["model"]; conn=model["connectivity"]
    for mirror in (False,True):
        xy=row["xy"].copy()
        if mirror: xy[:,1]=2*case["center"][1]-xy[:,1]
        ax.add_collection(PolyCollection(xy[conn[model["solid"]]],facecolors="#457b9d",edgecolors="#24455d",linewidths=.1))
        ax.add_collection(PolyCollection(xy[conn[model["workpiece_cells"]]],facecolors="lightgrey",edgecolors="none"))
        if component:
            positions=row["nodes"]["coordinates_mm"].copy(); vectors=row["nodes"]["forces_on_body_N"][component].copy()
            if mirror: positions[:,1]=2*case["center"][1]-positions[:,1]; vectors[:,1]*=-1
            ax.quiver(*positions.T,*(vectors*scale).T,angles="xy",scale_units="xy",scale=1.,color="#c43b21",width=.003,minlength=0,minshaft=1)
    ax.axhline(case["center"][1],color="grey",ls=":",lw=.7)
    if zoom:
        tip=row["xy"][2510]; ax.scatter(*tip,c="#e09113",s=25,zorder=4)
        for name,w in row["tip"].items():
            q=w["point_mm"]; ax.plot([tip[0],q[0]],[tip[1],q[1]],"--",lw=1,label=f"tip to {name}: {w['distance_mm']:.4g} mm")
        for face in row["geometry"]["faces"].values():
            hit=face["closest_hit"]
            if hit: ax.annotate("",xy=hit["edge_point_mm"],xytext=hit["face_point_mm"],arrowprops=dict(arrowstyle="->",color="#219653"))
        cx,cy=case["center"]; side=case["side"]
        ax.set_xlim(cx-side/2-4,max(84.,cx+side/2+3)); ax.set_ylim(cy-side/2-7,cy+1); ax.legend(fontsize=6)
    else: ax.set_xlim(*case["xlim"]); ax.set_ylim(*case["ylim"])
    ax.set_aspect("equal"); ax.set_xlabel("x [mm]"); ax.set_ylabel("y [mm]")
    r=row["record"]; ax.set_title(f"{case['label']} ({case['result']['status']}) | {index} {r['leg']} d={r['d']:g} mm | x1",fontsize=8)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ("repo","protocol","output"): p.add_argument("--"+k,type=Path,required=True)
    p.add_argument("--case",action="append",required=True,metavar="LABEL=RESULT_DIRECTORY")
    p.add_argument("--reference",action="append",default=[],metavar="LABEL=SUMMARY_JSON")
    p.add_argument("--stop-file",type=Path); p.add_argument("--time-limit",type=float,default=120.)
    a=p.parse_args(); repo=a.repo.resolve(); root=repo.parent; out=a.output.resolve(); out.relative_to(root)
    out.mkdir(parents=True,exist_ok=False)
    pins,cases,failure={},[],None; counts=dict(geometry_started=0,geometry_completed=0,nodal_started=0,nodal_completed=0)
    pure=False; peak=0; force_max=None
    import psutil
    process=psutil.Process()
    def checkpoint():
        nonlocal peak
        m=process.memory_info(); peak=max(peak,m.rss,getattr(m,"peak_wset",m.rss))
        if perf_counter()-STARTED>a.time_limit or peak>8*1024**3 or (a.stop_file and a.stop_file.exists()):
            raise RuntimeError("Saved observation/view resource window closed")
    def bind(path, expected=None):
        path=path.resolve(); path.relative_to(root); h=sha256(path.read_bytes()).hexdigest()
        if expected is not None and h!=expected: raise ValueError("File SHA differs: "+str(path))
        pins[path]=h; return h
    sys.path.insert(0,str(repo/"scripts")); sys.path.insert(0,str(repo/"src"))
    from measure_native_workpiece_regions import descriptor_sha,pure_sources
    def read(path, expected=None, semantic=False):
        bind(path,expected); value=json.loads(path.read_text(encoding="utf-8"))
        if semantic and descriptor_sha(value)!=value["descriptor_sha256"]: raise ValueError("Descriptor SHA differs")
        return value
    def archive(directory, declaration):
        path=directory/declaration["path"]; bind(path,declaration["sha256"])
        with np.load(path,allow_pickle=False) as z: data={k:z[k].copy() for k in z.files}
        fields={k:dict(dtype=v.dtype.name,shape=list(v.shape),sha256=sha256(v.tobytes()).hexdigest()) for k,v in data.items()}
        if fields!=declaration["fields"]: raise ValueError("Archive field identity differs")
        return data
    try:
        protocol=read(a.protocol.resolve())
        for name,h in protocol["bindings"].items(): bind(root/name,h)
        sources=list(pure_sources(repo).values())+[repo/"src/hf_eval/workpiece_nodal.py",repo/"scripts/measure_native_workpiece_regions.py",Path(__file__).resolve()]
        for source in sources: bind(source,protocol["bindings"][source.relative_to(root).as_posix()])
        from hf_eval.native_region_geometry import measure_native_workpiece_regions
        from hf_eval.workpiece_nodal import observe_workpiece_nodal_forces
        allowed={"hf_eval","hf_eval.native_region_geometry","hf_eval.boundary_geometry","hf_eval.workpiece_nodal"}
        loaded={n for n in sys.modules if n=="hf_eval" or n.startswith("hf_eval.")}
        if loaded!=allowed: raise ValueError("Unexpected hf_eval imports in pure observation")
        for name in loaded:
            expected=repo/"src/hf_eval"/("__init__.py" if name=="hf_eval" else name.split(".")[-1]+".py")
            if Path(sys.modules[name].__file__).resolve()!=expected: raise ValueError("Pure module came from another source")
        pure=True; references=dict(x.split("=",1) for x in a.reference)
        for spec in a.case:
            label,path=spec.split("=",1)
            if Path(label).name!=label or label in (".","..") or any(c["label"]==label for c in cases): raise ValueError("Use unique simple case labels")
            directory=Path(path).resolve(); directory=directory.parent if directory.is_file() else directory
            result=read(directory/"result.json",semantic=True); model_file=directory/result["model"]["descriptor_path"]
            meta=read(model_file,result["model"]["descriptor_file_sha256"],True)
            if meta["task_sha256"]!=result["task_sha256"] or meta["arrays"]["sha256"]!=result["model"]["arrays_sha256"]: raise ValueError("Path/model/task differ")
            model=archive(model_file.parent,meta["arrays"]); body=meta["task"]["workpiece"]
            if not np.array_equal(model["coordinates"][2510],[80.,30.]): raise ValueError("Declared coarse tip node2510 differs")
            ref=read(Path(references[label]).resolve()) if label in references else None
            if result["accepted_states"]!=len(result["states"]): raise ValueError("Saved accepted count differs")
            if ref and (ref["status"]!="pass" or ref["result_sha256"]!=pins[(directory/"result.json").resolve()] or ref["accepted_states"]!=len(result["states"]) or len(ref["states"])!=len(result["states"]) or ref["HP_calls_started"]!=ref["HP_calls_completed"] or ref["HP_calls_completed"]!=2*len(result["states"])): raise ValueError("Require same-path passing reference")
            target=out/label; target.mkdir(); case=dict(label=label,model=model,center=np.array(body["center_mm"]),side=float(body["side_mm"]),task=meta["task"],model_sha256=meta["arrays"]["sha256"],result=result,reference_available=ref is not None,cache=[]); cases.append(case)
            node_file=(target/"nodes.csv").open("x",newline="",encoding="utf-8")
            with node_file:
                writer=csv.writer(node_file); writer.writerow(["index","original_target_index","leg","d_mm","state_sha256","node_id","x_mm","y_mm","group"]+[c+"_F"+axis+"_N" for c in PARTS for axis in ("x","y")])
                for index,r in enumerate(result["states"]):
                    checkpoint(); stored=read(directory/r["descriptor_path"],r["descriptor_file_sha256"],True)
                    if stored!={k:v for k,v in r.items() if k not in ("descriptor_path","descriptor_file_sha256")}: raise ValueError("State/path record differs")
                    if ref:
                        q=ref["states"][index]
                        if q["status"]!="pass" or q["index"]!=index or q["state_sha256"]!=r["state_sha256"] or q["leg"]!=r["leg"] or q["original_target_index"]!=r["original_target_index"] or q["target_mm"]!=r["d"]: raise ValueError("Reference context differs")
                    state=archive(directory,r["state"]); force=archive(directory,r["forces"]); destination=target/f"{index:03d}"; destination.mkdir()
                    if any(np.any(state[k][model["workpiece_dofs"]]) for k in ("lift","fluctuation")): raise ValueError("Saved fixed-body arrays must both be zero")
                    counts["geometry_started"]+=1; geometry=measure_native_workpiece_regions(model,meta,state["lift"],state["fluctuation"]); counts["geometry_completed"]+=1; write(destination/"geometry.json",geometry)
                    if not geometry["geometry_valid"]: raise ValueError("Invalid saved geometry; evidence retained, following states stopped")
                    counts["nodal_started"]+=1; nodes=observe_workpiece_nodal_forces(model,force,symmetry_y_mm=case["center"][1],moment_origin_mm=case["center"]); counts["nodal_completed"]+=1; write(destination/"nodal.json",nodes)
                    if nodes["summary"]["force_on_lower_body_N"]!=r["workpiece"]["force_on_lower_body_N"]: raise ValueError("Nodal sum differs from cached body resultant")
                    if not np.array_equal(-nodes["forces_on_body_N"]["total"],force["support_reaction"].reshape(-1,2)[nodes["node_ids"]]): raise ValueError("Every body holding vector must oppose the ON-body total weak force")
                    xy=model["coordinates"]+state["lift"].reshape(-1,2)+state["fluctuation"].reshape(-1,2); tip=xy[2510]; lo=case["center"]-case["side"]/2; hi=np.array([case["center"][0]+case["side"]/2,case["center"][1]])
                    segments=dict(bottom=(lo,np.array([hi[0],lo[1]])),left=(lo,np.array([lo[0],hi[1]])),right=(np.array([hi[0],lo[1]]),hi)); witnesses={k:point_segment(tip,*v) for k,v in segments.items()}
                    medium=~model["solid"].copy(); medium[model["workpiece_cells"]]=False
                    strain=(np.swapaxes(force["F"],-1,-2)@force["F"]-np.eye(2))*.5; eigen=np.linalg.eigvalsh(strain)
                    row=dict(index=index,original_target_index=r["original_target_index"],leg=r["leg"],d_mm=r["d"],state_sha256=r["state_sha256"],R_input_N=r["R_input"],q_out_mm=r["q_out"],tip_x_mm=tip[0],tip_y_mm=tip[1],solid_min_J=float(force["J"][model["solid"]].min()),medium_min_J=float(force["J"][medium].min()),solid_Green_principal_min=float(eigen[model["solid"]].min()),solid_Green_principal_max=float(eigen[model["solid"]].max()),medium_max_abs_Hu_per_mm=float(abs(force["Hu"][medium]).max()),raw_overlap=geometry["regions"]["raw_interior_overlap"],strict_overlap=geometry["regions"]["strict_interior_overlap"],roundoff_ambiguous=geometry["regions"]["roundoff_ambiguous"])
                    row.update({"tip_to_"+k+"_mm":v["distance_mm"] for k,v in witnesses.items()}); row.update({k+"_first_ray_mm":v["minimum_first_ray_hit_mm"] for k,v in geometry["faces"].items()})
                    row.update({c+"_body_F"+axis+"_N":nodes["summary"]["force_on_lower_body_N"][c][j] for c in PARTS for j,axis in enumerate(("x","y"))})
                    row["cached_two_sided_normal_magnitude_sum_N"]=r["workpiece"]["two_sided_normal_magnitude_sum_N"]
                    case["cache"].append(dict(record=r,row=row,xy=xy,geometry=geometry,nodes=nodes,tip=witnesses,J=force["J"],Hu=force["Hu"],eigen=eigen,medium=medium)); write(destination/"derived.json",dict(row=row,tip_surface_witnesses=witnesses,scope="Binary64 saved-F in-plane Green strain and unsigned finite-segment tip distance; no new HP/contact qualification"))
                    for j,node in enumerate(nodes["node_ids"]):
                        group=next(g for g in GROUPS if nodes["masks"][g][j]); writer.writerow([index,r["original_target_index"],r["leg"],r["d"],r["state_sha256"],int(node),*nodes["coordinates_mm"][j],group]+[float(x) for c in PARTS for x in nodes["forces_on_body_N"][c][j]])
            rows=[x["row"] for x in case["cache"]]
            if not rows: raise ValueError("No saved accepted state")
            with (target/"states.csv").open("x",newline="",encoding="utf-8") as f:
                writer=csv.DictWriter(f,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
            write(target/"summary.json",dict(production_status=result["status"],reference_available=ref is not None,accepted_states=len(rows),rows=rows))
        force_max=max(float(np.linalg.norm(x["nodes"]["forces_on_body_N"][c],axis=1).max()) for case in cases for x in case["cache"] for c in PARTS); scale=4/force_max if force_max else 1.
        xlim=(min(-2.,min(float(x["xy"][:,0].min())-2 for c in cases for x in c["cache"])),max(83.,max(float(x["xy"][:,0].max())+2 for c in cases for x in c["cache"])))
        ylim=(min(-2.,min(float(x["xy"][:,1].min())-2 for c in cases for x in c["cache"])),max(82.,max(2*c["center"][1]-float(x["xy"][:,1].min())+2 for c in cases for x in c["cache"])))
        for case in cases: case.update(xlim=xlim,ylim=ylim)
        fig,axes=plt.subplots(len(cases),4,figsize=(19,5*len(cases)),squeeze=False)
        for i,case in enumerate(cases):
            peak_index=int(np.argmax([x["record"]["d"] for x in case["cache"]])); case["peak_index"]=peak_index
            draw(axes[i,0],case,peak_index); draw(axes[i,1],case,len(case["cache"])-1); draw(axes[i,2],case,peak_index,zoom=True)
            axes[i,0].set_title("PEAK accepted | "+axes[i,0].get_title(),fontsize=8); axes[i,1].set_title("LAST accepted | "+axes[i,1].get_title(),fontsize=8)
            ds=[x["record"]["d"] for x in case["cache"]]
            for c in PARTS: axes[i,3].plot(ds,[x["row"][c+"_body_Fy_N"] for x in case["cache"]],"o-",ms=3,label=c+" lower-body Fy")
            axes[i,3].plot(ds,[x["record"]["R_input"] for x in case["cache"]],"k.--",label="input R"); axes[i,3].plot(ds,[x["row"]["cached_two_sided_normal_magnitude_sum_N"] for x in case["cache"]],":",color="#bb4ea0",label="cached 2|lower Fy| magnitude sum"); axes[i,3].set(xlabel="mean d [mm]",ylabel="force [N]",title="Actual accepted path order"); axes[i,3].legend(fontsize=7)
        fig.suptitle("Production observations only, partial paths allowed; x1 + visual mirror; orange distances / green rays are not forces"); fig.tight_layout(); fig.savefig(out/"comparison.png",dpi=150); plt.close(fig)
        fig,axes=plt.subplots(len(cases),2,figsize=(12,4*len(cases)),squeeze=False)
        for i,case in enumerate(cases):
            ds=[x["record"]["d"] for x in case["cache"]]
            for name in ("bottom","left","right"): axes[i,0].plot(ds,[x["tip"][name]["distance_mm"] for x in case["cache"]],"o-",label="tip unsigned to "+name)
            for name in ("bottom","left"): axes[i,0].plot(ds,[x["geometry"]["faces"][name]["minimum_first_ray_hit_mm"] for x in case["cache"]],".--",label=name+" outward first ray")
            for c in PARTS: axes[i,1].plot(ds,[x["row"][c+"_body_Fx_N"] for x in case["cache"]],"o-",label=c+" lower-body Fx")
            axes[i,0].set(xlabel="d [mm]",ylabel="distance [mm]",title=case["label"]); axes[i,1].set(xlabel="d [mm]",ylabel="signed Fx [N]")
            for ax in axes[i]: ax.legend(fontsize=7); ax.grid(alpha=.2)
        fig.tight_layout(); fig.savefig(out/"distances_forces.png",dpi=150); plt.close(fig)
        peak_fields=[]
        for case in cases:
            x=case["cache"][case["peak_index"]]; model=case["model"]
            peak_fields.append([("solid max in-plane Green principal",model["solid"],x["eigen"][...,1].max(axis=1)),("free-medium mean J",x["medium"],x["J"].mean(axis=1)),("free-medium Hu Frobenius [1/mm]",x["medium"],np.linalg.norm(x["Hu"].reshape(len(model["solid"]),-1),axis=1))])
        field_ranges=[(min(float(fields[j][2][fields[j][1]].min()) for fields in peak_fields),max(float(fields[j][2][fields[j][1]].max()) for fields in peak_fields)) for j in range(3)]
        fig,axes=plt.subplots(len(cases),3,figsize=(15,4*len(cases)),squeeze=False)
        for i,case in enumerate(cases):
            checkpoint(); x=case["cache"][case["peak_index"]]; model=case["model"]
            for j,(ax,(title,mask,values)) in enumerate(zip(axes[i],peak_fields[i])):
                collection=PolyCollection(x["xy"][model["connectivity"][mask]],array=values[mask],cmap="viridis"); collection.set_clim(*field_ranges[j]); ax.add_collection(collection); ax.add_collection(PolyCollection(x["xy"][model["connectivity"][model["workpiece_cells"]]],facecolor="lightgrey")); ax.autoscale(); ax.set_aspect("equal"); ax.set_title(case["label"]+" | "+title,fontsize=8); fig.colorbar(collection,ax=ax)
        fig.tight_layout(); fig.savefig(out/"peak_fields.png",dpi=150); plt.close(fig)
        for case in cases:
            frames=[]
            for index,x in enumerate(case["cache"]):
                checkpoint(); fig,axes=plt.subplots(1,3,figsize=(14,7))
                for ax,c in zip(axes,PARTS): draw(ax,case,index,c,scale); ax.set_title(c+" ON-body nodal weak force [N] | "+str(index))
                glyph=f"{force_max:.5g} N =4 mm glyph" if force_max else "all nodal forces zero"
                fig.suptitle(f"{case['label']} [{case['result']['status']}; production-only] | {index}/{len(case['cache'])-1} {x['record']['leg']} d={x['record']['d']:g} mm | x1; mirror only; {glyph}; all body nodes incl cut/interior; no interpolation/pressure")
                fig.tight_layout(); fig.canvas.draw(); frames.append(Image.fromarray(np.asarray(fig.canvas.buffer_rgba()).copy()).convert("RGB")); plt.close(fig)
            frames[0].save(out/case["label"]/"actual_states.gif",save_all=True,append_images=frames[1:],duration=300,loop=0,optimize=False,disposal=2)
            for frame in frames: frame.close()
            with Image.open(out/case["label"]/"actual_states.gif") as gif:
                if gif.n_frames!=len(case["cache"]): raise ValueError("GIF must retain every accepted index")
        checkpoint()
        if {n for n in sys.modules if n=="hf_eval" or n.startswith("hf_eval.")}!=allowed:
            pure=False; raise ValueError("Unexpected mechanical import during observations")
        if not all(sha256(path.read_bytes()).hexdigest()==h for path,h in pins.items()): raise ValueError("Bound source/input changed")
    except BaseException as error:
        failure=repr(error); raise
    finally:
        write(out/"view.json",dict(schema_version="saved-shifted-workpiece-views-1.0",status="pass" if failure is None else "failed",failure=failure,**counts,
            new_F_T_model_solver_HP_calls=0 if pure else None,mechanical_hooks_monitored=False,zero_mechanics_basis="Pinned pure module origins and saved-array derivations, not dynamic mechanical hook monitoring",
            input_source_bindings={p.relative_to(root).as_posix():h for p,h in pins.items()},outputs={p.relative_to(out).as_posix():sha256(p.read_bytes()).hexdigest() for p in out.rglob("*") if p.is_file()},
            cases=[dict(label=c["label"],production_status=c["result"]["status"],production_path_completed=c["result"]["path_completed"],unload_endpoint_reached=c["result"]["unload_endpoint_reached"],reference_available=c["reference_available"],saved_accepted_states=c["result"]["accepted_states"],observed_states=len(c["cache"]),peak_index=c.get("peak_index"),last_index=len(c["cache"])-1,task=c["task"],model_sha256=c["model_sha256"]) for c in cases],
            common_nodal_force_scale=dict(max_force_N=force_max,display_length_mm=4,all_body_nodes=True,components=PARTS),
            common_peak_field_ranges=field_ranges if "field_ranges" in locals() else None,
            mirroring="Visualization only about native symmetry; lower-body resultants stay half-model quantities; reflected arrows flip Fy, no doubled solved DOFs",
            strain_scope="Binary64 in-plane Green eigenvalues from saved F; not fresh HP qualified",distance_scope="Node2510 unsigned finite-segment distance; outward face first rays separately; null=no hit, not zero",
            contact_pressure_clamping_qualified=False,elapsed_seconds=perf_counter()-STARTED,sampled_peak_RSS_bytes=peak))

if __name__=="__main__": main()
