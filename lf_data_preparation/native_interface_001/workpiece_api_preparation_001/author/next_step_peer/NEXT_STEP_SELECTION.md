# 固定方体经现有薄API：下一步只读选择审查

建议下一步做一个有界的新单例阶段：从无关cwd用既有 `evaluate_native.py --repo ...` 调用一次已有 `evaluate_native`，承接已完成4mm右介质余量、side18固定方体的完整24目标路径。它同时证明CLI和API的实际对接，不需要再单独重复一次API生产。此建议尚未执行，也不重开任何旧卡。

现有产品功能已足够：task1.1支持fixed_rigid square/circle和ordered_cycle；native_mean负责一次构模、原平均位移控制器、缓存接受态及工件弱式力；evaluate_native负责一次solve、一次cached writer、一次JSON summary。CLI已暴露机械响应、切线分块、初猜和控制限；保存摘要CLI已能独立接reference/view manifest。不需要新求解器、工件API、路径API、批量包装或通用配置框架。

缺的是固定工件大行程从薄入口执行的真实证明，以及不用占位jobs路径的可移植参数示例。已有2/4mm结果的JSON导出证明摘要消费能力；新真实单例和batch迄今证明的是无工件小行程，不能把它们称为已通过固定工件薄API。

应先写一个简短示例命令/参数说明，直接引用仓库已保存的4mm原任务和普通几何。新输出目录必须与旧stage/旧run不同；明确HF Python环境及repo根，不依赖原作者绝对路径。task及geometry原字节可作为输入，不需要再padding、重采样或复制整套历史模型/结果。geometry中的历史来源路径只是上下文，实际输入依赖为该JSON及其声明的邻接geometry.npz。

| 参数 | 已完成4mm工况的实际值 | 下一示例要求 |
|---|---|---|
| response_mode | mechanical | 显式保留，不采用complete默认 |
| tangent_mode | chunk256 | 显式保留，不采用full默认 |
| initial_guess | port_projection | 显式保留，不采用tangent默认 |
| minimum_increment | 0.00625mm | 显式保留；0.25/16默认会得到0.015625mm |
| target/path | 1.2mm；24目标0→1.2→0 | 从task原path读取，不用单独--targets改路径 |
| settings | 原容差/Armijo/回溯/二分设置 | 原门不改，独立声明新资源窗口 |
| geometry/body | h1、84×40mm域；side18、中心(71,40)固定下半体 | 保持原物理条件和身份 |
| material | E1MPa、nu.3、gamma/alpha1e-6、Lr80mm | 不在入口证明中另做物理调参 |

控制器原time_limit为4500s，但这是旧关闭卡的设置，不是新运行授权或whole窗口。新API构模、缓存保存、summary与response写出都需要计入独立外层窗口；evaluate response的elapsed只计到summary结束。下一步freeze前应记录新controller/whole/outer预算和首错边界，不能照抄180s默认或借用旧卡剩余时间。

最小实际验收看一次构模/控制器/solve/write/summary、保存零新增F/T、原路径/模式/输入身份、全部实际接受态和失败前缀。加载目标在原index13的1.2mm，卸载终点在index23的0mm，须分别报告；若出现二分态，按实际N保存，不固定未来N=24。原API异常或controller失败按原语义记录并关闭新阶段，不修复后循环重试。原科学门保持。

面向人工检查，应看×1夹持器和固定方体、输入R与q_out、signed total/material/Hu body Fx/Fy、holding、2|Fy|幅值和以及加载/卸载返零。q_out不是钳尖间隙；node-window clearance不是表面距离。既有固定体saved_right_margin_views已具有体覆盖、节点力、有限tip距离/射线、J/Hu/保存F的Green显示，优先做最小身份/路径适配。plot_native_mean原viewer面向无工件TEST，并硬写“No workpiece/contact/clamping or full-stroke claim.”，不应直接冒充固定体显示。有限距离、保存应变和节点力均不增加压力或接触资格。

生产原response仍不借旧参考/视图资格。若要新结果的qualified_response，待真实终态后按实际N另记录新2N参考/保存显示，再用现有summarize CLI输出独立新JSON；无需改写原response或给solve CLI增加reference参数。

文档有一个低成本修正点：docs/NATIVE_EVALUATION_INTERFACE.md顶部仍写“两例真实0.025mm尚未执行”，并宣称该顶部为当前状态；现batch已经完整闭合。应改为短最新事实/链接并把原顶部作为历史保留，不涉及产品或科学代码。

本审查只读源码、文字和已关闭JSON，并记录原字节SHA；0HF导入、0NPZ数值读取、0构模/F/T/solver/HP/观察/渲染、0正式修改。下一物理功能建议是已有大行程固定体的薄入口证明，不是再次实现已存在功能，也不授一般有效夹持、压力、自由体/摩擦、匹配网格、排名或HF5完整资格。
