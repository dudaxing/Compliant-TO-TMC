# 工件功能进度草稿（2026-10-04）

当前已完成“普通原生几何 → 明确材料/支承/工件任务 → 有限变形三分量内力 → 切线组装与平均位移平衡 → 完整加载—卸载 → 保存状态、独立参考及实际显示”的一条粗网格固定方体功能链。整体独立 HF 项目尚未完成。本稿仅读已闭合 pose002 存档与源码，不产生新求解、力、切线、HP 或几何测量；soft001 的实际结果留待终态填写。

## 整体目标与研究层的位置

总体目标是让 HF 在不导入 LF 优化器的情况下，仅凭自包含几何和明确任务，独立评估真实反向器/夹持器的非线性响应，并给出有单位、方向和适用范围的结果，最终支持既有研究层的同任务候选比较。目标定义见 [PROJECT_STATUS.md:7](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/docs/PROJECT_STATUS.md:7>)。

LF/N4 来源层已有优化、多样化几何、评分、筛选与导出流程，本仓库保存了来源审计、参考材料和取舍记录；不能把这些说成尚未编写，也不能把来源测试当成本轮重新验收。尚缺的是当前独立 HF 后端与该研究流程的同任务评价、共同有效域、敏感性与批量标签闭环，而不是在 HF 内重做 LF 优化器。见 [LF 来源审计](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/research_integration_20260920/LF10_SOURCE_AUDIT.md:90>)、[研究层复用与标签边界](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/research_integration_20260920/external_reviews_20260921/inputs/comparison_review.md:122>)及 [HF5 条件](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/research_integration_20260920/INTEGRATION_DECISIONS.md:60>)。

## 已实现的实际功能

| 功能 | 当前实现与物理含义 | 关键代码 |
|---|---|---|
| 原生输入与任务 | LF v2 四掩膜、网格与区域来源保留，不隐含重采样；按显式 native 网格建立 Q1 模型，实体附着支承与任务背景约束分别记录 | [lf_v2.py:54](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/hf_repo/src/hf_eval/lf_v2.py:54>)、[native_map.py:59](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/hf_repo/src/hf_eval/native_map.py:59>)、[native_project.py:189](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/hf_repo/src/hf_eval/native_project.py:189>) |
| 实体与第三介质有限变形 | 二维平面应变可压缩 Neo-Hookean、3×3 Lobatto Q1；保存 F、J、Hu 与材料/正则/总内力。HuHu 加在弱式残量，其变形倍率不是替代总能量的 Hessian | [tmc_kernel.py:1](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/hf_repo/src/hf_eval/tmc_kernel.py:1>)、[split_kernel_invariants_hu.py:128](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/hf_repo/src/hf_eval/split_kernel_invariants_hu.py:128>) |
| 平均端口控制与切线 | 只约束输入端口加权均值，各节点保留不同实际位移；输出自由测量。独立 NumPy 三切线保留非对称性，组装全 DOF CSC，KKT 用一般稀疏 LU | [split_displacement.py:163](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/hf_repo/src/hf_eval/split_displacement.py:163>)、[split_displacement.py:206](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/hf_repo/src/hf_eval/split_displacement.py:206>)、[split_numpy_tangent.py:168](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/hf_repo/src/hf_eval/split_numpy_tangent.py:168>) |
| 连续加载—卸载 | ordered_cycle 保持状态、反力与切线连续；有符号预测、Armijo、失败回滚和二分。起点零与返回零按实际 index/leg 分别保存，不去重 | [split_displacement.py:220](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/hf_repo/src/hf_eval/split_displacement.py:220>)、[split_displacement.py:287](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/hf_repo/src/hf_eval/split_displacement.py:287>) |
| 固定工件与三分量测力 | 方/圆原生单元约束覆盖入口已有；本次方体所有节点 ux/uy 固定。工件 on-body 力为负的保存全局内力，holding 为反向约束反力，材料/Hu/总量分别保留 | [native_project.py:95](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/hf_repo/src/hf_eval/native_project.py:95>)、[native_project.py:142](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/hf_repo/src/hf_eval/native_project.py:142>)、[native_mean.py:66](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/hf_repo/src/hf_eval/native_mean.py:66>) |
| 缓存、节点力与显示 | 每接受态缓存原始 lift/fluctuation、16 机械字段、三局部切线和 full CSC；保存不追加力学调用。全部工件节点、四互斥组、带基准点的普通力矩可观察。已有真实 ×1 结构/GIF、明确 ×4 辅助、三力、J/Hu 与数值曲线 | [native_mean.py:175](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/hf_repo/src/hf_eval/native_mean.py:175>)、[workpiece_nodal.py:13](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/hf_repo/src/hf_eval/workpiece_nodal.py:13>)、[实际路径动画](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/functional_views/native_workpiece_cycle010_20261004/saved_render_001/animation_001/cycle010_actual_path.gif>) |
| 保存几何诊断 | 原生凸 Q1 跨区域 AABB/SAT 内部重叠、有限底/左面法向射线和最近点；物理射线排除对称切口，节点窗口代理与边界量分开 | [native_region_geometry.py:45](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/hf_repo/src/hf_eval/native_region_geometry.py:45>)、[native_region_geometry.py:206](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/hf_repo/src/hf_eval/native_region_geometry.py:206>) |

