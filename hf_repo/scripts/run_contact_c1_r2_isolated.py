"""External time budget and immutable logs for a C1 solve or independent audit."""
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
    parser.add_argument("--action", choices=("solve", "audit"), required=True)
    parser.add_argument("--run", required=True)
    parser.add_argument("--kind", choices=("A0", "Aalpha", "TMC"))
    parser.add_argument("--h", type=float)
    parser.add_argument("--mode", choices=("uniform", "perturbation"))
    parser.add_argument("--preload-run")
    args = parser.parse_args()
    scripts = Path(__file__).resolve().parent
    protocol = scripts.parent / "configs/contact_c1_v1.json"
    spec = json.loads(protocol.read_text(encoding="utf-8"))
    run = Path(args.run).resolve()
    run.parent.mkdir(parents=True, exist_ok=True)
    log = run.parent / (run.name + "." + args.action + ".log")
    receipt = log.with_suffix(".receipt.json")
    if log.exists() or receipt.exists():
        parser.error("refusing to overwrite existing evidence")
    if args.action == "solve":
        if args.kind is None or args.h is None or args.mode is None:
            parser.error("solve requires kind, h, mode")
        command = [sys.executable, str(scripts / "run_contact_c1_r2.py"), "--output", str(run),
                   "--kind", args.kind, "--h", str(args.h), "--mode", args.mode]
        if args.preload_run:
            command += ["--preload-run", str(Path(args.preload_run).resolve())]
        seconds = spec["budget"]["subprocess_wall_seconds"]
    else:
        command = [sys.executable, str(scripts / "audit_contact_c1.py"), "--run", str(run),
                   "--output", str(run / "audit.json")]
        seconds = spec["budget"]["maximum_audit_seconds_per_path"]
    environment = dict(os.environ)
    environment.update(OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    started, start_utc, timed_out = time.perf_counter(), timestamp(), False
    with log.open("x", encoding="utf-8") as stream:
        try:
            done = subprocess.run(command, cwd=run.parent, env=environment, stdout=stream,
                                  stderr=subprocess.STDOUT, timeout=seconds)
            code = done.returncode
        except subprocess.TimeoutExpired:
            code, timed_out = None, True
    write_json(receipt, dict(started_utc=start_utc, finished_utc=timestamp(),
               elapsed_seconds=time.perf_counter()-started, timeout_seconds=seconds, timed_out=timed_out,
               returncode=code, command=command, protocol_sha256=sha(protocol), log_sha256=sha(log),
               thread_limits={key: environment[key] for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")}))
    print(json.dumps(dict(run=run.name, action=args.action, returncode=code, timed_out=timed_out,
                         elapsed_seconds=time.perf_counter()-started)), flush=True)
    raise SystemExit(124 if timed_out else code)
