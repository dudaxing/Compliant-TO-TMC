# M-INTEGRATE1 实际结果：默认保存态续算集成通过

2026-10-12（Asia/Seoul），直接批准后唯一启动已终端exit0／PASS；默认hf_repo已经安装11份绑定文件。25个冻结参数实例实际收集并全部通过，75个setup/call/teardown全部passed，XML 25项／0失败／0错误／0跳过，stdout为 `25 passed in 6.62s`。没有重试、修复重跑、延期、force或自动回滚；窗口已关闭。

## 目标、改变与效果

整体仍为独立HF有限变形／TMC前向评价，读取普通LF几何、在明确任务下提供实际变形、反力和可解释工件作用给外部研究层。HF不做优化、不调用dmftd，MPM暂不实现；main、既定origin和science0.5.0保持。

前一步M-RESUME1已实际验证原alpha5e−7保存峰值013复核与首次1.20→1.15 mm下降。此前候选只能在隔离包运行；本步把同一Mean/controller/reader/response续算合同安装到默认库与两个CLI，调用方可从原保存接受态继续同任务后缀。有效输入力核／NumPy切线／组装原字节保持。另加入settings类型检查，使非法dict/object在读取父数据和力学前保存typed invalid_settings；两个CLI帮助文字已修正。核心实现未因测试扩展加入新的物理算法。

安装共7份生产源码＋4份测试：6旧文件修改、5新文件，均与protocol候选逐字节一致；6原源码快照与Git2b550d0保存原值。运行身份58份（52 HF模块、2CLI、4测试）一致，26个实际HF导入均来自默认hf_repo/src，108不可变bindings保持。原prepare card/protocol的authorized/executed=false是历史准备字段，实际批准在author/authorization.json，执行在integration_launch和run_001记录，不能用旧准备字段否认本次执行。

## 有限验证与实际资源

| 范围 | 实际结果 | 含义 |
| --- | --- | --- |
| 4个真实小模型实例 | 7条建模记录，均16单元／50DOF；F33/33、T22/22 | NativeMean NumPy aliases计数，保存态测试含输入身份负分支构建；不是全部内核调用总数 |
| 6个controller实例 | 单单元8DOF合成代数响应，断言通过 | 均值／R、零起点warm、锚点复核失败及回滚合同 |
| 15个mock／普通记录实例 | API、CLI、错误、旧响应／视图链接和来源迁移通过 | 不把mock次数当真实力学；旧JSON测试拒绝旧NPZ |
| XML／plugin／pytest child | 6.601／6.705872099992121／8.018545099999756秒 | 三种计时范围分开；plugin采样155664384B |
| helper／outer | 8.505939700000454／9.125265299982857秒 | helper自身采样24649728B、outer进程树184213504B；exit0、stopNone |

本卡180／300／360秒和采样8GiB门满足，RSS是采样而非OS硬上限。原零起点complete/full/tangent、mechanical/chunk256、缓存保存、保存态选项和设置继承、新时钟、CLI接线及typed错误所选断言通过。HP/JIT/原夹持器路径／新观察绘图未执行，零额外调用依据冻结源闭包、测试guards与小模型记录；不是全库机械钩子监测声明。

## 旧来源与资格

right4来源迁移用例实际passed：生产摘要仍success／原24态，当前reader按原门对旧参考strict mismatch，原result/reference/qualified response原字节保持。right2的同两条mean/split来源失配是本次只读源核对，没有额外总结API实测；M-REF2实际12参考源没有交集且仍匹配。这不等于旧48HP数值失败，也不能更新旧pins来制造matched。

旧M-RESUME1的100个bindings路径与本次11target交集为0，旧候选并未被默认安装覆盖。终审核98非NPZ字节，另外2NPZ只保留原声明pin，未新读取／复审数组。本卡108普通绑定保持与旧100全数组重新审计不同。

原M-ALPHA1仍failed/time_limit、14加载态，full path/task flags false；M-RESUME1新段success和父NOT_PASS分开。默认集成通过不拼接为一次原完整路径通过，不转移参考，不增加连续总压力、有效夹持、稳定性、全部切线列或HF5资格。

## 可人工检查的既有实际效果

本步不产生新物理图。下面复用前一步实际峰值／首次下降的2帧GIF；原数组、数值和图件没有改变。

![原M-RESUME1峰值与首次下降实际变形和工件力](../saved_continuation_001/run_001/view/resumed_alpha_half/actual_states.gif)

| 原保存实际状态 | 输入R (N) | q_out (mm) | 下半工件total Fy (N) | 有限tip-bottom距离 (mm) |
| --- | ---: | ---: | ---: | ---: |
| loading 1.20 | 0.37865427196005513 | 1.016934534302024 | 0.12492121630032427 | 0.0009696602064828141 |
| unloading 1.15 | 0.3470376815403639 | 1.0153174242325562 | 0.10671287553103108 | 0.0012850478242718566 |

两个端点不是连续卸载曲线；弱式工件合力和几何距离不是压力或合格夹持力。三PNG见[结构／力](../saved_continuation_001/run_001/view/comparison.png)、[距离／signed Fx](../saved_continuation_001/run_001/view/distances_forces.png)、[峰值场](../saved_continuation_001/run_001/view/peak_fields.png)。原像素人工核查覆盖三PNG，未声称人工逐帧检查GIF。本轮没有重新渲染。

[默认入口用法](../../../docs/NATIVE_EVALUATION_INTERFACE.md) · [实际测试stdout](run_001/focused_tests_stdout.log) · [执行回执](run_001/execution_receipt.json) · [独立终审](author/EXECUTION_TERMINAL_REVIEW.md) · [有限测试审阅](author/FOCUSED_EXECUTION_REVIEW.md) · [下一步取舍](NEXT_STEP_REVIEW.md)
