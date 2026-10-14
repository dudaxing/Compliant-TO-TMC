# L-LINK1 候选作者记录

依据 main `909f8acee95279e449e09961fd4fe68fed9d688f`。本轮只写外部候选、解析四份 Python AST、核对源码差分；没有导入候选、运行测试或 API、安装默认文件、读取科学归档或媒体。作者记录不能代替独立静审或实际执行证据。

## 功能变化

`native_response.py` 只修改 `_reference`。该函数之外的原字节完全一致，公共函数签名和 writer 保持。真子集参考按实际 `index` 查找生产 `states[index]`，严格整数且唯一、非空、有效范围；核实际 SHA、目标、状态及每态 2 HP。报告 count／全局 2M HP、result/model 输入身份、原 source bytes、全单元／DOF声明及已有显式 selection/population 仍须一致。

合格部分参考返回 `matched_partial`、`selected_reference_pass=true`、实际匹配 indices/count 及生产 population。原 `accepted_reference_pass` 只允许全部接受态均匹配，`full_path_reference_pass` 还要求生产完整。原全覆盖顺序语义保持；无参考保留旧状态和资格含义并附加 coverage 字段。新增字段使 JSON 有附加说明，不能称整个旧响应字节兼容。所有原 all-column/contact/clamp/pressure/HF5 资格仍为 false。

## 冻结的下一卡运行范围

建议 helper180／outer240秒、采样8GiB；tests60秒含在helper内。一位 child、一次 failfast 测试、一次真实公共摘要、一次响应写入、一次轻索引写入，然后全部通过才安装一个默认 `native_response.py`，其字节须等于刚测试和实际调用的候选。默认旧 SHA 单独放 `source_before_installation`，不放 immutable bindings，避免将合法安装误报为原字节变化。

16 个固定 unittest 方法预定调用 **23次 `_reference`**，只用新目录内普通 JSON／源码 fixture，包含无/全/部分参考、未完成生产路径及 count/HP/index/SHA/目标/身份/来源/范围/显式声明反例。这不是16次科学试验；测试不调用公共摘要。真实 API 另有 **一次 `summarize_saved_native_result`**，其内部再调用一次 `_reference`。helper 分开记录真实调用和 unit 次数，每个方法前后检查 tests60及整个helper资源，首错停并保留实际部分计数。

实际关联复用 L-FWD1 同25态、L-REF1 indices13/16以及已有生产3PNG／25帧GIF和参考误差PNG。五个媒体只允许新窗口内原始字节身份检查，无解码、像素检查或重绘。当前编写阶段只读 producer 普通封存记录，不读媒体。无 NPZ／gzip／CSV、F/T/HP、构模、平衡路径、回滚、删除或默认其它文件修改。原生产 completed=true、原 reference full25=false、原历史文件字节保留。

## 文件与协议对接

- 外部 `native_response.py` → 正式 stage `candidate.native_response.py`，默认目标仅 `hf_repo/src/hf_eval/native_response.py`。
- `execute_lf_link.py`、`launch_link.py`、`test_partial_native_reference.py` 原字节进入正式 stage。
- `source_author_receipt.json` 列四份 SHA、精确16方法名称及实际AST结果。
- `protocol.schema_version='lf-selected-reference-linked-delivery-card-1.0'`，`card='L-LINK1'`；`prepared=true/authorized=false/executed=false`。
- `phases.link` 含 helper180、outer240、tests60，以及完整相对 argv；`candidate_source/tests_source/expected_test_methods/output_directory` 明确一次调用源及唯一新 `run_001`。
- `source_before_installation={path,sha256}`；`bindings` 仅声明普通源码/JSON/MD/5媒体；`inherited_media_bindings` 五条 `{sha256,bytes}`。
- 实际 result/model/original_response/reference/raw_view/view_case_summary/reference_observation/reference_observation_media/production_receipt/reference_execution_receipt 文件键与 root 统一。
- `production_accepted_states=25`、`expected_reference_states=2`、`selected_accepted_indices=original_target_indices=[13,16]`、`targets_mm=[1.20,1.05]`。
- `authorized_execution_source_commit` 必须取将来实际发布的候选提交，与 actual direct human reply／source publication proof／运行 HEAD 对齐；909 是准备基线，不能冒充未来已批准源码。

首次外部字符串替换生成器误假设 CRLF，定位失败并在写候选前停止。之后外部复制原文件、仅局部修改 `_reference`；该源码准备修訂不是卡执行或修复重跑，正式树未修改。相关 diff 保存在候选目录上一层 `native_response.diff`。
