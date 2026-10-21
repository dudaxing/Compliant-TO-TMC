# L-CTIPAFORCE1 只读准备：原 FORCE1 普通输入合同

日期：2026-10-21 Asia/Seoul。当前仅核查原实现与记录，未执行新处理、计算、绘图、测试、Git或默认源码修改。未读取三个输入本体、科学数组或媒体；下面定义来自原FORCE1的execute_step.py、force_views.py、protocol.json、RESULTS.md及run_001/execution_receipt.json。没有读取全历史。

## 三个原输入及身份

以下路径相对仓库根；共同前缀为 `lf_data_preparation/native_interface_001/lf_circle_tip_step_010/run_001/view/wave_circle_tip_step10/001/`。

|文件|原字节数|原SHA256|
|---|---:|---|
|nodal.json|163731|6bad001bcc762cc295d6238b1b33cdaaba9327312592d35550567a43c35f7e2f|
|derived.json|6327|5d3baa7ce000e93431297621fed2a0087fb6d57e51fc64e815a4675fc48e324a|
|geometry.json|54909|3dbf7ac0b94febfce3723f2a2ded942358e20565baf408cd12837ead5c9a632f|

原所选态：accepted index=1、original_target_index=12、leg=loading、d=1.06 mm；state SHA `dd9288140ae51ff3cfcc7f7f6d6811b2242a55054454002bd7c06ff88a4b6bc6`。这是旧alpha=5e-7的峰值，不能充作新alpha的输入或参考。新alpha输入未在本次只读核查中打开。

## 原输入字段合同

`nodal`使用：

- `node_ids`：全局节点ID列表；长度n且唯一。
- `coordinates_mm`：与ID逐行对应的有限二维坐标。
- `masks`：按原次序 `physical_only, cut_only, physical_and_cut, interior` 的四个布尔列表，每列长度n。
- `forces_on_body_N`：按原次序 `total, material, regularization` 的三个列表，每项n个有限二维向量。
- `edges`：原边组映射，每条边恰为两个已列节点ID。绘图使用 `edges.closed`；原程序不重新构造或分类边。
- `moment_origin_mm`：原力矩参考点，原记录为[80,40] mm。
- `summary.force_on_lower_body_N`：三分量各[Fx,Fy]；`summary.holding_reaction_on_model_N`：[Fx,Fy]。
- `summary.moment_about_origin_Nmm`：三分量各一标量。
- `summary.groups`：原四类，每类含 `node_count`、`force_on_body_N`（三分量各二维向量）、`moment_about_origin_Nmm`（三标量）。

`derived`使用完整 `row`，包括原index/original_target_index/leg/d_mm/state_sha256、全部原观察项及六个 `total/material/regularization_body_Fx_N/Fy_N`；另用 `tip_surface_witness.distance_mm`、`tip_surface_witness.point_mm`。原row须完整保留。

`geometry`使用 `boundary.groups.all_exposed.minimum_boundary_distance_mm` 及 `boundary.groups.all_exposed.closest_pair.mechanism_point_mm/workpiece_point_mm`。几何见证连接线是距离说明，不是力方向。

## 符号、节点与分组

ON-body为原保存内部弱式力的负值，单位N。`holding_N`由ON-body逐节点、逐分量取负，仅为显示记账；只有原summary的total holding作为原保存反力值独立保留，材料/Hu的反号不是新测得的独立支反力。

原记录n=565；四类计数为71/35/2/457，原观察每节点恰属于一类。物理边界节点集合和切面节点集合在physical_and_cut的2节点重叠；两边集合不能直接作为互斥分组相加。新阶段应保留原mask，不重定义、不按力大小过滤、不裁零。

固定坐标依据原protocol已绑定的producer合同：原viewer在观察前要求工件全部lift及fluctuation严格为零，因此参考工件坐标亦为该固定工件实际坐标；本次没有重新执行这一检查。仅有工件全部坐标、机制尖端和距离见证点，三份JSON不足以重画完整夹持器变形。

## 原对账规则：身份/来源检查与描述量分别保留

原严格检查：三个JSON的bytes/SHA；derived.row所选身份五元组(index,original_target_index,d_mm,state_sha256,leg)；ID唯一、各列长度/有限性/掩码布尔类型；各mask计数精确等于原summary.groups.node_count；原summary三力[Fx,Fy]精确等于derived.row对应六标量；geometry最小距离精确等于row.minimum_boundary_distance_mm；derived尖端距离精确等于row.tip_to_raster_boundary_mm；边端点全在ID集合中。

原新描述量仅普通算术：math.fsum全部节点及四mask各分量，减原summary原值；max(abs(total-(material+regularization)))；原holding+原ON-body total；每分量模最大值及原节点见证、严格零数、分量极值、正/负分量求和。它们不设新容差或相等门，不裁掉尾差；原矩不重积分、不转移参考点。旧结果记录重求和差为0、分解最大尾差1.3010426069826053e-18 N，仅为既有记录，不是本次重算。

## 显示与资格边界

原两图：force_vectors.png（所有565节点、三分量ON-body与反号方向、共享箭头mm/N比例、实际几何x1）和force_components.png（全节点有符号Fx/Fy、直接使用原summary四组结果）。无镜像倍增、径向投影、压力、连续表面牵引、有效夹持或自由工件响应推断。

旧GIF仅原stat/link：`lf_data_preparation/native_interface_001/lf_circle_tip_step_010/run_001/view/wave_circle_tip_step10/actual_states.gif`，原306111 B；原人工页：`lf_data_preparation/native_interface_001/lf_circle_tip_step_010/run_001/REVIEW.md`。本次未stat或打开媒体。

旧FORCE1普通receipt明确3个JSON读取、1次GIF stat、新科学/HP/测试/安装/API均0。新阶段须另定当前producer输入来源与绑定；本说明不授权或启动新执行。
