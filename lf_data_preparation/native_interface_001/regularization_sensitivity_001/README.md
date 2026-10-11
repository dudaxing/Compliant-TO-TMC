# 当前接续：M-ALPHA1实际执行已闭卡：未通过

独立HF有限变形／TMC评价仍面向结构实际变形、输入反力和可解释工件作用，逐步支持同任务候选比较及HF5。main开发，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git；HF与LF优化断开。

M-ALPHA1经真实直接批准后唯一执行，现已NOT_PASS闭卡：原点／加载14目标至1.20 mm全部接受并保存，第一次卸载至1.15 mm触发controller time_limit。loading_peak_reached=true；path_completed、unload_endpoint_reached、task_target_executed均false。已保存14态的缓存原生产门passed，完整15目标合同仍未完成。原57 bindings保持，science0.5.0和原资格保持。

只改alpha1e−6→5e−7，gamma1e−6、Lr80 mm、h0.5／84×40 mm下半域、原固定side18方体、E1 MPa／厚20 mm及原BC／平均端口保持。峰值R=0.37865427196005513 N，下半工件total／material／Hu Fy分别为0.12492121630032427／0.12405713468784063／0.0008640816124836284 N；它们是有符号弱力作用，双侧法向幅值和0.24984243260064853 N不是有效夹持力。新有限面距离和分区场指标尚未观察，原node-window／全模型J/Hu不能替代。

force304启动／259完成，tangent126／126；batch／API／model／solve／save／summary各1次，缓存保存和摘要额外F/T0，HP／JIT0、view_child0。outer exit1／stopnull、elapsed9059.673925399999 s、sampled tree RSS1401597952 B；停止来自controller原时间预算。采样不是硬OS上限，不作同刻RSS比较，无重试、修复重跑、延期或force。

本轮没有新alpha PNG／GIF／比较表，显示在首次终端非成功后未启动，旧窗口已结束。下一步先发布真实记录，然后准备复用14保存态做实际变形／三分量力显示，并静查既有卸载耗时／回滚记录；不重做加载或扫描新alpha。本正文不创建新卡或运行新观察。

完整NumPy力、全DOF未对称矩阵、平均输入Mean、API／同任务batch和实际保存态显示已有实现；新alpha显示尚无产物。原24态48HP只属于原alpha，独立切线参考限PORT方向。fixed square/circle构造与circle staircase支持已有，但当前region/viewer固定square专用；rectangle任务、一般输入控制、全部切线列独立验证、连续总压力、可移动工件／摩擦、有效夹持、物理稳定性与正式HF5仍有缺口。metadata审阅／发布通过不会改变本轮execution NOT_PASS。


[实际结果](RESULTS.md) · [最近取舍](NEXT_STEP_REVIEW.md) · [终态审阅](author/execution_terminal_review.json)

<details>
<summary>更新前完整原文（历史状态不代表当前）</summary>

# 同任务 alpha 敏感性候选 M-ALPHA1

2026-10-11。**已准备，未明确批准，未执行。** 当前生产基线为 main `5af8b5e` 的固定方体 h0.5／84×40mm／原24态任务。最近完成的 M-BOUND1 已通过并闭卡。

本阶段服务于独立 HF 有限变形／TMC 前向评价及后续同任务候选比较。已有力、切线、平均位移求解、API／batch、实际变形显示和原细网格48HP；本轮针对缺少的当前任务alpha单因素证据准备最小增量。

- [本轮目标、实际审计效果、既有曲线和完整取舍](PREPARATION_RESULTS.md)
- [M-ALPHA1 具体卡与资源](M-ALPHA1_CARD.md) · [协议](protocol.json)
- [task](task.json) · [manifest](manifest.json) · [生产包装](execute_alpha_cycle.py) · [纯显示／对照包装](compare_alpha_views.py)
- [网格任务审计](author/MESH_TASK_AUDIT.md) · [参数审计](author/PARAMETER_TASK_AUDIT.md) · [实施取舍](author/IMPLEMENTATION_OPTIONS.md)
- [准备回执](author/preparation_receipt.json) · [独立输入／合同静审](author/input_scope_static_review.json) · [独立物理静审](author/physics_static_review.json)

alpha1e−6→5e−7，其它物理因素固定；真实零起点执行原15目标前缀到1.20mm并回撤至1.15mm，保留原控制器和验收门。未来一次窗口包括生产、缓存保存及实际变形／力／间隙／局部场显示和15目标比较，不重跑基线。两点提供参数敏感性，不授予稳定、连续压力、有效夹持或HF5；原48HP只属于原alpha态。

仅在本卡取得真实明确批准、记录与实际源码提交相符的授权后，在仓库根执行：

```text
<HF-python> -X utf8 -B lf_data_preparation/native_interface_001/regularization_sensitivity_001/launch_alpha.py production --protocol lf_data_preparation/native_interface_001/regularization_sensitivity_001/protocol.json
```

controller9000秒／helper9600秒／outer9660秒，采样8GiB。显示子上限min(600秒,helper剩余时间)。首个终端错误停止，无包装重试、修复重跑、延期或force。实际调用、资源、退出与图件待未来运行产生；当前没有run目录或authorization。全部开发只在main，origin为 `https://github.com/dudaxing/Compliant-TO-TMC.git`。

另机从仓库恢复时，先读 [CURRENT_STATUS](../../../docs/CURRENT_STATUS.md) 和 [RESUME_DEVELOPMENT](../../../docs/RESUME_DEVELOPMENT.md)。旧外部作者绝对路径是来源记录，运行只依赖仓库内已绑定普通文件和独立HF环境。核实际main、manifest／protocol字节和批准状态，不因本轮准备静审通过而启动计算。

</details>
