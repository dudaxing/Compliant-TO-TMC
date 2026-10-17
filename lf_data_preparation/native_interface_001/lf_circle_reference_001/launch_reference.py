"""L-CREF1 one-shot saved-state reference launcher; run only after direct approval."""
from time import perf_counter, sleep
STARTED = perf_counter()
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import psutil

ROOT = Path(__file__).resolve().parents[3]
STAGE = Path(__file__).resolve().parent
read = lambda path: json.loads(path.read_bytes())


def sha(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def main():
    protocol_file = STAGE / 'protocol.json'
    protocol = read(protocol_file)
    authorization = read(STAGE/'author/authorization.json')
    assert authorization['authorized'] is authorization['authorization_from_direct_human_request'] is True
    assert authorization['card'] == protocol['card'] == 'L-CREF1'
    assert authorization['one_invocation'] is True and authorization['direct_human_request'].strip()
    assert authorization['protocol_sha256'] == sha(protocol_file)
    assert authorization['source_baseline_commit'] == protocol['source_baseline_commit']
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip() == protocol['source_baseline_commit']
    assert protocol['prepared'] is True and protocol['authorized'] is protocol['executed'] is False
    helper_limit,outer_limit = (protocol['phases']['reference'][name] for name in ('helper_seconds','outer_seconds'))
    assert helper_limit == 900 and outer_limit == 960
    assert authorization['helper_seconds'] == helper_limit and authorization['outer_seconds'] == outer_limit
    assert authorization['sampled_RSS_bytes'] == protocol['sampled_RSS_bytes'] == 8*1024**3
    receipt_file = STAGE / 'reference_launch.json'
    assert not receipt_file.exists() and not (STAGE / 'run_001').exists()
    assert not (STAGE / 'stop_requested.txt').exists() and not (STAGE / 'reference_stdout.log').exists()
    receipt = dict(card='L-CREF1', status='running', invocations=0,
        protocol_sha256=sha(protocol_file), source_baseline_commit=protocol['source_baseline_commit'],
        started_utc=datetime.now(timezone.utc).isoformat(),
        argv=[sys.executable, '-X', 'utf8', '-B', str(STAGE / 'execute_circle_reference.py'),
              '--repo', str(ROOT), '--input', str(ROOT / protocol['production_stage']),
              '--output', str(ROOT / protocol['reference_output']), '--protocol', str(protocol_file),
              '--time-limit', str(helper_limit)],
        outer_seconds=outer_limit, sampled_RSS_limit_bytes=protocol['sampled_RSS_bytes'],
        budget_mode='Elapsed checkpoints and sampled tree RSS; cooperative stop, no OS hard cap or force')
    write(receipt_file, receipt)
    peak, reason, child, child_elapsed, unchanged, helper = 0, None, None, None, False, {}
    try:
        assert all(sha(ROOT / name) == pin for name, pin in protocol['bindings'].items())
        assert perf_counter() - STARTED <= outer_limit and not (STAGE / 'stop_requested.txt').exists()
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1', MPLBACKEND='Agg')
        with (STAGE / 'reference_stdout.log').open('xb') as output:
            receipt['invocations'] = 1
            write(receipt_file, receipt)
            child_started = perf_counter()
            child = subprocess.Popen(receipt['argv'], cwd=ROOT, env=environment,
                stdout=output, stderr=subprocess.STDOUT)
            process = psutil.Process(child.pid)
            while child.poll() is None:
                try:
                    peak = max(peak, sum(member.memory_info().rss for member in
                        [process] + process.children(recursive=True) if member.is_running()))
                except psutil.NoSuchProcess:
                    pass
                if reason is None and (perf_counter() - STARTED > outer_limit or peak > protocol['sampled_RSS_bytes']):
                    reason = 'outer_elapsed_limit' if perf_counter() - STARTED > outer_limit else 'sampled_RSS_limit'
                    (STAGE / 'stop_requested.txt').write_text(reason, encoding='utf-8')
                sleep(.1)
        child_elapsed = perf_counter() - child_started
        if child_elapsed > helper_limit or perf_counter()-STARTED > outer_limit or (STAGE/'stop_requested.txt').exists():
            reason = reason or 'closed_resource_window_before_final_identity'
        unchanged = reason is None and all(sha(ROOT / name) == pin for name, pin in protocol['bindings'].items())
        helper_file = ROOT / protocol['reference_output'] / 'lifecycle.json'
        helper = read(helper_file) if helper_file.exists() else {}
        summary_file = ROOT / protocol['reference_output'] / 'summary.json'
        summary = read(summary_file) if summary_file.exists() else {}
        if reason is None and (child_elapsed > helper_limit or perf_counter() - STARTED > outer_limit or
                (STAGE / 'stop_requested.txt').exists()):
            reason = 'closed_resource_window_at_final_evidence'
        execution_file = ROOT/protocol['reference_output']/'execution_receipt.json'
        execution = read(execution_file) if execution_file.exists() else {}
        passed = execution.get('status') == 'pass' and execution.get('output_identity_seal') == 'complete_inside_original_helper_window' and child.returncode == 0 and reason is None and unchanged and helper.get('status') == summary.get('status') == 'pass'
        assert not passed or (summary['accepted_states'] == 1 and summary['HP_calls_started'] == summary['HP_calls_completed'] == 2
            and summary['plot_started'] == summary['plot_completed'] == helper['plot_started'] == helper['plot_completed'] == 1)
        receipt['status'] = 'pass' if passed else 'not_pass'
    except BaseException as error:
        receipt.update(status='not_pass', failure=dict(type=type(error).__name__, message=str(error)))
        if child is not None and child.poll() is None:
            reason = reason or 'launcher_observation_error'
            try:
                (STAGE / 'stop_requested.txt').write_text(reason, encoding='utf-8')
            finally:
                child.wait()
            child_elapsed = perf_counter() - child_started
    receipt.update(exit_code=child.returncode if child is not None else None,
        elapsed_seconds=perf_counter() - STARTED, child_terminal_wall_seconds=child_elapsed,
        peak_sampled_tree_RSS_bytes=peak, stop_reason=reason,
        all_bindings_unchanged=unchanged, helper_status=helper.get('status'),
        completed_utc=datetime.now(timezone.utc).isoformat())
    write(receipt_file, receipt)
    if perf_counter() - STARTED > outer_limit or (STAGE / 'stop_requested.txt').exists():
        receipt.update(status='not_pass', elapsed_seconds=perf_counter() - STARTED,
            stop_reason='closed_resource_window_at_receipt_write')
        write(receipt_file, receipt)
    print(json.dumps({key: receipt[key] for key in
        ('status', 'invocations', 'exit_code', 'elapsed_seconds', 'peak_sampled_tree_RSS_bytes', 'stop_reason')}, ensure_ascii=False), flush=True)
    if receipt['status'] != 'pass':
        raise RuntimeError('L-CREF1 closed non-success; no retry')


if __name__ == '__main__':
    main()
