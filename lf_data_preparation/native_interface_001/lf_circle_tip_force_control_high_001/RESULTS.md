# L-CTIPFHIGH1：高输入1.06 mm两载荷力控交叉结果

2026-10-23。**PASS，唯一执行窗口已关闭。** 机构平均输入保持1.06 mm，只给绝对半模型P0→P1、独立求工件有符号q和机构R；正式r9/mechanical/chunk256实际两态均通过原门及预先固定的端点工程比较。五张PNG各一次检查通过，2帧实际GIF已生成；四层SUP2清理及一次原字节封存通过。57份生产源码不改，新HP/测试/外部重试/安装均0。

## 整体目标、已实现能力与本次作用

整体目标是让独立HF读取LF夹持器几何，逐步实现大变形／第三介质接触分析、可审查的反力／工件力、加载／卸载和后续承载研究。原固定工件前向及续算、选定态参考、图像／接口关联、规定工件q探针已经具备，历史范围见[当前状态](../../../docs/CURRENT_STATUS.md)。[低输入.50 mm正式力控](../lf_circle_tip_force_control_real_001/RESULTS.md)又验证了给P→求未知q→对照给q结果的闭环。

本轮把这条功能推进到已有较强闭合、很小J的1.06 mm工况。复用已安装API和原力核，不新增生产层；研究包装只适配合法高输入父、实际3态参考的0/2配对及高输入显示标签／坐标近景。**参考q=.025 mm未作为力控输入、初值或夹限，也没有从旧probe终态热启动。** 同定义交叉通过说明正式高输入任务的控制方程、未知q/R及来源迁移可用，不能据此自动取得物理承载资格。[独立结果物理复核](author/RESULTS_PHYSICS_REVIEW.md)12/12项通过。

## 原任务与实际解

固定父为`D:/hpr1_001/parent_001/result.json`完整13目标load_only末峰accepted12/original12；原signed R=.19522304147728387 N和split迁移。保持α2.5e−7、γ1e−6、r9 mm／圆心(80,40) mm／right92 mm／Lr80 mm、E1 MPa／ν.3／plane strain／t20 mm／h.5 mm、14720单元／29970DOF、原510工件单元／565节点及端口／支撑；工件uy=0、转角0，成员不重mask。

|原目标索引|给定P_half/N|求得q/mm|机构R_input/N|Newton base checks|
|---|---:|---:|---:|---:|
|0|0.0002399800950672949|0|0.19522304147728387|1|
|1|0.0002561572865437846|0.025000000126731543|0.19536542042269825|4|

本次2原请求／2实际接受态、0内部二分、0failed_attempts；5个base checks、3个line-search trials，1次solver，8F/8完成、5T/5完成，HP0、save-time F/T0。fresh P0首次检查直接通过，q0、原lift/fluctuation及signed R逐位保持，没有predictor、投影或Newton修复锚点；P1使用原guided_reduced_tangent。父的port_projection只作历史metadata，新clock3600秒按卡独立覆盖。

原固定父split_displacement控制器SHA与当前版本不同，force/tangent两kernel匹配；差异及原SHA保留于[原准备来源审阅](../lf_circle_tip_force_control_high_preparation_001/SOURCE_BINDING.md)。这次实际准入和fresh检查已完成，仍不能将该局部结果解释为两个控制器所有行为等价。

## 适用原门与端点比较

|项|两态最不利实际值|原界|
|---|---:|---|
|ρF|1.2050887874880812e-12|≤1e−9|
|ρP|1.5237231287116481e-14|≤1e−9|
|mean绝对残差/mm|2.7755575615628914e-17|≤1.0600000000000001e−10 mm|
|relative global balance|1.8721359150883509e-15|≤1e−6|
|最小J|0.00041660852936145333|>0|
|rigid/zero误差/mm|0|≤8e−11 mm|

P1的g=Q_half−P_half=3.903127820947816e-18 N，SP=0.0002561572865437846 N，g界=2.561572865437846e-13 N。高输入Ffloor=2.12e−7 N、mean公式界1.0600000000000001e−10 mm保持，free与body合力尺度独立。

|P1对原规定q=.025 mm参考|实际绝对差|启动前冻结界|结果|
|---|---:|---:|---|
|未知q|1.2673154192732738e-10 mm|1e−6 mm|PASS|
|全29970DOF物理位移max差|2.9214952679268436e-10 mm|1e−6 mm|PASS|
|机构R|8.2428508463294747e-13 N|1.9536542042187397e-08 N|PASS|

全场差逐DOF用四split项fsum，最大差在DOF23309，不用显示位置相减。锚点硬身份和端点工程界分别核查，端点不要求逐位相同；工程界未按实际差收紧。详见[comparison原值/门](comparison.json)与[轻摘要](result_summary.json)。这些是功能工程比较，不是严格误差上界、完整路径HP或唯一稳定分支证明。

## 原位移参考困难完整保留

原PROBE1请求q=[0,.025]，实际接受[0,.0125,.025]；第一次直接+.025出现invalid_J、逐位回滚，内部二分后才接受.0125/.025。原28次F中27完成、15T均完成；旧终点minJ=.0004166085295994876。旧失败、中间态和计数仍在comparison/reference_history及source_binding中，图中.0125为HISTORY ONLY/unpaired。

本次力控顺利得到2态且未二分，是这次控制路径的实际表现，不改写原史。控制量、预测器及尝试数不同，不由单次总时间或8F/5T推断普适速度提升，也不把旧内部点配成新N中间态。

## 力、尖端与介质的物理含义

