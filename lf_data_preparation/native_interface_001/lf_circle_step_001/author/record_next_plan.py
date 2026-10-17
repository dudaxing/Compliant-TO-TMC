"""Add a concrete, unexecuted next-step decision from the completed ordinary records."""
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil

AUTHOR = Path('D:/hf-native-workpiece-api-author-20261017/L_CSTEP1_preparation_001')
ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
STAGE = ROOT / 'lf_data_preparation/native_interface_001/lf_circle_step_001'
closure_path = STAGE / 'author/closure.json'
closure = json.loads(closure_path.read_bytes())
assert closure['status'] == 'pass_closed' and closure['saved_accepted_states'] == 2
last = closure['last_saved_state']
assert last['d_mm'] == 1. and last['index'] == 1 and last['original_target_index'] == 4
body = last['workpiece']['force_on_lower_body_N']
fraction = body['regularization'][1] / body['total'][1]
decision = dict(proposed_stage='L-CSTEP2', status='proposed_not_executed',
    source_result='lf_data_preparation/native_interface_001/lf_circle_step_001/run_001/wave_circle_step/result.json',
    source_accepted_index=1, source_global_target_index=4, source_state_sha256=last['state_sha256'],
    anchor_mm=1., proposed_target_mm=1.15, proposed_increment_mm=.15,
    full_task_prefix_mm=[0., .25, .5, .75, 1., 1.15], child_targets_mm=[1., 1.15],
    workpiece=dict(shape='circle', radius_mm=9., center_mm=[71., 40.], fixed_components=[0, 1]),
    rationale='Successful seven-check loading with zero failed line trials or bisections supports continuation. Medium minJ has fallen from .5011 to .3293 and Hu contribution has grown; shorten the next requested increment from .25 to .15 mm to observe the increasingly compressed regime. This is a sampling choice, not a new acceptance gate or stability claim.',
    observed_Hu_fraction_of_signed_lower_body_Fy=fraction,
    interface='Installed evaluate_native saved load_only extension with extend_path=True; no new implementation or installation planned',
    proposed_resources=dict(controller_seconds=1800, shared_display_seconds=600, helper_seconds=2700, outer_seconds=2760, sampled_RSS_bytes=8*1024**3),
    unchanged='All other physical task fields, non-clock numerical settings, production gates and mechanics sources',
    outputs='Actual x1 deformation, signed input reaction and body Fx/Fy with material/Hu split, unsigned distances, solid/medium fields, convergence/line-search/bisection and original state identities; preserve every actual accepted state',
    execution_policy='Fresh separate stage only after user authorization; one invocation, first terminal error stops, original internal backtracking/bisection allowed, no external retry/repair rerun/extension/force',
    qualification='Segment only; no complete path, independent HP, surface pressure, effective grip, unloading/release, stability or HF5 claim')
