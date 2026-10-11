"""Ordinary source/AST receipt only; do not import or execute future workers."""
import ast
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
BASE = '01b5078acaf76fdaabfbdf214da9db16056467bc'

def digest(path):
    return sha256(path.read_bytes()).hexdigest()

author_file = HERE / 'candidate_author_receipt.json'
author = json.loads(author_file.read_bytes())
assert author['base_commit'] == BASE and len(author['focused_test_nodeids']) == 5
for name, entry in author['candidate_files'].items():
    assert digest(HERE / 'candidate' / name) == entry['sha256']
sources = {}
for name in ('execute_resume.py', 'resume_focused_budget.py'):
    path = HERE / name
    tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    sources[name] = dict(sha256=digest(path), bytes=path.stat().st_size,
        AST='parsed_without_import_or_execution',
        functions=sum(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) for node in ast.walk(tree)))
notes = HERE / 'PREPARATION_RUNNER_NOTES.md'
baseline = {path.relative_to(ROOT).as_posix():digest(path)
    for path in sorted((ROOT / 'hf_repo/src/hf_eval').glob('*.py'))}
assert len(baseline) == 51
runtime = {name.removeprefix('hf_repo/'):dict(source_kind='formal_baseline',source=name,sha256=pin)
    for name,pin in baseline.items()}
for name,entry in author['candidate_files'].items():
    runtime[name.removeprefix('hf_repo/')] = dict(source_kind='reviewed_candidate_overlay',
        source='candidate/' + name,sha256=entry['sha256'])
for name in ('test_native_force.py','test_native_mean_mechanical.py','test_split_displacement.py','test_split_cycle.py'):
    relative = 'hf_repo/tests/' + name
    runtime['tests/' + name] = dict(source_kind='formal_baseline_fixture',source=relative,sha256=digest(ROOT / relative))
runtime['resume_focused_budget.py'] = dict(source_kind='new_focused_budget_plugin',
    source='resume_focused_budget.py',sha256=sources['resume_focused_budget.py']['sha256'])
assert len(runtime) == 60 and len([name for name in runtime if name.startswith('src/hf_eval/')]) == 52
scope = json.loads((HERE / 'scope_persistence_review.json').read_bytes())
value = dict(status='prepared_helper_and_focused_plugin_source_AST_only_not_imported_or_executed',
    card='M-RESUME1',source_baseline_commit=BASE,recorded_utc=datetime.now(timezone.utc).isoformat(),
    authorized=False,executed=False,formal_repository_mutation=False,
    sources=sources,notes_sha256=digest(notes),candidate_author_receipt_sha256=digest(author_file),
    focused_test_nodeids=author['focused_test_nodeids'],baseline_module_SHA256=baseline,runtime_source_plan=runtime,
    future_protocol_keys=['card','source_baseline_commit','bindings','parent_result','parent_protocol',
        'selected_state_index','targets_mm','options','settings','gates','phases.production',
        'focused_tests_seconds','view_seconds','sampled_RSS_bytes','candidate_directory','view_directory',
        'source_package.files','focused_test_nodeids','pure_view_bindings','viewer_source'],
    future_resources=dict(controller_seconds=1800,focused_tests_seconds=120,viewer_seconds=600,
        helper_seconds=2700,outer_seconds=2760,sampled_tree_RSS_bytes=8 * 1024**3,
        mode='Cooperative limits and sampled RSS; no OS hard limit, no force, estimate not a success guarantee'),
    future_production=dict(public_API_calls=1,selected_parent_accepted_index=13,original_target_indices=[13,14],
        targets_mm=[1.2,1.15],target_origin=0.0,initial_parameter=1.2,initial_K=None,
        options=dict(response_mode='mechanical',tangent_mode='chunk256',initial_guess='port_projection'),
        existing_input_NPZ_files=2,existing_input_fields=6,no_saved_matrix_force_tangent_decode=True,
        success_accepted_states_min=2,success_accepted_states_max=9,
        gates='Literal original alpha protocol gates; all other settings unchanged except explicit time',
        typed_non_success='Existing writer/summary persist normal controller partial before stop; no viewer',
        retry=0,force_termination=False),
    future_tests=dict(selected_nodeids=5,synthetic_or_algebra_controller_contracts=4,tiny_TMC_public_integration_cells=16,
        accounting='Separate subprocess; test F/T are not claimed zero or included in production call counts',
        first_failure_stop='pytest -x'),
    future_views=dict(source='functional_views/right_margin4_20261007/complete_001/saved_right_margin_views.py',
        source_modified=False,imports_from='formal hf_repo pure closure; isolated from candidate package',
        accepted_states='N=2..9 after successful production only',geometry_calls='N',nodal_calls='N',
        decoded_NPZ_files='1+2N new saved files',decoded_fields='27+18N',node_CSV_rows='703N',
        PNG_files=3,GIF_files=1,GIF_frames='N',independent_reference=False,mechanical_hooks_monitored=False),
    qualifications=dict(continuation_validated=False,new_HP=False,pressure=False,clamping=False,physical_stability=False,HF5=False,
        original_parent_status_remains='NOT_PASS; original unload not accepted'),
    source_scope_audit=dict(status=scope['status'],sha256=digest(HERE / 'scope_persistence_review.json')),
    author_self_check_limits='AST and ordinary source identity only; not independent peer review or numerical PASS',
    actual_actions=dict(candidate_import=0,HF_import=0,tests=0,NPZ_decode=0,force=0,tangent=0,solver=0,observer=0,HP=0,JIT=0,render=0,formal_repository_write=0))
output = HERE / 'runner_source_author_receipt.json'
output.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False) + '\n',encoding='utf-8')
print(json.dumps(dict(status=value['status'],receipt_sha256=digest(output),source_SHA256={name:item['sha256'] for name,item in sources.items()},runtime_files=len(runtime)),indent=2))
