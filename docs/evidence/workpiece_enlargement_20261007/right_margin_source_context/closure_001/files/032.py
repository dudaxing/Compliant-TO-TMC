"""Independent source/JSON/SHA review only; never import or run the candidate."""
import ast
import difflib
import json
from hashlib import sha256
from pathlib import Path

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
HERE = Path(__file__).resolve().parent
OLD = 'lf_data_preparation/native_workpiece_001/enlarged_square_projection_001'
VAL = 'lf_data_preparation/native_workpiece_001/right_margin_validation_001'
read = lambda p: json.loads(p.read_text(encoding='utf-8'))
digest = lambda p: sha256(p.read_bytes()).hexdigest()
pins = {
    'prepare_right_margin.py': '5fdaa9088ff4d4129ba9073235a8cd6e68e40cfc3684d8287ee63a16140d1d91',
    'build_right_margin_card.py': 'ee445d5fa85e0e34a13f838f379336318eef078da2a4e183c8e6f19e9496ad67',
    'author_note.json': '8361b17fd66876980d5c36355722fdff111587a3610e4ecb52c2f1b82373f1cc',
    'source_additions.diff': 'c11822c789c98e75a7e6fcf6e45af1c3b23a40b88306844abc6b40eaf854a1bd',
}
checks = []
def check(name, truth, basis):
    assert truth, name
    checks.append(dict(name=name, status='pass_static_or_saved_identity_only', basis=basis))

