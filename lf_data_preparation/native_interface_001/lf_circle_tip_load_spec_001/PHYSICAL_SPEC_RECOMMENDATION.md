# 最小承载物理规格：独立建议（候选，未批准physics）

最近应先实现并验证 **夹持输入保持1.06 mm时，工件沿+x的位移控制刚体牵引小探针**，再考虑力控制承载。这里只准备规格；没有新代码、求解、API调用、测试、绘图、力/差/积分计算或提交。

## 已核参考与边界

现new模型普通元数据确认r9 mm、圆心(80,40) mm、参考域右界92 mm、Lr80 mm、厚度20 mm、h=(0.5,0.5) mm、plane strain、E=1 MPa/nu=0.3、gamma=1e-6及归档alpha=2.5e-7。**alpha=2.5e-7仅是本提案参照候选，不改变默认或生产physics。** 已保存力为计入20 mm厚度的N，不再乘厚度。

工件按“单元中心落入解析圆”选择510单元/565节点，边界是native staircase，不是拟合圆。圆的名义最右89 mm与参考右域92 mm之间3 mm只描述解析布局，**不是可用拔出行程**。本次两descriptor没有实际阶梯xmax标量；不猜89、89.5或其他坐标。非零探针冻结前，须以获准的几何证据绑定实际阶梯最右坐标、右边界/介质约束和buffer。必要的参考几何条件可写为`xmax_staircase + q + buffer < 92`，但这不保证变形后间距或J有效。

x=92是有限分析域边缘，不自动是刚性墙。已知背景对称在y=40、x0..92施加uy约束，不能据“右域界92”虚构右边ux夹紧或无限介质。右侧仅几毫米背景、其实际变形及Hu耦合可能影响反力；不能把有限域支撑当作夹持能力。

## 两种控制方式的取舍

|方式|真正控制/未知|近期价值与问题|
|---|---|---|
|力控承载|外载给定，刚体q未知，需`F_on,x^half(q)+P_full/2=0`|更接近指定外载的保持问题，但脱开后理想自由体受非零载荷无静力平衡；当前非零gamma背景又可能产生残余支撑。失败不是释放证明，收敛也不保证由夹持承担外载。|
|位移控牵引探针|刚体q给定，求机构/介质平衡及所需驱动反力|先消除自由刚体坐标的欠定性，能得到可解释的驱动反力—位移响应；它仍是有导向夹具的运动探针，不能称自由承载极限或释放。|

当前gamma>0使原medium具有非零弹性剪切刚度（源码给Lamé系数乘medium factor）；Hu贡献也保留。由此产生的切向/残余作用不是新实现的Coulomb摩擦，不引入摩擦系数或用“摩擦力”重新命名。material/Hu必须分别保留，不能为了得到理想脱开曲线删项。

## 推荐的首个最小候选任务

- 夹持器输入保持原1.06 mm；原几何/材料/gamma/域不静默改变。候选工件为**一套共同刚体+x平移**：全部原节点ux=q、uy=0，转角0；不重新栅格化工件，不把解锁565节点当作刚体。原工件是原medium单元上的运动约束覆盖，解锁会成为软介质，不是刚体。
- q路径先只考虑`0 → 0.025 mm`这一示意小探针；数值是候选，须在实际阶梯/域buffer明确后再固定和批准，不能据它小于名义3 mm就宣布安全。下一求解卡、资源和验收均尚未授权。
- q=0在新运动/控制合同下须显式重核。原保存峰可作为候选初始猜测，但当前default resume不自动接受新physics，也不迁移原参考资格。新工件坐标必须反映真实`X+q e_x`；旧“reference=actual”的固定工件显示合同不能原样套用。
- 无独立工件外力时，探针所需驱动力遵循`Q_drive^half = -F_on,x^half`，与保持机构输入的原actuator R分开报告。保q=0预载的绝对有符号值，不强制扣成零；同时保material/Hu贡献。若以后另加外载，平衡式必须包括外载和剩余约束反力，不能盲用旧holding反号等式。
- 未来能力验证应核刚体约束/实际pose、1.06输入保持、原平衡/J/约束门及广义反力口径。那只说明探针功能正确，**不是有效夹持、承载极限、自由释放或稳定性通过**。uy/转角约束可以提供支反力，此任务不验证其自由运动。

## 下半与完整装配口径

沿+x平移与y=40镜像相容：`q_upper=q_lower=q_full`，位移不翻倍。若定义完整装配驱动反力，虚功口径为`Q_full=2 Q_half`；若给完整装配外载，半模型取`P_half=P_full/2`。这些是符号约定，没有计算新的全装配力值。上下半Fy相消不意味着没有相向作用；`2|Fy|`也不是已认证的拔出承载力。

最近不做自由竖移/旋转/重力或释放轨迹、Coulomb摩擦、排名、降alpha、改gamma、域扩展或新HP。探针能力和有意义的物理判定建立后，再按实际结果决定力控外载与失稳/脱开处理；不把不收敛当脱开标签。

## 证据

- `docs/WORKPIECE_FORCE_DEFINITION.md`，11837 B，SHA `8a3ffbb984a14e81ea45f746eb479d1358ebb9957a16f6ae29e4af6e7f89a8ec`。
- 归档new `model/model.json`：89774 B，SHA `7f56cf78700c85145cce33a5972f73ac48e05923f16c27e69f7f118e6d239e0b`。selectors为task.workpiece、task.input.target_mm、material、grid、model_extent及region_metadata.workpiece的cell_selection/boundary_representation/kinematics/material_role。
- 同model的`source_geometry/geometry.json`：25085 B，SHA `9630f76972ffecbd60fa42eefb44da0c97c395db7baacaaede33cdabbbc9cf6a`；grid/thickness_mm/model_extent。
- `hf_repo/src/hf_eval/native_project.py` SHA `4f1b4f772938bb870e8784fac881bad9a16f004fabf3b6e91ea9d2701c7601bc`：95–107仅fixed_rigid/[0,1]，142–183下半/栅格规则，244–253非零medium弹性与厚度，270–279原medium上的运动覆盖。

完整仓库相对路径与候选/未定项在同名JSON。本文件不新增报告层或正式阶段文件。
