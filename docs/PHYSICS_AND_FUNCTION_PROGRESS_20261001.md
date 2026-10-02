# 物理与功能开发进度

2026-10-02增补：新候选的[NumPy完整力、组装、解析切线与新平衡](NUMPY_FORCE_PROGRESS_20261002.md)已闭合一条C1固定压缩任务。三近旋转场/C1保存态三力门、七方向21切线门、15唯一新平衡态336项新HP80/120检查均通过；[新实际变形与力曲线](../functional_views/numpy_c1_20261002/numpy_path.png)、[16帧动画](../functional_views/numpy_c1_20261002/numpy_path.gif)可人工检查。以下2026-10-01矩阵中的“新候选完整force未闭合”是当时状态：现在NumPy功能已有上述受限验证，compiled force/AD和原全矩阵资格仍待后续。整体目标、一般接触、平均端口及真实夹持任务边界继续适用。

2026-10-01。本文回答“目前能算什么、这些量意味着什么、下一步怎样得到有用结果”。依据现有源码和已经保存的数值结果整理；本次文档编写没有运行新的力学计算。近期执行细节另见 [CURRENT_STATUS](CURRENT_STATUS.md)，这里以功能为主。

## 目标与已经具备的能力

整体目标是独立 HF 正向力学评估器：给定普通几何文件、材料、边界与任务，得到有单位和符号的位移、节点内力、支反力及任务响应，最终支持真实夹持任务和候选比较。LF 负责几何生成与研究层的选择、统计；HF 运行时不依赖 LF 工作目录或优化器。当前已有真实机构的自由输出计算和受限接触计算，尚未完成真实工件夹持和批量 HF 评价。

“已实现”表示代码入口存在；“受限通过”表示对应已保存案例经过数值验证，范围按该案例理解；“未实施”表示不能从方案或外部结果推定为本线功能。

| 功能 | 代码与当前进度 | 物理含义及范围 |
|---|---|---|
| 独立几何读取 | [data.py](../hf_repo/src/hf_eval/data.py)、[evaluate/inspect](../hf_repo/src/hf_eval/evaluation.py)；两例规范几何导出、独立安装与断开 LF 读取已通过 | 单元掩膜、尺度、厚度、支承与端口可独立读取。LF v2 新格式的准备层转换仍是方案，不能直接当作已接入 |
| 实体线性诊断 | [linear.py](../hf_repo/src/hf_eval/linear.py)；反向器、夹持器两例通过 HF1 | 已得到微小输入下的位移、输入广义力与变形图；用于单位、方向、支承及线性极限检查，无工件接触 |
| TMC 非线性与内力组装 | [tmc_kernel.py](../hf_repo/src/hf_eval/tmc_kernel.py)、[tmc.py](../hf_repo/src/hf_eval/tmc.py)；HF2 修正 C-shape 的100原目标、HF3 两条40目标机构路径已验证 | **已有实际材料力、HuHu 正则力、总内力及一致非对称 Jacobian，并能求平衡。** 最近新候选尚未通过，不等于旧 TMC 没有 force 功能 |
| 单数组平均端口控制 | [displacement.py](../hf_repo/src/hf_eval/displacement.py)、[project_evaluation.py](../hf_repo/src/hf_eval/project_evaluation.py)；HF3 两例自由输出路径通过 | 约束端口平均位移，端口节点仍能相对变形；输入乘子为驱动器作用于模型的广义力，可读出输出平均位移 |
| split 位移与 Dirichlet 路径 | [split_state.py](../hf_repo/src/hf_eval/split_state.py)、[split_prescribed.py](../hf_repo/src/hf_eval/split_prescribed.py)、[split_affine.py](../hf_repo/src/hf_eval/split_affine.py)；HF4-B 四组合完整通过，C1/C2 有受限通过结果 | 分别保存宏观 lift 与微小 fluctuation，避免微小 Newton 更新被大位移吞掉；现有 split 控制是规定自由度位移，支持显式阶段交接 |
| split 平均端口增广控制 | 尚未实现；现有单数组平均端口与 split Dirichlet 控制不能直接拼接充当该系统 | 需要对 `b_inᵀ(u_lift+u_fluctuation)=d` 建立明确的增广方程，才能将 split 状态用于同类机构平均驱动 |
| 受限法向接触 | [contact_reference_a0.py](../hf_repo/src/hf_eval/contact_reference_a0.py)、[contact_c1.py](../hf_repo/src/hf_eval/contact_c1.py)、[contact_c2.py](../hf_repo/src/hf_eval/contact_c2.py)；C1十条选定路径80态通过，v4细网格21态通过 | 已比较分离接近、规定闭合阶段及持续压紧的参考/TMC响应，也观察二维非均匀加载。v4只补测一个固定均匀任务 |
| 一般局部接触、释放与重新接触 | 未完成一般主动集及相应物理验证 | 目前不能保证任意接触面、有限面离开/重入、卸载释放、角点等情形；已有阶段约束激活不等于一般接触算法 |
| 真实夹持力 | 尚未实现带真实机构与工件的已验收任务；[HF5任务草案](HF5_LF_V2_ADAPTER_AND_TASK_PLAN.md)已有定义建议 | 需要明确工件、间隙与加载后，读取工件的约束反力。HF3自由输出位移、输入广义力或 LF 输出弹簧力均不能改名为夹持力 |
| 近旋转新候选的完整 force / AD | [split_kernel_invariants_hu.py](../hf_repo/src/hf_eval/split_kernel_invariants_hu.py)已有响应实现及 NumPy 运算路径；有限算术/结构比较通过。完整 compiled force 同步及三力精度门仍未闭合，完整候选 AD 验证未完成 | 稳定 F 旧候选63保存态通过，但33制造场中3近旋转场失败。新候选应以实际力向量和参考比较判断，不能用微图通过或编译完成代替 |
| HF5、优化与1800候选 HF 标签 | HF5尚未实施；优化/生成研究层在 LF/N4 来源中存在，独立 HF 不是新优化器。1800包来源与语义已有审阅，未在本线生成可验收的批量 HF 标签或最终排名 | 外部标签可作研究资料，不能当作本实现、当前任务的高保真结果；先用一个有效任务，再逐步扩大比较数量 |

