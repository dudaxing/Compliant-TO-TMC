"""Own the original FRESUME1 helper clock and its single root PNG check."""
import time
START = time.monotonic()

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import traceback

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


def clock(deadline, label):
    if time.monotonic() >= deadline:
        raise TimeoutError('Original FRESUME1 window closed: '+label)


def main():
    if len(sys.argv) != 1 or RUN.exists() or (BASE/'outer_start.json').exists():
        raise ValueError('Unique original helper only; no alternate arguments or reopened output')
    write(BASE/'outer_start.json', dict(stage='L-CTIPFRESUME1', start_monotonic=START,
        start_utc=datetime.now(timezone.utc).isoformat(), helper_seconds=660,
        outer_seconds=720, execution_attempt=1, external_retries=0))
    RUN.mkdir()
    receipt = dict(stage='L-CTIPFRESUME1', status='not_pass', root_QA_accepted=False,
        numerical_retries=0, installation_owner='launch_resume1_after_all_four_cleanup_proofs',
        archive_owner='launch_resume1_after_complete_tree_cleanup')
    try:
        p = read(BASE/'protocol.json')
        if (p['stage'] != 'L-CTIPFRESUME1'
                or p['status'] != 'frozen_ready_for_unique_authorized_launch'
                or (p['helper_seconds'], p['outer_seconds'], p['tests_seconds'], p['viewer_seconds'])
                    != (660, 720, 480, 60)
                or p['memory_limit_bytes'] != 8*1024**3
                or p['thread_environment'] != {key:'16' for key in
                    ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS')}):
            raise ValueError('Frozen authorized resource contract differs')
        for item in p['bindings']:
            if identity(item['path']) != {key:item[key] for key in ('bytes', 'sha256')}:
                raise ValueError('Frozen byte mismatch: '+item['path'])
        clock(START+20., 'bootstrap')
        from windows_owned_process_sup2 import run_owned
        from run_resume1 import passed
        env = os.environ.copy()
        env.update(p['thread_environment'])
        env.update(PYTHONDONTWRITEBYTECODE='1', FRESUME1_HELPER_START=repr(START))
        supervised = run_owned([p['python_executable'], '-X', 'utf8', '-B',
            str(BASE/'run_resume1.py')], cwd=str(BASE), env=env, log=RUN/'helper.log',
            deadline=START+565., seconds=565., rss_limit=p['memory_limit_bytes'],
            instance_log_path=RUN/'helper.instances.ndjson',
            instance_identity=dict(stage='L-CTIPFRESUME1', phase='content565_cleanup570'))
        write(BASE/'outer_supervision.json', supervised)
        clock(START+570., 'helper process plus same-instance cleanup')
        if not passed(supervised):
            raise RuntimeError('Finite helper or its complete same-instance cleanup did not pass')
        helper = read(RUN/'helper_receipt.json')
        display = read(RUN/'display_start.json')
        if helper['status'] != 'ready_for_root_visual_check':
            raise ValueError('Finite helper did not complete tests and display')
        display_begin = display['start_monotonic']
        qa_deadline = min(display_begin+55., START+580.)
        print(json.dumps(dict(phase='ready_for_root_visual_check',
            image=str(RUN/'view/force_resume.png'), root_QA_deadline_monotonic=qa_deadline,
            elapsed_helper_seconds=time.monotonic()-START)), flush=True)
        while not (BASE/'root_qa.json').exists():
            clock(qa_deadline, 'one root PNG inspection')
            time.sleep(.1)
        clock(qa_deadline, 'before reading root QA')
        qa = read(BASE/'root_qa.json')
        png = identity(RUN/'view/force_resume.png')
        # Reading the marker and hashing the image must not escape either the
        # original shared display interval or the original helper deadline.
        clock(qa_deadline, 'after reading root QA and image identity')
        if (qa['status'] != 'pass' or qa['pixel_inspections'] != 1
                or qa['image_identity'] != png or qa['scientific_calls'] != 0
                or qa['rerenders'] != 0):
            raise ValueError('One original PNG check did not pass')
        receipt.update(root_QA_accepted=True, root_QA=qa,
            shared_display_elapsed_seconds=time.monotonic()-display_begin)
        clock(min(display_begin+60., START+585.), 'display completion and outer return')
        receipt['status'] = 'pass'
    except BaseException as error:
        receipt['error'] = dict(type=type(error).__name__, message=str(error),
            traceback=traceback.format_exc())
    finally:
        receipt['elapsed_helper_seconds'] = time.monotonic()-START
        write(BASE/'execution_receipt.json', receipt)
        print(json.dumps(dict(status=receipt['status'], installed_by_this_child=0,
            elapsed_helper_seconds=receipt['elapsed_helper_seconds'])), flush=True)
    return 0 if receipt['status'] == 'pass' and time.monotonic() < START+590. else 1


if __name__ == '__main__':
    raise SystemExit(main())
