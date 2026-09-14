# HF-2 精度修正交付包

本包保存0.2.1修正实现与独立证据，同时保留0.2.0的原始路径、失败判定和wheel。最终判定见 [修正报告](docs/HF2_REPAIR_REPORT.md) 及 `RELEASE.json`。HF-3未在本轮执行，物理接触精度和真实机构性能尚未验证。

修正保持网格、材料、载荷、九点积分及完整非保守HuHu项；材料内力采用等价直接第一Piola表达，对实际残差重新求Jacobian。新版基准内部停止值为10⁻⁹，独立外部平衡门槛仍为10⁻⁸。旧位移被新表达准确重算后仍可能不平衡，不能追溯改变旧实现的判定。

| 内容 | 包内位置 |
|---|---|
| 修正前的复审与冻结执行方案 | `docs/HF2_REPAIR_EXECUTION_PLAN.md`及两个独立审阅文档 |
| 独立安装、CLI与通用API | `hf_repo/README.md` |
| 新0.2.1及原0.2.0 wheel | `hf_repo/dist/` |
| 固定primitive输入及机读规则 | `hf_repo/validation/hf2_repair/` |
| 完整回归记录 | `hf2_repair_results/full_regression.xml` |
| 原16案例、976项参考检查 | `hf2_repair_results/small_reference_001/` |
| 三旧状态、192项求值与切线检查 | `hf2_repair_results/strong_precision_001/`、`strong_precision_report.md` |
| 唯一修正Python完整路径 | `hf2_repair_results/cshape_python_001/` |
| 新Python与原MATLAB的逐目标对账 | `hf2_repair_results/response_comparison_001/` |
| 新旧三条路径的全状态高精度复核 | `hf2_repair_results/full_precision_audit_resumed_001/`；原299态停止记录保留在`full_precision_audit_001/` |
| 新wheel独立安装、24项检查及访问审计 | `hf2_repair_results/detached/` |
| 本次资源时账与发布完整性 | `hf2_repair_results/resource_jobs/`、`release_integrity.json` |
| 原HF-2失败证据与Python路径 | `hf2_results/` |
| 原MATLAB完整路径的普通数字数据 | `reference_validation/matlab/cshape_001/` |
| 未修改的两例HF-1几何及完整来源数据 | `geometry_dataset/`，共395文件 |

包内不含原MATLAB代码、MAT文件、LF代码、原ZIP/PDF或虚拟环境。`hf2_repair_results/baseline/tmc_kernel_0_2_0.py` 是我们自己的旧HF内核，仅供同输入原因对照。原 `hf2_results/residual_sensitivity_001/probe.py` 的末尾来源哈希采集依赖研究工作区的原MATLAB源码，是原样保存的历史脚本；新版高精度验证脚本不需要该源码。

完整路径NPZ包含所有目标的位移、J、反力、内力及分域材料能量；不重复打包非线性求解的逐步检查点。原高精度分块检查点保留以支持续检来源核对。高精度残差字符串及判定保存在JSON/CSV中，50/80位交叉的完整Decimal力向量另存字符串NPZ；其余HP数组为浮点视图。原比较程序仍同时检查旧MATLAB平衡，因而其`not_pass`应与新版独立判定分别阅读。

安装锁定依赖和新wheel后，可从解压根目录仅用普通数组重做全路径离线核验：

```powershell
python hf_repo/scripts/validate_hf2_repaired_path.py --fixture hf_repo/validation/hf2_repair/strong_inputs.npz --spec hf_repo/validation/hf2_repair/precision_spec.json --new-python hf2_repair_results/cshape_python_001 --old-python hf2_results/cshape_python_001 --matlab reference_validation/matlab/cshape_001 --comparison hf2_repair_results/response_comparison_001/summary.json --output new-offline-audit
```

此命令不重新求解路径。其内部590秒保护在本机留下299/300已完成状态，因此保留了这次不完整作业，并在续检前以`resource_amendment_001.json`将后处理累计额度由600调整到720秒（总数值额度3000秒、外部1e-8门槛不变）。本包另含`hf_repo/scripts/resume_hf2_repaired_path.py`及其续检输出与输入哈希；它复用已落盘数组、恢复50/80位交叉摘要并补齐最后十个旧MATLAB数组，没有重复完整非线性路径。

原路径与新路径均不覆盖；所有新输出目录须另取名称。历史文档中的工作区绝对路径只作来源记录，部分历史原始附件不随本包分发。

本次独立安装使用缓存中的精确锁定版本，并核对安装后的RECORD文件哈希；第三方原wheel压缩包未在这次离线安装重新核对下载哈希。HF自身wheel的SHA-256及10个运行源文件另行核对。`PACKAGE_FILES.json`包含每个实文件的路径、大小和SHA-256，自身除外；外部发布清单给出最终ZIP哈希。
