"""Read-only post-run check: after the one authorised solve and audit, the v4 guard must refuse every further launch.

Asks the guard's plan_launch (no directory, no mechanics, no dispatch) and records the answers.

Usage: python hf4_c2_v4_results/postrun_guard_check.py --output hf4_c2_v4_results/postrun/guard_check_001.json
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / "hf_repo"
sys.path.insert(0, str(REPO / "scripts"))
import contact_c2_launch_p1 as p1  # noqa: E402
import contact_c2_launch_v4 as launch  # noqa: E402

RUNS = ROOT / "hf4_c2_v4_results/experiments"
QUESTIONS = (("second solve into the used run", "solve", "mesh_h00625_v4"),
             ("second audit of the used run", "audit", "mesh_h00625_v4"),
             ("solve into a new run name", "solve", "mesh_h00625_v4_b"))


def snapshot():
    return sorted((p.relative_to(ROOT).as_posix(), p.stat().st_size) for p in RUNS.rglob("*"))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or output.is_relative_to(REPO) or output.is_relative_to(RUNS):
        parser.error("choose a new receipt path outside hf_repo and outside the guard's experiment root")
    protocol = REPO / "configs/contact_c2_v4.json"
    rows = []
    for label, action, run in QUESTIONS:
        before = snapshot()
        try:
            launch.plan_launch(action, RUNS / run, "mesh_h00625", protocol)
            outcome = dict(result="accepted")
        except p1.ContractError as error:
            outcome = dict(result="rejected", message=str(error))
        outcome.update(label=label, side_effect_free=snapshot() == before)
        outcome["status"] = "pass" if outcome["result"] == "rejected" and outcome["side_effect_free"] else "not_pass"
        rows.append(outcome)
    receipt = dict(schema="contact-c2-v4-postrun-guard-check-1", created_utc=datetime.now(timezone.utc).isoformat(),
                   scope="read-only plan_launch questions after the single authorised v4 solve and audit; not a run",
                   protocol_sha256=hashlib.sha256(protocol.read_bytes()).hexdigest(), guard_pinned_sha256=launch.PROTOCOL_SHA256,
                   experiment_root_entries=sorted(p.name for p in RUNS.iterdir()), cases=rows,
                   status="pass" if all(r["status"] == "pass" for r in rows) else "not_pass")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(receipt, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    print(json.dumps(dict(status=receipt["status"], cases=[(r["label"], r["result"], r.get("message")) for r in rows]), indent=1))
    return 0 if receipt["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
