# L-CTIPUNLOAD3：最右尖端对向圆形工件的保存态延伸

2026-10-20；执行 **PASS**；图像QA `pass_root_visual_inspection_with_minor_layout_note`，本阶段完整完成 `True`。生产 `success`，helper `pass`，outer `pass`；实际停止阶段 `final_binding_and_seal`。

整体目标是把LF给出的夹持器几何接入独立、可恢复的高保真大变形/TMC有限元分析，逐步实现对工件接近、接触后的变形与作用力及卸载响应的可审查计算。结构优化、有效夹持判定和HF5标签尚不能由单段前向计算替代。

本轮做什么及原因：复用已安装ordered_cycle保存态延伸接口，从已成功的卸载1.00 mm状态重新核验平衡及SHA/有符号R，再执行五个卸载目标0.90/0.75/0.50/0.25/0 mm。input.target保持任务峰值1.06 mm，四项说明身份原值也不变；观察实际结构、力、距离、介质与收敛，并与pilot原始零输入origin的同定义标量作描述性对照。未从零重放旧前缀，也未改默认HF源码。

半径9 mm、圆心(80,40) mm、固定工件ux/uy、右域界92 mm、正则化长度80 mm保持；下半域92×40 mm、h=0.5 mm、厚20 mm、E=1 MPa、nu=0.3、plane strain、gamma=1e-6、alpha=5e-7及原支撑/平均端口/对称保持。完整ordered_cycle任务[0,.25,.5,.75,.90,.95,.98,1.00,1.02,1.03,1.04,1.05,1.06,1.05,1.00]只追加[.90,.75,.50,.25,0]，其余task字段精确保持；本次请求后缀[1.00,.90,.75,.50,.25,0]。本层不新增task_transition，首次卸载的五键转段记录只保留在嵌套parent_continuation历史。

已完成及实际效果：保存接受态 `6`，helper回调 `6`。缺失保存结果记为null，实际二分增加的接受态全部保留。父结果SHA `82fcf0b9d1f2485f9b655ec79a8e03978c3dc3ef9405f8baa20859731e0b6478` 与授权绑定一致，原成功与失败历史保留。

|child行|global目标|路段|d mm|输入R N|q_out mm|body Fy N|tip距离 mm|最近边界 mm|solid minJ|medium minJ|
|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
|0|14|resume_origin|1.0|0.17845354455643678|0.9524284256858055|0.00579420014046935|0.04968854151114499|0.04968854151114499|0.9762585262753055|0.03880995637928876|
|1|15|unloading|0.9|0.15807823081081884|0.8625531334711388|0.0029634728136028283|0.13886658198055812|0.13886658198055812|0.978485342367391|0.1297446087788906|
|2|16|unloading|0.75|0.13029373126695099|0.7209345473765181|0.0014019374851138356|0.27988491530854986|0.27988491530854986|0.9819914053937875|0.27350038751453865|
|3|17|unloading|0.5|0.08602790333542186|0.48091445412449807|0.0004782806618354332|0.5193940639875763|0.5193940639875763|0.9879538763129987|0.5165686928215502|
|4|18|unloading|0.25|0.04274353414710264|0.24018802342288847|0.00014591711519481153|0.7598854694338719|0.7598854694338719|0.9939667029510496|0.7591252661187657|
|5|19|unloading|0.0|1.6317430051868603e-25|-8.903399720651071e-25|-1.0014711119833229e-28|1.0|1.0|1.0|1.0|

|d mm|右介质 minJ|右介质 maxabsHu 1/mm|右条带最大节点位移 mm|relative residual|
|---:|---:|---:|---:|---:|
|1.0|0.21125930290424316|0.04719244592479832|1.0975264252874317|4.935362977086705e-10|
|0.9|0.27160449000954107|0.01617003257847882|1.144980350035047|2.9146416338715613e-12|
|0.75|0.39762377949682715|0.005591771605254592|1.0537179809466626|1.4413735417836727e-12|
|0.5|0.644133518565071|0.005909855856949489|0.7147775822035365|1.3085544812585784e-12|
|0.25|0.8663258675749972|0.004647480812679454|0.3379596327170865|1.3214845804383785e-12|
|0.0|1.0|1.3808221286067474e-26|2.499557320893313e-24|5.42212183309069e-10|

