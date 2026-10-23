# 力控保存态续载：数学与状态继承只读核查

日期：2026-10-23。核查基线：main `7ebcbf747a85e9c8bbe547bcd6e4fe600f76c12c`。

本备忘只静读源码并计算源码原字节 SHA256，没有导入生产模块、解码 NPZ、执行测试、调用 F/T/HP、运行平衡求解或打开旧媒体。结论是准备阶段的接口与数学设计判断，不是续载功能已经实现的证据。

## 结论

当前力控入口不能直接继续已有非零 q 力控末态。它调用固定工件父任务的 admission；该 admission 要求完成的 `load_only/fixed_rigid` 原峰值、原 lift 全零和原固定 DOF 上 fluctuation 为零。控制器本身也要求 lift 全零，并把初始 q 硬置为零。现有 `native_resume.py` 是机构输入位移路径的续算读取器，同样拒绝非零 lift，不能改名复用。

最小实现建议是三份生产源码候选：修改 `split_guided_force.py` 为显式初始绝对 q 与原始力尺度锚点添加关键字；修改 `native_guided_force.py` 仅提取共用私有 runner/capture，保留当前公开签名和默认固定父入口；新建 `native_guided_force_resume.py`，提供显式 force-parent append-only 入口。无需更改力核、切线核、原位移续算、原探针或默认固定工件行为。

**关键区别必须写入规格：段起点是当前 P_s、q_s，而原路径尺度锚点是 root P_0。两者不能共用一个变量。** 当前控制器的 `P_anchor` 同时用于 fresh 起点和广义残差归一化，续载必须拆分这两个职责，保持原门。

## 已核源码事实

正式源码根：`D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/hf_repo/src/hf_eval`。

| 事实 | 确切源码位置 |
| --- | --- |
| 现公开力控入口由 `native_probe._admit` 读取固定父态 | [native_guided_force.py:54](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/hf_repo/src/hf_eval/native_guided_force.py:54>) |
| 固定父 admission 限完成的 load_only/fixed_rigid 原峰值 | [native_probe.py:61](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/hf_repo/src/hf_eval/native_probe.py:61>)，至第 78 行 |
| admission 重构原项目并核 grid/material/regions/source；仅两份力/切线核作当前 SHA 一致门 | [native_probe.py:80](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/hf_repo/src/hf_eval/native_probe.py:80>)，至第 101 行 |
| 当前 admission 解两个 split 字段并拒绝非零 lift | [native_probe.py:108](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/hf_repo/src/hf_eval/native_probe.py:108>)，至第 127 行 |
| 控制器重复限制 q=0/lift=0，初始 q 硬置零 | [split_guided_force.py:101](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/hf_repo/src/hf_eval/split_guided_force.py:101>)，至第 118 行 |
| 更新 lift 时是 `lift[body_x] = q` 覆盖赋值，没有累加 q | [split_guided_force.py:148](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/hf_repo/src/hf_eval/split_guided_force.py:148>)，至第 154 行 |
| mean 投影仅修正原非工件输入 DOF；q 不投影 | [split_guided_force.py:156](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/hf_repo/src/hf_eval/split_guided_force.py:156>)，至第 170 行 |
| P_anchor 同时为 levels[0] 和广义力尺度中的原锚点 | [split_guided_force.py:116](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/hf_repo/src/hf_eval/split_guided_force.py:116>)、[split_guided_force.py:181](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/hf_repo/src/hf_eval/split_guided_force.py:181>) |
| 约束刚体与 ports/support DOF 冲突已显式检查 | [split_guided_force.py:87](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/hf_repo/src/hf_eval/split_guided_force.py:87>)，至第 100 行 |
| 非对称切线各自求行/列和；一般稀疏 LU；q 行为求和 | [split_guided_force.py:228](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/hf_repo/src/hf_eval/split_guided_force.py:228>)，至第 258 行 |
| fresh 锚点 P 相等时不走 predictor；不合格即拒绝而不是 corrector 修复 | [split_guided_force.py:260](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/hf_repo/src/hf_eval/split_guided_force.py:260>)，至第 293 行 |
| 高层保存 fresh 首态要求同 split hash、R 二进制位、恰好 1 次检查 | [native_guided_force.py:103](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/hf_repo/src/hf_eval/native_guided_force.py:103>)，至第 117 行 |
| 原控制器内部二分保持 rollback，并继承最小力步与 max_bisections | [split_guided_force.py:344](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/hf_repo/src/hf_eval/split_guided_force.py:344>)，至第 365 行 |
| 现 saved 位移 resume 拒非零 lift，虽可借鉴其参数/谱系身份核查但不能直接复用 | [native_resume.py:202](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/hf_repo/src/hf_eval/native_resume.py:202>)，至第 260 行 |
| split 对象不隐式重组/归一化；显示和不能作力学输入 | [split_state.py:1](<D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/hf_repo/src/hf_eval/split_state.py:1>)、第 32、52、60 行 |

## 最小数学与状态合同

