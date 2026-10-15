"""Launch the sole L-TUSE1 saved delivery from an unrelated cwd; cooperative limits."""
from time import perf_counter, sleep
STARTED = perf_counter()
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import psutil

STAGE = Path(__file__).resolve().parent
ROOT = STAGE.parents[2]
read = lambda p: json.loads(p.read_bytes())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')


def main():
    protocol_raw = (STAGE/'protocol.json').read_bytes()
    protocol, auth = json.loads(protocol_raw), read(STAGE/'author/authorization.json')
    assert auth['authorized'] is auth['authorization_from_direct_human_reply'] is auth['one_invocation'] is True
    assert auth['card'] == protocol['card'] == 'L-TUSE1' and auth['direct_human_answer'] == '好的，按你的建议，先完成第三个LF夹持器全部25态、两态独立参考和既有变形图的接口关联，生成状态表与人工检查页，注意做好记录和可视化，再根据结果安排三个设计的同定义对照。'
    assert auth['protocol_sha256'] == sha256(protocol_raw).hexdigest()
    assert subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip() == auth['authorized_execution_source_commit'] == protocol['source_baseline_commit']
    assert (protocol['helper_seconds'],protocol['outer_seconds'],protocol['sampled_RSS_bytes']) == (180,240,1024**3)
    output = ROOT/protocol['output_directory']
    receipt_file = STAGE/'delivery_launch.json'
    assert not any(path.exists() for path in (output,receipt_file,STAGE/'delivery_stdout.log',STAGE/'stop_requested.txt'))
    for name,pin in protocol['source_bindings'].items():
        assert sha256((ROOT/name).read_bytes()).hexdigest() == pin
    cwd = Path(protocol['working_directory']).resolve()
    assert cwd.is_dir() and not cwd.is_relative_to(ROOT)
    argv=[sys.executable,'-X','utf8','-B',str(STAGE/'execute_delivery.py')]
    receipt=dict(card='L-TUSE1',status='running',invocations=0,argv=argv,working_directory=str(cwd),
        protocol_sha256=auth['protocol_sha256'],authorized_execution_source_commit=auth['authorized_execution_source_commit'],
        started_utc=datetime.now(timezone.utc).isoformat(),helper_seconds=180,outer_seconds=240,
        sampled_RSS_limit_bytes=1024**3,resource_mode='Elapsed checkpoints and sampled RSS, cooperative stop/actual child wait, no OS hard cap or force')
    write(receipt_file,receipt)
    child, reason, peak, child_wall, helper = None,None,0,None,{}
    try:
        with (STAGE/'delivery_stdout.log').open('xb') as log:
            receipt['invocations']=1; write(receipt_file,receipt)
            child_start=perf_counter()
            child=subprocess.Popen(argv,cwd=cwd,stdout=log,stderr=subprocess.STDOUT,
                env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1'))
            process=psutil.Process(child.pid)
            while child.poll() is None:
                try:
                    peak=max(peak,sum(member.memory_info().rss for member in [process]+process.children(recursive=True) if member.is_running()))
                except psutil.NoSuchProcess:
                    pass
                if reason is None and (perf_counter()-child_start>180 or perf_counter()-STARTED>240 or peak>1024**3):
                    reason='resource_limit'; (STAGE/'stop_requested.txt').write_text(reason,encoding='utf-8')
                sleep(.05)
        child_wall=perf_counter()-child_start
        helper_path=output/'execution_receipt.json'
        helper=read(helper_path) if helper_path.exists() else {}
        passed=(child.returncode==0 and reason is None and child_wall<=180 and perf_counter()-STARTED<=240
            and helper.get('status')=='pass' and helper.get('output_identity_seal')=='complete_inside_original_helper_window')
        receipt['status']='pass' if passed else 'not_pass'
    except BaseException as failure:
        receipt.update(status='not_pass',error=dict(type=type(failure).__name__,message=str(failure)))
        if child is not None and child.poll() is None:
            reason=reason or 'launcher_observation_error'
            (STAGE/'stop_requested.txt').write_text(reason,encoding='utf-8')
            child.wait(); child_wall=perf_counter()-child_start
    receipt.update(exit_code=child.returncode if child is not None else None,
        elapsed_seconds=perf_counter()-STARTED,child_terminal_wall_seconds=child_wall,
        peak_sampled_tree_RSS_bytes=peak,stop_reason=reason,helper_status=helper.get('status'),
        completed_utc=datetime.now(timezone.utc).isoformat())
    write(receipt_file,receipt)
    print(json.dumps({key:receipt[key] for key in ('status','invocations','exit_code','elapsed_seconds','peak_sampled_tree_RSS_bytes','stop_reason')}),flush=True)
    if receipt['status']!='pass':
        raise RuntimeError('L-TUSE1 closed not_pass; no retry or force')


if __name__ == '__main__':
    main()
