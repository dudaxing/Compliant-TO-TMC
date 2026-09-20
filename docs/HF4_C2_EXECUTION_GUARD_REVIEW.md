# HF4-C2：执行前隔离停止门只读审查

日期：2026-09-21。范围：源码和协议的只读比较；未运行 FE，未修改冻结 builder、runner、audit 或协议。本文保留原发现，并在第 5 节记录最终 v3 修复的只读复核通过。本轮发现与修复均发生在首个 FE 前，**不是有限元计算失败或科学结论失败**。

## 1. 已核查的物理构造与保存语义

`contact_c2.py` 的三个正式 case 与 v1/v2 科学字段一致：padding=2.5、h=.125、整底边驱动；padding=2、h=.125、严格外底边自由；padding=2、h=.0625、整底边驱动。实体、间隙、障碍、面外厚度和材料常数保持。\(k_r\) 用固定 Lref=2；扩大域宽没有改变它。

outer-free 保留所有自由 DOF 的 lift，但 prescribed direction 只赋 fixed DOF。释放的是 x<0 或 x>2 的底节点 uy；x=0、2 保持实体底面的运动约束。top/bottom 反力组不含 free DOF；body 和 whole mean 是独立参考弧长测量。

`run_contact_c2.py` 调用冻结 split affine solver，使用共同七目标；每个 accepted 状态单独保存 NPZ 及完整 record gzip，步骤索引绑定两者，结束时保存完整 controller gzip 并双重绑定至 stage result/completion。独立 auditor 校验模型、初始 split、阶段/目标库存、每条 record 与总 controller 的一致性，并使用原 C1 门。没有发现明显的物理单因素构造或 DOF 方向执行偏离。

## 2. 初始来源版本差异：已由执行前修订记录

审查 v1 时，`implementation_sha256` 中 auditor 旧 SHA 为 `bd191957b9086f3e3ec472c108d2d4890a2173aeea04c80808602c4db3893c14`，实际文件已加固为 `50bcbe18d67d62ea1bce621c9bfd2c1c6247dbe2b095a965dab42c00bc47e543`。隔离器会因来源门正确拒绝执行。

主任务随后明确 v1 未执行，保存 `preflight_source_amendment.json`，冻结 v2。只读复核确认 v2 SHA 为 `174715e7c99b09cf3686e7eb86811a6460b1ac7cd6a6ca6af4d861bfb1136934`，其所有实现哈希与当时实际文件匹配；v1→v2 未改变科学参数、门槛、预算和次序。这是执行前版本一致性修订，不记为科学样本或 FE 失败。v2 也因下述停止门问题保留为未执行，等待后续冻结版本。

## 3. 复核问题：前序独立审计的进程状态与证据绑定未参与继续门

**来源定位。** `hf_repo/scripts/run_contact_c2_isolated.py`，SHA `f544417e8744759fb23a61d6b82b40aac4a9a7f98b890c8eb6dfd9b597db38dd`，原文件约第 32–51 行。准备下一个 `--action solve` 时，它读取 `*.solve.receipt.json`，对每个前序路径只要求：solve `returncode==0`、未超时、`audit.json` 存在且 `status=="pass"`。

**具体遗漏。** 它没有在这个继续门中要求对应 audit 外部回执成功，也没有重验前序 audit 的输入/helper 和逐状态输出哈希。`audit.json` 的 pass 表示该文件写出时的内部检查结果，不单独证明 audit 子进程成功退出或其绑定此刻仍有效。

可触发的两类情况：

1. audit 写出 pass 文件后进程超时或异常退出，已有 `.audit.receipt.json` 明确失败；原下一 solve 门仍可能放行。
2. audit 完成后其输入或逐状态审计输出改变，而顶层 `audit.json.status` 不变；原下一 solve 门仍可能放行。这不能满足协议“前序独立准入成功且源证据有效”的继续条件。

此处是根据分支逻辑提出的可证伪执行遗漏，未构造失败回执、未改实际证据，也未声称已经发生任何绕过。主任务已接受该问题，决定在首个 FE 前修复 wrapper、新增针对性测试，保留 v1/v2 并重新冻结。

## 4. 必须验证的继续条件

下一候选启动前，除现有 solve 成功、次序、attempt cap 和累计时间预算外，修订应绑定并检查：

