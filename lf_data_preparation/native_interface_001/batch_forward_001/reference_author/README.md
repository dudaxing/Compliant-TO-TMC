# 两例新批量结果的独立参考包装（未执行源候选）

本包装仅处理 `native_interface_001/batch_forward_001` 这次完整、真实的新批量结果。生产协议、外层 launch、执行回执和 index 必须全部通过；两个设计都必须完成原任务 `[0,.005,.010,.025] mm`，并通过原生产门。部分批量、旧结果、旧 HP 或 mock 测试均不提供本次参考资格。

`BatchCaseAudit` 直接继承原 `audit_native_mean.Audit.run`、`run_state`、HP80/120、Decimal scatter、端口方向作用及原 GATES。只适配真实回执与任务/模型身份、动态网格维度、整体计时和停止文件。每例参考覆盖全部实际接受态（包含实际二分态），执行新 `2N` 次 HP，不作空间采样。旧 0.025 mm inventory 的模型、任务、方向、零 lift 只供结构比较。运行来源为当前 28 个 HF 文件、5 个原参考数学文件及两个新包装，共 35 个文件。

输出分别为 `run_001/audit/canonical` 与 `run_001/audit/native_fine`，不向生产 `run_001/<label>` 追加文件。原 `Audit.run` 写出的 `summary.json` 原始字节保留。另存 `qualified_summary.json` 完整复制数学检查、门值、状态和 HP 字段，只纠正当前设计别名和本次完整 0.025 mm 任务范围，并绑定原摘要 SHA。该文件不授予全部切线列、能量、压力、接触、HF5、排名或网格收敛资格。

实际生产全部通过且 root 确认实际 N 和预算后，才允许 root 调用 builder。例如在独立 HF 环境中：

```text
python reference_case_builder.py --repo <absolute-clone> --case canonical --time-limit <explicit-helper> --outer-seconds <explicit-outer> --budget-basis <actual-N-and-cost-basis> --root-review <source-review.json> --peer-review <source-review.json>
```

`--repo` 明确路径基础。builder 创建该例新的 contract/protocol；共享 `reference_author` 只首次复制，第二例只核对相同原字节。预算不从旧卡继承，也不预设 N=4。名义四态的 240/270 秒 coarse 与 900/960 秒 fine 仅为 root 的待确认建议，RSS 均为 8 GiB。

root 随后用 stage 原 `launch_pose.py`（保持 ROOT 深度与原字节）启动 `reference_<label>`，并显式传 `reference_protocol_<label>.json`。停止文件始终为 stage 根的 `stop_requested.txt`；不得把 launcher 移到 author 子目录。单次执行，首错停止，无生产调用、修复或重试。

作者后续只读真实闭卡 JSON：新生产 helper/outer 均通过，两例各 4 态、14F/9T/1solver、0HP。root 已明确此次参考分别为 coarse 240/270 秒、fine 900/960 秒，各 8 GiB、各新 8HP；这些计划不等于已经执行的参考。

本目录仅是外部源作者成果：尚未构造 contract/protocol、加载数组、导入候选、执行 HP 或获得新参考资格。生产已关闭，最终参考冻结和执行属于 root 后续步骤。
