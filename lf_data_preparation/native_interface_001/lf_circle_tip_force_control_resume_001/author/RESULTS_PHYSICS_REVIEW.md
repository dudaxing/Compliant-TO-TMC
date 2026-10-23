# L-CTIPFRESUME1 结果物理与功能独立复核

结论：**12项普通结果一致性复核通过。力控保存态两次续载功能在获批16单元/50DOF模型验证通过；不扩为正式r9或独立HP资格。**

|项|实际结果|解释|
|---|---|---|
|R01 唯一有限验证与资源|{"pytest_methods":12,"pytest_xml_seconds":9.611,"real_paths":7,"finite_calls":37,"top_seconds":69.89382160000969,"helper_seconds":68.46430779999355}|7真实路径包括固定父、给q参考、4条成功force段及1条预定partial；方法数/路径数/有限注入数分开|
|R02 新结果身份与期望分支|{"reference":{"schema":"hf-native-guided-probe-1.0","status":"success","accepted":4},"direct":{"schema":"hf-native-guided-force-1.0","status":"success","accepted":4},"prefix":{"schema":"hf-native-guided-force-1.0","status":"success","accepted":2},"child":{"schema":"hf-native-guided-force-1.1","status":"success","accepted":2},"grandchild":{"schema":"hf-native-guided-force-1.1","status":"success","accepted":2},"partial":{"schema":"hf-native-guided-force-1.1","status":"failed","accepted":1}}|只复核新普通JSON与raw身份；不重新读取已验证科学缓存|
|R03 两次非零fresh身份|fresh绝对q=0.00012499999997504744／0.00024999999997505273 mm；q/P/R bits、两split field SHA相同，checks1|普通记录与原唯一运行测试相符：q/P/R binary64、两个split字段SHA和state hash继承，checks1且锚点无修正解；本审不再解码数组|
|R04 有符号载荷与根尺度|{"targets_half_N":[-3.216587387036128e-08,-2.4215824481779638e-08,-1.6275064208362818e-08,-4.213649168822395e-10],"root_P0_N":-3.216587387036128e-08,"SP_all_force_states_N":3.216587387036128e-08,"Ffloor_half_N":1.0000000000000001e-11}|负P严格递增是靠近零；SP保持根P0，绝对q和根/段增量不混用。half-N已含t2；完整对称轴向2P、q不倍增|
|R05 设置、完整任务和迁移继承|{"nonclock_unchanged":true,"minimum_mm_step":3.125e-05,"minimum_force_step_half_N":4.962975170885513e-10,"global_offsets":[1,2],"same_byte_fixed_tree_relocation":true}|仅新clock可变；同字节固定树显式迁移一次，第二续载默认解析已记录位置；只算新增段，不宣称重算历史|
|R06 同P交叉比较与给q参考分开|6对direct-chain三误差全0；10对给q参考max q/全场3.987103616e−13 mm，max R2.981555974e−19 N|6对分段/direct完全相同；10对给q参考最大q/全50DOF差3.9871e-13mm、R2.9816e-19N；这些是原功能比较界，不是HP或稳定性证明|
|R07 原生产门实际状态|{"force_accepted_states":11,"max_rho_F":7.846037227196187e-10,"max_rho_P":7.851719743963634e-10,"max_mean_residual_mm":2.710505431213761e-20,"minimum_J":0.9987437160016815,"max_abs_Hu_per_mm":0.002047076083532272,"max_global_relative_balance":1.6462876278820464e-11,"max_rigid_zero_error_mm":0.0}|11个force接受态普通摘要原门全过；不从普通摘要重构局部场，不新增门或升级资格|
|R08 预定partial语义|{"failure_code":"constraint_failure","T_attempted":2,"T_completed":1,"accepted_anchor":1,"q_mm":0.00012499999997504744,"rollback_bitwise_equal":true}|预定第二T注入constraint_failure；仅证明保存/回滚正确，不是物理失稳载荷或可重试错误|
|R09 真实路径F/T尝试/完成与资格|{"force_calls":38,"force_calls_completed":38,"tangent_calls":28,"tangent_calls_completed":27,"solver_invocations":7,"HP_calls":0}|仅7真实路径计数，不把有限代数fake assembler计为物理核。save-time F/T0，HP0；原false资格不升级，未执行正式r9|
|R10 读取与复制实际口径|533 read-capable opens／93 NPZ paths；49 own-state验证、98 source-inferred字段；12copies／72files／56NPZ／861048 B|audit是本RUN新NPZ读能力open观察，含hash/复制/w+等，不是动态字段读取数；98只来自49次自有state验证×2源码控制流，非整个测试总字段数。12copy/72文件出现/56NPZ出现/861048B|
|R11 已安装源码实字节|{"source_files":58,"old_files_unchanged":55,"replaced":2,"new":1,"installed":[{"name":"split_guided_force.py","sha256":"8e902a20e7131733678b5b99aaa9bc5d046323ef151dd73f0681f18198e5dc1f"},{"name":"native_guided_force.py","sha256":"3995cc0afc04907bfa650f1d01af3c93288a3c5fa17243b6536c530dd9fa4daf"},{"name":"native_guided_force_resume.py","sha256":"8455e3aad3de2fed517033f3a715c1a69dd0b41f5c0476a96138290817b230b7"}]}|正式磁盘三个安装SHA等于已测试pin，其他55源实hash保持；不导入新模块或复跑|
|R12 清理、一次显示与封存回执|四层清理PASS；QA在display+50.553095 s；shared50.678642 s；1PNG／17base／6trials；封存1441228 B／226成员|四层同实例清理全部通过；显示原检查回执准时且只一次。封存只查已有普通回执，不打开archive或媒体、不重新封存|

## 证据边界

- 本复核仅读取新普通JSON/XML和已安装.py原字节；未导入HF、读科学NPZ/ZIP/媒体、执行F/T/HP/测试、绘图或第二次像素检查。
- split原字节和全DOF差由原唯一窗口的实际验证证明，本审只对其普通字段SHA/测试结果与预先门交叉核对，不宣称重新独立解码。
- 小模型功能通过不证明正式r9承载、压力、极限、稳定性、释放或独立HP；真实续载还需单独准备并冻结载荷/资源。
- 图像可视性沿已通过QA的三项限制保留；本审没有重开图像。
