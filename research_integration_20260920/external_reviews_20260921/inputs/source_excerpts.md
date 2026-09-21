# 跨线比较：本轮实际读取的关键源码与记录

Astra = Compliant-TO-TMC；N = Compliant-Nonlinear-TMC-A；LF = Diversity-TO-Compliant-O。这里的原文包含各来源当时的解释，不等于审阅者接受其中每个解释。P4a关于池独立性、控制等价和区间端点的限制见比较报告。

## Astra/research_integration_20260920/INTEGRATION_DECISIONS.md · L1–L51

```text
1: # 2026-09-20研究接入决策：LF资产、N19经验与O线接触验证
2: 
3: 本文记录本轮根任务当前采用的路线及其理由，重点从LF数据、任务定义和研究可比性的角度划清范围。它是实施取舍和验收边界，不是下列功能均已完成的声明。后续实际实现、实验输出和验收状态应由本轮实现报告逐项记录。新来源的完整身份和读取验证见 [LF10_SOURCE_AUDIT.md](LF10_SOURCE_AUDIT.md)，输入清单见 [input_inventory.json](input_inventory.json)。
4: 
5: ## 1. 长期目标与当前起点
6: 
7: 长期目标是建立独立、可搬迁的正向力学评价器：仅依赖HF仓库、独立环境、普通几何数据和版本化物理任务，就能对柔顺机构输出有单位、符号、有效性和误差证据的非线性/接触响应。待同任务评价可靠后，再研究在固定预算下，LF质量、多样性和任务匹配排序如何影响找到已验证优良设计的概率。数据身份、几何资格、数值平衡、接触可容许性、模型误差和统计效能分别成立，不能由“求解器返回成功”替代。
8: 
9: O线起点为稳定0.5.0：HF4-B四组冻结均匀法向路径已完成指定验收；显式lift/fluctuation双分量状态解决了已取证的绝对位移舍入平台问题；独立高精度检查读取实际两数组。这个基线并未证明一般非均匀接触、固定圆柱、真实机构接触或候选排名的精度。旧失败和冻结证据不追溯改写，原395文件几何包继续冻结。
10: 
11: LF(10)提供更多可独立读取的候选与接口语义；N(19)提供另一条线的接触失败案例、受限实体接触模型及后续研究记录。它们能帮助设计本线验证，但其关闭状态和外部审阅结果不自动成为O线HF4-C/D或HF5已完成的证据。
12: 
13: ## 2. 本轮采用、暂不采用与待验证事项
14: 
15: | 事项 | 决策 | 理由及实际边界 |
16: |---|---|---|
17: | O0.5.0材料/非线性内核、split状态、原严格门槛 | 保留 | 已有固定状态、全路径与HP证据；不为新任务成功而改松停止门槛或折回单数组 |
18: | LF(10)普通JSON/NPZ、区域说明、索引、C1 | 采用为可追溯来源 | 只读准备/转换，HF运行不导入LF优化代码；新版本与冻结395文件并列 |
19: | E006补集与附着语义 | 采用为将来导入合同和测试项 | 物理背景区间(60,80]在消费者网格派生；支承附着政策显式；反力标签避免重复 |
20: | 1800正式池的严格资格状态 | 部分已独立验证，其余保留来源状态 | 本轮独立验证哈希、数组、二值体积和4/8连通；完整支承刚性、端口及非线性稳定性未重新验证 |
21: | N19实体—工件交面积诊断 | 独立实现并验证 | 积分点J>0仅是局部检查；必须另检实体与已定义障碍的重叠 |
22: | 全接受态的严格有效前缀 | 独立实现并验证 | 插入态首次失效必须截断其后的可比较区间；后续局部恢复不自动修复路径历史 |
23: | 小尺度固体宽平面A0 | 下一步受限参照验证 | 预先闭合接触分支上先核验均匀、非均匀响应及可容许性；不实现一般主动集 |
24: | N19有限平面主动集A源码/默认容差 | 不直接移植 | 存在任务、边缘、事件和数值政策差异；读其失败机制，独立确定O线可审核范围 |
25: | 完整实体A与TMC同任务对账 | 后续阶段 | 待A0及诊断接口验证后再评估有限面进入/释放/重入、角点作用域、共同控制和误差方案 |
26: | 直接拿N线A替代O线主评价器 | 当前不采用 | N线选择A有其任务与成本依据；O线当前工作是补足自身验证链，未完成同任务对账 |
27: | 因N19高alpha结果更接近A而改O线正则参数 | 当前不采用 | 来源现象不是跨任务通用参数；必须分离实现误差、介质偏差、边界与几何失效 |
28: | HF5候选统计、1800池重算、S0/S1/S2结论 | 暂缓 | 当前接触评价尚未对新任务建立可信有效域，不能把运行规模当验证替代 |
29: | 新LF优化、重新二值化/清理旧几何 | 当前不采用 | 新包已有充足普通资产；先隔离力学问题，避免同时改变生成政策和评价器 |
30: | 真实限力控制、摩擦、三维、稳定性认证 | 本轮范围之外 | 需要独立模型与验证；有限位移路径读出不自动覆盖这些物理问题 |
31: 
32: “不直接移植”不否定来源研究价值；它保证本线判断能够回到明确的本地任务、状态、公式和独立检验。
33: 
34: ## 3. 最近可实施顺序及停止边界
35: 
36: ### 阶段I：障碍交面积与严格有效前缀
37: 
38: 先独立实现变形实体单元与已定义几何障碍的交面积计算。起步对象应是可明确计算交集的小尺度二维障碍；输入为实际权威状态产生的变形坐标、实体标记和障碍几何，不能从显示用的单数组舍入和恢复权威split状态。面积单位、边界接触的零面积语义、退化/非法单元处理和容差都显式记录。该诊断检测给定障碍重叠，不证明全域映射单射，也不自动检测全部自接触。
39: 
40: 验证应包含零交、边界贴合、部分交、全包含、平移/方向/尺度变化和非法输入等独立可算情形；实际实现细节与门槛在执行前形成任务配置。源N19的多边形裁剪函数不作为本地算法被直接调用，也不能用同一实现输出充当独立真值。
41: 
42: 同时建立接受态分类：数值平衡状态、局部几何/接触有效性、是否到达目标、是否位于严格有效前缀分开保存。沿全部已接受状态顺序检查，包括二分插入态，记录首次失效及原因；首次失效之后的共同检查点即使局部有效，也不得作为该路径的可比较结果。保留这些数值供诊断，不归零、不删失、不跨失效区间插值。没有达到的目标是未到达，不是物理零接触力。已到达且验证无接触可以是有效零力。
43: 
44: 阶段I只增加诊断与诚实的范围分类，不因分类代码通过而宣布接触力精度已验证。
45: 
46: ### 阶段II：受限A0宽平面、已闭合接触分支
47: 
48: 根任务当前计划是使用小尺度实体、足够宽的刚性平面，在预先定义并确认已闭合的接触分支上构造A0参照。先完成可独立解析核对的均匀情形，再验证同一受限范围内的非均匀情形。实体本构、单元、厚度、边界、载荷/位移控制、测力符号和接触面范围全部写入任务；与TMC作任何比较之前先保证任务等同。
49: 
50: A0在这个阶段不搜索一般主动集，不声称处理接触进入、拉力释放、有限边缘越界/重入或任意角点/侧面接触。闭合分支的假设也需要检查：法向压力非负、对应节点/边处于作用域、非接触约束满足、无实体—障碍交面积超限、平衡与功共轭测力通过。若假设失败，应明确拒收或记录超出A0范围，不能靠“预先闭合”的名称跳过可容许性检验。
51: 
```

