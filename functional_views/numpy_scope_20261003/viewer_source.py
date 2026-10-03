"""Visualize saved NumPy scope results and one saved terminal state; no solve."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.colors import LogNorm
from matplotlib.patches import Rectangle
import numpy as np


COMPONENTS = ("total_force", "material_force", "regularization_force",
              "total_tangent", "material_tangent", "regularization_tangent")
LABELS = ("Total F", "Material F", "Regularization F", "Total K v", "Material K v", "Regularization K v")
COLORS = ("#0072B2", "#D55E00", "#009E73")


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_npz(path):
    with np.load(path, allow_pickle=False) as archive:
        return {key: archive[key].copy() for key in archive.files}


def binding(path):
    path = path.resolve()
    repo = Path(__file__).resolve().parents[2]
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return dict(path=path.relative_to(repo).as_posix() if path.is_relative_to(repo) else str(path),
                bytes=path.stat().st_size, sha256=digest)


def ratios(result):
    # A manufactured case has two directions. Keep the worst error for each
    # quantity, including both force observations rather than discarding one.
    if result is None:
        return np.full(6, np.nan)
    return np.array([max(float(c["normalized_error"]) / float(c["limit"])
                         for c in result["comparisons"] if c["component"] == name)
                     for name in COMPONENTS])


def plot_coverage(index, results, output, stops):
    groups = {}
    for row in index["cases"]:
        prefix = row["case"].split("__")[0]
        name = "C1 saved samples" if row["kind"] == "saved" and prefix.startswith("TMC_") else prefix
        groups.setdefault((row["kind"], name), []).append(row)
    manufactured = [key for key in groups if key[0] == "manufactured"]
    saved = [key for key in groups if key[0] == "saved"]
    manufactured.sort(key=lambda key: ("unit", "dyadic_rect", "nondyadic_rect").index(key[1]))
    saved.sort(key=lambda key: (key[1] == "C1 saved samples", key[1]))
    fig = plt.figure(figsize=(21, 16), layout="constrained")
    columns = fig.add_gridspec(1, 2)
    grids = [columns[i].subgridspec(len(keys), 1, height_ratios=[max(8, len(groups[key])) for key in keys])
             for i, keys in enumerate((manufactured, saved))]
    passed = sum(r["status"] == "pass" for r in results.values())
    failed = sum(r["status"] != "pass" for r in results.values())
    expected = len(index["cases"])
    checks = [c for r in results.values() for c in r["comparisons"]]
    candidate_pass = sum(float(c["normalized_error"]) <= float(c["limit"]) for c in checks)
    reference_pass = sum(float(c["hp80_hp120_error"]) <= float(c["reference_limit"]) for c in checks)
    fig.suptitle(f"NumPy full force + assembled mechanical Jacobian | saved reference comparison\n"
                 f"Cases: {passed} pass, {failed} fail, {expected-len(results)} not executed / {expected} expected; "
                 f"candidate gates {candidate_pass}/{len(checks)}, HP80/120 gates {reference_pass}/{len(checks)}",
                 fontsize=17)
    cmap = plt.colormaps["viridis"].copy()
    cmap.set_bad("#dce1e5")
    zero_count = 0
    for column, keys in enumerate((manufactured, saved)):
        for row_index, key in enumerate(keys):
            rows = groups[key]
            values = np.array([ratios(results.get(row["case"])) for row in rows])
            zero_count += int(np.count_nonzero(values == 0))
            shown = np.log10(np.maximum(values, 1e-18))
            ax = fig.add_subplot(grids[column][row_index, 0])
            im = ax.imshow(np.ma.masked_invalid(shown), cmap=cmap, vmin=-16, vmax=0,
                           aspect="auto", interpolation="nearest")
            labels = [(row["case"].replace("TMC_", "") if key[1] == "C1 saved samples" else
                       row["case"].split("__", 1)[1]) for row in rows]
            ax.set(xticks=np.arange(6), xticklabels=LABELS, yticks=np.arange(len(rows)),
                   yticklabels=labels, title=f"{key[0].capitalize()} | {key[1]} | "
                   f"{sum(row['case'] in results for row in rows)}/{len(rows)} observed")
            ax.tick_params(axis="x", labelsize=9)
            ax.tick_params(axis="y", labelsize=9)
            for i, j in zip(*np.where(values > 1)):
                ax.add_patch(Rectangle((j-.5, i-.5), 1, 1, fill=False, edgecolor="#cf2a35", linewidth=2.5))
                ax.text(j, i, f"{values[i, j]:.1e}", color="white", ha="center", va="center", fontsize=7)
            colorbar = fig.colorbar(im, ax=ax, shrink=.8, pad=.02, ticks=[-16, -12, -8, -4, 0])
            colorbar.ax.set_yticklabels(["1e-16", "1e-12", "1e-8", "1e-4", "1 (gate)"])
            colorbar.set_label("Error / limit" if key[1] == "C1 saved samples" else
                              "Normalized error / unchanged original limit", fontsize=9)
    fig.supxlabel("Lower ratios are better. Gray = not executed; red border = ratio > 1. "
                  "Manufactured panels retain the worse of two saved directions.\n"
                  "Color saturation below 1e-16 changes display only; exact zero ratios use a 1e-18 display floor. "
                  "These are stored-state comparisons, not new equilibrium paths.\n"
                  "Historical equilibrium audit status is preserved; static force / K v PASS does not admit a path."
                  + ("\nExecution stop: " + "; ".join(stops) if stops else ""), fontsize=11)
    path = output / "numpy_scope_coverage.png"
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return dict(file=binding(path), displayed_case_count=expected, observed_case_count=len(results),
                candidate_gate_passes=candidate_pass, candidate_gates=len(checks),
                reference_gate_passes=reference_pass, reference_gates=len(checks),
                exact_zero_ratios=zero_count, color_ratio_range=[1e-16, 1.], exact_zero_display_ratio=1e-18)


def plot_terminal(row, result, result_dir, inputs, output):
    model = load_npz(inputs / row["model_file"])
    arrays = load_npz(result_dir / "arrays.npz")
    state = load_npz(inputs / row["state_file"])
    for key in ("u_lift", "u_fluctuation"):
        if not np.array_equal(arrays[key], state[key]):
            raise ValueError("Result differs from displayed two-array state")
    xy, cells = model["coordinates"], model["connectivity"]
    solid = model["solid"].astype(bool)
    u = (state["u_lift"] + state["u_fluctuation"]).reshape(xy.shape)
    position = xy + u
    forces = [arrays[name].reshape(xy.shape) for name in COMPONENTS[:3]]
    J = arrays["J"].reshape((len(cells), -1)).min(axis=1)
    if not all(np.isfinite(a).all() for a in (xy, position, *forces, J)) or np.any(J <= 0):
        raise ValueError("Terminal display requires finite arrays and positive saved J")
    span = max(float(np.ptp(xy[:, 0])), float(np.ptp(xy[:, 1])))
    extent = np.concatenate((xy, position))
    lo, hi = extent.min(axis=0) - .16*span, extent.max(axis=0) + .16*span
    force_max = max(float(np.linalg.norm(force, axis=1).max()) for force in forces)
    arrow_scale = .13*span/force_max if force_max else 1.
    fixed_nodes = np.unique(model["fixed_dofs"].astype(int)//2)
    original_audit = row.get("original_audit_status", "not recorded")
    fig, axes = plt.subplots(2, 3, figsize=(21, 13), layout="constrained")
    fig.suptitle(f"Saved terminal state: {row['case']} | static NumPy force + tangent comparison: {result['status'].upper()}\n"
                 f"Original equilibrium HP audit: {original_audit.upper()} | "
                 f"{len(cells)} Q1 elements, {xy.size} DOFs | actual geometry x1 | no new equilibrium solve",
                 fontsize=17)

    def mesh(ax, undeformed=False):
        if undeformed:
            ax.add_collection(PolyCollection(xy[cells], facecolors="none", edgecolors="#b5bfc7",
                                            linewidths=.25, linestyles="--"))
        ax.add_collection(PolyCollection(position[cells],
                          facecolors=np.where(solid[:, None], [.43, .53, .58, .8], [.84, .91, .94, .28]),
                          edgecolors="#b0bbc2", linewidths=.25))
        ax.set(xlim=(lo[0], hi[0]), ylim=(lo[1], hi[1]), xlabel="x [mm]", ylabel="y [mm]")
        ax.set_aspect("equal", adjustable="box")

    ax = axes[0, 0]
    mesh(ax, undeformed=True)
    ax.add_collection(PolyCollection(position[cells[solid]], facecolors="none", edgecolors="#263b50", linewidths=.5))
    ax.scatter(position[fixed_nodes, 0], position[fixed_nodes, 1], marker="^", s=7, color="#263b50")
    ax.set_title("Solid + background medium, actual deformation\nDashed: initial mesh; triangles: constrained nodes", fontsize=12)
    for ax, force, name, color in zip((axes[0, 1], axes[0, 2], axes[1, 0]), forces,
                                      ("Total", "Material", "Regularization"), COLORS, strict=True):
        mesh(ax)
        shown = force * arrow_scale
        ax.quiver(position[:, 0], position[:, 1], shown[:, 0], shown[:, 1], angles="xy",
                  scale_units="xy", scale=1, color=color, width=.0025)
        maximum = float(np.linalg.norm(force, axis=1).max())
        ax.set_title(f"{name} complete nodal internal force\n"
                     f"Unified arrow scale {arrow_scale:.5g} mm/N; max node norm {maximum:.6g} N", fontsize=12)
    ax = axes[1, 1]
    values = PolyCollection(position[cells], edgecolors="#9ba9b2", linewidths=.2,
                            cmap="viridis", norm=LogNorm(vmin=J.min(), vmax=max(J.max(), J.min()*1.0001)))
    values.set_array(J)
    ax.add_collection(values)
    ax.set(xlim=(lo[0], hi[0]), ylim=(lo[1], hi[1]), xlabel="x [mm]", ylabel="y [mm]")
    ax.set_aspect("equal", adjustable="box")
    fig.colorbar(values, ax=ax, shrink=.65, label="Minimum saved quadrature J per element")
    ax.set_title(f"Positive J on the actual deformed mesh\nMin {J.min():.7g}; max {J.max():.7g}; logarithmic color", fontsize=12)
    ax = axes[1, 2]
    tangent_checks = [c for c in result["comparisons"] if c["component"].endswith("tangent")]
    xs = np.arange(len(tangent_checks))
    errors = np.array([float(c["normalized_error"]) for c in tangent_checks])
    limits = np.array([float(c["limit"]) for c in tangent_checks])
    ratios_array = errors/limits
    ax.scatter(xs, np.maximum(ratios_array, 1e-18), color=COLORS[0], s=60, label="Saved NumPy K v / HP error ratio")
    ax.axhline(1, color="#cf2a35", linestyle="--", label="Unchanged original gate")
    for i, (check, value) in enumerate(zip(tangent_checks, ratios_array, strict=True)):
        ax.annotate(f"{value:.3e}\n{'PASS' if check['pass_gate'] else 'FAIL'}", (i, max(value, 1e-18)),
                    xytext=(0, 10), textcoords="offset points", ha="center", fontsize=10)
    ax.set(xticks=xs, xticklabels=[c["component"].replace("_tangent", "") + f"\ndir {c['direction']}"
                                for c in tangent_checks], yscale="log", ylabel="Normalized error / original limit",
           ylim=(max(1e-20, min(1e-8, float(np.maximum(ratios_array, 1e-18).min())/5)),
                 max(5., float(ratios_array.max())*5)), title="Unsymmetrized assembled CSC Jacobian actions")
    ax.legend(fontsize=9, loc="upper right")
    ax.grid(alpha=.2, which="both", axis="y")
    ax.text(.02, .05, f"Relative matrix asymmetry: {result['matrix_relative_asymmetry']:.6e}\n"
            "Direction perturbs fluctuation; lift stays fixed.\n"
            "Total K gate 1e-10; material/reg gates 1e-9.\n"
            "Each scale is max(||HP80 K v||, 1e-10).", transform=ax.transAxes, fontsize=10)
    fig.supxlabel("All force panels show full DOF internal residual vectors, including constraints and background medium; "
                  "they are not contact pressure or LF clamping force.\n"
                  "Display coordinates use rounded lift + fluctuation; J and force retain saved candidate calculations. "
                  "Historical equilibrium acceptance is not reassessed by this view.", fontsize=11)
    path = output / "numpy_scope_terminal.png"
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return dict(file=binding(path), case=row["case"], status=result["status"],
                original_equilibrium_HP_audit_status=original_audit,
                model=binding(inputs/row["model_file"]), state=binding(inputs/row["state_file"]),
                reference=binding(inputs/row["reference_file"]), result=binding(result_dir/"result.json"),
                arrays=binding(result_dir/"arrays.npz"), matrix=binding(result_dir/"total_matrix.npz"),
                displacement_scale=1., unified_arrow_mm_per_N=arrow_scale, all_nodes_displayed=True,
                minimum_J_per_cell_range=[float(J.min()), float(J.max())])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--results", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--case", default="mesh_h00625__020")
    args = parser.parse_args()
    index_path = args.input/"index.json"
    index = read(index_path)
    index_sha = binding(index_path)["sha256"]
    results, directories, summaries, stops = {}, {}, [], []
    for directory in args.results:
        summary = read(directory/"summary.json")
        if summary["input_index_sha256"] != index_sha:
            raise ValueError("Result summary references a different input index")
        summaries.append(binding(directory/"summary.json"))
        if summary.get("stop"):
            stop = summary["stop"]
            stops.append(f"{stop.get('case', '?')}: {stop['type']} — {stop['message']}")
        for row in summary["cases_summary"]:
            case = row["case"]
            if case in results:
                raise ValueError("Duplicate case across supplied result directories: " + case)
            result = read(directory/case/"result.json")
            if result["case"] != case or result["status"] != row["status"]:
                raise ValueError("Result identity differs from summary")
            results[case], directories[case] = result, directory/case
    known = {row["case"]: row for row in index["cases"]}
    if set(results)-set(known):
        raise ValueError("Result contains an unknown case")
    for case, result in results.items():
        if result["input_identity"] != known[case]:
            raise ValueError("Case input identity differs from prepared index")
    files = {path: row["sha256"] for path, row in index["files"].items()}
    if args.case in results:
        row = known[args.case]
        for name in ("model_file", "state_file", "reference_file"):
            if binding(args.input/row[name])["sha256"] != files[row[name]]:
                raise ValueError("Displayed prepared input identity differs")
    plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False})
    args.output.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(Path(__file__), args.output/"viewer_source.py")
    coverage = plot_coverage(index, results, args.output, stops)
    terminal = (plot_terminal(known[args.case], results[args.case], directories[args.case], args.input, args.output)
                if args.case in results else dict(case=args.case, status="not executed; terminal image not generated"))
    metadata = dict(viewer_source=binding(args.output/"viewer_source.py"), input_index=binding(index_path),
                    result_summaries=summaries,
                    case_results=[binding(directories[case]/"result.json") for case in results],
                    coverage=coverage, terminal=terminal, constitutive_evaluation=False,
                    equilibrium_solved=False, historical_equilibrium_readmitted=False)
    (args.output/"metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False,
        allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps(dict(coverage=coverage["file"]["path"], terminal=terminal.get("file", {}).get("path"))))


if __name__ == "__main__":
    main()
