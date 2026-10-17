"""Install one reviewed reader and run one bounded tiny compatibility suite."""
from time import perf_counter, sleep
STARTED = perf_counter()
from collections import Counter
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import psutil

STAGE = Path(__file__).resolve().parent
ROOT = STAGE.parents[2]
CARD = 'L-CUNLOAD1'
read = lambda path: json.loads(path.read_bytes())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n',
                    encoding='utf-8', newline='\n')


def main():
    protocol_file, auth_file = STAGE/'protocol.json', STAGE/'author/authorization.json'
    protocol, auth = read(protocol_file), read(auth_file)
    assert protocol['card'] == auth['card'] == CARD
    assert auth['authorized'] is auth['authorization_from_direct_human_request'] is auth['one_invocation'] is True
    assert auth['protocol_sha256'] == sha256(protocol_file.read_bytes()).hexdigest()
    assert auth['authorized_execution_source_commit'] == protocol['source_baseline_commit']
    assert (protocol['tests_seconds'], protocol['plot_seconds'], protocol['helper_seconds'],
            protocol['outer_seconds'], protocol['sampled_RSS_bytes']) == (120, 30, 180, 240, 1024**3)
    run, stop = ROOT/protocol['output_directory'], STAGE/'stop_requested.txt'
    assert not run.exists() and not stop.exists()
    run.mkdir(exist_ok=False)
    receipt_file = run/'execution_receipt.json'
    process, peak, calls = psutil.Process(), 0, Counter()
    receipt = dict(card=CARD, status='running', protocol_sha256=auth['protocol_sha256'],
        authorization_sha256=sha256(auth_file.read_bytes()).hexdigest(),
        source_baseline_commit=protocol['source_baseline_commit'], default_installations=0,
        installed_transitions=[], new_tests=None, HP_calls_by_wrapper=0,
        real_circle_solver_invocations=0, historical_scientific_payload_reads=0,
        output_identity_seal='not_complete', qualification_scope='Tiny first-unload API compatibility only; no circle unload or mechanical qualification')
    phase, outputs = 'bootstrap', {}

    def checkpoint():
        nonlocal peak
        memory = process.memory_info()
        peak = max(peak, memory.rss, getattr(memory, 'peak_wset', memory.rss))
        reason = ('external_stop_requested' if stop.exists() else
                  'sampled_RSS_limit' if peak > protocol['sampled_RSS_bytes'] else
                  'whole_helper_elapsed_limit' if perf_counter()-STARTED > protocol['helper_seconds'] else None)
        if reason:
            receipt['resource_stop_reason'] = reason
            raise RuntimeError(reason)

    def digest(path):
        value = sha256()
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(1024*1024), b''):
                checkpoint()
                value.update(block)
        checkpoint()
        return value.hexdigest()

    def bindings(key):
        for name, pin in protocol[key].items():
            assert digest(ROOT/name) == pin, name

    def seal():
        sealed = {}
        for path in sorted(run.rglob('*')):
            if path.is_file() and path != receipt_file:
                sealed[path.relative_to(ROOT).as_posix()] = dict(sha256=digest(path), bytes=path.stat().st_size)
        checkpoint()
        return sealed

    def child_once(argv, limit, kind):
        checkpoint()
        calls[kind+'_started'] += 1
        started, child_stop, child_error = perf_counter(), None, None
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1', MPLBACKEND='Agg')
        with (run/(kind+'_stdout.log')).open('xb') as output:
            child = subprocess.Popen(argv, cwd=protocol['working_directory'], env=env,
                                     stdout=output, stderr=subprocess.STDOUT)
            try:
                while child.poll() is None:
                    try:
                        checkpoint()
                        if perf_counter()-started > limit:
                            raise RuntimeError(kind+'_elapsed_limit')
                    except Exception as error:
                        child_stop = child_stop or str(error)
                        if not stop.exists():
                            stop.write_text(child_stop, encoding='utf-8')
                    sleep(.1)
            except BaseException as error:
                child_error, child_stop = error, child_stop or type(error).__name__
            finally:
                if child.poll() is None:
                    if not stop.exists():
                        stop.write_text(child_stop or kind+'_interrupted', encoding='utf-8')
                    child.wait()
        elapsed = perf_counter()-started
        if elapsed > limit or stop.exists():
            child_stop = child_stop or 'elapsed_or_stop_request'
        receipt[kind+'_terminal'] = dict(exit_code=child.returncode, elapsed_seconds=elapsed,
            limit_seconds=limit, stop_reason=child_stop,
            cleanup='Actual child waited; cooperative stop, original outer SUP2 owns the entire process tree')
        write(receipt_file, receipt)
        if child_error is not None:
            raise child_error
        if child.returncode != 0 or child_stop is not None:
            raise RuntimeError(kind+' non-success; no retry or following stage')
        calls[kind+'_completed'] += 1
        checkpoint()

    write(receipt_file, receipt)
    try:
        phase = 'baseline_bindings_and_installation'
        bindings('baseline_source_bindings')
        transitions = protocol['candidate_installations']
        assert len(transitions) == 1
        for transition in transitions:
            source, target = ROOT/transition['source'], ROOT/transition['target']
            assert digest(target) == transition['before_sha256']
            raw = source.read_bytes()
            assert sha256(raw).hexdigest() == transition['after_sha256']
            target.write_bytes(raw)
            assert digest(target) == transition['after_sha256']
            receipt['installed_transitions'].append(transition)
            receipt['default_installations'] += 1
            write(receipt_file, receipt)
        bindings('source_bindings')
        phase = 'focused_tests'
        try:
            child_once([sys.executable, '-X', 'utf8', '-B', str(ROOT/protocol['test_source']),
                '--repo', str(ROOT/'hf_repo'), '--output', str(run/'t'),
                '--stop-file', str(stop), '--time-limit', str(protocol['tests_seconds'])],
                protocol['tests_seconds'], 'tests_child')
        finally:
            test_file = run/'t/test_report.json'
            if test_file.exists():
                tests = read(test_file)
                receipt.update(new_tests=tests['methods_run'], tests_report=tests)
        assert tests['successful'] is True and tests['methods_run'] == tests['methods_expected'] == 8
        assert tests.get('skipped', 0) == 0
        counts = tests['calls']
        assert counts['real_solver_invocations'] == 6 and counts['linear_controller_paths'] == 2
        assert counts['HP_calls'] == counts['JIT_calls'] == 0
        receipt['test_call_counts'] = counts
        phase = 'new_scalar_display'
        display_started = perf_counter()
        child_once([sys.executable, '-X', 'utf8', '-B', str(ROOT/protocol['plot_source']),
            '--input', str(run/'t/test_scalar_rows.json'), '--output', str(run/'tiny_response.png'),
            '--stop-file', str(stop), '--time-limit', str(protocol['plot_seconds'])],
            protocol['plot_seconds'], 'plot_child')
        scalars = read(run/'t/test_scalar_rows.json')
        lines = ['# L-CUNLOAD1 tiny compatibility review', '',
            '16 cells / 50 DOF, no workpiece. Actual new test records only; not circle grip evidence.', '',
            '|series|d mm|R N|relative residual|fresh anchor|', '|---|---:|---:|---:|---|']
        for row in scalars['rows']:
            lines.append('|'+ '|'.join(str(row[key]) for key in
                ('series', 'd_mm', 'R_input_N', 'relative_residual', 'anchor_revalidation'))+'|')
        lines += ['', '![Tiny reaction and residual](tiny_response.png)', '',
            'Source reader transition only. Real circle 1.40 -> 1.35 mm is not executed.']
        (run/'REVIEW.md').write_text('\n'.join(lines)+'\n', encoding='utf-8', newline='\n')
        assert perf_counter()-display_started <= protocol['plot_seconds']
        receipt['display_elapsed_seconds'] = perf_counter()-display_started
        phase = 'final_binding_and_seal'
        bindings('source_bindings')
        outputs = seal()
        receipt.update(status='pass', output_identity_seal='complete_inside_original_helper_window')
    except BaseException as error:
        receipt.update(status='not_pass', error=dict(exception_class=type(error).__name__,
            reason=str(error), phase=phase), output_identity_seal='not_complete')
        # One original-window partial seal only; no scientific/display/installation retry.
        if perf_counter()-STARTED < protocol['helper_seconds'] and not stop.exists():
            try:
                outputs = seal()
                receipt['output_identity_seal'] = 'actual_partial_inside_original_helper_window'
            except BaseException as seal_error:
                receipt['partial_seal_error'] = dict(exception_class=type(seal_error).__name__, reason=str(seal_error))
    receipt.update(phase=phase, call_counts=dict(calls), outputs=outputs,
        elapsed_seconds=perf_counter()-STARTED, peak_sampled_helper_RSS_bytes=peak)
    write(receipt_file, receipt)
    print(json.dumps({key:receipt[key] for key in ('card','status','phase','default_installations','new_tests','elapsed_seconds')}), flush=True)
    if receipt['status'] != 'pass':
        raise RuntimeError('L-CUNLOAD1 closed not_pass; keep actual installation and partial evidence, no retry')


if __name__ == '__main__':
    main()
