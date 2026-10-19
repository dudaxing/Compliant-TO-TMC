# L-CTIPSTEP3：最右尖端对向圆形工件的保存态延伸

2026-10-19；执行 **PASS**。生产 `success`，helper `pass`，outer `pass`；实际停止阶段 `final_binding_and_seal`。

整体目标是把LF给出的夹持器几何接入独立、可恢复的高保真大变形/TMC有限元分析，逐步实现对工件接近、接触后的变形与作用力及卸载响应的可审查计算。结构优化、有效夹持判定和HF5标签尚不能由单段前向计算替代。

本轮做什么及原因：复用已安装load_only显式保存态延伸接口，从已成功的0.90 mm状态重新核验平衡及SHA/有符号R，再执行唯一新目标0.95 mm。该小步用来观察最右尖端能否继续对向接近，并查看右侧介质压缩和计算成本，避免依据初始布置直接推断大行程效果。未从零重放原加载前缀，也未改默认HF源码。

半径9 mm、圆心(80,40) mm、固定工件ux/uy、右域界92 mm、正则化长度80 mm保持；下半域92×40 mm、h=0.5 mm、厚20 mm、E=1 MPa、nu=0.3、plane strain、gamma=1e-6、alpha=5e-7及原支撑/平均端口/对称保持。完整任务[0,.25,.5,.75,.90,.95]仅追加.95并将input.target改为.95及四项说明身份；本次请求后缀[.90,.95]。

已完成及实际效果：保存接受态 `2`，helper回调 `2`。缺失保存结果记为null，实际二分增加的接受态全部保留。父结果SHA `b40bcdddf695794c7fa1e217c4c882adf6a55b927be8122cc9367bd2ac61d8be` 与授权绑定一致，原成功与失败历史保留。

|child行|global目标|路段|d mm|输入R N|q_out mm|body Fy N|tip距离 mm|最近边界 mm|solid minJ|medium minJ|
|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
|0|4|resume_origin|0.9|0.1580782308108174|0.8625531334711433|0.002963472813601691|0.13886658198055457|0.13886658198055457|0.9784853423673909|0.12974460877888705|
|1|5|loading|0.95|0.16789587547053317|0.9084279574933386|0.004007918648033684|0.09329207578756282|0.09329207578756282|0.9773497667704835|0.08323634645955613|

|d mm|右介质 minJ|右介质 maxabsHu 1/mm|右条带最大节点位移 mm|relative residual|
|---:|---:|---:|---:|---:|
|0.9|0.2716044900094883|0.016170032723724637|1.144980350028813|1.3062334517729194e-12|
|0.95|0.23815254995490032|0.026347744148167207|1.1307733507642335|1.294813041268745e-12|

表中保留原数值。q_out是加权端口位移，不是表面间隙；输入R与工件合力为原下半模型数值。完整Fx/Fy的material/Hu/total分量、实际尖端及边界见证、分区极值与位置、原残差/约束界和整体平衡见[闭卡JSON](author/closure.json)及[显示摘要](run_001/view/wave_circle_tip_step3/summary.json)。

原验收门 `{'production_residual': '1e-9', 'average_constraint': '1e-10', 'global_force_balance': '1e-6', 'fixed_displacement_mm': '8e-11'}`；缓存检查 `{'actual_accepted_states': 2, 'minimum_J': 0.08323634645955613, 'maximum_fixed_split_sum_mm': 0.0, 'maximum_relative_residual': 1.3062334517729194e-12, 'native_constraint_bound_pass': True, 'maximum_relative_global_force_balance': 1.2155508670987057e-15, 'passed': True}`。生产调用 `{'force_calls': 10, 'force_calls_completed': 10, 'tangent_calls': 6, 'tangent_calls_completed': 6, 'solver_invocations': 1, 'JIT_calls': 0, 'HP_calls': 0}`；收敛计数 `{'accepted_states': 2, 'newton_base_checks': 6, 'inferred_check_groups': 2, 'line_search_trials': 4, 'line_search_accepted': 4, 'line_search_rejected': 0, 'failed_attempts': 0, 'linear_solves': 5, 'maximum_bisection_depth': 0, 'zero_newton_residuals': 0}`。API/solver/view等包装调用 `{'api_started': 1, 'solve_started': 1, 'solve_completed': 1, 'api_completed': 1, 'view_child_started': 1, 'view_child_completed': 1, 'convergence_plot_started': 1, 'convergence_plot_completed': 1}`。原门和非clock设置不变。

路径实际标志 `{'path_kind': 'load_only', 'targets_mm': [0.9, 0.95], 'reached_displacement': 0.95, 'path_completed': True, 'loading_peak_reached': True, 'new_peak_reached': True, 'extended_segment_completed': True, 'task_target_executed': False, 'full_original_path_completed': False, 'full_extended_path_completed': False, 'unload_endpoint_reached': None}`。新峰值与延伸段完成只说明本段；task_target_executed、full_original_path_completed、full_extended_path_completed保持false，完整加载前缀没有在child中执行。没有把本段PASS授予整条路径或独立参考。

图中实际坐标×1；完整结构和动画只作对称镜像，数值没有镜像加倍。尖端按唯一参考坐标(80,30)动态查找并跟随实际位移。unsigned Q1外露边界距离、相交/near-touch、跨区凸单元重叠和数值不确定性分别记录；正距离和非零弱力不能单独认定有效接触，完整包含关系/机构自重叠尚未验证。

