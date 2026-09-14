# HF4 双分量位移实现与验证对应

本次 `0.5.0` 实现增加显式的双分量位移入口，用两个独立的 binary64 数组保存宏观运动与小修正。目标是让近刚体运动下的微小平衡修正进入实际力学状态，并继续满足原 HF4 求解、独立高精度和模型偏差门槛。材料、第三介质倍率、HuHu 弱式、几何、边界、原始目标以及容差都沿用 [HF4 物理规范](../configs/hf4/validation_spec.json)。变更范围和放行顺序由[实施规范](../../docs/HF4_SPLIT_IMPLEMENTATION_SPEC.md)及[实施冻结记录](../../hf4_repair_results/implementation_freeze.json)约束。

本文记录接口及截至阶段 2 已完成的证据：阶段 0 因果实验、阶段 1 固定态与回归、从零开始的首目标生产路径及其独立审计。本文不判定四种组合的完整路径是否全部通过，也不据此确认非均匀接触、圆柱接触或真实候选机构的物理精度。

**问题、原因与已经观察到的效果。** 原第四组合为 `gamma=1e-7、h=0.0625 mm`。旧单数组状态在宏观位移约 `0.125 mm` 时，小修正与位移的量级相差很大；修正加回原位移后可能舍入消失。[固定态探查](../../hf4_results/fixed_state_probe_001/summary.json)显示该候选状态的独立 HP 残差约 `1.84103e-9`，生产内力求值与 HP 的差远小于该值。此处的失败不能归结为本构求值精度不够。

[阶段 0 保留更新实验](../../hf4_repair_results/retained_update_001/summary.json)复用同一已存状态、同一修正方向及固定步长，不重新求解方向。把实际状态定义为 `D(u)+D(alpha)D(delta)` 后，全步更新的 80 位相对残差降至约 `6.89026e-16`；先加回 binary64 位移再提升的状态仍约为 `1.84103e-9`。这项干预支持修正状态表示的因果依据；实验中的状态没有作为生产路径接受态或后续初值。

**状态权威与公开入口。** [split_state.py](../src/hf_eval/split_state.py) 定义：

```python
SplitDisplacement(lift, fluctuation)
# state.representation == "split_displacement_v1"
# state.ndof; state.copy(); state.u_display
SplitDisplacement.from_legacy(u)
```

`lift` 与 `fluctuation` 均为同长度、非空、偶数长度的一维有限实数数组，构造时各自复制成只读 float64。DOF 顺序仍为每节点 `[ux, uy]`。权威数学状态是 `D(lift[i])+D(fluctuation[i])`，其中 `D` 精确提升实际 binary64 数值。`u_display` 是新分配的、经过舍入的 `lift+fluctuation`，仅供显示和旧格式查看；它不能用于重新装配、独立审计或恢复双分量状态。显示求和溢出会报错，不会改写两分量。

新力学入口位于 [split_kernel.py](../src/hf_eval/split_kernel.py)，常量为 `KERNEL_VERSION="p26_q1_split_displacement_v1"`：

```python
determinants_split(lift_e, fluctuation_e, ops)
batch_response_split(lift_e, fluctuation_e, ops, lam, mu, kr, *, tangent=True)
assemble_split(model, state, *, tangent=True)
```

单元批数组为 `(ne, 8)`，局部节点依次为左下、右下、右上、左上，每节点两个位移分量；仅 `determinants_split` 也接受一对 `(8,)` 单元数组。`assemble_split` 要求 `TMCModel` 与 `SplitDisplacement`，拒绝把普通位移数组隐式解释成新状态，返回 `(K, internal, fields)`；`tangent=False` 时 `K=None`。模型仍采用原 canonical 连接和单元 DOF 映射，局部力用 `bincount` 装配，局部切线用 COO 转 CSC 并合并重复项，保留非对称性。运行环境需显式启用 JAX float64 CPU；导入内核不改变运行配置。

**总运动学与非线性弱式。** 两个数组先分别做线性的梯度和 Hessian 运算，再形成总量：

```text
GL = grad(lift)             Gw = grad(fluctuation)
G  = GL + Gw
F  = (I + GL) + Gw
HL = H(lift)                Hw = H(fluctuation)
Hu = HL + Hw
```

