# L-CTIPGDEF1 只读力字段与符号图谱

本文件是准备期定义/selector对照，不是新报告层、指标实现或执行卡。未调用API、重算力/差量/镜像/矩、测试、绘图、读媒体或操作Git。变量`study`仅表示既有函数已经返回时的对象。

## 核心符号与单位

- ON-body为介质/模型作用在固定下半工件上的全局弱力。每个原分量都取对应内部弱力的负号：`-global_*_force`；Fx/Fy沿全局+x/+y，不是圆的局部法向。
- holding为原support_reaction在工件DOF上的总向量，方向与ON-body total相反。当前返回nodal对象中只有一个保存的total holding；该对象不暴露material/Hu独立holding或逐节点holding原数组。原producer数组/NPZ的support_reaction确实存在，本准备未打开，不作全局否认。
- total/material/regularization各自保原保存值，regularization的显示名为Hu。力已标N、坐标mm、原矩N mm，不再乘厚度或镜像系数。
- 四节点mask互斥：physical_only71、cut_only35、physical_and_cut2、interior457。physical/cut边节点集另交2；physical_only组不能直接认定为接触力。
- 原矩为相对`nodal.moment_origin_mm`的z矩，正号为xFy−yFx；默认原点是工件节点均值，不可默认为圆心。这里只引用原值。

## 当前返回对象可用selector

`s=baseline/new`，`c=total/material/regularization`，`a=0/1`，`i`为原节点数组位置，`g`为原mask名。`within_value_key=loading_value/unloading_value/unloading_minus_loading`；`cross_value_key=baseline_value/new_value/new_minus_baseline`。两组均已仅读固定两JSON确认原键，不能混用；未计算新差量。精确模板、方向和源行在JSON同名条目。

|对象|精确selector模板|单位/限制|
|---|---|---|
|cycle six signed lower-body force scalars|`study["cycles"][s]["timeline_rows"][j][field]`|N；field is one of total_body_Fx_N,total_body_Fy_N,material_body_Fx_N,material_body_Fy_N,regularization_body_Fx_N,regularization_body_Fy_N. Keep raw leg/target/d/SHA/source, do not mirror or rescale.|
|same six scalars at selected peak|`study["peak_node_comparison"]["sources"][s]["state"][field]`|N；Current global12/loading1.06 only; old accepted1 versus new accepted12. Reader checks all original37 fields, not a new mechanical pass.|
|per-node ON-body vectors|`study["peak_node_comparison"]["sources"][s]["original"]["nodal"]["forces_on_body_N"][c][i][a]`|N；565 original nodes per source; node_ids[i]/coordinates_mm[i]/masks[g][i] use the same positional i. regularization is the saved Hu weak-force contribution, not a separate pressure field.|
|whole fixed lower-body resultants|`study["peak_node_comparison"]["sources"][s]["original"]["nodal"]["summary"]["force_on_lower_body_N"][c][a]`|N；Original per-component fsum of all fixed-body node forces; current map only references saved values and does not rerun fsum.|
|original total holding reaction|`study["peak_node_comparison"]["sources"][s]["original"]["nodal"]["summary"]["holding_reaction_on_model_N"][a]`|N；仅当前返回nodal对象中的原total向量；不暴露material/Hu独立holding或逐节点holding，不否认原producer support_reaction数组。|
|four original mask resultants|`study["peak_node_comparison"]["sources"][s]["original"]["nodal"]["summary"]["groups"][g]["force_on_body_N"][c][a]`|N；Four mutually exclusive nodal categories; not a face-traction integral. physical_only71,cut_only35,physical_and_cut2,interior457. physical/cut edge-node sets separately overlap at2 nodes.|
|original moments|`study["peak_node_comparison"]["sources"][s]["original"]["nodal"]["summary"]["moment_about_origin_Nmm"][c]`|N mm；Read the original nodal.moment_origin_mm; do not assume circle centre or shift the origin. Group moment selector adds groups[g] before moment_about_origin_Nmm. No new integral in this map.|
|within-alpha existing loading/unloading force differences|`study["cycles"][s]["same_input_pairs"][p]["metrics"][field][within_value_key]`|N for the six force fields；7 original pairs per alpha. Zero reference raw leg remains origin; loading_value is a column name, not proof of a loading zero state. No recalculation or equality/return criterion.|
|cross-alpha existing scalar force differences|`study["scalar_comparison"]["pairs"][p]["metrics"][field][cross_value_key]`|N for the six force fields；20 original-target pairs; keep global_index/display_branch/d and both source SHA. The existing13 metric set also contains nonforce quantities with their own units.|
|cross-alpha existing node force pairs|`study["peak_node_comparison"]["node_pairs"][p]["on_body_N"][c][cross_value_key][a]`|N；565 node pairs and3390 component differences already stored. Preserve node_id/coordinates_mm/masks and original raw indices; no new force extrema, ratio, projection or difference.|
|cross-alpha existing group force pairs|`study["peak_node_comparison"]["group_pairs"][p]["force_on_body_N"][c][cross_value_key][a]`|N；4 group pairs/24 stored component differences; p is selected by group name, not assumed contact status.|
|cross-alpha existing whole-force pairs|`study["peak_node_comparison"]["whole_resultant_comparison"]["force_on_lower_body_N"][c][cross_value_key][a]`|N；6 stored component differences. No original per-component holding-reaction difference or new moment-difference selector is claimed.|
|node identity and masks|`study["peak_node_comparison"]["sources"][s]["original"]["nodal"]["node_ids"][i]`|dimensionless ID; coordinates_mm are mm; masks are bool；Coordinate selector replaces node_ids with coordinates_mm; mask selector is masks[g][i]; edges.closed/physical/cut hold global node-ID endpoint pairs.|
|light report association and original units|`study["report"]["peak_links"][s]`|d_mm mm; alpha dimensionless; source identity indices/SHA are metadata；Light report has metadata/selectors, not nodal vector payload. units are study.report.cycles[s].original_task.units; report.qualification preserves source declarations, missing stays missing.|

