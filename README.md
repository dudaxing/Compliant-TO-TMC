# Compliant-TO-TMC：独立 HF 力学评估器

**稳定发布仍为 0.5.0 / HF4-B；HF4-C0 受限参照与 HF4-C1 冻结配对任务已通过各自门禁，HF4-C 一般接触验证仍未完成。** C1 的 10 条选定路径、80 个状态通过 80/120 位独立数值审计及几何门禁；这不代表 TMC 局部单边接触已验证。本仓库保存从开始至今的目标、开发说明、代码、数据和证据，支持在任意新目录接续，不需要原 ChatGPT 对话或原 Windows 工作目录。稳定标签和 0.5.0 wheel 保持原样，新增研究模块使用主分支源码。

先读这些入口：

1. [开发上下文](docs/DEVELOPMENT_CONTEXT.md)：整体目标、为什么分阶段、历次问题与修正、已完成工作、效果和未验证范围。
2. [新电脑接续指南](docs/RESUME_DEVELOPMENT.md)：Python 3.13 环境、校验、读取、测试和新输出目录复验命令。
3. [HF4-C1 最终报告](docs/HF4_C1_FINAL_REPORT.md)、[C1 证据入口](hf4_c1_results/README.md)与[最终摘要](hf4_c1_results/summary_v2/summary.json)：当前配对结果、失败与修正、局部接触边界及下一步。
4. [HF4-C0 研究集成报告](docs/HF4_C0_RESEARCH_INTEGRATION.md)、[C0 接续入口](research_integration_20260920/README.md)：来源审阅、取舍和受限参照验收。
5. [0.5.0 时的项目状态](docs/PROJECT_STATUS.md)、[原需求—代码—证据对照](docs/REQUIREMENTS_TRACEABILITY.md)：保留稳定阶段当时的记录。

## 目标与边界

LF 生成多样化反向器/夹持器几何；HF 在共同、明确的物理任务下独立进行正向力学评价。HF 包不导入 LF、不需要 MATLAB，不包含拓扑优化更新。数据可读、几何资格、求解收敛、模型精度与机构功能分别评价。真实候选资格、一般部分接触与释放、圆柱、稳定性、参数敏感性与最终排名仍待验证。

0.5.0 修正使用 `u_lift` 与 `u_fluctuation` 两个数组保存权威位移，解除已观察的绝对位移更新舍入平台；`u_display` 只作显示。旧物理合同与验收门槛没有改变。以下是稳定发布的历史验收：

- 四条路径均完成 6/6 原目标，52 个完整路径状态通过独立 HP；另有 2 个首目标试运行状态。
- 两次测试去重 604 通过、1 跳过；独立安装验收 73 项通过。
- [HF4 修正完整报告与五张图](docs/HF4_REPAIR_REPORT.md)、[机器可读验收](hf4_repair_results/acceptance_summary.json)、[实现说明](hf_repo/docs/HF4_SPLIT_IMPLEMENTATION.md)。

![新旧完整路径与原第四组失败对照](hf4_repair_results/comparison_plots_002/force_gap_comparison.png)

## 2026-09-20 实验扩展：HF4-C0

新增实体—矩形障碍交面积诊断、严格有效前缀，以及已闭合全接触 A0 参照任务。6 条均匀/非均匀路径、30 个接受态通过 620 项独立数值门和 30 次几何检查；独立有理数几何对照 288/288 通过，新增测试 72/72 通过。首次零接受态的 JAX 配置失败完整保留。

这只验收受限的已闭合分支，没有实现一般主动集或完成 A0/TMC 同任务比较。两网格力差还包含二次底面 profile 的 Q1 边界插值差，离散平均为 `1−a·h²/2`；本轮 `kr=0`，非零 Hu 不构成 HuHu 正则项验收。完整物理合同、原始数据和下一步见[研究报告](docs/HF4_C0_RESEARCH_INTEGRATION.md)与[权威摘要](research_integration_20260920/summary_final/admission_summary.json)。

![A0 力、网格敏感性与独立残差](research_integration_20260920/summary_final/a0_force_and_precision.png)

## HF4-C1：正间隙配对路径与分项诊断

按[冻结协议](docs/HF4_C1_PROTOCOL.md)，先完成 A0/TMC 两网格的四条均匀路径及独立门禁，再完成 A0/Aalpha/TMC 两网格的六条非均匀扰动路径。10 条选定路径共 80 个存盘状态（均匀 50、非均匀 30）通过 80/120 位独立审计与几何检查；选定范围内共有 2516 项独立检查通过，相关测试 173 项通过。状态计数包含阶段起点及插入态，不是 80 个不同物理加载量。

