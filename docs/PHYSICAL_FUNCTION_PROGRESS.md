# 当前功能矩阵补充：真实薄API小任务已闭合

HF仍仅正向评价，不含优化器。此前固定方体2/4mm域完整周期物理证据保留；本次新入口无工件1µm任务2态、4新HP及保存图完成，范围见[实际报告](../lf_data_preparation/native_interface_001/real_forward_001/RESULTS.md)。

| 功能 | 当前已验证 | 仍未完成 |
|---|---|---|
| 输入与域 | 既有普通native几何/task，经真实API一次构模/求解/保存；原边界、任务ID和默认模式保持 | 同设计匹配网格/域收敛；其它新模型自身资格 |
| HF5与易用 | 薄API/CLI、21项首次纯功能验证、4旧摘要；另本次真实coarse两态路径及同结果参考/视图身份闭合 | 同任务比较、小批量、重复性合同与HF5整体 |
| 力与显示 | 新例半模型R、加权q_out、J/Hu及×1/标明×1000图；没有工件，工件力null | 新例不授夹持/接触/压力、全切线列或自由工件资格 |
| 能量范围 | 新例complete保存辅助材料能量；旧固定工件mechanical卡不计算该辅助项 | 独立能量验证；不得从材料能量缓存扩展物理资格 |

未改变匹配网格、压力/接触定义、圆体自身完整任务、自由体、摩擦和统一E源码推论的原边界。下面机械模式说明只对应此前固定工件卡，与本次complete不同；当时“后续科学卡尚未执行”亦仅历史。

---

以下完整原字节为8330b821阶段功能矩阵历史；当前变化以上方为准。

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
