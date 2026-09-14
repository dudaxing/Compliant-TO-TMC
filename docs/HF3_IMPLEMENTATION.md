# HF-3 实现说明：真实几何、平均位移控制与独立精度接口

2026-09-14。本文记录当前代码实际实现及其验收接口。执行范围来自 [HF3_EXECUTION_PLAN.md](<../../docs/HF3_EXECUTION_PLAN.md>)，计算前的比较点、容差与资源上限来自 [validation_spec.json](<../configs/hf3/validation_spec.json>)。本文不是验收汇总，不根据文件已经生成或生产求解返回 `success` 宣布 HF-3 全部通过；原始证据入口见文末。

本阶段针对一份反向器和一份夹持器存档几何，建立带 mm/N 单位的平均端口位移任务，先检查小变形极限、实体线性对照和独立高精度求值，再根据这些证据决定是否执行预定完整路径。夹持器工况是**无工件运动**。几何研究资格仍为 `pending`，功能指标尚未冻结，HF-4 的接触精度、工件作用力和相关物理验证尚未完成。

## 1. 总体目标、工作及其可检查效果

| 要回答的问题 | 本阶段工作 | 为什么需要这项工作 | 可检查的效果及代码入口 |
|---|---|---|---|
| 独立 HF 能否直接使用已有真实几何？ | 读取四个权威掩膜、物理网格和端口标签，形成全域 TMC 模型 | HF-1 删除空区自由度，而 TMC 要让第三介质保留并传力；不能仅替换求解器名称 | 几何身份不变，材料数组与 canonical 单元顺序一致，实体/背景约束可逐项追踪；`project.build_project` |
| 能否实施一个真正的平均位移任务？ | 求解输入平均约束与执行器乘子组成的非对称 KKT 系统 | 逐节点施加相同位移会把端口刚性绑定；逐节点弹簧也不同于广义输出弹簧 | 平均约束、节点相对变形、输入反力符号与秩一弹簧均有解析小系统测试；`displacement.solve_displacement_path` |
| 非线性实现是否趋近自己的线性化？ | 同任务形成 `K0`，分别从零求解三个小位移点 | 趋零时仍存在第三介质、正则化和背景边界，直接对 HF-1 比较会混淆实现误差与模型差异 | 第一层检查非线性结果对自身 `K0` 的极限；第二层独立检查实体线性积分及响应，再报告模型偏差 |
| 极小位移残差是否受浮点相消支配？ | 保存旧核近零证据，采用从位移梯度形成的等价 Piola 表达，并复核实际 Jacobian | HF-2 强压缩状态的稳定表达，在 `F≈I` 时仍可能相减两个大于真实应力的项 | 新旧表达在相同 binary64 输入上可与 Decimal 参考比较；`tmc_kernel._residual_with_aux`、近零/强压缩原始证据 |
| 失败是否还留下可复核结果？ | 每个接受状态原子保存；失败时保留最后接受点、子步和拒绝原因 | 未到达原目标不能使用最后子步替代；持久化失败也不能丢弃已有内存记录 | `target_metrics=null`、独立的 `last_accepted_state`、已提交 step 索引及 I/O 失败回退；`project_evaluation.evaluate_project` |

实现独立性边界是：三个生产模块依赖 HF 自有几何/区域代码、NumPy、SciPy 和 JAX，不在运行时导入 LF、调用 MATLAB、修改原始几何或重新生成候选。外部参考与批量验收脚本在 `scripts/`，不作为生产求解器的隐藏依赖。

## 2. 三个新生产模块与复用边界

| 模块 | 实际职责及公开接口 | 不在该模块内决定的事项 |
|---|---|---|
| [project.py](<../src/hf_eval/project.py:157>) | `build_project(geometry_file, task_dict) -> Project`；校验试点任务，映射物理单位、材料、完整网格、实体/背景约束、输入/输出向量；不求解平衡 | 非线性路径、HP 验收、正式材料与资格阈值 |
| [displacement.py](<../src/hf_eval/displacement.py:195>) | `DisplacementSettings`；`solve_initial_tangent`；`solve_displacement_path`；KKT、可行预测、真实残差回溯、二分、回滚、接受状态记录 | 几何来源、端口几何语义、文件写入和绘图 |
| [project_evaluation.py](<../src/hf_eval/project_evaluation.py:168>) | `evaluate_project(geometry_file, task_config, solver_config, output_directory=None)`；身份摘要、各类状态、单位、solver 配置、每步和整条路径保存、持久化错误处理；返回普通 JSON 可表示的数据 | 独立 HP 通过判定、研究功能阈值、接触力解释 |

复用的 [tmc.assemble](<../src/hf_eval/tmc.py:123>) 负责从单元残差/切线装配完整网格的稀疏系统；[tmc_kernel.batch_response](<../src/hf_eval/tmc_kernel.py:206>) 提供单元实际残差和自动微分 Jacobian。HF-2 的 `tmc.solve_path` 仍是源数值力控制入口，HF-3 不通过伪造 `F0` 复用它的载荷归一化。

