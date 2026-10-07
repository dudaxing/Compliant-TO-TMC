"""Narrow saved JSON/raw documentation review; no HF, NumPy or rendering."""
import json
import math
import re
from hashlib import sha256
from pathlib import Path

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path('D:/hf-right-margin-author-20261007')
PROPOSALS = AUTHOR/'final_doc_proposals_001'
BASE = 'lf_data_preparation/native_workpiece_001/'
VIEW = 'functional_views/right_margin_20261007/complete_001'
CONTEXT = 'docs/evidence/workpiece_enlargement_20261007/right_margin_source_context'
PROGRESS = 'docs/evidence/workpiece_enlargement_20261007/right_margin_progress.json'
REPORT = 'docs/WORKPIECE_ENLARGEMENT_20261007.md'
PINS = {}
sha = lambda p:sha256(p.read_bytes()).hexdigest()

def read(p):
    PINS[str(p)] = sha(p)
    return json.loads(p.read_text(encoding='utf-8'))

def rootread(name):
    return read(ROOT/name)

summary = read(PROPOSALS/'final_summary.json')
assert summary['status'] == 'complete_mechanical_reference_views_project_incomplete'
assert len(summary['proposal_sha256']) == 6
for name,pin in summary['proposal_sha256'].items():
    assert sha(PROPOSALS/'proposals'/name) == pin
for name,pin in summary['input_json_and_figure_sha256'].items():
    assert sha(ROOT/name) == pin, name

def launch(control,phase,protocol_name=None):
    protocol_name = protocol_name or phase+'_protocol.json'
    p = rootread(control+'/'+protocol_name)
    l = rootread(control+'/'+phase+'_launch.json')
    assert l['status'] == 'pass' and l['exit_code'] == 0 and l['invocations'] == 1
    assert l['stop_reason'] is None and l['all_bindings_unchanged']
    assert l['protocol_sha256'] == sha(ROOT/control/protocol_name)
    assert l['bindings'] == p['bindings']
    assert 0 <= l['elapsed_seconds'] <= p['phases'][phase]['outer_seconds']
    assert 0 <= l['peak_sampled_tree_RSS_bytes'] <= p['sampled_RSS_bytes'] == 8*1024**3
    return p,l

tp,tl = launch(BASE+'right_margin_validation_001','tests','adapter_test_protocol.json')
tr = rootread(BASE+'right_margin_validation_001/run_001/test_receipt.json')
assert tr['status']=='pass' and tr['tests_collected']==tr['tests_passed']==5 and tr['constructor_invocations']==2
pp,pl = launch(BASE+'right_margin_preparation_001','prepare','preparation_protocol.json')
pr = rootread(BASE+'right_margin_preparation_001/run_001/preparation_receipt.json')
assert pr['status']=='pass' and pr['actual_counts']==summary['source_stage']['prep_actual_counts']
assert len(pr['model_comparison']['fields'])==27 and len(pr['model_comparison']['raw_equal_fields'])==10
assert len(pr['model_comparison']['physically_mapped_fields'])==17 and pr['final_resource_check_passed']
assert pp['phases']['prepare']['helper_seconds']==120 and pp['phases']['prepare']['outer_seconds']==150
assert all(pr[k]==0 for k in ('force_calls','tangent_calls','solver_calls','HP_calls','JIT_calls','LF_imports'))

vp,vl = launch(VIEW,'view','protocol.json')
phase = rootread(VIEW+'/view/phase_view.json')
view = rootread(VIEW+'/view/view.json')
assert phase['status']==view['status']=='pass' and phase['failure'] is view['failure'] is None
assert phase['original_view_sha256']==sha(ROOT/VIEW/'view/view.json')
assert phase['final_resource_check_passed'] and phase['final_resource_error'] is None
assert phase['elapsed_seconds']<=180 and phase['sampled_peak_helper_RSS_bytes']<=8*1024**3
assert vp['phases']['view']['helper_seconds']==180 and vp['phases']['view']['outer_seconds']==210
assert phase['new_geometry_nodal_F_T_model_solver_HP_calls_outside_raw_viewer']==view['new_F_T_model_solver_HP_calls']==0
assert all(view[k]==48 for k in ('geometry_started','geometry_completed','nodal_started','nodal_completed'))
assert sha(ROOT/VIEW/'saved_right_margin_views.py')=='761a9ffd1512233ce048be364c00a86882b69e2fb3e3fe81d7f79f74ad52b166'
assert sha(ROOT/VIEW/'launch_view.py')=='f3a96681afc474e42ae19875579d748237235dce90f21892b016b3b3af862477'

