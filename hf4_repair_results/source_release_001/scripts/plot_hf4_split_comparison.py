"""Plot archived old/split HF4 paths without evaluating mechanics or references.

Usage: python scripts/plot_hf4_split_comparison.py --new-root NEW_RESULTS
       --old-root OLD_RESULTS --output FRESH_DIRECTORY

Only committed accepted states are connected. Missing runs, failed paths, and
partially audited paths remain explicit; no extrapolation or reference solve
fills missing samples. New u_display is read only for the scale-one shape plot.
All HP metrics come from committed audit rows, never from displayed geometry.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import hashlib
import json
from pathlib import Path
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np


PAIRS = ((0, 0), (0, 1), (1, 0), (1, 1))
COLORS = {"old": "#6e7380", "new": "#126f9b", "hp_new": "#17847b",
          "hp_old": "#9b6c94", "finite": "#c57924", "hard": "#252c34"}
LOG_FLOOR = 1e-18  # Rendering only; zero and exact decimal values remain saved.


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, obj):
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(obj, ensure_ascii=False, indent=2,
                                    allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


class Sources:
    def __init__(self, new_root, old_root):
        self.roots = {"new": new_root, "old": old_root}
        self.files = {}

    def key(self, path):
        for name, root in self.roots.items():
            if path.is_relative_to(root):
                return name + "/" + path.relative_to(root).as_posix()
        if path == Path(__file__).resolve():
            return "implementation/" + path.name
        raise ValueError("plot input is outside the supplied evidence roots")

    def bind(self, path, expected=None):
        path = Path(path).resolve()
        key, digest = self.key(path), sha(path)
        if expected is not None and expected != digest:
            raise ValueError("input SHA256 mismatch: " + key)
        row = dict(sha256=digest, bytes=path.stat().st_size)
        if self.files.setdefault(key, row) != row:
            raise ValueError("input changed during plotting: " + key)
        return path

    def read_json(self, path, expected=None):
        return json.loads(self.bind(path, expected).read_text(encoding="utf-8-sig"))

    def read_npz(self, path, expected=None):
        with np.load(self.bind(path, expected), allow_pickle=False) as archive:
            arrays = {key: archive[key] for key in archive.files}
        for key, value in arrays.items():
            if value.dtype.kind not in "biuf" or not np.all(np.isfinite(value)):
                raise ValueError("nonfinite/nonnumeric plotting input: " + key)
        return arrays

    def verify(self):
        for key, row in list(self.files.items()):
            kind, relative = key.split("/", 1)
            path = Path(__file__).resolve() if kind == "implementation" else self.roots[kind]/relative
            self.bind(path, row["sha256"])


def child(directory, name):
    path = (directory/name).resolve()
    if path.parent != directory.resolve():
        raise ValueError("state/commit path escapes its evidence directory")
    return path


def decimal(value):
    result = Decimal.from_float(value) if isinstance(value, float) else Decimal(value)
    if not result.is_finite():
        raise ValueError("nonfinite archived scalar")
    return result


def metric(row, name):
    if row is None:
        return None
    found = [q for q in row["checks"] if q["name"] == name]
    if len(found) > 1:
        raise ValueError("duplicate audit metric: " + name)
    return found[0] if found else None


def metric_ratio(row, name):
    item = metric(row, name)
    if item is None:
        return None
    with localcontext() as ctx:
        ctx.prec = 100
        bound = decimal(item["bound"])
        if bound <= 0:
            raise ValueError("nonpositive error normalization bound")
        return str(decimal(item["value"])/bound)


def read_run(run, version, sources):
    audit = run.with_name(run.name + "_audit")
    summary = sources.read_json(audit/"summary.json")
    expected_schema = "hf4-split-normal-audit-1.0" if version == "new" else "hf4-normal-audit-1.0"
    if summary.get("schema_version") != expected_schema:
        raise ValueError("audit must have its final summary schema; do not plot a running audit")
    recorded_name = str(summary["source_run"]).replace("\\", "/").rstrip("/").split("/")[-1]
    if recorded_name != run.name:
        raise ValueError("audit source_run differs from its adjacent production directory")
    bindings = sources.read_json(audit/"bindings.json")
    normalized = {key.replace("\\", "/"): digest for key, digest in bindings.items()}

    def bound_file(relative, arrays=False):
        # Recorded absolute paths are provenance only. Match the unambiguous
        # run-relative suffix, then read exclusively beneath the CLI root.
        suffix = run.name + "/" + relative
        matches = [digest for key, digest in normalized.items()
                   if key == suffix or key.endswith("/" + suffix)]
        if len(matches) != 1:
            raise ValueError("audit binding is missing/ambiguous: " + suffix)
        return (sources.read_npz if arrays else sources.read_json)(run/relative, matches[0])

    meta = bound_file("metadata.json")
    result = bound_file("result.json")
    index = bound_file("steps/index.json")
    model = bound_file("model.npz", arrays=True)
    expected_meta = "hf4-split-normal-evidence-1.0" if version == "new" else "hf4-normal-evidence-1.0"
    if meta["schema_version"] != expected_meta:
        raise ValueError("unexpected production metadata schema")
    if version == "new" and (meta["execution_scope"] != "full_path"
                              or meta["requested_targets"] != meta["task"]["targets_mm"]):
        raise ValueError("first-target probe cannot stand in for a full-path comparison")
    entries, rows = index["steps"], summary["rows"]
    if (index["accepted_count"] != len(entries) or summary["accepted_count"] != len(entries)
            or len(result["accepted_steps"]) != len(entries)
            or summary["states_completed"] != len(rows) or len(rows) > len(entries)
            or summary["production_status"] != result["status"]):
        raise ValueError("production/audit state inventory differs")
    if summary["status"] == "pass" and (len(rows) != len(entries)
            or result["status"] != "success" or any(row["status"] != "pass" for row in rows)):
        raise ValueError("audit pass lacks complete passing evidence")
    audited = {}
    for i, row in enumerate(rows):
        if row["index"] != i or row["d"] != entries[i]["d"]:
            raise ValueError("audit rows are not the accepted-state prefix")
        commit = sources.read_json(audit/f"commit_{i:04d}.json")
        required = {f"state_{i:04d}.json", f"hp50_{i:04d}.json", f"reference_{i:04d}.json"}
        if row.get("crosscheck_relative") is not None:
            required.add(f"hp80_{i:04d}.json")
        if set(commit) != required:
            raise ValueError("audit commitment omits or adds state evidence")
        for name, digest in commit.items():
            sources.bind(child(audit, name), digest)
        if sources.read_json(audit/f"state_{i:04d}.json") != row:
            raise ValueError("summary differs from committed audit row")
        for check in row["checks"]:
            if (decimal(check["value"]) <= decimal(check["bound"])) != (check["status"] == "pass"):
                raise ValueError("archived check status differs from its values")
        audited[i] = row

    points, originals, last_arrays = [], [], None
    for i, entry in enumerate(entries):
        if entry["index"] != i:
            raise ValueError("nonsequential accepted-state index")
        scalar_path, array_path = child(run/"steps", entry["metadata"]), child(run/"steps", entry["file"])
        scalar = bound_file("steps/" + scalar_path.name)
        sources.bind(scalar_path, entry["metadata_sha256"])
        # Bind every NPZ twice independently: audited inputs and producer index.
        # Only the last accepted NPZ is retained for the shape panel.
        arrays = bound_file("steps/" + array_path.name, arrays=True)
        sources.bind(array_path, entry["arrays_sha256"])
        reported = result["accepted_steps"][i]
        if scalar["index"] != i or scalar["d"] != entry["d"]:
            raise ValueError("step identity differs from production index")
        for key in ("d", "is_original_target", "original_target_displacement", "bisection_depth"):
            if scalar[key] != reported[key]:
                raise ValueError("result/step target identity differs")
        if scalar["is_original_target"]:
            originals.append(scalar["d"])
        row = audited.get(i)
        if row and float(row["force_N"]) != scalar["drive_force"]:
            raise ValueError("audit/production force differs")
        point = dict(index=i, d_mm=scalar["d"], force_N=scalar["drive_force"],
                     gap_mm=scalar["gap_mm"], production_relative_residual=scalar["relative_residual"],
                     production_residual_scale_N=scalar["residual_scale"],
                     production_minimum_J=scalar["minimum_J"],
                     original_target_displacement=scalar["original_target_displacement"],
                     is_original_target=scalar["is_original_target"], bisection_depth=scalar["bisection_depth"],
                     audit_status=row["status"] if row else "not_audited", audit_row=row,
                     force_reference_error_over_bound=metric_ratio(row, "force_vs_finite_medium_reference"),
                     gap_reference_error_over_bound=metric_ratio(row, "gap_vs_finite_medium_reference"),
                     hp_relative_residual=row["hp_relative_residual"] if row else None,
                     evaluation_full=metric(row, "evaluation_internal_force"),
                     evaluation_free=metric(row, "free_evaluation_internal_force"),
                     production_arrays_source=sources.key(array_path), production_scalar_source=sources.key(scalar_path))
        for key in ("d_mm", "force_N", "gap_mm", "production_relative_residual", "production_residual_scale_N"):
            decimal(point[key])
        points.append(point)
        last_arrays = arrays
    if any(b["d_mm"] <= a["d_mm"] for a, b in zip(points, points[1:])):
        raise ValueError("accepted path is not strictly increasing")
    targets = meta["task"]["targets_mm"]
    if result["status"] == "success" and (originals != targets or not result["target_reached"]
            or result["target_metrics"] is None or result["target_metrics"]["d"] != targets[-1]):
        raise ValueError("successful path did not reach every original target")
    if result["status"] != "success" and (result["target_reached"] or result["target_metrics"] is not None):
        raise ValueError("failed path cannot publish successful terminal metrics")
    gi, mi = meta["gamma_index"], meta["mesh_index"]
    if (gi, mi) not in PAIRS:
        raise ValueError("unexpected combination")
    if meta["task"]["gamma"] != meta["spec"]["gammas"][gi] or meta["task"]["mesh_size_mm"] != meta["spec"]["mesh_sizes_mm"][mi]:
        raise ValueError("combination metadata differs from frozen spec")
    shape = None
    if last_arrays is not None:
        coords, conn, bodies = model["coordinates"], model["connectivity"], model["body_ids"]
        u = last_arrays["u_display"] if version == "new" else last_arrays["u"]
        if (coords.ndim != 2 or coords.shape[1] != 2 or conn.ndim != 2 or conn.shape[1] != 4
                or conn.dtype.kind not in "iu" or np.any(conn < 0) or np.any(conn >= len(coords))
                or bodies.shape != (len(conn),) or not np.all(np.isin(bodies, [0, 1, 2]))
                or u.shape != (2*len(coords),) or u.dtype != np.dtype("float64")):
            raise ValueError("invalid archived mesh/display displacement")
        if version == "new":
            if not np.array_equal(u, last_arrays["u_lift"] + last_arrays["u_fluctuation"]):
                raise ValueError("u_display is not the saved rounded two-array projection")
        shape = dict(reference_coordinates=coords, deformed_coordinates=coords + u.reshape(-1, 2),
                     display_displacement=u, connectivity=conn, body_ids=bodies)
    case = dict(version=version, gamma_index=gi, mesh_index=mi, gamma=meta["task"]["gamma"],
                mesh_size_mm=meta["task"]["mesh_size_mm"], geometry=meta["task"]["geometry"],
                source_run=sources.key(run/"metadata.json").rsplit("/", 1)[0],
                production_status=result["status"], audit_status=summary["status"],
                failure=result.get("failure"), requested_targets_mm=targets,
                accepted_original_targets_mm=originals, missing_original_targets_mm=[d for d in targets if d not in originals],
                accepted_states=len(points), audited_states=len(rows),
                last_accepted_d_mm=points[-1]["d_mm"] if points else None,
                production_tolerance=meta["settings"]["tolerance"],
                hp_tolerance=meta["spec"]["numerical_criteria"]["hp_relative_residual"],
                evaluation_tolerance=meta["spec"]["numerical_criteria"]["force_evaluation_relative_budget"],
                spec_sha256=meta["spec_sha256"], points=points)
    return case, shape


def load_all(new_root, old_root, sources):
    cases, shapes = {}, {}
    for version, root in (("old", old_root), ("new", new_root)):
        found = {}
        for run in sorted(root.iterdir()):
            match = re.fullmatch(r"g([01])_m([01])_\d+", run.name)
            if run.is_dir() and match:
                pair = tuple(map(int, match.groups()))
                if pair in found:
                    raise ValueError("multiple runs for one pair; supply an unambiguous evidence root")
                found[pair] = run
        for pair in PAIRS:
            if pair in found:
                case, shape = read_run(found[pair], version, sources)
                if (case["gamma_index"], case["mesh_index"]) != pair:
                    raise ValueError("directory name and run metadata disagree")
                cases[(version, *pair)], shapes[(version, *pair)] = case, shape
            else:
                cases[(version, *pair)], shapes[(version, *pair)] = None, None
    present = [case for case in cases.values() if case]
    if not present:
        raise ValueError("no archived runs were found")
    if len({case["spec_sha256"] for case in present}) != 1:
        raise ValueError("new/old paths do not share the frozen physical spec")
    for pair in PAIRS:
        old, new = cases[("old", *pair)], cases[("new", *pair)]
        if old and new:
            for field in ("gamma", "mesh_size_mm", "geometry", "requested_targets_mm",
                          "production_tolerance", "hp_tolerance", "evaluation_tolerance"):
                if old[field] != new[field]:
                    raise ValueError("new/old comparison changes " + field)
    return cases, shapes


def case_title(cases, pair):
    case = cases[("new", *pair)] or cases[("old", *pair)]
    return (f"gamma = {case['gamma']:.0e}  |  h = {case['mesh_size_mm']:g} mm"
            if case else f"g{pair[0]} m{pair[1]}: no archived run")


def coverage(case, prefix):
    if case is None:
        return prefix + ": no archived run"
    return (f"{prefix}: {case['production_status']}; {len(case['accepted_original_targets_mm'])}/"
            f"{len(case['requested_targets_mm'])} targets; HP {case['audited_states']}/{case['accepted_states']} "
            f"({case['audit_status']})")


def axes_style(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(True, which="major", color="#d8dfe5", linewidth=.65, alpha=.7)
    ax.set_axisbelow(True)
    ax.tick_params(labelsize=9)


def line(ax, points, key, *, color, marker, label=None, dashed=False, log=False):
    # Preserve missing HP evidence as NaN gaps, rather than joining over it.
    xx, yy = [], []
    for point in points:
        value = point.get(key)
        xx.append(point["d_mm"])
        yy.append(np.nan if value is None else max(float(value), LOG_FLOOR) if log else float(value))
    ax.plot(xx, yy, color=color, marker=marker, markersize=6.2 if marker == "s" else 4.2, linewidth=1.35,
            markerfacecolor="white" if dashed else color, markeredgewidth=.85,
            linestyle="--" if dashed else "-", label=label, zorder=3 if dashed else 4)


def finish(fig, path, title, subtitle, handles, footer, *, legend_y=.905):
    fig.suptitle(title, x=.035, y=.988, ha="left", fontsize=19, weight="bold", color="#1f3448")
    fig.text(.035, .933, subtitle, fontsize=10, color="#526476")
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(.5, legend_y),
               ncol=min(len(handles), 5), frameon=False, fontsize=9)
    fig.text(.035, .014, footer, fontsize=9, color="#526476", va="bottom")
    fig.savefig(path, dpi=250, facecolor="white")
    plt.close(fig)


def response_plot(cases, output):
    fig, axes = plt.subplots(2, 4, figsize=(18, 9))
    fig.subplots_adjust(left=.06, right=.985, top=.79, bottom=.10, hspace=.29, wspace=.27)
    for column, pair in enumerate(PAIRS):
        top, bottom = axes[:, column]
        top.set_title(case_title(cases, pair), fontsize=11, loc="left", pad=31)
        status = coverage(cases[("old", *pair)], "Old") + "\n" + coverage(cases[("new", *pair)], "Split")
        top.text(0, 1.01, status, transform=top.transAxes, fontsize=7.5, va="bottom", color="#526476")
        references = {}
        for version in ("old", "new"):
            case = cases[(version, *pair)]
            if case is None:
                continue
            for point in case["points"]:
                if point["audit_row"] is not None:
                    references[point["d_mm"]] = point["audit_row"]
            for ax, key in ((top, "force_N"), (bottom, "gap_mm")):
                line(ax, case["points"], key, color=COLORS[version], marker="s" if version == "old" else "o", dashed=version == "old")
                failed = [p for p in case["points"] if p["audit_status"] not in ("pass", "not_audited")]
                if failed:
                    ax.scatter([p["d_mm"] for p in failed], [p[key] for p in failed], c="#b93832", marker="x", s=45, zorder=7)
        samples = sorted(references.values(), key=lambda row: row["d"])
        for ax, quantity in ((top, "force_N"), (bottom, "gap_mm")):
            for reference, style in (("finite", ":"), ("hard", "-.")):
                ax.plot([r["d"] for r in samples], [float(r[reference + "_" + quantity]) for r in samples],
                        color=COLORS[reference], linestyle=style, linewidth=1.1, zorder=2)
            ax.set_xlim(-.008, .39)
            axes_style(ax)
        top.set_yscale("symlog", linthresh=1e-8, linscale=.8)
        bottom.set_yscale("symlog", linthresh=1e-6, linscale=.8)
        top.set_ylabel("Bottom-platen force on model [N]" if column == 0 else "")
        bottom.set_ylabel("Interface gap [mm]" if column == 0 else "")
        bottom.set_xlabel("Prescribed bottom displacement d [mm]")
    handles = [Line2D([], [], color=COLORS["old"], marker="s", mfc="white", ls="--", label="Old: accepted states"),
               Line2D([], [], color=COLORS["new"], marker="o", label="Split: accepted states"),
               Line2D([], [], color=COLORS["finite"], ls=":", label="Finite-gamma reference (saved samples)"),
               Line2D([], [], color=COLORS["hard"], ls="-.", label="Ideal hard contact (saved samples)")]
    finish(fig, output/"force_gap_comparison.png", "Normal contact: old and retained-state paths",
           "Positive force is the bottom platen acting on the model. No local pressure is inferred.", handles,
           "Lines connect archived samples only. Symlog linear regions: force +/-1e-8 N; gap +/-1e-6 mm. Missing paths are never extended.")


def validation_plot(cases, output, reference=False):
    fig, axes = plt.subplots(2, 4, figsize=(18, 8.8))
    fig.subplots_adjust(left=.065, right=.985, top=.805, bottom=.115, hspace=.28, wspace=.28)
    for column, pair in enumerate(PAIRS):
        top, bottom = axes[:, column]
        top.set_title(case_title(cases, pair), fontsize=11, loc="left", pad=12)
        if reference:
            bottom.set_title(case_title(cases, pair), fontsize=11, loc="left", pad=12)
        representative = cases[("new", *pair)] or cases[("old", *pair)]
        for version in ("old", "new"):
            case = cases[(version, *pair)]
            if case is None:
                continue
            points = case["points"]
            if reference:
                line(top, points, "force_reference_error_over_bound", color=COLORS[version], marker="s" if version == "old" else "o", dashed=version == "old", log=True)
                line(bottom, points, "gap_reference_error_over_bound", color=COLORS[version], marker="s" if version == "old" else "o", dashed=version == "old", log=True)
            else:
                line(top, points, "production_relative_residual", color=COLORS[version], marker="s" if version == "old" else "o", dashed=version == "old", log=True)
                line(top, points, "hp_relative_residual", color=COLORS["hp_" + version], marker="d", dashed=True, log=True)
                for point in points:
                    for key in ("evaluation_full", "evaluation_free"):
                        point[key + "_value"] = None if point[key] is None else point[key]["value"]
                line(bottom, points, "evaluation_full_value", color=COLORS[version], marker="s" if version == "old" else "o", dashed=version == "old", log=True)
                line(bottom, points, "evaluation_free_value", color=COLORS["hp_" + version], marker="d", dashed=True, log=True)
        for ax in (top, bottom):
            ax.set_yscale("log")
            ax.set_xlim(-.008, .39)
            ax.set_ylim(bottom=LOG_FLOOR/2)
            axes_style(ax)
        if reference:
            for ax in (top, bottom):
                ax.axhline(1, color="#ac4d2d", ls="--", lw=1.15)
                ax.set_ylim(top=max(3, ax.get_ylim()[1]))
            top.set_ylabel("Force error / frozen tolerance" if column == 0 else "")
            bottom.set_ylabel("Gap error / frozen tolerance" if column == 0 else "")
        elif representative:
            top.axhline(float(representative["production_tolerance"]), color="#222d37", ls="--", lw=1.15)
            top.axhline(float(representative["hp_tolerance"]), color="#ac4d2d", ls=":", lw=1.6)
            bottom.axhline(float(representative["evaluation_tolerance"]), color="#222d37", ls="--", lw=1.15)
            top.set_ylim(top=max(3e-8, top.get_ylim()[1]))
            bottom.set_ylim(top=max(3e-9, bottom.get_ylim()[1]))
            top.set_ylabel("Free residual norm / SF" if column == 0 else "")
            bottom.set_ylabel("Production - HP force norm / HP SF" if column == 0 else "")
        bottom.set_xlabel("Accepted displacement d [mm]")
    if reference:
        handles = [Line2D([], [], color=COLORS[v], marker="s" if v == "old" else "o", ls="--" if v == "old" else "-", label=v.title()) for v in ("old", "new")]
        handles.append(Line2D([], [], color="#ac4d2d", ls="--", label="Original finite-reference bound = 1"))
        finish(fig, output/"finite_reference_agreement.png", "Agreement with the independent finite-medium reference",
               "Absolute force and gap differences are normalized by their original, state-specific frozen bounds.", handles,
               "Reference values and errors are archived audit results, not recomputed here. Zero / below-display-floor values are shown at 1e-18; raw values are retained.")
    else:
        handles = [Line2D([], [], color=COLORS[v], marker="s" if v == "old" else "o", ls="--" if v == "old" else "-", label=v.title() + " production / full error") for v in ("old", "new")]
        handles += [Line2D([], [], color=COLORS["hp_" + v], marker="d", ls="--", label=v.title() + " HP / free error") for v in ("old", "new")]
        handles += [Line2D([], [], color="#222d37", ls="--", label="Original 1e-9 production / evaluation gate"),
                    Line2D([], [], color="#ac4d2d", ls=":", label="Original 1e-8 HP equilibrium gate")]
        finish(fig, output/"numerical_validation.png", "Separate acceptance and arithmetic accuracy gates",
               "Top: archived production and independent HP equilibrium. Bottom: full/free internal-force evaluation differences.", handles,
               "Zero / below-display-floor values are shown at 1e-18. Missing HP/free-error metrics remain gaps; no old free-error estimate is invented.", legend_y=.922)


def deformation_plot(cases, shapes, output):
    fig = plt.figure(figsize=(13.8, 12))
    grid = fig.add_gridspec(4, 4, height_ratios=(1, .18, 1, .18),
                           left=.065, right=.985, top=.815, bottom=.075,
                           hspace=.18, wspace=.28)
    axes = np.array([[fig.add_subplot(grid[2*row, col]) for col in range(4)]
                     for row in range(2)])
    caption_axes = np.array([[fig.add_subplot(grid[2*row+1, col]) for col in range(4)]
                             for row in range(2)])
    for caption_ax in caption_axes.flat:
        caption_ax.set_axis_off()
    cmap = ListedColormap(["#e5b45c", "#6f9fb8", "#92b7aa"])
    norm = BoundaryNorm([-.5, .5, 1.5, 2.5], cmap.N)
    saved = {}
    for row, version in enumerate(("old", "new")):
        for col, pair in enumerate(PAIRS):
            ax, key = axes[row, col], (version, *pair)
            case, shape = cases[key], shapes[key]
            title = (("Old" if version == "old" else "Split")
                     + (f" | gamma = {case['gamma']:.0e}\nh = {case['mesh_size_mm']:g} mm"
                        if case else f" | g{pair[0]} m{pair[1]}"))
            ax.set_title(title, fontsize=9.2, loc="left", pad=10)
            if case is None or shape is None:
                ax.text(.5, .5, "No accepted state", transform=ax.transAxes, ha="center", color="#8b4a40")
                ax.set_axis_off()
                continue
            coords, conn = shape["deformed_coordinates"], shape["connectivity"]
            collection = PolyCollection(coords[conn], array=shape["body_ids"].astype(float),
                                        cmap=cmap, norm=norm, edgecolors="#ffffff88", linewidths=.25)
            ax.add_collection(collection)
            geometry = case["geometry"]
            width = geometry["width_mm"]
            height = geometry["lower_height_mm"] + geometry["gap_mm"] + geometry["upper_height_mm"]
            ax.plot([0, width, width, 0, 0], [0, 0, height, height, 0], color="#536474", ls=":", lw=.8)
            ax.set_aspect("equal", adjustable="box")
            ax.set_xlim(-.12, width + .12)
            ax.set_ylim(-.08, height + .08)
            ax.set_xlabel("x [mm]", fontsize=9)
            ax.set_ylabel("y [mm]" if col == 0 else "", fontsize=9)
            axes_style(ax)
            last = case["points"][-1]
            caption = (f"d = {last['d_mm']:g} mm; gap = {last['gap_mm']:.3g} mm\n"
                       f"{case['production_status']}; {len(case['accepted_original_targets_mm'])}/{len(case['requested_targets_mm'])} targets; HP {case['audit_status']}")
            caption_axes[row, col].text(.5, .5, caption, fontsize=8,
                                       ha="center", va="center", color="#526476")
            prefix = f"{version}_g{pair[0]}_m{pair[1]}_"
            saved.update({prefix + field: value for field, value in shape.items()})
    np.savez_compressed(output/"deformation_coordinates.npz", **saved)
    handles = [Patch(color=cmap(i), label=label) for i, label in enumerate(("Third medium", "Lower elastic block", "Upper elastic block"))]
    handles.append(Line2D([], [], color="#536474", ls=":", label="Undeformed exterior"))
    finish(fig, output/"last_accepted_deformations.png", "Last accepted states at true geometric scale",
           "Coordinates + display displacement; magnification = 1. Colors identify material regions, not stress or pressure.", handles,
           "Each panel uses its own actual last accepted d. Thin gaps may be smaller than a pixel; their archived values are printed, not enlarged.")


def main(new_root, old_root, output):
    new_root, old_root, output = Path(new_root).resolve(), Path(old_root).resolve(), Path(output).resolve()
    if new_root == old_root:
        raise ValueError("new and old evidence roots must differ")
    sources = Sources(new_root, old_root)
    sources.bind(Path(__file__).resolve())
    cases, shapes = load_all(new_root, old_root, sources)
    output.mkdir(parents=True, exist_ok=False)
    plt.rcParams.update({"font.family": "DejaVu Sans", "axes.labelcolor": "#344a5f",
                         "text.color": "#263b4d", "axes.titlesize": 11, "savefig.facecolor": "white"})
    response_plot(cases, output)
    validation_plot(cases, output)
    validation_plot(cases, output, reference=True)
    deformation_plot(cases, shapes, output)
    present = [cases[(version, *pair)] for version in ("old", "new") for pair in PAIRS]
    data = dict(schema_version="hf4-split-comparison-plot-data-1.0",
                created_utc=datetime.now(timezone.utc).isoformat(),
                scope="Saved uniform normal-contact evidence only; this plot is not a new acceptance decision.",
                meanings=dict(force="bottom platen on model, compression positive, N",
                              gap="archived interface separation in mm", display_scale=1,
                              shape_color="body_ids: 0 third medium, 1 lower block, 2 upper block",
                              hp="committed Decimal-reference metrics; never evaluated from u_display"),
                rendering=dict(log_floor=LOG_FLOOR, missing_metrics="NaN gaps, not interpolated",
                               reference_curves="segments between saved reference samples only"),
                cases=present, missing_runs=[f"{v}/g{g}_m{m}" for (v,g,m), case in cases.items() if case is None])
    write_json(output/"plot_data.json", data)
    columns = ("version", "gamma_index", "mesh_index", "gamma", "mesh_size_mm", "index", "d_mm",
               "force_N", "gap_mm", "production_relative_residual", "hp_relative_residual",
               "force_reference_error_over_bound", "gap_reference_error_over_bound", "evaluation_full_value",
               "evaluation_free_value", "is_original_target", "bisection_depth", "audit_status")
    with (output/"plot_data.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for case in present:
            if case:
                for point in case["points"]:
                    writer.writerow({key: point.get(key, case.get(key)) for key in columns})
    sources.verify()
    write_json(output/"raw_source_hashes.json", dict(schema_version="hf4-plot-source-hashes-1.0",
                path_policy="new/ and old/ are relative to the supplied roots; recorded audit absolute paths are provenance only",
                files=sources.files, unchanged_at_end=True))
    artifacts = {path.name: dict(sha256=sha(path), bytes=path.stat().st_size)
                 for path in sorted(output.iterdir()) if path.is_file()}
    manifest = dict(schema_version="hf4-split-comparison-plot-manifest-1.0", status="rendered",
                    numerical_evaluations=0, reference_solves=0, production_acceptance_created=False,
                    input_files=len(sources.files), artifacts=artifacts,
                    coverage=[dict(version=c["version"], gamma_index=c["gamma_index"], mesh_index=c["mesh_index"],
                                   production_status=c["production_status"], audit_status=c["audit_status"],
                                   accepted_states=c["accepted_states"], audited_states=c["audited_states"],
                                   missing_original_targets_mm=c["missing_original_targets_mm"]) for c in present if c])
    write_json(output/"plot_manifest.json", manifest)
    print(json.dumps(dict(status="rendered", output=str(output), png_count=4,
                          input_files=len(sources.files)), ensure_ascii=False), flush=True)
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--new-root", type=Path, required=True)
    parser.add_argument("--old-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    main(args.new_root, args.old_root, args.output)
