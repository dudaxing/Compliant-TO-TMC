"""Freeze the exact reviewed card after the actual human approval; no science."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).resolve().parent
REL = 'lf_data_preparation/native_interface_001/lf_circle_step_002'
STAGE = ROOT/REL
BASE = 'a3e444dc106cd79123cd5455f623d54dc7b43628'
PROTOCOL = '7ffc36daed8c5ad516abbd0b029922124df412f7e2b7975526b5f2f11b74d853'
read = lambda p: json.loads(p.read_bytes())
pin = lambda p: sha256(p.read_bytes()).hexdigest()


def write_new(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write('\n')


def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==BASE
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()
    assert not STAGE.exists()
    protocol = read(AUTHOR/'protocol.proposed.json')
    assert pin(AUTHOR/'protocol.proposed.json')==PROTOCOL
    review = read(AUTHOR/'SOURCE_REVIEW.json')
    assert review['status']=='pass_source_only' and not review['blocking_findings']
    for name in ('execute_step.py','launch_step.py','protocol.proposed.json','step_task.json','L-CSTEP2_CARD.md','CANDIDATE_DIFF.md'):
        assert pin(AUTHOR/name)==review['reviewed_files'][name]['sha256']
    for name, digest in protocol['source_bindings'].items():
        path = AUTHOR/Path(name).name if name.startswith(REL+'/') else ROOT/name
        assert pin(path)==digest, name
    payloads = {row['path']:row for row in protocol['old_scientific_inputs']}
    assert len(payloads)==2
    for name,digest in protocol['input_bindings'].items():
        if name in payloads:
            assert payloads[name]['sha256']==digest and (ROOT/name).stat().st_size==payloads[name]['bytes']
        else:
            path = AUTHOR/'step_task.json' if name==REL+'/step_task.json' else ROOT/name
            assert pin(path)==digest, name
    cwd = Path(protocol['working_directory'])
    assert cwd.is_dir() and not list(cwd.iterdir())
    auth = dict(card='L-CSTEP2', approval_card='L-CSTEP2', authorized=True,
        authorization_from_direct_human_request=True, one_invocation=True,
        direct_human_request='批准按 L-CSTEP2 卡执行',
        source_kind='Actual structured human question reply received in this chat',
        question_item_id='["request_user_input_async","call_0657db5d83a5400c841bdb8432b9ec1b",0]',
        authorized_execution_source_commit=BASE, protocol_sha256=PROTOCOL,
        scope='Exactly the approved L-CSTEP2 card: one installed load_only1.00/1.15 segment, original physics/gates/settings, bounded views/pixels, records and ordinary main publication/restore.',
        recorded_utc=datetime.now(timezone.utc).isoformat())
    write_new(AUTHOR/'authorization.json', auth)
    (STAGE/'author').mkdir(parents=True, exist_ok=False)
    copies = {'execute_step.py':'execute_step.py','launch_step.py':'launch_step.py',
        'step_task.json':'step_task.json','L-CSTEP2_CARD.md':'L-CSTEP2_CARD.md',
        'protocol.proposed.json':'protocol.json'}
    for name in ('assemble_preparation.py','freeze_authorized.py','preparation_receipt.json',
                 'CANDIDATE_DIFF.md','SOURCE_REVIEW.json','SOURCE_REVIEW.md','authorization.json'):
        copies[name]='author/'+name
    for source,destination in copies.items():
        shutil.copyfile(AUTHOR/source, STAGE/destination)
        assert (AUTHOR/source).read_bytes()==(STAGE/destination).read_bytes()
    for name,digest in protocol['source_bindings'].items():
        assert pin(ROOT/name)==digest, name
    receipt = dict(card='L-CSTEP2', status='frozen_authorized_not_started',
        protocol_sha256=PROTOCOL, authorization_sha256=pin(STAGE/'author/authorization.json'),
        source_baseline_commit=BASE, ordinary_copies=len(copies), source_bindings=len(protocol['source_bindings']),
        old_payloads_opened=0, scientific_invocations=0, default_source_changes=0,
        files={destination:dict(bytes=(STAGE/destination).stat().st_size,sha256=pin(STAGE/destination)) for destination in copies.values()},
        recorded_utc=datetime.now(timezone.utc).isoformat())
    write_new(STAGE/'author/freeze_receipt.json',receipt)
    print(json.dumps({key:receipt[key] for key in ('status','protocol_sha256','ordinary_copies','source_bindings','scientific_invocations')}))


if __name__=='__main__':
    main()
