# M-RESUME1 执行包装源码准备

当前仅完成外部源码准备及 AST 解析，不构成授权、测试通过、续算成功或新图。正式基线为 main `01b5078acaf76fdaabfbdf214da9db16056467bc`；建议阶段路径为 `lf_data_preparation/native_interface_001/saved_continuation_001`。正式核心、原保存结果及旧显示均未改动。

## 一次连续执行的功能

未来 `execute_resume.py --repo <root> --protocol <stage/protocol.json>` 先执行冻结的5个 focused pytest nodeids（4个 synthetic/algebra 控制器合同及1个真实16-cell NumPy/TMC公共保存／续算集成），首个失败即停止；然后只调用一次原模型公共 `evaluate_native(None, None, new_directory, saved_result=parent_result, selected_state_index=13, targets=[1.20,1.15], ...)`。候选负责保存态读取、原任务 suffix、model/BC/material/options 一致性及控制器；包装不重写 task 或实现另一个续算算法。

父结果为原 alpha5e-7 的失败路径，已接受 original index13/loading/physical mean1.20 mm，原 index14 为卸载1.15 mm。初始状态使用保存 lift/fluctuation、JSON 完整精度 R、原绝对参数1.20及 target_origin0。初始 K 为 None，fresh F/T 在原生产容差下重验 anchor；之后只推进原第一下降目标。公共结果和响应必须保留 parent failed/time_limit、原 path/task/unload false，并明确 segment_completed、anchor 及局部0/1→原13/14身份。子段成功不意味着父完整路径完成。

普通 controller failure 返回后，先复用原 cached writer 和 summary 保存真实 partial result/typed response，再将 helper 关闭为非成功，并不启动显示。资源或导入异常可能早于完整 API 返回，届时只能承诺真实已有回调/收据/文件，不承诺伪造完整失败产物。没有 terminal retry、修复重跑、延期或 force。

## 输入与源码分离

生产保存读取为2个既存 NPZ、6字段：原 geometry 的 solid/design/passive_solid/passive_void 四个 uint8 栅格；selected accepted013 state 的 lift/fluctuation 两个 float64(27378) 数组。配套普通 JSON 为原 result/model/state013/source geometry；包装还读绑定的原 alpha protocol 来逐项继承 gates。无需解码原 model/forces/tangent/matrix NPZ，也不读取失败 trial 的切线缓存。该读取合同由候选 reader 验证，包装仅使用候选返回的缓存。

`protocol.source_package.files` 逐文件声明 runtime hf_repo 相对路径、正式仓库内冻结源路径及 SHA。运行目录为 `run_001/source/hf_repo`：完整51个原 `src/hf_eval/*.py` 经已审覆盖后，再加 `native_resume.py`，共52个 runtime 模块；另放候选 CLI/选定测试及 `resume_focused_budget.py`。机械 API 从该 runtime `src` 导入；源复制前后都逐项对账，最终收据记录实际 runtime 路径和 SHA。`mechanics_source` 中的 package 相对标签不能当作实际执行的是原正式核心，runtime 收据给出该关联。

pytest 子进程从同一 runtime hf_repo 执行 `-q -x -p resume_focused_budget <exact nodeids>`，插件将候选 src 放到导入路径首位、核所选 nodeids 及已导入 HF 模块来源。4个既存 fixture源（test_native_force/test_native_mean_mechanical/test_split_cycle/test_split_displacement）与新测试源均须复制并绑定。第5个测试确实进行tiny16-cell F/T、求解、保存和续算；其机械调用与原模型生产计数隔离，不声称测试 F/T 为零。测试都在未来授权窗口内；不能将 AST 解析误称为当前已进行过数值验证。

成功后才启动独立纯显示子进程，`--repo <formal root/hf_repo>`。原 `saved_right_margin_views.py` 字节不变，并保持原 pure import closure（__init__/native_region_geometry/boundary_geometry/workpiece_nodal、measure 脚本和 viewer）；它不从 runtime overlay 导入。动态普通 view protocol 仅绑定这些纯源码和本次新 result/model/state/forces 保存文件，不绑定或读取新 tangent/matrix。

