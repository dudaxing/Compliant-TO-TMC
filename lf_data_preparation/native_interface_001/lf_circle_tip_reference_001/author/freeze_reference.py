"""Freeze the authorized finite reference package using ordinary bytes and NPZ seal/stat."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).resolve().parent
REL='lf_data_preparation/native_interface_001/lf_circle_tip_reference_001'
STAGE=ROOT/REL
BASE='8cf86e81e414866a7d5cb110e006c7088f94eb97'
GIT=['git','-c','gc.auto=0','-c','maintenance.auto=false']
read=lambda p:json.loads(p.read_bytes())
pin=lambda p:sha256(p.read_bytes()).hexdigest()


def main():
    assert subprocess.check_output(GIT+['rev-parse','HEAD'],cwd=ROOT,text=True).strip()==BASE
    assert not subprocess.check_output(GIT+['status','--porcelain'],cwd=ROOT,text=True).strip()
    assert not STAGE.exists()
    p=read(AUTHOR/'protocol.proposed.json');prep=read(AUTHOR/'preparation_receipt.json');auth=read(AUTHOR/'authorization.json')
    review=read(AUTHOR/'SOURCE_REVIEW.json')
    digest=pin(AUTHOR/'protocol.proposed.json')
    assert digest==prep['protocol_sha256']==auth['protocol_sha256']==review['protocol_sha256']
    assert p['source_baseline_commit']==auth['source_baseline_commit']==BASE
    assert auth['authorized'] is auth['authorization_from_direct_human_request'] is auth['one_invocation'] is True
    assert auth['direct_human_request']=='批准按 L-CTIPREF1 计划实施并执行'
    assert review['status'].startswith('pass') and not review.get('blocking_findings',review.get('blockers',[]))
    for name,expected in {**review['reviewed_author_sha256'],**review['reviewed_support_sha256']}.items():
        assert pin(AUTHOR/name)==expected,name
    for name,metadata in prep['external_files'].items():assert pin(AUTHOR/name)==metadata['sha256']
    scientific={row['path']:row for row in p['old_scientific_inputs']}
    for name,expected in p['bindings'].items():
        if name in scientific:
            assert scientific[name]['sha256']==expected and (ROOT/name).stat().st_size==scientific[name]['bytes']
        else:
            path=AUTHOR/Path(name).name if name.startswith(REL+'/') else ROOT/name
            assert pin(path)==expected,name
    (STAGE/'author').mkdir(parents=True,exist_ok=False)
    copies={name:name for name in ('execute_circle_reference.py','launch_reference.py','L-CTIPREF1_CARD.md')}
    copies['protocol.proposed.json']='protocol.json'
    for name in ('assemble_reference.py','freeze_reference.py','preparation_receipt.json','authorization.json','SOURCE_REVIEW.json','SOURCE_REVIEW.md'):
        copies[name]='author/'+name
    for source,dest in copies.items():
        shutil.copyfile(AUTHOR/source,STAGE/dest)
        assert (AUTHOR/source).read_bytes()==(STAGE/dest).read_bytes()
    for name,expected in p['bindings'].items():
        if name not in scientific:assert pin(ROOT/name)==expected,name
    record=dict(card='L-CTIPREF1',status='frozen_authorized_not_executed',source_baseline_commit=BASE,
        protocol_sha256=digest,authorization_sha256=pin(STAGE/'author/authorization.json'),
        bindings=len(p['bindings']),reference_sources=len(p['reference_sources']),copies=len(copies),
        HP_calls=0,old_payloads_opened=0,default_source_changes=0,
        files={dest:dict(bytes=(STAGE/dest).stat().st_size,sha256=pin(STAGE/dest)) for dest in copies.values()},
        recorded_utc=datetime.now(timezone.utc).isoformat())
    with (STAGE/'author/freeze_receipt.json').open('x',encoding='utf-8',newline='\n') as handle:
        json.dump(record,handle,ensure_ascii=False,indent=2);handle.write('\n')
    print(json.dumps({key:record[key] for key in ('status','protocol_sha256','bindings','copies','HP_calls')}))


if __name__=='__main__':main()
