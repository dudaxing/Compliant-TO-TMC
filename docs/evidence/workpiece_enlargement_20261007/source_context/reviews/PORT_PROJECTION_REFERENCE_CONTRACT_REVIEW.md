# 端口投影初值：只读参考合同判断

本文件仅是 2026-10-07 的代码审阅与方案判断；未修改正式源代码，未执行构造器、F、T、求解器、HP、几何 API 或绘图。此前 side18/x71 的默认预测器生产已经失败，原完整参考与 final 文档 collector 均不得执行或声称通过。

保留真实 KKT 预测 LU、使用其 dR 预测初始反力，同时丢弃 dw 并采用端口投影，是合法的混合初值。初始反力可以是线性模型给出的估计，初始位移可以另选满足平均约束的状态；最终的非线性残量、平均约束、Newton、Armijo、回滚、J 守卫与收敛门必须保持原值。原预测 LU 的残差只检验该真实线性解，不检验丢弃 dw 后的候选状态。新候选的残差由原 Newton 首次真实 F/T 计算，不能把初值或线性残差写作已达到平衡。

建议端口调整使用当次完整平均约束残差：在自由端口方向 b_free 上增加 rhs_mean*b_free/(b_free·b_free)，其中 rhs_mean 同时考虑实际 lift 和 target_origin；不只写成 s-old_s。这样获得端口方向上的最小范数平均修正，再由原 feasible 的单点操作修正舍入误差。非端口 fluctuation 与固定零 fluctuation 保持前态；本固定工件任务的 lift 为零。这里的初始调整不是新的节点位移硬约束，后续 Newton 仍只控制原端口平均值。

每条真实 predictor LU 记录至少明示 displacement_mode='port_projection'、applied_dw=false、applied_dR=true，并保留实际线性求解残差及原 mean_error_before/after_projection。card、inventory 和 result 的 initial_guess 选择必须一致，执行前固定。旧默认路径保持原算法与 DisplacementSettings。初值反力是否适合新任务只能由实际路径判断；采用 dR 不自动证明比保留前态 R 更好。

原 B028 counter 可按原字节复用。它在第 28–40 行以实际 predictor LU 划分尝试，在第 107–110 行要求非原点尝试存在 predictor，在第 120–123 行识别首个 predictor-base invalid_J。保留并实际使用 dR 的 LU 满足这些原合同；新增字段没有被其现有字段检查禁用。所有 F/T、Newton history、试算、回滚与接受缓存序号继续按原逻辑重构，不伪造 predictor 或调用数。若将来完全移除 predictor LU，则 B028 原样不支持，须另设真实初始化边界的计数合同；该先前无 LU 方案已被本次混合方案取代，未执行。

原 B850 run_state、aa86 工件投影、B52 保存切线作用和 fresh all-actual-N HP 循环，与初始猜测选择无关，可以保持原字节及原数学门。新 LOAD 仅应验证初始化选项和每条 predictor 的三字段、实际生产全路径及原计数合同，并声明 split_displacement.py、native_mean.py 与新包装的真实源 SHA 变化。原切线 v5 过渡与历史失败/通过 capsules 分开保存；不借旧状态 HP，不把 source 范围扩大为重新审阅全部历史任务。

这份判断不提供接触压力、失败预测态 J 位置、完整新路径或夹持稳定性资格。实际新卡需要零起点完整加载卸载成功，再对每个实际接受索引单独完成 HP80/HP120；若遇到原计数合同未支持的新 trace，保留失败并按实际证据修订下一明确卡，不改原记录。
