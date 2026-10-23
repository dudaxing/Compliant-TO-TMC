"""Bound FRESUME1 once, install measured bytes after cleanup, seal once."""
import time
START = time.monotonic()

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

BASE = Path(__file__).resolve().parent


def read(path):
    return json.loads(Path(path).read_bytes())


def write(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def identity(path):
    raw = Path(path).read_bytes()
    return dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def main():
    if len(sys.argv) != 1 or any((BASE/name).exists() for name in
            ('top_start.json', 'run_001', 'outer_start.json', 'execution_evidence.zip', 'root_qa.json')):
        raise ValueError('Unique original launch only; no alternate arguments or reopened output')
    write(BASE/'top_start.json', dict(stage='L-CTIPFRESUME1', start_monotonic=START,
        start_utc=datetime.now(timezone.utc).isoformat(), outer_seconds=720, helper_seconds=660,
        helper_clock_origin='outer_resume1 first monotonic stamp before other imports', execution_attempt=1))
    p = read(BASE/'protocol.json')
    if (p['stage'] != 'L-CTIPFRESUME1'
            or p['status'] != 'frozen_ready_for_unique_authorized_launch'
            or (p['helper_seconds'], p['outer_seconds'], p['tests_seconds'], p['viewer_seconds'])
                != (660, 720, 480, 60)
            or p['memory_limit_bytes'] != 8*1024**3
            or p['thread_environment'] != {key:'16' for key in
                ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS')}):
        raise ValueError('Frozen authorized resource contract differs before tree launch')
    for item in p['bindings']:
        if identity(item['path']) != {key:item[key] for key in ('bytes', 'sha256')}:
            raise ValueError('Frozen source changed: '+item['path'])
    from windows_owned_process_sup2 import run_owned
    from run_resume1 import passed, cleanup_passed
    env = os.environ.copy()
    env.update(p['thread_environment'])
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    outer = run_owned([p['python_executable'], '-X', 'utf8', '-B',
        str(BASE/'outer_resume1.py')], cwd=str(BASE), env=env, log=BASE/'outer.log',
        deadline=START+595., seconds=595., rss_limit=p['memory_limit_bytes'],
        instance_log_path=BASE/'outer.instances.ndjson',
        instance_identity=dict(stage='L-CTIPFRESUME1', phase='outer595_cleanup600_within720'))
    write(BASE/'top_supervision.json', outer)
    clean = cleanup_passed(outer)
    ok = passed(outer)
    origin = (read(BASE/'outer_start.json')['start_monotonic']
        if (BASE/'outer_start.json').exists() else None)
    installation = dict(stage='L-CTIPFRESUME1', status='not_started', installed=[],
        all_four_cleanup_proofs_required=True, automatic_rollback=False)
    if ok:
        try:
            def install_clock():
                if origin is None or time.monotonic() >= origin+610. or time.monotonic() >= START+720.:
                    raise TimeoutError('Original installation margin closed')
            install_clock()
            for path in (BASE/'outer_supervision.json', BASE/'run_001/tests_supervision.json',
                         BASE/'run_001/viewer_supervision.json'):
                if not passed(read(path)):
                    raise ValueError('An inner supervision proof did not pass')
            execution = read(BASE/'execution_receipt.json')
            helper = read(BASE/'run_001/helper_receipt.json')
            if (execution['status'] != 'pass' or execution['root_QA_accepted'] is not True
                    or helper['status'] != 'ready_for_root_visual_check'
                    or helper['test_items_passed'] != 12
                    or helper['actual_new_call_counts']['real_16cell_paths'] != 7
                    or not 0 <= helper['actual_new_call_counts']['finite_oracle_injection_rejection_calls'] <= 37):
                raise ValueError('Finite tests, scopes or one root QA are incomplete')
            root = Path(p['root_repository'])
            head = subprocess.check_output(['git', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false',
                'rev-parse', 'HEAD'], cwd=root).decode().strip()
            if head != p['baseline']:
                raise ValueError('Formal baseline changed; do not install')
            originals = {str(Path(item['path']).resolve()):item for item in p['original_production']}
            if len(originals) != 57:
                raise ValueError('Expected exactly 57 original production files')
            for item in originals.values():
                install_clock()
                if identity(item['path']) != {key:item[key] for key in ('bytes', 'sha256')}:
                    raise ValueError('Old production bytes changed; do not install')
            install = p['install_files']
            package = (root/'hf_repo/src/hf_eval').resolve()
            expected = {'split_guided_force.py':True, 'native_guided_force.py':True,
                        'native_guided_force_resume.py':False}
            if (len(install) != 3 or {Path(item['target']).name:item['existing'] for item in install} != expected
                    or any(Path(item['target']).resolve().parent != package for item in install)):
                raise ValueError('Installation is restricted to two replacements and one new module')
            for item in install:
                target = Path(item['target'])
                if (target.exists() != item['existing']
                        or (item['existing'] and str(target.resolve()) not in originals)
                        or identity(item['source']) != {key:item[key] for key in ('bytes', 'sha256')}):
                    raise ValueError('Install target history or tested candidate identity changed')
            replaced = {str(Path(item['target']).resolve()) for item in install if item['existing']}
            for item in install:
                install_clock()
                raw = Path(item['source']).read_bytes()
                if dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()) != {
                        key:item[key] for key in ('bytes', 'sha256')}:
                    raise ValueError('Loaded candidate bytes differ before installation')
                with Path(item['target']).open('wb' if item['existing'] else 'xb') as stream:
                    stream.write(raw)
                actual = identity(item['target'])
                installation['installed'].append(dict(path=item['target'], **actual))
                if actual != {key:item[key] for key in ('bytes', 'sha256')}:
                    raise ValueError('Installed bytes differ; preserve actual partial installation')
            for path, item in originals.items():
                install_clock()
                if path not in replaced and identity(path) != {key:item[key] for key in ('bytes', 'sha256')}:
                    raise ValueError('An unrelated original module changed; preserve actual installed bytes')
            install_clock()
            expected_sources = set(originals) | {str(Path(item['target']).resolve())
                for item in install if not item['existing']}
            actual_sources = {str(path.resolve()) for path in package.rglob('*.py')}
            if actual_sources != expected_sources or len(actual_sources) != 58:
                raise ValueError('Actual installed production source set differs; preserve actual bytes')
            if subprocess.check_output(['git', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false',
                    'rev-parse', 'HEAD'], cwd=root).decode().strip() != p['baseline']:
                raise ValueError('Formal baseline changed during installation; preserve actual bytes')
            install_clock()
            installation.update(status='pass', original_source_files_unchanged=55,
                original_files_replaced=2, new_files_installed=1, production_source_files_after=58,
                default_fixed_entry_semantics_preserved=True)
        except BaseException as error:
            ok = False
            installation.update(status='failed_no_rollback',
                error=dict(type=type(error).__name__, message=str(error)))
    installation['elapsed_helper_seconds'] = None if origin is None else time.monotonic()-origin
    write(BASE/'installation_receipt.json', installation)
    seal = dict(stage='L-CTIPFRESUME1', status='not_started', attempts=0, outer_pass=ok,
        scientific_payloads_read_as_bytes_only=True, numerical_retries=0)
    # A partial may be sealed only after all actually launched trees have an
    # explicit passing cleanup receipt.  Missing proof is not inferred safe.
    for path in (BASE/'outer_supervision.json', BASE/'run_001/tests_supervision.json'):
        clean = clean and path.exists() and cleanup_passed(read(path))
    helper_path = BASE/'run_001/helper_receipt.json'
    if not helper_path.exists():
        clean = False
    elif read(helper_path).get('viewer_process_launches', 0):
        path = BASE/'run_001/viewer_supervision.json'
        clean = clean and path.exists() and cleanup_passed(read(path))
    if clean and origin is not None and time.monotonic() < origin+620. and time.monotonic() < START+720.:
        members = []
        seal['attempts'] = 1
        try:
            excluded = {'execution_evidence.zip', 'EVIDENCE_MANIFEST.json', 'seal_receipt.json'}
            paths = sorted(path for path in BASE.rglob('*') if path.is_file()
                and path.relative_to(BASE).as_posix() not in excluded)
            with zipfile.ZipFile(BASE/'execution_evidence.zip', 'x', zipfile.ZIP_DEFLATED) as archive:
                for path in paths:
                    if time.monotonic() >= origin+645. or time.monotonic() >= START+710.:
                        raise TimeoutError('Original shared helper member-sealing deadline reached')
                    raw = path.read_bytes()
                    name = path.relative_to(BASE).as_posix()
                    archive.writestr(name, raw)
                    members.append(dict(path=name, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))
            if time.monotonic() >= origin+645. or time.monotonic() >= START+710.:
                raise TimeoutError('No original margin for archive identity and receipts')
            archived = identity(BASE/'execution_evidence.zip')
            if time.monotonic() >= origin+650. or time.monotonic() >= START+715.:
                raise TimeoutError('Archive identity consumed the original receipt margin')
            write(BASE/'EVIDENCE_MANIFEST.json', dict(stage='L-CTIPFRESUME1',
                archive=dict(path='execution_evidence.zip', **archived), members=members,
                scope='Stable original full/partial bytes after complete same-instance cleanup; no NPZ decoding'))
            seal.update(status='pass', archive=archived, members=len(members))
        except BaseException as error:
            seal.update(status='failed_once_no_retry',
                error=dict(type=type(error).__name__, message=str(error)),
                members_written_before_error=len(members))
    else:
        seal['status'] = 'skipped_cleanup_unproven_or_original_helper_window_closed'
    seal.update(elapsed_outer_seconds=time.monotonic()-START,
        elapsed_helper_seconds=None if origin is None else time.monotonic()-origin)
    if seal['status'] == 'pass' and (seal['elapsed_helper_seconds'] >= 660
            or seal['elapsed_outer_seconds'] >= 720):
        seal['status'] = 'failed_original_window_exceeded'
    write(BASE/'seal_receipt.json', seal)
    within_window = (origin is not None and time.monotonic() < origin+660.
        and time.monotonic() < START+720.)
    print(json.dumps(dict(outer_pass=ok, reason=outer['reason'], returncode=outer['returncode'],
        installation=installation['status'], seal_status=seal['status'],
        all_receipts_within_original_windows=within_window,
        elapsed=time.monotonic()-START)), flush=True)
    return 0 if ok and installation['status'] == 'pass' and seal['status'] == 'pass' and within_window else 1


if __name__ == '__main__':
    raise SystemExit(main())
