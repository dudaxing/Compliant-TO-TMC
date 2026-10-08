# W-API1：固定方体经真实 CLI/API 的独立 HF 正向结果

**成功闭卡：唯一一次真实执行完成，24 个原目标及 24 个接受态全部保存。原窗口已消耗，不再用于重跑。**

整体目标是让 LF 普通几何及明确的物理任务进入独立 HF 有限变形/TMC 正向评估，取得真实响应、原失败原因和可检查输出。HF 保持正向评估职责。本卡选择已有固定方体大行程任务，把现有入口的真实执行链闭合：`CLI.main → evaluate_native_batch → evaluate_native → 原 solve_native_mean → write_native_mean → summarize_saved_native_result`。此前旧 worker 直接调用原求解/保存，保存 JSON formatter 与窄 mock 只能证明读取和参数传递；本次从零初值重新调用整条链，验证真实构模、求解、缓存保存和摘要是否完成。

用户于 **2026-10-08 明确批准“按 W-API1 卡执行”**。来源、输入与 worker 已按卡冻结为 36 份 bindings，含 28 份原 HF 源；唯一一次冻结 F3/worker 执行沿用原物理定义与控制器。依据：[W-API1 卡](../workpiece_api_preparation_001/W-API1_CARD.md)、[单例配置](../../../hf_repo/configs/native/fixed_square_cycle.json)、[生产协议](production_protocol.json)。旧物理结果及旧图仅见[此前实例准备结果](../workpiece_api_preparation_001/RESULTS.md)；本报告不把旧 48 HP 或旧图资格转移给新 producer。

原任务为 native h1、84×40 mm、3360 单元/6970 DOF，平面应变；固定方体中心 (71,40) mm、边长 18 mm、右表面 x=80 mm、右侧第三介质 4 mm。E=1 MPa、ν=.3、厚度 20 mm、γ=α=1e-6、Lr=80 mm；原端口和支撑，输入采用平均位移，输出弹簧为零。模式保持 `mechanical / chunk256 / port_projection`。

原 24 个 targets（mm）按实际加载/卸载顺序保存：

`0, .25, .5, .65, .75, .8, .85, .9, .95, 1, 1.05, 1.1, 1.15, 1.2, 1.15, 1.1, 1, .9, .8, .75, .65, .5, .25, 0`。

全部原 DisplacementSettings 保持：`tolerance=1e-9`、`constraint_tolerance=1e-10`、`displacement_scale_floor=1e-6`、`force_scale_floor_factor=1e-8`、`max_checks=25`、`armijo_c=1e-4`、`max_backtracks=12`、`max_bisections=4`、`minimum_increment=.00625 mm`、`time_limit_seconds=4500`。原卡窗口为 whole-helper 4500 s、outer 4560 s、采样 own/tree RSS 8 GiB；RSS 为采样约束。允许原控制器 trial 拒绝、回滚及二分，实际接受态 N 不预设为 24。首个 terminal non-success、来源变化、异常或资源停止即关闭，无修复重跑、延长或 force。

本次源提交为 `b1f01ac18d72a7093e7c822dbaba3daae3b7f8ec`。实际授权见 [授权记录](authorization_001.json)；冻结卡中的“待授权/未执行”文字是准备时历史，不改写原卡。

[F3回执](production_launch.json) 与 [worker回执](run_001/execution_receipt.json) 均为 pass，退出码 0，无 stop_reason 或 terminal exception。[batch index](run_001/batch/index.json) 为唯一 fixed_square success；[response](run_001/fixed_square/response.json) 关联 [result](run_001/fixed_square/result.json)，result 再关联原保存 model。[独立窄核](author/terminal_readback_review_001.json) 对 JSON、文件身份、原门记录和调用实数 PASS；不是新的独立力学/HP计算。

| 实际执行 | 结果 |
|---|---|
| CLI / batch / API / model / solve / save / summary | 各一次；CLI exit 0；所有 delegate 1/1 |
| F 启动 / 完成 | 340 / 325 |
| T 启动 / 完成 | 174 / 174 |
| 保存 / 摘要新增 F/T | 均 0 |
| 新 HP / JIT / LF / 几何节点观察 / 渲染 | 均 0 |
| 原 targets / settings / mechanical-chunk256-port_projection | 全部保持原值 |
| path_completed / loading_peak_reached / unload_endpoint_reached / task_target_executed | 全部 true |
| 接受态 / 原目标 / 额外二分接受态 | 24 / 24 / 0 |
| whole-helper / outer 秒数 | 2170.0202062 / 2171.3780382 |
| own peak / tree peak RSS bytes | 581165056 / 578031616 |
| 36 冻结 bindings | 末核全部不变，含 28 原 HF 源 |