cases = {}
for label,stage in [('gamma1e6','enlarged_square_projection_001'),('right2col','right_margin_cycle_001')]:
    control=BASE+stage
    production_protocol,production_launch=launch(control,'production')
    reference_protocol,reference_launch=launch(control,'reference')
    execution=rootread(control+'/run_001/execution_receipt.json')
    result=rootread(control+'/run_001/result/result.json')
    reference=rootread(control+'/reference/summary.json')
    assert execution['status']=='pass' and execution['invocations']==1
    assert result['status']=='success' and result['accepted_states']==execution['accepted_states']==24
    assert execution['result_sha256']==reference['result_sha256']==sha(ROOT/control/'run_001/result/result.json')
    assert reference['status']=='pass' and reference['accepted_states']==len(reference['states'])==24
    assert reference['HP_calls_started']==reference['HP_calls_completed']==48
    assert result['states'][0]['d']==result['states'][-1]['d']==0
    assert all(result[k] for k in ['path_completed','loading_peak_reached','unload_endpoint_reached','task_target_executed'])
    assert all(reference[k]==0 for k in ('candidate_force_calls','tangent_calls','solver_calls','model_constructions'))
    assert view['input_source_bindings'][control+'/run_001/result/result.json']==sha(ROOT/control/'run_001/result/result.json')
    assert view['input_source_bindings'][control+'/reference/summary.json']==sha(ROOT/control/'reference/summary.json')
    stored=rootread(VIEW+'/view/'+label+'/summary.json')
    assert sha(ROOT/VIEW/'view'/label/'summary.json')==view['outputs'][label+'/summary.json']==phase['outputs'][label+'/summary.json']
    rows=stored['rows']; assert len(rows)==24
    for i,(row,state,refrow) in enumerate(zip(rows,result['states'],reference['states'])):
        assert row['index']==refrow['index']==i and refrow['status']=='pass'
        assert row['state_sha256']==state['state_sha256']==refrow['state_sha256']
        assert row['leg']==state['leg']==refrow['leg'] and row['d_mm']==state['d']==refrow['target_mm']
        assert row['original_target_index']==state['original_target_index']==refrow['original_target_index']
        assert row['R_input_N']==state['R_input'] and row['q_out_mm']==state['q_out']
        assert row['cached_two_sided_normal_magnitude_sum_N']==state['workpiece']['two_sided_normal_magnitude_sum_N']
        assert row['cached_two_sided_normal_magnitude_sum_N']==2*abs(row['total_body_Fy_N'])
        assert row['solid_min_J']>0 and row['medium_min_J']>0
        assert not row['strict_overlap'] and not row['roundoff_ambiguous']
        for component in ('total','material','regularization'):
            assert [row[component+'_body_Fx_N'],row[component+'_body_Fy_N']]==state['workpiece']['force_on_lower_body_N'][component]
        nodal_name=label+f'/{i:03d}/nodal.json'
        derived_name=label+f'/{i:03d}/derived.json'
        assert sha(ROOT/VIEW/'view'/nodal_name)==view['outputs'][nodal_name]
        assert sha(ROOT/VIEW/'view'/derived_name)==view['outputs'][derived_name]
        nodal=rootread(VIEW+'/view/'+nodal_name)
        derived=rootread(VIEW+'/view/'+derived_name)
        assert derived['row']==row
        assert nodal['summary']['force_on_lower_body_N']==state['workpiece']['force_on_lower_body_N']
        assert nodal['summary']['holding_reaction_on_model_N']==[-row['total_body_Fx_N'],-row['total_body_Fy_N']]
    case=summary['cases'][label]
    assert case['result_sha256']==sha(ROOT/control/'run_001/result/result.json')
    assert case['call_counts']==result['call_counts']
    assert case['accepted_states']==24 and case['HP_completed']==48 and case['checks_completed']==reference['checks_completed']
    assert case['loading_peak']==rows[13] and case['return_state']==rows[23]
    assert case['tip_node']==(2510 if label=='gamma1e6' else 2570)
    assert case['loading_peak']['d_mm']==1.2 and case['return_state']['d_mm']==0
    for d in (.5,.75,.8,.85,1.):
        selected=[r for r in rows if r['leg']=='loading' and r['d_mm']==d and result['states'][r['index']]['is_original_target']]
        assert len(selected)==1
    if label=='right2col':
        assert result['call_counts']==dict(force_calls=348,force_calls_completed=331,tangent_calls=177,tangent_calls_completed=177,solver_invocations=1,JIT_calls=0,HP_calls=0)
        assert reference['checks_completed']==476733
        assert production_protocol['phases']['production']['helper_seconds']==4500 and production_protocol['phases']['production']['outer_seconds']==4560
        assert reference_protocol['phases']['reference']['helper_seconds']==1500 and reference_protocol['phases']['reference']['outer_seconds']==1560
        assert execution['seconds_limit']==4500 and execution['elapsed_seconds']<=4500
        assert reference['time_limit_seconds']==1500 and reference['elapsed_seconds']<=1500
        lifecycle=rootread(control+'/reference/lifecycle.json')
    cases[label]=dict(peak=rows[13],return_state=rows[23],rows=rows,call_counts=result['call_counts'],checks=reference['checks_completed'],
        production_helper_seconds=execution['elapsed_seconds'],production_outer_seconds=production_launch['elapsed_seconds'],
        reference_summary_seconds=reference['elapsed_seconds'],reference_outer_seconds=reference_launch['elapsed_seconds'])