现有 [evaluation.evaluate](<../src/hf_eval/evaluation.py:66>) 按任务 `schema_version="hf-project-task-1.0"` 分派到新接口。CLI `python -m hf_eval evaluate GEOMETRY --task TASK --solver SOLVER --output NEW_DIRECTORY` 使用同一分派；它在调用前显式设置 CPU 与 float64。模块导入本身不随意修改全局 JAX 配置。公开 Python 调用者须在首次 JAX 使用前配置 `JAX_ENABLE_X64=true` 与 `JAX_PLATFORMS=cpu`。

## 3. 数据、物理单位与 Project 对象

几何协议仍是 [DATA_FORMAT.md](<DATA_FORMAT.md>) 中的 `hf-geometry-1.0`。`geometry.json` 指向普通 NPZ；其四个字段 `solid`、`design`、`passive_solid`、`passive_void` 是 shape `(ny,nx)` 的二值 `uint8` 数组。权威对象是这些数组及物理尺度，不是图片或轮廓。`load_geometry` 重新检查字节/字段/描述符哈希，使用 `allow_pickle=False`，来源字符串只作为数据保存。

HF-3 当前适配器接受的试点范围为：

| 项目 | 实际约定 |
|---|---|
| 网格 | `shape_yx=[40,80]`；原点 `[0,0] mm`；单元 `[1,1] mm`；域 `[80,40] mm`；`model_extent.kind="lower_half"` |
| 厚度/二维假设 | `thickness_mm=20`；平面应变，`F33=1`，不执行平面应力的厚度伸缩消元 |
| 数组/编号 | 行从下向上、列从左向右，C-order；节点 `j*(nx+1)+i`；每节点 `[ux,uy]`；单元角点 BL、BR、TR、TL |
| 全域数量 | 3200 个单元、3321 个节点、6642 个自由度；第三介质节点保留，固定 DOF 再单独消元 |
| 单位 | 长度 mm，力 N，应力/模量 MPa，能量 N·mm；刚度与 `E*t` 为 N/mm |
| 材料 | `E=1 MPa, nu=0.3`；实体倍率 1，空区倍率 `gamma=1e-6`，包括被动空区 |
| 正则化 | `alpha=1e-6`，`Lr=80 mm`；`kr=alpha*Lr**2*(kappa_s+4*mu_s/3)`；保存单位字段名 `kr_MPa_mm2` |

其中 `lambda_s=E*nu/((1+nu)*(1-2*nu))`、`mu_s=E/(2*(1+nu))`、`kappa_s=E/(3*(1-2*nu))`。只对 `lam` 和 `mu` 逐单元乘 `gamma`；`kr` 由实体参数构成，作用全域，不再次乘材料倍率。厚度进入每个积分权重，不在最终力上补乘。

`Project` 的实际属性为 `geometry`、`model`、`bin`、`bout`、`task`、`task_hash`（另有同值属性 `task_sha256`）、`region_metadata`、`qualification`、`gamma`、`solid_nodes`、`solid_dofs`、`material`、`k_out`。`gamma` 是 canonical 一维单元倍率；`solid_nodes/solid_dofs` 是全网格索引，不是压缩后的重新编号。`material` 保存实体 Lamé 参数、厚度、正则化物理长度和 `kr_material_factor_applied=False` 等实际建模信息。

HF-1 的 `geometry_id` 不变；任务哈希包含实际任务 JSON；描述符哈希还保护端口和来源等元数据。相同几何可以有不同任务，但本阶段不把材料、背景边界或行程的改变伪装成原任务。

## 4. 任务及 solver 配置接口

两份主任务是 [inverter_pilot_v1.json](<../configs/hf3/inverter_pilot_v1.json>) 和 [gripper_pilot_v1.json](<../configs/hf3/gripper_pilot_v1.json>)。它们属于诊断试点，`parameter_origin="authorized_pilot_not_research_task"`。

`hf-project-task-1.0` 的必填键及当前含义如下，未知键或不支持的值在求解前拒绝：

| 键 | 实际值/语义 |
|---|---|
| `schema_version`, `task_id`, `case_family` | 协议版本、非空任务 ID、`inverter` 或 `gripper` |
| `units` | `{"length":"mm","force":"N","stress":"MPa","energy":"N mm"}` |
| `material` | `E_MPa`, `nu`, `formulation="plane_strain"`；值见上节 |
| `third_medium`, `regularization` | `gamma`；`alpha` 和 `length_mm` |
| `input` | `tag="input"`, `control="average_displacement"`, 正值 `target_mm` |
| `output` | `tag="output"`, `spring_N_per_mm=0` |
| `constraints` | 两项：`{"tag":"support","components":[0,1]}`、`{"tag":"symmetry","components":[1]}` |
| `support_selection` | `solid_incident_nodes_only` |
| `background_symmetry` | `points_mm=[[0,40],[80,40]], components=[1]`，必须显式声明 |
| `input_auxiliary_spring_N_per_mm`, `workpiece`, `reference_state` | 分别为 `0`、`null`、`"undeformed"` |
| `qualification_criteria` | `max_design_volume_fraction=null`, `min_feature_mm=null`，研究阈值未冻结 |

