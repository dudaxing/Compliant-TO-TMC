# Native 保存态入口兼容性静审

相对 main `d45f6ee92d8a0d6ca740772a1762abdc691489fa` 的八文件候选需要一处最小入口修订后集成：`native_evaluate.py` 在保存态模式中先访问 `settings.time_limit_seconds`，字典或普通对象会产生未捕获的 `AttributeError`，无法保存原合同要求的错误响应。其余入口、物理任务身份与父子语义未发现算法层阻断。

在新集成 overlay 的原 `try` 内、父 defaults 读取前，加 `DisplacementSettings` 类型检查；不符合时抛既有 `TMCError(code="invalid_settings")` 即可。已闭卡 M-RESUME1 候选和力／切线核应保持原字节。一个 mock 负面测试可覆盖 dict/object：禁止父 defaults 与 solver 被调用，检查 `input` 阶段错误码及 `response.json`，无需任何力学计算。

旧合法零起点调用的 None sentinel 回落仍是 `complete/full/tangent`，原 first-increment/16、完整任务路径匹配、缓存保存和 summary 分支保持。保存态入口继承父实际 options／settings，仅允许新时间窗口；直接 mean saved 调用不能默默复用父9000秒。路径使用保存包内相对路径与身份核对，额外几何／任务输入必须匹配原物理来源；原任务和绝对 suffix 不改写。

fresh anchor、原全局索引与子局部索引、`resume_origin`、父 `failed/time_limit` 与子段完成分别保存。当前普通结果 JSON 也保持父 full-path/task/unload 为 false，子只完成 `[1.20,1.15]`，不新增独立HP、压力、有效夹持、稳定性或 HF5 资格。reader 不接任意 warm start 或 continuation 子包再链。

原 `_reference` 严格门按当前 repo 的声明源码字节核验。正式安装 changed mean/controller 后，绑定旧源码的历史 reference 会显示 `mismatch`；原保存证据和 production 状态保留，但不能假设新运行 summary 仍自动认可旧 reference。应保留原门与旧 pins，以普通 JSON 负面用例核这一行为。

非阻断文字建议：`solve_native_mean.py` 的 `--targets`、`--minimum-increment` 与“至少zero”错误文字补充保存态含义。新增纯 mock native CLI flags／成对参数用例也有价值。旧 `python -m hf_eval` 和 batch 入口不在本次 continuation 接线范围内。

本报告只进行了八候选文件与六默认原文件的源码／AST／SHA 对照，以及依赖源码和既有普通 JSON 的身份审阅。没有导入候选、运行测试、读取NPZ字节或数组、求解／绘图，也没有改正式仓库。先前 M-RESUME1 的通过记录是历史证据，不能充当集成后的新回归通过。

准确 source SHA、行号、最小修订与边界见同目录 `ENTRY_COMPATIBILITY_REVIEW.json`。
