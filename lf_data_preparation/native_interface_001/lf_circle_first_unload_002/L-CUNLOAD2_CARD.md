# L-CUNLOAD2：仅修测试适配器并验证已安装首次卸载入口

2026-10-18状态：用户在已说明下一卡最小修正后直接指示“请继续”；据此实施本独立新卡。尚未运行，候选须先静审。执行基线main a8daffe767598e8329bc42c07d7f812afea33851，已正常推送并恢复核对，工作区干净。

## 目标、证据和边界

整体目标仍是普通LF几何进入独立HF后的非线性加载、工件传力、卸载和恢复。当前阻断是小模型测试包装没有正确调用已有零起点入口；不是已观测的新卸载分支数值失败。

L-CUNLOAD1已首错NOT_PASS闭卡：唯一终端7afb58/exit1，outer5.171843600022839秒，清理true。一个native_resume.py候选已安装，SHA68e3122950766f9cecb48a02a0f52a6d5f2efbfc466432bccc2cd48c77e2b798。第1方法在test direct()将targets=None传给零起点solve_native_mean时，被原显式targets门拒绝；实际native入口尝试1、返回0，平衡控制器0、接受态0、F/T/HP/JIT均0，图0。原报告real_solver_invocations=1是入口计数的命名缺陷；原字节及5份partial封存保持，不追改成通过。

本卡只修测试调用和计数，完成原8方法有限验证。**生产HF源码零修改，默认安装零次**；已安装reader、力核、切线、控制器、构模、API、CLI、响应和原门全保原字节。不执行真实圆形1.40→1.35 mm回程或HP。

## 唯一最小改动

1. 新版测试direct()在没有saved_result的零起点调用中，显式传task['path']['targets_mm']；保存续算仍传None，沿已有defaults继承。不得修改生产入口去容忍缺失targets。
2. 将native_mean入口开始/完成单独记为native_entry_started/native_entry_completed；在现有native_mean.solve_split_displacement_path调用处透明计数真实controller开始/完成。保留给helper消费的real_solver_invocations时，必须明确等于真实controller开始数；完整结果的metadata计数另记。部分失败不能把入口拒绝冒称已求解，completed_methods也不等于方法通过。
3. 包装仅更新卡号、基线、新输出目录和零安装路径；原SUP2源码、资源/停止规则与原标量绘图源复用。不得增加方法、真实求解、反例组或另建框架。候选编写依据本次直接继续指示进行，独立静审通过后才执行，未冻包前不运行HF导入或测试。

## 有限执行和输出

同一新helper内运行唯一8方法unittest failfast：

- 嵌套load来源→原load append→公开evaluate_native首次下降→原ordered_cycle再下降，4次真实16单元／50DOF求解。
- 独立旧ordered_cycle来源及原同kind延伸，2次真实求解。
- 原5组任务/来源/嵌套身份/public/低层模式反例，具体列表从原TEST_MATRIX保留。
- 线性cold锚和wrong-R warm拒绝，2条线性路径；不另跑rollback或历史全套。

仍是无工件兼容fixture，P=0.0005 mm；原物理、settings/options和原门保持：relative residual≤1e-9、逐态原constraint_bound(系数1e-10)、global balance≤1e-6、fixed split fsum≤8e-11mm、9点J>0。fresh锚需1次检查、原state SHA和signed R字节保持；保存F/T重算0、HP/JIT0。嵌套索引与来源完整、子段资格不升级为完整前缀或原任务。

全部8方法通过且6次真实controller完成、2线性、计数相符后，才从本窗口新tiny普通JSON生成1张反力/残差双面板PNG、状态表和人工页。图标16单元／50DOF、无工件、仅接口兼容；不读取旧circle或旧tiny科学/CSV/媒体，不拼接旧图。新PNG最多一次像素检查。

## 资源与停止

一次tests共享120秒(含imports和方法/API边界，合作式检查)、每tiny controller30秒、标量显示共享30秒；helper180秒／outer240秒，采样RSS1GiB，全部测试/图/页/最终seal均在原helper180秒内。原SUP2 CPU-CLEAN1同实例终止/成员覆盖/句柄释放，固定5秒清理在outer内，不新增force兜底。

首个终端错误停止后续测试/图；仅原窗口仍开放时一次partial seal。无外部重试、修复重跑、延期、force、删除或回滚；无新安装。本卡与原失败独立目录和独立资源，不复用CUNLOAD1剩余时钟。实际窗口封存后，普通记录、main正常推送与增量恢复核对发布真实PASS/NOT_PASS；Git逐命令禁自动gc/maintenance，科学/媒体身份继承原producer seal＋stat，闭窗不再解码或重hash。

PASS只证明已安装首次卸载入口及有限兼容。真实圆形1.40→1.35仍需随后另卡，保持r9/c(71,40)、input峰值1.40及原加载前缀，实际回程产生后才画真实变形/工件力/距离/分区场与收敛。压力、有效夹持、自由释放、稳定性、完整路径、制造和HF5资格不升级。

授权来源：用户在收到失败原因、原卡关闭及下一卡仅修测试包装/计数的说明后，直接回复“请继续”。这是本独立新阶段的指示，不是复用L-CUNLOAD1剩余时钟；根在实施前明确宣布同120/180/240秒/1GiB边界、零生产修改/安装和不含真实圆形回程。原NOT_PASS保持。
