"""Launch L-CLOCAL1 once under the frozen SUP2 owned-Job cleanup contract."""
from time import monotonic
STARTED = monotonic()
from datetime import datetime, timezone
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

STAGE = Path(__file__).resolve().parent
ROOT = STAGE.parents[2]
CARD = 'L-CLOCAL1'
BASE = 'e30d1024d0e8f1f5c03cbe1752cbd03baf5e70a6'
SUPERVISOR = 'hf_repo/scripts/windows_owned_process_sup2.py'
read = lambda path: json.loads(path.read_bytes())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n',
                    encoding='utf-8', newline='\n')


def main():
    protocol_raw = (STAGE / 'protocol.json').read_bytes()
    protocol, auth = json.loads(protocol_raw), read(STAGE / 'author/authorization.json')
    assert auth['authorized'] is auth['authorization_from_direct_human_request'] is auth['one_invocation'] is True
    assert auth['card'] == protocol['card'] == CARD
    assert auth['approval_card'] == CARD
    assert isinstance(auth['direct_human_request'], str) and auth['direct_human_request'].strip()
    assert auth['protocol_sha256'] == sha256(protocol_raw).hexdigest()
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == auth['authorized_execution_source_commit'] == protocol['source_baseline_commit']
    assert protocol['source_baseline_commit'] == BASE
    assert protocol['output_directory'] == 'lf_data_preparation/native_interface_001/lf_circle_local_001/run_001'
    assert (protocol['helper_seconds'], protocol['outer_seconds'], protocol['sampled_RSS_bytes']) == (180, 240, 8 * 1024**3)
    output = ROOT / protocol['output_directory']
    receipt_file = STAGE / 'local_launch.json'
    log_file = STAGE / 'local_stdout.log'
    instance_file = STAGE / 'local_instances.ndjson'
    assert not any(path.exists() for path in (output, receipt_file, log_file, instance_file, STAGE / 'stop_requested.txt'))
    for name, pin in protocol['source_bindings'].items():
        path = ROOT / name
        assert path.suffix.lower() in ('.py', '.json', '.md', '.toml', '.txt'), name
        assert sha256(path.read_bytes()).hexdigest() == pin, name
    # The three saved NPZ bindings belong only to the helper's
    # unique authorized window. This launcher never opens input_bindings.
    supervisor_file = ROOT / SUPERVISOR
    supervisor_pin = protocol['source_bindings'][SUPERVISOR]
    cwd = Path(protocol['working_directory']).resolve()
    assert cwd.is_dir() and not cwd.is_relative_to(ROOT)
    spec = importlib.util.spec_from_file_location('_L_CLOCAL1_frozen_SUP2', supervisor_file)
    supervisor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(supervisor)
    assert Path(supervisor.__file__).resolve() == supervisor_file.resolve()
    argv = [sys.executable, '-X', 'utf8', '-B', str(STAGE / 'execute_local.py')]
    receipt = dict(card=CARD, status='running', invocations=0, argv=argv, working_directory=str(cwd),
        protocol_sha256=auth['protocol_sha256'], authorized_execution_source_commit=auth['authorized_execution_source_commit'],
        started_utc=datetime.now(timezone.utc).isoformat(), helper_seconds=180, outer_seconds=240,
        sampled_RSS_limit_bytes=8 * 1024**3,
        source_preflight_scope='Pinned ordinary source bytes only; input_bindings not opened',
        supervisor_source=dict(path=SUPERVISOR, sha256=supervisor_pin),
        resource_mode='SUP2 sampled RSS and elapsed limits; original fixed five-second owned-Job cleanup included in outer, no extra process-control fallback',
        planned_default_installations=0, new_tests=0)
    write(receipt_file, receipt)
    supervision, helper = {}, {}
    try:
        now = monotonic()
        remaining = protocol['outer_seconds'] - (now - STARTED)
        assert remaining > 0
        receipt['invocations'] = 1
        write(receipt_file, receipt)
        supervision = supervisor.run_owned(argv, cwd=str(cwd),
            env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1', PYTHONUNBUFFERED='1', MPLBACKEND='Agg'),
            log=log_file, deadline=now + remaining, seconds=180,
            rss_limit=8 * 1024**3, instance_log_path=instance_file,
            instance_identity=dict(card=CARD, protocol_sha256=auth['protocol_sha256'],
                source_baseline_commit=protocol['source_baseline_commit']),
            telemetry_path=None)
        receipt['supervision'] = supervision
        helper_file = output / 'execution_receipt.json'
        helper = read(helper_file) if helper_file.exists() else {}
        passed = (supervision.get('reason') == 'normal_exit' and supervision.get('returncode') == 0
            and supervision.get('cleanup_verified') is True
            and supervision.get('protocol') == 'F-CPU-CLEAN1'
            and supervision.get('cleanup_contract') == 'CPU-CLEAN1'
            and supervision.get('supervisor_sha256') == supervisor_pin
            and helper.get('status') == 'pass'
            and helper.get('output_identity_seal') == 'complete_inside_original_helper_window'
            and monotonic() - STARTED <= protocol['outer_seconds'])
        receipt['status'] = 'pass' if passed else 'not_pass'
    except BaseException as error:
        receipt.update(status='not_pass', error=dict(type=type(error).__name__, message=str(error)))
    elapsed = monotonic() - STARTED
    if elapsed > protocol['outer_seconds']:
        receipt['status'] = 'not_pass'
    receipt.update(exit_code=supervision.get('returncode'), elapsed_seconds=elapsed,
        elapsed_scope='Earliest launcher clock through SUP2 cleanup and helper receipt read; before final launcher receipt write',
        owned_supervision_elapsed_seconds=supervision.get('elapsed_seconds'),
        peak_sampled_tree_RSS_bytes=supervision.get('peak_tree_rss_bytes'), rss_scope=supervision.get('rss_scope'),
        cleanup_verified=supervision.get('cleanup_verified'),
        stop_reason=None if supervision.get('reason') == 'normal_exit' else supervision.get('reason'),
        helper_status=helper.get('status'), completed_utc=datetime.now(timezone.utc).isoformat())
    write(receipt_file, receipt)
    print(json.dumps({key: receipt[key] for key in ('status', 'invocations', 'exit_code', 'elapsed_seconds',
        'peak_sampled_tree_RSS_bytes', 'cleanup_verified', 'stop_reason')}), flush=True)
    if receipt['status'] != 'pass':
        raise RuntimeError('L-CLOCAL1 closed not_pass; no retry or additional process cleanup')


if __name__ == '__main__':
    main()
