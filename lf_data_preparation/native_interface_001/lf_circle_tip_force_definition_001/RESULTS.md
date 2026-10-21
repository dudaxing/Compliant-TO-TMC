# L-CTIPGDEF1：单侧工件作用力规则整合

2026-10-21（Asia/Seoul）。文档整合及有限实际审阅通过；发布与异目录恢复以实际交付回执为准。本阶段没有数值执行窗口，不新增代码、计算、测试或图像。

整体目标是使外部研究层能在一致HF任务下使用LF几何的非线性／TMC响应。上一AREPORT1已提供保存研究结果读取函数；本轮解决这些力值如何正确取用和解释的问题。

正式入口为[单侧工件作用力：定义与字段用法](../../../docs/WORKPIECE_FORCE_DEFINITION.md)。README、hf_repo/README、CURRENT_STATUS、PHYSICAL_FUNCTION_PROGRESS和RESUME_DEVELOPMENT五处入口已增加规则及本记录链接，各自原字节后缀完整保留一次。

## 核清的规则与实际效果

|问题|本轮结论与用途|
|---|---|
|厚度和单位|两α各自model与geometry均明确20 mm；当前材料及Hu积分已各包含一次厚度。现有力单位N，不能再乘20，也不能未经定义改称N/mm。其他模型遵循自己的元数据。|
|单侧方向与符号|直接读取全部下半固定工件的原有符号Fy，同时保留Fx、原角色、位移与SHA；既有normal_force名称实际是Fy，不当作圆边局部压力。|
|三力与支撑反力|total、material、regularization（Hu）分别解释。当前返回nodal对象只有原total holding；分量反号不当独立反力测量。|
|镜像与节点范围|原producer镜像／净力／幅值和定义不同，且当前比较对象没有相应selector；只解释，不补算。原四mask、交点、全部节点与原矩参考点保持。|
|研究字段用法|列出完整周期、峰节点、合力、分组与矩的精确原字段。within使用unloading_minus_loading，cross使用new_minus_baseline，零态origin和accepted/global身份不混配。|

这样，研究程序可直接使用现有函数返回对象，避免二次厚度缩放、符号混淆和错误字段访问；无需再建reader或改动已保存数值。

## 实际核查与记录

[当前整卡授权](author/authorization.json)记录用户“批准按 L-CTIPGDEF1 整合并发布”。[本卡](L-CTIPGDEF1_CARD.md)含当前授权说明；准备期PLAN、原卡、proposed_plan及FINAL_PREPARATION中的pending/false按原字节保留，描述当时状态，不代替当前授权。

- [计划审阅](author/PLAN_REVIEW.md)：原10项通过。
- [定义来源复核](author/DEFINITION_SOURCE_CHECK.md)：8项通过，核去重13份源码及7份普通JSON身份，含两α各自model／geometry四份元数据。不是每文件只读一次的运行声明。
- [正式文档实际审阅](author/ACTUAL_REVIEW.md)：8项通过，核正式规则11837 B及SHA、23个规则链接和源码行、五处入口的旧后缀与真实字段语义；未预写发布／恢复结果。
- [原整合回执](author/integration_receipt.json)和[入口历史身份](author/front_history.json)保存实际写入时点与来源。审阅后已补齐本页及[NEXT_STEPS](NEXT_STEPS.md)，五条本页入口随后纳入最终文档检查。

最终新增文档格式、全部新文档链接及五个入口前缀核对记录于`author/DOCUMENT_CHECK.json`。普通发布和同机异目录local-Git恢复记录归档于`author/publication_receipt.json`；回执未产生前不将发布状态预写为成功。origin保持`https://github.com/dudaxing/Compliant-TO-TMC.git`，后续仍在main开发。

## 可视化与范围

[已有变形、全周期与节点力图总览](../lf_circle_tip_alpha_report_001/run_001/REVIEW.md)继续作为人工检查入口；本轮只链接，不读取旧媒体或新绘图。保留原密集小箭头和微小距离的显示限制。

本轮直接科学载荷／媒体读取、F／T、HP、构模、平衡、API调用、测试、新PNG、默认HF或研究reader实现改动均为0；普通源码／JSON身份、文档和Git对象操作单独计，不冒称科学验收。原物理、门、结果与资格保持，科学版本仍为0.5.0。

固定工件弱力的单位与取用已明确，尚不能据此证明自由工件承载、有效夹持、压力、释放或稳定性。整体项目未宣布完成。[下一步建议](NEXT_STEPS.md)是先固定最小物理任务规格及API能力缺口，再安排必要实现与真实运动／反力验证；本轮不启动该任务。
