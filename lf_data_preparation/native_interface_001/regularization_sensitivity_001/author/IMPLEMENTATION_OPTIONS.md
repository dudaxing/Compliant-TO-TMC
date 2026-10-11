# M-ALPHA1 最小实现取舍（仅源码准备）

本阶段服务于独立 HF 评估器的总目标：把已验证的非线性 TMC 力学实现，推进为能可靠分析夹持器、报告有符号载荷和实际变形，并说明适用范围的功能。当前固定方形工件已有完整细网格加载／卸载、三分量材料／Hu／总力观察、实际变形 GIF，以及原 24 保存态／48 HP 参考。M-VOLUME1 已解释选定单元的材料弱力与旧上缘牵引差别，M-BOUND1 已补足 Q1 Hu 的所有者／角点／节点离散解释；这些数值正确性证据不能替代参数与网格的物理稳定性。

建议下一最小功能为**同一 h=0.5 mm 任务的 α 单因素两值敏感性比较**。α 从 1e-6 改为 5e-7，保留 γ=1e-6、Lr=80 mm、E=1 MPa、ν=0.3、厚度 20 mm、84×40 mm 域、原结构／端口／边界／固定方形工件。α 改变 Hu 正则系数；它不改变结构材料弹性模量，也不保证新平衡态的 Hu 载荷简单减半。这里先观察其对反力、材料／Hu／总响应、尖端有限面距离与局部变形指标的影响。

## 为什么采用 15 个有序目标

原任务前 15 个目标为 `[0, 0.25, 0.5, 0.65, 0.75, 0.8, 0.85, 0.9, 0.95, 1.0, 1.05, 1.1, 1.15, 1.2, 1.15]` mm。候选从原始零状态重新开始，加载到 1.20 mm 后只回撤一次到 1.15 mm。它明确是**部分卸载**，不宣称返回零位移或完成原 24 目标全循环。

原 task validator 允许 `ordered_cycle` 在低于峰值处结束；原 controller 为这些状态保存 `leg` 与 `original_target_index`，原 viewer 可以直接读取。纯 14 个 `load_only` 目标虽然已有求解支持，但当前 viewer 直接读取上述两个身份字段，需额外适配。保留 15 个有序目标即可省去该适配，还能展示一段局部回撤。缩短路径是明确的比较范围；两条曲线只匹配原基准相同的 15 个目标，不混用剩余卸载状态。原 bisection 仍可产生额外接受态，它们全部保存并显示，比较表只精确匹配原目标。

原 `native_batch` 只允许同一个物理任务在一个批次中运行；因此候选批次只包含 `alpha_half` 一个新案例，基准直接取已有 JSON／CSV，不再求解基准、不将不同 α 塞进同一个批次。

## 最小源码与接口

- [execute_alpha_cycle.py](<D:/hf-native-workpiece-api-author-20261009/MSTAB1_preparation_001/execute_alpha_cycle.py>)：薄生产包装；单次直接 `evaluate_native_batch`，保留原 force／tangent 调用统计、接受态 callback、原缓存 writer 和原四项生产门。原 Armijo、失败 trial 回滚、general LU、backtrack／bisection 均由原 controller 处理。终端首错停止，不重启批次，不将正常可恢复 trial error 改写成终端错误，也不要求 force started/completed 相等。
- [compare_alpha_views.py](<D:/hf-native-workpiece-api-author-20261009/MSTAB1_preparation_001/compare_alpha_views.py>)：在全新的 Python child 中调用原保存态 viewer，然后与原基准普通 JSON／CSV 匹配 15 个目标，输出比较表和新比较图。新 child 避免 solver 进程已加载模块破坏原 viewer 的 pure imported-set 合同。
- 原 [native_project.py](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/hf_repo/src/hf_eval/native_project.py>)、[native_mean.py](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/hf_repo/src/hf_eval/native_mean.py>)、[native_batch.py](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/hf_repo/src/hf_eval/native_batch.py>) 与 [saved_right_margin_views.py](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/functional_views/native_api_workpiece_20261008/complete_001/saved_right_margin_views.py>) 均拟复用原字节，不新增核心有限元实现。

