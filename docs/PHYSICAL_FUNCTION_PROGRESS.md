# 2026-10-15：第三个LF原25目标完整加载/卸载已实际PASS

L-CYCLE1按直接用户请求从零完成0→1.20→0mm，25原目标/25接受态，原物理条件及门保持，默认HF源码不改。峰值输入R0.266484676N、下半工件法向弱式作用0.058810521N（材料0.057949540N＋Hu0.000860980N），镜像双侧法向幅值和0.117621041N，bottom有限面首射线0.002374315mm，25态均无几何交叠/舍入歧义。实体峰值minJ0.974696，自由介质minJ3.86453e-5；这是近接触承载响应。

卸载回零R约1.68e-25N、q_out约-9.68e-25mm、工件Fy约-1.20e-27N，bottom/left射线恢复1/2mm。10对正同位移原目标标量近重合。179次Newton检查、186试探/32拒绝、0失败增量/二分；最大接受残差9.60874e-10仍在原1e-9门内。约199.1分钟/树采样峰1.94GB，219输出已原窗口封存。实际变形/反力/场3PNG、25帧GIF及收敛PNG/JSON完成，四PNG各检查一次。

[目标、实现、原因、物理结果与限制](../lf_data_preparation/native_interface_001/lf_third_cycle_001/RESULTS.md) · [实际变形与反力](../lf_data_preparation/native_interface_001/lf_third_cycle_001/run_001/view/comparison.png) · [真实收敛图](../lf_data_preparation/native_interface_001/lf_third_cycle_001/run_001/convergence/convergence.png) · [25态动画](../lf_data_preparation/native_interface_001/lf_third_cycle_001/run_001/view/lf_third_cycle/actual_states.gif) · [结果驱动的下一步](../lf_data_preparation/native_interface_001/lf_third_cycle_001/NEXT_STEPS.md)。

下一步优先选定峰值13与首卸14做独立HP80/120参考（新候选，尚未执行），随后复用现有消费者做三设计同定义对照。当前原API响应尚未关联新媒体/参考；全25态独参、连续压力、有效夹持、自由工件释放/稳定性及HF5整体仍未完成。保存模型与source_geometry随结果目录，可从其他工作目录按显式repo读取；先读新RESULTS，不原地重启已关闭执行包装。

后续均在main，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git。下方完整保留080273b时代raw历史，旧“待执行/下一步”只指当时；发布/恢复以实际交付回执和Git HEAD为准。

---
# 2026-10-15：第三个LF独立0→0.25→0.50mm试算PASS

L-PILOT1按直接用户请求唯一执行，三原目标/三接受态成功；0.5mm输入R0.085930828N、加权q_out0.481151214mm，bottom首射线间隔0.519139767mm，尚未达到夹持阶段。实体minJ0.987951803、自由介质minJ0.516400467。15次Newton检查、12试探全接受、0失败/二分；全部原门通过，约16.9分钟/树峰848691200B。实际变形/反力3PNG与3帧GIF、真实收敛PNG/JSON均完成。

[结果、改动、目标、原因与效果](../lf_data_preparation/native_interface_001/lf_third_pilot_001/RESULTS.md) · [实际变形与反力](../lf_data_preparation/native_interface_001/lf_third_pilot_001/run_001/view/comparison.png) · [收敛图](../lf_data_preparation/native_interface_001/lf_third_pilot_001/run_001/convergence/convergence.png) · [三态动画](../lf_data_preparation/native_interface_001/lf_third_pilot_001/run_001/view/lf_third_pilot/actual_states.gif) · [后续计算计划](../lf_data_preparation/native_interface_001/lf_third_pilot_001/NEXT_STEPS.md)。为复用现有显示器，仅补齐load_only两路径标签并运行三个既有单胞控制器回归方法，未改机械算法/力核/门或旧保存结果。

下半工件弱式Fy0.000351243N不是有效夹持力。下一步建议原25目标0→1.20→0mm完整循环，从零开始；当前load_only末态不能直接转换续算。新完整路径/独参/压力/有效夹持/稳定性及HF5仍未完成。main开发，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git。下方保留e010d20原raw历史；旧“待执行/下一步”仅描述当时，当前发布/恢复另核实际回执。

