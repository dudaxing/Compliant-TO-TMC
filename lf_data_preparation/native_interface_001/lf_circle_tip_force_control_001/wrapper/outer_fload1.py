"""Unique FLOAD1 helper clock, validation/display and one root QA."""
import time
START=time.monotonic()

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import traceback

BASE=Path(__file__).resolve().parent
RUN=BASE/'run_001'

def read(path):
    return json.loads(Path(path).read_bytes())

def write(path,value):
    with Path(path).open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False)
        stream.write('\n')

def identity(path):
    raw=Path(path).read_bytes()
    return dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())

def clock(offset,label):
    if time.monotonic()>=START+offset:
        raise TimeoutError('Original FLOAD1 window closed: '+label)

def main():
    if len(sys.argv)!=1:
        raise ValueError('No alternate arguments or protocols')
    if RUN.exists() or (BASE/'outer_start.json').exists():
        raise FileExistsError('Preserve original attempt; cannot reopen unique window')
    write(BASE/'outer_start.json',dict(stage='L-CTIPFLOAD1',start_monotonic=START,
        start_utc=datetime.now(timezone.utc).isoformat(),helper_seconds=480,outer_seconds=540,
        execution_attempt=1,external_retries=0))
    RUN.mkdir()
    record=dict(stage='L-CTIPFLOAD1',status='not_pass',numerical_retries=0,
        installation_owner='launch_fload1_after_all_four_cleanup_proofs',
        archive_owner='launch_fload1_after_outer_cleanup',root_QA_accepted=False)
    cleanup_proven=False
    try:
        p=read(BASE/'protocol.json')
        if (p['status']!='frozen_ready_for_unique_authorized_launch'
                or p['helper_seconds']!=480 or p['outer_seconds']!=540
                or p['tests_seconds']!=300 or p['viewer_seconds']!=60
                or p['memory_limit_bytes']!=8*1024**3
                or p['thread_environment']!={k:'16' for k in
                    ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')}):
            raise ValueError('Frozen authorized resource contract differs')
        for item in p['bindings']:
            if identity(item['path'])!={k:item[k] for k in ('bytes','sha256')}:
                raise ValueError('Frozen byte mismatch: '+item['path'])
        clock(20,'bootstrap')
        from windows_owned_process_sup2 import run_owned
        from run_fload1 import passed
        env=os.environ.copy()
        env.update(p['thread_environment'])
        env.update(PYTHONDONTWRITEBYTECODE='1',FLOAD1_ROOT_START=repr(START))
        supervised=run_owned([p['python_executable'],'-X','utf8','-B',str(BASE/'run_fload1.py')],
            cwd=str(BASE),env=env,log=RUN/'helper.log',deadline=START+410.,seconds=410.,
            rss_limit=p['memory_limit_bytes'],instance_log_path=RUN/'helper.instances.ndjson',
            instance_identity=dict(stage='L-CTIPFLOAD1',phase='original_shared_helper'))
        write(BASE/'outer_supervision.json',supervised)
        cleanup_proven=(supervised.get('cleanup_verified') is True
            and supervised.get('cleanup_proof',{}).get('pass') is True
            and supervised.get('cleanup_proof',{}).get('job_handle_closed') is True)
        if not passed(supervised):
            raise RuntimeError('Helper or its complete same-instance cleanup failed')
        helper=read(RUN/'helper_receipt.json')
        if helper['status']!='ready_for_root_visual_check':
            raise ValueError('Helper did not complete finite tests/display')
        print(json.dumps(dict(phase='ready_for_root_visual_check',
            image=str(RUN/'view/force_control.png'),root_QA_deadline_seconds=440,
            elapsed=time.monotonic()-START)),flush=True)
        # The agent may inspect the one new image and supply one ordinary QA
        # receipt; this does not open another numerical or resource window.
        while not (BASE/'root_qa.json').exists():
            clock(440,'one root PNG inspection')
            time.sleep(.1)
        qa=read(BASE/'root_qa.json')
        png=identity(RUN/'view/force_control.png')
        if (qa['status']!='pass' or qa['pixel_inspections']!=1
                or qa['image_identity']!=png or qa['scientific_calls']!=0):
            raise ValueError('One original PNG inspection did not pass')
        record['root_QA_accepted']=True
        clock(445,'root QA and return for final outer cleanup')
        record['status']='pass'
    except BaseException as error:
        record['error']=dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc())
    finally:
        record['elapsed_before_seal_seconds']=time.monotonic()-START
        write(BASE/'execution_receipt.json',record)
        print(json.dumps(dict(status=record['status'],archive_owner=record['archive_owner'],
            installed_by_this_child=0,elapsed=time.monotonic()-START)),flush=True)
    return 0 if record['status']=='pass' and time.monotonic()<START+450. else 1

if __name__=='__main__':
    raise SystemExit(main())