P为固定空间+x的**绝对半模型合外载N，已含20mm厚度**，不能再乘厚度或用ΔP替代P0。Q_half=Σbody f_int,x，ON-body Fx=−Q_half；完整镜像装配轴向外载仅2P，q不倍增。R为机构均值端口乘子，独立于工件外载。

末态ON-body total=[-0.0002561572865437885, 0.012505048665928714] N；material=[-7.023681733969096e-05, 0.0094711764834105629] N；Hu=[-0.00018592046920409751, 0.0030338721825181516] N。轴向Hu约占72.5806%，只是总弱力分量比例，不是Hu压力比例或误差分摊。显式P仅入账一次、旧body-x处方驱动力移除，body-y导向与背景重叠去重；Fy导向反力及原global账本保持。

tip11260到原物理raster-body边段的无符号距离由0.0082275225227377291变为0.0086682434292946198 mm。坐标局部放大窗显示约8.67微米的小间距，**变形仍实际×1**；这不是解析圆的有符号接触间隙或新接触门。右480格均核为原非工件介质，实际自由右界随运动响应。当前仅显示右介质几何和全域保存的minJ/maxHu标量，没有读取局部场数组或重新定位极值。

新末态minJ=0.00041660852936145333，max|Hu|=0.31817338324076838 1/mm。很小的J、较大Hu贡献及微小几何距离仍需独立判断；本次不能把P1、ΔP、material或Fy称为纯接触抗拔力、最大容量、摩擦或自由工件释放。independent_HP/effective_grasp/release/HF四资格flags均false，原结果及历史资格保持。

## 可视化与一次检查

[人工检查页](inspection.html)关联全部新媒体：

|图|用途与可见性限制|
|---|---|
|[01实际×1](view/01_actual_geometry.png)|全机构／工件与尖端，密网格和.025 mm小平移在全域比例下有限。|
|[02 P–q及三误差](view/02_P_q_cross_check.png)|两新态对旧0/2原请求，旧.0125只历史点；微小误差靠精确标注及JSON读取。|
|[03力与R/账本](view/03_force_components_and_R.png)|有符号ON-body总/material/Hu、独立R和互斥支撑；Fy远大于Fx，共享尺度下Fx柱较小。|
|[04尖端/右介质/global J-Hu](view/04_tip_right_geometry_global_J_Hu.png)|同图坐标zoom ±.08 mm使小间距可见；inset标题位于彩色网格背景上但可读，未重绘。|
|[05全部收敛](view/05_convergence_and_gates.png)|5个base checks、3个trial及各原门，原旧invalid_J历史与本次0失败分开。|
|[实际态动画](view/actual_force_states.gif)|2次成功grab_frame、2帧，无插值／物理时间含义；帧数依据writer，不重开GIF解码查帧。|

五PNG各一次像素检查通过并保可见性限制，[root QA](execution/root_qa.json)为最终事实。renderer的pending字样保原QA前历史；没有补绘、重试或第二次像素检查。GIF原字节按renderer/封存/发布合同散列复制，不能将“无解码”说成“从未读取新GIF原字节”。

## 资源、读取与封存

science worker含导入／准入／保存实际396.626809秒；科学进程加清理监督398.929825秒，比较监督1.591829秒，viewer监督7.256852秒。helper含QA和一次封存542.904548秒，outer 544.704715秒，均在原4800/4860秒窗；controller3600、science3900、compare60、shared display-QA600保持。四层SUP2 normal_exit/0、同实例全部成员覆盖／ActiveProcesses0／句柄释放通过；top采样峰839888896B约801MiB，是采样值，不是连续峰值或16核实际利用率证明。采样64GiB/四库cap16/CPU、viewer8GiB均未改。

API实际监测3条旧NPZ路径、5次read-capable open事件，均在白名单；opaque model只hash，geometry四mask与selected012两split共6字段来自成功冻结控制流，**不是动态字段hook实测**。独立比较另实际4档8字段，合计7路径、6解码档／14字段；旧fields/force/tangent/matrix缓存不读。viewer只读4份普通JSON，局部科学场读取0；本阶段记录只解析普通输出及原字节身份，无科学补算。

一次封存60成员、14359478B，SHA256=`495b3f05eea588968bfc5c311b231c5c19a0b32e4781642a68feebf345923af6`，在原窗口内完成。见[原包](execution/execution_evidence.zip)、[成员清单](execution/EVIDENCE_MANIFEST.json)、[封存回执](execution/seal_receipt.json)。原高输入父／probe科学包不重复复制或重封。当前闭窗后不再新增F/T、HP、缓存解码、图像或像素检查。

## 使用、恢复与下一步

[USAGE](USAGE.md)已按闭窗实际记录更新功能状态与本次调用，完整结论以本页／result_summary为准。原卡pending标题、授权与冻结的numerical_launched=false、renderer pending均是原准备／执行时点，不覆盖当前实际PASS；actual授权与最终回执另存。

[恢复说明](RECOVERY.md)列新原包、旧父依赖、普通源和路径迁移边界。下一步建议先[准备最小力控保存态续载功能](NEXT_STEPS.md)，让本次非零q/P成功末态可被下一次同定义载荷任务复用；不立即加新P、不重复完整父加载、不把本轮成功当作容量证明。

## 发布与恢复

高输入1.06 mm正式r9力控结果与原始证据提交`f8168842ba2423cf963e3458ea5bed1d47505117`已普通推送并核远端main，`D:/hf-restore-20260930`已普通fetch／ff-only恢复到同提交。两工作树当时干净，82份本轮变化文件逐字节一致，仓库清单与Git索引集合相同；详见[实际回执](PUBLICATION_RESTORE_RECEIPT.json)。这是同机异目录核对，没有异机数值复算。归档回执的后续提交也将普通推送并恢复核对。
