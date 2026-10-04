"""Bounded C1 read-back, retaining original and amended precision audit files."""
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
    parser.add_argument("--run", required=True)
    parser.add_argument("--output-name", default="audit.json")
    parser.add_argument("--precision-amendment")
    args = parser.parse_args()
    scripts = Path(__file__).resolve().parent
    protocol = scripts.parent / "configs/contact_c1_v1.json"
    spec = json.loads(protocol.read_text(encoding="utf-8"))
    run = Path(args.run).resolve()
    if (Path(args.output_name).name != args.output_name or not args.output_name.endswith(".json")
            or "/" in args.output_name or "\\" in args.output_name):
        parser.error("output-name must be a JSON basename")
    output = run / args.output_name
    log = run.parent / (run.name + "." + output.stem + ".log")
    receipt = log.with_suffix(".receipt.json")
    if output.exists() or log.exists() or receipt.exists():
        parser.error("refusing to overwrite audit evidence")
    command = [sys.executable, str(scripts / "audit_contact_c1.py"), "--run", str(run), "--output", str(output)]
    amendment = None
    if args.precision_amendment:
        amendment = Path(args.precision_amendment).resolve()
        command += ["--precision-amendment", str(amendment)]
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
               precision_amendment_sha256=sha(amendment) if amendment else None,
               audit_sha256=sha(output) if output.exists() else None))
    print(json.dumps(dict(run=run.name, output=output.name, returncode=code, timed_out=timed_out,
                         elapsed_seconds=time.perf_counter()-started)), flush=True)
    raise SystemExit(124 if timed_out else code)
