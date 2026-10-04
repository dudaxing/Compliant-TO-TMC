2026-10-04最新：**新增全工件节点力API/CLI，5解析项一次通过；009保存九态全部153节点、1377行CSV核对通过。** 见[目标、实现、效果、显示问题修正与后续](../functional_views/native_workpiece_nodal_20261004/square009_001/RESULTS.md)和[峰态材料/Hu/总节点力图](../functional_views/native_workpiece_nodal_20261004/square009_view002/render_001/nodes_state_004.png)。峰态右底角节点力模0.0127476461 N，Hu局部反向抵消显著；合力仍与009一致。派生力矩未新增HP资格，节点力不是压力。

原001绘图零矢量假箭头已人工检出并保留；独立002仅改短箭头缩放，一次重绘相同数据通过。本轮无新力学/HP或更大行程求解。下一步依据底射线0.0767107 mm、介质minJ0.0280804，冻结小幅近接触峰值和完整卸载任务；圆体/尺寸位置/细网格继续作为独立工况。以下逐字节保留此前原文，当前以本条和新报告为准。

2026-10-04最新：**009保留原完整九目标，1.75mm加载与回零已完成；63F/36T，18次新HP/174111检查通过。** 显式256单元分块切线不改变数学或默认full；三份对照保存态（007初态、008峰态、007回零）逐字节等价，原前八态32整档相同，生产373.57秒在原600/660预算内。见[目标、变更、效果/成本、范围与下一步](../lf_data_preparation/native_workpiece_001/coarse_square_cycle_009/RESULTS.md)及[实际九态×1动画](../functional_views/native_workpiece_cycle009_20261004/saved_render_001/animation_001/cycle009_actual_path.gif)。

底面射线.0767107mm、左面2.83278mm，介质minJ=.0280804；几何无已测跨域内部重叠，尚未证明有效夹持、压力、能量或应力HP。旧008仍是time_limit失败。下一步补工件节点力位置图，再根据间隙/J规划近接触增量；圆/细网格未执行。以下逐字节保留此前时点原文，当前以本条与新报告为准。

2026-10-04最新：**008的1.75mm峰值已达到，但九目标完整循环因600秒时间限制失败，8接受态保存至卸载.5mm；新HP0，原卡已关闭。** 底/左首次法向射线约.0767107/2.83278mm；第三介质minJ=.0280804，实体minJ=.956236；无已测跨域内部重叠，不能认定有效夹持。见[目标、实现、原因、实际效果/成本/限制与下一步](../lf_data_preparation/native_workpiece_001/coarse_square_cycle_008/RESULTS.md)和[实际峰/最后态与距离图](../functional_views/native_workpiece_cycle008_20261004/partial_region_view_001/render_001/native_region_path.png)。

四张独立保存partial观测/绘图卡各一次通过，不是机械重试或HP资格；未补返回零点。main/origin保持，009仅计划未执行。以下完整保留此前时点原文，当前以本条及新报告为准。

# 物理与功能开发进度

2026-10-04当前：**新增完整原生Q1跨域内部重叠和固定方体有限底/左面射线诊断，39解析项通过，007保存七态测量完成。** 峰1.5mm底射线=.359398367462mm、左射线=2.698810358664mm，均是有限面端点命中；初/返两面2mm。七态有效、无内部域重叠/模糊；完整包含、自身重叠和有效夹持未证明。旧left unsigned=1.661960666472mm至下方角点，不能当水平间隙。见[整体目标、实现、排查、效果、成本和后续](../functional_views/native_region_geometry_20261004/RESULTS.md)、[×1结构/射线/七态三类距离图](../functional_views/native_region_geometry_20261004/square007_view_003/render_001/native_region_path.png)。

001布尔返回类型首错与保存图001旧metadata角色首错均关闭并保留；各独立最小候选通过，zoom文字遮挡另图003修复、数据原字节相同。原旧边界/机械实现、27模型数组和007接受态fresh参考范围保持，新F/T/HP/solver0，pure来源basis非hooks监测；无新力学/能量/压力资格。峰底部靠近、有限左面远离，不能称有效夹持。

下一据此准备独立1.75mm有序循环并保留中间/返程真实态，仍未执行；不线性推断接触或保证收敛，先核J/quad/域/面及原fresh门。细/圆/更大行程、自由体、压力/夹持、H2/H3/HF5/ADJIT和整体HF未完成。main唯一主干，origin固定https://github.com/dudaxing/Compliant-TO-TMC.git；公开恢复仅文件身份。

以下保留以前时点原字节；当前以本条及持续记录末节为准。


