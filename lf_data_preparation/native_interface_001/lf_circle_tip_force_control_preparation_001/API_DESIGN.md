# 导向轴向力控：最薄接口与能力核查

2026-10-23。**API设计，未实现；下面不是可直接运行的调用。** 当前固定工件和位移探针均不支持给P求q。拟只新增两个生产模块和一份测试，不改旧task parser、默认CLI、native_response、原controller、原力核或切线。

```python
# 拟议签名，不是当前可导入的函数。
from hf_eval.native_guided_force import evaluate_native_guided_force, GuidedForceSettings

evaluate_native_guided_force(
    saved_result, selected_state_index,
    body_load_targets_half_N, output_directory,
    *, force_settings, time_limit_seconds=120.0, on_accept=None,
)
# force_settings = GuidedForceSettings(minimum_force_increment_half_N=...)
```

|输入|明确合同|
|---|---|
|saved_result／selected_state_index|完整成功fixed_rigid/load_only父任务的真实最后原目标峰；继承d_hold，不能选probe JSON或旧路径中间态|
|body_load_targets_half_N|一维有限有符号绝对半模型合外载N；至少两个，首个匹配fresh q0预载，后续严格递增；无q目标、full/half自动猜测或增量歧义|
|force_settings|新不可变设置，仅必填正有限minimum_force_increment_half_N；不提供另一套未绑定的旧数值默认值|
|time_limit_seconds|唯一新clock；其余原DisplacementSettings由父绑定；不得把其中minimum_increment/mm用作N步长|
|output_directory／callback|全新、在父树外；每实际接受态一次callback；来源只读，首错保存实际partial|

q可正可负，由reduced平衡解出；首版只支持这条有序增载，不支持卸载、循环、任意负向推进、probe保存态延伸或自动force-to-displacement fallback。这里“有符号载荷”不等于所有路径模式已实现。

## 文件与复用边界

|拟文件|最小职责|
|---|---|
|新增hf_repo/src/hf_eval/split_guided_force.py|GuidedForceSettings及(w_F,q,R)控制器、新g门／N二分／partial；复用split_average_measurement及一般LU，不复制通用进程管理器|
|新增hf_repo/src/hf_eval/native_guided_force.py|薄API；复用native_probe._admit的严格父身份准入、原NumPy力/切线、split及_npz缓存模式；新账本和独立schema|
|新增hf_repo/tests/test_native_guided_force.py|8个非参数化方法及全新16格共享fixture；不读旧科学缓存|

直接复用私有_admit是当前仓库内的窄选择；候选静审绑定其SHA。若三新增文件范围无法完成，先报告并修订计划，不能暗改旧辅助函数放宽准入。原free35、body-x4节点合并为一个q，加R后小模型reduced系统37未知；50DOF仍是原全场尺寸，不能把它写成37DOF新网格。

_linear_solve可将[dw_F,dq]看成其位移block，传reduced K与[b_F,0]，并保持R在最后。旧诊断target_displacement必须写真实d_hold/mm，另加target_force_half_N；不把P/N写入位移字段。mixed-unit backward error仅诊断，不替代分开的N/mm门。kernel仍按原split物理状态求力和实际非对称切线。

## 首态准入与保存

复用_admit逐项核父success／完整原目标／最后原峰、task与model来源、材料／网格／成员／支撑、原机制源码、两个split字段及有符号R；不读取旧力或矩阵当新证据。进入本轮力控以后，首目标P0必须由fresh F/T直接满足[起点与验收合同](TASK_SPEC.md)，不能在API内部把首目标替换为fresh Q，也不回放父加载。

新result拟schema为`hf-native-guided-force-1.0`，独立于native-mean／guided-probe。原native_response只适配native-mean，首版不伪装为该schema或给它自动升级关联能力。

最低保存字段：

- source／原parent_task和SHA、mechanics SHA、原模式／非clock设置及force_settings。
- force_task：d_hold、原body成员、绝对half N目标、+x方向、厚度／对称合同、anchor声明与fresh测量、q未知的运动合同。
- 每接受态：P_target_half_N、generalized_body_internal_force_half_N、g/S_P/bound、body_q_mm、input_mean_mm、R_input_N、原free/mean/global门、J/Hu、material／regularization／total ON-body、互斥外载账本。
- 原split两字段、实际positions、accepted state/fields归档身份、请求目标序号及内部二分标记；全部Newton／trials／linear诊断、失败记录及调用计数。

只保存本接受态缓存，save-time F/T=0；实际q与载荷各有单位字段。不得重命名旧d字段后混用N和mm。原父结果／资格保持，HP／纯压力／承载极限／释放／稳定性／HF5不随新schema自动变true。

## 错误与partial

|阶段|拟行为|
|---|---|
|非法新设置／载荷／输出|invalid_settings或invalid_input，清楚区分mm与N；拒绝覆盖原树|
|来源错／约束冲突|invalid_saved_state或constraint_conflict；来源反例在F/T前拒绝|
|fresh初态不平衡|initial_state_not_equilibrated，检查1后零修正／零接受态，不二分锚点|
|路径数值失败|保原singular_tangent／nonfinite／invalid_J／constraint_failure／newton_limit／backtracking_failed／time_limit等明确原因及新g值|
|缓存或门失败|persistence_failure或明确force_acceptance_failure；保实际已有文件，不自动回滚或补算|

新函数的内部回溯／N二分可在冻结上限内发生；外部不得用重复API调用冒充同一窗口续跑。不把“未找到静力平衡”包装成“释放成功”。未来真实任务应用位移限值与工程承载条件尚需另定；本接口先完成总力平衡功能。

细节来源见[独立接口核查](author/API_REVIEW.md)、[数学核查](author/MATH_REVIEW.md)及[审阅取舍](author/REVIEW_DECISIONS.md)。
