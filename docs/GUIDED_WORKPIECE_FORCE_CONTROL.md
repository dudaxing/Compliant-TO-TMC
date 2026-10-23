# 导向轴向力控制：准备入口

2026-10-23。当前仅完成L-CTIPFLOADPREP1任务规格、拟议接口和有限小模型方案，**没有实现或执行力控**。已有导向位移探针仍是给定q、输出Q；新任务拟给定绝对半模型外载P，求未知工件q，同时保持机构平均输入及导向uy／转角约束。

半模型N已含源厚度，P_full=2P_half，q不倍增。原q0有非零预载，首外载必须匹配fresh初态，不能暗设零或修复状态。新增工件合力残差与原自由平衡分开验收；旧mm步长不能作为N步长。

完整设计与状态：

- [准备说明与示意](../lf_data_preparation/native_interface_001/lf_circle_tip_force_control_preparation_001/PREPARATION.md)
- [物理／数学／验收规格](../lf_data_preparation/native_interface_001/lf_circle_tip_force_control_preparation_001/TASK_SPEC.md)
- [API与结果schema草案](../lf_data_preparation/native_interface_001/lf_circle_tip_force_control_preparation_001/API_DESIGN.md)
- [有限小模型方案](../lf_data_preparation/native_interface_001/lf_circle_tip_force_control_preparation_001/SMALL_MODEL_VALIDATION.md)
- [下一候选实施卡（未批准／未冻结）](../lf_data_preparation/native_interface_001/lf_circle_tip_force_control_preparation_001/L-CTIPFLOAD1_CARD.md)

本轮不改默认固定工件、原位移probe、CLI或native_response。原结果与资格保持；新受限力控即使将来通过，也不自动授纯接触、承载极限、释放或稳定性资格。
