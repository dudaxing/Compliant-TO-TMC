"""Bounded external MATLAB reference process with sampled tree RSS telemetry."""
import argparse
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import psutil


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", default="small_001")
    parser.add_argument("--driver", default="generate_small_reference")
    parser.add_argument("--seconds", type=float, default=300)
    args = parser.parse_args()
    base = Path(__file__).resolve().parent
    out = base / args.run_id
    out.mkdir(exist_ok=False)
    matlab = Path("D:/Program Files/MATLAB/R2023b/bin/matlab.exe")
    command = "addpath('{}');{}('{}');".format(str(base).replace("'", "''").replace("\\", "/"), args.driver,
                                                    str(out).replace("'", "''").replace("\\", "/"))
    start = time.monotonic()
    record = {"run_id": args.run_id, "started_utc": datetime.now(timezone.utc).isoformat(),
              "command": [str(matlab), "-wait", "-batch", command], "seconds_limit": args.seconds,
              "rss_soft_limit_bytes": 4 * 1024**3, "rss_samples": [],
              "driver_sha256": hashlib.sha256((base / (args.driver + ".m")).read_bytes()).hexdigest()}
    reason = "completed"
    with (out / "console.log").open("wb") as log:
        process = subprocess.Popen(record["command"], stdout=log, stderr=subprocess.STDOUT,
                                   creationflags=subprocess.CREATE_NO_WINDOW, cwd=out)
        root = psutil.Process(process.pid)
        while process.poll() is None:
            elapsed = time.monotonic() - start
            tree = [root]
            try:
                tree += root.children(recursive=True)
            except psutil.Error:
                pass
            rss, pids = 0, []
            for p in tree:
                try:
                    rss += p.memory_info().rss
                    pids.append(p.pid)
                except psutil.Error:
                    pass
            record["rss_samples"].append({"wall_seconds": elapsed, "rss_bytes": rss, "pids": pids})
            if elapsed > args.seconds or rss > record["rss_soft_limit_bytes"]:
                reason = "wall_limit" if elapsed > args.seconds else "sampled_tree_rss_soft_limit"
                for p in reversed(tree):
                    try:
                        p.kill()
                    except psutil.Error:
                        pass
                break
            time.sleep(0.5)
        process.wait(timeout=15)
    record.update(ended_utc=datetime.now(timezone.utc).isoformat(), wall_seconds=time.monotonic()-start,
                  returncode=process.returncode, termination_reason=reason,
                  peak_sampled_tree_rss_bytes=max(s["rss_bytes"] for s in record["rss_samples"]))
    (out / "process_record.json").write_text(json.dumps(record, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in record.items() if k not in {"rss_samples", "command"}}, indent=2))
    print((out / "console.log").read_text(encoding="utf-8", errors="replace")[-8000:])
    raise SystemExit(0 if process.returncode == 0 and reason == "completed" else 1)


if __name__ == "__main__":
    main()
