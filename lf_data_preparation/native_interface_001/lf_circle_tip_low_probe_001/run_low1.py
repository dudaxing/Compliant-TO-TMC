"""One LOW1 helper; its parent and probe each call one existing public API.

The helper reads ordinary metadata and hashes bytes. Only its two explicitly
selected scientific children import HF. There is no retry or source install.
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
PARENT = RUN / "parent_fixed"
PROBE = RUN / "probe_low"
VIEW = RUN / "view"
SETTINGS = dict(tolerance=1e-9, constraint_tolerance=1e-10,
    displacement_scale_floor=1e-6, force_scale_floor_factor=1e-8,
    max_checks=25, armijo_c=1e-4, max_backtracks=12, max_bisections=4,
    minimum_increment=.00625, time_limit_seconds=3600.)


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


def finite_environment(protocol):
    env = os.environ.copy()
    env.update(PYTHONPATH=protocol["candidate_source"], PYTHONDONTWRITEBYTECODE="1",
        JAX_ENABLE_X64="true", JAX_PLATFORMS="cpu", MPLBACKEND="Agg")
    env.update({key: str(value) for key, value in protocol["cpu_thread_environment"].items()})
    return env


def validate_protocol():
    value = read_json(PROTOCOL)
    if (value.get("schema_version") != "hf-ctiplow1-protocol-1"
            or value.get("status") != "frozen_ready_for_unique_authorized_launch"):
        raise ValueError("wrong frozen LOW1 protocol")
    budgets = dict(parent_controller_seconds=3600, probe_controller_seconds=3600,
        parent_process_cap_seconds=3800, probe_process_cap_seconds=3800,
        viewer_seconds=900, viewer_process_cap_seconds=965,
        helper_seconds=9000, outer_seconds=9060,
        helper_content_deadline_offset_seconds=8900,
        helper_process_deadline_offset_seconds=8910,
        outer_process_deadline_offset_seconds=9050)
    if any(value.get(key) != expected for key, expected in budgets.items()):
        raise ValueError("authorized stage/resource budget changed")
    if (value.get("memory_limit_bytes") != 64*1024**3
            or value.get("viewer_memory_limit_bytes") != 8*1024**3):
        raise ValueError("authorized memory limits changed")
    if (value.get("parent_targets_mm") != [0., .25, .5]
            or value.get("body_q_targets_mm") != [0., .025]
            or value.get("held_input_mean_mm") != .5
            or value.get("parent_settings") != SETTINGS):
        raise ValueError("authorized explicit parent/probe controls or original settings changed")
    if (Path(value["runtime_base"]).resolve() != BASE
            or Path(value["run_directory"]).resolve() != RUN):
        raise ValueError("runtime directories differ from frozen locations")
    expected_threads = {name: "16" for name in (
        "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")}
    if {key: str(item) for key, item in value["cpu_thread_environment"].items()} != expected_threads:
        raise ValueError("four-library thread contract changed")
    if (Path(value["geometry_file"]).resolve() != BASE/"geometry"/"geometry.json"
            or Path(value["task_file"]).resolve() != BASE/"task.json"):
        raise ValueError("unexpected parent input location")
    entries = value["geometry_files"]
    if len(entries) != 1 or entries[0]["relative_path"] != "geometry.npz":
        raise ValueError("only the original geometry archive may be copied")
    bindings = value.get("bindings")
    if not isinstance(bindings, list) or not bindings:
        raise ValueError("candidate byte bindings missing")
    checked = []
    for binding in bindings:
        if Path(binding["path"]).suffix.casefold() == ".npz":
            raise ValueError("NPZ copy identities belong in geometry_files, not executable bindings")
        actual = identity(binding["path"])
        if actual["sha256"] != binding["sha256"] or actual["bytes"] != binding["bytes"]:
            raise ValueError("frozen source byte mismatch: " + actual["path"])
        checked.append(actual)
    required = [BASE/name for name in ("run_low1.py", "launch_low1.py", "outer_low1.py",
        "render_low1.py", "windows_owned_process_sup2.py")]
    required += [Path(value[key]) for key in ("observer_file", "geometry_file", "task_file", "high_table_file")]
    required += [Path(value["candidate_source"])/"hf_eval"/name for name in
        ("native_evaluate.py", "native_probe.py", "native_mean.py", "split_displacement.py")]
    if not {str(path.resolve()).casefold() for path in required} <= {row["path"].casefold() for row in checked}:
        raise ValueError("required executable or input absent from frozen bindings")
    if Path(value["observer_file"]).resolve() != Path(value["observer_definition_path"]).resolve():
        raise ValueError("observer aliases differ")
    task = read_json(value["task_file"])
    if (task["input"]["target_mm"] != .5 or task["path"] != dict(kind="load_only", targets_mm=[0., .25, .5])
            or task["workpiece"] != dict(kind="fixed_rigid", shape="circle", center_mm=[80., 40.],
                                        radius_mm=9., fixed_components=[0, 1])
            or task["regularization"] != dict(alpha=2.5e-7, length_mm=80.)
            or task["third_medium"] != dict(gamma=1e-6)):
        raise ValueError("explicit new fixed short-parent physics changed")
    return value, checked


def copy_geometry(protocol, deadline):
    receipt = dict(status="not_pass", copied=[], scientific_array_fields_decoded=0)
    try:
        for entry in protocol["geometry_files"]:
            check_clock(deadline, "geometry byte copy")
            source = Path(entry["source"])
            target = BASE/"geometry"/entry["relative_path"]
            raw = source.read_bytes()
            if len(raw) != entry["bytes"] or hashlib.sha256(raw).hexdigest() != entry["sha256"]:
                raise ValueError("original geometry archive bytes differ")
            with target.open("xb") as stream:
                stream.write(raw)
            actual = identity(target)
            if actual["bytes"] != entry["bytes"] or actual["sha256"] != entry["sha256"]:
                raise ValueError("copied geometry archive bytes differ")
            receipt["copied"].append(dict(source=str(source), **actual))
        receipt["status"] = "pass"
    finally:
        write_new(RUN/"geometry_copy_receipt.json", receipt)


def scientific_child(phase):
    started = time.monotonic()
    receipt = dict(schema="hf-ctiplow1-scientific-child-1", phase=phase, status="not_pass",
        start_utc=datetime.now(timezone.utc).isoformat(), start_monotonic=started,
        api_call_attempts=0, api_returned=False, external_retries=0,
        new_HP_calls_by_wrapper=0, new_tests=0, production_installations=0,
        scientific_array_decode_monitoring="not instrumented; original source read contract frozen")
    try:
        protocol, _ = validate_protocol()
        phase_deadline = float(os.environ["LOW1_PHASE_DEADLINE"])
        check_clock(phase_deadline, "before scientific import")
        sys.path.insert(0, protocol["candidate_source"])
        import hf_eval
        if Path(hf_eval.__file__).resolve() != Path(protocol["candidate_source"])/"hf_eval"/"__init__.py":
            raise ValueError("HF package imported outside frozen candidate")
        if phase == "parent":
            from hf_eval.displacement import DisplacementSettings
            import hf_eval.native_evaluate as api_module
            if Path(api_module.__file__).resolve() != Path(protocol["candidate_source"])/"hf_eval"/"native_evaluate.py":
                raise ValueError("parent API import resolved outside frozen candidate")
            original_solve = api_module.solve_native_mean
            receipt.update(solve_call_attempts=0, solve_calls_completed=0, callback_accepted_states=0)
            with (RUN/"parent_accepted_progress.jsonl").open("xb", buffering=0) as progress:
                def observe_cached_solve(*args, **kwargs):
                    # Same read-only cache observation as the original loading
                    # gate; original solver still called once and returns intact.
                    receipt["solve_call_attempts"] += 1
                    previous_callback = kwargs.get("on_accept")

                    def accepted(snapshot):
                        check_clock(phase_deadline, "parent accepted callback")
                        record = snapshot.record
                        event = dict(accepted_index=receipt["callback_accepted_states"],
                            utc=datetime.now(timezone.utc).isoformat(), elapsed_seconds=time.monotonic()-started,
                            **{key: record[key] for key in ("d", "R_input", "q_in", "q_out",
                                "relative_residual", "constraint_residual", "constraint_bound", "minimum_J",
                                "relative_global_force_balance", "newton_checks", "bisection_depth",
                                "state_sha256", "leg", "original_target_index", "is_original_target")})
                        receipt["callback_accepted_states"] += 1
                        raw = (json.dumps(event, allow_nan=False, separators=(",", ":"))+"\n").encode("utf-8")
                        if progress.write(raw) != len(raw):
                            raise OSError("short parent progress write")
                        os.fsync(progress.fileno())
                        if previous_callback is not None:
                            previous_callback(snapshot)

                    kwargs["on_accept"] = accepted
                    result = original_solve(*args, **kwargs)
                    receipt["solve_calls_completed"] += 1
                    rows = [snapshot.record for snapshot in result.accepted]
                    minimum_J = min((float(snapshot.arrays["J"].min()) for snapshot in result.accepted), default=None)
                    fixed = max((abs(math.fsum((float(snapshot.state.lift[i]), float(snapshot.state.fluctuation[i]))))
                        for snapshot in result.accepted for i in result.project.model.fixed_dofs), default=0.)
                    cached = dict(actual_accepted_states=len(rows), minimum_J=minimum_J,
                        maximum_fixed_split_sum_mm=fixed,
                        maximum_relative_residual=max((row["relative_residual"] for row in rows), default=0.),
                        native_constraint_bound_pass=all(abs(row["constraint_residual"]) <= row["constraint_bound"] for row in rows),
                        maximum_relative_global_force_balance=max((row["relative_global_force_balance"] for row in rows), default=0.))
                    cached["passed"] = (bool(rows) and minimum_J > 0 and fixed <= 8e-11
                        and cached["maximum_relative_residual"] <= 1e-9 and cached["native_constraint_bound_pass"]
                        and cached["maximum_relative_global_force_balance"] <= 1e-6)
                    receipt["cached_production_gates"] = cached
                    return result

                if phase_deadline-time.monotonic() < protocol["parent_controller_seconds"]+5:
                    raise TimeoutError("full parent controller opportunity plus cleanup no longer available")
                receipt["api_call_attempts"] = 1
                api_module.solve_native_mean = observe_cached_solve
                try:
                    response = api_module.evaluate_native(protocol["geometry_file"], protocol["task_file"], PARENT,
                        targets=protocol["parent_targets_mm"], settings=DisplacementSettings(**protocol["parent_settings"]),
                        response_mode="mechanical", tangent_mode="chunk256", initial_guess="port_projection")
                finally:
                    api_module.solve_native_mean = original_solve
            receipt.update(status="returned", api_returned=True, production_status=response["status"],
                failure=response.get("failure"), response_identity=identity(PARENT/"response.json"),
                read_contract="Original geometry four masks; zero start; original returned cache J and fixed lift/fluctuation gate only; no NPZ decode/old state/force/matrix by observer")
        else:
            import hf_eval.native_probe as api_module
            if Path(api_module.__file__).resolve() != Path(protocol["candidate_source"])/"hf_eval"/"native_probe.py":
                raise ValueError("probe API import resolved outside frozen candidate")
            parent = read_json(PARENT/"result.json")
            selected = len(parent["states"])-1
            receipt["selected_parent_state_index"] = selected
            with (RUN/"probe_accepted_progress.jsonl").open("xb", buffering=0) as progress:
                accepted_count = 0

                def accepted(record):
                    nonlocal accepted_count
                    check_clock(phase_deadline, "probe accepted callback")
                    event = dict(accepted_index=accepted_count, utc=datetime.now(timezone.utc).isoformat(),
                        elapsed_seconds=time.monotonic()-started,
                        **{key: record[key] for key in ("body_q_mm", "input_mean_mm", "R_input_N",
                        "Q_drive_half_N", "relative_residual", "constraint_residual", "minimum_J",
                        "max_abs_Hu_per_mm", "newton_checks", "bisection_depth", "state_sha256",
                        "is_original_target", "original_target_index")})
                    accepted_count += 1
                    raw = (json.dumps(event, ensure_ascii=False, allow_nan=False, separators=(",", ":"))+"\n").encode("utf-8")
                    if progress.write(raw) != len(raw):
                        raise OSError("short progress write")
                    os.fsync(progress.fileno())

                if phase_deadline-time.monotonic() < protocol["probe_controller_seconds"]+5:
                    raise TimeoutError("full probe controller opportunity plus cleanup no longer available")
                receipt["api_call_attempts"] = 1
                result = api_module.evaluate_native_guided_probe(PARENT/"result.json", selected,
                    protocol["body_q_targets_mm"], PROBE,
                    time_limit_seconds=protocol["probe_controller_seconds"], on_accept=accepted)
                receipt.update(status="returned", api_returned=True, production_status=result["status"],
                    failure=result["failure"], accepted_states=len(result["accepted_steps"]),
                    callback_accepted_states=accepted_count, call_counts=result["call_counts"],
                    result_identity=identity(PROBE/"result.json"),
                    read_contract="New parent model archive byte identity; original four geometry masks; new terminal lift/fluctuation only")
        receipt["imported_module_paths"] = dict(package=hf_eval.__file__, api=api_module.__file__)
    except BaseException as error:
        receipt["error"] = dict(type=type(error).__name__, code=getattr(error, "code", None),
            message=str(error), traceback=traceback.format_exc())
    finally:
        receipt["elapsed_seconds"] = time.monotonic()-started
        receipt["end_utc"] = datetime.now(timezone.utc).isoformat()
        write_new(RUN/(phase+"_child_receipt.json"), receipt)
    return 0 if receipt["api_returned"] else 1


def finite_number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("invalid saved scalar: " + label)
    return value


def accepted_gates(row, mean_target, mean_key):
    mean = finite_number(row[mean_key], "input mean")
    bound = 1e-10*max(abs(mean_target), 1e-6)
    if (abs(mean-mean_target) > bound
            or abs(finite_number(row["constraint_residual"], "constraint residual")) > row["constraint_bound"]
            or row["constraint_bound"] != bound
            or finite_number(row["relative_residual"], "relative residual") > 1e-9
            or finite_number(row["minimum_J"], "minimum J") <= 0
            or finite_number(row["relative_global_force_balance"], "global balance") > 1e-6):
        raise ValueError("an original saved numerical acceptance gate did not pass")


def new_archive_identities(root, rows, kinds, deadline):
    identities = []
    for index, row in enumerate(rows):
        for kind in kinds:
            check_clock(deadline, "new archive byte identity")
            declaration = row[kind]
            path = (root/declaration["path"]).resolve()
            path.relative_to(root)
            actual = identity(path)
            if actual["sha256"] != declaration["sha256"]:
                raise ValueError("new archive bytes differ from declared identity")
            identities.append(actual | dict(accepted_index=index, kind=kind, decoded_by_wrapper=False))
    return identities


def validate_parent(protocol, deadline):
    check_clock(deadline, "parent metadata checks")
    result, response = read_json(PARENT/"result.json"), read_json(PARENT/"response.json")
    child = read_json(RUN/"parent_child_receipt.json")
    if (child["solve_call_attempts"] != 1 or child["solve_calls_completed"] != 1
            or child["cached_production_gates"]["passed"] is not True
            or child["cached_production_gates"]["actual_accepted_states"] != len(result["states"])
            or child["callback_accepted_states"] != len(result["states"])):
        raise ValueError("original fresh-cache parent gates or unique solver call failed")
    if (response["status"] != "success" or response["failure"] is not None
            or result["status"] != "success" or result["failure"] is not None
            or any(result[key] is not True for key in
                ("path_completed", "target_reached", "loading_peak_reached", "task_target_executed", "production_converged"))
            or result["targets_mm"] != [0., .25, .5] or result["task_target_mm"] != .5
            or result["path_kind"] != "load_only" or result["target_origin"] != 0
            or result["lift_origin_zero"] is not True or result["lift_shape_zero"] is not True
            or "continuation" in result):
        raise ValueError("the new zero-start complete fixed-parent task did not pass")
    if (result["settings"] != SETTINGS or result["response_mode"] != "mechanical"
            or result["tangent_execution"]["mode"] != "chunk256" or result["initial_guess"] != "port_projection"):
        raise ValueError("explicit parent modes or original nonclock settings changed")
    if {key: result["counts"][key] for key in ("cells", "nodes", "dofs", "fixed_dofs")} != dict(
            cells=14720, nodes=14985, dofs=29970, fixed_dofs=1288):
        raise ValueError("parent full-model dimensions differ")
    model = read_json(PARENT/result["model"]["descriptor_path"])
    if model["task"] != read_json(protocol["task_file"]):
        raise ValueError("saved parent embedded task differs from the frozen new task")
    rows = result["states"]
    if len(rows) < 3 or [row["d"] for row in rows if row["is_original_target"]] != [0., .25, .5]:
        raise ValueError("parent original targets are incomplete")
    originals = [row for row in rows if row["is_original_target"]]
    if ([row["original_target_index"] for row in originals] != [0, 1, 2]
            or [row["leg"] for row in originals] != ["origin", "loading", "loading"]):
        raise ValueError("parent original-target identity differs")
    peak = rows[-1]
    if (peak["is_original_target"] is not True or peak["original_target_index"] != 2
            or any(peak[key] != .5 for key in ("d", "original_target_displacement", "physical_mean_target_mm"))):
        raise ValueError("new parent did not end at its original .50 loading peak")
    for row in rows:
        accepted_gates(row, finite_number(row["physical_mean_target_mm"], "parent target"), "q_in")
    counts = result["call_counts"]
    if (counts["solver_invocations"] != 1 or counts["HP_calls"] != 0
            or result["save_force_calls"] != 0 or result["save_tangent_calls"] != 0
            or any(result[key] is not False for key in ("independent_HP_qualified", "equilibrium_qualified", "HF_qualified"))):
        raise ValueError("parent computation or qualification contract differs")
    return dict(status="pass", parent_result_identity=identity(PARENT/"result.json"),
        accepted_states=len(rows), original_targets_mm=[0., .25, .5],
        selected_state_index=len(rows)-1, selected_state_sha256=peak["state_sha256"],
        selected_R_input_N=peak["R_input"], call_counts=counts,
        max_relative_residual=max(row["relative_residual"] for row in rows),
        min_J=min(row["minimum_J"] for row in rows),
        max_relative_global_force_balance=max(row["relative_global_force_balance"] for row in rows),
        cached_production_gates=child["cached_production_gates"],
        scientific_array_fields_decoded_by_wrapper=0,
        new_archive_byte_identities=new_archive_identities(PARENT, rows, ("state", "forces", "tangents", "matrix"), deadline))


def validate_probe(protocol, parent_validation, deadline):
    check_clock(deadline, "probe metadata checks")
    result, parent = read_json(PROBE/"result.json"), read_json(PARENT/"result.json")
    selected_index = parent_validation["selected_state_index"]
    peak = parent["states"][selected_index]
    if (result["schema_version"] != "hf-native-guided-probe-1.0" or result["status"] != "success"
            or result["target_reached"] is not True or result["failure"] is not None
            or result["probe_task"]["held_input_mean_mm"] != .5
            or result["probe_task"]["body_q_targets_mm"] != [0., .025]):
        raise ValueError("the low-hold prescribed q path did not succeed")
    if (result["response_mode"] != "mechanical" or result["tangent_mode"] != "chunk256"
            or result["initial_guess"] != "port_projection" or result["settings"] != SETTINGS):
        raise ValueError("probe inherited execution settings changed")
    model = result["model"]
    if (len(model["coordinates_mm"]) != 14985 or len(model["connectivity"]) != 14720
            or len(model["solid"]) != 14720 or len(model["body_nodes"]) != 565
            or len(model["fixed_dofs"]) != 1288 or len(model["zero_dofs"]) != 195):
        raise ValueError("probe full-model dimensions or body membership changed")
    selected = result["source"]["selected_state"]
    if (selected["accepted_index"] != selected_index or selected["state_sha256"] != peak["state_sha256"]
            or selected["R_input_N"] != peak["R_input"]
            or result["source"]["parent_result"]["sha256"] != parent_validation["parent_result_identity"]["sha256"]):
        raise ValueError("probe source is not the new successful original terminal parent")
    rows = result["accepted_steps"]
    if not 2 <= len(rows) <= 17 or [row["body_q_mm"] for row in rows if row["is_original_target"]] != [0., .025]:
        raise ValueError("accepted probe path differs from authorized original targets/read ceiling")
    anchor = rows[0]
    if (anchor["body_q_mm"] != 0 or anchor["fresh_anchor"] is not True or anchor["newton_checks"] != 1
            or anchor["state_sha256"] != peak["state_sha256"]
            or float(anchor["R_input_N"]).hex() != float(peak["R_input"]).hex()
            or anchor["state"]["fields"] != peak["state"]["fields"]):
        raise ValueError("q0 was changed or repaired instead of fresh identity validation")
    previous = -1.
    for row in rows:
        q = finite_number(row["body_q_mm"], "body q")
        if q <= previous or q < 0 or q > .025:
            raise ValueError("probe actual q sequence changed")
        previous = q
        accepted_gates(row, .5, "input_mean_mm")
        if finite_number(row["max_abs_prescribed_error_mm"], "prescribed error") > 8e-11:
            raise ValueError("original prescribed-body gate did not pass")
        if row["Q_drive_half_N"] != -row["force_on_body_N"]["total"][0]:
            raise ValueError("signed Q/ON-body convention changed")
        for component in ("total", "material", "regularization"):
            for value in row["force_on_body_N"][component]:
                finite_number(value, "ON body component")
    counts = result["call_counts"]
    if (counts["solver_invocations"] != 1 or counts["HP_calls"] != 0
            or counts["save_force_calls"] != 0 or counts["save_tangent_calls"] != 0
            or any(result[key] is not False for key in
                ("independent_HP_qualified", "effective_grasp_qualified", "release_qualified", "HF_qualified"))):
        raise ValueError("probe computation or qualification contract differs")
    return dict(status="pass", accepted_states=len(rows), body_q_original_targets_mm=[0., .025],
        q0_identity_preserved=True, selected_parent_state_index=selected_index, call_counts=counts,
        new_archive_byte_identities=new_archive_identities(PROBE, rows, ("state", "fields"), deadline),
        max_relative_residual=max(row["relative_residual"] for row in rows),
        min_J=min(row["minimum_J"] for row in rows),
        max_prescribed_error_mm=max(row["max_abs_prescribed_error_mm"] for row in rows),
        max_relative_global_force_balance=max(row["relative_global_force_balance"] for row in rows),
        scientific_array_fields_decoded_by_wrapper=0)


def observations_without_scientific_decode():
    answer = dict(scientific_array_fields_decoded=0)
    for phase, folder, rows_key in (("parent", PARENT, "states"), ("probe", PROBE, "accepted_steps")):
        item = dict(result_exists=(folder/"result.json").exists(), accepted_states=None)
        if item["result_exists"]:
            try:
                result = read_json(folder/"result.json")
                item.update(production_status=result.get("status"), failure=result.get("failure"),
                    accepted_states=len(result[rows_key]), call_counts=result.get("call_counts"))
            except Exception as error:
                item["metadata_read_error"] = dict(type=type(error).__name__, message=str(error))
        answer[phase] = item
    return answer


def helper():
    start = time.monotonic()
    deadline = float(os.environ["LOW1_HELPER_DEADLINE"])
    receipt = dict(schema="hf-ctiplow1-helper-1", status="not_pass", phase="preflight",
        start_utc=datetime.now(timezone.utc).isoformat(), start_monotonic=start,
        deadline_monotonic=deadline, parent_process_launches=0, probe_process_launches=0,
        viewer_process_launches=0, production_installations=0, external_retries=0,
        archive_owner="root_outer_bootstrap")
    try:
        protocol, checked = validate_protocol()
        receipt["checked_bindings"] = checked
        write_new(RUN/"protocol_copy.json", protocol)
        copy_geometry(protocol, deadline)
        env = finite_environment(protocol)
        for phase, reserve in (("parent", 8600), ("probe", 4800)):
            receipt["phase"] = phase
            if deadline-time.monotonic() < reserve:
                raise TimeoutError("insufficient original shared window before " + phase)
            cap = protocol[phase+"_process_cap_seconds"]
            phase_deadline = min(time.monotonic()+cap, deadline-(4800 if phase == "parent" else 975))
            if phase_deadline-time.monotonic() < protocol[phase+"_controller_seconds"]+5:
                raise TimeoutError("full controller plus cleanup opportunity not available")
            child_env = env | {"LOW1_PHASE_DEADLINE": str(phase_deadline)}
            receipt[phase+"_process_launches"] = 1
            record = run_owned([protocol["python_executable"], "-X", "utf8", "-B", str(BASE/"run_low1.py"), "--"+phase+"-child"],
                cwd=str(BASE), env=child_env, log=RUN/(phase+"_stdout.log"), deadline=phase_deadline,
                seconds=cap, rss_limit=protocol["memory_limit_bytes"], instance_log_path=RUN/(phase+"_instances.ndjson"),
                instance_identity=dict(stage="L-CTIPLOW1", phase=phase+"_single_API"))
            receipt[phase+"_supervision"] = record
            write_new(RUN/(phase+"_supervision.json"), record)
            if not phase_pass(record):
                raise RuntimeError("unique " + phase + " process or same-instance cleanup failed")
            child = read_json(RUN/(phase+"_child_receipt.json"))
            receipt[phase+"_child"] = child
            if child["api_call_attempts"] != 1 or child["api_returned"] is not True:
                raise ValueError("unique " + phase + " public API call did not return")
            validation = validate_parent(protocol, deadline) if phase == "parent" else validate_probe(protocol, receipt["parent_validation"], deadline)
            receipt[phase+"_validation"] = validation
            write_new(RUN/(phase+"_validation.json"), validation)
        receipt["phase"] = "viewer"
        if deadline-time.monotonic() < 975:
            raise TimeoutError("insufficient original window for one complete viewer and cleanup")
        receipt["viewer_process_launches"] = 1
        viewer_env = env | {"LOW1_VIEWER_DEADLINE": repr(min(time.monotonic()+protocol["viewer_seconds"], deadline))}
        record = run_owned([protocol["python_executable"], "-X", "utf8", "-B", str(BASE/"render_low1.py"),
            "--protocol", str(PROTOCOL), "--result", str(PROBE/"result.json"),
            "--parent", str(PARENT/"result.json"), "--output", str(VIEW)],
            cwd=str(BASE), env=viewer_env, log=RUN/"viewer_stdout.log", deadline=deadline-5,
            seconds=protocol["viewer_process_cap_seconds"], rss_limit=protocol["viewer_memory_limit_bytes"],
            instance_log_path=RUN/"viewer_instances.ndjson", instance_identity=dict(stage="L-CTIPLOW1", phase="pure_saved_viewer"))
        receipt["viewer_supervision"] = record
        write_new(RUN/"viewer_supervision.json", record)
        if not phase_pass(record):
            raise RuntimeError("unique viewer or same-instance cleanup failed")
        render = read_json(VIEW/"renderer_receipt.json")
        n = receipt["probe_validation"]["accepted_states"]
        if (render["status"] != "rendered_pending_visual_check" or render["accepted_states"] != n
                or render["archives_decoded"] != n or render["fields_decoded"] != 2*n or 2*n > 34
                or render["new_png_count"] != 4 or render["gif_frame_count"] != n
                or render["scientific_calls"] != 0):
            raise ValueError("pure viewer actual read/output counts differ from card")
        receipt["renderer"] = render
        check_clock(deadline, "after viewer ordinary receipt")
        receipt.update(status="ready_for_visual_check", phase="complete_without_installation")
    except BaseException as error:
        receipt["error"] = dict(type=type(error).__name__, code=getattr(error, "code", None),
            message=str(error), traceback=traceback.format_exc())
    finally:
        receipt["actual_partial_observation"] = observations_without_scientific_decode()
        receipt["elapsed_seconds"] = time.monotonic()-start
        receipt["end_utc"] = datetime.now(timezone.utc).isoformat()
        write_new(RUN/"helper_receipt.json", receipt)
    return 0 if receipt["status"] == "ready_for_visual_check" else 1


if __name__ == "__main__":
    if sys.argv[1:] in (["--parent-child"], ["--probe-child"]):
        raise SystemExit(scientific_child(sys.argv[1][2:-6]))
    if sys.argv[1:]:
        raise SystemExit("no alternate execution mode is authorized")
    raise SystemExit(helper())