## 下半/镜像定义与现有接口边界

`native_mean.py:100–101`原生结果源码定义了total的Fy、镜像上半`[fx,-fy]`、全物体净力`[2fx,0]`及`2abs(fy)`两侧幅值和。它们是不同量：全体y净力为零不能说无相向作用，幅值和不是全体净力，更不是局部压力或已合格夹持力。
关键边界：这几个字段以及原holding DOF分区在当前两个返回源报告中均未出现；当前函数不提供可用selector。本准备不补算、插入或用它们代替已有下半有符号力。原DOF holding分区也不是四个工件几何mask。

## 角色、原值与资格

可由cycles[s].timeline_rows取20个原目标；原raw锚/角色保持。字段field取六个原body Fx/Fy名。within-alpha的loading_value在零态仍可能对应origin参考，不能按列名伪造loading。跨alpha差量只读取原new_minus_baseline，不新增率、能量或压力。
当前两峰均global12/loading/1.06 mm，旧accepted1、新accepted12分别保留；准确SHA和源selector见JSON。轻report只有身份/路径/计数/资格，不含完整节点值，须通过已经返回的peak_node_comparison原对象访问，不能把轻selector字符串当值。
所有原资格分别保留，未读新的HP或原历史。节点弱力、原分组和图像都不授有效夹持、压力、释放、稳定性、alpha独立性、网格/域收敛、全路径参考或HF5资格。

## 源码定位与SHA

|源码|关键行|SHA256|
|---|---|---|
|`hf_repo/src/hf_eval/workpiece_nodal.py`|13–21,36–42,49–76|`697e056fee1bddf4a611f2fc6e83de10747d923627b5f2d28c34eaf9a1d33ae9`|
|`hf_repo/src/hf_eval/native_mean.py`|67–106,221–227,288|`76fd9917fe378865f3f359838958e58505afb9ae2e7c7ec257773a76178fd6e4`|
|`lf_data_preparation/native_interface_001/lf_circle_tip_alpha_report_001/saved_study_report.py`|54,94,103–119,137–144|`6537e31abd56a1c6749fa3ba2969f4a1af930ed080cd2af81e7125d7f8764ad3`|

已有轻report：`lf_data_preparation/native_interface_001/lf_circle_tip_alpha_report_001/run_001/report.json`，22172 B，SHA `718bfc5a8cd7b85f163ae4e7dc18c47f2d8f7c881465a138a3b8e9f1ddc497c6`。
另仅解析两份已经绑定的comparison普通JSON确认字段路径/名称存在性，未计算新数值；没有打开原node/cycle/完整历史文件或任何数组/媒体。输出仅本.md/.json两份指定说明文件。
