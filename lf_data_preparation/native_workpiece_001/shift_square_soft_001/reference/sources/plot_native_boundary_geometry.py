"""Display already saved Q1 boundary measurements on the original actual states.

No boundary extraction, distance calculation, mechanics or reference is called.
Unsigned edge distance is not signed penetration, pressure or contact proof.
"""
from __future__ import annotations

import argparse
import csv
from hashlib import sha256
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection, PolyCollection
from matplotlib.lines import Line2D
import numpy as np

GROUP_COLORS = dict(all_exposed="#777777", bottom="#176a80", left="#c26924")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def load_saved(measurement_file, result_directory):
    measured = json.loads(measurement_file.read_text(encoding="utf-8"))
    require(measured["schema_version"] == "native-workpiece-boundary-path-1.0"
            and measured["input_files_unchanged"] is True
            and all(measured[key] == 0 for key in ("force_calls", "tangent_calls", "solver_calls", "HP_calls")), "Saved measurement scope differs")
    declared = {name.replace("\\", "/"): pin for name, pin in measured["input_files_sha256"].items()}
    result_names = [name for name in declared if name.endswith("/result.json")]
    require(len(result_names) == 1, "Measurement must bind one original result.json")
    original_prefix = result_names[0][:-len("result.json")]
    repo = next(p for p in Path(__file__).resolve().parents if (p/"hf_repo").is_dir())
    pins, remapped = {}, {}
    for original, expected in declared.items():
        if original.startswith(original_prefix):
            relative = original[len(original_prefix):]
            path, role = result_directory/relative, "result/"+relative
        else:
            require("/hf_repo/" in original, "Unsupported measurement source suffix")
            relative = "hf_repo/"+original.split("/hf_repo/", 1)[1]
            path, role = repo/relative, relative
        path = path.resolve()
        require(digest(path) == expected, "Mapped measurement input SHA differs: "+role)
        pins[path] = expected
        remapped[original] = dict(local_role=role, sha256=expected)
    pins[measurement_file.resolve()] = digest(measurement_file)

    def read(path):
        path = path.resolve()
        require(path in pins and digest(path) == pins[path], "Read JSON is not bound by the measurement: "+path.name)
        return json.loads(path.read_text(encoding="utf-8"))

    def archive(path, declaration):
        path = path.resolve()
        require(path in pins and digest(path) == pins[path] == declaration["sha256"], "Read NPZ is not bound by the measurement: "+path.name)
        with np.load(path, allow_pickle=False) as saved:
            arrays = {name: saved[name].copy() for name in saved.files}
        require(set(arrays) == set(declaration["fields"]), "Saved NPZ fields differ")
        for name, array in arrays.items():
            require(dict(dtype=array.dtype.name, shape=list(array.shape), sha256=sha256(array.tobytes(order="C")).hexdigest())
                    == declaration["fields"][name], "Saved array field differs: "+name)
        return arrays

    result = read(result_directory/"result.json")
    model_file = result_directory/result["model"]["descriptor_path"]
    metadata = read(model_file)
    model = archive(model_file.parent/metadata["arrays"]["path"], metadata["arrays"])
    require(digest(model_file) == result["model"]["descriptor_file_sha256"]
            and metadata["descriptor_sha256"] == result["model"]["descriptor_sha256"]
            and metadata["arrays"]["sha256"] == result["model"]["arrays_sha256"]
            and measured["task_sha256"] == result["task_sha256"] == metadata["task_sha256"], "Saved measurement/model/result identity differs")
    require(metadata["task"]["workpiece"]["shape"] == "square"
            and metadata["element_node_order"] == ["BL", "BR", "TR", "TL"], "Viewer requires the saved native square Q1 case")
    rows, states = measured["accepted_states"], []
    require(len(rows) == len(result["states"]) == result["accepted_states"] and len(rows) > 0, "Accepted measurement coverage differs")
    for index, (row, record) in enumerate(zip(rows, result["states"])):
        require(row["accepted_index"] == index and row["d_mm"] == record["d"] and row["leg"] == record["leg"]
                and row["original_target_index"] == record["original_target_index"] and row["state_sha256"] == record["state_sha256"]
                and row["node_window_clearance_mm"] == record["workpiece"]["node_window_clearance_mm"], "Measurement chronology or state identity differs")
        state = archive(result_directory/record["state"]["path"], record["state"])
        require(set(state) == {"lift", "fluctuation"}, "Saved split state fields differ")
        identity = sha256(b"split_displacement_v1"+np.asarray(len(state["lift"]), dtype="<i8").tobytes()
                          +state["lift"].astype("<f8", copy=False).tobytes()+state["fluctuation"].astype("<f8", copy=False).tobytes()).hexdigest()
        require(identity == row["state_sha256"], "Saved split state byte identity differs")
        geometry = row["geometry"]
        require(geometry["schema_version"] == "native-workpiece-boundary-geometry-1.0" and geometry["shape"] == "square"
                and geometry["containment_tested"] is False
                and set(geometry["groups"]) == {"all_exposed", "bottom", "left"}
                and geometry["symmetry_cut_excluded"] == dict(axis="y", reference_offset_mm=metadata["model_extent"]["symmetry_axis"]["offset_mm"], applies_to="both boundaries")
                and all(geometry[key] == 0 for key in ("force_calls", "tangent_calls", "solver_calls", "HP_calls"))
                and geometry["contact_pressure_qualification"] is geometry["contact_or_clamping_qualification"] is False,
                "Boundary geometry/scope differs")
        states.append(state)
    pins[Path(__file__).resolve()] = digest(Path(__file__))
    return measured, model, metadata, result, states, pins, remapped


