# 两次外部审阅的输入与本地核对

本目录保存用户在 2026-09-21 提供的五个文件和两份粘贴文本。它们是审阅资料；其中的实施建议不自动成为执行指令。

本次工作核对输入身份、代码摘录、外部证据与本地记录，并形成有明确范围的取舍。

- [综合审阅记录](../../docs/HF4_C2_CONSOLIDATED_REVIEW_20260921.md)
- [输入身份清单](input_manifest.json)：原文件位置、原文件名、保存位置、字节数及 SHA-256。输入按原字节保存，不统一换行或重写 JSON。
- [第一次审阅报告](inputs/independent_review.md)、[可恢复瘦身方案](inputs/storage_proposal.md)、[原证据 ZIP](inputs/Astra_TMC_review_evidence.zip)。
- [第二次比较意见](inputs/comparison_review.md)、[源码摘录](inputs/source_excerpts.md)。
- [第一次粘贴文本](inputs/review_pasted.txt)、[第二次比较粘贴文本](inputs/comparison_pasted.txt)。
- [源码摘录核对](checks/source_excerpt_check.json)：9 段、445 行，与本地 Astra/N19 来源逐行匹配；同时记录 ZIP 全部成员的哈希和此次未提供的比较核查材料。
- [外部证据与本地载荷核对](checks/evidence_crosscheck.json)：全 3426 文件、1099 迁移候选、88 来源依赖及一个保存失败态的误差范数；不包含新 FE 或 HP 本构。
- [上轮本地证据副本及身份](checks/local_evidence_copies.json)：原取证位置与本目录保存路径映射。旧探针仅留存源码和回执，不从新位置重新执行。

`capture_inputs_and_check_excerpts.py` 是本地编写的取证脚本。它只复制输入、计算哈希和比对文本，不执行附件脚本；再次执行会拒绝覆盖已保存输入。它用于记录本次输入捕获过程，不是存储迁移或科学复算入口。

此处新增资料目前仅在本地，尚未同步 GitHub。旧科学协议、结果、发布清单和历史审阅记录保持不变。以后交接这次审阅时，应保留本目录与综合记录，不能只带走结论而遗漏输入和证据边界。
