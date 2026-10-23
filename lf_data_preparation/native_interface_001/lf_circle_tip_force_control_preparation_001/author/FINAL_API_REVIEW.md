# L-CTIPFLOADPREP1 最终接口／验证文档只读审阅

2026-10-23。审阅者 force_api_audit。结论：**本轮准备范围内静态通过；不存在可启动的力控候选，也没有数值通过结论。** 未发现阻止准备材料发布的接口、单位、计数或授权范围冲突。

正式目录：`D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/lf_data_preparation/native_interface_001/lf_circle_tip_force_control_preparation_001`。

仅读取 PREPARATION.md、API_DESIGN.md、SMALL_MODEL_VALIDATION.md、L-CTIPFLOAD1_CARD.md、PROPOSED_TASK.json、PROPOSED_EXECUTION.json，另读 TASK_SPEC.md 确认被引用的数学／力门。只核三份拟新增文件是否存在，结果均不存在。没有 HF import、pytest collect／测试、构模、F/T、HP、科学归档／旧媒体或图像读取；没有修改正式文件。

|核对项|判断|
|---|---|
|本轮与下轮授权|PREPARATION明确仅规格／接口／方案准备；下一卡新增实现／测试／显示／安装，须另获批准，不以本轮启动|
|新增与安装范围|两个新生产模块＋一个新测试，共三新增文件；全部验证／显示／清理通过才安装两生产文件，不改原55生产源码、默认入口／CLI、native_response或内核|
|当前不存在候选|三份新文件不存在；PROPOSED_EXECUTION的candidate_sha、unique_command、full_candidate_read_set均null，不能执行当前设计记录|
|未知与控制量|API仅给绝对half N载荷，不给q目标；未知w_F/q/R，机构mean由合法父保持；body uy／rotation仍导向|
|非零预载|首目标匹配fresh q0预载，状态／R逐位保持、检查1、无修正；绝对P0/P1与ΔP分开，不把P0设0或替换为fresh Q|
|half/full/厚度|half合力已含源厚度；P_full=2P_half、q不倍增，合力求和而非body平均，不逐节点重复施加完整P|
|力路径模式|仅绝对有符号目标严格递增；保留负值符号不等于任意负向推进、卸载或循环支持；q可由方程解为正或负，不夹到参考|
|新门与N步长|rho_P独立缩放，父tolerance1e−9明确复用于新增力门，base line-search尺度固定；minimum_force_increment_half_N带N单位，旧mm步长只作来源记录|
|新账本／保存／错误|外载P替代旧body-x处方驱动力，不重复；guide/zero去重，接受态缓存保存无额外F/T；独立schema及明确partial／失败码，不升级资格|
|有限计数|新8非参数方法＋旧9展开项=17；新16格最多4真实路径含注入partial＋旧2格1真实=最多5；新注入／拒绝≤32＋旧synthetic11=≤43；不同轴与partial重叠分开|
|新小模型与正式物理|新生成原16格／50DOF fixture自身2 mm厚度／alpha1e−4参数与Q0/Q1/Q2参考；不读旧科学缓存、不套正式LOW1载荷，正式r9／20 mm／alpha2.5e−7条件保持，下一卡不跑真实r9|
|交叉精度与资源|q与全场1e−8 mm、R混合界是事先声明功能回归精度，文档没有当成condition数严格误差界；记录灵敏度／conditioning，失败不放宽。300/60/480/540秒是有界建议非实测保证，首错停止，不延时或重跑|

原有 `test_split_displacement.py` 的静态计数依据已在 API_REVIEW.md 列明：8函数中一处2参数行，得9展开项；11次synthetic控制调用，另1条2单元／12DOF实际NumPy路径，solver预算15秒。本轮未collect或运行它们。新的最多32注入／拒绝与4条真实路径仍须在实现候选写成后按实码冻结；此处不是实现计数已核验的声明。

q回归门与本审阅原先“先由condition数估算后定”的建议作了明确取舍：正式文本将其作为预声明软件功能精度，另保留conditioning诊断，并禁止事后放宽，表述自洽。它不是严格数学误差界；本文不要求新增未计数的方向差分、HP或真实大模型运行。

PROPOSED_TASK的LOW1相对result与P0/P1仅为后续正式任务的上下文／候选输入，且自身标记design_only_not_native_task、numerical_launched=false、正式N步长null；本轮或下一小模型卡不应把它作为可直接运行的科学包。未来正式r9卡仍需另行冻结可完整恢复的科学缓存、读取集、N步长和资源。

## 审阅版本身份

|文件|bytes|SHA256|
|---|---:|---|
|PREPARATION.md|4053|149132cc54120ff28cc9063c6ea4af7d83487607971e7c026e8fb121dede1d21|
|API_DESIGN.md|5701|65459ce1cfffb543795c6d5b57440e0f67593ecd69cbe05b48109c1210ca8a35|
|SMALL_MODEL_VALIDATION.md|6626|80c8cb10238306a730adcdfb4d22f87f431a56701ba8fe03c025ea8757acced3|
|L-CTIPFLOAD1_CARD.md|4058|b680dbee761884dcd8cb8ea9412c092633ddf5af7e0feb802ee96f11831f127d|
|PROPOSED_TASK.json|1448|707791960ca2cd0ca46896bcc7a100d3047edc2bf9a5c9591f5b60ec50677a05|
|PROPOSED_EXECUTION.json|1128|517b640130f29a68e1a8ade1ec720889f23ee69b3476729286f43cfddb05974e|
|TASK_SPEC.md（补明global公式）|7394|0da456b36bdf52e8b24a167376136a059d0e1d7db465e16f801b72ee57dbe511|

这些SHA指本次已读版本；若后续修正措辞，应记录差异，不能把本审阅视为未读新实现或新授权的通过依据。

## 发布前定向补审

仅读取TASK_SPEC新增的全局门定义段，确认D为原fixed去body-x、body-y／其他zero去重；s_D在D取f_int−bR，G只包含该支撑、机构bR和一次显式(P_half,0)，S_G为各外力Euclidean范数和的原scale型归一化并以S_F作下限，norm(G)/S_G≤1e−6。定义与原互斥账本及半模型合力口径一致，没有恢复旧body-x support、分配任意节点P或更改门值／资源。**定向补审通过**；未重审无变化文件、未运行任何计算或打开媒体。

TASK_SPEC上一审阅版本为6983 bytes、SHA256 `8048599663c1642c5c90190d325a306e0886fd73bfcb958c82dfce4918f455ef`，仅保留作本次差异历史；表格已更新为本次新增段版本。PREPARATION及其他前述文件未在本次补审重读或修改。
