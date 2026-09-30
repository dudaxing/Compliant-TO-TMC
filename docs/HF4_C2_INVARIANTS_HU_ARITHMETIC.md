# HF4-C2 候选：保留低位的不变量与 Hu 算术

日期：2026-09-28。本文对应新增 `hf_repo/src/hf_eval/compensated_invariants.py`，版本 `split_invariants_hu_dd_v1`。它是候选算术的数学与实现合同，不是科学准入记录。本阶段不修改旧补偿模块、冻结协议、历史结果或原独立 HP 参考。实际运行结果由统一有界执行回执记录；本文不预告通过。

## 1. 为什么新增此路径

`near_rotation_segments_001` 的有序替换诊断表明：在三例保存近旋转输入上，仅提高下游组装精度或仅从旧 F 重算 J，仍不足以通过原门；替换为保存参考 F/J 后材料项达到参考精度差，随后替换 Hu 才关闭两个矩形例的正则分量差。该证据支持同时保留运动学低位和 Hu 低位的候选方向。它不证明所有单个 binary64 输出算法都不可能通过，也不为任何新求解路径提供准入。

本模块从原始 lift、fluctuation 与已保存参考算子计算，不重建几何，不使用 HP oracle，不把近旋转力置零。每个归一化 DD 为 `(hi, lo)`，两部分均为 binary64 数组，所代表的实数称为 shadow 值 `hi + lo`。保留低位直到小应变不变量、应力及弱式收缩形成以后，再由内核显式 `dd_value` 输出。

## 2. 运算路径与恒等式

参考算子 `grad` 为 `(9,4,2)`，`hessian` 为 `(4,2,2)`。单元 nodal 输入可为 `(8,)` 或 `(4,2)`，两者都支持任意相同 batch 前缀。

1. 将 lift 与 fluctuation 各自的四个节点积以 TwoProduct 展开，并以 DD 加法按固定顺序累加，得到 G 与 Hu；没有先将 lift 与 fluctuation 相加，也没有分别将两个 Hu 收缩到单浮点再相加。
2. F 从单位矩阵初始化，并与从零初始化的 G 分别累加相同八个乘积 pair；单位项直接参与 F 的累加，不先把 G 收缩为单浮点，也不先截断 G 的更高尾项后才加入单位项。
3. 以全部四个 high/low 乘积计算 `B = G + G^T + G G^T` 与 `delta = tr(G) + det(G)`。
4. J 始终直接由保留低位 F 的 `F00*F11 - F01*F10` 构造。强压缩状态不会用单浮点 `1 + delta` 恢复 J。
5. `hessian_action_pair` 对全部四个 `(j,k)` 项收缩，得到 `H^T Hu`，输出形状 `(...,4,2)`。不假设两个混合 Hessian 分量相等。

`dd_matmul` 将左、右矩阵广播为 `(...,row,inner,column)` 乘积数组，统一执行逐项 DD 乘法，再沿 inner 从零开始按递增索引固定累加。向量化只共享独立 row/column 的计算图；每个输出元素的四个 high/low 乘积及归约次序与分别循环 row/column 相同。

实数层面有 `B = F F^T - I`、`delta = J - 1`。在两分量有限精度实现中，直接 J 与独立构造的 `1 + delta` 允许有最后截断量级的差，不能声称两者逐位相等。正 J 判定以直接 J 为准；小量分支的对数使用保留低位 delta。

候选内核应遵守：

\[
T=\operatorname{cof}(F)/J,\qquad
P_{\rm small}=(\mu B+\lambda\log(1+\delta)I)T,
\]
\[
P_{\rm direct}=\mu F+(\lambda\log J-\mu)T,\qquad
S=T^TP.
\]

S 由已选择的同一个 P 得到，不另用会重新引入消去的直接 S 式，不强制对称化。正则弱式仍为 `kr * sum(weights * exp(-5J)) * H^T Hu`。补偿其算术不改变弱式。

## 3. 分支与能量

小不变量分支固定为 `maxabs(B) <= 2^-4` 且 `abs(delta) <= 2^-6`。比较在归一化两分量上实施，避免先舍入 `hi + lo` 后把边界两侧合并。这两个界是预先声明的二进制界，不拟合本轮结果，也不声称最优。`maxabs(B)` 不是旋转不变的标量；坐标旋转可能改变算术分支，两式的物理等价性和数值一致性仍必须验证。

