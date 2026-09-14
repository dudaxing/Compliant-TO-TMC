"""Static diagnostics derived only from saved geometry, displacement and task data."""
import json
from pathlib import Path
import numpy as np


def plot_result(geometry, result, arrays, directory):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    from .regions import region_nodes
    directory = Path(directory)
    coordinates = np.asarray(arrays["coordinates"])
    connectivity = np.asarray(arrays["solid_connectivity"], dtype=int)
    displacement = np.asarray(arrays["u"]).reshape(-1, 2)
    polygons = coordinates[connectivity]
    lx, ly = geometry.grid["extent_mm"]
    x0, y0 = geometry.grid["origin_mm"]
    metrics = result["metrics_at_target"]
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.4), constrained_layout=True)
    axes[0].imshow(geometry.solid, origin="lower", extent=(x0,x0+lx,y0,y0+ly),
                   cmap="Greys", vmin=0, vmax=1, interpolation="nearest")
    axes[1].imshow(geometry.arrays["design"] + 2*geometry.arrays["passive_solid"] +
                   3*geometry.arrays["passive_void"], origin="lower",
                   extent=(x0,x0+lx,y0,y0+ly), cmap="viridis", vmin=0, vmax=3,
                   interpolation="nearest")
    for name, tag in geometry.metadata["region_tags"].items():
        points=np.asarray(tag["points_mm"])
        color={"support":"#bb3e37", "symmetry":"#7756a9", "input":"#198579", "output":"#3479ad"}.get(name,"gray")
        for axis in axes:
            axis.plot(points[:,0],points[:,1],lw=3,color=color,label=name)
        if "direction" in tag:
            center=points.mean(axis=0)
            direction=np.asarray(tag["direction"])
            axes[0].annotate("",xy=center+direction*0.09*lx,xytext=center,
                             arrowprops={"arrowstyle":"->","color":color,"lw":2})
    if "support" in geometry.metadata["region_tags"]:
        selected=region_nodes(geometry,geometry.metadata["region_tags"]["support"])
        attached=np.asarray(arrays["active_nodes"],dtype=bool)[selected]
        for axis in axes:
            axis.scatter(coordinates[selected,0],coordinates[selected,1],s=15,
                         facecolors=["#bb3e37" if a else "white" for a in attached],
                         edgecolors="#bb3e37",linewidths=.8,zorder=5)
    for axis in axes:
        axis.set(xlabel="x [mm]",ylabel="y [mm]",aspect="equal",xlim=(x0-0.03*lx,x0+1.03*lx),ylim=(y0-0.04*ly,y0+1.07*ly))
    axes[0].set_title("Imported authority: solid cells, fixture and mean ports")
    axes[1].set_title("Regions: design / passive solid / passive void")
    axes[0].legend(loc="upper center",bbox_to_anchor=(.5,-.18),ncol=4,frameon=False)
    fig.suptitle(f"{geometry.metadata['case_family']} | t = {geometry.metadata['thickness_mm']:g} mm | qualification: {result['qualification']['status']}\n"
                 "Hollow fixture markers: no incident solid; not constrained in this diagnostic")
    fig.savefig(directory/"geometry_layout.png",dpi=170,bbox_inches="tight",pad_inches=.15)
    plt.close(fig)
    magnitude=np.linalg.norm(displacement,axis=1)
    peak=float(magnitude.max())
    factor=0.10*max(lx,ly)/peak if peak>0 else 1.0
    deformed=(coordinates+factor*displacement)[connectivity]
    fig, axes=plt.subplots(1,2,figsize=(12,4.4),constrained_layout=True)
    axes[0].add_collection(PolyCollection(polygons,facecolors="#dddfe2",edgecolors="none"))
    axes[0].add_collection(PolyCollection(deformed,facecolors="#6275a0",edgecolors="none",alpha=.85))
    color=axes[1].add_collection(PolyCollection(polygons,array=magnitude[connectivity].mean(axis=1),cmap="viridis",edgecolors="none"))
    fig.colorbar(color,ax=axes[1],label="Mean nodal displacement magnitude [mm]")
    for axis in axes:
        axis.autoscale_view();axis.set(xlabel="reference x [mm]",ylabel="reference y [mm]",aspect="equal")
    axes[0].set_title(f"Gray: reference; blue: display displacement x {factor:.3g}")
    axes[1].set_title("Magnitude plotted on reference solid geometry")
    domain_label="modeled half" if geometry.metadata["model_extent"]["kind"]=="lower_half" else "modeled domain"
    fig.suptitle(f"LINEAR diagnostic | q_in={metrics['q_in_mm']:.5g} mm | q_out={metrics['q_out_mm']:.5g} mm\n"
                 f"R_in={metrics['R_in_N']:.5g} N on {domain_label} | no contact or nonlinear path")
    fig.savefig(directory/"linear_deformation.png",dpi=170,bbox_inches="tight",pad_inches=.15)
    plt.close(fig)
    metadata={"status":"success", "files":["geometry_layout.png","linear_deformation.png"],
              "raw_data":"fields.npz", "displacement_display_factor":factor,
              "actual_input_displacement_mm":metrics["q_in_mm"],
              "scope":"Solid linear diagnostic, display amplification is not actual deformation",
              "region_codes":{"1":"design","2":"passive solid","3":"passive void"}}
    (directory/"plot_metadata.json").write_text(json.dumps(metadata,indent=2),encoding="utf-8")
    return metadata
