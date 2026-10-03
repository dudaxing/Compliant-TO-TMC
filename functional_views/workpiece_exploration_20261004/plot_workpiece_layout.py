"""One saved-array geometry preview; no FE construction or mechanics imports."""
from time import perf_counter
STARTED = perf_counter()
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import Circle, Rectangle

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INPUTS = {
    "lf_data_preparation/native_model_001/models/gripper_native_fine/model.json": "bb84034c655f4b74e5cfc478688af5c2565fa25358b4bb8e89ac3b3981883ccc",
    "lf_data_preparation/native_model_001/models/gripper_native_fine/model.npz": "f3ad62046286023344a2aab0cea4ac7466dcb98637c12f2ff7cdc66f988144d6",
    "lf_data_preparation/v2_adapter_001/converted/gripper_native_fine/geometry.json": "dbab7567c98e18174d198318f025184b3545c3681c060fa77d9435122bb0f32c",
    "lf_data_preparation/v2_adapter_001/converted/gripper_native_fine/geometry.npz": "92ff8918ae7502c3f8bfb99398b654ea1521549e7ff3ce0e8b24a9b4fa720d21",
}


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def clock():
    if perf_counter()-STARTED > 120:
        raise RuntimeError("Separate geometry-preview 120-second budget exceeded")


