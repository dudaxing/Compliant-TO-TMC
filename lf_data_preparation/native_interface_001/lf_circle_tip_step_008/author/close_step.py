"""Close L-CTIPSTEP8 using ordinary records and producer seals/stat only."""
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
STAGE = 'lf_data_preparation/native_interface_001/lf_circle_tip_step_008'
BASE = 'bfe7337bd061ccb3cd8cbdc46baa801f93b52a34'
CARD, LABEL = 'L-CTIPSTEP8', 'wave_circle_tip_step8'
FRONTS = ('README.md', 'hf_repo/README.md', 'docs/CURRENT_STATUS.md',
    'docs/PHYSICAL_FUNCTION_PROGRESS.md', 'docs/RESUME_DEVELOPMENT.md',
    'docs/L_USE1_NEXT_STEP_PLAN.md', 'docs/L_BFWD1_NEXT_STEP_PLAN.md')
MEDIA = ('view/comparison.png', 'view/distances_forces.png', 'view/peak_fields.png',
    'view/right_medium.png', 'convergence/convergence.png', 'view/'+LABEL+'/actual_states.gif')


def read(name, optional=False):
    path = ROOT/STAGE/name
    return None if optional and not path.is_file() else json.loads(path.read_bytes())


def shown(value):
    return '未提供' if value is None else str(value)


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode('utf-8')


