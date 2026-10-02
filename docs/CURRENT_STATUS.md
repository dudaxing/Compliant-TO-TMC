# 当前目标与状态

2026-10-02用户授权优先实现新候选NumPy完整力并按结果推进。**已完成完整力、全局组装、解析机械切线、C1从零接近与压紧，以及新实际状态的独立HP80/120审计。** 三近旋转场及C1保存末态三力门全过；七保存方向21项切线门全过；18项小测试通过。新路径覆盖七原目标，16接受记录／15唯一状态，336项新态独立检查全部通过。末态d=0.5 mm，完整顶边法向力71.42390219811888 N，最小J约1.89801e-5。详见[目标、实现理由、实际效果与边界](NUMPY_FORCE_PROGRESS_20261002.md)、[新路径图](../functional_views/numpy_c1_20261002/numpy_path.png)与[16帧实际动画](../functional_views/numpy_c1_20261002/numpy_path.gif)。

当前可显式选用NumPy力/切线并接入已有split仿射位移控制；省略assembler仍用原入口。新路径只通过该固定合成压缩任务的数值门，完整近旋转候选矩阵、compiled force/AD、一般接触释放重入、split平均端口、真实工件夹持及HF5仍需后续实施。下一步优先复用NumPy功能检查原完整制造/保存态范围，再按结果推进细网格与机构任务；旧F系列失败和额度不回写。

2026-10-01 用户明确批准F-SELECT1，并要求功能优先、逐步推进、记录并展示物理效果。**F-SELECT1唯一300秒/4GiB窗口已正常完成关闭**：实际总钟151.7630085秒，16组27个新控制通过，70个必需事件与4个诊断事件完整保存，既定解析/返回端点及双前缀SHA通过，三个原SUP1清理通过。仅既定前缀完成；全流、完整新候选force/AD及HF5仍未通过，详见[实际结果](F_SELECT1_RESULT_20261001.md)。

当前功能主线见[物理与功能进度](PHYSICS_AND_FUNCTION_PROGRESS_20261001.md)：旧TMC已有内力、切线与平衡能力；缺口是近旋转新候选完整力/AD、split平均端口、一般接触释放重入、真实工件夹持及HF5批量评价。已从15个历史C1保存态生成[实际变形/反力/力—位移/间隙图](../functional_views/c1_baseline_20261001/saved_mechanics.png)和[压缩动画](../functional_views/c1_baseline_20261001/compression.gif)，并链接两例真实机构的HF3变形/路径图；未新增物理覆盖。下一步优先新候选NumPy完整力入口与原门参考比较，再按结果推进C1组装、切线和平衡；profiler为辅助，不能变成全部功能工作的永久前置门。

2026-09-30提交推送与18根冻结证据公开恢复记录见[本次开发移交](DEVELOPMENT_HANDOFF_20260930.md)。其后的[只读排查](F_STREAM1_READONLY_FOLLOWUP_20260930.md)保留候选卡提出时“未执行”身份；用户随后明确批准并已完成F-SELECT1，不再等待该卡批准。

