# L-CSTEP4 源码适配摘要

本轮按直接用户请求和已发布S3后续方案，准备圆形保存态1.25→1.35 mm。此目录仅候选源码和普通收尾源码；未创建task/protocol/auth/assemble，未启动、运行测试、导入HF或读取、哈希科学NPZ及媒体，未写正式仓库。root负责实际授权冻结和唯一启动。

模板为正式 `lf_data_preparation/native_interface_001/lf_circle_step_003` 两个入口及author内三份收尾源码。未来正式stage `lf_circle_step_004`，基线 `df5398ba0903970e5f139d1679ee5f2cbc8f11d7`，输出basename仍为 `wave_circle_step`，新目录独立保存结果、日志、图表与回执。

| 层级 | 精确适配 |
|---|---|
| 直接父段 | S3 `[1.15,1.25]`，原global `[5,6]` |
| 选中父态 | accepted1/global6/child1/d1.25，SHA `d5b74358bf076a7d858efd710e61cf31fa2f9ddb1648a7a488e2cbc299213fc5`；R来自绑定父原记录并逐位保持 |
| 父continuation | source task到1.15，original task到1.25，appended `[1.25]`；整个parent_continuation继承，祖锚不能当作直接父态 |
| 新完整任务 | `[0,.25,.5,.75,1.,1.15,1.25,1.35]`，旧前缀保持，peak更新1.35及四说明字段 |
| 新真实子段 | `[1.25,1.35]`，global `[6,7]`、local `[0,1]`；actual N允许原内部二分增加 |
| 新态来源和显示 | reached/endpoint/scope/人工页/newglobal indices同步更新；首态fresh F/T、一次检查、原SHA和带符号R身份保持 |

没有全局数字替换。原半径9 mm、中心(71,40) mm及其余物理条件、settings（minimum_increment仍0.00625 mm）、原缓存验收门、API/solve/回调、停止与首错合同均保持。controller1800 / 共享显示600 / helper2700 / outer2760秒、采样8GiB、SUP2及实际N帧不改；无默认安装、新测试、HP、外部重试、修复重跑、延期或force。

viewer及收敛投影继续直接引用正式S1的两份纯源码，没有复制、修改或修正旧图例小注记。launcher只更换card、BASE与新输出目录；授权bool/approval_card/实际非空direct_human_request/protocolSHA/BASE/HEAD绑定及SUP2原合同保持。

L-CREF1仅核圆形1.15 mm/global5及一个PORT方向。直接父1.25 mm/global6没有独立HP，本次新1.35 mm/global7不从更早状态继承参考资格。新子段的new_peak_reached和extended_segment_completed不改变task_target_executed/full_original_path_completed/full_extended_path_completed为False的范围。

close/publish/archive仅同步阶段、BASE、父/新态与文字，保留actual N、真实partial/null、七front原始BASE suffix仅一次、科学/媒体原窗口seal＋stat、动态manifest继承、普通main推送和异目录增量恢复。关闭文案明确父1.25未取得HP。后续目标由root依据实际结果另定，不在这里执行。
