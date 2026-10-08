# HF物理与功能矩阵

整体目标是独立HF读取普通LF几何，对一致明确的物理任务给出可审查响应；外部研究层、优化器和排名保持独立。生产、独参、显示与一般物理资格分开记录。

| 功能 | 已实现与真实证据 | 仍缺的实际范围 |
|---|---|---|
| 同任务小批量 | 薄API/CLI、15项mock；两例同19键物理任务各4态真实生产、各8新HP、各4帧图与自有摘要全部完成 | 重复性合同与HF5整体；不授排名 |
| 独立参考 | 两例全部接受态共16新HP、77174/307574检查；双例saved-only独审PASS | 全切线列、能量/应力/应变HP未由本轮授予 |
| 结构与数值显示 | 本轮各PNG/全4态GIF，×1及明确×40、反力/端口节点与加权位移/J；链接匹配自有result/新独参 | 图不增加接触、压力或一般模型资格 |
| 固定工件入口 | task1.1支持fixed_rigid square/circle及ordered_cycle；API透传path/模式；已有弱式力/holding/mirror/net摘要；历史方体24态/48HP | 先核薄API承接已有大行程任务的具体实例缺口；圆体完整资格不可借用 |
| 接触与自由体 | 历史固定方体弱式力、有限距离及约束反力可查看 | 一般有效接触、连续压力、自由体平移/转动/力矩稳定性和摩擦 |
| 网格与域 | 原生Q1及HF派生介质域；本轮h1、h.5为不同设计 | 同设计匹配网格与全路径域收敛仍须独立证据 |

| 设计 | 实际PNG | 全4态GIF | 自有qualified响应 |
|---|---|---|---|
| canonical | [结构与数值](../lf_data_preparation/native_interface_001/batch_forward_001/run_001/view/canonical/native_mean_path.png) | [动画](../lf_data_preparation/native_interface_001/batch_forward_001/run_001/view/canonical/native_mean_path.gif) | [JSON](../lf_data_preparation/native_interface_001/batch_forward_001/run_001/qualified_response_canonical.json) |
| native_fine | [结构与数值](../lf_data_preparation/native_interface_001/batch_forward_001/run_001/view/native_fine/native_mean_path.png) | [动画](../lf_data_preparation/native_interface_001/batch_forward_001/run_001/view/native_fine/native_mean_path.gif) | [JSON](../lf_data_preparation/native_interface_001/batch_forward_001/run_001/qualified_response_native_fine.json) |

本轮无工件，body力为null；R为半模型输入反力，q_out是加权端口位移而非钳尖间隙。历史固定体2|Fy|是双侧法向幅值和，装配净力为(2Fx,0)，不能混称压力或净夹持力。自有摘要accepted/full-path reference为true，但producer flags、全切线列、接触/夹持、压力与HF5资格仍为false。

下一步先核已有固定工件大行程任务，经现有薄API的具体实例缺口：逐项对照原任务路径、fixed_rigid几何、初始化选项、力摘要和保存输出，再选择最小功能接续。task1.1已支持square/circle及ordered_cycle，API已透传路径/模式，摘要已有body弱式力、holding、mirror/net和双侧法向幅值和；不重复实现这些入口。此处只是接续计划，没有启动新科学计算。

[本轮短报告](../lf_data_preparation/native_interface_001/batch_reference_v2_001/RESULTS.md) · [批量接口](NATIVE_BATCH_INTERFACE.md) · [历史固定体报告与真实图](WORKPIECE_ENLARGEMENT_20261007.md)
