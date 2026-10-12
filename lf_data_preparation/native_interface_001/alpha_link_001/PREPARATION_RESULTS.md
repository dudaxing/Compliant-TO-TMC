# M-ALINK1准备：将已有两态证据连到可读取的响应

整体目标是独立HF有限变形／TMC前向评价，为普通LF几何给出可核查的变形、反力和工件作用，供外部研究层使用。当前默认NumPy力、组装、切线、均值平衡、保存／读取、显示及保存态续算已实现；本轮最近补齐的是使用已有API组织已验证两态的参考和原图。

M-AREF1已实际PASS并发布main84c67e4：两个alpha5e−7保存态，4HP／原十五门，193.3503027秒、树RSS采样峰1278435328B；原source／数据保持，窗口关闭。新参考目前单独存档，原response的not_provided历史状态未改。

本轮只读源码／普通JSON及stat，完成精确输入与资格语义审阅，并准备薄关联候选、卡和资源合同。未调用API、HF函数或测试；未读取图片原字节／像素、NPZ或科学gzip，未产生新response／索引／图。准备不等于执行PASS。

现有reader已经适配continuation。无需改默认源码；将来一份linked_response和轻索引将关联child0／1（原13／14）、同两态4HP和原三PNG／两帧GIF。full_path_reference_pass=true只表示child短段参考匹配；full_original_path_reference_pass和path.full_original_path_completed仍false，target_response=null、父failed/time_limit和原producer flags保持。原view reference_available=false不回写，不声称原图已绘制新HP结果。

| 原已保存且经M-AREF1方程／投影核对的值 | 峰值1.20 mm | 首次回撤1.15 mm |
| --- | ---: | ---: |
| 输入反力R（N） | 0.37865427196005513 | 0.3470376815403639 |
| 下半工件total Fy（N） | 0.12492121630032427 | 0.10671287553103108 |
| 输出均值q_out（mm） | 1.016934534302024 | 1.0153174242325562 |

这些是原保存数值，不是本轮新计算；工件弱式合力不授连续压力或有效夹持资格，两端点不构成完整卸载曲线。

![原两态实际变形GIF；未新绘图](../saved_continuation_001/run_001/view/resumed_alpha_half/actual_states.gif)

[已有实际参考与完整结果](../alpha_reference_001/RESULTS.md) · [本次具体卡](M-ALINK1_CARD.md) · [精确输入边界](author/INPUT_SCOPE_REVIEW.md) · [reader语义取舍](author/SOURCE_SCOPE_AND_FLAGS_REVIEW.md)

M-ALINK1拟一次180／240秒、采样8GiB，只关联普通JSON和现有媒体身份；原门、物理条件和科学结果保持。首错停，无重试／修复重跑／延期／force或新数组／F／T／HP／平衡／图。新的直接批准前不执行。

仍未完成：父子全路径参考覆盖、连续材料＋Hu总压力／有效夹持、一般LF输入可靠性、移动／摩擦或其他形状的完整验证、网格／域／参数稳定性、独立全部切线列及HF5。最近不重复长路径或扫alpha；先让已有证据通过API可用，再依据实际结果规划。
