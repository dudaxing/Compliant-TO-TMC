"""Run only the five independent construction tests, once within their card."""
from time import perf_counter
STARTED = perf_counter()
from hashlib import sha256
from pathlib import Path
import argparse
import json
import os
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    args = parser.parse_args()
    root = args.repo.resolve()
    protocol_file = args.protocol.resolve()
    stage = protocol_file.parent
    protocol = json.loads(protocol_file.read_text(encoding="utf-8"))
    pins = protocol["bindings"]
    digest = lambda p: sha256(p.read_bytes()).hexdigest()
    assert all(digest(root/name) == pin for name, pin in pins.items())
    run = stage/"run_001"
    run.mkdir(exist_ok=False)
    started = STARTED
    counts = dict(constructor_invocations=0,tests_collected=0,tests_passed=0)
    reports = []

    def check():
        if (stage/"stop_requested.txt").exists() or perf_counter()-started > protocol["phases"]["tests"]["helper_seconds"]:
            raise RuntimeError("Declared adapter-test limit reached; no retry")

    os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    sys.path.insert(0,str(root/"hf_repo/src"))
    import pytest
    from hf_eval import native_project
    original_constructor = native_project.build_native_project

    def construct(*a,**kw):
        check()
        counts["constructor_invocations"] += 1
        assert counts["constructor_invocations"] <= 2
        value = original_constructor(*a,**kw)
        check()
        return value

    class Record:
        def pytest_collection_finish(self,session):
            counts["tests_collected"] = len(session.items)
            assert counts["tests_collected"] == 5
            check()

        def pytest_runtest_logreport(self,report):
            reports.append(dict(nodeid=report.nodeid,when=report.when,outcome=report.outcome,duration_seconds=report.duration))
            if report.when == "call" and report.passed:
                counts["tests_passed"] += 1
            check()

    native_project.build_native_project = construct
    code = None
    error = None
    try:
        code = int(pytest.main(["-c",str(root/"hf_repo/pyproject.toml"),"-q","-x","--maxfail=1","-p","no:cacheprovider",
            str(root/protocol["test_file"])],plugins=[Record()]))
        check()
    except Exception as exc:
        error = repr(exc)
    finally:
        native_project.build_native_project = original_constructor
    unchanged = all(digest(root/name) == pin for name, pin in pins.items())
    try:
        check()
    except Exception as exc:
        error = repr(exc)
    passed = code == 0 and error is None and unchanged and counts == dict(constructor_invocations=2,tests_collected=5,tests_passed=5)
    receipt = dict(schema_version="right-margin-adapter-test-receipt-1.0",status="pass" if passed else "not_pass",
        pytest_exit_code=code,error=error,**counts,elapsed_seconds=perf_counter()-started,
        new_force_calls=0,new_tangent_calls=0,new_equilibrium_calls=0,new_HP_calls=0,
        zero_response_basis="Selected test source contains geometry, map and two constructor operations only; no response API is invoked",
        protocol_sha256=digest(protocol_file),all_bindings_unchanged=unchanged,reports=reports)
    (run/"test_receipt.json").write_text(json.dumps(receipt,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in receipt.items() if k != "reports"}),flush=True)
    if not passed:
        raise RuntimeError("Adapter-test card closed without pass; no retry")


if __name__ == "__main__":
    main()
