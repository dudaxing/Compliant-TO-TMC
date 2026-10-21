# L-CTIPGDEF1：厚度与单位的源码／元数据核查

只读准备，未获新执行授权；未import/执行HF、求解、重算节点力、测试、绘图、读NPZ/CSV/gzip/媒体、修改实现或Git。下面是当前源码与两α各自model/geometry共四份普通元数据的证据，不是新的数值验收。

**本次比较的旧α=5e−7与新α=2.5e−7均有20 mm厚度直接实证。两源现有工件弱力／反力单位为N，已计入20 mm厚度；不能再乘20。** task不写thickness不表示未指定：native任务绑定几何，而几何描述符明确保存厚度。

## 当前r9／c(80,40)／right92模型

- 模型：`lf_data_preparation/native_interface_001/lf_circle_tip_alpha_001/run_001/wave_circle_tip_alpha1/model/model.json`，SHA `7f56cf78700c85145cce33a5972f73ac48e05923f16c27e69f7f118e6d239e0b`。`material.thickness_mm=20.0`（187行），`units`明确mm/N/MPa/N mm（164行起）；材料为plane strain，E=1 MPa、nu=.3、alpha=2.5e-7、Lr=80 mm；工件task是固定圆r9、圆心(80,40)，grid extent(92,40)，lower_half。
- 该模型自己的几何快照：`lf_data_preparation/native_interface_001/lf_circle_tip_alpha_001/run_001/wave_circle_tip_alpha1/model/source_geometry/geometry.json`，SHA `9630f76972ffecbd60fa42eefb44da0c97c395db7baacaaede33cdabbbc9cf6a`，34行`thickness_mm=20.0`。其真实文件SHA与model.source_geometry.descriptor_file_sha256相合；task.geometry ID/descriptor SHA亦与此描述符声明相合。未打开同目录geometry.npz或model.npz。
- 补核旧α=5e−7的实际峰来源模型：`lf_data_preparation/native_interface_001/lf_circle_tip_step_010/run_001/wave_circle_tip_step10/model/model.json`，SHA `37b249eef1b01d37b83c58e13793c68d1215fd3e624f8159023e597af8dfea45`（89709 B）；其187行`material.thickness_mm=20.0`、191行kr=0.004307692307692307、193行force_scale_per_length=20。工作件仍为r9／圆心(80,40)，域(92,40)、lower_half、Lr80。
- 旧α模型自己的快照：`lf_data_preparation/native_interface_001/lf_circle_tip_step_010/run_001/wave_circle_tip_step10/model/source_geometry/geometry.json`，SHA `9630f76972ffecbd60fa42eefb44da0c97c395db7baacaaede33cdabbbc9cf6a`（25085 B），34行明确20 mm；实际文件SHA与该旧模型source_geometry绑定相合，task.geometry ID/descriptor声明亦相合。两个模型各自的geometry快照内容SHA相同，因而厚度证据可分别核清；这不是跨α状态或HP资格迁移。未读取旧态/数组/历史。
- task.material只有E/nu/formulation，厚度由geometry authority提供。`data.py:128`要求正thickness_mm，`data.py:218`把它纳入几何权威头；`native_project.py:200`核task.geometry绑定，再于251行读该厚度。缺少task厚度键与缺少模型厚度是两件不同的事。

## 乘入次数：每个材料／Hu积分项各一次

|环节|准确源码位置|作用|
|---|---|---|
|native构模|native_project.py:246、247、249、251–253|lambda/mu取MPa，kr=alpha Lr²(kappa+4mu/3)不含厚度；geometry厚度显式传TMCModel|
|model算子|tmc.py:46、88|类有generic默认1，但本native调用已显式传20；operators(hx,hy,self.thickness)|
|权重|tmc_kernel.py:51–65|grad为1/mm、Hessian为1/mm²；weights=Simpson*(hx*hy*thickness/36)，已是mm³|
|当前NumPy材料力|split_kernel_invariants_hu.py:170–175|P·gradN在173行乘一次已含t的weights，再求和|
|当前NumPy Hu力|split_kernel_invariants_hu.py:176–179|kr*sum(weights*exp(-5J))乘Hu/Hessian作用；weights只乘一次|
|合计与组装|split_kernel_invariants_hu.py:180、358–366|total相加、bincount散布，无再乘厚度|
|public supplied-state入口|native_force.py:56、58、62–69|构模→assemble_split_numpy→分量散布，不额外乘t|
|保存与节点显示|native_mean.py:221–227；workpiece_nodal.py:53、60–73|保存原N数组、选择/反号/求和与原矩，无再乘t或镜像倍增|

当前平衡路径也已追到正确NumPy入口：`native_mean.py:167,194`选择complete／mechanical assembler；complete别名位于`split_numpy_tangent.py:15–16`，mechanical入口位于`split_kernel_invariants_hu.py:327–335`；两者均走同一_response的173／178行。`native_mean.py`从native_force导入的是_npz/_state_hash保存辅助，不是由generic JAX batch_response推断当前结果。

`native_project.py:280`另存force_scale_per_length=E*t（此模型20 N/mm），`split_displacement.py:195`仅将其用于残差归一化floor；192–193及211–219的物理残差／支反力保原N，没有第二次厚度乘法。数值尺度名字不表示输出要再乘一次。

## 量纲推导（仅符号核查，没有数值计算）

- 材料力：P[N/mm²] × gradN[1/mm] × weight[mm³] = N。
- kr=alpha Lr²×模量，单位MPa·mm²=N；Hu[1/mm]，HessianN[1/mm²]。Hu弱力：kr[N] × weight[mm³] × Hu × HessianN = N。
- 材料能量密度MPa乘weight得到N·mm；切线df/du为N/mm。厚度不是P/S应力单位中的第二个因子。

原输出属于20 mm厚度的下半模型，没有自动镜像倍增（native_project.py:270）。未来若刻意报告每单位厚度力，单位应改为N/mm并明确另一步归一化；本轮未做该变换，也不据此增加压力、有效夹持或稳定性资格。

完整路径、逐条源码行、当前文件SHA和元数据原选项见[UNITS_SOURCE_AUDIT.json](UNITS_SOURCE_AUDIT.json)。本次两α厚度结论限于上述各自实际比较来源的四份普通元数据；不证明实际试件厚度，不做全历史/科学保存数组重验；task中未重复写厚度并非物理定义缺失。
