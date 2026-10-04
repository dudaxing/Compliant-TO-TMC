"""Standalone pure-metadata tests for the complete-attempt counter.

The synthetic prefix is a counter fixture, never a physical shorter task or
an accepted-state qualification. No audit/model/NumPy/HP code is imported.
"""
from time import perf_counter
STARTED = perf_counter()
from pathlib import Path
from hashlib import sha256
from copy import deepcopy
import argparse
import ast
import importlib.util
import json

COUNTER_PIN = "b028dba774d430a6d082ca05be86489a56e800be1f1bd69c60148ffccd51e8b3"
LIMIT = 60.
read = lambda p:json.loads(p.read_text(encoding="utf-8"))
sha = lambda p:sha256(p.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo",type=Path,required=True)
    parser.add_argument("--helper",type=Path,default=Path(__file__).with_name("counter_attempts.py"))
    parser.add_argument("--output",type=Path,required=True)
    args = parser.parse_args()
    root,helper,output = args.repo.resolve(),args.helper.resolve(),args.output.resolve()
    assert not output.exists() and sha(helper) == COUNTER_PIN
    old = root/"lf_data_preparation/native_workpiece_001/coarse_square_cycle_010"
    partial = root/"lf_data_preparation/native_workpiece_001/shift_square_pose_001/run_001"
    files = [helper,Path(__file__).resolve(),old/"result/result.json",old/"execution_receipt.json",
             partial/"result/result.json",partial/"execution_receipt.json"]
    pins = {str(f):sha(f) for f in files}
    tree = ast.parse(helper.read_text(encoding="utf-8"))
    assert all(isinstance(n,ast.ImportFrom) and n.module == "math" for n in tree.body
               if isinstance(n,(ast.Import,ast.ImportFrom)))
    spec = importlib.util.spec_from_file_location("pure_attempt_counter_test",helper)
    module = importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    complete,complete_receipt = read(old/"result/result.json"),read(old/"execution_receipt.json")
    failed,failed_receipt = read(partial/"result/result.json"),read(partial/"execution_receipt.json")
    cases = []

    def checked(condition,message):
        if not condition: raise AssertionError(message)

    def evaluate(name,result,receipt,expected_reject):
        assert perf_counter()-STARTED <= LIMIT
        try:
            accounting = module.reconstruct(result,receipt,result["settings"],checked)
        except AssertionError as error:
            assert expected_reject, name+": "+str(error)
            cases.append(dict(name=name,status="expected_rejection",reason=str(error)))
            return None
        assert not expected_reject,name+": malformed metadata was accepted"
        cases.append(dict(name=name,status="counter_reconstructed",counts=accounting["counts"],
            accepted_caches=accounting["accepted_completed_caches"],
            predictor_invalid_J_bases=accounting["predictor_invalid_J_bases"],
            failed_tangent_base=accounting["failed_tangent_base"],
            rejected_range_trials=accounting["rejected_range_trials"],qualification=False))
        return accounting

    original = evaluate("actual_old010_complete_trace",complete,complete_receipt,False)
    assert original["failed_tangent_base"]["tangent_call"] == 44 and original["failed_tangent_base"]["force_call"] == 77
    assert [x["force_call"] for x in original["rejected_range_trials"]] == [90]
    evaluate("actual_pose001_partial_timeout_must_reject",failed,failed_receipt,True)
    # Exact archived accepted prefix; only the trailing timed-out attempt is removed.
    # Seven prefix targets are a synthetic metadata shape, not a replacement physical task.
    synthetic,synthetic_receipt = deepcopy(failed),deepcopy(failed_receipt)
    assert len(synthetic["states"]) == 13 and synthetic["states"][-1]["assembler_force_call"] == 105
    assert synthetic["states"][-1]["assembler_tangent_call"] == 56 and synthetic["failure"]["code"] == "time_limit"
    diagnostics = synthetic["path_diagnostics"]
    assert len(diagnostics["newton_history"]) == 57 and len(diagnostics["trials"]) == 44
    assert len(diagnostics["linear_solve_diagnostics"]) == 63 and len(diagnostics["failed_attempts"]) == 7
    diagnostics["newton_history"] = diagnostics["newton_history"][:56]
    diagnostics["trials"] = diagnostics["trials"][:43]
    diagnostics["linear_solve_diagnostics"] = diagnostics["linear_solve_diagnostics"][:61]
    diagnostics["failed_attempts"] = diagnostics["failed_attempts"][:6]
    diagnostics["timing_seconds"]["kernel_calls"] = 105
    diagnostics["timing_seconds"]["successful_kernel_calls"] = 99
    synthetic.update(status="success",failure=None,path_completed=True,targets_mm=synthetic["targets_mm"][:7],
        scope="synthetic_counter_fixture_only_not_a_physical_task_or_qualification")
    counts = dict(force_calls=105,force_calls_completed=99,tangent_calls=56,tangent_calls_completed=56,
                  solver_invocations=1,HP_calls=0,JIT_calls=0)
    synthetic["call_counts"] = counts
    synthetic_receipt.update(status="synthetic_counter_fixture",call_counts=deepcopy(counts),
        force_calls=105,observed_force_calls=105,observed_force_calls_completed=99,
        tangent_calls=56,observed_tangent_calls=56,observed_tangent_calls_completed=56)
    prefix = evaluate("synthetic_counter_fixture_pose001_known_13_accepted_prefix",synthetic,synthetic_receipt,False)
    assert [x["force_call"] for x in prefix["predictor_invalid_J_bases"]] == [23,31,39,47,64,65]
    assert prefix["accepted_completed_caches"] == [{"force_call":s["assembler_force_call"],
        "tangent_call":s["assembler_tangent_call"],"state_sha256":s["state_sha256"]} for s in failed["states"]]
    mutations = ["cache_ordinal","missing_predictor_LU","rollback_false","unknown_J_reason","unexplained_counter_deficit"]
    for name in mutations:
        altered,altered_receipt = deepcopy(synthetic),deepcopy(synthetic_receipt)
        if name == "cache_ordinal": altered["states"][4]["assembler_force_call"] += 1
        elif name == "missing_predictor_LU": del altered["path_diagnostics"]["linear_solve_diagnostics"][12]
        elif name == "rollback_false": altered["path_diagnostics"]["failed_attempts"][0]["rollback_bitwise_equal"] = False
        elif name == "unknown_J_reason": altered["path_diagnostics"]["failed_attempts"][0]["reason"] = "unattributed J failure"
        else:
            altered["call_counts"]["force_calls"] += 1
            altered_receipt["call_counts"] = deepcopy(altered["call_counts"])
            altered_receipt["force_calls"] = altered_receipt["observed_force_calls"] = altered["call_counts"]["force_calls"]
        evaluate("negative_"+name,altered,altered_receipt,True)
    assert len(cases) == 8 and all(sha(Path(f)) == pin for f,pin in pins.items())
    assert perf_counter()-STARTED <= LIMIT
    output.mkdir(parents=True)
    with (output/"synthetic_counter_fixture.json").open("x",encoding="utf-8") as stream:
        json.dump(dict(kind="synthetic_counter_fixture",physical_qualification=False,result=synthetic,
            receipt=synthetic_receipt,source_failed_pose001_result_sha256=pins[str(partial/"result/result.json")],
            scope="Archived13 accepted metadata with timed-out terminal branch removed solely for counter testing; no FE or shortened physical task"),stream,indent=2,allow_nan=False)
        stream.write("\n")
    report = dict(status="pass",scope="Pure counter metadata unit proof only, never HP or equilibrium qualification",cases=cases,
        helper_sha256=COUNTER_PIN,bindings=pins,all_bindings_unchanged=all(sha(Path(f))==pin for f,pin in pins.items()),
        synthetic_fixture_sha256=sha(output/"synthetic_counter_fixture.json"),physical_qualification=False,
        force_calls=0,tangent_calls=0,HP_calls=0,model_constructions=0,solver_calls=0,consumer_calls=0,
        zero_call_basis="Only stdlib JSON/AST/source hashing and the math-only metadata helper are imported; no mechanical evaluator is present",
        elapsed_seconds=perf_counter()-STARTED,helper_seconds=LIMIT,sampled_RSS_bytes=None,
        memory_basis="This pure helper does not sample RSS; any external monitor reports its own observed scope")
    assert report["all_bindings_unchanged"] and report["elapsed_seconds"] <= LIMIT
    with (output/"result.json").open("x",encoding="utf-8") as stream:
        json.dump(report,stream,indent=2,allow_nan=False);stream.write("\n")
    assert perf_counter()-STARTED <= LIMIT and all(sha(Path(f))==pin for f,pin in pins.items())
    print(json.dumps(dict(status="pass",cases=len(cases),scope=report["scope"],elapsed_seconds=perf_counter()-STARTED)),flush=True)


if __name__ == "__main__": main()
