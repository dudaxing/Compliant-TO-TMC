"""Ordinary final binding checks; never import candidates or collect tests."""
import ast
from datetime import datetime,timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

A=Path(__file__).resolve().parent
B=Path('D:/hfrs1_001')
R=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
def identity(path):
    raw=path.read_bytes();return dict(bytes=len(raw),sha256=sha256(raw).hexdigest())
def write(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2);stream.write('\n')
p=json.loads((B/'protocol.json').read_bytes())
assert not any((B/name).exists() for name in ('run_001','top_start.json','outer_start.json','root_qa.json','execution_evidence.zip'))
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R).decode().strip()==p['baseline']
assert not subprocess.check_output(['git','status','--porcelain'],cwd=R)
for row in p['bindings']:
    assert identity(Path(row['path']))=={k:row[k] for k in ('bytes','sha256')},row['path']
assert len(p['original_production'])==57 and len(p['install_files'])==3
assert (p['tests_seconds'],p['viewer_seconds'],p['helper_seconds'],p['outer_seconds'])==(480,60,660,720)
assert p['memory_limit_bytes']==8*1024**3
ack=json.loads((A/'PROTOCOL_ACK.json').read_bytes())
assert ack['status'].startswith('PASS') and ack['protocol']['sha256']==identity(B/'protocol.json')['sha256']
test=json.loads((A/'TEST_STATIC_REVIEW.json').read_bytes())
assert test['file']['sha256']==identity(B/'test_force_resume.py')['sha256']
for name in ('API_STATIC_REVIEW','CONTROLLER_STATIC_REVIEW','TEST_STATIC_REVIEW','WRAPPER_VIEWER_STATIC_REVIEW'):
    assert (A/(name+'.json')).read_bytes()==(B/'prelaunch_reviews'/(name+'.json')).read_bytes(),name
record=dict(stage='L-CTIPFRESUME1',status='PASS_ELIGIBLE_FOR_UNIQUE_AUTHORIZED_LAUNCH',
    created_utc=datetime.now(timezone.utc).isoformat(),baseline=p['baseline'],
    protocol=identity(B/'protocol.json'),bindings_verified=len(p['bindings']),
    independent_source_reviews=4,protocol_independent_ack=True,
    source_AST_only_before_launch=True,HF_imports_before_launch=0,F=0,T=0,HP=0,tests_before_launch=0,
    new_modules_installed=False,numerical_launched=False,
    unique_command=[p['python_executable'],'-X','utf8','-B',str(B/'launch_resume1.py')])
write(A/'EXECUTION_ELIGIBILITY.json',record)
write(A/'LIVE_HANDOFF.json',dict(stage='L-CTIPFRESUME1',status='eligible_unique_command_not_launched',
    command=record['unique_command'],protocol_sha256=record['protocol']['sha256'],
    numerical_launched=False,do_not_retry_or_reopen=True,
    QA='When outer.log reports ready and helper/viewer cleanup passed, inspect only run_001/view/force_resume.png once; atomic root_qa.json before display+55 and helper+580. No rerender.',
    limits='tests480/sharedDisplayQA60/helper660/outer720,8GiB/cap16; first unexpected terminal failure stops; no realr9/HP'))
print(json.dumps(dict(status=record['status'],bindings=record['bindings_verified'],protocol=record['protocol'])))
