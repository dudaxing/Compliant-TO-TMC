"""Freeze reviewed study files; ordinary bytes and old NPZ stat only."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).resolve().parent
REL='lf_data_preparation/native_interface_001/lf_circle_tip_pilot_001'
BASE='036fd5d9298525894b5f90a37dab8f258d6cc9b1'
read=lambda p:json.loads(p.read_bytes())
pin=lambda p:sha256(p.read_bytes()).hexdigest()
assert subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==BASE
assert not subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false','status','--porcelain'],cwd=ROOT,text=True).strip()
assert not (ROOT/REL).exists()
review=read(AUTHOR/'SOURCE_REVIEW.json')
assert review['status'].startswith('pass') and not review.get('blocking_findings',[])
for name,expected in review['reviewed_author_sha256'].items():assert pin(AUTHOR/name)==expected,name
stage=ROOT/REL
stage.mkdir(parents=True,exist_ok=False);(stage/'author').mkdir()
for name in ('execute_pilot.py','circle_saved_views.py','launch_pilot.py','plot_convergence.py','pilot_task.json','L-CTIPPILOT1_CARD.md'):
    (stage/name).write_bytes((AUTHOR/name).read_bytes())
for name in ('SOURCE_REVIEW.json','SOURCE_REVIEW.md','assemble_pilot.py','freeze_pilot.py'):
    (stage/'author'/name).write_bytes((AUTHOR/name).read_bytes())
(stage/'protocol.json').write_bytes((AUTHOR/'protocol.proposed.json').read_bytes())
(stage/'author/authorization.json').write_bytes((AUTHOR/'authorization.proposed.json').read_bytes())
p=read(stage/'protocol.json')
assert read(stage/'author/authorization.json')['protocol_sha256']==pin(stage/'protocol.json')
for name,expected in p['source_bindings'].items():assert pin(ROOT/name)==expected,name
for name,expected in p['input_bindings'].items():
    if name.endswith('.json'):assert pin(ROOT/name)==expected,name
    else:
        assert name==p['old_scientific_input']['path']
        assert (ROOT/name).stat().st_size==p['old_scientific_input']['bytes']
print(json.dumps(dict(status='frozen_not_executed',protocol_sha256=pin(stage/'protocol.json'),old_payload_reads=0,default_HF_changes=0)))
