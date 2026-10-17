"""Close one saved circle HP audit from ordinary records and original seals."""
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
STAGE = 'lf_data_preparation/native_interface_001/lf_circle_reference_001'
BASE = '11a8b49ebef7d18fef17ffe6c9e365ce574de074'
CARD = 'L-CREF1'
FRONTS = ['README.md', 'hf_repo/README.md', 'docs/CURRENT_STATUS.md',
    'docs/PHYSICAL_FUNCTION_PROGRESS.md', 'docs/RESUME_DEVELOPMENT.md',
    'docs/L_USE1_NEXT_STEP_PLAN.md', 'docs/L_BFWD1_NEXT_STEP_PLAN.md']


def read(name, *, optional=False):
    path = ROOT/STAGE/name
    return None if optional and not path.is_file() else json.loads(path.read_bytes())


def write(name, value):
    (ROOT/STAGE/name).write_text(value, encoding='utf-8', newline='\n')


def shown(value):
    return '未提供' if value is None else str(value)


def main():
    protocol, launch = read('protocol.json'), read('reference_launch.json')
    receipt = read('run_001/reference/execution_receipt.json', optional=True)
    summary = read('run_001/reference/summary.json', optional=True)
    lifecycle = read('run_001/reference/lifecycle.json', optional=True)
    row = read('run_001/reference/accepted_005/summary.json', optional=True)
    observation = read('run_001/reference/reference_observations.json', optional=True)
    review = read('author/ACTUAL_REVIEW.json')
    pixel = read('author/pixel_QA.json', optional=True)
    assert protocol['card'] == launch['card'] == CARD
    assert launch['status'] in ('pass','not_pass')
    assert receipt is None or receipt['card'] == CARD
    assert receipt is None or receipt['status'] in ('pass','not_pass')
    assert receipt is None or receipt['protocol_sha256'] == launch['protocol_sha256']
    assert pixel is None or pixel['card'] == CARD
    assert review['status'].startswith('pass') and not review.get('blockers',review.get('blocking_findings',[]))
    assert protocol['source_baseline_commit'] == BASE
    assert protocol['selected_child_accepted_index'] == 1 and protocol['original_target_indices'] == [5]
    assert protocol['targets_mm'] == [1.15] and protocol['expected_new_HP_calls'] == 2
    assert not subprocess.check_output(['git','diff',BASE,'--name-only','--','hf_repo/src'],cwd=ROOT)
    helper, reference, life = receipt or {}, summary or {}, lifecycle or {}
    outcome = 'pass' if launch['status'] == helper.get('status') == 'pass' else 'not_pass'
    entries = observation.get('entries') if observation is not None else None
    if outcome == 'pass':
        assert reference.get('status') == life.get('status') == 'pass'
        assert launch['exit_code'] == 0 and launch['stop_reason'] is None and launch['invocations'] == 1
        assert helper['HP_calls_started'] == helper['HP_calls_completed'] == 2
        assert helper['accepted_mechanical_states_completed'] == helper['workpiece_states_completed'] == 1
        assert reference['accepted_states'] == 1 and reference['gates'] == protocol['gates']
        assert row['status'] == 'pass' and row['index'] == 5 and row['target_mm'] == 1.15
        assert row['state_sha256'] == protocol['selected_state_sha256']
        assert observation['accepted_child_index'] == 1 and observation['original_target_index'] == 5
        assert observation['state_sha256'] == protocol['selected_state_sha256']
        assert len(entries) == 10 and all(entry['pass_gate'] is True for entry in entries)
        assert helper['plot_started'] == helper['plot_completed'] == 1
    outputs = helper.get('outputs')
    png_name = STAGE+'/run_001/reference/reference_observations.png'
    image = None
    if png_name in (outputs or {}):
        assert (ROOT/png_name).stat().st_size == outputs[png_name]['bytes']
        image = outputs[png_name]
    if outcome != 'pass':
        next_step = ('先依据实际停止阶段、原错误与已完成HP/门/绘图数定位问题。保留实际部分参考和原生产成功；'
            '不修写原结果、不自动重试、修复重跑、延期或force。显示阶段失败也不能据此重做已通过HP。')
    else:
        next_step = ('本次只核定已保存圆形1.15 mm峰值和原PORT方向；先结合本参考误差、既有实际变形、'
            '距离、分区J、材料/Hu/总工件力与收敛成本，确定下一次只追加一个绝对加载目标或先做针对性诊断。'
            '具体目标由实际结果审阅后选择，本页不锁定新数值、不执行新计算；不例行给每个保存态补HP。')
    closure = dict(card=CARD,status=outcome+'_closed',execution_status=outcome,execution_closed=True,
        created_utc=datetime.now(timezone.utc).isoformat(),source_baseline_commit=BASE,
        science_version='0.5.0',science_baseline_commit='b1334bb6a83ba9a0efab7bdba7bd39722146f024',
        protocol_sha256=launch['protocol_sha256'],outer_status=launch['status'],helper_status=helper.get('status'),
        summary_status=reference.get('status'),lifecycle_status=life.get('status'),
        selected_child_accepted_index=1,original_target_index=5,target_mm=1.15,
        selected_state_sha256=protocol['selected_state_sha256'],
        HP_calls_started=helper.get('HP_calls_started'),HP_calls_completed=helper.get('HP_calls_completed'),
        accepted_mechanical_states_completed=helper.get('accepted_mechanical_states_completed'),
        workpiece_states_completed=helper.get('workpiece_states_completed'),
        checks_completed=life.get('checks_completed'),original_gates=protocol['gates'],
        plot_started=helper.get('plot_started'),plot_completed=helper.get('plot_completed'),
        observation_entries=entries,selected_reference_row=row,
        producer_record_unchanged=True,default_sources_unchanged=True,
        reference_qualification_scope=reference.get('qualification'),
        full_child_path_reference_pass=False,full_original_path_reference_pass=False,full_extended_path_reference_pass=False,
        pressure_qualified=False,clamp_qualified=False,contact_qualified=False,HF5_qualified=False,
        helper_elapsed_seconds=helper.get('elapsed_seconds'),outer_elapsed_seconds=launch.get('elapsed_seconds'),
        helper_sampled_peak_RSS_bytes=helper.get('sampled_peak_RSS_bytes'),
        outer_sampled_peak_tree_RSS_bytes=launch.get('peak_sampled_tree_RSS_bytes'),
        child_terminal_wall_seconds=launch.get('child_terminal_wall_seconds'),
        child_exit_code=launch.get('exit_code'),stop_reason=launch.get('stop_reason'),
        helper_error=helper.get('error'),outer_failure=launch.get('failure'),
        cleanup_scope='Actual cooperative child terminal and elapsed/RSS observations; no SUP2 or cleanup_verified contract',
        sealed_output_files=len(outputs) if outputs is not None else None,
        sealed_output_bytes=sum(value['bytes'] for value in outputs.values()) if outputs is not None else None,
        output_identity_seal=helper.get('output_identity_seal'),available_sealed_error_PNG=image,
        actual_review_status=review['status'],pixel_QA_status=pixel.get('status') if pixel is not None else None,
        pixel_QA_observations=pixel.get('observations') if pixel is not None else None,
        terminal=review.get('terminal'),next_step=next_step,
        read_scope='Ordinary JSON/MD/source only; scientific NPZ/gzip/CSV/media use original producer seals plus stat, no payload read/hash/decode',
        qualification_scope='One saved circle1.15 state and one PORT direction; no full path/all columns/stress/energy/new circle geometry/pressure/grip/release/stability/HF5')
    lines = [f'# {CARD}：圆形工件1.15 mm保存峰值独立参考','',
        f"实际执行 **{outcome.upper()}**：outer `{launch['status']}`、helper `{shown(helper.get('status'))}`、summary `{shown(reference.get('status'))}`、lifecycle `{shown(life.get('status'))}`。main基线 `{BASE}`，science 0.5.0／b1334保持。",'',
        '整体目标是普通LF几何进入独立HF的TMC前向力学。本步针对圆形峰值压缩及Hu贡献已明显增大的实际结果，复用B850逐状态数学审计与aa86工件投影，对唯一1.15 mm保存峰值做全单元HP80/120参考，检查已有力、方向切线、平衡与工件合力的数值可靠性。它不重做生产求解。','',
        f"对象为L-CSTEP2接受行1／全局目标5／loading1.15 mm，state SHA `{protocol['selected_state_sha256']}`。工件半径9 mm、圆心(71,40) mm、固定ux/uy及原材料、第三介质、正则化、网格、边界、端口和验收门保持。完整13440单元／27378DOF；圆形overlay继承L-CPREP1保存模型证据，仅核已保存模型一致性，未新增独立圆mask或边界资格。",'',
        f"HP启动/完成 `{shown(helper.get('HP_calls_started'))}`／`{shown(helper.get('HP_calls_completed'))}`；完成材料态 `{shown(helper.get('accepted_mechanical_states_completed'))}`、工件投影态 `{shown(helper.get('workpiece_states_completed'))}`，检查计数 `{shown(life.get('checks_completed'))}`，绘图启动/完成 `{shown(helper.get('plot_started'))}`／`{shown(helper.get('plot_completed'))}`。不存在的普通记录保留未提供，不按零或通过处理。",'',
        '原十五门：`'+str(protocol['gates'])+'`。覆盖材料/Hu/总局部力和全局力、实际固定兼容PORT方向切线、完整CSC系数组装身份及其方向作用、KKT力/均值作用、约束/残差/整体平衡和有符号工件/holding分区投影。只检查这一方向，不是所有切线列；独立解析能量仅归档，不比较候选能量，不授应力或能量资格。','',
        '|观察项|原归一化误差|原门|通过|','|---|---:|---:|---|']
    for entry in entries or []:
        lines.append('|'+ '|'.join(shown(entry.get(key)) for key in ('label','error','limit','pass_gate'))+'|')
    if entries is None:
        lines += ['|误差图普通记录未提供|未提供|未提供|未提供|']
    lines += ['',
        '图中十项是已计算参考记录的显示投影；零误差明确显示，不加地板、不修改原分母或阈值。完整逐元素/全局差值和工件核查保存在原封存gzip中，闭卡不重新打开或解码。','',
        '工件Fx/Fy仍是含材料和Hu的有符号弱式合力。legacy normal_force_on_lower_body_N是全局Fy，2absFy也不等于圆周局部法向压力或合格夹持力。原L-CSTEP2生产响应、路径标志和成功历史保持；本参考通过不自动授完整子段或完整前缀资格。','',
        f"实际审阅 `{review['status']}`；新PNG像素检查 `{shown(closure['pixel_QA_status'])}`，观察 `{shown(closure['pixel_QA_observations'])}`。",'']
    if image is not None:
        lines += ['![原参考误差与原门](run_001/reference/reference_observations.png)','']
    limits = protocol['phases']['reference']
    lines += [
        f"helper `{shown(helper.get('elapsed_seconds'))}` s／{limits['helper_seconds']} s，outer `{shown(launch.get('elapsed_seconds'))}` s／{limits['outer_seconds']} s；采样进程树峰值 `{shown(launch.get('peak_sampled_tree_RSS_bytes'))}` B／{protocol['sampled_RSS_bytes']} B；实际child wall `{shown(launch.get('child_terminal_wall_seconds'))}` s、exit `{shown(launch.get('exit_code'))}`、stop `{shown(launch.get('stop_reason'))}`。资源是合作停止和采样观察，不增加SUP2清理或硬抢占资格。",'',
        f"原窗口封存 `{shown(closure['sealed_output_files'])}` 份输出／`{shown(closure['sealed_output_bytes'])}` B，状态 `{shown(helper.get('output_identity_seal'))}`。后续科学gzip/NPZ/PNG只继承原seal并核大小，缺seal则停止发布。helper错误 `{shown(helper.get('error'))}`；outer错误 `{shown(launch.get('failure'))}`。",'',
        '本轮无新生产F/T、平衡求解、测试、默认安装、API关联或旧媒体重绘；不升级接触、压力、有效夹持、释放、稳定性或HF5资格。','',
        '下一步：'+next_step,'',
        '审查入口：[参考summary](run_001/reference/summary.json)、[逐态summary](run_001/reference/accepted_005/summary.json)、[误差普通JSON](run_001/reference/reference_observations.json)、[lifecycle](run_001/reference/lifecycle.json)、[封存回执](run_001/reference/execution_receipt.json)、[outer](reference_launch.json)、[实际审阅](author/ACTUAL_REVIEW.md)、[闭卡JSON](author/closure.json)。','',
        '既有实际变形与力：[L-CSTEP2人工页](../lf_circle_step_002/run_001/REVIEW.md)。此处仅链接旧媒体，不读取、重绘或重核旧像素。','']
    next_text='\n'.join(['# L-CREF1 后续','',f'实际独立参考执行 `{outcome}`。','',next_step,'',
        '保存态参考仅覆盖accepted1/global5/1.15 mm。旧生产结果与资格保持；下一阶段另按实际力学功能需求明确单目标、预算及记录，不自动重复参考或扩展资源。',''])
    old_fronts={name:subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT) for name in FRONTS}
    assert all((ROOT/name).read_bytes()==old for name,old in old_fronts.items())
    write('RESULTS.md','\n'.join(lines))
    write('NEXT_STEPS.md',next_text)
    write('author/closure.json',json.dumps(closure,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    history=dict(source_baseline_commit=BASE,files=[])
    for name,old in old_fronts.items():
        link=os.path.relpath(ROOT/STAGE/'RESULTS.md',(ROOT/name).parent).replace('\\','/')
        prefix=(f'> 2026-10-17 {CARD} **{outcome.upper()}**：圆形1.15 mm保存峰值独立参考；'
            f"HP启动/完成 {shown(helper.get('HP_calls_started'))}/{shown(helper.get('HP_calls_completed'))}。"
            f'保原生产历史及资格；见[实际记录]({link})。原历史说明保留如下。\n\n').encode('utf-8')
        (ROOT/name).write_bytes(prefix+old)
        current=(ROOT/name).read_bytes()
        assert current.endswith(old) and current.count(old)==1
        history['files'].append(dict(path=name,old_bytes=len(old),old_sha256=sha256(old).hexdigest(),
            prefix_bytes=len(prefix),raw_suffix_preserved_once=True))
    write('author/front_history.json',json.dumps(history,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(status='closed',execution_status=outcome,HP_calls_started=helper.get('HP_calls_started'),
        HP_calls_completed=helper.get('HP_calls_completed'),fronts=len(FRONTS)),ensure_ascii=False),flush=True)


if __name__=='__main__':
    main()
