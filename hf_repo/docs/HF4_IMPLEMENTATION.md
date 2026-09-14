# HF-4-A/B 实现与审查对照

本文记录 0.4.0 的合成均匀法向接触接口。阶段计划与实际结果分别见工作区 `docs/HF4_AB_EXECUTION_PLAN.md`、`docs/HF4_AB_REPORT.md`。此入口不解释真实圆柱或候选夹持性能；HF-1 数据与 HF-3 平均端口 API 保持其原任务语义。

## 数据和任务

`src/hf_eval/normal_contact.py:build_normal_contact(task)` 接受普通 JSON 字典。schema 为 `hf-normal-contact-task-1.0`，包含 units、geometry、material、gamma、regularization、mesh_size_mm、targets_mm 和 constraints。对象两块同材料实体，中间介质，固定顶端与驱动底端为边界装置。body_ids 为 0=介质、1=下块、2=上块。坐标为 x-fast、bottom-up；Q1 局部节点 BL/BR/TR/TL。

几何物理身份排除网格及 gamma；mesh_id 和 task_sha256 分别区分离散和完整任务。界面必须与网格精确对齐，不吸附或修复几何。接口间隙由参考弧长梯形权重计算：`g0 + b_gap^T u`，权重在每个网格上重新构造。独立审计从界面原坐标加实际位移重新计算，保留有符号结果。

用户可在安装的独立包中调用该构建器及下面的求解函数。当前统一 `evaluate(geometry_file,...)` 仍分派旧几何任务；合成基准用显式独立 API 和随包提供的开发运行脚本，不伪装成已有 HF-1 几何。

## 方程、符号与测力

`src/hf_eval/prescribed.py:solve_prescribed_path(model, base, direction, targets, *, reaction_groups, settings, force_scale_per_length, on_accept)` 施加 `u_D=base_D+d*direction_D`，无外加节点力；自由平衡 `fint_f=0`。base/direction 是全 DOF 向量，在 free 上必须为零。非零 base 要求首目标为零，以明确记录其平衡过程。

从已接受态作切线预测 `K_ff delta_u_f = -K_fD delta_u_D`；Newton 校正只改变 free DOF，使用实际非对称 Jacobian 和一般稀疏 LU。固定同一次回溯的残差尺度，Armijo 下降判断不通过重新放大尺度获得虚假改善。非法 J 拒绝而不裁剪，增量只在预定二分深度、最小增量和时间预算内继续。

reaction_groups 为 name→全 DOF 无量纲虚位移向量，仅在规定自由度上有非零项。`constraint_force` 是约束装置对模型的共轭力，`model_force` 为相反力。底部 +y 运动对应正压缩；顶部测量也取全局 +y，所以约束对模型为负。`virtual_work_generalized_force` 从逐单元残差与虚位移做收缩，再与全局归约反力核对；它是每单位规定运动的虚功，不是累计路径功。

测力向量允许重叠，因各组代表独立观察。全局合力只用去重后的固定 DOF 反力，不求和各组。材料与完整 HuHu 分量分别保存，不能从材料能量求导替代非保守完整残差。全合成模型不乘半模型倍率。

## 数值状态与原始证据

每个接受态保存 d、u、完整内力、材料/正则内力与逐单元分量、支反力、J、材料能量、测力、约束误差、SF、原目标身份、二分深度和检查次数。`failed_attempts` 保留失败原因及回滚相等检查；`trials` 保留所有回溯因子、尺度、merit、J 与接受/拒绝原因。未到目标时 `target_metrics=null`，最后接受态单列。

`scripts/run_hf4_normal.py` 负责普通文件交付。model.npz 保存实际数值原语，包括算子、材料、体标签、边界向量和间隙向量；metadata.json 保存任务、规范、源码哈希和参考输入。每个状态 NPZ 与 JSON 原子写盘后更新 steps/index.json。result.json 保存总体状态和路径历史。脚本不修改冻结阈值。

## 两种独立参考

`scripts/hf4_normal_reference.py` 只用标准库 Decimal 求解有限介质串联层与理想硬接触。输入是实际 binary64 实体/介质 Lamé 系数及尺寸，独立系数不会被反算成另一个 gamma。有限介质参考以正伸长域中的单调括区二分得到唯一压缩根，输出公式残差从导出的伸长比重算。它不导入生产内核、FE 装配器或求解器。

`scripts/hf4_precision_reference.py` 复用独立 Decimal Q1 材料/完整 HuHu 原语计算，并独立重建非零规定值、测力和 SF。它在实际保存的 D(u) 上验算，不将不满足约束的 u 替换为理想边界。可选 tangent_direction 与规定运动 direction 分开，支持非仿射 Jv 核验。

`scripts/hf4_input_audit.py` 从冻结 JSON 独立重建应有映射、材料公式和算子并检查存档；HP 随后仍使用实际存档值。该门防止生产模型和生产导出的参考输入同步出错。`scripts/audit_hf4_normal.py` 检查完整目标清单、逐态哈希、数组形状、输入映射、所有接受态 HP、有限模型参考及分相硬接触偏差。缓存只有在输入/脚本绑定与结果承诺哈希一致时复用。

## 必要检查与代码对照

| 需求 | 测试或证据入口 |
|---|---|
| 原始物理几何、界面、材料分区、约束、细化身份 | `tests/test_normal_contact.py` |
| 非零规定运动、自由预测、实际非对称矩阵、符号、虚功及失败回滚 | `tests/test_prescribed.py` |
| 独立闭式关系、单调参考、真实系数、量纲、50/80 自洽 | `tests/test_hf4_normal_reference.py`、`scripts/preflight_hf4_reference.py` |
| 精确边界乘积、实际保存态、反力去重、HP 尺度、非仿射 HuHu 导数 | `tests/test_hf4_precision.py` |
| 防止模型与参考同步错误、算子和配置错配 | `tests/test_hf4_input_audit.py` |
| 防止遗漏原目标、状态重排、伪终点与补步误标 | `tests/test_hf4_audit_inventory.py` |
| 新 wheel、异地 cwd、禁止原工作区/LF 访问、完整 A–B–A 重放 | `scripts/run_hf4_isolated.py` |

以上是实现和预定验证对照；具体通过数、失败修正、预算、版本与物理结论以本轮执行报告和 JSON 原始证据为准。均匀分层解 HuHu=0，不能据此给出非均匀二维接触或圆柱精度结论。
