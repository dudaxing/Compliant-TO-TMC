# 圆形工件分段加载—卸载：C5完成后的实际解释

本记录只汇总已保存普通JSON原值与原收据声明的媒体路径。没有新F/T、HP、求解、测试、几何搜索、载荷/CSV/媒体读取或绘图。C5已真实PASS关闭（父代理报告终态c56422/session24044/exit0）；临时BASELINE仅记录当时历史与运行中状态，不作为最终结果附件。

## 做了什么、实际完成了什么

目标是让现有圆形工件模型的公开保存态接口完成加载后的首次下降及继续卸载，并保留真实响应和近接关系。本次C5从C4保存的1.25mm出发，先用一次F/T重新验证锚，再接受1.15、1、0.75、0.5、0.25和0mm，实际7态，无二分。0端点是输入回零，固定工件和原物理条件没有变成自由释放。

历史共10个真实圆形窗口，覆盖17个按原顺序区分的目标；9个新窗口各有一个重新验证的保存锚，因此原件合计26条保存接受记录。9个锚均保持原SHA和R，且各为1个检查/F序号1/T序号1。完整SHA、各段计数和9个锚列于同名JSON，不合并或删除重复锚。

`[0,.25,.5,.75,1,1.15,1.25,1.35,1.4,1.35,1.25,1.15,1,.75,.5,.25,0]`

这表示分段历史目标覆盖，不表示C5一次重执行全部历史。C5的path_completed/unload_endpoint_reached为true；loading_peak_reached为false；task_target_executed、full_original_path_completed、full_extended_path_completed仍为false。原input峰值1.4保持，当前continuation不新增task_transition，首次跨kind证明保留在更深parent_continuation中。

| global | d mm | 原保存段 | R N | q_out mm | 下半工件total Fy N | medium minJ | 最近unsigned mm | 最右tip距 mm |
|---:|---:|---|---:|---:|---:|---:|---:|---:|
| 0 | 0 | CPILOT | 0 | 0 | 0 | 1 | 1 | 4.242641 |
| 1 | 0.25 | CPILOT | 0.04267919 | 0.2403558 | 0.00009658274 | 0.8362974 | 0.8370877 | 4.028093 |
| 2 | 0.5 | CPILOT | 0.08574821 | 0.481668 | 0.0002414252 | 0.6701214 | 0.6718882 | 3.811171 |
| 3 | 0.75 | CEXT | 0.1292606 | 0.7237693 | 0.0004832938 | 0.501097 | 0.5043742 | 3.592026 |
| 4 | 1 | STEP1 | 0.1733499 | 0.9662875 | 0.0009494406 | 0.3292998 | 0.3347371 | 3.349195 |
| 5 | 1.15 | STEP2 | 0.2002243 | 1.111617 | 0.001487188 | 0.2251542 | 0.2322577 | 3.202515 |
| 6 | 1.25 | STEP3 | 0.2184419 | 1.2081 | 0.002100912 | 0.1555328 | 0.1639716 | 3.104708 |
| 7 | 1.35 | STEP4 | 0.2371286 | 1.303665 | 0.003214135 | 0.08623625 | 0.09633236 | 3.007572 |
| 8 | 1.4 | STEP5 | 0.246843 | 1.350595 | 0.004223912 | 0.05213823 | 0.06329728 | 2.95984 |
| 9 | 1.35 | CUNLOAD3 | 0.2371286 | 1.303665 | 0.003214135 | 0.08623625 | 0.09633236 | 3.007572 |
| 10 | 1.25 | CUNLOAD4 | 0.2184419 | 1.2081 | 0.002100912 | 0.1555328 | 0.1639716 | 3.104708 |
| 11 | 1.15 | CUNLOAD5 | 0.2002243 | 1.111617 | 0.001487188 | 0.2251542 | 0.2322577 | 3.202515 |
| 12 | 1 | CUNLOAD5 | 0.1733499 | 0.9662875 | 0.0009494406 | 0.3292998 | 0.3347371 | 3.349195 |
| 13 | 0.75 | CUNLOAD5 | 0.1292606 | 0.7237693 | 0.0004832938 | 0.501097 | 0.5043742 | 3.592026 |
| 14 | 0.5 | CUNLOAD5 | 0.08574821 | 0.481668 | 0.0002414252 | 0.6701214 | 0.6718882 | 3.811171 |
| 15 | 0.25 | CUNLOAD5 | 0.04267919 | 0.2403558 | 0.00009658274 | 0.8362974 | 0.8370877 | 4.028093 |
| 16 | 0 | CUNLOAD5 | 4.038968e-26 | -7.940137e-25 | -2.774512e-28 | 1 | 1 | 4.242641 |

