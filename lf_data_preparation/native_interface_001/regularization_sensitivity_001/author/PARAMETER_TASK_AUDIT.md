# 参数探索与当前固定半方体任务的可比性审计

2026-10-11，main `5af8b5e`。本次只读普通 task／model JSON、原文档与源码；没有读取 NPZ 字段、导入 HF、调用 API／fsum、构模、求解或绘图，也没有新增科学门。详细源路径与真实 SHA 见 `parameter_task_audit.json`。

当前基线为 `lf_data_preparation/native_interface_001/nested_cycle_001/task.json` 和 `run_001/fixed_square/model/model.json`：84×40mm、h0.5、固定 side18 方体 center(71,40)，E1MPa、ν0.3、厚20mm、γ=α=1e-6、Lr80mm、原24目标0→1.2→0mm。背景 uy 对称线延至x84；LF设计原子域保持，细网格为同设计嵌套派生。

## 先区分三个参数

`native_project.py:244–253` 中，γ只通过 `where(solid,1,gamma)` 缩放原第三介质 λ、μ，不改变实体E或kr。α控制 `kr=αLr²(κs+4μs/3)`，kr基于实体参数，`kr_material_factor_applied=false`。Lr是物理正则长度，不是单元h，也不随分析域80→84自动改为84；当前模型实际仍为80mm。

`split_kernel_invariants_hu.py:176–180` 保留原 Hu 弱式：kr×Σw exp(-5J)×hessian_action(Hu)。改γ或α后重新平衡会改变材料与Hu响应，不能线性缩放原保存工件力。α／Lr不应同时改，γ也不应和α同时改以获得净力吻合。本审计不改变原Hu核，不构造替代能量门或压力。

## 哪些旧实验能够控制对照

| 原实验与具体来源 | 自身是否控制对照 | 与当前任务的关系 |
| --- | --- | --- |
| `enlarged_square_projection_001/run_001/result/model` 对 `gamma_half_cycle_001/run_001/result/model`；`gamma_half_preparation_001/run_001/preparation_receipt.json` | 真γ单因素：1e-6→5e-7；h1、80×40、零右余量、side18、E/α/Lr/端口/BC/24目标相同。普通JSON一致，原准备记录27字段中仅gamma/lam/mu变，其余24字段不变 | 旧域和网格不同，背景线终点x80；不能当h0.5／84×40的γcontrol。可启发检查早期加载敏感性，不能借其结论声明当前γ稳定 |
| `shift_square_pose_002/run_001/result/model` 对 `shift_square_soft_001/run_001/result/model`；`docs/WORKPIECE_SHIFT_AND_SOFTNESS_20261004.md` | 是有意耦合的实体软化探索：E减半、γ／α同时加倍，保存绝对介质Lamé与kr相同；不是α或γ单因素 | 自身side16、h1、80×40、11原目标到1.8mm；工件、域、网格和路径均不同。不能用作当前α因果证据 |
| `right_margin_cycle_001` 与 `right_margin4_cycle_001`；`docs/WORKPIECE_ENLARGEMENT_20261007.md` | h1的域／外边界因素，E/γ/α/Lr/机构工件和24目标保留，背景线随新增域延长 | 原right4是当前细网格物理父任务；域差异不是γ／α效应，旧gamma_half与right4不能拼成参数control |
| `right_margin4_cycle_001` 与 `nested_cycle_001`；`functional_views/native_nested_cycle_20261009/complete_001/RESULTS.md` | 同物理任务嵌套h1／h0.5敏感性，参数未变 | 已有mesh敏感性，保留复用；不能称α验证或完整网格收敛 |
| `hf_repo/configs/hf4/validation_spec.json`；`contact_c1_v1.json`；`docs/HF4_C1_FINAL_REPORT.md` | 小合成块体的γ、mesh及A0／Aalpha／TMC诊断；Aalpha改变作用范围，不是独立α幅值 | 尺寸、E、Lr、厚度、工件／障碍、BC和目标不同，只作公式／实现启发，不转移夹持器稳定性或阈值 |

真正旧γ基准应使用已经完成的 `enlarged_square_projection_001`，而不是把此前contact阶段或旧side16的资格混借。原γ准备receipt提供的字节对账在本审计中只引用，没有重读NPZ。当前设计来源与旧设计存在明确派生链，但几何／网格身份本来不同，不能用“同设计”替代“同域同网格同BC”。

在所审 native 固定工件实验中，没有找到当前h0.5／84×40／side18的已完成α单因素或Lr单因素证据；这是有界来源审计，不能用旧软化记录填补。

## 最近参数因素：当前网格上单独改变α

建议保留当前h0.5、84×40域、实体掩膜、side18工件、E、γ、Lr80、原物理端口／支撑、路径与Hu实现，先检验正则强度。它比新增网格更直接地回答Hu幅值对有符号工件力、反力、变形和间隙的影响；新增h回答空间离散问题，两者不能相互替代或消除h–α交互。

root正考虑α=1e-6→5e-7、零起点原目标前缀。最初14目标只加载到1.2mm；最新接口审阅考虑保留原 `ordered_cycle` 的15目标前缀，即14加载目标及一次回撤到1.15mm，以复用原 solver 的leg／original_target_index记录和原viewer字节，并与基线相同15目标精确配对。最终14或15由接口审阅决定，不在本审计冻结。两点只给敏感性，不是稳定／收敛／压力资格；15目标也只增加局部回撤，仍没有完整卸载／回零证据，不能推广为全路径或分支稳定。重新平衡结果不可按α比例预测。原四项生产门可保持，不给参数输出一致性新增人为阈值。

如不新增HP，新α态只具自己的生产数值记录，原48HP仍只属于原保存态；不能借给新α结果。保留公共signed total／material／Hu、输入R／输出q、实际变形、有限钳尖间隙及明确minJ／Hu诊断即可，不重复旧账本或同类投影HP。正式总压力与有效夹持仍是独立缺口。

具体新值、加载范围与9000／9600／9660秒、8GiB预算只是root的待冻结候选；本审计没有授权、实施或形成执行卡。后续由真实候选、独立审阅和用户资源授权确定。