历史功能结果分别见 [HF1](HF1_REPORT.md)、[HF2修正](HF2_REPAIR_REPORT.md)、[HF3](HF3_REPORT.md)、[HF4 split修正](HF4_REPAIR_REPORT.md)、[C1](HF4_C1_FINAL_REPORT.md)和 [v4](HF4_C2_V4_RETEST_REPORT.md)。这些报告中的旧“下一阶段未执行”描述属于当时状态；上述矩阵汇总到本页日期。

## 现有物理结果怎样理解

HF3 两例真实几何已能独立计算有限变形下的自由输出。输入平均位移与输入广义力功共轭；夹持器的输出是单侧夹爪运动。没有工件且输出弹簧系数为零，所以其零输出弹簧力并不是“已测得零夹持力”。力、能量和位移均按所建下半模型报告，不隐含乘二。

可直接人工查看以下已有真实机构图；`path_01` 的保存来源及图标题均为反向器，`path_02` 为夹持器。两条路径各完成40个原目标，末态平均输入均为1 mm；数值取自 [HF3实际报告](HF3_REPORT.md)。变形图使用真实位移比例1，J图分别显示实体和介质的单元积分点最小值，不能当作接触压力图。

旧图标题的`qualification pending`保留绘图时点；后续80路径态与6桥接态的独立HP审计已完成，结论以HF3报告为准，不改写历史PNG。

| HF3无工件自由输出任务 | 末态输出平均位移 q_out [mm] | 输入广义力 R_input [N] | 已有图 |
|---|---:|---:|---|
| 反向器；输出正方向−x | 1.682304535 | 0.175256261 | [实际变形与J](../hf3_results/plots_002/path_01/last_accepted_deformation_and_J.png)、[路径响应与数值诊断](../hf3_results/plots_002/path_01/accepted_path_diagnostics.png) |
| 夹持器；下夹爪输出正方向+y | 1.161186104 | 0.216125158 | [实际变形与J](../hf3_results/plots_002/path_02/last_accepted_deformation_and_J.png)、[路径响应与数值诊断](../hf3_results/plots_002/path_02/accepted_path_diagnostics.png) |

这些图显示已有机构运动和求解响应，没有工件、夹持力或新的机构功能验收；本次只是补充已有图链接，没有增加物理覆盖或重新求解。

