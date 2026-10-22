"""Launch the unique PROBE1 helper under unchanged SUP2; never archive or install."""
from __future__ import annotations

from datetime import datetime, timezone
import math
import os
from pathlib import Path
import sys
import time
import traceback

from windows_owned_process_sup2 import run_owned
from run_probe1 import (BASE, RUN, PARENT, PROTOCOL, finite_environment,
                        phase_pass, read_json, validate_protocol, write_new)


def main():
    root_start = float(os.environ["PROBE1_ROOT_START_MONOTONIC"])
    if not math.isfinite(root_start) or root_start > time.monotonic():
        raise ValueError("invalid original outer start clock")
    # Existing paths prove an earlier attempt. Never delete/reuse them and
    # never choose a different run number to get another execution window.
    if PARENT.exists():
        raise FileExistsError("parent_001 already exists; original attempt must be preserved")
    RUN.mkdir(exist_ok=False)
    started = time.monotonic()
    receipt = dict(schema="hf-ctipprobe1-launch-1", status="not_pass",
        root_start_monotonic=root_start, launch_start_monotonic=started,
        start_utc=datetime.now(timezone.utc).isoformat(), helper_window_seconds=4500,
        outer_window_seconds=4560, scientific_process_launches=None, viewer_process_launches=None,
        archive_owner="root_outer_bootstrap", archives_created_by_launcher=0,
        production_installations=0, external_retries=0)
    try:
        protocol, checked = validate_protocol()
        receipt["source_bindings"] = checked
        if time.monotonic() >= root_start+4490:
            raise TimeoutError("original helper window closed before unique launch")
        env = finite_environment(protocol)
        env["PROBE1_HELPER_DEADLINE"] = repr(root_start+4490.)
        command = [protocol["python_executable"], "-X", "utf8", "-B", str(BASE/"run_probe1.py")]
        record = run_owned(command, cwd=str(BASE), env=env, log=RUN/"helper_stdout.log",
            deadline=root_start+4495., seconds=4495., rss_limit=protocol["memory_limit_bytes"],
            instance_log_path=RUN/"helper_instances.ndjson",
            instance_identity=dict(stage="L-CTIPPROBE1", phase="original_shared_helper"))
        receipt["helper_supervision"] = record
        write_new(RUN/"helper_supervision.json", record)
        helper_path = RUN/"helper_receipt.json"
        if helper_path.exists():
            helper = read_json(helper_path)
            receipt.update(helper_status=helper["status"],
                scientific_process_launches=helper["scientific_process_launches"],
                viewer_process_launches=helper["viewer_process_launches"],
                actual_partial_observation=helper.get("actual_partial_observation"))
        if not phase_pass(record):
            raise RuntimeError("shared helper or same-instance cleanup failed")
        if receipt.get("helper_status") != "ready_for_visual_check":
            raise ValueError("helper did not complete numerical and pure display phases")
        if time.monotonic() > root_start+4500.:
            raise TimeoutError("original helper window exceeded including cleanup")
        receipt["status"] = "ready_for_visual_check"
        receipt["next_action"] = "root verifies outer cleanup, then one byte archive within original window and at most one check per new PNG"
    except BaseException as error:
        receipt["error"] = dict(type=type(error).__name__, message=str(error), traceback=traceback.format_exc())
    finally:
        receipt["end_utc"] = datetime.now(timezone.utc).isoformat()
        receipt["elapsed_since_launch_seconds"] = time.monotonic()-started
        receipt["elapsed_since_root_seconds"] = time.monotonic()-root_start
        write_new(RUN/"launch_receipt.json", receipt)
        print(receipt["status"], str(RUN/"launch_receipt.json"))
    return 0 if receipt["status"] == "ready_for_visual_check" else 1


if __name__ == "__main__":
    if (len(sys.argv) != 3 or sys.argv[1] != "--protocol"
            or Path(sys.argv[2]).resolve() != PROTOCOL):
        raise SystemExit("launch requires the frozen --protocol path; no alternate arguments")
    raise SystemExit(main())
