# L-CTIPAUNLOAD2：新α从1.05到1.00 mm继续卸载

2026-10-20（Asia/Seoul）。用户已明确批准按已发布计划实施并执行本卡；准备和有限静审通过后才唯一启动。准备、真实运行、数值门、图像检查及发布状态分别记录，不预写运行成功。

## 目标与依据

整体目标是独立HF读取普通LF几何，在一致任务下获得可恢复的非线性/TMC响应与工件作用，供外部研究层比较；HF不执行LF优化。新α=2.5e−7已从零完成13目标加载至1.06 mm，父峰值已有HP80/120及原十五门通过；AUNLOAD1随后完成首次1.06→1.05 mm卸载，原生产门和五图检查通过。

本卡只从成功1.05 mm保存态继续到1.00 mm。前次末态R=0.19075825359298318 N，工件下半模型总Fy=0.009628058927231453 N，介质minJ=0.0012518161249492532；未出现失败或二分。继续一个有限卸载步有助验证功能，不以同位移小差证明可逆性，也不因父峰值参考而给新态参考资格。

## 输入、物理及任务

- 正式Git根：`D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC`；main基线 `c8c3b1c69f36d8a93bfefbad3439c8dd33dbf755`；origin `https://github.com/dudaxing/Compliant-TO-TMC.git`。
- 外部作者目录：`D:/hf-native-workpiece-api-author-20261020/L_CTIPAUNLOAD2_preparation_001`；新增阶段 `lf_data_preparation/native_interface_001/lf_circle_tip_alpha_unload_002`。
- 父结果：`lf_data_preparation/native_interface_001/lf_circle_tip_alpha_unload_001/run_001/wave_circle_tip_alpha_unload1/result.json`。恢复accepted1/global13/raw leg unloading、d=1.05 mm，split状态身份 `e21cdc845dc3721bc32d9275f889f53e9b1560dcd7ca126a28ea8efa2254e2ee`，保原有符号R。
- 原同位移基线：ALPHA1 `run_001/view/wave_circle_tip_alpha1/summary.json` 第7行/global7/raw leg loading1.00 mm，状态身份 `77d9c615291d5856c0761f49a0e8686f7f71fbd81005d689631affc78ac81840`。仅普通JSON原值；不用旧α续算锚作替代。
- 仅两份旧科学输入：父source geometry NPZ四mask和selected state NPZ的lift/fluctuation两字段。准备仅继承producer SHA/大小并stat，不打开或重新hash这些NPZ；获批唯一helper内才核字节及必要解码。不读取旧model/force/tangent/matrix数组、科学gzip、CSV或旧媒体。

保持α=2.5e−7、固定圆形工件r9 mm/圆心(80,40) mm、right92 mm、Lr80 mm、下半域92×40 mm、h0.5 mm、14720单元/29970 DOF、厚20 mm、E1 MPa、ν0.3、plane strain、γ1e−6及所有原支撑、平均端口和对称条件。

task保持ordered_cycle及14目标前缀`[0,.25,.50,.75,.90,.95,.98,1.00,1.02,1.03,1.04,1.05,1.06,1.05]`，仅追加`1.00`形成15目标任务。全部其他task字段及四项metadata原样保留，`input.target_mm=1.06`。本次只执行suffix`[1.05,1.00]`、global13/14，不重放14目标前缀。本层不新增task_transition；原首次卸载转换保存在parent_continuation，其fresh-zero祖先的parent_continuation仍为None。

## 最小实施和验证

1. 薄适配既有同kind续算研究包装，固定任务、输入与源码绑定；独立有限静审后归档真实授权并freeze。默认HF源码、依赖和安装保持，不新加测试。
2. 唯一调用现有公开保存态延伸API：只恢复split与signedR，重新计算1.05锚F/T并核完整状态身份及bitwise R，再执行1.00 mm。旧力、矩阵、切线均不移植。
3. 保原生产验收：相对残差≤1e−9；原native均值约束尺度界、constraint_tolerance=1e−10；global force balance≤1e−6；fixed split≤8e−11 mm；J>0。原max_checks25、Armijo1e−4、max_backtracks12、max_bisections4、minimum_increment0.00625 mm及二进制比较保持。非clock设置完全相同，不沿用父峰值HP作为此态验收。
4. 仅成功后一次纯保存态viewer和原收敛投影生成4PNG+实际N帧GIF，再生成1张收敛PNG，总计5PNG。保所有实际内部回溯/二分与接受态，不硬写N=2。显示实际×1变形、输入R、工件total/material/Hu Fx/Fy、尖端/Q1距离、右侧介质及Newton/线搜/二分收敛。静态第二态、fields和right-medium取实际LAST1.00；真实argmax peak_index另存，不重标为祖先峰值。
5. 与ALPHA1 row7原加载1.00作原13项标量原值及有符号“卸载−加载”差表，保raw leg/global index/SHA；不插值、去重、计算新恢复率/能量或新增相等/单调/滞回门。q_out是加权端口位移，不是间隙；距离无符号，交叉/重叠及未测试包含分别保留。
6. 原helper窗口内封存实际输出。五张新PNG各最多一次原分辨率像素检查，GIF不额外解码，不重绘。原J均值与九点minJ、Hu Frobenius与maxabs component、右侧上裁剪与全480单元极值分别解释，不强令所有卸载量单调。
7. 结果有限独审、如实闭卡、更新既有7份入口说明并保旧后缀；main普通提交推送、远端main身份核对、同机异目录local Git对象fetch+ff-only恢复及发布回执归档。不称作另一机器独立复现。

## 资源与停止条件

|项目|唯一限制|
|---|---:|
|controller|1800秒|
|显示共享|600秒|
|helper（含核查/科学/显示/封存）|2700秒|
|outer（含清理）|2760秒，最多46分钟|
|进程树采样RSS|64 GiB|
|OMP/MKL/OpenBLAS/NumExpr|各上限16线程|
|原pure viewer内部|8 GiB，保持|

使用原CPU后端和SUP2同实例清理合同；线程配置不等于实测16核利用率。唯一启动，首个终端错误停止后续科学和显示，保真实partial；原helper窗口仍开放时可一次部分证据封存。原内部回溯和二分允许；无外部重试、修复重跑、延期、force、新HP、测试、默认HF源码/依赖改动、安装、API关联、删除或回滚。绑定失配也停止，不调物理、门或步长下限获得通过。

## 完成、解释与后续

成功只说明此次请求后缀完成。新child成功时target_reached/path_completed可为true；其未实际经过1.06，故loading_peak_reached应为false；task_target_executed/full原或新路径标志仍保持false。父成功、失败和参考历史均保留。本次不授完整卸载/循环、压力、有效夹持、释放、稳定性、α独立、网格/域宽收敛或HF5资格；保持下半模型有符号弱力，不镜像倍增为夹持力。

完成后依据真实力、J/Hu、距离和收敛决定下一个有限目标或先做定位；不预先授权完整卸载，也不例行重复HP。失败则先解释实际partial与失败类型，另作下一阶段计划。

对照源码：本卡`execute_step.py/launch_step.py`薄适配已有UNLOAD2同kind包装；viewer/收敛只改身份文字，保LAST算法；默认`hf_repo/src/hf_eval/native_resume.py/native_evaluate.py/split_displacement.py`原字节保持。SOURCE_REVIEW、protocol、真实授权、准备/执行/封存/QA/实际审阅/发布回执分别保存；静审不代替数值运行。
