"""One bounded controller regression suite; no full-size physical path or HP."""
from time import perf_counter
STARTED = perf_counter()
from pathlib import Path
from hashlib import sha256
import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET
import psutil


def main():
    parser = argparse.ArgumentParser()
    for name in ('repo', 'protocol', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    root, out = args.repo.resolve(), args.output.resolve()
    protocol = json.loads(args.protocol.read_text(encoding='utf-8'))
    out.mkdir(parents=True, exist_ok=False)
    digest = lambda path: sha256(path.read_bytes()).hexdigest()
    pins = protocol['bindings']
    process = psutil.Process()
    report = dict(status='running', pytest_invocations=0, small_solver_calls=0,
        source_transition=protocol['source_transition'],
        largest_test_model_elements=0, full_HF_solver_calls=0, HP_calls=0,
        production_force_changed=False, force_tangent_gates_changed=False,
        default_initial_guess_preserved=False, peak_sampled_RSS_bytes=0,
        scope='Small analytic controller and real NumPy integration tests; no workpiece qualification')

    def check():
        memory = process.memory_info()
        report['peak_sampled_RSS_bytes'] = max(report['peak_sampled_RSS_bytes'], memory.rss,
                                               getattr(memory, 'peak_wset', memory.rss))
        assert perf_counter()-STARTED <= 180
        assert report['peak_sampled_RSS_bytes'] <= 8*1024**3
        assert not (args.protocol.parent/'stop_requested.txt').exists()

    try:
        assert all(digest(root/name) == pin for name, pin in pins.items())
        check()
        sys.path.insert(0, str(root/'hf_repo/src'))
        sys.path.insert(0, str(root/'hf_repo/tests'))
        os.environ['JAX_ENABLE_X64'] = 'true'
        os.environ['JAX_PLATFORMS'] = 'cpu'
        import hf_eval.split_displacement as control
        original = control.solve_split_displacement_path

        def counted(model, *positional, **keywords):
            check()
            ne = len(model.connectivity)
            report['largest_test_model_elements'] = max(report['largest_test_model_elements'], ne)
            assert ne <= 16, 'This card does not authorize a full gripper path'
            report['small_solver_calls'] += 1
            result = original(model, *positional, **keywords)
            check()
            return result

        control.solve_split_displacement_path = counted
        import pytest

        class Limits:
            def pytest_runtest_setup(self, item):
                check()

            def pytest_runtest_teardown(self, item, nextitem):
                check()

        report['pytest_invocations'] = 1
        tests = [str(root/name) for name in protocol['test_files']]
        code = pytest.main([*tests, '-q', '--maxfail=1',
                            '--junitxml='+str(out/'tests.xml')], plugins=[Limits()])
        report['pytest_exit_code'] = int(code)
        suites = ET.parse(out/'tests.xml').getroot()
        totals = {key: sum(int(row.get(key, 0)) for row in suites.iter('testsuite'))
                  for key in ('tests', 'failures', 'errors', 'skipped')}
        report.update(tests=totals, tests_passed=totals['tests']-sum(totals[k] for k in ('failures','errors','skipped')),
                      tests_failed=totals['failures'], tests_errors=totals['errors'], tests_skipped=totals['skipped'])
        check()
        assert int(code) == 0 and report['tests_passed'] == protocol['expected_tests'] == 15
        assert totals['failures'] == totals['errors'] == totals['skipped'] == 0
        report.update(status='pass', default_initial_guess_preserved=True)
    except BaseException as error:
        report.update(status='not_pass', error=repr(error))
        raise
    finally:
        report.update(elapsed_seconds=perf_counter()-STARTED,
                      all_bindings_unchanged=all(digest(root/name) == pin for name, pin in pins.items()))
        if not report['all_bindings_unchanged']:
            report.update(status='not_pass', error='Source/input binding drift')
        (out/'receipt.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    assert report['all_bindings_unchanged']
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
