# HF 数据契约草案 v0.1（HF-0 提案，尚未冻结）

本文件设计独立数据接口，不是已经完成的导出器或读取器。当前实际样本映射见 `hf0_audit/lf/` 的审查产物；HF-1 将用它们验证并冻结 v1。论文参数、LF 生成参数与 HF 项目任务参数分别保存。

## 1. 四类对象与目录

```text
geometry_dataset/
  index.json                       # 全档案索引、当前交接子集、缺失资产状态
  geometries/<geometry_id>/
    geometry.json                  # 权威数组的物理语义、区域标签和校验
    geometry.npz                   # solid、design、passive_solid、passive_void
    preview.png                    # 派生显示，不定义几何
  generations/<generation_id>.json # 一次生成记录；多个记录可指向同一几何
  provenance/                      # 已有密度、轮廓、日志等资产及原始字节校验
  tasks/<task_id>.json             # 同算例共享的物理任务
  evaluations/<evaluation_id>/
    result.json
    path.npz
    figures/
```

HF 仓库拥有格式说明、通用读写/校验和结果接口；LF 专用转换脚本位于 `lf_data_preparation/`。数据包只含普通 JSON/NPZ 等数据，不依赖 LF Python 类、函数或可执行代码。NPZ 读取必须使用 `allow_pickle=False`。

`index.json` 分开记录 `archive_records`、`handoff_subsets` 和 `evaluations`。旧 v1/v2 清单是来源索引，不能直接宣称已是统一 HF 格式。相同几何只存一份权威数组，但生成记录、选择序列及已知计算成本不去重删除。没有独立 geometry.npz、只有归档 clean 数组的候选也保留其资产位置与状态。

## 2. 几何对象

第一版以规则网格的二值实体单元分布为唯一权威表示。不得从 PNG 或轮廓反向覆盖掩膜。实际映射文件为 `hf0_audit/lf/mapping_inverter.draft.json` 和 `mapping_gripper.draft.json`；其中暂定身份算法与字段结构只作 HF-0 展示，HF-1 按本草案完成一次明确的版本冻结，不把这些草稿宣称为已统一的 v1。

| 字段 | 语义与第一版约束 |
|---|---|
| `schema_version`, `geometry_id`, `case_family` | 显式版本；反向器/夹持器分开；标识不使用文件名代替内容 |
| `arrays` | NPZ 相对路径、字段名、shape、dtype、各数组内容摘要与文件 SHA256 |
| `solid` | uint8，0=非机构实体，1=机构实体；空区以后由任务指定为 TMC、外部空间或工件区域 |
| `design`, `passive_solid`, `passive_void` | 同 shape 的 uint8 区域掩膜，互斥且覆盖当前像素域；被动实体必须 solid=1，被动空区必须 solid=0 |
| `grid.shape_yx` | `[ny,nx]`，C 顺序，索引 `[j,i]`；不沿用 MATLAB 的线性索引 |
| `grid.origin_mm` | 网格左下角节点坐标；行 0 在物理下方，列 0 在左方 |
| `grid.cell_size_mm` | `[dx,dy]`；单元 `[j,i]` 覆盖 `[x0+i dx,x0+(i+1)dx] × [y0+j dy,y0+(j+1)dy]` |
| `grid.axes` | 固定全局 +x 向右、+y 向上；数组值定义在单元，不是节点 |
| `thickness_mm` | 真实面外厚度；进入总力、刚度、能量积分；不只写“单位厚度” |
| `model_extent` | 半/全模型、镜像轴及几何重建方式；倍数由具体指标定义，不能统一乘 2 |
| `region_tags` | 支承/输入/输出等物理线段或多边形；用于选择节点，旧节点号仅留 provenance |
| `processing` | 原密度标识、实际阈值、被动覆盖、已有清理顺序和变化计数；本轮没有做的处理不能补写为已执行 |
| `derived_assets` | 轮廓/图片相对路径及摘要；轮廓若没有稳定方向/孔洞标签，记录现有语义与缺失项 |

物理尺寸 `nx dx × ny dy` 必须与显式 extent 一致。第一版单位固定 mm；来源单位不同需显式转换并记录，禁止只改标签。原始连续密度另存 `provenance/`，不得用它替代正式 `solid`。

