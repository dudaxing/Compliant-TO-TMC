"""Independent closed-result review: JSON and file SHA only, no HF/NPZ imports."""
import json
from collections import Counter
from hashlib import sha256
from pathlib import Path

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
OUT=Path(__file__).resolve().parent
NEW='lf_data_preparation/native_workpiece_001/right_margin_cycle_001'
OLD='lf_data_preparation/native_workpiece_001/enlarged_square_projection_001'
PREP='lf_data_preparation/native_workpiece_001/right_margin_preparation_001'
VIEW='functional_views/right_margin_20261007/complete_001'
pins={}
def digest(p):
    p=Path(p)
    value=sha256(p.read_bytes()).hexdigest()
    if p.is_relative_to(ROOT): pins[p.relative_to(ROOT).as_posix()]=value
    return value
def read(name):
    p=ROOT/name
    digest(p)
    return json.loads(p.read_text(encoding='utf-8'))
def bind(name,pin):
    assert digest(ROOT/name)==pin,name
checks=[]
def check(name,truth,basis):
    assert truth,name
    checks.append(dict(name=name,status='pass_saved_only',basis=basis))
result=read(NEW+'/run_001/result/result.json')
receipt=read(NEW+'/run_001/execution_receipt.json')
reference=read(NEW+'/reference/summary.json')
lifecycle=read(NEW+'/reference/lifecycle.json')
inventory=read(NEW+'/run_001/input_inventory.json')
freeze=read(NEW+'/run_001/source_freeze.json')
oldresult=read(OLD+'/run_001/result/result.json')
oldreference=read(OLD+'/reference/summary.json')
check('complete24originaltargets',result['status']=='success' and receipt['status']==reference['status']=='pass' and result['accepted_states']==receipt['accepted_states']==reference['accepted_states']==24 and result['targets_mm']==oldresult['targets_mm'] and len(result['targets_mm'])==24 and all(s['is_original_target'] and s['bisection_depth']==0 and s['original_target_index']==i and s['d']==result['targets_mm'][i] for i,s in enumerate(result['states'])),'Same24 exact originaltargets, peak1.2 and returned0; all acceptedstates, no bisection prefixes.')
check('fullcycle_flags',all(result[k] is True for k in ('production_converged','target_reached','task_target_executed','path_completed','loading_peak_reached','unload_endpoint_reached','lift_origin_zero','lift_shape_zero')) and result['failure'] is None and not result['path_diagnostics']['failed_attempts'] and result['path_diagnostics']['maximum_bisection_depth']==0,'Full production closure, no failedpath attempt; recovered rejected line-search trials are separate.')
check('newstate_model_result_identity',receipt['result_sha256']==reference['result_sha256']==digest(ROOT/NEW/'run_001/result/result.json') and receipt['model_sha256']=='c880381a1906d6d0a53f54cd951a26bfdf2e5175658260213528e16e35b51c34' and result['states'][13]['state_sha256']=='6ae284e297811d465ba791b9a2fe90289cf958d1ba8c6eb7eec8ad5d7463e4fc','Actual newdomain2 model and peak state, not borrowed old identifiers.')

resources={}
for stage,phase,pfile,lfile in ((NEW,'production','production_protocol.json','production_launch.json'),(NEW,'reference','reference_protocol.json','reference_launch.json'),(VIEW,'view','protocol.json','view_launch.json')):
    protocol,launch=read(stage+'/'+pfile),read(stage+'/'+lfile)
    budget=protocol['phases'][phase]
    check(phase+'_launch_and_bindings',launch['status']=='pass' and launch['exit_code']==0 and launch['invocations']==1 and launch['stop_reason'] is None and launch['all_bindings_unchanged'] and launch['protocol_sha256']==digest(ROOT/stage/pfile) and launch['bindings']==protocol['bindings'],'Exact closed protocol/launch and same bindingmap.')
    for p,h in protocol['bindings'].items():bind(p,h)
    check(phase+'_bounded_resources',launch['elapsed_seconds']<=budget['outer_seconds'] and launch['outer_seconds']==budget['outer_seconds'] and launch['peak_sampled_tree_RSS_bytes']<=8*1024**3 and launch['sampled_RSS_limit_bytes']==protocol['sampled_RSS_bytes']==8*1024**3,'Actual one invocation within its own finite resourcewindow; no priorclosed budget inherited.')
    resources[phase]=dict(helper_budget_seconds=budget['helper_seconds'],outer_budget_seconds=budget['outer_seconds'],outer_elapsed_seconds=launch['elapsed_seconds'],tree_peak_RSS_bytes=launch['peak_sampled_tree_RSS_bytes'],binding_count=len(protocol['bindings']),protocol_sha256=digest(ROOT/stage/pfile))
