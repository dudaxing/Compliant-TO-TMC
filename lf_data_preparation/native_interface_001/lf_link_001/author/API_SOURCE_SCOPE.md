# L-LINK1 摘要 API 源码范围与最小修订

状态：仅源码与普通 JSON 读取；未调用 API，未运行测试、求解、HP 或绘图。正式仓库未修改。依据 main `909f8acee95279e449e09961fd4fe68fed9d688f`。

## 结论

现有公共 `summarize_saved_native_result` 能关联同一完整 25 态的已有视图，但 `_reference` 只接受覆盖全部保存态的参考。真实 L-REF1 是 accepted 013／016 两态；直接传入会被记作 `mismatch`。照抄 M-ALINK1 不可满足“公共 API 识别同一 25 态路径中已有的 2／25 参考”这个功能目标。

最近步骤应准备一个只改 `hf_repo/src/hf_eval/native_response.py` 的候选，在新执行卡中授权有限普通元数据兼容测试、默认安装及一次实际关联。当前不安装、不调用。不能用不传 reference、仅在旁路索引挂接来替代公共摘要的该功能。

## 实际入口与旧实现

- 公共读取：`hf_repo/src/hf_eval/native_response.py:166`，签名 `summarize_saved_native_result(result_file, *, repo_root=None, reference_file=None, view_manifest=None)`。
- 只写一次的新文件：同文件 `write_native_response(response, output_file)`。
- 现有 CLI：`hf_repo/scripts/summarize_native_mean.py`。参数为 `--repo ROOT --result RESULT --output NEW_JSON --reference REFERENCE --view-manifest VIEW`。CLI exit 0 只证明新摘要写出，不能取代检查 reference 的状态与资格字段。
- 最近薄包装：`alpha_link_001/execute_alpha_link.py`，实际 helper 参数 `--repo ROOT --protocol PROTOCOL --time-limit 180`；`launch_link.py` 由脚本位置定位正式根，不接收阶段参数。
- 更早薄包装：`nested_link_001/execute_nested_link.py`。它要求完整 24 态 reference matched，且额外第四 PNG／四表属于旧 phase；这些范围不可迁移至 L-LINK1。

M-ALINK1 的 child 两态恰好是该 result 的全部接受态，故原 `accepted_reference_pass=true` 只覆盖那个 child suffix。L-FWD1 是从零的完整 25 态 result，没有同样的 child 语义。

## 当前明确阻断

`native_response.py:77–118` 当前令 `n=len(result.states)`，并同时要求：

1. `reference.accepted_states == n` 且 `len(reference.states) == n`。
2. `HP_calls_started == HP_calls_completed == 2*n`。
3. `enumerate(zip(result.states, reference.states))` 中每条参考的 `index` 等于连续 `0..n-1`。

对当前 n=25、m=2、参考 indices=[13,16] 的真实记录，这三项均不满足。不是参考计算失败，也不是物理门失败；是摘要读取接口不支持选定态覆盖。

## 最薄候选语义

只修订 `_reference`；保留公共签名、返回 `hf-native-response-1.0` 和 writer。新增字段是附加说明，不改已有物理响应、调用次数、时长、producer flags、continuation 或 views。

- 令 `m=len(reference.states)`。要求 `0<m<=n`、`reference.accepted_states==m`、总 HP started／completed 都是 `2*m`。
- 每条 `check.index` 必须是严格整数（拒绝 bool）、唯一且 `0<=index<n`。按 `result.states[index]` 匹配 `state_sha256`、`target_mm`、原 `status=pass` 和 `HP_calls=2`，不把 13／16 改成 0／1。
- 原 result SHA、result/model input bindings、source bindings 的源码字节核对、`full_element_and_DOF_coverage=True` 原样保留。
- 若参考已有 `selected_accepted_indices`，要求其与 rows 的 indices 一致；若有 `production_accepted_states`，要求等于 n。旧完整参考没有这些附加字段仍可读。
- `selected_reference_pass` 表示全部选定 rows 及原身份／来源条件通过。
- 输出 `matched_state_indices`、`matched_state_count`、`production_accepted_state_count`、`covers_all_accepted_states`。indices 可按升序输出；只有检查全部通过才输出实际 matched 列表，失败为空，避免把已失败字段当合格覆盖。
- `status='matched'` 仍只用于全 n 态；合格真子集为 `matched_partial`；身份、计数、来源等失败保持 `mismatch`。
- **原 `accepted_reference_pass` 只在 selected pass 且覆盖全部 n 态时 true；原 `full_path_reference_pass` 仍再要求生产 completed。** m=2／n=25 下两字段均 false。全覆盖参考与无参考原含义保持。
- 无 reference 时新增 fields 为 false／[]／0，population count 为 n，原 `not_provided` 状态及所有资格 false 保持。
- `HP_all_columns_qualified/contact_qualified/clamp_qualified/pressure_qualified/HF5_qualified` 始终 false，不从参考的陈述升级。选定态通过仍只是原方向、全单元／DOF覆盖，不是所有切线列或压力资格。

这不重构参考，不重新读取 HP gzip，不重新算门；API 仅核原已封存普通记录的身份、计数和声明。原十五个数值门保持由 L-REF1 实际计算证据承担。

