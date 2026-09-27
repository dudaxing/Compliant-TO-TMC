"""Compare the v4 re-test of mesh_h00625 with the frozen v3 history (read-only: no FE, no HP arithmetic).

Reads the two audit summaries with their per-state audit details (each checked against the SHA-256 bound in its
audit summary), the two controller records (checked against the stage result) and the four receipts, and writes a
new write-once directory with comparison.json, a figure and output hashes. Needs the v3 run restored from the S0
release assets and the v4 large payloads present (see mesh_h00625_v4.external_payloads.json).

Usage: python hf4_c2_v4_results/compare_v4_with_v3.py --output hf4_c2_v4_results/comparison_001
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = {"v3": ROOT / "hf4_c2_diagnostics/experiments/mesh_h00625",
        "v4": ROOT / "hf4_c2_v4_results/experiments/mesh_h00625_v4"}
STAGE = "stages/uniform_tmc"
CHECKS = ("production_vs_hp80_total_force", "production_vs_hp80_total_tangent", "production_vs_hp80_material_force",
          "production_vs_hp80_regularization_force", "production_vs_hp80_material_tangent",
          "production_vs_hp80_regularization_tangent", "production_relative_residual")
COUNTS = ("kernel_calls", "successful_kernel_calls", "newton_base_checks", "predictors")
SECONDS = ("total", "kernel_and_transfer", "first_kernel_including_compile", "assembly", "sparse_solve", "callback")

inputs = {}


def read_bytes(path):
    data = path.read_bytes()
    inputs[path.relative_to(ROOT).as_posix()] = hashlib.sha256(data).hexdigest()
    return data


def read_json(path):
    return json.loads(read_bytes(path).decode("utf-8"))


def load_run(tag):
    run = RUNS[tag]
    audit = read_json(run / "audit.json")
    states = []
    for row in audit["states"]:
        data = read_bytes(run / row["detail_file"])
        if hashlib.sha256(data).hexdigest() != row["detail_sha256"]:
            raise SystemExit(f"{tag}: {row['detail_file']} does not match the hash bound in audit.json")
        detail = json.loads(data.decode("utf-8"))
        checks = {check["name"]: check for check in detail["checks"]}
        states.append(dict(row=row, checks=checks))
    controller_bytes = read_bytes(run / STAGE / "controller_full.json.gz")
    stage_result = read_json(run / STAGE / "result.json")
    if hashlib.sha256(controller_bytes).hexdigest() != stage_result["controller_full_sha256"]:
        raise SystemExit(f"{tag}: controller_full.json.gz does not match the stage result")
    controller = json.loads(gzip.decompress(controller_bytes).decode("utf-8"))
    receipts = {action: read_json(run.parent / f"{run.name}.{action}.receipt.json") for action in ("solve", "audit")}
    return dict(audit=audit, states=states, controller=controller, receipts=receipts)


def relative(a, b):
    with localcontext() as context:
        context.prec = 60
        a, b = Decimal(a), Decimal(b)
        return float(abs(a - b) / abs(b)) if b != 0 else float(abs(a - b))


def per_state(v3, v4):
    rows = []
    for s3, s4 in zip(v3["states"], v4["states"], strict=True):
        r3, r4 = s3["row"], s4["row"]
        if (r3["state_id"], r3["parameter_s"]) != (r4["state_id"], r4["parameter_s"]):
            raise SystemExit(f"state order differs: {r3['state_id']} {r3['parameter_s']} vs {r4['state_id']} {r4['parameter_s']}")
        u3 = v3["controller"]["accepted_steps"][r3["index"]]["u_display"]
        u4 = v4["controller"]["accepted_steps"][r4["index"]]["u_display"]
        scale = max(abs(x) for x in u3)
        rows.append(dict(
            index=r4["index"], d_mm=r4["parameter_s"], bisection_depth=r4["bisection_depth"], is_original_target=r4["is_original_target"],
            status=dict(v3=r3["status"], v4=r4["status"]),
            checks={name: dict(limit=s4["checks"][name]["limit"], v3=float(Decimal(s3["checks"][name]["value"])),
                               v4=float(Decimal(s4["checks"][name]["value"])), v3_status=s3["checks"][name]["status"],
                               v4_status=s4["checks"][name]["status"]) for name in CHECKS},
            normal_force_n=dict(v3=float(Decimal(r3["normal_force_raw"])) if r3["normal_force_raw"] is not None else None,
                                v4=float(Decimal(r4["normal_force_raw"])),
                                relative_difference=relative(r4["normal_force_raw"], r3["normal_force_raw"]) if r3["normal_force_raw"] is not None else None),
            displacement_relative_max_difference=(max(abs(a - b) for a, b in zip(u4, u3, strict=True)) / scale) if scale > 0 else max(abs(a - b) for a, b in zip(u4, u3, strict=True)),
            state_bitwise_identical=v3["controller"]["accepted_steps"][r3["index"]]["state_sha256"] == v4["controller"]["accepted_steps"][r4["index"]]["state_sha256"]))
    return rows


def controller_comparison(c3, c4):
    def accepted(c):
        return [(s["d"], s["bisection_depth"], s["is_original_target"], s["newton_checks"]) for s in c["accepted_steps"]]

    def failed(c):
        return [(f["from_displacement"], f["attempted_displacement"], f["depth"], f["code"]) for f in c["failed_attempts"]]

    return dict(
        accepted_sequence_identical=accepted(c3) == accepted(c4),
        accepted_sequence=[dict(d_mm=d, bisection_depth=b, is_original_target=o, newton_checks=n) for d, b, o, n in accepted(c4)],
        failed_attempts_identical=failed(c3) == failed(c4),
        failed_attempts=[dict(from_mm=a, attempted_mm=b, depth=c, code=e) for a, b, c, e in failed(c4)],
        failed_attempt_reasons=sorted({f["reason"] for f in c4["failed_attempts"]}),
        record_lengths={key: dict(v3=len(c3[key]), v4=len(c4[key])) for key in ("trials", "newton_history", "linear_solve_diagnostics")},
        counters={key: dict(v3=c3["timing_seconds"][key], v4=c4["timing_seconds"][key]) for key in COUNTS},
        seconds={key: dict(v3=c3["timing_seconds"][key], v4=c4["timing_seconds"][key],
                           ratio=c4["timing_seconds"][key] / c3["timing_seconds"][key]) for key in SECONDS},
        maximum_bisection_depth=dict(v3=c3["maximum_bisection_depth"], v4=c4["maximum_bisection_depth"]),
        status=dict(v3=c3["status"], v4=c4["status"]), target_reached=dict(v3=c3["target_reached"], v4=c4["target_reached"]))


def extreme(rows, run, name):
    index = max(range(len(rows)), key=lambda i: rows[i]["checks"][name][run])
    return dict(value=rows[index]["checks"][name][run], index=rows[index]["index"], d_mm=rows[index]["d_mm"])


def figure(rows, directory):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["svg.hashsalt"] = "hf4-c2-v4-comparison-001"
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.0), constrained_layout=True)
    for axis, (name, title) in zip(axes, (("production_vs_hp80_total_force", "total internal force"),
                                           ("production_vs_hp80_total_tangent", "total tangent action"))):
        limit = float(Decimal(rows[0]["checks"][name]["limit"]))
        for run, style in (("v3", dict(color="#b2182b", marker="o", label="v3 kernel (history, NOT_PASS)")),
                           ("v4", dict(color="#2166ac", marker="s", label="v4 compensated kernel"))):
            points = [(row["d_mm"], row["checks"][name][run]) for row in rows if row["checks"][name][run] > 0]
            axis.semilogy([p[0] for p in points], [p[1] for p in points], linewidth=1.2, markersize=4, **style)
        axis.axhline(limit, color="black", linestyle="--", linewidth=1.0, label=f"audit gate {limit:.0e}")
        axis.set_xlabel("prescribed mean drive d (mm)")
        axis.set_ylabel("relative error vs 80-digit reference")
        axis.set_title(f"mesh_h00625: {title}")
        axis.grid(True, which="both", linewidth=0.3, alpha=0.5)
        axis.legend(fontsize=8, loc="upper left")
    fig.savefig(directory / "force_tangent_error.png", dpi=150, metadata={"Software": None})
    fig.savefig(directory / "force_tangent_error.svg", metadata={"Date": None})
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        parser.error("the output directory must be new")
    v3, v4 = load_run("v3"), load_run("v4")
    rows = per_state(v3, v4)
    summary = dict(
        v4_audit_status=v4["audit"]["status"], v3_audit_status=v3["audit"]["status"],
        v4_prefix_length=v4["audit"]["prefix"]["prefix_length"], v3_prefix_length=v3["audit"]["prefix"]["prefix_length"],
        v3_first_invalid_state=v3["audit"]["prefix"]["first_invalid_state_id"],
        maxima={name: dict(v3=extreme(rows, "v3", name), v4=extreme(rows, "v4", name), limit=rows[0]["checks"][name]["limit"])
                for name in CHECKS},
        final_state={name: dict(v3=rows[-1]["checks"][name]["v3"], v4=rows[-1]["checks"][name]["v4"]) for name in CHECKS},
        normal_force_maximum_relative_difference=max(r["normal_force_n"]["relative_difference"] for r in rows
                                                     if r["normal_force_n"]["relative_difference"] is not None),
        displacement_maximum_relative_difference=max(r["displacement_relative_max_difference"] for r in rows),
        bitwise_identical_states=sum(r["state_bitwise_identical"] for r in rows))
    receipts = {run: {action: dict(elapsed_seconds=data["receipts"][action]["elapsed_seconds"],
                                   timeout_seconds=data["receipts"][action]["timeout_seconds"],
                                   returncode=data["receipts"][action]["returncode"],
                                   protocol_sha256=data["receipts"][action]["protocol_sha256"]) for action in ("solve", "audit")}
                for run, data in (("v3", v3), ("v4", v4))}
    record = dict(
        schema="hf4-c2-v4-vs-v3-comparison-1", created_utc=datetime.now(timezone.utc).isoformat(),
        scope=("read-only comparison of the v4 re-test with the frozen v3 history of the same case; no FE, no HP arithmetic; "
               "the v3 history stays NOT_PASS; checks and limits are the frozen audit's"),
        runs={run: path.relative_to(ROOT).as_posix() for run, path in RUNS.items()},
        summary=summary, controller=controller_comparison(v3["controller"], v4["controller"]), receipts=receipts,
        per_state=rows, inputs_sha256=dict(sorted(inputs.items())))
    output.mkdir(parents=True)
    with (output / "comparison.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(record, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    figure(rows, output)
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir())}
    with (output / "output_sha256.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(hashes, stream, indent=2)
        stream.write("\n")
    print(json.dumps(dict(summary=summary, controller_identical=dict(
        accepted=record["controller"]["accepted_sequence_identical"], failed=record["controller"]["failed_attempts_identical"])), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
