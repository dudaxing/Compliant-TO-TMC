"""One ordinary-file inverter mean CLI recovery with the frozen JSON rules.

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

LIMIT, RSS_LIMIT = 180., 8*1024**3
SETTINGS = dict(tolerance=1e-9, constraint_tolerance=1e-10, displacement_scale_floor=1e-6,
    force_scale_floor_factor=1e-8, max_checks=25, armijo_c=1e-4, max_backtracks=12,
    max_bisections=4, minimum_increment=.001/16, time_limit_seconds=180.)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New directory outside the clone")
    args = parser.parse_args()
    output = args.output.resolve()
    require(not output.is_relative_to(ROOT), "Replay output must be outside the public clone")
    output.mkdir(parents=True, exist_ok=False)
    stage = ROOT/"lf_data_preparation/native_inverter_mean_001"
    inventory_file, receipt_file = stage/"input_inventory.json", stage/"execution_receipt.json"
    record = dict(schema_version="native-inverter-mean-public-replay-1.0", status="running",
        scope="One same-machine independent-directory CLI recovery; no new scientific qualification",
        invocations=0, force_calls=None, tangent_calls=None, solver_calls=None, HP_calls=0, JIT_calls=0, LF_imports=0,
        seconds_limit=LIMIT, sampled_RSS_limit_bytes=RSS_LIMIT, outer_timeout_required_seconds=210,
        counter_semantics="Returned saved API counters; unavailable if CLI has not returned a result",
        equal_files=[], equal_arrays=0, equal_JSONs=[],
        JSON_exclusions=dict(result=["timing_seconds.project_preparation", "timing_seconds.evaluation", "descriptor_sha256"],
            path_diagnostics=["timing_seconds."+key for key in contract.PATH_TIMES],
            state=["elapsed_seconds", "descriptor_sha256"], flat_state=["descriptor_file_sha256"]),
        retained_time_settings=True, retained_kernel_call_counts=True,
        payload_comparison="Exact NPZ file bytes and every array dtype, shape and C-order bytes; original source file bytes",
        metadata_comparison="Frozen normalizers: explicit measured times/consequent hashes excluded; every other field recursively exact",
        comparison_helper_sha256=HELPER_SHA)
    peak_child = peak_total = 0
    owner, child, members = psutil.Process(), None, []

    def sample():
        nonlocal peak_child, peak_total, members
        current = []
        if child is not None and child.poll() is None:
            try:
                process = psutil.Process(child.pid)
                current = [process]+process.children(recursive=True)
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
        inventory, receipt = read(inventory_file), read(receipt_file)
        case = inventory["case"]
        require(inventory["schema_version"] == "native-mean-input-inventory-1.0"
            and case["alias"] == "inverter_canonical" and case["targets_mm"] == [0., .001]
            and (case["fixed_DOFs"], case["free_DOFs"]) == (89, 6553)
            and inventory["settings"] == SETTINGS and receipt["status"] == "pass" and receipt["invocations"] == 1
            and receipt["input_inventory_sha256"] == digest(inventory_file)
            and receipt["HP_calls"] == receipt["JIT_calls"] == receipt["LF_imports"] == 0
            and receipt["solver_calls"] == 1 and len(receipt["sources"]) == 37, "Saved inverter mean scope differs")
        expected = stage/case["result_directory"]
        require(digest(expected/"result.json") == receipt["result_sha256"], "Saved official result differs")
        left = read(expected/"result.json")
        verify_descriptor(left)
        counts, original_states = left["call_counts"], left["states"]
        nstates = len(original_states)
        require(left["schema_version"] == "hf-native-mean-result-1.0" and left["status"] == "success"
            and left["target_reached"] is True and left["task_target_executed"] is True
            and left["targets_mm"] == case["targets_mm"] and left["settings"] == SETTINGS
            and left["task_target_mm"] == .001 and left["k_out_N_per_mm"] == 0.
            and left["save_force_calls"] == left["save_tangent_calls"] == 0
            and left["equilibrium_qualified"] is left["independent_HP_qualified"] is left["HF_qualified"] is False
            and nstates >= 2 and left["accepted_states"] == receipt["accepted_states"] == nstates
            and [row["d"] for row in original_states if row["is_original_target"]] == case["targets_mm"]
            and original_states[0]["d"] == 0. and original_states[-1]["d"] == .001
            and all(a["d"] < b["d"] for a, b in zip(original_states, original_states[1:])), "Formal accepted path differs")
        require(counts == receipt["call_counts"] and counts["force_calls"] == counts["force_calls_completed"]
            and counts["tangent_calls"] == counts["tangent_calls_completed"] >= nstates
            and counts["force_calls"] >= counts["tangent_calls"] and counts["solver_invocations"] == 1
            and counts["HP_calls"] == counts["JIT_calls"] == 0
            and receipt["force_calls"] == counts["force_calls"] and receipt["tangent_calls"] == counts["tangent_calls"]
            and receipt["state_sha256"] == [row["state_sha256"] for row in original_states], "Formal counters/state identity differ")
        bindings = {**receipt["inputs"], **receipt["sources"],
            inventory_file.relative_to(ROOT).as_posix(): digest(inventory_file),
            receipt_file.relative_to(ROOT).as_posix(): digest(receipt_file),
            HELPER.relative_to(ROOT).as_posix(): HELPER_SHA,
            Path(__file__).relative_to(ROOT).as_posix(): digest(Path(__file__))}
        for name, pin in bindings.items():
            require(digest(ROOT/name) == pin, "Public input/source differs: "+name)
        for name, pin in receipt["sources"].items():
            capsule = stage/"sources"/Path(name).name
            require(digest(capsule) == pin, "Saved source capsule differs: "+name)
            bindings[capsule.relative_to(ROOT).as_posix()] = pin
        command = [sys.executable, "-B", str(ROOT/"hf_repo/scripts/solve_native_mean.py"),
            "--geometry", str(ROOT/case["geometry_file"]), "--task", str(ROOT/case["task_file"]),
            "--output", str(output/"result"), "--time-limit", "180"]
        record.update(command=command, input_source_bindings=bindings, expected_call_counts=counts,
            expected_accepted_states=nstates, expected_payload_arrays=23+27*nstates)
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
            peak_sampled_wrapper_and_child_tree_RSS_bytes=peak_total)
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
