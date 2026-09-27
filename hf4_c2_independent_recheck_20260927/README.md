# 2026-09-27 独立复核证据

这是从原 `c2_p1_f_workspace` 开展的独立复核。它与已经合入主分支的 `hf4_c2_stable_f_validation/` 不是同一次运行；同名子目录也不能覆盖或合并。两轮共同案例的结果一致，仍只有 33 个制造场和 8 个选定保存态，不能重复计数。

- `arithmetic_001`：28 项通过。
- `manufactured_001/results`：33 例中 30 例通过；三个 near_rotation 力失败，解析切线均通过。
- `saved_001/results`：原读取假设导致输入绑定失败，0 态，异常保留。
- `saved_002/results`：修正 C1/C2 来源读取后 8 态通过，NPZ 原始输出随本目录提交。
- `plots_001`：首次三张图；`plots_002` 改善图例位置，读取相同数值记录。
- `copy_inventory.json`：从原工作树复制时的逐文件字节与 SHA；原树继续保留。
- `acceptance_summary.json`：只读汇总，含集成复验与原复算逐检查值、NPZ 字节相等的结果。
- `summarize_recheck.py`：生成上述摘要的标准库脚本，不运行力学；已有输出不会覆盖。

完整解释见[复核报告](../docs/HF4_C2_INDEPENDENT_RECHECK_REPORT_20260927.md)。原始 plan、receipt 中的命令和绝对 cwd 保留运行当时原字节，不能在异机直接照抄。其引用的原 `hf4_c2_stable_f_validation/<run>` 对应本目录同名 `<run>`。源码快照在每个进程的 `source_snapshot/`，输入/输出哈希保持不变。

最新集成后的可执行驱动仍为 `hf_repo/scripts/validate_contact_c2_stable_f.py`，其首次复验保存于 `hf4_c2_stable_f_validation/independent_saved_20260927_001`。候选生产内核未变。图脚本只处理已存 JSON；旧图脚本副本与图回执保留，改进版在 `plot_recheck_records.py`。

## 新机器复算

先按 `docs/RESUME_DEVELOPMENT.md` 建立锁定 Python 3.13/JAX 0.11.0 环境。从同一仓库另建基线工作树，例如在仓库根目录运行：

```text
git worktree add --detach ../hf-s0-reference 7fea2e44b67d0eff421219ebbcac68c506fb9d2f
python ../hf-s0-reference/tools/handoff.py fetch-evidence --asset hf4-c2-s0-c1_runs-v1.zip --asset hf4-c2-s0-c2_runs-v1.zip
python ../hf-s0-reference/tools/handoff.py verify --asset hf4-c2-s0-c1_runs-v1.zip --asset hf4-c2-s0-c2_runs-v1.zip
```

然后从当前仓库根目录执行下列命令；`<python>` 为该机器环境的实际解释器路径，输出目录必须不存在：

```text
<python> tools/run_c2_bounded_validation.py --output hf4_c2_stable_f_validation/my_saved_recheck --category saved -- <python> hf_repo/scripts/validate_contact_c2_stable_f.py saved --baseline ../hf-s0-reference --output hf4_c2_stable_f_validation/my_saved_recheck/results
```

制造场对应将 `saved` 换为 `manufactured`，并使用另一个新输出目录。图可从本目录现有结果直接生成，不需要恢复大资产。参考文件的字节身份固定，不能更新旧清单、降低门槛或用本机绝对路径占位文件使校验通过。上面两资产名称以冻结基线的 `evidence_assets.json` 为准；没有请求新 FE。
