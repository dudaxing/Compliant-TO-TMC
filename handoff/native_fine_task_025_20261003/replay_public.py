"""One native-fine original 0.025 mm TEST recovery with frozen JSON rules.

The formal result supplies its actual call counts and all accepted states.
Every retained physical/diagnostic JSON field and all numeric payload bytes
must agree. No HP, JIT, LF import or new scientific qualification is involved.
"""
from time import perf_counter, sleep
STARTED = perf_counter()
import argparse
from hashlib import sha256
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT/"handoff/native_mean_20261003/replay_public.py"
HELPER_SHA = "9cdd3f6a12229cc2c3fe8febc0eedd47ba1a3b771b46aa4f220c4267236032b6"
if sha256(HELPER.read_bytes()).hexdigest() != HELPER_SHA:
    raise ValueError("Frozen public replay comparison helper changed")
spec = importlib.util.spec_from_file_location("_frozen_native_mean_replay_comparison", HELPER)
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)
digest, read, require = contract.digest, contract.read, contract.require
verify_descriptor = contract.verify_descriptor
normalized_state, normalized_result, recursive_equal = contract.normalized_state, contract.normalized_result, contract.recursive_equal

import numpy as np
import psutil

REPLAY_CONTRACT = read(Path(__file__).with_name("replay_contract.json"))
LIMIT = float(REPLAY_CONTRACT["seconds_limit"])
RSS_LIMIT = 8*1024**3
SETTINGS = dict(tolerance=1e-9, constraint_tolerance=1e-10, displacement_scale_floor=1e-6,
    force_scale_floor_factor=1e-8, max_checks=25, armijo_c=1e-4, max_backtracks=12,
    max_bisections=4, minimum_increment=.001/16, time_limit_seconds=1500.)

TARGETS = [0., .005, .010, .025]
BASELINE = "66398e9245c63c05d225f015cf50f1d95909344d"
EXPECTED_COUNTS = REPLAY_CONTRACT["expected_call_counts"]
FORMAL_PINS = REPLAY_CONTRACT["formal_pins"]
require(set(FORMAL_PINS) == {"input_inventory.json", "execution_receipt.json",
    "production_launch_receipt.json", "reference_launch_receipt.json", "result/result.json",
    "audit/summary.json", "audit/lifecycle.json"}, "Formal replay pin set differs")
