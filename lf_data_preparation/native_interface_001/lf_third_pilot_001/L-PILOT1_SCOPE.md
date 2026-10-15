# L-PILOT1：第三个LF夹持器独立小行程试算

日期2026-10-15（Asia/Seoul）。整体目标是独立HF从普通LF几何给出有限变形/TMC正向结果；本阶段使已经兼容的第三wave结构产生真实加载响应，检验功能是否能从两例扩展到第三例。前置L-THIRD1通过41项输入/未变形检查，但未证明力学收敛。

## 直接授权与明确范围

用户原请求：“好的，按你的建议进行第三个LF夹持器0→0.25→0.50 mm的独立试算，注意做好记录，可视化实际变形、反力和收敛情况，再根据结果安排后续计算。” 这已授权当前试算与必要显示/修复，无需再次申请相同工作。新controller1800秒／viewer600秒／helper2700秒／outer2760秒，进程树采样RSS8GiB；三个既有有限控制器测试先运行、最多60秒，含在2700秒。一次外部启动，首个终端错误停止、无修复重跑/延期/force/自动回滚；允许原控制器内部回溯/二分。合作stop和采样不等于OS硬限额。

源基线main e010d20938ae38f66a8b6a6fae9df8291fe1a59a；本轮新源码和两处必要默认/测试改动按protocol单独SHA绑定，不声称已包含在旧提交。原科学版本/公式/生产门及历史结果保持。

## 必要兼容修复和唯一测试

静读发现load_only接受态不含original_target_index/leg，既存pure viewer和进度记录会取键失败。最小通用修复是对所有接受态添加已有advance递归与for循环所计算的两个标签；ordered_cycle行为与机械语句不变。状态数组/物理stateSHA不变，新JSON正常包含新字段，descriptorSHA相应变化，不回写旧结果。

原test_split_cycle.py仅将过时的字段absence断言改为确切load_only标签；唯一运行三个既有单胞注入控制器测试：default加载标签/非法路径门、ordered_cycle重复目标与独立dense代数、descending二分保原目标标签/回滚。它们不是夹持器材料或接触资格，生产hook计数不包含这些toy算例；不运行完整测试套件。

## 单次真实生产

新pilot_task仅改变原task的input.target_mm=0.5、path=load_only[0,0.25,0.5]及task_id/purpose/parameter_origin三普通说明字段（去除旧ALPHA1误导标签）。其余原几何、掩码、h0.5、E1MPa、nu0.3、厚20mm、alpha5e-7、gamma1e-6、Lr80mm、固定方体/边界及原数值门保持。原25目标task字节保持，不从旧状态/矩阵warm start，不宣称完成完整循环。

复用evaluate_native一次，mechanical/chunk256/port_projection；三原目标必须按序完成，原内部二分可增加接受态。缓存保存/摘要不新增F/T，原HP/JIT计数保持原语义，不新增HP；JAX tangent本身可能编译，不能把旧计数JIT=0解释为零JAX编译。

## 可视化、证据与结果驱动计划

生产成功后原pure viewer新进程一次，覆盖所有真实接受态，生成3PNG/N帧GIF及几何/节点作用表；最多各新PNG一次像素检查。另从同一新普通result.json生成收敛JSON及一张PNG，保全部真实Newton/回溯/失败/线性求解记录，无新F/T/HP。图展示实际×1与必要镜像、R/q_out、下半工件材料/Hu/总弱式作用、同定义有限距离和分区J；收敛图不插值、不混合不同单位或把全局力平衡诊断当同一残差门。

所有新输出在原helper窗口封存；typed failure保存真实partial后停止后续显示，保实际已改元数据源，无自动回滚。失败不在本窗口改源重跑。结果记录目标/实现/原因/实际数值、图、收敛、资源与边界，并同步main及独立恢复目录。

本阶段不新增独参/压力/有效夹持/释放/稳定性/全路径/HF5资格；非零工件作用不单独证明接触。短load_only保存态当前不能直接延至1.2mm循环；若试算合理，下一阶段另从零完成保留25目标，根据实际效果再作行程取舍。