可选 chunk256 只降低切线临时数组成本，保留全域算术分支与全部三切线；默认 full 未改。当前 near-identity 方向尺度修复已有独立捕获态验证，不能因此声称任意输入或全部接触任务已完成。[native_mean.py:113](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/hf_repo/src/hf_eval/native_mean.py:113>)、[split_numpy_tangent.py:107](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/hf_repo/src/hf_eval/split_numpy_tangent.py:107>)。

## 最新已闭合 x71 方体结果

pose002 固定方体中心 (71,40) mm、边长 16 mm；实体 E=1 MPa、ν=.3，第三介质 γ=α=10⁻⁶、物理正则长度 80 mm。原 11 目标为 `0,.5,1,1.5,1.75,1.8,1.75,1.5,1,.5,0` mm。控制器二分后实际保存 17 态，完整回零；6 次预测态 invalid_J 拒绝按原规则回滚，并非把拒绝态算作通过。

| 已保存事实 | 数值 / 范围 |
|---|---|
| 生产 | 137 次 F 开始 / 131 完成，74 / 74 T，1 solve；helper 1413.3505 s、outer 1414.6824 s，原新卡 1500 / 1560 s、8 GiB |
| 独立参考 | 17 态全部 34 次新 HP80/120；328767 项检查通过；helper 618.8915 s、outer 620.5328 s，900 / 960 s、8 GiB |
| 1.8 mm 峰态 | 输入反力 R=.4381971939 N，自由 +y 输出 q_out=2.0153371129 mm；min J=.0008316610691，max |Hu 分量|=.3543912467 mm⁻¹ |
| 下半工件总力 | (Fx,Fy)=(-.002694482582,+.02692403501) N；材料 (-.002283786818,+.02589424148) N；Hu (-.000410695764,+.001029793529) N |
| 返回零 | R≈1.9401×10⁻²⁹ N，q_out≈-3.1995×10⁻²⁹ mm，保存 minJ=1；初零与返零是不同状态记录 |

生产依据：[result.json](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/lf_data_preparation/native_workpiece_001/shift_square_pose_002/run_001/result/result.json>)、[生产回执](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/lf_data_preparation/native_workpiece_001/shift_square_pose_002/run_001/execution_receipt.json>)。资格依据：[独立 summary](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/lf_data_preparation/native_workpiece_001/shift_square_pose_002/reference/summary.json>)及 [lifecycle](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/lf_data_preparation/native_workpiece_001/shift_square_pose_002/reference/lifecycle.json>)。资格仅覆盖这些实际接受态的三力、声明 PORT 方向作用、完整组装、平均约束/平衡和有符号工件投影；不是切线全列、拒绝态或一般接触资格。生产原 HP/equilibrium/HF flags 仍为 false，独立参考另外记录。

半模型的镜像合力是 (2Fx,0)；2|Fy|=.05384807002 N 只是双侧法向分量模之和，不能称净力、压力或已证实夹持力。工件固定约束承担外部 holding；该结果没有证明自由工件会静止、稳定或被夹持。

## 为什么先分位置、再软化

