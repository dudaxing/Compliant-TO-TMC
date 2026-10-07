"""One read-only plot of completed progress rows; no mechanical calculation."""
from pathlib import Path
from hashlib import sha256
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

repo = Path("D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC")
base = repo / "lf_data_preparation/native_workpiece_001"
old_file = base / "enlarged_square_projection_001/run_001/result/result.json"
raw = (base / "gamma_half_cycle_001/run_001/accepted_progress.jsonl").read_bytes()
new = [json.loads(line) for line in raw.split(b"\n")[:-1]]
old = json.loads(old_file.read_text())["states"]
lookup = {(s["original_target_index"], s["leg"]): s for s in old}
matched = [lookup[(s["original_target_index"], s["leg"])] for s in new]
out = Path(__file__).resolve().parent / "live_gamma_001"
out.mkdir(exist_ok=False)
(out / "progress_snapshot.jsonl").write_bytes(raw)
fig, axes = plt.subplots(1, 3, figsize=(12, 3.7))
labels = ("Input reaction [N]", "Lower-body signed Fy [N]", "Weighted output displacement [mm]")
for series, label, color in ((matched, "gamma=1e-6 baseline", "#457b9d"), (new, "gamma=5e-7 ongoing production", "#d95f02")):
    d = [s["d"] for s in series]
    fy = [s["workpiece"]["force_on_lower_body_N"]["total"][1] if "force_on_lower_body_N" in s["workpiece"] else s["workpiece"]["total"][1] for s in series]
    for ax, values in zip(axes, ([s["R_input"] for s in series], fy, [s["q_out"] for s in series])):
        ax.plot(d, values, "o-", color=color, ms=4, label=label)
for ax, title in zip(axes, labels):
    ax.set(xlabel="Mean input displacement [mm]", ylabel=title)
    ax.grid(alpha=.2)
axes[0].legend(fontsize=7)
fig.suptitle("Same geometry/body/boundaries: matched accepted loading progress; new full-cycle / HP pending", fontsize=10)
fig.tight_layout()
fig.savefig(out / "progress.png", dpi=150)
plt.close(fig)
receipt = dict(status="preliminary_plot_only", observed_progress_rows=len(new), last_d_mm=new[-1]["d"],
    source_progress_snapshot_sha256=sha256(raw).hexdigest(), baseline_result_sha256=sha256(old_file.read_bytes()).hexdigest(),
    new_force_tangent_solver_HP_calls=0, scope="Scalar production progress, not saved-geometry or independent reference qualification")
(out / "receipt.json").write_text(json.dumps(receipt, indent=2)+"\n")
print(json.dumps(receipt))
