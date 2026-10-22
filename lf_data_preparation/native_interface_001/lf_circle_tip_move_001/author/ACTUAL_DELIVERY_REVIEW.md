# L-CTIPMOVE1 实际交付审阅

2026-10-22（Asia/Seoul）；结论：**12/12检查通过，无阻断发现**。

本次审阅独立核对交付文档、实际新普通JSON、源码身份和ZIP清单，不是重复数值计算。审阅者参与新增测试编写，因此本报告不冒称独立测试设计认证或独立物理复算。

## 实际核对

- **D01 PASS**：Actual stored JUnit summary: 15 passed, old9/new6. No test execution during this review.
- **D02 PASS**：New probe model cache: 16 cells/25 nodes/50 DOF, original four body nodes retained.
- **D03 PASS**：Three raw JSON records show independent q and constant mean; actual prescribed error reported0.
- **D04 PASS**：Raw JSON production metrics all within unchanged gates; this is not new force/HP verification.
- **D05 PASS**：q0 recorded state identity, signed R and first fresh check are preserved. Split NPZ bytes were not decoded in this review.
- **D06 PASS**：Negative Q means a negative-x actuator/brake is needed against positive-x model force in this held guided fixture. No absolute-value pullout-capacity claim; units already contain fixture thickness2mm.
- **D07 PASS**：Raw JSON exposes separate body-x drive, body-y guide and remaining support ledger. Independent node/local aggregation was executed inside the approved tests; this read-only review does not repeat it.
- **D08 PASS**：Controlled second-tangent exception retains q0 partial and settings, explicitly test-only, not an observed physical constraint failure.
- **D09 PASS**：New runtime counters3/14 plus legacy static enumeration1/11, admitted after all9 old tests passed. One controlled real partial overlaps axes; old enumeration is not per-hook runtime instrumentation.
- **D10 PASS**：All four SUP2 layers pass same-instance/coverage/handle closure; RSS is sampled observation, not proof of every instantaneous allocation.
- **D11 PASS**：Two installed sources exactly match executed candidates and receipt; six key default/parser/kernel/CLI files equal baseline1e5e9cf. No post-install numerical rerun.
- **D12 PASS**：186-member archive names/sizes and whole-archive SHA match; delivery docs accurately keep real-r9/HP/bearing/release pending and local historical scripts nonportable for blind rerun. PNG QA is the recorded root single inspection, not independently reopened here.

## 主要数值与解释

|q mm|input mean mm|Q_half N|min J|free relative residual|
|---|---|---|---|
|0.0|0.0005|-3.2165873870361e-08|0.99874371600168|7.8460372271962e-10|
|0.00025|0.0005|-1.6275064208363e-08|0.99924371669024|5.6409336734089e-15|
|0.0005|0.0005|-4.2136491688224e-10|0.99974371737691|6.1560972000768e-15|

三态Q均为负；在此受导向的小模型中，模型对工件的+x作用需由-x驱动／制动平衡。不能翻正号后称为抗拔承载。半模型力已含t2mm；真实r9、力控承载、自由竖移／转动、释放与HP均未验证。

q0记录SHA与来源选定态一致，R保原符号及数值，首次fresh check为1；实际两数组位级比较由唯一窗口测试完成，本审阅未解码NPZ重做。新受控partial仅q0接受、原settings不变、rollback为true；其constraint_failure是人为测试异常，不能写成物理失败。

## 覆盖与限制

- 15 cases cover the approved finite old/new controller/probe scope, not whole-repository regression.
- Legacy path/rejection1/11 counts are source enumeration conditioned on old9 passing, not separately instrumented runtime hooks.
- Negative Q is guided-fixture braking, not real-gripper bearing or release.
- PNG was not reopened; its pass_with_visibility_limits and one inspection are taken from root QA receipt.
- No NPZ decoded, HF API imported, F/T/HP/equilibrium/test executed, old r9 arrays read, PNG opened, or ROOT files changed by this review.
- Only new small-model results and frozen command/source closure support the runtime-scope claim; no claim of independent system-wide file-access tracing.
- Publication/restoration was pending at the reviewed report snapshot; do not preclaim remote synchronization.

实际源路径：`D:/hmv1_001/run_001/artifacts/real16/probe/result.json`、同级`controlled_partial/result.json`，不是`window_result/helper_result`目录。两份生产源码与已测候选同SHA；默认fixed入口及六个关键旧文件逐字节保持基线。完整输入身份、12项依据与四层监督指标见同名JSON。

本审阅只写外部AUTHOR的本报告及JSON，不修改正式ROOT。下一步仅按NEXT_STEPS准备真实探针来源／bbox／显示包装；新增真实F/T或路径需明确新窗口。