将中心 x70→x71 改的是工件位置与约束覆盖，未修改原机制材料或设计。已保存的同 identity x71 峰态几何观察表明，最右钳尖节点 2510 为 (79.16727043,32.00927435) mm，仍在方体右面 x=79 外约 .16727043 mm。底面首次射线 .00580924818 mm 来自边 2509–2510 的内部点至 (79,32) 角点，不是钳尖间隙，不能据此写“钳尖接触”。该观察最初由 pose001 partial 峰态保存，峰态 state SHA 与 pose002 一致；本稿没有重测几何或扩大其资格。见 [钳尖与射线来源说明](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/docs/evidence/workpiece_shift_20261004/physics_tip_alignment_note.json>)。

soft001 保持同位置、网格、工件、端口和原完整路径，仅将实体 E=1→.5 MPa，并将 γ、α 同时 10⁻⁶→2×10⁻⁶。因此实体 Lamé 系数减半，但**第三介质绝对 Lamé 系数与全域 kr 保持原值**；几何/支承/端口不动，E×厚度力标度 20→10，原 floor 公式不变。[native_project.py:245](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/hf_repo/src/hf_eval/native_project.py:245>)。这分离了位置变化与实体相对软化的影响。平均输入位移已被控制，降低 E 并不自动保证钳尖多移动或夹持增强；介质/正则相对实体的阻力反而提高，需要实际求解后判断。

soft001 当前只有唯一新生产运行，显式预算 1800 / 1860 s、8 GiB；它不是对已关闭 pose001/pose002 延时或重试。

**[待填 soft001 实际终态]**：实际接受 N / 原目标覆盖、F/T 计数与成本、峰/返回、钳尖三面距离和射线 witness、实体/介质 J/Hu、三分量节点/合力，以及另行 fresh 全 N×2 HP 资格。当前不填成功、接触或性能改善结论。

## 还缺什么，已有代码到哪一步

- **研究层耦合和批量 HF 评价**：已有 LF/N4 生成/评分与来源资料；当前 HF 原生适配和单任务机械链已接通。同任务后端接入、共同分析政策 H2/任务定义 H3、候选比较和 HF5 统计仍未完成，不重新宣称上游优化从零缺失。
- **真实自由刚体及接触功能**：当前工件固定全部 ux/uy，没有自由刚体平移/旋转未知量及力矩平衡，也没有摩擦/滑移定律或已验证一般进入—释放—重入/角点接触。仓库有受限无摩擦法向/闭合接触基准代码（[contact_reference_a0.py:1](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/hf_repo/src/hf_eval/contact_reference_a0.py:1>)、[normal_contact.py:58](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/hf_repo/src/hf_eval/normal_contact.py:58>)），不能把其范围外推为本 x71 工况的一般接触能力。
- **压力、应力和能量**：P/S 字段及旧完整能量入口存在；当前机械模式明确省略材料能量，`not_evaluated/qualified:false`，不以它阻塞机械残量。此次工件路径没有压力、应力 HP、辅助能量或材料安全资格；Hu 弱式项不能直接当一个已验证总能量。[native_mean.py:133](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/hf_repo/src/hf_eval/native_mean.py:133>)、[split_kernel_invariants_hu.py:182](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/hf_repo/src/hf_eval/split_kernel_invariants_hu.py:182>)。普通节点力矩是保存数组诊断，本轮没有新增其 HP 资格。
- **几何与网格范围**：方体完整原生区域和有限两面诊断已实现，尚不测试完整集合包含、机构自重叠或 signed penetration。圆形固定单元覆盖可构造，但圆形完整物理边界/相应平衡没有本次资格；仍是 native 阶梯边界。原细 LF 夹持器的无工件 .025 mm 四态路径已成功，8 HP/307565 检查通过（[细例 summary](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/lf_data_preparation/native_fine_task_025_001/audit/summary.json>)）；细网格工件近接触循环及匹配设计的网格/参数收敛仍待完成，另一细设计不能称同机构网格收敛。

下一步首先依据 soft001 的真实终态选择：若完整路径及全接受态新参考通过，比较同几何任务下钳尖位置、有限面 witness、三分量力、J/Hu、回零与成本，再选择是否调整位置/介质参数或进入自由工件/圆形任务；若失败，先根据保存状态定位实际阻断。当前数据不支持盲目加行程或承诺夹持成立。
