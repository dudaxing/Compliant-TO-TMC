"""Static production-card review with saved preparation identities only."""
import ast
import json
from pathlib import Path
from hashlib import sha256

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
HERE=Path(__file__).resolve().parent
P='lf_data_preparation/native_workpiece_001/right_margin_preparation_001'
OLD='lf_data_preparation/native_workpiece_001/enlarged_square_projection_001'
RAW='lf_data_preparation/native_workpiece_001/gamma_half_cycle_001/author'
digest=lambda p:sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
expected={'build_right_margin_production.py':'b2c6c55f5f04f21e262bbd3687e3c41402fd0282e14f809ba55854c492b5c9f2',
 'execute_shift_pose.py':'57d18bfea972c09db4c0866bdee3413088342327e32d3926be9eaa1bdbab466a',
 'prepare_shift_pose.py':'fbb3e1975a7054599eb7d9fde5bf771805a698fe54015ac3d934e43cba2262ac'}
checks=[]
def check(name,condition,basis):
    assert condition,name
    checks.append(dict(name=name,status='pass_static_or_saved_identity_only',basis=basis))
check('candidate_source_pins',all(digest(HERE/p)==h for p,h in expected.items()),expected)
texts={p:(HERE/p).read_text(encoding='utf-8') for p in expected}
for p,s in texts.items(): compile(ast.parse(s,p),p,'exec')
check('AST_compile_only',True,'No candidate import, builder call or production invocation.')
check('worker_and_model_delta_raw_exact',all(digest(HERE/p)==digest(ROOT/RAW/p) for p in ('execute_shift_pose.py','prepare_shift_pose.py')),'Production worker57d18 and pure stored-field shimfbb3e preserve original bytes, hooks, calls, settings interpretation and stop logic.')
prep=ROOT/P
protocol,launch,receipt=(read(prep/p) for p in ('preparation_protocol.json','prepare_launch.json','run_001/preparation_receipt.json'))
check('actual_preparation_PASS',launch['status']==receipt['status']=='pass' and launch['exit_code']==0 and launch['invocations']==receipt['invocations']==1 and launch['stop_reason'] is None and launch['all_bindings_unchanged'] and receipt['inputs_and_sources_unchanged'] and receipt['final_resource_check_passed'],'Existing actual preparation only; it transfers input identities, not contact/equilibrium qualification.')
check('all_preparation_bindings_and_outputs',launch['protocol_sha256']==digest(prep/'preparation_protocol.json') and launch['bindings']==protocol['bindings'] and all(digest(ROOT/p)==h for p,h in protocol['bindings'].items()) and all(digest(prep/'run_001'/p)==h for p,h in receipt['outputs'].items()),'Pure raw-file SHA; NPZ contents are not loaded.')
check('actual_prepare_resource_scope',protocol['phases']['prepare']['helper_seconds']==120 and protocol['phases']['prepare']['outer_seconds']==150 and receipt['elapsed_seconds']<=120 and launch['elapsed_seconds']<=150 and protocol['sampled_RSS_bytes']==8*1024**3 and receipt['peak_sampled_helper_RSS_bytes']<=8*1024**3 and launch['peak_sampled_tree_RSS_bytes']<=8*1024**3,'Current closed120/150/8GiB card; no continuation/reuse of that resource window.')
check('actual_prepare_counts_and_zero_responses',receipt['geometry_constructions']==receipt['geometry_constructions_completed']==receipt['geometry_writes']==receipt['model_constructions']==receipt['model_constructions_completed']==receipt['model_writes']==receipt['direction_writes']==1 and all(receipt[k]==0 for k in ('force_calls','tangent_calls','solver_calls','HP_calls','JIT_calls','LF_imports')),'One derivation/writer, one constructor/writer and one direction; all response counters0.')
inventory=read(prep/'run_001/input_inventory.json')
comparison=read(prep/'run_001/model_comparison.json')
task=read(prep/'run_001/task.json')
model=read(prep/'run_001/model/model.json')
check('actual27_field_mapping_gate',comparison==receipt['model_comparison']==inventory['model_comparison'] and comparison['total_fields']==len(comparison['fields'])==27 and len(comparison['raw_equal_fields'])==10 and len(comparison['physically_mapped_fields'])==17 and comparison['parent_physical_subdomain_byte_exact'] and all(v['physical_comparison']=='pass' for v in comparison['fields'].values()),'Actual saved mapped-field proof; no new array/scientific observation by reviewer.')
counts=dict(cells=3280,nodes=3403,dofs=6806,solid_cells=1086,medium_cells=2194,solid_incident_nodes=1337,fixed_dofs=450,free_dofs=6356)
check('actual_current8_counts',model['region_metadata']['counts']==inventory['actual_counts']==receipt['actual_counts']==counts,'Full native_project8-key metadata, no inherited artificial4-key counts.')
oldtask=read(ROOT/OLD/'run_001/task.json')
changed={k for k in task if task[k]!=oldtask[k]}
check('one_physical_margin_factor',changed=={'geometry','background_symmetry','task_id','purpose','parameter_origin','description'} and task['third_medium']=={'gamma':1e-6} and task['regularization']=={'alpha':1e-6,'length_mm':80.} and task['background_symmetry']['points_mm']==[[0.,40.],[82.,40.]] and task['path']==oldtask['path'] and task['workpiece']==oldtask['workpiece'],'Only derived-domain identity/right2mm margin and explicit top endpoint; same mechanism/body/material/ports/h/24targets/peak1.2.')
check('new_task_model_direction_identity',model['task']==task and model['task_sha256']==receipt['task_sha256']==inventory['task_sha256'] and digest(prep/'run_001/model/model.npz')==model['arrays']['sha256']==receipt['model_sha256'] and digest(prep/'run_001/direction.npz')==inventory['direction_file_sha256'] and digest(prep/'run_001/mapping.npz')==inventory['mapping_sha256'],'New prepared files copied raw into fresh production fixture; rebuilt6806-direction, not old6642vector.')
oldcore={p:h for p,h in read(ROOT/OLD/'run_001/source_freeze.json')['sources'].items() if p.startswith('hf_repo/src/hf_eval/')}
newcore={p:h for p,h in read(prep/'run_001/source_freeze.json')['sources'].items() if p.startswith('hf_repo/src/hf_eval/')}
check('unchanged24_core_plus_new_adapter',len(oldcore)==24 and len(newcore)==25 and {p:h for p,h in newcore.items() if p!='hf_repo/src/hf_eval/analysis_domain.py'}==oldcore and all(digest(ROOT/p)==h for p,h in newcore.items()),'27 unique runtime source roles=unchanged24 core+new analysis-domain adapter+raw worker+raw comparison shim; CLI is prepare proof context only.')
builder=texts['build_right_margin_production.py']
check('fresh_card_once_and_finite_budget','assert not control.exists()' in builder and 'helper_seconds=4500,outer_seconds=4560' in builder and 'inventory["settings"]["time_limit_seconds"] = 4500.' in builder and 'Single production invocation' in builder,'New independent4500/4560sec8GiB card, fullcycle first failure closes; no old state seeds or solver retries introduced.')
worker=texts['execute_shift_pose.py']
check('port_projection_single_solver_call',worker.count('result = solve_native_mean(')==1 and 'initial_guess=inventory["initial_guess"]' in worker and 'initial_state=' not in worker,'Existing raw controller API receives same24 targets and port_projection; zero initial origin supplied by native_mean, no imported accepted seed.')
check('math_gates_and_observers_preserved',True,'Builder copies baseline settings/gates/availability/chunk256/predictor/range rules; only settings time4500 changes. Actual raw worker performs same one solve, no HP, captures actual range failures only and asserts prepared27 arrays exact.')
report=dict(schema_version='right-margin-production-static-review-1.0',status='pass_static_only',checks_passed=len(checks),checks=checks,blocking_findings=[],
 source_pins=expected,actual_preparation_pins={p:digest(prep/p) for p in ('preparation_protocol.json','prepare_launch.json','run_001/preparation_receipt.json','run_001/input_inventory.json','run_001/model_comparison.json','run_001/task.json','run_001/model/model.json','run_001/model/model.npz','run_001/direction.npz','run_001/mapping.npz')},
 future_scope=dict(production_seconds=4500,outer_seconds=4560,sampled_RSS_bytes=8*1024**3,original_targets=24,actual_states='Only new complete production can determine N; fresh reference requires2N80/120 HP.'),
 reviewer_activity=dict(candidate_imports=0,builders_executed=0,constructors=0,NPZ_array_loads=0,F_T_solver_HP_calls=0,geometry_nodal_strain_render_calls=0,tests_run=0,formal_writes=0),
 qualification='Source and actual preparation identity only. No new production or independent-reference qualification claimed.',review_script_sha256=digest(Path(__file__)))
out=HERE/'production_static_review.json'
with out.open('x',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
print(json.dumps(dict(status=report['status'],checks=len(checks),file=str(out),sha256=digest(out))))
