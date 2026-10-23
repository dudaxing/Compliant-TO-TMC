# L-CTIPFREAL1研究包装实现说明

2026-10-23。只有研究层包装；57份已安装生产源码保持。本文件是启动前说明，不是运行通过证据。

`science_freal1.py`唯一调用现有evaluate_native_guided_force，从LOW1原父索引2输入两个绝对P，q不作为参数。父及参考科学包不复制或解压。Python审计钩子只约束NPZ open：原3档只读，新force目录允许write-only；它不替换HF或NumPy函数。记录实际read-capable open事件。若完整API返回，API已执行的冻结源码控制流证明geometry四mask＋父split两字段均解码；receipt明确这是控制流推定，未声称动态监视各字段。未返回时不补造F/T或字段计数。on_accept只保存普通进度标量，不做新F/T。

`compare_freal1.py`在科学PASS和清理通过后唯一执行，4个state NPZ各一次原字节读取/hash，再BytesIO解码两字段，记录实际4档／8字段；所有29970DOF四项fsum差、锚点位身份、q／全场／R门及各接受态原门和新g门独立记录。不读fields、旧F/T或矩阵，不修改原result。分量／账本重组仅描述，不设新的浮点门。

`view_freal1.py`只读四普通JSON，成功后一次5PNG／N帧实际GIF，真实几何×1，全部内部态保留。仅新positions计算尖端到原body边段无符号最近距离、右480介质几何；J/Hu只有全局已有标量，无局部场图。图中精确0显示地板不改原值。root只查看每张新PNG一次；不打开旧媒体或新GIF。

连续时钟与保留余量：API控制器1800秒；科学process1885＋清理／receipt余15，总≤1900。比较process45＋余15，总≤60。viewer process510，清理及5图root检查共享600；root QA在显示585秒之前结束。helper所有内容在2600秒前返回，outer拥有该完整helper Job并于top原2630秒绝对deadline前停止等待（原SUP2清理仍受总窗约束）。顶层确认全部3子任务及整个helper的四份同实例清理证明后，才在原helper2645之前进入唯一原字节封存，members2680、archive identity2690、全部2700／outer2760之前结束。没有数值窗口挪用、延期或第二次封存。

任一步非预期终端错误阻止后续科学／比较／显示；只有原窗口仍足额且整个helper树清理可证明，才唯一封存实际部分字节。无安装、修复重跑、外部重试或force。冻结前修正只属于源码写作／静审，不是数值重试：曾统一renderer/helper的普通status字面量、将NPZ写限制收敛到新force目录、移除top对helper无用时钟模块导入；尚未启动任何候选。