2026-10-04当前：**同一粗方固定半工件的新0→.5→1→1.5→1→.5→0 mm完整机械循环成功；7实际接受态的14次新HP80/120与135364项原参考检查通过。** 45/45F、26/26T、1solve；峰输入R=.333178493234 N、自由+y输出=1.747632769069 mm、minJ=.168678218781。实际all/bottom unsigned边界距最低.358231982207 mm，卸载返回2 mm；返回最大节点位移模3.42228e-28 mm。见[整体目标、行动、原因、真实效果与限制](../lf_data_preparation/native_workpiece_001/coarse_square_cycle_007/RESULTS.md)、[实际结构/力/变形/最近点图](../functional_views/native_workpiece_cycle007_20261004/saved_001/render_001/cycle007_saved_path.png)。

本轮只扩物理任务，004/006的力学实现与原算法/门字节保持，6项接口测试未重跑；新的资格仅七个接受机械态的力、声明PORT方向、组装、平衡及工件合力，不包含辅助能量、应力HP、全列HP、一般接触或有效夹持。图仅读生产/已保存几何，原flags不回填；14fresh参考资格另见报告。旧003卸载失败/未知T25与closed005保持冻结。

下一先补封闭实体包容/相交和明确法向间隙诊断，再据实际结果选择1.75 mm或其它工况。正unsigned距离、left角点距离及第三介质小力不能直接作为夹持判据；1.75/2/3 mm、圆/细网格平衡尚未执行。压力/有效夹持、自由工件、H2/H3/HF5、AD/JIT及整体HF仍待完成。main为唯一开发主干，origin=https://github.com/dudaxing/Compliant-TO-TMC.git；公开恢复只核文件身份。

以下保留以前时点的原字节；当前以本条及持续记录末节为准。


2026-10-04当前：**同一粗方固定半工件的新0→.5→1→.5→0 mm完整机械循环成功，5实际接受态的10次新HP80/120与96,781项原门检查通过。** 31/31F、18/18T、1solve；峰输入R=.216813996933 N、自由+y输出=1.159355055764 mm、minJ=.458189164213。真实unsigned外边界距2→1.47194→.924425→1.47194→2 mm；各保存态无相交，尚未证明接触或有效夹持。见[目标、原因、问题排查、物理效果与限制](../lf_data_preparation/native_workpiece_001/coarse_square_cycle_006/RESULTS.md)、[实际结构/力/变形/最近点图](../functional_views/native_workpiece_cycle006_20261004/saved_001/render_001/cycle006_saved_path.png)。

本轮只扩物理任务，004实现与6项接口既有实测保持，未重复测试；schema1.2机械模式能量明确not_evaluated，原算法/门未变。005因冻结stage身份谓词错误在生产前闭卡、0新数值；006作者路径遗漏在正式安装前修正，原字节留存。新资格仅接受态机械力/声明PORT方向/组装/平衡与工件合力，不含能量、应力HP、全列HP或一般接触。图仅读生产，原独立flags不回填，fresh参考资格另见报告。

下一步新1.5 mm粗方加载—卸载，据实际minJ/距离/成本再考虑2/3 mm；1.5/2/3 mm、圆形/细网格平衡尚未执行。signed gap/包容/法向、压力/有效夹持、自由工件、H2/H3/HF5、AD/JIT及完整项目仍待完成。仅main开发，origin=https://github.com/dudaxing/Compliant-TO-TMC.git；公开恢复只核文件身份。

以下保留以前时点原字节；当前接续以上述新结果与持续记录末节为准。


2026-10-04当前：**可选机械模式已接入NumPy平均位移求解器；新的固定对称半方形工件0→0.5→0 mm完整加载—卸载成功，三个接受态的6次新HP80/120及58,197项原门检查通过。** 接口6项实际测试通过；本次生产17/17力、10/10切线、1求解，213.73秒。峰值R=.106253247986 N、自由输出+y=.575755712293 mm、minJ=.735764774113；卸载返回近初始。真实外边界距2→1.471935964045→2 mm，均无交叉；仍未证明有效夹持。见[目标、实现、原因、效果及全部限制](../lf_data_preparation/native_workpiece_001/coarse_square_cycle_004/RESULTS.md)、[真实结构/力/变形图](../functional_views/native_workpiece_cycle004_20261004/saved_001/render_001/cycle004_saved_path.png)、[实际边界距离](../functional_views/native_workpiece_cycle004_20261004/boundary_saved_001/RESULTS.md)。

默认complete响应保持原17字段；新response_mode=mechanical/schema1.2保存16力字段/3切线/full CSC，并明确材料能量not_evaluated/qualified:false/field_present:false。原控制器/CI/T/B52/收敛门未放宽。旧003卸载失败及未捕获T25问题保留；新三态资格限声明task/source的力、PORT方向作用、组装和平衡，不包含能量/应力HP/全列切线/一般接触。图只读生产所以标题仍PRODUCTION ONLY UNQUALIFIED；fresh参考资格另读本报告，不回填原生产flags。

