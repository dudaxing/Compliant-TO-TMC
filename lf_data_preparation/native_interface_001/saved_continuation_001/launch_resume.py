"""Launch each declared phase once, retaining terminal and sampled resources."""
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter, sleep
import argparse
import hashlib
import json
import os
import subprocess
import sys
import psutil

ROOT = Path(__file__).resolve().parents[3]
STAGE = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def write(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False)+"\n", encoding="utf-8")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("phase")
    parser.add_argument("--protocol", type=Path, default=STAGE/"protocol.json")
    args = parser.parse_args()
    protocol_file = args.protocol.resolve()
    protocol = json.loads(protocol_file.read_text(encoding="utf-8"))
    row = protocol["phases"][args.phase]
    receipt_file = STAGE/(args.phase+"_launch.json")
    assert not receipt_file.exists()
    pins = protocol["bindings"]
    assert all(sha(ROOT/name) == expected for name, expected in pins.items())
    receipt = dict(phase=args.phase, status="running", invocations=1, argv=[sys.executable,"-B"]+row["argv"],
        protocol_sha256=sha(protocol_file), bindings=pins, outer_seconds=row["outer_seconds"],
        sampled_RSS_limit_bytes=protocol["sampled_RSS_bytes"], started_utc=datetime.now(timezone.utc).isoformat(),
        budget_mode="Cooperative child limits and sampled tree RSS; no OS hard memory cap or force termination")
    write(receipt_file, receipt)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1", MPLBACKEND="Agg")
    started, peak, stop_reason = perf_counter(), 0, None
    with (STAGE/(args.phase+"_stdout.log")).open("xb") as output:
        child = subprocess.Popen(receipt["argv"], cwd=ROOT, env=env, stdout=output, stderr=subprocess.STDOUT)
        process = psutil.Process(child.pid)
        while child.poll() is None:
            try:
                members = [process]+process.children(recursive=True)
                peak = max(peak, sum(p.memory_info().rss for p in members if p.is_running()))
            except psutil.NoSuchProcess:
                pass
            if stop_reason is None and (perf_counter()-started > row["outer_seconds"] or peak > protocol["sampled_RSS_bytes"]):
                stop_reason = "external_elapsed_limit" if perf_counter()-started > row["outer_seconds"] else "sampled_RSS_limit"
                # Production observes this file before its next force call. No kill/force.
                (STAGE/"stop_requested.txt").write_text(stop_reason, encoding="utf-8")
            sleep(.1)
    unchanged = all(sha(ROOT/name) == expected for name, expected in pins.items())
    receipt.update(status="pass" if child.returncode == 0 and stop_reason is None and unchanged else "not_pass",
        exit_code=child.returncode, elapsed_seconds=perf_counter()-started, peak_sampled_tree_RSS_bytes=peak,
        stop_reason=stop_reason, all_bindings_unchanged=unchanged, completed_utc=datetime.now(timezone.utc).isoformat())
    write(receipt_file, receipt)
    print(json.dumps({key:receipt[key] for key in ("phase", "status", "exit_code", "elapsed_seconds",
        "peak_sampled_tree_RSS_bytes", "stop_reason", "all_bindings_unchanged")}), flush=True)
    if receipt["status"] != "pass":
        raise RuntimeError("Declared phase failed; no retry: "+args.phase)

if __name__ == "__main__":
    main()
