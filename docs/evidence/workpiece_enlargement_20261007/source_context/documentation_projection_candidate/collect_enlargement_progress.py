"""Collect real saved progress, including failed and pending work, without mechanics.

This collector writes only a new output directory. It never imports hf_eval,
executes a protocol, creates a model, derives mechanics, or renders a figure.
"""
from pathlib import Path
from hashlib import sha256
import argparse
import json

NATIVE = 'lf_data_preparation/native_workpiece_001/'
TIP = NATIVE+'shift_square_tip_align_001'
ENLARGED = NATIVE+'enlarged_square_contact_001'
PROJECTION = NATIVE+'enlarged_square_projection_001'
POSE = NATIVE+'shift_square_pose_002'
VALIDATION = NATIVE+'port_projection_validation_001'
TIP_VIEW = 'functional_views/workpiece_tip_align_20261007/failed_preview_001'
ENLARGED_VIEW = 'functional_views/workpiece_enlarge_20261007/failed_preview_001'
sha = lambda path: sha256(path.read_bytes()).hexdigest()


class SavedRecords:
    def __init__(self, root):
        self.root, self.pins = root, {}

    def read(self, name):
        path = (self.root/name).resolve(); path.relative_to(self.root)
        if not path.is_file():
            return None
        self.pins[path.relative_to(self.root).as_posix()] = sha(path)
        return json.loads(path.read_text(encoding='utf-8'))

    def pin(self, name, expected):
        path = (self.root/name).resolve(); path.relative_to(self.root)
        assert sha(path)==expected, name
        self.pins[path.relative_to(self.root).as_posix()] = expected

    def case(self, stage):
        result_name = stage+'/run_001/result/result.json'
        result = self.read(result_name)
        receipt = self.read(stage+'/run_001/execution_receipt.json')
        protocol = self.read(stage+'/production_protocol.json')
        launch = self.read(stage+'/production_launch.json')
        task = self.read(stage+'/run_001/task.json')
        inventory = self.read(stage+'/run_001/input_inventory.json')
        if result is None:
            return dict(stage=stage,status='pending' if launch is None else launch['status'],
                accepted_states=None,whole_path_passed=False,reference_qualified=False,
                task=task,production_launch=launch,production_receipt=receipt,view=None,
                loading_peak=None,loading_at_0p5_mm=None)
        states = result['states']; n = len(states)
        assert result['accepted_states'] == n
        full = (result['status']=='success' and receipt is not None and receipt['status']=='pass'
            and launch is not None and launch['status']=='pass' and launch['exit_code']==0
            and launch['invocations']==1 and launch['all_bindings_unchanged'] is True and launch['stop_reason'] is None
            and protocol is not None and launch['protocol_sha256']==self.pins[stage+'/production_protocol.json']
            and receipt['result_sha256']==self.pins[result_name]
            and all(result.get(k) is True for k in ('path_completed','task_target_executed','loading_peak_reached','unload_endpoint_reached')))
        reference = self.read(stage+'/reference/summary.json')
        life = self.read(stage+'/reference/lifecycle.json')
        ref_launch = self.read(stage+'/reference_launch.json')
        ref_protocol=self.read(stage+'/reference_protocol.json'); self.read(stage+'/reference_contract.json')
        qualified = bool(full and reference and life and ref_launch
            and reference['status']==life['status']==ref_launch['status']=='pass'
            and ref_launch['exit_code']==0 and reference['result_sha256']==self.pins[result_name]
            and ref_launch['all_bindings_unchanged'] is True and ref_launch['stop_reason'] is None
            and ref_protocol and ref_launch['protocol_sha256']==self.pins[stage+'/reference_protocol.json']
            and reference['accepted_states']==life['accepted_states_completed']==n
            and reference['HP_calls_started']==reference['HP_calls_completed']==life['HP_calls_started']==life['HP_calls_completed']==2*n
            and [x['state_sha256'] for x in reference['states']]==[x['state_sha256'] for x in states])
        resources = None if not receipt or not launch else dict(
            helper_seconds=receipt.get('elapsed_seconds'),outer_seconds=launch.get('elapsed_seconds'),
            helper_RSS_bytes=receipt.get('sampled_peak_RSS_bytes'),tree_RSS_bytes=launch.get('peak_sampled_tree_RSS_bytes'),
            helper_limit_seconds=receipt.get('seconds_limit'),outer_limit_seconds=launch.get('outer_seconds'))
        def physical_row(index):
            s=states[index]; body=s.get('workpiece'); forces=None if body is None else body['force_on_lower_body_N']
            return dict(index=index,d_mm=s['d'],leg=s.get('leg'),state_sha256=s['state_sha256'],
                R_input_N=s['R_input'],q_out_mm=s['q_out'],
                total_body_Fy_N=None if forces is None else forces['total'][1],
                material_body_Fy_N=None if forces is None else forces['material'][1],
                regularization_body_Fy_N=None if forces is None else forces['regularization'][1],
                two_sided_normal_magnitude_sum_N=None if body is None else body['two_sided_normal_magnitude_sum_N'],
                reference_qualified=qualified,view_row=None)
        loading=[i for i,s in enumerate(states) if s.get('leg')=='loading']
        peak=None if not loading else physical_row(max(loading,key=lambda i:states[i]['d']))
        common=[i for i in loading if states[i]['d']==.5]
        assert len(common)<=1, 'Select actual loading state only; no interpolation or unloading substitute'
        return dict(stage=stage,status=result['status'],accepted_states=n,whole_path_passed=bool(full),
            result_file=result_name,result_sha256=self.pins[result_name],task=task,
            initial_guess=result.get('initial_guess','tangent'),targets_mm=result['targets_mm'],
            reached_displacement_mm=result['reached_displacement'],failure=result['failure'],
            path_completed=result.get('path_completed',False),loading_peak_reached=result.get('loading_peak_reached',False),
            unload_endpoint_reached=result.get('unload_endpoint_reached',False),call_counts=result['call_counts'],
            counts=result['counts'],model=result['model'],states=[dict(index=i,d_mm=s['d'],leg=s.get('leg'),
                state_sha256=s['state_sha256'],R_input_N=s['R_input'],q_out_mm=s['q_out'],
                workpiece=s.get('workpiece'),relative_residual=s['relative_residual'],minimum_J=s['minimum_J']) for i,s in enumerate(states)],
            failed_attempts=result['path_diagnostics']['failed_attempts'],
            Newton_history_records=len(result['path_diagnostics']['newton_history']),
            trial_records=len(result['path_diagnostics']['trials']),resources=resources,
            original_production_qualification_flags={k:result[k] for k in ('HF_qualified','independent_HP_qualified','equilibrium_qualified')},
            model_comparison=None if inventory is None else inventory.get('model_comparison'),
            loading_peak=peak,loading_at_0p5_mm=None if not common else physical_row(common[0]),
            reference_qualified=qualified,reference=reference,reference_lifecycle=life,reference_launch=ref_launch,
            reference_scope='All accepted N fresh HP80/120 only when full production and matching2N proofs pass; no pressure/free-clamp qualification.',
            view=None,production_launch=launch,production_receipt=receipt,
            production_limits=None if protocol is None else protocol['phases']['production'])

    def attach_view(self, case, stage, label):
        if not stage:
            return
        report = self.read(stage+'/view/view.json')
        launch = self.read(stage+'/view_launch.json')
        protocol = self.read(stage+'/protocol.json')
        summary = self.read(stage+'/view/'+label+'/summary.json')
        if not (report and launch and summary):
            case['view'] = dict(stage=stage,label=label,status='pending')
            return
        if not (report['status']==launch['status']=='pass' and launch['exit_code']==0):
            case['view'] = dict(stage=stage,label=label,status=report['status'],failure=report.get('failure'),launch=launch)
            return
        assert launch['all_bindings_unchanged'] is True and launch['protocol_sha256']==self.pins[stage+'/protocol.json']
        assert report['input_source_bindings'][case['result_file']]==case['result_sha256']
        assert summary['accepted_states']==len(summary['rows'])==case['accepted_states']
        assert [s['state_sha256'] for s in summary['rows']]==[s['state_sha256'] for s in case['states']]
        case['view'] = dict(stage=stage,label=label,status='pass',rows=summary['rows'],
            last=summary['rows'][-1] if summary['rows'] else None,
            helper_seconds=report['elapsed_seconds'],outer_seconds=launch['elapsed_seconds'],
            geometry_completed=report['geometry_completed'],nodal_completed=report['nodal_completed'],
            new_F_T_model_solver_HP_calls=report['new_F_T_model_solver_HP_calls'],
            reference_available=summary['reference_available'],output_pins=report['outputs'],
            comparison_png=stage+'/view/comparison.png',fields_png=stage+'/view/peak_fields.png',
            distances_png=stage+'/view/distances_forces.png',gif=stage+'/view/'+label+'/actual_states.gif')
        assert case['view']['new_F_T_model_solver_HP_calls']==0
        if not case['whole_path_passed']:
            assert summary['reference_available'] is False
        for key in ('loading_peak','loading_at_0p5_mm'):
            metric=case[key]
            if metric is not None:
                row=summary['rows'][metric['index']]
                assert row['state_sha256']==metric['state_sha256'] and row['leg']=='loading' and row['d_mm']==metric['d_mm']
                metric['view_row']=row

    def validation(self):
        protocol = self.read(VALIDATION+'/protocol.json')
        launch = self.read(VALIDATION+'/validation_launch.json')
        receipt = self.read(VALIDATION+'/result/receipt.json')
        passed = bool(protocol and launch and receipt and launch['status']==receipt['status']=='pass'
            and launch['exit_code']==0 and receipt.get('tests_passed')==protocol['expected_tests']==15
            and launch['all_bindings_unchanged'] is True and receipt['all_bindings_unchanged'] is True
            and launch['protocol_sha256']==self.pins[VALIDATION+'/protocol.json']
            and all(receipt.get(k)==0 for k in ('tests_failed','tests_errors','tests_skipped')))
        status='pass' if passed else 'pending' if launch is None else 'not_qualified' if launch['status']=='pass' else launch['status']
        return dict(stage=VALIDATION,status=status,
            expected_tests=15,passed=passed,launch=launch,receipt=receipt,
            scope='Controller/default regression, independent cubic/dense KKT, and16-element native API tests; no workpiece contact or whole-path qualification.')