---
# 2026-10-15：第三个LF输入与未变形兼容性已通过

L-THIRD1按当前直接请求唯一执行：41项检查通过，原四掩码无损；新wave结构4349实体单元，与前两例分别1631/1099个实体单元不同。h0.5mm、13440单元、27378DOF，支撑/端口/固定工件约束兼容，case和自带source的model已保存。约18.72秒、进程树采样峰198811648B；一张四面板未变形图及完整记录完成，无新F/T/HP/平衡求解，制造资格仍pending。

[结果、目标、依据与限制](../lf_data_preparation/native_interface_001/lf_third_input_001/RESULTS.md) · [结构/工件/两设计差异图](../lf_data_preparation/native_interface_001/lf_third_input_001/run_001/undeformed_compatibility.png) · [结果驱动的下一步计划](../lf_data_preparation/native_interface_001/lf_third_input_001/NEXT_STEPS.md)。下一步建议独立0→0.25→0.50mm pilot；当前短加载任务不能直接续为完整循环，pilot良好后完整25目标需另从零。本轮仅准备与未变形检查，第三例实际变形、反力、独参及有效夹持尚未产生。

后续均在main，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git。下方保留ace8e92时代原文；旧“下一步/待执行”仅描述当时。当前入口见上述结果，发布/恢复以实际回执为准。

---
# 2026-10-15物理功能更新：两设计保存态对照已实际实现

L-COMP1唯一运行PASS：历史M五段25点与新LF单次25态，按同物理／网格／端口合同形成50条原状态及25组对照。新增反力／位移／工件材料-Hu-total作用图和底向距离／分区J／实体应变图，原变形媒体保链接；3方法通过、无新求解或HP。原M失败／源码历史及精确原参考来源保持。

[功能、效果及局限](../lf_data_preparation/native_interface_001/lf_saved_comparison_001/RESULTS.md) · [两图与逐行检查](../lf_data_preparation/native_interface_001/lf_saved_comparison_001/run_001/REVIEW.md)。两例实体峰值minJ仍约0.9734／0.9774，自由介质minJ约2.33e-5／3.78e-5；全局小J不等于实体塌缩。固定下半体弱式合力仍不等于连续压力或有效夹持，全部路径参考／网格域收敛／可移动工件与稳定性／HF5整体未完成。

下方完整保留dddb318历史原文，旧“下一步／未实现”只指当时。

---
# 2026-10-15物理功能补充：单例LF闭合，下一步为两设计响应对照

独立HF已具备NumPy完整力、组装／切线、平均位移平衡、保存续算、LF输入准备、API／CLI／batch及保存显示。新LF结构完成单次25目标0→1.20→0 mm，L-USE1已交付全25态外部消费；匹配独参仍为13／16两态。固定工件返回材料／Hu／总弱式合力，连续压力、有效夹持与自由体稳定性仍未完成。

历史另一结构同h0.5／84×40域、同物理任务已有五段25点到零；该组成路径保原failed/time_limit与源码版本差。优先复用两例保存结果作力／位移／有限距离／分区J对照，计划两PNG并链接旧变形。LF峰值实体minJ约0.977420，自由介质minJ约3.77508e-5，全局极小J不能解释为实体塌缩。

[下一步具体计划](L_USE1_NEXT_STEP_PLAN.md)。本轮未新增力学／HP／绘图，L-COMP1尚未实现或执行。下方27b53aaa完整历史原文保留，旧“下一步”仅表示当时。

---
# HF物理与功能矩阵

整体目标是独立HF读取普通LF几何，对一致明确的物理任务给出可审查响应；外部研究层、优化器和排名保持独立。生产、独参、显示与一般物理资格分开记录。

