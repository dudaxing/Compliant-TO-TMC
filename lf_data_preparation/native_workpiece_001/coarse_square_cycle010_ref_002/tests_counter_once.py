"""One pure-stdlib saved-counter test phase; no physics or reference evaluation."""
from time import perf_counter
STARTED = perf_counter()
import argparse
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys

STAGE = Path(__file__).resolve().parent
ROOT = next(p for p in STAGE.parents if (p/"hf_repo").is_dir())
SCIENCE = ROOT/"lf_data_preparation/native_workpiece_001/coarse_square_cycle_010"
COUNTER_SHA = "547a76f7d1b750a2f423fdce043a90e4b6754c6148167bb350d36f2852ced32e"
INPUT_SHA = {
    "result/result.json": "7338a65980abaa7d45d72ccee453352c5960e6dc416f82b8d8a4db5ca46e31c4",
    "execution_receipt.json": "fb3c998b414fc436a4da30435bc24ac0fc92b4dacd6b008effe643cce320df28",
    "input_inventory.json": "bb08fa9339ea36c2057bf6672630f3231bc7f61a923b22a63ab77cc55abcf5f6"}
sha = lambda p: sha256(p.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve(); output.mkdir(parents=True, exist_ok=False)
    report = dict(status="running",invocations=1,tests_collected=12,tests_started=0,
        tests_passed=0,tests_failed=0,rows=[],helper_seconds_limit=60,
        outer_seconds_contract=90,sampled_RSS_limit_bytes=8*1024**3,
        RSS_enforcement="Outer launcher sampling; tester uses only stdlib",
        new_calls=dict(force=0,tangent=0,solver=0,HP=0,consumer=0,NumPy_API=0,geometry=0,render=0),
        qualification="Counter/chronology metadata only; no failed-state or accepted mechanical HP qualification")
    pins = {}

    def checkpoint():
        assert perf_counter()-STARTED <= 60, "Metadata unit budget closed"
        assert not (STAGE/"stop_requested.txt").exists(), "Outer stop requested"

    def bind(path, expected=None):
        checkpoint(); actual = sha(path)
        assert expected is None or actual == expected, "Frozen identity differs: "+path.name
        pins[path.resolve()] = actual

    try:
        bind(Path(__file__).resolve()); bind(STAGE/"counter_contract.py",COUNTER_SHA)
        for name,pin in INPUT_SHA.items(): bind(SCIENCE/name,pin)
        sys.path.insert(0,str(STAGE))
        import counter_contract
        assert Path(counter_contract.__file__).resolve() == STAGE/"counter_contract.py"
        result = json.loads((SCIENCE/"result/result.json").read_text(encoding="utf-8"))
        receipt = json.loads((SCIENCE/"execution_receipt.json").read_text(encoding="utf-8"))
        settings = json.loads((SCIENCE/"input_inventory.json").read_text(encoding="utf-8"))["settings"]
        assert result["status"] == "success" and receipt["status"] == "pass"
        assert result["call_counts"] == dict(force_calls=94,force_calls_completed=93,tangent_calls=53,
            tangent_calls_completed=52,solver_invocations=1,JIT_calls=0,HP_calls=0)
        range_trial = next(i for i,t in enumerate(result["path_diagnostics"]["trials"])
                           if t.get("reason") == "unsupported_arithmetic_range")

        def mirror_count(r,p,name,value):
            r["call_counts"][name] = p["call_counts"][name] = value
            if name == "tangent_calls": p["tangent_calls"] = p["observed_tangent_calls"] = value
            if name == "tangent_calls_completed": p["observed_tangent_calls_completed"] = value

        def wrong_started(r,p): mirror_count(r,p,"tangent_calls",54)
        def multiple_missing(r,p): mirror_count(r,p,"tangent_calls_completed",51)
        def capture_force(r,p): p["first_tangent_range_input"]["bound_force_call_ordinal"] = 78
        def unknown_failure(r,p): r["path_diagnostics"]["failed_attempts"][0]["code"] = "unrecorded_failure"
        def rollback_false(r,p): r["path_diagnostics"]["failed_attempts"][0]["rollback_bitwise_equal"] = False
        def wrong_midpoint(r,p): r["states"][-2]["d"] = .3
        def wrong_depth(r,p): r["states"][-2]["bisection_depth"] = 0
        def failed_cache(r,p): r["states"][-2]["assembler_tangent_call"] = 44
        def wrong_halving(r,p): r["path_diagnostics"]["trials"][range_trial+1]["factor"] = .25
        def cache_state(r,p): r["states"][0]["assembler_state_sha256"] = "0"*64
        def cache_force(r,p): r["states"][0]["assembler_force_call"] = 2
        cases = [("real_saved_trace",None),("wrong_started_T",wrong_started),
            ("multiple_missing_T",multiple_missing),("capture_force_ordinal",capture_force),
            ("unknown_failed_attempt",unknown_failure),("rollback_false",rollback_false),
            ("wrong_midpoint",wrong_midpoint),("wrong_depth",wrong_depth),
            ("accepted_cache_on_failed_T",failed_cache),("wrong_trial_halving",wrong_halving),
            ("cache_state_SHA_mismatch",cache_state),("cache_force_ordinal_mismatch",cache_force)]
        for name,mutation in cases:
            checkpoint(); r,p = deepcopy(result),deepcopy(receipt)
            if mutation is not None: mutation(r,p)
            report["tests_started"] += 1
            row = dict(name=name,expected="accept" if mutation is None else "ValueError",gate_checks=0)

            def check(condition,label):
                checkpoint(); row["gate_checks"] += 1
                if not condition: raise ValueError(label)

            try:
                observed = counter_contract.reconstruct(r,p,settings,check)
                if mutation is not None: raise AssertionError("Corrupted metadata was admitted: "+name)
                assert observed["Newton_base_calls"] == 53 and observed["completed_Newton_base_calls"] == 52
                assert observed["trial_calls"] == 41 and observed["completed_trials"] == 40
                assert len(observed["reconstructed_force_events"]) == 94 and len(observed["accepted_completed_caches"]) == 12
                assert observed["failed_tangent_base"]["force_call"] == 77 and observed["failed_tangent_base"]["tangent_call"] == 44
                assert [x["force_call"] for x in observed["rejected_range_trials"]] == [90]
                assert observed["all_accepted_caches_completed"] is True and observed["all_Newton_base_and_tangent_calls_completed"] is False
                row.update(actual="accepted",status="pass")
            except ValueError as error:
                if mutation is None:
                    row.update(status="fail",error=repr(error)); report["rows"].append(row)
                    report["tests_failed"] += 1; raise
                row.update(actual="ValueError",rejection=str(error),status="pass")
            except BaseException as error:
                row.update(status="fail",error=repr(error)); report["rows"].append(row)
                report["tests_failed"] += 1; raise
            report["rows"].append(row); report["tests_passed"] += 1
        checkpoint(); assert all(sha(p) == pin for p,pin in pins.items())
        assert not any(n == "numpy" or n == "hf_eval" or n.startswith("hf_eval.") for n in sys.modules)
        report.update(status="pass",all_bindings_unchanged=True)
    except BaseException as error:
        report.update(status="not_pass",error=repr(error)); raise
    finally:
        report.update(elapsed_seconds=perf_counter()-STARTED,completed_utc=datetime.now(timezone.utc).isoformat(),
            source_and_input_bindings={p.relative_to(ROOT).as_posix():pin for p,pin in pins.items()})
        with (output/"tests_receipt.json").open("x",encoding="utf-8") as stream:
            json.dump(report,stream,indent=2); stream.write("\n")
    print(json.dumps({k:report[k] for k in ("status","tests_started","tests_passed","tests_failed","elapsed_seconds")}))


if __name__ == "__main__":
    main()
