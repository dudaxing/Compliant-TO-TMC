# L-CUNLOAD1：保存的load_only末态显式转入首次卸载

状态：只读设计已形成，待新授权实施。尚未编写候选实现、安装默认源码、运行测试、生成新科学结果或图像。本文件不是执行许可。

## 当前状态、目标和理由

正式根：D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC，源码为其下hf_repo，main基线c78658322587499e901e654516aed62b45aa022d，origin固定https://github.com/dudaxing/Compliant-TO-TMC.git。本轮只读Git确认clean、fetch后main与origin/main无差异；不在外层旧hf_repo开发。

整体目标是普通LF几何进入独立HF后，计算可检查的非线性加载、工件传力、卸载和恢复响应，供外部研究比较；HF不含优化，不调用dmftd，MPM仍不实现。当前不具有完整HF5、正式批量标签、最终排名、压力或有效夹持资格。

L-CSTEP5已完成圆形固定工件1.35→1.40 mm子段，生产/helper/outer PASS；新态全局目标8，下半工件Fy=0.004223912418638585 N，最小无符号Q1边界距离0.06329727765158799 mm，far-right tip距离2.959839839455605 mm，自由第三介质min J=0.052138230727749965。既有证据支持先观察小回程与恢复，没有新增J阈值，也没有证明已形成有效夹持。1.40 mm尚无独立HP，1.35的局部定位与1.15的HP不转授到新态。

本次只补下一项必要功能并做小模型验证：成功、完成的load_only保存末态，显式转为ordered_cycle首次下降。真实圆形1.40→1.35 mm在本卡通过后另卡安排，不包含在本次执行中。

## 最小实现合同

1. 复用现有公开`extend_path=True`和显式新task文件；不新增命令开关、控制器或另一套状态运输。默认不启用时，原保存续算合同保持。
2. 预期只修改`hf_repo/src/hf_eval/native_resume.py`。在`_extension_targets`的load_only来源处理中增加明确的cross-kind分支：新kind只能为ordered_cycle，完整旧targets前缀逐值/规范身份保持，只追加**一个**有限、非负且严格小于原峰值的目标；新input.target_mm保持原峰值。原load_only→load_only严格增载与原ordered_cycle延伸分支保持。
3. 新旧任务物理身份比较仅允许恢复旧kind/targets并沿用原四说明字段(task_id/purpose/parameter_origin/description)的规则；几何、网格、材料、正则参数、工件、边界、端口及其余任务字段不变。四说明字段例外只属于load_only来源；后续ordered_cycle同kind延伸仍按旧精确任务合同。下降目标可等于先前非相邻加载值，不能误加全路径唯一要求。来源仍须满足已有成功/完成、非零终末原目标、整段接受覆盖、父子来源和global/local索引证明。
4. `read_native_resume`继续只读取来源geometry和选定split的lift/fluctuation，不读取旧力、切线或矩阵；状态SHA、固定自由度及带符号R身份保持。来源锚点由原控制器fresh F/T检查，不作Newton修正来挽救不平衡锚点。
5. continuation保留`continuation_mode=explicit_task_extension`及其source/extended task SHA、完整目标、appended目标与parent_continuation；只在cross-kind时增加可辨认的`task_transition`说明来源load_only、目标ordered_cycle和首次卸载。峰值和新末目标来自明确任务，不混淆。
6. 复用现有native_mean、native_evaluate、native_response、两条CLI、project构模及split控制器。上述文件、力核、切线、Newton、线搜索、二分和生产门保持原字节；若实现发现必须改更多生产文件，先停止本卡实施并说明，不能扩范围。response的既有“Segment maximum”范围文本按子段观察解释：首次卸载子段包含原峰值锚点，其数值可以等于来源峰值，不代表重执行原加载。

## 有限验证及可视化

唯一测试子进程执行8个有限方法，failfast；以实施前冻结的验证表为准，不运行整套历史测试：

8方法职责与分组反例见本目录[只读验证表](READONLY_VALIDATION_PLAN.md)末表；实现前将具体反例字面列表冻结，不新增第9方法、额外FE或rollback路径。源码事实、行号与单文件取舍见[只读设计](READONLY_DESIGN.md)，当前Git/环境和原源SHA见[恢复记录](READONLY_RECOVERY.json)。这些是计划证据，不能当作测试通过。

- 一条嵌套来源链：tiny零起点load_only→原load_only继续增载child→显式首次卸载child→原ordered_cycle继续下降，共4次真实求解。首次卸载使用公开evaluate_native入口，确实覆盖实际圆形来源属于已延伸child这一结构。
- 一条旧ordered_cycle来源及同kind延伸，共2次真实求解，保留旧行为。
- 五组有限任务/来源/嵌套身份/API/低层入口反例；错误入口不调用真实求解来制造失败。具体输入、预期错误与计数在候选静审前列定，不增加真实求解数。
- 一项线性wrong-R检查：冷锚构造和不平衡warm锚拒绝，共2条线性控制器路径；不另跑已有rollback用例，不称其为TMC材料验证。

