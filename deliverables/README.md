# 发布附件导航

当前与历史必要证据附件位于 [GitHub Release：hf-history-0.5.0](https://github.com/dudaxing/Compliant-TO-TMC/releases/tag/hf-history-0.5.0)。

```text
python tools/handoff.py fetch-evidence
python tools/handoff.py verify --full
```

从仓库根目录运行。命令核对整个附件及其中每个文件的 SHA256，按原相对路径恢复历史数组/大 JSON，已有不同文件会拒绝覆盖。当前原样 `HF4_repaired_evaluator_and_evidence.zip` 保存到本目录而不解压覆盖主分支。

其余旧 ZIP 不重复上传，其大小/hash/原 Git 身份仍在本目录各阶段 release manifest 中。新阶段 bulk 附件的独立身份在 [evidence_assets.json](../handoff/evidence_assets.json)；不能混用新旧 hash。完整说明见 [公开内容与来源](../docs/SOURCE_MATERIALS_AND_PUBLICATION.md)。
