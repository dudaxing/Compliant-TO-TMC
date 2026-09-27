"""Read-only v4 launch check against the real frozen contract and restored evidence (no FE, no dispatch).

Asks the v4 guard's plan_launch (which creates no directory, imports no mechanics and dispatches nothing) a set
of questions and records the answers. Requires the restored S0 assets (C1 baseline audits) and the saved-field
admission inputs on this machine, exactly as a real launch would.

Usage: python hf_repo/scripts/check_contact_c2_v4_launch.py --output <new json outside hf_repo>
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import sys
import tempfile

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO.parent
sys.path.insert(0, str(REPO / "scripts"))
import contact_c2_launch_p1 as p1  # noqa: E402
import contact_c2_launch_v4 as launch  # noqa: E402
import contact_c2_v4_contract as contract  # noqa: E402


def snapshot():
    base = ROOT / "hf4_c2_v4_results"
    return sorted(p.as_posix() for p in base.rglob("*")) if base.exists() else []


def attempt(label, expect, function):
    before = snapshot()
    try:
        plan = function()
        outcome = dict(result="accepted", action=plan["action"], case_id=plan["case_id"], timeout_seconds=plan["timeout_seconds"],
                       bound_inputs=len(plan["input_sha256"]), launch_identity=plan["launch_identity"])
    except p1.ContractError as error:
        outcome = dict(result="rejected", message=str(error))
    except Exception as error:  # noqa: BLE001 - recorded; the check then fails
        outcome = dict(result="unexpected_error", type=type(error).__name__, message=str(error))
    outcome.update(label=label, expected=expect, side_effect_free=snapshot() == before)
    outcome["status"] = "pass" if outcome["result"] == expect and outcome["side_effect_free"] else "not_pass"
    return outcome


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or output.is_relative_to(REPO):
        parser.error("choose a new receipt path outside hf_repo")
    protocol = REPO / contract.PROTOCOL_PATH
    runs = ROOT / "hf4_c2_v4_results/experiments"
    rows = [
        attempt("solve mesh_h00625 into a fresh experiment root", "accepted",
                lambda: launch.plan_launch("solve", runs / "mesh_h00625_v4", "mesh_h00625", protocol)),
        attempt("audit before any solve", "rejected",
                lambda: launch.plan_launch("audit", runs / "mesh_h00625_v4", "mesh_h00625", protocol)),
        attempt("undeclared case padding_2p5", "rejected",
                lambda: launch.plan_launch("solve", runs / "padding_2p5", "padding_2p5", protocol)),
        attempt("run directory inside hf_repo", "rejected",
                lambda: launch.plan_launch("solve", REPO / "results/mesh_h00625_v4", "mesh_h00625", protocol)),
        attempt("the frozen v3 protocol passed as the v4 protocol", "rejected",
                lambda: launch.plan_launch("solve", runs / "mesh_h00625_v4", "mesh_h00625", REPO / contract.V3_PROTOCOL_PATH)),
    ]
    frozen = json.loads(protocol.read_text(encoding="utf-8"))
    edits = {"solver tolerance x10": ("solver", "tolerance", lambda v: v * 10),
             "one more path in the budget": ("budget", "maximum_paths", lambda v: v + 1),
             "kernel version renamed": ("kernel", "kernel_version", lambda v: v + "_x"),
             "environment numpy 2.3.5": ("environment", "numpy", lambda v: "2.3.5")}
    with tempfile.TemporaryDirectory(prefix="v4-edited-protocol-", dir=REPO / "configs") as directory:
        exact_copy = Path(directory) / "contact_c2_v4.json"
        exact_copy.write_bytes(protocol.read_bytes())
        rows.append(attempt("byte-identical copy at another path", "rejected",
                            lambda: launch.plan_launch("solve", runs / "mesh_h00625_v4", "mesh_h00625", exact_copy)))
        for label, (section, key, change) in edits.items():
            edited = json.loads(json.dumps(frozen))
            edited[section][key] = change(edited[section][key])
            path = Path(directory) / ("edited_" + key + ".json")
            path.write_text(json.dumps(edited, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            rows.append(attempt("edited protocol: " + label, "rejected",
                                lambda path=path: launch.plan_launch("solve", runs / "mesh_h00625_v4", "mesh_h00625", path)))
    stray = [p.as_posix() for p in (REPO / "configs").glob("v4-edited-protocol-*")]
    receipt = dict(schema="contact-c2-v4-launch-check-1", created_utc=datetime.now(timezone.utc).isoformat(),
                   scope="read-only plan_launch questions against the real frozen v4 contract and restored evidence; no directory created, no mechanics imported, nothing dispatched; not a run",
                   protocol_sha256=hashlib.sha256(protocol.read_bytes()).hexdigest(), guard_pinned_sha256=launch.PROTOCOL_SHA256,
                   environment=dict(python=platform.python_version(), mismatches=contract.environment_mismatches()),
                   experiments_root_created=runs.exists(), temporary_protocol_copies_left=stray, cases=rows,
                   status="pass" if all(r["status"] == "pass" for r in rows) and not runs.exists() and not stray else "not_pass")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(receipt, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    print(json.dumps(dict(status=receipt["status"], cases=[(r["label"], r["result"], r.get("message", r.get("bound_inputs"))) for r in rows]),
                     indent=1, ensure_ascii=False))
    return 0 if receipt["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
