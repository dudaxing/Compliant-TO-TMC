# v4 计划审查：原始源码与计划定位摘录
来源：本轮上传的 `Compliant-TO-TMC-claude-hf4-c2-v4-plan.zip`，ZIP 注释为 `a652a3fe5e9ccbc1b61ad0e90713bd01eb3a2da4`。以下行号是原文件行号。摘录不是新实现，也不是运行结果。

## docs/HF4_C2_V4_CHANGE_LIST_AND_RETEST_PLAN.md
原字节 SHA-256：`974ec06c5703958beb3f20e2287b8df25b8c1c07641063a564766b716c30b462`

### 第 1–84 行

```text
   1 | # HF4-C2 v4：最小实现变更清单与有界路径复验方案（待审阅与授权，未实施、未运行）
   2 | 
   3 | 2026-09-27。起点：`main` = `7e007ca`（已含 P1、稳定 F 候选与无求解验证记录）。本文回答一个问题：保存态上已经改善的运动学求值，进入实际 Newton 求解与路径控制之后，能否让原失败的细网格任务通过既定验收？
   4 | 
   5 | 本文只是清单和方案。经审阅确认之前，不写 v4 代码；在所有者明确授权新 FE 之前，不运行任何路径。C2 历史 `hf4_c2_diagnostics/experiments/mesh_h00625` 永久保持 `NOT_PASS`，v4 的结果单独记录，不改写它。
   6 | 
   7 | ## 1. 已核实的现状
   8 | 
   9 | - 路径求解器 `hf_eval/split_affine.py` 在模块顶层直接导入旧内核（`from .split_kernel import assemble_split`）。v3 的运行器 `scripts/run_contact_c2.py` 用旧内核记录每个接受态的生产量；它的分量切线作用来自 `run_contact_c1_r2.component_actions`，同样调用旧内核。
  10 | - 以上文件都在 v3 协议 `configs/contact_c2_v3.json` 绑定的 33 个实现文件之中。P1 的冻结源码测试也要求它们逐字节不变。所以 **v4 不能通过修改这些文件来换核**。
  11 | - v3 的审计 `scripts/audit_contact_c2.py` 用独立 Decimal 参考（80／120 位）核对运行时保存的生产量，这部分与内核无关。但它的协议校验写死了 v3 的模式与三个 case，运行元数据的必需源码也写死了旧内核文件。公开复读入口 `scripts/audit_contact_c2_readback.py` 已经示范过做法：按原样导入并复用冻结审计函数，只替换装载层。
  12 | - 原失败路径：`h = 0.0625 mm`、`padding = 2.0 mm`、外底边 driven；7 个均匀目标 0、0.125、0.21875、0.25、0.28125、0.375、0.5 mm；21 个接受态；求解子进程 33.1 s（上限 700 s）；审计 200.0 s（上限 1200 s），末态 `production_vs_hp80_total_force = 1.0943792164e-11 > 1e-11`。
  13 | - 候选内核 `split_kernel_compensated` 在固定态上已通过：63 个保存态全部通过，原失败末态 `8.6e-16`。见 [P1／稳定 F 报告](HF4_C2_P1_AND_STABLE_F_REPORT.md)。
  14 | 
  15 | ## 2. 最小实现变更清单（只新增文件，冻结文件一个字节不改）
  16 | 
  17 | | # | 新文件 | 内容 | 约束 |
  18 | | --- | --- | --- | --- |
  19 | | 1 | `hf_repo/src/hf_eval/split_affine_compensated.py` | `split_affine.py` 的逐字节副本，**只改一行**：`from .split_kernel import assemble_split` 换成 `from .split_kernel_compensated import assemble_split` | 由测试钉住：与冻结的 `split_affine.py` 相比只有这一行不同。Newton、回溯、二分、插入态、容差与所有控制逻辑因此与 v3 完全相同 |
  20 | | 2 | `hf_repo/scripts/run_contact_c2_v4.py` | v4 运行器：校验 v4 协议；路径用 #1 求解；每个接受态的生产量（内力、材料与正则分量、切线作用、J）都用补偿内核计算并保存；分量切线作用用补偿内核自己的 JVP（不再借用 `run_contact_c1_r2`）；运行元数据写入模式 `contact_c2_run_v4`、内核版本、编译选项与完整源码哈希 | 输出目录必须是新的；逐态记录格式与 v3 相同，使复用的审计函数可以直接读取 |
  21 | | 3 | `hf_repo/scripts/audit_contact_c2_v4.py` | v4 审计入口：按原样导入并复用 `audit_contact_c2.py` 的逐态审计、模型核对与控制器读取函数，只替换协议校验与运行装载（必需源码改为补偿模块与 #1、#2） | 门槛、精度（80／120）、几何与重叠检查全部沿用 v3；由测试钉住复用的函数就是冻结模块中的同一对象 |
  22 | | 4 | `hf_repo/scripts/contact_c2_launch_v4.py`、`run_contact_c2_v4_isolated.py` | v4 启动守卫：复用 P1 的通用部件（严格 JSON、哈希绑定、路径限定、回执），常量改为 v4 协议 SHA、单一 case 与 v4 后端。P1 文件本身不改 | 与 P1 相同：建目录、写日志或派发之前完成全部核对，子进程加载后端前再核一次；另外核对解释器版本与锁文件一致（补偿内核需要接受 `xla_cpu_ftz` 的 JAX，锁定的 0.11.0 满足） |
  23 | | 5 | `hf_repo/configs/contact_c2_v4.json` | 冻结的 v4 协议 | 见 §3 |
  24 | | 6 | `hf_repo/tests/test_contact_c2_v4.py` | #1 与冻结文件的差异只有一行；v4 协议的物理、审计、目标与 v3 逐项相等，逐字段改动都被拒绝；守卫在替身后端下的接受、拒绝与零副作用；审计复用函数的身份；小型合成模型上补偿求解器的路径行为 | 单元测试只用合成小模型（现有测试套件就是这样做的），不运行 C2 case |
  25 | 
  26 | **不纳入 v4 的内容：空支座补丁。** C2 的路径用 `displacement._check_support`，它本来就有 `len(fixed_dofs) < 3` 的短路判断；空支座补丁改的是 `tmc.py` 中力控制求解器的 `_check_support`，C2 路径根本不走那里。`tmc.py` 又在 v3 的 33 个绑定文件之中，改它会使 v3／P1 的冻结身份在工作树中失效。所以把它并入 v4 对 v4 没有作用，反而会破坏 v3 身份。这更正了我之前"随 v4 一并并入"的建议。建议等到新的力控制项目入口（例如 HF5 的任务入口）冻结自己的实现身份时再处理。
  27 | 
  28 | ## 3. v4 协议（冻结前草案）
  29 | 
  30 | | 字段 | 取值 |
  31 | | --- | --- |
  32 | | `schema` | `contact_c2_kernel_repair_v4` |
  33 | | `purpose` | 只把运行内核换成 `split_kernel_compensated`（`p26_q1_split_compensated_dot2_v1`），补测 v3 唯一失败的细网格均匀路径 |
  34 | | `geometry`、`material`、`solver`、`audit` | 与 v3（以及 C1 v1）逐项相同，由 v4 校验器逐项比对，不在 v4 中重写数值 |
  35 | | `uniform_targets_mm` | `[0, 0.125, 0.21875, 0.25, 0.28125, 0.375, 0.5]`（与 v3 相同） |
  36 | | `cases`、`run_sequence` | 只有 `mesh_h00625`（`h_mm` 0.0625、`padding_mm` 2.0、`outer_bottom_policy` driven）；序列 `["mesh_h00625"]` |
  37 | | `kernel` | 模块名、内核版本、编译选项（`xla_cpu_enable_fast_math=false`、`xla_cpu_ftz=false`）、操作数范围 |
  38 | | `saved_field_admission`、`baseline_audits` | 与 v3 相同的准入门与两份 C1 基线审计（哈希不变） |
  39 | | `stable_f_evidence` | 无求解验证汇总 `hf4_c2_stable_f_validation/summary_001.json` 的 SHA-256，作为换核的前置证据 |
  40 | | `environment` | 锁定版本：CPython 3.13.6、NumPy 2.4.6、SciPy 1.17.1、JAX／jaxlib 0.11.0 |
  41 | | `budget` | 1 条路径；求解子进程墙钟 700 s；审计每路径 1200 s；累计求解 700 s、累计审计 1200 s。求解与审计分开计 |
  42 | | `stopping` | 与 v3 相同：来源、代数、独立数值或几何、目标不完整任一失败即停；不自动重试，不搜索参数，不扩大资源；失败产物与接受记录全部保留 |
  43 | | `storage` | 运行目录在仓库根下新建的 `hf4_c2_v4_results/experiments/mesh_h00625_v4/`，与 `hf_repo` 和历史 C2 目录分开；按 S0 的做法，轻量记录进 Git，逐态大数组放在 Git 之外并附哈希清单 |
  44 | | `implementation_sha256` | 冻结时计算：C2 路径实际导入的全部模块（`contact_c2`、`split_affine_compensated`、`split_kernel_compensated`、`compensated_kinematics`、`split_state`、`split_prescribed`、`prescribed`、`displacement`、`tmc`、`tmc_kernel`，以及经 `split_prescribed` 间接载入、但不参与 v4 求值的旧 `split_kernel`），加上 v4 运行器、审计、守卫、`hf4_common.py`、两份独立参考脚本以及被复用的 `audit_contact_c2.py` |
  45 | 
  46 | ## 4. 有界复验：执行顺序、验收与停止
  47 | 
  48 | 执行顺序（需要授权）：
  49 | 1. 实现 #1–#6，在锁定环境运行全量测试。
  50 | 2. 冻结 v4 协议并单独提交（先于任何运行）。
  51 | 3. 用守卫做只读计划检查。
  52 | 4. 求解一次。
  53 | 5. 独立审计一次。
  54 | 6. 报告。
  55 | 
  56 | **验收**：沿用 v3，不放宽任何门。
  57 | - 7 个原目标全部到达。
  58 | - 每个存盘状态（包括插入态）都通过独立 80／120 位审计：内力求值 `1e-11`、切线作用 `1e-10`、分量 `1e-9`、80／120 一致 `1e-40`、残差 `1e-9`、约束 `1e-10`、力平衡 `1e-8`，以及几何与重叠容差。
  59 | - 通过记为"v4 补测通过"，v3 历史判定不变。
  60 | 
  61 | **停止**：
  62 | - 首个失效状态出现即停止并保存全部接受记录。
  63 | - 超时记为资源性不通过，保留有效前缀。
  64 | - 身份或来源不符则在运行前拒绝。
  65 | - 不重试，不改 γ、α、容差或门槛，不提高资源上限。
  66 | 
  67 | **成本估计**：
  68 | - 原求解 33.1 s；补偿内核每次组装约为旧内核的 5 倍（细网格上含切线时 20 ms → 102 ms），预计求解在 1–3 min，远低于 700 s。
  69 | - 审计的主要开销是独立 Decimal 参考，与内核无关，预计与原来的 200 s 相近。
  70 | - 合计约 5 min，本机串行，单进程。
  71 | 
  72 | **结果的含义**：
  73 | - 通过说明算术修复在这条完整路径上成立。
  74 | - 它不涉及网格收敛、其他网格或平台、接触物理或材料；也不自动改变任何默认入口。
  75 | - 是否再用 v4 补测 `padding_2p5` 与 `outer_free`（它们在 v3 中已通过）另行决定，不属于本方案。
  76 | 
  77 | ## 5. 需要审阅与决定
  78 | 
  79 | - **V1** 变更清单的做法：只新增文件；#1 是一行差异的副本；审计与守卫复用冻结部件；P1 与 v3 冻结文件不改；空支座补丁不进 v4。
  80 | - **V2** 是否在审阅通过后实施 #1–#6、跑测试并冻结 v4 协议。这一步不运行 FE。
  81 | - **V3** 新 FE 的明确授权：本机按 §4 求解并审计一条路径。
  82 | - **V4** 新运行的大数组是否沿用 S0 做法，放在 Git 之外并附哈希清单。
  83 | 
  84 | HF5 的 H1–H4 另行确认。其中 H1（LF v2 纯数据适配器）不依赖新 FE，可以与 v4 并行，但实施范围需要单独确认。
```