control=BASE+'right_margin_cycle_001'
freeze=rootread(control+'/run_001/source_freeze.json')
old_freeze=rootread(BASE+'enlarged_square_projection_001/run_001/source_freeze.json')
assert len(freeze['sources'])==27 and len({Path(n).name for n in freeze['sources']})==27
new_core={p:h for p,h in freeze['sources'].items() if p.startswith('hf_repo/src/hf_eval/')}
old_core={p:h for p,h in old_freeze['sources'].items() if p.startswith('hf_repo/src/hf_eval/')}
assert len(new_core)==25 and len(old_core)==24
assert {p:h for p,h in new_core.items() if p!='hf_repo/src/hf_eval/analysis_domain.py'}==old_core
for name,pin in freeze['sources'].items():
    assert sha(ROOT/name)==sha(ROOT/control/'run_001/sources'/Path(name).name)==pin
contract=rootread(control+'/reference_contract.json')
references=contract['reference_sources']
assert len(references)==len({Path(n).name for n in references})==37
for name,pin in references.items():
    assert sha(ROOT/name)==sha(ROOT/control/'reference/reference_sources'/Path(name).name)==pin
assert contract['accounting_source_transition']['proof_origin_stage']==BASE+'enlarged_square_projection_001/run_001'
source_identity=dict(production_raw_sources=27,current_HF_core=25,old_core_raw_retained=24,new_adapter=1,
    production_source_copies_byte_exact=True,reference_raw_sources=37,reference_source_copies_byte_exact=True,
    old_accounting_source_proof_origin=contract['accounting_source_transition']['proof_origin_stage'],
    old_accounting_scope='Original source-validation proof only, not actual newtrial counts or HP-state qualification.',
    production_source_freeze_sha256=sha(ROOT/control/'run_001/source_freeze.json'),reference_contract_sha256=sha(ROOT/control/'reference_contract.json'))

