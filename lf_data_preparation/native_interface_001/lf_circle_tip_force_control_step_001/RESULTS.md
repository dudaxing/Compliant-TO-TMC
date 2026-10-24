# L-CTIPFSTEP1：正式r9非零q保存态小载荷续载结果

2026-10-24。**PASS，唯一科学窗口已关闭。** 从成功HIGH1非零q/P/R末态按原门完成P1→P2；2接受态、6F/4T全部完成、0新失败/二分。五PNG各一次检查、2帧实际动画、四层normal_exit/0及完整清理、一次原字节封存通过。58生产源码保持，没有新HP/测试/外部重试/安装。

独立实际结果/物理功能复核12项通过，见[复核报告](author/RESULTS_PHYSICS_REVIEW.md)；该复核仅核普通材料，不重复科学或图像检查。

## 目标、进度及本轮作用

整体目标是独立HF读取LF设计，分析TMC大变形夹持器的实际变形、输入反力、工件作用及加载/卸载，逐步形成可审查的设计比较、优化和导向承载功能。此前已有多设计/圆矩工件、完整输入回程、选定态参考、α对照、给q探针和正式低/高输入两载荷力控；[FRESUME1](../lf_circle_tip_force_control_resume_001/RESULTS.md)又通过12项小模型验证并安装非零q续载入口。

本轮用正式14720单元模型验证该入口真正接续一个已移动工件，保持机构输入1.06 mm，给新P后独立求q/R。实际效果是可复用成功力控末态渐进加载，无需把q归零或重复旧P0→P1。单次局部平衡通过仍保原物理/参考资格边界；本轮没有判定极限容量或自由释放。

## 来源、保持条件与实际解

直接父`D:/hfh1_001/run_001/force/result.json`，选择accepted1/global original1；原state SHA`352103915d1f03e02da4b49de5426ddb3daf9438f0e7d25ed37c9876aaa0984c`。原fixed树`D:/hpr1_001/parent_001`只供原模型/物理，未读取其q0 split重放祖先。完整source列表[P0,P1,P2]保留，本次仅[P1,P2]，global offset1、原目标1/2、段内0/1。

保持mean1.06 mm、α2.5e−7/γ1e−6、r9/(80,40) mm、right92/Lr80 mm、E1 MPa/ν.3/plane strain/t20/h.5、14720单元/29970DOF、原510工件格/565节点、全部端口/支撑/导向。工件uy/转角0，仅绝对x平移q未知；成员不重mask。mechanical/chunk256/guided_reduced_tangent、所有非clock设置/Nmin保持，新clock1800秒。

|实际接受态|global原目标|P half N|求得绝对q mm|输入R N|Newton checks|
|---|---:|---:|---:|---:|---:|
|0 fresh|1|0.0002561572865437846|0.025000000126731543|0.19536542042269825|1|
|1 新末态|2|0.000260201584412907|0.03123384806234602|0.1954005432102683|3|

根P0=0.0002399800950672949 N保持；新增ΔP=4.044297869122411e-06 N，q增加0.0062338479356144755 mm，R增加3.512278757006326e-05 N。q2没有作为目标、初值、夹限或预测答案传入。fresh原q/P/R binary64、两split字段SHA和state hash保持，检查1原样通过，没有锚点修正。

原Nmin=1.011074467280606e−6 N、max_bisections4、max_checks25和旧mm最小步.00625保持；本次实际0二分，并不把派生最多5态写成已计算5态。原SP=max(|P|,|root P0|,Ffloor)，此正增段实际SP=P；root字段被硬核保持，数值主导证据仍沿已通过负P小模型，不由此例单独推断根/段尺度行为。

## 原门与收敛的实际效果

|项|两接受态最不利实际值|原界|
|---|---:|---|
|ρF|1.2233918339341764e-12|≤1e−9|
|ρP|5.656400795828763e-13|≤1e−9|
|mean绝对残差 mm|0|≤1.0600000000000001e−10|
|global relative|1.7018691195477797e-14|≤1e−6|
|rigid/zero mm|0|≤8e−11|
|接受态minJ|0.000406181815315325|有限且>0|

P2的g=Q−P=1.4718044491490723e-16 N，原界2.60201584412907e-13 N。全部4个Newton base checks和2个trial保留；P2用3个base checks、两次factor=1的Armijo trial收敛，无新failed_attempts。预测基态minJ约.0004060221也正；它是中间检查，不冒充保存接受态极值。原controller检查J/F/Hu的有限性，闭窗后没有额外解码场数组复核。

新P2没有给q或独立HP参考，q/fullDOF/R参考误差均为not_available/null。原P1与给q参考的工程界和微小误差只保历史，未套给新P2，未填0或升级独立参考资格。数值success、普通继承核对、显示、清理和封存分别记录，见[完整普通结果](force_result.json)、[普通核对](continuation_check.json)、[轻状态表](status_table.json)、[闭卡汇总](result_summary.json)。

## 力、结构及介质响应

P为有符号绝对半模型合外载N，已含20mm厚度；完整镜像轴向2P2=0.000520403168825814 N，q不倍增。Q=Σbody f_int,x，ON-body Fx=−Q；输入R是独立mean乘子。显式P只入账一次，旧body-x处方驱动力移除，body-y导向/背景重叠去重。

