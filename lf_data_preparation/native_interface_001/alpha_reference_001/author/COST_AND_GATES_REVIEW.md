# 两态独立参考复用：成本与十五原门审阅

此次只读原M-REF2普通JSON与Python源码／AST，没有解码NPZ、读取gzip科学档案、HF导入、试算、HP、计时测试或正式仓库修改。新alpha两态尚无独立HP；旧alpha的结果不可移用为新资格。

## 原实际成本及预算依据

原M-REF2唯一完整24态／48HP80+120实际PASS：helper2067.204527899972秒，outer2068.5294668000424秒；helper采样RSS1390268416B，tree RSS1398767616B。原额度helper4500／outer4560秒、采样8GiB。13峰值1.20及14首次下降1.15的小summary分别记2次HP、13440元素、27378DOF，但没有逐态或逐HP耗时。实际24份小summary均没有elapsed／seconds／duration／timing字段；lifecycle仅保留全窗终态，源码record也没有逐态时钟。不能给出两态各自“实测耗时”。

新范围若严格为两个完整保存态、4次新HP，仍每态计算全部元素、全DOF散射、原力／方向切线／CSC／方程／工件检查。可以把“旧全窗耗时 × 2/24”仅作为规模启发式，不据此保证线性速度或删减原检查。单态全模型的峰值内存和两个精度结果仍需保留，RSS不可除以12。建议新具体卡可考虑helper900／outer960秒、采样8GiB的有界窗口；这只是基于既有完整窗口和缩小态数的保守规划提议，未授权、不是试算或精确预计。若未来超限应首错结束，不按旧窗口剩余额度续算或延期。

原checkpoint在HP前后、精确scatter每256元素、local gate每128元素及输出／lifecycle后检查。Decimal参考evaluate本身的元素循环没有stop检查，因此这仍是协作停止；一次HP可运行至下一检查点，必须记录真实elapsed，不能声称OS硬时限或force清理。

## 原十五门全部继承

| gate | 原值 |
|---|---|
| production_residual | 1e-9 |
| independent_residual | 1e-8 |
| force_evaluation | 1e-9 |
| average_constraint | 1e-10 |
| global_force_balance | 1e-6 |
| fixed_displacement_mm | 8e-11 |
| hp80_hp120 | 1e-40 |
| total_force | 1e-11 |
| material_force | 1e-9 |
| regularization_force | 1e-9 |
| total_tangent | 1e-10 |
| material_tangent | 1e-9 |
| regularization_tangent | 1e-9 |
| augmented_force_tangent | 1e-10 |
| augmented_constraint_tangent | 1e-10 |

B850原GATES、M-REF2协议和实际摘要完全相同。HP80／120、3000位精确散射与Inexact trap保持；总力全局scale与原残差floor、材料／Hu force的1e-12 component floor、切线action的1e-10 norm floor、KKT mean的1e-6 displacement floor等均沿原式。不选更容易的方向、标量工件百分比或新的门来替代原完整检查。

方向仍为实际五节点 `b_in/max(abs(b_in))`，fixed分量零、27378长、deltaR=0，实际port权重[1/8,1/4,1/4,1/4,1/8]。方向由未来获批读取实际模型生成并绑定，不在此次重新计算。总／材料／Hu力覆盖全部元素和真实DOF；切线是此单一PORT方向的独立解析action。保存全部860160系数与CSC组装身份检查，不等于所有切线列独立HP。KKT检验同方向free force＋spring与mean row，未测试其它方向或deltaR列。

同一HP全局力进一步核signed工件总／材料／Hu作用、去重holding分区、背景对称重叠、镜像和双侧幅值；工件比较的原denominator规则保持，不能把归一化误差称为工件标量的百分比。没有压力、有效夹持力、全切线列、网格稳定性、拒绝trial、解唯一性或HF5资格。

mechanical模式的辅助材料能量仍not_evaluated、qualified=false、field_present=false。独立解析材料能量只归档，不作candidate能量比较；Hu总残差不能偷换为总势能梯度来加虚功资格。

## 最小复用合同

原B850 `run_state(index,row)`的index0要求未变形／R0；child局部0是原1.20峰值，不能直接enumerate0/1重用该条件。用绑定原execution index13/14运行原methods，可保留原检查与raw accepted013／014目录。工件检查实际读`self.rows[-1]`，支持两条追加record，无需填假的已完成行。最终新增普通摘要可映射local index0/1并另存reference_execution_index13/14；原stateSHA、绝对d、row descriptor、目录与原目标关系须清楚绑定。该映射只改变报告索引，不修改15门或声称新的未变形origin。

M-REF2旧loader／run wrapper硬绑定alpha1e-6完整24态／48HP、production full success及旧任务，不能直接调用。新loader应针对已保存alpha5e-7两态、其原任务及continuation身份作最小输入／元数据适配；保留父NOT_PASS、segment成功与完整原路径未完成，明确仅这两态的参考范围。新具体候选／卡仍需源审与新直接批准，本报告不执行或给出数值通过结论。
