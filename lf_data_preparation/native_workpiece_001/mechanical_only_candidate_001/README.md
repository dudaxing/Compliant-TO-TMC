# F16显式NumPy机械量入口：新独立候选卡

整体目标仍是与LF优化解耦的HF正向评估器：普通几何与任务输入、非线性力和切线、平均驱动加载/卸载、工件反力及实际可视化；不加入优化、dmftd或MPM。本卡只解决返零F16的机械响应职责，尚不运行另一条平衡路径。

依据：原粗方循环003失败，Horner192完整候选也失败；独立诊断证明其首次DD下限失效位于辅助能量，原始三力及运动学有限但未获参考资格。能量不参与当前mean残量/Armijo或缓存机械切线。因此优先显式职责拆分，保留完整入口要求，而不继续任意扩大能量缩放。

新实现仅隔离运行：从main795的42件源码复制，基线核心7fff，只增加`batch_response_split_mechanical_numpy`和`assemble_split_mechanical_numpy`。私有`auxiliary_energy=False`跳过能量设置/计算/字段，保持全部原机械公式、必需DD pair/系数/运动学支撑、正J与finite门。默认完整NumPy/JAX仍计算能量并拒绝失效；原KERNEL_VERSION不变，机械候选单列MECHANICAL_KERNEL_VERSION。核心候选d5f7；不是失败Horner192候选1d18的延续。

机械响应只省`material_energy`，不合成零或NaN。新验证包明确`response_contract=split-numpy-mechanical-1.0`及`auxiliary_material_energy={status:not_evaluated,qualified:false,field_present:false}`。完整入口、旧native元数据/legacy/JAX/controller均不默改。

输入不变：原F16的16数组、split state9dbd、原27数组模型a2d6、3200cells/6642DOF/376fixed、1mm网格、固定正方形半工件。原端口方向保留；验证方向复用冻结全域dyadic witness（3072非零单元，fixed DOF0），覆盖旧26和新35失败单元。诊断选择不改变物理数据。

执行顺序：

1. 唯一unit阶段：原20测试文件不变；原3 primitive+2未选完整响应断言仅source身份适配；7项新机械合同测试。预计32，以实际收集为准。helper60/outer90秒，采样树8GiB。
2. 唯一candidate阶段：一次新机械完整三力与P/S/retained pairs；即时保存force_fields。一次缓存显式T，立即保存T。三次原B52补偿tensor-action消费、三完整非对称CSC及全部fixed行列；即时结果/原始输入/来源capsule保存。helper90/outer120秒，采样树8GiB。
3. 只有实际candidate terminal pass后：独立进程fresh HP80和HP120各一次，对比全部3200cells×三力/三Jv=19200局部门，全部6642DOF×三力/action/CSC-action=9全局门，以及614400个完整局部系数的CSC组装身份。helper180/outer210秒，采样树8GiB。HP独立公式附带analytic energy保存，但无candidate能量对比/能量资格。

原数学门不变：total force1e-11、total Jv1e-10、material/Hu各1e-9；HP80/120相互误差1e-40。Et20按原`1e-8*Et*max(|d|,1e-6)`派生当前返零floor2e-13N，component force分母为max自身参考norm,1e-12总scale)，Jv分母max自身norm,1e-10)。所有DD四项、CI2^-400..2^400与temporary界、tensor非对称性均保留。

所有阶段计时含导入、调用、保存与身份校验，采样进程树/peak_wset协作检查，不是OS硬限。阶段各一次、首错即停，无修复/重试/force/延时；依赖只能在上阶段真实终端结束通过后启动。余钟不复活旧卡。完整F16旧失效继续保持，T25输入未捕获，不能预判T25或卸载已解决。

只有新F16 mechanical F/T原门及独立后审通过后，才允许按原字节合入opt-in函数及7项focused测试；默认完整入口仍原合同。此后单独规划native mechanical持久化/控制器接入和新路径。单方向参考不是全部切线列、应力/能量HP或平衡/夹持压力资格。循环0.5mm的2态尚无freshHP；圆形、细网格及1/2/3mm新路径尚未执行。

本卡与原001启动失败、002完整F失败、独立范围诊断并列保存。它改变的是明确新增的可选响应职责，不放宽旧完整入口任何门。
