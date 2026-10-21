"""Freeze reviewed AFORCE1 sources and preserve the pre-approval plan history."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).resolve().parent
REL='lf_data_preparation/native_interface_001/lf_circle_tip_alpha_force_001'
BASE='289450a8d27d915e1832beef9c75ca4fcc168232'
CARD='L-CTIPAFORCE1'
read=lambda path:json.loads(path.read_bytes())
pin=lambda path:sha256(path.read_bytes()).hexdigest()
git=lambda *a:subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false',*a],cwd=ROOT,text=True).strip()
assert git('rev-parse','HEAD')==BASE and not git('status','--porcelain')
assert not (ROOT/REL).exists()
auth=read(AUTHOR/'authorization.proposed.json');review=read(AUTHOR/'SOURCE_REVIEW.json')
assert auth['card']==auth['approval_card']==CARD
assert auth['authorized'] is auth['authorization_from_direct_human_request'] is auth['one_invocation'] is True
assert auth['protocol_sha256']==pin(AUTHOR/'protocol.proposed.json')==review['protocol_sha256']
assert review['status'].startswith('pass') and not review.get('blockers',review.get('blocking_findings',[]))
for name,expected in (review['reviewed_author_sha256']|review.get('reviewed_support_sha256',{})).items():
    assert pin(AUTHOR/name)==expected,name
stage=ROOT/REL;(stage/'author').mkdir(parents=True,exist_ok=False)
for name in ('execute_step.py','launch_step.py','force_views.py'):
    (stage/name).write_bytes((AUTHOR/name).read_bytes())
(stage/'L-CTIPAFORCE1_CARD.md').write_bytes((AUTHOR/'L-CTIPAFORCE1_APPROVED_CARD.md').read_bytes())
for name in ('SOURCE_REVIEW.json','SOURCE_REVIEW.md','assemble_step.py','freeze_step.py',
    'input_inventory.json','input_schema.json','producer_provenance.json','FORCE1_SOURCE_CONTRACT.md',
    'VISUAL_PLAN.md','READ_ONLY_STATE.json','PLAN_REVIEW.json','PLAN_REVIEW.md','proposed_plan.json',
    'FINAL_PREPARATION.json','preparation_receipt.json'):
    (stage/'author'/name).write_bytes((AUTHOR/name).read_bytes())
(stage/'author/preapproval_CARD.md').write_bytes((AUTHOR/'L-CTIPAFORCE1_CARD.md').read_bytes())
(stage/'protocol.json').write_bytes((AUTHOR/'protocol.proposed.json').read_bytes())
(stage/'author/authorization.json').write_bytes((AUTHOR/'authorization.proposed.json').read_bytes())
protocol=read(stage/'protocol.json')
for name,expected in protocol['source_bindings'].items():assert pin(ROOT/name)==expected,name
for name,seal in protocol['ordinary_JSON_bindings'].items():
    raw=(ROOT/name).read_bytes()
    assert len(raw)==seal['bytes'] and sha256(raw).hexdigest()==seal['sha256'],name
for item in protocol['existing_manuals']:
    assert (ROOT/item['path']).stat().st_size==item['bytes']
print(json.dumps(dict(status='frozen_not_executed',protocol_sha256=pin(stage/'protocol.json'),ordinary_JSONs=6,old_media_content_reads=0,scientific_calls=0)))
