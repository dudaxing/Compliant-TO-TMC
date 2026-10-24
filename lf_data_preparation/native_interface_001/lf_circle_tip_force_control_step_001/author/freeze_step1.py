# Freeze current source/ordinary bytes by AST and stat;never import candidate HF.
import ast
from datetime import datetime,timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
A=Path(__file__).resolve().parent
B=Path('D:/hfst1_001')
R=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
BASELINE='19f7f38e002f72e58a4a50925f1fb3d47535b864'
def read(p):return json.loads(Path(p).read_bytes())
def pin(p):
 p=Path(p).resolve();raw=p.read_bytes();return dict(path=p.as_posix(),bytes=len(raw),sha256=sha256(raw).hexdigest())
def write(p,row):
 with p.open('x',encoding='utf-8',newline='\n') as stream:json.dump(row,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
assert not any((B/n).exists() for n in ('protocol.json','run_001','top_start.json','helper_start.json','root_qa.json','execution_evidence.zip'))
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R).decode().strip()==BASELINE
assert not subprocess.check_output(['git','status','--porcelain'],cwd=R).strip()
source=read(B/'source_binding.json');contract=read(B/'contract.json');history=read(B/'history.json')
production=sorted((R/'hf_repo/src/hf_eval').glob('*.py'))
assert len(production)==58
for row in source['production_source_files']:
 actual=pin(R/row['path']);assert all(actual[k]==row[k] for k in ('bytes','sha256'))
scripts=[B/n for n in ('science_step1.py','check_step1.py','view_step1.py','helper_step1.py','launch_step1.py','windows_owned_process_sup2.py')]
ordinary=[B/n for n in ('source_binding.json','contract.json','history.json','observer_binding.json','approved_card.md','authorization.json')]
for row in source['ordinary_sources']:
 actual=pin(row['path']);assert all(actual[k]==row[k] for k in ('bytes','sha256'));ordinary.append(Path(row['path']))
for n in ('WORKER_CHECK_IMPLEMENTATION.md','WORKER_CHECK_IMPLEMENTATION.json','VIEWER_IMPLEMENTATION.md','VIEWER_IMPLEMENTATION.json','WRAPPER_IMPLEMENTATION.md','WRAPPER_IMPLEMENTATION.json'):
 q=A/n;assert q.is_file();target=B/'reviews'/n;target.parent.mkdir(exist_ok=True)
 assert not target.exists();target.write_bytes(q.read_bytes());ordinary.append(target)
files=list(dict.fromkeys(production+scripts+ordinary))
assert all(p.suffix.lower() not in ('.npz','.zip','.png','.gif','.svg') for p in files)
for path in production+scripts:ast.parse(path.read_bytes(),filename=str(path))
assert contract['loads']['full_targets_half_N']==[.0002399800950672949,.0002561572865437846,.000260201584412907]
p=dict(stage='L-CTIPFSTEP1',schema_version='hf-formal-force-continuation-protocol-1',
 status='frozen_for_one_approved_execution_after_independent_static_eligibility',baseline=BASELINE,
 root_repository=R.as_posix(),runtime_base=B.as_posix(),production_src=(R/'hf_repo/src').as_posix(),
 python_executable='D:/Coding/Diversity TO/Compliant-TO-TMC/.venv-handoff/Scripts/python.exe',
 source_binding_file=(B/'source_binding.json').as_posix(),contract_file=(B/'contract.json').as_posix(),
 observer_binding_file=(B/'observer_binding.json').as_posix(),parent_result=source['ordinary_sources'][0]['path'],
 source_context=source,source_selected=source['selected_force_state'],history=history,
 source_force_task=history['immediate_force_parent']['force_task'],
 loads_half_N=contract['loads']['full_targets_half_N'],segment_loads_half_N=contract['loads']['requested_segment_half_N'],
 held_input_mean_mm=1.06,root_P0_half_N=contract['loads']['root_P0_half_N'],
 nmin_half_N=contract['loads']['minimum_force_increment_half_N'],
 controller_seconds=1800,science_worker_total_seconds=2100,science_process_seconds=2085,
 science_cleanup_and_receipt_reserve_seconds=15,ordinary_check_total_seconds=60,ordinary_check_process_seconds=45,
 display_and_root_QA_shared_seconds=600,viewer_process_seconds=510,root_QA_end_before_shared_display_seconds=585,
 helper_seconds=3000,helper_content_exit_before_seconds=2900,outer_seconds=3060,
 outer_owned_helper_job_deadline_seconds_from_top_start=2930,
 clocks=dict(outer='launch_step1 START before ordinary imports',helper='helper_step1 START before ordinary imports',
 display='helper display_begin before viewer spawn',helper_QA_end_before_seconds=2890,
 helper_final_bindings_before_seconds=2895,seal_entry_before_helper_seconds=2945,
 seal_members_before_helper_seconds=2980,archive_identity_before_helper_seconds=2990,all_receipts_before_helper_seconds=3000),
 memory_limit_bytes=64*1024**3,viewer_memory_limit_bytes=8*1024**3,
 thread_environment={n:'16' for n in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')},
 image_names=['01_actual_geometry.png','02_P_q_continuation.png','03_force_components_and_R.png',
  '04_tip_right_geometry_global_J_Hu.png','05_convergence_and_gates.png'],animation_name='actual_force_states.gif',
 root_png_inspection_maximum=5,maximum_accepted_states=5,
 accepted_count_scope='Derived from original Nmin float cutoff for this quarter step;no new controller maxdepth/truncation',
 unique_scientific_API_calls=1,old_NPZ_unique_paths_in_API=3,API_decoded_archives_on_completed_admission=2,
 API_decoded_fields_on_completed_admission=6,ordinary_checker_NPZ_reads=0,viewer_NPZ_reads=0,
 new_P2_reference=dict(status='not_available_no_P2_reference',q_error_mm=None,full_DOF_error_mm=None,R_error_N=None),
 sealing_cleanup_scope='Success:all four launched layersnormal/0+complete cleanup. Partial:first terminal error stops later phases;unstarted phasesnot_started,full helper-tree member/termination/handleproof and original time remaining required;never report unstarted layersaspassed.',
 bindings=[pin(path) for path in files],production=[pin(path) for path in production],
 new_HP=0,new_tests=0,production_modifications=0,external_retries=0,numerical_launched=False,
 created_utc=datetime.now(timezone.utc).isoformat())
write(B/'protocol.json',p);(A/'protocol.json').write_bytes((B/'protocol.json').read_bytes())
write(A/'CANDIDATE_FREEZE.json',dict(stage='L-CTIPFSTEP1',status='frozen_pending_protocol_ack_and_eligibility',
 baseline=BASELINE,protocol=pin(B/'protocol.json'),bindings=len(files),original_production_unchanged=58,
 AST_source_files=len(production+scripts),unique_command=[p['python_executable'],'-X','utf8','-B',str(B/'launch_step1.py')],
 scientific_payloads_not_read_hashed_decoded_or_copied=True,candidate_imports=0,tests_run=0,scientific_calls=0,numerical_launched=False))
print(json.dumps(dict(status='frozen',bindings=len(files),production=58,AST=len(production+scripts),protocol=pin(B/'protocol.json'))))
