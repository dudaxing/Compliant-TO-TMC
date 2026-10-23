# L-CTIPFREAL1 纯JSON显示候选

2026-10-23。候选 `D:/hfr1_001/view_freal1.py`；只编写和AST／源码核对，**未导入、试绘、运行或打开任何图像／NPZ**。需要完整源码冻结、独立静审和正式科学／比较成功后，原唯一窗口内运行一次。

运行时仅读四份不同普通JSON：BASE/protocol.json、BASE/observer_binding.json、RUN/force/result.json、RUN/comparison.json。用读取当时原字节记录输入SHA，receipt不需再读取旧资料；不读source_binding文件、原probe JSON、任何NPZ或旧媒体。所需两参考scalar由比较器 `reference_steps` 携带；`cross_errors` 给预声明误差与界。只有force success与comparison pass才建全新view目录；没有partial显示或重绘fallback。

## 固定五图及动画

|文件|内容|
|---|---|
|01_actual_geometry.png|全域和工件／尖端近景，源参考网格点线与新接受末态多边形；真实几何×1，不放大位移，标半模型P、未知q、hold及机构R。|
|02_P_q_cross_check.png|原两given-q端点参考和新所有given-P实际接受态；线仅视觉引导，不插值参考。原P1的q／全场／R三误差除各自预声明界单列，原值和单位标明。|
|03_force_components_and_R.png|有符号内部total／material／Hu、显式P、独立机构R；末态ON-body Fx/Fy分量及去重外载账本，半模型厚度20mm已含，不称压力或容量。|
|04_tip_right_geometry_global_J_Hu.png|原body栅格边界与tip节点11260的最近线段无符号距离；原right480介质及自由右边界实际×1几何；全部新接受态的距离和已有全局minJ/maxHu曲线。没有局部场色图。|
|05_convergence_and_gates.png|所有实际Newton base checks双rho及原mean门；每接受态global门、rigid/zero门与Newton检查数，保trial／内部失败计数。|
|actual_force_states.gif|每实际接受态一帧，N≤17，含全部二分接受态，真实几何×1；帧文字含原P／未知q／R／hold和请求或内部态分类。播放顺序不是物理时间，无插值或伪造中间帧。|

输出 `geometry_metrics.json`（只从本次JSON positions观察几何）与 `renderer_receipt.json`。receipt键 `new_png_count=5`、`images` 五图原字节SHA／大小、`animation`身份、actual_animation_frames、4个输入identity、NPZ_fields_decoded=0、scientific_calls=0、old_media_reads=0。动画只按writer.grab_frame次数记录，不重开GIF解码。原窗口后续root只检查五新PNG各最多一次。

## 定义及限制

body原510 cells边界按Q1四边邻接计数1生成，保原成员／节点，不随运动remask；每态用真实positions把tip投影到各原边界线段，取最近无符号欧氏距离。包含原半模型cut edge，且不凭该距离阈值发接触／压力／承载资格。只观察保存的几何，不新增有限元或导数计算。

right480必须在新model.solid均为false且不属于原body cells，模型body成员与新observer匹配后才绘制。使用新.50父身份绑定；旧observer1.06元数据不进入显示。右侧图明确是窄几何条带，蓝线实际自由右边界、点线原x92，不称固定墙。global J／Hu来自接受态已有标量，不冒称right480局部场；不读fields.npz。

所有几何equal aspect、实际×1，既不夸大工件位移也不把示意图拿来当FE网格。三相仅分类色，非场色标；长窄右域采用全高专用列并旋转x标签。各数值轴有N／microN、mm或1/mm标记。残差／误差只有精确0映射到显示floor，严格正值保原，原JSON完全不改。API结果数值／工程门来源独立于图像可读性。

计时从第一段可执行time.monotonic开始（早于Matplotlib导入）；内部生成上限510秒，各图／动画每帧及receipt前检查；完整显示与root五图检查共享原600秒，viewer由原SUP2另受8GiB子限和外限保护。程序不延长窗口、不retry、不删除/覆盖旧view，也不生成额外图。若中途失败，实际新输出由原首错停止流程保留，不修复重绘。

当前只生成候选源码，没有加载结果或科学数据。下阶段需要独立核对最终comparison schema和protocol、Matplotlib静态调用及五图布局，实际图像检查仍未发生。
