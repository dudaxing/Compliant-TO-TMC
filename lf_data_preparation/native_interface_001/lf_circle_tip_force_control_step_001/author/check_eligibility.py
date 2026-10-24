# Final read-only source/protocol eligibility;not a candidate test or science run.
import ast
from datetime import datetime,timezone
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
A=Path(__file__).resolve().parent;B=Path('D:/hfst1_001')
R=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
def read(p):return json.loads(Path(p).read_bytes())
def pin(p):
 raw=p.read_bytes();return dict(path=p.as_posix(),bytes=len(raw),sha256=sha256(raw).hexdigest())
p=read(B/'protocol.json');review=read(A/'RUNTIME_STATIC_REVIEW.json')
assert review['status'].startswith('PASS')
assert pin(B/'protocol.json')==review['protocol']
assert p['baseline']==subprocess.check_output(['git','rev-parse','HEAD'],cwd=R).decode().strip()
assert not subprocess.check_output(['git','status','--porcelain'],cwd=R).strip()
assert read(B/'authorization.json')['approved'] is True
assert not any((B/n).exists() for n in ('top_start.json','helper_start.json','run_001','root_qa.json','execution_evidence.zip'))
for row in p['bindings']:
 q=Path(row['path']);assert q.suffix.lower() not in ('.npz','.zip','.png','.gif','.svg')
 assert pin(q)==row,row['path']
 if q.suffix=='.py':ast.parse(q.read_bytes(),filename=str(q))
for row in review['source_files']:assert pin(Path(row['path']))==row
assert len(p['production'])==58 and len(p['bindings'])==84
for n in ('RUNTIME_STATIC_REVIEW.md','RUNTIME_STATIC_REVIEW.json'):
 target=B/'reviews'/n;assert not target.exists();shutil.copyfile(A/n,target)
row=dict(stage='L-CTIPFSTEP1',status='PASS_ELIGIBLE_FOR_ONE_APPROVED_LAUNCH',created_utc=datetime.now(timezone.utc).isoformat(),
 protocol=pin(B/'protocol.json'),independent_review=pin(A/'RUNTIME_STATIC_REVIEW.json'),baseline=p['baseline'],
 bindings_verified=len(p['bindings']),production_unchanged=58,source_AST_checks_only=True,
 unique_command=[p['python_executable'],'-X','utf8','-B',str(B/'launch_step1.py')],
 scientific_calls=0,HF_imports=0,NPZ_reads_or_hashes=0,tests_run=0,launches_so_far=0)
with (A/'EXECUTION_ELIGIBILITY.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(row,f,ensure_ascii=False,indent=2);f.write('\n')
shutil.copyfile(A/'EXECUTION_ELIGIBILITY.json',B/'reviews/EXECUTION_ELIGIBILITY.json')
print(json.dumps(row))
