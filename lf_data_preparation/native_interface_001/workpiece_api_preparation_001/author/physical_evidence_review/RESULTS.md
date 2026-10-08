# 固定方体大行程：薄API实例准备记录（草案）

整体目标是让普通LF几何和明确物理任务，经独立HF入口得到一次正向响应、失败原因及可检查输出。本次选择已有右4 mm介质余量、固定side18方体的完整加载/卸载任务，以验证现有入口的实际可用性；沿用原物理输入，不同时改变形状、材料、边界、网格或行程。

只读定位已完成。普通几何与任务均已在仓库内，可用显式repo解析：`right_margin4_cycle_001/run_001/fixture/model/source_geometry/geometry.json`及同run的`task.json`。API已经支持fixed_rigid、ordered_cycle、路径与模式透传，摘要也已有body弱式力/holding/mirror/net；本次不重写工件入口。旧worker直接调用solve_native_mean和write_native_mean；已有saved_right4col_response仅由保存JSON formatter生成，科学调用为0，不能替代通过新API的真实forward。

原任务为native h1、84×40 mm、3360单元/6970 DOF；固定方体中心(71,40)、边长18 mm，右表面x80、右侧介质4 mm。E=1 MPa、ν=.3、厚度20 mm、γ=α=1e-6、Lr=80 mm和原端口/支承不变。24原目标为0,.25,.5,.65,.75,.8,.85,.9,.95,1,1.05,1.1,1.15,1.2,1.15,1.1,1,.9,.8,.75,.65,.5,.25,0 mm；mechanical/chunk256/port_projection，minimum_increment=.00625 mm，原全部settings与门保持。

| 旧右4 mm卡的实际量 | 保存读数 |
|---|---:|
| 完整路径 | 24/24原目标、加载峰值和卸载终点均到达 |
| 原生产 | 340F/325完成、174T/174完成、1solve |
| 峰值输入/输出 | d=1.2 mm，R_input=.4072527715 N，q_out=1.0088461324 mm |
| 峰值下半体总力(Fx,Fy) | (-.0024081239,.1193619515) N |
| 峰值Fy分量 | material .1178513816 N；regularization .0015105699 N |
| 峰值minJ / max\|Hu\| | 3.2722993e-5 / .2088465634 mm⁻¹ |
| 保存node-window底部余隙 | .0057303162 mm，原栅格诊断 |
| 独立参考 | 全24接受态、48新HP、488232检查通过 |
| 原成本 | production helper2489.5635228 s/outer2491.9097172 s；reference summary531.4370633 s/outer532.8025968 s |

这些是旧独立右4 mm卡的实际证据与人工检查背景，不是本次薄API的新结果或新视图。下半体力是固定体弱式合力；2|Fy|为双侧法向幅值和，装配净力为(2Fx,0)，不能混称压力或净夹持力。小正余隙不是接触证明。旧参考只授该接受态机械力及PORT方向切线，不授全列、一般接触/夹持/压力、能量/应力HP、域收敛或HF5整体。

[旧结构/实际变形](../../../functional_views/right_margin4_20261007/complete_001/view/comparison.png) · [旧力和距离](../../../functional_views/right_margin4_20261007/complete_001/view/distances_forces.png) · [旧峰值场](../../../functional_views/right_margin4_20261007/complete_001/view/peak_fields.png) · [旧24态动画](../../../functional_views/right_margin4_20261007/complete_001/view/right4col/actual_states.gif) · [旧真实生产](../../native_workpiece_001/right_margin4_cycle_001/run_001/result/result.json) · [旧独立参考](../../native_workpiece_001/right_margin4_cycle_001/reference/summary.json)

新可用manifest/窄mock的正式输入SHA、实际次数、功能receipt和资源窗口：**待根任务读取真实准备回执填写**。此处不预写测试PASS或数值资格。拟新实例仅含fixed_square一例，case输出为`native_interface_001/workpiece_forward_001/run_001/fixed_square`，index为同run的`batch`目录；每例现有API一次，不能在入口外先重复构模。

新真实forward、独参和新视图均尚未执行。W-API1仅拟一次4500/4560 s、8 GiB生产与compact summary，原controller settings4500 s一致；输入和whole外层时钟分别记录。根任务待worker/peer与实际源SHA固定后完善卡和授权登记；旧完整一次成本只是依据，已闭窗口不能续用，新结果不借旧48HP旗标。新HP和新保存视图根据实际结果另选阶段，旧generic无工件plot不能作为新WP显示包装直接复制。

外部evidence_review.json/md记录完整身份与范围，仅供准备核查；正式归档时由根任务补上这些准备资料的实际仓库路径。本报告是外部草案，不声明新科学卡、提交或推送完成。
