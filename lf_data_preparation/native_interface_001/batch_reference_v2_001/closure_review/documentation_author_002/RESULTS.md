# 两例薄批量：生产、独立参考与保存显示已贯通

整体目标是让外部LF/N4普通几何，经一致明确的物理任务，得到独立HF非线性响应、有效性标识和可审查输出。HF负责正向评价；优化器和排名仍在外部研究层。本轮以两例现有设计验证薄批量API/CLI到真实生产、逐例独参、图和紧凑摘要的接通。

薄批量先预检全部JSON、共享物理声明和全新输出，再逐例调用现有evaluate_native一次；首非success保存原失败/partial，后续not_run。15项mock功能测试只是接口证据。随后两例真实生产均完成0/.005/.010/.025 mm的4个原目标态，各14F/9T/1solve；真实once delegate每例各一次，缓存保存新增F/T为0。19个共同物理键、无工件、E=1 MPa、ν=.3、γ=α=10⁻⁶、Lr=80 mm、厚度20 mm、80×40 mm下半域、原支承和端口、自由输出保持。minimum_increment=6.25e-5 mm，complete/full/tangent；原残差/平均约束、global balance1e-6、fixed8e-11 mm与正J门没有放宽。

| 设计 | 原生网格 | 末态输入 mm | 半模型输入反力 N | 加权q_out mm | min J |
|---|---|---:|---:|---:|---:|
| canonical | 1 mm | .025 | .00521459203 | .0286037185 | .996581260 |
| native_fine | .5 mm | .025 | .00375627879 | .0238778244 | .997535854 |

生产helper950.6635555 s、outer951.8787648 s，52绑定保持，原生产已关闭。V1参考因新增包装误读coords在LOAD停止，实际字段为coordinates，HP0；旧失败卡和输出完整保留。完成实际模型字段和继承依赖排查后，建立独立阶段/源/协议/输出的V2，数学和门沿用；原summary字节保留，qualified_summary只纠正本例别名与.025任务范围，并绑定原摘要SHA。

V2每例4态、8次全实际态新HP，共16新HP；canonical/fine分别77174/307574检查。canonical helper104.8475573 s、outer105.1806084 s，own/tree峰RSS338857984/342667264 bytes；fine execution receipt的helper420.8701840 s、outer423.9015102 s，own/tree峰RSS1169620992/1179213824 bytes。每例134绑定保持。双例saved-only独审PASS，核对290个原文件身份，不新增HP或数组计算。

B-VIEW2在独立120/150 s、8 GiB卡下一次PASS：helper9.775682300 s、F3 outer11.255066000 s，own/tree峰采样RSS285483008/283164672 bytes分别按原记录保存。245绑定保持，19个输出文件；每例真实4态和GIF4帧。保存缓存显示的构模/F/T/solver/HP均为0；视图saved-only闭卡独审PASS，347个文件身份已记录。PNG和GIF给出×1真实变形及明确×40补充，原网格、端口、反力箭头、节点与加权位移及J数值可人工检查；放大图不是实际形状，J不是压力。

| 设计 | 实际PNG | 全4态GIF | 自有qualified响应 |
|---|---|---|---|
| canonical | [结构与数值](../../../lf_data_preparation/native_interface_001/batch_forward_001/run_001/view/canonical/native_mean_path.png) | [动画](../../../lf_data_preparation/native_interface_001/batch_forward_001/run_001/view/canonical/native_mean_path.gif) | [JSON](../../../lf_data_preparation/native_interface_001/batch_forward_001/run_001/qualified_response_canonical.json) |
| native_fine | [结构与数值](../../../lf_data_preparation/native_interface_001/batch_forward_001/run_001/view/native_fine/native_mean_path.png) | [动画](../../../lf_data_preparation/native_interface_001/batch_forward_001/run_001/view/native_fine/native_mean_path.gif) | [JSON](../../../lf_data_preparation/native_interface_001/batch_forward_001/run_001/qualified_response_native_fine.json) |

自有qualified_response分别匹配本例result、全4态新独参及2个图链接，accepted/full-path reference为true、views matched。原生产response/index与producer_flags不回写。全切线列、接触/夹持、压力及HF5资格仍为false，保存图也不增加力学资格。

两例是不同LF设计，且原生网格分别为1和0.5 mm，不能据此声称同设计网格收敛或排名。本轮无工件：body力为null，q_out是加权端口位移而非钳尖间隙。一般有效接触、连续压力、自由体/摩擦、匹配网格、重复性合同和HF5整体仍未完成；全切线列、能量/应力/应变HP没有被本轮授予。

历史固定side18方体2/4 mm域的24态/48HP、加载卸载和弱式力图属于独立任务，不能混同本轮无工件各4态。下一步先核已有固定工件大行程任务，经现有薄API的具体实例缺口：逐项对照原任务路径、fixed_rigid几何、初始化选项、力摘要和保存输出，再选择最小功能接续。task1.1已支持square/circle及ordered_cycle，API已透传路径/模式，摘要已有body弱式力、holding、mirror/net和双侧法向幅值和；不重复实现这些入口。此处只是接续计划，没有启动新科学计算。

本轮文档记录完成的功能及证据，提交推送由发布步骤另行记录，尚不声明新commit或push完成。

[生产报告](../batch_forward_001/RESULTS.md) · [新生产index](../batch_forward_001/run_001/batch/index.json) · [V1失败记录](../batch_forward_001/reference_failure_diagnosis.json) · [双例保存独审](closure_review/dual_saved_review.json) · [视图报告](../batch_saved_view_v2_001/RESULTS.md) · [视图独审](../batch_saved_view_v2_001/closure_review/saved_closure_review.json) · [视图回执](../batch_forward_001/run_001/view_execution_receipt.json) · [批量用法](../../../docs/NATIVE_BATCH_INTERFACE.md) · [物理矩阵](../../../docs/PHYSICAL_FUNCTION_PROGRESS.md)