同输入0 mm对照仅描述pilot原始origin/global0与本次卸载global19的13项原标量及差值；保旧摘要origin原leg，不称为loading，不设归零、相等或恢复门，不据差值授予可逆性、耗散或夹持资格。详细原值见[状态表](run_001/state_table.json)及人工页。

表中保留原数值。q_out是加权端口位移，不是表面间隙；输入R与工件合力为原下半模型数值。完整Fx/Fy的material/Hu/total分量、实际尖端及边界见证、分区极值与位置、原残差/约束界和整体平衡见[闭卡JSON](author/closure.json)及[显示摘要](run_001/view/wave_circle_tip_unload3/summary.json)。

原验收门 `{'production_residual': '1e-9', 'average_constraint': '1e-10', 'global_force_balance': '1e-6', 'fixed_displacement_mm': '8e-11'}`；缓存检查 `{'actual_accepted_states': 6, 'minimum_J': 0.03880995637928876, 'maximum_fixed_split_sum_mm': 0.0, 'maximum_relative_residual': 5.42212183309069e-10, 'native_constraint_bound_pass': True, 'maximum_relative_global_force_balance': 5.690959552910058e-11, 'passed': True}`。生产调用 `{'force_calls': 74, 'force_calls_completed': 70, 'tangent_calls': 38, 'tangent_calls_completed': 38, 'solver_invocations': 1, 'JIT_calls': 0, 'HP_calls': 0}`；收敛计数 `{'accepted_states': 6, 'newton_base_checks': 38, 'inferred_check_groups': 6, 'line_search_trials': 36, 'line_search_accepted': 32, 'line_search_rejected': 4, 'failed_attempts': 0, 'linear_solves': 37, 'maximum_bisection_depth': 0, 'zero_newton_residuals': 0}`。API/solver/view等包装调用 `{'api_started': 1, 'solve_started': 1, 'solve_completed': 1, 'api_completed': 1, 'view_child_started': 1, 'view_child_completed': 1, 'convergence_plot_started': 1, 'convergence_plot_completed': 1}`。原门和非clock设置不变；minimum_increment=0.00625 mm保持，本段原目标间隔及原内部二分均受该原限值、最大二分深度和原终端停止规则约束；保持原二进制浮点判断，不新增修约或容差，无外部重试。

路径实际标志 `{'path_kind': 'ordered_cycle', 'targets_mm': [1.0, 0.9, 0.75, 0.5, 0.25, 0.0], 'reached_displacement': 0.0, 'path_completed': True, 'loading_peak_reached': False, 'new_peak_reached': None, 'extended_segment_completed': None, 'task_target_executed': False, 'full_original_path_completed': False, 'full_extended_path_completed': False, 'unload_endpoint_reached': True}`。unload_endpoint_reached为true时只说明本次请求输入回程终点0完成，不代表结构恢复零位、自由释放或稳定；task_target_executed、full_original_path_completed、full_extended_path_completed保持false，完整加载前缀没有在child中执行。没有把本段PASS授予整条路径或独立参考。

本child不访问1.06 mm任务峰值，loading_peak_reached保持false；响应maximum_loading_stroke仅是本child实际保存段最大输入1.00 mm，不能代替task input.target峰值1.06 mm。

图中实际坐标×1；完整结构和动画只作对称镜像，数值没有镜像加倍。尖端按唯一参考坐标(80,30)动态查找并跟随实际位移。unsigned Q1外露边界距离、相交/near-touch、跨区凸单元重叠和数值不确定性分别记录；正距离和非零弱力不能单独认定有效接触，完整包含关系/机构自重叠尚未验证。

右侧条带固定参考x89..92、6列480cells，保留实际位移后的外界与原顶uy约束。完整条带极值覆盖80行，局部图是上部裁剪；Green应变不换算为工程压缩百分比，cellwise Hu代表点不当作独立九点量。右条带最大节点位移不是尖端间隙；其极值节点可随状态切换，具体位置见原摘要。右侧场变化不能单独证明边界污染或域宽充分。

