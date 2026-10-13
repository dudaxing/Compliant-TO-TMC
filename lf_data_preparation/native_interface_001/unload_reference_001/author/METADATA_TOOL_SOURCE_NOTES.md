# M-PREF1 普通元数据工具源码说明

三份工具仅源码准备，未运行、未写正式库、未导入HF或科学库、未读取科学／媒体内容。最终协议、卡、准备正文与数值门由root及独立源审冻结；这些工具不生成科学计划或验收结果。

- prepare_stage.py 接受 --repo、--previous-publication-receipt，直接读取同外部目录已冻 protocol.json（不把seed当协议）。一次复制3runtime、协议、卡、PREPARATION_RESULTS及明确author清单；--author-file仅追加root明确普通文件。final_source_review.json/.md必须先到齐并绑定actual protocol及源SHA。既有两front完整BASE正文上方只加一次front_prefix。receipt artifact map排最终reviewJSON自身及随后生成的receipt，避免循环。
- publisher_source.py finalize／verify接受 --repo／--restore。实际BASE eb92b41fd58547640d2c2a8381f98aa5012154df、M-PATH1闭卡证明、旧manifest19962项／10330137433B均核；只rehash新普通stage＋两front，旧科学及媒体条目完整继承。10NPZ bindings只核旧manifest SHA／size与stat。finalize只改manifest及外部delta收据，commit／push／ff-only恢复由root另行执行；verify核主干父提交、origin、remote、root/restore clean、精确路径增量、普通delta身份和旧entries继承。外部副本运行，正式副本只作恢复源码。
- record_authorization.py仅未来收到本卡直接human原话／上下文且source实际发布之后运行；使用actual source proof、published_commit／protocolSHA及900／960秒／采样8GiB，auth与reply用authorized_execution_source_commit。不把该字段解释为用户逐字审过commit，也不强制批准词面字符串。此时不生成authorization、reply或sourceproof占位；自动goal接续不构成该future human input。

公共接口：partial-saved-state-independent-reference-card-1.0，M-PREF1，selected_child_accepted_indices2/3、global18/19、target0.9/0.8、2selected／4plannedHP、900／960秒／采样8GiB、11平铺数学依赖、原15门。仅校对已冻元数据；不执行HP或重新定义数学门。reference_output正式repo-relative unload_reference_001/run_001/reference，未创建外部runtime。

stage author标准清单：front_prefix、input_scope_review与physical_gate_review两份、SOURCE_AUTHOR_NOTES／source_author_receipt、input_contract_seed、这三工具、本说明／metadata_tools_author_receipt、final_source_review两份及previous_execution_publication_receipt。所有复制源在正式写入前校对普通suffix、PY AST和完整finalreview源SHA；复制缺项直接报错，不猜生成future资料。

本次仅AST解析；工具实际执行及出版结论待root独立审后另记。源代码没有构造模型、API／F／T／HP／solver／测试／绘图入口。
