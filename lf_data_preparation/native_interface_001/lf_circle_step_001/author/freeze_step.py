"""Copy reviewed study bytes, without scientific reads or default changes."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess
ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).resolve().parent
REL='lf_data_preparation/native_interface_001/lf_circle_step_001'
BASE='ec0d958f81db06777457aeaadd0a29b971da8457'
read=lambda p:json.loads(p.read_bytes())
pin=lambda p:sha256(p.read_bytes()).hexdigest()
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==BASE
assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()
review=read(AUTHOR/'SOURCE_REVIEW.json')
assert review['status'].startswith('pass') and not review.get('blocking_findings',[])
stage=ROOT/REL;assert not stage.exists()
stage.mkdir(parents=True);(stage/'author').mkdir()
for name in ('execute_step.py','launch_step.py','circle_saved_views.py','plot_convergence.py','step_task.json','L-CSTEP1_CARD.md'):
    (stage/name).write_bytes((AUTHOR/name).read_bytes())
for name in ('SOURCE_REVIEW.json','SOURCE_REVIEW.md','assemble_step.py','freeze_step.py'):
    (stage/'author'/name).write_bytes((AUTHOR/name).read_bytes())
(stage/'protocol.json').write_bytes((AUTHOR/'protocol.proposed.json').read_bytes())
(stage/'author/authorization.json').write_bytes((AUTHOR/'authorization.proposed.json').read_bytes())
p=read(stage/'protocol.json');a=read(stage/'author/authorization.json')
assert a['protocol_sha256']==pin(stage/'protocol.json')
for name,expected in p['source_bindings'].items():assert pin(ROOT/name)==expected,name
for name,expected in p['input_bindings'].items():
    if name.endswith('.json'):assert pin(ROOT/name)==expected,name
    else:
        seal=next(row for row in p['old_scientific_inputs'] if row['path']==name)
        assert (ROOT/name).stat().st_size==seal['bytes']
print(json.dumps(dict(status='frozen_not_executed',protocol_sha256=pin(stage/'protocol.json'),source_bindings=len(p['source_bindings']),old_payloads_opened=0,default_changes=0)))