表内显示精度只为阅读；JSON保留原普通记录的binary64数值和独立状态SHA。最近unsigned距离不是有符号法向间隙，tip距离也不是最近边界距离。

## 卸载与同位移对照

峰1.4mm时，下半工件Fy为0.004223912418638585N，分为material 0.0008761171827550221N和Hu 0.0033477952358835616N；medium minJ为0.052138230727749965。卸载时这些压缩/弱力/Hu指标整体回到接近初态的保存值。它们支持“本模型本路径下响应恢复”的观察，不建立可逆性、唯一性、稳定性或零耗散。

以下仅对两次已保存普通标量相减，不同SHA和加载/卸载身份全部保留。C5的1.25锚只复核C4状态，不充作第三次独立新位移解。

| 同值d mm | load / unload global | ΔR N（卸-载） | Δtotal Fy N | Δq_out mm |
|---:|---:|---:|---:|---:|
| 0 | 0 / 16 | 4.039e-26 | -2.775e-28 | -7.940e-25 |
| 0.25 | 1 / 15 | 0.000e+0 | -4.066e-20 | 0.000e+0 |
| 0.5 | 2 / 14 | 1.388e-17 | -1.355e-19 | -5.551e-17 |
| 0.75 | 3 / 13 | 2.776e-17 | -1.518e-18 | 0.000e+0 |
| 1 | 4 / 12 | 1.388e-16 | 1.193e-18 | -1.110e-16 |
| 1.15 | 5 / 11 | -2.776e-17 | 2.168e-19 | 0.000e+0 |
| 1.25 | 6 / 10 | -5.551e-17 | 8.674e-19 | 0.000e+0 |
| 1.35 | 7 / 9 | -1.665e-16 | -2.168e-17 | 0.000e+0 |

0端点SHA为`3e4f405a5e312904dbc6a0d4c3d1ded4c42341f41c4a912801ce5dc087047589`，与原始0态SHA不同。原值保持：R=4.038967834295913e-26N，q_out=-7.940137446503689e-25mm，下半工件Fy=-2.7745116903123907e-28N，Hu显示极值5.204651817156875e-25/mm；solid/medium minJ均为1，nearest=1mm，tip=4.242640687119285mm。没有裁小量为0，也没有据此宣布完整位移场严格恢复或自由释放。

## C5成本、收敛及内部拒绝

C5实际45个Newton基点检查、42次线搜索（38接受/4拒绝）、44次线性求解；failed_attempts=0、最大二分深度0。F为87 started/83 completed，T为45/45，solver invocation1、HP/JIT0。4次拒绝全在0目标checks7/8/9/10的factor1，原因为unsupported_arithmetic_range；父代理已确认各次随后factor0.5接受、J=1。不是invalid_J，也不是一次Armijo数值比较不通过。具体失效算子没有保存，不能据此定位primitive或推断物理失稳；原内部回溯成功处理，无需因此自动修改guard/force或例行新增HP。

controller总计3468.0947298999818s，其中kernel+transfer 3366.29688440013s，sparse solve12.79685760004213s；helper3494.7855913999956s，display13.703840099973604s，outer约3495.7s。原窗口预算与原门未扩大：5400/600/6600/6660s，授权64GiB采样树上限、4个库环境上限16；上限不等于实际并行利用，viewer内部8GiB子限保留。

0端点11个检查，relative residual=5.424899524890885e-10，仍低于原1e-9门；分子free-force residual=1.0849799049781767e-22，保存尺度=1.9999999999999998e-13。constraint=0/bound1e-16；relative global force balance=1.2345531937516092e-11。这是近零载荷下原分母的缓存残差，不是独立HP误差，也不因相对数比其他点大就证明物理异常。

## 尚未实现的物理资格

- 当前力是ON工件的下半体节点弱式合力，material/Hu分解不是连续表面压力；Hu极值是参考Hessian分量指标，也不能直接等同某处全工件Hu Fy来源。
- 历史峰1.4mm的最近unsigned距离虽为0.06329727765158799mm，最右tip仍距圆形光栅边界2.959839839455605mm。最近部位靠近不等于目标尖端已承载。
- 保存的无交叉/near-touch/strict-overlap记录保留其原范围；complete containment未测。不授接触压力、有效夹持、自由工件释放或稳定性资格。
- CREF1只独立核验祖层加载1.15mm，不转授后续峰值、卸载态或历史整路径。生产原independent_HP/equilibrium/HF资格flag继续false。

## 已有媒体索引和本次图的意义

这些链接只来自原producer普通收据，未打开或哈希媒体。链接面向复制后的正式`lf_circle_first_unload_005/author/`位置。10个真实圆形段共有40PNG/10GIF；另5PNG为不同范围的辅助证据。各段comparison是该子段实际峰/末态，不冒称每段重现历史1.4峰；C5峰图是1.25锚、末图是0，GIF记录7帧。force/distance图保留全部接受索引和零端点微量，field图仅显示保存量，convergence图仅投影已保存标量。

