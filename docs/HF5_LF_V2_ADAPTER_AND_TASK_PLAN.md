2026-10-04最新：**新增全工件节点力API/CLI，5解析项一次通过；009保存九态全部153节点、1377行CSV核对通过。** 见[目标、实现、效果、显示问题修正与后续](../functional_views/native_workpiece_nodal_20261004/square009_001/RESULTS.md)和[峰态材料/Hu/总节点力图](../functional_views/native_workpiece_nodal_20261004/square009_view002/render_001/nodes_state_004.png)。峰态右底角节点力模0.0127476461 N，Hu局部反向抵消显著；合力仍与009一致。派生力矩未新增HP资格，节点力不是压力。

原001绘图零矢量假箭头已人工检出并保留；独立002仅改短箭头缩放，一次重绘相同数据通过。本轮无新力学/HP或更大行程求解。下一步依据底射线0.0767107 mm、介质minJ0.0280804，冻结小幅近接触峰值和完整卸载任务；圆体/尺寸位置/细网格继续作为独立工况。以下逐字节保留此前原文，当前以本条和新报告为准。

2026-10-04最新：**009保留原完整九目标，1.75mm加载与回零已完成；63F/36T，18次新HP/174111检查通过。** 显式256单元分块切线不改变数学或默认full；三份对照保存态（007初态、008峰态、007回零）逐字节等价，原前八态32整档相同，生产373.57秒在原600/660预算内。见[目标、变更、效果/成本、范围与下一步](../lf_data_preparation/native_workpiece_001/coarse_square_cycle_009/RESULTS.md)及[实际九态×1动画](../functional_views/native_workpiece_cycle009_20261004/saved_render_001/animation_001/cycle009_actual_path.gif)。

底面射线.0767107mm、左面2.83278mm，介质minJ=.0280804；几何无已测跨域内部重叠，尚未证明有效夹持、压力、能量或应力HP。旧008仍是time_limit失败。下一步补工件节点力位置图，再根据间隙/J规划近接触增量；圆/细网格未执行。以下逐字节保留此前时点原文，当前以本条与新报告为准。

2026-10-04最新：**008的1.75mm峰值已达到，但九目标完整循环因600秒时间限制失败，8接受态保存至卸载.5mm；新HP0，原卡已关闭。** 底/左首次法向射线约.0767107/2.83278mm；第三介质minJ=.0280804，实体minJ=.956236；无已测跨域内部重叠，不能认定有效夹持。见[目标、实现、原因、实际效果/成本/限制与下一步](../lf_data_preparation/native_workpiece_001/coarse_square_cycle_008/RESULTS.md)和[实际峰/最后态与距离图](../functional_views/native_workpiece_cycle008_20261004/partial_region_view_001/render_001/native_region_path.png)。

四张独立保存partial观测/绘图卡各一次通过，不是机械重试或HP资格；未补返回零点。main/origin保持，009仅计划未执行。以下完整保留此前时点原文，当前以本条及新报告为准。

# HF5 计划草案：LF v2 几何接入、网格与任务映射、真实夹持任务（待所有者确认，未实施）

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

