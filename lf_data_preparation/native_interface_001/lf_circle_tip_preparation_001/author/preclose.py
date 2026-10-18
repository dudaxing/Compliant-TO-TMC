"""Ordinary source preflight and review archival before the single closure."""
import ast
from hashlib import sha256
import json
from pathlib import Path

AUTHOR=Path(__file__).resolve().parent
STAGE=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/lf_data_preparation/native_interface_001/lf_circle_tip_preparation_001')
review=json.loads((AUTHOR/'CLOSURE_SOURCE_REVIEW.json').read_bytes())
assert review['status']=='pass_closure_source_review' and not review['blocking_findings']
for name,row in review['reviewed_sources'].items():
    raw=(AUTHOR/name).read_bytes()
    assert len(raw)==row['bytes'] and sha256(raw).hexdigest()==row['sha256'],name
    if name.endswith('.py'):ast.parse(raw,filename=name)
for name in ('CLOSURE_SOURCE_REVIEW.json','CLOSURE_SOURCE_REVIEW.md'):
    (STAGE/'author'/name).write_bytes((AUTHOR/name).read_bytes())
(STAGE/'author/preclose.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps(dict(status='ordinary_preclose_pass',sources=len(review['reviewed_sources']),scientific_payload_reads=0)))
