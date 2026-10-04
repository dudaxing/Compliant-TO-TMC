# Cycle009 工件节点力：只读输入与最小输出方案

本次只读核对正式仓库的源码、保存 JSON/NPZ 描述与既有 HP 字符串；未调用 F/T、HP、求解、几何测量或绘图，未修改正式文件。当前实例是已完成九态、18 次新 HP 对比的 cycle009；本说明不是新的节点力消费验收结果。

正式根目录为 `D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC`，输入根为 `lf_data_preparation/native_workpiece_001/coarse_square_cycle_009`。

## 已存字段与符号

`model/model.npz` 保留 27 项，3321 节点、6642 DOF、3200 Q1 单元。`connectivity` 的顺序为 BL/BR/TR/TL；`edofs=(2*connectivity[...,None]+[0,1]).reshape(ne,8)`，每个节点按 ux、uy 交错。`solid` 仍是原机构分类；工件由独立 `workpiece_cells/nodes/dofs` 约束覆盖表达，不是新增材料相。

每态 `forces.npz` 的 16 项为三张 `(3200,8)` 元素力、三条 `(6642,)` 全局内部力、J/Hu/F/两个应力字段，以及 input_force、support_reaction、spring_force_on_structure、force_residual、global_force_balance。机械模式明确没有 material_energy。

全局 total/material/regularization 内部力分别是相应元素弱式残量按 edofs 散射求和；生产用 `np.bincount`。保存的全局字段已经可直接消费，无需再次散射或调用本构。代码位置为 `split_kernel_invariants_hu.py:366`、`split_displacement.py:192`、`native_mean.py:183`。

若 `i=2*node+c`，工件节点受到的模型/介质离散力定义为 `f_body[i]=-global_*_force[i]`。保持约束作用于模型的力为 `support_reaction[i]`。一般残量 `internal+spring-actuator`；本实例工件不与输入/输出端口共享节点，k_out=0，因此工件上的保持反力就是内部力，二者逐节点符号相反。不能把整个模型的内部力图直接标成外部接触力图。

工件所有 306 DOF 的负全局力投影，正是现有 `force_on_lower_body_N` 的三个 signed XY 合力；`math.fsum` 用于保存合力。17 个背景 uy 重叠 DOF 由工件优先拥有，合并 fixed376 不重复计数。镜像上半受力为 `[Fx,-Fy]`，整物体合力为 `[2Fx,0]`，`2abs(Fy)` 是两侧法向分量幅值之和，不是整物体净 y 力，也不是压力。

## 原 HP 直接可核对的内容

每态 `reference/accepted_NNN/hp80_hp120_full_global.json.gz` 已保存两精度各 6642 项的 `internal_decimal/material_internal_decimal/regularization_internal_decimal`。后续节点力入口可以只读取这些字符串、按同一节点 DOF 选择并取负号；不需要新 HP 或元素力重算。

每态 `equation_hp80_hp120.json.gz` 的 independent_equations 两精度中另有 actuator、spring、support、residual 全量向量。`workpiece_checks.json.gz` 已保存三分量 signed_body_reference_N、holding_partition_dofs、holding_partition_reference_N、overlap_reference_N 和原门检查。已有 body 合力、保持约束分组与镜像量能直接对账。新边界节点子集/逐节点 CSV 尚未被独立保存验收；不得将其未来消费结果冒称已通过。

已有 HP 资格覆盖该保存全局力向量及全部元素，不能静默新增以接近零节点力作分母的相对门。最小新验收是保持原尺度/原门，保留全 DOF 与工件子集的原值和 HP80/120 字符串，核对节点投影与现有 body 合力/反力分组一致；HP 调用数为零并明确继承来源。也不重新评价应力、能量或压力。

实际初态 index0 的 body 三分量都为零。峰 index4 的总力为 `[-0.0007910899872955321,0.0037892857813192618] N`，材料分量 `[-0.0003137551201961619,0.0023430611778208557] N`，Hu 分量 `[-0.00047733486709937006,0.0014462246034984065] N`。返程 index8 总力 `[-4.407897629741671e-31,2.985672011257475e-32] N`；保留这些微小非零值，不阈值裁零。

