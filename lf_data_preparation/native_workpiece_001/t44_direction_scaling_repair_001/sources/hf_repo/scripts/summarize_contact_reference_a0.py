"""Combine independent A0 admission with geometry gates and reproducible plots."""
from pathlib import Path
import argparse
from decimal import Decimal, localcontext
from math import fsum
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from hf_eval.contact_audit import audit_rectangle_overlap, strict_valid_prefix
from hf4_common import read_json, read_npz, sha, write_json, timestamp


CASES = ["a0_h025_a000_r1", "a0_h0125_a000", "a0_h025_a0125", "a0_h0125_a0125",
         "a0_h025_a025", "a0_h0125_a025"]


def summarize(root, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    if output.exists():
        raise FileExistsError("refusing to overwrite an existing summary")
    output.mkdir(parents=True)
    protocol = read_json(REPO / "configs/contact_reference_a0_v1.json")
    gates = protocol["audit"]
    runs, bindings, all_checks, plot_data = [], {}, [], []
    for name in CASES:
        run = root / name
        audit = read_json(run / "audit.json")
        index = read_json(run / "steps/index.json")["steps"]
        metadata = read_json(run / "metadata.json")
        result, model = read_json(run / "result.json"), read_npz(run / "model.npz")
        if audit["status"] != "pass" or len(audit["states"]) != len(index):
            raise ValueError("independent admission not passed: " + name)
        for key in ("audit.json", "model.npz", "metadata.json", "steps/index.json", "result.json"):
            bindings[name + "/" + key] = sha(run / key)
        geometry, prefix_input, state_metrics = [], [], []
        for entry, hp in zip(index, audit["states"]):
            file = run / "steps" / entry["file"]
            if sha(file) != entry["sha256"] or hp["index"] != entry["index"] or hp["d"] != entry["d"]:
                raise ValueError("state identity mismatch")
            bindings[name + "/steps/" + entry["file"]] = sha(file)
            arrays = read_npz(file)
            # Accurately round each physical position once for clipping. Bound
            # this rounding against the independently reconstructed Decimal
            # positions; never feed these coordinates back into FE mechanics.
            xy = np.array([[fsum((float(model["coordinates"][i, k]),
                                 float(arrays["u_lift"][2*i+k]),
                                 float(arrays["u_fluctuation"][2*i+k])))
                            for k in (0, 1)] for i in range(len(model["coordinates"]))])
            with localcontext() as ctx:
                ctx.prec = 90
                round_error = max(abs(Decimal.from_float(float(value))-Decimal(ref))
                                  for row, refs in zip(xy, hp["measurements"]["nodal_positions"])
                                  for value, ref in zip(row, refs))
            geom = audit_rectangle_overlap(xy, model["connectivity"], model["solid"],
                    protocol["geometry"]["obstacle_rectangle_mm"],
                    length_tolerance=gates["length_tolerance_mm"],
                    area_tolerance=gates["area_tolerance_mm2"], overlap_tolerance=gates["overlap_tolerance_mm2"])
            # For this horizontal full-width obstacle, the exact HP nodal y
            # bound plus nonnegative Q1 shape functions gives a stronger test
            # than a rounded-coordinate area calculation alone.
            exact_nodal_bound = Decimal(hp["measurements"]["max_nodal_y"]) <= Decimal(1)
            geom.update(index=entry["index"], d=entry["d"],
                        maximum_coordinate_rounding_mm=str(round_error),
                        hp_exact_all_nodes_at_or_below_plane=exact_nodal_bound)
            geometry.append(geom)
            checks = hp["checks"]
            all_checks.extend(checks)
            metric = {c["name"]: float(c["value"]) for c in checks}
            metric.update(d=entry["d"], normal_force_N=float(hp["measurements"]["normal_force"]),
                          nonuniform={k: float(v) for k, v in hp["measurements"]["nonuniform"].items()},
                          overlap_area_mm2=geom["total_overlap_area"],
                          hp_exact_all_nodes_at_or_below_plane=exact_nodal_bound,
                          geometric_rounding_mm=float(round_error))
            state_metrics.append(metric)
            prefix_input.append(dict(id=entry["index"], d=entry["d"],
                solver_valid=metric["production_relative_residual"] <= gates["relative_residual"],
                geometry_valid=bool(geom["geometry_valid"] and exact_nodal_bound
                                    and round_error <= Decimal(str(gates["length_tolerance_mm"]))),
                reference_valid=hp["status"] == "pass", value=metric["normal_force_N"]))
            if entry is index[-1]:
                plot_data.append((metadata["task"], xy, model["connectivity"],
                                  np.array(hp["precision_evidence_decimal"]["80"]["G_decimal"], dtype=float)))
        prefix = strict_valid_prefix(prefix_input)
        runs.append(dict(name=name, task=metadata["task"], independent_status=audit["status"],
                         states=state_metrics, geometry=geometry, prefix=prefix,
                         path_admitted=prefix["prefix_length"] == len(index) and result["status"] == "success"))
    sensitivity = []
    for i in (0, 2, 4):
        coarse, fine = runs[i], runs[i+1]
        differences = [{"d": x["d"], "coarse_force_N": x["normal_force_N"], "fine_force_N": y["normal_force_N"],
                        "relative_coarse_minus_fine": (x["normal_force_N"]-y["normal_force_N"])/abs(y["normal_force_N"])}
                       for x, y in zip(coarse["states"], fine["states"]) if y["d"] > 0]
        sensitivity.append(dict(amplitude=coarse["task"]["amplitude"], states=differences,
                                max_absolute_relative_difference=max(abs(x["relative_coarse_minus_fine"]) for x in differences),
                                interpretation="two-grid sensitivity, not convergence or an error bound"))
    receipts = [read_json(p) for p in root.glob("*.receipt.json")]
    payload = dict(schema="contact_reference_a0_admission_v1", created_utc=timestamp(),
        status="pass" if all(r["path_admitted"] for r in runs) else "not_pass", runs=runs,
        accepted_states=sum(len(r["states"]) for r in runs),
        independent_numeric_checks=len(all_checks), independent_checks_passed=sum(c["status"] == "pass" for c in all_checks),
        geometry_checks=sum(len(r["geometry"]) for r in runs), mesh_sensitivity=sensitivity,
        solve_attempts=sum(Path(r["command"][1]).name == "run_contact_reference_a0.py" for r in receipts),
        audit_attempts=sum(Path(r["command"][1]).name == "audit_contact_reference_a0.py" for r in receipts),
        solve_elapsed_seconds_including_failed_configuration=sum(r["elapsed_seconds"] for r in receipts
                           if Path(r["command"][1]).name == "run_contact_reference_a0.py"),
        subprocess_elapsed_seconds_including_failed_configuration=sum(r["elapsed_seconds"] for r in receipts),
        input_sha256=bindings, source_sha256={"summary_script": sha(__file__),
        "geometry_prefix_module": sha(REPO / "src/hf_eval/contact_audit.py")},
        scope="A0 reference admission only; HF4-C, active-set contact and matched TMC comparison remain open")
    write_json(output / "admission_summary.json", payload)
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.0), constrained_layout=True)
    colors = ["#315b8a", "#b34b31", "#308270"]
    for j, (i, color) in enumerate(zip((0, 2, 4), colors)):
        for k, style in ((i, "--"), (i+1, "-")):
            r = runs[k]
            axes[0].plot([s["d"] for s in r["states"]], [s["normal_force_N"] for s in r["states"]],
                         style, color=color, marker="o" if k == i+1 else None, markersize=3,
                         label=f"a={r['task']['amplitude']}, h={r['task']['h']}")
        sample = sensitivity[j]["states"]
        axes[1].plot([s["d"] for s in sample], [100*s["relative_coarse_minus_fine"] for s in sample],
                     "o-", color=color, markersize=4, label=f"a={runs[i]['task']['amplitude']}")
    for k, r in enumerate(runs):
        axes[2].semilogy([s["d"] for s in r["states"] if s["d"] > 0],
                         [s["hp80_relative_residual"] for s in r["states"] if s["d"] > 0],
                         "o-" if k % 2 else "o--", color=colors[k//2], markersize=3)
    axes[0].set(xlabel="Compression d (mm)", ylabel="Normal force on obstacle (N)", title="A0 full-contact response")
    axes[1].set(xlabel="Compression d (mm)", ylabel="(coarse - fine) / |fine| (%)", title="Two-grid sensitivity (not convergence)")
    axes[2].axhline(1e-9, color="#b34b31", linestyle=":", label="Original 1e-9 gate")
    axes[2].set(xlabel="Compression d (mm)", ylabel="Independent residual / SF", title="80-digit check of saved split states")
    for ax in axes:
        ax.grid(alpha=.2)
        ax.legend(fontsize=7)
    for ext in ("png", "svg"):
        fig.savefig(output / ("a0_force_and_precision." + ext), dpi=180)
    plt.close(fig)
    fig, axes = plt.subplots(1, 3, figsize=(12.5, 4), constrained_layout=True)
    vmax = max(float(np.max(np.abs(g[:, :, 0, 1]))) for _, _, _, g in plot_data)
    for ax, (task, xy, conn, grad) in zip(axes, [plot_data[i] for i in (1, 3, 5)]):
        colors_cell = np.mean(grad[:, :, 0, 1], axis=1)
        collection = PolyCollection(xy[conn], array=colors_cell, cmap="RdBu_r", clim=(-vmax, vmax),
                                    edgecolors="#52616b", linewidths=.25)
        ax.add_collection(collection)
        ax.axhline(1., color="#252f3a", linewidth=3)
        ax.set(xlim=(-.2, 2.2), ylim=(-.05, 1.15), aspect="equal", xlabel="x (mm)", ylabel="y (mm)",
               title=f"a={task['amplitude']}, h={task['h']} mm")
    fig.colorbar(collection, ax=axes, shrink=.7, label="Mean Gxy (dimensionless)")
    fig.suptitle("A0 at d=0.25 mm | actual-scale deformation | rigid plane y=1 mm", fontsize=12)
    for ext in ("png", "svg"):
        fig.savefig(output / ("a0_deformed_shear." + ext), dpi=180)
    plt.close(fig)
    # A hand-computable counterexample plus temporal gating illustration.
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), constrained_layout=True)
    diamond = np.array([[-1., 0.], [0., -1.], [1., 0.], [0., 1.]])
    axes[0].fill(*diamond.T, color="#84accb", alpha=.65)
    axes[0].fill([.25, 1, 1, .25], [.25, .25, 1, 1], color="#f0b987", alpha=.6)
    axes[0].fill([.25, .75, .25], [.25, .25, .75], color="#b34b31", alpha=.9)
    axes[0].scatter(*diamond.T, s=22, color="#315b8a")
    axes[0].set(aspect="equal", title="No Q4 vertex inside; overlap area = 1/8", xlabel="x", ylabel="y")
    sample = [dict(id=i, d=d, solver_valid=True, geometry_valid=(i != 2), reference_valid=True, value=value)
              for i, (d, value) in enumerate(zip([0., 1., 1.5, 2.], [0., 1., 1.5, 2.]))]
    prefix = strict_valid_prefix(sample)
    write_json(output / "negative_examples.json", {"cross_corner_overlap": .125, "prefix_example": prefix,
               "scope": "manufactured semantic examples, not additional FE solves"})
    axes[1].plot([0, 1, 1.5, 2], [0, 1, 1.5, 2], "o--", color="#8895a3", label="Raw observations")
    axes[1].plot([0, 1], [0, 1], "o-", color="#308270", linewidth=3, label="Comparable prefix")
    axes[1].axvline(1.5, color="#b34b31", label="Invalid inserted state")
    axes[1].annotate("Later recovery stays unknown", (2, 2), xytext=(.65, 2.45), fontsize=9,
                     arrowprops={"arrowstyle": "->", "color": "#b34b31"})
    axes[1].set(xlabel="Path displacement", ylabel="Illustrative response", ylim=(-.1, 2.8),
                title="First invalid state ends the valid prefix")
    axes[1].legend(fontsize=8, loc="lower right")
    for ext in ("png", "svg"):
        fig.savefig(output / ("contact_failure_semantics." + ext), dpi=180)
    plt.close(fig)
    print({"status": payload["status"], "states": payload["accepted_states"], "independent_checks": len(all_checks)})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    summarize(args.root, args.output)
