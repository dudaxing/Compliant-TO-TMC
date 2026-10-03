# 保存切线作用失败：全域分解诊断卡

matmul320候选一次完整F/T已返回，但独立参考首错在e0 Hu action：误差/原1e-10分母=2.424349759e-9，越过1e-9门；原reference真实exit1关闭，2次HP已完整生成，原文件永久保留。当前live内核不改，不将候选并入，也不重开原阶段。

先前仅e0保存态分析表明：原shadow swapaxes布局下einsum的收缩产生约2.42e-19绝对误差；保存同一K、同一方向的独立精确Decimal收缩误差仅约1.88e-32。e0方向局部Hv严格零，但J依赖项的真实Hu Jv仍微小非零，不能强制归零；只换fsum不能补回乘积的舍入损失。这个结论尚不能推及全部元素。

本卡只处理已经保存的三切线张量、原saved action、同一dyadic witness、两精度原参考与CSC action。一次独立进程对全部3200单元/三分量分解：原saved action与HP差异；精确保存binary64 K×保存v与HP差异；原布局再现与C布局的诊断差异。global用3000位精确scatter核原global/CSC action。精确收缩与scatter陷阱禁止Inexact，范数比较在120位处理；不调用任何F、T内核、Newton、模型构造或HP力学evaluate。新Decimal只是保存数组算术，不计为新的独立力学参考。

各误差采用原action规则max(norm(HP),1e-10)分母，总1e-10、材/Hu1e-9、80/120一致1e-40；只用于诊断分类，**无新资格**，不补写原reference的gate/pass/result。保留原saved action作为正式失败对象，不能用NPZ重载后C布局einsum覆盖它。保存逐元素/全局数据和图，显示floor仅用于图；实际物理变形仍引用粗方002七个已接受×1状态。

新独立窗口：整体helper120秒、outer150秒、8GiB采样树RSS，包含加载、全3tensor精确收缩、scatter、保存和绘图。依据e0保存数组分析约0.45秒及既有PNG数秒，采用有界完整数据分类窗口；与关闭reference剩余时间无关。仅一次，首异常/源输入变化/资源失败停止，不修复重试，无force；采样协同停止不是OS硬限。

完成后据全域分类决定最小功能修正：若证明收缩舍入主导，新增带乘积补偿的可靠切线作用入口/对比包装并另卡验收；若存在张量或映射差异，先处理实际定位。当前不提前选择改公式、改CI范围或放宽门。
