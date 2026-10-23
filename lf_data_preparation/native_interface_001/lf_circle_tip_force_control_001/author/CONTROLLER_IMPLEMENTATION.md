# L-CTIPFLOAD1 低层候选实现说明

2026-10-23。文件：`D:/hfl1_001/candidate/hf_repo/src/hf_eval/split_guided_force.py`。
这份说明只记录本次候选实现及静态核查，不是测试或数值通过证据。

## 功能与边界

- 新增不可变 `GuidedForceSettings`，只有必填、正有限的 `minimum_force_increment_half_N`。旧 `DisplacementSettings` 必须显式传入；其 mm 最小步长不用于 N 路径。
- `solve_split_guided_force_path` 签名按本卡统一接口。未知为原自由 fluctuation、一个刚体 x 平移 q、输入乘子 R；body-x 全部取 q，body-y 和 body fluctuation 保持零。输入机构均值从 contract 的 d_hold 保持。
- 只接受至少两个有符号有限、严格递增的绝对 half N 目标。不给 q 目标，不转 full N，不乘厚度，不夹限 q，不支持卸载或力控保存态延伸。
- 首态必须是 fixed 父的原 q=0 split。首目标执行一次 fresh F/T，原自由残差、mean、新 generalized 力门必须直接通过；否则 `initial_state_not_equilibrated`，无 projection、predictor、linear solve 或修复，原 split/R 保留。

## 离散方程及精度

复用旧 `split_average_measurement` 的乘积补偿、split 分量测量和 mean 扣目标规则。仅在后续预测与 Newton trial 用原非 body 端口 pivot 补偿 mean；q 不参与投影。

在原实际 K 上分别计算 K_FF、K_Fc（body-x 列求和）、K_cF（body-x 行求和）和 K_cc。两向耦合没有以转置替代，c 是 1 而非平均权。`_linear_solve` 复用一般 sparse LU；它的 `target_displacement` 保持 d_hold/mm，另列 `target_force_half_N`，不混用 P 与位移字段。

Q 用 body-x 内力的 `math.fsum`，g=Q−P。旧自由残差尺度 SF 与新 SP=max(abs(P),abs(P_anchor),force_floor) 分开；每次目标的 SP 固定，每次 line search 的 SF 固定为当次 base SF。merit 为 `.5*(||r_F/SF||²+(g/SP)²)`，沿旧 Armijo、checks 和 backtracks 上限。N 二分仅用新 force_settings 步长及旧 max_bisections。

接受态包含旧 split/R/mean/自由残差/组件/J/全局诊断、新 q/P/g/SP/bound、原目标序号和内部二分分类。试算、失败回滚身份、线性诊断、时钟和 callback 保留。预测诊断列 dq/dP；已有 reduced Jacobian 和一般 LU backward-error 诊断可供有限小模型测试观察，无新增 F/T。生产控制器不分配大模型 dense conditioning 矩阵。

## 外载账本与验收分工

support 仅取原 fixed DOF 去除 body-x，保留去重后的 body-y 导向及原 zero。全局平衡显式加入 `(P_half,0)` 一次，原 body-x support 不再重复计入。低层计算该诊断，但不因任意 synthetic oracle 的非守恒 global 合量而拒绝；真实路径 global≤1e−6、rigid/zero≤8e−11 mm 等原门由薄 API capture 检查。

## 静态核查

只读取四份已发布规格及旧 controller/linear/probe/split_state；只新增本候选文件。已使用 Python 标准库 `ast.parse` 检查语法，未导入 hf_eval、NumPy 或候选，未 collect/pytest、未生成新科学场、未执行 Newton/F/T、未触及正式 55 份生产源码。独立静审、源冻结与唯一授权窗口由 root 随后安排。
