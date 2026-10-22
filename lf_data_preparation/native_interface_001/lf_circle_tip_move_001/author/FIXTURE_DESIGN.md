# L-CTIPMOVE1 小模型静态设计

本文件仅是源代码核查后的 fixture 设计，尚未生成几何、构模、读取 NPZ、调用 HF、评估力/切线、运行求解或测试。以下节点与 DOF 均由既有结构网格编号规则手工推导，不能作为运行通过记录。

## 结论

不能直接复用现存 `test_native_force.small_native` 的掩码与区域：其 16 格中 15 格为 solid，passive_void 全零，`workpiece=None`，不能形成不与实体共节点的合法工件。建议新增独立 fixture，保留 4×4、h=0.5 mm、25 节点/50 DOF 的大小、左支撑与输入区域，使用下述最小 L 形实体与右上介质窗口。不要改变共享旧 fixture，以免把旧兼容证据换成新几何。

## 网格与材料

- 原点 (0,0) mm，范围 [0,2]×[0,2] mm；lower_half，对称面 y=2 mm。
- 格 (i,j)，i,j=0..3；cell id=4j+i。
- 节点 n(i,j)=5j+i，i,j=0..4；坐标 (0.5i,0.5j) mm。
- Q1 局部顺序为 [n(i,j),n(i+1,j),n(i+1,j+1),n(i,j+1)]。
- DOF ux=2n、uy=2n+1；总计 16 单元、25 节点、50 DOF。
- 小模型建议保留现存测试材料：E=1 MPa、nu=.3、plane_strain、t=2 mm、gamma=1e-6、alpha=1e-4、Lr=2 mm。它是接口/约束测试件，不是正式 r9 工件物理参数；不能据此授予真实夹持资格。
- source passive_void 的介质材料不替换；工件仍是运动约束覆盖。

掩码按 C_yx_bottom_up 列出：

| j | solid | passive_void | design | passive_solid |
|---|---|---|---|---|
| 0 | 1 1 1 1 | 0 0 0 0 | 1 1 1 1 | 0 0 0 0 |
| 1 | 1 1 1 1 | 0 0 0 0 | 1 1 1 1 | 0 0 0 0 |
| 2 | 1 0 0 0 | 0 1 1 1 | 1 0 0 0 | 0 0 0 0 |
| 3 | 1 0 0 0 | 0 1 1 1 | 1 0 0 0 | 0 0 0 0 |

solid cells=[0,1,2,3,4,5,6,7,8,12]，passive_void cells=[9,10,11,13,14,15]。每格 design+passive_solid+passive_void=1；solid 与 passive_void 不相交。实体 10 格经共边连成一个 L 形体。

## 工件、支撑与端口

为复用现存构模门，先定义固定工件旧任务：schema 1.1、shape=circle、center=[1.25,2] mm、radius=.375 mm、fixed_components=[0,1]；path 的加载输入可沿用小模型 [0,.0005] mm，input.target_mm=.0005。真实新运动候选必须另有显式运动参数，不把原 fixed_rigid 任务暗改为自由体。

原生单元中心闭圆选择仅取得 cell 14，即 i=2,j=3。其中心 (1.25,1.75) 与圆心距离平方 .0625，小于 r²=.140625；最近水平邻格为 .3125、下邻格 .5625，均大于 r²。不存在恰好落在圆周的选择歧义。cell14 connectivity=[17,18,23,22]；body nodes（升序）=[17,18,22,23]。

| 对象 | 参考节点 | 约束/方向 | DOF 或权重 |
|---|---|---|---|
| support x=0,y=0→.5 | [0,5] | ux=uy=0 | [0,1,10,11] |
| input x=0,y=1→2 | [10,15,20] | 加权平均 ux，个别 ux 不捆绑 | ux [20,30,40]；权 [.25,.5,.25] |
| output x=2,y=0→.5 | [4,9] | 自由 y 观测，spring=0 | uy [9,19]；权 [.5,.5] |
| entity symmetry x=0→2,y=2 | selected [20,21,22,23,24]；solid-attached [20,21] | uy=0 | [41,43] |
| background symmetry 同顶边全段 | [20,21,22,23,24] | uy=0 | [41,43,45,47,49] |
| body | [17,18,22,23] | 同一 ux=q，uy=0 | ux [34,36,44,46]；uy [35,37,45,47] |

