# L-CTIPFLOADPREP1：力控接口与有限验证只读审阅

2026-10-23。审阅者 force_api_audit。本轮仅阅读源码、已有普通说明和测试定义，未导入 HF 模块、读取科学归档／图像、实现代码或执行测试。工作仓库为 `D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC`。

## 结论

当前可复用来源准入、原 NumPy 力与非对称切线、split 状态、缓存保存及有限小模型；当前不存在“给定工件合外载、求未知工件 q”的控制器。最薄可审查方案是新增显式 `evaluate_native_guided_force` 入口和专用 reduced 力控控制器，保持 `evaluate_native_guided_probe`、固定工件入口及既有任务 schema 不变。不能把 N 目标传给现有位移 targets，也不能通过外层反复调用位移探针、规定 q 后输出 Q 来声称已实现未知 q 力控。

实际 controller 是 `hf_repo/src/hf_eval/split_displacement.py`，不是 `native_controller.py`。以下接口仅为准备草案，尚无实现、运行许可或测试通过记录。

## 已核实的可复用部位与边界

|源码／定义|可复用内容|必须避免的误用|
|---|---|---|
|`native_probe.py:44` `_admit`|完整成功 fixed_rigid/load_only 原末峰值、模型／材料／几何／来源身份、两个原 split 字段、有符号 R、原设置和执行选项准入|当前只接纳固定父任务，不能把 probe JSON 当 native-mean 父来源；不能用旧显示位置重建 state|
|`native_probe.py:142` 现有 probe|fresh F/T、q0 原 state/R 一次检查、F/T 计数、同接受态缓存保存、body/zero 分区及组件力求和模式|当前 q 为指定量，`Q_drive_half_N` 为输出，body-x 仍属于原 fixed DOFs；这一语义不能移植后仍称 body-x 保持反力|
|`split_displacement.py:55` 控制器|原误差／Armijo／回溯／一般 LU 思路、split 补偿平均测量、first-anchor 不修正、partial 与历史诊断格式|`prescribed_body` 的参数 s 就是 q/mm，未知量只有 `(w_F,R)`；现有 `_kkt` 无 q 平衡行，不是力控 KKT|
|`displacement.py:24` 设置|原位移与 free 残差容差、检查次数、时限、回溯参数可明确继承|`minimum_increment` 的既有使用是 mm；真实任务 .00625 mm、类默认 .025/16 mm、小模型 PEAK/16 mm 是三种值，不能静默选一个当 N|
|`native_project.py:251,278–280`|原物理模型、厚度、`force_scale_per_length=E*thickness`、原 cell/node 成员|不重新 remask；不再次乘厚度；不把 overlay 替换成新材料刚体或修改右侧边界|
|`native_response.py:7,194`|普通 JSON 摘要的职责边界和清楚的身份／路径／资格字段习惯|该函数只接受 native-mean schema，不接受当前 guided-probe schema；新力控不得仅改 schema 字符串伪装 mean，也不在首版强行扩展默认摘要|
|`data.py:60` 附近 `canonical_hash`、`native_force._npz`|有限、稳定的元数据身份及缓存归档格式|只复用现有辅助函数，不新建通用序列化／兼容层|

## 建议的显式最小 API

```python
# 拟议名称；尚未安装，不可运行。
evaluate_native_guided_force(
    saved_result, selected_state_index,
    body_force_targets_half_N, output_directory,
    *, force_settings, time_limit_seconds, on_accept=None,
)
```

首版来源只接受完整成功固定工件 load_only 原末峰；`held_input_mean_mm`、材料、厚度、网格、成员、支撑及非 clock 原设置从父来源绑定，调用方不得再次覆盖。调用方传入**有符号绝对半模型合外载**，每个目标的单位都是 N、方向为工件 +x。首个目标必须等于新 fresh q0 反力所需的预载 P0；后续仅考虑本次最小正向增载，卸载／负目标／保存态延伸留待以后明确扩展。输出目录全新、位于父树外。