圆形工件表面的法向随位置变化；下半体材料/Hu/总Fx/Fy是有符号弱式合力，Hu也不能当作连续表面压力。因此本卡不授压力、有效夹持、完整卸载/自由释放、稳定性、网格/域宽收敛或HF5资格；本卡不新增HP，已有选定加载态参考保留其原范围，不转授当前卸载端点。

本次六个请求态完成 1.00→0.90→0.75→0.50→0.25→0 mm，原生产门通过。末态 R=1.6317430051868603e−25 N、q_out=−8.903399720651071e−25 mm、下半工件总 Fy=−1.0014711119833229e−28 N；尖端／实际 Q1 边界距离1 mm、两类最小J=1。微小Hu、应变及不同逻辑SHA仍原样保留，因此不把结果写成逐位恢复或自由工件释放。零目标原内部发生4次 unsupported_arithmetic_range 完整步拒绝，随后半步接受，第11检查通过原门；无需把这一已完成过程重跑为精确零。

功能上的下一缺口是全程结果分散在14个成功子段，人工尚需逐页拼接。优先将已有普通摘要汇成按真实顺序的加载／卸载响应视图、状态表和人工页，直接检查接近、作用力、回程和原收敛历史。当前没有新增求解或例行HP的具体必要；既有峰值1.06参考仍仅授该保存态范围。

helper `4475.934626200004`/6600 s，outer `4477.766651500002`/6660 s；controller5400 s，显示共享600 s；进程树采样峰值 `1143726080` B/64 GiB，清理 `True`。四库线程配置上限16，不等于实测16核利用率；pure viewer原内部8 GiB限制保持。

原窗口封存 `70` 个输出、`164239516` B；闭卡仅继承seal并核大小。实际审查 `pass_record_audit`，像素记录 `pass_root_visual_inspection_with_minor_layout_note`。新测试 `0`、默认安装 `0`、wrapper新HP `0`。

错误原值：helper `未提供`；API `未提供`；outer `未提供`。生产与显示阶段状态分开保留，不覆盖历史，不进行外部重试、修复重跑、延期、force、回滚或删除。

![view/comparison.png](run_001/view/comparison.png)

![view/distances_forces.png](run_001/view/distances_forces.png)

![view/peak_fields.png](run_001/view/peak_fields.png)

![view/right_medium.png](run_001/view/right_medium.png)

![convergence/convergence.png](run_001/convergence/convergence.png)

![view/wave_circle_tip_unload3/actual_states.gif](run_001/view/wave_circle_tip_unload3/actual_states.gif)

后续决策：Unify fourteen existing ordinary saved summaries and convergence records into one chronological loading/unloading response view and manual page

复核/恢复：主仓库origin保持https://github.com/dudaxing/Compliant-TO-TMC.git，后续开发在main。另一位置执行git clone该地址后，先读README、docs/CURRENT_STATUS.md、docs/RESUME_DEVELOPMENT.md及本卡RESULTS/NEXT_STEPS；依据仓库固定环境重建依赖，再核对protocol、author/authorization和保存态来源。不要重跑已关闭launcher或从显示数组重建锚；下一科学窗口使用公开evaluate_native(..., saved_result=..., selected_state_index=..., extend_path=True)和明确的新任务。

恢复起点命令（PowerShell；读取状态，不启动旧运行）：

```powershell
git clone https://github.com/dudaxing/Compliant-TO-TMC.git
git -C Compliant-TO-TMC status --short --branch
Get-Content -LiteralPath Compliant-TO-TMC/docs/RESUME_DEVELOPMENT.md
```

入口：[人工页](run_001/REVIEW.md) · [原结果](run_001/wave_circle_tip_unload3/result.json) · [原响应](run_001/wave_circle_tip_unload3/response.json) · [收敛记录](run_001/convergence/convergence.json) · [outer](step_launch.json) · [helper](run_001/execution_receipt.json) · [实际审查](author/ACTUAL_REVIEW.md) · [像素记录](author/pixel_QA.json) · [闭卡JSON](author/closure.json) · [后续](NEXT_STEPS.md)