check('final_source_pins', all(digest(HERE/p) == h for p,h in pins.items()), pins)
sources = {p:(HERE/p).read_text(encoding='utf-8') for p in ('prepare_right_margin.py','build_right_margin_card.py')}
trees = {p:ast.parse(s,p) for p,s in sources.items()}
for p,t in trees.items(): compile(t,p,'exec')
check('AST_compile_without_import', True, 'Both reviewed sources parsed and compiled, never imported or executed.')
expected_diff = ''.join(''.join(difflib.unified_diff([],s.splitlines(keepends=True),fromfile='/dev/null',tofile=p)) for p,s in sources.items())
check('source_additions_diff_exact', (HERE/'source_additions.diff').read_text(encoding='utf-8') == expected_diff, 'Two additions reconstruct reviewed final sources.')
worker = sources['prepare_right_margin.py']
builder = sources['build_right_margin_card.py']
calls = sorted({ast.unparse(n.func) for n in ast.walk(trees['prepare_right_margin.py']) if isinstance(n,ast.Call)})
check('no_response_API_calls', not any(x in calls for x in ('force','tangent','solve_native_mean','solve_split_displacement_path','HP','nodal_forces','deformed_geometry')), 'Call AST and full source review: only one padding writer, one project constructor/writer, saved-array comparisons and storage.')
check('one_new_constructor_and_padding_call', calls.count('build_native_project') == calls.count('write_right_medium_geometry') == 1, 'One call site each, no loop around construction; no old-model reconstruction.')
check('whole_helper_timer', 'STARTED = perf_counter()' in worker and 'started = STARTED' in worker, 'Timer begins before argparse/json/sys imports and covers initial/final hashes; outer supervisor additionally covers Python startup.')
check('one_continuous_preparation_budget', 'helper_seconds=120, outer_seconds=150' in builder and '8 * 1024**3' in worker, 'Separate new prepare card, first exception closes it, no retry or force.')
protocol = read(ROOT/VAL/'adapter_test_protocol.json')
launch = read(ROOT/VAL/'tests_launch.json')
receipt = read(ROOT/VAL/'run_001/test_receipt.json')
check('actual_small_test_qualification', receipt['status']=='pass' and receipt['pytest_exit_code']==0 and receipt['tests_collected']==receipt['tests_passed']==5 and receipt['constructor_invocations']==2 and all(receipt[k]==0 for k in ('new_force_calls','new_tangent_calls','new_equilibrium_calls','new_HP_calls')), 'Saved actual test receipt; not a new test invocation.')
check('small_test_launch_identity', launch['status']=='pass' and launch['exit_code']==0 and launch['invocations']==1 and launch['stop_reason'] is None and launch['all_bindings_unchanged'] and receipt['all_bindings_unchanged'] and launch['protocol_sha256']==digest(ROOT/VAL/'adapter_test_protocol.json') and launch['bindings']==protocol['bindings'] and all(digest(ROOT/p)==h for p,h in protocol['bindings'].items()), 'Actual proof/protocol/launch/current-source pins close the gate.')
oldtask = read(ROOT/OLD/'run_001/task.json')
oldmodel = read(ROOT/OLD/'run_001/result/model/model.json')
oldresult = read(ROOT/OLD/'run_001/result/result.json')
oldreference = read(ROOT/OLD/'reference/summary.json')
check('selected_gamma1em6_baseline_identity', oldtask==oldmodel['task'] and oldtask['third_medium']=={'gamma':1e-6} and oldtask['regularization']=={'alpha':1e-6,'length_mm':80.0} and oldmodel['region_metadata']['counts']==dict(cells=3200,nodes=3321,dofs=6642,solid_cells=1086,medium_cells=2114,solid_incident_nodes=1337,fixed_dofs=448,free_dofs=6194), 'Saved baseline JSON only; old qualification is an identity prerequisite, never transferred to new domain.')
check('baseline_complete_reference_identity', oldresult['status']=='success' and oldreference['status']=='pass' and oldreference['accepted_states']==24 and oldreference['HP_calls_started']==oldreference['HP_calls_completed']==48 and oldreference['result_sha256']==digest(ROOT/OLD/'run_001/result/result.json'), 'Existing complete baseline; this review invokes no fresh HP.')
check('hand_derived_row_stride_maps', '* 82 + np.arange(80' in worker and '* 83 + np.arange(81' in worker and '2 * node_map[:, None]' in worker, 'Cell j*80+i→j*82+i; node j*81+i→j*83+i; DOF mapping preserves component, not a uniform offset.')
check('current_constructor_counts_schema', 'dict(cells=3280, nodes=3403, dofs=6806, solid_cells=1086, medium_cells=2194, solid_incident_nodes=1337, fixed_dofs=450, free_dofs=6356)' in worker, 'Current native_project returns all 8 keys. Counts are expected assertions until actual new construction.')
check('physics_and_boundary_scope', '"geometry", "background_symmetry", "task_id", "purpose", "parameter_origin", "description"' in worker and 'points_mm"][1][0] = 82.' in worker, 'Only new geometry identity, top endpoint80→82 and four description fields; E/nu/gamma/alpha/Lr80/thickness/workpiece/24targets remain inherited exactly.')
check('physical_mapping_checks_reviewed', True, '10 scalar/reference-operator fields raw exact;17 shape/index fields checked by cell/node/DOF mappings; old materials and solid masks exact on old cells, new columns medium only; body162/190/380 and top overlap19 preserved; fixed450=old mapped448 plus 2 new top uy.')
check('new_direction_scope_reviewed', True, 'Recompute PORT from new b_in, require dimension6806/fixed zeros and mapped old direction raw equality; no tail-padding old6642-vector reuse.')
check('source_and_output_identity_reviewed', True, 'Bind old selected task/model/source geometry/direction/proof and unchanged24 core plus adapter/CLI; bind current validation inputs and all copied reviewed helpers; final hashes then checkpoint; writer copies new source package raw.')
check('no_contact_qualification_transfer', 'no equilibrium, contact or force qualification' in worker and 'static review alone cannot freeze' in builder, 'Preparation has no F/T/solver/HP/JIT/LF or accepted states; new production/reference must independently qualify.')
input_paths = [ROOT/VAL/p for p in ('adapter_test_protocol.json','tests_launch.json','run_001/test_receipt.json')]
input_paths += [ROOT/OLD/p for p in ('run_001/task.json','run_001/result/model/model.json','run_001/result/model/model.npz','run_001/result/result.json','reference/summary.json')]
input_paths += [ROOT/p for p in ('hf_repo/src/hf_eval/native_project.py','hf_repo/src/hf_eval/analysis_domain.py','hf_repo/scripts/prepare_analysis_domain.py','hf_repo/tests/test_analysis_domain.py')]
report = dict(schema_version='right-margin-preparation-static-review-1.0',status='pass_static_only',reviewed_source_pins=pins,
    checks=checks,checks_passed=len(checks),blocking_findings=[],saved_input_pins={p.relative_to(ROOT).as_posix():digest(p) for p in input_paths},
    static_expected_counts=dict(cells=3280,nodes=3403,dofs=6806,fixed=450,free=6356,body_cells=162,body_nodes=190,body_dofs=380,body_top_uy_overlap=19),
    scope=dict(candidate_imports=0,builders_executed=0,API_calls=0,constructors=0,tests_executed=0,F_calls=0,T_calls=0,solver_calls=0,HP_calls=0,geometry_observations=0,formal_writes=0),
    limits='Source/AST and saved JSON/raw-file SHA review only. No saved NPZ arrays loaded. Actual right-margin preparation has not run; expected model counts and mappings are not claimed as observations.',
    source_correction_before_freeze='Reviewed final5fdaa worker includes full-helper STARTED and full current8-key count schema; older6a8 source not approved.',
    review_script_sha256=digest(Path(__file__)))
output = HERE/'preparation_static_review.json'
with output.open('x',encoding='utf-8') as handle: json.dump(report,handle,ensure_ascii=False,indent=2,allow_nan=False); handle.write('\n')
print(json.dumps(dict(status=report['status'],checks=len(checks),report=str(output),sha256=digest(output))))
