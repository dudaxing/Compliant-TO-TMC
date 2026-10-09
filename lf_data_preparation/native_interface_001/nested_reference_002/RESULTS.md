# M-REF2：完整细网格保存路径的独立参考已通过

2026-10-09，M-REF2细网格完整24保存态独立参考已通过，唯一窗口已关闭。 明确批准后新HP80／120开始／完成48／48，全部24原目标机械态和24工件态通过；197绑定保持。独立终态审阅PASS确认实际来源、输入／输出身份、覆盖和已关闭资源。M-REF1失败窗口仍保持关闭，没有复用、修复重跑、延期或force。

实际helper 2067.204527899972 s／outer 2068.5294668000424 s；helper采样自身RSS峰值1390268416 B／launcher采样进程树峰值1398767616 B。冻结额度4500／4560 s、采样8 GiB；采用协作停止与采样资源，非OS硬内存上限或强制终止。HP开始／完成48／48；机械态24、工件态24。 exit0、stop_reason null。参考程序内部检查计数1,937,265与独立审阅的3289／3289只读身份／门值核对分开记录，均不是新增科学试验数量或新增数学门。

[实际launch](reference_launch.json) · [实际HP报告](run_001/reference/summary.json) · [lifecycle](run_001/reference/lifecycle.json) · [stdout](reference_stdout.log) · [授权记录](author/authorization_record.json) · [独立终态审阅](author/terminal_review.json) · [冻结卡](M-REF2_CARD.md) · [冻结协议](protocol.json)。独立终态报告原字节SHA：`55fbbec300c71ff8b7d73ac17bcc3bffc77f2a0e5aec73618d507580e2054940`。

## 整体目标、本步理由与实现

项目目标是从普通LF几何独立读取并完成HF有限变形／第三介质接触(TMC)前向评估，输出可核对的反力、结构变形与工件受力。当前已经实现完整加载／卸载、固定工件有符号总／材料／Hu弱式力和真实保存态可视化。本步给h0.5完整曲线取得自身的独立数值证据，先排除当前离散方程的生产算术／组装／平衡误差，再解释粗细网格差异；未重复昂贵生产路径，没有新增LF运行或优化器。

M-REF1唯一一次在深来源归档mkdir失败，0／0HP；其原来源、卡、协议和失败记录保留。M-REF2只修正该来源归档接口：11个唯一basename平铺在B850构造器已经创建的`sources`目录，原仓库相对路径／SHA仍记录。实际来源胶囊已形成；本机最长来源文件202字符，静态科学输出最长205字符。没有修改Windows机器路径策略、Python环境或包，也没有文件系统复现。

270行读取／身份／资源／报告薄层继承原B850 `Audit.run_state`及aa86 `WorkpieceCycleAudit.workpiece_checks`，独立数学公式、HP80／120、3000位精确散射／Inexact trap、15项原GATES与分量floor均不变。实际方向在本次授权读取后由5节点`b_in/max(abs(b_in))`生成，固定DOF零、长度27378、deltaR=0；权重为[1/8,1/4,1/4,1/4,1/8]。

输入保持13440单元／13689节点／27378DOF，fixed1548／free25830；固定工件648单元／703节点／1406DOF、与背景对称重叠37DOF。全24原索引／leg／0→1.2→0mm和当前状态身份对应。新生产F／T／模型／平衡求解／JIT／LF／观察／绘图均未调用：依据冻结入口及调用来源消费保存张量，不宣称动态hook仪器监测。

## 实际数值效果与原严格门

每个状态全部13440单元的局部三种力和声明方向切线、全部27378真实DOF的精确散射与全局三种力/action通过。保存完整未对称CSC的全部张量系数组装身份和PORT action、KKT、执行器／弹簧／支撑方程、平均约束／固定／总体平衡通过；同一完整参考投影验证有符号工件总／材料／Hu力、去重holding分区、重叠与镜像观测。

下表是已关闭24小JSON报告的实际最大归一化误差；位置保留原索引与加载／卸载leg。分量floor和原力／action归一化保持，因此这些不是某个标量工件力的百分比误差。完整原字符串、分母、局部最坏单元与原门在每态summary及参考档案中。

