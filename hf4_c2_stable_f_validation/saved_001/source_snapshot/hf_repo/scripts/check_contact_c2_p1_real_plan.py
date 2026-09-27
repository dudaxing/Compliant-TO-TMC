"""Read-only P1 check against the real frozen C2 v3 contract and restored evidence (no FE, no dispatch).

The P1 unit tests replace every backend and use synthetic admission files. This script instead asks the
unchanged P1 planner about the genuine repository: the frozen v3 protocol, its 33-file implementation
manifest, the saved-field admission gate and the two C1 baseline audits restored from the S0 release
assets, and the three historical C2 runs with their receipts. It only calls ``plan_launch`` (which creates
no directory, imports no mechanics and dispatches nothing) and records whether each case is accepted or
rejected, with the rejection message. The receipt goes to a new file; nothing else is written.

Usage (from the repository root, restored hf4-c2-s0-c1_runs-v1 and hf4-c2-s0-c2_runs-v1 assets required):
    python hf_repo/scripts/check_contact_c2_p1_real_plan.py --output review_runs/p1_real_plan_001.json
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO.parent
sys.path.insert(0, str(REPO / "scripts"))

import contact_c2_launch_p1 as p1  # noqa: E402


def attempt(label, expect, function):
    """Run one planning question; a rejection is a ContractError, anything else is an unexpected error."""

    before = sorted(p.as_posix() for p in (ROOT / "review_runs").rglob("*")) if (ROOT / "review_runs").exists() else []
    try:
        plan = function()
        outcome = dict(result="accepted", case_id=plan["case_id"], action=plan["action"], timeout_seconds=plan["timeout_seconds"],
                       bound_inputs=len(plan["input_sha256"]))
    except p1.ContractError as error:
        outcome = dict(result="rejected", message=str(error))
    except Exception as error:  # noqa: BLE001 - recorded, and the check fails
        outcome = dict(result="unexpected_error", type=type(error).__name__, message=str(error))
    after = sorted(p.as_posix() for p in (ROOT / "review_runs").rglob("*")) if (ROOT / "review_runs").exists() else []
    outcome.update(label=label, expected=expect, side_effect_free=before == after, status="pass" if outcome["result"] == expect and before == after else "not_pass")
    return outcome


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        parser.error("choose a new receipt path")
    protocol = REPO / "configs/contact_c2_v3.json"
    fresh = ROOT / "review_runs/p1_real_plan_fresh_root"
    historical = ROOT / "hf4_c2_diagnostics/experiments"
    rows = [
        attempt("fresh root: first frozen case padding_2p5 (solve)", "accepted",
                lambda: p1.plan_launch("solve", fresh / "padding_2p5", "padding_2p5", protocol)),
        attempt("fresh root: second case first (outer_free, out of the frozen serial order)", "rejected",
                lambda: p1.plan_launch("solve", fresh / "outer_free", "outer_free", protocol)),
        attempt("fresh root: undeclared baseline case", "rejected",
                lambda: p1.plan_launch("solve", fresh / "baseline", "baseline", protocol)),
        attempt("fresh root: audit without a solve", "rejected",
                lambda: p1.plan_launch("audit", fresh / "padding_2p5", "padding_2p5", protocol)),
        attempt("historical root: a fourth solve after the three frozen paths", "rejected",
                lambda: p1.plan_launch("solve", historical / "mesh_h00625_again", "mesh_h00625", protocol)),
        attempt("historical root: repeat the audit of the failed fine-mesh path", "rejected",
                lambda: p1.plan_launch("audit", historical / "mesh_h00625", "mesh_h00625", protocol)),
        attempt("run directory inside hf_repo", "rejected",
                lambda: p1.plan_launch("solve", REPO / "results/padding_2p5", "padding_2p5", protocol)),
    ]
    frozen = protocol.read_bytes()
    edits = {"solver tolerance (the motivating case)": ("solver", None), "budget: one more path": ("budget", "maximum_paths"),
             "one trailing space (bytes only)": (None, None)}
    with tempfile.TemporaryDirectory(prefix="p1-edited-protocol-", dir=REPO / "configs") as directory:
        for label, (group, key) in edits.items():
            document = json.loads(frozen)
            if group == "solver":
                key = next(k for k in document["solver"] if "tol" in k)
                document["solver"][key] = document["solver"][key] * 10
                data = json.dumps(document, indent=2, ensure_ascii=False).encode("utf-8")
            elif group == "budget":
                document["budget"][key] += 1
                data = json.dumps(document, indent=2, ensure_ascii=False).encode("utf-8")
            else:
                data = frozen + b" "
            edited = Path(directory) / ("edited_" + str(len(rows)) + ".json")
            edited.write_bytes(data)
            rows.append(attempt("edited protocol copy: " + label, "rejected",
                                lambda edited=edited: p1.plan_launch("solve", fresh / "padding_2p5", "padding_2p5", edited)))
    stray = [p.as_posix() for p in (REPO / "configs").glob("p1-edited-protocol-*")]
    receipt = dict(schema="contact-c2-p1-real-plan-check-1", created_utc=datetime.now(timezone.utc).isoformat(),
                   scope="read-only plan_launch questions against the genuine v3 contract and restored evidence; no directory created, no mechanics imported, nothing dispatched",
                   protocol_sha256=hashlib.sha256(frozen).hexdigest(), p1_source_sha256={name: p1.sha(REPO / name) for name in p1.P1_FILES},
                   fresh_root_created=fresh.exists(), temporary_protocol_copies_left=stray, cases=rows,
                   status="pass" if all(r["status"] == "pass" for r in rows) and not fresh.exists() and not stray else "not_pass")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(receipt, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    print(json.dumps(dict(status=receipt["status"], cases=[(r["label"], r["result"], r["status"]) for r in rows]), indent=1, ensure_ascii=False))
    return 0 if receipt["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
