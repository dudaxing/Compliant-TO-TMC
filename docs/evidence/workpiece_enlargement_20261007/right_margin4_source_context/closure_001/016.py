"""Propose/install closed4mm documents from saved JSON/SHA; no HF/NumPy imports."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

BASE = 'lf_data_preparation/native_workpiece_001/'
CASES = {'right2col':BASE+'right_margin_cycle_001','right4col':BASE+'right_margin4_cycle_001'}
VIEW = 'functional_views/right_margin4_20261007/complete_001'
EVIDENCE = 'docs/evidence/workpiece_enlargement_20261007/'
PROGRESS = EVIDENCE+'right_margin4_progress.json'
CONTEXT = EVIDENCE+'right_margin4_source_context/closure_001'
REPORT = 'docs/WORKPIECE_ENLARGEMENT_20261007.md'
MATRIX = 'docs/PHYSICAL_FUNCTION_PROGRESS.md'
FRONTS = ['README.md','hf_repo/README.md','docs/CURRENT_STATUS.md','docs/PROJECT_STATUS.md','docs/RESUME_DEVELOPMENT.md']
METRICS = ['R_input_N','q_out_mm','total_body_Fx_N','total_body_Fy_N','material_body_Fx_N','material_body_Fy_N',
           'regularization_body_Fx_N','regularization_body_Fy_N','cached_two_sided_normal_magnitude_sum_N',
           'tip_to_bottom_mm','medium_min_J','medium_max_abs_Hu_per_mm','solid_min_J',
           'solid_Green_principal_min','solid_Green_principal_max']
sha = lambda data:sha256(data).hexdigest()
dump = lambda value:(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')


def collect(root):
    pins = {}
    def raw(name):
        data=(root/name).read_bytes();pins[name]=sha(data);return data
    def read(name):return json.loads(raw(name))
    def same_files(bindings):
        assert all(sha((root/name).read_bytes())==pin for name,pin in bindings.items())
    def closed(control,phase,protocol_name=None):
        name=control+'/'+(protocol_name or phase+'_protocol.json')
        protocol,launch=read(name),read(control+'/'+phase+'_launch.json')
        assert launch['status']=='pass' and launch['exit_code']==0 and launch['invocations']==1
        assert launch['stop_reason'] is None and launch['all_bindings_unchanged']
        assert launch['protocol_sha256']==pins[name] and launch['bindings']==protocol['bindings']
        limits=protocol['phases'][phase]
        assert launch['elapsed_seconds']<=limits['outer_seconds'] and launch['peak_sampled_tree_RSS_bytes']<=protocol['sampled_RSS_bytes']
        same_files(protocol['bindings'])
        return protocol,launch
    cases,states={},{}
    for label,control in CASES.items():
        prod,pl=closed(control,'production')
        assert prod['phases']['production']['helper_seconds']==4500 and prod['phases']['production']['outer_seconds']==4560 and prod['sampled_RSS_bytes']==8*1024**3
        execution=read(control+'/run_001/execution_receipt.json')
        result_name=control+'/run_001/result/result.json';result=read(result_name)
        assert result['status']=='success' and execution['status']=='pass'
        assert execution['result_sha256']==pins[result_name] and execution['sources_unchanged'] and execution['inputs_unchanged']
        assert execution['elapsed_seconds']<=prod['phases']['production']['helper_seconds'] and execution['sampled_peak_RSS_bytes']<=prod['sampled_RSS_bytes']
        assert execution['HP_calls']==execution['JIT_calls']==execution['LF_imports']==0
        assert all(result[k] for k in ('path_completed','loading_peak_reached','unload_endpoint_reached','task_target_executed'))
        n=result['accepted_states'];assert n==len(result['states'])==execution['accepted_states']
        rp,rl=closed(control,'reference')
        assert rp['phases']['reference']['helper_seconds']==1500 and rp['phases']['reference']['outer_seconds']==1560 and rp['sampled_RSS_bytes']==8*1024**3
        ref=read(control+'/reference/summary.json');contract=read(control+'/reference_contract.json')
        assert ref['status']=='pass' and ref['result_sha256']==pins[result_name]
        assert ref['accepted_states']==len(ref['states'])==n and ref['HP_calls_started']==ref['HP_calls_completed']==2*n
        assert contract['actual_accepted_states']==rp['actual_accepted_states']==n
        assert contract['expected_new_HP80_120_calls']==rp['expected_new_HP80_120_calls']==2*n
        assert contract['production_result_sha256']==pins[result_name] and contract['production_receipt_sha256']==pins[control+'/run_001/execution_receipt.json']
        assert ref['independent_reference_contract_sha256']==pins[control+'/reference_contract.json']
        assert ref['full_element_and_DOF_coverage'] and not ref['HP_matrix_columns_exhaustively_checked']
        assert all(ref[k] is False for k in ('contact_qualified','clamp_qualified','pressure_qualified'))
        assert ref['elapsed_seconds']<=rp['phases']['reference']['helper_seconds'] and ref['sampled_peak_RSS_bytes']<=rp['sampled_RSS_bytes']
        assert all(ref[k]==0 for k in ('candidate_force_calls','tangent_calls','solver_calls','model_constructions'))
        same_files(ref['source_bindings']);same_files(ref['input_bindings'])
        assert [s['index'] for s in ref['states']]==list(range(n))
        for state,check in zip(result['states'],ref['states']):
            assert check['status']=='pass' and check['HP_calls']==2 and check['state_sha256']==state['state_sha256']
        model_name=control+'/run_001/result/'+result['model']['descriptor_path'];model=read(model_name)
        assert pins[model_name]==result['model']['descriptor_file_sha256'] and model['task_sha256']==result['task_sha256']
        cases[label]=dict(stage=control,result_sha256=pins[result_name],task=model['task'],task_sha256=model['task_sha256'],
            model_sha256=model['arrays']['sha256'],counts=model['region_metadata']['counts'],accepted_states=n,
            call_counts=result['call_counts'],production_helper_seconds=execution['elapsed_seconds'],production_outer_seconds=pl['elapsed_seconds'],
            reference_helper_seconds=ref['elapsed_seconds'],reference_outer_seconds=rl['elapsed_seconds'],HP_calls=2*n,checks_completed=ref['checks_completed'],
            reference_summary_sha256=pins[control+'/reference/summary.json'],reference_qualification=ref['qualification'])
        states[label]=result['states']
    old,new=cases['right2col']['task'],cases['right4col']['task']
    assert all(new[k]==v for k,v in old.items() if k not in {'geometry','background_symmetry','task_id','parameter_origin','description'})
    assert old['background_symmetry']['points_mm']==[[0.,40.],[82.,40.]]
    assert new['background_symmetry']=={**old['background_symmetry'],'points_mm':[[0.,40.],[84.,40.]]}
    vp,vl=closed(VIEW,'view','protocol.json');phase=read(VIEW+'/view/phase_view.json');view=read(VIEW+'/view/view.json')
    assert vp['phases']['view']['helper_seconds']==180 and vp['phases']['view']['outer_seconds']==210 and vp['sampled_RSS_bytes']==8*1024**3
    assert phase['status']==view['status']=='pass' and phase['final_resource_check_passed']
    assert phase['original_view_sha256']==pins[VIEW+'/view/view.json']
    assert phase['new_geometry_nodal_F_T_model_solver_HP_calls_outside_raw_viewer']==view['new_F_T_model_solver_HP_calls']==0
    assert phase['elapsed_seconds']<=vp['phases']['view']['helper_seconds'] and phase['sampled_peak_helper_RSS_bytes']<=vp['sampled_RSS_bytes']
    expected=sum(c['accepted_states'] for c in cases.values())
    assert all(view[k]==expected for k in ('geometry_started','geometry_completed','nodal_started','nodal_completed'))
    vc={c['label']:c for c in view['cases']};assert set(vc)==set(CASES)
    original={}
    for label,control in CASES.items():
        case,c=cases[label],vc[label]
        assert c['task']==case['task'] and c['model_sha256']==case['model_sha256']
        assert c['reference_available'] and c['production_path_completed'] and c['unload_endpoint_reached']
        assert c['saved_accepted_states']==c['observed_states']==case['accepted_states']
        assert view['input_source_bindings'][control+'/run_001/result/result.json']==case['result_sha256']
        assert view['input_source_bindings'][control+'/reference/summary.json']==case['reference_summary_sha256']
        name=label+'/summary.json';rows=read(VIEW+'/view/'+name)['rows']
        assert pins[VIEW+'/view/'+name]==view['outputs'][name]==phase['outputs'][name]
        assert len(rows)==case['accepted_states'];selected={}
        for index,(row,state) in enumerate(zip(rows,states[label])):
            assert row['index']==index and row['state_sha256']==state['state_sha256']
            assert row['d_mm']==state['d'] and row['leg']==state['leg'] and row['original_target_index']==state['original_target_index']
            if state['is_original_target']:
                assert row['d_mm']==case['task']['path']['targets_mm'][row['original_target_index']]
                key=(row['leg'],row['original_target_index'],row['d_mm']);assert key not in selected;selected[key]=row
        original[label]=selected
        case.update(tip_node=c['tip_node'],maximum_loading_stroke=rows[c['peak_index']],return_state=rows[c['last_index']],
            loading_Fy_peak=max((r for r in rows if r['leg']=='loading'),key=lambda r:r['total_body_Fy_N']))
    matched=[dict(leg=k[0],original_target_index=k[1],d_mm=k[2],right2col=original['right2col'][k],right4col=original['right4col'][k],
                  differences={name:original['right4col'][k][name]-original['right2col'][k][name] for name in METRICS})
             for k in sorted(set(original['right2col'])&set(original['right4col']),key=lambda k:k[1])]
    assert len(matched)==len(old['path']['targets_mm'])
    figures=['comparison.png','distances_forces.png','peak_fields.png','right2col/actual_states.gif','right4col/actual_states.gif']
    for name in figures:assert sha(raw(VIEW+'/view/'+name))==view['outputs'][name]==phase['outputs'][name]
    return dict(status='complete_mechanical_reference_views_project_incomplete',cases=cases,matched_original_targets=matched,
        view=dict(stage=VIEW,observations_each=expected,helper_seconds=phase['elapsed_seconds'],outer_seconds=vl['elapsed_seconds'],new_mechanics_calls=0,figures=figures),
        qualification='Complete declared cycle/allN fresh2N force/equilibrium/PORT-direction reference and saved observations; no general contact/pressure/full-tangent/mesh-convergence/free-body/HF5 claim',
        input_sha256=pins,new_scientific_calls=0)


def proposals(root,data):
    before={name:(root/name).read_bytes() if (root/name).exists() else None for name in FRONTS+[REPORT,PROGRESS,MATRIX]}
    progress=json.loads(before[PROGRESS])
    progress['prior_production_snapshot']=progress['production'];progress['prior_reference_snapshot']=progress['reference']
    progress['prior_complete_cycle_view_snapshot']=progress['complete_cycle_views']
    new=data['cases']['right4col'];peak=new['maximum_loading_stroke']
    progress.update(status=data['status'],production=dict(status='pass',stage=CASES['right4col'],accepted_states=new['accepted_states'],result_sha256=new['result_sha256'],actual_call_counts=new['call_counts']),
        reference=dict(status='pass',accepted_states=new['accepted_states'],HP_calls=new['HP_calls'],checks_completed=new['checks_completed'],result_sha256=new['result_sha256'],summary_sha256=new['reference_summary_sha256']),
        complete_cycle_views=dict(status='pass',**data['view']),final_closed_comparison=data,qualification=data['qualification'],
        next='Use whole matched2/4mm force/component/gap curves to select one further physical sensitivity or matched-design mesh step; two margins do not establish convergence')
    table='| 最大加载行程态 | R [N] | Fy [N] | 材料Fy | HuFy | 2侧法向幅值和 | tip-bottom [mm] | medium minJ | maxHu [/mm] |\n|---|---|---|---|---|---|---|---|---|\n'
    for label,c in data['cases'].items():
        row=c['maximum_loading_stroke'];table+='| '+label+' | '+' | '.join(f'{row[k]:.9g}' for k in ['R_input_N','total_body_Fy_N','material_body_Fy_N','regularization_body_Fy_N','cached_two_sided_normal_magnitude_sum_N','tip_to_bottom_mm','medium_min_J','medium_max_abs_Hu_per_mm'])+' |\n'
    common='| 原目标 | leg | d [mm] | R2/R4 [N] | Fy2/Fy4 [N] | gap2/gap4 [mm] |\n|---|---|---|---|---|---|\n'
    for m in data['matched_original_targets']:
        a,b=m['right2col'],m['right4col'];common+=f"| {m['original_target_index']} | {m['leg']} | {m['d_mm']:g} | {a['R_input_N']:.9g}/{b['R_input_N']:.9g} | {a['total_body_Fy_N']:.9g}/{b['total_body_Fy_N']:.9g} | {a['tip_to_bottom_mm']:.9g}/{b['tip_to_bottom_mm']:.9g} |\n"
    matrix="""# HF物理功能进度：当前闭卡范围

