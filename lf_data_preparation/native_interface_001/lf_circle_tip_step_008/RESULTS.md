# L-CTIPSTEP8：最右尖端对向圆形工件的保存态延伸

2026-10-19；执行 **PASS**。生产 `success`，helper `pass`，outer `pass`；实际停止阶段 `final_binding_and_seal`。

整体目标是把LF给出的夹持器几何接入独立、可恢复的高保真大变形/TMC有限元分析，逐步实现对工件接近、接触后的变形与作用力及卸载响应的可审查计算。结构优化、有效夹持判定和HF5标签尚不能由单段前向计算替代。

本轮做什么及原因：复用已安装load_only显式保存态延伸接口，从已成功的1.03 mm状态重新核验平衡及SHA/有符号R，再执行唯一新目标1.04 mm。该小步用来观察最右尖端能否继续对向接近，并查看右侧介质压缩和计算成本，避免依据初始布置直接推断大行程效果。未从零重放原加载前缀，也未改默认HF源码。

半径9 mm、圆心(80,40) mm、固定工件ux/uy、右域界92 mm、正则化长度80 mm保持；下半域92×40 mm、h=0.5 mm、厚20 mm、E=1 MPa、nu=0.3、plane strain、gamma=1e-6、alpha=5e-7及原支撑/平均端口/对称保持。完整任务[0,.25,.5,.75,.90,.95,.98,1.00,1.02,1.03,1.04]仅追加1.04并将input.target改为1.04及四项说明身份；本次请求后缀[1.03,1.04]。

已完成及实际效果：保存接受态 `2`，helper回调 `2`。缺失保存结果记为null，实际二分增加的接受态全部保留。父结果SHA `b32e03eaf0340e912ffe534e986703647d6619ecacfc47388038756d0de98494` 与授权绑定一致，原成功与失败历史保留。

|child行|global目标|路段|d mm|输入R N|q_out mm|body Fy N|tip距离 mm|最近边界 mm|solid minJ|medium minJ|
|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
|0|9|resume_origin|1.03|0.1856995754415686|0.9764698050071479|0.007798735907497663|0.025985908706346095|0.025985908706346095|0.9756590064288826|0.014938189525383425|
|1|10|loading|1.04|0.18849743751609724|0.9834816595480069|0.00885936998869095|0.01913067004654323|0.01913067004654323|0.9754825764272813|0.008284170402941726|

|d mm|右介质 minJ|右介质 maxabsHu 1/mm|右条带最大节点位移 mm|relative residual|
|---:|---:|---:|---:|---:|
|1.03|0.19901412159349638|0.0688448907313699|1.0666036522612292|1.3853469473992041e-11|
|1.04|0.19568872186830083|0.07697553677344571|1.057265926156959|1.246258475664169e-12|

表中保留原数值。q_out是加权端口位移，不是表面间隙；输入R与工件合力为原下半模型数值。完整Fx/Fy的material/Hu/total分量、实际尖端及边界见证、分区极值与位置、原残差/约束界和整体平衡见[闭卡JSON](author/closure.json)及[显示摘要](run_001/view/wave_circle_tip_step8/summary.json)。

原验收门 `{'production_residual': '1e-9', 'average_constraint': '1e-10', 'global_force_balance': '1e-6', 'fixed_displacement_mm': '8e-11'}`；缓存检查 `{'actual_accepted_states': 2, 'minimum_J': 0.008284170402941726, 'maximum_fixed_split_sum_mm': 0.0, 'maximum_relative_residual': 1.3853469473992041e-11, 'native_constraint_bound_pass': True, 'maximum_relative_global_force_balance': 2.0302440530409943e-13, 'passed': True}`。生产调用 `{'force_calls': 10, 'force_calls_completed': 10, 'tangent_calls': 6, 'tangent_calls_completed': 6, 'solver_invocations': 1, 'JIT_calls': 0, 'HP_calls': 0}`；收敛计数 `{'accepted_states': 2, 'newton_base_checks': 6, 'inferred_check_groups': 2, 'line_search_trials': 4, 'line_search_accepted': 4, 'line_search_rejected': 0, 'failed_attempts': 0, 'linear_solves': 5, 'maximum_bisection_depth': 0, 'zero_newton_residuals': 0}`。API/solver/view等包装调用 `{'api_started': 1, 'solve_started': 1, 'solve_completed': 1, 'api_completed': 1, 'view_child_started': 1, 'view_child_completed': 1, 'convergence_plot_started': 1, 'convergence_plot_completed': 1}`。原门和非clock设置不变；minimum_increment=0.00625 mm保持，0.01 mm可直接尝试，若失败则半步0.005 mm低于原限值，按原规则停止。

路径实际标志 `{'path_kind': 'load_only', 'targets_mm': [1.03, 1.04], 'reached_displacement': 1.04, 'path_completed': True, 'loading_peak_reached': True, 'new_peak_reached': True, 'extended_segment_completed': True, 'task_target_executed': False, 'full_original_path_completed': False, 'full_extended_path_completed': False, 'unload_endpoint_reached': None}`。新峰值与延伸段完成只说明本段；task_target_executed、full_original_path_completed、full_extended_path_completed保持false，完整加载前缀没有在child中执行。没有把本段PASS授予整条路径或独立参考。

图中实际坐标×1；完整结构和动画只作对称镜像，数值没有镜像加倍。尖端按唯一参考坐标(80,30)动态查找并跟随实际位移。unsigned Q1外露边界距离、相交/near-touch、跨区凸单元重叠和数值不确定性分别记录；正距离和非零弱力不能单独认定有效接触，完整包含关系/机构自重叠尚未验证。

