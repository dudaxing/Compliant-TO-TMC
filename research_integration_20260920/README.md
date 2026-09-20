# 2026-09-20 新研究融合交接

**当前状态：HF4-C0 受限参照准入通过；HF4-C 一般接触及项目整体仍在开发中。**

先读 [完整实现与实验报告](../docs/HF4_C0_RESEARCH_INTEGRATION.md)，再按需要看 [来源审计](LF10_SOURCE_AUDIT.md)、[N19 与代码复核](N19_SOURCE_AND_CODE_REVIEW.md)、[取舍理由](INTEGRATION_DECISIONS.md)、[预先计划](EXPERIMENT_PLAN.md)、[机器可读结论](summary_final/admission_summary.json)。`input_inventory.json` 记录用户附件身份和 SHA256，其中绝对路径仅作来源记录，程序不依赖它们。

本轮新增 6 条 A0 路径、30 状态、620 项独立数值门、30 次几何检查、288 个有理数几何对照及 72 个测试。原 0.5.0 内核、HP helper、物理合同、几何包和历史证据未改。详见报告的通过范围，不能把 A0 解释为一般主动集或完整 TMC 接触验收。

## 文件与权限边界

- `results/`：6 条成功路径和首次配置失败；每条包含普通 JSON/NPZ、源代码/任务/状态哈希及执行收据。NPZ 不需要 pickle。
- `summary_final/`：权威汇总、PNG/SVG、几何与前缀负例；绘图合并位移不是权威力学状态。
- `geometry_rational_audit.json`：全部独立有理数面积对照及精确分数。
- 用户提供的完整 ZIP、N19 解压源码、MATLAB/PDF、原 ChatGPT 会话缓存只在本地作为参考；公开仓库提供必要的来源摘要、哈希、取舍和我们独立新增的实现，不依赖这些本地参考文件运行。

新机器可以直接重做本轮 A0 与几何实验。若要重新审阅 N19 全部源码或导入新 LF 的 1800 个候选，仍须取得与 `input_inventory.json` 中 SHA256 一致的原附件；这项后续数据准备不包含在本轮的独立运行依赖中。

## 在另一台机器复核

在仓库根目录，用 Python 3.13 和 `hf_repo/requirements.lock` 建立独立环境；原稳定包的安装步骤见仓库 `docs/RESUME_DEVELOPMENT.md`。本轮脚本从自身位置解析 `hf_repo/src`，不要求当前目录与原作者目录相同。以下用 `python` 表示已配置好的解释器；运行输出必须选择新目录。

```powershell
python -m pytest hf_repo/tests/test_contact_audit.py hf_repo/tests/test_contact_reference_a0.py hf_repo/tests/test_contact_reference_a0_audit.py -q
python hf_repo/scripts/audit_contact_geometry_rational.py --output NEW_geometry_audit.json
python hf_repo/scripts/audit_contact_reference_a0.py --run research_integration_20260920/results/a0_h025_a000_r1 --output NEW_a0_audit.json
python hf_repo/scripts/run_contact_reference_a0_isolated.py --mode solve --run NEW_RESULTS/a0_h025_a000 --h 0.25 --amplitude 0
python hf_repo/scripts/run_contact_reference_a0_isolated.py --mode audit --run NEW_RESULTS/a0_h025_a000
```

先独立验收粗均匀，再细均匀，再其他四个协议组合；不要覆盖现有证据。独立 HP 审计对源文件和保存哈希有严格绑定；如有新实现修改，应冻结为新的来源与结果版本，不把旧状态当成新代码的通过证据。`audit.json` 内记录的原机器绝对路径是审计时来源说明，新机器重审时会重新解析本地路径。

下一阶段是明确同一物理任务下 A0/实体接触与 TMC 的配对比较，并扩展激活、释放和有限边缘失败。当前仍不启动新的 LF 优化或 1800 例 HF 标签计算。完整后续边界见报告。