可选键为 `diagnostic_variant`、`purpose`、`parameter_origin`、`description`。唯一非主任务变体是 `gripper_release_background_beyond_entity`，仅用于夹持器初始切线诊断；公开非线性封装明确拒绝用这个变体运行路径。短程桥接任务必须复制原任务并设置实际较小 `input.target_mm`，不修改已冻结的 1 mm 主任务文件。

`hf-project-solver-1.0` 的必填键为 `schema_version`、`solver_id`、`analysis="tmc_average_displacement"`、`targets_mm` 和 `settings`；可选元数据键为 `description`、`purpose`、`parameter_origin`。`targets_mm` 是有限、非负、严格递增的普通 JSON 数值列表，允许第一项为 0；最后一项必须与任务 `input.target_mm` **精确相等**。`validation_spec.json` 是独立验收规范，不是可以直接作为该 solver 配置传入的同一种文件。

[DisplacementSettings](<../src/hf_eval/displacement.py:24>) 的全部字段与默认值为：

```text
tolerance = 1e-9
constraint_tolerance = 1e-10
displacement_scale_floor = 1e-6       # mm
force_scale_floor_factor = 1e-8
max_checks = 25
armijo_c = 1e-4
max_backtracks = 12
max_bisections = 4
minimum_increment = 0.025/16        # mm；短程任务必须按自己的原增量/16传入
time_limit_seconds = 1200           # 低层默认；阶段runner显式传资源桶允许值
```

次数必须为真正的整数，实数配置必须有限且落在合法范围；未知字段被拒绝。每次结果保存 `effective_settings`，独立验收仍依据冻结规范，不能以任意放宽后的生产配置冒充原计划通过。`force_scale_per_length` 不接受从 solver JSON 额外注入；封装用真实项目 `E_MPa * model.thickness` 得到它。

## 5. 实体边界、背景边界与端口

节点选择来自 [regions.region_nodes / port_vector](<../src/hf_eval/regions.py:35>)；不同来源的约束分别记录，然后取固定 DOF 的唯一并集。

| 来源 | 主试点的物理区域及作用 | 输出中的可追踪字段 |
|---|---|---|
| 实体夹具 | 几何标签的 `x=0, y∈[0,8]`，`ux=uy=0`；只选与实体相邻节点 | `regions.support.selected_nodes/attached_nodes/excluded_unattached_nodes/dofs` |
| 实体对称 | `y=40`，反向器 `x∈[0,80]`、夹持器 `x∈[0,60]`；实体相邻节点 `uy=0` | `regions.entity_symmetry`；独立保留 `solid_constraint_dofs` |
| 背景对称 | 完整 `y=40, x∈[0,80]` 上所有全域节点 `uy=0` | `regions.background_symmetry` 区分 `solid_incident_nodes` 和 `medium_only_nodes` |
| 其他背景边界 | 未另行指定的外边界保持自然边界 | 不从 C 形夹具或源 `full_midline` 自动增添约束 |

`regions.intersections`、`fixed_dof_sources` 和 `fixed_dofs` 保留交集、每 DOF 来源和去重集合。共享 DOF 只恢复一次支反力，不把按标签重复求和的量解释为实体/介质接触力。`source_full_midline_history` 只保存来源记录，其 `role` 明确为 inert provenance。

输入方向固定为参考构形 `+x`；输出方向反向器为 `-x`、夹持器为 `+y`。每个原生端口是三个节点，权重严格保留 `[1/4,1/2,1/4]`；三个节点都须连接实体，且端口作用方向不能与项目固定 DOF 冲突。不会删除一个脱离的节点再重归一化剩余权重。

完整 DOF 向量中 `b[2*node+component]=weight*direction[component]`。广义位移 `q=bᵀu`，广义力向量为 `b*R`，因此虚功满足 `(bR)ᵀδu=R δq`。三个节点的局部位移不必相同。所有力与能量首先属于已建模下半域，不默认乘 2；理想镜像下的 `2*q_out` 只能另标为几何闭合量，不能称为工件夹持力。

## 6. 平均位移方程、KKT 与实际 Jacobian

低层接口为：

```python
solve_displacement_path(
    model, b_in, b_out, targets, k_out=0.0,
    settings=None, on_accept=None, *, force_scale_per_length
)
solve_initial_tangent(model, b_in, b_out, k_out=0.0)
```

