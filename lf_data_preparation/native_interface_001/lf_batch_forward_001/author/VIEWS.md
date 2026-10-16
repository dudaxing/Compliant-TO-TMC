# L-BFWD1：最小保存态显示与批量人工页方案

只读准备；基线 main ff448447a135d31314f7a0bd88e6ddd8ed449bfb。未执行/import候选、求解、测试或绘图，未读取NPZ、PNG、GIF、gzip或CSV。此文不是执行回执，也不续用L-BPREP1的窗口。

## 最小选择

推荐一次原pure viewer同时传两个 --case：它已原生支持多例，不必对每例各开一次、生成重复的三张PNG。两例均有三个接受态时，最小原样输出为三张双行PNG、两份各三帧GIF；另外复用既有普通result收敛函数每例一次，目标共五张PNG、两份GIF。源入口没有关闭某张PNG的参数，因此再减图需要改viewer，不建议本轮做。

三张原图是 comparison.png（每例实际峰值、last、局部及反力/三力）、distances_forces.png（有限距离/首射线和Fx）、peak_fields.png（每例实体Green应变、自由介质J/Hu）。两例在同次viewer内共享力箭头尺度、视窗和峰值场色标；不用合成或重画旧媒体。短加载的peak只是实际最大接受d，成功时0.50mm；peak与last是同一保存态，不是两次独立计算，也不是原1.20mm循环峰值。

现有收敛函数无title/label参数：third_cycle源码标题硬编码“Third LF gripper full cycle”，pilot源码硬编码“Third LF gripper pilot”。最终拟卡范围采用研究层收敛副本，只参数化label/title，保原JSON投影、残差/分组/坐标数据逻辑；原HF、已封存收敛源和pure viewer不改。副本最终源码及接口在实施后冻结；本记录不把两张收敛PNG记成已生成或已验证。

## 真实入口和参数

- 原viewer：functional_views/right_margin4_20261007/complete_001/saved_right_margin_views.py，SHA 761a9ffd1512233ce048be364c00a86882b69e2fb3e3fe81d7f79f74ad52b166。56–61行CLI；103–149行保存态观察；154–194行三图/GIF；201–211行完整view.json。
- 必须另起干净Python子进程，不能在已导入生产HF的batch进程内import/main。92–100行核完整允许模块集合；生产进程已含native_mean等，会违背这个纯读取合同。
- --repo 指formalroot/hf_repo，不是formalroot；--output必须是formalroot内的全新目录。两个--case分别使用 gripper_native_fine=新result目录、gripper_wave_fine=新result目录。--protocol使用新view_protocol.json；--stop-file使用本阶段stop_requested.txt；--time-limit取600秒和剩余helper窗口的较小值。
- 不传--reference。旧两态HP不转给新生产目录，新两例也未授权新HP；reference_available保持false。
- 收敛复用基础：lf_data_preparation/native_interface_001/lf_third_cycle_001/plot_convergence.py::plot_convergence(result_file, output_dir, checkpoint)。研究层副本仅增加label/title显示参数；每次只读新result普通JSON，写一JSON/一PNG，要求output_dir全新。不可在同一路径覆盖或因画图失败修复重跑。

建议新运行根为 lf_data_preparation/native_interface_001/lf_batch_forward_001/run_001，最终由本轮协议固定；viewer输出view/，收敛分convergence/000与001。这些是拟用路径，当前不存在任何本轮图或新结果。L-BPREP1的原25目标task与batch_manifest保持原字节；短加载task及其新case输出路径必须另建在新stage，不能直接执行指向旧准备run_001/evaluations的原清单。

## 读取集合和数量

viewer只读本次新result/model/逐态descriptor及其新model/state/forces NPZ，不读旧geometry NPZ、旧状态、每态matrix、科学gzip、旧媒体或HP档案。纯源码绑定沿原六文件闭包：viewer本身、measure_native_workpiece_regions.py、hf_eval/__init__.py、boundary_geometry.py、native_region_geometry.py、workpiece_nodal.py。

