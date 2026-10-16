"""Copy reviewed ordinary bytes into a new stage; no scientific payload reads."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).resolve().parent
STAGE=ROOT/'lf_data_preparation/native_interface_001/lf_circle_input_preparation_001'
BASE='d2cad344a3675cc1129c4786629f56e5678cb895'
read=lambda p:json.loads(p.read_bytes())
pin=lambda p:sha256(p.read_bytes()).hexdigest()
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==BASE
assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()
assert not STAGE.exists()
review=read(AUTHOR/'SOURCE_REVIEW.json')
assert review['status'].startswith('pass') and not review.get('blocking_findings',[])
STAGE.mkdir(parents=True,exist_ok=False)
(STAGE/'author').mkdir()
for name in ('execute_preparation.py','plot_circle.py','launch_preparation.py','L-CPREP1_CARD.md'):
    (STAGE/name).write_bytes((AUTHOR/name).read_bytes())
for name in ('SOURCE_REVIEW.json','SOURCE_REVIEW.md','assemble_preparation.py','freeze_preparation.py'):
    (STAGE/'author'/name).write_bytes((AUTHOR/name).read_bytes())
(STAGE/'protocol.json').write_bytes((AUTHOR/'protocol.proposed.json').read_bytes())
(STAGE/'author/authorization.json').write_bytes((AUTHOR/'authorization.proposed.json').read_bytes())
protocol=read(STAGE/'protocol.json')
auth=read(STAGE/'author/authorization.json')
assert auth['protocol_sha256']==pin(STAGE/'protocol.json')
for name,expected in protocol['source_bindings'].items():
    assert (ROOT/name).suffix.lower() in ('.py','.toml')
    assert pin(ROOT/name)==expected,name
for name,expected in protocol['input_bindings'].items():
    if (ROOT/name).suffix.lower()=='.json':
        assert pin(ROOT/name)==expected,name
    else:
        assert name==protocol['old_scientific_input']['path']
        assert (ROOT/name).stat().st_size==protocol['old_scientific_input']['bytes']
print(json.dumps(dict(status='frozen_not_executed',protocol_sha256=pin(STAGE/'protocol.json'),
    source_bindings=len(protocol['source_bindings']),old_NPZ_payloads_opened=0,new_default_HF_files=0)))
