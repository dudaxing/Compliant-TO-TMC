# F-STREAM1 后只读排查与最小后续方案（2026-09-30）

本记录承接用户“请提交推送，并继续”。本轮只读保存的 JSON、源码、AST 和文件哈希；新增的唯一文件是本文。没有再次解压原 gzip，没有导入或执行项目 helper／控制／JAX／科学程序，没有新 profiler、执行根或数值窗口。提交和推送由根代理另行处理，本文不把其结果预登记为成功。

## 整体目的及本轮问题

项目目标是建立与 LF 解耦、任务定义明确、可异机恢复且数值与接触物理可信的独立 HF 非线性力学评估器。当前完整 force 同步、AD、真实接触／平衡路径和 HF5 仍未完成。局部算术门、数据可读、诊断运行、profiler 接口和真实力学资格必须分别验收。

F-STREAM1 的唯一窗口已结束：16 组 82 子例通过，真实流在 4,000,000 个接纳事件处遇 event_count_limit；execution_failure／partial，P3 只封存 partial。三后审通过不改变这个结论。整体目标的工具状态以根代理最新真实返回及 CURRENT_STATUS 为准，本文不独立修改或推定该状态。

本轮只读排查回答三个问题：采集包装是否出现在已保存 trace 样本中；56 次直接 module 参数匹配为什么没有形成原执行区域候选；下一步最小的新信息应是什么。它没有重新判断全流，也没有开始新的归因或科学执行。

## 实际读取的证据与源码身份

正式 Git 根为 D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC。下表路径相对此根，运行文本的两类绝对路径另列。哈希是本轮直接读文件所得；正文前缀 SHA 只读取已有保存值，没有重新解压验证。

| 文件 | bytes | SHA256 |
|---|---:|---|
| native_stream_001/results/stream/count.json | 10,209 | fa0c75a69955dc2cfca89b11536d1b7ab9f6a592b87563b6e2d39189e768bc54 |
| native_stream_001/results/stream/census.json | 4,649 | e779021b8e5868fb6a94fc76b7c1e64c74a3b84e9bb19f31cbbdfe4009e2c6a3 |
| native_stream_001/results/stream/samples.json | 35,255 | 01a273a4c3b1fd411d1f276cf9853256648d8c5c254bb2eb6f7e288df6d3d72d |
| native_stream_001/results/stream/controls.json | 817,637 | 4c1cff870130dbdfc9621d844eb320ccff9ba50b9dfd11cd7262fa93c0b4c1d4 |
| native_stream_001/receipt_binding.json | 7,182 | 0bba3f6663d342e3c13c7a6dc9f5098846b1f9a0bf5702df59100b0d97e5ea48 |
| micro_trace_002/results/trace/summary.json | 190,902 | 1c996bfcd9688772a7404e752023b7e44e3c35d73f1a9ffaca8fa1cf9a2c96f0 |
| hf_repo/scripts/run_saved_trace_census.py | 128,256 | 1250415b2084cd4d52aaae2a0f996f3a905e513cbb8e1b6085ac15c143569174 |
| hf_repo/scripts/probe_micro_trace_v2.py | 59,537 | 3e952ab7e717b15ca3b1fc63a0c82d81fc7aa777cf822fec82b054fc42011e23 |
| hf_repo/scripts/micro_trace_v2_evidence.py | 106,549 | 7acd278ff379c06ab1e44e1f288fa9e6e3cc82c7952383c16417270ed5d7613e |

表中 native_stream_001 和 micro_trace_002 均位于 hf4_c2_stable_f_validation 下。主要入口是[计数](../hf4_c2_stable_f_validation/native_stream_001/results/stream/count.json)、[统计](../hf4_c2_stable_f_validation/native_stream_001/results/stream/census.json)、[128 样本](../hf4_c2_stable_f_validation/native_stream_001/results/stream/samples.json)、[控制](../hf4_c2_stable_f_validation/native_stream_001/results/stream/controls.json)、[本次绑定](../hf4_c2_stable_f_validation/native_stream_001/receipt_binding.json)及[原采集 summary](../hf4_c2_stable_f_validation/micro_trace_002/results/trace/summary.json)。

