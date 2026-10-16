# L-BFWD1 真实短加载批量消费结果：PASS

2026-10-16。基线main `ff448447a135d31314f7a0bd88e6ddd8ed449bfb`，science版本0.5.0，science baseline `b1334bb6a83ba9a0efab7bdba7bd39722146f024`。唯一终端 `8e5296/session26587`，实际tool exit=0。记录只读最终普通JSON，不重开科学窗口、不读取数组或媒体payload。

## 整体目标、目的与本步实现

整体目标是独立HF读取普通LF几何，在明确共同任务下返回可追溯、可恢复的非线性/TMC响应，供外部研究层消费与比较；HF不做优化、不调用dmftd，MPM不实现。

本轮补L-BPREP1新fine/wave准备产物、task1.1固定工件和当前mechanical/chunk256/port_projection到已有native batch真实求解链的衔接。不是声称首次实现batch：旧无工件batch已有历史。没有重做LF转换、默认HF安装、生产内核变更、新测试或HP。

两新任务仅把input.target由1.20改0.50mm、path改为load_only [0,.25,.50]，并改准确的task_id/purpose/parameter_origin/description；其余逐值保持，原两份25目标task/准备产物不动。保E1MPa、nu.3、厚20mm、h.5、84×40mm、固定side18方体center(71,40)、原支撑/端口/对称、gamma1e-6、alpha5e-7/Lr80mm。controller每例1800，原生产门和内部Armijo/二分设置保持。

新代码只在研究层：一次原batch、薄API/solve/on_accept标量观察与原cache门；成功后一次干净子进程原pure viewer、两次只改label/title/来源元数据的收敛副本、状态表和人工页。显示共享600秒，含显示流式seal；helper4500/outer4560秒、8GiB。原接受态/字段原值保留，不按同d去重、插值、造力或新设误差阈值。

## 实际结果与作用

outer=pass；helper=pass；batch=success；display=pass。整体PASS按实际终端、两收据、batch、显示及其原seal判断；生产success不能覆盖显示、清理或封存失败。

| 设计 | batch | result | 接受态 | 最后d mm | R N | q_out mm | 总Fy N | 材料Fy N | Hu Fy N | 全局minJ |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| gripper_native_fine | success | success | 3 | 0.5 | 0.07624835727107876 | 0.4792732955273436 | 0.00034791873300466907 | 0.0002147193965801673 | 0.00013319933642450178 | 0.5177396181452025 |
| gripper_wave_fine | success | success | 3 | 0.5 | 0.08593082815865576 | 0.4811512138551336 | 0.0003512425565784398 | 0.0002156916134184984 | 0.00013555094315994133 | 0.5164004668740174 |

原调用计数：`{"batch_started": 1, "api_started": 2, "solve_started": 2, "solve_completed": 2, "api_completed": 2, "batch_completed": 1, "display_started": 1, "display_completed": 1}`；接受进度行数=6。每例生产F/T来自原返回cache元数据，不冒称全局动态机械hook；真实开始/完成、原门、settings和失败见收据/closure。无新测试、默认安装、HP；原内部拒绝/二分属于原控制器，不叫外部重试。

- gripper_native_fine：原诊断记录行数 {"newton_history": 15, "trials": 12, "failed_attempts": 0, "linear_solve_diagnostics": 14}
- gripper_wave_fine：原诊断记录行数 {"newton_history": 15, "trials": 12, "failed_attempts": 0, "linear_solve_diagnostics": 14}

上述仅普通原诊断表的行数；缺失为未产生/未观察，不填0。异常终止后快照中的running也不表示进程仍在运行，实际终端及SUP2清理事实分别保留。

## 物理解读及限制

- gripper_native_fine：最后接受d=0.5mm，R=0.07624835727107876N、q_out=0.4792732955273436mm，下半工件Fy=0.00034791873300466907N。 同态bottom有限首射线=0.5210256544012282mm，实体minJ=0.9891806659477834、自由介质minJ=0.5177396181452025。该有限射线观察仍为正，非零弱式作用不能据此命名接触后夹持。分区场来自保存态viewer；没有新HP资格。
- gripper_wave_fine：最后接受d=0.5mm，R=0.08593082815865576N、q_out=0.4811512138551336mm，下半工件Fy=0.0003512425565784398N。 同态bottom有限首射线=0.5191397665813575mm，实体minJ=0.9879518030952109、自由介质minJ=0.5164004668740174。该有限射线观察仍为正，非零弱式作用不能据此命名接触后夹持。分区场来自保存态viewer；没有新HP资格。

