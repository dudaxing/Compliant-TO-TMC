# F16机械量入口：实现、实际对比与合入

新显式NumPy机械量入口及force-only组装器已按验证的原字节合入。32/32测试通过；原F16新三力、缓存机械切线及声明方向的fresh HP80/120对比全部满足原门。最大归一误差7.24335987355e-15，HP80/120最大相互误差1.21169345815e-52。本卡没有执行新的平衡路径，粗方0.5mm卸载仍未完成。

## 整体目标与本步作用

项目目标是与LF优化解耦的HF正向评估器：普通几何/任务输入、非线性TMC力和切线、平均驱动加载/卸载、工件反力、接触相关量及实际可视化。HF不包含优化，也不调用dmftd或MPM。用户授权按对称半工件探索方形/圆形和更大行程；当前先处理已暴露的返零算术问题，随后按实际结果扩大行程。

原循环003的[0,.5,0]mm路径在预算内只保存初态/峰值；完整F16及后续T25出现范围拒绝。Horner192共尺度候选测试包装001先在收集前失败；新002的25例通过，但完整F16仍失败。独立诊断定位能量平方回缩的DD低字下限：48积分点/35单元，最终能量35NaN；原始三力及运动学有限，却没有数学资格。这些闭卡失败均保留。

材料辅助能量在机械三力之后独立计算；现有mean回溯使用增广残量平方，缓存切线是实际机械残量的导数。能量并不参与这两个计算。因而本步显式拆分机械响应职责，同时保持旧完整入口的能量要求；没有把NaN替换成0、忽略旧完整支持标记或删掉DD项。

## 实现与代码对照

在[split_kernel_invariants_hu.py](../../../hf_repo/src/hf_eval/split_kernel_invariants_hu.py)增加：

- `batch_response_split_mechanical_numpy`：返回三力、P/S、F/J/G/Hu/B/delta及保留的high/low pairs；不计算、不返回`material_energy`。
- `assemble_split_mechanical_numpy`：复用原global力散射和计时，返回`(None, internal, fields)`；不自行计算切线或启动求解。

机械支持标记由原运动学/系数、机械输出DD pairs及T/log_J/exponential/Hu-action检查构成；正J、float64、finite、原CI支撑域与全部四项乘积保留。默认完整NumPy/JAX仍计算并检查辅助能量。独立逆向AST与基线7fff完全一致，原KERNEL_VERSION保留，机械入口单列`MECHANICAL_KERNEL_VERSION`。

新验证包明确`response_contract=split-numpy-mechanical-1.0`和`auxiliary_material_energy={status:not_evaluated,qualified:false,field_present:false}`。native_mean/controller、legacy指标和原native结果格式没有接入该可选入口；不能把旧需要能量的读取器直接接到新省能量字段集。

核心新SHA为`d5f7d20a6ec0c92847d67f8782f4dcc89772fc4ea62797626b0beae7effabd9a`。它从7fff构造，未复用失败的1d18 Horner组织。验证时production仍7fff；独立后审及实际保存图完成后按原字节合入新API和[7项focused测试](../../../hf_repo/tests/test_split_numpy_mechanical.py)，没有额外数值重跑。见[promotion.json](promotion.json)。

交付勘误：冻结`runtime_origin.json`的`kernel_version`与`description`沿用了上一Horner作者标签，描述不准确；其机械schema、d5f7 SHA、42件source地图与实际入口正确。原文件按封存原字节保留，不能依据这两个文字标签选内核。实际源码常量为完整入口`p26_q1_split_invariants_hu_matmul320_candidate1`及新机械入口`p26_q1_split_mechanical_numpy_aux_omitted_candidate1`；promotion记录列出实际版本及旧标签局限。此勘误不改变数据、源、数值调用或数学门。

## 输入、门与实际执行

原16字段F16 input SHA47824b…8248e、split state9dbd3c…764e2、27字段模型a2d6e1…66049均保持原字节。3200单元/6642DOF/376fixed，h=1mm；固定半方形工件side16mm、中心(70,40)mm，初始间隙2mm。方向复用固定DOF清零的全域dyadic witness，3072非零单元覆盖旧26及后续35失败单元；原端口方向另行保存。

原门：total力1e-11、total Jv1e-10、material/Hu各1e-9，HP80/120一致性1e-40。Et20按原native规则派生返零floor2e-13N，component力分母为max自身参考norm,1e-12总scale)，Jv分母max自身norm,1e-10N/mm)。未改门、模型、方向、网格、材料或fixed集合。

| 阶段 | 实际调用/结果 | helper秒 / outer秒 | helper / outer采样峰B |
| --- | --- | --- | --- |
| unit | 32收集/启动/通过，0failed/skipped | 5.59426339995116 / 6.02861809998285 | 158760960 / 157462528 |
| candidate | 1F开始/完成、1缓存T开始/完成、3consumer开始/完成；pass | 34.304839099990204 / 35.23666819999926 | 785612800 / 781123584 |
| reference | fresh HP80/120各一次，2开始/完成；pass | 29.701445399958175 / 30.119989799975883 | 422068224 / 426860544 |

