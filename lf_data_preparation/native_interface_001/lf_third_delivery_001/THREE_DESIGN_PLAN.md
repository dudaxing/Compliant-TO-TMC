# 三个 LF 夹持器的保存结果对照计划

**交付执行后更新：L-TUSE1 唯一启动 3422d4 exit0，helper／outer PASS，25行与六媒体交付已完成。** 实际结果见 [RESULTS.md](RESULTS.md) 和 [带图人工检查页](run_001/consumer/REVIEW.md)。下文“本文写入时／候选／待实际PASS”描述准备时点，现由本次真实收据关闭；三设计对照本身仍未执行。

2026-10-15（Asia/Seoul）。本文只规划后续对照，不是对照执行记录。所有路径相对于恢复后的仓库根目录；不依赖原计算机的绝对开发路径。

## 整体目标与目前已有功能

整体目标是让独立 HF 接收 LF 几何，在明确的材料、工件、边界和输入路径下，计算有限变形／Third Medium Contact 响应，保存输入反力、输出位移、固定工件作用、收敛记录及可恢复状态，供外部研究层使用。研究层负责比较和研究决策；HF 不承担 LF 优化。固定工件上的弱式合力与连续接触压力、自由工件稳定夹持是不同功能，当前结果不提供后两项资格。

第三个 wave 夹持器已经完成输入与未变形兼容性检查，以及一次从零开始的原 25 目标 `0→1.20→0 mm` 路径。原纯 viewer 已观察全部 25 个保存态，产生实际变形／力图、GIF 和分区几何观测；收敛观察器已保存原迭代记录及收敛图。峰值 loading 1.20 mm（accepted/original 13）与首次卸载 1.15 mm（14）的独立 HP80／120 共四次参考已经通过原十五门。该参考只覆盖两个保存态及原 PORT 方向。

本轮 L-TUSE1 的目标是把第三例的完整生产路径、两态参考和六份既有媒体关联到公共响应与轻索引，再由纯普通 JSON 消费入口输出 25 行状态表和人工检查页。本文件写入时，候选已经准备，**本轮关联和消费尚未执行，实际状态待本轮 helper／outer 回执确认**。不能把本文或准备好的路径称为已关联成功。

先交付再比较，是为了让研究层通过一个可恢复入口取得数值、身份、参考覆盖和媒体，避免临时从开发目录挑选文件，也避免把“生产路径完成”与“全路径独立参考通过”混在一起。关联和消费不需要重新求解、重算力或增加默认源码功能。

## 本轮交付入口与成功前置条件

阶段根为 `lf_data_preparation/native_interface_001/lf_third_delivery_001/`，计划产物为：

- `run_001/linked_response.json`：一次公共摘要关联，保留原生产响应的物理值与生产资格。
- `run_001/light_index.json`：仓库相对路径、文件身份、原参考范围和六份既有媒体链接。
- `run_001/consumer/states_table.json`、`run_001/consumer/REVIEW.md`：完整 25 行原值和人工检查页。
- `run_001/delivery_summary.json`、`run_001/execution_receipt.json`：实际交付范围、调用计数、结果与封存状态。

这些是已约定的输出位置，不是已存在或已通过的声明。后续比较以实际 PASS、完整封存及原输入身份不变为前置条件；若本轮失败，应依据真实 partial 定位，不跳过交付检查来开展比较。

当前默认 `hf_repo/src/hf_eval/native_response.py` 的 `_reference` 动态匹配选定态索引，无需把 `[13,14]` 写成新的默认特例。预期返回 `matched_partial`、`selected_reference_pass=true`、`matched_state_indices=[13,14]`，同时保持 `covers_all_accepted_states`、`accepted_reference_pass` 和 `full_path_reference_pass` 为 false。原参考的 `qualification` 由接口传为 `qualification_scope`；原 `reference_scope` 及参考摘要文件还应在轻索引中保留，不能通过伪造 continuation 来表达。

消费算法沿用 `lf_saved_consumer_001/example/consume_saved_lf.py` 的 `consume`：读取 index、linked response、result 三份普通 JSON，按 `enumerate(result.states)` 保留接受行号、原目标号、路段、位移、状态 SHA、原力／位移和三分量工件力。只有 13／14 行标记已有匹配参考。旧阶段包装中的 `[13,16]`／五份媒体限制不属于默认算法；新包装核本例实际范围。研究层副本的“五份既有媒体”标题可改为“既有媒体”，不修改 HF 默认数学实现。

## 下一步比较的最小普通输入

下一比较拟输出 **75 行原值（每例 25 行）和 25 组三方对应关系**。优先继承已经核对的普通结果，不重开原 NPZ、科学 gzip、CSV 或重新运行 HF。