require(math.isfinite(LIMIT) and LIMIT >= SETTINGS["time_limit_seconds"]
    and REPLAY_CONTRACT["outer_seconds"] == LIMIT+60, "Replay clock contract differs")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New directory outside the clone")
    args = parser.parse_args()
    output = args.output.resolve()
    require(not output.is_relative_to(ROOT), "Replay output must be outside the public clone")
    output.mkdir(parents=True, exist_ok=False)
    stage = ROOT/"lf_data_preparation/native_fine_task_025_001"
    inventory_file, receipt_file = stage/"input_inventory.json", stage/"execution_receipt.json"
    record = dict(schema_version="native-fine-task-025-public-replay-1.0", status="running",
        scope="One same-machine independent-directory native fine original [0,0.005,0.010,0.025] mm CLI recovery; no new scientific qualification",
        invocations=0, force_calls=None, tangent_calls=None, solver_calls=None, HP_calls=0, JIT_calls=0, LF_imports=0,
        seconds_limit=LIMIT, sampled_RSS_limit_bytes=RSS_LIMIT, outer_timeout_required_seconds=REPLAY_CONTRACT["outer_seconds"],
        budget_mode="Cooperative elapsed/RSS checks and external timeout; not an OS memory hard cap",
        counter_semantics="Returned saved API counters; unavailable if CLI has not returned a result",
        equal_files=[], equal_arrays=0, equal_JSONs=[],
        JSON_exclusions=dict(result=["timing_seconds.project_preparation", "timing_seconds.evaluation", "descriptor_sha256"],
            path_diagnostics=["timing_seconds."+key for key in contract.PATH_TIMES],
            state=["elapsed_seconds", "descriptor_sha256"], flat_state=["descriptor_file_sha256"]),
        retained_time_settings=True, retained_kernel_call_counts=True,
        payload_comparison="Exact NPZ file bytes and every array dtype, shape and C-order bytes; original source file bytes",
        metadata_comparison="Frozen normalizers: explicit measured times/consequent hashes excluded; every other field recursively exact",
        comparison_helper_sha256=HELPER_SHA,
        root_PID_memory_scope="Popen root/launch PID only; excludes descendant workers and is not whole-solver memory",
        root_PID_peak_used_as_whole_solver_memory=False,
        resource_memory_acceptance="Cooperative sampled wrapper plus full child tree including all descendant workers, below 8 GiB",
        output_reference_direction=[0., 1.], physical_output_mean="q_out = physical weighted uy; output reference is +y",
        original_task_target_mm=.025, task_target_executed=True,
        cli_returncode=None, API_counter_observation_error="No complete saved result observed",
        process_completion_contract="True Popen return code plus complete saved payload agreement; member observations are diagnostic only",
        complete_descendant_cleanup_qualified=False, replay_contract_sha256=digest(Path(__file__).with_name("replay_contract.json")),
        different_design_from_coarse=True, fine_mesh_convergence_qualified=False)
    peak_child = peak_total = peak_root_pid = peak_root_pid_os = 0
    owner, child, members = psutil.Process(), None, []

    def sample():
        nonlocal peak_child, peak_total, peak_root_pid, peak_root_pid_os, members
        current = []
        if child is not None and child.poll() is None:
            try:
                process = psutil.Process(child.pid)
                current = [process]+process.children(recursive=True)
                memory = process.memory_info()
                peak_root_pid = max(peak_root_pid, memory.rss)
                peak_root_pid_os = max(peak_root_pid_os, getattr(memory, "peak_wset", 0))
            except psutil.NoSuchProcess:
                pass
        current = list({p.pid: p for p in [*members, *current] if p.is_running()}.values())
        members = current
        rss = 0
        for member in current:
            try:
                rss += member.memory_info().rss
            except psutil.NoSuchProcess:
                pass
        peak_child, peak_total = max(peak_child, rss), max(peak_total, owner.memory_info().rss+rss)
        require(perf_counter()-STARTED <= LIMIT, "Public native fine mean replay elapsed budget exceeded")
        require(peak_total <= RSS_LIMIT, "Public native fine mean replay sampled tree RSS exceeded 8 GiB")

    def observe_members():
        observations = []
        for member in members:
            try:
                observations.append(dict(pid=member.pid, creation_time=member.create_time(),
                    status=member.status(), diagnostic_only=True))
            except psutil.Error as error:
                observations.append(dict(pid=member.pid, observation_error=repr(error), diagnostic_only=True))
        return observations

    def observe_saved_result():
        file = output/"result/result.json"
        try:
            value = read(file)
            verify_descriptor(value)
            counts = value["call_counts"]
            observed = dict(API_counter_observation_error=None, saved_API_status=value["status"],
                saved_API_result_sha256=digest(file), call_counts=counts,
                force_calls=counts["force_calls"], tangent_calls=counts["tangent_calls"],
                solver_calls=counts["solver_invocations"])
        except (OSError, ValueError, KeyError, TypeError) as error:
            record["API_counter_observation_error"] = repr(error)
        else:
            record.update(observed)

    def compare_file(relative, expected, actual, count=None):
        sample()
        pin = digest(expected)
        require(digest(actual) == pin, "Public payload byte mismatch: "+relative)
        item = dict(path=relative, sha256=pin)
        record["equal_files"].append(item)
        if count is not None:
            item["arrays"] = []
            with np.load(expected, allow_pickle=False) as left, np.load(actual, allow_pickle=False) as right:
                require(set(left.files) == set(right.files) and len(left.files) == count,
                    "Public NPZ field/count mismatch: "+relative)
                for name in left.files:
                    a, b = left[name], right[name]
                    require(a.dtype == b.dtype and a.shape == b.shape and a.tobytes(order="C") == b.tobytes(order="C"),
                        "Public raw array differs: "+relative+"/"+name)
                    item["arrays"].append(dict(name=name, dtype=a.dtype.name, shape=list(a.shape),
                        sha256=sha256(a.tobytes(order="C")).hexdigest()))
                    record["equal_arrays"] += 1
        sample()

    try:
        sample()
        for name, pin in FORMAL_PINS.items():
            require(digest(stage/name) == pin, "Frozen formal evidence differs: "+name)
        inventory, receipt = read(inventory_file), read(receipt_file)
        case = inventory["case"]
        require(inventory["schema_version"] == "native-mean-input-inventory-1.0"
            and inventory["baseline_commit"] == BASELINE
            and case["alias"] == "gripper_native_fine" and case["targets_mm"] == TARGETS
            and (case["elements"], case["dofs"], case["fixed_DOFs"], case["free_DOFs"]) == (12800, 26082, 169, 25913)
            and inventory["settings"] == SETTINGS and receipt["status"] == "pass" and receipt["invocations"] == 1
            and receipt["input_inventory_sha256"] == digest(inventory_file)
            and receipt["HP_calls"] == receipt["JIT_calls"] == receipt["LF_imports"] == 0
            and receipt["solver_calls"] == 1 and receipt["task_target_executed"] is True
            and len(receipt["sources"]) == 39
            and len({Path(name).name for name in receipt["sources"]}) == 39
            and inventory["execution_limits"] == dict(production_seconds=1500, reference_seconds=720,
                sampled_RSS_bytes=RSS_LIMIT, production_outer_seconds=1560, reference_outer_seconds=780, view_outer_seconds=120),
            "Saved native fine prefix TEST scope differs")
        expected = stage/case["result_directory"]
        require(digest(expected/"result.json") == receipt["result_sha256"], "Saved official result differs")
        left = read(expected/"result.json")
        verify_descriptor(left)
        counts, original_states = left["call_counts"], left["states"]
        nstates = len(original_states)
        require(left["schema_version"] == "hf-native-mean-result-1.0" and left["status"] == "success"
            and left["target_reached"] is True and left["task_target_executed"] is True
            and left["targets_mm"] == case["targets_mm"] and left["settings"] == SETTINGS
            and left["task_target_mm"] == .025 and left["k_out_N_per_mm"] == 0.
            and left["save_force_calls"] == left["save_tangent_calls"] == 0
            and left["equilibrium_qualified"] is left["independent_HP_qualified"] is left["HF_qualified"] is False
            and nstates == REPLAY_CONTRACT["accepted_states"] >= 4 and left["accepted_states"] == receipt["accepted_states"] == nstates
            and [row["d"] for row in original_states if row["is_original_target"]] == case["targets_mm"]
            and original_states[0]["d"] == 0. and original_states[-1]["d"] == .025
            and all(a["d"] < b["d"] for a, b in zip(original_states, original_states[1:])), "Formal accepted path differs")
        require(counts == receipt["call_counts"] == EXPECTED_COUNTS and counts["force_calls"] == counts["force_calls_completed"]
            and counts["tangent_calls"] == counts["tangent_calls_completed"] >= nstates
            and counts["force_calls"] >= counts["tangent_calls"] and counts["solver_invocations"] == 1
            and counts["HP_calls"] == counts["JIT_calls"] == 0
            and receipt["force_calls"] == counts["force_calls"] and receipt["tangent_calls"] == counts["tangent_calls"]
            and receipt["state_sha256"] == [row["state_sha256"] for row in original_states], "Formal counters/state identity differ")
        model_meta = read(expected/left["model"]["descriptor_path"])
        verify_descriptor(model_meta)
        require(digest(expected/left["model"]["descriptor_path"]) == left["model"]["descriptor_file_sha256"]
            and left["model"]["arrays_sha256"] == receipt["model_sha256"] == case["prior_model_sha256"]
            and digest(expected/left["model"]["arrays_path"]) == case["prior_model_sha256"]
            and model_meta["task"] == read(ROOT/case["task_file"])
            and model_meta["task"]["case_family"] == "gripper"
            and model_meta["task"]["input"]["target_mm"] == .025, "Formal model/task identity differs")
        audit_root = stage/"audit"
        audit, lifecycle = read(audit_root/"summary.json"), read(audit_root/"lifecycle.json")
        require(audit["schema_version"] == "native-mean-independent-audit-1.0" and audit["status"] == "pass"
            and audit["alias"] == "gripper_native_fine" and audit["case_family"] == "gripper"
            and audit["input_reference_direction"] == [1., 0.] and audit["output_reference_direction"] == [0., 1.]
            and audit["input_port_dofs"] == [24472, 24794, 25116, 25438, 25760] and audit["output_port_dofs"] == [18353, 18675, 18997, 19319, 19641]
            and audit["input_port_weights"] == audit["output_port_weights"] == [.125, .25, .25, .25, .125]
            and audit["baseline_commit"] == BASELINE and audit["audited_targets_mm"] == TARGETS
            and audit["prefix_target_mm"] == TARGETS[-1] and audit["task_target_mm"] == .025
            and audit["task_target_executed"] is True and audit["recorded_native_model_is_fine"] is True
            and audit["result_sha256"] == receipt["result_sha256"]
            and audit["source_bindings"] == receipt["sources"] and audit["gates"] == inventory["gates"]
            and audit["full_element_and_DOF_coverage"] is True and audit["HP_matrix_columns_exhaustively_checked"] is False
            and audit["accepted_states"] == len(audit["states"]) == nstates
            and audit["HP_calls_started"] == audit["HP_calls_completed"] == 2*nstates
            and lifecycle["status"] == "pass" and lifecycle["accepted_states_completed"] == nstates
            and lifecycle["HP_calls_started"] == lifecycle["HP_calls_completed"] == 2*nstates, "Formal independent audit is not complete/pass")
        for index, (item, row) in enumerate(zip(audit["states"], original_states, strict=True)):
            require(item["status"] == "pass" and item["index"] == index
                and item["state_sha256"] == row["state_sha256"] and item["target_mm"] == row["d"]
                and item["elements_compared"] == 12800 and item["global_DOFs_compared"] == 26082
                and item["HP_calls"] == 2, "Formal reference state coverage differs")
        for name in ("production_launch_receipt.json", "reference_launch_receipt.json"):
            launch = read(stage/name)
            require(launch["status"] == "pass" and launch["exit_code"] == 0, "Formal stage did not exit successfully")
        bindings = {**receipt["inputs"], **receipt["sources"],
            inventory_file.relative_to(ROOT).as_posix(): digest(inventory_file),
            receipt_file.relative_to(ROOT).as_posix(): digest(receipt_file),
            HELPER.relative_to(ROOT).as_posix(): HELPER_SHA,
            Path(__file__).with_name("replay_contract.json").relative_to(ROOT).as_posix(): record["replay_contract_sha256"],
            Path(__file__).relative_to(ROOT).as_posix(): digest(Path(__file__)),
            **{(stage/name).relative_to(ROOT).as_posix(): pin for name, pin in FORMAL_PINS.items()},
            **audit["input_bindings"]}
        for name, pin in bindings.items():
            require(digest(ROOT/name) == pin, "Public input/source differs: "+name)
        for name, pin in receipt["sources"].items():
            capsule = stage/"sources"/Path(name).name
            require(digest(capsule) == pin, "Saved source capsule differs: "+name)
            bindings[capsule.relative_to(ROOT).as_posix()] = pin
        for name, pin in audit["source_bindings"].items():
            capsule = audit_root/"sources"/Path(name).name
            require(digest(capsule) == pin, "Independent source capsule differs: "+name)
            bindings[capsule.relative_to(ROOT).as_posix()] = pin

        def bind_references(value):
            if isinstance(value, dict):
                if "path" in value and "sha256" in value:
                    file = (audit_root/value["path"]).resolve()
                    require(file.is_relative_to(audit_root.resolve()), "Reference payload must remain inside its audit directory")
                    require(digest(file) == value["sha256"], "Saved reference payload differs: "+value["path"])
                    bindings[file.relative_to(ROOT).as_posix()] = value["sha256"]
                for part in value.values():
                    bind_references(part)
            elif isinstance(value, list):
                for part in value:
                    bind_references(part)
        bind_references(audit["states"])
        sample()
        command = [sys.executable, "-B", str(ROOT/"hf_repo/scripts/solve_native_mean.py"),
            "--geometry", str(ROOT/case["geometry_file"]), "--task", str(ROOT/case["task_file"]),
            "--output", str(output/"result"), "--time-limit", "1500",
            "--targets", "0", ".005", ".010", ".025", "--minimum-increment", "6.25e-5"]
        record.update(command=command, input_source_bindings=bindings, expected_call_counts=counts,
            expected_accepted_states=nstates, expected_payload_arrays=23+27*nstates, expected_payload_files=4+4*nstates, declared_targets_mm=TARGETS,
            independent_audit_sha256=FORMAL_PINS["audit/summary.json"],
            scientific_reference_replayed=False, new_HP_calls=0)
        with (output/"cli.log").open("x", encoding="utf-8") as log:
            child = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
            record["invocations"] = 1
            while child.poll() is None:
                sample()
                sleep(.05)
        sample()
        record["cli_returncode"] = child.returncode
        record["decision_member_observations"] = observe_members()
        observe_saved_result()
        require(child.returncode == 0, "Public native fine mean CLI returned nonzero")
        actual = output/"result"
        right = read(actual/"result.json")
        verify_descriptor(right)
        require(right["call_counts"] == counts and right["accepted_states"] == nstates and len(right["states"]) == nstates,
            "Recovered call counts/accepted count differ")
        record.update(force_calls=right["call_counts"]["force_calls"], tangent_calls=right["call_counts"]["tangent_calls"],
            solver_calls=right["call_counts"]["solver_invocations"], call_counts=right["call_counts"],
            state_sha256=[row["state_sha256"] for row in right["states"]], actual_targets_mm=[row["d"] for row in right["states"]])
        compare_file("model/model.json", expected/"model/model.json", actual/"model/model.json")
        compare_file("model/model.npz", expected/"model/model.npz", actual/"model/model.npz", 23)
        model_meta = read(expected/"model/model.json")
        require(model_meta["task"]["case_family"] == "gripper", "Recovered ordinary model must be gripper")
        for source_path in model_meta["source_geometry"]["snapshot"].values():
            name = "model/"+source_path
            compare_file(name, expected/name, actual/name)
        for original, restored in zip(original_states, right["states"], strict=True):
            for name, count in (("state", 2), ("forces", 17), ("tangents", 3), ("matrix", 5)):
                relative = original[name]["path"]
                require(relative == restored[name]["path"], "Recovered accepted payload path differs")
                compare_file(relative, expected/relative, actual/relative, count)
                for base, row in ((expected, original), (actual, restored)):
                    require(digest(base/relative) == row[name]["sha256"], "Accepted payload declaration differs")
            pair = []
            for base, row in ((expected, original), (actual, restored)):
                state_file = base/row["descriptor_path"]
                require(digest(state_file) == row["descriptor_file_sha256"], "Accepted JSON file hash differs")
                value = read(state_file)
                verify_descriptor(value)
                recursive_equal(value, {key: part for key, part in row.items()
                    if key not in ("descriptor_path", "descriptor_file_sha256")})
                pair.append(value)
            recursive_equal(normalized_state(pair[0]), normalized_state(pair[1]))
            record["equal_JSONs"].append(dict(path=original["descriptor_path"], comparison="Frozen explicit state time/hash exclusions only"))
            sample()
        require(record["equal_arrays"] == 23+27*nstates == record["expected_payload_arrays"] and len(record["equal_files"]) == 4+4*nstates == record["expected_payload_files"],
            "Full model/accepted payload coverage differs")
        recursive_equal(normalized_result(left), normalized_result(right))
        record["equal_JSONs"].append(dict(path="result.json", comparison="Frozen explicit measured time/consequent hash exclusions only"))
        record["physical_states"] = [{key: row[key] for key in ("d", "q_in", "q_out", "R_input", "minimum_J",
            "relative_residual", "constraint_residual", "relative_global_force_balance", "state_sha256")} for row in right["states"]]
        for name, pin in bindings.items():
            require(digest(ROOT/name) == pin, "Public source/input changed during recovery: "+name)
        record.update(status="pass", result_sha256=digest(actual/"result.json"), official_result_sha256=digest(expected/"result.json"),
            cli_log_sha256=digest(output/"cli.log"), state_payloads_byte_equal=True, whole_result_JSON_byte_equality_claimed=False)
        sample()
    except Exception as error:
        record.update(status="fail", error=repr(error))
        if child is not None:
            record["cli_returncode"] = child.poll()
            record["error_member_observations"] = observe_members()
            record["cleanup_attempts"] = []
            try:
                process = psutil.Process(child.pid)
                members = list({p.pid: p for p in [*members, process, *process.children(recursive=True)] if p.is_running()}.values())
            except psutil.Error as cleanup_error:
                record["cleanup_discovery_error"] = repr(cleanup_error)
            for member in reversed(members):
                attempt = dict(pid=member.pid, action="terminate_observed_member")
                record["cleanup_attempts"].append(attempt)
                if member.pid == child.pid and record["cli_returncode"] is not None:
                    attempt["action"] = "skip_root_with_true_exit_code"
                    continue
                try:
                    member.terminate()
                except psutil.Error as cleanup_error:
                    attempt["error"] = repr(cleanup_error)
            try:
                _, remaining = psutil.wait_procs(members, timeout=10)
                record["cleanup_remaining_observed_pids"] = [member.pid for member in remaining]
            except psutil.Error as cleanup_error:
                record.update(cleanup_wait_error=repr(cleanup_error), cleanup_remaining_observed_pids=None)
            record["cleanup_scope"] = "Observed identity-checked members only; no complete descendant termination proof"
        raise
    finally:
        if child is not None:
            record["cli_returncode"] = child.poll()
        observe_saved_result()
        record.update(elapsed_seconds=perf_counter()-STARTED, peak_sampled_child_tree_RSS_bytes=peak_child,
            peak_sampled_wrapper_and_child_tree_RSS_bytes=peak_total,
            peak_sampled_CLI_root_PID_RSS_bytes=peak_root_pid,
            Windows_CLI_root_PID_peak_working_set_bytes=peak_root_pid_os or None)
        receipt_path = output/"replay_receipt.json"
        with receipt_path.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(record, stream, indent=2, allow_nan=False)
            stream.write("\n")
        try:
            sample()
        except Exception as error:
            record.update(status="fail", final_budget_error=repr(error), elapsed_seconds=perf_counter()-STARTED)
            receipt_path.write_text(json.dumps(record, indent=2, allow_nan=False)+"\n", encoding="utf-8")
            raise
    print(json.dumps({key: record[key] for key in ("status", "equal_arrays", "force_calls", "tangent_calls", "solver_calls",
        "elapsed_seconds", "peak_sampled_child_tree_RSS_bytes")}))


if __name__ == "__main__":
    main()
