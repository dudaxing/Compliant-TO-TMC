# M-SUPPORT1：两态保存单元材料力的工件节点支撑诊断卡

2026-10-11，基线为已实际发布并增量恢复的 main `96bfea73ebb538d413dd01b722fa1f3a6d43913d`。本卡是具体候选与待批准方案，本身不是执行授权；已通过的 M-PTRACE1 窗口关闭。

## 目标与实际依据

整体目标仍是读取普通 LF 几何，在独立 HF 有限变形／TMC 前向任务下提供可解释的反力、工件载荷和实际变形，供外部研究比较。HF 不优化、不调用 dmftd；继续 main，origin 保持 `https://github.com/dudaxing/Compliant-TO-TMC.git`。

M-PTRACE1 已唯一执行通过：loading 0.85／1.20 mm 的材料线 Fy 为 +0.0029293605006823825／+0.027662985836060965 N，原材料弱 Fy 为 +0.0034790753630243565／+0.12191255705872141 N；line−weak 为 −0.0005497148623419741／−0.09424957122266045 N。峰值差值得解释，不能当舍入噪声，也不能用 Hu 补平材料与材料的差。

本次用原保存单元材料力追溯同一工件节点弱载荷，先回答底边、两侧、身体内部和只触及角点的对角单元各贡献多少。只分析原 index／original_target_index 6（loading、0.85 mm、state SHA `2d19d368d255e5966c880502f444386c2d56336e7201a017e849f3fcd7ae61dd`）和 13（loading、1.20 mm、state SHA `b9024263e887e0f0813c8ef64c6686f0b65899555bad19cf67a98f293958d7ed`），不扩展其余 22 态。

## 输入与功能

冻结来源与字节 SHA 见 `protocol.json`；静态依据见 `author/support_input_scope.json`、`author/support_physical_basis.json`。新增公共 NumPy 入口 `hf_repo/src/hf_eval/saved_material_support.py`；本目录薄执行器读取普通保存资料，不调用原模型加载器或旧观察器。

仅解码 **3 个既存 NPZ／8 个指定数组字段**：model.npz 一次取 coordinates、connectivity、edofs、workpiece_nodes；两个 forces.npz 各取 element_material_force、global_material_force。逐字段核原 dtype、shape、C-order raw SHA 后使用。身体 cell／node／DOF、全部 fixed DOF 的完整 ID 来自原 model.json 元数据；原 state/result/nodal 与已保存 material_trace、sides、whole CSV 作身份、节点载荷和迹值关联。

不解码 solid、P、lift／fluctuation、F／J／Hu、grad／weights、总力／正则力、切线；不重算材料力。坐标只表示参考支撑位置，新图不宣称实际变形。原 M-PTRACE1 实际变形图和 24 帧 GIF 可以通过链接人工对照。

每态一次入口、一次原 **C-order `np.bincount(edofs.ravel(), weights=element_material_force.ravel(), minlength=ndof)`**。须与原 global_material_force **精确数值数组相等**；这是同一保存组装算子的重播检查，不是原字节或 signed-zero 门，不是新的本构参考。

工件作用载荷取保存内部力的负号：每个局部 body-node 出现只取该节点的两个材料分量，不能把整个单元八分量总和归给身体。原力单位 N，已含厚度 20 mm，不再次乘厚度或面积。每个局部出现仅归一个支撑类别：body、bottom_owner、left_owner、right_owner、corner_only。前三物理外邻类别按旧材料迹的真实 owner 与原 connectivity／node-ID 边对账；剩余仅共享一个物理底角节点的单元归 corner_only。它们是 Q1 基函数支撑类别，不能称作表面压力分区。

每态预期 **722 个支撑单元／2738 次局部节点出现／703 个身体节点**；五组单元数 648／36／18／18／2。两个 corner_only 单元 10371／10408 的原材料相位本卡不读取，不推断为 third_medium。内部 body 项保留原保存值，不预先丢弃或强置零。

## 对账规则与解释边界

