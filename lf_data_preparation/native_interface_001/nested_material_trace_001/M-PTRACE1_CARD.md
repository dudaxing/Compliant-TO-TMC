# M-PTRACE1：两态保存材料 P 的工件外邻边界诊断卡

2026-10-11，来源基线为已实际发布并恢复的 main `808e719945f3a378704deea7c492eaaee50a39cd`。本卡处于源码准备／待批准；本卡本身不是执行授权。M-LEDGER2 已通过并关闭，不续用其额度。

## 目标与依据

整体目标仍是读取普通 LF 几何，在独立 HF 有限变形／TMC 前向任务下输出可靠、可解释的反力、工件载荷和真实变形，供外部研究层比较。HF 不优化、不调用 dmftd，后续继续 main，origin 保持 `https://github.com/dudaxing/Compliant-TO-TMC.git`。

M-LEDGER2 全 24 态显示：加载 0.85 mm 的底边 Hu Fy 为 −0.011794230646605314 N，两个物理角点为 +0.012892696672903312 N，净 Hu Fy 只有 +0.001157502187101581 N；峰值加载 1.2 mm 的材料净 Fy 为 +0.12191255705872141 N。先看强局部抵消态与材料主导峰值态的外邻材料应力，比继续扩展账本或重求解更直接。

仅分析两个已接受的原 loading 态：index／original_target_index 6、d=0.85 mm、state SHA `2d19d368d255e5966c880502f444386c2d56336e7201a017e849f3fcd7ae61dd`；13、d=1.2 mm、state SHA `b9024263e887e0f0813c8ef64c6686f0b65899555bad19cf67a98f293958d7ed`。它们不是新的加载路径，也不代表其余 22 态的新应力分析。

## 输入和新功能范围

来源、原文件 SHA 和具体运行参数冻结于同目录 `protocol.json`；静态依据为 `author/trace_input_scope.json` 与 `author/trace_physical_basis.json`。正式源码在 `hf_repo/src/hf_eval/saved_material_trace.py`，薄执行器为本目录 `execute_saved_material_trace.py`，复用既有通用 launcher 字节。

本次新增受控读取 **5 个既存 NPZ**：model.npz 一次仅取 coordinates、connectivity、solid、workpiece_cells、points、thickness；两态 forces.npz 各一次仅取 stress_first_piola；两态 state.npz 各一次仅取 lift、fluctuation。共 12 个指定数组字段，按原 descriptor 的 dtype、shape 与 C-order raw field SHA 核对。读取原描述、普通 view／nodal／geometry JSON 和 result／summary 作身份及边界核对。不开启其余 NPZ 字段，不调用原模型加载器或力学观察器。

公共 NumPy 入口每态一次，共 2 次。从真实保存 connectivity 和 workpiece_cells 找出每条物理边的 body／outer owner，保留原 node-ID 无向边身份，原 solid／medium 相位由 exterior owner 的 solid 数组给出，不能把运动学 overlay 当新材料掩码。结果边集合须与各态原 nodal physical72／cut36 对账；对称切面单独记录并排除本次物理边界线积分。

## 物理定义

原固定下半方体 x62..80／y31..40 mm，身体外向参考法向 bottom=(0,−1)、left=(−1,0)、right=(+1,0)。不能由无向排序 edge 旋转生成法向；right 由原方体定义与参考坐标确定，旧 geometry faces 仅保存 bottom／left。

原 9 点为 xi、eta∈{−1,0,1}、xi 慢／eta 快的 Simpson 采样，包含边界点。bottom 取外邻 top 面点索引 [2,5,8]，left 取外邻 right 面 [6,7,8]，right 取外邻 left 面 [0,1,2]，按真实 points／owner／参考坐标核对，不插值、不跨 owner 平均共享角点值。每态 72 条边×3点，合计 **432 个样本／144 条边／6 个侧面／2 个整体汇总**。

