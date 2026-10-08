当前薄 API 没有接入本固定方体任务的必需核心功能缺口。`evaluate_native`、`native_batch` 和单例 CLI 已传递 `mechanical/chunk256/port_projection`；native task 1.1 已声明固定方体与完整加载卸载 cycle；保存摘要已经区分1.2 mm峰值、0 mm卸载终点与最后接受态，并携带原工件力字段。

自带控制器 settings 也已有：Python API 接受 `DisplacementSettings` 实例；batch manifest 的 `options.settings` JSON 构造同一类。目前 HF 没有独立 `SolverSettings` 类型。原 right4 inventory 的全部10个 settings 可直接提供，不能同时再传非默认 time/minimum 两个控制器参数。

本任务真正需要显式保持的是 minimum_increment=0.00625 与 time_limit_seconds=4500。默认首步0.25/16=0.015625，单例CLI默认180秒，都与原任务不同；其余CLI默认控制器参数与原inventory相同。因此现有CLI加这两项和三模式即可，无需新增settings机制。通用完整settings-file CLI是可选便利，不是本任务阻断。

可移植输入已是普通文件：`right_margin4_cycle_001/run_001/fixture/model/source_geometry/geometry.json` 与同目录 `geometry.npz`，以及 `run_001/task.json`。task绑定geometry ID/descriptor SHA，NPZ由相对文件名绑定；HF不需要导入LF，也无需把旧模型或旧24态缓存作为新solve输入。

推荐最小推进是data-only单case batch manifest，全部原settings、三模式和原geometry/task不变，输出指向新 `native_interface_001/workpiece_forward_001/run_001/fixed_square` 和 `batch`。候选已放外部 `api_job_candidate_001/fixed_square_manifest.json`，未导入、执行或安装。既有 saved_right4col_response 是旧保存态的摘要导出，不能当作新入口真实执行通过；未来新任务需自己的独立卡及实际终态。

批入口的现有边界是共享完整task声明（只排除task_id/geometry）和物理geometry声明。purpose/description/parameter_origin 等metadata差异也会触发严格相等检查；单case推进无需放宽合同。新index/invocation/response是运输metadata，不是新物理或新资格。不会重复实现模式、工件摘要、HP、接触或压力功能。

本次只读源与JSON、做普通SHA/AST元数据核查，正式仓库写入、产品导入、NPZ载入、tests、solve/F/T/HP均0。详细绑定与行级入口见同目录JSON：native_evaluate:21、native_batch options:44/preflight:88/call:154、native_project task:30、native_mean:113、native_response:162。
