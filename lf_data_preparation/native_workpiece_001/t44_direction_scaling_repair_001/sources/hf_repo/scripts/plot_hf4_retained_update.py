"""Render saved HF4 stage-0 update evidence, without any mechanics evaluation.

CLI: python scripts/plot_hf4_retained_update.py --input STAGE0_DIR --output NEW
Only ordinary archived JSON values are read. Decimal source values and every
derived plotting quantity are saved before binary64 conversion for rendering.
The five states are diagnostic interventions, never production accepted states.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import hashlib
import json
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ORDER = ("base", "rounded_1", "rounded_half", "retained_1", "retained_half")
LABELS = ("Saved\nbase", "Rounded\n"+r"$\alpha=1$", "Rounded\n"+r"$\alpha=1/2$",
          "Retained\n"+r"$\alpha=1$", "Retained\n"+r"$\alpha=1/2$")
COLORS = ("#536474", "#b65b2c", "#b65b2c", "#167d8d", "#167d8d")


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path, value):
    temporary = path.with_name(path.name+".tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


class Inputs:
    def __init__(self, root):
        self.root = root.resolve()
        self.files = {}

    def read(self, relative, expected=None):
        path = (self.root/relative).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError("evidence path escapes input directory")
        digest = _sha(path)
        if expected is not None and digest != expected:
            raise ValueError("evidence hash mismatch: "+relative)
        record = dict(sha256=digest, bytes=path.stat().st_size)
        if relative in self.files and self.files[relative] != record:
            raise ValueError("input changed while preparing plot: "+relative)
        self.files[relative] = record
        return json.loads(path.read_text(encoding="utf-8-sig"))

    def verify(self):
        for relative, record in self.files.items():
            path = (self.root/relative).resolve()
            if _sha(path) != record["sha256"] or path.stat().st_size != record["bytes"]:
                raise ValueError("input changed during plotting: "+relative)


def _decimal(value, name):
    result = Decimal(value)
    if not result.is_finite():
        raise ValueError("nonfinite archived quantity: "+name)
    return result


def _read_values(input_directory):
    sources = Inputs(input_directory)
    summary = sources.read("summary.json")
    metadata = sources.read("metadata.json")
    if (summary.get("schema_version") != "hf4-retained-update-summary-1.0"
            or summary.get("diagnostic_only") is not True
            or summary.get("production_accepted") is not False
            or summary.get("completed_HP_evaluations") != 10):
        raise ValueError("expected the completed ten-evaluation diagnostic record")
    rows_by_name = {row["name"]: row for row in summary["rows"]}
    if set(rows_by_name) != set(ORDER) or len(summary["rows"]) != len(ORDER):
        raise ValueError("expected each of the five predeclared states exactly once")
    spec_relative = "hf_repo/configs/hf4/validation_spec.json"
    spec_binding = summary["input_bindings"][spec_relative]["sha256"]
    spec = sources.read("input_snapshot/"+spec_relative, spec_binding)
    production = _decimal(metadata["production_target"], "production target")
    external = _decimal(spec["numerical_criteria"]["hp_relative_residual"], "external HP gate")
    if production != Decimal("1e-9") or external != Decimal("1e-8"):
        raise ValueError("unexpected original production or external HP line")
    values = []
    with localcontext() as context:
        context.prec = 110
        for name in ORDER:
            row = rows_by_name[name]
            entry = row["files"]["80"]
            state = sources.read(entry["path"], entry["sha256"])
            if (state["name"] != name or state["precision_digits"] != 80
                    or state["diagnostic_state_only"] is not True
                    or state["production_accepted"] is not False
                    or state["alpha"] != row["alpha"]):
                raise ValueError("HP80 state identity mismatch: "+name)
            for key, value in row["metrics"]["80"].items():
                if state[key] != value:
                    raise ValueError("summary and state metric disagree: "+name+":"+key)
            residual = _decimal(state["relative_residual_decimal"], "residual")
            phi = _decimal(state["phi_fixed_base_scale_decimal"], "merit")
            bound = _decimal(state["armijo_bound_decimal"], "Armijo bound")
            baseline = _decimal(state["base_phi_decimal"], "base merit")
            if min(residual, phi, bound, baseline) <= 0:
                raise ValueError("this comparison requires positive saved residual/merit quantities")
            margin = Decimal(100)*(bound-phi)/bound
            if state["production_target_pass"] != (residual <= production) or state["armijo_pass"] != (phi <= bound):
                raise ValueError("saved diagnostic decision contradicts its quantities: "+name)
            values.append(dict(name=name, alpha=row["alpha"], representation=row["representation"],
                relative_residual_decimal=str(residual),
                force_scale_N_decimal=state["force_scale_decimal"],
                free_residual_norm_N_decimal=state["free_residual_norm_decimal"],
                fixed_reaction_norm_N_decimal=state["fixed_reaction_norm_decimal"],
                force_floor_N_decimal=state["force_floor_decimal"],
                base_force_scale_N_decimal=state["base_force_scale_decimal"],
                phi_fixed_base_scale_decimal=str(phi), base_phi_decimal=str(baseline),
                armijo_bound_decimal=str(bound), armijo_margin_percent_decimal=str(margin),
                phi_over_armijo_bound_decimal=str(phi/bound), phi_over_base_phi_decimal=str(phi/baseline),
                relative_constraint_decimal=state["relative_constraint_decimal"], minimum_J_decimal=state["minimum_J_decimal"],
                production_target_pass=state["production_target_pass"], armijo_pass=state["armijo_pass"],
                validity_pass=row["validity_pass"], diagnostic_only=True, production_accepted=False))
        if any(value["base_force_scale_N_decimal"] != values[0]["base_force_scale_N_decimal"]
               or value["base_phi_decimal"] != values[0]["base_phi_decimal"] for value in values):
            raise ValueError("Armijo quantities do not share the same baseline scale")
    return sources, summary, metadata, production, external, values


def render(input_directory, output):
    input_directory, output = Path(input_directory).resolve(), Path(output).resolve()
    sources, summary, metadata, production, external, values = _read_values(input_directory)
    output.mkdir(parents=True, exist_ok=False)
    plot_data = dict(schema_version="hf4-retained-update-plot-data-1.0", precision_digits=80,
        state_order=list(ORDER), data=values,
        production_line_decimal=str(production), external_HP_line_decimal=str(external),
        armijo_margin_formula="100*(armijo_bound-phi)/armijo_bound",
        baseline_force_scale_N_decimal=values[0]["base_force_scale_N_decimal"],
        baseline_phi_decimal=values[0]["base_phi_decimal"],
        derived_decimal_context_digits=110, rendering="binary64 view of these Decimal values only",
        scope="one saved candidate and one fixed Newton direction; diagnostic, not accepted production states")
    _write_json(output/"plot_data.json", plot_data)
    with (output/"plot_data.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(values[0]))
        writer.writeheader()
        writer.writerows(values)
    x = np.arange(len(values), dtype=float)
    residuals = np.array([float(Decimal(value["relative_residual_decimal"])) for value in values])
    margins = np.array([float(Decimal(value["armijo_margin_percent_decimal"])) for value in values])
    if not np.all(np.isfinite(residuals)) or not np.all(np.isfinite(margins)) or np.any(residuals <= 0):
        raise ValueError("values cannot be represented on the proposed display axes")
    np.savez_compressed(output/"plot_coordinates.npz", x=x, relative_residual=residuals,
                        armijo_margin_percent=margins, state_names=np.array(ORDER),
                        production_line=np.array(float(production)), external_line=np.array(float(external)))

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.labelcolor": "#273b4b", "text.color": "#273b4b",
                         "xtick.color": "#536474", "ytick.color": "#536474",
                         "axes.edgecolor": "#cdd6dc", "axes.spines.top": False,
                         "axes.spines.right": False, "savefig.facecolor": "white"})
    fig, axes = plt.subplots(1, 2, figsize=(14.4, 7.5))
    fig.subplots_adjust(left=.083, right=.978, bottom=.25, top=.765, wspace=.30)
    fig.text(.055, .954, "Fixed-candidate update retention", fontsize=20, fontweight="bold", ha="left")
    fig.text(.055, .907,
        "One saved g1/m1 candidate  |  d = 0.125 mm  |  HP80  |  same stored Newton direction",
        fontsize=11, color="#536474")
    fig.text(.955, .951, "STAGE 0 · DIAGNOSTIC", ha="right", fontsize=10, color="#167d8d", fontweight="bold")

    left, right = axes
    left.set_title("A   Force equilibrium at each saved state", loc="left", fontsize=12, pad=17, fontweight="bold")
    left.axvspan(.5, 2.5, color="#b65b2c", alpha=.045, linewidth=0)
    left.axvspan(2.5, 4.5, color="#167d8d", alpha=.045, linewidth=0)
    lower = min(float(production)/100, float(residuals.min())/5)
    upper = max(float(external)*2.6, float(residuals.max())*3)
    for position, value, color in zip(x, residuals, COLORS):
        left.vlines(position, lower, value, color=color, alpha=.28, linewidth=2)
        left.scatter(position, value, s=80, color=color, edgecolor="white", linewidth=1.1, zorder=5)
        left.annotate(f"{value:.3e}", (position, value), xytext=(0, 10), textcoords="offset points",
                      ha="center", fontsize=9, color=color, fontweight="bold")
    left.axhline(float(production), color="#ae3e49", linewidth=1.3, linestyle="--", label=r"Original production target: $10^{-9}$")
    left.axhline(float(external), color="#7c8994", linewidth=1.2, linestyle=":", label=r"External HP equilibrium gate: $10^{-8}$")
    left.set_yscale("log")
    left.set_ylim(lower, upper)
    left.set_ylabel(r"HP80 free residual / $S_F$  [dimensionless]", labelpad=10)
    left.grid(axis="y", which="major", color="#e5eaf0", linewidth=.7)
    left.legend(loc="lower left", frameon=True, facecolor="white", edgecolor="#e4e9ee", fontsize=8.6)

    right.set_title("B   Armijo margin with a fixed base force scale", loc="left", fontsize=12, pad=17, fontweight="bold")
    right.set_yscale("symlog", linthresh=.001, linscale=.7)
    right.set_ylim(min(-.1, float(margins.min())*2), max(200., float(margins.max())*2))
    right.axhspan(0, right.get_ylim()[1], color="#167d8d", alpha=.04, linewidth=0)
    right.axhspan(right.get_ylim()[0], 0, color="#b65b2c", alpha=.04, linewidth=0)
    right.axhline(0, color="#536474", linewidth=1.2, linestyle="--")
    for position, value, color, item in zip(x, margins, COLORS, values):
        right.vlines(position, 0, value, color=color, alpha=.45, linewidth=2)
        right.scatter(position, value, s=80, color=color, edgecolor="white", linewidth=1.1, zorder=5)
        label = "0 · base" if item["name"] == "base" else ("≈100%" if value > 99.99995 else f"{value:.4g}%")
        right.annotate(label, (position, value), xytext=(0, 10 if value >= 0 else -18),
                       textcoords="offset points", ha="center", fontsize=9, color=color, fontweight="bold")
    right.set_yticks([-.1, -.01, 0, .01, 1, 100], labels=["−0.1", "−0.01", "0", "0.01", "1", "100"])
    right.set_ylabel("100 × (Armijo bound − merit) / bound  [%]\nPositive passes; symmetric-log display", labelpad=9)
    right.grid(axis="y", which="major", color="#e5eaf0", linewidth=.7)
    for axis in axes:
        axis.set_xlim(-.5, 4.5)
        axis.set_xticks(x, labels=LABELS)
        axis.tick_params(axis="x", length=0, pad=10)
        axis.set_axisbelow(True)

    with localcontext() as context:
        context.prec = 110
        base = Decimal(values[0]["relative_residual_decimal"])
        full = Decimal(values[3]["relative_residual_decimal"])
        reduction = base/full
    fig.text(.055, .143,
        f"Retained full update: {float(reduction):.3g}× lower residual than the saved base.  "
        "Rounded updates remain above the original production target.", fontsize=10, fontweight="bold")
    fig.text(.055, .098,
        "These are fixed-state diagnostic interventions, not formally accepted production states. "
        "No solver path, new direction or strong-compression verification was performed.", fontsize=9, color="#536474")
    fig.text(.055, .061,
        r"A uses each state's original HF4 $S_F$.  B uses the same base $S_F$ for all merits; "
        "its zero line is the stored Armijo bound. Exact Decimal values are saved alongside this figure.", fontsize=8.7, color="#536474")
    figure = output/"retained_update_comparison.png"
    fig.savefig(figure, dpi=260, facecolor="white")
    plt.close(fig)
    sources.verify()
    outputs = {path.name: dict(sha256=_sha(path), bytes=path.stat().st_size)
               for path in output.iterdir() if path.is_file()}
    manifest = dict(schema_version="hf4-retained-update-plot-manifest-1.0", status="rendered",
                    created_utc=datetime.now(timezone.utc).isoformat(),
                    script_sha256=_sha(Path(__file__).resolve()), source_result_status=summary["status"],
                    source_inputs=sources.files, outputs=outputs, inputs_unchanged=True,
                    figure="retained_update_comparison.png", source_precision_digits=80,
                    physics_recomputed=False, plotting_only=True,
                    diagnostic_only=True, production_accepted=False)
    _write_json(output/"manifest.json", manifest)
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = render(args.input, args.output)
    print(json.dumps(dict(status=result["status"], figure=result["figure"])), flush=True)
