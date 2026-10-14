# L-PREP1 增量执行发布工具源码

`publisher_execution.py` 薄改已实际使用的 M-PREF1 发布工具，仅编写并做 AST 检查，尚未运行或写正式仓库。基线为已发布 main `004efde5b2b9952bc4a9e6c7e756b8a520f24cde`；原 manifest `f788e35d…`，20082项／10498769295 bytes。没有预设实际执行成功、产物数量或未来提交。

外部调用接口沿用 `publisher_execution.py finalize|verify --repo <formal_root> --restore <restore_root>`。正式副本只作恢复资料；必须从正式库外运行，后续发布证明落外部。工具不 commit/push/pull；finalize 只在 root 已精确 stage 后更新 manifest 和外部 delta receipt，verify 在 root 实际提交、推送和恢复后核 main/origin/父提交/clean/精确增量，输出真实 publication receipt。

最小实际文件接口：

- `author/source_publication_receipt.json`、`direct_human_reply.json`、`authorization.json` 原授权／源证明；协议原23 bindings保持，3旧NPZ只继承 manifest 身份＋stat。
- `preparation_launch.json` completed 真实终态，`run_001/execution_receipt.json` 的 actual counts、安装记录与原窗口 `outputs={仓库相对路径:{sha256,bytes}}`。失败也按实际 not_pass 保存，不要求不存在的成功 view；但任何实际科学文件缺少封存身份则阻断，不补 hash。
- `author/execution_documentation_receipt.json`：`source_baseline_commit=004ef…`、`actual_execution_closed=true`、`actual_execution_status`与outer一致、两份 `front_history`（path/old_sha256/new_sha256/history_start_byte/history_end_byte_exclusive）。两前台保留 source BASE 原文连续恰好一次。
- `author/final_execution_review.md` 先写普通正文，不放JSON SHA；再写 `final_execution_review.json`，字段 `status` pass前缀、`blocking_findings=[]`、`authorized/executed/execution_closed=true`、真实 `execution_status`、`protocol_SHA256`、`declared_binary_identities={name:{path:name,sha256,bytes}}`、`reviewed_repository_SHA256`覆盖全部普通增量含MD，唯独不含JSON自身。独立终态与实际文稿审阅可作为本阶段普通资料归档，没有新增框架要求。

PASS分支只核已冻结卡的实际记录：2安装、3真实准备、2API、1同解释器CLI、9负例、3对账、11 archive opens、1图，各started/completed一致；三case掩码/任务对账及9反例结果保存。44字段读取仍静态依据，不把字段未插桩改成观测通过；零model/F/T/solver/HP是源码范围事实，mechanical_hooks_monitored保持false。图保持undeformed／声明未应用，无独立参考/HF5资格升级。

增量仅新阶段普通及封存科学文件、两front、两个实际存在的全新默认PY、manifest。两新默认PY必须与候选 d37ab7ea…／468384ec…同字节；若实际 partial 无正确安装身份，报告阻断，不覆盖或回滚。所有原默认、`__init__.py`、旧阶段、卡／协议及旧结果由精确 Git delta 和原 manifest 条目继承保持。没有旧科学遍历/hash/header，也没有全库字节重扫。

新 NPZ／PNG只用真实 closed helper seal 的 sha/bytes及当前stat，恢复树也仅stat＋原producer身份，不声称重新核数组或媒体字节。普通 JSON/PY/MD/log/txt可 raw SHA。工具拒绝不在封存库存中的新科学文件；缺口须如实处理，不能闭窗补科学 hash／解码／图。原 manifest 行采用原命名 ordinary_manifest_files/bytes，是总库存条目及字节的元数据计数，并非本工具读取了全部库存。
