"""Closed saved JSON/CSV and document bytes only; no scientific modules or renders."""
from pathlib import Path
from hashlib import sha256
import csv
import json
import math
import re
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
OUT=Path('D:/hf-workpiece-enlarge-author-20261007')
EVIDENCE=ROOT/'docs/evidence/workpiece_enlargement_20261007'
BASELINE='16ee4ebb67161e2c8bc9a27d8e44285308778171'
digest=lambda p:sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
receipt_file=EVIDENCE/'gamma_documentation_install.json'
progress_file=EVIDENCE/'gamma_half_progress.json'
receipt=read(receipt_file)
progress=read(progress_file)
assert digest(receipt_file)=='6556307969a1ecb522b9c8d5d47615abacf1f2550689e1569cc1a0576a3a59c9'
assert digest(progress_file)=='cfd60a7fe23f8ffa25ec7e7c74759b4f4ce7da91f1b800090d87368c3ea13b37'
assert receipt['status']=='pass' and receipt['baseline_commit']==progress['baseline_commit']==BASELINE
documents={row['path']:row['sha256'] for row in receipt['documents']}
assert len(documents)==5 and all(digest(ROOT/name)==pin for name,pin in documents.items())
assert documents['docs/WORKPIECE_ENLARGEMENT_20261007.md']=='01646c89a8256f67a226938516cfebf2436a1bdfbc563d020ed2af61c1064a8a'
fronts={}
suffixes={}
for name,row in receipt['four_historical_suffixes'].items():
    blob=(ROOT/name).read_bytes()
    old=subprocess.check_output(['git','show',BASELINE+':'+name],cwd=ROOT)
    offset=row['current_suffix_offset_bytes']
    assert blob[offset:]==old and sha256(old).hexdigest()==row['old_entire_file_sha256']
    fronts[name]=blob[:offset].decode('utf-8')
    suffixes[name]=dict(offset_bytes=offset,old_entire_file_sha256=sha256(old).hexdigest(),raw_exact=True)
    assert '465255' in fronts[name] and '48' in fronts[name] and '0.118620312' in fronts[name]
    assert '5.535555' in fronts[name] and '42–43%' in fronts[name] and '0.3254%' in fronts[name]
    assert '16ee4ebb' in fronts[name] and '历史' in fronts[name] and '关闭' in fronts[name]
    assert '零' in fronts[name] and '压力' in fronts[name] and 'gamma=1e-6' in fronts[name]
main_path=ROOT/'docs/WORKPIECE_ENLARGEMENT_20261007.md'
main_text=main_path.read_text(encoding='utf-8')
old_main=subprocess.check_output(['git','show',BASELINE+':docs/WORKPIECE_ENLARGEMENT_20261007.md'],cwd=ROOT)
assert old_main in main_path.read_bytes()
tail=main_text.split('## 同一工件的 gamma 单因素对照（已完成）',1)[1]
for text in ['465255','5.535554895','0.165197','41.92%/43.33%/43.37%','0.3254085%',
    '0.01272622618→0.01299279069','x63–80','整个项目尚未完成','零右侧介质余量',
    '压力与自由工件稳定夹持不在资格内','全列切线','465255','368/338F','180/180T']:
    assert text in tail,text
assert '它不软化夹持器实体E、不改变Hu系数kr' in tail
assert '没有生成padding模型、卡或求解' in tail
for name in receipt['old_raw_receipts_and_source_context_unchanged']:
    assert (ROOT/name).read_bytes()==subprocess.check_output(['git','show',BASELINE+':'+name],cwd=ROOT)

phase_locations={
    'preparation':('lf_data_preparation/native_workpiece_001/gamma_half_preparation_001','preparation_protocol.json'),
    'production':('lf_data_preparation/native_workpiece_001/gamma_half_cycle_001','production_protocol.json'),
    'reference':('lf_data_preparation/native_workpiece_001/gamma_half_cycle_001','reference_protocol.json'),
    'view':('functional_views/workpiece_gamma_20261007/complete_001','protocol.json'),
    'cached_local_view':('functional_views/workpiece_gamma_20261007/fit_001','protocol.json')}
