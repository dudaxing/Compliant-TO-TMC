# M-LINK1：已有参考与图件的关联入口已通过

2026-10-09，用户明确批准后唯一实际执行 PASS，exit0、stop_reason null；helper 0.2004934000 s／outer 0.3920396001 s，采样自身 RSS 26537984 B／tree RSS 30978048 B。35 份绑定保持。保存摘要开始／完成 1／1，response 写入 1 次、轻索引写入 1 次，新三份JSON共21111B。独立终态审阅 PASS，180／180项为只读身份／来源／资源检查，并非新增科学试验；本阶段没有重试、修复重跑、延期或 force。

[新增关联 response](run_001/linked_response.json) · [轻交付索引](run_001/delivery_index.json) · [实际 helper 收据](run_001/execution_receipt.json) · [实际 outer 收据](link_launch.json) · [独立终态审阅](author/terminal_review.json) · [冻结卡](M-LINK1_CARD.md) · [冻结协议](protocol.json)。独立终态报告原字节 SHA：`15ceacda5cbc2e88c4f07e96fc91eaea3e8e3d2b225a6e0dea1080ab5f86dd87`。

## 整体目标、已有实现与这一步的理由

整体目标是从普通 LF 几何输入独立完成 HF 有限变形／第三介质接触(TMC)前向评估，获得可核对的加载／卸载、反力、结构变形与工件受力，并能在另一目录或计算机恢复继续开发。当前已实现固定方形工件完整24态加载／卸载、13440单元／27378DOF细网格、总／材料／Hu有符号弱式力、M-REF2自身48／48HP独立参考及M-VIEW1保存态实际变形图。

此前原生产 response 尚未关联随后生成的独立参考和图件。本步直接复用现有 `summarize_saved_native_result` 与 `write_native_response`，新增同身份 `linked_response.json` 和 `delivery_index.json`，让人工检查与恢复开发从一个入口到达已有证据。109行薄层不复制逐态数值核对，不新增科学测试、模型或绘图。

现有API实际匹配同一result／model／task全部24态、已有48HP记录和12条参考Python来源SHA；reference=matched、full_path_reference_pass=True，views=matched。关联仅核对保存元数据和原字节，不重新审计大型HP／NPZ档案。原生产 response 的 producer 三个flags仍false，reference／views not_provided保持原历史事实；新增response保留这些false flags，同时单独记录新的matched artifact。

## 实际功能效果、资源与数值

索引把原result／response、本次新增response、既有M-REF2 summary、原raw view和phase、4PNG／24帧GIF及四份表用repo-relative路径与SHA串联。raw view仍有3PNG＋GIF；第四粗细PNG来自原phase `comparison.image`。原result、response、raw view、phase及图件未复制或改写；换目录恢复后从仓库根解析这些相对路径即可。

本次保存摘要API调用1次，写response1次，写索引1次。新增科学F／T／HP／模型／求解／JIT／LF／observer／render为0，依据冻结入口和stdlib保存元数据／来源／图件调用路径；没有动态hooks监控，不能笼统写“API0”。helper时间／RSS是最后checkpoint之后、成功收据构造和写入之前的快照；outer时间确认完整launcher终态。新增代码运行成本为上述0.2／0.39秒量级；linked response中原生产F开始443／完成386、T201／201及生产evaluation11428.1522s是M-CYCLE1历史，不是M-LINK1次数或耗时。

物理任务仍为h0.5、84×40mm下半模型、固定方形中心(71,40)mm／边长18mm、E1MPa、ν0.3、厚度20mm，原平均输入0→1.2→0mm。下面是同一保存态的原物理数值，本次仅关联展示：

| 量 | loading原13／1.2mm | unloading原23／0mm |
|---|---:|---:|
| 下半模型输入反力R(N) | 0.3787064524 | -2.746498125e-26 |
| 物理端口平均输出q_out(mm) | 1.016699361 | -9.310010186e-25 |
| 下半工件ON-body Fy(N) | 0.1231794016 | -4.553785362e-27 |
| 保存积分点最低J | 2.339669248e-05 | 1 |

