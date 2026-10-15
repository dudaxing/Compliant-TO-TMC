# L-USE1 已完成：外部研究层可消费全部25保存态

2026-10-15（Asia/Seoul）。用户直接批准后，只执行一次消费示例，实际tool终态 `27c8eb`／exit0，outer与helper均PASS。原生产力学、结果、参考、媒体和hf_repo实现源码保持。

## 目标、实现与理由

整体目标是独立HF读取LF普通几何，在明确任务下给出有限变形/TMC响应、固定工件弱式合力与保存变形，供外部研究层使用；HF不优化、不调用dmftd，MPM未实现。L-LINK1已关联原25态路径与两态4HP，但紧凑响应只展开峰值/终点，缺少全过程和卸载1.05 mm数值快照。

本步新增一个[纯标准库示例](example/consume_saved_lf.py)，通过显式repo/index/output读取原light_index、linked_response和result三JSON，各一次。一次外部cwd进程调用同一CLI main与参数解析、consume一次；没有另外运行第二次独立CLI或测试。实际cwd为 `D:\hf-native-workpiece-api-author-20261015\LF_USE_execution_cwd_001`，位于正式仓库之外。新示例/两个包装在批准后编写，由protocol逐文件SHA冻结；c9ca9a2只表示继承基线，不声称新字节原已在该提交。

[25态JSON表](run_001/states_table.json)保留接受行、原目标编号、state SHA、加载/卸载、输入反力、q_in/q_out、minJ和材料/Hu/总合力向量，另保原物理、选项、身份、资格和五媒体记录。[人工检查页](run_001/REVIEW.md)展示全25行与五份既有图/动画链接；数值显示舍入，原浮点在JSON中保持。接受序号来自enumerate(result.states)，原反力字段为R_input。

## 实际效果

| 保存态 | 输入反力R (N) | 输出端口位移 (mm) | 下半工件总Fy (N) | 已匹配参考 |
|---|---:|---:|---:|---|
| loading1.20/index13 | 0.243657687269 | 1.00751993498 | 0.0585119884831 | 是 |
| unloading1.05/index16 | 0.170017263171 | 0.991801491053 | 0.00774740870419 | 是 |
| 回零/index24 | 2.2860558e-25 | -9.3544073e-25 | -1.1990387e-27 | 未覆盖 |

这些全为原保存值的投影，没有重新求力。全部25目标生产完成与仅2/25匹配参考分别保留；其余23行“未覆盖”不等于数值失败。原matched_partial、selected_reference_pass=true，accepted/full_path参考通过仍false，原producer flags保持。工件值含材料与Hu，是固定下半体弱式合力，不能当作连续压力或正式有效夹持力；q_out不是表面间隙，minJ沿原全局保存含义。没有新的正式标签或排名。

实际计数：{'consumptions_started': 1, 'consumptions_completed': 1, 'json_reads_started': 3, 'json_reads_completed': 3, 'table_writes': 1, 'review_writes': 1}。helper封存计时0.791752秒，child实际终止2.483558秒，outer共3.755071秒；采样child树RSS峰值29790208 B。原额度helper120/outer180秒、采样1GiB满足；采样/合作停止不是OS硬限额。两普通输出在原helper窗口内完成SHA/大小封存，真实回执另存。没有重试、修复重跑、延期、force、回滚或删除。

新增HF摘要/API、单测、F/T、HP、求解、构模、绘图、NPZ/科学gzip/CSV、媒体字节/解码/像素检查均0。这里的三个输入JSON读计数属于消费示例；准备/包装/收尾还读取普通协议、授权、回执和新输出。零新科学依据固定源码、执行路径和实际计数，不声称动态机械hook监控。五旧媒体仅保身份/路径，闭窗交付使用继承封存与stat。

## 复用、记录与后续

可在任意cwd用本机Python调用下列相同入口；这是复用示意，不表示本卡执行了第二次：

```text
<Python> <repo>/lf_data_preparation/native_interface_001/lf_saved_consumer_001/example/consume_saved_lf.py --repo <repo> --index lf_data_preparation/native_interface_001/lf_link_001/run_001/light_index.json --output <全新目录>
```

示例针对本次固定工件保存字段，不宣称支持任意机构/缺失工件字段/未知schema；输入与输出路径按显式repo解析。JSON媒体路径仍为repo_relative，检查页链接相对自身位置，因此恢复到其他目录后不依赖原D盘路径。原科学值和scope不因消费而升级。

[具体卡](L-USE1_CARD.md)、[helper真实回执](run_001/execution_receipt.json)、[outer真实回执](use_launch.json)、[根工具终态](author/root_terminal_confirmation.json)与[独立实际审阅](author/actual_review.md)区分源静审和真实运行。两front完整保留c9ca9a2原raw历史连续一次。推送/独立恢复结论以真实交付回执为准，本文写入本身不宣称已推送。

下一步应根据这份全路径表选择一项必要工作：需要整条路径独参时仅补其余23保存态；跨几何比较前先明确共同任务、网格/域政策和逐例参考。当前不重做生产路径。压力/有效夹持、全部切线列、释放/摩擦/稳定性、一般LF/HF5整体与正式标签/排名仍未完成。