text = '''建议下一阶段 L-CSTEP2 复用已安装接口，从本次成功1.00 mm末态只追加1.15 mm，增量0.15 mm。新增加载态7次检查（含锚点共8次）、无失败回溯或二分，支持继续；但自由第三介质minJ由0.5011降至0.3293，且Hu分量增长，故缩小请求步长以观察更强压缩区间。此选择不改变原门，也不证明稳定性。保持半径9 mm、圆心(71,40) mm、固定工件及其余物理条件和非clock设置；仅规划，不在本轮运行。'''
closure['next_step'] = text
closure['next_step_decision'] = decision
closure['next_step_recorded_utc'] = datetime.now(timezone.utc).isoformat()
closure_path.write_text(json.dumps(closure, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8', newline='\n')
results_path = STAGE / 'RESULTS.md'
results = results_path.read_text(encoding='utf-8')
start = results.index('下一步：')
end = results.index('\n\n审查入口：', start)
results = results[:start] + '下一步：' + text + ' 具体来源、资源和输出见[NEXT_STEPS.md](NEXT_STEPS.md)。' + results[end:]
overview = '''实际效果摘要：输入由0.75增至1.00 mm，R由0.129261增至0.173350 N，q_out由0.723769增至0.966288 mm；所选物理Q1边界最小无符号距离由0.504374降至0.334737 mm。最近边界位置与最右尖端不是同一点，1.00 mm时尖端距离仍为3.349195 mm。因此图中不能声称尖端已贴合圆面。自由介质minJ为0.329300、solid minJ为0.975949，均通过原J>0门。下半工件Fy=0.000949441 N，其中Hu=0.000770303 N（约81.1%）；这是弱式力分解，不能当作有效夹持力或连续压力。正的无符号距离下也可出现第三介质弱式传力，不以等待边界相交作为接触判据。

收敛：复核锚点1次检查、新目标7次检查；6次线搜索试算全部接受，0失败、0二分。总计F14/T8；本轮含显示约494.2秒，采样进程树峰值约0.777 GiB，清理通过。输出4PNG与2帧实际变形GIF。收敛图外侧图例遮挡了右面板标题的一部分，两条约束界及数据仍可见；保留原图，不重绘。

'''
marker = '整体目标仍是'
position = results.index(marker)
results = results[:position] + overview + results[position:]
results_path.write_text(results, encoding='utf-8', newline='\n')
next_text = '''# L-CSTEP1结果驱动的下一步计划

本轮生产、原门、显示和清理均PASS，0.75→1.00 mm子段完成。整条圆形路径未从零重做，原资格及历史保持。

''' + text + '''

1. 准备：来源为本轮wave_circle_step/result.json的接受态1（global4、1.00 mm），使用原状态SHA及原绝对lift/fluctuation和带符号R。完整任务前缀保持[0,0.25,0.50,0.75,1.00]，仅追加1.15 mm并更新新峰值。使用已安装load_only接口，无新源码、测试或默认安装。
2. 单次计算：原fresh-anchor F/T复核通过后，执行[1.00,1.15]子段；物理条件、非clock设置和全部原验收门保持。原内部回溯/二分允许，保留每个实际接受态；首个终端错误停止，无外部重试、修复重跑、延期或force。
3. 显示与记录：同定义实际×1变形/镜像图、输入R与q_out、下半工件有符号Fx/Fy及材料/Hu分解、无符号边界和尖端距离、solid/medium J与局部场、残差/约束界/线搜索/二分。两态以上则按实际帧数显示，保留真实partial，不锁定两态。
4. 拟用资源：controller1800秒；保存态显示与收敛共600秒；helper2700秒、outer2760秒，采样8 GiB。需独立新阶段授权；本计划不启动任何新计算。
5. 再决策：按实际几何、介质压缩、力分量和收敛成本决定下一目标或参数诊断。若出现相交、重叠或不确定观察，先核查；不因非零Fy或正距离单独认定有效夹持，也不等待几何相交来定义TMC传力。独立参考只在有信息增量时另行安排，不例行每态补HP。

当前最近Q1边界距离0.334737 mm，最右尖端距离3.349195 mm。推进输入不等于尖端贴合；需要继续同时观察真正最近位置与尖端。下半全局Fy中Hu占约81.1%，尚无连续压力、有效夹持、卸载/释放、稳定性或HF5资格。

审查：[实际结果](RESULTS.md)、[原值人工页](run_001/REVIEW.md)、[闭卡与下一步来源](author/closure.json)、[已安装接口用法](../lf_circle_extension_001/USAGE.md)。
'''
(STAGE / 'NEXT_STEPS.md').write_text(next_text, encoding='utf-8', newline='\n')
for name in ['close.py', 'publish.py', 'archive_publication.py', 'record_pixel_qa.py', 'record_next_plan.py', 'DOC_SOURCE_REVIEW.json', 'DOC_SOURCE_REVIEW.md']:
    target = STAGE / 'author' / name
    assert not target.exists()
    shutil.copyfile(AUTHOR / name, target)
print(json.dumps(dict(status='recorded_proposed_not_executed', next_target_mm=1.15, Hu_Fy_fraction=fraction), ensure_ascii=False))
