# 当前接续：M-REF2细网格完整24态独立参考已通过（2026-10-09）

明确批准后的唯一新窗口PASS闭卡：48／48新HP80／120、24机械／24工件态、原15门、197绑定保持；helper2067.2045 s／outer2068.5295 s，采样自身RSS1390268416 B／tree1398767616 B。M-REF1历史失败未重跑。独立最大残差7.38799638e-10；全局总力归一化误差最大1.50051688e-15，声明PORT总切线action最大1.00623029e-16。全部13440单元／27378DOF已覆盖；完整CSC组装核对不赋予全部切线列的HP资格。

[完整目标、实现、为何、效果与限制](../lf_data_preparation/native_interface_001/nested_reference_002/RESULTS.md) · [同身份新reference](../lf_data_preparation/native_interface_001/nested_reference_002/run_001/reference/summary.json) · [实际launch](../lf_data_preparation/native_interface_001/nested_reference_002/reference_launch.json) · [独立终态审阅](../lf_data_preparation/native_interface_001/nested_reference_002/author/terminal_review.json)。当前卡／协议prepared字段保持来源冻结历史，当前事实以上述actual回执为准。

物理功能保持同设计h0.5完整0→1.2→0mm路径：峰值R0.378706N、下半工件Fy0.123179N、钳尖到底面0.00114436mm；卸载尖端回到(80,30)mm，微小残量保留。[既有24态真实变形及节点力](../functional_views/native_nested_cycle_20261009/complete_001/run_001/view/fixed_square/actual_states.gif) · [粗细六量曲线](../functional_views/native_nested_cycle_20261009/complete_001/run_001/view/mesh_response_comparison.png) · [图件物理解释](../functional_views/native_nested_cycle_20261009/complete_001/RESULTS.md)。新参考通过不把两个网格敏感性变成收敛结论，也不将节点弱式力称为压力。

最近下一步准备复用已有`summarize_saved_native_result`生成新增关联response／轻交付索引，匹配同24态result／本次reference／原raw view，第四粗细PNG由原phase关联；原response及raw view/phase不改，无新求解／HP／渲染。此步尚未执行；之后才准备包含材料+Hu、物理表面／对称切面／角点的总表面力定义。现有P只含材料，不能单独作为Hu模型总表面力。压力／有效夹持、网格／域收敛、圆体自身任务、自由体摩擦、正式标签／排名和HF5整体仍未完成。

整体目标仍为独立HF有限变形／TMC前向评估，不含优化或LF运行；main继续开发，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git。旧生产response中的reference/views not_provided及producer flags false保持原字节，本次参考单独归档。

<details>
<summary>M-REF1闭卡与M-REF2来源准备时的接续原文（历史状态不代表当前）</summary>

# 当前接续：M-REF1路径失败已关闭，HP尚未开始（2026-10-09）

用户明确批准后的唯一一次参考NOT_PASS：源码归档首个目录mkdir失败，HP0/0、机械/工件态0、原15数学门未开始。helper9.1415 s/outer11.3335 s，采样RSS111,505,408 B/tree116,588,544 B；187绑定保持，exit1、stop_reason null，无修复重跑/延期/force，窗口已关闭。

[目标、实际效果、失败原因、成本与限制](../lf_data_preparation/native_interface_001/nested_reference_001/RESULTS.md) · [实际launch](../lf_data_preparation/native_interface_001/nested_reference_001/reference_launch.json) · [stdout](../lf_data_preparation/native_interface_001/nested_reference_001/reference_stdout.log) · [只读路径诊断](../lf_data_preparation/native_interface_001/nested_reference_001/author/path_diagnosis.json) · [独立终态审阅](../lf_data_preparation/native_interface_001/nested_reference_001/author/terminal_review.json)。深层归档目录261字符、目标文件286字符，机器LongPathsEnabled0；前次静审遗漏该路径配置。11依赖唯一basename可平铺至已存在sources目录，最长202字符；不改系统策略或冻结M-REF1源。最近仅准备M-REF2具体候选并静审，再单独批准新参考资源，不缩成子集、不改变物理/原门。

既有M-CYCLE1完整24态和M-VIEW1的实际图件保持：[24态变形与工件节点力](../functional_views/native_nested_cycle_20261009/complete_001/run_001/view/fixed_square/actual_states.gif) · [同设计粗细曲线](../functional_views/native_nested_cycle_20261009/complete_001/run_001/view/mesh_response_comparison.png) · [图件和物理解释](../functional_views/native_nested_cycle_20261009/complete_001/RESULTS.md)。峰值R0.378706 N、下半工件Fy0.123179 N、钳尖到底面0.00114436 mm，卸载恢复初始坐标；两网格只是敏感性，原细网格独参仍未提供。HP/压力/有效夹持/网格域收敛/圆体自身任务/自由体摩擦/正式标签排名/HF5整体均未完成。main开发，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git。

[M-REF2具体执行卡](../lf_data_preparation/native_interface_001/nested_reference_002/M-REF2_CARD.md)及[最终独立静审](../lf_data_preparation/native_interface_001/nested_reference_002/author/final_static_review.json)已准备通过；唯一功能修正为平铺11个唯一依赖文件，本机最长归档文件202／科学文件205字符。全24态／48HP、原15数学门、4500／4560 s及采样8 GiB保持。新卡未授权、未执行；M-REF1已关闭，不能续用剩余窗口。

<details>
<summary>M-VIEW1及更早接续记录（历史原文）</summary>

# 当前接续：M-VIEW1细网格24态显示已通过（2026-10-09）

明确批准后唯一一次PASS闭卡：24几何+24节点力、24帧GIF、4PNG、24原目标/14量粗细CSV/JSON。helper39.70 s/outer40.43 s，采样进程树峰值474,722,304 B（约453 MiB），96绑定保持；新求解/F/T/HP/JIT/LF0（纯保存态源码依据，非动态hook监测），无修复重跑/延期/force。

本次显示的是M-CYCLE1同设计h0.5完整0→1.20→0 mm路径。峰值钳尖(79.701652,30.998856) mm、到底面有限线段距离0.00114436 mm，输入反力0.378706 N、平均输出位移1.016699 mm、下半工件Fy0.123179 N，两侧法向幅值和0.246359 N；完整镜像净力(−0.00175203,0) N。卸载末态钳尖回到(80,30) mm、底面距离1 mm，原力/位移微小残量保留。

[整体目标、工作、理由、实际效果、24态及解释](../functional_views/native_nested_cycle_20261009/complete_001/RESULTS.md) · [24帧实际变形与红色节点力箭头](../functional_views/native_nested_cycle_20261009/complete_001/run_001/view/fixed_square/actual_states.gif) · [六量粗细曲线](../functional_views/native_nested_cycle_20261009/complete_001/run_001/view/mesh_response_comparison.png) · [峰值局部场](../functional_views/native_nested_cycle_20261009/complete_001/run_001/view/peak_fields.png) · [实际回执](../functional_views/native_nested_cycle_20261009/complete_001/run_001/view/phase_view.json) · [独立终态审阅](../functional_views/native_nested_cycle_20261009/complete_001/author/terminal_review.json)。全部生产NPZ与图件已保存，恢复/查看不需重求解。

同设计h1→h0.5峰值R−7.01%、工件Fy+3.20%、介质minJ−28.50%、Hu最大分量+73.08%，只能说明两网格敏感性。min积分点J2.33967e−5不同于图中单元均值；Hu分量不同于Frobenius范数；平均输出位移不同于尖端距离；ON-body力不同于保持反力或压力。全部region-edge overlap标志false，但包含/自身重叠没有检查。原细网格reference/views仍not_provided、producer flags仍false；新raw view manifest提供匹配诊断，不能转移粗网格旧HP资格或改写原response。

最近下一步完成细网格保存态的独立数学参考适配，按原严格门区分数值误差和离散敏感性，再据结果推进局部网格/介质研究。尚未运行新参考；不立即重跑四小时完整路径。正式细网格HP、压力/有效夹持、网格/域收敛、圆体自身任务、自由体/摩擦、正式批量标签/排名、HF5整体仍未完成。整体为独立HF正向评估，不含优化/dmftd；继续main开发，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git。

[M-REF1具体卡：完整24态自己的48次HP参考，源码/协议已独立静审，待新批准](../lf_data_preparation/native_interface_001/nested_reference_001/M-REF1_CARD.md)；一次helper4500 s/outer4560 s、采样8 GiB，原数学与严格门保持，无新生产路径，首错即停、无修复重跑/延期/force。[下一步只读范围与成本依据](../functional_views/native_nested_cycle_20261009/complete_001/author/fine_reference_scope.json)。本轮M-VIEW1窗口已关闭，新参考未授权、未执行。

<details>
<summary>M-CYCLE1及更早接续记录（历史原文，“下一步”只指当时）</summary>

# 当前接续：M-CYCLE1细网格完整循环已通过（2026-10-09）

明确批准后唯一一次PASS闭卡：同设计h0.5、24原目标/24接受态、无二分态；加载1.20 mm再卸载0。44绑定保持，13,440单元/13,689节点/27,378 DOF与M-PREP1模型身份匹配。helper11461.54 s/outer11463.22 s（191.05 min），原生产缓存门通过；采样RSS约1.76 GiB，窗口已关闭，无修复重跑/延期/force。

峰值R0.378706 N、qout1.016699 mm、下半工件Fy0.123179 N、两侧法向幅值和0.246359 N；相较同设计h1，R−7.01%、Fy+3.20%。minJ2.33967e−5、峰值|Hu|分量较粗网格增73.08%，先作局部场与变形显示再决定后续研究；两网格尚不证明收敛。卸载末态标量近零。

[目标、实现、理由、效果、完整24态与限制](../lf_data_preparation/native_interface_001/nested_cycle_001/RESULTS.md) · [真实response](../lf_data_preparation/native_interface_001/nested_cycle_001/run_001/fixed_square/response.json) · [完整保存状态](../lf_data_preparation/native_interface_001/nested_cycle_001/run_001/fixed_square/result.json) · [独立终态审阅](../lf_data_preparation/native_interface_001/nested_cycle_001/author/terminal_review.json)。F443/386、T201/201；57原trial算术/J拒绝与8 Armijo拒绝完整保留。保存/摘要额外F/T0，新HP/JIT执行/LF/观察/渲染0。