## Astra/research_integration_20260920/INTEGRATION_DECISIONS.md · L87–L104

```text
87: 
88: 这些约束不要求本线此刻重新打开N线P3/C1、改变原研究记录或启动1800条新HF路径。它们解释为何本线先补足力学有效性，再开展HF5。
89: 
90: ## 6. 新LF资产将来的最小接入条件
91: 
92: 准备环节只能消费普通JSON/NPZ。若需要转换新包，建立独立新数据版本并保存ZIP哈希、成员路径/哈希、来源geometry_id和新HF geometry_id映射；禁止原位修改395文件，禁止在HF运行时导入LF生成或测量模块。
93: 
94: 读取器应严格处理网格顺序、原点、单位、厚度、bool/uint8、三分掩膜、包内相对路径和数组hash；不能复用来源节点号代替物理段。在原生、160×80和320×160等消费者网格上验证E006补集派生、x=60归属、全线覆盖、支承附着和反力分组去重。端口权重应由参考弧长重新产生，不能把原生三节点权重套到五节点细网格。
95: 
96: 跨LF/HF比较先使用无弹簧严格实体线性的gain/输入刚度建立接口桥接，记录控制方式差异；原生去地板分数、C1恢复分数、严格实体参考各有独立字段。新正式池的资格阈值不追溯改写旧两例诊断身份，旧两例也不因为被重复导出而获得研究准入。
97: 
98: 支承附着长度0.5/1.5/2mm可用于后续有限样本的边界/网格敏感性分层。不得用全池“连通且体积合格”推断接触稳定、无局部锁定、性能排名可信或材料可用。
99: 
100: ## 7. 成果表述与后续报告要求
101: 
102: 本轮结果应分别列出：来源读取审计、独立诊断实现、合成测试、受限A0数值检查、仍未覆盖的任务。保留失败状态、原门槛和版本，不将来源会话中的测试数或外部关闭决定记入本仓库实际测试数。
103: 
104: 若A0依赖稳定内核，明确写出共享部分和独立部分；若比较只涵盖已闭合宽平面分支，标题与结论也保留该限定。对失效前缀之外的目标不补分、不按候选切换评价器、不用其他任务结果替代。实际完成到哪里、哪些证据尚缺，按输出文件说明，不以长期研究目标替代当前验收状态。
```

## Astra/docs/HF4_C0_RESEARCH_INTEGRATION.md · L1–L51

