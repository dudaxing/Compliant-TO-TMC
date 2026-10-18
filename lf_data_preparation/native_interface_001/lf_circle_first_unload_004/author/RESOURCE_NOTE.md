# L-CUNLOAD4 实际资源说明

1.35→1.25 mm回程执行PASS，outer **397.7018694 s**（约6分38秒），helper 394.2738134 s，原SUP2清理verified。

**64 GiB采样RSS上限和四库16线程环境配置保持。** OMP、OpenBLAS、MKL、NumExpr的对应变量均为16；这不是整个进程硬限16线程，也不保证实际同时用16核。未设置affinity、改变CPU数学后端或启用GPU。64 GiB是允许上限，不是预分配；原viewer仍保留8 GiB内部门。

进程树采样峰值 **828624896 B（0.772 GiB）**。唯一普通资源快照位于根进程启动后368.544 s：数值进程PID63904有33线程、RSS459079680 B，累计CPU360.562500 s。按该进程创建到快照的367.643953 s计算，累计平均约 **0.980738个逻辑核当量**。这是单个快照时的累计比率，不是瞬时CPU占用，也不是已完成全程利用率或峰值；33个线程可能含多个库的线程池和空闲线程。

PID18932是Windows虚拟环境重定向根进程，数值工作在PID63904。根进程低CPU不能用于判断数值进程是否工作。

原生产计时：kernel_and_transfer **380.260448 s**，assembly **0.090682 s**，sparse_solve **1.184993 s**，controller total 381.728484 s；整体evaluation 381.809313 s。这些是producer原字段；all_assembly_attempts_wall包含相关工作，不能与其子项重复相加。kernel_and_transfer的名称不表示启用了GPU。

原记录F12／T7、平衡controller1、API/solve各开始和完成1次；新测试、默认安装和HP均0。此次与上一回程的位移增量及非线性工作量不同，未做同任务受控比较，不能据耗时差异判断线程配置加速或减速。

本说明只读已有helper、launcher、普通result计时、environment和1份资源快照。无新增遥测、GPU基准、测试、科学运行或载荷读取，既有收尾脚本未修改。
