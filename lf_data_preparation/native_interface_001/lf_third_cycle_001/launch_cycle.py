"""Launch L-CYCLE1 once from an external cwd with cooperative sampled limits."""
from time import perf_counter, sleep
STARTED = perf_counter()
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import psutil

STAGE = Path(__file__).resolve().parent
ROOT = STAGE.parents[2]
read = lambda path: json.loads(path.read_bytes())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def main():
    raw = (STAGE / 'protocol.json').read_bytes()
    protocol, auth = json.loads(raw), read(STAGE / 'author/authorization.json')
    assert auth['authorized'] is auth['authorization_from_direct_human_request'] is auth['one_invocation'] is True
    assert auth['card'] == protocol['card'] == 'L-CYCLE1' and auth['direct_human_request']
    assert auth['protocol_sha256'] == sha256(raw).hexdigest()
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == auth['source_baseline_commit']
    assert (protocol['helper_seconds'], protocol['outer_seconds'], protocol['sampled_RSS_bytes']) == (19000, 19060, 8*1024**3)
    output, receipt_file = ROOT / protocol['output_directory'], STAGE / 'cycle_launch.json'
    assert not any(path.exists() for path in (output, receipt_file, STAGE/'cycle_stdout.log', STAGE/'stop_requested.txt'))
    for name, pin in protocol['source_bindings'].items():
        assert sha256((ROOT / name).read_bytes()).hexdigest() == pin, name
    cwd = Path(tempfile.mkdtemp(prefix='hf-LCYCLE1-')).resolve()
    assert not cwd.is_relative_to(ROOT)
    argv = [sys.executable, '-X', 'utf8', '-B', str(STAGE / 'execute_cycle.py'), '--repo', str(ROOT), '--protocol', str(STAGE/'protocol.json')]
    receipt = dict(card='L-CYCLE1', status='running', invocations=0, argv=argv, working_directory=str(cwd),
        protocol_sha256=auth['protocol_sha256'], source_baseline_commit=auth['source_baseline_commit'],
        started_utc=datetime.now(timezone.utc).isoformat(), helper_seconds=19000, outer_seconds=19060,
        sampled_RSS_limit_bytes=8*1024**3,
        resource_mode='Elapsed checkpoints and sampled RSS; cooperative stop and actual child wait, no OS hard cap or force')
    write(receipt_file, receipt)
    child, reason, peak, child_wall, helper = None, None, 0, None, {}
    try:
        with (STAGE / 'cycle_stdout.log').open('xb') as log:
            receipt['invocations'] = 1
            write(receipt_file, receipt)
            child_start = perf_counter()
            child = subprocess.Popen(argv, cwd=cwd, stdout=log, stderr=subprocess.STDOUT,
                env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1', MPLBACKEND='Agg'))
            process = psutil.Process(child.pid)
            while child.poll() is None:
                try:
                    peak = max(peak, sum(member.memory_info().rss for member in [process]+process.children(recursive=True) if member.is_running()))
                except psutil.NoSuchProcess:
                    pass
                if reason is None and (perf_counter()-child_start > 19000 or perf_counter()-STARTED > 19060 or peak > 8*1024**3):
                    reason = 'resource_limit'
                    (STAGE / 'stop_requested.txt').write_text(reason, encoding='utf-8')
                sleep(.05)
        child_wall = perf_counter()-child_start
        helper_path = output / 'execution_receipt.json'
        helper = read(helper_path) if helper_path.exists() else {}
        passed = (child.returncode == 0 and reason is None and child_wall <= 19000 and perf_counter()-STARTED <= 19060
            and helper.get('status') == 'pass' and helper.get('output_identity_seal') == 'complete_inside_original_helper_window')
        receipt['status'] = 'pass' if passed else 'not_pass'
    except BaseException as failure:
        receipt.update(status='not_pass', error=dict(type=type(failure).__name__, message=str(failure)))
        if child is not None and child.poll() is None:
            reason = reason or 'launcher_observation_error'
            (STAGE / 'stop_requested.txt').write_text(reason, encoding='utf-8')
            child.wait()
            child_wall = perf_counter()-child_start
    receipt.update(exit_code=child.returncode if child is not None else None,
        elapsed_seconds=perf_counter()-STARTED, child_terminal_wall_seconds=child_wall,
        peak_sampled_tree_RSS_bytes=peak, stop_reason=reason, helper_status=helper.get('status'),
        completed_utc=datetime.now(timezone.utc).isoformat())
    write(receipt_file, receipt)
    print(json.dumps({key: receipt[key] for key in ('status', 'invocations', 'exit_code', 'elapsed_seconds', 'peak_sampled_tree_RSS_bytes', 'stop_reason')}), flush=True)
    if receipt['status'] != 'pass':
        raise RuntimeError('L-CYCLE1 closed not_pass; no retry or force')


if __name__ == '__main__':
    main()
