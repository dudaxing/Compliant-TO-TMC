# L-FWD1 薄执行包装源码（未执行）

`execute_lf_forward.py` 和 `launch_lf_forward.py` 以已实际使用的 saved_extension_004 execute_unload.py／launch_unload.py 为模板。原模板保留在原目录；本次仅外部新源码及 AST 检查，没有导入 HF、构模、F/T/HP/求解、测试、数组字节/header/hash、图或正式仓库写入。

## 最小改动

- 正式拟 REL 为 `lf_data_preparation/native_interface_001/lf_forward_001`；card L-FWD1、schema `prepared-native-lf-forward-card-1.0`、输出标签 lf_fine_forward。
- 删除 saved parent/reader/defaults、扩展任务与祖先匹配分支；唯一输入是 L-PREP1 fine 已保存 derived geometry、task 和普通 input_manifest。核归属和已有身份，不再转换 LF、扩域或提前构模。
- 一次 `evaluate_native(geometry_file, task_file, production, repo_root=root, targets=None, settings=DisplacementSettings(**protocol['settings']), **protocol['options'])`。不传 saved_result、selected_state_index 或 extend_path。原 API 内构模通过后才求解，typed 构模失败仍由 API 写真实 response；没有第二次 constructor 预览。
- 原25目标、固定方形工件及所有 task 字段不改；原 settings 逐字段核除clock相等，controller 9000→18000秒。明确原已用 mechanical/chunk256/port_projection，不用零起点 API 的隐式 complete/full/tangent 或 first_increment/16 默认。
- 保留原 NativeMean alias 计数、accepted callback、缓存生产门、缓存保存/摘要不得新增F/T的检查。新16项计数为 api/model/solve/force/tangent/save/summary/view_child，各 started/completed。F/T次数随实际 controller trials，允许原invalid-J/Armijo/二分；首终态失败不重试。计数不是全系统hook，`mechanical_hooks_monitored=false`。
- 成功结果原25目标完整、zero origin、无continuation；本次真实 path_completed/loading_peak_reached/task_target_executed 可true，和独立参考/压力/夹持/HF5资格分开。旧 task 标签仅模板历史，不称旧几何的 alpha-only 试验。
- 成功后原纯 viewer 一次新进程，reference 不提供、--repo 是正式hf_repo；用实际保存 result/model/states/forces 填新 view_protocol。三PNG及实际N帧GIF原样，N≥25允许原二分，不重读保存切线/矩阵、不新F/T/HP。失败不启动 viewer；view失败保留生产成功但整个卡 not_pass。

## 协议所需字段

`schema_version/card/source_baseline_commit/bindings`；`geometry_file/task_file/input_manifest`；`settings_source_result`=原 saved_extension_004/run_001/unloaded_alpha_half/result.json；`gates_source_protocol`=原 saved_extension_004/protocol.json；`task_sha256/targets_mm/settings/options/gates`；`candidate_directory=REL/run_001/lf_fine_forward`、`view_directory=REL/run_001/view`；`pure_view_bindings/viewer_source`。只有 prepared HF geometry NPZ 的四authority字段是生产输入，没有旧 LF／保存态／旧矩阵warm start。

资源 `controller_seconds=18000`、`view_seconds=600`、`phases.production.helper_seconds=19000/outer_seconds=19060`、sampled_RSS_bytes=8GiB；phase还沿原launcher提供实际 argv。helper最早模块clock包括imports、bootstrap/身份、一次API、缓存保存、viewer与seal。viewer可用额度取 min(600, helper剩余)，没有独立额外窗口，controller额度不覆盖保存/图的clock由wholehelper兜住。

auth/reply/source proof必须未来真实形成，使用 authorized_execution_source_commit 关联真正已发布HEAD；sourceproof中 prepared/未授权/未执行是假设之前的历史事实，不改原字节。未来 proof、批准、commit和科学PASS没有占位。实际监督继承 Popen/psutil进程树采样、stop file、等待真实退出；没有 SUP2、TermJobObject、强制终止或 OS硬cap。

## 输出和终态

launcher写 production_launch.json／production_stdout.log／stop_requested.txt（仅需要合作stop时）。helper写 run_001/execution_receipt.json、accepted_progress.jsonl、lf_fine_forward保存包、view_protocol.json、view_child_stdout.log及原viewer全部输出。封存 outputs={仓库相对路径:{sha256,bytes}}在原开放whole窗口一次完成；若窗口关闭只保既有文件和 incomplete/skipped 记录，不晚补科学hash或seal。未完成API操作／任意异常不能保证全部状态都已保存，记录真实partial。source binding初末检查、helper实际RSS和child/outer wall保持原模板规则；迟到PASS、残留stop或viewer失败不得整体PASS，无修复重跑、删除、回滚、延期或force。

引用模板源 SHA：execute_unload.py `6d85f784a038c0f014c9cfc192aa1f6dcd4b379cf336c57e007cdf7eb18a96b8`；launch_unload.py `9ec7eff74a42fa17ee74d79c7d27583f7ea2194fa655ededda7e763e0281cf22`。本次没有修改这些旧源及原pure viewer。实际开卡之前还须联合源码/协议静审与真实直接人类授权；AST通过不授模型兼容或数值资格。