check('production_final_receipt',receipt['elapsed_seconds']<=4500 and receipt['sampled_peak_RSS_bytes']<=8*1024**3 and receipt['sources_unchanged'] and receipt['inputs_unchanged'] and receipt['force_hook_restored'] and receipt['tangent_hook_restored'] and receipt['HP_calls']==receipt['JIT_calls']==receipt['LF_imports']==0 and receipt['solver_calls']==1 and receipt['save_force_calls']==receipt['save_tangent_calls']==0,'Original rawworker closes one solve, observers restored, zero savingreevaluations/HP/JIT/LF.')
resources['production'].update(helper_elapsed_seconds=receipt['elapsed_seconds'],helper_peak_RSS_bytes=receipt['sampled_peak_RSS_bytes'])

# Reconstruct the force chronology directly from saved Newton blocks/trials,
# independently of the accounting source or its reconstruction entry point.
history,trials=result['path_diagnostics']['newton_history'],result['path_diagnostics']['trials']
blocks=[]
for h in history:
    if h['newton_check']==1:blocks.append([])
    blocks[-1].append(h)
check('Newton_blocks_match24states',len(blocks)==24 and len(history)==177 and all(len(b)==s['newton_checks'] and [h['newton_check'] for h in b]==list(range(1,len(b)+1)) and all(h['d']==s['d'] for h in b) and b[-1]['state_sha256']==s['state_sha256'] for b,s in zip(blocks,result['states'])),'177 actual basechecks split at each check1; final cached accepted state matches corresponding terminalbase.')
events=[];cursor=0;ordinal=0;baseordinal=0;groups=[];categories=Counter();rejected=[]
for b,s in zip(blocks,result['states']):
    for h in b:
        ordinal+=1;baseordinal+=1
        events.append(dict(force_call=ordinal,kind='Newton_base',completed=True,tangent_call=baseordinal,state_sha256=h['state_sha256']))
        group=[]
        while cursor<len(trials) and trials[cursor]['target_displacement']==h['d'] and trials[cursor]['newton_check']==h['newton_check']:
            t=trials[cursor];ordinal+=1
            reason=t.get('reason');complete=reason not in ('invalid_J','unsupported_arithmetic_range')
            category='accepted' if t['accepted'] else reason
            categories[category]+=1
            event=dict(force_call=ordinal,kind='line_search_trial',completed=complete,trial_index=cursor,reason=reason)
            events.append(event);group.append(t)
            if not complete:rejected.append(dict(event,original_target_index=s['original_target_index'],leg=s['leg'],newton_check=h['newton_check'],factor=t['factor']))
            assert complete==('phi' in t and 'minimum_J' in t)
            cursor+=1
        if h is b[-1]:
            assert not group
            assert s['assembler_force_call']==ordinal and s['assembler_tangent_call']==baseordinal
        else:
            assert group and group[-1]['accepted'] is True and all(t['accepted'] is False for t in group[:-1])
            assert group[0]['factor']==1. and all(y['factor']==x['factor']*.5 for x,y in zip(group,group[1:]))
            groups.append(group)
