# HF-1 自包含数据包

入口为 `dataset_index.json`。`canonical_subset` 是本阶段两个真实机构，`synthetic_samples` 只用于读写和方向验证，`archive_index` 保存完整来源数据档案。普通运行只需要选定 `geometry_path` 对应的 JSON/NPZ，以及 `task_path` 和 `solver_path`；不需要 LF 源码、原 ZIP、审计目录或准备环境。

## 当前输入

| 项目 | 反向器 | 夹持器 |
| --- | --- | --- |
| 几何入口 | `canonical/inverter/geometry.json` | `canonical/gripper/geometry.json` |
| 原 ID | `inverter__sweep__kin_1e+01__kout_1e-01` | `gripper__sweep__kin_1e+01__kout_1e+00` |
| 原生网格 | 40 行 × 80 列；1×1 mm cells | 同左 |
| 包络与厚度 | 80×40 mm 下半模型；20 mm | 同左 |
| 实体面积 | 1128 mm² | 1086 mm² |
| 设计区实体占比 | 0.3525 | 0.3533783783783784 |
| 本阶段资格 | pending | pending |

两份 `solid` 均由原存档 `clean` 无损转成 uint8；没有再次阈值化、填孔、增厚、删岛或重新优化。设计区和被动 mask 也与原数组逐位一致。原始连续密度、raw design、原几何 NPZ、轮廓、优化末态/历史、端口/物理 case 记录、独立各阶段 provenance 保存在相邻 `provenance/`，不参与权威二值几何解析。

两例原 LF 均是 200 次更新后 `max_iterations` 停止的预算终态，源优化 `converged=false`；不能把可读取的优化终态说成优化已收敛。二值设计占比超过来源连续密度的0.35数值上限，HF研究资格阈值仍为 null。数据、求解成功和研究合格是不同状态。

## 物理接口与诊断任务

坐标采用原点左下、x向右、y向上；数组第0行在物理底边。`region_tags` 给出物理支座、对称和输入/输出段，不依赖旧节点号。端口使用参考弧长梯形权重，当前三节点为0.25、0.5、0.25。夹持器权威物理对称tag为y=40、x∈[0,60] mm（61个源网格节点）。原LF `full_midline` 的x∈[0,80] mm、81节点包含软隙上边界，完整保留在provenance，空区约束未复制成HF实体tag。任务仍只对tag内与实体相连的节点约束，第三介质的边界处理留待后续任务定义。

`tasks/` 中参数为当前明确授权的接口诊断试点：E=1 MPa、ν=0.3、平面应变、平均输入位移1e−6 mm、无输入辅助弹簧、零输出弹簧、无工件、无第三介质。它们没有继承各候选的 LF 弹簧，也不是正式非线性研究任务。`solvers/` 的2×2 Gauss仅属于实体线性Q1诊断，不是TMC积分方案。

`validation/asymmetric_marker/geometry.json` 是人工标记：5×7 cells、原点(10,20) mm、dx=2 mm、dy=3 mm，面积48 mm²。它故意不对称，含两个分量，不属于 LF 优化候选，不参加默认力学评价。

## 完整来源档案

`archive/source_members/` 保存上传快照里的普通数据与归属说明，保持原成员相对路径。没有 Python/MATLAB 源码、原 ZIP、优化器模块、symlink 或 Python对象反序列化需求。原文件中的绝对路径、旧命令和旧流程字段是**惰性来源文本**；程序只使用规范化索引中的包内相对路径。

- 六份汇总终态含243条记录；25条是baseline密度复读，共218个密度字节身份组。记录和已存成本不因去重而合并。
- `supplementary_terminal_records.json` 另外保留独立夹持器试点、AuTO参考终态及旧M4测试夹具密度三类来源。
- 全部58份 `geometry.npz` 和58份轮廓都保留，包含8份空诊断几何。handoff_v1为16例、handoff_v2为30例，二者只是旧候选子集。
- v2的 `inverter__p2__kin_1e-02__kout_1e+00` 四邻接有2分量、八邻接有1分量。它保留在来源档案，未作为当前两例正式接口样本。
- axes的150条新运行有汇总rho/clean和行级记录，但原上传包未提供逐运行raw设计及完整历史目录；不编造缺失内容。

`archive/source_index.json` 有每个保留原资产的SHA-256。`file_manifest.json` 覆盖本数据包所有文件（自身除外），路径均可随目录搬迁。

## 验证证据

`evidence/roundtrip_report.json` 来自独立直读原ZIP与通用读取器的比较：两例四类数组改变格数均为0，物理面积/厚度/坐标/端口方向/权重一致，357个来源资产逐字节一致，243条记录数组引用和92条归一化handoff文件引用解析成功，原ZIP哈希未变。

`evidence/source_import_difference.png` 展示两例来源、导入与差异；`asymmetric_marker_roundtrip.png` 检查非对称布局。原始绘图数组在 `roundtrip_plot_data.npz`。这些证明数据传递一致，不证明非线性/接触模型精度。
