# M-AREF1 实际结果：两态独立参考PASS，窗口已关闭

整体目标是独立HF有限变形／TMC前向评价：读取普通LF几何，在明确任务下给出实际变形、反力及可解释的工件作用，供外部研究层比较。HF不优化、不调用dmftd，MPM暂不实现；main、既定origin和science0.5.0保持。M-INTEGRATE1已安装默认保存态续算，有限25项兼容测试通过。

本卡为什么做：新alpha=5e−7的峰值／首次下降已保存，但旧alpha的48HP不能移植。复用已验证数学，在实际两个接受态上补独立力／声明方向切线／工件投影证据，使后续API能够区分原生产成功、独立参考和物理夹持资格。本卡没有重做加载／卸载平衡。

2026-10-12（Asia/Seoul）直接批准后唯一session54727真实terminal exit0；outer PASS、一次启动、stop=None、48不可变bindings保持。outer 193.35030270001153秒，child终端墙钟192.32251390002784秒，helper 191.6140807000047秒；树RSS采样峰1278435328B、helper峰1269972992B，均在900／960秒、8GiB内。实际4HP开始／4完成、2机械态／2工件态、161495项运行检查。没有重试、修复重跑、延期、force、新生产F／T、模型、平衡、测试、API关联或绘图；未用时间不构成新许可。

每态覆盖13440单元／27378 DOF、322560局部三分量力条目、322560局部三分量方向作用条目，以及860160个总保存张量系数的CSC组装身份。HP80／120各一次，Decimal3000全局散射并trap Inexact；原十五门、原分母／floor保持。实际PORT方向由原五节点b_in给出，固定分量0、deltaR=0。完整CSC组装身份和单PORT解析方向比较不等于独立验证全部切线列。

原执行索引13／14保留在raw accepted_013／014科学summary；顶层只复制元数据到child0／1，保留原索引、state／descriptor身份、leg与continuation_anchor。子0为原1.20 mm峰值锚点，子1为原1.15 mm首次下降。原result／response／缓存及图件不改，父M-ALPHA1 NOT_PASS／14加载态／time_limit保持；不拼接为原一次完整路径通过。

| 已产普通summary中的归一化检查 | 峰值1.20 mm | 首次回撤1.15 mm | 原门 |
| --- | ---: | ---: | ---: |
| 全局总力 | 9.3418e-16 | 9.8062e-16 | 1e−11 |
| 全局材料力 | 3.1860e-16 | 3.3003e-16 | 1e−9 |
| 全局Hu力 | 2.0390e-16 | 2.3484e-16 | 1e−9 |
| PORT总切线作用 | 5.0863e-17 | 4.6972e-17 | 1e−10 |
| PORT材料切线作用 | 8.0647e-17 | 6.0568e-17 | 1e−9 |
| PORT Hu切线作用 | 1.9929e-16 | 2.8249e-16 | 1e−9 |
| CSC总方向作用 | 5.7065e-17 | 7.8673e-17 | 1e−10 |
| KKT自由力方向作用 | 5.6642e-17 | 7.8957e-17 | 1e−10 |
| 独立相对平衡残差 | 9.6141e-13 | 4.5848e-12 | 1e−8 |
| 全局总力HP80／120一致性 | 7.0627e-77 | 7.5974e-77 | 1e−40 |

数值为报告原值的显示舍入；完整Decimal、原分母与限值见下方两个原summary。误差使用原全局／分量规范，不是标量工件力的百分比。两态均值、固定、全局平衡及原局部门也由继承原方法核对；J/F/Hu rounded记录仍仅为原诊断，没有新增stress-HP／独立Hu数组门或能量梯度资格。机械辅助材料能量保持not_evaluated／unqualified／absent，独立解析材料能量仅归档。

| 原实际保存值（同两态，未新绘图／积分） | 峰值1.20 mm | 首次回撤1.15 mm |
| --- | ---: | ---: |
| 输入反力R（N） | 0.37865427196005513 | 0.3470376815403639 |
| 输出均值位移（mm） | 1.016934534302024 | 1.0153174242325562 |
| 下半工件total Fy（N） | 0.12492121630032427 | 0.10671287553103108 |
| 下半工件material Fy（N） | 0.12405713468784063 | 0.10585842148635459 |
| 下半工件Hu Fy（N） | 0.0008640816124836284 | 0.0008544540446764915 |
| 尖端到底面有限采样间隙（mm） | 0.0009696602064828141 | 0.0012850478242718566 |

输入反力是原保存乘子，工件数值来自原保存视图摘要；本次独立方程与aa86 signed total／material／Hu投影检查已实际完成。它们说明此固定方形任务在首次回撤时作用减小，不构成连续压力、有效夹持力或完整卸载曲线。工件固定、center(71,40) mm、side18 mm；E1MPa、ν0.3、厚度20mm、h0.5mm、gamma1e−6、alpha5e−7保持。

![原两个保存态实际变形GIF，原字节复用](../saved_continuation_001/run_001/view/resumed_alpha_half/actual_states.gif)

[原位形／反力对照图](../saved_continuation_001/run_001/view/comparison.png) · [原距离／工件作用图](../saved_continuation_001/run_001/view/distances_forces.png) · [原峰值场图](../saved_continuation_001/run_001/view/peak_fields.png)

[实际顶层参考](run_001/reference/summary.json) · [原13峰值科学summary](run_001/reference/accepted_013/summary.json) · [原14回撤科学summary](run_001/reference/accepted_014/summary.json) · [helper终态](run_001/reference/lifecycle.json) · [outer终态](reference_launch.json) · [直接批准](author/direct_human_reply.json)

边界：只核这两个新alpha接受态及声明方向。未给父14加载前缀、完整原路径、全部切线列、连续总压力／有效夹持、移动／摩擦／其他形状完整验证、网格／域／参数稳定性或HF5升级资格。原producer资格及response的not_provided保持；新参考目前独立存档，尚未运行API关联。后续据本次结果最近应关联这两态现有参考与原图，先做好子段范围说明，不重做平衡／HP或扩展参数。