## 当前真实身份与将来一次调用

正式根：`D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC`。

| 字段 | 仓库相对路径或身份 |
|---|---|
| result_file | `lf_data_preparation/native_interface_001/lf_forward_001/run_001/lf_fine_forward/result.json` |
| result SHA | `bfb711b5b948e188eb275f201f4a6dcca210687598a928d8772fa6359aa8888b` |
| model_file | `lf_data_preparation/native_interface_001/lf_forward_001/run_001/lf_fine_forward/model/model.json` |
| model descriptor raw SHA | `642972acd677372911f462948bfb554add69dc2209f781e89b70186429d865c3` |
| original_response_file | `lf_data_preparation/native_interface_001/lf_forward_001/run_001/lf_fine_forward/response.json` |
| reference_file | `lf_data_preparation/native_interface_001/lf_reference_001/run_001/reference/summary.json` |
| raw_view_file | `lf_data_preparation/native_interface_001/lf_forward_001/run_001/view/view.json` |
| view_case_summary_file | `lf_data_preparation/native_interface_001/lf_forward_001/run_001/view/lf_fine_forward/summary.json` |
| reference states | index13／loading／1.20 mm／`d23cdaee0a02e727726ef8789c902494f3f0ec09256fdeed74c0086cd3169e96`；index16／unloading／1.05 mm／`29910bc07e26bd7d7e5f7bb113c58094c2cff27ea544a71b2c523e1078265e14` |

L-REF1 普通 summary 的 result SHA 及 input bindings 匹配上述原 result/model；`selected_accepted_indices=[13,16]`、`production_accepted_states=25`、4 HP、全单元／DOF覆盖 true；`full_production_path_reference_pass=false`、`public_API_association_performed=false`。API 关联不回写这两个原历史字段。

候选未来实际调用仍是一次：

```python
response = summarize_saved_native_result(
    protocol['result_file'], repo_root=repo,
    reference_file=protocol['reference_file'],
    view_manifest=protocol['raw_view_file'])
write_native_response(response, output/'linked_response.json')
```

薄包装应核 `matched_partial`、selected pass=true、indices=[13,16]、count=2／population=25、原 full flags=false、views matched、生产 completed=true，然后写一份 `light_index.json`。索引路径以 restored repo root 为基准，引用原 response、原 result/model、同两态参考、普通观测 JSON、新响应和已有媒体。不是另造科学结果或重写旧图。

`_views` 会读取全25态普通 view／case summary，并 raw-hash 同 case 的原 3 PNG 和 25 帧 GIF。当前 source-only 审阅未读这些媒体；将来此读取须在新卡内明确列入。它不解码图片、不生成新图、不打开 NPZ／gzip／CSV。参考误差 PNG 若要纳入轻索引，明确为参考 producer 封存媒体身份；不要假称原 `_views` 会自动把它识别成生产 view。

## 有限兼容测试的证据位置与必要补充

现有源码位置：

- `api_validation_001/tests/test_native_saved_response.py:64`：完整保存路径及同身份全部参考；`:145`：other_result／missing_state／HP_count／not_pass 反例；`:168`：原 views 关联。
- `hf_repo/tests/test_native_reference_source_migration.py:40`：旧 positive 参考因已安装 mechanics source 不同而 mismatch，并保原生产 success 与冻结文件。该文件导入 NumPy，并依赖真实旧记录，不应默默纳入本次 metadata-only 新测试范围。
- `hf_repo/tests/test_native_batch.py:59,99`：mock 公共响应原字段运输，未实际测试 `_reference`，不能证明 sparse matching。

最小新测试应只使用临时普通 JSON／源码文件、pytest／stdlib，并通过**公共摘要函数**验证临时 model/result 的身份。至少覆盖：无参考、原完整参考、合格 sparse13/16、完整参考但生产未 completed、重复／bool／越界 index、错误 SHA／target、错误 result/model binding、错误 HP count／reported m、空 rows、缺失 row 而 reported m 保持、source mismatch、可选 selection/population 陈述不一致。检查原 producer flags 与数值摘要不变、同 displacement 不同 loading/unloading index不能互借、subset 不升级 accepted/full flags。

不需要新增完整路径、真实 HF 小模型或旧图测试来证明本次元数据读取功能。不要把这些候选测试规划写作已经通过。执行顺序、准确测试清单、安装时机及有界资源额度由新卡冻结；本报告不授新窗口。

## 读取范围与未完成项

本次只读取 native_response／纯 CLI／旧两份包装与 launcher、上述测试源码，以及 L-REF summary 和 L-FWD result／view 的普通 JSON。曾尝试两个不存在的定位名称 `launch_alpha_link.py` 与 `NEXT_STEP_REVIEW.md`，读取失败后已用真实 `launch_link.py` 和当前 stage 记录定位；没有启动任何科学入口。

所有 source SHA 在 `API_SOURCE_PINS.json` 中；它是源码／普通记录审阅证据，不是候选执行、默认安装或 API PASS 证据。完整25态独立参考、压力、有效夹持、释放、稳定性和 HF5 仍未完成。
