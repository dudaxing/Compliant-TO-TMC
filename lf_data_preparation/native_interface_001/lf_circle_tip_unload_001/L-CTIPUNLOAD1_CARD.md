# L-CTIPUNLOAD1：当前尖端圆形工件首次1.06→1.05 mm回程

用户明确批准“批准按 L-CTIPUNLOAD1 计划实施并执行”，依据main 6cac08b4a9ea30bf295d9e4da3fddb8d55e94ba5的L-CTIPREF1/NEXT_STEPS。项目目标为独立可恢复的TMC大变形前向分析，审查LF夹持器接近工件、结构变形、作用力与回程。本卡在已通过选定态HP参考的峰值后实现一次实际小回程，不扩大加载。

唯一科学起点STEP10真实result.json accepted1/global12/child1/loading1.06 mm，SHA dd9288140ae51ff3cfcc7f7f6d6811b2242a55054454002bd7c06ff88a4b6bc6，signedR=0.19568183324206792 N。不得误用参考summary、LOCAL显示JSON或1.05 mm祖锚。只读原source_geometry四mask及选定state的lift/fluctuation作保存态输入，不移植旧力、切线、矩阵或HP科学gzip。

复用已安装evaluate_native(saved_result=...,selected_state_index=1,extend_path=True)；fresh F/T复核峰值平衡/SHA/signedR后执行child[1.06,1.05]、global12/13、resume_origin/unloading。完整13目标加载前缀保持，仅path.kind由load_only改ordered_cycle并append1.05；input.target_mm仍1.06，另改四项说明身份。保原五键task_transition与完整嵌套历史。ordered_cycle不要求load_only的new_peak_reached/extended_segment_completed字段；本段下降完成不代表原全路径重放或卸载至零。

保持固定r9/c(80,40) mm、right92/Lr80、h.5mm、14720单元/14985节点/29970DOF、厚20mm、E1MPa/nu.3/plane strain、gamma1e-6/alpha5e-7、原支撑/对称/平均端口。mechanical/chunk256/port_projection及全部非clock设置保持；原残差1e-9、均值系数1e-10原scale、全局平衡1e-6、固定split8e-11mm、J>0门保持，不增加恢复或单调门。minimum_increment=.00625mm；直接-.01首次尝试允许，失败后半步-.005低于原限值，按原规则停止，不降低限值。原内部线搜索/目标二分允许。

一次controller1800秒，viewer/收敛/表页共享600秒，helper2700/outer2760秒（最多46分钟），采样64GiB、四库线程上限16，原viewer内部8GiB保持。包装与有限独立静审后唯一启动；首终端错停止后续科学/显示，保真实partial，仅原新窗口内封存。无外部重试、修复重跑、延期、force、新HP、测试、API关联、默认HF修改/安装、回滚或删除。

成功后5PNG/实际N帧GIF、状态表与人工页。研究viewer只改显示选态及相应标题/范围元数据：comparison为锚与实际LAST，保存场与右介质静态图为LAST，真实peak_index仍原语义；数值读取/定义/公式/几何距离与力不改，收敛源码逐字节继承。图含实际×1变形、原signed material/Hu/total Fx/Fy、R/q_out、tip/full Q1距离及几何标志、J/Hu、全480cell右条带与原Newton/trial/二分。N以实际接受态为准；每张新PNG最多一次实际检查，不解码旧媒体/GIF或闭窗修图重跑，不增加第六图。

另仅读旧STEP10普通summary row0/global11/d1.05/raw leg resume_origin（继承此前loading态），与新global13/unloading1.05按同一定义记录13项原值及描述差值：R/q_out、body total/material/Hu Fx/Fy、tip/fullQ1距离、solid minJ、medium minJ和maxabsHu。保原leg/SHA与加载来源，不比较state或数值必须相等，不新增数组读取、科学调用、百分比/恢复/滞回门；嵌入原state_table和人工页。

记录整体目标、原因、实际完成、效果与限制，分开执行/视觉QA/阶段完成。main普通推送和同机异目录local Git对象恢复核对，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git。保所有原成功/失败与LOCAL1视觉失败历史；峰值的选定态参考不转授新卸载态，不升级完整路径、压力/有效夹持、自由释放、稳定性、网格/域宽或HF5。固定工件上的输入回撤不等于自由工件释放；依据本次实际回程另定下一步，不自动继续。
