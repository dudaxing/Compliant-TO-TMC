"""F-PATH1: one approved native-path diagnostic; no arrays or scientific graph.

One driver, three supervised modes. Author review precedes its only 90 s run.
The old F-TRACE1 implementations and all native supervisor records stay intact.
"""
from __future__ import annotations
import time
_ENTRY_START = time.monotonic()

import argparse
import copy
from datetime import datetime, timezone
import hashlib
from html import escape
import importlib.metadata
import importlib.util
import json
import math
import ntpath
import os
from pathlib import Path
import re
import shutil
import stat
import sys
import traceback

PROTOCOL = "F-PATH1"
RUN_ID = "native_path_001"
SUBJECT = "native_profile_path"
MARKER = "F-PATH1.native_boundary"
SUCCESS = "native_path_interface_pass"
CARD = "docs/HF4_C2_S0_PREPARATION_RESULT_20260928.md"
DRIVER = "run_native_path_diagnostic.py"
SECONDS = 90.
LIMITS = dict(P0=15., P1=45., P3=15., shared=15.)
GUARD = 5.25
RSS_LIMIT = 8 * 1024**3
PRIOR_BINDING = "ea89c28be4d1acfff1a11fba8f1a51b139cf6625101f5df98e5951eec8d53cf7"
SUP1_SHA = "9f3da2f22bec869d069278058aa8502bd5f73c4b977b01ec5daa7b26ff1aec32"
SUP2_SHA = "b5f149e1cd3d6d9b4ad392123e410b786606f120f2e078139b7bacc97f2d9499"
PROOF_SHA = "2d378c64705461d58fa966528a347b6e411431402877663fd546f3fec8912f45"
CAPS = dict(max_files=64, max_file_bytes=64*1024**2,
            max_total_bytes=128*1024**2, max_json_body_bytes=256*1024**2)
HELPERS = ("windows_owned_process.py", "windows_owned_process_sup2.py",
           "cpu_supervision_evidence.py", "s0_event_log.py", "s0_preparation_evidence.py",
           "force_cost_evidence.py", "micro_trace_evidence.py")
HISTORY = ("receipt_binding.json", "execution_receipt.json", "output_sha256.json", "input_manifest.json",
           "results/trace/summary.json", "results/trace/environment.json", "results/trace/runtime_config.json",
           "events/P1_trace.ndjson", "logs/P1_trace.log", "results/P1_supervision/request.json",
           "results/P1_supervision/receipt.json", "results/P1_supervision/instances.ndjson",
           "supervision_proof.json", "native_manifest.json")
DOCS = ("docs/CURRENT_STATUS.md", CARD)
EXCLUSIONS = ("output_sha256.json", "receipt_binding.json", "execution_receipt.json",
              "ledger.json", "events/P3_seal.ndjson", "logs/P3_seal.log")
ENV_NAMES = ("XLA_FLAGS", "JAX_DEBUG_NANS", "JAX_DEBUG_INFS", "JAX_DISABLE_JIT",
             "JAX_ENABLE_PGLE", "JAX_PGLE_PROFILING_RUNS", "JAX_CPU_ENABLE_ASYNC_DISPATCH",
             "JAX_ENABLE_X64", "JAX_ENABLE_COMPILATION_CACHE", "JAX_PLATFORMS",
             "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
             "JAX_TRACEBACK_FILTERING", "PYTHONDONTWRITEBYTECODE")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def utc():
    return datetime.now(timezone.utc).isoformat()


def extended(value):
    value = os.path.abspath(os.fspath(value))
    if os.name == "nt" and not value.startswith("\\\\?\\"):
        value = "\\\\?\\UNC\\" + value[2:] if value.startswith("\\\\") else "\\\\?\\" + value
    return Path(value)


def check_time(deadline):
    require(deadline is None or finite(deadline) and time.monotonic() < deadline, "evidence deadline reached")


def no_reparse(filename):
    info = os.lstat(filename)
    require(not stat.S_ISLNK(info.st_mode) and not getattr(info, "st_file_attributes", 0) & 0x400,
            "reparse evidence path: " + str(filename))
    return info


def digest(filename, deadline=None):
    before = no_reparse(filename)
    require(stat.S_ISREG(before.st_mode), "expected regular file: " + str(filename))
    value = hashlib.sha256()
    with open(filename, "rb") as stream:
        while True:
            check_time(deadline)
            block = stream.read(1024**2)
            if not block:
                break
            value.update(block)
    after = no_reparse(filename)
    require(before.st_size == after.st_size and before.st_mtime_ns == after.st_mtime_ns,
            "file changed while hashing")
    return value.hexdigest()


def checked(filename, expected, size=None, deadline=None):
    require(size is None or no_reparse(filename).st_size == size, "size differs: " + str(filename))
    require(digest(filename, deadline) == expected, "SHA differs: " + str(filename))


def read(filename):
    return json.loads(Path(filename).read_text(encoding="utf-8"))


def write(filename, value, *, replace=False):
    filename = Path(filename)
    filename.parent.mkdir(parents=True, exist_ok=True)
    target = filename.with_name(filename.name + ".pending") if replace else filename
    with target.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, allow_nan=False, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    if replace:
        os.replace(target, filename)


def failure(error):
    return dict(type=type(error).__name__, module=type(error).__module__, message=str(error),
                traceback="".join(traceback.format_exception(error)))


def record(root, filename):
    filename = Path(filename)
    return dict(path=filename.relative_to(root).as_posix(), bytes=no_reparse(filename).st_size,
                sha256=digest(filename)) if filename.is_file() else None


def native_argument(plain_root, candidate=None):
    """Pure lexical gate; the actual filesystem is separately checked below."""
    def normalized(value):
        require(isinstance(value, str) and not value.startswith("\\\\")
                and re.match(r"^[A-Za-z]:[\\/]", value) is not None, "ordinary drive-absolute path required")
        require(".." not in value.replace("/", "\\").split("\\"), "parent traversal refused")
        return ntpath.normpath(value)
    root = normalized(plain_root)
    wanted = ntpath.join(root, "native")
    actual = normalized(candidate) if candidate is not None else wanted
    require(ntpath.normcase(actual) == ntpath.normcase(wanted), "native path outside fixed root/native")
    return wanted


def actual_native_path(root, plan, *, create=False):
    value = native_argument(plan["plain_root"])
    require(os.path.samefile(plan["plain_root"], root), "ordinary/extended root are not the same directory")
    cursor = Path(plan["plain_root"])
    for ancestor in reversed((cursor, *cursor.parents)):
        no_reparse(ancestor)
    folder = root / "native"
    if create:
        require(not folder.exists(), "native directory already exists")
        folder.mkdir()
    if folder.exists():
        require(stat.S_ISDIR(no_reparse(folder).st_mode) and os.path.samefile(value, folder),
                "native ordinary path does not identify the same directory")
    return value


