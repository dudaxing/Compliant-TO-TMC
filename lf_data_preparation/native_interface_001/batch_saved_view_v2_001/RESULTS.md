# B-VIEW2：两例实际保存态图与关联响应

整体目标是独立 TMC 正向评价。本步让已有两例真实批量生产及各自独立参考的效果可直接查看：结构变形、力的作用位置、输入反力、输出位移、各输入节点位移及 J。图像来自本批量的实际保存态，不能用此前单例图代替。

用户既有可视化授权、两份实际 V2 worker/F3 PASS、双例保存闭合独审，以及 root 对原绘图/适配器/worker/installer 与独立静审的阅读，构成本阶段启用依据，见 [root 决定](ROOT_DECISION.md)。先一次标准库安装冻结245项绑定，再一次执行120／150秒、8 GiB的独立图卡；未复算、修复重试、force 或延期。

实际 worker PASS，helper9.775682300秒、采样RSS285,483,008字节；F3终态PASS、exit0、invocations1，outer11.255066000秒、采样树RSS283,164,672字节。两种采样方法分别记录，不混称OS硬内存上限。245绑定和两份原response字节不变。新增19个输出文件；每例4个实际状态、GIF4帧，没有插值。F/T/HP/求解/构模均为0。

| 末态数值（输入0.025 mm） | canonical | native_fine |
|---|---:|---:|
| 半模型输入反力 R（N） | 0.0052145920257 | 0.0037562787853 |
| 加权自由输出位移 q_out（mm） | 0.028603718459 | 0.023877824390 |
| 全积分点 minimum J | 0.996581260084 | 0.997535853825 |
| 输入节点数 | 3 | 5 |

root 已实际打开并检查两张PNG。左上为×1接受态与原轮廓、作用于模型的力箭头；上中明确为×40位移补图，不画力箭头；右上为反力与输出位移曲线。左下分别画3／5节点的实际位移和加权平均，节点可不同；中下为min J及残差／力平衡；右下给末态实际值及独立HP数值。颜色是单元积分点平均J，数值min J来自全部积分点，J不是压力。箭头倍率在同一例全部状态/分量间固定，两例各有自己的倍率；跨例比较力应读N值。

独立 [保存闭合审查](closure_review/saved_closure_review.json) PASS：347个原文件身份核对，原生产52／54、V1失败HP0、前次290项原文件身份及两份V2参考均不变；各响应/manifest/CSV与状态、模型、参考身份一致。直接读取媒体格式结构核到PNG2880×1680、GIF1680×770且4帧。审查只比较保存值、JSON/CSV和普通字节，不打开科学数组、不计算力学或重新绘图。实际视觉检查与该结构审查分别记录。

| 实际产物 | canonical | native_fine |
|---|---|---|
| 结构与数值PNG | [图](../batch_forward_001/run_001/view/canonical/native_mean_path.png) | [图](../batch_forward_001/run_001/view/native_fine/native_mean_path.png) |
| 四态GIF | [动画](../batch_forward_001/run_001/view/canonical/native_mean_path.gif) | [动画](../batch_forward_001/run_001/view/native_fine/native_mean_path.gif) |
| 可对照的数值CSV | [数值](../batch_forward_001/run_001/view/canonical/numeric_states.csv) | [数值](../batch_forward_001/run_001/view/native_fine/numeric_states.csv) |
| 新qualified响应 | [响应](../batch_forward_001/run_001/qualified_response_canonical.json) | [响应](../batch_forward_001/run_001/qualified_response_native_fine.json) |

新增响应各自关联自己的result、全部4态、独立参考和2个图链接，accepted/full-path reference均通过、views matched；原生产response/index保持原未关联记录，不倒填旧卡。各producer flag及全部切线列、接触/夹持、压力、HF5资格仍为false。

效果是本批量的「读取普通LF → 一次构模/求解/缓存保存 → 自有独立全态机械参考 → 自有实际图/响应」已经实际接通。此轮无工件、行程仅0.025 mm，q_out不是钳尖间隙；两设计与原生网格不同，不作网格收敛或排名。此前固定方体大行程加载/卸载及弱式工件力仍是独立历史证据，见 [物理功能矩阵](../../../docs/PHYSICAL_FUNCTION_PROGRESS.md)。HF5整体、一般有效接触、连续压力、自由体/摩擦及同设计网格/域验证仍未完成。

后续先核现有薄API承接固定方体大行程任务的具体实例缺口，复用已有task1.1路径、固定体入口和力摘要，按结果选最小功能步骤。新科学任务应另有明确任务及预算，不能重跑本阶段已闭卡。
