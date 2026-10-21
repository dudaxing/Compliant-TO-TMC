"""Freeze reviewed comparison sources under the existing direct approval."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).resolve().parent
REL='lf_data_preparation/native_interface_001/lf_circle_tip_alpha_comparison_001'
BASE='08d07caf6cbb1e6ebe1af6f35c8dc1b8c9d0d669'
CARD='L-CTIPACOMP1'
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
for name in ('execute_step.py','launch_step.py','comparison_views.py','L-CTIPACOMP1_CARD.md'):
    (stage/name).write_bytes((AUTHOR/name).read_bytes())
for name in ('SOURCE_REVIEW.json','SOURCE_REVIEW.md','assemble_step.py','freeze_step.py',
    'input_inventory.json','input_schema.json','preparation_receipt.json'):
    (stage/'author'/name).write_bytes((AUTHOR/name).read_bytes())
(stage/'protocol.json').write_bytes((AUTHOR/'protocol.proposed.json').read_bytes())
(stage/'author/authorization.json').write_bytes((AUTHOR/'authorization.proposed.json').read_bytes())
protocol=read(stage/'protocol.json')
for name,expected in protocol['source_bindings'].items():assert pin(ROOT/name)==expected,name
for name,seal in protocol['ordinary_JSON_bindings'].items():
    raw=(ROOT/name).read_bytes()
    assert len(raw)==seal['bytes'] and sha256(raw).hexdigest()==seal['sha256'],name
for item in protocol['cases']:
    assert (ROOT/item['manual_path']).stat().st_size==item['manual_bytes']
print(json.dumps(dict(status='frozen_not_executed',protocol_sha256=pin(stage/'protocol.json'),ordinary_JSONs=2,old_media_content_reads=0,scientific_calls=0)))
