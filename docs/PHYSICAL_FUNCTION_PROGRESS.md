# HF物理功能进度：当前闭卡范围

HF复用LF/N4研究成果，提供独立正向评价，不含优化器。外部研究层负责比较、优选，HF5评价接口尚未完成。

| 功能 | 已实现/本次可查看 | 待实现或未取得资格 |
|---|---|---|
| 结构作用与变形 | 固定side18方体、2/4mm域、平均输入/自由输出、加载/回零、×1结构/GIF | 更多任务自身证据；自由体释放/稳定性 |
| 力及其位置 | R、固定下半工件总/材料/Hu(Fx,Fy)、holding及节点力；完整力、平衡和PORT方向切线作用的新参考 | 连续压力、有效接触/夹持定义、全切线列、摩擦 |
| 距离与场 | 有限面距离、保存J/Hu、binary64 Green主应变；原9点Lobatto含角点J门 | signed penetration、一般包含/自身重叠、应变/应力HP；场图不是压力 |
| 输入与域 | 自包含LFv2/明确task、Q1原生网格、HF派生介质域；82→84旧物理子域保持 | 同设计匹配网格、新入口真实任务尚待执行；新模型不继承旧资格 |
| 一般夹持 | 固定方体完整评价；固定圆体单元覆盖入口存在 | 圆体自身完整边界/平衡、自由刚体平移/转动/力矩、摩擦 |
| 统一E尺度 | 严格同branch、无独立力尺度的方程缩放推论 | 尚无本项新实验；降低E不作为改善贴合证据 |
| HF5与易用 | 薄一次API/CLI及保存摘要已实现；21项JSON/模拟集成通过，4份摘要可审，LF/N4研究层保留 | 新API真实平衡路径、同任务小批量和完整HF5重复性合同 |

R为半模型输入反力；下半工件Fy为固定体弱式on-body力，holding反向。2|Fy|为镜像法向幅值和，装配净力为(2Fx,0)。q_out为加权竖向端口位移，不是tip gap。Hu场最大值与Hu力分量分开记录。当前机械模式不计算辅助材料能量，不表示旧能量入口不存在。

两域结果不单独证明域/网格收敛。看同方向/原目标全曲线、材料/Hu分量、绝对量及距离，再选择一次物理敏感性或同设计细网格；同时推进薄正向接口，不重写LF/N4优化器。后续科学卡尚未执行。

统一E缩放是有条件的源码方程推论，尚未做本项实验：同几何/网格/厚度、位移约束与固定工件、同静态解分支，固定ν/γ/α/Lr，k_out=0且无未同比缩放的独立外载时，E→cE（c>0）理论上保持位移/贴合与q_out，机械力和反力乘c。物理刚度块缩放，但整个KKT矩阵不同比例缩放；数值舍入/解分支和迭代次数不保证相同。统一降低E不能据此宣称固定工件位移控制下更贴合。

[统一E源码说明](evidence/workpiece_enlargement_20261007/right_margin4_source_context/closure_001/009.md)；[HF5薄接口事实与未实现提案](evidence/workpiece_enlargement_20261007/right_margin4_source_context/closure_001/011.md)。

[完整报告](WORKPIECE_ENLARGEMENT_20261007.md)；[进度](evidence/workpiece_enlargement_20261007/right_margin4_progress.json)；[结构与力](../functional_views/right_margin4_20261007/complete_001/view/comparison.png)；[距离与力](../functional_views/right_margin4_20261007/complete_001/view/distances_forces.png)；[J/Hu/Green](../functional_views/right_margin4_20261007/complete_001/view/peak_fields.png)；[4mm实际动画](../functional_views/right_margin4_20261007/complete_001/view/right4col/actual_states.gif)。

[薄评价接口用法与实际验证范围](NATIVE_EVALUATION_INTERFACE.md)。
