"""Show all saved body nodal vectors with one N scale across the entire path."""
import argparse
import csv
from hashlib import sha256
import json
from pathlib import Path
import sys
from time import perf_counter
STARTED = perf_counter()
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection, LineCollection
from PIL import Image

COMPONENTS = ("total", "material", "regularization")
COLORS = ("#162d45", "#2472a5", "#c55b23")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("repo", "input", "source", "output"):
        parser.add_argument("--"+name, required=True, type=Path)
    parser.add_argument("--reference", type=Path)
    parser.add_argument("--stop-file", type=Path)
    parser.add_argument("--time-limit", type=float, default=120.)
    args = parser.parse_args()
    report_file = args.input/"summary.json"
    csv_file = args.input/"nodes.csv"
    source_file = args.source/"result.json"
    pins = {p:sha256(p.read_bytes()).hexdigest() for p in (report_file,csv_file,source_file)}
    report = json.loads(report_file.read_text(encoding="utf-8"))
    source = json.loads(source_file.read_text(encoding="utf-8"))
    assert report["status"] == "pass" and report["observations_completed"] == len(source["states"])
    assert len(report["states"]) == len(source["states"])
    for role, value in report["input_source_bindings"].items():
        p = (args.reference if role == "reference" else
             (args.repo if role.startswith("repo/") else args.source)/role.split("/",1)[1])
        assert p is not None and sha256(p.read_bytes()).hexdigest() == value; pins[p] = value
    with csv_file.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    with np.load(args.source/"model/model.npz", allow_pickle=False) as archive:
        model = {name: archive[name].copy() for name in archive.files}
    xy, cells = model["coordinates"], model["connectivity"]
    body = model["workpiece_cells"]
    fixed_xy = xy[model["workpiece_nodes"]]
    states = []
    for index, (saved, observed) in enumerate(zip(source["states"], report["states"])):
        selected = [r for r in rows if int(r["accepted_index"]) == index]
        assert len(selected) == len(fixed_xy) and observed["state_sha256"] == saved["state_sha256"]
        assert [int(r["node_id"]) for r in selected] == model["workpiece_nodes"].tolist()
        vectors = {name: np.array([[float(r[name+"_Fx_N"]),float(r[name+"_Fy_N"])] for r in selected])
                   for name in COMPONENTS}
        states.append((saved,observed,vectors,[r["group"] for r in selected]))
    assert len(rows) == len(states)*len(fixed_xy)
    maximum = max(float(np.linalg.norm(v,axis=1).max()) for s,o,vec,g in states for v in vec.values())
    scale = 3./maximum if maximum else 1.
    key = 10.**np.floor(np.log10(maximum)) if maximum else 1.
    peak = max(range(len(states)),key=lambda i:states[i][0]["d"])
    output = args.output.resolve(); output.mkdir(parents=True,exist_ok=False)

    def checkpoint():
        assert perf_counter()-STARTED <= args.time_limit
        assert args.stop_file is None or not args.stop_file.exists()

    def draw(index):
        checkpoint()
        saved, observed, vectors, groups = states[index]
        path = args.source/saved["state"]["path"]
        with np.load(path,allow_pickle=False) as archive:
            moved = xy+(archive["lift"]+archive["fluctuation"]).reshape(-1,2)
        fig,axes = plt.subplots(1,3,figsize=(15,5.8),layout="constrained")
        for ax,name,color in zip(axes,COMPONENTS,COLORS):
            ax.add_collection(PolyCollection(moved[cells[model["solid"]]],facecolors="#e5edf3",edgecolors="#bccdd9",linewidths=.25))
            ax.add_collection(PolyCollection(xy[cells[body]],facecolors="#f1f3f5",edgecolors="#dce1e5",linewidths=.2))
            edges = observed["edges"]
            ax.add_collection(LineCollection(xy[np.asarray(edges["physical"],int)],colors="#586879",linewidths=1.2))
            ax.add_collection(LineCollection(xy[np.asarray(edges["cut"],int)],colors="#8753a4",linewidths=1.1,linestyles="dashed"))
            mask = np.array([g == "physical_and_cut" for g in groups])
            ax.scatter(*fixed_xy[mask].T,s=28,facecolor="#d9942b",edgecolor="#6f451b",zorder=4)
            mask = np.array([g == "cut_only" for g in groups])
            ax.scatter(*fixed_xy[mask].T,s=6,c="#8753a4",zorder=4)
            force = vectors[name]
            arrows = ax.quiver(*fixed_xy.T,*force.T,color=color,angles="xy",scale_units="xy",scale=1./scale,
                               width=.005,headwidth=3.5,headlength=4.5,minlength=0,minshaft=0)
            ax.quiverkey(arrows,.70,.05,key,f"{key:g} N",labelpos="E",coordinates="axes")
            fx,fy = observed["summary"]["force_on_lower_body_N"][name]
            moment = observed["summary"]["moment_about_origin_Nmm"][name]
            ax.set(title=f"{name}\nSum (Fx,Fy)=({fx:.5g},{fy:.5g}) N\nDerived Mz={moment:.5g} N mm",
                   xlabel="x [mm]",ylabel="y [mm]",xlim=(fixed_xy[:,0].min()-8,fixed_xy[:,0].max()+4),
                   ylim=(fixed_xy[:,1].min()-6,fixed_xy[:,1].max()+3))
            ax.set_aspect("equal")
        fig.suptitle(f"Saved path {report['production_status']} | accepted {index+1}/{len(states)}: {saved['leg']} | mean input {saved['d']:g} mm | "
                     f"input R={saved['R_input']:.6g} N\nFixed lower-half body: force ON body = negative saved internal force; physical geometry x1",fontsize=13)
        fig.supxlabel("One arrow scale across all states/components; dashed purple = symmetry cut; gold = physical/cut shared nodes.\n"
                      "All body nodes retained; zero arrows invisible, tiny signed values remain in CSV. Nodal forces are not pressure. "
                      f"Moments about {observed['moment_origin_mm']} mm; no new solve/HP/contact qualification.",fontsize=9)
        image = output/f"nodes_state_{index:03d}.png"
        fig.savefig(image,dpi=130);plt.close(fig)
        return image

    images = [draw(index) for index in range(len(states))]
    frames = [Image.open(path).convert("RGB") for path in images]
    gif = output/"nodal_force_path.gif"
    frames[0].save(gif,save_all=True,append_images=frames[1:],duration=1200,loop=0)
    index_list = [0,peak,len(states)-1]
    modules = sorted(n for n in sys.modules if n == "hf_eval" or n.startswith("hf_eval."))
    assert not modules
    (output/"key_states.json").write_text(json.dumps(dict(indices=index_list,
        observation_summary_sha256=pins[report_file], nodal_csv_sha256=pins[csv_file],
        saved_result_sha256=pins[source_file], renderer_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
        common_N_to_display_mm=scale,arrow_key_N=key,maximum_nodal_vector_N=maximum,
        actual_frames=len(states),all_body_nodes=len(fixed_xy),deformation_scale=1,
        loaded_hf_eval_modules=modules, mechanical_hooks_monitored=False,
        count_basis="Pinned saved data and plotting source/import closure; no mechanical or geometry metrics",
        new_force_tangent_solver_HP_calls=0,new_geometry_measurements=0,
        scope="Saved signed nodal vectors; no pressure, face allocation or new moment/constitutive qualification"),indent=2)+"\n",encoding="utf-8")
    checkpoint()
    assert all(sha256(p.read_bytes()).hexdigest() == value for p,value in pins.items())
    print(json.dumps(dict(status="pass",frames=len(states),maximum_nodal_vector_N=maximum,
                         elapsed_seconds=perf_counter()-STARTED)))


if __name__ == "__main__":
    main()