峰值下半工件Fy材料分量 0.1219125571 N、Hu分量 0.001266844543 N；两侧法向幅值和 0.2463588032 N，完整镜像净力Fx -0.001752031409 N／Fy0是另一个物理量。ON-body力与holding反力相反号；卸载微小残量保留，没有人为清零。q_out为端口平均位移，不是间隙。响应中的node-window clearance仍为原栅格窗口诊断，不是表面距离或接触证明。

## 原图件与表：直接人工检查

以下均是原M-VIEW1图件，没有新渲染。红色箭头是工件节点弱式力显示；峰值场及两网格曲线保留各自诊断口径。

![原24态实际×1变形与工件节点力箭头](../../../functional_views/native_nested_cycle_20261009/complete_001/run_001/view/fixed_square/actual_states.gif)

![原结构／钳尖与力曲线](../../../functional_views/native_nested_cycle_20261009/complete_001/run_001/view/comparison.png)

![原有限距离及力分量](../../../functional_views/native_nested_cycle_20261009/complete_001/run_001/view/distances_forces.png)

![原峰值J／Hu／固体应变诊断](../../../functional_views/native_nested_cycle_20261009/complete_001/run_001/view/peak_fields.png)

![原同设计粗细网格六量曲线](../../../functional_views/native_nested_cycle_20261009/complete_001/run_001/view/mesh_response_comparison.png)

原四表：[states.csv](../../../functional_views/native_nested_cycle_20261009/complete_001/run_001/view/fixed_square/states.csv) · [nodes.csv](../../../functional_views/native_nested_cycle_20261009/complete_001/run_001/view/fixed_square/nodes.csv) · [mesh_comparison.csv](../../../functional_views/native_nested_cycle_20261009/complete_001/run_001/view/mesh_comparison.csv) · [mesh_comparison.json](../../../functional_views/native_nested_cycle_20261009/complete_001/run_001/view/mesh_comparison.json)。

## 科学边界、未实现功能与下一步

M-REF2仍只资格化此精确result／model／task的24接受机械态和原5节点PORT切线方向；完整CSC组装身份不等于所有切线列的独立HP验证。图件是保存态诊断及两网格敏感性，两个网格不证明网格／域收敛。本次关联不增加压力、有效夹持、全列切线、应力／能量HP或HF5资格。圆体自身任务、自由体／摩擦、正式标签／批量排名仍未完成。

最近一步按[只读物理规划](author/physical_next_scope.json)准备一个简洁的stdlib CSV／JSON节点载荷账本，直接读取已有 `fixed_square/nodes.csv` 和关闭的工件／边界元数据。保留每节点原total Fx/Fy、material Fx/Fy、regularization(Hu) Fx/Fy六列，以及state SHA／原索引／leg／d；数值和微小卸载残量不裁剪，厚度已在原N单位中。将原physical_only细分为bottom／left／right侧内点和physical_corner；physical_and_cut交点、cut_only切面内点、body内部各自保留，形成七类互斥节点，每节点一次。物理角点与物理／切面交点的向量独立记录，不平均分配给相邻侧。

来源准备与审阅后，未来可先观察缓存origin、loading0.95(maxHu)、loading1.2、unload0，并在旧表适用时加入粗网格peak；实际分类／符号／分量结果明确后再处理all24、对照已有整体及原分组弱式合力，展示类别曲线与原几何上的角点／交点。**本轮未分组或求和新账本，也未执行未来实验／绘图或授权未来卡。**这一步是原节点弱式载荷的可解释组织，不是压力、连续牵引或新增力核资格；不重做已通过的求解／HP／NPZ／观察器。

外邻medium侧的材料P trace诊断留待账本实际结果解释后决定，**不纳入最近账本阶段**。固定工件是介质内运动学overlay，其内部保存F=I、P/Hu=0，不能采工件内部P来解释非零holding力；若以后做材料probe，需明确采用外邻trace且仍仅材料诊断。现有 `stress_first_piola` 只含材料P，不能把 `P·N`当作Hu模型总表面力或总压力；节点弱式力也不能直接除面积命名为压力。包含材料＋Hu、物理表面／对称切面／角点及余项的总边界力重建需再明确与当前离散弱式一致的定义；本阶段未实现它。

当前可恢复链条：原M-CYCLE1完整求解 → M-VIEW1图件 → M-REF2独立参考 → M-LINK1同身份关联入口。来源、卡、协议和各阶段原历史证据保持；本次独立审阅检查是只读身份／输出核对，不是新增科学测试。
