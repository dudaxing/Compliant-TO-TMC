# L-CTIPUNLOAD2：尖端圆形工件1.05→1.00 mm继续卸载

用户明确批准“批准按 L-CTIPUNLOAD2 计划实施并执行”，依据main 52ba58df1958523c457b9db970683ed28ac483b2的UNLOAD1/NEXT_STEPS。整体目标为LF普通几何接入独立、可恢复的TMC大变形前向分析，观察接近工件、实际变形、作用力及卸载。本卡根据首次回程原门通过、线搜索全部接受和距离/J恢复的实际结果，只推进一个卸载目标。

唯一科学起点UNLOAD1真实result.json accepted1/global13/child1/unloading1.05 mm，SHA 64b9301899b2599203140b634ffc5340e5d0a7c31ce75d0931203a6b72d58d1d，signedR=0.1917119776052677 N。不得误用旧加载1.05、峰值1.06、参考summary或显示JSON。保存态输入仅为父source_geometry四mask及选中state的lift/fluctuation，不移植旧力、切线、矩阵或HP科学gzip。

复用已安装evaluate_native(saved_result=...,selected_state_index=1,extend_path=True,time_limit_seconds=1800)；fresh F/T复核锚态原平衡/SHA/signedR后执行child[1.05,1.00]、global13/14、resume_origin/unloading。完整14目标前缀保持，仅append1.00，path.kind仍ordered_cycle、input.target_mm仍1.06。**父task其余字段全部原样继承，包括task_id/purpose/parameter_origin/description四说明字段**；新阶段身份放本卡、protocol和输出目录。此项纠正已在授权前说明的计划误写，符合现有same-kind API，不改默认源码或验收门。

本层不新增task_transition，原first_unload五键保留在完整嵌套parent_continuation。新child不经过1.06，loading_peak_reached应为false；response段内最大行程为1.05，任务/祖先峰值仍1.06。ordered_cycle不要求load_only的new_peak_reached/extended_segment_completed字段。末目标完成只代表本段回程，不代表完整前缀重放、卸载至零或自由释放。

保持固定r9/c(80,40) mm、right92/Lr80、h.5mm、14720单元/14985节点/29970DOF、厚20mm、E1MPa/nu.3/plane strain、gamma1e-6/alpha5e-7及原支撑/对称/平均端口。mechanical/chunk256/port_projection和全部非clock设置原样；原残差1e-9、均值系数1e-10原scale、全局平衡1e-6、固定split8e-11mm、J>0保持，不新增单调、恢复或小J门。minimum_increment=.00625mm；-.05可按原规则二分至-.025/-.0125/-.00625，下一半步低于原下限则停止，max_bisections4保持。允许原内部线搜索/二分，实际接受态全部保留。

一次controller1800秒，viewer/收敛/表页共享600秒，helper2700/outer2760秒（最多46分钟），采样64GiB、四库线程上限16、原viewer内部8GiB保持。完成研究包装及有限独立静审后唯一启动，首终端错误停止后续科学/显示，保真实partial，仅原窗口内封存。无外部重试、修复重跑、延期、force、新HP、测试、API关联、默认HF修改/安装、回滚或删除。

成功后5PNG/实际N帧GIF、状态表及人工页。viewer与收敛源码逐字节继承已通过实际检查的UNLOAD1：comparison为锚与实际LAST，字段/右介质静态图显示LAST，peak_index仍保段内最大值的原语义；数值读取、公式、几何距离与力定义不改。图含实际×1变形、R/q_out、signed material/Hu/total bodyFx/Fy、tip/full-Q1距离及几何标志、实体/介质J/Hu、全480cells右条带和原Newton/trial/二分。每张新PNG最多一次实际检查，不解码旧媒体/GIF或闭窗修图，不增加第六图。

另仅读既存STEP6普通summary row0/global7/d1.00/rawleg resume_origin（加载来源），与新global14/unloading1.00记录同13项原值及描述差值：R/q_out、body total/material/Hu Fx/Fy、tip/full-Q1距离、solid minJ、medium minJ及maxabsHu。保原leg/SHA与加载来源；不要求state或数值相等，不新增数组读取、科学调用、百分比/恢复/滞回门，嵌入原状态表和人工页。

记录总体目标、原因、实际完成、效果和限制，分别保执行/视觉QA/阶段完成。普通main推送和同机异目录local Git对象恢复核对，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git。保原成功、失败和LOCAL1视觉失败历史；本卡HP0，既有峰值参考不转授新卸载态；不升级整条路径、压力/有效夹持、自由释放、稳定性、网格/域宽或HF5。依据实际结果安排下一步，不自动继续其它目标。
