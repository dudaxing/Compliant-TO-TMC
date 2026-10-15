# L-TREF1结果驱动的下一步：第三例保存交付

2026-10-15。第三wave原25目标循环已完成，本轮峰值13/loading1.20与首卸14/unloading1.15共4次HP80/120及原十五门全部通过。总力归一化误差约1.17e-15/1.30e-15，原门1e-11；PORT总切线约6.21e-17/4.87e-17，原门1e-10。没有证据要求先修力核或更改物理任务。

## 建议下一阶段一次贯通第三例外部消费

1. 复用默认summarize_saved_native_result，一次关联原第三例result、同25态viewer和本轮reference summary，写新linked_response，不回写原response。现有native_response.py的_reference动态处理indices13/14，会明确返回matched_partial、selected_reference_pass=true和matched_state_indices=[13,14]；全25态参考仍false。
2. 轻索引引用完整25态result/model/原response、viewer summary、本轮参考/误差JSON及两份执行收据。保原reference_scope文本（默认reader映射qualification为qualification_scope，不另造continuation）。链接三张变形/场PNG、GIF、收敛PNG及本次参考PNG，共6份既有媒体。
3. 复用consume_saved_lf.consume读取轻索引、linked response、result三个普通JSON，生成25行状态表和人工检查页。默认HF代码与消费算法均可保持；仅适配新阶段包装中的13/14、媒体数，把研究层副本的“五份媒体”标题改为“既有媒体”。不重做旧L-LINK1的16项变更测试、候选加载或默认安装。

源码静读依据：hf_repo/src/hf_eval/native_response.py:77–146动态校验选态，:149–190关联原viewer。其中:185为既有媒体读取原字节核SHA，未来新范围必须明确覆盖；不解码或重绘。原viewer关联四份媒体，轻索引补收敛和参考PNG两份。下一包装仅需普通元数据与必要媒体原字节读取，不需NPZ/gzip/F/T/HP/构模/求解。

可按已验证元数据交付量准备新的helper180/outer240秒、采样1GiB候选，一次执行、首错停、保实际部分记录；不沿用已关闭L-TREF1窗口。当前仅计划，包装尚未准备/执行，不声称API已关联。

## 随后供三设计统一对照

第三例先形成与L-USE1相同schema的25行表。三设计按(original_target_index,leg,d_mm)原顺序对齐75条原值/25组三方，保每态result/stateSHA及各自独参覆盖。不能把原LF的13/16或M历史分段参考冒认成第三例13/14；保M原失败与源码epoch。

对照R_input、q_out、材料/Hu/总工件作用、finite-ray及尖端距离、实体/自由介质J与实体应变，链接实际变形。几何/分区量从各自已有viewer普通summary取，不用consumer的global minimum_J代替；不插值补0.85/0.95mm卸载点，不加任意评分/正式排名或压力资格。新对照图另明确范围后执行。

全25态参考、全部切线列、连续压力/高阶总牵引、可移动工件/稳定性/释放、网格/域/参数收敛和HF5整体仍需各自功能与证据；按实际消费/比较结果逐步推进。
