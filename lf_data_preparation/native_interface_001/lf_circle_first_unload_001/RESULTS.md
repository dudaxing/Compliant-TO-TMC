# L-CUNLOAD1：保存load_only末态首次转入卸载

本卡 **NOT_PASS**，helper `not_pass`／outer `not_pass`；默认源码实际转移数 `1`。

整体目标仍是普通LF几何进入独立HF后完成可检查的非线性加载、工件传力、卸载和恢复。本次补齐公开保存态首次卸载入口，避免从零重做已完成加载；真实圆形回程是随后依赖本功能的下一物理步骤。

唯一生产修改native_resume.py：成功load_only末原目标可以在显式extend_path下转成ordered_cycle，完整保原前缀/峰值，只追加一个下降目标；增加task_transition来源说明。控制器、API、两CLI、响应、力核、切线和原门保持原字节。来源任务SHA/parent_continuation/global-local索引及fresh F/T原锚复核沿用既有机制。

实际默认源：`{'path': 'hf_repo/src/hf_eval/native_resume.py', 'baseline_sha256': 'e8162964487df510a608a980feb1a03b3ac36e97a55452fac9e342274cfee2d1', 'actual_sha256': '68e3122950766f9cecb48a02a0f52a6d5f2efbfc466432bccc2cd48c77e2b798', 'candidate_sha256': '68e3122950766f9cecb48a02a0f52a6d5f2efbfc466432bccc2cd48c77e2b798', 'changed_from_baseline': True, 'bytes': 18014, 'matches_candidate': True}`。失败时仅据实记录已安装字节，不自动回滚。

测试原报告：方法 `1`／8；真实/线性等计数 `{'real_solver_invocations': 1, 'real_solver_completed': 0, 'real_force_calls': 0, 'real_force_calls_completed': 0, 'real_tangent_calls': 0, 'real_tangent_calls_completed': 0, 'HP_calls': 0, 'JIT_calls': 0, 'linear_controller_paths': 0, 'linear_assembler_calls': 0, 'rejected_lowlevel_entries': 0, 'forbidden_old_cache_reads': 0}`。缺报告为None，不能写成零或默认通过。完整反例及预期见[冻结验证表](TEST_MATRIX.md)。

计划6次真实求解使用16单元／50DOF、无工件的小模型。嵌套load→load append→首次卸载→cycle再下降为4次；另旧cycle来源及旧同kind延伸为2次。线性冷锚＋wrong-R拒绝计划为2条，不是TMC材料验证。实际执行以原报告和下面边界解释为准。共享tests120秒，每tiny controller30秒，原残差/约束/平衡/fixed/J门保持。

实现合同：新增跨kind路径使用公开evaluate_native；峰值保留、下降可重访旧非相邻加载值；fresh锚点保状态SHA/R，子段响应给末态且full/tasktarget仍False，缓存保存不重算F/T。本轮若验证未通过，这些只能列为候选合同，不能列为已验证功能。

|series|d mm|R N|relative residual|fresh anchor|
|---|---:|---:|---:|---|

本次没有生成图：第1方法在direct(source, task, None)处被原零起点显式targets门拒绝，尚未进入控制器。实际native入口尝试1、完成0，平衡控制器0、F0/T0、接受态0。原report的real_solver_invocations=1计的是native_mean入口，不是1次真实平衡求解；原字节保留，本解释单独勘误。新增卸载分支尚未运行，不能据此判断其数值成功或失败。

新reader已安装，但本次兼容验证NOT_PASS，功能尚未验收；绘图在首错后停止，不从旧记录拼接“效果图”。

outer耗时 `5.171843600022839` s，helper `3.1484738000144716` s；进程树采样峰值 `189579264` B，清理 `True`。1GiB是采样门；原SUP2同实例终止/成员覆盖/句柄释放合同保持。原窗口封存 `5` 输出、`7653` B，封存状态 `actual_partial_inside_original_helper_window`。

图只使用本窗新tiny普通JSON；它展示接口功能和数值收敛，不是圆形工件实际变形或接触图。本卡没有执行1.40→1.35 mm、没有新增HP，既有圆形1.40 mm结果和资格保持。压力、有效夹持、自由释放、稳定性、制造和HF5仍未完成。

独立实际审阅 `pass_actual_finite_review`；像素检查 `not_applicable_no_image_created`。授权前false/pending快照没有回写；新human授权与实际运行单独保存。首错后没有修复重跑或更改门。

下一步：准备L-CUNLOAD2新卡，仅修测试包装：零起点direct显式传task.path.targets_mm，保存续算保持None；分开记录native入口与实际controller开始/完成，原real_solver_invocations不得再把入口拒绝当作求解。已安装native_resume候选及其他生产源保持原字节，不回滚、不再安装。保持原8方法/6真实/2线性、物理、门与有界预算，在新授权和新目录中执行；本卡不修复重跑，也未执行真实圆形回程。

入口：[原helper](run_001/execution_receipt.json)、[原tests](run_001/t/test_report.json)、[实际审阅](author/ACTUAL_REVIEW.md)、[闭卡JSON](author/closure.json)。原值人工页和PNG未生成。
