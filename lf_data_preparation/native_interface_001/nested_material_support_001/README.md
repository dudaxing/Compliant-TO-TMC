# 当前接续：M-VOLUME1九点材料体积诊断已通过（2026-10-11）

整体目标仍是读取普通 LF 几何的独立 HF 有限变形／TMC 前向评估，提供可解释的反力、工件载荷和实际变形；HF不优化、不调用dmftd，main开发，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git。

M-VOLUME1已在直接人类批准后唯一实际PASS并闭卡：原loading6／0.85mm、13／1.20mm的10406／10407两个单元，3个既存NPZ／9字段、2次公共入口，36九点采样／12深度／4单元对照行及两PNG。31冻结绑定保持，outer2.5381053000019165秒／tree RSS132591616 B；helper2.2876966999901924秒／own RSS128356352 B是成功收据构造前快照。exit0、stopnull、一次启动，无重试／修复重跑／延期／force；本卡窗口结束。独立终态核对通过，主任务实际查看两张原2100×2400像素，物理解读已归档。

四case的Fy保存W−九点观察V全为保存0；Fx只在6/10406和13/10407出现−1.6940658945086007e−21／+2.710505431213761e−20 N。峰值10406与10407的W=V Fy分别+.037219775006120934／+.08022435531475952 N，旧上缘T分别+.004917548552353244／+.01938390857410906 N。W−T差分别+.03230222645376769／+.060840446740650464 N，V并未消去体积／上缘差；现有局部证据不支持立即重开DD核追究舍入分离。

0.85mm中层Q较大，1.20mm下层Q较大。三个Q是同批九项的可加体积贡献；Qtop不是整上缘T。唯一新增8eps×同九项L1重组门四case均通过，无地板；跨表达差只描述，原保存DD力、旧迹和原门保持。两图各panel独立尺度，只能按标签／CSV跨panel比较绝对量；图为参考采样及材料贡献，实际结构变形仍见原图／24帧GIF。protocol及card的False是准备历史，实际授权和终态另有独立记录。

下一功能选择先核当前公共API已有total/material/Hu工件载荷、半模及镜像报告合同，避免重做已有功能；再根据本次局部体积／上缘证据推进尚缺的总作用量物理解释和可用输出。这里仅记粗路线，不拟定或授权新数值卡。不扩展同类全24态账本，不把P@N加一个Hu数认定为总压力。总Hu边界作用／压力、有效夹持、自由体／摩擦、网格收敛、正式标签排名与HF5仍未完成；本卡不增加力核／切线／HP／平衡路径或压力／夹持资格。

[新九点实际结果](../nested_material_volume_001/RESULTS.md) · [九点P图](../nested_material_volume_001/run_001/nine_point_material_P.png) · [分层贡献图](../nested_material_volume_001/run_001/material_depth_volume_comparison.png) · [本阶段原实际结果](RESULTS.md) · [原实际变形](../nested_material_trace_001/run_001/actual_material_trace.png)

<details>
<summary>更新前完整原文（历史状态不代表当前）</summary>

# 当前接续：M-VOLUME1 九点材料体积候选待批准（2026-10-11）

整体目标仍是独立 HF 有限变形／TMC 前向评估，读取普通 LF 几何，为外部研究提供反力、工件载荷和实际变形。HF不优化、不调用dmftd；main开发，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git。

M-SUPPORT1已唯一实际PASS闭卡并发布／恢复于main1671e2d。峰值bottom-owner弱Fy与旧bottom线差+0.09415598535141824 N，大差主要来自同一owner的体积与面迹表达；corner_only不能解释该量级。最近新候选M-VOLUME1聚焦原6/0.85mm和13/1.20mm的10406／10407两个单元。

新入口读取3个既存NPZ／9字段，对九点保存P／原grad和含厚度weights做材料体积重构，并按η三层显示；保留原DD收缩后的保存元素力及旧上缘迹。保存P已舍入，重构不是原DD重播；两者差单独报告，不设相等门。只对同一批九点观察项的行重组使用8eps·L1无地板新代数门，原门保持。

当前仅编码、AST、普通元数据和字节静审；尚未导入候选、解码NPZ、积分／fsum或绘图。新卡拟一次helper180秒／outer240秒／采样8GiB、首错停止、无重试／修复重跑／延期／force，待人类批准。预期36九点行／12深度行／4单元对照行及两PNG；新图显示参考单元采样和有符号材料贡献，实际变形复用原图。未证明差值连续物理原因。

总Hu边界作用／压力、有效夹持、自由体／摩擦、网格收敛及正式HF5标签排名仍未完成。最近只执行该小范围观察，按实际结果再决定原收缩核查或Hu边界功能，不预先扩展全24态或新平衡路径。

[具体卡](../nested_material_volume_001/M-VOLUME1_CARD.md) · [说明](../nested_material_volume_001/README.md) · [冻结协议](../nested_material_volume_001/protocol.json)

<details>
<summary>更新前完整原文（历史状态不代表当前）</summary>

# 当前接续：M-SUPPORT1两态材料支撑诊断已通过（2026-10-11）

整体目标仍是读取普通 LF 几何的独立 HF 有限变形／TMC 前向评估，输出可解释的反力、工件载荷与实际变形；HF不优化、不调用dmftd，继续main，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git。

