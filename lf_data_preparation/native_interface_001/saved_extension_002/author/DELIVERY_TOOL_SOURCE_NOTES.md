# M-EXTEND2 执行后增量交付源码准备

本工具只准备 ordinary publisher 源码，未执行、未写formal、未读取live run或科学数组/媒体。父代理的唯一M-EXTEND2正在运行；本文件及作者receipt不能推断终态或授权重试。基线main781f408cce5704817ebb67f2defcafc047af3820，origin固定。改编M-EXTEND1已审普通publisher，未写新的launcher、模型、核、测试或图。

## 操作范围

`deliver_execution.py finalize --repo ROOT`要求root先完成真实终态报告/文稿/config/final静审和精确stage。它仅增量更新repository_manifest及外部delivery_delta，不commit/push；verify在root随后唯一commit/push/独立restore后核main父提交、origin/remote/clean、完整tracked路径集合、普通delta SHA、科学baseline和oldentries继承，写真实publication_receipt。不读old9GB、不解压ZIP、不访问ephemeral runtime成员；外部runtime保持原样。

旧148bindings与已发布prepared proof原字节身份继承：141普通source/JSON/MD等未来可rawhash，7旧NPZ/媒体仅manifest+stat。旧stage只新增实际关闭记录，card/protocol/准备源码静审不改。除两front外，允许旧tracked变更仅六安装目标中实际SHA与BASE不同者；success必须六new，NOT_PASS允许真正partial/异常SHA并绑定outer/helper实际记录，不自动rollback。其余oldentries逐项metadata继承，禁止改旧证据或制造数值资格。两front须完整BASE原字节连续保留各一次。

新binary/科学派生CSV delta只接受**已闭helper.outputs明确记录的SHA**和实际stat bytes。类别NPZ/NPY/PNG/GIF/ZIP/gzip/CSV不由publisher读字节、decode或重hash。没有真实outputs SHA的partial ZIP/任一binary必须报告缺口，本工具不能把它静默纳入manifest；不补科学读取、不试运行/重做归档。普通PY/JSON/JSONL/MD/log/TOML/XML/TXT/patch未来可rawhash。恢复binary只核stat＋producer/declared identity，不声称恢复binary重新哈希或内容重算；ZIP内member核来自唯一运行的manifest/终态审阅，publisher不重开ZIP。

## 等root终态后冻结的config

位置formal `author/execution_delivery_config.json`；schema MEXTEND2-closed-incremental-delivery-config-1.0。最少字段：

- source_commit=上述BASE、protocol_sha256、execution_status(pass/not_pass)、execution_closed=true。
- outer_sha256、helper_sha256(存在则普通rawSHA，否则null)、helper_condition(valid_json/missing/malformed_preserved_as_ordinary_bytes/non_object_json)。完成outer决定终态；失败可保初始running/helper缺失或坏JSON，不伪造helper成功。成功必须真实helper pass和全部原门。
- actual_default_SHA256为六target实际普通sourceSHA，匹配outer及helper现存记录；helper_counts为真实完整26phase值，缺失为null，不用旧24或测试计数推生产计数。
- allowed_delta_paths精确集合：两oldfront＋真实改变的0至6oldtargets＋全部newstage已存在文件＋config/final报告自身。不得改原tracked stage文件。
- declared_output_identities为所有新NPZ/NPY/PNG/GIF/ZIP/gz/CSV的{path,bytes,sha256}精确表，必须全部在已闭helper.outputs中存在；只继承SHA和stat，不能凭文件存在捏造SHA。
- front_history两项：path、old_sha256、new_sha256、history_start_byte、history_end_byte_exclusive。
- terminal_review_path为真实独立终态报告，至少status pass前缀、execution_status与execution_closed。final_review_path为真实独立交付静审报告。最终review必须config_sha256/同execution_status/closed、reviewed_repository_SHA256覆盖全部ordinary delta除self，declared_binary_identities完整等于config表。

授权核原reply/hash/source/card一致，不把答案硬编码成特定词句，不将自动goal continuation当许可。prepared历史false保留，实际auth单存；成功/失败执行和审阅PASS分开。成功资源/helperwall/stop及26计数按已冻结原卡核；失败资源超界/stop/部分档案原值由outer/报告保留，不为出版虚构PASS。

未生成实际config、manifest/publication receipt或最终PASS；只AST解析，无import工具或HF、collect/tests、IOprobe、数组/媒体/CSV读取、ZIP打开或科学计算。独立静审后才可将此工具归档，终态和root具体config出现后还须实际字节终审。

工具SHA256：`6da19d9403d36f9c9f7fe4170c1599fce53968b7a87cbfe116aaace451a5f2c5`。
