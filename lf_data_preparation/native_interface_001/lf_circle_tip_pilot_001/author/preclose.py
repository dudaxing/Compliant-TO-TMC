"""Archive reviewed ordinary closure sources after the actual run has closed."""
import ast
from hashlib import sha256
import json
from pathlib import Path

AUTHOR=Path(__file__).resolve().parent
STAGE=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/lf_data_preparation/native_interface_001/lf_circle_tip_pilot_001')
read=lambda path:json.loads(path.read_bytes())
launch=read(STAGE/'pilot_launch.json')
actual=read(STAGE/'author/ACTUAL_REVIEW.json')
assert launch['card']=='L-CTIPPILOT1' and launch['status'] in ('pass','not_pass') and launch['cleanup_verified'] is True
assert actual['status'].startswith('pass') and not actual.get('blocking_findings',[])
review=read(AUTHOR/'CLOSURE_SOURCE_REVIEW.json')
assert review['status'].startswith('pass') and not review['blocking_findings']
for name,row in review['sources'].items():
    raw=(AUTHOR/name).read_bytes()
    assert len(raw)==row['bytes'] and sha256(raw).hexdigest()==row['sha256'],name
    ast.parse(raw,filename=name)
for name in ('CLOSURE_SOURCE_REVIEW.json','CLOSURE_SOURCE_REVIEW.md','monitor_pilot.py'):
    (STAGE/'author'/name).write_bytes((AUTHOR/name).read_bytes())
(STAGE/'author/preclose.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps(dict(status='ordinary_preclose_pass',sources=len(review['sources']),scientific_payload_reads=0)))
