"""Freeze the reviewed S5 bytes after the explicit human stage approval."""
from datetime import datetime,timezone
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).resolve().parent
REL='lf_data_preparation/native_interface_001/lf_circle_step_005'
STAGE=ROOT/REL
BASE='8ac36c0f3ce4b0609c592522cb70f810635a7a9d'
PIN='72618f6a9d9d4bf03f9fc8b903bcd579724340ffbb7129316f7a40e5bc4d81cc'
read=lambda path:json.loads(path.read_bytes())
pin=lambda path:sha256(path.read_bytes()).hexdigest()


def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==BASE
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()
    assert not STAGE.exists()
    p,prep,auth=[read(AUTHOR/name) for name in ('protocol.proposed.json','preparation_receipt.json','authorization.json')]
    review=read(AUTHOR/'SOURCE_REVIEW.json')
    assert review['status'].startswith('pass') and not review.get('blockers',review.get('blocking_findings',[]))
    assert pin(AUTHOR/'protocol.proposed.json')==prep['protocol_sha256']==auth['protocol_sha256']==PIN
    assert auth['authorized_execution_source_commit']==p['source_baseline_commit']==BASE
    assert auth['card']==auth['approval_card']==p['card']=='L-CSTEP5'
    assert auth['authorized'] is auth['authorization_from_direct_human_request'] is auth['one_invocation'] is True
    assert auth['direct_human_request']=='批准按 L-CSTEP5 卡执行'
    for name,row in prep['files'].items():assert pin(AUTHOR/name)==row['sha256']
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
    copies={name:name for name in ('execute_step.py','launch_step.py','step_task.json','L-CSTEP5_CARD.md')}
    copies['protocol.proposed.json']='protocol.json'
    for name in ('prepare_step.py','freeze_step.py','preparation_receipt.json','authorization.template.json',
        'authorization.json','READY_FOR_APPROVAL.json','SOURCE_REVIEW.json','SOURCE_REVIEW.md',
        'PARENT_REVIEW.json','PARENT_REVIEW.md','DOC_SOURCE_REVIEW.json','DOC_SOURCE_REVIEW.md',
        'CANDIDATE_DIFF.md','close.py','publish.py','archive_publication.py'):
        copies[name]='author/'+name
    for source,target in copies.items():
        shutil.copyfile(AUTHOR/source,STAGE/target)
        assert (AUTHOR/source).read_bytes()==(STAGE/target).read_bytes()
    for name,digest in p['source_bindings'].items():assert pin(ROOT/name)==digest,name
    receipt=dict(card='L-CSTEP5',status='frozen_authorized_not_started',source_baseline_commit=BASE,
        protocol_sha256=PIN,actual_authorization_sha256=pin(STAGE/'author/authorization.json'),
        prior_proposal_records='Pre-approval template/card/source-review statuses are immutable preparation snapshots; actual authority is the separate new human authorization.json.',
        copies=len(copies),source_bindings=len(p['source_bindings']),input_bindings=len(p['input_bindings']),
        old_payloads_opened=0,scientific_invocations=0,default_source_changes=0,
        files={target:dict(bytes=(STAGE/target).stat().st_size,sha256=pin(STAGE/target)) for target in copies.values()},
        recorded_utc=datetime.now(timezone.utc).isoformat())
    with (STAGE/'author/freeze_receipt.json').open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(receipt,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print(json.dumps({key:receipt[key] for key in ('status','protocol_sha256','copies','source_bindings','scientific_invocations')}))


if __name__=='__main__':main()
