"""Freeze one approved protocol using source/ordinary bytes only, no HF imports."""
import ast
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

AUTHOR=Path(__file__).resolve().parent
BASE=Path('D:/hfr1_001')
ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
BASELINE='e80009232796d158b466fbd887cde82fdd7859fe'
def read(path): return json.loads(Path(path).read_bytes())
def pin(path):
    raw=path.read_bytes(); return dict(path=str(path.resolve()),bytes=len(raw),sha256=sha256(raw).hexdigest())
def write(path,row):
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(row,stream,ensure_ascii=False,indent=2); stream.write('\n')
assert not (BASE/'protocol.json').exists()
assert not any((BASE/name).exists() for name in ('run_001','top_start.json','helper_start.json','root_qa.json','execution_evidence.zip'))
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()==BASELINE
assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT).strip()
source=read(BASE/'source_binding.json')
production=sorted((ROOT/'hf_repo/src/hf_eval').glob('*.py'))
assert len(production)==57
for row in read(ROOT/'lf_data_preparation/native_interface_001/lf_circle_tip_force_control_real_preparation_001/author/PRODUCTION_IDENTITY.json')['files']:
    actual=pin(ROOT/row['path'])
    assert all(actual[key]==row[key] for key in ('bytes','sha256'))
scripts=[BASE/name for name in ('science_freal1.py','compare_freal1.py','view_freal1.py','helper_freal1.py','launch_freal1.py','windows_owned_process_sup2.py')]
ordinary=[BASE/name for name in ('source_binding.json','observer_binding.json','approved_card.md','authorization.json')]
for row in source['ordinary_files']:
    actual=pin(Path(row['path']))
    assert all(actual[key]==row[key] for key in ('bytes','sha256'))
    ordinary.append(Path(row['path']))
files=production+scripts+ordinary
assert len(files)==len(set(files))
for path in production+scripts:
    ast.parse(path.read_bytes(),filename=str(path))
p=dict(stage='L-CTIPFREAL1',schema_version='hf-formal-force-protocol-1',
    status='frozen_for_one_authorized_execution_after_final_static_eligibility',
    baseline=BASELINE,root_repository=str(ROOT),runtime_base=str(BASE),
    production_src=str(ROOT/'hf_repo/src'),
    python_executable='D:/Coding/Diversity TO/Compliant-TO-TMC/.venv-handoff/Scripts/python.exe',
    parent_result=source['parent_binding']['result_path'],reference_result=source['reference_binding']['result_path'],
    source_binding_file=str(BASE/'source_binding.json'),observer_binding_file=str(BASE/'observer_binding.json'),
    selected_state_index=2,loads_half_N=[3.686421133658022e-5,4.3272306948756724e-5],
    nmin_half_N=4.0050597576103156e-7,controller_seconds=1800,
    science_worker_total_seconds=1900,science_process_seconds=1885,science_cleanup_and_receipt_reserve_seconds=15,
    comparison_total_seconds=60,comparison_process_seconds=45,
    display_and_root_QA_shared_seconds=600,viewer_process_seconds=510,
    root_QA_end_before_shared_display_seconds=585,
    helper_seconds=2700,helper_content_exit_before_seconds=2600,
    outer_seconds=2760,outer_owned_helper_job_deadline_seconds_from_top_start=2630,
    clocks=dict(outer='launch_freal1 START before ordinary imports',
        helper='helper_freal1 START before ordinary imports',
        display='helper records display_begin before viewer process creation',
        seal_entry_before_helper_seconds=2645,seal_members_before_helper_seconds=2680,
        archive_identity_before_helper_seconds=2690,all_seal_receipts_before_helper_seconds=2700),
    memory_limit_bytes=64*1024**3,viewer_memory_limit_bytes=8*1024**3,
    thread_environment={key:'16' for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')},
    image_names=['01_actual_geometry.png','02_P_q_cross_check.png','03_force_components_and_R.png',
        '04_tip_right_geometry_global_J_Hu.png','05_convergence_and_gates.png'],
    animation_name='actual_force_states.gif',root_png_inspection_maximum=5,
    maximum_accepted_states=17,unique_scientific_API_calls=1,old_NPZ_unique_paths_in_API=3,
    API_decoded_fields_on_completed_admission=6,comparison_state_NPZ_paths=4,comparison_decoded_fields=8,
    total_unique_NPZ_read_paths=7,total_decoded_fields=14,
    q_and_full_field_cross_bound_mm=1e-6,R_cross_absolute_floor_N=1e-10,R_cross_relative_factor=1e-7,
    bindings=[pin(path) for path in files],production=[pin(path) for path in production],
    new_HP=0,new_tests=0,production_modifications=0,external_retries=0,
    numerical_launched=False,created_utc=datetime.now(timezone.utc).isoformat())
assert p['loads_half_N']==source['reference_binding']['load_candidates_half_N']
assert p['nmin_half_N']==(p['loads_half_N'][1]-p['loads_half_N'][0])/16
write(BASE/'protocol.json',p)
(AUTHOR/'protocol.json').write_bytes((BASE/'protocol.json').read_bytes())
write(AUTHOR/'CANDIDATE_FREEZE.json',dict(stage='L-CTIPFREAL1',status='frozen_pending_final_protocol_ack_and_eligibility',
    baseline=BASELINE,protocol=pin(BASE/'protocol.json'),bindings=len(files),
    original_production_unchanged=57,AST_source_files=len(production+scripts),
    unique_command=[p['python_executable'],'-X','utf8','-B',str(BASE/'launch_freal1.py')],
    runtime_inputs_not_copied_or_decoded=True,numerical_launched=False,
    candidate_imports=0,pytest_or_collect_runs=0,scientific_calls=0,pixel_inspections=0))
print(json.dumps(dict(status='frozen',bindings=len(files),production=57,AST=len(production+scripts),protocol=pin(BASE/'protocol.json'))))