最近下一步准备[M-VIEW1具体保存态显示卡](../functional_views/native_nested_cycle_20261009/complete_001/M-VIEW1_CARD.md)，只观察细网格保存态，复用粗网格既有观察数据，显示粗细曲线、实际变形/钳尖/作用力与J/Hu及全24帧；具体新卡独立静审后另获批准。新独参/views仍not_provided，flags false；不转移粗网格参考/图件资格。整体仍为独立HF正向评估，不含优化；细网格HP、压力/有效夹持、网格/域收敛、圆体自身任务、自由体/摩擦、正式标签/排名、HF5整体未完成。正式Git根以真实checkout为准，main开发，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git。

<details>
<summary>M-PREP1及更早的接续记录（历史原文，“下一步”只指当时）</summary>

2026-10-09 接续：M-PREP1已明确批准并一次PASS关闭，101/101构模检查，17绑定保持。实际同结构h0.5为13,440单元/13,689节点/27,378 DOF，fixed1548/free25830；helper16.7743 s/outer17.9396 s，tree RSS峰值187,662,336 B。[目标、实现、依据、效果和限制](../lf_data_preparation/native_interface_001/nested_mesh_preparation_001/RESULTS.md) · [未变形粗细网格/尖端图](../lf_data_preparation/native_interface_001/nested_mesh_preparation_001/run_001/nested_geometry.png) · [真实模型](../lf_data_preparation/native_interface_001/nested_mesh_preparation_001/run_001/model/model.json)。

四掩码物理并集、边界、同工件/材料和连续端口保持，5节点线积分/Q1尺度/物理约束验证通过。新F/T/求解/HP/JIT执行/LF均0；该图只有未变形几何，构模通过不授予细网格平衡或接触资格。最近下一阶段是[M-CYCLE1同任务细网格完整24目标加载—卸载卡](../lf_data_preparation/native_interface_001/nested_cycle_001/M-CYCLE1_CARD.md)，保持原门和零起点；新资源具体批准后才运行，其自有参考和变形/力图依赖真实生产结果。

<details>
<summary>身份核对完成、M-PREP1源准备时的接续记录</summary>

2026-10-09 接续：保存态身份核对已完成，24态/96对缓存、4对模型几何实际字节一致，37参考源及副本匹配；353文件/308,949,469字节，独立12对抽查通过。[完整依据与适用范围](../lf_data_preparation/native_interface_001/workpiece_identity_001/RESULTS.md)。历史同快照数学证据单独引用；原fresh-reference入口、API响应和资格标志保持，新独参仍not_provided，未重复48HP。

最近下一阶段为[M-PREP1：同一结构的派生细网格构模与未变形显示](../lf_data_preparation/native_interface_001/nested_mesh_preparation_001/M-PREP1_CARD.md)。2×2细分候选及协议已写，尚未生成数组、构模或绘图；源审阅归档后待明确批准。预测h0.5为13,440单元/13,689节点/27,378 DOF，保持同域、工件、物理端口和材料。现有两份不同LF设计不能充当此网格对照。构模通过后再根据实际结果制定细网格平衡卡；两个网格只报告敏感性。


</details>

# 固定工件真实 API：24态完整路径与可视化已完成

2026-10-08，W-API1完整加载—卸载已完成；明确批准的W-VIEW1唯一一次保存观察/绘图也成功闭卡，几何24/24、节点力24/24，3 PNG与全24帧GIF可人工检查。原力学源、输入/材料/端口/约束保持，W-VIEW1新增F/T/求解/HP均0；原窗口不续用。

峰值d=1.2 mm：尖端到底面距离0.0057303162 mm，输入反力0.4072527715 N，下半工件Fy=0.1193619515 N，两侧法向幅值和0.2387239030 N；卸载后回到初始形态，力接近零。图为真实×1与显示镜像；力箭头为工件节点弱式力。J色图为单元平均，与最小积分点J分开。

[目标、实现、依据、效果与限制](../functional_views/native_api_workpiece_20261008/complete_001/RESULTS.md) · [结构/尖端与力曲线](../functional_views/native_api_workpiece_20261008/complete_001/run_001/view/comparison.png) · [全24态动画](../functional_views/native_api_workpiece_20261008/complete_001/run_001/view/fixed_square/actual_states.gif) · [含图摘要响应](../functional_views/native_api_workpiece_20261008/complete_001/run_001/response_with_views.json)。新views=matched仅表示保存观察/图件匹配，独参仍未提供，producer flags仍false；原API生产JSON未改。

整体目标仍为独立有限变形/TMC正向评估，HF不包含优化。新producer独参、接触压力/有效夹持、匹配网格/域收敛、圆体自身任务、自由体/摩擦、正式标签/排名及HF5整体仍未完成。main开发，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git。

<details>
<summary>W-API1原生产闭卡记录（当时新HP/观察/渲染均0）</summary>

# 固定工件真实 CLI/API：完整加载—卸载已完成

2026-10-08，经用户明确批准，W-API1 唯一一次真实执行成功闭卡：24 原目标、24 接受态，1.2 mm 加载峰后卸载回 0 mm；CLI/batch/API/构模/求解/保存/摘要各一次，保存及摘要新增 F/T 为0。28 原 HF 源及36绑定不变。

峰值输入反力0.4072527715 N，加权输出位移1.0088461324 mm，下半工件 signed Fy=0.1193619515 N（材料0.1178513816、正则0.0015105699）；两侧法向幅值和0.2387239030 N，与 full mirrored net (-0.0048162478,0) N 分开。回零输入反力约1.208e-24 N。实际 helper2170.0202 s / outer2171.3780 s，原缓存生产门通过。

[目标、实现、理由、实际效果和限制](../lf_data_preparation/native_interface_001/workpiece_forward_001/RESULTS.md)及[新真实 response](../lf_data_preparation/native_interface_001/workpiece_forward_001/run_001/fixed_square/response.json)是本次恢复入口。新 HP/观察/渲染均0，reference/views未提供，producer flags仍false；旧固定工件48HP和旧图资格不转移。下一步优先复用保存态 viewer 展示新 API 数据，另立新范围/资源；W-API1已关闭不重跑。

整体目标仍是供外部 LF/N4 研究层使用的独立有限变形/TMC正向评估，不包含优化。接触/压力资格、匹配网格与域收敛、圆体自身任务、自由体/摩擦、正式标签及HF5整体仍未完成。main开发，origin保持 https://github.com/dudaxing/Compliant-TO-TMC.git。


</details>

<details>
<summary>65020bd及更早阶段历史原文（原字节完整保留；旧“下一步”与未执行表述只指当时）</summary>

# 恢复开发入口

先读[本轮短报告](../lf_data_preparation/native_interface_001/batch_reference_v2_001/RESULTS.md)、[生产index](../lf_data_preparation/native_interface_001/batch_forward_001/run_001/batch/index.json)、[双例保存独审](../lf_data_preparation/native_interface_001/batch_reference_v2_001/closure_review/dual_saved_review.json)及[视图回执](../lf_data_preparation/native_interface_001/batch_forward_001/run_001/view_execution_receipt.json)。两例生产、V2独参和B-VIEW2均已实际PASS关闭；各4态/8次新HP/4帧，V1的HP0失败仍保留，不再补算已闭卡。

| 设计 | 实际PNG | 全4态GIF | 自有qualified响应 |
|---|---|---|---|
| canonical | [结构与数值](../lf_data_preparation/native_interface_001/batch_forward_001/run_001/view/canonical/native_mean_path.png) | [动画](../lf_data_preparation/native_interface_001/batch_forward_001/run_001/view/canonical/native_mean_path.gif) | [JSON](../lf_data_preparation/native_interface_001/batch_forward_001/run_001/qualified_response_canonical.json) |
| native_fine | [结构与数值](../lf_data_preparation/native_interface_001/batch_forward_001/run_001/view/native_fine/native_mean_path.png) | [动画](../lf_data_preparation/native_interface_001/batch_forward_001/run_001/view/native_fine/native_mean_path.gif) | [JSON](../lf_data_preparation/native_interface_001/batch_forward_001/run_001/qualified_response_native_fine.json) |

下一步先核已有固定工件大行程任务，经现有薄API的具体实例缺口：逐项对照原任务路径、fixed_rigid几何、初始化选项、力摘要和保存输出，再选择最小功能接续。task1.1已支持square/circle及ordered_cycle，API已透传路径/模式，摘要已有body弱式力、holding、mirror/net和双侧法向幅值和；不重复实现这些入口。此处只是接续计划，没有启动新科学计算。

任意clone/cwd均用显式repo作为相对路径基础，在项目HF环境中运行；后续在main开发，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git。保持原任务、几何、参数、网格、边界和模式明确，独立新执行须记录新范围与预算。不要把无工件两设计差异当作网格收敛、排名或夹持资格；不要把已实现fixedbody入口再写一遍。发布状态以实际Git记录确认。


<details>
<summary>历史阶段记录（原文完整保留；旧状态只对应当时）</summary>

B-REF2 更新：最小V2候选已完成作者、root与独立静审，尚未制卡、导入或执行；[具体新卡与源码](evidence/native_batch_reference_v2_proposal_001/B-REF2_CARD.md)待新授权。原生产PASS、V1参考失败HP0及未生成批量图的状态保持。

## 当前恢复入口：生产通过，参考读取失败卡已关闭

先读 [CURRENT_STATUS](CURRENT_STATUS.md)、[当前结果](../lf_data_preparation/native_interface_001/batch_forward_001/RESULTS.md) 与该目录 `current_progress_002.json`、`reference_failure_diagnosis.json`。原两例生产卡 PASS，各四态/14F/9T，54份保存输出和28核心源字节保持。canonical 新参考一次 NOT_PASS：`coords` 字段不存在，HP=0；细例参考/图未执行。不得复跑原生产卡、失败参考卡或修改冻结 source/protocol/output。

下一步是最小 V2 参考包装的全部字段、状态和属性审阅，随后单独新卡；原参考数学、门和资源预算保持。V2 数值执行尚未授权或启动。新参考两例均通过后才能生成自有批量图与 qualified_response；旧单例图/HP不能替代新结果资格。开发只用 main，origin=https://github.com/dudaxing/Compliant-TO-TMC.git；任意克隆目录以实际 Git 根为准，不依赖这台机器的绝对工作路径。

