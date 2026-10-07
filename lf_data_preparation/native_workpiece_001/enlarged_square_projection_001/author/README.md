# 同一工件任务的端口投影初始化候选

目标是解决加大工件时，原切线预测初猜在逼近阶段越过正 J 的问题。此次只改变可选的数值初猜，检查是否能用同一 TMC 方程完成接近、加载和卸载。它尚未证明接触、夹持或收敛改善。

物理任务逐字节沿用已关闭的 `enlarged_square_contact_001`：工件中心 `(71,40) mm`、边长18 mm，半模型覆盖 `[62,80]×[31,40] mm`；材料 E=1 MPa、厚度20 mm，原 LF 几何、支撑、端口、介质与正则化参数一致。`task.json` 的 SHA256 为 `385cce960696b8c01e1323fc43d98f4ee28a392214c44a8f3609006324cde2e0`。24个原始目标仍是0→1.2→0 mm，原二分和最小增量不变。

`initial_guess='port_projection'` 仍执行真实缓存 KKT 的 LU 求解，使用它的 dR 预测初始反力，但不施加该解的 dw。位移从前一接受态出发，只按自由端口权重分布平均位移差，再由原 feasibility 函数修正舍入误差。LU 残差属于真实计算的线性解，不能解释为投影后初猜的残差。原 Newton、Armijo、正 J、回滚、最多4层二分、最小增量、力/切线和验收门槛都不改变。默认 `initial_guess='tangent'` 保留；本次需要显式指定新选项。

独立验证须实际通过15项测试（原控制器9项、native入口2项、新功能4项），无失败、错误或跳过；一次180秒、外层240秒、8 GiB。证明必须绑定 `native_mean.py` 和 `split_displacement.py` 的两项 `port_projection_initialization` 转换。切线 v5 原证明单独以 `tangent_direction_scaling` 分类，不能替新控制器证明。T44 原胶囊与协议保留原字节；其中旧的根路径控制器 SHA 是历史身份，新根路径只能由本轮控制器证明支持。

新阶段 `lf_data_preparation/native_workpiece_001/enlarged_square_projection_001` 从零开始。准备一次120秒、外层150秒；生产一次3000秒、外层3060秒，均8 GiB。每相首个正式失败关闭，无修复重试、延期、force或前缀替代。失败的原同尺寸运行保留9个接受状态及四份终态文件作为关闭上下文；旧 x72 失败上下文、已通过 x71/E1 与 x71/E0.5 的身份和成本证据继续保留。没有借用新状态资格。

当前来源仍为原68个角色中切线和两处初始化的显式转换，再加2个包装，共70个。新的测试和审查文件是证据绑定，不增加数学运行角色。`baseline_wrappers` 保存本轮修改前3个包装原字节；三份 delta 对应它们。`producer_original_96bf.py` 与 target delta 保留之前1.8→1.2的元数据适配历史，不进入运行来源。

作者仅进行文本、AST、编译和 SHA 检查，未导入候选模块或运行准备、FE、求解、HP、几何 API 或绘图；正式执行由 root 在真实控制器证明通过、独立审阅后进行。生产记录明确保存选项，检查每个真实 predictor 的 displacement_mode、applied_dw=false、applied_dR=true 并统计实际行数。完整生产若通过，才能用实际全部 N 个接受态重新冻结2N次高精度参考，再生成已保存状态的变形、作用力和有限工件边距离可视化。

可移植入口由 root 执行，所有 repo 参数为 `--repo .`。先用本外部作者目录的 `build_pose_card.py --repo . --mode prepare` 安装新卡；准备成功后用正式 `author/build_pose_card.py --repo . --mode production` 冻结生产，再交给原 F3 `launch_pose.py`。作者不运行任何上述入口，不推送。main 基线为 `b31003303960231c5cc6bf95c9fd6fe751f85da8`，origin 保持 `https://github.com/dudaxing/Compliant-TO-TMC.git`。
