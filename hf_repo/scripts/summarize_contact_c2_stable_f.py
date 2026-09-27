"""Summarise the stable-F no-solve validation records (reads saved JSON only; no mechanics).

Writes one machine-readable summary of: the bounded-run receipts (budget), the manufactured phase (candidate and
the non-gating legacy control, per case), the saved-state phases (candidate, legacy control, original audit values)
and the kernel timing. Every input file is bound by SHA-256.

Usage: python hf_repo/scripts/summarize_contact_c2_stable_f.py --root hf4_c2_stable_f_validation --output <new json>
"""
from __future__ import annotations

import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class Reader:
    def __init__(self):
        self.bound = {}

    def json(self, path):
        path = Path(path)
        self.bound[path.resolve().relative_to(ROOT).as_posix()] = sha(path)
        return json.loads(path.read_text(encoding="utf-8"))


def values(checks):
    return {c["name"]: float(Decimal(c["value"])) for c in checks}


def manufactured(reader, directory):
    rows = []
    for path in sorted(directory.glob("*/result.json")):
        result = reader.json(path)
        candidate_fail = sorted({c["name"] for d in result["directions"] for c in d["checks"] if c["status"] != "pass"})
        legacy_status = [d["legacy_control"].get("status", "error") for d in result["directions"]]
        worst = lambda key, family: max(values(d[key]["checks"] if key else d["checks"]).get(family, 0.0) for d in result["directions"])
        hp = {d["direction"]: reader.json(path.parent / f"hp_{d['direction']}.json")["120"] for d in result["directions"]}

        def flat(value):
            out, stack = [], [value]
            while stack:
                item = stack.pop(0)
                if isinstance(item, list):
                    stack[0:0] = item
                else:
                    out.append(item)
            return out

        def candidate_kinematics():
            # Recomputed from the saved candidate arrays: ulp over components with a nonzero exact value only
            # (spacing(0) is subnormal, so an ulp count at an exactly-zero component is meaningless); the
            # absolute error at exactly-zero components is reported separately.
            out = {}
            for k in ("F", "G", "J"):
                ulp, zero_abs = 0.0, 0.0
                for d in result["directions"]:
                    with np.load(path.parent / f"production_{d['direction']}.npz", allow_pickle=False) as archive:
                        actual = archive[k].ravel()
                    reader.bound[(path.parent / f"production_{d['direction']}.npz").resolve().relative_to(ROOT).as_posix()] = sha(path.parent / f"production_{d['direction']}.npz")
                    reference = [Decimal(x) for x in flat(hp[d["direction"]][k + "_decimal"])]
                    for a, b in zip(actual, reference):
                        error = abs(Decimal.from_float(float(a)) - b)
                        if b == 0:
                            zero_abs = max(zero_abs, float(error))
                        else:
                            ulp = max(ulp, float(error / Decimal.from_float(float(np.spacing(float(b))))))
                out[k] = dict(max_ulp_nonzero_reference=ulp, max_abs_error_at_zero_reference=zero_abs)
            return out

        def legacy_kinematics():
            # The legacy control saved only aggregate metrics; its max absolute error is well defined, its saved
            # max-ulp value is not (it may come from an exactly-zero component), so only the former is reported.
            return {k: dict(max_abs_error=max(float(Decimal(d["legacy_control"]["kinematics"][k]["max_absolute_error"])) for d in result["directions"]))
                    for k in ("F", "G", "J")}

        candidate_kin = candidate_kinematics()
        legacy_kin = legacy_kinematics()
        candidate_abs = {k: max(float(Decimal(d["kinematics"][k]["max_absolute_error"])) for d in result["directions"]) for k in ("F", "G", "J")}
        rows.append(dict(case=result["case"], candidate_status=result["status"], candidate_failing_checks=candidate_fail,
                         legacy_control_status="pass" if all(s == "pass" for s in legacy_status) else "not_pass",
                         candidate_total_force=worst(None, "candidate_total_force"), legacy_total_force=worst("legacy_control", "candidate_total_force"),
                         candidate_total_tangent=worst(None, "candidate_total_tangent"), legacy_total_tangent=worst("legacy_control", "candidate_total_tangent"),
                         candidate_kinematics=candidate_kin, candidate_max_abs_error=candidate_abs, legacy_kinematics=legacy_kin))
    discriminating = [r["case"] for r in rows if r["candidate_status"] == "pass" and r["legacy_control_status"] != "pass"]
    shared = [r["case"] for r in rows if r["candidate_status"] != "pass" and r["legacy_control_status"] != "pass"]
    only_candidate = [r["case"] for r in rows if r["candidate_status"] != "pass" and r["legacy_control_status"] == "pass"]
    return dict(cases=len(rows), candidate_pass=sum(r["candidate_status"] == "pass" for r in rows),
                legacy_control_pass=sum(r["legacy_control_status"] == "pass" for r in rows),
                fixed_by_candidate=discriminating, failing_for_both=shared, failing_only_for_candidate=only_candidate,
                candidate_kinematics_over_cases={k: {m: max(r["candidate_kinematics"][k][m] for r in rows) for m in ("max_ulp_nonzero_reference", "max_abs_error_at_zero_reference")} for k in ("F", "G", "J")},
                kinematics_note="candidate ulp recomputed from the saved arrays over nonzero exact components; the legacy control saved only aggregates, of which the max absolute error is reported (its saved max-ulp can stem from an exactly-zero component and is not used)",
                rows=rows)


