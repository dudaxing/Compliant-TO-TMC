# M-ALPHA1 实际结果物理解读

状态：`completed_actual_saved_result_interpretation_no_new_scientific_gate`。本次真实执行为 **not_pass**；本报告只读现有普通 JSON/JSONL 和源码、复制原值并作解释，没有新数值计算、NPZ 解码、科学入口或绘图，也没有新增验收门。

## 目标、所做工作及其原因

整体目标是实现与 LF 优化断开的独立有限变形／TMC 前向评价，让结构实际变形、输入反力和含义明确的工件作用可检查。本轮保持 h=0.5 mm、84×40 mm 下半域、固定边长18 mm方体、中心(71,40) mm、E=1 MPa、厚度20 mm、gamma=1e−6、Lr=80 mm、原支撑和端口，仅将 alpha=1e−6 改为5e−7。原模型记录实际 kr=0.004307692307692307 MPa·mm²；这是原结果，不是本审阅计算。

这项工作用于补当前同任务的正则参数敏感性证据。alpha、介质材料 gamma、物理长度 Lr 的作用不同；重新平衡后的材料/Hu作用不能用比例缩放旧结果。原15目标为原点、加载至1.20 mm、再回撤至1.15 mm的前缀，未安排完整卸载。

## 实际终态与已完成效果

唯一 outer 调用 exit=1，记录 elapsed=9059.673925399999 s，stop_reason=None；helper记录 elapsed=9059.380507799986 s。批准源提交 `64a19f7d990d294d09f16145eae946e0edfa1580`，协议 `430137c7e81cb12281937a6201519235fcc161de0503323684541c1c72b94d11`；原57绑定 unchanged=true。

直接停止原因是原 controller 的9000秒路径预算：`time_limit: split average path wall-time budget exceeded`。不是外部stop、内存停止或图形子进程失败。控制器返回部分结果，原写入与摘要均完成，随后 batch non-success 导致薄包装退出，view_child_started/completed均0，HP0。

14个接受态包括原点和原加载索引1..13，已加载至1.20 mm。`loading_peak_reached=true`，`path_completed=false`、`unload_endpoint_reached=false`。原状态/反力/工件作用和每态完整力、切线、全矩阵的保存声明已保留。`task_target_executed=false`、摘要目标/终点为null是公共摘要要求完成指定路径的语义，不能误读为1.20 mm峰值未算到。

原缓存门仅针对这14态：

- minimum_J=2.3283009562457014e-05；maximum_relative_residual=1.8258554853651901e-10。
- 最大平均约束残差=2.7755575615628914e-17 mm，native_constraint_bound_pass=true。
- maximum_relative_global_force_balance=5.166621345328082e-13；最大固定split和=0.0 mm。
- cached passed=true；整个M-ALPHA1仍not_pass，新态producer资格仍false。没有把部分门通过改写为完成15态或独立HP通过。

## 回撤到底进行到哪里

1.20→1.15 mm 回撤实际执行了 predictor、Newton基点1..5和线搜索。第一全步因invalid_J拒绝；半步有效，其后试探继续。最后记录的Newton基点 relative_residual=0.032195140683106124、minimum_J=2.2862689240188248e−05；之后第5步trial记录 phi=7.609458874889267e−07、minimum_J=2.3740207303790917e−05、R_input=0.3470376718304425。这些是试探记录，未得到后续合格基点与卸载接受态，不能当作1.15 mm卸载结果。

唯一failed_attempts为from1.20、attempted1.15、depth0、time_limit，rollback_bitwise_equal=true。durable保存态仍为1.20 mm；maximum_bisection_depth=0。没有Newton上限、全部回溯拒绝或线性分解失败的终态依据，也不能从预算停止推导物理分支失稳、非唯一性或求解器bug。

保留计数：force开始304／完成259，tangent开始／完成126；178条线搜索记录中45条invalid_J拒绝、22条Armijo拒绝。45次力入口未返回与invalid_J试探记录一致；Armijo拒绝是已返回的有效力计算未满足原减小规则。这些是唯一授权求解内的原有回溯，不是45个失败接受态或45次外部重跑。125条Newton基点和125条线性诊断仍在原result。

## 同原目标的原值并列