```text
1: # HF4-C0：新研究审阅、选择性融合与参照准入
2: 
3: 日期：2026-09-20。状态：本轮来源审阅、诊断融合、受限 A0 参照准入已完成；**整个项目以及一般非均匀 TMC 接触验证仍未完成**。科学基线为 `hf_repo` 0.5.0 / `b1334bb6a83ba9a0efab7bdba7bd39722146f024`。本轮是新增实验性扩展，不改变旧 HF4-B 的物理合同和历史证据。
4: 
5: ## 目标、当前工作与理由
6: 
7: 长期目标是建立独立 HF 力学评价器：在任意工作目录、仅依赖普通几何数据和 HF 环境即可运行；对有限变形与接触的输出，明确任务、单位、符号、数值平衡、接触可容许性、失败路径和证据。它最终服务于固定预算下柔顺机构候选的可靠比较，而不是把 LF 分数或求解器成功标志直接当作物理正确性。
8: 
9: 本轮用户提供 LF(10)、TMC-A(19) 和“TMC开发”研究会话。我们先核对其来源、任务和证据强度，再独立实现有用的方法。资料内的旧阶段安排和授权只作研究背景，不替代当前用户请求。当前用户授权取舍与融合，因此没有机械照搬另一条线的任务、1800 次试验安排或默认求解政策。
10: 
11: 最有用的新增证据是：候选接触节点不穿透、Newton 残差达标时，单元边仍可能跨进工件角点；N19 的真实细网格案例报告了约 `0.0072228517365 mm²` 重叠。故必须把几何失效识别与可信接触参照放到大样本计算之前。
12: 
13: ## 阅读结果与取舍
14: 
15: 完整来源与决策见 [LF 来源审计](../research_integration_20260920/LF10_SOURCE_AUDIT.md)、[N19 来源与代码复核](../research_integration_20260920/N19_SOURCE_AND_CODE_REVIEW.md)及[集成决策](../research_integration_20260920/INTEGRATION_DECISIONS.md)。关键结论如下。
16: 
17: | 发现 | 本线处理 |
18: |---|---|
19: | 新 LF 两例四类掩膜与冻结两例逐格相同；原 395 文件集校验通过 | 保留旧几何及其原资格，不重写数据 |
20: | E006 明确背景物理补集 `(60,80]` 与实体附着支承 | 纳入将来 v2 导入合同；当前 `project.py` 已有全线背景和实体附着政策，不能据此宣告旧实现有同一缺陷 |
21: | 正式池 1800 包的身份、数组、体积与连通性可独立读取核对；完整优化历史归档在包外 | 采用可追溯普通数据，暂不启动 HF5 标签重算 |
22: | C1 修正评分 reference，且发生于另一条线 HF 解盲后 | 保留原分数和修正值各自来源；不把恢复排序冒充预先冻结顺序 |
23: | N19 的实体接触 A 与 TMC 共用材料/FE/求解器 | 独立的是接触处理层；不能作为完全独立的 FE 真值 |
24: | N19 使用单 U 与不同残差政策、参考力尺度底值 | 保留 O 线稳定内核、split 状态及原严格门槛 |
25: | 增大 α 能改善部分穿透，但同时改变近接触力和寄生刚度 | 不直接迁移 α=1e-5；须在同任务下分别评估 |
26: 
27: 本轮没有执行附件里的 LF 优化或 N19 求解脚本，没有声称在 N19 的 Python 3.11 环境复现其结果。新计算均使用 O 的 Python 3.13.6、NumPy 2.4.6、SciPy 1.17.1、JAX/JAXLIB 0.11.0 环境。原论文、MATLAB 原码和附件完整源目录没有加入公开仓库。
28: 
29: ## 实际修改
30: 
31: 新增 [contact_audit.py](../hf_repo/src/hf_eval/contact_audit.py) 实现严格凸、逆时针 Q4 与固定轴对齐矩形的交面积；非法、退化、自交或数值溢出的单元返回“不可评估”，不能以零面积通过。所有容差必须显式输入。该模块只检查实体—障碍重叠，不宣称自接触检查或任意障碍支持。
32: 
33: 同一模块新增严格有效前缀。每个接受态必须有明确的求解、几何和独立参考有效性字段；第一个失效点截断其后的计分，后续局部恢复不能恢复评分，未知 `None` 与真实零响应分开。通用工具保留时间顺序，支持卸载；A0 审计另外强制本任务单调加载、完整原目标和全部插入态清单。
34: 
35: 新增 [contact_reference_a0.py](../hf_repo/src/hf_eval/contact_reference_a0.py) 作为受限任务构造器，并新增执行、隔离、独立审计和汇总脚本。A0 使用现有 O 材料、积分和 split 求解器，**没有实现一般主动集**。只有逐态法向乘子非负、几何有效和自由 DOF 平衡通过时，规定上表面法向位移才可解释为该分支上的单边无摩擦接触。
36: 
37: 既有跟踪的生产内核、求解器和 HP helper 未修改。原来的 0.5.0 wheel、HF1–HF4 结果和失败记录均保留。
38: 
39: ## 预先冻结的计算与独立验收
40: 
41: [计划](../research_integration_20260920/EXPERIMENT_PLAN.md)和[完整协议](../hf_repo/configs/contact_reference_a0_v1.json)在新 FE 计算前写定；协议 SHA256 为 `20cbadef31797287e850ceab8f912facd71c2d6389354750e4cbc05bd9dac7e7`。
42: 
43: 实体为 2×1 mm、厚度 1 mm；E=100 N/mm²、ν=0.3；仅实体、kr=0。障碍下表面 y=1 mm，水平范围远离实体边缘。初态已经闭合，上表面 uy=0、ux 自由；底面 uy=d·[1+a·(1−3(x−1)²)]，仅底中心 ux 固定以消除水平刚移。网格 h=0.25/0.125 mm；a=0、0.125、0.25；d=0、0.03125、0.0625、0.125、0.25 mm，共六条路径。
44: 
45: 先验收两条均匀路径，再运行四条非均匀路径。几何 lift 不包含解析平衡解。每态保存实际 `u_lift`、`u_fluctuation`、内力、J 和任意固定测试方向的 Jv；HP 公式提升两数组的精确和，不使用显示用的合并位移。独立 50/80 位参考重建网格、Q1 导数、积分和边界；核对存储哈希链、完整目标清单、残差、约束、力、切线作用、反力平衡、乘子和节点位置。均匀路径另用 Pxx=0 的独立标量解析公式验力。
46: 
47: 法向力定义为 `−Σfint_top,y`，正值表示模型作用于障碍的压缩力。非均匀底面控制的 `drive_force` 是带空间 profile 权重的功共轭广义力；底面竖向合力另取 `group_reactions.bottom`，二者不混用。
48: 
49: 几何裁剪使用一次准确舍入的节点位置，同时相对 80 位节点坐标记录舍入误差。本轮实际 HP 节点均满足 y≤1；由 Q1 形函数非负且和为 1，单元内部亦不越过该水平平面。这个实际结果比仅通过 y≤1+1e-12 容差门更强，不能把它外推至任意障碍。
50: 
51: ## 结果与效果
```

## Astra/docs/HF4_C2_KINEMATICS_REPAIR_PLAN.md · L1–L26

