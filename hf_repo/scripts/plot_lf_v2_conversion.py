"""Inspect saved LF v2 -> HF native geometry, without conversion or mechanics.

Arrows show declared reference directions only. All boundary lines describe
source regions; this viewer does not assert that an HF task has applied them.
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
from matplotlib.colors import ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np


ROOT = next(parent for parent in Path(__file__).resolve().parents
            if (parent / "hf_repo" / "src" / "hf_eval" / "data.py").is_file())
sys.path.insert(0, str(ROOT / "hf_repo" / "src"))
from hf_eval.data import ARRAY_NAMES, load_geometry
from hf_eval.regions import active_nodes, node_coordinates, port_vector, region_nodes


ALIASES = ("inverter_canonical", "gripper_canonical", "gripper_native_fine")
SOURCE_KEYS = {"solid": "solid", "design": "design_domain",
               "passive_solid": "passive_solid", "passive_void": "passive_void"}
COLORS = ["#e6e8eb", "#dcebf8", "#233d59", "#c87729"]
PORT_COLORS = {"input": "#137d99", "output": "#a83c79"}


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def source_tags(source):
    regions = source["regions_mm"]
    tags = {}
    for name, original in (("support", "support"), ("symmetry", "symmetry_solid"),
                           ("input", "input_port"), ("output", "output_port")):
        tag = regions[original]
        tags[name] = {"points_mm": tag["points"]}
        if "direction_reference" in tag:
            tags[name].update(direction=tag["direction_reference"], averaging=tag["averaging"])
        else:
            tags[name]["components"] = [{"ux": 0, "uy": 1}[c] for c in tag["components"]]
    return tags


def source_nodes(source, points):
    """Derive native nodes directly from LF physical endpoints, without snapping."""
    nx, ny = source["grid"]["native_mesh"]
    origin = np.asarray(source["grid"]["origin_mm"])
    cell = np.asarray(source["grid"]["cell_mm"])
    logical = (np.asarray(points) - origin) / cell
    rounded = np.rint(logical)
    require(np.allclose(logical, rounded, rtol=0., atol=64*np.finfo(float).eps*max(nx, ny)),
            "LF endpoint is off the native grid")
    start, stop = rounded.astype(int)
    varying = int(start[0] == stop[0])
    step = 1 if stop[varying] > start[varying] else -1
    positions = np.arange(start[varying], stop[varying] + step, step)
    if varying == 0:
        return start[1] * (nx + 1) + positions
    return positions * (nx + 1) + start[0]


def load_case(stage, item):
    alias = item["alias"]
    source_path = stage / "inputs" / alias / "design.json"
    array_path = source_path.with_name("design.npz")
    geometry_path = stage / "converted" / alias / "geometry.json"
    source = read_json(source_path)
    require(digest(source_path) == item["descriptor_sha256"], alias + ": source descriptor pin differs")
    require(digest(array_path) == item["NPZ_sha256"] == source["arrays"]["sha256"], alias + ": source NPZ pin differs")
    with np.load(array_path, allow_pickle=False) as archive:
        original = {name: archive[SOURCE_KEYS[name]].copy() for name in ARRAY_NAMES}
    geometry = load_geometry(geometry_path)
    provenance = geometry.metadata["provenance"]["lf_v2"]
    require(provenance["descriptor"] == source, alias + ": full original descriptor differs")
    require(provenance["descriptor_sha256"] == item["descriptor_sha256"]
            and provenance["array_file_sha256"] == item["NPZ_sha256"], alias + ": provenance hashes differ")
    require(provenance["geometry_id"] == source["geometry_id"]
            and provenance["design_id"] == source["design_id"], alias + ": source identities differ")
    bound_paths = [source_path, array_path, geometry_path, geometry_path.with_name("geometry.npz")]
    for field, source_file in (("descriptor_path", source_path), ("array_path", array_path)):
        saved = geometry_path.parent / provenance[field]
        require(saved.read_bytes() == source_file.read_bytes(), alias + ": saved source bytes differ")
        bound_paths.append(saved)
    nx, ny = source["grid"]["native_mesh"]
    require(geometry.grid["shape_yx"] == [ny, nx]
            and geometry.grid["cell_size_mm"] == source["grid"]["cell_mm"]
            and geometry.grid["extent_mm"] == source["grid"]["domain_mm"]
            and geometry.grid["origin_mm"] == source["grid"]["origin_mm"], alias + ": native grid differs")
    require(geometry.grid["axes"] == [[1., 0.], [0., 1.]]
            and geometry.grid["array_order"] == "C_yx_bottom_up", alias + ": orientation differs")
    require(geometry.metadata["thickness_mm"] == source["grid"]["thickness_mm"] == 20.
            and geometry.metadata["model_extent"] == {"kind": "lower_half",
                "symmetry_axis": {"normal": [0., 1.], "offset_mm": 40.}}, alias + ": model extent differs")
    require(geometry.metadata["case_family"] == source["case"] == item["case"], alias + ": family differs")
    tags = source_tags(source)
    require(geometry.metadata["region_tags"] == tags, alias + ": physical regions differ")
    processing = geometry.metadata["processing"]
    require(processing["background_boundary_applied"] is False
            and processing["support_attachment"] == "solid_incident"
            and processing["source_native_grid_preserved"] is True
            and processing["lossless_bool_to_uint8"] is True
            and processing["new_threshold_or_cleanup_applied"] is False, alias + ": conversion policy differs")
    counts, differences = {}, {}
    for name in ARRAY_NAMES:
        require(original[name].dtype == np.dtype(bool) and original[name].shape == (ny, nx), alias + ": LF mask contract differs")
        differences[name] = int(np.count_nonzero(original[name] != geometry.arrays[name]))
        counts[name] = int(original[name].sum())
        require(differences[name] == 0, alias + ": " + name + " was changed")
    coordinates = node_coordinates(geometry)
    incident = active_nodes(geometry)
    support = region_nodes(geometry, tags["support"])
    require(np.array_equal(support, source_nodes(source, tags["support"]["points_mm"])), alias + ": support nodes differ")
    ports = {}
    for name in ("input", "output"):
        _, nodes, weights = port_vector(geometry, tags[name])
        require(np.array_equal(nodes, source_nodes(source, tags[name]["points_mm"])), alias + ": port nodes differ")
        lengths = np.linalg.norm(np.diff(coordinates[nodes], axis=0), axis=1)
        expected = np.r_[lengths[0]/2, (lengths[:-1]+lengths[1:])/2, lengths[-1]/2] / lengths.sum()
        require(np.array_equal(weights, expected), alias + ": port averaging differs")
        ports[name] = {"nodes": nodes.tolist(), "coordinates_mm": coordinates[nodes].tolist(),
                       "weights": weights.tolist(), "direction_reference": tags[name]["direction"],
                       "solid_incident": incident[nodes].tolist()}
    return {"alias": alias, "source": source, "original": original, "geometry": geometry,
            "tags": tags, "coordinates": coordinates, "incident": incident, "support": support,
            "ports": ports, "record": {"alias": alias, "design_id": source["design_id"],
                "source_geometry_id": source["geometry_id"], "hf_geometry_id": geometry.geometry_id,
                "native_shape_yx": [ny, nx], "cell_size_mm": source["grid"]["cell_mm"],
                "extent_mm": source["grid"]["domain_mm"], "thickness_mm": source["grid"]["thickness_mm"],
                "mask_cell_counts": counts, "mask_changed_cells": differences, "ports": ports,
                "support_source_segment_nodes": support.tolist(),
                "support_solid_incident_nodes": support[incident[support]].tolist(),
                "support_nonincident_nodes": support[~incident[support]].tolist(),
                "background_source_metadata": source["regions_mm"]["symmetry_background"],
                "background_boundary_applied": False,
                "input_files_sha256": {str(path.relative_to(stage)): digest(path) for path in bound_paths}}}


def cell_image(arrays):
    codes = np.zeros(arrays["solid"].shape, dtype=np.uint8)
    codes[arrays["design"].astype(bool)] = 1
    codes[(arrays["design"] & arrays["solid"]).astype(bool)] = 2
    codes[arrays["passive_solid"].astype(bool)] = 3
    return codes


def draw_cells(ax, case, arrays):
    width, height = case["geometry"].grid["extent_mm"]
    ax.imshow(cell_image(arrays), origin="lower", interpolation="nearest", extent=(0, width, 0, height),
              cmap=ListedColormap(COLORS), vmin=-.5, vmax=3.5)
    ax.set_aspect("equal")
    ax.set_xlabel("x [mm]")
    ax.set_ylabel("y [mm]")


def draw_regions(ax, case):
    coords, incident, support = case["coordinates"], case["incident"], case["support"]
    for name in ("support", "symmetry"):
        xy = np.asarray(case["tags"][name]["points_mm"])
        ax.plot(xy[:, 0], xy[:, 1], color="#3b6550" if name == "support" else "#7262a3", lw=1.2)
    ax.scatter(*coords[support[incident[support]]].T, s=24, c="#218053", marker="s", zorder=5)
    ax.scatter(*coords[support[~incident[support]]].T, s=22, facecolors="none", edgecolors="#218053", marker="s", zorder=5)
    for name in ("input", "output"):
        port = case["ports"][name]
        xy = np.asarray(port["coordinates_mm"])
        color = PORT_COLORS[name]
        ax.scatter(xy[:, 0], xy[:, 1], s=20, color=color, zorder=6)
        center, direction = xy.mean(axis=0), np.asarray(port["direction_reference"])
        ax.annotate("", xy=center + 5*direction, xytext=center,
                    arrowprops=dict(arrowstyle="->", color=color, lw=1.6), zorder=7)
    background = case["source"]["regions_mm"]["symmetry_background"]
    if background is not None:
        start, stop = background["start_exclusive_mm"], background["end_inclusive_mm"]
        ax.plot([start, stop], [40., 40.], ls="--", lw=1.6, color="#ba5c39", clip_on=False)
        ax.scatter([start], [40.], facecolors="white", edgecolors="#ba5c39", s=20, zorder=8, clip_on=False)
        ax.scatter([stop], [40.], color="#ba5c39", s=20, zorder=8, clip_on=False)
        ax.text(70, 43, "(60,80] source only; unapplied", fontsize=8, ha="center", color="#9a4225")
    ax.set_xlim(-3, 88)
    ax.set_ylim(-2, 46)


def overview(cases, output):
    fig, axes = plt.subplots(3, 2, figsize=(14, 12.6), layout="constrained")
    fig.suptitle("LF v2 -> HF geometry: native cells copied unchanged\n"
                 "Reference directions only: arrows are neither force nor displacement; regions are source metadata", fontsize=13)
    for row, case in enumerate(cases):
        shape = case["geometry"].grid["shape_yx"]
        cell = case["geometry"].grid["cell_size_mm"]
        for col, (label, arrays) in enumerate((("Original LF masks", case["original"]), ("Converted HF masks", case["geometry"].arrays))):
            ax = axes[row, col]
            draw_cells(ax, case, arrays)
            draw_regions(ax, case)
            counts = case["record"]["mask_cell_counts"]
            numbers = "/".join(str(counts[n]) for n in ARRAY_NAMES)
            result = "all four changed-cell counts = 0" if col else "bottom-up source grid; no resampling"
            ax.set_title(f"{case['alias']} | {label}\nny x nx = {shape[0]} x {shape[1]}, h = {cell[0]:g} mm; t = 20 mm\n"
                         f"S/D/PS/PV cells: {numbers}; {result}", fontsize=9)
    legend = [Patch(color=c, label=t) for c, t in zip(COLORS,
              ("Passive void", "Design void", "Design solid", "Passive solid"))]
    legend += [Line2D([], [], color="#137d99", marker=">", label="Input reference +x"),
               Line2D([], [], color="#a83c79", marker=">", label="Output reference: inverter -x / gripper +y"),
               Line2D([], [], color="#218053", marker="s", ls="", label="Support solid-incident nodes"),
               Line2D([], [], color="#ba5c39", ls="--", label="Background source interval; unapplied")]
    fig.legend(handles=legend, loc="outside lower center", ncol=4, fontsize=9)
    fig.savefig(output / "lf_v2_native_masks.png", dpi=150)
    plt.close(fig)


def native_nodes(cases, output):
    fig, axes = plt.subplots(3, 3, figsize=(13, 12), layout="constrained")
    fig.suptitle("Native nodes in physical mm: source support attachment and normalized port weights\n"
                 "Geometry preparation only; no applied HF constraints, forces or deformation", fontsize=13)
    for row, case in enumerate(cases):
        coords, incident, support = case["coordinates"], case["incident"], case["support"]
        for col, name in enumerate(("support", "input", "output")):
            ax = axes[row, col]
            draw_cells(ax, case, case["geometry"].arrays)
            if name == "support":
                nodes, weights, color = support, None, "#218053"
                ax.scatter(*coords[nodes[incident[nodes]]].T, s=45, c=color, marker="s", zorder=4)
                ax.scatter(*coords[nodes[~incident[nodes]]].T, s=45, edgecolors=color, facecolors="white", marker="s", zorder=4)
                note = f"solid-incident: {int(incident[nodes].sum())}/{len(nodes)}\nfilled = incident; open = nonincident\nsource policy solid_incident"
            else:
                port = case["ports"][name]
                nodes, weights, color = np.asarray(port["nodes"]), port["weights"], PORT_COLORS[name]
                ax.scatter(*coords[nodes].T, s=40, c=color, zorder=4)
                for node, weight in zip(nodes, weights):
                    x, y = coords[node]
                    ax.annotate(f"w={weight:g}", (x, y), xytext=(8, 0), textcoords="offset points", fontsize=9, va="center", color=color)
                note = f"reference direction {port['direction_reference']}\nsum(w)={sum(weights):g}; {len(nodes)} native nodes\nno force/displacement arrow"
            xy = coords[nodes]
            h = case["geometry"].grid["cell_size_mm"][0]
            ax.set_xlim(xy[:, 0].min() - 1.2*h, xy[:, 0].max() + 4*h)
            ax.set_ylim(xy[:, 1].min() - .8*h, xy[:, 1].max() + .8*h)
            ax.set_title(f"{case['alias']} | {name}\n{note}", fontsize=9)
            ax.tick_params(labelsize=8)
            ax.grid(alpha=.16)
    fig.savefig(output / "lf_v2_native_nodes.png", dpi=150)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "lf_data_preparation" / "v2_adapter_001")
    parser.add_argument("--output", type=Path, required=True, help="New directory for static PNGs and bindings")
    args = parser.parse_args()
    stage = args.input.resolve()
    inventory_path = stage / "source_inventory.json"
    inventory = read_json(inventory_path)
    by_alias = {item["alias"]: item for item in inventory["selected"]}
    require(set(by_alias) == set(ALIASES), "Expected the three frozen source packages")
    cases = [load_case(stage, by_alias[alias]) for alias in ALIASES]
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    overview(cases, output)
    native_nodes(cases, output)
    frozen = output / "plot_lf_v2_conversion_frozen.py"
    frozen.write_bytes(Path(__file__).read_bytes())
    metadata = {"schema_version": "lf-v2-conversion-view-1.0", "input_root": str(stage),
                "source_inventory_sha256": digest(inventory_path), "cases": [case["record"] for case in cases],
                "scope": "Saved ordinary geometry only; no LF/HF mechanics, conversion, solver, deformation, force or HP calls",
                "reference_arrow_length_mm": 5., "arrow_meaning": "Declared reference direction only; not force/displacement",
                "geometry_scale": 1., "half_model_quantities_doubled": False,
                "media_sha256": {path.name: digest(path) for path in sorted(output.glob("*.png"))},
                "viewer_sha256": digest(frozen),
                "data_helpers_sha256": {name: digest(ROOT / "hf_repo" / "src" / "hf_eval" / name) for name in ("data.py", "regions.py")}}
    (output / "view_metadata.json").write_text(json.dumps(metadata, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "cases": len(cases), "all_four_masks_changed_cells": 0,
                      "mechanics_calls": 0, "media": list(metadata["media_sha256"])}))


if __name__ == "__main__":
    main()
