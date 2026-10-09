# 同结构h0.5完整路径：来源与执行准备

2026-10-09。状态：源码及普通JSON输入已准备，**未授权、未运行**。M-PREP1构模/未变形图已一次通过，新路径不借其资源窗口。

最近目标是通过既有真实CLI/API执行同结构、同物理任务的h0.5完整24原目标加载—卸载，取得自有保存态，为网格敏感性对照增加真实响应。只新增单例[manifest](manifest.json)、[task](task.json)、现有观察包装的局部适配；HF核心没有修改。[具体M-CYCLE1卡](M-CYCLE1_CARD.md)说明物理任务、原门、实际基线及新资源申请。

派生几何/模型来源于[M-PREP1实际结果](../nested_mesh_preparation_001/RESULTS.md)，fine fixed1548/free25830，模型数组及四项几何身份在新[protocol](protocol.json)中绑定。新task仅更正非物理说明与ID，保持原物理字段及目标路径；构模计数在首个力计算前核对，成功保存模型数组需与已验证准备模型一致。

[源码及成本依据审阅](author/next_cycle_source_review.json)、[精确差异](author/execute_nested_cycle_source_diff.patch)与[执行候选](author/execute_nested_cycle.py)保留来源。原力/切线观察、solve及缓存门数学逐字保持；24原目标匹配允许原控制器插入二分态。源码准备没有HF导入、NPZ解码、pilot/cost/力学或渲染调用。

[独立最终静审](author/final_cycle_static_review.json)通过：44实际文件绑定、已有API字段、物理任务、原门/观测块及资源合同一致，未发现执行前必须修正项。这是静态准备，不是细网格数值通过。

申请一次controller14400／helper15000／outer15060秒、采样8 GiB；其依据和不确定性见卡。新阶段尚无结果、变形图、独立参考或资格。收到具体卡批准后才执行，生产结果再决定自有HP/观察最近一步；两网格只报告敏感性。
