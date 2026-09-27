# 稳定 F 的无求解验证记录（2026-09-27）

报告：[docs/HF4_C2_P1_AND_STABLE_F_REPORT.md](../docs/HF4_C2_P1_AND_STABLE_F_REPORT.md)。执行前修订：[docs/HF4_C2_STABLE_F_VALIDATION_AMENDMENT_001.md](../docs/HF4_C2_STABLE_F_VALIDATION_AMENDMENT_001.md)。

每个运行目录都由 `tools/run_c2_bounded_validation.py` 创建，内含 `execution_plan.json`（命令、环境、超时、源码 SHA 与相对基线 `7fea2e4` 改动过的源码快照）、`execution_receipt.json`（退出码、是否超时、墙钟、运行中源码是否改动、输出哈希）、`stdout.log` 与 `stderr.log`。验证驱动的输出在 `driver_output/`。

| 目录 | 内容 | 状态 |
| --- | --- | --- |
| `arithmetic_001/` | 补偿算术与导数的单元测试 | 28 passed |
| `manufactured_001/` | 33 个制造场 case（含旧内核对照、有限差分曲线、编译证据） | 30／33；3 个 `near_rotation` 为分辨率限制，新旧内核相同 |
| `saved_001/` | 第一次保存态尝试，在输入绑定阶段停止（修订 002 之前），0 个状态 | 失败，原样保留 |
| `saved_002/` | 计划选定的 8 个保存态 | 8／8 |
| `saved_all_c2_001/` | 全部 59 个 C2 状态与 4 个 C1 末态 | 63／63 |
| `timing_001/` | 两核组装计时（不设门） | — |
| `summary_001.json` | 只读汇总（`hf_repo/scripts/summarize_contact_c2_stable_f.py`），绑定全部输入哈希 | — |
| `plots_001/` | 三张图：制造场门槛比（含旧内核对照）、保存态对比、方向差分曲线 | — |

复现方式：
- 先建立基线：在独立目录检出 `7fea2e4`，用 `tools/handoff.py fetch-evidence --asset hf4-c2-s0-c1_runs-v1.zip` 与 `--asset hf4-c2-s0-c2_runs-v1.zip` 恢复两个资产，再逐个 `verify --asset`。
- 然后在本分支执行：`python tools/run_c2_bounded_validation.py --output hf4_c2_stable_f_validation/<新目录> --category <类别> -- <python> -B hf_repo/scripts/validate_contact_c2_stable_f.py <manufactured|saved> --baseline <基线目录> --output hf4_c2_stable_f_validation/<新目录>/driver_output`。

保存态阶段的候选输出数组 `saved_*/driver_output/*/production.npz`（71 个文件，30.1 MB）不进 Git，以保持 S0 之后的轻量主树。它们打包为 `hf4-c2-stable-f-saved-production-arrays-v1.zip`，保存在所有者本机的 `Compliant-TO-TMC-evidence/hf4-c2-stable-f-v1/`；清单是 [local_evidence_archive_001.json](local_evidence_archive_001.json)，含整包与每个成员的 SHA-256，并已与各运行 `output_sha256.json` 中的记录逐一核对一致。这些数组可以由已提交的代码和 S0 发布资产重新生成，所有检查值都在已提交的逐态 `result.json` 里。是否作为发布附件公开，由所有者决定。

这些是固定态与制造场的检查，不求解平衡路径，也不构成路径准入。