phase_data={}
bindings_checked={}
for name,(stage,protocol_name) in phase_locations.items():
    item=progress[name]
    assert item['status']=='pass' and item['invocations']==1 and item['all_bindings_unchanged']
    for declaration in [item['receipt'],item['launch']]:
        path=ROOT/declaration['path']
        assert path.stat().st_size==declaration['bytes'] and digest(path)==declaration['sha256']
    actual=read(ROOT/item['receipt']['path'])
    launch=read(ROOT/item['launch']['path'])
    protocol_path=ROOT/stage/protocol_name
    protocol=read(protocol_path)
    assert launch['status']=='pass' and launch['invocations']==1 and launch['exit_code']==0
    assert launch['stop_reason'] is None and launch['all_bindings_unchanged']
    assert launch['protocol_sha256']==digest(protocol_path) and launch['bindings']==protocol['bindings']
    assert actual['status']=='pass'
    assert item['helper_elapsed_seconds']==actual['elapsed_seconds']
    assert item['outer_elapsed_seconds']==launch['elapsed_seconds']
    assert 0<=item['helper_elapsed_seconds']<=item['helper_seconds_limit']
    assert 0<=item['outer_elapsed_seconds']<=item['outer_seconds_limit']
    assert item['sampled_RSS_limit_bytes']==protocol['sampled_RSS_bytes']==8*1024**3
    assert item['tree_sampled_peak_RSS_bytes']==launch['peak_sampled_tree_RSS_bytes']<=8*1024**3
    helper_peak=next(actual[k] for k in ['peak_sampled_helper_RSS_bytes','sampled_peak_RSS_bytes','sampled_peak_helper_RSS_bytes'] if k in actual)
    assert item['helper_sampled_peak_RSS_bytes']==helper_peak<=8*1024**3
    for path,pin in protocol['bindings'].items():
        if path not in bindings_checked:
            assert digest(ROOT/path)==pin,path
            bindings_checked[path]=pin
        else:
            assert bindings_checked[path]==pin,path
    phase_data[name]=dict(receipt=actual,launch=launch,protocol_sha256=digest(protocol_path),binding_count=len(protocol['bindings']))
prep=phase_data['preparation']['receipt']
production=phase_data['production']['receipt']
reference=phase_data['reference']['receipt']
view=phase_data['view']['receipt']
fit=phase_data['cached_local_view']['receipt']
assert prep['model_comparison']==progress['model_comparison']
assert prep['model_constructions']==prep['model_writes']==1 and prep['force_calls']==prep['tangent_calls']==prep['solver_calls']==prep['HP_calls']==0
assert progress['model_identity']['model_sha256']==prep['model_sha256']==production['model_sha256']
assert progress['model_identity']['task_sha256']==prep['task_sha256']==production['task_sha256']
result_file=ROOT/'lf_data_preparation/native_workpiece_001/gamma_half_cycle_001/run_001/result/result.json'
result=read(result_file)
assert digest(result_file)==progress['model_identity']['result_sha256']==production['result_sha256']==reference['result_sha256']
assert result['status']=='success' and result['accepted_states']==production['accepted_states']==reference['accepted_states']==24
assert result['path_completed'] and result['unload_endpoint_reached']
assert all(result[k] is False for k in ['equilibrium_qualified','independent_HP_qualified','HF_qualified'])
assert reference['HP_calls_started']==reference['HP_calls_completed']==48 and reference['checks_completed']==465255
assert all(row['status']=='pass' and row['index']==index and row['state_sha256']==result['states'][index]['state_sha256']
    and row['leg']==result['states'][index]['leg'] and row['target_mm']==result['states'][index]['d']
    for index,row in enumerate(reference['states']))
assert all(reference[k] is False for k in ['contact_qualified','clamp_qualified','pressure_qualified'])
assert reference['counter_accounting']['counts']==result['call_counts']==production['call_counts']
assert result['call_counts']['force_calls']==368 and result['call_counts']['force_calls_completed']==338
assert result['call_counts']['tangent_calls']==result['call_counts']['tangent_calls_completed']==180
assert len(result['path_diagnostics']['failed_attempts'])==0
assert all(row['is_original_target'] for row in result['states'])
assert [row['d'] for row in result['states']]==result['targets_mm']
model=read(ROOT/'lf_data_preparation/native_workpiece_001/gamma_half_cycle_001/run_001/result/model/model.json')
old_model=read(ROOT/'lf_data_preparation/native_workpiece_001/enlarged_square_projection_001/run_001/result/model/model.json')
assert {k for k in model['arrays']['fields'] if model['arrays']['fields'][k]!=old_model['arrays']['fields'][k]}=={'gamma','lam','mu'}
assert {k for k in model['task'] if model['task'][k]!=old_model['task'][k]}=={'third_medium','task_id','purpose','parameter_origin'}
assert model['material']==dict(old_model['material'],third_medium_gamma=5e-7)
assert model['task']['regularization']==old_model['task']['regularization']==dict(alpha=1e-6,length_mm=80.)

