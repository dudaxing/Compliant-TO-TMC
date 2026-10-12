# M-ALINK1 保存子段关联候选

当前只完成外部源码准备和 AST 检查；未导入候选或 HF，未调用摘要 API，未读取 NPZ／gzip／图像字节，未生成任何 response、索引、执行回执或数值结果。正式仓库未修改。

默认 `hf_repo/src/hf_eval/native_response.py` 已支持保存态续算。其 `_reference` 能匹配 M-AREF1 的 child 索引 0／1 元数据，`_views` 能匹配 M-RESUME1 的两态实际图像。原 `nested_link_001/execute_nested_link.py` 的一次摘要、一次写入和轻索引流程可复用；旧 view phase、第四 PNG、表格、24 态及整任务表述不适用于本子段。无需修改默认摘要入口、原参考门、原结果或图像。

未来新授权下，`execute_alpha_link.py` 仅调用一次 `summarize_saved_native_result`，再调用一次 `write_native_response`。API 解码原 result／model／reference summary／view manifest／view case summary 五份 JSON；校验原参考声明的 12 份 Python 源码字节和 3 PNG＋1 GIF 字节。包装额外解码前轮发布证明、reference launch 和 lifecycle 三份普通 JSON，核已关闭、已发布的原 4 HP 记录；其余旧 JSON 只校验字节并链接。不存在旧 NPZ、gzip、CSV 或逐态 descriptor 的读取，也不重做 HP 或绘图。

`full_path_reference_pass=true` 明确只覆盖完整两态 child suffix；`full_original_path_reference_pass=false`、`path.full_original_path_completed=false`、`target_response=null` 与父路径 failed／time_limit 保留。峰值为 child 0／original 13 的 resume_origin，终点为 child 1／original 14 的 unloading。原三个 producer flags 和 all-column／contact／clamp／pressure／HF5 均保持 false。两态力和结构范围从默认摘要原文复制，不新增物理投影、差值或资格。

新输出独占 `protocol.output_directory`：`linked_response.json`、`light_index.json`、`execution_receipt.json`。索引给出 repository-relative 结果／原响应／父结果／参考／view／case summary／原 launch、lifecycle 和发布证明链接、现有四项 media、grid／material／结构范围及原 signed 力含义。继承 continuation 元数据含原历史绝对路径；该历史原文不被改写，索引中的实际 artifact 链接可依据恢复后的仓库根解析。

协议 schema 为 `alpha-saved-segment-linked-delivery-card-1.0`；required keys：`card`、`prepared`、`authorized`、`executed`、`source_baseline_commit`、`bindings`、`output_directory`、`result_file`、`model_file`、`original_response_file`、`parent_result_file`、`reference_file`、`raw_view_file`、`view_case_summary_file`、`reference_launch_file`、`reference_lifecycle_file`、`previous_publication_file`、`expected_accepted_states`、`targets_mm`、`original_target_indices`、`selected_state_identity`、`media_files`、`phases.link.helper_seconds`／`outer_seconds`、`sampled_RSS_bytes`。`selected_state_identity` 沿 input seed 原两条记录，`media_files` 沿原四条路径。

未来 bootstrap 必须先读真实 `author/authorization.json`、`direct_human_reply.json` 和本卡 `source_publication_receipt.json`，核实际批准的 HEAD、协议／证明／直接回复原字节、可信 reply context、一次调用／无重试／无 force 与本卡新窗口。缺授权会在创建输出目录及导入 HF 之前停止。准备期协议的 authorized／executed=false 是不可变计划历史，不被修改或当作授权。本轮没有创建这些授权记录。

`STARTED` 从脚本最早语句计时。未来 helper 180 秒／outer 240 秒／采样 8 GiB；原 bindings 后缀只允许 py／json／md／png／gif，禁止数组和压缩档案。helper 的 checkpoint 覆盖检查、摘要、写入、最终 rehash 和回执写出后；outer 协作树采样不由此代码重复实现。仅 `hf_eval` 和 `hf_eval.native_response` 可导入。没有新机械 hook：零新 mechanics 的依据是固定纯摘要源码、导入集合和有限读取范围。

失败只保存真实部分输出和 not_pass 回执，首错停止。若最终 checkpoint 在临时 pass 回执写出后失败，回执改为真实 not_pass；这不是 API 重试。bootstrap／新目录创建之前的异常可能没有 helper 回执，outer 真实终态仍是最终记录。没有自动修复、重复启动或资源延期。

独立数值门和现有图像已由此前实际执行产生。本准备只证明源码和接口可审阅，不证明本卡执行成功或新增科学资格；新的 API 读取关联仍须具体卡发布恢复和直接人类授权。
