# W-API1 保存态身份与历史参考范围核对

2026-10-09（Asia/Seoul）。已实际完成字节/JSON核对及独立抽查；没有新的力学计算。基线提交为 `d508035fdbdbfffdc4f17eda1f26aece1e5ad700`。

整体目标是独立的有限变形／TMC正向评估器：读取普通LF几何，在明确的HF任务下输出响应，供外部研究层比较。HF不包含优化。本轮确认新CLI/API与旧right4参考所覆盖的保存数据之间的关系，为同一设计的网格实验建立可信粗网格基线。

## 已做什么，为什么这样做

新API已经独立从零完成24态加载—卸载，W-VIEW1已展示这24态的真实结构、变形和节点弱式力。本轮先比较实际文件与参考来源，判断重复计算是否能增加新的数值覆盖。[比较源码](author/compare_saved_identity.py)仅使用Python标准库，不解码NPZ、不导入HF、不调用力、切线、构模、求解、HP或绘图。

| 实际检查 | 结果 |
|---|---|
| 接受态索引、目标、加载/卸载分支、状态身份及科学字段 | 24/24一致 |
| 每态state、forces、tangents、CSC matrix档案 | 96/96对实际文件哈希一致 |
| 模型JSON/NPZ和几何JSON/NPZ | 4/4对实际文件哈希一致 |
| 原参考源及冻结副本 | 37/37当前文件与副本匹配 |
| 实际读取并哈希的不同文件 | 353份，308,949,469字节 |
| 比较器计时 | 0.6027564秒 |
| 独立首态、峰值、末态字节抽查 | 12/12对一致 |

完整逐文件、逐态记录见[identity.json](identity.json)；独立核对见[identity_peer_review.json](author/identity_peer_review.json)。[参考范围静审](author/reference_scope_review.json)保留其当时“待root字节核对”的原状态，不能用它代替已经完成的身份核对。

新旧结果JSON整体文件不同。每态差异仅为`elapsed_seconds`及由计时产生的descriptor摘要；顶层另有路径计时和状态清单摘要差异。排除计时后路径诊断一致。两次调用的历史、时钟和执行计数仍各自属于原运行；本轮没有声称两个生产实例相同。

## 证据的效果与边界

旧[right4参考summary](../../native_workpiece_001/right_margin4_cycle_001/reference/summary.json)记录了该粗网格固定方形工件24态、48次HP的通过结果。本轮实际验证旧summary对旧result/contract的绑定、37项参考源与副本、各态原raw fixture及方向档案的文件绑定；没有重新解码方向，也没有重新审计HP输出。可以据此单独引用**历史同保存快照的数学证据**，省去仅为身份确认而重复的48次HP。

该引用不满足新API现有fresh-reference入口：入口仍要求当前result文件SHA和新的`2N`次HP记录，而两份result文件SHA不同。原入口没有修改，旧summary没有改写或直接挂到新响应。`qualification_transfer=false`、新`independent_reference=not_provided`及producer flags=false保持原值。

历史范围包括该任务24接受态的总／材料／正则力、原平衡及约束门、声明的单方向切线作用和CSC组装核对。它不授予全列HP、拒绝态、能量／应力HP、压力、有效夹持、网格收敛、未来细网格、H2/H3或HF5资格。

实际物理展示仍见[W-VIEW1结果](../../../functional_views/native_api_workpiece_20261008/complete_001/RESULTS.md)和[24态动画](../../../functional_views/native_api_workpiece_20261008/complete_001/run_001/view/fixed_square/actual_states.gif)。峰值下半工件Fy=0.1193619515 N、尖端到底面距离0.0057303162 mm为保存观察值；本轮没有新增图或改变这些值。

## 接下来做什么

先补明确来源的2×2 HF细分接口，并验证同一结构的派生h=0.5 mm构模、约束、端口及未变形网格图。保持84×40 mm域、side18/center(71,40)工件、E/nu/gamma/alpha/Lr、支持/对称与物理端口，以及原24目标路径。细网格预测为13,440单元、13,689节点、27,378 DOF；实际fixed/free数量待构模。

最近阶段见[M-PREP1卡](../nested_mesh_preparation_001/M-PREP1_CARD.md)。该卡只准备模型，细网格平衡路径尚未启动。随后根据构模结果制定细网格完整路径的资源卡，比较匹配目标下的反力、工件力、间隙、J/Hu与卸载恢复；两个网格只报告敏感性，收敛研究另行开展。圆体、尺寸/位置/软硬度变体按结果逐步推进。
