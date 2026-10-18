# L-CTIPPILOT1：圆形固定工件实际短加载

执行状态 **PASS**；生产 `success`、helper `pass`、outer `pass`，停止阶段 `final_binding_and_seal`。基线 main `036fd5d9298525894b5f90a37dab8f258d6cc9b1`；science 0.5.0／b1334 基线保持。

目标是让已准备的 wave LF 结构，在固定圆形工件下从零完成0→0.25→0.50 mm并显示实际变形、反力和收敛。该步检验圆形构模进入真实非线性/TMC工作流的能力。

工件半径9 mm、中心(80,40) mm、固定ux/uy；其余E=1 MPa、nu=0.3、plane strain、厚20 mm、h=0.5 mm、92×40 mm下半域、gamma=1e-6、alpha=5e-7、Lr=80 mm及支撑/平均端口/对称保持。仅更新四个任务说明字段；prepared父任务已经是input.target0.50/load_only三目标，路径及物理原值保持，全部旧结果不改。

保存接受态数 `3`；helper接受回调数 `3`，两者分别记录，缺失保存结果不写成零。路径原标志：`{'path_kind': 'load_only', 'targets_mm': [0.0, 0.25, 0.5], 'reached_displacement': 0.5, 'path_completed': True, 'loading_peak_reached': True, 'task_target_executed': True, 'unload_endpoint_reached': None}`。

|接受行|原目标|路段|d mm|输入R N|q_out mm|下半体Fy N|Q1边界距离 mm|solid minJ|free-medium minJ|relative residual|
|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
|0|0|origin|0.0|0.0|0.0|0.0|1.0|1.0|1.0|0.0|
|1|1|loading|0.25|0.042743534147102635|0.24018802342288847|0.00014591711519481185|0.7598854694338719|0.9939667029510496|0.7591252661187656|1.30114129157108e-12|
|2|2|loading|0.5|0.08602790333542189|0.480914454124498|0.00047828066183543393|0.5193940639875763|0.9879538763129987|0.5165686928215502|1.2689651419092905e-12|

数值保持原保存值；完整材料/Hu/总Fx/Fy、状态SHA、约束残差/原界、整体平衡和观测原值见闭卡JSON及原结果。q_out是加权端口位移，不是表面间隙；输入R和工件力保持下半模型含义。

原生产门 `{'production_residual': '1e-9', 'average_constraint': '1e-10', 'global_force_balance': '1e-6', 'fixed_displacement_mm': '8e-11'}`；缓存门实录 `{'actual_accepted_states': 3, 'minimum_J': 0.5165686928215502, 'maximum_fixed_split_sum_mm': 0.0, 'maximum_relative_residual': 1.30114129157108e-12, 'native_constraint_bound_pass': True, 'maximum_relative_global_force_balance': 2.934241029324146e-15, 'passed': True}`。生产F/T等计数 `{'force_calls': 27, 'force_calls_completed': 27, 'tangent_calls': 15, 'tangent_calls_completed': 15, 'solver_invocations': 1, 'JIT_calls': 0, 'HP_calls': 0}`；wrapper API/solve/view调用 `{'api_started': 1, 'solve_started': 1, 'solve_completed': 1, 'api_completed': 1, 'view_child_started': 1, 'view_child_completed': 1, 'convergence_plot_started': 1, 'convergence_plot_completed': 1}`。原门未更改。

收敛原记录计数 `{'accepted_states': 3, 'newton_base_checks': 15, 'inferred_check_groups': 3, 'line_search_trials': 12, 'line_search_accepted': 12, 'line_search_rejected': 0, 'failed_attempts': 0, 'linear_solves': 14, 'maximum_bisection_depth': 0, 'zero_newton_residuals': 1}`。回溯或二分若存在，属于原控制器工作，全部实际接受态保留；不会锁定仅三态。新测试 `0`、默认安装 `0`、wrapper新HP `0`。

