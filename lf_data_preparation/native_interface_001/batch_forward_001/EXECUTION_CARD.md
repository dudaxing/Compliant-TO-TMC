# 两例真实 batch 执行卡

目标：用当前薄 batch 一次顺序计算 canonical 与 native_fine 原0.025 mm无工件任务，验证同一物理声明下实际构模、求解、缓存保存、response和index。HF读取原LF普通几何；不优化、不调用LF或dmftd。

输入：production_protocol.json所绑定的28个当前HF源、manifest、两份原task、geometry.json/npz以及门槛/成本来源。两设计的原生网格分别h1和h0.5；它们不是同设计细化。各例零lift/未变形开始，目标0、0.005、0.010、0.025 mm，最小增量6.25e-5 mm，complete/full/tangent保持。

执行：全批JSON预检后各例一次；继承既有controller、真实力和切线、cached writer与formatter。仅插入阶段计数、前后资源检查和原capture后的标量进度；保留原固定DOF缓存门检查。保存不得新增F/T，不持有前例大缓存进入后一例；每例API返回后单次垃圾回收清理不可达controller递归闭包，计入本段时间。原门包括production residual1e-9、原约束bound、J>0、global balance1e-6、fixed8e-11 mm。独参门仅记录。

预算：一次连续whole-helper2400秒、外层2460秒、8 GiB采样RSS；共享controller1800秒是每例求解限额，不能代替全段时钟。旧两例生产约176.48和1099.22秒仅作成本背景。合作停止/采样内存，不宣称OS硬限制，不force、不重试、不借旧卡剩余额度。

完成：两例各自原目标到达，真实delegate计数和F/T与结果对账，原生产门通过，缓存保存0额外F/T，source/input hashes不变，response与batch index身份一致。保留每例真实状态数、失败和last accepted，不能用旧14F/9T猜测新迭代次数。

停止：首非success、输入/source改变、资源越限或包装异常即结束。原已保存失败/partial不改写；资源异常继续传播，可能只留下标量接受前缀及interrupted index。不得修复后重开本卡。

输出：run_001下每例result/response、batch/index、accepted_progress.jsonl与执行回执。独立参考和实际状态图另按实际N冻结新阶段；本卡不生成图，不授予接触/压力、网格收敛、排名或HF5资格。