## hf_repo/src/hf_eval/split_affine.py
原字节 SHA-256：`6ca9ef3bfccdee3fd5a3d392a7673fe4273af0790d6a63bf8969277944104dda`

### 第 1–22 行

```text
   1 | """Explicit affine geometric lift stages with immutable split-state handoff.
   2 | 
   3 | The controller below retains the frozen split prescribed controller's Newton,
   4 | Armijo, general sparse-LU, bisection, rollback and time-budget policies. Only
   5 | stage initialization and lift construction are extended. Old code is untouched.
   6 | """
   7 | from __future__ import annotations
   8 | 
   9 | from copy import deepcopy
  10 | from time import perf_counter
  11 | from typing import Callable
  12 | 
  13 | import numpy as np
  14 | from .displacement import _check_support, _positive_scalar, _vector
  15 | from .prescribed import PrescribedSettings, _inputs, _linear_step
  16 | from .tmc import TMCModel, TMCError
  17 | from .tmc_kernel import KernelError
  18 | from .split_state import SplitDisplacement
  19 | from .split_kernel import assemble_split
  20 | from .split_prescribed import STATE_SCHEMA, state_hash
  21 | 
  22 | LIFT_SCHEME = "affine_geometric_origin_v1"
```

### 第 91–104 行

```text
  91 |              "all_assembly_attempts_wall": 0.0, "callback": 0.0,
  92 |              "first_kernel_including_compile": None, "kernel_calls": 0,
  93 |              "successful_kernel_calls": 0, "newton_base_checks": 0, "predictors": 0}
  94 | 
  95 |     def check_time():
  96 |         if perf_counter() - started > settings.time_limit_seconds:
  97 |             raise TMCError("prescribed path wall-time budget exceeded", code="time_limit")
  98 | 
  99 |     def prescribed_values(d):
 100 |         with np.errstate(over="ignore", invalid="ignore"):
 101 |             values = base[model.fixed_dofs] + d * direction[model.fixed_dofs]
 102 |         if not np.all(np.isfinite(values)):
 103 |             raise TMCError("prescribed displacement overflowed", code="nonfinite")
 104 |         return values
```