def number(value):
    return '待执行/未保存' if value is None else f'{value:.10g}'


def case_row(title, case):
    last = case.get('view',{}).get('last') if case.get('view') else None
    forces = None if not case.get('states') else case['states'][-1].get('workpiece')
    fy = None if not forces else forces['force_on_lower_body_N']['total'][1]
    return '| '+title+' | '+case['status']+' | '+str(case['accepted_states'])+' | '+number(case.get('reached_displacement_mm'))+' | '+number(fy)+' | '+number(None if not last else last['tip_to_bottom_mm'])+' | '+number(None if not last else last['medium_min_J'])+' |'


def physical_table(cases, field):
    lines=['| 工况 | 实际加载d mm | 输入R N | 输出qout mm | 单侧总Fy N | 材料Fy N | Hu Fy N | 双侧法向幅值和 N | 有限底边距 mm | 介质minJ | 全固体最大Green主应变 |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for title,case in cases:
        row=case[field]
        if row is None:
            lines.append('| '+title+' | 尚无实际该加载态 | — | — | — | — | — | — | — | — | — |')
            continue
        view=row['view_row']
        values=[row[k] for k in ('d_mm','R_input_N','q_out_mm','total_body_Fy_N','material_body_Fy_N','regularization_body_Fy_N','two_sided_normal_magnitude_sum_N')]
        values += [None if view is None else view[k] for k in ('tip_to_bottom_mm','medium_min_J','solid_Green_principal_max')]
        lines.append('| '+title+' | '+' | '.join(number(x) for x in values)+' |')
    return '\n'.join(lines)


def document(data):
    tip,old,new = (data['cases'][k] for k in ('x72_failed','side18_tangent','side18_projection'))
    validation=data['validation']
    peak_table=physical_table([('旧合格x71/side16/E1',data['cases']['pose_E1']),('side18/tangent（失败）',old),('side18/port_projection',new)],'loading_peak')
    common_table=physical_table([('旧合格x71/side16/E1',data['cases']['pose_E1']),('side18/tangent（失败前生产态）',old),('side18/port_projection',new)],'loading_at_0p5_mm')
    table='\n'.join(['| 工况 | 实际状态 | 接受态数 | 最后输入 mm | 下半工件 Fy N | 钳尖有限底边距离 mm | 介质 min J |',
        '|---|---|---:|---:|---:|---:|---:|',case_row('x72 / side16 / tangent',tip),
        case_row('x71 / side18 / tangent',old),case_row('x71 / side18 / port_projection',new)])
    if new['whole_path_passed']:
        outcome=f"新初猜实际完整加载—卸载通过，共{new['accepted_states']}个接受态。"
        outcome+=f"全部状态新鲜HP80/120参考通过，共{new['reference']['HP_calls_completed']}次。" if new['reference_qualified'] else '独立全部状态HP参考尚未通过或未执行，不能写作独立HF资格。'
    elif new['status']=='pending':
        outcome='新初猜完整工况尚待正式执行；没有新完整路径、HP或接触资格。'
    else:
        outcome=f"新初猜实际状态为{new['status']}，完整路径未通过；仅保留真实已接受状态，未给失败前缀完整参考资格。"
    view=old.get('view'); new_view=new.get('view')
    visuals='' if not view or view.get('status')!='pass' else f"\n![扩大工件的实际接受态](../{view['comparison_png']})\n\n[扩大工件的{old['accepted_states']}帧实际动画](../{view['gif']})；失败之后没有外推帧或卸载动画。\n"
    if new_view and new_view.get('status')=='pass':
        visuals+=f"\n![新初猜的实际状态](../{new_view['comparison_png']})\n\n[新初猜实际{new['accepted_states']}帧](../{new_view['gif']})。\n"
    fit=data.get('projection_fit')
    if fit and fit['status']=='pass':
        visuals+=f"\n![新初猜局部保存观察](../{fit['png']})\n"
    return f'''# 工件右移、增大与接触附近分析：2026-10-07

扩大工件后，默认初猜到输入0.86875 mm附近仍触发原positive-J守卫，未完成1.2 mm加载与卸载。{outcome}

整体目标是独立HF读取普通LF几何，计算明确物理任务的非线性力、变形与工件受力，再供现有LF/N4研究层使用。现有优化研究层保留，不在HF重做LF优化、不调用dmftd、不实施MPM。整个HF项目尚未完成。此前x71/side16/E1的完整17态及34次参考已通过；本记录不能覆盖或替换那项资格。

用户希望有限工件面更靠右、物体稍大，以检验逼近接触后TMC分析和夹持相关力。新方形工件中心(71,40) mm、边长18 mm，半模型覆盖[62,80]×[31,40]；相对合格side16，右面79→80、底面32→31 mm。原最右钳尖(80,30)在初始几何中与有限底边相隔1 mm。新工件右面到域边界，没有右侧包围介质；原合格x71/side16则有1 mm右侧介质余量。保留native1 mm网格、LF结构/端口/支撑、E=1 MPa、ν=.3、厚度20 mm、γ=α=10⁻⁶及Lr=80 mm。162工件单元/190节点/380工件DOFs，19个顶部uy重叠，448固定/6194自由；21内部字段不变，仅6覆盖字段改变。此次保留E1以识别位置和尺寸作用；此前均匀软化未自动改善钳尖贴合。

这两个默认初猜工况都真实失败并关闭，没有重试原卡：x72/side16最后输入1.6875 mm，7次首预测F拒绝、31次T全部完成；增大side18最后输入0.86875 mm，4次首预测F拒绝、30次T全部完成。均未到目标峰值与卸载终点，0HP。二者失败均为invalid_J，不是已保存接受态的负J；失败预测位移没有保存，不能把接受态最小J单元当作失败负J位置。side18末次0.86875→0.875 mm因原最小增量规则停止。接受态与真实部分可视化均保留。

{table}

上表显示终态，完整卸载返回零后Fy接近零，并不能展示夹持阶段受力。下面另列**最大已接受加载位移处**的物理读数：旧合格side16为1.8 mm，新任务目标为1.2 mm；失败工况只到自己的实际最后加载态。这些不同位移不用于尺寸因果力比，也不假设该态恰是全路径最大Fy。

{peak_table}

共同原始加载0.5 mm态的实际对照如下，不插值、不用同位移卸载态替代。旧合格基线有原同路径参考；默认side18失败卡该态仍为生产读数，不能继承完整资格。新模式的参考资格取实际终端证据。

{common_table}

表中失败工况的数值是最后实际接受状态，属于生产与保存观察；没有完整独立参考，不能称为成功夹持。不同峰值/最后输入不用于尺寸因果力比。下半固定工件的力是负的固定DOF内力，holding反向；总力=材料+Hu。2|Fy|是两侧法向力大小之和，镜像净力为(2Fx,0)，不是同一物理量。节点弱式力不等于点接触压力；正J下介质压缩、小间隙也不是精确硬接触或自由物体稳定夹持的证明。

下一项功能改变只选择初猜：仍真实求解原KKT预测LU、保留R+=dR；可选port_projection丢弃预测dw，将完整平均约束残差按b_free/(b_free·b_free)分配到自由输入端口旧fluctuation，再用原feasible修正舍入。非端口旧fluctuation和固定零值保留，后续原Newton仍允许输入节点各自运动，未改成刚性绑节点。原方程、材料/F/T、缓存、Armijo、J、回滚、二分和收敛门不改；默认tangent保留原行为。预测LU记录displacement_mode、applied_dw=false、applied_dR=true，只检验真实线性解；初猜是否平衡由原下一次F/T判断。

15项独立功能验证实际状态：**{validation['status']}**。范围为原9项控制器、2项native回归，加4项新测试：cubic1000且不二分的独立brentq平衡；非零lift/非对称KKT与秩一弹簧加载—卸载；默认数组位/轨迹与J门；原16单元native API转发。默认失效是测试内预期断言，不是正式卡重试。测试通过也不能替代新工件的真实完整计算。

新物理卡路径为`{new['stage']}`，保持同一side18/E1与24个原目标0→1.2→0，从零开始，实际状态与资源见[阶段JSON](evidence/workpiece_enlargement_20261007/progress.json)。若生产再次失败，记录部分结果并停止，不给失败前缀补whole-path资格；只有完整成功后，才对每个实际N态执行新鲜2N次80/120位HP，再做完整保存视图。新N、HP次数和图只取实际文件，不猜测或借前态。
{visuals}
人工查看顺序：实际×1结构与工件有限面位置 → 每个真实索引的动画 → 输入反力与工件总/材料/Hu力 → 钳尖有限边距离及首次法向射线 → 实体应变与介质J。上半仅镜像显示，不新增求解DOF。全域与局部应变采样区不同；原局部x63–80尖端窗口不能代表新工件整个x62–80底边。色标和力箭头按图共有标尺，曲线按各自坐标刻度读。

当前可实现独立NumPy完整力分量、组装/切线、平均位移控制、保存真实变形与约束工件受力。尚需完成接触附近稳定全周期的资格、圆体与自由工件运动/释放、摩擦、接触压力、同设计网格与介质/正则参数收敛，以及HF5与既有研究层的同任务耦合。后续按实际功能结果逐步选取行程和参数；整体项目仍未完成。
'''


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True,help='Absent external proposal directory')
    parser.add_argument('--projection-view',help='Actual root-relative view stage, complete or partial')
    parser.add_argument('--projection-label',default='projection001')
    parser.add_argument('--projection-fit',help='Actual root-relative passed cached-fit stage')
    args=parser.parse_args();root=args.repo.resolve();out=args.output.resolve()
    assert not out.exists(), 'Use a new output directory; saved records are never overwritten'
    records=SavedRecords(root)
    cases=dict(pose_E1=records.case(POSE),x72_failed=records.case(TIP),side18_tangent=records.case(ENLARGED),side18_projection=records.case(PROJECTION))
    records.attach_view(cases['pose_E1'],ENLARGED_VIEW,'pose_E1')
    records.attach_view(cases['x72_failed'],TIP_VIEW,'tip_failed')
    records.attach_view(cases['side18_tangent'],ENLARGED_VIEW,'enlarged_failed')
    if args.projection_view and cases['side18_projection'].get('result_file'):
        records.attach_view(cases['side18_projection'],args.projection_view,args.projection_label)
    fit=None
    if args.projection_fit:
        report=records.read(args.projection_fit+'/view/fit_view.json')
        launch=records.read(args.projection_fit+'/view_launch.json')
        protocol=records.read(args.projection_fit+'/protocol.json')
        if report and launch and report['status']==launch['status']=='pass':
            assert cases['side18_projection']['whole_path_passed'] and cases['side18_projection']['reference_qualified']
            new=cases['side18_projection']
            assert launch['exit_code']==0 and launch['invocations']==1 and launch['all_bindings_unchanged'] is True and launch['stop_reason'] is None
            assert protocol and launch['protocol_sha256']==records.pins[args.projection_fit+'/protocol.json']
            assert report['input_source_bindings'].get(new['result_file'])==new['result_sha256']
            assert report['new_F_T_model_solver_HP_geometry_observation_calls']==0
            for name,pin in report['input_source_bindings'].items(): records.pin(name,pin)
            for name,pin in report['outputs'].items(): records.pin(args.projection_fit+'/view/'+name,pin)
            fit=dict(stage=args.projection_fit,status='pass',png=args.projection_fit+'/view/local_fit.png',
                new_mechanics_and_geometry_calls=report['new_F_T_model_solver_HP_geometry_observation_calls'],
                input_source_pins=report['input_source_bindings'],output_pins=report['outputs'])
    validation=records.validation()
    sources={name:sha(root/'hf_repo/src/hf_eval'/name) for name in ('split_displacement.py','native_mean.py','split_numpy_tangent.py')}
    data=dict(schema_version='workpiece-enlargement-progress-1.0',client_date='2026-10-07',
        whole_HF_project_complete=False,cases=cases,validation=validation,projection_fit=fit,
        current_source_sha256=sources,input_bindings=records.pins,pressure_qualified=False,free_workpiece_clamp_qualified=False,
        collector=dict(source_sha256=sha(Path(__file__)),model_constructions=0,F=0,T=0,solver=0,HP=0,geometry_API=0,render=0))
    out.mkdir(parents=True)
    (out/'progress.json').write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    (out/'WORKPIECE_ENLARGEMENT_20261007.md').write_text(document(data),encoding='utf-8')
    assert all(sha(root/name)==pin for name,pin in records.pins.items())
    print(json.dumps(dict(status='saved_progress_proposals_only',projection_status=cases['side18_projection']['status'],
        whole_path_passed=cases['side18_projection']['whole_path_passed'],reference_qualified=cases['side18_projection']['reference_qualified'],new_numerical_calls=0)))


if __name__=='__main__':
    main()