完整原 trial 记录留在 result.path_diagnostics：166 个 trial，16 个 rejected。F 启动数和完成数分别保留原实数，不将未完成调用抹掉，也不要求两者相等。原控制器允许的 trial 拒绝与回退没有变为新的整次求解；本卡只有一次真实路径，无终止失败后的重试。

| 缓存生产门 | 全接受态实际值 |
|---|---:|
| minimum J > 0 | 3.2722992545782586e-05 |
| maximum relative residual ≤ 1e-9 | 9.3345149056299271e-10 |
| maximum absolute constraint residual mm | 5.5511151231257827e-17，原 scaled constraint_bound 全部通过 |
| maximum relative global force balance ≤ 1e-6 | 9.6264088935657563e-11 |
| maximum fixed split-sum mm ≤ 8e-11 | 0 |

下表直接读取新 response 的加载目标与请求终点；回零不是 1.2 mm 任务响应。

| 新实际响应 | 1.2 mm 加载峰（index 13） | 0 mm 卸载终点（index 23） |
|---|---:|---:|
| 输入 R [N] | 0.40725277148913858 | 1.2083582019558206e-24 |
| q_in / q_out [mm] | [1.2,1.008846132373483] | [0.0,-6.2153656524766926e-24] |
| 下半体 total signed (Fx,Fy) [N] | [-0.0024081238889866684,0.11936195151183741] | [5.589409350514336e-25,-5.149182846763533e-24] |
| 材料项 signed Fy [N] | 0.11785138159936352 | -8.5151177880218731e-27 |
| 正则项 signed Fy [N] | 0.0015105699124738784 | -5.1406677289755109e-24 |
| 两侧法向幅值和 2\|Fy\| [N] | 0.23872390302367483 | 1.0298365693527066e-23 |
| full mirrored net (2Fx,0) [N] | [-0.004816247777973337,0.0] | [1.1178818701028673e-24,0.0] |
| 全域 minimum J | 3.2722992545782586e-05 | 1 |
| 全域 maximum \|Hu\| [1/mm] | 0.2088465633790193 | 7.3178374658836231e-21 |
| relative residual | 1.0459402174471055e-12 | 9.3345149056299271e-10 |
| relative global force balance | 2.1338893243130401e-13 | 9.6264088935657563e-11 |
| node-window bottom / left [mm] | {"bottom":0.005730316194075158,"left":2.3287460107852738} | {"bottom":1.0,"left":2.0} |

工件力是模型/介质对固定下半体的 signed 弱式合力；holding reaction 在模型上的方向相反。两侧法向幅值和与 full net 分开，不能将相互抵消的上下 Fy 当作没有夹持作用，也不能把幅值和称为完整净合力。q_out 是加权端口位移，node-window 是原栅格窗口诊断；本卡没有新连续面距、压力或场观察。全域 J/Hu 不改称独立实体/介质场资格。

本阶段的实际效果是：普通单例配置经现有真实 CLI/batch/API 完成原构模、完整大行程平衡路径、缓存保存和摘要，并将加载峰与卸载终点、工件材料/正则分量力直接暴露给使用者。此前保存 JSON 或 mock 能证明的读取/传参范围，现在增加了真实工件执行链的证据。力学源码未改，剩余预算不续用。

新 producer_flags 全部 false，independent_reference 与 views 均 not_provided。旧 48 HP 和旧图仍属于旧 producer；此次缓存门通过不授予新独参、接触/压力/有效夹持、全切线列、网格/域收敛、自由体/摩擦或 HF5 整体资格。原生产 JSON 与 frozen 输入不在后续读取或绘图中改写。

下一步优先让人工看到新 API 数据的真实 x1 结构、工件合力与输入反力、加载/卸载及 J/Hu 保存场。现有 saved_right_margin_views.py 读取普通 result/model/split/forces，与新数据兼容；可复用其源，使用新 producer 的独立输入绑定。本卡不含新观察/渲染；后续阶段须另行明确范围和资源，不重开本卡，不借旧 reference/view 资格。

[W-VIEW1具体执行卡](../../../functional_views/native_api_workpiece_20261008/complete_001/W-VIEW1_CARD.md)已完成原字节源复用、173项新绑定和独立静审，待明确授权。其run_001与view_launch.json均不存在，准备不属于已生成新图。