### 第 124–147 行

```text
 124 |             K, internal, values = assemble_split(model, u, tangent=tangent)
 125 |         finally:
 126 |             times["all_assembly_attempts_wall"] += perf_counter() - begin
 127 |         for key in ("kernel_and_transfer", "assembly"):
 128 |             times[key] += values["timing_seconds"][key]
 129 |         if times["first_kernel_including_compile"] is None:
 130 |             times["first_kernel_including_compile"] = values["timing_seconds"]["kernel_and_transfer"]
 131 |         times["successful_kernel_calls"] += 1
 132 |         if not np.all(np.isfinite(internal)):
 133 |             raise TMCError("internal force is nonfinite", code="nonfinite")
 134 |         if not np.all(np.isfinite(values["J"])) or np.any(values["J"] <= 0):
 135 |             raise TMCError("all determinants must be finite and positive", code="invalid_J")
 136 |         check_time()
 137 |         return K, internal, values
 138 | 
 139 |     def force_state(u, target, internal):
 140 |         free_norm = float(np.linalg.norm(internal[model.free]))
 141 |         fixed_norm = float(np.linalg.norm(internal[model.fixed_dofs]))
 142 |         dscale = max(abs(target), settings.displacement_scale_floor)
 143 |         floor = settings.force_scale_floor_factor * force_scale_per_length * dscale
 144 |         scale = max(free_norm, fixed_norm, floor)
 145 |         # Fixed fluctuation is zero by construction; no rounded display vector
 146 |         # enters this check. Independent HP compares to the ideal base+d*motion.
 147 |         error = float(np.max(np.abs((u.lift[model.fixed_dofs] - prescribed_values(target))
```

### 第 322–365 行

```text
 322 |     def advance(target, depth, original_target):
 323 |         nonlocal state_u, state_d, state_K, max_depth_used
 324 |         before_u, before_d, before_K = state_u.copy(), state_d, state_K
 325 |         max_depth_used = max(max_depth_used, depth)
 326 |         try:
 327 |             solved, solved_K, measured = newton(before_u, before_d, state_K, target)
 328 |         except (KernelError, TMCError) as error:
 329 |             assert (_bitwise_equal(state_u.lift, before_u.lift)
 330 |                     and _bitwise_equal(state_u.fluctuation, before_u.fluctuation)
 331 |                     and state_d == before_d and state_K is before_K)
 332 |             code = getattr(error, "code", "numerical_failure")
 333 |             failures.append({"from_displacement": before_d, "attempted_displacement": float(target),
 334 |                              "depth": depth, "code": code, "reason": str(error),
 335 |                              "details": deepcopy(getattr(error, "details", {})), "rollback_bitwise_equal": True})
 336 |             increment = target - before_d
 337 |             if (code in ("time_limit", "constraint_failure") or depth >= settings.max_bisections
 338 |                     or increment / 2 < settings.minimum_increment * (1 - 1e-12)):
 339 |                 raise
 340 |             midpoint = before_d + increment / 2
 341 |             advance(midpoint, depth + 1, original_target)
 342 |             advance(target, depth + 1, original_target)
 343 |             return
 344 |         state_u, state_d, state_K = solved.copy(), float(target), solved_K
 345 |         record = {**measured, "u_lift": solved.lift.copy(), "u_fluctuation": solved.fluctuation.copy(),
 346 |                   "u_display": solved.u_display, "state_representation": STATE_SCHEMA,
 347 |                   "state_sha256": state_hash(solved), "original_target_displacement": float(original_target),
 348 |                   "is_original_target": bool(target == original_target), "bisection_depth": depth,
 349 |                   "elapsed_seconds": perf_counter() - started}
 350 |         accepted.append(record)
 351 |         if on_accept is not None:
 352 |             begin = perf_counter()
 353 |             try:
 354 |                 on_accept(deepcopy(record))
 355 |             except OSError as error:
 356 |                 raise TMCError(str(error), code="persistence_failure",
 357 |                                details={"last_equilibrated_displacement": state_d}) from error
 358 |             finally:
 359 |                 times["callback"] += perf_counter() - begin
 360 |             check_time()
 361 | 
 362 |     try:
 363 |         _check_support(model)
 364 |         for target in levels:
 365 |             advance(float(target), 0, float(target))
```

## hf_repo/src/hf_eval/displacement.py
原字节 SHA-256：`fbae379e37f0816edcdebd765bcae73a525c8709c2cb8f798146e497c9a4a386`

### 第 94–102 行

```text
  94 | def _check_support(model):
  95 |     rigid = np.zeros((model.ndof, 3))
  96 |     rigid[0::2, 0], rigid[1::2, 1] = 1, 1
  97 |     center = model.coordinates.mean(axis=0)
  98 |     span = max(float(np.ptp(model.coordinates, axis=0).max()), 1.0)
  99 |     rigid[0::2, 2] = -(model.coordinates[:, 1] - center[1]) / span
 100 |     rigid[1::2, 2] = (model.coordinates[:, 0] - center[0]) / span
 101 |     if len(model.fixed_dofs) < 3 or np.linalg.matrix_rank(rigid[model.fixed_dofs]) < 3:
 102 |         raise TMCError("support does not eliminate three planar rigid modes", code="insufficient_support")
```

## hf_repo/src/hf_eval/tmc.py
原字节 SHA-256：`b2a1d4d449886667821e805cddeaf7bab3073d2d7a6cc1baeddfed05f407f025`

### 第 167–176 行

```text
 167 | def _check_support(model):
 168 |     rigid = np.zeros((model.ndof, 3))
 169 |     rigid[0::2, 0] = 1
 170 |     rigid[1::2, 1] = 1
 171 |     span = max(np.ptp(model.coordinates, axis=0).max(), 1.0)
 172 |     center = model.coordinates.mean(axis=0)
 173 |     rigid[0::2, 2] = -(model.coordinates[:, 1] - center[1]) / span
 174 |     rigid[1::2, 2] = (model.coordinates[:, 0] - center[0]) / span
 175 |     if np.linalg.matrix_rank(rigid[model.fixed_dofs]) < 3:
 176 |         raise TMCError("support does not eliminate three planar rigid modes", code="insufficient_support")
```

## hf_repo/scripts/run_contact_c2.py
原字节 SHA-256：`d6adb2918e5b7b1e763dc9bb5d11c644ba6d195e361b5f42783cebcea21b9555`

### 第 15–21 行

