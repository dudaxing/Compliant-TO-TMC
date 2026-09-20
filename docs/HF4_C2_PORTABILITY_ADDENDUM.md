# HF4-C2 公开副本数值复读与历史来源边界补充

当前状态：**两个选定案例的公开保存态数值复读已完成，逐态科学内容精确复现原结果；两个外部历史来源仍未重新核验**。本补充记录搬迁验证发现的来源依赖问题及其限定范围的解决方式。原冻结报告、协议、源代码与科学证据均保持原字节。本次没有新增 FE 求解，也没有修改原力学准入结果。

## 首次搬迁失败及原因

首次验证将公开载荷复制到同一主机的另一目录，并从外部工作目录启动原完整来源审计。`padding_2p5` 在进入保存态 HP 计算前即因缺少历史 MATLAB 逐行源码文本失败，返回 `not_pass`、`FileNotFoundError`，`states` 为空。外部验证 receipt 同时记录 `production_FE_executed: false`。这次失败不能解释为该算例新的数值检查失败，也不能解释为可移植性验证通过。

原因是冻结的 `saved_field_admission_r3.json` 将 166 个历史输入纳入来源绑定，其中有两个按既有 `SOURCE_MATERIALS_AND_PUBLICATION.md` 发布边界明确不随公开副本上传的第三方逐行源码。原完整来源审计无条件核查这两个文件，于是把未公开的历史材料变成了公开数值复读的隐式依赖。公开副本缺项凭据列明的文件身份如下，路径为仓库相对路径，文件本身不在公开载荷中：

| 历史源码路径 | 原 SHA256 |
|---|---|
| `hf0_audit/tmc/assembleKtFi.m.numbered.txt` | `56e6759471a87b1d32e75c3e8a3ba8a0a439d5dc3a959d27eed3d7e3a4d5285c` |
| `hf0_audit/tmc/initializeFEA.m.numbered.txt` | `ca0ead10a18ff35373c82f0b967876a19976adf6fca3afa06d22129515209ef0` |

不通过补入这些原源码、删除历史绑定或改写旧审计来掩盖该问题。原完整来源审计及其资格不变：在具备全部匹配来源文件的环境中，它仍要求全部来源闭合；本次公开搬迁未重新验证这两个外部来源。

## 原字节失败证据

首次失败材料已复制到 [portability_failure_001](../hf4_c2_diagnostics/portability_failure_001/)，每份副本与原文件逐字节一致：

- [失败审计](../hf4_c2_diagnostics/portability_failure_001/padding_2p5_portability_audit.json)：原位置 `.github_handoff/c2_portability_001/publication/review_runs/padding_2p5_portability_audit.json`。
- [失败日志](../hf4_c2_diagnostics/portability_failure_001/padding_2p5.audit.log)：原位置 `.github_handoff/c2_portability_001/padding_2p5.audit.log`。
- [外部验证 receipt](../hf4_c2_diagnostics/portability_failure_001/receipt.json)：原位置 `.github_handoff/c2_portability_001/receipt.json`。
- [缺失来源凭据](../hf4_c2_diagnostics/portability_failure_001/missing_sources.json)：原位置 `.github_handoff/c2_portability_missing_sources_001.json`。

[复制 receipt](../hf4_c2_diagnostics/portability_failure_001/copy_receipt.json) 保存原位置、目标名称、字节数和 SHA256。[输出清单](../hf4_c2_diagnostics/portability_failure_001/output_sha256.json) 在创建自身之前完成枚举和哈希，不包含自身。旧 receipt 和审计中的绝对路径是原始上下文，未重写成新目录路径。

## 新公开数值复读入口的资格

新增入口为 [audit_contact_c2_readback.py](../hf_repo/scripts/audit_contact_c2_readback.py)，源 SHA256 为 `32343b17ea164e32909f1313a0bc4d2d9011b6dc4c4fd6e1120d4a6d4aea2225`。它使用不同的 `schema_version: contact-c2-numerical-readback-1.0` 与状态 `numerical_pass` / `numerical_not_pass`，另列 `numerical_status: pass / not_pass`、`valid_for_execution_admission: false`。它检查公开保存态的数值证据及可取得来源，明确将上述未公开历史源码标记为 `not_reverified_external_source`。这个状态不等于完整来源已经重新闭合；缺少其它应随公开载荷提供的必需输入、来源不匹配或数值门失败，不能被这个声明豁免。

`historical_sources` 逐项保留相对路径、预期 SHA256、状态与实际 SHA256；文件未取得时实际 hash 为 `null`，不把它加入已读取输入的 hash 字典。预期 hash 的声明仅追溯 `review_receipt → saved_field_admission_r3 → 原 audit` 的历史来源链，不等于重新核验原字节。这两个文件用于历史 MATLAB 公式来源核查，不参与当前保存态数值求值。输入错误时历史来源状态可以是 `not_assessed_due_to_input_error`，不能伪写 `verified`；若取得实际文件，则仍须核验其字节与预期 hash。

新入口仅复读已保存的模型、状态和数值记录，不产生新 FE 路径，不重新授予原协议的全来源资格，不改变准入门槛，也不把原失败末态变为通过。原结论继续有效：`padding_2p5` 与 `outer_free` 的原路径通过；`mesh_h00625` 的原末态因生产与 HP80 总内力门失败，整条路径保持 `not_pass`，只有此前有效前缀可比较。

同一主机、不同目录的公开载荷复读只支持相应的路径可移植性结论，不构成跨操作系统或跨硬件验证。

## 已完成的搬迁数值复读

