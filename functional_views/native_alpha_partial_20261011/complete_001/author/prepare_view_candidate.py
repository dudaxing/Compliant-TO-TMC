"""Archive the reviewed saved-view candidate and ordinary preparation records.

No candidate import, NPZ decode, observation, rendering or scientific call.
"""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import ast
import json
import re
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
EXT = Path(__file__).resolve().parent
BASE = '9e2e37cce7f0441af042337d1c26c50ae660acc0'
REL = 'functional_views/native_alpha_partial_20261011/complete_001'
STAGE = ROOT/REL
OLD = 'lf_data_preparation/native_interface_001/regularization_sensitivity_001'
sha = lambda path: sha256(path.read_bytes()).hexdigest()
read = lambda path: json.loads(path.read_bytes())
git = lambda *args: subprocess.check_output(['git','-c','gc.auto=0',*args],cwd=ROOT)


def write(path, value):
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        stream.write(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def copy(source, target):
    assert not target.exists()
    target.write_bytes(source.read_bytes())


assert git('rev-parse','HEAD').decode().strip() == BASE
assert git('branch','--show-current').decode().strip() == 'main'
assert git('rev-parse','origin/main').decode().strip() == BASE
assert not git('status','--porcelain') and not STAGE.exists()
reviews = ('wrapper_static_review.json','physical_card_static_review.json')
for name in reviews:
    report = read(EXT/name)
    assert report['status'].startswith('pass'), (name,report['status'])
    assert report['authorized'] is False and report['executed'] is False
    checked_files = report.get('reviewed_external_SHA256',report.get('frozen_external_sources'))
    assert checked_files and all(sha(EXT/checked) == pin for checked,pin in checked_files.items())
audit = read(EXT/'view_input_scope_audit.json')
assert audit['status'] == 'pass_saved_view_input_scope_source_audit_no_execution'
source = read(EXT/'source_author_receipt.json')
for name,pin in source['authored_files_SHA256'].items():
    assert sha(EXT/name) == pin
ast.parse((EXT/'saved_alpha_partial_views.py').read_text(encoding='utf-8'))
old_bindings = dict(audit['pure_source_pins'])
for item in audit['raw_NPZ_plan']+audit['ordinary_input_plan']:
    old_bindings[item['path']] = item
for key in ('raw_view','helper'):
    item = audit['prior_cost_evidence'][key]
    old_bindings[item['path']] = item
assert len(old_bindings) == 58
assert all(sha(ROOT/name) == item['sha256'] for name,item in old_bindings.items())

author = STAGE/'author'
author.mkdir(parents=True)
for name in ('source_author_receipt.json','source_author_receipt_initial.json','SOURCE_SCOPE_NOTES.md',
        'view_input_scope_audit.json','VIEW_INPUT_SCOPE_AUDIT.md',
        'unload_cost_audit.json','write_unload_cost_audit.py',
        'wrapper_static_review.json','WRAPPER_STATIC_REVIEW.md',
        'physical_card_static_review.json','PHYSICAL_CARD_STATIC_REVIEW.md'):
    copy(EXT/name,author/name)
original_math = EXT/'UNLOAD_COST_AUDIT.md'
portable_math = original_math.read_text(encoding='utf-8').replace(ROOT.as_posix()+'/', '../../../../')
portable_math = re.sub(r'(\.py):(\d+)(?=\))',r'\1#L\2',portable_math)
portable_math += '\n\n归档说明：仅把本机源码链接改为仓库相对路径与行锚；未改变原数值/审计结论。外部原说明 SHA256：`'+sha(original_math)+'`。原普通 JSON 按字节保留。\n'
(author/'UNLOAD_COST_AUDIT.md').write_text(portable_math,encoding='utf-8',newline='\n')
copy(Path('D:/hf-native-workpiece-api-author-20261009/MALPHA1_execution_review_001/execution_publication_receipt.json'),author/'M_ALPHA1_execution_publication_receipt.json')
copy(EXT/'saved_alpha_partial_views.py',STAGE/'saved_alpha_partial_views.py')
copy(ROOT/OLD/'launch_alpha.py',STAGE/'launch_view.py')
copy(Path(__file__),author/'prepare_view_candidate.py')
for source_name,target_name in (('M-AVIEW1_CARD_draft.md','M-AVIEW1_CARD.md'),
        ('PREPARATION_RESULTS_draft.md','PREPARATION_RESULTS.md'),('README_draft.md','README.md')):
    copy(EXT/source_name,STAGE/target_name)

bindings = {name:item['sha256'] for name,item in old_bindings.items()}
for path in STAGE.rglob('*'):
    if path.is_file():
        bindings[path.relative_to(ROOT).as_posix()] = sha(path)
prefix = [0.,.25,.5,.65,.75,.8,.85,.9,.95,1.,1.05,1.1,1.15,1.2]
protocol = dict(schema_version='saved-alpha-partial-view-card-1.0',card='M-AVIEW1',
    preparation_baseline_commit=BASE,prepared=True,authorized=False,executed=False,
    viewer_source='functional_views/right_margin4_20261007/complete_001/saved_right_margin_views.py',
    candidate_directory=OLD+'/run_001/alpha_half',view_directory=REL+'/run_001/view',
    baseline_result='lf_data_preparation/native_interface_001/nested_cycle_001/run_001/fixed_square/result.json',
    baseline_summary='functional_views/native_nested_cycle_20261009/complete_001/run_001/view/fixed_square/summary.json',
    baseline_csv='functional_views/native_nested_cycle_20261009/complete_001/run_001/view/fixed_square/states.csv',
    targets_mm=prefix,sampled_RSS_bytes=8589934592,
    phases={'view':dict(helper_seconds=180,outer_seconds=240,
        argv=[REL+'/saved_alpha_partial_views.py','--repo','.','--protocol',REL+'/protocol.json'])},
    actual_decoder_plan=audit['exact_raw_loader_scope'],
    raw_NPZ_declarations=audit['raw_NPZ_plan'],
    common_original_target_identities=audit['compatibility']['common_original_loading_targets'],
    raw_gates=audit['raw_gates'],non_gates=audit['non_gates'],
    planned_observations=dict(geometry=14,nodal=14,node_CSV_data_rows=9842),
    planned_outputs=dict(PNG_files=6,GIF_files=1,GIF_frames=14,comparison_metrics=14,
        comparison_differences=196,snapshot_GIF_indices=[6,13]),
    original_status=dict(production='failed',failure='time_limit',path_completed=False,
        unload_endpoint_reached=False,task_target_executed=False,independent_HP_qualified=False),
    new_mechanical_calls=0,baseline_observer_calls=0,whole_HF5_complete=False,
    stop_contract='Once; first terminal error stops. No retry, repair rerun, extension, force or new mechanics.',
    bindings=dict(sorted(bindings.items())))
write(STAGE/'protocol.json',protocol)

front_history = []
body = (EXT/'CURRENT_BODY_draft.md').read_text(encoding='utf-8')
links = '\n\n[新显示卡](../'+REL+'/M-AVIEW1_CARD.md) · [准备结果](../'+REL+'/PREPARATION_RESULTS.md) · [原数值结果](../'+OLD+'/RESULTS.md)\n\n'
prefix_bytes = ('# 当前接续：M-AVIEW1 保存态显示已准备、未授权／未执行\n\n'+body+links+
    '<details>\n<summary>更新前完整原文（历史状态不代表当前）</summary>\n\n').encode('utf-8')
for name in ('docs/CURRENT_STATUS.md','docs/RESUME_DEVELOPMENT.md'):
    old = git('show',BASE+':'+name)
    assert (ROOT/name).read_bytes() == old
    current = prefix_bytes+old+b'\n\n</details>\n'
    assert current.count(old) == 1
    (ROOT/name).write_bytes(current)
    front_history.append(dict(path=name,old_bytes=len(old),old_sha256=sha256(old).hexdigest(),
        new_sha256=sha256(current).hexdigest(),history_start_byte=len(prefix_bytes),
        history_end_byte_exclusive=len(prefix_bytes)+len(old),old_body_preserved_exactly=True))
receipt = dict(status='ordinary_view_candidate_prepared_not_authorized_not_executed',
    created_utc=datetime.now(timezone.utc).isoformat(),card='M-AVIEW1',source_baseline_commit=BASE,
    prepared=True,authorized=False,executed=False,protocol_sha256=sha(STAGE/'protocol.json'),
    bindings_checked=len(bindings),old_bindings_checked=len(old_bindings),
    raw_viewer_unchanged=True,generic_launcher_copied_exactly=True,
    original_math_MD_sha256=sha(original_math),portable_math_MD_sha256=sha(author/'UNLOAD_COST_AUDIT.md'),
    archived_external_files={p.name:sha(p) for p in author.iterdir() if p.is_file()},
    documentation_files={name:sha(STAGE/name) for name in ('M-AVIEW1_CARD.md','PREPARATION_RESULTS.md','README.md')},
    front_history=front_history,actual_scientific_actions=dict(HF_imports=0,NPZ_decodes=0,
        observations=0,models=0,force_tangent=0,equilibrium=0,HP=0,new_renders=0),whole_HF5_complete=False)
write(author/'preparation_receipt.json',receipt)
print(json.dumps(dict(status=receipt['status'],binding_count=len(bindings),old_bindings=len(old_bindings),
    new_stage=REL,protocol_sha256=receipt['protocol_sha256']),ensure_ascii=False))
