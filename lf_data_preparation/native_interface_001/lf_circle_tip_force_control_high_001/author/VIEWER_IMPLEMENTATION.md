# L-CTIPFHIGH1 高输入保存态显示实现

2026-10-23。本文是源码实现说明，不是运行或图像验收记录。研究层显示器从已完成 FREAL1 的纯 JSON viewer 有限改写；不改 57 份生产源码、物理任务、求解器或数值门。当前仅编写、读源码及标准库 AST 解析；未导入候选、HF 或渲染库，未运行科学计算、测试、图像生成或像素检查。

## 输入与来源

唯一入口 `D:/hfh1_001/view_high1.py` 不接受参数，运行时只读四份普通 JSON：BASE/protocol.json、BASE/observer_binding.json、新 RUN/force/result.json、新 RUN/comparison.json。需数值路径 success 且工程比较 pass 才显示。accepted 2 至 17 态全部使用新结果缓存坐标、连通性、solid 和普通测量；不读 NPZ、旧媒体、局部 J/Hu 场或参考科学缓存。510 秒进程内生成时限由自身 monotonic 检查，进程树 8 GiB 及完整清理由外层 SUP2 负责。

原模型 14985 节点／14720 Q1 单元，工件 510 格／565 节点、右侧 480 个原非工件介质格和 81 个原域边界节点由观察绑定核对。固定尖端 node11260 到原工件栅格边界线段的距离使用真实新坐标；明确排除 y=40 对称切口。没有重新选工件成员、改掩码或用解析圆代替栅格边界。

## 五图与动画

1. 全机构与工件实际 ×1 坐标，叠加未变形网格；显示输入均值、外载 P、未知解 q 和输入 R。
2. P–q 与预声明工程误差／门比值。旧位移参考只取 accepted[0,2] 两个原请求配对；accepted1／q=.0125 仅灰色 HISTORY ONLY 标记，不与新 N 二分态配对或插值。
3. 有符号 total／material／Hu、独立机构 R、ON-body x/y 与互斥外载账本；P 为已含 t20 的半模型 N。全对称轴向外载 2P，q 不变；不重复加入旧 body-x 处方反力。
4. 尖端与右介质实际几何、全域已保存 min J／max |Hu| 及无符号栅格边界距离。保留上下文，并在 tip／closest 中点 ±.08 mm 添加同图坐标放大 inset；坐标窗口缩小，变形倍率仍 ×1。该图不声称局部 J/Hu 场或接触压力。
5. 全实际 Newton base 双残差、原 mean 门、全部 line-search merit／Armijo trial、所有接受态 global／rigid 门与计数。旧 invalid_J／内部二分历史单独保留；高输入实际 Ffloor／mean bound从新普通结果显示，不借用低输入常数。长失败码换行、2×3 布局容纳最多17态。

GIF 按所有实际接受态顺序逐次 writer.grab_frame，成功一次才递增 written_frames；无插值、不冒称物理时间。receipt 使用实际写帧计数，不解码 GIF 来数帧。renderer 在保存后仅一次读取所生成 GIF 原字节作 SHA；后续原字节封存不属于 renderer 的该计数。

## 结果协议与限制

输出 01_actual_geometry.png、02_P_q_cross_check.png、03_force_components_and_R.png、04_tip_right_geometry_global_J_Hu.png、05_convergence_and_gates.png、actual_force_states.gif、geometry_metrics.json 和 renderer_receipt.json。receipt 固定 status=`rendered_pending_root_visual_check`，五图像素检查仍须 root 在原共享600秒窗口执行；本说明不预填检查通过。

比较 JSON 延续 reference_steps/new_requested_steps/cross_errors 合同，新增 reference_history_steps、reference_failed_attempts、reference_call_counts、reference_pairing；需历史3态、原目标 accepted[0,2]、internal[1] 且 intermediate_N_states_paired=false。全部旧失败及计数由比较器带入，viewer 不另读旧参考文件。

log 图只给恰好为零的值显示下限，原记录不变：rho 1e-18、mean/rigid/trial ratio 1e-22、global 1e-20；图和 receipt 明示单位与显示下限。new_body q 是求解未知量；预载 P0 非零，所示内部弱力含 Hu，ON-body 与施加载荷反号，不能从本次局部两载荷交叉升级压力、纯接触承载、极限、摩擦、释放、唯一性、稳定性或 HF5 资格。

## 冻结身份

|源码|bytes|SHA256|
|---|---:|---|
|view_high1.py|28963|a0cb4d36e8e85b47bb7a3f91c571b12090d0d31af918f99acf92dc6ca174dee9|
|继承来源 view_freal1.py|22698|702c93b13af54a4120220711b8418adc963474ce45b8ade030ca4ee5382096f3|

AST：pass。候选导入／数值执行／试绘／新像素检查均为0；生成是否成功以未来唯一正式窗口的真实记录为准。