| 功能 | 已实现与真实证据 | 仍缺的实际范围 |
|---|---|---|
| 同任务小批量 | 薄API/CLI、15项mock；两例同19键物理任务各4态真实生产、各8新HP、各4帧图与自有摘要全部完成 | 重复性合同与HF5整体；不授排名 |
| 独立参考 | 两例全部接受态共16新HP、77174/307574检查；双例saved-only独审PASS | 全切线列、能量/应力/应变HP未由本轮授予 |
| 结构与数值显示 | 本轮各PNG/全4态GIF，×1及明确×40、反力/端口节点与加权位移/J；链接匹配自有result/新独参 | 图不增加接触、压力或一般模型资格 |
| 固定工件入口 | task1.1支持fixed_rigid square/circle及ordered_cycle；API透传path/模式；已有弱式力/holding/mirror/net摘要；历史方体24态/48HP | 先核薄API承接已有大行程任务的具体实例缺口；圆体完整资格不可借用 |
| 接触与自由体 | 历史固定方体弱式力、有限距离及约束反力可查看 | 一般有效接触、连续压力、自由体平移/转动/力矩稳定性和摩擦 |
| 网格与域 | 原生Q1及HF派生介质域；本轮h1、h.5为不同设计 | 同设计匹配网格与全路径域收敛仍须独立证据 |

| 设计 | 实际PNG | 全4态GIF | 自有qualified响应 |
|---|---|---|---|
| canonical | [结构与数值](../lf_data_preparation/native_interface_001/batch_forward_001/run_001/view/canonical/native_mean_path.png) | [动画](../lf_data_preparation/native_interface_001/batch_forward_001/run_001/view/canonical/native_mean_path.gif) | [JSON](../lf_data_preparation/native_interface_001/batch_forward_001/run_001/qualified_response_canonical.json) |
| native_fine | [结构与数值](../lf_data_preparation/native_interface_001/batch_forward_001/run_001/view/native_fine/native_mean_path.png) | [动画](../lf_data_preparation/native_interface_001/batch_forward_001/run_001/view/native_fine/native_mean_path.gif) | [JSON](../lf_data_preparation/native_interface_001/batch_forward_001/run_001/qualified_response_native_fine.json) |

本轮无工件，body力为null；R为半模型输入反力，q_out是加权端口位移而非钳尖间隙。历史固定体2|Fy|是双侧法向幅值和，装配净力为(2Fx,0)，不能混称压力或净夹持力。自有摘要accepted/full-path reference为true，但producer flags、全切线列、接触/夹持、压力与HF5资格仍为false。

下一步先核已有固定工件大行程任务，经现有薄API的具体实例缺口：逐项对照原任务路径、fixed_rigid几何、初始化选项、力摘要和保存输出，再选择最小功能接续。task1.1已支持square/circle及ordered_cycle，API已透传路径/模式，摘要已有body弱式力、holding、mirror/net和双侧法向幅值和；不重复实现这些入口。此处只是接续计划，没有启动新科学计算。

[本轮短报告](../lf_data_preparation/native_interface_001/batch_reference_v2_001/RESULTS.md) · [批量接口](NATIVE_BATCH_INTERFACE.md) · [历史固定体报告与真实图](WORKPIECE_ENLARGEMENT_20261007.md)


<details>
<summary>历史阶段记录（原文完整保留；旧状态只对应当时）</summary>

# 当前功能矩阵补充：真实薄API小任务已闭合

HF仍仅正向评价，不含优化器。此前固定方体2/4mm域完整周期物理证据保留；本次新入口无工件1µm任务2态、4新HP及保存图完成，范围见[实际报告](../lf_data_preparation/native_interface_001/real_forward_001/RESULTS.md)。

| 功能 | 当前已验证 | 仍未完成 |
|---|---|---|
| 输入与域 | 既有普通native几何/task，经真实API一次构模/求解/保存；原边界、任务ID和默认模式保持 | 同设计匹配网格/域收敛；其它新模型自身资格 |
| HF5与易用 | 薄API/CLI、21项首次纯功能验证、4旧摘要；另本次真实coarse两态路径及同结果参考/视图身份闭合 | 同任务比较、小批量、重复性合同与HF5整体 |
| 力与显示 | 新例半模型R、加权q_out、J/Hu及×1/标明×1000图；没有工件，工件力null | 新例不授夹持/接触/压力、全切线列或自由工件资格 |
| 能量范围 | 新例complete保存辅助材料能量；旧固定工件mechanical卡不计算该辅助项 | 独立能量验证；不得从材料能量缓存扩展物理资格 |