`force_scale_per_length` 是必须显式给出的正值，项目中等于 `E*t`，单位 N/mm。低层函数校验完整有限向量，要求输入在自由 DOF 上有非零分量，但不重新解释或归一化端口权重；项目适配器执行更严格的物理端口检查。实体支承还须独立消除三个平面刚体模式。

令 `I` 表示自由 DOF，所有固定 DOF 的位移为零。实际方程是

\[
r(u,R)=f_{int}(u)+k_{out}b_{out}(b_{out}^{T}u)-b_{in}R,
\qquad r_I=0,
\qquad g(u,d)=b_{in}^{T}u-d=0.
\]

`R_input=R` 正号表示执行器对结构的力；结构对执行器为 `-R`。输出弹簧对结构的力是 `-k_out*b_out*q_out`；其加到残差中的项是相反号 `+k_out*b_out*q_out`。输出刚度为秩一矩阵 `k_out*b_out*b_outᵀ`，不是每个端口节点一根独立弹簧。

令 `K=∂f_int/∂u` 为实际残差 Jacobian，则使用一般稀疏 LU 分解

\[
\begin{bmatrix}
(K+k_{out}b_{out}b_{out}^{T})_{II} & -b_{in,I}\\
b_{in,I}^{T} & 0
\end{bmatrix}.
\]

它不被对称化；即使某个材料状态的物理切线恰好对称，这个乘子符号约定下的增广矩阵也不能直接假定对称正定。实现见 [_kkt / _linear_solve](<../src/hf_eval/displacement.py:105>)。

每个新目标从上一接受状态的切线预测，右端为 `[0, d_new-d_old]`。预测点先保持固定 DOF 为零，并仅纠正一个最大输入权重 DOF 上的浮点均值误差；这不是把整个端口刚性绑定。预测点若出现非法 J，拒绝本次增量并按规则二分。之后 Newton 修正右端为 `[-r_I,0]`，乘子和位移以同一个回溯因子更新；均值误差每次单独复核。

`linear_solve_diagnostics` 分开记录 `force_block_residual_norm`、`relative_force_block_residual`、`constraint_block_residual`，并记录预测/修正相位。`normwise_backward_error` 是混合量纲矩阵的数值诊断，标记 `mixed_unit_backward_error_is_diagnostic_only=True`，不拿它代替力/位移各自的物理尺度验收。

`solve_initial_tangent` 只在 `u=0` 形成 `K0`，以单位平均位移右端求线性参考，返回 `u`、`R_input`、`q_in/q_out`、`K0`、`K_total`、`KKT`、零状态单元字段、支反力和矩阵诊断。此处的单位位移向量是**线性参考向量**；没有把它当成有限变形的合法状态，也不宣称其所有 J 为正。

## 7. v3 近零表达式及其计算理由

当前 [tmc_kernel._residual_with_aux](<../src/hf_eval/tmc_kernel.py:138>) 标识为 `p26_q1_incremental_piola_huhu_v3`。几何仍采用总拉格朗日矩形 Q1，3×3 Gauss–Lobatto；`points` 顺序为 xi 慢、eta 快。`grad` 的 shape 为 `(9,4,2)`，`hessian` 为 `(4,2,2)`，包含 xy、yx 两项；`weights` 为 `(9,)`，包含 `hx*hy*thickness`。

v2 已使用稳定于强压缩问题的直接第一 Piola 形式

\[
P=\mu F+(\lambda\log J-\mu)F^{-T}.
\]

在 `F≈I` 时，两项各含 `±mu*I`，真实应力却可能仅为 `O(mu*||F-I||)`。先形成两个较大量再相减，会让舍入误差相对于真实小内力放大；先算 `F=I+G` 再由 `J` 求普通 `log(J)`，也可能丢失很小的增量信息。原 v2 的材料能量 `trace(C)-2-2*log(J)` 还要相减若干接近零或彼此接近的项。这些是表达式的浮点性质，不能通过降低材料模量、改变介质倍率或放松残差阈值来掩盖。

v3 直接从 nodal u 与参考梯度构成 `G=Grad_X(u)`，而非从已经舍入的 `F` 减单位阵。在每个积分点满足 `max(abs(G))<=0.01` 时，使用

\[
\delta=G_{11}+G_{22}+G_{11}G_{22}-G_{12}G_{21},\quad
J=1+\delta,\quad \ell=\log1p(\delta),
\]
\[
B=G+G^T+GG^T=FF^T-I,\qquad
P=\mu B F^{-T}+\lambda\ell F^{-T}.
\]

由于 `B F^{-T}=F-F^{-T}`，材料残差与原 Neo-Hookean 形式数学等价，但不再先产生 `+mu*I` 和 `-mu*I` 再相消。阈值外仍使用直接 Piola 表达。第二 Piola 应力为辅助输出，近零分支由 `S=F^{-1}P` 得到，不反向参与内力求值。

