# L-CSTEP2 候选源适配摘要

时点说明：下文“未生成protocol/task/card”描述两份包装候选子任务刚完成时的范围；root随后已生成这些普通准备文件，当前完整状态以preparation_receipt.json及独立静审为准。授权仍未生成，科学执行仍为0次。

本目录仅静态准备。未获准科学执行，未生成 protocol、task、card 或 authorization；未启动 launcher/helper，未导入 HF、运行测试或读取科学数组、媒体。仅复制正式 L-CSTEP1 两份源码并逐处适配，执行 AST 语法解析。

来源：`lf_data_preparation/native_interface_001/lf_circle_step_001/execute_step.py` 与 `launch_step.py`。未来正式目录为 `lf_data_preparation/native_interface_001/lf_circle_step_002`，基线固定为 `a3e444dc106cd79123cd5455f623d54dc7b43628`。basename `wave_circle_step`、`step_launch.json`、`step_stdout.log` 与 `step_instances.ndjson` 保持，由新目录隔离产物。working_directory 仍由未来 protocol 指定新 AUTHOR 的外部执行目录；其既有“存在且不位于正式仓库内”的合同保持。

## 明确适配

| 对象 | L-CSTEP2 候选要求 |
|---|---|
| card / 源基线 | `L-CSTEP2`，protocol 与 authorization、launcher HEAD 严格绑定当前基线；helper 亦断言基线 |
| 唯一父结果 | `lf_circle_step_001/run_001/wave_circle_step/result.json` |
| 选中父态 | accepted index 1，global original index 4，d=1.00 mm，本地原目标索引1 |
| 父子段 | `[0.75,1.00]`，完整父任务 `[0,0.25,0.50,0.75,1.00]` |
| 父 continuation 来源层 | source task `[0,0.25,0.50,0.75]`，original task 到1.00，appended `[1.00]`，全局索引 `[3,4]` |
| 新完整任务 | `[0,0.25,0.50,0.75,1.00,1.15]`，input peak=1.15 mm |
| 本次真实子段 | `[1.00,1.15]`，新 global indices `[4,5]`、local `[0,1]`；首态为 fresh F/T 复核的1.00 mm源态 |
| 新 continuation | source task到1.00，original task到1.15，appended `[1.15]`，requested suffix `[1.00,1.15]`；parent_continuation 原值继承 |
| 响应与显示说明 | reached、endpoint response、来源/资格文字、view protocol 与人工页改为1.00/1.15；不声称重新执行完整前缀 |

未对数字做全局替换。父层和新层分别更新，物理 radius=9 mm、center=(71,40) mm、固定自由度及其他任务值仍按原合同精确保持；只允许旧前缀追加和四个任务说明字段更新。原数值设置、options、门和资源保持，minimum_increment 仍0.00625 mm并作明确核对。

## 授权包装适配

旧 launcher 硬编码上次用户整段批准原话；新阶段尚无对应人类批准，因此不编造替代原话。经 root 指示，候选要求 `authorization.approval_card == 'L-CSTEP2'`，`direct_human_request` 为非空字符串，同时保留 authorized / authorization_from_direct_human_request / one_invocation 三个严格布尔、card、protocol SHA、授权源基线和实际 HEAD 的严格绑定。实际原话只在收到人类批准后记录，由 root 核对其范围与卡。此候选不构造授权、不启动运行。

## 保持部分

复用正式 S1 的 `circle_saved_views.py` 和 `plot_convergence.py`，通过 protocol 引用且在 helper 断言这两条既有路径；未复制或修改绘图源码，保留既有图例小注记。继续只解码新保存态显示所需数组，旧 parent 的力、切线或矩阵不作为续算入口。纯 viewer source pins、独立子进程、原几何/节点观察、N态显示与GIF帧数、4PNG范围及新图像检查安排不扩大。

控制器1800秒、共享显示600秒、helper2700秒、outer2760秒、采样8GiB；原 SUP2、固定清理合同、停止文件、首错停止、一次启动、原内部回溯/二分、窗口内封存及无外部重试/force 保持。没有默认源码安装、测试、新HP或新力学核。new_peak_reached / extended_segment_completed只描述本子段；task_target_executed、full_original_path_completed、full_extended_path_completed仍为False。

此处不是科学结果或执行批准，只有候选代码和普通适配摘要。后续 root 另行准备并审阅 protocol/task/card 与授权元数据。
