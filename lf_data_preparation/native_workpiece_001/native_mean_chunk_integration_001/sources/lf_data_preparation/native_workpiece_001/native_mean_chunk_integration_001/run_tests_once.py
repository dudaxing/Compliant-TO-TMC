"""One fail-fast native mean entry integration window, no formal workpiece path."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from time import perf_counter
import sys

STARTED = perf_counter()
STAGE = Path(__file__).resolve().parent
ROOT = STAGE.parents[2]
sha = lambda p: sha256(p.read_bytes()).hexdigest()


def main():
    protocol = json.loads((STAGE/"protocol.json").read_text(encoding="utf-8"))
    assert not (STAGE/"tests_receipt.json").exists()
    assert all(sha(ROOT/n) == v for n,v in protocol["bindings"].items())
    sys.path.insert(0, str(ROOT/"hf_repo/src"))
    import psutil
    import pytest
    process = psutil.Process()
    record = dict(status="running", invocations=1, formal_workpiece_solver_calls=0,
        fixture_force_calls=None, fixture_tangent_calls=None, fixture_solver_calls=None,
        counts_scope="Pytest internal mechanics calls are not instrumented; tests contain small temporary paths",
        HP_calls=0, JIT_calls=0, elapsed_limit_seconds=120., sampled_RSS_limit_bytes=8*1024**3)
    class Outcome:
        def pytest_terminal_summary(self, terminalreporter):
            for name in ("passed", "failed", "skipped", "error"):
                record[name+"_tests"] = len(terminalreporter.stats.get(name, []))
    try:
        code = pytest.main(["-q", "-x", "-p", "no:cacheprovider",
                            "hf_repo/tests/test_native_mean.py",
                            "hf_repo/tests/test_native_mean_mechanical.py",
                            "hf_repo/tests/test_split_numpy_tangent_chunked.py"], plugins=[Outcome()])
        record["pytest_exit_code"] = int(code)
        assert code == 0, "Integration failed; no retry"
        assert record["passed_tests"] == 10 and all(record[n+"_tests"] == 0 for n in ("failed", "skipped", "error"))
        unchanged = all(sha(ROOT/n) == v for n,v in protocol["bindings"].items())
        memory = process.memory_info()
        peak = max(memory.rss, getattr(memory, "peak_wset", memory.rss))
        assert unchanged and perf_counter()-STARTED <= 120. and peak <= 8*1024**3
        assert not (STAGE/"stop_requested.txt").exists()
        record.update(status="pass", all_bindings_unchanged=True, sampled_peak_RSS_bytes=peak)
    except BaseException as error:
        record.update(status="not_pass", error=repr(error))
        raise
    finally:
        record.update(elapsed_seconds=perf_counter()-STARTED,
                      completed_utc=datetime.now(timezone.utc).isoformat())
        with (STAGE/"tests_receipt.json").open("x", encoding="utf-8") as stream:
            json.dump(record, stream, indent=2)
            stream.write("\n")
    print(json.dumps(record))


if __name__ == "__main__":
    main()
