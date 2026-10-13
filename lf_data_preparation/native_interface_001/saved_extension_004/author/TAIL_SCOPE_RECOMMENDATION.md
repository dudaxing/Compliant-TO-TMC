# 当前1.05 mm末态至零：普通记录／源码范围建议

建议在当前结果完成发布恢复后，准备**一张批量卸载尾段卡**，复用已安装默认API及原pure viewer，取得实际作用、变形与是否释放的趋势。无需新增力学核心、重做36测试、安装或先重复1.05参考。当前输入仍1.05且固定工件Fy约0.07149 N，尚未走到零；尾段是功能缺口，有真实收益。这里仅静读普通源码／task／result／成本记录并提出范围，不实施新task或代码、不授权或执行科学。

原M-CYCLE1 task（`lf_data_preparation/native_interface_001/nested_cycle_001/task.json`）的24目标在卸载1.10后依次为`[1.00,.90,.80,.75,.65,.50,.25,0]`，**没有卸载1.05**（旧1.05在loading）。当前model.task已保留17目标前缀、插入新卸载1.05；因此只append这8项，形成25个完整task目标，不能称恢复原24同task或删改已保存前缀。新请求suffix为`[1.05,1.00,.90,.80,.75,.65,.50,.25,0]`，global16起点／17..24新目标；成功至少9接受态，原bisection可增加N，不硬设N=9。

默认`native_resume._extension_targets`已支持任意严格追加列表，返回`new_targets[index:]`并验证成功父段、末接受态、完整旧task前缀／canonical身份和local／global映射；`evaluate_native`支持一次`extend_path=True`，settings／targets／options留None继承。选当前child001／global16／1.05／state `96a9d68c51df98de266530e18607a8f9adfacac24287770edcd462ece5d6f915`，新task只有path.targets_mm追加8项，其余完整task包括task_id／description／input.target_mm=1.2和alpha5e−7保持。原lift／fluctuation及signed R不平移，K=None／fresh F/T由原controller验收。需要的是精简包装中父路径、目标／index／prefix计数与预算的适配，**不是核心功能补丁**。从零末态再次加载的保存延伸被现有nonzero-anchor门拒绝，属于之后的另一功能，不阻碍本次到零。

旧M-CYCLE1同h0.5／同几何声明已实际完成24态，但alpha=1e−6，而当前alpha=5e−7；task标签、说明／purpose和路径也不同。它提供目标顺序与成本参照，不转移状态或HP资格。其1.10接受时间`6583.719449699973`至零`11428.044742799946`差为**4844.325293秒**，这8段新增175次force-start／80次tangent；最慢旧尾段1.00→.90约1108秒。当前新1.10→1.05的evaluation580.758582秒、helper605.739464秒，22次force-start／19完成、10次tangent。旧全24态采样helper峰值约1.89GB，当前两态约0.80GB；缓存N增加及bisection仍可能改变成本／内存。

建议具体新上限：**controller9000秒、pure viewer最多600秒、helper10200秒、outer10260秒／采样8GiB**。controller比旧8段4844秒留约86%余量；helper另外留600秒viewer和600秒导入／保存／身份封存，outer再60秒。该上限是有依据的有限提案，不是ETA、运行成功／释放／内存保证；不能沿用本卡剩余1800／2700额度。原25checks／12backtracks／4bisections／mininc.00625及全部生产门保持。峰值和晚返回如实记录，首错保存实际partial，不重试、修复重跑、延期或force。

一张尾段卡比逐0.05拆多卡更贴近功能目标，省多次构模／fresh anchor／审阅与重复图；原完整尾段曾成功，当前两次单段也成功，没有静态接口阻断。不过alpha不同、.10／.25大步及接触状态变化使批尾仍可能失败，尤其旧.90附近和最后回零并不便宜；不把Fy下降或连续Hyperelastic假设当收敛证明。失败时保真实已接受路径，再据结果决定下一步。

成功后原viewer只画这条真实尾段：3PNG＋N帧GIF，报告signed输入R／qout、材料／Hu／总工件作用、有限尖端距离、J／变形及全部实际接受目标，reference=None。它的segment PEAK是1.05，不是历史1.20。到零仅说明输入目标走完，不自动等于自由工件释放、接触压力、有效夹持或稳定性；原父成功／早期M-ALPHA1 failed/time_limit、producer flags false、full_original／extended未由本child从零执行均保留。新全段HP参考若需要，待尾段实际结果再决定范围，旧1.10单点参考不能拼成新全段资格。

实际依据（本次仅ordinary读）：`nested_cycle_001/task.json`、`nested_cycle_001/run_001/fixed_square/result.json`及model.json／production_launch.json；`saved_extension_003/run_001/unloaded_alpha_half/result.json`及model.json／execution_receipt.json；`hf_repo/src/hf_eval/native_resume.py:46,100,127`和`native_evaluate.py:26`。未读取NPZ／gzip／CSV／媒体字节或像素，未导入HF／调用API、HP、求解、测试或绘图，正式文件未改。
