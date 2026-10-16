"""Copy reviewed study bytes; no default installation or scientific reads."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess
ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).resolve().parent
REL='lf_data_preparation/native_interface_001/lf_circle_extension_001'
BASE='09c3495c1a4dfc30ec58143ae192d851ac7d3283'
read=lambda p:json.loads(p.read_bytes())
pin=lambda p:sha256(p.read_bytes()).hexdigest()
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==BASE
assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()
stage=ROOT/REL; assert not stage.exists()
review=read(AUTHOR/'SOURCE_REVIEW.json')
assert review['status'].startswith('pass') and not review.get('blocking_findings',[])
stage.mkdir(parents=True);(stage/'author').mkdir()
for name in ('execute_extension.py','launch_extension.py','circle_saved_views.py','plot_convergence.py','test_load_only_extension.py','extension_task.json','L-CEXT1_CARD.md','USAGE.md','TEST_SCOPE.md'):
    (stage/name).write_bytes((AUTHOR/name).read_bytes())
for name in ('SOURCE_REVIEW.json','SOURCE_REVIEW.md','prepare_wrappers.py','assemble_extension.py','freeze_extension.py','candidate.diff'):
    (stage/'author'/name).write_bytes((AUTHOR/name).read_bytes())
for file in (AUTHOR/'candidate').rglob('*.py'):
    target=stage/file.relative_to(AUTHOR);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(file.read_bytes())
(stage/'protocol.json').write_bytes((AUTHOR/'protocol.proposed.json').read_bytes())
(stage/'author/authorization.json').write_bytes((AUTHOR/'authorization.proposed.json').read_bytes())
p=read(stage/'protocol.json');a=read(stage/'author/authorization.json')
assert a['protocol_sha256']==pin(stage/'protocol.json')
for name,expected in p['baseline_source_bindings'].items(): assert pin(ROOT/name)==expected,name
for name,expected in p['input_bindings'].items():
    if name.endswith('.json'): assert pin(ROOT/name)==expected,name
    else:
        sealed=next(row for row in p['old_scientific_inputs'] if row['path']==name)
        assert (ROOT/name).stat().st_size==sealed['bytes']
print(json.dumps(dict(status='frozen_not_installed_or_executed',protocol_sha256=pin(stage/'protocol.json'),sources=len(p['baseline_source_bindings']),old_payloads_opened=0)))
