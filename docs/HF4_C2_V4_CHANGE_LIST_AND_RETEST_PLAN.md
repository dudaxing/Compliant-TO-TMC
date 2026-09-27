# HF4-C2 v4：最小实现变更清单与有界路径复验方案（待审阅与授权，未实施、未运行）

2026-09-27。起点：`main` = `7e007ca`（已含 P1、稳定 F 候选与无求解验证记录）。本文回答一个问题：保存态上已经改善的运动学求值，进入实际 Newton 求解与路径控制之后，能否让原失败的细网格任务通过既定验收？

本文只是清单和方案。经审阅确认之前，不写 v4 代码；在所有者明确授权新 FE 之前，不运行任何路径。C2 历史 `hf4_c2_diagnostics/experiments/mesh_h00625` 永久保持 `NOT_PASS`，v4 的结果单独记录，不改写它。

## 1. 已核实的现状

- 路径求解器 `hf_eval/split_affine.py` 在模块顶层直接导入旧内核（`from .split_kernel import assemble_split`）。v3 的运行器 `scripts/run_contact_c2.py` 用旧内核记录每个接受态的生产量；它的分量切线作用来自 `run_contact_c1_r2.component_actions`，同样调用旧内核。
- 以上文件都在 v3 协议 `configs/contact_c2_v3.json` 绑定的 33 个实现文件之中。P1 的冻结源码测试也要求它们逐字节不变。所以 **v4 不能通过修改这些文件来换核**。
- v3 的审计 `scripts/audit_contact_c2.py` 用独立 Decimal 参考（80／120 位）核对运行时保存的生产量，这部分与内核无关。但它的协议校验写死了 v3 的模式与三个 case，运行元数据的必需源码也写死了旧内核文件。公开复读入口 `scripts/audit_contact_c2_readback.py` 已经示范过做法：按原样导入并复用冻结审计函数，只替换装载层。
- 原失败路径：`h = 0.0625 mm`、`padding = 2.0 mm`、外底边 driven；7 个均匀目标 0、0.125、0.21875、0.25、0.28125、0.375、0.5 mm；21 个接受态；求解子进程 33.1 s（上限 700 s）；审计 200.0 s（上限 1200 s），末态 `production_vs_hp80_total_force = 1.0943792164e-11 > 1e-11`。
- 候选内核 `split_kernel_compensated` 在固定态上已通过：63 个保存态全部通过，原失败末态 `8.6e-16`。见 [P1／稳定 F 报告](HF4_C2_P1_AND_STABLE_F_REPORT.md)。

## 2. 最小实现变更清单（只新增文件，冻结文件一个字节不改）

| # | 新文件 | 内容 | 约束 |
| --- | --- | --- | --- |
| 1 | `hf_repo/src/hf_eval/split_affine_compensated.py` | `split_affine.py` 的逐字节副本，**只改一行**：`from .split_kernel import assemble_split` 换成 `from .split_kernel_compensated import assemble_split` | 由测试钉住：与冻结的 `split_affine.py` 相比只有这一行不同。Newton、回溯、二分、插入态、容差与所有控制逻辑因此与 v3 完全相同 |
| 2 | `hf_repo/scripts/run_contact_c2_v4.py` | v4 运行器：校验 v4 协议；路径用 #1 求解；每个接受态的生产量（内力、材料与正则分量、切线作用、J）都用补偿内核计算并保存；分量切线作用用补偿内核自己的 JVP（不再借用 `run_contact_c1_r2`）；运行元数据写入模式 `contact_c2_run_v4`、内核版本、编译选项与完整源码哈希 | 输出目录必须是新的；逐态记录格式与 v3 相同，使复用的审计函数可以直接读取 |
| 3 | `hf_repo/scripts/audit_contact_c2_v4.py` | v4 审计入口：按原样导入并复用 `audit_contact_c2.py` 的逐态审计、模型核对与控制器读取函数，只替换协议校验与运行装载（必需源码改为补偿模块与 #1、#2） | 门槛、精度（80／120）、几何与重叠检查全部沿用 v3；由测试钉住复用的函数就是冻结模块中的同一对象 |
| 4 | `hf_repo/scripts/contact_c2_launch_v4.py`、`run_contact_c2_v4_isolated.py` | v4 启动守卫：复用 P1 的通用部件（严格 JSON、哈希绑定、路径限定、回执），常量改为 v4 协议 SHA、单一 case 与 v4 后端。P1 文件本身不改 | 与 P1 相同：建目录、写日志或派发之前完成全部核对，子进程加载后端前再核一次；另外核对解释器版本与锁文件一致（补偿内核需要接受 `xla_cpu_ftz` 的 JAX，锁定的 0.11.0 满足） |
| 5 | `hf_repo/configs/contact_c2_v4.json` | 冻结的 v4 协议 | 见 §3 |
| 6 | `hf_repo/tests/test_contact_c2_v4.py` | #1 与冻结文件的差异只有一行；v4 协议的物理、审计、目标与 v3 逐项相等，逐字段改动都被拒绝；守卫在替身后端下的接受、拒绝与零副作用；审计复用函数的身份；小型合成模型上补偿求解器的路径行为 | 单元测试只用合成小模型（现有测试套件就是这样做的），不运行 C2 case |