候选正式 stage 拟为 `lf_data_preparation/native_interface_001/regularization_sensitivity_001`。`manifest.json` 一个案例 label=`alpha_half`，案例输出 `run_001/alpha_half`，批次输出 `run_001/batch`，新图输出 `run_001/view`。protocol 使用 `manifest_file`、`candidate_directory`、`view_directory`、`viewer_source`、`baseline_result`、`baseline_summary`、`baseline_csv`、`targets_mm`、`bindings`、`sampled_RSS_bytes`、`view_seconds`、`phases.production` 和原四个 `gates`。执行前还要求归档的 `author/authorization.json` 绑定真实 `author/direct_human_reply.json` SHA、当前源码提交、卡名 `M-ALPHA1` 与实际 protocol SHA。两份记录用 `authorization_from_direct_human_reply=true` 明确来源，`direct_human_answer` 保留完全相同的回复原文；证据还包含非空 `reply_context` 和匹配的 `approved_source_commit`，不限制“批准”的固定字面写法。准备阶段 protocol 的 `authorized=false/executed=false` 不作改写。本文与脚本不是数值执行授权。

未来 `checked_model` 在首次 force 前核对实际 constructor 返回的 `project.material`：仅 alpha 与 kr 允许改变，实际 `project.model.kr` 必须对应基准 kr 的半值，其余材料元数据、hx／hy／厚度／输出弹簧保持。`region_metadata` 的边界、固定 DOF 与端口等保持基准普通 model.json 原值；仅 `effective_boundary.task_sha256` 随新任务合法变化，并与实际新 task SHA 一致。原几何与源码已有字节绑定，不增加十余数组 hash 门，不读取基准 NPZ，也不要求新旧 model.npz 相同。

## 原证据与候选成本

原 [accepted_progress.jsonl](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/lf_data_preparation/native_interface_001/nested_cycle_001/run_001/accepted_progress.jsonl>) 的累计 helper 快照：原点 81.40964069997426 s，加载 0.85 mm 2030.5818528999807 s，峰值 1.20 mm 5721.272085799952 s，第一次卸载 1.15 mm 6150.8550677 s，返回 0 mm 11429.610730099957 s。这些是原基准的已保存耗时，不是新 α 的速度预测。原完整 24 态 helper 为 11461.540579099907 s，采样峰值 RSS 1891209216 B；原 24 态保存显示 helper 为 39.6988670 s。

root 提出的候选预算是 controller 9000 s、整个 helper 9600 s、outer 9660 s、采样 8 GiB，尚待源码、物理与卡审阅和直接授权。viewer 自身上限 600 s，实际 child 获得 `min(600, helper 剩余时间)`，包含在 9600 s 内。原 cooperative launcher 对 helper 与全部子进程采样树 RSS，并通过原 stopfile 协作停止；不新增 timeout／force 或清理框架。原基准前缀记录支持把它列为可审阅候选，但 α 变化可能产生更多 backtrack／bisection，不能保证在预算内完成。

## 预期保存与人工检查

未来实际成功时，新批次调用／API／模型／求解／保存／摘要各一次，不新增 HP 或 JIT，保存原 15 个目标及全部额外接受态。原四项门保持：相对生产残差 1e-9、原平均输入约束 bound（设置 1e-10）、全局力平衡 1e-6、固定 DOF 的 lift＋fluctuation 8e-11 mm；原有效 J 要求也保持。

原 viewer 输出实际变形三分量力箭头 GIF，以及 3 张既有 PNG；比较 child 增加 1 张 α 响应对照 PNG，共 4 张。三分量有符号 Fx／Fy、保持反力及镜像解释仍在原保存响应／raw 表中；新比较表使用现有 14 个指标，不重建投影。比较关注反力、输出位移、总／材料／Hu 的 Fy、缓存两侧法向幅值、尖端坐标与对三个有限面的无符号距离、solid／free-medium minJ、free-medium 最大绝对 Hu 分量。无符号几何距离不会改称有符号穿透量。

数值核正确性和敏感性结论分开记录。两值 α 比较只能发现本任务的响应变化，不能授予网格／参数收敛、有效压力、合格夹持力、HF5 或新保存态独立参考资格。原 48 HP 继续属于原基准状态，不转授新候选。结果产生后先审实际曲线和变形，再决定是否需要另一个最小因素；当前不安排第三网格或同时改变 γ，也不重做原 24 态账本／48 HP。

当前状态：已静读现有源码与普通保存记录，并写外部候选；尚未导入候选、创建模型、读取 NPZ、运行力核／solver／viewer／HP 或生成新图与科学数值。
