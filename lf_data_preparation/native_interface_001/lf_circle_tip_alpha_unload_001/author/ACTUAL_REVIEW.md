# L-CTIPAUNLOAD1 有限实际审阅

结论：**PASS**，10项有限核对通过，无阻断。该结论基于唯一真实终端结果，不将准备期尚未授权的SOURCE快照改写为执行记录。

目标是让独立TMC评估器在新α下完成可恢复的首次卸载，并显示真实变形、输入反力、工件作用及收敛。此轮只从已验证1.06 mm峰值推进到1.05 mm，不重放13目标加载前缀。

实际独立批准后唯一启动300b2a／session88227，f7eaee终端退出0；helper/outer均PASS。outer557.5321556秒，helper553.9062700秒，共享显示10.2514497秒，采样进程树峰值894627840 B，SUP2清理确认，无活动会话。原controller1800／display600／helper2700／outer2760秒、64GiB／四库线程上限16和viewer内部8GiB保持；线程上限不等于实测16核利用率。

| 有限项 | 结论 |
|---|---|
|explicit_authorization_and_frozen_identity|独立真实批准为true，协议SHA一致；原未授权SOURCE10历史快照保留，其14份普通候选/支持字节与原封条一致。|
|unique_terminal_resources_cleanup|唯一launcher退出0，helper/outer PASS，原1800/600/2700/2760秒及64GiB窗口内完成；SUP2同实例清理覆盖与句柄释放已证实，无后续重启。|
|physics_task_prefix_and_settings|task仅load_only→ordered_cycle并追加1.05，13目标前缀、全部其余字段与四metadata原保；α2.5e-7、r9/c80/right92/Lr80及非clock设置、原门保持。|
|fresh_saved_anchor_and_accepted_identity|锚child0/global12的SHA及bitwise signed R与父accepted12一致；fresh F/T各1、1次Newton检查。child1/global13是真实unloading1.05；未读取旧F/T/矩阵或重放前缀。|
|production_equilibrium_and_saved_values|两态result/summary身份、R/q和工件总力精确对账；原残差、native约束、global balance、fixed split和J>0均通过，缓存原门不放宽。|
|complete_convergence_and_call_records|原7检查、5接受试探、0拒绝/失败/二分、6线性求解完整保留并与原路径历史一致；F12/T7均完成，含锚重算，HP/JIT均0。|
|same_alpha_same_input_raw_comparison|同新αALPHA1 loading行11/global11与新unloading行1/global13逐项核13条原值及卸载−加载差；两状态SHA/原leg保留，不去重、不插值、不新增相等性门。|
|true_LAST_five_PNG_and_root_QA|静态显示真实LAST1.05，peak_index仍为锚0；原viewer4PNG+收敛1PNG和2帧GIF有原窗口封条。root五PNG各一次原分辨率检查通过并记录可视限制；actual_total_PNGs缺失保持，不回填producer。|
|finite_footprint_and_original_window_seals|原窗口38份/63308860B封条与stat一致；viewer解码5归档/63字段，geometry/nodal/boundary/region各2。所有输入绑定未变；无外部重试、修复、HP、测试、默认安装/改核或旧记录改写。|
|qualification_and_closure_contract|只完成1.06→1.05后缀；原task/full路径false和API producer flags/reference未提供保留。父峰值HP不迁移至卸载；有限实际审阅与NEXT字段满足已审close合同，发布/闭卡由root后续执行。|

| 保存态 | global目标／raw leg | R N | q_out mm | 工件总Fy N | unsigned尖端/Q1距离 mm | 全介质minJ |
|---|---|---|---|---|---|---|
| 0／锚1.06 mm | 12／resume_origin | 0.19522304147728387 | 0.9946672298032242 | 0.012372524610902783 | 0.008227522522737729 | 0.00046587891715793817 |
| 1／新1.05 mm | 13／unloading | 0.19075825359298318 | 0.9921056957636342 | 0.009628058927231453 | 0.010336706005979579 | 0.0012518161249492532 |

末态工件Fy=material 0.006620004745329734 + Hu 0.003008054181901719 N。保持下半模型有符号原值，不镜像倍增；节点弱力不称为压力或连续面牵引。q_out为加权端口位移，距离为无符号直Q1边界距离，不证明解析圆接触或释放。

同新α原加载1.05 mm逐项保留13指标原值和各自状态SHA。卸载−加载：ΔR=−1.712074926274454e−12 N，Δ总Fy=−1.6689618437260023e−12 N，Δq_out=4.6450621127291924e−12 mm，Δunsigned距离=−5.051958851254312e−12 mm。差量很小只作描述，不新增相等性门，不推出全路径可逆、无耗散或释放。原完整前缀未在child执行，task_target_executed及full original/extended path均保持false。

7次Newton检查包含锚1次和卸载6次，5次试探全接受；拒绝、失败和二分均0，线性求解6次；F12/T7全部完成。最大相对残差3.863291644968067e−10，最大relative global balance4.3523775792780164e−14，fixed split0，原native约束与J>0均通过。右条带maxabsHu由0.05494412008014038略升至0.05524822338548496 1/mm，不能概括为所有场量均改善。

root于56bb29对五张新PNG各作一次原分辨率检查，结果pass_root_visual_inspection_with_visibility_limits；本审阅不另开媒体。静态图真实显示LAST1.05，legacy peak_fields文件名不改变其LAST标题，peak_index仍为锚0。微米距离不能靠全图分辨；tip/global距离曲线重合、J均值≠九点minJ、Hu范数≠最大绝对分量、右侧裁剪≠全480单元统计，收敛约束线位于图顶界等限制已保留。2帧GIF未额外解码，无重绘。

helper没有actual_total_PNGs字段，原记录保持缺失；5PNG由原封条路径、viewer 4PNG＋convergence 1PNG及五次QA共同确定，不向producer补写。原窗口38份输出共63308860 B，全部stat大小与原封条一致；未在窗口后读取或重新哈希数组、gzip、CSV或媒体。新HP、测试、默认修改/安装、外部重试和旧记录改写均0。

AREF1只核父峰值一态及其原PORT范围，不授此卸载态独立参考；API producer flags和reference not_provided保持。此轮通过不授完整循环、压力、有效夹持、自由工件释放、稳定性、α独立、网格／域宽收敛或HF5。下一阶段建议由独立NEXT_DECISION记录；本审阅不启动下一目标、不执行闭卡或推送。