保存 P 是材料第一 Piola，单位 MPa，本身不含厚度；名义材料牵引为 P_exterior·N_body，分量仍为 MPa（N/mm² 参考面积）。名义法向压缩定义为 −N·(P N)，保留正负；剪向按采样正向 T：bottom=(1,0)、left／right=(0,1)，不是闭合有向边界切向约定。不截负值、不取绝对值替换符号。

解释性材料边积分采用独立参考线权 L×[1,4,1]/6，再乘原厚度 20 mm **一次**。不得复用含面积×厚度的原 9 点 volume weights；原节点弱力 N 已含厚度，也不能再次乘厚度。输出外邻单侧迹边／侧／整体向量，和原 state.json 的整体材料弱力并列及作有符号差。离散外邻应力迹积分与体积弱式载荷不是预先规定相等的量：Q1 基函数、单元应力跳跃、体积／线积分及 rounded P 与原补偿收缩均需解释；**不设相等、百分比或近零科学门**。

固定 overlay 内部 F=I、P=0 不能解释外部传力。材料 P·N 不是包含 Hu 的总压力；本卡不输出 Cauchy 应力、当前面积压力或已合格夹持力，不重建 Hu 边界项／角点项。

## 输出与人工检查

新 `run_001` 下保存 `material_trace.json`、432 行 `samples.csv`、144 行 `edges.csv`、6 行 `sides.csv`、2 行 `whole_material_comparison.csv`，以及 helper `execution_receipt.json`。表中保留两态原身份、body／outer owner、node IDs、边／点索引、相位、参考位置、P 四分量、PN、法向压缩／约定剪量、独立线权及积分向量。

唯一执行器写 **2 张 PNG**：`actual_material_trace.png` 是两态原下半域的实际结构边界／工件邻域细节与材料迹采样；`nominal_material_profiles.png` 是三物理侧的有符号名义压缩／剪量曲线。形变坐标复用旧 viewer 左结合 `X + lift.reshape(-1,2) + fluctuation.reshape(-1,2)`，只作 rounded 显示，不作为精确 split 力学状态。工件固定，所以其参考／当前边界位置重合。两态共用有符号色标／相应轴尺度，图例放图外；保留原采样，不平滑、剪裁或变更旧图。旧 24 帧 GIF、M2 两图与原观察结果保留。

## 检查、预算和停止规则

静态审阅先核输入路径／原 field 规范、owner／面／点映射、N／T／线权和调用路径、两图与输出用途，区分尚未解码的声明和实际数组证据。批准后一次实际运行核来源绑定、5 档案／12 数组、两态身份、有限值及原边集合／预期行数、2 API／2 PNG 和终态收据。这些是本次保存数组读取与输出有效性检查，不升级原力核／切线／HP、接触、压力、夹持或网格收敛资格。

一次 helper **180 秒**、outer **240 秒**、采样 RSS **8 GiB**。复用通用 launcher；child 在读取／处理／输出之间检查停止信号与自身采样资源，输出 SHA 完成后作末 checkpoint，helper 时间／RSS为成功收据构造／写入前快照，outer 覆盖完整进程终态。内存是采样合同而非 OS 硬限制，段内操作可能在下一 checkpoint 才停止。不得以剩余墙钟扩展状态／数组／图／功能范围。

**一次启动，首错停止，无重试、修复重跑、延期或 force。** 任何来源、数组、身份、拓扑、有限值、资源或输出异常均记录实况并闭卡，不修改原值／旧证据，不自动修复后重跑。通过后写实际结果／目标／理由／效果／限制，提交推送 main 并恢复核对。新读取、PN／线积分和绘图计数与无新本构、force-kernel、tangent、HP、模型构造、平衡求解明确区分；不声称零新增计算。

本次不新增求解路径、本构或力核调用、F／Hu 重建、T／HP、LF 优化、总压力、自由体／摩擦任务、正式标签排名或 HF5 完成。后续只依据实际两态结果判断是否需要解释离散弱力与外邻迹的差别，再规划 Hu 总边界作用及夹持功能；不提前扩成全路径分析。
