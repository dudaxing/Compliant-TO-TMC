# M-AREF1：新 alpha 两个保存接受态的独立参考

状态：具体候选准备；未获本卡直接授权，未执行新 HP。不可变协议的 prepared=true、authorized=false、executed=false 是准备状态；实际批准和运行另存证据。

## 目标与最近取舍

整体目标是独立 HF 有限变形／TMC 前向评价：读取普通 LF 几何，在明确物理任务下给出变形、输入反力和可解释的工件作用，供外部研究层比较。HF 不优化、不调用 dmftd；MPM 暂不实现，开发继续在 main。science0.5.0、既定 origin 保持。

M-INTEGRATE1 已安装保存态续算默认入口，25 项有限兼容测试通过并闭卡。新 alpha=5e−7 的 M-RESUME1 两态短段已成功，尚无独立 HP；旧 alpha=1e−6 的 48 次参考不能转移。最近有用的步骤是在这两个实际保存态上核对力与切线作用，不重做约十分钟的平衡路径，也不开始新参数扫描。

本卡不是完整夹持功能验收。连续总压力、有效夹持、全切线列独立验证、稳定性、一般 LF 几何可靠性及 HF5 尚未完成。

## 冻结输入与原物理任务

仅 `saved_continuation_001/run_001/resumed_alpha_half` 的子态000／001，分别为原任务目标13／14，绝对平均输入1.20／1.15 mm。首态是非零峰值锚点，次态是首次下降接受端点。原 result、row、split、R、descriptor、父子身份及原图件均保持。

原 h0.5 mm、13440 单元、13689 节点、27378 DOF；固定1548／自由25830 DOF。E=1 MPa、ν=0.3、平面应变、厚度20 mm、gamma=1e−6、alpha=5e−7、Lr=80 mm。下半固定方形工件中心(71,40) mm、边长18 mm，648 单元／703 节点／1406 DOF；背景对称重叠37 DOF。原输入／输出均为五节点端口、权重[.125,.25,.25,.25,.125]，k_out=0，force_scale_per_length=20。

原 M-ALPHA1 仍 NOT_PASS／14 加载态／time_limit；M-RESUME1 仅短段 success。不得把父和子拼成原一次完整路径通过，不得把原 task_target_executed 或 full_original_path_completed 改为 true。

未来实际读取9个独立解码 NPZ：model27字段，每态state2、机械forces16、tangents3、CSC数值声明3，共75个descriptor字段。SciPy还读取两态CSC format/shape（合计79个必需成员）并探测可选 `_is_array`；这不是本轮已读数组的结论。aa86另外重复打开两态state／forces共4次、36个字段。另1份source_geometry NPZ仅原字节绑定，不解码／构模。准备期只读源码、普通JSON和文件stat，全部10份NPZ哈希从已发布manifest／原实际证据继承；授权后才逐一原字节核对和读取。

## 实现与科学门

新入口只负责真实输入装载、来源、索引、资源窗口和汇总。原 B850 `Audit.run_state`（SHA b850308dd35a0c74a42a1900bfb643cb9731fcb8ab6cb8e65a3cc7b2f87412b5）和 aa86 `WorkpieceCycleAudit.workpiece_checks`（SHA aa86bb162632f8c660ae0f547ad1ec16b9d655bcb99693b807381a6ddeafd938）原字节继承，不重写数学、归一化、散射顺序或门。原11份依赖按唯一basename平铺存档；import 会载入 JAX 并注册原jacfwd／vmap／jit／custom_jvp转换包装，不执行JAX本构核、AD求值、JIT编译或核执行。零AD／JIT执行计数不表示没有导入或注册包装。

按真实原任务索引13／14调用这两个方法，保留其原 `index==0` 未变形初态条件；不把子态000伪装成零初态。raw目录为accepted_013／014，raw科学summary保留13／14。仅新顶层summary复制元数据映射到子索引0／1，同时保留reference_execution_index、original_target_index和原child身份。本卡不调用 API 关联，也不改 reader。

每态新 HP80／120各一次，总计4次；覆盖全部实际13440单元、27378 DOF的总／材料／Hu局部与全局力，Decimal3000全局散射并trap Inexact，原均值／固定／平衡方程。方向取实际 `b_in/max(abs(b_in))`、固定分量0、deltaR=0，比较三分量方向切线作用、保存CSC作用、均值KKT作用。保存全局CSC逐系数重组身份仍检查；这不等于独立HP检查全部切线列。

复用同一独立力，核原signed total／material／Hu工件合力、去重holding分组、重叠、镜像和刚体dummy内部。原正则化Hu没有新的独立误差门；J/F/Hu rounded输出只作原诊断。机械辅助材料能量保持not_evaluated／unqualified／absent；独立解析材料能量仅归档，不进行候选能量或总Hu能量梯度资格比较。

| 原门 | 阈值 |
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

这15个原门使用原分母、原floor和原局部界，不能解释为标量工件力的相对百分比，不能增加地板或放宽。

## 一次资源窗口与停止规则

拟一次 helper900秒／outer960秒（16分钟）、采样8 GiB。包含import、输入原字节核对、读取、归档、4次HP、所有比较和终态证据写出。旧 M-REF2 24态／48HP 实测helper2067.2045279秒、outer2068.5294668秒、树RSS采样1398767616 B；没有逐态／逐HP耗时。新窗口是依据旧总量的保守规划，不是两态实测耗时或完成保证；内存不按态数缩小。

一次启动；首个终端错误停止，保留实际partial和真实started／completed计数。无测试、重试、修复重跑、延期、force、新生产F／T、构模、平衡求解或绘图。使用最早STARTED和最终写出后的检查，采样RSS／协作stop不是OS硬上限。原HP evaluate内部没有checkpoint，stop会在其返回后检查；只等待本次进程真实终止，超窗结果不得PASS，也不得把清理等待当新计算授权。

批准证据、协议SHA及已发布／独立恢复的源提交证据必须在导入科学入口前通过。原 M-INTEGRATE1 已闭卡，不能续用其时间额度。

## 输出、效果与后续判断

若通过，得到两个actual accepted-state独立参考，每态原fixture、HP80／120 local、global、element gates、equations、actions、重组CSC、rounded诊断、workpiece_checks及summary；顶层summary/lifecycle/来源/协议、outer回执和日志。若失败，只报告实际完成范围和错误，停止后根据新证据安排下一步。

新参考无论通过与否，都不能给压力、有效夹持、stress-HP、全部切线列、网格／域／参数稳定性、父14加载前缀、整个原路径或HF5授予资格。不生成新图；现有2态实际变形GIF与三PNG继续供人工对照。实际HP结果产生后，再决定两态参考关联与有符号作用可视化的最小下一步，另立范围与资源。