check('independent_force_tangent_chronology',cursor==171 and ordinal==348 and sum(e['completed'] for e in events)==331 and baseordinal==177 and categories==Counter(accepted=153,armijo_insufficient_decrease=1,invalid_J=9,unsupported_arithmetic_range=8),'177 base+171 trials=348 F;177 base+154 complete trials=331 complete F;177 completeT;17 rejected incomplete trials=9invalidJ+8range.')
stored_events=reference['counter_accounting']['reconstructed_force_events']
check('stored_counter_equals_independent_ordinals',len(stored_events)==len(events) and all(all(v==stored_events[i].get(k) for k,v in e.items()) for i,e in enumerate(events)) and result['call_counts']==receipt['call_counts']==reference['counter_accounting']['counts']==dict(force_calls=348,force_calls_completed=331,tangent_calls=177,tangent_calls_completed=177,solver_invocations=1,JIT_calls=0,HP_calls=0),'Saved referencecounter all348event ordinals/classifications match independent direct JSONchronology.')
linear=result['path_diagnostics']['linear_solve_diagnostics']
check('predictor_and_corrector_LU',Counter(x['phase'] for x in linear)==Counter(predictor=23,corrector=153) and all(x['displacement_mode']=='port_projection' and x['applied_dw'] is False and x['applied_dR'] is True for x in linear if x['phase']=='predictor'),'23 realpredictorreaction-estimator LUs and153 correctorLUs; originalprojectioninitialization flags.')
first=read(NEW+'/run_001/first_force_range_input/observation.json')
range_trials=[r for r in rejected if r['reason']=='unsupported_arithmetic_range']
check('firstrange323_recovered_trial',range_trials[0]['force_call']==first['force_call_ordinal']==323 and first==receipt['first_force_range_input'] and first['state_sha256'] not in [s['state_sha256'] for s in result['states']] and range_trials[0]['original_target_index']==23 and range_trials[0]['newton_check']==5 and range_trials[0]['factor']==1. and all(first[k]==0 for k in ('extra_force_calls','extra_tangent_calls','extra_solver_calls','HP_calls')),'Actual zero-endpoint rejected force trial323 was followed by smaller acceptedtrial within same Newton group; saved rejected state is not HPqualified or described as repaired.')
bind(NEW+'/run_001/first_force_range_input/input.npz',first['input_npz_sha256'])
check('fullfresh48HP',len(reference['states'])==24 and reference['HP_calls_started']==reference['HP_calls_completed']==lifecycle['HP_calls_started']==lifecycle['HP_calls_completed']==48 and reference['checks_completed']==lifecycle['checks_completed']==476733 and lifecycle['status']=='pass' and lifecycle['elapsed_seconds']<=1500 and lifecycle['sampled_peak_RSS_bytes']<=8*1024**3 and all(r['status']=='pass' and r['HP_calls']==2 and r['state_sha256']==s['state_sha256'] and r['index']==i and r['target_mm']==s['d'] and r['elements_compared']==3280 and r['global_DOFs_compared']==6806 and all(c['pass_gate'] for c in r['checks']) for i,(r,s) in enumerate(zip(reference['states'],result['states']))),'Every actualaccepted state gets two freshHP references and full3280element/6806DOF coverage,476733 checks. No rejectedstate qualification.')
def bind_reference_records(value):
    if isinstance(value,dict):
        if 'path' in value and 'sha256' in value:
            bind(NEW+'/reference/'+value['path'],value['sha256'])
        for child in value.values():bind_reference_records(child)
    elif isinstance(value,list):
        for child in value:bind_reference_records(child)
for row in reference['states']:bind_reference_records(row)
hp_paths=[p['path'] for row in reference['states'] for p in row['references']]
check('48_distinct_new_HP_archives_and_all_output_records',len(hp_paths)==len(set(hp_paths))==48 and all([Path(p['path']).name for p in row['references']]==['hp80_full_local.json.gz','hp120_full_local.json.gz'] for row in reference['states']),'Raw SHA of all currentreference records including48 distinct80/120 gzip archives; no decompress/import/reference evaluation.')
check('qualification_limits_preserved',all(reference[k] is False for k in ('contact_qualified','pressure_qualified','clamp_qualified')) and reference['counter_accounting']['rejected_trials_independently_qualified'] is False and reference['counter_accounting']['unsupported_arithmetic_issue_resolved'] is False,'Acceptedmechanics qualification is separate from contact/pressure/clamping and unresolvedrejectedtrial range scope.')
resources['reference'].update(helper_elapsed_seconds=lifecycle['elapsed_seconds'],helper_peak_RSS_bytes=lifecycle['sampled_peak_RSS_bytes'])