实际距离使用所选圆形Q1单元的物理外露阶梯边，排除对称切口；解析圆只作图示参考。无符号距离不等于有符号间隙。通用凸Q1跨区域单元重叠是另一项观察，完整包含关系及机构自重叠仍未检查；False、None与数值不确定状态分别保留。

最右尖端按唯一参考坐标(80,30)查找后跟随实际位移，不硬码节点编号；初始tip和整体最近均1mm，但不代表唯一首触。右侧介质完整逐态极值、位置与约束如已完成显示，见末尾对应摘要入口。条带按实际参考body右端与域界动态定位为x89..92、6列480cells；相接body节点仍固定，原顶uy对称保持。条带实际坐标/J/Hu只为保存态观察，不是域宽收敛。末态几何与分区场原值见闭卡JSON的last_saved_state/view_observation。若显示未完成或该项未提供，不能据缺失值判断无接触、无重叠或场稳定。

圆周局部法向随位置变化；下半工件全局Fx/Fy是含材料和Hu的有符号弱式合力，不是连续压力或圆周总法向夹持力。坐标×1，完整结构图和GIF仅作对称镜像，数值没有镜像加倍；节点箭头包含切口/内部节点，不能当作表面压力。

实际独立审阅 `pass_actual_finite_review`；像素检查 `pass_pixel_review`；逐图观察：[像素记录](author/pixel_QA.json)；若未完成则按缺失记录保留。没有新增重绘或媒体重解码。

| d mm | 同tip距离 mm | 最近距离 mm | 右介质minJ | 右介质maxabsHu 1/mm | 右条带max节点位移 mm |
|---:|---:|---:|---:|---:|---:|
|0.0|1.0|1.0|1.0|0.0|0.0|
|0.25|0.7598854694338719|0.7598854694338719|0.8663258675749972|0.0046474808126793846|0.33795963271708657|
|0.5|0.5193940639875763|0.5193940639875763|0.644133518565071|0.005909855856949434|0.7147775822035364|

## 独立物理/功能判断

本次r9/(80,40)、right92、Lr80的从零[0,.25,.5]实际完成，新的短任务path_completed/loading_peak_reached/task_target_executed为true，只表示本次0→.5指令，不是完整循环、卸载或旧路径重执行。实际已实现：新域/布置进入现有公开非线性mechanical+chunk256流程，保存真实接受态并观察指定tip、全Q1边界、弱力和右480介质单元；不是单纯未变形布置通过。

同tip/global unsigned距离三态为1、0.7598854694338719、0.5193940639875763mm。零态public firstpair在x78，tip投影在x80；后两态firstpair的机构见证就是tip：.5为(79.86088009934946,30.480605936012424)→(79.86088009934946,31)mm。目标tip实际进入最短距离层级并持续接近，回应了此前x74布置中tip落后横梁的问题。global正距离ties未穷举，不能宣称唯一最近/唯一首触；三态交叉、near-touch、raw/strict overlap和roundoff ambiguity均false，containment未测。距离仍为正，不授压力或接触资格。

.5时R=0.08602790333542189N，q_out=0.480914454124498mm；solid minJ=0.9879538763129987，非body介质minJ=0.5165686928215502。下半工件Fy=0.00047828066183543393N，material=0.0001040097253926478N、Hu=0.0003742709364427861N。它们是有符号弱式合力，不是连续压力、局部法向承载或有效夹持，Hu极值位置也不能归因全部body HuFy。

右480单元在.5的minJ=0.644133518565071，e11402/q2参考(89,31)、实际(89.05313643825475,31.011150397181808)mm；Green最小主值−0.30461585991290596为无量纲Green应变，不转换成工程压缩百分数。同单元Hu最大绝对分量0.005909855856949434/mm，代表中心参考(89.25,30.75)mm，分量[1,0,1]，有2个exact ties。该中心只是cellwise指标代表点。最大节点|u|=0.7147775822035364mm位于底右外角node184，实际(92.43489713973966,0.5672490369026598)mm；它不是tip间隙闭合。右介质参与压缩不证明域污染，3mm余量也不自动证明域宽充分或无边界影响。