设 `I_f` 为原 free fluctuation 的嵌入矩阵，`c` 在全部原工件 x DOF 为 1，其他 DOF 为 0。q 是原参考坐标系中的绝对刚体平移（mm），P 是已含厚度的半模型有符号绝对合力（N）。其余原任务、网格、边界、材料、工件 mask、输入均值 d_hold 及原 ports 保持。

保存态为 `(L_s, w_s, R_s, q_s, P_s)`。其中 `L_s[body_x] = q_s`，其余 lift 为原合法零值，`w_s[original_fixed_dofs] = 0`。这一刚体 lift 已经包含 q_s。admission 原样读入两个 binary64 数组，不能从 `positions_mm`、`u_display` 或二者相减重建，不能把 q_s 并入 w，也不能把父态重新定位到 q=0。

后续候选可写成 `u = L_rest + c*q + I_f*w_f`。现实现可沿用“复制原 lift 后覆盖 `body_x = q`”；不能写成 `L_s + c*q`（会重复加入 q_s）。数学等价的 `L_s + c*(q-q_s)` 也不宜作为实际数组重建步骤，因为它多一次减法/加法并改变已保存分量的舍入。fresh 首态直接用保存数组，不调用 impose 或 mean 投影。

原方程保持：

```text
r_f = I_f^T (f_internal(L,w) - b_in*R) = 0
g   = c^T f_internal(L,w) - P_absolute_half = 0
h   = compensated_dot(b_in, L, w, -d_hold) = 0

Newton unknowns: [delta_w_free, delta_q_absolute, delta_R]

Jacobian = [ K_ff   K_fc   -b_free ]
           [ K_cf   K_cc     0     ]
           [ b_free^T 0      0     ]
```

`K_fc` 与 `K_cf` 分别从实际切线取和，不能相互转置替代；`c` 为求和而不是平均权重。P 不再乘厚度；对称完整装配轴向载荷是 2P、q 不翻倍。原体 y 导向和其与 background 重叠仅计一次；工件 x 已是未知量，不能同时计作 prescribed-body-x drive。

## q / P / R / split 的继承关系

| 项 | force 父态到子段 | 禁止做法 |
| --- | --- | --- |
| q_s | 使用父成功末原目标的原绝对 body_q_mm，作为 controller 初始 q；子段 fresh 行仍报 q_s | 报 0、将之后 q 写作 delta_q、把 q_s 再加到 lift |
| P_s | 子段请求第一项等于父末原目标 P_s；fresh 用该绝对 P_s | 用 0 或原 root P0 作为本段初始载荷；根据 fresh 内力重写 P_s |
| root P0 | 从 force 祖先的原始 anchor 继承，不随段切换改变 | 以本段 P_s 悄悄替换原门的尺度锚点 |
| R_s | signed multiplier 按原 binary64 标量继承 | 取绝对值、从全局反力图重新估计、重算后覆盖 |
| L_s,w_s | 两数组逐位继承，fresh hash 一致；其固定 DOF 合法性先核查 | 用合并位移、显示位置或四舍五入 JSON 向量重建 |
| settings | 除新 clock 外全部 DisplacementSettings 与 GuidedForceSettings 继承 | 为本次新增小步另算更小 N_min，或修改 max_bisections/tolerance |
| physics | 原 grid、材料、ports、支持、工件原 mask 与 d_hold 原样继承 | 运动后 remask、换几何域、把机构输入 d_hold 当工件 q |

## 原验收门及尺度继承

原 `dscale=max(abs(d_hold), displacement_scale_floor)`、`Ffloor=force_scale_floor_factor*force_scale_per_length*dscale`、输入均值约束门、free residual 比例门和所有 J/有限性/刚体/全局闭合门保持。关键的广义力尺度必须是：

```text
segment_anchor_P = selected_parent_P
root_scale_anchor_P = original_force_path_P0
S_P(P) = max(abs(P), abs(root_scale_anchor_P), Ffloor)
rho_P = abs(sum(original_body_internal_x) - P) / S_P(P)
```

fresh 判定仍按 `old_P == P == segment_anchor_P`。因此不能简单把旧 `P_anchor` 全局替换为 root P0，否则非零 P_s fresh 可能进入 corrector。应独立保留 `segment_anchor_P` 与 `force_scale_anchor_half_N`。

对于本项目当前正且严格递增的 P0→P1，root P0 与 segment P1 的 abs 最大值在当前 P≥P1 时恰好不会改变数值门；这个巧合不能代替通用合同。比如严格递增绝对载荷 -10→-2→+1，若续载以 -2 重置尺度，原 10N 尺度会变成 2N。这会静默改变原验收门。需要至少一条控制层纯代数/有限桩验证覆盖该情形，不要求新增真实大模型路径。

fresh 第一次新 F/T 只核 saved 状态、R_s、q_s、P_s 是否原门通过；恰好一次基准检查，状态 hash/R 位/q 位与父相同。任何不通过保存 typed partial 并停止，不能修复锚点、重投影 q、默默跳过 fresh、读取旧 F/T 冒充新检查。