```text
1: # C2 失败后的稳定运动学修复计划（尚未执行）
2: 
3: 本计划基于 [C2 最终诊断](HF4_C2_FINAL_REPORT.md) 和 [固定失败态算术分段证据](../hf4_c2_diagnostics/force_precision_001/summary.json)。目的只在于修复强压缩小量 F 的生产求值精度，保持既有物理弱式、材料、边界、载荷、双数组位移权威、验收门和历史证据不变。不能把固定状态的算术反事实当作新内核已经通过验收。
4: 
5: ## 1. 先实现并核对稳定 F 运算，不求解路径
6: 
7: 以新模块/明确的新实现版本承载候选，保留旧内核及原失败。比较局部差分、补偿求和或误差补偿展开的可微实现；选择依据是保存场和制造场精度，不是末态净力拟合。当前 `math.fsum` 全分量正确舍入只在本 dyadic 梯度上观察到，不可直接推广到一般非 dyadic 单元、乘积舍入或任意几何。需明确适用单元范围，处理乘积与求和误差。
8: 
9: JAX 的代数重排可能抵消补偿项，必须检查实际编译路径；不能假设 Python 括号足以固定运算。保留正 J 原始域检查、近单位增量材料分支、双数组实际增量预测器以及 HuHu 原弱式，不添加裁剪、小 J 截断或新的能量项。
10: 
11: ## 2. 力、导数与回归的共同准入
12: 
13: - 在完全相同的失败双数组上，新生产完整内力向量应满足原 1e-11 总力求值门，仍使用原 SF；新代码不得读取 HP 力作为生产答案。
14: - 独立 80/120 位的材料/正则分量及 Jv 沿用原门。核对补偿/自定义微分规则与实际残差的一致切线，不只检查 F 或净顶面力。
15: - 覆盖近刚体、小应变、剪切、非零 Hu、强压缩、不同网格和非 dyadic 输入；对可支持的输入范围明确说明。使用独立方向导数和制造场，不用同一实现复制出“参考”。
16: - 在 C1 及已通过 C2 保存状态上检查新旧行为和来源身份。旧准入结果保留，不因新脚本而改写旧审计。任何真实物理变化须另列任务，不能夹带在算术修复中。
17: 
18: ## 3. 通过无求解检查后再冻结一次新路径
19: 
20: 先由独立审查确认方案和切线证据，再写新的修复协议、实现哈希、输出目录、预算及停止条件。第一条补测应是原失败的 h=0.0625 均匀七目标任务；保持原参数、初值、几何、目标和门槛。使用新目录，旧 `experiments/mesh_h00625` 永久保留为不通过。
21: 
22: 若新路径仍失败，按首次失效状态停止并保存全部接受记录，不自动重试、调 gamma/alpha、降低容差或提高资源上限。通过后再判定是否需要有针对性的历史路径补测；不能只凭末态固定场改进宣称完整路径或跨平台稳定性。
23: 
24: ## 4. 与总体路线的关系
25: 
26: 本项关闭的是生产运动学的算术问题，不同时解决连续网格收敛、体积分阶数、高阶广义边界条件、一般部分接触或真实机构资格。修复验收之前保持 HF4-C open，不进入 HF5。后续接触参考范围继续以 C2 已观察的边界敏感性和远端材料拉应力为依据，不按净力接近程度挑选模型。
```

## Astra/hf_repo/src/hf_eval/data.py · L1–L44

```text
1: """Portable binary-cell geometry records, independent of any geometry producer."""
2: 
3: from __future__ import annotations
4: 
5: from copy import deepcopy
6: from dataclasses import dataclass
7: from hashlib import sha256
8: from io import BytesIO
9: import json
10: from pathlib import Path
11: from typing import Any
12: from zipfile import BadZipFile
13: 
14: import numpy as np
15: 
16: 
17: ARRAY_NAMES = ("solid", "design", "passive_solid", "passive_void")
18: SCHEMA_VERSION = "hf-geometry-1.0"
19: 
20: 
21: class GeometryError(ValueError):
22:     """A geometry record is invalid, unsupported, or fails integrity checks."""
23: 
24: 
25: @dataclass(frozen=True)
26: class Geometry:
27:     metadata: dict
28:     arrays: dict[str, np.ndarray]
29:     path: Path
30: 
31:     @property
32:     def solid(self) -> np.ndarray:
33:         return self.arrays["solid"]
34: 
35:     @property
36:     def grid(self) -> dict:
37:         return self.metadata["grid"]
38: 
39:     @property
40:     def geometry_id(self) -> str:
41:         return self.metadata["geometry_id"]
42: 
43: 
44: def _canonical(value: Any) -> Any:
```

## N/scripts/run_n4_p3_labels.py · L1–L23

```text
1: #!/usr/bin/env python3
2: """N4-P3 stage C: the HF label library of the formal pools (primary evaluator A, fixed workpiece task, main label F_n(5 mm)).
3: 
4: Protocol: docs/N4_P3_protocol_v1.md section 4 (frozen).  Every unique strictly qualified member of every pool is evaluated
5: with the solid frictionless contact reference A under the N3b / N3c task: block x in [70, 80] x y in [32, 40] mm, pointwise
6: input u_x = d, E = 1 MPa, nu = 0.3, t = 20 mm, 160x80, N3b reference solver settings, the load path d = 0.5, 1, 1.5, 2,
7: 2.5, 3, 4, 5 mm (the existing prefix; never a jump from 0 to 5 mm).  The N3c post-processing (version 2) is reused
8: unchanged: the comparable prefix ends at the first geometrically invalid accepted state of the whole path (inserted states
9: included) or at the first not-reached checkpoint; a later locally valid 5 mm value is not a label.
10: 
11:   label value = F_n(5 mm) when the 5 mm checkpoint is comparable (0.0 for a valid state without contact)
12:               = None with a reason otherwise (unknown is not zero; the logical budget is still consumed; no TMC substitute)
13: 
14: The stage refuses to start unless the orders manifest of ALL pools exists and every file it lists still has the recorded
15: hash (selection before unblinding).  Identical geometries (same geometry_id) are computed once and referenced explicitly;
16: the pools stay separate samples.  float64 run folders go to tmp/n4_p3_label_runs and from there to the external archive
17: (stage n4_p3_formal_v1 -> n4_p3_hf_labels/v1); the repository keeps the label table, the effective configuration and the
18: archive manifest.
19: 
20:     python scripts/run_n4_p3_labels.py --lf-record <LF repo>/research/n4_formal_gripper_v1 [--workers 12] [--resume] [--no-archive]
21:     python scripts/run_n4_p3_labels.py --handoff-check      # pipeline regression on the 12 OLD handoff grippers against the N3c table
22: """
23: from __future__ import annotations
```

## N/experiments/n4/selection.py · L1–L97