首次 A0 激活失败留下的四个接受态另作为有效前缀保存，该 run 仍不通过。把它们加入历史范围后共有 84 个存盘状态、2644 项独立检查通过；**这一范围包含上述 80 态/2516 项，不能相加或把旧前缀计作第 11 条已准入路径**。最终比较按[选定路径清单](hf4_c1_results/selection_v1.json)去重，详见[权威摘要](hf4_c1_results/summary_v2/summary.json)。

两项修正均保留因果证据：[激活修正](docs/HF4_C1_ACTIVATION_REPAIR.md)只在新增固定自由度上显式移除不超过既定上限的微小 fluctuation；[精度补充](docs/HF4_C1_PRECISION_AUDIT.md)保留原 50/80 位失败审计，统一以 80/120 位核对相同存盘状态，80 位仍为测量权威，物理参数与验收门槛不变。重读当前证据必须显式使用精度补充协议。

已完成[四个 TMC 末态的局部节点反力分项诊断](hf4_c1_results/local_reaction_diagnostic.json)，并保存[分项与正负抵消图](hf4_c1_results/local_reaction_diagnostic.png)。四态的 18 个负节点均位于初始实体 x 跨度 [0,2] 之外；这是参考位置分类，不是实际接触区判定。**节点反力不等同于接触压力，负节点项不能单独证明接触压力失效；净合力吻合也不能证明局部单边接触条件成立。**

下一步依据保存场检查边界材料牵引、正则边界贡献及虚功平衡，再冻结外区边界与网格的单因素诊断；之后才据因果证据定义部分接触参考，不直接进入 HF5 或候选排名。两网格只支持敏感性观察，TMC−Aalpha 还含背景介质、边界及非线性耦合差异。

## 文件位置与历史

| 位置 | 内容 |
|---|---|
| `hf_repo/` | 独立 Python 包、配置、测试、开发审计与依赖锁；[包说明](hf_repo/README.md) |
| `geometry_dataset/` | 395 个普通几何/来源文件，包含两例规范输入；[数据索引](geometry_dataset/dataset_index.json) |
| `docs/` | HF0 至今的计划、核查、报告、原因分析、当前状态和接续指南 |
| `research_integration_20260920/` | LF/N19 来源审阅与取舍、本轮 7 次尝试和 6 份独立审计、最终图表与机器可读摘要；[本轮入口](research_integration_20260920/README.md) |
| `hf4_c1_results/` | C1 的 10 条选定路径、旧激活失败前缀、原 50/80 失败与 80/120 补充审计、诊断、测试及最终比较；[入口](hf4_c1_results/README.md) |
| `hf1_results/`、`hf4_results/`、`hf4_repair_results/` | 主分支内完整普通证据，保留旧失败和新版结果 |
| `hf2_results/`、`hf2_repair_results/`、`hf3_results/` | 摘要、图表、门禁、日志、测试及脚本；大数组/大 HP JSON 从 Release 恢复 |
| `reference_validation/`、`hf0_audit/` | 已生成数值参考、资料身份、独立核查及历史过程；不是 HF 运行依赖 |
| `reference_inputs/hf_start_brief.txt` | 原用户启动任务书，作为历史背景保存 |
| `tools/handoff.py`、`handoff/` | 跨目录校验、环境/几何读取记录、证据下载和逐文件清单 |

原七次 Git 开发提交全部保留。科学基线为 `b1334bb6a83ba9a0efab7bdba7bd39722146f024`；原提交的 HF 代码位于 Git 根，新交接提交将其移至 `hf_repo/`，随后加入外层文档和证据，不改写原提交身份。

阶段阅读顺序：[HF0](docs/HF0_REPORT.md) → [HF1](docs/HF1_REPORT.md) → [HF2 原版](docs/HF2_REPORT.md) → [HF2 修正](docs/HF2_REPAIR_REPORT.md) → [HF3](docs/HF3_REPORT.md) → [HF4 原版](docs/HF4_AB_REPORT.md) → [HF4 修正](docs/HF4_REPAIR_REPORT.md) → [HF4-C0 研究集成](docs/HF4_C0_RESEARCH_INTEGRATION.md) → [HF4-C1](docs/HF4_C1_FINAL_REPORT.md)。旧报告中的“部分完成/未开始”保留其当时事实，最新进度看本页和 C1 最终报告。

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