## 边界节点分类

依据既有 `boundary_geometry.exposed_q1_edges` 的拓扑定义：被选 body 单元的无向 Q1 边只出现一次即 closed-body 边；reference 两端 y40 的边为数学对称切口，物理暴露边去掉它。节点由这些已定义边的端点集合分类，而不是按力大小、analytic 圆方程或位移阈值分类。

推荐三个互斥总组：物理暴露边节点、仅切口节点、内部节点；另外以标签保留“既是物理边端点又在切口”的角点。全部 workpiece_nodes 必须各归一次，以便节点合力覆盖完整 body 而不会重复。对于当前对齐 17×9 节点矩形，拓扑期望为 33 个物理边节点、15 个仅切口节点、105 个内部节点，总153；这来自原网格矩形计数，尚未运行新分类消费者。顶部两个端角包含在物理边节点中。

方体 bottom/left/right 边标签可以重叠，角点不能被多次加入 body 总合力；一个角点的 FE 弱式节点力无法仅凭全局向量唯一分摊给两个面。不要由节点力直接除以网格长度/面积生成“压力”。

Circle 构造政策同样取 native cell-centre mask、再约束所有 incident nodes，实际边界是 staircase，不是拟合圆。圆体应使用同一 exposed-edge/cut 拓扑分类；可以展示台阶边或角点标签，不能用 analytic radial normal 自动宣称表面法向压力。当前 finite-face normal-ray 诊断只适用于完整固定半方体，不因新的节点力图自动获得圆体面距离资格。

## 最小功能与可视化

建议独立纯保存消费者只接受 model27、状态 descriptor/forces16、reference summary 与其已存全局/方程/body 检查文件。其输出无需 Project/TMC 或内核导入：一个节点 CSV 共 `9×153=1377` 行，保存实际 accepted_index、original_target_index、leg、d、stateSHA、node_id、source/actual XY、分组标签、三分量 Fx/Fy、holding Fx/Fy、对应 HP80/120 原字符串；另九行摘要保留节点合力、现有缓存 body 合力、signed Fy、2absFy、分组和重叠说明。

一张 3×3 图即可：行是 index0 初态、index4 峰、index8 返态；列是 total/material/Hu。真实 ×1 机构与固定方体、原节点位置，画全部 body 节点力箭头（只发生显示抽稀时明确节点名单）。同一个线性 N/箭头标尺跨三态、三分量；零初态不造箭头，返态保留原非零数值且诚实说明公共尺度下不可见。角点、cut-only、内部节点使用不同 marker；图示无 surface traction/pressure。附九态 signed XY 合力曲线，按路径索引连接而不按 d 排序，以区分加载卸载同目标；不插值变形或添加镜像求解态。

所有来源输出路径应相对完整 Git 根，原 model/forces/ref 哈希绑定，独占新目录，原证据不覆写。最近执行范围只做保存数据投影与实际图，不增加新 FE/HP/campaign；后续工件形状和更大行程仍需独立任务与真实结果，不能借此图授予夹持资格。

## 关键保存身份

- result/result.json：`d62d584b618af4c1ead89c4c9fb07cea4585c9ce873221bf66600d019550cb42`
- result/model/model.json：`7570b702a674b197f58cb8f22246f1b115ae3420e35feb7b5100285794ef01b8`
- result/model/model.npz：`a2d6e141fecb5f34efa66455c19ee67f47f476e019f760feb685f1a091266049`
- reference/summary.json：`7ffea3f27ae288d23fead7647bf4d24e468cc197bef7caa12dbfff22139110f7`
- 初0/峰4/返8 stateSHA：`26d76fa997d7fc33a9ff6a4b606fc4f31e3f1c0753050e330d97c92565c2bbe2` / `dfc83d4510b22ca97a914b72fb593c140d1e542255cf2054836705b555bf2558` / `ac522b8e239841d3e59a19a6dd61ba3ff76e03f4d296c5225e78dc6a2cbd5891`
