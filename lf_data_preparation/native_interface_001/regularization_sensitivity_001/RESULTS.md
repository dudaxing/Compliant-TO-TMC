# M-ALPHA1：14加载态已保存，首次卸载因时间预算停止

本卡实际终态为 **NOT_PASS**。14个原点／加载目标从零至1.20 mm均接受并保存；计划中的第一次卸载至1.15 mm未接受，控制器返回 `time_limit: split average path wall-time budget exceeded`。批次首个终端非成功后停止，显示子进程没有启动，新alpha图件与独立HP均未取得。已保存14态的缓存原生产门通过，不能据此将完整15目标执行改写为PASS。

## 整体目标、已有功能与本轮目的

整体目标是从LF普通几何建立独立HF有限变形／TMC前向评价，给出结构实际变形、输入反力和含义明确的工件作用，逐步支持同物理任务的候选比较与正式HF5。HF与LF优化断开，生成／优化／评分研究层继续复用；开发在main，origin保持 `https://github.com/dudaxing/Compliant-TO-TMC.git`。

完整NumPy力、全DOF组装与未对称切线矩阵、平均输入位移平衡、缓存保存／复读、CLI／API／同任务batch已经实现。固定方体原24态加载／卸载、实际变形和total／material／Hu节点作用显示、原细网格24态／48HP及关联功能已有证据。原参考属于原alpha状态；独立切线参考限已声明PORT方向，完整矩阵实现与全部切线列的独立验证是不同范围。

现有网格证据表明整体响应和局部场可能表现不同敏感性。旧gamma实验使用不同网格／域，旧软化实验同时改变多项，没有当前任务的alpha单因素控制。因此本轮保持原几何、材料、工件、端口和边界，只将alpha从1e−6减至5e−7，重新平衡，观察参数对结构和有符号工件作用的影响；不按比例缩放旧力，不重写已实现力核或重复原参考账本。[准备审计与取舍](PREPARATION_RESULTS.md)保留完整依据。

## 物理任务与实际完成范围

保持84×40 mm下半域、h=0.5 mm、13440单元／13689节点／27378 DOF、平面应变、E=1 MPa、nu=0.3、厚20 mm；固定刚性方体中心(71,40) mm、边长18 mm，gamma=1e−6、Lr=80 mm，原支撑／背景对称及2 mm平均输入端口保持。实际新模型alpha=5e−7、kr=0.004307692307692307 MPa·mm²；首次力计算前的材料／区域单因素核对完成。

[任务](task.json)的15原目标为 `[0,0.25,0.50,0.65,0.75,0.80,0.85,0.90,0.95,1.00,1.05,1.10,1.15,1.20,1.15]` mm。实际接受原index0–13，最后为loading1.20 mm；没有额外二分接受态，没有unloading接受态。`loading_peak_reached=true`，`path_completed=false`、`unload_endpoint_reached=false`、`task_target_executed=false`保持原结果。

原失败尝试记录为from1.20／attempt1.15 mm、depth0、time_limit，`rollback_bitwise_equal=true`。回撤曾出现invalid_J全步试探，原半步回溯后继续；最终停止原因仍是时间预算，没有全部回溯失败、线性分解失败或物理分支失稳的终态依据。Newton／line-search记录中的trial accepted只表示试探步接受，不表示卸载平衡态接受。没有把未收敛试探当作可恢复的正式卸载状态。

实际batch／API／model／solve／save／summary各启动并完成一次；force304启动／259完成，tangent126启动／126完成；原控制器内部试探／回溯保留。缓存保存与摘要各额外F/T为0，HP／JIT为0，view_child启动／完成均0。窗口已结束，无包装重试、修复重跑、延期或force。

## 保存状态的原值对照

下表只从新旧普通result/state JSON复制原值，未新增差值、百分比、积分或科学计算。baseline为原h0.5、alpha1e−6；本轮为alpha5e−7，均明确匹配原目标index与loading leg。

| 原目标／量 | baseline alpha1e−6 | 本轮alpha5e−7 |
| --- | ---: | ---: |
| index6，0.85 mm：输入反力R，N | 0.16705078472657217 | 0.16568184818471396 |
| 同态q_out，mm | 0.983337384341189 | 0.9873593768599482 |
| 同态ON-body total Fx，N | −0.0003661101623771459 | −0.0001634171406509839 |
| 同态ON-body total Fy，N | 0.004636577550125938 | 0.005023464047615883 |
| 同态ON-body material Fy，N | 0.0034790753630243565 | 0.004186672838810768 |
| 同态ON-body Hu Fy，N | 0.001157502187101581 | 0.0008367912088051133 |
| 同态全模型积分点minJ | 0.008390713308768259 | 0.0038272078209654267 |
| 同态全模型max abs Hu，mm⁻¹ | 0.35064216120266933 | 0.3464004696667464 |
| index13，1.20 mm：输入反力R，N | 0.37870645239539324 | 0.37865427196005513 |
| 同态q_out，mm | 1.0166993609101365 | 1.016934534302024 |
| 同态ON-body total Fx，N | −0.0008760157046173312 | −0.0005990919179800212 |
| 同态ON-body total Fy，N | 0.12317940160165043 | 0.12492121630032427 |
| 同态ON-body material Fy，N | 0.12191255705872141 | 0.12405713468784063 |
| 同态ON-body Hu Fy，N | 0.0012668445429290087 | 0.0008640816124836284 |
| 同态全模型积分点minJ | 2.339669248338757e−5 | 2.3283009562457014e−5 |
| 同态全模型max abs Hu，mm⁻¹ | 0.3614815860369214 | 0.363602237992235 |

