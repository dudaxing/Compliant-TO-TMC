# W-API1：固定方体大行程薄入口真实forward候选卡

这是外部未冻结草案，**当前未授权、未执行**。worker/peer、manifest、当前源和输入SHA待根任务固定后填写。它不复用旧闭卡，也不许可修复重试或force。

目标是通过已存在的薄入口，真实完成一次固定方体大行程正向评价并返回可用compact summary/失败原因。现有fixed_rigid、ordered_cycle及力摘要已经实现；本卡只补真实入口实例。旧右4 mm生产/独参是物理输入与成本背景，新结果不借旧资格。

| 项目 | 明确范围 |
|---|---|
| 准备记录 | `lf_data_preparation/native_interface_001/workpiece_api_preparation_001` |
| 新数值stage | `lf_data_preparation/native_interface_001/workpiece_forward_001` |
| 新case输出 | stage下`run_001/fixed_square`，必须全新 |
| 新index | stage下`run_001/batch`，必须全新 |
| 实际入口 | 根任务固定的单例manifest，通过现有薄入口；fixed_square对应evaluate_native只调用一次，内部solve_native_mean一次、缓存write_native_mean一次；不得预构模 |
| whole-helper / outer | 一次连续4500 / 4560 s，包含imports、核查、API构模/求解/保存、summary和末身份核对；receipt写出由outer覆盖 |
| 采样RSS界 | 8 GiB（8,589,934,592 bytes）；own与tree样本按原字段分别记录，不声称OS硬内存保证 |
| controller | 原完整DisplacementSettings保持，time_limit_seconds4500；其时钟不等于whole-helper时钟 |
| 物理任务 | fixed side18 square，center(71,40)，native h1、84×40 mm、右余量4 mm；E1 MPa、ν.3、t20 mm、γ=α=1e-6、Lr80 mm、原端口/支承/固定体，free output |
| 原路径 | 24 targets：0,.25,.5,.65,.75,.8,.85,.9,.95,1,1.05,1.1,1.15,1.2,1.15,1.1,1,.9,.8,.75,.65,.5,.25,0 mm |
| 模式与设置 | mechanical / chunk256 / port_projection；minimum_increment=.00625 mm；tolerance1e-9、constraint_tolerance1e-10、displacement floor1e-6、force floor factor1e-8、checks25、Armijo1e-4、backtracks12、bisections4，均与旧inventory一致 |
| 继承原门 | production residual1e-9、average constraint1e-10、global balance1e-6、fixed displacement8e-11 mm、正J及原controller行为；不得静默改为其他更松或更紧门 |
| 保存范围 | 原API生产结果/接受态缓存、compact response、batch index和执行receipt；原source/input/result/状态身份与实际计数记录 |
| 独参/显示 | 本卡新增HP=0、新几何/节点观察=0、新plot/render=0。fresh HP及WP新图按实际结果另定新阶段；不预授权 |

源与输入：普通几何使用旧右4 mmrun的`fixture/model/source_geometry/geometry.json`及旁置`geometry.npz`，task使用同run的`task.json`；显式--repo解析。新manifest和worker签名以根任务最终真实文件为准，不在草案补猜SHA。原task raw SHA为da85758a9eaf89697c5cac657f492d565cfe7c66cf9cb74139c3464e9f667e84；原geometry JSON raw SHA为408908d2cb947e09999c6e2b2babd92b3c6b4c8c340b130908d134ae42e73286；array声明SHA为5c575f3cc33107cd792be5bc6f1986639739df8c4a605784c2a9f1125ae07497。本次作者未读取NPZ；冻结前最终输入身份由根任务明确绑定。

原方法允许line-search trial遭invalid_J或unsupported_arithmetic_range后依原controller回滚、减半并继续；这是一次求解内部原行为，不等于terminal失败后的修复重试。遇首个terminal failed/error、异常、来源变化或资源停止，保存真实已接受前缀/原class/code/reason并关闭本卡；完整target_response不能由partial冒充。无重跑、无修复再试、无force。原生产和所有旧证据目录不改。

完成判断只限“薄入口一次真实正向任务及compact response是否接通”：全原24态、峰值及卸载终点是否到达，真实调用次数/保存身份、原门和资源、输出是否可用分别报告。新result的producer/reference旗标不得据旧reference PASS回填；旧保存formatter或图只能作为人工背景。即使新production完整，也不自动授新独参、接触/压力、全切线列、HF5或收敛资格。

成本依据是旧同物理任务一次helper2489.5635228 s/outer2491.9097172 s；它支持4500/4560 s候选预算的量级判断，不保证本机新冷启动耗时或PASS。worker计数、准备mock真实结果、绑定数量、source pins、最终根审/peer及人类授权登记均待根任务按实际证据补齐后，才可冻结和单次执行。
