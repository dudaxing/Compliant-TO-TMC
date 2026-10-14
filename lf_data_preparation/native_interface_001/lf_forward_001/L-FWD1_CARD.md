# L-FWD1：已准备 LF 细网格的一次完整 HF 前向计算

2026-10-14（Asia/Seoul）。本卡仅完成源准备，尚未批准或执行。基线 main `6e7d32fb52395938314a665c66993ba8d736a702`；origin 保持 `https://github.com/dudaxing/Compliant-TO-TMC.git`。

## 目标、现状及本步作用

整体目标是独立 HF 接收普通 LF 几何，执行有限变形／第三介质接触前向分析，返回位移、反力、固定工件作用及可恢复状态，供外部研究层比较。HF 不优化、不调用 dmftd；MPM 尚未实现，后续继续 main 开发。

L-PREP1 已实际安装输入准备 API／CLI，三个真实准备和九反例通过，完成未变形图及异地恢复核对。准备成功只证明输入处理与保真，不证明工件、端口或约束兼容，更不代表已经得到夹持响应。

本步直接使用已准备的 `gripper_native_fine`，一次调用已安装 `evaluate_native`：原构模检查通过才从零执行全部二十五个目标，成功后从真实保存态显示变形与力。没有发现需要重写构模器、求解器、力核、批量入口或 viewer 的功能缺口，因此只新增阶段运行包装，不安装或修改默认 HF 文件。

## 输入及明确物理任务

输入为 `lf_input_preparation_001/run_001/cases/gripper_native_fine/derived_geometry/geometry.json`、同 case 的 `task.json` 与 `input_manifest.json`。几何身份为 `ddc7a66a3ef45689e9b9a881155d5e5b4f71475615dcb33b5717a4353c60f91a`。来源 LF design_id 包含 `random`；保留来源身份，不将其认定为已优化或已验证的夹持结构。

原 h=0.5 mm、四掩码和 80×40 mm LF 子域保持，既有准备包显式增加八列／4 mm 被动空域，总域84×40 mm。声明网格80×168，对应预计13440单元／27378DOF；实际构模数、固定DOF和工件节点以本次结果记录为准。整个派生域不称为 LF 原域。

原 task1.1 字节保持：E=1 MPa、ν=0.3、平面应变、厚20 mm、γ=1e−6、α=5e−7、Lr=80 mm，固定方形工件中心(71,40)／边18 mm，原端口、支撑、实体及背景对称、自由输出及零辅助弹簧保持。原 task_id、description 和 parameter_origin 是历史模板来源；新几何不同于旧试验，不能把本次称作同几何单因素 α 对比。

完整绝对输入目标依次为：

`[0, .25, .50, .65, .75, .80, .85, .90, .95, 1.00, 1.05, 1.10, 1.15, 1.20, 1.15, 1.10, 1.05, 1.00, .90, .80, .75, .65, .50, .25, 0] mm`。

调用 geometry/task 的真实路径，`targets=None`，不传旧 saved_result、selected_state 或旧参考，不延伸旧路径。原内部线搜索／回溯／二分允许，接受态 N 可超过25；不得删目标、换更容易的几何、移动工件或放宽门来取得通过。

## 原检查与显式求解配置

构模在首次 F／T 前检查工件单元均为 passive_void、不共享机构／端口／支撑节点、工件顶节点满足背景约束，以及支撑、对称和端口附着／固定DOF冲突等原门。普通 JSON 审查尚不能代替这些数组检查。构模失败保存 API 的真实 typed error；不另做一次构模或在卡内改几何后重试。

显式使用已有 `response_mode=mechanical`、`tangent_mode=chunk256`、`initial_guess=port_projection`。原 zero-start API 字面默认为 complete／full／tangent，且默认最小增量为首步／16；本卡不把以下显式配置冒称默认值。

DisplacementSettings 完整复用 M-UNLOAD2 实际保存设置，只有 clock 改为18000秒：tolerance1e−9、constraint_tolerance1e−10、displacement_scale_floor1e−6、force_scale_floor_factor1e−8、max_checks25、armijo_c1e−4、max_backtracks12、max_bisections4、minimum_increment0.00625 mm。不将 settings 与独立 time_limit_seconds 参数混传。

保留原生产残差1e−9、原 average constraint_bound 规则、global force balance1e−6、固定位移8e−11 mm 和 J>0；用原缓存观察对账，不额外调用 F／T。记录实际 F／T 开始／完成及接受态，监测仅限现有 NativeMean 别名，不声称全局通用 hook。完整成功核二十五个 original_target_index 0…24、对应 d、实际任务／设置／选项身份及输入端点；缓存保存与摘要不新增力学计算。

## 数组、实际显示与产物

生产仅由原构模读取一份派生 geometry.npz 的 solid／passive_solid／passive_void／design 四字段（原 LF design_domain 对应 HF design）；不重做 LF 转换或读取 LF 快照数组。构模／生产生成的新模型、状态、三力、切线及 CSC 缓存由原保存器写入，实际次数依收敛／二分产生。科学身份读取／hash 和新产物封存只在本次开放窗口内。准备期只有普通源码／JSON读取及这一份旧 NPZ stat，没有数组字节、header、hash 或解码。

API及原生产门全部成功后，仅一次新纯进程运行原 `saved_right_margin_views.py`，不传 reference。它从保存 model/state/forces 读取观察字段，原模型27字段及每态18字段，即1+2N个NPZ／27+18N字段的静态清单；逐字段动态监测不作声称。不读取保存切线／矩阵、不调用新构模／F／T／HP／平衡求解。

产生原三张 PNG：实际变形与输入／输出响应、几何距离与有符号工件力、峰值保存场；产生全部实际 N 态的真实尺度变形 GIF。工件力是含材料和 Hu 的下半体 ON-body 弱式合力，距离是原节点／窗口几何观察，不能认定为局部总压力或有效夹持力。最多对三个新 PNG 各一次像素检查，不补图，不重读旧媒体，不再次解码新 GIF。

记录实际构模 metadata、API响应、接受进度、实际门／计数、真实保存结果、viewer terminal、显示及产物身份。任一终端非成功即停止后续科学／显示，保留已产生响应和部分结果；不保证任意中断都已保存所有状态。只有原窗口仍开放时允许一次部分证据身份封存，闭窗后不补科学 hash／解码／图。

## 一次资源窗口及结果分支

同网格旧 α=5e−7 的四段实际 API 耗时合计15230.27秒，尚不包含1.10→1.05 mm 段；旧14400秒预算偏紧。新 LF 几何的成本仍未知，本卡预算不承诺完成。

一次 controller18000秒／helper19000秒／outer19060秒（最多5小时17分40秒），采样8 GiB。viewer 上限600秒且共享 helper 剩余时间，不能追加窗口。helper 从最早 clock 覆盖导入、输入身份／批准核对、原构模、单次 API、保存与摘要、纯 viewer 和身份封存。outer 保持原 Popen／psutil 进程树采样、合作 stop 文件和真实子进程等待；不是 OS 硬限制，不使用 force，迟到 PASS 不通过。

首错停止，无外部重试、修复重跑、延期、force、删除或回滚；不新增测试、默认安装、候选复制、HP、API参考关联、优化或排名。不修改既有结果、失败历史、物理字段、原门或来源身份。完整输入回到零仅表示任务输入端点达到；独立参考、压力、有效夹持、释放、稳定性和 HF5 资格不升级。

通过后按实际响应判断下一项功能／独立参考；失败先依据原 typed error、部分状态及资源记录定位一个实际问题，另行准备明确修复。尚未执行时不能声称本新 LF 几何的构模、力学或路径通过。
