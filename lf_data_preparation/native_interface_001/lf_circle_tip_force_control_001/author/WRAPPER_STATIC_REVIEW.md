# L-CTIPFLOAD1 最终运行包装独立静审

2026-10-23。审阅者 `/root/fload_controller`，包装作者 `/root`。
结论：**最终版本14/14项有限静态通过，无本包装启动阻断。** 已补审四层清理全部通过后、由top负责安装的顺序收紧；最终字节如下。仍无实际执行、清理、图像QA、安装或封存通过证据。

|对象|字节数|SHA256|
|---|---:|---|
|launch_fload1.py|7509|757d796f2cf6489d7ab7ea6a5a0b3c305c4dadc2c5dd93af01beb8d193153dd7|
|outer_fload1.py|5042|7774652da7ec8f0a7c0d2d28af3b46ddae0b05b78d0bad5de5adff3e236cf1dc|
|run_fload1.py|5588|aa1a090fcee9c1798ce682a00762868849fc7ea77d5683363eb723b97b954cf1|
|protocol.json|31415|3476f6d6136181c498ca80bfa422c7c334a160f5cda2ee530b2c714c5a37ece0|
|windows_owned_process_sup2.py|43559|b5f149e1cd3d6d9b4ad392123e410b786606f120f2e078139b7bacc97f2d9499|

以上文件均位于 `D:/hfl1_001`。四份 Python 仅用标准库 `ast.parse` 成功解析；SUP2 为原未改字节，并有限静读其 `run_owned`、deadline、RSS采样、5秒共享 cleanup 及 proof/handle-release 实现。没有 import 或运行这些文件。

|项|静态证据与结论|
|---|---|
|1 批准范围绑定|protocol 绑定当前 5c496c8 基线、显式两测试模块、两份新安装文件、本卡 tests300/view60/helper480/outer540、8GiB和16线程。未扩到正式 r9、HP、卸载/延伸或旧生产修改。|
|2 原字节身份|本审阅逐个读取并核67份 bindings 与55份原正式生产源码，大小/SHA全部匹配；两安装文件 SHA 与独立实现/API静审一致。旧文件未被本审阅改写。|
|3 唯一启动|top 拒绝替代参数及任何已存在 top_start/run/outer_start/ZIP/root_QA；child 再拒既存 run/outer_start；写入用 x，ZIP用x，安装用xb。实际静态检查时五个启动标记均不存在。|
|4 两层原时钟|top START 从入口早期建立，outer child 自身 START 为原480窗口起点；protocol 显式区分，不以剩余时间建立新阶段。top SUP2 deadline=top+460，留5秒同实例清理；helper监督至child+410；QA440、child<450退出、top安装455、封存入口465/成员475/归档身份478，最终还需child<480且top<540。|
|5 整树资源|top 的真正SUP2对象是 outer 全树，RSS限8GiB；其下 helper/tests/viewer 分别继续原SUP2合同。环境OMP/OPENBLAS/MKL/NUMEXPR各16，CPU/x64；未启GPU或升级环境。封存是top的普通原字节工作，并仍检查原两层时钟。|
|6 清理合同|`passed` 要求normal_exit、returncode0、cleanup_verified、proof.pass、job_handle_closed全真。失败同样执行原SUP2终止/成员覆盖/释放，不能以裸PID消失代替。规划最多四层SUP2；实际失败可能尚未启动viewer，届时不能声称四层实际运行。|
|7 唯一测试命令|显式 Python -X utf8 -B -m pytest -q -x -p no:cacheprovider，仅原split九展开和新八方法；新短basetemp/JUnit位于全新run；环境禁插件自动加载与pyc。无预先collect或另开探索测试。|
|8 有限结果门|XML必须17个case且无failure/error/skipped；实际新16格路径要求4，注入/拒绝≤32，partial重叠计数1；原1条真实/11次synthetic另列，总上限保持5真实/43注入拒绝。实际force成功及受控partial恰保首态必须符合冻结验证记录；不把受控失败叫真实物理奇异。|
|9 显示启动顺序|只有测试进程和同实例清理通过、17项及实际合同核对后才启动唯一viewer60；共享内容时钟额外留70秒，窗口不足停止。helper只核viewer声明的一张PNG和零science；纯viewer源的科学读取集/图义另由其独立审阅证明，本包装记录不单独替代该证明。|
|10 一次PNG QA|viewer及helper完整清理后 outer 才公布图路径、等root marker；要求pass、pixel_inspections=1、精确PNG大小/SHA、scientific_calls=0；未通过或超时停止后续安装，无重绘。root写marker应先完整写同目录临时JSON再原子rename，避免exists/read竞态；已将操作建议告知root。|
|11 条件安装|outer child只在tests/display/一次root QA通过后退出，自身不安装。top先取得outer第四份完整cleanup proof，再逐一核helper/tests/viewer另三份normal_exit/returncode/cleanup/handle全通过，才核正式HEAD、55旧源码、两新target不存在和候选原SHA；在原helper<455内仅安装两份原候选字节，不切换默认入口。不允许自动rollback，首错保留实际部分安装。|
|12 失败保持|各层异常写明type/message/traceback或监督原因；无科学重跑、补测、补HP、重绘、延期或force分支。child execution_receipt明确installation_owner/archive_owner皆为top；最终安装事实由top installation_receipt记载，不以child尚未安装快照冒充安装通过，也不以预封存seal_attempts=0伪称最终事实。|
|13 稳定日志封存|top等outer全树同实例清理、proof/handle全通过才有一次封存资格；包括普通top监督记录和已关闭outer/helper/tests/viewer日志。ZIP只读原字节，不解码NPZ；原窗口不足则跳过，失败只记failed_once_no_retry，不另开窗口补封。|
|14 静态与实测区分|本审阅只读、hash和AST；没有导入候选/NumPy/JAX、没有pytest/collect、F/T/平衡、媒体/缓存解码、QA、安装或封存实际执行。protocol的numerical_launched=false/new_modules_installed=false是冻结前历史快照，执行结果应由未来receipt证明而不是重写该快照。|

有限边界：本审阅不预授实际17项通过、8GiB峰值、清理成功、图像可读或最终安装/归档身份。只有唯一原窗口的实际证据能证明这些结果。独立viewer/测试/控制器源审阅及root最终eligibility仍需一并成立才可启动。

## 顺序收紧的差异审阅与历史

此前已审版本：launch 4897字节/SHA `4e67fe844e0c38f19cf50f5496e17a8bdf98493ff8069f5a091763bc383f62b6`，outer 6537字节/SHA `8ccfcada9646d3a1436701b13ee0bd1c0bdedb6002774214d9cb3efe92f16b1e`，protocol 31329字节/SHA `1e760e6854cc447f0354d34d95be0f8ed51d43054f938b6f4740d0606869e9f0`。该版本曾有限静态通过，但现已superseded，不能用于最终启动。

本次只补审三项差异：①child删除全部安装代码且只在QA后返回；②top取得自身outer及内部三份proof全通过后才核源/HEAD并安装；③安装边界在同一原helper内由450收紧顺序后安排至455，封存465/475/478及480/540总窗不变。三项均通过。重新AST核最终launcher/outer，重核67绑定无差异，run/helper、viewer、SUP2及两份数值实现SHA不变；五个启动标记仍未存在。未重复导入或运行无变的数值源码。