近零材料能量的数值求值写为

\[
W=\tfrac12\{\lambda\ell^2+\mu[(G_{11}-G_{22})^2+(G_{12}+G_{21})^2+2a(\delta)]\},
\quad a(\delta)=\delta-\log(1+\delta).
\]

代码以 `sum_{p=2}^{14} (-1)^p*delta^p/p` 的 Horner 形式计算这个辅助余项，避免再次对很接近的 `delta` 与 `log1p(delta)` 作减法；这是有限级数求值，不应描述成符号上无限精度的对数。分支内 `|delta|<=0.0202`，截断余项可用 `|delta|^15/(15*(1-|delta|))` 上界审查；实际可接受精度仍须看冻结样本的独立比较。阈值外继续使用原能量公式。

HuHu 残差保持

\[
(r_{reg})_{ai}=k_r\left[\sum_q w_q e^{-5J_q}\right]
\sum_{JK}H_{aJK}\left(\sum_b H_{bJK}u_{bi}\right).
\]

`kr`、材料插值、全域作用范围和积分方式没有因近零分支改变。切线由 `jax.jacfwd` 对**实际 material+HuHu 残差**求导，含 `exp(-5J)` 的变形导数；不从材料能量或伪造总势能求 Hessian，也不删除非对称部分。辅助能量的稳定求值不会取代实际残差 Jacobian。

所有响应调用先以 NumPy 检查全部 J 有限且正，再进入任何对数/逆运算；JAX 输出也再次检查。非正 J 被拒绝，不截断到一个小正数。`tangent=True` 与 `False` 使用同一残差定义但不同 JIT 路径，因此仍须分别接受数值核验。近零测试跨越分支两侧，并比较材料力、能量和实际方向导数；这不自动证明任意状态、任意网格的物理准确性。

## 8. 停止尺度、回溯、资源与失败状态

每个状态用实际自由力项构造

\[
d_s=\max(|d|,10^{-6}\mathrm{mm}),\qquad
S_F=\max(\|f_{int,I}\|_2,\|b_{in,I}R\|_2,
\|k_{out}b_{out,I}q_{out}\|_2,10^{-8}Et\,d_s).
\]

生产接受条件是 `relative_residual=||r_I||/S_F <= tolerance`（冻结值 `1e-9`），且 `abs(g)<=constraint_tolerance*d_s`（冻结系数 `1e-10`）；固定 DOF 保持零，全部 J 必须正且有限。零目标仍有严格正的尺度下限。不会使用力控制中的 `||lambda*F0||` 作为这个位移任务的分母。

一次回溯固定当前状态的 `S_F`，用 `phi=0.5*||r_I/S_F||²` 和 `phi_trial <= (1-2*armijo_c*factor)*phi`。因子为 `2**(-backtrack)`，索引 `0..max_backtracks`，默认包含全步在内最多 13 次试探。候选的实际新尺度另行记录，但不用于让当前回溯的下降判据变宽。每个接受状态重新计算尺度，且以 `tangent=True` 基点响应检查，不仅依据残差专用试探路径的结果。

每个目标尝试最多 25 次 Newton 基点检查；失败可最多二分 4 层。主路径最小增量为 `0.025/16 mm`；每个从零短程桥接最小增量为该目标幅值的 `/16`。`time_limit_seconds` 在装配、线性求解和 callback 前后检查；它不能打断一次正在执行的底层库调用，外层受预算监控的独立进程还负责实际墙钟与内存停止。

失败语义如下：

- 无全局候选热启动：每次函数调用从 `u=0, R=0, d=0` 开始。只在本次路径中使用上一接受状态的切线与位移。
- Newton 或试探失败时不修改上一接受状态。`failed_attempts` 保存 `from_displacement`、`attempted_displacement`、深度、错误码及 `rollback_bitwise_equal=True`。
- 二分的第一子步若接受、后续子步失败，第一子步仍是合法的最后接受状态；它的 `original_target_displacement` 和 `is_original_target=False` 防止冒充原目标。
- 失败返回 `status="failed"`, `target_reached=False`, `target_metrics=None`，保留 `u/R_input/reached_displacement` 与 `last_accepted_state`；若尚未接受任何状态，后者为 `None`，初始零数组不作为成功目标结果。
- `invalid_J`、`nonfinite`、`singular_tangent`、`newton_limit`、`backtracking_failed`、`constraint_failure`、`time_limit`、`persistence_failure` 等错误码及 details 可追踪。非法配置在求解前直接拒绝；公开封装转成明确失败摘要。

`timing_seconds` 区分 kernel/transfer、assembly、sparse solve、所有装配尝试墙钟、callback、第一次 kernel（含编译）和总时间，并统计成功/全部 kernel 调用及 Newton 检查。资源累计、失败启动、独立进程采样和阶段门属于外层 runner；不能仅把求解器内部计时当作阶段总成本。

