# L-CTIPFREAL1：正式r9导向两载荷力控交叉结果

2026-10-23。**PASS，唯一执行窗口已关闭。** 用户已明确批准本卡。原封保存的[执行卡](approved_card.md)仍保留准备时“尚未获批”字样；这是历史原字节，实际授权见[本轮授权](authorization.json)。本轮从小模型验证推进到14720单元／29970DOF正式r9模型：机构平均输入保持0.50 mm，只给两个正的绝对半模型外载P0→P1，工件刚体轴向q由求解确定。原物理、原验收门及57份生产源码保持。

## 目标、已有能力与本次作用

项目目标是形成独立于LF设计代码的HF第三介质接触分析器，接收LF夹持器几何，计算大变形、接触相关响应、加载／卸载和可追溯的力；以数值核查和实际变形图支持设计比较及后续开发。功能必须逐步落地，数值成功与物理资格分别记录。

此前已完成LF输入准备、多设计前向加载／卸载、保存态延伸、选定态HP80/120参考、保存态接口／图像关联、两α对照和单侧力口径；这些历史范围见[当前状态](../../../docs/CURRENT_STATUS.md)。近期又完成固定机构输入下的规定工件q探针，以及[17项小模型力控验证和两个新模块安装](../lf_circle_tip_force_control_001/RESULTS.md)。

本轮使用LOW1从零[0,.25,.50] mm完整固定父最后峰值index2，给P求q，再与已有给q求P参考交叉，检验正式网格、chunk256切线、未知q/R、来源迁移和外载账本是否一致。**没有把参考q=.025 mm输入力控，也未从probe终态热启动。** 没有重做父加载、probe、HP、测试或修改生产源码。

## 物理任务和实际解

r9 mm、圆心(80,40) mm、right92 mm、Lr80 mm、α=2.5e−7、γ=1e−6、E=1MPa／ν=.3、plane strain、厚20mm、h=.5mm、原510工件单元／565节点及原端口／边界均保持。full29970DOF，free28682，reduced(w,q,R)28684。导向限制工件uy=0、转角0；q为有符号未知量，未裁剪到预期答案。

|原请求|给定P_half／N|求得q／mm|机构R_input／N|Newton base checks|
|---|---:|---:|---:|---:|
|P0非零预载|3.686421133658022e−5|0|0.08589635225389337|1|
|P1|4.3272306948756724e−5|0.024999999999923774|0.08589811003453524|3|

2个请求、2个接受态，无内部二分、无失败尝试；1次solver、6次F／4次T均完成，2次line-search trial。P0由原合法父q0的预载确定，本次fresh检查1即原样通过，两split与signed R逐位保持。P1是绝对载荷，ΔP不是P1，N最小二分步长4.0050597576103156e−7与旧mm步长分别保留。

## 原门及参考交叉

|适用生产门|两态最不利实际值|原界|
|---|---:|---:|
|free ρF|1.3004823600170763e−12|≤1e−9|
|独立body ρP|9.395750847384523e−16|≤1e−9|
|mean绝对残差|6.938893903907228e−18 mm|≤5e−11 mm|
|relative global balance|6.034159322635907e−16|≤1e−6|
|最小J|0.5154001178738727|>0|
|rigid／zero误差|0 mm|≤8e−11 mm|

P1的g=Q_half−P_half=−4.0657581468206416e−20 N，SP=4.3272306948756724e−5 N，|g|界4.327230694875673e−14 N。free与body力尺度独立，没有替换生产门。

|P1对原规定q=.025终点|实际绝对差|启动前冻结工程界|结果|
|---|---:|---:|---|
|q|7.622721898137286e−14 mm|1e−6 mm|PASS|
|全29970DOF物理位移max差|7.676498325892567e−14 mm|1e−6 mm|PASS|
|R_input|1.3877787807814457e−17 N|8.589811003453524e−9 N|PASS|

全场比较逐DOF对四个binary64 split项用fsum求差，未用显示坐标相减；最大差DOF25082。fresh锚点身份与端点工程误差分开验收；没有因实际差很小而收紧未来门。详细原值／身份／门见[comparison](comparison.json)，轻量全记录见[result_summary](result_summary.json)。这不是严格误差界、唯一稳定分支或全路径独立参考证明。

## 从力与几何能判断什么

P是固定空间+x的**半模型合外载N，已含20mm厚度**，不再乘厚度。Q_half=sum_body f_int,x，ON-body Fx=−Q_half。镜像完整装配轴向外载可记2P_half，q不倍增；R_input是机构平均端口有符号乘子，不能当工件外载。

P1的ON-body力(N)：total=[−4.3272306948756683e−5, +3.711449563209588e−4]，material=[−5.934019104250851e−6, +1.0249499809837568e−4]，Hu=[−3.733828784450584e−5, +2.6864995822258313e−4]。轴向Hu约占total的86.2868%；这是总弱力分量的描述，不是压力比例。显式P仅入账一次，旧body-x处方驱动力不再计入；body-y导向与background重叠去重，原global账本保持，分组末位重求和差仅描述。

