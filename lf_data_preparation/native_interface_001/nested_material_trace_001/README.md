# 当前接续：M-PTRACE1 两态材料牵引与实际变形已通过（2026-10-11）

整体目标仍是读取普通 LF 几何的独立 HF 有限变形／TMC 前向评估，为外部研究提供可解释的反力、工件载荷和真实变形；HF不优化、不调用dmftd，继续main，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git。

人类明确批准后，M-PTRACE1唯一运行实际PASS并闭卡：5个既存NPZ／12字段、2次材料迹入口、432样本／144边／6侧／2整体表和两PNG。31原字节绑定保持，outer2.2380354999913834秒／tree RSS118493184 B；helper1.9568402000004426秒／own RSS114257920 B为成功收据构造前快照。exit0、stopnull，无重试／修复重跑／延期／force。独立终态审阅通过，物理结果已独立解读，两张实际图已读取像素查看。

两态各72物理外邻owner均为原third_medium；材料压缩主要在底边右端。0.85／1.20mm的最大名义压缩为0.00016737104079557997／0.0039494633933005825 MPa。整体材料线Fy为0.0029293605006823825／0.027662985836060965 N，原材料弱Fy为0.0034790753630243565／0.12191255705872141 N；保存差为−0.0005497148623419741／−0.09424957122266045 N，不强制相等，不按差判solver失效。

原protocol的False字段是冻结准备历史；当前批准与一次实际终态另有收据。P·N是材料名义牵引，线权独立乘原20mm厚度一次，不是包含Hu的总压力或合格夹持力。固定工件、原平衡／HP／旧图／科学版本保持，未新增力核、切线、HP或平衡路径。

最近下一步优先解释峰值材料weak与面trace差别，核对局部Q1支撑／体积积分关系；根据新证据再推进Hu总边界作用及夹持功能，不预先扩全路径。总压力、有效夹持、自由体／摩擦、网格收敛、正式标签排名与HF5仍未完成。下一张执行卡尚未批准／执行。

[本次结果](RESULTS.md) · [实际变形与材料迹](run_001/actual_material_trace.png) · [三侧材料牵引](run_001/nominal_material_profiles.png) · [完整数值](run_001/whole_material_comparison.csv) · [公共入口](../../../hf_repo/src/hf_eval/saved_material_trace.py) · [冻结卡](M-PTRACE1_CARD.md) · [当前批准](author/authorization.json) · [终态审阅](author/terminal_execution_review.json) · [物理结果审阅](author/physical_results_review.json)

<details>
<summary>更新前完整原文（历史状态不代表当前）</summary>

# 当前接续：M-PTRACE1 两态保存外邻材料应力候选已准备，待批准（2026-10-11）

整体目标仍是独立 HF 有限变形／TMC 前向评估，读取普通 LF 几何并提供可审查的反力、工件载荷和实际变形，供外部研究比较；main 开发，origin 保持 https://github.com/dudaxing/Compliant-TO-TMC.git。

上一 M-LEDGER2 已唯一执行 PASS、推送 main 808e719 并完成同提交恢复核对，24 态完整账本／两图和原 24 帧变形均保留。局部 Hu 力抵消较强的原6／loading0.85 mm与材料净载主导的原13／loading1.2 mm，为最近新阶段提供实际依据。

新公共 NumPy 入口已编码但未执行：追踪72条物理边的真实外邻 owner／相位，直接取保存 P 的边界三点，给有符号材料名义牵引与独立厚度线积分，和原整体材料弱力并列；不设相等科学门。候选薄执行器将读取5个既存NPZ的12字段，调用2次入口，生成432样本／144边／6侧／2整体表与2PNG实际变形／载荷图。N力已含厚度，P为MPa且未含厚度，线积分单乘原20mm；不复用体积分权重、不分摊角点弱力、不把P当Hu总压力。

目前只有源码／AST／metadata与原文件字节审阅；未解码NPZ、取P数值、计算PN／线积分或绘图，资源窗口未开启。本卡一次helper180秒／outer240秒／采样8GiB、首错停止、无重试／修复重跑／延期／force，须人类批准后启动，不能续用已闭M2额度。

原力核／切线／求解、HP、旧图与科学版本保持。总边界作用／压力、有效夹持、自由体／摩擦、收敛、正式标签排名与HF5仍未完成。下一步只运行这两个保存态，根据实际外邻迹与弱力关系继续推进功能。

[本次具体卡](M-PTRACE1_CARD.md) · [冻结协议](protocol.json) · [公共读取与材料迹源码](../../../hf_repo/src/hf_eval/saved_material_trace.py) · [薄执行器](execute_saved_material_trace.py) · [静态输入核查](author/trace_input_scope.json) · [静态物理依据](author/trace_physical_basis.json) · [独立源码物理审阅](author/trace_static_physics_review.json) · [上一M2实际结果](../nested_ledger_002/RESULTS.md) · [上一提交实际发布恢复收据](author/MLEDGER2_publication_receipt.json)

批准后从仓库根唯一启动：

```text
python -X utf8 -B lf_data_preparation/native_interface_001/nested_material_trace_001/launch_trace.py trace --protocol lf_data_preparation/native_interface_001/nested_material_trace_001/protocol.json
```

</details>
