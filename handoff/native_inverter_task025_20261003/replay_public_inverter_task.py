"""One four-target ordinary-file inverter TEST recovery with frozen JSON rules.

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

LIMIT, RSS_LIMIT = 300., 8*1024**3
SETTINGS = dict(tolerance=1e-9, constraint_tolerance=1e-10, displacement_scale_floor=1e-6,
    force_scale_floor_factor=1e-8, max_checks=25, armijo_c=1e-4, max_backtracks=12,
    max_bisections=4, minimum_increment=.001/16, time_limit_seconds=300.)

TARGETS = [0., .005, .010, .025]
BASELINE = "163db2508946aea2e3c9948745ff13813ee98d1d"
EXPECTED_COUNTS = dict(force_calls=14, force_calls_completed=14, tangent_calls=9,
    tangent_calls_completed=9, solver_invocations=1, JIT_calls=0, HP_calls=0)
FORMAL_PINS = {
    "input_inventory.json": "b10a445dfe1a87dbd79073b9edc4e9aaa2395425d85ea4d69909da74dadf1af8",
    "execution_receipt.json": "5a5afe4430ba34b57e59b93dd8b1a15c2be6e0bdee5825f77a7bdd56c1a0ac17",
    "production_launch_receipt.json": "25962524aa8fae7d23f31b956ccdb7bf424e47574efc870aa689724026f20531",
    "reference_launch_receipt.json": "5a0027d465a1a7d3291f000dbf6d132966f8912734601f76b44c966c5842cf91",
    "result/result.json": "2fe0ef112bbef1a73bcbc4c48a15cf8e4dd297bc8d25a1a44bb3eb613e2c26aa",
    "audit/summary.json": "4557e32a709fa6b8210176b8e4d6578c476cb4ac6a51e9c6e760f48c6be27327",
    "audit/lifecycle.json": "240170b185448f2b0c773eca6a2b433cab555d8c455f9f7912f5a33f0fa5f49b",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New directory outside the clone")
    args = parser.parse_args()
    output = args.output.resolve()
    require(not output.is_relative_to(ROOT), "Replay output must be outside the public clone")
    output.mkdir(parents=True, exist_ok=False)
    stage = ROOT/"lf_data_preparation/native_inverter_task_025_001"
    inventory_file, receipt_file = stage/"input_inventory.json", stage/"execution_receipt.json"
    record = dict(schema_version="native-inverter-task025-public-replay-1.0", status="running",
        scope="One same-machine independent-directory CLI recovery; no new scientific qualification",
        invocations=0, force_calls=None, tangent_calls=None, solver_calls=None, HP_calls=0, JIT_calls=0, LF_imports=0,
        seconds_limit=LIMIT, sampled_RSS_limit_bytes=RSS_LIMIT, outer_timeout_required_seconds=330,
        budget_mode="Cooperative elapsed/RSS checks and external timeout; not an OS memory hard cap",
        counter_semantics="Returned saved API counters; unavailable if CLI has not returned a result",
        equal_files=[], equal_arrays=0, equal_JSONs=[],
        JSON_exclusions=dict(result=["timing_seconds.project_preparation", "timing_seconds.evaluation", "descriptor_sha256"],
            path_diagnostics=["timing_seconds."+key for key in contract.PATH_TIMES],
            state=["elapsed_seconds", "descriptor_sha256"], flat_state=["descriptor_file_sha256"]),
        retained_time_settings=True, retained_kernel_call_counts=True,
        payload_comparison="Exact NPZ file bytes and every array dtype, shape and C-order bytes; original source file bytes",
        metadata_comparison="Frozen normalizers: explicit measured times/consequent hashes excluded; every other field recursively exact",
        comparison_helper_sha256=HELPER_SHA)
    peak_child = peak_total = peak_production = peak_production_os = 0
    owner, child, members = psutil.Process(), None, []

    def sample():
        nonlocal peak_child, peak_total, peak_production, peak_production_os, members
        current = []
        if child is not None and child.poll() is None:
            try:
                process = psutil.Process(child.pid)
                current = [process]+process.children(recursive=True)
                memory = process.memory_info()
                peak_production = max(peak_production, memory.rss)
                peak_production_os = max(peak_production_os, getattr(memory, "peak_wset", 0))
                members = current
            except psutil.NoSuchProcess:
                pass
        rss = 0
        for member in current:
            try:
                rss += member.memory_info().rss
            except psutil.NoSuchProcess:
                pass
        peak_child, peak_total = max(peak_child, rss), max(peak_total, owner.memory_info().rss+rss)
        require(perf_counter()-STARTED <= LIMIT, "Public inverter mean replay elapsed budget exceeded")
        require(peak_total <= RSS_LIMIT, "Public inverter mean replay sampled tree RSS exceeded 8 GiB")

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
            and case["alias"] == "inverter_canonical" and case["targets_mm"] == TARGETS
            and (case["fixed_DOFs"], case["free_DOFs"]) == (89, 6553)
            and inventory["settings"] == SETTINGS and receipt["status"] == "pass" and receipt["invocations"] == 1
            and receipt["input_inventory_sha256"] == digest(inventory_file)
            and receipt["HP_calls"] == receipt["JIT_calls"] == receipt["LF_imports"] == 0
            and receipt["solver_calls"] == 1 and len(receipt["sources"]) == 39
            and len({Path(name).name for name in receipt["sources"]}) == 39
            and inventory["execution_limits"] == dict(production_seconds=300, reference_seconds=240,
                sampled_RSS_bytes=RSS_LIMIT, production_outer_seconds=330, reference_outer_seconds=270, view_outer_seconds=120),
            "Saved inverter TEST scope differs")
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
            and nstates == 4 and left["accepted_states"] == receipt["accepted_states"] == nstates
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
            and model_meta["task"]["case_family"] == "inverter"
            and model_meta["task"]["input"]["target_mm"] == TARGETS[-1], "Formal model/task identity differs")
        audit_root = stage/"audit"
        audit, lifecycle = read(audit_root/"summary.json"), read(audit_root/"lifecycle.json")
        require(audit["schema_version"] == "native-mean-independent-audit-1.0" and audit["status"] == "pass"
            and audit["alias"] == "inverter_canonical" and audit["case_family"] == "inverter"
            and audit["baseline_commit"] == BASELINE and audit["audited_targets_mm"] == TARGETS
            and audit["task_target_mm"] == TARGETS[-1] and audit["result_sha256"] == receipt["result_sha256"]
            and audit["source_bindings"] == receipt["sources"] and audit["gates"] == inventory["gates"]
            and audit["full_element_and_DOF_coverage"] is True and audit["HP_matrix_columns_exhaustively_checked"] is False
            and audit["accepted_states"] == len(audit["states"]) == nstates
            and audit["HP_calls_started"] == audit["HP_calls_completed"] == 8
            and lifecycle["status"] == "pass" and lifecycle["accepted_states_completed"] == nstates
            and lifecycle["HP_calls_started"] == lifecycle["HP_calls_completed"] == 8, "Formal independent audit is not complete/pass")
        for index, (item, row) in enumerate(zip(audit["states"], original_states, strict=True)):
            require(item["status"] == "pass" and item["index"] == index
                and item["state_sha256"] == row["state_sha256"] and item["target_mm"] == row["d"]
                and item["elements_compared"] == 3200 and item["global_DOFs_compared"] == 6642
                and item["HP_calls"] == 2, "Formal reference state coverage differs")
        for name in ("production_launch_receipt.json", "reference_launch_receipt.json"):
            launch = read(stage/name)
            require(launch["status"] == "pass" and launch["exit_code"] == 0, "Formal stage did not exit successfully")
        bindings = {**receipt["inputs"], **receipt["sources"],
            inventory_file.relative_to(ROOT).as_posix(): digest(inventory_file),
            receipt_file.relative_to(ROOT).as_posix(): digest(receipt_file),
            HELPER.relative_to(ROOT).as_posix(): HELPER_SHA,
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
            "--output", str(output/"result"), "--time-limit", "300",
            "--targets", "0", ".005", ".010", ".025", "--minimum-increment", "6.25e-5"]
        record.update(command=command, input_source_bindings=bindings, expected_call_counts=counts,
            expected_accepted_states=nstates, expected_payload_arrays=131, declared_targets_mm=TARGETS,
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
        require(child.returncode == 0, "Public inverter mean CLI failed")
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
        require(model_meta["task"]["case_family"] == "inverter", "Recovered ordinary model must be inverter")
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
        require(record["equal_arrays"] == 23+27*nstates, "Full model/accepted array coverage differs")
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
        if child is not None and child.poll() is None:
            try:
                process = psutil.Process(child.pid)
                members = [process]+process.children(recursive=True)
            except psutil.NoSuchProcess:
                pass
            for member in reversed(members):
                try:
                    member.terminate()
                except psutil.NoSuchProcess:
                    pass
            _, remaining = psutil.wait_procs(members, timeout=10)
            record["cleanup_remaining_observed_pids"] = [member.pid for member in remaining]
        raise
    finally:
        record.update(elapsed_seconds=perf_counter()-STARTED, peak_sampled_child_tree_RSS_bytes=peak_child,
            peak_sampled_wrapper_and_child_tree_RSS_bytes=peak_total,
            peak_sampled_production_process_RSS_bytes=peak_production,
            Windows_production_process_peak_working_set_bytes=peak_production_os or None)
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