**不纳入 v4 的内容：空支座补丁。** C2 的路径用 `displacement._check_support`，它本来就有 `len(fixed_dofs) < 3` 的短路判断；空支座补丁改的是 `tmc.py` 中力控制求解器的 `_check_support`，C2 路径根本不走那里。`tmc.py` 又在 v3 的 33 个绑定文件之中，改它会使 v3／P1 的冻结身份在工作树中失效。所以把它并入 v4 对 v4 没有作用，反而会破坏 v3 身份。这更正了我之前"随 v4 一并并入"的建议。建议等到新的力控制项目入口（例如 HF5 的任务入口）冻结自己的实现身份时再处理。

## 3. v4 协议（冻结前草案）

| 字段 | 取值 |
| --- | --- |
| `schema` | `contact_c2_kernel_repair_v4` |
| `purpose` | 只把运行内核换成 `split_kernel_compensated`（`p26_q1_split_compensated_dot2_v1`），补测 v3 唯一失败的细网格均匀路径 |
| `geometry`、`material`、`solver`、`audit` | 与 v3（以及 C1 v1）逐项相同，由 v4 校验器逐项比对，不在 v4 中重写数值 |
| `uniform_targets_mm` | `[0, 0.125, 0.21875, 0.25, 0.28125, 0.375, 0.5]`（与 v3 相同） |
| `cases`、`run_sequence` | 只有 `mesh_h00625`（`h_mm` 0.0625、`padding_mm` 2.0、`outer_bottom_policy` driven）；序列 `["mesh_h00625"]` |
| `kernel` | 模块名、内核版本、编译选项（`xla_cpu_enable_fast_math=false`、`xla_cpu_ftz=false`）、操作数范围 |
| `saved_field_admission`、`baseline_audits` | 与 v3 相同的准入门与两份 C1 基线审计（哈希不变） |
| `stable_f_evidence` | 无求解验证汇总 `hf4_c2_stable_f_validation/summary_001.json` 的 SHA-256，作为换核的前置证据 |
| `environment` | 锁定版本：CPython 3.13.6、NumPy 2.4.6、SciPy 1.17.1、JAX／jaxlib 0.11.0 |
| `budget` | 1 条路径；求解子进程墙钟 700 s；审计每路径 1200 s；累计求解 700 s、累计审计 1200 s。求解与审计分开计 |
| `stopping` | 与 v3 相同：来源、代数、独立数值或几何、目标不完整任一失败即停；不自动重试，不搜索参数，不扩大资源；失败产物与接受记录全部保留 |
| `storage` | 运行目录在仓库根下新建的 `hf4_c2_v4_results/experiments/mesh_h00625_v4/`，与 `hf_repo` 和历史 C2 目录分开；按 S0 的做法，轻量记录进 Git，逐态大数组放在 Git 之外并附哈希清单 |
| `implementation_sha256` | 冻结时计算：C2 路径实际导入的全部模块（`contact_c2`、`split_affine_compensated`、`split_kernel_compensated`、`compensated_kinematics`、`split_state`、`split_prescribed`、`prescribed`、`displacement`、`tmc`、`tmc_kernel`，以及经 `split_prescribed` 间接载入、但不参与 v4 求值的旧 `split_kernel`），加上 v4 运行器、审计、守卫、`hf4_common.py`、两份独立参考脚本以及被复用的 `audit_contact_c2.py` |

