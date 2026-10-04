"""Read four saved HP80 C1 endpoint reactions; never evaluate or solve FE.

Values are discrete top-node constraint reactions on the plane, in N.
They are not Cauchy traction/contact pressure. The initial x-span label is
only a reference-coordinate classification, not a deformed contact region.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from fractions import Fraction
import hashlib
import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_npz(path):
    with np.load(path, allow_pickle=False) as data:
        return {key: data[key] for key in data.files}


def plot_reactions(payload, output):
    """Join saved node values for display; do not reconstruct a stress field."""
    fig, axes = plt.subplots(2, 2, figsize=(13, 8), constrained_layout=True)
    ordered = sorted(payload["cases"], key=lambda c: (c["mode"] != "uniform", -c["h_mm"]))
    for ax, case in zip(axes.ravel(), ordered):
        nodes = case["all_top_nodes"]
        x = [n["reference_x_mm"] for n in nodes]
        for key, label, color, style, marker in (
                ("total_N", "Total", "#243849", "-", "o"),
                ("material_N", "Material", "#397ca2", "--", "."),
                ("regularization_N", "HuHu regularization", "#ba622e", ":", "s")):
            ax.plot(x, [float(n[key]) for n in nodes], linestyle=style, marker=marker,
                    markersize=3, linewidth=1.1, color=color, label=label)
        ax.axhline(0, color="#59636c", linewidth=.7)
        ax.axvspan(0, 2, color="#d5dde2", alpha=.25, label="Initial solid x-span only")
        ax.set(xlabel="Reference top-node x (mm)", ylabel="Discrete nodal reaction (N per node)",
               yscale="symlog", xlim=(-2.1, 4.1),
               title=f"{case['mode']}, h={case['h_mm']} mm, s={case['parameter_s']} mm")
        ax.set_yscale("symlog", linthresh=1e-6)
        aggregate = case["aggregate"]
        ax.text(.02, .04,
                f"Negative sum {float(aggregate['negative_total_N']):.6g} N\n"
                f"Positive sum {float(aggregate['positive_total_N']):.8g} N\n"
                f"Net {float(aggregate['net_total_N']):.8g} N",
                transform=ax.transAxes, fontsize=8,
                bbox=dict(facecolor="white", alpha=.9, edgecolor="#d6dce1"))
        ax.grid(alpha=.2)
        ax.legend(fontsize=7, loc="upper left")
    fig.suptitle("Saved HP80 TMC endpoint reactions | not Cauchy traction or contact pressure\n"
                 "Discrete node markers; signed log scale (linear within +/-1e-6 N); shaded span is reference geometry only",
                 fontsize=11)
    for extension in ("png", "svg"):
        path = output.with_suffix("." + extension)
        if path.exists():
            raise FileExistsError("refusing to overwrite a diagnostic figure")
        fig.savefig(path, dpi=180)
    plt.close(fig)


def diagnose(root, selection, output):
    root, selection, output = Path(root).resolve(), Path(selection).resolve(), Path(output).resolve()
    if output.exists():
        raise FileExistsError("refusing to overwrite a diagnostic")
    selected = read_json(selection)
    if selected.get("schema") != "contact_c1_summary_selection_v1":
        raise ValueError("unsupported explicit selection")
    bindings = {str(selection): sha(selection)}
    cases = []
    choices = [entry for entry in selected["runs"] if entry["kind"] == "TMC"]
    if {(e["mode"], e["h"]) for e in choices} != {
            ("uniform", .25), ("uniform", .125), ("perturbation", .25), ("perturbation", .125)} or len(choices) != 4:
        raise ValueError("selection must identify exactly four TMC paths")
    for entry in choices:
        run = (root / entry["run"]).resolve()
        if not run.is_relative_to(root):
            raise ValueError("selected run escapes experiment root")
        audit_path = run / "audit.json"
        audit = read_json(audit_path)
        if audit.get("status") != "pass" or audit.get("measurement_precision") != 80:
            raise ValueError("endpoint requires a passing HP80 measurement audit")
        for name, digest in audit["input_and_helper_sha256"].items():
            path = (run / name).resolve()
            if not path.is_relative_to(root.parent) or sha(path) != digest:
                raise ValueError("audit input/helper binding changed: " + name)
        phase = "uniform_tmc" if entry["mode"] == "uniform" else "perturbation"
        target = .5 if entry["mode"] == "uniform" else .0625
        matches = [row for row in audit["states"] if row["phase_id"] == phase and row["parameter_s"] == target]
        if len(matches) != 1 or matches[0]["status"] != "pass":
            raise ValueError("missing unique admitted endpoint")
        row = matches[0]
        prefix = next(p for p in audit["prefix"]["states"] if p["state_id"] == row["state_id"])
        if prefix.get("comparable") is not True:
            raise ValueError("endpoint is outside the valid prefix")
        stage = run / "stages" / phase
        model_path, index_path = stage / "model.npz", stage / "steps/index.json"
        model = read_npz(model_path)
        index = read_json(index_path)["steps"]
        state_entries = [s for s in index if s["index"] == row["index"] and s["d"] == target
                         and s["is_original_target"] is True]
        if len(state_entries) != 1:
            raise ValueError("endpoint is not a unique original target")
        state_path = (stage / "steps" / state_entries[0]["file"]).resolve()
        if not state_path.is_relative_to(stage / "steps") or sha(state_path) != state_entries[0]["sha256"]:
            raise ValueError("endpoint file/hash mismatch")
        state = read_npz(state_path)
        for path in (audit_path, model_path, index_path, state_path):
            bindings[path.relative_to(root).as_posix()] = sha(path)
        hp = row["precision_evidence_decimal"]["80"]
        components = {key: [Decimal(value) for value in hp[key + "_internal_decimal"]]
                      for key in ("material", "regularization")}
        total = [Decimal(value) for value in hp["internal_decimal"]]
        multipliers = list(map(Decimal, row["measurements"]["top_normal_multipliers"]))
        nodes = []
        with localcontext() as context:
            context.prec = 160
            for ordinal, node in enumerate(model["top_nodes"]):
                node = int(node)
                dof = 2 * node + 1
                force, material, regularization = -total[dof], -components["material"][dof], -components["regularization"][dof]
                if force != multipliers[ordinal]:
                    raise ValueError("stored node force differs from independent normal-multiplier field")
                x = float(model["coordinates"][node, 0])
                current = sum((Fraction.from_float(float(v)) for v in
                               (model["coordinates"][node, 0], state["u_lift"][2*node], state["u_fluctuation"][2*node])), Fraction(0))
                nodes.append(dict(node_id=node, reference_x_mm=x, reference_y_mm=float(model["coordinates"][node, 1]),
                                  current_x_exact_split_fraction=f"{current.numerator}/{current.denominator}",
                                  current_x_display_mm=float(current), in_initial_solid_xspan=0 <= x <= 2,
                                  total_N=str(force), material_N=str(material), regularization_N=str(regularization),
                                  total_minus_component_sum_N=str(force-material-regularization)))
            negative = [n for n in nodes if Decimal(n["total_N"]) < 0]
            positive = [n for n in nodes if Decimal(n["total_N"]) > 0]
            def summed(items, key):
                return sum((Decimal(n[key]) for n in items), Decimal(0))
            net, neg, pos = summed(nodes, "total_N"), summed(negative, "total_N"), summed(positive, "total_N")
            aggregate = dict(negative_node_count=len(negative), positive_node_count=len(positive),
                             zero_node_count=len(nodes)-len(negative)-len(positive),
                             negative_total_N=str(neg), positive_total_N=str(pos), net_total_N=str(net),
                             positive_plus_negative_minus_net_N=str(pos+neg-net),
                             sum_absolute_nodal_reactions_N=str(pos-neg),
                             all_nodes_material_N=str(summed(nodes, "material_N")),
                             all_nodes_regularization_N=str(summed(nodes, "regularization_N")),
                             negative_set_material_N=str(summed(negative, "material_N")),
                             negative_set_regularization_N=str(summed(negative, "regularization_N")),
                             audit_net_force_N=row["measurements"]["normal_force"],
                             summed_nodes_minus_audit_net_N=str(net-Decimal(row["measurements"]["normal_force"])),
                             all_negative_nodes_outside_initial_solid_xspan=all(not n["in_initial_solid_xspan"] for n in negative))
        cases.append(dict(run=entry["run"], kind="TMC", mode=entry["mode"], h_mm=entry["h"],
                          state_id=row["state_id"], parameter_s=target,
                          measurement_precision_digits=80, verification_precision_pair=audit["verification_precision_pair"],
                          audit_status=audit["status"], prefix_comparable=True,
                          aggregate=aggregate, negative_nodes=negative, all_top_nodes=nodes))
    payload = dict(schema="contact_c1_local_reaction_diagnostic_v1", created_utc=datetime.now(timezone.utc).isoformat(),
                   source="stored independently audited HP80 residual arrays; no new FE or HP evaluation",
                   sign="positive is discrete normal reaction exerted on plane; negative is its opposite",
                   classification="reference x in inclusive [0,2] only; not a deformed contact-region classification",
                   limitations=["Nodal reaction is not Cauchy traction or contact pressure.",
                                "Material and regularization components do not independently satisfy equilibrium.",
                                "Positive/negative sums diagnose cancellation; no values are clipped or used to change path admission.",
                                "Arithmetic sums use saved HP80 decimal outputs at 160-digit summation precision; this is not a new 160-digit mechanics audit.",
                                "No continuum, mesh-convergence, unilateral-law or parameter-accuracy claim follows from these four endpoints."],
                   cases=cases, input_sha256=bindings, script_sha256=sha(Path(__file__).resolve()))
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
    plot_reactions(payload, output)
    print(json.dumps({"cases": len(cases), "negative_nodes": sum(c["aggregate"]["negative_node_count"] for c in cases),
                      "output_sha256": sha(output)}))
    return payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--selection", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    diagnose(args.root, args.selection, args.output)