几何身份建议为 SHA256：版本化规范头（网格 shape、原点、方向、尺寸、厚度、半/全模型描述）加固定顺序四个 uint8 数组的 C 顺序字节。数值规范头的编码规则在 HF-1 冻结，避免 JSON 浮点格式歧义；原始压缩 NPZ 文件另算字节哈希，不能只用 ZIP 元数据作几何身份。来源记录不进入几何哈希。端口/区域标签另有描述摘要；改标签不会抹掉旧描述版本。

几何ID固定在导入后冻结的权威原始网格与其物理语义上。HF细化整数倍网格且所有子单元继承原材料时，仍引用该 geometry_id，另生成 mesh_id/discretization_id；不得用细化后的数组重新计算并覆盖原几何身份。两个独立输入若分辨率不同，不自动宣称几何哈希相同，必要时另建立经核验的物理等价关系。如阶梯边界平滑、圆柱像素化规则改变、阈值或清理改变，则是显式几何/任务离散转换，需要记录差异。扩大介质域不能改变机构原点、物理尺寸及真实支承。

## 3. 端口和约束的物理语义

一个端口至少包含物理线段、固定参考方向和权重规则：

```json
{
  "id": "input",
  "region": {"kind": "polyline_mm", "points": [[0,38],[0,40]]},
  "direction_reference": [1,0],
  "averaging": "normalized_reference_arclength_trapezoid",
  "source_nodal_weights_example": [0.25,0.5,0.25]
}
```

这是实际 1 mm 网格端口的映射示例。细网格应从同一物理线段重新构造归一化弧长积分权重，不能照搬 3 个旧节点。若端口端点不落在网格节点上，v1 先明确拒绝不支持的映射并报告；不得默默把端口移到最近节点。非轴对齐、跨单元积分在必要时再扩展。

定义 `q=bᵀu`、`f=Fb`，权重和方向固定在参考构形。平均输入位移约束为 `b_inᵀu=d`，保留端口局部变形自由度。可使用拉格朗日乘子联立系统：`R_internal + k_out b_out b_outᵀu - f_external - b_in λ = 0`、`b_inᵀu=d`。输出 `R_in=λ` 表示执行器对机构的广义力，机构对执行器为 `-λ`，符号须随结果保存。输出广义弹簧是秩一刚度，不是逐节点独立弹簧。

几何只提供可定位的支承/对称区域，任务明确施加哪些分量。尤其夹持器的真实实体对称段与第三介质背景对称边界是不同字段；背景边界会传力，必须写入任务版本。几何端口不能自动成为圆柱接触约束。

## 4. 两个真实样本如何映射

首对建议使用归档 80×40 网格候选：

- `inverter__sweep__kin_1e+01__kout_1e-01`
- `gripper__sweep__kin_1e+01__kout_1e+00`

二者均来自已有 LF 优化记录；本轮是读取和审查。以最终 LF 审查 JSON 为字段和值的证据，禁止将本段当作独立数据包。

| 属性 | 反向器 | 夹持器 |
|---|---|---|
| 权威来源 | 归档 `geometry.npz` 中 clean | 同左 |
| 网格/尺寸 | shape `[40,80]`，1×1 mm，80×40 mm | 同左 |
| 原点/厚度 | 左下角 `[0,0]`，20 mm | 同左 |
| 几何范围 | y=40 mm 对称轴下半模型 | 同左 |
| 夹具 | x=0，y∈[0,8]，源任务 ux=uy=0 | 同左 |
| 输入 | x=0，y∈[38,40]，+x | 同左 |
| 输出 | x=80，y∈[38,40]，−x | x=80，y∈[28,30]，+y |
| 1 mm 端口权重 | `[1/4,1/2,1/4]` | 同左 |
| 实体对称段 | y=40，x∈[0,80] | y=40，x∈[0,60]；来源 `full_midline` 还约束 x∈[60,80] 的软隙顶边，单独记为来源背景边界策略 |
| HF 材料/行程/输出负载 | `null/pending` | `null/pending`，圆柱和间隙也 pending |

清理历史、被动区实际索引、面积与来源哈希由审查附表给出。夹持器被动实体为 [60,80]×[28,30] mm²，被动空区为 [60,80]×[30,40] mm²。实际实体面积分别1128、1086 mm²；设计区体积分数分别0.3525、1046/2960≈0.353378；两例 HF 资格均 pending。支承段9个源节点分别只有4、3个与实体附着；背景介质不能自动接受同样的夹持条件。源输入/输出弹簧、力、材料、LF 指标属于 generation 的 `source_task`，不自动成为未来 HF 任务。