| 检查 | 最大归一化误差 | 原限值 | 实际位置 |
|---|---:|---:|---|
| 全局总力 | 1.5005169E-15 | 1e-11 | 原22／unloading／d=0.25 mm |
| 全局材料力 | 3.4625086E-16 | 1e-9 | 原6／loading／d=0.85 mm |
| 全局Hu正则力 | 3.5888159E-16 | 1e-9 | 原19／unloading／d=0.75 mm |
| 全局总PORT切线action | 1.0062303E-16 | 1e-10 | 原20／unloading／d=0.65 mm |
| 全局材料PORT切线action | 9.8013913E-17 | 1e-9 | 原10／loading／d=1.05 mm |
| 全局Hu正则PORT切线action | 3.3723683E-16 | 1e-9 | 原12／loading／d=1.15 mm |
| 保存CSC的PORT action | 1.2035036E-16 | 1e-10 | 原0／origin／d=0 mm |
| KKT PORT 力action | 1.2080146E-16 | 1e-10 | 原0／origin／d=0 mm |
| KKT PORT 平均约束action | 0 | 1e-10 | 原0／origin／d=0 mm |
| 保存生产残差 | 7.3879967E-10 | 1e-9 | 原14／unloading／d=1.15 mm |
| 独立HP120残差 | 7.3879964E-10 | 1e-8 | 原14／unloading／d=1.15 mm |
| 独立平均约束 | 2.5232341E-17 | 1e-10 | 原11／loading／d=1.1 mm |
| 独立总体平衡 | 8.7141063E-11 | 1e-6 | 原9／loading／d=1 mm |
| 独立固定位移(mm) | 0 | 8e-11 | 原0／origin／d=0 mm |

| 局部检查 | 最大归一化误差 | 原限值 | 实际位置 |
|---|---:|---:|---|
| 局部总力 | 1.2863119E-16 | 1e-11 | 原15／unloading／d=1.1 mm |
| 局部材料力 | 1.3989040E-16 | 1e-9 | 原12／loading／d=1.15 mm |
| 局部Hu正则力 | 1.6685577E-16 | 1e-9 | 原14／unloading／d=1.15 mm |
| 局部总PORT切线action | 9.1409239E-17 | 1e-10 | 原12／loading／d=1.15 mm |
| 局部材料PORT切线action | 1.0080375E-16 | 1e-9 | 原10／loading／d=1.05 mm |
| 局部Hu正则PORT切线action | 1.6502591E-14 | 1e-9 | 原22／unloading／d=0.25 mm |

独立HP120最低J为2.3396692E-5（原13／loading／d=1.2 mm），正J门通过。此数值是积分点最低J，图中的单元平均J另有统计意义。24态F／J／Hu从HP120参考圆整到binary64后与原保存诊断全部相同，保留为重建观察，未增加单独Hu误差门。48份新HP80／120记录均按原1e-40协议一致性门检查；原报告归一化agreement最大7.5939444E-54。解析能量只归档，未作候选能量比较／资格。

## 当前物理功能与人工检查

原物理任务保持h0.5、84×40mm下半模型、固定方形中心(71,40)mm／边长18mm，E1MPa、ν0.3、厚度20mm、gamma=alpha=1e-6和Lr80。以下是已经显示的同一M-CYCLE1保存态生产值，本次参考未重新求解或改变它们：

| 量 | 峰值原13／loading1.2mm | 卸载末态原23／0mm |
|---|---:|---:|
| 输入反力R(N) | 0.3787064524 | −2.7464981e-26 |
| 平均输出位移q_out(mm) | 1.0166993609 | −9.3100102e-25 |
| 下半工件ON-body Fy(N) | 0.1231794016 | −4.5537854e-27 |
| 钳尖坐标(mm) | (79.7016521645,30.9988556374) | (80,30) |
| 钳尖到底面有限线段距离(mm) | 0.0011443626 | 1 |

