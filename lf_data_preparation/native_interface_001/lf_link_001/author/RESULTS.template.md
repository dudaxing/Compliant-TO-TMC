# L-LINK1 已完成：选定独立参考接入公共摘要

2026-10-15（Asia/Seoul）08:27:21–08:27:22。直接人工批准“批准按 L-LINK1 卡执行”后，按 main `4fd70556402347c73029cf7070217efaf7a4ea13` 的[执行卡](L-LINK1_CARD.md)只运行一次。实际工具 terminal `ba13f2`、exit 0，outer／helper 均 PASS；单文件摘要候选已安装。源准备文档中的“待批准／未执行”是保留的历史。

## 目标、功能与取舍

整体目标是让独立 HF 读取外部 LF 普通几何，在明确物理任务下计算有限变形／TMC响应、固定工件弱式合力和实际变形，再返回可供研究层使用的摘要。HF 不包含拓扑优化；MPM 尚未实现。本次推进的是已有数值结果和独立参考的公共接口消费能力。

L-FWD1 已从零完成25目标 `0→1.20→0 mm` 与25个接受保存态。L-REF1 已核 loading 1.20 mm／index13、unloading 1.05 mm／index16，两态共4次 HP80／120，保持原十五门。旧摘要只接受全部态参考，因此无法识别这个真实2／25参考。现已在 `_reference` 中增加严格的选定态匹配和显式覆盖字段，函数签名及其余源码字节保持；没有重算力、切线、平衡或参考。

## 实际完成和证据

固定16个标准库元数据测试方法全部通过，私有 `_reference` 调用23次。其后对真实数据调用公共摘要一次，response、轻索引各写一次，全部通过才安装一次 `hf_repo/src/hf_eval/native_response.py`。原文件 SHA `53bee087509f780ec5a62dae5b39a067e5f0df38f6fd7cc47311766ab3e2f14b`，实际安装 SHA 与测试／真实调用候选相同，为 `346a97b30f675ccf063de1720002f936adf90011e69231edd89e776ba4e70eaa`。只有此元数据源码改变，力学源码和旧结果保持。

新[关联响应](run_001/linked_response.json)返回：

| 字段 | 实际结果 |
|---|---|
| 生产路径 | success，25接受态，输入目标完成 |
| 独立参考状态 | matched_partial |
| selected_reference_pass | true |
| matched_state_indices | [13, 16] |
| 覆盖 | 2／25，已有4HP |
| accepted_reference_pass／full_path_reference_pass | false／false |
| views | matched，原3PNG／25帧GIF |

原科学资格字段保持 false，原 producer response／reference 没有重写。新[轻索引](run_001/light_index.json)包含同一result、model、task／geometry身份、两態参考及五份既有媒体。公共摘要中的共同物理值与原响应逐项相同；原响应有其自身 invocation／evaluation_elapsed 等附加字段，新摘要不声称全文完全相同。

实际测试用时0.5875975秒，helper封存时计时1.0706764秒；child实际终止墙钟1.3065472秒，outer共1.9210903秒，tree RSS峰值35,913,728 B（约34.25 MiB）。均在测试60秒、helper180秒／outer240秒、采样8 GiB额度内。helper封存67份普通输出，其中63份测试fixture，另有测试摘要／日志、关联响应和索引。封存为 `complete_inside_original_helper_window`，全部65不可变绑定保持。

没有重试、修复重跑、延期、force或回滚。新NPZ／科学gzip／CSV读取、媒体解码、求解、F／T、HP、构模、绘图和像素检查均为0；零新力学的证据来自固定纯元数据源码、导入来源检查与执行计数，不声称用hook监控所有力学调用。五份旧媒体的原字节身份只在批准窗口内核对；闭窗审阅与交付只继承既有封存身份和stat。

## 可观察的物理效果

这些数值来自原普通保存结果，本次只关联：

| 状态 | 输入反力 R（N，半模型） | 加权输出位移（mm） | 下半工件总 Fy（N） | 材料 Fy（N） | Hu Fy（N） |
|---|---:|---:|---:|---:|---:|
| loading 1.20／index13 | 0.2436576873 | 1.0075199350 | 0.0585119885 | 0.0577945794 | 0.0007174091 |
| unloading 1.05／index16 | 0.1700172632 | 0.9918014911 | 0.0077474087 | 0.0069385038 | 0.0008089049 |
| 回零／index24 | 2.2861e−25 | −9.3544e−25 | −1.1990e−27 | −2.9107e−28 | −9.0797e−28 |

峰值下半体 Fx=−0.0006742601 N；两侧法向幅值和0.1170239770 N，完整镜像净合力为(−0.0013485202,0) N，含义不同。工件力是固定体弱式合力，含材料和Hu，尚不能命名为连续接触压力或正式有效夹持力。q_out是加权端口位移。峰值节点窗口底距0.0027672909 mm、minJ=3.77508e−5；前者仅是原栅格节点诊断，后者需要结合场图人工检查，均不自动赋予接触或稳定性资格。

物理条件仍为0.5 mm网格、84×40 mm下半域、13440单元／27378DOF、E=1 MPa、nu=0.3、平面应变、厚20 mm、gamma=1e−6、alpha=5e−7、Lr=80 mm；固定正方形工件中心(71,40) mm、边长18 mm。

五份既有可视化供人工检查，本卡不补画或解码检查：

- [结构变形与响应曲线](../lf_forward_001/run_001/view/comparison.png)
- [距离与力](../lf_forward_001/run_001/view/distances_forces.png)
- [峰值实际场](../lf_forward_001/run_001/view/peak_fields.png)
- [全部25保存态实际变形GIF](../lf_forward_001/run_001/view/lf_fine_forward/actual_states.gif)
- [两态独立参考误差](../lf_reference_001/run_001/reference/reference_observations.png)

## 审查、恢复与下一步

实际[启动回执](link_launch.json)、[helper回执](run_001/execution_receipt.json)、[16项测试记录](run_001/tests_stdout.txt)、[根实际终态确认](author/root_terminal_confirmation.json)与[独立终态审阅](author/independent_terminal_review.md)区分静审、测试、真实关联、安装及后续发布。普通根收尾最初把67份封存输出计数序列化为67个1的数组，原记录保留；当前确认中明示更正为实际映射len=67。没有改变任何卡内执行输出、源码或验收结果。

前置状态和恢复文档完整保留源提交4fd7055的原字节连续一次，并在顶部给出当前闭卡状态。开发继续在main，origin保持 `https://github.com/dudaxing/Compliant-TO-TMC.git`；推送／独立恢复结论以真实交付回执为准，本结果写入本身不宣称已推送。

下一步应优先让外部研究层消费此紧凑响应及索引，明确任务、几何、力的含义和2／25参考覆盖；以实际消费结果决定是否需要补其余保存态参考或跨几何比较，避免无目的重算本完整路径。若新增独立参考／科学计算、跨几何任务或资源范围，另行给出具体计划。完整25态独参、全部切线列、压力／有效夹持、自由工件释放、摩擦、稳定性、一般LF／HF5整体、正式标签／排名和MPM仍未完成。