C1 的合成实体为2×1 mm、厚1 mm，初始间隙0.25 mm，材料E=100 MPa。它让实体参考 A0、实体正则化诊断 Aalpha 和 TMC 使用共同驱动。细网格 TMC 在名义闭合前 d=0.125 mm 已有约0.0003901 N反力，在 d=0.25 mm 有约0.20059 N；这是介质的接触前传力与转折响应。压紧后的净力接近 A0，有助于判断这一固定任务，但不能证明转折、局部接触压力或任意接触均正确。底边约束对模型的+y合力为正，顶边沿同一方向读出通常为负；完整反力包含材料和正则贡献。

非均匀任务中，规定阶段的平均预压保持0.375 mm，随后改变零均值驱动幅值。C1末态净力和变形已保存；C2进一步考察背景宽度、外底边约束和网格。局部负节点力是离散弱式反力，须结合材料牵引及正则贡献理解，不能直接把它裁成零或逐点当作物理接触压力。

## 可视化与最近一个功能步骤

本轮已将历史 `TMC_h025_uniform_r2` 的15个保存态画为 [数值、反力与末态变形图](../functional_views/c1_baseline_20261001/saved_mechanics.png)及 [15帧逐态压缩动画](../functional_views/c1_baseline_20261001/compression.gif)，[绘图元数据](../functional_views/c1_baseline_20261001/metadata.json)记录来源和实际数值。图含参考网格与实际变形，位移比例为1且全程使用相同位移色标；反力箭头另用固定显示比例0.03779618 mm/N，不是结构位移。位移显示是存盘两数组的舍入和，科学状态仍以两数组为准。静态图已实际查看，图中文字和六个面板可辨认。

粗网格末态驱动0.5 mm时，已存HP80法向力为71.4239021981 N；全底边生产反力约71.4239021980 N，其中实体底组约66.9596498900 N、外区介质组约4.4642523080 N。实体顶到刚面的保存间隙为4.2654e-6至5.7839e-6 mm。15态生产法向读数与HP80的最大绝对差约5.8634e-11 N。这些数值帮助看清“实体压向上平面、介质被压薄、约束反力增长”的已有功能；这是历史合成压缩基准的重绘，没有新FE或HP求解，不是LF机构的夹持力，也不授予新候选通过。

[保存态查看器](../hf_repo/scripts/plot_saved_mechanics.py)仅用NumPy/Matplotlib/Pillow读取三来源并绘图。元数据保存原读取位置、项目相对路径、bytes与SHA，异机可在恢复树中对照，不需复刻原盘符；本轮补相对来源字段没有重求解或改变图/动画。

已有 [C1两网格力比较](../hf4_c1_results/summary_v2/c1_force_comparison.png)、[分量与数值误差](../hf4_c1_results/summary_v2/c1_precision_and_components.png)和 [实际比例变形](../hf4_c1_results/summary_v2/c1_last_accepted_deformation.png)仍可对照。重绘不增加物理覆盖。

最近的最小功能闭环建议是：为新候选已有 `_response(..., xp=np)` 提供清晰的 NumPy 力入口，先用原 `unit__near_rotation` 的实际 lift/fluctuation 计算全部八个自由度的材料力、正则力和总力。它能绕开当前大型 JIT 图的执行等待，直接回答新公式是否改善已知的力误差；这会增加可用的固定状态响应入口，尚不等于实现新的平衡路径。

本步只需比较已保存 HP80/120 参考，保留原总力 `1e-11`、两分力 `1e-9` 的归一尺度与门限，同时检查有限值、`J>0`、支持域及力分解一致性。给出八分量数值表、参考/变形网格叠图、三类力及误差图，明确该位移场是给定场。随后根据结果决定：通过则接一个已验证 C1 保存态的全局组装，检验实际残差的切线/Jv，再推进平衡控制；失败则针对实际误差分量修改。记录一份结果 JSON、数值数组与短说明即可。

Profiler及F系列日志只用于解释计算成本和运行异常，不能替代物理力、位移或接触验证。用户已批准的F-SELECT1可按其范围进行，其结果不是所有功能开发的永久前置门，也不会自动改变上述功能资格。每个后续功能步骤都应产生实际数值、力或变形图，再据结果选择下一步，避免预先展开长实验链。
