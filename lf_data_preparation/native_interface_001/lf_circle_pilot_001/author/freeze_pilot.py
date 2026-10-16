"""Install reviewed study bytes in a new stage, without scientific payload reads."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).resolve().parent
REL='lf_data_preparation/native_interface_001/lf_circle_pilot_001'
BASE='f4a681c8acbae9f91637b052f793109c45af3dcc'
read=lambda p:json.loads(p.read_bytes())
pin=lambda p:sha256(p.read_bytes()).hexdigest()
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==BASE
assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()
stage=ROOT/REL
assert not stage.exists()
review=read(AUTHOR/'SOURCE_REVIEW.json')
assert review['status'].startswith('pass') and not review.get('blocking_findings',[])
stage.mkdir(parents=True,exist_ok=False); (stage/'author').mkdir()
for name in ('execute_pilot.py','circle_saved_views.py','launch_pilot.py','plot_convergence.py','pilot_task.json','L-CPILOT1_CARD.md'):
    (stage/name).write_bytes((AUTHOR/name).read_bytes())
for name in ('SOURCE_REVIEW.json','SOURCE_REVIEW.md','assemble_pilot.py','freeze_pilot.py'):
    (stage/'author'/name).write_bytes((AUTHOR/name).read_bytes())
(stage/'protocol.json').write_bytes((AUTHOR/'protocol.proposed.json').read_bytes())
(stage/'author/authorization.json').write_bytes((AUTHOR/'authorization.proposed.json').read_bytes())
p=read(stage/'protocol.json'); auth=read(stage/'author/authorization.json')
assert auth['protocol_sha256']==pin(stage/'protocol.json')
for name,expected in p['source_bindings'].items(): assert pin(ROOT/name)==expected,name
for name,expected in p['input_bindings'].items():
    if name.endswith('.json'): assert pin(ROOT/name)==expected,name
    else:
        assert name==p['old_scientific_input']['path']
        assert (ROOT/name).stat().st_size==p['old_scientific_input']['bytes']
print(json.dumps(dict(status='frozen_not_executed',protocol_sha256=pin(stage/'protocol.json'),source_bindings=len(p['source_bindings']),old_NPZ_payloads_opened=0,default_HF_changes=0)))
