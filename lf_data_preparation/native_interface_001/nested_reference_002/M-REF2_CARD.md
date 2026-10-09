# M-REF2：细网格完整保存路径的独立数值参考

**状态：来源、执行入口和本卡已准备；未获本卡执行授权，未执行。**

整体目标仍是独立 HF 大变形／TMC 前向评估器。本步验证已完成 M-CYCLE1 的细网格完整路径，使目前可见的力和粗细网格差异有本次独立数值证据。M-VIEW1 已显示24个真实保存状态；已有粗网格参考不会转移到新模型。本卡不重新求解加载／卸载。

## 上一窗口与唯一修正

M-REF1已按原卡一次执行并关闭：在首个依赖来源归档目录的`mkdir`处失败，HP开始／完成0/0，接受／工件参考状态0。原源码、卡、协议、输入保持原字节，没有重跑。只读诊断记录HKLM `LongPathsEnabled=0`；失败来源胶囊目录261字符、文件286字符，符合当前Windows旧路径限制的原因解释。未进行文件系统复现或修改机器设置。

本候选唯一功能修正：把11个**已有且basename互异**的依赖放入B850构造器已创建的`output/sources`平面目录，目的文件使用`Path(name).name`；原仓库相对路径和SHA继续原样保留在`self.sources`。新basename互异检查是接口归档检查，不是新增数学门。删去深目录创建；既有数学、所有状态、方向、resource和qualification范围不变，不改变全局路径政策、Python环境或包。

本机新输出前缀下来源目录169字符、最长归档来源文件202字符；全部B850／aa86科学输出路径的静态枚举与长度见`author/source_preparation.json`。这些是源代码与路径字符串核对，无科学执行或成本探测。新卡／新协议／新输出单独记录，M-REF1全部历史保持不变。

## 固定输入与行为

- 原结果：`../nested_cycle_001/run_001/fixed_square/result.json`，SHA `624ff6618e12670ea2bed9f84992a5001a7fd983fc7d2ade2415b8f1072ac5cf`。
- h=0.5 mm，84×40 mm下半模型；13440单元、13689节点、27378DOF、fixed1548/free25830。
- 原固定方形工件中心(71,40) mm、边长18 mm；648工件单元、703节点、1406DOF；背景对称重叠37DOF。E=1 MPa、ν=0.3、厚度20 mm；gamma=alpha=1e-6、Lr=80 mm。
- 原24个实际接受且原目标状态：0→1.2→0 mm；原索引、leg、状态SHA完全对应，不裁剪、不替代或插入状态。
- 全24状态各执行一次新的HP80和HP120，合计48次。每次覆盖全部单元，精确散射到全部真实DOF。独立参考保留总力、材料力、Hu正则力及其方向导数。
- 方向在获授权后的读取中由实际`b_in/max(abs(b_in))`生成，固定DOF置零；实际5节点权重[1/8,1/4,1/4,1/4,1/8]，长度27378，deltaR=0。不会沿用旧6970DOF方向或在准备阶段生成新NPZ。
- 不变数学：B850 `core_audit_mechanical.Audit.run_state`及aa86 `WorkpieceCycleAudit.workpiece_checks`；仅增加当前API保存布局的读取、身份、时钟／资源和报告薄层。源文件通过导入组合，未复制或修改公式。
- 使用已有保存张量的纯action消费器；不调用生产F/T、模型构造、平衡求解、JIT或LF；不渲染新图、不实现API附加参考。

## 原严格验收门

保留15项原GATES及原归一化／分量floor、HP80/120精度对和3000位精确散射／Inexact trap。对每个状态验证全部局部和全局三种力、三种独立方向切线、保存完整未对称CSC的组装身份和所声明方向action、KKT力与平均约束action、独立与生产残差、约束、总体平衡、固定位移、执行器／弹簧／支撑方程。工件有符号力及材料／Hu分解、去重holding分区、重叠与镜像投影由同一完整参考产生。

| 原门 | 限值 |
|---|---:|
| production_residual / independent_residual / force_evaluation | 1e-9 / 1e-8 / 1e-9 |
| average_constraint / global_force_balance / fixed_displacement_mm | 1e-10 / 1e-6 / 8e-11 mm |
| hp80_hp120 | 1e-40 |
| total_force / material_force / regularization_force | 1e-11 / 1e-9 / 1e-9 |
| total_tangent / material_tangent / regularization_tangent | 1e-10 / 1e-9 / 1e-9 |
| augmented_force_tangent / augmented_constraint_tangent | 1e-10 / 1e-10 |

完整张量组装身份不等于独立验证所有切线列；独立解析切线仅覆盖上述固定PORT方向。F/J/Hu保留原重建诊断和正J门，**没有新增独立Hu误差门**。保存应力只检查原形状／有限性；HP解析能量只归档，无候选能量资格。原443次F开始／386次完成属于已记录生产过程，不能用旧“开始=完成”条件拒绝完整细网格结果。

## 一次连续资源窗口及停止

helper **4500秒**，outer **4560秒**，采样RSS **8 GiB**。通用launcher与原已使用launcher字节相同；唯一输出`run_001/reference`，launcher唯一收据`reference_launch.json`。首个身份、原数值门、资源或运行错误立即关闭本卡；无修复重跑、重试、延期、force或第二次窗口。采用协作式时钟／停止文件和采样进程树RSS，非OS硬内存上限或强制终止；重任务完成后的checkpoint响应停止。

预算依据为已有同机native_fine完整4状态／8HP（12800单元、26082DOF）的实际helper420.870184 s、outer423.901510 s、helper采样RSS1169620992 B。按单元13440/12800和状态24/4缩放约2651.482159 s；1.5倍余量+90 s约4067.223239 s，因此本次申请4500/4560 s。旧完整h1工件24状态／48HP实际helper531.437063 s仅作补充成本背景。**以上是推断，不是本次耗时测量或完成保证**；强压缩J、Hu和归档成本可能不同，不另作成本探测。

## 输出、资格与后续

若通过，输出全部24状态的HP80/120局部／全局档案、原严格门、方向action／CSC/KKT／方程与工件分解证据、summary和lifecycle。同一结果／模型／任务身份可供后续独立API汇总绑定，但本卡不做该附加。原`response.json`保持原字节与producer false flags、reference/views not_provided历史字段。

PASS仅说明本离散模型已接受保存状态在原数值门内；不证明拒绝试探、全切线列、连续体准确性、解唯一性、接触压强、有效夹持、网格／域收敛或HF5资格。已有24帧力／变形图持续可供人工检查。本步之后再依据实际结果决定：失败先定位首项；通过才解释粗细差异，不直接重复约4小时生产路径。

## 精确启动命令（需本卡新授权后一次执行）

在正式Git仓库根目录，使用既有Python3.13.6虚拟环境：

```powershell
& 'D:/Coding/Diversity TO/Compliant-TO-TMC/.venv-handoff/Scripts/python.exe' -X utf8 -B lf_data_preparation/native_interface_001/nested_reference_002/launch_reference.py reference --protocol lf_data_preparation/native_interface_001/nested_reference_002/protocol.json
```

冻结依赖、输入及已关闭M-REF1的launch／lifecycle／summary／stdout／授权／原协议／路径诊断原字节SHA在`protocol.json`；准备动作与AST静审依据在`author/source_preparation.json`。本卡的准备状态是历史快照，授权和实际执行应另外记录。
