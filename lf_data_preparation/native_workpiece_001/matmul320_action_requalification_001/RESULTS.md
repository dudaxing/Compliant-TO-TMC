# 补偿切线作用：保存数据重新验收实际结果

目标是实现可靠的NumPy切线作用消费入口，解决原view布局einsum的消减舍入失败，支持随后有序卸载和平衡路径的独立检查。整体物理目标、原范围异常、matmul320最小候选及全域诊断详见[连续过程](../matmul320_candidate_001/RESULTS.md)。本卡一次执行已通过，但未增加新的物理平衡态。

## 实现与实际结果

29行 `hf_eval.tangent_action.apply_element_tangent_numpy` 沿用既有CI乘积EFT和固定顺序两词求和，只在返回作用处舍入一次；不改原张量、TMC公式、原支持域、门限或分母。consumer SHA `b52f8b5ab279321f6e716885dd00dae946929c4b7c23d97d98d9bcd7f5b593fe`，冻结源码副本位于 `sources/`。生产张量来自先前隔离matmul320候选7fff，不来自当前live旧内核。

唯一新requalification真实exit0/pass：helper 12.672814900s、peak_wset 375730176B；outer 13.338634200s、采样树峰 368619520B。310个protocol绑定前后相同，stop_reason=null。helper120/outer150秒、8GiB合作采样窗口；采样不是OS硬内存限。没有重试、修复或force。

3次新consumer开始/完成。**本轮新F/T内核/HP力学evaluate/solve/JIT均0**；历史候选1F/1T及原reference2次完整HP80/120在结果中分别继承记录。原reference首错exit1及原saved action不改；此卡是方法改变后的新保存数据资格，不能冒称原reference当时已通过。

全部3200单元×三力/三作用共19200局部门、9个全6642DOF全局门通过。614400局部张量存储贡献用于独立重构三完整CSC，data/indices/indptr与原保存全部逐项字节相同。一个方向的action HP验证与全部CSC系数存储核对是不同覆盖范围，未穷举矩阵列。

| 原规则类别；全部local/global中的最大归一误差 | total | material | Hu |
|---|---:|---:|---:|
| force | 7.943165973e-30 | 7.742121142e-18 | 7.481829865e-20 |
| action | 7.243359874e-15 | 1.160238823e-16 | 1.010655561e-16 |
| CSC_action | 1.543546097e-16 | 1.439647753e-16 | 1.097136972e-16 |

总force/action门1e-11/1e-10，材/Hu各1e-9；原力floor2e-13N、action分母max(norm(HP80),1e-10)、分力floor1e-12总尺度保持。全部HP80/120一致最大 1.412526706e-52 <1e-40。HP值原字符串精确载入，3000位/Inexact陷阱scatter，120位范数/比较；不是重新HP求值。

## 证据与人工检查

`evidence/actions.npz` 保存三个实际新local action及三个实际新global action；`checks.json.gz`19209门、`differences.json.gz`完整差值、`inherited_HP_globals.json.gz`保存两原HP的独立scatter、`result.json`来源/实际计数/最坏门；launcher回执保存真实exit及310绑定。四份执行前静态审查和随后实际证据复核分开记录，不将静态判断当运行通过。

此前[全域诊断图](../matmul320_saved_action_diagnostic_001/evidence/saved_action_differences.png)的橙点是**精确保存K×v**，不是本29行consumer。随后独立保存态查看卡一次实际exit0（outer2.35793s），[新实际consumer与原失败数据图](../matmul320_action_view_001/evidence/requalified_action_errors.png)已由root打开检查，9600行数表和322来源绑定保存；0新consumer或力学调用，不增加新的形变或夹持证据。

## 资格边界与决定

资格仅属于完整捕获F36、新尺度候选7fff、补偿consumer B52和同一声明dyadic witness。源码范围支持的格点证明只适用于这份K/v（最细2^-172、8项绝对和<96），不承诺任意方向和张量。压力/真实接触、平衡、应力HP、全部矩阵列、其他状态的资格字段均false。旧七个0.5mm状态归旧31d955源码，不因本卡通过而迁移。

live核心暂不合入，保持旧源码和此前全部记录可核对。下一独立阶段逐字节合入已验证的7fff候选，替换新路径审阅器的action消费入口并重新冻结；同粗方 `[0,.1,.25,.5,.25,.1,0]`mm一次新循环，对所有新接受态fresh80/120核验后再探索1mm。当前1/2/3mm未执行。真实底距离旧峰值1.471935964mm，尚未夹紧。主干main，origin仍 `https://github.com/dudaxing/Compliant-TO-TMC.git`。