```text
  15 | from hf_eval.contact_c2 import build_problem, CASES
  16 | from hf_eval.prescribed import PrescribedSettings
  17 | from hf_eval.split_affine import solve_split_affine_path
  18 | from hf_eval.split_state import SplitDisplacement
  19 | from hf_eval import split_kernel
  20 | from run_contact_c1_r2 import component_actions
  21 | from hf4_common import read_json, write_json, write_npz, sha, timestamp, plain
```

### 第 64–91 行

```text
  64 |     vector = np.sin(np.arange(model.ndof, dtype=float)+.37)
  65 |     vector[model.fixed_dofs] = 0.
  66 |     vector /= np.linalg.norm(vector)
  67 |     def accepted(record):
  68 |         state = SplitDisplacement(record["u_lift"], record["u_fluctuation"])
  69 |         matrix, force, fields = split_kernel.assemble_split(model, state, tangent=True)
  70 |         actions = component_actions(model, state, vector)
  71 |         components = {key:np.bincount(model.edofs.ravel(), weights=fields[key].ravel(), minlength=model.ndof)
  72 |                       for key in ("material_residual", "regularization_residual")}
  73 |         filename = f"state_{len(entries):03d}.npz"
  74 |         write_npz(stage/"steps"/filename, u_lift=state.lift, u_fluctuation=state.fluctuation,
  75 |                   internal_force=force, material_internal_force=components["material_residual"],
  76 |                   regularization_internal_force=components["regularization_residual"], J=fields["J"],
  77 |                   tangent_direction=vector, production_tangent_action=matrix@vector,
  78 |                   material_tangent_action=actions["material_residual"],
  79 |                   regularization_tangent_action=actions["regularization_residual"])
  80 |         record_file = f"state_{len(entries):03d}.record.json.gz"
  81 |         with gzip.open(stage/"steps"/record_file, "wt", encoding="utf-8") as stream:
  82 |             json.dump(plain(record), stream, allow_nan=False, separators=(",", ":"))
  83 |         entry = {k:record[k] for k in ("d","is_original_target","original_target_displacement","bisection_depth")}
  84 |         entry.update(index=len(entries),file=filename,sha256=sha(stage/"steps"/filename),
  85 |                      record_file=record_file,record_sha256=sha(stage/"steps"/record_file))
  86 |         entries.append(entry)
  87 |         write_json(stage/"steps/index.json",dict(steps=entries))
  88 |         print(json.dumps(dict(case=case_id,accepted=len(entries),d=record["d"],residual=record["relative_residual"])),flush=True)
  89 |     result = solve_split_affine_path(model,arrays["base"],arrays["direction"],arrays["lift_origin"],
  90 |         arrays["lift_shape"],problem.targets,initial_state=problem.initial_state,reaction_groups=problem.groups,
  91 |         settings=PrescribedSettings(**protocol["solver"]),force_scale_per_length=100.,on_accept=accepted)
```

## hf_repo/scripts/contact_c2_launch_p1.py
原字节 SHA-256：`4109cf054cdec42285a988e1adec161a74c5143374eba9300c3d44b60c5f9958`

### 第 25–32 行

```text
  25 | REPO = Path(__file__).resolve().parents[1]
  26 | PROTOCOL_SHA256 = "b17c8328dd1e350563b70305c0b311c8d38c9c0ef68c08b85fac5f13604d0b4d"
  27 | C1_PROTOCOL_SHA256 = "5b30bafc226cb97038ae1b0d08e745f9f7df2a049333a8019cdf03cc48fe5308"
  28 | PLAN_SCHEMA = "contact_c2_launch_plan_p1_v1"
  29 | RECEIPT_SCHEMA = "contact_c2_external_receipt_p1_v1"
  30 | P1_FILES = ("scripts/contact_c2_launch_p1.py", "scripts/run_contact_c2_p1.py",
  31 |             "scripts/run_contact_c2_p1_isolated.py")
  32 | SEQUENCE = ["padding_2p5", "outer_free", "mesh_h00625"]
```

### 第 152–169 行

```text
 152 | def validate_protocol(protocol_path, bindings):
 153 |     """Pin all bytes before trusting any source path, numerical value or budget."""
 154 |     protocol_path = Path(protocol_path).resolve()
 155 |     require(protocol_path.is_relative_to(REPO), "protocol must reside in this repository")
 156 |     protocol = bindings.json(protocol_path, PROTOCOL_SHA256)
 157 |     require(type(protocol) is dict, "protocol must be an object")
 158 |     # The independently pinned reference authenticates all keys/types, including
 159 |     # explanatory semantics and source manifests, without a self-declared SHA.
 160 |     reference_path = REPO / "configs/contact_c2_v3.json"
 161 |     reference = bindings.json(reference_path, PROTOCOL_SHA256)
 162 |     exact(protocol, reference, "protocol")
 163 |     c1 = bindings.json(REPO / "configs/contact_c1_v1.json", C1_PROTOCOL_SHA256)
 164 |     for section in ("geometry", "material", "solver"):
 165 |         exact(protocol[section], c1[section], section)
 166 |     exact(protocol["schema"], "contact_c2_uniform_diagnostic_v1", "schema")
 167 |     exact(protocol["run_sequence"], SEQUENCE, "run_sequence")
 168 |     exact(protocol["audit"]["precisions"], [80, 120], "audit.precisions")
 169 |     # Hash identity already protects every field. Explicit domain checks make
```

### 第 179–201 行

```text
 179 |     require(type(protocol["budget"]["maximum_paths"]) is int
 180 |             and protocol["budget"]["maximum_paths"] == len(SEQUENCE), "path cap differs")
 181 |     bindings.manifest(REPO, protocol["implementation_sha256"], "implementation manifest")
 182 |     workspace = REPO.parent
 183 |     gate_spec = protocol["saved_field_admission"]
 184 |     gate_path = confined(protocol_path.parent, gate_spec["path"], limit=workspace, parents=True)
 185 |     gate = bindings.json(gate_path, gate_spec["sha256"])
 186 |     require(type(gate) is dict and gate.get("schema") == "contact_c2_saved_field_admission_v1"
 187 |             and gate.get("status") == "pass"
 188 |             and gate.get("valid_for_execution_admission", True) is True,
 189 |             "saved-field execution admission is absent")
 190 |     bindings.manifest(workspace, gate.get("input_sha256_from_workspace_root"),
 191 |                       "saved-field admission input manifest")
 192 |     require(type(protocol["baseline_audits"]) is list and len(protocol["baseline_audits"]) == 2,
 193 |             "two baseline audits are required")
 194 |     for item in protocol["baseline_audits"]:
 195 |         baseline = bindings.json(confined(protocol_path.parent, item["path"],
 196 |                                          limit=workspace, parents=True), item["sha256"])
 197 |         require(type(baseline) is dict and baseline.get("schema_version") == "contact-c1-independent-audit-1.0"
 198 |                 and baseline.get("status") == "pass", "baseline audit did not pass")
 199 |     for name in P1_FILES:
 200 |         bindings.file(confined(REPO, name))
 201 |     return protocol
```

### 第 271–292 行

