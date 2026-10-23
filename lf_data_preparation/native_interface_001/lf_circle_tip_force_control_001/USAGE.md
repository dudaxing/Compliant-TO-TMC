# 最小导向轴向力控：用法与当前能力边界

2026-10-23。依据本轮已测的两个新模块和本次普通 JSON 记录编写；没有再次运行 API、测试、数值计算或图像检查。唯一17项检查、显示及四层同实例清理通过后，top安装两个同字节新模块，随后在原窗口内一次封存。旧 55 份生产源码、默认固定工件入口、位移 probe、CLI 和 native_response 保持原样。

## 面向保存文件的薄 API

```python
from hf_eval.native_guided_force import (
    GuidedForceSettings, evaluate_native_guided_force,
)

# 调用模板，不是本卡第二次执行命令。
# parent_file 是完整成功 fixed_rigid/load_only 父任务的 result.json，
# selected 是它最后一个原目标峰的 states 索引，output_directory 必须全新且在父树外。
result = evaluate_native_guided_force(
    parent_file, selected,
    body_load_targets_half_N=[P0_half_N, P1_half_N],
    output_directory=output_directory,
    force_settings=GuidedForceSettings(
        minimum_force_increment_half_N=minimum_force_step_half_N,
    ),
    time_limit_seconds=approved_controller_seconds,
    on_accept=None,
)
```

API 从合法父任务继承机构输入均值 d_hold、原几何/材料/网格、原 body 成员、支撑、执行模式及非 clock 数值设置。它迁移原 lift/fluctuation 和有符号 R；不回放父加载、不改几何、不重选运动后的成员、不从位移 probe 终点热启动。

q 是新的有符号未知量，不在参数中输入 `.025` 或任何预期位移。全部原 body-x 位移等于同一个 q，body-y=0、转角=0；机构均值仍等于父末峰 d_hold。新控制器采用约化切线预测；原父初猜模式单列为 `parent_initial_guess`，不冒称力控仍执行原位移端口初猜。

结果采用独立 `hf-native-guided-force-1.0` schema，不能交给仅支持 native-mean 的旧响应入口冒充已关联结果。`accepted_steps` 记录每个真实接受态和内部二分态；保存 split/fields 时不再求 F/T。数值失败保实际 partial，检查 `status`、`failure`、`target_reached`，不能只看目录存在或已有首态文件。

## P0 来自真实预载，不能设为零

固定工件父末态 q=0 不意味着工件广义合力为零。机构已经变形，第三介质/正则项可以在这个位置给出非零弱力。首目标必须是与该原态相容的**绝对**预载 P0，不是本段增量。

已有父普通摘要给出 ON-body 总力时，可用下面的读取关系选出 P0 候选；若已有同父的 q=0 位移 probe，也可用该态的 `Q_drive_half_N`。这些已有普通数值只用来选目标，不替代新验证。

```python
import json
from pathlib import Path

parent = json.loads(Path(parent_file).read_text(encoding="utf-8"))
selected = len(parent["states"]) - 1
P0_half_N = -parent["states"][selected]["workpiece"][
    "force_on_lower_body_N"
]["total"][0]
```

来源准入必须先确认最后原目标、完整成功 load_only、fixed_rigid、材料/网格/成员/源码/两字段身份。随后力控 API 对原 q0、原 split 和 R 进行本轮**新鲜 F/T**首检；原 free/mean/几何门和新增 g 门全部通过才检查 1 直接接受。错误 P0、R 或均值会失败，不能把 P0 替换成刚算出的 Q，也不能先做 Newton、投影或重平衡修复锚点。

本次小模型真实目标是：

|绝对 P_half / N|独立求得 q / mm|位移参考 q / mm|
|---:|---:|---:|
|−3.216587387036128e−8|0|0|
|−1.6275064208362818e−8|0.0002499999996011167|0.00025|
|−4.213649168822395e−10|0.0004999999996012887|0.0005|

这些数值直接抄自本次 `validation_summary.json`，不是新增复算。负 P0 被原样保留；从较负值向较大值递增是当前受支持路径，不能为了“正向载荷”改符号或把锚点归零。小模型的载荷不能移植到正式 r9 模型。

## 半模型、符号和力步长

P_half 是沿固定空间 +x 的有符号刚体合外载，单位 N，已含模型源厚度；不是 N/mm，也不需要再乘厚度。镜像完整装配的轴向载荷 P_full=2P_half；同一个 q 不倍增。API 只收 half N，没有自动 full/half 猜测参数。

