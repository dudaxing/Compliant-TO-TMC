# M-BOUND1 候选源码说明

这是源码准备记录。两个候选仅做 AST 解析及普通来源核查，没有导入或运行候选，没有解码 NPZ、调用 API、计算新的力／fsum／投影或绘图；正式仓库未改。

新增功能是保存 Q1 Hu 端点／角点广义作用的所有者解释。已存在的 total/material/Hu 工件摘要、24态独立 HP、全节点账本和实际变形三分量 GIF 继续复用。本候选不会将局部力变为连续压力或新夹持资格。

公共入口为 `observe_saved_q1_hu_boundary`，输入是一个原 `element_regularization_force` 普通数组、M-SUPPORT1 的原722条单元拓扑、M-LEDGER2 原703条节点字符串，以及原模型／状态普通元数据。原模型 NPZ、global Hu、Hu/J、P、位移和切线均不读取。worker 每态只解码一个力 NPZ 的一个字段，共两 NPZ／两字段；原7节点类别仅复制 `category_loads.csv` 的14条原行，不重算分类或六力和，不读大型 `ledger.json`。

预执行普通 JSON 核查确认 `region_metadata.workpiece.fixed_dofs` 是计数1406；完整约束 DOF 列表是 `region_metadata.fixed_dofs`。入口用明确的 `global_fixed_dofs` 参数核对 body DOF 子集，并单独核对原 body fixed_dofs 计数，调用器传原全局列表。本修正在任何候选运行之前完成，未更改科学范围或验收公式。

每态只核722个支撑单元的原8分量 `+−+−` 模式，BL原内部向量作为核对幅值。`np.array_equal` 是数值结构门，不是字节或 signed-zero 门。原八分量仍是权威值，不用重算 Hu／指数系数得到替代力。

原选择的 body 局部出现按 cell/local/component 原 C 序填入1406个工件自由度的紧凑 `np.bincount`，先重放正内部力再取负，要求与每个原节点 Hu 数值精确相等。这里不重放全域组装。局部 fsum 与节点值／整体节点和的重组使用8eps乘原被选局部 Hu L1，无绝对地板；原节点 fsum 与原状态 whole 的原节点 L1 门独立保留。五 owner 角色、两个 corner_only 及原 whole 的跨投影差仅描述，不引入 total=material+Hu 或新的压力、能量／力核资格门。

两 PNG 分别显示两态各三单元的四端点负局部协向量，以及五 owner 角色与原7节点类别的不同分组。只有选中 body 点可标 ON-body；其它顶点只是局部协向量。前五组是一个支撑分解，两个角点和原 whole 是比较量，后七组是另一个原节点类别分解，不能跨组相加。图为参考网格；已有实际变形图按 protocol 关联，不重新生成。新四角参考坐标由原 grid/node 索引得出，并精确核对所有 body 节点的原 M2 坐标。

拟 protocol schema 为 `saved-Q1-Hu-boundary-card-1.0`，phase 为 `hu_boundary`；selected states 为6／loading0.85mm、13／loading1.2mm，selected endpoint cells 为10371／10407／10408。每态 body648、bottom36、left18、right18、corner_only2，共722单元／2738局部出现／703节点；原厚度20mm已经包含在原 N 力值中，不再乘厚度。

| 调用器合同 | 预期总数 |
| --- | ---: |
| NPZ_read_started／completed | 各2 |
| selected_array_fields | 2 |
| hu_boundary_started／completed | 各2 |
| PNG_writes | 2 |
| cells_total | 1444 |
| group_rows_total | 10 |
| whole_rows_total | 2 |
| nodes_total | 1406 |
| selected_endpoint_rows_total | 24 |
| node_category_rows_total | 14 |

预期十文件为 `hu_boundary.json`、`cells.csv`、`groups.csv`、`whole.csv`、`nodes.csv`、`selected_endpoints.csv`、`node_categories.csv`、`Q1_Hu_endpoint_actions.png`、`Hu_owner_node_comparison.png`、`execution_receipt.json`。worker 在 receipt 之前核对前九个名字与 protocol 完全相同。

worker 继续原包装的 checkpoint／selected field SHA／one-pass／末绑定复核／新目录合同。拟 helper180秒、outer240秒、采样 RSS8GiB；一次启动、首错停止，无修复重跑、force或延期。本记录没有开启资源窗口，仍待具体卡、独立审阅、发布／恢复核对与所需授权。
