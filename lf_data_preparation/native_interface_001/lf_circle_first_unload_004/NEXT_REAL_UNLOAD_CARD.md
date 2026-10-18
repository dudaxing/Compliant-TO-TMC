# 待批准 L-CUNLOAD5：一次有界完成剩余圆形输入卸载

**本文件仅下一阶段普通计划，尚待人类批准新目标与新资源额度；未实现、冻结或执行。** 拟继续使用现有saved public API，无默认源码修改/安装、新测试、HP或新的力学算法。

## 父态与精确目标

父结果：`lf_data_preparation/native_interface_001/lf_circle_first_unload_004/run_001/wave_circle_unload125/result.json`。选末accepted **1** / global原目标 **10** / **1.25mm**，state SHA `4e3c308bba3e6776abebafb2964542ec4c1efb5224c26f5233d7e11a511adfa2`，signed R `.21844194402663442N`。

一次 `evaluate_native(..., saved_result=parent, selected_state_index=1, extend_path=True)` 请求：

`[1.25, 1.15, 1.00, .75, .50, .25, 0] mm`

其中1.25只fresh重验，后六项为新目标；对应global original **10..16**、child-original **0..6**。新完整task为17个原目标：

`ordered_cycle [0,.25,.5,.75,1,1.15,1.25,1.35,1.4,1.35,1.25,1.15,1,.75,.5,.25,0]`

只在C4的targets后追加这六项。**input.target_mm仍1.40；其他所有task键（包括四说明metadata）精确保留。** 新阶段说明放外层card/protocol。工件仍固定圆r9/center(71,40)，原wave网格/掩码/端口/支承/材料/介质/正则化不变；mechanical/chunk256/port_projection不变。

## 授权额度、原门与停止策略

建议controller **5400s**、shared display **600s**、helper **6600s**、outer **6660s（111min）**、helper/outer采样上限**64GiB**。四库线程env cap16在导入前设置，实际使用核数不保证；原viewer内部8GiB更严子限原字节保留。

数值设置只把本次time_limit_seconds从1800改5400（现reader允许新clock），其余原样：Newton25、Armijo1e-4/backtracks12、max_bisections4、minimum_increment.00625、原floors。J>0、residual1e-9、原mean约束bound、relative global balance1e-6、fixed split fsum8e-11mm等门完全不变。

C3/C4实际窗口约340/398s，新卸载端点5/6检查、无拒绝trial或二分，恢复指标持续改善。约400s×6≈2400s支持5400s controller的有界预算，但不是最坏成本或收敛保证；0端点更接近原残量/约束尺度下限，可能需要更多迭代/内部二分。不得按预计时间冒填PASS或自动增加额度。

仅一个API/一个controller，一次连续下降。先在父1.25原split/stateSHA/signedR上fresh F/T平衡重验，不修正/重基准该accepted锚，不复用旧F/T/CSC。真实内部backtracking/bisection照原边界允许；其额外接受态全部保留，不硬锁N=7、不按d去重。首terminal错误保留原typed failure、partial result/response和本窗实际seal，停止后续显示并闭卡；不重试、修门、强制零反力、回滚、删除或从partial偷偷续算。

## 纯保存显示与输出身份

准备只继承旧producer seals＋stat，两个旧science输入仅父geometry.npz和selected001 state.npz(lift/fluctuation)，科学运行时在新唯一窗口读取。冻结普通父result/model/geometry/state descriptor/task/protocol/receipt及当前源。实现后先有限静审和最终byte-freeze，再唯一启动。

成功及全部原cached门通过才在共享600s内复用原S1 pure circle viewer＋convergence/table/page/display seal：**4PNG、1GIF实际N帧、真实×1**，全态/原顺序/原global-child索引，反力/q_out、material/Hu/total Fx/Fy、unsigned nearest与far-right tip、solid/medium J/Hu、Newton/线搜索收敛完整显示。viewer按实际N读1+2N新NPZ/27+18N字段（若N7则15NPZ/153字段）；全输出seal仍包含其余新tangents/CSC/来源档，不把viewer读集当全部科学文件。最终全封存在helper6600s内完成。

子段maximum accepted/maximum_loading_stroke为**1.25锚**，不是历史1.40峰；loading_peak_reached应false。当前continuation不加新的task_transition，首次跨kind旧proof留在parent_continuation历史链。完成到0时segment/path/unload_endpoint可true，**task_target/full-original/full-extended仍false**，target_response仍null，requested_endpoint_response为实际0端点。报告实际零返回R/q_out/弱力/J/Hu，不裁小量、不把浮点微小值改为精确零。

## 功能意义与明确范围

此阶段验证同一固定圆形模型能否经现有原门完成剩余输入回程；适合一次有界计划，现无迹象需要再造API或逐目标重复审批。可与对应旧加载位移的普通记录对照，保留重复位移身份，不把近一致当滞回/严格可逆/唯一性或稳定证明。

**输入回到0不等于工件自由释放**；工件DOF始终固定。unsigned不等于signed gap/containment，Hu/弱式分量不等于接触压力或有效夹持。完整加载prefix继承而非本次从零重演；旧CREF1仍只祖先1.15/global5单态/PORT，不能因本次再经过1.15就转授HP。全部旧闭卡失败/通过证据原样保留。若未到0，诚实报告实际最后接受位置与失败，不称完成回程。