correction=rootread(VIEW+'/launch_path_correction.json')
assert correction['status']=='prelaunch_file_not_found_no_observation_started'
assert correction['attempted_protocol']==VIEW+'/view_protocol.json' and correction['actual_frozen_protocol']==VIEW+'/protocol.json'
assert correction['exit_code']==1 and not correction['existing_view_launch_receipt'] and not correction['existing_view_output_directory']
assert all(correction[k]==0 for k in ('new_observation_processes','new_geometry_calls','new_nodal_calls','new_F_T_model_solver_HP_calls','protocol_or_source_changes'))
assert vl['invocations']==1 and vl['argv'][1]=='-B'

historical={}
for name,info in summary['historical_suffixes'].items():
    original=(ROOT/CONTEXT/name).read_bytes(); proposal=(PROPOSALS/'proposals'/name).read_bytes()
    assert sha256(original).hexdigest()==info['sha256'] and len(original)==info['bytes']
    assert proposal[info['new_suffix_offset_bytes']:]==original
    banner=PROPOSALS/'interim_banners'/(name+'.prefix.md')
    assert sha(banner)==info['interim_banner_sha256']
    prefix=proposal[:info['new_suffix_offset_bytes']].decode('utf-8')
    assert '不含优化器' in prefix and '尚未实现' in prefix and '2|Fy|不是完整装配净力' in prefix
    for target in re.findall(r'\]\(([^)]+)\)',prefix):
        if '://' in target: continue
        repo_target=((ROOT/name).parent/target).resolve()
        relative=repo_target.relative_to(ROOT)
        assert (PROPOSALS/'proposals'/relative).exists() or repo_target.exists(), str(repo_target)
    historical[name]=info
original_report=(ROOT/REPORT).read_bytes(); proposed_report=(PROPOSALS/'proposals'/REPORT).read_bytes()
assert sha256(original_report).hexdigest()==summary['main_report_before_append_sha256']
assert proposed_report.startswith(original_report)
assert original_report.startswith((ROOT/CONTEXT/REPORT).read_bytes())
appended=proposed_report[len(original_report):].decode('utf-8')
assert '此前source-phase段是当时来源准备快照' in appended
assert 'PORT方向切线作用' in appended and '保存Green应变为binary64观察' in appended
old_progress=rootread(PROGRESS)
new_progress=read(PROPOSALS/'proposals'/PROGRESS)
assert new_progress['prior_production_snapshot']==old_progress['production']
for name,value in old_progress.items():
    if name not in {'status','production','qualification','next'}:
        assert new_progress[name]==value, name
assert new_progress['production']['status']=='pass' and new_progress['production']['accepted_states']==24
assert new_progress['production']['actual_call_counts']==cases['right2col']['call_counts']
assert new_progress['final_reference_view_observations']['cases']==summary['cases']

old,new=cases['gamma1e6']['peak'],cases['right2col']['peak']
pct=lambda key:100*(new[key]/old[key]-1)
physical=dict(old_peak=old,new_peak=new,
    total_Fy_percent_change=pct('total_body_Fy_N'),material_Fy_percent_change=pct('material_body_Fy_N'),
    regularization_Fy_ratio=new['regularization_body_Fy_N']/old['regularization_body_Fy_N'],
    old_regularization_Fy_fraction=old['regularization_body_Fy_N']/old['total_body_Fy_N'],
    new_regularization_Fy_fraction=new['regularization_body_Fy_N']/new['total_body_Fy_N'],
    medium_max_abs_Hu_percent_change=pct('medium_max_abs_Hu_per_mm'),
    Fx_absolute_percent_change=100*(abs(new['total_body_Fx_N'])/abs(old['total_body_Fx_N'])-1),
    gap_old_um=1000*old['tip_to_bottom_mm'],gap_new_um=1000*new['tip_to_bottom_mm'],
    gap_delta_um=1000*(new['tip_to_bottom_mm']-old['tip_to_bottom_mm']),
    original_loading_Fy_changes=[dict(d_mm=d,percent_change=100*(next(r for r in cases['right2col']['rows'] if r['leg']=='loading' and r['d_mm']==d)['total_body_Fy_N']/next(r for r in cases['gamma1e6']['rows'] if r['leg']=='loading' and r['d_mm']==d)['total_body_Fy_N']-1)) for d in (.5,.75,.8,.85,1.)])