可采用两份新源码：`native_guided_force.py` 负责薄适配和缓存保存，`split_guided_force.py` 负责专用 `(w_F,q,R)` 路径与新 `GuidedForceSettings`；配一份 `tests/test_native_guided_force.py`，合计三份新增文件，首版不改旧源码、默认 CLI 或 native_response。这是候选边界，不是本轮安装清单。直接复用私有 `_admit` 在当前仓库内可行，可在候选中明确 pin 该源码；不为提前“通用化”而重写默认模块。实现阶段若确需调整私有辅助函数，应列出精确旧调用兼容测试再冻结，不能默认为无影响。

`GuidedForceSettings` 必须用 `minimum_force_increment_half_N` 等带单位字段表达新增载荷步长；旧 .00625 mm 保留为来源历史值，不参与力路径二分。原 held-mean、free-force、J、刚体／零支撑和全局平衡门保留；新增 generalized-force 门、归一化及 merit 必须明确写进新卡，不能声称它们已经属于原位移门。第一版可不承诺内部载荷二分；若包含，须冻结其 N 步长、最大深度和所有内部目标保存规则。

建议新设置对象只含必填 `minimum_force_increment_half_N`；其余数值参数从原 `DisplacementSettings` 绑定继承，包括 tolerance1e−9（在新卡中明确再用于新增力残差相对门）、检查／回溯／二分上限和 force-floor 公式，而不是拷贝出另一组默认值。原 `_linear_solve` 可在构好非对称 `(w_F,q,R)` 系统后复用：将 `[dw_F,dq]` 作为其 displacement block，传入相同形状的 reduced matrix 和 `[b_F,0]`。其诊断字段 `target_displacement` 必须保持实际 held d/mm 并另加 `target_force_half_N`，或在新结果改用清晰字段；不能把 P/N 填入含 displacement 的旧字段。该辅助函数的 mixed-unit backward error 仍只作诊断，不替代新原门。

## 非零预载与未知 q

原 q0 的 body-x 固定约束承受非零广义力。释放这个约束而保持 q0，必须施加同一 P0，而不是 0。真实低输入的已有普通结果提供候选载荷：

- P0_half = `3.686421133658022e-5 N`；
- P1_half = `4.3272306948756724e-5 N`；
- ΔP_half = `6.408095612176505e-6 N`。

这些是以后真实功能交叉检查的输入候选，**不是小模型载荷，也不是承载极限**。未来小模型必须重新生成自己的父任务和位移探针参考，并从新 q0／终点记录取得自己的 P0／P1。不能读取旧科学缓存冒充新小模型参考，也不把真实 .025 mm 与这两个载荷硬套到 2 mm 小域。

fresh q0 必须保原 lift／fluctuation 和 R 的字节身份，q=0，先做新 F/T，同时检查原 free 平衡、held mean、新 `sum_body f_int,x-P0`。失败直接 `initial_state_not_equilibrated`，不 projection／Newton 修正，也不把“从 P=0 再加载到 P0”当相同初态。只更改首载荷的反例应在 fresh F/T 后拒绝；来源身份反例则在 F/T 前拒绝，二者不能混计。

未来增载目标 P1 下 q 是解，不是输入或 Dirichlet 条件。刚体形状 `s` 在每个 body-x DOF 为 1，body-y 为 0，状态表示仍可用 `lift=q*s`、非 body 原自由 fluctuation；原 body fluctuation 保持零，q 通过额外广义平衡未知量求解。原 body-x 在 reduced 系统中不再是独立自由节点或零约束；不能同时给各 body-x 节点自由量再加 q 造成冗余。

载荷为半模型合力，已含来源厚度；全装配同向轴力 `P_full=2*P_half`，q 不倍增。不得将同一 P_half 施加到每个 body 节点，或用 body 节点平均弱力代替总和。导向装置仍保持 y=0／转角0，允许对应反力和力矩，因此本任务不是自由工件六自由度平衡，也不自动得到夹持极限。

## 保存、响应与失败语义