下一步同一粗方形固定工件的新1 mm递增加载与卸载，根据实际收敛/minJ/距离/费用再推进2/3 mm；圆形r8/细方/细圆模型已构建但对应平衡未执行。压力、有效夹持判据、signed gap/包容、自由工件、H2/H3/HF5及完整AD/JIT仍待完成。整体独立HF目标未完成，后续在main，origin固定https://github.com/dudaxing/Compliant-TO-TMC.git；公有恢复只核对文件身份。

以下保留先前阶段的原始记录。当前状态以上述新结论及执行记录末节为准，旧“下一步/尚未实现”只代表该记录当时状态。


2026-10-04当前：**显式NumPy机械量入口与force-only组装器已按原验证字节合入main；原F16三力/缓存切线及fresh HP80/120通过原门。** 32/32测试、19200局部＋9全局门全部通过，614400个局部T系数的完整CSC组装身份核同；最大归一误差7.24336e-15，HP80/120最坏相互误差1.21169e-52。新core d5f7新增可选机械职责，默认完整NumPy/JAX公式及能量要求保留；能量明确not_evaluated/qualifiedfalse，P/S仅finite无HP资格。见[目标、实现、为何拆分、实际效果与后续](../lf_data_preparation/native_workpiece_001/mechanical_only_candidate_001/RESULTS.md)与[保存三力和方向力变化率图](../functional_views/mechanical_F16_20261004/saved_001/render_001/mechanical_F16_qualified_fields.png)。

旧Horner192 001测试收集前失败、002的25例通过但完整F16失败、独立诊断48IP/35能量NaN均保持原记录；1d18候选未合入。新单态F16不是接受平衡，不解决尚未捕获的T25输入，也不转移到旧循环资格。粗方[0,.5,0]mm循环003仍仅2接受态、0新HP、卸载time_limit失败；见[真实0.5mm峰值与旧失败](../lf_data_preparation/native_workpiece_001/coarse_square_cycle_003/RESULTS.md)。

下一唯一近期功能：显式接入native_mean机械字段/能量可用性及source版本，保持原控制器、Armijo/KKT和默认结果合同；先小闭环，再新独立卡探索同一0.5mm加载—卸载，按新证据处理残余切线问题并扩到1/2/3mm与细方/圆工件。本接入和新路径尚未执行。压力/有效夹持、signed gap/交叉/包容、自由工件、H2/H3/HF5及完整AD/JIT仍待完成。整体HF目标未完成，继续仅main、origin保持https://github.com/dudaxing/Compliant-TO-TMC.git；公开恢复只验文件身份。

以下旧条目保留各执行时点；当前状态与接续以本条及持续报告末节为准，旧“下一步/尚未实现”不覆盖最新记录。

2026-10-04当前：**matmul320候选7fff已按原字节合入；新粗方固定半工件[0,.5,0]mm三点探索正式失败并关闭，峰值达到但卸载未完成。** 2接受态[0,.5]、R_input=.106253248N、自由+y输出=.575755712mm、minJ=.735764774。600s内部预算后实际exit1，66F/50完成、27T/26完成、1solve、0新HP。16全步范围拒绝后half收敛，随后T25范围失败回滚、二分.25遇时间门；全部来源和原27数组不变。不能称新循环或两态独立参考通过。见[整体目标、选择依据、全过程与实际结果](../lf_data_preparation/native_workpiece_001/coarse_square_cycle_003/RESULTS.md)、[×1结构/力及失败时序图](../functional_views/native_workpiece_cycle003_20261004/failure_saved_001/render_001/cycle003_failure.png)。

新独立保存F16诊断一次复现原异常：首坏为已选辅助能量Horner乘积的(lo,hi)回缩项，非旧矩阵乘法、非overflow；36点物理词落到2^-400下界以下。只1F开始/0完成、0T/HP/solve，diagnostic_captured不是数学资格。下一最小候选改Horner共同尺度与乘加顺序，保留原14阶系数/CI域/P/门；尚未实现，先新F16完整F/T与fresh HP核验，再新连续路径和1mm探索。不增预算重开旧失败，不裁零或借旧F36解释后期未捕获T25。

