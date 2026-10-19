"""Close the selected saved-state HP reference from ordinary records and original seals."""
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).resolve().parent
STAGE = 'lf_data_preparation/native_interface_001/lf_circle_tip_reference_001'
BASE = '8cf86e81e414866a7d5cb110e006c7088f94eb97'
CARD = 'L-CTIPREF1'
FRONTS = ['README.md', 'hf_repo/README.md', 'docs/CURRENT_STATUS.md',
    'docs/PHYSICAL_FUNCTION_PROGRESS.md', 'docs/RESUME_DEVELOPMENT.md',
    'docs/L_USE1_NEXT_STEP_PLAN.md', 'docs/L_BFWD1_NEXT_STEP_PLAN.md']
GIT = ['git', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false']


def read(name, *, optional=False):
    path = ROOT/STAGE/name
    return None if optional and not path.is_file() else json.loads(path.read_bytes())


def write(name, value):
    (ROOT/STAGE/name).write_text(value, encoding='utf-8', newline='\n')


def shown(value):
    return '未提供' if value is None else str(value)


def main():
    stage = ROOT/STAGE
    assert not (stage/'author/closure.json').exists(), 'Preserve the existing closed record'
    protocol, launch = read('protocol.json'), read('reference_launch.json')
    receipt = read('run_001/reference/execution_receipt.json', optional=True)
    summary = read('run_001/reference/summary.json', optional=True)
    lifecycle = read('run_001/reference/lifecycle.json', optional=True)
    row = read('run_001/reference/accepted_012/summary.json', optional=True)
    observation = read('run_001/reference/reference_observations.json', optional=True)
    review, decision = read('author/ACTUAL_REVIEW.json'), read('author/NEXT_DECISION.json')
    source_review = read('author/SOURCE_REVIEW.json')
    pixel = read('author/pixel_QA.json', optional=True)
    assert protocol['card'] == launch['card'] == CARD
    assert launch['status'] in ('pass', 'not_pass') and launch['invocations'] in (0, 1)
    assert receipt is None or receipt['card'] == CARD
    assert receipt is None or receipt['status'] in ('pass', 'not_pass')
    assert receipt is None or receipt['protocol_sha256'] == launch['protocol_sha256']
    assert review['status'].startswith('pass') and not review.get('blockers', review.get('blocking_findings', []))
    assert source_review['status'].startswith('pass') and not source_review.get('blocking_findings', [])
    for name in ('close.py', 'publish.py', 'archive_publication.py'):
        assert sha256((AUTHOR/name).read_bytes()).hexdigest() == source_review['reviewed_support_sha256'][name], name
    assert protocol['source_baseline_commit'] == BASE
    assert protocol['selected_child_accepted_index'] == 1 and protocol['original_target_indices'] == [12]
    assert protocol['targets_mm'] == [1.06] and protocol['expected_new_HP_calls'] == 2
    assert not subprocess.check_output(GIT+['diff', BASE, '--name-only', '--', 'hf_repo/src'], cwd=ROOT)
    helper, reference, life = receipt or {}, summary or {}, lifecycle or {}
    outcome = 'pass' if launch['status'] == helper.get('status') == 'pass' else 'not_pass'
    assert review['execution_status'] == decision['execution_status'] == outcome
    entries = observation.get('entries') if observation is not None else None
    if outcome == 'pass':
        assert reference.get('status') == life.get('status') == 'pass'
        assert launch['exit_code'] == 0 and launch['stop_reason'] is None and launch['invocations'] == 1
        assert helper['HP_calls_started'] == helper['HP_calls_completed'] == 2
        assert helper['accepted_mechanical_states_completed'] == helper['workpiece_states_completed'] == 1
        assert reference['accepted_states'] == 1 and reference['gates'] == protocol['gates']
        assert row['status'] == 'pass' and row['index'] == 12 and row['target_mm'] == 1.06
        assert row['state_sha256'] == protocol['selected_state_sha256']
        assert observation['accepted_child_index'] == 1 and observation['original_target_index'] == 12
        assert observation['state_sha256'] == protocol['selected_state_sha256']
        assert len(entries) == 10 and all(entry['pass_gate'] is True for entry in entries)
        assert helper['plot_started'] == helper['plot_completed'] == 1
    outputs = helper.get('outputs') or {}
    for name, seal in outputs.items():
        assert (ROOT/name).stat().st_size == seal['bytes'], name
    png_name = STAGE+'/run_001/reference/reference_observations.png'
    image = outputs.get(png_name)
    if pixel is not None:
        assert pixel['card'] == CARD
        assert pixel['inspections'] == 1 and len(pixel['media']) == 1
        assert pixel['media'][0]['path'] == png_name and pixel['media'][0]['inspections'] == 1
    visual_status = pixel['status'] if pixel is not None else 'not_provided'
    stage_complete = outcome == 'pass' and image is not None and visual_status.startswith('pass')
    closure = dict(card=CARD, status='closed', execution_status=outcome, execution_closed=True,
        visual_QA_status=visual_status, stage_complete=stage_complete,
        created_utc=datetime.now(timezone.utc).isoformat(), source_baseline_commit=BASE,
        science_version='0.5.0', science_baseline_commit='b1334bb6a83ba9a0efab7bdba7bd39722146f024',
        protocol_sha256=launch['protocol_sha256'], outer_status=launch['status'], helper_status=helper.get('status'),
        summary_status=reference.get('status'), lifecycle_status=life.get('status'),
        selected_child_accepted_index=1, original_target_index=12, target_mm=1.06,
        selected_state_sha256=protocol['selected_state_sha256'],
        HP_calls_started=helper.get('HP_calls_started'), HP_calls_completed=helper.get('HP_calls_completed'),
        accepted_mechanical_states_completed=helper.get('accepted_mechanical_states_completed'),
        workpiece_states_completed=helper.get('workpiece_states_completed'),
        checks_completed=life.get('checks_completed'), original_gates=protocol['gates'],
        plot_started=helper.get('plot_started'), plot_completed=helper.get('plot_completed'),
        observation_entries=entries, selected_reference_row=row,
        producer_record_unchanged=True, default_sources_unchanged=True,
        reference_qualification_scope=reference.get('qualification'),
        full_child_path_reference_pass=False, full_original_path_reference_pass=False, full_extended_path_reference_pass=False,
        pressure_qualified=False, clamp_qualified=False, contact_qualified=False, HF5_qualified=False,
        helper_elapsed_seconds=helper.get('elapsed_seconds'), outer_elapsed_seconds=launch.get('elapsed_seconds'),
        helper_sampled_peak_RSS_bytes=helper.get('sampled_peak_RSS_bytes'),
        outer_sampled_peak_tree_RSS_bytes=launch.get('peak_sampled_tree_RSS_bytes'),
        child_terminal_wall_seconds=launch.get('child_terminal_wall_seconds'),
        child_exit_code=launch.get('exit_code'), stop_reason=launch.get('stop_reason'),
        ordinary_bindings_unchanged=launch.get('ordinary_bindings_unchanged'),
        helper_error=helper.get('error'), outer_failure=launch.get('failure'),
        cleanup_scope='Actual cooperative child terminal and elapsed/RSS observations; no SUP2 or cleanup_verified contract',
        sealed_output_files=len(outputs), sealed_output_bytes=sum(value['bytes'] for value in outputs.values()),
        output_identity_seal=helper.get('output_identity_seal'), available_sealed_error_PNG=image,
        actual_review_status=review['status'], pixel_QA=pixel, next_decision=decision,
        read_scope='Ordinary JSON/MD/source only; scientific NPZ/gzip/CSV/media use original producer seals plus stat, no payload read/hash/decode',
        qualification_scope='Only selected saved circle1.06/global12 state and one PORT direction; no full path/all columns/stress/energy/pressure/grip/release/stability/mesh-domain/HF5')

    def available_link(label, name):
        path = stage/name
        if not path.is_file():
            return label+'（未生成）'
        if path.suffix.lower() in ('.npz', '.gz', '.csv', '.png', '.gif') and path.relative_to(ROOT).as_posix() not in outputs:
            return label+'（缺原窗口seal，未链接）'
        return f'[{label}]({name})'

    lines = [f'# {CARD}：当前尖端布置1.06 mm保存态独立参考', '',
        f'2026-10-19；唯一执行 **{outcome.upper()}**；图像QA **{visual_status}**；阶段完成 `{stage_complete}`。', '',
        f"outer `{launch['status']}`、helper `{shown(helper.get('status'))}`、summary `{shown(reference.get('status'))}`、lifecycle `{shown(life.get('status'))}`。main基线 `{BASE}`；science 0.5.0／b1334保持。执行、数值检查与实际像素检查分别记录，不由生成意图或旧QA代替本卡图像效果。", '',
        '整体目标是普通LF几何进入独立HF的TMC前向分析，逐步实现可比较的非线性响应和接触相关指标。前序已完成当前r9 mm、圆心(80,40) mm、right92 mm、Lr80 mm布置的保存态延伸和实际变形、力、尖端、右侧介质与收敛显示；LOCAL3定位到当前最小J角点与Hu首个代表。本轮检查当前保存态数值可靠性，不重做生产平衡。', '',
        f"批准对象为STEP10接受行1／全局目标12／loading1.06 mm，state SHA `{protocol['selected_state_sha256']}`。完整14720单元／29970DOF（固定1288、自由28682），原材料、第三介质、正则化、网格、边界、端口、设置及验收门保持。实际完成范围由以下回执计数给出；缺失记录不视作已完成。", '',
        f"HP启动/完成 `{shown(helper.get('HP_calls_started'))}`／`{shown(helper.get('HP_calls_completed'))}`；完成力学态 `{shown(helper.get('accepted_mechanical_states_completed'))}`、工件投影态 `{shown(helper.get('workpiece_states_completed'))}`、检查 `{shown(life.get('checks_completed'))}`，绘图启动/完成 `{shown(helper.get('plot_started'))}`／`{shown(helper.get('plot_completed'))}`。", '',
        '原十五门：`'+str(protocol['gates'])+'`。比较材料/Hu/总局部力与全局力、同一固定兼容PORT方向切线、完整CSC系数组装身份及方向作用、KKT力/均值作用、约束/残差/整体平衡和有符号工件/holding投影。只检查这一方向；独立解析能量仅归档，不授候选应力或能量资格。', '',
        '|观察项|原归一化误差|原门|通过|', '|---|---:|---:|---|']
    for entry in entries or []:
        lines.append('|'+ '|'.join(shown(entry.get(key)) for key in ('label', 'error', 'limit', 'pass_gate'))+'|')
    if entries is None:
        lines.append('|误差普通记录未提供|未提供|未提供|未提供|')
    lines += ['', decision.get('interpretation_md', ''), '',
        '仅在全部原门PASS后允许生成十项误差图，实际生成与否见回执；零误差不加地板、不改变原分母或阈值。逐元素/全局差值及工件核查若已产生，保持在原窗口封存gzip；闭卡不重开载荷、切线、矩阵、科学gzip或媒体。工件Fx/Fy是含材料与Hu的有符号弱式合力；legacy normal_force为全局Fy，2absFy也不是圆周局部压力或有效夹持力。', '',
        f"实际审阅 `{review['status']}`；像素记录 `{shown(pixel)}`。原生产成功、失败历史及全部未完成资格保持；本卡通过只覆盖此保存态与同一PORT方向。", '']
    if image is not None:
        lines += ['![原参考误差与原门](run_001/reference/reference_observations.png)', '']
    limits = protocol['phases']['reference']
    lines += [
        f"资源：helper `{shown(helper.get('elapsed_seconds'))}` /{limits['helper_seconds']} s，outer `{shown(launch.get('elapsed_seconds'))}` /{limits['outer_seconds']} s；采样进程树峰值 `{shown(launch.get('peak_sampled_tree_RSS_bytes'))}` /{protocol['sampled_RSS_bytes']} B；四库线程上限16。实际child wall `{shown(launch.get('child_terminal_wall_seconds'))}` s、exit `{shown(launch.get('exit_code'))}`、stop `{shown(launch.get('stop_reason'))}`。合作停止和采样记录不增加SUP2或硬抢占清理资格。", '',
        f"原窗口封存 {len(outputs)} 份输出／{closure['sealed_output_bytes']} B，状态 `{shown(helper.get('output_identity_seal'))}`。helper错误 `{shown(helper.get('error'))}`；outer错误 `{shown(launch.get('failure'))}`。首错后的实际partial如实保留；本卡未自动重试、修复重跑、延期或force。", '',
        '本轮无新生产F/T、平衡求解、测试、默认安装或API关联。旧实际变形、力、收敛和局部定位只链接，不解码或重绘；不升级完整路径参考、接触压力、有效夹持、自由释放、稳定性、网格/域宽收敛或HF5资格。', '',
        '审查入口：'+' · '.join(available_link(label, name) for label, name in (
            ('参考summary', 'run_001/reference/summary.json'), ('选定态summary', 'run_001/reference/accepted_012/summary.json'),
            ('误差普通JSON', 'run_001/reference/reference_observations.json'), ('lifecycle', 'run_001/reference/lifecycle.json'),
            ('封存回执', 'run_001/reference/execution_receipt.json'), ('outer', 'reference_launch.json'),
            ('实际审阅', 'author/ACTUAL_REVIEW.md')))+' · [闭卡JSON](author/closure.json)', '',
        '既有实际效果：'+available_link('STEP10实际变形与力', '../lf_circle_tip_step_010/RESULTS.md')+' · '+available_link('LOCAL3当前空间定位', '../lf_circle_tip_local_003/RESULTS.md')+'。', '',
        '下一步：'+decision['next_step'], '',
        '恢复开发：origin保持https://github.com/dudaxing/Compliant-TO-TMC.git，后续在main。先读README、docs/CURRENT_STATUS.md和docs/RESUME_DEVELOPMENT.md，再读本卡RESULTS/NEXT_STEPS、protocol及授权。异路径恢复使用同机local Git对象fetch/ff-only，不是独立机器或远端对象下载验证。已关闭launcher不再执行。', '']
    old_fronts = {name: subprocess.check_output(GIT+['show', BASE+':'+name], cwd=ROOT) for name in FRONTS}
    assert all((ROOT/name).read_bytes() == old for name, old in old_fronts.items())
    write('RESULTS.md', '\n'.join(lines))
    write('NEXT_STEPS.md', decision.get('next_steps_md', decision['next_step']).rstrip()+'\n')
    write('author/closure.json', json.dumps(closure, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    history = dict(source_baseline_commit=BASE, files=[])
    for name, old in old_fronts.items():
        link = os.path.relpath(stage/'RESULTS.md', (ROOT/name).parent).replace('\\', '/')
        prefix = (f'> 2026-10-19 {CARD} **执行{outcome.upper()}／图像QA {visual_status}**：当前r9/(80,40)、right92/Lr80布置的accepted1/global12/1.06 mm保存态参考；'
            f"HP启动/完成 {shown(helper.get('HP_calls_started'))}/{shown(helper.get('HP_calls_completed'))}，阶段完成{stage_complete}。"
            f'保原生产历史及资格；见[实际记录]({link})。原历史说明保留如下。\n\n').encode('utf-8')
        (ROOT/name).write_bytes(prefix+old)
        current = (ROOT/name).read_bytes()
        assert current.endswith(old) and current.count(old) == 1
        history['files'].append(dict(path=name, old_bytes=len(old), old_sha256=sha256(old).hexdigest(),
            prefix_bytes=len(prefix), raw_suffix_preserved_once=True))
    write('author/front_history.json', json.dumps(history, ensure_ascii=False, indent=2)+'\n')
    for name in ('close.py', 'publish.py'):
        path, raw = stage/'author'/name, (AUTHOR/name).read_bytes()
        if path.exists():
            assert path.read_bytes() == raw
        else:
            with path.open('xb') as stream:
                stream.write(raw)
    print(json.dumps(dict(status='closed', execution_status=outcome, visual_QA_status=visual_status,
        stage_complete=stage_complete, HP_calls_started=helper.get('HP_calls_started'),
        HP_calls_completed=helper.get('HP_calls_completed'), fronts=len(FRONTS)), ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
