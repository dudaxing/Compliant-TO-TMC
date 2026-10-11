"""Future approved M-INTEGRATE1: install eleven pinned files, test once."""
from time import perf_counter, sleep
STARTED = perf_counter()
from pathlib import Path
from hashlib import sha256
import json
import os
import subprocess
import sys
import psutil

ROOT = Path(__file__).resolve().parents[3]
STAGE = Path(__file__).resolve().parent
read = lambda path: json.loads(path.read_bytes())
sha = lambda path: sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def main():
    protocol = read(STAGE / 'protocol.json')
    authorization, reply = read(STAGE / 'author/authorization.json'), read(STAGE / 'author/direct_human_reply.json')
    proof_file = STAGE / 'author/source_publication_receipt.json'
    proof = read(proof_file)
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    assert protocol['card'] == authorization['card'] == reply['card'] == proof['prepared_card'] == 'M-INTEGRATE1'
    assert authorization['authorized'] is True and authorization['authorization_from_direct_human_reply'] is reply['authorization_from_direct_human_reply'] is True
    assert head == authorization['approved_source_commit'] == reply['approved_source_commit'] == proof['published_commit']
    assert authorization['protocol_sha256'] == sha(STAGE / 'protocol.json')
    assert authorization['human_evidence_sha256'] == sha(STAGE / 'author/direct_human_reply.json')
    assert authorization['source_publication_receipt_sha256'] == sha(proof_file)
    assert authorization['direct_human_answer'] == reply['direct_human_answer'] and reply['direct_human_answer'].strip() and reply['reply_context']
    assert proof['status'] == 'published_and_incrementally_restored_pass' and proof['prepared'] is True and proof['authorized'] is proof['executed'] is False
    assert (protocol['focused_tests_seconds'], protocol['helper_seconds'], protocol['outer_seconds'], protocol['sampled_RSS_bytes']) == (180, 300, 360, 8 * 1024**3)
    assert len(protocol['installation']) == 11 and len(protocol['focused_test_selectors']) == 25
    assert all(sha(ROOT / name) == pin for name, pin in protocol['bindings'].items())
    for row in protocol['installation']:
        target = (ROOT / row['target']).resolve()
        target.relative_to(ROOT / 'hf_repo')
        assert sha(ROOT / row['candidate']) == row['sha256']
        assert (sha(target) if target.exists() else None) == row['previous_sha256']
        if row['previous_sha256'] is not None:
            assert sha(ROOT / row['baseline_snapshot']) == row['previous_sha256']
    run, stop = STAGE / 'run_001', STAGE / 'stop_requested.txt'
    assert not run.exists() and not stop.exists()
    run.mkdir()
    receipt = dict(card='M-INTEGRATE1', status='running', approved_source_commit=head,
        protocol_sha256=sha(STAGE / 'protocol.json'), installed=[], focused_tests_started=0, focused_tests_completed=0,
        automatic_rollback=False, original_gripper_or_HP_or_plot_execution=0)
    receipt_file, peak, error = run / 'execution_receipt.json', 0, None
    process = psutil.Process()

    def checkpoint():
        nonlocal peak
        memory = process.memory_info()
        peak = max(peak, memory.rss, getattr(memory, 'peak_wset', memory.rss))
        if stop.exists() or peak > protocol['sampled_RSS_bytes'] or perf_counter() - STARTED > protocol['helper_seconds']:
            raise RuntimeError('integration_helper_resource_window_closed')

    write(receipt_file, receipt)
    try:
        checkpoint()
        for row in protocol['installation']:
            target = ROOT / row['target']
            target.parent.mkdir(parents=True, exist_ok=True)
            mode = 'xb' if row['previous_sha256'] is None else 'wb'
            with target.open(mode) as output:
                output.write((ROOT / row['candidate']).read_bytes())
            assert sha(target) == row['sha256']
            receipt['installed'].append(dict(path=row['target'], sha256=row['sha256']))
            write(receipt_file, receipt)
            checkpoint()
        assert all(sha(ROOT / name) == pin for name, pin in protocol['installed_runtime_SHA256'].items())
        test_receipt = run / 'focused_test_receipt.json'
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1', MPLBACKEND='Agg',
            HF_INTEGRATION_ROOT=str(ROOT), HF_INTEGRATION_STAGE=str(STAGE), HF_INTEGRATION_TEST_RECEIPT=str(test_receipt),
            HF_INTERFACE_TEST_REPO=str(ROOT), HF_BATCH_TEST_REPO=str(ROOT),
            PYTHONPATH=os.pathsep.join((str(STAGE), str(ROOT / 'hf_repo/src'), str(ROOT / 'hf_repo/tests'))))
        argv = [sys.executable, '-B', '-m', 'pytest', '-q', '-x', '--rootdir=' + str(ROOT),
            '-c', str(ROOT / 'hf_repo/pyproject.toml'), '-p', 'integration_focused_budget',
            '--basetemp=' + str(run / 'test_tmp'), '--junitxml=' + str(run / 'test_results.xml'),
            '-o', 'cache_dir=' + str(run / 'pytest_cache'), *protocol['focused_test_selectors']]
        receipt['test_argv'] = argv
        receipt['focused_tests_started'] = 1
        write(receipt_file, receipt)
        started, test_stop = perf_counter(), None
        with (run / 'focused_tests_stdout.log').open('xb') as output:
            child = subprocess.Popen(argv, cwd=ROOT, env=environment, stdout=output, stderr=subprocess.STDOUT)
            while child.poll() is None:
                try:
                    checkpoint()
                    if perf_counter() - started > protocol['focused_tests_seconds']:
                        raise RuntimeError('focused_tests_elapsed_limit')
                except RuntimeError as failure:
                    test_stop = test_stop or str(failure)
                    if not stop.exists():
                        stop.write_text(test_stop, encoding='utf-8')
                sleep(.1)  # Pinned pytest/real force checkpoints end the child; no force.
        elapsed = perf_counter() - started
        receipt['focused_tests_terminal'] = dict(exit_code=child.returncode, elapsed_seconds=elapsed, stop_reason=test_stop)
        if child.returncode != 0 or test_stop is not None or elapsed > protocol['focused_tests_seconds']:
            raise RuntimeError('focused_tests_terminal_non_success')
        tests = read(test_receipt)
        assert tests['status'] == 'pass' and tests['collected_selectors'] == protocol['focused_test_selectors'] and tests['passed_calls'] == 25
        receipt['focused_tests_completed'] = 1
        receipt['test_receipt_sha256'] = sha(test_receipt)
        checkpoint()
    except BaseException as failure:
        error = dict(code='integration_terminal_non_success', exception_class=type(failure).__name__, message=str(failure))
    finally:
        immutable = all(sha(ROOT / name) == pin for name, pin in protocol['bindings'].items())
        installed = {row['target']: (sha(ROOT / row['target']) if (ROOT / row['target']).exists() else None) for row in protocol['installation']}
        complete = all(installed[row['target']] == row['sha256'] for row in protocol['installation'])
        memory = process.memory_info()
        peak = max(peak, memory.rss, getattr(memory, 'peak_wset', memory.rss))
        window_closed = stop.exists() or peak > protocol['sampled_RSS_bytes'] or perf_counter() - STARTED > protocol['helper_seconds']
        if window_closed and error is None:
            error = dict(code='integration_helper_resource_window_closed', exception_class='RuntimeError', message='Resource boundary reached during final evidence collection')
        receipt.update(status='pass' if error is None and immutable and complete and receipt['focused_tests_completed'] == 1 else 'not_pass',
            failure=error, immutable_bindings_unchanged=immutable, installed_SHA256=installed, installation_complete=complete,
            elapsed_seconds=perf_counter() - STARTED, peak_sampled_RSS_bytes=peak,
            old_frozen_records_rewritten=False, new_pressure_clamp_stability_HF5_qualified=False)
        write(receipt_file, receipt)
        if stop.exists() or perf_counter() - STARTED > protocol['helper_seconds']:
            receipt.update(status='not_pass', elapsed_seconds=perf_counter() - STARTED,
                failure=error or dict(code='integration_helper_resource_window_closed', exception_class='RuntimeError', message='Resource boundary reached during receipt write'))
            write(receipt_file, receipt)
    print(json.dumps({key:receipt[key] for key in ('status', 'focused_tests_started', 'focused_tests_completed', 'elapsed_seconds', 'failure')}, ensure_ascii=False), flush=True)
    if receipt['status'] != 'pass':
        raise RuntimeError('M-INTEGRATE1 stopped; actual installation/test partials preserved, no retry or rollback')


if __name__ == '__main__':
    main()
