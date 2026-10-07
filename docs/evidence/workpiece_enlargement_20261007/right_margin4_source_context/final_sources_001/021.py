"""Source/closed-2mm-JSON peer only; does not import or execute candidate."""
import ast
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
OUT=Path('D:/hf-margin4-author-20261007/closure_candidate')
digest=lambda p:sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
note=read(OUT/'author_note.json')
source=OUT/'close_margin4_docs.py'
assert digest(source)=='7e2e32543dd367fcadb84f8666fb32fb58cb4803aa1780adaa4ce7184ab2b1c9'
for name,pin in note['candidate_sources'].items():assert digest(OUT/name)==pin,name
tree=ast.parse(source.read_text(encoding='utf-8-sig'))
imports={n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)}|{a.name for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names}
assert imports=={'argparse','hashlib','json','pathlib'}
closed_pins={}
for relative,pin in note['schema_sources'].items():
    assert digest(ROOT/relative)==pin,relative
    closed_pins[relative]=pin

control='lf_data_preparation/native_workpiece_001/right_margin_cycle_001'
viewstage='functional_views/right_margin_20261007/complete_001'
result=read(ROOT/control/'run_001/result/result.json')
ref=read(ROOT/control/'reference/summary.json')
execution=read(ROOT/control/'run_001/execution_receipt.json')
contract=read(ROOT/control/'reference_contract.json')
prod=read(ROOT/control/'production_protocol.json')
pl=read(ROOT/control/'production_launch.json')
rp=read(ROOT/control/'reference_protocol.json')
rl=read(ROOT/control/'reference_launch.json')
view=read(ROOT/viewstage/'view/view.json')
phase=read(ROOT/viewstage/'view/phase_view.json')
rows=read(ROOT/viewstage/'view/right2col/summary.json')['rows']
n=result['accepted_states']
assert result['status']=='success' and execution['status']=='pass' and n==24==len(result['states'])
assert execution['result_sha256']==digest(ROOT/control/'run_001/result/result.json')
assert all(k in execution for k in ['sources_unchanged','inputs_unchanged','sampled_peak_RSS_bytes','elapsed_seconds','accepted_states','HP_calls','JIT_calls','LF_imports'])
assert all(result[k] for k in ['path_completed','loading_peak_reached','unload_endpoint_reached','task_target_executed'])
assert ref['status']=='pass' and n==len(ref['states'])==ref['accepted_states'] and ref['HP_calls_started']==ref['HP_calls_completed']==2*n
assert contract['actual_accepted_states']==rp['actual_accepted_states']==n
assert contract['expected_new_HP80_120_calls']==rp['expected_new_HP80_120_calls']==2*n
assert all(k in ref for k in ['result_sha256','independent_reference_contract_sha256','full_element_and_DOF_coverage',
    'HP_matrix_columns_exhaustively_checked','contact_qualified','clamp_qualified','pressure_qualified','elapsed_seconds',
    'sampled_peak_RSS_bytes','candidate_force_calls','tangent_calls','solver_calls','model_constructions','source_bindings',
    'input_bindings','checks_completed','qualification'])
for index,(state,check,row) in enumerate(zip(result['states'],ref['states'],rows)):
    assert index==check['index']==row['index'] and check['HP_calls']==2 and check['status']=='pass'
    assert state['state_sha256']==check['state_sha256']==row['state_sha256']
    assert row['d_mm']==state['d'] and row['leg']==state['leg'] and row['original_target_index']==state['original_target_index']
    assert 'is_original_target' in state
    assert all(k in row for k in ['R_input_N','q_out_mm','total_body_Fx_N','total_body_Fy_N',
        'material_body_Fx_N','material_body_Fy_N','regularization_body_Fx_N','regularization_body_Fy_N',
        'cached_two_sided_normal_magnitude_sum_N','tip_to_bottom_mm','medium_min_J','medium_max_abs_Hu_per_mm',
        'solid_min_J','solid_Green_principal_min','solid_Green_principal_max'])
assert isinstance(view['cases'],list)
case=next(c for c in view['cases'] if c['label']=='right2col')
assert case['saved_accepted_states']==case['observed_states']==len(rows)==n
assert rows[case['peak_index']]['d_mm']==max(r['d_mm'] for r in rows)
assert case['last_index']==n-1
assert all(k in case for k in ['reference_available','production_path_completed','unload_endpoint_reached','task','model_sha256','tip_node'])
assert all(k in phase for k in ['final_resource_check_passed','original_view_sha256',
    'new_geometry_nodal_F_T_model_solver_HP_calls_outside_raw_viewer','elapsed_seconds','sampled_peak_helper_RSS_bytes','outputs'])
