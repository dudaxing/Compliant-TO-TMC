"""One authorized PROBE1 helper and its single scientific child.

Only --science-child imports HF. The helper reads ordinary JSON or file bytes,
uses the original SUP2, and never decodes an NPZ or installs production code.
Root's outer bootstrap alone owns the one final byte archive.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time
import traceback

from windows_owned_process_sup2 import run_owned


BASE = Path(__file__).resolve().parent
PROTOCOL = BASE / "protocol.json"
RUN = BASE / "run_001"
PARENT = BASE / "parent_001"
SCIENCE = RUN / "science"
VIEW = RUN / "view"


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_new(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, allow_nan=False, indent=2)
        stream.write("\n")


def identity(path):
    path = Path(path)
    raw = path.read_bytes()
    return dict(path=str(path.resolve()), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def phase_pass(row):
    return (row.get("reason") == "normal_exit" and row.get("returncode") == 0
            and row.get("cleanup_verified") is True
            and row.get("cleanup_proof", {}).get("pass") is True
            and row.get("cleanup_proof", {}).get("job_handle_closed") is True)


def check_clock(deadline, label):
    if time.monotonic() >= deadline:
        raise TimeoutError("original shared deadline exhausted: " + label)


def validate_protocol():
    value = read_json(PROTOCOL)
    if (value.get("schema_version") != "hf-ctipprobe1-protocol-1"
            or value.get("status") != "frozen_ready_for_unique_authorized_launch"):
        raise ValueError("wrong frozen PROBE1 protocol")
    expected_budget = dict(controller_seconds=3600, viewer_seconds=600, helper_seconds=4500,
                           outer_seconds=4560, science_process_cap_seconds=3800, viewer_reserve_seconds=665)
    for key, expected in expected_budget.items():
        if value.get(key) != expected:
            raise ValueError("authorized budget changed: " + key)
    if value.get("memory_limit_bytes") != 64*1024**3 or value.get("viewer_memory_limit_bytes") != 8*1024**3:
        raise ValueError("authorized memory limits changed")
    if (value.get("selected_state_index") != 12 or value.get("body_q_targets_mm") != [0., .025]
            or value.get("held_input_mean_mm") != 1.06):
        raise ValueError("authorized peak or probe control definition changed")
    if Path(value["runtime_base"]).resolve() != BASE or Path(value["run_directory"]).resolve() != RUN:
        raise ValueError("runtime directory differs from frozen location")
    expected_threads = {name: "16" for name in (
        "OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS")}
    if {key: str(item) for key, item in value["cpu_thread_environment"].items()} != expected_threads:
        raise ValueError("four-library thread contract changed")
    bindings = value.get("bindings")
    if not isinstance(bindings, list) or not bindings:
        raise ValueError("candidate byte bindings missing")
    checked = []
    for binding in bindings:
        # The parent archives are copied and hashed by the helper, not by this
        # preflight in the launcher outside that helper-owned phase.
        if Path(binding["path"]).suffix.casefold() == ".npz":
            raise ValueError("parent NPZ belongs in parent_files, not executable bindings")
        actual = identity(binding["path"])
        if actual["sha256"] != binding["sha256"] or actual["bytes"] != binding["bytes"]:
            raise ValueError("frozen source byte mismatch: " + actual["path"])
        checked.append(actual)
    required = [BASE/"run_probe1.py", BASE/"launch_probe1.py", BASE/"render_probe1.py",
                BASE/"windows_owned_process_sup2.py", Path(value["observer_file"]),
                Path(value["candidate_source"])/"hf_eval"/"native_probe.py",
                Path(value["candidate_source"])/"hf_eval"/"split_displacement.py"]
    if not {str(path.resolve()).casefold() for path in required} <= {row["path"].casefold() for row in checked}:
        raise ValueError("required executable or observer definition absent from frozen bindings")
    if Path(value["observer_file"]).resolve() != Path(value["observer_definition_path"]).resolve():
        raise ValueError("observer aliases differ")
    entries = value.get("parent_files", [])
    required_parent = {"result.json", "model/model.json", "model/model.npz",
        "model/source_geometry/geometry.json", "model/source_geometry/geometry.npz",
        "accepted/012/state.json", "accepted/012/state.npz"}
    if len(entries) != 7 or {entry["relative_path"] for entry in entries} != required_parent:
        raise ValueError("exactly the seven approved parent files are required")
    return value, checked


def finite_environment(protocol):
    env = os.environ.copy()
    env.update(PYTHONPATH=protocol["candidate_source"], PYTHONDONTWRITEBYTECODE="1",
               JAX_ENABLE_X64="true", JAX_PLATFORMS="cpu", MPLBACKEND="Agg")
    env.update({key: str(value) for key, value in protocol["cpu_thread_environment"].items()})
    return env


def copy_parent(protocol, deadline):
    receipt = dict(status="not_pass", copied=[], bytes_decoded_as_scientific_arrays=0)
    try:
        check_clock(deadline, "before parent copy")
        PARENT.mkdir(exist_ok=False)
        for entry in protocol["parent_files"]:
            check_clock(deadline, "parent byte copy")
            source = Path(entry["source"])
            target = (PARENT/entry["relative_path"]).resolve()
            target.relative_to(PARENT)
            raw = source.read_bytes()
            if len(raw) != entry["bytes"] or hashlib.sha256(raw).hexdigest() != entry["sha256"]:
                raise ValueError("parent source bytes differ: " + str(source))
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as stream:
                stream.write(raw)
            actual = identity(target)
            if actual["sha256"] != entry["sha256"] or actual["bytes"] != entry["bytes"]:
                raise ValueError("parent copied bytes differ: " + str(target))
            receipt["copied"].append(dict(source=str(source), relative_path=entry["relative_path"], **actual))
        check_clock(deadline, "after parent copy")
        receipt["status"] = "pass"
    except BaseException as error:
        receipt["error"] = dict(type=type(error).__name__, message=str(error), traceback=traceback.format_exc())
        raise
    finally:
        write_new(RUN/"parent_copy_receipt.json", receipt)


def scientific_child():
    started = time.monotonic()
    receipt = dict(schema="hf-ctipprobe1-scientific-child-1", status="not_pass",
        start_utc=datetime.now(timezone.utc).isoformat(), start_monotonic=started,
        api_call_attempts=0, api_returned=False, production_status=None,
        accepted_states=None, call_counts=None, scientific_array_decode_monitoring="not instrumented",
        old_array_decode_contract="unchanged API: geometry four masks and selected lift/fluctuation only; model archive bytes only",
        external_retries=0, new_HP_calls_by_wrapper=0, new_tests=0,
        production_installations=0)
    try:
        protocol, _ = validate_protocol()
        deadline = float(os.environ["PROBE1_HELPER_DEADLINE"])
        check_clock(deadline, "before scientific import")
        sys.path.insert(0, protocol["candidate_source"])
        import hf_eval
        import hf_eval.native_probe as probe_module
        if (Path(hf_eval.__file__).resolve() != Path(protocol["candidate_source"])/"hf_eval"/"__init__.py"
                or Path(probe_module.__file__).resolve() != Path(protocol["candidate_source"])/"hf_eval"/"native_probe.py"):
            raise ValueError("HF import resolved outside the frozen candidate")
        from hf_eval.native_probe import evaluate_native_guided_probe
        receipt["api_imported"] = True
        receipt["imported_module_paths"] = dict(package=hf_eval.__file__, native_probe=probe_module.__file__)
        with (RUN/"accepted_progress.jsonl").open("xb", buffering=0) as progress:
            accepted_count = 0

            def accepted(record):
                nonlocal accepted_count
                check_clock(deadline, "accepted-state callback")
                accepted_count += 1
                event = dict(accepted_index=accepted_count-1, utc=datetime.now(timezone.utc).isoformat(),
                    elapsed_seconds=time.monotonic()-started,
                    **{key: record[key] for key in ("body_q_mm", "input_mean_mm", "R_input_N",
                        "Q_drive_half_N", "relative_residual", "constraint_residual", "minimum_J",
                        "max_abs_Hu_per_mm", "newton_checks", "bisection_depth", "state_sha256",
                        "is_original_target", "original_target_index")})
                raw = (json.dumps(event, ensure_ascii=False, allow_nan=False, separators=(",", ":"))+"\n").encode("utf-8")
                if progress.write(raw) != len(raw):
                    raise OSError("short accepted progress write")
                os.fsync(progress.fileno())

            receipt["api_call_attempts"] = 1
            result = evaluate_native_guided_probe(PARENT/"result.json", 12, [0., .025], SCIENCE,
                time_limit_seconds=protocol["controller_seconds"], on_accept=accepted)
            receipt.update(status="returned", api_returned=True, production_status=result["status"],
                accepted_states=len(result["accepted_steps"]), callback_accepted_states=accepted_count,
                call_counts=result["call_counts"], failure=result["failure"],
                target_reached=result["target_reached"], result_file=str(SCIENCE/"result.json"),
                api_timing_seconds=result["timing_seconds"])
        receipt["result_identity"] = identity(SCIENCE/"result.json")
    except BaseException as error:
        receipt["error"] = dict(type=type(error).__name__, code=getattr(error, "code", None),
            message=str(error), traceback=traceback.format_exc())
    finally:
        receipt["elapsed_seconds"] = time.monotonic()-started
        receipt["end_utc"] = datetime.now(timezone.utc).isoformat()
        write_new(RUN/"science_child_receipt.json", receipt)
    # A returned typed numerical failure is a clean child exit, not a success
    # of the physical path. The helper separately gates result.status.
    return 0 if receipt["api_returned"] else 1


def finite_number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("invalid saved scalar: " + label)
    return value


def validate_numerical_result(protocol, deadline):
    check_clock(deadline, "result metadata checks")
    result = read_json(SCIENCE/"result.json")
    parent = read_json(PARENT/"result.json")
    peak = parent["states"][12]
    if (result["schema_version"] != "hf-native-guided-probe-1.0" or result["status"] != "success"
            or result["target_reached"] is not True or result["failure"] is not None):
        raise ValueError("the requested q path did not succeed")
    if result["probe_task"]["held_input_mean_mm"] != 1.06 or result["probe_task"]["body_q_targets_mm"] != [0., .025]:
        raise ValueError("probe task differs from the authorized hold/q definition")
    if (result["response_mode"] != "mechanical" or result["tangent_mode"] != "chunk256"
            or result["initial_guess"] != "port_projection"):
        raise ValueError("parent execution modes were changed")
    if result["settings"] != (parent["settings"] | {"time_limit_seconds": 3600}):
        raise ValueError("nonclock parent settings changed")
    model = result["model"]
    if (len(model["coordinates_mm"]) != 14985 or len(model["connectivity"]) != 14720
            or len(model["solid"]) != 14720 or len(model["body_nodes"]) != 565
            or len(model["fixed_dofs"]) != 1288 or len(model["zero_dofs"]) != 195):
        raise ValueError("admitted full model dimensions or body membership changed")
    selected = result["source"]["selected_state"]
    if (selected["accepted_index"] != 12 or selected["state_sha256"] != peak["state_sha256"]
            or selected["R_input_N"] != peak["R_input"]):
        raise ValueError("selected peak identity changed")
    rows = result["accepted_steps"]
    if not 2 <= len(rows) <= 5 or [row["body_q_mm"] for row in rows if row["is_original_target"]] != [0., .025]:
        raise ValueError("accepted q path differs or exceeds the original minimum-increment bound")
    anchor = rows[0]
    if (anchor["body_q_mm"] != 0 or anchor["fresh_anchor"] is not True or anchor["newton_checks"] != 1
            or anchor["state_sha256"] != peak["state_sha256"]
            or float(anchor["R_input_N"]).hex() != float(peak["R_input"]).hex()
            or anchor["state"]["fields"] != peak["state"]["fields"]):
        raise ValueError("q0 did not preserve original two split fields and signed R")
    identities = []
    previous = -1.
    for row in rows:
        check_clock(deadline, "accepted metadata/archive byte identity")
        q = finite_number(row["body_q_mm"], "q")
        mean = finite_number(row["input_mean_mm"], "input mean")
        bound = 1e-10*max(1.06, 1e-6)
        if (q <= previous or q < 0 or q > .025 or abs(mean-1.06) > bound
                or abs(finite_number(row["constraint_residual"], "constraint residual")) > row["constraint_bound"]
                or row["constraint_bound"] != bound
                or finite_number(row["relative_residual"], "relative residual") > 1e-9
                or finite_number(row["minimum_J"], "minimum J") <= 0
                or finite_number(row["relative_global_force_balance"], "global balance") > 1e-6
                or finite_number(row["max_abs_prescribed_error_mm"], "prescribed error") > 8e-11):
            raise ValueError("an original acceptance gate did not pass")
        previous = q
        if row["Q_drive_half_N"] != -row["force_on_body_N"]["total"][0]:
            raise ValueError("signed body drive/ON-body relation differs")
        for component in ("total", "material", "regularization"):
            for value in row["force_on_body_N"][component]:
                finite_number(value, "ON body " + component)
        for values in row["ledger"].values():
            for value in values:
                finite_number(value, "ledger")
        for kind in ("state", "fields"):
            declared = row[kind]
            file = (SCIENCE/declared["path"]).resolve()
            file.relative_to(SCIENCE)
            actual = identity(file)
            if actual["sha256"] != declared["sha256"]:
                raise ValueError("new accepted archive bytes differ from declaration")
            identities.append(actual | dict(kind=kind, body_q_mm=q, decoded_by_wrapper=False))
    counts = result["call_counts"]
    if any(type(value) is not int or value < 0 for value in counts.values()):
        raise ValueError("production call count invalid")
    if (counts["solver_invocations"] != 1 or counts["HP_calls"] != 0
            or counts["save_force_calls"] != 0 or counts["save_tangent_calls"] != 0
            or counts["force_calls"] < counts["force_calls_completed"]
            or counts["tangent_calls"] < counts["tangent_calls_completed"]):
        raise ValueError("actual production call contract differs")
    if any(result[key] is not False for key in ("independent_HP_qualified", "effective_grasp_qualified", "release_qualified", "HF_qualified")):
        raise ValueError("new qualifications were promoted")
    return dict(status="pass", accepted_states=len(rows), body_q_original_targets_mm=[0., .025],
        q0_identity_preserved=True, gates="original residual/mean/J/global-balance/prescribed gates",
        call_counts=counts, new_archive_byte_identities=identities,
        max_relative_residual=max(row["relative_residual"] for row in rows),
        min_J=min(row["minimum_J"] for row in rows),
        max_prescribed_error_mm=max(row["max_abs_prescribed_error_mm"] for row in rows),
        max_relative_global_force_balance=max(row["relative_global_force_balance"] for row in rows),
        scientific_array_fields_decoded_by_wrapper=0)


def observations_without_scientific_decode():
    value = dict(result_exists=(SCIENCE/"result.json").exists(), accepted_states=None, call_counts=None,
                 progress_records=None, accepted_archive_files=[], scientific_array_fields_decoded=0)
    if value["result_exists"]:
        try:
            result = read_json(SCIENCE/"result.json")
            value.update(production_status=result.get("status"), failure=result.get("failure"),
                accepted_states=len(result["accepted_steps"]), call_counts=result.get("call_counts"))
        except Exception as error:
            value["result_read_error"] = dict(type=type(error).__name__, message=str(error))
    progress = RUN/"accepted_progress.jsonl"
    if progress.exists():
        try:
            value["progress_records"] = sum(1 for line in progress.read_text(encoding="utf-8").splitlines() if json.loads(line))
        except Exception as error:
            value["progress_read_error"] = dict(type=type(error).__name__, message=str(error))
    accepted = SCIENCE/"accepted"
    if accepted.exists():
        value["accepted_archive_files"] = [dict(path=str(path), bytes=path.stat().st_size)
            for path in sorted(accepted.rglob("*.npz")) if path.is_file()]
    return value


def helper():
    start = time.monotonic()
    deadline = float(os.environ["PROBE1_HELPER_DEADLINE"])
    receipt = dict(schema="hf-ctipprobe1-helper-1", status="not_pass", phase="preflight",
        start_utc=datetime.now(timezone.utc).isoformat(), start_monotonic=start,
        deadline_monotonic=deadline, scientific_process_launches=0, viewer_process_launches=0,
        production_installations=0, archive_owner="root_outer_bootstrap", external_retries=0)
    try:
        protocol, checked = validate_protocol()
        receipt["checked_bindings"] = checked
        write_new(RUN/"protocol_copy.json", protocol)
        copy_parent(protocol, deadline)
        env = finite_environment(protocol)
        receipt["phase"] = "science"
        if deadline-time.monotonic() <= protocol["viewer_reserve_seconds"]+5:
            raise TimeoutError("insufficient original helper window for science and reserved later phases")
        science_deadline = min(deadline-protocol["viewer_reserve_seconds"], time.monotonic()+protocol["science_process_cap_seconds"])
        if science_deadline-time.monotonic() < protocol["controller_seconds"]+5:
            raise TimeoutError("insufficient original shared window for the full controller opportunity and cleanup")
        command = [protocol["python_executable"], "-X", "utf8", "-B", str(BASE/"run_probe1.py"), "--science-child"]
        receipt["scientific_process_launches"] = 1
        record = run_owned(command, cwd=str(BASE), env=env, log=RUN/"science_stdout.log",
            deadline=science_deadline, seconds=protocol["science_process_cap_seconds"],
            rss_limit=protocol["memory_limit_bytes"], instance_log_path=RUN/"science_instances.ndjson",
            instance_identity=dict(stage="L-CTIPPROBE1", phase="single_API_science"))
        receipt["science_supervision"] = record
        write_new(RUN/"science_supervision.json", record)
        if not phase_pass(record):
            raise RuntimeError("unique scientific process or same-instance cleanup failed")
        receipt["science_child"] = read_json(RUN/"science_child_receipt.json")
        if receipt["science_child"]["api_call_attempts"] != 1 or not receipt["science_child"]["api_returned"]:
            raise ValueError("the unique public API call did not return")
        validated = validate_numerical_result(protocol, deadline)
        receipt["numerical_validation"] = validated
        write_new(RUN/"numerical_validation.json", validated)
        receipt["phase"] = "viewer"
        if deadline-time.monotonic() <= 605:
            raise TimeoutError("insufficient original helper window for one viewer plus cleanup")
        command = [protocol["python_executable"], "-X", "utf8", "-B", str(BASE/"render_probe1.py"),
            "--protocol", str(PROTOCOL), "--result", str(SCIENCE/"result.json"), "--output", str(VIEW)]
        receipt["viewer_process_launches"] = 1
        record = run_owned(command, cwd=str(BASE), env=env, log=RUN/"viewer_stdout.log",
            deadline=deadline-5, seconds=protocol["viewer_seconds"],
            rss_limit=protocol["viewer_memory_limit_bytes"], instance_log_path=RUN/"viewer_instances.ndjson",
            instance_identity=dict(stage="L-CTIPPROBE1", phase="pure_saved_viewer"))
        receipt["viewer_supervision"] = record
        write_new(RUN/"viewer_supervision.json", record)
        if not phase_pass(record):
            raise RuntimeError("unique viewer or same-instance cleanup failed")
        render = read_json(VIEW/"renderer_receipt.json")
        n = validated["accepted_states"]
        if (render["status"] != "rendered_pending_visual_check" or render["accepted_states"] != n
                or render["archives_decoded"] != n or render["fields_decoded"] != 2*n or 2*n > 10
                or render["new_png_count"] != 3 or render["gif_frame_count"] != n or render["scientific_calls"] != 0):
            raise ValueError("pure viewer actual read/output counts differ from authorized scope")
        receipt["renderer"] = render
        check_clock(deadline, "after viewer metadata receipt")
        receipt.update(status="ready_for_visual_check", phase="complete_without_installation")
    except BaseException as error:
        receipt["error"] = dict(type=type(error).__name__, code=getattr(error, "code", None), message=str(error), traceback=traceback.format_exc())
    finally:
        receipt["actual_partial_observation"] = observations_without_scientific_decode()
        receipt["elapsed_seconds"] = time.monotonic()-start
        receipt["end_utc"] = datetime.now(timezone.utc).isoformat()
        write_new(RUN/"helper_receipt.json", receipt)
    return 0 if receipt["status"] == "ready_for_visual_check" else 1


if __name__ == "__main__":
    if sys.argv[1:] == ["--science-child"]:
        raise SystemExit(scientific_child())
    if sys.argv[1:]:
        raise SystemExit("no alternate execution mode is authorized")
    raise SystemExit(helper())
