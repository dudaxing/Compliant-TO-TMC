# 全域保存数组诊断的实际结果

一次正式analysis真实exit0，outer5.1519525s，采样树峰257421312B；helper4.554007s，peak_wset334696448B。291个冻结绑定执行前后相同，stop_reason=null。0新F/T内核、0HP力学evaluate、0solve/JIT；Decimal仅消费保存数组，资格字段为false。

同一候选3200单元、三分量、同一完整F36输入和dyadic witness，9600个局部作用均与HP80/120保存参考比较。原action尺度max(norm(HP),1e-10)，总1e-10、材/Hu1e-9，80/120一致1e-40保持。精确保存binary64 K×v及HP全局scatter在3000位/Inexact陷阱下完成，范数比较120位。

| 分量 | 原saved action越门 | 精确保存K×v越门 | C布局einsum越门 | HP80/120一致越门 |
|---|---:|---:|---:|---:|
| total | 0 | 0 | 0 | 0 |
| material | 0 | 0 | 0 | 0 |
| Hu regularization | 693 | 0 | 507 | 0 |

三个原swapaxes view replay与原saved action全数组字节相同。9个global原作用/CSC/精确局部scatter比较均在原action门内，最大归一误差约1.54355e-16；Hu global尺度约0.8104135、总/材约1481.09/1480.64，不能用整体通过抹去693个局部越门。

![完整单元误差分布](evidence/saved_action_differences.png)

图中蓝点为原保存作用，橙点为精确保存K×v，红线为原门。显示floor1e-30只处理log显示，不参与判门。图由本卡一次处理实际数组生成；原失败对象与完整HP永久保留。e0/1275/1348例见 `evidence/examples.json`，全部9600分类见 `evidence/element_classification.json.gz`，global见 `evidence/global_diagnostic.json`。

结论支持优先修正消费端的乘积和求和舍入，而非改切线物理公式、裁零或降低原门。本诊断本身不授候选资格，后续新补偿consumer必须另冻结并重新判完整原力/action/CSC门。物理状态仍见[粗方002七態](../coarse_square_cycle_002/RESULTS.md)，本卡不增加变形或夹持结果。
