# 单任务前向接口的最小边界审阅

现有后端足以组合一个易用入口。本阶段新增一次 `solve_native_mean`＋一次 `write_native_mean`，保持 native_mean、模型、Newton、J门、线搜索和生产资格字段原样。求解入口已包含一次构模；不预构模，不自动切换初始化或重试。缓存保存以后，响应整理只读 JSON，不追加 F/T、NPZ、几何或绘图调用。

任务 1.1 的路径必须等于声明 targets；1.0 可以沿用 `[0, input.target]`。网格来自 geometry。CLI 原规则是首个非零增量 `targets[1]/16`，API 的显式 settings 不自动重写；这与 `DisplacementSettings` 的固定默认 `.025/16` 不同。完整记录实际 complete/mechanical、full/chunk256、tangent/port_projection 和 settings；默认冷启动保持 tangent，新增 CLI 选项不能静默改为探索包装所用 port_projection。

控制器失败返回可保存前缀，目标响应 null，最后接受态和前缀峰值另列。加载峰到达与卸载端点／整路径完成分开；无接受态时不创造零态，无工件力时用 null。输入、几何、构模等可在返回结果前抛错：只能报告实际调用边界、原异常类/message/code，不能从文本猜更细阶段，不能把此类异常伪造成已返回的数值失败。保存或响应整理失败不复算，并保留已实际落盘的结果路径。

时间要分层：控制器内部 clock 不包含构模与保存；native_mean `evaluation` 包含构模和求解，不含 writer；现 CLI 的 STARTED 总时钟在保存后检查，因此可能已有 success result，但整体命令仍超时退出。接口须分别保留 solver status、整体调用状态及时间来源。不得通过修改 solver status 隐藏保存后的超时，也不能把协作式 time check 说成硬进程或 RSS 限制；实际执行阶段仍由单独有限 launcher 约束。

紧凑数值用保存 JSON 原值和 scope：R 为 actuator-on-model，q_out 为加权端口位移；最低 J／maxHu 原字段是其声明的全域范围。node_window_clearance 是光栅节点诊断，不能改名为有限尖端面距；Green／有限 gap／图链接缺失则 null，或仅链接显式绑定的保存观察。下半固定体的总／材料／Hu 弱力和 holding 分开，`2|Fy|` 是镜像幅值和，镜像净力为 `(2Fx,0)`，均不直接称为压力。

生产 flags 始终 false。新 summary 只负责报告，不能制造独立参考或 HF5 资格；若用户显式提供旧 witness，须同 result SHA、全部实际 N/state 身份和实际 2N 调用一致，并保留其原资格范围。没有或不匹配时仍是可用的未独立合格前向结果；不按 case 名搜索旧 pass，不把解析成功扩大为压力、全切线列、应变 HP 或新 HF5 验证。

新 output directory 不复用，求解前只需一个廉价存在检查。输入与输出明确按约定解析，provenance 历史路径不成为运行依赖；stdlib JSON 响应记录 result/task/source 和显式 reference/view 的实际 SHA。一个普通入口、几个明确状态和 compact response 已足够，不需要新增大框架或全项目防御层。本审阅仅当前源码和三个已闭合 JSON，无接口实现、科学调用或执行资格。
