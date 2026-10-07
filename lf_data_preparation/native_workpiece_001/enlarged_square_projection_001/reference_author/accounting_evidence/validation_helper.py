"""Pure JSON chronology reproduction of the actual completed path and retained baselines."""
from pathlib import Path
from hashlib import sha256
from time import perf_counter
from copy import deepcopy
import importlib.util
import json

STARTED = perf_counter()
REPO = Path("D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC")
AUTHOR = Path(__file__).resolve().parent
OUTPUT = AUTHOR/"saved_reproduction_001"
CURRENT = REPO/"lf_data_preparation/native_workpiece_001/enlarged_square_projection_001/run_001"
OLD_PIN = "b028dba774d430a6d082ca05be86489a56e800be1f1bd69c60148ffccd51e8b3"
digest = lambda path:sha256(path.read_bytes()).hexdigest()
read = lambda path:json.loads(path.read_text(encoding="utf-8"))


def write(path,value):
    with path.open("x",encoding="utf-8") as handle:
        json.dump(value,handle,ensure_ascii=False,indent=2,allow_nan=False);handle.write("\n")


def counter(path):
    spec = importlib.util.spec_from_file_location(path.stem+"_pure_saved",path)
    module = importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.reconstruct


def reconstruct(function,result,receipt):
    checks = 0
    def check(condition,message):
        nonlocal checks
        checks += 1
        if not condition: raise AssertionError(message)
    return function(result,receipt,result["settings"],check),checks


