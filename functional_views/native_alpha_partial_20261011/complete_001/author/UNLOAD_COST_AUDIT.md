# M-ALPHA1 保存回撤记录与耗时静查

状态：`completed_saved_record_source_cost_audit`。这是一份现有普通记录／源码审计，不是新数值通过；未读NPZ、导入HF、调用observer/F/T/HP/solver、计算新科学差值/比率或绘图，未改正式代码。

当前正式main `9e2e37cce7f0441af042337d1c26c50ae660acc0`；原批准源码 `64a19f7d990d294d09f16145eae946e0edfa1580`。仅选择真实alpha-half result、response、回执、progress和相关入口，没有扫描旧9GB历史。文件SHA、逐条原记录及源码行号在unload_cost_audit.json。

## 已证明的停止原因

14个origin/loading状态接受并保存到1.20 mm；1.20→1.15 mm在depth0因原controller `time_limit: split average path wall-time budget exceeded` 停止，失败记录rollback_bitwise_equal=true。outer exit1、stop_reason=null，view_child0。停止不是外部stop或viewer失败；没有卸载接受态或二分接受态。原14缓存门passed不补齐15目标合同，也不新增HP/物理资格。

选取各诊断列表最后loading1.20条目之后的有序后缀，排除此前loading1.15同数值记录。现有回撤包括1个predictor、Newton基点1..5、6条line-search和6条linear记录。predictor为port_projection：applied_dw=false、applied_dR=true；第一全步invalid_J后半步通过，后续trial继续。记录general sparse LU、未对称和mixed-unit backward error仅诊断的含义保持。

| 回撤基点原记录 | relative_residual | minJ | R_input N | q_out mm |
| --- | --- | --- | --- | --- |
| 1 | 1.0331269586221747 | 2.3283009562457014e-05 | 0.3469423978687202 | 1.016934534302024 |
| 2 | 1.0702640195042776 | 1.4836005188760713e-05 | 0.34587261074181724 | 1.0161685038188368 |
| 3 | 0.5042937690821574 | 1.3842920988223533e-05 | 0.3465475984526561 | 1.0154200692417523 |
| 4 | 0.1883442835511377 | 1.9243629314096702e-05 | 0.34702580232762265 | 1.0153413874176795 |
| 5 | 0.032195140683106124 | 2.2862689240188248e-05 | 0.34703692706067296 | 1.0153191150094354 |

第5基点后原trial5为factor1、accepted=true、phi=7.609458874889267e−07、minJ=2.3740207303790917e−05、R=0.3470376718304425 N。trial accepted只更新Newton局部候选；后续合格基点没有记录，不能当成卸载平衡态或可恢复第15帧。

全路径force304开始／259完成、tangent126／126；125条Newton基点、178条trial、125条linear。拒绝库存为45条invalid_J和22条Armijo，属于原控制器内的bounded试探，不是外部重跑；计数未隐藏。回撤后缀中1条invalid_J，其余5条trial接受。

## 时间范围及能解释到哪里

