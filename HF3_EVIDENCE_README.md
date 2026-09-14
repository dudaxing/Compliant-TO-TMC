# HF-3 交付证据导航

先读 [总体目标与阶段状态](docs/PROJECT_STATUS.md)，再读 [HF3报告](docs/HF3_REPORT.md)及 [需求—代码—证据对照](docs/REQUIREMENTS_TRACEABILITY.md)。

- `hf_repo/`：独立Git源码快照、精确依赖锁、0.3.0已验收wheel、普通任务/求解JSON、测试与验证脚本。
- `geometry_dataset/`：原395文件，未修改权威几何掩膜或单位/端口含义。
- `hf3_results/`：失败及修正、六个小位移桥接态、两个40目标路径、86态独立HP、图、独立安装和资源。
- `HF3_CONTENT_MANIFEST.json`：包内每个文件SHA-256、源码哈希、Git提交及wheel身份。
- `deliverables/HF2_repaired_evaluator_and_evidence.zip`：上一阶段原包逐字保留，供追溯其特定版本数值证据；不是HF3运行依赖。

数学实现验收不等于物理真值。资格仍pending、功能性未评估、HF4接触未执行。生产文件保留当时的独立精度未评估标识；最终独立结论来自外部审计与总验收摘要。
