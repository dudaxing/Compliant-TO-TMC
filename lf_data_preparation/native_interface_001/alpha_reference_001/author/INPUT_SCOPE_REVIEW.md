# M-AREF1 两个新 alpha 保存接受态：只读输入合同

普通 JSON 身份及字段合同一致；可以复用冻结 B850 run_state 与 aa86 工件检查的科学方法，但必须使用原任务序号13/14执行，再在新的顶层摘要显式关联 child0/1。直接按 child0调用不合法：原 run_state 299行要求 index0 的 fluctuation 与 R全0，而当前child000是已变形1.20 mm峰值。这个门不改、不删；原Core/raw报告的13/14序号及目录保持。

本轮仅普通 JSON、源码/AST、源码字节SHA和NPZ文件stat；没有打开任何NPZ字节或header、没有导入HF/调用HP/F/T/solver/tests/方向投影/绘图，也没有修改正式仓库。原生产与父失败保持；本报告不是参考资格或资源批准。

## 两态与身份

| child / 原任务 | leg | d (mm) | R (N) | q_out (mm) | state SHA |
| --- | --- | ---: | ---: | ---: | --- |
| 000 / 13 | resume_origin | 1.2 | 0.37865427196005513 | 1.016934534302024 | fa0054288cd7eca4140f8bf04a94b5f833278b1c6e39813beb57cae16d7e9bca |
| 001 / 14 | unloading | 1.15 | 0.3470376815403639 | 1.0153174242325562 | 999b581e0d959599087149b83c2f12e3c1c261d91b1ddba7b3829dce06b52593 |

child000 state hash、保存state archive的声明SHA、signed R的binary64 hex均与M-ALPHA1原父013一致。父仍failed/time_limit、path/task/unload false；child仅两态suffix成功，full_original_path_completed/task_target_executed仍false，原HP/equilibrium/HF flags false。child/parent model JSON原字节与task/geometry canonical身份一致；本轮未以数组重读证明NPZ内容。两帧view summary中state/R/d/leg及原index分别对应这两态，原图/GIF不重生成。

## 物理与算子

模型13440 cells、13689 nodes、27378 DOFs，域84×40 mm、h0.5、lower_half关于y40对称。E1 MPa、nu0.3 plane_strain、thickness20 mm；gamma1e-6、alpha5e-7、Lr80 mm、kr0.004307692307692307 MPa mm²均直接抄自保存JSON，未重新计算。固定square中心(71,40)、side18 mm；648工件cells、703nodes、1406DOFs。

输入五节点位于x0/y38..40，沿+x，weights[.125,.25,.25,.25,.125]；输出五节点x80/y28..30沿+y，k_out0。支持选solid-incident节点，entity/background symmetry及holding分组来自原model.region_metadata。参考方向继承actual b_in/max(abs(b_in))并将fixed components归零、deltaR0；本轮没有构造方向数组，未来无需额外输入direction NPZ。

## 最小原保存输入

9个distinct NPZ需要解码：model一次27fields；两态各state2、forces16、tangents3、CSC numeric fields3，共75个descriptor字段。完整字段名/dtype/shape/声明SHA、原文件stat及路径在JSON future_archive_plan。aa86工件方法会再次打开两态state/forces，即4次额外打开及36字段重复；不是额外distinct数组。

SciPy CSC loader另读取format/shape并探测optional_is_array；若把mandatory CSC容器元数据计为字段，共79个。它们来自已读实际runtime源码，实际NPZ/ZIP keys本轮未看，不把声明字段误称header核查。source_geometry/geometry.npz可作为额外1个原字节绑定输入，4个mask不需解码：总计9 decoded＋1 provenance raw-only distinct NPZ。保留原geometry/model/result JSON及两个state.json；父result/model/013state普通JSON绑定身份即可，不需要读取父force/tangent/matrix或parent NPZ。

## 核心与来源胶囊

原15门、HP80/120各态一次（未来4HP）与完整local/global/CSC作用范围保持。机械availability为auxiliary energy omitted原合同；alpha变化通过保存lam/mu/kr等实际算子进入独立HP，不把旧完整24态loader的alpha1e-6和全路径flags硬套到child。新loader只负责实际2态身份、模型/任务/来源和明确flags，科学run_state/workpiece_checks不覆盖。

继承11份来源依赖，唯一basename平铺归档；原相对来源/SHA保持：

- `core_audit_mechanical.py` ← `lf_data_preparation/native_workpiece_001/right_margin4_cycle_001/reference_author/core_audit_mechanical.py`

- `audit_native_workpiece_cycle.py` ← `hf_repo/scripts/audit_native_workpiece_cycle.py`

- `audit_native_mean.py` ← `hf_repo/scripts/audit_native_mean.py`

- `audit_native_force.py` ← `hf_repo/scripts/audit_native_force.py`

- `hf4_split_precision_reference.py` ← `hf_repo/scripts/hf4_split_precision_reference.py`

- `hf2_precision_reference.py` ← `hf_repo/scripts/hf2_precision_reference.py`

- `run_split_average_demo.py` ← `hf_repo/scripts/run_split_average_demo.py`

- `__init__.py` ← `hf_repo/src/hf_eval/__init__.py`

- `tangent_action.py` ← `hf_repo/src/hf_eval/tangent_action.py`

- `compensated_invariants.py` ← `hf_repo/src/hf_eval/compensated_invariants.py`

- `tmc_kernel.py` ← `hf_repo/src/hf_eval/tmc_kernel.py`

原M-REF2平铺胶囊最长路径为 202 字符：`D:\Coding\Diversity TO\Compliant-Nonlinear-TMC-O\.github_handoff\Compliant-TO-TMC\lf_data_preparation\native_interface_001\nested_reference_002\run_001\reference\sources\hf4_split_precision_reference.py`。当前选定数组最长原路径207字符（source geometry NPZ）；根已明确新stage alpha_reference_001，拟output为run_001/reference，平铺sources最长路径201字符；这里只核这份prospective source capsule，不声称全部生成文件或OS路径政策已获保证。

Core按13/14输出accepted_013/014并由原工件checker保持原index/leg；新的top summary复制元数据关联index0/1，同时显式reference_execution_index/original_target_index13/14。raw accepted摘要及其所有physical/reference值保持，不能为consumer覆写。现native_response._reference的enumeration为child0/1，因此这份映射是必需合同。

是否新alpha两态通过所有原严格门尚未知，只有新批准后的fresh HP能回答。它不代表父14态、完整卸载路径、压力/有效夹持、全列HP、稳定性或HF5通过。

JSON SHA256：`978ffba68185589841feb2abc1b56198a85075f1a7af5e7b868b7e6928f0d7f9`。

补充：实际原launcher实名为saved_continuation_001/production_launch.json，不是resume_launch.json；task实名为regularization_sensitivity_001/task.json。新拟窗口helper900/outer960秒、8GiB、2态4HP，尚未授权执行。10个NPZ输入pin逐一继承已读旧M-RESUME1 execution_receipt.outputs，并与descriptor声明相等；本轮没有重新hash或打开NPZ，来源文件及成员key逐项写入JSON/seed。