本轮另读三份实际固定运行文本：

| 实际路径 | bytes | SHA256 |
|---|---:|---|
| C:/Python313/Lib/json/__init__.py | 14,379 | feb17670e443e5db2723f217727dcc5d5e155c40e4e6935b16061c88542f24e7 |
| C:/Python313/Lib/json/encoder.py | 16,592 | 955cb7cc721e3881f084c2e334eb66d6a1f0fc08457b3e06cccbea218b3819fe |
| D:/Coding/Diversity TO/Compliant-TO-TMC/.venv-handoff/Lib/site-packages/jax/_src/profiler.py | 19,711 | abb2a2b16a34a060d581dccc0acecd655b20d60313377af3f727cce50a9c2a83 |

这些运行文本与原保存身份相符；没有实例化 native ProfileOptions 或把磁盘文本误当成新的执行证据。上述源码行号对应这些精确身份。

## 确证一：本次失败是事件容量停止

已有 count 保存 496 次非空 read，返回 453,720,232 bytes，raw／reader 各打开或创建一次、各关闭一次。返回前缀 SHA 为 1964b1b99c02b4281bc63c6d0a9214c566d96331bc98ae3f3c808f7e0c0ae90b。framer 消费到 453,449,107，最后接纳事件 end（exclusive）是 453,448,982；当前单元 start=453,448,983、长度 124。这个第 4,000,001 单元已经框定并严格解码，随后在 census 接纳前被事件界拒收，不是已证坏 JSON。

453,720,232−453,449,107=271,125 bytes 是已返回而未被 framer 消费的后缀。旧 268,435,457-byte 前缀交叉检查 true，SHA 保持 7a6f358825b281d5c59f58824eb77a93f7972a11e3bc2794a98919a084d0ec90。完整正文大小／SHA 为 null，EOF／各 member 正文 CRC32＋ISIZE／UTF8 final／完整严格 JSON 均未验证；FHCRC 仍未检查。

