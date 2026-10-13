# M-EREF1：新1.10 mm保存态的独立参考与误差图

2026-10-13（Asia/Seoul）。状态：具体源准备，尚未运行HP或绘图；原M-EXTEND2已PASS闭卡并发布至main43e3ba7。本卡取得新窗口的直接批准后，只启动一次，不使用旧卡余时。

## 目标与取舍

整体目标是独立HF读取普通LF几何，输出有限变形／TMC前向反力、位移、固定工件作用、可恢复状态和实际变形，供外部研究层使用。HF不优化、不调用dmftd；MPM暂未实现，继续在main开发。

默认显式延伸入口已安装，36项测试与1.15→1.10 mm子段已成功。现在先核新1.10态的力和方向切线，再根据真实结果安排更低卸载目标。仅新增HP80／120各一次，不重做生产平衡、不重复已有1.15参考或旧48HP。

## 唯一保存态与原物理条件

来源为`../saved_extension_002/run_001/extended_alpha_half/result.json`的accepted child001／global15、绝对平均输入1.10 mm、leg=unloading、非continuation anchor。state SHA为`3dc492f8aef4751e643ddb1413a797ca39434d349bfed59844d46e4e730015ff`，新task canonical为`94671c3226afb193349324a91f15bd55923ba73e662e9ad76528c844000f74f6`。原生产仍为两态1.15／1.10，新参考只核其中child1；raw accepted_015保持global15，顶层summary保child1，不伪装成零初态或完整两态。

原h0.5 mm、13440单元／13689节点／27378DOF、固定1548／自由25830；E1 MPa、ν0.3、plane strain、厚20 mm、γ1e−6、α5e−7、Lr80 mm。固定方形工件中心(71,40) mm、边18 mm；五节点端口、原权重及k_out=0保持。原数组、物理任务、源状态、门、结果、response和图不修改。成功立即parent、failed/time_limit祖先及M-ALPHA1／M-EXTEND1 NOT_PASS分别保留。

实际输入为6NPZ：model、选中state／forces／tangents／CSC、source_geometry。前五份解码；source_geometry仅字节来源绑定。51独立descriptor字段，CSC另有format／shape两必需成员及原可选_is_array探针。aa86重开选中state／forces两次、18重复字段；合计7数组loader调用、69 descriptor读取出现（含CSC两必需容器成员则71），不是只5次打开。准备期NPZ身份只从已闭producer、发布manifest和普通descriptor继承并核stat，不读字节／header。

## 原数学与十五门

原B850 `CoreAudit.run_state(15,row)`和aa86 `WorkpieceCycleAudit.workpiece_checks`全字节继承，11依赖按唯一basename平铺；另归档本卡driver及纯plot模块。原import会加载JAX并注册转换包装，但不执行AD、本构JIT编译或核；不把零JIT执行说成未导入JAX。

HP80／120覆盖全13440单元和27378DOF、材料／Hu／总局部及全局力。Decimal3000散射并trap Inexact保持。方向为原b_in/max(abs(b_in))，固定分量0、deltaR=0；比较总／材料／Hu三分量在同一PORT方向的切线作用、CSC及KKT。保存总CSC逐系数组装身份保持，不等于独立核全部切线列。原工件ON-body、holding去重分组、重叠、镜像和dummy内部检查保持。

| 原门 | 原阈值 |
| --- | --- |
| production_residual | 1e−9 |
| independent_residual | 1e−8 |
| force_evaluation | 1e−9 |
| average_constraint | 1e−10 |
| global_force_balance | 1e−6 |
| fixed_displacement_mm | 8e−11 |
| hp80_hp120 | 1e−40 |
| total_force | 1e−11 |
| material_force／regularization_force | 各1e−9 |
| total_tangent | 1e−10 |
| material_tangent／regularization_tangent | 各1e−9 |
| augmented_force_tangent／augmented_constraint_tangent | 各1e−10 |

十五门的原分母、floor、局部规则和投影顺序保持；这些误差不是工件Fy的相对百分比。Hu／F／J rounded数组仍仅原诊断，不增加stress／独立Hu数组门。独立解析能量仅归档，机械候选的辅助材料能量not_evaluated／unqualified／absent保持。

## 一次可视化及输出

全部原数学、工件检查与来源绑定通过后，同一helper只调用一次纯plot，读取本次新accepted_015/summary.json。图显示10个原记录的error／limit：三全局力、三PORT作用、CSC／KKT作用、HP120平衡残差与HP80／120总力一致性。Decimal40的log10比值仅用于显示；原零误差标为零，不加新floor、规范或验收门。产生`reference_observations.png`及普通JSON，plot_started／completed在PASS时各1；真实模块来源及SHA记录，不声称动态监控了所有力学hook。

现有M-EXTEND2两态实际变形GIF和三PNG通过文档链接供物理对照，本卡不重读旧媒体或新画结构。实际新PNG生成后，允许在记录阶段一次像素检查／展示以核可读性；不重绘、读科学数组或改变数值资格。

参考输出为run_001/reference：原fixture、两HP local、global、element gates、equations、actions、重组CSC、rounded诊断、workpiece checks、raw与顶层summary、来源／protocol／lifecycle；加上述一PNG／JSON。失败保存真实partial、HP与机械／工件／plot实际计数，原error及来源保留。

## 新资源窗口与首错规则

一次helper900秒／outer960秒（16分钟）、采样8GiB。包含最早clock后的批准与来源核对、import、数组读取、归档、2HP、全部比较、Matplotlib import／一次plot、最后hash／summary／回执。旧同α两态4HP实际outer193.3503秒可作保守规划依据，不保证本次耗时或成功；内存额度不按态数缩小。

首个终端错误停止，无测试、修复重跑、重试、延期、force、新生产F／T、构模、平衡求解、API关联、reader修改或安装。采样RSS／合作stop不是OS硬上限；继承HP evaluate内部无checkpoint，stop在返回后检查，等待真实退出，迟到PASS不得通过。plot失败同样整体NOT_PASS，不在闭窗外重画。本卡只授独立参考及显示，不授下一卸载目标。

## 资格与后续

现有公开API参考读取要求原结果全部两态和4次新HP；本卡一态／2HP独立存档，不能作为该两态result的matched参考，也不改reader来放宽要求。full_child／original／extended reference及完整任务、压力／有效夹持、稳定性、全列切线、一般LF和HF5资格保持false。

若通过，依据新1.10实际参考与已保存力／距离，准备下一段卸载，首先评估1.05 mm；另行明确目标、资源、原门和实际显示。若失败先据本次证据排查，不静默修复重跑或扩大任务。
