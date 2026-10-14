# 已准备 LF fine → 既有 HF 前向入口：窄源码审查

结论：现有入口已经具备这条功能链，下一步只需薄的单次执行包装。采用 L-PREP1 实际保存的 `cases/gripper_native_fine/derived_geometry/geometry.json` 和同 case 的 `task.json`，调用现有 `evaluate_native`。不重做转换、构模器、求解器或显示器，不另造小模型或较容易的任务。

普通记录一致：LF fine 原四掩码与 h=0.5 mm 保持，右扩8列/4 mm形成84×40 mm域；task1.1 保留25个原目标、输入峰1.20 mm、最终输入0、固定方形工件中心(71,40)/边18 mm、E=1 MPa、ν=0.3、gamma=1e−6、alpha=5e−7、Lr=80 mm、厚20 mm及明确背景对称。任务绑定新几何身份 `ddc7a66a…`；准备成功记录仍明确工件/模型兼容未检查。原模板 task_id/description/parameter_origin 的文字是被保留的来源，不能据此把新 LF random 几何的计算称作旧几何的单因素 alpha 试验。

`evaluate_native → solve_native_mean` 内部先调用 `build_native_project`，成功后才进入原 controller；无须另做一次重复构模预览。尺寸、上缘 y=40、背景声明和端口 profile 在 JSON 层相符，但以下原数组门尚未评估：工件各单元全属 passive_void；工件节点不共享机构、支撑或端口；背景覆盖工件顶部节点；支撑/实体对称有足够 solid 附着；原端口全附着且方向不交叉固定DOF。必须在未来一次实际 API 内保留这些原门。拒绝时保留 typed error，不能改工件、掩码或任务去寻找较容易通过的替代。

新计算须从零开始：不传 saved_result/selected_state_index，extend_path=False，targets=None 即取本 task 的全部25目标。原接口默认选项为 complete/full/tangent；settings=None 会把最小增量取第一步0.25/16，不能自动继承旧试验设置。执行卡应明确记录所选 settings 和已有机械入口 mechanical/chunk256/port_projection；这些是已有功能，不需修改力核。具体资源与设置尚待规划，本审查没有给出耗时保证。

成功或 controller partial 的 accepted 状态、R、q_out、F/J/Hu、材料/Hu/总弱力和切线均由现有缓存保存；write_native_mean 不新增 F/T。构模异常可由 API 写 response.json（阶段solve、原code/class/reason）；此时不承诺存在 model/result。非预期或保存异常只保真实已产生 partial，不能保证任意中断都已保存全部状态。首次 terminal 非成功后停止，不重试或调整任务。

显示可原样复用 `functional_views/right_margin4_20261007/complete_001/saved_right_margin_views.py`：新纯进程 `--repo <formal_root/hf_repo> --protocol <新保存输出绑定> --case LF_FINE=<真实结果目录> --output <新目录>`，不传 reference。同进程已经导入 solver 时，其严格纯模块集合门会拒绝，因此必须保持纯进程隔离。脚本没有 result.scope 白名单，支持新的 explicit zero-start square path；运行时核真实模型/任务/状态身份、(80,30)唯一见证节点、固定工件及 geometry/nodal 一致。它读取保存 model/state/forces，不重读切线/矩阵或调用 F/T/solver/HP，已有三张PNG和实际N帧GIF可显示变形、力、距离及保存场；N包含原二分，不预置25帧。失败后能显示partial是脚本能力，不自动授权在本卡终止后继续观察。

R 是半模型执行器作用于模型的输入R；q_out是端口加权位移；工件力是有符号下半体 ON-body 弱式合力，含材料及Hu，不是局部压力或有效夹持。2|Fy|是幅值和而非完整装配净力；输入到零也不自动授释放资格。旧 HP／图／warm state 不跨新 geometry/result 身份迁移；准备、生产和显示都不自动授接触、压力、夹持、稳定性或 HF5 资格。

本审实际读取并 raw SHA 核16份普通 JSON/PY，AST读纯模块来源；仅 stat 一份已准备HF NPZ，并继承 descriptor 的原SHA。没有数组字节/header/hash/解码、HF导入、构模、F/T/HP/求解/API/测试/绘图/像素或正式写入。JSON报告保存精确路径、原值和源码身份；这是源码/输入合同审查通过，不是构模或数值执行通过。
