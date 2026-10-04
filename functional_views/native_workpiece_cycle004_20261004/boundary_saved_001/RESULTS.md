# 新三态实际外边界距离：尚未闭合

为根据真实运动选择下一步行程，本卡复用原Q1实际外边界线段算法，只读cycle004三个新保存态，各执行一次几何测量，排除y=40对称切口。496机构外边、32工件边（bottom16、left8），保留起始/峰值/返回身份。

| index / target mm | all_exposed最短距 mm | bottom距 mm | left距 mm | 交叉 / roundoff近接触 |
|---|---:|---:|---:|---|
| 0 / 0 | 2 | 2 | 2 | false / false |
| 1 / .5 | 1.4719359640452387 | 1.4719359640452387 | 1.9022564574612992 | false / false |
| 2 / 0 | 2 | 2 | 2 | false / false |

峰值最近对为机构(78.03903207312621,30.528581643611425)与工件(78,32) mm。roundoff容差初始/返回5.684341886080801e-13 mm、峰值5.723587229937861e-13 mm。每个group都是指定工件边集对全部机构外边的unsigned欧氏距，left最短对可落在工件下角，不等于左侧signed normal gap。所有containment_tested=false，不能由无交叉排除包容，也不能把正距或微小第三介质合力标记为夹持。峰值图代理bottom1.477624456079269/left2.206238808736721 mm与真实边界距不同，应分别报告。

[实际JSON](measurement_001/boundary_measurements.json) SHA `4d622d3c2658b2ba195e23d1b16a82f999e27c7ad3fa77e3e947f04ab6364738`，[实际只读复核](actual_boundary_review.json)核对来源、计数、状态和距离；没有借用旧31d同值结果。唯一measure terminal exit0：3started/3completed真实geometry、0F/T/solver/HP；hooks恢复，29pins前后不变。helper.6144473999738693秒/40792064字节，outer1.094329999992624秒/43212800字节；原120/120秒、8GiB采样树限额包括import/hash/IO，不是OS硬cap，无重试/force。

效果为实际间距2→1.47194→2 mm，与加载缩距/卸载恢复一致，尚未证明闭隙或有效夹持。下一新卡同一方形模型探索1 mm并参考实际收敛、minJ、距离/合力再选择较大行程；signed gap、包容、接触法向、压力和夹持定义另行实现。完整目标/实现/原因/数值资格见[cycle004报告](../../../lf_data_preparation/native_workpiece_001/coarse_square_cycle_004/RESULTS.md)。
