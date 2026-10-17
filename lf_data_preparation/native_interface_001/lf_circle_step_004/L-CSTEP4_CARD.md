# L-CSTEP4：圆形工件1.25→1.35 mm保存态延伸

2026-10-17 Asia/Seoul。用户“请继续进行下一步”批准上一回复和已发布S3 NEXT_STEPS的明确建议。main基线df5398ba0903970e5f139d1679ee5f2cbc8f11d7，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git。本文件为执行前快照，尚未启动。

整体目标仍是普通LF几何进入独立HF/TMC非线性前向分析，逐步实现可检查的变形、作用力和卸载功能；HF不优化、不调用/安装dmftd，MPM暂不实现。S3新目标6检查/5线搜索全部接受/0失败二分，原门通过；min free-medium J=0.155533、unsigned最近边距0.163972 mm、最右尖端距3.104708 mm，Hu约占弱式工件Fy的81.3%。采用相同0.10 mm增量观察实际变化，不能预言接触或相同收敛成本。

父源lf_data_preparation/native_interface_001/lf_circle_step_003/run_001/wave_circle_step/result.json accepted1/global6/1.25 mm，stateSHA d5b74358bf076a7d858efd710e61cf31fa2f9ddb1648a7a488e2cbc299213fc5，R=0.21844194402663447 N；parent.continuation.selected_state为祖先1.15，不能误选。新完整任务[0,.25,.5,.75,1,1.15,1.25,1.35]，inputpeak1.35，实际child[1.25,1.35]/global6,7/child0,1；只更新四说明字段、追加目标和峰值，其余任务精确保持。

圆形半径9 mm、圆心(71,40) mm固定ux/uy；E1MPa/nu.3/plane strain/厚20mm、h.5mm、13440元素/27378DOF、gamma1e-6/alpha5e-7/Lr80mm及原支撑/对称/平均端口/mechanical/chunk256/port_projection保持。settings和原门精确继承，minimum_increment=.00625、max_bisections4、controller1800秒。默认HF源码和绘图实现不改，无新测试、HP或安装。

一次evaluate_native(None,newtask,newout,...saved_result=父result,selected_state_index=1,extend_path=True)，以fresh F/T先复核1.25 mm原lift/fluctuation、带符号R、原门及SHA/R身份，第一检查须接受，不复用旧力/T/矩阵，再求1.35。保relative residual1e-9、逐态constraint_bound系数1e-10、globalbalance1e-6、fixed fsum8e-11 mm和全部GP J>0；原内部回溯/二分允许，保全部实际接受态，不锁定仅两态。

成功后复用S1纯viewer和收敛投影，一次新进程生成4PNG、实际N帧GIF、逐态表和人工页，显示×1变形/全结构视觉镜像、R/qout、工件有符号材料/Hu/总Fx/Fy、unsigned最近梁段/尖端距离、分区J/Green/Hu、残差/约束界/线搜索/二分。镜像不加倍数值，qout非表面间隙；圆周法向变化，全局弱式Fy非圆周压力或有效夹持力。保原图例标题轻微重叠注记，不修图重绘。

旧科学输入仅父geometry.npz和selected001 split state.npz；准备只继承producer seal/stat，helper唯一窗口才打开。CREF1普通summary仅属祖先1.15参考，不是parent1.25或新态资格，不读其gzip/NPZ/媒体。viewer为原五源，解码1+2N新NPZ/27+18N字段，无切线解码；原helper窗口封存新输出，成功后四新PNG各最多一次像素检查，不另解码GIF。

一次controller1800/共享显示600/helper2700/outer2760秒（最多46分钟），采样8GiB。共享显示含binding/viewer/收敛/表/页，seal仍限helper。原SUP2 CPU-CLEAN1同实例终止、全成员覆盖、句柄释放及固定5秒清理在outer内保持。唯一启动，首个终端错误停止后续科学/显示并保真实partial；仅原窗口仍开时允许部分seal。无外部重试、修复重跑、延期、force、回滚或删除。

new_peak_reached/extended_segment_completed仅本子段；task_target/full_original/full_extended仍False、target_response=None，requested_endpoint_response为新1.35。未授全前缀重算、独立HP/全列切线、独立圆mask、压力/有效夹持/卸载/释放/稳定性/制造/HF5资格。包含实际记录、图表、资源/清理回执、后续决策、普通main推送及异目录恢复核对。首错如实闭卡，不静默改门或物理条件；下一步根据本次实际证据再定。
