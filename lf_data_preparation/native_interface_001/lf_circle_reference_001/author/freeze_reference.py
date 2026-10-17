"""Freeze the already authorized and reviewed reference package; no payload reads."""
from datetime import datetime,timezone
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).resolve().parent
REL='lf_data_preparation/native_interface_001/lf_circle_reference_001'
STAGE=ROOT/REL
BASE='11a8b49ebef7d18fef17ffe6c9e365ce574de074'
PIN='016f9d20b77426bf8f3ed2379e4c356fa0c5afc06cec25d4f2eaf0a98d034f28'
read=lambda p:json.loads(p.read_bytes())
pin=lambda p:sha256(p.read_bytes()).hexdigest()


def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==BASE
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()
    assert not STAGE.exists()
    p=read(AUTHOR/'protocol.proposed.json');prep=read(AUTHOR/'preparation_receipt.json');auth=read(AUTHOR/'authorization.json')
    assert pin(AUTHOR/'protocol.proposed.json')==PIN==prep['protocol_sha256']==auth['protocol_sha256']
    assert p['source_baseline_commit']==auth['source_baseline_commit']==BASE
    assert auth['authorized'] is auth['authorization_from_direct_human_request'] is auth['one_invocation'] is True
    assert auth['direct_human_request']=='好的，按你的建议先核对圆形工件1.15 mm峰值保存态的独立高精度参考，保持半径9 mm、圆心(71,40) mm、其余物理条件和原验收门不变，注意做好记录和误差可视化，再根据结果安排后续加载。'
    for name in ('SOURCE_REVIEW.json','MATH_SCOPE_REVIEW.json'):
        r=read(AUTHOR/name)
        assert r['status'].startswith('pass') and not r.get('blocking_findings',r.get('blockers',r.get('blocking',[])))
    for name,metadata in prep['external_files'].items():assert pin(AUTHOR/name)==metadata['sha256']
    scientific={row['path']:row for row in p['old_scientific_inputs']}
    for name,digest in p['bindings'].items():
        if name in scientific:
            assert scientific[name]['sha256']==digest and (ROOT/name).stat().st_size==scientific[name]['bytes']
        else:
            path=AUTHOR/Path(name).name if name.startswith(REL+'/') else ROOT/name
            assert pin(path)==digest,name
    (STAGE/'author').mkdir(parents=True,exist_ok=False)
    copies={name:name for name in ('execute_circle_reference.py','launch_reference.py','L-CREF1_CARD.md')}
    copies['protocol.proposed.json']='protocol.json'
    for name in ('assemble_reference.py','freeze_reference.py','preparation_receipt.json','authorization.json',
                 'SOURCE_REVIEW.json','SOURCE_REVIEW.md','MATH_SCOPE_REVIEW.json','MATH_SCOPE_REVIEW.md'):
        copies[name]='author/'+name
    for source,dest in copies.items():
        shutil.copyfile(AUTHOR/source,STAGE/dest)
        assert (AUTHOR/source).read_bytes()==(STAGE/dest).read_bytes()
    for name,digest in p['bindings'].items():
        if name not in scientific:assert pin(ROOT/name)==digest,name
    record=dict(card='L-CREF1',status='frozen_authorized_not_executed',source_baseline_commit=BASE,
        protocol_sha256=PIN,authorization_sha256=pin(STAGE/'author/authorization.json'),
        bindings=len(p['bindings']),reference_sources=len(p['reference_sources']),copies=len(copies),
        HP_calls=0,old_payloads_opened=0,default_source_changes=0,
        files={dest:dict(bytes=(STAGE/dest).stat().st_size,sha256=pin(STAGE/dest)) for dest in copies.values()},
        recorded_utc=datetime.now(timezone.utc).isoformat())
    with (STAGE/'author/freeze_receipt.json').open('x',encoding='utf-8',newline='\n') as handle:
        json.dump(record,handle,ensure_ascii=False,indent=2);handle.write('\n')
    print(json.dumps({key:record[key] for key in ('status','protocol_sha256','bindings','copies','HP_calls')}))


if __name__=='__main__':main()
