"""Plot saved F16 mechanical force/action qualification; no mechanics calls."""
import argparse
import csv
from decimal import Decimal
import gzip
import hashlib
import json
from pathlib import Path
from time import perf_counter

STARTED = perf_counter()
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.colors import LogNorm
import numpy as np
import psutil

PARTS = ("total", "material", "regularization")
FORCES = ("residual", "material_residual", "regularization_residual")
AUXILIARY = dict(status="not_evaluated", qualified=False, field_present=False)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--stage", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.repo.resolve()
    stage, output = (root/args.stage).resolve(), args.output.resolve()
    candidate, reference = stage/"check/candidate", stage/"check/reference"
    bindings, process, peak = {}, psutil.Process(), 0
    source_pin = sha(Path(__file__))
    output.mkdir(parents=True, exist_ok=False)

    def checkpoint():
        nonlocal peak
        memory = 0
        for member in [process, *process.children(recursive=True)]:
            try:
                info = member.memory_info()
                memory += max(info.rss, getattr(info, "peak_wset", info.rss))
            except psutil.NoSuchProcess:
                pass
        peak = max(peak, memory)
        if perf_counter()-STARTED > 120 or peak > 8*1024**3 or (output.parent/"stop_requested.txt").exists():
            raise RuntimeError("Saved-view resource or stop limit reached")

    def bind(path, expected=None):
        relative = path.resolve().relative_to(root).as_posix()
        pin = sha(path)
        if expected is not None and pin != expected:
            raise ValueError("Saved file SHA differs: "+relative)
        bindings[relative] = pin
        return path

    def archive(directory, record, exact=True):
        path = bind(directory/record["path"], record["sha256"])
        with np.load(path, allow_pickle=False) as stored:
            arrays = {name: stored[name] for name in stored.files}
        if exact and set(arrays) != set(record["fields"]):
            raise ValueError("Saved archive field set differs")
        for name, declaration in record["fields"].items():
            value = arrays[name]
            if (value.dtype.name != declaration["dtype"] or list(value.shape) != declaration["shape"]
                    or hashlib.sha256(value.tobytes(order="C")).hexdigest() != declaration["sha256"]):
                raise ValueError("Saved raw field differs: "+name)
        checkpoint()
        return arrays

    result_file = bind(candidate/"result.json")
    result = json.loads(result_file.read_text(encoding="utf-8"))
    audit = json.loads(bind(reference/"result.json").read_text(encoding="utf-8"))
    counts, hp_counts = result["call_counts"], audit["call_counts"]
    if not (result["status"] == audit["status"] == "pass"
            and audit["candidate_result_sha256"] == sha(result_file)
            and result["response_contract"] == audit["response_contract"] == "split-numpy-mechanical-1.0"
            and result["auxiliary_material_energy"] == audit["auxiliary_material_energy"] == AUXILIARY
            and counts["force_started"] == counts["force_completed"] == 1
            and counts["tangent_started"] == counts["tangent_completed"] == 1
            and counts["action_consumer_started"] == counts["action_consumer_completed"] == 3
            and hp_counts["HP_started"] == hp_counts["HP_completed"] == 2
            and audit["fresh_HP_for_this_phase"] is True
            and audit["full_tangent_columns_HP_checked"] is False):
        raise ValueError("Terminal mechanical candidate and reference pass required")
    for name, pin in result["source_bindings"].items():
        bind(candidate/"sources"/name, pin)
    snapshot_pins = {
        "input_state.npz": result["input_sha256"],
        "model_snapshot.npz": result["model_source_sha256"],
        "direction_snapshot.npz": result["direction_source_sha256"],
        "witness_direction_snapshot.npz": result["witness_direction_source_sha256"],
        "diagnostic_result.json": result["diagnostic_result_sha256"],
        "diagnostic_first_bad.npz": result["diagnostic_payload_sha256"],
        "latest_closed_diagnostic.json": result["latest_closed_diagnostic"]["result_sha256"],
        "latest_first_bad.npz": result["latest_closed_diagnostic"]["payload_sha256"],
        "observation.json": result["bindings"]["lf_data_preparation/native_workpiece_001/coarse_square_cycle_003/first_force_range_input/observation.json"],
    }
    for name, pin in snapshot_pins.items():
        bind(candidate/name, pin)
    for name, pin in audit["files"].items():
        bind(reference/name, pin)
    fixture = archive(candidate, result["fixture"])
    arrays = archive(candidate, result["arrays"])
    archive(candidate, result["force_fields"])
    archive(candidate, result["tangents"])
    for record in result["matrices"].values():
        stored = archive(candidate, record, exact=False)
        if (stored["shape"].tolist() != record["shape"] or len(stored["data"]) != record["nnz"]
                or stored["format"].item() != b"csc"):
            raise ValueError("Saved full CSC storage declaration differs")
    if "material_energy" in arrays or not np.all(fixture["lift"] == 0):
        raise ValueError("Expected omitted energy and authoritative zero lift")
    ne, ndof = len(fixture["connectivity"]), len(fixture["fluctuation"])
    if not (ne == result["elements"] == audit["elements_compared"] == 3200
            and ndof == audit["global_dofs"] == 6642
            and audit["local_gate_count"] == 6*ne and audit["global_gate_count"] == 9
            and audit["full_local_tangent_coefficients_assembly_checked"] == 3*64*ne):
        raise ValueError("Full saved mechanical coverage differs")
    with gzip.open(reference/"checks.json.gz", "rt", encoding="utf-8") as stream:
        checks = json.load(stream)
    if len(checks) != 6*ne+9 or not all(row["pass_gate"] is True
            and Decimal(row["normalized_error"]) <= Decimal(row["limit"])
            and Decimal(row["hp80_hp120_error"]) <= Decimal(row["reference_limit"])
            and Decimal(row["reference_limit"]) == Decimal("1e-40") for row in checks):
        raise ValueError("All original saved 19200+9 gates must pass")
    errors = {(row["element"], row["kind"], row["component"]): row["normalized_error"]
              for row in checks if row["scope"] == "local"}
    if len(errors) != 6*ne:
        raise ValueError("Every element/component force and action record is required")
    force_norms = [np.linalg.norm(arrays[name], axis=1) for name in FORCES]
    action_norms = [np.linalg.norm(arrays[part+"_action"], axis=1) for part in PARTS]
    polygons = fixture["coordinates"][fixture["connectivity"]]
    maximum_displacement = float(np.abs(fixture["fluctuation"]).max())
    plt.rcParams.update({"font.size": 12, "axes.titlesize": 13})
    figure, axes = plt.subplots(2, 3, figsize=(16, 10))
    ranges = {}
    for row, values, label, unit, floor in [(0, force_norms, "Mechanical force", "N", 1e-60),
                                          (1, action_norms, "Cached DD Jv", "N/mm", 1e-30)]:
        maximum = max(float(value.max()) for value in values)
        upper = max(maximum, floor*10)
        ranges[label] = dict(minimum=floor, maximum=upper, units=unit, display_floor_only=True)
        for axis, data, part in zip(axes[row], values, PARTS):
            collection = PolyCollection(polygons, array=np.maximum(data, floor), cmap="viridis",
                norm=LogNorm(floor, upper), edgecolors="none")
            axis.add_collection(collection)
            axis.add_collection(PolyCollection(polygons[fixture["solid"]], facecolors="none", edgecolors="#333", linewidths=.12))
            axis.autoscale_view(); axis.set_aspect("equal")
            axis.set_xlabel("reference x (mm)"); axis.set_ylabel("reference y (mm)")
            axis.set_title(f"{part.title()} {label}\nmax {data.max():.5g} {unit}")
            figure.colorbar(collection, ax=axis, shrink=.73, label="8-DOF local norm ("+unit+")")
    def worst(kind):
        return ", ".join(f"{part}: {Decimal(audit['worst'][kind][part]['normalized_error']):.3E}" for part in PARTS)
    agreement = max(Decimal(row["hp80_hp120_error"]) for row in checks)
    figure.suptitle("F16 MECHANICAL QUALIFICATION — tiny trial, NOT an accepted equilibrium state", fontsize=16)
    caption = (f"Reference native cell locations only; zero lift, actual max |u|={maximum_displacement:.7g} mm. No deformation magnification.\n"
        f"Original gates: 19200 local + 9 global PASS; HP80/120 agreement worst {agreement:.3E} <= 1e-40; all 614400 local-to-CSC coefficients checked.\n"
        "Force base floor 2e-13 N (component scales as saved); Jv floor 1e-10 N/mm. Limits force: 1e-11 / 1e-9; Jv: 1e-10 / 1e-9 (total / components).\n"
        "Worst force errors — "+worst("force")+"\nWorst cached DD action errors — "+worst("action")+"\n"
        "One dimensionless witness direction, not exhaustive HP matrix columns. P/S finite only; auxiliary energy NOT EVALUATED; no unloading/T25, contact or equilibrium qualification.\n"
        "Colors show all elements. Floors 1e-60 N / 1e-30 N/mm are display-only. No new force, tangent, consumer, HP, scatter, solve or distance calculation.")
    figure.text(.025, .025, caption, va="bottom", fontsize=10.5)
    figure.subplots_adjust(left=.05, right=.97, top=.89, bottom=.27, wspace=.32, hspace=.45)
    checkpoint()
    image = output/"mechanical_F16_qualified_fields.png"
    figure.savefig(image, dpi=180); plt.close(figure)
    table = output/"mechanical_F16_element_values.csv"
    with table.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["element", "solid", *[part+"_force_norm_N" for part in PARTS],
            *[part+"_Jv_norm_N_per_mm" for part in PARTS],
            *[part+"_force_normalized_error" for part in PARTS], *[part+"_action_normalized_error" for part in PARTS]])
        for element in range(ne):
            writer.writerow([element, bool(fixture["solid"][element]), *[float(x[element]) for x in force_norms],
                *[float(x[element]) for x in action_norms],
                *[errors[(element, "force", p)] for p in PARTS], *[errors[(element, "action", p)] for p in PARTS]])
    checkpoint()
    if sha(Path(__file__)) != source_pin or not all(sha(root/name) == pin for name, pin in bindings.items()):
        raise ValueError("Frozen source/input changed during saved rendering")
    metadata = dict(schema="mechanical-F16-saved-view-1.0", status="rendered_recorded_mechanical_qualification",
        qualification_scope="Only captured F16 mechanical force and the recorded dimensionless-direction action; not equilibrium",
        auxiliary_material_energy=AUXILIARY, source_sha256=source_pin, input_bindings=bindings,
        historical_candidate_bindings=result["bindings"], historical_HP_sources=audit["HP_source_bindings"],
        display_binding_scope="Owned source capsules, input snapshots, candidate archives/CSCs and reference files; historical live sources recorded, not required for saved display",
        elements=ne, dofs=ndof, captured_state_sha256=result["captured_state_sha256"],
        local_gates=6*ne, global_gates=9, full_CSC_coefficient_checks=3*64*ne,
        HP_agreement_worst=str(agreement), worst=audit["worst"], HP_full_columns_qualified=False,
        maximum_physical_displacement_mm=maximum_displacement, lift_zero=True, accepted_state=False,
        reference_geometry_only=True, color_ranges=ranges, norm_semantics="Euclidean norms of eight saved local entries; no global assembly",
        force_base_floor_N=audit["force_scale_floor_N"], action_floor_N_per_mm=audit["action_scale_floor_N_per_mm"],
        stress_HP_qualified=False, energy_qualified=False, unload_T25_qualified=False,
        seconds_limit=120, outer_seconds=120, rss_limit_bytes=8*1024**3,
        new_calls=dict(force=0,tangent=0,consumer=0,HP=0,solver=0,global_assembly=0,distance=0,geometry=0),
        output_sha256={path.name:sha(path) for path in (image, table)})
    (output/"view_metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")


if __name__ == "__main__":
    main()