以下为历史记录，当前以上方及真实终态记录为准。

---

## 最近恢复入口：批量功能已完成，真实两例待执行

先读[当前状态](CURRENT_STATUS.md)和[批量接口用法](NATIVE_BATCH_INTERFACE.md)。main新增两例顺序入口并通过15项mock检查；下一项是明确manifest中的两个原0.025mm任务及新资源卡。旧科学窗口均已关闭，新批量没有真实结果；不复用旧单例参考或图作为新batch资格。

---

以下完整原字节保留为7e54e34阶段历史；批量当前状态以上方为准。

## 当前：真实薄评价入口已完成小型正向任务

HF复用LF/N4几何与研究成果，提供独立正向力学评价，不含优化器。新入口从无关工作目录、显式repo完成无工件夹持器0→0.001mm（1µm）任务：2个真实接受态、4次新HP及保存图通过；真实构模、求解、缓存保存和响应生成各一次，默认complete/full/tangent与25个既有核心文件保持。前一阶段21项JSON/模拟集成是首次纯功能验证，本次才验证真实调用流程。

这项小任务检验接口接通与身份/保存语义；此前固定side18方体、4mm右介质域完整24态/48HP仍是大行程固定工件力学的独立证据。两者不混用资格。HF5整体、同任务比较/小批量、匹配网格、连续压力、有效接触定义、自由体和摩擦仍待完成；q_out是加权端口位移，不是钳尖间隙。

[本次效果与实际图](../lf_data_preparation/native_interface_001/real_forward_001/RESULTS.md)；[接口用法](NATIVE_EVALUATION_INTERFACE.md)。后续按现有物理证据选择同任务比较或匹配网格步骤，不重跑旧闭卡；开发统一main，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git。

---

以下完整原字节为8330b821阶段历史；其中“新API真实任务尚待执行”等文字只描述当时状态，当前以上方及本次闭卡报告为准。

## 当前：薄原生评价接口已通过纯功能验证

HF保持独立正向评价、不含优化器；4mm固定方体完整24态、48新HP及已有变形/力视图仍是最近的实际力学证据。新增一次evaluate_native入口、保存JSON摘要及任意cwd CLI，21项功能测试和4份保存响应导出通过；25核心文件原字节保持，真实科学调用为0。本轮模拟集成不表示已从新入口执行真实任务，HF5整体尚未完成。

响应区分任务目标、请求终点和最后接受态；参考与图链接核对同结果/模型/全部状态身份。下一步独立新窗口执行小型真实API任务，再推进同任务比较与小批量；压力/接触判据和匹配网格等仍待验证。[接口用法与本轮效果](NATIVE_EVALUATION_INTERFACE.md)。main开发，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git；旧执行卡不重跑。

---

以下原字节保留为前一阶段历史；当前接口状态以上方及接口报告为准。

## 当前：4 mm右介质域完整正向评价已完成

HF复用LF/N4几何与研究成果，提供独立正向力学评价，不含优化器；开发统一main，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git，HF5尚未完成。同固定side18中心(71,40)、h1/E1/γ=α=1e-6/Lr80，2→4mm域的新完整24态、48新HP及488232检查和保存视图通过；未借旧模型资格。

最大加载行程态d=1.2mm：半模型R=0.407252771N，下半工件Fy=0.119361952N，两侧法向幅值和=0.238723903N，有限tip底面距=0.00573031619mm。2|Fy|不是装配净力，q_out是加权端口位移。同原目标全曲线、材料/Hu分量及绝对量须一起看，不由峰值概括全路径或域/网格收敛。压力/接触定义、圆体自身完整任务、自由体/摩擦和HF5仍待实现或验证。

[完整报告](WORKPIECE_ENLARGEMENT_20261007.md)；[实际进度](evidence/workpiece_enlargement_20261007/right_margin4_progress.json)；[功能矩阵](PHYSICAL_FUNCTION_PROGRESS.md)；[结构/力](../functional_views/right_margin4_20261007/complete_001/view/comparison.png)；[距离/力](../functional_views/right_margin4_20261007/complete_001/view/distances_forces.png)；[4mm动画](../functional_views/right_margin4_20261007/complete_001/view/right4col/actual_states.gif)。异目录恢复main后以实际Git根定位；旧闭卡不重跑，下一项据整条2/4mm曲线选择一个物理或匹配网格步骤。默认tangent未切换，探索显式port_projection，HF不重写优化器。

---

以下整段原字节为收尾前历史；当前状态以上方及最新报告/进度为准。

<!-- current-front right-margin actualcomplete; predecessor abf62b04d0a384f3c9cfa352dd6232ad1d4ab3d1 -->

## 当前：右侧2 mm介质域完整对照已完成（2026-10-07）

HF本项目仅提供独立有限变形/TMC正向评估，不含优化器；复用LF/N4成果，供外部LF/N4研究层比较、优选并推进HF5评价接口；开发统一main，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git，HF5尚未实现。固定side18中心(71,40)、右面80，分析域80→82；原物理坐标、h1/E1/gamma1e-6/alpha1e-6/Lr80/端口/支撑保持，只新增右介质列和相应顶边。

新analysis_domain API write_right_medium_geometry(parent_path,output_dir,right_columns:int)->Path，与prepare_analysis_domain.py CLI只生成新HF几何；原LF数据/provenance保留，全域不冒称LF native。任务geometry身份、DOF和PORT direction另行重建，tip按坐标(80,30)选择。5测试和准备27字段映射已通过；新完整24态、48新HP80/120、476733检查及实际视图通过。

新加载峰值d=1.2 mm：半模型R=0.407199455 N，下半体Fy=0.11923167 N，2|Fy|幅值和=0.238463339 N，钳尖底面距=0.00571667264 mm。2|Fy|不是完整装配净力；q_out为原加权端口位移。压力/接触判据、网格及域收敛、圆体/自由工件/摩擦仍待验证或实现。默认tangent不切换，探索仍显式port_projection。

[完整记录](WORKPIECE_ENLARGEMENT_20261007.md)；[实际进度](evidence/workpiece_enlargement_20261007/right_margin_progress.json)；[结构/力](../functional_views/right_margin_20261007/complete_001/view/comparison.png)；[距离/力](../functional_views/right_margin_20261007/complete_001/view/distances_forces.png)；[新实际动画](../functional_views/right_margin_20261007/complete_001/view/right2col/actual_states.gif)。

从任意目录恢复main后按实际仓库根定位文件；几何CLI示意：python <仓库根>/hf_repo/scripts/prepare_analysis_domain.py --geometry <父geometry.json> --output <全新目录> --right-columns 2（不创建task或求解）。下一步根据本轮实际效果选择匹配网格和域余量敏感性，再推进压力/接触定义及HF5；未执行后续科学卡，旧资格不能转给新模型。

---

下面完整原文是abf62b04阶段历史，原字节保留；当前进度以上方和最新报告为准，旧已关闭卡不重跑。

<!-- current-front gamma-half complete 2026-10-07; historical predecessor 16ee4ebb67161e2c8bc9a27d8e44285308778171 -->

## 任意目录接续 main：γ 对照已完成（2026-10-07）

从 `https://github.com/dudaxing/Compliant-TO-TMC.git` 的 `main` 恢复，按实际仓库根目录定位文件，无需原电脑路径。先读本页上方、[当前状态](CURRENT_STATUS.md)、最新报告与进度 JSON，再核对下方实际图／动画；保存态可视化不能替代新物理任务的参考。

固定方块边长 `18 mm`、中心 `(71,40) mm`，对称下半体为 `[62,80]×[31,40] mm`，右面 `x=80 mm`，右侧介质余量仍为零。本次仅将 `gamma=1e-6` 改为 `5e-7`，其余物理参数、几何、端口、支撑与网格保持；24 个原始目标完成 `0→1.2→0 mm` 加载—卸载。

新工况完整24态通过；全部24态的新 HP80/120 参考共48次，465255项检查通过。加载峰值 `d=1.2 mm`：半模型输入反力 `R=0.406911563 N`，下半工件 `Fy=0.118620312 N`，对称两侧法向力幅值和 `2|Fy|=0.237240623 N`；钳尖到底面的有限距离为 `5.535555 μm`。`2|Fy|` 不是完整装配净力。

相同加载目标 `0.75–0.85 mm` 的 Fy 下降约42–43%，峰值下降0.3254%；因此不能概括为全路径不敏感。这是已通过独立数值参考的合力与变形对照，压力分布、物理接触／夹持判据仍未验证。

[报告末尾 γ 对照](WORKPIECE_ENLARGEMENT_20261007.md)；[实际进度与证据](evidence/workpiece_enlargement_20261007/gamma_half_progress.json)；[同目标力／间隙对照](../functional_views/workpiece_gamma_20261007/complete_001/view/gamma_comparison/matched_force_gap.png)；[新工况24帧实际动画](../functional_views/workpiece_gamma_20261007/complete_001/view/gamma5em7/actual_states.gif)。

本轮未改核心代码，默认 `initial_guess="tangent"` 保持；探索工况显式使用已有 `port_projection`。`q_out` 仍是加权竖向端口位移，与钳尖间隙分别报告。HF5 优化耦合尚未实现；圆体、自由工件及摩擦也未完成。

下一步路线是以 `gamma=1e-6` 基线在同一物理坐标下扩展右侧第三介质 **HF 分析域**：保留原 LF 数据、原子域的 native 网格 `h=1 mm`、E、alpha、`Lr=80 mm` 及端口／支撑位置，重建 DOF 与 direction，并按坐标选择钳尖。该域扩展尚未执行，不能继承本轮旧模型的资格。 新计算须以实际新模型、协议和终态记录为准；历史卡及旧接受态不提供新域资格。

---

以下完整原文是 **16ee4ebb 阶段历史**，逐字节保留当时的状态、计划与命令；当前进度以本页上方及最新报告为准，历史中的已关闭执行卡不应重跑。

<!-- current-front 2026-10-07; actual complete records; baseline b310033 -->

## 从任意目录继续 main 开发

