"""Freeze source and ordinary protocol only, without importing candidate HF."""
import ast
from datetime import datetime,timezone
from hashlib import sha256
from importlib.metadata import version
import json
from pathlib import Path
import shutil
import subprocess
import sys

A=Path(__file__).resolve().parent
B=Path('D:/hfrs1_001')
R=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
C=B/'candidate/hf_repo'
PYTHON='D:/Coding/Diversity TO/Compliant-TO-TMC/.venv-handoff/Scripts/python.exe'
BASELINE='66794cd8e9e84c514a8deff14fe7be3f76cd6f05'
def git(*args): return subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false',*args],cwd=R)
def pin(path):
    raw=path.read_bytes();return dict(path=path.resolve().as_posix(),bytes=len(raw),sha256=sha256(raw).hexdigest())
def write(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
def main():
    assert git('rev-parse','HEAD').decode().strip()==BASELINE and not git('status','--porcelain')
    assert not (B/'protocol.json').exists() and not (B/'run_001').exists()
    original=sorted((R/'hf_repo/src/hf_eval').glob('*.py')); assert len(original)==57
    names=('split_guided_force.py','native_guided_force.py','native_guided_force_resume.py')
    for p in original:
        if p.name not in names:
            assert p.read_bytes()==(C/'src/hf_eval'/p.name).read_bytes(),p.name
    assert len(list((C/'src/hf_eval').glob('*.py')))==58
    assert not (R/'hf_repo/src/hf_eval/native_guided_force_resume.py').exists()
    test=B/'test_force_resume.py'; tree=ast.parse(test.read_bytes())
    tests=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')]
    assert len(tests)==12 and all(not n.decorator_list for n in tests)
    assert [n.name.split('_')[1] for n in tests]==[f'V{i:02d}' for i in range(1,13)]
    assert sha256((B/'windows_owned_process_sup2.py').read_bytes()).hexdigest()=='b5f149e1cd3d6d9b4ad392123e410b786606f120f2e078139b7bacc97f2d9499'
    source=sorted(p for p in B.rglob('*') if p.is_file())
    for p in source:
        if p.suffix=='.py':ast.parse(p.read_bytes(),filename=str(p))
    reviews=('API_STATIC_REVIEW.json','CONTROLLER_STATIC_REVIEW.json','TEST_STATIC_REVIEW.json','WRAPPER_VIEWER_STATIC_REVIEW.json')
    for name in reviews:
        value=json.loads((A/name).read_bytes())
        assert value['status'].startswith('PASS'),name
    command=[PYTHON,'-X','utf8','-B','-m','pytest','-q','-x','--maxfail=1','-p','no:cacheprovider',str(test),
        '--basetemp',str(B/'run_001/tmp'),'--junitxml',str(B/'run_001/pytest.xml')]
    protocol=dict(stage='L-CTIPFRESUME1',status='frozen_ready_for_unique_authorized_launch',baseline=BASELINE,
        root_repository=R.as_posix(),runtime_base=B.as_posix(),candidate_hf_repo=C.as_posix(),candidate_source=(C/'src').as_posix(),python_executable=PYTHON,
        tests_seconds=480,viewer_seconds=60,helper_seconds=660,outer_seconds=720,memory_limit_bytes=8*1024**3,
        thread_environment={key:'16' for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')},
        clocks=dict(tests_process=465,tests_cleanup_reserve=15,viewer_process=35,viewer_cleanup_reserve=10,
            shared_display_QA=60,QA_finish_before_display=55,helper_content_supervision_deadline=565,
            helper_cleanup_before=570,outer_QA_before_helper=580,outer_return_before_helper=590,
            top_owned_outer_deadline_from_top=595,installation_before_helper=610,
            seal_entry_before_helper=620,seal_members_before_helper=645,archive_identity_before_helper=650,
            helper_total_limit=660,outer_total_limit=720),
        test_command=command,maximum_real_paths=7,expected_methods=12,maximum_finite_calls=37,
        original_production=[pin(p) for p in original],
        install_files=[dict(source=(C/'src/hf_eval'/name).as_posix(),target=(R/'hf_repo/src/hf_eval'/name).as_posix(),
            existing=(name!='native_guided_force_resume.py'),**{k:v for k,v in pin(C/'src/hf_eval'/name).items() if k!='path'}) for name in names],
        bindings=[pin(p) for p in source]+[pin(p) for p in original],
        independent_static_reviews=[pin(A/name) for name in reviews],
        viewer=dict(ordinary_JSON_sources=1,PNG=1,pixel_inspections_max=1,NPZ_decodes=0,HF_imports=0),
        new_HP=0,real_r9_paths=0,external_retries=0,production_installation_allowed_only_after_all_PASS=True,
        numerical_launched=False,created_utc=datetime.now(timezone.utc).isoformat())
    write(B/'protocol.json',protocol);shutil.copyfile(B/'protocol.json',A/'protocol.json')
    record=dict(stage='L-CTIPFRESUME1',status='frozen_pending_protocol_ack_and_eligibility',baseline=BASELINE,
        protocol=pin(B/'protocol.json'),bindings=len(protocol['bindings']),AST_files=sum(p.suffix=='.py' for p in source),
        unchanged_originals=55,modified_originals=2,new_modules=1,methods=12,maximum_real_paths=7,maximum_finite_calls=37,
        python=sys.version,environment={name:version(name) for name in ('numpy','scipy','matplotlib','jax','jaxlib','pytest','psutil')},dependency_changes=0,
        unique_command=[PYTHON,'-X','utf8','-B',str(B/'launch_resume1.py')],numerical_launched=False,production_installed=False)
    write(A/'CANDIDATE_FREEZE.json',record)
    print(json.dumps(dict(status=record['status'],bindings=record['bindings'],protocol=record['protocol'])))
if __name__=='__main__':main()