右侧条带固定参考x89..92、6列480cells，保留实际位移后的外界与原顶uy约束。完整条带极值覆盖80行，局部图是上部裁剪；Green应变不换算为工程压缩百分比，cellwise Hu代表点不当作独立九点量。右条带最大节点位移不是尖端间隙；其极值节点可随状态切换，具体位置见原摘要。右侧场变化不能单独证明边界污染或域宽充分。

圆形工件表面的法向随位置变化；下半体材料/Hu/总Fx/Fy是有符号弱式合力，Hu也不能当作连续表面压力。因此尚无压力、有效夹持、卸载/自由释放、稳定性、网格/域宽收敛或HF5资格；当前布置也未做新HP，旧布置参考不转授。

0.90→0.95 mm时，tip实际位置从(79.73048789,30.86113342)变为(79.71406677,30.90670792) mm；tip/整体最近Q1边界距离同为0.093292076 mm（上态0.138866582）。保存态无相交、near-touch或跨区重叠记录；共享最小距离并不表示唯一或首次接触。输入R=0.167895875 N、q_out=0.908427957 mm。下半工件total Fy=0.004007918648 N，material=0.001199564238、Hu=0.002808354410 N，Hu约占有符号总Fy的70.07%；这是弱式全局分量，不是连续表面压力或合格夹持力。

实体minJ=0.977349767，非工件介质minJ=0.083236346，不能把介质的大压缩解释成实体同等变形。介质maxabsHu升至0.331997314/mm，约为上态1.23倍；右480单元条带minJ=0.238152550，J见证仍为e11218/q2、reference(89,30.5)，新actual位置[89.01174409111486, 30.63921782979618] mm。右Hu=0.026347744/mm，较上态约1.63倍，代表单元e11591的当前Q1中心为[91.99258070031912, 30.76172289645352] mm；Hu逐单元常值，中心是代表标记，不是独立九点量。统计覆盖全部80行480cells，空间图上部裁剪另计，不能据这些单布局值判断边界污染或域宽充分。

右条带最大节点位移从1.144980350微降至1.130773351 mm，且最大值节点由184（reference外角(92,0)）切换为178（reference条带内侧底部(89,0)），新actual位置[89.68773774575207, 0.8975885270358727] mm。保留这个非单调观测及位置变化；原门不要求这些不同场量随输入单调，也不能把它叫作tip间隙或卸载表现。

helper `592.2711595000001`/2700 s，outer `593.2165563999988`/2760 s；controller1800 s，显示共享600 s；进程树采样峰值 `890200064` B/64 GiB，清理 `True`。四库线程配置上限16，不等于实测16核利用率；pure viewer原内部8 GiB限制保持。

原窗口封存 `38` 个输出、`63248310` B；闭卡仅继承seal并核大小。实际审查 `pass_record_audit`，像素记录 `pass_root_visual_inspection`。新测试 `0`、默认安装 `0`、wrapper新HP `0`。

错误原值：helper `未提供`；API `未提供`；outer `未提供`。生产与显示阶段状态分开保留，不覆盖历史，不进行外部重试、修复重跑、延期、force、回滚或删除。

![view/comparison.png](run_001/view/comparison.png)

![view/distances_forces.png](run_001/view/distances_forces.png)

![view/peak_fields.png](run_001/view/peak_fields.png)

![view/right_medium.png](run_001/view/right_medium.png)

![convergence/convergence.png](run_001/convergence/convergence.png)

![view/wave_circle_tip_step3/actual_states.gif](run_001/view/wave_circle_tip_step3/actual_states.gif)

后续决策：建议下一阶段 L-CTIPSTEP4 复用已安装 load_only 保存态延伸接口，从本轮成功0.95 mm末态只推进到0.98 mm（增量0.03 mm）；保持r9、圆心(80,40)、右域界92、Lr80、其余物理、非clock设置及原门，继续显示实际变形、尖端/整体距离、反力和工件力分解、右侧介质及收敛。本轮仅记录计划，不自动执行。

复核/恢复：主仓库origin保持https://github.com/dudaxing/Compliant-TO-TMC.git，后续开发在main。另一位置执行git clone该地址后，先读README、docs/CURRENT_STATUS.md、docs/RESUME_DEVELOPMENT.md及本卡RESULTS/NEXT_STEPS；依据仓库固定环境重建依赖，再核对protocol、author/authorization和保存态来源。不要重跑已关闭launcher或从显示数组重建锚；下一科学窗口使用公开evaluate_native(..., saved_result=..., selected_state_index=..., extend_path=True)和明确的新任务。

恢复起点命令（PowerShell；读取状态，不启动旧运行）：

```powershell
git clone https://github.com/dudaxing/Compliant-TO-TMC.git
git -C Compliant-TO-TMC status --short --branch
Get-Content -LiteralPath Compliant-TO-TMC/docs/RESUME_DEVELOPMENT.md
```

入口：[人工页](run_001/REVIEW.md) · [原结果](run_001/wave_circle_tip_step3/result.json) · [原响应](run_001/wave_circle_tip_step3/response.json) · [收敛记录](run_001/convergence/convergence.json) · [outer](step_launch.json) · [helper](run_001/execution_receipt.json) · [闭卡JSON](author/closure.json) · [实际审查](author/ACTUAL_REVIEW.md) · [像素记录](author/pixel_QA.json) · [后续](NEXT_STEPS.md)
