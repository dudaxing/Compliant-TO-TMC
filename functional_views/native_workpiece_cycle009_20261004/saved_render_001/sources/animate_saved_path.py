"""Animate each saved accepted state at physical deformation scale one."""
import argparse
import io
import json
from pathlib import Path
from hashlib import sha256
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.colors import Normalize
from PIL import Image


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--stage",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    directory=args.stage/"result"
    result=json.loads((directory/"result.json").read_text(encoding="utf-8"))
    assert result["status"]=="success" and result["unload_endpoint_reached"]
    summary=json.loads((args.stage/"reference/summary.json").read_text(encoding="utf-8"))
    assert summary["status"]=="pass" and summary["HP_calls_completed"]==2*len(result["states"])
    args.output.mkdir(parents=True,exist_ok=False)
    with np.load(directory/"model/model.npz",allow_pickle=False) as source:
        xy, cells, solid, body=(source[n] for n in ("coordinates","connectivity","solid","workpiece_cells"))
    states=[]
    for row in result["states"]:
        with np.load(directory/row["state"]["path"],allow_pickle=False) as data:
            u=(data["lift"]+data["fluctuation"]).reshape(-1,2)
        states.append((row,u))
    peak=max(float(np.linalg.norm(u,axis=1).max()) for row,u in states)
    peak_index=max(range(len(states)),key=lambda i:states[i][0]["d"])
    norm=Normalize(0,peak)
    frames=[]
    for index,(row,u) in enumerate(states):
        fig,axes=plt.subplots(1,2,figsize=(12,4.5),constrained_layout=True)
        moved=xy+u
        field=np.linalg.norm(u[cells],axis=2).mean(axis=1)
        for ax in axes:
            ax.add_collection(PolyCollection(xy[cells[solid]],facecolors="none",edgecolors="#d6dce3",linewidths=.2))
            polygons=PolyCollection(moved[cells[solid]],array=field[solid],cmap="Oranges",norm=norm,
                                   edgecolors="#946b32",linewidths=.12)
            ax.add_collection(polygons)
            ax.add_collection(PolyCollection(xy[cells[body]],facecolors="#dde3e8",edgecolors="#78899c",linewidths=.2))
            ax.set_aspect("equal")
            ax.set(xlabel="x [mm]",ylabel="y [mm]")
        axes[0].set(xlim=(-1,81),ylim=(-1,41),title="Full lower-half model / physical deformation x1")
        axes[1].set(xlim=(53,81),ylim=(23,41),title="Workpiece detail / physical deformation x1")
        fig.colorbar(polygons,ax=axes,label="Mechanism mean nodal |u| [mm]",shrink=.65)
        fx,fy=row["workpiece"]["force_on_lower_body_N"]["total"]
        fig.suptitle(f"Accepted {index+1}/{len(states)}: {row['leg']}, mean input {row['d']:g} mm\n"
                     f"Input R={row['R_input']:.6g} N | output uy={row['q_out']:.6g} mm | "
                     f"body (Fx,Fy)=({fx:.4g},{fy:.4g}) N | min J={row['minimum_J']:.5g}",fontsize=11)
        buffer=io.BytesIO()
        fig.savefig(buffer,format="png",dpi=110)
        plt.close(fig)
        if index in (0,peak_index,len(states)-1):
            (args.output/f"actual_state_{index:03d}.png").write_bytes(buffer.getvalue())
        buffer.seek(0)
        frames.append(Image.open(buffer).convert("RGB"))
    gif=args.output/"cycle009_actual_path.gif"
    frames[0].save(gif,save_all=True,append_images=frames[1:],duration=1000,loop=0)
    (args.output/"metadata.json").write_text(json.dumps(dict(
        actual_accepted_frames=len(states),state_sha256=[r["state_sha256"] for r,u in states],
        deformation_scale=1,force_scope="Fixed lower-body weak-form force, not pressure or clamp qualification",
        image_sha256=sha256(gif.read_bytes()).hexdigest(),new_mechanics_calls=0),indent=2)+"\n",encoding="utf-8")


if __name__=="__main__":
    main()
