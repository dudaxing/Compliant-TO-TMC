"""One ordinary-file native mean CLI recovery; no new HP or LF import.

All saved numeric payloads are compared byte for byte. JSON comparison removes
only explicitly listed measured times and their consequent descriptor hashes;
call counts, solver diagnostics and every physical value remain compared.
This same-machine replay does not provide new scientific qualification.
"""
import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from time import perf_counter, sleep

STARTED = perf_counter()
import numpy as np
import psutil

ROOT = Path(__file__).resolve().parents[2]
LIMIT, RSS_LIMIT = 180., 8*1024**3
PATH_TIMES = ("kernel_and_transfer", "assembly", "sparse_solve", "callback", "all_assembly_attempts_wall", "total")
EXPECTED_COUNTS = dict(force_calls=4, force_calls_completed=4, tangent_calls=3,
    tangent_calls_completed=3, solver_invocations=1, JIT_calls=0, HP_calls=0)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_hash(value):
    def normalize(item):
        if isinstance(item, dict):
            return {key: normalize(part) for key, part in item.items()}
        if isinstance(item, list):
            return [normalize(part) for part in item]
        if isinstance(item, float):
            require(np.isfinite(item), "Nonfinite descriptor")
            return (0. if item == 0. else item).hex()
        return item
    raw = json.dumps(normalize(value), sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False).encode("utf-8")
    return sha256(raw).hexdigest()


def verify_descriptor(value):
    require(value["descriptor_sha256"] == canonical_hash({key: part for key, part in value.items()
        if key != "descriptor_sha256"}), "Descriptor semantic hash differs")


def normalized_state(value, *, flat=False):
    result = deepcopy(value)
    del result["elapsed_seconds"]
    del result["descriptor_sha256"]
    if flat:
        del result["descriptor_file_sha256"]
    return result


def normalized_result(value):
    result = deepcopy(value)
    require(set(result["timing_seconds"]) == {"project_preparation", "evaluation"}, "Unexpected top timing fields")
    del result["timing_seconds"]
    del result["descriptor_sha256"]
    times = result["path_diagnostics"]["timing_seconds"]
    require(set(times) == set(PATH_TIMES)|{"kernel_calls", "successful_kernel_calls"}, "Unexpected path timing fields")
    for key in PATH_TIMES:
        del times[key]
    result["states"] = [normalized_state(row, flat=True) for row in result["states"]]
    return result


