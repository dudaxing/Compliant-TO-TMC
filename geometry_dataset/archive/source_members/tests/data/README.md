# 测试金标（E004 从封存证据抽出）

这些文件是 `milestones/` 归档到标签 `e004-archive-v1`（提交 `689c748`）之前，内核测试仍直接读取的封存证据。
三个是逐字节副本（SHA-256 与来源文件一致），一个是只含测试所需键的 NPZ 子集（每个数组的字节 SHA-256 记在 E004 台账里）。
它们不是新的证据，测试断言也没有改动；来源文件的原始位置可用 `git checkout e004-archive-v1 -- <路径>` 恢复。

| 文件 | 来源（标签中的路径） | 形式 | 字节 | SHA-256 | 使用它的测试 |
| --- | --- | --- | ---: | --- | --- |
| `A002_auto_gradient_reference_v1.npz` | `milestones/M0/addenda/A002_auto_gradient_reference_v1.npz` | 逐字节副本 | 113,121 | `968d8421ded36847…` | `tests/test_m2_adjoint.py`、`tests/test_m3_optimizer.py` |
| `M2_C_result_v1.json` | `milestones/M2/C/result_v1.json` | 逐字节副本 | 387,731 | `3a114a76b6a3ed25…` | `tests/test_verification.py` |
| `M4_battery_v2_m3_final_160_p3_160x80_metrics.json` | `milestones/M4/battery_v2/m3_final_160_p3_160x80/metrics.json` | 逐字节副本 | 12,065 | `6592cd3da3249555…` | `tests/test_measure_case.py` |
| `M4_battery_v2_m3_final_160_p3_160x80_arrays_subset.npz` | `milestones/M4/battery_v2/m3_final_160_p3_160x80/arrays_v1.npz` | 数组子集（measurement_rho_physical、u_free、w、u_block、u_direct_khat_1、U_total） | 976,107 | `28dcdfb42ceb9a7f…` | `tests/test_measure_case.py` |

完整哈希见 [E004 台账](../../errata/E004_milestones_archive_v1/archived_milestones_ledger_v1.json) 的 `test_oracles` 字段。
