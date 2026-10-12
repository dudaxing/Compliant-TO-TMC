# M-AREF1 普通执行发布工具接口

`deliver_execution.py` 只准备源码，尚未调用。`finalize` 写增量 manifest 与外部 delta 收据；root 另行 commit/push/恢复后，`verify` 检查远端main、source/restore clean、唯一BASE子提交和全部新delta原字节。BASE为 `e687bdf1ca60edbd0fd044f4f8c990b3b9ccc182`，旧19277文件／9717330143字节清单继承，不重扫历史科学存档。

配置路径固定为 `lf_data_preparation/native_interface_001/alpha_reference_001/author/execution_delivery_config.json`，必要字段：

```json
{
  "source_commit": "e687bdf1ca60edbd0fd044f4f8c990b3b9ccc182",
  "executed_card": "M-AREF1",
  "authorized": true,
  "executed": true,
  "execution_closed": true,
  "execution_status": "从实际终态复制pass或not_pass",
  "protocol_sha256": "实际protocol的SHA256",
  "allowed_delta_paths": ["所有真实新stage文件及docs/CURRENT_STATUS.md和docs/RESUME_DEVELOPMENT.md"],
  "front_history": [{"path":"docs/...", "old_sha256":"...", "new_sha256":"...", "history_start_byte":0, "history_end_byte_exclusive":0}],
  "closed_output_SHA256": {"真实终态冻结的run/outer/log/auth/proof路径":"实际SHA256"},
  "previous_publication_receipt": {"path":"lf_data_preparation/native_interface_001/alpha_reference_001/author/source_publication_receipt.json", "sha256":"实际原proofSHA256"},
  "terminal_review_paths": ["真实普通终态审阅JSON路径"],
  "final_review_path": null
}
```

这是字段示意，不是实际配置或授权。所有路径为ROOT相对完整路径。两front完整旧raw各保留一次；除这两项，BASE已有文件必须保持，阶段prepared README/card/protocol/runner不改。所有真实run文件须明确Git add，连同失败时存在的部分产物；closed_output中run路径集合必须与实际rglob完全相同，不能只保存成功的子集合。

最终终态review的审阅状态可以pass而execution_status为not_pass，表示记录准确，不表示计算通过。可选final_review使用pass前缀、相同execution_status、config_sha256，以及至少覆盖allowed除自身的reviewed_repository_SHA256。与配置／清单相同的原48bindings可在该map继承；其中10旧input NPZ不再raw读，由原manifest条目及真实runner all_bindings_unchanged承载。新科学输出中的NPZ仅流式哈希交付，不解码。

工具PASS分支要求实际completed outer/exit0/stopNone、900/960秒和8GiB采样、helper/summary均pass、机械／工件2态、HP4、child0/1与原执行13/14及资格false。NOT_PASS分支保留实际原因和missing/running/corrupt helper snapshot，不强迫2态／4HP完整、不修复或重跑。两种执行状态都可以取得“出版／恢复通过”的运输收据，execution_status原样保留。

本工具不安装或运行科学、HF、HP、测试、绘图，不更改原960秒窗口、不commit/push或建立恢复checkout。源码只AST审查；任何实际结果、文档、终态报告与配置由root在真实闭卡后冻结。默认hf_repo、science0.5.0、原producer/父状态和资格保持。

未来命令语法仅为用法，当前未执行：`python -B deliver_execution.py finalize --repo <repo> --external-base <this_directory>`；完成root的commit/push/恢复后再用 `verify --repo <repo> --restore <restore> --external-base <this_directory>`。
