# 工件节点力 CLI 最终静态审阅

结论：**static_ready，无阻止当前一次正式执行的具体问题。** 本次仅读取源码与既有 cycle009 的保存 JSON 身份，并作 AST/`compile(source)` 语法检查；未导入生产模块、运行测试或观察入口，未调用 F/T、HP、求解或几何测量。不是正式运行通过回执。

审阅源码 `hf_repo/scripts/observe_workpiece_nodal_forces.py` 为199行，SHA `b30cc3af4587ae60b764f300aded6d6f29cc0f26ad2bfc5b84aa207a75bbe2c3`；`hf_repo/src/hf_eval/workpiece_nodal.py` 为76行，SHA `697e056fee1bddf4a611f2fc6e83de10747d923627b5f2d28c34eaf9a1d33ae9`。已读新增的三个纯模块 `__file__` 对账代码，verified 必须在模块集合排除及来源路径检查后才为真。

- 保存向量是真值入口：三分量均直接从 full-DOF global force 按 body 节点提取并取负号，无重新 scatter/本构。total 保持独立，未用 material+Hu 替代；各分量 `fsum` 合力与原缓存 body 合力精确对账，total 逐节点与 holding reaction 反号对账。单位 N，指定 task centre `[70,40]` 的派生矩单位 Nmm，不是压力或面力分摊。
- model 的 descriptor/task/array 身份与 result 交叉核对；每态 descriptor 全记录与 inline state 对应。实际 cycle009 已存九态及九参考态长度一致，model 的 workpiece definition 与 task 一致。循环按每个实际 state 索引 enumerate，不按位移值去重、不通过 zip 截断；有 reference 时逐态核 status/index/stateSHA/original_target_index/leg/target。无 reference 时明确 not_available，不借资格。
- 原 body 的全部153节点均写 CSV；API 要求节点集等于选中单元的 incident nodes，两个 DOF 均 fixed，CLI 核原 L/w 两数组在 body 上为零。四个拓扑组互斥且覆盖所有节点，cut 角点只归一次。三分量分组合力的 roundoff consistency 是保存数据一致性检查，不是新增 HP 验收门。
- 输入和源码按 `repo/`、`input/`、`reference` 角色保存相对键；source snapshot 使用输出相对路径及 SHA，拷贝后核对。受控正式 CLI 本身与 descriptor helper 都位于 `--repo` 内，角色映射能恢复，无作者绝对路径依赖。
- 首错误保存 failed/partial summary 后原样 re-raise；新机械调用计数仅在纯 hf_eval 模块集合及其 `--repo` 文件来源核验后为0，否则 None，`mechanical_hooks_monitored=false`。这是已读纯源码/模块来源推导，不冒称 hooks 实测。最后输入源码 SHA 检查后再 checkpoint，覆盖协同时间窗收尾。

原 `boundary_geometry.py`（`b22a9efe…fb31`）、descriptor helper（`56bba895…ed925`）、package init（`112503f3…eb73b`）静态依赖仍只供保存拓扑/哈希操作。当前一次正式卡应绑定上述实际字节及真实输入，沿冻结 helper/outer/RSS 预算、首错停止执行；本审阅不预填测试、节点观察或派生矩的实际通过状态，也不授予接触、夹持或压力资格。
