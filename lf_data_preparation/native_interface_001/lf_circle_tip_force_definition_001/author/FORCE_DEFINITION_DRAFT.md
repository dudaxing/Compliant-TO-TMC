# 单侧工件作用力：报告规则草案

本文件是只读准备产生的可审阅草案，尚未作为正式报告规则整合到仓库。它解释现有字段，不改变力核、物理任务、原数据或验收门。

整体目标是让外部研究层在同一HF任务下比较LF几何的非线性与TMC响应。目前独立输入、力与切线、平衡求解、保存态续算、两α周期及研究层读取入口已实现。本步补齐这些力数值的物理用法。

## 对象、单位与厚度

当前比较对象是固定圆形工件的下半模型：r=9 mm、圆心(80,40) mm、右域界92 mm、正则化长度80 mm，α分别为5e−7与2.5e−7。工件两方向自由度均固定。这是当前已计算任务的说明，不是自由工件承载试验。

厚度来自geometry的`thickness_mm`，不是由task中是否重复填写决定。当前保存几何与model材料元数据均明确为20 mm；`native_project.py:251`把geometry厚度传入TMCModel，`tmc.py:88`传给operators，`tmc_kernel.py:65`的weights含面积与厚度。当前NumPy力入口使用这些weights；完整证据链见配套UNITS_SOURCE_AUDIT。

因此，现有`*_N`是已经积分原模型厚度的N，不能再乘20，也不能未经定义就称N/mm。积分前的应力字段MPa与已积分节点弱力N是不同对象。通用规则是遵循各自geometry/model实际厚度，本例20 mm不能替代其他模型的元数据。数值单位明确不等于已证明实物承载能力。

## 有符号的单侧报告量

原坐标+x向右、+y向上。对全部工件节点集合B及每个分量p，代码保存的是：

`f_on_body[p, node] = -global_internal_force[p, node]`

下半工件向量是这些原节点弱力的原合力；这里不重新求和、不重分类节点。竖直操作量直接读取该合力的y分量，保留正负号。正值表示模型对下半工件沿+y的作用，负值保留其原方向；不以绝对值、截零或筛小力代替原值。

建议中文名称为“下半固定工件竖直作用力（有符号，N）”，并同时报告Fx、α、source/leg/d/state SHA。当前圆形边界的局部法向沿边变化，因此竖直合力不应称作某处局部法向压力。

`native_mean.py:100`的既有`normal_force_on_lower_body_N`实际赋值为total Fy。它是既有字段名，解释时明确其竖直合力含义，不改旧字段或历史结果。研究周期中的`total_body_Fy_N`是相同对象的报告字段。

## total、material与Hu

原键名是`total`、`material`、`regularization`；本文以Hu描述最后一项的来源，不重命名原键。它们来自同一离散弱式及原组装顺序。total与分量关系按原计算表达解释，浮点重组尾差沿用已有记录，不新增逐位相等门或再算差值。

material项与Hu项分别报告；total接近不能单独证明两项或α已经独立。Hu项是该TMC离散系统的一部分，不能静默删除，也不能将material独自当成已验证的真实夹持力。

原`holding_reaction_on_model_N`是保持固定工件的总支撑反力；在本任务没有工件外加端口力的条件下，它与ON-body总量反向。分量取负只是代数分解，不是新增的独立反力测量。

## 镜像与节点分组

当前y=40 mm对称任务中，现有代码把下半量(Fx,Fy)镜像为上半(Fx,−Fy)，并另存完整工件合力(2Fx,0)。这些是对称推导的报告量，不是另做一次上半求解。原`two_sided_normal_magnitude_sum_N=2*abs(Fy)`也是已有派生字段，不能改称完整装配的全局合力，也不自动成为合格夹持力。

上述镜像、完整合力和幅值和是producer源码中的既有定义；它们没有出现在当前两份comparison的rich对象中，因此本研究入口没有这些可直接读取的selector。本卡只解释其含义，不补算这些数值。

原节点四类掩码为physical_only、cut_only、physical_and_cut、interior。两峰原计数均为71、35、2、457。四类构成节点分区；physical和cut边集合在角点相交是另一概念。交点节点弱力不能任意分到某一入射边。正式竖直作用量沿用全部原工件节点合力，不只挑physical_only，不丢弃交点或小项。

节点弱力含支撑关联范围和高阶项信息，不能通过除一个任意节点面积就得到连续面压力。已有几何距离也保持原定义，不由很小距离或力阈值宣告接触/有效夹持通过。

## 直接使用已有函数返回值

以下是字段用法说明，不是本轮的再次API执行。`view`表示已经由现有`load_saved_study_report`返回的四分区对象，`role`为baseline或new：

|需要的原数据|现有位置|
|---|---|
|完整周期与角色|`view['cycles'][role]['timeline_rows']`|
|周期竖直分量|每行`total_body_Fy_N`、`material_body_Fy_N`、`regularization_body_Fy_N`|
|周期水平分量|每行对应的`*_body_Fx_N`|
|已有20对260项差|`view['scalar_comparison']['pairs']`|
|两峰原对象|`view['peak_node_comparison']['sources'][role]`|
|峰节点原三力、坐标与mask|上述source的`original.nodal`|
|峰原三力合力与总holding|上述source的`original.nodal.summary`|
|已有565对3390项差|`view['peak_node_comparison']['node_pairs']`|

精确JSON键、源码位置与分组解释见配套FORCE_FIELD_MAP。来源α、accepted/global序号、原leg及state SHA分别保留；不按相同d合并加载/卸载或转移参考覆盖。

现有人工总览集中链接两周期、标量和峰节点力图；原页还提供实际变形动画入口。本规则不新绘、不重读媒体，不把示意箭头当作重构的完整机构变形。

## 完成边界

本规则解决单位、对象、方向、符号、镜像、分量和字段取用的可重复性。它不新增科学通过记录，不授压力、有效夹持、自由释放、稳定性、α独立、网格/域收敛或完整路径参考资格。

下一物理问题是明确工件允许怎样运动、承受何种外载及何种结果算成功，再单独制定最小验证任务。固定工件的反力和输入回到零尚不能替代该任务。
