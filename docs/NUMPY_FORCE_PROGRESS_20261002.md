# NumPy 完整力入口：功能进度与参考比较

2026-10-03当前：普通文件两类粗机构已接通NumPy完整力、非对称CSC切线与平均驱动平衡。新增反向器0→.001mm两态4新HP参考通过，实际output ux=−.0016019203686mm，输入R=.00016987267293N。完整目标、行动、依据、成本、效果、执行边界及下一阶段见本文[反向器最新记录](#native-inverter-mean-20261003)，[真实形变和力](../functional_views/native_inverter_mean_20261003/native_mean_path.png)、[两帧实际动画](../functional_views/native_inverter_mean_20261003/native_mean_path.gif)可人工检查。当前仍为无工件TEST；下一唯一功能阶段为反向器明确.025mm测试路径，尚未执行。

本文以下各阶段按原执行时点保留；当前状态以最新段为准，不能将历史“下一步”重新当作当前待办。

2026-10-03接续：[原完整33制造＋63保存范围、局部算术修复及实际图](#numpy-scope-20261003)已完成，修订后的独立96状态范围通过。下文2026-10-02的路径证据保留自己的执行源码身份。

2026-10-02。用户授权“优先实现新候选的 NumPy 完整力入口及参考对比，再根据结果推进组装、切线和平衡求解”。本文记录此步的目标、实现、数值效果与边界；不改写旧 F 系列的结果或授权记录。

## 整体目标及本步位置

整体目标仍是独立 HF 正向力学评估器：从普通几何、材料、支承和任务得到有单位、有方向的位移、节点内力、约束反力与任务响应，最终支持真实机构与工件的夹持任务及候选比较。HF 运行时不依赖 LF 工作目录或优化器。现有旧 TMC 已能组装材料力、正则力、总力和一致非对称 Jacobian，并求解已验证的平衡路径；这次补足的是近旋转新候选的可用入口。

旧稳定 F 候选在三个近旋转制造场中未达到原力门限。新候选此前主要通过算术原语和局部比较，完整 compiled force 的执行与候选 AD 尚未闭合。因此先用已有 NumPy `_response` 计算真实完整力向量，可以直接判断公式是否有效，并得到可用功能。Profiler 证据不再作为这一功能步骤的永久前置条件。

## 已实现什么，为什么逐步扩大

- [batch_response_split_numpy](../hf_repo/src/hf_eval/split_kernel_invariants_hu.py) 返回批量单元的材料力、Hu 正则力、总力、应力、运动学和支持域字段。它复用原公式、split 两数组及原有输入检查，没有更改物理模型或门限。
- 单位近旋转场的八个自由度首先通过三力门。随后才增加 `assemble_split_numpy`，将单元贡献按全局自由度累加，验证两个多单元矩形场的共享节点组装。
- 三个制造场通过后，进一步读取一个 C1 保存压缩末态，验证 120 单元／300 自由度的完整组装及法向力读数。这是保存状态的响应重算，没有重新求平衡。
- NumPy 入口不调用 `_runtime` 或 JIT 执行；**模块 import 仍依赖 JAX**。它不是一个已完全去除 JAX 依赖的新软件包。默认 compiled 入口及历史证据保持原来的资格。

本轮 [test_split_numpy_force.py](../hf_repo/tests/test_split_numpy_force.py) 的 **8 项测试通过**：恒等场与解析剪切力、非零 Hessian 的解析正则力、混合分支／批量系数、共享节点组装，以及四类非法状态的既有错误码。测试把 `_runtime` 和两个 compiled 批量入口替换成报错函数，检查 NumPy 功能不执行它们。

## 实际效果与原验收尺度

以下四个固定场比较使用已存 HP80／HP120 的原十进制参考，未生成新的 HP 参考。候选 binary64 值先精确转为 Decimal，再与参考相减；绘图使用该差值的浮点显示值，避免先舍入参考后相减而掩盖微小误差。新平衡态的独立审计另见后节。

总力误差为 `||f - f_HP80||₂ / S_F`；两分力使用 `max(||f_component_HP80||₂, 1e-12*S_F)`。`S_F` 保留原案例定义。原门限分别为总力 **1e-11**、材料力 **1e-9**、正则力 **1e-9**。三近旋转场 `S_F=1.25e-7 N`；C1 为 `34.8537543751 N`。这里的归一误差是无量纲数，不是力值。

| 保存场；单元／DOF | 新总力误差 | 新材料力误差 | 新正则力误差 | 三力原门 |
|---|---:|---:|---:|---|
| unit；1／8 | 2.909766e-24 | 2.392723e-17 | 7.098906e-21 | 全通过 |
| dyadic rectangle；4／18 | 7.876924e-25 | 5.631504e-17 | 6.172988e-20 | 全通过 |
| nondyadic rectangle；2／12 | 1.157022e-24 | 6.311224e-17 | 3.590023e-20 | 全通过 |
| C1 state 014；120／300 | 1.484275e-16 | 1.444996e-16 | 9.175548e-17 | 全通过 |

以下是同一参考下的保存生产基线误差，对应 summary 中 `old_stable_F_normalized_error`。不重新命名旧失败为通过，也不将 C1 已有通过说成此前整个项目没有力功能。

| 保存生产基线 | 旧总力误差 | 旧材料力误差 | 旧正则力误差 |
|---|---:|---:|---:|
| unit | 7.609767e-8 | 1.047624 | 1.011385e-19 |
| dyadic rectangle | 1.323342e-8 | 1.046521 | 3.222423e-3 |
| nondyadic rectangle | 1.973855e-8 | 1.045212 | 1.958983e-3 |
| C1 state 014 | 2.542625e-12 | 2.542636e-12 | 7.175562e-16 |

三个近旋转制造场的新材料力与总力显著改善；两个矩形场的正则力也达到原门。单位场的正则力基线本已通过。C1 基线本已通过，本轮证明该候选在这个保存压缩态也可完整组装，并非扩大到任意接触的证明。

各场均通过有限值、`J>0`、声明算术支持域及力分解舍入界检查。三个制造场输出最小 `J=1.0`；C1 最小 `J=1.89800785468e-5`。两数组仍是科学状态；显示用的 `lift + fluctuation` 舍入和不替代它们。

NumPy force／组装的记录耗时分别约 0.0382、0.0394、0.0356、0.0722 s，不包含解释器启动、模块 import、绘图或平衡求解。这是本机单次观测，不能据此宣称相对 JAX 的整体性能倍率。

## 物理解释与人工检查

长度单位 mm，力单位 N，厚度 1 mm。图中的 `f` 为离散节点内力／弱式残余力分量，不是逐节点接触压力，也不应把局部负值裁为零。无外力项的已约束自由度读数可形成约束反力；顶边法向净力使用 `-group_top @ internal_force`，即沿共同法向取完整顶边约束反力的相反数。

C1 末态驱动 0.5 mm，新候选法向读数为 **71.42390219811922 N**，HP80 为 **71.4239021981192319… N**。完整顶／底边读数含背景介质贡献，不能改名为真实 LF 机构的工件夹持力。当前没有在本轮建立真实机构／工件的新任务。

四张图均由 [plot_numpy_forces.py](../hf_repo/scripts/plot_numpy_forces.py) 读取保存数组生成，并实际查看。每张含真实比例 x1 的参考／变形网格、三类参考与候选节点力、独立放大的差值向量、全 DOF 带符号差值，以及原门限对照。箭头比例独立标注 N/mm；它是力显示尺度，不是结构变形倍率。极小力先换算成绘图 mm 再传给 quiver，避免可视化内部舍入使箭头消失。所有正归一误差保留真实 log 高度。

![单位近旋转完整力比较](../hf4_c2_stable_f_validation/numpy_force_001/unit__near_rotation/forces_and_errors.png)

![二进制矩形多单元组装](../hf4_c2_stable_f_validation/numpy_force_001/dyadic_rect__near_rotation/forces_and_errors.png)

![非二进制矩形多单元组装](../hf4_c2_stable_f_validation/numpy_force_001/nondyadic_rect__near_rotation/forces_and_errors.png)

![C1保存压缩末态组装](../hf4_c2_stable_f_validation/numpy_force_001/c1_state_014/forces_and_errors.png)

## 来源、可恢复输入与复现

本步证据根为 [numpy_force_001](../hf4_c2_stable_f_validation/numpy_force_001)。四个子目录各有 `summary.json`、`arrays.npz`、`inputs/` 和执行时 `sources/` 快照；制造场另有逐分量 `force_components.csv`。summary 保存输入与源码 SHA256、门限、尺度、参考一致性和执行范围。单位场快照是先实现单元入口时的版本，矩形和 C1 是增加组装后的版本；不要用后来的源码覆盖这些快照。

制造场输入原来自 `near_rotation_segments_001/inputs/`，现已复制五个小文件到每例 `inputs/`。C1 保存了 model、state、metadata，以及从旧 audit 抽取的 HP80／120 十进制 `reference.json`，并记录原 audit SHA。`sources/` 是审查快照，仍依赖完整 `hf_eval` 包；不能声称复制单个文件就可独立执行整个项目。

在恢复仓库根目录、使用 [hf_repo/pyproject.toml](../hf_repo/pyproject.toml) 的 Python 3.13／固定数值依赖后，可对同一输入生成新的结果目录；**输出路径必须不存在**，避免覆盖本轮证据。例如：

```powershell
python -B hf_repo/scripts/run_numpy_force_comparison.py --input hf4_c2_stable_f_validation/numpy_force_001/unit__near_rotation/inputs --output hf4_c2_stable_f_validation/numpy_force_replay/unit
python -B hf_repo/scripts/plot_numpy_forces.py --arrays hf4_c2_stable_f_validation/numpy_force_replay/unit/arrays.npz --output hf4_c2_stable_f_validation/numpy_force_replay/unit/forces_and_errors.png
python -B -m pytest hf_repo/tests/test_split_numpy_force.py -q
```

当前比较脚本使用当前 checkout 的组装入口；若需逐字复现首次单位入口版本，须对照该例 `sources/` 快照和绑定 SHA。两个矩形场只需换成对应 `inputs/`。C1 增加了瘦输入入口，可只用本次随 Git 提交的四个输入重算：

```powershell
python -B hf_repo/scripts/run_numpy_c1_force.py --saved-input hf4_c2_stable_f_validation/numpy_force_001/c1_state_014/inputs --output hf4_c2_stable_f_validation/numpy_force_replay/c1
python -B hf_repo/scripts/plot_numpy_forces.py --arrays hf4_c2_stable_f_validation/numpy_force_replay/c1/arrays.npz --output hf4_c2_stable_f_validation/numpy_force_replay/c1/forces_and_errors.png --title 'C1 saved compression end state | NumPy force vs HP80 | no new equilibrium solve'
```

上述命令是复现说明。C1 瘦入口另在仓库外目录执行了一次恢复验证：三门通过，41个输出数组全部与原保存输出逐字节相同；它没有打开原 audit。见[恢复回执](../hf4_c2_stable_f_validation/numpy_path_001/saved_input_replay_receipt.json)。仅重绘原图可直接读取本轮 `arrays.npz`，不需要任何新力学计算。

## 依据力结果推进解析切线

四场三力门通过后，新增 [split_numpy_tangent.py](../hf_repo/src/hf_eval/split_numpy_tangent.py)。固定 lift，对实际 fluctuation 的物理影子场求解析导数；保留 DD 高低位，正则导数包含 `−5 dJ exp(−5J)` 项，使用一般稀疏 LU 所需的完整非对称 Jacobian。它没有从辅助能量求 Hessian，也没有以有限差分浮点记账步骤替代机械导数。

模块提供三分量单元矩阵、总切线 CSC 组装，以及一次力计算配合可选切线的 `assemble_split_numpy(model, state, tangent=True)`。新解析切线版本为 `p26_q1_split_numpy_shadow_jacobian_v1`；它属于 NumPy 功能，不等于先前 compiled AD 已通过。

[九项解析／方向差分小测试](../hf_repo/tests/test_split_numpy_tangent.py)通过。随后 [保存切线比较](../hf_repo/scripts/run_numpy_tangent_comparison.py)对三近旋转场各两方向、C1 末态一方向，合计七方向、21 项原 HP80/120 门全部通过。每分量分母为 `max(norm(HP80 Jv),1e-10)`，包含总切线；它不是力尺度 SF。

| 保存方向范围 | 总切线最大归一误差 | 材料最大误差 | 正则最大误差 |
|---|---:|---:|---:|
| 三近旋转场，六方向 | 4.19510e-16 | 5.10954e-16 | 1.38239e-15 |
| C1 末态，一方向 | 1.02625e-16 | 8.87462e-17 | 1.30892e-16 |
| 原门限 | 1e-10 | 1e-9 | 1e-9 |

[切线结果](../hf4_c2_stable_f_validation/numpy_tangent_001/summary.json)及各例数组/矩阵保存了三项完整单元 Jacobian、方向、全局作用与 Decimal 差值。C1 全局矩阵为300×300、4672个存储项，相对不对称度约6.28106e-9，未被对称化。上述门通过后才进入新平衡求解。

## 从零求解接近与压紧

[split_affine.py](../hf_repo/src/hf_eval/split_affine.py)只增加可选 `assembler` 参数，使明确选择的 NumPy 力/切线接入已有 Newton、Armijo、步长细分与回滚控制。省略参数仍调用原 split 入口；没有复制一套求解器。[独立均匀伸长平衡测试](../hf_repo/tests/test_numpy_equilibrium.py)通过，结果与另一条标量解析方程的根一致。本轮三份小测试共18项通过。

[新路径脚本](../hf_repo/scripts/run_numpy_c1_path.py)首先由原 C1 构造器从零求解 h=0.25 mm 的接近阶段 `[0,0.125,0.21875] mm`。通过后显式继承存盘两数组，以增量参数继续到物理驱动 `[0.21875,0.25,0.28125,0.375,0.5] mm`。采用原协议：残差1e-9、约束1e-10、最多35次检查/16次回退/8层细分，最小增量1e-5 mm、每阶段300秒。没有以大位移舍入和替代 split 状态。

| 新平衡阶段 | 实际耗时 | 接受记录 | 末态法向力 [N] | 末态归一残差 | 最小 J |
|---|---:|---:|---:|---:|---:|
| 从零接近，至0.21875 mm | 4.05793 s | 3 | 0.00312083517 | 6.67286e-12 | 0.125045167 |
| 继承两数组后压紧，至0.5 mm | 30.90489 s | 13 | 71.42390219811888 | 1.38156e-12 | 1.89800785e-5 |

16条接受记录包含同一交接状态的重复记录，共15个唯一状态，覆盖七个原物理目标；闭合附近自动细分原目标步长。压紧末态全底边反力71.42390219797825 N，实体底组66.95964988997122 N，外区介质组4.46425230800703 N。绘图舍入状态的最小实体间隙约4.26539543e-6 mm；精确两数组的独立几何解释仍由审计给出。

[实际新路径图](../functional_views/numpy_c1_20261002/numpy_path.png)及 [16帧接受态动画](../functional_views/numpy_c1_20261002/numpy_path.gif)保持结构位移比例1、统一位移色标、固定反力箭头比例0.09411789 mm/N，不插值。图含实体/介质、位移、约束反力、力—位移、J与间隙，保存HP曲线只是历史路径对照，不能充当新状态的独立验收。两阶段 [approach](../hf4_c2_stable_f_validation/numpy_path_001/approach/summary.json)、[compression](../hf4_c2_stable_f_validation/numpy_path_001/compression/summary.json)保存真实数值、失败的试步诊断及来源快照。

### 新求解状态的独立 HP80/120 审计

[独立审计脚本](../hf_repo/scripts/audit_numpy_c1_path.py)用未改的两份 Decimal 参考 helper 评价本次实际保存的 lift/fluctuation，**新计算30次 HP80/120**。交接重复态按位相同，明确复用本次新参考；各阶段的 `base + parameter_s*direction` 约束仍分别检查。没有用历史HP曲线替代新态审计。

[审计结果](../hf4_c2_stable_f_validation/numpy_path_001/audit/summary.json)为 **16记录／15唯一状态、336项检查全部通过、exit0**。连续300秒上限内实际21.07815秒，进程峰值工作集230.27 MiB；新参考和输出约4.35 MB随Git保存。

| 新平衡全路径项目 | 最大归一误差／量 | 原门 |
|---|---:|---:|
| 总力 | 1.69458e-16 | 1e-11 |
| 材料力 | 1.79827e-16 | 1e-9 |
| 正则力 | 1.26318e-16 | 1e-9 |
| 总 Jv | 1.47336e-16 | 1e-10 |
| 材料 Jv | 1.35731e-16 | 1e-9 |
| 正则 Jv | 2.08331e-16 | 1e-9 |
| HP80平衡残差 | 4.35563e-10 | 1e-9 |
| HP80全局力平衡 | 1.27966e-9 | 1e-8 |
| HP80/120分量一致性 | 2.24665e-74 | 1e-40 |

所有J为正，约束误差全零。末态新HP80完整顶部法向力71.4239021981188856 N，最小J约1.8980078546778917e-5，平衡残差约1.38160e-12。96项力/Jv误差从压缩Decimal参考和候选数组独立重算后与摘要精确一致。可以认定**这条新实际路径通过数值HP验收**；本轮未重跑完整接触几何、局部单边条件或HF5任务。

两阶段作者 summary 的 `new_state_independent_HP_audited=false` 保留生成时点；后完成的审计摘要明确覆盖此状态，不能据旧作者字段否认本次后审，也不能回写作者状态伪造提前完成。查看器显式读取新审计并核对16个状态摘要后标注当前通过状态。[绘图元数据](../functional_views/numpy_c1_20261002/metadata.json)保留输入、图像与审计的来源身份。

`recovery_model.npz`及其说明补齐材料、算子、控制数组与初始 split 状态，来源与已用模型逐字段核对；这是执行后制作的恢复辅助，不伪装为执行前冻结件。额外三份直接依赖源码的SHA先核对再复制，原model/summary不回写。新态审计本身的瘦输入与完整新参考均在Git，无需依赖本机绝对路径才能阅读和复查。

## 下一步与资格范围

本步完成“完整力 → 原参考比较 → 全局组装 → 解析切线 → 七原目标的接近/压紧平衡 → 新状态独立审计”。下一步优先复用这套NumPy入口，检查原完整制造场及保存态的适用范围，再选一条细网格路径观察精度与成本。确认范围后推进 split 平均端口及真实机构/工件任务，每次以实际结果和可视化选择下一步。

旧 compiled 完整 force 执行、候选 AD、原完整制造场／保存态矩阵仍未因这四例 NumPy 结果自动解决。不能授予总体 full-matrix pass。一般局部接触、释放／再接触、split 平均端口增广控制、真实工件夹持与 HF5／批量候选评价仍按原功能进度推进，详见 [物理与功能进度](PHYSICS_AND_FUNCTION_PROGRESS_20261001.md)。

## 主干交付与异目录复读

源码和本轮约11.63 MB的结果/图像/新参考随main提交`81a13b7`并普通推送至既定origin。轻量交付清单4075文件校验通过；另一目录克隆从公开远端快进到该提交后再次通过4075文件校验，并直接用克隆中的四个瘦输入执行C1 force复读，41个数组与作者保存结果逐字节相同，三力门通过。见[公开克隆复读回执](../handoff/numpy_20261002/public_clone_verify.json)。没有新Release依赖，已有旧证据恢复方式不变；这个复读证明交付和该保存态响应可恢复，不增加物理覆盖。记录回执后的主干提交可从Git历史追溯到上述科学提交。

<a id="numpy-scope-20261003"></a>
## 2026-10-03：完整静态范围与微小应变修复

### 做什么及为什么

整体目标、HF/LF分工和物理边界继续沿用本文开头。上一步四场及新C1路径的成功还不能证明新NumPy入口在原完整输入范围内可靠。因此本步先用**原33制造场、63保存态**检查完整力与实际全局CSC切线作用，再决定更细网格功能路径。没有运行新的生产平衡路径或生成HP参考。制造场各两方向、保存态各一方向，总计96状态／129方向；同一制造场的力在两个方向记录中重复，不能计作两个物理状态。

[执行协议](../hf4_c2_stable_f_validation/numpy_scope_001/protocol.json)、[修订后的独立重测协议](../hf4_c2_stable_f_validation/numpy_scope_001/protocol_revision_002.json)及[实际执行记录](../hf4_c2_stable_f_validation/numpy_scope_001/execution_notes.json)记录范围、停止及预算。比较预算600秒、8GiB采用每例前后的协作式检查，**不是硬进程监督或连续峰值认证**；不续用旧F系列或v4窗口。

### 先排查，再修复

第一版完整比较在第26场`nondyadic_rect__tiny_strain`停止：前25场／50方向的300候选门与300参考门通过，第26场在完整力入口被`unsupported_arithmetic_range`拒绝。原[停止摘要](../hf4_c2_stable_f_validation/numpy_scope_001/results/summary.json)与[缺测图](../functional_views/numpy_scope_20261003_partial/numpy_scope_coverage.png)永久保留，不把这25场拼接入修订版。

原输入与提取输入的18数组逐字节一致，旧v2与当前原NumPy公式都能复现该拒绝；旧v2在算术测试超时后没有这个制造场的通过证据。输入支持域合法，J=1，运动学有限。[原运算诊断](../hf4_c2_stable_f_validation/numpy_scope_001/diagnosis_002/summary.json)定出了第一个拒绝：`log1p`低部比值的DD Newton校正产生孤立乘积hi约7.94696e-122、lo约−3.59501e-138，低于原2^-400支持界；这些值仍是正常binary64数，不能称为硬件下溢或物理J异常。随后沙盒证实辅助能量平方还有同类孤立项。

只修改两份算术源码：

- `compensated_invariants.py`的`log1p`低部校正沿用已有`log`的binary64超越函数边界，计算低部比值后继续检查域、保留`(-1, positive_low)`回退。它仍是有界近似算术，不宣称正确舍入的DD对数。
- `split_kernel_invariants_hu.py`的辅助能量平方先精确乘2^128，保留四个DD产品及原Horner收缩，最后乘2^-256。小分支及未选中的直接能量平方采用同一方式，避免后者内部NaN。没有删低×低项、把力或能量归零、改变支持界、物理弱式或门限。

微小应变场的两元素能量均保持非零1.7361147335e-36；从原存盘两数组独立重构的180位Decimal NeoHookean能量与结果一致。新增回归覆盖该能量、微小对数、保留的−1回退及原域拒绝，连同受影响的NumPy力、切线和解析平衡小测试，**26/26通过，9.96秒**。小测试包含一个解析平衡问题，与本次没有新生产接触路径是两个计数。诊断第一轮JSON导出曾拒绝传播的NaN，原NPZ和来源仍保留；修订导出器以字符串记录非有限诊断值，未改变计算或接受行为。

模型／算术版本字符串仍表示原合同；新旧具体字节以源码SHA区分。修订版实际kernel SHA为`4fb1314058f4ab6d8b8cb5e102cbc1fcc7960a2372b39479db5e13827f61ce4e`，ci SHA为`8115e1032e45a3178f399a904cce9b9b0cc0c9297638cc5b7a035fbe29b57081`。旧10月2日路径和旧F系列保持原执行来源，不能当作这两新字节已经跑过完整路径。

### 完整重测实际效果

修订版从头独立计算全部96状态，不复用第一版通过结果。[修订版摘要](../hf4_c2_stable_f_validation/numpy_scope_001/results_revision_002/summary.json)：**96/96状态、129/129方向、774/774候选门及774/774参考一致性门通过**，程序exit0。范围包含三个11场制造网格、21个h=0.0625保存态、19个outer_free、19个padding_2p5及4个C1末态。最大模型1920元素／4074DOF。

| 量 | 全范围最大归一化误差 | 原门 |
| --- | ---: | ---: |
| 总力 | 3.42227e-16 | 1e-11 |
| 材料力 | 3.08325e-16 | 1e-9 |
| 正则力 | 2.93818e-16 | 1e-9 |
| 总CSC Jv | 2.16057e-15 | 1e-10 |
| 材料CSC Jv | 9.72671e-16 | 1e-9 |
| 正则CSC Jv | 2.70507e-15 | 1e-9 |
| HP80/120同分母差 | 9.11573e-63 | 1e-40 |

总力除以原SF；材料／正则力除以max(对应HP80范数,1e-12 SF)；三个Jv均除以max(对应HP80 Jv范数,1e-10)。SF按原精度重算：制造120位，保存80位。C1扰动的局部参数0.0625与物理平均位移0.375不混用。

driver实测422.5942714秒；每例间及结束时采样RSS最大136,491,008 bytes（约130.17MiB），不代表例内峰值。三分量均通过实际组装CSC@原方向比较，矩阵保留非对称性。保存总矩阵、完整力、分量作用、差值、J/Hu及两个权威状态数组，足以查看实际结果。

[独立复核](../hf4_c2_stable_f_validation/numpy_scope_001/independent_review.json)重新用原HP字符串与保存数组计算774＋774门、129个SF，误差／分母／参考差的Decimal序列与摘要完全一致；129个实际总CSC@v与存盘作用逐字节一致，10来源快照与执行代码SHA相符。材料／正则矩阵未另行存盘：复核它们的保存作用与原HP门，并静态审查实际CSC组装源码，不声称重放未保存的两个矩阵。没有重新生成力、K、HP或平衡状态。

### 可见的物理效果与资格边界

[完整覆盖图](../functional_views/numpy_scope_20261003/numpy_scope_coverage.png)按96真实输入显示六种误差／原门比。[细网格保存末态图](../functional_views/numpy_scope_20261003/numpy_scope_terminal.png)显示实际x1形变、总／材料／正则完整节点内力、J及保存方向的切线门；[图元数据](../functional_views/numpy_scope_20261003/metadata.json)绑定输入、结果、来源及图像SHA。三力使用同一0.3215159804 mm/N箭头比例，箭头不是位移或接触压力。

该末态h=0.0625、d=0.5 mm，NumPy完整顶部法向读数71.42389357316964 N，最小J约1.4274265096e-5。结构压向固定上平面，介质层被压薄，材料贡献占主体。这个力包含背景介质及正则贡献，是合成任务的整边反力，不是LF真实工件夹持力。

该保存末态的**原HP平衡审计仍是not_pass**；63旧审计状态保留62 pass／1 not_pass。新静态力／Jv通过只说明响应入口准确，没有对旧状态重新求解或重新授予平衡资格，图标题同时显示两层状态。本步也不证明任意方向、任意四边形、一般接触释放重入、S／能量完整资格、compiled AD、split平均端口或HF5。

### 恢复与下一步

新源码、最小模型／状态NPZ、完整来源索引、新结果、总矩阵及图随Git。原精确参考约75.50MB、完整记录绑定约85.10MB由本机提取器恢复，不重复加入Git；完整本地输入170.08MB属于旧数据的恢复产物。415源绑定和原209保存输入绑定已验证，129方向的六向量／两个精度逐字符串回读一致。旧冻结清单固定SHA为`e8877ce1713dbb648a2d6135dff2f15a7d3618a4fcb0591321824928644e17f5`。

首次提取前Windows重复扩展前缀造成读路径错误，没有创建输出；修复幂等路径后提取exit0／43.258431秒。实际提取源码SHA`238c419a…`已单独封存；后来只给未来提取入口增加上述固定清单检查，未来源码SHA`03bce2ae…`与实际执行字节分列，原输入和摘要没有回写。

任意克隆目录恢复原参考后可重算；下列两个新输出目录必须不存在：

```text
python tools/handoff.py fetch-evidence --asset hf4-c2-development-arithmetic-20260930-v1.zip
python hf_repo/scripts/prepare_numpy_scope_inputs.py --source hf4_c2_stable_f_validation/invariants_hu_campaign_001/version_002/data --output my-scope-inputs
python hf_repo/scripts/run_numpy_scope.py --input my-scope-inputs --output my-scope-results --max-seconds 600
```

只看图和新结果无需大资产；当前绘图入口可以直接用Git中的模型／状态／结果重绘，不读HP文件。既成图保存绘制当时的源码及其实际参考SHA核对记录，未来入口的简化不回写旧图来源。

下一功能步骤选h=0.125的独立NumPy接近／压紧路径，比较实际力、形变、残差与成本，并对新接受状态独立HP核查。先保留原材料、行程、门与控制设置，用结果决定是否进入h=0.0625；随后推进split平均端口、普通LF文件适配和真实机构／工件任务。本次静态覆盖补齐了开始细网格路径所需的响应证据，项目整体仍未完成。

科学源码及新结果已随main提交`e7c302266ff4ba6e419594a0426b50c7075e34c4`普通推送。另一目录克隆从公开远端快进后，4591文件轻量校验通过；用其已恢复且固定SHA核对的原证据执行提取器，286文件的bytes／SHA、96案例索引、415源绑定与作者提取完全一致。Git瘦输入中没有新HP目录，当前绘图入口仍可重画两PNG，并与作者图逐字节相同。[公开恢复回执](../handoff/numpy_scope_20261003/public_recovery_verify.json)记录实际命令、退出和范围。没有重跑完整数值比较、生成HP或求解；这是同机异目录的交付恢复证明，不是异机力学准入。

<a id="numpy-h0125-path-20261003"></a>
## 2026-10-03后续：新 NumPy h=0.125 接近与压紧

### 目标、实施与依据

整体目标仍是独立HF正向评估：读取普通几何，在明确的材料、边界和任务下提供可靠的变形、力与响应，供外部研究层选择。前步完整静态范围通过后，本步检验最新NumPy算术是否真正支持细网格的平衡推进，而不只会准确评价给定场。沿用C1合成实体／第三介质任务，**没有重新选择工件、材料、行程或接受门**。

[本次协议](../hf4_c2_stable_f_validation/numpy_path_h0125_001/protocol.json)明确这是用户自动开发及NumPy后续平衡授权下的新阶段，旧F系列／v4窗口不复用。一次从零接近、一次逐位继承压紧、一次新HP审计；原协作式求解钟仍300秒／阶段，审计300秒，采样RSS上限8GiB。求解器原Armijo、无效试步回退与二分是阶段内既定算法；“首次失败停止”指最终阶段失败或独立审计失败，不禁止这些原试步。不是硬进程监督，测试、准备、绘图和交付另记。

未改生产弱式、NumPy力／切线源码、默认内核或依赖版本。只将[路径入口](../hf_repo/scripts/run_numpy_c1_path.py)从固定h=.25改为读取绑定metadata.h，并核对原模型全部材料、算子、控制和反力向量；执行前保存完整模型、16份直接执行依赖及输入SHA。[普通文件提取器](../hf_repo/scripts/prepare_numpy_c1_input.py)只提取原模型、协议、单位扰动方向和19条历史曲线，不运行FE或HP；历史曲线不能替代新态审计。已提取[小输入包](../hf4_c2_stable_f_validation/numpy_path_h0125_001/inputs/bindings.json)随Git，复算新路径无需原大资产或原机盘符。

[新审计入口](../hf_repo/scripts/audit_numpy_c1_path.py)现比较真实组装的全自由度CSC@方向，保存每条总矩阵，并检查新路径模型、存盘力和来源。三个切线保持非对称。新HP80/120公式helper字节不变；lift固定，方向只扰动fluctuation。末条计算后也检查钟和RSS，避免末步超预算仍被记为pass。启动前独立审阅已检查这些变化；原split控制和解析NumPy平衡测试**38/38通过，3.68秒**。

### 实际新平衡结果

h=.125：480个Q1元素、539节点、1078DOF。接近3记录，28.8930409秒；压紧17记录，266.6290935秒，两阶段各exit0。20条记录包含交接重复态，共19唯一两数组状态；覆盖全部七个物理目标0、.125、.21875、.25、.28125、.375、.5 mm。闭合附近保留实际二分接受状态，未插值或拼接旧路径。Windows进程峰值工作集分别222,826,496和233,492,480 bytes，均在上限内。

[接近摘要](../hf4_c2_stable_f_validation/numpy_path_h0125_001/approach/summary.json)、[压紧摘要](../hf4_c2_stable_f_validation/numpy_path_h0125_001/compression/summary.json)及各阶段`solver_diagnostics.json`保存接受数组、试步回退、实际残差和成本。末态d=.5 mm：顶部完整法向力**71.4238945967069 N**，底边完整反力71.42389459675027 N；最小J **1.7984753177690e-5**，生产相对残差4.51922e-12，规定约束误差为零。图示舍入的最小实体／上平面间隙4.07763954e-6 mm。

### 新状态独立参考结果

[审计](../hf4_c2_stable_f_validation/numpy_path_h0125_001/audit/summary.json)实际新计算**38次HP（19态×80／120位）**；只复用本次逐位相同的交接态参考，两阶段约束分别检查。**20记录、420/420检查通过，exit0，118.123483秒**，Windows进程峰值工作集700,080,128 bytes（约667.65MiB）。所有J为正，HP约束误差为零，原门不变。

| 量 | 新路径最大归一误差／量 | 原门 |
| --- | ---: | ---: |
| 总力／SF | 2.27497e-16 | 1e-11 |
| 材料力 | 2.24857e-16 | 1e-9 |
| 正则力 | 2.32230e-16 | 1e-9 |
| 总CSC Jv | 2.43383e-16 | 1e-10 |
| 材料CSC Jv | 1.98952e-16 | 1e-9 |
| 正则CSC Jv | 1.57050e-16 | 1e-9 |
| HP80平衡残差 | 4.35299e-10 | 1e-9 |
| HP80全局反力平衡 | 1.79135e-9 | 1e-8 |
| HP80/120同分母差 | 1.70789e-74 | 1e-40 |

分力与Jv仍用前文原下限／范数尺度。末态新HP80反力71.42389459670690754… N；这是本次实际状态的参考，不是旧19态曲线抄值。作者求解summary中的`new_state_independent_HP_audited=false`保持当时生成身份；随后审计与图明确链接通过结果，不回写作者数据。

[独立保存证据复核](../hf4_c2_stable_f_validation/numpy_path_h0125_001/independent_review.json)重新计算420个Decimal门的值、限值和判定，以及120分母／120 HP80测量字段，均与摘要精确一致；20个保存总CSC@方向与作用逐位相同，60个保存力一致。交接两数组、完整模型、32份阶段来源、11份审计来源及所有输入SHA核对通过。压紧的12个`invalid_J`试增量按原回退／二分规则处理，最大二分深度5；这是一次控制器内部的原算法，并非重新执行失败阶段。审阅器第一次额外位移权威断言误用80／120位加法，后来按冻结helper先以3000位形成两数组精确和，40个参考物理位移检查通过；该审阅失败及更正历史保留，不重算生产或HP。

### 可视化、物理效果与取舍

[20帧实际路径动画](../functional_views/numpy_c1_h0125_20261003/numpy_path.gif)、[完整末态图](../functional_views/numpy_c1_h0125_20261003/numpy_path.png)及[薄介质局部／间隙图](../functional_views/numpy_c1_h0125_20261003/numpy_medium_zoom.png)展示实体与介质、实际x1变形、固定比例反力箭头、总／材料／正则反力、J和真实接受步。局部图使用实际坐标，但纵横轴显示尺度不同以便看清薄层，明确标注；它不是位移放大后的全局结构，也不是接触压力图。查看器核对实际新审计覆盖及整个state文件SHA，既绑定两数组，也绑定force/J。

| 物理驱动mm | 新h=.125完整顶反力N | 旧h=.25完整顶反力N |
| --- | ---: | ---: |
| .125 | .000390114619 | .000392055531 |
| .25 | .200589748494 | .201197274100 |
| .375 | 30.9093318094 | 30.9093449374 |
| .5 | 71.4238945967 | 71.4239021981 |

结果显示接近阶段已有小介质反力，闭合附近力迅速增长，压紧末态总反力两级相差约7.60141e-6 N（约1.06427e-7相对值）。但最小J和间隙仍变化，粗网格路径绑定10月2日源码、本次绑定10月3日修订源码，接受步也不同；这里只报告已验收路径的观察，**不把末力接近解释成全面网格或连续体收敛**。

末态底实体节点组69.1916498624 N、外区节点组2.23224473433 N；旧粗网格分别66.9596498900和4.4642523080 N。两组按共享界面节点各分一半，随网格变化，不是材料、接触力或工件分区。整边法向力包含背景介质；材料／正则弱式分量有单独曲线，仍不是局部压力或真实夹持力。

这条路径通过的是数值平衡与完整力／方向切线审计；本轮没有重做全部接触几何、单边非拉力或释放／重入准入，不授予HF5资格。已有h=.0625旧保存末态的原平衡not_pass保持。新h=.125成本明显高于h=.25（压紧266.63 vs30.90秒），且原300秒预算余量有限。

因此下一功能步骤优先**split平均端口增广控制**，接NumPy力与实际非对称切线。先在小Q1解析任务闭环，再接原HF3规范机构的小行程；应显示端口节点各自位移及其加权平均、输入乘子、自由输出和实际形变。平均控制的内力＋弹簧−驱动力及HP尺度继承HF3任务，不能照搬C1的自由内力为零审计。h=.0625新路径留待具体精度／物理问题需要时规划，避免继续细化挤占功能实施。普通LF v2适配随后推进；真实工件、夹持力、网格政策仍需明确任务，不能自动采用HF5草案数值。

### 任意目录恢复与复算

新输入、完整状态、总矩阵、38次新HP原字符串、来源、图和协议均随main，不新增Release依赖。只阅读或重画图无需旧ZIP；在克隆根可直接运行（`my-view`必须不存在）：

```text
python hf_repo/scripts/plot_numpy_path.py --approach hf4_c2_stable_f_validation/numpy_path_h0125_001/approach --compression hf4_c2_stable_f_validation/numpy_path_h0125_001/compression --audit hf4_c2_stable_f_validation/numpy_path_h0125_001/audit/summary.json --comparison hf4_c2_stable_f_validation/numpy_path_001 --output my-view
```

后续需要新数值路径时，沿用绑定小输入及新输出目录：`run_numpy_c1_path.py --task-input …/inputs --output new-root/approach`，再传入该`last_state.npz`运行compression；`audit_numpy_c1_path.py --path new-root --task-input …/inputs --output new-root/audit --time-limit 300`重新生成参考。这是恢复方法，不是建议重复本次已完成实验或复用关闭的窗口。具体执行、独立复核及交付另存本新根和handoff记录。

本轮科学结果及约28.6MB新证据／图已普通推送main提交`6580f00cdda6a51cf95ff0daeb6ab41bcea84728`。本机和另目录公开克隆均通过4745文件清单；克隆只用Git中的数据重画主PNG、20帧GIF、局部PNG，三个媒体文件及查看器源码与作者版本逐字节相同。[公开恢复回执](../handoff/numpy_c1_h0125_20261003/public_recovery_verify.json)保存原提交、清单SHA、实际命令／exit和各图SHA。未重跑candidate、HP或求解，不新增Release依赖；这是同机异目录恢复证明，不能扩大为异机数值准入。

<a id="split-average-20261003"></a>
## 2026-10-03后续：split平均端口功能

### 本步目标、实现与执行范围

为把已通过的NumPy力／切线用于机构平均输入，新增显式`solve_split_displacement_path`，未知量为自由fluctuation与输入乘子R。方程为`fint + k*b_out*q_out - b_in*R = 0`和`b_in·(lift+w) = target_origin+s`；实际CSC增广矩阵保留非对称，使用一般稀疏LU。各端口节点不绑在一起，固定支撑仍为零。精确两数组状态独立保存；加权测量用FMA补偿每个乘积，再将目标减项纳入同一次fsum，避免先舍入平均值后失去小约束误差。FMA方案只承诺当前有界力学范围，不是任意精度或任意有限输入的通用代数。

`lift_origin`、`lift_shape`、`target_origin`和warm状态／R均显式提供；默认lift为零。stage参数s从0严格递增，warm的lift必须逐位匹配origin，初始平衡也重新检查。保留原HF3力尺度、Armijo与二分设置，NumPy assembler显式传入，默认内核不变。没有改材料弱式、力／切线公式、依赖或严格编译设置；不接入LF、不生成正式标签。

先运行一个**新诊断任务**，不改写原HF3规范机构：3×2mm、3×2个全实体Q1、E=100MPa、nu=.3、t=1mm、alpha=1e-6，左侧固定；右侧+x平均端口三权重[.125,.25,.625]，顶部自由+y输出三权重[.25,.5,.25]。原`rectangular_model`正则参数策略给kr=.0012115384615384614。目标[0,.025,.05,.1]mm，输出弹簧k=0与10N/mm；lift的ux=x/3，未规定个别输入节点位移。它能显示拉伸、Poisson横向收缩及弹簧反馈，**不是机构、接触、工件或夹持力任务**。

自动开发授权下的新阶段：两条生产路径各一次／60秒；一轮独立HP80/120审计／180秒；采样RSS上限8GiB。首次最终路径或审计失败停止，无失败阶段重试；控制器内原有回溯／二分属于一次路径算法。钟和RSS协作检查，非硬进程监督。测试、绘图、只读复核和交付另记。执行前脚本保存模型、端口／扰动方向、协议、源码；审计用新保存两数组重构独立参考，不用生产显示位移。

沿用HF3：生产残差1e-9、独立残差1e-8、约束1e-10×max(|d|,1e-6)、全局平衡1e-6、固定误差8e-11mm、力评价1e-9／SF。SF包括自由内力、输入力、输出弹簧力及原下限；不能使用C1的自由内力为零门。当前三力／三CSC方向门与HP80/120一致性仍保留；新增增广矩阵力／约束作用检查是方程身份检查，不替代原平衡门。保存支反力／输入力／弹簧力及报告均值分别对独立参考核查。状态hash只含lift/w；R和任务数据由其所在summary／协议的完整文件SHA绑定。

### 执行前验证与限制

新9项测试及原35项共同代数测试通过：包括非均匀权重、不同节点位移、非对称KKT、弹簧耦合lift预测、乘积低位、warm成功续算／位级回退、原回溯及NumPy真实小Q1响应。组合命令`pytest -q tests/test_split_displacement.py tests/test_displacement.py`为44通过／1失败（2.72秒）；唯一失败是原真实JAX测试的x64配置检查：新测试先导入JAX，原文件随后才设置环境变量，尚未执行其真实编译力学。未改配置、升级依赖或重试，不能声称完整组合全过。独立审阅在首次数值执行前检查新控制器及审计方程。

### 实际结果与物理效果

独立公式预审通过后，两条路径各执行一次并完成全部四原目标，**8接受记录／7唯一状态**（两例零态重复），没有二分或最终失败。[生产摘要](../hf4_c2_stable_f_validation/split_average_001/solve/summary.json)记录k=0路径2.5907564秒、k=10路径2.6676230秒，Windows进程峰值工作集123,420,672bytes。后续[独立新参考审计](../hf4_c2_stable_f_validation/split_average_001/audit/summary.json)实际16次HP调用（8记录×80／120位，不复用重复零态），**272/272检查通过**，1.9532606秒，峰值123,592,704bytes；两次命令exit0。没有运行编译力／AD或修改关闭卡。生产字段`new_state_independent_HP_audited=false`保留生成当时身份，后续审计给出资格，不回写生产。

| d=.1mm末态 | k=0N/mm | k=10N/mm |
| --- | ---: | ---: |
| 输入乘子R，N | 4.45437756179 | 4.68078693820 |
| 输入加权平均，mm | .1 | .1 |
| 输出+y加权平均，mm | -.0602863982432 | -.0416812887747 |
| 输出弹簧广义作用力，N | 0 | +.416812887747 |
| 输出弹簧能量，N·mm | 0 | .00868664916962 |
| 生产相对平衡残差 | 4.28954e-16 | 3.20272e-10 |
| HP80相对平衡残差 | 4.08208e-16 | 3.20272e-10 |
| 最小J | .991371976616 | .991644339756 |

这里负输出是顶部向−y收缩。输出弹簧产生+y力，减小收缩幅度约30.86%，同时输入力增加约5.083%。非均匀输入权重使节点运动不同，不能把它视为均匀单轴拉伸的解析材料试验；解析响应另由小Q1测试验证。输出力是弹簧作用，不是工件夹持力。

全部状态最大总力／SF误差1.31387e-16，总CSC方向误差1.93339e-16，增广力作用误差2.01892e-16；分量方向最大5.61973e-16。HP80/120一致性最大8.73890e-78。最大HP残差3.20272e-10、约束归一误差1.73472e-17、反力平衡2.16555e-11；固定误差零，所有J正。原门不变，尚未转接`project_evaluation`文件评价dispatcher，也未验证规范机构完整行程。

[实际x1形变与四列物理图](../functional_views/split_average_20261003/split_average_demo.png)、[四帧实际路径动画](../functional_views/split_average_20261003/split_average_demo.gif)展示两例结构、支反力／输入／弹簧箭头、输入与弹簧力、自由输出、三处输入节点位移及加权平均。统一力箭头比例.23927600525005804mm/N，全路径共用J色域[.9913719766161554,1.0493218201112178]；颜色为单元平均J，标题为积分点最小J。原网格虚线、变形实线均按真实尺度。显示用舍入lift+w，不用于力学／约束。[图元数据](../functional_views/split_average_20261003/metadata.json)保存末态数值、完整输入绑定和两媒体SHA。原点帧没有非零力，Matplotlib一次空legend警告不影响输出；图／源码保持运行时版本。

[独立保存证据复核](../hf4_c2_stable_f_validation/split_average_001/independent_review.json)不调用力、求解器或新HP：8记录、16参考文件、16CSC、13输入及35源码绑定通过；两数组精确和与两种HP权威一致，SF／任务量与256/272个原检查的数值和布尔值独立复算一致。另16个材料／正则候选Jv误差缺少保存候选作用向量，仅保留作者审计通过，**没有声称这些值已独立复算**。总CSC及增广作用可完整重放；新控制器实际使用的是总切线。后续新任务若保留分量误差应直接保存小作用向量，原已完成审计不为补包装而重跑。

独立物理审图查看PNG及GIF原点／末帧通过，方向、数值与节点自由运动一致。末态三输入ux分别为k0[.002182747,.045134466,.141509664]mm、k10[.012265672,.047293809,.138629342]mm，加权均值均.1mm。弹簧箭头按共用真实比例较小，GIF色域须结合PNG色标查看；图不能代替新机构或接触资格。

### 当前取舍与下一步

这个最小普通任务证明平均输入、自由输出弹簧、实际非对称切线和平衡已可协同工作；不扩大为一般接触、真实夹持或HF5资格。下一步沿用原HF3规范反向器／夹持器几何、材料及端口，先做一条小行程NumPy split路径和新态参考核查，观察输出符号、传递比例、输入力与实际形变；以成本和结果决定扩大行程。随后实现普通LF v2数据适配。工件、夹持力定义与网格政策仍需明确，不能静默采用HF5草案。

### 恢复和使用

新入口、完整小模型／状态、总与增广CSC、全部新HP原字符串、来源、协议及图均随Git，无新增Release依赖。在任意克隆根重画图（my-view必须不存在）：

```text
python hf_repo/scripts/run_split_average_demo.py plot --input hf4_c2_stable_f_validation/split_average_001/solve --audit hf4_c2_stable_f_validation/split_average_001/audit --output my-view
```

API：从`hf_eval.split_displacement`导入`solve_split_displacement_path`，显式传入NumPy combined assembler；lift/mean/R按上述合同提供。CLI的solve和audit只用于该诊断夹具；复算必须另用新目录、记录新预算及身份，不覆盖本次证据。只看／重绘无需力学或新HP；后续公开克隆恢复与独立只读复核记录补在本节。

本轮科学结果普通推送main提交`5443b6b64352a69b6aeee8304319af7ea4223c49`，本机及另目录公开克隆4842件轻量校验通过。公开克隆只用Git输入重画PNG、四帧GIF；两媒体、查看器源码及完整metadata与作者版本逐字节相同，[恢复回执](../handoff/split_average_20261003/public_recovery_verify.json)保存命令、exit和SHA。没有新力／HP／求解、不新增Release依赖；这是同机异目录恢复证明。

接续预研已纯构造核对原HF3普通机构输入：`geometry_dataset/canonical/inverter/geometry.json`＋`geometry.npz`及`hf_repo/configs/hf3/inverter_pilot_v1.json`全部随Git。拟先反向器[0,.001,.025]mm前缀，父任务仍1mm，不改写完成范围。保持原80×40／1mm、3200Q1／6642DOF、E1MPa、t20mm、nu.3、gamma=alpha=1e-6、Lr80mm、kr=.008615384615384613、k0与无工件。新lift仅三个输入ux DOF为1，节点fluctuation独立。直接`build_project`后调用split平均入口；旧`evaluate_project`仍单数组且强制父任务末目标，尚不改成新dispatcher。

拟一次300秒／8GiB NumPy路径和一次300秒／8GiB新HP审计；按480单元实测粗估3200单元约10秒／内核、20秒／参考，仅预算依据，不是保证。保持原HF3门，**SF下限必须使用E*t=20N/mm，不能套用小演示的100**。新参考不能复用旧单数组态；保存各候选作用向量以便完整重放。这个近期范围尚未执行，不声称规范机构新候选通过；后续根据结果扩大行程／转夹持器，再推进普通文件适配。

<a id="numpy-inverter-prefix-20261003"></a>
## 2026-10-03后续：原HF3反向器的NumPy split小行程

### 目标、实施范围与执行前依据

整体目标仍为普通几何驱动的独立HF力学评价。前步小实体证明新平均端口的方程和弹簧反馈，本步把它用于实际机构，在**原任务、原几何／材料／边界**下观察输出反向运动、增益和输入力。只走[0,.001,.025]mm前缀；父任务保持1mm，不改成小目标或假称完成父任务。普通局部新驱动直接调用`build_project`＋split平均控制器＋显式NumPy assembler；旧文件dispatcher保持原语义。

原反向器普通geometry JSON／NPZ和HF3 task均来自Git；80×40mm、1mm网格、3200Q1／6642DOF、1128实体单元与2072介质单元，模型下半部不自动翻倍。E1MPa、nu.3、t20mm、gamma=alpha=1e-6、Lr80mm、kr=.008615384615384613、k_out0及无工件均保持。输入三节点ux权重[.25,.5,.25]，输出仍为右上原端口的−ux。lift仅三个输入ux DOF为s，固定处零；独立fluctuation允许三个节点位移不同。这个任务没有工件或接触闭合，不命名为夹持力。

新阶段明确一次300秒／8GiB NumPy路径＋一次300秒／8GiB新HP80/120审计；钟和RSS为协作采样，非硬OS监督。第一次最终路径或审计失败停止，无失败阶段重试；既定Newton回溯／二分属于一次路径内部算法。保持HF3 max_checks25、max_backtracks12、max_bisections4、Armijo1e-4；最低增量按原“首增量/16”规则取.001/16，记录其来源而非套用默认.025/16。生产1e-9、HP1e-8、约束1e-10、全局平衡1e-6、固定8e-11mm、力评价1e-9及原SF规则不变；下限Et=20。沿用当前严格六项NumPy方向门和HP一致性1e-40，保存所有候选方向向量和总／增广CSC，便于完整只读重放。

前轮组合测试的导入顺序问题已修正：新测试在共享JAX模块导入前使用原控制器测试相同的x64／CPU设置，未修改运行内核、依赖或严格编译选项。独立子进程以120秒限执行原组合，**45/45通过，4.85秒，exit0**；其中原两单元JAX力学测试实际执行，不能混称为新NumPy生产路径。前轮44通过／1配置失败保持原回执；本轮新事实另记。其余步骤仍待首次数值执行和参考验证。

### 实际生产、独立参考与复核

本轮一次[新生产路径](../hf4_c2_stable_f_validation/numpy_inverter_prefix_001/solve/summary.json)完成全部三个原前缀目标，3条接受记录，exit0；求解内部141.4550317秒、准备后阶段总钟141.8789636秒，Windows峰值工作集772,149,248bytes（约736.38MiB）。9次内核调用全部返回，内核＋传输140.9176572秒、组装.0281402秒、一般稀疏LU .2552358秒；没有失败增量、二分或回溯拒绝。末目标Newton检查3次，.001目标2次。来源和输入末次核对通过；[执行前预审／测试](../hf4_c2_stable_f_validation/numpy_inverter_prefix_001/pre_review_and_tests.json)记录当前入口身份及范围。力、切线、split控制器源码与本轮开始的main完全相同；本步新增普通驱动和审计／图。

[新状态HP80/120审计](../hf4_c2_stable_f_validation/numpy_inverter_prefix_001/audit/summary.json)实际新算6次参考，**3状态／111项检查全部通过**，exit0。summary计时150.8710172秒，随后lifecycle完成时150.9391131秒；峰值工作集956,456,960bytes（约912.15MiB）。先由绑定普通几何和父task纯数据重建并逐项核对完整模型／算子／端口，再对每条保存两数组和固定lift做检查；未替换为旧HP或显示位移。保留全部六候选作用向量、总／增广CSC、原始新参考和所有输入／来源SHA。

[独立保存证据复核](../hf4_c2_stable_f_validation/numpy_inverter_prefix_001/independent_review.json)在不调用力、Newton或新HP的条件下，**111/111原检查全部精确重放**，没有分量向量遗漏。两数组以3000位形成物理和与加权目标，再按120位方程重算SF和指标；保存总／增广CSC作用与向量逐位一致，KKT恒等式、原任务重映射、lift逐位、反力／约束及输入／来源绑定均通过。本次实际新状态没有重试或拼接原单数组结果。

| 输入均值mm | 新输入力N | 新输出−x均值mm | q_out/d | 最小J |
| --- | ---: | ---: | ---: | ---: |
| .001 | .000169872672930454 | .001601920368560766 | 1.60192036856 | .999909395124 |
| .025 | .004249845332071079 | .04009602327735562 | 1.60384093109 | .997735791369 |

末态生产残差7.46051e-13、HP80残差7.46038e-13，平均约束误差零。实体最小J .999423766641，介质最小J .997735791369；两类均接近1，没有接触闭合证据。末态三个输入ux分别.0247666856067、.0250502606777、.0251327930379mm，加权均值.025mm；它们并未被绑成同值。输出沿原−x方向，显示机构的反向运动及约1.604位移增益。输入力为所建下半模型的广义力，k0使弹簧作用与能量为零；不能称为夹持力或自动翻倍。

| 最大量／归一误差 | 实际 | 既有门 |
| --- | ---: | ---: |
| 总力／SF | 1.24729e-15 | 1e-11 |
| 材料力 | 2.19771e-16 | 1e-9 |
| 正则力 | 1.50915e-16 | 1e-9 |
| 总CSC方向作用 | 9.72835e-16 | 1e-10 |
| 材料CSC方向作用 | 9.73307e-16 | 1e-9 |
| 正则CSC方向作用 | 1.94598e-14 | 1e-9 |
| 增广力块方向作用 | 1.31473e-15 | 1e-10 |
| HP80/120差 | 1.48823e-73 | 1e-40 |
| HP80平衡残差 | 8.71543e-12 | 1e-8 |
| HP80全局反力平衡 | 4.73005e-15 | 1e-6 |

HP均值和固定误差均零，所有J为正。[与原HF3标量的对照](../hf4_c2_stable_f_validation/numpy_inverter_prefix_001/historical_comparison.json)分别绑定原bridge .001和原首全路径目标.025；输入力相对差不超过2.075e-15，输出相对差不超过1.731e-16，报告最小J相同。这里只是同物理任务的响应观察，旧状态／参考不能替代本次新状态资格，也不是全面连续体收敛证明。

### 可视化、取舍与接续

[当前实际形变／力／输出图](../functional_views/numpy_inverter_prefix_20261003_display_v2/split_project_path.png)、[三接受帧动画](../functional_views/numpy_inverter_prefix_20261003_display_v2/split_project_path.gif)及[逐状态数值CSV](../functional_views/numpy_inverter_prefix_20261003_display_v2/numeric_states.csv)可人工检查。主结构倍率1，补充结构明确倍率100且不画力箭头，其J仍是实际状态；实体蓝色、介质橙色，各用独立J色域。统一节点作用箭头417.658867343079mm/N（所有状态／支承／输入／弹簧共用），并保留原实体边界虚线。J为单元积分点均值的色图，数字表为积分点最小值，都不是接触压力。增益轴局部放大，实际增益仅从1.601920增至1.603841，约.12%变化，不夸大非线性。

两路物理审图确认方向、节点平均、作用力平衡、半模型未翻倍和倍率标注。首次图的实体色条使用Matplotlib“+1”偏移，负小数刻度可能被误读为负J；仅修正查看器的刻度格式，在新display_v2目录重绘（9.4379秒／exit0）。[首次图](../functional_views/numpy_inverter_prefix_20261003/split_project_path.png)及其源码／元数据保留；新图直接显示.9996～1.0004附近实际正J。新旧CSV及GIF逐字节相同，没有重跑力、HP或平衡。[执行回执](../hf4_c2_stable_f_validation/numpy_inverter_prefix_001/execution_receipt.json)与[物理审图记录](../hf4_c2_stable_f_validation/numpy_inverter_prefix_001/visual_review.json)分清数值运行与两次纯绘图。

这个结果把新平均控制从实体演示推进到实际反向机构。**仅小行程前缀通过，不授予原1mm全程、接触／夹持或HF5资格**，原几何研究资格阈值仍pending。当前NumPy计算可靠但成本高，9次力／切线几乎占全部141秒；没有证据支持用更多稀疏求解检查或重复同例改善成本。

下一步将同一普通入口扩展到原HF3夹持器的同尺度小前缀，复用实现并检验其+y输出及背景对称边界，不复制整套驱动；随后实施普通LF v2文件适配。全行程的预算将根据实际调用数另行明确，真实工件和夹持力定义仍待明确，不能把自由输出改称夹持。当前生产默认内核、源力／切线公式、strict选项与依赖保持。

完整普通任务输入、状态、候选向量、总／增广矩阵、新参考字符串、源码和图随本轮main交付。只阅读／重画无需旧工作盘符或大资产；在任意克隆根运行下列命令（my-view必须不存在），不执行力、HP或求解：

```text
python hf_repo/scripts/plot_split_project_path.py --input hf4_c2_stable_f_validation/numpy_inverter_prefix_001/solve --audit hf4_c2_stable_f_validation/numpy_inverter_prefix_001/audit --output my-view
```

另需新数值时以新的solve／audit目录运行本节冻结身份入口，不覆盖本次数据；旧科研结果、失败和卡窗口都不重开。

本轮科学代码、状态、新参考与图普通推送main提交`581a9990c6cee05f5d48c3936c86c9a3bc220f65`。另目录公开克隆从`496b317`仅fetch＋fast-forward至该提交，4938件普通文件身份校验通过，前后工作树干净；使用Git保存输入和证据纯重画三帧。当前PNG、GIF、数值CSV、查看器源码及完整metadata五文件均与作者版本逐字节相同；[公开恢复回执](../handoff/numpy_inverter_prefix_20261003/public_recovery_verify.json)保存实际命令、exit与SHA。本次不调用力、HP或求解，不新增Release资产；这是同机异目录恢复及显示可复现证明，不冒称异机运行环境或新的力学资格。

<a id="numpy-gripper-prefix-20261003"></a>
## 2026-10-03后续：复用NumPy split入口验证原夹持器

### 执行前计划与物理边界

整体目标仍是只读普通LF几何的独立HF正向评价；本阶段把前步已通过的实际反相器入口复用于第二类机构，验证下夹爪的自由运动和输入力。依据前步141.88秒生产／150.94秒新参考及未出现失败增量，本步明确**一次300秒／8GiB采样生产和一次300秒／8GiB采样HP80/120审计**。保持协作预算、首个最终失败停止、无阶段重试及既有Newton内部回溯／二分；不是重开旧执行卡或挪用它们的剩余额度。main基线`2b16e7ce12db1a2e96b0f96e836ebdd09abe6f8a`、工作树开始干净、origin仍为既定Compliant-TO-TMC。

保持原`canonical/gripper`几何和`gripper_pilot_v1.json`任务：80×40mm／1mm、3200Q1／6642DOF、87固定／6555自由，E1MPa、nu.3、厚20mm、Et20N/mm、gamma=alpha=1e-6、Lr80mm、kr=.008615384615384613、k_out0、无工件。输入仍三节点+ux权重[.25,.5,.25]，仅这些ux的lift_shape为1；输出改按原夹持器节点[2348,2429,2510]的**+uy**平均。实体对称段x0..60，但原背景uy对称线x0..80必须保留；旧释放20个背景自由度的诊断变体不进入本步。

共用驱动／审计／查看器以有限两例身份表和保存端口参数化，源力、切线、控制器、默认编译内核和严格选项不改。新状态走原[0,.001,.025]mm前缀，原父任务1mm仍未完成。保持原HF3力／均值／平衡／固定门、Et标度及.001/16最低增量；保持新候选六方向门、HP80/120差1e-40和增广恒等式门，保存全部分量向量／CSC／新参考，拟独立精确重放111项。新参考必须针对夹持器新状态，不能借用反相器或旧单数组资格。

完成条件为本次前缀数值完成、独立门通过及真实结构／力／自由输出可人工查看；它不授予完整1mm、工件接触、夹持力、正式标签或HF5资格。资格研究阈值仍pending，半模型无力或能量自动翻倍。实际结果、停止／失败、数值成本、图与接续决定将在本节补记；新证据用独立`numpy_gripper_prefix_001`目录，原证据不改。

### 实际功能、验证与效果

共用[普通驱动](../hf_repo/scripts/run_split_project_path.py)、[独立审计](../hf_repo/scripts/audit_split_project_path.py)和[查看器](../hf_repo/scripts/plot_split_project_path.py)已支持两个规范案例，case从绑定任务确定，有限身份表保留原反相器及新增夹持器；没有复制整套功能实现。源力／切线／split控制器与基线逐字节保持，默认内核和依赖不改。[纯模型预核对](../hf4_c2_stable_f_validation/numpy_gripper_prefix_001/pure_model_preflight.json)两例通过；夹持器1086实体／2114介质单元、原87固定DOF和+y端口均确认。[静态预审](../hf4_c2_stable_f_validation/numpy_gripper_prefix_001/pre_review.json)记录独立case pins、两例输入、原方程／每状态37项检查AST不变及四源码静态compile；原45/45控制器测试明确复用，没有声称本步重跑测试或修改力学公式。附加交叉预审于生产启动后收到，未改运行源码。

本轮[生产](../hf4_c2_stable_f_validation/numpy_gripper_prefix_001/solve/summary.json)实际一次exit0，3个原目标全部接受，没有失败增量、二分或回溯拒绝；内部153.6282638秒、阶段准备后154.0390809秒，峰值工作集768,274,432bytes（732.68MiB）。9次内核调用全部完成，内核＋传输153.0364333秒、组装.0344361秒、一般稀疏LU .3104101秒；成本仍集中在力／切线。[新HP80/120](../hf4_c2_stable_f_validation/numpy_gripper_prefix_001/audit/summary.json)唯一一次exit0，6尝试／6完成参考、3状态／**111检查全部通过**；summary计时144.6374772秒、最终lifecycle144.6951645秒，峰值950,128,640bytes（906.11MiB）。完整原任务纯映射、输入／来源末次核对、lift和固定约束、分量力／J、六分量候选向量及总／增广CSC均有保存。

新副本[独立保存证据重放](../hf4_c2_stable_f_validation/numpy_gripper_prefix_001/independent_review.json)仅针对本次夹持器身份，**111/111精确重算、无遗漏、exit0**。保留原方程与门；仅换本例三项输入SHA／87固定DOF／family，并把稠密rank-one临时替换为等价稀疏列乘积。两数组以3000位形成物理均值，120位重放任务方程／SF／误差；全来源、状态、新参考、候选向量、CSC作用与增广恒等式通过。未调用力、HP或Newton；原反相器reviewer保持原样。

| 输入均值mm | 输入力N | 夹爪输出+y均值mm | q_out/d | 最小J |
| --- | ---: | ---: | ---: | ---: |
| .001 | .000208412073644746 | .001143715684723626 | 1.14371568472 | .999863031457 |
| .025 | .005214592025732367 | .02860371845879621 | 1.14414873835 | .996581260084 |

末态HP80残差4.48242e-13、均值约束误差零、全局反力平衡2.83845e-16；实体最小J .999361112607、介质最小J .996581260084，均为正并接近1。三个输入ux分别.0247345731789、.0250567791411、.0251518685388mm，权重平均.025mm；节点未被绑同值。R为原下半模型的输入广义力，k0使输出弹簧力／能量为零，夹爪自由向+y运动；无工件反力或真实接触资格。

| 最大归一误差 | 本例实际 | 既有门 |
| --- | ---: | ---: |
| 总力／SF | 1.16583e-15 | 1e-11 |
| 材料力 | 2.65874e-16 | 1e-9 |
| 正则力 | 1.13925e-16 | 1e-9 |
| 总CSC方向作用 | 9.13062e-16 | 1e-10 |
| 材料CSC方向作用 | 9.22907e-16 | 1e-9 |
| 正则CSC方向作用 | 2.13873e-14 | 1e-9 |
| 增广力块方向作用 | 1.23326e-15 | 1e-10 |
| 增广均值方向作用 | 3.72185e-17 | 1e-10 |
| HP80/120差 | 1.17752e-73 | 1e-40 |

[原HF3标量对照](../hf4_c2_stable_f_validation/numpy_gripper_prefix_001/historical_comparison.json)绑定旧.001桥接及.025首目标／旧HP记录，输入力相对差至多3.902e-16，输出至多2.426e-16，报告最小J相同。这支持同任务响应一致的观察，不能替代本次新参考、冒称旧／新状态逐位一致或连续体收敛。

### 可视化及下一步选择

[实际结构／力／J／输出图](../functional_views/numpy_gripper_prefix_20261003/split_project_path.png)、[三接受帧动画](../functional_views/numpy_gripper_prefix_20261003/split_project_path.gif)、[数值CSV](../functional_views/numpy_gripper_prefix_20261003/numeric_states.csv)只读保存态一次绘成（5.57594秒，exit0）。主图变形倍率1，补充明确100且无力箭头；J色图仍为实际状态的积分点均值，数值最小J为所有积分点极小值，都不是压力。支承／输入／输出弹簧箭头所有状态共用482.59344736108017mm/N，没有半模型自动翻倍。+y方向来自保存b_out并核对原端口；实体和介质J各用独立色域及真实正数刻度。增益轴局部放大，实际增益仅从1.143716至1.144149，约.038%变化，不能夸大非线性。

现在新候选已在两种实际机构上实现原普通输入→NumPy力和切线→平均端口平衡→新参考验收→实际显示；两例各111门及完整保存重放通过，仍仅各自小前缀。下一步转向**普通LF v2数据适配**，先两个规范包及一个原生细网格包，保留原生网格和全部掩膜／端口语义，以无FE转换及几何图验证；不继续重复规范小行程，也不把analysis_mesh自动当HF政策。当前正式Git尚无LF v2原包，文档所指`Diversity-TO-Compliant-O-main (10).zip`可按明确成员只读取得，81,618,414bytes／SHA79c44fbf2570651539137d74299714823c8046d13efd9c3bad6eb32bc389745e。重新读30份描述仍为23粗／7细；1800正式包本轮只抽读一例，不能称全量新验收。工件、完整行程、统一分析网格和夹持力定义仍待明确，不能套用HF5草案数值。

本轮完整输入、新状态、向量／矩阵、新参考、源码和图随main保存；[执行回执](../hf4_c2_stable_f_validation/numpy_gripper_prefix_001/execution_receipt.json)区分一次生产、一次审计、一次纯绘图及只读记录提取。报告提取曾误用不存在的summary键，修正为实际per-check计数后写回执，未重跑任何数值阶段。[物理审图](../hf4_c2_stable_f_validation/numpy_gripper_prefix_001/visual_review.json)两路实际查看PNG及GIF首末帧通过，原87约束、+y均值、作用力平衡、J和倍率一致；增益范围说明保留。独立重放采用120秒subprocess上限，未超时；回执创建至写出6.684456秒仅为该内部区间，不含启动／导入／终止，未测整进程墙钟。

科学代码／结果／图已普通推送main提交`b744d41635fd151b2153467b614684e17e166884`；另目录公开克隆仅fetch＋fast-forward至此，5027件普通文件校验通过，更新前后工作树干净。用Git保存输入和随图冻结查看器纯重画三帧，PNG、GIF、CSV、查看器源码、完整metadata五文件与作者版本逐字节相同。[公开恢复回执](../handoff/numpy_gripper_prefix_20261003/public_recovery_verify.json)保存命令／exit／SHA；没有新力、HP或求解，没有新增Release依赖。这是同机异目录恢复与显示重现，不授予异机环境运行或新的力学资格。

在克隆根仅重绘本例（输出目录必须不存在）：

```text
python functional_views/numpy_gripper_prefix_20261003/viewer_source.py --input hf4_c2_stable_f_validation/numpy_gripper_prefix_001/solve --audit hf4_c2_stable_f_validation/numpy_gripper_prefix_001/audit --output my-gripper-view
```

使用随图冻结的查看器保持该次显示身份，既有反相器同理；新的入口修改不要求覆盖历史图或证据。独立保存重放若核对当时代码来源，应在对应科学提交或源码副本上运行，文件恢复校验与新力学资格仍分开。

<a id="lf-v2-adapter-20261003"></a>
## 2026-10-03后续：普通LF v2数据适配

### 目标、依据与近期范围

整体目标要求HF从独立LF优化器输出的普通几何继续计算；前步已接通两例规范机构的NumPy力／切线／平衡，但`dmftd.hf_export.v2`与`hf-geometry-1.0`仍不同。本步实现准备阶段转换入口，读取普通JSON／NPZ、保留原生几何及来源语义，供后续明确任务读取；不把LF生成条件、LF参考响应或评分变成HF材料／任务／资格。

基线main`b8e04f15abfc9145ac866bda39727698787285ef`，开始工作树干净。已从用户所指`Diversity-TO-Compliant-O-main (10).zip`按明确成员复制两个规范设计及按名字排序第一份原生细网格交接夹持器；ZIP前后SHA79c44fbf2570651539137d74299714823c8046d13efd9c3bad6eb32bc389745e相同，三个NPZ均与原描述SHA一致。[来源清单](../lf_data_preparation/v2_adapter_001/source_inventory.json)记录成员、原字节、原生／analysis网格与LF身份，普通输入随Git保存，后续无需原下载盘符。选择与性能无关，不冒称全部30或1800包已转换／验收。

近期只细化这个数据阶段：新增独立HF数据模块和普通CLI；bool四掩膜无损转uint8、`design_domain`→`design`，原native_mesh／cell_mm／origin／domain／厚度／下半模型和四闭线段标签保持。保存完整原JSON／NPZ、原JSON／NPZ SHA、LF→HF身份与原背景(60,80]开闭语义；该背景不作为已施加HF约束，`analysis_mesh`只作来源，不重采样、不清理、不阈值、不优化。

执行范围和预算在运行前明确：三个正式转换按序首错停止、无阶段重试；预计几秒，转换／独立纯数据核对阶段合计上限120秒／8GiB采样，另一次必要pytest子进程上限120秒、纯绘图上限120秒。均没有力、HP或平衡求解。坏输入反例放临时目录，原输入与旧冻结输出不改。验收为两规范HF四掩膜／权威网格／模型范围／区域标签／HF geometry_id逐项相同、细网格保持160×80／0.5mm且端口五节点梯形权重、来源和身份哈希正确、损坏SHA／掩膜／方向／区间等拒绝行为，并生成未变形几何对照图。图中端口箭头表示参考方向，不是力或位移。

完成这个阶段不授予细网格FE、统一分析网格、工件、完整行程、正式标签或HF5资格。现有HF3 `build_project`的原80×40／1mm任务限制保持；下一步根据转换结果扩展普通任务／模型入口，再决定有限路径与物理定义。实际实现、测试、效果、取舍与恢复将在本节补记。

### 实际实现、验证与可见效果

新增 [lf_v2.py](../hf_repo/src/hf_eval/lf_v2.py)（163行）与 [普通CLI](../hf_repo/scripts/import_lf_v2.py)（28行），复用既有HF几何写入、区域节点和梯形权重实现。严格读取原声明的四个bool数组，保留原生轴向／尺度／厚度／半模型及原始JSON／NPZ；仅无损dtype和字段名映射。LF v2继承的LF v1 geometry_id只覆盖三掩膜，因而同时保存原JSON／NPZ SHA和新的HF四掩膜身份，避免把未覆盖的design_domain或区域记录当作已校验。完整LF参考响应／生成记录只保留为来源。

运行前静态交叉审阅发现类型比较可能让False==0或数字字符串通过前段比较，已在正式执行前改为把原始类型交给既有HF规范化器验证；增加两个定向反例，未放宽门、未改既有data.py／regions.py。实现、CLI、测试、查看器和独立核对器的执行字节随[sources](../lf_data_preparation/v2_adapter_001/sources)冻结。

[正式转换回执](../lf_data_preparation/v2_adapter_001/execution_receipt.json)记录三例各一次、exit0／pass、内部0.104891秒、采样峰值38,334,464bytes（36.56MiB）；这是准备后区间，非整进程墙钟。原ZIP与保存输入来源绑定，三例源文件和9份冻结源码前后SHA一致。LF导入、FE、force、HP和solver调用均为0。

| 原生包 | 网格nx×ny／h mm | 实体单元 | 四掩膜变化单元 | 原生端口节点／权重 |
| --- | --- | ---: | ---: | --- |
| 规范反相器 | 80×40／1 | 1128 | 每张0 | 3／[.25,.5,.25]；输入+x、输出−x |
| 规范夹持器 | 80×40／1 | 1086 | 每张0 | 3／[.25,.5,.25]；输入+x、输出+y |
| 原生细夹持器 | 160×80／.5 | 4358 | 每张0 | 5／[.125,.25,.25,.25,.125]；输入+x、输出+y |

[独立核对器](../lf_data_preparation/v2_adapter_001/review_conversion.py)不调用作者适配器，按冻结原文件SHA、独立LF三掩膜header、HF权威四掩膜ID、原生闭段和单元关联核对；实际一次2.254537秒／exit0，三例通过，见[独立结果](../lf_data_preparation/v2_adapter_001/independent_review.json)。两规范HF身份分别2e2bb346…／d4e82cfd…，四掩膜、网格、厚度、model_extent和region_tags与旧规范件相同；细包新HF身份62dd40a9ed8a41a6a2deb55927982c7f409d63bfedbf96079b2ee032e816da8d。支承原闭段关联实体节点分别4/9、3/9、4/17；原背景和实体对称段互斥并覆盖顶线，背景保持来源且未施加HF约束。

独立检查初始外层启动包装因Windows路径键的斜杠不一致出现KeyError，发生于subprocess之前、检查器实际启动0次；仅包装使用as_posix统一后执行唯一一次实际检查，冻结检查器及实现字节未改。[启动回执](../lf_data_preparation/v2_adapter_001/review_launch_receipt.json)保留异常和0→1次的区别；没有重转换、修改数据或放宽验收。

[相关pytest](../lf_data_preparation/v2_adapter_001/test_receipt.json)唯一一次，进程3.449562秒、pytest内部2.63秒，**72通过、1跳过**：新16项包括三例正例与13定向坏输入反例，另复用数据／区域回归。跳过项是既有descriptor_symlink测试，Windows WinError1314禁止创建符号链接，本轮未授予该项通过；没有导入LF或运行力学回归。

[未变形结构对照](../functional_views/lf_v2_adapter_20261003/lf_v2_native_masks.png)和[原生节点／端口权重](../functional_views/lf_v2_adapter_20261003/lf_v2_native_nodes.png)纯读取保存数据一次绘成（2.653237秒／exit0），原生尺寸与结构倍率1。深蓝为设计实体、橙为被动实体、浅蓝为设计空区、灰为被动空区；左右四掩膜与来源一致。箭头固定5mm仅表示原声明参考方向，无力或位移含义；背景(60,80]以开／闭端点标source-only／unapplied。填充绿方块是与实体单元相邻的支承候选节点，空心是不相邻节点；均不代表本步创建或施加了HF任务。细网格五节点权重可逐点人工检查。[绘图回执](../lf_data_preparation/v2_adapter_001/plot_receipt.json)和[身份元数据](../functional_views/lf_v2_adapter_20261003/view_metadata.json)绑定来源／viewer／图SHA。

### 用途、当前缺口与接续

本步补上普通LF文件进入独立HF准备层的真实功能；无需LF软件、优化器或原下载工作目录。运行时HF仍读取明确的hf-geometry-1.0。它没有使用analysis_mesh重采样，没有自动采用源LF弹簧／评分／材料，也没有完成细网格力学、统一网格政策、工件或全量候选资格。已有HF3 build_project的80×40／1mm限制与原任务保持；新转换包不能自动变成细网格HF任务。

下一步扩展**显式普通任务／模型映射**：复用既有Q1模型构造和端口函数，明确材料、支承关联、实体／背景对称、输入均值和输出方向；先做无力／无求解的模型核对及节点图，验证规范包与旧模型等价、细包五节点正确，再根据新模型成本计划有限路径。后续HF分析网格的原生／统一.5mm政策已向所有者提问，尚无答复；本轮只保留原生数据。工件、行程、真实夹持力定义也仍未由HF5草案自动批准。全部30／1800包的转换与资格另按需要扩展，不用三例结论代替全量验收。

在任意克隆根可运行普通数据转换（new-geometry必须不存在；expected SHA见来源清单）：

```text
python hf_repo/scripts/import_lf_v2.py --source lf_data_preparation/v2_adapter_001/inputs/gripper_native_fine/design.json --output new-geometry --expected-descriptor-sha256 05aa71c6d3a77d4a221fe16453f06e7e19b45325a4aff824a951c95d4fd1a443
```

仅读保存数据重画本次图（my-data-view必须不存在）：

```text
python functional_views/lf_v2_adapter_20261003/plot_lf_v2_conversion_frozen.py --input lf_data_preparation/v2_adapter_001 --output my-data-view
```

这是数据入口和显示的复现，不是新力、HP或平衡求解。异目录图元数据中的input_root会跟随实际读入根，其他身份与数值须一致，不虚称完整metadata字节相同。main交付和公开异目录恢复的实际结果将在下段补记。

两路实际审图及独立保存数据检查通过，见[测试／数据审图](../lf_data_preparation/v2_adapter_001/visual_review_tests.json)和[独立数理审图](../lf_data_preparation/v2_adapter_001/visual_review_math.json)。均确认三例结构与mm尺度、细网格端半权、实体关联节点、开闭背景、方向箭头和未施加HF任务说明；无重绘／重转换／力学计算。测试回执的started_utc字段实际在运行后写入；回执原字节保持，这里明确更正其解释：该值不是实测启动时间。3.449562秒为实际subprocess墙钟，不受字段命名影响。

本轮数据源码、三份原始包／转换包、独立核对、测试和图已普通推送main提交602d0763183eab82f4c00fbb1dc5b42619be7aae。另目录公开克隆仅fetch＋fast-forward至此，5073件普通文件身份校验通过，工作树前后干净。实际使用该克隆中的CLI和保存普通输入各转换一次到新的外部目录；三例共12个geometry JSON／NPZ及原始source副本与已发布结果逐字节相同，HF身份一致；转换输入与执行源码均来自公开克隆，未读原下载ZIP。

冻结查看器以该克隆中的保存数据重绘，两张PNG及查看器源码逐字节相同；metadata只有input_root随实际克隆根变化，其他全部字段、数值及SHA一致。完整metadata不声称字节相同。[公开恢复回执](../handoff/lf_v2_adapter_20261003/public_recovery_verify.json)保存每条命令、exit、墙钟与12件产物／图SHA，所有步骤exit0，无重试、无LF导入／FE／force／HP／solver，没有新增Release依赖。这证明同机异目录普通数据接入和显示可重现；不是异机运行环境或新力学资格证明。

<a id="native-q1-preparation-20261003"></a>
## 2026-10-03后续：原生Q1几何与端口映射

### 最近阶段的目标与执行前约束

前步普通LF v2适配及公开异目录CLI／图恢复已经闭合。整体目标仍是普通几何进入明确HF任务后获得力、形变及接触响应；当前阻碍是project.py的80×40／1mm、三节点端口和规范文件身份限制。只读沿真实代码核对发现regions.py、Q1算子、NumPy组装及split均值控制已经按实际尺寸工作，因此下一步复用几何映射，随后再接显式任务；不复制或修改力／切线公式，不把新候选塞进旧CASES身份表。

main基线ccbd902aad73abebeb171795e3d37b98d88dd1b8，开始工作树干净、fetch后无分叉、origin保持Compliant-TO-TMC。近期只详细实施原生Q1准备层：同一三份已转换普通HF包，由既有HF reader和regions函数导出坐标、BL／BR／TR／TL连接、四掩膜、实体关联节点、支承／实体对称段的完整节点及关联子集、两端口节点／梯形权重／完整向量，以及LF背景开闭区间的来源候选节点。不会产生fixed/free、材料、已施加约束、HF任务或求解状态；analysis policy明确not_selected。原生几何保留和后续HF分析网格的选择是不同决定，H2问题仍待答，H3工件和5mm草案仍未自动采用。

[输入清单](../lf_data_preparation/native_q1_001/input_inventory.json)绑定三份HF JSON原字节SHA、NPZ SHA和HF身份，不读ZIP或LF工作目录。新小API与CLI仅标准库／NumPy／data／regions，输出普通map.json／map.npz并保存可直接HF读取的原HF JSON／NPZ字节副本；LF provenance仍为原包上下文，原LF普通包在前步证据目录完整保存，不为几何映射引入对LF源码或外部路径的运行依赖。映射描述保存完整原HF metadata、输出字段形状／dtype／SHA及节点／元素／DOF顺序说明，不引入新力学标签。

三个正式映射各唯一一次，首个失败停止、无生产阶段重试；本次映射及独立纯数据核对合计120秒／8GiB采样预算，必要pytest一次子进程120秒、纯绘图一次120秒。预计均数秒；预算是协作采样及subprocess时限，非硬OS监督，不借用任何旧科学卡额度。源和输入在运行前冻结、前后核SHA，旧证据不改。测试可只读两规范已保存model.npz的坐标／连接／实体掩膜／端口向量进行等价对照，不导入TMC或启动新的模型响应。

验收限定三例完整映射：两规范数据逐项与直接索引及既有模型字段相同；细网格12800单元、13041节点、26082DOF，.5mm及五节点端半权保持；每单元有向面积h_x h_y为正；实体关联集合由独立四角节点并集复核；全部／关联支承与对称集合分开，背景(60,80]排60含80但未施加。端口向量仿射平均／虚功身份、反向闭段、非零原点与矩形单元用最少有意义的测试验证。离网格端点、源哈希损坏和复用输出目录应明确拒绝。独立审阅器不调用作者mapping API，以原生索引自行重建所有字段。

图只展示真实mm／x1原生网格、局部Q1节点编号及BL→BR→TR→TL顺序、端口权重与方向、支承完整段和实体关联子集、来源背景；无力／变形／实际fixed边界含义。完成条件为三例mapping通过、独立完整数组核对、相应测试通过和实际图可人工查看。该步骤不授予细网格力学、任务／材料合同、工件或全量候选资格；通过后下一步才添加显式任务／模型入口，并据模型及实际成本规划有限路径。实际结果、异常、图、取舍及main恢复将在本节补记。

### 实际实现、独立核对与效果

新增 [native_map.py](../hf_repo/src/hf_eval/native_map.py) 135行和[普通CLI](../hf_repo/scripts/prepare_native_geometry.py) 30行，复用现有data／regions，既有project.py、力、切线、控制器和默认入口均未改。19项普通数组包括坐标／连接、原四掩膜、实体关联标志、两段完整／关联节点、两个端口向量／节点／权重和背景来源完整／关联节点；元数据写明原生网格、厚度、下半模型、DOF交错顺序和CCW局部单元顺序，并明确无fixed/free／材料／task／已施加约束及未选择HF分析网格政策。

源HF JSON原字节SHA、语义descriptor_sha256、NPZ SHA和几何ID分别记录；完整原HF metadata与可直接load_geometry的HF JSON／NPZ原字节副本随输出保存。HF几何ID不覆盖区域标签，源描述的完整身份继续绑定区域和来源语义。metadata中LF provenance的路径明确属于原来源上下文，不在mapping中解析；原LF数据仍完整保存在前步包内。无外部LF软件、ZIP、旧机盘符或原始优化运行需求。

正式执行前六新源码的最终SHA／AST核对通过；两路静态交叉审阅未发现索引／API／背景语义问题。查看器在正式绘图前增加entity／background实际来源节点的实心／空心关联显示，最终9源码随[sources](../lf_data_preparation/native_q1_001/sources)冻结，没有在生产后修改。执行脚本此前消息中的117行是手工计数错误，实际初次保存及冻结均121行／dbaa97d0…，不代表执行中编辑。

[正式生产](../lf_data_preparation/native_q1_001/execution_receipt.json)唯一一次exit0／pass，三例各一次。内部准备后区间1.4180471秒、采样RSS峰值46,948,352bytes（44.77MiB）；9源码及三源JSON／NPZ前后身份相同。生产不导入TMC／project／split／JAX或LF，没有组装、force、HP或solver调用。

[独立审阅器](../lf_data_preparation/native_q1_001/review_mapping.py)不导入mapping作者，以直接i+j(nx+1)索引、四角单元并集与独立闭段／梯形权重重建全部字段；实际子进程一次2.3074527秒／exit0，19字段×3例的dtype、shape和全部值精确相同，源副本可独立HF读取，见[完整独立结果](../lf_data_preparation/native_q1_001/independent_review.json)。原四掩膜每张零变化，全单元有向面积正，源背景与实体对称段互斥并覆盖顶线。9个current／frozen源码SHA前后均相同，原project.py身份593c7c8a…保持。

[审阅启动回执](../lf_data_preparation/native_q1_001/review_launch_receipt.json)记录唯一子进程、118秒时限、源码前后和exit／stderr。本阶段“合计120秒”按生产内部实际运行区间与独立子进程运行区间扣计；两者测得合计3.7254998秒，独立上限已扣生产。生产receipt的continuous_seconds字段是生产自身的协作时限，不是两个独立进程及其间消息调度的连续墙钟窗口；两者之间没有统一整进程墙钟计时，不以此声称连续窗口验收。8GiB只为生产RSS协作采样上限，未声称checker峰值或硬OS监督。

| 原生几何 | 单元／节点／DOF | 单元有向面积mm² | 支承关联／全部 | 实体对称关联／全部 | 背景来源节点 |
| --- | --- | ---: | --- | --- | ---: |
| 规范反相器 | 3200／3321／6642 | 1 | 4／9 | 13／81 | 0 |
| 规范夹持器 | 3200／3321／6642 | 1 | 3／9 | 14／61 | 20 |
| 原生细夹持器 | 12800／13041／26082 | .25 | 4／17 | 24／121 | 40 |

端口权重为三点[.25,.5,.25]或五点[.125,.25,.25,.25,.125]；b按交错ux／uy位置放置，输入+x、反相器输出−x、夹持器输出+y。独立制造的仿射位移场下，梯形平均与解析端口中点均值精确相同，制造广义载荷下的节点虚功恒等式也精确成立。这是端口代数核对，未计算真实位移或作用力；后续明确任务可用bᵀu读取均值、Rb形成相应节点载荷。

[pytest](../lf_data_preparation/native_q1_001/test_receipt.json)唯一一次，**10项全通过**；pytest内部.74秒、子进程1.2204181秒。两规范坐标／连接／实体掩膜／b_in／b_out与原已保存model.npz字段逐项相同，测试绑定两旧文件SHA；不导入或重构TMC模型，不借用旧平衡资格。另验证非零原点[10,−3]和2×.5mm矩形单元、反向端点保持向量、离网格端点不吸附、源NPZ损坏拒绝、原输出不可覆盖。临时目录中的测试映射与本步三份正式产物计数分开，没有重复运行旧LFv2或力学测试。

### 可视化、取舍和接续

[原生几何／Q1编号](../functional_views/native_q1_20261003/native_q1_geometry.png)与[端口b分量／候选节点](../functional_views/native_q1_20261003/native_q1_ports_candidates.png)仅从保存数据一次绘成，exit0／2.612122秒，见[绘图回执](../lf_data_preparation/native_q1_001/plot_receipt.json)。整幅真实mm、结构倍率1；右侧局部视窗是原生坐标zoom，标明BL→BR→TR→TL及面积。细包e12160节点[12236,12237,12398,12397]对应x0..0.5、y38..38.5，面积.25mm²；不以视窗放大表示位移。

绿支承／紫实体对称／橙背景均为来源候选，实心表示相邻实体单元、空心表示非实体关联；背景节点实际从61或60.5至80，60只属entity段。端口图逐点写权重和对应b_ux或b_uy，反相器负bx／夹持器正by明确。5mm箭头仅原参考方向；没有载荷、变形或实际fixed边界、接触／夹持含义。背景20／40节点均非实体关联，且未施加。两路实际审图与显示metadata一致，见[数据／测试审图](../lf_data_preparation/native_q1_001/visual_review_tests.json)、[数理审图](../lf_data_preparation/native_q1_001/visual_review_math.json)。输入青色小文字在深蓝实体上对比略低但可辨认，记为后续查看器非阻断改进，不覆盖本次冻结图或重跑数值。

本步使不同原生网格的节点、连接、端口及来源候选集合真实可用，补齐进入任务模型前的数据缺口。旧project.py三节点／h1限制仍保留，纯准备层没有替代完整HF任务或给细网格授予力学资格。下一步增加**显式任务／模型构造入口**：重用native mapping与既有TMCModel，任务明确网格政策、材料／γ／α／Lr、支承关联、entity／background实际约束、端口控制／自由输出；先用纯模型核对原两规范模型数组、约束集合与算子，再构造一个明确测试合同的细网格模型，不启动未决定的物理路径。后续新平衡和HP的目标／预算由模型及成本另定；H2／H3仍待明确，不从LF analysis_mesh／来源弹簧或HF5草案推断。

在任意克隆根可用普通HF几何准备新原生映射（my-native-map必须不存在）：

```text
python hf_repo/scripts/prepare_native_geometry.py --geometry lf_data_preparation/v2_adapter_001/converted/gripper_native_fine/geometry.json --output my-native-map
```

仅读保存映射重画本次两图（my-native-view必须不存在）：

```text
python functional_views/native_q1_20261003/plot_native_geometry_map_frozen.py --input lf_data_preparation/native_q1_001 --output my-native-view
```

map.json／map.npz及source_geometry副本均普通数据；独立检查和冻结源码／图同时随main交付。显示metadata仅保存相对输入布局／路径与SHA，异目录可对照完整字节；实际CLI／恢复运行与main推送将在下段按真实结果补记。

本轮原生Q1 API／CLI、三份完整映射／HF源副本、冻结源码、独立审阅／测试和两张图已普通推送main提交6076ad70b29291b21f361240570ed824b7698702。公开异目录克隆只fetch＋fast-forward至该提交，5113件普通仓库文件身份通过，工作树前后干净；公开克隆的9个执行源码SHA也与冻结生产身份一致。

实际仅使用公开克隆中的普通HF转换包和CLI，三例各准备一次至三个新的外部目录；12件map.json／map.npz／source_geometry JSON／NPZ全部与已发布结果逐字节相同。冻结查看器仅读公开克隆的保存map重绘一次，**两张PNG、冻结查看器和完整view_metadata.json四件全部逐字节相同**；本次metadata只用相对输入布局，未出现前步LF查看器的绝对input_root差异。[公开恢复回执](../handoff/native_q1_20261003/public_recovery_verify.json)记录实际命令、启动／运行时间、exit、全部文件SHA及结果，均exit0、无重试。它证明同机另一目录使用普通Git资料的数据准备及显示可复现，不证明异机环境或新力／切线／平衡资格。实际恢复没有导入LF、选择分析网格政策、创建物理任务或调用组装／force／HP／solver；没有新增Release依赖。回执和本段说明随后与更新后的普通文件清单一同交付main。

<a id="native-model-construction-20261003"></a>
## 2026-10-03接续：显式任务与原生模型构造

### 目标、依据与正式执行前计划

原生Q1准备及公开异目录恢复已闭合，main基线a0b009dfafef7c2dcbb6aa817f9428cd7e9461f5。整体目标和“NumPy完整力／参考→组装／切线→平衡”的数值顺序保持；现有函数层和两规范小前缀已分阶段验证，当前新几何进入实际模型仍被旧HF3严格接口阻碍。本阶段复用native_map与现有Project／TMCModel，新增显式task API／普通CLI，只生成材料、边界、端口和Q1参考算子，随后才为新候选安排静态力与有限平衡。

新接口build_native_project(geometry_file,task_dict)不改旧project.py／HF3 schema／驱动身份表／NumPy公式／默认内核／编译选项／依赖。新task独立schema且完整必填：几何四掩膜ID及覆盖区域的语义descriptor SHA、显式analysis_grid.policy、单位／plane_strain材料／γ／α／物理Lr、实体关联支承与实体对称分量、明确背景段或null、输入加权平均及目标、自由输出、无输入辅助弹簧／工件、未变形参考及待定资格门。首版policy只支持显式native；不隐式选择或实现统一细分。几何hx／hy／厚度保持，kr使用物理Lr，力与能量保持下半模型无自动倍增，LF参数／背景候选不会自动施加。

本轮只构造[清单](../lf_data_preparation/native_model_001/input_inventory.json)绑定的三份普通HF几何，各配一个[构造TEST任务](../lf_data_preparation/native_model_001/tasks)：两规范沿旧HF3材料与完整顶线条件，细夹持器明确native及相同测试材料／完整顶线条件，仅验证接口。目标.025mm是保存指令，不在本阶段执行；与原父task1mm的hash不等价，不授予父完整路径资格。细包是另一结构，不能作为粗→细网格收敛证据。这些TEST不回答全研究H2网格选择，不采用HF5工件／5mm／夹持力草案；新项目记录和原mapping的未施加标记各属不同层，不改原mapping。

正式构造三例各唯一一次、首错停止、不覆盖／重试；生产一个进程120秒／采样RSS8GiB，独立核对另一个子进程120秒，两个窗口明确独立、不声称跨调度的连续总窗口。必要pytest一次120秒，仅读保存模型绘图一次120秒。只调用构造器／写入器，组装、force、HP和solver为0；导入TMC定义可能载入JAX Python模块，但NumPy reference operators不初始化／编译或调用JAX响应。预算仅协作elapsed/RSS及subprocess timeout，非硬OS资源监督。源码／输入正式执行前冻结，执行后核SHA；旧失败、卡窗口、原TMC源码保持。

最低验收为三例全部intrinsic数组／材料／端口／约束与独立索引／参数公式相同；粗两例只读旧model.npz intrinsic字段精确对照（不借F0／lift／方向／路径资格）。细例12800单元／13041节点／26082DOF、五节点端半权、169 merged fixed；从h1到h.5参考梯度×2、mixed Hessian×4、九点Simpson积分权重÷4，物理Lr／kr不变。独立审阅器不调用作者native_project、旧build_project或TMCModel，以Q1节点符号解析微分重建九点算子、材料数组、约束、free／edofs和端口。五案针对测试：两粗等价、细模型及制造仿射梯度／零Hessian、显式background=null不会继承LF来源、缺policy拒绝；不扩展重复防御检查。

可视化仅读保存模型，真实mm／x1展示已施加support ux／uy、entity uy、task background uy及交集／merged计数，来源(60,80]另标来源。输入说明Σwᵢuₓᵢ=d，个别端口自由度不被逐点固定；k_out=0为自由输出，方向只是参考，无力／形变／接触含义。通过后根据实际模型／成本制定新候选NumPy静态力与参考核对，再推进有限平衡；不从构造成功直接授予非线性响应或夹持资格。实际执行、效果及交付将继续在本节补记。


### 实际实现、核对结果与作用

新增 [native_project.py](../hf_repo/src/hf_eval/native_project.py) 239行和[普通CLI](../hf_repo/scripts/prepare_native_project.py) 33行，复用既有Project的数据结构／验证小函数、native_map和TMCModel。task schema为hf-native-project-task-1.0；材料值由明确任务提供，范围为E>0／0≤ν<.5／0<γ≤1／α≥0／Lr>0，首版仍限plane strain／两机构方向profile／无工件／自由输出／无辅助弹簧。这些接口范围不是对任意材料／任务的新数值资格；本次实际三个TEST均沿原E=1MPa、ν=.3、γ=α=1e-6、Lr80mm。

[正式构造](../lf_data_preparation/native_model_001/execution_receipt.json)三例各唯一一次pass；构造区间1.4459982秒，采样RSS峰值137,342,976bytes（130.98MiB）。[外层生产启动](../lf_data_preparation/native_model_001/production_launch_receipt.json)记录整子进程2.2175733秒／exit0、120秒timeout；13个current／frozen源码及所有输入前后身份一致。执行前静态交叉审阅只给root包装补了最终sample()，保障最后SHA检查也在生产协作预算内；旧包装未执行，模型源码未改。构造阶段仅准备NumPy数组／算子和区域；没有组装、force、HP或solver，未执行任何.025mm目标。

每个产物是[model.json／model.npz及源副本](../lf_data_preparation/native_model_001/models)：JSON保存完整task／task hash、source几何四maskID／完整semantic descriptor SHA／原JSON与NPZ SHA、网格／厚度／extent、材料、实际groups／交集／counts和资格诊断；23数组是坐标、连接、flat bool solid、λ／μ／γ、kr／hx／hy／thickness、edofs／fixed／free／solid nodes／solid DOFs、b_in／b_out、grad／hessian／weights／points、k_out及Et参考力标度。原四张二维uint8掩膜与完整metadata保留在可独立HF读取的原字节source_geometry包；不重复保存原生准备层19项数组。模型标明material／constraints／task已构造、response_evaluated=false，与前步map的未施加状态各属各层，不改其文件或语义。

[独立审阅](../lf_data_preparation/native_model_001/independent_review.json)唯一子进程.5255859秒／exit0（独立120秒窗口），见[启动回执](../lf_data_preparation/native_model_001/review_launch_receipt.json)。不调用作者native_project／旧build_project／TMCModel／kernel或JAX，以节点索引、独立集合并集和N=(1+s_x ξ)(1+s_y η)/4解析微分重建：三例原19字段与前步冻结map精确相同，当前23字段dtype／shape／全部值精确一致，各C-order raw SHA声明正确，源四mask零改变，所有材料／task／背景与端口集合正确。两粗规范17个intrinsic字段与旧保存model.npz精确相同；不借用F0／lift／切线方向或原任务路径资格。

| 明确构造TEST | 单元／节点／DOF | 支承DOF | entity uy DOF | task顶线uy DOF | entity／task重叠 | merged fixed／free |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| 规范反相器 | 3200／3321／6642 | 8 | 13 | 81 | 13 | 89／6553 |
| 规范夹持器 | 3200／3321／6642 | 6 | 14 | 81 | 14 | 87／6555 |
| 原生细夹持器 | 12800／13041／26082 | 8 | 24 | 161 | 24 | 169／25913 |

背景在本TEST明确为全顶线，不是源LF(60,80]补集；重叠DOF只合并一次。E、厚度、Lr保持，λ_s=.5769230769230769MPa、μ_s=.3846153846153846MPa、κ_s=.8333333333333333MPa、kr=.008615384615384613MPa mm²，Et=20N/mm；实体材料因子为1，第三介质因子γ仅缩放其λ与μ；kr不随γ或网格hx缩放。细网格梯度×2、mixed Hessian×4、九点Simpson权重÷4；每单元参考积分体积5mm³、全计算域含介质64,000mm³。五节点端半权保持，驱动方向DOF均在free集合，未逐点绑输入位移。

[五案pytest](../lf_data_preparation/native_model_001/test_receipt.json)一次 **5通过**，pytest2.78秒、整子进程4.0333607秒／exit0。两粗模型及保存源副本等价；细模型显式TEST下169fixed／25913free、独立制造仿射梯度准确重建且Hu=0；背景显式null时粗夹持器只有6支承＋14entity=20fixed，即使LF来源背景仍存在也不自动施加；缺少analysis_grid.policy明确拒绝、不从analysis_mesh推断。临时测试模型与正式三份产物分开，没有重复旧力学／LF适配测试。五案与下一绘图独立子进程并行启动，预算各自120秒，不合并为单一连续窗口。

三例几何诊断均status=pending：共享边连通、支承／端口实体关联及同一连通体检查通过，设计体积分数门与最小特征门仍pending，没有重定义门或授予正式研究资格。数据／模型入口成功不代表非线性平衡、一般接触、夹持力或批量标签成功。

### 实际可视化、近期接续与普通复现

[实际模型边界图](../functional_views/native_model_20261003/native_model_applied_bcs.png)及[端口均值方程图](../functional_views/native_model_20261003/native_model_port_equations.png)仅读保存模型／task／HF源副本一次绘成，2.0740424秒／exit0，见[绘图回执](../lf_data_preparation/native_model_001/plot_receipt.json)。整幅真实mm／x1；深蓝实体、浅蓝第三介质；绿色实心支承ux／uy、紫色entity uy、蓝空心显式task uy均来自实际fixed groups。源LF背景另淡虚线标provenance，右表列交集并明确合并一次；5mm方向箭头仅参考。没有绘制力、真实形变或工件。

端口图在原生坐标局部zoom内逐点显示3／5权重、b符号与真实非驱动分量约束。输入Σw_i ux_i=.025mm是保存指令、节点值unsolved，并未各点规定同位移；只有y40顶点的非驱动uy实际为0，其余uy不固定。反相器output−x顶点uy=0，夹持器output+y的非驱动ux均未固定；k_out=0为自由输出，不能解释为夹持力。青色标签改用白底，避免前步深蓝底低对比。细例明确是另一源设计，不作粗细收敛对。

两路实际审图通过，见[数据／测试审图](../lf_data_preparation/native_model_001/visual_review_tests.json)及[独立数理审图](../lf_data_preparation/native_model_001/visual_review_math.json)。均实际看两PNG并核对保存的显示字段／文件身份，不重跑23字段全检查或构造。夹持器overview的LF背景来源虚线与task顶线标记共线，局部被遮；文字／图例／metadata仍明确provenance-only，记录为非阻断显示限制，不覆盖本轮冻结图。

本阶段补齐普通几何＋明确task到真实材料／边界／端口／算子的功能接口。下一近期工作是用这些明确普通模型接入已验证的NumPy完整force，先做少量明确静态场的参考比较及三力显示，再据成本推进组装／切线和有限平衡；不从构造结果跳过新候选验证。H2全研究网格政策、H3工件／行程／真实夹持力仍未决定。新runner或批量调度尚未实现；旧HF3严格入口及已关闭数值卡保持。

在任意克隆根构造新的普通模型（my-native-model必须不存在，TEST保存目标不执行）：

```text
python hf_repo/scripts/prepare_native_project.py --geometry lf_data_preparation/v2_adapter_001/converted/gripper_native_fine/geometry.json --task lf_data_preparation/native_model_001/tasks/gripper_native_fine.json --output my-native-model
```

仅读保存模型重绘本次图（my-model-view必须不存在）：

```text
python functional_views/native_model_20261003/plot_native_project_frozen.py --input lf_data_preparation/native_model_001 --output my-model-view
```

模型、源HF普通副本、明确task、冻结源码、独立核对／测试／图都随main。查看器的实际HF reader仍来自完整Git根，helpers/data.py保存其原字节和SHA；显示metadata仅相对布局，无绝对input_root或时间。main／公开异目录恢复在下段按真实结果补记。


本轮显式native任务／模型源码、三份TEST、23字段模型／HF源副本、独立核对、五案测试和两图已普通推送main提交bc39526ace4f827e6c5248d44c3e612f84c23609。公开异目录克隆只fetch＋fast-forward至此，5162件普通文件身份通过，13个执行源码SHA与冻结生产一致，工作树前后干净。

实际使用该公开克隆中的CLI、已保存普通HF几何和明确TEST任务，三例各构造一次至新的外部目录；12件model JSON／NPZ及source_geometry JSON／NPZ与已发布模型逐字节相同，task hash、source geometry ID及所有counts一致。恢复确实执行了三次模型构造，这是相同TEST合同的普通CLI异目录复现，不计作重新执行正式三例生产或新物理任务；没有组装、force、HP或solver。

冻结查看器仅读公开保存模型重绘一次，两张PNG、冻结查看器、helpers/data.py和完整view_metadata.json **五件全部逐字节相同**。[公开恢复回执](../handoff/native_model_20261003/public_recovery_verify.json)记录真实命令、启动／运行时间、exit及每件文件SHA，所有步骤exit0、无重试；未读原LF工作目录／ZIP，也没有新的Release依赖。它证明同机另一目录用完整Git普通文件可构造同一模型并显示同一图；不证明异机运行环境、统一分析政策或新非线性资格。回执、本段说明和更新后的普通文件清单随后一并交付main。

<a id="native-force-20261003"></a>
## 新普通候选 NumPy 完整力入口（2026-10-03，执行前计划）

**整体目标仍是独立HF机构正向评估**：普通LF几何→明确物理任务→材料/边界/端口→可信内力、切线和非线性平衡→接触/工件/夹持功能→研究层批量。前步完成三例显式native模型，本步响应用户优先NumPy完整力及参考对比的指示；先实现可用普通文件力入口，再根据实际结果决定切线与平衡工作。历史受限通过不能替代新候选证明。

本步增加 native_force API 和 evaluate_native_force CLI：普通HF几何JSON/NPZ、明确native TEST task、NPZ中原始lift/fluctuation→完整材料/HuHu/总单元力及三类全域内力、J/Hu/F/应力/能量和可恢复源/模型/状态。直接复用既有NumPy force-only候选；不复制公式、不切换默认核、不执行JIT/切线/平衡、不定义H2全研究网格或H3工件。平均输入.025mm仍是未执行的task指令；给定位移不是解、内部节点力不是任务反力/夹持力。

已纯数据准备六制造态，见 lf_data_preparation/native_force_001/input_inventory.json，基线524ffc0998f7dff578df890f45a97bc4b7c9928a。对三例各用a=2^-10mm=.0009765625mm：stripe ux=a*(ix%2)，checker ux=a*((ix+iy)%2)，uy=0、lift=0、实际fixed DOF归零。stripe分片仿射Hu=0，checker非零Hu。保留原始绝对局部位移，不减局部平移；完整局部L/w、lambda/mu及公共kr/算子原字节分组。纯数据实际类数4/7/4/6/4/7，覆盖38400单元（两粗各3200×2，细12800×2）。细例是另一设计，不能当粗细收敛对。

**冻结执行范围**：正式六态各一次完整NumPy力，生产120秒/采样RSS8GiB、外层150秒超时；独立参考64次（32 raw类×HP80/120，无导数），全部类展开逐单元三力检查、在Decimal中独立scatter全部DOF，参考300秒/采样RSS8GiB、外层330秒超时。首次错误即停，不修复重试/force，不复开旧卡。源码/输入执行前固定SHA及普通副本，回执含次数、实际时间、资源、身份。预算为本新范围而非沿用已关闭卡；没有把类分组当空间采样或从小样本外推。

原三力门：total 1e-11、material/HuHu 1e-9，HP80/120一致性1e-40。无外载制造态SF=max(||全域总内力||,1e-8 Et max(a,1e-6))，Et由实际模型读取（本三例20N/mm）；子力尺度=max(||该参考力||,1e-12 SF)。局部8DOF使用独立LocalSF同公式，不能由全域尺度稀释误差。保存原始成员表、每类全精度Decimal字串、全域HP字串、完整候选场及全部门统计，覆盖每个单元/DOF；不能仅用global抵消后的误差。

功能测试仅新增入口有意义的少量案例；另绘三例制造位移/J/Hu和材料/HuHu/总内力，实际查看PNG。显示倍率声明，任何抽稀仅绘图；HP核对全量。若通过，main普通提交推送后公开异目录仅一次六态CLI复现（120秒/8GiB，外层150秒），对全部模型/状态/力数组精确比对，另仅读保存数据重绘，不新增HP。此为同机异目录恢复证明，不是新物理资格或跨机性能证明。记录真实效果/限制再决定下一最小切线/平衡范围，避免防御框架膨胀。

执行前补充：功能入口123行、CLI40行，复用既有力公式；独立静态复核见static_review_api.json。新增三案测试在16单元临时混合材料模型上各调用一次force（零态、非零split、刚体平移），与正式六态分开计数；pytest和保存态绘图分别一次／各120秒外层上限。图只读取场，不求力；正式源码胶囊包含22件实际依赖／测试／查看器／checker，需完整Git根和现有运行库，不宣称将flat sources单独搬走便可运行。

### 实际实现、结果和物理解释

本步实际新增 [native_force.py](../hf_repo/src/hf_eval/native_force.py)（123行，SHA9806b675fb33962115b0921d8a5a44ca467677d6968ad44a16d5a29151c2e93d）及 [evaluate_native_force.py](../hf_repo/scripts/evaluate_native_force.py)（40行，SHA2d5b4e1ec864beb8240190bf9efb0bb060ad9943fceaa13048c06dc3af1a7623）。evaluate_native_force(geometry, task, SplitDisplacement)构造明确模型后调用既有NumPy force-only一次，再分别scatter材料及HuHu内力；write_native_force保存普通模型/HF源副本、原始L/w、12项场及JSON身份。固定值兼容只测量，不静默改位移。CLI直接读普通文件，不依赖LF；输出包含真实性质和单位，不增加执行框架或新公式。顶层源snapshot路径在静态复核中改为model/source_geometry/...，模型内部仍source_geometry/...；静态发现的依赖胶囊缺件也在执行前补齐。默认内核/严格编译/依赖/旧冻结数值均未改。

[正式生产回执](../lf_data_preparation/native_force_001/execution_receipt.json)六态各一次通过，内部45.4054561秒、外层46.5220949秒，采样峰值160780288bytes（153.33203125MiB），120秒/8GiB范围内，无重试。六份模型各23字段精确匹配前阶段模型，source/input身份结束再次相同。两粗力核各约2.6–2.8秒，细力核各约15.8秒；这些是完整场调用实测，不是未来Newton/切线成本保证。只有力向量组装，不生成切线矩阵或求平衡。

[新独立审计](../lf_data_preparation/native_force_001/audit/summary.json)status=pass，64/64新HP calls、六例完整覆盖；内部14.8609222秒、整子进程15.4229860秒，采样峰值135561216bytes（129.28125MiB），300秒/8GiB范围内。审计不导入生产mechanics或构造/求解；单单元参考按完整raw bytes分组，每个单元与所属类8DOF三力逐一核对，HP80/120保持全精度；独立推导edofs，以3000位Decimal及Inexact trap对每个单元全部DOF求和，无新增组装舍入后才输出float供显示。921600个局部分量标量和236196个全域分量标量均覆盖；115200个单元分量向量比较＋18个全域分量向量比较通过原三力门和一致门。回执115611 checks另包含身份/范围等核对，不把它们全称物理误差门。原raw类、成员表、各类全精度、全域参考和精确验收字串随Git保存。

| 比较范围 | 总力最大归一化误差 | 材料力最大误差 | HuHu力最大误差 |
|---|---:|---:|---:|
| 每单元独立LocalSF | 7.54148e-17 | 6.27970e-17 | 8.63754e-17 |
| 全域独立Decimal组装 | 5.25390e-17 | 8.20586e-17 | 7.95910e-17 |
| 原门 | 1e-11 | 1e-9 | 1e-9 |

HP80/120最坏一致性9.43561e-78，保持原1e-40门；全量J/F/Hu对HP120四舍五入结果均binary64精确相同，这是本dyadic制造态的附加诊断，没有扩大验收标准。Hu正则力不是材料能量的梯度，不能用材料能量差分替代总残量检查。

| checker实际量（原模型范围、无翻倍） | 反相器粗 | 夹持器粗 | 夹持器细 |
|---|---:|---:|---:|
| 元素／DOF | 3200／6642 | 3200／6642 | 12800／26082 |
| 最小J | .9990234375 | .9990234375 | .998046875 |
| 最大绝对Hu分量（1/mm） | .001953125 | .001953125 | .0078125 |
| 最大节点材料力模（N） | .0338001330 | .0285562030 | .0337962198 |
| 最大节点HuHu力模（N） | 1.81406986e-5 | 1.81406986e-5 | 7.25636595e-5 |
| 最大节点总力模（N） | .0338137275 | .0285718524 | .0338505540 |
| 材料能量（N mm） | .00620622706 | .00597514651 | .0239776460 |

全部stripe的Hu及正则化力精确为零；checker确实激活两者。相同节点位移幅度在.5mm网格上产生更大梯度和二阶梯度，所以细例Hu为粗例四倍；这不是机构实际行程响应或网格收敛结果。材料力随实体/软介质系数显著变化；kr保持未按gamma缩小，制造曲率在整个域均产生正则力。该功能现在能解释内力来源，但给定位移未平衡、无工件/外载，因此这些节点内力模不是输入力、支反力或夹持力；平均输入.025mm指令仍未执行。

[三案pytest](../lf_data_preparation/native_force_001/tests_launch_receipt.json)一次3passed／2.32秒，外层3.2909261秒；16单元混合模型覆盖零态/两分量非零/刚体平移、原状态不可修改、可读取保存源/两数组/场、平移虚功/独立np.add.at组装，并禁止compiled/legacy入口。临时三案另有3次force，不冒充正式6态或新HP。保存态查看器一次5.7966877秒，见[绘图回执](../lf_data_preparation/native_force_001/plot_launch_receipt.json)；0 force/HP/solver。

两图为 [制造位移、J和Hu](../functional_views/native_force_20261003/native_force_fields.png)及[材料/HuHu/总节点内力](../functional_views/native_force_20261003/native_force_components.png)。实际source轮廓/全部节点标量显示；mm主图x1、ux色标micrometres、局部Q1参考灰与给定位移蓝x200；J用每单元9点最小值、Hu用绝对最大分量。力色标log且零值不填地板，箭头只按明示逻辑stride抽稀显示，共用N/显示mm尺度；数值审计全量不抽稀。root已实际看两PNG，已请求Codex面板打开但返回queued，不声称用户已看到面板。Q1小图标题黑字在密棋盘底局部对比低，是非阻断显示限制，主标题/数据/倍率完整；本轮不覆盖冻图。细例另一设计、无contact/pressure/reaction解释、无半模型翻倍均写图和metadata。

### 功能位置、接续与普通文件使用

本步闭合普通文件→明确模型→NumPy完整静态力及新参考；三个旧机制前缀/受限C1资格仍按其原范围独立保留。下一最小工作先把既有非对称NumPy切线接到这套普通模型，选明确方向进行全域组装/作用验证，再根据实测成本执行小步均值驱动平衡并显示实际机构变形/输入乘子/自由输出；不能从本次制造场直接授予新候选路径资格。真实工件、完整行程/一般接触、研究H2/H3决定、全部候选批量标签/排名尚未完成。切线、求解虽已有受限内存API，当前new ordinary native force CLI尚不执行它们。

在任意完整克隆根和现有HF环境，以下新输出目录必须不存在（本命令计算checker内力，非执行task目标）：

```text
python hf_repo/scripts/evaluate_native_force.py --geometry lf_data_preparation/v2_adapter_001/converted/gripper_native_fine/geometry.json --task lf_data_preparation/native_model_001/tasks/gripper_native_fine.json --state lf_data_preparation/native_force_001/states/gripper_native_fine/checker.npz --output my-native-force
```

仅读冻结保存态和审计重绘（不求力）：

```text
python functional_views/native_force_20261003/plot_native_force_frozen.py --input lf_data_preparation/native_force_001 --output my-force-view
```

正式六态、64新HP额度及三案测试/一次图均已经执行；上述命令是可复用的普通功能说明，不表示旧正式窗口重新开放。提交/公开恢复及独立事后身份/审图将在下段按真实结果补记。

### 独立事后复核与审图

[保存数据复核](../lf_data_preparation/native_force_001/postrun_identity_review.json)SHA70fd3f794be93c3ebab1e0b0b6dc51a271a13ce9a818a5059a5af9eb002e43a7，pass_saved_data_review：22来源及18唯一输入身份、六例23模型＋2state＋12场，32 raw类成员恰覆盖每个单元，64参考SHA/precision/原输入字节均核对；从已保存有限Decimal字串另做精确scatter/验收重放，与所有全域值及局部门相同。此为API作者对root生产及另一数学作者审计的交叉核查，构成独立数值公式的仍是原Decimal参考；不把该身份复核伪称又做了64次新HP。所有新增force/reference.evaluate/构造/求解调用0。

[实际两图审查](../lf_data_preparation/native_force_001/visual_review_tests.json)SHAc86ec5734b0405f69f4cad18dcf620a0454be642d797a4d80f65cc6ed82ea8ee，status=pass：实际查看PNG并复核116件来源/显示字段及全量审计范围。记录局部caption低对比和公用标尺下HuHu箭头最大仅约.00552显示mm（亚像素）的非阻断显示限制；力的全节点log色标仍可读，未为了图像夸大物理量或重绘。root亦实际看图；没有重复正式计算/测试或重绘。所有本轮必需检查已通过，现在按此前授权提交main和执行已计划的公开异目录恢复。

### main交付与实际公开异目录恢复

科学实现/六态/64HP/三案测试/两图及事后复核已推送main **537bf965417d4ea07f4f59614b358d0b91874f1e**，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git。原正式工作区和公开异目录D:/hf-restore-20260930均核对为main，公开克隆从524ffc0仅fetch＋fast-forward至537bf96，无分支改换/覆盖/reset；5441件普通交付文件verify通过，22项current/frozen source pins相同。本次不恢复或重审完整历史Release资产。

[公开恢复证明](../handoff/native_force_20261003/public_recovery_verify.json)SHAd955871df8fd9b9c40d97301d2bf4f9a2693f7087a381ec806e19b58900a49ca：在该公开根实际启动六次普通CLI，各新输出至D:/hf-native-force-public-results-20261003，内部连续61.7195277秒、外层64.4004638秒、采样child-tree峰值547758080bytes（522.3828125MiB），120秒/8GiB范围内。36件模型/source/state/force文件字节一致；每例23model＋2state＋12force=37数组，总222字段dtype/shape/values精确相同。result JSON除timing_seconds及其关联descriptor hash外全部字段相同，不能称JSON字节相同。每例stdout log、完整replay receipt和外层回执已普通保存handoff下。正式生产6＋临时测试3＋异目录CLI6=15 force calls分别计数；HP仍唯一64，没有追加或借旧HP来认定本轮通过；tangent/solver/LF调用均0。

公开冻结查看器实际从公开保存的原正式模型/状态/审计读图至D:/hf-native-force-public-view-20261003，4.5970206秒／exit0；两PNG＋脚本＋helper＋完整metadata五件均字节相同，0 force/HP/solver。源审查不等于图重绘，恢复重绘不等于新数值资格。本证据为同一机器/runtime异目录的真实功能恢复，不能声称异机性能或一般物理验收。恢复证据及本补充另随main后续普通提交推送；所有正式窗口均已完成且不重开。

<a id="native-tangent-next-20261003"></a>
### 据本步结果决定的下一唯一近期阶段（尚未执行）

下一步先接**粗夹持器普通模型的切线入口**，使用本轮已保存checker一态；两方向vx=stripe、vy=checker，均dyadic无量纲节点形状，actual fixed DOFs置0、lift固定，扰动参数单位mm、Jv单位N/mm。首先纯数据统计完整raw L/w/材料/公共算子及局部direction类数，再冻结。新module/CLI一次复用batch_tangent_components_split_numpy生成三分量(ne,8,8)，按原COO→CSC模式完整全DOF组装并sum_duplicates，不对称化、不删fixed rows/cols、不把任务端口当逐点强制。旧force/NumPy kernel/查看器字节保持，以继续读取本阶段冻结包。

三分量所有单元和全域Jv分别与新HP80/120方向参考核对；沿用原切线门total1e-10、material/Hu1e-9、80/1201e-40及max(||HP Jv||,1e-10)分母。保存局部矩阵/CSC/方向/完整成员与Decimal参考及全节点力增量图，记录非对称性。建议生产与参考各一次120秒/采样8GiB、各外层150秒，首错停止；新阶段实际成本尚未测，不能把两方向理解成只生成两列（既有实现仍生成八个局部基方向），也不能从细例15.8秒force推出细例切线预算保证。粗例通过并看实测成本后，再决定细例/小步平均平衡。此最近阶段不启动平衡、工件或标签；研究H2/H3继续待决，没有从制造态外推路径资格。

<a id="native-tangent-20261003"></a>
## 普通模型三分量切线与方向参考（2026-10-03，执行前记录）

前轮是实质进展：普通完整力已实现，六态新参考和实际复现通过，main8373a9b与origin同步。整体HF功能目标/无LF优化依赖/无MPM/研究H2-H3待决保持；本轮依据该新证据接普通模型切线，用于随后增量平衡，不能把制造态本身当机构功能。此前切线核已有96静态范围受限证据，但没有这个普通文件入口；本轮新增接口/全域组装和两方向新参考，不重开旧卡。

**范围及功能实现**：新 native_tangent.py/API及evaluate_native_tangent.py/CLI从geometry/task/原始split状态生成三分量全单元(ne,8,8)与full-DOF CSC；K_ij=df_i/dw_j、lift固定，单位N/mm，不对称化，不裁fixed rows/cols，不逐点强制端口。复用既有batch_tangent_components_split_numpy一次，内部完整baseforce一次＋解析tangent一次；没有JIT/solve/target执行。保留model/HF源/state/完整三张量/三CSC及语义/原字节SHA。保持现有force/kernel/测试/查看器/默认参数原字节，新模块119行/CLI40行，不复制本构/导数公式。

只用粗gripper_canonical已有checker态，3200单元/6642DOF，87fixed。两方向dimensionless shape：vx_stripe=(ix%2,0)、vy_checker=(0,(ix+iy)%2)，都用actual mergedfixed清零；扰动scalar参数mm，因此Jv为N/mm。纯数据准备已生成两方向，每条10 raw类，40个新HP80/120 evaluate(...,derivative=True)；分组包含原始L/w/材料/公共kr+算子及完整局部方向字节，保留绝对值，不做平移归一化/空间抽样。输入清单位于lf_data_preparation/native_tangent_001/input_inventory.json。

**原门和证明范围**：独立参考全量核对3200×2方向×3分量的8DOF局部作用、全6642DOF的element-scatter作用及CSC@v作用；total1e-10、material/Hu1e-9、HP80/1201e-40，分母各自max(||HP Jv||,1e-10 N/mm)，不借用force SF。两precision类值经3000位Decimal/Inexact trap精确scatter，再保存原始全精度及全部门。CSC组装另由conn推row/col、对全部系数核对。完整矩阵所有项保存/组装一致不等于已做全部列独立HP：参考验收只覆盖这两条方向。记录三矩阵的Frobenius非对称性及分解舍入诊断，不把应当非对称的Hu项强制对称或以材料能量代替残量导数。

生产与新参考各一次连续120秒／采样8GiB，各外层150秒；包括进口、计算/组装/序列化/最终身份核对的已声明边界，首错误即停止、不修复重试/force。producer所有源码/输入冻结原SHA，独立checker仅读模型原语、通用SciPy稀疏组装及Decimal参考，不导入生产mechanics。新功能测试仅少量16单元临时模型；pytest/保存态图各一次120秒外层，与正式一态分开计数。显示两方向及三Jv，结构x1/单位明确、所有节点norm配色、明示glyph抽稀和公共尺度、caption用白底改善前步图局部低对比，图不求切线/HP。

若所有门通过，依据旧授权继续main提交/推送及公开异目录单次CLI复现（120秒/采样8GiB、外层150秒），比较23模型＋2state＋3张量和所有CSC存储/文件；result除time及关联hash全字段相同，仅读保存数据重绘。正式新HP40不追加/借旧结果；当前不执行平衡、细网格切线/工件/完整行程/标签。粗例实测成本将决定下一最小范围，不能拿15.8秒fine force保证fine八基方向切线耗时。


执行前交叉复核补充：26件源码依赖胶囊、16件实际生产导入闭包及flat basename唯一性均静态核对；root对新八脚本/模块AST及compile(source)通过，未由此构造模型或启动机制计算。checker与pure-data inventory的raw key拼接统一为common+L+w+lambda+mu+v，并严格核对SHA→成员计数完整字典。查看器静态核对保存audit字段及两方向覆盖一致；统计非对称性直接采用已绑定生产/审计量，不因换机BLAS求和尾差阻止纯查看。所有修正在首次正式执行前完成，最终API27250878、CLI8b0cb519、checker52a2b7bf、tests0fe91b64、viewerccb26bf9，旧force及依赖原字节保持。公开CLI恢复helper计时起点也在NumPy/psutil导入前。

### 实际功能、成本与独立数值结果

新入口已运行一次并通过。[生产回执](../lf_data_preparation/native_tangent_001/execution_receipt.json)SHA a3b92500a730a1070a846f5d369100b26a2c95d5f9df35dffa42db5e47452aee：连续21.2462008秒，外层21.8848064秒，采样RSS136.14453125MiB，全部包括导入、构造、计算、序列化与结束身份核对。API元素切线18.0140949秒，模型准备.0132375秒，CSC组装及非对称统计.0157708秒。23字段模型与前步精确相同，三张量及三CSC均完整保存；每矩阵6642×6642，存储nnz116644（包含存储零值，不等于所有值非零）。1次baseforce＋1次解析切线，0 JIT/HP/solver/LF；本次成本仅粗例这一态实测，细例/其他状态尚未测。

[独立新参考](../lf_data_preparation/native_tangent_001/audit/summary.json)SHA ad3050dfb6a0de31720b0e8528e99ed44141dfaddf5e0605fb7ef077a91d3a4e：40/40 HP80/120调用完成，5.7313417秒、外层5.8514353秒，采样92.0859375MiB。两个方向各10raw类全部展开3200单元，没有空间抽样；总153600局部作用标量、39852全域scatter标量＋39852 CSC作用标量完整覆盖，19200单元向量门＋12全域门通过；19316 checks另含身份等核对，不能全称物理门。三分量614400局部矩阵系数均进入独立推导row/col的全CSC组装核对；这证明保存/组装完整，但独立HP物理导数范围仅两方向，不宣称所有矩阵列穷尽通过。3000位Decimal/Inexact trap全域scatter及全精度类参考、成员表、方向/作用/完整原门字串随Git保留。

| 方向作用比较范围（两方向最坏） | 总切线 | 材料切线 | HuHu切线 |
|---|---:|---:|---:|
| 每个单元独立方向范数 | 6.41736e-15 | 8.96736e-17 | 2.59237e-14 |
| 全域独立element scatter | 1.08808e-16 | 8.40491e-17 | 9.03847e-15 |
| 全CSC@v | 2.84873e-16 | 1.10451e-16 | 4.43244e-14 |
| 原门 | 1e-10 | 1e-9 | 1e-9 |

HP80/120全量保存门的最坏一致性8.21531e-80，小于原1e-40。各分母仍独立max(||该HP Jv||,1e-10 N/mm)。全CSC总−材料−Hu分解绝对范数1.91213e-13 N/mm为分量组装舍入诊断，未增设放宽门；真正三作用分别与独立参考核对。

### 物理效果及实际图

[两方向及三内力变化率图](../functional_views/native_tangent_20261003/native_tangent_directional_actions.png)从保存值生成，root已实际查看。当前给定checker态仍a=2^-10mm，不是平衡态；v只是无量纲节点形状，delta s单位mm，小增量内力近似delta f=K v delta s。这张图没有施加任何delta s，不代表输入/支反力/夹持力或真实形变。几何80×40mm按x1显示，3321节点全部norm配色，72个箭头按逻辑stride7仅为显示；方向1对应3显示mm、最大作用53.8462089N/mm对应4显示mm。每列独立log色标但两行相同，不能只凭不同列颜色比较物理幅值；精确0不填人为地板。

| 保存作用（最大节点模，N/mm） | vx_stripe | vy_checker |
|---|---:|---:|
| 材料K v | 53.8462089 | 34.6154024 |
| HuHu K v | 4.53517466e-5 | .0185760754 |
| 总K v | 53.8462089 | 34.6293344 |

从实际公式解释：vx_stripe的Q1方向二阶梯度为零（actual fixed清零仅落在该方向原零位置），但基态Hu非零、指数exp(-5J)随方向J变化，所以HuHu导数仍很小但非零；vy_checker还直接改变二阶梯度，HuHu作用明显更大。材料与总作用主要沿实体结构显著，HuHu系数未按材料gamma缩小。此为本制造场的导数效应，不是一般接触资格。

相对Frobenius非对称量||K−K.T||/||K||：材料1.55575519e-17、HuHu .00369324352、总1.71309518e-6。材料接近舍入对称，HuHu实际非对称来自其非保守弱残量导数；后续Newton必须使用原矩阵，不能改用材料能量Hessian或静默对称化。测试零态Hu=0时对称、混合split/Hu非零时保留非对称，覆盖这个物理区别。

[两案功能测试](../lf_data_preparation/native_tangent_001/tests_launch_receipt.json)唯一运行2passed／1.53秒，外层2.5178383秒：16单元混合模型的完整CSC/固定行列保留/刚体平移零模、state/tensor/matrix/source无损读取，以及非零split不可修改/Hu非对称/两方向独立scatter。临时测试另有2force＋2tangent，不合并正式调用资格；0新HP。查看器一次外层2.8605623秒，0force/tangent/HP/solver；图与冻结脚本/helper/完整metadata保存。白底caption修复前步图低对比；公共箭头尺度下HuHu最大长度约.00138显示mm，箭头亚像素，HuHu大小需读全节点色标和数值，不为视觉效果放大其力学占比。

### 功能位置与普通使用

当前链路已有普通LF v2数据→HF原生几何→明确任务模型→完整NumPy材料/HuHu/总内力→完整三切线CSC及新方向参考。代码复用现有补偿算术/力/导数，仅新增119行API及40行CLI，不重新复制本构公式；默认内核、依赖、严格选项和旧force包保持字节。给定态接口完成，普通文件平均驱动平衡入口仍是下一步骤；已有split平均控制器在小实体/旧规范模型中的受限证据保持独立。研究H2/H3、工件、完整行程/释放重入/真正夹持指标及批量标签/最终排名仍未完成。

在完整克隆根及HF环境执行（新输出目录必须不存在）：

```text
python hf_repo/scripts/evaluate_native_tangent.py --geometry lf_data_preparation/v2_adapter_001/converted/gripper_canonical/geometry.json --task lf_data_preparation/native_model_001/tasks/gripper_canonical.json --state lf_data_preparation/native_force_001/states/gripper_canonical/checker.npz --output my-native-tangent
```

仅读已保存方向及参考重绘，不重新求切线：

```text
python functional_views/native_tangent_20261003/plot_native_tangent_frozen.py --input lf_data_preparation/native_tangent_001 --output my-tangent-view
```

以上为功能使用说明，不重开已执行关闭的一次正式生产/40新HP窗口。独立事后保存态核查、实际图审和main/公开恢复将在下段按真实结果补记；下一步按21.25秒粗切线成本制订最小普通文件平衡阶段，先产生可信机构形变/输入力/自由输出。

### 独立事后保存态复核与实际审图

[保存数据交叉复核](../lf_data_preparation/native_tangent_001/postrun_identity_review.json)SHA e6876139a6c89252ec5fc71e409e5b8b4c21013bac5e009ec61120a8362fc29d，pass_saved_data_review：26 current/production/audit原来源、6唯一输入、23model＋2state＋3tensor＋三CSC和40参考文件均核对；20 raw类共6400单元方向成员恰覆盖，原SHA→成员字典一致。由已保存字串以3000位Decimal/Inexact trap精确scatter、重新核对19200局部门及6全域＋6CSC门，和原门/差值/方向作用完全一致。此为API作者对root生产及独立数学作者参考的交叉核查，独立本构参考仍是原40新HP，不冒充新增参考。0新模型/force/tangent/HP.evaluate/solver/test/CLI/plot。全量HP门最坏8.21531e-80，报告采用全量最坏而非候选最坏条目所附的HP误差。

只读保存方向与hessian收缩还确认vx_stripe全部二阶梯度精确零，fixed清零未改该方向；vy_checker3200单元均非零，最大绝对2mm^-2（v无量纲）。据此确认上述HuHu方向作用解释，不修改力/切线公式或门。

[实际审图回执](../lf_data_preparation/native_tangent_001/visual_review_tests.json)SHA 0770a2caafe236e2aed5306681f7be800088c6a2342a8a6382ad20e7910db97a，pass：实际查看3040×1472 PNG（工具全图显示2048×992），76文件SHA和26来源绑定相同，计数/全部节点/矩阵语义及单位无阻断。明确公共箭头标尺使Hu glyph亚像素，只能按颜色/精确数值读量；没有为了观感改变数值或重绘。root也实际看图并请求面板打开，工具返回queued，不声称用户已经看到面板。唯一正式一态/40HP、两测试/一次图窗口均已完成关闭；接下来按已授权main提交/推送和计划内公开异目录一次CLI恢复。

### main交付与实际公开异目录恢复

科学实现、唯一一态／40新HP／两测试／实际图及独立后审已推送main **ae8f29c62f1a449adb64cfcef42b055281160d0d**，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git。公开克隆D:/hf-restore-20260930从8373a9b仅fetch＋fast-forward到ae8f29c，main且干净；5611普通交付文件verify通过，26来源pins与原正式同字节。未改分支、未覆盖旧结果或重开旧卡。

[公开恢复证明](../handoff/native_tangent_20261003/public_recovery_verify.json)SHA 73bbb607b43d8887e82289ed010f5f68de96b209b091107d6e183a1b4f042211：在公开根实际一次普通CLI，外部新目录D:/hf-native-tangent-public-results-20261003，连续22.5660826秒、外层22.9040424秒，采样child-tree峰647.76171875MiB，在120秒／8GiB范围内。9件模型／source／state／tensor／CSC文件字节一致；23model＋2state＋3tensor＋三CSC各5存储字段=43数组全部dtype／shape／values相同。result除timing_seconds与其关联descriptor hash外全字段相同，不称整个result JSON字节相同。完整CLI log、replay及外层回执随main普通文件保存。

公开冻结查看器又一次仅读原保存数据到D:/hf-native-tangent-public-view-20261003，4.5966989秒；PNG、脚本、helper和完整metadata四件字节相同。0force/tangent/HP/solver。正式1＋临时测试2＋公开CLI1=4force与4tangent分别计数，HP仍原唯一40，solver/LF0；后审和重绘不新增数值资格。这是同机/runtime的异目录恢复证明，不是另一机器的性能或一般接触验收。恢复资料、本补充与下一计划随后另作普通main提交推送。

<a id="native-mean-next-20261003"></a>
### 根据本步证据确定的下一唯一近期阶段（尚未执行）

下一步集中实现**普通文件粗gripper小步平均驱动平衡**，目标是得到真实机构形变、输入乘子与自由输出；不先扩大细网格或制造态矩阵列核查。旧split平均控制器已有小实体／旧规范模型受限结果，现在缺普通文件薄入口。新入口构造Project一次后显式注入既有split_numpy_tangent.assemble_split_numpy，其(K,internal,fields)满足控制器真实合同；不能直接把native_tangent返回的保存包当assembler。新增薄API／CLI／保存函数，不复制本构／Newton／审计框架，不改当前源及冻证据。

另建明确的新TEST任务和hash：同粗gripper普通几何、材料和80mm正则长度，87 actual fixed、全顶线对称、输入加权均值、自由+y输出、k_out=0、无工件；目标仅[0,.001]mm，不将原construction-only的.025mm草案当已执行/批准路径。明确本阶段零lift_origin／零lift_shape，从undeformed开始，真实物理仍D(L)+D(w)。求解方程为(f_int−b_in R)_free=0及b_in·(L+w)=d；端口节点允许各自不同位移，不能绑等值或以每节点载荷总和之外的量冒称输入R。

非对称KKT／通用LU、原HF3 stopping／constraint／force floor／Armijo／backtrack／bisection门保持；minimum_increment按既有初始增量/16规则显式设为.001/16，时间上限单独设定。不改变默认内核，使用NumPy显式assembler；不能为通过关闭严格选项／升级依赖／放宽残量或Jv门。新task目的只为small_mean_driven_test，H2/H3与正式标签资格继续待定。

保存完整23模型＋task/source、所有接受态原L/w／R／三内力／输入与支承力／spring（本例0）／J/Hu／均值／SF及残量、接受态CSC与绑定、Newton试探／LU／Armijo／二分记录；统计正式baseforce／tangent／reference调用真实次数。图以actual结构及x1／声明放大局部对比、输入q-R／自由输出、三端口各节点位移、J及平衡力解释；有限制造态箭头不能替代本次实际解。

独立新参考按每个接受态完整模型HP80/120，不能沿用本制造场10raw类或空间采样；正常两接受态预计4次整模型参考调用（覆盖12800个单元precision instances）。若出现二分中间接受态，它也必须检查，按2×实际接受态数记录，未完成时不授予本轮路径资格。绑定一条明确无量纲输入支撑方向v=b_in/max|b_in|，固定DOF零、lift固定，参考同时给三力／Jv及均值/KKT边界检查；全量局部与global门和HP80/120一致门沿用当前原门/尺度，真实平衡门沿用旧HF3定义，不能只检查已组装抵消后的总残量。正式执行前应把精确检查定义和输入/来源原SHA写入新清单，并静态交叉核对。

新范围建议生产与独立参考各一次连续**180秒／采样8GiB**、各外层210秒，包含导入、构造、所有试探／参考／序列化和结束身份核对；首错误停止、不修复重试/force。历史同物理.001前缀正常3切线＋1force试探，结合本轮21.25秒／完整切线仅估正常约60–75秒，不作保证；历史三态整模型参考实际144.64秒，支持本轮先用180秒两态预算，但新普通模型／方向的真实成本未知。参考超时或有未审状态时明确保留“生产完成、独立验收未完成”，不用墙钟余量重开。小功能测试／仅读图分别一次120秒外层、回执与正式计算分开。通过后main／公开普通CLI及图恢复按当时实测成本再定最小范围。此为基于用户允许按结果推进平衡的最新授权之新阶段计划，不是延用已关闭切线120秒窗口；本段截至提交只读规划，尚未编码或启动新平衡。


<a id="native-mean-20261003"></a>
## 普通文件小步平均驱动：执行前核定（2026-10-03）

前轮普通完整力与切线均有新参考、实际图和公开恢复，属于实质进展。本轮接用户“根据结果推进组装、切线和平衡求解”的授权，采用上一段唯一近期阶段，不重开旧卡。整体目标仍是读LF普通几何，独立计算非线性响应供研究层优选；此处先让普通入口真正产生机构形变、输入力和自由输出。

**已实现与静态取舍**：新增native_mean.py 194行及solve_native_mean.py 47行，构造原Project一次、复用旧平均控制器。原assemble_split_numpy只保留总张量，无法保存/比较三分量；新薄assembler依次调用既有_assemble_force、_tangent、_assemble_tangent(total)，不复制公式或Newton。仅切线调用更新接受态cache；接受state SHA必须相同，force-only试探不覆盖cache。保存从cache取值，0额外力/切线求值；真实attempt/completed分别计数。默认内核/严格选项/依赖及旧源字节不变。

纯数据prepare_inputs.py已唯一执行，0模型/力/切线/求解/HP。清单e0b5ccd8绑定同粗gripper 3200单元/6642 DOF/87fixed/6555free、新task目标[0,.001]mm及零lift。E=1、nu=.3、t=20、gamma=1e-6、alpha=1e-6、Lr=80、kr=.008615384615384613；原实体支承与对称/全顶线约束保持，均值输入、自由+y输出、k_out=0、无工件。task目的small_mean_driven_test；原.025 construction-only草案未自动执行。非对称KKT/通用LU及HF3门保持，minimum_increment=.001/16。

**独立参考的精确定义**：每个接受态，HP80/120各一次整模型计算，预计两态共4次/12800 element-precision instances；若有二分接受态，也逐态覆盖。参考临时conn=arange(4ne).reshape(ne,4)，向量由真实edofs展开，F0/fixed为空；因此一次evaluate能直接给每单元8个局部力/Jv，而非只有相互抵消后的global值。再以3000位Decimal/Inexact trap精确scatter至真实6642 DOF。此仅参考节点重编号，原实际模型未断开、不新增平衡求解，不重新实现本构。保存完整两precision、映射、全局scatter、差值及门字串。方向v=b_in/max|b_in|，实际fixed清零，无量纲；扰动参数mm，Jv为N/mm，乘子方向deltaR=0。

原force总门1e-11、材料/Hu1e-9；global SF=max(||HP fint_free||,||b_in R_free||,||spring_free||,1e-8 Et max(|d|,1e-6))。每单元SF_e=max(||HP total_e||,同物理floor)；分量分母max(||自身HP分量||,1e-12 SF_e)，global分量用自身norm和1e-12 SF。不分摊外力或用全局尺度稀释局部误差。局部/global/CSC三Jv分母各max(||自身HP Jv||,1e-10 N/mm)，原总1e-10、材料/Hu1e-9；HP80/120同分母1e-40。KKT力方向为(K+k b_out b_out.T)v-b_in deltaR，自由部分分母max(||HP作用||,1e-10)，均值方向分母max(|b_in·v|,1e-6)，各1e-10。完整CSC所有204800局部系数组装逐项核对，但独立HP导数范围只有这一方向，不称所有列通过。

真实平衡另按原门：生产残量1e-9、独立残量1e-8、力求值1e-9、平均约束1e-10、global力平衡1e-6、fixed位移8e-11mm。完整17力场、3张量、2split数组和全DOF总CSC保存；输入/支反力/残量及SF由HP再计算，两precision都检查。production JSON资格保持false；独立small TEST资格由audit单独声明，不能冒充HF5完整任务或接触资格。

**执行边界及静态证据**：生产/参考各一次连续180秒/采样8GiB，各外层210秒，包括第三方导入、所有试探/参考、保存及结束来源核对。首个阶段错误停止，无修复重试/force；旧控制器原本有界的Armijo/backtrack/bisection是算法步骤，未增加循环权限。API异常未返回时计数None，避免虚报0。新两功能测试和仅读图各一次外层120秒，仅正式通过后执行；测试临时16单元模型与正式计算分开计数。

API95a3b710、CLI64cbb8c4、checker331eb1d5、tests3771e1af、viewer0f6e3ae5已静态冻结。独立API交叉记录static_review_api.json（af7e3d1c）确认33源覆盖22模块导入闭包、平铺basename唯一、schema/任务/source/state/计数兼容；root已读源码并复核，0数值执行。正式source/input SHA将在生产回执与胶囊留存，期间不得改源。

图从实际接受态显示结构x1、另附明确x1000形变、N力箭头公共尺度、输入q-R/free output、三个输入节点位移与均值、全部3200单元J以及独立残量/平衡；动画只含真实接受帧，不插值。此阶段尚无工件接触/夹持力、细网格路径、完整行程或批量标签。通过后按实测成本规划一次公开CLI/保存图恢复，再提交main；下一最小功能阶段依据本轮结果决定。


### 实际实现结果、成本与物理效果

唯一生产[回执](../lf_data_preparation/native_mean_001/execution_receipt.json) b488b170：pass、67.0487453秒（外层67.3984977），Windows峰工作集/采样RSS736.9140625MiB；2接受态、4完整force／3三分量tangent／1controller调用，0JIT／HP／LF。模型23原始字段与前步逐字节相同。初态切线→预测器→末目标一次Newton修正（factor1 Armijo接受），未二分、无failed_attempt；两次general sparse LU保留非对称，混合单位backward error只作诊断。API力学阶段55.1113222秒，4核调用/3切线占54.9599992秒，CSC组装.0131678秒、稀疏求解.0863224秒；本例主要成本为切线核，不能用此单例保证细模型成本。导入和保存/结束绑定也包含在67.05秒内。

唯一[新独立参考](../lf_data_preparation/native_mean_001/audit/summary.json) 08cc44a0及[lifecycle](../lf_data_preparation/native_mean_001/audit/lifecycle.json) 1b33ad0c：pass，两态4/4 HP调用完成；summary45.1257777秒，lifecycle45.1269200秒、终端45.1274267秒，外层45.9999773秒，采样324.34375MiB。所有3200单元／6642 DOF逐态覆盖，12800 element-precision instances；两态共153600局部力标量及153600局部Jv标量、三全域力和作用，以及409600局部矩阵系数组装核对。38634 checks含绑定等，不全称物理门。参考节点重编号与真实edofs精确scatter完整保存，没有沿用制造态raw类或新增生产计算。

| 全量接受态最坏归一化误差 | 总分量 | 材料 | HuHu |
|---|---:|---:|---:|
| 单元力 | 1.05018e-16 | 9.55427e-17 | 1.36411e-16 |
| 全域力 | 1.14365e-15 | 2.57875e-16 | 1.06772e-16 |
| 单元Jv | 6.33200e-17 | 5.70314e-17 | 8.90240e-17 |
| 全域element-scatter Jv | 5.48463e-17 | 7.78141e-17 | 1.55781e-16 |

总CSC@v最坏1.04798e-16，KKT自由力方向1.05831e-16、均值方向0；都在原1e-10门内。HP80/120完整局部门最坏2.76254e-72（不是只取候选最坏条目所附的HP误差），远小于原1e-40。完整总CSC6642×6642、每态存储nnz116644（含存储零值），所有fixed行列保留。独立方向仍只有v=b_in/max|b_in|，不把完整组装核对称作全部矩阵列HP验收。

| 实际末态物理量 | 数值 |
|---|---:|
| 加权平均输入 | .001 mm |
| 输入执行器对模型总+x力R | .0002084120736447459 N |
| 自由输出加权均值（+y） | .0011437156847236257 mm |
| 此小步输出/输入比 | 1.1437156847 |
| 最大节点位移模 | .00159567335422854 mm |
| 实体最小J | .9999744402870642 |
| 背景介质最小J／全域最小J | .9998630314571697 |
| 生产自由残量／独立HP残量 | 1.5357180e-11／1.5357166e-11 |
| HP平均约束相对误差 | 5.4210109e-17 |
| HP外力平衡相对误差 | 2.4569826e-15 |
| fixed位移 | 精确0 |

这里input force=b_in R，三个节点权重(.25,.5,.25)，三ux实际为(.0009893878015,.0010022700415,.0010060721156)mm，均值为.001mm；节点没有强制等值。输入横向运动产生自由夹爪端+y微位移，下半模型往对称线的这一响应已从普通文件真正算出。R是输入反力/执行器力；输出无弹簧、无工件，不能称夹持力。J接近1，本步只是小变形自由响应，尚未展示介质压薄接触或完整行程。

实体支承节点486/567/648（x=0,y=6/7/8mm）对模型力合计(-.0002084120736447474,-.00005680788371915068)N；其他实际约束合计(0,+5.68078837e-5)N。输入合计(+.0002084120736447459,0)N，完整ΣFx/Fy=(-1.50433e-18,-1.87985e-20)N。支承+y与对称背景约束+y相抵，不能只看实体支承组误认为全域不平衡。原下半模型数量未翻倍。

[真实形变、力和路径图](../functional_views/native_mean_20261003/native_mean_path.png)、[两帧实际动画](../functional_views/native_mean_20261003/native_mean_path.gif)及numeric_states.csv随Git保存。主几何x1；补充图仅位移x1000且没有力箭头，用于看清微米运动。全部3200单元J着色为各单元九点平均，精确min为所有积分点；J不是压力。三输入节点及mean各自显示，右轴输出单位µm，精确N/mm数值另列。路径只存0和.001两个真实接受帧、无插值；连接线不是连续路径所有中间状态的证明。root已实际看2880×1680 PNG，工具缩至2048×1195；面板open返回queued，未声称用户已看到面板。

本版左下legend遮挡实体支承箭头，作为显示局限保留，上表提供完整支承数值；未用新增绘图窗口改写已冻结图。公共最大节点外力.00033157975963119245N对应4显示mm，结构仍x1；力箭头显示长度不是结构位移，顶线支反力按stride3显示，支承节点来源全保存。后续查看器应将legend移出几何区域并保持原数字/尺度。

[唯一两案功能测试](../lf_data_preparation/native_mean_001/tests_launch_receipt.json) pass、2passed/3.97秒，外层5.4174432秒；临时16单元／50DOF检验构造一次、mean-only不同节点、zeroL/fixed0/J>0/原门及cached无新求值保存/源无修改。另有两次临时API/solver，测试临时调用计数没有单独持久化，不能猜算并合入正式4/3。[唯一仅读图回执](../lf_data_preparation/native_mean_001/view_launch_receipt.json) pass、6.6999717秒，0模型/力/切线/HP/solver。图包PNG/GIF/CSV/冻结脚本/helper/metadata共6件，所有bindings及单位保存。

### 普通入口及恢复使用

当前普通文件链路已接通：LF v2数据→HF普通几何→显式native任务模型→NumPy完整力和CSC切线→非对称mean增广平衡→实际形变/输入力/自由输出，并对粗gripper这条小TEST作新独立参考。CLI默认执行明确task目标，API也可给explicit targets；task_target_executed只有成功且实际末目标等于task目标才true。生产equilibrium_qualified/HP/HF flags保持false，audit另声明受限数值TEST通过；不静默升级研究层资格。

从完整克隆根、独立HF环境执行（新输出目录须不存在）：

```text
python hf_repo/scripts/solve_native_mean.py --geometry lf_data_preparation/v2_adapter_001/converted/gripper_canonical/geometry.json --task lf_data_preparation/native_mean_001/task.json --output my-native-mean
```

只读取本次保存态与参考重绘：

```text
python functional_views/native_mean_20261003/plot_native_mean_frozen.py --input lf_data_preparation/native_mean_001 --output my-mean-view
```

上述说明不是重开唯一正式生产/HP/测试/图窗口。两路保存态交叉复核后按用户既有main提交/推送授权交付。根据正式67.05秒成本，公开异目录单次CLI采用同settings／180秒／采样8GiB、外层210秒；只复现同小TEST、0新HP。逐字节比较模型/source与两接受态全部payload，77数组dtype/shape/值；result/state JSON只排实测耗时与其关联descriptor hash，其余源/设置/步序/残量/力/位移/调用计数/资格字段全部核对。另一次冻结查看器仅读原Git保存数据，6件图包字节比较，外层120秒；不把同机异目录恢复当异机性能证明。

整体功能仍缺普通反向器的新平衡、普通两例更长路径/任务行程、真实工件/夹持力、一般接触释放重入、研究H2分析网格/H3定义及HF5批量输出。下一唯一近阶段优先同一薄入口的**粗inverter 0→.001mm小TEST**，检验几何/实体支承/自由-y输出的另一种机构响应；先绑定新task、原model/89个实际fixed DOF，沿用原门和完整两态参考，以本轮成本提出生产/参考各一次180秒、各外层210秒。该阶段截至本段仅计划，未构造/求解；无自动细化或工件假定。通过后再按两例结果选择更长前缀，不详细承诺后续所有阶段。


### 实际审图交叉记录

[实际图审](../lf_data_preparation/native_mean_001/visual_review_tests.json) 2b5ce99e，pass：另一作者实际查看PNG及GIF原1680×770的首末两帧，129文件SHA／33来源绑定一致；NPZ/CSV/meta中三节点ux、精确dyadic均值、J、输入/实体支承/其他fixed合力一致。0新模型／force／tangent／HP／solver／test／CLI／plot，媒体与源字节未改。除图例遮挡外，也明确GIF量化减弱局部颜色、两点双y轴自动尺度使R与q_out连线重叠；应按各自单位及保存数值读量，不能凭重叠线宣称函数关系或完整曲线资格。


### 独立保存态事后复核与本次关账

[保存数据交叉复核](../lf_data_preparation/native_mean_001/postrun_identity_review.json) 79ffe5fa，pass：API作者另用保存数据核对33 current源＋两套来源胶囊共99件、7输入、23model、两态全部2state／17force／3tensor／full CSC。4保存HP覆盖12800 element-precision instances，159408全域Decimal force/action entries以3000位/Inexact trap重新精确scatter；38400局部门＋18global/CSC/KKT门＋48scalar门共38466数值门逐值重放与原字串一致。270270 checks是保存数据核对总数，不能与原38634执行checks相加作为新物理门。0新模型／force／tangent／solver／HP.evaluate／test／plot，独立物理参考仍是原唯一4 HP调用。实际4/3/1及保存0calls再次闭合；所有结束绑定一致、无阻断。唯一正式生产／参考／测试／图窗口至此完成关闭，接下来仅按已写范围交付与公开同小TEST恢复。


### main交付与实际公开恢复

科学实现、两态新求解／4新HP／两案测试／图及两路事后复核已推送main **93851df65a656396d1efd22d65d9eaaf21d08a79**，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git。公开克隆D:/hf-restore-20260930从8a6e188仅fetch＋fast-forward到93851df，干净main；5750交付文件verify通过，science manifest SHA1d74af5f570bb2b18759e1cc94a1da56af22999ed5890d9e84f0b3bb725d6fda。全参考／普通模型／源码／图为Git普通文件，不需旧机盘符或额外Release即可读取本次。

[实际公开恢复证明](../handoff/native_mean_20261003/public_recovery_verify.json) c25b3123：一次普通CLI到公开根之外D:/hf-native-mean-public-results-20261003，63.1868441秒，外层63.3185445秒；采样child-tree724.4375MiB、wrapper＋child759.91796875MiB，180秒／8GiB范围内。12 payload文件原字节相同，23model＋两接受态各(2state＋17force＋3tensor＋5CSC存储)=77数组dtype／shape／Cbytes相同。两个state.json和result全部非时间字段一致，包括所有物理值、source/task、settings、Newton／Armijo／LU诊断、4/3/1计数和资格；只排明确耗时及其关联hash，不称整个JSON字节相同。公开CLI log、回执及实际JSON随本次恢复证明保存，原正式JSON不覆盖。

公开冻结查看器一次到D:/hf-native-mean-public-view-20261003，2.9188564秒；PNG／两帧GIF／CSV／脚本／helper／metadata六件字节相同，0model／force／tangent／HP／solver。正式与公开合计8force／6tangent／2solver，测试另两次临时solver及未单独持久化的force/tangent数不猜算；新HP仍唯一4次，不重复扩大数值资格。此为同机/runtime异目录恢复，不是另一机器的性能或一般接触验收。main交付过程有一次身份check在manifest builder尚未结束时读到旧清单，拒绝modified README；待builder正常结束、重新暂存新清单后完整verify通过，未重跑任何科学执行，此先后错误在恢复证明delivery_events保留。

恢复证明、本补充和原接续计划随后另作普通main提交／推送。粗反向器0→.001mm近期阶段尚未执行；将复用当前入口、原两态参考门、实际89fixed与自由-y输出、新明确TEST和180秒／8GiB各一次预算，先补齐第二类普通机构的功能。下一阶段同时将legend移出结构区域改善力显示；原冻结图/数据不回写。更长行程、真实工件／接触夹持、研究H2/H3及批量HF仍需后续逐步实施，整体目标保持active。


<a id="native-inverter-mean-20261003"></a>
## 普通反向器小步平均驱动：新阶段执行前计划

前轮属于实质进展：main3f0c45d0554a340217bdbfe504b68c445008a06b已交付普通夹爪平衡、两态新参考、真实图与异目录恢复。当前正式根及origin/main干净同步，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git。本轮接已记录的下一唯一阶段，补齐另一类普通机构，整体HF正向评估／不含LF优化／不含MPM／H2-H3待定义保持，前轮唯一执行窗口关闭。

**静态核查与接续描述勘误**：上一段把反向器近期输出写为“自由-y”，描述有误。native_project.py与真实geometry/model明确input+x、output reference−x；b_out在DOF6316/6478/6640为[-.25,-.5,-.25]，所以q_out=−加权ux。正q_out意味着物理向−x移动，实际反相效果须看新解的ux而非仅方向标签。此处修正计划文字，原任务／geometry／model／公式未变，未执行或翻转保存输出。

原model23为3200 Q1单元／3321nodes／6642 DOF／89fixed／6553free；1128实体、2072介质。4实体attached支承的8DOF与全top uy81形成实际89fixed；均值输入DOF6156/6318/6480权重[.25,.5,.25]，两个端口均无fixed交集。h1mm、80×40mm、t20mm、E1MPa/nu.3 plane_strain、gamma/alpha1e-6、Lr80mm/kr.008615384615384613、Et20N/mm保持。源geometry JSON23adf44e、NPZ1911362e、原task5d488f27、原modelNPZ321a10e0、modelJSONaa4b5b34经纯保存数据完整SHA／数组核对。没有导入LF或重新生成几何。

**最小实施取舍**：native_mean API、solver、force与tangent可直接复用，无案例专属改动。旧audit/load和viewer含gripper/87fixed/+y身份，直接参数化原文件将破坏旧33 current源的保存查看合同。因此旧33源及旧来源/结果/媒体保持原字节；新增inverter检查器薄子类，继承旧Audit.run_state及全部力／Jv／HP／CSC／KKT数学方法，只写新身份load、从imports前计时的checkpoint/lifecycle和真实case summary。新图复用纯读/数组/边界/数值表helper，绘制正确−x响应、独立R与q_out轴、坐标区域外图例；不复制旧本构/导数/Newton或整个数学审计。

新stage lf_data_preparation/native_inverter_mean_001/的prepare_inverter.py只由原task/model保存值生成新明确TEST、target[0,.001]mm、zeroL与v=b_in/max|b_in|。原.025 construction-only不自动执行。execute_inverter.py保留接受态cache保存与真实attempt/completed计数，来源包括旧33＋新checker/plot/prepare/execute共37；新包装改名避免平铺basename覆盖。旧两stage包装只继承来源身份、不会执行。源码／输入先静态冻结，再唯一计算。

**物理方程与原门**：(f_int−b_in R)_free=0、b_in·(L+w)=d，free output k_out=0、无工件；lift origin/shape0、undeformed开始。非对称KKT/通用LU、所有HF3 stopping/constraint/SF/Armijo/backtrack/bisection保持，minimum_increment=.001/16。力单位N，K及Jv N/mm，u单位mm；方向v无量纲、lift固定、deltaR=0。只接受真实参考方向和实际fixed/source task身份，不按预期反相更改b_out。

每接受态HP80/120各一次整模型：完整局部重编号后3000位Decimal/Inexact trap精确scatter至真实DOF，正常两态4次／12800 element-precision instances，二分接受态也覆盖。继承原总force1e-11、材料/Hu1e-9；局部SF_e=max(||自身HP总力||,原1e-8 Et max(|d|,1e-6)floor)，分量自身norm/1e-12 SF_e，globalSF与全局分量按原方程尺度；没有全域尺度稀释局部误差。各局部/global/CSC Jv自身max(norm,1e-10)作分母，总1e-10、分量1e-9；HP一致1e-40。KKT力/mean方向1e-10、独立残量1e-8、生产1e-9、force_eval1e-9、mean1e-10、globalbalance1e-6、fixed8e-11mm全部原样。保存所有单元、DOF、17force fields、2split、3tensor、全total CSC及全参考/差值/门字串；独立导数资格限这一方向，非全部列。

**边界与验证**：生产／新参考各一次连续180秒／采样8GiB，各外层210秒，包括第三方imports、所有试探/HP、保存/endpins。依据前轮67.05秒生产／45.13秒参考提出这个新case窗口，成本是估计不是保证。首阶段错误停止、无修复重试/force；旧有界Armijo/二分保持算法本义，超时／未审接受态时保留生产/验收各自终态，不借剩余钟重开。API异常未返回计数None，避免虚报0。核心与小功能测试源原字节不变，本轮实际新案例及完整新参考承担功能验收，不重复旧小模型数值测试。图唯一一次仅读保存数据、外层120秒；事后核查仅读，不新生成参考。通过后main交付及一次公开CLI恢复范围按实际成本决定。

图显示实际x1结构、另附x1000位移、公共N箭头标尺、全部attached支承、其余fixed stride3、全3200单元J；三个输入ux与加权均值、输入R及输出q_out各自轴、物理输出weighted ux=−q_out、独立残量/平衡与minJ。帧仅真实接受态，无插值；正J不等于接触压力，无工件小TEST不构成夹持力/完整行程/研究H2-H3或HF5标签资格。更长路径依两例结果再选，不预先细化所有后续卡。截至本段为静态计划和新文件编写，未启动pure prepare、模型/force/tangent/solver/HP/plot。


### 纯数据准备实际完成

prepare_inverter.py唯一执行exit0，约1.965秒，仅保存新task／direction／zeroL／inventory，0model／force／tangent／solver／HP。新task TEST_native_mean_inverter_0001_20261003 SHA d0f898b2f44dce4d2928ade24f3a1b63d8ba367242cf2d673d065e6786f67f8c；direction文件177124bd、zeroL fbfe6d9d；原任务物理字段逐项保持，显式输入0→.001mm。图的参考保存文件SHA纯读取补充在正式执行前完成；接受态数量与动画按实际N读取，合法二分态也覆盖。新源码尚未运行力学或绘图，正式生产等待最终静态37来源冻结。


### 正式执行前最终来源冻结

root已实际复核旧33source字节全相同、真实七输入SHA、37来源完整／平铺basename唯一，四新源AST/compile通过；来源closure的22本地模块静态交叉审查与旧入口相同。新checker直接继承旧run_state，viewer已对实际N帧及全部保存audit payload绑定SHA，无执行前阻断。

hf_repo/scripts/audit_native_mean_inverter.py SHA 63fbd68560d2e2b2f129d36ca160678b726085ab90f5f7a70933db854a4833b4
hf_repo/scripts/plot_native_mean_inverter.py SHA 0e030174da8e5bbf63f1df48b0211576c9edce713a539ec094dafa7680676f8a
lf_data_preparation/native_inverter_mean_001/prepare_inverter.py SHA c5348652d50194044d216854fd1f7c8e086e7fc7559c8adf9d8e7e58e364b546
lf_data_preparation/native_inverter_mean_001/execute_inverter.py SHA 73f24de2461ee171d1be03c8154a9497f07bc2f4b0ccc3c182fb511f18ed1be2

新inventory SHA fd578d9ba3451e83c43b03daccb2f628b722f81cdcd19595efa4f864836c11a4；这张新case生产/参考各180秒／采样8GiB、外层各210秒，图仅读外层120秒，原门／设置保持，旧窗口不重开。现在启动唯一生产，第一阶段错误停止；此行写入时0新model／force／tangent／solver／HP／plot。


### 实际求解与独立参考结果

[静态交叉审查](../lf_data_preparation/native_inverter_mean_001/static_review_inverter.json) 9f139d16确认37来源/旧33/22模块闭包、七输入、89fixed/+x/−x、新包装及原门；这是静态记录，未增加数值资格。root在生产前另实际核四源SHA及七输入/old33。新source与图/数据保持冻结。

唯一[生产回执](../lf_data_preparation/native_inverter_mean_001/execution_receipt.json) SHA 64fb6336f61a7253b5fe411efa84a82661c869d09367220d0697d4528e005e90：pass，57.8509754秒，外层58.5055498秒，采样RSS/Windowspeak 740.82812MiB，2接受态、4完整force／3三分量tangent／1solver，0JIT／HP／LF。原model23字段逐字节不变；初始切线预测＋一次完整factor1 Armijo Newton修正，2次非对称general sparse LU，无二分或failed_attempt。API评价55.4086841秒，kernel55.2439794、CSC assembly .0145641、sparse .1015934秒，主要成本仍为切线核。此粗例实测不保证一般细网格成本。

唯一[独立参考](../lf_data_preparation/native_inverter_mean_001/audit/summary.json) SHA a0d468d608b9515d13b8417f08c2291654a3256f93d99bb1e243f9cf0a1e553a：pass，summary40.9159965、lifecycle40.9169366、终端40.9173372、外层41.4342377秒；采样322.28125MiB。2态4新HP80/120调用覆盖3200单元／6642DOF／12800 element-precision instances，共153600局部力和153600局部Jv标量、409600局部矩阵系数的全量组装核对。38655 checks含身份核对；实际物理门38400局部＋18global/CSC/KKT＋48scalar=38466，不能用总checks或仅读复核数增加物理门。

| 两态最坏归一化误差 | 总 | 材料 | HuHu |
|---|---:|---:|---:|
| 单元力 | 1.00425e-16 | 9.55783e-17 | 1.30563e-16 |
| 全域力 | 1.16434e-15 | 2.11153e-16 | 1.46452e-16 |
| 单元Jv | 8.38627e-17 | 6.10587e-17 | 2.20356e-16 |
| 全域element-scatter Jv | 5.34357e-17 | 4.79835e-17 | 1.38795e-16 |

CSC总作用最坏1.04798e-16，KKT自由力方向1.05831e-16、均值方向0；原门全部保持。全部局部HP80/120一致最坏4.40426e-73，不是只选候选最坏条目的参考误差。6642×6642总CSC／116644存储nnz保留所有fixed行列和非对称性；HP导数独立资格仅原声明v方向，不称全部矩阵列通过。

| 末态实际物理量 | 数值 |
|---|---:|
| 加权平均输入 [mm] | 0.001 |
| 输入+x总驱动力 R [N] | 0.0001698726729304546 |
| 输出参考−x 均值 q_out [mm] | 0.001601920368560766 |
| 实际输出平均 ux [mm] | -0.001601920368560766 |
| 最大节点位移模 [mm] | 0.001627388470833483 |
| 实体积分点最小J | 0.9999769532457247 |
| 介质/全域积分点最小J | 0.9999093951242075 |
| 独立自由残量 | 8.728594662358681e-12 |
| 独立均值约束相对误差 | 5.421010862427522e-17 |
| 独立外力平衡相对误差 | 4.329611375098013e-15 |

actual input三个ux分别0.0009906721121596279／0.001002009388630091／0.00100530911058019mm，权重.25/.5/.25只约束均值，不绑节点等值。输入+x微运动得到真实output−x响应，小步输出/输入比1.6019203686；q_out是原b_out·u，没有再翻号。输入R是执行器对模型力，无弹簧/工件，不能称夹持力。fixed位移精确0，全部J接近1，当前显示自由小变形；并未展示完整行程或介质压薄接触。

[实际图](../functional_views/native_inverter_mean_20261003/native_mean_path.png)、[真实两帧动画](../functional_views/native_inverter_mean_20261003/native_mean_path.gif)、CSV及metadata共6件保存；唯一仅读图回执2.5703003秒，0新model／force／tangent／HP／solver。x1主结构显示输入／支反力，补充只位移x1000，无力箭头；common最大节点外力0.000383197967619N=4显示mm，显示箭长不是结构位移。legend已移出几何，R与q_out各自独立轴，物理ux=−q_out明确列数；全3200单元J色为九点均值，min取全部积分点、J不是压力。只有0和.001两真实帧，连接线不构成完整连续曲线。核心／旧测试字节不变，本次不重复旧小模型测试，实际第二机构及新HP承担功能验证。

普通文件链路已在夹爪和反向器两类接通：LF v2纯数据→HF几何→明确native任务→NumPy完整力／非对称CSC切线→平均驱动平衡→实际响应图。生产三资格flags保持false，独立audit声明小粗TEST通过，不升级HF5／H2-H3／一般接触或完整任务。

### 普通使用、交付与下一功能阶段

完整clone根及独立HF环境中，使用新输出目录：
```
python hf_repo/scripts/solve_native_mean.py --geometry lf_data_preparation/v2_adapter_001/converted/inverter_canonical/geometry.json --task lf_data_preparation/native_inverter_mean_001/task.json --output my-inverter-mean
python functional_views/native_inverter_mean_20261003/plot_native_mean_inverter_frozen.py --input lf_data_preparation/native_inverter_mean_001 --output my-inverter-view
```
普通CLI执行task明确目标；读取冻结参考图不再求解。新viewer验证历史双来源胶囊和全部保存参考payload，current源匹配只作信息，以后活动源码变化不会改变冻结证据身份。完整Git根和runtime必需；旧媒体保持原图及旧读法。

根据本例实测57.85秒，main交付后计划公开干净clone一次同TEST普通CLI复现，180秒／采样8GiB、外层210秒；新helper replay_public_inverter.py 8fef6235已静态互审，复用旧纯比较函数，不改原37sources。完整23＋27N数组与payload字节精确比，result/state JSON仅排原明确实测时间及关联hash，全物理/设置/调用计数/Newton/Armijo/LU/资格保留；图另一次保存数据读回，外层120秒，6件比较。0新HP、同机异目录恢复不能当跨机性能或新物理验收。现正式生产／参考／图窗口已执行完毕，事后审核均仅读，不重开。

下一唯一近期功能选择**反向器原构造TEST目标.025mm，明确targets[0,.005,.010,.025]mm**，完成普通数据任务的较长前缀而不再扩无目的微步；随后依结果决定夹爪对应任务。保持native h1/材料/89fixed/+x input/−x output/free spring及原门，无工件；新task保留原.025作为显式TEST，绝不把它称正式研究行程。新stage和全部新的实际接受态、source/input绑定、每态HP80/120全模型以及真实N帧图。依据两小步约18秒/T和约10.5秒/HP预计4态7–10T约130–190秒生产、8HP约85秒参考，提出一次生产300秒/8GiB、一次参考240秒/8GiB、外层330/270秒；导入/所有原有有界Newton试探/保存/endpins包含，原gate/scaling/Armijo/二分规则不改，第一阶段错误停止，无修复重试或借余钟重开。这是下一阶段预算计划，尚未准备/执行；结束后再按实测细化近期路线。原task.001与全部冻结证据不回写。完整研究行程、真实工件/夹持力、释放重入、H2分析网格/H3定义和HF5批量比较仍未实现，整体goal active。


### 保存态事后复核与关账

[独立保存态核对](../lf_data_preparation/native_inverter_mean_001/postrun_identity_review_inverter.json) 33c13273：37 current源＋两胶囊111件、7输入、23model＋两态27字段=77数组、4原HP文件／全部参考payload、模型／力／方向／source及计数闭合；38466项已保存门字串finite／原阈值／pass／<=limit逐项核对。78234是保存数据检查项，不计为新数值门。未重新求Decimal门或HPscatter，0新model／force／tangent／solver／HP／test／plot。实际4/3/1及0新保存调用保持。

[实际图像交叉审查](../lf_data_preparation/native_inverter_mean_001/visual_review_inverter.json) 8f4f67a4：另一作者实际查看2880×1840 PNG及1680×882 GIF的两原帧，164文件SHA before/after与20参考payload绑定一致，CSV/metadata和NPZ、exact Fraction均值／physical ux=−q_out相符。四实体支承节点405/486/567/648均显示；实体支反力合计(-.0001698726729304567,-.000029949646186834165)N，otherfixed(0,+.000029949646186836177)N，input(+.00016987267293045455,0)N，完整平衡一致。legends无结构遮挡；邻近反力glyph可重叠、otherfixed按stride3显示、输入三曲线微差接近、GIF无数值J色条、两点连线不作连续函数证据等局限保留，PNG与数表供精确审查。0新图／数值计算，源和媒体未改。

本例唯一正式生产／新HP／图窗口完成关闭，未重跑旧功能测试。接下来依既有main提交/推送授权，交付必要普通数据、完整新参考、源码、图、执行过程和恢复说明，并按已写范围仅一次公开同小TEST恢复；当前无阻断，整体目标仍active。


### main交付与实际公开恢复

科学实现、两态求解／4新HP／真实图及两路事后核查已提交推送main **b86cd1db9d45595d4bed63c43b727cd0ce4fddf9**。origin保持https://github.com/dudaxing/Compliant-TO-TMC.git；公开clone D:/hf-restore-20260930仅fetch＋fast-forward，5896交付文件身份verify通过，science manifest SHA2d1fd3cebb64bbbc9af0b691b57ceaeb160d7a280a2c67c8e163423c635fdde8。必要模型、所有完整新参考、源码、图与过程记录均随普通Git，不需原目录或Release才能读本次。

[实际公开恢复证明](../handoff/native_inverter_mean_20261003/public_recovery_verify.json) SHA b6935fe55112df2ce558c7feaaa2e94524e376433503d42eb948671ef964ab60：公开一次普通CLI 61.2949845秒、外层61.5714616秒，采样child-tree 721.67969MiB、wrapper＋child 757.48828MiB，在180秒／8GiB窗口内。12 payload原字节和77数组dtype/shape/Cbytes相同，2state JSON/result除原明确耗时与关联descriptor hash外全部类型/数值一致，物理/设置/4force3tangent1solver调用数/Newton/Armijo/LU诊断/资格均保留。不是整个JSON字节相同；实际CLI log、两state JSON/result及回执随证明保留，不覆盖正式输出。

冻结viewer一次仅读Git保存数据 2.3021639秒，PNG／两帧GIF／CSV／脚本／helper／metadata6件字节相同，0构造／force／tangent／solver／HP。公开clone计算前后干净；输出位于clone之外。正式与公开共8force/6tangent/2solver，新HP仍原唯一4调用，本次未重跑小模型测试。此为同机同runtime异目录恢复，不称另一机器性能、一般接触或完整行程验收。原7输入／37source／原task/model/state均保持；本阶段执行窗口关账，恢复证明与本记录另提交main。下一唯一近期功能仍为上段明确反向器[0,.005,.010,.025]mm TEST，尚未开始准备或求解，完整研究任务与HF5目标仍active。


<a id="native-inverter-task025-20261003"></a>
## 普通反向器明确0.025mm TEST：执行前近期计划

上一goal turn属于**实质进展**：main163db2508946aea2e3c9948745ff13813ee98d1d已交付普通反向器.001mm两态／4新HP／图／实际异目录恢复，补齐两类普通机构的力→组装→非对称切线→均值平衡链路。当前正式Git root已实际核对：main干净，origin为https://github.com/dudaxing/Compliant-TO-TMC.git，fetch后0/0。没有活着的数值job需要等待；旧唯一执行窗口全部关闭，整体HF目标仍active。

本轮唯一详细阶段接上一报告：原构造任务的**明确TEST target .025mm，targets[0,.005,.010,.025]mm**。目的是完成普通数据任务的较长前缀，观察输入反力／反向输出／非线性Newton及J随位移的实际变化，先建立可用功能。不是一般接触/研究完整行程/工件夹持资格，不自动采用H2网格或H3定义，不生成HF5标签，不导入/安装/调用LF优化器或MPM。

原80×40mm/h1、t20mm、E1MPa/nu.3、gamma/alpha1e-6、Lr80mm/kr.008615384615384613、89fixed/6553free、1128实体/2072介质、+x输入b_in权重(.25,.5,.25)、−x输出b_out权重(−.25,−.5,−.25)、k_out0/no workpiece保持。源geometry23adf44e/1911362e、prior task5d488f27、prior model23字段321a10e0绑定；新task采用既有task_id显式TEST，不添核心不支持的字段，物理input target本来是.025。zeroL、undeformed初态及v=b_in/maxabs/δR0与上一阶段一致。

**实施取舍**：native_mean API/CLI、核心公式/控制器、原33source不改；新增stage native_inverter_task_025_001/的纯准备和执行薄包装。活动inverter checker/viewer泛化显式已登记stage/task目标、原物理身份和实际接受态N，直接继承冻结CoreAudit.run_state及原全部数学门，避免再复制一套检查器/绘图。旧37胶囊/旧冻结viewer/旧输出/图/任务/包装不回写；历史reader核双胶囊/参考payload，current来源只记录信息，因此新局部wrapper改进不伪造历史身份。新source39=原33＋原四inverter包装的当前版本＋新增2unique文件，静态全文/AST/compile/源闭包和实际输入先核后冻。新stage与所有新输出目录，所有每态缓存payload、真实calls和source/input/endpins保存；不借旧.001接受态作为本次新路径初值或参考。

**方程、原门与控制**：free(f_int−b_in R)=0、b_in·(L+w)=d，q_out=b_out·u（physical weighted ux=−q_out），L=0；通用非对称LU/增广CSC原样，forceN、K/Jv N/mm、u mm。tolerance1e-9、constraint1e-10、scale_floor1e-6、forcefloor1e-8、maxchecks25、Armijo1e-4/backtracks12/bisections4全部原值。minimum_increment**明确仍6.25e-5mm**，不会由首目标.005自动变成.005/16。此下界和最大四次二分共同约束原算法，二分帧也全部保存与审计，不新增失败修复循环。

继承全部gate：总force1e-11、材料/HuHu1e-9；局部SF_e用各自HP力norm及原物理floor，global用原方程尺度，分量自身norm/1e-12SF；Jv各自norm与1e-10 floor，总1e-10/分量1e-9；HP80/120一致1e-40；生产残量1e-9、独立1e-8、force_evaluation1e-9、mean1e-10、globalbalance1e-6、fixed8e-11mm、KKT两方向1e-10均原样。每新实际接受态HP80/120各一次全3200单元/6642DOF、精确Decimal/Inexact scatter，正常4态8次HP=25600 element-precision instances，二分时按实际2N；全部2split/17force/3tensor/总CSC/全精度raw参考及门保存。所有矩阵系数组装逐项核对，独立HP导数范围仍只有声明v方向，不冒称全部矩阵列。

**执行边界**：本轮新生产一次连续300秒／采样8GiB、外层330秒；新参考一次240秒／采样8GiB、外层270秒。依据两小步约18秒/T、10.5秒/HP估计4态7–10T约130–190秒、8HP约85秒；成本估计不是保证。第三方imports、全部原有有界试探、HP、serialization/endpins包含在各自时限，第一阶段错误停止，无修复重试/force/借余钟重开。API异常返回前调用计数None，不猜0。原数学与功能测试不变，本次真实较长路径+全量新参考担任功能验证，不再跑重复小模型测试。纯准备只std/NPZ数据0physics；正式通过后新图一次仅读，外层120秒，保存态事后审核0新HP/solve。main交付及一次普通CLI公开恢复依实测成本另写范围后执行，旧复验卡不重开。

图保留真实x1结构/公共N箭头标尺/attached四支承全显示和otherfixed stride3/全3200J；另补充**仅位移x40**并明确无力箭头，使末输入显示约1mm，避免较长路径沿用x1000导致错误观感。R/q_out独立轴、所有实际输入节点ux与均值、physical ux=−q_out、独立残量/forcebalance/minJ全数表、真实N帧无插值。J色为每单元积分点均值，min取全部积分点，J不是接触压力；完整x1与forceN数字是主要物理依据。

完成条件：明确.025目标真正成功，全部实际接受态覆盖/原门通过，源/23model未改、cache保存0额外求值与实际attempt/completed计数相符，图与数值方向/尺度一致，新普通CLI可复现、必要数据/上下文/过程随main。若某阶段不通过保留已发生状态和失败证据，先定位具体问题，不自动更换物理任务/阈值。之后只按这轮实测结果选择夹爪对应目标或发现的阻断修复；更后路线保持粗粒度：明确普通任务→较长/细模型能力→带明确定义工件的功能→一般接触与批量研究输出。本段写入时0本轮新prepare/model/force/tangent/solver/HP/plot。


### 纯准备实际结果

prepare_inverter_task.py唯一pure执行通过，prepare_launch_receipt.json 0.5122579999733716秒；0构造／force／tangent／solver／HP。实际new task全部物理字段包括原input target .025mm与prior逐项相同，只更新现有身份／说明字段；新inventory及task_id显式标识测试范围。显式min6.25e-5mm、prod300/ref240/8GiB与outer330/270、图120保持先前计划。

task.json SHA 6e737cb17f67aa79d25ea25da8018eebebb47cec1b8dcaf03e8beb2deef0958d
direction.npz SHA 177124bd1968f9e451e59cba4d7124c393eb8fee15cc93851f570f980aada29a
lifting.npz SHA fbfe6d9d1e77aa541991d1f0124a596d7a9574b720eb0e4ac5dbf851fcf1d465
input_inventory.json SHA b10a445dfe1a87dbd79073b9edc4e9aaa2395425d85ea4d69909da74dadf1af8

正式来源等待最终39源静态交叉冻结；本段写入时仅产生四纯输入及prepare回执，未开始新模型／力学／HP／图。


### 正式执行前最终来源冻结

root实际核old33当前字节完全相同、39来源覆盖／basename唯一、四新/修改源AST与compile、实际七输入SHA及新inventory b10a445d。各作者静态交叉核真实inventory/task和原物理、继承run_state/原门、target/budget/timer/所有接受态、viewer−x语义均无阻断。旧001冻结viewer350/0e030174保持；不重跑或重写历史数据。

hf_repo/scripts/audit_native_mean_inverter.py SHA 9491d18e76d3acd15feabe61fae5f789a3df69a00151333420624a8e493fafbc
hf_repo/scripts/plot_native_mean_inverter.py SHA a8708f4c9ca857a3a225d7fa07f52c376f9b52b980de1055a34b9a5128362e8b
lf_data_preparation/native_inverter_task_025_001/prepare_inverter_task.py SHA 13e01f4144096bb5cb3add7150d8b350834b4236d4a1c1bab90e83a14ec43f44
lf_data_preparation/native_inverter_task_025_001/execute_inverter_task.py SHA f9a7f80814dc3b4fa34fe42a972d3ea1dfe1c2681593b72d9a2c4443d5488f51

本段写入时0本轮新model／force／tangent／solver／HP／plot；现在启动既定唯一生产300秒/8GiB/outer330，随后仅pass时新参考240/8GiB/outer270与保存读图120。source/input固定，第一阶段错误停止，无修复重试/force。


### 实际求解、独立参考与可视化结果

唯一正式生产 exit0/pass：[执行回执](../lf_data_preparation/native_inverter_task_025_001/execution_receipt.json)，169.1223799秒，outer169.4130299秒，Windows峰/采样804884480 bytes（767.59765625 MiB），300秒／8GiB内完成。四目标全部接受，14完整force／9tangent／1solver；三初预测＋五Newton修正均一般非对称LU，五Armijo试探全部factor1，无二分／失败尝试／修复重试。完整结果保存17 NPZ包／131数组（23模型＋每态27）与四状态JSON，保存0额外force/tangent；旧23模型dtype/shape/raw bytes及七输入、39source endpins保持。

API评价165.7036154秒，其中内核及transfer165.1956005、CSC组装.0369986、稀疏求解.3366985秒；主要成本仍在元素切线，不由稀疏LU主导。这是当前粗3200Q1/6642DOF任务实测，不能按四倍单元直接保证细网格总耗时。

| 实际平均输入 d [mm] | 输入+x驱动力 R [N] | 输出参考−x q_out [mm] | 独立HP自由相对残量 | 全域积分点最小J |
|---|---:|---:|---:|---:|
| 0 | 0 | 0 | 0 | 1 |
| .005 | .0008494641904889284 | .008011202128388739 | 7.29149e-13 | .9995470060502105 |
| .010 | .001699180585920530 | .01602640517581522 | 5.44071e-10 | .9990940881881588 |
| .025 | .004249845332071079 | .04009602327735562 | 7.77440e-13 | .9977357913691891 |

[新独立审计](../lf_data_preparation/native_inverter_task_025_001/audit/summary.json) exit0/pass，4态8新HP80/120完整3200单元／6642实际DOF；25600 element-precision instances，全部局部force/Jv 307200项各、完整204800系数组装×4，全部原门保持。77165检查包含身份；数值门另据保存后验回执计数。summary96.0028437秒、lifecycle96.0047247、terminal96.0051970、outer96.5100915秒，peak338907136 bytes（323.20703125 MiB），240秒／8GiB内。没有候选复算或新求解；继承旧run_state及原gate，独立导数仅v=b_in/maxabs、fixed lift、deltaR0方向，全CSC组装逐项检查不等于独立HP遍历所有矩阵列。

| 全路径最坏归一化误差 | total | material | HuHu regularization |
|---|---:|---:|---:|
| 单元完整力 | 1.02298e-16 | 1.01313e-16 | 1.40388e-16 |
| 全模型scatter力 | 1.18321e-15 | 2.19940e-16 | 1.40607e-16 |
| 单元Jv | 8.09029e-17 | 7.65676e-17 | 2.09760e-16 |
| 全模型scatter Jv | 6.47459e-17 | 5.32812e-17 | 1.15331e-16 |

CSC总作用最坏1.04798e-16，KKT自由力方向1.05831e-16、均值方向0；全部局部HP80/120一致最坏9.34152e-74，原1e-40门保持。四状态固定位移精确0，独立残量最高5.44071e-10、均值相对误差最高4.33681e-17、外力平衡最高3.41260e-13，均低于原门。生产独立资格flags仍false；本次audit声明上述具体粗无工件TEST范围通过，不提升研究资格。

末态actual output ux=−.04009602327735562mm，最大节点位移模.04073084846568401mm；solid Jmin.9994237666409495、medium Jmin.9977357913691891。输入三ux .02476668560670649／.02505026067771577／.02513279303786196mm，仅weighted .25/.5/.25均值为.025，不是节点绑等位移。输入是执行器对模型的力，free output spring0/no workpiece，不能改名夹持力。完整外力ΣFx=−1.73472e-18、ΣFy=−1.25767e-17N，按原下半模型不乘二。

**物理效果与取舍**：由此前.001保存数值和本次.025实际值仅读比较，位移比q_out/d由1.60192037至1.60384093，提高约.1199%；割线输入刚度R/d由.169872673至.169993813N/mm，提高约.07131%。较长TEST仍近线性自由变形，背景J仅轻微变化，并没有展示薄介质强压缩或真实夹持。这一结果支持继续同入口接夹爪对应原TEST；不需要为本次成功改机械公式、加稳定补丁或重跑旧小模型测试。

[实际图](../functional_views/native_inverter_task025_20261003/native_mean_path.png)与[四实际帧动画](../functional_views/native_inverter_task025_20261003/native_mean_path.gif)及CSV、metadata、冻结viewer/helper共6件保存。唯一仅读plot3.7094957秒，0构造／force／tangent／solver／HP。主结构位移x1，补充位移x40无力箭头；全部外力使用公共标尺最大节点力.00957719400391484N=4显示mm。J色为全3200单元九点均值，数值min用全部积分点；R和q_out各自独立轴，physical ux=−q_out、支承全四节点、otherfixed stride3明确。四点连线/四帧只对应真实接受状态，无补造连续路径。root实际查看PNG并打开；其他作者继续仅读保存态与实际四帧审阅，source39/媒体不回写。

本阶段实际功能链为普通文件→明确原TEST模型→NumPy完整力/三切线与full CSC→split均值非对称增广平衡→带单位与方向的实际输出。较长原构造目标已执行；HF3原1mm完整行程、新细网格普通路径、工件/真实夹持、一般释放重入、H2/H3正式定义和HF5批量评价仍未完成。整体目标active，下一段根据本结果只详细规划最近夹爪阶段。



### 下一唯一近期功能：普通夹爪原0.025mm TEST

本轮反向器已达到原构造TEST而且全部新参考通过，因此下一步使用同一普通文件链路完成**粗夹爪[0,.005,.010,.025]mm**。不再扩重复的微步验证；优先得到另一类机构的实际输入力和自由钳口运动，随后依据两例成本决定细网格或原研究行程前缀。本段是执行前计划，本轮尚未创建或运行夹爪新stage。

输入为现有v2_adapter_001/converted/gripper_canonical的原geometry、native_model_001/tasks/gripper_canonical.json及其23字段prior model，原目标本来.025；新task只显式TEST身份/说明。80×40mm、h1、t20、E1MPa/nu.3、gamma/alpha1e-6/Lr80、87fixed/6555free、+x输入加权均值和+y自由输出、k_out0/workpiecenull、原实体附着支承与全部背景top uy保持，不借反向器状态/参考或旧夹爪.001状态作本次初态。zero lift/origin，未变形初态；所有值以实际准备逐SHA/字段核对后冻结。

实施仅新增唯一stage纯准备/执行薄包装，并扩展已有明确stage checker合同，**继承原CoreAudit.run_state和全部原数学门**；已有通用viewer已能区分inverter−x/gripper+y，复用真实N状态及共享力标尺的读法。核心native_mean/CLI/原33源、公式、默认内核、严格依赖不变，不复制整套数学审计/绘图。历史胶囊/参考/media不回写；新来源集合及unique basename在执行前依据真实依赖冻结，任何旧source identity变化均不迁入旧资格。

唯一生产300秒／采样8GiB、outer330；pass后唯一新参考240秒／8GiB、outer270；pass后唯一仅读图outer120。依据本轮9T/169秒、8HP/96秒估计相似粗任务可在这些界内，不保证其Newton数相同。tol1e-9/mean1e-10、scale floors、Armijo/backtracks/maxchecks、maxbisections4和minimum_increment6.25e-5原样，包含imports、原有所有有界试探、存储/endpins；首阶段错误保存并停止，不修复重试/借余钟重开。全部实际接受态2N次新HP80/120，全元素/DOF/raw references、原force/Jv/80-120/平衡/均值/固定门；所有CSC系数组装与声明v方向验证，不称全列独立导数。

完成条件为原.025目标真正到达、原模型物理/源绑定准确、全部新门通过、真实响应图/CSV及可恢复CLI/必要资料随main。图仍x1实际结构，补充位移x40明确无力箭头；input+x、output+y标注，只约束均值不绑节点，support箭头和全部J、独立R/qout轴、全部N帧、数值残量/balance/零spring明确。output+y是自由钳口运动，无工件不能称夹持力；完整行程、H2/H3、一般释放重入、批量HF标签保持未完成。新小模型测试不重复，真实第二机构较长路径+全量新参考承担功能验证。main交付与公开恢复按实际成本另冻结。

更后路线保持依赖层次：两粗机构原TEST完成→现有细候选的对应能力/明确较长任务→确定工件与测力协议→最小参照和一真实夹持案例→少量同任务候选比较与必要网格/参数试验→HF5研究输出。每一步由实际结果修改下一步，HF始终独立正向评价，不实现LF优化或MPM。



### 保存数据后验与实际审图关账

[静态审阅](../lf_data_preparation/native_inverter_task_025_001/static_review_inverter_task.json) SHA51160d50已核实际输入、39来源闭包、原33字节和预算。正式求解/参考/图之后，[保存态核对](../lf_data_preparation/native_inverter_task_025_001/postrun_identity_review_inverter_task.json) SHA4d09f659核39 current+producer/audit双胶囊、七输入、23＋4×27=131字段、四态与调用日志、8完整HP原始payload及40参考payload、所有76932条保存数值门记录和153768次保存error/limit比较；77165是正式审计含身份总计，不把保存核对次数当新增数值门。只读取已有字符串/数组/哈希，没有重算全部Decimal门/scatter或新增model/force/tangent/solver/HP/test/plot。

[实际图审](../lf_data_preparation/native_inverter_task_025_001/visual_review_inverter_task.json) SHAa5be56a1：另一作者实际查看2880×1840 PNG和全部四个原GIF帧，4×1000ms无插值；160文件SHA before/after、39双caps、40参考payload绑定、CSV全列/NPZ端口均值、forcegroup/Jrange一致。attached四支承均显示；末support合力(-.004249845332071081,-.0007477687766321631)N、otherfixed(0,+.0007477687766321499)N、input(+.004249845332071079,0)N，完整平衡相符。x1/x40/共享N标尺、外legend/两独立轴/−qout可读。保留局限：真实位移仍小、放大仅显示；邻近支反力glyph可重叠、otherfixed stride3、输入三曲线微差接近、GIF无定量色条，PNG与数表作为精确读数依据。0新physics/plot，源码/媒体未改。

本阶段唯一正式生产／新参考／读图窗口关闭；没有重跑旧测试或力学公式，结果明确支持上述下一夹爪功能阶段。此后按既定main交付授权保留全部必要原数据、完整参考和过程记录，公开恢复仅按事先冻结范围一次执行；整体目标仍active。



### 公开异目录恢复：执行前具体范围

本节只登记恢复前计划，不记录已执行恢复。依据本次唯一正式生产169.1223799秒、四态[0,.005,.010,.025]及14完整force／9三分量tangent／1solver，当前执行卡另允许公开干净clone中**一次恢复，内部连续300秒／采样8GiB、外层330秒**；导入、来源核对、CLI全部原有试探、保存、全部payload比较、endpins及回执serialization均计入内部窗口。外层余量用于终止与收尾，不增加计算额度；这是协作计时／RSS检查，不是OS内存硬上限。0新HP／JIT／LF导入，原正式生产与参考窗口不重开；第一项错误停止，不修复重试，不覆盖已有输出，不强杀重跑。

新helper [replay_public_inverter_task.py](../handoff/native_inverter_task025_20261003/replay_public_inverter_task.py) 318行，SHA feab07cc76331f0b58ccd0ffd4a09116075b7412f54a37de81d8914c9f42942f；复用冻结9cdd3f6a纯比较函数，历史8fef6235恢复脚本与核心39source原字节保持。AST／compile与实际保存schema、七正式文件pin、current／生产与audit双来源胶囊／所有输入、40完整参考payload SHA静态读取核对通过；这不增加数值门或新物理资格。helper启动前必须确认本次正式生产及独立audit／lifecycle／外层返回均pass，绑定真实inverter／89fixed／原23模型／新TESTtask／四目标／实际14-9-1调用／四态身份和原8次HP结果；缺失或身份变化即停。

在完整公开clone根、同一已配置HF环境，用**clone之外且此前不存在**的新目录，例如：
```
python -B handoff/native_inverter_task025_20261003/replay_public_inverter_task.py --output D:/hf-native-inverter-task025-replay-20261003
```
helper唯一启动的普通入口仍为 solve_native_mean.py，显式传原geometry及本stage task、新output/result、`--targets 0 .005 .010 .025 --minimum-increment 6.25e-5 --time-limit 300`。其余数值选项与正式设置逐项相同，不能用默认[0,tasktarget]省略中间态，也不能由首目标.005重新计算最小增量。已有输出路径直接停止，无自动换目录再执行。

恢复后核**23＋4×(2 split＋17 force＋3 tensor＋5 CSC)＝131数组**的dtype／shape／C-order bytes，以及20份模型／源快照／接受态NPZ payload原字节。所有state/result JSON只用冻结normalizers排明确实测时间及因此变化的descriptor hash；目标／材料／边界／全部物理量／14-9-1计数／Newton／Armijo／LU残量诊断／资格全部保留并递归精确比较，不称result JSON整文件字节相同。正式source39、输入、完整参考保存文件与helper依赖前后均核SHA；不重算HP门。记录生产子进程自身采样RSS及可用Windows working-set peak、child-tree和wrapper＋child-tree采样峰值、命令／日志／实际state身份和比较回执。错误时仅一次terminate已观察子树并等待、保存仍存活成员，外层330秒监督收尾；没有恢复循环。

这只验证同机同runtime的公开clone异目录恢复，不能当另一机器性能、HF5／H2-H3／一般接触或完整研究行程验收。本节写入时0本次公开CLI／新force／tangent／solver／HP／test／plot；root将在提交与公开来源复核后才执行这次恢复，并另追加实际结果。


公开CLI通过后，仅一次**冻结viewer仅读恢复**（outer120秒），明确传与原图一致的倍率：
```
python -B functional_views/native_inverter_task025_20261003/plot_native_mean_inverter_frozen.py --input lf_data_preparation/native_inverter_task_025_001 --output D:/hf-native-inverter-task025-public-view-20261003 --magnification 40
```
新输出位于clone外，检查全部6件PNG/GIF/CSV/metadata/viewer/helper字节，0新model/force/tangent/solver/HP。不使用默认1000倍率，不启动新正式参考。完整普通CLI使用上述四targets/minimum-increment300秒命令；实际日志/4stateJSON/result/恢复receipt另随证明保存，数值payload已存在正式Git，不再复制大数组包。正式和公开计算前后来源保持且clone干净；manifest建立、验证、main提交/推送及公开fast-forward都按真实终止结果顺序执行，未完成程序不能提前宣称交付通过。


### main交付与实际公开恢复

科学源码、完整四态及8新HP、真实图和独立核对已提交推送main **1419427f4fe45ccfaed8142ffa27a6b5dea57f2a**；origin保持https://github.com/dudaxing/Compliant-TO-TMC.git。公开clone D:/hf-restore-20260930由163db25仅fetch＋fast-forward到此提交，main/clean/HEAD实际核对；6077交付文件身份verify exit0/pass，science manifest SHA18f0bf187f5c2d31bbd7aae0958aa416979f8d2ff97b54887073e0b30206781d。本次必要普通输入、全部模型/状态/三力/CSC/raw新参考/来源/图/过程说明随普通Git，不依赖原盘符或Release读取这些结果。

[实际恢复证明](../handoff/native_inverter_task025_20261003/public_recovery_verify.json) SHA491af2749d7212f7260285d319ffefaaf83c39ff7e3c3c25975e864aa84ec2fd：公开一次普通CLI184.7927093秒、外层185.0445906秒，采样child-tree750.359375MiB、wrapper＋child-tree787.125MiB，300秒／8GiB内。20数值payload文件字节精确相同，131数组dtype/shape/raw bytes相同；四state JSON及result仅排原明确实测时间与关联descriptor hash，全部物理/设置/14force9tangent1solver计数/Newton/Armijo/LU/资格类型与数值保留。不是整个result JSON字节相同。实测Popen根PID的RSS/Windows peak另仅4.6875MiB，排除后代进程；该root-only读数不能代表整个求解器，资源判定用包含后代的完整树采样峰。本字段范围已在proof注明，raw receipt不回写，不因附带遥测读数重开物理实验。

冻结viewer唯一仅读公开Git数据2.7486531秒，x40明确参数、四帧GIF/PNG/CSV/metadata/reader/helper全部6件字节相同；0model/force/tangent/solver/HP。实际CLI log、4stateJSON/result、replay receipt及两outer receipts随proof保存，公共大数组不重复复制。公开计算前后clone干净，输出在clone外；同机同runtime异目录恢复不冒称另一机器性能或新物理验收。正式与公开本阶段共28force/18tangent/2solver，HP仍原唯一8调用，无重复小模型测试，全部source39/原23模型和task输入保持。

本阶段生产／参考／读图／公开恢复窗口完成关闭，恢复证明及本记录按既有main授权另交付。整体目标仍active；下一夹爪原.025mm TEST已写执行前近期计划，**本轮没有创建或执行它**。补充只读核对确认gripper prior model与其旧.001模型23字段字节相同，实际87fixed/6555free、输入+x DOFs[6156,6318,6480]／.25,.5,.25、输出+y DOFs[4697,4859,5021]同权；其87约束来自3实体支承节点ux/uy6＋原显式TEST全top uy81。下一checker必须绑实际gripper geometry/task/model和+y符号，不能沿用inverter pins/89fixed/−x；fulltop来自task.background_symmetry，不由LF provenance (60,80]自动施加。原材料、min6.25e-5/no workpiece/zeroL/下半不翻倍与H2/H3待定均保持，300/240界有本机成本依据但不保证其Newton数。
