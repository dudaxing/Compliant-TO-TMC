"""One mock-only batch functional window; reuse the existing science guard."""
from time import perf_counter
STARTED = perf_counter()
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--protocol', type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    card_file = (repo / args.protocol).resolve()
    card = json.loads(card_file.read_bytes())
    output = repo / card['output_directory']
    output.mkdir(parents=True, exist_ok=False)
    digest = lambda path: sha256(path.read_bytes()).hexdigest()
    receipt = dict(status='not_pass', invocations=1, protocol_sha256=digest(card_file),
                   scope='Mock transport and declared JSON contracts only; no numerical qualification',
                   started_utc=datetime.now(timezone.utc).isoformat())
    peak, failure, guard = 0, None, None
    old_profile = sys.getprofile()
    process = None

    def checkpoint():
        nonlocal peak
        if (card_file.parent / 'stop_requested.txt').exists():
            raise RuntimeError('Cooperative outer stop requested')
        if perf_counter() - STARTED > card['phases']['functional']['helper_seconds']:
            raise RuntimeError('Whole-helper elapsed limit')
        if process is not None:
            memory = process.memory_info()
            peak = max(peak, memory.rss, getattr(memory, 'peak_wset', 0))
            if peak > card['sampled_RSS_bytes']:
                raise RuntimeError('Sampled helper RSS limit')

    class Limits:
        def pytest_runtest_setup(self, item):
            checkpoint()

        def pytest_runtest_teardown(self, item, nextitem):
            checkpoint()

    try:
        checkpoint()
        before = {name: digest(repo / name) for name in card['bindings']}
        assert before == card['bindings']
        spec = importlib.util.spec_from_file_location('existing_interface_guard', repo / card['guard_file'])
        guard = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(guard)
        sys.setprofile(guard.profile_guard)
        import numpy
        guard.NP_LOAD_CODE = numpy.load.__code__
        import psutil
        process = psutil.Process()
        os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'
        os.environ['HF_BATCH_TEST_REPO'] = str(repo)
        sys.path.insert(0, str(repo / 'hf_repo/src'))
        import pytest
        checkpoint()
        junit = output / 'test_results.xml'
        code = pytest.main(['-q', '-x', '--disable-warnings', '--junitxml=' + str(junit),
                            str(repo / card['test_file'])], plugins=[Limits()])
        tree = ET.parse(junit).getroot()
        suites = list(tree) if tree.tag == 'testsuites' else [tree]
        counts = {key: sum(int(s.attrib.get(key, 0)) for s in suites)
                  for key in ('tests', 'errors', 'failures', 'skipped')}
        test_module = sys.modules.get('test_native_batch')
        receipt.update(pytest_exit_code=int(code), tests=counts,
                       mock_transport_calls=dict(getattr(test_module, 'MOCK_TRANSPORT_COUNTS', {})))
        assert code == 0 and counts == dict(tests=card['expected_tests'], errors=0, failures=0, skipped=0)
        assert receipt['mock_transport_calls'] == card['expected_mock_transport_calls']
        assert not any(guard.SCIENCE.values())
        receipt['all_bindings_unchanged'] = all(digest(repo / name) == pin for name, pin in before.items())
        assert receipt['all_bindings_unchanged']
        checkpoint()
        receipt['status'] = 'pass'
    except BaseException as error:
        failure = dict(exception_class=type(error).__name__, reason=str(error))
    finally:
        sys.setprofile(old_profile)
        receipt.update(failure=failure, scientific_calls=dict(guard.SCIENCE) if guard else None,
                       elapsed_seconds=perf_counter() - STARTED, peak_sampled_RSS_bytes=peak,
                       helper_seconds_limit=card['phases']['functional']['helper_seconds'],
                       sampled_RSS_limit_bytes=card['sampled_RSS_bytes'],
                       completed_utc=datetime.now(timezone.utc).isoformat())
        (output / 'execution_receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(receipt), flush=True)
    return 0 if receipt['status'] == 'pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
