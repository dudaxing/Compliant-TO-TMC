# M-RESUME1：从保存峰值态执行首次下降

状态：候选和静审已准备，未授权、未执行；执行时绑定本阶段 protocol 与发布提交。

## 目的与判断依据

整体目标是独立 HF 有限变形／TMC 前向评价：读取普通几何，在一致物理任务下计算实际变形、输入反力与工件作用，供外部研究层比较。HF 不做 LF 优化，不使用 dmftd 或 MPM。

M-ALPHA1 已接受并保存 alpha=5e−7 的14个原点／加载目标至1.20 mm，但第一次下降至1.15 mm因controller时间预算停止，完整任务 NOT_PASS。M-AVIEW1已实际生成14态显示并发布。已有证据只支持“原时间预算耗尽”；不能据此认定卸载不可能、切线有误或物理失稳。

最近的功能缺口是公共 Mean／API 不能从保存的非零平衡态开始。因此本卡验证一个隔离候选：复用原峰值 split 位移和 R，从原绝对目标 [1.20, 1.15] mm 执行第一个下降段，避免重算已经完成的长加载。

## 输入与不变条件

原父包：`../regularization_sensitivity_001/run_001/alpha_half/result.json`，接受态013（原目标13），split SHA fa0054288cd7eca4140f8bf04a94b5f833278b1c6e39813beb57cae16d7e9bca，R=0.37865427196005513 N。selected state.json、state.npz、父 result/model/source geometry 与候选、完整源码包闭包均按最终 protocol 原字节绑定。

保持原 h0.5／84×40 mm 下半域、固定方体 center(71,40)／side18 mm、E1 MPa、nu0.3、厚20 mm、gamma1e−6、Lr80 mm、alpha5e−7、原BC与平均端口、原15目标物理任务。候选段用原目标13和14，target_origin=0、initial_parameter=1.20；不改写任务为新两目标任务。

生产仅解码两个旧NPZ的六字段：source geometry的四个uint8掩码，selected state的float64 lift/fluctuation。不读取旧 model NPZ、力、切线或稀疏矩阵的字段／字节。四份旧JSON为 result、model、selected state、geometry；task来自原model内嵌任务。本阶段输入绑定哈希只覆盖明确选中的旧输入，不声称全旧目录重新校验。

原 response_mode=mechanical、tangent_mode=chunk256、initial_guess=port_projection 保持。原controller设置保持，仅新增时间窗口：tolerance1e−9、constraint_tolerance1e−10、displacement_scale_floor1e−6、force_scale_floor_factor1e−8、max_checks25、armijo_c1e−4、max_backtracks12、max_bisections4、minimum_increment0.00625 mm。

## 唯一执行顺序

1. 在新 run_001/source/hf_repo 中复制绑定原源码并叠加审阅候选。运行最终 protocol 指定的唯一局部测试组；测试失败立即终止，不进入真实力学。
2. 调用候选 evaluate_native 一次；从原 saved split/R 恢复并重建同一几何、材料、BC和端口。初始 K=None，峰值锚点重新计算力与切线；必须直接满足原平衡／mean／J门及状态SHA一致。锚点不允许Newton修正；不满足时以 initial_state_not_equilibrated 停止。
3. 使用新鲜锚点切线进入原1.15 mm下降目标。一般非对称增广系统、R符号、line search、原有界二分、检查次数与生产门不变。目标间距0.05 mm和最小步0.00625 mm最多允许8个下降段；成功时保存接受态总数 N=2..9，不要求固定两态。
4. 同一次 API 用已有接受缓存写出新模型／状态／力／切线／矩阵及摘要，保存和摘要额外F/T=0。typed controller非成功先保留实际已接受状态和失败响应，再按本卡终止；不启动显示。
5. 仅生产成功后，在独立纯读取进程中复用原 saved_right_margin_views.py 与原四个纯模块，读取新保存态。输出3PNG和N帧实际变形GIF、表格与状态摘要。仅读取一个新model NPZ的27字段和2N个新state/forces NPZ的18N字段；geometry/nodal各N次。无HP参考、无额外F/T/平衡。

## 验收与资源

唯一启动，一次连续helper2700秒／outer2760秒（约46分钟），采样8GiB。局部测试120秒，controller1800秒，纯显示600秒；其余覆盖启动、构模、保存、摘要、检查和实际终止。预算是有界探索，不保证下降收敛。CPU／RSS采用既有采样及协作停止，不是硬OS内存限制；单次正在执行的组装可能跨过controller检查点，outer按真实终止计时，不强制杀进程。

局部测试必须全部通过；真实段保留原生产 residual≤1e−9、原逐态constraint_bound、J>0、全局力平衡≤1e−6、固定DOF split和≤8e−11 mm。峰值锚点 state SHA 必须等于父态，原任务／设置（除clock）／来源身份保持。成功须接受原目标13／14并达到1.15 mm，缓存生产门及显示原检查通过，原绑定在退出时不变。具体门以原已发布生产合同及 protocol 为准，不额外引入独立压力门。

首个终端非成功停止。无重试、修复重跑、延期、force、新HP、重新长加载、alpha扫描或默认力核切换。本卡之前不启动局部测试或真实力学；卡后不凭剩余墙钟重启。

## 记录、可见效果与解释边界

新结果仅写本阶段 run_001；原M-ALPHA1 result/14态、原M-AVIEW1图件、science0.5.0及已有资格保持。记录局部测试、真实调用次数、逐接受态 split/R/残差/作用力、typed失败、耗时和RSS，保存源码覆盖身份与外层真实退出。全部文档与候选留在main，可换机器恢复；默认 hf_repo 暂不安装候选，待实际证据决定是否集成。

成功显示实际峰值到下降段的形状与有符号 total/material/Hu 工件力，PEAK是恢复锚点、LAST是接受的终点。失败则说明实际停止位置和已有部分态；不绘制不存在的卸载态。

“候选下降段完成”与“原完整任务完成”分别记录。原父路径NOT_PASS与未完成标记不修改；新短段成功不自动升级完整原路径／有效夹持／连续总压力／物理稳定性／新alpha独立HP／HF5资格。矩阵来源、未改核心字节和本次明确变更的Mean/controller入口分开记录。

## 依据与下一步

本卡依据 M-ALPHA1 的真实峰值及超时、M-AVIEW1的实际显示、UNLOAD_COST_AUDIT、CONTINUATION_CONTRACT、SCOPE_PERSISTENCE_REVIEW和最终候选／测试／helper静审。静审不是数值通过。先得到首次下降的实际结果，再决定集成入口、继续原剩余路径或排查具体失败；不预先安排新参数扫描或重做离散力账本。
