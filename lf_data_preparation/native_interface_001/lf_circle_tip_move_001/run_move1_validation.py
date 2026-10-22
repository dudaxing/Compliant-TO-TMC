"""One authorized MOVE1 validation window; SUP2 owns every child process.

This script has no HF imports. It starts only the frozen pair of pytest files,
then one pure renderer after all 15 cases and exact call counts have passed.
It never installs production code and never retries a failed phase.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import traceback
import xml.etree.ElementTree as ET

from windows_owned_process_sup2 import run_owned


BASE = Path(__file__).resolve().parent
RUN = BASE / "run_001"
CANDIDATE = BASE / "candidate" / "hf_repo"
PYTHON = Path("D:/Coding/Diversity TO/Compliant-TO-TMC/.venv-handoff/Scripts/python.exe")
PROTOCOL = BASE / "frozen_protocol.json"
RSS_LIMIT = 8 * 1024**3
TEST_FILES = [
    CANDIDATE / "tests" / "test_split_displacement.py",
    CANDIDATE / "tests" / "test_native_guided_probe.py",
]


def write_new(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, allow_nan=False, indent=2)
        stream.write("\n")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def identity(path):
    value = Path(path)
    raw = value.read_bytes()
    return dict(path=str(value.resolve()), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def validate_protocol():
    protocol = read_json(PROTOCOL)
    if protocol.get("schema") != "hf-move1-execution-protocol-1":
        raise ValueError("wrong frozen execution protocol schema")
    if protocol.get("expected_test_cases") != 15:
        raise ValueError("the authorized test case count must remain 15")
    expected = protocol.get("expected_counts")
    if not isinstance(expected, dict) or not expected:
        raise ValueError("exact expected call counts were not frozen")
    if any(isinstance(v, bool) or not isinstance(v, int) or v < 0 for v in expected.values()):
        raise ValueError("call counts must be nonnegative integer values")
    bindings = protocol.get("bindings")
    if not isinstance(bindings, list) or not bindings:
        raise ValueError("source bindings were not frozen")
    checked = []
    for binding in bindings:
        actual = identity(binding["path"])
        if actual["sha256"] != binding["sha256"]:
            raise ValueError("frozen byte mismatch: " + actual["path"])
        checked.append(actual)
    required = {str(p.resolve()).casefold() for p in [
        Path(__file__), BASE / "render_move1.py", BASE / "windows_owned_process_sup2.py",
        CANDIDATE / "src" / "hf_eval" / "split_displacement.py",
        CANDIDATE / "src" / "hf_eval" / "native_probe.py", *TEST_FILES,
    ]}
    checked_paths = {row["path"].casefold() for row in checked}
    if not required <= checked_paths:
        raise ValueError("required executable source is absent from frozen bindings")
    return protocol, checked


def phase_pass(record):
    return (record.get("reason") == "normal_exit" and record.get("returncode") == 0
            and record.get("cleanup_verified") is True
            and record.get("cleanup_proof", {}).get("pass") is True
            and record.get("cleanup_proof", {}).get("job_handle_closed") is True)


def finite_environment():
    env = os.environ.copy()
    env.update(PYTHONPATH=str(CANDIDATE / "src"), PYTHONDONTWRITEBYTECODE="1",
               MOVE1_ARTIFACT_DIR=str(RUN / "artifacts"),
               JAX_ENABLE_X64="true", JAX_PLATFORMS="cpu", MPLBACKEND="Agg")
    for name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        env[name] = "16"
    return env


def junit_summary():
    tree = ET.parse(RUN / "tests.xml")
    cases = list(tree.getroot().iter("testcase"))
    failed = [c.attrib for c in cases if any(c.find(tag) is not None for tag in ("failure", "error", "skipped"))]
    suite_errors = list(tree.getroot().iter("error"))
    summary = dict(tests=len(cases), failed_or_skipped=failed,
                   errors=len(suite_errors), cases=[dict(c.attrib) for c in cases])
    if len(cases) != 15 or failed or suite_errors:
        raise ValueError("JUnit does not prove exactly 15 passed cases")
    class_names = {c.attrib.get("classname", "").split(".")[-1] for c in cases}
    if class_names != {"test_split_displacement", "test_native_guided_probe"}:
        raise ValueError("JUnit contains unexpected test modules")
    counts_by_module = {name: sum(c.attrib.get("classname", "").split(".")[-1] == name
                                  for c in cases) for name in class_names}
    if counts_by_module != {"test_split_displacement": 9, "test_native_guided_probe": 6}:
        raise ValueError("JUnit module counts differ from the frozen nine-plus-six cases")
    summary["counts_by_module"] = counts_by_module
    return summary


def checked_new_result_path(value):
    path = Path(value).resolve()
    path.relative_to(BASE)
    if "candidate" in [part.casefold() for part in path.parts]:
        raise ValueError("new result cannot be read from candidate source")
    return path


def helper():
    # Parent supplies a system-wide monotonic deadline. The same original clock
    # applies to tests, renderer, and all SUP2 cleanup; no window is reopened.
    deadline = float(os.environ["MOVE1_HELPER_DEADLINE"])
    result = dict(schema="hf-move1-helper-1", status="not_pass", phase="preflight",
                  start_utc=datetime.now(timezone.utc).isoformat(),
                  start_monotonic=time.monotonic(), deadline_monotonic=deadline,
                  scientific_launches=0, viewer_launches=0, production_installations=0)
    try:
        protocol, bindings = validate_protocol()
        result["checked_bindings"] = bindings
        env = finite_environment()
        if deadline - time.monotonic() <= 190:
            raise TimeoutError("insufficient original shared window for unique test launch")
        tests_command = [str(PYTHON), "-X", "utf8", "-B", "-m", "pytest", "-q", "-x",
                         "-p", "no:cacheprovider", "--basetemp", str(BASE / "t"),
                         "--junitxml", str(RUN / "tests.xml"), *map(str, TEST_FILES)]
        result["phase"] = "tests"
        result["scientific_launches"] = 1
        record = run_owned(tests_command, cwd=str(CANDIDATE), env=env,
                           log=RUN / "tests.log", deadline=deadline - 5., seconds=180.,
                           rss_limit=RSS_LIMIT, instance_log_path=RUN / "tests.instances.ndjson",
                           instance_identity=dict(stage="L-CTIPMOVE1", phase="tests"))
        result["tests_supervision"] = record
        write_new(RUN / "tests_supervision.json", record)
        if not phase_pass(record):
            raise RuntimeError("unique tests phase or same-instance cleanup did not pass")
        result["junit"] = junit_summary()
        index = read_json(RUN / "artifacts" / "index.json")
        counts_path = checked_new_result_path(index["counts_file"])
        counts = read_json(counts_path)
        if counts != protocol["expected_counts"]:
            raise ValueError("actual exact call counts differ from frozen counts")
        result["call_counts"] = counts
        result["artifact_index"] = index
        probe_path = checked_new_result_path(index["probe_result_file"])
        result["probe_result"] = identity(probe_path)
        if deadline - time.monotonic() <= 65:
            raise TimeoutError("insufficient original shared window for unique renderer and cleanup")
        result["phase"] = "viewer"
        result["viewer_launches"] = 1
        viewer_command = [str(PYTHON), "-X", "utf8", "-B", str(BASE / "render_move1.py")]
        record = run_owned(viewer_command, cwd=str(BASE), env=env,
                           log=RUN / "viewer.log", deadline=deadline - 5., seconds=60.,
                           rss_limit=RSS_LIMIT, instance_log_path=RUN / "viewer.instances.ndjson",
                           instance_identity=dict(stage="L-CTIPMOVE1", phase="pure_viewer"))
        result["viewer_supervision"] = record
        write_new(RUN / "viewer_supervision.json", record)
        if not phase_pass(record):
            raise RuntimeError("unique viewer phase or same-instance cleanup did not pass")
        result["render"] = read_json(RUN / "render.json")
        if result["render"].get("status") != "rendered_pending_visual_check":
            raise ValueError("renderer did not produce its declared single PNG")
        result["png"] = identity(RUN / "move1_actual.png")
        result["status"] = "ready_for_visual_check"
        result["phase"] = "complete_without_installation"
    except BaseException as error:
        result["error"] = dict(type=type(error).__name__, message=str(error), traceback=traceback.format_exc())
    finally:
        result["end_utc"] = datetime.now(timezone.utc).isoformat()
        result["end_monotonic"] = time.monotonic()
        result["elapsed_seconds"] = result["end_monotonic"] - result["start_monotonic"]
        write_new(RUN / "helper_result.json", result)
    return 0 if result["status"] == "ready_for_visual_check" else 1


def main():
    # A pre-existing directory is authoritative evidence of a prior attempt.
    # Refuse it; do not clean it, replace it, or select a fresh run number.
    RUN.mkdir(exist_ok=False)
    (RUN / "artifacts").mkdir(exist_ok=False)
    start = time.monotonic()
    summary = dict(schema="hf-move1-window-1", status="not_pass", start_monotonic=start,
                   start_utc=datetime.now(timezone.utc).isoformat(),
                   helper_window_seconds=300, tool_outer_seconds=360,
                   tests_seconds=180, viewer_seconds=60, rss_limit_bytes=RSS_LIMIT,
                   production_installations=0)
    try:
        protocol, checked = validate_protocol()
        write_new(RUN / "frozen_protocol_copy.json", protocol)
        write_new(RUN / "bindings_before_launch.json", checked)
        if (BASE / "t").exists():
            raise ValueError("pytest basetemp already exists; no old test directory may be deleted or reused")
        env = finite_environment()
        # SUP2 has one bounded five-second cleanup. Reserve that time inside
        # the shared 300 seconds, and another five seconds for helper cleanup.
        env["MOVE1_HELPER_DEADLINE"] = repr(start + 290.)
        command = [str(PYTHON), "-X", "utf8", "-B", str(Path(__file__).resolve()), "--helper"]
        outer = run_owned(command, cwd=str(BASE), env=env, log=RUN / "helper.log",
                          deadline=start + 295., seconds=295., rss_limit=RSS_LIMIT,
                          instance_log_path=RUN / "helper.instances.ndjson",
                          instance_identity=dict(stage="L-CTIPMOVE1", phase="shared_helper"))
        summary["helper_supervision"] = outer
        write_new(RUN / "helper_supervision.json", outer)
        if not phase_pass(outer):
            raise RuntimeError("shared helper phase or same-instance cleanup did not pass")
        inner = read_json(RUN / "helper_result.json")
        summary["helper_status"] = inner["status"]
        if inner["status"] != "ready_for_visual_check":
            raise RuntimeError("shared helper did not finish successfully")
        if time.monotonic() > start + 300.:
            raise TimeoutError("shared helper exceeded original 300-second window including cleanup")
        summary["status"] = "ready_for_visual_check"
        summary["next_action"] = "root may inspect the one new PNG once; no installation performed by this script"
    except BaseException as error:
        summary["error"] = dict(type=type(error).__name__, message=str(error), traceback=traceback.format_exc())
    finally:
        summary["end_utc"] = datetime.now(timezone.utc).isoformat()
        summary["elapsed_seconds"] = time.monotonic() - start
        write_new(RUN / "window_result.json", summary)
        print(json.dumps(dict(status=summary["status"], result=str(RUN / "window_result.json")), ensure_ascii=False))
    return 0 if summary["status"] == "ready_for_visual_check" else 1


if __name__ == "__main__":
    if sys.argv[1:] == ["--helper"]:
        raise SystemExit(helper())
    if sys.argv[1:]:
        raise SystemExit("no alternate execution arguments are authorized")
    raise SystemExit(main())
