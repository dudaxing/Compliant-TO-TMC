# HF-0：上传 LF 快照核查

本报告仅依据用户上传的 `Diversity-TO-Compliant-O-main (6).zip`。没有把相邻 LF 工作树、旧聊天结论或旧里程碑授权作为当前证据。原 ZIP 未修改；审计只读取其解压副本，未导入 `dmftd`、未执行优化、未运行 LF 测试，也未生成 HF 生产导出器。

审计工作副本在 `hf0_audit/lf/snapshot/Diversity-TO-Compliant-O-main/`，不是未来 `hf_repo` 的组成部分。所有下文源码位置均相对此上传快照根目录。

## 1. 可复用资产及实测数量

ZIP 有 **719 个条目、534 个文件**，文件解压合计 **40,707,870 bytes**。全文件路径、大小、SHA-256 见 `hf0_audit/lf/archive_inventory.json`；全部 **73 个 NPZ + 20 个 NPY** 已使用 `allow_pickle=False` 读取，字段、形状、类型、数组哈希见 `array_inventory.json`。这证明普通数组可读，不证明力学正确。

| 档案 | 反向器 | 夹持器 | 数组及记录语义 |
| --- | ---: | ---: | --- |
| spring_sweep，80×40 | 25 | 25 | `rho_physical_final` 和 `raw_design_final` 为 `[5,5,40,80]`；前两维分别对应 `k_hat_in`、`k_hat_out`；另有三个分区 mask |
| refine，160×80 | 9 | 9 | 每个记录有 `rho__<run>`、`raw__<run>`，各 `[80,160]`；18 个字段/文件 |
| generation_axes，80×40 | 105 | 70 | 每个记录 `rho__<id>`、`clean__<id>` 各 `[40,80]`；有 15+10 个 baseline 复读记录 |
| geometry_extraction_v1 | 26 | 18 | 共 44 个 `geometry.npz`、44 个 `outline.json`，包括不合格诊断记录 |
| handoff_v2 新增实体文件 | 8 | 6 | 共 14 个只有 `clean` 的 `geometry.npz` 及对应轮廓 |
| handoff_v1 联集 | 10 | 6 | 共 16 个候选，均引用 geometry_extraction_v1 |
| handoff_v2 联集 | 18 | 12 | 共 30 个候选：保留旧 16 个引用，新增 14 个 |

六份 `final_densities.npz` 合计 **243 条储存记录**：68 条 sweep/refine +175 条 axes。按「类型、形状、C-order 数组字节」比较，得到 **218 组密度身份**：193 组只有一条记录，25 组各含一个 sweep 与其 axes baseline 复读。源码 `scripts/run_generation_axes.py:92–96` 确认 baseline 直接读取既有密度；不能把 243 称为独立优化运行数。`generation_records.json` 保留每条记录的来源、状态、成本字段、源码提交、环境和父索引；`density_identity_groups.json` 仅建立关联，不抹去复读成本或不同来源。

六份文件之外另有三类终态证据，已单列到 `supplementary_terminal_records.json`，没有混入上表计数：

- `research/gripper_80x40_v1/final_arrays.npz`：独立夹持器试点记录，有密度、raw design、位移、梯度及分区。
- `reference/auto_inverter_40x20/final/reference.npz`：AuTO 参考优化终态，另有 `xphys.npy` 等重复保存形式。它使用另一参考轮廓、尺寸/单位语境及边界，不能自动冒充本项目的 80×40 mm 机构。
- `tests/data/M4_battery_v2_m3_final_160_p3_160x80_arrays_subset.npz`：M4 夹具内有 `measurement_rho_physical`，当前 ZIP 没有相应完整旧里程碑终态目录，来源证据强度应单列。

`research/diversity_selection_v1/selected_designs.npz` 另存默认入选的 12 个 clean/gray 复本，统一为 `[80,160]`。粗网格重复到共同网格属于既有派生表示，不是新增优化记录，也不能反过来覆盖原始几何。完整候选档案保留，不因本次选两个样本而裁掉其他资产。

## 2. 路径与版本闭合

针对所有候选 `density_source`、44 个提取记录的 geometry/outline/summary、handoff_v1 全部 16 个候选、handoff_v2 全部 30 个候选及 14 个新候选到 axes 的 rho/clean 映射，检查了 **340 条明确数据引用，零缺失**。NPZ 键和索引一并解析，结果见 `data_reference_trace.json`。14 份 handoff_v2 新 clean 与 axes 同 ID clean 均逐元素相同。

