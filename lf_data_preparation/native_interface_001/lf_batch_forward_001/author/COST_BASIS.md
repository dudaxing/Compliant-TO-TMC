# L-BFWD1：两个 LF 固定工件短加载的既有成本依据

2026-10-16（Asia/Seoul）。只读准备，未实施新的 batch、构模、F／T／HP、测试、性能测量或图。未导入HF、未读NPZ／科学归档或媒体；没有仓库修改。原普通文件与源码的确切路径／raw SHA／大小见 [COST_BASIS.json](COST_BASIS.json)。

## 直接依据与时钟

wave真实短例目录是 `lf_third_pilot_001`（L-PILOT1），不是probe／forward别名；`lf_third_cycle_001`是完整循环。fine依据为L-FWD1原25态中的前三接受态，不能称已独立跑过相同fine短任务。共同机械模式均为mechanical／chunk256／port_projection，固定side18 mm方体center(71,40)，h0.5／84×40 mm／13440单元／27378DOF。

| 例 | 原点累计s | .25累计s | .50累计s | 原点/.25/.50新增检查 | .50累计F/T索引 | 中间二分 |
| --- | ---: | ---: | ---: | --- | --- | --- |
| LF native fine | 90.66581430000952 | 581.7781426999718 | 1113.1135367000243 | 1/7/7 | 27/15 | 无，depth均0 |
| LF wave | 90.55128550005611 | 553.2496371000307 | 968.223704700009 | 1/7/7 | 27/15 | 无，depth均0 |

| 例 | 零态增量s | 0→.25增量s | .25→.50增量s | 构模准备s |
| --- | ---: | ---: | ---: | ---: |
| LF native fine | 90.66581430000952 | 491.1123283999623 | 531.3353940000525 | 0.08135709998896345 |
| LF wave | 90.55128550005611 | 462.69835159997456 | 414.9740675999783 | 0.07855159998871386 |

上表累计是controller时钟，不是helper时钟；两例prefix至.50累计相加约2081.34秒，只作规划。原点约90.6秒包含首次力／切线等计算，已在controller内；不能把构模准备约0.08秒误作零态成本，也没有独立F与T逐调用耗时可拆分。两例原JIT_calls／HP_calls均0；不等于没有导入或注册JAX。

wave整个三态结果：F27/27完成、T15/15完成，solver total968.2397345000063秒、API evaluation968.3215757999569秒；kernel/transfer964.4389181002625秒、assembly0.2172773999045603秒、sparse solve3.062918399926275秒。fine只取prefix调用索引27/15，不把完整25态389/347 force计数当作短路径计数。

## 外层成本与内存

| 来源 | helper实际s | outer实际s | helper峰RSS B | outer树峰RSS B | 读数范围 |
| --- | ---: | ---: | ---: | ---: | --- |
| L-FWD1 | 12920.589909099974 | 12922.065238300012 | 1936846848 | 1931960320 | 完整25态+viewer，不是前三态RSS |
| L-PILOT1 | 1011.0132517000311 | 1013.6499084000243 | 845869056 | 848691200 | 仅三态pilot含原测试/viewer/convergence/seal |

wave原view child16.351580300019123秒、原有限测试child18.042115600022953秒；这些不是下一步必须重跑的开销。fine原25态view child48.981327900022734秒，不是三态viewer实测。原helper/outer峰采样时刻不同，应分别保留。

1GiB不是已被两例短batch证明足够的额度：wave单短例树峰848691200B已经接近1GiB；fine没有前三态RSS采样曲线，只有完整25态约1.94GB峰；同一进程顺序运行两例的内存保留／复用未被本轮测量。建议新卡采样8GiB，不声称它是OS硬限制或数学必要下限。原L-BPREP1输入准备的1GiB成本不能直接外推到真实F/T。

## 只规划下一条短路径

建议每例controller1800秒，两例顺序总controller额度3600秒；一个合并pure viewer额度600秒，准备／imports／保存／摘要／封存留300秒，helper4500秒、outer4560秒、采样8GiB。实际两例prefix观察约2081.34秒，旧成本不是下次保证。若root选择其他显示范围，须在卡中写清对应预算；本记录不执行或授权新计算。

须新建显式load_only任务：input.target_mm=.50、path.targets_mm=[0,.25,.50]；原25目标task／输入manifest保持，不用targets覆盖静默截断。两例共享task内容除geometry与允许的task_id外相同。新增短任务仅测试该链，不宣称原25任务完成。

九项nonclock settings两旧例完全一致，尤其minimum_increment=.00625必须明确保持。建议共享options用完整settings字典(time_limit_seconds1800)+mechanical/chunk256/port_projection；不要同时另给individual limits。原batch默认180秒不足以覆盖既有prefix，短步长默认minimum_increment=.25/16=.015625也不同。源码依据为native_batch.py:14/56/83/187与native_evaluate.py:89–99。

输入来自已prepared index中的000／001新geometry，普通JSON身份已核；不要重准备、重读旧响应数组或借用旧HP资格。当前四个mechanics source SHA与wave pilot完全匹配；fine原controller epoch较早，差异保留。

已经有旧的真实native batch，下一步不是“首次batch”；旧无工件complete/full/tangent模式不是本次固定工件chunk256短路径的直接成本依据。本轮只补已准备两LF输入的实际消费；不详细安排两个25目标循环。首个终端非success停止后续案例，原controller内部回溯／二分依旧settings；不外部重试、修复重跑、延期、force或借用旧资源窗口。