| 原段 | 原声明媒体 |
|---|---|
| lf_circle_pilot_001 | [convergence.png](../../../../lf_data_preparation/native_interface_001/lf_circle_pilot_001/run_001/convergence/convergence.png) · [comparison.png](../../../../lf_data_preparation/native_interface_001/lf_circle_pilot_001/run_001/view/comparison.png) · [distances_forces.png](../../../../lf_data_preparation/native_interface_001/lf_circle_pilot_001/run_001/view/distances_forces.png) · [peak_fields.png](../../../../lf_data_preparation/native_interface_001/lf_circle_pilot_001/run_001/view/peak_fields.png) · [GIF](../../../../lf_data_preparation/native_interface_001/lf_circle_pilot_001/run_001/view/wave_circle_pilot/actual_states.gif) |
| lf_circle_extension_001 | [convergence.png](../../../../lf_data_preparation/native_interface_001/lf_circle_extension_001/run_001/convergence/convergence.png) · [comparison.png](../../../../lf_data_preparation/native_interface_001/lf_circle_extension_001/run_001/view/comparison.png) · [distances_forces.png](../../../../lf_data_preparation/native_interface_001/lf_circle_extension_001/run_001/view/distances_forces.png) · [peak_fields.png](../../../../lf_data_preparation/native_interface_001/lf_circle_extension_001/run_001/view/peak_fields.png) · [GIF](../../../../lf_data_preparation/native_interface_001/lf_circle_extension_001/run_001/view/wave_circle_extension/actual_states.gif) |
| lf_circle_step_001 | [convergence.png](../../../../lf_data_preparation/native_interface_001/lf_circle_step_001/run_001/convergence/convergence.png) · [comparison.png](../../../../lf_data_preparation/native_interface_001/lf_circle_step_001/run_001/view/comparison.png) · [distances_forces.png](../../../../lf_data_preparation/native_interface_001/lf_circle_step_001/run_001/view/distances_forces.png) · [peak_fields.png](../../../../lf_data_preparation/native_interface_001/lf_circle_step_001/run_001/view/peak_fields.png) · [GIF](../../../../lf_data_preparation/native_interface_001/lf_circle_step_001/run_001/view/wave_circle_step/actual_states.gif) |
| lf_circle_step_002 | [convergence.png](../../../../lf_data_preparation/native_interface_001/lf_circle_step_002/run_001/convergence/convergence.png) · [comparison.png](../../../../lf_data_preparation/native_interface_001/lf_circle_step_002/run_001/view/comparison.png) · [distances_forces.png](../../../../lf_data_preparation/native_interface_001/lf_circle_step_002/run_001/view/distances_forces.png) · [peak_fields.png](../../../../lf_data_preparation/native_interface_001/lf_circle_step_002/run_001/view/peak_fields.png) · [GIF](../../../../lf_data_preparation/native_interface_001/lf_circle_step_002/run_001/view/wave_circle_step/actual_states.gif) |
| lf_circle_step_003 | [convergence.png](../../../../lf_data_preparation/native_interface_001/lf_circle_step_003/run_001/convergence/convergence.png) · [comparison.png](../../../../lf_data_preparation/native_interface_001/lf_circle_step_003/run_001/view/comparison.png) · [distances_forces.png](../../../../lf_data_preparation/native_interface_001/lf_circle_step_003/run_001/view/distances_forces.png) · [peak_fields.png](../../../../lf_data_preparation/native_interface_001/lf_circle_step_003/run_001/view/peak_fields.png) · [GIF](../../../../lf_data_preparation/native_interface_001/lf_circle_step_003/run_001/view/wave_circle_step/actual_states.gif) |
| lf_circle_step_004 | [convergence.png](../../../../lf_data_preparation/native_interface_001/lf_circle_step_004/run_001/convergence/convergence.png) · [comparison.png](../../../../lf_data_preparation/native_interface_001/lf_circle_step_004/run_001/view/comparison.png) · [distances_forces.png](../../../../lf_data_preparation/native_interface_001/lf_circle_step_004/run_001/view/distances_forces.png) · [peak_fields.png](../../../../lf_data_preparation/native_interface_001/lf_circle_step_004/run_001/view/peak_fields.png) · [GIF](../../../../lf_data_preparation/native_interface_001/lf_circle_step_004/run_001/view/wave_circle_step/actual_states.gif) |
| lf_circle_step_005 | [convergence.png](../../../../lf_data_preparation/native_interface_001/lf_circle_step_005/run_001/convergence/convergence.png) · [comparison.png](../../../../lf_data_preparation/native_interface_001/lf_circle_step_005/run_001/view/comparison.png) · [distances_forces.png](../../../../lf_data_preparation/native_interface_001/lf_circle_step_005/run_001/view/distances_forces.png) · [peak_fields.png](../../../../lf_data_preparation/native_interface_001/lf_circle_step_005/run_001/view/peak_fields.png) · [GIF](../../../../lf_data_preparation/native_interface_001/lf_circle_step_005/run_001/view/wave_circle_step/actual_states.gif) |
| lf_circle_first_unload_003 | [convergence.png](../../../../lf_data_preparation/native_interface_001/lf_circle_first_unload_003/run_001/convergence/convergence.png) · [comparison.png](../../../../lf_data_preparation/native_interface_001/lf_circle_first_unload_003/run_001/view/comparison.png) · [distances_forces.png](../../../../lf_data_preparation/native_interface_001/lf_circle_first_unload_003/run_001/view/distances_forces.png) · [peak_fields.png](../../../../lf_data_preparation/native_interface_001/lf_circle_first_unload_003/run_001/view/peak_fields.png) · [GIF](../../../../lf_data_preparation/native_interface_001/lf_circle_first_unload_003/run_001/view/wave_circle_first_unload/actual_states.gif) |
| lf_circle_first_unload_004 | [convergence.png](../../../../lf_data_preparation/native_interface_001/lf_circle_first_unload_004/run_001/convergence/convergence.png) · [comparison.png](../../../../lf_data_preparation/native_interface_001/lf_circle_first_unload_004/run_001/view/comparison.png) · [distances_forces.png](../../../../lf_data_preparation/native_interface_001/lf_circle_first_unload_004/run_001/view/distances_forces.png) · [peak_fields.png](../../../../lf_data_preparation/native_interface_001/lf_circle_first_unload_004/run_001/view/peak_fields.png) · [GIF](../../../../lf_data_preparation/native_interface_001/lf_circle_first_unload_004/run_001/view/wave_circle_unload125/actual_states.gif) |
| lf_circle_first_unload_005 | [convergence.png](../../../../lf_data_preparation/native_interface_001/lf_circle_first_unload_005/run_001/convergence/convergence.png) · [comparison.png](../../../../lf_data_preparation/native_interface_001/lf_circle_first_unload_005/run_001/view/comparison.png) · [distances_forces.png](../../../../lf_data_preparation/native_interface_001/lf_circle_first_unload_005/run_001/view/distances_forces.png) · [peak_fields.png](../../../../lf_data_preparation/native_interface_001/lf_circle_first_unload_005/run_001/view/peak_fields.png) · [GIF](../../../../lf_data_preparation/native_interface_001/lf_circle_first_unload_005/run_001/view/wave_circle_unload0/actual_states.gif) |

