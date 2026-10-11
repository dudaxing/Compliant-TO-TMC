# MSTAB1：既有 h1／h0.5 物理任务核查

结论：**两循环是同一固定方体物理任务的两级Q1离散，可沿用既有24态作网格敏感性比较；本核查没有取得网格收敛、接触压力或合格夹持力的新资格。无阻断项。**

基线 `main 5af8b5e`。正式仓库根为 `D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC`；下列路径相对该根。审计仅读普通JSON/CSV/源码和原字节SHA，未解码NPZ、导入API、调用候选、计算力／积分／新差值、绘图、建模或求解。详细出处与记录核对见同目录 `mesh_task_audit.json`。

## 原始来源与已证实一致

- h1：`lf_data_preparation/native_interface_001/workpiece_forward_001/run_001/fixed_square/{model/model.json,result.json}`；其视图 `functional_views/native_api_workpiece_20261008/complete_001/run_001/view/fixed_square/{summary.json,states.csv}`。
- h0.5：`lf_data_preparation/native_interface_001/nested_cycle_001/run_001/fixed_square/{model/model.json,result.json}`；其视图及原配对表 `functional_views/native_nested_cycle_20261009/complete_001/run_001/view/{fixed_square/summary.json,fixed_square/states.csv,mesh_comparison.csv,mesh_comparison.json}`。
- 几何：84×40mm下半域，镜面y40；同一LF设计及原右侧被动介质扩展。细网格来源JSON明确绑定上述h1几何，四种二值掩码逐父格2×2复制，不做平滑、插值、再阈值或清理。两者实体区域并集不变。M-PREP1已保存101项全通过（包括四掩码、物理面积、端口平均、BC、算子缩放），本轮继承该旧证据并核原17pins、几何快照及模型NPZ原字节身份，**不重做数组比较**。
- 方体：固定刚体、中心(71,40)mm、边18mm；下半方体为x62..80/y31..40。两者节点窗口初始left2/bottom1mm。它覆盖原介质的运动学约束，并非新赋高刚度材料；当前方边与两网格对齐。
- 材料完全相同：E1MPa、ν0.3、平面应变、厚20mm；gamma=alpha=1e−6，Lr80mm，kr=0.008615384615384613MPa·mm²。kr不随h／gamma再次缩放；厚度已进入原力，不能重复乘。
- task除task_id、geometry及三项说明文字外完全相同。28份原HF力学源码绑定一致；NumPy机械响应、chunk256切线、port_projection初猜及控制器策略一致。仅资源time_limit从4500改为14400秒。
- 输入为x0/y38..40的+x平均位移；输出为x80/y28..30的+y平均位移，自由输出、输出弹簧及输入辅助弹簧均0。两端口均用归一化参考弧长梯形平均，控制平均量，**不绑定端口各节点相同位移**。
- 支撑声明x0/y0..8的ux/uy，仅施于实体附着节点（实际y6..8）；实体对称声明y40/x0..60的uy，附着段x0..5及53..60保持。背景对称为y40/x0..84全部节点的uy，来源仅为HF task。旧LF背景x(60,80]元数据仅为来源说明。方体ux/uy全部固定；重叠固定DOF合并计一次。
- 原24目标相同：0→0.25→0.5→0.65→0.75→0.8→0.85→0.9→0.95→1→1.05→1.1→1.15→1.2→1.15→1.1→1→0.9→0.8→0.75→0.65→0.5→0.25→0mm。index0为origin，1..13 loading，14..23 unloading；两循环均完成，0二分／0失败尝试。普通state.json与result内记录、原视图及24对状态身份逐项一致。

## 允许的离散差与观察量定义

| 项目 | h1 | h0.5 |
|---|---:|---:|
| 网格(y,x) | 40×84 | 80×168 |
| 单元／节点／DOF | 3360／3485／6970 | 13440／13689／27378 |
| 实体单元 | 1086 | 4344 |
| 固定／自由DOF | 452／6518 | 1548／25830 |
| 方体单元／节点／DOF | 162／190／380 | 648／703／1406 |
| 每端口节点 | 3 | 5 |
| 端口梯形权重 | 1/4,1/2,1/4 | 1/8,1/4,1/4,1/4,1/8 |

原M-PREP1确认grad×2、hessian×4、权重×1/4、积分参考点相同、kr不变。索引、身份SHA、离散自由度及积分采样位置改变合理；Q1细分并不保证局部应变、Hu或力不变。

原比较表的14项值与两侧既存summary／CSV逐项对账；仅核已有差值在CSV／JSON一致，未重算差值或百分比。R为装置作用于模型的输入反力；方体力为模型／介质作用于下半固定体，负的保持反力。镜像上半为[Fx,−Fy]、全体净力[2Fx,0]；2|Fy|是法向幅值和，不能当净力或压力。无自动双倍。

q_out是输出端口平均量，不能当尖端位移。尖端固定选择参考点(80,30)mm（粗节点2630／细节点10300）；tip_to_*是到有限方体线段的**无符号最短距离**，与节点窗口clearance／首次射线距离不同，也不证明接触。solid_min_J取原实体积分点最小J；medium_min_J及max_abs_Hu取原介质剔除固定方体后的积分点，后者是Hu最大绝对分量（1/mm）。场图则用单元平均J／Hu Frobenius范数，不能把图中颜色与上述极值直接等同。节点physical/cut/intersection分区不是单元owner分区，也不是连续牵引。

## 资格边界与下一准备的约束

当前细循环已有M-REF2同24态／48HP独参通过，M-LINK1已关联；原生产result的false资格标志按历史保持。原M-VIEW1比较的reference_available=false是更早的历史快照，不能当当前细循环无参考。**当前h1 API循环自身reference仍not_provided**；早先另一个producer的48HP不能移用到它。

两网格结果用于敏感性观察，未证明收敛率／误差界、唯一平衡分支、域尺寸稳定性或gamma／alpha／Lr稳定性。原域与4mm右侧介质余量均固定。细网格owner／角点Hu诊断未提供同定义h1 owner重建；不能比较不同网格的局部编号或把节点分区代替owner。制造及体积分数门仍null/pending，未实现自由／可变形工件、摩擦，也无压力／有效夹持／HF5资格。本轮仅确认可比物理输入与保存记录，未增加科学验收门或重开计算窗口。