| 输入 | 确切仓库相对路径 | 作用 |
| --- | --- | --- |
| 既有两设计对照 | `lf_data_preparation/native_interface_001/lf_saved_comparison_001/run_001/comparison.json` | `designs[0]` 为 Historical M，`designs[1]` 为 LF native fine；每例已有 25 行原 state、observation、source、references、aliases 和物理合同 |
| 第三例消费表 | `lf_data_preparation/native_interface_001/lf_third_delivery_001/run_001/consumer/states_table.json` | 待本轮实际 PASS；第三例标准消费入口及参考行标记 |
| 第三例轻索引／关联响应 | 同阶段 `run_001/light_index.json`、`run_001/linked_response.json` | 待实际 PASS；绑定消费表来源、参考范围及既有媒体 |
| 第三例原生产结果 | `lf_data_preparation/native_interface_001/lf_third_cycle_001/run_001/lf_third_cycle/result.json` | 25 行原 `states`、目标路径、settings、源身份及原资格；消费表与其逐行对应 |
| 第三例分区／几何观测 | `lf_data_preparation/native_interface_001/lf_third_cycle_001/run_001/view/lf_third_cycle/summary.json` | 25 行 `rows` 中的有限射线、尖端位置与距离、实体／自由介质 J、实体 Green 主应变和力分量 |
| 第三例两态参考 | `lf_data_preparation/native_interface_001/lf_third_reference_001/run_001/reference/summary.json` | 原 accepted/original 13／14、两态四次 HP、原十五门及范围；不读取其科学归档 |

最小数值集合是旧 `comparison.json` 加第三例原 result、viewer summary 和 reference summary；本轮三份交付 JSON 提供标准入口和身份验证。若消费表已经包含某字段，不应为得到相同值而另增科学读取。普通输入的实际 SHA 应从本轮封存记录和旧交付记录绑定，不能用本文路径代替身份核对。

既有两设计对照已经保存以下来源映射；下一比较应原样继承其记录与原浮点值，而非重新解释其历史：

| 设计／全局原目标 | 主来源 | 保存态位置说明 |
| --- | --- | --- |
| M：0–13 | `regularization_sensitivity_001/run_001/alpha_half/result.json` | 原 loading 前缀，父路径曾因时间限失败；保留原失败与源码 epoch |
| M：14 | `saved_continuation_001/run_001/resumed_alpha_half/result.json` | child accepted 1；child 0 是峰值锚点 alias |
| M：15 | `saved_extension_002/run_001/extended_alpha_half/result.json` | child accepted 1 |
| M：16 | `saved_extension_003/run_001/unloaded_alpha_half/result.json` | child accepted 1 |
| M：17–24 | `saved_extension_004/run_001/unloaded_alpha_half/result.json` | child accepted 1–8 |
| LF native fine：0–24 | `lf_forward_001/run_001/lf_fine_forward/result.json` | 同一次零起点完整路径；既有消费表在 `lf_saved_consumer_001/run_001/states_table.json` |
| 第三例 wave：0–24 | `lf_third_cycle_001/run_001/lf_third_cycle/result.json` | 同一次零起点完整路径；本轮准备标准交付入口 |

上表的简写阶段路径都位于 `lf_data_preparation/native_interface_001/` 下。M 的原 viewer 来源分别为 alpha partial、RESUME、EXTEND2、UNLOAD1、UNLOAD2；其实际路径和文件 SHA 已在旧 `comparison.json` 的逐行 `source.viewer`／`source_aliases` 中保留。不能把 M 称为与另两例一样的一次从零完整生产，也不能抹去早期源码 epoch。

## 配对、参考覆盖与同定义检查

三方匹配键为 **`(original_target_index, leg, d_mm)`**，按原目标顺序生成 25 组；接受行索引、原目标号和源结果／state SHA 各自保留。不能只按位移去重，否则会把加载、卸载和原点／回零合并。原目标 0.85／0.95 mm 没有原卸载配对；如另做加载／卸载描述，只允许精确同位移的原目标配对，不插值、不用邻态替代。

参考覆盖必须按各例、各主来源分别表达：

- **Historical M**：主来源参考覆盖全局 14／15／18／19。全局 13 的参考属于 M-RESUME1 child 0 锚点 alias，旧记录明确 `applies_to_primary_source=false`；不能把它授予 ALPHA 父源的峰值态。保留 alias 及其原参考说明。
- **LF native fine**：主来源只有 13／16 匹配已有两态参考。
- **第三例 wave**：本次已有参考为 13／14；关联通过后才由本轮消费表标记匹配。

不能把三例的相同行号统一涂成已参考，也不能把两态参考解释为整条 25 态路径或全部切线列通过。

绘图前只用普通声明核对以下同定义条件；不一致时应说明差异或停止比较，不自动改数据取得一致：

1. 共同任务的材料与厚度、plane strain、gamma／alpha／正则化长度、固定工件、域与网格、输入／输出控制、原目标序列及单位。预期为 E=1 MPa、nu=0.3、厚 20 mm、gamma=1e-6、alpha=5e-7、Lr=80 mm，h=0.5 mm、84×40 mm 下半域，中心 (71,40) mm／边长 18 mm 固定方形工件，平均输入 +x、输出 +y、k_out=0。任务 SHA 因几何或路径历史不同而不同，不能要求全部原 task SHA 相等。
2. 支撑、对称和端口的参考几何定义、方向、五节点权重及实际附件选择规则。不同拓扑可有不同实体节点、fixed/free 数量；不能以计数不同直接判为任务不一致。
3. `R_input`／`R_input_N` 是半模型输入反力；`q_out` 是加权端口位移。下半固定工件的 material／regularization（Hu）／total 有符号 Fx、Fy 保留原分解及作用方向；不能把双侧 `2|lower Fy|` 幅值和称为完整工件净力或压力。
4. 几何身份来自各自普通 source geometry 声明及已有兼容性证据。下一阶段不重读掩码、不重新阈值化或修改几何；M 的分段源身份和早期源码 epoch 一并保存。
5. 原生产停止规则、选项及 settings 的物理／数值部分明确列出；各窗口的 clock 不作为材料差异。共同定义成立也不代表不同源码历史已由一个新的全路径参考消除。

