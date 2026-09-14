# HF-2 独立交付与证据导航

**阶段状态：部分完成。** 100个目标的源码响应一致性通过，但Python λ=0.73、MATLAB λ=0.76及0.99三个存档状态的50位独立残差超过原10⁻⁸门槛。原始失败记录保留；没有修正后完整路径或HF-3结果。

先读 [HF-2执行报告](docs/HF2_REPORT.md)，安装与接口见 [HF仓库](hf_repo/README.md)。[有限修正计划](docs/HF2_REPAIR_PLAN.md) 与 [HF-3预备计划](docs/HF3_PLAN.md) 均为未执行提案。历史核查文档的原资料路径仅作来源记录，部分历史原始附件保留在研究工作区，不随本包分发。

| 内容 | 位置 |
|---|---|
| 独立源码、锁定依赖、185通过/1跳过的测试 | `hf_repo/` |
| 经新环境复验的0.2.0 wheel | `hf_repo/dist/` |
| HF-1原两例及来源数据，共395文件 | `geometry_dataset/` |
| 冻结定义与普通小型数值参考 | `hf_repo/validation/hf2/`、`hf_repo/tests/fixtures/hf2/` |
| 小规模976项跨语言检查及差分曲线 | `hf2_results/small_validation_001/` |
| Python原100步路径、模型、结果与图 | `hf2_results/cshape_python_001/` |
| MATLAB导出的普通NPZ/JSON原100步路径 | `reference_validation/matlab/cshape_001/` |
| 全100目标误差及三个严格平衡失败标记 | `hf2_results/cshape_comparison_001/` |
| 固定存档状态的50位取证 | `hf2_results/residual_sensitivity_001/` |
| 最终科学判定 | `hf2_results/cshape_final_decision.json` |
| 17项独立验收、4511个RECORD核对与访问审计 | `hf2_results/detached/` |
| 含失败作业的363.53秒共享时账 | `hf2_results/resource_jobs/` |
| 文件与原资料完整性核对 | `hf2_results/release_integrity.json` |

MATLAB源文件、MAT文件、原ZIP/PDF、LF导出器和虚拟环境均不分发。完整路径的普通NPZ已经保存各目标数组，未重复打包100个Python逐步检查点。Git保留代码、小参考和紧凑结论；完整路径证据随ZIP提供。50位取证的原 `probe.py` 作为研究工作区记录保留，其末尾来源哈希采集需要未分发的MATLAB源码；独立数值内核及下述全路径比较不依赖该源码。

日后在已安装锁定依赖的环境中，可仅从存档数组重新生成比较结果，无须MATLAB或完整求解。以下是复验说明，本次打包没有再次执行：

```powershell
python hf_repo/scripts/compare_cshape.py --python hf2_results/cshape_python_001 --matlab reference_validation/matlab/cshape_001 --spec hf_repo/validation/hf2/validation_spec.json --output new-comparison
```

该比较预期返回未通过状态，因为独立平衡的三个失败项仍存在。`cshape_comparison_001/validation_spec_used.json` 是首次比较时的精确说明版本，仅增加合力公式说明；冻结原规范另存，门槛未改变。原比较记录及其哈希不重写。

独立重放曾遇到在线CDN超时，最终从缓存按锁定版本安装并核对安装后的RECORD文件哈希；第三方原wheel压缩包没有在离线重放重新核对锁定哈希。HF自身wheel的SHA-256、10个运行源文件和全路径运行版本已核对。第一次独立重放的报告序列化失败也单独保留日志；修复仅涉及验收脚本。

`RELEASE.json` 记录Git提交、wheel哈希及科学状态；`PACKAGE_FILES.json` 列出所有实文件的包内路径、大小和SHA-256，自身除外。包外发布清单给出最终ZIP哈希。