峰值输入反力接近，同时工件分量、横向作用及局部场指标有变化；单个总反力不能代表所有量都稳定。减半alpha后的Hu Fy没有按旧值简单减半，因为新位移和材料作用也重新平衡。本表支持保存加载态的敏感性观察，不给出收敛或有效夹持结论。

峰值原保存holding为 `[0.0005990919179800212,−0.12492121630032427]` N，镜像上半作用为 `[−0.0005990919179800212,−0.12492121630032427]` N；镜像推导的完整工件net为 `[−0.0011981838359600423,0.0]` N，双侧法向幅值和为0.24984243260064853 N。它们沿用下半固定工件弱力语义；镜像观测没有新求解上半模型，双侧幅值和不是有效夹持力。

本轮保存的node-window bottom clearance在0.85／1.20 mm分别为0.014959419952848663／0.0009696602064828141 mm，只是原栅格节点窗口诊断。新有限钳尖面距离尚未观察，不能把这些数值改名为新surface gap或接触证明。以上J／Hu是全模型保存标量，不能改称排除工件的free-medium分区指标。

## 原门、资源与真实停止原因

helper缓存原门对14个保存态报告passed：minJ=2.3283009562457014e−5、最大相对残差1.8258554853651901e−10、最大平均约束绝对残差2.7755575615628914e−17 mm且原native bound通过、最大相对总体力平衡5.166621345328082e−13、最大fixed split sum=0 mm。原残差／平均约束／固定／总体平衡规则保持；这是保存生产门的记录，没有新独立数值数组或HP验收。

| 原回执成本／范围 | 实际保存值 |
| --- | ---: |
| helper elapsed，s | 9059.380507799986 |
| helper sampled own RSS，B | 1420775424 |
| outer elapsed，s | 9059.673925399999 |
| outer sampled tree RSS，B | 1401597952 |
| 原path timing：kernel_and_transfer，s | 8850.413170600033 |
| 原path timing：assembly，s | 2.150289499972132 |
| 原path timing：sparse_solve，s | 31.222233099935693 |
| 原path timing：total，s | 9031.857919999995 |

controller9000／helper9600／outer9660秒及采样8GiB授权保持。停止来自控制器wall-time budget；outer exit1，stop_reason=null，不是outer资源停止。协作时间检查不是硬时间中断，helper与outer的不同RSS采样快照不能比较为同一时刻或硬OS内存上限。父包装的实际调用计数由实现与回执承载；viewer未启动，不声称已动态监测viewer中的机械hook。

## 图件缺口、证据与代码核对

本轮没有alpha新PNG／GIF／view receipt／alpha比较表。首次终端非成功触发停止，显示被跳过，原窗口已经关闭；不补画、不重启viewer，不以旧图冒作新alpha图。可继续查阅[原alpha1e−6的24帧实际变形](../../../functional_views/native_nested_cycle_20261009/complete_001/run_001/view/fixed_square/actual_states.gif)，其身份和数值属于旧baseline。

[本轮result](run_001/alpha_half/result.json)、[response](run_001/alpha_half/response.json)、[helper](run_001/execution_receipt.json)、[outer](production_launch.json)、[stdout](production_stdout.log)、[实际接受progress](run_001/accepted_progress.jsonl)和[batch](run_001/batch/index.json)保留真实部分路径。[授权](author/authorization.json)、[直接人类原话](author/direct_human_reply.json)、[原源码发布／恢复证明](author/M_ALPHA1_source_publication_receipt.json)关联main64a19f7与原57 bindings。执行期[终态审阅](author/execution_terminal_review.json)、[14态部分保存身份审阅](author/execution_partial_identity_review.json)、[物理JSON](author/execution_physical_review.json)、[物理文字说明](author/execution_physical_review.md)及[图件范围记录](author/execution_visual_review.json)归档后承载独立说明：79份真实run文件原字节保留，78份helper声明产物与回执分别记录，无声明或身份缺口。metadata审阅通过不改变execution NOT_PASS。

| 实现入口 | 对应功能与边界 |
| --- | --- |
| [native_project](../../../hf_repo/src/hf_eval/native_project.py) | 原模型／材料／端口及fixed square/circle构造；circle为native staircase，rectangle task尚未实现 |
| [native_force](../../../hf_repo/src/hf_eval/native_force.py)／[native_tangent](../../../hf_repo/src/hf_eval/native_tangent.py) | 完整力和全DOF未对称矩阵已实现；全部切线列独立HP验证仍缺 |
| [native_mean](../../../hf_repo/src/hf_eval/native_mean.py)／[split_displacement](../../../hf_repo/src/hf_eval/split_displacement.py) | 平均输入控制、Newton／LU／回溯／二分及接受缓存；一般任意输入控制不是当前native接口范围 |
| [native_evaluate](../../../hf_repo/src/hf_eval/native_evaluate.py)／[native_batch](../../../hf_repo/src/hf_eval/native_batch.py) | 单次API、同任务顺序batch、真实失败／部分路径保存、首个终端非成功停止 |
| [execute_alpha_cycle](execute_alpha_cycle.py)／[compare_alpha_views](compare_alpha_views.py) | 单因素包装与保存态对照；本轮前者执行，后者未启动，原对照包装要求15原目标 |

保存几何／实际变形／三分量quiver与GIF显示功能已经实现，但本轮尚无新产物。当前square region/viewer不能据circle构造能力宣称circle完整验证；连续总压力、可移动工件／摩擦、有效夹持、参数／网格稳定性、一般输入控制、全部切线列独立验证、正式HF5及研究层同任务接入仍未完成或未验证。原57项源码及证据绑定、science0.5.0及原24态48HP资格保持。

最近取舍见[NEXT_STEP_REVIEW](NEXT_STEP_REVIEW.md)：先完成本次真实记录发布，再准备读取14保存态的实际显示和原耗时记录静查，不重新做加载或扫描新alpha。
