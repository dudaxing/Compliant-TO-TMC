# 当前接续：M-BOUND1 保存Q1 Hu顶点作用候选待批准（2026-10-11）

整体目标仍是独立 HF 有限变形／TMC 前向评估，从普通 LF 几何得到结构实际变形与工件作用。main开发，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git；HF与LF优化断开。

M-VOLUME1已唯一实际PASS闭卡、发布／独立恢复于main0d83b18。四个局部case的材料九点体积观察与原保存DD弱力接近，现有证据不要求重开DD核。固定工件total/material/Hu总力、保持反力、24态／48HP工件力参考、实际变形及三分量节点图均已实现并保留。

当前新增M-BOUND1公共入口，直接关联原Q1 Hu单元八值与原工件拓扑，显示四顶点符号、side成对平移相消、两corner_only与整体作用、owner与原节点分组差别。原论文式(6)和源码的exp(-5J)作用不等于替代能量的梯度；不引入该错误验收。原fixed_dofs字段是计数而非列表的包装假设已在运行前修正。

本卡拟仅读原6／0.85mm、13／1.20mm，两forces NPZ／2字段、2次新公共入口；每态722support单元／703工件节点／2738local出现。仅compact1406DOF按原C序scatter，数值精确对原节点；原nodal L1门保留，新local重组单独使用8eps·对应原local L1无地板。只复制原六力文本与七类表，跨分组差描述，不升格为压力。

当前仅源码、AST、普通元数据及原字节核查，未导入候选、解码NPZ、调用API／新fsum／绘图。新卡一次helper180秒／outer240秒／采样8GiB，首错停止、无重试／修复重跑／延期／force，待人类批准。预期1444cell／10group／2whole／1406node／24endpoint／14原category行和两PNG；新图均参考几何且独立尺度，实际变形复用原24帧GIF。

连续总Hu边界压力、可移动工件／摩擦、有效夹持、物理参数与网格稳定性及正式HF5标签排名仍未完成。按本卡实际结果再选择下一功能或稳定性验证，不预先扩展路径／HP／求解。

[具体卡](../nested_hu_boundary_001/M-BOUND1_CARD.md) · [说明](../nested_hu_boundary_001/README.md) · [冻结协议](../nested_hu_boundary_001/protocol.json)

<details>
<summary>更新前完整原文（历史状态不代表当前）</summary>

# 当前接续：M-VOLUME1九点材料体积诊断已通过（2026-10-11）

整体目标仍是读取普通 LF 几何的独立 HF 有限变形／TMC 前向评估，提供可解释的反力、工件载荷和实际变形；HF不优化、不调用dmftd，main开发，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git。

M-VOLUME1已在直接人类批准后唯一实际PASS并闭卡：原loading6／0.85mm、13／1.20mm的10406／10407两个单元，3个既存NPZ／9字段、2次公共入口，36九点采样／12深度／4单元对照行及两PNG。31冻结绑定保持，outer2.5381053000019165秒／tree RSS132591616 B；helper2.2876966999901924秒／own RSS128356352 B是成功收据构造前快照。exit0、stopnull、一次启动，无重试／修复重跑／延期／force；本卡窗口结束。独立终态核对通过，主任务实际查看两张原2100×2400像素，物理解读已归档。

四case的Fy保存W−九点观察V全为保存0；Fx只在6/10406和13/10407出现−1.6940658945086007e−21／+2.710505431213761e−20 N。峰值10406与10407的W=V Fy分别+.037219775006120934／+.08022435531475952 N，旧上缘T分别+.004917548552353244／+.01938390857410906 N。W−T差分别+.03230222645376769／+.060840446740650464 N，V并未消去体积／上缘差；现有局部证据不支持立即重开DD核追究舍入分离。

