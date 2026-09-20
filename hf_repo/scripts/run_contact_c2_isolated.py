"""External time and attempt bounds for the frozen C2 diagnostic matrix."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import time
from hf4_common import read_json, write_json, sha, timestamp


def validate_previous(previous, experiment_root, protocol_path):
    """A written pass is insufficient without successful bound subprocesses."""
    experiment_root, protocol_path = Path(experiment_root).resolve(), Path(protocol_path).resolve()
    workspace = Path(__file__).resolve().parents[2]
    protocol_digest = sha(protocol_path)
    for receipt in previous:
        name = receipt["run_name"]
        if Path(name).name != name or name in (".", ".."):
            raise ValueError("previous run name escapes experiment root")
        old_run = experiment_root/name
        for action in ("solve", "audit"):
            saved = receipt if action == "solve" else read_json(experiment_root/f"{name}.audit.receipt.json")
            if (saved.get("schema") != "contact_c2_external_receipt_v1"
                    or saved.get("action") != action or saved.get("case_id") != receipt["case_id"]
                    or saved.get("run_name") != name or saved.get("returncode") != 0
                    or saved.get("timed_out") is not False
                    or saved.get("protocol_sha256") != protocol_digest
                    or saved.get("log_sha256") != sha(experiment_root/f"{name}.{action}.log")):
                raise ValueError("previous subprocess did not complete with bound evidence: " + action)
        audit_path = old_run/"audit.json"
        if saved.get("audit_sha256") != sha(audit_path):
            raise ValueError("previous audit differs from its completed subprocess receipt")
        audit = read_json(audit_path)
        if (audit.get("status") != "pass" or audit.get("case_id") != receipt["case_id"]
                or audit.get("schema_version") != "contact-c2-independent-audit-1.0"):
            raise ValueError("previous path was not independently admitted")
        for field in ("input_and_helper_sha256", "detail_output_sha256"):
            bindings = audit.get(field)
            if not isinstance(bindings, dict) or not bindings:
                raise ValueError("previous audit lacks its bound evidence: " + field)
            for relative, digest in bindings.items():
                if not isinstance(relative, str) or "\\" in relative or ":" in relative or Path(relative).is_absolute():
                    raise ValueError("previous audit binding must be portable and relative")
                path = (old_run/relative).resolve()
                limit = old_run if field == "detail_output_sha256" else workspace
                if not path.is_relative_to(limit) or sha(path) != digest:
                    raise ValueError("previous audit bound file changed or escaped its tree: " + relative)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--action", required=True, choices=("solve", "audit"))
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--case", required=True)
    parser.add_argument("--protocol", required=True, type=Path)
    args = parser.parse_args()
    run, protocol_path = args.run.resolve(), args.protocol.resolve()
    protocol = read_json(protocol_path)
    if protocol.get("schema") != "contact_c2_uniform_diagnostic_v1" or args.case not in protocol["cases"]:
        parser.error("undeclared frozen diagnostic case")
    scripts = Path(__file__).resolve().parent
    for name, digest in protocol["implementation_sha256"].items():
        path = (scripts.parent / name).resolve()
        if not path.is_relative_to(scripts.parent) or sha(path) != digest:
            parser.error("frozen implementation changed: " + name)
    run.parent.mkdir(parents=True, exist_ok=True)
    log = run.parent / (run.name + "." + args.action + ".log")
    receipt = log.with_suffix(".receipt.json")
    if log.exists() or receipt.exists():
        parser.error("refusing to overwrite evidence")
    budget = protocol["budget"]
    previous = [read_json(p) for p in run.parent.glob("*.solve.receipt.json")]
    if args.action == "solve":
        if run.exists() or len(previous) >= budget["maximum_paths"]:
            parser.error("new path required within the frozen attempt cap")
        if any(p["case_id"] == args.case for p in previous):
            parser.error("automatic retries are outside the frozen protocol")
        if args.case != protocol["run_sequence"][len(previous)]:
            parser.error("case differs from the frozen serial execution order")
        if sum(p["elapsed_seconds"] for p in previous) >= budget["maximum_total_solve_seconds"]:
            parser.error("cumulative solve budget exhausted")
        try:
            validate_previous(previous, run.parent, protocol_path)
        except (ValueError, KeyError, OSError) as error:
            parser.error(str(error))
        seconds = min(budget["subprocess_wall_seconds"], budget["maximum_total_solve_seconds"]
                      - sum(p["elapsed_seconds"] for p in previous))
        command = [sys.executable, "-B", str(scripts/"run_contact_c2.py"), "--output", str(run),
                   "--case", args.case, "--protocol", str(protocol_path)]
    else:
        if not (run/"metadata.json").is_file() or read_json(run/"metadata.json")["case_id"] != args.case:
            parser.error("audit case differs from saved run")
        audited = [read_json(p) for p in run.parent.glob("*.audit.receipt.json")]
        remaining = budget["maximum_total_audit_seconds"] - sum(p["elapsed_seconds"] for p in audited)
        if remaining <= 0:
            parser.error("cumulative audit budget exhausted")
        seconds = min(budget["maximum_audit_seconds_per_path"], remaining)
        command = [sys.executable, "-B", str(scripts/"audit_contact_c2.py"), "--run", str(run),
                   "--output", str(run/"audit.json"), "--protocol", str(protocol_path)]
    environment = dict(os.environ)
    environment.update(JAX_ENABLE_X64="true", JAX_PLATFORMS="cpu", OMP_NUM_THREADS="1",
                       OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", PYTHONDONTWRITEBYTECODE="1")
    start, started, timed_out = time.perf_counter(), timestamp(), False
    with log.open("x", encoding="utf-8") as stream:
        try:
            done = subprocess.run(command, cwd=run.parent, env=environment, stdout=stream,
                                  stderr=subprocess.STDOUT, timeout=seconds)
            code = done.returncode
        except subprocess.TimeoutExpired:
            code, timed_out = None, True
    payload = dict(schema="contact_c2_external_receipt_v1", action=args.action, case_id=args.case,
        run_name=run.name, command=command, started_utc=started, finished_utc=timestamp(),
        elapsed_seconds=time.perf_counter()-start, timeout_seconds=seconds, returncode=code,
        timed_out=timed_out, protocol_sha256=sha(protocol_path), log_sha256=sha(log))
    if args.action == "audit" and (run/"audit.json").is_file():
        payload["audit_sha256"] = sha(run/"audit.json")
    write_json(receipt, payload)
    print({"case":args.case,"action":args.action,"returncode":code,"timed_out":timed_out}, flush=True)
    raise SystemExit(124 if timed_out else code)
