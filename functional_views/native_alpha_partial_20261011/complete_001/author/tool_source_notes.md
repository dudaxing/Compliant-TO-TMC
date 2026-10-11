# M-AVIEW1 增量交付工具源码说明

`deliver_view_preparation.py` 沿用此前 α 准备／执行交付的普通文件机制。本轮只准备外部源码及 AST；工具尚未运行，没有写正式仓库、manifest、提交、推送、恢复副本或数值结果。

固定 parent 为 `9e2e37cce7f0441af042337d1c26c50ae660acc0`，新 stage 为 `functional_views/native_alpha_partial_20261011/complete_001`，manifest 为 `handoff/repository_manifest.json`。唯一可改旧文件是 `docs/CURRENT_STATUS.md` 和 `docs/RESUME_DEVELOPMENT.md`；它们必须完整保留 BASE 旧字节。其余改动全部是新 stage 的新增文件，manifest 自身独立处理。

未来 CLI：

```text
<Python> -X utf8 -B deliver_view_preparation.py finalize --repo <仓库> --external-base <外部准备目录>
<Python> -X utf8 -B deliver_view_preparation.py verify --repo <仓库> --restore <恢复仓库> --external-base <外部准备目录>
```

`finalize` 前必须由 root 完成真实普通准备、文档、独立最终静审及全部允许文件 staging。脚本读取正式 `author/preparation_delivery_config.json`，字段合同为：

- `allowed_delta_paths`：精确、无重复的新 stage＋两 front 文件路径列表，含 config、工具和最终审阅本身；排除 manifest。
- `protocol_sha256`、`binding_pins`：实际冻结协议原 SHA 与原 `bindings` 字典。旧 bindings 只对继承 manifest 身份，新增 bindings 对本次真实 delta 身份；不重新扫描旧科学归档。
- `front_history`：两行，沿既有 schema 的 `path`、`old_bytes`、`old_sha256`、`new_sha256`、`history_start_byte`、`history_end_byte_exclusive`、`old_body_preserved_exactly=true`。读取 BASE 的完整旧 front，核对应字节区间与新 SHA。
- `previous_publication_receipt`：`{"path":"<stage>/author/M_ALPHA1_execution_publication_receipt.json","sha256":"9bede98281b5b63233f12c6add0b92f75d215eb9042e74ea5ef54d9ecd1ccc38"}`。它必须原字节绑定真实旧发布收据，保留其 execution_status=not_pass；不能将发布恢复通过解释成旧数值执行通过。
- `final_review_path`：新 stage author 内实际已存在的独立审阅 JSON，status 以 pass 开头、authorized/executed 均为 false、`config_sha256` 等于实际 config，`reviewed_external_SHA256` 绑定此工具及实际审阅的外部源，`reviewed_repository_SHA256` 至少覆盖全部 allowed delta（除最终报告自身）与全部 binding_pins 路径，并核其 manifest 身份。最终报告自身不自 hash。

工具通过 `git show BASE:handoff/repository_manifest.json` 取得旧 manifest 原字节，核旧收据 manifest SHA、18761 条记录／9646933366 字节的真实旧 schema 和科学版本 0.5.0（实现以真实收据计数作核对，未硬编码归档大小）。只继承旧 entries 和其 science_baseline_commit；不进行旧 9.65 GB 文件哈希扫描。

`finalize` 要求当前 HEAD=BASE、main/origin 正确、无 unstaged／untracked 文件、index 改动与 allowed 完全一致、新阶段文件集精确、没有授权／run／view 回执。对 allowed 的真实文件哈希，然后写新 manifest 和外部独占 `preparation_delivery_delta_verify.json`。没有 git commit、push、checkout、清理或任何科学动作。

root 随后另外执行提交、推送及恢复。`verify` 只核唯一 BASE 子提交、remote main 同提交、source/restored main 和 origin 正确且 clean、manifest/config 原字节相同、git diff 范围精确、全部新 delta 文件在两树的实际身份相同、其余旧 entries 完全继承、科学版本／baseline 不变，并重复普通准备／历史／静审字节合同。输出外部独占 `publication_receipt.json`，其中 `prepared_card='M-AVIEW1'`、prepared=true、authorized/executed=false，供以后真实授权记录绑定。

正式执行授权、NPZ 解码、观察、GIF 或 PNG 均不属于此工具。新 worker 后段若错误，原 raw `view.json` 可以已经 pass 而新 α 显示收据尚缺、outer 为 not_pass；以后终态应记录实际组合，不能承诺所有失败都有完整显示收据。
