# L-CTIPMOVE1 controller 最小变更设计（尚未实现）

2026-10-22。参照 main `1e5e9cf76480254a6a288f27fb10bc884acb4c38`。只读源码设计；本文件不代表编码、测试、F/T 或数值路径已获授权或已执行。依据已发布 `docs/WORKPIECE_LOAD_TASK_SPEC.md`。

## 选择：原 controller 的窄 opt-in 扩展

在 `split_displacement.py` 内新增一个显式的 prescribed-body 探针合同参数（名称在实施卡固定，建议单一 `prescribed_body` 对象），默认 `None`。该对象只描述原 body-x/y DOF 集合和正的 `d_hold`，不成为通用 MPC／任意多载荷控制框架。新模式仍调用同一 `solve_split_displacement_path`、同一 `_kkt`、一般稀疏 LU、Newton、Armijo、回溯及内部二分。**不复制完整 controller，不增加第二个平均位移约束，不改变力核或切线。**

保留 `native_mean.py`／`native_evaluate.py` 的既有固定工件入口。新 `native_probe.py`（建议文件名）作为独立薄研究入口，负责新合同、显式初猜 admission、新模式调用、移动工件观察和独立结果 schema；不通过 `extend_path` 伪装新物理任务。该入口仅复用当前构模得到的参考 body 成员和原力／切线函数，不调用旧固定工件求解入口再改结果。

最少需要修改一个既有实现文件：`split_displacement.py`；新增一个薄探针模块和相应小模型测试文件。无需改 `split_state.py`、`displacement.py`、`native_resume.py`、原 kernel 或原公开 task schema。若实际候选需要额外修改，先写出证据和范围，再按执行卡裁定，不能临时扩成另一套 solver。

## prescribed DOF 与两套控制量

令 `B_x`、`B_y` 为同一已绑定工件节点的 ux、uy DOF，`C=model.fixed_dofs`，`F=model.free`。保持原 `C` 和 `F`，不解除任何 body 节点为独立未知量。新运动只令 `L[B_x]=q`，`L[B_y]=0`，`w[C]=0`。其余零支撑的 lift／fluctuation 继续为零。`B_x` 仍是 prescribed DOF；把它从 `fixed_dofs` 删除会失去刚体消元，不能采用。

新 opt-in 的 v1 限制为：body 成员与完整 x/y DOF 映射精确；`B_x∪B_y⊆C`；与 input/output/实体支撑冲突拒绝，只有已声明 body-uy 与背景对称重叠可去重；`lift_origin=0`，`lift_shape` 只有 `B_x` 恰为1、其余恰为0；`target_origin=0`，`initial_parameter=0`，路径为从0严格增加的 `load_only` q，`saved_load_only_anchor=False`；`initial_state` 与有符号 `initial_R` 显式提供。这些限制避免把本次有限探针偷偷扩成任意非零支撑或保存态续算框架。

当前第116–117行“所有 fixed lift 必须为零”的保护不能直接删除。旧模式照原代码检查；新模式只接受上述 B_x 仿射 lift，并对 `C\B_x` 保留零保护。第123–126行的 warm state 类型／DOF、lift 逐位相同及 fixed fluctuation 为零检查继续保留。q=0 初猜保留两份 split 数组与 multiplier 的原字节，不合并、不 rebase，不经 `u_display`。实际 body bbox／来源／节点身份由薄入口负责绑定，controller 不重新按移动后的圆心选单元。

路径参数现在是 q，机构目标是固定 `d_hold`。建议在 controller 内集中两个局部函数：

- `mean_offsets(s)`：旧模式返回 `(-target_origin,-s)`；新模式返回 `(-d_hold,)`。
- `physical_mean_target(s)`：旧模式返回原 `target_origin+s`；新模式返回 `d_hold`。

所有平均测量／约束误差继续调用 `_dot`，传入原独立 offsets；不能先计算一个已舍入的 `target_origin+s` 再从测量值相减。旧分支这样保留原 FMA／fsum 补偿算术。新模式的 force floor、constraint bound 使用 `max(abs(d_hold), displacement_scale_floor)`，不使用 q，也不因 q=0 降低归一化尺度。

## `target_origin+s` 的完整修改表

以下行号均来自本次绑定源码；共10处实际计算／诊断位置，另需更新第61、63–75行的函数说明。这里不把 docstring 或 guard 算作第11个计算位置。