def saved(reader, directory):
    rows = []
    for path in sorted(directory.glob("*/result.json")):
        result = reader.json(path)
        c, l, o = values(result["checks"]), values(result["legacy_control"]["checks"]), values(result["original_checks"])
        rows.append(dict(state=result["case"], candidate_status=result["status"], original_audit_status=result["original_audit_status"],
                         legacy_control_status=result["legacy_control"]["status"], force_scale=float(Decimal(result["force_scale"])),
                         candidate_total_force=c["candidate_total_force"], legacy_total_force=l["candidate_total_force"],
                         original_total_force=o["production_vs_hp80_total_force"], candidate_total_tangent=c["candidate_total_tangent"],
                         legacy_total_tangent=l["candidate_total_tangent"], original_total_tangent=o["production_vs_hp80_total_tangent"],
                         candidate_residual_jvp_vs_hp=c["residual_only_jvp_vs_independent"]))
    reproduced = all(abs(r["legacy_total_force"] - r["original_total_force"]) <= 1e-12 * r["original_total_force"]
                     and abs(r["legacy_total_tangent"] - r["original_total_tangent"]) <= 1e-12 * r["original_total_tangent"] for r in rows)
    return dict(states=len(rows), candidate_pass=sum(r["candidate_status"] == "pass" for r in rows),
                original_pass=sum(r["original_audit_status"] == "pass" for r in rows), legacy_control_reproduces_original_errors=reproduced,
                candidate_max_total_force=max(r["candidate_total_force"] for r in rows), legacy_max_total_force=max(r["legacy_total_force"] for r in rows),
                candidate_max_total_tangent=max(r["candidate_total_tangent"] for r in rows), legacy_max_total_tangent=max(r["legacy_total_tangent"] for r in rows),
                candidate_max_residual_jvp_vs_hp=max(r["candidate_residual_jvp_vs_hp"] for r in rows), rows=rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("choose a new output path")
    reader = Reader()
    receipts = [dict(run=p.parent.name, **{k: reader.json(p)[k] for k in ("category", "status", "returncode", "timed_out", "elapsed_seconds")})
                for p in sorted(args.root.glob("*/execution_receipt.json"))]
    summary = dict(schema="contact-c2-stable-f-validation-summary-1",
                   scope="saved validation records only; fixed states and manufactured fields; no equilibrium path; not a path admission",
                   receipts=receipts, validation_seconds_used=sum(r["elapsed_seconds"] for r in receipts if r["category"] != "p1"),
                   validation_budget_seconds=3600,
                   manufactured=manufactured(reader, args.root / "manufactured_001/driver_output"),
                   saved_plan_selection=saved(reader, args.root / "saved_002/driver_output"),
                   saved_all_c2_and_c1=saved(reader, args.root / "saved_all_c2_001/driver_output"),
                   timing=reader.json(args.root / "timing_001/timing.json"))
    summary["input_sha256"] = reader.bound
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(summary, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    m, s, a = summary["manufactured"], summary["saved_plan_selection"], summary["saved_all_c2_and_c1"]
    print(json.dumps(dict(seconds=round(summary["validation_seconds_used"], 1), manufactured=(m["candidate_pass"], m["cases"], m["fixed_by_candidate"], m["failing_for_both"], m["failing_only_for_candidate"]),
                          saved=(s["candidate_pass"], s["states"]), all=(a["candidate_pass"], a["states"], a["legacy_control_reproduces_original_errors"]),
                          kin=m["candidate_kinematics_over_cases"]), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
