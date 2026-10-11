# M-ALPHA1：同任务 alpha 单因素加载及一次回撤候选

2026-10-11。准备基线 main `5af8b5e`。本卡是待明确批准的候选，未构建新模型、执行求解、读取新的 NPZ 字段或产生新图。M-BOUND1 已执行通过并闭卡，其资源窗口不续用。

## 目标及选择依据

整体目标是独立 HF 有限变形／TMC 前向评价：从 LF 普通几何得到结构实际变形、输入反力和有明确含义的工件作用，逐步用于同任务候选比较及 HF5。已有完整力、组装、切线、求解、CLI／API／batch、固定方体循环、实际显示和原24态48HP参考，本次复用这些功能。

同任务 h1／h0.5 已提供网格敏感性。旧 gamma 单因素实验使用 h1、80×40mm域、零右侧余量，当前是 h0.5、84×40mm、4mm余量；旧软化实验同时改 E、gamma、alpha。因此当前任务尚缺独立 alpha 敏感性证据。M-BOUND1 的侧边局部相消和角点整体来源也说明不能仅凭 Hu 整体小就忽略其局部作用。

本卡只改变 **alpha：1e−6 → 5e−7**。gamma仍1e−6、Lr仍80mm；E1MPa、nu0.3、plane strain、厚20mm、84×40mm域、原h0.5嵌套几何、固定 side18 方体 center(71,40)、支撑、背景对称、2mm平均端口、零输出／输入辅助弹簧不变。kr由原 `native_project` 公式随alpha改变；介质Lamé参数不变，不改Hu核、不缩放旧响应来代替重新平衡。

两点只给参数敏感性，不设“输出相差多少即稳定”的新阈值，不授予网格／参数收敛、压力或有效夹持资格。原48HP属于原alpha任务，不移给新态。

## 原目标前缀及最近功能增量

从真实零起点执行原循环前15目标：

```text
[0, .25, .5, .65, .75, .8, .85, .9, .95, 1, 1.05, 1.1, 1.15, 1.2, 1.15] mm
```

14个起点／加载目标到1.20mm，随后只回撤一次到1.15mm。这段与旧基线相同前缀比较；不重做其余完整卸载，不宣称恢复到零或全路径稳定。

保持原 `ordered_cycle` 是具体接口取舍：原纯 `load_only` 保存记录缺少现有viewer要求的leg／original_target_index；原循环前缀能直接复用求解器及显示器，不需要修改或伪造原保存身份。原控制器可恢复拒绝试探、Armijo回溯及二分仍按原算法运行，接受的额外二分态完整保留。单例batch仅含新alpha任务；旧基线由普通已存JSON／CSV匹配，不放宽batch同任务合同，不新增基线求解或观察。

## 一次窗口中的步骤和输出

1. 核原输入和源码字节绑定、task只有声明差异、控制设置、独占新输出及实际批准记录；构模后、首次力计算前核实际材料与区域元数据，alpha和kr按声明变化，其它材料与边界／端口保持。
2. 一次原batch／API构模及求解，机械模式 `mechanical`、切线 `chunk256`、初猜 `port_projection`。记录原接受回调和真实F／T调用；缓存writer／summary不得新增F／T。
3. 保留新model、全部接受态state／forces／tangent／CSC、result、response、batch index、progress及执行回执。原15目标各有一个正确原目标态，允许原控制器二分态；保持真实失败或未完成，不修复重跑。
4. 生产成功后，另起一个纯显示子进程，复用原保存态viewer字节。对新任务全部实际接受态进行原几何／节点力观察，生成实际比例、镜像及total／material／Hu节点作用的动画、原三张PNG和原观察表。镜像仅显示上半，不求解上半。viewer无新力核、切线、HP或平衡求解。
5. 用原目标索引、分支、d及state身份匹配15个共同原目标；基线仅复用旧CSV／summary。输出14指标的原值及candidate−baseline表、新六量对照图，因此共四张PNG。新二分态保留在raw显示，不插值进原目标对照。
6. 核实际终态、原门及源码／输入保持，独立审阅实际结果与图件后记录下一步。窗口结束即关闭；观察或绘图失败也停止，不复用旧窗口重画。

公共力报告继续区分半工件有符号total／material／Hu ON-body、反向保持反力、镜像净力和双侧法向幅值和；后者不是有效夹持力。曲线同时显示输入反力、平均输出位移、有限钳尖到底面无符号距离、介质积分点minJ及最大Hu分量。图中原 free-medium 范围为非solid且排除workpiece的单元，不是按自由DOF邻接筛选。间隙、射线与node-window不同；Hu范数、最大分量与J单元均值不同，不以图色标替代真实极值。

## 生产门与资源

保留原生产停止门：relative residual≤1e−9、平均约束使用原1e−10 tolerance和native scaled bound、relative global force balance≤1e−6、fixed split和≤8e−11mm、所有接受态积分点J>0。其余原设置保持：displacement floor1e−6、force floor factor1e−8、max checks25、Armijo1e−4、max backtracks12、max bisections4、minimum increment0.00625mm。局部相消或输出接近不是新的物理门。

申请唯一 **controller9000秒／helper9600秒／outer9660秒，采样8GiB** 窗口，约2小时41分钟。helper覆盖导入、求解、缓存持久化、纯显示子进程、比较、最终字节核对及终态；viewer子上限取600秒与helper剩余时间的较小值，不另加窗口。outer同样包括子进程树和最终退出。协作检查和采样RSS不等于硬时间／OS内存上限，不force结束同步计算；原计算返回检查点才确认越限。

预算依据为旧同任务h0.5实际接受累计：origin81.40964069997426秒、0.85mm2030.5818528999807秒、峰值1.2mm5721.272085799952秒、一次回撤1.15mm6150.855067699915秒。原完整24态viewer实际39.698867秒。以上是原快照，不是新alpha成本预测或成功保证；新alpha可能改变条件性与迭代。controller留出的helper余量同时服务保存、显示及终态，不能延期。

一次启动。终端异常、路径未完成、资源越限、身份／原门失败或图件失败立即NOT_PASS，保存已有记录；无包装重试、修复重跑、延期、force、新HP／JIT／LF优化。控制器原可恢复试探不算包装重跑，原失败试探如实保留。

## 具体候选命令与成功含义

在真实仓库根用独立HF Python，仅在本卡获明确批准后执行：

```text
<HF-python> -X utf8 -B lf_data_preparation/native_interface_001/regularization_sensitivity_001/launch_alpha.py production --protocol lf_data_preparation/native_interface_001/regularization_sensitivity_001/protocol.json
```

PASS表示这条新alpha前缀任务的生产门、保存来源及显示／匹配完成。它不表示物理稳定／收敛、有效夹持、连续总压力、自由体／摩擦、全列切线或HF5。原24态／48HP资格和科学版本保持；新alpha结果未取得自己的HP参考。按新实际有符号力、间隙、局部场及变形再决定需要更小alpha、更细网格或另一个因素，不同时改参数与网格，不预定下一卡。

需要本卡的新明确批准，因为这次新增非线性路径、纯保存态观察／绘图和上述资源窗口；已闭合的M-BOUND1只覆盖两态Hu来源诊断。先完成候选及独立静审、发布和恢复核对，再申请此具体范围。
