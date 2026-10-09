# M-VIEW1：细网格保存态显示与原目标粗细对照

**准备态：待独立静审，未授权、未执行。** 本卡是新的保存态阶段，不续用已关闭的 M-CYCLE1 资源窗口；下文观察次数、图件及验收均为计划范围，当前没有新图或新观察结果。

整体目标是供外部研究层比较同设计的 HF/TMC 正向响应。M-CYCLE1 已唯一一次正常完成 24 个原目标、24 个接受态、无二分；实际 helper/outer 为 11461.5405791/11463.2176853 s，见[生产结果](../../../lf_data_preparation/native_interface_001/nested_cycle_001/RESULTS.md)。下一步显示这 24 个细网格保存态的实际结构、钳尖、工件作用及 J/Hu 场，再与已保存的粗网格观察逐原目标对照，供人工判断网格敏感性。

| 项目 | 本卡固定范围 |
|---|---|
| 细网格输入 | `lf_data_preparation/native_interface_001/nested_cycle_001/run_001/fixed_square`；13,440 单元、13,689 节点、27,378 DOF，fixed 1548/free 25830；24 个原目标接受态 |
| 物理定义 | 原 84×40 mm 下半域，固定方体 side 18 mm、center (71,40) mm；E=1 MPa、ν=0.3、gamma=alpha=1e−6、Lr=80 mm；原支持、端口与 0→1.2→0 mm 路径保持；native 指 HF 供给的派生网格 |
| 源与绑定 | [协议](protocol.json)冻结原 viewer、本卡、新包装源及全部实际输入身份；核对输入 SHA、24 行和实际 27,378 DOF；准备源不构成新科学证据 |
| 复用方式 | [新 worker](execute_nested_views.py)通过 `runpy` 恰好一次调用[冻结的原 viewer](../../native_api_workpiece_20261008/complete_001/saved_right_margin_views.py)，单一 `fixed_square` 细网格 case；新源仅含资源包装与对照，不复制原 219 行 viewer 或 HF 力学计算 |
| 细网格观察 | 原 viewer 计划逐态 geometry 24 次、nodal 24 次；由保存场绘图。新 F/T、构模、求解、HP、JIT、LF、CLI/API 调用均不在范围内 |
| 粗网格复用 | 只读旧 W-VIEW1 的 `run_001/view/fixed_square/states.csv`、`summary.json`、旧 view manifest 及原 h1 `result.json`；不再观察粗网格，不解码旧 NPZ |
| 原目标匹配 | 由两例 producer 记录取得 `is_original_target`，按 `original_target_index`、`leg` 和 d 核对全部 24 对；不以接受态数组位置代替分支身份 |
| 新输出 | 新 `run_001/view`：原细网格 3 PNG、24 帧 GIF、逐态 geometry/nodal/derived 与原 CSV/JSON；另加 `mesh_comparison.csv`、`mesh_comparison.json`、`mesh_response_comparison.png`、`phase_view.json` |
| 资源 | 一次连续 whole-helper 600 s、outer 660 s；采样 own/tree RSS 8 GiB；协作停止，无 OS 硬内存保证、无 force |
| 停止与验收 | 冻结身份、细网格尺寸、原 viewer 全态/几何/节点力门、GIF 24 帧、24 对匹配、输出身份及资源回执均须通过；首个错误或资源停止即关闭，保留实际部分输出；不重试、不修复重跑、不延长 |

新增 2×3 对照 PNG 展示输入反力 R、下半工件 signed Fy、加权输出位移 qout、钳尖到工件底部有限线段的无符号距离、自由介质积分点 min J，以及自由介质 max |Hu| 分量。CSV/JSON 保留 14 项量：R、qout、工件总/材料/Hu 三个 Fy 分量、两侧 2|Fy| 幅值、钳尖 x/y、到底/左/右有限线段的三项无符号距离、solid/medium min J 与 medium max |Hu|；每项保留粗细值及 fine−coarse 差值。

min J 面板使用对数 y 轴，以显示接近压缩状态的差异；要求保存值为正。全部数值保留原值，不裁剪、不归零。

原图继续使用实际变形 ×1、关于 y=40 的显示镜像及参考钳尖节点 (80,30) mm。红色节点弱式力指模型作用于工件的力；holding 反向，下半 signed 力、两侧 2|Fy| 幅值和 full net 分开。有限线段距离与 ray 是几何诊断；节点窗口间隙、生产全域极值、自由介质极值及图中色标统计各按原定义使用。

旧粗网格 W-VIEW1 的实际 19.7715 s 仅是粗网格显示成本。细网格区域 AABB 扫描的 broadphase 组合可增至 16 倍，且单元、箭头与动画数据增加，因此本卡另设 600/660 s 额度；这不是细网格成本实测或完成时间保证。

新图与对照仅提供生产保存态诊断，不授予 HP、压力、有效夹持、网格/域收敛或 HF5 资格。细网格原 response 的 reference/views 仍 `not_provided`，producer 的独立资格 flags 仍 false；原 `view.json` 保留，新比较由 `phase_view.json` 记录，不改写生产 response。

独立静审通过且本卡获明确授权后，在实际 clone 根使用 HF Python 执行以下唯一入口；**命令尚未执行**：

```text
<HF-python> -X utf8 -B functional_views/native_nested_cycle_20261009/complete_001/launch_view.py view --protocol functional_views/native_nested_cycle_20261009/complete_001/protocol.json
```

当前实际工作只有源码与文档准备。授权范围限于上述新保存态显示、旧观察复用及数值对照；本卡中的计划输出须以后续实际回执确认。
