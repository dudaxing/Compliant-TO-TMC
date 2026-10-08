# 固定方体大行程：实例准备与实际功能检查

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

本次新增[单例配置](../../../hf_repo/configs/native/fixed_square_cycle.json)，通过既有batch将全部原DisplacementSettings和三种模式交给薄API，不新增产品求解逻辑。特别显式保留minimum_increment=.00625 mm；直接用默认值会按首步.25/16得到.015625 mm。新真实数值输出为`workpiece_forward_001/run_001/fixed_square`，其index在同run的`batch`，两者尚未创建。

独立静审通过后，根任务从Downloads无关cwd、显式repo唯一执行一次窄mock，exit0。真实batch与真实evaluate_native各1次，求解/保存/摘要三个科学委托均用mock各1次；全10项settings、24原目标、三模式、加载峰值/卸载终点和工件力记录正确透传。这只验证实例参数与字段的对接，真实构模/F/T/求解/HP/NPZ读取/新渲染均为0，新接受态0；fixture的24态及力值属于上表旧证据。所有新参考/视图/数值资格保持false。

实际helper至读回检查为1.3861648000 s（不含末回执写出/stdout），终端工具总钟3.9449683 s。28份原HF源保持原字节，不重跑旧21/15项测试或任何旧数值卡。[真实功能回执](validation_001/mock_check_receipt.json)、[终端退出回执](functional_terminal_receipt.json)、[独立保存闭审](author/mock_saved_closure_review.json)及4份原JSON均已归档。

下一步为[W-API1具体卡](W-API1_CARD.md)：一次4500/4560 s、8 GiB，经既有CLI/batch/API真实生产该工件完整加载卸载任务与摘要。其本轮尚未授权或执行，原资源窗口已关闭。后续根据实际N另选新独参及工件保存视图，不预授权。原无工件viewer不直接复制为新工件视图；人工检查可先使用上面6个真实旧证据链接。接触/压力定义、匹配网格及域收敛、圆体自身任务、自由体/摩擦与HF5整体仍未完成。