```text
 271 | def plan_launch(action, run, case_id, protocol_path, *, _worker=False):
 272 |     """Read-only launch planning. No mkdir, imports of mechanics, or dispatch."""
 273 |     require(action in ("solve", "audit"), "unsupported action")
 274 |     require(case_id in SEQUENCE, "undeclared case; baseline is preflight only")
 275 |     run, protocol_path = Path(run).resolve(), Path(protocol_path).resolve()
 276 |     root = run.parent
 277 |     require(root.is_relative_to(REPO.parent) and not root.is_relative_to(REPO),
 278 |             "experiment root must be in the workspace and outside hf_repo")
 279 |     _run_name(run.name)
 280 |     bindings = Bindings()
 281 |     protocol = validate_protocol(protocol_path, bindings)
 282 |     log = root / (run.name + "." + action + ".log")
 283 |     receipt = root / (run.name + "." + action + ".receipt.json")
 284 |     launch_file = root / (run.name + "." + action + ".p1-plan.json")
 285 |     require(not receipt.exists(), "refusing to overwrite a subprocess receipt")
 286 |     if _worker:
 287 |         require(log.is_file() and launch_file.is_file(), "private worker requires its parent's artifacts")
 288 |     else:
 289 |         require(not log.exists() and not launch_file.exists(), "refusing to overwrite launch evidence")
 290 |     require(not root.exists() or root.is_dir(), "experiment root is not a directory")
 291 |     static_bindings = dict(bindings.values)
 292 |     solves = [_receipt(p, "solve", protocol, bindings, static_bindings)
```

### 第 323–353 行

```text
 323 |     solve_elapsed = sum(row["elapsed_seconds"] for row in solves)
 324 |     audit_elapsed = sum(row["elapsed_seconds"] for row in audits)
 325 |     budget = protocol["budget"]
 326 |     if action == "solve":
 327 |         require(solve_elapsed < budget["maximum_total_solve_seconds"], "cumulative solve budget exhausted")
 328 |         require(audit_elapsed < budget["maximum_total_audit_seconds"], "cumulative audit budget exhausted")
 329 |         require(not run.exists() and len(solves) < budget["maximum_paths"], "new path required within path cap")
 330 |         require(case_id == SEQUENCE[len(solves)], "case differs from frozen serial order")
 331 |         require(set(audit_by_name) == set(by_name), "every prior solve requires a successful audit")
 332 |         for row in solves:
 333 |             _admitted_run(root, row, audit_by_name[row["run_name"]], protocol, bindings)
 334 |         timeout = min(budget["subprocess_wall_seconds"], budget["maximum_total_solve_seconds"] - solve_elapsed)
 335 |     else:
 336 |         require(audit_elapsed < budget["maximum_total_audit_seconds"], "cumulative audit budget exhausted")
 337 |         require(solves and case_id == SEQUENCE[len(solves) - 1]
 338 |                 and case_id in by_case and by_case[case_id]["run_name"] == run.name,
 339 |                 "audit must follow the latest successful solve")
 340 |         require(run.name not in audit_by_name, "automatic audit retry is forbidden")
 341 |         require(set(audit_by_name) == set(by_name) - {run.name}, "earlier solve lacks an admitted audit")
 342 |         for row in solves:
 343 |             if row["run_name"] != run.name:
 344 |                 _admitted_run(root, row, audit_by_name[row["run_name"]], protocol, bindings)
 345 |         _run_metadata(run, case_id, protocol, bindings)
 346 |         require(not (run / "audit.json").exists(), "refusing to overwrite an existing audit")
 347 |         timeout = min(budget["maximum_audit_seconds_per_path"], budget["maximum_total_audit_seconds"] - audit_elapsed)
 348 |     _number(timeout, "remaining timeout", positive=True)
 349 |     return dict(schema=PLAN_SCHEMA, scope="historical v3 contract validation; not a new scientific admission",
 350 |                 action=action, case_id=case_id, run=run.relative_to(REPO.parent).as_posix(),
 351 |                 protocol_path=protocol_path.relative_to(REPO.parent).as_posix(),
 352 |                 protocol_sha256=PROTOCOL_SHA256, timeout_seconds=timeout,
 353 |                 input_sha256=dict(sorted(bindings.values.items())))
```

### 第 394–408 行

```text
 394 | def worker(launch_file, expected_sha):
 395 |     """Internal child handshake; not a supported standalone execution API."""
 396 |     launch_file = Path(launch_file).resolve()
 397 |     _digest(expected_sha, "parent plan digest")
 398 |     require(sha(launch_file) == expected_sha, "parent launch plan changed")
 399 |     saved = strict_json(launch_file)
 400 |     require(type(saved) is dict and saved.get("schema") == PLAN_SCHEMA, "invalid parent plan")
 401 |     run = confined(REPO.parent, saved["run"])
 402 |     require(launch_file == run.parent / (run.name + "." + saved["action"] + ".p1-plan.json"),
 403 |             "private launch plan is in the wrong location")
 404 |     repeated = plan_launch(saved["action"], run, saved["case_id"],
 405 |                            confined(REPO.parent, saved["protocol_path"]), _worker=True)
 406 |     exact(repeated, saved, "revalidated parent plan")
 407 |     require(sha(launch_file) == expected_sha, "parent launch plan changed during validation")
 408 |     return _invoke_backend(repeated)
```

### 第 436–444 行

```text
 436 |     payload = dict(schema=RECEIPT_SCHEMA, action=action, case_id=case_id, run_name=run.name,
 437 |                    command=command, started_utc=started, finished_utc=_timestamp(),
 438 |                    elapsed_seconds=time.perf_counter() - start, timeout_seconds=plan["timeout_seconds"],
 439 |                    returncode=code, timed_out=timed_out, protocol_sha256=PROTOCOL_SHA256,
 440 |                    log_sha256=sha(log), launch_plan_sha256=plan_digest, launch_failure=failure)
 441 |     if action == "audit" and (run / "audit.json").is_file():
 442 |         payload["audit_sha256"] = sha(run / "audit.json")
 443 |     _write_new(receipt, payload)
 444 |     return 124 if timed_out else (125 if failure else code)
```

## hf_repo/scripts/audit_contact_c2.py
原字节 SHA-256：`50bcbe18d67d62ea1bce621c9bfd2c1c6247dbe2b095a965dab42c00bc47e543`

### 第 18–37 行

