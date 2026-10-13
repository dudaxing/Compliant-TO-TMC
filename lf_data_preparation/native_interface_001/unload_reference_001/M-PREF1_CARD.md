# M-PREF1：卸载 0.90／0.80 mm 两保存态独立参考

2026-10-13（Asia/Seoul）。当前为源准备：本卡尚未授权或执行。M-UNLOAD2 已保存卸载至输入零的九态，M-PATH1 已实际完成二十五目标统一读取、逐点索引和两张曲线。基线 main `eb92b41fd58547640d2c2a8381f98aa5012154df`，新科学窗口须取得直接批准。

## 整体目标、当前进度与本步作用

整体目标是独立 HF 读取普通 LF 几何，完成有限变形／第三介质接触（TMC）前向分析，给出反力、位移、固定工件作用、可恢复状态和可检查变形，供外部研究层使用。HF 不优化、不调用 dmftd；MPM 尚未实现，继续在 main 开发。

现有默认入口已实现从零求解、保存态续算与显式延伸；本模型的实际保存段已覆盖加载及卸载至零，统一显示保留原首段 failed/time_limit、各源版本与精确锚点。已有独立参考覆盖另两个结果的 1.20／1.15／1.10 mm 三个状态，不能迁移到新来源或授整条路径资格。

本步只核卸载 0.90／0.80 mm：原保存下半工件 signed Fy 分别为 0.019843004460390452／0.0023451588658585914 N，有限底边间隙分别为 0.006536020506683116／0.06488253685016332 mm。作用与距离变化显著，先验证这两态的原力、分量和同一 PORT 方向切线，才据结果解释卸载行为。无需重复平衡求解或原变形图。

## 唯一输入与物理条件

来源 `../saved_extension_004/run_001/unloaded_alpha_half/result.json`；只选择 child 2／global 18／d=0.90 mm 和 child 3／global 19／d=0.80 mm，均为 unloading、原目标、非 continuation anchor。state SHA 分别为 `fa1cffaa2d9911c01752d702ab7cbc91d048b2c41a2f701d555953f91c7e598f`、`8b834bcae162345adb6036970a91ccbb427455f84a07b2bdb0e111ee05db437a`。原生产九态、完整二十五目标、成功父链及深层 failed/time_limit 祖先保持。

保持 h=0.5 mm、下半域 84×40 mm、13440 单元／13689 节点／27378 DOF，固定1548／自由25830；E=1 MPa、ν=0.3、plane strain、厚20 mm、γ=1e−6、α=5e−7、Lr=80 mm。固定方形工件中心(71,40) mm、边18 mm，五节点端口、原权重及 k_out=0 保持。任务、几何、设置、数组、力核、切线、默认入口、结果和资格均不修改。

最小科学输入为10份 NPZ：共享 model／source_geometry，每态 state／forces／tangents／CSC 各四份；未来解码九份，source_geometry只绑定原字节来源。75个不同 descriptor 字段，CSC另有每矩阵 format／shape 两必需成员及原可选 `_is_array` 探针；原 aa86 逐态重开 state／forces，合计13个数组 loader、111次声明字段读取（含 CSC 必需容器成员为115）。准备期只继承已闭 producer／manifest 的身份并核 stat，不读数组、header 或科学字节。

## 原数学与十五门

原 B850 `CoreAudit.run_state(18,row2)`／`run_state(19,row3)` 与 aa86 `WorkpieceCycleAudit.workpiece_checks` 全字节继承；11依赖按唯一 basename 平铺，另归档本卡 driver 与纯 plot。原 imports 会加载 JAX、注册转换包装，不执行 AD、本构 JIT 或生产核。

每态新 HP80／120 各一次，共四次，覆盖全单元／DOF，核材料／Hu／总局部及全局力。Decimal3000散射及 Inexact trap 保持。方向为原 b_in/max(abs(b_in))，固定分量0、deltaR=0；核同一 PORT 方向的三分量切线作用、保存 CSC 逐系数组装身份及方向作用、增广 KKT 与工件原投影／去重／镜像检查。完整 CSC 身份不等于独立验证全部切线列。

