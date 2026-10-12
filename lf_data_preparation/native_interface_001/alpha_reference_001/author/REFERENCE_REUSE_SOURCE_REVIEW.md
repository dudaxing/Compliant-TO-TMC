# 新 alpha 两态独立参考：源码复用审阅

结论：M-REF2 的旧入口不能直接运行新 child；B850 `Audit.run_state` 和 aa86 `WorkpieceCycleAudit.workpiece_checks` 的数学与原 15 门可以原字节继承。需要一个只负责绑定输入、索引、资源及汇总的薄 loader。本结论只来自源码／AST／普通 JSON，尚未验证数组或执行 HP。

## 原包装与实际 child 的差别

| 部分 | 源码证据及取舍 |
| --- | --- |
| M-REF2 包装 | `execute_nested_reference.py:32` 固定旧协议 schema；`:66` 起要求 24 态／48 HP、旧生产阶段／回执；`:116` 起要求整个原路径／任务目标成功和回零；`:198` 起要求原索引 0–23 及 origin/loading/unloading；`:224` 起汇总 24／48。它还绑定 alpha=1e−6、原14400秒设置与4500秒参考窗口。这些都是旧卡范围，不能沿用授权或改旧文件来适配。 |
| 新结果 | `saved_continuation_001/run_001/resumed_alpha_half/result.json` 是 schema1.2、机械模式、chunk256、两个绝对目标 `[1.20,1.15]`。子行 0 是 `resume_origin`，原目标13，父态原 leg 为 loading；子行1是 unloading，原目标14。`segment_completed=true`，父仍 failed/time_limit；`task_target_executed`、`full_original_path_completed` 仍 false。 |
| 物理及数组声明 | model schema1.1、h0.5、13440 单元／27378 DOF、固定 square、27 model 字段与旧 fine 几何相同。实际声明 alpha=5e−7、kr=0.004307692307692307 MPa·mm²；不能套用旧 alpha/kr。每态声明 split2、机械 forces16、三 tangent，以及 full unsymmetrized CSC。这里只核 JSON 声明，未读取 NPZ。 |
| B850 首态限制 | `core_audit_mechanical.py:299` 将调用 `index==0` 判为 fluctuation 全零且 R=0。新首态是非零1.20锚点，直接 `run_state(0,row)` 会失败；不能为了通过门把原 row、R、d、leg 或物理位移改成零。 |

## 最小复用路线

新 loader 按绑定的原目标索引13／14调用原 `run_state`，随后同索引调用原 `workpiece_checks`。这保留真实原目标身份，不把子段首态当未变形 origin。B850 的 index 只用于输出目录、这项原 origin 条件和记录身份；真正力学方程使用 row 的 `target_origin+d`、原 split、R 与模型。aa86 使用 `self.rows[-1]`，不按13／14索引长度为2的列表，所以不需伪造前13态占位。

raw 科学目录保持 `accepted_013`／`accepted_014`，其 summary index13／14、工作件文件及所有科学结果不重写。仅在**新顶层 summary 的复制元数据**中填 `index=0/1`，并保存 `reference_execution_index=13/14`、`original_target_index=13/14` 和输入 child 行身份。`native_response.py:98` 的已有参考匹配要求顶层 index 与 child 枚举0／1一致；本阶段只准备该合同，不调用摘要/API关联，也不改 consumer。原 child/result/descriptor/图帧身份保持。

loader 的 load 需建立 `origin/result_file/model/edofs/direction/result/metadata/receipt/workpiece_dofs/groups`，并复用原 CoreAudit 的 bind/check/gate/record；`CoreAudit.__init__` 的历史 repo 推导须由显式新 repo 覆盖。checkpoint、lifecycle、run 与 summary 是包装层；`run_state`、`workpiece_checks`、Decimal公式、分母、散射次序和15个门不 override。必须新绑当前 child 的原生产回执／终态、原两态 cache、任务及 continuation，不强加旧完整路径字段。原生产 F17开始／16完成含一个正常拒绝的 invalid_J trial；不借旧 loader 的开始=完成假设否认两态接受缓存。

## 继承的数学与验证范围

B850 `run_state:276–496` 读取保存 split/forces/tangents/CSC，逐单元比较三分量力和**声明 PORT 方向**作用，重新检查原顺序组装与 saved CSC，全局 Decimal 散射和均值/KKT/平衡。每态新 HP80／120各一次，完整13440单元／27378 DOF；两态拟4次新HP。实际 direction 仍为 `b_in/max(abs(b_in))`、固定分量0、deltaR=0，由加载的真实模型给出，不另造单位方向。

aa86 `workpiece_checks:269–327` 复用这些全局独立力与方程，比较 signed total/material/Hu 工件投影、holding 的不重叠 fixed partition、镜像 net／两侧幅值及 rigid dummy interior。它不再调用一次独立 constitutive evaluator，也不新增材料+Hu合成门或独立 Hu 误差门。

原15门的源码字面值与原 audit_native_mean／run_split_average_demo 一致，完整键值记录在 JSON。包括原残差、均值、平衡、固定位移、HP80/120一致性、三力／三方向切线及KKT门。辅助材料能量候选仍 not_evaluated；独立 HP 的 analytic energy 仅存档，不进行候选能量比较。J/F/Hu 的 rounded diagnostics 仍是原描述性输出，不能升级为新的 HP stress/Hu 资格。完整 CSC 从保存 tensors 的系数重组与比较，不等于独立检查全部切线列。

## 输入、依赖与输出边界

未来核心需要一个 model NPZ 和每态 state/forces/tangents/CSC，共9个独立 NPZ文件；aa86还会重复读取两态 state/forces，不能把它误写为一次读取缓存。本轮没有读取这些文件字节或字段。源 geometry JSON 用于声明身份，源 geometry NPZ在旧 M-REF2只作 raw身份绑定，不构模／重采样。最终实际 decode 字段／次数范围由独立输入审阅与候选源码冻结，不从模型27字段误推 CSC archive只含其3个数值声明。

原 M-REF2 的11份 source closure在当前main仍全部同SHA，目录 basename唯一，可直接保留原来源映射：B850、aa86、audit_native_mean、audit_native_force、hf4/hf2 Decimal helper、run_split_average_demo 的 AST门依据，以及 `hf_eval/__init__`、tangent_action、compensated_invariants、tmc_kernel。tangent_action 仅消费保存 tensors；其后两依赖在 import 时会载入 JAX/JAX NumPy，不能声称未来完全不 import JAX，但继承路径不调用 constitutive JAX kernel、AD或JIT。这里当前没有实际导入它们。

每个继承 raw 目录会保存原 fixture、HP80/120 local、full global、element gates、global differences、equations、actions、rounded kinematics、重组 CSC、workpiece_checks 和 summary；顶层另存全2态 summary、lifecycle、来源与协议。无新生产力／切线评估、构模、平衡、HP结果关联或绘图。总产物数待具体候选冻结，当前不制造结果或设置资源窗口。

新参考即使以后通过，也只覆盖这两态及声明方向和弱式投影；不能借旧48HP、不能宣布父14加载前缀或原15／24态完整路径通过，不授压力、有效夹持、全部切线列、网格／域／参数稳定性或HF5资格。当前只完成可复用性证据；root再据输入与成本证据安排新候选和具体卡。