```text
  18 | from audit_contact_c1 import (
  19 |     D, THRESHOLDS, add_check, analytic_uniform_force, bitwise_equal, classify_prefix,
  20 |     component_error, evaluate_split_prescribed_state, exact_geometry, finite64,
  21 |     norm, physical_drive, plain, portable_bindings, read_json, read_npz, sha,
  22 |     state_identity, validate_inventory,
  23 | )
  24 | 
  25 | REPO = Path(__file__).resolve().parents[1]
  26 | C1_AUDITOR_SHA256 = "715c748111e255bd4d1a945e80eca4a778f54ce2fa8ac2601e761160cd14c1ce"
  27 | TARGETS = [0., .125, .21875, .25, .28125, .375, .5]
  28 | CASES = {"mesh_h00625": (.0625, 2., "driven"),
  29 |          "padding_2p5": (.125, 2.5, "driven"),
  30 |          "outer_free": (.125, 2., "free")}
  31 | MEASUREMENT_SEMANTICS = {
  32 |     "top_weak_normal_reactions": "Minus prescribed-top weak nodal internal residual, in N; not a verified unilateral contact multiplier or pressure.",
  33 |     "minimum_weak_normal_reaction": "Minimum of top_weak_normal_reactions, retaining its signed value.",
  34 |     "compatibility_aliases": {"top_normal_multipliers": "top_weak_normal_reactions",
  35 |                               "minimum_normal_multiplier": "minimum_weak_normal_reaction"},
  36 |     "normal_force": "Sum of signed prescribed-top weak reactions, including material and regularization contributions; not a direct material-edge traction integral.",
  37 | }
```

### 第 78–91 行

```text
  78 | def validate_protocol(protocol):
  79 |     require(protocol.get("schema") == "contact_c2_uniform_diagnostic_v1", "unsupported C2 protocol")
  80 |     require(protocol["audit"].get("precisions") == [80, 120], "C2 requires 80/120 arithmetic")
  81 |     for key, value in THRESHOLDS.items():
  82 |         require(Decimal(str(protocol["audit"].get(key))) == Decimal(value), "audit threshold changed: " + key)
  83 |     old = read_json(REPO/"configs/contact_c1_v1.json")
  84 |     require(protocol["geometry"] == old["geometry"], "common physical geometry changed")
  85 |     require(protocol["material"] == old["material"], "material/Lref/regularization contract changed")
  86 |     require(protocol["solver"] == old["solver"], "solver acceptance or control contract changed")
  87 |     require(protocol["uniform_targets_mm"] == TARGETS, "uniform targets changed")
  88 |     require(set(protocol["cases"]) == set(CASES), "C2 must declare exactly the three new cases")
  89 |     for name, (h, padding, policy) in CASES.items():
  90 |         require(protocol["cases"][name] == dict(h_mm=h, padding_mm=padding, outer_bottom_policy=policy),
  91 |                 "undeclared one-factor case: " + name)
```

### 第 214–259 行

```text
 214 |         model, arrays["u_lift"], arrays["u_fluctuation"], s, model["base"], model["direction"],
 215 |         groups, metadata["force_scale_per_length"], precision=precision,
 216 |         tangent_direction=v, fluctuation_offset=0.0) for precision in pair}
 217 |     with localcontext() as context:
 218 |         context.prec = max(pair)
 219 |         high, other, checks = hp[80], hp[50 if pair == (50, 80) else 120], []
 220 |         sf = high["force_scale_decimal"]
 221 |         force_floor = Decimal(THRESHOLDS["component_force_floor_relative_to_SF"])*sf
 222 |         tangent_floor = Decimal(THRESHOLDS["component_tangent_floor_N_per_mm"])
 223 |         add_check(checks, "production_relative_residual", D(production["relative_residual"]), THRESHOLDS["relative_residual"])
 224 |         add_check(checks, "production_minimum_J_all_cells", D(np.min(arrays["J"])), 0, ">")
 225 |         for precision in pair:
 226 |             for name in ("relative_residual", "relative_constraint", "relative_force_balance"):
 227 |                 add_check(checks, f"hp{precision}_"+name, hp[precision][name+"_decimal"], THRESHOLDS[name])
 228 |             add_check(checks, f"hp{precision}_minimum_J_all_cells", hp[precision]["minimum_J_decimal"], 0, ">")
 229 |         constraint = max(abs(D(arrays["u_lift"][i])+D(arrays["u_fluctuation"][i])
 230 |                              -D(model["base"][i])-D(s)*D(model["direction"][i])) for i in fixed)
 231 |         add_check(checks, "saved_split_relative_constraint", constraint/max(abs(D(s)), Decimal("1e-6")),
 232 |                   THRESHOLDS["relative_constraint"])
 233 |         component_comparisons = {}
 234 |         comparisons = (
 235 |             ("total_force", "internal_force", "internal_decimal", sf, THRESHOLDS["relative_force_evaluation"]),
 236 |             ("total_tangent", "production_tangent_action", "tangent_action_decimal",
 237 |              max(norm(high["tangent_action_decimal"]), tangent_floor), THRESHOLDS["relative_tangent_action"]),
 238 |             ("material_force", "material_internal_force", "material_internal_decimal", force_floor,
 239 |              THRESHOLDS["relative_component_evaluation"]),
 240 |             ("regularization_force", "regularization_internal_force", "regularization_internal_decimal", force_floor,
 241 |              THRESHOLDS["relative_component_evaluation"]),
 242 |             ("material_tangent", "material_tangent_action", "material_tangent_action_decimal", tangent_floor,
 243 |              THRESHOLDS["relative_component_evaluation"]),
 244 |             ("regularization_tangent", "regularization_tangent_action", "regularization_tangent_action_decimal", tangent_floor,
 245 |              THRESHOLDS["relative_component_evaluation"]),
 246 |         )
 247 |         for name, archive_key, hp_key, minimum, threshold in comparisons:
 248 |             comparison = component_error(arrays[archive_key], high[hp_key], minimum)
 249 |             # Total force retains exactly the old SF normalization; component
 250 |             # terms use max(component norm, declared dimensional floor).
 251 |             if name == "total_force":
 252 |                 comparison["denominator"] = sf
 253 |                 comparison["relative_error"] = comparison["absolute_error"]/sf
 254 |             cross_error = norm([a-b for a, b in zip(other[hp_key], high[hp_key])])
 255 |             cross = cross_error/comparison["denominator"]
 256 |             comparison.update(cross_precision_absolute_error=cross_error, cross_precision_relative_error=cross)
 257 |             component_comparisons[name] = comparison
 258 |             add_check(checks, "production_vs_hp80_"+name, comparison["relative_error"], threshold)
 259 |             add_check(checks, f"hp{pair[0]}_vs_hp{pair[1]}_"+name, cross, THRESHOLDS["relative_precision_agreement"])
```

### 第 427–464 行