真实模型限定为既有4×4、16单元／50自由度兼容fixture，PEAK=0.0005 mm，其他fixture物理沿用L-CEXT1；无工件，不能据此判断圆形夹持效果。6次真实solver invocation、2条线性路径和所有失败入口的实际计数分别记录。没有HP、JIT或新夹持器平衡计算。

接受态沿用原门：relative residual≤1e-9、原逐态constraint_bound(系数1e-10)、global balance≤1e-6、固定split fsum≤8e-11 mm、原9点J>0。每个fresh锚点须1次检查、状态SHA/R字节保持；接受缓存与原索引/leg/parent来源一致，不读取旧矩阵或把子段完成升级为整条任务完成。结果/continuation/公共response仍保持task_target_executed、full_original_path_completed和full_extended_path_completed为False，target_response为None；requested_endpoint_response指向新末态。生产资格与独立参考仍False/未提供。

全部测试通过后，从本窗口新tiny普通JSON标量生成一张双面板PNG：输入反力—绝对输入位移、接受态残差及原界。显示锚点复核和新下降步骤，标注16单元／50DOF、无工件、仅功能兼容；不读取旧circle数组/CSV/媒体，不冒充圆形实际变形。新PNG最多一次像素检查。真实圆形实际×1变形、距离/工件力及恢复图在后续真实回程产生后另行安排。

## 唯一实施与执行顺序

1. 获新授权后，在外部author目录编写一份候选native_resume.py、8方法测试和最小执行包装。只做源审阅，不提前运行测试、HF导入或真实求解。独立静审通过后，冻结候选、依赖、测试表、协议与授权；未通过则不启动helper。保持LF/HF各自环境，不升级依赖或删严格选项。
2. 在尚不存在的正式`lf_data_preparation/native_interface_001/lf_circle_first_unload_001`冻结准备资料。唯一SUP2 helper内先安装该**一份**默认源码，记录转移前/后字节，再运行唯一测试子进程。这样直接验证默认入口，不搭建overlay框架。
3. 测试全PASS后才生成上述一PNG和结果/状态/人工检查页；输出身份在原窗口内封存。普通记录应包含目标、改动、理由、方法、效果、限制、实际失败和下一步。
4. 首错停止后续测试/显示；原窗口仍开放时只封存实际部分结果。失败时保留实际已安装字节及部分结果，无自动回滚。本卡不执行圆形回程或重新执行已完成路径。
5. 结果闭卡后，以普通main提交/推送和增量恢复核对发布实际状态；七份入口历史原字节保留。历史科学/CSV/媒体校验只沿用producer seal＋stat，不重新读取、hash或解码旧载荷。Git传输对象I/O不包含在该wrapper读范围表述中；逐Git命令禁自动gc/maintenance，不改全局配置。

## 固定资源、停止和资格边界

Python使用D:/Coding/Diversity TO/Compliant-TO-TMC/.venv-handoff/Scripts/python.exe，Python3.13.6；依赖仍按hf_repo/pyproject.toml现有固定版本。CEXT旧5次真实小模型＋2条线性路径的测试子进程实录6.5548945秒，只作预算依据，不当作本次通过证据。

一次tests共享120秒(含imports与方法/API边界，合作式检查，不称硬抢占)、每tiny controller30秒；标量图/页共享30秒；helper180秒、outer240秒(最多4分钟)，采样RSS 1GiB。安装、测试、显示和最终seal均在同一helper180秒内。采用既有SUP2 CPU-CLEAN1同实例终止/全部成员覆盖/句柄释放合同，固定5秒清理在outer内；不新增force兜底。

一次启动，首个终端错误停止；无外部重试、修复重跑、延期、force、删除或自动回滚。原控制器内部回溯/二分仅按既有算法执行。若错误发生，依实际结果规划另卡，不能复用剩余时钟。候选源审阅不是测试；本卡PASS仅证明这项公共保存态转换与有限兼容，不授圆形卸载、自由释放、压力、有效夹持、稳定性、完整路径、独立参考、制造或HF5资格。

## 当前审批边界

L-CSTEP5的1.35→1.40 mm授权和资源窗口已经关闭，未覆盖新增源码安装及本次小模型平衡测试。本卡需新的明确实施/执行授权。当前只读设计资料位于本author目录，正式仓库与默认HF源码保持未改；不以自动goal继续或剩余时间当作批准。
