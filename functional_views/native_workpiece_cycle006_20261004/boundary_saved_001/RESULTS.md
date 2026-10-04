# Cycle006五态实际边界观察

目标：在新1 mm机械循环的保存态上显示实际几何接近与恢复，避免把节点窗口代理或介质合力当接触。唯一measure调用5/5完成，hook恢复；39绑定前后相同。0F/T/solver/HP；helper .775346500042s /41218048B，outer1.366642699984s /45817856B，均120s/8GiB采样限额，一次terminal exit0无重试/force。

| index | d mm | all/bottom unsigned距 mm | left组 unsigned距 mm |
|---|---:|---:|---:|
| 0 | 0 | 2 | 2 |
| 1 | .5 | 1.471935964045 | 1.902256457461 |
| 2 | 1 | .924425179299 | 1.790156357371 |
| 3 | .5 | 1.471935964045 | 1.902256457461 |
| 4 | 0 | 2 | 2 |

496机制边、32工件边（bottom16/left8），双方排除y=40对称切口；各态all/bottom/left均无相交或roundoff near-touch。unsigned线段欧氏距离，未测试containment/signed penetration/接触压力/夹持资格；left最近在下角，不能当水平normal gap。峰节点窗口bottom=.948768611401、left=2.440586262978 mm是另一代理定义。

原测量JSON SHA57f7207da1f29ff9c2c1ba9fff954486588fcf0e2162115ed441d9a5973c4bd5，原geometryCLI/module/caps不改，只把包装固定3态检查换成冻结expected_geometry_calls=5。[保存身份审阅](actual_identity_review.json)核对5state/SHA/原输入/边集合，无重测。[同图实际最近点与曲线](../saved_001/render_001/cycle006_saved_path.png)0新geometry；[机械路径与资格范围](../../../lf_data_preparation/native_workpiece_001/coarse_square_cycle_006/RESULTS.md)。