```text
1: """N4 selectors: selection orders from LF-side information only (standard library only).
2: 
3: INFORMATION BOUNDARY (docs/N4_experiment_design_plan_v1.md section 3): this module receives the LF-only candidate file
4: and the geometric distance file and nothing else.  It must never import the HF descriptor module or open an HF result
5: file; HF labels are merged only after the orders have been written to disk and hashed.
6: 
7: Sets: P = pool (qualified, exact duplicates merged); C = {i in P : L_i > 0 and L_i >= eta * L_max(P)} = common quality
8: set.  All three strategies select from the same C, share the same first pick (the LF-best member of C) and produce ONE
9: order each; every budget k uses the prefix of that order (nested selections).
10: 
11:   S0  LF-first:                     C by decreasing LF score
12:   S1  same-gate shared-first random: LF-best first, the rest a random permutation without replacement (recorded seeds)
13:   S2  shared-first topology-diverse: LF-best first, then greedy maximin on the geometric distance
14:       (largest minimum distance to the selected set; ties -> larger LF score -> design_id ascending)
15: 
16: Ties in the LF score are broken by design_id ascending (stable key).
17: """
18: from __future__ import annotations
19: 
20: import hashlib
21: import json
22: import random
23: from pathlib import Path
24: from typing import Any
25: 
26: SCHEMA_ORDERS = "tmcn.n4.orders.v1"
27: 
28: 
29: def text_sha256(path: str | Path) -> str:
30:     """Newline-portable identity of a text file (CRLF normalised to LF), same policy as the descriptor table."""
31: 
32:     return hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
33: 
34: 
35: def quality_set(candidates: list[dict[str, Any]], eta: float) -> list[dict[str, Any]]:
36:     """C in LF order: positive LF score and at least eta times the best LF score of the pool."""
37: 
38:     positive = [c for c in candidates if c["lf_score"] is not None and c["lf_score"] > 0.0]
39:     if not positive:
40:         return []
41:     l_max = max(c["lf_score"] for c in positive)
42:     return sorted((c for c in positive if c["lf_score"] >= eta * l_max), key=lambda c: (-c["lf_score"], c["design_id"]))
43: 
44: 
45: def order_lf_first(quality: list[dict[str, Any]]) -> list[str]:
46:     return [c["design_id"] for c in quality]
47: 
48: 
49: def order_shared_first_random(quality: list[dict[str, Any]], seed: int) -> list[str]:
50:     ids = [c["design_id"] for c in quality]
51:     rest = ids[1:]
52:     random.Random(seed).shuffle(rest)
53:     return ids[:1] + rest
54: 
55: 
56: def order_shared_first_maximin(quality: list[dict[str, Any]], distances: dict[str, Any]) -> list[str]:
57:     index = {design_id: k for k, design_id in enumerate(distances["ids"])}
58:     matrix = distances["matrix"]
59:     score = {c["design_id"]: c["lf_score"] for c in quality}
60:     ids = [c["design_id"] for c in quality]
61:     selected = ids[:1]
62:     remaining = sorted(ids[1:])  # design_id ascending: max() keeps the first of equal keys
63:     while remaining:
64:         pick = max(remaining, key=lambda i: (min(matrix[index[i]][index[s]] for s in selected), score[i]))
65:         selected.append(pick)
66:         remaining.remove(pick)
67:     return selected
68: 
69: 
70: def selection_orders(candidates_file: str | Path, distances_file: str | Path, *, eta: float, n_random: int, base_seed: int) -> dict[str, Any]:
71:     """Read the two LF-only files and return the orders document (nothing else is read)."""
72: 
73:     cand_doc = json.loads(Path(candidates_file).read_text(encoding="utf-8"))
74:     dist_doc = json.loads(Path(distances_file).read_text(encoding="utf-8"))
75:     if cand_doc.get("information_class") != "LF-only" or dist_doc.get("information_class") != "LF-only":
76:         raise ValueError("the selector accepts LF-only files")
77:     pool = cand_doc["candidates"]
78:     if sorted(c["design_id"] for c in pool) != sorted(dist_doc["ids"]):
79:         raise ValueError("candidate ids and distance ids differ")
80:     quality = quality_set(pool, eta)
81:     in_c = {c["design_id"] for c in quality}
82:     ids_c = [c["design_id"] for c in quality]
83:     position = {design_id: k for k, design_id in enumerate(ids_c)}
84:     permutations = [[position[i] for i in order_shared_first_random(quality, base_seed + r)] for r in range(n_random)]
85:     return {"schema": SCHEMA_ORDERS, "case": cand_doc["case"], "information_class": "LF-only",
86:             "inputs": {"candidates": {"file": Path(candidates_file).name, "sha256": text_sha256(candidates_file)},
87:                        "distances": {"file": Path(distances_file).name, "sha256": text_sha256(distances_file)}, "hash_policy": "sha256 of the text with CRLF normalised to LF"},
88:             "eta": eta, "lf_score_name": cand_doc["lf_score_name"], "pool_ids": sorted(c["design_id"] for c in pool), "quality_set_ids_lf_order": ids_c,
89:             "gated_out_ids": sorted(c["design_id"] for c in pool if c["design_id"] not in in_c), "shared_first_pick": ids_c[0] if ids_c else None,
90:             "orders": {"S0_lf_first": order_lf_first(quality), "S2_shared_first_maximin": order_shared_first_maximin(quality, dist_doc) if quality else []},
91:             "S1_shared_first_random": {"base_seed": base_seed, "n_permutations": n_random, "seed_rule": "permutation r uses random.Random(base_seed + r)",
92:                                        "index_base": "positions in quality_set_ids_lf_order", "permutations": permutations}}
93: 
94: 
95: def s1_orders(orders_doc: dict[str, Any]) -> list[list[str]]:
96:     ids = orders_doc["quality_set_ids_lf_order"]
97:     return [[ids[k] for k in perm] for perm in orders_doc["S1_shared_first_random"]["permutations"]]
```

## N/src/tmcn/archive.py · L1–L43