这里 `F` 的运算次序是实现契约的一部分。在强压缩制造场中，`I+GL` 可先消去宏观部分，使 `Gw` 的小量直接保留在 `F` 中；写成 `I+(GL+Gw)` 可能先丢失该小量。JAX 在 `I+GL` 后设置 `optimization_barrier`，约束编译器重排。该原语保留恒等 JVP 和批处理规则，并非 `stop_gradient`。`G` 另行保存，用于近单位状态的稳定表达。

在每个积分点，当 `max(abs(G)) <= 0.01` 时，使用 `delta=tr(G)+det(G)`、`J=1+delta` 与 `log1p(delta)`；其它状态使用上述总 `F` 的直接行列式和 `log(J)`。近单位 Piola 表达采用 `B=G+G.T+G@G.T`，避免两个约为单位量的项相减；近单位材料能量沿用稳定的 `delta-log1p(delta)` 表达，在小 `delta` 分支求和到 14 次幂。远离单位状态仍采用原直接 Piola 表达。两种公式表示同一材料模型，各分支都有固定制造场核验。

每个单元的材料和正则化残差都在**总** `F、J、Hu` 上评估。特别是 HuHu 中的系数 `kr*exp(-5*J)` 依赖总变形，不能分别求 `R(lift)`、`R(fluctuation)` 后相加。`lam、mu` 已由模型带入对应实体或第三介质倍率；`kr` 继续使用实体参数计算的值，不再次乘 `gamma`。切线是对 fluctuation 的完整自动微分，lift 固定；它包括 `exp(-5*J)` 对总状态的导数，因此不强制对称。

返回的 `G、F` 为 `(ne,9,2,2)`，`J` 为 `(ne,9)`，`Hu` 为 `(ne,2,2,2)`，后者不重复积分点维度；另有局部总力、材料力、正则化力、第二 Piola 应力和逐单元材料能量。材料能量只对应材料项。原 HuHu 弱式的非保守性质没有改变，不能把材料能量单独当成全系统势能或用其下降替代残差接受门槛。

`determinants_split` 在不调用对数、逆矩阵的情况下返回原始总 `J`，包括零和负值；lift 自身不可逆并不构成拒绝理由。生产调用先在 NumPy 检查有限总运动学及 `J>0`，JAX 再用批外单一 `lax.cond` 守护有效分支，避免逐单元条件在向量化后提前求非法对数或逆矩阵。近单位分支的 `log1p` 输入也经过安全选择。拒绝态保留原始运动学供判定，不裁剪 `J` 或伪造有效内力。

**路径、预测器与回滚。** [split_prescribed.py](../src/hf_eval/split_prescribed.py) 增加：

```python
normal_lift_shape(problem)
solve_split_prescribed_path(
    model, base, direction, lift_shape, targets, *, reaction_groups=None,
    settings=None, force_scale_per_length, on_accept=None)
split_linear_measurement(state, vector, offset=0.0)
state_hash(state)
```

当前均匀法向任务的 `normal_geometric_piecewise_v1` lift shape 仅依赖几何：下实体的竖直值为 1，上实体为 0，中间间隙内线性过渡，水平值为 0。它不读取材料、反力或半解析平衡解。在目标 `d` 上保存实际 binary64 运算所得 `lift=base+d*lift_shape`，固定 DOF 的 fluctuation 始终为零。固定 DOF 上的 lift shape 必须精确匹配规定运动方向。当前冻结几何和目标为二进制可精确表示的数，存档审计还独立确认实际 lift 等于对应 Decimal 乘加值。通用非二进制精确输入并没有隐式补偿机制，仍必须通过独立约束误差审计。

从上一个接受态前进时，保留旧 fluctuation，将 lift 改为新目标值，并用完整的 `-(K @ delta_lift)[free]` 求预测修正。此过程不先从 fluctuation 减去 `delta_lift`，避免同一 lift 变化被补偿两次。后续 Newton 和回溯仅更新自由 fluctuation。回溯采用同一次基态的固定力尺度计算 Armijo merit，每个候选重新检查总 `J` 和有限性；接受线搜索点后，还需在下一次 Newton 基态检查满足收敛门槛。