def main():
    png, metadata = HERE/"workpiece_layout.png", HERE/"layout_metadata.json"
    if png.exists() or metadata.exists():
        raise FileExistsError("Preview outputs already exist; no overwrite or repeat")
    before = {name: digest(ROOT/name) for name in INPUTS}
    if before != INPUTS:
        raise ValueError("Saved geometry/model input SHA differs")
    model_meta = json.loads((ROOT/next(iter(INPUTS))).read_text(encoding="utf-8"))
    with np.load(ROOT/list(INPUTS)[1], allow_pickle=False) as z:
        coords, conn, solid, old_fixed = (z[k].copy() for k in ("coordinates", "connectivity", "solid", "fixed_dofs"))
    with np.load(ROOT/list(INPUTS)[3], allow_pickle=False) as z:
        passive_void = z["passive_void"].astype(bool).ravel()
        if not np.array_equal(solid, z["solid"].ravel().astype(bool)):
            raise ValueError("Saved model and source solid masks differ")
    science = ROOT/"lf_data_preparation/native_fine_task_025_001/execution_receipt.json"
    sources = json.loads(science.read_text(encoding="utf-8"))["sources"]
    source_before = {name: digest(ROOT/name) for name in sources}
    if len(sources) != 39 or source_before != sources:
        raise ValueError("Frozen scientific source39 differs")
    center, radius, side = np.array([70., 40.]), 8., 16.
    centres = coords[conn].mean(axis=1)
    masks = {"square": (np.abs(centres-center) <= side/2).all(axis=1),
             "circle": np.sum((centres-center)**2, axis=1) <= radius**2}
    mechanism_nodes = np.unique(conn[solid])
    regions = model_meta["region_metadata"]
    ports = regions["ports"]
    candidates = {}
    for name, mask in masks.items():
        cells, nodes = np.flatnonzero(mask), np.unique(conn[mask])
        dofs = (2*nodes[:, None]+np.arange(2)).ravel()
        overlaps = {group: np.intersect1d(nodes, np.asarray(values, dtype=np.int64)).tolist()
                    for group, values in {"mechanism": mechanism_nodes, "support": regions["support"]["attached_nodes"],
                    "input": ports["input"]["nodes"], "output": ports["output"]["nodes"]}.items()}
        compatible = bool(len(cells) and np.all(passive_void[mask]) and not overlaps["mechanism"]
                          and not any(overlaps[k] for k in ("support", "input", "output")))
        merged = np.union1d(old_fixed, dofs)
        symmetry = np.intersect1d(dofs, regions["background_symmetry"]["dofs"])
        gap = min(float(np.sqrt(np.sum((coords[batch, None]-coords[mechanism_nodes][None])**2, axis=2)).min())
                  for batch in np.array_split(nodes, max(1, (len(nodes)+63)//64)))
        candidates[name] = dict(shape=name, center_mm=center.tolist(), side_mm=side if name=="square" else None,
            radius_mm=radius if name=="circle" else None, cell_rule="closed analytic shape contains native cell centre; existing lower-half grid only",
            geometry_compatible=compatible, cells=cells.tolist(), nodes=nodes.tolist(), proposed_fixed_dofs=dofs.tolist(),
            cell_mask_sha256=sha256(mask.astype(np.uint8).tobytes()).hexdigest(),
            selected_cells=len(cells), incident_nodes=len(nodes), proposed_workpiece_fixed_dofs=len(dofs),
            original_fixed_dofs=len(old_fixed), proposed_merged_fixed_dofs=len(merged), proposed_free_dofs=2*len(coords)-len(merged),
            proposed_merged_fixed_dof_indices=merged.tolist(), non_passive_void_cells=int(np.count_nonzero(mask & ~passive_void)),
            source_solid_cell_overlap=int(np.count_nonzero(mask & solid)), node_overlaps=overlaps,
            original_fixed_dof_overlap=np.intersect1d(dofs, old_fixed).tolist(), symmetry_uy_dof_overlap=symmetry.tolist(),
            symmetry_uy_overlap_count=len(symmetry), minimum_raster_node_to_mechanism_node_gap_mm=gap,
            full_analytic_bounds_mm=[[62.,32.],[78.,48.]], actual_half_bounds_mm=[[62.,32.],[78.,40.]],
            source_geometry_modified=False, effective_HF_model_created=False)
        clock()
    if not candidates["square"]["geometry_compatible"]:
        raise ValueError("Square proposal conflicts with saved geometry; stop without repairing inputs")

    fig, axes = plt.subplots(2, 2, figsize=(14.4, 11.), constrained_layout=True)
    for column, name in enumerate(("square", "circle")):
        mask, case = masks[name], candidates[name]
        for row in range(2):
            ax = axes[row, column]
            ax.axhspan(40, 52, color="#e8edf1", alpha=.8)
            ax.add_collection(PolyCollection(coords[conn[passive_void]], facecolors="#fff4df", edgecolors="none"))
            ax.add_collection(PolyCollection(coords[conn[solid]], facecolors="#285574", edgecolors="#163549", linewidths=.18))
            if case["geometry_compatible"]:
                ax.add_collection(PolyCollection(coords[conn[mask]], facecolors="#eaa04b", edgecolors="#b56813", linewidths=.32, alpha=.85))
                if row == 1:
                    ax.scatter(*coords[case["nodes"]].T, s=3, color="#633908", zorder=4)
            shape = Rectangle((62,32),16,16,fill=False,ls="--",lw=1.4,color="#75430b") if name=="square" else Circle(center,8,fill=False,ls="--",lw=1.4,color="#75430b")
            ax.add_patch(shape)
            ax.axhline(40, color="#4d6273", ls="-.", lw=1.1)
            ax.plot(70,40,"+",ms=9,color="#8b4308")
            ax.annotate("2 mm initial gap", xy=(70,31), xytext=(60,26.6), fontsize=9,
                        arrowprops=dict(arrowstyle="-",color="#444"), bbox=dict(fc="white",ec="none",alpha=.8))
            ax.annotate("",xy=(70,32),xytext=(70,30),arrowprops=dict(arrowstyle="<->",color="#222",lw=1.2))
            ax.set_aspect("equal"); ax.set_xlabel("x [mm]"); ax.set_ylabel("y [mm]")
            ax.set_xlim((-5,89) if row==0 else (57,83)); ax.set_ylim((-2,52) if row==0 else (25,50))
            if row==0:
                ax.scatter(*coords[regions["support"]["attached_nodes"]].T, marker="^", s=30,color="#111",zorder=6)
                ax.scatter(*coords[ports["input"]["nodes"]].T,s=18,color="#c25427",zorder=6)
                ax.scatter(*coords[ports["output"]["nodes"]].T,s=28,marker="D",facecolors="none",edgecolors="#85479d",zorder=6)
                ax.annotate("",xy=(6,39),xytext=(0,39),arrowprops=dict(arrowstyle="->",color="#a33f1f",lw=1.5))
                ax.text(0,44,"+x input\nreference only",color="#a33f1f",fontsize=9)
                ax.annotate("",xy=(80,35),xytext=(80,29),arrowprops=dict(arrowstyle="->",color="#85479d",lw=1.5))
                ax.text(80,24,"+y output\nmeasurement",color="#85479d",fontsize=9)
                ax.text(4,48,"Above y=40: mirrored workpiece outline only",fontsize=9,color="#4d6273")
                ax.text(4,41,"y=40 symmetry line",fontsize=8,color="#4d6273",bbox=dict(fc="white",ec="none",alpha=.8))
                ax.set_title(("Square: side 16 mm" if name=="square" else "Circle alternative: radius 8 mm")+"; centre (70,40)")
            else:
                ax.set_title(f"Native h=0.5 mm: {case['selected_cells']} cells / {case['incident_nodes']} incident nodes")
                ax.text(58,49,"Solid: original mechanism | orange: candidate half-mask",fontsize=8)
                ax.text(58,25.5,f"Proposed fixed union {case['proposed_merged_fixed_dofs']}; symmetry uy overlap {case['symmetry_uy_overlap_count']}",fontsize=8)
            if not case["geometry_compatible"]:
                ax.text(58,36,"ANALYTIC OUTLINE ONLY — mask incompatible",color="#a00000",fontsize=10)
    fig.suptitle("Workpiece geometry/task-definition preview — no mechanics computed\nActual lower-half native geometry; dashed complete workpiece is a mirror schematic",fontsize=14)
    fig.savefig(png,dpi=180); plt.close(fig)
    after = {name: digest(ROOT/name) for name in INPUTS}
    source_after = {name: digest(ROOT/name) for name in sources}
    if after != before or source_after != source_before:
        raise ValueError("Saved inputs or frozen source39 changed during preview")
    clock()
    result = dict(schema_version="workpiece-geometry-preview-1.0",status="geometry_preview_complete",
        scope="Static candidate geometry only; not an effective HF model, mechanics, contact or clamping qualification",
        geometry_id=model_meta["source_geometry"]["geometry_id"], grid=model_meta["grid"], counts=regions["counts"],
        input_sha256_before=before,input_sha256_after=after,source39_sha256_before=source_before,source39_sha256_after=source_after,
        script_sha256=digest(Path(__file__)),README_sha256=digest(HERE/"README.md"),candidates=candidates,
        symmetry=dict(axis_y_mm=40.,modeled_region="original lower half only",upper_outline="mirror schematic only",quantities_doubled=False),
        original_ports=ports, directions_are_reference_only=True, arrow_forces_computed=False,
        media=dict(path=png.name,sha256=digest(png),pixels=[2592,1980]),
        budget=dict(scope="Independent geometry-preview budget; does not consume fine .025 or public recovery authorization",outer_seconds=120,invocations=1,elapsed_seconds=perf_counter()-STARTED),
        call_counts=dict(Project_constructions=0,material_assignments=0,force_calls=0,tangent_calls=0,solver_calls=0,HP_calls=0,LF_imports=0),
        physics_quantities=dict(displacement=None,contact_force=None,pressure=None,maximum_loading_displacement=None,unloading_endpoint=None),
        qualification=dict(scientific=False,workpiece_model=False,contact=False,clamping=False,H2=False,H3=False,mesh_convergence=False),
        limitations=["Circle is a cell-centre staircase mask, not an exact fitted circle; geometry and gap depend on rasterization.",
                     "Proposed fixed sets are index-set calculations only; no new TMCModel or Project was constructed.",
                     "Two-millimetre gap is an initial geometric definition, not a computed contact onset or safe stroke."])
    with metadata.open("x",encoding="utf-8") as stream:
        json.dump(result,stream,ensure_ascii=False,indent=2,allow_nan=False); stream.write("\n")
    print(json.dumps(dict(status=result["status"],elapsed_seconds=result["budget"]["elapsed_seconds"],media_sha256=result["media"]["sha256"],cases={k:{n:v for n,v in c.items() if n in ("geometry_compatible","selected_cells","incident_nodes","proposed_merged_fixed_dofs","proposed_free_dofs","symmetry_uy_overlap_count","minimum_raster_node_to_mechanism_node_gap_mm")} for k,c in candidates.items()})))


if __name__ == "__main__":
    main()
