# M-ALPHA1 执行期封账／增量交付接口（源码准备，尚未执行）

三份工具只操作普通记录与原字节。`deliver_execution.py` 提供复用的 metadata 函数；另外两份工具只导入这些标准库函数，不导入 HF、NumPy、候选、solver 或 viewer。未来先完成真实终态 reader，再填写文稿和配置；当前不创建实际结果、审阅、配置或发布证明。

## 实际终态后的输入

root 在本外部目录创建 `execution_closure_input.json`，字段如下。所有 `file` 都指向本外部目录已有真实文件，`sha256` 必须填实际原字节 SHA。此处是字段合同，不是已经存在的执行记录。

| 字段 | 实际填写规则 |
| --- | --- |
| `source_commit` | `64a19f7d990d294d09f16145eae946e0edfa1580` |
| `execution_status` | 真实 reader 的 `pass` 或 `not_pass`，不能按文稿愿望填写 |
| `reports.terminal` | `{file: terminal_execution_review.json, sha256: 实际值}`；input_scope 只在真实 completed outer 后运行 reader |
| `reports.physical` | 真实保存结果／部分结果／失败证据解释 JSON，状态以 `completed` 或 `pass` 开头；不增加资格 |
| `reports.visual` | root 实际像素观察 JSON；没有候选图时写明确 `not_available…` 状态和缺口，不能借旧图冒作候选图 |
| `reports.tools` | 独立工具静审 JSON，`status` 以 `pass` 开头，`reviewed_external_SHA256` 至少绑定下面三份工具 |
| `drafts.RESULTS.md` | `{file: RESULTS_draft.md, sha256: 实际值}`，写整体目标、功能、原因、实际进度、数值／力／变形、成本、限制，并链接真实回执和存在的图件 |
| `drafts.NEXT_STEP_REVIEW.md` | `{file: NEXT_STEP_REVIEW_draft.md, sha256: 实际值}`，只依据真实结果规划最近一步，不创建新执行卡或自动重跑 |
| `front_body` | `{file: CURRENT_BODY_draft.md, sha256: 实际值}`，简短当前说明；正文用于三处入口，避免使用相对链接（工具自动加正确链接） |

物理／视觉 JSON 允许失败或缺少图件时的真实解释，不要求虚构完整结果。三份审阅的执行状态与科学含义由最终独立人工静审核对；工具不会把 metadata 交付 PASS 解释为数值 PASS。原生产门、十五目标、额外接受态、实际计数与资源条件均由已审阅 reader 的真实报告承载，不重复科学计算。

## 三份薄工具与顺序

1. `close_execution_docs.py --repo <正式仓库> --input <实际 execution_closure_input.json>`：核真实终态与输入 SHA，独占写 `RESULTS.md`／`NEXT_STEP_REVIEW.md`，更新 `docs/CURRENT_STATUS.md`、`docs/RESUME_DEVELOPMENT.md` 与 stage `README.md`。三处64a原文按完整连续 byte区间保留一次；执行期审阅归档为 `author/execution_terminal_review.json`、`execution_physical_review.json`、`execution_visual_review.json`、`execution_tool_static_review.json`，并生成独立 `execution_documentation_receipt.json`。准备期审阅／回执不改。
2. `configure_execution_delivery.py --repo <正式仓库> --external-base <本外部目录>`：在已实际闭卡的目录中列出真实新文件，保留实际 stopfile／部分产物，冻结所有新文件及三份入口的 SHA；归档同字节 `execution_delivery_config.json`。唯一待生成文件为 `author/execution_final_delivery_static_review.json`，配置不记录自身或该报告的 SHA，不形成 self-hash 环。
3. root 请独立 reviewer 静审实际文档、三处历史、链接、全部现存 delta、终态、授权／source proof 与配置，写实际 `execution_final_delivery_static_review.json` 并原字节归档。其 `status` 以 `pass_actual_results_documentation_and_incremental_delivery_static_review` 开头，包含实际 `config_sha256`、`reviewed_external_SHA256`（至少三工具）和 `reviewed_repository_SHA256`；后者不含尚待更新的 `handoff/repository_manifest.json` 或报告自身。旧 manifest 来源以固定 source proof 和 `git show BASE` 核对。
4. root 精确 stage 配置的 `allowed_delta_paths`，再运行 `deliver_execution.py finalize --repo <正式仓库>`。工具只改 manifest 并在外部写 `execution_delivery_delta_verify.json`；它不 commit／push，不运行科学工具。root 再 stage 新 manifest，显式提交到 main、推送 origin、在已有恢复 checkout 取得同提交。
5. `deliver_execution.py verify --repo <正式仓库> --restore <恢复 checkout>`：核唯一64a子提交、远程同提交、source／restore clean、delta原字节与 manifest 原条目继承，外部生成 `execution_publication_receipt.json`。`execution_status` 原样保留；失败执行也可完成有效的文档发布／恢复。

原18651条／9296517834字节／science0.5.0的旧 manifest 只读普通 JSON；旧科学数据不重新全扫。57 source pins 仍按实际原字节核对。新run产物只作 raw hash，不解码 NPZ 或计算新力、切线、积分、差值、HP、求解或图。三份入口以外不能改写任何原文件，旧 baseline 与 qualification 不升级。没有自动重跑、延期、force、监控／清理框架或修改准备 protocol 的历史 false 标记。

当前动作仅是外部源码／AST准备；运行尚未结束，本文没有声称终态、十五目标、图件或稳定性结论已经取得。
