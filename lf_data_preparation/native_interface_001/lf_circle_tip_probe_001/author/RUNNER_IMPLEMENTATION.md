# L-CTIPPROBE1：薄执行包装说明

2026-10-22；仅编写与静读，尚未运行。研究脚本不写正式仓库，不安装源码，不修改生产API、内核、原SUP2或既存证据。root另拥有`outer_probe1.py`、protocol和唯一封存；本说明只绑定以下两文件。

|文件|字节|SHA256|
|---|---:|---|
|`D:/hpr1_001/run_probe1.py`|22763|`4da346dd9eaeb5e51ae3c0bbfcf35f6934368f3e2648f252493deab60aae51c6`|
|`D:/hpr1_001/launch_probe1.py`|4199|`d1172be8ad9b64a2042322f77061d18559dcc9cdee78982a819eb19c56c5b188`|

`launch_probe1.py --protocol D:/hpr1_001/protocol.json`只接受这一固定协议路径。它继承最外bootstrap的`PROBE1_ROOT_START_MONOTONIC`，唯一新建run_001，拒绝任何已有parent_001或run_001。原SUP2给helper绝对deadline=root_start+4495，保留原五秒清理并收于4500；helper内部deadline=root_start+4490。没有另选目录重试、删除、force或回滚。

helper先核所有candidate／observer绑定，然后仅按protocol.parent_files精确复制七个来源文件到parent_001；每份源和复制后的实际字节均核尺寸／SHA，三个NPZ不解码。源copy全部在helper原时钟内。协议的schema_version、frozen状态、预算、内存、线程、selected12、hold1.06及q[0,.025]都必须相符。

随后原SUP2唯一运行同脚本`--science-child`。子进程在首次HF import之前把candidate_source插入sys.path首位，并核hf_eval／native_probe的`__file__`确属冻结候选；不依赖旧editable环境。唯一API调用是copied parent、index12、q=[0,.025]、time_limit_seconds=3600。外子进程硬相位3800秒只容纳准入／单调用返回成本，总deadline还受helper剩余−665限制；计算该deadline后若剩余不足3600+5秒则停止，不启动科学子进程，不改变API controller的3600秒。回调只fsync紧凑标量JSONL，不保留大对象、不重算力或切线。

API返回失败与子进程失败分开：typed failed result是干净的子进程返回，但helper的数值门检查失败并停止viewer。来源拒绝／超时可能没有result，此时实际计数为null，只保存异常、已有回调及文件stat。没有用缺失result推断“零F/T”或“释放”。每层SUP2清理仍须通过同实例信号／成员覆盖／句柄释放合同。

成功后helper只读新普通JSON及新缓存字节身份，逐态核原数值门、q0两字段与R原身份、原选项／非clock settings、N≤5、原q目标、三力符号和false资格。只有上述及SUP2全部通过，才唯一调用pure viewer：

```text
python -X utf8 -B D:/hpr1_001/render_probe1.py --protocol D:/hpr1_001/protocol.json --result D:/hpr1_001/run_001/science/result.json --output D:/hpr1_001/run_001/view
```

viewer原SUP2为600秒／8GiB，主helper／science为64GiB采样；四库线程16。helper核其receipt的N个archive／2N字段≤10、3PNG／N帧和scientific_calls=0。成功只返回ready_for_visual_check，没有自动像素确认或安装。

runner／launcher不生成ZIP。root最外bootstrap完成outer清理、写回执后，只有原共享4500秒仍开放时，才一次按原字节封存整个BASE并排除目标ZIP／manifest／seal receipt本身。窗口已关就记录跳过；不在关闭后补压、补算或补画。这样outer实际清理证据能够进入唯一ZIP，避免launcher先压包时outer仍在写日志的问题。

运行时产物为parent_copy_receipt、science_child_receipt、accepted_progress.jsonl、各层SUP2日志／instances／supervision、numerical_validation、helper_receipt、launch_receipt，以及API和viewer实际新输出。主流程未对新state／force／F数组做科学解码；viewer的J／Hu范围由其单独静审和实际receipt证明。

本说明作者未启动HF import、API、F/T、HP、pytest、helper、renderer或生成PNG。独立运行准备检查和viewer审阅另记，不把自述当作执行通过证据。
