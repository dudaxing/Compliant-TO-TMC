# L-CREF1：圆形工件1.15 mm峰值保存态独立参考

2026-10-17 Asia/Seoul，用户直接授权按已发布L-CSTEP2/NEXT_STEPS计划执行。main基线11a8b49ebef7d18fef17ffe6c9e365ce574de074，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git。此为准备/静审快照，尚未执行HP。

整体目标为普通LF几何进入独立HF的TMC前向力学，输出可比较的实际响应与接触相关量。HF不优化、不导入/安装/调用dmftd，MPM暂不实现。本阶段首次核圆形较强介质压缩新峰值的数值一致性，供下一加载决策；不重做已有平衡路径。

唯一来源为lf_circle_step_002/run_001/wave_circle_step/result.json中accepted1/global5/child1/loading1.15 mm，stateSHA3db267551ea6cb5817c2a1946a80363ecccb0329078d516e90e0106f27e709ef；不能误用其continuation里的1.00 mm祖锚。原子段[1,1.15]、完整任务前缀到1.15及原资格保持，未重新从零执行。

原r9/c(71,40) mm固定圆形、E1MPa/nu.3/plane strain/厚20mm、h.5mm、13440单元/13689节点/27378DOF、fixed1272/free26106、gamma1e-6/alpha5e-7/Lr80mm、支撑/对称/平均端口、全部数值门保持。只读取保存模型与split及缓存，不新增生产F/T、构模、Newton、测试、安装或API关联。

独立数学原B850 Audit.run_state(5,row)与aa86 workpiece_checks字节不改；HP80/120各一次，覆盖全局/逐元材料/Hu/总力、同一PORT方向v=b_in/maxabs(b_in)且fixed0/deltaR0、精确Decimal3000 scatter/trap、CSC全系数组装身份、KKT和工件/支撑投影。不等于核全部切线列。新loader按圆形保存overlay与L-CPREP1普通模型证据核对，不继承旧square load()，不新增独立圆mask/边界资格。

原十五门及其分母/floor/局部规则/投影顺序原样保持：production residual1e-9、independent residual1e-8、force evaluation1e-9、constraint1e-10、balance1e-6、fixed8e-11mm、HP80/120一致1e-40；total/material/Hu force=1e-11/1e-9/1e-9，三切线方向=1e-10/1e-9/1e-9，KKT force/mean各1e-10。检查数量按实际原检查报告，不把十五类门当总检查数。stress/energy/独立Hu数组资格不增加。

六份原NPZ仅从producer seal+stat准备绑定：model、所选state/forces/tangents/CSC、source_geometry。前五份唯一解码；source_geometry只原字节身份。原workpiece方法重开state/forces，两次重复loader，不能混同unique数。51 descriptor字段+18重复出现，CSC另format/shape必需容器及原可选_is_array探针。十一数学依赖保持SHA且unique basename平铺归档；driver和纯plot另归档。原依赖会导入JAX/注册包装，不等于执行AD/JIT或生产力学。

全部通过后同一helper一次调用原pure误差plot，读本次accepted_005/summary.json，输出一张10项error/原limit的PNG及JSON，log10只作显示、原零误差保持零，无新floor/门。之后允许一次新PNG像素检查/展示，不重绘、不重读旧媒体；结构对照链接原S2实际图。

一次helper900秒/outer960秒（最多16分钟）、采样8GiB，含批准/来源核对、import、读数组、归档、2HP、全部比较、plot、完整输出seal及回执。launcher最早clock覆盖其preflight和最终输入身份SHA，helper独立900秒；合作stop/采样RSS不是OS硬上限，原HP内部无checkpoint时须等实际退出，迟到PASS不得通过。首错停止，无修复重跑、重试、延期、force或其它新科学；失败保真实partial与实际HP/plot计数，原窗口内可部分封存。

只授这一个保存圆形模型的数值参考/PORT方向，不授全部两态或完整路径参考、全列切线、连续压力、有效夹持、卸载/自由释放、稳定性、制造或HF5。legacy normal字段仅解释为全局Fy投影，不能当圆周局部法向压力或整圆总法向夹持力。原S2 response/results/flags不改。

包括实际结果、误差PNG、来源/资源回执、next决策记录和普通main提交推送及异目录恢复核对。若通过，再按实际误差/压缩/几何/成本提出下一加载目标；若失败，先解释实际错误，不静默重跑。具体protocol/授权/source静审同目录归档。
