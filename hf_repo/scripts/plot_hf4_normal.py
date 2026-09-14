"""Plot only saved HF-4 uniform-normal evidence; never evaluate mechanics.

Usage: python scripts/plot_hf4_normal.py --root ../hf4_results --output NEW_DIR
Four completed audit summaries are discovered through *_audit/summary.json.
Each summary's source_run and the run metadata identify its gamma/mesh pair.
Failed or partially audited runs remain visible; no missing reference is filled.
Lines connect archived samples only. Deformation is coordinates + displacement,
with scale exactly one. The force is bottom-platen force on the model, not an
inferred local contact traction, stress, or pressure.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import hashlib
import json
from pathlib import Path, PureWindowsPath

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np


class Sources:
    """Record every input read and reject changes during plotting."""

    def __init__(self):
        self.files = {}

    def bind(self, path, expected=None):
        path = Path(path).resolve()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if expected is not None and digest != expected:
            raise ValueError(f"input hash differs: {path}")
        record = dict(sha256=digest, size_bytes=path.stat().st_size)
        previous = self.files.setdefault(str(path), record)
        if previous != record:
            raise ValueError(f"input changed during plotting: {path}")
        return path

    def json(self, path, expected=None):
        path = self.bind(path, expected)
        return json.loads(path.read_text(encoding="utf-8-sig"))

    def npz(self, path, expected=None):
        path = self.bind(path, expected)
        with np.load(path, allow_pickle=False) as archive:
            result = {key: archive[key] for key in archive.files}
        for key, array in result.items():
            if array.dtype.kind not in "biuf" or not np.all(np.isfinite(array)):
                raise ValueError(f"nonfinite or nonnumeric NPZ field: {path}:{key}")
        return result

    def verify(self):
        for path, record in list(self.files.items()):
            self.bind(path, record["sha256"])


def within(directory, filename):
    path = (directory / filename).resolve()
    if path.parent != directory.resolve():
        raise ValueError(f"unexpected evidence path: {filename}")
    return path


def portable(path):
    return str(path).replace("\\", "/").rstrip("/")


def find_source_run(root, recorded):
    # Relocation preserves source_run's directory name and validates file hashes.
    # It never searches outside the supplied HF-4 root for a substitute run.
    name = PureWindowsPath(recorded).name if "\\" in recorded else Path(recorded).name
    run = (root / name).resolve()
    if run.parent != root or not run.is_dir():
        raise ValueError(f"source_run unavailable under --root: {recorded}")
    return run


def finite_number(value, name):
    number = float(value)
    if not np.isfinite(number):
        raise ValueError(f"nonfinite {name}")
    return number


def read_case(summary_path, root, sources):
    summary = sources.json(summary_path)
    if summary.get("schema_version") != "hf4-normal-audit-1.0":
        raise ValueError(f"expected a completed HF-4 audit summary: {summary_path}")
    audit = summary_path.parent.resolve()
    run = find_source_run(root, summary["source_run"])
    bindings = sources.json(audit / "bindings.json")
    bindings = {portable(key): value for key, value in bindings.items()}

    def run_file(relative, npz=False):
        original = portable(summary["source_run"]) + "/" + relative
        if original not in bindings:
            raise ValueError(f"audit does not bind source input: {original}")
        reader = sources.npz if npz else sources.json
        return reader(run / relative, bindings[original])

    metadata = run_file("metadata.json")
    result = run_file("result.json")
    index = run_file("steps/index.json")
    model = run_file("model.npz", npz=True)
    if metadata.get("schema_version") != "hf4-normal-evidence-1.0":
        raise ValueError("unexpected production evidence schema")
    entries = index["steps"]
    if index["accepted_count"] != len(entries) or len(entries) != len(result["accepted_steps"]):
        raise ValueError("accepted state inventory differs")
    rows = summary["rows"]
    if summary["states_completed"] != len(rows) or summary["accepted_count"] != len(entries):
        raise ValueError("audit state inventory differs")
    if summary["production_status"] != result["status"]:
        raise ValueError("audit/production statuses differ")
    if summary["status"] == "pass" and (
            len(rows) != len(entries) or result["status"] != "success"
            or any(row["status"] != "pass" for row in rows)):
        raise ValueError("audit claims pass without all accepted states")
    audited = {}
    for expected_index, row in enumerate(rows):
        i = row["index"]
        if i != expected_index or i >= len(entries) or row["d"] != entries[i]["d"]:
            raise ValueError("audit rows must be the ordered accepted-state prefix")
        commitment = sources.json(audit / f"commit_{i:04d}.json")
        required = {f"state_{i:04d}.json", f"hp50_{i:04d}.json", f"reference_{i:04d}.json"}
        if row["d"] == metadata["task"]["targets_mm"][-1]:
            if row.get("crosscheck_relative") is None:
                raise ValueError("terminal audit row lacks its precision crosscheck")
            required.add(f"hp80_{i:04d}.json")
        if set(commitment) != required:
            raise ValueError("audit commit has incomplete or extra evidence files")
        for name, digest in commitment.items():
            sources.bind(within(audit, name), digest)
        if sources.json(audit / f"state_{i:04d}.json") != row:
            raise ValueError("audit summary row differs from committed state")
        audited[i] = row

    records = []
    originals = []
    targets = metadata["task"]["targets_mm"]
    for i, entry in enumerate(entries):
        if entry["index"] != i:
            raise ValueError("unordered production index")
        scalar_path = within(run / "steps", entry["metadata"])
        array_path = within(run / "steps", entry["file"])
        scalar = sources.json(scalar_path, entry["metadata_sha256"])
        sources.bind(array_path, entry["arrays_sha256"])
        reported = result["accepted_steps"][i]
        if scalar["index"] != i or scalar["d"] != entry["d"]:
            raise ValueError("production state identity differs")
        for key in ("d", "is_original_target", "original_target_displacement", "bisection_depth"):
            if scalar[key] != reported[key]:
                raise ValueError("step/result state identity differs")
        if scalar["is_original_target"]:
            originals.append(scalar["d"])
        row = audited.get(i)
        point = dict(index=i, d_mm=finite_number(scalar["d"], "d"),
                     force_N=finite_number(scalar["drive_force"], "drive force"),
                     gap_mm=finite_number(scalar["gap_mm"], "saved gap"),
                     is_original_target=scalar["is_original_target"],
                     original_target_displacement_mm=scalar["original_target_displacement"],
                     bisection_depth=scalar["bisection_depth"],
                     audit_status=row["status"] if row else "not_audited",
                     production_scalar_file=str(scalar_path),
                     production_arrays_file=str(array_path), audit_row=row)
        if row:
            if float(row["force_N"]) != point["force_N"]:
                raise ValueError("audited drive force differs from production value")
            with localcontext() as context:
                context.prec = metadata["spec"]["crosscheck_precision_digits"]
                force = Decimal(row["force_N"])
                point["finite_force_error_N_decimal"] = str(force - Decimal(row["finite_force_N"]))
                point["hard_force_error_N_decimal"] = str(force - Decimal(row["hard_force_N"]))
            for key in ("finite_force_N", "finite_gap_mm", "hard_force_N", "hard_gap_mm"):
                point[key] = finite_number(row[key], key)
            point["independent_gap_mm"] = finite_number(row["gap_mm"], "independent gap")
            for label in ("finite", "hard"):
                point[f"{label}_force_error_N"] = finite_number(
                    point[f"{label}_force_error_N_decimal"], f"{label} force error")
        records.append(point)
    if any(b["d_mm"] <= a["d_mm"] for a, b in zip(records, records[1:])):
        raise ValueError("accepted displacements are not strictly increasing")
    if result["status"] == "success" and (
            originals != targets or not result["target_reached"]
            or result["target_metrics"] is None or result["target_metrics"]["d"] != targets[-1]):
        raise ValueError("production success lacks all original targets")
    if result["status"] != "success" and (result["target_reached"] or result["target_metrics"] is not None):
        raise ValueError("failure cannot publish target metrics")
    if not records:
        raise ValueError("no accepted state is available for a shape plot")
    last = records[-1]
    last_arrays = sources.npz(last["production_arrays_file"])
    coordinates = model["coordinates"]
    connectivity = model["connectivity"]
    body_ids = model["body_ids"]
    displacement = last_arrays["u"]
    if (coordinates.ndim != 2 or coordinates.shape[1] != 2
            or connectivity.ndim != 2 or connectivity.shape[1] != 4
            or connectivity.dtype.kind not in "iu"
            or np.any(connectivity < 0) or np.any(connectivity >= len(coordinates))
            or body_ids.shape != (len(connectivity),) or not np.all(np.isin(body_ids, [0, 1, 2]))
            or displacement.shape != (2*len(coordinates),)):
        raise ValueError("invalid saved mesh/displacement representation")
    geometry = metadata["task"]["geometry"]
    gi, mi = metadata["gamma_index"], metadata["mesh_index"]
    if gi not in (0, 1) or mi not in (0, 1):
        raise ValueError("unexpected gamma/mesh index")
    if (metadata["task"]["gamma"] != metadata["spec"]["gammas"][gi]
            or metadata["task"]["mesh_size_mm"] != metadata["spec"]["mesh_sizes_mm"][mi]):
        raise ValueError("gamma/mesh metadata differs from the selected frozen pair")
    coverage = dict(requested_original_targets_mm=targets, accepted_original_targets_mm=originals,
                    missing_original_targets_mm=[d for d in targets if d not in originals],
                    requested_original_target_count=len(targets), accepted_original_target_count=len(originals),
                    accepted_state_count=len(records), accepted_substep_count=len(records)-len(originals),
                    audited_state_count=len(rows), passed_audit_state_count=sum(r["status"] == "pass" for r in rows),
                    last_accepted_displacement_mm=last["d_mm"], requested_final_displacement_mm=targets[-1],
                    positive_displacement_state_count=sum(p["d_mm"] > 0 for p in records))
    return dict(gamma_index=gi, mesh_index=mi, gamma=metadata["task"]["gamma"],
                mesh_size_mm=metadata["task"]["mesh_size_mm"],
                source_run=str(run), recorded_source_run=summary["source_run"],
                audit_directory=str(audit), metadata=metadata,
                production_status=result["status"], audit_status=summary["status"],
                target_reached=result["target_reached"], failure=result.get("failure"),
                geometry=geometry, records=records, coverage=coverage,
                shape=dict(index=last["index"], d_mm=last["d_mm"],
                           coordinates_mm=coordinates.tolist(), connectivity=connectivity.tolist(),
                           body_ids=body_ids.tolist(), displacement_mm=displacement.reshape(-1, 2).tolist(),
                           deformation_scale=1.0))


COLORS = ("#0072B2", "#D55E00")
MARKERS = ("o", "s")


def label(case, show_partial=False):
    text = f"gamma={case['gamma']:.0e}, h={case['mesh_size_mm']:g} mm"
    if show_partial and not case["target_reached"]:
        coverage = case["coverage"]
        text += f" [PARTIAL: {coverage['accepted_original_target_count']}/{coverage['requested_original_target_count']} targets]"
    return text


def evidence_status(cases):
    reached = sum(c["target_reached"] for c in cases)
    passed = sum(c["audit_status"] == "pass" for c in cases)
    partial = reached != len(cases) or passed != len(cases)
    return dict(status="rendered_partial_evidence" if partial else "rendered_complete_evidence",
                paths_reaching_target=reached, passing_audits=passed, path_count=len(cases),
                message=("PARTIAL EVIDENCE" if partial else "Complete archived coverage")
                + f": {reached}/{len(cases)} paths reached target; {passed}/{len(cases)} audits pass")


def figure_title(fig, title, cases):
    status = evidence_status(cases)
    fig.suptitle(title + "\n" + status["message"], fontsize=12,
                 color="#A32638" if status["status"] == "rendered_partial_evidence" else "#222222")


def annotate_stop(ax, case, point, ordinate):
    """Point at the actual last saved sample; never extend an unfinished curve."""
    if case["target_reached"]:
        return
    coverage = case["coverage"]
    anchor = "stopped" if point["index"] == case["records"][-1]["index"] else "last audited sample"
    ax.annotate(f"NOT REACHED: {anchor} d={point['d_mm']:g} mm\n"
                f"{coverage['accepted_original_target_count']}/{coverage['requested_original_target_count']} original targets",
                xy=(point["d_mm"], point[ordinate]), xycoords="data",
                xytext=(0.32, 0.70), textcoords="axes fraction", fontsize=9,
                color="#A32638", bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor="#A32638", alpha=0.93),
                arrowprops=dict(arrowstyle="->", color="#A32638", linewidth=1.2))


def save_figure(fig, path):
    fig.savefig(path, dpi=180, facecolor="white")
    plt.close(fig)


def axes_style(ax):
    ax.grid(True, alpha=0.22)
    ax.spines[["top", "right"]].set_visible(False)


def plot_curves(cases, output):
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.7), layout="constrained")
    for case in cases:
        color, marker = COLORS[case["gamma_index"]], MARKERS[case["mesh_index"]]
        points = case["records"]
        checked = [p for p in points if p["audit_row"] is not None]
        for ax, quantity, suffix in ((axes[0], "force", "N"), (axes[1], "gap", "mm")):
            ax.plot([p["d_mm"] for p in points], [p[f"{quantity}_{suffix}"] for p in points],
                    color=color, linewidth=1.1, alpha=0.9)
            for original in (False, True):
                selected = [p for p in points if p["is_original_target"] == original]
                ax.plot([p["d_mm"] for p in selected], [p[f"{quantity}_{suffix}"] for p in selected],
                        linestyle="none", marker=marker, markersize=5 if original else 3,
                        markerfacecolor=color if original else "white", markeredgecolor=color)
            for reference, style in (("finite", "--"), ("hard", ":")):
                ax.plot([p["d_mm"] for p in checked],
                        [p[f"{reference}_{quantity}_{suffix}"] for p in checked],
                        color=color if reference == "finite" else "#333333",
                        linestyle=style, linewidth=1.05, alpha=0.75)
            unreviewed = [p for p in points if p["audit_status"] != "pass"]
            ax.plot([p["d_mm"] for p in unreviewed], [p[f"{quantity}_{suffix}"] for p in unreviewed],
                    linestyle="none", marker="x", color="#222222", markersize=7)
            annotate_stop(ax, case, points[-1], f"{quantity}_{suffix}")
    for ax in axes:
        ax.set_xlabel("Prescribed bottom motion d [mm]")
        axes_style(ax)
    axes[0].set_ylabel("Bottom-platen force on model [N]")
    axes[1].set_ylabel("Mean interface gap [mm]")
    axes[0].set_title("Force versus prescribed motion")
    axes[1].set_title("Gap versus prescribed motion")
    handles = [Line2D([], [], color=COLORS[c["gamma_index"]], marker=MARKERS[c["mesh_index"]],
                      markersize=5, label=label(c, show_partial=True)) for c in cases]
    handles += [Line2D([], [], color="#555555", linestyle="--", label="Finite-medium reference"),
                Line2D([], [], color="#333333", linestyle=":", label="Ideal hard-contact reference"),
                Line2D([], [], color="#555555", marker="o", markerfacecolor="white", linestyle="none",
                       markersize=4, label="Open marker: accepted substep")]
    if any(p["audit_status"] != "pass" for c in cases for p in c["records"]):
        handles.append(Line2D([], [], color="#222222", marker="x", linestyle="none", label="Not passed / not audited"))
    fig.legend(handles=handles, loc="outside lower center", ncol=3, fontsize=8)
    figure_title(fig, "HF-4 uniform normal compression | archived samples only", cases)
    save_figure(fig, output / "force_gap_vs_d.png")


def plot_errors(cases, output):
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.2), layout="constrained")
    EA_values = [c["metadata"]["task"]["material"]["E_MPa"] * c["geometry"]["width_mm"]
                 * c["geometry"]["thickness_mm"] for c in cases]
    for reference, ax in zip(("finite", "hard"), axes):
        for case in cases:
            points = [p for p in case["records"] if p["audit_row"] is not None]
            ax.plot([p["d_mm"] for p in points], [p[f"{reference}_force_error_N"] for p in points],
                    color=COLORS[case["gamma_index"]], marker=MARKERS[case["mesh_index"]],
                    markersize=4, linewidth=1, label=label(case, show_partial=True))
            if points:
                annotate_stop(ax, case, points[-1], f"{reference}_force_error_N")
        ax.axhline(0, color="#555555", linewidth=0.8)
        ax.set_yscale("symlog", linthresh=1e-12*max(EA_values))
        ax.set_xlabel("Prescribed bottom motion d [mm]")
        ax.set_ylabel("FE force - reference force [N]")
        ax.set_title("Finite-medium reference" if reference == "finite" else "Ideal hard-contact reference")
        axes_style(ax)
    fig.legend(*axes[0].get_legend_handles_labels(), loc="outside lower center", ncol=2, fontsize=9)
    figure_title(fig, "Signed force differences | symmetric log axis preserves zero", cases)
    save_figure(fig, output / "force_errors_vs_d.png")


def plot_shapes(cases, output):
    fig, axes = plt.subplots(2, 4, figsize=(15.5, 9), layout="constrained",
                             gridspec_kw={"height_ratios": [2, 1]})
    body_colors = {0: "#E9C46A", 1: "#8CBBD7", 2: "#B5A1CC"}
    maximum_height = max(c["geometry"]["lower_height_mm"] + c["geometry"]["gap_mm"]
                         + c["geometry"]["upper_height_mm"] for c in cases)
    maximum_width = max(c["geometry"]["width_mm"] for c in cases)
    for column, case in enumerate(cases):
        shape = case["shape"]
        xy = np.asarray(shape["coordinates_mm"])
        conn = np.asarray(shape["connectivity"], dtype=int)
        ids = np.asarray(shape["body_ids"])
        u = np.asarray(shape["displacement_mm"])
        deformed = xy + u  # Exactly scale 1, with no display offset.
        ax = axes[0, column]
        cells = PolyCollection(deformed[conn], facecolors=[body_colors[int(i)] for i in ids],
                               edgecolors="#777777", linewidths=0.25)
        ax.add_collection(cells)
        width = case["geometry"]["width_mm"]
        levels = [0.0, case["geometry"]["lower_height_mm"],
                  case["geometry"]["lower_height_mm"] + case["geometry"]["gap_mm"],
                  maximum_height]
        for y in levels:
            ax.plot([0, width], [y, y], color="#555555", linestyle="--", linewidth=0.7, alpha=0.6)
        ax.set_xlim(-0.08*maximum_width, 1.08*maximum_width)
        ax.set_ylim(-0.05*maximum_height, 1.05*maximum_height)
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlabel("x [mm]")
        if column == 0:
            ax.set_ylabel("y [mm]")
        coverage = case["coverage"]
        terminal = "Reached target" if case["target_reached"] else "NOT REACHED"
        ax.set_title(f"{label(case)}\nd={shape['d_mm']:g} mm; scale 1\n"
                     f"{terminal}: {coverage['accepted_original_target_count']}/{coverage['requested_original_target_count']} targets\n"
                     f"{coverage['accepted_state_count']} saved states; audit: {case['audit_status']}", fontsize=9,
                     color="#222222" if case["target_reached"] else "#A32638")
        axes_style(ax)
        # Saved nodal values along the closest existing centreline; no interpolation.
        xline = np.unique(xy[:, 0])[np.argmin(abs(np.unique(xy[:, 0]) - width/2))]
        selected = np.flatnonzero(xy[:, 0] == xline)
        selected = selected[np.argsort(xy[selected, 1])]
        lower = axes[1, column]
        lower.plot(u[selected, 1], xy[selected, 1], color=COLORS[case["gamma_index"]],
                   marker=MARKERS[case["mesh_index"]], markersize=2.5, linewidth=1)
        lower.set_xlabel("Saved vertical displacement uy [mm]")
        if column == 0:
            lower.set_ylabel("Reference y [mm]")
        lower.set_ylim(-0.05*maximum_height, 1.05*maximum_height)
        lower.set_xlim(-0.02*max(c["shape"]["d_mm"] for c in cases),
                       max(1e-6, 1.05*max(c["shape"]["d_mm"] for c in cases)))
        lower.set_title(f"Nodal profile at x={xline:g} mm", fontsize=9)
        axes_style(lower)
        shape["profile_node_indices"] = selected.tolist()
        shape["profile_x_mm"] = float(xline)
        shape["deformed_coordinates_mm"] = deformed.tolist()
    handles = [Patch(facecolor=body_colors[i], edgecolor="#777777", label=name)
               for i, name in ((1, "Lower elastic block"), (0, "Third medium"), (2, "Upper elastic block"))]
    handles.append(Line2D([], [], color="#555555", linestyle="--", label="Reference horizontal boundaries"))
    fig.legend(handles=handles, loc="outside lower center", ncol=4, fontsize=9)
    figure_title(fig, "Last accepted states | true displacement scale | material regions only", cases)
    save_figure(fig, output / "deformed_shapes.png")


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def plot(root, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    if output.exists():
        raise FileExistsError("plot output must be a new directory")
    if not root.is_dir() or output == root:
        raise ValueError("invalid HF-4 input root or output")
    sources = Sources()
    sources.bind(Path(__file__))
    summaries = sorted(root.glob("*_audit/summary.json"))
    if len(summaries) != 4:
        raise ValueError("expected exactly four HF-4 *_audit/summary.json files")
    cases = [read_case(path, root, sources) for path in summaries]
    cases.sort(key=lambda c: (c["gamma_index"], c["mesh_index"]))
    if {(c["gamma_index"], c["mesh_index"]) for c in cases} != {(0, 0), (0, 1), (1, 0), (1, 1)}:
        raise ValueError("expected one run for each of the four gamma/mesh pairs")
    if any(c["geometry"] != cases[0]["geometry"] for c in cases[1:]):
        raise ValueError("the four cases have different physical geometries")
    for case in cases:
        for directory in (Path(case["source_run"]), Path(case["audit_directory"])):
            if output == directory or directory in output.parents:
                raise ValueError("plot output cannot modify an evidence directory")
    sources.verify()
    output.mkdir(parents=True, exist_ok=False)
    plot_curves(cases, output)
    plot_errors(cases, output)
    plot_shapes(cases, output)
    sources.verify()
    overall = evidence_status(cases)
    data = dict(schema_version="hf4-normal-plot-data-1.0", created_utc=datetime.now(timezone.utc).isoformat(),
                status=overall["status"], evidence_coverage=overall,
                scope="HF-4 uniform normal compression only", input_root=str(root),
                force_definition="bottom-platen constraint force on model; positive upward compression; no multiplier",
                gap_definition="reference arclength mean of upper minus lower material interface height",
                units=dict(length="mm", force="N"), deformation_scale=1.0,
                sample_policy="all accepted FE states; references only at committed audit rows; lines connect samples, with no new samples or mechanical interpolation",
                error_policy="signed FE minus reference from archived Decimal strings before binary64 plotting conversion",
                force_error_axis=dict(scale="symlog", linear_threshold_N=1e-12*max(
                    c["metadata"]["task"]["material"]["E_MPa"] * c["geometry"]["width_mm"]
                    * c["geometry"]["thickness_mm"] for c in cases)),
                interpretation="finite-medium leakage is not a measured contact-onset event; colors identify material regions only",
                cases=cases, input_files=sources.files,
                figures=["force_gap_vs_d.png", "force_errors_vs_d.png", "deformed_shapes.png"])
    write_json(output / "plot_data.json", data)
    files = [output/name for name in data["figures"]] + [output/"plot_data.json"]
    write_json(output / "plot_manifest.json", dict(
        schema_version="hf4-normal-plot-manifest-1.0", status=overall["status"],
        evidence_coverage=overall, case_coverage=[dict(gamma=c["gamma"], mesh_size_mm=c["mesh_size_mm"],
                                                     **c["coverage"]) for c in cases], input_files=sources.files,
        output_files={p.name: dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
                                  size_bytes=p.stat().st_size) for p in files}))
    print(json.dumps(dict(output=str(output), status=overall["status"], figures=data["figures"],
                          cases=[dict(gamma=c["gamma"], mesh_size_mm=c["mesh_size_mm"],
                                      production_status=c["production_status"], audit_status=c["audit_status"])
                                 for c in cases]), indent=2))
    return data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2]/"hf4_results")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    plot(args.root, args.output)
