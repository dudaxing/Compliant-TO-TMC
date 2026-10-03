# 新循环F16范围拒绝：独立保存输入诊断

coarse_square_cycle_003正式生产已经exit1关闭，600秒内未完成返零；仅初0及峰.5为接受态。原生产/参考/查看卡不重开、不延时、不转为pass。本阶段专门研究新的实际F16输入，不复跑失败路径，不修复生产源码。

唯一调用当前7fff内核的原NumPy完整力入口一次，输入为原保存16字段、state 9dbd3c95、archive47824b83。沿用已审阅观察器，明确改003路径、source63/input25，并在原资源检查点读取新launcher的阶段stop文件；通过_finish/dd_from包装保存按执行顺序第一个不支持返回，再恢复原函数。期望原外层unsupported_arithmetic_range异常逐字段复现；观测不得替换输出或掩盖异常。0切线/组装/求解/HP/JIT/LF。第一个坏分支可能未被选中，不能单凭时间顺序断言最终输出原因。

新整体helper60秒、outer90秒、8GiB采样树，协同检查、无force/OS硬限。按全部来源、旧关闭生产及输入归属前后冻结；输出新exclusive evidence。一次且首错关闭，无重试、修复或资源延长。expected诊断捕获成功仅为diagnostic_captured，qualification=false，不给F16或两接受态数学/接触/循环资格。后续按实际primitive与完整路径日志决定修复或分段，不凭猜测扩大算术域。
