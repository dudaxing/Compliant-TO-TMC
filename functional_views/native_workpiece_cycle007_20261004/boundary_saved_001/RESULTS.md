# Cycle007七态实际边界观察

目标是在新1.5 mm机械循环的保存态上显示真实几何接近与恢复，避免把节点窗口代理或第三介质合力当接触。唯一measure调用7/7完成，hook同实例恢复；49绑定前后不变，所有实际接受index含重复1/.5/0均保留。0F/T/solver/HP；helper0.730944100011s/41910272B，outer1.252367500041s/45580288B；120s/8GiB采样，实际terminal exit0，一次无重试/force。

| index | d mm | all/bottom unsigned距 mm | left组 unsigned距 mm |
|---|---:|---:|---:|
| 0 | 0 | 2.000000000000 | 2.000000000000 |
| 1 | 0.5 | 1.471935964045 | 1.902256457461 |
| 2 | 1 | 0.924425179299 | 1.790156357371 |
| 3 | 1.5 | 0.358231982207 | 1.661960666472 |
| 4 | 1 | 0.924425179299 | 1.790156357371 |
| 5 | 0.5 | 1.471935964045 | 1.902256457461 |
| 6 | 0 | 2.000000000000 | 2.000000000000 |

表值仅显示舍入，原JSON保留完整binary64数值。每态496机制边、32工件边（bottom16/left8），双方排除y=40对称切口；all/bottom/left均无相交或roundoff near-touch。unsigned直Q1外边线段欧氏最短距，未测试containment/signed penetration/接触压力/有效夹持。

峰index3：底部最近工件点(78,32) mm，对应机制点(78.02883763663667,31.642930617681507) mm，距离0.35823198220719793 mm。left最近工件点(62,32) mm是下角，对应机制点(62.13102016940224,30.34321185056467) mm，距离1.6619606664718432 mm；不能称水平normal gap。峰节点窗口bottom=0.41637603593684247、left=2.700994461573245 mm是另一代理定义，不能与真实边界距混称。

[原测量JSON](measurement_001/boundary_measurements.json) SHA ebd98815cf5c569f9244002bf66a4e7249c1cec3ac3d5cdba7b704171a248d0d；[测量回执](measurement_receipt.json) SHA ff92918851b44cf592165dc0da4b702958aa2d2d2892cb8e5abdd301bbae732f。原geometry CLI/module不改，包装只把固定3态次数检查换成冻结expected_geometry_calls=实际7，调用参数、原返回与恢复hook保持；没有重测旧卡。

[同图的实际最近点与曲线](../saved_001/render_001/cycle007_saved_path.png)仅读取本测量，0新geometry；[机械路径与另行14次fresh HP/135364检查资格](../../../lf_data_preparation/native_workpiece_001/coarse_square_cycle_007/RESULTS.md)。测距本身不授机械、接触或夹持资格，原图仍production-only。