旧31d955七态14fresh HP及真实边距1.471935964mm保持自己的来源资格；保存F36/candidate7fff/consumer B52的19200局部＋9全局原门和原失败也保留，不能转给新循环。当前新图仅保存诊断、无新测距/夹持资格；1/2/3mm未执行。signed gap/交叉/包容、压力/有效夹持、自由工件、细/圆平衡、H2/H3/HF5及完整AD/JIT仍待实现或资格化。完整持续记录见[开发进度](NUMPY_FORCE_PROGRESS_20261002.md#native-workpiece-cycle003-20261004)。仅main、origin固定https://github.com/dudaxing/Compliant-TO-TMC.git；公开恢复只验文件身份。

以下为上一阶段及更早时点的保留记录；当前状态以页首与持续报告末节为准。


2026-10-04历史状态（0.1mm阶段）：**普通文件的固定半工件、平均输入驱动和连续加载—卸载已实现；粗方形工件[0,.1,0] mm实际完成，3接受态的6次新HP80/120独立参考全部通过。** 正方形side16mm、中心(70,40)mm，计算下半；3200单元／6642DOF／376有效fixed。峰值输入R=.020941490699N、自由+y输出=.114466446177mm，半工件总(Fx,Fy)=(-3.0237102546e-5,+2.3930273461e-5)N，minJ=.947487891；卸载末输入R≈-1.19e-27N、输出≈1.76e-27mm。生产263.45秒，参考60.11秒／58010检查；30项相关测试通过。见[完整目标、实现、诊断、成本和效果](NUMPY_FORCE_PROGRESS_20261002.md#native-workpiece-cycle-20261004)、[实际结构与力](../functional_views/native_workpiece_cycle_20261004/render_001/workpiece_cycle_physical.png)、[三帧真实动画](../functional_views/native_workpiece_cycle_20261004/render_001/workpiece_cycle_actual.gif)、[数值与分力](../functional_views/native_workpiece_cycle_20261004/render_001/workpiece_cycle_response.png)。

独立参考覆盖全部单元与DOF、三力、声明方向切线作用、CSC组装、平均约束及工件/支承反力；不是高精度穷举全部切线列。生产22F开始/19完成、11T完成、1solve，差额是3次返零力-only全步范围拒绝及原规则下的半步回溯，接受态通过不代表这些拒绝态已获资格。原“所有F开始必须完成”前置合同明确0HP关闭；[新保存态合同与计数对账](../lf_data_preparation/native_workpiece_001/coarse_square_cycle_001/reference_002/reference_contract.json)只修订这一已声明计数条件，全部原数学门保持。算术范围限制未完全消失；不扩大到接触、夹持压力、H2/H3、HF5、AD/JIT或全部任意输入。

Agent已按用户授权选择圆r8mm和正方形side16mm、中心(70,40)mm，粗方/细方/细圆三包构造通过；细方/细圆尚未求平衡。当前×1图仍明显张开，底/左节点窗口约1.896/2.039mm只是代理观测，非真实表面距离；微小预接触介质传力不能当有效夹持。新增纯保存态Q1外边界测量已通过14解析例及3接受态读取，双方排除y=40镜像切口、0新F/T/solve/HP；峰值底边最近无符号距离1.895882476mm、左边集1.981492877mm（最近为下角到下方实体，非侧向normal gap），卸载显示2mm，包容未检测。见[实际×1边界/最近点与独立代理曲线](../functional_views/native_workpiece_boundaries_20261004/render_001/native_boundary_geometry.png)。下一以同一粗方模型探索[0,.1,.25,.5,.25,.1,0]mm；依据实际作用和成本再扩到1/2/3mm及圆形/细网格。该大行程当前未执行。仅在main开发，origin固定为https://github.com/dudaxing/Compliant-TO-TMC.git。旧无工件细.025路径及公开重放保留各自冻结资格；本轮公开恢复仅验文件身份，不借用其数值重放资格。

以下增补保留各执行时点；当前结论和下一步以本条及报告末节为准。旧记录中的“尚未实现”和旧计划不作为当前状态。

2026-10-03最新：**普通原生模型的三分量NumPy切线入口及完整CSC组装已接通**。粗夹持器3200单元／6642DOF保存checker态，两个方向经40次新HP80/120全量核对通过，2案功能测试通过；最坏归一化误差4.43e-14，原门未改。三完整矩阵保留fixed行列及HuHu非对称性，见[实现、数值、成本及物理解释](NUMPY_FORCE_PROGRESS_20261002.md#native-tangent-20261003)与[两方向的内力变化率图](../functional_views/native_tangent_20261003/native_tangent_directional_actions.png)。本步21.25秒为粗例给定态实测，未求平衡／未执行.025mm目标；下一步接普通文件的小步平均驱动平衡并显示真实形变、输入力和自由输出。工件／研究H2-H3／完整接触与批量标签仍待完成。

2026-10-03最新：**普通文件的NumPy平均驱动平衡入口已接通**。粗夹持器0→.001mm实际路径、两态4次新HP80/120全量参考及两功能测试通过；输入力.0002084121N、自由+y输出.0011437157mm，独立残量1.54e-11。见[目标、实现、数值和物理解释](NUMPY_FORCE_PROGRESS_20261002.md#native-mean-20261003)、[实际形变/力/端口图](../functional_views/native_mean_20261003/native_mean_path.png)与[两帧动画](../functional_views/native_mean_20261003/native_mean_path.gif)。这是无工件小TEST，普通反向器新路径、完整行程、研究H2/H3、真实夹持与批量标签仍未完成；下一步同入口接粗反向器小步，现未执行。

2026-10-03最新：**新普通候选的NumPy完整力入口已接通，三例六制造态经64次新HP80/120全量核对通过，3案功能测试通过**。材料/HuHu/总力均满足原门，38400单元/全部DOF覆盖，最大归一化误差8.64e-17；保存模型、原始split状态、三力/应力/J/Hu/能量和全精度参考。见[目标、实施、物理效果和接续](NUMPY_FORCE_PROGRESS_20261002.md#native-force-20261003)、[位移/J/Hu](../functional_views/native_force_20261003/native_force_fields.png)、[三类内力](../functional_views/native_force_20261003/native_force_components.png)。本步为给定位移静态内力，未执行task的.025mm目标；下一普通模型的非对称切线/小步平均驱动平衡，工件/研究H2-H3/一般接触/批量标签仍待完成。

2026-10-03最新：**普通LF文件→HF几何→显式原生任务模型已接通**。三例23模型字段独立精确核对、5案构造测试通过；两粗模型17旧字段相同，细.5mm／26082DOF、五节点端半权、169fixed保持。看[材料与实际边界](../functional_views/native_model_20261003/native_model_applied_bcs.png)、[均值输入与自由输出](../functional_views/native_model_20261003/native_model_port_equations.png)及[目标、依据、实施与效果](NUMPY_FORCE_PROGRESS_20261002.md#native-model-construction-20261003)。本步材料和约束已构造，保存的.025mm没有被执行；未计算新力或形变。此前NumPy函数层及两规范小前缀已受限通过；下一步新普通模型静态力／参考，完整行程、工件、一般接触及批量HF继续待实现。

以下增补按执行时点保留；功能矩阵已更新到本条日期，旧近期建议作为开发历程阅读。

2026-10-03最新增补：**split平均输入与输出弹簧已接入NumPy平衡**，两条实体拉伸诊断路径／272项新HP门通过。看[实际x1变形、支反力、驱动力、自由输出及各节点位移](../functional_views/split_average_20261003/split_average_demo.png)、[四帧动画](../functional_views/split_average_20261003/split_average_demo.gif)及[完整记录](NUMPY_FORCE_PROGRESS_20261002.md#split-average-20261003)。.1mm平均输入时，10N/mm弹簧使输出收缩幅度减少约30.86%，输入力提高约5.083%；弹簧力+.416813N不是夹持力。这里节点只满足加权平均，未绑等位移。这次验证新控制器的小实体任务；原HF3机构已有历史功能结果，新候选尚需转接机构小行程、文件适配和真实工件任务。

2026-10-03后续增补：新NumPy h=.125接近和压紧已覆盖全部七原目标，19唯一新平衡态／420项HP80/120数值门通过。可看[真实x1末态和力曲线](../functional_views/numpy_c1_h0125_20261003/numpy_path.png)、[20帧动画](../functional_views/numpy_c1_h0125_20261003/numpy_path.gif)和[薄介质／间隙](../functional_views/numpy_c1_h0125_20261003/numpy_medium_zoom.png)，[实施与取舍记录](NUMPY_FORCE_PROGRESS_20261002.md#numpy-h0125-path-20261003)完整说明目标、行动、依据及效果。末态整顶反力71.4238945967 N，Jmin1.79848e-5；与粗网格末力相近，但间隙、J及底部节点分组仍变，不宣称全面收敛。接近已有小介质反力，闭合附近力迅速增加，压紧时介质被压薄。下一步优先split平均端口，以便把本候选用于真实机构平均驱动；真实工件、释放／重入与HF5仍未完成。

2026-10-03增补：新NumPy完整力及固定lift的实际CSC切线已通过原33制造＋63保存静态范围（96状态／129方向，774候选及774参考门）。微小应变拒绝已局部修复，原域和原门保持；[完整记录](NUMPY_FORCE_PROGRESS_20261002.md#numpy-scope-20261003)、[范围图](../functional_views/numpy_scope_20261003/numpy_scope_coverage.png)和[细网格保存形变与三力](../functional_views/numpy_scope_20261003/numpy_scope_terminal.png)可对照。最细保存末态h=0.0625／d=0.5 mm，完整顶边法向读数71.42389357316964 N，最小J约1.42743e-5；其**原HP平衡审计仍not_pass**。这次准确读取静态响应，没有对旧状态重新求解；一般接触、split平均端口和真实工件功能继续待实施。下一步是新的h=0.125 NumPy路径及新状态审计。

2026-10-02增补：新候选的[NumPy完整力、组装、解析切线与新平衡](NUMPY_FORCE_PROGRESS_20261002.md)已闭合一条C1固定压缩任务。三近旋转场/C1保存态三力门、七方向21切线门、15唯一新平衡态336项新HP80/120检查均通过；[新实际变形与力曲线](../functional_views/numpy_c1_20261002/numpy_path.png)、[16帧动画](../functional_views/numpy_c1_20261002/numpy_path.gif)可人工检查。以下2026-10-01矩阵中的“新候选完整force未闭合”是当时状态；10月3日静态范围已补齐，compiled AD和一般接触资格仍待后续。整体目标、平均端口及真实夹持任务边界继续适用。

2026-10-01。本文回答“目前能算什么、这些量意味着什么、下一步怎样得到有用结果”。依据现有源码和已经保存的数值结果整理；本次文档编写没有运行新的力学计算。近期执行细节另见 [CURRENT_STATUS](CURRENT_STATUS.md)，这里以功能为主。

## 目标与已经具备的能力

整体目标是独立 HF 正向力学评估器：给定普通几何文件、材料、边界与任务，得到有单位和符号的位移、节点内力、支反力及任务响应，最终支持真实夹持任务和候选比较。LF 负责几何生成与研究层的选择、统计；HF 运行时不依赖 LF 工作目录或优化器。当前已有真实机构的自由输出计算和受限接触计算，尚未完成真实工件夹持和批量 HF 评价。

“已实现”表示代码入口存在；“受限通过”表示对应已保存案例经过数值验证，范围按该案例理解；“未实施”表示不能从方案或外部结果推定为本线功能。

| 功能 | 代码与当前进度 | 物理含义及范围 |
|---|---|---|
| 独立几何读取 | [data.py](../hf_repo/src/hf_eval/data.py)、[evaluate/inspect](../hf_repo/src/hf_eval/evaluation.py)；两例规范几何导出、独立安装与断开 LF 读取已通过 | 单元掩膜、尺度、厚度、支承与端口可独立读取；新增 [lf_v2.py](../hf_repo/src/hf_eval/lf_v2.py) 纯数据转换和 [native_map.py](../hf_repo/src/hf_eval/native_map.py) 原生Q1准备均已验证两个规范包与一个细网格包；全部30／1800包和一般接触任务仍未验收 |
| 显式原生任务模型 | [native_project.py](../hf_repo/src/hf_eval/native_project.py) 与普通CLI已实现；三例23数组独立精确核对、5案构造测试通过 | 两粗规范17个旧模型intrinsic字段相同；细.5mm／五节点端半权与169fixed保持。材料、实际边界和算子已构造；两粗机构原.025mm TEST目标均已完成；细候选0→.001mm前缀/4新HP已通过，原.025task未完成；H2／H3仍待定 |
| 普通原生模型完整内力 | [native_force.py](../hf_repo/src/hf_eval/native_force.py)／普通CLI已实现；三例六制造态64次新HP80/120全域核对及3案功能测试通过 | 12场及完整model/state保存，材料/HuHu/总单元与节点力均可读/显示；给定位移内力不是平衡/任务反力；另经普通平均驱动平衡，两粗机构原.025mm TEST均已完成。另有细候选两接受态完整力/4新HP通过；细原.025task、完整研究行程及工件任务待推进 |
| 普通原生模型完整切线 | [native_tangent.py](../hf_repo/src/hf_eval/native_tangent.py)／普通CLI已实现；粗夹持器两方向40次新HP80/120全量核对及2案测试通过 | 三张量及full-DOF CSC保存，HuHu非对称保留；所有系数组装一致，HP物理导数范围仅两方向。给定态切线、两粗原.025及细原.025mm平均驱动fullCSC已通过；细接受态HP导数限固定lift端口方向，全部系数组装独立检查不等于HP全列导数 |
| 普通文件 NumPy 平均驱动平衡 | [native_mean.py](../hf_repo/src/hf_eval/native_mean.py)／solve_native_mean CLI；两粗机构各.025mm四态／各8新HP通过；细模型五节点端口原.025mm四态/8新HP通过 | 真实反向器+x输入→−x输出，夹爪+x输入→+y输出；原模型/端口权重/约束保持，保存完整力与CSC，输出自由且无工件，不能称夹持力或完整行程 |
| 实体线性诊断 | [linear.py](../hf_repo/src/hf_eval/linear.py)；反向器、夹持器两例通过 HF1 | 已得到微小输入下的位移、输入广义力与变形图；用于单位、方向、支承及线性极限检查，无工件接触 |
| TMC 非线性与内力组装 | [tmc_kernel.py](../hf_repo/src/hf_eval/tmc_kernel.py)、[tmc.py](../hf_repo/src/hf_eval/tmc.py)；HF2 修正 C-shape 的100原目标、HF3 两条40目标机构路径已验证 | **已有实际材料力、HuHu 正则力、总内力及一致非对称 Jacobian，并能求平衡。** 显式NumPy新候选已通过96静态状态、新C1路径及两规范机构小前缀；默认内核保持原入口 |
| 单数组平均端口控制 | [displacement.py](../hf_repo/src/hf_eval/displacement.py)、[project_evaluation.py](../hf_repo/src/hf_eval/project_evaluation.py)；HF3 两例自由输出路径通过 | 约束端口平均位移，端口节点仍能相对变形；输入乘子为驱动器作用于模型的广义力，可读出输出平均位移 |
| split 位移与 Dirichlet 路径 | [split_state.py](../hf_repo/src/hf_eval/split_state.py)、[split_prescribed.py](../hf_repo/src/hf_eval/split_prescribed.py)、[split_affine.py](../hf_repo/src/hf_eval/split_affine.py)；HF4-B 四组合完整通过，C1/C2 有受限通过结果 | 分别保存宏观 lift 与微小 fluctuation，避免微小 Newton 更新被大位移吞掉；现有 split 控制是规定自由度位移，支持显式阶段交接 |
| split 平均端口增广控制 | [split_displacement.py](../hf_repo/src/hf_eval/split_displacement.py) 已实现；两个小实体路径及两规范机构小前缀通过新参考核查 | 明确求解 `b_inᵀ(u_lift+u_fluctuation)=d` 的非对称增广CSC方程，节点允许相对位移；普通native任务模型构造已通过；两粗机构普通文件0→.025mm新路径及每态全量HP参考已通过；细候选五节点mean的0→.025mm四态/8新HP也通过；原task已完成（不同设计，不称网格收敛） |
| 受限法向接触 | [contact_reference_a0.py](../hf_repo/src/hf_eval/contact_reference_a0.py)、[contact_c1.py](../hf_repo/src/hf_eval/contact_c1.py)、[contact_c2.py](../hf_repo/src/hf_eval/contact_c2.py)；C1十条选定路径80态通过，v4细网格21态通过 | 已比较分离接近、规定闭合阶段及持续压紧的参考/TMC响应，也观察二维非均匀加载。v4只补测一个固定均匀任务 |
| 一般局部接触、释放与重新接触 | 未完成一般主动集及相应物理验证 | 目前不能保证任意接触面、有限面离开/重入、卸载释放、角点等情形；已有阶段约束激活不等于一般接触算法 |
| 真实夹持力 | 尚未实现带真实机构与工件的已验收任务；[HF5任务草案](HF5_LF_V2_ADAPTER_AND_TASK_PLAN.md)已有定义建议 | 用户已委托探索对称半工件和较大加载—卸载行程；下一接显式工件节点组及有符号法向反力。HF3自由输出位移、输入广义力或 LF 输出弹簧力均不能改名为夹持力 |
| 近旋转新候选的完整 force / AD | [split_kernel_invariants_hu.py](../hf_repo/src/hf_eval/split_kernel_invariants_hu.py) 的NumPy完整力与 [split_numpy_tangent.py](../hf_repo/src/hf_eval/split_numpy_tangent.py) 的解析机械切线已接通，并完成原静态范围和受限新平衡验证 | 96静态状态／774候选及774参考门通过，近旋转与微小应变误差已定位修正；完整compiled AD资格仍未闭合，不将NumPy结果换称AD通过 |
| HF5、优化与1800候选 HF 标签 | HF5尚未实施；优化/生成研究层在 LF/N4 来源中存在，独立 HF 不是新优化器。1800包来源与语义已有审阅，未在本线生成可验收的批量 HF 标签或最终排名 | 外部标签可作研究资料，不能当作本实现、当前任务的高保真结果；先用一个有效任务，再逐步扩大比较数量 |

历史功能结果分别见 [HF1](HF1_REPORT.md)、[HF2修正](HF2_REPAIR_REPORT.md)、[HF3](HF3_REPORT.md)、[HF4 split修正](HF4_REPAIR_REPORT.md)、[C1](HF4_C1_FINAL_REPORT.md)和 [v4](HF4_C2_V4_RETEST_REPORT.md)。这些报告中的旧“下一阶段未执行”描述属于当时状态；上述矩阵更新到2026-10-03最新数据适配阶段；原路径资格各按原报告范围。

## 现有物理结果怎样理解

HF3 两例真实几何已能独立计算有限变形下的自由输出。输入平均位移与输入广义力功共轭；夹持器的输出是单侧夹爪运动。没有工件且输出弹簧系数为零，所以其零输出弹簧力并不是“已测得零夹持力”。力、能量和位移均按所建下半模型报告，不隐含乘二。

可直接人工查看以下已有真实机构图；`path_01` 的保存来源及图标题均为反向器，`path_02` 为夹持器。两条路径各完成40个原目标，末态平均输入均为1 mm；数值取自 [HF3实际报告](HF3_REPORT.md)。变形图使用真实位移比例1，J图分别显示实体和介质的单元积分点最小值，不能当作接触压力图。

旧图标题的`qualification pending`保留绘图时点；后续80路径态与6桥接态的独立HP审计已完成，结论以HF3报告为准，不改写历史PNG。

| HF3无工件自由输出任务 | 末态输出平均位移 q_out [mm] | 输入广义力 R_input [N] | 已有图 |
|---|---:|---:|---|
| 反向器；输出正方向−x | 1.682304535 | 0.175256261 | [实际变形与J](../hf3_results/plots_002/path_01/last_accepted_deformation_and_J.png)、[路径响应与数值诊断](../hf3_results/plots_002/path_01/accepted_path_diagnostics.png) |
| 夹持器；下夹爪输出正方向+y | 1.161186104 | 0.216125158 | [实际变形与J](../hf3_results/plots_002/path_02/last_accepted_deformation_and_J.png)、[路径响应与数值诊断](../hf3_results/plots_002/path_02/accepted_path_diagnostics.png) |

这些图显示已有机构运动和求解响应，没有工件、夹持力或新的机构功能验收；本次只是补充已有图链接，没有增加物理覆盖或重新求解。

C1 的合成实体为2×1 mm、厚1 mm，初始间隙0.25 mm，材料E=100 MPa。它让实体参考 A0、实体正则化诊断 Aalpha 和 TMC 使用共同驱动。细网格 TMC 在名义闭合前 d=0.125 mm 已有约0.0003901 N反力，在 d=0.25 mm 有约0.20059 N；这是介质的接触前传力与转折响应。压紧后的净力接近 A0，有助于判断这一固定任务，但不能证明转折、局部接触压力或任意接触均正确。底边约束对模型的+y合力为正，顶边沿同一方向读出通常为负；完整反力包含材料和正则贡献。

非均匀任务中，规定阶段的平均预压保持0.375 mm，随后改变零均值驱动幅值。C1末态净力和变形已保存；C2进一步考察背景宽度、外底边约束和网格。局部负节点力是离散弱式反力，须结合材料牵引及正则贡献理解，不能直接把它裁成零或逐点当作物理接触压力。

## 可视化与最近一个功能步骤

本轮已将历史 `TMC_h025_uniform_r2` 的15个保存态画为 [数值、反力与末态变形图](../functional_views/c1_baseline_20261001/saved_mechanics.png)及 [15帧逐态压缩动画](../functional_views/c1_baseline_20261001/compression.gif)，[绘图元数据](../functional_views/c1_baseline_20261001/metadata.json)记录来源和实际数值。图含参考网格与实际变形，位移比例为1且全程使用相同位移色标；反力箭头另用固定显示比例0.03779618 mm/N，不是结构位移。位移显示是存盘两数组的舍入和，科学状态仍以两数组为准。静态图已实际查看，图中文字和六个面板可辨认。

粗网格末态驱动0.5 mm时，已存HP80法向力为71.4239021981 N；全底边生产反力约71.4239021980 N，其中实体底组约66.9596498900 N、外区介质组约4.4642523080 N。实体顶到刚面的保存间隙为4.2654e-6至5.7839e-6 mm。15态生产法向读数与HP80的最大绝对差约5.8634e-11 N。这些数值帮助看清“实体压向上平面、介质被压薄、约束反力增长”的已有功能；这是历史合成压缩基准的重绘，没有新FE或HP求解，不是LF机构的夹持力，也不授予新候选通过。

[保存态查看器](../hf_repo/scripts/plot_saved_mechanics.py)仅用NumPy/Matplotlib/Pillow读取三来源并绘图。元数据保存原读取位置、项目相对路径、bytes与SHA，异机可在恢复树中对照，不需复刻原盘符；本轮补相对来源字段没有重求解或改变图/动画。

已有 [C1两网格力比较](../hf4_c1_results/summary_v2/c1_force_comparison.png)、[分量与数值误差](../hf4_c1_results/summary_v2/c1_precision_and_components.png)和 [实际比例变形](../hf4_c1_results/summary_v2/c1_last_accepted_deformation.png)仍可对照。重绘不增加物理覆盖。

以下为2026-10-01当时的近期建议，其NumPy力／切线／平衡及后续平均端口工作已完成受限验证，当前接续见本页首条及最新实施记录。原建议是：为新候选已有 `_response(..., xp=np)` 提供清晰的 NumPy 力入口，先用原 `unit__near_rotation` 的实际 lift/fluctuation 计算全部八个自由度的材料力、正则力和总力。它能绕开当前大型 JIT 图的执行等待，直接回答新公式是否改善已知的力误差；这会增加可用的固定状态响应入口，尚不等于实现新的平衡路径。

本步只需比较已保存 HP80/120 参考，保留原总力 `1e-11`、两分力 `1e-9` 的归一尺度与门限，同时检查有限值、`J>0`、支持域及力分解一致性。给出八分量数值表、参考/变形网格叠图、三类力及误差图，明确该位移场是给定场。随后根据结果决定：通过则接一个已验证 C1 保存态的全局组装，检验实际残差的切线/Jv，再推进平衡控制；失败则针对实际误差分量修改。记录一份结果 JSON、数值数组与短说明即可。

Profiler及F系列日志只用于解释计算成本和运行异常，不能替代物理力、位移或接触验证。用户已批准的F-SELECT1可按其范围进行，其结果不是所有功能开发的永久前置门，也不会自动改变上述功能资格。每个后续功能步骤都应产生实际数值、力或变形图，再据结果选择下一步，避免预先展开长实验链。
