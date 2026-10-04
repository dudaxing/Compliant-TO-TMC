"""Plot saved Q1-region/ray records only; no geometry or mechanics API imports."""
from __future__ import annotations

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


def file_sha(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="regions_measurements.json or its directory")
    parser.add_argument("--result", type=Path, required=True, help="Original saved result directory or result.json")
    parser.add_argument("--saved-view", type=Path, required=True, help="Original saved view_metadata.json declaring its CSV")
    parser.add_argument("--boundary-comparison", type=Path, help="Optional original unsigned JSON instead of its measurement snapshot")
    parser.add_argument("--output", type=Path, required=True, help="New exclusive view directory")
    parser.add_argument("--time-limit", type=float, default=120.0)
    parser.add_argument("--stop-file", type=Path)
    args = parser.parse_args()
    if not np.isfinite(args.time_limit) or args.time_limit <= 0:
        parser.error("--time-limit must be positive and finite")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    pins, file_roles = {}, {}

    def checkpoint():
        if perf_counter() - STARTED > args.time_limit:
            raise RuntimeError("Saved view time limit exceeded")
        if args.stop_file is not None and args.stop_file.exists():
            raise RuntimeError("Outer launcher requested stop")

    def bind(path, role, expected=None):
        path = path.resolve()
        value = file_sha(path)
        if expected is not None and value != expected:
            raise ValueError("Saved identity differs: " + role)
        pins[path] = value
        file_roles[role] = value
        return value

    def read(path, role, expected=None):
        bind(path, role, expected)
        return json.loads(path.read_text(encoding="utf-8"))

    def archive(path, role, declaration):
        bind(path, role, declaration["sha256"])
        with np.load(path, allow_pickle=False) as stored:
            return {name: stored[name].copy() for name in stored.files}

    checkpoint()
    measurement_file = args.input.resolve()
    if measurement_file.is_dir():
        measurement_file /= "regions_measurements.json"
    measurement_root = measurement_file.parent
    measurement = read(measurement_file, "measurement/regions_measurements.json")
    if (measurement["schema_version"] != "native-workpiece-region-path-1.0" or
            measurement["status"] != "pass" or not measurement["inputs_and_sources_unchanged"]):
        raise ValueError("Expected a complete passed saved region measurement")
    result_file = args.result.resolve()
    if result_file.is_dir():
        result_file /= "result.json"
    result_root = result_file.parent
    comparison_info = measurement["boundary_comparison"]
    if comparison_info is None:
        raise ValueError("This view requires the bound saved unsigned comparison")
    comparison_file = args.boundary_comparison.resolve() if args.boundary_comparison else measurement_root / comparison_info["path"]
    if comparison_file.is_dir():
        comparison_file /= "boundary_measurements.json"
    comparison = read(comparison_file, "comparison/boundary_measurements.json", comparison_info["sha256"])
    for role, expected in measurement["input_files_sha256"].items():
        if role.startswith("input/"):
            bind(result_root / role[6:], "result/" + role[6:], expected)
        elif role == "comparison/boundary_measurements.json":
            bind(comparison_file, role, expected)
        else:
            raise ValueError("Unexpected measurement input role: " + role)
    for role, declaration in measurement["sources"].items():
        bind(measurement_root / declaration["snapshot_path"], "measurement_source/" + role, declaration["sha256"])
    result = read(result_file, "result/result.json", measurement["input_files_sha256"]["input/result.json"])
    if measurement["task_sha256"] != result["task_sha256"] or comparison["task_sha256"] != result["task_sha256"]:
        raise ValueError("Geometry, old unsigned comparison and task identities differ")
    model_file = result_root / result["model"]["descriptor_path"]
    metadata = read(model_file, "result/" + result["model"]["descriptor_path"], result["model"]["descriptor_file_sha256"])
    model = archive(model_file.parent / metadata["arrays"]["path"], "result/" + result["model"]["arrays_path"], metadata["arrays"])
    if len(model) != 27:
        raise ValueError("Expected the original fixed-workpiece model's 27 fields")
    count = len(result["states"])
    if (count < 2 or count != result["accepted_states"] or result["status"] != "success" or
            result["path_completed"] is not True or result["unload_endpoint_reached"] is not True or
            result["targets_mm"][-1] != 0. or result["states"][-1]["d"] != 0. or
            measurement["declared_accepted_states"] != count or
            len(measurement["accepted_states"]) != count or len(comparison["accepted_states"]) != count or
            measurement["geometry_calls_started"] != count or measurement["geometry_calls_completed"] != count or
            any(row["geometry"]["geometry_valid"] is not True for row in measurement["accepted_states"])):
        raise ValueError("Expected a complete zero-return path and all actual saved measurement states")
    legacy_view_file = args.saved_view.resolve()
    legacy = read(legacy_view_file, "saved_view/view_metadata.json")
    if legacy["accepted_states"] != count or legacy["accepted_d_mm"] != [state["d"] for state in result["states"]]:
        raise ValueError("Original saved view path differs")
    if legacy["input_files_sha256"].get("stage/result/result.json") != file_sha(result_file):
        raise ValueError("Legacy view does not bind this original result")
    csv_names = [name for name in legacy["outputs_sha256"] if name.endswith(".csv")]
    if len(csv_names) != 1:
        raise ValueError("Expected one declared legacy numerical CSV")
    legacy_csv_file = legacy_view_file.parent / csv_names[0]
    bind(legacy_csv_file, "saved_view/" + csv_names[0], legacy["outputs_sha256"][csv_names[0]])
    with legacy_csv_file.open(encoding="utf-8", newline="") as stream:
        legacy_rows = list(csv.DictReader(stream))
    if len(legacy_rows) != count:
        raise ValueError("Legacy CSV accepted-state count differs")
    rows, coordinates = [], []
    for index, (record, measured, old, legacy_row) in enumerate(zip(result["states"], measurement["accepted_states"], comparison["accepted_states"], legacy_rows)):
        checkpoint()
        identity = dict(accepted_index=index, original_target_index=record["original_target_index"],
                        d_mm=record["d"], leg=record["leg"], state_sha256=record["state_sha256"])
        if any(measured[key] != value or old[key] != value for key, value in identity.items()):
            raise ValueError("Measurement accepted-state identity differs")
        if int(legacy_row["index"]) != index or legacy_row["leg"] != record["leg"] or float(legacy_row["d_mm"]) != record["d"]:
            raise ValueError("Legacy CSV accepted-state identity differs")
        state = archive(result_root / record["state"]["path"], "result/" + record["state"]["path"], record["state"])
        geometry = measured["geometry"]
        region = geometry["regions"]
        row = dict(identity, geometry_valid=True, minimum_J=record["minimum_J"],
                   raw_interior_overlap=region["raw_interior_overlap"], strict_interior_overlap=region["strict_interior_overlap"],
                   roundoff_ambiguous=region["roundoff_ambiguous"], candidate_cell_pairs=region["candidate_cell_pairs"],
                   closed_boundary_intersects=region["boundary_intersections"]["intersects"],
                   closed_boundary_near_touch=region["boundary_intersections"]["roundoff_near_touch"],
                   set_containment_tested=geometry["set_containment_tested"])
        for face_name in ("bottom", "left"):
            face = geometry["faces"][face_name]
            ray, no_hit = face["minimum_first_ray_hit_mm"], face["no_outward_ray_hit"]
            if no_hit != (ray is None):
                raise ValueError("Ray no-hit/null declarations differ")
            hit = face["closest_hit"]
            if (hit is None) != no_hit:
                raise ValueError("Ray closest-hit declaration differs")
            unsigned = old["geometry"]["groups"][face_name]["minimum_boundary_distance_mm"]
            proxy = float(legacy_row["clearance_" + face_name + "_mm"])
            if (proxy != record["workpiece"]["node_window_clearance_mm"][face_name] or
                    proxy != old["node_window_clearance_mm"][face_name]):
                raise ValueError("Legacy node-window proxy differs from cached state")
            row.update({face_name + "_ray_mm": ray, face_name + "_no_hit": no_hit,
                        face_name + "_corner_hit": None if hit is None else hit["corner_hit"],
                        face_name + "_near_corner_hit": None if hit is None else hit["near_corner_hit"],
                        face_name + "_interpretation": face["separation_interpretation"],
                        face_name + "_old_unsigned_mm": unsigned, face_name + "_node_window_proxy_mm": proxy})
        rows.append(row)
        # Coordinate display only; no edge extraction or distance measurement.
        coordinates.append(model["coordinates"] + state["lift"].reshape(-1, 2) + state["fluctuation"].reshape(-1, 2))
    peak = max(range(count), key=lambda i: rows[i]["d_mm"])
    last = count - 1
    if (rows[peak]["d_mm"] != max(result["targets_mm"]) or
            legacy["actual_peak_index"] != peak or legacy["last_accepted_index"] != last):
        raise ValueError("Actual declared peak or saved last index differs from the legacy view")
    checkpoint()
    fig, axes = plt.subplots(3, 2, figsize=(16, 15), constrained_layout=True)
    colors = dict(bottom="#7c3aed", left="#16a34a")
    conn, solid, body_cells = model["connectivity"], model["solid"], model["workpiece_cells"]
    cut = metadata["model_extent"]["symmetry_axis"]["offset_mm"]

    def structure(ax, index, zoom_face=None):
        actual, geometry = coordinates[index], measurement["accepted_states"][index]["geometry"]
        ax.add_collection(PolyCollection(model["coordinates"][conn[solid]], facecolors="#d1d5db", edgecolors="none", alpha=.5))
        ax.add_collection(PolyCollection(actual[conn[solid]], facecolors="#334155", edgecolors="#64748b", linewidths=.2))
        ax.add_collection(PolyCollection(actual[conn[body_cells]], facecolors="#d1d5db", edgecolors="#9ca3af", linewidths=.25))
        physical = np.asarray(geometry["physical_mechanism_edges"], dtype=int)
        ax.add_collection(LineCollection(actual[physical], colors="#0f172a", linewidths=.55))
        shown_points = []
        for name, face in geometry["faces"].items():
            a, b = np.asarray(face["face_start_mm"]), np.asarray(face["face_end_mm"])
            ax.plot([a[0], b[0]], [a[1], b[1]], color=colors[name], lw=1.8, label=name + " finite face")
            if zoom_face is None or zoom_face == name:
                hit = face["closest_hit"]
                shown_points.extend((a, b))
                if hit is not None:
                    p, q = np.asarray(hit["face_point_mm"]), np.asarray(hit["edge_point_mm"])
                    ax.annotate("", xy=q, xytext=p, arrowprops=dict(arrowstyle="->", color=colors[name], lw=1.8))
                    ax.scatter([p[0], q[0]], [p[1], q[1]], s=18, color=colors[name], zorder=5)
                    shown_points.extend((p, q))
        ax.axhline(cut, ls="--", lw=1., color="#dc2626", label="mathematical y=40 cut")
        if zoom_face is None:
            ax.set(xlim=(-1, 82), ylim=(-1, 42), title=f"{'Peak' if index == peak else 'Return'} index {index}: d={rows[index]['d_mm']:g} mm | actual ×1")
        else:
            points = np.asarray(shown_points)
            lower, upper = points.min(axis=0) - 1., points.max(axis=0) + 1.
            ax.set(xlim=(lower[0], upper[0]), ylim=(lower[1], upper[1]),
                   title=f"Peak {zoom_face} face zoom | same actual mm coordinates")
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlabel("x [mm]")
        ax.set_ylabel("y [mm]")
        ax.grid(alpha=.15)
        summary = "\n".join(f"{name} ray: {'no hit' if face['no_outward_ray_hit'] else format(face['minimum_first_ray_hit_mm'], '.6g') + ' mm'}"
                            for name, face in geometry["faces"].items())
        summary += f"\nraw/strict overlap: {rows[index]['raw_interior_overlap']}/{rows[index]['strict_interior_overlap']}"
        summary += f"\nroundoff ambiguous: {rows[index]['roundoff_ambiguous']}"
        ax.text(.015, .02 if zoom_face is None else .98, summary, transform=ax.transAxes,
                va="baseline" if zoom_face is None else "top", fontsize=9,
                bbox=dict(facecolor="white", alpha=.9, edgecolor="none"))

    structure(axes[0, 0], peak)
    structure(axes[0, 1], last)
    structure(axes[1, 0], peak, "bottom")
    structure(axes[1, 1], peak, "left")
    for ax, name in zip(axes[2], ("bottom", "left")):
        x = range(count)
        values = [np.nan if row[name + "_ray_mm"] is None else row[name + "_ray_mm"] for row in rows]
        ax.plot(x, values, "o-", color=colors[name], label="new finite-face first ray")
        ax.plot(x, [row[name + "_old_unsigned_mm"] for row in rows], "s--", color="#475569", label="old unsigned exterior distance")
        ax.plot(x, [row[name + "_node_window_proxy_mm"] for row in rows], "^:", color="#ea580c", label="source node-window proxy")
        ax.set_xticks(list(x), [f"{i}\n{row['d_mm']:g}" for i, row in enumerate(rows)])
        ax.set(title=name.capitalize() + ": distinct saved quantities", xlabel="Actual accepted index / input d [mm]", ylabel="Distance [mm]")
        ax.axvline(peak, color="#94a3b8", ls=":", lw=1.)
        ax.grid(alpha=.2)
        ax.legend(fontsize=8)
    axes[0, 0].legend(loc="upper left", fontsize=8)
    fig.suptitle("Saved Q1 regions and finite-face rays | no geometry remeasurement in this view", fontsize=16)
    no_hits = {name: [row["accepted_index"] for row in rows if row[name + "_no_hit"]] for name in ("bottom", "left")}
    fig.supxlabel("Cut closure is mathematical, not a contact face. Rays/unsigned distances/proxies are distinct; null rays are missing curve points.\n"
                  "No signed penetration, complete containment, self-overlap, contact pressure or clamping qualification. No force arrows. " + str(no_hits), fontsize=9)
    png = output / "native_region_path.png"
    fig.savefig(png, dpi=160)
    plt.close(fig)
    checkpoint()
    csv_file = output / "region_states.csv"
    with csv_file.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    own_sha = bind(Path(__file__), "render/source.py")
    frozen_source = output / "render_native_region_path_frozen.py"
    frozen_source.write_bytes(Path(__file__).read_bytes())
    if file_sha(frozen_source) != own_sha or any(file_sha(path) != value for path, value in pins.items()):
        raise ValueError("Inputs/source changed during saved rendering")
    if any(name == "hf_eval" or name.startswith("hf_eval.") for name in sys.modules):
        raise ValueError("Saved renderer must not import hf_eval APIs")
    checkpoint()
    view = dict(schema_version="native-workpiece-region-saved-view-1.0", status="rendered_saved_geometry",
        actual_peak_index=peak, return_index=last, accepted_states=rows, input_files_sha256=file_roles,
        inputs_and_sources_unchanged=True, source_sha256=own_sha,
        outputs_sha256={path.name: file_sha(path) for path in (png, csv_file, frozen_source)},
        display=dict(actual_coordinate_scale=1, normal_witness_arrows="Saved body-to-edge ray points; geometric direction, not force",
                     zoom="Same actual mm coordinates; axis viewport zoom only", symmetry_cut="Mathematical half-domain closure, not a contact face",
                     null_ray="None in JSON, empty CSV plus no_hit=True, missing curve point; never replaced by zero", interpolated_states=0),
        no_hit_indices=no_hits, elapsed_seconds=perf_counter() - STARTED, helper_seconds_limit=args.time_limit,
        new_calls={name: 0 for name in ("geometry_measurement", "force", "tangent", "consumer", "assembly", "solver", "HP")},
        call_count_basis="Only saved JSON/NPZ/CSV and Matplotlib; no hf_eval imports or API calls",
        identity_scope="Archive/file SHA and saved stateSHA/index checks; per-field and canonical state identities were verified by the bound measurement, not re-evaluated here",
        qualification=False, scope="New saved-region/face diagnostics displayed alongside bound legacy unsigned distances and node proxies; no new physics/contact qualification",
        legacy_view_scope="Only metadata path identity and its declared numerical CSV were bound; old PNG/sources/reference were not re-audited")
    with (output / "view.json").open("x", encoding="utf-8") as stream:
        json.dump(view, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
    print(json.dumps(dict(status=view["status"], accepted_states=count, actual_peak_index=peak, return_index=last, output=str(output))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
