# W-VIEW1：新 API 的真实变形、工件力与加载—卸载可视化

**成功闭卡。2026-10-08 用户明确批准后，冻结 viewer/包装/F3 唯一一次执行完成；24 个新 API 保存态全部观察，3 PNG 与全24帧 GIF 已生成。原180/240秒窗口已消耗，不用于重跑。**

整体目标是让 LF 普通几何在明确任务下进入独立 HF 有限变形/TMC 正向评估，供外部研究层比较；HF 不包含优化。本阶段把[W-API1真实执行结果](../../../lf_data_preparation/native_interface_001/workpiece_forward_001/RESULTS.md)展示给人工检查：结构怎样变形、尖端怎样接近工件、作用力怎样增长及卸载后怎样恢复。原任务、原材料与源码保持不变，没有新平衡路径或独立HP。

[执行卡](W-VIEW1_CARD.md)、[协议](protocol.json)、[明确授权](authorization_001.json)及[来源准备](preparation_receipt.json)记录范围和依据。源提交为 `66cfc1fda8a93e3897a6d37b21f36cc3db609dc5`；准备卡/协议中的“待授权/未执行”及授权记录中的“尚未启动”是冻结时历史，本报告与终态回执记录当前闭卡状态。

原84×40 mm、h1、固定边长18 mm方体中心(71,40)、右侧第三介质4 mm；E=1 MPa、ν=.3、厚度20 mm、γ=α=1e-6、Lr=80 mm。原24态0→1.2→0 mm、mechanical/chunk256/port_projection、端口和支撑均保持。新的result/response分别为 `eceef508…` / `43dd9c1f…`；173冻结绑定末核全部不变。源为原字节复用，未修绘图或力学实现。

| 实际执行 | 结果 |
|---|---|
| F3 / raw viewer | 各唯一一次；pass，exit 0 |
| 几何观察启动/完成 | 24/24 |
| 节点力观察启动/完成 | 24/24 |
| 新F/T/构模/求解/HP/JIT/LF | 均0 |
| wrapper外新增观察或力学 | 0 |
| raw viewer / whole-helper / outer | 19.0901595 / 19.7715440 / 20.4901847 s |
| helper peak / tree peak RSS | 325615616 / 327839744 bytes |
| 原预算 | whole-helper180 s / outer240 s / 采样own/tree8 GiB；无硬OS内存保证、无force |
| 图件 / GIF | 3 PNG / 24真实索引帧，300 ms/帧，声明7.2 s |
| CSV | 状态24行；节点4560行，含190个工件节点×24态 |

[F3回执](view_launch.json)、[原view回执](run_001/view/view.json)与[whole-helper回执](run_001/view/phase_view.json)均pass，无failure/stop_reason。173原绑定与174观察输入绑定不变；独立窄核核对79输出哈希和终态链。24个几何有效，raw/strict/roundoff-ambiguous overlap标志均false；固定工件lift/fluctuation均为0，原节点holding反向门通过。24态节点合计与生产缓存材料/正则/总合力精确一致。零新增力学由冻结纯模块来源及保存数组派生界定，未宣称动态mechanical hooks监测。依据：[独立终态窄核](author/terminal_readback.json)。

| 人工检查 | 图件与含义 |
|---|---|
| 峰值、卸载末态、尖端局部及Fy/R曲线 | [comparison.png](run_001/view/comparison.png)，真实×1；关于y=40的镜像仅显示 |
| 距离及signed Fx曲线 | [distances_forces.png](run_001/view/distances_forces.png)，尖端有限线段距离与工件面外first ray分别列出 |
| 保存场 | [peak_fields.png](run_001/view/peak_fields.png)，实体Green主值、自由介质单元平均J、保存Hu按单元展平后的范数 |
| 全路径及工件节点力 | [actual_states.gif](run_001/view/fixed_square/actual_states.gif)，原24个真实帧、无插值；total/material/regularization三分量 |
| 数值与节点明细 | [states.csv](run_001/view/fixed_square/states.csv)、[nodes.csv](run_001/view/fixed_square/nodes.csv)、[summary.json](run_001/view/fixed_square/summary.json) |

| 新保存态观察 | 1.2 mm峰（index13） | 0 mm卸载末态（index23） |
|---|---:|---:|
| 尖端(x,y) mm | (79.7163212171, 30.9942696838) | (80,30) |
| 尖端到底面有限线段距离 mm | 0.00573031619408 | 1 |
| 尖端到右侧有限线段距离 mm | 0.283736653269 | 1 |
| 实体minimum J | 0.975846959574 | 1 |
| 自由介质minimum积分点 J | 3.27229925458e-05 | 1 |
| 实体Green主值最小/最大 | -0.0212945081629 / 0.0328068711197 | ±2.525e-24 |
| 下半工件signed total Fy N | 0.119361951512 | -5.14918284676e-24 |
| 两侧法向幅值和2\|Fy\| N | 0.238723903024 | 1.02983656935e-23 |

峰值尖端到底面的距离约5.73 μm，图中主要靠数值标注检查。输入反力0.4072527715 N，工件下半Fy=0.1193619515 N，其中材料0.1178513816 N、正则0.0015105699 N。signed工件合力、反向holding、两侧幅值和与full mirrored net (-0.0048162478,0) N分别保留。箭头包含工件physical/cut/interior节点的弱式力；显示尺度为最大节点力0.120187143861 N对应4 mm箭头，箭头长度不是位移或压力。

尖端到left有限侧边段的欧氏距离17.7163221 mm、left面外first ray2.32736654 mm和旧node-window left2.32874601 mm属于不同定义。PNG的J色条按单元平均，最低0.0129841991，不能代替最小积分点J=3.27229925e-5；Hu展平范数图最高0.3217948868，区别于最大绝对分量0.2088465634。binary64 Green/J/Hu显示派生不授予独参资格。加载/卸载力曲线视觉重合，但图件不用于声称普遍无滞回或收敛。独立[现有像素审阅](author/visual_review.json)确认布局无裁切、图义可读；GIF只核对头/块元数据，未重新解码/渲染。

为让保存接口直接提供图链接，卡允许的既有纯JSON CLI又调用一次：[含图摘要响应](run_001/response_with_views.json)的views=matched，4个图链接身份一致，独参仍not_provided、producer flags仍false。它的共享字段仅views变化；原API wrapper的invocation、evaluation_elapsed_scope、evaluation_elapsed_seconds不由摘要入口复制，仍从原生产response/receipt获取。原生产result/response不改写。[metadata回执](metadata_linkage_001.json)记录该独立元数据操作，不把它算作新求解、观察或闭卡窗口续用。

本阶段实际效果是把新真实API结果形成可人工检查的完整变形/工件力/保存场视图，并返回可移植图链接。完整工件执行链和保存显示已贯通；新producer没有新HP、接触压力/有效夹持资格。匹配网格/域收敛、圆体自身任务、自由体/摩擦、正式批量标签/排名及HF5整体仍未完成。后续按人工图件检查与现有数值证据选择最近一步；原窗口已关闭，不重跑或扩大物理定义。