2026-10-03状态更新：LF v2转换、原生Q1准备及显式任务模型已分阶段实现，三例23模型字段精确核对／5案构造测试通过，见[实际范围与接续](NUMPY_FORCE_PROGRESS_20261002.md#native-model-construction-20261003)。新native模型入口不改旧HF3接口，仅在明确TEST task下构造材料和边界；.025mm指令未执行、工件为null。下一步普通模型的NumPy静态完整力／参考核对，再有限路径。全部30／1800包、统一细分政策、工件与正式HF5仍未完成；全研究H2／H3／5mm／测力建议继续待决定。

初稿：2026-09-27；事实勘误：2026-09-28。来源：外部功能审阅（`research_integration_20260920/external_reviews_20260927/`）指出的缺口 1、2，以及本仓库既定目标——在共同、明确的物理任务下，独立地对 LF 几何做正向力学评价。这是初稿时点的方案与停止边界；其后H1三例纯数据准备层已按阶段计划实施，当前状态见本页首条。未决定的网格／工件任务仍不启动新FE。[v4 唯一细网格补测](HF4_C2_V4_RETEST_REPORT.md)已完成：21/21 状态、651/651 检查、7/7 原目标；一次求解/一次审计额度已用完。默认内核仍未切换，HF5 仍未实施，不能把 v4 单路径资格推广为真实夹持任务资格。近期数值修复状态以 [CURRENT_STATUS](CURRENT_STATUS.md) 为准。

## 1. 现状（已核实）

- HF 权威几何格式为 `hf-geometry-1.0`（`geometry.json` + `geometry.npz`：`solid`、`design`、`passive_solid`、`passive_void` 四个 uint8 单元数组；网格、厚度、下半模型对称轴；区域标签是轴向线段：支承 `components [0,1]`，对称 `components [1]`，端口带方向与 `normalized_reference_arclength_trapezoid` 平均）。
- LF 当前导出 `dmftd.hf_export.v2`（`design.json` + `design.npz`：`solid`、`passive_solid`、`passive_void`、`design_domain` 四个 bool 数组；`regions_mm` 带区间语义）。把 v2 描述文件直接交给 `load_geometry` 会报 `descriptor_sha256 mismatch`（格式不同，不是文件损坏）。
- `project.py` 的项目任务写死为 80×40 单元、1 mm、20 mm 厚的下半模型，自由输出，没有工件，材料与介质参数冻结为 HF3 值。
- 待接入的 LF 数据：
  - 30 个交接设计（`research/hf_export_v2/`）：**23 个原生 80×40、1 mm；7 个原生 160×80、0.5 mm**。原“全部为粗网格”的描述不正确。按 `grid.native_mesh` 和 `grid.cell_mm` 读取原生几何；30 份描述的 `analysis_mesh` 虽均为 160×80，不能据此替换原生网格或自动确定 HF 分析网格政策。
  - 1800 个正式夹持器候选（`research/n4_formal_gripper_v1/export_v2/`，原生 160×80、0.5 mm）。
  - 两个规范 HF 几何对应的 LF 设计（`inverter__sweep__kin_1e+01__kout_1e-01`、`gripper__sweep__kin_1e+01__kout_1e+00`）都有 v2 包，可以做精确往返核对。
- v2 的区域语义：
  - 支承 x = 0、y∈[0, 8] 闭区间，`attachment: solid_incident`（与 HF3 的 `solid_incident_nodes_only` 相同）。
  - 实体对称段：夹持器为 [0, 60]，反向器为 [0, 80]。
  - 夹持器的背景对称是镜像线上的开闭区间 (60, 80]，属于 LF 的 `full_midline` 建模选择，不是物理夹持。
  - 输入端口：x = 0、y∈[38, 40]，方向 +x。
  - 输出端口：夹持器 x = 80、y∈[28, 30]，方向 +y；反向器 x = 80、y∈[38, 40]，方向 −x。
- 夹持器的被动区（已对全部 1800 个正式包核对）：被动实体钳口 x∈[60, 80]、y∈[28, 30]；其上方被动空区 x∈[60, 80]、y∈[30, 40]。下文建议的块区 x∈[70, 80]、y∈[32, 40] 与其下 2 mm 间隙在所有包中都是被动空区，没有实体单元。

本次网格勘误依据是用户提供的 `Diversity-TO-Compliant-O-main (10).zip` 内 30 份原生描述，逐包网格、描述 SHA256、ZIP SHA256 和统计保存在[只读元数据清单](../research_integration_20260920/lf_v2_grid_inventory_20260928.json)。源 ZIP 在读取前后哈希一致。本次只读 JSON 并确认对应 NPZ 成员存在，没有验证 NPZ 内容、转换几何、重新核查 1800 包被动区、导入 LF 或运行 HF；1800 包本次仅复核压缩包目录中的描述文件数，其他已核实语义仍是原审阅证据。

## 2. 数据适配器（HF 侧，纯数据）

- 在准备阶段做显式转换（例如 `lf_data_preparation/import_lf_v2.py`），只用标准库与 NumPy；不导入 `dmftd`，不重新优化，运行时 HF 仍只读 `hf-geometry-1.0`。
- 映射规则：
  - 掩膜：bool 转 uint8，无损；`design_domain` → `design`。
  - 区域：支承 → `support`；实体对称段 → `symmetry`；端口 → `input`／`output`，方向与平均规则原样保留。
  - 背景对称 (60, 80] 不作为几何标签，交给任务层的 `background_symmetry` 声明（HF3 的做法），并记录它来自 LF 的 `full_midline` 选择。
- 身份：每个转换产物记录 LF `design_id`、LF 包文件 SHA-256、LF `geometry_id` 与新的 HF `geometry_id`／`descriptor_sha256` 的映射；原 395 个几何文件不动。
- 验收（无 FE）：
  1. 两个规范设计的 v2 包转换后，与现有规范 HF 几何的掩膜与区域标签逐项相同。
  2. 反例：错误区间语义、错误方向、形状不一致、掩膜互斥被破坏、哈希不符，都应被拒绝。
  3. 1800 个正式包与 30 个交接包全部可转换、可被 `load_geometry` 读取，并附转换清单。

## 3. 网格与任务映射

- 新增任务模式（保留原 HF3 任务与接口不变），网格由几何元数据推导：物理域 80×40 mm、厚度 20 mm、下半模型不变，允许 1 mm 与 0.5 mm 单元。
- **需要决定**：分析网格用原生网格，还是统一用 160×80（对 80×40 原生设计做整数嵌套细分，每个单元一分为四，无损）。统一网格便于同任务比较；不做任何降采样。
- 材料、介质与正则沿用冻结值（E = 1 MPa 诊断材料、ν = 0.3、平面应变、γ = 1e-6、α = 1e-6、L_r = 80 mm），除非另行决定。

## 4. 任务定义（需要所有者决定）

**反向器（先做）**：平均输入位移控制到声明行程，自由输出。输出：各检查点的 q_out、输入广义力、有效状态、最小 J。先用 1e-3 mm 量级做线性极限核对，对照 LF 端口量；这些只记录，不设为跨模型等式门。

**夹持器工件任务**：

| 事项 | 建议（待定） |
| --- | --- |
| 工件 | 刚性矩形块，放在钳口与镜像面之间的介质区内，由块内与块边界节点全固定表示。钳口面 y = 30、块底 y = 32，初始间隙 2 mm；x 方向覆盖输出端口所在的 [70, 80]。块占据的单元为第三介质区。接触通过压缩间隙中的介质传递，这是 TMC 的本来方式 |
| 驱动 | 平均输入位移控制，行程到 5 mm，检查点事先声明 |
| 夹持力 | 块节点 y 向约束反力之和，按下半模型计，不自动翻倍；接触前由介质传来的力单独报告。输入广义力、LF 弹簧力或净合力范数都不能称为夹持力 |
| 有效性 | J > 0；实体与块不重叠；保存态做独立 80／120 位审计；接触状态按事先写明的规则分为接触前／接触中 |
| 与另一条 HF 线的关系 | 块的几何与驱动如与 N 线的固定工件任务取相同定义，就能在同一批几何上对照两个独立实现（TMC 与实体接触参照）。标签分开保存，不迁入对方的验收或结论，对照明确标为跨模型比较 |

实现要点（方案确认后另写执行计划）：
- 平均位移约束用拉格朗日乘子增广：b_inᵀ(u_lift + u_fluctuation) = d。
- 现有 [displacement.py](../hf_repo/src/hf_eval/displacement.py) 为单数组平均控制；[split_prescribed.py](../hf_repo/src/hf_eval/split_prescribed.py) 为固定自由度路径。2026-10-03新增 [split_displacement.py](../hf_repo/src/hf_eval/split_displacement.py) 已实现独立split平均端口增广系统，并通过两例原HF3小前缀；它不自动授予本文工件或HF5任务资格。
- 固定块节点与支承、对称约束一起进入固定自由度集合。
- 拟使用 split 状态；具体内核须在任务协议中绑定来源并满足相应数值与路径准入。稳定 F 保存态或 v4 单路径通过不会自动切换 HF5 生产内核。
- 写明方程、固定集合与一致切线，不靠接口拼接。
- 先用一个与 C0／C1 同类的最小参照核对测力定义，再接真实几何。

## 5. 推进顺序与停止规则

1. 适配器与转换验收（无 FE）。
2. 一个反向器、一个夹持器新包：导入 → 线性极限 → 有限行程自由输出，生成结果文件。
3. 夹持器工件任务：先最小参照，再一个真实设计；协议（任务、门槛、预算、停止条件）在运行前冻结。
4. 同一任务下的少量几何（3–5 个）比较，再做有针对性的网格、γ、α 敏感性检查。之后才谈扩大候选数量与优选预算。

每一步失败都保存原状态与回执，不自动重试、不调参；有效前缀与完整路径分开判定。计算在本机进行。第 2 步的有限先导也须先冻结自己的预算，再据实测决定后续额度：历史 v4 细网格路径的单次求解上限为 700 s，该额度已用完，不是 HF5 的授权预算。160×80 完整夹持任务的成本尚未实测。

## 6. 需要所有者确认的事项

- H1：适配器方案（准备阶段显式转换、无重采样、身份映射）已实现，两个规范设计及一个原生细网格包完成核对；三例不代替全部30／1800包转换验收。
- H2：分析网格政策（原生，或统一 160×80 整数嵌套）。
- H3：夹持器工件任务的定义（块的位置与大小、刚性假设、行程、夹持力定义），以及是否与 N 线固定工件任务取相同定义以便跨线对照。

原 H4“与 C2 v4 路径补测的先后顺序”已失效，v4 已完成，不再列作待执行事项。正式HF5后续实施仍依赖H2／H3任务决定、数据接入范围的扩展、对应资格及独立执行协议；本页更新不批准工件、5mm行程、测力定义或分析网格政策。
