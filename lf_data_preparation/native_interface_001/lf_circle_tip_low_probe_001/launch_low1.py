"""Launch the one LOW1 shared helper under unchanged SUP2; no science here."""
from __future__ import annotations

from datetime import datetime, timezone
import math
import os
from pathlib import Path
import sys
import time
import traceback

from windows_owned_process_sup2 import run_owned
from run_low1 import (BASE, RUN, PROTOCOL, finite_environment, phase_pass,
                      read_json, validate_protocol, write_new)


def main():
    root_start = float(os.environ["LOW1_ROOT_START_MONOTONIC"])
    if not math.isfinite(root_start) or root_start > time.monotonic():
        raise ValueError("invalid original outer start clock")
    # A previous run directory is an earlier attempt, never a reusable window.
    RUN.mkdir(exist_ok=False)
    started = time.monotonic()
    receipt = dict(schema="hf-ctiplow1-launch-1", status="not_pass",
        root_start_monotonic=root_start, launch_start_monotonic=started,
        start_utc=datetime.now(timezone.utc).isoformat(), helper_window_seconds=9000,
        outer_window_seconds=9060, parent_process_launches=None,
        probe_process_launches=None, viewer_process_launches=None,
        archive_owner="root_outer_bootstrap", archives_created_by_launcher=0,
        production_installations=0, external_retries=0)
    try:
        protocol, checked = validate_protocol()
        receipt["source_bindings"] = checked
        if time.monotonic() >= root_start + 8900.:
            raise TimeoutError("original helper content window closed before unique launch")
        env = finite_environment(protocol)
        env["LOW1_HELPER_DEADLINE"] = repr(root_start + 8900.)
        command = [protocol["python_executable"], "-X", "utf8", "-B", str(BASE / "run_low1.py")]
        record = run_owned(command, cwd=str(BASE), env=env,
            log=RUN / "helper_stdout.log", deadline=root_start + 8910., seconds=8910.,
            rss_limit=protocol["memory_limit_bytes"],
            instance_log_path=RUN / "helper_instances.ndjson",
            instance_identity=dict(stage="L-CTIPLOW1", phase="original_shared_helper"))
        receipt["helper_supervision"] = record
        write_new(RUN / "helper_supervision.json", record)
        helper_path = RUN / "helper_receipt.json"
        if helper_path.exists():
            helper = read_json(helper_path)
            receipt.update(helper_status=helper["status"],
                parent_process_launches=helper["parent_process_launches"],
                probe_process_launches=helper["probe_process_launches"],
                viewer_process_launches=helper["viewer_process_launches"],
                actual_partial_observation=helper.get("actual_partial_observation"))
        if not phase_pass(record):
            raise RuntimeError("shared helper or same-instance cleanup failed")
        if receipt.get("helper_status") != "ready_for_visual_check":
            raise ValueError("helper did not complete both numerical phases and pure display")
        if time.monotonic() >= root_start + 9000.:
            raise TimeoutError("original helper window exceeded including cleanup")
        receipt["status"] = "ready_for_visual_check"
        receipt["next_action"] = ("outer verifies cleanup and seals bytes within original 9000-second window; "
                                  "root may inspect each of four new PNGs at most once")
    except BaseException as error:
        receipt["error"] = dict(type=type(error).__name__, message=str(error),
                                 traceback=traceback.format_exc())
    finally:
        receipt["end_utc"] = datetime.now(timezone.utc).isoformat()
        receipt["elapsed_since_launch_seconds"] = time.monotonic() - started
        receipt["elapsed_since_root_seconds"] = time.monotonic() - root_start
        write_new(RUN / "launch_receipt.json", receipt)
        print(receipt["status"], str(RUN / "launch_receipt.json"), flush=True)
    return 0 if receipt["status"] == "ready_for_visual_check" else 1


if __name__ == "__main__":
    if (len(sys.argv) != 3 or sys.argv[1] != "--protocol"
            or Path(sys.argv[2]).resolve() != PROTOCOL):
        raise SystemExit("launch requires the frozen --protocol path; no alternate arguments")
    raise SystemExit(main())