冻结设置仍为生产相对残差 `1e-9`、相对约束 `1e-10`、最多 35 次基态检查、回溯上限 16、二分深度上限 8、最小增量 `1e-5 mm` 和单路径 120 秒。力尺度为

```text
SF = max(||fint_free||, ||fint_fixed||,
         1e-8 * E * thickness * max(abs(d), 1e-6 mm)) .
```

无外部节点载荷，残差为 `fint`，反力只取固定 DOF。驱动力和测力组采用相应方向向量与固定反力的内积，报告装置作用于模型及其反号；没有额外乘 2。测量线性位移时分别累积 lift 与 fluctuation 的贡献，并用 `math.fsum` 合并，避免先使用显示数组。

每次尝试保留 `(lift, fluctuation, d, K)` 的接受态快照；失败时核对两数组及目标、切线未被替换，再决定是否在原限制内二分。已接受子步可以保留，失败目标的 `target_metrics` 必须为空。失败候选、该基态对应的最后修正、线搜索基态与试探态 hash 另行存档；新基态没有求出修正时不会沿用上一基态的旧方向。`on_accept` 接收深复制，无法通过修改记录影响求解器。持久化失败或超时会作为失败返回，不能据最后的有效数组声明整条路径成功。

**独立 HP 参考及验收尺度。** [hf4_split_precision_reference.py](../scripts/hf4_split_precision_reference.py) 不导入生产有限元、材料内核或自动微分。它仅复用冻结 [HF2 Decimal helper](../scripts/hf2_precision_reference.py) 的 primitive 验证和保存逻辑，独立实现 Decimal 运动学、Piola 力、HuHu 力及解析方向导数，不调用旧 helper 的力学 `evaluate`。

```python
DecimalSplitQ1Reference(fixture, precision=50).evaluate(
    lift, fluctuation, *, tangent_direction=None,
    fluctuation_offset=0.0, derivative=True)

evaluate_split_prescribed_state(
    fixture, u_lift, u_fluctuation, d, base, direction,
    reaction_groups, force_scale_per_length, precision=50, *,
    tangent_direction=None, fluctuation_offset=0.0, derivative=True)
```

`fixture` 保存实际 `grad、hessian、weights、lam、mu、kr、connectivity、fixed_dofs` 等普通数组；`F0` 仅用于确定 DOF 数，本任务不把它当作外载。适配器先精确提升实际数组，在足以保留任意有限 binary64 加法和扰动乘积的 Decimal 上下文中构造权威位移，然后以指定 50 或 80 位精度计算力学。接受态固定 `fluctuation_offset=0`。方向检查只扰动 fluctuation：`D(L)+D(w)+D(h)D(v)`；不能用旧的 offset/direction 接口同时藏入 lift 和导数方向。

HP 输出保留原始 Decimal 位移、`G/F/Hu/J`、材料与正则化力、材料能量、组反力、驱动力、约束、力平衡，以及可选的总/分项切线作用。`*_decimal` 为比较依据，float 视图用于普通显示。生产与 HP 的差按 `D(production)-HP` 计算，不能先把 HP 内力转为 float 再相减。约束比较使用 `D(L)+D(w)-D(base)-D(d)D(direction)`，因此也核验实际 prescribed 乘积和状态表示，而非仅比较两个来源相同的舍入视图。

任务固定态预检对全 DOF、自由 DOF 的总力、材料力、正则化力均使用 `1e-9*SF` 求值预算，并对正则化分项另加自身尺度检查，避免总反力掩盖该分项误差。非均匀方向检查使用

```text
||K v - HP(K v)|| <= 1e-9 * max(||HP(K v)||, 1e-12*E*thickness*||v||),
```

全/自由 DOF 分别比较，正则化方向作用另按自身 HP 范数核验。方向参数无量纲，`v` 为位移，故右侧量纲为力；此处不再除以单元尺寸。固定态 `J` 的范数相对误差上限为 `1e-9`，分母下限 `1e-12`；50/80 位总力及方向作用交叉差在相同尺度下不超过 `1e-30`。人工非平衡场记录 HP 平衡残差但不要求平衡。