## 分区观测与可视化计划

原值来源和物理含义保持分离：

| 显示量 | 来源与含义 |
| --- | --- |
| 输入反力、输出位移、三分量工件力 | 原 state／消费表；M、LF2 的旧 comparison 保留原 state 与 viewer 观察，跨表达末位差不增设精确相等门 |
| `bottom_first_ray_mm`、`left_first_ray_mm` | 原 viewer 的有限工件面沿外法线首次命中；`null` 是无命中，不是零。若 overlap／roundoff 标志不允许分离解释，不能仍称真实间隙 |
| `tip_to_*_mm` 与 tip 坐标 | 特定参考 (80,30) mm 节点的实际保存坐标及到有限面线段的无符号距离，不等于整体表面距离 |
| `node_window_clearance_mm` | 原结果中的参考节点窗口极值诊断；不与 finite-ray 或尖端距离互换 |
| `global_minimum_J`／消费表 `minimum_J` | 原保存全局最小值；不替代实体与自由介质分区值 |
| `solid_min_J`、`medium_min_J` | viewer 原分区观测；free medium 排除固定工件 overlay |
| `solid_Green_principal_min/max` | 原保存 F 派生的实体平面内 Green 主应变范围；不是新 HP 应变资格 |
| `medium_max_abs_Hu_per_mm` | 原分区最大绝对分量；不能与场图中的 Hu Frobenius 范数混作同一个量 |

预计生成两类标量图，具体布局在后续范围明确后冻结：

- **响应图**：三例输入反力、输出位移及下半工件有符号材料／Hu／总力，明确加载和卸载顺序；参考覆盖逐例标注。
- **几何与数值状态图**：原 finite-ray、实体／自由介质最小 J、实体 Green 主应变及必要的原收敛摘要。近零量保留精确零和 `null`，若使用对数或 symlog，写明显示规则，不增加科学 floor 或新验收门。

25 个原目标按原顺序显示；若横轴用位移，应使加载／卸载可区分。曲线连线只表示保存态顺序，不产生新机械状态。75 行 JSON 保留原浮点值，人工表允许明确的显示舍入。不计算“综合性能分数”或无定义的优劣排名，不把路径差当作已测耗散能。

人工页同时并列实际变形来源，使读者能核对结构和作用位置。LF2、wave 各有完整 25 态 GIF；M 必须按历史分段引用已有 GIF，峰值全局 13 来自 ALPHA 段，最终零位移全局 24 来自 UNLOAD2 child 8。不能把 M 子段的局部最大位移误作全局 1.20 mm 峰值。显示使用原 x1 变形及镜像说明，不新增 DOF 或声称镜像是第二次求解。每份既有力箭头媒体有自己的原尺度；未经共同尺度核对，箭头长度不能跨图直接比较力大小。

第三例的六份既有媒体分别是：

- `lf_third_cycle_001/run_001/view/comparison.png`
- `lf_third_cycle_001/run_001/view/distances_forces.png`
- `lf_third_cycle_001/run_001/view/peak_fields.png`
- `lf_third_cycle_001/run_001/view/lf_third_cycle/actual_states.gif`
- `lf_third_cycle_001/run_001/convergence/convergence.png`
- `lf_third_reference_001/run_001/reference/reference_observations.png`

这些简写均位于 `lf_data_preparation/native_interface_001/` 下。原 viewer 的 `reference_available=false` 表示其制作时没有传入参考，保留该历史事实；新轻索引另外关联后来完成的参考，不改原 manifest 或重绘。并列页可引用既有媒体；若后续需要抽帧或导出合成图，应把媒体读取／解码和像素核对明确计入该后续阶段，不混入普通 JSON 比较的零媒体读取说明。

## 后续执行边界与结果记录

本轮先完成保存交付，记录实际调用、封存、外部恢复和资格。三设计比较目前仅有此计划，未执行。后续根据本轮实际交付结果确定一次比较的输入身份、资源、输出与检查范围；计划新增的标量图不使用本轮关联授权静默执行。

比较应记录整体目标、本步为何必要、实际读取的普通文件、75 行与 25 组的对应规则、同定义核对结果、来源差异、图义和可复核路径。成功仅表示保存结果可一致读取和描述；不升级完整路径独立参考、压力、有效夹持、自由工件释放、稳定性或 HF5 资格。若发现来源／定义不符，保留事实并定位最小问题，不插值补点、修改物理或重算来隐藏差异。