def main():
    preflight_file = AUTHOR.parent/"b028_saved_preflight_001/report.json"
    preflight = read(preflight_file)
    assert preflight["status"] == "saved_accounting_unsupported" and preflight["source_sha256"] == OLD_PIN
    pins = dict(preflight["input_bindings"])
    assert all(digest(REPO/name) == pin for name,pin in pins.items())
    assert digest(AUTHOR/"counter_original_B028.py") == OLD_PIN
    launch = read(CURRENT.parent/"production_launch.json")
    receipt = read(CURRENT/"execution_receipt.json");result = read(CURRENT/"result/result.json")
    assert launch["status"] == receipt["status"] == "pass" and result["status"] == "success"
    assert launch["all_bindings_unchanged"] and result["path_completed"] and result["unload_endpoint_reached"]
    assert result["accepted_states"] == len(result["states"]) == 24 and result["failure"] is None
    trials,history = result["path_diagnostics"]["trials"],result["path_diagnostics"]["newton_history"]
    assert not result["path_diagnostics"]["failed_attempts"]
    invalid = [(index,row) for index,row in enumerate(trials) if row.get("reason") == "invalid_J"]
    range_rows = [(index,row) for index,row in enumerate(trials) if row.get("reason") == "unsupported_arithmetic_range"]
    assert len(invalid) == 14 and len(range_rows) == 10
    incomplete_fields = {"target_displacement","stage_parameter","newton_check","factor","fixed_residual_scale","base_phi","accepted","reason"}
    for index,row in invalid:
        assert set(row) == incomplete_fields and row["accepted"] is False and index+1 < len(trials)
        following = trials[index+1]
        assert (following["stage_parameter"],following["newton_check"],following["factor"],following["fixed_residual_scale"],following["base_phi"]) == (
            row["stage_parameter"],row["newton_check"],row["factor"]/2,row["fixed_residual_scale"],row["base_phi"])
    completed_trials = [row for row in trials if row.get("reason") not in ("invalid_J","unsupported_arithmetic_range")]
    independent_counts = dict(force_calls=len(history)+len(trials),force_calls_completed=len(history)+len(completed_trials),
        tangent_calls=len(history),tangent_calls_completed=len(history),solver_invocations=1,JIT_calls=0,HP_calls=0)
    assert independent_counts == result["call_counts"] == receipt["call_counts"]
    assert (len(history),len(trials),len(completed_trials)) == (176,178,154)
    assert len(result["path_diagnostics"]["linear_solve_diagnostics"]) == len(history)-1 == 175
    assert not OUTPUT.exists();OUTPUT.mkdir()
    old,new = counter(AUTHOR/"counter_original_B028.py"),counter(AUTHOR/"counter_attempts.py")
    accounting,checks = reconstruct(new,result,receipt)
    assert accounting["counts"] == independent_counts
    assert [row["trial_index"] for row in accounting["rejected_invalid_J_trials"]] == [index for index,row in invalid]
    assert [row["trial_index"] for row in accounting["rejected_range_trials"]] == [index for index,row in range_rows]
    assert not accounting["predictor_invalid_J_bases"] and not accounting["failed_tangent_base"]
    assert len(accounting["accepted_completed_caches"]) == 24 and len(accounting["reconstructed_force_events"]) == 354
    assert accounting["rejected_range_trials"][0]["force_call"] == receipt["first_force_range_input"]["force_call_ordinal"] == 325
    write(OUTPUT/"current_accounting.json",accounting)
    regressions = []
    for label,stage in (("pose002",REPO/"lf_data_preparation/native_workpiece_001/shift_square_pose_002/run_001"),
                        ("soft001",REPO/"lf_data_preparation/native_workpiece_001/shift_square_soft_001/run_001"),
                        ("original010",REPO/"lf_data_preparation/native_workpiece_001/coarse_square_cycle_010")):
        result_file,receipt_file = stage/"result/result.json",stage/"execution_receipt.json"
        saved,saved_receipt = read(result_file),read(receipt_file)
        pins.update({path.relative_to(REPO).as_posix():digest(path) for path in (result_file,receipt_file)})
        previous,old_checks = reconstruct(old,saved,saved_receipt)
        candidate,new_checks = reconstruct(new,saved,saved_receipt)
        assert candidate.pop("rejected_invalid_J_trials") == [] and candidate == previous
        regressions.append(dict(label=label,result_sha256=digest(result_file),receipt_sha256=digest(receipt_file),
            status="exact_original_output_after_removing_only_empty_new_field",old_checks=old_checks,new_checks=new_checks,
            accepted_states=saved["accepted_states"]))
    rejections = []
    for name,mutate in (("fake_completed_invalid_J",lambda value:value["path_diagnostics"]["trials"][invalid[0][0]].update(phi=0.)),
                       ("wrong_half_factor",lambda value:value["path_diagnostics"]["trials"][invalid[0][0]+1].update(factor=.3))):
        changed = deepcopy(result);mutate(changed)
        try: reconstruct(new,changed,receipt)
        except AssertionError as error: rejections.append(dict(case=name,status="rejected",message=str(error)))
        else: raise AssertionError("Tampered saved chronology was incorrectly accepted: "+name)
    report = dict(status="saved_only_reproduction_pass",checks_completed=checks,
        preflight_file=str(preflight_file),preflight_sha256=digest(preflight_file),
        source_transition=dict(path="counter_attempts.py",previous_sha256=OLD_PIN,current_sha256=digest(AUTHOR/"counter_attempts.py"),
            proof_kind="recovered_invalid_J_saved_accounting"),
        complete_current_states=24,independent_counts=independent_counts,
        actual_recovered_invalid_J_trials=[dict(trial_index=index,**row) for index,row in invalid],
        actual_rejected_range_trials=len(range_rows),first_range_force_ordinal=325,
        current_accounting_sha256=digest(OUTPUT/"current_accounting.json"),regressions=regressions,tampered_chronologies=rejections,
        all_bindings_unchanged=all(digest(REPO/name) == pin for name,pin in pins.items()),input_bindings=pins,
        calls=dict(new_force=0,new_tangent=0,new_solver=0,new_HP=0,new_model=0,geometry_API=0,render=0),
        source_bindings={str(path):digest(path) for path in (AUTHOR/"counter_attempts.py",AUTHOR/"counter_original_B028.py",Path(__file__))},
        elapsed_seconds=perf_counter()-STARTED,
        scope="Saved chronology accounting and explicit rejected-trial labels only; no force/tangent repair, rejected-state qualification or independent physical-state HP qualification.")
    assert report["all_bindings_unchanged"]
    write(OUTPUT/"report.json",report)
    print(json.dumps({name:report[name] for name in ("status","source_transition","complete_current_states","independent_counts","checks_completed","elapsed_seconds")}))


if __name__ == "__main__":
    main()