实际×1几何的tip-node到原阶梯工件边段**无符号距离**从0.5190339177997849变为0.5190421063444752 mm。它不是解析圆的有符号接触间隙或新接触门。右侧固定480格均核为原非工件介质，未重选成员；本轮未读局部J/Hu场，图中只画既存全域极值标量和真实几何。

因此，本次证明正式模型的导向总力控制及同定义位移↔力闭环。较大间距与Hu占主导，仍不能把P1或ΔP称为纯接触抗拔力、最大承载力。独立HP／有效夹持／释放／HF资格flags仍false；压力、摩擦、自由工件y／转动、承载极限及稳定性尚未建立。独立[结果物理复核](author/RESULTS_PHYSICS_REVIEW.md)保留这些限制。

## 实际可视化与人工检查

[人工总览页](inspection.html)包含5PNG及2帧实际GIF，便于逐图检查：

|图|内容与观察边界|
|---|---|
|[01](view/01_actual_geometry.png)|原网格实际×1变形、工件运动；小q和密网格在全图中不显著。|
|[02](view/02_P_q_cross_check.png)|P–q与给q参考重合，三项误差和冻结界；精确值依标注／JSON。|
|[03](view/03_force_components_and_R.png)|有符号ON-body total／material／Hu、单列R和去重外载账本。|
|[04](view/04_tip_right_geometry_global_J_Hu.png)|尖端近景、右侧介质实际几何、unsigned距离和全域minJ／maxHu。距离曲线自动使用数值offset，图例给直接末值。|
|[05](view/05_convergence_and_gates.png)|全部4个Newton base checks、2个trial及独立残差／mean／global／刚体门。|
|[GIF](view/actual_force_states.gif)|每个实际接受态一帧，共2帧；无插值，不代表物理时间。|

五张PNG各一次像素检查均通过，见[实际root QA](execution/root_qa.json)；未修图重跑。GIF只按writer两次grab_frame记帧，未二次解码检查。原renderer的pending字符串是QA前历史状态，最终QA和helper已PASS。

## 范围、资源与记录完整性

唯一启动从2026-10-23 09:50 UTC附近开始。worker实际311.2029秒（含导入、准入、保存；监督含创建清理313.5384秒），比较监督2.8655秒，viewer监督5.9841秒；显示及root QA共享阶段80.1646秒。helper397.9866秒，outer含一次封存398.6823秒，均在原2700／2760秒窗口。controller1800、science1900、comparison60、display共享600保持；采样64GiB／四库线程cap16／CPU，viewer8GiB。top采样进程树峰843264000B，约804MiB；是采样值，不是连续峰值或16核实际利用率证明。

top／science／comparison／viewer四份SUP2均normal_exit／0；同实例终止信号、全部成员覆盖、ActiveProcesses=0及句柄释放证明均通过。0外部重试、0修复重跑、0新HP、0测试、0生产修改／安装，窗口关闭后没有科学补算或再次绘图。

API实际只读3条旧NPZ路径、5次open事件；opaque model只核整档身份，geometry四mask和父selected split两字段的**6字段计数来自成功冻结控制流，并非动态字段hook实测**。比较另实际读4个state档／8字段；合计7路径、6解码档／14字段，旧力／切线／矩阵缓存未读。viewer只读4份普通JSON；后续记录仅读普通元数据和原字节，不解码科学缓存。详见[science receipt](execution/run_001/science_receipt.json)及[协议](protocol.json)。

一次原始封存59成员、13984762B，SHA256=`7452459bd88751087bdc0040754226eafedae3d42159fd3f1273b5d21cc81158`，见[已封原包](execution/execution_evidence.zip)、[逐成员清单](execution/EVIDENCE_MANIFEST.json)、[seal回执](execution/seal_receipt.json)。封存在原窗口完成，发布只复制原包原字节；没有窗口外补封科学档。

## 使用、恢复与下一步

现有固定／probe／force三种接口和本次原调用见[USAGE](USAGE.md)。force结果为独立schema，尚不支持其保存态续算／卸载或旧native_response自动关联。恢复所需资料、父依赖和路径迁移限制见[RECOVERY](RECOVERY.md)，逐文件发布身份见[DELIVERY_MANIFEST](DELIVERY_MANIFEST.json)。预启动false计数和旧路径原封保留，当前PASS以实际回执为准。

下一步先[准备高输入1.06 mm的同定义两载荷交叉](NEXT_STEPS.md)，优先检查功能能否进入已有较强夹持工况。它的旧probe曾直接大步invalid_J后内部二分，终点minJ约4.17e−4；不能以这次低输入311秒外推保证，也不能现在追加计算。当前只完成本卡，不把项目整体目标标成完成。
