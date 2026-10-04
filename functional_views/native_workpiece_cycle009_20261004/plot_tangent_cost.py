"""Plot the closed single-pass tangent comparison; saved receipts only."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = next(p for p in Path(__file__).resolve().parents if (p/"hf_repo").is_dir())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    source = ROOT/"lf_data_preparation/native_workpiece_001/numpy_tangent_chunk_001/comparison_receipt.json"
    record = json.loads(source.read_text(encoding="utf-8"))
    assert record["status"] == "pass" and record["candidate_cost_gate_passed"]
    rows = record["rows"]
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    labels = ["Origin / zero", "Peak / 1.75 mm", "Return / near zero"]
    x = np.arange(3)
    fig, ax = plt.subplots(figsize=(11, 5.5), constrained_layout=True)
    colors = ["#698096", "#bbc5d0", "#078579"]
    for k, name in enumerate(("archived", "factored_full", "chunk256")):
        values = [row["timings_seconds"][name] for row in rows]
        bars = ax.bar(x+(k-1)*.24, values, .22, color=colors[k],
                      label={"archived":"Frozen old full batch", "factored_full":"Refactored full batch",
                             "chunk256":"Optional 256-cell blocks"}[name])
        ax.bar_label(bars, labels=[f"{v:.2f}" for v in values], fontsize=9, padding=3)
    for i,row in enumerate(rows):
        ax.text(i, 25., f'{row["single_pass_speed_ratio"]:.2f}x', ha="center",
                color=colors[-1], fontsize=14, fontweight="bold")
    ax.set(xticks=x, xticklabels=labels, ylabel="Single tangent call wall time (seconds)", ylim=(0, 29))
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=.15)
    ax.set_axisbelow(True)
    fig.legend(*ax.get_legend_handles_labels(), loc="lower center", bbox_to_anchor=(.5,-.02),
               ncol=3, fontsize=9)
    fig.suptitle("Same mechanical Jacobian, lower measured cost", fontsize=18)
    ax.set_title("Each state: all 614,400 tensor coefficients + full CSC bytes identical",
                 fontsize=11, pad=12)
    fig.text(.01, -.10, "One pass per implementation, not a statistical benchmark. Shared exact rich cache; "
             "global small-product branch retained.\n3 force / 9 tangent / 9 CSC evaluations; 0 equilibrium solves or new HP. "
             "This comparison does not qualify contact pressure or a new loading path.", fontsize=9)
    image = output/"tangent_cost.png"
    fig.savefig(image, dpi=200, bbox_inches="tight")
    plt.close(fig)
    with (output/"tangent_cost.csv").open("x",newline="",encoding="utf-8") as stream:
        writer=csv.writer(stream)
        writer.writerow(["state","mechanical_force_s","archived_s","factored_full_s","chunk256_s","speed_ratio"])
        for row in rows:
            writer.writerow([row["name"]]+[row["timings_seconds"][n] for n in
                ("mechanical_force","archived","factored_full","chunk256")]+[row["single_pass_speed_ratio"]])
    (output/"metadata.json").write_text(json.dumps(dict(
        source_receipt_sha256=sha256(source.read_bytes()).hexdigest(),
        image_sha256=sha256(image.read_bytes()).hexdigest(),
        new_force_tangent_solver_HP_calls=0, scope="Saved closed timing and byte-comparison receipts only"),
        indent=2)+"\n",encoding="utf-8")


if __name__ == "__main__":
    main()
