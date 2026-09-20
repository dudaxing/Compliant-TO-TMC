"""Bounded subprocess wrapper; preserve stdout/stderr and timeout receipts."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from hf4_common import sha, timestamp, write_json


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("solve", "audit"), required=True)
    parser.add_argument("--run", required=True)
    parser.add_argument("--h", type=float)
    parser.add_argument("--amplitude", type=float)
    args = parser.parse_args()
    scripts = Path(__file__).resolve().parent
    protocol = scripts.parent / "configs/contact_reference_a0_v1.json"
    spec = json.loads(protocol.read_text(encoding="utf-8"))
    run = Path(args.run).resolve()
    run.parent.mkdir(parents=True, exist_ok=True)
    logfile = run.parent / (run.name + "." + args.mode + ".log")
    receipt = logfile.with_suffix(".receipt.json")
    if logfile.exists() or receipt.exists():
        parser.error("log/receipt already exists; no rerun over existing evidence")
    if args.mode == "solve":
        if args.h is None or args.amplitude is None:
            parser.error("solve requires --h and --amplitude")
        command = [sys.executable, str(scripts / "run_contact_reference_a0.py"),
                   "--output", str(run), "--h", str(args.h), "--amplitude", str(args.amplitude)]
        seconds = spec["budget"]["subprocess_wall_seconds"]
    else:
        command = [sys.executable, str(scripts / "audit_contact_reference_a0.py"),
                   "--run", str(run), "--output", str(run / "audit.json")]
        seconds = spec["budget"]["maximum_audit_seconds_per_path"]
    started = time.perf_counter()
    start_utc = timestamp()
    environment = dict(os.environ)
    environment.update(OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    timed_out = False
    # The case parent is unrelated to imports: all paths are derived from the
    # script, and the evaluator never imports LF/source archives.
    with logfile.open("x", encoding="utf-8") as stream:
        try:
            completed = subprocess.run(command, cwd=run.parent, env=environment,
                                       stdout=stream, stderr=subprocess.STDOUT, timeout=seconds)
            code = completed.returncode
        except subprocess.TimeoutExpired:
            timed_out, code = True, None
    write_json(receipt, {"started_utc": start_utc, "finished_utc": timestamp(),
               "elapsed_seconds": time.perf_counter() - started, "timeout_seconds": seconds,
               "timed_out": timed_out, "returncode": code, "command": command,
               "thread_limits": {k: environment[k] for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")},
               "protocol_sha256": sha(protocol), "log_sha256": sha(logfile)})
    print(json.dumps({"run": run.name, "mode": args.mode, "returncode": code, "timed_out": timed_out,
                      "elapsed_seconds": time.perf_counter() - started}), flush=True)
    raise SystemExit(124 if timed_out else code)