| 原门 | 原阈值 |
| --- | --- |
| production_residual | 1e−9 |
| independent_residual | 1e−8 |
| force_evaluation | 1e−9 |
| average_constraint | 1e−10 |
| global_force_balance | 1e−6 |
| fixed_displacement_mm | 8e−11 |
| hp80_hp120 | 1e−40 |
| total_force | 1e−11 |
| material_force／regularization_force | 各1e−9 |
| total_tangent | 1e−10 |
| material_tangent／regularization_tangent | 各1e−9 |
| augmented_force_tangent／augmented_constraint_tangent | 各1e−10 |

原分母、floor、局部规则与投影顺序保持；工件误差使用原全域力／分量尺度，不是工件 Fy 相对百分比。rounded F／J／Hu 仍只作原诊断；独立解析能量仅归档，机械候选辅助材料能量 not_evaluated／unqualified／absent 保持。

## 一次显示与实际记录

全部原参考门和来源检查通过后，纯 plot 一次仅读本次新 `accepted_018/summary.json` 与 `accepted_019/summary.json`，生成一张双面板 `reference_observations.png` 与普通 JSON。各面板标明真实 child 2／3、global18／19和绝对 d，配套 JSON 保存完整 state SHA；显示原10项 error／limit：三全局力、三 PORT 切线作用、CSC／KKT 作用、HP120 平衡残差及 HP80／120 总力一致性。Decimal40 的 log10 比值只作显示；精确零单独标注，不加 floor 或新验收门。十项图示不代替完整十五门。

保存原 fixture、HP local／global、element gates、equations、actions、重组 CSC、rounded诊断、工件检查、raw 与两选点顶层 summary、source archive／protocol／lifecycle。raw accepted_018／019 保持；top index／child_accepted_index 保留2／3，另记 reference_execution_index18／19，不伪装成0／1初态。失败保留真实 partial、错误与 HP／mechanical／body／plot 计数。

新 PNG 产生后，记录阶段最多一次像素检查／展示；不重绘或读取旧媒体。已有实际变形和全路径曲线通过相对链接供对照：[M-UNLOAD2 实际结果](../saved_extension_004/RESULTS.md)、[25点统一显示](../../../functional_views/native_alpha_composed_20261013/complete_001/RESULTS.md)。

## 新资源与首错规则

一次 helper900秒／outer960秒（最多16分钟）、采样8 GiB。最早 clock 后包括批准／来源核对、imports、数组读取、13份源码平铺归档、四次 HP、全部比较、Matplotlib import／一次绘图、产物身份和回执。已闭两态四 HP 实际 outer193.3503027秒、一态两 HP99.3701711秒仅为规划依据，不保证本次成功或耗时，不沿用旧窗口。

一次启动，首个终端错误停止，保实际部分证据；无测试、修复重跑、外部重试、延期、force、新生产 F／T、构模、平衡求解、API关联、reader修改、安装、回滚或删除。采样 RSS／合作 stop 不是 OS 硬限制；原 HP 内部无 checkpoint，返回后检查并等待真实退出，迟到 PASS 不通过。plot失败也整体 NOT_PASS，闭窗不补图或科学 hash。

## 资格与结果分支

此卡只授所选两态四 HP及参考误差显示。公共 reference reader仍要求本 result 全九态／18 HP；本卡不能 matched全九态，不放宽 reader或升级完整原／延伸／组合路径、连续压力、有效夹持、完全释放、稳定性、全列切线、一般 LF 或 HF5 资格。输入到零仅完成目标，不等于物理完全释放。

通过后，结合已有二十五点力／距离／变形和这两点参考作具体物理判断，再确定下一项功能缺口；失败则依据本次实际证据排查，另拟具体修复范围，不静默重跑。准备静审不替代四次实际 HP；批准前不启动计算。