view_root=ROOT/'functional_views/workpiece_gamma_20261007/complete_001/view'
original_view=read(view_root/'view.json')
assert original_view['status']=='pass' and view['status']=='pass' and view['final_resource_check_passed']
assert all(original_view[k]==48 for k in ['geometry_started','geometry_completed','nodal_started','nodal_completed'])
assert original_view['new_F_T_model_solver_HP_calls']==view['cached_geometry_nodal_F_T_model_solver_HP_calls']==0
cached=read(view_root/'gamma_comparison/cached_comparison.json')
assert cached['matched_states']==24 and all(cached['saved_states'][label]==24 for label in ['gamma1e6','gamma5em7'])
assert all(not value for value in cached['extra_bisection_indices'].values())
assert all(not value for value in cached['unmatched_original_target_indices'].values())
with (view_root/'gamma_comparison/matched_states.csv').open(encoding='utf-8',newline='') as handle:
    matched=list(csv.DictReader(handle))
assert len(matched)==24
saved={}
for label in ['gamma1e6','gamma5em7']:
    saved[label]=[read(view_root/label/f'{index:03d}'/'derived.json')['row'] for index in range(24)]
    assert progress['peak_rows'][label]==saved[label][13]
    assert progress['return_rows'][label]==saved[label][23]
    assert all(not row['raw_overlap'] and not row['strict_overlap'] and not row['roundoff_ambiguous'] for row in saved[label])
    assert all(read(view_root/label/f'{index:03d}'/'geometry.json')['geometry_valid'] for index in range(24))
    for row in saved[label]:
        assert math.isclose(row['total_body_Fy_N'],row['material_body_Fy_N']+row['regularization_body_Fy_N'],rel_tol=1e-13,abs_tol=1e-30)
        assert row['cached_two_sided_normal_magnitude_sum_N']==2*abs(row['total_body_Fy_N'])
old,new=progress['peak_rows']['gamma1e6'],progress['peak_rows']['gamma5em7']
differences=dict(peak_Fy_change_percent=100*(new['total_body_Fy_N']/old['total_body_Fy_N']-1),
    peak_R_change_percent=100*(new['R_input_N']/old['R_input_N']-1),
    peak_q_out_change_mm=new['q_out_mm']-old['q_out_mm'],
    peak_tip_bottom_gap_change_um=1000*(new['tip_to_bottom_mm']-old['tip_to_bottom_mm']),
    peak_medium_min_J_ratio=new['medium_min_J']/old['medium_min_J'])
assert all(math.isclose(value,progress['peak_differences'][key],rel_tol=1e-13,abs_tol=1e-15) for key,value in differences.items())
for early in progress['early_loading_Fy_differences']:
    pair=[next(row for row in saved[label] if row['leg']=='loading' and row['d_mm']==early['d_mm']) for label in ['gamma1e6','gamma5em7']]
    assert early['baseline_Fy_N']==pair[0]['total_body_Fy_N'] and early['gamma_half_Fy_N']==pair[1]['total_body_Fy_N']
    assert math.isclose(early['relative_change_percent'],100*(pair[1]['total_body_Fy_N']/pair[0]['total_body_Fy_N']-1),rel_tol=1e-13)
for row in matched:
    index=int(row['original_target_index'])
    assert float(row['d_mm'])==model['task']['path']['targets_mm'][index]
    for label in ['gamma1e6','gamma5em7']:
        assert row[label+'_state_sha256']==saved[label][int(row[label+'_index'])]['state_sha256']
assert fit['new_F_T_model_solver_HP_geometry_observation_calls']==0 and fit['pressure_contact_clamping_qualified'] is False
fit_root=ROOT/'functional_views/workpiece_gamma_20261007/fit_001/view'
for label in ['gamma1e6','gamma5em7']:
    detail=read(fit_root/(label+'_fit.json'))
    assert detail==progress['cached_local_view']['cases'][label]
    assert detail['source_reference_window']==dict(y_mm=30.,x_mm=[63.,80.])
    assert detail['state_sha256']==progress['peak_rows'][label]['state_sha256']
    assert detail['contact_or_pressure_qualified'] is False
assert progress['cached_local_view']['new_F_T_model_solver_HP_geometry_nodal_calls']==0
manifest_file=EVIDENCE/'gamma_half_source_context/raw_manifest.json'
manifest=read(manifest_file)
assert digest(manifest_file)==receipt['raw_context_manifest']['sha256']
assert len(manifest['files'])==21
for row in manifest['files']:
    path=manifest_file.parent/row['path']
    assert digest(path)==row['sha256'] and path.stat().st_size==row['bytes']
