# L-CLOCAL1：圆形工件1.35 mm保存场空间定位

执行 **PASS**；helper `pass`／outer `pass`。原S4生产成功记录保持。

最小J与最大Hu已定位到不同部位。最小J=0.08623624515762662来自自由第三介质单元10394、Simpson q2（xi=-1、eta=1），实际位置(73,31) mm，恰与原最近见证的工件端点重合。该单元与该工件边共用一个角点，并非拥有整条面对边；这里报告的是介质侧的单元梯度，不能把该J当作固定工件内部J或表面压力。

最大absHu=0.41607250505717375/mm来自单元10368，其实际代表中心为(59.88354518548698,30.783401623846615) mm，位于左侧机构转角邻域的非工件介质。两个精确并列分量为Hu[1,0,1]与Hu[1,1,0]，均为负值；中心不是唯一Hu极值点。高Hu单元还包含工件阶梯边缘邻域的次高簇。

J衡量一阶位移梯度对应的局部面积变化，Hu为相对参考坐标的二阶位移Hessian。强压缩与强非仿射变化可以位于不同部位；本次分区、点序、原标量与坐标映射未发现不相容。这个解释说明极值为何不必同位，并未量化工件Hu合力的局部来源：原约80.5%的Hu/Fy比例来自弱式力组装和固定工件节点求和，不能由最大Hu或排名位置反推。

据此可考虑下一段L-CSTEP5以0.05 mm增量从原成功1.35 mm保存态推进到1.40 mm，保持原物理、设置和验收门。本次未执行该段，也不预测下一态的J、间距、力或收敛；没有新增J截止门、独立HP或夹持资格。

整体目标为普通LF几何进入独立HF/TMC前向分析，逐步实现可检查的加载、传力、夹持相关响应和卸载。本次只定位已保存的J/Hu极值和最近边界关系，用于判断更强介质压缩发生在哪里；不重算平衡路径。

保持圆形半径9 mm、圆心(71,40) mm、原材料/网格/边界/端口/alpha/gamma及所有原数值门。唯一来源accepted1/global7/loading1.35 mm，state SHA `0c8c5b07ad3ef5872502dede2f76cee6a152b9f78d3b0b7f831ebc6286a12455`。

执行前源核查纠正了上一计划的术语：J是九点Simpson（xi慢eta快），非Gauss；Hu没有采样点轴，是Q1单元常值参考位移Hessian。Hu中心只是单元代表标记，最大绝对分量与Frobenius范数分开。原保存值、物理任务、3NPZ/8字段及资源范围保持。

自由第三介质 `8581` 单元／`77229` 原Simpson样本；最小J `0.08623624515762662`，最大Hu绝对分量 `0.41607250505717375` /mm。

最低十个J element/point条目及截断并列、最高十个Hu单元及截断/分量并列均保留；实际行数见JSON/CSV。原四项标量精确对账：`{'free_medium_minJ': True, 'free_medium_max_abs_Hu': True, 'global_minJ': True, 'global_max_abs_Hu': True}`。

|极值|单元（从0计）|原Simpson点/分量|实际位置 mm|
|---|---:|---|---|
|最小J|10394|q=2, (xi,eta)=(-1.0,1.0)|[73.0, 31.0]|
|最大absHu|10368|[{'component_index': [1, 0, 1], 'signed_value_per_mm': -0.41607250505717375}, {'component_index': [1, 1, 0], 'signed_value_per_mm': -0.41607250505717375}]|单元代表中心[59.88354518548698, 30.783401623846615]|

最近边界信息直接复用原普通JSON，未新增搜索：`{'mechanism_edge_index': 812, 'workpiece_edge_index': 8, 'mechanism_nodes': [10286, 10287], 'workpiece_nodes': [10623, 10624], 'mechanism_point_mm': [73.00611919346724, 30.90386218509938], 'workpiece_point_mm': [73.0, 31.0]}`。

完整定位、参考/实际坐标和逐行连接关系见[原值摘要](run_001/summary.json)、[J位置表](run_001/j_locations.csv)、[Hu单元/分量表](run_001/hu_locations.csv)。跨单元重合点保留各自单元/采样身份；同单元/共享节点只描述几何关系，不证明因果或接触。

![整体实际位置](run_001/overview.png)

![工件下方梁段局部](run_001/local.png)

helper `5.407765300013125` s／180 s，outer `7.621844499983126` s／240 s，SUP2采样峰值 `147718144` B／8589934592 B，清理 `True`。

实际归档/字段解码 `3`／`8`；调用计数 `{'model_constructions': 0, 'force_calls': 0, 'tangent_calls': 0, 'HP_calls': 0, 'solver_calls': 0, 'tests': 0, 'default_installations': 0, 'boundary_searches': 0, 'plots_started': 2, 'plots_completed': 2}`。无HF力核/API/solver导入；计数不是通用机械hook。

helper真实错误 `None`；封存 `6` 份／`829205` B，状态 `complete_inside_original_helper_window`。像素检查 `pass_pixel_inspection_with_marker_overlap_annotation`。

原J/Hu数组、平衡态、原验收门、父任务历史和资格不改。CREF1仍仅祖先1.15 mm参考；本步骤不取得1.35态独立HP、圆周压力、有效夹持、卸载/释放、稳定性、完整路径、制造或HF5资格。

下一步：建议L-CSTEP5复用已安装load_only入口，从原S4成功1.35 mm末态仅延伸至1.40 mm，先fresh复核原锚点，保完整任务前缀、原物理/设置/门；详见NEXT_STEPS.md。该段尚未执行；本次定位不升级压力、有效夹持或独立HP资格。

[人工页](run_001/REVIEW.md) · [实际审阅](author/ACTUAL_REVIEW.md) · [helper](run_001/execution_receipt.json) · [outer](local_launch.json) · [闭卡JSON](author/closure.json)