Controller在初始化后开始计时；evaluate前／组装后均检查，sparse step前／后检查，接受callback后再检查。源码：[split_displacement.py:113](../../../../hf_repo/src/hf_eval/split_displacement.py#L113)、[split_displacement.py:126](../../../../hf_repo/src/hf_eval/split_displacement.py#L126)、[split_displacement.py:214](../../../../hf_repo/src/hf_eval/split_displacement.py#L214)、[split_displacement.py:325](../../../../hf_repo/src/hf_eval/split_displacement.py#L325)。9000秒是这些检查点的协作限制，不能中断正执行的组装，因此记录略过9000秒不等于擅自延期。API明确该时间不含imports／persistence，见[native_evaluate.py:25](../../../../hf_repo/src/hf_eval/native_evaluate.py#L25)。

| 原记录时间／范围 | 原值 s |
| --- | --- |
| peak接受controller elapsed | 8573.541880299992 |
| peak progress callback helper elapsed | 8579.992402699994 |
| controller path total | 9031.857919999995 |
| kernel_and_transfer | 8850.413170600033 |
| all_assembly_attempts_wall | 8995.9231345 |
| assembly | 2.150289499972132 |
| sparse_solve | 31.222233099935693 |
| callback | 0.2753118999826256 |
| native Mean evaluation | 9031.9274209 |
| response through-summary | 9051.659623300002 |
| helper | 9059.380507799986 |
| outer | 9059.673925399999 |

上述全部复制原字段；不相减、不算成本占比、不估剩余回撤时间。kernel_and_transfer标签在Mean中还加上切线时长；成功返回的fields才进入该累计，而all_assembly_attempts_wall在finally覆盖未返回组装。两者不能当成同范围，也不能从聚合值判断45次invalid_J的单次成本或强行选一个优化。没有每个force/tangent/block的独立时间。

126个完成切线调用与125条logged基点、峰值assembler_tangent_call120及5个卸载logged基点一致支持：下一次切线组装在预算检查处止步，基点尚未记录。evaluate组装后clock是符合源码的候选位置；日志没有每个clock的stack/timestamp，不能把具体执行行和未记录候选值写成直接观测。

## 持久状态和临时缓存必须分开

控制器在newton返回后才赋durable state/R/s/K；失败assert检查split位移／R的逐bit相同、s相同及K对象身份，不是重新核K矩阵的字节或数值。time_limit直接传播不二分。见[split_displacement.py:299](../../../../hf_repo/src/hf_eval/split_displacement.py#L299)、[split_displacement.py:311](../../../../hf_repo/src/hf_eval/split_displacement.py#L311)、[split_displacement.py:317](../../../../hf_repo/src/hf_eval/split_displacement.py#L317)。原峰值state及assembler_state SHA均为`fa0054288cd7eca4140f8bf04a94b5f833278b1c6e39813beb57cae16d7e9bca`，接受状态、独立state JSON与progress身份一致。

native_mean的last_tangent是每次tangent更新的临时cache，源码没有承诺把它随失败回滚。capture先核同状态，再copy数组、只读tensors及matrix并追加accepted；writer仅遍历accepted。见[native_mean.py:173](../../../../hf_repo/src/hf_eval/native_mean.py#L173)、[native_mean.py:177](../../../../hf_repo/src/hf_eval/native_mean.py#L177)、[native_mean.py:192](../../../../hf_repo/src/hf_eval/native_mean.py#L192)、[native_mean.py:256](../../../../hf_repo/src/hf_eval/native_mean.py#L256)。因此不能说‘所有缓存回滚’，但已保存的峰值接受缓存不会被失败候选覆写；最后trial或临时切线不在正式保存态中。此审计未读取任何实际NPZ值或临时cache。

## 是否已有现成非零续算入口

公共solve_native_mean从zero lift／undeformed状态开始，signature没有initial_state／initial_R／target_origin；调用底层时也未传这些参数。见[native_mean.py:113](../../../../hf_repo/src/hf_eval/native_mean.py#L113)、[native_mean.py:209](../../../../hf_repo/src/hf_eval/native_mean.py#L209)。evaluate_native、CLI与batch只有initial_guess(tangent/port_projection)，不是resume-file。见[native_evaluate.py:21](../../../../hf_repo/src/hf_eval/native_evaluate.py#L21)、[evaluate_native.py:13](../../../../hf_repo/scripts/evaluate_native.py#L13)、[native_batch.py:14](../../../../hf_repo/src/hf_eval/native_batch.py#L14)。

底层确有warm-start实现：明确lift_origin、initial_state、initial_R、target_origin，warm lift必须bitwise匹配origin且fixed fluctuation为零。不能写成完全没有warm-start代码。但stage s必须从0开始且非负，物理mean=target_origin+s，初始K=None并重测初始态。见[split_displacement.py:55](../../../../hf_repo/src/hf_eval/split_displacement.py#L55)、[split_displacement.py:88](../../../../hf_repo/src/hf_eval/split_displacement.py#L88)、[split_displacement.py:98](../../../../hf_repo/src/hf_eval/split_displacement.py#L98)、[split_displacement.py:114](../../../../hf_repo/src/hf_eval/split_displacement.py#L114)。从physical1.20直接到1.15需要的下降不能靠[1.20,1.15]或负stage直接塞入现有合同；也不能把任意初始mean塞进不同target_origin并假称等价。不存在已验证的公共saved-state下降续算功能。

## 最近取舍与未证明事项

最近可见功能应是读取14接受保存态，复用现有square实际变形／三分量节点作用viewer；保持partial/failed、无新HP、原身份和压力／夹持限制，不把未接受trial补成卸载帧。这个显示不需要重做平衡。本静查已经定位time_limit与缓存语义，不必再长加载来证明相同事实。

目前没有Newton上限、全回溯失败、LU失败、物理分支失稳／非唯一性或Hu力核／切线bug作为终态原因的证据；也不能反向保证以后增加时间一定会收敛。最后trial merit并不替代新基点验收。不能据这次超时放宽门、改Hu核、重扫参数或延长原卡。

如果保存态显示后仍需要完成回撤，先准备原状态身份、物理初始mean、split representation、multiplier与下降目标的明确续算合同，区分可重复使用的接受缓存和必须重测的切线；再决定最小局部诊断。这里只给粗路线，不实现续算、不创建新数值卡或资源窗口。原24态／48HP仍属原alpha；本次alpha新态HP0及pressure／effective clamp／meshparameter stability／HF5缺口不变。

## 原文件与身份

- [lf_data_preparation/native_interface_001/regularization_sensitivity_001/run_001/alpha_half/result.json](../../../../lf_data_preparation/native_interface_001/regularization_sensitivity_001/run_001/alpha_half/result.json) — SHA `c8be41801bc6f5dff682d148b479d1ada16b38c637203c45abcacbbdc62526cb`
- [lf_data_preparation/native_interface_001/regularization_sensitivity_001/run_001/alpha_half/response.json](../../../../lf_data_preparation/native_interface_001/regularization_sensitivity_001/run_001/alpha_half/response.json) — SHA `42c404b9ee9234d40ea9aa84fe40b2f01e6286a49dbefa374fbe72e25c2e1419`
- [lf_data_preparation/native_interface_001/regularization_sensitivity_001/run_001/execution_receipt.json](../../../../lf_data_preparation/native_interface_001/regularization_sensitivity_001/run_001/execution_receipt.json) — SHA `4782b90e38cc5af1453d72c6fa0e9daddafab009916ebe16ccc0712e297c5e21`
- [lf_data_preparation/native_interface_001/regularization_sensitivity_001/production_launch.json](../../../../lf_data_preparation/native_interface_001/regularization_sensitivity_001/production_launch.json) — SHA `6a8f8595683d8d8fc5bfc5797c3d50c7b1eb245378f1fec70c6a5141cbb72290`
- [lf_data_preparation/native_interface_001/regularization_sensitivity_001/run_001/accepted_progress.jsonl](../../../../lf_data_preparation/native_interface_001/regularization_sensitivity_001/run_001/accepted_progress.jsonl) — SHA `6ed4f56496b9c67fdf996dd8248056a1e5cbb8ee15735119dad438c22f3cc828`
- [lf_data_preparation/native_interface_001/regularization_sensitivity_001/run_001/alpha_half/accepted/013/state.json](../../../../lf_data_preparation/native_interface_001/regularization_sensitivity_001/run_001/alpha_half/accepted/013/state.json) — SHA `9eb90d9f9430917710f972fa4b4c2c590727811e686726d681c8fecccea9d77e`
- [hf_repo/src/hf_eval/split_displacement.py](../../../../hf_repo/src/hf_eval/split_displacement.py) — SHA `6738ace4b617b0103b6d266d9b62b68343cc6d053c52246b6ca0344f72e9dc6e`
- [hf_repo/src/hf_eval/native_mean.py](../../../../hf_repo/src/hf_eval/native_mean.py) — SHA `379856e9b3fc226928361a09d4028c60af7aeabf74b19024d227f806cf351998`
- [hf_repo/src/hf_eval/native_evaluate.py](../../../../hf_repo/src/hf_eval/native_evaluate.py) — SHA `bd6c2e858bfa8d7e4202ecd670275d952759197def94eada99bfb353a80bc942`

其余源码SHA及选中原字段见同目录unload_cost_audit.json。所有审阅产物仅位于外部准备目录。


归档说明：仅把本机源码链接改为仓库相对路径与行锚；未改变原数值/审计结论。外部原说明 SHA256：`de2d818fa0da5e753aaecd42106c9fd0469f28d9c3da395a0435b50c4d08c288`。原普通 JSON 按字节保留。