links=[]
for name,text in {**fronts,'docs/WORKPIECE_ENLARGEMENT_20261007.md':tail,
    'docs/evidence/workpiece_enlargement_20261007/gamma_half_source_context/INDEX.md':(manifest_file.parent/'INDEX.md').read_text(encoding='utf-8')}.items():
    for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',text):
        if '://' in target or target.startswith('#'):
            continue
        target=target.split('#',1)[0]
        path=((ROOT/name).parent/target).resolve()
        assert path.exists(),(name,target)
        path.relative_to(ROOT)
        links.append(dict(source=name,target=path.relative_to(ROOT).as_posix()))
for name in progress['figures'].values():
    assert (ROOT/name).is_file()
assert len(receipt['document_only_operator_read_errors'])==2
assert receipt['document_only_operator_read_errors'][0]['actual_name']=='prepare_launch.json'
assert receipt['document_only_operator_read_errors'][1]['actual_name']=='source_context/raw_sha_manifest.json'
assert receipt['HF_core_diff_empty'] and receipt['zero_new_mechanics_HP_geometry_nodal_calls']
assert all(digest(ROOT/name)==pin for name,pin in documents.items())
report=dict(status='pass_closed_data_and_final_documentation_only',baseline_commit=BASELINE,
    documents=documents,progress_sha256=digest(progress_file),documentation_receipt_sha256=digest(receipt_file),
    raw_context_manifest_sha256=digest(manifest_file),raw_context_files=21,
    historical_suffixes=suffixes,old_entire_report_bytes_retained=True,old_receipts_manifest_raw_exact_to_git=True,
    closed_phases={name:dict(status='pass',invocations=1,helper_seconds=progress[name]['helper_elapsed_seconds'],
        outer_seconds=progress[name]['outer_elapsed_seconds'],protocol_sha256=data['protocol_sha256'],
        binding_count=data['binding_count']) for name,data in phase_data.items()},
    unique_binding_SHA_checks=len(bindings_checked),
    scientific_scope=dict(new_actual_original_states=24,new_fresh_HP80_120_calls=48,reference_checks=465255,
        result_sha256=digest(result_file),force_started_completed=[368,338],tangent_started_completed=[180,180],
        production_original_qualification_flags_false=True,reference_contact_clamp_pressure_false=True,
        gamma_delta_only3_fields_other24_metadata_raw_identities_exact=True,
        new_Fy_N=new['total_body_Fy_N'],two_sided_magnitude_N=new['cached_two_sided_normal_magnitude_sum_N'],
        new_gap_um=1000*new['tip_to_bottom_mm'],peak_differences=differences,
        early_loading_Fy_differences=progress['early_loading_Fy_differences'],
        local_Green_principal_max={label:progress['cached_local_view']['cases'][label]['adjacent_solid_Green_principal_max'] for label in ['gamma1e6','gamma5em7']},
        local_scope='Reference y30,x63–80 adjacent solid; different from whole-solid and body full bottom x62–80.'),
    final_documentation_findings=dict(physical_units_and_force_roles_correct=True,
        gamma_not_solid_softening_or_force_gap_halving=True,early_sensitivity_not_hidden_by_peak=True,
        new_bound_resources_disclosed_and_old_closed_cards_preserved=True,
        project_and_HF5_still_incomplete_LF_N4_research_retained=True,
        next_padding_task_explicitly_unexecuted_and_not_old_model_qualified=True,
        current_relative_links_resolve_within_repo=True,current_links_checked=len(links),
        source_context_pending_snapshots_marked_as_history=True,
        documentation_read_errors_separate_from_scientific_phase_invocation=True,
        raw_diff_context_whitespace_preserved_as_original_bytes=True),
    links=links,
    limitations='No candidate or scientific module was imported, no model/FE/solver/HP/geometry/nodal/view was rerun. Only closed JSON/CSV, saved hashes, source identities and document bytes were read; scalar comparisons were reconstructed. Five PNG/GIF visual quality observations and clipping limitations are root-reported, not a new independent render or manual image inspection. No all-array equality or new physical qualification is added by this review.',
    activity=dict(candidate_imports=0,scientific_reruns=0,array_loads=0,model=0,F=0,T=0,solver=0,HP=0,
        geometry=0,nodal=0,render=0,formal_writes=0,commit=0,push=0))
path=OUT/'gamma_final_documentation_static_review.json'
path.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
print(json.dumps(dict(status=report['status'],review_sha256=digest(path),documents=documents,
    bindings_checked=len(bindings_checked),phases=report['closed_phases']),ensure_ascii=False))