|现行行号|现行表达或用途|新模式的最小处理|
|---|---|---|
|179|feasible 前 `_dot(...,-target_origin,-s)`|用 `*mean_offsets(s)`，held target 不随 q 增加|
|182|feasible 后相同表达|同上，仍保留逐位 lift 与 compensated measurement|
|183|constraint bound 的 `abs(target_origin+s)`|用 `physical_mean_target(s)`；q=0 也用 d_hold|
|194|残差 force floor 的 displacement scale|同上，保持原尺度与 factor|
|198|measure 的 constraint residual|用 `*mean_offsets(s)`|
|201|accepted 的 `physical_mean_target_mm`|用 held target；原 `d=s` 仅内部阶段参数，新结果明确别名为 body q，不能对外称机构位移|
|238|一般 LU 诊断的 target|记实际 mean=d_hold，并保留 stage_parameter=q；不影响 LU 矩阵与 RHS|
|254|q 预测步 mean RHS|用 `-_dot(candidate,...,*mean_offsets(s))`；已平衡上态且 body/input 不相交时等价于 `-b_inᵀΔL=0`，不带 `+Δq`|
|292|backtracking record 的 target_displacement|新模式必须同时明确 body q 与 mean target；不得让消费者把 d_hold 误作 q|
|365|末端 `physical_mean_target_mm`|用 d_hold；目标／到达 stage 参数另写 q 字段|

第251–253行 `delta_L` 与 `-(K@delta_L+k_out*b_out*delta_q_out)[F]` 已是仿射 lift 的正确力预测 RHS，保留；不改 K 的非对称性。第234行仍以原 C/F 消元并组同一个 bordered KKT。第257–261行原 tangent／port_projection 初猜选择保持；新模式 mean_rhs=0 不意味着取消真实 R 预测或跳过随后的原 Newton 检查。

与 `target_origin+s` 无直接字面关系、但必须一并明确的 stage 字段为第268行 history 的 d、第330行 failed-attempt from/attempted displacement、第341行 original target、第358行 leg、第364行 target/reached、第380行 loading_peak。新薄结果不套用旧 mean-path／peak1.06 的语义；记录 `body_translation_mm`、`requested_body_translation_mm`、`physical_mean_target_mm`，保留 controller 原阶段诊断。旧模式原字段及含义保持，新增 probe 字段只在 opt-in 分支输出。

## q=0 新任务 anchor：禁止 Newton 修复的缺口

这是本次设计的必处理项。当前第275行仅在 `initial_parameter` 非零时触发“保存态首次新 F/T 必须直接通过”的保护。探针从旧 loading 1.06 mm 保存态迁移到新任务的 `q=0`，其 `initial_parameter=0`；即使 `initial_state` 非零，该布尔条件也为假。仅设置 `initial_state` 会让第283行继续 Newton 修正，这违反发布规格。

需要与参数是否为零无关的显式 anchor 合同。新 prescribed-body 模式本阶段一律要求已 admission 的 initial_state/R，并自动开启 `require_fresh_anchor`；默认旧模式条件保持。建议把第275行的判据扩成：`fresh_anchor_required and not accepted and old_s == s == initial_parameter`，其中旧模式的 `fresh_anchor_required=bool(initial_parameter)`，新模式固定 True。新模式拒绝缺 initial_state；**不能以设置一个很小的非零 initial_parameter 绕过此问题**。

第一个 q=0 调用：在任何 predictor、feasibility projection 或 corrector 前，以原 split 数组和原 R 做一次新 F/T。现有 q=old_s 分支不会执行 predictor，可以复用这一点；新 mode 必须显式记录 anchor=true。若新力残差或平均约束不通过，报 `initial_state_not_equilibrated`，不调用 linear solve、不投影初猜、不二分出另一个起点、不修正 R。若 kernel/J/非有限失败，保留真实 typed 原因并终止，不改称释放。首步差值为0也会使现有二分最小步判断终止，但应把 fresh-anchor 失败列入不可二分类型以使合同直接可读。

`advance` 第326–335行的 catch 还需显式识别新模式首次 anchor 尝试：`not accepted and before_s == s == initial_parameter` 且新合同要求 fresh anchor。此尝试的任意 typed 失败立即终止，不进入二分；不只依赖 `initial_state_not_equilibrated` code，因为首态 J 或 kernel 失败也应首错停。只对 opt-in probe 加此判据，旧模式原处理保持。

成功的 q=0 接受记录必须核 state SHA 与 R 的二进制字节仍等于源初猜；首态有新 F/T，无缓存矩阵输入；不存在 Newton correction 或 predictor 线性求解。随后 q>0 正常使用本窗口新切线。不能只查 `newton_checks==1` 推断 identity，必须同时检查数组／R 身份和 solve 计数／phase。

## 薄入口、来源迁移与观察的边界

