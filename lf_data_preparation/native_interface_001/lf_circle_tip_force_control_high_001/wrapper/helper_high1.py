"""One continuous helper: science, endpoint comparison, pure display, root QA."""
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
def read(path): return json.loads(Path(path).read_bytes())
def write(path,row):
    with Path(path).open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(row,stream,ensure_ascii=False,indent=2,allow_nan=False); stream.write('\n')
def identity(path):
    raw=Path(path).read_bytes()
    return dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def passed(row):
    proof=row.get('cleanup_proof',{})
    return (row.get('reason')=='normal_exit' and row.get('returncode')==0
        and row.get('cleanup_verified') is True and proof.get('pass') is True
        and proof.get('job_handle_closed') is True)
def clock(offset,label):
    if time.monotonic()>=START+offset:
        raise TimeoutError('Original helper window closed: '+label)
def reserve(seconds,label):
    if time.monotonic()+seconds>=START+4700:
        raise TimeoutError('Insufficient complete original reserve: '+label)

def main():
    if len(sys.argv)!=1 or RUN.exists() or (BASE/'helper_start.json').exists():
        raise FileExistsError('One original helper only; cannot reopen output')
    write(BASE/'helper_start.json',dict(stage='L-CTIPFHIGH1',start_monotonic=START,
        started_utc=datetime.now(timezone.utc).isoformat(),helper_seconds=4800,
        outer_seconds=4860,execution_attempt=1,external_retries=0))
    RUN.mkdir()
    receipt=dict(stage='L-CTIPFHIGH1',status='not_pass',science_launches=0,comparison_launches=0,
        viewer_launches=0,root_QA_accepted=False,production_modifications=0,new_tests=0,new_HP=0,
        archive_owner='top after all four complete same-instance cleanup proofs')
    try:
        p=read(BASE/'protocol.json')
        for row in p['bindings']:
            if identity(row['path'])!={k:row[k] for k in ('bytes','sha256')}:
                raise ValueError('Frozen byte mismatch: '+row['path'])
        clock(20,'ordinary bootstrap')
        from windows_owned_process_sup2 import run_owned
        env=os.environ.copy()
        env.update(p['thread_environment'])
        env.update(PYTHONPATH=p['production_src'],PYTHONDONTWRITEBYTECODE='1',
            JAX_PLATFORMS='cpu',JAX_ENABLE_X64='true',MPLBACKEND='Agg',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
        def owned(script,phase,seconds,memory):
            return run_owned([p['python_executable'],'-X','utf8','-B',str(BASE/script)],
                cwd=str(BASE),env=env,log=RUN/(phase+'.log'),
                deadline=time.monotonic()+seconds,seconds=seconds,rss_limit=memory,
                instance_log_path=RUN/(phase+'.instances.ndjson'),
                instance_identity=dict(stage='L-CTIPFHIGH1',phase=phase))
        reserve(3900+60+600+15,'full science3900/comparison60/display600')
        begin=time.monotonic(); receipt['science_launches']=1
        supervised=owned('science_high1.py','science',3885,p['memory_limit_bytes'])
        write(RUN/'science_supervision.json',supervised)
        receipt['science_stage_seconds']=time.monotonic()-begin
        if not passed(supervised) or receipt['science_stage_seconds']>3900:
            raise RuntimeError('Science process, complete cleanup or science3900 budget did not pass')
        if read(RUN/'science_receipt.json')['status']!='pass':
            raise RuntimeError('Science did not complete the original two-load task')
        reserve(60+600+15,'full comparison60/display600')
        begin=time.monotonic(); receipt['comparison_launches']=1
        supervised=owned('compare_high1.py','comparison',45,p['memory_limit_bytes'])
        write(RUN/'comparison_supervision.json',supervised)
        receipt['comparison_stage_seconds']=time.monotonic()-begin
        if not passed(supervised) or receipt['comparison_stage_seconds']>60:
            raise RuntimeError('Comparison, cleanup or comparison60 budget did not pass')
        if read(RUN/'comparison.json')['status']!='pass':
            raise RuntimeError('Endpoint comparison did not pass; retain original science status')
        reserve(600+15,'complete shared display/root QA600')
        display_begin=time.monotonic()
        write(RUN/'display_start.json',dict(start_monotonic=display_begin,shared_seconds=600,
            viewer_process_seconds=510,root_QA_end_before_shared_seconds=585))
        receipt['viewer_launches']=1
        supervised=owned('view_high1.py','viewer',510,p['viewer_memory_limit_bytes'])
        write(RUN/'viewer_supervision.json',supervised)
        if not passed(supervised):
            raise RuntimeError('One pure viewer or its complete cleanup did not pass')
        rendered=read(RUN/'view/renderer_receipt.json')
        if rendered['status']!='rendered_pending_root_visual_check':
            raise ValueError('Viewer receipt did not confirm the frozen display scope')
        print(json.dumps(dict(phase='ready_for_root_visual_check',
            images=p['image_names'],directory=str(RUN/'view'),
            shared_display_start_monotonic=display_begin,QA_end_before_shared_seconds=585,
            elapsed_helper_seconds=time.monotonic()-START)),flush=True)
        while not (BASE/'root_qa.json').exists():
            if time.monotonic()>=display_begin+585:
                raise TimeoutError('Original shared display/root QA window closed')
            clock(4690,'five root PNG checks')
            time.sleep(.1)
        qa=read(BASE/'root_qa.json')
        expected={name:identity(RUN/'view'/name) for name in p['image_names']}
        if (qa['status']!='pass' or qa['pixel_inspections']!=5 or qa['image_identities']!=expected
                or qa['scientific_calls']!=0 or qa['rerenders']!=0):
            raise ValueError('Five original PNG checks did not pass')
        if time.monotonic()>=display_begin+585:
            raise TimeoutError('Original root QA completion margin closed')
        clock(4690,'completed five root PNG checks')
        receipt['display_and_root_QA_seconds']=time.monotonic()-display_begin
        if receipt['display_and_root_QA_seconds']>600:
            raise TimeoutError('Original display600 exceeded')
        receipt['root_QA_accepted']=True
        clock(4695,'final ordinary bindings and helper exit')
        for row in p['bindings']:
            if identity(row['path'])!={k:row[k] for k in ('bytes','sha256')}:
                raise ValueError('Frozen source changed while executing: '+row['path'])
        receipt['status']='pass'
    except BaseException as error:
        receipt['error']=dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc())
    finally:
        receipt['elapsed_helper_before_final_tree_cleanup_seconds']=time.monotonic()-START
        write(BASE/'helper_receipt.json',receipt)
        print(json.dumps(dict(status=receipt['status'],elapsed=receipt['elapsed_helper_before_final_tree_cleanup_seconds'])),flush=True)
    return 0 if receipt['status']=='pass' and time.monotonic()<START+4700 else 1

if __name__=='__main__':
    raise SystemExit(main())
