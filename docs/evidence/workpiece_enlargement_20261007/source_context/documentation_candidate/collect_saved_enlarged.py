"""Collect final closed saved facts and append proposals; no mechanics/API/plot imports.

Root runs this only after complete new production, all fresh HP and saved views.
The output contains proposals. Source documents, protocols and results are untouched.
"""
from pathlib import Path
from hashlib import sha256
import argparse
import json

BASELINE = 'b31003303960231c5cc6bf95c9fd6fe751f85da8'
CASE = 'lf_data_preparation/native_workpiece_001/enlarged_square_contact_001'
POSE = 'lf_data_preparation/native_workpiece_001/shift_square_pose_002'
FAILED = 'lf_data_preparation/native_workpiece_001/shift_square_tip_align_001'
FAILED_VIEW = 'functional_views/workpiece_tip_align_20261007/failed_preview_001'
VIEW = 'functional_views/workpiece_enlarge_20261007/complete_001'
FIT = 'functional_views/workpiece_enlarge_20261007/fit_001'
TARGETS = [0.,.25,.5,.65,.75,.8,.85,.9,.95,1.,1.05,1.1,1.15,1.2,1.15,1.1,1.,.9,.8,.75,.65,.5,.25,0.]
PREDECESSOR_TARGETS = [0.,.5,1.,1.5,1.75,1.8,1.75,1.5,1.,.5,0.]
DOCUMENTS = ('WORKPIECE_SHIFT_AND_SOFTNESS_20261004.md','HF_FUNCTION_PROGRESS_20261004.md','CURRENT_STATUS.md','RESUME_DEVELOPMENT.md')


def sha(path):
    return sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')


