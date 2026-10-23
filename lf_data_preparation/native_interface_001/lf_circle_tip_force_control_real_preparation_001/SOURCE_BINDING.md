# L-CTIPFREALPREP1：正式 r9 两载荷交叉检查的来源与接口绑定

2026-10-23。**本轮只完成普通资料/源码核对；未运行准入函数、构模、F/T、平衡路径或测试。旧 NPZ 和媒体只 stat，没有读取原字节、重新散列、解码或打开。** 原档声明的 NPZ/字段 SHA 原样引用，不能称本轮已验证科学 payload。

结论：现有 LOW1 的正确固定父与位移参考已经定位；普通身份、物理参数、成员及已安装入口的静态前置相符，可以据此准备下一张有界执行卡。完整 API 准入、两字段位身份和非零预载 fresh F/T 仍须在另行授权的唯一执行中完成。机器可读证据、完整普通文件/源码 SHA、声明的缓存身份及 stat 结果见 `SOURCE_BINDING.json`。

## 正确的固定父和参考

|用途|本机历史路径|本轮读取的普通文件 SHA256|
|---|---|---|
|完整固定父|`D:/hlo1_001/run_001/parent_fixed/result.json`|`09e37f483f4839ef5c03193d7cdd2f36cc2cccf045d96cd1026766e746ecad46`|
|父 model 描述|`D:/hlo1_001/run_001/parent_fixed/model/model.json`|`628d0d57f8d6de2a81f0dbef5b72f3a22248f3b56ee168b03dc94aa4cd6b3bd0`|
|选中父 state 描述|`D:/hlo1_001/run_001/parent_fixed/accepted/002/state.json`|`1247551e314aa312df687e1370bc9d011700148f1b2f67b618c31ce449c68347`|
|旧位移 probe 参考|`D:/hlo1_001/run_001/probe_low/result.json`|`acca0b8b97681cabf6e8517b28395b2c5b4cc20db9bb7496d6b10400b5400629`|

父是从零完成 `[0,.25,.50] mm` 的固定工件 `load_only`，status=success、path_completed/target_reached/loading_peak_reached 均为 true。**共3个接受态，选择索引2，即第三态 accepted/002；“accepted2”不表示只有两态。** 该态 is_original_target=true、original_target_index=2，d/physical_mean/original_target 均 .50 mm；目标不来自旧长加载路径的中间态。

选中父的有符号 `R_input=0.08589635225389337 N`；状态声明 SHA 为 `48fd7c621a8b1a060a5bec81307f2c8fe524569c6a4052da75884a8053e45bd8`。其 state.npz 声明 SHA 为 `fe83a2665105b692d6b2422292ecd07d35646c54f0221f29d61d008197ee9310`，两字段 float64/29970，lift 与 fluctuation 字段身份见 JSON。本轮只比较了这些普通声明，没有打开 state.npz。

probe 的 source.parent_result/model/selected_state 明确绑定该父文件 SHA、索引2、同一 split 身份及 R。其 q0 记录 newton_checks=1，状态档 SHA 与两字段声明、state_sha256、R 都与父相同；相对归档路径不同是正常的。父/probe 原验证 JSON 仍记录其当时 PASS；本轮没有重做这些数值验证。

## 原物理条件、成员和非 clock 参数

域 `[0,92]×[0,40] mm`、h=.5 mm，184×80=14720 单元、14985 节点、29970 全场 DOF；原 fixed1288/free28682。力控只是从这些原 free fluctuation 增加一个刚体 q 与 R 的约化未知量，不能把约化维数称新网格。

固定工件 circle r9、圆心(80,40) mm，原 body510格、565节点/1130DOF，与背景 y 对称重叠37DOF；source数组与几何不改。材料 E=1MPa、nu=.3、plane strain、厚20mm、gamma=1e−6、alpha=2.5e−7、Lr80mm、E*t=20N/mm。输出及辅助 spring 均0。q0由固定父继承；此后工件 body-x 统一为未知 q，body-y/转角保持约束，没有移动重选mask。

input 仍是5节点 `[14060,14245,14430,14615,14800]` 的 ux 平均，权 `[.125,.25,.25,.25,.125]`；output 仍是5节点原 uy 端口。原实体附着支撑、实体对称与全域背景对称规则保持；SOURCE_BINDING.json 保存实际 body cells/nodes、zero/background 集合和端口原记录，与 probe 普通成员完全一致。

原设置：tolerance1e−9、constraint_tolerance1e−10、displacement_scale_floor1e−6mm、force_scale_floor_factor1e−8、checks25、Armijo1e−4、backtracks12、bisections4、旧 minimum_increment=.00625mm。父历史 controller3600秒不是新授权窗口；新力控只能另定 clock。新的 N 最小步长必须另列，不能复用 .00625mm。

父/参考响应为 **mechanical + chunk256**，切线 block256 且 full-batch selector 保持。父历史 initial_guess=port_projection；新力控的数学规格采用 guided_reduced_tangent，原模式只作为 parent_initial_guess 保存，不能伪称新力控执行位移端口投影。小模型本轮只测 full，正式 chunk256 两载荷路径尚未运行。

