"""Final ordinary/AST eligibility, without importing any numerical candidate."""
import ast
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

AUTHOR=Path(__file__).resolve().parent
BASE=Path('D:/hfr1_001')
def read(path): return json.loads(Path(path).read_bytes())
def pin(path):
    raw=path.read_bytes(); return dict(bytes=len(raw),sha256=sha256(raw).hexdigest())
raw=(BASE/'protocol.json').read_bytes()
assert sha256(raw).hexdigest()=='b07ac9a43bb421011f6469dc01b71f17dfe43345364fe02cdcc390951081da83'
p=json.loads(raw); root=Path(p['root_repository'])
for row in p['bindings']:
    assert Path(row['path']).suffix.lower()!='.npz'
    assert pin(Path(row['path']))=={k:row[k] for k in ('bytes','sha256')},row['path']
assert len(p['bindings'])==75 and len(p['production'])==57
assert p['controller_seconds']==1800 and p['science_worker_total_seconds']==1900
assert p['comparison_total_seconds']==60 and p['display_and_root_QA_shared_seconds']==600
assert p['helper_seconds']==2700 and p['outer_seconds']==2760
assert p['memory_limit_bytes']==64*1024**3 and p['viewer_memory_limit_bytes']==8*1024**3
assert p['thread_environment']=={k:'16' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')}
assert p['loads_half_N']==[3.686421133658022e-5,4.3272306948756724e-5]
assert p['nmin_half_N']==(p['loads_half_N'][1]-p['loads_half_N'][0])/16
assert all(not (BASE/name).exists() for name in ('run_001','top_start.json','helper_start.json','root_qa.json','execution_evidence.zip'))
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=root).decode().strip()==p['baseline']
assert not subprocess.check_output(['git','status','--porcelain'],cwd=root).strip()
assert subprocess.check_output(['git','remote','get-url','origin'],cwd=root).decode().strip()=='https://github.com/dudaxing/Compliant-TO-TMC.git'
parsed=0
for row in p['bindings']:
    path=Path(row['path'])
    if path.suffix=='.py': ast.parse(path.read_bytes(),filename=str(path)); parsed+=1
assert parsed==63
reviews=[]
for name in ('PRELAUNCH_PHYSICS_CHECK','COMPARATOR_STATIC_REVIEW','VIEWER_STATIC_REVIEW','WORKER_WRAPPER_STATIC_REVIEW'):
    path=AUTHOR/(name+'.json'); review=read(path)
    assert review['status'].lower().startswith('pass'),(name,review['status'])
    reviews.append(dict(path=str(path),status=review['status'],**pin(path)))
wrapper=read(AUTHOR/'WORKER_WRAPPER_STATIC_REVIEW.json')
assert sha256(raw).hexdigest() in json.dumps(wrapper)
row=dict(stage='L-CTIPFREAL1',status='eligible_for_one_authorized_launch',
    created_utc=datetime.now(timezone.utc).isoformat(),protocol=pin(BASE/'protocol.json'),
    bindings_checked=75,production_sources_unchanged=57,AST_files=63,reviews=reviews,
    numerical_launched=False,scientific_calls=0,NPZ_reads=0,pixel_inspections=0,
    formal_head=p['baseline'],formal_clean=True,unique_markers_absent=True,
    unique_command=[p['python_executable'],'-X','utf8','-B',str(BASE/'launch_freal1.py')])
with (AUTHOR/'EXECUTION_ELIGIBILITY.json').open('x',encoding='utf-8') as stream:
    json.dump(row,stream,ensure_ascii=False,indent=2); stream.write('\n')
with (AUTHOR/'LIVE_HANDOFF.json').open('x',encoding='utf-8') as stream:
    json.dump(dict(stage='L-CTIPFREAL1',status='eligible_not_launched',protocol_sha256=sha256(raw).hexdigest(),
        command=row['unique_command'],QA='When helper.log says ready, inspect the five new PNG once each, then atomically rename a complete root_qa.json receipt. No GIF decode, rerender or new science.',
        original_window='controller1800/science1900/compare60/shared display+QA600/helper2700/outer2760; no restart or repair run'),stream,ensure_ascii=False,indent=2)
copies=BASE/'prelaunch_reviews'; copies.mkdir()
for path in AUTHOR.iterdir():
    if path.suffix in ('.md','.json') and path.name not in ('LIVE_HANDOFF.json',):
        (copies/path.name).write_bytes(path.read_bytes())
print(json.dumps(dict(status=row['status'],bindings=75,production57='unchanged',AST=63,reviews=4)))
