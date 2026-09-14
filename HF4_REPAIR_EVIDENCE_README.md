# HF4-B 修正交付：0.5.0

本包包含四条冻结均匀法向接触路径的 0.5.0 实现与完整证据。原 0.4.0 三过一失败的记录在 `hf4_results/`，新结果在 `hf4_repair_results/`。新版本 52 个完整路径接受态 HP 通过，另 2 个首目标态单列；604 个唯一测试通过、1 跳过；独立安装 73 项通过。当前结论不覆盖非均匀二维、圆柱或真实机构资格。

先阅读 [修正报告](docs/HF4_REPAIR_REPORT.md)、[总验收摘要](hf4_repair_results/acceptance_summary.json)、[实现对照](hf_repo/docs/HF4_SPLIT_IMPLEMENTATION.md)。可视化及原值在 [comparison_plots_002](hf4_repair_results/comparison_plots_002/plot_manifest.json)，固定校正干预见 [retained_update_001](hf4_repair_results/retained_update_001/summary.json)。

## 安装与复验

使用 Python 3.13。安装已提供的 `hf_repo/dist/independent_hf_evaluator-0.5.0-py3-none-any.whl`，开发审计/测试另需 [requirements.lock](hf_repo/requirements.lock) 中的工具依赖。精确环境、安装回执及外部运行脚本在 [detached_location.json](hf4_repair_results/detached_location.json)、[prepare_detached.py](hf4_repair_results/prepare_detached.py)；其中机器绝对路径是历史来源信息，需要按新机器实际 Python 路径配置，不应直接复制运行。

以下命令从解压后的 `hf_repo` 目录执行，`python` 指向准备好的独立环境。每次复验选新的输出目录，保存失败/拒绝/子步记录，不覆盖发布证据。

```powershell
python scripts/run_hf4_split_normal.py --spec configs/hf4/validation_spec.json --gamma-index 1 --mesh-index 1 --output ../review_run_g1_m1
python scripts/audit_hf4_split_normal.py --spec configs/hf4/validation_spec.json --run ../review_run_g1_m1 --output ../review_audit_g1_m1 --source-freeze ../hf4_repair_results/source_paths_001/source_freeze.json
python scripts/plot_hf4_split_comparison.py --new-root ../hf4_repair_results --old-root ../hf4_results --output ../review_plots
python -m pytest -q
```

命令选项以相应脚本 `--help` 为准。保存状态的权威输入是 `u_lift` 与 `u_fluctuation` 两个数组；`u_display` 只能画图。不得将显示位移回灌后声称是同一高精度状态。`from_legacy(u)` 只能保持旧 binary64 状态，无法恢复过去丢掉的小量。

`HF4_REPAIR_CONTENT_MANIFEST.json` 绑定本包普通文件，外部 `HF4_repair_release_manifest.json` 绑定 ZIP 自身。旧 `HF4_CONTENT_MANIFEST.json` 与 `HF3_CONTENT_MANIFEST.json` 用于历史来源核对，**不是当前整包的校验清单**。`verify_delivery.py` 可在解压根目录验证新内容清单。部分历史文档链接指向既有 HF1–HF3 包，本包不重复附上全部历史几何/来源档案；本轮合成任务本身不依赖它们或 LF。

依赖 wheel 不随本包分发，需要可用的包源或缓存。已完成的独立验收使用 lock 的精确版本及安装后 RECORD；原依赖下载归档哈希未重新验证。`hf4_repair_results/finalize_stage.py` 是本次汇总复核脚本；运行会生成新的汇总时间戳，应在审查副本使用。数值算例重跑与重新绘图会创建新结果，不是对原记录的替换。
