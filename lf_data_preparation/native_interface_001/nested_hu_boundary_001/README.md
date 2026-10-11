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