```text
 427 | def load_run(run, protocol_path, bindings):
 428 |     protocol_path = Path(protocol_path).resolve()
 429 |     require(protocol_path.is_relative_to(REPO), "protocol must reside in the portable repository tree")
 430 |     protocol = read_json(protocol_path)
 431 |     validate_protocol(protocol)
 432 |     bind(protocol_path, bindings)
 433 |     bind(REPO/"configs/contact_c1_v1.json", bindings)
 434 |     if "implementation_sha256" in protocol:
 435 |         bind_manifest(REPO, protocol["implementation_sha256"], bindings, "frozen implementation manifest")
 436 |     gate_spec = protocol["saved_field_admission"]
 437 |     require(isinstance(gate_spec["path"], str) and "\\" not in gate_spec["path"]
 438 |             and ":" not in gate_spec["path"] and not PurePosixPath(gate_spec["path"]).is_absolute(),
 439 |             "admission path must be protocol-relative POSIX")
 440 |     gate = (protocol_path.parent/gate_spec["path"]).resolve()
 441 |     require(gate.is_relative_to(REPO.parent), "admission escapes repository/results tree")
 442 |     bind(gate, bindings, gate_spec["sha256"])
 443 |     admission = read_json(gate)
 444 |     require(admission.get("status") == "pass", "saved-field admission did not pass")
 445 |     if "input_sha256_from_workspace_root" in admission:
 446 |         bind_manifest(REPO.parent, admission["input_sha256_from_workspace_root"], bindings,
 447 |                       "saved-field admission input manifest")
 448 |     meta = read_json(run/"metadata.json")
 449 |     bind(run/"metadata.json", bindings)
 450 |     require(meta.get("schema") == "contact_c2_run_v1" and meta.get("kind") == "TMC"
 451 |             and meta.get("mode") == "uniform" and meta.get("case_id") in CASES
 452 |             and meta.get("protocol") == protocol and meta.get("protocol_sha256") == sha(protocol_path),
 453 |             "run metadata is not bound to frozen C2 protocol")
 454 |     sources = meta.get("source_sha256")
 455 |     required = {"src/hf_eval/contact_c2.py", "src/hf_eval/split_affine.py", "src/hf_eval/split_kernel.py",
 456 |                 "src/hf_eval/split_state.py", "scripts/run_contact_c2.py", "scripts/run_contact_c1_r2.py",
 457 |                 "scripts/hf4_common.py"}
 458 |     require(isinstance(sources, dict) and required <= set(sources), "production source manifest is incomplete")
 459 |     for name, expected in sources.items():
 460 |         bind(confined(REPO, name), bindings, expected)
 461 |     require(sha(REPO/"scripts/audit_contact_c1.py") == C1_AUDITOR_SHA256, "frozen C1 audit prototype changed")
 462 |     for name in ("audit_contact_c2.py", "audit_contact_c1.py", "audit_contact_reference_a0.py",
 463 |                  "hf4_split_precision_reference.py", "hf2_precision_reference.py"):
 464 |         bind(REPO/"scripts"/name, bindings)
```

### 第 475–484 行

```text
 475 |         for name in ("result.json", "stages/index.json", "exception.json"):
 476 |             if (run/name).exists():
 477 |                 bind(run/name, bindings)
 478 |     stage = run/"stages/uniform_tmc"
 479 |     require(stage.is_dir() and {p.name for p in (run/"stages").iterdir() if p.is_dir()} == {"uniform_tmc"},
 480 |             "missing or unindexed stage directory")
 481 |     require((stage/"completion.json").exists(),
 482 |             "interrupted stage lacks full-controller/completion inventory; standalone NPZ/record data remain readable but prefix certification is outside this audit scope")
 483 |     completion, compact = bind_completion(stage, "steps/index.json", bindings)
 484 |     if complete:
```

### 第 508–549 行

```text
 508 | def audit(run, output, protocol_path):
 509 |     run, output = Path(run).resolve(), Path(output).resolve()
 510 |     require(not output.exists(), "audit output already exists")
 511 |     # Re-audits select a new output stem and hence an independent detail tree.
 512 |     detail_directory = run/("audit_states" if output.name == "audit.json" else output.stem+"_states")
 513 |     require(not detail_directory.exists(), "audit detail directory already exists")
 514 |     bindings, detail_bindings, compact_states, stages = {}, {}, [], []
 515 |     data = load_run(run, protocol_path, bindings)
 516 |     detail_directory.mkdir()
 517 |     valid_prefix, passed_checks, total_checks = True, 0, 0
 518 |     for entry, record, path in zip(data["entries"], data["full"]["accepted_steps"], data["paths"]):
 519 |         print(f"Auditing uniform_tmc:{entry['index']} d={entry['d']} at 80/120 digits", flush=True)
 520 |         try:
 521 |             row = audit_state(data["model"], read_npz(path), entry, record, data["stage_metadata"],
 522 |                               data["groups"], data["protocol"], (80, 120))
 523 |         except (ValueError, KeyError, IndexError, ArithmeticError) as error:
 524 |             row = dict(state_id=f"uniform_tmc:{entry['index']}", phase_id="uniform_tmc", index=entry["index"],
 525 |                        parameter_s=entry["d"], status="not_pass", normal_force_raw=None,
 526 |                        error_type=type(error).__name__, error=str(error), checks=[])
 527 |         row["kind"] = "TMC"
 528 |         valid_prefix &= row["status"] == "pass"
 529 |         row["valid_prefix_comparable"] = valid_prefix
 530 |         total_checks += len(row["checks"])
 531 |         passed_checks += sum(check["status"] == "pass" for check in row["checks"])
 532 |         detail = detail_directory/f"state_{entry['index']:03d}.json"
 533 |         write_new(detail, row)
 534 |         relative = detail.relative_to(run).as_posix()
 535 |         digest = sha(detail)
 536 |         detail_bindings[relative] = digest
 537 |         keys = ("state_id", "phase_id", "kind", "index", "parameter_s", "status", "physical_mean_drive",
 538 |                 "normal_force_raw", "is_original_target", "original_target_parameter", "bisection_depth",
 539 |                 "valid_prefix_comparable")
 540 |         compact_states.append({**{key: row[key] for key in keys if key in row},
 541 |                                "detail_file": relative, "detail_sha256": digest,
 542 |                                "checks_count": len(row["checks"]),
 543 |                                "passed_checks": sum(check["status"] == "pass" for check in row["checks"])})
 544 |         del row
 545 |     prefix = classify_prefix(compact_states)
 546 |     stage_passed = data["inventory"]["status"] == "pass" and all(row["status"] == "pass" for row in compact_states)
 547 |     stages.append(dict(phase_id="uniform_tmc", status="pass" if stage_passed else "not_pass",
 548 |                        inventory=data["inventory"], initialization=dict(type="geometric_zero", split_arrays_verified=True),
 549 |                        state_ids=[row["state_id"] for row in compact_states]))
```

## hf_repo/scripts/validate_contact_c2_stable_f.py
原字节 SHA-256：`3be1be7277c663d01f23f6a4602bec28dc5a85c8e53e65aeaa34f995fd03277d`

### 第 249–274 行