body 与 support/input/output **节点集合**两两不相交。全部端口节点均附着原实体，input 的非零 ux 不与任一零约束冲突。背景 uy 与 body 的交集为 [45,47]，应保持一次约束和一次反力记账；不能把交集从背景集合中删去而改变任务。

输出区域必须从旧 fixture 的 x=2,y=.5→1.5 移到 y=0→.5：旧区域含 node19，它在新介质窗不再 solid-incident，会触发既有 port attachment 门。此改动只适用于新的独立 fixture，不覆盖原 fixture。

工件节点 (1,1.5)、(1.5,1.5)、(1,2)、(1.5,2) 的相邻格全部在 6 格 passive_void 中，因此无工件/实体共节点。顶面 body nodes [22,23] 全由背景对称覆盖。解析圆距右界 .375 mm；实际 staircase 工件最右 x=1.5，距右界 .5 mm，右侧 cell15 仍为介质。它不是拟合圆边界模型。

## 小模型约束与刚体模态

现存固定 body 构模集合的合并 union 应为：
[0,1,10,11,34,35,36,37,41,43,44,45,46,47,49]。
共 15 个处方 DOF，35 个非处方 DOF；输入平均约束再配一个乘子，单边 KKT 应为 36×36，而非把全部 body ux 自由释放。

支撑两点 (0,0)/(0,.5) 均锁 ux/uy，在连续全域完整网格且 gamma>0 的前提下，几何整体平移及转动刚体模态被去除；这是静态约束覆盖论证，不保证实际 Jacobian 非奇异。实体 L 形体共边连通。工件给定四个相同 ux=q、四个 uy=0，不具有独立竖移和转角。小模型进入新模式时，仍可保留同一组 fluctuation=0，改由 body ux 的显式 lift=q；要在新接口中允许这一处方平移，不能删除旧控制器的一般 fixed lift 防护。机构输入均值另保持 d_hold=.0005 mm，与 q 参数解耦。

建议新模式验证候选 q=[0,.00025,.0005] mm，首次 q=0 是同一旧固定工件保持态的锚点核查。该候选尺度只用于小模型功能；任何实际测试次数、子阶段、资源窗口以 root 卡为准，本文件不授予运行许可。应让锚点与非零 q 使用同一 body/port/support 定义和同一材料，不通过改刚度制造通过。

## 需由后续实际运行证明

1. 生成几何后 mask/节点/DOF/端口权与本表一致，构模不改变 source arrays。
2. 旧固定工件锚点成功后，新 q=0 模式与其状态/反力保持原门内一致；新 q 不得随之改变 d_hold。
3. 四个 body ux 全等于 q、uy 全零，且 body fluctuation 保持相应处方合同；不可仅核平均。
4. 非零 q 时实际发生刚体平移，支持节点仍零、input 均值不漂移；自由 DOF 平衡、约束、J 等原生产门保持。
5. ON-body=-sum(body internal)；处方 x actuator=+sum(body internal)，不双计 body/background 交集。t=2 已包含在该小模型力，完整对称轴向值仅展示 2×半模型时明确标签。
6. 失败保实际部分结果；不把“未收敛”或“到达 q”叫作释放或承载成功。
7. 后续图须展示实际×1小模型变形、原/新工件位置、d_hold 与 q 两个独立横轴/记录、输入与工件有符号反力、残差和最小 J。当前文本不是数值图。

## 源码依据

本报告依据 HEAD 1e5e9cf76480254a6a288f27fb10bc884acb4c38 的普通 .py 文本：

- hf_repo/tests/test_native_force.py:31–53：原 16 格 fixture 的坐标、材料、掩码与区域。
- hf_repo/src/hf_eval/regions.py:13–26：结构节点/单元编号；63 起：梯形归一端口权。
- hf_repo/src/hf_eval/native_project.py:97–106：现存 fixed_rigid 任务合同；142–185：cell-center 选择、passive_void、实体/端口不相交、背景覆盖；230–231：固定集合合并。
- hf_repo/src/hf_eval/data.py:203–206：mask partition 及 solid/passive_void 合同。
- hf_repo/tests/test_native_mean_mechanical.py:26、36–44：现存 .0005 mm 小模型输入峰值与 cycle_task。
- hf_repo/tests/test_native_mean.py：原 16 格实际测试的有限功能定位；不可把原测试成功挪用为新几何成功。

精确来源 SHA 见同名 JSON。只读设计完成不代表以上待证事项已经通过。