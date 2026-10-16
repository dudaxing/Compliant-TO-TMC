# L-CPREP1：圆形固定工件未变形准备

执行状态：**PASS**。基线main `d2cad344a3675cc1129c4786629f56e5678cb895`，默认science版本0.5.0、原science baseline保持。目标是把第三个 wave LF 结构接入圆形工件探索，先核原网格、四个掩码、端口和约束能否组成明确模型，再安排实际加载。本轮未执行输入路径。

保留原 wave 几何；固定圆形工件中心 [71.0, 40.0] mm、半径 9.0 mm。实际 Q1 单元阶梯边界是计算边界，解析圆和原 side-18 方体包络只是参考。实际完成计数 `{'model_build_started': 1, 'model_build_completed': 1, 'model_write_started': 1, 'model_write_completed': 1, 'plot_calls_started': 1, 'plot_calls_completed': 1}`；普通独立审阅 `pass_finite_actual_readonly_review`，人工像素检查 `pass_pixel_inspection`。

其余条件逐值保持：E=1MPa、nu=0.3、plane strain、厚20mm、h=0.5mm、84×40mm下半域、gamma=1e-6、alpha=5e-7、Lr=80mm及原支撑/平均位移端口/对称。工件采用固定节点运动学覆盖，不把原介质掩码改成实体。新任务身份、工件定义及尚未执行的短路径已明确记录；原25目标方体task不变。

![圆形工件未变形模型](run_001/circle_prepared.png)

兼容性检查 25 / 25。原模型 13440 单元、27378 DOF；工件 510 单元、565 节点、1130 固定 DOF；合并固定 1272、自由 26106 DOF。实际暴露边 72 条，另有对称切口 36 条。背景介质计数包含固定工件覆盖，不能全部称为自由介质。

初始节点窗口 `{'left': 2.0, 'bottom': 1.0}` mm 按原机构节点的同水平／竖直线定义；它不是有限表面间隙，也不是接触起点。图为未变形下半域、坐标倍率 ×1，局部图只放大视窗。C 面板顶部第二行注记与节点标记轻微重叠；关键计数可读，精确值见诊断 JSON，本轮无重绘。

实际 F/T/HP/平衡求解调用记录分别为 0/0/0/0，测试 0，默认安装 0。结论基于冻结调用路径与实际记录，未部署全局动态机械 hook；依赖可导入或注册 JAX，不能声称零依赖导入。保存的 [0,0.25,0.5] mm 只是后续任务定义，尚未执行。

helper 17.44179119999899 秒，outer 18.11095270000078 秒；采样进程树峰值 241025024 B，预算 180/240 秒、1 GiB，清理确认 `True`。实际终端 `cbd644 exit0/session1925 closed`；原窗口封存 8 个输出、738974 B。科学／媒体身份继承原 helper seal 加 stat，闭卡不重读或重哈希载荷。

制造资格仍为 pending。未新增平衡、独立参考、压力、有效夹持、卸载／释放、稳定性或 HF5 资格。下一步先适配圆形保存态显示，再另卡安排同三目标短加载，依据真实反力、变形和收敛决定后续。现有方体显示器不能直接当作圆形显示器使用。

审查入口：[诊断](run_001/diagnostics.json)、[模型](run_001/model/model.json)、[任务](run_001/task.json)、[运行回执](run_001/execution_receipt.json)、[外层记录](preparation_launch.json)、[人工检查页](run_001/REVIEW.md)、[实际审阅](author/ACTUAL_REVIEW.md)、[像素检查](author/pixel_QA.json)、[闭卡记录](author/closure.json)。
