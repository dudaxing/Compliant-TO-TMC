# 两例新的独立参考卡

依据已经授权的原生接口实现、独立参考对比与可视化工作，按实际结果逐步推进。新生产终态已经 PASS，原生产卡已关闭，不重复求解。

## canonical

实际生产接受态 N=4（0、0.005、0.010、0.025 mm），执行原 Audit 的全部实际态循环，各态独立计算 80/120 精度各一次，共 8 次新 HP。helper 240 秒、outer 270 秒，采样 RSS 8 GiB。一次执行、首错停止、无修复、无重试。具体身份与全部输入源以 `reference_contract_canonical.json` 和 `reference_protocol_canonical.json` 为准。

## native_fine

仅在 canonical 新参考终态通过后冻结和执行。实际 N=4，同样需要 8 次新 HP；helper 900 秒、outer 960 秒，采样 RSS 8 GiB。一次执行、首错停止、无修复、无重试。具体身份以该例单独 contract/protocol 为准。

## 不变部分与证据边界

原 28 份运行源与 5 份参考数学源不变；原 Audit.run/run_state、80/120 精度、散射、端口方向切线计算和验收门直接继承。旧参考只估计成本；旧模型、任务、方向、lift 只核对结构身份，不继承数值资格。两例新生产 result/response 与 batch index 保持原始字节。

原始 summary 保留，另存 qualified_summary 仅修正案例、任务行程与范围说明。若写出数学 summary 后发生资源或终态失败，该 summary 不能单独赋予资格；必须同时检查新参考 execution_receipt 与外层 F3 launch。

本卡验证无工件 0.025 mm 完整机械 TEST 的全部实际态与端口方向切线；不赋予接触、夹持、压力、能量、全切线列、网格收敛、排序或 HF5 资格。两种 LF 设计与网格不同，不能直接解释为同一设计的网格收敛对照。
