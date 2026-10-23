"""Unique LOW1 outer supervision, then one byte seal in the original window."""
import time

# The original resource window includes these remaining imports and preflight.
STARTED = time.monotonic()

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import zipfile

BASE = Path(__file__).resolve().parent
PROTOCOL = BASE / "protocol.json"


def write_new(name, value):
    with (BASE / name).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def main():
    if len(sys.argv) != 1:
        raise ValueError("outer has no alternate protocol, run directory or arguments")
    previous = ("root_outer_start.json", "root_outer_supervision.json", "root_outer.log",
                "root_outer.instances.ndjson", "execution_evidence.zip", "EVIDENCE_MANIFEST.json",
                "seal_receipt.json", "run_001")
    if any((BASE / name).exists() for name in previous):
        raise FileExistsError("original LOW1 attempt must be preserved; unique window cannot be reopened")
    write_new("root_outer_start.json", dict(stage="L-CTIPLOW1",
        start_monotonic=STARTED, start_utc=datetime.now(timezone.utc).isoformat(),
        helper_window_seconds=9000, outer_window_seconds=9060,
        external_retries=0, execution_attempt=1,
        observation="outer bootstrap entered; scientific launch is recorded only by subsequent phase receipts"))
    protocol = json.loads(PROTOCOL.read_bytes())
    if (protocol.get("schema_version") != "hf-ctiplow1-protocol-1"
            or protocol.get("status") != "frozen_ready_for_unique_authorized_launch"
            or Path(protocol["runtime_base"]).resolve() != BASE
            or protocol.get("helper_seconds") != 9000
            or protocol.get("outer_seconds") != 9060
            or protocol.get("helper_content_deadline_offset_seconds") != 8900
            or protocol.get("helper_process_deadline_offset_seconds") != 8910
            or protocol.get("outer_process_deadline_offset_seconds") != 9050
            or protocol.get("memory_limit_bytes") != 64 * 1024**3):
        raise ValueError("wrong frozen LOW1 protocol or original resource window")
    expected_threads = {key: "16" for key in (
        "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")}
    if {key: str(value) for key, value in protocol["cpu_thread_environment"].items()} != expected_threads:
        raise ValueError("four-library thread contract changed")
    bindings = {str(Path(row["path"]).resolve()).casefold(): row for row in protocol["bindings"]}
    for name in ("outer_low1.py", "launch_low1.py", "windows_owned_process_sup2.py"):
        path = BASE / name
        frozen = bindings[str(path.resolve()).casefold()]
        data = path.read_bytes()
        if len(data) != frozen["bytes"] or hashlib.sha256(data).hexdigest() != frozen["sha256"]:
            raise ValueError("frozen bootstrap source changed: " + name)
    # Import the byte-bound, unchanged supervisor only after the finite checks.
    from windows_owned_process_sup2 import run_owned

    environment = os.environ.copy()
    environment.update(expected_threads)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["LOW1_ROOT_START_MONOTONIC"] = repr(STARTED)
    record = run_owned(
        [protocol["python_executable"], "-X", "utf8", "-B", str(BASE / "launch_low1.py"),
         "--protocol", str(PROTOCOL)],
        cwd=str(BASE), env=environment, log=BASE / "root_outer.log",
        # SUP2 cleanup has its own five seconds, then five seconds remain for
        # ordinary receipts under the authorized 9060-second outer ceiling.
        deadline=STARTED + 9050., seconds=9050., rss_limit=protocol["memory_limit_bytes"],
        instance_log_path=BASE / "root_outer.instances.ndjson",
        instance_identity={"stage": "L-CTIPLOW1", "phase": "outer9060"})
    write_new("root_outer_supervision.json", record)
    proof = record.get("cleanup_proof", {})
    outer_pass = (record["reason"] == "normal_exit" and record["returncode"] == 0
                  and record["cleanup_verified"] is True and proof.get("pass") is True
                  and proof.get("job_handle_closed") is True)
    seal = dict(stage="L-CTIPLOW1", status="not_started", attempts=0,
        scope=("BASE exact files after outer cleanup, excluding archive/manifest/seal receipt themselves; "
               "no scientific NPZ decoding"),
        outer_pass=bool(outer_pass), shared_window_seconds=9000,
        scientific_retries=0, extra_F_T_HP_tests_or_render_calls=0)
    if not (record.get("cleanup_verified") is True and proof.get("pass") is True
            and proof.get("job_handle_closed") is True):
        seal["status"] = "skipped_same_instance_cleanup_not_proven"
    elif time.monotonic() >= STARTED + 8980.:
        seal["status"] = "skipped_shared_window_not_open_with_sealing_margin"
    else:
        seal["attempts"] = 1
        members = []
        excluded = {"execution_evidence.zip", "EVIDENCE_MANIFEST.json", "seal_receipt.json"}

        def check_seal_clock():
            if time.monotonic() >= STARTED + 8990.:
                raise TimeoutError("original shared sealing window expired")

        try:
            paths = sorted(path for path in BASE.rglob("*")
                           if path.is_file() and path.relative_to(BASE).as_posix() not in excluded)
            check_seal_clock()
            with zipfile.ZipFile(BASE / "execution_evidence.zip", "x", zipfile.ZIP_DEFLATED) as archive:
                for path in paths:
                    check_seal_clock()
                    data = path.read_bytes()
                    name = path.relative_to(BASE).as_posix()
                    archive.writestr(name, data)
                    members.append(dict(path=name, bytes=len(data), sha256=hashlib.sha256(data).hexdigest()))
            check_seal_clock()
            data = (BASE / "execution_evidence.zip").read_bytes()
            manifest = dict(stage="L-CTIPLOW1", archive=dict(path="execution_evidence.zip",
                bytes=len(data), sha256=hashlib.sha256(data).hexdigest()), members=members,
                scope=seal["scope"], scientific_payloads_read_as_bytes_only=True)
            check_seal_clock()
            write_new("EVIDENCE_MANIFEST.json", manifest)
            seal["status"] = "pass" if time.monotonic() < STARTED + 9000. else "failed_shared_sealing_deadline"
            seal["members"] = len(members)
            seal["archive"] = manifest["archive"]
            seal["evidence_completeness"] = "normal_exit" if outer_pass else "actual_partial_after_terminal_error"
        except Exception as error:
            seal["status"] = "failed_once_no_retry"
            seal["error"] = dict(type=type(error).__name__, message=str(error))
            seal["members_written_before_error"] = len(members)
    seal["elapsed_seconds_from_outer_start"] = time.monotonic() - STARTED
    write_new("seal_receipt.json", seal)
    print(json.dumps(dict(outer_pass=bool(outer_pass), reason=record["reason"],
        returncode=record["returncode"], elapsed_seconds=record["elapsed_seconds"],
        seal_status=seal["status"])), flush=True)
    return 0 if outer_pass and seal["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
