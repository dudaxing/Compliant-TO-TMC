# M-AVIEW1 保存态显示输入审计（只读准备）

原 `saved_right_margin_views.py` 可以复用：它明确允许 failed/partial 保存路径，图题和view记录会保留原生产状态。本轮14态原index0..13从原点加载至1.20 mm，无额外二分；原第一次卸载没有接受态。显示通过也不会把M-ALPHA1改为PASS。当前仅静审与原字节核对，没有解码NPZ、运行viewer/observer/HF、计算新量或绘图。

## 实际读取范围

原archive函数遍历`z.files`并复制、校验全部数组。因此最小原样复用范围是 **29 NPZ／279字段实例**：model.npz一份27字段，14份state.npz各lift/fluctuation两字段，14份forces.npz各16字段。不能用科学实际使用的model7／state2／forces7字段子集来描述原入口的真实解码预算。完整path/SHA/field schema及每份字段声明身份见同名JSON；tangents、total_matrix、source_geometry和baseline的NPZ均不解码。

原viewer必须读result/model及14个state JSON；最小包装另外只读response/progress和baseline result／summary／CSV作原目标身份与原值对照。baseline仍24态成功，只匹配共同原index0..13，不重新观察baseline。不会把原baseline HP传给新alpha的`--reference`；该参数要求同结果SHA／同态数／同状态身份，现有新alpha无独立参考。

## 源码与兼容性

pure closure为hf_eval package、native_region_geometry、boundary_geometry、workpiece_nodal四个模块，加measure_native_workpiece_regions脚本与原viewer，共六份原源码。package中的legacy evaluate只是未调用的惰性定义。原viewer核模块白名单、实际来源和绑定原字节，机械hook明确false；零新力／切线／模型／求解／HP依据纯来源及保存数组推导，不是动态hook监测。

metadata确认完整lower-half square声明、中心(71,40)、边18、原Cartesian h0.5网格与Q1节点顺序、每态703个body节点，故预计9842个nodes CSV数据行。实际27字段值、tip(80,30)唯一性、body两个split字段零值和严格凸正向quad仍是运行时读取后的检查，本审计不从正minJ推导这些已验证。

原viewer的几何门是geometry_valid；raw/strict overlap及roundoff ambiguity会记录，不自动变成接触验收或view失败。节点三分量fsum须与保存body resultant精确一致，每个body holding矢量须与total ON-body相反。坐标、tip距离、分区J/Hu与Green应变都是新保存态观察；原14态cached production门和原failed路径保持。

## 显示与指标

原输出为14×geometry/nodal/derived JSON、14行states CSV、9842行nodes CSV、summary、3 PNG和14帧GIF及view.json。结构变形x1，加y40视觉镜像；镜像箭头Fy翻转，未另求上半模型。所有body节点（含cut/interior）三分量weak force一起显示，公共glyph长度只是可视比例，不是压力、连续面牵引或接触归属。

CSV的solid minJ和free-medium minJ取保存积分点值；free-medium排除固定体，Hu标量是最大绝对分量。peak_fields的J为单元积分点均值，Hu为Frobenius范数，不能混写。Green是保存F推导的二维面内主应变。tip是原reference(80,30)节点到有限bottom/left/right段的无符号距离；bottom/left连续有限face first-ray另报，null是无命中，不能置零或称压力／有效夹持。

原3PNG的PEAK/LAST均为accepted index13／1.20 mm，0.85态只在GIF中。新增成功GIF frame6与13原像素导出`loading_085_forces.png`／`loading_120_forces.png`合理，便于直接看0.85／1.20的三分量画布；须先raw PASS、14行身份／leg／原target／stateSHA匹配、GIF14帧，再提取本次新产物，不读旧图、不重画、不新增NPZ或observer。

## 最小包装与资源

旧compare_alpha_views不能直接复用：matcher强制success，15完整前缀要求未取得的卸载index14。新包装应保留原viewer字节，复用14指标及原六panel显示的小段逻辑，只允许本次failed14加载数据；新14目标对照和两张GIF像素快照使总数为6 PNG／1 GIF。字段和原节点/几何门保留，不给新alphaHP、稳定性、压力或HF5资格。

准备stage为`functional_views/native_alpha_partial_20261011/complete_001`，卡M-AVIEW1、phase view，整helper180／outer240秒、采样8GiB。原同h0.5的24态证据raw37.50952459999826秒、helper39.69886699994095秒、helper采样RSS474333184B；只作为历史实际成本，不按比例预测新运行。helper必须包括前检查、原viewer、对照、GIF提取及最终hash，rawviewer只能接剩余额度。当前尚无新数值批准或显示执行，待实际包装／protocol／card完成再独立静审。
