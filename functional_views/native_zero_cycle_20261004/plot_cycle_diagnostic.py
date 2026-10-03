"""Compare two saved tiny-cycle JSON receipts; never evaluate mechanics."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from time import perf_counter


ROOT = Path(__file__).resolve().parents[2]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_name(path):
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.name


def segments(rows, target_key):
    groups = []
    for index, row in enumerate(rows, 1):
        if (not groups or row[target_key] != groups[-1]["target_mm"]
                or row["newton_check"] < groups[-1]["rows"][-1][1]["newton_check"]):
            groups.append(dict(target_mm=row[target_key], rows=[]))
        groups[-1]["rows"].append((index, row))
    return groups


def prepare(result):
    if (result["counts"]["cells"] != 16 or result["counts"]["dofs"] != 50
            or result["path_kind"] != "ordered_cycle"
            or result["targets_mm"] != [0., .0005, 0.]
            or result["settings"]["tolerance"] != 1e-9):
        raise ValueError("expected the saved 16-cell, 50-DOF 0/.0005/0 tiny cycle with its original gate")
    diagnostics = result["path_diagnostics"]
    groups = segments(diagnostics["newton_history"], "d")
    unload = 0
    for index, group in enumerate(groups):
        if index == 0:
            group["label"] = "O"
        elif group["target_mm"] == .0005:
            group["label"] = "L"
        elif group["target_mm"] > 0:
            group["label"] = "B"
        else:
            unload += 1
            group["label"] = f"U{unload}"
    events, cursor = [], 0
    for trial_group in segments(diagnostics["trials"], "target_displacement"):
        while cursor < len(groups) and groups[cursor]["target_mm"] != trial_group["target_mm"]:
            cursor += 1
        if cursor == len(groups):
            raise ValueError("saved trial order does not match saved Newton attempts")
        positions = {row["newton_check"]: index for index, row in groups[cursor]["rows"]}
        for trial_index, row in trial_group["rows"]:
            events.append(dict(index=positions[row["newton_check"]], trial_index=trial_index,
                               segment=groups[cursor]["label"], row=row))
        cursor += 1
    range_rejects = sum(not e["row"]["accepted"] and e["row"].get("reason") == "unsupported_arithmetic_range"
                        and e["row"]["factor"] == 1. for e in events)
    half_accepts = sum(e["row"]["accepted"] and e["row"]["factor"] == .5 for e in events)
    full_accepts = sum(e["row"]["accepted"] and e["row"]["factor"] == 1. for e in events)
    last = events[-1]["row"] if events else {}
    missing_half_clock = ((result.get("failure") or {}).get("code") == "time_limit"
                          and last.get("reason") == "unsupported_arithmetic_range" and last.get("factor") == 1.)
    return dict(result=result, groups=groups, events=events, range_rejects=range_rejects,
                half_accepts=half_accepts, full_accepts=full_accepts, missing_half_clock=missing_half_clock)


def residual_panel(ax, dataset, name, color, ylim):
    result, groups = dataset["result"], dataset["groups"]
    ax.set_yscale("log")
    ax.set_ylim(*ylim)
    count = len(result["path_diagnostics"]["newton_history"])
    ax.set_xlim(.5, count+.5)
    ax.axhline(1e-9, color="#35424a", linestyle="--", linewidth=1, label="Original gate 1e-9")
    event_ax = ax.inset_axes([0., -.29, 1., .18], sharex=ax)
    event_ax.set_ylim(-.5, 2.5)
    event_ax.set_yticks([0, 1, 2], ["Half accepted", "Full step", "Exact zero"])
    event_ax.tick_params(axis="both", labelsize=7, length=0)
    event_ax.tick_params(axis="x", bottom=False, labelbottom=False)
    for spine in event_ax.spines.values():
        spine.set_visible(False)
    for group in groups:
        positive = [(i, r["relative_residual"]) for i, r in group["rows"] if r["relative_residual"] > 0]
        if positive:
            ax.plot([p[0] for p in positive], [p[1] for p in positive], "o-", color=color,
                    markersize=3, linewidth=1.3)
        zeros = [i for i, r in group["rows"] if r["relative_residual"] == 0.]
        event_ax.scatter(zeros, [2]*len(zeros), marker="o", facecolors="none", edgecolors=color, s=28)
        first, last = group["rows"][0][0], group["rows"][-1][0]
        if first > 1:
            ax.axvline(first-.5, color="#a0a8ad", linestyle=":", linewidth=.8)
        ax.text((first+last)/2, .98, group["label"], transform=ax.get_xaxis_transform(),
                ha="center", va="top", fontsize=8, color="#24333d")
    for event in dataset["events"]:
        row, x = event["row"], event["index"]
        if row["factor"] == 1. and row.get("reason") == "unsupported_arithmetic_range":
            event_ax.scatter(x, 1, marker="x", color="#bb3d38", s=22, linewidths=1.)
        elif row["accepted"] and row["factor"] == 1.:
            event_ax.scatter(x, 1, marker="^", color="#66747d", s=20)
        elif row["accepted"] and row["factor"] == .5:
            event_ax.scatter(x, 0, marker="v", color="#26764b", s=20)
    failure = result.get("failure") or {}
    subtitle = failure.get("code", "completed" if result["path_completed"] else "incomplete")
    ax.set_title(f"{name}: {result['status']} / {subtitle} ({count} base checks)", fontsize=11, loc="left")
    ax.set_ylabel("Relative free-force residual (dimensionless)", fontsize=9)
    ax.set_xlabel("Chronological Newton base-check index (own sequence)", fontsize=9, labelpad=3)
    ax.tick_params(labelsize=8)
    ax.grid(axis="y", alpha=.18)
    ax.legend(loc="lower left", fontsize=8, frameon=False)
    note = f"Full range rejects {dataset['range_rejects']}; half accepts {dataset['half_accepts']}; full accepts {dataset['full_accepts']}"
    if dataset["missing_half_clock"]:
        note += "\nLast half trial: unrecorded at wall-time stop, not a numerical rejection."
    return note


def accepted_panels(axes, datasets):
    from matplotlib.lines import Line2D
    colors = {"Before": "#bf6b24", "After": "#286eaa"}
    markers = {"origin": "o", "loading": "^", "unloading": "v"}
    for name, dataset in datasets.items():
        rows, color = dataset["result"]["states"], colors[name]
        indices, ds, forces = list(range(len(rows))), [1000*r["d"] for r in rows], [r["R_input"] for r in rows]
        axes[0].plot(indices, ds, color=color, linewidth=1.3, label=name)
        axes[1].plot(ds, forces, color=color, linewidth=1.3, label=name)
        for index, row in enumerate(rows):
            marker = markers[row["leg"]]
            axes[0].scatter(index, ds[index], marker=marker, color=color, s=52, edgecolors="white", linewidths=.6, zorder=3)
            axes[1].scatter(ds[index], forces[index], marker=marker, color=color, s=52, edgecolors="white", linewidths=.6, zorder=3)
            if not row["is_original_target"]:
                axes[0].annotate("bisected", (index, ds[index]), xytext=(-30, 13), textcoords="offset points", fontsize=8, color=color)
            if index:
                axes[1].annotate("", xy=(ds[index], forces[index]), xytext=(ds[index-1], forces[index-1]),
                                 arrowprops=dict(arrowstyle="->", color=color, linewidth=.9, shrinkA=8, shrinkB=8))
    axes[0].set(xlabel="Accepted-state index (zero based)", ylabel="Accepted mean input displacement (um)",
                title="Accepted states only; a missing zero endpoint is not filled")
    axes[0].set_xticks(sorted({i for d in datasets.values() for i in range(len(d["result"]["states"]))}))
    axes[1].set(xlabel="Accepted mean input displacement (um)", ylabel="Input multiplier R (N)",
                title="Accepted input multiplier in actual path order")
    for ax in axes:
        ax.grid(alpha=.18)
        ax.tick_params(labelsize=8)
        ax.xaxis.label.set_size(9)
        ax.yaxis.label.set_size(9)
        ax.title.set_size(10)
    axes[0].legend(fontsize=8, frameon=False, loc="upper left")
    role_handles = [Line2D([], [], color="#43515a", marker=marker, linestyle="none", label=leg)
                    for leg, marker in markers.items()]
    axes[1].legend(handles=role_handles, fontsize=8, frameon=False, loc="upper left")
    axes[1].ticklabel_format(axis="y", style="sci", scilimits=(-3, 3))
    for name, dataset in datasets.items():
        last = dataset["result"]["states"][-1]
        offset = (-125, -24) if name == "Before" else (12, 10)
        axes[1].annotate(f"{name} endpoint: {1000*last['d']:g} um", (1000*last["d"], last["R_input"]),
                         xytext=offset, textcoords="offset points", fontsize=8, color=colors[name])


def write_csv(path, datasets):
    keys = ["dataset", "record_type", "sequence_index", "segment", "newton_check", "target_mm", "R_input_N",
            "relative_residual", "residual_scale", "factor", "accepted", "reason", "original_target_index", "bisection_depth"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        for name, dataset in datasets.items():
            for group in dataset["groups"]:
                for index, row in group["rows"]:
                    writer.writerow(dict(dataset=name, record_type="Newton base", sequence_index=index,
                                         segment=group["label"], newton_check=row["newton_check"], target_mm=row["d"],
                                         R_input_N=row["R_input"], relative_residual=row["relative_residual"], residual_scale=row["residual_scale"]))
            for event in dataset["events"]:
                row = event["row"]
                writer.writerow(dict(dataset=name, record_type="trial event", sequence_index=event["index"], segment=event["segment"],
                                     newton_check=row["newton_check"], target_mm=row["target_displacement"], factor=row["factor"],
                                     accepted=row["accepted"], reason=row.get("reason", "")))
            for index, row in enumerate(dataset["result"]["states"]):
                writer.writerow(dict(dataset=name, record_type="accepted state", sequence_index=index, target_mm=row["d"],
                                     R_input_N=row["R_input"], relative_residual=row["relative_residual"], residual_scale=row["residual_scale"],
                                     original_target_index=row["original_target_index"], bisection_depth=row["bisection_depth"]))


def main():
    started = perf_counter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="new output directory; no overwrite")
    args = parser.parse_args()
    inputs = {name: path.resolve() for name, path in (("Before", args.before), ("After", args.after))}
    pins = {name: sha256(path) for name, path in inputs.items()}
    datasets = {name: prepare(json.loads(path.read_text(encoding="utf-8"))) for name, path in inputs.items()}
    if datasets["Before"]["result"]["source_geometry"] != datasets["After"]["result"]["source_geometry"]:
        raise ValueError("before/after saved source geometry bindings differ")
    positive = [row["relative_residual"] for d in datasets.values() for g in d["groups"] for _, row in g["rows"]
                if row["relative_residual"] > 0.]
    if any(not math.isfinite(x) for x in positive):
        raise ValueError("saved relative residual is nonfinite")
    ylim = (10.**math.floor(math.log10(min(positive+[1e-9]))), 10.**math.ceil(math.log10(max(positive+[1e-9]))))
    args.output.mkdir(parents=True, exist_ok=False)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.subplots_adjust(left=.11, right=.98, top=.89, bottom=.12, hspace=.73, wspace=.28)
    notes = [residual_panel(axes[0, i], datasets[name], name, color, ylim)
             for i, (name, color) in enumerate((("Before", "#bf6b24"), ("After", "#286eaa")))]
    accepted_panels(axes[1], datasets)
    fig.suptitle("Saved tiny zero-return cycle: arithmetic failure and subsequent recorded outcome", fontsize=15, x=.11, ha="left")
    fig.text(.11, .925, "16 Q1 cells / 50 DOFs / no workpiece. Diagnostic fixture, not a physical gripper or contact validation.", fontsize=10)
    for x, note in zip((.11, .59), notes):
        fig.text(x, .47, note, fontsize=8, va="top")
    fig.text(.11, .045, "O: origin; L: loading peak; U: separate zero-target attempt; B: accepted bisection midpoint.\n"
             "Red x: unsupported full-step arithmetic; gray triangle: full-step accepted; green triangle: half-step accepted.\n"
             "Exact zero is shown only in the event strip. Lines/arrows join saved observations in order; no intermediate states or deformation are generated.", fontsize=8)
    png, csv_path = args.output/"cycle_diagnostic.png", args.output/"numeric_records.csv"
    fig.savefig(png, dpi=180)
    plt.close(fig)
    write_csv(csv_path, datasets)
    endpins = {name: sha256(path) for name, path in inputs.items()}
    if endpins != pins:
        raise RuntimeError("input JSON bytes changed during saved-data visualization")
    metadata = dict(schema_version="saved-tiny-cycle-view-1.0", scope="saved JSON visualization only",
                    inputs={name: dict(path=source_name(path), sha256=pins[name]) for name, path in inputs.items()},
                    input_sha256_after=endpins, inputs_unchanged=True,
                    script=dict(path=source_name(Path(__file__)), sha256=sha256(Path(__file__))),
                    outputs={p.name: sha256(p) for p in (png, csv_path)}, original_relative_residual_gate=1e-9,
                    residual_y_limits=list(ylim), exact_zero_policy="event strip only; never replaced by a positive floor",
                    rejected_trial_residual_policy="not available; events have no fabricated residual",
                    line_policy="join observations in order only; no computed intermediate states",
                    mechanics_calls=0, force_calls=0, tangent_calls=0, HP_calls=0,
                    contact_qualified=False, public_recovery_qualified=False, elapsed_seconds=perf_counter()-started,
                    datasets={})
    for name, dataset in datasets.items():
        r = dataset["result"]
        metadata["datasets"][name] = dict(status=r["status"], failure=r.get("failure"), path_completed=r["path_completed"],
            loading_peak_reached=r["loading_peak_reached"], unload_endpoint_reached=r["unload_endpoint_reached"],
            counts=r["counts"], call_counts=r["call_counts"], declared_targets_mm=r["targets_mm"],
            segments=[dict(label=g["label"], target_mm=g["target_mm"], check_range=[g["rows"][0][0], g["rows"][-1][0]]) for g in dataset["groups"]],
            full_range_rejects=dataset["range_rejects"], half_accepts=dataset["half_accepts"], full_accepts=dataset["full_accepts"],
            last_half_trial_unrecorded_at_clock=dataset["missing_half_clock"],
            accepted_states=[{k: row[k] for k in ("d", "R_input", "relative_residual", "leg", "is_original_target", "bisection_depth")} for row in r["states"]])
    (args.output/"visual_metadata.json").write_text(json.dumps(metadata, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps(dict(status="saved_view_written", output=source_name(args.output), inputs_unchanged=True,
                          before_status=datasets["Before"]["result"]["status"], after_status=datasets["After"]["result"]["status"])))


if __name__ == "__main__":
    main()
