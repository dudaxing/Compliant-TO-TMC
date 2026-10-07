<!-- front proposal 2026-10-07; dynamic results require final actual records -->

## 当前独立 HF 功能与接口

HF 复用 LF/N4 的普通几何与物理任务，独立求解固体／第三介质有限变形、机械力及加载—卸载。NumPy 机械入口、材料/Hu/总力、三切线和 CSC、平均输入 KKT、固定工件、保存态几何与全节点力已接通；最新实际结果为：{{CURRENT_VERIFIED_RESULT}}

{{ACTUAL_VISUAL_LINKS}}

本轮仍用 E=1 MPa 的原夹持器，固定方体中心 `(71,40)` mm、边长 `18` mm，对称下半体 `[62,80]×[31,40]` mm；右面贴分析域边界，按 24 目标执行 `0→1.2→0` mm 平均输入探索。生产结果、独立参考范围、实际成本和图见 [本轮报告](../docs/WORKPIECE_ENLARGEMENT_20261007.md)。

`solve_native_mean` 新增可选关键字 `initial_guess="port_projection"`；默认仍为 `"tangent"`。示例接口组合是 `response_mode="mechanical", tangent_mode="chunk256", initial_guess="port_projection"`，并显式提供任务、目标和 settings。端口投影沿前一 fluctuation 分配所需平均增量，保留真实 KKT LU 的反力预测和后续 Newton／Armijo／J 门；自由输入节点无需相同位移。15 项小模型测试已通过，默认回归保持。源码见 [native_mean.py](src/hf_eval/native_mean.py) 与 [split_displacement.py](src/hf_eval/split_displacement.py)。

`q_out` 是 `.25 uy(80,28)+.5 uy(80,29)+.25 uy(80,30)` mm。`R_input` 是半模型输入端反力，固定下半工件 `(Fx,Fy)` 为弱式合力；镜像完整体净力是 `(2Fx,0)`，`2 abs(Fy)` 是双侧法向幅值和。工件材料/Hu/总力与节点力分别保存；有限面间隙和 ×1 钳尖变形由保存几何观察。压力、接触／夹持判据、应力 HP、辅助能量及全切线列仍有各自未完成范围。

后续按本轮结果实现接触／压力定义，匹配网格和 gamma，再探索圆体／自由工件与 HF5 接口。开发统一在 `main`；[跨目录恢复](../docs/RESUME_DEVELOPMENT.md) 保持原记录和来源。机械模式省略辅助材料能量，默认 complete/full 接口保持原合同。

---

## 历史记录

以下保留此前完整文字；其中“当前”“下一步”对应当时阶段。现在的结论和开发顺序以上方及本轮报告为准。