HF复用LF/N4研究成果，提供独立正向评价，不含优化器。外部研究层负责比较、优选，HF5评价接口尚未完成。

| 功能 | 已实现/本次可查看 | 待实现或未取得资格 |
|---|---|---|
| 结构作用与变形 | 固定side18方体、2/4mm域、平均输入/自由输出、加载/回零、×1结构/GIF | 更多任务自身证据；自由体释放/稳定性 |
| 力及其位置 | R、固定下半工件总/材料/Hu(Fx,Fy)、holding及节点力；完整力、平衡和PORT方向切线作用的新参考 | 连续压力、有效接触/夹持定义、全切线列、摩擦 |
| 距离与场 | 有限面距离、保存J/Hu、binary64 Green主应变；原9点Lobatto含角点J门 | signed penetration、一般包含/自身重叠、应变/应力HP；场图不是压力 |
| 输入与域 | 自包含LFv2/明确task、Q1原生网格、HF派生介质域；82→84旧物理子域保持 | 同设计匹配网格、统一一次评价入口；新模型不继承旧资格 |
| 一般夹持 | 固定方体完整评价；固定圆体单元覆盖入口存在 | 圆体自身完整边界/平衡、自由刚体平移/转动/力矩、摩擦 |
| HF5与易用 | 单任务后端和保存证据可用，LF/N4研究层保留 | 薄评价接口、同任务小批量、紧凑响应/失败/来源和重复性合同 |