## 4. 有界复验：执行顺序、验收与停止

执行顺序（需要授权）：
1. 实现 #1–#6，在锁定环境运行全量测试。
2. 冻结 v4 协议并单独提交（先于任何运行）。
3. 用守卫做只读计划检查。
4. 求解一次。
5. 独立审计一次。
6. 报告。

**验收**：沿用 v3，不放宽任何门。
- 7 个原目标全部到达。
- 每个存盘状态（包括插入态）都通过独立 80／120 位审计：内力求值 `1e-11`、切线作用 `1e-10`、分量 `1e-9`、80／120 一致 `1e-40`、残差 `1e-9`、约束 `1e-10`、力平衡 `1e-8`，以及几何与重叠容差。
- 通过记为"v4 补测通过"，v3 历史判定不变。

**停止**：
- 首个失效状态出现即停止并保存全部接受记录。
- 超时记为资源性不通过，保留有效前缀。
- 身份或来源不符则在运行前拒绝。
- 不重试，不改 γ、α、容差或门槛，不提高资源上限。

**成本估计**：
- 原求解 33.1 s；补偿内核每次组装约为旧内核的 5 倍（细网格上含切线时 20 ms → 102 ms），预计求解在 1–3 min，远低于 700 s。
- 审计的主要开销是独立 Decimal 参考，与内核无关，预计与原来的 200 s 相近。
- 合计约 5 min，本机串行，单进程。

**结果的含义**：
- 通过说明算术修复在这条完整路径上成立。
- 它不涉及网格收敛、其他网格或平台、接触物理或材料；也不自动改变任何默认入口。
- 是否再用 v4 补测 `padding_2p5` 与 `outer_free`（它们在 v3 中已通过）另行决定，不属于本方案。

## 5. 需要审阅与决定

- **V1** 变更清单的做法：只新增文件；#1 是一行差异的副本；审计与守卫复用冻结部件；P1 与 v3 冻结文件不改；空支座补丁不进 v4。
- **V2** 是否在审阅通过后实施 #1–#6、跑测试并冻结 v4 协议。这一步不运行 FE。
- **V3** 新 FE 的明确授权：本机按 §4 求解并审计一条路径。
- **V4** 新运行的大数组是否沿用 S0 做法，放在 Git 之外并附哈希清单。

HF5 的 H1–H4 另行确认。其中 H1（LF v2 纯数据适配器）不依赖新 FE，可以与 v4 并行，但实施范围需要单独确认。

## 修订 1（2026-09-27，按计划审查）

审查（`research_integration_20260920/external_reviews_20260927_v4_plan/`）指出：§2 第 4 项（守卫写入协议 SHA）与 §3 `implementation_sha256`（清单含守卫）会形成相互引用，无法冻结。本文以上内容保留原样作为审查对象，实施时按下列修订执行：

- **身份分层**：协议清单绑定运行器、审计、共用合同模块、两套内核及其实际导入闭包（共 21 个文件），**不含**启动守卫、隔离入口与被复用的 P1 模块；守卫在协议冻结后写入协议 SHA，这三个文件的哈希记录在协议之外的 `configs/contact_c2_v4_launch_identity.json`，并写入每份启动计划与回执。
- **预算写全三层**：求解器内部 300 s（`solver.time_limit_seconds`）、求解子进程 700 s、审计子进程 1200 s；外部 700 s 不覆盖内部 300 s。
- **停止口径**：
  - "不自动重试"不禁止控制器已声明的回溯与二分。
  - 审计在求解之后进行。
  - 求解失败或超时时，保留全部已落盘接受态；只有通过独立审计的连续部分才称为"已验证可比较前缀"；不增加续算或不完整目录审计功能。
- **测试**：控制器测试只用解析弹簧替身，不运行真实 TMC 小路径；只读启动检查不属于运行。
- **其他**：v3 的 21 个接受态不作为 v4 的要求。成本比取实测值（含切线 5.18 倍、仅力 8.00 倍），"约五分钟"只是粗估。

实施、冻结与检查结果见 [v4 冻结报告](HF4_C2_V4_FREEZE_REPORT.md)。

