# 当前接续：M-LEDGER1 来源已冻结，待新授权（2026-10-10）

整体目标是独立 HF 有限变形／TMC 前向评估：读取普通几何，得到可核对的反力、工件载荷及实际变形，供外部研究比较。开发继续在 main，origin 为 https://github.com/dudaxing/Compliant-TO-TMC.git。前次 M-LINK1 已实际发布并增量恢复到 `909d7ba6a4bd3ba6bd11b97af830f4aeeef203c7`；细网格完整24态、48次保存态独立参考及原图件保持。原生产资格没有改写。

最近的功能步骤是整理已有 nodes.csv，回答工件载荷来自底边、左右边、角点还是对称切面，以及 total／material／Hu 的有符号分量。新增122行 stdlib 读取函数和151行薄调用脚本，先处理原态0、8、13、23（初始、加载0.95 mm既有最大Hu记录、峰值1.2 mm、卸载0）；完整24态仅用于旧身份登记。七类互斥，角点／交点向量独立保留，原六力文本、厚度已包含的N单位及微小卸载量保持。直接整体 fsum 对账，七类回并沿原8·eps·节点L1舍入合同，无绝对误差地板。

候选源码、输入合同、正式卡／协议已作独立静审；本阶段尚未获执行授权，未调用新读取函数、解析CSV行分类求和、生成图或创建run。预计三张新图为固定工件参考节点分区图（无力箭头）、峰值七类分量柱形图、四个缓存态的分区变化图；四态连线只作阅读引导。源码静审不等于实际功能通过。当前效果是最近工作已可审阅和恢复，新的数值／视觉效果要等唯一执行后报告。

[正式执行卡](../nested_ledger_001/M-LEDGER1_CARD.md) · [冻结协议](../nested_ledger_001/protocol.json) · [来源记录](../nested_ledger_001/author/source_preparation.json) · [独立正式静审](../nested_ledger_001/author/final_static_review.json) · [上一阶段实际结果](RESULTS.md)

下一步仅申请 M-LEDGER1 一次 helper180秒／outer240秒、采样RSS8GiB，首错停止，无重试、修复重跑、延期或force。已关闭的M-LINK1不覆盖新分类／渲染。按这四态实际结果再决定全24态账本及外邻材料P诊断；本卡不实现压力、总边界力重建或有效夹持。全列切线、网格／域收敛、自由体／摩擦、正式标签／排名及HF5整体仍未完成。

<details>
<summary>本次更新前完整原文（历史状态不代表当前）</summary>

# 当前接续：M-LINK1关联入口已通过（2026-10-09）

整体目标仍是独立HF有限变形／TMC前向评估，提供可核对的反力、工件受力、加载／卸载变形及可恢复开发资料。用户明确批准后的唯一M-LINK1实际执行PASS闭卡：保存摘要1／1、response写1、索引写1，35绑定保持；helper 0.2004934000 s／outer 0.3920396001 s，采样自身 RSS 26537984 B／tree RSS 30978048 B，exit0／无stop。helper资源是收据构造／写入前快照，outer为完整launcher终态。独立终态审阅PASS；新增科学F/T/HP/求解/模型/渲染为0（固定调用路径依据、无动态hooks），新增保存摘要API为1。

同一细网格24态与已有48HP参考、原3PNG＋GIF及原phase第四PNG／四表已关联到新增response与仓库相对路径轻索引。原生产response及false flags、raw view／phase和原图件保持历史字节。峰值R=0.3787064524N、q_out=1.016699361mm、下半工件Fy=0.1231794016N；卸载R=-2.746498125e-26N。原生产F443／T201等记录是历史，不是本次API运行成本。

最近仅准备已有nodes.csv的stdlib CSV／JSON互斥载荷账本：保留total/material/Hu Fx/Fy原六列，将physical_only细分bottom/left/right侧内点与physical_corner，另保留physical_and_cut交点、cut内点、body内部；每节点一次，角点／交点向量不分摊。先观察缓存选定态，再按实际结果推进all24分类曲线；本轮未分组／求和新账本或执行未来卡。外邻medium材料P trace诊断留待账本结果之后，不纳最近阶段。材料P·N不能当Hu总压力；含材料＋Hu、物理表面／对称切面／角点的总边界力仍需单独定义。压力／有效夹持、网格／域收敛、全列切线及HF5仍未完成。

[目标／实现／物理数值／原图与边界](RESULTS.md) · [新增关联response](run_001/linked_response.json) · [轻交付索引](run_001/delivery_index.json) · [下一物理功能只读规划](author/physical_next_scope.json) · [原24态×1变形GIF](../../../functional_views/native_nested_cycle_20261009/complete_001/run_001/view/fixed_square/actual_states.gif)

<details>
<summary>本次更新前完整原文（历史状态不代表当前）</summary>

# M-LINK1 来源已准备，未授权／未执行

[执行卡](M-LINK1_CARD.md) · [协议](protocol.json) · [薄层来源](execute_nested_link.py) · [准备收据与保留的修正依据](author/source_preparation.json)

基线 main `d092532d2789b70d440edc29688b6351efce7f34` 的 M-REF2 已完成实际推送及恢复验收。此阶段准备最近的功能步骤：复用已有保存摘要 API，把同一细网格完整 24 态结果、48／48 HP 参考与已有 M-VIEW1 图件关联到新增 `linked_response.json` 和轻量 `delivery_index.json`。索引用仓库相对路径引用原 4 PNG、24 帧 GIF 与四份表；第四 PNG 经原 phase 关联。

准备期间没有执行 API、读取 NPZ／大型 HP 档案、求解或渲染，也未创建 run 输出。原生产 response、producer false flags、view／phase 和已有资格保持历史字节。已修正的外部 109 行 worker 仅替换来源说明后提升；三份预审及两次 checkpoint 修正快照保留在 `author/`，通用 launcher 字节不变。

下一步是正式来源独立静审、发布及恢复，然后请求 M-LINK1 一次 180／240 秒、采样 8 GiB 的执行授权。本阶段尚未授权或执行；关联不增加压力、有效夹持、网格／域收敛、全列切线或 HF5 资格。之后才准备材料＋Hu 在物理表面、对称切面与角点上的总表面力定义。


</details>

</details>
