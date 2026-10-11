# 当前接续：M-BOUND1保存Q1 Hu顶点作用实际执行已闭卡

2026-10-11。整体目标仍是读取普通 LF 几何的独立 HF 有限变形／TMC 前向评估，提供结构实际变形、输入反力和可解释的工件作用，逐步支持同任务候选比较及正式 HF5。HF 与 LF 优化断开，不调用 dmftd；后续只在 main 开发，origin 保持 https://github.com/dudaxing/Compliant-TO-TMC.git。

直接人类批准后，M-BOUND1 唯一实际执行 PASS，数值窗口已结束：原 loading6／0.85 mm、13／1.20 mm，两 forces NPZ／两字段、两次新公共入口，两态合计1444 单元／10 组／2 整体／1406 节点行／24 端点／14 原类别行与两 PNG。45 份原字节绑定保持；原 Q1 四顶点模式及每态703工件节点／1406 DOF的原序 scatter 数值精确对账通过，原 nodal L1 门及新增 8eps·原 local L1 无地板重组门分别保留并通过。一次启动、exit0、stopnull，无重试、修复重跑、延期或 force。

实际 outer 为 7.165070099988952 秒、采样 tree RSS126521344 B；helper 为 6.821014200002537 秒、采样 own RSS122286080 B，是成功收据构造前快照。采样内存不代表硬内存上限；mechanical_hooks_monitored=false，调用范围由冻结实现、计数与收据支持，不宣称独立动态仪器覆盖。独立终态核查 PASS，保存态物理解读及两张原像素检查已归档。

两态 body、bottom_owner、left_owner、right_owner 的局部保存合力均为 (0,0) N；两个 corner_only owner 的整体 Hu 作用分别为 (-0.0002573690035747477,+0.0011575021871015807) 与 (-0.00031478888287665577,+0.0012668445429290084) N。它们与 local 整体的保存差均为零；与原 state/nodal 整体 Hu 作用的差仅为记录中的浮点余差。side owner 的两顶点相消不代表每个顶点或组装后边界节点作用为零。owner 角色、单元及原七类节点是不同划分；corner_only owner 不等于 physical_corner 节点类别，跨表达差仍只描述。

两张新图显示参考位置、有符号局部作用与 owner／节点分组；每个 panel 独立尺度，绝对值须看标签或 CSV。端点图局部箭头穿过数字块，原像素仍可读；极小条靠近零不易辨识。本卡不重绘。原 24 帧实际变形 GIF、工件 total/material/Hu 三分量、保持反力及镜像输出继续可用；原 M-REF2 的 24 态／48 HP 工件力参考资格保持，切线仍限原 PORT 方向。冻结 protocol/card 的 False 字段属于准备历史，实际批准和终态分别记录。

本次已解释当前固定半方体矩形 Q1 任务的离散 Hu 合力来源，无证据要求重开 Hu/DD 核或再扩展同类全24态账本。最近下一步先准备同物理任务的最小网格／正则参数稳定性比较：核既有 h1/h0.5 与参数探索是否可比，复用现有曲线、API、GIF 和 48 HP，再只选择确实缺少的一项新证据。此处仅记录判断，不预设新模型、求解次数、验收门或资源卡，也不执行新的数值任务。

连续总压力、可移动工件与摩擦、有效夹持、网格／参数物理稳定性、一般输入／全列切线及正式 HF5 标签排名仍未完成。本卡未新增力核、切线、HP 或平衡路径，科学版本与原资格保持。

[实际结果](RESULTS.md) · [后续判断](NEXT_STEP_REVIEW.md) · [端点作用图](run_001/Q1_Hu_endpoint_actions.png) · [owner／节点对比](run_001/Hu_owner_node_comparison.png) · [实际授权](author/authorization.json) · [终态核对](author/terminal_execution_review.json) · [物理解读](author/physical_results_review.json) · [像素检查](author/visual_review.json)

<details>
<summary>更新前完整原文（历史状态不代表当前）</summary>

# M-BOUND1 保存Q1 Hu顶点作用候选：待批准（2026-10-11）

整体目标仍是独立 HF 有限变形／TMC 前向评估，从普通 LF 几何得到结构实际变形与工件作用。main开发，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git；HF与LF优化断开。

M-VOLUME1已唯一实际PASS闭卡、发布／独立恢复于main0d83b18。四个局部case的材料九点体积观察与原保存DD弱力接近，现有证据不要求重开DD核。固定工件total/material/Hu总力、保持反力、24态／48HP工件力参考、实际变形及三分量节点图均已实现并保留。

当前新增M-BOUND1公共入口，直接关联原Q1 Hu单元八值与原工件拓扑，显示四顶点符号、side成对平移相消、两corner_only与整体作用、owner与原节点分组差别。原论文式(6)和源码的exp(-5J)作用不等于替代能量的梯度；不引入该错误验收。原fixed_dofs字段是计数而非列表的包装假设已在运行前修正。

本卡拟仅读原6／0.85mm、13／1.20mm，两forces NPZ／2字段、2次新公共入口；每态722support单元／703工件节点／2738local出现。仅compact1406DOF按原C序scatter，数值精确对原节点；原nodal L1门保留，新local重组单独使用8eps·对应原local L1无地板。只复制原六力文本与七类表，跨分组差描述，不升格为压力。

当前仅源码、AST、普通元数据及原字节核查，未导入候选、解码NPZ、调用API／新fsum／绘图。新卡一次helper180秒／outer240秒／采样8GiB，首错停止、无重试／修复重跑／延期／force，待人类批准。预期1444cell／10group／2whole／1406node／24endpoint／14原category行和两PNG；新图均参考几何且独立尺度，实际变形复用原24帧GIF。

连续总Hu边界压力、可移动工件／摩擦、有效夹持、物理参数与网格稳定性及正式HF5标签排名仍未完成。按本卡实际结果再选择下一功能或稳定性验证，不预先扩展路径／HP／求解。

[具体卡](M-BOUND1_CARD.md) · [协议](protocol.json) · [公共入口](../../../hf_repo/src/hf_eval/saved_q1_hu_boundary.py) · [薄执行器](execute_saved_hu_boundary.py) · [最终输入核查](author/final_input_scope.json) · [物理依据](author/physical_basis.json) · [原论文核查](author/paper_formula_check.json) · [独立静审](author/static_physics_review.json) · [前次结果](../nested_material_volume_001/RESULTS.md) · [原实际GIF](../../../functional_views/native_nested_cycle_20261009/complete_001/run_001/view/fixed_square/actual_states.gif)

批准后在真实仓库根用独立HF环境一次启动：

```text
python -X utf8 -B lf_data_preparation/native_interface_001/nested_hu_boundary_001/launch_boundary.py hu_boundary --protocol lf_data_preparation/native_interface_001/nested_hu_boundary_001/protocol.json
```

</details>
