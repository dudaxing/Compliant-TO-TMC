# L-CTIPFREAL1：科学worker与连续资源包装独立静审

2026-10-23。审阅者 `/root/fload_controller`，代码作者 `/root`。**最终PASS：15项有限源码静审及最终4项protocol/绑定差异核对通过，无本审阅范围内启动阻断。** 比较器、viewer的内部数值/媒体定义由其另行独立审阅负责，root仍需合并全部独立审阅完成最终eligibility；这不是实际数值、清理或图像通过证据。

|当前审阅对象（D:/hfr1_001）|字节|SHA256|
|---|---:|---|
|science_freal1.py|7779|457ce5a8263688dd82aa7b8e4e766daaf882ff962e54f75c4e4d656c1ccda346|
|helper_freal1.py|7051|7594bf641f1c075f5dcd3d92a9a0fc74f1177410550cb9c262891825a57dddd5|
|launch_freal1.py|5936|d481a1fee59f68867cd03007e45a5251b037630d6d719866efd25d174d3d0cff|
|原SUP2|43559|b5f149e1cd3d6d9b4ad392123e410b786606f120f2e078139b7bacc97f2d9499|
|protocol.json|36357|b07ac9a43bb421011f6469dc01b71f17dfe43345364fe02cdcc390951081da83|

以上四份Python仅标准库AST解析；没有import或执行。当前top_start/helper_start/run/root_QA/ZIP五个标记均不存在。没有科学来源复制、NPZ/媒体读取或字段解码。

|项|静态结论与依据|
|---|---|
|1 单一科学调用|science只有一次现有evaluate_native_guided_force，api_attempts/returns分列，RUN/force或既有science_receipt拒绝重开；无旧父/位移probe重做、HP、测试、改源码、安装或指定q fallback。|
|2 准确的来源边界|source_binding中角色admission_恰3条：opaque model、snapshot geometry、原parent accepted002/state；_admit用原直接D:/hlo1_001树。worker无解ZIP/复制旧payload，pbindings最终须仅普通文件/源码，不能用其中额外hash旧NPZ。|
|3 NPZ只读及输出隔离|sys.audit不patchHF/NumPy。修订后先按访问flags分类，任何NPZ write-capable若不在新RUN/force内即拒绝；新force write-only不冒充read。readonly/read-capable open只容3条准入来源；O_RDWR即使在新force也会因不属old read白名单被拒绝。完整API返回后actual unique read set须恰3条。|
|4 读取事实分层|NPZ open记录是实际路径/事件观察；解码6字段明确依据“完整_admit及冻结源码控制流”，不冒称动态字段hook。若API在_admit前异常，未写该字段数；返回partial时_admit已完整完成，亦不会把partial误称路径成功。|
|5 参数与来源结果核对|成功后核parent result SHA、selected index2、hold.50、两载荷原值、unknown-q flag、mechanical/chunk256、新reduced与父port_projection分列、body成员、14985节点/14720单元、≤17接受态、callback数、非clock设置完全继承且controller1800、solver1/HP0/saveF/T0。|
|6 fresh与原门分工|已冻结57生产源的_admit/低层/capture负责原身份、新fresh F/T/无修复以及free/g/mean/J/global/rigid门；薄worker不改其函数或设置，不在外部投影q。独立的原门/方程静核见PRELAUNCH_PHYSICS_CHECK，实际门留原唯一运行证明。|
|7 progress与partial|on_accept只在生产capture已保存态后写普通标量progress并打印，pending→os.replace更新不改旧缓存；数值failed/result partial保留，再停比较及显示。异常原type/code/reason/traceback及已接受callbacks均记录，不通过外部再次调用API修复。|
|8 科学时限|所有科学包导入、准入与保存都在受监督worker；内部API1800，外层SUP2进程1885+原cleanup5及包装余量，整个阶段实测必须≤1900。没有把worker超时后剩余helper时间当第二次科学窗口。|
|9 比较时限及阶段门|仅science status+同实例清理通过才comparison一次；其SUP2进程45、cleanup5及余量，阶段实测≤60；comparison.json必须pass才进入显示。比较失败保原API实际status，不改写原解。|
|10 显示共享预算|viewer仅一次510秒、原8GiB子限，清理后root QA仍在同一display起点；等待必须<585，完整display+rootQA≤600。root五图各一次，精确PNG身份、science0/rerenders0；无新图修复。当前helper与viewer预期status为单数rendered_pending_root_visual_check。|
|11 连续时钟与保留量|helper bootstrap<20，reserve完整1900+60+600+15；每阶段开始前重核完整后续额度，不缩时凑过。root QA还受helper2590，最后binding校验2595、返回<2600；该严格内部界均在helper2700内。|
|12 整树资源与四份清理|top自身独立START后SUP2持有整个helper树，绝对deadline top+2630并沿原5秒清理；science/comparison/viewer各原SUP2。内存总64GiB、各库16、CPU，viewer8GiB；通过需normal_exit/0/cleanup_verified/proof.pass/job_handle_closed全真。正常完成最多四份job证明全部先于封存，失败不得伪称未运行阶段已清理。|
|13 唯一启动及源冻结|top拒替代参数、任一既存标记；helper再拒既存run/helper_start；写入x，ZIP x。source bindings在top/helper/science及最终helper退出前核身份；生产57文件保持，不删旧结果或rollback。top的passed为本地函数，未因import helper而提前制造无用helper START。|
|14 一次稳定字节封存|top待整个helper树句柄释放后才读新BASE文件；entry<helper2645、members<2680、identity<2690，最后仍helper<2700/outer<2760。只新BASE原字节，不打开旧NPZ/ZIP，不解码新NPZ。原窗口仍开放且cleanup可证明时才一次完整/部分封存，失败不补封。|
|15 证据及资格|所有pending/failed/normal实际证据分列；prelaunch protocol预状态不改写成实际事实。ROOT生产代码无修改；本次science完成不授HP/压力/纯接触承载/稳定性。当前审阅没有运行包装、真实求解、比较、viewer或任何媒体检查。|