R为半模型输入执行器作用，q_out为加权端口位移，不是间隙。工件total/material/Hu是固定下半体ON-body有符号弱式合力，holding reaction相反；完整工件净力和双侧法向幅值和分别保留，不能替代局部连续压力或有效夹持资格。有限射线、tip无符号有限距离和节点窗口各按原定义，不相互改名；null不是零。

本轮只处理短加载，不授原1.20mm完整路径、卸载、全路径独参、全部切线列、压力、有效夹持、自由体释放/稳定性、正式标签、排名或HF5。制造pending和原失败历史保持，原producer flags/参考覆盖不升级。整体HF目标仍未完成。

## 实际显示及恢复入口

- gripper_native_fine [result](<run_001/cases/000/result.json>)
- gripper_native_fine [response](<run_001/cases/000/response.json>)
- gripper_native_fine [viewer summary](<run_001/view/gripper_native_fine/summary.json>)
- gripper_wave_fine [result](<run_001/cases/001/result.json>)
- gripper_wave_fine [response](<run_001/cases/001/response.json>)
- gripper_wave_fine [viewer summary](<run_001/view/gripper_wave_fine/summary.json>)

![convergence.png](<run_001/convergence/000/convergence.png>)

![convergence.png](<run_001/convergence/001/convergence.png>)

![comparison.png](<run_001/view/comparison.png>)

![distances_forces.png](<run_001/view/distances_forces.png>)

[实际接受态GIF：gripper_native_fine](<run_001/view/gripper_native_fine/actual_states.gif>)

[实际接受态GIF：gripper_wave_fine](<run_001/view/gripper_wave_fine/actual_states.gif>)

![peak_fields.png](<run_001/view/peak_fields.png>)

媒体链接仅来自本轮helper/display原seal路径，不在关闭阶段打开、解码或重新hash。真正显示的×1形变、显示镜像、nodal弱式箭头及场尺度沿原viewer；短任务peak/last是实际最大接受态，不能误称1.20mm峰值。若本轮失败，已存在媒体仍只是实际partial证据，不改变NOT_PASS。

[batch index](run_001/batch/index.json) · [helper收据](run_001/execution_receipt.json) · [outer收据](batch_launch.json) · [同实例日志](batch_instances.ndjson) · [状态表/人工页](run_001/REVIEW.md)。某文件若未生成，以实际收据为准，链接不代表成功或许可重建。像素QA记录：pass_pixel_inspection；本关闭脚本不查看图像，不追加任何像素检查。实际结果审阅：pass_finite_actual_readonly_review。

## 执行、资源、封存与失败事实

helper=1743.728596699999秒／4500秒；outer=1744.4946827999993秒／4560秒；SUP2采样峰=1119481856B／8589934592B。 采样RSS不是OS硬限。CPU telemetry关闭，原SUP2协议F-CPU-CLEAN1/CPU-CLEAN1保持；cleanup_verified=True。不存在新force fallback、延期、第二次启动或自动回滚。

原helper seal=complete_inside_original_helper_window，列82份；显示独立seal=complete_inside_shared_display_window，列38份。显示共享600秒seal与helper总窗口seal作用范围分开；此脚本不以关闭后重hash补完整封存。生产source/input bindings保持事实=True，旧结果重写标记=False。

```json
{
  "helper": null,
  "outer": null,
  "batch_failure_case": null,
  "stop_reason": null,
  "helper_resource_stop": null
}
```

任何首个non-success后后例not_run、partial、错误stage/code/class/reason均保留。不为看partial追加viewer/收敛或把缺失数据填零。本关闭只写普通说明，不重跑构模/F/T/HP/测试/图或封窗科学核对。

## 结果驱动的下一步

详见[NEXT_STEPS.md](NEXT_STEPS.md)。最近步骤按两例实际状态和最后接受态选择，不自动扩行程、降低原门或宣称本卡完成全项目。发布/恢复另核真实main回执；本文件不等于已提交/推送声明。
