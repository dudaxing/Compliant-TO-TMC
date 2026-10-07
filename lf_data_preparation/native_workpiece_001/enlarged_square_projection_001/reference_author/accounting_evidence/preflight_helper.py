"""Read a terminal complete production only and run the frozen pure saved-data counter."""
from pathlib import Path
from hashlib import sha256
from time import perf_counter
from collections import Counter
import importlib.util
import json

STARTED = perf_counter()
REPO = Path("D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC")
CONTROL = REPO/"lf_data_preparation/native_workpiece_001/enlarged_square_projection_001"
STAGE = CONTROL/"run_001"
COUNTER_FILE = Path("D:/hf-workpiece-enlarge-author-20261007/projection_reference_candidate/counter_attempts.py")
COUNTER_PIN = "b028dba774d430a6d082ca05be86489a56e800be1f1bd69c60148ffccd51e8b3"
OUTPUT = Path("D:/hf-workpiece-enlarge-author-20261007/b028_saved_preflight_001")
read = lambda path:json.loads(path.read_text(encoding="utf-8"))
digest = lambda path:sha256(path.read_bytes()).hexdigest()


def write(path,value):
    with path.open("x",encoding="utf-8") as handle:
        json.dump(value,handle,ensure_ascii=False,indent=2,allow_nan=False)
        handle.write("\n")


def main():
    # No running/partial saved trace is inspected. Final outer and helper gates come first.
    launch_file,protocol_file = CONTROL/"production_launch.json",CONTROL/"production_protocol.json"
    launch = read(launch_file)
    assert launch["status"] == "pass" and launch["exit_code"] == 0 and launch["invocations"] == 1
    assert launch["stop_reason"] is None and launch["all_bindings_unchanged"] is True
    protocol = read(protocol_file)
    assert launch["protocol_sha256"] == digest(protocol_file) and launch["bindings"] == protocol["bindings"]
    receipt_file = STAGE/"execution_receipt.json"
    receipt = read(receipt_file)
    assert receipt["status"] == "pass" and receipt["invocations"] == 1 and receipt["sources_unchanged"] and receipt["inputs_unchanged"]
    inventory_file,freeze_file = STAGE/"input_inventory.json",STAGE/"source_freeze.json"
    inventory,freeze = read(inventory_file),read(freeze_file)
    assert receipt["input_inventory_sha256"] == digest(inventory_file)
    assert receipt["source_freeze_sha256"] == inventory["source_freeze_sha256"] == digest(freeze_file)
    assert receipt["sources"] == freeze["sources"] and receipt["inputs"] == inventory["input_bindings"]
    result_file = STAGE/inventory["case"]["result_directory"]/"result.json"
    assert receipt["result_sha256"] == digest(result_file)
    result = read(result_file)
    assert result["status"] == "success" and result["failure"] is None
    assert all(result[name] is True for name in ("production_converged","target_reached","path_completed",
        "loading_peak_reached","unload_endpoint_reached","task_target_executed"))
    assert result["targets_mm"] == inventory["case"]["targets_mm"]
    assert result["accepted_states"] == receipt["accepted_states"] == len(result["states"])
    assert result["settings"] == inventory["settings"] and result["call_counts"] == receipt["call_counts"]
    assert [row["d"] for row in result["states"] if row["is_original_target"]] == result["targets_mm"]
    assert result["states"][0]["d"] == result["states"][-1]["d"] == 0.
    pins = dict(protocol["bindings"])
    pins.update(receipt["sources"]);pins.update(receipt["inputs"])
    pins.update({file.relative_to(REPO).as_posix():digest(file) for file in
        (launch_file,protocol_file,receipt_file,inventory_file,freeze_file,result_file)})
    assert all(digest(REPO/name) == pin for name,pin in pins.items())
    assert all(digest(STAGE/"sources"/Path(name).name) == pin for name,pin in receipt["sources"].items())
    assert digest(COUNTER_FILE) == COUNTER_PIN
    assert not OUTPUT.exists()
    OUTPUT.mkdir()
    spec = importlib.util.spec_from_file_location("frozen_B028_saved_data_only",COUNTER_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # B028 imports math.isfinite and defines pure chronology logic only.
    checks = 0

    def check(condition,message):
        nonlocal checks
        checks += 1
        if not condition:
            raise AssertionError(message)

    report = dict(scope="Terminal full-pass saved-data accounting only; no numerical mechanics or reference qualification.",
        source_file=str(COUNTER_FILE),source_sha256=COUNTER_PIN,
        production_stage=STAGE.relative_to(REPO).as_posix(),accepted_states=result["accepted_states"],
        result_sha256=digest(result_file),receipt_sha256=digest(receipt_file),production_launch_sha256=digest(launch_file),
        production_protocol_sha256=digest(protocol_file),source_freeze_sha256=digest(freeze_file),
        input_bindings=pins,force_trial_reasons=dict(Counter(row.get("reason","accepted") for row in result["path_diagnostics"]["trials"])),
        failed_attempt_codes=dict(Counter(row["code"] for row in result["path_diagnostics"]["failed_attempts"])),
        calls=dict(new_force=0,new_tangent=0,new_solver=0,new_HP=0,new_model=0,geometry_API=0,render=0))
    try:
        accounting = module.reconstruct(result,receipt,inventory["settings"],check)
        write(OUTPUT/"accounting.json",accounting)
        report.update(status="saved_accounting_pass",counter_adapter_required=False,
            accounting_sha256=digest(OUTPUT/"accounting.json"),checks_completed=checks)
    except AssertionError as error:
        report.update(status="saved_accounting_unsupported",error=str(error),checks_completed=checks,
            counter_adapter_required="Review actual trace before any candidate adapter or reference freeze.")
    report.update(elapsed_seconds=perf_counter()-STARTED,
        all_bindings_unchanged=all(digest(REPO/name) == pin for name,pin in pins.items()),
        source_unchanged=digest(COUNTER_FILE) == COUNTER_PIN)
    assert report["all_bindings_unchanged"] and report["source_unchanged"]
    write(OUTPUT/"report.json",report)
    print(json.dumps({name:report[name] for name in ("status","accepted_states","force_trial_reasons",
        "failed_attempt_codes","checks_completed","counter_adapter_required","elapsed_seconds")}))


if __name__ == "__main__":
    main()
