"""Read frozen C2 evidence and plot two narrowly scoped presentation figures.

No constitutive evaluation, equilibrium solve, or change to admission is performed.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    out = args.output.resolve()
    if out.exists():
        raise FileExistsError(f"Refusing to overwrite {out}")
    bindings = {}
    notes = []

    def read(rel):
        path = root / rel
        bindings[path.relative_to(root).as_posix()] = sha(path)
        return json.loads(path.read_text(encoding="utf-8"))

    # These are frozen, source-gated evidence bundles. Bind the manifests and
    # verify their scientific JSON entries; do not rerun any numerical audit.
    summary_dir = "hf4_c2_diagnostics/summary_001"
    analytic_dir = "hf4_c2_diagnostics/analytic_experiments_001"
    fields_dir = "hf4_c2_diagnostics/fields_experiments_001"
    case_file = "hf4_c2_diagnostics_experiments_outer_free.json"
    manifests = {}
    for directory in (summary_dir, analytic_dir, fields_dir):
        manifests[directory] = read(f"{directory}/output_sha256.json")
    if "output_sha256.json" in manifests[summary_dir]:
        notes.append("Frozen summary_001 manifest has a self entry (empty-file hash); that entry is not a valid self-check. Its actual bytes are bound separately here. All consumed scientific JSON entries match their listed hashes.")

    def bound_read(directory, filename):
        obj = read(f"{directory}/{filename}")
        actual = bindings[f"{directory}/{filename}"]
        if manifests[directory][filename] != actual:
            raise ValueError(f"Manifest mismatch: {directory}/{filename}")
        return obj

    summary = bound_read(summary_dir, "summary.json")
    analytic = bound_read(analytic_dir, case_file)
    fields = bound_read(fields_dir, case_file)
    bound_read(analytic_dir, "plan.json")
    bound_read(fields_dir, "plan.json")
    assert analytic["status"] == "pass"
    assert fields["diagnostic_algebra_status"] == "pass"
    assert analytic["state_id"] == fields["state_id"] == "uniform_tmc:18"
    assert Decimal(fields["physical_mean_drive"]) == Decimal("0.5")

    runs = {r["case_id"]: r for r in summary["runs"]}
    records = []
    for case in ("baseline_h025", "baseline_h0125", "mesh_h00625"):
        run = runs[case]
        assert run["source_and_detail_chain_valid"]
        target = next(t for t in run["targets"] if Decimal(t["d_mm"]) == Decimal("0.375"))
        assert target["accepted"] and target["comparable"]
        m = target["measurement"]
        records.append({
            "case_id": case, "h_mm": run["spec"]["h_mm"],
            "whole_path_status": run["status"], "whole_path_admitted": run["admitted"],
            "d_mm": target["d_mm"], "target_comparable": True,
            "normal_top_N": m["normal_top_N"],
            "negative_node_count": m["negative_node_count"],
            "negative_sum_N": m["negative_sum_N"],
            "negative_magnitude_N": m["negative_magnitude_N"],
            "left_hat": m["functionals"]["left_hat"],
            "right_hat": m["functionals"]["right_hat"],
        })
    assert records[-1]["whole_path_status"] == "failed"
    node_by_id = {n["node_id"]: n for n in analytic["all_top_nodes"]}
    field_by_id = {n["node_id"]: n for n in fields["all_top_nodes"]}
    far_nodes = []
    for node in analytic["all_top_nodes"]:
        x = node["reference_x_mm"]
        if x <= -1.5 or x >= 3.5:
            f = field_by_id[node["node_id"]]
            assert Decimal(f["total_on_plane_N"]) == Decimal(node["weak_total_on_plane_N"])
            far_nodes.append(dict(node, current_coordinate_mm=f["current_coordinate_mm"]))
    edges = []
    for edge in analytic["analytic_edges_HP120"]:
        x0 = node_by_id[edge["left_node"]]["reference_x_mm"]
        x1 = node_by_id[edge["right_node"]]["reference_x_mm"]
        if not (x1 <= -1.5 or x0 >= 3.5):
            continue
        eps = edge["endpoints"]
        p = [Decimal(e["P"][1][1]) for e in eps]
        assert all(Decimal(e["F"][1][0]) == 0 for e in eps)
        assert Decimal(eps[0]["F"][0][0]) == Decimal(eps[1]["F"][0][0]) > 0
        assert all(Decimal(e["F"][1][1]) > 0 for e in eps)
        assert Decimal(edge["lam"]) >= 0 and Decimal(edge["mu"]) > 0
        sign = "entire_edge_tension" if min(p) > 0 else "entire_edge_compression" if max(p) < 0 else "single_sign_change_or_endpoint_zero"
        edges.append({"element": edge["element"], "reference_x_mm": [x0, x1],
                      "endpoint_Pyy_MPa": [str(v) for v in p], "material_sign": sign,
                      "endpoint_F": [e["F"] for e in eps]})

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "axes.titleweight": "semibold", "svg.fonttype": "none"})
    colors = ["#23649C", "#2A8B80", "#C07124"]
    out.mkdir(parents=True)
    fig, axs = plt.subplots(2, 2, figsize=(11.5, 8.2))
    labels = ["0.25", "0.125", "0.0625\nvalid prefix only"]
    for i, record in enumerate(records):
        for name, dx, marker in (("left_hat", -.055, "o"), ("right_hat", .055, "s")):
            y = float(record[name]["values_N"]["total"]) * 1000
            axs[0, 0].scatter(i+dx, y, s=65, marker=marker,
                              facecolors="none" if i == 2 else colors[i], edgecolors=colors[i], linewidths=1.6)
        axs[0, 1].bar(i, float(record["negative_magnitude_N"]) * 1000,
                      color=colors[i], alpha=.85, hatch="//" if i == 2 else None)
        axs[1, 0].bar(i, record["negative_node_count"], color=colors[i], alpha=.85,
                      hatch="//" if i == 2 else None)
        axs[1, 1].scatter(i, float(record["normal_top_N"]["total"]), s=70,
                          facecolors="none" if i == 2 else colors[i], edgecolors=colors[i], linewidths=1.6)
        axs[1, 1].annotate(f"{float(record['normal_top_N']['total']):.9f}",
                           (i, float(record["normal_top_N"]["total"])), xytext=(0, 10),
                           textcoords="offset points", ha="center", fontsize=9)
    titles = ["Fixed-support weak reactions: left (circle), right (square)",
              "Magnitude of the sum of negative weak nodes", "Number of negative weak nodes", "Net top weak reaction"]
    units = ["Signed weighted reaction (mN)", "Negative magnitude (mN)", "Node count", "Net reaction (N)"]
    for ax, title, unit in zip(axs.flat, titles, units):
        ax.set_title(title, fontsize=10)
        ax.set_ylabel(unit)
        ax.set_xticks(range(3), labels)
        ax.set_xlabel("Mesh spacing h (mm)")
        ax.set_xlim(-.5, 2.5)
        ax.grid(axis="y", alpha=.18)
    axs[0, 0].axhline(0, color=".5", lw=.7)
    axs[1, 1].ticklabel_format(axis="y", style="plain", useOffset=False)
    axs[1, 1].margins(y=.3)
    fig.suptitle("C2 | same original target d = 0.375 mm | saved HP80 weak forces", fontsize=15, y=.98)
    fig.text(.5, .025, "h = 0.0625: whole path FAILED at d = 0.5; shown state lies within its valid prefix.\n"
             "Fixed hats: [-0.5, -0.25, 0] and [2, 2.25, 2.5] mm, heights [0, 1, 0]. Mesh sensitivity only; no convergence claim.",
             ha="center", va="bottom", fontsize=9)
    fig.tight_layout(rect=(0, .105, 1, .95), h_pad=1.8)
    for ext in ("png", "svg"):
        fig.savefig(out / f"common_target_three_meshes.{ext}", dpi=180)
    plt.close(fig)

    fig, axs = plt.subplots(2, 2, figsize=(11.5, 8.2), sharex="col")
    styles = [("weak_total_on_plane_N", "Weak total", "#222222", "o"),
              ("weak_material_on_plane_N", "Weak material", "#23649C", "s"),
              ("regularization_weak_on_plane_N", "Weak regularization", "#B76823", "^"),
              ("analytic_material_edge_on_plane_N", "Direct analytic material", "#228467", "D")]
    for col, (low, high, side) in enumerate(((-2, -1.5, "Left far boundary"), (3.5, 4, "Right far boundary"))):
        ns = [n for n in far_nodes if low <= n["reference_x_mm"] <= high]
        for key, label, color, marker in styles:
            axs[0, col].plot([n["reference_x_mm"] for n in ns], [float(n[key])*1e6 for n in ns],
                             color=color, marker=marker, ms=5, lw=1, label=label)
        for edge in edges:
            xs = edge["reference_x_mm"]
            if xs[0] < low or xs[1] > high:
                continue
            if edge["material_sign"] == "entire_edge_tension":
                axs[1, col].axvspan(*xs, color="#C35555", alpha=.14)
            elif edge["material_sign"] == "single_sign_change_or_endpoint_zero":
                axs[1, col].axvspan(*xs, color="#D6AD47", alpha=.14)
            axs[1, col].plot(xs, [float(p)*1e6 for p in edge["endpoint_Pyy_MPa"]], "o--", color="#874F73", ms=5, lw=1)
        for row in range(2):
            axs[row, col].axhline(0, color=".5", lw=.8)
            axs[row, col].grid(alpha=.15)
            axs[row, col].set_xlim(low-.015, high+.015)
        axs[0, col].set_title(side)
        axs[0, col].set_ylabel("On-plane force (microN / node)")
        axs[1, col].set_ylabel("Material nominal Pyy (Pa)")
        axs[1, col].set_xlabel("Reference x (mm)")
        axs[1, col].text(.03, .05, "Pyy > 0: material tension\nshaded red: entire edge; yellow: sign change", transform=axs[1, col].transAxes,
                          fontsize=8, bbox={"facecolor":"white", "alpha":.85, "edgecolor":"none"})
    handles, labels = axs[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(.5,.923), ncol=4, fontsize=9)
    fig.suptitle("outer_free | h = 0.125 mm | d = 0.5 mm | saved medium field", fontsize=15, y=.985)
    fig.text(.5, .023, "Upper: signed weak nodal force and direct material boundary projection are different quantities; lines only guide the eye.\n"
             "Lower: element endpoint values (HP120, checked against HP80); dashed segments are not a sampled stress curve.\n"
             "Signs use the flat-Q1 edge monotonicity certificate. These are not Cauchy contact pressures or unilateral-law validation.",
             ha="center", va="bottom", fontsize=8.7)
    fig.tight_layout(rect=(0, .12, 1, .89), h_pad=2)
    for ext in ("png", "svg"):
        fig.savefig(out / f"outer_free_far_boundary.{ext}", dpi=180)
    plt.close(fig)

    script = Path(__file__).resolve()
    bindings[script.relative_to(root).as_posix()] = sha(script)
    record = {"schema": "contact_c2_presentation_v1", "created_utc": datetime.now(timezone.utc).isoformat(),
              "operation": "read-only frozen-evidence extraction and plotting; no FE or new admission",
              "common_original_target_three_meshes": records,
              "outer_free": {"state_id": analytic["state_id"], "d_mm": "0.5", "h_mm": "0.125",
                             "far_nodes": far_nodes, "far_edges": edges,
                             "analytic_aggregate": analytic["aggregate"]},
              "source_manifest_notes": notes, "input_sha256_from_workspace_root": bindings,
              "limitations": ["h=0.0625 whole path remains failed; d=0.375 is a comparable original target inside the valid prefix.",
                              "Three-grid observations do not establish convergence.",
                              "Weak total/material/regularization and direct material edge projections are distinct; components are not independently equilibrated.",
                              "Positive Pyy is nominal material tension, not an admitted contact pressure. Endpoint guide segments are not the exact stress field."]}
    (out / "summary.json").write_text(json.dumps(record, indent=2)+"\n", encoding="utf-8")
    outputs = {p.name: sha(p) for p in sorted(out.iterdir()) if p.is_file()}
    (out / "output_sha256.json").write_text(json.dumps(outputs, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"output": str(out), "source_sha256": sha(script), "summary_sha256": sha(out/"summary.json"),
                      "manifest_sha256": sha(out/"output_sha256.json"), "verified_source_files": len(bindings)}, indent=2))


if __name__ == "__main__":
    main()
