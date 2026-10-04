# Independent HF evaluator — HF-1 through HF-4-A/B

2026-10-04当前：**同一粗方固定半工件的新0→.5→1→.5→0 mm完整机械循环成功，5实际接受态的10次新HP80/120与96,781项原门检查通过。** 31/31F、18/18T、1solve；峰输入R=.216813996933 N、自由+y输出=1.159355055764 mm、minJ=.458189164213。真实unsigned外边界距2→1.47194→.924425→1.47194→2 mm；各保存态无相交，尚未证明接触或有效夹持。见[目标、原因、问题排查、物理效果与限制](../lf_data_preparation/native_workpiece_001/coarse_square_cycle_006/RESULTS.md)、[实际结构/力/变形/最近点图](../functional_views/native_workpiece_cycle006_20261004/saved_001/render_001/cycle006_saved_path.png)。

本轮只扩物理任务，004实现与6项接口既有实测保持，未重复测试；schema1.2机械模式能量明确not_evaluated，原算法/门未变。005因冻结stage身份谓词错误在生产前闭卡、0新数值；006作者路径遗漏在正式安装前修正，原字节留存。新资格仅接受态机械力/声明PORT方向/组装/平衡与工件合力，不含能量、应力HP、全列HP或一般接触。图仅读生产，原独立flags不回填，fresh参考资格另见报告。

下一步新1.5 mm粗方加载—卸载，据实际minJ/距离/成本再考虑2/3 mm；1.5/2/3 mm、圆形/细网格平衡尚未执行。signed gap/包容/法向、压力/有效夹持、自由工件、H2/H3/HF5、AD/JIT及完整项目仍待完成。仅main开发，origin=https://github.com/dudaxing/Compliant-TO-TMC.git；公开恢复只核文件身份。

以下保留以前时点原字节；当前接续以上述新结果与持续记录末节为准。


2026-10-04当前：**可选机械模式已接入NumPy平均位移求解器；新的固定对称半方形工件0→0.5→0 mm完整加载—卸载成功，三个接受态的6次新HP80/120及58,197项原门检查通过。** 接口6项实际测试通过；本次生产17/17力、10/10切线、1求解，213.73秒。峰值R=.106253247986 N、自由输出+y=.575755712293 mm、minJ=.735764774113；卸载返回近初始。真实外边界距2→1.471935964045→2 mm，均无交叉；仍未证明有效夹持。见[目标、实现、原因、效果及全部限制](../lf_data_preparation/native_workpiece_001/coarse_square_cycle_004/RESULTS.md)、[真实结构/力/变形图](../functional_views/native_workpiece_cycle004_20261004/saved_001/render_001/cycle004_saved_path.png)、[实际边界距离](../functional_views/native_workpiece_cycle004_20261004/boundary_saved_001/RESULTS.md)。

默认complete响应保持原17字段；新response_mode=mechanical/schema1.2保存16力字段/3切线/full CSC，并明确材料能量not_evaluated/qualified:false/field_present:false。原控制器/CI/T/B52/收敛门未放宽。旧003卸载失败及未捕获T25问题保留；新三态资格限声明task/source的力、PORT方向作用、组装和平衡，不包含能量/应力HP/全列切线/一般接触。图只读生产所以标题仍PRODUCTION ONLY UNQUALIFIED；fresh参考资格另读本报告，不回填原生产flags。

下一步同一粗方形固定工件的新1 mm递增加载与卸载，根据实际收敛/minJ/距离/费用再推进2/3 mm；圆形r8/细方/细圆模型已构建但对应平衡未执行。压力、有效夹持判据、signed gap/包容、自由工件、H2/H3/HF5及完整AD/JIT仍待完成。整体独立HF目标未完成，后续在main，origin固定https://github.com/dudaxing/Compliant-TO-TMC.git；公有恢复只核对文件身份。

以下保留先前阶段的原始记录。当前状态以上述新结论及执行记录末节为准，旧“下一步/尚未实现”只代表该记录当时状态。


2026-10-04当前：**显式NumPy机械量入口与force-only组装器已按原验证字节合入main；原F16三力/缓存切线及fresh HP80/120通过原门。** 32/32测试、19200局部＋9全局门全部通过，614400个局部T系数的完整CSC组装身份核同；最大归一误差7.24336e-15，HP80/120最坏相互误差1.21169e-52。新core d5f7新增可选机械职责，默认完整NumPy/JAX公式及能量要求保留；能量明确not_evaluated/qualifiedfalse，P/S仅finite无HP资格。见[目标、实现、为何拆分、实际效果与后续](../lf_data_preparation/native_workpiece_001/mechanical_only_candidate_001/RESULTS.md)与[保存三力和方向力变化率图](../functional_views/mechanical_F16_20261004/saved_001/render_001/mechanical_F16_qualified_fields.png)。

旧Horner192 001测试收集前失败、002的25例通过但完整F16失败、独立诊断48IP/35能量NaN均保持原记录；1d18候选未合入。新单态F16不是接受平衡，不解决尚未捕获的T25输入，也不转移到旧循环资格。粗方[0,.5,0]mm循环003仍仅2接受态、0新HP、卸载time_limit失败；见[真实0.5mm峰值与旧失败](../lf_data_preparation/native_workpiece_001/coarse_square_cycle_003/RESULTS.md)。

下一唯一近期功能：显式接入native_mean机械字段/能量可用性及source版本，保持原控制器、Armijo/KKT和默认结果合同；先小闭环，再新独立卡探索同一0.5mm加载—卸载，按新证据处理残余切线问题并扩到1/2/3mm与细方/圆工件。本接入和新路径尚未执行。压力/有效夹持、signed gap/交叉/包容、自由工件、H2/H3/HF5及完整AD/JIT仍待完成。整体HF目标未完成，继续仅main、origin保持https://github.com/dudaxing/Compliant-TO-TMC.git；公开恢复只验文件身份。

