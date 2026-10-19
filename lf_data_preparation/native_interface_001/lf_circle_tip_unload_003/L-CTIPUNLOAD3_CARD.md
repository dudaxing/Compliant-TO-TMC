# L-CTIPUNLOAD3：尖端圆形工件剩余五目标卸载至零

用户明确批准“批准按 L-CTIPUNLOAD3 计划实施并执行”，依据main 2fe7a5f942454ca75acc4ddd54b5926732afcb46的UNLOAD2/NEXT_STEPS。整体目标为普通LF几何接入独立、可恢复的TMC大变形前向分析，观察工件附近的真实结构、作用力和回程。上一步1.05→1.00 mm原门及五图通过、4次线搜索全部接受且无二分，本卡据此在一个有界窗口完成剩余5个输入目标，不开展优化或正式标签。

唯一科学起点UNLOAD2真实result.json accepted1/global14/child1/unloading1.00 mm，SHA 0be638c03daaa369d3a740493f6e99bd6978e839709cf83029642fdf8abd2c0b，signedR=0.17845354455643678 N。不得误用旧加载1.00、峰值1.06、参考summary或显示JSON。旧科学输入仅为父source_geometry四mask及所选state的lift/fluctuation，不移植旧力、切线、矩阵或HP科学gzip。

复用已安装evaluate_native(saved_result=...,selected_state_index=1,extend_path=True)；fresh F/T复核锚态原平衡/SHA/signedR后执行child[1.00,.90,.75,.50,.25,0]，global14..19、child-original0..5。完整15目标前缀和所有其他task字段精确继承，包括四项说明字段；仅追加[.90,.75,.50,.25,0]形成20目标任务。path.kind仍ordered_cycle、input.target_mm仍任务峰值1.06。本层无新task_transition，旧first_unload五键仅在真实嵌套parent_continuation内。child最大输入为1.00，loading_peak_reached为false；不添加load_only新峰值旗标，不重放完整前缀。

保持固定r9/c(80,40) mm、right92/Lr80、h.5mm、14720单元/14985节点/29970DOF、厚20mm、E1MPa/nu.3/plane strain、gamma1e-6/alpha5e-7及原支撑/对称/平均端口。mechanical/chunk256/port_projection及全部非clock设置原样，仅将新controller clock改为5400秒。原残差1e-9、均值系数1e-10原scale、全局平衡1e-6、固定split8e-11mm、J>0保持；不新增零残力、相等、恢复或单调门。minimum_increment=.00625mm及max_bisections4保持，线搜索/二分完全沿原实现；名义半步0.10/16=.00625、0.15/16=.009375、0.25/16=.015625，实际浮点比较及原停止规则不改。保留全部实际接受/二分态，不只保原请求目标。

一次controller5400秒，viewer/收敛/表页共享600秒，helper6600/outer6660秒（最多111分钟），采样64GiB、四库线程上限16、原viewer内部8GiB保持。完成研究包装及有限独立静审后唯一启动；首终端错停止后续科学/显示，保真实partial，仅原窗口内封存。无外部重试、修复重跑、延期、force、新HP、测试、API关联、默认HF修改/安装、回滚或删除。

成功后5PNG/实际N帧GIF、状态表和人工页。viewer与收敛源码逐字节继承UNLOAD2：comparison为锚与实际LAST，字段/右介质静态图为LAST，peak_index保段内最大值语义；读数、公式、几何距离与力定义不改。图含实际×1变形、R/q_out、signed material/Hu/total bodyFx/Fy、tip/full-Q1距离及几何标志、实体/介质J/Hu、全480cells右条带和原Newton/trial/二分。五张新PNG各最多一次实际检查，不解码旧媒体/GIF、不闭窗修图，不增加第六图。零值、小值及非单调量按实际保留。

零态仅作描述性对照：普通pilot summary `lf_circle_tip_pilot_001/run_001/view/wave_circle_tip_pilot/summary.json` row0/global0/d0/rawleg=origin，逻辑SHA 950ee55405b86a22e9343997432d398600e1904b7f3046a72f8de53a72229fc9。旧摘要无path_metadata，不能沿用加载续算摘要的continuation读取假设或重标为loading。与新global19/unloading0比较原13标量及差值：R/q_out、body total/material/Hu Fx/Fy、tip/full-Q1距离、solid minJ、medium minJ及maxabsHu。旧原点的力、q、Hu为0，两种距离1mm、两类minJ为1；新结果按实际报告，不预设恢复到精确零、不比较state必须相等。仅嵌入状态表/人工页，不增加旧数组、媒体或科学调用。

记录总体目标、原因、完成内容、实际效果和限制，分开执行/视觉QA/阶段完成。普通main推送及同机异目录local Git对象恢复核对，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git。保原成功、失败、LOCAL1视觉失败及既有参考范围。本卡HP0；到零仅代表本次输入回程终点完成，不代表自由工件释放、精确恢复、整条路径/独立参考、压力/有效夹持、稳定性、网格/域宽或HF5资格。依据真实零态再安排下一步，不自动开展后续科学工作。