handoff_v2 不是一个只复制它本目录就自包含的数据集。该 JSON 的 `paths` 明示：

- `designs/...` 相对 `research/handoff_v2/`。
- 其余 `research/...` 相对原仓库根目录。
- 旧 16 个候选仍需要 `research/geometry_extraction_v1/`；原密度和物理 case metadata 继续追到 sweep/refine 的汇总文件。

实际有两种几何与轮廓序列化格式：

| 资产来源 | NPZ 字段 | 轮廓 schema | 物理元信息 |
| --- | --- | --- | --- |
| geometry_extraction_v1，44 份 | `solid`, `clean`, `opened_r1`, `opened_r2`, `opened_r3`，均 bool | `dmftd.outline_loops.v1` | units/domain/element/symmetry/convention 存于 outline；source 密度在 summary；厚度/端口需父记录 |
| handoff_v2 新增，14 份 | `clean`，bool | `dmftd.outline.v1` | mesh/element/symmetry；未显式写 units/domain/convention，须由 `build_handoff_set.py:174–179` 与上游来源解释 |

权威几何建议选原 native-grid 的 `clean`。`solid` 是阈值化前景，`opened_r*` 只是细颈诊断变换，不能自动作为 HF 分析几何。清理算法源见 `src/dmftd/geometry_extraction.py:35–95,216–243`：阈值后强制 passive mask，保留同时接触物理支座、输入和输出的 **8 邻接**分量；未保留的材料记作 islands。

轮廓在源码 `geometry_extraction.py:165–213` 中按单元边生成，实体在行进方向左侧，外环逆时针、孔洞顺时针，角点接触分环。**首顶点不在尾部重复**：209–212 行回到起点就结束，最后一边隐含连接末点与首点。按照此真实编码独立重算后，58 份轮廓的所有边均组成单元边闭环，带符号面积和均等于对应 clean 面积；其中 8 份空 clean 对应空环集合。不得误把未重复首点解释为轮廓开口。

诊断档案中，58 份 clean 文件有 **8 份为空**，另 **1 份非空但四邻接传力路径断开**；其余 49 份四邻接为一个分量。这些记录可读、可存档，不等于正式几何合格。逐件测量见 `geometry_asset_measurements.json`。

这份非空断路结构是 **`inverter__p2__kin_1e-02__kout_1e+00`**，实际包含在 **handoff_v2 的 18 个反向器中**，文件位于 `research/handoff_v2/designs/inverter__p2__kin_1e-02__kout_1e+00/geometry.npz`。本轮独立测得四邻接有 **2 个分量**，支座—输入—输出不能组成共享边连通传力路径；八邻接有 **1 个分量**。因此 handoff_v2 的 30 个入选记录不能统称为 30 个正式合格候选。这份原资产保留在诊断档案，不自动补桥或删掉，也不作为本轮两个交接演示样本之一。

## 3. 缺失证据与非运行依赖

`availability_gaps.json` 区分当前数据闭合与旧路径记录：

- 上述 340 条候选交接数据引用无缺项；本轮两例读数不需要 LF 源码执行。
- axes 的 90 个反向器、60 个夹持器非 baseline 记录都有汇总 rho/clean 与 index 行，但 ZIP 没有两组 `runs/` 目录。因此缺少各自原始逐运行 `summary/history/arrays.npz/raw design`，不能从汇总字段编造完整迭代历史。`run_generation_axes.py:85–128` 说明这些逐运行文件原先产生于何处。
- 作为附带的 JSON 字面路径扫描，有 920 次 `milestones/...`、15 次 `tmp/...`、1 次旧 `tests/test_m2_review_gate.py` 引用在此快照内不存在；另 38 次历史绝对路径。这里是**引用出现次数**，不是缺失候选数，也不是 936 项 HF 运行依赖。旧归档目录、原输出目录和旧解释器位置只作来源记录；不去恢复整套旧执行链。完整字面清单在 `json_path_references.json`，没有将这些旧字段当成新授权。
- ZIP 的 `.gitmodules:1–3` 注册 `third_party/AuTO`，实际目录内无文件。完整上游 notebook 的重新生成没有当前离线源码支持。但 `third_party/AuTO_frozen/models/utilfuncs.py` 已随包保存，实际 SHA-256 为 `0aa90e8479e545ffab7e5022ac30433fbd64e2207b4fe57634444ff2e36b69c2`，与 PROVENANCE 记录相符；其 GPL-3.0 LICENSE 随附。LF 项目根目录没有 LICENSE。HF 不接入此 MMA/AuTO 代码；公开发布的许可决定需另行核对，不能由论文开放获取替代。