以下旧条目保留各执行时点；当前状态与接续以本条及持续报告末节为准，旧“下一步/尚未实现”不覆盖最新记录。

2026-10-04当前：**matmul320候选7fff已按原字节合入；新粗方固定半工件[0,.5,0]mm三点探索正式失败并关闭，峰值达到但卸载未完成。** 2接受态[0,.5]、R_input=.106253248N、自由+y输出=.575755712mm、minJ=.735764774。600s内部预算后实际exit1，66F/50完成、27T/26完成、1solve、0新HP。16全步范围拒绝后half收敛，随后T25范围失败回滚、二分.25遇时间门；全部来源和原27数组不变。不能称新循环或两态独立参考通过。见[整体目标、选择依据、全过程与实际结果](../lf_data_preparation/native_workpiece_001/coarse_square_cycle_003/RESULTS.md)、[×1结构/力及失败时序图](../functional_views/native_workpiece_cycle003_20261004/failure_saved_001/render_001/cycle003_failure.png)。

新独立保存F16诊断一次复现原异常：首坏为已选辅助能量Horner乘积的(lo,hi)回缩项，非旧矩阵乘法、非overflow；36点物理词落到2^-400下界以下。只1F开始/0完成、0T/HP/solve，diagnostic_captured不是数学资格。下一最小候选改Horner共同尺度与乘加顺序，保留原14阶系数/CI域/P/门；尚未实现，先新F16完整F/T与fresh HP核验，再新连续路径和1mm探索。不增预算重开旧失败，不裁零或借旧F36解释后期未捕获T25。

旧31d955七态14fresh HP及真实边距1.471935964mm保持自己的来源资格；保存F36/candidate7fff/consumer B52的19200局部＋9全局原门和原失败也保留，不能转给新循环。当前新图仅保存诊断、无新测距/夹持资格；1/2/3mm未执行。signed gap/交叉/包容、压力/有效夹持、自由工件、细/圆平衡、H2/H3/HF5及完整AD/JIT仍待实现或资格化。完整持续记录见[开发进度](../docs/NUMPY_FORCE_PROGRESS_20261002.md#native-workpiece-cycle003-20261004)。仅main、origin固定https://github.com/dudaxing/Compliant-TO-TMC.git；公开恢复只验文件身份。

以下为上一阶段及更早时点的保留记录；当前状态以页首与持续报告末节为准。


2026-10-04历史状态（0.1mm阶段）：**普通文件的固定半工件、平均输入驱动和连续加载—卸载已实现；粗方形工件[0,.1,0] mm实际完成，3接受态的6次新HP80/120独立参考全部通过。** 正方形side16mm、中心(70,40)mm，计算下半；3200单元／6642DOF／376有效fixed。峰值输入R=.020941490699N、自由+y输出=.114466446177mm，半工件总(Fx,Fy)=(-3.0237102546e-5,+2.3930273461e-5)N，minJ=.947487891；卸载末输入R≈-1.19e-27N、输出≈1.76e-27mm。生产263.45秒，参考60.11秒／58010检查；30项相关测试通过。见[完整目标、实现、诊断、成本和效果](../docs/NUMPY_FORCE_PROGRESS_20261002.md#native-workpiece-cycle-20261004)、[实际结构与力](../functional_views/native_workpiece_cycle_20261004/render_001/workpiece_cycle_physical.png)、[三帧真实动画](../functional_views/native_workpiece_cycle_20261004/render_001/workpiece_cycle_actual.gif)、[数值与分力](../functional_views/native_workpiece_cycle_20261004/render_001/workpiece_cycle_response.png)。

独立参考覆盖全部单元与DOF、三力、声明方向切线作用、CSC组装、平均约束及工件/支承反力；不是高精度穷举全部切线列。生产22F开始/19完成、11T完成、1solve，差额是3次返零力-only全步范围拒绝及原规则下的半步回溯，接受态通过不代表这些拒绝态已获资格。原“所有F开始必须完成”前置合同明确0HP关闭；[新保存态合同与计数对账](../lf_data_preparation/native_workpiece_001/coarse_square_cycle_001/reference_002/reference_contract.json)只修订这一已声明计数条件，全部原数学门保持。算术范围限制未完全消失；不扩大到接触、夹持压力、H2/H3、HF5、AD/JIT或全部任意输入。

Agent已按用户授权选择圆r8mm和正方形side16mm、中心(70,40)mm，粗方/细方/细圆三包构造通过；细方/细圆尚未求平衡。当前×1图仍明显张开，底/左节点窗口约1.896/2.039mm只是代理观测，非真实表面距离；微小预接触介质传力不能当有效夹持。新增纯保存态Q1外边界测量已通过14解析例及3接受态读取，双方排除y=40镜像切口、0新F/T/solve/HP；峰值底边最近无符号距离1.895882476mm、左边集1.981492877mm（最近为下角到下方实体，非侧向normal gap），卸载显示2mm，包容未检测。见[实际×1边界/最近点与独立代理曲线](../functional_views/native_workpiece_boundaries_20261004/render_001/native_boundary_geometry.png)。下一以同一粗方模型探索[0,.1,.25,.5,.25,.1,0]mm；依据实际作用和成本再扩到1/2/3mm及圆形/细网格。该大行程当前未执行。仅在main开发，origin固定为https://github.com/dudaxing/Compliant-TO-TMC.git。旧无工件细.025路径及公开重放保留各自冻结资格；本轮公开恢复仅验文件身份，不借用其数值重放资格。

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