右侧条带固定参考x89..92、6列480cells，保留实际位移后的外界与原顶uy约束。完整条带极值覆盖80行，局部图是上部裁剪；Green应变不换算为工程压缩百分比，cellwise Hu代表点不当作独立九点量。右条带最大节点位移不是尖端间隙；其极值节点可随状态切换，具体位置见原摘要。右侧场变化不能单独证明边界污染或域宽充分。

圆形工件表面的法向随位置变化；下半体材料/Hu/总Fx/Fy是有符号弱式合力，Hu也不能当作连续表面压力。因此尚无压力、有效夹持、卸载/自由释放、稳定性、网格/域宽收敛或HF5资格；当前布置也未做新HP，旧布置参考不转授。

1.03→1.04 mm时，tip实际坐标由(79.690547235,30.974014091)变为(79.688496386,30.980869330) mm，tip及完整Q1共同最近距离由0.025985909降至0.019130670 mm（约19.131微米）。两态相交、near-touch与跨区重叠标志均false，containment未测试；这仍是unsigned Q1几何观察，不是连续圆面有符号gap或唯一首次接触证明。q_out=0.983481660 mm是端口位移而非gap。输入R=0.188497438 N；下半工件全局竖向弱力total Fy=0.008859369989 N，其中material=0.004564338477、Hu=0.004295031512 N，Hu占有符号total Fy约48.48%。镜像显示不将数值加倍，这些量不授连续压力或有效夹持资格。

实体minJ=0.975482576，全非工件介质minJ=0.008284170（较上态下降44.54%）、medium maxabsHu=0.451802887/mm；原9点Simpson含角点，不改称Gauss点或新增corner-J门。原门通过，目标5次Newton检查、4次线搜索全接受、无失败/二分，不能仅因J较小另判失败或例行插入HP。全介质minJ/maxHu仅有标量，既有derived/summary没有其元素及坐标；不得假定它们位于tip或右条带。

右侧固定480cells全条带minJ=0.195688722，见证e11218/Simpson2、local[-1.0, 1.0]，reference[89.0, 30.5]、actual[89.01458789502229, 30.433465027899604] mm；maxabsHu=0.076975537/mm（上态1.118倍），见证e11591/component[1, 0, 1]、Q1代表中心actual[91.98775562401411, 30.43098146520621] mm。Hu逐单元常值，代表中心不是额外九点采样。right最大节点位移逐态核实仍在node178/reference[89.0, 0.0]，actual[89.6489004578937, 0.8347091914899903] mm，norm由1.066603652降至1.057265926 mm；这不是tip gap、外界角点或更安全/卸载证据。单域宽场变化不证明边界污染或域宽充分。

helper `452.1993812999972`/2700 s，outer `452.9527608999997`/2760 s；controller1800 s，显示共享600 s；进程树采样峰值 `887869440` B/64 GiB，清理 `True`。四库线程配置上限16，不等于实测16核利用率；pure viewer原内部8 GiB限制保持。

原窗口封存 `38` 个输出、`63481330` B；闭卡仅继承seal并核大小。实际审查 `pass_record_audit`，像素记录 `pass_root_visual_inspection`。新测试 `0`、默认安装 `0`、wrapper新HP `0`。

错误原值：helper `未提供`；API `未提供`；outer `未提供`。生产与显示阶段状态分开保留，不覆盖历史，不进行外部重试、修复重跑、延期、force、回滚或删除。

![view/comparison.png](run_001/view/comparison.png)

![view/distances_forces.png](run_001/view/distances_forces.png)

![view/peak_fields.png](run_001/view/peak_fields.png)

![view/right_medium.png](run_001/view/right_medium.png)

![convergence/convergence.png](run_001/convergence/convergence.png)

![view/wave_circle_tip_step8/actual_states.gif](run_001/view/wave_circle_tip_step8/actual_states.gif)

后续决策：建议下一阶段L-CTIPLOCAL1优先完成1.03/1.04 mm两保存态的实际等比例尖端近景，以及全非工件介质minJ/maxabsHu的空间定位；只观察既有保存数组，不新增平衡求解。输出两张PNG、普通定位JSON和人工检查页；先让人工看清约19微米的实际Q1距离、介质极值和右侧关系，再决定是否推进1.05 mm。本轮仅记录计划，尚未实现或执行。

复核/恢复：主仓库origin保持https://github.com/dudaxing/Compliant-TO-TMC.git，后续开发在main。另一位置执行git clone该地址后，先读README、docs/CURRENT_STATUS.md、docs/RESUME_DEVELOPMENT.md及本卡RESULTS/NEXT_STEPS；依据仓库固定环境重建依赖，再核对protocol、author/authorization和保存态来源。不要重跑已关闭launcher或从显示数组重建锚；下一科学窗口使用公开evaluate_native(..., saved_result=..., selected_state_index=..., extend_path=True)和明确的新任务。

恢复起点命令（PowerShell；读取状态，不启动旧运行）：

```powershell
git clone https://github.com/dudaxing/Compliant-TO-TMC.git
git -C Compliant-TO-TMC status --short --branch
Get-Content -LiteralPath Compliant-TO-TMC/docs/RESUME_DEVELOPMENT.md
```

入口：[人工页](run_001/REVIEW.md) · [原结果](run_001/wave_circle_tip_step8/result.json) · [原响应](run_001/wave_circle_tip_step8/response.json) · [收敛记录](run_001/convergence/convergence.json) · [outer](step_launch.json) · [helper](run_001/execution_receipt.json) · [闭卡JSON](author/closure.json) · [实际审查](author/ACTUAL_REVIEW.md) · [像素记录](author/pixel_QA.json) · [后续](NEXT_STEPS.md)
