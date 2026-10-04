"""Saved observations only: failed complete F16 response, no mechanics evaluation."""
from __future__ import annotations

import argparse
import csv
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

NEW = "lf_data_preparation/native_workpiece_001/horner192_range_diagnostic_001/evidence"
OLD = "lf_data_preparation/native_workpiece_001/coarse_square_cycle_003/range_diagnostic_001/evidence"
NEW_RESULT = "3f2678fde968da9032237d52227db9e124307e3331e7450d812d83d411a8cd31"
OLD_RESULT = "00e6d728f4099aa3cce74ab7375b9e3645d04919383c7b9af1e4d4aa7fa2473a"
NEW_LAUNCH = "c76d64c600a8798695ce80ee087cf714bca0eadcf154e933645d8045807ffbda"
DISPLAY_FLOOR = 1e-30


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root, output = args.repo.resolve(), args.output.resolve()
    started, process, bindings, peak = STARTED, psutil.Process(), {}, 0
    output.mkdir(parents=True, exist_ok=False)
    source_pin = sha(Path(__file__))

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
        if (perf_counter()-started > 120 or peak > 8*1024**3
                or (output.parent/"stop_requested.txt").exists()):
            raise RuntimeError("Saved-view resource or stop limit reached")

    def bind(path, expected=None):
        relative = path.resolve().relative_to(root).as_posix()
        actual = sha(path)
        if expected is not None and actual != expected:
            raise ValueError("Saved input SHA differs: "+relative)
        bindings[relative] = actual
        return path

    def archive(path, pin, fields):
        bind(path, pin)
        with np.load(path, allow_pickle=False) as stored:
            arrays = {name: stored[name] for name in stored.files}
        if set(arrays) != set(fields):
            raise ValueError("Saved archive fields differ")
        for name, array in arrays.items():
            declaration = fields[name]
            if (array.dtype.name != declaration["dtype"] or list(array.shape) != declaration["shape"]
                    or hashlib.sha256(array.tobytes(order="C")).hexdigest() != declaration["sha256"]):
                raise ValueError("Saved field differs: "+name)
        checkpoint()
        return arrays

    reports = []
    for relative, pin in [(OLD, OLD_RESULT), (NEW, NEW_RESULT)]:
        directory = root/relative
        report = json.loads(bind(directory/"result.json", pin).read_text(encoding="utf-8"))
        if not (report["status"] == "diagnostic_captured" and report["qualification"] is False
                and report["force_started"] == 1 and report["force_completed"] == 0
                and report["observation_hooks_restored"] is True):
            raise ValueError("Expected a captured closed force failure")
        for name, value in report["input_bindings"].items():
            bind(root/name, value)
        reports.append(report)
        checkpoint()
    old, new = reports
    launch = json.loads(bind((root/NEW).parent/"diagnostic_launch.json", NEW_LAUNCH).read_text(encoding="utf-8"))
    if not (launch["status"] == "pass" and launch["exit_code"] == 0
            and launch["invocations"] == 1 and launch["all_bindings_unchanged"] is True):
        raise ValueError("Expected the single captured diagnostic launch")
    for name, value in launch["bindings"].items():
        bind(root/name, value)
    fields = new["raw_response"]
    raw = archive(root/NEW/fields["payload"], fields["payload_sha256"], fields["fields"])
    original = new["original_observation"]
    supplied = archive(root/NEW/"input.npz", original["input_npz_sha256"], original["fields"])
    if old["original_observation"]["state_sha256"] != original["state_sha256"]:
        raise ValueError("The two observations are not the same F16 state")
    bad = []
    for relative, report in [(OLD, old), (NEW, new)]:
        record = report["first_bad_primitive"]
        bad.append(archive(root/relative/record["payload"], record["payload_sha256"], record["fields"])["invalid_indices"])
    for name, array in raw.items():
        counts = fields["finite_counts"][name]
        if int(np.isfinite(array).sum()) != counts["finite"] or int((~np.isfinite(array)).sum()) != counts["nonfinite"]:
            raise ValueError("Stored finite count differs: "+name)
    coordinates, connectivity = supplied["coordinates"], supplied["connectivity"]
    polygons = coordinates[connectivity]
    count = len(connectivity)
    bad_counts = [np.bincount(indices[:, 0], minlength=count) for indices in bad]
    force_names = ("material_residual", "regularization_residual", "residual")
    if not all(np.isfinite(raw[name]).all() for name in force_names):
        raise ValueError("Raw force observations are not finite")
    norms = [np.linalg.norm(raw[name], axis=1) for name in force_names]
    energy_bad = ~np.isfinite(raw["material_energy"])
    maximum = max(float(value.max()) for value in norms)
    normalization = LogNorm(DISPLAY_FLOOR, max(maximum, DISPLAY_FLOOR*10))
    plt.rcParams.update({"font.size": 12, "axes.titlesize": 14})
    figure, axes = plt.subplots(2, 3, figsize=(16, 11))

    def cells(axis, values, title, **options):
        collection = PolyCollection(polygons, array=values, edgecolors="none", **options)
        axis.add_collection(collection)
        axis.add_collection(PolyCollection(polygons[supplied["solid"]], facecolors="none", edgecolors="#303030", linewidths=.12))
        axis.autoscale_view(); axis.set_aspect("equal")
        axis.set_xlabel("reference x (mm)"); axis.set_ylabel("reference y (mm)")
        axis.set_title(title)
        return collection

    for axis, values, label in zip(axes[0], norms, ("Material", "Hu regularization", "Total")):
        collection = cells(axis, np.maximum(values, DISPLAY_FLOOR),
            f"Raw {label}: max {values.max():.6g} N", cmap="viridis", norm=normalization)
        figure.colorbar(collection, ax=axis, shrink=.75, label="8-DOF element force norm (N)")
    collection = cells(axes[1, 0], energy_bad.astype(float),
        f"Auxiliary energy unavailable: {energy_bad.sum()} / {count} cells", cmap="Reds", clim=(0, 1))
    figure.colorbar(collection, ax=axes[1, 0], ticks=[0, 1], shrink=.75).ax.set_yticklabels(["finite", "NaN / nonfinite"])
    for axis, values, label in zip(axes[1, 1:], bad_counts, ("Old matmul320", "Horner192 candidate")):
        collection = cells(axis, values.astype(float),
            f"{label}: {values.sum()} bad IPs / {np.count_nonzero(values)} cells", cmap="magma", clim=(0, 9))
        figure.colorbar(collection, ax=axis, shrink=.75, label="First-primitive invalid IP count / cell")
    def where(report):
        stack = report["first_bad_primitive"]["stack"]
        return " -> ".join(f"{row['function']}:{row['line']}" for row in stack if row["file"].endswith("split_kernel_invariants_hu.py"))
    figure.suptitle("F16 SAVED DIAGNOSTIC — complete force still FAILED; raw fields unqualified", fontsize=17)
    caption = ("Original native locations, reference geometry only; no deformation or new geometry calculation.\n"
        f"Full 3200-cell raw forces/stresses/kinematics finite; material energy {energy_bad.sum()} nonfinite; combined support flag {raw['arithmetic_supported'].item():g}.\n"
        "Force colors use a common N scale. 1e-30 N is a display floor only; no global assembly or reaction interpretation.\n"
        "Old first kernel stack: "+where(old)+"\nNew first kernel stack: "+where(new)+"\n"
        "These are first executed invalid returns, not proof of branch contribution. No fresh force, tangent, HP or solver; no equilibrium/contact claim.")
    figure.text(.025, .03, caption, va="bottom", fontsize=11)
    figure.subplots_adjust(left=.05, right=.97, top=.9, bottom=.25, wspace=.32, hspace=.35)
    checkpoint()
    image = output/"horner192_raw_diagnostic.png"
    figure.savefig(image, dpi=180); plt.close(figure)
    table = output/"raw_element_diagnostic.csv"
    with table.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["element", "material_force_norm_N", "regularization_force_norm_N", "total_force_norm_N", "material_energy_N_mm_if_finite", "energy_nonfinite", "old_invalid_IPs", "new_invalid_IPs"])
        for i in range(count):
            writer.writerow([i, *[float(value[i]) for value in norms], "" if energy_bad[i] else float(raw["material_energy"][i]), bool(energy_bad[i]), int(bad_counts[0][i]), int(bad_counts[1][i])])
    checkpoint()
    if sha(Path(__file__)) != source_pin or not all(sha(root/name) == pin for name, pin in bindings.items()):
        raise ValueError("Source/input changed during saved rendering")
    metadata = dict(schema="horner192-saved-diagnostic-view-1.0", status="rendered_unqualified_diagnostic", qualification=False,
        source_sha256=source_pin, input_bindings=bindings, elements=count, finite_counts=fields["finite_counts"],
        force_norm_definition="Euclidean norm of eight saved local force entries; no global scatter", force_units="N", energy_units="N mm",
        force_color_range_N=[DISPLAY_FLOOR, max(maximum, DISPLAY_FLOOR*10)], display_floor_N=DISPLAY_FLOOR,
        reference_geometry_only=True, zero_nonfinite_energy_not_filled=True,
        old_first_primitive=dict(stack=old["first_bad_primitive"]["stack"], invalid_IPs=int(bad_counts[0].sum()), affected_cells=int(np.count_nonzero(bad_counts[0]))),
        new_first_primitive=dict(stack=new["first_bad_primitive"]["stack"], invalid_IPs=int(bad_counts[1].sum()), affected_cells=int(np.count_nonzero(bad_counts[1]))),
        raw_response_support_flag=float(raw["arithmetic_supported"].item()), energy_nonfinite_cells=int(energy_bad.sum()),
        seconds_limit=120, rss_limit_bytes=8*1024**3, new_calls=dict(force=0,tangent=0,consumer=0,HP=0,solver=0,geometry=0,global_assembly=0),
        output_sha256={path.name:sha(path) for path in (image, table)})
    (output/"view_metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")


if __name__ == "__main__":
    main()