每例N个接受态：1+2N个不同NPZ，27+18N个解码字段；state有2字段、forces有16字段。两例N=3时合计14个新NPZ、162字段，geometry/nodal各6次，GIF分别3帧。内部二分导致N增加时，按实际N计算，不能硬写仍是6态。

h0.5当前网格的维度依据来自旧普通model/state声明，未开旧NPZ：13689节点、13440单元、27378DOF、9积分点；coordinates=[13689,2]、connectivity=[13440,4]、edofs=[13440,8]；state lift/fluctuation均[27378]；forces中J=[13440,9]、F及两个Piola=[13440,9,2,2]、Hu=[13440,2,2,2]、局部三力=[13440,8]、全局/约束力向量=[27378]。fixed/free/solid_nodes等长度随拓扑变化，必须据新声明记录，不强求两例相等。完整27/2/16字段集合见VIEWS.json。

14是不同文件数，不是14次payload读取。原viewer若沿既有协议把全部新NPZ也列入bindings，则每个archive经过协议预hash、archive内hash、一次np.load解码、末尾hash复核；不能声称每文件只读一次。新GIF帧数检查及新媒体原窗口seal也保留；封窗后仅stat/原seal，不另解码或重画。

## 批量页和失败策略

人工页只读新batch index、每例response/result、viewer summary/view.json及收敛JSON，保manifest顺序，显示status、failure/reason、requested/reached targets、接受态数、原目标/leg、R/q_out、固定下半工件total/material/Hu作用及几何观察。嵌入上述新图，分别链接真实GIF及各result/response；不另画第三份比较图，不读CSV回填。

最终拟卡采用严格首错停：现有native_batch.py:197–223在首个non-success后停止、后例not_run。
1. 仅两例batch全部success才启动一次双例viewer、随后两次收敛投影和人工页。任何batch typed失败、stopped/error或CLI nonzero均不启动viewer/收敛；即使已有首例success或当前partial，也不在本卡补画。
2. 保实际partial和后例not_run，以及真实failure/原目标身份，不填零力、零间隙、不借历史图。仅原窗口仍开放时按本卡规则封存已有实际文件；partial后续观察需要另行范围，不能自动开启窗口。
3. 资源/中断窗口关闭即停止新增显示；若viewer自身身份/几何检查失败，保存其failed view.json和实际部分输出，停止后续收敛/人工页，不跳过错误态重新开viewer。
4. 成功路径的人工页显示真实两例success/三原目标及实际接受态数；失败记录属于收据/partial事实，不生成伪装成功的带图页面。

## 成本和资源建议

普通历史收据支持：L-PILOT1第三wave三态viewer子进程16.3515803秒，viewer自身15.7928676秒/217104384B；该pilot整体1013.6499084秒、树峰848691200B。旧fine完整路径的0.50mm接受进度在1116.1646733秒，属于较长任务的前缀elapsed，不能当作新短任务独立计时。25态fine/wave viewer子进程分别48.9813279/43.9884247秒，各51 NPZ/477字段。

最终拟卡资源：每例controller1800秒，helper4500／outer4560秒，采样8GiB。显示阶段共享600秒，包含一次双例原viewer、两次普通JSON收敛投影、人工页及显示封存；原viewer的--time-limit必须受该显示阶段剩余时间和helper剩余时间共同限制，不能先用满600秒再额外给收敛/页面时钟。其余300秒为imports、生产保存及一般封存预留，实际操作不重复计时。SUP2清理按原合同计入outer，全部仍在唯一新窗口。

8GiB沿既有生产范围更有依据，不能把BPREP1的180/240秒、1GiB数据准备授权沿用给真实求解。两个controller上限和历史成本不保证总耗时或收敛。本文件只记录拟卡范围，不是执行批准，也未开始本次计算。

## 不授予的含义

本步只有0→0.25→0.50mm加载，不是完整25目标、1.20mm夹持或卸载试验。q_out不是间隙；节点窗口、有限射线、tip无符号距离分开；非零固定体弱式力不证明接触。保持制造pending、无新独参、pressure/effective-clamp/release/stability/HF5及排名均false。镜像只是显示，完整工件净力与双侧法向幅值和分别保留。
