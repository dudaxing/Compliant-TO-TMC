# L-CTIPFHIGH1 包装实现记录

2026-10-23；作者记录，供独立静审使用。此记录不替代独立审阅，也不宣称运行通过。

本次只在 D:/hfh1_001 新建 science_high1.py、helper_high1.py、launch_high1.py，由已完成 FREAL1 的三份冻结研究包装作有限改写；生产57份源码、数值算法、原门和 SUP2 均不改。作者仅运行标准库文本处理与 AST 解析，没有导入或运行这三份候选，没有科学 NPZ 打开、哈希或解码，没有 HF/NumPy 导入、科学预检、测试、绘图或启动标记。正式基线为 main 3a9a59dea0b55848814baef252018550249cefaa。

## 科学入口的有限变化

唯一 evaluate_native_guided_force 调用继续从 protocol 取得两个绝对 P、Nmin、父路径及 selected index；完成后硬核父 accepted12、hold1.06、guided_reduced_tangent、父 port_projection、mechanical/chunk256、原成员及14720单元/14985节点、原全部非clock设置与新 clock3600。最多17接受态，回调数必须一致，solver_invocations1、HP0、saveF0、saveT0。未传未知 q 的参考值或初值，不从旧 probe/旧 force 续算。

worker 保留原只读审计：只允许 source_binding 中 admission_ 前缀的3个原 NPZ 路径；NPZ 写能力仅限新 run_001/force；读写混合新包仍因不属于原三路径而被拒绝。不 patch HF 或 NumPy。成功完整 API 控制流的四 mask+两 split 共6字段为冻结源码推定，记录明确说明字段访问没有动态 hook；open 事件与路径才是动态观测。原 model 仅核身份，不解码。ordinary bindings 在导入前逐份核验；导入位置必须是冻结 production_src。

若 API 抛错、返回非 success、target 未达或包装事后合同不符，只保存实际 receipt/progress/已有 partial 后非零退出，不再调用 API。没有试修、投影、外部重试、HP、安装或生产修改。原父 controller 历史身份差异不会被包装改写或绕过当前准入；fresh P0 和位身份由不改的生产入口执行。

## 完整原窗口与停止顺序

两个时钟均在各自文件第一个标准库 time 导入后立即起点：top 绝对 outer4860，helper4800含全部阶段及一次封存。science3885进程加完整清理最多3900，comparison45加完整清理最多60；viewer510及其清理和 root 五图一次检查共享600，QA必须在 display+585前完成。controller3600已包含在science预算中。

helper 的 reserve 用 START+4700 作内容终界，要求科学前完整预留3900+60+600+15、比较前60+600+15、显示前600+15；不足就停，不压缩阶段或延期。ordinary bootstrap <20；root等待另有 helper+4690界；读到QA与图身份后再次检查 display+585 和 helper+4690，关闭原包装仅在等待循环检查的临界到达漏洞；final bindings 开始 <4695；helper正常返回 <4700。科学和比较不仅检查 SUP2 同实例清理，还核总阶段分别不超过3900/60。

top 对整个 helper 树的 SUP2 deadline 为 top START+4730（relative seconds4730），同实例清理完成才读取稳定日志作封存。完整成功需 science/comparison/viewer 三份及外层第四份 proof 均 normal_exit/returncode0、cleanup_verified、proof.pass、job_handle_closed，并且 helper/renderer/QA/compare receipt 通过。每个阶段只有一处启动，首个终端错误跳过后续科学/比较/显示。

封存只读新 BASE 原字节，不读或复制 D:/hpr1_001 原科学包/旧 ZIP/媒体。封存条件为整个 helper 树清理证明通过且原 helper 时钟仍开放；partial 时允许记录已发生阶段的实际证据，不伪造未启动阶段。只一次 ZIP x 模式；入口 <helper+4745、逐成员 <4780、归档身份开始 <4790、最终 receipt <4800，同时 outer<4860；任何封存错误只记录一次失败，不重封。不稳定或未清理树不封。正式卡的240秒非科学余量包含准入调度、各层清理及该次封存，没有单独补封窗口。

## 仍待冻结与独立审阅

protocol 必须绑定这三份文件、比较器、viewer、原字节 SUP2、全部57生产源、4份 BASE 普通来源及原 ordinary 文件；具体集合由 root 冻结。必须核准确高输入 parent/result SHA、12选择、P0/P1、Nmin、3600/3885/3900/60/600/4800/4860、64GiB线程16/viewer8GiB及上述绝对截止，禁止沿用旧 LOW1 路径或 clock。root 负责原卡已获批准记录、唯一启动前无 RUN/markers、完整 bindings/eligibility 和五张新图的一次像素检查。比较器和 viewer 由其他作者完成，需独立审阅后才冻结运行。

源文件身份如下（完整数字记录另存 WRAPPER_IMPLEMENTATION.json）：

|文件|bytes|SHA256|
|---|---:|---|
|science_high1.py|7790|3217854b935bd6cfa078a56c114c3ba3b3bb42680d51c5bc155cc4c73b9643a9|
|helper_high1.py|7225|0df7f98294cf08101d6b9ed5ea333ed0594bb778a16e19137bd845b85446a5ca|
|launch_high1.py|5948|dbb277f84f66ae1deb2f72cbc0f54839cb26efba5cc04e0c4bf0453541414bb5|
