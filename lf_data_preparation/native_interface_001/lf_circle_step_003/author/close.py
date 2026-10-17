"""Close one saved circle loading step from ordinary records and producer seals."""
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
STAGE = 'lf_data_preparation/native_interface_001/lf_circle_step_003'
BASE = '260d4b86ee87ab3dd12c04dbcccef7ffa4c31eac'
CARD = 'L-CSTEP3'
FRONTS = ['README.md', 'hf_repo/README.md', 'docs/CURRENT_STATUS.md',
    'docs/PHYSICAL_FUNCTION_PROGRESS.md', 'docs/RESUME_DEVELOPMENT.md',
    'docs/L_USE1_NEXT_STEP_PLAN.md', 'docs/L_BFWD1_NEXT_STEP_PLAN.md']


def read(name, *, optional=False):
    path = ROOT / STAGE / name
    return None if optional and not path.is_file() else json.loads(path.read_bytes())


def write(name, value):
    (ROOT / STAGE / name).write_text(value, encoding='utf-8', newline='\n')


def shown(value):
    return '未提供' if value is None else str(value)


def main():
    launch = read('step_launch.json')
    receipt = read('run_001/execution_receipt.json', optional=True)
    result = read('run_001/wave_circle_step/result.json', optional=True)
    response = read('run_001/wave_circle_step/response.json', optional=True)
    summary = read('run_001/view/wave_circle_step/summary.json', optional=True)
    view = read('run_001/view/view.json', optional=True)
    convergence = read('run_001/convergence/convergence.json', optional=True)
    protocol, task = read('protocol.json'), read('step_task.json')
    parent_file = ROOT/protocol['parent_result']
    parent = json.loads(parent_file.read_bytes())
    parent_selected = parent['states'][protocol['selected_state_index']]
    review = read('author/ACTUAL_REVIEW.json')
    pixel = read('author/pixel_QA.json', optional=True)
    assert launch['card'] == protocol['card'] == CARD
    assert receipt is None or receipt['card'] == CARD
    assert pixel is None or pixel['card'] == CARD
    assert review['status'].startswith('pass') and not review.get('blockers', review.get('blocking_findings', []))
    assert launch['status'] in ('pass', 'not_pass')
    assert receipt is None or receipt['status'] in ('pass', 'not_pass')
    assert receipt is None or receipt['protocol_sha256'] == launch['protocol_sha256']
    assert task['workpiece'] == dict(kind='fixed_rigid', shape='circle', center_mm=[71., 40.],
        radius_mm=9., fixed_components=[0, 1])
    assert task['path'] == dict(kind='load_only', targets_mm=[0., .25, .5, .75, 1., 1.15, 1.25])
    assert task['input']['target_mm'] == 1.25
    assert protocol['selected_state_index'] == 1
    assert parent['status'] == 'success' and parent['path_completed']
    assert parent_selected['d'] == 1.15 and parent_selected['original_target_index'] == 5
    assert protocol['settings'] == parent['settings']
    assert not subprocess.check_output(['git', 'diff', BASE, '--name-only', '--', 'hf_repo/src'], cwd=ROOT)
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
            child_original_target_index=state.get('child_original_target_index'),
            continuation_anchor=state.get('continuation_anchor'),
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
        assert result['path_completed'] is True and result['reached_displacement'] == 1.25
        assert result['settings'] == parent['settings']
        assert result['targets_mm'] == [1.15, 1.25] and result['path_kind'] == 'load_only'
        assert result['new_peak_reached'] and result['extended_segment_completed']
        assert result['task_target_executed'] is False
        assert result['full_original_path_completed'] is False and result['full_extended_path_completed'] is False
        continuation = result['continuation']
        assert continuation['anchor_revalidated'] and continuation['anchor_identity_preserved']
        assert continuation['new_peak_reached'] and continuation['extended_segment_completed']
        assert continuation['full_original_path_completed'] is False
        assert continuation['full_extended_path_completed'] is False and continuation['task_target_executed'] is False
        originals = [row for row in states if row['is_original_target']]
        assert [(row['original_target_index'], row['child_original_target_index'], row['d']) for row in originals] == [(5, 0, 1.15), (6, 1, 1.25)]
        assert states[0]['state_sha256'] == parent_selected['state_sha256']
        assert float(states[0]['R_input']).hex() == float(parent_selected['R_input']).hex()
        assert helper.get('new_tests') == helper.get('default_installations') == helper.get('HP_calls_by_wrapper') == 0
    outputs = helper.get('outputs')
    media = {}
    for name in ('view/comparison.png', 'view/distances_forces.png', 'view/peak_fields.png',
                 'view/wave_circle_step/actual_states.gif', 'convergence/convergence.png'):
        relative = STAGE + '/run_001/' + name
        if relative in (outputs or {}):
            assert (ROOT / relative).stat().st_size == outputs[relative]['bytes']
            media[name] = outputs[relative]
    counts = result.get('call_counts') if result is not None else helper.get('production_call_counts')
    path_flags = {key: result.get(key) for key in ('path_kind', 'targets_mm', 'reached_displacement',
        'path_completed', 'loading_peak_reached', 'new_peak_reached', 'extended_segment_completed',
        'task_target_executed', 'full_original_path_completed', 'full_extended_path_completed',
        'unload_endpoint_reached')} if result is not None else None
    continuation = result.get('continuation') if result is not None else None
    terminal = review.get('terminal', {}).get('tool_terminal_as_reported_by_parent')
    if outcome != 'pass':
        next_step = ('先处理实际停止阶段；若生产已成功而显示未完成，只安排保存态显示问题诊断，'
            '不得重写原API成功或重做已完成求解。没有自动重试、修复重跑或新窗口。')
    elif (last_observation is not None and (last_observation.get('boundary_intersects') is True
            or last_observation.get('raw_overlap') is True or last_observation.get('roundoff_ambiguous') is True)):
        next_step = ('先核查已保存的边界相交、单元重叠或数值不确定观察，再决定是否安排下一目标；'
            '不把无符号距离或非零工件合力单独认定为接触。')
    elif (last_observation is None or convergence is None
            or any(last_observation.get(key) is not False for key in
                ('boundary_intersects', 'raw_overlap', 'roundoff_ambiguous'))
            or any(last_observation.get(key) is None or last_observation[key] <= 0 for key in
                ('minimum_boundary_distance_mm', 'solid_min_J', 'medium_min_J'))):
        next_step = ('先核查已保存的实际几何、分区J或收敛观察缺项与不确定性，再确定下一个单目标。'
            '不能把缺失值当作无接触、正间隙或稳定性证明，也不安排自动重试。')
    else:
        next_step = ('依据本次末态实际边界距离、局部变形、材料/Hu/总工件力、分区J、残差、回溯与耗时，'
            '规划从成功1.25 mm末态只追加一个绝对加载目标。具体目标和资源由本次原值审阅后确定，'
            '本页不锁定数值、不执行后续计算，也不自动移植旧方体1.20 mm上限。'
            '正的无符号距离与非零Fy仍不能单独证明接触、压力或有效夹持。')
    closure = dict(card=CARD, status=outcome + '_closed', execution_status=outcome, execution_closed=True,
        created_utc=datetime.now(timezone.utc).isoformat(), source_baseline_commit=BASE,
        science_version='0.5.0', science_baseline_commit='b1334bb6a83ba9a0efab7bdba7bd39722146f024',
        protocol_sha256=launch['protocol_sha256'], terminal=terminal,
        helper_status=helper.get('status'), outer_status=launch['status'], production_status=production_status,
        helper_phase=helper.get('phase'), helper_error=helper.get('error'), outer_stop_reason=launch.get('stop_reason'),
        saved_accepted_states=saved_count, saved_count_basis='len(result.states), or null if result is absent',
        helper_on_accept_count=helper.get('accepted_states'),
        helper_count_basis='Observer callback counter; separate from persisted accepted-state count',
        path_flags=path_flags, original_gates=protocol['gates'], cached_production_gates=cached,
        continuation=continuation,
        source_parent=dict(result_file=protocol['parent_result'], status=parent['status'],
            path_completed=parent['path_completed'], targets_mm=parent['targets_mm'],
            selected_state_index=protocol['selected_state_index'],
            selected_original_target_index=parent_selected['original_target_index'],
            selected_displacement_mm=parent_selected['d'], state_sha256=parent_selected['state_sha256'],
            parent_continuation=parent.get('continuation')),
        default_sources_unchanged=True,
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
        qualification_scope='Circle saved 1.15/1.25 loading segment only; old task prefix not reexecuted; no full extended path, original25 path, fresh HP, pressure, effective clamp, unloading, release, stability, manufacturing or HF5 qualification',
        closure_read_scope='Ordinary records and producer output seals/stat only; no scientific/media payload read, hash, decode, rendering, tests or mechanics')

    lines = [f'# {CARD}：圆形固定工件1.15→1.25 mm保存态加载', '',
        f"执行状态 **{outcome.upper()}**；生产 `{shown(production_status)}`、helper `{shown(helper.get('status'))}`、outer `{launch['status']}`，停止阶段 `{shown(helper.get('phase'))}`。基线 main `{BASE}`；science 0.5.0／b1334 基线保持。", '',
        '整体目标仍是普通LF几何进入独立HF的TMC前向力学，逐步实现可检查的加载、接触与卸载。本次复用已安装并验证的load_only保存态显式延伸，从L-CSTEP2成功1.15 mm末态推进到1.25 mm；借助实际变形、反力、工件合力、距离、分区场与收敛记录判断下一步。', '',
        '工件半径9 mm、中心(71,40) mm、固定ux/uy；其余E=1 MPa、nu=0.3、plane strain、厚20 mm、h=0.5 mm、84×40 mm下半域、gamma=1e-6、alpha=5e-7、Lr=80 mm及支撑/平均端口/对称保持。新任务完整保留[0,0.25,0.50,0.75,1.00,1.15]前缀，只追加1.25 mm并将input目标更新至新峰值；四说明字段可更新，其余物理任务、数值设置及原门保持。原父任务、结果与方体25目标历史不改。', '',
        f"来源父段 `{protocol['parent_result']}` 状态 `{parent['status']}`；选中接受行 `{protocol['selected_state_index']}`，全局目标索引 `{parent_selected['original_target_index']}`，d=`{parent_selected['d']}` mm，state SHA `{parent_selected['state_sha256']}`。本子段使用全局索引5/6和本地索引0/1；原数值设置与父段精确保持。默认HF源码保持，未新增测试、HP或安装。", '',
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
        f"收敛原记录计数 `{shown(closure['convergence_counts'])}`。回溯或二分若存在，属于原控制器工作，全部实际接受态保留；不会锁定仅两态。新测试 `{shown(helper.get('new_tests'))}`、默认安装 `{shown(helper.get('default_installations'))}`、wrapper新HP `{shown(helper.get('HP_calls_by_wrapper'))}`。", '',
        f"保存延伸来源和资格原值 `{shown(continuation)}`。new_peak_reached与extended_segment_completed仅描述本次子段；task_target_executed、full_original_path_completed、full_extended_path_completed保持False，因为本次没有从零执行完整前缀。首态使用原绝对lift/fluctuation及带符号R，以fresh F/T复核原门并保持状态身份，不复用旧力或切线。", '',
        '实际距离使用所选圆形Q1单元的物理外露阶梯边，排除对称切口；解析圆只作图示参考。无符号距离不等于有符号间隙。通用凸Q1跨区域单元重叠是另一项观察，完整包含关系及机构自重叠仍未检查；False、None与数值不确定状态分别保留。', '',
        f"末态几何与分区场实录：`{shown(last_observation)}`。若显示未完成或该项未提供，不能据缺失值判断无接触、无重叠或场稳定。", '',
        '圆周局部法向随位置变化；下半工件全局Fx/Fy是含材料和Hu的有符号弱式合力，不是连续压力或圆周总法向夹持力。坐标×1，完整结构图和GIF仅作对称镜像，数值没有镜像加倍；节点箭头包含切口/内部节点，不能当作表面压力。', '',
        f"实际独立审阅 `{review['status']}`；像素检查 `{shown(closure['pixel_QA_status'])}`，观察 `{shown(closure['pixel_QA_observations'])}`。没有新增重绘或媒体重解码。", '']
    for name in media:
        lines += [f'![{name}](run_001/{name})', '']
    lines += [f"helper `{shown(helper.get('elapsed_seconds'))}` s／{protocol['helper_seconds']} s，outer `{shown(launch.get('elapsed_seconds'))}` s／{protocol['outer_seconds']} s；controller {protocol['controller_seconds']} s，viewer＋收敛＋人工页共享{protocol['viewer_seconds']} s；进程树采样峰值 `{shown(launch.get('peak_sampled_tree_RSS_bytes'))}` B／{protocol['sampled_RSS_bytes']} B，清理 `{shown(launch.get('cleanup_verified'))}`。终端 `{shown(terminal)}`。原窗口封存 {shown(closure['sealed_output_files'])} 个输出、{shown(closure['sealed_output_bytes'])} B，状态 `{shown(helper.get('output_identity_seal'))}`；闭卡继承producer seal＋stat，不重读载荷。", '',
        f"真实错误：helper `{shown(helper.get('error'))}`；API `{shown(helper.get('API_failure'))}`；outer `{shown(launch.get('error'))}`。生产成功与显示阶段失败分别报告，不回写原API或原结果。", '',
        '本轮不取得整条新路径从零执行、独立HP、压力、有效夹持、原25态完整循环、卸载/自由释放、稳定性或HF5资格；制造仍pending。既有父段成功保留历史，不把原参考资格自动转授新态。', '',
        '下一步：' + next_step, '',
        '审查入口：[原响应](run_001/wave_circle_step/response.json)、[原结果](run_001/wave_circle_step/result.json)、[原值人工页](run_001/REVIEW.md)、[显示摘要](run_001/view/wave_circle_step/summary.json)、[收敛JSON](run_001/convergence/convergence.json)、[helper](run_001/execution_receipt.json)、[outer](step_launch.json)、[实际审阅](author/ACTUAL_REVIEW.md)、[闭卡JSON](author/closure.json)。', '']
    next_text = '\n'.join(['# L-CSTEP3 后续', '',
        f"实际执行 `{outcome}`；生产 `{shown(production_status)}`；保存态 `{shown(saved_count)}`。", '', next_step, '',
        '下一阶段必须依据本次保存的几何、原分区J、残差、回溯和成本明确物理目标与资源；本页不授权新运行。不例行补HP，不把旧方体或旧同值状态的参考转授给这条圆形路径。', '',
        '禁止自动重试、修复重跑、延期或force；若生产已成功而显示失败，先利用普通错误记录定位显示问题，不重复平衡求解。未通过部分与原历史保持。', ''])
    old_fronts = {name: subprocess.check_output(['git', 'show', BASE + ':' + name], cwd=ROOT) for name in FRONTS}
    for name, old in old_fronts.items():
        assert (ROOT / name).read_bytes() == old, 'Front already differs from baseline: ' + name
    write('RESULTS.md', '\n'.join(lines))
    write('NEXT_STEPS.md', next_text)
    write('author/closure.json', json.dumps(closure, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    history = dict(source_baseline_commit=BASE, files=[])
    for name, old in old_fronts.items():
        link = os.path.relpath(ROOT / STAGE / 'RESULTS.md', (ROOT / name).parent).replace('\\', '/')
        prefix = (f'> 2026-10-17 L-CSTEP3 **{outcome.upper()}**：复用load_only保存态延伸，固定圆形工件1.15→1.25 mm；'
            f'生产 {shown(production_status)}，保存态 {shown(saved_count)}，helper／outer '
            f"{shown(helper.get('status'))}／{launch['status']}。原资格及历史保持；"
            f'见[实际记录]({link})。原历史说明保留如下。\n\n').encode('utf-8')
        (ROOT / name).write_bytes(prefix + old)
        current = (ROOT / name).read_bytes()
        assert current.endswith(old) and current.count(old) == 1
        history['files'].append(dict(path=name, old_bytes=len(old), old_sha256=sha256(old).hexdigest(),
            prefix_bytes=len(prefix), raw_suffix_preserved_once=True))
    write('author/front_history.json', json.dumps(history, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(dict(status='closed', execution_status=outcome,
        production_status=production_status, saved_accepted_states=saved_count, fronts=len(FRONTS)), ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