def marker_analysis(document):
    """Read one target interval, without treating application markers as graphs."""
    require(isinstance(document, dict) and isinstance(document.get("traceEvents"), list), "unsupported trace schema")
    stacks, intervals, metadata = {}, [], []
    for index, item in enumerate(document["traceEvents"]):
        require(isinstance(item, dict), "trace event is not an object")
        phase, name = item.get("ph"), item.get("name")
        plane = (item.get("pid"), item.get("tid"))
        if phase == "M":
            metadata.append(item)
        if phase == "X" and name == MARKER:
            require(finite(item.get("ts")) and finite(item.get("dur")) and item["dur"] >= 0, "invalid marker X interval")
            require(all(isinstance(x, (int, str)) and not isinstance(x, bool) for x in plane), "marker plane unavailable")
            intervals.append(dict(start=item["ts"], end=item["ts"]+item["dur"], pid=plane[0], tid=plane[1],
                                  raw_indices=[index], raw_events=[item]))
        elif phase == "B":
            require(all(isinstance(x, (int, str)) and not isinstance(x, bool) for x in plane), "B plane unavailable")
            stacks.setdefault(plane, []).append((index, item))
        elif phase == "E":
            require(all(isinstance(x, (int, str)) and not isinstance(x, bool) for x in plane), "E plane unavailable")
            stack = stacks.get(plane, [])
            if stack:
                begin_index, begin = stack.pop()
                if begin.get("name") == MARKER:
                    require(item.get("name") in (None, MARKER), "named E does not close the target marker")
                    require(finite(begin.get("ts")) and finite(item.get("ts")) and item["ts"] >= begin["ts"],
                            "invalid paired marker interval")
                    intervals.append(dict(start=begin["ts"], end=item["ts"], pid=plane[0], tid=plane[1],
                                          raw_indices=[begin_index, index], raw_events=[begin, item]))
    require(not any(item.get("name") == MARKER for stack in stacks.values() for _, item in stack), "unclosed target marker")
    require(len(intervals) == 1, "expected exactly one complete target marker")
    require(finite(intervals[0]["end"]), "marker endpoint overflow")
    return dict(status="unique_application_marker_verified", marker=MARKER, count=1, interval=intervals[0],
                trace_event_count=len(document["traceEvents"]), trace_thread_metadata=metadata,
                time_unit="Chrome trace microseconds", runtime_native_trace_observed=False,
                scientific_admission=False)


def valid_summary(summary, expected):
    if not isinstance(summary, dict):
        return False
    if (summary.get("protocol") != PROTOCOL or summary.get("run_id") != RUN_ID
            or summary.get("subject") != SUBJECT or summary.get("identity") != expected
            or summary.get("scientific_admission") is not False or summary.get("force_executed") is not False):
        return False
    life = summary.get("profiler", {})
    if not isinstance(life, dict) or life.get("start_attempts") != 1:
        return False
    start, body, stop = life.get("start_returned"), life.get("body_returned"), life.get("stop_returned")
    if not all(isinstance(v, bool) for v in (start, body, stop)):
        return False
    if summary.get("status") == SUCCESS:
        return (all(life.get(k) is True for k in ("start_returned", "body_returned", "stop_returned"))
                and all(type(life.get(k)) is int and life[k] == 1 for k in ("start_attempts", "body_attempts", "stop_attempts"))
                and all(life.get(k) is None for k in ("start_error", "body_error", "stop_error", "pre_body_error"))
                and summary.get("first_error") is None and summary.get("controls_passed") == 12
                and summary.get("body", {}).get("result") == 32640
                and summary.get("marker_result", {}).get("status") == "unique_application_marker_verified"
                and summary.get("native_inventory", {}).get("status") == "complete")
    if not start:
        return (life.get("body_attempts") == life.get("stop_attempts") == 0 and not body and not stop
                and isinstance(life.get("start_error"), dict) and summary.get("first_error") == life["start_error"])
    if life.get("stop_attempts") != 1 or life.get("start_error") is not None:
        return False
    if life.get("body_attempts") == 0:
        return (not body and life.get("body_error") is None and isinstance(life.get("pre_body_error"), dict)
                and summary.get("first_error") == life["pre_body_error"]
                and stop == (life.get("stop_error") is None))
    if life.get("body_attempts") != 1:
        return False
    if body != (life.get("body_error") is None) or stop != (life.get("stop_error") is None):
        return False
    for name in ("body_error", "stop_error"):
        err = life.get(name)
        if err is not None and (not isinstance(err, dict) or not all(isinstance(err.get(k), str) for k in ("type", "module", "message", "traceback"))):
            return False
    if not body:
        return summary.get("first_error") == life["body_error"]
    if not stop:
        return summary.get("first_error") == life["stop_error"]
    return isinstance(summary.get("first_error"), dict)


def classify(raw, summary, expected, *, source_ok, proof_ok, resource_ok=True):
    """The same real classification function is used by controls and the parent."""
    answer = dict(status="execution_failure", passed=False, raw_reason=raw.get("reason"),
                  raw_returncode=raw.get("returncode"), first_error=summary.get("first_error") if isinstance(summary, dict) else None)
    if raw.get("cleanup_verified") is not True or raw.get("cleanup_proof", {}).get("pass") is not True or not proof_ok:
        answer["status"] = "cleanup_not_pass"
    elif (raw.get("reason") == "supervision_error" or raw.get("errors") or raw.get("supervision_error")
          or raw.get("telemetry_status") != "complete" or raw.get("telemetry_first_error") is not None):
        answer["status"] = "supervision_not_pass"
    elif not resource_ok or raw.get("reason") in ("global_deadline", "phase_timeout", "rss_limit"):
        answer["status"] = "resource_stop"
    elif not source_ok or raw.get("protocol") != "F-CPU-CLEAN1" or raw.get("cleanup_contract") != "CPU-CLEAN1":
        answer["status"] = "source_or_identity_not_pass"
    elif (raw.get("candidate_supervisor") != expected.get("candidate_supervisor")
          or raw.get("supervisor_sha256") != SUP2_SHA or not valid_summary(summary, expected)):
        pass
    elif raw.get("reason") == "normal_exit" and type(raw.get("returncode")) is int and raw["returncode"] == 0 and summary["status"] == SUCCESS:
        answer.update(status=SUCCESS, passed=True)
    elif (raw.get("reason") == "nonzero_exit" and isinstance(raw.get("returncode"), int)
          and not isinstance(raw["returncode"], bool) and raw["returncode"] != 0 and summary["status"] == "native_interface_not_pass"
          and summary.get("first_error_kind") == "native_interface"):
        answer["status"] = "native_interface_not_pass"
    return answer