| 辅助范围（不转授C5资格） | 原声明媒体 |
|---|---|
| lf_circle_input_preparation_001 | [circle_prepared.png](../../../../lf_data_preparation/native_interface_001/lf_circle_input_preparation_001/run_001/circle_prepared.png) |
| lf_circle_reference_001 | [reference_observations.png](../../../../lf_data_preparation/native_interface_001/lf_circle_reference_001/run_001/reference/reference_observations.png) |
| lf_circle_local_001 | [local.png](../../../../lf_data_preparation/native_interface_001/lf_circle_local_001/run_001/local.png) · [overview.png](../../../../lf_data_preparation/native_interface_001/lf_circle_local_001/run_001/overview.png) |
| lf_circle_first_unload_002 | [tiny_response.png](../../../../lf_data_preparation/native_interface_001/lf_circle_first_unload_002/run_001/tiny_response.png) |

本次4PNG由父代理各做一次像素检查并报告可读；本作者未读图。原第三个收敛面板legend/title小重叠保持，未重画。

## 一个最小有用的下一步

下一步只准备一个面向最右尖端的圆形右移布置输入与未变形兼容性对照，不直接重跑大行程。先从实际网格/域/连通与工件覆盖核定可行位置，保留当前圆形为对照，检查完整有限边界、机构实体/端口/支撑及固定体覆盖、域边界和右侧介质是否存在，再选定新坐标/半径及其明确边界条件。当前尚不能承诺 center=(75,40)、r=9 可用：若实际右域界为84，该圆会贴外边界并失去右侧介质，必须在未来准备卡中实际核清。兼容性准备完成后，才根据尖端与完整圆形边界关系选择一个有物理目的的小加载段，另行授权；本次不实现或运行新task。

这比无目的继续加行程或例行重做HP更直接回应当前未实现的目标：让真正预期的尖端接近圆形工件，随后才讨论承载与贴合。完成输入/未变形兼容性对照仍不是新的平衡或夹持资格。