def csv_rows(measured):
    rows = []
    for row in measured["accepted_states"]:
        saved = dict(accepted_index=row["accepted_index"], original_target_index=row["original_target_index"],
            leg=row["leg"], d_mm=row["d_mm"], state_sha256=row["state_sha256"],
            node_window_bottom_proxy_mm=row["node_window_clearance_mm"]["bottom"],
            node_window_left_proxy_mm=row["node_window_clearance_mm"]["left"], containment_tested=False)
        for name, group in row["geometry"]["groups"].items():
            saved.update({name+"_unsigned_distance_mm": group["minimum_boundary_distance_mm"],
                name+"_intersects": group["intersects"], name+"_roundoff_near_touch": group["roundoff_near_touch"],
                name+"_roundoff_tolerance_mm": group["roundoff_tolerance_mm"], name+"_intersection_pairs": len(group["intersections"])})
            pair = group["closest_pair"]
            for body in ("mechanism", "workpiece"):
                for component, axis in enumerate("xy"):
                    saved[f"{name}_closest_{body}_{axis}_mm"] = pair[body+"_point_mm"][component] if pair else None
        rows.append(saved)
    return rows


def render(measured, model, result, states, output, xlim, ylim):
    rows = measured["accepted_states"]
    figure = plt.figure(figsize=(6.*len(rows), 10.5), layout="constrained")
    grid = figure.add_gridspec(3, len(rows), height_ratios=[1., .16, .65])
    coords, conn, solid = (model[name] for name in ("coordinates", "connectivity", "solid"))
    for index, (row, state) in enumerate(zip(rows, states)):
        ax = figure.add_subplot(grid[0, index])
        # Display coordinates only; no boundary extraction or distance measurement.
        actual = coords+state["lift"].reshape(-1, 2)+state["fluctuation"].reshape(-1, 2)
        geometry = row["geometry"]
        ax.add_collection(PolyCollection(actual[conn[solid]], facecolors="#d8e7ef", edgecolors="none"))
        ax.add_collection(PolyCollection(actual[conn[model["workpiece_cells"]]], facecolors="#cccccc", edgecolors="none"))
        for name, color, width in (("mechanism_edges", "#174e75", 1.), ("workpiece_edges", "#555555", 1.5)):
            pairs = np.asarray(geometry[name], dtype=int).reshape(-1, 2)
            ax.add_collection(LineCollection(actual[pairs], colors=color, linewidths=width))
        labels = []
        for name in ("bottom", "left"):
            group, color = geometry["groups"][name], GROUP_COLORS[name]
            pair = group["closest_pair"]
            if pair is not None:
                points = np.asarray([pair["mechanism_point_mm"], pair["workpiece_point_mm"]])
                ax.plot(*points.T, "--", color=color, linewidth=1.4)
                ax.scatter(*points[0], color=color, marker="o", s=36, zorder=6)
                ax.scatter(*points[1], color=color, marker="s", s=36, zorder=6)
            distance = group["minimum_boundary_distance_mm"]
            labels.append(f"{name} unsigned nearest: {distance:.9g} mm" if distance is not None else name+": no saved pair")
            labels.append(f"  intersection={group['intersects']}; roundoff near-touch={group['roundoff_near_touch']}")
        labels.append("Left-edge closest pair may use its lower corner; NOT an x-normal gap.")
        ax.text(.02, .02, "\n".join(labels), transform=ax.transAxes, fontsize=8, va="bottom",
                bbox=dict(facecolor="white", edgecolor="none", alpha=.96))
        ax.set(xlim=xlim, ylim=ylim, aspect="equal", xlabel="actual x [mm]", ylabel="actual y [mm]",
               title=f"Accepted {index}: {row['leg']}; d={row['d_mm']:g} mm\nActual deformation ×1; original target index {row['original_target_index']}")
    handles = [Line2D([], [], color="#174e75", label="saved actual Q1 mechanism outer edges"),
               Line2D([], [], color="#555555", label="saved fixed-workpiece outer edges")]
    handles += [Line2D([], [], color=GROUP_COLORS[name], linestyle="--", label=name+" saved nearest-point connector") for name in ("bottom", "left")]
    handles += [Line2D([], [], color="black", marker=marker, linestyle="none", label=label)
                for marker, label in (("o", "mechanism closest point"), ("s", "workpiece closest point"))]
    legend = figure.add_subplot(grid[1, :]); legend.axis("off"); legend.legend(handles=handles, loc="center", ncol=3, fontsize=8)
    lower = grid[2, :].subgridspec(1, 2, width_ratios=[1.3, 1.])
    boundary, proxy = [figure.add_subplot(lower[0, i]) for i in range(2)]
    order = np.arange(len(rows))
    for name in ("all_exposed", "bottom", "left"):
        values = [row["geometry"]["groups"][name]["minimum_boundary_distance_mm"] for row in rows]
        boundary.plot(order, [np.nan if x is None else x for x in values], "o-", color=GROUP_COLORS[name], label=name)
    for name in ("bottom", "left"):
        values = [row["node_window_clearance_mm"][name] for row in rows]
        proxy.plot(order, [np.nan if x is None else x for x in values], "o--", color=GROUP_COLORS[name], label=name+" node-window proxy")
    labels = [f"{row['accepted_index']}: {row['leg']}\nd={row['d_mm']:g} mm" for row in rows]
    for ax in (boundary, proxy):
        ax.set_xticks(order, labels); ax.set(xlabel="actual accepted chronology", ylabel="distance / proxy [mm]")
        ax.grid(alpha=.25); ax.legend(fontsize=8)
    boundary.set_title("Unsigned Q1 distance to named edge SETS; left may be a corner pair")
    proxy.set_title("Separate source NODE-WINDOW proxies; not boundary distance")
    figure.suptitle(f"Saved native square-workpiece boundary geometry — production {result['status']}\n"
        "Actual ×1 only; both y=40 mm symmetry-cut edges excluded. Points/lines use saved measurements.\n"
        "Containment not tested; no pressure/contact/clamping proof. Curves connect real samples only.", fontsize=11)
    figure.savefig(output/"native_boundary_geometry.png", dpi=170); plt.close(figure)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Saved boundary_measurements.json or its directory")
    parser.add_argument("--result", type=Path, required=True, help="SHA-bound saved result directory in this clone")
    parser.add_argument("--output", type=Path, required=True, help="New exclusive view directory")
    parser.add_argument("--xlim", type=float, nargs=2, default=[54., 80.])
    parser.add_argument("--ylim", type=float, nargs=2, default=[24., 41.])
    args = parser.parse_args()
    require(args.xlim[0] < args.xlim[1] and args.ylim[0] < args.ylim[1], "View bounds must increase")
    measurement_file = args.input if args.input.is_file() else args.input/"boundary_measurements.json"
    measured, model, metadata, result, states, pins, remapped = load_saved(measurement_file.resolve(), args.result.resolve())
    rows = csv_rows(measured)
    output = args.output.resolve(); output.mkdir(parents=True, exist_ok=False)
    render(measured, model, result, states, output, args.xlim, args.ylim)
    with (output/"boundary_numeric_states.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    frozen = output/"plot_native_boundary_geometry_frozen.py"; frozen.write_bytes(Path(__file__).read_bytes())
    require(all(digest(path) == pin for path, pin in pins.items()), "Bound saved files/source changed during display")
    report = dict(schema_version="native-workpiece-boundary-view-1.0", production_status=result["status"],
        task_sha256=result["task_sha256"], measurement_sha256=digest(measurement_file), accepted_states=len(rows), numerical_states=rows,
        view=dict(deformation_scale=1., xlim_mm=args.xlim, ylim_mm=args.ylim, interpolation_states=0,
            closest_points="Saved group closest_pair coordinates; no nearest-point recomputation", symmetry_cut_excluded="Both saved boundaries exclude reference y=40 mm section edges"),
        units=dict(length="mm", unsigned_boundary_distance="mm", node_window_proxy="mm"),
        geometry_scope="Unsigned straight Q1 boundary distances; not signed penetration; containment not tested",
        left_distance_scope="Minimum to the saved left edge set may occur at the lower corner and below the body; not an x-normal gap",
        node_window_scope=measured["accepted_states"][0]["node_window_scope"], containment_tested=False,
        contact_or_clamping_qualification=False, pressure_defined=False,
        force_calls=0, tangent_calls=0, solver_calls=0, HP_calls=0, geometry_measurement_calls=0, boundary_extraction_calls=0,
        input_files_sha256={**{record["local_role"]: record["sha256"] for record in remapped.values()},
                            "measurement/boundary_measurements.json": digest(measurement_file),
                            "viewer/plot_native_boundary_geometry.py": digest(frozen)}, input_pins_unchanged_after_plot=True,
        measurement_input_remapping=remapped,
        remapping_scope="Original absolute paths are historical only; result/model/accepted suffixes and hf_repo source suffixes bind this clone by SHA",
        source_sha256=digest(frozen), output_files_sha256={name:digest(output/name) for name in
            ("native_boundary_geometry.png", "boundary_numeric_states.csv", "plot_native_boundary_geometry_frozen.py")})
    (output/"view_metadata.json").write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps(dict(accepted_states=len(rows), output=str(output), new_mechanics_calls=0, new_geometry_measurements=0)))


if __name__ == "__main__":
    main()
