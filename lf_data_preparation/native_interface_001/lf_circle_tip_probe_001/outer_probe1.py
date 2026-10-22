"""Unique outer supervisor and one byte-only seal inside the shared window."""
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import zipfile

from windows_owned_process_sup2 import run_owned

BASE = Path(__file__).resolve().parent
PROTOCOL = BASE / 'protocol.json'
protocol = json.loads(PROTOCOL.read_bytes())
assert protocol['status'] == 'frozen_ready_for_unique_authorized_launch'
assert not (BASE / 'root_outer_supervision.json').exists()
assert not (BASE / 'execution_evidence.zip').exists()
started = time.monotonic()
environment = os.environ.copy()
environment.update(protocol['cpu_thread_environment'])
environment['PYTHONDONTWRITEBYTECODE'] = '1'
environment['PROBE1_ROOT_START_MONOTONIC'] = repr(started)
record = run_owned(
    [protocol['python_executable'], '-X', 'utf8', '-B', str(BASE/'launch_probe1.py'),
     '--protocol', str(PROTOCOL)],
    cwd=str(BASE), env=environment, log=BASE/'root_outer.log',
    # Reserve five seconds after SUP2's own five-second cleanup for final
    # ordinary receipts/printing inside the original 4560-second ceiling.
    deadline=started+4550., seconds=4550., rss_limit=protocol['memory_limit_bytes'],
    instance_log_path=BASE/'root_outer.instances.ndjson',
    instance_identity={'stage': 'L-CTIPPROBE1', 'phase': 'outer4560'})

def write(name, value):
    with (BASE/name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')

write('root_outer_supervision.json', record)
proof = record.get('cleanup_proof', {})
outer_pass = (record['reason'] == 'normal_exit' and record['returncode'] == 0
              and record['cleanup_verified'] and proof.get('pass')
              and proof.get('job_handle_closed'))
seal = {'stage': 'L-CTIPPROBE1', 'status': 'not_started', 'attempts': 0,
        'scope': 'BASE exact files after outer cleanup, excluding archive/manifest/seal receipt themselves. No scientific NPZ decode.',
        'outer_pass': bool(outer_pass), 'shared_window_seconds': 4500,
        'scientific_retries': 0, 'extra_F_T_HP_tests_or_render_calls': 0}
if time.monotonic() >= started+4485.:
    seal['status'] = 'skipped_shared_window_not_open_with_sealing_margin'
else:
    seal['attempts'] = 1
    members = []
    excluded = {'execution_evidence.zip', 'EVIDENCE_MANIFEST.json', 'seal_receipt.json'}
    def check_seal_clock():
        if time.monotonic() >= started+4490.:
            raise RuntimeError('shared sealing window expired')
    try:
        paths = sorted(path for path in BASE.rglob('*')
                       if path.is_file() and path.relative_to(BASE).as_posix() not in excluded)
        with zipfile.ZipFile(BASE/'execution_evidence.zip', 'x', zipfile.ZIP_DEFLATED) as archive:
            for path in paths:
                check_seal_clock()
                data = path.read_bytes()
                name = path.relative_to(BASE).as_posix()
                archive.writestr(name, data)
                members.append({'path': name, 'bytes': len(data),
                                'sha256': hashlib.sha256(data).hexdigest()})
        check_seal_clock()
        data = (BASE/'execution_evidence.zip').read_bytes()
        manifest = {'stage': 'L-CTIPPROBE1', 'archive': {
            'path': 'execution_evidence.zip', 'bytes': len(data),
            'sha256': hashlib.sha256(data).hexdigest()}, 'members': members,
            'scope': seal['scope'], 'scientific_payloads_read_as_bytes_only': True}
        check_seal_clock()
        write('EVIDENCE_MANIFEST.json', manifest)
        seal['status'] = 'pass' if time.monotonic() < started+4500. else 'failed_shared_sealing_deadline'
        seal['members'] = len(members)
        seal['archive'] = manifest['archive']
    except Exception as error:
        seal['status'] = 'failed_once_no_retry'
        seal['error'] = {'type': type(error).__name__, 'message': str(error)}
        seal['members_written_before_error'] = len(members)
seal['elapsed_seconds_from_outer_start'] = time.monotonic()-started
write('seal_receipt.json', seal)
print(json.dumps({'outer_pass': bool(outer_pass), 'reason': record['reason'],
                  'returncode': record['returncode'], 'elapsed_seconds': record['elapsed_seconds'],
                  'seal_status': seal['status']}), flush=True)
sys.exit(0 if outer_pass and seal['status'] == 'pass' else 1)
