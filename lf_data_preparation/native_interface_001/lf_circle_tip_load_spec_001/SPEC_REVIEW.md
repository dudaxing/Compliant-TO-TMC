# L-CTIPLOADSPEC1：独立数学与物理规格审阅

2026-10-22。审阅者 `/root/loadspec_independent_review`。**结论：规格与下一最小范围自洽，12项查核通过；实现、数值验证和真实探针均未执行。** 这不是新机械PASS或承载资格。

审阅最终候选：

- `PHYSICAL_TASK_SPEC.md` SHA `216ae09a4a3e4c2d07b6a47273b747ac27d9d1f2f08e7d5287303cfa59be8f86`。
- `NEXT_IMPLEMENTATION_CARD.md` SHA `50dcee88fbc05901bbf2c11f889885f8443c4842ae2a3c42f696326a8f4ba21e`。

|项|实际查核|结论|依据与含义|
|---|---|---|---|
|R01|运动与控制|通过|全部原工件节点 ux=q、uy=0 与 theta=0 是同一导向刚体平移；机构仅平均输入保持1.06，不锁死各输入节点。|
|R02|消元与独立路径|通过|给定 body q 消元后仍为一条输入平均约束；Newton 的单边框KKT及 predictor [-(K deltaL)_F,-b_in^T deltaL] 符号正确，不把 q 增量加到 d_hold。|
|R03|刚体成员与边界|通过|成员冻结，不通过解锁原介质节点或重新mask替代刚体；body/port及不相容支撑冲突拒绝。原y对称与+x运动相容。|
|R04|作用力与驱动符号|通过|ON-body=-sum_B fint，prescribed probe drive=+sum_B fint；负Q是制动而非数值失败。保q0预载及signed增量，不abs或截零。|
|R05|半模型虚功口径|通过|同一q在两半相同，完整轴向力为2倍半模型；完整外载进入半模型时除2。t20已计入N，不另乘厚度，不把2|Fy|当轴向承载。|
|R06|反力账本|通过|body ux、body uy及其余固定DOF互斥，body uy/背景对称交集只计一次；不将原全support向量与body drive再次相加。|
|R07|新任务状态准入|通过|旧固定峰只作显式新任务初猜。q0须fresh F/T及平衡核验，不自动Newton修复、不改普通resume物理合同、不迁移旧矩阵或旧HP资格。|
|R08|门层级与移动约束|通过|分清controller残差/mean/J、研究wrapper global/fixed以及独立HP15门；body改核ux-q而非强制ux=0。归一化仍基于d_hold，真实minstep=.00625来源明确。|
|R09|实际坐标与矩|通过|新记录必须使用实际body X+q，保split两数组；新矩若提供，以实际中心(80+q,40)定义且不覆盖旧矩。示意图不冒充数值变形。|
|R10|有限域解释|通过|89.25节点上界由单元中心入圆及半单元宽推得，89.275与2.725只是参考几何保守界；未冒称实际bbox或变形间距，真实前仍须绑定bbox和DOF。右域界不是新增刚墙。|
|R11|成功与失败含义|通过|规格完成、功能通过、真实probe数值完成与承载/释放资格分离。0.025是驱动范围；Q>0、非收敛、零模、低J均未被当有效夹持或释放。|
|R12|后续最小范围|通过|NEXT卡仅安排opt-in候选、小模型六类行为与一图；不包括真实probe、HP、force-control、通用MPC或默认入口替换。fixture/唯一命令/次数/源码及资源需实施前冻结并静审。|

## 已消除的歧义

最终规格将Q—q图注改为“有符号原值和有符号增量”，避免误实施为abs(Q)；新矩若提供，使用实际刚体中心(80+q,40)，不覆盖旧报告原点或矩。消元单输入KKT、独立q predictor、反力互斥分区和旧门分层已逐项核对，没有发现需要首阶段增加第二乘子或通用MPC框架的理由。

## 尚未验证的部分

下一卡目前是实施范围，尚非已冻结源码/fixture/唯一命令/次数的执行包。实施前须冻结这些项目及资源窗口并静审。六类小模型行为没有实际结果；真实staircase bbox/边界DOF没有本轮数组证据，真实probe前必须另绑定。当前不能授予承载、释放、稳定性或新路径独立参考资格。

本审阅读取范围限两候选MD、既有审计/建议、选定源码和普通protocol JSON；原execute_step.py:217–227及protocol settings/gates已实际读核。未调用/import HF、F/T/HP、平衡或测试，未读NPZ/CSV/gzip/媒体，未写正式仓库或操作Git。一次rg字面glob路径无效后改精确文件读取，无代码或数据影响。**未检查示意PNG像素**，由root另记。其他审计员独立记录的范围偏差不被本审阅的零计数覆盖。

精确源文件身份、12项依据和待办见[SPEC_REVIEW.json](SPEC_REVIEW.json)。