4,000,000 个接纳事件中 X=3,999,991、M=9。四个 typed trace 线程合计 3,999,998 条，两条 tid 缺失，与字段桶一致。源码 [Census.event](../hf_repo/scripts/run_saved_trace_census.py#L550) 在 553 行于自增前拒绝超界；[Framer.finish_unit](../hf_repo/scripts/run_saved_trace_census.py#L633) 先解码验证，再在 653 行调用 census。因此事件界及保存位置有具体代码支持。字节量低于本卡 1GiB，已存资源未触时间或内存界，不能把本次失败写成内存耗尽、超时或数值内核失败。

## 确证二：采集包装确实进入已保存样本

128 样本仅是原数组索引 0–127；本轮标准库读取并筛查后，其中原五应用标记匹配为 0，直接 module 键匹配也为 0。它们不能给 56 条匹配事件补出实际名称或参数。样本中的具体原记录为：

| 原数组 index | 原 name |
|---:|---|
| 23 | $probe_micro_trace_v2.py:278 checkpoint |
| 36 | $probe_micro_trace_v2.py:160 write_json |
| 71 | $__init__.py:120 dump |
| 73 | $encoder.py:205 iterencode |
| 75 | $encoder.py:263 _make_iterencode |
| 82、127 | $encoder.py:334 _iterencode_dict |

对应[原 probe](../hf_repo/scripts/probe_micro_trace_v2.py)的调用链：278–281 行 checkpoint 写 summary.pending.json 并替换 summary；160–165 行 write_json 使用 json.dump、逐次 flush／fsync；162 行显式 indent=2。317–375 行 step 在每阶段前后 checkpoint。985 行 start 之后，两次 observe_output 执行到 1008 行 finally 的唯一 stop；725–736 行的 transfer、save_output 和 compare 也都位于这个采集会话内。

固定 CPython json/__init__.py 的 173–180 行调用 iterencode(obj) 并逐 chunk fp.write；encoder.py 的 205 行默认 _one_shot=False，251–260 行由此选择 Python _make_iterencode。保存样本与这个具体源链吻合，说明采集期间的 JSON 摘要写入活动确实被记录。仅改 indent 不能根据本机这份源码保证 json.dump 转入 _one_shot 的 C 路径；本轮没有做任何替换或性能试验。

这里确证的是采集包含包装活动，不能据此认定 399 万 X 事件均为编码器，也不能把捕获事件数量当 CPU 成本或科学工作量。原数组顺序并不自动是时间顺序或调用树；上表不是未经验证的因果时轴。

尤其是 step 的 327／328 行 checkpoint／event 发生在 336 行 TraceAnnotation 和 347–355 行实际 function_measurement 之前；372／374 行记录发生在 annotation 退出之后。包装 JSON 能扩大整份 trace，却不能直接被计入所保存的 sync 函数 wall。它对异步工作、CPU 竞争或 profiler 扰动的影响仍是假设，不能直接解释约 13 秒同步根因。

## 确证三：56 次直接 module 匹配没有满足原执行名称门

原 [TARGET_RULE](../hf_repo/scripts/micro_trace_v2_evidence.py#L80) 第 80–86 行固定如下：module=jit_reused；精确名称只有 Execute(jit_reused)、Execute: jit_reused；六个通用名称是 Execute、CpuExecutable::Execute、CpuExecutable::ExecuteAsyncOnStream、PjRtCpuExecutable::Execute、PjRtCpuExecutable::ExecuteWithExecutionInputs、ThunkExecutor::Execute；直接键是 hlo_module、hlo_module_name、module_name、program_name、executable_name。

同文件 582–595 行的执行区域选择先排除 F-TRACE2 应用名，再要求精确名称，或者“通用名称在六项 allowlist 内且存在直接 module 参数”。之后还要求 duration、CPU metadata、唯一 call／sync 窗口包含等原门。单有 module 字段不满足这个联合条件。

现有 census 报告 exact_event_name=0、generic_name_with_direct_module_arg=0、direct_module_arg_any_nonapplication_name=56。其实现见 run_saved_trace_census.py 的 564–572 行；原数组前缀内 name 字段全部为 string。因此在这 400 万接纳事件内，56 次非应用直接 module 匹配没有属于六个通用执行名称的匹配，也没有精确执行名称命中。这是固定谓词和保存计数的逻辑结果，不是新的全流解析。

目前没有保存这 56 条的 name、phase、ts／dur、各 module 字段、冲突情况及原位置。它们可能是其他粒度的 host／算子记录，也可能有别的含义；本轮不能给它们命名、改成新的执行区域或将其数量和 44 producer／26 fusion 对应。通用执行名称在前缀中是否另有“不带合格 module 参数”的出现，原 census 没有无条件计数，也仍未知。未解析余量更不能被两个零排除。

## profiler 默认项的可知边界

probe 第 847–848 行实际请求 profiler_options=None；原 summary 同样记录 requested_options=null、effective_defaults=native_not_exposed。固定 jax/_src/profiler.py 第 49 行的 ProfileOptions 继承 native 类型，194–206 行仅说明 None 被换成 ProfileOptions() 再交给 ProfilerSession。159–162 行说明采集包含 Python functions 和设备活动。

这足以说明原会话采用 native 默认对象，并与实际 Python 名称样本相容；这份 Python shim 没有公开具体默认 python_tracer_level／host_tracer_level 的数值。本轮没有导入、实例化或枚举它们。下一次若考虑显式选项，应先在具体新卡中验证本机实际字段／合法值及所需 host 事件是否保留，不能把猜测的默认值写入旧回执或静默改原采集门。

## 取舍：先拿到被汇总但未留存的事件身份

当前最小信息缺口是 56 次匹配的实际 name／参数及与原执行名称的关系。再次仅提高 400 万界来追求全流会重做已知前缀并增加解析量，却没有先解决为什么原名字规则没有命中；立即重采集或修改 checkpoint／选项又同时改变观察对象及证据形态。因此建议先做一次严格限定旧已验证前缀的定向提取，再据真实记录选择原规则适配研究或新的采集设计。原规则是否应该修订，还需要实际名称的语义依据和单独明确批准。

## 最小候选卡 F-SELECT1（建议合同，未执行）

这是下一张具体卡的候选方案，不是已批准窗口或已完成作者稿。下述读取范围、正常前缀停止和资源须在正式卡明示批准后，才允许作者、同 SHA 静审及唯一运行。本轮只提交这份方案记录，不创建对应根。

1. **目的与唯一范围。** 从同一 micro_trace_002 原 gzip 中重建 F-STREAM1 已接纳的 4,000,000-event 前缀，定向保留 56 个非应用直接 module 匹配、5 个原标记、9 个 metadata，共 70 个必需记录。调查它们的身份／字段，不授予全流或成本资格。唯一新根可用 prefix_select_001；具体 helper、步骤／binding／排除清单和最终 SHA 在正式停编稿固定。原源码、冻结根和科学环境保持字节不变。
2. **来源锚点。** 固定 F-TRACE2 与 F-STREAM1 binding、count／census／规则源及必要 runtime；原 gzip 的压缩 bytes=24,572,396、SHA=e5a40ab0916e6b39f08e3c61a5c702d151f5e745553a4277c969ef69284eae40。所有必要 source／manifest／reference 路径须有精确身份、边界、reparse 和 pre／post 检查。原件只作固定只读引用；选择件及角色数量在作者稿实际列明，不递归重验未选择 payload。
3. **同一流的两个明确端点。** raw gzip 只打开一次、直接 _GzipReader 一个、每次正请求≤1MiB。最多返回并计数 453,720,232 bytes，最后请求按剩余量缩窄；核全部返回前缀 SHA 恰为 1964b1b99c02b4281bc63c6d0a9214c566d96331bc98ae3f3c808f7e0c0ae90b，同时保留旧 268,435,457-byte 前缀 SHA 同流检查。严格解析只到已接纳 end=453,448,982，必须恰为第 4,000,000 个完整 object 的 end。此后只为完成预声明返回前缀的来源核对而继续计字节／SHA，不解释后缀，不 seek、重开或求 EOF。该正常前缀截止是新合同，不能在旧 F-STREAM1 中把硬界首错改为成功。真正语法／配置／I/O／deadline 首错仍立即停止所有额外读取。
4. **解析配置。** 继承已验证 framing、增量 UTF8、解码后重复键拒绝、有限浮点／≤256位整数、代理／BOM、1MiB单元、深度64、键4096／4KiB及必需状态4096项等严格配置。端点必须在完整单元边界；decoded／retained／counted／unconsumed 的位置各自记录。没有完整顶层结束、UTF8 final 或 EOF 资格。哈希侧端点不是已全部解析端点。
5. **必需记录与有界补充。** 70个必需记录必须全量保留原 index、单元 start／end／SHA、固定 trace 字段、五 module 字段的存在／类型／匹配及矛盾键、metadata name／sort、标记字段。不能只存匹配的一个 module 键而掩盖其他矛盾。非标量选定字段记录其类型和未保留状态，不能冒称原值不存在。单字段文本≤4KiB、累计留存文本≤16MiB；容量不足立即 partial。另对六个原通用名称做无条件固定桶计数，最多保留58个诊断样本，总留存记录≤128；遗漏数量及 sample_set_complete 明示。可用预先固定的样本名称／$encoder.py前缀桶统计已有前缀里的文字匹配量，标签只能是名称模式匹配，不能把它们自动当包装成本或科学分类。
6. **保存控制与原规则。** 必需记录的56／5／9数量、既有phase／字段计数和端点要与固定前缀证据交叉核对；不一致属来源／实现首错。原 TARGET_RULE 全文身份保持，输出记录为何不满足原执行名称，不把观察到的新名字自动加 allowlist。CPU metadata 唯一性、5标记唯一／顺序／duration、call窗口唯一归属、producer同线程／直接module关联及矛盾门仍不授予全流验收。B／E为0是这个旧前缀的统计，不代表全流不存在。
7. **真正必要的新小控制。** 原82子例仅在核心文本／AST身份及接口相同的部分继承；改变的前缀截止／选择／保存接口另需同实际路径小控制。至少覆盖完整单元恰端点与错端点、跨块UTF8／已停止后缀不被解释、两个前缀SHA匹配与不匹配、必需选择计数／字段冲突、留存恰界与超界／诊断样本遗漏、早EOF／trailer异常、deadline或I/O首错＋secondary close。fixture正文累计≤64KiB，不分配大数组；具体子例和期望分类在作者稿静核，不能用既有82个pass代替新接口验收。
8. **资源候选。** 建议沿用一次连续300秒／4GiB和原SUP1：P0含清理15秒／活动9.75；P1含清理240／活动234.75；P3含清理15／活动9.75；shared30，封存前≤25、末绑定保留5。保5秒清理＋.25余量、nonseal≤D−25.25、seal≤D−10.25，真实首read在最后检查点后余量≥20秒。依据只有旧流同前缀解析wall129.0881791秒及整卡143.2721776秒；新保存／控制开销未知，不保证完成。输出总≤32MiB、单件≤4MiB、根≤128文件、progress／阶段日志保持原有界合同；不借旧窗口或预算余量。
9. **停止与完成。** 任何真首错、选定来源不一致、必需记录不足／溢出、错端点、预算／清理／封存问题都关闭 partial，首错不被记录／关闭异常覆盖，无重试。仅当选择和两个端点／SHA、全部声明前缀统计／控制／来源／清理／保存绑定闭合，才允许一个新的 prefix_selection_complete 诊断结果；其 scope 必须写明“仅既定前缀”。若已经达到合法解析端点，预声明的后缀来源计数属于该新合同的一部分，不是错后续读；若真错，禁止再读来凑哈希。
10. **资格边界。** 即使候选卡完整成功，整流大小／SHA、EOF／CRC、完整JSON／metadata或候选唯一性仍未知；scientific_admission、force_executed、runtime_native_trace_observed、native_json_parsed、xplane_decoded均false，44producer／26fusion observations仍null。旧 F-TRACE2 和 F-STREAM1 的失败及接受门不改。仅把实际名称／字段和已有数组前缀统计作为下一次取舍的证据。

若正式作者不能在原端点、同一流前缀SHA与这些上界内实现，先收紧方案或停在静审，不凭“继续”临时改变读取或完成合同。若提取显示执行名称规则与真实事件格式不适配，下一阶段再以来源语义证据明确申请适配；若确有原规则执行记录，才审原窗口／metadata／producer门。若采集包装显著扩大前缀计数，才设计独立对照采集；这三个方向都没有在本文提前执行。

## 本轮效果与恢复

本轮将“可能有包装活动”推进为有具体样本和固定源码链支持的事实，同时排除了“56直接参数已等同原执行区域”及“包装JSON直接解释sync wall”的过强表述。仍缺56条身份、全流余量及有效内部区间，完整force／AD目标未解决。

异机恢复须携带 native_stream_001、已选择历史来源及 micro_trace_002 两个原 native 文件；新根中的引用不携带原件副本。原件 SHA／相对项目路径及旧 source pins需据实际恢复位置明确核对，不用旧绝对 source 路径静默指向其他文件。本文及最新源码／证据是否已经发布，以本轮实际提交推送回执和交付清单为准，不由本文的“提交推送”任务授权推定远端结果。

本文检查限于标准库文件读取、JSON／AST／哈希；没有把 partial 前缀普查升级为全量，没有新增实验结果，也没有更改任何科学门或目标状态工具。
