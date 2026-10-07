"""Local saved fixed-square fit, from cached physical edges/F/nodal reports only."""
from time import perf_counter
STARTED = perf_counter()
from pathlib import Path
from hashlib import sha256
import argparse, csv, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

PARTS = ("total", "material", "regularization")

def canonical(value):
    if isinstance(value, dict): return {k:canonical(v) for k,v in value.items()}
    if isinstance(value, list): return [canonical(v) for v in value]
    return (0. if value == 0. else value).hex() if isinstance(value,float) else value

def descriptor(value):
    return sha256(json.dumps(canonical({k:v for k,v in value.items() if k != "descriptor_sha256"}),sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("repo","protocol","output"): p.add_argument("--"+name,type=Path,required=True)
    p.add_argument("--case",action="append",required=True,metavar="LABEL=RESULT_DIRECTORY")
    p.add_argument("--view",action="append",required=True,metavar="LABEL=MASTER_VIEW_CASE_DIRECTORY")
    p.add_argument("--stop-file",type=Path); p.add_argument("--time-limit",type=float,default=120.)
    a=p.parse_args(); root=a.repo.resolve().parent; out=a.output.resolve(); out.relative_to(root)
    out.mkdir(parents=True,exist_ok=False); pins={}; cases=[]; failure=None; peak=0; force_max=None
    import psutil
    process=psutil.Process()
    def checkpoint():
        nonlocal peak
        m=process.memory_info(); peak=max(peak,m.rss,getattr(m,"peak_wset",m.rss))
        if perf_counter()-STARTED>a.time_limit or peak>8*1024**3 or (a.stop_file and a.stop_file.exists()): raise RuntimeError("Saved fit resource window closed")
    def bind(path,expected=None):
        path=path.resolve(); path.relative_to(root); h=sha256(path.read_bytes()).hexdigest()
        if expected is not None and h!=expected: raise ValueError("Saved source/input identity differs: "+str(path))
        pins[path]=h; return h
    def read(path,expected=None,semantic=False):
        bind(path,expected); v=json.loads(path.read_text(encoding="utf-8"))
        if semantic and descriptor(v)!=v["descriptor_sha256"]: raise ValueError("Semantic descriptor differs")
        return v
    def archive(directory,d):
        path=directory/d["path"]; bind(path,d["sha256"])
        with np.load(path,allow_pickle=False) as z: v={k:z[k].copy() for k in z.files}
        if {k:dict(dtype=str(x.dtype),shape=list(x.shape),sha256=sha256(x.tobytes()).hexdigest()) for k,x in v.items()}!=d["fields"]: raise ValueError("Saved archive field identity differs")
        return v
    def save(path,value):
        with path.open("x",encoding="utf-8") as f: json.dump(value,f,indent=2,allow_nan=False); f.write("\n")
    try:
        protocol=read(a.protocol.resolve())
        for name,h in protocol["bindings"].items(): bind(root/name,h)
        bind(Path(__file__).resolve(),protocol["bindings"][Path(__file__).resolve().relative_to(root).as_posix()])
        views=dict(x.split("=",1) for x in a.view)
        for spec in a.case:
            checkpoint(); label,path=spec.split("=",1); directory=Path(path).resolve(); cached=Path(views[label]).resolve()
            if Path(label).name!=label or label in (".","..") or any(c["label"]==label for c in cases): raise ValueError("Use unique simple labels")
            result=read(directory/"result.json",semantic=True); mv=read(cached.parent/"view.json")
            if result["status"]!="success" or not all(result[k] for k in ("path_completed","unload_endpoint_reached","task_target_executed")): raise ValueError("Local full-fit comparison requires complete paths; use master viewer for partial paths")
            if mv["status"]!="pass" or mv["input_source_bindings"].get((directory/"result.json").relative_to(root).as_posix())!=pins[(directory/"result.json").resolve()]: raise ValueError("Cached viewer came from another saved path")
            def cached_read(name):
                q=cached/name; return read(q,mv["outputs"][q.relative_to(cached.parent).as_posix()])
            summary=cached_read("summary.json")
            if summary["production_status"]!="success" or not summary["reference_available"] or summary["accepted_states"]!=len(result["states"]): raise ValueError("Require same-path reference-checked master case")
            index=int(np.argmax([r["d"] for r in result["states"]])); r=result["states"][index]
            stored=read(directory/r["descriptor_path"],r["descriptor_file_sha256"],True)
            if stored!={k:v for k,v in r.items() if k not in ("descriptor_path","descriptor_file_sha256")}: raise ValueError("Peak state descriptor differs")
            meta_file=directory/result["model"]["descriptor_path"]; meta=read(meta_file,result["model"]["descriptor_file_sha256"],True)
            if meta["task_sha256"]!=result["task_sha256"] or meta["descriptor_sha256"]!=result["model"]["descriptor_sha256"]: raise ValueError("Model/task semantic binding differs")
            model=archive(meta_file.parent,meta["arrays"]); state=archive(directory,r["state"]); force=archive(directory,r["forces"])
            geometry=cached_read(f"{index:03d}/geometry.json"); nodal=cached_read(f"{index:03d}/nodal.json"); derived=cached_read(f"{index:03d}/derived.json")
            if not geometry["geometry_valid"] or derived["row"]["state_sha256"]!=r["state_sha256"] or nodal["summary"]["force_on_lower_body_N"]!=r["workpiece"]["force_on_lower_body_N"]: raise ValueError("Cached geometry/nodal/derived context differs")
            xy=model["coordinates"]+state["lift"].reshape(-1,2)+state["fluctuation"].reshape(-1,2); conn=model["connectivity"]; solid=model["solid"]
            if not np.array_equal(model["coordinates"][2510],[80.,30.]) or any(np.any(state[k][model["workpiece_dofs"]]) for k in state): raise ValueError("Original tip/fixed-body contract differs")
            edges=np.asarray(geometry["physical_mechanism_edges"],dtype=np.int64); ref=model["coordinates"][edges]
            edges=edges[np.all(ref[:,:,1]==30.,axis=1)&np.all((ref[:,:,0]>=63.)&(ref[:,:,0]<=80.),axis=1)]
            if not len(edges) or not any(set(edge)=={2509,2510} for edge in edges): raise ValueError("Saved physical y30 contact-candidate boundary misses tip edge")
            owners={tuple(sorted((int(row[j]),int(row[(j+1)%4])))):i for i,row in enumerate(conn) if solid[i] for j in range(4)}
            cells=np.unique([owners[tuple(sorted(edge))] for edge in edges]); strain=.5*(np.swapaxes(force["F"],-1,-2)@force["F"]-np.eye(2)); principal=np.linalg.eigvalsh(strain)
            body=meta["task"]["workpiece"]; cx,cy=body["center_mm"]; half=body["side_mm"]/2
            case=dict(label=label,index=index,record=r,model=model,xy=xy,edges=edges,cells=cells,principal=principal,nodal=nodal,derived=derived,box=(cx-half,cx+half,cy-half,cy)); cases.append(case)
            save(out/(label+"_fit.json"),dict(label=label,index=index,leg=r["leg"],d_mm=r["d"],state_sha256=r["state_sha256"],source_reference_window=dict(y_mm=30.,x_mm=[63.,80.]),physical_edges=edges.tolist(),adjacent_solid_cells=cells.tolist(),tip_xy_mm=xy[2510].tolist(),body_box_mm=list(case["box"]),saved_tip_distances=derived["tip_surface_witnesses"],saved_face_rays=geometry["faces"],nodal_summary=nodal["summary"],adjacent_solid_min_J=float(force["J"][cells].min()),adjacent_solid_Green_principal_min=float(principal[cells].min()),adjacent_solid_Green_principal_max=float(principal[cells].max()),contact_or_pressure_qualified=False))
            with (out/(label+"_curve.csv")).open("x",newline="",encoding="utf-8") as f:
                w=csv.writer(f); w.writerow(["edge_index","endpoint","node_id","reference_x_mm","reference_y_mm","actual_x_mm","actual_y_mm","solid_cell","saved_Green_min","saved_Green_max"])
                for ei,edge in enumerate(edges):
                    cell=owners[tuple(sorted(edge))]
                    for j,node in enumerate(edge): w.writerow([ei,j,int(node),*model["coordinates"][node],*xy[node],cell,float(principal[cell].min()),float(principal[cell].max())])
        force_max=max(float(np.linalg.norm(np.asarray(c["nodal"]["forces_on_body_N"][part]),axis=1).max()) for c in cases for part in PARTS); glyph_scale=.5/force_max if force_max else 1.
        limits=(min(c["box"][0] for c in cases)-1.,max(82.,max(c["box"][1] for c in cases)+1.),min(c["box"][2] for c in cases)-3.,max(c["box"][3] for c in cases)+.5)
        vrange=(min(float(c["principal"][c["cells"],...,1].max(axis=1).min()) for c in cases),max(float(c["principal"][c["cells"],...,1].max(axis=1).max()) for c in cases))
        fig,axes=plt.subplots(len(cases),3,figsize=(16,5*len(cases)),squeeze=False)
        for i,c in enumerate(cases):
            checkpoint(); xy=c["xy"]; lo,hi,bottom,top=c["box"]
            for ax in axes[i]:
                ax.add_collection(PolyCollection(xy[c["model"]["connectivity"][c["model"]["solid"]]],facecolor="#dde6ea",edgecolor="none")); ax.fill([lo,hi,hi,lo],[bottom,bottom,top,top],color="lightgrey"); ax.set(xlim=limits[:2],ylim=limits[2:],xlabel="x [mm]",ylabel="y [mm]"); ax.set_aspect("equal"); ax.axhline(top,color="grey",ls=":",lw=.7)
            for edge in c["edges"]: axes[i,0].plot(*xy[edge].T,color="#235789",lw=2)
            axes[i,0].scatter(*xy[2510],color="#ea9010",s=25,zorder=5); axes[i,0].annotate("tip 2510",xy[2510],xytext=(4,-12),textcoords="offset points",fontsize=8)
            for name,witness in c["derived"]["tip_surface_witnesses"].items(): axes[i,0].plot([xy[2510,0],witness["point_mm"][0]],[xy[2510,1],witness["point_mm"][1]],"--",lw=.8,label=f"tip to {name}: {witness['distance_mm']:.4g} mm")
            collection=PolyCollection(xy[c["model"]["connectivity"][c["cells"]]],array=c["principal"][c["cells"],...,1].max(axis=1),cmap="viridis"); collection.set_clim(*vrange); axes[i,1].add_collection(collection); fig.colorbar(collection,ax=axes[i,1],label="max in-plane Green principal (saved F)")
            positions=np.asarray(c["nodal"]["coordinates_mm"])
            for part,color in zip(PARTS,("#161616","#277da8","#e07a5f")):
                v=np.asarray(c["nodal"]["forces_on_body_N"][part]); axes[i,2].quiver(*positions.T,*(v*glyph_scale).T,color=color,angles="xy",scale_units="xy",scale=1.,minlength=0,minshaft=1,width=.004,label=part)
            for ax in (axes[i,0],axes[i,2]): ax.legend(fontsize=7)
            for j,title in enumerate(("saved physical y30 boundary / finite surfaces","adjacent solid strain; no HP stress qualification","cached all-body weak forces; not pressure")): axes[i,j].set_title(f"{c['label']} | peak {c['index']} d={c['record']['d']:g} mm | {title}",fontsize=8)
        fig.suptitle(f"Actual x1 local fit; mathematical y40 cut dotted; no new measurement/mechanics | common glyph {force_max:.4g} N =0.5 mm"); fig.tight_layout(); fig.savefig(out/"local_fit.png",dpi=150); plt.close(fig)
        checkpoint()
        if not all(sha256(path.read_bytes()).hexdigest()==h for path,h in pins.items()): raise ValueError("Bound source/input changed")
    except BaseException as error: failure=repr(error); raise
    finally:
        save(out/"fit_view.json",dict(schema_version="saved-local-square-fit-1.0",status="pass" if failure is None else "failed",failure=failure,input_source_bindings={p.relative_to(root).as_posix():h for p,h in pins.items()},outputs={p.relative_to(out).as_posix():sha256(p.read_bytes()).hexdigest() for p in out.rglob("*") if p.is_file()},case_indices={c["label"]:c["index"] for c in cases},common_nodal_force_glyph=dict(max_force_N=force_max,display_length_mm=.5,minlength=0,minshaft=1),new_F_T_model_solver_HP_geometry_observation_calls=0,zero_call_basis="No hf_eval imports/APIs; pinned cached edges/nodal reports and saved-array derivations only",pressure_contact_clamping_qualified=False,strain_scope="Binary64 in-plane Green eigenvalues derived from saved F; not HP stress qualification",elapsed_seconds=perf_counter()-STARTED,sampled_peak_RSS_bytes=peak))

if __name__=="__main__": main()