def controls(plain_root, expected):
    records = []
    def result(name, function, expected_value=None, rejects=False):
        try:
            actual = function()
        except ValueError as error:
            require(rejects, "control unexpectedly rejected: " + name)
            records.append(dict(name=name, status="pass", rejected=True, error=str(error)))
            return
        require(not rejects and actual == expected_value, "control failed: " + name)
        records.append(dict(name=name, status="pass", result=actual))
    wanted = ntpath.join(ntpath.normpath(plain_root), "native")
    result("ordinary_path_admitted", lambda:native_argument(plain_root), wanted)
    result("outside_path_rejected", lambda:native_argument(plain_root, ntpath.join(ntpath.dirname(plain_root), "outside")), rejects=True)
    golden = dict(protocol=PROTOCOL, run_id=RUN_ID, subject=SUBJECT, identity=expected, status=SUCCESS,
        scientific_admission=False, force_executed=False, controls_passed=12, first_error=None, body=dict(result=32640),
        marker_result=dict(status="unique_application_marker_verified"), native_inventory=dict(status="complete"),
        profiler=dict(start_attempts=1, start_returned=True, body_attempts=1, body_returned=True,
                      stop_attempts=1, stop_returned=True, start_error=None, body_error=None, stop_error=None))
    raw = dict(reason="normal_exit", returncode=0, cleanup_verified=True, cleanup_proof={"pass":True}, errors=[],
               telemetry_status="complete", telemetry_first_error=None, protocol="F-CPU-CLEAN1", cleanup_contract="CPU-CLEAN1",
               candidate_supervisor=expected["candidate_supervisor"], supervisor_sha256=SUP2_SHA)
    err = dict(type="JaxRuntimeError", module="jax.errors", message="synthetic native stop failure", traceback="control-only")
    negative = copy.deepcopy(golden)
    negative.update(status="native_interface_not_pass", first_error=err, first_error_kind="native_interface")
    negative["profiler"].update(stop_returned=False, stop_error=err)
    nonzero = dict(raw, reason="nonzero_exit", returncode=1)
    variants = [("successful_phase", raw, golden, SUCCESS),
                ("nonzero_native_error", nonzero, negative, "native_interface_not_pass"),
                ("nonzero_missing_summary", nonzero, None, "execution_failure")]
    inconsistent = copy.deepcopy(negative)
    inconsistent["profiler"]["stop_attempts"] = 2
    variants.extend([("nonzero_inconsistent_lifecycle", nonzero, inconsistent, "execution_failure"),
                     ("resource_stop_preserved", dict(nonzero, reason="global_deadline"), negative, "resource_stop"),
                     ("supervision_error_preserved", dict(nonzero, reason="supervision_error", errors=["synthetic telemetry error"]), negative, "supervision_not_pass"),
                     ("cleanup_failure_preserved", dict(raw, cleanup_verified=False, cleanup_proof={"pass":False}), golden, "cleanup_not_pass")])
    for name, receipt, summary, wanted_status in variants:
        value = classify(receipt, summary, expected, source_ok=True, proof_ok=True)
        require(value["status"] == wanted_status and value["passed"] is (wanted_status == SUCCESS)
                and value["raw_reason"] == receipt["reason"] and value["raw_returncode"] == receipt["returncode"], "classification control failed: " + name)
        records.append(dict(name=name, status="pass", result=value))
    marker = dict(name=MARKER, ph="X", ts=3., dur=2., pid=1, tid=2)
    result("marker_unique", lambda:marker_analysis(dict(traceEvents=[marker]))["count"], 1)
    result("marker_absent", lambda:marker_analysis(dict(traceEvents=[])), rejects=True)
    result("marker_duplicate", lambda:marker_analysis(dict(traceEvents=[marker, dict(marker, ts=6.)])), rejects=True)
    require(len(records) == 12, "control count differs")
    return dict(protocol=PROTOCOL, run_id=RUN_ID, status="pass", groups=dict(path=2, classification=7, marker=3),
                controls=records, count=12, synthetic=True, native_sessions=0, scientific_admission=False)


def authority(old):
    checked(old / "receipt_binding.json", PRIOR_BINDING)
    binding = read(old / "receipt_binding.json")
    for name in ("input_manifest.json", "output_sha256.json"):
        rec = binding["records"][name]
        checked(old/name, rec["sha256"], rec["bytes"])
    return binding, read(old/"input_manifest.json"), read(old/"output_sha256.json")


def specs(repo, root):
    old = repo / "hf4_c2_stable_f_validation/micro_trace_001"
    binding, prior, payload = authority(old)
    rows = []
    def add(source, target, role, expected, size, live=None):
        rows.append(dict(path=target, source=str(source), live_source=str(live or source),
                         role=role, bytes=size, sha256=expected))
    for name in HISTORY:
        source = old/name
        if name == "receipt_binding.json":
            expected = PRIOR_BINDING
        elif name in binding["records"] and binding["records"][name] is not None:
            expected = binding["records"][name]["sha256"]
        else:
            expected = payload[name]
        add(source, "provenance/micro_trace_001/"+name, "selected_history", expected, source.stat().st_size)
    indexed = {row["path"]:row for row in prior["files"]}
    for name in HELPERS:
        rel = "aux/hf_repo/scripts/"+name
        rec = indexed[rel]
        add(old/rel, rel, "fixed_helper", rec["sha256"], rec["bytes"], repo/"hf_repo/scripts"/name)
    require(len(prior["runtime_files"]) == 20, "old runtime set differs")
    for rec in prior["runtime_files"]:
        add(old/rec["frozen_path"], rec["frozen_path"], "runtime", rec["sha256"], rec["bytes"], Path(rec["path"]))
    for name in ("hf_repo/scripts/"+DRIVER, *DOCS):
        source = repo/name
        add(source, "aux/"+name, "author_input", digest(source), source.stat().st_size)
    require(len(rows) == 44 and len({row["path"] for row in rows}) == 44, "44 input contract differs")
    require(sum(row["bytes"] for row in rows if row["role"] != "author_input") == 2185577, "41 old bytes differ")
    return rows, prior


def verify_inputs(root, *, include_live=True, installed=True, deadline=None):
    manifest = read(root/"input_manifest.json")
    require(manifest["protocol"] == PROTOCOL and manifest["run_id"] == RUN_ID and len(manifest["files"]) == 44, "input identity differs")
    for row in manifest["files"]:
        check_time(deadline)
        checked(root/row["path"], row["sha256"], row["bytes"], deadline)
        if include_live:
            checked(Path(row["live_source"]), row["sha256"], row["bytes"], deadline)
    if installed:
        require(sys.version == manifest["python"]["version"] and extended(sys.executable) == extended(manifest["python"]["executable"]), "HF Python differs")
        for name, version in manifest["packages"].items():
            require(importlib.metadata.version(name) == version, "package differs: " + name)
        for row in manifest["installed_binary_checks"]:
            checked(Path(row["path"]), row["sha256"], row["bytes"], deadline)
    return dict(status="verified", count=44, bytes=sum(row["bytes"] for row in manifest["files"]),
                installed_checked=installed, include_live=include_live, scientific_admission=False)


