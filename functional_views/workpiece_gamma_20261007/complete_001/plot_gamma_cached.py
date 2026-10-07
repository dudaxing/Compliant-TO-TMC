"""Plot CSV/derived gamma differences only; no geometry or mechanics imports."""
from hashlib import sha256
from pathlib import Path
import csv
import json

LABELS = ("gamma1e6", "gamma5em7")
NAMES = {"gamma1e6": r"$\gamma=10^{-6}$", "gamma5em7": r"$\gamma=5\times10^{-7}$"}
FIELDS = ("R_input_N", "total_body_Fy_N", "material_body_Fy_N", "regularization_body_Fy_N",
    "tip_to_bottom_mm", "medium_min_J", "medium_max_abs_Hu_per_mm")


def plot_cached(output: Path, mode: str, checkpoint):
    import matplotlib.pyplot as plt
    rows, pins, summaries = {}, {}, {}

    def load(file):
        pins[file.relative_to(output).as_posix()] = sha256(file.read_bytes()).hexdigest()
        return json.loads(file.read_text(encoding="utf-8"))

    view = load(output / "view.json")
    assert view["status"] == "pass"
    for label in LABELS:
        directory = output / label
        summaries[label] = load(directory / "summary.json")
        file = directory / "states.csv"
        pins[file.relative_to(output).as_posix()] = sha256(file.read_bytes()).hexdigest()
        with file.open(newline="", encoding="utf-8") as handle:
            stored = list(csv.DictReader(handle))
        selected = []
        for item in stored:
            row = load(directory / f"{int(item['index']):03d}" / "derived.json")["row"]
            assert row["state_sha256"] == item["state_sha256"] and row["leg"] == item["leg"]
            assert row["d_mm"] == float(item["d_mm"]) and row["original_target_index"] == int(item["original_target_index"])
            assert all(row[field] == float(item[field]) for field in FIELDS)
            selected.append(row)
        assert len(selected) == summaries[label]["accepted_states"]
        rows[label] = selected
    tasks = {case["label"]: case["task"]["path"]["targets_mm"] for case in view["cases"]}
    targets, extra = {}, {}
    for label in LABELS:
        targets[label], extra[label] = [], []
        for row in rows[label]:
            index = row["original_target_index"]
            assert type(index) is int and 0 <= index < len(tasks[label])
            selected = targets[label] if row["d_mm"] == tasks[label][index] else extra[label]
            selected.append(row)
    key = lambda row: (row["leg"], row["original_target_index"], row["d_mm"])
    indexed = {label: {key(row): row for row in targets[label]} for label in LABELS}
    assert all(len(indexed[label]) == len(targets[label]) for label in LABELS), "Ambiguous original target/branch"
    matched = [(row, indexed[LABELS[1]][key(row)]) for row in targets[LABELS[0]] if key(row) in indexed[LABELS[1]]]
    assert matched, "No exact saved target/leg matches"
    if mode == "complete":
        assert all(summaries[label]["production_status"] == "success" and summaries[label]["reference_available"] for label in LABELS)
    else:
        assert summaries[LABELS[1]]["production_status"] != "success" and not summaries[LABELS[1]]["reference_available"]
    destination = output / "gamma_comparison"; destination.mkdir()
    table = []
    for before, after in matched:
        row = dict(leg=before["leg"], original_target_index=before["original_target_index"], d_mm=before["d_mm"],
            gamma1e6_index=before["index"], gamma5em7_index=after["index"],
            gamma1e6_state_sha256=before["state_sha256"], gamma5em7_state_sha256=after["state_sha256"])
        for field in FIELDS:
            row["gamma1e6_" + field] = before[field]; row["gamma5em7_" + field] = after[field]
            row["delta_" + field] = after[field] - before[field]
        row["gamma1e6_bottom_gap_um"] = 1000 * before["tip_to_bottom_mm"]
        row["gamma5em7_bottom_gap_um"] = 1000 * after["tip_to_bottom_mm"]
        table.append(row)
    with (destination / "matched_states.csv").open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(table[0])); writer.writeheader(); writer.writerows(table)
    qualifier = "complete paths; same-path mechanical references" if mode == "complete" else "PRELIMINARY FAILED PREFIX; new path has no reference"
    checkpoint()
    fig, axes = plt.subplots(2, 3, figsize=(17, 9))
    for label in LABELS:
        color = "#2465a7" if label == LABELS[0] else "#c75b2b"
        for leg in dict.fromkeys(row["leg"] for row in table):
            selected = [pair[LABELS.index(label)] for pair in matched if pair[0]["leg"] == leg]
            ds = [row["d_mm"] for row in selected]; fy = [row["total_body_Fy_N"] for row in selected]
            gap = [1000 * row["tip_to_bottom_mm"] for row in selected]
            style = "--" if leg == "unloading" else "-"
            name = NAMES[label] + " " + leg
            for ax, x, y in ((axes[0, 0], ds, fy), (axes[0, 1], ds, gap), (axes[0, 2], gap, fy),
                    (axes[1, 0], ds, [row["medium_min_J"] for row in selected]),
                    (axes[1, 1], ds, [row["medium_max_abs_Hu_per_mm"] for row in selected]),
                    (axes[1, 2], ds, [row["regularization_body_Fy_N"] for row in selected])):
                ax.plot(x, y, style, marker="o", ms=3, color=color, label=name)
    titles = ("Signed lower-body total Fy [N]", "Unsigned finite-bottom tip gap [µm]", "Fy versus unsigned tip gap",
        "Free-medium min J", "Free-medium max |Hu| [1/mm]", "Lower-body Hu Fy [N]")
    for ax, title in zip(axes.flat, titles):
        ax.set(title=title, xlabel="mean input d [mm]"); ax.grid(alpha=.25); ax.legend(fontsize=7)
    axes[0, 2].set(xlabel="unsigned finite-bottom tip gap [µm]", ylabel="lower-body Fy [N]")
    axes[0, 2].set_xscale("symlog", linthresh=1.)
    axes[1, 0].set_yscale("log")
    fig.suptitle("Matched saved states | " + qualifier); fig.tight_layout(); checkpoint()
    fig.savefig(destination / "matched_force_gap.png", dpi=150); plt.close(fig); checkpoint()
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    for ax, field, title in zip(axes.flat, ("R_input_N", "total_body_Fy_N", "medium_min_J", "medium_max_abs_Hu_per_mm"),
            ("Δ half-model input R [N]", "Δ lower-body Fy [N]", "Δ free-medium min J", "Δ free-medium max |Hu| [1/mm]")):
        for leg in dict.fromkeys(row["leg"] for row in table):
            selected = [row for row in table if row["leg"] == leg]
            ax.plot([row["d_mm"] for row in selected], [row["delta_" + field] for row in selected],
                "o--" if leg == "unloading" else "o-", ms=3, label=leg)
        ax.axhline(0, color="grey", lw=.7); ax.set(title=title, xlabel="mean input d [mm]"); ax.grid(alpha=.25); ax.legend(fontsize=8)
    fig.suptitle("Saved differences: 5×10⁻⁷ minus 10⁻⁶ | " + qualifier); fig.tight_layout(); checkpoint()
    fig.savefig(destination / "matched_differences.png", dpi=150); plt.close(fig); checkpoint()
    report = dict(status="pass", mode=mode, matching="Original task targets only: saved d == task.path.targets_mm[original_target_index], then exact (leg, original_target_index, d); no interpolation or nearest-state substitution",
        matched_states=len(matched), saved_states={label: len(rows[label]) for label in LABELS},
        extra_bisection_indices={label: [row["index"] for row in extra[label]] for label in LABELS},
        unmatched_original_target_indices={label: [row["index"] for row in targets[label] if key(row) not in indexed[LABELS[1 - LABELS.index(label)]]] for label in LABELS},
        source_bindings=pins, new_geometry_nodal_F_T_model_solver_HP_calls=0,
        scope="CSV/derived arithmetic and plots; signed half-model/body forces, unsigned finite-segment tip gap is not q_out or pressure. No assumed Fy halving or new contact qualification.",
        outputs={p.relative_to(output).as_posix(): sha256(p.read_bytes()).hexdigest() for p in destination.iterdir() if p.is_file()})
    with (destination / "cached_comparison.json").open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False, allow_nan=False); handle.write("\n")
    return report
