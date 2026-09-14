# 需求、代码、测试与效果对照

更新：2026-09-14。本表连接总体目标与具体实现，执行后填入原始结果链接，不以计划中的文件名冒充已完成证据。最新0.5.0已通过HF4-B四组冻结均匀法向路径；旧0.4.0三过一失败及HF1–HF3结论保留各自历史范围。总结果见[修正验收摘要](../hf4_repair_results/acceptance_summary.json)，动机、变更与边界见[修正报告](HF4_REPAIR_REPORT.md)。

| 目标 / 为什么 | 当前实现入口 | 验证方法 / 证据 | 状态与效果 |
|---|---|---|---|
| 普通文件独立输入，消除LF运行耦合 | `hf_repo/src/hf_eval/data.py`、`regions.py` | HF1往返、395文件哈希、断开LF A–B–A | 已完成；几何资格独立pending |
| 实体线性参照，建立单位/端口基准 | `linear.py:analyze/solve_average_system` | HF1报告及纯实体解析/单元检查 | 已完成两例线性诊断 |
| 正确TMC材料/非保守HuHu/实际切线 | `tmc_kernel.py`、`tmc.py:assemble` | HF2修正报告：正常/强态/100目标HP | 0.2.1指定基准通过；旧失败保留 |
| 真实几何全域TMC及实体/背景边界区分 | [project.py:build_project](../hf_repo/src/hf_eval/project.py) | [test_project.py](../hf_repo/tests/test_project.py)、[真实约束图](../hf3_results/plots_002/regions_and_background_constraints.png) | 已完成；全域6642 DOF，实体/背景来源分列，交集去重 |
| 功共轭平均位移控制、反力符号 | [displacement.py:solve_displacement_path](../hf_repo/src/hf_eval/displacement.py) | [test_displacement.py](../hf_repo/tests/test_displacement.py)小KKT/弹簧/回滚；[最终回归](../hf3_results/regression_final.xml) | 已完成；端口保留相对自由度、非对称切线与失败状态 |
| 近零内力精度及独立约束验收 | [tmc_kernel.py](../hf_repo/src/hf_eval/tmc_kernel.py)、[hf3_precision_reference.py](../hf_repo/scripts/hf3_precision_reference.py) | [近零测试](../hf_repo/tests/test_tmc_near_zero.py)、[旧失败](../hf3_results/near_zero_v021_001/summary.json)、[修正复验](../hf3_results/near_zero_v3_final_001/summary.json) | 已完成；约5.97e-8→2.98e-13，材料/正则不变，976/192回归通过 |
| 两层桥接，分离实现误差和模型偏差 | [run_hf3_bridge.py](../hf_repo/scripts/run_hf3_bridge.py) | [39项检查](../hf3_results/bridge_001/summary.json)、[6态HP](../hf3_results/bridge_hp_001/summary.json) | 已完成；误差随幅值同比下降；初始刚度偏差约0.140%/0.159%，无符号反转 |
| 任务独立、结果带单位/版本/状态 | [project_evaluation.py](../hf_repo/src/hf_eval/project_evaluation.py)、[configs/hf3](../hf_repo/configs/hf3) | [test_project_evaluation.py](../hf_repo/tests/test_project_evaluation.py)；生产result/model/path/steps/hash | 已完成；失败目标null，最终I/O失败保留内存状态，原子提交标识独立 |
| 条件完整平均位移路径 | [run_hf3_path.py](../hf_repo/scripts/run_hf3_path.py)、[audit_hf3_states.py](../hf_repo/scripts/audit_hf3_states.py) | [放行记录](../hf3_results/full_path_gate.json)、[80态HP](../hf3_results/full_path_hp_001/summary.json)、[总验收](../hf3_results/acceptance_summary.json) | 两例各40/40目标到1mm，无补步/拒绝；完整HP通过，无工件自由输出 |
| 任意安装位置可独立运行 | [run_hf3_isolated.py](../hf_repo/scripts/run_hf3_isolated.py)、0.3.0 wheel | [独立39项检查](../hf3_results/detached/summary.json)、[安装回执](../hf3_results/detached_receipt.json) | 已完成；阻断原工作区/LF、HF1/HF3 A–B–A逐位一致，395文件不变 |
| 非零规定运动与分侧虚功合力 | [prescribed.py](../hf_repo/src/hf_eval/prescribed.py)、[normal_contact.py](../hf_repo/src/hf_eval/normal_contact.py) | [接口测试](../hf_repo/tests/test_prescribed.py)、[独立输入审计](../hf_repo/scripts/hf4_input_audit.py) | HF4-A完成；全局反力去重、材料/HuHu分量与方向明确 |
| 同模型误差与硬接触近似分开 | [hf4_normal_reference.py](../hf_repo/scripts/hf4_normal_reference.py)、[hf4_precision_reference.py](../hf_repo/scripts/hf4_precision_reference.py) | [12态预检](../hf4_results/reference_preflight_001/summary.json)、[原阶段摘要](../hf4_results/acceptance_summary.json) | 0.4.0历史：HF4-B为3/4通过；39个接受态含第四仅零态完成HP，已通过组合原压紧目标最大模型力差0.1969% |
| 数值失败必须定位并保留 | [固定态探针](../hf_repo/scripts/probe_hf4_precision.py)、[更新量探针](../hf_repo/scripts/probe_hf4_update.py) | [失败原记录](../hf4_results/g1_m1_001/result.json)、[排查报告](HF4_PRECISION_INVESTIGATION.md) | 0.4.0第四组合未过1e-9内部门；同输入力求值准确，绝对位移更新出现舍入平台，目标指标null；历史不回写 |
| 旧版本可搬迁与失败行为重现 | [run_hf4_isolated.py](../hf_repo/scripts/run_hf4_isolated.py)、0.4.0 wheel | [独立63项](../hf4_results/detached/summary.json) | 历史验收：粗网格A–B–A逐位一致，第四组合失败/回滚及null语义亦复现 |
| 先验证状态表示的因果作用，再改生产 | [冻结实施规范](HF4_SPLIT_IMPLEMENTATION_SPEC.md) | [阶段0干预](../hf4_repair_results/retained_update_001/summary.json)、[修正报告](HF4_REPAIR_REPORT.md) | 同一已存修正方向：保留更新的HP残差约6.890e-16，先舍入仍约1.841e-9；实验未用作生产初值 |
| 保存宏观运动与微小修正的实际权威 | [split_state.py](../hf_repo/src/hf_eval/split_state.py) | [test_split_state.py](../hf_repo/tests/test_split_state.py)、[实现文档](../hf_repo/docs/HF4_SPLIT_IMPLEMENTATION.md) | 0.5.0新增显式两数组、只读副本、schema/hash；显示和有损，旧状态导入不伪造已丢失小量 |
| 总G/F/Hu与J正确传播，保留完整导数 | [split_kernel.py](../hf_repo/src/hf_eval/split_kernel.py) | [test_split_kernel.py](../hf_repo/tests/test_split_kernel.py)、[六固定态预检](../hf4_repair_results/split_preflight_001/summary.json) | 强压缩、近单位、非零HuHu相消、等价分解、Jv及混合材料装配通过；材料/正则系数不变 |
| 预测/修正/回滚均使用两数组，防止假收敛 | [split_prescribed.py](../hf_repo/src/hf_eval/split_prescribed.py) | [控制器测试](../hf_repo/tests/test_split_prescribed.py)、[存档审计测试](../hf_repo/tests/test_hf4_split_audit.py) | 仅更新fluctuation；完整lift预测避免重复补偿；两数组回滚；已保存内力独立重算原生产1e-9停止门槛 |
| 独立提升实际状态，区分求值误差、平衡与模型偏差 | [hf4_split_precision_reference.py](../hf_repo/scripts/hf4_split_precision_reference.py)、[audit_hf4_split_normal.py](../hf_repo/scripts/audit_hf4_split_normal.py) | [HP测试](../hf_repo/tests/test_hf4_split_precision.py)、[新总验收](../hf4_repair_results/acceptance_summary.json) | D(lift)+D(fluctuation)权威、方向只扰动fluctuation；最大HP相对残差4.50301e-10，完整内力求值误差6.24321e-12×SF |
| 在原工况/门槛下复验四组合完整路径 | [run_hf4_split_normal.py](../hf_repo/scripts/run_hf4_split_normal.py)、原[HF4 spec](../hf_repo/configs/hf4/validation_spec.json) | [四组合与52态验收](../hf4_repair_results/acceptance_summary.json)、[修正报告](HF4_REPAIR_REPORT.md) | 四组各6/6原目标，52完整路径态加另2首目标态HP通过；压紧区最大硬接触模型力差0.196916%，只限冻结均匀任务 |
| 修正版本可搬迁、读回及重复运行 | [run_hf4_split_isolated.py](../hf_repo/scripts/run_hf4_split_isolated.py)、0.5.0 wheel | [73项安装验收及完整性摘要](../hf4_repair_results/acceptance_summary.json) | A–B–A和双数组存档读取通过；604去重测试通过、1跳过来自592+12两次运行；旧14运行文件除版本/376证据/395几何/旧ZIP验hash不变 |
| 一般二维接触/圆柱/稳定性/敏感性 | 后续HF4-C/D及HF5 | 均匀B已闭合，后续需单独冻结非均匀接触参考及误差规范 | C/D未开始；真实机构资格与功能未评价，不由制造场或均匀基准外推 |

每个新增或修正模块在阶段报告解释动机、具体改动及测试效果。验证失败也属于结果；必须留下输入和失败位置，并记录为什么允许或禁止下一步。

本轮可视证据为[力与间隙](../hf4_repair_results/comparison_plots_002/force_gap_comparison.png)、[有限介质参考一致性](../hf4_repair_results/comparison_plots_002/finite_reference_agreement.png)、[数值门槛](../hf4_repair_results/comparison_plots_002/numerical_validation.png)与[最后接受态变形](../hf4_repair_results/comparison_plots_002/last_accepted_deformations.png)；普通绘图数据与source hash同目录保存。[修正版交付包路径](../deliverables/HF4_repaired_evaluator_and_evidence.zip)是发布位置，科学结论以已保存验收摘要为准。持续维护文档、README与版本声明随结果更新；“旧文件不变”仅适用于明确列出并核验hash的历史集合，不代表整个工作区没有更新。