## 5. 生成、任务和评价对象

`generation_id` 标识一次记录，包含原 archive SHA256、相对源成员路径、来源候选标识、运行类别（读既有结果/从密度导出/重新优化）、方法参数、初始化、已知种子、已有运行状态/耗时/迭代数和 LF 指标。未知成本写 null；复用基线的实验记录与实际新优化次数分别计数。相同几何多个生成记录是合法关系。

`task_id` 描述一个算例共同物理任务：材料与其来源、二维假设、厚度解释、真实夹具、对称条件、参考状态、输入路径、输出负载/工件、第三介质域与边界、指标定义、资格阈值。每个数值标明 `user_decision`、`uploaded_baseline` 或 `proposed_pilot`，后者不宣称冻结。反向器和夹持器分别有任务，不混排。

TMC 材料刚度与正则化参数改变响应，也要纳入评价的模型版本；将它们组织在 solver 文件中也不能伪装成不影响物理的数值细节。迭代容差、增量缩步规则、线性解法、dtype 和实现版本属于 solver 摘要。具体的 J 合法域检查不允许取绝对值或裁剪修复。

`evaluation_id` 每次调用新建，记录 geometry、task、solver 的完整内容摘要，以及代码版本、依赖版本、调用起止时间。固定二者之后，才可把正式 `evaluate(geometry_file, task_config, solver_config)` 包装成输入几何的简化入口。每个候选均从任务规定参考状态开始。

```json
{
  "schema_version": "hf-result-0.1-draft",
  "evaluation_id": null,
  "geometry_id": null,
  "task_id": null,
  "solver_id": null,
  "readability": {"status": "pending"},
  "qualification": {"status": "pending", "measurements": {}, "criteria": {}},
  "numerics": {"status": "not_run", "target_reached": false, "reached_input_mm": null,
    "failure_stage": null, "reason": null},
  "functionality": {"status": "not_evaluated"},
  "metrics_at_target": null,
  "path_file": null,
  "units": {"length":"mm", "force":"N", "stress":"MPa", "energy":"N mm"}
}
```

## 6. 资格和结果有效性

文件可读、几何任务资格、数值成功、功能达标分别判定。缺少体积容差、最小特征尺寸或应变限值时，输出测量值和 pending。源 LF `valid` 不能直接升级为 HF 合格。诊断档案允许不合格结构存在。

主体以共享边四邻接检查传力连通；另测角点连接和端口/夹具附着。工件是独立物体，不要求与机构在初态连通。细颈诊断需说明物理尺度和方法；四邻接通过不等于制造合格。

每个收敛步保存输入位移、输出位移、广义输入力、输出负载/分侧工件力、最小 J、残差分子与归一化尺度、约束误差、迭代数、实际增量、失败重试信息及必要位移场。失败时保留最后收敛点作为路径记录，目标指标为 null 并说明原因；不得用该点代替目标性能或填零。

夹持器分别定义单爪力、两爪向内力之和与有符号净力；半模型倍率按指标定义。第三介质没有现成接触乘子，工件合力必须以残差/虚功一致方法恢复并验证。首版不承诺压力场精度。

能量分别积分实体与第三介质；正则化仅在有明确定义时报告对应量，不将非保守弱式构造为虚假的总势能守恒证据。排序和评分只作为有效原始结果的派生物。

## 7. 可搬迁与断开 LF 验收

所有运行用引用须在包内、为相对路径且存在。历史绝对路径可作 provenance 字符串，读取器绝不访问它。检查数组和文件哈希、端口面积方向、引用闭包与 schema 状态。

HF-1 验收将只打包 HF 仓库和两个样本到新的临时目录，创建独立虚拟环境并从 wheel 安装，不携带 `hf0_audit`、LF 副本或导出脚本；从仓库外 cwd 调用。清除 `PYTHONPATH` 等入口，关闭 user site，记录 sys.path、已安装包和输入访问清单，检查无 dmftd/MMA/AuTO 来源。完成读取、校验、独立小型线性分析和输出。这支持“无 LF 运行依赖”；完整 TMC 评价需在 HF-5 再做端到端复验。
