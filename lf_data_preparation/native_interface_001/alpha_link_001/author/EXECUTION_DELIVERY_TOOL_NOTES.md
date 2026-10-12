# M-ALINK1 执行增量交付工具

`deliver_execution.py` 为普通 metadata 工具源码，尚未执行 finalize／verify，也未修改正式仓库、生成发布证明或调用 HF。它沿用已发布本阶段 `author/deliver_preparation.py` 的小增量方式，适配真实已关闭的 M-ALINK1 PASS；不宣称可发布未经解释的失败终态。

基线固定 `1e639641625b4d0f92eb84aff4b4c6fdb05d0171`。从该 commit 的 `handoff/repository_manifest.json` 继承原 19362 条、9885238132 字节及 science 0.5.0／b1334bb。原 stage 21 文件和所有其它旧条目保持，唯一可修改的旧文件是 CURRENT_STATUS 与 RESUME_DEVELOPMENT；新增文件只能在 alpha_link_001。工具只哈希新的 JSON／PY／MD／LOG 和两份 front；数组、压缩档案、CSV 及原媒体不被读取或哈希。原 30 binding 身份来自继承 manifest 与唯一运行的 `all_bindings_unchanged`，不重做已关闭 API 的输入检查。

输入为正式 `alpha_link_001/author/execution_delivery_config.json`，required keys：

- `source_commit`：上述 source 基线。
- `protocol_sha256`：实际冻结协议 SHA。
- `allowed_delta_paths`：全部新文件及两 front，含 config 和最终审阅自身。
- `front_history`：两行 `path/old_sha256/new_sha256/history_start_byte/history_end_byte_exclusive`；旧 raw 全文须精确保留一次。
- `closed_output_SHA256`：至少覆盖 run_001 三 JSON 的 repository-relative 路径／实际 SHA，可额外覆盖 launch／log 等已关闭普通输出。
- 可选 `review_pins`：actual 普通报告、文档 receipt 等 repository-relative 路径／SHA。
- 可选 `final_review_path`：若提供，文件必须真实存在、status 以 pass 开头、绑定 config SHA；其 reviewed_repository_SHA256 必须覆盖全部 allowed 除自己且不得 selfhash。

将来人工流程先明确 stage 全部 allowed。`finalize --repo ROOT` 核准确 cached diff、无 unstaged/untracked、原 manifest、真实 auth／回复／source proof、唯一 outer/helper PASS／预算和停止状态、原两态参考及父原路径 false、三个原输出和文档历史；只新增 manifest 内容和外部 `execution_delivery_delta_verify.json`。不会 commit、push、restore 或运行科学。

人工 commit／push／恢复后，`verify --repo ROOT --restore D:/hf-restore-20260930` 核新 commit 是 source 基线的直接子提交、main／origin 原地址、remote main 相等、源与恢复均 clean、准确 commit delta、manifest 同字节和新 delta bytehash。旧条目只检查继承 metadata，不扫描旧大数据字节。通过后才写外部 `execution_publication_receipt.json`，标实际 executed_card=M-ALINK1／authorized／executed／execution_closed=true／execution_status=pass，whole_HF5_complete=false。

资源镜像核查沿原停门的等号允许规则：outer elapsed≤240 秒、child terminal wall 与 helper elapsed≤180 秒、采样 RSS≤原 8 GiB。只是原终端合同的普通记录核查，不收紧原执行门。

工具只核真实普通记录和身份，复用原审阅，不新增数学/API 门或任何资格。实际两态参考 pass 仍仅为 child suffix；原 alpha 父路径 failed/time_limit、整原任务未完成、压力／有效夹持／稳定性／HF5 未认证。完整 stage 输出只有 linked_response／light_index／execution_receipt 三 JSON；没有新媒体。

当前仅 AST parse。工具模式、发布证明及恢复校验尚未运行；所需 config 与最终审阅由 root 基于真实封账资料准备。
