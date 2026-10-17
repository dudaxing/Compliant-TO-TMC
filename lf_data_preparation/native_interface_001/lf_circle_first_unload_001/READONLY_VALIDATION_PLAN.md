# L-CUNLOAD1 只读验证计划

状态：仅静态计划，尚无本记录授予的实现、测试或真实卸载执行资格。基线由主代理报告为 `c786583`。

建议新阶段只做一个 `native_resume.py` 候选和有限小模型验证。现有 `ordered_cycle` 控制器已经支持非零保存锚点及下降；无需改 Newton/KKT、力、切线、Armijo、二分或 `saved_load_only_anchor`。使用既有 `extend_path=True` 和显式新 task，窄化允许成功 `load_only` 末点转 `ordered_cycle`：旧前缀完全保留，只追加一个有限、非负、严格下降目标；`input.target_mm` 保留旧峰值，除现有四说明字段和这次路径变化外其余物理完全一致。保留嵌套来源的完整 anchor/suffix/索引证明，并在既有 `explicit_task_extension` 中增加 task-transition 元数据。

建议 **8 个方法，6 次真实 tiny solve，加 2 条线性控制器路径**。如需第9个方法，仅拆分纯元数据正例，不增求解。

1. 一个真实集成方法复用同一来源，依次做 load parent `[0,P/2,P]`、既有 load append 到 `1.5P`、从该已延伸 child 首次下降到 `P`、再按既有 ordered-cycle append 下降到 `P/2`，共4次求解。`P=.0005 mm`，沿用16单元/50DOF、无工件夹具和 mechanical/chunk256/port_projection。首次卸载的全局原目标索引为3/4、子索引0/1；后续下降为4/5。真实二分额外接受态不得被删掉或冒作原目标。
2. 一个真实旧 ordered-cycle parent `[0,P,P/2]` 及同kind append到 `P/4`，共2次，验证没有新跨kind标记的旧路径仍兼容。
3. 五组纯元数据/API反例覆盖：前缀/物理/峰值篡改和非法单下降；失败/未完成/非末点/非原目标来源；嵌套anchor或索引证明损坏；缺显式extend/task或错误布尔；旧load-only及低层保存锚点模式限制。失效调用应在读取科学载荷/进入solver前拒绝。
4. 一个线性方法：cold anchor一次，再wrong-R warm下降一次，必须 `initial_state_not_equilibrated`、fresh anchor检查1次、无接受/修正/trial，返回状态/R原样。原控制器已有rollback/二分测试，保留其覆盖，不另开真实FE失败campaign。

每个真实保存子段检查首F/T为新调用且ordinal1、anchor `newton_checks=1`、lift/fluctuation字节及state SHA和signed R字节完全相同；仅载入原state，不读旧F/T/矩阵。检查原J/残差/平均位移约束门、继承设置和options、局部/全局索引、`resume_origin/unloading`、public response和缓存保存（16 force fields/3 tangent/原CSC、save F/T=0、保存时禁止重算）。旧父文件不变。子段/卸载终点完成可为true，full-original/full-extended/task-target仍false，HP/HF生产标志仍false。锚点包含旧峰不代表重新加载或新峰；不要增加误导的new-peak成功断言。

资源建议与主代理当前方案一致：共享tests120s、每tiny controller30s、普通标量图30s、helper180s、outer240s、采样1GiB。旧CEXT实际5次真实tiny加2条线性路径约6.55s，仅作成本依据。本次最多6真实求解仍应受共享120s窗口约束，不能把每次30s累加成可延长额度。获批冻结后才在唯一helper内安装一份候选，再fresh child测试，再从普通tiny标量记录画1张反力/残差PNG及封存。首错停止，保留实际安装及部分证据，无自动回滚或重试。图须清楚标16cells/50DOF/no workpiece，不模拟circle接触图。

**本阶段不包含真实1.40→1.35。** 小模型通过后再独立授权真实卡，可沿现controller1800/display600/helper2700/outer2760s/8GiB；S5加载耗时不能保证卸载收敛。固定工件下的actuator下降也不等于自由工件释放，更不授压力/有效夹持或新HP资格。旧CREF1仅1.15，不转授新状态。

本审仅阅读当前native/saved/split-cycle及CEXT相关源码，未实现、未导入HF、未执行测试/科学，未读取或哈希NPZ/CSV/媒体。详细方法和来源行号见同名JSON。

## 主代理收束后的精确8方法

| 方法 | 职责 | 真实FE/线性路径 |
| --- | --- | --- |
| 01 | 同一来源链：原load、原load append、新首次卸载、原cycle再下降；嵌套证明/fresh anchor/响应/缓存保存 | 4 / 0 |
| 02 | 独立旧ordered-cycle parent和旧同kind append，保原行为 | 2 / 0 |
| 03 | task反例：前缀、材料、input峰值、追加多个目标、非下降、负/非有限端点 | 0 / 0 |
| 04 | source反例：failed、incomplete、非末接受态、非原目标接受态 | 0 / 0 |
| 05 | 嵌套证明反例：anchor flags、首state/R、suffix或局部/全局索引不符 | 0 / 0 |
| 06 | public入口反例：未显式extend、缺新task、非bool、zero-start；不能进入solver | 0 / 0 |
| 07 | 旧边界反例：same-kind load下降仍拒绝；saved-load flag对cycle或非bool仍拒绝，不能调用assembler | 0 / 0 |
| 08 | 线性cold anchor + wrong-R warm下降拒绝；fresh检查1次、无修正/接受/trial、状态/R保留 | 0 / 2 |

不增加第9方法，不另跑rollback。各组字面反例最终实现时应静态列清实际数量，不能以方法数隐藏额外真实调用。最小成功门为8方法无fail/error/skip、6真实与2线性计数分开记录；所有真实路径成功且原目标/额外接受态完整，原J/残差/约束及缓存身份门通过；新跨kind来自嵌套load child并可接旧cycle继续下降；fresh anchor与索引/flags精确；父来源保持、save F/T与HP/JIT为0。

唯一标量PNG仅使用**本窗新tiny普通JSON**，反力/残差双面板；不得读取NPZ展示或重绘旧circle。资源和候选先安装的顺序保持tests120/shared plot30/helper180/outer240/采样1GiB。计划至此收束，未执行。