def main():
    stage = ROOT/STAGE
    assert not (stage/'author/closure.json').exists(), 'This closure already exists'
    protocol, task = read('protocol.json'), read('step_task.json')
    launch = read('step_launch.json')
    helper = read('run_001/execution_receipt.json', optional=True) or {}
    result = read('run_001/'+LABEL+'/result.json', optional=True)
    response = read('run_001/'+LABEL+'/response.json', optional=True)
    summary = read('run_001/view/'+LABEL+'/summary.json', optional=True)
    views = read('run_001/view/view.json', optional=True)
    convergence = read('run_001/convergence/convergence.json', optional=True)
    review, decision = read('author/ACTUAL_REVIEW.json'), read('author/NEXT_DECISION.json')
    pixel = read('author/pixel_QA.json', optional=True)
    assert protocol['card'] == launch['card'] == CARD
    assert protocol['source_baseline_commit'] == BASE
    assert launch['invocations'] == 1 and launch['status'] in ('pass', 'not_pass')
    assert not helper or helper['card'] == CARD and helper['protocol_sha256'] == launch['protocol_sha256']
    assert review['status'].startswith('pass') and not review.get('blockers', review.get('blocking_findings', []))
    assert task['path'] == dict(kind='load_only', targets_mm=[0., .25, .5, .75, .9, .95, .98, 1.00, 1.02, 1.03, 1.04])
    assert task['input']['target_mm'] == 1.04 and protocol['targets_mm'] == [1.03, 1.04]
    assert task['workpiece'] == dict(kind='fixed_rigid', shape='circle', center_mm=[80., 40.], radius_mm=9., fixed_components=[0,1])
    assert task['regularization'] == dict(alpha=5e-7, length_mm=80.)
    outcome = 'pass' if launch['status'] == helper.get('status') == 'pass' else 'not_pass'
    assert decision['execution_status'] == outcome
    assert isinstance(decision['next_step'], str) and decision['next_step'].strip()
    parent_file = ROOT/protocol['parent_result']
    parent_raw = parent_file.read_bytes()
    assert sha256(parent_raw).hexdigest() == protocol['input_bindings'][protocol['parent_result']]
    parent = json.loads(parent_raw)
    assert parent['status'] == 'success' and parent['path_completed'] and parent['reached_displacement'] == 1.03
    assert parent['targets_mm'] == [1.02, 1.03] and parent['path_kind'] == 'load_only'
    assert all(parent[key] is False for key in ('task_target_executed', 'full_original_path_completed', 'full_extended_path_completed'))
    assert isinstance(parent['continuation']['parent_continuation'], dict)
    selected = parent['states'][1]
    assert selected['original_target_index'] == 9 and selected['d'] == 1.03
    assert selected['state_sha256'] == protocol['source_anchor']['state_sha256']
    assert float(selected['R_input']).hex() == float(protocol['source_anchor']['R_input_N']).hex()
    outputs = helper.get('outputs') or {}
    for name, seal in outputs.items():
        assert (ROOT/name).stat().st_size == seal['bytes'], name
    media = {name: outputs[STAGE+'/run_001/'+name] for name in MEDIA if STAGE+'/run_001/'+name in outputs}
    observed = {row['index']: row for row in summary['rows']} if summary is not None else {}
    states = result['states'] if result is not None else None
    rows = []
    for index, state in enumerate(states or []):
        observation = observed.get(index)
        if observation is not None:
            assert (observation['state_sha256'], observation['d_mm'], observation['original_target_index'], observation['leg']) == (
                state['state_sha256'], state['d'], state['original_target_index'], state['leg'])
            assert (observation['R_input_N'], observation['q_out_mm']) == (state['R_input'], state['q_out'])
        rows.append(dict(index=index, original_target_index=state.get('original_target_index'),
            child_original_target_index=state.get('child_original_target_index'),
            continuation_anchor=state.get('continuation_anchor'), is_original_target=state.get('is_original_target'),
            leg=state.get('leg'), d_mm=state['d'], state_sha256=state['state_sha256'],
            R_input_N=state['R_input'], q_out_mm=state['q_out'], workpiece=state.get('workpiece'),
            minimum_J=state.get('minimum_J'), relative_residual=state.get('relative_residual'),
            constraint_residual_mm=state.get('constraint_residual'), constraint_bound_mm=state.get('constraint_bound'),
            relative_global_force_balance=state.get('relative_global_force_balance'), view_observation=observation))
    saved_count = len(states) if states is not None else None
    continuation = result.get('continuation') if result is not None else None
    path_keys = ('path_kind', 'targets_mm', 'reached_displacement', 'path_completed', 'loading_peak_reached',
        'new_peak_reached', 'extended_segment_completed', 'task_target_executed', 'full_original_path_completed',
        'full_extended_path_completed', 'unload_endpoint_reached')
    path_flags = {key: result.get(key) for key in path_keys} if result is not None else None
    if outcome == 'pass':
        assert result is not None and result['status'] == 'success' and result['reached_displacement'] == 1.04
        assert saved_count >= 2 and helper['accepted_states'] == saved_count
        assert helper['cached_production_gates']['passed'] and launch['cleanup_verified']
        assert all(result[key] is False for key in ('task_target_executed', 'full_original_path_completed', 'full_extended_path_completed'))
        assert all(continuation[key] is True for key in ('segment_completed', 'anchor_revalidated', 'anchor_identity_preserved', 'extended_segment_completed', 'new_peak_reached'))
        assert continuation['source_task_targets_mm'] == [0., .25, .5, .75, .9, .95, .98, 1.00, 1.02, 1.03]
        assert continuation['extended_task_targets_mm'] == [0., .25, .5, .75, .9, .95, .98, 1.00, 1.02, 1.03, 1.04]
        assert continuation['requested_suffix_targets_mm'] == [1.03, 1.04] and continuation['appended_targets_mm'] == [1.04]
        assert continuation['parent_continuation'] == parent['continuation']
        assert continuation['original_target_indices'] == [9,10]
        assert continuation['selected_state']['accepted_index'] == 1 and continuation['selected_state']['original_target_index'] == 9
        assert states[0]['state_sha256'] == selected['state_sha256'] and states[0]['continuation_anchor']
        assert float(states[0]['R_input']).hex() == float(selected['R_input']).hex()
        assert pixel is not None and pixel['card'] == CARD and pixel['status'].startswith('pass') and pixel['inspections'] == 5
        pngs = {STAGE+'/run_001/'+name for name in MEDIA if name.endswith('.png')}
        assert {row['path'] for row in pixel['media']} == pngs and len(pixel['media']) == 5
        assert all(row['inspections'] == 1 for row in pixel['media'])
        assert len(media) == 6 and views['status'] == 'pass' and helper['actual_GIF_frames'] == saved_count
    counts = result.get('call_counts') if result is not None else helper.get('production_call_counts')
    closure = dict(card=CARD, status=outcome+'_closed', execution_status=outcome, execution_closed=True,
        created_utc=datetime.now(timezone.utc).isoformat(), source_baseline_commit=BASE,
        science_version='0.5.0', science_baseline_commit='b1334bb6a83ba9a0efab7bdba7bd39722146f024',
        protocol_sha256=launch['protocol_sha256'], outer_status=launch['status'], helper_status=helper.get('status'),
        production_status=result.get('status') if result is not None else None,
        terminal=review.get('terminal', {}).get('tool_terminal_as_reported_by_parent'),
        helper_phase=helper.get('phase'), helper_error=helper.get('error'), outer_error=launch.get('error'),
        outer_stop_reason=launch.get('stop_reason'), API_failure=helper.get('API_failure'),
        saved_accepted_states=saved_count, helper_on_accept_count=helper.get('accepted_states'),
        saved_count_basis='len(result.states); null if result absent; actual controller bisections preserved',
        path_flags=path_flags, continuation=continuation, source_anchor=protocol['source_anchor'],
        parent_result=protocol['parent_result'], parent_result_sha256=sha256(parent_raw).hexdigest(), parent_success_preserved=True,
        complete_task_targets_mm=protocol['complete_task_targets_mm'], child_requested_targets_mm=protocol['targets_mm'],
        original_gates=protocol['gates'], cached_production_gates=helper.get('cached_production_gates'),
        production_call_counts=counts, wrapper_call_counts=helper.get('call_counts'),
        rows=rows, last_saved_state=rows[-1] if rows else None,
        convergence_counts=convergence.get('counts') if convergence is not None else None,
        view_status=views.get('status') if views is not None else None, view_actual_counts=helper.get('view_actual_counts'),
        actual_GIF_frames=helper.get('actual_GIF_frames'), right_medium=summary.get('right_medium') if summary is not None else None,
        available_sealed_visualizations=media, pixel_QA_status=pixel.get('status') if pixel is not None else None,
        pixel_QA_observations=pixel.get('observations') if pixel is not None else None, actual_review_status=review['status'],
        helper_elapsed_seconds=helper.get('elapsed_seconds'), outer_elapsed_seconds=launch.get('elapsed_seconds'),
        peak_sampled_tree_RSS_bytes=launch.get('peak_sampled_tree_RSS_bytes'), cleanup_verified=launch.get('cleanup_verified'),
        sealed_output_files=len(outputs), sealed_output_bytes=sum(row['bytes'] for row in outputs.values()),
        output_identity_seal=helper.get('output_identity_seal'),
        new_tests=helper.get('new_tests'), default_installations=helper.get('default_installations'), HP_calls_by_wrapper=helper.get('HP_calls_by_wrapper'),
        independent_reference=response.get('independent_reference') if response is not None else None,
        producer_flags=response.get('producer_flags') if response is not None else None,
        next_decision=decision, next_step=decision['next_step'],
        qualification_scope='Freshly revalidated 1.03mm anchor and explicit 1.04mm suffix only; no complete prefix replay, independent HP, pressure, effective grip, unload/release, stability, mesh/domain-width convergence or HF5 qualification',
        closure_read_scope='Ordinary JSON/source/docs and original producer seals/stat only; no scientific/media/CSV hash, decode, rendering, tests or mechanics; Git object I/O separate')
    table = ['|child行|global目标|路段|d mm|输入R N|q_out mm|body Fy N|tip距离 mm|最近边界 mm|solid minJ|medium minJ|',
        '|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    right_table = ['|d mm|右介质 minJ|右介质 maxabsHu 1/mm|右条带最大节点位移 mm|relative residual|',
        '|---:|---:|---:|---:|---:|']
    for row in rows:
        observed_row = row['view_observation'] or {}
        force = (row.get('workpiece') or {}).get('force_on_lower_body_N', {}).get('total')
        values = [row['index'], row['original_target_index'], row['leg'], row['d_mm'], row['R_input_N'], row['q_out_mm'],
            force[1] if force is not None else None] + [observed_row.get(key) for key in
            ('tip_to_raster_boundary_mm', 'minimum_boundary_distance_mm', 'solid_min_J', 'medium_min_J')]
        table.append('|'+'|'.join(map(shown, values))+'|')
        values = [row['d_mm']] + [observed_row.get(key) for key in ('right_medium_min_J', 'right_medium_max_abs_Hu_per_mm', 'right_medium_max_nodal_displacement_mm')] + [row['relative_residual']]
        right_table.append('|'+'|'.join(map(shown, values))+'|')
    lines = [f'# {CARD}：最右尖端对向圆形工件的保存态延伸', '',
        f"2026-10-19；执行 **{outcome.upper()}**。生产 `{shown(closure['production_status'])}`，helper `{shown(helper.get('status'))}`，outer `{launch['status']}`；实际停止阶段 `{shown(helper.get('phase'))}`。", '',
        '整体目标是把LF给出的夹持器几何接入独立、可恢复的高保真大变形/TMC有限元分析，逐步实现对工件接近、接触后的变形与作用力及卸载响应的可审查计算。结构优化、有效夹持判定和HF5标签尚不能由单段前向计算替代。', '',
        '本轮做什么及原因：复用已安装load_only显式保存态延伸接口，从已成功的1.03 mm状态重新核验平衡及SHA/有符号R，再执行唯一新目标1.04 mm。该小步用来观察最右尖端能否继续对向接近，并查看右侧介质压缩和计算成本，避免依据初始布置直接推断大行程效果。未从零重放原加载前缀，也未改默认HF源码。', '',
        '半径9 mm、圆心(80,40) mm、固定工件ux/uy、右域界92 mm、正则化长度80 mm保持；下半域92×40 mm、h=0.5 mm、厚20 mm、E=1 MPa、nu=0.3、plane strain、gamma=1e-6、alpha=5e-7及原支撑/平均端口/对称保持。完整任务[0,.25,.5,.75,.90,.95,.98,1.00,1.02,1.03,1.04]仅追加1.04并将input.target改为1.04及四项说明身份；本次请求后缀[1.03,1.04]。', '',
        f"已完成及实际效果：保存接受态 `{shown(saved_count)}`，helper回调 `{shown(helper.get('accepted_states'))}`。缺失保存结果记为null，实际二分增加的接受态全部保留。父结果SHA `{closure['parent_result_sha256']}` 与授权绑定一致，原成功与失败历史保留。", '',
        '\n'.join(table), '', '\n'.join(right_table), '',
        '表中保留原数值。q_out是加权端口位移，不是表面间隙；输入R与工件合力为原下半模型数值。完整Fx/Fy的material/Hu/total分量、实际尖端及边界见证、分区极值与位置、原残差/约束界和整体平衡见[闭卡JSON](author/closure.json)及[显示摘要](run_001/view/'+LABEL+'/summary.json)。', '',
        f"原验收门 `{protocol['gates']}`；缓存检查 `{shown(helper.get('cached_production_gates'))}`。生产调用 `{shown(counts)}`；收敛计数 `{shown(closure['convergence_counts'])}`。API/solver/view等包装调用 `{shown(helper.get('call_counts'))}`。原门和非clock设置不变；minimum_increment=0.00625 mm保持，0.01 mm可直接尝试，若失败则半步0.005 mm低于原限值，按原规则停止。", '',
        f"路径实际标志 `{shown(path_flags)}`。新峰值与延伸段完成只说明本段；task_target_executed、full_original_path_completed、full_extended_path_completed保持false，完整加载前缀没有在child中执行。没有把本段PASS授予整条路径或独立参考。", '',
        '图中实际坐标×1；完整结构和动画只作对称镜像，数值没有镜像加倍。尖端按唯一参考坐标(80,30)动态查找并跟随实际位移。unsigned Q1外露边界距离、相交/near-touch、跨区凸单元重叠和数值不确定性分别记录；正距离和非零弱力不能单独认定有效接触，完整包含关系/机构自重叠尚未验证。', '',
        '右侧条带固定参考x89..92、6列480cells，保留实际位移后的外界与原顶uy约束。完整条带极值覆盖80行，局部图是上部裁剪；Green应变不换算为工程压缩百分比，cellwise Hu代表点不当作独立九点量。右条带最大节点位移不是尖端间隙；其极值节点可随状态切换，具体位置见原摘要。右侧场变化不能单独证明边界污染或域宽充分。', '',
        '圆形工件表面的法向随位置变化；下半体材料/Hu/总Fx/Fy是有符号弱式合力，Hu也不能当作连续表面压力。因此尚无压力、有效夹持、卸载/自由释放、稳定性、网格/域宽收敛或HF5资格；当前布置也未做新HP，旧布置参考不转授。', '',
        decision.get('interpretation_md', ''), '',
        f"helper `{shown(helper.get('elapsed_seconds'))}`/2700 s，outer `{shown(launch.get('elapsed_seconds'))}`/2760 s；controller1800 s，显示共享600 s；进程树采样峰值 `{shown(launch.get('peak_sampled_tree_RSS_bytes'))}` B/64 GiB，清理 `{shown(launch.get('cleanup_verified'))}`。四库线程配置上限16，不等于实测16核利用率；pure viewer原内部8 GiB限制保持。", '',
        f"原窗口封存 `{len(outputs)}` 个输出、`{closure['sealed_output_bytes']}` B；闭卡仅继承seal并核大小。实际审查 `{review['status']}`，像素记录 `{shown(closure['pixel_QA_status'])}`。新测试 `{shown(helper.get('new_tests'))}`、默认安装 `{shown(helper.get('default_installations'))}`、wrapper新HP `{shown(helper.get('HP_calls_by_wrapper'))}`。", '',
        f"错误原值：helper `{shown(helper.get('error'))}`；API `{shown(helper.get('API_failure'))}`；outer `{shown(launch.get('error'))}`。生产与显示阶段状态分开保留，不覆盖历史，不进行外部重试、修复重跑、延期、force、回滚或删除。", '']
    for name in media:
        lines += [f'![{name}](run_001/{name})', '']
    lines += ['后续决策：'+decision['next_step'], '',
        '复核/恢复：主仓库origin保持https://github.com/dudaxing/Compliant-TO-TMC.git，后续开发在main。另一位置执行git clone该地址后，先读README、docs/CURRENT_STATUS.md、docs/RESUME_DEVELOPMENT.md及本卡RESULTS/NEXT_STEPS；依据仓库固定环境重建依赖，再核对protocol、author/authorization和保存态来源。不要重跑已关闭launcher或从显示数组重建锚；下一科学窗口使用公开evaluate_native(..., saved_result=..., selected_state_index=..., extend_path=True)和明确的新任务。', '',
        '恢复起点命令（PowerShell；读取状态，不启动旧运行）：', '', '```powershell',
        'git clone https://github.com/dudaxing/Compliant-TO-TMC.git',
        'git -C Compliant-TO-TMC status --short --branch',
        'Get-Content -LiteralPath Compliant-TO-TMC/docs/RESUME_DEVELOPMENT.md', '```', '',
        '入口：[人工页](run_001/REVIEW.md) · [原结果](run_001/'+LABEL+'/result.json) · [原响应](run_001/'+LABEL+'/response.json) · [收敛记录](run_001/convergence/convergence.json) · [outer](step_launch.json) · [helper](run_001/execution_receipt.json) · [闭卡JSON](author/closure.json) · [实际审查](author/ACTUAL_REVIEW.md) · [像素记录](author/pixel_QA.json) · [后续](NEXT_STEPS.md)', '']
    next_text = decision.get('next_steps_md') or ('# '+CARD+' 后续\n\n'+decision['next_step']+'\n\n本页只记录下一步建议，不启动新目标或授权新窗口；原物理与验收门保持，先明确新范围及资源。\n')
    generated = {'RESULTS.md': ('\n'.join(lines).rstrip()+'\n').encode('utf-8'),
        'NEXT_STEPS.md': (next_text.rstrip()+'\n').encode('utf-8'), 'author/closure.json': encoded(closure)}
    old_fronts = {name: subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false','show',BASE+':'+name], cwd=ROOT) for name in FRONTS}
    for name, old in old_fronts.items():
        assert (ROOT/name).read_bytes() == old, 'Front differs from baseline: '+name
    history = dict(source_baseline_commit=BASE, files=[])
    prefixed = {}
    for name, old in old_fronts.items():
        link = os.path.relpath(stage/'RESULTS.md', (ROOT/name).parent).replace('\\','/')
        prefix = (f'> 2026-10-19 {CARD} **{outcome.upper()}**：固定圆形工件r9/(80,40)、right92/Lr80，从成功1.03 mm保存态延伸至1.04 mm；'
            f"生产 {shown(closure['production_status'])}，保存态 {shown(saved_count)}，helper/outer {shown(helper.get('status'))}/{launch['status']}。"
            f'本次只执行后缀，完整前缀未重放；原资格与历史保持。见[实际记录]({link})。原历史说明保留如下。\n\n').encode('utf-8')
        prefixed[name] = prefix+old
        assert prefixed[name].endswith(old) and prefixed[name].count(old) == 1
        history['files'].append(dict(path=name, old_bytes=len(old), old_sha256=sha256(old).hexdigest(), prefix_bytes=len(prefix), raw_suffix_preserved_once=True))
    generated['author/front_history.json'] = encoded(history)
    for name, raw in generated.items():
        assert not any(line.rstrip(b' \t') != line for line in raw.splitlines()), name
    for name, raw in generated.items():
        (stage/name).write_bytes(raw)
    for name, raw in prefixed.items():
        (ROOT/name).write_bytes(raw)
    (stage/'author/close_step.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps(dict(status='closed', execution_status=outcome, production_status=closure['production_status'],
        saved_accepted_states=saved_count, fronts=len(FRONTS)), ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
