# L-CTIPSTEP9：最右尖端对向圆形工件的保存态延伸

2026-10-19；执行 **PASS**；图像QA `pass_root_visual_inspection`，本阶段完整完成 `True`。生产 `success`，helper `pass`，outer `pass`；实际停止阶段 `final_binding_and_seal`。

整体目标是把LF给出的夹持器几何接入独立、可恢复的高保真大变形/TMC有限元分析，逐步实现对工件接近、接触后的变形与作用力及卸载响应的可审查计算。结构优化、有效夹持判定和HF5标签尚不能由单段前向计算替代。

本轮做什么及原因：复用已安装load_only显式保存态延伸接口，从已成功的1.04 mm状态重新核验平衡及SHA/有符号R，再执行唯一新目标1.05 mm。该小步用来观察最右尖端能否继续对向接近，并查看右侧介质压缩和计算成本，避免依据初始布置直接推断大行程效果。未从零重放原加载前缀，也未改默认HF源码。

半径9 mm、圆心(80,40) mm、固定工件ux/uy、右域界92 mm、正则化长度80 mm保持；下半域92×40 mm、h=0.5 mm、厚20 mm、E=1 MPa、nu=0.3、plane strain、gamma=1e-6、alpha=5e-7及原支撑/平均端口/对称保持。完整任务[0,.25,.5,.75,.90,.95,.98,1.00,1.02,1.03,1.04,1.05]仅追加1.05并将input.target改为1.05及四项说明身份；本次请求后缀[1.04,1.05]。

已完成及实际效果：保存接受态 `2`，helper回调 `2`。缺失保存结果记为null，实际二分增加的接受态全部保留。父结果SHA `505852aced7b43b13524ef00af9de9f190b11a6f310ff9bbd7fe3a35c2ccf799` 与授权绑定一致，原成功与失败历史保留。

|child行|global目标|路段|d mm|输入R N|q_out mm|body Fy N|tip距离 mm|最近边界 mm|solid minJ|medium minJ|
|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
|0|10|resume_origin|1.04|0.18849743751609724|0.9834816595480069|0.00885936998869095|0.01913067004654323|0.01913067004654323|0.9754825764272813|0.008284170402941726|
|1|11|loading|1.05|0.1917119776052685|0.9893918140696001|0.010344906240341959|0.013434644879975366|0.013434644879975366|0.9753318497649357|0.0032268105740065082|

|d mm|右介质 minJ|右介质 maxabsHu 1/mm|右条带最大节点位移 mm|relative residual|
|---:|---:|---:|---:|---:|
|1.04|0.19568872186830083|0.07697553677344571|1.057265926156959|1.246258475664169e-12|
|1.05|0.19270007749393256|0.08409066184842073|1.0507256158949554|1.2186285374229884e-12|

表中保留原数值。q_out是加权端口位移，不是表面间隙；输入R与工件合力为原下半模型数值。完整Fx/Fy的material/Hu/total分量、实际尖端及边界见证、分区极值与位置、原残差/约束界和整体平衡见[闭卡JSON](author/closure.json)及[显示摘要](run_001/view/wave_circle_tip_step9/summary.json)。

原验收门 `{'production_residual': '1e-9', 'average_constraint': '1e-10', 'global_force_balance': '1e-6', 'fixed_displacement_mm': '8e-11'}`；缓存检查 `{'actual_accepted_states': 2, 'minimum_J': 0.0032268105740065082, 'maximum_fixed_split_sum_mm': 0.0, 'maximum_relative_residual': 1.246258475664169e-12, 'native_constraint_bound_pass': True, 'maximum_relative_global_force_balance': 2.378625104655694e-15, 'passed': True}`。生产调用 `{'force_calls': 12, 'force_calls_completed': 12, 'tangent_calls': 7, 'tangent_calls_completed': 7, 'solver_invocations': 1, 'JIT_calls': 0, 'HP_calls': 0}`；收敛计数 `{'accepted_states': 2, 'newton_base_checks': 7, 'inferred_check_groups': 2, 'line_search_trials': 5, 'line_search_accepted': 5, 'line_search_rejected': 0, 'failed_attempts': 0, 'linear_solves': 6, 'maximum_bisection_depth': 0, 'zero_newton_residuals': 0}`。API/solver/view等包装调用 `{'api_started': 1, 'solve_started': 1, 'solve_completed': 1, 'api_completed': 1, 'view_child_started': 1, 'view_child_completed': 1, 'convergence_plot_started': 1, 'convergence_plot_completed': 1}`。原门和非clock设置不变；minimum_increment=0.00625 mm保持，0.01 mm可直接尝试，若失败则半步0.005 mm低于原限值，按原规则停止。

路径实际标志 `{'path_kind': 'load_only', 'targets_mm': [1.04, 1.05], 'reached_displacement': 1.05, 'path_completed': True, 'loading_peak_reached': True, 'new_peak_reached': True, 'extended_segment_completed': True, 'task_target_executed': False, 'full_original_path_completed': False, 'full_extended_path_completed': False, 'unload_endpoint_reached': None}`。新峰值与延伸段完成只说明本段；task_target_executed、full_original_path_completed、full_extended_path_completed保持false，完整加载前缀没有在child中执行。没有把本段PASS授予整条路径或独立参考。

图中实际坐标×1；完整结构和动画只作对称镜像，数值没有镜像加倍。尖端按唯一参考坐标(80,30)动态查找并跟随实际位移。unsigned Q1外露边界距离、相交/near-touch、跨区凸单元重叠和数值不确定性分别记录；正距离和非零弱力不能单独认定有效接触，完整包含关系/机构自重叠尚未验证。

