"""Final frozen-byte/AST eligibility, without importing numerical candidates."""
import ast
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

A=Path(__file__).resolve().parent
BASE=Path('D:/hfh1_001')
def read(path): return json.loads(Path(path).read_bytes())
def pin(path):
    raw=path.read_bytes(); return dict(bytes=len(raw),sha256=sha256(raw).hexdigest())
raw=(BASE/'protocol.json').read_bytes(); p=json.loads(raw); root=Path(p['root_repository'])
frozen=read(A/'CANDIDATE_FREEZE.json')['protocol']
assert pin(BASE/'protocol.json')=={key:frozen[key] for key in ('bytes','sha256')}
assert p['stage']=='L-CTIPFHIGH1' and p['baseline']=='3a9a59dea0b55848814baef252018550249cefaa'
assert len(p['bindings'])==75 and len(p['production'])==57
for row in p['bindings']:
    assert Path(row['path']).suffix.lower() not in ('.npz','.zip','.png','.gif')
    assert pin(Path(row['path']))=={key:row[key] for key in ('bytes','sha256')},row['path']
assert p['selected_state_index']==12 and p['reference_requested_accepted_indices']==[0,2]
assert p['held_input_mean_mm']==1.06 and p['loads_half_N']==[.0002399800950672949,.0002561572865437846]
assert p['nmin_half_N']==(p['loads_half_N'][1]-p['loads_half_N'][0])/16
assert p['controller_seconds']==3600 and p['science_worker_total_seconds']==3900 and p['science_process_seconds']==3885
assert p['comparison_total_seconds']==60 and p['comparison_process_seconds']==45
assert p['display_and_root_QA_shared_seconds']==600 and p['viewer_process_seconds']==510
assert p['helper_seconds']==4800 and p['helper_content_exit_before_seconds']==4700
assert p['outer_seconds']==4860 and p['outer_owned_helper_job_deadline_seconds_from_top_start']==4730
assert p['clocks']['seal_entry_before_helper_seconds']==4745
assert p['clocks']['seal_members_before_helper_seconds']==4780
assert p['clocks']['archive_identity_before_helper_seconds']==4790
assert p['clocks']['all_seal_receipts_before_helper_seconds']==4800
assert p['memory_limit_bytes']==64*1024**3 and p['viewer_memory_limit_bytes']==8*1024**3
assert p['thread_environment']=={key:'16' for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')}
assert p['R_cross_actual_bound_N']==1.9536542042187397e-8
assert all(not (BASE/name).exists() for name in ('run_001','top_start.json','helper_start.json','root_qa.json','execution_evidence.zip'))
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=root).decode().strip()==p['baseline']
assert not subprocess.check_output(['git','status','--porcelain'],cwd=root).strip()
assert subprocess.check_output(['git','remote','get-url','origin'],cwd=root).decode().strip()=='https://github.com/dudaxing/Compliant-TO-TMC.git'
parsed=0
for row in p['bindings']:
    path=Path(row['path'])
    if path.suffix=='.py': ast.parse(path.read_bytes(),filename=str(path)); parsed+=1
assert parsed==63
reviews=[]; by_name={}
for name in ('PRELAUNCH_PHYSICS_CHECK','COMPARATOR_STATIC_REVIEW','VIEWER_STATIC_REVIEW','WORKER_WRAPPER_STATIC_REVIEW'):
    path=A/(name+'.json'); review=read(path)
    assert review['status'].lower().startswith('pass'),(name,review['status'])
    by_name[name]=review
    reviews.append(dict(path=str(path),status=review['status'],**pin(path)))
sha=sha256(raw).hexdigest()
assert sha in json.dumps(by_name['WORKER_WRAPPER_STATIC_REVIEW'])
assert sha in json.dumps(by_name['COMPARATOR_STATIC_REVIEW'])
mapping={'compare_high1.py':'COMPARATOR_STATIC_REVIEW','view_high1.py':'VIEWER_STATIC_REVIEW',
         'science_high1.py':'WORKER_WRAPPER_STATIC_REVIEW','helper_high1.py':'WORKER_WRAPPER_STATIC_REVIEW',
         'launch_high1.py':'WORKER_WRAPPER_STATIC_REVIEW'}
for filename,review_name in mapping.items():
    assert pin(BASE/filename)['sha256'] in json.dumps(by_name[review_name]),filename
result=dict(stage='L-CTIPFHIGH1',status='eligible_for_one_authorized_launch',
    created_utc=datetime.now(timezone.utc).isoformat(),protocol=pin(BASE/'protocol.json'),
    bindings_checked=75,production_sources_unchanged=57,AST_files=63,reviews=reviews,
    numerical_launched=False,scientific_calls=0,NPZ_reads=0,pixel_inspections=0,
    formal_head=p['baseline'],formal_clean=True,unique_markers_absent=True,
    unique_command=[p['python_executable'],'-X','utf8','-B',str(BASE/'launch_high1.py')])
with (A/'EXECUTION_ELIGIBILITY.json').open('x',encoding='utf-8') as stream:
    json.dump(result,stream,ensure_ascii=False,indent=2); stream.write('\n')
with (A/'LIVE_HANDOFF.json').open('x',encoding='utf-8') as stream:
    json.dump(dict(stage='L-CTIPFHIGH1',status='eligible_not_launched',protocol_sha256=sha,
        command=result['unique_command'],
        QA='When helper.log says ready, inspect five new PNG once each, then atomically rename a complete root_qa.json receipt. No GIF decode, rerender or new science.',
        original_window='controller3600/science3900/compare60/shared display+QA600/helper4800/outer4860; no restart or repair run'),stream,ensure_ascii=False,indent=2)
copies=BASE/'prelaunch_reviews'; copies.mkdir()
for path in A.iterdir():
    if path.suffix in ('.md','.json') and path.name not in ('LIVE_HANDOFF.json',):
        (copies/path.name).write_bytes(path.read_bytes())
print(json.dumps(dict(status=result['status'],bindings=75,production=57,AST=63,reviews=4)))
