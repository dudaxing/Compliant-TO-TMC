# Horner192 范围诊断：首次拒绝已定位，完整力资格仍失败

独立观察卡唯一调用原 F16 一次，捕获首次失效的DD primitive及终端原始响应，并按原样重现外层 `KernelError`。诊断 `diagnostic_captured`、外层exit0表示证据采集完成，完整力仍是1次启动、0次完成；没有切线或HP资格，也没有修复或重跑001/002。


## 实际发现及位置勘误

首次拒绝的调用链是 `_response:195` 的 `scaled_square(small_delta, remainder)`，进入 `scaled_square:146` 的最后乘 `2^-64`，再到 `_scaled_mul:115` 最外层乘 `down=2^-192` 的回缩。DD四项乘积中被捕获的是第三项 `(lo,hi)`，即 `a_lo*b_hi`；不是 `scaled_square:145` 的系数乘，也不是 `(lo,lo)`。

保存参数显示 Horner循环已结束于power2，`horner_scaled=true`、`small_products=true`。本次首次拒绝涉及48个积分点、35个单元。独立保存原值审阅确认35个单元与材料能量NaN单元集合完全一致，其中29个原机构solid、6个third medium、0个工件单元；不能统称medium，也不能把旧原内核诊断的36积分点/26单元套用到新候选。

原始输入字有限。已保存的primitive标量审阅表明，拒绝来自声明的DD分量下界 `2^-400`：该 `(lo,hi)` 非零结果约为 `4.21459303788755e-132 .. 1.7622661807780653e-121`，低于声明下界；这些值仍是IEEE正常数。因此不能把它描述为NaN原输入、IEEE下溢、溢出或几何接触失败。本草稿仅引用独立保存审阅，没有重算本构或HP。

## 原始响应与资格边界

观察器保留了原 `_response` 返回的26个字段，并返回原tuple，没有换掉数值或支撑标记。保存的三元素力、F/J/Hu及P/S均有限；唯一非有限字段是 `material_energy`，3200个单元中3165有限、35为NaN。全局 `arithmetic_supported=0`，原完整公开入口随后按原门拒绝。

有限原始字段只是观察事实。它们没有经过本卡HP参考，不能称为力正确、应力正确、DD所有机械分量受支持或平衡通过。被捕获能量分支在保存选择器中为选中分支，且首次拒绝单元与最终能量NaN单元对应；这一证据不能证明每个位置没有后续失效或该点是所有范围拒绝的唯一根因。

## 实际执行与资源

| 保存字段 | 实际值 |
| --- | --- |
| `evidence/result.status` / `qualification` | `diagnostic_captured` / false |
| 外层 `status` / `exit_code` / `invocations` | pass / 0 / 1 |
| `force_started` / `force_completed` | 1 / 0 |
| tangent / HP / solver / JIT / LF / global assembly | 全部0 |
| helper `elapsed_seconds` | 8.149948399979621 s |
| 外层 `elapsed_seconds` | 8.516662999987602 s |
| helper采样峰值 / 外层树采样峰值 | 246530048 / 238292992 B |
| 外层protocol / 诊断input bindings | 310 / 279项，前后同 |

原16字段输入、27字段模型、14个重叠模型字段、积分点和stateSHA保持一致。63份生产来源及capsule、隔离42文件runtime和失败卡部分包保持原字节。首坏NPZ有41字段及48对invalid索引；raw NPZ的26字段逐dtype/shape/rawSHA和finitecounts均经只读核对。共319个文件身份核查一致。三原hook还原由保存回执及两处finally源码支持；只读后审没有重新建立过去的运行时句柄身份。

本卡为新独立60 s helper / 90 s外层 / 采样树8 GiB窗口，含导入、原调用、观测保存和末端身份检查；属于协同时间检查和进程树采样，不是OS硬限或强制清理合同。脚本封存，不能用诊断成功覆盖原失败卡。

## 下一唯一近期功能：显式机械量职责合同（尚未实施/执行）

下一候选应先明确opt-in机械入口的职责，保留默认完整输出入口及其失败记录：三分量力与切线、必需运动学和J门各自仍按原DD支撑域检查；辅助能量单列状态和原证据，不能填0、删项、忽略其NaN或冒称完整能量通过。应力原始有限也不附带应力HP资格。当前mean控制器的Armijo使用增广残量平方，不以材料能量作为merit；这为最小职责拆分提供代码依据，不等于已经修复了控制器或卸载路径。

只在同一原 F16/27字段模型上打开新候选卡：一次完整机械力、一次缓存切线、三次补偿action消费和独立进程fresh80/120参考；保持原19200项local、9项global及614400个CSC系数检查、Et20派生 `2e-13 N` floor和全部原门。候选首错即停，候选未通过不启动HP。新预算和来源需另行冻结，本阶段不借用旧HP、不启动另一条循环、不推定T25已经解决。

整个HF目标仍包含普通数据入口、非线性响应、加载/卸载平衡、工件反力和可视化。这张单态候选即使以后通过，也只给原F16声明的机械返回和方向验证范围，不会自动给接触压力、夹持完成、任意切线列或新循环资格。

## 可复核证据

- [evidence/result.json](evidence/result.json)，SHA256 `3f2678fde968da9032237d52227db9e124307e3331e7450d812d83d411a8cd31`。
- [diagnostic_launch.json](diagnostic_launch.json)，SHA256 `c76d64c600a8798695ce80ee087cf714bca0eadcf154e933645d8045807ffbda`。
- [protocol.json](protocol.json)，SHA256 `5c8c81ce5f57c38fa9d4d120fcfb2dba27f5e725b56a4b3b1203b99dcc9f6fa8`。
- [evidence/raw_response.npz](evidence/raw_response.npz)，SHA256 `512cf2c369e704efd1d1a4661c55da28aa175aecacb5ac74ed30bed79bee1aaf`。
- [evidence/first_bad_primitive.npz](evidence/first_bad_primitive.npz)，SHA256 `ebea330eabdf5edbf872dbfd22d61556e9722aa3d338c359c435938d648ede40`。
- [身份后审](actual_saved_review.json)，SHA256 `15dc387ba58866e7fffad8d65e08811284aac47c477805ea2903f878d55a78cf`；[独立保存primitive审阅](actual_primitive_review.json)，SHA256 `a88ffb28a760859801596c15772d48f31d7d64b37f55c8615b0941db6e319587`。

production内核仍为 `7fff354270a276764445b45a281a5924fd9f0356236b89e0dbd4f00088b383ce`。隔离 `1d18a5512396649200de908cc5106c17d7c9a9f7c3fa62ba518cbe7d5659517e` 未合入；所有旧科学证据、源capsule和闭卡脚本保持原样。

职责拆分的代码依赖与后续原门详见[机械接口计划](next_mechanical_interface_plan.json)。原图与修订图及真实render回执在[保存诊断视图](../../../functional_views/horner192_diagnostic_20261004/saved_002/README.md)，不重算力学。

后续状态补记：以上“尚未实施/执行”为本诊断关闭时的计划。随后新独立[mechanical-only卡已实际通过并合入可选API](../mechanical_only_candidate_001/RESULTS.md)，32测试和原F16 fresh力/Jv门通过；本诊断和旧完整入口失败的身份/范围没有改写。native_mean接入与新卸载路径仍未执行。
