# L-CSTEP2：圆形工件保存态1.00→1.15 mm执行卡（待授权）

2026-10-17 Asia/Seoul。仅外部准备候选；新科学执行0次，正式仓库及冻结输出未修改。本卡不是授权文件。main基线 `a3e444dc106cd79123cd5455f623d54dc7b43628`，origin为https://github.com/dudaxing/Compliant-TO-TMC.git。

## 目标、依据及固定任务

整体目标仍为普通LF几何进入独立HF的TMC正向力学，取得可比较的实际变形与接触相关响应，供外部研究层使用；HF不优化、不导入/安装/调用dmftd，MPM暂不实现。原near_rotation诊断及旧版本资格不因本卡重开或转移。

L-CSTEP1的1.00 mm加载成功：新目标7检查、含锚点共8；6次线搜索全部接受，0失败/二分；耗时494.16秒。自由介质minJ由0.501097降至0.329300，最小Q1边界无符号距离由0.504374降至0.334737 mm。因此本次建议把请求增量由0.25缩至0.15 mm，观察更强压缩区间；这是采样选择，不是新门或收敛/稳定性预测。

唯一新目标1.15 mm。来源 `lf_data_preparation/native_interface_001/lf_circle_step_001/run_001/wave_circle_step/result.json`，accepted1/global4/d1.00，state SHA `8eca12177e50cecf8fc47c4668e19c34109a21965b21d62d9e262eb9459b3f06`，原带符号R=0.17334986866494886 N。不能误用其continuation里保存的0.75 mm祖锚。新完整task为[0,.25,.5,.75,1,1.15]、input.target_mm=1.15，实际子段仅[1,1.15]、global4/5、child0/1。仅四说明字段、追加目标及输入峰值变化，其余任务精确相同。

固定圆形r9/c(71,40) mm，ux/uy固定；E1 MPa、nu.3、plane strain、厚20 mm、h.5 mm、13440单元/27378DOF、gamma1e-6/alpha5e-7/Lr80 mm、原支撑/平均端口/对称保持。mechanical/chunk256/port_projection、原非clock设置（显式minimum_increment=.00625）保持。

## 唯一执行及原门

复用已安装evaluate_native(None,newtask,newout,repo_root=ROOT,saved_result=上述父result,selected_state_index=1,extend_path=True,settings=原DisplacementSettings,**原options)。先以fresh F/T对1.00 mm锚点第一次检查即通过，保持原state SHA和R字节身份，再推进1.15。无旧力/切线/矩阵读取、无新测试/HP/默认安装，默认HF及绘图实现不改。

包装仅更新新stage、父/祖层身份、目标与元数据绑定；授权包装由旧请求逐字比较改为本卡approval_card与非空实际人类原话，并保持原授权bool、protocol SHA、BASE/HEAD绑定。当前不生成授权文件；只有收到新的人类批准后才记录原话、冻结并使用本卡。该调整不更改科学验收。

保持relative residual1e-9、每态原constraint_bound（系数1e-10）、global force balance1e-6、fixed split fsum8e-11 mm、全部积分点J>0。原内部回溯/有界二分允许，保留全部实际接受态，不锁定两态。new_peak_reached/extended_segment_completed可真，task_target_executed/full_original_path_completed/full_extended_path_completed保持假，target_response仍None、requested_endpoint_response=1.15。保留所有原结果和失败历史。

## 记录与可视化

成功后一次新进程纯保存态viewer，加一次普通JSON收敛投影：4PNG、实际N帧GIF、逐态表与人工页。包含实际×1变形/全结构镜像、输入R/q_out、下半工件Fx/Fy及材料/Hu分解、unsigned边界距离与尖端距离、分区J/局部场、残差/约束界/线搜索/二分。镜像不加倍数值。保留现有图例/标题轻微重叠，不为本卡改变绘图源码。

旧科学读集只含父source_geometry geometry.npz和accepted001 state.npz（lift/fluctuation）；准备继承原producer SHA＋stat，不打开数组。新viewer只读自身模型/状态/力1+2N份NPZ、27+18N字段，不解码切线；全输出在原helper窗口内封存。成功后四个新PNG各最多一次像素检查；GIF帧数取原viewer回执，不额外解码。

## 资源、完成与停止

一次controller1800秒；显示共享600秒；helper2700秒、outer2760秒（最多46分钟）、采样8 GiB。共享显示包含binding/viewer/收敛/表/人工页，全输出封存仍限helper。原SUP2同实例终止/全成员覆盖/句柄释放合同与5秒清理在outer内保持。原494秒成本是预算参考，不保证新压缩态耗时。

唯一启动，首个终端错误停止后续科学/显示，保真实partial，仅原窗口仍开放时允许部分封存。无外部重试、修复重跑、延期、force、回滚或删除。完成条件为锚点复核、1.15接受、原门、实际显示/资源/清理及记录齐全；未完成项如实保留，不改写失败为成功。

包括实际结果/局限/下一步记录、普通main提交推送及异目录恢复核对。当前准备不提交推送。若获授权后静审发现需改变科学源码、物理、原门或资源，本卡停止在执行前，不能静默扩大。

## 解释边界与后续粗路线

1.00 mm时尖端距raster工件边界仍3.349195 mm；真正最近位置不是尖端。下半Fy=.000949441 N中Hu约81.13%，这是弱式传力，不是圆周压力或有效夹持；正unsigned距离下可有TMC传力，不以等待边界相交作接触判据。完整包含/自重叠未检查状态继续保留。

只授本子段范围，不授完整前缀/原25目标循环、独立HP、连续压力、有效夹持、卸载/自由释放、稳定性、制造或HF5资格。后续按实际几何/介质压缩/力/收敛选择继续加载、必要的参数诊断或选定态独立参考，再安排卸载与同定义比较；不在本卡预定更远目标或批量标签。

候选输入：step_task.json；协议：protocol.proposed.json；静态包装：execute_step.py、launch_step.py。来源：已发布L-CSTEP1 RESULTS/NEXT_STEPS和原普通result/producer seals。独立静审回执在本准备目录，只有静审无阻断且新授权到达后方可进入新执行窗口。