实际接受态还需同时满足原生产 `1e-9` 停止门槛、HP 自由残差 `1e-8*SF`、生产力求值误差 `1e-9*SF`、约束、有限正 `J` 与全局力平衡要求。[独立审计器](../scripts/audit_hf4_split_normal.py) 从已保存生产内力重算生产尺度和残差，核对每一项存档指标；较宽的 HP 平衡门槛不能让违反生产停止条件的状态通过。有限介质半解析参考对账与硬接触模型偏差另列 `numerical_status`、`model_status`；两者不互相替代。二分过程中处于未冻结模型误差区间的状态标为 `measurement_only`，仍须通过数值审计。

**普通文件、身份与可搬迁读取。** [生产 runner](../scripts/run_hf4_split_normal.py) 每次创建新目录，保存 `metadata.json、model.npz、result.json、steps/index.json` 和逐接受态 JSON/NPZ。metadata 绑定任务、物理 spec、source 文件 hash、几何和网格身份、settings、lift scheme、请求目标及执行范围。model 包含实际坐标、连接、材料、算子、DOF、base/direction、lift shape、测力组和 gap vector。每个接受态 NPZ 保留 `u_lift、u_fluctuation、u_display`、内力及分项、反力、`J/F`、材料能量等；JSON 记录状态 hash、目标/子步身份、求解指标和时间。

状态 hash 为 SHA256，按顺序输入 ASCII `split_displacement_v1`、little-endian int64 的 `[ndof]`、little-endian float64 的 lift 字节、fluctuation 字节。它标识实际**两数组表示**，不是对物理等价分解作规范化；显示数组相同的两个状态也可具有不同 hash。文件 SHA256 另行绑定完整 NPZ/JSON，不能用状态 hash 替代 model、任务或源代码身份。

[普通文件 helper](../scripts/hf4_common.py) 通过临时文件、flush/fsync 后替换写出单个文件，JSON 禁止 NaN，Decimal 写成字符串；读取 NPZ 使用 `allow_pickle=False` 并拒绝非普通实数或非有限数组。接受态索引仅在其数组与标量文件写出后更新。HP 审计把每态报告、原始 HP 和半解析参考作为一组 commitment 保存；续读需确认输入、spec、脚本、逐态 hash 和 commitment 均未变化，还会从数值检查重新推导缓存状态，拒绝只改 `status` 的记录。

[输入独立审计](../scripts/hf4_input_audit.py) 从冻结 spec 重建几何、材料、算子、区域与边界约束，避免生产模型和半解析参考同步误配仍显得一致。双分量审计另外重建几何 lift、核对固定 fluctuation 为零、显示投影、原始目标与二分子步顺序及完整性。可搬迁重读依赖普通 JSON/NPZ 和安装后的 HF 包，不依赖 LF、MATLAB 或原始优化程序；[安装环境回放脚本](../scripts/run_hf4_split_isolated.py) 提供源目录禁止访问、A–B–A 路径及两数组读回检查。该脚本的存在本身不构成已完成隔离验收的结论。

**旧入口和适用范围。** 原 `tmc_kernel、tmc、prescribed` 等单数组入口保持原语义，新入口通过显式模块和类型选择。`from_legacy(u)` 构造 `(u,0)`，精确保留旧 binary64 状态所代表的数学位移，不能恢复历史舍入丢失的小量。不同内核运算次序的力学一致性按冻结容差验证，不承诺所有新旧输出逐字节相同。双分量也不是任意精度求解器：每个分量自身仍有 binary64 舍入；任意坏分解、超出验证量级的 cancellation 或非精确边界乘积不自动获得精度保证。

单元与装配接口可接收一般非均匀 split 场，制造测试已覆盖两分量 Hessian 非零、相消后 HuHu 非零及混合材料装配。当前 `normal_lift_shape` 和路径 runner 则仅定义此合成法向任务的 lift。把接口用于真实机构、不同工件或一般非均匀接触，需要另行定义任务/lift 与验证，不能从均匀法向结果推断其物理合格。