新 result 使用独立拟议 schema `hf-native-guided-force-1.0`。最小字段应包括：来源与源码身份、原 parent_task 保留、新 `force_task`、绝对 `body_force_targets_half_N`、新鲜 `anchor_P_half_N`、单位／方向／厚度／half 合同、每个接受态的 `P_half_N`、`body_q_mm`、`input_mean_mm`、`R_input_N`、`generalized_force_residual_half_N`、该项 scale/bound、原 free 残差与 held-mean 门、J／Hu、组件 `force_on_body_N`、新 external-load／guide／zero／actuator ledger、历史／trials／partial，以及缓存 state/fields 身份。

新增工件外载应进入全局外力账本。原 probe 的 `body_x_drive_N` 是规定 q 所需的保持／驱动力；新力控的同位置量是输入 `P_half_N`，不能仍当一个独立未知 support reaction 再与 P 相加。body-y 导向和其余 zero 支撑应互斥分区，overlap 不重复。节点力分布若无单独定义，只保存合外载／广义力和内力组件，不捏造唯一节点分载。

保存仅用本接受态真实缓存，无 save-time F/T。所有独立 HP、压力、有效夹持／释放、稳定性和承载极限资格维持 false。`target_reached` 只表示本次新力路径所有原目标通过。

建议失败码：输入／单位／非法目标为 `invalid_input`，不合法新设置 `invalid_settings`，来源身份 `invalid_saved_state`，约束交叉／秩冲突 `constraint_conflict`，fresh 初态 `initial_state_not_equilibrated`；数值沿用 `singular_tangent`、`nonfinite`、`invalid_J`、`constraint_failure`、`newton_limit`、`backtracking_failed`、`time_limit`、`persistence_failure`。新广义力门若是数值平衡未收敛，必须保留具体 residual/scale/bound，不用“已释放”包装失败。首次终端失败停止，保已接受态、最后原目标及失败目标；不得把非原二分态认成请求终点。

## 有限小模型验证建议

既有 `test_native_guided_probe.py:118` 的真实 fixture 为 4×4 Q1／16 单元／50 DOF，域 2×2 mm、厚度2 mm、PEAK=.0005 mm、位移 q=[0,.00025,.0005] mm，body 为 cell14、nodes[17,18,22,23]；原 free35、fixed15，body-y 与背景 y 对称有重叠。它在测试中生成新几何与新父任务，适合作本次**未来重生成**的基础。现有真实 fixture 使用默认 full tangent；若下一卡想核 chunk256，需明确增加该有限路径或更改新测试选项，不得声称自动覆盖。

建议按下列验证轴冻结唯一清单，最终测试方法数与真实路径调用数在候选写成后分别统计，不提前声称已完成：

1. **独立非对称代数 oracle**：构造小型非对称 K，显式独立 dense reduced 系统，输入 P0／P1，核 w、q、R；含非零预载，证明符号、求和、额外 q 列／行没有被对称化。特意设置双向 free/body 耦合 `K_Fq≠0`、`K_qF≠0` 且两者不互为转置；仅有旧位移 fixture 的单向 Kwq 耦合无法检查新增行。不是只和候选自己的组装函数比。
2. **总和与单位**：多 body 节点同一 q、节点数不改变总 P 口径；half/full 只换算一次，厚度通过模型积分一次。可在纯代数／元数据检查中检验，不需要为每种口径另跑真实路径。
3. **fresh 锚点**：原 state/R/q 字节不变、一次新 F/T 通过；错误 R、held mean、P0 分开拒绝，不执行线性修正或 backtracking。非法来源在 F/T 前拒绝。
4. **真实小模型交叉检验**：一次新固定父、一次新位移探针生成参考 Q(q)；新力控从同一父以新参考 P0/P1 求未知 q。核 body 刚性、held mean、原门与新增广义力门，不在力控输入里规定预期 q。
5. **组件／全局账本**：total=material+Hu 的有符号合力、外载 P+工件 ON-body Fx 的闭合、guide 与 zero 去重、整体外力平衡，检查 accepted 缓存与普通摘要一致。
6. **真实 partial 与持久化**：复用新生成小模型源，受控切线终端异常可验证仅保 anchor、原字节不变；这是注入持久化场景，不是实际物理奇异结果。save-time F/T 为零。
7. **输入／约束有限反例**：bool/complex/nonfinite、空目标、首载荷不符、相邻重复／首版未支持路径、输出覆盖或位于父树、body 与 input/support 非法交叉、坏来源；参数化计数独立记录，不堆无关防御分支。
8. **旧行为有限兼容**：零参数的默认 fixed 位移入口和现有 guided displacement 的代表性代数／小模型用例，证明新能力不改变旧结果或源字节。

