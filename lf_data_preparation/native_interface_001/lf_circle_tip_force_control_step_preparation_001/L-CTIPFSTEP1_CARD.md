# L-CTIPFSTEP1：正式r9非零q小载荷续载候选卡

2026-10-24。**尚未获批或执行。** 本轮只准备，见[PREPARATION](PREPARATION.md)、[TASK_SPEC](TASK_SPEC.md)、[CONTRACT](CONTRACT.json)。获批后先编写最小研究包装，冻结已安装58源/SUP2/包装/普通来源及声明科学路径，独立静审通过再唯一启动；本准备不试跑/导入HF/pytest或新fresh。

## 任务和原门

现有extend_native_guided_force从`D:/hfh1_001/run_001/force/result.json`成功末态accepted1/original1续载。full targets=`[0.0002399800950672949, 0.0002561572865437846, 0.000260201584412907]`，仅算[P1,P2]；候选新output=`D:/hfst1_001/run_001/force`。原非零绝对q=0.025000000126731543 mm、signed R=0.19536542042269825 N、P1/两split继承；mean1.06保持、q2未知。P2按源binary64计算P1+(P1−P0)/4，不由显示截断值生成。

保持α2.5e−7/γ1e−6/r9/(80,40)/right92/Lr80/E1/ν.3/plane strain/t20/h.5、14720单元/29970DOF、全部原成员/端口/支撑/导向及非clock设置、mechanical/chunk256/guided_reduced_tangent。P为含t20的半模型绝对N、显式只入账一次，完整镜像2P/q不加倍；body-y/背景去重和旧body-x处方移除保持，不重mask。

root P0=0.0002399800950672949 N保持，段anchor=P1；SP=max(|P|,|root P0|,2.12e−7)，本正增段实际SP=P。Nmin=1.011074467280606e-06 N/maxdepth4/maxchecks25及其他非clock规则不改；Δ/Nmin=3.9999999999999867，原截止允许两级二分、最多fresh+4叶=5态，不新增强截或改maxdepth。

fresh须checks1及原q/P/R bits、两split字段/state身份保持，不修复/投影。所有接受态保原ρF/ρP≤1e−9、mean界1.0600000000000001e−10 mm、全J正有限/原F-Hu有限性、global≤1e−6、rigid/zero≤8e−11 mm及其余原门。新原目标P2/index2是否到达及segment/full谱系分别核。P2无给q/HP参考，旧P1工程误差只历史，不填新零误差或指定q2。

旧minJ约4.166e−4/Hu轴向72.58%、PROBE invalid_J/回滚/q=.0125内部二分、HIGH1两态零失败均保留，不配伪中间态。原参考/压力/纯接触抗拔/极限/稳定性/释放/整路径HP/HF5资格不升级。

## 读取和实际显示

API只3旧NPZ：fixed model opaque hash、geometry四mask、直接HIGH1 accepted001两split，共2解码档6字段。旧fixed012/probe/fields/force/tangent/matrix/ZIP/媒体不读；无旧包解压或科学复制。新保存NPZ正常raw写/hash另计。普通核对只读协议/新result，viewer四普通JSON上限、无科学场。

数值及普通核对全通过后一次生成5PNG/真实N帧GIF：实际×1变形，绝对P–q，三力/独立R/互斥账本，tip/右介质几何及全域保存J-Hu，全部Newton/trial/二分/原门。坐标zoom/箭头倍率明确，不插值、固定2或17帧或伪画局部场。五新PNG各最多一次像素检查。

## 独立预算、停止和交付

controller1800秒包含在science2100秒内；science进程2085+清理15，含导入/准入/读取/fresh/路径/保存。普通核对60=进程45+清理15。显示/root QA共享600：viewer510+清理15，五图各一次检查须在共享585秒前完成，余15退出。helper3000=2100+60+600+240其他调度/清理/一次封存；outer3060秒（最多51分钟）。采样64GiB、四库cap16、CPU；viewer原8GiB。冻结审清绝对deadline，不能science后再加controller或显示后另开QA。

依据HIGH1科学监督398.9298秒预留；小步不保证更快/成功。唯一启动，首个终端错误停止后续科学/核对/显示，保实际partial；原内部Armijo/有界N二分允许。无外部重试、修复重跑、延期、force、新HP/测试、生产修改/安装、API关联、q回放、删除/回滚或旧科学包复制解压。沿SUP2同实例终止信号+全部成员覆盖+句柄释放；四层清理通过且原窗有余量才一次完整/部分原字节封存，不另开补封窗。

包括实际记录、五图各一次检查、普通main推送及同机异目录恢复。不改原结果/失败/资格；若失败据typed错误/partial决定下一步，不静默改α/步长/原门或加时。

需要另行批准的原因：用户本轮只授权准备；HIGH1/FRESUME1窗口均关闭。本卡新增正式r9非零q平衡、科学读取、实际显示和独立资源额度，不能沿用旧授权。
