# L-CTIPFREAL1 四档比较器候选

2026-10-23。候选 `D:/hfr1_001/compare_freal1.py`；仅编写与 AST 解析，**未导入、未运行比较/测试、未读任何 NPZ/媒体或调用力学**。实际 SHA 以 root 最终冻结为准。唯一命令不接参数，固定读同目录 protocol.json 与 run_001/force/result.json。

## 普通身份与完整路径

比较器仅读4份普通JSON：protocol、已绑定原字节的 source_binding、旧LOW1 probe结果、新force结果。source_binding 必须在 protocol.bindings 中恰好一次匹配路径/大小/SHA；旧probe普通JSON必须匹配其中已冻结的 result_file_sha256。旧参考与新force各自 canonical descriptor 重核，只用标准库float.hex规范化，不导入HF。

新force原路径必须success、无failure、target_reached，且独立force schema正确；新旧source声明都必须绑定同一原固定父结果/model/task、accepted index2、原state descriptor及state/archive身份、有符号R和.50mm。原非clock设置、mechanical/chunk256、P0/P1、独立N步长、E*t=20N/mm、body/zero成员与全模型尺寸保持。比较不会回写或重新标记原force result。

新结果必须保全部实际接受态，2到17态、P严格递增，恰好2个原请求且位于首尾。全部接受态逐一核缓存普通门：有限、原free tol/scale/floor、新g独立尺度及绝对bound、原补偿mean界、正minimum_J、rigid/zero、global、checks与depth上限。原API在接受前已检查完整J/相关field有限；本比较器不读fields.npz冒称独立全J复查。调用计数须为一个solver、保存F/T与HP均0，完成的真实F/T不少于实际接受态数。

signed total/material/Hu和账本只作已有组件的描述性重组：保符号，显式(P,0)且没有旧body-x驱动重复项、body-y背景重叠去重。分量和分组的舍入残差输出原值，不增加未批准的新误差门或压力资格。

## 唯一科学读取及比较门

只打开4个明确的state NPZ：旧probe q0、旧probe q=.025、新force anchor、新force原P1终点。每档只read_bytes一次，记录实际读取后用同一原字节做SHA核查，再BytesIO(np.load)解码lift/fluctuation。每个字段实际取出后才递增计数，核float64、shape29970、有限与字段SHA；档内不允许其他字段，保存身份按原split representation重建state SHA。失败时保实际已读档/字段数量，不能预填4/8。

新anchor与旧probe q0：lift/fluctuation各逐位相同、原父/参考/new state SHA相同、有符号R逐位相同、q0=0、newton检查1。该硬门不使用终点工程容差。

终点：所有29970DOF逐项 `math.fsum([new_lift,new_fluctuation,-ref_lift,-ref_fluctuation])`，不能由rounded positions或先相加的display代替。输出最大绝对差、所在DOF和带符号差；q、全场位移各≤1e−6mm，R≤max(1e−10N,1e−7absRref)。只配两个实际原请求，不插值或将内部二分态凑成额外参考点。

API自身的原parent/geometry读取由worker另计，**不藏在本比较器4档8字段预算内**。比较器没有读任何旧force/tangent/matrix或新fields缓存，也不保存/改写科学payload。

## 输出合同

写一次 run_001/comparison.json，成功status=pass且退出0；第一个错误写status=failed、实际错误与读取计数，退出非0，停止后续显示。已有comparison不覆盖，只stdout报失败并退出；外部不得重试。具体可供纯viewer使用的键：

- `reference_steps`：两行原值，body_q_mm、P_target_half_N（由旧Q_drive_half_N映射）、R_input_N、force_on_body_N、minimum_J、max_abs_Hu_per_mm、input_mean_mm、relative_residual、relative_global_force_balance、newton_checks、state_sha256。
- `new_requested_steps`：新force两个原请求的相同普通字段。
- `anchor_checks`：split逐位、R逐位、state SHA、检查1和q0等硬门。
- `cross_errors`：q_abs_error_mm/q_bound_mm、physical_displacement_max_error_mm/physical_displacement_bound_mm/physical_max_error_dof、R_abs_error_N/R_bound_N及各pass布尔。
- `endpoint_comparison`：reference/new/errors，interpolation=false。
- `accepted_scalar_gates`、`component_and_ledger_descriptions`：全部实际接受态；重组描述不增加门。
- `scientific_npz_reads`、`scientific_fields_decoded`：实际动作计数；`counts.state_npz_files_read/state_npz_fields_decoded`提供同值；`scientific_reads`逐档记路径、实际SHA及实际解码字段。

纯viewer只需新force结果和该比较JSON中的原参考行，不再读旧LOW1结果或旧媒体。正式比较失败也必须保留原API数值成功与工程回归NOT_PASS的区别；本比较器不把失败解释为释放、承载极限或不稳定性。