**固定检查与代码测试的对应。**

| 要验证的风险 | 对应实现/测试 | 判据或保存量 |
| --- | --- | --- |
| 显示数组掩盖微小位移；数组别名改写状态 | [test_split_state.py](../tests/test_split_state.py)、[test_hf4_split_precision.py](../tests/test_hf4_split_precision.py) | 只读独立副本；`1/8 + 2^-60` 例显示丢失但权威位移与力非零；非法输入拒绝 |
| `F` 重排丢失强压缩小量、近单位分支差异 | [test_split_kernel.py](../tests/test_split_kernel.py) | 两矩形尺寸；强压缩/合法总态但非法 lift/分支两侧；NumPy 与 JAX 总 `J`、HP 力和运动学 |
| 漏掉 lift 的 Hessian 或错误叠加非线性残差 | 同上及 [HP 测试](../tests/test_hf4_split_precision.py) | 两分量 Hessian 均非零；正则化总力非零；精确等价分解的 HP 总态一致；生产响应按精度门槛一致 |
| 导数误把 lift 当变量；只验证对称切线 | [test_split_kernel.py](../tests/test_split_kernel.py) | fluctuation 方向的独立解析 Jv；固定五步有限差分曲线全保存；2×2 混合材料全局装配和非对称性 |
| 预测器重复补偿、失败后污染状态或旧方向错配 | [test_split_prescribed.py](../tests/test_split_prescribed.py) | 独立线性链真值；修改自由 lift 延拓后物理解一致；两分量回滚、回调隔离、失败目标 null、修正与基态绑定 |
| 正确内核掩盖任务精度或映射错误 | [preflight_hf4_split.py](../scripts/preflight_hf4_split.py) | 真实 g1/m1 三个均匀固定位形；非均匀、等价分解、微小量共六例；实际数组形状/hash、HP50/80 与生产两模式 |
| 只满足 HP 门槛却未满足生产接受条件 | [test_hf4_split_audit.py](../tests/test_hf4_split_audit.py) | 从普通保存数组重算生产 `1e-9`；拒绝改指标、非法 J、错误精度；数值与模型状态分开推导 |

制造单元测试使用其冻结人工系数 `lam=2、mu=3、kr=1/8` 和专用尺度，力误差门槛 `1e-9`、Jv 门槛 `1e-8`；实际 HF4 预检的 Jv 门槛为 `1e-9`。这两个层次的材料和尺度不混用。有限差分保存每个预定步长、两侧力及最小 `J`，同时比较普通浮点扰动和独立 Decimal 理想扰动，避免仅用一个最优步长掩盖表示误差。

截至本文证据截点，[阶段 1 gate](../../hf4_repair_results/stage1_gate.json) 记录六个固定态全部通过，完整回归 592 通过、1 跳过；[回归 XML](../../hf4_repair_results/split_regression_001.xml) 保留 41 个 properties，其中 4 个为完整有限差分曲线。[另加的存档审计测试](../../hf4_repair_results/audit_gate_tests_001.xml) 为 12 通过，未据此改写前一份完整回归计数。三个均匀固定态来自独立半解析参考减去实际几何 lift 后一次舍入的 fluctuation，**仅作求值夹具**，没有用作生产求解初值；其余三例检验非均匀 HuHu、等价分解与小于显示 ULP 的状态保留。具体逐项结果见[预检摘要](../../hf4_repair_results/split_preflight_001/summary.json)。

从零开始的[首目标生产结果](../../hf4_repair_results/first_target_001/result.json) 与[逐态独立审计](../../hf4_repair_results/first_target_001_audit/summary.json) 覆盖 `d=0、0.125 mm` 两个接受态，均通过。在 `0.125 mm` 处，HP 相对残差约 `3.64924e-15`，最小 `J≈0.500000818155`，50/80 位归一化内力差约 `9.68e-43`。这是新生产入口实际保留修正并在原门槛下达到首目标的证据，强于固定态求值通过；仍只覆盖首目标。[阶段 2 gate](../../hf4_repair_results/stage2_gate.json) 据此放行一次原第四组合完整路径，后续各路径及发布结论由单独的最终证据报告判定。