oldfreeze=read(OLD+'/run_001/source_freeze.json')
oldcore={p:h for p,h in oldfreeze['sources'].items() if p.startswith('hf_repo/src/hf_eval/')}
newcore={p:h for p,h in freeze['sources'].items() if p.startswith('hf_repo/src/hf_eval/')}
check('core24_preserved_and_preparation_only_delta',len(oldcore)==24 and len(newcore)==25 and {p:h for p,h in newcore.items() if p!='hf_repo/src/hf_eval/analysis_domain.py'}==oldcore,'New API adds onegeometry derivationmodule; existing24core raw identity unchanged.')
prep=read(PREP+'/run_001/preparation_receipt.json')
task,oldtask=read(NEW+'/run_001/task.json'),read(OLD+'/run_001/task.json')
check('actual_onefactor_mapping_inputs',prep['status']=='pass' and prep['model_sha256']==receipt['model_sha256'] and prep['model_comparison']['total_fields']==27 and len(prep['model_comparison']['raw_equal_fields'])==10 and len(prep['model_comparison']['physically_mapped_fields'])==17 and prep['model_comparison']['parent_physical_subdomain_byte_exact'] and {k for k in task if task[k]!=oldtask[k]}=={'geometry','background_symmetry','task_id','purpose','parameter_origin','description'},'Actual prepareproof: oldphysicaldomain preserved; addright2columns andtop82. SameE/nu/gamma/alpha/Lr80/t20/h1/body/ports/24targets; no NPZreobservation by reviewer.')
check('oldbaseline_preserved',digest(ROOT/OLD/'run_001/result/result.json')=='b1bffb74a3ef105b111e9f6aa50ef6322e392899135073f58a4283f6408b3ba4' and oldreference['status']=='pass' and oldreference['accepted_states']==24 and oldreference['HP_calls_completed']==48 and oldreference['result_sha256']==digest(ROOT/OLD/'run_001/result/result.json'),'Selectedgamma1e-6 completedbaseline retained; not gammahalfcomparison or reusednewHP.')

view,phase=read(VIEW+'/view/view.json'),read(VIEW+'/view/phase_view.json')
summaries={n:read(VIEW+'/view/'+n+'/summary.json') for n in ('gamma1e6','right2col')}
check('view_closed48observations',view['status']==phase['status']=='pass' and view['failure'] is phase['failure'] is None and all(view[k]==phase['original_observation_counts'][k]==48 for k in ('geometry_started','geometry_completed','nodal_started','nodal_completed')) and view['new_F_T_model_solver_HP_calls']==phase['new_geometry_nodal_F_T_model_solver_HP_calls_outside_raw_viewer']==0 and phase['final_resource_check_passed'] and phase['elapsed_seconds']<=180,'Existing originalviewer observed both24state cases oncegeometry/nodal each; reviewer does no observation.')
resources['view'].update(helper_elapsed_seconds=phase['elapsed_seconds'],helper_peak_RSS_bytes=phase['sampled_peak_helper_RSS_bytes'])
for p,h in phase['outputs'].items():bind(VIEW+'/view/'+p,h)
for name,r in (('gamma1e6',oldresult),('right2col',result)):
    rows=summaries[name]['rows']
    check(name+'_saved_state_source',len(rows)==summaries[name]['accepted_states']==24 and summaries[name]['reference_available'] and all(v['index']==i and v['original_target_index']==s['original_target_index'] and v['leg']==s['leg'] and v['d_mm']==s['d'] and v['state_sha256']==s['state_sha256'] and v['R_input_N']==s['R_input'] and v['q_out_mm']==s['q_out'] and v['total_body_Fy_N']==s['workpiece']['force_on_lower_body_N']['total'][1] and v['total_body_Fx_N']==s['workpiece']['force_on_lower_body_N']['total'][0] for i,(v,s) in enumerate(zip(rows,r['states']))),'Viewsummary rows tied exactly to saved matching mechanicalstates, not ordinalshift or wrongbranch.')
    for i,row in enumerate(rows):
        d=read(VIEW+'/view/'+name+f'/{i:03d}/derived.json')
        check(name+f'_derived_{i:03d}_identity',d['row']==row,'Saved viewerderived row exactly agrees with casesummary.')
fields=['R_input_N','q_out_mm','total_body_Fx_N','total_body_Fy_N','material_body_Fy_N','regularization_body_Fy_N','medium_max_abs_Hu_per_mm','medium_min_J','solid_Green_principal_max','tip_to_bottom_mm']
comparisons=[]
for old,new in zip(summaries['gamma1e6']['rows'],summaries['right2col']['rows']):
    assert (old['original_target_index'],old['leg'],old['d_mm'])==(new['original_target_index'],new['leg'],new['d_mm'])
    metrics={k:dict(baseline=old[k],right2=new[k],delta=new[k]-old[k],relative_percent=(new[k]-old[k])/abs(old[k])*100 if old[k]!=0 else None) for k in fields}
    comparisons.append(dict(index=old['index'],leg=old['leg'],d_mm=old['d_mm'],metrics=metrics))
