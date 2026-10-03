# Independent HF evaluator — HF-1 through HF-4-A/B

2026-10-03当前：**两例普通粗机构原0.025mm TEST均已完成NumPy完整力、非对称CSC切线与split平均驱动平衡**。本轮夹爪四态[0,.005,.010,.025]mm／8新HP80/120全模型参考通过，输入反力.00521459203N，自由钳口+y输出.02860371846mm；生产176.48秒、14force/9tangent/1solver，无二分或失败。见[目标、实现、成本、物理效果与接续](../docs/NUMPY_FORCE_PROGRESS_20261002.md#native-gripper-task025-20261003)、[实际x1形变／力与补充x40](../functional_views/native_gripper_task025_20261003/native_mean_path.png)及[四帧动画](../functional_views/native_gripper_task025_20261003/native_mean_path.gif)。下一功能优先现有原生细夹爪的小步平均驱动及真实切线/LU成本；该设计不同于粗设计，不称网格收敛。完整研究行程／真实夹持／释放重入／H2-H3／HF5标签仍待完成。

main 7baa4b6及[本阶段实际公开恢复](../handoff/native_gripper_task025_20261003/public_recovery_verify.json)通过：20 payload／131数组、图包6文件字节相同；物理与求解诊断JSON仅排明确耗时及关联hash。公开CLI192.58秒、0新HP，同机同runtime异目录范围；正式与公开共28force/18tangent/2solver，原新HP仍8。下一细候选小步路径已具体规划，尚未准备或执行。

以下增补保留各执行时点；当前结论和下一步以本条及报告末节为准。旧记录中的“尚未实现”和旧计划不作为当前状态。

2026-10-03 current: Native NumPy average-displacement API and CLI now solve an ordinary coarse gripper file for [0,.001] mm. Two accepted states passed four fresh HP80/120 full-element references and two integration tests: input R=.0002084121 N, free +y output=.0011437157 mm, independent residual 1.54e-11. See [implementation, evidence and commands](../docs/NUMPY_FORCE_PROGRESS_20261002.md#native-mean-20261003), [actual deformation and forces](../functional_views/native_mean_20261003/native_mean_path.png), and [two actual frames](../functional_views/native_mean_20261003/native_mean_path.gif). This is a small no-workpiece TEST; next is the ordinary coarse inverter. Full stroke, workpiece, study H2/H3 and batch qualification remain incomplete.

Science commit 93851df passed [public recovery](../handoff/native_mean_20261003/public_recovery_verify.json): 12 payload files, 77 arrays and all six saved-view files match. Physical and solver JSON matches except explicit measured times and their hashes; zero new HP calls. Next ordinary inverter small TEST is not yet executed.

2026-10-03 current: `native_tangent.evaluate_native_tangent` and `scripts/evaluate_native_tangent.py` now save all three complete NumPy element tensors and full CSC matrices. One supplied coarse gripper checker state (3200 elements, 6642 DOFs) passed 40 fresh HP80/120 calls for both declared directions and two integration tests; worst normalized action error is 4.43e-14. Fixed rows/columns and HuHu asymmetry are retained. See [implementation, physical meaning and commands](../docs/NUMPY_FORCE_PROGRESS_20261002.md#native-tangent-20261003) and [saved directional internal-force derivatives](../functional_views/native_tangent_20261003/native_tangent_directional_actions.png). The 21.25-second evaluation is not an equilibrium solve or an executed .025 mm target. Next is an ordinary-file small mean-driven path; workpiece, study H2/H3, complete contact and batch qualification remain incomplete.

Science commit ae8f29c passed [public independent-directory recovery](../handoff/native_tangent_20261003/public_recovery_verify.json): nine result files, 43 array fields and all four view-package files match. The [next coarse-gripper small mean-driven path](../docs/NUMPY_FORCE_PROGRESS_20261002.md#native-mean-next-20261003) is planned, not executed.

2026-10-03 current: `native_force.evaluate_native_force` and the ordinary-file `scripts/evaluate_native_force.py` now provide complete NumPy element/global material, HuHu and total forces. Six supplied states on three native models passed 64 fresh HP80/120 calls with every element and DOF covered; three focused integration tests passed. Worst normalized force error is 8.64e-17. See [implementation, physical results and commands](../docs/NUMPY_FORCE_PROGRESS_20261002.md#native-force-20261003), [displacement/J/Hu](../functional_views/native_force_20261003/native_force_fields.png), and [internal forces](../functional_views/native_force_20261003/native_force_components.png). These manufactured states are not equilibrium solutions or an executed .025 mm target. Next is ordinary-model unsymmetrized tangent validation, then a small mean-driven path; research H2/H3, workpiece clamping and batch qualification remain incomplete.

2026-10-03 current: native_project.build_native_project and scripts/prepare_native_project.py bind an explicit task to unchanged native geometry and construct material arrays, actual Dirichlet groups, weighted ports and Q1 operators. Three TEST models passed exact independent comparison of all 23 saved arrays; five focused construction tests passed. The two coarse models match 17 intrinsic historical fields; the fine gripper has 26082 DOFs and 169 fixed DOFs under its explicit TEST contract. See [implementation and commands](../docs/NUMPY_FORCE_PROGRESS_20261002.md#native-model-construction-20261003), [actual boundary groups](../functional_views/native_model_20261003/native_model_applied_bcs.png) and [mean input equations](../functional_views/native_model_20261003/native_model_port_equations.png). The stored .025 mm target was not executed. Next is static NumPy force/reference for the new file interface, then bounded numerical paths; study H2/H3, workpiece clamping and formal HF5 remain incomplete.

Earlier entries below retain their execution-time scope; use the latest linked record for the next step.

2026-10-03 current feature: `hf_eval.split_displacement.solve_split_displacement_path` supports weighted mean input, a free output spring, explicit lift/warm state and multiplier, using the unsymmetrized augmented CSC system. Pass the NumPy combined assembler explicitly. Two six-element tensile-block paths completed; 272 fresh HP80/120 checks passed. See the [implementation and physical results](../docs/NUMPY_FORCE_PROGRESS_20261002.md#split-average-20261003) and [actual deformation/force/output view](../functional_views/split_average_20261003/split_average_demo.png). This small-task qualification does not extend to canonical mechanisms, contact or HF5. The legacy file dispatcher and default kernel remain unchanged.

2026-10-03 follow-up: the new h=.125 NumPy C1 approach/compression reaches all seven original targets. Twenty accepted records / nineteen unique split states pass 420 newly computed HP80/120 numerical checks. The [functional record](../docs/NUMPY_FORCE_PROGRESS_20261002.md#numpy-h0125-path-20261003), [actual animation](../functional_views/numpy_c1_h0125_20261003/numpy_path.gif), task inputs, full models, matrices and exact new references are in Git. `scripts/run_numpy_c1_path.py --task-input` reads the compact ordinary task files; the default kernel is unchanged. Next is split average-port control; general contact and real workpiece clamping remain incomplete.

2026-10-03 opt-in NumPy split mechanics: `split_kernel_invariants_hu.assemble_split_numpy` supplies forces; `split_numpy_tangent.assemble_split_numpy` also supplies the unsymmetrized mechanical Jacobian. The existing 33 manufactured + 63 saved static states passed 774 candidate and 774 HP80/120 gates after a local tiny-energy/log correction; 26 relevant regressions passed. See the [functional record and original scope](../docs/NUMPY_FORCE_PROGRESS_20261002.md#numpy-scope-20261003) and [actual deformation/force view](../functional_views/numpy_scope_20261003/numpy_scope_terminal.png). The default kernel remains unchanged. Static coverage does not admit new equilibrium paths, compiled AD, average-port split control or general contact.

Version **0.5.0** adds explicit two-component displacement storage and prescribed-motion evaluation. The physical state is the exact sum of the saved binary64 `u_lift` and `u_fluctuation` arrays; `u_display` is a rounded plotting view. Four frozen uniform normal-contact combinations have passed their production, independent precision and reference audits with the original material parameters and thresholds. See [split-state implementation](docs/HF4_SPLIT_IMPLEMENTATION.md). General nonuniform contact, cylinder gripping and real mechanism performance remain outside this validation.

Use `hf_eval.split_state.SplitDisplacement`, `hf_eval.split_kernel.assemble_split`, and `hf_eval.split_prescribed.solve_split_prescribed_path` for this explicit state interface. The synthetic geometry still comes from `hf_eval.normal_contact.build_normal_contact`. For ordinary NPZ/JSON evidence, run:

```powershell
python scripts/run_hf4_split_normal.py --spec configs/hf4/validation_spec.json --gamma-index 1 --mesh-index 1 --output ../new-split-result
```

The split interface has no automatic conversion of the geometry-file `evaluate` dispatcher below. Each state, reaction and gap must use the declared representation. The independent audit is `scripts/audit_hf4_split_normal.py`; a run-specific frozen source manifest binds its evidence. Reuse no output directory from a prior run.

Historical **0.4.0** added the normal-contact task and U-only affine prescribed-motion interface, with **3 of 4 paths** completing. The fine gamma=1e-7 case stalled because free-node updates were lost in the absolute binary64 state. Its failed path, null target metrics and [original implementation](docs/HF4_IMPLEMENTATION.md) remain historical evidence. The old `solve_prescribed_path` and U-only kernel retain their original semantics; the split interface is explicit.

This standalone Python package provides immutable geometry input, the HF-1 **solid-only small-strain linear diagnostic**, and the HF-2 **finite-deformation Q1 third-medium source-code benchmark**. The latter is one uploaded C-shape configuration, in explicitly labeled source numeric units. It is not a validation of contact accuracy or a research performance ranking; geometry generation and topology optimization are outside this package.

Version **0.3.0** adds explicit project mapping and average-displacement control for the native inverter/gripper pilot tasks, plus stable near-zero material arithmetic. See [HF3 implementation](docs/HF3_IMPLEMENTATION.md) and [HF3 validation](docs/HF3_VALIDATION.md) for the recorded evidence and its limits. Readability, research qualification, numerical completion and functionality remain distinct.

The historical **0.2.1** C-shape path passed independent high-precision equilibrium at all 100 targets under the unchanged external 1e-8 threshold. See [repair validation](docs/HF2_REPAIR_VALIDATION.md). That full-path evidence remains tied to version 0.2.1; version 0.3.0 separately reruns the original small and fixed strong-state regressions. The original 0.2.0 run remains [partially complete](docs/HF2_VALIDATION.md), with its failed states preserved.

Runtime: Python 3.13, NumPy, SciPy, Matplotlib, JAX and jaxlib. All exact runtime versions and hashes are in `requirements.lock`. No LF source, LF environment, MATLAB process, exporter, or external source path is required. MATLAB and LF-specific preparation scripts are maintained outside this repository.

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install --require-hashes -r requirements.lock
.venv\Scripts\python -m pip install --no-deps .
.venv\Scripts\python -m hf_eval inspect <geometry.json>
.venv\Scripts\python -m hf_eval evaluate <geometry.json> --task <task.json> --solver <solver.json> --output <new-result-directory>
```

The release ZIP also contains the tested wheel in `dist/`; it can replace the
source installation step above (`pip install --no-deps <wheel>`). A Git checkout
does not need that ignored build artifact: the source installation uses only this
repository and its pinned build backend, never an LF checkout.

For the supplied data package, use `canonical/inverter/geometry.json` with
`tasks/inverter_linear_interface_smoke.json`, or the corresponding `gripper`
files, and `solvers/hf1_q1_solid_linear_v1.json`. Paths are relative to the
data package, not hardcoded by the evaluator. See `dataset_index.json` there.

Developer validation: after installing the locked runtime, install `requirements-dev.txt` in the independent HF
environment, then select tests appropriate to the current change. Routine tests use ordinary fixtures; full C-shape paths are excluded. The four campaign-bound modules `test_windows_owned_process.py`, `test_windows_owned_cpu.py`, `test_windows_cleanup_contract.py` and `test_s0_event_logging.py` retain closed-card identity/deadline requirements. Do not fabricate those environments for a generic suite. See [the scoped regression command](../docs/RESUME_DEVELOPMENT.md) and the archived campaign receipts. Recovery of evidence does not authorize replay of a closed experiment.

The result has separate readability, geometry qualification, numerical convergence and functionality fields. Missing research criteria remain `pending`; a successful linear solve is not proof of nonlinear/contact fidelity. Output signs, reference thickness, mean-port weights and support selection are explicit. Every call starts from the undeformed state and generates a fresh evaluation ID.

Q1 plane-strain stiffness is independently implemented with 2×2 Gauss integration and assembled only over solid cells. Mean input displacement uses a Lagrange multiplier, rather than equal displacement at every port node. Optional output loading is one generalized rank-one spring. Symmetry and fixtures constrain only solid-incident nodes in this diagnostic; there is no third medium.

See `docs/DATA_FORMAT.md` for the frozen file contract and `docs/HF1_VALIDATION.md` for the historical 0.1.0 validation. The input geometry remains unchanged; results store hashes, configurations, dependency versions, arrays and plotting data.

HF-2 keeps all solid/third-medium nodes, uses 3×3 Gauss–Lobatto integration,
and differentiates the actual nonconservative residual with JAX float64 on CPU.
The Jacobian is not symmetrized. Newton trials check positive J and finite values;
bounded residual-based backtracking and bisection preserve the last verified state.
For exactly the archived source target multipliers, run from this repository:

```powershell
.venv\Scripts\python -m hf_eval tmc-cshape --source-setup validation/hf2/reference/cshape_setup.npz --output new-cshape-result --time-limit 1200
```

The source setup is ordinary data and is checked against the independent preset.
The preset has E=100, nu=0.3, kv=1e-6, alpha=1e-6, thickness factor 1 and total
y-force −3 in source numeric units. It does not inherit HF-1's MPa/mm/thickness
choices. For direct Python API use, set `JAX_ENABLE_X64=true` and
`JAX_PLATFORMS=cpu` before the first JAX use; the CLI sets them explicitly.
Every call begins from zero. Accepted steps are saved incrementally; failed
targets have null metrics and the last reached multiplier. Hard process termination
may leave only checkpoints and the external resource receipt.

See `docs/HF2_IMPLEMENTATION.md` for the new interface and `docs/HF2_VALIDATION.md`
for validation scope and evidence. The original HF-1 release ZIP remains unchanged.