项目目标是把 LF/N4 的几何与研究任务交给独立 HF 正向评估器，获得有限变形、力、TMC 作用和加载—卸载的可解释结果，再推进优化接口。当前是固定方体中心 `(71,40)` mm、边长 `18` mm、对称下半体 `[62,80]×[31,40]` mm、24 目标 `0→1.2→0` mm 的探索。右面贴到分析域边界；原 x71/side16 是对照，两个后续失败工况保留原终态。

当前可接续事实：完整24态、原24目标和回零成功；新参考48 HP80/120、465220检查通过；峰值单侧Fy=0.119008 N、双侧法向幅值和=0.238015 N、钳尖底面距0.005701 mm（5.7 μm）。

[整体/力曲线](../functional_views/workpiece_enlarge_20261007/complete_001/view/comparison.png)；[钳尖/应变/节点力](../functional_views/workpiece_enlarge_20261007/fit_001/view/local_fit.png)；[24帧实际动画](../functional_views/workpiece_enlarge_20261007/complete_001/view/projection001/actual_states.gif)。

可选 `initial_guess="port_projection"` 已通过 15 项小模型测试，保留默认初猜行为、真实 KKT LU 和原 Newton／J 门。新大模型的状态、HP 资格与图仅按上方最终记录判断。先读 [本轮报告](WORKPIECE_ENLARGEMENT_20261007.md) 和 [当前状态](CURRENT_STATUS.md)，核对峰值加载与共同加载位移的实际图和力。

下面的 PowerShell 命令从所选新目录恢复文件，路径不要求与原电脑一致：

```powershell
$repoRoot = Join-Path (Get-Location).Path 'Compliant-TO-TMC'
git clone --branch main https://github.com/dudaxing/Compliant-TO-TMC.git $repoRoot
git -C $repoRoot switch main
python (Join-Path $repoRoot 'tools/handoff.py') verify
```

证据大资产按实际移交清单恢复：`python (Join-Path $repoRoot 'tools/handoff.py') fetch-evidence`，随后同入口 `verify --full`。文件校验用于核对来源；另机数值实验使用新任务与新输出目录，原已关闭卡作为历史保留。

当前源码包要求 Python 3.13。新建环境并使用仓库锁定依赖；无需复制原机器虚拟环境：

```powershell
py -3.13 -m venv (Join-Path $repoRoot '.venv-hf')
$hfPython = Join-Path $repoRoot '.venv-hf/Scripts/python.exe'
& $hfPython -m pip install --require-hashes -r (Join-Path $repoRoot 'hf_repo/requirements.lock')
& $hfPython -m pip install -r (Join-Path $repoRoot 'hf_repo/requirements-dev.txt')
& $hfPython -m pip install --no-deps --no-build-isolation -e (Join-Path $repoRoot 'hf_repo')
```

开发只在 `main`，origin 保持上述仓库。下一项功能按本轮真实力／间隙／变形确定：先逐项检查同任务网格、gamma/alpha和右侧介质余量；据此明确接触／夹持判据与压力，再探索圆体或可动工件、HF5/LF-N4 接口。`q_out` 是 `(80,28/29/30)` mm 的加权竖向输出端口；钳尖间隙另测。输入 `R_input`、单侧工件 `Fy`、双侧 `2 abs(Fy)` 和全体净力各自报告，避免混读。

---

## 历史记录

以下保留此前完整文字与命令；其“当前”“下一步”对应当时阶段。现在的结论和开发顺序以上方及本轮报告为准。

<!-- current-front 2026-10-05 (phase20261004); historical baseline 38ecc77cc14fee9fd0c69d026ed8df1e32b19bc2 -->

## 当前可移植接续入口

pose002 已完整回零：17 态、34 次新 HP80/120、328767 项检查通过。

soft001：完整加载—卸载完成，14 个实际接受态；独立参考全量通过：28 次新 HP80/120、270829 项检查。实体E减半、gamma/alpha倍增，绝对介质Lamé/kr不变；局部接触边最大应变增加约9.06%，但钳尖右面距离.167270→.172489mm，工件Fy约减半，未证明更贴合。E1保留为当前基准，E.5为独立低驱动力探索。

[总体目标、实际结果、成本与资格](WORKPIECE_SHIFT_AND_SOFTNESS_20261004.md)；[完整实际路径图](../functional_views/workpiece_shift_20261004/complete_002/view/comparison.png)、[局部贴合与钳尖图](../functional_views/workpiece_shift_20261004/fit_001/view/local_fit.png)；[本轮持续总记录](evidence/workpiece_shift_20261004/final_comparison.json)。

旧 pose001 失败只作成本来源；[T44 v5 修正与独立验证](../lf_data_preparation/native_workpiece_001/t44_direction_scaling_repair_001/README.md) 的资格限已捕获 T44，不延伸为一般接触或全列资格。

从任意新目录获取 main 并校验文件：

```text
git clone https://github.com/dudaxing/Compliant-TO-TMC.git my-hf-work
cd my-hf-work
git switch main
python tools/handoff.py verify
```

必要大资产按下面保留的移交说明 fetch-evidence 后 verify --full；无需创建原机器 D: 路径。先读本轮总报告/数值与图，再按新的明确任务和预算开发；历史命令和已闭卡不是当前同路径重跑指令。

下一选择：优先定义最右钳尖与有限工件面的覆盖对齐；x72会触及x80分析域边界，必须作为新边界贴靠任务，不能继承x71资格，随后再比较局部软化，不继续盲目降低整体E。接受态资格限机械力、声明 PORT 方向切线作用、组装/平衡与工件投影；不含压力、应力 HP、辅助能量、全切线列或自由工件夹持。

---

## 历史内容（截至 38ecc77，以下原字节保留）

以下‘最新/下一步/未完成’均指其当时时点；当前状态以本页上方和本轮总记录为准。

2026-10-04最新：**010的1.8 mm完整加载—卸载已完成，原11目标全部达到，包含原控制器额外.25 mm的12实际态；新Ref003全24 HP/232272项检查通过。** 输入峰反力.414394469 N、输出+y=2.08019363 mm，底/左有限法向射线.0317909716/2.85343057 mm，介质minJ=.00662089875、实体minJ=.955246548。见[整体目标、实现、排查、效果、全部失败/资源/资格与后续](../lf_data_preparation/native_workpiece_001/coarse_square_cycle_010/RESULTS.md)、[实际12帧×1动画](../functional_views/native_workpiece_cycle010_20261004/saved_render_001/animation_001/cycle010_actual_path.gif)、[J/Hu位置图](../functional_views/native_workpiece_cycle010_20261004/saved_render_001/fields_001/peak_saved_J_Hu.png)。

新12次几何/12次全节点力观察、1836行节点CSV和位置图完成，右下角节点峰力模.0181035417 N。原010参考因错误完整计数假设在HP前失败、Ref002在16HP/7完整态后超时，均关闭保留；Ref003新预算独立全量重新计算，没有拼接旧前缀。T44/F77范围失败虽已按原控制器回滚二分，primitive根因仍未修复；新资格只覆盖接受机械态，不含失败trial、压力/夹持、能量、应力HP或切线全列。原生产flags保持false。下一优先定位已捕获范围问题，再补圆体边界观察并开展匹配形状工况；本轮圆/细网格/更大峰值未运行，整体项目仍未完成。以下逐字节保留先前记录，当前以本条和新报告为准。

2026-10-04最新：**新增全工件节点力API/CLI，5解析项一次通过；009保存九态全部153节点、1377行CSV核对通过。** 见[目标、实现、效果、显示问题修正与后续](../functional_views/native_workpiece_nodal_20261004/square009_001/RESULTS.md)和[峰态材料/Hu/总节点力图](../functional_views/native_workpiece_nodal_20261004/square009_view002/render_001/nodes_state_004.png)。峰态右底角节点力模0.0127476461 N，Hu局部反向抵消显著；合力仍与009一致。派生力矩未新增HP资格，节点力不是压力。

原001绘图零矢量假箭头已人工检出并保留；独立002仅改短箭头缩放，一次重绘相同数据通过。本轮无新力学/HP或更大行程求解。下一步依据底射线0.0767107 mm、介质minJ0.0280804，冻结小幅近接触峰值和完整卸载任务；圆体/尺寸位置/细网格继续作为独立工况。以下逐字节保留此前原文，当前以本条和新报告为准。

2026-10-04最新：**009保留原完整九目标，1.75mm加载与回零已完成；63F/36T，18次新HP/174111检查通过。** 显式256单元分块切线不改变数学或默认full；三份对照保存态（007初态、008峰态、007回零）逐字节等价，原前八态32整档相同，生产373.57秒在原600/660预算内。见[目标、变更、效果/成本、范围与下一步](../lf_data_preparation/native_workpiece_001/coarse_square_cycle_009/RESULTS.md)及[实际九态×1动画](../functional_views/native_workpiece_cycle009_20261004/saved_render_001/animation_001/cycle009_actual_path.gif)。

底面射线.0767107mm、左面2.83278mm，介质minJ=.0280804；几何无已测跨域内部重叠，尚未证明有效夹持、压力、能量或应力HP。旧008仍是time_limit失败。下一步补工件节点力位置图，再根据间隙/J规划近接触增量；圆/细网格未执行。以下逐字节保留此前时点原文，当前以本条与新报告为准。

2026-10-04最新：**008的1.75mm峰值已达到，但九目标完整循环因600秒时间限制失败，8接受态保存至卸载.5mm；新HP0，原卡已关闭。** 底/左首次法向射线约.0767107/2.83278mm；第三介质minJ=.0280804，实体minJ=.956236；无已测跨域内部重叠，不能认定有效夹持。见[目标、实现、原因、实际效果/成本/限制与下一步](../lf_data_preparation/native_workpiece_001/coarse_square_cycle_008/RESULTS.md)和[实际峰/最后态与距离图](../functional_views/native_workpiece_cycle008_20261004/partial_region_view_001/render_001/native_region_path.png)。

四张独立保存partial观测/绘图卡各一次通过，不是机械重试或HP资格；未补返回零点。main/origin保持，009仅计划未执行。以下完整保留此前时点原文，当前以本条及新报告为准。

# 在新电脑或任意新目录接续开发

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