近分支材料能量的实数恒等式是：

\[
W=\tfrac12\{\lambda\ell^2+\mu[(G_{00}-G_{11})^2+(G_{01}+G_{10})^2+2r(\delta)]\},
\quad \ell=\log(1+\delta),\quad r(\delta)=\delta-\log(1+\delta).
\]

内核使用 14 阶 Horner 多项式 `r14 = delta^2 * (1/2 - delta/3 + ... + delta^12/14)`。在此分支，

\[
|r-r_{14}|\le\frac{|\delta|^{15}}{15(1-|\delta|)}
\le\frac1{945\,2^{84}}<6\times10^{-29},
\quad
|r'-r'_{14}|\le\frac1{63\,2^{78}}.
\]

这些是实数截断界，不包含 binary64 系数舍入、DD 运算与 libm 误差；实际能量与导数检查不可省略。截断能量不是逐位精确的原能量，其 AD 梯度不能替代原材料 P 或实际弱残差 JVP。其他正 J 状态使用直接能量式。原语边界检查须覆盖正负 delta 两面，B 边界以及等值和 `nextafter` 两侧；制造场的名义幅值不等于非二进制网格上实际不变量的精确边界值。

## 4. 可执行范围合同

旧 affine 模块对初始操作数的证明不能自动扩展到 B、delta、Hu、材料乘积或商。本模块不作这种推断，而在每一个公共 primitive 上重新检查。

| 对象 | 条件与拒绝行为 |
| --- | --- |
| 每个原始 binary64 操作数与 DD 分量 | 有限，且为零，或绝对值在 `[2^-400, 2^400]` 内；DD 使用归一化表示。 |
| DD 输入 | 上述分量范围；还检查 `abs(lo) <= 2^-52 * abs(hi)`，拒绝明显重叠的手工 pair。此宽检查不是任意输入已正确归一化的证明；公共合同要求使用本模块构造器/运算输出。 |
| TwoProduct | 每次都检查两个实际操作数；不根据最初 lift 范围跳过后续乘积检查。所有四个 high/low 乘积都计算，包括 `lo*lo`。 |
| 暂存与 DD 输出 | `_finish` 在 TwoSum 前检查有限且绝对值不超过 `2^900`；归一化后重新检查严格分量范围。极小但非零的 low、相消前的大乘积或巨大商可被保守拒绝。 |
| 除法 | 分母 pair 有效且 high 非零；先替换非法入口为安全占位值，再计算；初商与两次余数修正都走相同 DD 检查。 |
| log | 代表值严格正；非法入口先置为 1，再调用 libm，最终返回 NaN。 |
| log1p | 保留低位的 `1+a` 严格正；若 high 等于 −1 而 low 为正，使用保留的 `1+a` 的 log，未选择的 log1p 输入先安全化。 |
| exp | pair 有效且代表值绝对值不超过 256；非法入口先置零，最后拒绝。`exp(±256)` 量级在约 `2^±370`，随后乘积及 low 仍需通过逐原语检查。 |
| 非法结果 | 对应两个分量均为 NaN；不夹紧 J、不取绝对值、不静默丢弃低位。`kinematics_pairs.supported` 为整批标量 verdict。 |

保守界的推导：每个非零合法 binary64 操作数的最低可能有效位为 `2^-452`，因此精确乘积的最低量化位不低于 `2^-904`，高于 binary64 最小正规数 `2^-1022`。Dekker Split 的放大量小于 `2^428`；只使用各次加减的宽三角界，`large/high/low` 分别小于 `2^429/2^430/2^431`，分裂片乘积小于 `2^862`，误差重构可用保守 `2^865` 上界覆盖，仍小于 `2^900` 暂存上界与溢出界。每个 DD 结果都会重新收紧到 `2^400` 分量界，因此后续二次运算不会无依据地继承更大范围。加法中误差项最小量化位也保持正规；非法输入先被安全占位值替代。此实现不使用自动缩放来扩大范围，故不需要也不声称缩放后恢复的误差证明。

这套域刻意保守：原始输入在范围内并不保证整个响应受到支持，数学上合法的有限变形也可能因中间量或极小低位而被拒绝。内核须分别检查运动学 `supported`、正 J、材料系数与 weights 的 `dd_from`/`pair_supported`、所有所用材料/收缩结果和最终有限性。越域必须记录为声明样本的失败；不得删除、替换、剪裁或扩大阈值来凑齐通过数。冻结的 69 制造场与 63 保存态集合保持完整。

