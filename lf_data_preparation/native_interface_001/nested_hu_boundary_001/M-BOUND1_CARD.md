# M-BOUND1：原保存 Q1 Hu 顶点作用与工件边／角点解释

2026-10-11。源码准备卡；当前 **prepared，未授权、未执行**。前次 M-VOLUME1 已唯一 PASS 闭卡并发布／独立恢复于 main `0d83b18b2bb320f137b1c4c3295805dc7c15aa65`。本卡不续用旧资源窗口。

## 目标、已有功能与本次增量

整体目标是独立 HF 有限变形／TMC 前向评估：从普通 LF 几何得到结构实际变形、反力与有明确物理含义的工件作用。main 是后续开发主干；origin 保持 `https://github.com/dudaxing/Compliant-TO-TMC.git`。HF 与 LF 优化断开。

固定工件的 total/material/Hu 总作用、保持反力、镜像与实际节点力图已经实现；24 保存态／48 HP 独立参考已经覆盖材料与 Hu 工件力投影。M-VOLUME1 已对四个局部保存 case 解释材料体积弱力与旧上缘迹的差别。本卡不重新实现这些摘要、参考或整幅力箭头。

本次增加公共入口 `hf_eval.saved_q1_hu_boundary.observe_saved_q1_hu_boundary`，把原 Hu 单元弱力与原工件拓扑关联，展示 Q1 四顶点的有符号作用、侧边成对顶点的平移相消、两枚角点 owner 对总作用的贡献，以及 owner 分组和原节点分组的差别。实际变形继续链接原图；新增图只显示参考单元与有符号 N 值。

## 原弱式及解释合同

原论文 P26 PDF 第4页式(6)与原实现相符：Hu 虚功项含 `kr exp(-5J) Hu:Hδu`；该系数没有写入所述能量密度，切线一般非对称。不能用替代能量 `.5 c_e ||Hu||²` 的导数作为原完整力。详见 [物理推导](author/physical_basis.json) 和 [原论文公式核查](author/paper_formula_check.json)。

矩形 Q1 节点顺序 BL、BR、TR、TL；Hessian 的 xy/yx 符号为 `[+1,-1,+1,-1]/(hx hy)`。每个单元的原内部 Hu 四顶点力为 `[+β,-β,+β,-β]`，其中 `β_i = kr sum_q(w_q exp(-5J_q)) (Hu_i,xy+Hu_i,yx)/(hx hy)`。作用于工件的符号是原内部力的负号。

全选四顶点或相邻两个顶点，对共同平移的合力在实数代数中为零；单独选中一个角点可保留作用。侧边 owner 成对合力为零不代表组装后边界节点力为零。保存 Q1 顶点共轭作用不能唯一分配为连续面压力；不得把它补成 `P@N` 的一个标量压力。

本卡直接使用原 `element_regularization_force` 八值，不重建 Hu、J、系数、应力、超应力、能量梯度、面通量或力矩，也不改变原力核和切线。跨角色求和、两角点与原整体差只作描述，不增设相等门或物理资格。

## 冻结输入范围

只处理原 loading 保存态6／0.85 mm和13／1.20 mm。保留原 task、state identity 与 SHA；域84×40 mm、h0.5 mm、13440单元，固定下半正方形工件中心(71,40) mm、边长18 mm、厚度20 mm。原物理参数与24态路径保持。

运行仅读取9份原文件：4 JSON（model、result、两 state）；3 CSV（M-SUPPORT1 cells、M-LEDGER2 all_nodes 与 category_loads）；2个原 forces NPZ。每 NPZ 只解码 `element_regularization_force`，合计2字段、2次新公共入口。文件字节 SHA、原 descriptor 与字段 dtype／shape／C字节 SHA 均绑定。详见 [最终输入核查](author/final_input_scope.json)。

每态观察722个原 support 单元：body648、bottom_owner36、left_owner18、right_owner18、corner_only2；工件703节点、2738局部出现，最多4项／节点。单元从小到大、local从小到大、x/y依原 C 顺序；只做工件1406 DOF compact `bincount`，不做全域重组。

端点显示固定为10371、10407、10408，每态12个顶点。10371只选TR、10408只选TL；10407为bottom_owner选TR/TL，不能误记为角点。坐标按原网格与 node ID 得到参考坐标，并与原节点坐标精确核对。没有新的位移数组读取或实际变形重构。

