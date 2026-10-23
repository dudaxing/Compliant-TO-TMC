"""Unique finite validation and one display; HF imports occur only in pytest."""
import time
START = time.monotonic()

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import traceback
import xml.etree.ElementTree as ET

from windows_owned_process_sup2 import run_owned

BASE = Path(__file__).resolve().parent
RUN = BASE/'run_001'


def read(path):
    return json.loads(Path(path).read_bytes())


def write(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def identity(path):
    raw = Path(path).read_bytes()
    return dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def cleanup_passed(row):
    proof = row.get('cleanup_proof', {})
    return (row.get('cleanup_verified') is True and proof.get('pass') is True
            and proof.get('job_handle_closed') is True)


def passed(row):
    return (row.get('reason') == 'normal_exit' and row.get('returncode') == 0
            and cleanup_passed(row))


def main():
    if len(sys.argv) != 1:
        raise ValueError('No alternate arguments or reopened execution')
    origin = float(os.environ['FRESUME1_HELPER_START'])
    p = read(BASE/'protocol.json')
    env = os.environ.copy()
    env.update(PYTHONPATH=p['candidate_source'], PYTHONDONTWRITEBYTECODE='1',
        PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', JAX_ENABLE_X64='true', JAX_PLATFORMS='cpu',
        MPLBACKEND='Agg', FRESUME_ARTIFACT_DIR=str(RUN/'artifacts'))
    env.update(p['thread_environment'])
    receipt = dict(stage='L-CTIPFRESUME1', status='not_pass', execution_attempt=1,
        start_monotonic=START, start_utc=datetime.now(timezone.utc).isoformat(),
        test_process_launches=0, viewer_process_launches=0, external_retries=0,
        new_HP=0, scientific_calls_by_helper=0, production_installations=0)
    try:
        # Reserve the complete 480 tests + 60 shared display interval, not just
        # the expected run time.  Tests cannot consume the display allowance.
        if time.monotonic()+480.+60. >= origin+565.:
            raise TimeoutError('Insufficient original helper reserve for tests and shared display')
        tests_begin = time.monotonic()
        receipt['test_process_launches'] = 1
        tests = run_owned(p['test_command'], cwd=p['candidate_hf_repo'], env=env,
            log=RUN/'pytest.log', deadline=tests_begin+465., seconds=465.,
            rss_limit=p['memory_limit_bytes'], instance_log_path=RUN/'tests.instances.ndjson',
            instance_identity=dict(stage='L-CTIPFRESUME1', phase='tests465_within_shared480'))
        write(RUN/'tests_supervision.json', tests)
        if time.monotonic() >= tests_begin+480. or not passed(tests):
            raise RuntimeError('Unique tests or their original 480-second cleanup interval failed')
        cases = ET.parse(RUN/'pytest.xml').findall('.//testcase')
        if len(cases) != 12 or any(case.find(name) is not None for case in cases
                for name in ('failure', 'error', 'skipped')):
            raise ValueError('Expected exactly 12 passing, unskipped pytest items')
        summary = read(RUN/'artifacts/validation_summary.json')
        counts = summary['counts']
        if (summary['all_twelve_methods_passed'] is not True or summary['expected_methods'] != 12
                or summary['passed_methods'] != [f'V{index:02d}' for index in range(1, 13)]
                or counts['real_16cell_paths'] != 7
                or not 0 <= counts['finite_oracle_injection_rejection_calls'] <= 37
                or counts['controlled_partial_counted_on_both_axes'] != 1):
            raise ValueError('Finite validation summary/counts differ from the frozen contract')
        paths = summary['paths']
        if (set(paths) != {'reference', 'direct', 'prefix', 'child', 'grandchild', 'partial'}
                or any(paths[name]['status'] != 'success' for name in paths if name != 'partial')
                or paths['partial']['status'] != 'failed'
                or paths['partial']['failure']['code'] != 'constraint_failure'
                or paths['partial']['accepted_count'] < 1):
            raise ValueError('Actual path outcomes differ from the successful/controlled-partial contract')
        for branch in paths.values():
            pin = branch['result']
            if identity(pin['path']) != {key:pin[key] for key in ('bytes', 'sha256')}:
                raise ValueError('An actual finite-path ordinary result identity differs')
        receipt.update(test_items_passed=len(cases), actual_new_call_counts=counts,
            validation_summary=dict(path=str(RUN/'artifacts/validation_summary.json'),
                **identity(RUN/'artifacts/validation_summary.json')),
            tests_elapsed_seconds=time.monotonic()-tests_begin)
        if time.monotonic()+60. >= origin+565.:
            raise TimeoutError('Insufficient original helper reserve for the full shared display interval')
        display_begin = time.monotonic()
        write(RUN/'display_start.json', dict(stage='L-CTIPFRESUME1',
            start_monotonic=display_begin, helper_start_monotonic=origin,
            shared_seconds=60, viewer_process_seconds=35, viewer_cleanup_reserve_seconds=10,
            root_QA_before_monotonic=min(display_begin+55., origin+580.),
            image=str(RUN/'view/force_resume.png')))
        receipt['viewer_process_launches'] = 1
        viewer = run_owned([p['python_executable'], '-X', 'utf8', '-B',
            str(BASE/'render_resume1.py')], cwd=str(BASE), env=env, log=RUN/'viewer.log',
            deadline=display_begin+35., seconds=35., rss_limit=p['memory_limit_bytes'],
            instance_log_path=RUN/'viewer.instances.ndjson',
            instance_identity=dict(stage='L-CTIPFRESUME1', phase='viewer35_within_shared60'))
        write(RUN/'viewer_supervision.json', viewer)
        if time.monotonic() >= display_begin+45. or not passed(viewer):
            raise RuntimeError('Unique viewer or its original 45-second process/cleanup interval failed')
        rendered = read(RUN/'view/renderer_receipt.json')
        if (rendered['new_png_count'] != 1 or rendered['scientific_calls'] != 0
                or rendered.get('rerenders', 0) != 0):
            raise ValueError('Pure display scope differs from the authorized one-PNG renderer')
        if time.monotonic() >= min(display_begin+50., origin+565.):
            raise TimeoutError('No original reserve remains for root QA and helper cleanup')
        receipt.update(status='ready_for_root_visual_check', renderer=rendered,
            display_start_monotonic=display_begin,
            next_action='One root PNG inspection within the same display interval; no science or rerender.')
    except BaseException as error:
        receipt['error'] = dict(type=type(error).__name__, message=str(error),
            traceback=traceback.format_exc())
    finally:
        receipt['elapsed_since_helper_origin_seconds'] = time.monotonic()-origin
        receipt['elapsed_process_seconds'] = time.monotonic()-START
        write(RUN/'helper_receipt.json', receipt)
        print(json.dumps(dict(status=receipt['status'],
            elapsed=receipt['elapsed_since_helper_origin_seconds'])), flush=True)
    return 0 if receipt['status'] == 'ready_for_root_visual_check' else 1


if __name__ == '__main__':
    raise SystemExit(main())
