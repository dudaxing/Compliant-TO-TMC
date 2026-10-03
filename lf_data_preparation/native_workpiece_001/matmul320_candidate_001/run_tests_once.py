"""One existing focused suite and three saved-primitive candidate probes."""
from pathlib import Path
from time import perf_counter
import hashlib
import json
import sys
import traceback

STARTED = perf_counter()
STAGE = Path(__file__).resolve().parent
ROOT = STAGE.parents[2]
RUNTIME = STAGE/'runtime/hf_repo/src'
LIMIT_SECONDS = 60
LIMIT_RSS = 8*1024**3
PEAK = 0


def main():
    import psutil
    import pytest

    output = STAGE/'unit_tests_result.json'
    assert not output.exists()
    report = dict(status='running', invocations=1,
        scope='Existing focused regression suite plus saved-primitive Decimal probes; no equilibrium qualification',
        test_source_sha256=hashlib.sha256((STAGE/'test_matmul320.py').read_bytes()).hexdigest(),
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        numerical_call_counts='Unit tests exercise mechanics and toy solver paths; calls are not separately instrumented or reported as zero',
        full_model_HP_calls=0, new_physical_production_paths=0)

    def write():
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

    def checkpoint():
        global PEAK
        info=psutil.Process().memory_info()
        PEAK=max(PEAK, info.rss, getattr(info, 'peak_wset', info.rss))
        if (STAGE/'stop_requested.txt').exists() or perf_counter()-STARTED > LIMIT_SECONDS or PEAK > LIMIT_RSS:
            raise RuntimeError('New unit-stage resource window closed; no retry')

    class Budget:
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
        paths.append(STAGE/'test_matmul320.py')
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