下表只复制原result字段；不计算差值、百分比、比率或插值。alpha1e−6原24态证据与新alpha5e−7仅在共同的14个原目标并列。

| 原索引 | d mm | 原alpha R N | 新alpha R N | 原alpha q_out mm | 新alpha q_out mm |
| --- | --- | --- | --- | --- | --- |
| 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 1 | 0.25 | 0.04576752431496978 | 0.04566571116134366 | 0.29254733533081145 | 0.29279930966593776 |
| 2 | 0.5 | 0.09289097516604754 | 0.09253330650808447 | 0.58628499811431 | 0.5872328828911214 |
| 3 | 0.65 | 0.12238702152121542 | 0.1216258353890282 | 0.7615196734802416 | 0.7636240548816405 |
| 4 | 0.75 | 0.14315504454823655 | 0.1418548575099262 | 0.8762752007043639 | 0.8799478056232992 |
| 5 | 0.8 | 0.15421292136397552 | 0.15254385353643912 | 0.9321081313981173 | 0.9368588283739611 |
| 6 | 0.85 | 0.16705078472657217 | 0.16568184818471396 | 0.983337384341189 | 0.9873593768599482 |
| 7 | 0.9 | 0.19350330938851512 | 0.19341336553117802 | 0.9977776885286317 | 0.9983217851036671 |
| 8 | 0.95 | 0.2233701677820972 | 0.22349880903000086 | 1.0032094249654324 | 1.0031901039335445 |
| 9 | 1.0 | 0.2540320771886477 | 0.2541367335203968 | 1.0066727288277793 | 1.006721865866614 |
| 10 | 1.05 | 0.28487470006361904 | 0.2849720920433688 | 1.0097696149749142 | 1.009829903897611 |
| 11 | 1.1 | 0.3158256314006974 | 0.3158860166997356 | 1.0127027458468831 | 1.0127763701278443 |
| 12 | 1.15 | 0.3471343276801674 | 0.34703768154036385 | 1.0149529767451642 | 1.0153174242325562 |
| 13 | 1.2 | 0.37870645239539324 | 0.37865427196005513 | 1.0166993609101365 | 1.016934534302024 |

q_out是端口加权位移，不是钳尖位移或表面间隙。完整JSON另按同原索引保留原minJ、global maxAbsHu、缓存残差、Newton次数与累计时间；不生成新的科学差值/比率。

## 已有工件作用的实际原值

以下均来自现有普通state/response，无需重新组装。分量顺序[Fx,Fy]，单位N，为下半固定体的有符号弱式ON-body作用：

- 原索引6，loading d=0.85 mm：新alpha total `[-0.0001634171406509839, 0.005023464047615883]`、material `[-0.00012101727104415016, 0.004186672838810768]`、Hu `[-4.239986960683371e-05, 0.0008367912088051133]`；双侧法向幅值和 `0.010046928095231765`。
  原alpha同目标：total `[-0.0003661101623771459, 0.004636577550125938]`、material `[-0.00010874115880239823, 0.0034790753630243565]`、Hu `[-0.0002573690035747477, 0.001157502187101581]`；双侧法向幅值和 `0.009273155100251876`。
- 原索引13，loading d=1.2 mm：新alpha total `[-0.0005990919179800212, 0.12492121630032427]`、material `[-0.0005068460128634392, 0.12405713468784063]`、Hu `[-9.224590511658194e-05, 0.0008640816124836284]`；双侧法向幅值和 `0.24984243260064853`。
  原alpha同目标：total `[-0.0008760157046173312, 0.12317940160165043]`、material `[-0.000561226821740675, 0.12191255705872141]`、Hu `[-0.0003147888828766561, 0.0012668445429290087]`；双侧法向幅值和 `0.24635880320330086`。

新alpha峰值原保持反力为`[0.0005990919179800212, -0.12492121630032427]`；镜像上半作用`[-0.0005990919179800212, -0.12492121630032427]`；完整镜像净力`[-0.0011981838359600423, 0.0]`。它们是原API已有量，镜像上半不是第二个完整物理求解。双侧法向幅值和不等于完整净力，更不是已合格有效夹持力。