## 4. 两个真实优化样本的映射

选择两个 handoff_v2 已收录、历史 `thin_necks=false` 的粗网格结构作为 HF-1 数据交接演示。这是**读取旧优化终态及旧二值几何**，本轮没有重新优化。二者原优化都完成 200 次更新并以 `max_iterations` 停止，`source_profile.converged=false`；因此应称「真实优化得到的预算终态」，不能声称优化已满足收敛判据。

| 测量或来源字段 | 反向器 | 夹持器 |
| --- | --- | --- |
| 原 ID | `inverter__sweep__kin_1e+01__kout_1e-01` | `gripper__sweep__kin_1e+01__kout_1e+00` |
| geometry 路径前缀 | `research/geometry_extraction_v1/candidates/<ID>/` | 同左 |
| 原密度文件 | `research/spring_sweep_inverter_80x40_v1/final_densities.npz` | `research/spring_sweep_gripper_80x40_v1/final_densities.npz` |
| 密度键及索引 | `rho_physical_final[4,2]` | `rho_physical_final[4,3]` |
| 原生数组 | bool clean `[40,80]` | bool clean `[40,80]` |
| 设计/被动实体/被动空 cells | 3200 / 0 / 0 | 2960 / 40 / 200 |
| clean 实体 cells；半模型面积 | 1128；1128 mm² | 1086；1086 mm² |
| 半模型实体体积，t=20 mm | 22560 mm³ | 21720 mm³ |
| 设计区实体占比 | **0.352500** | **1046/2960 = 0.3533783784** |
| 全包络实体占比 | 0.352500 | 0.339375 |
| 原连续密度设计区占比 | 0.3499990176 | 0.3499995377 |
| 新独立四邻接 / 八邻接分量数 | 1 / 1 | 1 / 1 |
| 新独立局部纯角点 2×2 模式数 | 0 | 0 |
| 支座区域 9 节点中接触实体 | 4，y=5,6,7,8 mm | 3，y=6,7,8 mm |
| 输入 / 输出节点接触实体 | 各 3/3 | 各 3/3 |
| passive mask 保持 | 是 | 是 |
| 此次几何修改 | 无；历史 solid=clean | 无；历史 solid=clean |

两例的二值设计占比均超过来源连续密度的数值上限 0.35。HF 共同约束未冻结，故资格为 `pending`、`formal_HF_eligible=null`。这不是自动降低材料上限的理由，也不应补杆/变薄来凑合格。本次有四邻接、无局部角点模式、历史开运算未断，仅能支持这些有限几何测量，不能支持制造、细颈强度、非线性性能已验证的结论。支座不是 9 个节点都保有实体；HF-1 应明确传力实体附着区域，并保持几何原样。

### 坐标、厚度与端口

源 `contracts/benchmark_v1.1.yaml:18–24,37–52`、`geometry.py:3–5,34–38,85–112` 和两组 sweep `index.json.case_record` 共同明确：