人类明确批准后，M-SUPPORT1唯一实际运行PASS并闭卡：3个既存NPZ／8字段，2个入口／2次原C-order材料global组装精确数值重播，5476局部出现／1444单元／1406节点／10组／2整体行及两PNG。36原绑定保持，outer2.116422799997963秒／tree RSS129019904 B；helper1.9246779000095557秒／own RSS113950720 B为成功收据构造前快照。exit0、stopnull，无重试／修复重跑／延期／force。独立终态审阅通过，两图实际像素已看；物理报告是解释，不是新增科学验收门。

原6/loading0.85mm与13/loading1.20mm的底边owner材料弱Fy为+0.0033910508870495064／+0.12182859983276352 N，对应旧底边材料line为+0.0029375878559500844／+0.02767261448134528 N；support−side-line为+0.00045346303109942195／+0.09415598535141824 N。峰值corner_only合Fy仅+0.00009348741040979886 N，body组保存贡献为0；大差主要定位于同一底边owner的体积弱式与面迹表达，不能归因两个对角支撑单元或用Hu补平材料差。右角节点10638材料Fy+.06463699536344664 N主要来自底边owner10407的局部TR项，不能当右面压力。

原global精确重播与节点身份／材料向量对账通过；整体新局部重组在0.85mm的Fy误差4.336808689942018e−19 N，小于6.236745013039355e−18 N局部L1界，峰值误差为0。原M1/M2节点L1门保留。protocol的False字段是冻结准备历史；当前批准、一次实际终态和结果另有记录。新图是参考支撑位置／有符号材料贡献，原实际变形与24帧GIF继续用于对照。共同尺度会隐藏很小的条／色差，应看CSV精确值。

最近下一步聚焦峰值底边末端10406／10407等单元的九点保存材料P／原体积弱收缩与上缘迹局部对照，解释已定位差值的离散来源；这只是依据实际结果的粗路线，未新增卡或授权新读取／计算。总Hu边界作用／压力、有效夹持、自由体／摩擦、网格收敛、正式标签排名与HF5仍未完成。本卡不产生新力核／切线／HP／平衡路径资格。

[本次完整结果](RESULTS.md) · [支撑位置图](run_001/reference_support_map.png) · [有符号贡献图](run_001/material_support_comparison.png) · [精确分组表](run_001/groups.csv) · [当前批准](author/authorization.json) · [终态审阅](author/terminal_execution_review.json) · [物理解读](author/physical_results_review.json) · [原实际变形](../nested_material_trace_001/run_001/actual_material_trace.png)

<details>
<summary>更新前完整原文（历史状态不代表当前）</summary>

# M-SUPPORT1 两态保存材料支撑候选：待批准（2026-10-11）

整体目标仍是读取普通 LF 几何，在独立 HF 有限变形／TMC 前向任务下给出可解释的反力、工件载荷和实际变形。HF不优化、不调用dmftd；main开发，origin保持 https://github.com/dudaxing/Compliant-TO-TMC.git。

M-PTRACE1 已唯一实际通过并闭卡，结果发布／恢复于 main 96bfea73。峰值1.20mm材料线Fy为+0.027662985836060965 N，原材料弱Fy为+0.12191255705872141 N，差−0.09424957122266045 N。该差需要追溯完整Q1节点支撑，不能按舍入噪声或Hu补平解释。

最近新候选 M-SUPPORT1 已编码，仅读同loading0.85／1.20mm的3个既存NPZ／8字段，重播2次原材料C-order组装并按body／bottom-owner／left-owner／right-owner／corner-only五类追溯局部节点贡献。每态预期722支撑单元／2738局部出现／703节点。两个仅角点相连的对角单元可能有弱式贡献，其phase未读取。N力已含厚度；支撑类别不是面压力。新局部L1舍入规则与原M1/M2节点L1门分开，旧门保持。

目前仅源码／AST、普通JSON/CSV与原字节核查：候选未导入、NPZ未解码、组装／投影／新fsum／图均未运行，尚无实际支撑贡献值或差值原因结论。拟一次helper180秒／outer240秒／采样8GiB，首错停止、无重试／修复重跑／延期／force；两PNG显示参考支撑位置与有符号材料贡献，实际变形复用原图链接。本卡待人类批准，不能续用已闭M-PTRACE1窗口。

总Hu边界作用／压力、有效夹持、自由体／摩擦、网格收敛、正式标签排名与HF5仍未完成。批准后仅运行这两个保存态，根据实际支撑结果再规划最近一步。

[具体卡](M-SUPPORT1_CARD.md) · [冻结协议](protocol.json) · [公共入口](../../../hf_repo/src/hf_eval/saved_material_support.py) · [薄执行器](execute_saved_material_support.py) · [输入核查](author/support_input_scope.json) · [物理依据](author/support_physical_basis.json) · [独立物理静审](author/support_static_physics_review.json) · [前次实际发布恢复](author/MPTRACE1_publication_receipt.json) · [前次实际结果](../nested_material_trace_001/RESULTS.md) · [既存实际变形](../nested_material_trace_001/run_001/actual_material_trace.png)

批准后从真实仓库根一次启动（使用本项目独立HF环境）：

```text
python -X utf8 -B lf_data_preparation/native_interface_001/nested_material_support_001/launch_support.py support --protocol lf_data_preparation/native_interface_001/nested_material_support_001/protocol.json
```

</details>

</details>

</details>
