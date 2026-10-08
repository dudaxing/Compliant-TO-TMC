这是 B-VIEW2 的外部 source-only installer 候选。`install_saved_view_v2.py` 只依赖 Python 标准库；读取 JSON、逐文件 SHA、AST 和只读 Git，不导入 candidate、NumPy 或 HF，不载入 NPZ 数组，不执行 scientific/render/launcher。

未来一次 root 调用 `python install_saved_view_v2.py --repo <formal-root>` 才会检查完整实际前提并创建同深度的新 `batch_saved_view_v2_001` 控制目录。创建前必须两 V2 worker、F3 outer、原 audit lifecycle 全部 PASS，各 N4/HP8，原生产 52 bindings/54 outputs 完整原 SHA，以及每例 raw/qualified summary、所有 audit 输入绑定、35 份源与冻结副本一致。缺少任何终态文件或不满足检查都在正式写入之前停止。此脚本不会启动新图阶段。

协议按已审 worker 的实际字段生成：`bindings`、`sampled_RSS_bytes`、`phases.view`、`input_directory`、`reference_run`、`view_directory`、`viewer_file`、`adapter_file`、`display`、`cases`、`prerequisites`。其中 `reference_run` 显式指向 V2 新参考 stage；原生产输入和未来图/新 response 仍在旧 production run。额外 `reference_proofs` 只记录生成时已核验的实际 N/HP/result/raw/qualified SHA 与 35 源数量，不取代 worker 运行时前提检查。

预算为一次 whole-helper 120 秒、outer 150 秒、8 GiB 采样 RSS。每例仅四个真实保存态 PNG/GIF，主几何 ×1、显式补位移 ×40，不插值。复制原 F3 launcher，worker 与 adapter 精确使用正式 `docs/evidence/native_batch_saved_view_v2_candidate_001` 已审 pins；不修改旧候选或28个 core。

本次仅写本外部目录、做源 AST 与内容核查。installer 调用、控制 stage 创建、协议冻结、科学导入、NPZ 数组读取、F/T/HP/solve/model/geometry、render、launcher、正式文件写入均为0。root 负责签署明确的独立图卡并在两参考实际 PASS 后决定启用；当前不声明图 PASS。
