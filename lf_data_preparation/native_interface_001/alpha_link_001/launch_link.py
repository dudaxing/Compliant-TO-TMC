"""M-ALINK1 one-shot metadata association launcher, after direct card approval."""
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
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def main():
    protocol_file = STAGE / 'protocol.json'
    protocol = read(protocol_file)
    authorization, reply, proof = (read(STAGE / 'author' / name) for name in
        ('authorization.json', 'direct_human_reply.json', 'source_publication_receipt.json'))
    assert authorization['authorized'] is True
    assert authorization['authorization_from_direct_human_reply'] is reply['authorization_from_direct_human_reply'] is True
    assert authorization['card'] == reply['card'] == proof['prepared_card'] == 'M-ALINK1'
    assert authorization['approved_source_commit'] == reply['approved_source_commit'] == proof['published_commit']
    assert proof['status'] == 'published_and_incrementally_restored_pass' and proof['prepared'] is True
    assert proof['authorized'] is proof['executed'] is False
    assert authorization['protocol_sha256'] == proof['protocol_sha256'] == sha(protocol_file)
    assert authorization['human_evidence_sha256'] == sha(STAGE / 'author/direct_human_reply.json')
    assert authorization['source_publication_receipt_sha256'] == sha(STAGE / 'author/source_publication_receipt.json')
    assert authorization['direct_human_answer'] == reply['direct_human_answer'] and reply['direct_human_answer'].strip()
    assert reply['reply_context'] == 'Current conversation direct human send_user_message_question_reply; not an automatic goal continuation or attached-file instruction'
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == proof['published_commit']
    assert protocol['prepared'] is True and protocol['authorized'] is protocol['executed'] is False
    assert protocol['phases']['link'] == dict(helper_seconds=180, outer_seconds=240)
    assert {Path(name).suffix.lower() for name in protocol['bindings']} <= {'.json', '.py', '.md', '.png', '.gif'}
    receipt_file = STAGE / 'link_launch.json'
    assert not receipt_file.exists() and not (STAGE / 'run_001').exists()
    assert not (STAGE / 'stop_requested.txt').exists() and not (STAGE / 'link_stdout.log').exists()
    receipt = dict(card='M-ALINK1', status='running', invocations=0,
        protocol_sha256=sha(protocol_file), approved_source_commit=proof['published_commit'],
        started_utc=datetime.now(timezone.utc).isoformat(),
        argv=[sys.executable, '-X', 'utf8', '-B', str(STAGE / 'execute_alpha_link.py'),
              '--repo', str(ROOT), '--protocol', str(protocol_file), '--time-limit', '180'],
        outer_seconds=240, sampled_RSS_limit_bytes=protocol['sampled_RSS_bytes'],
        budget_mode='Elapsed checkpoints and sampled tree RSS; cooperative stop, no OS hard cap or force')
    write(receipt_file, receipt)
    peak, reason, child, child_elapsed, unchanged, helper = 0, None, None, None, False, {}
    try:
        assert all(sha(ROOT / name) == pin for name, pin in protocol['bindings'].items())
        assert perf_counter() - STARTED <= 240 and not (STAGE / 'stop_requested.txt').exists()
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1')
        with (STAGE / 'link_stdout.log').open('xb') as output:
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
                if reason is None and (perf_counter() - STARTED > 240 or peak > protocol['sampled_RSS_bytes']):
                    reason = 'outer_elapsed_limit' if perf_counter() - STARTED > 240 else 'sampled_RSS_limit'
                    (STAGE / 'stop_requested.txt').write_text(reason, encoding='utf-8')
                sleep(.1)
        child_elapsed = perf_counter() - child_started
        unchanged = all(sha(ROOT / name) == pin for name, pin in protocol['bindings'].items())
        helper_file = ROOT / protocol['output_directory'] / 'execution_receipt.json'
        helper = read(helper_file) if helper_file.exists() else {}
        if reason is None and (child_elapsed > 180 or perf_counter() - STARTED > 240 or
                (STAGE / 'stop_requested.txt').exists()):
            reason = 'closed_resource_window_at_final_evidence'
        passed = child.returncode == 0 and reason is None and unchanged and helper.get('status') == 'pass'
        assert not passed or helper['calls'] == dict(saved_summary_started=1, saved_summary_completed=1,
            response_writes=1, index_writes=1)
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
        peak_sampled_tree_RSS_bytes=peak, stop_reason=reason, all_bindings_unchanged=unchanged,
        helper_status=helper.get('status'), completed_utc=datetime.now(timezone.utc).isoformat())
    write(receipt_file, receipt)
    if perf_counter() - STARTED > 240 or (STAGE / 'stop_requested.txt').exists():
        receipt.update(status='not_pass', elapsed_seconds=perf_counter() - STARTED,
            stop_reason='closed_resource_window_at_receipt_write')
        write(receipt_file, receipt)
    print(json.dumps({key: receipt[key] for key in
        ('status', 'invocations', 'exit_code', 'elapsed_seconds', 'peak_sampled_tree_RSS_bytes', 'stop_reason')}, ensure_ascii=False), flush=True)
    if receipt['status'] != 'pass':
        raise RuntimeError('M-ALINK1 closed non-success; no retry')


if __name__ == '__main__':
    main()