准备时已发现并修正包装字段假设：`region_metadata.workpiece.fixed_dofs` 是计数1406，真实 DOF 列表位于 `region_metadata.fixed_dofs`。公共入口显式接收该原全局列表并核 body dofs 子集；这是运行前源码修订，未发生试跑或修复重跑。

## 原门与新增代数门

1. 原 model/result/state identity、固定工件完整 DOF 与原连接／选择／角色／数量精确核对；逐单元原八值有限且数值精确满足 Q1 `[+,-,+,-]` 模式。
2. 工件 compact scatter 保原内部力加法次序，最后取负；703节点／态与原 M2 Hu 节点值 `np.array_equal`。这是数值精确门，不是字节或 signed-zero 门。
3. 原节点 total/material/Hu 六力字符串、原七类表复制保留。原节点到原 state 整体 Hu 对比继续使用 `8eps × 原节点Hu L1`、无地板，独立于新增门。
4. 新局部 regroup 与原节点逐节点对账，以及局部整体与原节点整体对账，使用 `8eps × 对应原选中local Hu L1`、无地板。不混用旧 nodal L1 作为新 local 重组界限。
5. 五 owner 组重组差、两 corner_only 与原整体差只报告；不把它们或材料／总力的复制值变成新压力、能量或夹持验收。
6. exact输入绑定在运行前后核对；calls、行数、输出文件集合精确核对。原 M1/M2/SUPPORT/TRACE/VOLUME/HP 验收门及资格保持。

## 输出及可视化

| 输出 | 冻结数量／内容 |
| --- | --- |
| hu_boundary.json | 两态公共入口观察、原七类数据、原实际变形链接、解释限制 |
| cells.csv | 1444单元行，保留八个原Hu分量和选中顶点作用 |
| groups.csv / whole.csv | 10 owner组行／2整体行，误差与对应L1界限 |
| nodes.csv | 1406节点行，原六力文本与新local重组对账 |
| selected_endpoints.csv | 24顶点行，参考坐标、内力／负局部covector、工件选择标记 |
| node_categories.csv | 14行原七类完整文本，仅读取复制，不重新分组或求和 |
| Q1_Hu_endpoint_actions.png | 两态×三单元，红色为选中ON-body，其它顶点为负局部covector；各面板独立箭头比例，标注N值及参考坐标 |
| Hu_owner_node_comparison.png | 两态×Fx/Fy，五owner、两角点与原整体比较、原七节点类；分组间隔与独立面板尺度，不能跨partition相加 |
| execution_receipt.json | 实际次数、时间、采样RSS、输出SHA；成功receipt记录前采样，不声明硬内存限或机械hook监测 |

共10文件（含receipt）、2 PNG。原实际变形：[24帧GIF](../../../functional_views/native_nested_cycle_20261009/complete_001/run_001/view/fixed_square/actual_states.gif)。只有获得本卡授权并产生实际结果后，才能查看并解释新PNG；静审不冒充数值通过。

## 一次执行、资源与异常规则

一次启动：helper180秒、outer240秒／采样8GiB（8589934592 B）。复用 M-VOLUME1 通用launcher原字节为 `launch_boundary.py`，phase=`hu_boundary`；无OS硬内存cap、无force termination。首错停止，无重试、修复重跑、延期或force；若异常，本窗口关闭，保留终端与receipt后再评估新卡。

预期calls：NPZ started/completed各2、selected fields2、hu_boundary started/completed各2、PNG writes2。不新增力核、切线、HP或平衡求解，不调用旧账本入口。包初始化与库导入不构成新的机械入口调用。

批准后在正式仓库根用独立HF环境一次执行：

```text
python -X utf8 -B lf_data_preparation/native_interface_001/nested_hu_boundary_001/launch_boundary.py hu_boundary --protocol lf_data_preparation/native_interface_001/nested_hu_boundary_001/protocol.json
```

## 阶段结束与下一步判断

实际结束后核 receipt／终端、绑定、原节点对账、全部行数与两张图，保存目标—实现—原因—效果说明及独立审阅，再提交main并推送、独立恢复核对。若通过，只取得两态保存Q1 Hu离散边／角点解释，不升级到总压力、有效夹持或网格收敛。

根据实际 corner、side、node 作用再选择下一项物理功能或稳定性验证；不预先扩展全24态、重新平衡求解或增加HP。自由工件、摩擦、物理参数／网格稳定性和正式HF5标签排名仍未完成。