for protocol,launch,phase_name,helper,outer in [(prod,pl,'production',4500,4560),(rp,rl,'reference',1500,1560)]:
    assert protocol['phases'][phase_name]['helper_seconds']==helper and protocol['phases'][phase_name]['outer_seconds']==outer
    assert protocol['sampled_RSS_bytes']==8*1024**3
    assert all(k in launch for k in ['status','exit_code','invocations','stop_reason','all_bindings_unchanged',
        'protocol_sha256','bindings','elapsed_seconds','peak_sampled_tree_RSS_bytes'])
source_text=source.read_text(encoding='utf-8-sig')
assert 'sha(raw(VIEW' in source_text and "view['outputs'][name]==phase['outputs'][name]" in source_text
assert source_text.index('data=collect(root)')<source_text.index("if args.action=='propose':")
assert source_text.count("front.encode('utf-8')+before[name]")==1
assert "REPORT:before[REPORT]+append.encode('utf-8')" in source_text
assert "'001.json':before[PROGRESS]" in source_text
assert "assert manifest['input_sha256']==data['input_sha256']" in source_text

report={
 'schema_version':'margin4-closing-documents-source-peer-review-1.0',
 'status':'pass_static_only','generated_utc':datetime.now(timezone.utc).isoformat(),
 'candidate_sources':{**note['candidate_sources'],'author_note.json':digest(OUT/'author_note.json')},
 'closed_2mm_schema_sources':closed_pins,
 'actual_closed_2mm_schema_checks':{'accepted_states':n,'fresh_HP_calls':2*n,'all_state_identities':True,
   'view_cases_is_list':True,'scalar_rows_match_states':True,'peak_index_is_maximum_input_stroke':True,
   'resource_and_receipt_key_compatibility':True},
 'read_scope':'Candidate full216-line source/README/author note/checks/diff and selected closed2mm JSON schemas only; no candidate import or execution.',
 'findings':[
  'collect requires both actual single-pass production launches/receipts, complete result path, same-result allN fresh2N references and actual complete saved-view phase before proposal writes.',
  'Resource windows remain4500/4560 production,1500/1560 reference,180/210 views and8GiB. Helper/posthash checks and current protocol/source/input identities are read, not changed.',
  'View cases list is handled by label; perstate indices/SHA/leg/displacement/original_target_index bind saved rows to actual states. Original-target comparisons exclude bisections while full views retain all states.',
  'Maximum input stroke and maximum loading Fy are distinct. Signed lower-half body forces/material-Hu contributions,2absFy magnitude sum, finite tip distance, Hu and binary64 Green scopes are preserved without pressure/free-body/HP strain/mesh-convergence claims.',
  'Five current fronts plus report/matrix/progress produce8 external payloads. Docs links are relative to their location; source proposer uses explicit absolute repo/output roots, not current working directory.',
  'Install repeats closed gates/input signatures and all preimage/payload identities. Fronts preserve raw suffixes/report raw prefix; previous progress and proposal/review/helper/author files are separately archived. Existing short running/prelaunch context is retained.',
  'Actual future4mm production/reference/view states or results are not prefilled. Current top-level reference becomespass only after fresh reference/view closure; historical snapshots remain distinguishable.',
 ],
 'blocking_findings':[],
 'current_stage_context':'Parent reports4mm production24PASS, reference stillrunning and viewunexecuted. This review did not read live4mm scientific output and grants no final documentation or new numeric PASS.',
 'required_next':'After final author wording/context addition, re-pin its final source; execute proposer only after actual new reference and complete-view closure, then independently saved-only review actual proposals before install.',
 'activity':{'HF_or_candidate_imports':0,'candidate_execution':0,'NPZ_or_array_reads':0,'model_constructors':0,
  'F_T_solver_HP':0,'geometry_nodal_plot':0,'tests_or_cards':0,'formal_writes':0}
}
target=OUT/'closure_static_review.json'
target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':report['status'],'report':str(target),'sha256':digest(target)},ensure_ascii=False))
