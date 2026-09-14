# Compliant-TO-TMC：独立 HF 力学评估器

**当前状态：0.5.0，HF4-B 四组冻结均匀法向任务已完成；下一步准备 HF4-C 非均匀二维接触验证计划。** 本仓库保存从开始至今的目标、开发说明、当前代码、数据和证据，支持在任意新目录接续，不需要原 ChatGPT 对话或原 Windows 工作目录。

先读这三份文件：

1. [开发上下文](docs/DEVELOPMENT_CONTEXT.md)：整体目标、为什么分阶段、历次问题与修正、已完成工作、效果和未验证范围。
2. [新电脑接续指南](docs/RESUME_DEVELOPMENT.md)：Python 3.13 环境、校验、读取、测试和新输出目录复验命令。
3. [当前状态与下一步](docs/PROJECT_STATUS.md)、[需求—代码—证据对照](docs/REQUIREMENTS_TRACEABILITY.md)。

## 目标与边界

LF 生成多样化反向器/夹持器几何；HF 在共同、明确的物理任务下独立进行正向力学评价。HF 包不导入 LF、不需要 MATLAB，不包含拓扑优化更新。数据可读、几何资格、求解收敛、模型精度与机构功能分别评价。真实候选资格、一般非均匀接触、圆柱、稳定性、参数敏感性与最终排名仍待验证。

当前修正使用 `u_lift` 与 `u_fluctuation` 两个数组保存权威位移，解除已观察的绝对位移更新舍入平台；`u_display` 只作显示。物理参数与验收门槛没有改变。

- 四条路径均完成 6/6 原目标，52 个完整路径状态通过独立 HP；另有 2 个首目标试运行状态。
- 两次测试去重 604 通过、1 跳过；独立安装验收 73 项通过。
- [HF4 修正完整报告与五张图](docs/HF4_REPAIR_REPORT.md)、[机器可读验收](hf4_repair_results/acceptance_summary.json)、[实现说明](hf_repo/docs/HF4_SPLIT_IMPLEMENTATION.md)。

![新旧完整路径与原第四组失败对照](hf4_repair_results/comparison_plots_002/force_gap_comparison.png)

## 文件位置与历史

| 位置 | 内容 |
|---|---|
| `hf_repo/` | 独立 Python 包、配置、测试、开发审计与依赖锁；[包说明](hf_repo/README.md) |
| `geometry_dataset/` | 395 个普通几何/来源文件，包含两例规范输入；[数据索引](geometry_dataset/dataset_index.json) |
| `docs/` | HF0 至今的计划、核查、报告、原因分析、当前状态和接续指南 |
| `hf1_results/`、`hf4_results/`、`hf4_repair_results/` | 主分支内完整普通证据，保留旧失败和新版结果 |
| `hf2_results/`、`hf2_repair_results/`、`hf3_results/` | 摘要、图表、门禁、日志、测试及脚本；大数组/大 HP JSON 从 Release 恢复 |
| `reference_validation/`、`hf0_audit/` | 已生成数值参考、资料身份、独立核查及历史过程；不是 HF 运行依赖 |
| `reference_inputs/hf_start_brief.txt` | 原用户启动任务书，作为历史背景保存 |
| `tools/handoff.py`、`handoff/` | 跨目录校验、环境/几何读取记录、证据下载和逐文件清单 |

原七次 Git 开发提交全部保留。科学基线为 `b1334bb6a83ba9a0efab7bdba7bd39722146f024`；原提交的 HF 代码位于 Git 根，新交接提交将其移至 `hf_repo/`，随后加入外层文档和证据，不改写原提交身份。

阶段阅读顺序：[HF0](docs/HF0_REPORT.md) → [HF1](docs/HF1_REPORT.md) → [HF2 原版](docs/HF2_REPORT.md) → [HF2 修正](docs/HF2_REPAIR_REPORT.md) → [HF3](docs/HF3_REPORT.md) → [HF4 原版](docs/HF4_AB_REPORT.md) → [HF4 修正](docs/HF4_REPAIR_REPORT.md)。旧报告中的“部分完成/未开始”保留其当时事实，最新进度看本页和当前状态。

## 快速取得与恢复

```text
git clone https://github.com/dudaxing/Compliant-TO-TMC.git my-hf-work
cd my-hf-work
python tools/handoff.py verify
```

校验仅需 Python 标准库。后续安装按照[接续指南](docs/RESUME_DEVELOPMENT.md)，不要照抄历史 `.venv`、临时目录或累计预算脚本。开发修改后清单会如实报告变化；应使用 Git 记录修改，为新数值实验另建源码冻结和输出。

完整早期原始证据及原样 0.5.0 交付 ZIP 在 [GitHub Release](https://github.com/dudaxing/Compliant-TO-TMC/releases/tag/hf-history-0.5.0)：

```text
python tools/handoff.py fetch-evidence
python tools/handoff.py verify --full
```

下载会校验附件和每个成员，并拒绝覆盖不同的已有文件。原论文、原 MATLAB/LF 源包不作为公开附件；资料身份、取得方式、旧 ZIP 链接和许可核查见[来源与发布说明](docs/SOURCE_MATERIALS_AND_PUBLICATION.md)。已有源路径只作来源记录。迁移校验不等同于新平台力学验收。
