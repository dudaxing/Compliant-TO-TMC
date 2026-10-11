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
