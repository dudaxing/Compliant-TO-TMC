# L-CTIPFHIGH1 比较器实现说明

2026-10-23；作者 `/root/fload_tests`。仅编写 `D:/hfh1_001/compare_high1.py`，由已通过低输入实际运行的 `D:/hfr1_001/compare_freal1.py` 改写。当前只做AST/源码核对；未导入比较器、HF或NumPy，未读NPZ/ZIP/媒体，未试运行、测试或绘图。正式生产57文件未改。

候选身份：24340 bytes，SHA256 `63a07ef7d9e99afe0af16c5ec9b53261384a21b43c9915c3a3a06979fbd7c249`。唯一未来命令无参数；只在helper确认新科学路径success后运行一次。输出固定 `run_001/comparison.json`，已有输出即拒绝且保留，不写来源或force/result。

## 高输入适配

- 准备来源结构改为 `parent_binding/reference_probe/proposed_loads`；普通source_binding按protocol的唯一原字节pin绑定，旧reference/result按准备SHA及canonical descriptor核验。
- 固定父选accepted12，held mean=1.06mm；明确P0=`0.0002399800950672949`、P1=`0.0002561572865437846 N`，Nmin=`1.011074467280606e−6 N`；全model29970DOF/14720格。父split/R及任务/模型/掩码来源身份保持。
- 旧给q参考实际3态 `[0,.0125,.025]`、原目标标志 `[true,false,true]`，只选旧accepted `[0,2]` 的两个原请求，原target indices `[0,1]`。核对source绑定的三态原值及原invalid_J回滚/计数，不读中间态NPZ。
- 新路径必须完整success、两原P请求且严格递增，保全部实际2至17接受态；mechanical/chunk256、父port_projection元数据和新guided_reduced_tangent均核对；原非clock设置保持、新controller3600。
- 每接受态都核普通保存摘要的free/generalized/compensated mean/J/rigid/global门、成员及原检查/二分上限。mean门固定1.0600000000000001e−10mm、Ffloor2.12e−7N、SP=max(absP,absP0,Ffloor)。API已在缓存前检查全部J/字段，比较器不借摘要伪称重扫科学场。

## 唯一科学读取和比较

只有四次 `state_arrays` 调用：旧q0、旧q=.025、新anchor、新原P1终点；共4个不同state NPZ/8字段。每档仅一次read_bytes，先核archive SHA，随后同一BytesIO解码；只允许lift/fluctuation，各29970 float64，核shape/有限/字段SHA/原split hash。无fields、旧力/切线、HP、媒体或新F/T。

锚点lift/fluctuation逐位等同旧q0、R按binary64字节等同旧q0及父R，state SHA相等、q0且checks1。终点全29970DOF逐项四split的math.fsum差，预定q与全场界1e−6mm；R界为max(1e−10,1e−7|Rref|)=`1.9536542042187397e−8 N`。不是显示坐标差、插值或给q回退。分量重组/载荷账本浮点差只作描述，不增门。

## 普通JSON输出合同

沿用旧viewer字段 `reference_steps`（仅两原请求）、`new_requested_steps`、`anchor_checks`、`cross_errors`、`endpoint_comparison`、`accepted_scalar_gates`、`component_and_ledger_descriptions`、`counts`。增加：

- `reference_history_steps`：三态普通标量/forceparts/ledger及accepted/original/depth标记；中间态 `pairing_role=HISTORY_ONLY`。
- `reference_failed_attempts` 与 `reference_call_counts`：原历史原对象；`reference_history_counts`保实际3态、15检查、12trial计数。
- `reference_pairing`：selected_accepted_indices `[0,2]`，原目标 `[0,1]`，内部 `[1]`，`intermediate_N_states_paired=false`，不插值。
- `numeric_path_status/failure`保持API原数值结论；`engineering_comparison_status`在完整误差产生前为 `not_run_or_incomplete`，终点工程门才为 `PASS/NOT_PASS`。最终 `status=pass` 仅全部门通过；失败不改API success、不填虚假零差。

异常仅记录实际失败及已发生读取计数后退出1；无循环重试/修复重跑。四档/八字段成功计数是实际累积，失败可小于上限。未来helper在status=pass后才允许viewer；本候选不会发起科学或显示。待独立静审和root最终protocol绑定，当前尚未执行。
