"""Plot saved native Q1 maps and source node candidates, without preparing them.

No material, applied constraints, force, deformation, project or solver is
created. Port vectors shown here are normalized reference directions.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Polygon
import numpy as np

ROOT = next(parent for parent in Path(__file__).resolve().parents
            if (parent / "hf_repo/src/hf_eval/data.py").is_file())
sys.path.insert(0, str(ROOT / "hf_repo/src"))
from hf_eval.data import ARRAY_NAMES, canonical_hash, load_geometry

ALIASES = ("inverter_canonical", "gripper_canonical", "gripper_native_fine")
COLORS = ["#e6e8eb", "#dcebf8", "#233d59", "#c87729"]
PORT_COLORS = {"input": "#137d99", "output": "#a83c79"}


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_saved(stage, alias):
    path = stage / "mapped" / alias / "map.json"
    metadata = read_json(path)
    require(metadata["schema_version"] == "hf-native-geometry-map-1.0", alias + ": schema differs")
    require(canonical_hash({k: v for k, v in metadata.items() if k != "descriptor_sha256"})
            == metadata["descriptor_sha256"], alias + ": semantic map hash differs")
    npz = path.parent / metadata["arrays"]["path"]
    require(digest(npz) == metadata["arrays"]["sha256"], alias + ": map NPZ hash differs")
    with np.load(npz, allow_pickle=False) as archive:
        require(set(archive.files) == set(metadata["arrays"]["fields"]), alias + ": array fields differ")
        arrays = {name: archive[name].copy() for name in archive.files}
    for name, values in arrays.items():
        field = dict(dtype=values.dtype.name, shape=list(values.shape), sha256=sha256(values.tobytes(order="C")).hexdigest())
        require(field == metadata["arrays"]["fields"][name], alias + ": " + name + " declaration differs")
    snapshot = metadata["source_geometry_snapshot"]
    source_path, source_npz = (path.parent / snapshot[k] for k in ("descriptor_path", "array_path"))
    require(digest(source_path) == metadata["source_geometry_file_sha256"]
            and digest(source_npz) == metadata["source_geometry_npz_sha256"], alias + ": source snapshot hashes differ")
    geometry = load_geometry(source_path)
    require(geometry.metadata == metadata["geometry_metadata"]
            and geometry.geometry_id == metadata["source_geometry_id"]
            and geometry.metadata["descriptor_sha256"] == metadata["source_geometry_descriptor_sha256"], alias + ": source identity differs")
    for name in ARRAY_NAMES:
        require(np.array_equal(arrays[name], geometry.arrays[name]), alias + ": native mask changed")
    require(metadata["constraints_applied"] is False and metadata["material_assigned"] is False
            and metadata["task_created"] is False and metadata["analysis_grid_policy"] == "not_selected", alias + ": preparation scope differs")
    coordinates, connectivity = arrays["coordinates_mm"], arrays["connectivity"]
    require(metadata["element_node_order"] == ["BL", "BR", "TR", "TL"], alias + ": local node order differs")
    xy = coordinates[connectivity]
    areas = .5*np.sum(xy[:, :, 0]*np.roll(xy[:, :, 1], -1, axis=1) - xy[:, :, 1]*np.roll(xy[:, :, 0], -1, axis=1), axis=1)
    require(np.all(areas > 0), alias + ": element area is not positive")
    dx, dy = metadata["grid"]["cell_size_mm"]
    require(np.allclose(areas, dx*dy, rtol=2e-14, atol=0.), alias + ": native cell areas differ")
    incident = arrays["solid_incident"].astype(bool)
    for name in ("support", "symmetry", "background_source"):
        require(np.array_equal(arrays[name+"_solid_nodes"], arrays[name+"_nodes"][incident[arrays[name+"_nodes"]]]), alias + ": incident subset differs")
    ports = {}
    for name in ("input", "output"):
        nodes, weights, vector = (arrays[name+suffix] for suffix in ("_nodes", "_weights", "_vector"))
        direction = np.array(geometry.metadata["region_tags"][name]["direction"])
        expected = np.zeros_like(vector).reshape(-1, 2)
        expected[nodes] = weights[:, None]*direction
        require(np.array_equal(vector, expected.ravel()) and np.isclose(weights.sum(), 1., rtol=0., atol=4e-15), alias + ": port vector differs")
        ports[name] = dict(nodes=nodes.tolist(), coordinates_mm=coordinates[nodes].tolist(), weights=weights.tolist(),
                           direction_reference=direction.tolist(), nonzero_dofs=np.flatnonzero(vector).tolist(),
                           nonzero_components=vector[np.flatnonzero(vector)].tolist())
    bindings = {p.relative_to(stage).as_posix(): digest(p) for p in (path, npz, source_path, source_npz)}
    record = dict(alias=alias, source_geometry_id=geometry.geometry_id, source_geometry_file_sha256=metadata["source_geometry_file_sha256"],
                  source_geometry_descriptor_sha256=metadata["source_geometry_descriptor_sha256"], counts=metadata["counts"],
                  grid=metadata["grid"], element_node_order=metadata["element_node_order"],
                  min_signed_area_mm2=float(areas.min()), max_signed_area_mm2=float(areas.max()), ports=ports,
                  support_candidate_nodes=arrays["support_nodes"].tolist(), support_solid_incident_nodes=arrays["support_solid_nodes"].tolist(),
                  entity_symmetry_candidate_nodes=arrays["symmetry_nodes"].tolist(), entity_symmetry_solid_incident_nodes=arrays["symmetry_solid_nodes"].tolist(),
                  background_source=metadata["background_source"], background_source_nodes=arrays["background_source_nodes"].tolist(),
                  background_source_solid_nodes=arrays["background_source_solid_nodes"].tolist(), input_files_sha256=bindings)
    return dict(alias=alias, arrays=arrays, metadata=metadata, geometry=geometry, areas=areas, record=record)


def draw_cells(ax, case):
    arrays, grid = case["arrays"], case["metadata"]["grid"]
    codes = np.zeros(arrays["solid"].shape, dtype=np.uint8)
    codes[arrays["design"].astype(bool)] = 1
    codes[(arrays["solid"] & arrays["design"]).astype(bool)] = 2
    codes[arrays["passive_solid"].astype(bool)] = 3
    x, y = grid["origin_mm"]
    width, height = grid["extent_mm"]
    ax.imshow(codes, origin="lower", extent=(x, x+width, y, y+height), interpolation="nearest",
              cmap=ListedColormap(COLORS), vmin=-.5, vmax=3.5)
    ax.set_aspect("equal")
    ax.set_xlabel("x [mm]")
    ax.set_ylabel("y [mm]")


def draw_candidates(ax, case):
    arrays = case["arrays"]
    coordinates, incident = arrays["coordinates_mm"], arrays["solid_incident"].astype(bool)
    for name, color in (("support", "#218053"), ("symmetry", "#7262a3")):
        nodes = arrays[name+"_nodes"]
        xy = coordinates[nodes]
        ax.plot(xy[:, 0], xy[:, 1], color=color, lw=1)
        if name == "support":
            ax.scatter(*coordinates[nodes[incident[nodes]]].T, s=22, marker="s", color=color, zorder=5)
            ax.scatter(*coordinates[nodes[~incident[nodes]]].T, s=20, marker="s", facecolors="white", edgecolors=color, zorder=5)
        else:
            ax.scatter(*coordinates[arrays[name+"_solid_nodes"]].T, s=6, color=color, zorder=3)
            ax.scatter(*coordinates[nodes[~incident[nodes]]].T, s=6, facecolors="white", edgecolors=color, linewidths=.6, zorder=3)
    for name in ("input", "output"):
        xy = coordinates[arrays[name+"_nodes"]]
        direction = np.array(case["record"]["ports"][name]["direction_reference"])
        ax.scatter(xy[:, 0], xy[:, 1], color=PORT_COLORS[name], s=20, zorder=6)
        ax.annotate("", xy=xy.mean(axis=0)+5*direction, xytext=xy.mean(axis=0),
                    arrowprops=dict(arrowstyle="->", color=PORT_COLORS[name], lw=1.5))
    background = case["metadata"]["background_source"]
    if background is not None:
        start, stop = background["start_exclusive_mm"], background["end_inclusive_mm"]
        value = background["line"]["value_mm"]
        ax.plot([start, stop], [value, value], ls="--", lw=1.5, color="#ba5c39")
        nodes = arrays["background_source_nodes"]
        ax.scatter(*coordinates[arrays["background_source_solid_nodes"]].T, s=6, color="#ba5c39", zorder=3)
        ax.scatter(*coordinates[nodes[~incident[nodes]]].T, s=6, facecolors="white", edgecolors="#ba5c39", linewidths=.6, zorder=3)
        ax.text((start+stop)/2, value+3, "(60,80] source candidates; unapplied", ha="center", fontsize=8, color="#9a4225")


def draw_q1_patch(ax, case):
    arrays, grid = case["arrays"], case["metadata"]["grid"]
    ny, nx = grid["shape_yx"]
    dx, dy = grid["cell_size_mm"]
    x0, y0 = grid["origin_mm"]
    input_xy = arrays["coordinates_mm"][arrays["input_nodes"]]
    i = min(nx-1, max(0, round((input_xy[:, 0].min()-x0)/dx)))
    j = min(ny-1, max(0, round((input_xy[:, 1].min()-y0)/dy)))
    selected = j*nx+i
    cells = [jj*nx+ii for jj in range(j, min(ny, j+2)) for ii in range(i, min(nx, i+2))]
    xy = arrays["coordinates_mm"][arrays["connectivity"][cells]]
    edges = [polygon[[k, (k+1)%4]] for polygon in xy for k in range(4)]
    ax.add_collection(LineCollection(edges, color="#788ca3", linewidth=.9))
    polygon = arrays["coordinates_mm"][arrays["connectivity"][selected]]
    ax.add_patch(Polygon(polygon, facecolor="#f3d791", alpha=.55, edgecolor="#333333", lw=1.5))
    local = case["metadata"]["element_node_order"]
    for label, node, point, offset in zip(local, arrays["connectivity"][selected], polygon, ((-5,-10),(5,-10),(5,5),(-5,5))):
        ax.scatter(*point, s=28, color="#243d59", zorder=5)
        ax.annotate(f"{label}: n{node}", point, xytext=offset, textcoords="offset points", fontsize=9,
                    ha="right" if offset[0]<0 else "left", va="top" if offset[1]<0 else "bottom")
    for element, polygon_xy in zip(cells, xy):
        ax.text(*polygon_xy.mean(axis=0), f"e{element}", fontsize=8, ha="center", va="center")
    bounds = xy.reshape(-1, 2)
    ax.set_xlim(bounds[:, 0].min()-.9*dx, bounds[:, 0].max()+.9*dx)
    ax.set_ylim(bounds[:, 1].min()-.9*dy, bounds[:, 1].max()+.9*dy)
    ax.set_aspect("equal")
    ax.set_xlabel("x [mm]")
    ax.set_ylabel("y [mm]")
    ax.set_title(f"Coordinate zoom; e{selected}, BL -> BR -> TR -> TL\n"
                 f"signed area = {case['areas'][selected]:g} mm^2 > 0; h = ({dx:g}, {dy:g}) mm", fontsize=9)
    case["record"]["displayed_Q1_element"] = dict(element=int(selected), nodes=arrays["connectivity"][selected].tolist(),
                                                   coordinates_mm=polygon.tolist(), signed_area_mm2=float(case["areas"][selected]))


def plot_maps(cases, output):
    fig, axes = plt.subplots(3, 2, figsize=(14, 12.5), layout="constrained")
    fig.suptitle("Saved native Q1 geometry maps: unchanged mm coordinates and counterclockwise connectivity\n"
                 "Reference directions and source node candidates only; no force, deformation or applied fixed DOFs", fontsize=13)
    for row, case in enumerate(cases):
        ax = axes[row, 0]
        draw_cells(ax, case)
        draw_candidates(ax, case)
        counts = case["metadata"]["counts"]
        ax.set_title(f"{case['alias']} | {counts['elements']} elements, {counts['nodes']} nodes, {counts['dofs']} DOFs\n"
                     "Full original geometry; analysis-grid policy not selected", fontsize=10)
        ax.set_xlim(-3, 88)
        ax.set_ylim(-2, 46)
        draw_q1_patch(axes[row, 1], case)
    legend = [Patch(color=color, label=label) for color, label in zip(COLORS, ("Passive void", "Design void", "Design solid", "Passive solid"))]
    legend += [Line2D([], [], ls="", marker="s", color="#218053", label="Support source candidates"),
               Line2D([], [], color="#7262a3", label="Entity symmetry source segment"),
               Line2D([], [], ls="--", color="#ba5c39", label="Background source; unapplied"),
               Line2D([], [], ls="", marker="o", color="#666666", label="Source nodes: filled = solid-incident"),
               Line2D([], [], ls="", marker="o", markerfacecolor="white", color="#666666", label="Source nodes: open = nonincident")]
    fig.legend(handles=legend, loc="outside lower center", ncol=3, fontsize=9)
    fig.savefig(output / "native_q1_geometry.png", dpi=150)
    plt.close(fig)


def plot_ports(cases, output):
    fig, axes = plt.subplots(3, 3, figsize=(13, 12), layout="constrained")
    fig.suptitle("Source support candidates and normalized reference port vectors on native Q1 nodes\n"
                 "Filled support = solid-incident; open = nonincident. No constraints, force or displacement applied", fontsize=13)
    for row, case in enumerate(cases):
        arrays, grid = case["arrays"], case["metadata"]["grid"]
        coordinates, incident = arrays["coordinates_mm"], arrays["solid_incident"].astype(bool)
        dx, dy = grid["cell_size_mm"]
        for col, name in enumerate(("support", "input", "output")):
            ax = axes[row, col]
            draw_cells(ax, case)
            nodes = arrays[name+"_nodes"]
            xy = coordinates[nodes]
            if name == "support":
                ax.scatter(*coordinates[nodes[incident[nodes]]].T, s=40, marker="s", color="#218053", zorder=5)
                ax.scatter(*coordinates[nodes[~incident[nodes]]].T, s=40, marker="s", facecolors="white", edgecolors="#218053", zorder=5)
                title = f"{len(arrays['support_solid_nodes'])}/{len(nodes)} solid-incident\nSource candidates only; no applied fixed DOFs"
            else:
                color = PORT_COLORS[name]
                ax.scatter(xy[:, 0], xy[:, 1], s=35, color=color, zorder=5)
                direction = np.array(case["record"]["ports"][name]["direction_reference"])
                components = "ux" if direction[0] else "uy"
                for node, point, weight in zip(nodes, xy, arrays[name+"_weights"]):
                    value = case["arrays"][name+"_vector"][2*node+(0 if direction[0] else 1)]
                    ax.annotate(f"w={weight:g}; b_{components}={value:g}", point, xytext=(8, 0),
                                textcoords="offset points", fontsize=8, color=color, va="center")
                title = f"{len(nodes)} nodes; sum(w)=1; reference {direction.tolist()}\nNonzero b components, neither force nor displacement"
            ax.set_xlim(xy[:, 0].min()-1.2*dx, xy[:, 0].max()+5.5*dx)
            ax.set_ylim(xy[:, 1].min()-.8*dy, xy[:, 1].max()+.8*dy)
            ax.set_title(f"{case['alias']} | {name}\n{title}", fontsize=9)
            ax.tick_params(labelsize=8)
            ax.grid(alpha=.15)
    fig.savefig(output / "native_q1_ports_candidates.png", dpi=150)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "lf_data_preparation/native_q1_001")
    parser.add_argument("--output", type=Path, required=True, help="New output directory")
    args = parser.parse_args()
    stage, output = args.input.resolve(), args.output.resolve()
    cases = [load_saved(stage, alias) for alias in ALIASES]
    output.mkdir(parents=True, exist_ok=False)
    plot_maps(cases, output)
    plot_ports(cases, output)
    frozen = output / "plot_native_geometry_map_frozen.py"
    frozen.write_bytes(Path(__file__).read_bytes())
    metadata = dict(schema_version="hf-native-Q1-map-view-1.0", input_layout="mapped/<alias>/map.json", cases=[case["record"] for case in cases],
                    scope="Saved geometry, Q1 connectivity and source reference vectors only; no prepare/project/TMC/material/task/force/HP/solver calls",
                    geometry_scale=1., reference_arrow_length_mm=5., arrows_meaning="reference direction only, not force or displacement",
                    constraints_applied=False, material_assigned=False, task_created=False, analysis_grid_policy="not_selected",
                    half_model_quantities_doubled=False, viewer_sha256=digest(frozen), data_helper_sha256=digest(ROOT / "hf_repo/src/hf_eval/data.py"),
                    media_sha256={path.name: digest(path) for path in sorted(output.glob("*.png"))})
    (output / "view_metadata.json").write_text(json.dumps(metadata, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps(dict(output=str(output), cases=3, all_element_signed_areas_positive=True, mechanics_calls=0)))


if __name__ == "__main__":
    main()
