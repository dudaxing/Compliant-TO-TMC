"""Close the half-alpha first-unload segment using ordinary records and seals."""
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess


ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
STAGE = 'lf_data_preparation/native_interface_001/lf_circle_tip_alpha_unload_001'
BASE = 'eecd5c6ddfcfe01da46a37d0d0b980068eb930ec'
CARD, LABEL = 'L-CTIPAUNLOAD1', 'wave_circle_tip_alpha_unload1'
PREFIX = [0., .25, .50, .75, .90, .95, .98, 1.00, 1.02, 1.03, 1.04, 1.05, 1.06]
FRONTS = ('README.md', 'hf_repo/README.md', 'docs/CURRENT_STATUS.md',
    'docs/PHYSICAL_FUNCTION_PROGRESS.md', 'docs/RESUME_DEVELOPMENT.md',
    'docs/L_USE1_NEXT_STEP_PLAN.md', 'docs/L_BFWD1_NEXT_STEP_PLAN.md')
MEDIA = ('view/comparison.png', 'view/distances_forces.png', 'view/peak_fields.png',
    'view/right_medium.png', 'convergence/convergence.png')
GIT = ['git', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false']


def read(name, optional=False):
    path = ROOT/STAGE/name
    return None if optional and not path.is_file() else json.loads(path.read_bytes())


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode('utf-8')


def shown(value):
    return '未提供' if value is None else str(value)


def table(headers, rows):
    return '\n'.join(['|'+'|'.join(headers)+'|', '|'+'|'.join('---' for _ in headers)+'|']+
        ['|'+'|'.join(shown(value) for value in row)+'|' for row in rows])


def main():
    stage = ROOT/STAGE
    assert not (stage/'author/closure.json').exists(), 'This closure already exists'
    protocol, launch = read('protocol.json'), read('step_launch.json')
    task = json.loads((ROOT/protocol['task_file']).read_bytes())
    helper = read('run_001/execution_receipt.json', optional=True) or {}
    saved = read('run_001/'+LABEL+'/result.json', optional=True)
    response = read('run_001/'+LABEL+'/response.json', optional=True)
    summary = read('run_001/view/'+LABEL+'/summary.json', optional=True)
    views = read('run_001/view/view.json', optional=True)
    convergence = read('run_001/convergence/convergence.json', optional=True)
    review, decision = read('author/ACTUAL_REVIEW.json'), read('author/NEXT_DECISION.json')
    pixel = read('author/pixel_QA.json', optional=True)
    assert protocol['card'] == launch['card'] == CARD
    assert protocol['source_baseline_commit'] == BASE
    assert launch['invocations'] == 1 and launch['status'] in ('pass', 'not_pass')
    assert not helper or (helper['card'] == CARD and helper['protocol_sha256'] == launch['protocol_sha256'])
    assert review['status'].startswith('pass') and not review.get('blockers', review.get('blocking_findings', []))
    assert task['path'] == dict(kind='ordered_cycle', targets_mm=PREFIX+[1.05])
    assert task['input']['target_mm'] == 1.06 and protocol['targets_mm'] == [1.06, 1.05]
    assert task['regularization'] == dict(alpha=2.5e-7, length_mm=80.)
    outcome = 'pass' if launch['status'] == helper.get('status') == 'pass' else 'not_pass'
    assert decision['execution_status'] == review['execution_status'] == outcome
    assert isinstance(decision['next_step'], str) and decision['next_step'].strip()
    parent_raw = (ROOT/protocol['parent_result']).read_bytes()
    assert sha256(parent_raw).hexdigest() == protocol['input_bindings'][protocol['parent_result']]
    parent = json.loads(parent_raw)
    assert parent['status'] == 'success' and parent['path_completed'] and parent['reached_displacement'] == 1.06
    assert parent['path_kind'] == 'load_only' and parent['targets_mm'] == PREFIX
    assert parent['accepted_states'] == len(parent['states']) == 13 and 'continuation' not in parent
    selected = parent['states'][12]
    assert selected['original_target_index'] == 12 and selected['d'] == 1.06
    assert selected['state_sha256'] == protocol['source_anchor']['state_sha256']
    assert float(selected['R_input']).hex() == float(protocol['source_anchor']['R_input_N']).hex()
    outputs = helper.get('outputs') or {}
    for name, seal in outputs.items():
        assert (ROOT/name).stat().st_size == seal['bytes'], name
    media = {name: outputs[STAGE+'/run_001/'+name] for name in MEDIA if STAGE+'/run_001/'+name in outputs}
    GIF = 'view/'+LABEL+'/actual_states.gif'
    gif_seal = outputs.get(STAGE+'/run_001/'+GIF)
    states = saved['states'] if saved is not None else []
    observed = {row['index']: row for row in summary['rows']} if summary is not None else {}
    rows = []
    for index, state in enumerate(states):
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
            relative_global_force_balance=state.get('relative_global_force_balance'),
            newton_checks=state.get('newton_checks'), bisection_depth=state.get('bisection_depth'), view_observation=observation))
    progress_rows = []
    progress_file = stage/'run_001/accepted_progress.jsonl'
    if saved is None and progress_file.is_file():
        progress_rows = [json.loads(line) for line in progress_file.read_text(encoding='utf-8').splitlines() if line.strip()]
    saved_count = len(states) if saved is not None else None
    continuation = saved.get('continuation') if saved is not None else None
    path_keys = ('path_kind', 'targets_mm', 'target_origin', 'reached_displacement', 'path_completed',
        'loading_peak_reached', 'unload_endpoint_reached', 'task_target_executed',
        'full_original_path_completed', 'full_extended_path_completed')
    path_flags = {key: saved.get(key) for key in path_keys} if saved is not None else None
    visual_status = pixel.get('status') if pixel is not None else 'not_provided'
    expected_pngs = {STAGE+'/run_001/'+name for name in MEDIA}
    qa_complete = False
    if pixel is not None:
        assert pixel['card'] == CARD
        inspections = pixel['media']
        assert len(inspections) <= 5 and len({row['path'] for row in inspections}) == len(inspections)
        assert {row['path'] for row in inspections} <= expected_pngs
        assert all(row['inspections'] == 1 for row in inspections)
        assert pixel['inspections'] == len(inspections)
        qa_complete = len(inspections) == 5 and visual_status.startswith('pass')
    if outcome == 'pass':
        assert saved is not None and saved['status'] == 'success'
        assert saved['path_kind'] == 'ordered_cycle' and saved['path_completed'] and saved['reached_displacement'] == 1.05
        assert saved['targets_mm'] == [1.06, 1.05] and saved['unload_endpoint_reached'] is True
        assert saved_count >= 2 and helper['accepted_states'] == saved_count
        assert helper['cached_production_gates']['passed'] and launch['cleanup_verified'] is True
        assert helper['default_installations'] == helper['new_tests'] == helper['HP_calls_by_wrapper'] == 0
        assert all(saved[key] is False for key in ('task_target_executed', 'full_original_path_completed', 'full_extended_path_completed'))
        assert all(continuation[key] is True for key in ('segment_completed', 'anchor_revalidated', 'anchor_identity_preserved'))
        assert continuation['source_task_targets_mm'] == PREFIX
        assert continuation['extended_task_targets_mm'] == PREFIX+[1.05]
        assert continuation['requested_suffix_targets_mm'] == [1.06, 1.05] and continuation['appended_targets_mm'] == [1.05]
        assert continuation['parent_continuation'] is None
        assert continuation['task_transition'] == protocol['expected_task_transition'] == dict(
            source_path_kind='load_only', extended_path_kind='ordered_cycle', first_unload=True,
            loading_peak_mm=1.06, first_unload_target_mm=1.05)
        assert continuation['original_target_indices'] == [12, 13]
        assert continuation['selected_state']['accepted_index'] == 12 and continuation['selected_state']['original_target_index'] == 12
        assert states[0]['state_sha256'] == selected['state_sha256'] and states[0]['continuation_anchor']
        assert float(states[0]['R_input']).hex() == float(selected['R_input']).hex()
        assert 'new_peak_reached' not in saved and 'extended_segment_completed' not in saved
        assert 'new_peak_reached' not in continuation and 'extended_segment_completed' not in continuation
        assert len(media) == 5 and gif_seal is not None and helper['actual_GIF_frames'] == saved_count
        assert views['status'] == 'pass' and views['cases'][0]['last_index'] == saved_count-1
    stage_complete = outcome == 'pass' and qa_complete
    closure = dict(card=CARD, status=outcome+'_closed', execution_status=outcome, execution_closed=True,
        visual_QA_status=visual_status, visual_QA_complete=qa_complete, stage_complete=stage_complete,
        created_utc=datetime.now(timezone.utc).isoformat(), prepared_client_local_date='2026-10-20',
        report_client_local_date='2026-10-20', report_timezone='Asia/Seoul', source_baseline_commit=BASE,
        science_version='0.5.0', science_baseline_commit='b1334bb6a83ba9a0efab7bdba7bd39722146f024',
        protocol_sha256=launch['protocol_sha256'], outer_status=launch['status'], helper_status=helper.get('status'),
        production_status=saved.get('status') if saved is not None else None,
        terminal=review.get('terminal'), helper_phase=helper.get('phase'), helper_error=helper.get('error'),
        outer_error=launch.get('error'), outer_stop_reason=launch.get('stop_reason'), API_failure=helper.get('API_failure'),
        alpha=2.5e-7, task=task, path_flags=path_flags, continuation=continuation,
        parent_result=protocol['parent_result'], parent_result_sha256=sha256(parent_raw).hexdigest(),
        source_anchor=protocol['source_anchor'], parent_success_and_reference_scope_preserved=True,
        complete_task_targets_mm=protocol['complete_task_targets_mm'], child_requested_targets_mm=protocol['targets_mm'],
        saved_accepted_states=saved_count, helper_on_accept_count=helper.get('accepted_states'), rows=rows,
        progress_only_rows_when_saved_result_absent=progress_rows,
        saved_count_basis='len(result.states); null if absent; callback progress is not substituted for saved equilibrium evidence',
        last_saved_state=rows[-1] if rows else None, original_gates=protocol['gates'],
        cached_production_gates=helper.get('cached_production_gates'), settings=protocol['settings'],
        actual_settings=helper.get('actual_settings'), wrapper_call_counts=helper.get('call_counts'),
        production_call_counts=saved.get('call_counts') if saved is not None else helper.get('production_call_counts'),
        convergence_counts=convergence.get('counts') if convergence is not None else None,
        same_input_comparison=helper.get('same_input_comparison'),
        view_status=views.get('status') if views is not None else None, view_actual_counts=helper.get('view_actual_counts'),
        actual_GIF_frames=helper.get('actual_GIF_frames'), actual_total_PNGs=helper.get('actual_total_PNGs'),
        right_medium=summary.get('right_medium') if summary is not None else None,
        available_sealed_visualizations=media, available_sealed_GIF=gif_seal,
        pixel_QA_observations=pixel.get('observations') if pixel is not None else None, actual_review_status=review['status'],
        helper_elapsed_seconds=helper.get('elapsed_seconds'), outer_elapsed_seconds=launch.get('elapsed_seconds'),
        peak_sampled_tree_RSS_bytes=launch.get('peak_sampled_tree_RSS_bytes'), cleanup_verified=launch.get('cleanup_verified'),
        sealed_output_files=len(outputs), sealed_output_bytes=sum(row['bytes'] for row in outputs.values()),
        output_identity_seal=helper.get('output_identity_seal'), new_tests=helper.get('new_tests'),
        default_installations=helper.get('default_installations'), HP_calls_by_wrapper=helper.get('HP_calls_by_wrapper'),
        independent_reference=response.get('independent_reference') if response is not None else None,
        producer_flags=response.get('producer_flags') if response is not None else None,
        next_decision=decision, next_step=decision['next_step'],
        qualification_scope='Only freshly revalidated alpha2.5e-7 1.06 anchor and first unloading to1.05. Parent selected-state HP does not qualify child unloading or the complete path; no pressure/effective grip/release/stability/alpha independence/mesh-domain convergence/HF5.',
        closure_read_scope='Ordinary JSON/JSONL/source/docs and producer seals/stat only; no CSV, NPZ, NPY, gzip or media payload read/hash/decode, rendering, tests or mechanics; Git object I/O separate')
    state_rows = []
    for row in rows:
        observation = row['view_observation'] or {}
        force = (row.get('workpiece') or {}).get('force_on_lower_body_N', {}).get('total')
        state_rows.append([row['index'], row['original_target_index'], row['leg'], row['d_mm'],
            row['R_input_N'], row['q_out_mm'], force[1] if force is not None else None,
            observation.get('tip_to_raster_boundary_mm'), observation.get('minimum_boundary_distance_mm'),
            observation.get('medium_min_J'), observation.get('medium_max_abs_Hu_per_mm'),
            observation.get('right_medium_min_J'), row['relative_residual']])
    comparison = helper.get('same_input_comparison')
    comparison_rows = []
    for row in comparison['rows'] if comparison is not None else []:
        comparison_rows.append([row['metric'], row['unit'], row['loading_source_value'],
                                row['unloading_value'], row['unloading_minus_loading']])
    available = lambda label, name: f'[{label}](<{name}>)' if (stage/name).is_file() else label+'（未生成）'
    limits = {key: protocol[key] for key in (
        'controller_seconds', 'viewer_seconds', 'helper_seconds', 'outer_seconds',
        'sampled_RSS_bytes', 'cpu_thread_limit', 'cpu_thread_environment')}
    lines = [f'# {CARD}：新α圆形工件首次1.06→1.05 mm卸载', '',
        f'2026-10-20准备（Asia/Seoul）；执行 **{outcome.upper()}**；五图QA `{visual_status}`／完成 `{qa_complete}`；阶段完成 `{stage_complete}`。实际UTC保留在原凭证与闭卡JSON。', '',
        '整体目标是将LF几何接入独立、可恢复的大变形/TMC评估，得到可审查的结构变形、工件作用及加载卸载响应。前序ALPHA1已在α=2.5e-7从零完成13个加载目标；AREF1只对父峰值一态完成其独立参考。本轮关注同一新α下首次回程的实际行为，不更改α或移植旧α结果。', '',
        '使用原公开保存态延伸接口，从新α成功父accepted12/global12/loading1.06 mm重新核验平衡、状态SHA和有符号R，再执行首个1.05 mm卸载目标。完整13加载目标作为任务前缀保留，任务kind从load_only转为ordered_cycle，追加1.05；input.target仍为峰值1.06。其余物理条件、非clock数值设置及原门保持；不从零重放前缀。', '',
        '固定圆形工件r9 mm、圆心(80,40) mm、right92 mm、Lr80 mm、α=2.5e-7、下半域92×40 mm、h0.5 mm、厚20 mm、E1 MPa、nu0.3、plane strain、gamma1e-6及原支撑、平均端口和对称保持。父为从零13态，无parent continuation；本child只记录本次真实首次卸载转段，不伪造旧嵌套续算。', '',
        f'实际production `{shown(closure["production_status"])}`、helper `{shown(helper.get("status"))}`、outer `{launch["status"]}`；最终阶段 `{shown(helper.get("phase"))}`。保存接受态 `{shown(saved_count)}`，on_accept `{shown(helper.get("accepted_states"))}`，所有实际内部二分态保留。缺失result记null，只有进度回调的情形单独记录。', '',
        table(['child行', 'global目标', 'raw leg', 'd mm', 'R N', 'q_out mm', '工件总Fy N', '尖端距离 mm',
               'Q1最小距 mm', '介质minJ', '介质maxabsHu 1/mm', '右介质minJ', '原相对残差'], state_rows), '',
        f'原门 `{shown(protocol["gates"])}`；缓存核对 `{shown(helper.get("cached_production_gates"))}`。global_force_balance≤1e-6是原wrapper验收门；native均值约束界、残差、fixed split8e-11 mm和J>0均保持。实际生产调用 `{shown(closure["production_call_counts"])}`；原收敛计数 `{shown(closure["convergence_counts"])}`，不扣除锚重新核验或内部回溯工作。', '',
        '## 同输入1.05 mm的加载与卸载', '',
        '只与同新α父ALPHA1接受行11／global11／raw leg loading的1.05 mm作原值对照；不沿用旧αSTEP10的resume_origin来源。原加载与新卸载是两个不同状态，保留各自SHA、符号与来源，不以同输入去重。差值定义为卸载−加载，不插值，不增加相等性、恢复率、耗散能、α独立或可逆性门。', '',
        table(['原指标', '单位', '原加载值', '新卸载值', '卸载−加载'], comparison_rows), '',
        '完整原值、力分量、诊断和来源见'+available('状态表', 'run_001/state_table.json')+'及闭卡JSON；q_out为加权端口位移，不是间隙。输入R和material/Hu/total Fx/Fy保留下半模型有符号原值，不镜像倍增。', '',
        '## 实际×1变形、力、介质与收敛', '',
        '成功后原纯viewer按实际接受顺序生成4PNG和实际N帧GIF，原收敛图再生成1PNG，总计五张新PNG，不增加α比较第六图。静态比较第二态、fields和right-medium均显示实际LAST卸载端点1.05 mm；真实argmax peak_index仍保留，但不以峰值锚1.06替代卸载末态。legacy文件名peak_fields.png只作文件身份，标题明确LAST。',
        '全结构与动画只作对称镜像，数值仍为下半；实际坐标×1。尖端按参考(80,30)跟踪。Q1距离无符号，不能当作解析圆间隙或接触／释放证明；相交、roundoff near-touch、区域重叠和包含未测试状态分别保留。',
        '右条带仍为固定参考x89..92六列480单元、全部80行统计。局部图裁剪不改变全条带极值；J均值图不等于九点minJ，Hu范数图不等于maxabs component，介质区Hu不等于全模型Hu，右条带最大节点位移不是尖端间隙。', '',
        f'原路径旗标 `{shown(path_flags)}`；只完成当前请求后缀，不能由unload_endpoint_reached断言卸载至零、自由释放或完整循环。父13目标前缀未在本child执行；原完整路径标志保持原值。', '',
        'AREF1父峰值HP80/120只保其原状态和同一PORT方向范围，不迁移为本child卸载态独立参考。本轮新HP、测试、默认修改／安装及API关联均为0；节点弱力不是连续表面牵引或压力，不授有效夹持、稳定性、α独立、网格／域宽收敛、释放或HF5资格。', '',
        decision.get('interpretation_md', ''), '',
        f'原资源配置 `{shown(limits)}`；helper实际 `{shown(helper.get("elapsed_seconds"))}`、outer `{shown(launch.get("elapsed_seconds"))}` 秒，进程树采样峰值 `{shown(launch.get("peak_sampled_tree_RSS_bytes"))}` B，清理 `{shown(launch.get("cleanup_verified"))}`。四库线程上限16为配置，不等于实测16核利用率；纯viewer原8 GiB子限保持。', '',
        f'原窗口封存 `{len(outputs)}` 份输出／`{closure["sealed_output_bytes"]}` B，seal `{shown(helper.get("output_identity_seal"))}`。闭卡只继承producer seal并stat，不在窗口后打开或重新哈希科学数组、CSV、gzip或媒体。helper错误 `{shown(helper.get("error"))}`；API `{shown(helper.get("API_failure"))}`；outer `{shown(launch.get("error"))}`。',
        '生产、执行、像素QA和阶段完整完成分别报告，真实partial和原失败历史保留。首个终端错误后停止后续科学与显示，无外部重试、修复重跑、延期、force、回滚或删除。', '']
    for name in media:
        lines += [f'![{name}](<run_001/{name}>)', '']
    lines += ['既有父加载与独立参考只链接：'+available('ALPHA1加载记录', '../lf_circle_tip_alpha_001/RESULTS.md')+' · '
        +available('AREF1父单峰参考', '../lf_circle_tip_alpha_reference_001/RESULTS.md')+'。旧媒体不重开。', '',
        '入口：'+' · '.join(available(label, name) for label, name in (
            ('人工页', 'run_001/REVIEW.md'), ('原结果', 'run_001/'+LABEL+'/result.json'),
            ('原响应', 'run_001/'+LABEL+'/response.json'), ('收敛记录', 'run_001/convergence/convergence.json'),
            ('outer', 'step_launch.json'), ('helper', 'run_001/execution_receipt.json'),
            ('实际审查', 'author/ACTUAL_REVIEW.md'), ('像素记录', 'author/pixel_QA.json')))
        +' · [闭卡JSON](<author/closure.json>) · [后续](<NEXT_STEPS.md>)', '',
        '后续：'+decision['next_step'], '',
        'origin保持https://github.com/dudaxing/Compliant-TO-TMC.git，后续在main。先读README、CURRENT_STATUS、RESUME_DEVELOPMENT与本卡RESULTS／NEXT_STEPS；不要重跑已关闭launcher。异路径恢复采用同机local Git对象fetch／ff-only，远端main身份另核；这不是独立机器或远端对象下载恢复测试。', '']
    next_text = decision.get('next_steps_md') or ('# '+CARD+' 后续\n\n'+decision['next_step']+
        '\n\n这里只记录建议，不启动新的物理目标或资源窗口，原门保持。\n')
    generated = {'RESULTS.md': ('\n'.join(lines).rstrip()+'\n').encode('utf-8'),
        'NEXT_STEPS.md': (next_text.rstrip()+'\n').encode('utf-8'), 'author/closure.json': encoded(closure)}
    old_fronts = {name: subprocess.check_output(GIT+['show', BASE+':'+name], cwd=ROOT) for name in FRONTS}
    history, prefixed = dict(source_baseline_commit=BASE, files=[]), {}
    for name, old in old_fronts.items():
        assert (ROOT/name).read_bytes() == old, 'Front differs from baseline: '+name
        link = os.path.relpath(stage/'RESULTS.md', (ROOT/name).parent).replace('\\', '/')
        prefix = (f'> 2026-10-20 {CARD} **执行{outcome.upper()}**／五图QA {visual_status}／阶段完成{stage_complete}：'
            f'新α2.5e-7从已验证父峰值1.06 mm首次卸载至1.05 mm；生产 {shown(closure["production_status"])}，保存态 {shown(saved_count)}。'
            f'父13目标未重放，旧父HP不授卸载态，所有资格和历史保持；见[实际记录](<{link}>)。原历史说明保留如下。\n\n').encode('utf-8')
        prefixed[name] = prefix+old
        assert prefixed[name].endswith(old) and prefixed[name].count(old) == 1
        history['files'].append(dict(path=name, old_bytes=len(old), old_sha256=sha256(old).hexdigest(),
            prefix_bytes=len(prefix), raw_suffix_preserved_once=True))
    generated['author/front_history.json'] = encoded(history)
    for name, raw in generated.items():
        assert all(line.rstrip(b' \t') == line for line in raw.splitlines()), name
        assert not (stage/name).exists(), 'Preserve existing closure document: '+name
    for name, raw in generated.items():
        (stage/name).write_bytes(raw)
    for name, raw in prefixed.items():
        (ROOT/name).write_bytes(raw)
    (stage/'author/close_step.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps(dict(status='closed', execution_status=outcome, stage_complete=stage_complete,
        saved_accepted_states=saved_count, fronts=len(FRONTS)), ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