class SavedFacts:
    def __init__(self, root):
        self.root, self.bindings = root, {}

    def path(self, name):
        path = (self.root/name).resolve()
        path.relative_to(self.root)
        return path

    def read(self, name):
        path = self.path(name)
        self.bindings[path.relative_to(self.root).as_posix()] = sha(path)
        return json.loads(path.read_text(encoding='utf-8'))

    def pin(self, name, expected):
        path = self.path(name)
        assert sha(path) == expected, name
        self.bindings[path.relative_to(self.root).as_posix()] = expected

    def phase(self, stage, name):
        protocol = self.read(stage+'/'+name+'_protocol.json')
        launch = self.read(stage+'/'+name+'_launch.json')
        assert launch['protocol_sha256'] == self.bindings[stage+'/'+name+'_protocol.json']
        assert launch['status'] == 'pass' and launch['exit_code'] == 0 and launch['invocations'] == 1
        assert launch['all_bindings_unchanged'] is True and launch['stop_reason'] is None
        limit = protocol['phases'][name]
        assert launch['elapsed_seconds'] <= limit['outer_seconds']
        assert launch['peak_sampled_tree_RSS_bytes'] <= protocol['sampled_RSS_bytes']
        return protocol, launch

    def completed_case(self, stage, label, targets, view):
        run = stage+'/run_001'
        inventory = self.read(run+'/input_inventory.json')
        receipt = self.read(run+'/execution_receipt.json')
        result_name = run+'/result/result.json'
        result = self.read(result_name)
        task = self.read(run+'/task.json')
        _, production_launch = self.phase(stage,'production')
        contract = self.read(stage+'/reference_contract.json')
        _, reference_launch = self.phase(stage,'reference')
        reference = self.read(stage+'/reference/summary.json')
        life = self.read(stage+'/reference/lifecycle.json')
        n = len(result['states'])
        assert result['status'] == 'success' and result['failure'] is None and receipt['status'] == 'pass'
        assert all(result[k] is True for k in ('path_completed','target_reached','production_converged','task_target_executed','loading_peak_reached','unload_endpoint_reached'))
        assert result['targets_mm'] == task['path']['targets_mm'] == inventory['case']['targets_mm'] == reference['audited_targets_mm'] == targets
        assert [s['d'] for s in result['states'] if s['is_original_target']] == targets
        assert result['states'][0]['d'] == result['states'][-1]['d'] == 0.
        assert result['accepted_states'] == receipt['accepted_states'] == reference['accepted_states'] == life['accepted_states_completed'] == n
        assert reference['status'] == life['status'] == 'pass'
        assert reference['HP_calls_started'] == reference['HP_calls_completed'] == life['HP_calls_started'] == life['HP_calls_completed'] == 2*n
        assert reference['result_sha256'] == receipt['result_sha256'] == contract['production_result_sha256'] == self.bindings[result_name]
        assert [s['state_sha256'] for s in reference['states']] == receipt['state_sha256'] == [s['state_sha256'] for s in result['states']]
        assert reference['independent_reference_contract_sha256'] == self.bindings[stage+'/reference_contract.json']
        assert all(result[k] is False for k in ('equilibrium_qualified','independent_HP_qualified','HF_qualified'))
        summary = self.read(view+'/view/'+label+'/summary.json')
        rows = summary['rows']
        assert summary['reference_available'] is True and summary['production_status'] == 'success'
        assert summary['accepted_states'] == len(rows) == n
        assert [s['state_sha256'] for s in rows] == [s['state_sha256'] for s in result['states']]
        assert all(s['index'] == i and s['d_mm'] == result['states'][i]['d'] for i,s in enumerate(rows))
        peak_index = max(range(n), key=lambda i: result['states'][i]['d'])
        assert result['states'][peak_index]['d'] == result['task_target_mm'] == max(targets)
        matched = [r for r in rows if r['leg']=='loading' and r['d_mm']==1.]
        assert len(matched)==1, 'No interpolation or loading/unloading substitution is permitted'
        fit = self.read(FIT+'/view/'+label+'_fit.json')
        assert fit['index'] == peak_index and fit['state_sha256'] == rows[peak_index]['state_sha256']
        assert fit['d_mm'] == max(targets) and fit['leg'] == 'loading'
        model_name = run+'/result/'+result['model']['arrays_path']
        self.pin(model_name,result['model']['arrays_sha256'])
        model_delta = inventory['model_comparison']
        return dict(label=label,stage=stage,result_file=result_name,result_sha256=self.bindings[result_name],
            model_file=model_name,model_sha256=self.bindings[model_name],task=task,
            N=n,targets_mm=targets,state_sha256=[s['state_sha256'] for s in result['states']],
            call_counts=result['call_counts'],accepted_history=len(result['path_diagnostics']['newton_history']),
            trials=len(result['path_diagnostics']['trials']),failed_attempts=result['path_diagnostics']['failed_attempts'],
            counts=result['counts'],model_comparison=model_delta,
            production=dict(helper_seconds=receipt['elapsed_seconds'],outer_seconds=production_launch['elapsed_seconds'],
                helper_RSS_bytes=receipt['sampled_peak_RSS_bytes'],tree_RSS_bytes=production_launch['peak_sampled_tree_RSS_bytes'],
                helper_limit_seconds=receipt['seconds_limit'],outer_limit_seconds=production_launch['outer_seconds']),
            reference=dict(helper_seconds=reference['elapsed_seconds'],outer_seconds=reference_launch['elapsed_seconds'],
                helper_RSS_bytes=reference['sampled_peak_RSS_bytes'],tree_RSS_bytes=reference_launch['peak_sampled_tree_RSS_bytes'],
                fresh_HP=reference['HP_calls_completed'],checks=reference['checks_completed'],
                contract_sha256=self.bindings[stage+'/reference_contract.json'],scope=reference['reference_scope']),
            peak=rows[peak_index],return_to_zero=rows[-1],loading_at_1_mm=matched[0],local_fit=fit,
            production_qualification_flags={k:result[k] for k in ('equilibrium_qualified','independent_HP_qualified','HF_qualified')})

    def saved_view(self, stage, report_name, phase='view'):
        protocol = self.read(stage+'/protocol.json')
        launch = self.read(stage+'/view_launch.json')
        report = self.read(stage+'/view/'+report_name)
        assert launch['status']==report['status']=='pass' and report['failure'] is None
        assert launch['exit_code']==0 and launch['all_bindings_unchanged'] is True and launch['stop_reason'] is None
        assert launch['protocol_sha256']==self.bindings[stage+'/protocol.json']
        assert launch['elapsed_seconds'] <= protocol['phases'][phase]['outer_seconds']
        assert report.get('new_F_T_model_solver_HP_calls',report.get('new_F_T_model_solver_HP_geometry_observation_calls'))==0
        for name,pin in report['outputs'].items(): self.pin(stage+'/view/'+name,pin)
        return dict(stage=stage,report_file=stage+'/view/'+report_name,report_sha256=self.bindings[stage+'/view/'+report_name],
            helper_seconds=report['elapsed_seconds'],outer_seconds=launch['elapsed_seconds'],
            helper_RSS_bytes=report['sampled_peak_RSS_bytes'],tree_RSS_bytes=launch['peak_sampled_tree_RSS_bytes'],
            geometry_completed=report.get('geometry_completed',0),nodal_completed=report.get('nodal_completed',0),
            output_pins=report['outputs'],source_input_pins=report['input_source_bindings'])

    def closed_x72(self):
        result = self.read(FAILED+'/run_001/result/result.json')
        receipt = self.read(FAILED+'/run_001/execution_receipt.json')
        protocol = self.read(FAILED+'/production_protocol.json')
        launch = self.read(FAILED+'/production_launch.json')
        assert result['status']=='failed' and result['failure']['code']=='invalid_J'
        assert receipt['status']==launch['status']=='not_pass' and result['accepted_states']==8
        assert result['path_completed'] is result['unload_endpoint_reached'] is False and result['call_counts']['HP_calls']==0
        assert launch['protocol_sha256']==self.bindings[FAILED+'/production_protocol.json']
        view = self.saved_view(FAILED_VIEW,'view.json')
        assert view['geometry_completed']==view['nodal_completed']==25
        return dict(stage=FAILED,status='closed_failed',accepted_states=8,failed_reason=result['failure'],
            last_accepted_input_mm=result['states'][-1]['d'],call_counts=result['call_counts'],
            helper_seconds=receipt['elapsed_seconds'],outer_seconds=launch['elapsed_seconds'],
            helper_RSS_bytes=receipt['sampled_peak_RSS_bytes'],tree_RSS_bytes=launch['peak_sampled_tree_RSS_bytes'],
            new_HP=0,whole_path_qualified=False,failed_predictor_J_location_known=False,pure_preview=view,
            scope='Saved accepted states and failure identity only; no failed-prefix reference or reexecution')


