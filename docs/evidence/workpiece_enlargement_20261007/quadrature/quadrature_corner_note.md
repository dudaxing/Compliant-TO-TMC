# 九点积分角点检查：撤回记录

2026-10-07，原计划为 `medium_geometry_001` 增加 24 次保存数组的第三介质角点观察。源码复核表明，现有九点 Simpson／Gauss–Lobatto 积分已包含四个角点，原正 J 门检查全部九点。因此，“最小 J 仅覆盖内部积分点”的前提不成立，根 Agent 已在建卡前撤回该计划。

独立源码依据、P26 原代码与当前源码 SHA、点序及模型积分声明见 [quadrature_corner_source_review.json](quadrature_corner_source_review.json)，SHA-256 为 `55ae6bd86d695f5b7d248f7a86d285b2e3cf639d7464daaae7da62dc0e346bac`。

作者未创建该卡、helper 或第三介质候选目录，未冻结协议或启动执行；新增数组读取、几何观察、构模、力、切线、求解、HP、几何 API 与渲染调用均为 0。正式仓库未改写。完整活动记录见 [quadrature_corner_note.json](quadrature_corner_note.json)。

本次仅更正检查依据，已有生产、参考与实体／工件几何证据保持原样；不增加接触或全局自重叠资格。
