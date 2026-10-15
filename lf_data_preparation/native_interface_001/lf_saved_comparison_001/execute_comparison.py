"""One approved L-COMP1 metadata suite, saved comparison, two plots and receipt."""
from time import perf_counter
STARTED = perf_counter()
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sys
import unittest
import psutil

STAGE = Path(__file__).resolve().parent
ROOT = STAGE.parents[2]
read = lambda path: json.loads(path.read_bytes())
protocol = read(STAGE / 'protocol.json')
OUTPUT = ROOT / protocol['output_directory']
events, calls, peak = Counter(), Counter(), 0
process = psutil.Process()


def checkpoint(event='resource_check'):
    global peak
    peak = max(peak, process.memory_info().rss)
    if (perf_counter() - STARTED > protocol['helper_seconds']
            or peak > protocol['sampled_RSS_bytes'] or (STAGE / 'stop_requested.txt').exists()):
        raise RuntimeError('L-COMP1 resource/stop boundary reached')
    events[event] += 1


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_bindings():
    for name, pin in (protocol['source_bindings'] | protocol['json_input_bindings']).items():
        checkpoint()
        assert sha256((ROOT / name).read_bytes()).hexdigest() == pin, name


def seal():
    outputs = {}
    for name in ('comparison.json', 'REVIEW.md', 'responses.png', 'geometry_quality.png'):
        checkpoint()
        path = OUTPUT / name
        if path.exists():
            raw = path.read_bytes()
            outputs[path.relative_to(ROOT).as_posix()] = dict(sha256=sha256(raw).hexdigest(), bytes=len(raw))
    checkpoint()
    return outputs


class BoundedResult(unittest.TextTestResult):
    def startTest(self, test):
        checkpoint()
        super().startTest(test)
        calls['test_methods_started'] += 1

    def stopTest(self, test):
        super().stopTest(test)
        calls['test_methods_finished'] += 1
        checkpoint()


def main():
    auth = read(STAGE / 'author/authorization.json')
    assert auth['card'] == protocol['card'] == 'L-COMP1'
    assert auth['authorized'] is auth['authorization_from_direct_human_reply'] is auth['one_invocation'] is True
    assert auth['protocol_sha256'] == sha256((STAGE / 'protocol.json').read_bytes()).hexdigest()
    assert not OUTPUT.exists()
    status, error, outputs, identity_seal, data, tests_run = 'not_pass', None, {}, 'not_complete', None, 0
    try:
        check_bindings()
        tests = load('_lcomp1_metadata_tests', ROOT / protocol['test_source'])
        suite = unittest.defaultTestLoader.loadTestsFromModule(tests)
        assert suite.countTestCases() == protocol['expected_test_methods'] == 3
        calls['test_suites_started'] += 1
        result = unittest.TextTestRunner(stream=sys.stdout, verbosity=2, failfast=True,
                                        resultclass=BoundedResult).run(suite)
        tests_run = result.testsRun
        assert result.wasSuccessful() and tests_run == calls['test_methods_started'] == calls['test_methods_finished'] == 3
        calls['test_suites_completed'] += 1
        checkpoint()
        example = load('_lcomp1_saved_comparison', ROOT / protocol['example_source'])
        calls['comparisons_started'] += 1
        data = example.main(['--repo', str(ROOT), '--spec', protocol['specification'],
                             '--output', str(OUTPUT)], checkpoint)
        calls['comparisons_completed'] += 1
        assert len(data['pairs']) == protocol['expected_pairs'] == 25
        assert len(data['designs']) == 2 and all(len(item['rows']) == 25 for item in data['designs'])
        assert events['json_read_started'] == events['json_read_completed'] == protocol['expected_comparison_json_reads'] == 26
        assert events['plot_started'] == events['plot_completed'] == 2
        assert events['comparison_written'] == events['review_written'] == 1
        check_bindings()
        outputs = seal()
        assert len(outputs) == 4
        identity_seal = 'complete_inside_original_helper_window'
        status = 'pass'
    except BaseException as failure:
        error = dict(type=type(failure).__name__, message=str(failure))
        if perf_counter() - STARTED <= protocol['helper_seconds'] and not (STAGE / 'stop_requested.txt').exists():
            try:
                outputs = seal()
                identity_seal = 'actual_partial_inside_original_helper_window'
            except BaseException:
                identity_seal = 'not_completed_before_resource_close'
    OUTPUT.mkdir(parents=True, exist_ok=True)
    receipt = dict(card='L-COMP1', status=status, error=error, calls=dict(calls),
        events=dict(events), json_read_event_scope='Example only: one spec plus 25 cached JSON inputs; wrapper binding checks are separate byte reads',
        test_methods_run=calls['test_methods_started'],
        test_methods_in_successful_suite=tests_run if calls['test_suites_completed'] else None,
        protocol_sha256=auth['protocol_sha256'], authorized_execution_source_commit=auth['authorized_execution_source_commit'],
        source_baseline_commit=protocol['source_baseline_commit'],
        design_rows=[len(item['rows']) for item in data['designs']] if data else [],
        pairs=len(data['pairs']) if data else 0, outputs=outputs, output_identity_seal=identity_seal,
        elapsed_seconds=perf_counter()-STARTED, helper_seconds=protocol['helper_seconds'],
        sampled_peak_RSS_bytes=peak, sampled_RSS_limit_bytes=protocol['sampled_RSS_bytes'],
        working_directory=str(Path.cwd()), completed_utc=datetime.now(timezone.utc).isoformat(),
        zero_new_science_basis='Pinned ordinary JSON comparison and scalar renderer; no dynamic mechanics hooks',
        new_HF_API_calls=0, new_force_calls=0, new_tangent_calls=0, new_HP_calls=0, new_solver_calls=0,
        new_plots=events['plot_completed'], old_media_reads=0, old_media_decodes=0,
        NPZ_reads=0, scientific_gzip_reads=0, CSV_reads=0,
        full_path_reference_upgraded=False, formal_labels=False, ranking=False)
    target = OUTPUT / 'execution_receipt.json'
    with target.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n')
    try:
        checkpoint()
    except RuntimeError as failure:
        status = receipt['status'] = 'not_pass'
        receipt['error'] = dict(type=type(failure).__name__, message=str(failure))
        receipt['elapsed_seconds'] = perf_counter()-STARTED
        target.write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(status=status, calls=dict(calls), tests=tests_run, pairs=receipt['pairs'])), flush=True)
    if status != 'pass':
        raise RuntimeError('L-COMP1 closed not_pass; no retry')


if __name__ == '__main__':
    main()