def recursive_equal(left, right, path=""):
    """All retained types and scalar values, including binary64 signed zero."""
    require(type(left) is type(right), "Metadata type differs: "+path)
    if isinstance(left, dict):
        require(left.keys() == right.keys(), "Metadata fields differ: "+path)
        for key in left:
            recursive_equal(left[key], right[key], path+"/"+key)
    elif isinstance(left, list):
        require(len(left) == len(right), "Metadata length differs: "+path)
        for index, (a, b) in enumerate(zip(left, right, strict=True)):
            recursive_equal(a, b, path+"/"+str(index))
    elif isinstance(left, float):
        require(left.hex() == right.hex(), "Metadata float differs: "+path)
    else:
        require(left == right, "Metadata value differs: "+path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New directory outside the clone")
    args = parser.parse_args()
    output = args.output.resolve()
    require(not output.is_relative_to(ROOT), "Replay output must be outside the public clone")
    output.mkdir(parents=True, exist_ok=False)
    stage = ROOT/"lf_data_preparation/native_mean_001"
    inventory_file, receipt_file = stage/"input_inventory.json", stage/"execution_receipt.json"
    record = dict(schema_version="native-mean-public-replay-1.0", status="running",
        scope="One same-machine independent-directory CLI recovery; no new scientific qualification",
        invocations=0, force_calls=None, tangent_calls=None, solver_calls=None, HP_calls=0, JIT_calls=0, LF_imports=0,
        seconds_limit=LIMIT, sampled_RSS_limit_bytes=RSS_LIMIT, outer_timeout_required_seconds=210,
        counter_semantics="Returned saved API counters; unavailable if CLI has not returned a result",
        equal_files=[], equal_arrays=0, equal_JSONs=[],
        JSON_exclusions=dict(result=["timing_seconds.project_preparation", "timing_seconds.evaluation", "descriptor_sha256"],
            path_diagnostics=["timing_seconds."+key for key in PATH_TIMES],
            state=["elapsed_seconds", "descriptor_sha256"], flat_state=["descriptor_file_sha256"]),
        retained_time_settings=True, retained_kernel_call_counts=True,
        payload_comparison="Exact NPZ file bytes and every array dtype, shape and C-order bytes; original source file bytes",
        metadata_comparison="Recursive exact types/values after explicit time/consequent-hash exclusions; JSON whole-file equality is not claimed")
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
        require(perf_counter()-STARTED <= LIMIT, "Public mean replay elapsed budget exceeded")
        require(peak_total <= RSS_LIMIT, "Public mean replay sampled process-tree RSS exceeded 8 GiB")

    def compare_file(relative, expected, actual, *, arrays=False):
        sample()
        pin = digest(expected)
        require(digest(actual) == pin, "Public payload byte mismatch: "+relative)
        record["equal_files"].append(dict(path=relative, sha256=pin))
        if arrays:
            record["equal_files"][-1]["arrays"] = []
            with np.load(expected, allow_pickle=False) as left, np.load(actual, allow_pickle=False) as right:
                require(set(left.files) == set(right.files), "Public NPZ fields differ: "+relative)
                for name in left.files:
                    a, b = left[name], right[name]
                    require(a.dtype == b.dtype and a.shape == b.shape and a.tobytes(order="C") == b.tobytes(order="C"),
                        "Public raw array differs: "+relative+"/"+name)
                    record["equal_files"][-1]["arrays"].append(dict(name=name, dtype=a.dtype.name,
                        shape=list(a.shape), sha256=sha256(a.tobytes(order="C")).hexdigest()))
                    record["equal_arrays"] += 1
        sample()

    try:
        sample()
        inventory, receipt = read(inventory_file), read(receipt_file)
        case = inventory["case"]
        require(inventory["schema_version"] == "native-mean-input-inventory-1.0"
            and case["alias"] == "gripper_canonical" and case["targets_mm"] == [0., .001]
            and receipt["status"] == "pass" and receipt["invocations"] == 1
            and receipt["call_counts"] == EXPECTED_COUNTS and receipt["accepted_states"] == 2
            and receipt["input_inventory_sha256"] == digest(inventory_file), "Saved native mean scope differs")
        settings = inventory["settings"]
        require(settings == dict(tolerance=1e-9, constraint_tolerance=1e-10, displacement_scale_floor=1e-6,
            force_scale_floor_factor=1e-8, max_checks=25, armijo_c=1e-4, max_backtracks=12,
            max_bisections=4, minimum_increment=.001/16, time_limit_seconds=180.), "Official settings changed")
        bindings = {**receipt["inputs"], **receipt["sources"],
            inventory_file.relative_to(ROOT).as_posix(): digest(inventory_file),
            receipt_file.relative_to(ROOT).as_posix(): digest(receipt_file)}
        for name, pin in bindings.items():
            require(digest(ROOT/name) == pin, "Public input/source differs: "+name)
        for name, pin in receipt["sources"].items():
            require(digest(stage/"sources"/Path(name).name) == pin, "Saved source capsule differs: "+name)
        expected = stage/case["result_directory"]
        require(digest(expected/"result.json") == receipt["result_sha256"], "Saved official result differs")
        command = [sys.executable, "-B", str(ROOT/"hf_repo/scripts/solve_native_mean.py"),
            "--geometry", str(ROOT/case["geometry_file"]), "--task", str(ROOT/case["task_file"]),
            "--output", str(output/"result"), "--time-limit", "180"]
        record.update(command=command, input_source_bindings=bindings,
            replay_helper_sha256=digest(Path(__file__)))
        with (output/"cli.log").open("x", encoding="utf-8") as log:
            child = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
            record["invocations"] = 1
            while child.poll() is None:
                sample()
                sleep(.05)
        sample()
        require(child.returncode == 0, "Public native mean CLI failed")
        actual = output/"result"
        left, right = (read(path/"result.json") for path in (expected, actual))
        for value in (left, right):
            verify_descriptor(value)
            require(value["call_counts"] == EXPECTED_COUNTS and value["status"] == "success"
                and value["target_reached"] is True and value["task_target_executed"] is True
                and value["save_force_calls"] == value["save_tangent_calls"] == 0
                and [row["d"] for row in value["states"]] == [0., .001]
                and value["accepted_states"] == 2, "Recovered path/call counts differ")
        record.update(force_calls=right["call_counts"]["force_calls"], tangent_calls=right["call_counts"]["tangent_calls"],
            solver_calls=right["call_counts"]["solver_invocations"], call_counts=right["call_counts"],
            state_sha256=[row["state_sha256"] for row in right["states"]], actual_targets_mm=[row["d"] for row in right["states"]])
        compare_file("model/model.json", expected/"model/model.json", actual/"model/model.json")
        compare_file("model/model.npz", expected/"model/model.npz", actual/"model/model.npz", arrays=True)
        model_metadata = read(expected/"model/model.json")
        for source_path in model_metadata["source_geometry"]["snapshot"].values():
            name = "model/"+source_path
            compare_file(name, expected/name, actual/name)
        for index, (original, restored) in enumerate(zip(left["states"], right["states"], strict=True)):
            for name in ("state", "forces", "tangents", "matrix"):
                relative = original[name]["path"]
                require(relative == restored[name]["path"], "Recovered accepted payload path differs")
                compare_file(relative, expected/relative, actual/relative, arrays=True)
                for base, row in ((expected, original), (actual, restored)):
                    require(digest(base/relative) == row[name]["sha256"], "Accepted payload declaration differs")
            originals = []
            for base, row in ((expected, original), (actual, restored)):
                state_file = base/row["descriptor_path"]
                require(digest(state_file) == row["descriptor_file_sha256"], "Accepted JSON file hash differs")
                value = read(state_file)
                verify_descriptor(value)
                recursive_equal(value, {key: part for key, part in row.items()
                    if key not in ("descriptor_path", "descriptor_file_sha256")})
                originals.append(value)
            recursive_equal(normalized_state(originals[0]), normalized_state(originals[1]))
            record["equal_JSONs"].append(dict(path=original["descriptor_path"], comparison="Only measured elapsed and consequent semantic hash excluded"))
            sample()
        require(record["equal_arrays"] == 77, "Expected 23 model and two full 27-array accepted payloads")
        recursive_equal(normalized_result(left), normalized_result(right))
        record["equal_JSONs"].append(dict(path="result.json", comparison="Only explicit measured times and their consequent descriptor hashes excluded"))
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
