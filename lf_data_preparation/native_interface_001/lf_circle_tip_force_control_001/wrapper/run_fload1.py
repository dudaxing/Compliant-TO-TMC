"""One bounded validation/display helper; HF imports occur only in pytest."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import traceback
import xml.etree.ElementTree as ET

from windows_owned_process_sup2 import run_owned

BASE=Path(__file__).resolve().parent
RUN=BASE/'run_001'
PROTOCOL=BASE/'protocol.json'

def read(path):
    return json.loads(Path(path).read_bytes())

def write(path,value):
    with Path(path).open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False)
        stream.write('\n')

def identity(path):
    raw=Path(path).read_bytes()
    return dict(path=str(Path(path).resolve()),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())

def passed(row):
    return (row.get('reason')=='normal_exit' and row.get('returncode')==0
        and row.get('cleanup_verified') is True and row.get('cleanup_proof',{}).get('pass') is True
        and row.get('cleanup_proof',{}).get('job_handle_closed') is True)

def main():
    start=float(os.environ['FLOAD1_ROOT_START'])
    p=read(PROTOCOL)
    env=os.environ.copy()
    env.update(PYTHONPATH=p['candidate_source'],PYTHONDONTWRITEBYTECODE='1',
        PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',JAX_ENABLE_X64='true',JAX_PLATFORMS='cpu',
        MPLBACKEND='Agg',FLOAD1_ARTIFACT_DIR=str(RUN/'artifacts'))
    env.update(p['thread_environment'])
    receipt=dict(stage='L-CTIPFLOAD1',status='not_pass',start_utc=datetime.now(timezone.utc).isoformat(),
        test_process_launches=0,viewer_process_launches=0,new_HP=0,production_installations=0,
        execution_attempt=1,external_retries=0,scientific_calls_by_helper=0)
    try:
        if time.monotonic()+300+75>=start+400:
            raise TimeoutError('Insufficient original helper reserve for full tests/display budgets')
        receipt['test_process_launches']=1
        tests=run_owned(p['test_command'],cwd=p['candidate_hf_repo'],env=env,
            log=RUN/'pytest.log',deadline=time.monotonic()+300.,seconds=300.,
            rss_limit=p['memory_limit_bytes'],instance_log_path=RUN/'tests.instances.ndjson',
            instance_identity=dict(stage='L-CTIPFLOAD1',phase='tests300'))
        write(RUN/'tests_supervision.json',tests)
        receipt['tests_supervision_pass']=passed(tests)
        if not passed(tests):
            raise RuntimeError('Unique pytest process or same-instance cleanup did not pass')
        tree=ET.parse(RUN/'pytest.xml')
        cases=tree.findall('.//testcase')
        if len(cases)!=17 or any(c.find('failure') is not None or c.find('error') is not None
                                or c.find('skipped') is not None for c in cases):
            raise ValueError('Expected exactly 17 passing, unskipped pytest items')
        counts=read(RUN/'artifacts/call_counts.json')
        if (counts['new_real_16cell_paths']!=4
                or counts['new_injected_or_rejected_calls']>32
                or counts['controlled_real_partial_included_in_both_axes']!=1):
            raise ValueError('Actual finite test calls differ from frozen maximums')
        summary=read(RUN/'artifacts/validation_summary.json')
        force=read(summary['force_result_file'])
        partial=read(summary['partial_result_file'])
        if (force['status']!='success' or force['target_reached'] is not True
                or partial['status']!='failed' or len(partial['accepted_steps'])!=1):
            raise ValueError('Actual force path or controlled partial differs from test contract')
        receipt.update(test_items_passed=len(cases),actual_new_call_counts=counts,
            legacy_items_passed=9,legacy_real_2cell_paths=1,legacy_synthetic_calls=11,
            legacy_count_basis='Byte-bound original nine expanded tests all passed; static 1 real/11 synthetic calls.',
            validation_summary=identity(RUN/'artifacts/validation_summary.json'))
        if time.monotonic()+70>=start+400:
            raise TimeoutError('Insufficient original reserve for full viewer60 and cleanup')
        receipt['viewer_process_launches']=1
        viewer=run_owned([p['python_executable'],'-X','utf8','-B',str(BASE/'render_fload1.py')],
            cwd=str(BASE),env=env,log=RUN/'viewer.log',deadline=time.monotonic()+60.,seconds=60.,
            rss_limit=p['memory_limit_bytes'],instance_log_path=RUN/'viewer.instances.ndjson',
            instance_identity=dict(stage='L-CTIPFLOAD1',phase='viewer60'))
        write(RUN/'viewer_supervision.json',viewer)
        if not passed(viewer):
            raise RuntimeError('Viewer or same-instance cleanup did not pass')
        rendered=read(RUN/'view/renderer_receipt.json')
        if rendered['new_png_count']!=1 or rendered['scientific_calls']!=0:
            raise ValueError('Viewer scope differs from approved one-PNG pure display')
        receipt.update(status='ready_for_root_visual_check',renderer=rendered,
            next_action='Root inspects this one new PNG once. No rerender, retry or science permitted.')
    except BaseException as error:
        receipt['error']=dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc())
    finally:
        receipt['elapsed_since_root_seconds']=time.monotonic()-start
        write(RUN/'helper_receipt.json',receipt)
        print(json.dumps(dict(status=receipt['status'],elapsed=receipt['elapsed_since_root_seconds'])),flush=True)
    return 0 if receipt['status']=='ready_for_root_visual_check' else 1

if __name__=='__main__':
    raise SystemExit(main())