新增 regrouping 用标量 `math.fsum` 汇总局部出现到节点、组与整体。每身体节点至多 4 个原局部贡献，实际拓扑须检查该前提；节点／整体与保存 global 选择值的误差界为 **8 × 2⁻⁵² × 对应被选局部元素项绝对值之和**，无绝对地板。原顺序 `bincount` 先精确重播；这个局部 L1 包络只核不同求和次序的保存数据投影。最多四项原浮点累加与有限层 fsum 的舍入界依据已明确记录于物理报告。

这是一项明确的新保存组装／投影一致性规则。原 M1/M2 的 8eps × 原节点 L1 门保持原字节与用途；不能把节点内强抵消后的 L1 当作局部元素重排的界，也不能替换或放宽旧门。新入口保存 global 节点向量与原 nodal material 向量、整体与原 state/nodal/PTRACE weak 全部精确数值对账。

旧 PTRACE 三侧／整体线值仅并列复制，不重取 P 或积分。支撑组弱力与相应侧线力不设相等、百分比或近零科学门。对角单元可通过体内 Q1 梯度影响一个角点，却没有有限长度的身体面；其贡献不是点接触压力。相同外邻 owner 的体积弱式与材料边界迹还可能受基函数、其余面、Div(P)、应力跳跃和不同积分影响；本卡不能单独证明这些连续项、求解器缺陷或网格收敛。

## 输出与可视化

新 `run_001` 保存 `support.json`、五张 CSV：`occurrences.csv` **5476 行**、`cells.csv` **1444 行**、`nodes.csv` **1406 行**、`groups.csv` **10 行**、`whole_material_comparison.csv` **2 行**。保留原态身份、cell／local-node／global-node IDs、参考位置、内部／ON-body 材料分量、支撑类别、原节点值、重组值／误差／局部 L1 界，以及旧材料迹对照值。三 owner 组保存对应旧侧 line 与 support−side-line 的解释性差；body／corner_only 没有侧线值，保持为空，不发明边界面。

唯一运行写 **2 张 PNG**：`reference_support_map.png` 显示参考位置的带符号单元身体投影 Fx／Fy，两态每分量共用色标，标记工件与两角点；`material_support_comparison.png` 显示五类有符号材料贡献，并列原 weak／旧 line。图上明确 N、材料分量、基函数支撑与参考位置；不平滑、不截负值、不把支撑类别标为压力侧面。另存 helper `execution_receipt.json`，合计 9 个输出。

## 预算、检查与停止

先完成源码／AST、JSON／CSV 身份、字段声明／原字节、符号／owner映射／舍入规则、输出和图用途的独立静审；这不等于数组投影或新图实际通过。批准后一次运行核原绑定、3 档案／8 字段、2 入口／2 完成回放、实际支撑集合与行数、节点／整体对账、2 PNG 与进程终态收据。

复用原通用 launcher 字节。helper **180 秒**，outer **240 秒**，采样 RSS **8 GiB**。child 在读／处理／输出之间检查停止与资源；输出 SHA 完成后末 checkpoint，helper 时间／RSS 是成功收据构造前快照，outer 覆盖完整进程终态。采样合同不是 OS 硬限，段内操作可能在下一 checkpoint 才停止。

**一次启动，首错停止，无重试、修复重跑、延期或 force。** 来源、字段、身份、拓扑、组装、投影、资源、输出任何异常按实记录并闭卡。剩余时间不扩状态或功能；不修改旧值或拼接资格。通过后记录目标／行动／理由／结果／效果与限制，读取两图像素人工检查，提交推送 main 并增量恢复核对。

本次有新数组读取、保存材料组装重播、投影与 fsum、差值／界计算和新绘图，不能声称零新增计算。无新力核／本构、F／Hu 重建、T／HP、模型构造、Newton／平衡路径、LF 优化、总压力或有效夹持资格。总 Hu 边界作用、自由体／摩擦、网格收敛、正式标签排名与 HF5 仍未完成。下一步根据实际局部支撑结果选择最小解释与实现步骤，不预先扩成全路径分析。
