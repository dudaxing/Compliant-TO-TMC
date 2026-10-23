"""One ordinary prelaunch identity/AST audit; no candidate imports."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

AUTHOR = Path(__file__).resolve().parent
BASE = Path('D:/hfl1_001')
raw = (BASE/'protocol.json').read_bytes()
sha = hashlib.sha256(raw).hexdigest()
assert sha == '3476f6d6136181c498ca80bfa422c7c334a160f5cda2ee530b2c714c5a37ece0'
p = json.loads(raw)
root = Path(p['root_repository'])
def ident(path):
    data = Path(path).read_bytes()
    return dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
for item in p['bindings'] + p['original_production']:
    assert ident(item['path']) == {k:item[k] for k in ('bytes','sha256')}, item['path']
assert len(p['bindings']) == 67 and len(p['original_production']) == 55
for item in p['original_production']:
    candidate = BASE/'candidate/hf_repo/src/hf_eval'/Path(item['path']).name
    assert ident(candidate) == {k:item[k] for k in ('bytes','sha256')}
for item in p['install_files']:
    assert not Path(item['target']).exists()
assert not any((BASE/name).exists() for name in ('run_001','top_start.json','outer_start.json','root_qa.json','execution_evidence.zip'))
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=root).decode().strip() == p['baseline']
assert not subprocess.check_output(['git','status','--porcelain'],cwd=root).strip()
assert subprocess.check_output(['git','remote','get-url','origin'],cwd=root).decode().strip() == 'https://github.com/dudaxing/Compliant-TO-TMC.git'
parsed = []
for item in p['bindings']:
    path = Path(item['path'])
    if path.suffix == '.py':
        ast.parse(path.read_bytes(), filename=str(path))
        parsed.append(str(path))
reviews = []
for name in ('API','CONTROLLER','TEST','VIEWER','WRAPPER'):
    path = AUTHOR/(name+'_STATIC_REVIEW.json')
    review = json.loads(path.read_bytes())
    assert review['status'].startswith('pass'), (name, review['status'])
    reviews.append(dict(path=str(path), **ident(path), status=review['status']))
viewer = json.loads((AUTHOR/'VIEWER_STATIC_REVIEW.json').read_bytes())
assert sha in json.dumps(viewer['final_protocol_ack'])
record = dict(stage='L-CTIPFLOAD1',status='eligible_for_one_authorized_launch',
    created_utc=datetime.now(timezone.utc).isoformat(),protocol=dict(bytes=len(raw),sha256=sha),
    bindings_checked=67,original_production_unchanged=55,AST_files=len(parsed),reviews=reviews,
    formal_head=p['baseline'],formal_clean=True,unique_markers_absent=True,new_targets_absent=True,
    candidate_imports=0,pytest_runs=0,scientific_calls=0,pixel_inspections=0,
    unique_command=[p['python_executable'],'-X','utf8','-B',str(BASE/'launch_fload1.py')])
with (AUTHOR/'EXECUTION_ELIGIBILITY.json').open('x',encoding='utf-8') as stream:
    json.dump(record,stream,ensure_ascii=False,indent=2); stream.write('\n')
with (AUTHOR/'LIVE_HANDOFF.json').open('x',encoding='utf-8') as stream:
    json.dump(dict(stage='L-CTIPFLOAD1',status='eligible_not_launched',
        protocol_sha256=sha,command=record['unique_command'],
        QA='One view_image only after ready phase; write complete JSON to temporary sibling then atomically rename to root_qa.json.',
        original_window='tests300/view60/helper480/outer540; no restart or repair run'),stream,ensure_ascii=False,indent=2)
print(json.dumps(dict(status=record['status'],bindings=67,original55='unchanged',AST=len(parsed),reviews=5)))