## 9. 接受状态、JSON 结果与磁盘文件

低层返回包含 `status`、`target_reached`、`target_displacement`、`reached_displacement`、`u`、`R_input`、`target_metrics`、`last_accepted_state`、`failure`，以及 `accepted_steps`、`trials`、`failed_attempts`、`newton_history`、`linear_solve_diagnostics`、`maximum_bisection_depth`、`timing_seconds`。每个接受记录拥有独立数组；`on_accept(record)` 接收深复制，不能改坏求解器后续起点或已有证据。

每步核心数组的实际键为：

| 字段 | Shape / 单位 | 含义 |
|---|---|---|
| `u` | `(ndof,)` / mm | 完整网格位移，包括介质 DOF |
| `J` | `(ne,9)` / 无量纲 | 全部积分点，不只实体或最小值 |
| `internal_force`, `material_internal_force`, `regularization_internal_force` | 各 `(ndof,)` / N | 实际总内力及独立装配的两个分量 |
| `input_force` | `(ndof,)` / N | `bin*R_input` |
| `spring_force_on_structure` | `(ndof,)` / N | `-k_out*bout*q_out` |
| `force_residual` | `(ndof,)` / N | `fint + k*bout*qout - bin*R`；固定 DOF 上保留反力信息 |
| `support_reaction` | `(ndof,)` / N | 上述残差在唯一固定 DOF 上的值，其他位置为零 |
| `material_energy` | `(ne,)` / N·mm | 逐单元材料能量，已含厚度与积分权重 |
| `global_force_balance` | `(2,)` / N | 唯一支反力、输入力、弹簧对结构力的全局合力 |

标量包括 `d`、`R_input`、`q_in`、`q_out`；`constraint_residual`、`displacement_scale`、`constraint_bound`；`free_force_residual_norm`、`residual_scale`、`relative_residual`、`force_scale_floor` 与三个 `*_free_norm`；`minimum_J`、`solid_minimum_J`、`medium_minimum_J`；`solid_material_energy`、`medium_material_energy`、`output_spring_energy`、`output_spring_generalized_force`；合力尺度/相对误差、固定 DOF 误差、Newton 次数、原目标身份、二分深度和耗时。不存在的材料分区最小 J 为 `None`，不编码为假零。

支反力与输入/输出载荷采用去重 DOF 恢复。合力的尺度是 `max(norm(support)+norm(input)+norm(spring), S_F)`。`output_spring_energy=0.5*k*q_out**2` 可以报告；材料能量两区之和不称为含 HuHu 的保守总势能，也不拿总能量守恒检验本非保守残差。

公开返回 `schema_version="hf-project-result-1.0"`，保存：

- `geometry_id`、`geometry_descriptor_sha256`、几何文件 SHA；`task_id/task_sha256`、`solver_id/solver_sha256`；`task_config`、`solver_config`、`effective_settings`。
- `implementation` 中的包版本、源文件集合哈希、`kernel_version`、Python/平台及依赖版本；`material`、`regions`、`units`、符号约定和 `force_scale_per_length_N_per_mm`。
- 分开的 `readability`、`qualification`、`numerics`、`functionality`、`independent_precision`。生产正常完成使用 `numerics.status="success"`，独立精度仍为 `not_evaluated`，功能仍为 `not_evaluated`；该返回不会自行升级资格。
- `metrics_at_target` 与 `target_metrics` 是同一终点标量摘要；失败均为 `null`。`last_accepted_state` 是最后接受点摘要；其完整数组在路径/逐步 NPZ 或明确的内存回退中。
- `path.targets_mm`、原目标计数、全部接受点及子步；`solver_trace` 保存生产拒绝历史、线性解诊断和计时。

指定全新输出目录时写入：

| 文件 | 内容与提交含义 |
|---|---|
| `metadata.json` | 路径开始前身份、实际配置、单位和区域信息；不是最终完成证明 |
| `model.npz` | `coordinates/connectivity/solid/gamma/fixed_dofs/free_dofs/solid_nodes/solid_dofs`；`bin/bout/k_out/targets_mm`；`lam/mu/kr/hx/hy/thickness`；`grad/hessian/weights/points` |
| `steps/step_NNNN.npz` | 一个接受状态的全部规定数组，加 `d/R_input/is_original_target` |
| `steps/step_NNNN.json` | 该状态标量、相对 `arrays_file` 和 NPZ SHA；在 NPZ 写完后提交，作为单步提交标记 |
| `steps/index.json` | 已提交 pair 的目录；仅列完整写入的 NPZ/JSON，不把只有内存的接受点宣传为已落盘 |
| `path.npz` | 按接受顺序堆叠全部数组与可表示的数值标量列；原目标和二分子步全部保留 |
| `result.json` | 最终公开摘要、完整 accepted 标量历史及 solver trace |

