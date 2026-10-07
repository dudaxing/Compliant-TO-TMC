<!-- front proposal 2026-10-07; dynamic results require final actual records -->

# Compliant-TO-TMC：独立 HF 力学评估器

目标是复用 LF/N4 已形成的几何、任务与研究成果，建立能独立运行的有限变形 TMC 正向评估器，输出有单位和方向的结构变形、输入反力、工件力及误差范围，并逐步接回优化研究。后续开发统一在 `main`；origin 保持 `https://github.com/dudaxing/Compliant-TO-TMC.git`。

本轮依据用户意见让工件靠右并放大：中心 `(71,40)` mm、边长 `18` mm，计算对称下半体 `[62,80]×[31,40]` mm；刚体固定，右面贴到分析域边界。输入平均位移沿 24 个目标走 `0→1.2→0` mm，观察接近、变形和卸载。原 x71/side16 完整工况继续作为对照；旧 x72 与本任务默认初猜的失败保持原记录。

当前实际结果：{{CURRENT_VERIFIED_RESULT}}

{{ACTUAL_VISUAL_LINKS}}

NumPy 完整机械力、三分量切线与 CSC 组装、平均输入 KKT、固定工件与有序卸载、保存态的结构／力／J 可视化已经实现。新增可选 `initial_guess="port_projection"` 只改变初猜；默认路径、真实 KKT LU、反力预测和原验收门保持。15 项小模型测试已通过，大模型本轮资格以实际终态和新参考为准。

`R_input` 是半模型输入反力；工件下半体的 `Fy` 是另一个投影量；`2 abs(Fy)` 表示对称上下两侧法向力幅值之和。`q_out` 是原加权竖向端口位移，钳尖与工件有限面的间隙单独报告。压力分布与接触／夹持判据、匹配网格和介质参数、圆体／自由工件、HF5 耦合仍待实现或验证。

先读 [本轮目标、失败排查、真实效果和下一步](docs/WORKPIECE_ENLARGEMENT_20261007.md)、[当前状态](docs/CURRENT_STATUS.md) 与 [任意目录恢复](docs/RESUME_DEVELOPMENT.md)。根据上一工况的力、间隙与变形选择下一项功能实验。

---

## 历史记录

以下保留此前完整文字；其中“当前”“下一步”对应当时阶段。现在的结论和开发顺序以上方及本轮报告为准。

