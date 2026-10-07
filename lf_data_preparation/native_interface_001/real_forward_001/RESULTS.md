# 真实薄评价入口：小型无工件正向任务

整体目标是给外部LF/N4研究层提供独立HF正向响应，供比较、优选并推进HF5评价接口；HF不含优化器。此前21项纯功能验证使用JSON与模拟transport，本次通过同一个已有普通夹持器几何及明确0→0.001mm任务，验证真实入口确实只构模/求解/缓存保存一次，再生成紧凑响应。任务ID、边界及默认complete/full/tangent均保持，25个既有核心文件不改。此例没有工件，也不是新大行程夹持任务。

实际得到2个接受态。构造器、project builder、controller、native solve、cached writer、formatter、response writer七个真实委托各started/completed一次；生产F=4、T=3，缓存保存额外F/T为0。新独立参考覆盖全部实际态、3200单元和6642DOF，用4次新HP（每态80/120位）完成38640项检查；核对完整力、PORT方向切线作用及离散平衡，未核对全部切线列或独立能量。参考未借旧结果资格。

| 任务目标态保存量 | 实际值 |
|---|---:|
| 平均输入d / q_in (mm) | 0.001 / 0.001 |
| 半模型输入反力R (N) | 0.0002084120736447459 |
| 加权输出端口q_out (mm) | 0.001143715684723626 |
| 全域minimum J | 0.9998630314571697 |
| 相对平衡残差 | 1.535718e-11 |
| 相对全局力平衡 | 2.4514837e-15 |
| 全域max abs Hu (1/mm) | 7.8371174e-05 |
| 工件力 | null（没有工件，不填零力） |

输入端口三个节点ux分别为0.0009893878015、0.001002270041、0.001006072116mm；加权均值满足目标，节点没有被刚性绑成相同位移。q_out不是钳尖距离；J不是压力。complete模式保存辅助材料能量，不据此授予独立能量资格。

原比例×1图及明确标注×1000的位移补充图均使用全部2个实际保存态；保存视图新增F/T、构模、求解和HP为0。PNG和GIF引用同结果/模型/所有状态身份，未重新计算力学。

[结构、位移、力与J图](run_001/view/real_api/native_mean_path.png)；[全部实际态动画](run_001/view/real_api/native_mean_path.gif)；[图中保存数值](run_001/view/real_api/numeric_states.csv)；[新参考与视图响应](run_001/qualified_response.json)。原[result/response.json](run_001/result/response.json)保持生产时的无参考/无视图版本，没有覆盖。

| 阶段 | helper/outer上限(s) | helper/outer实际(s) | helper/outer采样峰值(bytes) |
|---|---:|---:|---:|
| production | 180/210 | 86.092118/88.071228 | 788230144/763252736 |
| reference | 180/210 | 39.578755/40.323424 | 337489920/341741568 |
| view | 60/90 | 3.227272/3.501443 | 155828224/149504000 |

各窗口均一次且8GiB采样上限，无修复重试；采样/协作停止不表示OS硬内存上限。API through-summary耗时83.668552s，不含response写出和CLI启动/stdout；与整helper/outer时钟分开。

生产原independent_HP/equilibrium/HF flags仍false；新响应单独记录同结果/all-N/2N参考匹配及请求路径通过。全切线列、连续压力、一般接触/夹持定义、HF5整体仍false/未完成。此前固定方体24态/48HP的大行程证据见[工件报告](../../../docs/WORKPIECE_ENLARGEMENT_20261007.md)；本次无工件1µm例不替代该物理任务，也不证明匹配网格或域收敛。

[生产卡](production_protocol.json) / [启动](production_launch.json) / [回执](run_001/execution_receipt.json)；[参考卡](reference_protocol.json) / [启动](reference_launch.json) / [回执](run_001/audit/execution_receipt.json) / [摘要](run_001/audit/summary.json)；[视图卡](view_protocol.json) / [启动](view_launch.json) / [回执](run_001/view_execution_receipt.json)；[闭卡进度](closure_progress.json)；[独立保存证据审阅](closure_author/001.json)。

后续依据现有证据选择同任务比较或匹配网格的一个步骤，再推进小批量和HF5重复性合同；压力/有效接触、圆体自身任务、自由体及摩擦仍需各自物理验证。