NPZ 只接受有限普通数值类型；各文件以临时文件、flush/fsync、replace 完成原子替换。已经存在的输出目录即使为空也不复用，防止覆盖此前证据。所有标量在 JSON 中保留；含 `None` 的列列入 `nullable_or_nonnumeric_columns_in_json_only`，不强制转成 0 或 NaN。

持久化发生在接受之后：checkpoint 写失败仍保留内存接受点，生产路径标记 `persistence_failure`。最终 `path.npz`、补充 `metadata.json` 或 `result.json` 再遇到 OSError，也返回失败摘要而不是让已有状态随着未捕获异常丢失。`persistence.errors` 保存失败文件与原因，`numerics_before_failure` 保留此前数值判定；目标指标清空。若 `path.npz` 写失败，完整数组回退到返回对象的 `path.arrays`，`arrays_file=None`；已经提交的 step pair 保留其真实索引。若最后 JSON 本身无法写入，函数仍可返回内存摘要，但不声称该摘要已经落盘。

不指定输出目录时也不自动写文件，完整数组以 JSON 列表放入 `path.arrays`。路径未完成的空数组有正确的 `(0,...)` shape，和成功零响应分开。

## 10. 两层桥接与独立高精度验收接口

第一层对每个候选单独从零计算 `d=1e-3,1e-4,1e-5 mm`，比较 `q_out/d`、`R_input/d`、实体附着 DOF 的 `u/d` 与同模型 `K0`。同模型包含相同介质、`kr`、厚度、背景边界与端口。冻结最小幅值误差上限 `1e-4`；首末误差比至少 5，若首点已不大于 `1e-6` 则记录平台并免趋势判据。全部三点保留。

第二层移除介质单元及不连接实体的 DOF，关闭正则化，以相同实体支承、材料、厚度和端口检查独立实体线性参考。矩形 Q1 常系数刚度的 3×3 Lobatto 与 [HF-1 的 2×2 Gauss](<../src/hf_eval/linear.py:82>) 相对 Frobenius 差要求 `<=1e-11`，同任务响应 `<=1e-9`。随后报告完整 TMC 的 `K0` 相对实体模型的偏差；超过 5% 的 `model_bias_requires_followup` 是模型不可互换的诊断，不通过调参消掉，也不把它当物理精度许可值。夹持器释放额外背景约束的变体仅再形成一次 `K0`。

独立参考入口是 [hf3_precision_reference.evaluate_project_state](<../scripts/hf3_precision_reference.py:58>)：

```python
evaluate_project_state(
    fixture, u, R, d, bin, bout, kout, E, thickness,
    precision=50, *, direction=None, dR=0.0
)
```

它使用独立标准库 Decimal 参考，不导入生产 kernel/solver。`fixture` 提供实际 `grad/hessian/weights/lam/mu/kr/connectivity/fixed_dofs/solid`；若存在源力控制 `F0` 也不使用它来定义本项目外力。实际 binary64 `u/R/d/bin/bout/kout/E/thickness` 逐个 `Decimal.from_float` 提升，重新计算梯度、J、材料/HuHu、端口均值、弹簧与乘子。不能把生产端已经舍入的 `q`、`F`、`J` 或 `bin*R` 提升为所谓独立参考。

独立验收以 HP 各项构成的共同 `S_F` 为分母：HP 自由残差 `<=1e-8`；生产全/自由内力求值误差 `<=1e-9*S_F`；平均约束另验；50/80 位力差除共同尺度 `<=1e-30`。合力相对误差阈值为 `1e-6`，固定 DOF 阈值为 `8e-11 mm`。方向参考为 `dr=K_int*v+k*bout*(boutᵀv)-bin*dR`、`dg=binᵀv`；力/位移两块分别报告，不能不缩放地拼接后判定。

这些是冻结的验收要求，不是本文给出的结果。每个接受状态都需要相应独立证据；生产成功但独立复核未完成时只能保留独立状态待定，不能通过降低终点、调整参数、放宽门槛或省略子步宣布通过。

## 11. 需求—代码—测试对应

以下链接表示已有测试定义及检查意图，不等于本文宣布它们全部通过。测试结果应绑定运行时源码哈希、日志和资源回执。