- 对应 audit receipt 的 schema、action、case、run 身份和同一协议 SHA；`returncode=0` 且 `timed_out=false`，日志与回执绑定一致。缺失或失败必须停止。
- audit 文件本身与该成功回执的身份绑定；如果回执新增 `audit_sha256`，应核验它，从而将进程完成证明和读取的具体结果连起来。
- audit schema、case、路径身份和 `status=pass`；`input_and_helper_sha256` 的所有当前输入/helper 哈希、`detail_output_sha256` 的所有逐状态输出哈希。
- 前序 audit 的相对输入路径可能包含保存场准入清单所绑定的既有 C1 资料；允许范围应是明确的同一完整实验/仓库树，不能错误地把这些合法兄弟证据路径全拒绝，也不能允许越出证据树。逐状态输出只允许在其所属 run 内。
- 原始目标完整性与 run/stage completion 等库存链继续由正式 audit 证明；状态 JSON、进程回执或文件名任何一个都不应单独取代它。

还须保持：只在同一个实验根目录串行执行，失败 artifact 和日志不覆盖，无自动重试/参数搜索；外部超时后不能因为目录中有部分结果就进入下一候选。本审查不要求另开算例，也不借修复改变数值门槛。

## 5. 修复后复核状态

**通过；可按冻结三案、次序和预算执行。** 该判断仅针对所审阅执行门，不预判任何 FE 或独立审计结果。本轮没有代替主任务启动算例，也没有重复运行测试。

只读源码确认新增 `validate_previous` 在下一 solve 前逐条检查：两个 action 回执的 schema/action/case/run、`returncode=0`、`timed_out=false`、协议和日志哈希；随后用 audit 回执新增的 `audit_sha256` 绑定实际结果，核对 audit 的 schema/case/status，并重验非空 `input_and_helper_sha256` 和 `detail_output_sha256`。相对 POSIX 输入路径不能越出同一 workspace；逐状态输出不能越出所属 run。原先“写出 pass 后 audit 超时/异常仍可继续”与“证据后变更仍可继续”的分支已被关闭。

现有 attempt cap、固定顺序、无同 case 自动重试、累计时间预算和拒绝覆盖证据仍保留。使用条件依旧是同一完整实验根下的**串行**调用；该工具不是并发任务调度器。正式 auditor 仍负责完整目标/accepted/controller/completion 库存链；隔离器不替它重算 FE。

本轮实际重算并核对：

|证据|SHA-256 / 核对结果|
|---|---|
|`hf_repo/configs/contact_c2_v3.json`|`b17c8328dd1e350563b70305c0b311c8d38c9c0ef68c08b85fac5f13604d0b4d`；全部 `implementation_sha256` 当前匹配。|
|修复后 `run_contact_c2_isolated.py`|`80ddbcdfedfbd9dbd22a9cf43a291f8f6f324a8366070adfbf3f82f921c7d82b`；v2→v3 唯一实现变化。|
|`hf4_c2_diagnostics/saved_field_admission_r3.json`|`d4c8700c60d19a2b2d15462f1d9e5b45eb9318499f435cf5ddb41036df7bdfef`；其 166 个绑定输入全部重算匹配。|
|`hf4_c2_diagnostics/preflight_tests_003.json`|`428f9afe683513d67891fd7941e1864844e8a42777c2cfb3089fe8d880a6f166`；现有回执为 103 tests、0 failures、returncode 0。|
|`hf4_c2_diagnostics/preflight_tests_003.xml`|`4c2bc984d58943a223f790767a0f315d546f35087808660891e8e77833b578c4`；JUnit 103 tests、0 errors、0 failures、0 skipped，与回执一致。|
|`hf4_c2_diagnostics/preflight_tests_003.log`|`a71a1e2dbffeb8fa65eb819e887299c4bdb44bca2d480deb06830ccb87f3c43e`；与回执及准入清单一致。|
|`hf_repo/tests/test_contact_c2_isolated.py`|`8bafc11d62b1236ad6dda472dfab22b82cab7424550cfaed1d97fa3e0090d434`；1 个正常继续测试、8 个 timeout/exit/missing receipt/audit/detail/source/log/protocol 改变拒绝测试，实际测试源码与回执绑定相符。|

v2→v3 的科学字段、病例、七目标、帽函数、次序、数值门与预算没有改变，差异限于 wrapper、准入及冻结修订元数据；[preflight_guard_amendment.json](../hf4_c2_diagnostics/preflight_guard_amendment.json) 保存“v1/v2 未执行、无 FE、修复原因”记录。冻结 [公式审查](HF4_C2_FORMULATION_REVIEW.md) 的 SHA 仍为 `9017d22696662bfbf3b83aabe872f5d375d70f12053e6a1d15bf57bdc33ee4a8`。

预先科学解释另存 [HF4_C2_INTERPRETATION_RULES.md](HF4_C2_INTERPRETATION_RULES.md)，不因这个执行修复改变。