```text
1: """Location and verification of the float64 scientific archives (kept OUTSIDE the code repository since 2026-09-16).
2: 
3: Owner decision after the N3b revision review: the code repository keeps the sources, tests with small fixtures, rules,
4: summaries, selected figures and an ``archive_manifest.json`` per stage (file list with SHA-256); the full float64 run
5: directories (``result.json`` with every Newton / active-set history and ``fields.npz`` with every accepted displacement
6: field) live in an external, immutable archive with at least two verified copies.  Git history is not rewritten.
7: 
8: Layout of an archive root::
9: 
10:     <root>/<stage>/<version>/<run path>/result.json
11:     <root>/<stage>/<version>/<run path>/fields.npz
12:     <root>/<stage>/<version>/index.json          (same content as the repository manifest)
13: 
14: The root is taken from the environment variable ``TMCN_ARCHIVE_ROOT``; without it the default sibling directory of the
15: repository (``../TMC_A_scientific_archive``) is tried, then the legacy in-repository location ``research/<stage>/raw_float64``.
16: Absolute machine paths never enter a scientific record: run identities are the relative archive paths and the hashes.
17: New runs are appended with ``scripts/archive_raw_states.py`` (two-phase incremental append: old entries kept, identical
18: runs idempotent, conflicts abort without touching files or index).
19: """
20: from __future__ import annotations
21: 
22: import hashlib
23: import json
24: import os
25: from pathlib import Path
26: from typing import Any
27: 
28: REPO = Path(__file__).resolve().parents[2]
29: ENV_ROOT = "TMCN_ARCHIVE_ROOT"
30: DEFAULT_ROOT = REPO.parent / "TMC_A_scientific_archive"
31: STAGES = {"nonlinear_pilot_v1": ("n2_nonlinear_pilot", "v1"), "n3a_free_output_v1": ("n3a_free_output", "v1"), "n3b_contact_v1": ("n3b_contact", "v1"),
32:           "n3c_gripper_coverage_v1": ("n3c_gripper_coverage", "v1"), "n3d_contact_exploration_v1": ("n3d_contact_exploration", "v1"),
33:           "n4_p3_formal_v1": ("n4_p3_hf_labels", "v1")}
34: RUN_FILES = ("result.json", "fields.npz")
35: 
36: 
37: def manifest_path(stage: str) -> Path:
38:     return REPO / "research" / stage / "archive_manifest.json"
39: 
40: 
41: def candidate_roots(stage: str) -> list[Path]:
42:     name, version = STAGES[stage]
43:     roots = []
```

## N/research/n4_p4a_mechanism_diagnosis_v1/summary.md · L1–L92

