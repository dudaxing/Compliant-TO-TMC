# 待批准 L-CUNLOAD4：圆形继续卸载 1.35 → 1.25 mm

**仅普通计划，尚未批准实施/执行，非冻结卡。** 供人类批准后实现研究包装、有限静审及唯一真实窗口。无新默认源码修改/安装、测试或HP；不重演加载，不从零重算。

## 父态、完整任务和API

父结果：`lf_data_preparation/native_interface_001/lf_circle_first_unload_003/run_001/wave_circle_first_unload/result.json`。选择其末态accepted **1** / original-global **9** / **1.35 mm**，state SHA `1e53b0a10e8c8f6614c7278d80326e91aded925ceba4c05f9a63376725dedab3`，signed R=`.23712864270675904 N`。

复用已安装public `evaluate_native`，显式 `saved_result=parent, selected_state_index=1, extend_path=True`。新task从C3 task精确复制，**只追加1.25**：

`ordered_cycle [0,.25,.5,.75,1,1.15,1.25,1.35,1.4,1.35,1.25] mm`

input.target_mm仍为**1.40**，circle r9/center(71,40)、机构网格/掩码/端口/材料/介质/正则化/支承/固定工件全部不变。此次来源已为ordered_cycle，同kind扩展要求其他task键精确一致，**连task_id、purpose、parameter_origin、description也不改**；新card名称/阶段说明写外层协议和记录。

实际child请求 `[1.35,1.25]`，global原目标9/10、child-original0/1，leg为resume_origin/unloading。保留全prefix内重复位移及全部真实二分接受态，不按d去重、不硬锁两态。

只允许两项旧science输入：父包 `model/source_geometry/geometry.npz` 和 `accepted/001/state.npz` 的lift/fluctuation。准备时只继承producer seal＋stat；运行在唯一窗口内读取。绑定父普通result/model/geometry/state descriptor、原task/协议/收据和当前来源。不得读取/复用旧F/T/CSC、改变旧结果或把显示位移当续算state。

## 原窗口、门与首错策略

controller **1800s**、共享display **600s**、helper **2700s**、outer **2760s**；helper/outer采样上限**64GiB**。OMP/OPENBLAS/MKL/NUMEXPR四库线程环境cap各**16**，在HF导入前生效并由clean viewer继承，实际利用核数不保证；保持CPU数学，不引入GPU。原S1 viewer内部**8GiB**更严子门原字节保留。

继承mechanical/chunk256/port_projection和C3/S5原设置：residual1e-9、mean约束原bound、global balance≤1e-6、fixed split fsum≤8e-11mm、J>0；minimum_increment .00625、Newton25、Armijo1e-4/backtracks12、max_bisections4及其他floors不变。

一次API/一个controller。先fresh F/T重验1.35锚，保持其state SHA、split与signed R原字节且锚平衡检查通过；不修正/重基准该accepted state。随后仅向1.25下降，记录实际F/T/检查/线搜索/二分和全部接受态。首terminal失败保留原typed error、partial result/response及本窗实际seal，停止后续显示并闭卡；不外部重试、延长、改门、回滚、删结果。原内部有界线搜索/二分允许。后续阶段须基于实际结果另决定。

## 显示与元数据必须正确

全child成功且全部原cached门通过后，原S1 pure circle viewer＋普通convergence程序在同600s内完成，连同binding/table/page/display seal；所有新输出在helper2700s内完整seal。保原**4PNG＋1GIF**，实际N帧按原viewer记录，全部接受态真实×1，不插值。显示R/q_out、material/Hu/total signed body Fx/Fy、unsigned nearest与far-right tip两项距离、solid/medium minJ、cellwise Hu与收敛。N按实际，viewer只读1+2N新NPZ/27+18N字段（N2时5NPZ/63字段）；其余新科学输出也全部封存，不漏tangent/CSC。

**本子段不含原1.40峰值。** maximum accepted d/maximum_loading_stroke及图的max应为**1.35锚点**，LAST为1.25；`loading_peak_reached`可为false，绝不能照C3硬要求true。input峰1.40是task历史值，不代表本次重到峰。

此次是同kind续卸载，**不新增当前continuation.task_transition**；C3的首次跨kind证明保存在`parent_continuation`。成功segment/path/unload-endpoint可true，task-target/full-original/full-extended仍false；target_response仍null，requested_endpoint_response为1.25。父记录及producer qualification flags不改。旧关闭卡NOT_PASS及原错误收据、L-CUNLOAD2 tiny验证证据均原样保留，不追改失败或借tiny成功替代真实状态。

## 选择1.25的理由与边界

C3的-.05卸载5端点检查/4个全步trial接受、无失败attempt/二分；medium minJ .052138→.086236，Hu max .471300→.416073，body Fy .004224→.003214N、nearest unsigned .06330→.09633mm。新1.35与历史加载global7在这些标量上几乎回到旧值，但state SHA不同。下一单目标-.10到已有历史加载1.25，可观察进一步恢复而不再增载或展开campaign；这是有依据的候选，不保证新平衡收敛。

完成后可把新global10与旧加载1.25分开列普通标量，不加精确state相同、单调力或滞回门。unsigned不是signed gap/containment，弱式体力/Hu不是压力；固定工件卸载不等于自由释放，也不授夹持/稳定性/完整cycle资格。CREF1仍仅祖先1.15/global5单态/PORT参考，不转授1.35或新1.25。本计划不调用任何新科学或读取载荷/媒体。