## 两个绝对载荷候选

|原参考态|字段|绝对 P_half/N|原 q/mm|原 R_input/N|
|---|---|---:|---:|---:|
|probe accepted000|Q_drive_half_N|3.686421133658022e−5|0|0.08589635225389337|
|probe accepted001|Q_drive_half_N|4.3272306948756724e−5|.025|0.08589811003453525|

P0也精确等于父 accepted002 普通记录 `−workpiece.force_on_lower_body_N.total[0]`，与旧 probe q0 的 Q 同值。P1只是从旧位移参考选出的外载候选；新力控只能输入两个绝对 P，q=.025 是求解后的比较对象，不作为处方、初值或夹限。负 ON-body Fx 与正 P 的符号保持，P已含20mm厚度，完整对称装配轴向载荷仅换算为2P、q不倍增。

首目标不能从0开始或写成ΔP。它必须由原父 split/R 的一次新鲜 F/T 同时满足原free/mean/几何门与新g门，在检查1原样接受；不匹配则按 typed失败保存实际partial，不投影、修复或替换P0。原状态、父任务和已有 probe 资格保持历史，不能因这次准备升为完整参考/压力/承载资格。

## 已安装入口与未来读取边界

薄 API `evaluate_native_guided_force` 仍通过 `native_probe._admit`：普通结果/模型/状态 canonical identity、成功完整固定父最后原峰、源几何/材料/成员/支撑/任务、两个原力核 SHA、原执行模式均要绑定；接着实际读取原 selected state 的 lift/fluctuation、核payload/字段SHA、q0边界和state hash。此准备仅核了不需payload的普通前置与源码，没有调用 `_admit`。

父绑定的四个机制文件与当前安装源码 SHA 一致。新两个模块已另记录当前源码 SHA，未来候选仍需冻结完整执行源闭包。API保留 fresh/cache/typed partial；旧固定入口、位移 probe、默认CLI/native_response 不切换，不需要本准备改源码。

`build_native_project → native_map.prepare_native_geometry → data.load_geometry` 只加载父 model/source_geometry 下自包含 descriptor 与唯一 geometry.npz，解码 solid/design/passive_solid/passive_void 四 mask。native_map 为防读取时变化再读该同一 NPZ 原字节并核SHA，但不再解码。`_background_source` 仅读内嵌 LF provenance 的普通 descriptor 字典；**没有递归解析历史LF路径、读取历史LF NPZ、导入或调用dmftd。** 来源几何里的历史路径只是上下文。

建议下一卡明确分开计数：

|阶段|科学读取集建议|本准备是否执行|
|---|---|---|
|唯一 API 来源准入|3个旧NPZ：model.npz只整档hash不decode；snapshot geometry.npz解码4mask；父 accepted002/state.npz解码lift/fluctuation2字段。共2个decode档/6字段；旧force/tangent/matrix不读。|否；本轮只stat。|
|成功后的独立交叉比较|4个state NPZ：旧probe q0/.025与新force anchor/原P1终点，各lift/fluctuation，共8字段。q0须位身份；终点按预先声明的q/R/全场位移门，不能逐位要求两控制器相同。|否。|
|显示|新force result及本轮比较普通JSON/已核固定选择说明，**不读科学数组或旧媒体**。5PNG＋实际N帧GIF；包含全部实际接受态，单一P间隔原max_bisections4时至多17态。|否；只建议。|

因此API与比较合计建议7个不同NPZ路径：其中1个opaque model档不解码，其他6档共14字段；不能把API自身读取藏在“比较4档8字段”内。source geometry 和父state为完整身份验证有正常原字节散列/单次字段解码，不把字节读取次数等同字段数量。未来若要复制旧科学包，其复制/散列读取也须在卡里显式绑定，而非在本准备偷做。

显示可直接用新result的model坐标/连通/solid和所有accepted positions画实际×1变形、尖端接近与右侧介质**几何**，用已有接受态普通 minimum_J/max_abs_Hu 标量画全局曲线，另画P–q、R/分量力与双残差/收敛；没有局部J/Hu场就不能称画了局部场图。无需读取旧fields.npz或旧PNG/GIF。

## 固定选择文件的历史字段注意

LOW1复用 `D:/hlo1_001/observer_definition.json`，tip_node11260、right_medium_cells480、right_boundary_nodes81；body/input/grid固定ID已与LOW1模型普通成员核对一致。但该旧文件的 `held_input_mean_mm=1.06`，source_parent/model SHA属于旧高输入来源。**它只能作为固定选择ID来源，不能覆盖本次 .50mm 的任务或父身份。** 新准备应显式绑定LOW1父来源和 .50，并保旧选择文件原字节，不回写它。

未来用新result.model.solid检查right480相位，用本次父/force_task给d_hold；不要把旧observer的物理历史字段直接合入执行合同。本准备没有读取mask payload，因此没有重授right480介质或当前各场的数值资格。

本阶段19项普通/源码检查相符；全部旧NPZ/字段身份仍是已发表记录中的声明。下一步是把比较界值、N步长、读取集/显示与独立资源冻结成具体卡后审阅，当前不执行正式力控。
