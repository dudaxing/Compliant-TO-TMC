# Cycle007七态真实结构、力、变形与边界图

目标是在1.5 mm固定方形工件机械循环上，让结构、输入/支承、输出测量、变形、力与几何接近都可人工检查。唯一render实际terminal exit0：helper3.125667100016s/173195264B，outer3.554125900031s/177995776B；120s/8GiB采样，168绑定前后不变，无重试/force。PNG3300×3150，CSV7行×60列，共420项与保存JSON/NPZ/测量逐项核对；峰actual index3、末index6，按实际chronology保留[0,.5,1,1.5,1,.5,0]，没有重复目标/状态去重、插值或动画。

×1峰值及卸载返回，4×辅助位移放大；4×图无力箭头，其视觉重叠不表示真实接触。共同N箭头标尺为0.12402162912204807 N/显示mm（0.4960865164881923 N对应4显示mm）。机制viridis与第三介质Oranges采用同一实际mm平均节点位移色标[0,2.3349311667332864]；该上限是单元平均节点|u|，不同于峰状态最大节点|u|=2.3853164371595783 mm。输入+x、自由+y输出测量菱形、实体关联支承及工件标识均明确，图例在结构外。

峰保存R输入=0.33317849323421816 N，qout=+1.7476327690686049 mm，minJ=0.16867821878132877（不是压力）。下半工件总力Fx=−0.0004918744882668527 N、Fy=+0.0009807651115565457 N，材/Hu分量另绘；这些是负保持反力的模型投影，不是夹持或接触压力资格。微小工件箭头在共同输入/支承标尺下不易看见，曲线与CSV保留数值。原Newton26/trial19按实际顺序显示，base残量不是接受态观察。

峰实际unsigned底边/全外边距0.35823198220719793 mm、left组距1.6619606664718432 mm，读取已完成测量；节点窗口bottom=0.41637603593684247、left=2.700994461573245 mm为另一代理，在CSV单列。left最近点位于工件下角，不当侧壁水平normal gap。返回态微小非零位移保留于原数组/CSV，×1视觉近似初态，不手动归零。0新F/T/consumer/assembly/solver/HP/geometry。

[PNG](render_001/cycle007_saved_path.png) SHA cf5226d299ac1d3c0c42408a6ec2576a51fd55b87b9b52946a92a132d54a12f5；[CSV](render_001/accepted_numeric_states.csv) SHA 415355f4a662102338572e20d1f0fd9578b1cf6c272e7a37a9ca582f500a7f76；[图元数据](render_001/view_metadata.json) SHA af688afc8917bee9359f1f178ed2541a715da02216947c945505586397cc8adc。冻结查看器SHA b2e9df6ce359f9bc8458a631c64fbc29995371f3532c06bcdd666808d2ea4814。

原图题PRODUCTION ONLY–UNQUALIFIED，因仅读生产缓存与几何，原HP/equilibrium/HF flags不改。[另行14次fresh HP/135364检查](../../../lf_data_preparation/native_workpiece_001/coarse_square_cycle_007/RESULTS.md)已实际terminal pass，授予明确的接受机械态范围；这不是图工具重新授予资格，也不涵盖能量/应力HP/全列T/压力/有效夹持。原媒体没有重绘。
