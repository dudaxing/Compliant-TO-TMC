# M-REF1 实际结果：源码归档路径失败，HP未开始，卡已关闭

2026-10-09（Asia/Seoul）。用户明确“批准按 M-REF1 卡执行”后唯一一次运行；**NOT_PASS，首错停止，窗口已关闭**。源码基线 main `e372eca264b18e1e70fd6d3f153505ff257ed6ca`。187 个原字节绑定保持，未修复重跑、延期或force。授权是执行前历史记录，冻结卡/协议中 prepared 字样保留原身份；实际终态以本页及 launch/lifecycle/summary 为准。

## 目标、工作与实际效果

整体目标仍是读取 LF 普通几何的独立有限变形/TMC 正向评估器，不含优化或dmftd。本步原计划用冻结 B850机械参考与aa86工件投影，检查M-CYCLE1细网格全部24保存态／48次新HP80/120及原15项严格门，区分数值实现误差和已显示的两网格敏感性，不重新求解加载—卸载。

本次执行只到新包装的源码归档阶段。`load()`第84行`destination.parent.mkdir`创建首个B850依赖的归档目录时遇到`FileNotFoundError [WinError 3]`，第85行源码复制尚未执行。**HP开始/完成0/0，接受机械态0、工件态0、states=[]**；模型NPZ尚未读取，run_state及工件参考尚未调用。`checks_completed=1`是合同范围/资源/门声明一致性检查，不能说原15数学门已执行或失败。

本卡没有产生独立力、切线或平衡参考；既有M-CYCLE1生产结果和M-VIEW1图件字节保持，不能以本次NOT_PASS否定那些实际响应，也不能授予细网格独参资格。新生产F/T、模型构造、平衡路径、JIT、LF、观察与渲染均未执行，其依据是冻结源码的实际失败调用位置及0HP/0态回执。

## 路径原因、最小修正与责任

[只读路径诊断](author/path_diagnosis.json)和stdout定位到新增的深层源码归档布局。首个目标目录包含完整原仓库路径，长度**261字符**，目标`core_audit_mechanical.py`路径286字符；HKLM `LongPathsEnabled=0`。这个配置与失败的长目录一致，支持Windows旧路径限制的原因判断；没有通过创建长目录复现，也没有改系统配置。

此前源码静审检查了数学继承、原门、187绑定与实际格式，但**漏掉该机器输出路径限制**。这是包装入口的问题，数学验证未开始。11个依赖的basename全部唯一，平铺到基类已创建的`sources`目录可把本路径的最长文件缩至202字符，同时保留原仓库路径与SHA映射。最小后续候选只修这个归档布局，另列新源码、路径清单、差异与独立静审；不在本卡冻结源或输出上修复、不重开剩余窗口。

## 成本、停止与资格

helper lifecycle终态 **9.1415305 s**；summary稍后记录9.1421876 s，两者采样时点分别保留。outer **11.3335414 s**，helper采样RSS **111,505,408 B**、outer进程树 **116,588,544 B**。原4500/4560 s、8 GiB额度没有触发，实际stop_reason null，子进程exit1导致NOT_PASS。协作时钟和采样RSS不是OS硬上限。没有其他重试或force，剩余额度不构成新许可。

原24态自己的HP参考仍未提供，原response的reference/views not_provided及producer false flags不改写。压力/有效夹持、网格/域收敛、圆体自身任务、自由体/摩擦、正式标签/排名及HF5整体仍未完成。

## 证据、历史与最近下一步

[授权记录](author/authorization_record.json) · [实际launch](reference_launch.json) · [完整stdout](reference_stdout.log) · [实际lifecycle](run_001/reference/lifecycle.json) · [实际summary](run_001/reference/summary.json) · [独立终态审阅](author/terminal_review.json) · [原卡](M-REF1_CARD.md) · [原协议](protocol.json) · [既有细网格变形、力与粗细图件](../../../functional_views/native_nested_cycle_20261009/complete_001/RESULTS.md)。本次输出只有lifecycle和summary；部分空目录不是科学结果，Git不保存空目录，恢复不需重跑。

独立审阅对NOT_PASS证据的一致性检查通过，raw SHA `9143060b3f17a7c2a27913b3c436ccfd4335a9e10c67c911c8acc8cec60e83b9`；审阅PASS不等于科学卡PASS。审阅者最初把stdout异常repr的双反斜线当成单反斜线，造成一次字符串格式假告警；纠正仅限普通文本审阅，来源与原SHA在最终审阅报告中保留，不改变科学输出或卡状态。

最近一步是准备M-REF2平铺源码归档候选，保持相同全部24态、48HP、方向、原数学及15严格门，重新独立静审具体路径后另获一次资源授权。不存在本卡继续执行或新参考已通过的结果。继续main开发，origin https://github.com/dudaxing/Compliant-TO-TMC.git。
