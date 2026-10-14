# L-REF1 两关键保存态物理／数学范围审阅（未执行）

两态选择合理：新LF fine loading1.20 mm、source accepted/original index13覆盖强压缩峰值；unloading1.05 mm、index16覆盖材料作用显著减小而Hu仍存在的早期恢复转变区。此处不是同输入的加载／卸载配对，也不是完整释放试验。当前完整25态生产PASS与三图／25帧显示已完成，但没有独立HP资格。本轮仅普通JSON/源码读、AST和科学文件stat，没有新HP、F/T、构模、求解、测试或图。

| source/original index | leg | d mm | 原全域minJ | ON-lower total Fy N | material Fy N | Hu Fy N | 原有限tip-bottom mm |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 13 | loading | 1.2 | 3.775081792887928e-05 | 0.058511988483089014 | 0.057794579410338345 | 0.0007174090727506572 | 0.002767290909318376 |
| 16 | unloading | 1.05 | 0.000655968173824588 | 0.007747408704194823 | 0.006938503841861044 | 0.0008089048623337788 | 0.01103329834709399 |

以上为已保存原值，没有新差值、比例、force或积分。邻卸载index15/d1.10保存J=9.714643655993198e-05、Fy=0.023525771697494112；index17/d1.00保存J=0.033323534010771316、Fy=0.0027773810011731603。因此index16应称强压缩到恢复之间的转变区，不能写完全恢复、分离或有效释放。选择两种数值状态可验证本新拓扑及局部路径条件，不证明路径唯一性、滞回或参数／网格稳定性。

## 保持原数学与十五门

复用B850 CoreAudit.run_state与aa86 WorkpieceCycleAudit.workpiece_checks原字节及其11源依赖；只适配这个新已保存producer/task/model、selection和元数据。实际模型13440 cells／27378 DOF、fixed1546、free25832，原固定下半方体648 cells／703 nodes／1406 DOF。每态新HP80和HP120，全元素局部参考后以3000-digit Decimal／Inexact trap scatter回真实共享DOF，不是拆散的物理模型；无需重新构模或求平衡。

原三分量local/global force、同一个固定lift PORT方向total/material/Hu action、完整未对称CSC系数组装身份及该方向CSC/KKT自由force与mean action、独立平衡／约束／反力、固定工件有符号total/material/Hu合力、disjoint holding及镜像投影均保留。独立HP只覆盖一个PORT方向、deltaR=0；完整矩阵已实现／组装可核，不等于HP全列独立验证。原辅助材料energy仅参考归档，mechanical候选没有energy比较或资格。

十五门必须与M-PREF1字典全等；保留原force/component/action denominator及floor，不能改成bodyFy相对百分误差或因小量换容易指标。aa86 body_force采用原global component规模规则，因此通过只能确认这种既定规范下的弱式合力。负holding得到ON-body、半模与镜像推导保持，不能改成连续压力或有效夹持资格。

## 身份、索引和API边界

新result是zero-start完整路径，无continuation。source accepted index13/16恰为original index13/16；raw参考目录和run_state必须用真实13/16，不能enumerate为0/1：B850 index0硬要求零fluctuation和R=0。摘要可另存selected ordinal0/1用于排列，但不得把该排列误当原物理索引。top记录应保source accepted／original／stateSHA／leg／d，plot不把零起点叫旧续算child。

当前公开native_response._reference要求全部N态身份、2N HP和完整source声明。两点即使通过也仅2/25点参考，不能与原25态匹配或让accepted/full_path_reference_pass成为true。旧几何、alpha和旧参考不迁移；不修改原完整生产结果／producer false flags或放宽reader门。以后需要全路径参考须另明确范围。旧source era作为历史依据保留，新参考绑定实际L-FWD1 source/task/model/arrays来源。

## 资源与唯一最小图

拟helper900／outer960秒、采样8GiB可沿同规模旧两态4HP实际outer193.35030270001153秒、M-PREF1两态4HP178.64134569995804秒及单态2HP99.37017110001761秒作预算依据；这些是历史原值，不是本新状态计时预测或授权。whole helper必须覆盖导入、身份／flattened archive、4HP、全部门、2次工件投影、一次纯观察图、summary与seal。原HP.evaluate内部没有checkpoint，合作stop不能保证瞬时硬停止；实际child退出与原窗口条件仍必须核，不延期、force或重跑。成本源独立窄审由另agent记录，不新增试算。

最小图只需一个两面板参考误差PNG＋配套普通JSON，读取本次新accepted013/016 summary已有标量。沿原10项global三力／PORT三action／CSC／KKT自由action／HP残差／HP80-120 agreement，显示log10(原normalized_error/原limit)，exact0文字标识，不添加floor或新的gate。标题标source accepted、original、leg、d；完整stateSHA在配套JSON。说明一个PORT方向和原规范分母，不是bodyFy百分误差，也不是压力／全路径合格。已有三PNG／25帧变形图只引用原链接，不再绘制物理图或读取旧媒体。

本报告是源准备，具体卡发布恢复后仍需新的直接人类批准才能进行4HP和一次图。当前不制定下一大范围研究；先完成此两个关键点真实参考，再依据实际结果决定近期需求。

独立成本／原数学范围审阅已完成，见[COST_SCOPE_AUDIT.md](COST_SCOPE_AUDIT.md)与普通JSON；原actualreceipt量只作规划依据，不是新运行或授权。