```text
1: # N4-P4a 机制诊断：可复算表（探索性，只读已有数据）
2: 
3: 由 `experiments/n4/p4a_mechanism_diagnosis.py` 生成；设计 1800 个、有效主标签 1799 个、池 200 个；LF 分数除注明外为恢复冻结口径版（勘误 C1）。不求解任何结构；不改变 P3 的预注册结果；下列比率都不是确认性结果。
4: 
5: ## A1 方差分解（弹簧格 / 池种子 / 残差）
6: 
7: | 量 | 弹簧格 | 池种子 | 残差 |
8: | --- | --- | --- | --- |
9: | LF score L (restored) | 99.73 % | 0.08 % | 0.19 % |
10: | LF score L (executed) | 99.73 % | 0.08 % | 0.19 % |
11: | F_n(5 mm) | 99.84 % | 0.04 % | 0.12 % |
12: | gain g | 99.82 % | 0.06 % | 0.11 % |
13: | K_in | 99.65 % | 0.10 % | 0.25 % |
14: | blocked-output compliance | 99.81 % | 0.05 % | 0.14 % |
15: 
16: ## A1 同格跨种子、A3 线性预测、A4 格中位数
17: 
18: | 弹簧格 | n | g | K_in (N/mm) | L (mm) | d_c 线性 (mm) | F_lin(5) (N) | F_n(5) (N) | HF/线性 | CV(L) | CV(F_n) | τ(L, F_n) 同格 | HF 小行程增益/g | HF 小行程输入刚度/K_in | HF R_in(5)/线性 |
19: | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
20: | (0.1, 1) | 200 | 0.5281 | 0.0350 | 0.3528 | 3.788 | 0.3603 | 0.2971 | 0.825 | 1.09 % | 4.57 % | 0.650 | 1.0021 | 1.0296 | 0.876 |
21: | (0.1, 3.16) | 200 | 0.4780 | 0.0385 | 0.3189 | 4.184 | 0.2311 | 0.1629 | 0.713 | 1.02 % | 8.85 % | 0.646 | 0.9994 | 1.0048 | 0.840 |
22: | (0.1, 10) | 200 | 0.4581 | 0.0396 | 0.3053 | 4.366 | 0.1760 | 0.1095 | 0.614 | 1.07 % | 16.93 % | 0.715 | 0.9985 | 1.0016 | 0.824 |
23: | (1, 1) | 199 | 0.9528 | 0.1523 | 0.5910 | 2.099 | 1.1007 | 1.0481 | 0.952 | 1.56 % | 1.86 % | 0.815 | 1.0090 | 1.0207 | 1.026 |
24: | (1, 3.16) | 200 | 0.8523 | 0.1458 | 0.5305 | 2.347 | 0.9896 | 0.9477 | 0.959 | 1.39 % | 2.19 % | 0.825 | 1.0074 | 1.0177 | 1.005 |
25: | (1, 10) | 200 | 0.8176 | 0.1414 | 0.5104 | 2.446 | 0.9421 | 0.9022 | 0.959 | 1.20 % | 2.24 % | 0.813 | 1.0069 | 1.0201 | 0.997 |
26: | (10, 1) | 200 | 1.1248 | 0.2299 | 0.6655 | 1.778 | 1.2107 | 1.1190 | 0.925 | 1.33 % | 0.93 % | 0.680 | 1.0110 | 1.0264 | 1.058 |
27: | (10, 3.16) | 200 | 1.0109 | 0.2180 | 0.6027 | 1.978 | 1.1374 | 1.0742 | 0.945 | 1.18 % | 1.19 % | 0.778 | 1.0094 | 1.0218 | 1.042 |
28: | (10, 10) | 200 | 0.9691 | 0.2144 | 0.5782 | 2.064 | 1.1006 | 1.0467 | 0.951 | 1.18 % | 1.27 % | 0.769 | 1.0088 | 1.0199 | 1.034 |
29: 
30: - A2：L = g / (K_in + k_ref) 的最大相对重构误差 3.69e-16；K_in / k_ref = 0.019–0.168；L·k_ref / g = 0.856–0.981；池内 τ(g, L) min／median = 0.889／0.944；池内 τ(g, F_n) min／median = 0.889／1.000；g、L、F_n(5) 三者最大为同一设计的池数 200／200。
31: - A3：全体设计的 Pearson r = 0.9992；HF／线性 = 0.440–0.965（中位 0.945）；池内 τ(线性, HF) min／median = 0.944／1.000；线性最优 = 已验证 HF 最优的池数 200；线性接触起点落在 HF 采样接触区间内 1730／1799（HF 更早 69，更晚 0）。
32: - A5（(10, 1) 对 (10, 3.16)）：平均差 0.0439 N；格内 SD 0.0105／0.0128 N；配对差的 SD 0.0092 N（不配对 0.0165 N）；跨池相关 F_n 0.705、L 0.385；池内相对裕度 1.53–5.96 %（中位 3.92 %）；次优格胜出的池 0；不配对跨池比较中次优格胜出的比例 0.59 %。
33: 
34: ## A6 LF 与 HF 次序不一致之处
35: 
36: | LF 分数版本 | 有反转的池 | 反转的格对（池数；HF 相对差 min／median／max） |
37: | --- | --- | --- |
38: | 恢复冻结口径版（C1） | 94 | (1, 1)–(10, 10)（90；0.01／0.57／2.61 %）；(1, 1)–(10, 3.16)（4；0.08／0.18／0.89 %） |
39: | 实际执行版 | 96 | (1, 1)–(10, 10)（92；0.01／0.57／2.61 %）；(1, 1)–(10, 3.16)（4；0.08／0.43／0.89 %） |
40: 
41: ## A7 去顶反事实（按 LF 分数去掉前 r 名后，在剩余成员上重做 95 % 近优命中，k = 3，无质量门）
42: 
43: | 去掉 | 每池剩余 | 首选未命中 | 其中首选标签未知 | S0 命中 | S2 命中 |
44: | --- | --- | --- | --- | --- | --- |
45: | 0 | 9 | 0 | 0 | 200 | 200 |
46: | 1 | 8 | 0 | 0 | 200 | 200 |
47: | 2 | 7 | 1 | 1 | 200 | 199 |
48: | 3 | 6 | 0 | 0 | 200 | 200 |
49: | 4 | 5 | 0 | 0 | 200 | 200 |
50: 
51: ## B1 已保存的其他响应量（η = 0.5，冻结的 LF 分数与选择器；探索性）
52: 
53: | 标签 | 首选未命中 | S0 k=1／2／3／5 | S1 | S2 | k = 3：都命中／仅 S2／仅 S0／都未 | C 内最优格 |
54: | --- | --- | --- | --- | --- | --- | --- |
55: | F_n(2.5 mm) | 0 | 1.000／1.000／1.000／1.000 | 1.000／1.000／1.000／1.000 | 1.000／1.000／1.000／1.000 | 200／0／0／0 | (10, 1) 200 |
56: | F_n(3 mm) | 0 | 1.000／1.000／1.000／1.000 | 1.000／1.000／1.000／1.000 | 1.000／1.000／1.000／1.000 | 200／0／0／0 | (10, 1) 200 |
57: | F_n(4 mm) | 0 | 1.000／1.000／1.000／1.000 | 1.000／1.000／1.000／1.000 | 1.000／1.000／1.000／1.000 | 200／0／0／0 | (10, 1) 200 |
58: | F_n(5 mm) | 0 | 1.000／1.000／1.000／1.000 | 1.000／1.000／1.000／1.000 | 1.000／1.000／1.000／1.000 | 200／0／0／0 | (10, 1) 200 |
59: | force ratio F_n(5 mm) / R_in(5 mm) | 200 | 0.000／0.000／0.000／0.000 | 0.000／0.166／0.332／0.665 | 0.000／0.985／0.985／0.995 | 0／197／0／3 | (0.1, 1) 200 |
60: 
61: ## B1／B2 限力限行程执行器的替代标签阶梯（从已保存的位移控制路径读出；不是对限力任务的 HF 评价）
62: 
63: | R* (N) | 标签类型：行程限（= 任务 A）／接触前为零／接触段内插／跨接触起点内插／未知 | 首选未命中 | S0／S1／S2 命中 k=3 | 都命中／仅 S2／仅 S0／都未 | 跨起点内插取下界／上界时的首选未命中 | C 内最优格 | 对照：匹配 LF 口径的首选未命中（k=1 命中率） |
64: | --- | --- | --- | --- | --- | --- | --- | --- |
65: | 0.25 | 243／1195／200／162／0 | 200 | 0.000／0.332／0.985 | 0／197／0／3 | 200／200 | (0.1, 1) 200 | 0（1.000） |
66: | 0.5 | 600／0／620／580／0 | 200 | 0.000／0.332／0.985 | 0／197／0／3 | 200／200 | (0.1, 1) 200 | 0（1.000） |
67: | 0.75 | 600／0／1173／27／0 | 200 | 0.105／0.629／0.995 | 21／178／0／1 | 200／200 | (1, 10) 145，(0.1, 1) 29，(1, 3.16) 25，(1, 1) 1 | 85（0.575） |
68: | 1 | 600／0／1200／0／0 | 200 | 0.010／0.543／0.990 | 2／196／0／2 | 200／200 | (1, 10) 189，(1, 3.16) 10，(1, 1) 1 | 0（1.000） |
69: | 1.5 | 739／0／1060／0／1 | 200 | 0.005／0.580／0.965 | 1／192／0／7 | 200／200 | (1, 10) 137，(1, 3.16) 63 | 0（1.000） |
70: | 2 | 1199／0／600／0／1 | 200 | 0.915／0.336／0.015 | 3／0／180／17 | 200／200 | (1, 1) 199，(1, 3.16) 1 | 1（0.995） |
71: | 2.5 | 1599／0／200／0／1 | 47 | 1.000／0.953／0.765 | 153／0／47／0 | 47／47 | (10, 3.16) 181，(10, 1) 13，(1, 1) 6 | 47（0.765） |
72: | 3 | 1799／0／0／0／1 | 0 | 1.000／1.000／1.000 | 200／0／0／0 | 0／0 | (10, 1) 200 | 0（1.000） |
73: 
74: ### 同一阶梯的全部预算与 η = 0 敏感性（命中率 k = 1／2／3／5）；最后一列为池内 τ(L, 标签) 的中位数（只作描述，不是选择收益的度量）
75: 
76: | R* (N) | η = 0.5：S0 | S1 | S2 | 对照：匹配口径 S0 | η = 0：首选未命中 | S0 | S1 | S2 | τ(L, 标签) 中位 |
77: | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
78: | 0.25 | 0.000／0.000／0.000／0.000 | 0.000／0.166／0.332／0.665 | 0.000／0.985／0.985／0.995 | 1.000／1.000／1.000／1.000 | 200 | 0.000／0.000／0.000／0.000 | 0.000／0.147／0.288／0.550 | 0.000／0.165／0.165／0.775 | -0.417 |
79: | 0.5 | 0.000／0.000／0.000／0.000 | 0.000／0.166／0.332／0.665 | 0.000／0.985／0.985／0.995 | 1.000／1.000／1.000／1.000 | 200 | 0.000／0.000／0.000／0.000 | 0.000／0.125／0.250／0.500 | 0.000／0.060／0.060／0.740 | -0.444 |
80: | 0.75 | 0.000／0.005／0.105／0.720 | 0.000／0.372／0.629／0.905 | 0.000／0.430／0.995／1.000 | 0.575／1.000／1.000／1.000 | 200 | 0.000／0.005／0.105／0.720 | 0.000／0.280／0.498／0.787 | 0.000／0.025／0.975／0.995 | +0.000 |
81: | 1 | 0.000／0.005／0.010／0.785 | 0.000／0.298／0.543／0.875 | 0.000／0.000／0.990／1.000 | 1.000／1.000／1.000／1.000 | 200 | 0.000／0.005／0.010／0.785 | 0.000／0.224／0.420／0.726 | 0.000／0.000／0.990／1.000 | +0.167 |
82: | 1.5 | 0.000／0.000／0.005／0.940 | 0.000／0.321／0.580／0.912 | 0.000／0.000／0.965／0.985 | 1.000／1.000／1.000／1.000 | 200 | 0.000／0.000／0.005／0.940 | 0.000／0.241／0.449／0.765 | 0.000／0.000／0.965／0.985 | +0.222 |
83: | 2 | 0.000／0.020／0.915／1.000 | 0.000／0.169／0.336／0.668 | 0.000／0.000／0.015／0.970 | 0.995／1.000／1.000／1.000 | 200 | 0.000／0.020／0.915／1.000 | 0.000／0.127／0.253／0.504 | 0.000／0.000／0.015／0.840 | +0.444 |
84: | 2.5 | 0.765／1.000／1.000／1.000 | 0.765／0.882／0.953／1.000 | 0.765／0.765／0.765／1.000 | 0.765／1.000／1.000／1.000 | 47 | 0.765／1.000／1.000／1.000 | 0.765／0.853／0.916／0.983 | 0.765／0.765／0.765／0.990 | +0.833 |
85: | 3 | 1.000／1.000／1.000／1.000 | 1.000／1.000／1.000／1.000 | 1.000／1.000／1.000／1.000 | 1.000／1.000／1.000／1.000 | 0 | 1.000／1.000／1.000／1.000 | 1.000／1.000／1.000／1.000 | 1.000／1.000／1.000／1.000 | +1.000 |
86: 
87: - 一致性检查：F_n(5 mm) 配实际执行版 LF 分数——首选未命中 0，k = 3 表 {'both': 200, 'only_S2': 0, 'only_S0': 0, 'neither': 0}（应与 P3 记录相同）。
88: - S0 前三名的弹簧格：(10, 1) > (10, 3.16) > (1, 1)（180 池）；(10, 1) > (10, 3.16) > (10, 10)（16 池）；(10, 1) > (1, 1) > (10, 3.16)（4 池）。
89: - S2 前三名的弹簧格（η = 0.5）：(10, 1) > (0.1, 1) > (1, 10)（185 池）；(10, 1) > (0.1, 1) > (1, 3.16)（8 池）；(10, 1) > (0.1, 1) > (1, 1)（4 池）；(10, 1) > (0.1, 3.16) > (1, 10)（3 池）。
90: - S2 前三名的弹簧格（η = 0，无质量门）：(10, 1) > (0.1, 10) > (1, 10)（88 池）；(10, 1) > (0.1, 3.16) > (1, 10)（88 池）；(10, 1) > (0.1, 1) > (1, 10)（12 池）；(10, 1) > (0.1, 3.16) > (1, 3.16)（5 池）。
91: - 输入反力非单调的路径：0。
92: - 考察过的全部量：F_n(2.5 mm)；F_n(3 mm)；F_n(4 mm)；F_n(5 mm)；force ratio F_n(5 mm) / R_in(5 mm)；force- and stroke-limited surrogate, R* = 0.25 N；force- and stroke-limited surrogate, R* = 0.5 N；force- and stroke-limited surrogate, R* = 0.75 N；force- and stroke-limited surrogate, R* = 1 N；force- and stroke-limited surrogate, R* = 1.5 N；force- and stroke-limited surrogate, R* = 2 N；force- and stroke-limited surrogate, R* = 2.5 N；force- and stroke-limited surrogate, R* = 3 N。
```