2026-10-03最新：**普通文件的NumPy平均驱动平衡入口已接通**。粗夹持器0→.001mm实际路径、两态4次新HP80/120全量参考及两功能测试通过；输入力.0002084121N、自由+y输出.0011437157mm，独立残量1.54e-11。见[目标、实现、数值和物理解释](NUMPY_FORCE_PROGRESS_20261002.md#native-mean-20261003)、[实际形变/力/端口图](../functional_views/native_mean_20261003/native_mean_path.png)与[两帧动画](../functional_views/native_mean_20261003/native_mean_path.gif)。这是无工件小TEST，普通反向器新路径、完整行程、研究H2/H3、真实夹持与批量标签仍未完成；下一步同入口接粗反向器小步，现未执行。

main 93851df的[实际公开恢复](../handoff/native_mean_20261003/public_recovery_verify.json)通过：12 payload／77数组及图包6文件字节相同，物理/求解诊断JSON除耗时与关联hash外一致，0新HP。下一粗反向器小TEST尚未执行。

2026-10-03最新：**普通原生模型的三分量NumPy切线入口及完整CSC组装已接通**。粗夹持器3200单元／6642DOF保存checker态，两个方向经40次新HP80/120全量核对通过，2案功能测试通过；最坏归一化误差4.43e-14，原门未改。三完整矩阵保留fixed行列及HuHu非对称性，见[实现、数值、成本及物理解释](NUMPY_FORCE_PROGRESS_20261002.md#native-tangent-20261003)与[两方向的内力变化率图](../functional_views/native_tangent_20261003/native_tangent_directional_actions.png)。本步21.25秒为粗例给定态实测，未求平衡／未执行.025mm目标；下一步接普通文件的小步平均驱动平衡并显示真实形变、输入力和自由输出。工件／研究H2-H3／完整接触与批量标签仍待完成。

科学交付main ae8f29c及[实际公开恢复证明](../handoff/native_tangent_20261003/public_recovery_verify.json)已通过：异目录9结果文件／43数组精确相同，图包4文件字节相同，0新HP。接续见[粗夹持器0→.001mm平均驱动平衡的新近期计划](NUMPY_FORCE_PROGRESS_20261002.md#native-mean-next-20261003)，截至本条尚未执行该新路径。

2026-10-03最新：**新普通候选的NumPy完整力入口已接通，三例六制造态经64次新HP80/120全量核对通过，3案功能测试通过**。材料/HuHu/总力均满足原门，38400单元/全部DOF覆盖，最大归一化误差8.64e-17；保存模型、原始split状态、三力/应力/J/Hu/能量和全精度参考。见[目标、实施、物理效果和接续](NUMPY_FORCE_PROGRESS_20261002.md#native-force-20261003)、[位移/J/Hu](../functional_views/native_force_20261003/native_force_fields.png)、[三类内力](../functional_views/native_force_20261003/native_force_components.png)。本步为给定位移静态内力，未执行task的.025mm目标；下一普通模型的非对称切线/小步平均驱动平衡，工件/研究H2-H3/一般接触/批量标签仍待完成。

2026-10-03最新先看[显式原生任务／模型实现与恢复](NUMPY_FORCE_PROGRESS_20261002.md#native-model-construction-20261003)：native_project API／CLI、三份明确TEST task、23字段model.json／model.npz和源HF副本、独立核对、五案测试及两图随Git。两粗旧模型intrinsics精确相同；细.5mm保留五节点权重和169fixed。任务绑定四mask几何ID及完整descriptor语义SHA，analysis_grid.policy必须显式native；没有默认全研究政策。输入.025只是保存指令，force／solver未运行。下一步先新文件接口的NumPy静态力与参考，再安排有限路径；原冻结证据与默认内核保持。

以下按执行时点保留早期恢复说明；接续优先使用最新实施记录，不重开关闭窗口。

2026-10-03最新先看[split平均端口功能与恢复命令](NUMPY_FORCE_PROGRESS_20261002.md#split-average-20261003)：显式新入口已接NumPy实际CSC增广系统，两条六单元路径／272项新HP检查通过。模型、split状态、总／增广矩阵、参考、协议与[实际图](../functional_views/split_average_20261003/split_average_demo.png)均随Git。新平均入口尚未接入旧文件dispatcher；下一步用原HF3规范机构小行程，不能将普通实体演示当作机构、接触或批量标签验收。

2026-10-03后续先看[新h=.125 NumPy平衡结果和接续方法](NUMPY_FORCE_PROGRESS_20261002.md#numpy-h0125-path-20261003)。20条实际接受记录／19唯一状态及420项新HP检查通过，完整小输入、模型、两数组状态、总CSC矩阵、精确新参考、源码及20帧动画均随Git，不需旧机盘符或Release恢复即可读取／重绘。最新下一步为split平均端口控制，而非继续自动细化。新路径数值资格不等于一般接触或真实工件夹持资格；以前的关闭窗口仍保持历史身份。

2026-10-03接续先看[NumPy完整静态范围、微小应变修复与实际图](NUMPY_FORCE_PROGRESS_20261002.md#numpy-scope-20261003)：96状态／129方向的774＋774原门全通过，新源码、最小NPZ、结果及图随Git。重画图不需HP大数据；完整参考比较需恢复既有`hf4-c2-development-arithmetic-20260930-v1.zip`，再运行报告中的输入提取器，不能把缺参考的轻量树记作全参考恢复。原25场停止及微小应变诊断保留，不拼接资格。下一步选新的h=0.125 NumPy路径和新态独立核查；旧h=0.0625图示末态HP平衡仍not_pass。

2026-10-02新增[NumPy完整力→组装→解析切线→C1新平衡与独立审计](NUMPY_FORCE_PROGRESS_20261002.md)。新源码、三组小测试、四保存场比较、七方向切线比较、15唯一新状态和完整新HP80/120参考、图与动画均随Git，阅读和复核这些结果不需要旧机盘符或大资产恢复。C1瘦输入的 `run_numpy_c1_force.py --saved-input` 已在另一目录复算，41数组逐位相同。新路径的 `recovery_model.npz` 及源码扩展记录补齐控制/材料输入，原作者summary与后完成audit按时点分别保留。先看本次报告再接续范围；前文F系列仍保持历史结论。

当前主干状态先看 [CURRENT_STATUS](CURRENT_STATUS.md)、[物理与功能进度及可视化](PHYSICS_AND_FUNCTION_PROGRESS_20261001.md)与[主干开发流程](DEVELOPMENT_WORKFLOW.md)。截至2026-10-01，F-SELECT1已按明确批准正常关闭，70个必需事件和4个诊断事件已保留，仅既定前缀完成；[实际结果](F_SELECT1_RESULT_20261001.md)可直接阅读。完整新候选force/AD、一般接触与HF5仍未完成，旧TMC已有内力/切线/平衡能力，默认内核未切换。前次大证据交付见[开发证据移交](DEVELOPMENT_HANDOFF_20260930.md)；原S0、v3/v4、F-STREAM1 partial及[主干整合报告](MAIN_CONSOLIDATION_REPORT_20260927.md)保留历史事实，不相加重叠覆盖。

后续只在本仓库 main 开发，origin 为 `https://github.com/dudaxing/Compliant-TO-TMC.git`。本机正式根为 `D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC`，其中 `hf_repo/` 是源码；外层旧 `Compliant-Nonlinear-TMC-O/hf_repo/` 只保留历史。其他电脑可以选任意克隆目录，不需要原盘符。

本指南覆盖稳定 0.5.0 / HF4-B 与主分支 C0/C1/C2 扩展。[旧项目状态](PROJECT_STATUS.md)、[v3 最终报告](HF4_C2_FINAL_REPORT.md)、[v4 冻结报告](HF4_C2_V4_FREEZE_REPORT.md)保留各自时点事实，不作为最新执行许可。C0 受限参照与 C1 配对任务通过各自门禁；一般接触与项目整体仍未完成。TMC 净合力对账不构成局部单边接触验收，文件恢复与安装检查也不构成新的力学验收。

## 1. 克隆与校验

仓库名称、盘符、父目录均可自行选择；不要创建原机的 `D:\Coding`、用户 Downloads 或 Zotero 目录来满足旧路径。

```text
git clone https://github.com/dudaxing/Compliant-TO-TMC.git my-hf-work
cd my-hf-work
git config core.longpaths true
git switch main
python tools/handoff.py verify
```

本文除明确说明外，命令均从克隆根目录执行。`python` 应指向 Python 3.13；Windows 可先用 `py -3.13` 代替。保留仓库中的相对结构：`hf_repo/` 是独立求解器，`geometry_dataset/` 是普通几何数据，`docs/` 是项目文档，阶段结果各在自己的目录。

S0 后主分支保留说明、395 个几何文件、完整 hf_repo、各阶段摘要和图。详细 C0/C1/C2、HF4 审计/探针及早期原始证据通过版本化 Release 资产按需恢复；原字节和失败状态不变。见 [S0 分层报告](HF4_C2_S0_STORAGE_REPORT.md)。需要全部原始证据时运行：

```text
python tools/handoff.py fetch-evidence
python tools/handoff.py verify --full
```

`fetch-evidence` 按移交清单下载、校验并恢复证据；不要把任意同名 ZIP 当作对应发布附件。先用 `python tools/handoff.py --help` 查看本次移交工具的接口。依赖包并未随仓库或证据附件完整分发，安装还需要可用的 Python 包源或自备、已校验的缓存。

新增2026-09-28至09-30完整冻结根的恢复入口见[最新移交](DEVELOPMENT_HANDOFF_20260930.md)。Windows 的 Git 长路径选项用于克隆；当前移交工具另以 native extended path 恢复/核验深层证据，不需修改系统 LongPathsEnabled。原 `.pyd` 仅作历史身份快照，不复制到新环境加载。

2026-10-01新增F-SELECT1根的31个结果/入口文件随Git，13个`aux`来源复制件由新版本化资产恢复，避免Windows Git保留名拒绝。查看图/74条选择JSON不需下载；完整来源用`python tools/handoff.py fetch-evidence --asset hf4-fselect1-prefix-select-20261001-v1.zip`，再用同资产参数`verify`核对。索引带原reader/native来源依赖；不能把缺13复制件记作完整冻结根已恢复。无需关闭`core.protectNTFS`或修改冻件。

稳定 F 保存输出与 v4 大载荷通过本轮后续证据 Release `hf4-c2-followup-evidence-v1` 接入统一索引；旧报告中的“只存于本机”描述保持其历史时点。只需要这两项时：

```text
python tools/handoff.py fetch-evidence --asset hf4-c2-stable-f-saved-production-arrays-v1.zip --asset hf4-c2-v4-mesh_h00625_v4-payloads-v1.zip
python tools/handoff.py verify --asset hf4-c2-stable-f-saved-production-arrays-v1.zip --asset hf4-c2-v4-mesh_h00625_v4-payloads-v1.zip
```

需独立复制树时，将上面的资产名传给 `prepare-replay --destination <尚不存在的目录> --asset NAME`；可重复 `--asset`。工具恢复索引声明的依赖，准备目录本身不启动 FE 或 HP 审计。本轮上传和空目录恢复结果见[整合报告](MAIN_CONSOLIDATION_REPORT_20260927.md)。

历史文档链接遵循完整工作区相对结构；未下载大证据时，部分深入到原始数组或日志的链接可能尚无本地文件。阶段报告和当前状态可先阅读，不能因附件未下载就把历史“已验收”改记为“未运行”。

## 2. 建立新的独立 Python 环境

当前包要求 `>=3.13,<3.14`，历史验收使用 CPython **3.13.6 / Windows CPU**。不要沿用 LF 虚拟环境，也不要复制原机 `.venv*` 目录。以下为 PowerShell 示例：

```powershell
py -3.13 -m venv .venv-handoff
$hfPython = (Resolve-Path .venv-handoff/Scripts/python.exe).Path
& $hfPython -m pip install --require-hashes -r hf_repo/requirements.lock
& $hfPython -m pip install -r hf_repo/requirements-dev.txt
& $hfPython -m pip install --no-deps --no-build-isolation -e hf_repo
```

Linux/macOS 的对应安装命令为：

```sh
python3.13 -m venv .venv-handoff
.venv-handoff/bin/python -m pip install --require-hashes -r hf_repo/requirements.lock
.venv-handoff/bin/python -m pip install -r hf_repo/requirements-dev.txt
.venv-handoff/bin/python -m pip install --no-deps --no-build-isolation -e hf_repo
```

`requirements.lock` 固定运行依赖及其下载哈希；`requirements-dev.txt` 固定 pytest、构建和资源监控工具。历史交付说明里将开发工具概括为 lock 依赖的一句话应按这里理解。安装开发工具后，`--no-build-isolation` 使用已安装的固定构建后端。此流程不依赖 uv、原机包缓存或 MATLAB。

运行依赖为 NumPy 2.4.6、SciPy 1.17.1、Matplotlib 3.10.9、JAX/jaxlib 0.11.0，其他传递依赖以 lock 为准。若某平台缺少所需发行文件，先记录平台和安装错误；不要静默升级版本后沿用原验收标签。Linux/macOS 的命令写法可移植，不代表这些平台已经完成项目验收。

开发安装使用 `-e hf_repo`，源代码修改会影响后续执行。若要验证普通安装，可把最后一步改成不带 `-e` 的源码安装，或安装经哈希确认的 0.5.0 wheel：

```powershell
& $hfPython -m pip install --no-deps hf_repo/dist/independent_hf_evaluator-0.5.0-py3-none-any.whl
```

该 0.5.0 wheel 已在主分支，不需要 `fetch-evidence` 恢复；稳定标签 `hf-history-0.5.0` 和 wheel 均保持原样。**它不含新增的 C0/C1/C2 研究模块。** 运行实验扩展应使用上述 `-e hf_repo` 源码安装和 `hf_repo/scripts/` 中的新脚本，不能把旧 wheel 称为新扩展的已安装发行包。严格“断开源码”验证还必须新建工作区以外的环境、复制普通输入、安装普通 wheel，并从外部目录运行独立脚本；editable 安装不能用于声称源码已经断开。

## 3. 固定运行设置，保存新机记录

直接使用 Python API 时，必须在首次 JAX 初始化前选 CPU 和 float64。PowerShell：

```powershell
$env:JAX_ENABLE_X64 = 'true'
$env:JAX_PLATFORMS = 'cpu'
$env:OMP_NUM_THREADS = '1'
$env:OPENBLAS_NUM_THREADS = '1'
$env:MKL_NUM_THREADS = '1'
$env:MPLBACKEND = 'Agg'
$env:PYTHONIOENCODING = 'utf-8'
& $hfPython tools/handoff.py inspect --output review_runs/environment.json
& $hfPython tools/handoff.py verify
```

POSIX shell 使用 `export JAX_ENABLE_X64=true JAX_PLATFORMS=cpu OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 MPLBACKEND=Agg PYTHONIOENCODING=utf-8`，后续将 `$hfPython` 换成 `.venv-handoff/bin/python`。`inspect` 保存新机环境及输入检查结果；不要用新环境记录替换历史安装回执。

普通几何独立读取示例：

```powershell
& $hfPython -m hf_eval inspect geometry_dataset/canonical/inverter/geometry.json
& $hfPython -m hf_eval inspect geometry_dataset/canonical/gripper/geometry.json
```

读取成功只证明数据可读和相应文件契约成立。真实几何研究资格、功能表现和接触精度仍按各阶段报告分别判断。

## 4. 开发回归、保存证据复读与历史数值接口

本节从**当前主分支**读取历史 HF4/C0/C1 数据的审计、重绘与预载示例，均以前面 `python tools/handoff.py fetch-evidence` 和 `python tools/handoff.py verify --full` 成功为数据前置；轻量克隆本身不含这些原始文件。只做相关阶段时，也可按下表恢复并核验对应资产。C2 使用后面的独立 `prepare-replay` 示例。恢复数据不等于启动新 FE 的准入；下述求解命令保留历史复验接口说明，当前仍停止新 FE。

| 当前主分支的数据用途 | `fetch-evidence --asset NAME` 后以 `verify --asset NAME` 核验 |
|---|---|
| HF4 新旧结果重绘 | 分别恢复 `hf4-c2-s0-historical_repair_details-v1.zip`、`hf4-c2-s0-historical_hf4_details-v1.zip` |
| C0 保存态审计 | `hf4-c2-s0-c0_runs-v1.zip` |
| C1 保存态审计与预载数据 | `hf4-c2-s0-c1_runs-v1.zip` |

以上命令均接在 `python tools/handoff.py` 之后；每个资产分别执行一次。单元测试和普通几何读取不需要恢复这些大资产。另行检出稳定标签时，以该标签自己的历史布局和证据清单为准。

先保留新环境记录，再按改动范围选择测试；输出使用新的命名。下面是普通回归范围，假设 `review_runs/regression_001.xml` 尚不存在：

```powershell
Push-Location hf_repo
& $hfPython -m pytest -q --ignore=tests/test_windows_owned_process.py --ignore=tests/test_windows_owned_cpu.py --ignore=tests/test_windows_cleanup_contract.py --ignore=tests/test_s0_event_logging.py --junitxml=../review_runs/regression_001.xml
Pop-Location
```

上面排除的四个实验监督/日志测试依赖原执行卡身份与 deadline；它们随源码及原回执保留，不应为运行通用测试伪造已关闭卡的环境或重开旧窗口。其他新增研究测试也须根据本次计算范围、来源及预算选择。文件交付验证可独立运行 `python -m unittest discover -s tools -p "test_*.py"`，不执行 FE。

移交基线历史测试为一次 **592 通过、1 跳过**，另一次 **12 通过**，合计 604 个唯一通过项。新机完整执行是新的测试记录，实际通过/跳过数量应以本次输出为准。原跳过为 Windows 符号链接权限；不同平台可能不再跳过。历史 xunit2/record_property 警告及实际保留的属性已在修正报告说明。

如需在新机严格重做原 HF4-B，应先在独立目录检出 `hf-history-0.5.0`，按该目录建立环境；当前主分支还包含后续阶段新增源码，其源文件清单不同于旧冻结。先确定本次时间、内存和停止预算，串行执行，并选没有使用过的输出目录。以下命令从该稳定标签目录执行，是原第四组合的完整路径及其独立审计；这里选 `review_runs/g1_m1_001`，已存在时应换一个新名字：

```powershell
& $hfPython hf_repo/scripts/run_hf4_split_normal.py --spec hf_repo/configs/hf4/validation_spec.json --gamma-index 1 --mesh-index 1 --output review_runs/g1_m1_001
& $hfPython hf_repo/scripts/audit_hf4_split_normal.py --spec hf_repo/configs/hf4/validation_spec.json --run review_runs/g1_m1_001 --output review_runs/g1_m1_001_audit --source-freeze hf4_repair_results/source_release_001/source_freeze.json
```

生产运行成功后才可把后续审计称为完整成功路径验收；运行失败时保留失败目录及原始状态，按失败证据分析。HP 审计可检查已保存接受态，但不能把部分接受态通过改写成原目标全部完成。

上述 source freeze 只用于**未经修改的 0.5.0 生产源码**。开始修改代码时另建本次源码冻结、执行计划和结果目录；不得修改旧 freeze 来使新代码与旧证据“匹配”。其余三组索引为 `(0,0)`、`(0,1)`、`(1,0)`。每组都应保存原目标、子步、失败增量、反力/间隙、独立 HP 及参考误差。修改 `--gamma-index` 或 `--mesh-index` 时同时修改输出名称，不并发占用既定数值预算。

查看历史图不需要重算。需要重绘已归档新旧 HF4 比较时，可运行：

```powershell
& $hfPython hf_repo/scripts/plot_hf4_split_comparison.py --new-root hf4_repair_results --old-root hf4_results --output review_runs/comparison_plots_001
```

该命令绘制已保存的发布证据；它不会自动用 `review_runs/g1_m1_001` 替换其中某条曲线。新的四组比较应另建完整输入组织和对应来源清单。

### HF4-C0 保存证据复核与历史求解接口

以下从当前主分支根目录、使用源码环境执行，先测试和复核已保存证据，再按需要进行新计算。每个输出必须使用未存在的路径：

```powershell
& $hfPython -m pytest hf_repo/tests/test_contact_audit.py hf_repo/tests/test_contact_reference_a0.py hf_repo/tests/test_contact_reference_a0_audit.py -q
& $hfPython hf_repo/scripts/audit_contact_geometry_rational.py --output review_runs/geometry_audit_001.json
& $hfPython hf_repo/scripts/audit_contact_reference_a0.py --run research_integration_20260920/results/a0_h025_a000_r1 --output review_runs/a0_saved_state_audit_001.json
& $hfPython hf_repo/scripts/run_contact_reference_a0_isolated.py --mode solve --run review_runs/a0_h025_a000_001 --h 0.25 --amplitude 0
& $hfPython hf_repo/scripts/run_contact_reference_a0_isolated.py --mode audit --run review_runs/a0_h025_a000_001
```

冻结协议是 [contact_reference_a0_v1.json](../hf_repo/configs/contact_reference_a0_v1.json)。顺序为粗均匀独立验收、细均匀独立验收，再运行四个非均匀组合；沿用该轮明确预算，任一依赖门失败即停止后续组合。HP 审计会核对存储哈希链、每个原目标与全部插入态，以及当前源码身份。首次配置失败、6 条正式路径和 30 个接受态原件均保留，不覆盖旧输出。

该历史 C0 比较的两网格差包含 Q1 边界插值差（离散平均 `1−a·h²/2`），不是单独的内部离散误差；`kr=0` 下 Hu 非零不证明 HuHu 正则项通过。研究来源和限制见[完整报告](HF4_C0_RESEARCH_INTEGRATION.md)。

### HF4-C1 保存证据的独立读回入口

当前选定的 10 条 C1 路径有 80 个状态（均匀 50、非均匀 30），80/120 位独立 HP 与几何门禁全部通过，选定范围共 2516 项独立检查；相关测试 173 项通过。另保留旧激活失败 run 的四态有效前缀，该 run 不通过。含前缀的历史统计为 84 态、2644 项检查，包含上述选定范围，不能重复相加。比较按[selection_v1.json](../hf4_c1_results/selection_v1.json)去重；阶段起点、原目标和插入态仍按存盘身份分别保存。

先读[物理协议](HF4_C1_PROTOCOL.md)、[激活修正](HF4_C1_ACTIVATION_REPAIR.md)与[精度补充说明](HF4_C1_PRECISION_AUDIT.md)。以下命令只读回已保存状态，并将新审计写到原证据目录以外的独立输出名；请先自行创建 `review_runs/` 目录，不要覆盖任何既有审计：

```powershell
& $hfPython hf_repo/scripts/audit_contact_c1.py --run hf4_c1_results/A0_h025_uniform_r2 --output review_runs/c1_a0_h025_readback_001.json --precision-amendment hf_repo/configs/contact_c1_precision_r2.json
```

`review_runs/` 是新建的本地复核目录，不属于发布原证据。也可以从任意其他 cwd 执行上述脚本，此时对脚本、run、output 和精度补充协议均使用本机实际绝对路径；无需重建历史盘符。审计会核对当前存盘状态、完整原目标、两数组继承、模型/代码哈希与相对来源链，不能只看顶层 `status`。

必须显式传入 [contact_c1_precision_r2.json](../hf_repo/configs/contact_c1_precision_r2.json)，才是 C1 精度补充采用的 80/120 位交叉核对；80 位仍为读出量权威，原物理协议和全部误差门槛保持不变。省略此参数仍走原 50/80 位合同，用于复现历史近零分量精度失败，**不能将默认命令当作最新验收入口**。原失败审计及其日志继续保留。

### 历史 C1 路径重放接口（非本轮执行计划）

以下仅记录历史接口与当时预算；不表示当前获准启动新 C1 路径。该历史求解使用 `run_contact_c1_r2_isolated.py --action solve`；独立审计使用另一个外壳 `audit_contact_c1_isolated.py` 并显式传精度补充。未来若另行准入新复验，须建立独立目录、预算和选定路径清单。原合同的单路径求解外部上限 700 秒、单阶段内部上限 300 秒、单路径独立审计外部上限 1200 秒；最多 10 条选定路径，累计求解预算 7000 秒。失败尝试也记录耗时，不删除旧回执来重置预算。

粗网格 A0 的第一组示例：

```powershell
& $hfPython hf_repo/scripts/run_contact_c1_r2_isolated.py --action solve --run review_runs/c1_replay_001/A0_h025_uniform_r2 --kind A0 --h 0.25 --mode uniform
& $hfPython hf_repo/scripts/audit_contact_c1_isolated.py --run review_runs/c1_replay_001/A0_h025_uniform_r2 --precision-amendment hf_repo/configs/contact_c1_precision_r2.json
```

按同一合同分别完成 A0/TMC、`h=0.25/0.125` 的四条均匀路径，且四者完整独立审计均通过并保存 admission 决定后，才能运行 A0/Aalpha/TMC 两网格的六条扰动路径。下例仅在该四路径门已满足后执行：

```powershell
& $hfPython hf_repo/scripts/run_contact_c1_r2_isolated.py --action solve --run review_runs/c1_replay_001/A0_h025_perturbation_r2 --kind A0 --h 0.25 --mode perturbation --preload-run review_runs/c1_replay_001/A0_h025_uniform_r2
& $hfPython hf_repo/scripts/audit_contact_c1_isolated.py --run review_runs/c1_replay_001/A0_h025_perturbation_r2 --precision-amendment hf_repo/configs/contact_c1_precision_r2.json
```

A0 与 Aalpha 使用对应网格的 A0 均匀预载，TMC 使用对应 TMC 预载；Aalpha 是跨模型 warm start，继承的零幅态必须重新平衡并独立验收。局部阶段参数不总是物理总位移：闭合阶段是 0.25 mm 间隙之后的附加压缩，扰动阶段是固定 0.375 mm 预载上的零均值幅值。保持这一区别，不能直接按不同阶段的同名 `d` 比较力。

源预载必须保留匹配的 `audit.json` 和完整来源链；新审计外壳默认使用这个名称并拒绝覆盖。已有输出应换新 run 或显式使用新的 `--output-name` 保存诊断，不能改写历史结果来通过门禁。全路径、失败前缀、几何、数值及物理资格分别判断，依赖门失败即停止后续组合。

### 冻结 HF4-C2 v3 证据的独立读回入口

**本小节仅复读历史 v3：v3 C2 仅部分通过，v3 细网格路径仍为未通过。** 后来的 v4 单独补测已通过，见[v4 报告](HF4_C2_V4_RETEST_REPORT.md)，不覆盖这里的原失败。 三次新 FE 尝试均求解至 `d=0.5 mm`，其中 padding 的 19 态/589 项检查和 outer-free 的 19 态/570 项检查完整通过。细网格路径为 `NOT_PASS`：末态 `production_vs_hp80_total_force = 1.0943792164e-11 > 1e-11`；21 态中 20 态通过，651 项检查中 650 项通过，有效前缀止于 `d=0.4375 mm`，覆盖 6/7 原目标。三次尝试合计 59 态/58 态通过，1810 项检查/1809 项通过，包含上述子范围，不能重复相加。求解到达末目标不等于独立验收通过。

在 v3 收尾时停止了后续 FE；当时固定失败保存场的主差定位到强压缩背景单元的 F 浮点求和。原生产总力位级复现；保留生产 F、只提高本构/装配精度，误差仍约 `1.09438e-11`，而精确 split F 正确舍入为 binary64 后，诊断路径的误差约 `6.28152e-16`。这一历史分段诊断本身没有部署新 kernel、验证新一致切线或完成新路径；之后的候选与 v4 另有报告，原 v3 细网格仍为 `not_pass`。保留失败末态、原审计及外部回执，不调松门槛或覆盖旧失败。执行前 103 项测试与 17 项汇总回归分别通过，不把早期 62/94 项预检重复相加。证据见[C2 最终报告](HF4_C2_FINAL_REPORT.md)、[分段精度诊断](../hf4_c2_diagnostics/force_precision_001/summary.json)与[C2 证据入口](../hf4_c2_diagnostics/README.md)。

两条已通过新边界路径另有 206 项保存场检查和 22 项解析边积分检查通过。外底边自由场只有 44/48 条顶边满足整边材料压缩条件，远端出现保存场材料名义拉应力；不能把原四态的 144/144 全压缩推广到此任务，也不能把该名义应力直接解释为已验证真实接触压力。

[独立最终复核](../hf4_c2_diagnostics/independent_final_review.json)核对 420 个来源文件、93 个存盘状态（59 新增、34 基线）、71,000 个单元和 558 次分项重算，结论为证据完整性 `pass`、力学状态 `partial`。它重用保存的 HP 本构结果，不能代替新实现的完整力与一致切线验收，也没有取消细网格唯一失败。稳定 0.5.0 标签及 wheel 不变。

另保留了历史汇总清单的自引用缺陷，见[存储清单补充](../hf4_c2_diagnostics/summary_manifest_amendment_001/amendment.json)及[独立补充复核](../hf4_c2_diagnostics/summary_manifest_review.json)；科学数值和原文件未改。后续生成使用 [summarize_contact_c2_r2.py](../hf_repo/scripts/summarize_contact_c2_r2.py)，其 2 项存储测试与 103 项预检、17 项汇总测试分别计数。 该汇总脚本、原固定场精度诊断及原最终复核仍沿用完整历史来源链，缺少两份外部源码时不能在公开副本直接重跑；已保存结果可以读取，新公开数值入口只解决保存态重审，详见下述范围说明。

本小节历史执行协议为 [contact_c2_v3.json](../hf_repo/configs/contact_c2_v3.json)。v1/v2 都未执行新 FE，保留其配置、预检和修订说明；不要将 v2 的 `pre_execution_review.json` 当作最终执行准入。v3 的三条路径依次是 `padding_2p5`、`outer_free`、`mesh_h00625`。各路径既要满足求解/独立审计全部门禁，也要有未超时且退出码为 0 的外部回执以及完整来源、详情哈希链。

**公开数值读回与完整历史来源核验是两个入口。** 搬迁实测表明，原 `audit_contact_c2.py` 的 v3 admission 哈希链要求两份按既定出版范围排除的 MATLAB 编号源码；它们没有包含在主分支或 Release。缺少原件时，该完整审计会在 HP 求值前失败，历史源码不能伪造、静默跳过或被称为已核验。新机先用新增 [audit_contact_c2_readback.py](../hf_repo/scripts/audit_contact_c2_readback.py) 对公开数值证据复读。它限定那两条路径及精确 SHA，仍逐项核对其余 164 个 admission 输入和 33 个冻结实现，以及所有数值/控制器记录；如果外部来源存在但字节不匹配，同样失败。结果使用独立 schema 和 `numerical_pass` / `numerical_not_pass`，不替代完整来源资格，也不能传入继续执行门。详情、首次失败和新读回证据见[搬迁审计补充说明](HF4_C2_PORTABILITY_ADDENDUM.md)。 本机实际验证已复读上述两条路径共 40 个状态，科学详情 JSON 和 SHA 与原件全部一致；padding 保持通过，细网格保留唯一末态失败。新增入口有 21 项针对性测试记录，比较器有 12 项对照与反例检查，均不计作新的 FE 路径或原数值门禁。

C2 审计采用 80/120 位，80 位为测量权威，协议固定原物理参数与容差。它会在输入 run 内创建 `<output-stem>_states/`（标准 `audit.json` 对应 `audit_states/`）。**即使 `--output` 指向外部目录，也会向 run 写入详情；必须先建立独立复制树，不能直接在冻结原证据上复读。** 保留复制树内 `hf_repo/`、`hf4_c1_results/`、`hf4_c2_diagnostics/` 和 `docs/` 的相对关系，C2 来源门依赖已保存 C1 证据。

以下 PowerShell 示例从轻量克隆根建立一个尚不存在的同级复读树，并自动恢复 C2 及其 C1 来源依赖，再从副本之外的 cwd 读取第一条保存路径。`$hfPython` 使用前面已配置的环境；命令只独立核对存盘状态，不启动生产 FE：

```powershell
$originalRoot = (Get-Location).Path
$readbackRoot = Join-Path (Split-Path $originalRoot -Parent) 'hf-c2-readback-001'
& $hfPython tools/handoff.py prepare-replay --destination $readbackRoot --asset hf4-c2-s0-c2_runs-v1.zip
Push-Location (Split-Path $readbackRoot -Parent)
& $hfPython (Join-Path $readbackRoot 'tools/handoff.py') verify --asset hf4-c2-s0-c2_runs-v1.zip
& $hfPython (Join-Path $readbackRoot 'hf_repo/scripts/audit_contact_c2_readback.py') --run (Join-Path $readbackRoot 'hf4_c2_diagnostics/experiments/padding_2p5') --output (Join-Path $readbackRoot 'review_runs/c2_padding_readback_001.json') --protocol (Join-Path $readbackRoot 'hf_repo/configs/contact_c2_v3.json')
Pop-Location
```

副本、输出名和逐态详情目录均不得已经存在。公开数值入口的数值通过可返回退出码 0，但顶层状态为 `numerical_pass`；细网格应继续为 `numerical_not_pass` 并返回非零，不能当作意外中断重跑。重新审计后分别检查数值状态、历史来源未复核列表、完整目标库存、每态检查及 `input_and_helper_sha256` / `detail_output_sha256`，并与原审计逐字段比较。每态科学详情应保持相同字节；顶层 schema、范围、两项未验证来源和新增读回脚本绑定属于有意差异，时间、显示根目录与新输出路径单独记录。仅相同 `status` 不足以证明完整读回。为新机记录自己的环境和外部时间预算；同一 Windows 主机上的异目录复读只证明该环境下的搬迁/来源链可用，不是跨平台数值验收。

**读回 v3 的失败不应触发自动重跑 FE，也不能通过清理回执重置预算。** 原 v3 wrapper 和直接 runner 保留历史身份；P1 已另行实现并验收，稳定 F 候选与 v4 补测也已完成其记录范围，不能继续照抄旧的“P1 尚未实现”待办。当前仍存在三个制造场失败，默认内核未切换；v4 的一次求解与一次审计额度已使用。新的路径必须另有明确协议、预算与准入，公开 v3 数值读回不能授予这些资格。

历史 v3 预算为每条求解外部上限 700 秒、三条累计 2100 秒；每条独立审计最多 1200 秒、累计 3600 秒。它们只是历史合同，不自动成为新计划预算。任何失败、超时、来源变化或不完整目标应按本次预先定义的停止条件记录，不删除旧失败。稳定 0.5.0 wheel 不含 C2，应使用主分支源码环境阅读或开发扩展。

### v4 与稳定 F 的当前读取范围

先恢复本节开头列出的两项后续资产，再核对对应逐态结果、来源清单与[独立复核对照](HF4_C2_INDEPENDENT_RECONCILIATION_20260927.md)。资产无损恢复不会执行 FE，也不会重新计算 HP；如需重新数值审计，须在独立树中明确当前脚本/协议的来源要求和外部预算。v4 已有一次审计回执，不能覆盖、删除或用换名规避其单路径守卫。

公开 v3 读回的两项 MATLAB 来源例外不自动适用于其他工具。稳定 F 历史复算还使用明确的基线 `7fea2e4`；按[验证目录说明](../hf4_c2_stable_f_validation/README.md)建立独立基线并恢复 C1/C2 资产，不能用后来更新的仓库清单伪装旧基线。冻结运行自身的来源快照优先于后来变动的活动脚本。 完整恢复当前 main 只用于读取、文件身份校验和当前回归，不自动满足历史 stable-F driver 对 S0 提交、manifest 和资产索引的锁定；重跑历史 driver 必须使用其原冻结 S0/source-snapshot，不得改锁定哈希以适配 main。本轮整合不重跑该历史 driver。

## 5. 哪些路径及脚本只表示历史

| 对象 | 接续时的处理 |
|---|---|
| `D:/Coding/...`、`C:/Users/Lenovo/...`、原机临时目录 | 是原运行来源、日志或访问阻断记录；不要求新机存在，不应全局替换历史文件。 |
| `hf4_repair_results/prepare_detached.py` | 固定原 Windows Python、虚拟环境和 uv 离线缓存；保留作历史流程，不直接作为新机 bootstrap。 |
| `hf4_repair_results/run_remaining.py` | 固定旧 `.venv-hf2-repair/Scripts/python.exe`；使用新环境和明确的新输出入口。 |
| `hf4_repair_results/run_budgeted.py` | 读取历史已用预算，且禁止同 `_path` 分类二次启动。不要删除旧回执重置预算；新复验必须有自己的预算与监控记录。 |
| 既有 HP 审计 `bindings.json` | 键包含历史绝对路径。搬迁后不能直接 resume 旧审计输出；在新目录建立新的 bindings 和审计。 |
| `finalize_stage.py` | 会生成汇总时间戳；历史复核需在审查副本进行，不把发布根目录当临时输出区。 |
| 旧 `*_CONTENT_MANIFEST.json`、旧 ZIP | 绑定各自发布快照；移交仓库的新增文档与布局由移交清单负责。不要修改旧清单或误称其覆盖当前全部文件。 |
| MATLAB、LF 来源验证器 | 属于资料核查/开发参考；复跑需要另行准备其明确依赖，生产 HF 不导入它们。 |

保留 `.gitattributes` 的字节保持规则，避免 Git 的 CRLF 自动转换破坏源码和证据 SHA。不要把“修正路径”做成批量重写 JSON、日志、冻结文档或原始状态。

跨电脑复用文件和环境不保证跨 CPU、操作系统或编译后端逐位相同。历史 73 项独立安装检查证明其记录环境中 A–B–A 与保存权威数组一致。新机器若逐位比较不同，应记录差异并用独立 HP、原物理门槛和明确的新运行条件判断；不能修改阈值来沿用旧 PASS。

## 6. 恢复开发时的首项工作

先按 [CURRENT_STATUS](CURRENT_STATUS.md)确认现状与本次范围。固定场分段诊断、算术候选、JIT/AD修订及F系列都已实施并保留失败，详见[连续执行报告](HF4_C2_S0_PREPARATION_RESULT_20260928.md)。F-SELECT1已完成定向提取，可直接读74条小JSON，[结果](F_SELECT1_RESULT_20261001.md)明确56条身份与旧规则差距；不再把“读取旧128样本”作为待办或重跑已关闭卡。完整EOF/CRC/JSON与内部成本归因仍未取得。

当前优先功能步骤是新候选清晰的NumPy完整力入口：先给原unit近旋转场的八自由度材料/正则/总力，与已保存HP80/120原门参考比较并画力及误差；根据实际结果再接一个C1保存态全局组装、切线和小平衡路径，见[功能进度末节](PHYSICS_AND_FUNCTION_PROGRESS_20261001.md#可视化与最近一个功能步骤)。本轮C1十五态图和GIF是历史数组重绘，新克隆可直接查看；重绘源码带`--model/--result/--audit/--output`四参数，在任意目录显式提供相对恢复来源即可，不需原绝对工作目录。没有重新求解。Profiler是运行成本辅助，不是每个功能步骤的永久前置门。

原实验 runner 保留原机 Python、运行库 pins、路径及冻结身份。异机恢复证据不等于可以直接复跑旧卡；不要修改旧脚本/manifest 以适配新盘符。先恢复相对证据树并核 SHA；重新计算、读取 native gzip 或采集 profiler 须另定新环境、身份、预算与停止合同。原材料力、正则力、总力、导数及 native 接受门保持，不切换默认内核、不自动进入 HF5。缺少出版范围内排除的外部来源时，明确未核验范围，不伪造原件。

后续真实接触资格仍需围绕明确任务核查部分接触、释放/重入、模型与网格敏感性。负弱节点项不是已验证的负接触压力，材料名义应力也不是已经验证的真实接触压力；Aalpha 仅作诊断，TMC−Aalpha 不是纯接触误差。不要同时调整 alpha/gamma 追求净力吻合，也不能以三网格观察替代收敛证明。

后续开发统一在 main，流程见 [DEVELOPMENT_WORKFLOW](DEVELOPMENT_WORKFLOW.md)。每次继续记录总体目标、要做与已做、理由、效果、局限、代码/输入/输出哈希和资源成本；保留失败和修正因果链。HF5、LF 优化、1800 例 HF 标签与最终排名仍未实施，不因本次仓库整合自动开始。


</details>


</details>


</details>


</details>


</details>


</details>
