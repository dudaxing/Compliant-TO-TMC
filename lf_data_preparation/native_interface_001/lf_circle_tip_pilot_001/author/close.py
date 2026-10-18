"""Close the actual circle pilot from ordinary records; never reopen payloads."""
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
STAGE = 'lf_data_preparation/native_interface_001/lf_circle_tip_pilot_001'
BASE = '036fd5d9298525894b5f90a37dab8f258d6cc9b1'
CARD = 'L-CTIPPILOT1'
FRONTS = ['README.md', 'hf_repo/README.md', 'docs/CURRENT_STATUS.md',
    'docs/PHYSICAL_FUNCTION_PROGRESS.md', 'docs/RESUME_DEVELOPMENT.md',
    'docs/L_USE1_NEXT_STEP_PLAN.md', 'docs/L_BFWD1_NEXT_STEP_PLAN.md']


def read(name, *, optional=False):
    path = ROOT / STAGE / name
    return None if optional and not path.is_file() else json.loads(path.read_bytes())


def write(name, value):
    (ROOT / STAGE / name).write_text(value.rstrip()+'\n', encoding='utf-8', newline='\n')


def shown(value):
    return '未提供' if value is None else str(value)


def main():
    launch = read('pilot_launch.json')
    receipt = read('run_001/execution_receipt.json', optional=True)
    result = read('run_001/wave_circle_tip_pilot/result.json', optional=True)
    response = read('run_001/wave_circle_tip_pilot/response.json', optional=True)
    summary = read('run_001/view/wave_circle_tip_pilot/summary.json', optional=True)
    view = read('run_001/view/view.json', optional=True)
    convergence = read('run_001/convergence/convergence.json', optional=True)
    protocol, task = read('protocol.json'), read('pilot_task.json')
    review = read('author/ACTUAL_REVIEW.json')
    pixel = read('author/pixel_QA.json', optional=True)
    assert launch['card'] == protocol['card'] == CARD
    assert receipt is None or receipt['card'] == CARD
    assert pixel is None or pixel['card'] == CARD
    assert review['status'].startswith('pass') and not review.get('blockers', review.get('blocking_findings', []))
    assert launch['status'] in ('pass', 'not_pass')
    assert launch['invocations']==1 and launch['cleanup_verified'] is True
    assert receipt is None or receipt['status'] in ('pass', 'not_pass')
    assert receipt is None or receipt['protocol_sha256'] == launch['protocol_sha256']
    assert task['workpiece'] == dict(kind='fixed_rigid', shape='circle', center_mm=[80., 40.],
        radius_mm=9., fixed_components=[0, 1])
    assert task['path'] == dict(kind='load_only', targets_mm=[0., .25, .5])
    assert task['input']['target_mm'] == .5
    helper = receipt or {}
    outcome = 'pass' if launch['status'] == helper.get('status') == 'pass' else 'not_pass'
    states = result.get('states') if result is not None else None
    saved_count = len(states) if states is not None else None
    observed = {row['index']: row for row in summary['rows']} if summary is not None else {}
    rows = []
    for index, state in enumerate(states or []):
        observation = observed.get(index)
        if observation is not None:
            assert (observation['state_sha256'], observation['d_mm'], observation['leg'],
                observation['original_target_index']) == (state['state_sha256'], state['d'],
                state['leg'], state['original_target_index'])
            assert observation['R_input_N'] == state['R_input'] and observation['q_out_mm'] == state['q_out']
        rows.append(dict(index=index, state_sha256=state['state_sha256'], leg=state.get('leg'),
            original_target_index=state.get('original_target_index'), is_original_target=state.get('is_original_target'),
            d_mm=state['d'], R_input_N=state['R_input'], q_out_mm=state['q_out'],
            workpiece=state.get('workpiece'), minimum_J=state.get('minimum_J'),
            relative_residual=state.get('relative_residual'),
            relative_global_force_balance=state.get('relative_global_force_balance'),
            constraint_residual_mm=state.get('constraint_residual'), constraint_bound_mm=state.get('constraint_bound'),
            view_observation=observation))
    last = rows[-1] if rows else None
    last_observation = last['view_observation'] if last is not None else None
    production_status = result.get('status') if result is not None else None
    cached = helper.get('cached_production_gates')
    if outcome == 'pass':
        assert production_status == 'success' and cached is not None and cached['passed'] is True
        assert result['path_completed'] is True and result['reached_displacement'] == .5
        assert pixel is not None and pixel['status'].startswith('pass') and pixel['inspections']==5
    pixel_link='[像素记录](author/pixel_QA.json)' if (ROOT/STAGE/'author/pixel_QA.json').is_file() else '未提供像素记录'
    right_medium=summary.get('right_medium') if summary is not None else None
    outputs = helper.get('outputs')
    for name,row in (outputs or {}).items():assert (ROOT/name).stat().st_size==row['bytes'],name
    media = {}
    for name in ('view/comparison.png', 'view/distances_forces.png', 'view/peak_fields.png',
                 'view/wave_circle_tip_pilot/actual_states.gif', 'view/right_medium.png', 'convergence/convergence.png'):
        relative = STAGE + '/run_001/' + name
        if relative in (outputs or {}):
            assert (ROOT / relative).stat().st_size == outputs[relative]['bytes']
            media[name] = outputs[relative]
    if outcome=='pass':
        expected_pngs={STAGE+'/run_001/'+name for name in ('view/comparison.png','view/distances_forces.png','view/peak_fields.png','view/right_medium.png','convergence/convergence.png')}
        assert expected_pngs.issubset(outputs)
        assert {row['path'] for row in pixel['media']}==expected_pngs and len(pixel['media'])==5
        assert all(row['inspections']==1 for row in pixel['media'])
    counts = result.get('call_counts') if result is not None else helper.get('production_call_counts')
    path_flags = {key: result.get(key) for key in ('path_kind', 'targets_mm', 'reached_displacement',
        'path_completed', 'loading_peak_reached', 'task_target_executed', 'unload_endpoint_reached')} if result is not None else None
    terminal = review.get('terminal', {}).get('tool_terminal_as_reported_by_parent')
    if outcome != 'pass':
        next_step = ('先处理实际停止阶段；若生产已成功而显示未完成，只安排保存态显示问题诊断，'
            '不得重写原API成功或重做已完成求解。没有自动重试、修复重跑或新窗口。')
    elif (last_observation is not None and (last_observation.get('boundary_intersects') is True
            or last_observation.get('boundary_roundoff_near_touch') is True
            or last_observation.get('raw_overlap') is True or last_observation.get('roundoff_ambiguous') is True)):
        next_step = ('先核查已保存的边界相交、单元重叠或数值不确定观察，再决定是否安排下一目标；'
            '不把无符号距离或非零工件合力单独认定为接触。')
    else:
        next_step = ('依据本次末态真实距离、接近位置、分区J及收敛成本，提出只增加一个加载目标的后续方案；'
            '新目标、模式、受支持续算方式及预算另行明确；本卡不授完整路径，也不自动移植旧布置上限。')
    decision=read('author/NEXT_DECISION.json',optional=True)
    if decision is not None:
        assert decision['execution_status']==outcome
        next_step=decision['next_step']
    closure = dict(right_medium=right_medium,next_decision=decision,card=CARD, status=outcome + '_closed', execution_status=outcome, execution_closed=True,
        created_utc=datetime.now(timezone.utc).isoformat(), source_baseline_commit=BASE,
        science_version='0.5.0', science_baseline_commit='b1334bb6a83ba9a0efab7bdba7bd39722146f024',
        protocol_sha256=launch['protocol_sha256'], terminal=terminal,
        helper_status=helper.get('status'), outer_status=launch['status'], production_status=production_status,
        helper_phase=helper.get('phase'), helper_error=helper.get('error'), outer_stop_reason=launch.get('stop_reason'),
        saved_accepted_states=saved_count, saved_count_basis='len(result.states), or null if result is absent',
        helper_on_accept_count=helper.get('accepted_states'),
        helper_count_basis='Observer callback counter; separate from persisted accepted-state count',
        path_flags=path_flags, original_gates=protocol['gates'], cached_production_gates=cached,
        production_call_counts=counts, wrapper_call_counts=helper.get('call_counts'),
        last_saved_state=last, rows=rows,
        convergence_counts=convergence.get('counts') if convergence is not None else None,
        view_status=view.get('status') if view is not None else None,
        view_actual_counts=helper.get('view_actual_counts'),
        new_tests=helper.get('new_tests'), default_installations=helper.get('default_installations'),
        HP_calls_by_wrapper=helper.get('HP_calls_by_wrapper'),
        independent_reference=response.get('independent_reference') if response is not None else None,
        producer_flags=response.get('producer_flags') if response is not None else None,
        helper_elapsed_seconds=helper.get('elapsed_seconds'), outer_elapsed_seconds=launch.get('elapsed_seconds'),
        peak_sampled_tree_RSS_bytes=launch.get('peak_sampled_tree_RSS_bytes'),
        cleanup_verified=launch.get('cleanup_verified'),
        sealed_output_files=len(outputs) if outputs is not None else None,
        sealed_output_bytes=sum(row['bytes'] for row in outputs.values()) if outputs is not None else None,
        output_identity_seal=helper.get('output_identity_seal'),
        actual_review_status=review['status'], pixel_QA_status=pixel.get('status') if pixel is not None else None,
        pixel_QA_observations=pixel.get('observations') if pixel is not None else None,
        available_sealed_visualizations=media, next_step=next_step,
        qualification_scope='Circle short loading only; no full cycle, fresh HP, pressure, effective clamp, unloading, release, stability, manufacturing or HF5 qualification',
        closure_read_scope='Ordinary records and producer output seals/stat only; no scientific/media payload read, hash, decode, rendering, tests or mechanics')

    lines = [f'# {CARD}：圆形固定工件实际短加载', '',
        f"执行状态 **{outcome.upper()}**；生产 `{shown(production_status)}`、helper `{shown(helper.get('status'))}`、outer `{launch['status']}`，停止阶段 `{shown(helper.get('phase'))}`。基线 main `{BASE}`；science 0.5.0／b1334 基线保持。", '',
        '目标是让已准备的 wave LF 结构，在固定圆形工件下从零完成0→0.25→0.50 mm并显示实际变形、反力和收敛。该步检验圆形构模进入真实非线性/TMC工作流的能力。', '',
        '工件半径9 mm、中心(80,40) mm、固定ux/uy；其余E=1 MPa、nu=0.3、plane strain、厚20 mm、h=0.5 mm、92×40 mm下半域、gamma=1e-6、alpha=5e-7、Lr=80 mm及支撑/平均端口/对称保持。仅更新四个任务说明字段；prepared父任务已经是input.target0.50/load_only三目标，路径及物理原值保持，全部旧结果不改。', '',
        f"保存接受态数 `{shown(saved_count)}`；helper接受回调数 `{shown(helper.get('accepted_states'))}`，两者分别记录，缺失保存结果不写成零。路径原标志：`{shown(path_flags)}`。", '',
        '|接受行|原目标|路段|d mm|输入R N|q_out mm|下半体Fy N|Q1边界距离 mm|solid minJ|free-medium minJ|relative residual|',
        '|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for row in rows:
        observation = row['view_observation'] or {}
        force = (row.get('workpiece') or {}).get('force_on_lower_body_N', {}).get('total')
        values = [row['index'], row['original_target_index'], row['leg'], row['d_mm'],
            row['R_input_N'], row['q_out_mm'], force[1] if force is not None else None,
            observation.get('minimum_boundary_distance_mm'), observation.get('solid_min_J'),
            observation.get('medium_min_J'), row['relative_residual']]
        lines.append('|' + '|'.join(shown(value) for value in values) + '|')
    lines += ['', '数值保持原保存值；完整材料/Hu/总Fx/Fy、状态SHA、约束残差/原界、整体平衡和观测原值见闭卡JSON及原结果。q_out是加权端口位移，不是表面间隙；输入R和工件力保持下半模型含义。', '',
        f"原生产门 `{protocol['gates']}`；缓存门实录 `{shown(cached)}`。生产F/T等计数 `{shown(counts)}`；wrapper API/solve/view调用 `{shown(helper.get('call_counts'))}`。原门未更改。", '',
        f"收敛原记录计数 `{shown(closure['convergence_counts'])}`。回溯或二分若存在，属于原控制器工作，全部实际接受态保留；不会锁定仅三态。新测试 `{shown(helper.get('new_tests'))}`、默认安装 `{shown(helper.get('default_installations'))}`、wrapper新HP `{shown(helper.get('HP_calls_by_wrapper'))}`。", '',
        '实际距离使用所选圆形Q1单元的物理外露阶梯边，排除对称切口；解析圆只作图示参考。无符号距离不等于有符号间隙。通用凸Q1跨区域单元重叠是另一项观察，完整包含关系及机构自重叠仍未检查；False、None与数值不确定状态分别保留。', '',
        f"最右尖端按唯一参考坐标(80,30)查找后跟随实际位移，不硬码节点编号；初始tip和整体最近均1mm，但不代表唯一首触。右侧介质完整逐态极值、位置与约束如已完成显示，见末尾对应摘要入口。条带按实际参考body右端与域界动态定位为x89..92、6列480cells；相接body节点仍固定，原顶uy对称保持。条带实际坐标/J/Hu只为保存态观察，不是域宽收敛。末态几何与分区场原值见闭卡JSON的last_saved_state/view_observation。若显示未完成或该项未提供，不能据缺失值判断无接触、无重叠或场稳定。", '',
        '圆周局部法向随位置变化；下半工件全局Fx/Fy是含材料和Hu的有符号弱式合力，不是连续压力或圆周总法向夹持力。坐标×1，完整结构图和GIF仅作对称镜像，数值没有镜像加倍；节点箭头包含切口/内部节点，不能当作表面压力。', '',
        f"实际独立审阅 `{review['status']}`；像素检查 `{shown(closure['pixel_QA_status'])}`；逐图观察：{pixel_link}；若未完成则按缺失记录保留。没有新增重绘或媒体重解码。", '']
    lines += ['| d mm | 同tip距离 mm | 最近距离 mm | 右介质minJ | 右介质maxabsHu 1/mm | 右条带max节点位移 mm |',
              '|---:|---:|---:|---:|---:|---:|']
    for row in rows:
        observed=row['view_observation'] or {}
        lines.append('|'+ '|'.join(shown(value) for value in [row['d_mm']]+[observed.get(key) for key in ('tip_to_raster_boundary_mm','minimum_boundary_distance_mm','right_medium_min_J','right_medium_max_abs_Hu_per_mm','right_medium_max_nodal_displacement_mm')])+'|')
    if decision is not None and 'interpretation_md' in decision:lines+=['',decision['interpretation_md'],'']
    for name in media:
        lines += [f'![{name}](run_001/{name})', '']
    lines += [f"helper `{shown(helper.get('elapsed_seconds'))}` s／2700 s，outer `{shown(launch.get('elapsed_seconds'))}` s／2760 s；controller 1800 s，viewer＋收敛＋人工页共享600 s；进程树采样峰值 `{shown(launch.get('peak_sampled_tree_RSS_bytes'))}` B／64 GiB，清理 `{shown(launch.get('cleanup_verified'))}`。终端 `{shown(terminal)}`。原窗口封存 {shown(closure['sealed_output_files'])} 个输出、{shown(closure['sealed_output_bytes'])} B，状态 `{shown(helper.get('output_identity_seal'))}`；闭卡继承producer seal＋stat，不重读载荷。", '',
        f"真实错误：helper `{shown(helper.get('error'))}`；API `{shown(helper.get('API_failure'))}`；outer `{shown(launch.get('error'))}`。生产成功与显示阶段失败分别报告，不回写原API或原结果。", '',
        '本轮不取得独立HP、压力、有效夹持、完整加载卸载循环、卸载/自由释放、稳定性或HF5资格；制造仍pending。', '',
        '下一步：' + next_step, '',
        '审查入口：'+' · '.join('['+label+']('+path+')' for label,path in [('原响应','run_001/wave_circle_tip_pilot/response.json'),('原结果','run_001/wave_circle_tip_pilot/result.json'),('人工页','run_001/REVIEW.md'),('显示摘要','run_001/view/wave_circle_tip_pilot/summary.json'),('收敛JSON','run_001/convergence/convergence.json'),('helper','run_001/execution_receipt.json'),('outer','pilot_launch.json'),('实际审阅','author/ACTUAL_REVIEW.md'),('闭卡JSON','author/closure.json')] if path=='author/closure.json' or (ROOT/STAGE/path).is_file()), '']
    next_text = '\n'.join(['# L-CTIPPILOT1 后续', '',
        f"实际执行 `{outcome}`；生产 `{shown(production_status)}`；保存态 `{shown(saved_count)}`。", '', next_step, '',
        '下一阶段必须依据本次保存的几何、原分区J、残差、回溯和成本明确物理目标与资源；本页不授权新运行。不例行补HP，不把旧方体或旧同值状态的参考转授给这条圆形路径。', '',
        '禁止自动重试、修复重跑、延期或force；若生产已成功而显示失败，先利用普通错误记录定位显示问题，不重复平衡求解。未通过部分与原历史保持。', ''])
    if decision is not None and 'next_steps_md' in decision:next_text=decision['next_steps_md']
    old_fronts = {name: subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false','show',BASE+':'+name], cwd=ROOT) for name in FRONTS}
    for name, old in old_fronts.items():
        assert (ROOT / name).read_bytes() == old, 'Front already differs from baseline: ' + name
    write('RESULTS.md', '\n'.join(lines))
    write('NEXT_STEPS.md', next_text)
    write('author/closure.json', json.dumps(closure, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    history = dict(source_baseline_commit=BASE, files=[])
    for name, old in old_fronts.items():
        link = os.path.relpath(ROOT / STAGE / 'RESULTS.md', (ROOT / name).parent).replace('\\', '/')
        prefix = (f'> 2026-10-18 L-CTIPPILOT1 **{outcome.upper()}**：固定圆形工件0→0.25→0.50 mm短加载；'
            f'生产 {shown(production_status)}，保存态 {shown(saved_count)}，helper／outer '
            f"{shown(helper.get('status'))}／{launch['status']}。原资格及历史保持；"
            f'见[实际记录]({link})。原历史说明保留如下。\n\n').encode('utf-8')
        (ROOT / name).write_bytes(prefix + old)
        current = (ROOT / name).read_bytes()
        assert current.endswith(old) and current.count(old) == 1
        history['files'].append(dict(path=name, old_bytes=len(old), old_sha256=sha256(old).hexdigest(),
            prefix_bytes=len(prefix), raw_suffix_preserved_once=True))
    write('author/front_history.json', json.dumps(history, ensure_ascii=False, indent=2) + '\n')
    for name in ('close.py','publish.py','archive_publication.py','prepare_document_sources.py'):
        (ROOT/STAGE/'author'/name).write_bytes((Path(__file__).resolve().parent/name).read_bytes())
    print(json.dumps(dict(status='closed', execution_status=outcome,
        production_status=production_status, saved_accepted_states=saved_count, fronts=len(FRONTS)), ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