本轮main图/结果交付与[F-SELECT1资产](https://github.com/dudaxing/Compliant-TO-TMC/releases/tag/hf4-fselect1-evidence-20261001-v1)公开恢复已验证：31结果文件随Git，13个Windows Git拒绝的AUX来源从完整44件小资产恢复；异目录克隆与十资产依赖闭包通过，首次网络发布失败保留。见[本轮交付关账](F_SELECT1_RESULT_20261001.md#关闭后核对与交付)。

**历史目标工具关账读回状态：blocked（2026-09-30），F-STREAM1唯一窗口、三路后审、实际审图及记录已完成关闭；全流普查未通过。** 用户“批准”的300秒／4GiB卡已使用，exit1／execution_failure／partial。16组82子例通过，原gzip一次读取触4,000,000事件界后关闭；真实总钟143.272178秒、采样峰86.425781MiB，三阶段原SUP1清理通过，无续读／修复／重试。完整force／AD／接触／HF5及项目目标仍未完成。详见[本轮实际结果](HF4_C2_S0_PREPARATION_RESULT_20260928.md#f-stream1实际执行结果2026-09-30)。

关账状态补记：作者期本批准turn的两次工具读回为active，最后关账get_goal返回blocked且未附原因。解析后审agent确认未操作goal；root本次未调用update_goal或pause／complete。以最后真实读回为准，不推定状态变化原因，也不把已完成F-STREAM1重新解释为待批准。作者历史active保持，完整项目未完成；本卡已授权工作全部关闭。


**最新F-BYTES1已执行、三路独立后审并关闭：现有gzip正文超过原256MiB上限。** 用户2026-09-30“批准”的唯一60秒／4GiB窗口已使用，exit 0／`saved_gzip_volume_diagnostic_complete`，真实结果为`body_over_cap`。五组控制、12步骤及341事件闭合；只打开原gzip一次，294次有界读取累计268,435,457 bytes（256MiB＋1）后立即关闭。正文精确大小／完整SHA为null，EOF／正文CRC＋ISIZE未验证，未解析JSON或XPlane。终端总钟5.882316秒，采样进程树RSS峰值73,805,824 bytes（70.386719 MiB）；三阶段原SUP1正常退出及清理通过，无修复／重试。详见[实际结果与边界](HF4_C2_S0_PREPARATION_RESULT_20260928.md#f-bytes1实际执行结果2026-09-30)、[回执](../hf4_c2_stable_f_validation/native_volume_001/execution_receipt.json)、[最终绑定](../hf4_c2_stable_f_validation/native_volume_001/receipt_binding.json)、[体积图](../hf4_c2_stable_f_validation/native_volume_001/volume.svg)及[封存前资源图](../hf4_c2_stable_f_validation/native_volume_001/resources.svg)。

关闭后来源／封存、监督／预算、计数／图表三路只读后审均通过：18输入角色（16复制＋2原件引用）、43 payload、31非空绑定及恰六排除一致；原八件112,731,618 bytes及F-TRACE2绑定保持原SHA。新单helper保持64,216 bytes／SHA b209a80111b18c42c60c16c859c6d8b999f27f512f7c7ab578ef5beadc8122c3，后审完成后才更新本页与原报告，冻结的作者文档不回写。两SVG已实际渲染审图、显示清晰且源SHA保持。`scientific_admission / force_executed / runtime_native_trace_observed / native_json_parsed / xplane_decoded`全部false；诊断完成不改变F-TRACE2原接受门失败。

**最新[F-STREAM1](HF4_C2_S0_PREPARATION_RESULT_20260928.md#f-stream1实际执行结果2026-09-30)取得可信的部分数组前缀，未取得完整EOF／CRC／JSON或内部归因。** 496次有界read返回453,720,232 bytes，旧268,435,457-byte前缀SHA同流交叉检查通过；接纳4,000,000事件（X3,999,991／M9），第4,000,001单元已frame及strict decode但按事件界拒收。framer位置453,449,107，最后接纳事件end453,448,982，未消费后缀271,125 bytes；精确正文／完整SHA未知。仅保存128数组前缀样本、遗漏3,999,872；五应用名各一次，原精确名称／generic+direct候选均0，任意名称下direct module参数56次，均不能授予原归因门或断言全流缺失。详见[计数](../hf4_c2_stable_f_validation/native_stream_001/results/stream/count.json)、[统计](../hf4_c2_stable_f_validation/native_stream_001/results/stream/census.json)、[最终绑定](../hf4_c2_stable_f_validation/native_stream_001/receipt_binding.json)及[普查图](../hf4_c2_stable_f_validation/native_stream_001/census.svg)。


F-STREAM1的P0／P1／P3耗时6.632416／131.562011／3.175371秒；12步骤11过1失败，92事件。ledger／receipt仅elapsed/shared两个写时点不同，分别142.798676／142.931411秒，binding前143.124955秒，终端143.272178秒；不能伪称同字节或混成同一快照。P3仅封存partial，EOF／CRC／全文及saved_gzip_stream_census_complete未授予；五科学／native／force／XPlane资格false。两live在三后审前仍等于作者冻结快照，随后更新本页与原报告，冻结根未改。[资源图](../hf4_c2_stable_f_validation/native_stream_001/resources.svg)仅preseal P0／P1；异机恢复还须micro_trace_002两原native文件。本轮交付状态见开发移交验收记录。

**前轮F-TRACE2已执行、三路独立核验并关闭：原数值门通过，native单件容量门未通过。** 用户2026-09-30“F-TRACE2 明确批准”的唯一180秒／8GiB窗口已使用，exit 1／`observability_not_pass`，无修复／重试。终端74.275337秒，receipt写前快照74.247847秒，绑定前74.272022秒，采样进程树RSS峰值2,670,940,160 bytes（2.4875069 GiB）。16控制组、两次原24叶比较通过，一次start／body／stop均返回；普通路径导出JSON.gz 24,572,396 bytes及XPlane 87,819,545 bytes，总112,391,941 bytes。XPlane超过原64MiB单件接受门，native.collect首错停止，JSON未解码、内部事件及成本未归因；不是API错误或资源不足。详见[实际结果与边界](HF4_C2_S0_PREPARATION_RESULT_20260928.md#f-trace2实际执行结果2026-09-30)、[回执](../hf4_c2_stable_f_validation/micro_trace_002/execution_receipt.json)、[最终绑定](../hf4_c2_stable_f_validation/micro_trace_002/receipt_binding.json)、[阶段图](../hf4_c2_stable_f_validation/micro_trace_002/stages.svg)、[封存前资源图](../hf4_c2_stable_f_validation/micro_trace_002/resources.svg)及[分层覆盖图](../hf4_c2_stable_f_validation/micro_trace_002/coverage.svg)。

关闭后三路只读后审通过：105输入／8,497,004 bytes、149 payload／126,437,904 bytes、43绑定（42实件＋1真实未到达native_analysis null）、原SUP2三同实例终止／句柄释放及六排除闭合。实际29步骤（28通过）、78事件、9常规artifact，不补成31／84／10；completed_counts与总体compiler_options_execution未形成，实际trace／compile步骤已记录原严格两选项false。两sync 14.530080／15.429572秒，同一完整ready树再等待91.2µs；CPU内部覆盖各不足30秒，三窗按原门inconclusive。44个ENTRY producer／26个fusion observations全null。原件和三稿保持，冻结的两作者文档保持原SHA；只在三路后审后更新本页与原报告。

2026-09-30另完成三SVG的实际渲染审图，文字、数值、灰色unknown及短柱显示无截断；源SVG SHA与已封存output清单相同。独立文字复核发现两个图注口径需说明，已在[关闭后图表复核](HF4_C2_S0_PREPARATION_RESULT_20260928.md#f-trace2关闭后图表复核2026-09-30)记录：profiler.start为包装wall；资源图的receipt是绑定前快照，最终绑定时点由receipt_binding独立记录。冻结图、回执及结论保持。

**前轮F-PATH1已执行、独立核验并关闭：普通Windows绝对路径的native导出接口通过。** 用户2026-09-30“批准”的唯一90秒／8GiB窗口已使用，exit 0／`native_path_interface_pass`；终端总钟16.048155秒，receipt快照15.954078秒，绑定前16.045299秒，采样进程树RSS峰值168,353,792 bytes（0.156791687 GiB）。12项控制、一次start／标准库标记体／stop全部通过；唯一session导出JSON.gz及XPlane各一件，总107,363 bytes，唯一应用标记完整。三个阶段正常退出并清理；没有数组、微图、force或AD调用，没有修复／重试。详见[实际结果与边界](HF4_C2_S0_PREPARATION_RESULT_20260928.md#f-path1实际执行结果2026-09-30)、[回执](../hf4_c2_stable_f_validation/native_path_001/execution_receipt.json)、[最终绑定](../hf4_c2_stable_f_validation/native_path_001/receipt_binding.json)、[阶段摘要](../hf4_c2_stable_f_validation/native_path_001/stages.svg)、[封存前资源摘要](../hf4_c2_stable_f_validation/native_path_001/resources.svg)及[接口覆盖](../hf4_c2_stable_f_validation/native_path_001/coverage.svg)。

三路关闭后只读后审通过：44输入／2,661,245 bytes、78 payload／2,953,468 bytes、33非空绑定及原SUP2三个同实例终止／句柄释放全部闭合；全根84件，恰六声明排除。新单辅助live／冻结保持63,144 bytes及既定SHA；旧科学／测试／监督／辅助字节保持。两live文档在后审前与作者快照相同，随后只更新本页和原报告，冻结文档不回写。native API目录131字符、两实际文件路径197／193字符，原件及有界JSON读取通过；这只证明固定本机的一次路径接口，不唯一确定旧扩展路径失败根因。`scientific_admission=false / force_executed=false / runtime_native_trace_observed=false`；没有微图内部事件、fusion成本或完整force资格。

**前轮F-TRACE1已执行并关闭：两次原24叶门通过，原生导出失败，成本归因仍未解决。** 用户2026-09-30“批准”的唯一180秒／8GiB窗口已使用，退出码1；终端总钟48.440658秒，保存receipt口径48.372862秒，绑定前48.437823秒，采样进程树RSS峰值931,233,792 bytes（0.867279053 GiB）。唯一start成功返回、唯一stop/export抛`INVALID_ARGUMENT`，错误指向带`\\?\`前缀的`native/plugins`目录；原生文件0件，`observability_not_pass`。三阶段清理与P3封存通过，无修复／重试。父原状态`resource_or_supervision_stop`源于非零退出分流缺口，不能解释为实际资源耗尽；SUP2实际为`nonzero_exit / 1`且无监督错误。详见[本轮结果、分类勘误和后续依据](HF4_C2_S0_PREPARATION_RESULT_20260928.md#f-trace1实际执行结果2026-09-30)、[父回执](../hf4_c2_stable_f_validation/micro_trace_001/execution_receipt.json)、[最终绑定](../hf4_c2_stable_f_validation/micro_trace_001/receipt_binding.json)、[阶段图](../hf4_c2_stable_f_validation/micro_trace_001/stages.svg)、[资源图](../hf4_c2_stable_f_validation/micro_trace_001/resources.svg)及[覆盖图](../hf4_c2_stable_f_validation/micro_trace_001/coverage.svg)。

F-TRACE1完成28阶段（27通过、profiler.stop失败）／74事件／8常规artifact；3项真实parser控制通过。同步12.949009／12.828373秒，同一已ready完整树再等待54.4µs；两NPZ各16,080 bytes，均与F-COST1对应原件同SHA。没有JSON／XPlane，26个ENTRY producer运行观测均为null，不能把结构重复解释为已证运行重复或成本根因。45条CPU原记录完整，两sync短窗均不足30秒，原门inconclusive。关闭后三路独立只读核验93输入／5,937,198 bytes、134 payload／11,268,196 bytes、43绑定（41实件＋2真实未到达null）及四实例终止／释放通过；更新前两live文档与冻结一致，随后仅更新本页及原报告。

**前轮F-COST1成本诊断完成；完整force及科学准入仍未通过。** 用户2026-09-30批准的唯一240秒／8GiB窗口已使用并关闭，退出码0／`runtime_cost_diagnostic_complete`。终端总钟45.410554秒，保存receipt口径45.354241秒，绑定前45.408621秒；采样进程树RSS峰值486,240,256 bytes（0.452846527 GiB）。三个阶段正常退出／清理通过，43阶段／114事件及严格两图四call／四sync／两ready-only／共同输入ready一次全闭合。详情见[该轮完整结果、取舍与边界](HF4_C2_S0_PREPARATION_RESULT_20260928.md#f-cost1实际执行结果2026-09-30)、[父回执](../hf4_c2_stable_f_validation/force_cost_001/execution_receipt.json)、[最终绑定](../hf4_c2_stable_f_validation/force_cost_001/receipt_binding.json)、[四列阶段图](../hf4_c2_stable_f_validation/force_cost_001/stages.svg)及[CPU图](../hf4_c2_stable_f_validation/force_cost_001/cpu.svg)。

同字节R1微图首次／重复同步分别12.909607／13.021047秒，而对同一个已ready完整24叶树再次等待仅68.8µs；tiny前／后同步分别33.3／35.6µs。这削弱通用block固定13秒和仅首次冷启动解释，成本随新micro派发后的首次就绪出现，内部图计算／native首次多叶等待、自旋或调度仍未区分。本次actual config为CPU／x64／async开启，debug NaN／Inf、disable_jit、PGLE、缓存关闭，strict两选项false；环境快照只证明本次进程，不回填前轮。六个CPU区间全按原门保持inconclusive，两micro内部覆盖仅11.262485／12.297575秒，不能升级有效CPU分类。两tiny及两micro完整24叶原值门通过，六IR与四先保存再比较的NPZ完整保留。

三路关闭后独立只读审计通过：80输入／3,758,121 bytes及live对应来源（文档更新前）、32R1原字节／零patch、15runtime pins、122 payload／9,146,395 bytes、39非空最终绑定与SUP2三实例终止／句柄释放全部闭合。新根128件只比payload多六项声明排除；原三force辅助和科学／测试／监督字节保持。随后只更新本页和报告；冻结的作者状态文档保持原件，未回写冻结或重跑数值。科学准入false，完整force原三力门、AD、接触任务和HF5仍未完成；本轮交付状态见开发移交验收记录。

F-COST1的六组DD高低共同前缀仍仅为结构线索。F-PATH1补接口证据，F-TRACE2实际导出但单件门停止，F-BYTES1证明正文超过256MiB；[F-STREAM1](HF4_C2_S0_PREPARATION_RESULT_20260928.md#f-stream1实际执行结果2026-09-30)当前只闭合400万事件前缀与partial保存。三后审核36角色／34复制＋2引用、19runtime、70files／64payload／34非空bindings／六排除及来源一致；新单helper128256B／1250415b2084cd4d52aaae2a0f996f3a905e513cbb8e1b6085ac15c143569174保持，两SVG已实际渲染审图。先审保存样本、原包装及direct参数与执行名称规则的适配，再选择下一有界区间／采集方法；新解压、重采集、门禁变更或科学执行需各自具体卡。44producer／26fusion仍null，完整force／AD／HF5资格不变。

更新：2026-09-30。本页是主干接续入口；历史报告、协议、日志和结果保留原件。主干整合情况见[最终整合报告](MAIN_CONSOLIDATION_REPORT_20260927.md)。**前轮F-REUSE2：P1完整局部合同通过，P2完整force编译及调用返回，但输出同步在239.75秒阶段活动界内未完成。** 终态`resource_or_supervision_stop`，总钟510.535803秒、采样进程树RSS峰值2,009,739,264 bytes（1.871716 GiB）。P3封存与已启动阶段清理通过；三个完整力门未到达。详情见[该轮结果与边界](HF4_C2_S0_PREPARATION_RESULT_20260928.md#f-reuse2-实际执行结果2026-09-30)、[父回执](../hf4_c2_stable_f_validation/force_reuse_002/execution_receipt.json)、[最终绑定](../hf4_c2_stable_f_validation/force_reuse_002/receipt_binding.json)及[资源图](../hf4_c2_stable_f_validation/force_reuse_002/resources.svg)。

R1本轮按原32件／380,009 bytes继承，零新patch；原canonical C1／ci、H1、HR1、SUP1／SUP2和默认内核字节保持。新的P1完整重做48阶段：NumPy六单例＋mixed批26字段、材料范围拒绝、选择器及HP80/120三参考一致性通过；两份严格微图、全部八组／16次call及同步通过，16份局部NPZ新保存。同步单次13.223568–15.162371秒，合计229.591270秒。P1只授予有限局部结构等价，未授予完整compiled constitutive／AD资格。前轮F-REUSE1的五组通过和NaN组开放等待仍单独保留，本轮没有拼接旧结果。

三路独立只读复核通过：347输入／9,457,076 bytes、R1同字节继承、407 payload／57,298,730 bytes及最终25个绑定目标（23非空匹配、2未到达空目标）均闭合。P1／P2各三实例按PID＋创建时间证明终止、句柄释放及Job末活动数零。新证据根为`hf4_c2_stable_f_validation/force_reuse_002`，最终binding SHA `b223ad7b85c9b3f561ffcb609fd8155866cee9e4f368dc4cd2dde3da00f4f856`。HR1原生F-REUSE1身份由独立当前F-REUSE2绑定封装，没有重写原报告。P2子summary保留停止前running检查点，父回执及清理证明是终态，冻结目录不回写。

用户“按 F-REUSE2 卡执行”的唯一620秒／8GiB窗口已使用并关闭。P2 trace／lower／compile分别5.293057／1.747016／37.770459秒，call约0.678毫秒返回；没有输出NPZ，三个力门均未到达。三份新R1 IR完整保存，优化图指令数由C1基线191,329降至173,544，但未证明输出精度、实际加速或成本根因。[CPU报告](../hf4_c2_stable_f_validation/force_reuse_002/cpu_observation.json)在同步内176样本／约178.878秒取得有效观测，平均约1.846318逻辑核；CPU消耗不能证明物理进度。[阶段图](../hf4_c2_stable_f_validation/force_reuse_002/stages.svg)与[CPU图](../hf4_c2_stable_f_validation/force_reuse_002/cpu.svg)均保存实际范围。触发的是P2阶段界，未用剩余总额度重试。新代码、证据与文档纳入本次main交付（见验收记录）；完整force／AD资格、科学准入和HF5仍未完成。

此前[F-CPU-OBS1](HF4_C2_S0_PREPARATION_RESULT_20260928.md#f-cpu-obs1-实际执行结果2026-09-29)取得约1.576逻辑核的有效CPU消耗观测，但C1完整force同步未完成。其raw JAXPR／StableHLO与旧F-OBS分别字节相同，optimized HLO仅8行来源metadata不同；合法分支重复运动学是提出复用候选的结构依据。F-REUSE2取得新R1图和完整局部门，但同步等待问题仍在，原生成本尚未归因。关闭后的[只读成本排查与F-COST1卡](HF4_C2_S0_PREPARATION_RESULT_20260928.md#f-reuse2后成本排查与f-cost1执行卡待授权)确认：六个最大融合体中五个指令数与C1完全相同，能量及Hu链保留大量共享子DAG；旧环境记录不足以排除继承的XLA/debug/PGLE配置。F-COST1的两图／四call／两次同对象ready-only诊断现已批准、执行并关闭；本次配置与等待证据详见最新结果，它不替代完整force。原卡标题保留提案历史身份。

## 整体目标与工作理由

授权等待历史（2026-09-30）：F-PATH1、F-TRACE2、F-BYTES1、F-STREAM1各曾三轮待批准登记blocked，随后对应明确批准解除；四卡唯一窗口、后审与记录现均已关闭。历史保留原报告，不当当前仍待这四卡批准。完整目标未完成，关账工具现返回blocked（原因未提供）；最近300秒／4GiB不能用未耗余额扩展，新阶段须以实际证据审后立卡。

建立一个与 LF 解耦、可异机恢复且任务定义明确的 HF 正向力学评估器。LF/N4 负责候选生成及研究层选择/统计；HF 通过普通几何文件独立输出可信的力学结果，再在一致任务、实现身份和有效前缀规则下供研究层使用。数据可读、求解收敛、算术精度、接触物理及机构功能不能互相代替。

现阶段先处理启动和数值可信性，是为了避免把缺少合同约束或受到舍入误差污染的输出当作 HF 标签。保留失败、来源链、成本和重复实验身份，是为了让改善有可复查的因果依据，而不是只留下后来通过的图表。

## 已做、效果与未完成事项

| 工作 | 当前事实 | 范围限制 |
|---|---|---|
| HF0–HF4-B / 0.5.0 | 独立包、两例普通几何、split 权威位移及历史门禁已交付 | 稳定 wheel 不含后续 C0/C1/C2 模块 |
| HF4-C0/C1 | 受限全接触参考和 C1 的 10 条选定路径通过对应门禁 | 未验证一般局部单边接触、释放/重入和最终机构功能 |
| S0 | 主树与可恢复大证据分层 | 工作树缩小不等于 Git 历史缩小；不改写历史 |
| P1 | wrapper 与直接 runner 前置完整合同，相关验证已保存 | 冻结 v3 原入口保持历史身份；P1 不是无限新路径授权 |
| 稳定 F 候选 | 63/63 保存态通过，原细网格末态误差由约 `1.094e-11` 降至 `8.61e-16` | 固定保存态复算不改原 v3 `NOT_PASS` |
| 制造场 | 30/33 通过；三个近旋转场完整力失败，两个矩形网格另有极小正则力失败 | 不放宽 SF 或门槛，不把近旋转输入直接当作零应变态 |
| 近旋转五段诊断 | 10 项合成测试通过；三例 80/120 位参考重构及分段一致性通过；一次运行约 14.733 秒、峰值约 139 MiB | 只提高后续精度/重算 J 仍不足；HP F/J 闭合材料力，HP Hu 才闭合矩形场正则力。诊断本身不授予新候选资格 |
| 小不变量/Hu 新候选 | 新增 `p26_q1_split_invariants_hu_v1`、DD 原语、范围/JVP 合同与冻结验证驱动；Windows 监督器 5 项合成测试通过 | v1 准备阶段遇到目标长路径错误；v2 S0 日志含失败进度，随后达到 300 秒上限。窗口约 493.149 秒关闭，峰值约 2.69 GiB；没有完整算术/内核通过回执，也没有候选科学准入 |
| S0 执行准备诊断 | 即时日志/监督 8/8 通过；取得 B0 与无屏障对照的完整编译边界错误；51 份输入、99 份输出哈希通过，8 个阶段确认清理 | `s0_ready_001` 约 43.799 秒以 `execution_failure` 关闭，峰值约 487.27 MiB；联合/分别屏障未执行，原屏障假设未判定，无 C1 或后续科学通过 |
| JIT/AD-1 | H1 修正包装；none/separate 全通过、joint 与 B0 目标末端断言一致；条件 C1＋同一 H1 九项全过并同步。68 份输入、190 份输出核验通过，17/17 阶段清理成功 | `jit_ad_ready_001` 以 `resource_or_supervision_stop` 关闭。A5 编译已完成，首次调用/同步未完成；没有固定单元输出/IR，A6 未到达。C1 只是本卡局部修订身份，不代表 HF4-C1 阶段或科学准入 |
| F-OBS-1 | 同一 C1/H1 固定 force 的三份图完整保存；compile 73.799 秒完成，首次调用 1.045 毫秒返回；87 份输入来源核验、3/3 阶段清理和封存通过 | `force_observe_001` 以 `resource_or_supervision_stop` 关闭；同步未完成，126.788 秒只是含清理/调度的开放观察上界，无 NPZ 或输出数值验收。没有修科学代码、重跑九项或推进 tangent/矩阵 |
| F-CPU-1 | 新增可选 Job CPU 日志及辅助脚本；原五项监督回归通过，115 组来源、147 项输出及 3/3 阶段清理核验通过 | `force_cpu_001` 以 `execution_failure` 关闭；首个新增测试两层内部短时限先后触发，另外三项未运行，新增监督合同未通过。force 未启动，不能更新科学 CPU 或同步结论 |
| F-CPU-S1 | 修订回执先落盘、入口/负载/退出标记及固定嵌套期限；原五项通过，正常场景两层 normal_exit/0；34 组来源、74 项输出核验通过 | `cpu_supervision_001` 以 `execution_failure` 关闭；首新增测试的历史 PID 存在性断言失败，后续 CPU 断言及另外三项未执行。两级 Job 末计数归零与裸 PID 断言的差异尚未定因，不能据封存或离线读数补登记通过 |
| F-CPU-PID1 | 保留原门并记录实际短路查询；唯一 PID 1704 的 native 查询链与关闭成功；45 组来源、87 项输出及三图封存通过 | `cpu_pid_diagnostic_001` 以 `execution_failure` 关闭；五过一败、三未运行。Wait 未 signaled、退出码 125 和退出时间 0 分别保留；自动生成的退出时间有效性标签过强，见报告勘误。缺历史实例绑定，监督合同未通过，无 force |
| F-CPU-CLEAN1 | 独立 SUP2；12 控制＋九真实场景全过，十份实例证明全闭合；busy 父6/子3身份各自闭合，查询/写入注错保留且独立清理通过；49 组来源、157 件输出和三图保全 | `cpu_cleanup_contract_001` 以 `synthetic_supervision_pass_no_force` 关闭；39.088 秒、141.75 MiB。新合同明确替换裸 PID 门，不能倒改 SUP1/S1/PID1 资格，不能保证任意短命成员必被轮询捕获；无 force 或科学准入 |
| F-CPU-OBS1 | 同一C1/H1一次force；79个同步内样本满足原质量门，125.4375 CPU秒／79.5855墙钟秒≈1.576核；SUP2四实例证明通过，199来源、229输出和三图封存 | 总251.293秒、峰值1.9607 GiB，`resource_or_supervision_stop`；compile96.670秒、call1.243毫秒返回，sync未完成、无输出NPZ。CPU消耗不能证明数学进度；无科学准入 |
| F-REUSE1 | R1独立派生；NumPy有限26字段、选择器和参考一致性通过；两微图编译、前五组比较通过；248来源、32派生、327输出与三图封存 | 总184.038秒、峰值512.73 MiB；P1时限停止，第六组R1同步未完，P2未启动。完整局部门、三个R1力门及科学资格未通过，原内核不切换 |
| F-REUSE2 | 同字节R1零新patch；P1完整48阶段／八组／16次call及同步通过，16份NPZ；新完整force三IR、有效CPU观测与双阶段同实例清理证明取得；347输入、407输出及25绑定目标核验通过 | 总510.536秒、峰值1.871716 GiB；P2编译完成但输出同步阶段超时，无完整force输出或三力门。图规模缩减不等于加速；无完整AD或科学准入，窗口已关闭 |
| F-COST1 | 同字节R1/HR1两图四调用，两次完整输出ready-only；43阶段114事件、四原数值比较、实际配置／CPU原记录、80输入122输出39绑定及同实例清理全部核验通过 | 总45.411秒、峰值0.452847GiB；两micro sync仍约13秒，已ready微树仅68.8µs。六CPU窗均不足30秒或无样本，原分类inconclusive；内部成本未定因，fullforce／AD／科学准入未推进，窗口已关闭 |
| F-COST1后只读定位／F-TRACE1 | 原六对hi／lo结构线索保留；3parser控制、两24叶原门、93输入／134输出／43绑定、四实例清理和三图均核验通过 | 唯一窗口48.441秒、0.867279GiB关闭；native stop/export路径INVALID_ARGUMENT，0原生文件，observability_not_pass。父非零退出分流过强已记录，未改冻结。成本／完整force／AD／科学准入仍未通过 |
| F-PATH1原生路径接口 | 12控制、start／标记体／stop各一次；44输入／78输出／33非空绑定、P1三成员同实例清理及三摘要SVG后审通过 | 唯一90秒卡使用16.048秒，0.156792GiB；普通路径导出JSON.gz与XPlane各一件，native_path_interface_pass。无数组或科学计算，微图观测／成本归因／完整force／AD仍缺 |
| F-TRACE2原微图观测 | 16组控制、两原24叶、一次start／body／stop／导出、105输入／149payload／43绑定及三实例清理后审通过 | 唯一窗口74.275秒／2.487507GiB关闭；XPlane87,819,545B超过64MiB单件门，observability_not_pass。JSON未解码、44producer／26fusion全null；完整force／AD／科学准入未推进 |
| F-BYTES1现有gzip体积 | 五控制、一次真实gzip／294次有界读取、12步骤341事件、18输入／43payload／31非空绑定及原SUP1三阶段清理后审通过；两SVG已渲染审图 | 唯一窗口5.882秒／70.387MiB关闭；body_over_cap，下界268,435,457B，精确正文／完整SHA未知、EOF／CRC未验证。无JSON／XPlane解释或内部归因；原接受门及科学资格保持 |
| F-STREAM1有界流式普查 | 16组82控制子例、一次真实gzip／496reads、400万接纳事件、旧前缀交叉检查、36来源／64payload／34绑定／原SUP1清理与三后审通过，两图实际审图 | 唯一窗口143.272秒／86.426MiB；event_count_limit、execution_failure／partial，EOF／正文CRC／UTF8 final／完整JSON未验证，完整普查未授予；无余量续读、内部归因或科学资格 |
| 独立复核 | 重算算术、制造场及选定 8 态；增强真实 C1/C2 schema 的来源绑定 | 重叠状态与重复测试分别报告，不累加为更多物理覆盖 |
| v4 补测 | 唯一细网格路径 21/21 状态、651/651 检查、7/7 原目标通过，末态完整力误差约 `8.44e-16` | 只补测该路径，未用 v4 重跑另外两条；不构成一般接触或网格收敛证明 |
| 下游 HF5 | 已有 LF v2 适配与真实夹持任务方案 | 尚未实施；默认内核未切换，也未开始批量 HF 标签或最终排名 |

HF5 草案的事实勘误已完成：[30 包元数据清单](../research_integration_20260920/lf_v2_grid_inventory_20260928.json)确认原生网格为 23 个 80×40/1 mm、7 个 160×80/0.5 mm；全部 `analysis_mesh=160×80` 不代表原生网格相同或 HF 分析政策已确定。草案已移除 v4 尚待排序的过时事项，并明确现有单 u 平均端口控制不等于尚未实现的 split 平均端口增广系统。本次为只读资料核对与文档勘误，没有转换几何或新增数值验收。

v3 三次单因素尝试共 59 态，其中 58 态通过；1810 项检查中 1809 项通过。细网格有效前缀止于 `d=0.4375 mm`，末态门失败永久保存。v4 的 21 态属于新协议下单独运行，不能替换 v3 结果，也不能把两个版本拼成同一内核的全路径资格。

P1/稳定 F 的原报告包含“任何 binary64 实现都不可能达标”的过强解释；当前解释采用[范围勘误](HF4_C2_NEAR_ROTATION_SCOPE_NOTE_20260927.md)与[独立失败分析](HF4_C2_STABLE_F_FAILURE_ANALYSIS.md)。证据支持当前 F/J/应力及 Hu 求值链的不足，不证明所有 binary64 算法不可能达标。

## 当前可执行边界与后续次序

1. 后续开发统一在 main。恢复、核验和阅读已有证据可按[接续指南](RESUME_DEVELOPMENT.md)执行；写入审计详情前使用独立复制树。
2. 近旋转五段诊断、C1＋H1九项、CLEAN1、OBS1、R1局部门及成本诊断保持各自原资格；完整force同步仍未完成。F-TRACE1／PATH1／TRACE2／BYTES1均关闭；F-STREAM1也已按400万事件界partial关闭。下一步先只读已有样本、原采集包装及原规则适配，充分排查后再立最近一张有界卡，不能续用旧窗口或直接推进AD、新路径、HF5。
3. 候选窗口 `invariants_hu_campaign_001` 已因单进程超时关闭。虽然总耗时未到 1200 秒且只冻结两版，原卡规定的资源停止条件优先；不得使用剩余时间/第三版续跑，不换目录名重置额度。任何后续数值执行须另有明确的新卡与授权。完整材料力、正则力、总力和真实残差导数仍沿用原门，旧快照不能回写。
4. v4 原授权的一次求解、一次审计已经完成，单路径额度已耗尽。剩余墙钟余量不等于剩余执行次数；不能换目录名、清回执或自动重跑。新的平衡路径需另有明确协议、预算和准入。
5. 完成目标任务的数值与接触物理资格后，才推进 HF5 接入。复用 N4 研究层时先定义任务与标签适配，不能混用不同后端或把 v4 单条均匀路径的通过推广至真实夹持候选。

旧诊断调度器保留当时字节；本次新增 Windows Job Object 监督器，正常/非零退出、超时、低内存限额、孙进程清理的 5 项测试通过，且实际超时后已确认 Job 活动进程为零。监督器的通过不代表候选算术或力学通过。

[旧候选窗口 ledger](../hf4_c2_stable_f_validation/invariants_hu_campaign_001/ledger.json)、[v2 最终回执](../hf4_c2_stable_f_validation/invariants_hu_campaign_001/version_002/execution_receipt.json)、[旧资源图](../hf4_c2_stable_f_validation/invariants_hu_campaign_001/version_002/resources.svg)保存旧轮实际结果。v1/v2 来源保全分别为 270/744 组、运行期间变化均为零；v1 的目标长路径失败保留原状态，另附实现错误归因，没有把真实来源变化解释为普通修错。该旧轮回执为 `resource_or_supervision_stop`；新的 S0 诊断为 `execution_failure`，两次运行不拼接。默认内核和既有 v3/v4 资格不变。当前 main 的 HEAD 仍为 `18f1f62`，origin 仍为 `https://github.com/dudaxing/Compliant-TO-TMC.git`；本轮没有提交、推送或改分支。

**旧 S0 执行准备诊断卡已经执行并关闭。** [回执](../hf4_c2_stable_f_validation/s0_ready_001/execution_receipt.json)、[绑定](../hf4_c2_stable_f_validation/s0_ready_001/receipt_binding.json)、[资源图](../hf4_c2_stable_f_validation/s0_ready_001/resources.svg)及[未到达阶段图](../hf4_c2_stable_f_validation/s0_ready_001/stages.svg)保存该次完整结果。无屏障 eager 七步骤通过，但无屏障 strict-JIT 的 VJP 构造即遇与 B0 同类 ValueError；当时联合/分别屏障未执行，不能用该次结果判定原假设。首次静态审查遗漏了这项 JAX 接口限制，报告已明确记录。当时科学源码及原测试未改，完整矩阵未运行；新 JIT/AD-1 的结果单独保存，没有覆盖旧证据。

**JIT/AD-1 也已执行并关闭。** 用户“批准按卡执行”的一次新窗口已使用；[最终回执](../hf4_c2_stable_f_validation/jit_ad_ready_001/execution_receipt.json)、[绑定](../hf4_c2_stable_f_validation/jit_ad_ready_001/receipt_binding.json)、[资源图](../hf4_c2_stable_f_validation/jit_ad_ready_001/resources.svg)与[分段图](../hf4_c2_stable_f_validation/jit_ad_ready_001/stages.svg)给出终态。A5 trace/lower/compile 分别约 18.303/7.024/87.924 秒；首次调用与同步的开放观察区间约 23.331 秒，包含停止清理/调度，不是完成的执行耗时。子探针最后 `running` 快照不代表后台仍有进程，父回执及 17/17 清理记录是终态依据。A6、69 场/138 方向/63 态矩阵及新平衡路径均未运行。

只读核验和本次记录更新已完成。600 秒不是触发停止后可继续消费的余额；不得重用目录、重跑 A5 或启动 A6。进一步数值执行需要基于当前证据的新执行卡及明确授权，整体开发目标仍未完成。

**F-OBS-1 已获批准、执行并关闭，额度已使用。** [原卡及授权登记](HF4_C2_S0_PREPARATION_RESULT_20260928.md#f-obs-1-固定-force-首次调用与同步观测卡待授权)中的“待授权／未创建目录”是提案及启动前记录；最新终态见[回执](../hf4_c2_stable_f_validation/force_observe_001/execution_receipt.json)、[最终绑定](../hf4_c2_stable_f_validation/force_observe_001/receipt_binding.json)、[分段图](../hf4_c2_stable_f_validation/force_observe_001/stages.svg)和[资源图](../hf4_c2_stable_f_validation/force_observe_001/resources.svg)。F1 的 `reason=global_deadline` 是监督器对绝对截止的名称；`active_limit_kind=phase_inclusive_limit` 表明触发的是 239.75 秒活动上限，含清理实际 239.776 秒，并非整卡 300 秒耗尽。原完整 26 字段合同保留，但传输、NPZ 和 finite/float64、J、支持域门均未到达。F2 的 pass 只表示证据保全；子 summary 的 running 是终止前快照，后台科学进程已清理。

本轮只新增三个辅助脚本，初次作者和 AST/静态审查后统一计时执行；没有改 C1/H1、默认内核或依赖。旧监督/日志八项与 C1/H1 九项只继承证据。关闭后只读复核、静态图/源码核对和记录更新，不以余量启动第二次 force。下一次实际数值执行、任何候选图修改或额外资源需要新的具体卡；当前没有后续数值窗口授权，也没有把整体目标标为完成。

关闭后的[静态定位](HF4_C2_S0_PREPARATION_RESULT_20260928.md#关闭后的静态定位事实与待验证假设)在优化 HLO 中确认 guard 与合法分支保留重复运动学结构；辅助能量与第二 Piola 应力仍参与支持域检查。它们是后续结构对照的候选线索，尚无耗时归因。不能把优化图中的 barrier 来源元数据解释为运行时屏障，也不能通过删除输出或检查来制造“完成”。

进一步只读审阅确认辅助能量在显示输出与支持域融合体中还有部分重算；直接复用运动学则涉及整批/逐元素支持域区别及 `jacfwd` 输入链。因此提出先观测 CPU、再决定结构修改的 [F-CPU-1 运行状态观测卡](HF4_C2_S0_PREPARATION_RESULT_20260928.md#f-cpu-1-运行状态观测卡待授权)：一次连续 360 秒/8 GiB，其中原 force 含清理上限仍为 245 秒；只增加每秒 Job 累计 CPU 记录及必要监督回归，C1/H1、26 字段及科学范围不变。该提案现已获批、执行并关闭；链接标题中的“待授权”保留提案历史身份。

**F-CPU-1 已关闭，未耗完时间不能继续使用。** [最终回执](../hf4_c2_stable_f_validation/force_cpu_001/execution_receipt.json)、[最终绑定](../hf4_c2_stable_f_validation/force_cpu_001/receipt_binding.json)、[资源图](../hf4_c2_stable_f_validation/force_cpu_001/resources.svg)、[未到达阶段图](../hf4_c2_stable_f_validation/force_cpu_001/stages.svg)及[无样本 CPU 图](../hf4_c2_stable_f_validation/force_cpu_001/cpu.svg)给出本轮终态。P0/P1/P3 分别为 9.594/17.504/6.943 秒；P1 收集九项、执行六项（五过一败），另外三项未运行。失败来自新增测试外层 7 秒绝对截止；已保存的后代回执还显示更早的内层 3 秒 `phase_timeout`，不能仅延长外层来掩盖它。两级合成 CPU 末记录的 Job 活动成员均归零；完整外层合成 receipt 未持久化、后代缺少正文入口标记，是下一步需要补足的取证缺口。CPU 观测错误与内层启动/等待原因尚未定因。

本轮监督器和四份新辅助/测试文件已保存，科学源码及 H1 未改。新增合成检查未完整通过，P2 没有启动；本轮继承目录中的 IR 均为旧 F-OBS 证据。封存 pass、CPU 判读 `inconclusive` 和 `actual_telemetry_failure=false` 都不能替代观测验收。关闭后只读复核及文档更新，没有修补后重跑，也没有下一次合成或科学窗口授权。后续先形成范围明确的合成验证修订卡，整体目标仍未完成。

此前只读续轮形成的 [F-CPU-S1 合成监督修订验证卡](HF4_C2_S0_PREPARATION_RESULT_20260928.md#f-cpu-s1-合成监督修订验证卡待授权)现已获批、执行并关闭。一次 120 秒/8 GiB 窗口的额度已使用，监督器固定为 `9f3da2f2…aec32`，没有 force。实际 P0 携带选定 24 件监督失败证明（322,631 bytes），新辅助/文档共 10 件，总输入 34 件、567,548 bytes；旧 147 项 payload 中携带 19 项、省略 128 项，不重新复制旧科学 IR。提案标题中的“待授权”保留历史身份，不代表本轮需要再次批准。

**F-CPU-S1 的新增监督合同未通过。** [最终回执](../hf4_c2_stable_f_validation/cpu_supervision_001/execution_receipt.json)、[最终绑定](../hf4_c2_stable_f_validation/cpu_supervision_001/receipt_binding.json)、[九项覆盖图](../hf4_c2_stable_f_validation/cpu_supervision_001/tests.svg)、[两级合成 CPU 图](../hf4_c2_stable_f_validation/cpu_supervision_001/cpu_lifecycle.svg)和[资源图](../hf4_c2_stable_f_validation/cpu_supervision_001/resources.svg)保存实际终态。P0/P1/P2 分别 1.896/10.629/1.257 秒，三个父阶段回执均确认 Job 清理且无监督错误；外层/内层合成调用分别 4.617/1.155 秒，正常退出并保留完整标记。失败在冻结测试第 221 行 `any(psutil.pid_exists(pid) ...)`，并未走到 busy/sleep 与退出后累计量断言；`cpu_comparison.json` 不存在。不能以正常回执、清理计数或关闭后原始数据重算替代失败测试的验收。窗口关闭后只读核对、资料核查及文档更新，没有修补或第二次 pytest。

**F-CPU-PID1 已执行、封存并关闭。** [最终回执](../hf4_c2_stable_f_validation/cpu_pid_diagnostic_001/execution_receipt.json)、[最终绑定](../hf4_c2_stable_f_validation/cpu_pid_diagnostic_001/receipt_binding.json)、[PID 原始链汇总](../hf4_c2_stable_f_validation/cpu_pid_diagnostic_001/pid_diagnostic.json)、[九项覆盖图](../hf4_c2_stable_f_validation/cpu_pid_diagnostic_001/tests.svg)、[两级 CPU 图](../hf4_c2_stable_f_validation/cpu_pid_diagnostic_001/cpu_lifecycle.svg)和[资源图](../hf4_c2_stable_f_validation/cpu_pid_diagnostic_001/resources.svg)保存实际结果。P0/P1/P2 分别 1.372/14.814/1.826 秒；外层/内层场景均 normal_exit/0，末 Job 活动数均为 0，但 PID 门仍失败，后续 CPU 断言未到达。`triggered_native_success` 仅表示一次诊断 API 链和关闭成功，不表示测试或清理合同通过。原查询之后 Wait 未 signaled，退出码 125 与监督器终止请求码一致；异步终止是候选解释，不能据此认定历史同一实例或根因。冻结 `exit_filetime_validity` 标签由退出码自动推导，未获 signaled 佐证，报告已勘误，不将退出时间 0 当作有效终止时刻。实际携带 S1 35 件/649,470 bytes；固定监督器、原五项与科学源码未变。没有第二次 pytest 或 force。

## 恢复和记录

**用户“批准按 F-CPU-CLEAN1 卡执行”的唯一 180 秒／8 GiB 窗口已执行并关闭。** [最终回执](../hf4_c2_stable_f_validation/cpu_cleanup_contract_001/execution_receipt.json)、[最终绑定](../hf4_c2_stable_f_validation/cpu_cleanup_contract_001/receipt_binding.json)、[实例清理合同](../hf4_c2_stable_f_validation/cpu_cleanup_contract_001/cleanup_contract.json)、[21 项覆盖图](../hf4_c2_stable_f_validation/cpu_cleanup_contract_001/tests.svg)、[两层 CPU 图](../hf4_c2_stable_f_validation/cpu_cleanup_contract_001/cpu_lifecycle.svg)和[资源图](../hf4_c2_stable_f_validation/cpu_cleanup_contract_001/resources.svg)保存实际结果。P0/P1/P2 分别 2.762/31.060/4.803 秒；pytest 21/21 通过，封存合同 `verified_all_instances`。查询/写入故障各在第2次调用按预声明触发，错误保留而清理通过；其 `supervision_error` 是预期测试结果，不是整个 campaign 异常。两个故意超时场景的轮询观测延迟约 10.925/23.788 ms，不能解释为硬实时截止。

关闭后先独立核验 49 组活源/冻结副本与科学4、psutil3、stdlib1文件，再更新本页和结果报告。冻结 `aux/docs/` 保留运行前记录，不回写。SUP1 固定 `9f3da2f2…aec32`；SUP2 固定 `b5f149e1…9499`。剩余墙钟不是追加额度，没有重跑、force、默认内核切换或 HF5 推进，也没有提交/推送。

**F-CPU-OBS1已授权、执行并关闭，额度已使用。** [原卡及作者记录](HF4_C2_S0_PREPARATION_RESULT_20260928.md#f-cpu-obs1-固定-force-cpu同步观测卡待授权)中的“待授权／未创建根”保留提案时点；最新终态以[父回执](../hf4_c2_stable_f_validation/force_cpu_observe_001/execution_receipt.json)、[最终绑定](../hf4_c2_stable_f_validation/force_cpu_observe_001/receipt_binding.json)、[CPU报告](../hf4_c2_stable_f_validation/force_cpu_observe_001/cpu_observation.json)和[实例证明](../hf4_c2_stable_f_validation/force_cpu_observe_001/supervision_proof.json)为准。三个限定辅助作者后经两名独立静审才一次执行；P0/P3保持SUP1，P2直接从本次冻结aux加载SUP2。原生CLEAN1合同与OBS1身份分字段，原回执先保存。P1为not_scheduled_inherited_CLEAN1。

P0/P2/P3分别8.1326323／240.8410134／1.6386463秒，均在15／245／25额度内；P2活动界仍为239.75秒，停止不是整卡300秒耗尽。首次清理比活动截止晚4.2525毫秒，约1.071秒完成实例闭合，使用同一5秒共享清理界。compile96.6698693秒完成，call1.243毫秒返回，sync没有finished；[阶段图](../hf4_c2_stable_f_validation/force_cpu_observe_001/stages.svg)的81.654秒为含清理/dispatch的开放上界，不是同步耗时。[资源图](../hf4_c2_stable_f_validation/force_cpu_observe_001/resources.svg)不含P3，最终回执另含。

CPU原237条和科学30条事件完整；严格同步内原行157–235全部79样本无删选，最大相邻dt_max1.0346154秒；user123.59375＋kernel1.84375 CPU秒，比率区间[1.5761326641,1.5761366903]，原30秒／2.5秒／0.5门满足。实际采集错误为false、integrity_valid=true。高CPU只约束本次观察，不能排除spin或后处理，也不能归因到具体线程/算子。

直接继承177件／3,166,771 bytes，另冻结13执行aux/文档及9 JAX来源，输入总199件／4,828,992 bytes。新输出229件／56,551,499 bytes；全根235件恰好含6项声明排除，14绑定目标全过。三名独立读者先核活源/冻结、CPU和清理后才更新本页及报告，冻结aux/docs不回写。原C1/H1/输入、26字段和14步骤不变；三份新IR完成但无输出NPZ及partial，数值门未到达。封存pass不改写force未完成，所有终态scientific_admission=false。唯一窗口不续用、不重跑，下一次计算没有当前卡授权。

**历史提案入口：[F-CPU-CLEAN1 卡](HF4_C2_S0_PREPARATION_RESULT_20260928.md#pid1-后清理合同审查与-f-cpu-clean1-卡待授权)，现已批准并完成。** 卡中“待授权／未实现／未创建目录”描述的是提案当时状态。实际仍保留父 SUP1；独立 SUP2 按同 Job、同句柄、原始创建身份验证，取得 signal 后释放，并以最终累计数闭合覆盖。原九场景负载和 CPU 门保持，裸 PID 门的变更已明示授权。实际直接继承 PID1 的37件／901,532 bytes，新增辅助和文档12件，总输入49件／1,310,326 bytes，不递归历史。

用户“授权F-CPU-PID1”的唯一 120 秒／8 GiB 窗口已经使用并关闭。准备、冻结、测试、一次 PID 诊断、三图、封存和末绑定均在该窗口内完成；停止后没有修改实现、重试或使用剩余预算。独立只读复核先确认 45 组活来源和冻结副本一致，再更新本页与结果报告；冻结 `aux/docs/` 不回写。提案中的“待授权／尚未执行”保留历史身份，不重复请求这一批准。当前没有下一次合成或 force 窗口授权。

用户明确回复“授权F-CPU-S1”的唯一窗口已执行完毕。实际准备、冻结、测试、可视化、封存及末绑定均在本次窗口内；关闭后先独立只读核验冻结/来源，再更新本页和结果报告。冻结的 `aux/docs/` 保留运行前版本，不回写。剩余墙钟不构成第二次运行额度，当前无新合成或 force 窗口授权。

已发布基线的轻量树以 `handoff/repository_manifest.json` 为准，大证据以 `handoff/evidence_assets.json` 为准；已发布后续资产入口为 `hf4-c2-followup-evidence-v1`，包含稳定 F 保存输出和 v4 载荷。[最终整合报告](MAIN_CONSOLIDATION_REPORT_20260927.md)链接实际上传、归档哈希、第二副本和空目录恢复回执；旧文档中“仅本机保存”是当时状态，不作为新的下载入口。最新近旋转诊断、候选、S0/JIT/AD/F-OBS/F-CPU/F-CPU-S1/F-CPU-PID1/F-CPU-CLEAN1/F-CPU-OBS1/F-REUSE1/F-REUSE2/F-COST1/F-TRACE1/F-PATH1/F-TRACE2/F-BYTES1辅助代码及证据仍在本地未提交工作树，尚未纳入这些远端交付清单；仅恢复已发布资产不能恢复到本页全部最新进度。

公开 v3 数值复读的外部来源例外仍严格限于原搬迁补充声明的两份 MATLAB 编号源码及其精确哈希，不能扩大。公开数值复读既不伪装完整来源复核，也不授予生产执行资格。

每次后续工作记录：整体目标、拟做事项、实际改动、理由、实际计算/测试、效果、失败和局限、代码/输入/输出身份、资源成本及下一步。当前状态入口可更新；被来源清单绑定的历史报告和证据不得为消除表面矛盾而改字节。