在三文件边界和共享 fixture 前提下，可把上面交叉重叠的轴收敛为**8个非参数化新测试方法**：非对称代数（含总和／符号）、fresh-anchor拒绝、真实q↔P回归、共享真实缓存与账本、真实注入partial、来源拒绝、有限输入／settings／约束拒绝、旧代表性代数兼容。共享 fixture 新生成 fixed parent、displacement probe、force path 三条真实路径；partial 再增加一条真实力控路径，合计**4条真实路径（含注入partial）**。来源／输入循环只记拒绝场景，不新增真实求解；必须把循环分支数与8个方法数、4条路径数分栏，候选写成后精确冻结。该清单是未来卡的建议，不是本轮执行内容或成功保证。

ROOT提出再运行原 `test_split_displacement.py` 的有限旧检查。静态核实：该文件有8个 test 函数，其中 compensated weighted mean 函数有2个参数行，所以是**9个展开检查项**；synthetic controller 调用计为 **11次**（average1、nonsymmetric1、nonzero_lift2、warm_start4、nonfinite1、nonlinear2），另有**1条真实2单元／12 DOF路径**（最后 actual NumPy test，独立 homogeneous stretch 标量根参考，solver15秒）。因此未来候选可明确为 **8新方法＋9旧展开项＝17检查项；最多4条新16单元路径＋1条旧2单元路径＝5条真实路径**。新注入／拒绝若封顶32次，则加原11次为上限43，候选完成后仍须静审每个循环精确实数；不能把17检查项或43注入／拒绝叫作真实科学路径。现有 probe 的6个旧方法不需额外整批运行：新共享 fixture 已实际调用既有 probe，旧一般 split 控制器另有这9项覆盖；覆盖范围需按此有限声明，不能写完整回归通过。

容差必须按验证对象分开：现有 held mean 为 `1e-10*max(|d_hold|,1e-6 mm)`，free relative residual≤1e−9，J>0，global relative balance≤1e−6，rigid／zero 误差≤8e−11 mm，仍保留；独立 dense fixture 可沿用已存在 rtol1e−12／atol2e−14 的有尺度代数断言，但需记录该 fixture 尺度。8eps×对应原局部项 L1（无地板）只用于不同求和次序的重组核对，不是非线性收敛或 q 交叉回归容差。

新 generalized-force 残差单独按 N 归一化，不能仅以大机构反力的 free-force norm 把微小工件载荷误差稀释；建议源自 `max(|P_target|,|P0|,原force_floor)` 的显式 scale，并在整个本次 line search 固定 base scale。需和数学审阅统一新门及 merit 后才冻结代码。q 回归门必须用该新小模型的有效导向切线／conditioning 将力残差映射为位移误差并给出明确有限界，不能未经计算就要求 bitwise 相同或预设 .025 mm 回归；误差大须报告并停止，不能临时放宽。该检查不证明唯一性、分支稳定或真实工件可行。

资源方面，现有单个真实小模型源／probe测试都声明60秒 solver预算，但这并不是新增力控的实测上界。ROOT的下一候选上限为 tests300秒／显示60秒，共享helper480秒／outer540秒、采样8GiB、各库线程上限16。若新4条真实路径各给60秒，加旧15秒，名义 solver 上限255秒；导入、有限拒绝、普通记录／监督清理仍须纳入对应预算，不能宣称300秒必能完成。本轮仅将其作为未来卡的有界建议；候选冻结后逐项统计，唯一启动、超时／首错停止、保真实partial，无延期／修复重跑，成功才安装两份全新生产源码。没有任何一项在本轮执行。

**本轮结果：API 与验证准备可推进；尚未实现／运行，不能标为力控数值 PASS。**