peak=comparisons[13]
nextstep=dict(recommendation='Use the current analysis_domain API for right4mm versus actualright2mm before calling the bodyforce marginindependent.',
 reason='PeakFy changes little0→2, but earlyweak Fy changes appreciably; only one finite-margin datum exists and right-edgebody was boundarytouching in oldcase.',
 method='Add2rightcolumns to current82-wide HFgeometry, retain fulloldphysical82domain and LFsourcehistory, retask only geometryidentity+top84+description; actual totalmargin4 is distinct from appendedincrement2.',
 matched_conditions=['Same originalmechanism/bodyphysicalcoordinates','Sameh1mm/E1MPa/nu.3/t20/gamma1e-6/alpha1e-6/Lr80','Same support/entity/bodyconstraints andphysicalports/weights','Same24targets0→1.2→0/freshzero/port_projection/settings/gates','Onlyrightdomainmargin2→4 and explicitbackgroundtop82→84 change'],
 outputs=['Allmatched loading/unloading signedbodyFx/Fy total/material/Hu components','Inputreaction/qout and peak/same1mm/early0.25–0.85 targets','Tipfinitegap/rayclearance, mediumminJ/maxHu withsamefieldscope','Return-zero residual forces and pathfailure/rejected-trial chronology'],
 analytical_expected_counts=dict(cells=3360,nodes=3485,dofs=6970,fixed=452,free=6518,body_cells=162,body_nodes=190,body_dofs=380,body_top_overlap=19),
 budget_principle='Newclosedcards only. Production use actual2485.75s×3360/3280≈2546.38s ascostcontext with nonlineariterationheadroom; proposed4500/4560sec8GiB ifrootchooses. Reference derivesactualN afterfullproductionPASS: actual554.096s×(3360/3280)×N/24, thenexplicitheadroom;1500/1560 isplausibleforN24 butmustberecheckedbeforefreeze. View180/2108GiB for allsavedstates, not inheritedoldwindow.',
 limits='One2→4 comparison tests margin sensitivity; it cannot prove convergence over everymargin, mesh, gamma orstablefree-bodyclamping. Mesh refinement is a laterlargercost separatefactor, not mixed into marginstudy.')
report=dict(schema_version='right-margin-final-saved-result-review-1.0',status='pass_saved_only',checks_passed=len(checks),checks=checks,
 actual_counts=result['call_counts'],independent_chronology=dict(base_calls=177,trial_calls=171,trial_categories=dict(categories),corrector_groups=len(groups),maximum_trials_per_group=max(map(len,groups)),forceevents=events,rejected_incomplete_trials=rejected,first_range_force_ordinal=323,failed_attempts=0,bisections=0),
 reference=dict(actual_states=24,fresh_HP_calls=48,checks_completed=476733,qualification=reference['qualification'],contact_qualified=False,pressure_qualified=False,clamp_qualified=False),
 resources=resources,paired24comparisons=comparisons,peak_comparison=peak,next_step=nextstep,
 relative_percent_definition='100*(right2-baseline)/abs(baseline); signedchange. Positivepercentage for negativeFx means its magnitude decreased.',
 physical_interpretation=['Observed0→2domainpadding has weak effect onpeaknormalresultant, but substantiallylarger relativeeffect on earlysmallforces; reportsignedcomponents/absolutechanges aswellaspercentages.',
 'Atpeak materialFy changes-0.00039503N while regularizationFy changes+0.000619127N, yielding smallnet+0.000224097N. TotalFy stability thereforedoesnot establishcomponentstability; regularizationfraction rises~0.159%→0.678% oftotal, whileFx magnitude falls8.256%.',
 'Hu is regularizationkinematicfieldmax, and bodyregularizationforce is a separateweakprojection; maximumHu doesnot byitselfattribute everybodyforce contribution or isolate all addedstripforce.',
 'BodyFx remainsnonzero: symmetricupperreflection doubleshorizontalbodyload whileverticalcancels. Fixedbodyholdingmodel doesnot establish stablefreebodygrip orpressure distribution.',
 'Unsignedtipfinitegap and outwardfirst-raydiagnostics are geometryobservations; they do not prove acontactset. minJ is9pointSimpsonincludingcorners; coarseh1 doesnot establishmeshconvergedforce/gap.',
 '9invalidJ+8arithmeticrange trialexceptions are recovered byexistingline-searchhalving. AllacceptedstatespassfreshHP, but rejectedtrialarithmeticissue is not claimedresolved or independentlyqualified.'],
 reviewer_activity=dict(HF_imports=0,NPZ_array_loads=0,constructors=0,F_T_solver_HP_calls=0,geometry_nodal_strain_plot_calls=0,formal_writes=0),
 reviewer_selfcheck=dict(kind='Saved-reference record parsing only',initial_error='TypeError when passing record dictionary rather than record[path] to Path basename check',correction='Use declared path string; source retained as review_final_saved_result_before_record_path_fix.py',science_or_formal_phase_failure=False,preserved_source_sha256=digest(OUT/'review_final_saved_result_before_record_path_fix.py')),
 source_and_evidence_pins=pins,unique_files_hashed=len(pins),review_helper_sha256=digest(Path(__file__)))
