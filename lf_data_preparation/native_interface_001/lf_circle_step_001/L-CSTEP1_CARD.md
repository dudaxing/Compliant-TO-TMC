# L-CSTEP1：圆形工件保存态0.75→1.00 mm

2026-10-17，用户直接授权。本卡复用已安装load_only延伸，不修改默认HF、不重做兼容测试、不新增HP。main基线ec0d958f81db06777457aeaadd0a29b971da8457；origin保持https://github.com/dudaxing/Compliant-TO-TMC.git。当前准备／静审，未执行。

## 目标与固定任务

整体目标是独立HF分析普通LF夹持器的真实变形、TMC作用及工件力，并通过实际保存态逐段研究接近与夹持。此前0.75 mm已成功，实体minJ0.98193、自由介质minJ0.50110、最小实际边界距离0.50437 mm；本次在相同物理定义下明确追加1.00 mm峰值。

父源是L-CEXT1成功child/result.json的accepted1/global original3，不能误用其continuation中记录的祖父0.50 mm锚点索引。新完整task为[0,.25,.5,.75,1.00] mm、input.target_mm=1.00；实际子段仅[.75,1.00]。四说明字段变化明确列入协议，其余物理精确保持：固定圆形r9/c(71,40)、E=1MPa/nu=.3/plane strain、厚20mm、h=.5mm、13440单元/27378DOF、gamma1e-6/alpha5e-7/长度80mm、原支撑/平均端口/对称。

## 唯一执行

一次默认evaluate_native(...,saved_result=父result,selected_state_index=1,extend_path=True)，非clock设置及mechanical/chunk256/port_projection保持。第一态须fresh F/T检查即通过，状态SHA及R字节身份保持，不接受旧力/切线/矩阵作为锚点检查。新target global3/4、child0/1；原内部回溯/有界二分可增加实际接受态，全部保存并显示。

原relative residual1e-9、逐态原constraint_bound（系数1e-10）、global force balance1e-6、fixed split fsum8e-11mm、全部积分点J>0保持。wrapper只保留原缓存观察和身份核对，生产内核、门与尺度不变。

新增峰值及子段完成由new_peak_reached/extended_segment_completed明确报告；全路径/task_target_executed仍False，旧target_response仍None，新requested_endpoint_response为1.00 mm。继承前缀不作为本次新执行或新参考，原父/祖先结果及资格保持。

成功后单次fresh纯circle viewer及普通result JSON收敛投影，生成4PNG、实际N帧GIF、逐态表和人工页。结构坐标x1，全结构镜像仅显示，下半数值不加倍。原纯几何/节点力观察复用；仅把约束图图例移到数据区外，投影/数值/symlog及其余绘图调用不变。

旧科学读集只有父source geometry NPZ与accepted001 split NPZ；准备阶段原producer seal+stat，不打开载荷。新viewer纯闭包5源，1+2N唯一NPZ、27+18N字段；不解码切线，最终全输出seal仍包含全部新产物。

## 资源、停止与交付

controller1800／显示共享600／helper2700／outer2760秒（最多46分钟），采样8GiB。显示600包括binding、viewer、收敛、表和页；最终seal仍限helper2700。原SUP2 CPU-CLEAN1同实例/覆盖/句柄释放合同，固定5秒清理在outer内，无force兜底。

唯一启动，首个终端错误停止后续科学/显示，保真实partial，仅原窗口开放时允许部分seal。无外部重试、修复重跑、延期、force、回滚或删除。成功后四张新PNG各最多一次像素检查；GIF只由原viewer核实际帧数，不额外解码。

保存授权、输入/源码绑定、静审、原响应/状态/矩阵、图表、资源清理收据、实际结果与下一步。完成普通main提交推送、异目录恢复核对。无符号边界距离、几何观察和材料/Hu弱式合力不自动授予连续压力、有效夹持、完整循环、卸载/自由释放、独参、稳定性、制造或HF5资格。
