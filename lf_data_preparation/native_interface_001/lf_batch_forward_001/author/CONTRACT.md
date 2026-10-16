# L-BFWD1：现有批量消费合同（只读方案）

基线ff448447；当前源码无阻止这一最小方案的必改缺口。本记录不是执行许可或候选实现。真实batch已在2026-10-07运行过canonical/fine两例；旧任务无工件且complete/full/tangent。本步只验证L-BPREP1新fine/wave输入、固定工件task1.1与mechanical/chunk256/port_projection现默认链的真实消费，不重复旧once/全套测试（batch_forward_001/RESULTS.md:18–35）。

## 最少任务与清单改动

保原25task和prepared geometry字节不动。新阶段复制两例当前绑定task，仅改input.target_mm=0.5与path={kind:load_only,targets_mm:[0,.25,.5]}；新task_id/purpose/parameter_origin/description准确说明本短加载。其余几何绑定、材料、固定工件、边界、网格、alpha/gamma/Lr保持。task1.1必须有path，load_only要求严格递增且max(path)=input.target；删path会拒绝，降为1.0又禁止当前非空工件（native_project.py:40–46,67–94）。

两例purpose/parameter_origin/description须用共同文字，逐例来源放label/index；batch仅排除task_id与geometry，其余文字也比较（native_batch.py:123–126）。新建本阶段manifest，case保持label/geometry/task/output四字段；geometry引用既有prepared/000,001 derived文件，任务副本/评价目录/index放新阶段。不能直接用仍指原25任务的旧prepared manifest再以targets截短；显式targets必须等于task.path（native_batch.py:68–80,101–133）。

## 设置和预算

共享options显式mechanical/chunk256/port_projection，建议settings完整保既有L-PILOT1九项非clock：tolerance1e-9,constraint1e-10,displacement_floor1e-6,force_floor_factor1e-8,max_checks25,Armijo1e-4,backtracks12,bisections4,minimum_increment0.00625；settings.time_limit_seconds另定新额度。原probe为1800s，仅作来源，不是新授权。使用settings时省略顶层time_limit_seconds/minimum_increment；二者若与settings并用且clock不是180默认会拒绝（native_batch.py:44–58,185–198；native_evaluate.py:89–101）。

无显式options会使用complete/full/tangent和180s；无settings时minimum_increment由第二target/16得到0.015625，会偏离原probe0.00625（native_batch.py:14–16；native_evaluate.py:82–99）。每case各有完整controllerclock，batch没有总资源管理；导入、构模、保存、摘要、图和封存另占时间（native_evaluate.py:27–35）。同进程顺序执行也无显式逐例GC合同，不能承接已关闭的数据准备180/240s、1GiB窗口或假定新求解RSS。需新卡明确总额度，不改科学门。

## 失败、日志与显示

预检错误可能在index目录创建前发生。控制器数值失败保真实accepted partial，API保存后返回failed；输入/保存等错误返回含stage/code/class/reason的error response。batch首例非success即stopped并将后例保not_run；意外BaseException记录interrupted和当前error、finally写index后继续抛出，无重试（native_evaluate.py:102–125；native_batch.py:176–220；TMCError为ValueError，tmc.py:19）。

CLI只在返回后打印完整index，status success才exit0；原index可反映正在运行的case，但没有默认流式Newton stdout。收敛图可直接用新result.json的真实path_diagnostics和cached states，不需新日志框架或重算力（evaluate_native_batch.py:11–26；native_mean.py:247–282,307–344；split_displacement.py:347–368）。三个是请求目标数，原内部二分可增加accepted态，不新增严格三态科学门。

不存在force/--force入口，未知force选项会拒绝，已有输出目录不覆盖（native_batch.py:44–46,95–113；native_evaluate.py:43–51）。成功只证明这两新输入的短路径批量消费；新结果不套用旧参考/响应资格，也不代表原25cycle、接触压力、有效夹持、释放、稳定性或HF5通过。

本次只静读上述源码、原probe task/protocol及旧batch结果说明，未导入HF，未调用prepare/preflight/API/求解、测试或绘图，未读NPZ/ZIP/科学归档/媒体，未改正式仓库。
