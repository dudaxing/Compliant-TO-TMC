"""Future one-shot launcher with sampled tree RSS and cooperative stop."""
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
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def main():
    protocol_file = STAGE / 'protocol.json'
    protocol = json.loads(protocol_file.read_bytes())
    receipt_file = STAGE / 'integration_launch.json'
    assert not receipt_file.exists()
    assert all(sha(ROOT / name) == pin for name, pin in protocol['bindings'].items())
    receipt = dict(card='M-INTEGRATE1', status='running', invocations=1,
        protocol_sha256=sha(protocol_file), started_utc=datetime.now(timezone.utc).isoformat(),
        argv=[sys.executable, '-B', str(STAGE / 'execute_integration.py')],
        outer_seconds=protocol['outer_seconds'], sampled_RSS_limit_bytes=protocol['sampled_RSS_bytes'],
        budget_mode='Cooperative checkpoints and sampled RSS; no OS hard cap or force termination')
    write(receipt_file, receipt)
    started, peak, reason = STARTED, 0, None
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1', MPLBACKEND='Agg')
    with (STAGE / 'integration_stdout.log').open('xb') as output:
        child_started = perf_counter()
        child = subprocess.Popen(receipt['argv'], cwd=ROOT, env=environment, stdout=output, stderr=subprocess.STDOUT)
        process = psutil.Process(child.pid)
        while child.poll() is None:
            try:
                peak = max(peak, sum(member.memory_info().rss for member in [process] + process.children(recursive=True) if member.is_running()))
            except psutil.NoSuchProcess:
                pass
            if reason is None and (perf_counter() - started > protocol['outer_seconds'] or peak > protocol['sampled_RSS_bytes']):
                reason = 'outer_elapsed_limit' if perf_counter() - started > protocol['outer_seconds'] else 'sampled_RSS_limit'
                (STAGE / 'stop_requested.txt').write_text(reason, encoding='utf-8')
            sleep(.1)
    child_elapsed = perf_counter() - child_started
    unchanged = all(sha(ROOT / name) == pin for name, pin in protocol['bindings'].items())
    helper_file = STAGE / 'run_001/execution_receipt.json'
    helper = json.loads(helper_file.read_bytes()) if helper_file.exists() else {}
    if reason is None and (child_elapsed > protocol['helper_seconds'] or perf_counter() - started > protocol['outer_seconds'] or (STAGE / 'stop_requested.txt').exists()):
        reason = 'closed_resource_window_at_final_evidence'
    receipt.update(status='pass' if child.returncode == 0 and reason is None and unchanged and helper.get('status') == 'pass' else 'not_pass',
        exit_code=child.returncode, elapsed_seconds=perf_counter() - started, peak_sampled_tree_RSS_bytes=peak,
        child_terminal_wall_seconds=child_elapsed,
        stop_reason=reason, immutable_bindings_unchanged=unchanged, helper_status=helper.get('status'),
        completed_utc=datetime.now(timezone.utc).isoformat())
    write(receipt_file, receipt)
    if perf_counter() - started > protocol['outer_seconds'] or (STAGE / 'stop_requested.txt').exists():
        receipt.update(status='not_pass', elapsed_seconds=perf_counter() - started, stop_reason='closed_resource_window_at_receipt_write')
        write(receipt_file, receipt)
    print(json.dumps({key:receipt[key] for key in ('status', 'exit_code', 'elapsed_seconds', 'peak_sampled_tree_RSS_bytes', 'stop_reason')}, ensure_ascii=False), flush=True)
    if receipt['status'] != 'pass':
        raise RuntimeError('M-INTEGRATE1 terminal non-success; no retry')


if __name__ == '__main__':
    main()
