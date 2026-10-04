"""One analytic test invocation; cooperative budget and actual JUnit counts."""
from pathlib import Path
from time import perf_counter
import argparse
import hashlib
import json
import sys
import xml.etree.ElementTree as ET

STARTED = perf_counter()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--stop-file", type=Path, required=True)
    parser.add_argument("--time-limit", type=float, default=60.)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(args.repo.resolve()/"src"))
    import pytest
    from hf_eval import native_region_geometry

    def checkpoint():
        if perf_counter()-STARTED > args.time_limit or args.stop_file.exists():
            pytest.exit("Analytic phase cooperative budget reached", returncode=2)

    class Budget:
        def pytest_runtest_setup(self, item):
            checkpoint()

        def pytest_runtest_teardown(self, item, nextitem):
            checkpoint()

    checkpoint()
    code = int(pytest.main([str(args.repo/"tests/test_native_region_geometry.py"),
        "-q", "-x", "-p", "no:cacheprovider", "--junitxml="+str(args.output/"junit.xml")], plugins=[Budget()]))
    checkpoint()
    suites = ET.parse(args.output/"junit.xml").getroot().findall("testsuite")
    counts = {name:sum(int(suite.attrib.get(name, 0)) for suite in suites)
              for name in ("tests", "failures", "errors", "skipped")}
    modules = sorted(name for name in sys.modules if name == "hf_eval" or name.startswith("hf_eval."))
    allowed = {"hf_eval", "hf_eval.native_region_geometry", "hf_eval.boundary_geometry"}
    closure = {name:Path(sys.modules[name].__file__).resolve() for name in modules}
    correct_paths = all(path == args.repo.resolve()/"src/hf_eval"/("__init__.py" if name == "hf_eval" else name.split(".")[-1]+".py")
                        for name,path in closure.items())
    verified = set(modules) == allowed and correct_paths
    status = "pass" if code == 0 and verified and counts["tests"] > 0 and not any(counts[n] for n in ("failures", "errors", "skipped")) else "failed"
    receipt = dict(status=status, pytest_exit_code=code, junit_counts=counts,
        loaded_hf_eval_modules=modules, source_sha256={name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in closure.items()},
        mechanical_scope_verified=verified, mechanical_hooks_monitored=False,
        mechanical_call_count_basis="Pinned pure geometry test sources and allowed loaded module closure; no mechanical hooks monitored",
        force_calls=0 if verified else None, tangent_calls=0 if verified else None,
        HP_calls=0 if verified else None, solver_calls=0 if verified else None,
        elapsed_seconds=perf_counter()-STARTED, helper_seconds_limit=args.time_limit)
    (args.output/"test_receipt.json").write_text(json.dumps(receipt, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps(receipt), flush=True)
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
