# L-CUNLOAD5 实际资源说明

**唯一窗口已PASS并结束**：outer **3495.7050112 s**（约58分16秒），helper 3494.7855914 s，原SUP2清理verified。保存7个接受态，输入到0端点；原窗口完整seal为78输出／177255296 B。本说明不改变原结果或资格。

controller5400 s、共享显示600 s、helper6600 s、outer6660 s；采样RSS上限64 GiB，四库环境各16线程，原viewer内部8 GiB保持。**进程树采样峰值1095417856 B（1.020 GiB）**。许可64 GiB不是预分配；各库16不是总进程线程16的硬限，也不保证使用16核。无affinity、GPU或CPU数学后端更改。

仍只保留UTC 2026-10-18T07:17:38.331389+00:00 的唯一既有快照：数值PID68628累计CPU421.453125 s／age429.280869 s，约 **0.981765个逻辑核当量**；点RSS493043712 B、线程31。这个比率只累计到该快照，不是瞬时或完成全程利用率；线程可能包含多个库池和空闲线程。PID43056是venv重定向根，61136是conhost，不能用其低CPU代替数值进程。没有新增快照或GPU基准。

producer原墙钟分解以controller total **3468.094730 s** 为分母：

|原计时字段|秒|占controller total|
|---|---:|---:|
|kernel_and_transfer|3366.296884|97.0647%|
|assembly|0.829332|0.0239%|
|sparse_solve|12.796858|0.3690%|
|callback|0.127286|0.0037%|

整体evaluation为3468.174415 s，显示为13.703840 s。all_assembly_attempts_wall为3453.669595 s（99.5841%），包含相关kernel/assembly-attempt工作，不能与上表重复相加；这些计时也不是完整互斥分区。kernel_and_transfer沿用CPU实现原字段名，不表示GPU传输，以上均非CPU工时。

原计数：F开始87／完成83，T45／45，平衡controller1；45个Newton基点检查、42个trial中38接受／4拒绝、failed_attempts0、线性求解44、最大二分深度0。**零端点使用11次检查**，保留真实微量和原残差；不写成“所有trial接受”，根转达独立实际审阅已核明：4次拒绝均在零端点check7–10、全步factor1.0，reason为unsupported_arithmetic_range；原回溯处理成功，并非invalid_J或Armijo比较拒绝。F开始87／完成83的差4对应这些范围异常，不称全部F完成、无回溯或物理失稳。API/solve及原显示程序各调用一次，新测试、默认安装和HP均0。

此次含6个下降目标且靠近零端点，与此前单增量的N、迭代和工作量不同；没有同任务受控对照，不能据耗时或配置宣称速度提升。仅读普通JSON和原seal条目统计，未打开、哈希或解码NPZ、CSV或媒体，未新增遥测、科学或测试。
