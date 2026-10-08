# 恢复开发入口

先读[本轮短报告](../lf_data_preparation/native_interface_001/batch_reference_v2_001/RESULTS.md)、[生产index](../lf_data_preparation/native_interface_001/batch_forward_001/run_001/batch/index.json)、[双例保存独审](../lf_data_preparation/native_interface_001/batch_reference_v2_001/closure_review/dual_saved_review.json)及[视图回执](../lf_data_preparation/native_interface_001/batch_forward_001/run_001/view_execution_receipt.json)。两例生产、V2独参和B-VIEW2均已实际PASS关闭；各4态/8次新HP/4帧，V1的HP0失败仍保留，不再补算已闭卡。

| 设计 | 实际PNG | 全4态GIF | 自有qualified响应 |
|---|---|---|---|
| canonical | [结构与数值](../lf_data_preparation/native_interface_001/batch_forward_001/run_001/view/canonical/native_mean_path.png) | [动画](../lf_data_preparation/native_interface_001/batch_forward_001/run_001/view/canonical/native_mean_path.gif) | [JSON](../lf_data_preparation/native_interface_001/batch_forward_001/run_001/qualified_response_canonical.json) |
| native_fine | [结构与数值](../lf_data_preparation/native_interface_001/batch_forward_001/run_001/view/native_fine/native_mean_path.png) | [动画](../lf_data_preparation/native_interface_001/batch_forward_001/run_001/view/native_fine/native_mean_path.gif) | [JSON](../lf_data_preparation/native_interface_001/batch_forward_001/run_001/qualified_response_native_fine.json) |

下一步先核已有固定工件大行程任务，经现有薄API的具体实例缺口：逐项对照原任务路径、fixed_rigid几何、初始化选项、力摘要和保存输出，再选择最小功能接续。task1.1已支持square/circle及ordered_cycle，API已透传路径/模式，摘要已有body弱式力、holding、mirror/net和双侧法向幅值和；不重复实现这些入口。此处只是接续计划，没有启动新科学计算。

任意clone/cwd均用显式repo作为相对路径基础，在项目HF环境中运行；后续在main开发，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git。保持原任务、几何、参数、网格、边界和模式明确，独立新执行须记录新范围与预算。不要把无工件两设计差异当作网格收敛、排名或夹持资格；不要把已实现fixedbody入口再写一遍。发布状态以实际Git记录确认。