## 原门、输出和观察范围

包装要求 `protocol.gates == original_alpha_protocol.gates`，且为原四门：residual1e-9、average constraint1e-10、global force balance1e-6、fixed split sum8e-11 mm。接受态还沿原 J>0 检查。25 Newton checks、Armijo1e-4／12 backtracks、max bisections4、minimum increment0.00625 mm和其余 settings 与父保持，仅 controller time limit 为本次明确的新额度。缓存门读取实际 accepted 的缓存，不增加新的力/切线/HP。

成功子段接受数 N 为2..9：一个 fresh 合格 anchor 加至多8个0.00625 mm下降子步，原两个 target13/14必须存在；失败保存实际已接受数量。生产 F/T started/completed 与原 result.call_counts 对账；save/summary 前后 F/T计数应不增。计数仅监测生产 native_mean 入口，不声称全局动态 hook 覆盖；HP/JIT0依据限定原源码路径和已有 producer records。

原纯 viewer 每个新态执行一次 geometry 和 nodal observer，故成功为N+N、703N条节点 CSV 行；它读取本次新1+2N个 NPZ、27+18N个字段（model27、每态 split2+force16）。新增观察只在 API 成功后发生。输出固定3PNG（comparison/distances_forces/peak_fields）及1个 N帧 actual_states.gif，不另复制帧或绘制跨父子合并图。纯 viewer 已检查实际 GIF 帧数；包装保持这些原输出和资格合同。

变形 x1、镜像仅显示；箭头是 ON-body nodal weak force，含cut/interior，材料/Hu分量可抵消。距离、ray、J/Hu/Green 场沿原 saved-array 定义，没有新独立参考、压力、有效夹持力、稳定性或 HF5资格。原父图和旧24态/48HP资格不转移到新段。

## 暂定资源与真实收据

拟一次 continuous controller1800／helper2700／outer2760秒，采样8GiB；focused tests最多120秒，pure viewer最多600秒，约180秒用于其余 import/copy/save/check。生产设置/测试/显示各有明确上限，后两子进程受剩余 helper window 约束。helper检查自身RSS，原 generic outer launcher 采样整棵树；这些是合作检查及采样，不是 OS 硬限，force-free cleanup可能超过名义阈值。

估算依据为原普通记录：父峰值接受于8573.541880299992秒（F292/T120），父完整失败controller9031.857919999995秒，outer9059.673925399999秒，峰值采样树RSS约1.402GB。已有同h0.5原24态 raw显示约37.51秒、helper39.70秒；本次至多9态。它们只提供预算依据，不能保证fresh anchor及卸载在1800秒内成功。

共享 stop_requested.txt 在下一原 F/T/checkpoint 或子进程检查点生效。父 helper 等待真实子进程终止、无 kill/force；terminal child elapsed也核上限。正常一次执行留下 outer完整终态、helper成本快照、focused_test_receipt、accepted_progress、typed result/response、cached gates、pure view收据和实际输出SHA。最终 helper收据在写完后仍检查2700秒；若该最后检查失败，即使已有 provisional pass收据，仍以真实非零 helper／outer NOT_PASS为准。

## 保留证据的边界

执行前后检查选定 inputs/source/protocol pins 原字节保持，新产物只在新 run_001；不为声称全部父文件不变而读取旧 force/tangent/matrix。后续普通 Git差异与增量交付继承旧manifest，另提供父旧条目保留证据。准备稿、AST及作者收据均保持 authorized:false／executed:false；实际公开source proof和人类原回复只能在后续正式批准后另行建立。复用原 generic `launch_alpha.py` 原字节为新 launch 文件，阶段仍为三层路径，其 ROOT=parents[3]保持正确。

协议最少需要 card/source_baseline_commit/bindings、parent_result/parent_protocol、selected_state_index、targets_mm/options/settings/gates、phases.production、focused_tests_seconds/view_seconds/sampled_RSS_bytes、candidate_directory/view_directory、source_package.files、focused_test_nodeids、pure_view_bindings/viewer_source。最终 frozen协议及候选测试清单必须独立复审后方可执行，本说明不替代该审阅或授权。
