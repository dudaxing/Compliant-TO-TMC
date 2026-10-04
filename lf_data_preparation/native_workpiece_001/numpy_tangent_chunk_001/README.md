# NumPy 切线分块独立诊断卡 001

目标是保留固定工件 1.75 mm 完整九目标路径
[0, 0.5, 1, 1.5, 1.75, 1.5, 1, 0.5, 0]，解决 cycle008 时间超限。
上一轮 RESULTS.md 中删去卸载 1.5 mm 观察点的后续建议不作为本轮执行计划。
本轮先验证功能等价与实际成本，不运行新的平衡路径，也不补发 cycle008 的 HP 资格。

## 唯一实现变化

split_numpy_tangent.py 提取原 DD 计算为 _tangent_pairs，提取原全域支持检查和
swapaxes 为 _finish_tangent。默认 _tangent 仍做一次整批计算。
新增私有可选 _tangent_chunked：固定 256 单元连续块，完整批次只选择一次
small_products 分支，各块复用。每块保留全部九积分点、八方向及原固定求和顺序。
三份完整 DD 张量填完后按原 total/material/regularization 顺序统一支持检查，
最后仍按原全域 COO 顺序组装 CSC。CI/force/控制器/物理任务均未改；
TANGENT_VERSION 及默认生产接线未变。候选不因写出代码自动获准用于新路径。

## 两个独立有界窗口

1. tests：一次 pytest -x，原 tangent 测试及新增 chunk 风险测试；
   helper 120 s / outer 150 s / sampled RSS 8 GiB。
2. comparison：只有 tests 正常结束后才执行一次；helper 180 s / outer 210 s /
   sampled RSS 8 GiB。原点007/000、峰008/004、回零007/006，顺序固定。

协议冻结精确输入、旧源码快照、新源码快照、测试和测量脚本 SHA。
任一正式错误关闭当前卡，后续窗口不执行；无修复重试、无 force、无续时。
限时为调用边界协作检查和进程树 RSS 采样，不能称为操作系统硬中止；
结束时超过预算仍不通过。

每个实际保存态从原27字段模型和精确 lift/fluctuation 执行一次 mechanical rich F，
保存 retained hi/lo cache。旧保存的16个力场没有这些 pairs，不能直接重建切线。
同一 rich cache 各执行 archived original / factored full / chunk256 一次 T，
三者不重算力。精确比对9个保存力字段、三张完整切线张量、旧布局 strides、
完整 CSC data/indices/indptr；每次比较立即验收，首次差异停止。
三态合计3 F、9 T、9 CSC组装；0 Newton/平衡求解/HP/JIT/LF调用。
pytest 内部 F/T 单独运行且不混入这组计数，未知的内部计数记 null。
编译入口在比较及针对性测试中被禁止调用。

数值门为 dtype/shape/bytes 全同，不引入容差。时间是各候选一次执行的 wall time，
不视为重复统计基准。每态 archived/chunk >=1.25 才判成本值得进入后续接线。
该成本决策不改变力/Jv/KKT/工件及 HP80/120 的原验收门。

## 输出与解释范围

comparison_001 保存 rich cache、三种实现完整三切线和完整CSC、每态比较结果；
各窗口保留终态、资源与输入/源码未变记录。可视化展示实际单次耗时及等价范围。
旧峰008仍 production-only unqualified；旧007独立参考资格按原 scope 保留。
本卡只证明给定保存态和小型风险态的算法等价与成本，不证明所有新路径、
全列高精度、接触压力或有效夹持。成功后下一步才冻结新的完整九点求解及独立审计卡。