## 执行前差异及最终冻结核对

science最初读查版本为7563字节/SHA `0bbb25e28c0cdf4330580cdfaf77e1c7ae4ab99f33b799c4dc7418b43c7a200a`。审阅提出old NPZ write-only和O_RDWR分类不完整，root在首次执行前作上述最小audit修订；控制逻辑、载荷、资源及57份生产源码不变。新audit已补静审，无剩余问题。无需、也没有运行包装试验来验证它。

最终protocol已核：36357字节/SHA见上表，baseline e80009232796d158b466fbd887cde82fdd7859fe；75份bindings逐项大小/SHA全匹配，构成为57生产源+6包装/比较/显示Python+4份BASE普通文件+8份原来源普通JSON。Python共63份AST解析通过，绑定中没有NPZ、ZIP、PNG/GIF或其他旧媒体，没有通过identity循环暗增科学payload读取。

最终四项差异核对均通过：①上述完整身份及Windows访问模式审阅；②原连续时钟science1900/comp60/display+QA600/helper2700/outer2760、64GiB/16/viewer8GiB及各内部deadline一致；③P0/P1、Nmin、selected2、单API、17态、3+4=7路径/6+8=14字段、工程门及5图/1真实N帧GIF上限与原卡一致；④所有五个启动标记仍不存在，封存只在四份完整同实例清理后、原helper窗口内一次进行。旧pending_protocol为本文件形成过程的历史状态，已由本次普通文件核对完成。

root写root_qa.json应使用同目录临时完整JSON再atomic rename，避免exists/read读取半写marker；该操作不另开窗口或改冻结科学源码。本最终审阅仍是只读/hash/AST，未导入或运行任何包装、HF、比较器或viewer，未读NPZ或媒体。
