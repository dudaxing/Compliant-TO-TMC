"""Record the next single loading proposal from the completed numerical reference."""
from datetime import datetime,timezone
import json
from pathlib import Path
import shutil

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
STAGE=ROOT/'lf_data_preparation/native_interface_001/lf_circle_reference_001'
path=STAGE/'author/closure.json'
closure=json.loads(path.read_bytes())
assert closure['status']=='pass_closed' and closure['HP_calls_completed']==2
assert closure['target_mm']==1.15 and closure['original_target_index']==5
text=('建议下一阶段L-CSTEP3复用已安装load_only保存态延伸，从成功且已选定态独立参考通过的1.15 mm末态，'
    '仅追加1.25 mm绝对目标（增量0.10 mm）。保持r9/c(71,40)及其余物理、原数值设置和验收门，'
    '用实际变形、输入反力、材料/Hu/总工件力、边界/尖端距离、分区J及收敛继续观察更强压缩区间。'
    '当前minJ0.225154、最小无符号边距0.232258 mm，故比上次0.15 mm请求再缩小一步；'
    '该选择不新增门，也不预言接触或稳定性。本次不执行新加载，需另行明确新阶段授权。')
decision=dict(proposed_stage='L-CSTEP3',status='proposed_not_executed',
    source_result='lf_data_preparation/native_interface_001/lf_circle_step_002/run_001/wave_circle_step/result.json',
    selected_accepted_index=1,selected_global_target_index=5,source_state_sha256=closure['selected_state_sha256'],
    selected_reference='lf_data_preparation/native_interface_001/lf_circle_reference_001/run_001/reference/summary.json',
    anchor_mm=1.15,target_mm=1.25,increment_mm=.1,child_targets_mm=[1.15,1.25],
    complete_task_targets_mm=[0.,.25,.5,.75,1.,1.15,1.25],original_target_indices=[5,6],child_original_target_indices=[0,1],
    unchanged='All physics and non-clock settings, including minimum_increment .00625/max_bisections4; original gates and installed mechanics sources.',
    proposed_resources=dict(controller_seconds=1800,shared_display_seconds=600,helper_seconds=2700,outer_seconds=2760,sampled_RSS_bytes=8*1024**3),
    fresh_anchor='Original absolute lift/fluctuation and signed R; fresh F/T first check with exact state SHA/R identity. The reference archive is evidence, not the continuation input.',
    outputs='Actual x1 deformation/mirror, signed R/qout and lower-body total/material/Hu forces, unsigned boundary/tip distances, partitioned fields, convergence and actual N accepted states.',
    stop_policy='One invocation, first terminal error stops; original internal backtracking/bisection allowed, actual partial retained; no external retry/repair rerun/extension/force.',
    no_new_default_install_tests_HP=True,
    qualification='Child segment only, no full original/extended path, pressure/effective grip/unloading/release/stability/HF5 transfer.')
closure.update(next_step=text,next_step_decision=decision,next_step_recorded_utc=datetime.now(timezone.utc).isoformat())
path.write_text(json.dumps(closure,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
results_path=STAGE/'RESULTS.md';results=results_path.read_text(encoding='utf-8')
overview='''实际结论摘要：1.15 mm圆形峰值的独立参考通过，2次HP80/120、80785项实际检查，原十五类门不变。全局total/material/Hu力归一化误差分别约1.45953e-15/3.27486e-16/2.77125e-16；总PORT作用约6.63787e-17，CSC作用约8.19275e-17，KKT force作用约8.19550e-17，HP120相对平衡残差约1.38383e-12，均低于相应原门。HP80/120总力一致误差约1.22783e-76（原门1e-40）。这些使用原分母/floor，不是工件Fy误差百分比。

这支持当前保存圆形模型中力和所检方向切线的数值一致性，不能据此认定圆周压力或有效夹持。原1.15态最小边距0.232258 mm、尖端距离3.202515 mm、自由介质minJ0.225154和Hu占约81.4%弱Fy的观察保持；它们没有因参考通过而变成接触证明。

实际outer123.8793秒（约2分4秒），采样树峰值1281785856 B（约1.19 GiB），真实child exit0且无stop。一张误差PNG完成一次像素检查，十项标签/数值/阈值清楚，无遮挡；原结构媒体只链接，未重读或重绘。

'''
position=results.index('整体目标是');results=results[:position]+overview+results[position:]
start=results.index('下一步：');end=results.index('\n\n审查入口：',start)
results=results[:start]+'下一步：'+text+' 具体来源与资源见[NEXT_STEPS.md](NEXT_STEPS.md)。'+results[end:]
results_path.write_text(results,encoding='utf-8',newline='\n')
plan='''# L-CREF1之后的单步加载计划

本轮仅圆形1.15 mm峰值的选定态独立参考PASS：原十五类门、全13440单元/27378DOF与同一PORT方向，2HP、80785项实际检查。原S2响应、全路径/压力/夹持等资格保持，未做API关联。

'''+text+'''

1. 来源为L-CSTEP2的accepted1/global5/1.15 mm成功末态，SHA与本次参考相同；不以reference输出替代生产saved_result，不误用continuation的1.00 mm祖锚。新完整任务只在[0,.25,.5,.75,1,1.15]后追加1.25并更新峰值/四说明字段；子段[1.15,1.25]，global5/6、child0/1。
2. 已安装evaluate_native(...,saved_result=原S2result,selected_state_index=1,extend_path=True)保持。先fresh F/T复核原绝对split及带符号R，第一次检查保持SHA/R身份；再执行新目标。原mechanical/chunk256/port_projection与minimum_increment=.00625、max_bisections4及全部生产门保持，无新测试/HP/安装/默认修改。
3. 输出同定义4PNG、实际N帧GIF及表/人工页，显示×1变形与对称镜像、输入R/qout、下半工件有符号Fx/Fy的材料/Hu/总分解、实际无符号边界距离与尖端距离、solid/medium J/局部场、残差/约束界/回溯/二分。所有实际接受态保留，不能锁定仅两态；镜像不加倍数值。
4. 拟controller1800秒、显示共享600秒、helper2700秒/outer2760秒、采样8 GiB。新候选包装需更新父链与索引并有限静审，明确新授权后才启动一次；首错停止，无外部重试、修复重跑、延期或force。原内部回溯/二分允许。
5. 完成后再按真实几何/介质压缩/力分量/收敛成本决定下个目标或参数诊断。相交、重叠或不确定观察先核查；不以正距离、非零Fy或数值参考通过单独证明有效夹持。尖端仍远于真正最近边界位置，须分别观察。

后续保持能力路线：充分接近/传力观察→有针对性的参数与接触指标验证→圆形卸载及同定义设计比较。更远目标暂不锁定；不例行每态补HP，不授完整路径/全列切线/独立几何mask/连续压力/有效夹持/释放/稳定性/制造/HF5资格。

审查：[本次数值结果与误差图](RESULTS.md)、[参考summary](run_001/reference/summary.json)、[原S2实际变形/反力](../lf_circle_step_002/run_001/REVIEW.md)、[闭卡与决策](author/closure.json)。
'''
(STAGE/'NEXT_STEPS.md').write_text(plan,encoding='utf-8',newline='\n')
target=STAGE/'author/record_next_plan.py';assert not target.exists();shutil.copyfile(Path(__file__),target)
print(json.dumps(dict(status='recorded_proposed_not_executed',next_stage='L-CSTEP3',target_mm=1.25)))