002 验证将 3361 个公开载荷文件逐字节复制到另一目录，再加入新的数值入口和对应测试两个文件，从外部工作目录复读一个原通过案例和一个含原失败末态的案例。总 [receipt](../hf4_c2_diagnostics/portability_readback_001/receipts/receipt.json) 的 SHA256 为 `4808f20b93fa9cc056a6d912d831ae965b7845394cfa74dc5253c0e11e13c788`，记录 `status: pass`、`error: null`、`source_and_publication_unchanged: true`、`production_FE_executed: false`。这里的总 `pass` 表示搬迁复读与原结果比较成功，包括成功保留原失败状态，不表示两个力学路径全部通过。

| 案例 | 新数值状态 | 已存状态 | 数值门检查 | 输入绑定数 | 复读耗时 |
|---|---|---|---|---|---|
| `padding_2p5` | `numerical_pass` | 19 / 19 通过 | 589 / 589 通过 | 220 | 52.015 s |
| `mesh_h00625` | `numerical_not_pass` | 20 / 21 通过 | 650 / 651 通过 | 224 | 201.095 s |

两案共 40 份完整状态详情与各自原实验详情逐字节相同；原科学摘要和详情均精确匹配。细网格末态 `uniform_tmc:20` 的原失败及有效前缀边界保持不变。两个历史源码条目在两案中始终为 `not_reverified_external_source`，`valid_for_execution_admission` 始终为 `false`。本次没有对 `outer_free` 再做搬迁 HP 复读，不能把两案验证写成三案或全部历史数据的再次验证。

新的 [portability_readback_001](../hf4_c2_diagnostics/portability_readback_001/) 归档保留两份新审计、两份日志、两份逐案 receipt、总 receipt、40 份完整状态详情、执行固定凭据、比较器自检、测试回顾记录和三份出版核对工具源码。共 53 份原字节副本，另有复制 receipt 和输出清单，共 55 个文件。

[copy_receipt.json](../hf4_c2_diagnostics/portability_readback_001/copy_receipt.json) 逐项列出原工作区位置、公开存储位置、字节数与 hash，并映射每案原运行目录及每个 `detail_file` 到归档中的详情文件。审计 JSON 中的原绝对 `run` 和相对输入绑定未被改写。相对输入绑定仍以当时运行目录为基准；新归档是结果存档，不是独立运行目录。需要定位详情时使用上述显式映射，需要输入时使用公开工程内原实验与源码路径。[output_sha256.json](../hf4_c2_diagnostics/portability_readback_001/output_sha256.json) 不包含自身。

执行前 [固定凭据](../hf4_c2_diagnostics/portability_readback_001/preflight/c2_portability_execution_pin_002.json) 绑定当时公开载荷、源码、测试、编排工具和实际命令。[比较器自检](../hf4_c2_diagnostics/portability_readback_001/preflight/c2_portability_r2_comparison_selfcheck_001.json) 有 12 项通过：1 个接受对照与 11 个拒绝反例，覆盖状态、阈值、源码身份、缺少其它输入、历史声明 hash 和科学详情篡改。这些是比较器行为检查，不重复计入原科学门。

[新入口 21 项测试记录](../hf4_c2_diagnostics/portability_readback_001/preflight/c2_readback_preflight_001.json) 是明确标记的回顾性记录：当时工具输出为 `21 passed in 12.16s`，但未单独保留原始 stdout 日志或机器 receipt。该记录没有为补证而重新运行测试，不能将它描述为同期原始日志。本次归档仅复制与哈希核验，没有执行 FE、HP 或测试。

归档的 `publication_tools/verify_c2_portability_r2.py`、`verify_c2_portability.py`、`prepare_c2_sync.py` 是当时出版核对的工具源码，含固定 `ROOT` / `.github_handoff` 逻辑；它们不作为公开通用运行入口。使用公开数值入口前，先按[接续指南](RESUME_DEVELOPMENT.md)建立独立复制树，仅从该复制树根目录执行以下命令，输出名称须未使用。即使 `--output` 指向外部目录，脚本也会在 `--run` 目录内写入逐态 details，因此不要在发布原树运行：

```powershell
python -B hf_repo/scripts/audit_contact_c2_readback.py --run hf4_c2_diagnostics/experiments/padding_2p5 --protocol hf_repo/configs/contact_c2_v3.json --output review_runs/padding_2p5_numerical_readback_new.json
python -B hf_repo/scripts/audit_contact_c2_readback.py --run hf4_c2_diagnostics/experiments/mesh_h00625 --protocol hf_repo/configs/contact_c2_v3.json --output review_runs/mesh_h00625_numerical_readback_new.json
```

第二条命令应保留 `numerical_not_pass`，对应非零退出码；不能为得到零退出码而改变门槛或忽略末态。这里列出的是复读命令，不是授权新的 FE 执行。

## 公开可复读范围的限制

此修正只保证上述新入口能够在缺少精确声明的两项历史源码时复读公开保存态，不能概括为所有历史诊断、汇总和图表均可在纯公开副本中独立再生：

- 原完整来源审计 `audit_contact_c2.py` 仍要求完整来源。
- `summarize_contact_c2_r2.py` 复用冻结的 `Reader.audit_bindings` 完整核验，仍会要求两项历史来源。
- `diagnose_contact_c2_force_precision.py` 直接导入原 `load_run`，同样保留完整来源依赖。
- `review_contact_c2_final.py` 遍历原 166 项来源，纯公开副本无法重新闭合其中的两项外部材料。

已有 summary、图表和固定失败场算术反事实证据仍可读取并按相应清单核对。若要重建完整历史来源链，须合法取得与原 hash 匹配的材料；本次不重新发布这些材料，也不解除既有来源条件。未来对历史再生流程或执行内核的修复，需要另行明确作用范围与协议，不能把本次 `numerical_pass` 当作新的执行准入。