out=OUT/'final_saved_result_review.json'
with out.open('w',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def value(i,k):
    m=comparisons[i]['metrics'][k]
    return f"{m['baseline']:.10g} → {m['right2']:.10g} ({m['relative_percent']:+.6g}%)" if m['relative_percent'] is not None else f"{m['baseline']:.10g} → {m['right2']:.10g}"
md=['# 右侧介质余量2mm：保存结果独立审查','',f'状态：PASS saved-only；{len(checks)}项核查，{len(pins)}个唯一文件SHA。只JSON/原文件SHA，不导入HF或加载NPZ数组，不新增力学/几何/节点力/应变/绘图。','',
 '新工况完整24原始目标、无失败路径尝试/二分态；348次F中331次完成，177次T全部完成；23 predictor+153 corrector LU。171次试探含153接受、1完整Armijo拒绝、9invalid_J与8arithmetic-range不完整拒绝。首range ordinal323属于卸载0mm第5Newton完整步试探，后续缩半接受，非失败路径或已修复算术范围。',
 '', '24态48次新80/120 HP全部PASS、476733检查；新模型c880381a…，峰值状态6ae284e…。生产/参考/视图协议、全部绑定和输出SHA复核。原γ=1e-6基线保持。', '',
 '| 同loading峰值1.2mm指标 | 0mm旧余量 → 2mm新余量 |','| --- | --- |']
for k in fields:md.append('| '+k+' | '+value(13,k)+' |')
md+=['','| early loading d(mm) | 总Fy(N)：旧→新 | material Fy | regularization Fy |','| --- | --- | --- | --- |']
for i in (1,2,3,4,5,6,7,9):md.append(f"| {comparisons[i]['d_mm']} | {value(i,'total_body_Fy_N')} | {value(i,'material_body_Fy_N')} | {value(i,'regularization_body_Fy_N')} |")
md+=['','百分比定义为100×(新−旧)/abs(旧)：Fx负值时正百分比表示幅值减小。峰值material Fy下降0.00039503N、regularization Fy增加0.000619127N，小净增0.000224097N含有两分量抵消；Hu力占总Fy约0.159%→0.678%，全局Hu最大值仅增0.0576%不能证明该力分量稳定。Fx幅值降低8.256%。','','峰值有限tip-bottom间隙用毫米保存；与全域minJ、free-medium maxHu按各字段范围比较，不以范围不同的全域/medium观察强制相等。早期小力百分比不能单独代表工程重要性，需同看绝对变化。Fx非零、固定刚体及对称反射不支持自由物体稳定夹持或压力资格。','','下一步优先在现有API下对比4mm与2mm余量：保持h1、材料、Lr80、工件/结构坐标、端口、支承及24行程完全相同。可对当前82列HF几何再补2列，明确总余量4mm；任务顶边延伸至84。解析预期3360cells/3485nodes/6970DOFs、452fixed/6518free，必须由新实际准备核验。','','成本以本次实际生产2485.75s、参考554.096s、视图28.93s为依据；新生产4500/4560、参考1500/1560、视图180/210秒各8GiB是可供根考虑的有限独立卡，实际N确定后复核参考预算，不能续用旧关闭窗口。一个4vs2对照只能判断该范围敏感性，不能自动宣称所有余量或网格收敛。','',f'证据JSON：final_saved_result_review.json SHA `{digest(out)}`。']
(OUT/'final_saved_result_review.md').write_text('\n'.join(md)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(dict(status=report['status'],checks=len(checks),files=len(pins),json_sha256=digest(out),md_sha256=digest(OUT/'final_saved_result_review.md'),peak=peak,early_Fy=[(c['d_mm'],c['metrics']['total_body_Fy_N']) for c in comparisons[1:10]],resources=resources),ensure_ascii=False))