|P2单侧ON-body弱力 N|Fx|Fy|
|---|---:|---:|
|total|-0.0002602015844130542|0.012537665631271991|
|material|-7.099887164487156e-05|0.00950888135479409|
|Hu|-0.00018920271276818263|0.003028784276477901|

轴向Hu占total约72.713897%，单侧Fy与body-y导向反力反号；这些是总/material/Hu弱力贡献，不能当作压力、纯接触抗拔力或承载极限。外载账本末态余额=[3.0574501264091225e-17, -8.462440260611836e-15] N，独立R、显式P、导向和其余零位支撑按互斥口径保持。

minJ由0.00041660852936145333降至0.000406181815315325（下降约2.5028%）；max|Hu|由0.3181733832407684增至0.31998793705692913 /mm。tip11260到原物理栅格工件边段的无符号距离由0.00866824342929462到0.008777299023513763 mm，略有增加；新q平衡成功不等于尖端更贴合。右480格原非工件介质核对通过，实际自由右界形变可见。

这些J/Hu是全域已保存标量，不是新局部场定位；raster无符号距离不是解析圆有符号间隙或接触门。较小J、较大Hu贡献和旧微小距离持续存在，independent_HP/effective_grasp/release/HF四flag仍false。

## 实际图与人工检查

[人工检查页](inspection.html)集中展示五图、实际两帧动画和原值表：

- [01实际×1变形](view/01_actual_geometry.png)：全机构与工件/尖端；很小新增位移在全域比例下近乎重合。
- [02 P–q续载](view/02_P_q_continuation.png)：红色为本次P1/P2，旧HIGH1淡色背景及PROBE中间点均为历史，未作为新参考或动画态。
- [03三力/独立R/账本](view/03_force_components_and_R.png)：Fx比Fy小，共享柱形尺度下Fx较短，精确值在普通JSON。
- [04尖端/右介质/J-Hu](view/04_tip_right_geometry_global_J_Hu.png)：坐标zoom仍是实际×1；inset标题/标签覆盖彩色栅格，较密但可读，无重绘。
- [05全部收敛](view/05_convergence_and_gates.png)：4 base/2 trial及原门，零仅按明示绘图地板显示；rigid零点/图例靠近柱上限但标注可分。

[实际动画](view/actual_force_states.gif)只含本段2次成功grab_frame，无插值/物理时间含义，不解码复核帧数。五PNG各一次检查于共享显示+66.2818秒完成，通过并保可见性限制；[root QA](execution/root_qa.json)为最终事实。renderer pending与protocol numerical_launched=false保QA前/冻结时点，不覆盖实际闭卡PASS。

## 资源、读取与封存

science worker 362.421993秒，含监督清理science362.818736秒，普通核对监督.310298秒，viewer监督5.594993秒；helper含QA/封存430.587526秒，outer430.848600秒（约7分11秒），在原3000/3060秒内。四层normal_exit/0、同实例全部成员/终止/句柄释放及ActiveProcesses0证明通过。top采样峰873754624 B约833MiB，属于树RSS采样，不是硬峰值或16核实际利用率证明；64GiB/四库cap16/CPU及viewer8GiB合同保持。

实际API观察到3条旧NPZ路径/5次read-capable opens；opaque model只核身份，geometry四mask与直接force两个split共2解码档/6字段来自已冻结成功控制流，并非动态字段hook实测。新输出仅4个NPZ write事件，无新输出read事件；保存时新增F/T0。普通checker只读protocol与新result，viewer只4普通JSON，无科学场或旧媒体读取。

一次封存55成员、14380965 B，SHA `2a3b8cbac13d578a1dd526c680a4db788cd1200a1ebfbdc7f6467d8a6d120881`。[原包](execution/execution_evidence.zip)、[成员清单](execution/EVIDENCE_MANIFEST.json)、[封存回执](execution/seal_receipt.json)保原字节；旧fixed/HIGH1科学包不复制重封。闭窗后的记录/复核/发布只读普通材料或交付原字节，不新增科学解码、F/T/HP、测试、绘图或第二像素检查。

## 后续

当前正式非零q续载已取得一个新载荷的功能证据。建议先准备新P2保存态的独立参考核对，明确q/R混合平衡的参考口径，再决定下一小增量；当前不自动开启新求解或HP。详见[USAGE](USAGE.md)、[NEXT_STEPS](NEXT_STEPS.md)、[RECOVERY](RECOVERY.md)。

## 发布与恢复

正式r9非零q保存态小载荷续载实际结果、状态记录及已生成媒体提交`08806e9aac4bf8b60bbb606b544dea4901925c4c`已普通推送并核远端main，`D:/hf-restore-20260930`已普通fetch／ff-only恢复到同提交。两工作树当时干净，69份本轮变化文件逐字节一致，仓库清单与Git索引集合相同；详见[实际回执](PUBLICATION_RESTORE_RECEIPT.json)。这是同机异目录的交付字节核对，没有异机环境验证或数值复算；本卡只记录实际局部续载及已生成证据；没有新HP、测试或生产源码修改，也不授压力、纯接触承载、稳定性或释放资格。归档回执的后续提交也将普通推送并恢复核对。
