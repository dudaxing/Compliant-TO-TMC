# 三方保存对照后的功能优先方向

本轮实际结果以RESULTS及执行回执为准；本文不声称下面的新功能已经实现。三方共同任务核对成立、保存结果可以对齐，不意味着制造pending、源epoch历史或完整路径参考资格已消除。

实际L-TCOMP1已PASS：两LF结构在近接触后输出受限、工件作用上升，可直接从同一表/图检查；本轮未发现要求先改力学内核或重做原路径的接口问题。历史M的曲线分离保留为来源受限的观察；若未来专门研究其原因，应另做受控同版本研究，不从本次历史拼接比较直接归因。

近期最有用的功能增量是“普通LF来源清单→共同task绑定→既有native batch manifest”的薄准备入口。现有批量求解器已能顺序执行，应该直接复用，而不是另建力学核、控制器或并行求解器。

- [lf_native_inputs.py](../../../hf_repo/src/hf_eval/lf_native_inputs.py) 的prepare_native_lf_inputs已完成普通LF v2数据转换、可选精确右侧介质列及task绑定；只允许替换task的两项geometry身份，保留其他字段。
- [native_batch.py](../../../hf_repo/src/hf_eval/native_batch.py) 的evaluate_native_batch已有共同任务/几何声明预检、逐例API、失败停止和index；[现有CLI](../../../hf_repo/scripts/evaluate_native_batch.py)直接可用。现有_preflight比较的是声明，不能冒认网格等价或收敛。

目前缺口是每个普通LF来源仍需手工单独准备geometry/task再拼batch manifest。建议新准备函数/CLI读取一个明确来源清单和同一task模板，循环已有单例准备函数，返回每例准备索引及现有hf-native-batch-manifest-1.0；路径以显式repo为基准，输出必须新建，保实际partial，不偷偷求解或重新优化。

首轮范围应限已验证的两个gripper普通LF来源、同h0.5网格、现有固定方体及原共同任务，明确右侧介质政策；核对新输出与既有准备结果的几何/task身份、输入未改和batch预检兼容，不重算已有三条完整循环。输入准备的数组读取、必要测试/显示和默认安装应在后续具体阶段另定范围与资源，不能沿用已关闭L-TCOMP1窗口。

批量准备成功也只得到可用输入，不授力学、独参、HF5或排名。批量实际运行仍逐例保原参考覆盖与失败；探索性响应先用于研究观察，制造阈值仍pending。连续压力、可移动工件/稳定夹持/释放以及更广样本/网格收敛，是后续各自的物理与证据范围，不由这张对照图代替。