R为半模型输入反力；下半工件Fy为固定体弱式on-body力，holding反向。2|Fy|为镜像法向幅值和，装配净力为(2Fx,0)。q_out为加权竖向端口位移，不是tip gap。Hu场最大值与Hu力分量分开记录。当前机械模式不计算辅助材料能量，不表示旧能量入口不存在。

两域结果不单独证明域/网格收敛。看同方向/原目标全曲线、材料/Hu分量、绝对量及距离，再选择一次物理敏感性或同设计细网格；同时推进薄正向接口，不重写LF/N4优化器。后续科学卡尚未执行。
"""
    matrix+=f"\n[完整报告](WORKPIECE_ENLARGEMENT_20261007.md)；[进度](evidence/workpiece_enlargement_20261007/right_margin4_progress.json)；[结构与力](../{VIEW}/view/comparison.png)；[距离与力](../{VIEW}/view/distances_forces.png)；[J/Hu/Green](../{VIEW}/view/peak_fields.png)；[4mm实际动画](../{VIEW}/view/right4col/actual_states.gif)。\n"
    append=f"\n\n## 右介质余量2→4 mm：完整新生产、参考与保存视图终态\n\n同h1、E1/ν.3/厚20、γ=α=1e-6/Lr80、side18中心(71,40)、原端口/支撑与24目标，仅父82mm域再补2列至84mm、累计余量4mm并延长背景顶边。来源准备阶段的实际映射核验不代替力学资格。本次新生产实际接受{new['accepted_states']}态完成0→1.2→0，新全部N态{new['HP_calls']}次HP80/120、{new['checks_completed']}项检查通过。视图共{data['view']['observations_each']}次几何/{data['view']['observations_each']}次节点力观察，各1/态，零新F/T/构模/求解/HP。\n\n{table}\n共同原目标对照：加载/卸载按leg和原目标序号分别匹配，二分中间态保留于完整视图，不混下表。所有Fx、材料/Hu分量、J/Hu、Green主应变及回零原值在进度JSON保存，不重算物理或人为归零。\n\n{common}\nR、下半Fy及2侧法向幅值和分别解释；q_out与有限tip距离分别记录。完整力、离散平衡/固定工件力及声明PORT方向切线作用参考，不扩展到全切线列、连续压力、一般接触、自由体、应变HP或域/网格收敛。原准备/运行前缀是历史快照，本节为实际终态；冻结源码、门槛和科学窗口不改。\n\n[功能矩阵](PHYSICAL_FUNCTION_PROGRESS.md)；[实际进度](evidence/workpiece_enlargement_20261007/right_margin4_progress.json)；[结构/力](../{VIEW}/view/comparison.png)；[距离/力](../{VIEW}/view/distances_forces.png)；[J/Hu/Green](../{VIEW}/view/peak_fields.png)；[4mm动画](../{VIEW}/view/right4col/actual_states.gif)。HF只正向评价、不重写LF/N4优化器；HF5未完成。下一项依据整条2/4mm同目标曲线决定，不预先宣布收敛。\n"
    matrix_bytes=matrix.encode('utf-8')
    if before[MATRIX] is not None:matrix_bytes+=b'\n\n---\n\n'+before[MATRIX]
    result={REPORT:before[REPORT]+append.encode('utf-8'),MATRIX:matrix_bytes,PROGRESS:dump(progress)}
    for name in FRONTS:
        prefix='../' if name.startswith(('hf_repo/','docs/')) else ''
        report='WORKPIECE_ENLARGEMENT_20261007.md' if name.startswith('docs/') else prefix+REPORT
        progress_link='evidence/workpiece_enlargement_20261007/right_margin4_progress.json' if name.startswith('docs/') else prefix+PROGRESS
        matrix_link='PHYSICAL_FUNCTION_PROGRESS.md' if name.startswith('docs/') else prefix+MATRIX
        front=f"## 当前：4 mm右介质域完整正向评价已完成\n\nHF复用LF/N4几何与研究成果，提供独立正向力学评价，不含优化器；开发统一main，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git，HF5尚未完成。同固定side18中心(71,40)、h1/E1/γ=α=1e-6/Lr80，2→4mm域的新完整{new['accepted_states']}态、{new['HP_calls']}新HP及{new['checks_completed']}检查和保存视图通过；未借旧模型资格。\n\n最大加载行程态d={peak['d_mm']:g}mm：半模型R={peak['R_input_N']:.9g}N，下半工件Fy={peak['total_body_Fy_N']:.9g}N，两侧法向幅值和={peak['cached_two_sided_normal_magnitude_sum_N']:.9g}N，有限tip底面距={peak['tip_to_bottom_mm']:.9g}mm。2|Fy|不是装配净力，q_out是加权端口位移。同原目标全曲线、材料/Hu分量及绝对量须一起看，不由峰值概括全路径或域/网格收敛。压力/接触定义、圆体自身完整任务、自由体/摩擦和HF5仍待实现或验证。\n\n[完整报告]({report})；[实际进度]({progress_link})；[功能矩阵]({matrix_link})；[结构/力]({prefix}{VIEW}/view/comparison.png)；[距离/力]({prefix}{VIEW}/view/distances_forces.png)；[4mm动画]({prefix}{VIEW}/view/right4col/actual_states.gif)。异目录恢复main后以实际Git根定位；旧闭卡不重跑，下一项据整条2/4mm曲线选择一个物理或匹配网格步骤。默认tangent未切换，探索显式port_projection，HF不重写优化器。\n\n---\n\n以下整段原字节为收尾前历史；当前状态以上方及最新报告/进度为准。\n\n"
        result[name]=front.encode('utf-8')+before[name]
    return before,result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['propose','install'])
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True,help='external short-file proposal directory')
    parser.add_argument('--review',type=Path,help='saved-only final documentation review for install')
    args=parser.parse_args();root,output=args.repo.resolve(),args.output.resolve()
    assert not output.is_relative_to(root)
    data=collect(root)  # Actual closed science/view gates precede any proposal/install write.
    if args.action=='propose':
        assert not output.exists();before,payloads=proposals(root,data);output.mkdir();(output/'files').mkdir()
        files={}
        for index,(name,payload) in enumerate(payloads.items(),1):
            short=f'files/{index:03d}{Path(name).suffix}';(output/short).write_bytes(payload)
            files[name]=dict(path=short,sha256=sha(payload),expected_preimage_sha256=sha(before[name]) if before[name] is not None else None)
        manifest=dict(status=data['status'],files=files,input_sha256=data['input_sha256'],closed_summary=data,new_scientific_calls=0)
        (output/'manifest.json').write_bytes(dump(manifest));print(json.dumps(dict(status='external_proposals_only',files=len(files),manifest=str(output/'manifest.json'))));return
    assert args.review is not None
    manifest=json.loads((output/'manifest.json').read_bytes());review=json.loads(args.review.read_bytes())
    assert manifest['status']==data['status'] and review['status']=='pass_saved_only' and not review['blocking_findings']
    assert review['proposal_sha256']=={name:entry['sha256'] for name,entry in manifest['files'].items()}
    assert manifest['input_sha256']==data['input_sha256'], 'Closed inputs changed after review'
    before={name:(root/name).read_bytes() if (root/name).exists() else None for name in manifest['files']}
    blobs={name:(output/entry['path']).read_bytes() for name,entry in manifest['files'].items()}
    for name,entry in manifest['files'].items():
        assert (sha(before[name]) if before[name] is not None else None)==entry['expected_preimage_sha256']
        assert sha(blobs[name])==entry['sha256']
    context=root/CONTEXT;assert not context.exists();context.mkdir()
    archive={'001.json':before[PROGRESS],'002.json':(output/'manifest.json').read_bytes(),'003.json':args.review.read_bytes(),'004.py':Path(__file__).read_bytes()}
    author=Path(__file__).resolve().parent
    for short,name in [('005.md','README.md'),('006.json','author_note.json'),('007.json','author_checks.json'),('008.diff','source_additions.diff')]:archive[short]=(author/name).read_bytes()
    for name,payload in archive.items():(context/name).write_bytes(payload);assert (context/name).read_bytes()==payload
    installed={}
    for name,payload in blobs.items():
        (root/name).parent.mkdir(parents=True,exist_ok=True);(root/name).write_bytes(payload);assert (root/name).read_bytes()==payload
        installed[name]=dict(before_sha256=sha(before[name]) if before[name] is not None else None,after_sha256=sha(payload))
    assert (root/REPORT).read_bytes().startswith(before[REPORT]) and all((root/name).read_bytes().endswith(before[name]) for name in FRONTS)
    receipt=dict(status='pass_reviewed_file_only_install',new_scientific_calls=0,installed_files=installed,
        archive={name:dict(path=CONTEXT+'/'+name,sha256=sha(payload)) for name,payload in archive.items()},original_fronts_and_report_raw_preserved=True,
        prelaunch_and_running_archives='Existing source_context short files unchanged; prior progress raw001.json here',closed_input_sha256=data['input_sha256'])
    (context/'documentation_install.json').write_bytes(dump(receipt))
    (context/'INDEX.md').write_text('Selected file-only closure:001 prior progress;002 proposal manifest;003 saved-only review;004–008 author source. RawSHA/path map in documentation_install.json. Existing prelaunch/running snapshots and scientific records unchanged; no large output or duplicated whole history tree.\n',encoding='utf-8')
    print(json.dumps(dict(status=receipt['status'],files=len(installed),receipt=CONTEXT+'/documentation_install.json')))


if __name__=='__main__':main()