| 实现要求 | 源码/函数 | 相关测试 |
|---|---|---|
| 全域/单位/材料映射、掩膜不变 | `project.build_project` | [test_full_domain_preserves_geometry_and_scales_material_in_project_units](<../tests/test_project.py:70>) |
| 原端口权重及作用功共轭 | `project.build_project`, `regions.port_vector` | [test_reference_ports_keep_weights_direction_and_work_conjugacy](<../tests/test_project.py:107>)；脱离/冲突端口拒绝测试 |
| 实体/背景约束分开与去重 | `project.build_project` | [test_solid_and_background_constraints_are_separate_and_deduplicated](<../tests/test_project.py:123>)；夹持器释放 20 个背景 DOF 的测试 |
| 平均约束不刚性绑定、反力符号 | `displacement._kkt`, `solve_initial_tangent` | [test_analytic_average_keeps_port_deformation_and_actuator_sign](<../tests/test_displacement.py:55>) |
| 秩一弹簧与实际非对称矩阵 | `displacement._kkt`, `_linear_solve` | [test_rank_one_output_spring_is_not_individual_node_springs](<../tests/test_displacement.py:79>)；紧随其后的非对称解析测试 |
| 固定尺度 Armijo、均值可行性、非零尺度下限 | `solve_displacement_path` 的 `force_state/feasible/newton` | [test_fixed_scale_armijo_and_feasible_newton_corrections](<../tests/test_displacement.py:113>)；零目标/显式尺度测试 |
| 非法 J、奇异、二分、回滚、超时 | `solve_displacement_path` 的 `advance` | [test_failed_target_keeps_previous_u_and_reaction_and_null_target](<../tests/test_displacement.py:148>) 及其后的二分/奇异/回溯/超时用例 |
| 从零重复与自身切线小极限 | `solve_displacement_path`, `solve_initial_tangent` | [test_real_tmc_small_path_tangent_limit_and_A_B_A](<../tests/test_displacement.py:292>)；仅小网格，不替代真实候选桥接 |
| v3 极小应变及分支附近力/能量/方向导数 | `tmc_kernel._residual_with_aux` | [test_tmc_near_zero.py](<../tests/test_tmc_near_zero.py:14>)；原小样本/强压缩回归另存原始证据 |
| Decimal 端口、反力、秩一项及增广导数 | `hf3_precision_reference.evaluate_project_state` | [test_hf3_precision.py](<../tests/test_hf3_precision.py:57>)；包含 50/80 位近零比较和纯乘子方向 |
| callback 与返回历史一致、原目标不冒用子步 | `project_evaluation.evaluate_project` | [test_atomic_step_pairs_exist_before_solver_returns_and_are_replayable](<../tests/test_project_evaluation.py:130>)；失败子步/伪成功拒绝测试 |
| 最终 I/O 失败仍保留状态与诊断 | `project_evaluation` 的 `persistence_failure` 与 finalization | [test_final_path_write_failure_returns_all_arrays_and_failed_summary](<../tests/test_project_evaluation.py:277>) 及其后两项真实 OSError 注入测试 |

## 12. 原始证据入口与当前结论边界

写本文时下列原始证据目录/文件已经存在，部分阶段仍在继续生成或复核。这里只记录用途，不从目录名或单项日志推断最终通过；后续总验收由主任务统一汇总。

| 原始证据入口 | 用途 |
|---|---|
| [hf3_results/baseline_manifest.json](<../../hf3_results/baseline_manifest.json>) 与 [baseline](<../../hf3_results/baseline>) | 旧实现字节副本、输入/配置身份与原资产保留记录 |
| [near_zero_v021_001](<../../hf3_results/near_zero_v021_001>) | 原 v2 在真实几何 K0 近零输入上的浮点/HP 取证；旧输出不覆盖 |
| [near_zero_v030_001](<../../hf3_results/near_zero_v030_001>)、[near_zero_v3_final_001](<../../hf3_results/near_zero_v3_final_001>) | 修改阶段与当前 v3 的近零输入数组、比较摘要；必须按各自源码哈希区分，不能合并成未注明版本的证明 |
| [small_kernel_v3_001](<../../hf3_results/small_kernel_v3_001>) | 原小型参考、方向误差曲线、原始数值和所用规范 |
| [strong_kernel_v3_001](<../../hf3_results/strong_kernel_v3_001>) | 强压缩冻结输入的表达式/实际切线参考比较，防止只改进近零状态 |
| [regression_a.xml](<../../hf3_results/regression_a.xml>)、[regression_b.xml](<../../hf3_results/regression_b.xml>) | 分次测试原始结果；不能用较早一次结果代表之后修改的文件 |
| [resource_jobs](<../../hf3_results/resource_jobs>) | 每个顺序数值作业的日志、墙钟/内存回执与运行范围 |

本文负责描述实现与接口，完整桥接、路径和独立安装的最终结论见[HF3验收记录](HF3_VALIDATION.md)。`qualification=pending` 与“允许明确标记的诊断运行”可以并存；`numerics=success` 与“独立 HP 尚未完成”也可以并存。即使两例最终完成全部冻结实现验收，所证明的仍是这一指定离散模型和任务的实现一致性与可重复性，不能自动扩展为真实接触精度、正式材料有效性、稳定性、制造资格、工件夹持力或候选性能排名。HF-4 对应工作尚未验证。