与旧x74/right84在同.5比较，tip2.0389747275151535→0.5193940639875763mm、整体nearest0.6038158762254856→0.5193940639875763mm；R0.08581310622787962→0.08602790333542189N，bodyFy0.00029683638167977717→0.00047828066183543393N。这是圆心和域边界同时变化的两例，不是单一位置效应或域宽收敛试验；不能将差异归因于其中一个因素。

实际15次基点检查、12次trial全部接受、14次线性求解、0二分/failed_attempt；F27/27、T15/15、solver1、HP/JIT0。末态relative residual1.2689651419092905e-12、constraint6.938893903907228e-18/bound5e-11mm、relative global force balance5.361568321541662e-16，保原门。当前controller总1310.7252118000179s，其中kernel+transfer1305.1132949999883s；旧x74案例同15/12/14计数的总时1043.465763699991s。这里只报告不同窗口的实测成本，不把差异定性为性能基准或数值困难。

未见必须先排查才可提出单步续算的具体字段失败：tip方向目标已实际对齐，原门和全部线搜索通过。可以提出仅.5→.75以继续检验tip与最近见证是否保持对向，避免直接追大行程。medium J和右区Green说明需持续看位置/场变化，但没有依据新增门或预报.75的间距、收敛和接触。未做独立HP、压力/有效夹持、自由释放、稳定性或域宽收敛；旧布局HP不转授本布局。


![view/comparison.png](run_001/view/comparison.png)

![view/distances_forces.png](run_001/view/distances_forces.png)

![view/peak_fields.png](run_001/view/peak_fields.png)

![view/wave_circle_tip_pilot/actual_states.gif](run_001/view/wave_circle_tip_pilot/actual_states.gif)

![view/right_medium.png](run_001/view/right_medium.png)

![convergence/convergence.png](run_001/convergence/convergence.png)

helper `1332.4355910999875` s／2700 s，outer `1335.5250312999997` s／2760 s；controller 1800 s，viewer＋收敛＋人工页共享600 s；进程树采样峰值 `946929664` B／64 GiB，清理 `True`。终端 `{'chunk_id': '96f02a', 'exit_code': 0, 'session_id': 52162, 'session_closed': True}`。原窗口封存 46 个输出、63251881 B，状态 `complete_inside_original_helper_window`；闭卡继承producer seal＋stat，不重读载荷。

真实错误：helper `未提供`；API `未提供`；outer `未提供`。生产成功与显示阶段失败分别报告，不回写原API或原结果。

本轮不取得独立HP、压力、有效夹持、完整加载卸载循环、卸载/自由释放、稳定性或HF5资格；制造仍pending。

下一步：建议另行授权仅一个新目标：沿已安装load_only显式保存态延伸接口，从本次accepted2/global2的0.50mm续算到0.75mm；保留r9/(80,40)、right92、Lr80、原物理/门/设置，不回放加载前缀。新fulltask只追加0.75并提高input.target到0.75及必要说明身份；先fresh验证0.50锚SHA/R。资源拟controller1800/display600/helper2700/outer2760秒、64GiB、四库16、viewer内部8GiB；首个终端失败保partial并关闭，不外部重试。本建议不启动或授权新窗口，不预测未来距离/收敛。

审查入口：[原响应](run_001/wave_circle_tip_pilot/response.json) · [原结果](run_001/wave_circle_tip_pilot/result.json) · [人工页](run_001/REVIEW.md) · [显示摘要](run_001/view/wave_circle_tip_pilot/summary.json) · [收敛JSON](run_001/convergence/convergence.json) · [helper](run_001/execution_receipt.json) · [outer](pilot_launch.json) · [实际审阅](author/ACTUAL_REVIEW.md) · [闭卡JSON](author/closure.json)
