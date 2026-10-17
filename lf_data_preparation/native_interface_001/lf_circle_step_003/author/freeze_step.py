"""Freeze reviewed ordinary sources and the actual approved S3 metadata."""
from datetime import datetime,timezone
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).resolve().parent
REL='lf_data_preparation/native_interface_001/lf_circle_step_003'
STAGE=ROOT/REL
BASE='260d4b86ee87ab3dd12c04dbcccef7ffa4c31eac'
PIN='ae3e6a346585de2379cdd546ede54639a46b8f70b99bbae9d78231dde0b43a2c'
read=lambda p:json.loads(p.read_bytes())
pin=lambda p:sha256(p.read_bytes()).hexdigest()


def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==BASE
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()
    assert not STAGE.exists()
    p=read(AUTHOR/'protocol.proposed.json');prep=read(AUTHOR/'preparation_receipt.json');auth=read(AUTHOR/'authorization.json')
    review=read(AUTHOR/'SOURCE_REVIEW.json')
    assert review['status'].startswith('pass') and not review.get('blocking_findings',review.get('blockers',[]))
    assert pin(AUTHOR/'protocol.proposed.json')==prep['protocol_sha256']==auth['protocol_sha256']==PIN
    assert p['source_baseline_commit']==auth['authorized_execution_source_commit']==BASE
    assert auth['card']==auth['approval_card']==p['card']=='L-CSTEP3'
    assert auth['authorized'] is auth['authorization_from_direct_human_request'] is auth['one_invocation'] is True
    assert auth['direct_human_request']=='好的，按你的建议复用已安装的 load_only 保存态延伸接口，从圆形工件1.15 mm保存态推进到1.25 mm。保持半径9 mm、圆心(71,40) mm、其余物理条件和原验收门不变，注意做好记录，可视化实际变形、反力和收敛情况，再根据结果安排后续计算。'
    for name,record in prep['files'].items():assert pin(AUTHOR/name)==record['sha256']
    for name,digest in p['source_bindings'].items():
        file=AUTHOR/Path(name).name if name.startswith(REL+'/') else ROOT/name
        assert pin(file)==digest,name
    payloads={row['path']:row for row in p['old_scientific_inputs']}
    assert len(payloads)==2
    for name,digest in p['input_bindings'].items():
        if name in payloads:
            assert payloads[name]['sha256']==digest and (ROOT/name).stat().st_size==payloads[name]['bytes']
        else:
            file=AUTHOR/'step_task.json' if name==REL+'/step_task.json' else ROOT/name
            assert pin(file)==digest,name
    cwd=Path(p['working_directory']);assert cwd.is_dir() and not list(cwd.iterdir())
    (STAGE/'author').mkdir(parents=True,exist_ok=False)
    copies={name:name for name in ('execute_step.py','launch_step.py','step_task.json','L-CSTEP3_CARD.md')}
    copies['protocol.proposed.json']='protocol.json'
    for name in ('assemble_step.py','freeze_step.py','preparation_receipt.json','authorization.json',
                 'SOURCE_REVIEW.json','SOURCE_REVIEW.md','CANDIDATE_DIFF.md'):
        copies[name]='author/'+name
    for source,target in copies.items():
        shutil.copyfile(AUTHOR/source,STAGE/target)
        assert (AUTHOR/source).read_bytes()==(STAGE/target).read_bytes()
    for name,digest in p['source_bindings'].items():assert pin(ROOT/name)==digest,name
    record=dict(card='L-CSTEP3',status='frozen_authorized_not_started',source_baseline_commit=BASE,
        protocol_sha256=PIN,authorization_sha256=pin(STAGE/'author/authorization.json'),copies=len(copies),
        source_bindings=len(p['source_bindings']),input_bindings=len(p['input_bindings']),old_payloads_opened=0,
        scientific_invocations=0,default_source_changes=0,
        files={target:dict(bytes=(STAGE/target).stat().st_size,sha256=pin(STAGE/target)) for target in copies.values()},
        recorded_utc=datetime.now(timezone.utc).isoformat())
    with (STAGE/'author/freeze_receipt.json').open('x',encoding='utf-8',newline='\n') as handle:
        json.dump(record,handle,ensure_ascii=False,indent=2);handle.write('\n')
    print(json.dumps({key:record[key] for key in ('status','protocol_sha256','copies','source_bindings','scientific_invocations')}))


if __name__=='__main__':main()
