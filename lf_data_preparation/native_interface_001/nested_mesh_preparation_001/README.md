# 同设计细网格接口准备记录

2026-10-09（Asia/Seoul）。状态：**源码、协议已准备，尚未数值执行**。没有派生几何、细网格模型、力学结果或新PNG。

项目目标是独立有限变形／TMC正向评估器。本次接续已完成的真实API24态与保存显示，准备同一结构h1→h0.5的网格敏感性研究。已有两份不同LF设计不能充当同设计粗细网格对照。

本轮新增[nested_geometry.py](../../../hf_repo/src/hf_eval/nested_geometry.py)，提供固定2×2四掩码细分接口；原几何、构模、力、切线、求解及参考入口保持。每个父格的实体/设计/被动实体/被动空域复制到四个子格，连续边界、厚度、半模型和历史LF/右域padding来源保存。新来源明确为HF派生网格，`native`仅选择这个供应的网格。

[准备脚本](author/prepare_nested_model.py)复用现有构模和存储，直接比较物理字段、材料、父子节点与Q1算子尺度；用物理方框/附着节点独立核对工件、支持和固定集合，并用仿射场核对端口积分。保存字段与未变形三联图属于同一个小构模阶段。源静审修正了算子尺度、节点嵌入、工件单元独立选择和存储档身份等证据缺口，没有执行数值试验。

| 项目 | 本轮实际情况 |
|---|---|
| 来源与接口静审 | [schema_review](author/schema_review.json) |
| 候选数学/字段静审 | [candidate_review_final](author/candidate_review_final.json)，通过 |
| 资源/包装/文档静审 | [resource_document_review](author/resource_document_review.json) |
| Python语法 | 3个候选/包装源AST解析，无模块导入 |
| 派生数组、构模、求解、HP、绘图 | 尚未执行，全部0 |
| 粗网格保存身份关系 | [实际353文件核对及独立抽查](../workpiece_identity_001/RESULTS.md) |

预期h0.5为13,440单元、13,689节点、27,378 DOF；同2mm物理端口应有5节点及归一化梯形权重。它们当前是静态预测，实际结果需[M-PREP1](M-PREP1_CARD.md)的一次构模检查证实。原API响应与qualification flags未改变；源码审阅不授予细网格力学或接触资格。

资源静审在执行前发现初稿缺少最终报告/哈希整理后的完成检查点，已补齐并更新候选协议身份。初稿[source_preparation_receipt](author/source_preparation_receipt.json)和[candidate_review](author/candidate_review.json)保留当时哈希；当前身份以[final_source_preparation](author/final_source_preparation.json)及最终两份静审为准。这是未授权草稿的静态修正，没有失败数值运行或重试。

具体[协议](protocol.json)绑定17份源、卡和父输入；新180秒helper／240秒outer／采样8GiB窗口待明确批准。通过后展示真实未变形网格图并独立核对模型，再依据构模规模和既有h1成本准备细网格完整加载—卸载卡。其平衡、参考、保存观察和物理比较不在本卡内，两网格只报告敏感性。