`native_resume.py` 第183–201行严格同 task／模型材料／边界来源；第229–230行要求原 split 全零 lift，旧 suffix/extension 不能承接新物理。保持这些原规则。新薄入口提供单独的显式“固定峰初猜→q=0 探针” admission：仅同几何、节点／cell、材料、原边界、原设置、原力核／切线及所选态身份一致，绑定 original parent task 和独立 probe task；保留旧路径与资格。读取两份 split 字段、原 R；不读原 K、force 或 tangent 来替代新验证。字段/来源错误在新 F/T 前 typed 拒绝。本轮仅设计，未读取任何科学 NPZ。

**saved-file admission 属于下一张最小实现卡，不能仅用内存 initial_state 代替交付。** 新 `native_probe.py` 应接收明确 parent result 文件、selected index 和独立 probe task／q targets，读取 fixed parent task/model/source/selected descriptor，核普通文件 SHA 与声明身份，读取绑定 state archive 的且仅有 `lift`／`fluctuation` 两字段及其 dtype/shape/字段 SHA／state hash；R 取绑定 descriptor 的有符号原值。保留父几何和构模函数，独立 probe 合同不写入旧 task path，也不在父冻结目录产生新文件。

实现需要分清“旧力核／切线源必须相同”和“controller 正为本功能变更”：迁移保留 parent source pins，新结果另存实际执行 controller 的新 SHA；不能要求新 controller 与父 controller 相同而把本功能拒之门外，也不能直接改写父记录来假装相同。仅提取或复用窄的现有普通身份读取帮助（如需），不改旧 resume 的 default strict 比较、metadata 或 extension 规则。API 不在 `__init__`／旧 CLI 默认安装；不新增通用本构、自由刚体、力控或全路径自动回放。

小模型验证须通过该真实 saved-file API 读取**新生成的小模型** parent 保存态和源身份，覆盖正常及不一致 admission；不能只测试内部 controller 然后宣称文件接口完成。真实14720单元旧峰值文件／数组本卡不读取；真实 L-CTIPPROBE1 另行授权。

`native_mean.py` 的第191–211行展示现有同态 force/tangent assembler 调用，新的薄入口可复用已有 `_assemble_force`／机械分支、`_tangent`／chunk256选择和 `_assemble_tangent`，以小闭包保留一态一次 F/T 缓存；本阶段不为抽象化去大改默认入口。完整 controller 不复制；若实施选共享缓存 helper，须证明旧调用路径与既有 cache 计数保持。不是通过保存／显示阶段再次计算 mechanics。

旧 `_workpiece_observations` 第67–110行固定 body bbox／holding 字段，旧 metadata 第259–285行 task_target／mean peak 语义，不能直接拿来给移动体赋名。新观察使用实际位置 `X+L+w`，互斥 `body ux驱动/body uy导向/其余零支撑` 分区（背景 uy 重叠只一次），有符号驱动 `Σ_B f_int,x`，ON-body `−Σ_B f_int`，total/material/Hu 各存，厚度已计入 N。全局原 support_reaction 向量可作为同一残差来源，但账本分组的和必须精确复原，不能额外重复相加“工件力”。

下一阶段小模型应以非零 held mean 和非零初猜为主，验证 q0 直接通过、污染初猜直接拒绝、q>0 平均输入不随 q 改变、body 各 ux=q/uy=0，以及默认路径保持；具体测试数、预算和候选源闭包由总执行卡固定。真实 14720单元圆形路径、新 HP、默认固定入口安装和力控制均不属于本设计的执行范围。

## 本次只读源身份

|文件|bytes|SHA256|
|---|---:|---|
|hf_repo/src/hf_eval/split_displacement.py|24156|151cc130f0a75e3b2f201b393541107ccf2feaa3de365db72d1987568dae1bb8|
|hf_repo/src/hf_eval/native_mean.py|22777|76fd9917fe378865f3f359838958e58505afb9ae2e7c7ec257773a76178fd6e4|
|hf_repo/src/hf_eval/native_resume.py|18014|68e3122950766f9cecb48a02a0f52a6d5f2efbfc466432bccc2cd48c77e2b798|
|hf_repo/src/hf_eval/split_state.py|2544|457e78f7f9dfa55566800915637af3b2e5ea38db969d7da98c8294efad69538e|
|hf_repo/src/hf_eval/displacement.py|26838|fbae379e37f0816edcdebd765bcae73a525c8709c2cb8f798146e497c9a4a386|

说明：读取源码与已发布规格、查看 Git HEAD、普通文件 size/hash；未 import HF、未测试、未构模、未读科学数组、未读 CSV 或媒体，未改 ROOT 源码、结果或 Git。