峰值工件Fy材料分量0.1219125571N、Hu正则分量0.0012668445N，两侧法向幅值和0.2463588032N；完整镜像净力(−0.0017520314,0)N是另一物理量。保持反力与ON-body力相反号。卸载微小非零残量完整保留，没有人为清零。q_out是物理端口平均位移，不是尖端距离或间隙。

[24态实际×1变形与红色工件节点力箭头](../../../functional_views/native_nested_cycle_20261009/complete_001/run_001/view/fixed_square/actual_states.gif) · [结构／钳尖与力曲线](../../../functional_views/native_nested_cycle_20261009/complete_001/run_001/view/comparison.png) · [有限距离及Fx分量](../../../functional_views/native_nested_cycle_20261009/complete_001/run_001/view/distances_forces.png) · [峰值J／Hu／固体应变场](../../../functional_views/native_nested_cycle_20261009/complete_001/run_001/view/peak_fields.png) · [第四PNG：同设计粗细六量曲线](../../../functional_views/native_nested_cycle_20261009/complete_001/run_001/view/mesh_response_comparison.png)。这是既有M-VIEW1显示，图件原字节保持；未新渲染。

同设计h1→h0.5峰值R−7.01%、工件Fy+3.20%、介质minJ−28.50%、Hu最大绝对分量+73.08%。当前数值参考把当前离散保存态的算术／平衡误差限制在原门内，粗细差异仍是离散敏感性，不能据两个网格宣称收敛。峰值自由介质minJ2.33966925e-5和|Hu|最大分量0.3614815860/mm体现强局部压缩；全path最大Hu分量0.3966806010/mm在loading0.95mm。Hu绝对分量不同于图中Frobenius范数。

## 资格边界、尚未实现与最近下一步

本次PASS属于当前精确结果／模型／任务的24个保存接受机械状态，不证明拒绝试探、所有切线列、连续体准确性或解唯一性。完整张量CSC组装核对**不等于独立HP验证所有切线列**；独立解析切线仅覆盖上述PORT方向。保存应力仅作原形状／有限性检查，没有stress-HP资格。既有region-edge overlap false不覆盖包含／自身重叠，不能作为全域无穿透证明。

本次没有授予接触压强、有效夹持、网格／域收敛或HF5整体资格；圆体自身任务、自由体／摩擦、正式标签／批量排名仍未完成。当前`stress_first_piola`是材料P；总节点弱式力还有Hu正则贡献。节点力不能直接称作压力，单用材料`P·N`也不能直接表示这套Hu模型的总表面力。

原[生产result](../nested_cycle_001/run_001/fixed_square/result.json)和[原response](../nested_cycle_001/run_001/fixed_square/response.json)保持原字节；producer flags仍false、reference/views仍not_provided，表示当时生成状态。本次独立报告是新的同身份artifact，原M-VIEW1 raw view/phase同样保持。本卡未调用公共摘要接口附加参考，没有偷偷改写历史字段。

最近的功能步骤是复用现有`summarize_saved_native_result`，对同一24态result／本次reference／既有raw view生成**新增关联response与轻交付索引**，由原phase索引关联第四粗细PNG；原response和raw view/phase均不改，不重做求解／HP或绘图。此项尚未执行，具体来源和有限资源待独立准备／审阅后再推进。

关联完成后，再准备总表面力定义：材料与Hu两部分、真实工件物理表面、对称切面以及角点分别明确，检查它们与已验证弱式holding／工件合力的关系，然后按实际结果决定压力／有效夹持研究。保持循序渐进，避免重复无用试验或直接重跑约4小时完整路径。

继续只在main开发，origin为`https://github.com/dudaxing/Compliant-TO-TMC.git`。本次输出为291个科学文件／1,935,447,146字节，以及11个来源文件，合计302文件／1,935,685,796字节；最大单文件40,367,705字节。独立审阅按原字节身份确认，没有重新计算HP或解码大型HP档案。本阶段普通JSON、HP档案和现有PNG／GIF可携带恢复，换机接续无需重新求解或生成图件；实际提交／远程／独立恢复结果由本次交付回执单独记录。
