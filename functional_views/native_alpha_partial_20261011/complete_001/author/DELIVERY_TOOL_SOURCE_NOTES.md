# M-AVIEW1 执行封账增量交付工具

`deliver_execution.py` 是已静审并发布的 `author/deliver_view_preparation.py` 的普通文件适配。它尚未运行，没有写正式仓库、manifest、Git 提交、远程或恢复目录。本次实际 M-AVIEW1 已完成 PASS；源码准备通过不能代替之后真实文档、最终静审或发布核验。

固定 source commit 为 `7887aa1138f8e46a2b15f47a1060aa7d72cfe651`，stage 为 `functional_views/native_alpha_partial_20261011/complete_001`。旧准备发布证明为既存 `author/M_AVIEW1_source_publication_receipt.json`，原 SHA `e0c5865550a3e24844d7447e6e44ebd272f9d479a798264458599257a6e96cc3`。证明绑定旧 manifest SHA `f185d15d9a9ddfdc5b90533c7d723896ca32ea8082a37bf68db6806a585cd353`，18790 条／9647335892 字节、science 0.5.0。工具以实际旧证明和 `git show BASE` 核 schema 后继承 entries，不扫描旧 9.65 GB 科学归档。

旧阶段 README、PREPARATION_RESULTS、卡片、协议、源码和全部 77 pins 保持原字节。唯一可修改的旧文件是 CURRENT_STATUS 与 RESUME_DEVELOPMENT，两者须完整保留 7887 的原文；其余 allowed delta 必须是 stage 下真实新增文件，包括实际 run、授权、证明、终态审阅、物理解释、人工像素记录、RESULTS／NEXT_STEP、封账收据及本工具。

未来 CLI 与准备工具相同：`finalize --repo <仓库> --external-base <本外部目录>`；root 另行 commit、push、restore 后，再执行 `verify --repo <仓库> --restore <恢复目录> --external-base <本外部目录>`。工具自身不 commit/push、下载、恢复、清理或运行科学代码。

正式 `author/execution_delivery_config.json` 的接口：

- 原通用字段 `allowed_delta_paths`、`protocol_sha256`、`binding_pins`、`front_history`、`final_review_path`、`previous_publication_receipt={path,sha256}`。后者引用上述真实准备证明；bindings 取冻结协议的原 77 项。
- `source_commit=7887...`、`execution_status='pass'`、`documentation_receipt_path`、`review_pins`（至少实际终态／物理／像素三报告的 SHA）。报告的物理解释 status 不必伪装成科学资格 PASS。
- 文档收据沿现有 schema：`status='pass_actual_execution_documentation_closed'`、`execution_closed=true`、source/protocol/execution 字段；`result_sha256` 对新 RESULTS、`next_step_sha256` 对新 NEXT_STEP；`front_history` 与 config 同值，`actions` 仅封账工作为零科学动作，`qualification` 全 false。实际 view 的 14+14 次观察独立由真实 receipts 承载。
- 独立 final review 必须绑定 config SHA、实际 authorized/executed/closed true 与 execution_status=pass；`reviewed_repository_SHA256` 覆盖 allowed delta（除 report 自身）及全部 bindings，`reviewed_external_SHA256` 含本工具。报告自身不自 hash。

工具只读取完成的 ordinary auth／reply／outer／helper／raw view。它核原文授权、批准源提交、protocol SHA、证明 SHA，以及一次完成 exit0／view pass、14 个保存态与观察计数、已有全部输出哈希和原 M-ALPHA1 failed/time_limit/path false/unload false。它不重读 CSV 科学值、不重算差值、不解析 NPZ、不解码或重画像素；这些动作和人工检查由已生成的真实结果与独立终态审阅负责。原没有新 HP、压力、有效夹持、稳定性或 HF5 资格的边界仍保持。

`finalize` 要求当前 HEAD=BASE、main/origin 正确、全部 allowed files 已 staging、无 unstaged／untracked、index 差值恰为两 front＋新 stage 文件、全部新文件实际哈希和最终审阅一致。只写新 manifest 与外部独占 `execution_delivery_delta_verify.json`。`verify` 要求唯一 BASE 子提交、远程 main 同提交、source/restored main/origin 正确且 clean、manifest/config 同字节，核实际新 delta 与旧 entries 完全继承、science version/baseline 不变。输出外部 `execution_publication_receipt.json`，明确实际 `executed_card=M-AVIEW1`、execution pass、authorized/executed/closed true；所有 `new_NPZ_decodes_or_HF_calls_or_plots=0` 字段仅指此 metadata 交付，不抹去前面已经执行的保存态观察。

工具输入须是 root 完成且冻结的实际集合；现在没有制造未来 config、closure／最终审阅或发布通过收据。文本适配来源脚本 `author_delivery_source.py` 只用于外部源码生成与 AST，未导入或执行交付工具。
