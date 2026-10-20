"""Close L-CTIPALPHA1 using ordinary records and original producer seals/stat only."""
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
STAGE = 'lf_data_preparation/native_interface_001/lf_circle_tip_alpha_001'
BASE = '0687a138ca60ac09f6555b09132646e8a30bd5d7'
CARD, LABEL = 'L-CTIPALPHA1', 'wave_circle_tip_alpha1'
FRONTS = ('README.md', 'hf_repo/README.md', 'docs/CURRENT_STATUS.md',
    'docs/PHYSICAL_FUNCTION_PROGRESS.md', 'docs/RESUME_DEVELOPMENT.md',
    'docs/L_USE1_NEXT_STEP_PLAN.md', 'docs/L_BFWD1_NEXT_STEP_PLAN.md')
MEDIA = ('view/comparison.png', 'view/distances_forces.png', 'view/peak_fields.png',
    'view/right_medium.png', 'convergence/convergence.png', 'alpha_comparison/comparison.png')
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
    comparison = read('run_001/alpha_comparison/comparison.json', optional=True)
    review, decision = read('author/ACTUAL_REVIEW.json'), read('author/NEXT_DECISION.json')
    pixel = read('author/pixel_QA.json', optional=True)
    assert protocol['card'] == launch['card'] == CARD
    assert protocol['source_baseline_commit'] == BASE
    assert launch['invocations'] == 1 and launch['status'] in ('pass', 'not_pass')
    assert not helper or (helper['card'] == CARD and helper['protocol_sha256'] == launch['protocol_sha256'])
    assert review['status'].startswith('pass') and not review.get('blockers', review.get('blocking_findings', []))
    outcome = 'pass' if launch['status'] == helper.get('status') == 'pass' else 'not_pass'
    assert decision['execution_status'] == review['execution_status'] == outcome
    assert isinstance(decision['next_step'], str) and decision['next_step'].strip()
    outputs = helper.get('outputs') or {}
    for name, seal in outputs.items():
        assert (ROOT/name).stat().st_size == seal['bytes'], name
    media = {name: outputs[STAGE+'/run_001/'+name] for name in MEDIA if STAGE+'/run_001/'+name in outputs}
    GIF = 'view/'+LABEL+'/actual_states.gif'
    gif_seal = outputs.get(STAGE+'/run_001/'+GIF)
    states = saved['states'] if saved is not None else []
    observed = {row['index']:row for row in summary['rows']} if summary is not None else {}
    rows = []
    for index,state in enumerate(states):
        observation = observed.get(index)
        if observation is not None:
            assert (observation['state_sha256'],observation['d_mm'],observation['original_target_index'],observation['leg']) == (
                state['state_sha256'],state['d'],state['original_target_index'],state['leg'])
            assert (observation['R_input_N'],observation['q_out_mm']) == (state['R_input'],state['q_out'])
        rows.append(dict(index=index,original_target_index=state.get('original_target_index'),
            leg=state.get('leg'),d_mm=state['d'],state_sha256=state['state_sha256'],
            is_original_target=state.get('is_original_target'),R_input_N=state['R_input'],q_out_mm=state['q_out'],
            workpiece=state.get('workpiece'),minimum_J=state.get('minimum_J'),
            relative_residual=state.get('relative_residual'),constraint_residual_mm=state.get('constraint_residual'),
            constraint_bound_mm=state.get('constraint_bound'),relative_global_force_balance=state.get('relative_global_force_balance'),
            newton_checks=state.get('newton_checks'),bisection_depth=state.get('bisection_depth'),view_observation=observation))
    progress_rows = []
    progress_file = stage/'run_001/accepted_progress.jsonl'
    if saved is None and progress_file.is_file():
        progress_rows = [json.loads(line) for line in progress_file.read_text(encoding='utf-8').splitlines() if line.strip()]
    saved_count = len(states) if saved is not None else None
    path_keys = ('path_kind','targets_mm','target_origin','reached_displacement','path_completed',
        'loading_peak_reached','task_target_executed','full_original_path_completed','full_extended_path_completed',
        'unload_endpoint_reached')
    path_flags = {key:saved.get(key) for key in path_keys} if saved is not None else None
    visual_status = pixel.get('status') if pixel is not None else 'not_provided'
    expected_pngs = {STAGE+'/run_001/'+name for name in MEDIA}
    qa_complete = False
    if pixel is not None:
        assert pixel['card'] == CARD
        inspections = pixel['media']
        assert len(inspections) <= 6 and len({row['path'] for row in inspections}) == len(inspections)
        assert {row['path'] for row in inspections} <= expected_pngs
        assert all(row['inspections'] == 1 for row in inspections)
        assert pixel['inspections'] == len(inspections)
        qa_complete = len(inspections) == 6 and visual_status.startswith('pass')
    if outcome == 'pass':
        assert saved is not None and saved['status'] == 'success'
        assert saved['path_kind'] == 'load_only' and saved['path_completed'] and saved['reached_displacement'] == 1.06
        assert saved['targets_mm'] == protocol['targets_mm'] and len(protocol['targets_mm']) == 13
        assert saved_count >= 13 and saved_count == helper['accepted_states']
        assert helper['cached_production_gates']['passed'] and launch['cleanup_verified'] is True
        assert helper['default_installations'] == helper['new_tests'] == helper['HP_calls_by_wrapper'] == 0
        assert comparison is not None and comparison['counts']['matched_pairs'] == comparison['counts']['baseline_rows'] == 13
        assert comparison['counts']['new_rows'] == saved_count
        assert len(media) == 6 and gif_seal is not None and helper['actual_GIF_frames'] == saved_count
    stage_complete = outcome == 'pass' and qa_complete
    closure = dict(card=CARD,status=outcome+'_closed',execution_status=outcome,execution_closed=True,
        visual_QA_status=visual_status,visual_QA_complete=qa_complete,stage_complete=stage_complete,
        created_utc=datetime.now(timezone.utc).isoformat(),prepared_client_local_date='2026-10-20',
        report_client_local_date='2026-10-20',report_timezone='Asia/Seoul',source_baseline_commit=BASE,
        science_version='0.5.0',science_baseline_commit='b1334bb6a83ba9a0efab7bdba7bd39722146f024',
        protocol_sha256=launch['protocol_sha256'],outer_status=launch['status'],helper_status=helper.get('status'),
        production_status=saved.get('status') if saved is not None else None,
        terminal=review.get('terminal'),helper_phase=helper.get('phase'),helper_error=helper.get('error'),
        outer_error=launch.get('error'),outer_stop_reason=launch.get('stop_reason'),API_failure=helper.get('API_failure'),
        zero_start=helper.get('zero_start'),saved_parent_or_state_used=helper.get('saved_parent_or_state_used'),
        extend_path=helper.get('extend_path'),alpha=task['regularization']['alpha'],baseline_alpha=5e-7,
        task=task,requested_targets_mm=protocol['targets_mm'],path_flags=path_flags,
        saved_accepted_states=saved_count,helper_on_accept_count=helper.get('accepted_states'),rows=rows,
        progress_only_rows_when_saved_result_absent=progress_rows,
        saved_count_basis='len(result.states); null if absent; callback progress reported separately, not substituted for saved equilibrium evidence',
        last_saved_state=rows[-1] if rows else None,original_gates=protocol['gates'],
        cached_production_gates=helper.get('cached_production_gates'),settings=protocol['settings'],
        actual_settings=helper.get('actual_settings'),wrapper_call_counts=helper.get('call_counts'),
        production_call_counts=saved.get('call_counts') if saved is not None else helper.get('production_call_counts'),
        convergence_counts=convergence.get('counts') if convergence is not None else None,
        baseline_file=protocol['baseline_file'],alpha_comparison=comparison,
        comparison_source=helper.get('alpha_comparison_source'),
        view_status=views.get('status') if views is not None else None,view_actual_counts=helper.get('view_actual_counts'),
        actual_GIF_frames=helper.get('actual_GIF_frames'),actual_total_PNGs=helper.get('actual_total_PNGs'),
        right_medium=summary.get('right_medium') if summary is not None else None,
        available_sealed_visualizations=media,available_sealed_GIF=gif_seal,
        pixel_QA_observations=pixel.get('observations') if pixel is not None else None,actual_review_status=review['status'],
        helper_elapsed_seconds=helper.get('elapsed_seconds'),outer_elapsed_seconds=launch.get('elapsed_seconds'),
        peak_sampled_tree_RSS_bytes=launch.get('peak_sampled_tree_RSS_bytes'),cleanup_verified=launch.get('cleanup_verified'),
        sealed_output_files=len(outputs),sealed_output_bytes=sum(row['bytes'] for row in outputs.values()),
        output_identity_seal=helper.get('output_identity_seal'),new_tests=helper.get('new_tests'),
        default_installations=helper.get('default_installations'),HP_calls_by_wrapper=helper.get('HP_calls_by_wrapper'),
        independent_reference=response.get('independent_reference') if response is not None else None,
        producer_flags=response.get('producer_flags') if response is not None else None,
        next_decision=decision,next_step=decision['next_step'],
        qualification_scope='Only this new-alpha zero-start load-only experiment and actual accepted states; historical segmented baseline versus one zero-start run is not a pure-alpha CPU comparison; no inherited old-alpha HP, unloading, pressure, effective grip, release, stability, alpha convergence, full-cycle reference, mesh/domain convergence or HF5 upgrade',
        closure_read_scope='Ordinary JSON/JSONL/source/docs and original producer seals/stat only; no CSV, NPZ, NPY, gzip or media payload reading/hashing/decoding, rendering, tests or mechanics; Git object I/O separate')
    state_table_rows = []
    for row in rows:
        observation = row['view_observation'] or {}
        force = (row.get('workpiece') or {}).get('force_on_lower_body_N',{}).get('total')
        state_table_rows.append([row['index'],row['original_target_index'],row['leg'],row['is_original_target'],
            row['d_mm'],row['R_input_N'],row['q_out_mm'],force[1] if force is not None else None,
            observation.get('tip_to_raster_boundary_mm'),row['minimum_J'],row['relative_residual'],row['bisection_depth']])
    pair_table_rows = []
    for pair in comparison['pairs'] if comparison is not None else []:
        for metric in ('R_input_N','q_out_mm','total_body_Fy_N','material_body_Fy_N','regularization_body_Fy_N',
                       'tip_to_raster_boundary_mm','medium_min_J','medium_max_abs_Hu_per_mm',
                       'right_medium_min_J','right_medium_max_abs_Hu_per_mm'):
            values = pair['metrics'][metric]
            pair_table_rows.append([pair['d_mm'],pair['baseline_raw_leg'],metric,
                values['baseline_value'],values['new_value'],values['new_minus_baseline']])
    available = lambda label,name: f'[{label}](<{name}>)' if (stage/name).is_file() else label+'（未生成）'
    baseline_link = os.path.relpath(ROOT/protocol['baseline_file'],stage).replace('\\','/')
    lines = [f'# {CARD}：减半α的从零加载实验','',
        f'2026-10-20准备（Asia/Seoul）；执行 **{outcome.upper()}**；图像QA `{visual_status}`，六图检查完成 `{qa_complete}`，本阶段完整完成 `{stage_complete}`。实际完成UTC保留在原执行凭证及闭卡JSON，旧历史日期不修改。','',
        '整体目标是将LF几何接入独立、可恢复的大变形/TMC评估，形成可审查的结构变形、工件作用力及加载卸载响应。前一步节点力追溯发现Hu局部贡献有明显抵消；本轮用真实单参数实验观察正则化权重变化对作用力、接近位置和介质压缩的影响，帮助选择后续物理实验。','',
        '本轮唯一物理改动：从原STEP10的load_only完整任务复制，α从5e-7改为2.5e-7；另改四项实验metadata并单列新controller时钟14400秒。圆形固定工件r9 mm、圆心(80,40) mm、right92 mm、Lr80 mm、E=1 MPa、nu=0.3、plane strain、gamma=1e-6、厚度20 mm、原网格、支撑/平均端口/对称及其余物理条件保持。非clock数值设置和原验收门保持。','',
        '使用相同LF几何从零调用现有evaluate_native；不从旧α保存态热续、不移植旧力、切线或矩阵。13个原绝对加载目标为[0,.25,.50,.75,.90,.95,.98,1.00,1.02,1.03,1.04,1.05,1.06] mm，不含卸载。原内部回溯/二分保留，所有实际接受态及原拒绝/失败历史照实保存；minimum_increment=.00625 mm和原浮点判断保持，末端.01 mm若失败且半步.005低于原限值，按原规则停止。','',
        f'实际执行：production `{shown(closure["production_status"])}`，helper `{shown(helper.get("status"))}`，outer `{launch["status"]}`；最终阶段 `{shown(helper.get("phase"))}`。保存接受态 `{shown(saved_count)}`，on_accept回调 `{shown(helper.get("accepted_states"))}`；接受态N按实际统计，不硬写为13。缺失result时保存态数记null，只有原回调进度的情况单独记录。','',
        table(['接受行','原目标','原leg','原目标态','d mm','输入R N','q_out mm','下半工件总Fy N','尖端距离 mm','全模型minJ','相对残差','二分深度'],state_table_rows),'',
        f'实际路径标志 `{shown(path_flags)}`。原结果标志按原值保留；成功的本实验完整加载与未实施的卸载、其他α路径和整项目资格分别记录，不跨范围授予完成。','',
        f'原验收门 `{shown(protocol["gates"])}`；缓存检查 `{shown(helper.get("cached_production_gates"))}`。global_force_balance≤1e-6是原wrapper验收门，不能仅称作诊断；平均约束用原native bound，固定拆分位移门8e-11 mm、J>0与残差门均保持。生产调用 `{shown(closure["production_call_counts"])}`；新收敛原计数 `{shown(closure["convergence_counts"])}`，不扣除实际内部工作。','',
        '## 与原α的同目标对照','',
        f'原基线固定为[PATH1统一普通JSON](<{baseline_link}>)中13个origin/loading原目标及其SHA，新α按同原目标index和精确d配对。二分接受态保留在新曲线及原收敛历史中，不插值补配。完整23个原字段、每态来源/SHA及原值/差量见'+available('比较JSON','run_001/alpha_comparison/comparison.json')+'和'+available('比较人工页','run_001/alpha_comparison/REVIEW.md')+'。下表选列部分同定义标量；差量统一为新α−原α。','',
        table(['d mm','原基线raw leg','原metric','原α原值','新α原值','新−原'],pair_table_rows),'',
        '原零态的leg为origin；分段基线中的resume_origin及全部来源保留，不用显示身份改写。原α加载来自先前分段续算后的汇总，新α是一次从零加载；原分段包含锚重新核验，PATH1的全路径成本还含卸载。因此总CPU/求解次数不能直接归因为α，也不作纯α性能排名。','',
        '保留符号、小负值、非单调量和抵消，不裁零、不吸附零值，不增参数相等/收敛门。两点参数实验只作描述，曲线接近或重合不证明α独立；新参数不继承原α峰值的HP80/120通过。','',
        '## 实际显示、作用力与介质','',
        '成功后原pure viewer只读取本次新模型/状态缓存，输出四张实际×1变形/距离与力/场/右介质PNG和实际N帧GIF；原收敛绘图输出一张PNG，纯dict比较再输出一张PNG，共六张新图。各新PNG最多人工检查一次；新GIF帧数采用原producer检查，不额外解码，旧媒体未打开。若先终端失败，则停止后续显示，只有实际已生成并原窗口封存的产品才能列入本记录。','',
        '完整结构和动画的镜像只作显示，数值不镜像加倍。输入R与工件material/Hu/total Fx/Fy是有符号下半模型原值，Hu弱式贡献不是连续表面压力或有效夹持力。q_out是加权端口位移，不是间隙。尖端按参考(80,30)跟踪；距离是unsigned Q1栅格边界距离，不代替解析圆有符号间隙；相交、near-touch和区域重叠分别记录，包含关系仍未测试。','',
        '右介质为参考x89..92的六列480cells，全部80行统计，局部图可裁剪。J图的cell均值不能替代九点minimum J；Hu范数场图不等于maxabs Hu component，介质区max|Hu|也不是全模型max|Hu|。右条带最大节点位移不是尖端间隙，其极值节点可变化；本卡不授域宽充分或边界污染结论。','',
        decision.get('interpretation_md',''),'',
        f'资源与停止：controller14400秒、显示共享900秒、helper16200秒、outer16260秒；实际helper `{shown(helper.get("elapsed_seconds"))}`、outer `{shown(launch.get("elapsed_seconds"))}` 秒；进程树采样峰值 `{shown(launch.get("peak_sampled_tree_RSS_bytes"))}` B/64 GiB，清理 `{shown(launch.get("cleanup_verified"))}`。四库线程上限16是配置，不是实测16核利用率；原viewer内部8 GiB子限保持。','',
        f'原窗口封存 `{len(outputs)}` 份输出、`{closure["sealed_output_bytes"]}` B，seal `{shown(helper.get("output_identity_seal"))}`；闭卡只继承原producer seal并stat，不在窗口后哈希或解码数组/媒体。新测试 `{shown(helper.get("new_tests"))}`、默认安装 `{shown(helper.get("default_installations"))}`、wrapper新HP `{shown(helper.get("HP_calls_by_wrapper"))}`。','',
        f'原错误：helper `{shown(helper.get("error"))}`；API `{shown(helper.get("API_failure"))}`；outer `{shown(launch.get("error"))}`。production、执行、像素QA和阶段完整完成分开保留。首个终端错误停止后续科学/显示，保真实partial；无外部重试、修复重跑、延期、force、新HP、测试、API关联、默认源码改动、安装、回滚或删除。','',
        '资格保持：本轮只评估新α从零加载及实际接受态，不授卸载、压力、有效夹持、自由释放、稳定性、α收敛、完整加载卸载路径参考、网格/域宽收敛或HF5资格。旧α结果、原成功/失败历史和所选旧峰值参考范围保持。','']
    for name in media:
        lines += [f'![{name}](<run_001/{name}>)','']
    if gif_seal is not None:
        lines += [f'![实际接受态变形动画](<run_001/{GIF}>)','']
    lines += ['后续决策：'+decision['next_step'],'',
        '跨机器继续：origin保持https://github.com/dudaxing/Compliant-TO-TMC.git，后续开发在main。clone后先读README、docs/CURRENT_STATUS.md、docs/RESUME_DEVELOPMENT.md与本目录RESULTS/NEXT_STEPS，核对protocol、授权、任务及保存态来源后安排新工作。不要重跑已关闭launcher或把显示汇总当作新求解起点。恢复核对为同机异目录local Git objects fetch/ff-only，远程main单独核验，不称为异机科学重算。','',
        '入口：'+' · '.join(available(label,name) for label,name in (
            ('人工页','run_001/REVIEW.md'),('原结果','run_001/'+LABEL+'/result.json'),
            ('原响应','run_001/'+LABEL+'/response.json'),('状态表','run_001/state_table.json'),
            ('新显示摘要','run_001/view/'+LABEL+'/summary.json'),('原收敛','run_001/convergence/convergence.json'),
            ('参数比较','run_001/alpha_comparison/comparison.json'),('outer','step_launch.json'),
            ('helper','run_001/execution_receipt.json'),('实际审查','author/ACTUAL_REVIEW.md'),
            ('像素记录','author/pixel_QA.json')))+' · [闭卡JSON](<author/closure.json>) · [后续](<NEXT_STEPS.md>)','']
    next_text = decision.get('next_steps_md') or ('# '+CARD+' 后续\n\n'+decision['next_step']+
        '\n\n这里只记录建议，不启动新目标或新窗口；先明确范围、物理定义与资源，原门保持。\n')
    generated = {'RESULTS.md':('\n'.join(lines).rstrip()+'\n').encode('utf-8'),
        'NEXT_STEPS.md':(next_text.rstrip()+'\n').encode('utf-8'),'author/closure.json':encoded(closure)}
    old_fronts = {name:subprocess.check_output(GIT+['show',BASE+':'+name],cwd=ROOT) for name in FRONTS}
    front_history = dict(source_baseline_commit=BASE,files=[])
    prefixed = {}
    for name,old in old_fronts.items():
        assert (ROOT/name).read_bytes() == old,'Front differs from baseline: '+name
        link = os.path.relpath(stage/'RESULTS.md',(ROOT/name).parent).replace('\\','/')
        prefix = (f'> 2026-10-20 {CARD} **执行{outcome.upper()}**／图像QA {visual_status}／六图QA完成{qa_complete}／阶段完成{stage_complete}：仅α由5e-7减至2.5e-7，从零请求原13个加载目标至1.06 mm；'
            f'生产 {shown(closure["production_status"])}、实际保存态 {shown(saved_count)}，保留partial及原内部历史，同定义差量只描述；旧α的HP不继承，不以分段基线总CPU作纯α性能判断。'
            f'见[实际记录](<{link}>)。原历史说明保留如下。\n\n').encode('utf-8')
        prefixed[name] = prefix+old
        assert prefixed[name].endswith(old) and prefixed[name].count(old) == 1
        front_history['files'].append(dict(path=name,old_bytes=len(old),old_sha256=sha256(old).hexdigest(),
            prefix_bytes=len(prefix),raw_suffix_preserved_once=True))
    generated['author/front_history.json'] = encoded(front_history)
    for name,raw in generated.items():
        assert all(line.rstrip(b' \t') == line for line in raw.splitlines()),name
        assert not (stage/name).exists(),'Preserve existing closure document: '+name
    for name,raw in generated.items():
        (stage/name).write_bytes(raw)
    for name,raw in prefixed.items():
        (ROOT/name).write_bytes(raw)
    (stage/'author/close_step.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps(dict(status='closed',execution_status=outcome,stage_complete=stage_complete,
        saved_accepted_states=saved_count,fronts=len(FRONTS)),ensure_ascii=False),flush=True)


if __name__ == '__main__':
    main()
