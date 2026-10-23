"""Freeze ordinary sources and protocol only; never import candidate mechanics."""
import ast
from datetime import datetime, timezone
from hashlib import sha256
from importlib.metadata import version
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
BASE=Path('D:/hfl1_001')
AUTHOR=Path(__file__).parent
PYTHON='D:/Coding/Diversity TO/Compliant-TO-TMC/.venv-handoff/Scripts/python.exe'
BASELINE='5c496c808d78e20ad26541febbcc6b49ca3ab647'
CANDIDATE=BASE/'candidate/hf_repo'

def git(*args):
    return subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false',*args],cwd=ROOT)

def pin(path):
    raw=path.read_bytes()
    return dict(path=str(path.resolve()),bytes=len(raw),sha256=sha256(raw).hexdigest())

def write(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False)
        stream.write('\n')

def main():
    assert git('rev-parse','HEAD').decode().strip()==BASELINE
    assert not git('status','--porcelain')
    assert not (BASE/'protocol.json').exists() and not (BASE/'run_001').exists()
    original=sorted((ROOT/'hf_repo/src').rglob('*.py'))
    assert len(original)==55
    for p in original:
        assert p.read_bytes()==(CANDIDATE/'src'/p.relative_to(ROOT/'hf_repo/src')).read_bytes()
    new_names=('split_guided_force.py','native_guided_force.py')
    assert len(list((CANDIDATE/'src').rglob('*.py')))==57
    for name in new_names:
        assert not (ROOT/'hf_repo/src/hf_eval'/name).exists()
    test=CANDIDATE/'tests/test_native_guided_force.py'
    methods=[node for node in ast.parse(test.read_bytes()).body
             if isinstance(node,ast.FunctionDef) and node.name.startswith('test_')]
    assert len(methods)==8
    assert test.read_bytes() and sha256(test.read_bytes()).hexdigest()=='23b9b1a84edbf48beb9c2641957a094b977cb6901058d9336e89c675c62191f5'
    assert (CANDIDATE/'tests/test_split_displacement.py').read_bytes()==(ROOT/'hf_repo/tests/test_split_displacement.py').read_bytes()
    source=list((CANDIDATE/'src').rglob('*.py'))+list((CANDIDATE/'tests').glob('*.py'))
    source += [CANDIDATE/'pyproject.toml']+[BASE/name for name in
        ('run_fload1.py','outer_fload1.py','launch_fload1.py','render_fload1.py',
         'windows_owned_process_sup2.py','approved_card.md','authorization.json')]
    for p in source:
        if p.suffix=='.py':
            ast.parse(p.read_bytes(),filename=str(p))
    assert sha256((BASE/'windows_owned_process_sup2.py').read_bytes()).hexdigest()=='b5f149e1cd3d6d9b4ad392123e410b786606f120f2e078139b7bacc97f2d9499'
    protocol=dict(stage='L-CTIPFLOAD1',schema='hf-guided-force-validation-protocol-1',
        status='frozen_ready_for_unique_authorized_launch',
        scope='User-approved candidate. Root must finish independent wrapper/viewer review and eligibility before invoking unique command.',
        baseline=BASELINE,root_repository=str(ROOT),runtime_base=str(BASE),candidate_hf_repo=str(CANDIDATE),
        candidate_source=str(CANDIDATE/'src'),python_executable=PYTHON,
        tests_seconds=300,viewer_seconds=60,helper_seconds=480,outer_seconds=540,
        clocks=dict(outer='launch_fload1 first executable line before imports',
            helper='outer_fload1 first executable line before imports',helper_content_end=400,
            helper_supervisor_deadline=410,root_QA_deadline=440,install_end=450,
            outer_owned_child_deadline_relative_to_outer=460,seal_entry_before_helper=465,
            seal_members_before_helper=475,archive_identity_before_helper=478,
            helper_total_limit=480,outer_total_limit=540),
        memory_limit_bytes=8*1024**3,
        thread_environment={k:'16' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')},
        expected_expanded_items=17,expected_new_methods=8,expected_new_real_16cell_paths=4,
        expected_new_injected_or_rejected_calls=30,expected_legacy_real_2cell_paths=1,
        expected_legacy_synthetic_calls=11,maximum_total_real_paths=5,maximum_total_injected_or_rejected=43,
        partial_is_both_real_and_injected=1,
        test_command=[PYTHON,'-X','utf8','-B','-m','pytest','-q','-x','-p','no:cacheprovider',
            str(CANDIDATE/'tests/test_split_displacement.py'),str(test),'--basetemp',str(BASE/'run_001/tmp'),
            '--junitxml',str(BASE/'run_001/pytest.xml')],
        original_production=[pin(p) for p in original],
        install_files=[dict(source=str(CANDIDATE/'src/hf_eval'/name),
            target=str(ROOT/'hf_repo/src/hf_eval'/name),**{k:v for k,v in pin(CANDIDATE/'src/hf_eval'/name).items() if k!='path'})
            for name in new_names],
        bindings=[pin(p) for p in sorted(source)],
        viewer=dict(ordinary_json_files=3,new_pngs=1,NPZ_fields=0,scientific_calls=0,root_pixel_inspections=1),
        new_HP=0,real_r9_paths=0,old_production_modifications=0,external_retries=0,
        physics_scope='Fresh 16-cell/50-field-DOF fixture only; original full-size gripper physics unchanged',
        numerical_launched=False,new_modules_installed=False,
        created_utc=datetime.now(timezone.utc).isoformat())
    write(BASE/'protocol.json',protocol)
    environment=dict(python=sys.version,executable=sys.executable,packages={name:version(name) for name in
        ('numpy','scipy','matplotlib','jax','jaxlib','pytest','psutil')},dependency_changes=0)
    write(AUTHOR/'CANDIDATE_FREEZE.json',dict(stage='L-CTIPFLOAD1',status='source_frozen_review_before_launch',
        baseline=BASELINE,protocol=pin(BASE/'protocol.json'),source_bindings=len(source),
        old_source_files_identical=55,new_source_files=2,new_tests_methods=8,environment=environment,
        unique_command=[PYTHON,'-X','utf8','-B',str(BASE/'launch_fload1.py')],
        numerical_launched=False,default_source_installed=False))
    shutil.copyfile(BASE/'protocol.json',AUTHOR/'protocol.json')
    print(json.dumps(dict(status='source_frozen_pending_final_eligibility',protocol=pin(BASE/'protocol.json'),
        bindings=len(source),new_methods=len(methods),new_real_paths=4,new_synthetic=30)))

if __name__=='__main__':
    main()