def fmt(value):
    return '未命中（null）' if value is None else f'{value:.10g}'


def table(cases, field, title):
    rows=['| 量 | x71 / side16 / E1 | x71 / side18 / E1 |','|---|---:|---:|']
    for name,key in field:
        rows.append('| '+name+' | '+' | '.join(fmt(cases[label][title][key]) for label in ('pose002','enlarged001'))+' |')
    return '\n'.join(rows)


def append_sections(data):
    c=data['cases']; new=c['enlarged001']; old=c['pose002']; fail=data['x72_closed_failure']
    metrics=[('输入反力 N','R_input_N'),('自由输出 +y mm','q_out_mm'),('下半工件总 Fx N','total_body_Fx_N'),
        ('下半工件总 Fy N','total_body_Fy_N'),('材料 Fx N','material_body_Fx_N'),('材料 Fy N','material_body_Fy_N'),
        ('Hu Fx N','regularization_body_Fx_N'),('Hu Fy N','regularization_body_Fy_N'),
        ('双侧法向幅值和 2|Fy| N','cached_two_sided_normal_magnitude_sum_N'),('钳尖有限底边距离 mm','tip_to_bottom_mm'),
        ('钳尖有限右边距离 mm','tip_to_right_mm'),('底面首次法向射线 mm','bottom_first_ray_mm'),
        ('第三介质 min J','medium_min_J'),('实体 min J','solid_min_J'),('实体全域最大平面 Green 主应变','solid_Green_principal_max')]
    peak_table=table(c,metrics,'peak'); matched_table=table(c,metrics,'loading_at_1_mm')
    resources=['| 阶段 | F/T 开始与完成；HP | helper / outer s | helper / tree RSS bytes |','|---|---|---:|---:|']
    for label,x in c.items():
        q=x['call_counts']; p=x['production']; r=x['reference']
        resources.append(f'| {label}生产 | F{q["force_calls"]}/{q["force_calls_completed"]}；T{q["tangent_calls"]}/{q["tangent_calls_completed"]}；HP0 | {p["helper_seconds"]:.8f}/{p["outer_seconds"]:.8f} | {p["helper_RSS_bytes"]}/{p["tree_RSS_bytes"]} |')
        resources.append(f'| {label}参考 | 0新F/T/模型/求解；{r["fresh_HP"]}新HP | {r["helper_seconds"]:.8f}/{r["outer_seconds"]:.8f} | {r["helper_RSS_bytes"]}/{r["tree_RSS_bytes"]} |')
    same_force=new['loading_at_1_mm']['total_body_Fy_N']; old_force=old['loading_at_1_mm']['total_body_Fy_N']
    fit=new['local_fit']; strain=fit['adjacent_solid_Green_principal_max']; prep=data['preparation']
    master=f'''\n\n## 2026-10-07：增大工件，检验受力与接触附近响应

本段接续既有记录。整体目标仍是独立 HF 读取普通 LF 几何，对显式、可比的物理任务计算力与变形，供既有 LF/N4 研究层使用；不在 HF 重做优化，不导入、安装或子进程调用 dmftd，不实施 MPM。整体项目尚未完成。

用户本次希望工件的有限接触面更靠右、尺寸稍大，以观察 TMC 在夹持器逼近工件后是否能稳定分析并报告夹持相关力。本次固定方体中心保持 (71,40) mm，边长从 16 改为 18 mm：相对合格 x71/side16，右面 x79→80、左面 x63→62、下表面 y32→31 mm。初始最右钳尖 (80,30) 已被有限底边 [62,80] 覆盖，初始底边距离 1 mm。本工况右侧第三介质余量为 0，是明确的边界触碰任务；原合格x71/side16的右侧余量为1 mm。162工件单元/190节点/380工件 DOF，19个背景对称 uy 重叠，448固定/6194自由；原 native 1 mm 网格、LF实体/支撑/端口、E=1 MPa、Et=20 N/mm、gamma/alpha=1e-6、Lr=80 mm 均保留，原21 intrinsic字段保持、只改6个覆盖字段。新执行包装只将目标断言1.8→1.2 mm，原数学、控制器、hooks、缓存、trace与门限不改；旧96bf包装保留。

前一步 x72/side16 的全路径已因 invalid_J 关闭：8个接受态，最后输入 {fail['last_accepted_input_mm']:.10g} mm；helper {fail['helper_seconds']:.8f} s、outer {fail['outer_seconds']:.8f} s，0 HP。7次失败是预测/约束投影之后首F拒绝，31次切线均完成；末次1.6875→1.703125 mm在原深度4上限停止。失败预测位移没有保存，不能把最后接受态的 cell2559 小J归为失败负J位置。其25态纯保存预览（17旧＋8失败接受态）通过，未给失败前缀补参考或完整资格。

本次新24目标从零细分加载至1.2 mm再卸载至零，生产3000/3060 s、准备120/150 s、8 GiB。准备实际helper {prep['helper_seconds']:.8f} s、outer {prep['outer_seconds']:.8f} s，一次模型构造、0F/T/求解/HP；实际生产接受 {new['N']} 态，全部原目标与新增二分态保留；独立参考新HP80/120共 {new['reference']['fresh_HP']} 次、{new['reference']['checks']}项通过。原生产qualification flags保持 false，另存完整独立参考结果；未回填旧记录。

下面分别列各工况自己的峰值：旧为1.8 mm，新为1.2 mm，不能用这张表归因尺寸变化，也不做同峰值力比。

{peak_table}

同输入1.0 mm的实际加载态对照如下，来自各自完整参考支持的保存接受态，不插值、不用卸载态替代。下半工件总Fy为 {old_force:.10g}→{same_force:.10g} N；这比较整个新工件任务的响应，不能单独分离位移工件有限面与增大尺寸的贡献。

{matched_table}

新峰态所选原生y={fit['source_reference_window']['y_mm']:.10g}、x={fit['source_reference_window']['x_mm']} mm候选边邻接实体最大Green主应变 {strain:.10g}；保留的x63–80窗口覆盖钳尖片段，不能代表新工件整个x62–80底边。此普通保存F派生值和全域最大应变的采样区域不同，未新增应力HP资格。有限边距离、首次法向射线与弱式节点力分别报告；小间隙不等于精确硬接触或压力。

{chr(10).join(resources)}

新返回零实际R={new['return_to_zero']['R_input_N']:.10g} N，qout={new['return_to_zero']['q_out_mm']:.10g} mm；极小量按存档原值保留。固定下半工件的on-body力为负的全局内力，holding反向；材料/Hu/总Fx/Fy见[阶段JSON](evidence/workpiece_enlarge_20261007/final_comparison.json)。2|Fy|是双侧法向幅值之和，镜像净力为(2Fx,0)，不能混称完整装配净夹持力。工件全ux/uy固定，外部holding承担反力；尚未证明自由刚体平移/旋转平衡、摩擦或稳定夹持。

![实际×1结构与返回零](../{VIEW}/view/comparison.png)

![局部实际边与应变、节点受力](../{FIT}/view/local_fit.png)

实际动画：[旧x71/side16共{old['N']}帧](../{VIEW}/view/pose002/actual_states.gif)、[新side18共{new['N']}帧](../{VIEW}/view/enlarged001/actual_states.gif)。各帧来自实际接受索引，原点与返回零未去重，没有插值。上半仅对称显示，未新增求解DOF。场色标与节点箭头按图的共同比例读；曲线按实际坐标刻度读。新保存view/fit均0新F/T/模型/求解/HP，view有{data['complete_view']['geometry_completed']}次几何及同数节点观察，fit复用保存结果。

下一步按这些已通过的实际位移、介质J和工件受力选择有限行程，随后处理圆体/自由工件、明确接触与释放定义、同设计网格/介质/正则参数收敛及HF5同任务研究层耦合。本段终态不把整个项目标为完成，也不外推任意工况、压力或所有切线列。main/origin与跨目录恢复仍按[恢复入口](RESUME_DEVELOPMENT.md)；文件身份核对和新数值重验是不同工作。
'''
    progress=f'''\n\n## 2026-10-07 新工件功能推进

已完成新的 side18、center(71,40)、固定下半工件从零→1.2→零任务：{new['N']}实际接受态、{new['reference']['fresh_HP']}次fresh HP、完整保存view与局部fit。增加尺寸使右面至x80、底边至y31，原结构与材料不变；工件位于分析域右边界，右侧介质余量为零。新24目标和旧11目标、峰值1.2/1.8 mm分开记录；实际加载1.0 mm用于比较。前一步x72/side16失败保留，不借其8态前缀资格。

现有功能可以计算受约束工件的三分量有符号受力和实际变形、夹持相关法向幅值；自由工件运动与稳定夹持、摩擦、精确接触压力、圆体的完整物理资格、收敛和HF5研究层耦合仍待完成。全过程与图、单位、范围、资源、原文件SHA见[工件主记录2026-10-07续篇](WORKPIECE_SHIFT_AND_SOFTNESS_20261004.md#2026-10-07增大工件检验受力与接触附近响应)及[阶段JSON](evidence/workpiece_enlarge_20261007/final_comparison.json)。
'''
    status=f'''\n\n## 2026-10-07 工件增大终态

新 side18/x71/E1 24目标0→1.2→0完整任务、全部{new['N']}接受态/{new['reference']['fresh_HP']}fresh HP和保存图已完成。旧x72/side16 invalid_J失败关闭保留；未重跑或借前缀。整体HF项目仍未完成，下一步以实际受力与介质压缩结果选择有限物理任务，并推进接触定义/圆体与自由工件/收敛及HF5耦合。[完整工作记录与图](WORKPIECE_SHIFT_AND_SOFTNESS_20261004.md)、[物理功能进度](HF_FUNCTION_PROGRESS_20261004.md)、[本阶段JSON及SHA](evidence/workpiece_enlarge_20261007/final_comparison.json)。
'''
    resume='''\n\n## 2026-10-07 继续开发上下文

继续开发前先读[工件主记录的2026-10-07续篇](WORKPIECE_SHIFT_AND_SOFTNESS_20261004.md)与[功能进度](HF_FUNCTION_PROGRESS_20261004.md)，再核对[新尺寸阶段JSON](evidence/workpiece_enlarge_20261007/final_comparison.json)和其输入SHA。新side18、x71任务为24目标/峰值1.2 mm，原合格side16为11目标/峰值1.8 mm；不要比较不同峰值作因果结论。x72/side16失败卡仍关闭，不重跑、不继承接受态前缀。工件全部固定、右边界余量零与力方向定义必须随新任务保留或显式改变。普通交付verify只证明文件身份；历史协议不是异目录原卡重跑授权。
'''
    return dict(zip(DOCUMENTS,(master,progress,status,resume)))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True,help='New directory for summary and append proposals')
    parser.add_argument('--baseline-docs',type=Path,default=Path(__file__).with_name('baseline_docs'))
    args=parser.parse_args(); root=args.repo.resolve(); output=args.output.resolve()
    assert not output.exists(), 'Use a new output identity; never overwrite saved records'
    baseline_docs=args.baseline_docs.resolve(); facts=SavedFacts(root)
    comparison={label:facts.completed_case(stage,label,targets,VIEW) for label,stage,targets in
        (('pose002',POSE,PREDECESSOR_TARGETS),('enlarged001',CASE,TARGETS))}
    new=comparison['enlarged001']
    assert new['task']['workpiece']==dict(kind='fixed_rigid',shape='square',center_mm=[71.,40.],side_mm=18.,fixed_components=[0,1])
    assert new['counts']['fixed_dofs']==448 and new['counts']['free_dofs']==6194
    assert new['model_comparison']['parameter_case']=='position_and_size_only'
    view=facts.saved_view(VIEW,'view.json'); fit=facts.saved_view(FIT,'fit_view.json')
    assert view['geometry_completed']==view['nodal_completed']==sum(x['N'] for x in comparison.values())
    for x in comparison.values():
        assert view['source_input_pins'][x['result_file']]==x['result_sha256']
        assert view['source_input_pins'][x['stage']+'/reference/summary.json']==facts.bindings[x['stage']+'/reference/summary.json']
    closed=facts.closed_x72()
    prep_receipt=facts.read(CASE+'/run_001/preparation_receipt.json')
    prep_protocol=facts.read(CASE+'/preparation_protocol.json')
    prep_launch=facts.read(CASE+'/prepare_launch.json')
    assert prep_receipt['status']==prep_launch['status']=='pass' and prep_launch['exit_code']==0
    assert prep_receipt['model_constructions']==1 and all(prep_receipt[k]==0 for k in ('force_calls','tangent_calls','solver_calls','HP_calls'))
    assert prep_launch['protocol_sha256']==facts.bindings[CASE+'/preparation_protocol.json']
    assert prep_launch['all_bindings_unchanged'] is prep_receipt['inputs_and_sources_unchanged'] is True
    assert prep_launch['elapsed_seconds']<=prep_protocol['phases']['prepare']['outer_seconds']
    preparation=dict(helper_seconds=prep_receipt['elapsed_seconds'],outer_seconds=prep_launch['elapsed_seconds'],
        helper_RSS_bytes=prep_receipt['sampled_peak_RSS_bytes'],tree_RSS_bytes=prep_launch['peak_sampled_tree_RSS_bytes'],
        helper_limit_seconds=prep_protocol['phases']['prepare']['helper_seconds'],outer_limit_seconds=prep_protocol['phases']['prepare']['outer_seconds'],
        receipt=prep_receipt,protocol_sha256=facts.bindings[CASE+'/preparation_protocol.json'])
    doc_records={}
    for name in DOCUMENTS:
        original=(baseline_docs/name).read_bytes(); current=(root/'docs'/name).read_bytes()
        assert current==original, 'Root applies append to exact b310 original; source document already changed: '+name
        doc_records[name]=dict(baseline_commit=BASELINE,original_sha256=sha256(original).hexdigest(),original_bytes=len(original))
    output.mkdir(parents=True)
    data=dict(schema_version='workpiece-enlarge-saved-final-summary-1.0',status='closed_saved_complete',client_date='2026-10-07',
        baseline_commit=BASELINE,whole_HF_project_complete=False,cases=comparison,x72_closed_failure=closed,
        complete_view=view,local_fit_view=fit,preparation=preparation,input_bindings=facts.bindings,baseline_documents=doc_records,
        interpretation=dict(new_vs_old_peaks_mm=[1.2,1.8],peak_causal_ratio_reported=False,matched_actual_loading_input_mm=1.,
            pressure_qualified=False,free_workpiece_clamp_qualified=False,two_sided_normal='2|Fy| scalar normal-magnitude sum',
            symmetric_net_force='(2Fx,0) vector; different from normal-magnitude sum'),
        collector=dict(sha256=sha(Path(__file__)),model_constructions=0,new_force=0,new_tangent=0,solver=0,HP=0,geometry_API=0,render=0,
            basis='stdlib JSON/SHA only; no hf_eval or numeric/plot imports'))
    write(output/'final_comparison.json',data)
    originals=output/'baseline_docs'; originals.mkdir()
    proposals=output/'append_proposals'; proposals.mkdir()
    for name,append in append_sections(data).items():
        original=(baseline_docs/name).read_bytes(); (originals/name).write_bytes(original)
        (proposals/name).write_bytes(original+append.encode('utf-8'))
        doc_records[name].update(proposal_sha256=sha(proposals/name),appended_bytes=len(append.encode('utf-8')),original_preserved_byte_exact=True)
    write(output/'append_proposals_record.json',dict(status='proposals_only_source_documents_untouched',documents=doc_records,
        input_bindings=facts.bindings,collector_sha256=sha(Path(__file__)),numerical_calls=0))
    assert all(sha(facts.path(name))==pin for name,pin in facts.bindings.items()), 'Saved input changed while collecting'
    print(json.dumps(dict(status='final_saved_facts_and_append_proposals_created',actual_new_N=new['N'],actual_fresh_HP=new['reference']['fresh_HP'],new_numerical_calls=0)))


if __name__=='__main__':
    main()
