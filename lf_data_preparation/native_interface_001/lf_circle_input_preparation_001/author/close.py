"""Close L-CPREP1 from ordinary records without scientific/media payload reads."""
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
STAGE = 'lf_data_preparation/native_interface_001/lf_circle_input_preparation_001'
BASE = 'd2cad344a3675cc1129c4786629f56e5678cb895'
FRONTS = ['README.md', 'hf_repo/README.md', 'docs/CURRENT_STATUS.md',
          'docs/PHYSICAL_FUNCTION_PROGRESS.md', 'docs/RESUME_DEVELOPMENT.md',
          'docs/L_USE1_NEXT_STEP_PLAN.md', 'docs/L_BFWD1_NEXT_STEP_PLAN.md']


def read(name):
    return json.loads((ROOT/STAGE/name).read_bytes())


def write(name, text):
    (ROOT/STAGE/name).write_text(text, encoding='utf-8', newline='\n')


def main():
    receipt, launch, diag = [read(name) for name in
        ('run_001/execution_receipt.json', 'preparation_launch.json', 'run_001/diagnostics.json')]
    review, pixel = read('author/ACTUAL_REVIEW.json'), read('author/pixel_QA.json')
    assert receipt['card'] == launch['card'] == pixel['card'] == 'L-CPREP1'
    assert receipt['status'] in ('pass', 'not_pass') and launch['status'] in ('pass', 'not_pass')
    assert launch['invocations'] == 1 and launch['cleanup_verified'] is True
    assert review['status'].startswith('pass') and not review.get('blockers', review.get('blocking_findings', []))
    assert receipt['protocol_sha256'] == launch['protocol_sha256']
    outcome = 'pass' if receipt['status'] == launch['status'] == 'pass' else 'not_pass'
    # A missing field in a partial receipt remains null, never an invented zero.
    calls = {key:receipt.get(key) for key in
             ('force_calls', 'tangent_calls', 'HP_calls', 'solver_calls', 'tests', 'default_installations')}
    counts, circle = diag.get('counts', {}), diag.get('circle', {})
    gaps, outputs = diag.get('workpiece', {}).get('initial_gaps_mm'), receipt['outputs']
    terminal = review.get('terminal', {}).get('tool_terminal_as_reported_by_parent')
    closure = dict(card='L-CPREP1', status=outcome+'_closed', execution_status=outcome,
        execution_closed=True, created_utc=datetime.now(timezone.utc).isoformat(),
        source_baseline_commit=BASE, protocol_sha256=receipt['protocol_sha256'],
        terminal=terminal,
        helper_elapsed_seconds=receipt.get('elapsed_seconds'), outer_elapsed_seconds=launch.get('elapsed_seconds'),
        peak_sampled_tree_RSS_bytes=launch.get('peak_sampled_tree_RSS_bytes'),
        cleanup_verified=launch['cleanup_verified'], checks_completed=receipt.get('checks_completed'),
        checks_passed=receipt.get('checks_passed'), preparation_counts=counts, calls=calls,
        sealed_output_files=len(outputs), sealed_output_bytes=sum(row['bytes'] for row in outputs.values()),
        output_identity_seal=receipt.get('output_identity_seal'),
        requested_targets_executed=receipt.get('requested_targets_executed'),
        actual_review_status=review['status'], pixel_QA_status=pixel['status'],
        qualification_scope=receipt.get('qualification_scope'),
        next_step='Prepare a circle-aware saved viewer; separately scope a 0/.25/.5 mm pilot afterwards. No new execution window opened.',
        closure_read_scope='Ordinary records only; no scientific/media payload reads, hashes, reconstruction, tests, mechanics or rendering.')
    checks = f"{receipt.get('checks_passed')} / {receipt.get('checks_completed')}"
    results = f'''# L-CPREP1：圆形固定工件未变形准备

执行状态：**{outcome.upper()}**。基线main `{BASE}`，默认science版本0.5.0、原science baseline保持。目标是把第三个 wave LF 结构接入圆形工件探索，先核原网格、四个掩码、端口和约束能否组成明确模型，再安排实际加载。本轮未执行输入路径。

保留原 wave 几何；固定圆形工件中心 {circle.get('center_mm')} mm、半径 {circle.get('radius_mm')} mm。实际 Q1 单元阶梯边界是计算边界，解析圆和原 side-18 方体包络只是参考。实际完成计数 `{receipt.get('counts')}`；普通独立审阅 `{review['status']}`，人工像素检查 `{pixel['status']}`。

其余条件逐值保持：E=1MPa、nu=0.3、plane strain、厚20mm、h=0.5mm、84×40mm下半域、gamma=1e-6、alpha=5e-7、Lr=80mm及原支撑/平均位移端口/对称。工件采用固定节点运动学覆盖，不把原介质掩码改成实体。新任务身份、工件定义及尚未执行的短路径已明确记录；原25目标方体task不变。

![圆形工件未变形模型](run_001/circle_prepared.png)

兼容性检查 {checks}。原模型 {counts.get('cells')} 单元、{counts.get('dofs')} DOF；工件 {counts.get('workpiece_cells')} 单元、{counts.get('workpiece_nodes')} 节点、{counts.get('workpiece_fixed_dofs')} 固定 DOF；合并固定 {counts.get('fixed_dofs')}、自由 {counts.get('free_dofs')} DOF。实际暴露边 {counts.get('boundary_edges')} 条，另有对称切口 {counts.get('symmetry_cut_edges')} 条。背景介质计数包含固定工件覆盖，不能全部称为自由介质。

初始节点窗口 `{gaps}` mm 按原机构节点的同水平／竖直线定义；它不是有限表面间隙，也不是接触起点。图为未变形下半域、坐标倍率 ×1，局部图只放大视窗。C 面板顶部第二行注记与节点标记轻微重叠；关键计数可读，精确值见诊断 JSON，本轮无重绘。

实际 F/T/HP/平衡求解调用记录分别为 {calls['force_calls']}/{calls['tangent_calls']}/{calls['HP_calls']}/{calls['solver_calls']}，测试 {calls['tests']}，默认安装 {calls['default_installations']}。结论基于冻结调用路径与实际记录，未部署全局动态机械 hook；依赖可导入或注册 JAX，不能声称零依赖导入。保存的 [0,0.25,0.5] mm 只是后续任务定义，尚未执行。

helper {receipt.get('elapsed_seconds')} 秒，outer {launch.get('elapsed_seconds')} 秒；采样进程树峰值 {launch.get('peak_sampled_tree_RSS_bytes')} B，预算 180/240 秒、1 GiB，清理确认 `{launch['cleanup_verified']}`。实际终端 `{terminal}`；原窗口封存 {len(outputs)} 个输出、{closure['sealed_output_bytes']} B。科学／媒体身份继承原 helper seal 加 stat，闭卡不重读或重哈希载荷。

制造资格仍为 pending。未新增平衡、独立参考、压力、有效夹持、卸载／释放、稳定性或 HF5 资格。下一步先适配圆形保存态显示，再另卡安排同三目标短加载，依据真实反力、变形和收敛决定后续。现有方体显示器不能直接当作圆形显示器使用。

审查入口：[诊断](run_001/diagnostics.json)、[模型](run_001/model/model.json)、[任务](run_001/task.json)、[运行回执](run_001/execution_receipt.json)、[外层记录](preparation_launch.json)、[人工检查页](run_001/REVIEW.md)、[实际审阅](author/ACTUAL_REVIEW.md)、[像素检查](author/pixel_QA.json)、[闭卡记录](author/closure.json)。
'''
    next_steps = '''# L-CPREP1 后续

本轮只完成圆形固定工件输入、未变形兼容性和显示。原 25 目标任务及历史结果保持，短任务 [0,0.25,0.5] mm 尚未执行。

1. 为下一张L-CPILOT1计算卡准备圆形保存态显示适配：使用实际保存的工件单元／节点／暴露边，区分 Q1 阶梯圆边界与解析参考圆；保留真实倍率、反力方向和原距离定义。现有方体显示器不能直接复用为圆形结果。这是短加载卡所需的准备，不另设一轮重复链接/投影。
2. 候选和资源窗口明确后，另卡执行同三目标、零起点短加载及其实际显示；保持当前物理、材料、端口、约束和生产验收门，保存实际变形、反力与真实 solver history。
3. 根据实际收敛、J 和接触作用观测决定继续行程或排查问题。弱式工件合力与节点窗口不自动成为压力、有效夹持或接触起点。

本页是开发安排，不代表新执行窗口已经开启；没有运行新测试、F/T、HP、平衡求解或显示。
'''
    old_fronts = {name:subprocess.check_output(['git', 'show', BASE+':'+name], cwd=ROOT) for name in FRONTS}
    for name, old in old_fronts.items():
        assert (ROOT/name).read_bytes() == old, 'Front already differs from baseline: '+name
    write('RESULTS.md', results)
    write('NEXT_STEPS.md', next_steps)
    write('author/closure.json', json.dumps(closure, ensure_ascii=False, indent=2)+'\n')
    history = dict(source_baseline_commit=BASE, files=[])
    for name, old in old_fronts.items():
        link = os.path.relpath(ROOT/STAGE/'RESULTS.md', (ROOT/name).parent).replace('\\', '/')
        prefix = (f'> 2026-10-16 L-CPREP1 **{outcome.upper()}**：圆形工件输入／未变形准备，'
                  f'{checks} 检查；三目标加载未执行。先适配圆形保存态显示，后另卡短加载。'
                  f'见[实际记录]({link})。原历史说明保留如下。\n\n').encode('utf-8')
        (ROOT/name).write_bytes(prefix+old)
        current = (ROOT/name).read_bytes()
        assert current.endswith(old) and current.count(old) == 1
        history['files'].append(dict(path=name, old_bytes=len(old), old_sha256=sha256(old).hexdigest(),
                                    prefix_bytes=len(prefix), raw_suffix_preserved_once=True))
    write('author/front_history.json', json.dumps(history, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(dict(status='closed', execution_status=outcome, fronts=len(FRONTS),
                         outputs=len(outputs)), ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
