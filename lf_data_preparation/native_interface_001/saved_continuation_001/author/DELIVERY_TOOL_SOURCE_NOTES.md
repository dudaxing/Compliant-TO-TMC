# M-RESUME1 执行结果增量交付工具（仅源码准备）

此处仅普通 Python stdlib 源码／AST，未运行 configure、finalize、verify 或任何 HF／NPZ 解码／测试／绘图。数值运行由 root 管理，本工具准备不宣称其终态；所有未来结果字段必须来自 completed outer 及实际终态审阅，不能由工具生成授权或数值 PASS。

两个工具复用上一轮已审增量逻辑：

- `configure_execution_delivery.py`：文档封账及真实报告归档后，仅冻结实际新文件集合、两 front、protocol pins、报告和历史字节范围。运行时写正式 `author/execution_delivery_config.json`，并归档这两个工具及说明／收据／来源与两份普通 peer 报告。
- `deliver_execution.py finalize --repo <root>`：所有 allowed delta 已明确 stage 后，要求真实 index/worktree 变化等于 config，仅新增本阶段文件和两个 front。继承旧 manifest entries，哈希真实新增 delta，写 manifest 和外部 `execution_delivery_delta_verify.json`。不 commit、push 或执行任何科学工作。
- `deliver_execution.py verify --repo <root> --restore <independent restore>`：commit/push/独立恢复由 root 完成后，核 main/origin、唯一 8b456d 子提交、远程同 commit、source/restore clean、新 delta 原字节与旧 entries 原样继承，写外部 `execution_publication_receipt.json`。

BASE=`8b456dcdc2c0566fb2e927175a781712dd5e78ec`，阶段 `lf_data_preparation/native_interface_001/saved_continuation_001`。旧准备 proof 为已归档的 `author/M_RESUME1_source_publication_receipt.json`，其 SHA／commit／manifest/counts/bytes 必须与真实 prepare receipt 一致。旧 18915 entries／9657472556 bytes 仅普通 JSON 继承和元数据求和；不扫描旧 9.65 GB。43 个既有阶段文件、100 pins、science_version0.5.0／science_baseline 保持；README／card／protocol／candidate／测试源码均不能改。两个 front 保存完整 BASE 原字节且仅出现一次，记录旧／新 SHA 与精确字节区间。

## 未来字段合同

封账先由 root 写 `RESULTS.md`、`NEXT_STEP_REVIEW.md`、两 front 及 `author/execution_documentation_receipt.json`。该收据的 status=`pass_actual_execution_documentation_closed` 表示文档封账通过；`execution_status` 必须原样为 completed production outer 的 `pass` 或 `not_pass`，两者不可混淆。还需要 source_commit、protocol_sha256、execution_closed=true、result_sha256、next_step_sha256、front_history、review_pins、actions（本封账 metadata-only 全0）、qualification（不授新增物理资格，全false）。实际机械调用已在原执行收据，不得混入封账 actions0。

`author/execution_terminal_review.json` 至少给出 status（真实终态元数据审阅通过的 pass 前缀）、execution_status、outer_sha256；需进入 documentation.review_pins。其作用是普通终态分类，不重新计算机械门。数值 NOT_PASS 也可有通过的终态／文档审阅记录。其他实际物理解读及像素观察／不可用记录同样原字节绑定。

configure 需要外部 `execution_delivery_tool_static_review.json` 与 `execution_documentation_physics_review.json` 的 pass 前缀普通审阅，之后归档并纳入 pins。config 字段沿用 allowed_delta_paths、binding_pins、protocol_sha256、front_history、previous_publication_receipt、documentation_receipt_path、review_pins、final_review_path；加 source_commit、真实 execution_status、authorized/executed/execution_closed=true 与 terminal_review_path。唯一未来文件是 `author/execution_final_delivery_static_review.json`，不要求自身哈希。

最终普通终审 JSON 需 config_sha256、status pass 前缀、真实 execution_status 及 authorized/executed/execution_closed=true、reviewed_external_SHA256、reviewed_repository_SHA256。后者至少覆盖全部 allowed delta 除自身与100 pins；前者绑定这两个未来工具及实际审过外部来源。工具只核实际元数据／原字节，不赋予独立 HP、压力、有效夹持、网格稳定或 HF5 资格。

## 成功和失败的分别处理

唯一 completed outer 为首要状态。成功才要求 helper pass、五项测试／单次 API+构模+求解+缓存保存+摘要+viewer、N=2..9、已存原 cached gate passed、原索引13／14／resume_origin、三 PNG／N帧 GIF、原父失败标记、原 F/T bookkeeping 和输出 SHA 原样一致。检查只是读取现存 JSON 已保存字段，不计算新科学值，不解码 NPZ／图像。

NOT_PASS 仅要求真实 completed outer 非成功和独立终态记录匹配。真实 helper 可能 missing、running、provisional pass、partial 或 malformed；原样哈希归档，不能强求完整 helper/result/view 或虚造图／响应。目录中的实际产物由 config 精确增量集合保存，终态审阅负责说明缺口。本工具不重试、修复、延期、force，不改父 failed/time_limit 或完整路径资格。后续基于实际终态作最小适配时，需重新静审并绑定修改后的工具 SHA。