- 长度 mm，域 x∈[0,80]、y∈[0,40]，厚度 20 mm，是下半模型，镜面 y=40 mm。数组 `[iy,ix]` 行向 +y、列向 +x，row 0 是物理底边；C-order x-fast。80×40 源网格单元尺寸为 1×1 mm，单元中心 `(ix+0.5, iy+0.5)`。节点物理坐标 `(ix,iy)` mm，辅助节点号 `iy*(nx+1)+ix`，DOF 顺序 `[ux,uy]`。
- 支座物理区域是 x=0、y∈[0,8] mm，ux=uy=0。不是 C-shape 整边固定。
- 两例输入物理端口 x=0、y∈[38,40] mm，方向 `[+1,0]`；反向器输出 x=80、y∈[38,40]，方向 `[-1,0]`；夹持器输出 x=80、y∈[28,30]，方向 `[0,+1]`，向镜面运动为闭合。
- 三节点权重均 `[0.25,0.5,0.25]`，来自归一化梯形分担长度。源 `fem/port.py:111–137,178–206` 实现 `f=F b`、`q=bᵀu`、`K_s=k bbᵀ`；这不是逐节点独立弹簧，也不是刚性等位移夹具。
- 夹持器被动实体 jaw 是 x∈[60,80]、y∈[28,30] mm；被动空区是 x∈[60,80]、y∈[30,40] mm。数组为 `passive_solid[28:30,60:80]` 和 `passive_void[30:40,60:80]`，两类都不进入设计区分母。该 jaw 来自旧图示解释并已被旧 LF 采用，不能把它当作本轮用户已冻结的圆柱工件尺寸。
- 反向器 y=40 全边 uy=0。夹持器 **实际 sweep 使用 `full_midline`**，也对 y=40 的全部 81 个节点约束 uy；这与 benchmark 标注的 x≤60 `contract_segment` 不同。`mechanism_case.py:220–241` 明确两种策略，且 y=30 的夹爪面不被钉住。HF 必须独立决定第三介质在 x60..80 顶边的对称/边界处理，不能无记录地继承或删除这部分约束。
- 来源力和弹簧是每半模型总量。源 `benchmark_v1.1.yaml:66–72` 规定对称全模型力/弹簧倍率 2，位移不倍增。HF 工件分侧力定义还需独立建立。

### 来源参数不是 HF 任务

两个 sweep 的 index 记录源码提交 `31e99af7fa4dbfcd6f9066b6f7ccdb26cc502fd3`，Python 3.11.13 / NumPy 1.26.4 / SciPy 1.12.0 / JAX 0.4.30、x64 开、单线程 OpenBLAS、WSL2 Linux。后续 geometry extraction 和 handoff 各有自己的提交与环境，均分别保留在 JSON，不以 handoff 提交覆盖优化提交。当前快照没有 `.git` 对象，无法把这些历史提交字串当作本次源码 checkout 已验证 commit。

两例为 uniform 初始化、随机种子不适用（draft 记 `null` 加原因），p=3、beta=4、eta=.5、滤波半径3 mm、E_scale=1 MPa、Emin=.001 MPa、ν=.3、plane strain、t=20 mm、输入总力1 N/半模型。反向器源 k_in=32.6626692886、k_out=.326626692886 N/mm；夹持器源 k_in=14.6042878603、k_out=1.46042878603 N/mm。这些只保存在 `generation_record.source_profile`。

原 LF 输入下末态平均输出分别为 .01873739416 mm、.01173049431 mm，源计时字段约39.40 s、37.95 s；它们不是本轮 HF 结果、不是纯优化核计时，也不能跨候选不同弹簧直接排名。

## 5. 可审阅的交付与 HF-1 缺项

机器可读草案在：

- `hf0_audit/lf/mapping_inverter.draft.json`
- `hf0_audit/lf/mapping_gripper.draft.json`

草案拆分几何资产、生成记录、任务和评价；包含真实来源数组键、分区数组、物理坐标、端口权重、哈希、实测面积与拓扑。正式包路径仍为 `null`，另给 `proposed_package_path`；这是映射证明，**尚未制作 HF-1 的生产数据包**。草案的临时几何 ID 只用于审阅，它声明了自身算法；HF-1 应统一依照 `DATA_CONTRACT_DRAFT.md` 冻结包括实体数组、尺度、分区与布局的完整规范后重新计算，不能宣称本轮已经冻结 hash schema。

HF 材料、本构/二维假设、输入位移路径、输出负载、圆柱工件、第三介质外域、共同资格阈值和求解版本均未从 LF 偷渡，保留 `null/pending`。当前导出验证不需要先确定这些远期物理参数。

已生成实际预览 `hf0_audit/lf/two_real_geometries.png`，并人工查看：物理方向、厚度、面积、支座和端口注释可读；紫虚线表示 LF 源约束，红色支座空心节点表示该节点不接触 clean 实体。夹持器 jaw 和 gap 已分色。绘图原始数组与坐标在 `preview_raw_data.npz`，对应来源说明在 `preview_metadata.json`。图仅展示既有几何，不含变形或 HF 求解结果。

建议下一阶段仅执行 HF-1 小样本：在 HF 外制作一次性来源适配器，把两份 clean/分区/必要纯数据 metadata 连同非对称标记样本封装成相对路径数据包；在新 HF 仓库实现纯 JSON+NPZ 读取、物理语义/资格测量与断开 LF 测试。保持上传快照、完整候选索引、诊断状态和来源成本分开存档。无需为准备几何重新运行 LF 优化。