def prepare(root, repo, deadline, events):
    rows, prior = specs(repo, root)
    plan = read(root/"plan.json")
    for row in rows:
        check_time(deadline)
        if row["role"] == "author_input":
            relative = row["path"][4:]
            require(row["sha256"] == plan["author_sha256"][relative], "author input changed before freeze")
        checked(Path(row["source"]), row["sha256"], row["bytes"], deadline)
        checked(Path(row["live_source"]), row["sha256"], row["bytes"], deadline)
        target = root/row["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(row["source"], "rb") as src, target.open("xb") as dst:
            while True:
                check_time(deadline)
                chunk = src.read(1024**2)
                if not chunk:
                    break
                dst.write(chunk)
            dst.flush()
            os.fsync(dst.fileno())
        checked(target, row["sha256"], row["bytes"], deadline)
        events.emit("input_frozen", target=row["path"], bytes=row["bytes"], sha256=row["sha256"])
    manifest = dict(schema="hf-native-path-input-1", protocol=PROTOCOL, run_id=RUN_ID, subject=SUBJECT,
                    files=rows, python=prior["python"], packages=prior["packages"], runtime_files=prior["runtime_files"],
                    installed_binary_checks=prior["installed_binary_checks"], historical_canonical_files=prior["canonical_files"],
                    historical_canonical_interpretation="uncarried prior metadata; not a current scientific admission",
                    prior_binding_sha256=PRIOR_BINDING, helper_sha256={Path(x["path"]).name:x["sha256"] for x in rows if x["role"] == "fixed_helper"},
                    scientific_admission=False, created_utc=utc())
    write(root/"input_manifest.json", manifest)
    write(root/"inheritance_manifest.json", dict(protocol=PROTOCOL, run_id=RUN_ID, historical_files=14,
         historical_bytes=324018, fixed_helpers=7, runtime_files=20, installed_only_binary=prior["installed_binary_checks"],
         location_map=rows, derived_files=[], new_patch_applications=0, prior_binding_sha256=PRIOR_BINDING))
    write(root/"selected_source.json", dict(protocol=PROTOCOL, run_id=RUN_ID, subject=SUBJECT,
         source_manifest_sha256=digest(root/"input_manifest.json"), parent_supervisor=plan["parent_supervisor"],
         candidate_supervisor=plan["candidate_supervisor"], science_version=None, harness_version=None, force_executed=False))
    value = verify_inputs(root, deadline=deadline)
    write(root/"results/prepare/summary.json", dict(status="pass", verification=value))


def helper_identities(root):
    manifest = read(root/"input_manifest.json")
    result = {}
    for name in HELPERS:
        module = sys.modules.get(name[:-3])
        if module is None:
            result[name] = dict(actual_import=False)
            continue
        filename = root/"aux/hf_repo/scripts"/name
        require(extended(module.__file__) == filename, "helper module loaded outside frozen set: " + name)
        checked(module.__file__, manifest["helper_sha256"][name])
        result[name] = dict(actual_import=True, path=str(extended(module.__file__)), sha256=manifest["helper_sha256"][name])
    return result


def load_generic(root):
    manifest = read(root/"input_manifest.json")
    for name in HELPERS:
        checked(root/"aux/hf_repo/scripts"/name, manifest["helper_sha256"][name])
    sys.path.insert(0, str(root/"aux/hf_repo/scripts"))
    import micro_trace_evidence as generic
    require(extended(generic.__file__) == root/"aux/hf_repo/scripts/micro_trace_evidence.py", "generic helper loaded outside frozen set")
    checked(generic.__file__, manifest["helper_sha256"]["micro_trace_evidence.py"])
    require(generic.CAPS == CAPS, "generic caps differ")
    helper_identities(root)
    return generic


def collect_native(root, generic, deadline):
    result = dict(schema="hf-native-path-inventory-1", protocol=PROTOCOL, run_id=RUN_ID, status="partial",
                  caps=CAPS, files=[], issues=[], sessions=[], enumeration_complete=False,
                  all_enumerated_hashes_complete=False, parser_permitted=False, json_record=None, xplane_records=[])
    folder = root/"native"
    if not folder.exists():
        result["issues"].append("native_directory_absent")
        return result
    try:
        actual_native_path(root, read(root/"plan.json"))
        entries = list(generic.walk_no_reparse(folder, deadline=deadline, maximum=65))
        result["enumeration_complete"] = len(entries) <= 64
        result["enumerated_files"] = len(entries)
        result["enumerated_bytes"] = sum(info.st_size for _,info in entries)
        if not result["enumeration_complete"]:
            result["issues"].append("file_count_over_64_stopped_at_65")
        if result["enumerated_bytes"] > CAPS["max_total_bytes"]:
            result["issues"].append("native_total_over_cap")
        sessions = set()
        for filename, info in sorted(entries, key=lambda x:str(x[0])):
            item = dict(path=filename.relative_to(root).as_posix(), bytes=info.st_size, sha256=None, status="unhashed",
                        ordinary_path=str(Path(read(root/"plan.json")["plain_root"])/filename.relative_to(root)),
                        ordinary_path_characters=len(str(Path(read(root/"plan.json")["plain_root"])/filename.relative_to(root))))
            result["files"].append(item)
            if info.st_size > CAPS["max_file_bytes"]:
                result["issues"].append(dict(path=item["path"], reason="native_file_over_cap"))
            parts = filename.relative_to(folder).parts
            if len(parts) < 4 or parts[:2] != ("plugins", "profile"):
                result["issues"].append(dict(path=item["path"], reason="unexpected_native_layout"))
            else:
                sessions.add(parts[2])
            try:
                item.update(generic.streamed_record(root, filename, deadline=deadline, flush=True), status="hashed")
            except Exception as error:
                item["error"] = failure(error)
                result["issues"].append(item["error"])
                break
        result["sessions"] = sorted(sessions)
        result["all_enumerated_hashes_complete"] = len(result["files"]) == len(entries) and all(x["status"] == "hashed" for x in result["files"])
        result["unhashed_enumerated_paths"] = [str(p.relative_to(root).as_posix()) for p,_ in entries
             if not any(x["path"] == p.relative_to(root).as_posix() and x["status"] == "hashed" for x in result["files"])]
        jsons = [x for x in result["files"] if x["path"].endswith(".trace.json.gz")]
        xplanes = [x for x in result["files"] if x["path"].endswith(".xplane.pb")]
        if len(sessions) != 1:
            result["issues"].append("expected_one_session")
        if len(jsons) != 1:
            result["issues"].append("expected_one_trace_json_gz")
        if not xplanes:
            result["issues"].append("missing_xplane")
        result.update(json_record=jsons[0] if len(jsons) == 1 else None, xplane_records=xplanes)
        if not result["issues"] and result["all_enumerated_hashes_complete"]:
            result.update(status="complete", parser_permitted=True)
    except Exception as error:
        result["issues"].append(failure(error))
    return result


def runtime(root, deadline):
    verify_inputs(root, deadline=deadline)
    import jax
    import jaxlib
    import jax.profiler as public
    from jax._src import profiler as internal, lib
    actual = dict(jax_cpu_enable_async_dispatch=jax.config.read("jax_cpu_enable_async_dispatch"),
        jax_debug_nans=jax.config.jax_debug_nans, jax_debug_infs=jax.config.jax_debug_infs,
        jax_disable_jit=jax.config.jax_disable_jit, jax_enable_pgle=jax.config.jax_enable_pgle,
        jax_pgle_profiling_runs=jax.config.jax_pgle_profiling_runs, jax_enable_x64=jax.config.x64_enabled,
        jax_enable_compilation_cache=jax.config.jax_enable_compilation_cache,
        jax_traceback_filtering=jax.config.jax_traceback_filtering, backend=jax.default_backend())
    previous = read(root/"provenance/micro_trace_001/results/trace/runtime_config.json")
    expected = {k:v for k,v in previous["actual_config"].items() if k != "compiler_options"}
    write(root/"results/native/runtime_config.json", dict(protocol=PROTOCOL, run_id=RUN_ID, actual_config=actual,
          jax=jax.__version__, jaxlib=jaxlib.__version__, python=sys.version,
          historical_compiler_options=previous["actual_config"]["compiler_options"], compiler_options_executed=False,
          config_mutations=0, environment_mutations=0))
    require(actual == expected, "actual CPU/x64/async/debug/cache config differs")
    require(public.start_trace is internal.start_trace and public.stop_trace is internal.stop_trace
            and public.TraceAnnotation is internal.TraceAnnotation and internal._profile_state.profile_session is None,
            "profiler entry or preexisting session differs")
    modules = {"jax/profiler.py":public, "jax/_src/profiler.py":internal, "jax/_src/lib/__init__.py":lib,
               "jaxlib/_profiler.pyd":lib._profiler, "jaxlib/_profile_data.pyd":lib._profile_data}
    manifest = read(root/"input_manifest.json")
    identities = {}
    for relative, module in modules.items():
        row = next(x for x in manifest["runtime_files"] if x["frozen_path"] == "aux/runtime/"+relative)
        require(extended(module.__file__) == extended(row["path"]), "actual profiler import path differs")
        checked(module.__file__, row["sha256"], row["bytes"], deadline)
        identities[relative] = dict(module=module.__name__, path=str(extended(module.__file__)), bytes=row["bytes"], sha256=row["sha256"])
    write(root/"results/native/profiler_identity.json", dict(installed_modules=identities,
         installed_binary=manifest["installed_binary_checks"], binary_interpretation="installed pin, not loaded DLL enumeration",
         requested_options=None, effective_defaults="native_not_exposed", preexisting_session=False))
    verify_inputs(root, deadline=deadline)
    return public


class NativeAcceptance(ValueError):
    """Explicit saved-export gate; logging/source exceptions are not this class."""


def accept_native(function):
    try:
        return function()
    except Exception as error:
        raise NativeAcceptance(str(error)) from error


def probe(root, repo, deadline, events):
    request = read(root/"results/P1_supervision/request.json")
    plan = read(root/"plan.json")
    summary = dict(schema="hf-native-path-probe-1", protocol=PROTOCOL, run_id=RUN_ID, subject=SUBJECT,
        identity=request["identity"], status="running", scientific_admission=False, force_executed=False,
        runtime_native_trace_observed=False, first_error=None, first_error_kind=None, shutdown_error=None,
        stages=[], controls_passed=0, profiler=dict(start_attempts=0, start_returned=False, body_attempts=0,
        body_returned=False, stop_attempts=0, stop_returned=False, start_error=None, body_error=None, stop_error=None,
        pre_body_error=None))
    filename = root/"results/native/summary.json"
    def checkpoint():
        write(filename, summary, replace=filename.exists())
    def step(name, function):
        begin = time.monotonic()
        events.emit("stage_started", stage=name)
        try:
            value = function()
        except BaseException as error:
            detail = failure(error)
            summary["stages"].append(dict(name=name, status="failed", start=begin, end=time.monotonic(), error=detail))
            if summary["first_error"] is None:
                summary.update(first_error=detail, first_error_kind="native_interface" if isinstance(error, NativeAcceptance) else "execution")
            try:
                events.emit("stage_failed", stage=name, error=detail)
                checkpoint()
            except BaseException as record_error:
                summary.setdefault("secondary_record_errors", []).append(failure(record_error))
            raise
        summary["stages"].append(dict(name=name, status="pass", start=begin, end=time.monotonic()))
        events.emit("stage_finished", stage=name)
        checkpoint()
        return value
    checkpoint()
    life = summary["profiler"]
    public = None
    try:
        step("source_verification", lambda:verify_inputs(root, deadline=deadline))
        control = step("controls", lambda:controls(plan["plain_root"], request["identity"]))
        write(root/"results/native/controls.json", control)
        summary["controls_passed"] = control["count"]
        variables = {n:dict(present=n in os.environ, value=os.environ.get(n)) for n in ENV_NAMES}
        write(root/"results/native/environment.json", dict(protocol=PROTOCOL, run_id=RUN_ID, variables=variables,
             captured_utc=utc(), interpretation="raw strings, not effective config"))
        previous = read(root/"provenance/micro_trace_001/results/trace/environment.json")
        require(variables == previous["variables"], "raw environment differs from original capture")
        public = step("runtime_identity", lambda:runtime(root, deadline))
        argument = step("native_path", lambda:actual_native_path(root, plan, create=True))
        summary["native_path"] = dict(argument=argument, characters=len(argument), evidence_path="native", samefile_verified=True)
        checkpoint()
        try:
            events.emit("stage_started", stage="profiler.start")
            checkpoint()
            require(deadline - time.monotonic() >= 20., "less than 20 seconds before unique start")
            begin = time.monotonic()
            life.update(start_attempts=1, start_requested_monotonic=begin)
            try:
                public.start_trace(argument, create_perfetto_link=False, create_perfetto_trace=False, profiler_options=None)
            except BaseException as error:
                ended = time.monotonic()
                life["start_error"] = failure(error)
                summary.update(first_error=life["start_error"], first_error_kind="native_interface")
                summary["stages"].append(dict(name="profiler.start", status="failed", start=begin, end=ended, error=life["start_error"]))
                raise
            life.update(start_returned=True, start_returned_monotonic=time.monotonic())
            summary["stages"].append(dict(name="profiler.start", status="pass", start=begin, end=life["start_returned_monotonic"]))
            # All post-return logging is under the successful-start finally.
            events.emit("stage_finished", stage="profiler.start")
            checkpoint()
            life["body_attempts"] = 1
            checkpoint()
            def body():
                with public.TraceAnnotation(MARKER):
                    begin = time.monotonic()
                    value = sum(range(256))
                    end = time.monotonic()
                summary["body"] = dict(result=value, start=begin, end=end, elapsed_seconds=end-begin,
                     operation="sum(range(256))", arrays_created=0, scientific_calls=0)
                require(value == 32640, "standard-library body result differs")
            step("marker.body", body)
            life["body_returned"] = True
        except BaseException as error:
            if life["start_returned"]:
                key = "body_error" if life["body_attempts"] else "pre_body_error"
                # A failed step already saved the original traceback before the
                # outer wrapper adds frames; reuse that same first-error object.
                life[key] = summary["first_error"] if summary["first_error"] is not None else failure(error)
                if summary["first_error"] is None:
                    summary.update(first_error=life[key], first_error_kind="execution")
            elif summary["first_error"] is None:
                summary.update(first_error=failure(error), first_error_kind="execution")
        finally:
            if life["start_returned"]:
                # No fallible event/checkpoint separates this attempt from its API.
                begin = time.monotonic()
                life.update(stop_attempts=1, stop_requested_monotonic=begin)
                try:
                    public.stop_trace()
                except BaseException as error:
                    ended = time.monotonic()
                    life["stop_error"] = failure(error)
                    summary["shutdown_error"] = life["stop_error"]
                    if summary["first_error"] is None:
                        summary.update(first_error=life["stop_error"], first_error_kind="native_interface")
                    summary["stages"].append(dict(name="profiler.stop", status="failed", start=begin, end=ended, error=life["stop_error"]))
                else:
                    life.update(stop_returned=True, stop_returned_monotonic=time.monotonic())
                    summary["stages"].append(dict(name="profiler.stop", status="pass", start=begin, end=life["stop_returned_monotonic"]))
                try:
                    events.emit("stage_finished" if life["stop_returned"] else "stage_failed", stage="profiler.stop", api_attempts=1)
                    checkpoint()
                except BaseException as error:
                    summary["shutdown_record_error"] = failure(error)
                    if summary["first_error"] is None:
                        summary.update(first_error=summary["shutdown_record_error"], first_error_kind="execution")
        if summary["first_error"] is not None:
            raise RuntimeError("saved native/body error; no retry")
        generic = load_generic(root)
        inventory = step("native.inventory", lambda:collect_native(root, generic, deadline))
        summary["native_inventory"] = inventory
        write(root/"results/native/inventory.json", inventory)
        if not inventory["parser_permitted"]:
            raise NativeAcceptance("native export acceptance did not pass")
        document, body_bytes = step("native.json", lambda:accept_native(lambda:generic.parse_native_json(root/inventory["json_record"]["path"], deadline=deadline)))
        marker = step("native.marker", lambda:accept_native(lambda:marker_analysis(document)))
        marker["decoded_bytes"] = body_bytes
        summary["marker_result"] = marker
        write(root/"results/native/marker.json", marker)
        step("final_source_verification", lambda:verify_inputs(root, deadline=deadline))
        summary["loaded_helpers"] = helper_identities(root)
        summary["status"] = SUCCESS
    except BaseException as error:
        if summary["first_error"] is None:
            summary.update(first_error=failure(error), first_error_kind="native_interface" if isinstance(error, NativeAcceptance) else "execution")
        summary["status"] = "native_interface_not_pass" if summary["first_error_kind"] == "native_interface" else "execution_failure"
    finally:
        summary["finished_utc"] = utc()
        checkpoint()
    return 0 if summary["status"] == SUCCESS else 1


def proof_report(root):
    manifest = read(root/"input_manifest.json")
    for name in ("cpu_supervision_evidence.py", "s0_event_log.py"):
        checked(root/"aux/hf_repo/scripts"/name, manifest["helper_sha256"][name])
    sys.path.insert(0, str(root/"aux/hf_repo/scripts"))
    import cpu_supervision_evidence as proof
    checked(proof.__file__, PROOF_SHA)
    require(extended(proof.__file__) == root/"aux/hf_repo/scripts/cpu_supervision_evidence.py", "proof helper not frozen")
    request = read(root/"results/P1_supervision/request.json")
    raw = read(root/"results/P1_supervision/receipt.json")
    result = proof.proof_evidence(root, root/"results/P1_supervision", "receipt.json", raw, request["identity"])
    result["loaded_helpers"] = helper_identities(root)
    return result


def stdlib_walk(folder, deadline):
    """P0-partial safe preservation: no absent-manifest helper import required."""
    no_reparse(folder)
    stack = [Path(folder)]
    while stack:
        check_time(deadline)
        directory = stack.pop()
        with os.scandir(directory) as entries:
            for entry in entries:
                check_time(deadline)
                filename = Path(entry.path)
                info = no_reparse(filename)
                if stat.S_ISDIR(info.st_mode):
                    stack.append(filename)
                elif stat.S_ISREG(info.st_mode):
                    yield filename, info
                else:
                    raise ValueError("nonregular evidence entry: " + str(filename))


def svg(title, lines):
    height = 80 + 25*len(lines)
    return '<svg xmlns="http://www.w3.org/2000/svg" width="980" height="'+str(height)+'"><rect width="100%" height="100%" fill="#f8fafc"/><text x="20" y="30" font-family="sans-serif" font-size="18">'+escape(title)+'</text>'+''.join('<text x="20" y="'+str(60+25*i)+'" font-family="monospace" font-size="13">'+escape(line)+'</text>' for i,line in enumerate(lines))+'</svg>'


def write_text(filename, value):
    with Path(filename).open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(value)
        stream.flush()
        os.fsync(stream.fileno())


def seal(root, repo, deadline, events):
    issues = []
    try:
        source = verify_inputs(root, deadline=deadline)
    except Exception as error:
        source = dict(status="not_pass", error=failure(error))
        issues.append(source["error"])
    write(root/"source_preservation.json", source)
    try:
        summary = read(root/"results/native/summary.json") if (root/"results/native/summary.json").is_file() else None
    except Exception as error:
        summary = None
        issues.append(dict(scope="probe_summary", error=failure(error)))
    try:
        proof = proof_report(root)
    except Exception as error:
        proof = dict(status="not_pass_or_not_reached", error=failure(error))
        if (root/"results/P1_supervision/receipt.json").is_file():
            issues.append(proof["error"])
    write(root/"supervision_proof.json", proof)
    inventory, marker = dict(status="partial", files=[], issues=["not_reached"]), None
    if (root/"input_manifest.json").is_file():
        generic = load_generic(root)
        inventory = collect_native(root, generic, deadline)
        if inventory.get("parser_permitted"):
            try:
                document, decoded = generic.parse_native_json(root/inventory["json_record"]["path"], deadline=deadline)
                marker = marker_analysis(document)
                marker["decoded_bytes"] = decoded
            except Exception as error:
                marker = dict(status="not_pass", error=failure(error))
    write(root/"native_manifest.json", inventory)
    write(root/"marker_verification.json", marker)
    diagnostic = dict(status=summary.get("status") if summary else "not_reached", source=source["status"],
        cleanup=proof["status"], native=inventory["status"], marker=marker.get("status") if marker else "not_reached",
        scientific_admission=False, force_executed=False, runtime_native_trace_observed=False)
    if diagnostic["status"] == SUCCESS:
        require(source["status"] == "verified" and proof["status"] == "verified_all_instances"
                and inventory["status"] == "complete" and marker and marker["status"] == "unique_application_marker_verified",
                "successful diagnostic lacks independent saved evidence")
    write(root/"diagnostic_verification.json", diagnostic)
    if (root/"input_manifest.json").is_file():
        write(root/"loaded_helpers.json", dict(protocol=PROTOCOL, run_id=RUN_ID, phase="P3_seal",
             captured_utc=utc(), modules=helper_identities(root), interpretation="post-native-analysis P3 snapshot"))
    resources = read(root/"resources.json")
    stages = summary.get("stages", []) if summary else []
    write_text(root/"stages.svg", svg("F-PATH1 recorded stages; no scientific graph", [
        x["name"]+": "+x["status"]+" / "+format(x["end"]-x["start"], ".6f")+" s" for x in stages]))
    write_text(root/"resources.svg", svg("F-PATH1 preseal owned process RSS", [
        x["name"]+": "+format(x["peak_tree_rss_bytes"]/1024**2, ".3f")+" MiB / "+format(x["elapsed_seconds"], ".6f")+" s" for x in resources["phases"]]))
    write_text(root/"coverage.svg", svg("F-PATH1 interface coverage; scientific admission false", [str(k)+": "+str(v) for k,v in diagnostic.items()]))
    events.emit("preservation_complete", diagnostic_status=diagnostic["status"], issues=issues)
    write(root/"results/seal/summary.json", dict(status="pass" if not issues else "not_pass", diagnostic_status=diagnostic["status"],
          payload_sealed=not issues, issues=issues))
    payload = {}
    # All observed native files are preserved; byte caps gate parsing, never delete.
    for filename, info in stdlib_walk(root, deadline):
        rel = filename.relative_to(root).as_posix()
        if rel not in EXCLUSIONS:
            payload[rel] = digest(filename, deadline)
    write(root/"output_sha256.json", dict(sorted(payload.items())))
    return 0 if not issues else 1


def load_module(name, filename, expected):
    require(name not in sys.modules, "module already loaded: " + name)
    checked(filename, expected)
    spec = importlib.util.spec_from_file_location(name, filename)
    require(spec is not None and spec.loader is not None, "cannot load pinned module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    require(extended(module.__file__) == extended(filename), "loaded module file differs")
    checked(module.__file__, expected)
    return module


class Stop(RuntimeError):
    def __init__(self, status, detail):
        super().__init__(detail)
        self.status = status


def parent(repo_arg, root_arg):
    require(os.name == "nt", "this card is for the fixed Windows environment")
    plain_repo = ntpath.normpath(os.fspath(repo_arg))
    plain_root = ntpath.normpath(os.fspath(root_arg))
    native_argument(plain_root)
    repo, root = extended(plain_repo), extended(plain_root)
    require(root == repo/"hf4_c2_stable_f_validation"/RUN_ID and not root.exists(), "refuse alternate/existing campaign root")
    require(extended(__file__) == repo/"hf_repo/scripts"/DRIVER, "parent driver from another repository")
    old = repo/"hf4_c2_stable_f_validation/micro_trace_001"
    _, prior, _ = authority(old)
    hashes = {Path(x["path"]).name:x["sha256"] for x in prior["files"] if x["role"] != "selected_history" and x["path"].startswith("aux/hf_repo/scripts/")}
    for name in HELPERS:
        checked(repo/"hf_repo/scripts"/name, hashes[name])
    require(hashes[HELPERS[0]] == SUP1_SHA and hashes[HELPERS[1]] == SUP2_SHA and hashes[HELPERS[2]] == PROOF_SHA, "fixed supervisor pins differ")
    supervisor = load_module("_fpath_sup1", repo/"hf_repo/scripts/windows_owned_process.py", SUP1_SHA)
    start, deadline = _ENTRY_START, _ENTRY_START+SECONDS
    author = {n:digest(repo/n) for n in ("hf_repo/scripts/"+DRIVER, *DOCS)}
    root.mkdir(parents=True)
    for name in ("events", "logs", "results"):
        (root/name).mkdir()
    aux = root/"aux/hf_repo/scripts"
    parent_identity = dict(version="SUP1", path=str(aux/HELPERS[0]), sha256=SUP1_SHA)
    candidate_identity = dict(version="SUP2", path=str(aux/HELPERS[1]), sha256=SUP2_SHA)
    phases, attempted = [], set()
    ledger = dict(schema="hf-native-path-campaign-1", protocol=PROTOCOL, run_id=RUN_ID, subject=SUBJECT,
        status="running", error=None, first_stop=None, start_monotonic=start, deadline_monotonic=deadline,
        seconds=SECONDS, limits_seconds=LIMITS, rss_limit_bytes=RSS_LIMIT, phases=phases,
        scientific_admission=False, force_executed=False, runtime_native_trace_observed=False,
        parent_supervisor=parent_identity, candidate_supervisor=candidate_identity, source_manifest_sha256=None,
        P1_status="not_reached", supervision_proof_status="not_reached", trace_session=None)
    write(root/"plan.json", dict(ledger, plain_root=plain_root, repo=str(repo), prior_binding_sha256=PRIOR_BINDING,
        author_sha256=author, helper_sha256={n:hashes[n] for n in HELPERS}, non_seal_active_deadline=deadline-25.25,
        seal_active_deadline=deadline-10.25, final_binding_reserved_seconds=5., output_manifest_exclusions=EXCLUSIONS))
    plan_hash = digest(root/"plan.json")
    write(root/"ledger.json", ledger)
    env = os.environ.copy()
    env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONUNBUFFERED="1", PYTHONNOUSERSITE="1",
        JAX_ENABLE_X64="true", JAX_TRACEBACK_FILTERING="off", JAX_ENABLE_COMPILATION_CACHE="false", JAX_PLATFORMS="cpu",
        OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    candidate = None
    uncertain = False
    def shared():
        return time.monotonic()-start-sum(x["elapsed_seconds"] for x in phases)
    def save():
        ledger.update(elapsed_seconds=time.monotonic()-start, shared_elapsed_seconds=shared(), supervision_uncertain=uncertain)
        write(root/"ledger.json", ledger, replace=True)
    def execute(name, bucket, action, frozen):
        nonlocal uncertain
        require(name not in attempted, "phase retry refused")
        require(shared() <= 10., "preseal shared allowance exhausted")
        begin = time.monotonic()
        active = min(begin+LIMITS[bucket]-GUARD, deadline-(10.25 if bucket == "P3" else 25.25))
        require(active > begin, "no authorized phase interval")
        attempted.add(name)
        worker = aux/DRIVER if frozen else repo/"hf_repo/scripts"/DRIVER
        if bucket == "P3" and frozen:
            try:
                checked(worker, author["hf_repo/scripts/"+DRIVER])
            except (OSError, ValueError):
                # Partial P0 may have created but not completed this copied file.
                # Use the same pinned live driver once, never retry a P3 process.
                worker = repo/"hf_repo/scripts"/DRIVER
        checked(worker, author["hf_repo/scripts/"+DRIVER])
        runenv = env.copy()
        runenv.update(PYTHONPATH=str(aux) if frozen else str(repo/"hf_repo/scripts"), HF_FPATH1_ACTIVE_DEADLINE=repr(active),
            HF_S0_EVENT_FILE=str(root/"events"/(name+".ndjson")), HF_S0_PHASE=name, HF_S0_VERSION="F-PATH1",
            HF_S0_SOURCE_MANIFEST_SHA=ledger["source_manifest_sha256"] or plan_hash)
        command = [sys.executable, "-u", "-B", str(worker), "--action", action, "--repo", str(repo), "--root", str(root)]
        run_owned, options = supervisor.run_owned, {}
        if bucket == "P1":
            require(candidate is not None, "candidate not loaded")
            identity = dict(campaign_protocol=PROTOCOL, run_id=RUN_ID, subject=SUBJECT, phase=name,
                source_manifest_sha256=ledger["source_manifest_sha256"], source_version="F-PATH1", science_version=None,
                harness_id=None, candidate_supervisor=candidate_identity)
            write(root/"results/P1_supervision/request.json", dict(identity=identity, command=command, cwd=str(root),
                  deadline_monotonic=active, seconds=LIMITS[bucket]-GUARD, rss_limit_bytes=RSS_LIMIT))
            run_owned = candidate.run_owned
            options = dict(instance_log_path=root/"results/P1_supervision/instances.ndjson", instance_identity=identity,
                telemetry_path=root/"events/P1_native_cpu.ndjson", telemetry_identity=identity, telemetry_interval_seconds=1.)
        print(json.dumps(dict(phase=name, started_utc=utc(), active_seconds_limit=active-begin)), flush=True)
        try:
            raw = run_owned(command, cwd=str(root), env=runenv, log=root/"logs"/(name+".log"), deadline=active,
                seconds=LIMITS[bucket]-GUARD, rss_limit=RSS_LIMIT, **options)
        except BaseException:
            uncertain = True
            raise
        if not isinstance(raw, dict) or raw.get("cleanup_verified") is not True:
            uncertain = True
        if bucket == "P1":
            write(root/"results/P1_supervision/receipt.json", raw)
        row = dict(raw, name=name, bucket=bucket, worker_path=str(worker), owned_elapsed_seconds=raw["elapsed_seconds"],
             elapsed_seconds=time.monotonic()-begin, phase_start_monotonic=begin, phase_return_monotonic=time.monotonic(),
             active_deadline_monotonic=active, inclusive_phase_limit_seconds=LIMITS[bucket], campaign_protocol=PROTOCOL,
             active_limit_kind="phase_inclusive_limit" if begin+LIMITS[bucket]-GUARD <= deadline-(10.25 if bucket == "P3" else 25.25) else "campaign_seal_reserve")
        phases.append(row)
        save()
        print(json.dumps(dict(phase=name, reason=row["reason"], returncode=row["returncode"],
              elapsed_seconds=row["elapsed_seconds"], peak_rss_bytes=row["peak_tree_rss_bytes"], cleanup_verified=row["cleanup_verified"])), flush=True)
        if uncertain and bucket != "P1":
            raise Stop("cleanup_not_pass", "same-instance cleanup did not close")
        if row["elapsed_seconds"] > LIMITS[bucket] and bucket != "P1":
            raise Stop("resource_stop", "inclusive phase limit exceeded")
        if bucket != "P1":
            if row.get("supervisor_sha256") != SUP1_SHA:
                raise Stop("source_or_identity_not_pass", name+": supervisor source differs")
            if row["reason"] == "supervision_error" or row.get("supervision_error") or row.get("errors"):
                raise Stop("supervision_not_pass", name+": "+row["reason"])
            if row["reason"] in ("global_deadline", "phase_timeout", "rss_limit"):
                raise Stop("resource_stop", name+": "+row["reason"])
            if row["reason"] != "normal_exit" or row["returncode"] != 0:
                raise Stop("execution_failure", name+": "+row["reason"])
        return raw
    try:
        execute("P0_prepare", "P0", "prepare", False)
        verify_inputs(root, deadline=deadline-25.25)
        ledger["source_manifest_sha256"] = digest(root/"input_manifest.json")
        candidate = load_module("_fpath_sup2", aux/HELPERS[1], SUP2_SHA)
        write(root/"loaded_supervisors.json", dict(protocol=PROTOCOL, run_id=RUN_ID, parent_supervisor=parent_identity,
             candidate_supervisor=candidate_identity, loaded_parent_supervisor=dict(path=str(extended(supervisor.__file__)),sha256=SUP1_SHA),
             loaded_candidate_supervisor=dict(path=str(extended(candidate.__file__)),sha256=SUP2_SHA)))
        ledger["P1_status"] = "running"
        raw = execute("P1_native", "P1", "probe", True)
        # Materialize each failed gate; never jump around the real classifier.
        source_ok, proof_ok = False, False
        try:
            proof = proof_report(root)
            ledger["supervision_proof_status"] = proof["status"]
            proof_ok = proof["status"] == "verified_all_instances"
        except BaseException as error:
            ledger["supervision_proof_status"] = "not_pass"
            ledger["proof_error"] = failure(error)
            uncertain = True
        try:
            source = verify_inputs(root, deadline=deadline-25.25)
            source_ok = source["status"] == "verified"
        except BaseException as error:
            ledger["source_error"] = failure(error)
        filename = root/"results/native/summary.json"
        try:
            summary = read(filename) if filename.is_file() else None
        except BaseException as error:
            summary = None
            ledger["summary_error"] = failure(error)
        if isinstance(summary, dict):
            ledger.update(P1_status=summary.get("status"), trace_session=summary.get("profiler"), probe_first_error=summary.get("first_error"))
        expected = read(root/"results/P1_supervision/request.json")["identity"]
        outcome = classify(raw, summary, expected, source_ok=source_ok, proof_ok=proof_ok,
             resource_ok=phases[-1]["elapsed_seconds"] <= LIMITS["P1"])
        ledger["classification"] = outcome
        ledger["status"] = outcome["status"]
        if not outcome["passed"]:
            raise Stop(outcome["status"], "P1_native: "+str(outcome["first_error"] or outcome["raw_reason"]))
    except BaseException as error:
        ledger.update(status=error.status if isinstance(error, Stop) else "execution_failure", error=failure(error))
        ledger["first_stop"] = dict(status=ledger["status"], error=ledger["error"], monotonic=time.monotonic())
    finally:
        if ledger["P1_status"] == "running":
            ledger["P1_status"] = "not_complete"
        save()
        write(root/"resources.json", dict(protocol=PROTOCOL, run_id=RUN_ID, phases=phases,
            status=ledger["status"], scope="preseal", elapsed_seconds=time.monotonic()-start,
            peak_tree_rss_bytes=max((x["peak_tree_rss_bytes"] for x in phases), default=0), rss_limit_bytes=RSS_LIMIT))
        if not uncertain and shared() <= 10. and time.monotonic() < deadline-10.25:
            try:
                execute("P3_seal", "P3", "seal", (aux/DRIVER).is_file())
                require(read(root/"results/seal/summary.json")["status"] == "pass", "P3 preservation failed")
            except BaseException as error:
                ledger["seal_error"] = failure(error)
                if ledger["status"] == SUCCESS:
                    ledger.update(status="evidence_failure", error=ledger["seal_error"])
        else:
            ledger["seal_skipped"] = "cleanup uncertain or shared/seal reserve exhausted"
            if ledger["status"] == SUCCESS:
                ledger["status"] = "evidence_failure"
        if time.monotonic() >= deadline or shared() > LIMITS["shared"]:
            ledger["status"] = "resource_stop"
        save()
        write(root/"execution_receipt.json", read(root/"ledger.json"))
        targets = ("plan.json", "input_manifest.json", "inheritance_manifest.json", "selected_source.json", "loaded_supervisors.json",
            "execution_receipt.json", "output_sha256.json", "resources.json", "loaded_helpers.json", "results/prepare/summary.json", "results/native/summary.json",
            "results/native/controls.json", "results/native/environment.json", "results/native/runtime_config.json", "results/native/profiler_identity.json",
            "results/native/inventory.json", "results/native/marker.json", "results/P1_supervision/request.json", "results/P1_supervision/receipt.json",
            "results/P1_supervision/instances.ndjson", "events/P1_native_cpu.ndjson", "events/P1_native.ndjson", "source_preservation.json",
            "supervision_proof.json", "native_manifest.json", "marker_verification.json", "diagnostic_verification.json", "results/seal/summary.json",
            "stages.svg", "resources.svg", "coverage.svg", "events/P3_seal.ndjson", "logs/P3_seal.log")
        binding = dict(schema="hf-native-path-binding-1", protocol=PROTOCOL, run_id=RUN_ID, status=ledger["status"],
            scientific_admission=False, records={n:record(root,root/n) for n in targets},
            prior_binding_sha256=PRIOR_BINDING, output_manifest_exclusions=EXCLUSIONS,
            elapsed_before_binding_seconds=time.monotonic()-start, binding_completion_monotonic=time.monotonic())
        write(root/"receipt_binding.json", binding)
        if time.monotonic() >= deadline or shared() > LIMITS["shared"]:
            ledger["status"] = "resource_stop"
            save()
            write(root/"execution_receipt.json", read(root/"ledger.json"), replace=True)
            binding.update(status=ledger["status"], elapsed_before_binding_seconds=time.monotonic()-start)
            binding["records"]["execution_receipt.json"] = record(root,root/"execution_receipt.json")
            write(root/"receipt_binding.json", binding, replace=True)
        print(json.dumps(dict(protocol=PROTOCOL, run_id=RUN_ID, status=ledger["status"], error=ledger["error"],
              elapsed_seconds=time.monotonic()-start, root=str(root), scientific_admission=False)), flush=True)
    return 0 if ledger["status"] == SUCCESS else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--action", choices=("prepare", "probe", "seal"))
    args = parser.parse_args()
    if args.action is None:
        return parent(args.repo, args.root)
    repo, root = extended(args.repo), extended(args.root)
    require(root == repo/"hf4_c2_stable_f_validation"/RUN_ID, "child root differs")
    deadline = float(os.environ["HF_FPATH1_ACTIVE_DEADLINE"])
    plan = read(root/"plan.json")
    event_source = extended(__file__).parent/"s0_event_log.py"
    checked(event_source, plan["helper_sha256"]["s0_event_log.py"])
    from s0_event_log import EventLog
    event_module = sys.modules["s0_event_log"]
    require(extended(event_module.__file__) == event_source, "child EventLog module from wrong source")
    with EventLog() as events:
        events.emit("process_started", protocol=PROTOCOL, run_id=RUN_ID, mode=args.action)
        result = prepare(root, repo, deadline, events) if args.action == "prepare" else (
            probe(root, repo, deadline, events) if args.action == "probe" else seal(root, repo, deadline, events))
        events.emit("process_finished", protocol=PROTOCOL, run_id=RUN_ID, mode=args.action, returncode=result or 0)
    return result or 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
