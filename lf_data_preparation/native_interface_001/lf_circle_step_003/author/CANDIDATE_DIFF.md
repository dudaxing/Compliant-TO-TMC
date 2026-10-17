# L-CSTEP3 源码适配摘要

人类已授权从圆形1.15 mm保存态推进到1.25 mm。本目录仅静态准备候选和普通收尾源码；未创建授权、protocol、task或card，未启动、测试、导入HF或读取科学数组及媒体。root另行冻结实际授权与启动参数，并负责唯一执行。

来源为正式 `lf_data_preparation/native_interface_001/lf_circle_step_002` 的两个入口和 `author` 内三份收尾源码。未来stage为 `lf_circle_step_003`，基线固定 `260d4b86ee87ab3dd12c04dbcccef7ffa4c31eac`。输出basename仍为 `wave_circle_step`；`step_launch.json`、日志、状态、图表在新stage下隔离。

| 层级 | 本轮明确适配 |
|---|---|
| 直接父段 | S2已保存成功子段 `[1.00,1.15]`，不是更早的S1或祖锚 |
| 选中父态 | accepted1 / global5 / local1 / loading1.15；SHA `3db267551ea6cb5817c2a1946a80363ecccb0329078d516e90e0106f27e709ef` |
| 父 continuation | source task `[0,.25,.5,.75,1.00]`，original task到1.15，appended `[1.15]`，global indices `[4,5]`；整个parent_continuation原值继承 |
| 新任务 | 完整前缀 `[0,.25,.5,.75,1.00,1.15]` 只追加1.25，input peak=1.25；只另改四说明字段 |
| 新子段 | `[1.15,1.25]`，global `[5,6]` / local `[0,1]`；实际接受态数N允许原二分增加 |
| 首态 | 使用父原绝对split与带符号R，fresh F/T各首次调用、一次检查、状态SHA及R身份保持 |
| 新来源/结果 | source task到1.15，original task到1.25，appended1.25；endpoint、scope、人工页与新global indices同步更新 |

未做全局数字替换。父/祖层与新层按明确上下文逐处替换；圆半径9 mm、中心(71,40) mm、固定DOF、原材料与网格、平均端口及所有剩余物理任务、数值门和settings保持。minimum_increment明确保持0.00625 mm。原API/solve/cache-gates/接受回调、内部回溯与二分、停止文件和新保存态持久化流程不改。

绘图仍直接引用正式S1的 `circle_saved_views.py` 与 `plot_convergence.py`，没有复制或修改绘图源码；既有图例小注记保留。新4PNG和实际N帧GIF按原显示合同生成。本候选没有重画或解码任何图像。

launcher保留三个授权严格布尔、card、approval_card、非空实际direct_human_request、protocol SHA、BASE与实际HEAD绑定。未替人类编造原话或创建authorization。SUP2、固定清理、一次调用、controller1800 / 共享显示600 / helper2700 / outer2760秒及采样8GiB不改；首错停止，无外部重试、修复重跑、延期、force、默认安装、测试或HP。

L-CREF1只核父global5的已保存1.15 mm态和声明PORT方向；不向本次新1.25 mm、完整前缀、压力或夹持资格转授。new_peak_reached、extended_segment_completed只表示实际子段，task_target_executed/full_original_path_completed/full_extended_path_completed保持False。

三份普通收尾源码同步修改CARD、stage、BASE、父态、子段与提交说明，保留actual N、partial/null、七front的BASE原始suffix仅一次、原窗口科学seal＋stat、动态manifest继承及普通main推送/异目录增量恢复。当前manifest历史21865条不重新扫描或哈希旧payload；脚本动态读取条目数，不锁定历史数。下一单目标由root依据实际结果补充，不在候选内执行。
