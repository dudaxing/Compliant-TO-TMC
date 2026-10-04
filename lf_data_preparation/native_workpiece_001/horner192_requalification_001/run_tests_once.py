"""New unit window after001 pre-collection hook failure; frozen tests unchanged."""
from pathlib import Path
from time import perf_counter
import hashlib
import json
import sys
import traceback

STARTED = perf_counter()
STAGE = Path(__file__).resolve().parent
ROOT = STAGE.parents[2]
SOURCE_STAGE = ROOT/'lf_data_preparation/native_workpiece_001/horner192_candidate_001'
RUNTIME = SOURCE_STAGE/'runtime/hf_repo/src'
LIMIT_SECONDS = 60
LIMIT_RSS = 8*1024**3
PEAK = 0


def main():
    import psutil
    import pytest

    output = STAGE/'unit_tests_result.json'
    assert not output.exists()
    report = dict(status='running', invocations=1,
        scope='New002 unit window after closed001 pre-collection PluginValidationError; frozen00120+3+2cases unchanged; no equilibrium qualification',
        test_source_sha256=hashlib.sha256((SOURCE_STAGE/'test_horner192.py').read_bytes()).hexdigest(),
        baseline_source_sha256=hashlib.sha256((SOURCE_STAGE/'baseline_core.py').read_bytes()).hexdigest(),
        collected_tests=0, started_tests=0, passed_tests=0, failed_tests=0, skipped_tests=0,
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        numerical_call_counts='Unit tests exercise mechanics and toy solver paths; calls are not separately instrumented or reported as zero',
        full_model_HP_calls=0, new_physical_production_paths=0,
        predecessor_unit_result_sha256=hashlib.sha256((SOURCE_STAGE/'unit_tests_result.json').read_bytes()).hexdigest())
    stats = report

    def write():
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

    def checkpoint():
        global PEAK
        info=psutil.Process().memory_info()
        PEAK=max(PEAK, info.rss, getattr(info, 'peak_wset', info.rss))
        if (STAGE/'stop_requested.txt').exists() or perf_counter()-STARTED > LIMIT_SECONDS or PEAK > LIMIT_RSS:
            raise RuntimeError('New unit-stage resource window closed; no retry')

    outcomes = {}

    class Budget:
        def pytest_collection_finish(self, session):
            report["collected_tests"] = len(session.items)

        def pytest_runtest_logstart(self, nodeid, location):
            report["started_tests"] += 1

        def pytest_runtest_logreport(self, report):
            if report.failed:
                outcomes[report.nodeid] = "failed"
            elif report.skipped and outcomes.get(report.nodeid) != "failed":
                outcomes[report.nodeid] = "skipped"
            elif report.when == "call" and report.passed and report.nodeid not in outcomes:
                outcomes[report.nodeid] = "passed"
            for status in ("passed", "failed", "skipped"):
                stats[status+"_tests"] = sum(value == status for value in outcomes.values())

        def pytest_runtest_teardown(self, item, nextitem):
            checkpoint()

    write()
    try:
        sys.path.insert(0, str(RUNTIME))
        import hf_eval
        assert Path(hf_eval.__file__).resolve() == (RUNTIME/'hf_eval/__init__.py').resolve()
        checkpoint()
        paths=[ROOT/'hf_repo/tests'/name for name in (
            'test_split_numpy_force.py', 'test_split_numpy_tangent.py', 'test_split_cycle.py')]
        paths.append(SOURCE_STAGE/'test_horner192.py')
        report['test_file_sha256'] = {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
        report['test_files']=[path.relative_to(ROOT).as_posix() for path in paths]
        code=pytest.main(['-q', '--maxfail=1', '-p', 'no:cacheprovider', *map(str, paths)], plugins=[Budget()])
        report['pytest_exit_code']=int(code)
        checkpoint()
        report['status']='pass' if int(code)==0 else 'failed'
    except Exception as error:
        report.update(status='failed', error=repr(error), traceback=traceback.format_exc())
    finally:
        report.update(elapsed_seconds=perf_counter()-STARTED, sampled_peak_RSS_bytes=PEAK)
        write()
    print(json.dumps(report, ensure_ascii=False), flush=True)
    return 0 if report['status']=='pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