```text
 249 | def jvp_function(jax, jnp, kernel, compiler_options=None):
 250 |     def actions(L, w, grad, hess, weights, lam, mu, kr, direction):
 251 |         def residual(varied):
 252 |             fields = jax.vmap(kernel._without_tangent,
 253 |                               in_axes=(0, 0, None, None, None, 0, 0, None))(
 254 |                 L, varied, grad, hess, weights, lam, mu, kr)
 255 |             return tuple(fields[k] for k in ("residual", "material_residual", "regularization_residual"))
 256 |         return jax.jvp(residual, (w,), (direction,))[1]
 257 |     options = kernel.COMPILER_OPTIONS if compiler_options is None else compiler_options
 258 |     return jax.jit(actions, compiler_options=options) if options else jax.jit(actions)
 259 | 
 260 | 
 261 | def evaluate_production(np, kernel, SplitDisplacement, model, L, w, v, action_function):
 262 |     K, force, fields = kernel.assemble_split(model, SplitDisplacement(L, w), tangent=True)
 263 |     _, force_only, only_fields = kernel.assemble_split(model, SplitDisplacement(L, w), tangent=False)
 264 |     actions = action_function(L[model.edofs], w[model.edofs], model.ops["grad"],
 265 |                               model.ops["hessian"], model.ops["weights"], model.lam, model.mu,
 266 |                               model.kr, v[model.edofs])
 267 |     assemble = lambda a: np.bincount(model.edofs.ravel(), weights=np.asarray(a).ravel(), minlength=model.ndof)
 268 |     out = dict(total_force=force, total_force_only=force_only,
 269 |                material_force=assemble(fields["material_residual"]),
 270 |                regularization_force=assemble(fields["regularization_residual"]),
 271 |                material_force_only=assemble(only_fields["material_residual"]),
 272 |                regularization_force_only=assemble(only_fields["regularization_residual"]),
 273 |                total_tangent=K@v, residual_jvp=assemble(actions[0]),
 274 |                material_tangent=assemble(actions[1]), regularization_tangent=assemble(actions[2]),
```

## hf_repo/src/hf_eval/split_kernel_compensated.py
原字节 SHA-256：`480129222206f9a16ef986829c1524582879f33f2dd2afd858f102c0bb3e707c`

### 第 19–27 行

```text
  19 | from .split_state import SplitDisplacement
  20 | from .tmc import TMCError, TMCModel
  21 | from .tmc_kernel import KernelError, _array, _coefficient, _ops, _runtime
  22 | from .compensated_kinematics import (
  23 |     COMPILER_OPTIONS, OPERAND_MIN, OPERAND_MAX, affine_gradient, operand_domain,
  24 | )
  25 | 
  26 | 
  27 | KERNEL_VERSION = "p26_q1_split_compensated_dot2_v1"
```

### 第 169–172 行

```text
 169 | _batch_with_tangent = jax.jit(lambda *args: _guarded_batch(*args, tangent=True),
 170 |                             compiler_options=COMPILER_OPTIONS)
 171 | _batch_without_tangent = jax.jit(lambda *args: _guarded_batch(*args, tangent=False),
 172 |                                compiler_options=COMPILER_OPTIONS)
```

## hf_repo/tests/test_split_affine.py
原字节 SHA-256：`2ca9e293d28b71ee7693dd33f55172b4e3f1fa1ed642befaa2679f09715bcb54`

### 第 1–15 行

```text
   1 | """Independent spring laws exercise affine split stages without an FE solve."""
   2 | from math import fsum
   3 | 
   4 | import numpy as np
   5 | import pytest
   6 | from scipy import sparse
   7 | 
   8 | from hf_eval import split_affine as control
   9 | from hf_eval.prescribed import PrescribedSettings
  10 | from hf_eval.split_state import SplitDisplacement
  11 | from hf_eval.tmc import rectangular_model, TMCError
  12 | from hf_eval.tmc_kernel import KernelError
  13 | 
  14 | 
  15 | def problem(monkeypatch, *, cubic=0., invalid_above=None, nonsymmetric=False):
```

### 第 34–63 行

```text
  34 |     counts = np.bincount(model.edofs.ravel(), minlength=model.ndof)
  35 |     calls = []
  36 | 
  37 |     def assembled(actual_model, state, tangent=True):
  38 |         assert actual_model is model
  39 |         calls.append((state.copy(), tangent))
  40 |         if invalid_above is not None and state.lift[1] > invalid_above:
  41 |             raise KernelError("independent injected inadmissible state", code="invalid_J")
  42 |         # The manufactured force is defined from both stored components, with
  43 |         # an analytic spring tangent. The production FE kernel is never called.
  44 |         force = matrix@state.lift + matrix@state.fluctuation
  45 |         stiffness = matrix.copy()
  46 |         for a, b, _ in edges:
  47 |             v = np.zeros(12)
  48 |             v[a], v[b] = 1., -1.
  49 |             stretch = fsum((state.lift[a], state.fluctuation[a], -state.lift[b], -state.fluctuation[b]))
  50 |             force += cubic*stretch**3*v
  51 |             stiffness += 3*cubic*stretch**2*np.outer(v, v)
  52 |         local = force[model.edofs]/counts[model.edofs]
  53 |         fields = dict(residual=local, material_residual=local,
  54 |                       regularization_residual=np.zeros_like(local),
  55 |                       J=np.ones((model.ne, 9)), material_energy=np.zeros(model.ne),
  56 |                       timing_seconds=dict(kernel_and_transfer=0., assembly=0.))
  57 |         return sparse.csc_matrix(stiffness) if tangent else None, force, fields
  58 | 
  59 |     monkeypatch.setattr(control, "assemble_split", assembled)
  60 |     return dict(model=model, direction=motion, shape=shape,
  61 |                 groups={"bottom": motion.copy(), "top": top}, calls=calls)
  62 | 
  63 | 
```

## hf_repo/scripts/audit_contact_c2_readback.py
原字节 SHA-256：`32343b17ea164e32909f1313a0bc4d2d9011b6dc4c4fd6e1120d4a6d4aea2225`

### 第 1–6 行

```text
   1 | """Numerical-only C2 readback with explicit external historical provenance.
   2 | 
   3 | This new entry point preserves the frozen numerical evaluator, tolerances and
   4 | prefix logic. It is never an execution-admission audit. Only the two exact
   5 | historical MATLAB source identities below may be absent from the admission
   6 | manifest; present files and every other input must still verify.
```

### 第 30–48 行

```text
  30 | }
  31 | # Verify the frozen code before importing it, then bind it again during load.
  32 | if hashlib.sha256((REPO/"scripts/audit_contact_c2.py").read_bytes()).hexdigest() != FROZEN_AUDITOR_SHA256:
  33 |     raise ValueError("frozen C2 auditor changed")
  34 | from audit_contact_c2 import (
  35 |     CASES, C1_AUDITOR_SHA256, MEASUREMENT_SEMANTICS, THRESHOLDS,
  36 |     audit_state, bind, bind_completion, bind_manifest, classify_prefix,
  37 |     confined, load_controller, portable_bindings, read_json, read_npz,
  38 |     require, sha, validate_model, validate_protocol, write_new,
  39 | )
  40 | 
  41 | 
  42 | def bind_historical_admission(root, manifest, bindings):
  43 |     """No exception applies to implementation, production, model or state files."""
  44 |     require(isinstance(manifest, dict) and len(manifest) == 166,
  45 |             "frozen admission must contain exactly 166 source identities")
  46 |     for name, expected in EXTERNAL_HISTORICAL_SOURCES.items():
  47 |         require(manifest.get(name) == expected, "external historical identity changed: " + name)
  48 |     records = []
```
