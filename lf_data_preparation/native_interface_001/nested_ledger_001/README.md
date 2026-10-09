# 当前接续：M-LEDGER1 来源已冻结，待新授权（2026-10-10）

整体目标是独立 HF 有限变形／TMC 前向评估：读取普通几何，得到可核对的反力、工件载荷及实际变形，供外部研究比较。开发继续在 main，origin 为 https://github.com/dudaxing/Compliant-TO-TMC.git。前次 M-LINK1 已实际发布并增量恢复到 `909d7ba6a4bd3ba6bd11b97af830f4aeeef203c7`；细网格完整24态、48次保存态独立参考及原图件保持。原生产资格没有改写。

最近的功能步骤是整理已有 nodes.csv，回答工件载荷来自底边、左右边、角点还是对称切面，以及 total／material／Hu 的有符号分量。新增122行 stdlib 读取函数和151行薄调用脚本，先处理原态0、8、13、23（初始、加载0.95 mm既有最大Hu记录、峰值1.2 mm、卸载0）；完整24态仅用于旧身份登记。七类互斥，角点／交点向量独立保留，原六力文本、厚度已包含的N单位及微小卸载量保持。直接整体 fsum 对账，七类回并沿原8·eps·节点L1舍入合同，无绝对误差地板。

候选源码、输入合同、正式卡／协议已作独立静审；本阶段尚未获执行授权，未调用新读取函数、解析CSV行分类求和、生成图或创建run。预计三张新图为固定工件参考节点分区图（无力箭头）、峰值七类分量柱形图、四个缓存态的分区变化图；四态连线只作阅读引导。源码静审不等于实际功能通过。当前效果是最近工作已可审阅和恢复，新的数值／视觉效果要等唯一执行后报告。

[正式执行卡](M-LEDGER1_CARD.md) · [冻结协议](protocol.json) · [来源记录](author/source_preparation.json) · [独立正式静审](author/final_static_review.json) · [上一阶段实际结果](../nested_link_001/RESULTS.md)

下一步仅申请 M-LEDGER1 一次 helper180秒／outer240秒、采样RSS8GiB，首错停止，无重试、修复重跑、延期或force。已关闭的M-LINK1不覆盖新分类／渲染。按这四态实际结果再决定全24态账本及外邻材料P诊断；本卡不实现压力、总边界力重建或有效夹持。全列切线、网格／域收敛、自由体／摩擦、正式标签／排名及HF5整体仍未完成。

<details>
<summary>本次更新前完整原文（历史状态不代表当前）</summary>

# M-LEDGER1正式来源已准备，未授权／未执行

[执行卡](M-LEDGER1_CARD.md) · [协议](protocol.json) · [公共stdlib来源](../../../hf_repo/src/hf_eval/saved_workpiece_loads.py) · [薄调用器](execute_saved_ledger.py) · [来源收据](author/source_preparation.json)

main基线909d7ba的M-LINK1已经实际推送／恢复。最近的物理功能是从已有节点表组织载荷账本，保留材料＋Hu和共享角点；本阶段仅准备来源。原24态身份是登记输入，当前新输出限定0／8／13／23四态、每态703标准节点，不授予全24新账本或压力资格。公共模块可在将来接收全部记录，但本caller锁定四态。

拟新增两CSV、账本JSON、三Matplotlib诊断图与执行收据；位置图只有固定工件参考节点／类别，没有力箭头。原力字符串、符号与微小残量保留，直接whole fsum复现旧记录，七到四分区沿用无绝对地板的8eps·L1算术合同。本轮没有运行候选、分类／求和／绘图或任何NPZ／力核／HP／模型／求解。

公共模块与通用launcher原字节提升；151行caller只改首docstring和文件名，执行AST不变。原input scope、外部准备收据、预静审、worker／card／protocol草案和M-LINK1实际发布收据原字节归档。来源静审不是运行证据。下一步正式最终静审、发布恢复后请求一次180／240s、采样8GiB新卡授权；首错停止，无重试／延期／force。

外邻材料P诊断及材料＋Hu总边界力重建仍待账本实际结果之后决定。压力／有效夹持、网格／域收敛、全列切线及HF5尚未完成。旧结果／response／view／phase和资格均不改。

</details>