右侧条带固定参考x89..92、6列480cells，保留实际位移后的外界与原顶uy约束。完整条带极值覆盖80行，局部图是上部裁剪；Green应变不换算为工程压缩百分比，cellwise Hu代表点不当作独立九点量。右条带最大节点位移不是尖端间隙；其极值节点可随状态切换，具体位置见原摘要。右侧场变化不能单独证明边界污染或域宽充分。

圆形工件表面的法向随位置变化；下半体材料/Hu/总Fx/Fy是有符号弱式合力，Hu也不能当作连续表面压力。因此尚无压力、有效夹持、卸载/自由释放、稳定性、网格/域宽收敛或HF5资格；当前布置也未做新HP，旧布置参考不转授。

1.04→1.05 mm时，tip实际坐标由(79.688496386,30.980869330)变为(79.687143551,30.986565355) mm；tip与完整Q1共同最近距离由19.130670降至13.434645微米。两态相交/near-touch/跨区重叠标志false，containment未测。这是unsigned Q1观察，不是连续圆面有符号gap或首次接触证明。输入R=0.191711977605 N，q_out=0.98939181407 mm仍为端口位移而非gap。下半工件全局竖向弱式Fy total/material/Hu=0.0103449062403/0.00589587323608/0.00444903300426 N，Hu占有符号total约43.01%；镜像不翻倍，这些量不授连续压力或有效夹持资格。

实体minJ=0.975331850与全非工件介质minJ=0.00322681057401分开；后者较上态下降61.05%，但正值与全部原严格门通过。medium maxabsHu=0.46195690592/mm。本轮没有新定位1.05 mm全介质极值：旧LOCAL1关于1.03/1.04的e11199或e11344见证不能转授本态，也不因标量J较小自动判失败、例行插HP或要求每微小步重复定位。

新right480cells全条带minJ=0.192700077494，e11218/Simpson2、local[-1.0, 1.0]、reference[89.0, 30.5]、actual[89.01164368139588, 30.41491233495974] mm；maxabsHu=0.0840906618484/mm（上态1.092倍），首代表e11591/component[1, 0, 1]、actual Q1中心[91.98635366685926, 30.405524054822788] mm、exactties=2。Hu逐单元常值，中心仅代表标记，未声明全部并列唯一。right最大节点位移实际仍node178/reference[89.0, 0.0]，norm由1.057265926降至1.050725616 mm，不是gap、卸载或更安全证据；单域宽变化不证明污染或充分。

新目标需6次Newton检查：第5次尚高于原1e-9门，继续到第6次约1.22e-12；5次线搜索全部接受，无拒绝/失败/二分。总7次base checks（锚1+目标6）、F12/T7、solver1、HP/JIT0。新约束残差为精确0，原symlog显示保留，未造小正值。controller约620.924秒，在原1800秒内；数值和五图QA均通过，没有已知矛盾要求修力核或改原门。

helper `636.4604457999994`/2700 s，outer `637.1806968000019`/2760 s；controller1800 s，显示共享600 s；进程树采样峰值 `891568128` B/64 GiB，清理 `True`。四库线程配置上限16，不等于实测16核利用率；pure viewer原内部8 GiB限制保持。

原窗口封存 `38` 个输出、`63527568` B；闭卡仅继承seal并核大小。实际审查 `pass_record_audit`，像素记录 `pass_root_visual_inspection`。新测试 `0`、默认安装 `0`、wrapper新HP `0`。

错误原值：helper `未提供`；API `未提供`；outer `未提供`。生产与显示阶段状态分开保留，不覆盖历史，不进行外部重试、修复重跑、延期、force、回滚或删除。

![view/comparison.png](run_001/view/comparison.png)

![view/distances_forces.png](run_001/view/distances_forces.png)

![view/peak_fields.png](run_001/view/peak_fields.png)

![view/right_medium.png](run_001/view/right_medium.png)

![convergence/convergence.png](run_001/convergence/convergence.png)

![view/wave_circle_tip_step9/actual_states.gif](run_001/view/wave_circle_tip_step9/actual_states.gif)

后续决策：建议下一阶段L-CTIPSTEP10复用已安装load_only保存态延伸API，从成功1.05 mm末态仅推进到1.06 mm；保持全部原物理、非clock设置、验收门与完整嵌套历史，继续实际变形、反力、尖端、右介质和收敛记录。该单目标须取得新的明确执行授权，本轮没有执行后续加载。

复核/恢复：主仓库origin保持https://github.com/dudaxing/Compliant-TO-TMC.git，后续开发在main。另一位置执行git clone该地址后，先读README、docs/CURRENT_STATUS.md、docs/RESUME_DEVELOPMENT.md及本卡RESULTS/NEXT_STEPS；依据仓库固定环境重建依赖，再核对protocol、author/authorization和保存态来源。不要重跑已关闭launcher或从显示数组重建锚；下一科学窗口使用公开evaluate_native(..., saved_result=..., selected_state_index=..., extend_path=True)和明确的新任务。

恢复起点命令（PowerShell；读取状态，不启动旧运行）：

```powershell
git clone https://github.com/dudaxing/Compliant-TO-TMC.git
git -C Compliant-TO-TMC status --short --branch
Get-Content -LiteralPath Compliant-TO-TMC/docs/RESUME_DEVELOPMENT.md
```

入口：[人工页](run_001/REVIEW.md) · [原结果](run_001/wave_circle_tip_step9/result.json) · [原响应](run_001/wave_circle_tip_step9/response.json) · [收敛记录](run_001/convergence/convergence.json) · [outer](step_launch.json) · [helper](run_001/execution_receipt.json) · [实际审查](author/ACTUAL_REVIEW.md) · [像素记录](author/pixel_QA.json) · [闭卡JSON](author/closure.json) · [后续](NEXT_STEPS.md)
