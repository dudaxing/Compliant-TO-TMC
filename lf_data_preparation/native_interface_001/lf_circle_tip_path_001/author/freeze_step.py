"""Check the finite static-review seal immediately before the unique launch."""
from hashlib import sha256
import json
from pathlib import Path

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).resolve().parent
STAGE=ROOT/'lf_data_preparation/native_interface_001/lf_circle_tip_path_001'
protocol=json.loads((STAGE/'protocol.json').read_bytes())
review=json.loads((AUTHOR/'SOURCE_REVIEW.json').read_bytes())
assert review['status'].startswith('pass') and not review.get('blockers',[])
assert review['protocol_sha256']==sha256((STAGE/'protocol.json').read_bytes()).hexdigest()
for name,pin in review['reviewed_author_sha256'].items():
    assert sha256((AUTHOR/name).read_bytes()).hexdigest()==pin,name
assert not (STAGE/'step_launch.json').exists() and not (STAGE/'run_001').exists()
for name,pin in protocol['source_bindings'].items():
    assert sha256((ROOT/name).read_bytes()).hexdigest()==pin,name
for name in ('SOURCE_REVIEW.json','SOURCE_REVIEW.md'):
    target=STAGE/'author'/name
    assert not target.exists()
    target.write_bytes((AUTHOR/name).read_bytes())
print(json.dumps(dict(status='frozen_not_executed',protocol_sha256=sha256((STAGE/'protocol.json').read_bytes()).hexdigest())))