EFT 并不意味 DD 运算全部精确：DD 加/乘舍去更高阶尾项，除法只作两次余数修正，不承诺正确舍入。log/log1p/exp 使用基础 binary64 libm 值及低位参数修正；基础 libm 误差没有被估计成第三个分量，更不承诺 106 位超越函数精度。NumPy/JAX 共享显式运算结构，libm 的后端差异仍须数值检查。

## 5. JVP 与实际残差合同

EFT 的浮点误差簿记不能直接作为物理导数。本模块为 product、DD add/sub/mul/div/log/log1p/exp 定义 custom JVP，依据 shadow 值 `x = hi + lo` 的物理链式法则。统一切空间代表为 `(dx, 0)`：这不是把原物理低位当常数的任意 stop-gradient，而是将完整物理方向存入 high tangent；输入方向中的两部分先相加，乘除及超越函数的导数系数显式使用 primal 的 high 与 low。内部没有 `stop_gradient`。

例如乘法为 `dx*y + x*dy`，实现分别计算每个 primal 分量乘以方向再相加；除法为 `(dx-q*dy)/y`，q 与倒数都使用 DD primal；log/log1p 的导数系数为 DD 倒数，exp 使用返回的 DD exponential。对低位系数的影响仍最终舍入到 binary64 tangent；不承诺无限精度导数。矩阵乘法、归约、G/F/Hu 收缩由这些 primitives 组合，因此 grad/hessian/lift 的扰动也被链式法则包含，机械求导时它们保持固定。

该规则定义平滑物理 shadow 表达式的一阶导数，**不是**离散舍入映射 `hi(input), lo(input)` 的经典导数，也不是未经验证的高阶 AD 合同。范围边界与算术分支选择是离散谓词；只在合法分支内部定义物理导数，边界必须检查两侧物理等价表达式的数值一致性。最终实际残差的 `jacfwd(..., argnums=fluctuation)`、返回 K v、独立 HP 切向与多步长差分仍是必要验证，不能用原内核切向或能量 Hessian 替代。

固定 lift 时应得到：

\[
dF=\nabla v,\quad dHu=Hv,\quad dJ=\operatorname{cof}(F):dF,
\]
\[
dB=dG+dG^T+dG G^T+G dG^T,\quad d\ell=dJ/J,\quad dT=-T(dF)^TT,
\]
\[
dR_{\rm reg}=kr\sum_q w_q e^{-5J_q}
\{H^THv-5\,dJ_q\,H^THu\}.
\]

这里 `Hu` 与 `H^THu` 不依赖 q，dJ 依赖 q；上式的第二项须保留求和。该源弱式产生的实际 Jacobian 可以非对称，不能强制对称化或凭空引入正则能量。

所有候选 JIT 必须使用 `xla_cpu_enable_fast_math=False` 与 `xla_cpu_ftz=False`，CPU binary64，由调用程序显式配置。模块不修改全局 JAX 配置。操作屏障用于约束关键加、减、乘次序；受支持编译器上的行为仍须原语测试与数值证据确认。

## 6. API 与状态

- 构造及检查：`dd_from/dd_const`、`operand_domain`、`pair_supported`。
- 数值：`dd_product`（两个原始 binary64）、`dd_add/sub/mul/div`、`dd_log/log1p/exp`、`dd_value`。
- 结构：`dd_getitem/neg/where/transpose/swapaxes/sum/matmul/cofactor`。
- 场：`kinematics_pairs(lift,w,grad,hessian,xp)` 返回 DD `F/G/B/Hu/J/delta`、标量 `supported` 与每积分点 `near`；`hessian_action_pair(Hu,hessian,xp)` 保留 Hu 低位完成收缩。
- 选择：`dd_abs_le`、`near_invariants`，界为 `B_THRESHOLD=2^-4`、`DELTA_THRESHOLD=2^-6`。

作者阶段仅静态阅读与语法解析，不导入本模块、不运行 pytest/JAX/HP/FE。测试作者与内核作者独立集成；统一运行由主代理在已授权的 1200 秒总预算内执行并记录。此文件的数学说明与代码必须一并冻结，随后任何修改均须形成新的清晰回执。
