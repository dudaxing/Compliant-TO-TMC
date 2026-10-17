"""Freeze the reviewed ordinary localization sources; no NPZ payload reads."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).resolve().parent
REL='lf_data_preparation/native_interface_001/lf_circle_local_001'
STAGE=ROOT/REL
BASE='e30d1024d0e8f1f5c03cbe1752cbd03baf5e70a6'
PIN='b9c5f4f40eb4e1237288e19ef9a80989e448b5bb0999bfdfc95810e87c20cea5'
read=lambda path:json.loads(path.read_bytes())
pin=lambda path:sha256(path.read_bytes()).hexdigest()


def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==BASE
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()
    assert not STAGE.exists()
    p,auth,prep=[read(AUTHOR/name) for name in ('protocol.proposed.json','authorization.json','preparation_receipt.json')]
    review=read(AUTHOR/'SOURCE_REVIEW.json')
    assert review['status'].startswith('pass') and not review.get('blocking_findings',review.get('blockers',[]))
    assert pin(AUTHOR/'protocol.proposed.json')==auth['protocol_sha256']==prep['protocol_sha256']==PIN
    assert auth['authorized_execution_source_commit']==p['source_baseline_commit']==BASE
    assert auth['card']==auth['approval_card']==p['card']=='L-CLOCAL1'
    assert auth['authorized'] is auth['authorization_from_direct_human_request'] is auth['one_invocation'] is True
    assert auth['direct_human_request'].startswith('好的，按你的建议开展 L-CLOCAL1，')
    for name,row in prep['files'].items():assert pin(AUTHOR/name)==row['sha256']
    for name,digest in p['source_bindings'].items():
        file=AUTHOR/Path(name).name if name.startswith(REL+'/') else ROOT/name
        assert pin(file)==digest,name
    payloads={row['path']:row for row in p['old_scientific_inputs']}
    assert len(payloads)==3 and sum(len(row['fields']) for row in payloads.values())==8
    for name,digest in p['input_bindings'].items():
        if name in payloads:
            assert digest==payloads[name]['sha256'] and (ROOT/name).stat().st_size==payloads[name]['bytes']
        else:assert pin(ROOT/name)==digest,name
    cwd=Path(p['working_directory'])
    assert cwd.is_dir() and not list(cwd.iterdir())
    (STAGE/'author').mkdir(parents=True,exist_ok=False)
    copies={name:name for name in ('execute_local.py','launch_local.py','L-CLOCAL1_CARD.md')}
    copies['protocol.proposed.json']='protocol.json'
    for name in ('assemble_local.py','freeze_local.py','preparation_receipt.json','authorization.json',
        'SOURCE_REVIEW.json','SOURCE_REVIEW.md','MATH_PARENT_REVIEW.json','MATH_PARENT_REVIEW.md',
        'prepare_publication.py','publish.py','archive_publication.py','DOC_SOURCE_REVIEW.json','DOC_SOURCE_REVIEW.md'):
        copies[name]='author/'+name
    for source,target in copies.items():
        shutil.copyfile(AUTHOR/source,STAGE/target)
        assert (AUTHOR/source).read_bytes()==(STAGE/target).read_bytes()
    for name,digest in p['source_bindings'].items():assert pin(ROOT/name)==digest,name
    receipt=dict(card='L-CLOCAL1',status='frozen_authorized_not_started',source_baseline_commit=BASE,
        protocol_sha256=PIN,copies=len(copies),source_bindings=7,input_bindings=11,
        scientific_invocations=0,old_payloads_opened=0,default_source_changes=0,
        files={target:dict(bytes=(STAGE/target).stat().st_size,sha256=pin(STAGE/target)) for target in copies.values()},
        recorded_utc=datetime.now(timezone.utc).isoformat())
    with (STAGE/'author/freeze_receipt.json').open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(receipt,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print(json.dumps({key:receipt[key] for key in ('status','protocol_sha256','copies','source_bindings','scientific_invocations')}))


if __name__=='__main__':main()