两个保存点的ON-body Fy正、保持反力方向相反，材料与Hu作用均已记录。它们展示当前代码能够输出工件作用，但单凭这些resultants仍不能证明连续压力分布、摩擦/可移动体平衡或有效夹持资格。原值已显示参数改变时反力、变形及材料/Hu响应并非同一比例缩放；本次不计算比例或设置‘足够接近’门。

## 尚未看到的实际效果与验证边界

新alpha没有PNG/GIF、view manifest或alpha comparison CSV/JSON；没有查看本轮新像素。钳尖实际坐标、有限面无符号距离、solid/medium各自积分点minJ及medium分量maxHu尚未由viewer观察。普通JSON现有minimum_J/max_abs_Hu为全域保存标量；node-window clearances是原栅格界限，不能冒作finite-face unsigned gap或接触证明。原alpha的图和M-VOLUME/M-BOUND局部诊断不能替代新alpha实际效果。

原24态／48HP M-REF2/M-LINK1资格保留，属于原alpha状态。新alpha HP0；本次没有全列切线独立验证、总压力、有效夹持、参数/网格稳定或HF5资格，也没有新alpha接受回撤、完整卸载、滞回或回零证据。

代码已具备完整NumPy力、材料/Hu及完整DOF未对称切线/组装、当前平均输入任务平衡、保存/独立读取/CLI/API/batch、工件total/material/Hu/保持/镜像摘要和square实际变形viewer。当前缺全列HP验证，不能写成缺完整切线矩阵实现。现有native schema限定inverter/gripper、平均位移、自由输出k_out=0和既定支持/对称；更一般控制/载荷/BC组合尚未资格化。

square/circle固定体constructor选项已存在，circle使用cell-centre阶梯选择；现有区域测量、viewer和参考路径仍square专用。circle自身完整路径/图/参考、rectangle width/height任务支持仍缺，不能笼统说其它形状选项不存在。连续总压力、有效夹持、移动体/摩擦、物理稳定性与正式HF5仍是后续目标。

## 最近一步建议

先保留并关闭这次真实not_pass，准备短窗口的14个接受保存态可视化，复用已有支持partial result的square viewer与公共工件响应；显式标明partial/failed、无新HP、不增加平衡求解。这样能看到已经实现的加载、实际变形和有符号三分量作用，而不再重复长加载。

并排查现有回撤predictor/基点/trial/线性和成本记录。真实停止已定位为预算；首次invalidJ被原半步回溯处理，后续记录有进展，因此目前没有修改Hu力核/切线或放松门的依据。像素与入口兼容性核查后，再决定最小独立回撤诊断及其单独资源合同；不默认现有API可任意非零warm-start，不延期旧卡、不重做0→1.20来重复取得已有证据。本报告不制定新数值卡。

## 对照证据

- 批准源码：`64a19f7d990d294d09f16145eae946e0edfa1580`；协议SHA：`430137c7e81cb12281937a6201519235fcc161de0503323684541c1c72b94d11`。
- [实际result](../../../../lf_data_preparation/native_interface_001/regularization_sensitivity_001/run_001/alpha_half/result.json)、[response](../../../../lf_data_preparation/native_interface_001/regularization_sensitivity_001/run_001/alpha_half/response.json)、[execution receipt](../../../../lf_data_preparation/native_interface_001/regularization_sensitivity_001/run_001/execution_receipt.json)、[outer](../../../../lf_data_preparation/native_interface_001/regularization_sensitivity_001/production_launch.json)、[accepted progress](../../../../lf_data_preparation/native_interface_001/regularization_sensitivity_001/run_001/accepted_progress.jsonl)。
- [原基线result](../../../../lf_data_preparation/native_interface_001/nested_cycle_001/run_001/fixed_square/result.json)、[原控制器](../../../../hf_repo/src/hf_eval/split_displacement.py)、[public summary](../../../../hf_repo/src/hf_eval/native_response.py)、[已有viewer](../../../../functional_views/right_margin4_20261007/complete_001/saved_right_margin_views.py)。
- 各真实普通文件SHA、接受态身份、两点完整工件字段和原回撤记录在同目录physical_results_review.json。只读文件身份不是新增物理验收门。


归档说明：仅把原本机仓库路径前缀改为相对仓库链接，物理解读原文保持。原文件及副本 SHA 见 execution_supplemental_archive_receipt.json；对应普通记录 JSON 已归档为 execution_physical_review.json。
