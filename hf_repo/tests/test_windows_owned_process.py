"""Original five synthetic workloads, explicitly checked under SUP2."""
import json
import os
from pathlib import Path
import sys
import time
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from windows_owned_process_sup2 import run_owned
from test_windows_cleanup_contract import (
    assert_cleanup_proof,durable_json,identity,record_runtime_identity,
)

pytestmark=pytest.mark.skipif(os.name!='nt',reason='Windows Job Object contract')

@pytest.fixture(scope='module',autouse=True)
def bind_process_sources():
    record_runtime_identity(__file__,'runtime_identity_process.json')


def invoke(tmp_path,code,*,deadline=None,**kwargs):
    if deadline is None:
        deadline=time.monotonic()+12
    command=[sys.executable,'-B','-c',code]
    nodeid=os.environ['PYTEST_CURRENT_TEST'].rsplit(' ',1)[0]
    request=dict(schema='hf-cpu-clean1-request-1',protocol='F-CPU-CLEAN1',
                 test_nodeid=nodeid,identity=identity('process_case'),command=command,
                 deadline_monotonic=deadline,seconds=8.,overrides=kwargs)
    durable_json(tmp_path/'request.json',request)
    try:
        receipt=run_owned(command,cwd=str(tmp_path),env=os.environ.copy(),
                         log=tmp_path/'child.log',deadline=deadline,seconds=8,
                         instance_identity=request['identity'],**kwargs)
    except BaseException as error:
        durable_json(tmp_path/'call_outcome.json',
                     dict(status='raised',exception_type=type(error).__name__,message=str(error)))
        raise
    durable_json(tmp_path/'receipt.json',receipt)
    durable_json(tmp_path/'call_outcome.json',
                 dict(status='returned',receipt_path='receipt.json'))
    return receipt

@pytest.mark.parametrize('exitcode',[0,7])
def test_exit(tmp_path,exitcode):
    r=invoke(tmp_path,f'raise SystemExit({exitcode})')
    assert r['returncode']==exitcode and r['cleanup_verified']
    assert r['reason']==('normal_exit' if exitcode==0 else 'nonzero_exit')
    assert_cleanup_proof(r)

def test_timeout(tmp_path):
    r=invoke(tmp_path,'import time; time.sleep(20)',deadline=time.monotonic()+.3)
    assert r['reason']=='global_deadline' and r['cleanup_verified']
    assert_cleanup_proof(r)

def test_resource_trigger(tmp_path):
    r=invoke(tmp_path,'import time; x=bytearray(16*1024**2); time.sleep(20)',rss_limit=1)
    assert r['reason']=='rss_limit' and r['cleanup_verified']
    assert_cleanup_proof(r)

def test_orphan_grandchild(tmp_path):
    code="import subprocess,sys,time; p=subprocess.Popen([sys.executable,'-B','-c','import time; time.sleep(20)']); open('grandchild.json','w').write(str(p.pid)); time.sleep(.2)"
    r=invoke(tmp_path,code)
    assert r['reason']=='normal_exit' and r['cleanup_verified']
    pid=int((tmp_path/'grandchild.json').read_text())
    assert pid in r['owned_pids']
    proof=assert_cleanup_proof(r)
    assert any(row['pid']==pid and row['signaled'] for row in proof['identities'])
