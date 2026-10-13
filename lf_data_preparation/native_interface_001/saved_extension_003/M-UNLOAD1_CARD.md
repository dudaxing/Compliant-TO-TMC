# M-UNLOAD1：默认入口从1.10延伸至1.05 mm

2026-10-13（Asia/Seoul）。源码准备；尚未授权或运行。先前M-EREF1已实际PASS、闭卡、发布和恢复核对至main6f58d96。本卡只有一个最近阶段，取得新直接批准后单次启动。

## 功能目标与依据

整体目标仍是独立HF读取普通LF几何、输出非线性TMC正向反力、位移、固定工件作用、可恢复状态与实际变形，供外部研究层比较；不优化、不调用dmftd，MPM暂不实现。默认显式续算入口已安装并有36项兼容测试，1.15→1.10实际生产成功；新1.10点2HP及原十五门已通过，确认该点力／声明方向切线一致。

现有保存生产：1.15→1.10 mm时，输入R从0.347037681540降至0.315886016700 N，工件Fy从0.106712875531降至0.088978471092 N，尖端底边间隙从0.001285047824增至0.001730504605 mm。下一步仅追加1.05，观察力下降、距离和变形；不把一致性通过当成连续压力、有效夹持或完整释放。

## 唯一输入与原物理条件

从saved_extension_002/run_001/extended_alpha_half/result.json的最新success末态accepted child001／global15／absolute input1.10、unloading、非anchor继续。state SHA为3dc492f8aef4751e643ddb1413a797ca39434d349bfed59844d46e4e730015ff。proposed_task仅在原完整16目标前缀后追加1.05，其他task字段逐字段保持，input.target_mm仍1.2；新子段[1.10,1.05]，global15／16。

原h0.5 mm、84×40 mm域、13440单元／13689节点／27378DOF，固定1548、自由25830。E1MPa、ν0.3、plane strain、厚20mm、γ1e−6、α5e−7、Lr80mm；固定方形工件中心(71,40)、边18mm，五节点端口原权重，k_out=0。几何、材料、边界、原settings／mechanical／chunk256／port_projection全部继承，controller1800秒也与父段相同。

生产默认loader为source geometry／selected split state两NPZ、六字段合同；不解码保存force／tangent／matrix作初始预测，initial_K=None。六份父NPZ还作为来源rawSHA绑定，在批准窗口核身份；准备期只继承闭producer／manifest及stat。不要把零解码预测写成完全未读旧科学字节，也不声称动态np.load计数。新纯viewer在实际N接受态上打开1+2N NPZ、27+18N descriptor字段，geometry／nodal各N次，无参考输入或力核重算。

## 最小实现与原验收

两份薄包装调用已安装evaluate_native一次，不复制候选、重跑36项测试、修改默认实现或安装。调用geometry=None、saved_result=真实父result、selected_state_index=1、extend_path=True、time_limit_seconds=1800；targets/settings/options省略并由原默认继承。原fresh F/T起点复核必须先过原平衡／均值门，不使用保存切线修正起点。

只沿原控制器执行F/T、回溯和必要bisection。原门保持：production_residual1e−9、global_force_balance1e−6、fixed split sum8e−11mm；均值设定tolerance1e−10及原逐态native_constraint_bound规则保持，正J必须成立。从实际接受缓存核门，不新增F/T。正常invalid_J／Armijo拒绝试探和内部bisection允许，F/T开始可大于完成；它们不等于外部重跑。成功原目标global15／16、原anchor state与signed R身份必须保持，N为真实接受数，至少2，允许原bisection保存中间态。

## 真实可视化与输出

生产成功后原pure viewer调用一次，无reference，输出comparison.png、distances_forces.png、peak_fields.png与实际N帧actual_states.gif；segment PEAK是1.10起点，不冒充原1.20峰值。图显示实际结构变形、三分量节点作用、输入反力、工件Fy和间隙等原观察量。原viewer在批准窗口内核GIF帧数；闭卡后最多对三个新PNG各一次像素检查／展示，不再解码GIF或补绘。

输出为run_001/unloaded_alpha_half的原model／accepted缓存、result／response／sources，run_001/accepted_progress.jsonl、execution_receipt.json、view_protocol及原view.json／图件；实际F/T、API／model／reader／solve／save／summary次数和原cache门记录。保存／摘要包装核零新增F/T；只监测已绑定NativeMean aliases，不声称所有力学hook动态监控。原窗口内一次输出SHA／stat封存，闭窗不补科学hash。

## 完整新资源窗口与停止

controller1800／viewer600／helper2700／outer2760秒（最多46分钟）、采样8GiB；这是新授权，不能续用已闭M-EREF1或M-EXTEND2余时。原M-EXTEND2该生产子段加测试及图实际outer961.34秒，仅供预算规划，不保证下一段耗时或成功。最早whole clock涵盖身份、import、构模、API、保存、viewer及封存；controller内部计时不覆盖API构模前段与保存，故另有whole边界。viewer只获min(600,原helper剩余秒)。采样RSS和协作stop不是OS硬上限，实际等待同一helper及viewer终态，迟到PASS不通过，无force。

首个终端错误停止，无修复重跑、重试、延期、测试、HP、安装、回滚或删除。helper的运行资源stop使用原TMCError(code=time_limit)穿过trial捕获，不触发后续bisection。原controller1800内typed failure通常仍有whole窗口交原API保存真实partial；whole窗口或stop已关闭时不保证缺失缓存完整保存，不补造结果。viewer失败保留生产success及partial viewer，整卡NOT_PASS。仅原whole窗口仍开放时允许一次输出身份封存；关闭时保已有文件／日志和真实异常，不新启动复制、ZIP、绘图或科学hash。

## 资格与后续

原成功parent及祖先failed/time_limit、M-ALPHA1／M-EXTEND1 NOT_PASS保持。子段成功与unload_endpoint_reached仅指1.05的新请求；完整原／延伸任务、压力／有效夹持／完全释放、稳定性、全列切线、一般LF及HF5不升级。已有M-EREF1仅旧result的1.10点2HP，不能改绑成新两态result的完整4HP参考，也不放宽公开reader。

成功后根据真实1.05反力、工件作用、距离与变形决定更低卸载目标及必要参考；只详细计划本段。失败先据真实证据排查，不在旧卡内静默修复重跑。代码：[helper](execute_unload.py)、[outer](launch_unload.py)、[任务](proposed_task.json)；前置：[M-EREF1实际结果](../extension_reference_001/RESULTS.md)、[父生产](../saved_extension_002/RESULTS.md)。
