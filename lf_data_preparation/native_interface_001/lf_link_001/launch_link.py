"""L-LINK1 one-child launcher; direct approved metadata window, cooperative stop only."""
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
    protocol_file = STAGE/'protocol.json'
    protocol = read(protocol_file)
    authorization, reply, proof = (read(STAGE/'author'/name) for name in
        ('authorization.json','direct_human_reply.json','source_publication_receipt.json'))
    assert authorization['authorized'] is True and authorization['one_invocation'] is True
    assert authorization['authorization_from_direct_human_reply'] is reply['authorization_from_direct_human_reply'] is True
    assert authorization['card'] == reply['card'] == proof['prepared_card'] == protocol['card'] == 'L-LINK1'
    assert protocol['schema_version'] == 'lf-selected-reference-linked-delivery-card-1.0'
    assert authorization['authorized_execution_source_commit'] == reply['authorized_execution_source_commit'] == proof['published_commit']
    assert proof['status'] == 'published_and_incrementally_restored_pass'
    assert authorization['protocol_sha256'] == proof['protocol_sha256'] == sha(protocol_file)
    assert authorization['human_evidence_sha256'] == sha(STAGE/'author/direct_human_reply.json')
    assert authorization['source_publication_receipt_sha256'] == sha(STAGE/'author/source_publication_receipt.json')
    assert authorization['direct_human_answer'] == reply['direct_human_answer'] and reply['direct_human_answer'].strip()
    assert reply['reply_context']
    assert subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT).decode().strip() == proof['published_commit']
    assert protocol['prepared'] is True and protocol['authorized'] is protocol['executed'] is False
    helper_limit, outer_limit = (protocol['phases']['link'][name] for name in ('helper_seconds','outer_seconds'))
    assert helper_limit == authorization['helper_seconds'] == 180
    assert outer_limit == authorization['outer_seconds'] == 240
    assert protocol['phases']['link']['tests_seconds'] == 60
    assert protocol['sampled_RSS_bytes'] == authorization['sampled_RSS_bytes'] == 8*1024**3
    assert {Path(name).suffix.lower() for name in protocol['bindings']} <= {'.json','.py','.md','.png','.gif'}
    before = protocol['source_before_installation']
    assert before['path'] == 'hf_repo/src/hf_eval/native_response.py' and before['path'] not in protocol['bindings']
    assert sha(ROOT/before['path']) == before['sha256']
    receipt_file, output_dir = STAGE/'link_launch.json', ROOT/protocol['output_directory']
    assert not receipt_file.exists() and not output_dir.exists()
    assert not (STAGE/'stop_requested.txt').exists() and not (STAGE/'link_stdout.log').exists()
    expected_argv = [str(STAGE.relative_to(ROOT)/'execute_lf_link.py'),'--repo','.',
        '--protocol',str(STAGE.relative_to(ROOT)/'protocol.json'),'--time-limit','180']
    assert protocol['phases']['link']['argv'] == [arg.replace('\\','/') for arg in expected_argv]
    receipt = dict(card='L-LINK1', status='running', invocations=0,
        protocol_sha256=sha(protocol_file), authorized_execution_source_commit=proof['published_commit'],
        started_utc=datetime.now(timezone.utc).isoformat(),
        argv=[sys.executable,'-X','utf8','-B',str(STAGE/'execute_lf_link.py'),
            '--repo',str(ROOT),'--protocol',str(protocol_file),'--time-limit',str(helper_limit)],
        outer_seconds=outer_limit, sampled_RSS_limit_bytes=protocol['sampled_RSS_bytes'],
        budget_mode='Earliest elapsed checkpoints and sampled tree RSS; cooperative stop and actual child wait, no OS hard cap or force')
    write(receipt_file, receipt)
    peak, reason, child, child_elapsed, unchanged, helper = 0, None, None, None, False, {}
    actual_default = before['sha256']
    try:
        for name, pin in protocol['bindings'].items():
            assert perf_counter()-STARTED <= outer_limit and not (STAGE/'stop_requested.txt').exists()
            assert sha(ROOT/name) == pin
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1')
        with (STAGE/'link_stdout.log').open('xb') as output:
            receipt['invocations'] = 1; write(receipt_file, receipt)
            child_started = perf_counter()
            child = subprocess.Popen(receipt['argv'], cwd=ROOT, env=environment, stdout=output, stderr=subprocess.STDOUT)
            process = psutil.Process(child.pid)
            while child.poll() is None:
                try:
                    peak = max(peak, sum(member.memory_info().rss for member in
                        [process]+process.children(recursive=True) if member.is_running()))
                except psutil.NoSuchProcess:
                    pass
                if reason is None and (perf_counter()-STARTED > outer_limit or peak > protocol['sampled_RSS_bytes']):
                    reason = 'outer_elapsed_limit' if perf_counter()-STARTED > outer_limit else 'sampled_RSS_limit'
                    (STAGE/'stop_requested.txt').write_text(reason, encoding='utf-8')
                sleep(.1)
        child_elapsed = perf_counter()-child_started
        if child_elapsed > helper_limit or perf_counter()-STARTED > outer_limit or (STAGE/'stop_requested.txt').exists():
            reason = reason or 'closed_resource_window_before_final_identity'
        if reason is None:
            unchanged = True
            for name, pin in protocol['bindings'].items():
                if perf_counter()-STARTED > outer_limit:
                    reason = 'closed_resource_window_during_final_identity'; unchanged = False; break
                if sha(ROOT/name) != pin:
                    unchanged = False; break
        helper_file = output_dir/'execution_receipt.json'
        helper = read(helper_file) if helper_file.exists() else {}
        actual_default = sha(ROOT/before['path'])
        passed = (child.returncode == 0 and reason is None and unchanged and helper.get('status') == 'pass'
            and helper.get('output_identity_seal') == 'complete_inside_original_helper_window'
            and helper.get('installation_complete') is True
            and actual_default == helper.get('actual_default_SHA256') == protocol['bindings'][protocol['candidate_source']])
        assert not passed or (helper['unit_tests_run'] == 16 and helper['unit_reference_calls'] == 23
            and helper['calls'] == dict(tests_started=1,tests_completed=1,saved_summary_started=1,
                saved_summary_completed=1,response_writes=1,index_writes=1,
                installation_started=1,installation_completed=1))
        receipt['status'] = 'pass' if passed else 'not_pass'
    except BaseException as error:
        receipt.update(status='not_pass', failure=dict(type=type(error).__name__, message=str(error)))
        if child is not None and child.poll() is None:
            reason = reason or 'launcher_observation_error'
            try:
                (STAGE/'stop_requested.txt').write_text(reason, encoding='utf-8')
            finally:
                child.wait()
            child_elapsed = perf_counter()-child_started
        actual_default = sha(ROOT/before['path'])
    receipt.update(exit_code=child.returncode if child is not None else None,
        elapsed_seconds=perf_counter()-STARTED, child_terminal_wall_seconds=child_elapsed,
        peak_sampled_tree_RSS_bytes=peak, stop_reason=reason, all_bindings_unchanged=unchanged,
        helper_status=helper.get('status'), installation_complete=helper.get('installation_complete', False),
        actual_default_SHA256=actual_default, completed_utc=datetime.now(timezone.utc).isoformat())
    write(receipt_file, receipt)
    if perf_counter()-STARTED > outer_limit or (STAGE/'stop_requested.txt').exists():
        receipt.update(status='not_pass', elapsed_seconds=perf_counter()-STARTED,
            stop_reason='closed_resource_window_at_receipt_write'); write(receipt_file, receipt)
    print(json.dumps({key:receipt[key] for key in ('status','invocations','exit_code',
        'elapsed_seconds','peak_sampled_tree_RSS_bytes','stop_reason','installation_complete')}, ensure_ascii=False), flush=True)
    if receipt['status'] != 'pass':
        raise RuntimeError('L-LINK1 closed non-success; no retry or rollback')


if __name__ == '__main__':
    main()