```text
Q_half = sum_body(f_int,x)
F_ON_body,x = -Q_half
g = Q_half - P_half
平衡：F_ON_body,x + P_half = 0
```

P>0 表示外载沿 +x；P<0 表示沿 −x。R_input 是机构均值端口乘子，不能当工件轴向载荷。下半模型 Fy 与导向反力属于另一方向，不能把 2|Fy| 称轴向承载能力。

外力账本用显式 (P_half,0) 代替原 body-x 处方驱动力；body-y 导向与其他零支撑按集合去重。工件内部广义合力是输出，不能再当另一个外载重复加入账本。逐节点弱力不除任意面积称压力。

`GuidedForceSettings.minimum_force_increment_half_N` 是 N 量纲的最小二分半步；不得用旧 `DisplacementSettings.minimum_increment` 的 mm 数值代替。本次小模型 N 设置为 `9.908562057175361e−10 N`，旧 mm 设置另为 `3.125e−5 mm`。目标均为绝对 P；ΔP=P−P0 仅供解释，不偷偷转换输入语义。

## 低层控制器入口

```python
from hf_eval.split_guided_force import (
    GuidedForceSettings, solve_split_guided_force_path,
)

# project、anchor_state、anchor_R、parent_settings 和 fresh_assembler
# 必须已经过上层同等来源准入；这不是读取任意缓存的捷径。
path = solve_split_guided_force_path(
    project.model, project.bin, project.bout, loads_half_N, project.k_out,
    initial_state=anchor_state,
    initial_R=anchor_R,
    settings=parent_settings,
    force_settings=force_settings,
    force_scale_per_length=project.material["force_scale_per_length"],
    body_contract={
        "nodes": original_body_nodes,
        "d_hold": held_input_mean_mm,
        "zero_dofs": original_zero_dofs,
        "background_dofs": original_background_dofs,
    },
    assembler=fresh_assembler,
    on_accept=accept_cached_state,
)
```

低层未知量为原 free fluctuation、一个 q 和 R，保持实际非对称 K 的两个耦合方向独立求和，使用一般稀疏 LU。它对 synthetic oracle 保留 global 诊断；真实保存文件 API 另执行 rigid/zero/global 物理接受门。直接调用低层不能省略来源准入与这些物理门后声称完成正式任务。

free 残差、工件 g 和机构均值分开验收：原 free tolerance=1e−9，独立 g 使用同 tolerance 且 SP=max(|P|,|P0|,Ffloor)，mean 使用补偿测量与原 1e−10*dscale 门；真实 J 全正、刚体/零支撑误差≤8e−11 mm、全局相对闭合≤1e−6。新步长与 merit 不改变原门。

## 当前支持与下一步

当前只支持从合法固定父 q0 出发、至少两个有限有符号绝对 P 严格递增的路径。q 可以正或负，但不支持指定 q、力控结果续算、力控卸载/循环、自由 y/转动、摩擦、随动压力、弧长或极限点搜索；没有自动 force→displacement 回退。原内部回溯/有界 N 二分与外部重试不是同一件事。

本轮只验证 16 格/50DOF、full 切线的有限功能；正式 r9 模型原 chunk256 的新力控路径没有在本轮运行。通过 q↔P、全局账本和本轮精度门不等于已经验证压力、纯接触力、承载极限、释放、稳定性、唯一性或 HF5。

下一步建议只准备正式 **机构均值 .50 mm 的两载荷交叉检查卡**：从 LOW1 原完整固定父最后 .50 mm 峰出发，复用原 α=2.5e−7、r9/圆心(80,40)/right92/Lr80 与全部原条件；候选 P0=`3.686421133658022e−5 N`、P1=`4.3272306948756724e−5 N` 来自已有同父 q=0/.025 记录。只给 P 求未知 q，再与原位移 probe 的实际 .025 mm 末态作事后比较，不输入这个 q。

新卡应先冻结父/参考身份、原 chunk256 执行模式、独立 N 最小步长、正式模型 q/R/状态交叉比较界值、实际显示读取集及独立有界资源；小模型的 1e−8 mm 功能回归界值不能未经审阅自动变成正式 r9 精度保证。成功后显示实际 ×1 变形、P–q、机构 R、material/Hu/total、J/介质和收敛；暂不扩展至1.06 mm、卸载或额外HP。本轮窗口已关闭，这些仅是下一步建议，没有执行正式路径。
