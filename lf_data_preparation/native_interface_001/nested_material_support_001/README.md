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
