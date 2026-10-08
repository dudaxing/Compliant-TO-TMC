# 薄批量接口及真实两例结果

evaluate_native_batch及CLI先预检全批共享物理声明、JSON和新输出，再每例调用现有evaluate_native一次；首非success保留原失败/partial，后续not_run。15项mock功能测试后，两例真实.025 mm路径、各4态/14F/9T/1solve已完成；逐例各8次新HP及全4态保存图也已完成。所有比较仍使用19个共同物理键和原complete/full/tangent，不静默改变任务或网格。

| 设计 | 实际PNG | 全4态GIF | 自有qualified响应 |
|---|---|---|---|
| canonical | [结构与数值](../lf_data_preparation/native_interface_001/batch_forward_001/run_001/view/canonical/native_mean_path.png) | [动画](../lf_data_preparation/native_interface_001/batch_forward_001/run_001/view/canonical/native_mean_path.gif) | [JSON](../lf_data_preparation/native_interface_001/batch_forward_001/run_001/qualified_response_canonical.json) |
| native_fine | [结构与数值](../lf_data_preparation/native_interface_001/batch_forward_001/run_001/view/native_fine/native_mean_path.png) | [动画](../lf_data_preparation/native_interface_001/batch_forward_001/run_001/view/native_fine/native_mean_path.gif) | [JSON](../lf_data_preparation/native_interface_001/batch_forward_001/run_001/qualified_response_native_fine.json) |

[manifest](../lf_data_preparation/native_interface_001/batch_validation_001/example_two_case_manifest.json)给出本轮真实输入；[index](../lf_data_preparation/native_interface_001/batch_forward_001/run_001/batch/index.json)保留生产原摘要，自有qualified响应另存。图中×1是真实形状、×40只为小位移显示，另有反力、节点/加权位移与J值。原生产response不回写新参考/视图flag。

任意cwd用显式--repo统一解析输入和输出；请在项目HF环境中（与LF环境分开）运行。下方历史用法保留，但已使用的run_001输出不能再用作新执行目录；一次新的调用需新的输出和资源记录。本轮whole生产2400/2460 s、8 GiB和shared controller1800 s均已关闭，参考与显示为各自独立窗口。

两例是不同LF设计，且原生网格分别为1和0.5 mm，不能据此声称同设计网格收敛或排名。本轮无工件：body力为null，q_out是加权端口位移而非钳尖间隙。一般有效接触、连续压力、自由体/摩擦、匹配网格、重复性合同和HF5整体仍未完成；全切线列、能量/应力/应变HP没有被本轮授予。

下一步先核已有固定工件大行程任务，经现有薄API的具体实例缺口：逐项对照原任务路径、fixed_rigid几何、初始化选项、力摘要和保存输出，再选择最小功能接续。task1.1已支持square/circle及ordered_cycle，API已透传路径/模式，摘要已有body弱式力、holding、mirror/net和双侧法向幅值和；不重复实现这些入口。此处只是接续计划，没有启动新科学计算。

[本轮报告](../lf_data_preparation/native_interface_001/batch_reference_v2_001/RESULTS.md) · [恢复开发](RESUME_DEVELOPMENT.md)
