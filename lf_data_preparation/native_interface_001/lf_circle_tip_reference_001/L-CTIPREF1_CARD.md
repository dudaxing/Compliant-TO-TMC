# L-CTIPREF1：当前尖端对向圆形工件1.06 mm保存态独立参考

用户明确批准“批准按 L-CTIPREF1 计划实施并执行”，依据main 8cf86e81e414866a7d5cb110e006c7088f94eb97的LOCAL3/NEXT_STEPS。本项目目标是独立可恢复的TMC大变形前向分析，观察LF夹持器接近工件、变形及力；本卡核强压缩下的数值一致性，不重新求平衡。

唯一来源STEP10 scientific result的accepted1/global12/child1/loading1.06 mm，逻辑state SHA dd9288140ae51ff3cfcc7f7f6d6811b2242a55054454002bd7c06ff88a4b6bc6、signedR=0.19568183324206792 N。不能误用LOCAL3显示JSON或1.05 mm祖锚。原两态[1.05,1.06]、全load_only前缀与嵌套历史保持；生产F15started/14completed与T8如实保留，一次invalid_J内部试探拒绝不是终端失败。

保持固定圆形r9/c(80,40) mm、right92 mm、Lr80 mm、h.5 mm、14720单元/14985节点/29970DOF（fixed1288/free28682）、E1MPa/nu.3/plane strain/厚20 mm、gamma1e-6/alpha5e-7及全部原边界、平均端口、设置和门。当前L-CTIPPREP1普通模型/工件overlay证据精确对照，旧c71/global5/旧网格身份不继承，不新增独立几何掩码资格。

复用原B850 Audit.run_state与aa86 workpiece_checks的数学字节；HP80和HP120各一次，覆盖全部单元与DOF。原材料/Hu/总力、同一PORT方向v=b_in/maxabs(b_in)且fixed0/deltaR0、Decimal3000精确scatter/trap、CSC全系数组装身份、KKT及工件ON-body/holding投影保持。这不核全部切线列。原11依赖unique basename平铺归档，driver和原pure plot另归档；不写新力核或默认HF。

原十五门及分母/floor/局部规则/投影顺序不变：production residual1e-9、independent residual1e-8、force evaluation1e-9、constraint1e-10、balance1e-6、fixed8e-11mm、HP80/120一致1e-40；total/material/Hu force=1e-11/1e-9/1e-9，三方向切线=1e-10/1e-9/1e-9，KKT force/mean各1e-10。十五类门不等于实际检查总数，不增加小J、应力/能量/独立Hu数组门。

6份既存NPZ绑定model、所选state/forces/tangents/CSC、source_geometry；前5份解码，source_geometry只原字节身份。51 descriptor字段与原workpiece重开state/forces的18次重复字段出现保持，CSC另format/shape及原可选_is_array探针；不把7次loader混同5次。准备/闭卡只用原seal和stat，科学NPZ身份hash/归档和数组读取全部限唯一helper窗口；launcher只核普通bindings。原依赖导入JAX/注册包装不代表执行AD/JIT。

全部参考和工件门通过后，同一helper调用一次原pure误差plot，仅读新accepted_012/summary.json，生成一张10项原error/limit PNG与普通JSON；Decimal40 log10只作显示，零误差保零、无新floor。新PNG最多一次实际检查，无重绘；LOCAL3两图、原反力和收敛图只链接，不打开旧媒体或新画结构/GIF。

一次helper900秒/outer960秒、采样8GiB、四库线程上限16，包含来源/导入/读取/归档/2HP/比较/plot/输出seal。继承原合作stop/采样RSS合同，无SUP2或OS硬限主张；HP内部无checkpoint时等待实际返回，迟到PASS不能通过。先有限包装与独立静审，再唯一启动，首终端错停止保实际partial，仅原窗口内封存。无修复重跑、外部重试、延期、force、新生产F/T、构模、Newton/平衡、测试、API关联、reader修改、默认安装、回滚或删除。

记录目标、原因、完成内容、误差、效果与限制，分开执行与视觉QA；main普通推送和同机异目录local Git恢复核对，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git。保全部原结果、资格与LOCAL1失败历史，不改生产response。仅授本态/声明方向的独立参考，不授完整两态/路径、全切线列、压力、有效夹持、卸载/自由释放、稳定性、制造、网格/域宽收敛或HF5。圆形legacy normal只解释全局Fy，不能作为圆周局部法向压力。暂不加载1.07 mm；依据实际参考结果另作下一步决策。