## 最小 admission、谱系与结果 schema

建议公开独立入口接受 force-result、完整延伸请求 P 列表和新输出目录；不允许用户再传初始 q、R、P0、split、材料或新 force_settings。只接受 `success && target_reached` 的父力控结果之最后 accepted 原目标；完整旧请求列表必须逐值精确为新列表前缀，追加段严格递增，至少追加一个新 P。内部二分行不能替代完整请求前缀；父失败历史与原 root 状态仍保留。

admission 应读取 force 父普通 result 原字节并核 canonical/hash、其选中 state 的归档与字段 hash、原 fixed root 的 result/model/source-geometry 描述及重构的 grid/material/region/ports；仅解 selected-force 的 lift/fluctuation 两字段，不需要解原 fixed root 的 q=0 状态，也不能读旧 force/fields/J/Hu/tangent/matrix。`native_probe._admit` 不能直接调用，因为它必读原 q=0 状态并拒非零 lift。

source 至少分开 `immediate_force_parent`、`root_fixed_parent`、`selected_force_state`、`root_force_scale_anchor_half_N`、`parent_requested_loads_half_N`、`full_extended_requested_loads_half_N`、`executed_suffix_targets_half_N`、`appended_targets_half_N`。新段仅执行 `[P_s, appended...]`，不能称自己重算完整祖先请求路径。原 q/历史 accepted index 和新的本段 index 也应分别记录。

新结果 schema 建议明确可辨识的 resume 版本或 continuation 字段；保留原 schema producer 的只读兼容分支，不把老结果改写成新格式。`load_increment_from_anchor_half_N` 保持“本段 P−P_s”；另加 `load_increment_from_root_half_N=P−P0`，不要把同名字段换成其他定义。q 始终绝对值，若显示 `delta_q_from_segment_anchor_mm` 必须单独命名。

原 `mechanics_source_sha256` 列 6 份生产文件，见 native_guided_force.py:182。本次授权修改 native/controller 后，旧 6 个 hash 不能全部与当前文件硬相等；应保留原 producer hash 原值、明确受支持旧/新 schema 和审阅过的兼容迁移，并保持原两个力核/切线核 SHA 一致的机械硬门。新 producer 应额外记录新 resume 模块及当前 controller/runner 的真实 hash。不能伪造旧 producer hash、以所有 SHA 不变作为这次代码修改的前提，也不能取消原两核一致门。

输出必须是新目录且在全部父冻结树外。普通 metadata/归档在恢复目录下的解析应有明确闭包映射；不能为了找到缺失源而递归搜索并接受任意同名文件。当前旧 result 的绝对来源路径需要作为跨目录恢复方案核定事项，不能声称新签名天然解决了可移植性。

## 有限小模型验证的必要证据

以下是方案要点，未运行；最终用例数、资源窗口和门需由主任务冻结：

1. 旧 q=0 默认路径回归：同原入口、签名、P 列表、原门和结果语义，确认新增关键字默认不改变旧行为。
2. 一条真实小模型连续原载荷路径与“成功非零 q 父段→保存态续段”在共同绝对 P 对照。fresh L/w hash、R/q/P 位与父保持；最后 q、全 DOF 的四分量补偿位移差、signed R 及原所有门通过。等价解允许预先核定的小数值容差，不能要求不同舍入路径所有终态逐位相同。
3. 明确断言非零 q 存在于保存 lift，fresh 不是 q=0；下一步 body lift 等于绝对 q、不是 q_s+q；这条验证应检查实际生产 controller/capture，不只比较一个辅助函数。
4. 再续一段检查祖先 P0、完整请求前缀、局部/全局 index、段增量/root 增量仍保持；可在同一小模型试验链中完成，避免再造大验证项目。
5. fresh 锚点不平衡/状态 hash 或 q 元数据冲突：应 typed 拒绝，fresh 不进入 predictor/corrector 修复。来源错误在任何 F/T 前拒绝，数值 fresh 错误记录实际一次检查后停止。
6. 非 append、篡改前缀、选择内部二分或非末原目标、失败父、参数或 force_settings 改变、路径逃逸/原树覆盖等必要反例使用普通 metadata 修改或受限桩，避免为每项反例跑真实求解。
7. 纯代数/有限桩覆盖 root |P0| 大于本段与新 P 的有符号情形，确认 `S_P` 和 fresh 使用不同锚点；保持原 N_min 和内部二分 rollback 规则。

## 尚待主任务核定

- 最终公开函数和 schema 字段命名、exact source closure 及异目录恢复映射；不能把仅文档建议写为已安装能力。
- 真实小模型使用的原父 fixture、P 列表/工程对照门、总测试数量及资源窗口；本备忘不授予计算额度。
- 后续 r9 新载荷数值和资源是独立阶段。本阶段不得运行正式 r9 或依据 q=0.025 反向指定未知 q 的力控解。

