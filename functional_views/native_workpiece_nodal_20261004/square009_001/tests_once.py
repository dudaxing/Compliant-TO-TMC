"""Run only five analytic saved-nodal-force cases once, without mechanics."""
from pathlib import Path
from hashlib import sha256
import json
import sys
from time import perf_counter

STARTED = perf_counter()
STAGE = Path(__file__).resolve().parent
ROOT = STAGE.parents[2]


def main():
    record = dict(status="running", invocations=1, failure=None,
        mechanical_hooks_monitored=False, new_force_tangent_solver_HP_calls=None)
    pins = json.loads((STAGE/"protocol.json").read_text())["bindings"]
    try:
        assert all(sha256((ROOT/n).read_bytes()).hexdigest() == v for n,v in pins.items())
        assert not (STAGE/"stop_requested.txt").exists()
        sys.path.insert(0, str(ROOT/"hf_repo/src"))
        import pytest
        code = pytest.main(["-q", "-x", "-p", "no:cacheprovider", "--junitxml="+str(STAGE/"junit.xml"),
                            str(ROOT/"hf_repo/tests/test_workpiece_nodal.py")])
        assert code == 0, "Analytic nodal tests failed; no retry"
        modules = sorted(n for n in sys.modules if n == "hf_eval" or n.startswith("hf_eval."))
        assert set(modules) == {"hf_eval", "hf_eval.workpiece_nodal", "hf_eval.boundary_geometry"}
        assert all(sha256((ROOT/n).read_bytes()).hexdigest() == v for n,v in pins.items())
        assert perf_counter()-STARTED <= 120 and not (STAGE/"stop_requested.txt").exists()
        record.update(status="pass", loaded_hf_eval_modules=modules, new_force_tangent_solver_HP_calls=0,
                      count_basis="Literal analytic cached vectors and pure boundary source/import closure")
    except BaseException as error:
        record.update(status="failed", failure=repr(error))
        raise
    finally:
        record["elapsed_seconds"] = perf_counter()-STARTED
        with (STAGE/"tests_receipt.json").open("x", encoding="utf-8") as stream:
            json.dump(record, stream, indent=2); stream.write("\n")
    print(json.dumps(record))


if __name__ == "__main__":
    main()
