# HF-4-A/B 部分成果与完整诊断证据

2026-09-14，0.4.0。**A完成；B为3/4组合通过，第四组合未完成。** 原始内部停止容差1e-9、外部HP1e-8及物理参数保持不变。此包不宣称一般二维接触、圆柱或真实夹持性能通过。

## 审查入口

1. [完整执行报告](docs/HF4_AB_REPORT.md)：整体目标、做了什么、原因、效果及边界。
2. [阶段摘要](hf4_results/acceptance_summary.json)：每组目标覆盖、HP、测试、资源及partial状态。
3. [冻结计划](docs/HF4_AB_EXECUTION_PLAN.md)、[参考公式与容差依据](docs/HF4_REFERENCE_AND_TOLERANCE.md)、[配置](hf_repo/configs/hf4/validation_spec.json)。
4. [问题排查](docs/HF4_PRECISION_INVESTIGATION.md)、[固定态证据](hf4_results/fixed_state_probe_001/summary.json)、[更新量证据](hf4_results/fixed_update_probe_001/summary.json)。
5. [后续状态表示方案](docs/HF4_STATE_REPRESENTATION_PLAN.md)：尚未实现，不把建议写成已通过结论。
6. [代码与测试对照](hf_repo/docs/HF4_IMPLEMENTATION.md)、[部分结果图](hf4_results/plots_001/force_gap_vs_d.png)、[新环境重放](hf4_results/detached/summary.json)。

## 文件与版本

`hf_repo/`包含独立源码、测试、小型参考、配置、依赖锁与0.4.0 wheel。`hf4_results/`包含四组模型/状态/原始迭代、所有接受态HP、三个末态50/80对照、参考预检、失败候选/校正量探针、资源账本、源码冻结副本、安装与图。`docs/`提供阶段历史与本轮记录；旧阶段的大型原始证据仍见各自既有发布包。

各载荷文件的SHA-256见`HF4_CONTENT_MANIFEST.json`（清单不包含自身哈希）；该清单及ZIP本身的SHA-256位于包外`deliverables/HF4_AB_release_manifest.json`。这是追加的部分成果包，原HF1/HF2/HF3发布包保留。原395数据文件已按HF3清单核对不变；本合成任务运行不需要这些真实几何，也不需要LF或MATLAB。

## 复验方式

在`hf_repo`中按[安装说明](hf_repo/README.md)建立Python3.13环境、安装锁定依赖和包。使用新输出目录，例如：

```powershell
python scripts/preflight_hf4_reference.py --spec configs/hf4/validation_spec.json --output ../replay/reference
python scripts/run_hf4_normal.py --spec configs/hf4/validation_spec.json --gamma-index 0 --mesh-index 0 --output ../replay/g0_m0
python scripts/audit_hf4_normal.py --spec configs/hf4/validation_spec.json --source-freeze ../hf4_results/production_source_freeze.json --run ../replay/g0_m0 --output ../replay/g0_m0_audit
```

其余组合通过索引0/1选择。第四组合预期保留未达目标状态，而不是必须返回成功。开发脚本的数值预算由外层`hf4_results/run_budgeted.py`监控；原账本不覆盖。复验新路径须记录新预算与新目录，不能在历史结果上覆盖写入。

原始记录中的绝对路径、环境路径与脚本调用用于溯源；复验以当前解压路径和新输出目录为准。缓存HP恢复严格绑定当次输入和脚本哈希；搬迁后可用新目录重新审计，不修改旧绑定伪装同一次运行。完整pytest依赖的小型固定参考随HF仓库提供，完整C-shape历史路径不属于日常测试。

本轮观察到的是当前双精度绝对位移的更新平台，非任意binary64位形不可达的数学证明。有关两分量状态的新方案需独立实现与验证后，才能改变B阶段结论。