各阶段实际exit0，372项protocol绑定前后同，无外部stop。helper/outer覆盖范围与采样方法不同，分别保留。原测试20例不变，原3 primitive+2未选分支断言只适配来源身份，新7例检查省能量/旧完整finite拒绝/不调用编译/near与direct机械字段字节一致/输入J与形状门/组装和状态不变。测试内toy力学调用未单独计数，不能统称为0；本卡没有新增物理生产路径。

候选保存25字段完整机械响应、3份即时T字段、40字段combined数组和3个完整6642×6642 CSC（各nnz116644）；固定行列保留，未对称化。独立参考逐项比较19200局部门和9全局门，覆盖全部单元与DOF；614400个局部T系数按独立索引方式核对CSC组装身份。独立后审复核所有19209个保存差值与HP字符串的norm/分母/门一致，没有再次计算本构或组装。

| 量 | 本次最坏归一误差 |
| --- | --- |
| total力 | 3.21910431899e-32 |
| material力 | 3.15753049751e-20 |
| Hu力 | 8.10228034996e-22 |
| total缓存Jv | 7.24335987355e-15 |
| material缓存Jv | 1.16023882344e-16 |
| Hu缓存Jv | 1.01065556074e-16 |
| total CSC Jv | 1.54354609741e-16 |

HP80/120最大差异1.21169345815e-52低于1e-40。力标度floor较实际微小内力大，误差按原分母解释，不能把这些数写成无floor的相对误差。参考程序附带保存analytic材料能量，但没有candidate能量对比或能量资格。

## 实际可视化与物理含义

[三力和方向内力变化率图](../../../functional_views/mechanical_F16_20261004/saved_001/render_001/mechanical_F16_qualified_fields.png)来自保存数组；上排三力共N色阶，下排Jv共N/mm色阶，覆盖3200单元。真实max位移分量3.40787911055e-28mm，图使用参考坐标，没有放大微小试算态为加载形变。总局部力max约2.0831e-29N，总方向内力变化率max约50.995N/mm；前者是该态内力，后者是沿声明方向的线性化响应。

本视图唯一渲染exit0/pass，outer2.7021155999973416秒、159039488B，80项绑定同；无新F/T/consumer/HP/scatter/solve/距离计算。全3200行14字段CSV保留实际范数与原Decimal误差，显示下限不改CSV。见[元数据](../../../functional_views/mechanical_F16_20261004/saved_001/render_001/view_metadata.json)与[CSV](../../../functional_views/mechanical_F16_20261004/saved_001/render_001/mechanical_F16_element_values.csv)。

实际0.5mm峰值变形、输入力与失败时序仍见[循环003 ×1图](../../../functional_views/native_workpiece_cycle003_20261004/failure_saved_001/render_001/cycle003_failure.png)：R_input=.106253247986N，自由+y输出=.575755712293mm，minJ=.735764774113。它的2个接受态尚无freshHP，本卡单态资格不转给该峰值或卸载。

## 效果、限制与下一步

本步让原F16机械三力及方向切线作用得到真实返回并通过原独立参考门，解除该保存试算态的辅助能量耦合阻断。支持范围仍是这份原F16、声明方向和已运行回归；不是全部切线列、P/S的HP资格、能量资格或接受平衡态。

下一唯一近期功能是把新可选合同接入native_mean持久化与缓存组装：显式记录能量不可用、省能量字段集和机械source版本，保持控制器/Armijo/KKT原式及旧默认格式。先小闭环检查，然后单独新卡探索同一粗方[0,.5,0]路径，原失败不重开；依实际新结果定位仍可能出现的T25类问题。只有新路径和新接受态参考通过，才扩大到1/2/3mm及细方/圆形工件。一般接触、压力/有效夹持、自由工件、H2/H3/HF5和完整AD/JIT仍未完成。

资源卡为unit60/90、candidate90/120、reference180/210秒，每阶段采样树8GiB，含导入/计算/保存/身份检查。阶段各一次，首错停止，不force、延时、重试；协作检查和采样不是OS硬限。此新增职责合同没有放宽旧完整入口的门。

## 原始证据

- [冻结新卡](README.md)、[core差异](core_delta.diff)、[核心静态数学审阅](core_math_review.json)、[验证器数学审阅](validator_math_review.json)。
- [测试结果](unit_tests_result.json)、[candidate](check/candidate/result.json)、[reference](check/reference/result.json)，含完整原输入/来源capsule/所有比较结果。
- [实际保存身份后审](actual_saved_identity_review.json)、[实际数学后审](mechanical_actual_math_review.json)。
- [旧001启动失败](../horner192_candidate_001/RESULTS.md)、[旧002完整力失败](../horner192_requalification_001/RESULTS.md)、[范围诊断](../horner192_range_diagnostic_001/RESULTS.md)。

交付检查：正式源/文档的`git diff --cached --check`通过；单独封存的unified diff数据中13个空上下文行按diff语法保留单空格标记，通用空白检查会报告这些格式行，检查时只排除此数据文件。未改其冻结SHA或关闭源码检查。