未改变匹配网格、压力/接触定义、圆体自身完整任务、自由体、摩擦和统一E源码推论的原边界。下面机械模式说明只对应此前固定工件卡，与本次complete不同；当时“后续科学卡尚未执行”亦仅历史。

---

以下完整原字节为8330b821阶段功能矩阵历史；当前变化以上方为准。

# HF物理功能进度：当前闭卡范围

HF复用LF/N4研究成果，提供独立正向评价，不含优化器。外部研究层负责比较、优选，HF5评价接口尚未完成。

| 功能 | 已实现/本次可查看 | 待实现或未取得资格 |
|---|---|---|
| 结构作用与变形 | 固定side18方体、2/4mm域、平均输入/自由输出、加载/回零、×1结构/GIF | 更多任务自身证据；自由体释放/稳定性 |
| 力及其位置 | R、固定下半工件总/材料/Hu(Fx,Fy)、holding及节点力；完整力、平衡和PORT方向切线作用的新参考 | 连续压力、有效接触/夹持定义、全切线列、摩擦 |
| 距离与场 | 有限面距离、保存J/Hu、binary64 Green主应变；原9点Lobatto含角点J门 | signed penetration、一般包含/自身重叠、应变/应力HP；场图不是压力 |
| 输入与域 | 自包含LFv2/明确task、Q1原生网格、HF派生介质域；82→84旧物理子域保持 | 同设计匹配网格、新入口真实任务尚待执行；新模型不继承旧资格 |
| 一般夹持 | 固定方体完整评价；固定圆体单元覆盖入口存在 | 圆体自身完整边界/平衡、自由刚体平移/转动/力矩、摩擦 |
| 统一E尺度 | 严格同branch、无独立力尺度的方程缩放推论 | 尚无本项新实验；降低E不作为改善贴合证据 |
| HF5与易用 | 薄一次API/CLI及保存摘要已实现；21项JSON/模拟集成通过，4份摘要可审，LF/N4研究层保留 | 新API真实平衡路径、同任务小批量和完整HF5重复性合同 |

R为半模型输入反力；下半工件Fy为固定体弱式on-body力，holding反向。2|Fy|为镜像法向幅值和，装配净力为(2Fx,0)。q_out为加权竖向端口位移，不是tip gap。Hu场最大值与Hu力分量分开记录。当前机械模式不计算辅助材料能量，不表示旧能量入口不存在。

两域结果不单独证明域/网格收敛。看同方向/原目标全曲线、材料/Hu分量、绝对量及距离，再选择一次物理敏感性或同设计细网格；同时推进薄正向接口，不重写LF/N4优化器。后续科学卡尚未执行。

统一E缩放是有条件的源码方程推论，尚未做本项实验：同几何/网格/厚度、位移约束与固定工件、同静态解分支，固定ν/γ/α/Lr，k_out=0且无未同比缩放的独立外载时，E→cE（c>0）理论上保持位移/贴合与q_out，机械力和反力乘c。物理刚度块缩放，但整个KKT矩阵不同比例缩放；数值舍入/解分支和迭代次数不保证相同。统一降低E不能据此宣称固定工件位移控制下更贴合。

[统一E源码说明](evidence/workpiece_enlargement_20261007/right_margin4_source_context/closure_001/009.md)；[HF5薄接口事实与未实现提案](evidence/workpiece_enlargement_20261007/right_margin4_source_context/closure_001/011.md)。

[完整报告](WORKPIECE_ENLARGEMENT_20261007.md)；[进度](evidence/workpiece_enlargement_20261007/right_margin4_progress.json)；[结构与力](../functional_views/right_margin4_20261007/complete_001/view/comparison.png)；[距离与力](../functional_views/right_margin4_20261007/complete_001/view/distances_forces.png)；[J/Hu/Green](../functional_views/right_margin4_20261007/complete_001/view/peak_fields.png)；[4mm实际动画](../functional_views/right_margin4_20261007/complete_001/view/right4col/actual_states.gif)。

[薄评价接口用法与实际验证范围](NATIVE_EVALUATION_INTERFACE.md)。


</details>