0.85mm中层Q较大，1.20mm下层Q较大。三个Q是同批九项的可加体积贡献；Qtop不是整上缘T。唯一新增8eps×同九项L1重组门四case均通过，无地板；跨表达差只描述，原保存DD力、旧迹和原门保持。两图各panel独立尺度，只能按标签／CSV跨panel比较绝对量；图为参考采样及材料贡献，实际结构变形仍见原图／24帧GIF。protocol及card的False是准备历史，实际授权和终态另有独立记录。

下一功能选择先核当前公共API已有total/material/Hu工件载荷、半模及镜像报告合同，避免重做已有功能；再根据本次局部体积／上缘证据推进尚缺的总作用量物理解释和可用输出。这里仅记粗路线，不拟定或授权新数值卡。不扩展同类全24态账本，不把P@N加一个Hu数认定为总压力。总Hu边界作用／压力、有效夹持、自由体／摩擦、网格收敛、正式标签排名与HF5仍未完成；本卡不增加力核／切线／HP／平衡路径或压力／夹持资格。

[完整结果](RESULTS.md) · [九点P图](run_001/nine_point_material_P.png) · [分层贡献图](run_001/material_depth_volume_comparison.png) · [精确对照表](run_001/cell_comparisons.csv) · [实际授权](author/authorization.json) · [终态核对](author/terminal_execution_review.json) · [物理解读](author/physical_results_review.json) · [原实际变形](../nested_material_trace_001/run_001/actual_material_trace.png)

<details>
<summary>更新前完整原文（历史状态不代表当前）</summary>

# M-VOLUME1 四个保存单元状态材料体积分候选：待批准（2026-10-11）

整体目标仍是独立 HF 有限变形／TMC 前向评估，读取普通 LF 几何，为外部研究提供反力、工件载荷和实际变形。HF不优化、不调用dmftd；main开发，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git。

M-SUPPORT1已唯一实际PASS闭卡并发布／恢复于main1671e2d。峰值bottom-owner弱Fy与旧bottom线差+0.09415598535141824 N，大差主要来自同一owner的体积与面迹表达；corner_only不能解释该量级。最近新候选M-VOLUME1聚焦原6/0.85mm和13/1.20mm的10406／10407两个单元。

新入口读取3个既存NPZ／9字段，对九点保存P／原grad和含厚度weights做材料体积重构，并按η三层显示；保留原DD收缩后的保存元素力及旧上缘迹。保存P已舍入，重构不是原DD重播；两者差单独报告，不设相等门。只对同一批九点观察项的行重组使用8eps·L1无地板新代数门，原门保持。

当前仅编码、AST、普通元数据和字节静审；尚未导入候选、解码NPZ、积分／fsum或绘图。新卡拟一次helper180秒／outer240秒／采样8GiB、首错停止、无重试／修复重跑／延期／force，待人类批准。预期36九点行／12深度行／4单元对照行及两PNG；新图显示参考单元采样和有符号材料贡献，实际变形复用原图。未证明差值连续物理原因。

总Hu边界作用／压力、有效夹持、自由体／摩擦、网格收敛及正式HF5标签排名仍未完成。最近只执行该小范围观察，按实际结果再决定原收缩核查或Hu边界功能，不预先扩展全24态或新平衡路径。

[具体卡](M-VOLUME1_CARD.md) · [协议](protocol.json) · [公共入口](../../../hf_repo/src/hf_eval/saved_material_volume.py) · [薄执行器](execute_saved_material_volume.py) · [输入核查](author/input_scope.json) · [物理依据](author/physical_basis.json) · [独立静审](author/static_physics_review.json) · [前次结果](../nested_material_support_001/RESULTS.md) · [既存实际变形](../nested_material_trace_001/run_001/actual_material_trace.png)

批准后在真实仓库根使用独立HF环境一次启动：

```text
python -X utf8 -B lf_data_preparation/native_interface_001/nested_material_volume_001/launch_volume.py volume --protocol lf_data_preparation/native_interface_001/nested_material_volume_001/protocol.json
```

</details>

</details>
