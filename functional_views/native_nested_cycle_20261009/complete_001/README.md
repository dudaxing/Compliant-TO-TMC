# M-VIEW1具体源码已静审：待本卡批准，尚未执行

2026-10-09。[独立最终静审](author/final_view_static_review.json)通过；96实际绑定、600/660秒与8 GiB合同、24态细观察和粗网格既有派生值匹配入口一致。静审没有执行观察/渲染、NPZ解码或HF。冻结[原卡](M-VIEW1_CARD.md)及[协议](protocol.json)保留准备态身份；只有本卡明确批准后执行一次，M-CYCLE1已关闭不续用。

<details>
<summary>源码准备时的说明（历史原文）</summary>

# M-VIEW1：准备态，待独立静审，未授权、未执行

[M-VIEW1 卡](M-VIEW1_CARD.md)与[协议](protocol.json)准备一次新的细网格保存态阶段。[M-CYCLE1](../../../lf_data_preparation/native_interface_001/nested_cycle_001/RESULTS.md)已正常完成 24 个原目标、24 个接受态、无二分；本阶段把同设计派生 h0.5 的实际结构、钳尖、工件作用及 J/Hu 场显示出来，供人工检查并与 h1 比较。

[新 worker](execute_nested_views.py)只包装资源控制和粗细对照，通过 `runpy` 恰好一次复用[原冻结 viewer](../../native_api_workpiece_20261008/complete_001/saved_right_margin_views.py)，仅观察 27,378 DOF 的细网格 `fixed_square` 保存态。旧粗网格 `states.csv`、`summary.json`、view manifest 和原 h1 result JSON 用于匹配 24 个原目标，不新增粗网格观察或旧 NPZ 解码。匹配核对 producer 的 `is_original_target`、原目标索引、分支与位移。

计划输出位于新 `run_001/view`：原细网格 3 PNG、24 帧 GIF 与逐态观察文件，另加 `mesh_comparison.csv`、`mesh_comparison.json`、六量 2×3 图 `mesh_response_comparison.png` 和 `phase_view.json`。数值表含力分量、钳尖坐标及底/左/右有限线段距离、solid/medium min J 和自由介质 max |Hu|。原 viewer 与 HF 力学计算未复制到新包装源。

对照图 min J 使用对数 y 轴，数据保持原值；不裁剪或归零。

本卡额度为 helper 600 s、outer 660 s、采样 RSS 8 GiB；首错即停，不重试、不延长、不 force。旧粗网格 19.7715 s 不能作为细网格成本实测；较多区域扫描、单元、箭头和动画数据是新增额度的依据，不保证完成时间。

当前只有源码/协议准备，没有新观察、渲染或执行结果。计划图件仅属生产保存态诊断，不升级 HP、压力、有效夹持或网格/域收敛资格；原细网格 response 的 reference/views 仍 `not_provided`、独立资格 flags 仍 false。具体冻结身份、验收门、命令和输出范围见本卡及协议；本阶段另行授权，不续用已关闭的生产窗口。


</details>
