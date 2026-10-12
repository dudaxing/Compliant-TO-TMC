# M-INTEGRATE1 实际终态审阅范围

这是审阅提纲，不是执行回执或通过结论。主任务已报告直接人类答复“批准按 M-INTEGRATE1 卡执行”；本审阅者不归档或构造授权，不启动安装、测试或科学入口，也不由文件存在推断 live／terminal。仅在主任务确认真实终态后读取原保存记录。

原合同：协议 `62396704768bd3f6cd4ec09bf2e438c126ebd1867b590b5a119d4671a26e666e`，11 项安装（6 原源码快照／5 新目标），108 不可变绑定；拟运行包为 52 hf_eval 模块、2 CLI、4 安装测试。唯一 25 项 pytest 选择，tests180／helper300／outer360秒，采样8GiB；首错停，无 retry、force 或自动回滚。

终态只核实际普通 JSON、XML、stdout、源码和声明哈希：

- outer 和 helper 的实际状态、exit code、stop、一次调用记录、各整窗时间及采样 RSS；局部 receipt 不能覆盖 outer 非成功。
- 11 项实际安装记录和最终目标字节；未完成时如实保留 partial，既有6份 baseline 快照不变。52 个默认模块与2 CLI／4测试身份及实际 HF 导入路径来自正式包。
- 108 原绑定与原 material／Hu／切线／组装／补偿等核源码保持；本审阅不读取 NPZ。
- 实际收集顺序必须等于协议25项；25个 call 全部 passed，XML/stdout 没有 failed/error/skipped。测试可含原16单元小模型；不将 synthetic／mock 例认定为原夹持器验证。
- NativeMean NumPy aliases 的真实 started／completed 总数、分测试记录及16单元／50DOF范围按原回执复制。监测只覆盖被包装的 aliases，不推为全部 F/T 内核次数；异常 started 可以大于 completed。
- 来源迁移测试实际结果：旧 right4 生产摘要仍 success，但当前来源参考严格 mismatch；原保存 qualified response／参考／结果字节保留。right2 的来源影响是同两交集静审结论，未经实际调用不说新增测试已验证 right2。M-REF2 protocol11／summary12无迁移交集，不撤销其既有机械参考。
- 原 M-ALPHA1 NOT_PASS、未完成完整原路径和新alpha无HP保持。集成成功只支持默认入口及本卡有限兼容；不升级压力、有效夹持力、网格稳定性、全部切线列或HF5资格。

最终报告只解释已保存的实际结果，不重跑 pytest／collect，不调用总结API、模型、F/T、HP、solver、observer或绘图，不解码数组，不计算新物理差值或比例，不修改正式仓库。