report=dict(status='pass_saved_only',blocking_findings=[],proposal_sha256=summary['proposal_sha256'],
    actual_closed_facts=dict(new_states=24,new_F_started=348,new_F_completed=331,new_T_started=177,new_T_completed=177,new_HP_started=48,new_HP_completed=48,new_reference_checks=476733,
        production_helper_seconds=cases['right2col']['production_helper_seconds'],production_outer_seconds=cases['right2col']['production_outer_seconds'],
        reference_lifecycle_helper_seconds=lifecycle['elapsed_seconds'],reference_outer_seconds=cases['right2col']['reference_outer_seconds'],
        view_raw_seconds=view['elapsed_seconds'],view_whole_helper_seconds=phase['elapsed_seconds'],view_outer_seconds=vl['elapsed_seconds'],geometry_observations=48,nodal_observations=48,
        budget_windows_seconds=dict(prepare=[120,150],production=[4500,4560],reference=[1500,1560],view=[180,210]),all_sampled_RSS_limits_bytes=8*1024**3),
    physical_saved_statistics=physical,
    interpretation=['Lower-body weak ON-body Fy is opposite holding reaction;2absFy is mirrored magnitude sum, whole mirrored net=(2Fx,0), not pressure/free-body clamping qualification.',
        'Gap is unsigned finite node-to-body-segment distance; peakgap remains positive. J guards include original9Simpson/Lobatto points includingcorners.',
        '4.27x refers to regularization Fy contribution, not maxabsHu field; Green values are saved-F binary64 observations, not independentHP strain.',
        'Peak totalFy changes little because materialFy decrease and regularizationFy increase partly offset; early loadingFy varies materially.',
        'Only0mm vs2mm right margins atsameh1 were compared; no mesh/domain convergence or pressure/contact/friction/free-body/HF5 completion implied.'],
    historical_whole_suffixes=historical, main_report_current_prefix_byte_exact=True,source_phase_snapshot_explicitly_historical=True,progress_prior_snapshot_and_closed_fields_preserved=True,
    current_source_identity_and_retained_roles=source_identity,
    operator_error=dict(record_file=VIEW+'/launch_path_correction.json',record_sha256=sha(ROOT/VIEW/'launch_path_correction.json'),
        status='Human command filename error before protocol/receipt/resource clock/subprocess;0child/0observation, then canonical protocol1worker1phase. Not zero operator errors and not2scientific invocations.'),
    next_choice='Prefer one additional sameh1 rightmargin4mm comparison withE/gamma/alpha/Lr/body/ports/path unchanged before grid refinement or new body shapes. First prepare/mapping/source freeze, then budgeted fresh production/reference/view only if actual preceding phase passes. Compare2vs4 material/regularizationFy,Fx and earlyloading aswellaspeak/gap; this measures boundary sensitivity, not automatic convergence. Mesh sensitivity can follow at a selected nonzero margin.',
    readback_pins=PINS, reviewer_activity=dict(HF_imports=0,NPZ_array_loads=0,constructors=0,F_T_solver_HP=0,geometry_nodal_render=0,formal_writes=0))
output=AUTHOR/'final_documentation_review.json'
output.write_text(json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
(AUTHOR/'final_documentation_review.md').write_text('六份实际文档 proposal 与闭合保存记录窄审通过。原四 front 完整 abf62b04 后缀、主报告来源阶段前缀及旧进度字段保持；24态/48HP/476733检查、48几何/48节点观察及各预算符合冻结记录。查看器有一次协议文件名操作错误，协议读取前退出、0子进程/0观察；canonical protocol仅一次worker和phase。峰值总Fy约+0.1883%，正则化Fy约4.27倍，但max|Hu|场仅约+0.0576%，不能混称；Fx幅值约减8.26%。建议先固定h1做2→4mm余量的单因素实际对照，再择非零余量开展网格敏感性。仍不授予压力/接触判据/自由体/HP应变或整个HF项目完成资格。全部为保存JSON/raw统计，没有新的科学计算或观察。\n',encoding='utf-8')
print(json.dumps(dict(status=report['status'],report=str(output),sha256=sha(output),physical=physical),ensure_ascii=False))
