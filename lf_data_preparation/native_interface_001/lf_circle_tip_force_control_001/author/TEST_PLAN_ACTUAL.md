# L-CTIPFLOAD1 新测试的实际有限清单

2026-10-23。本说明对应候选 `D:/hfl1_001/candidate/hf_repo/tests/test_native_guided_force.py`；目前仅完成源码编写、AST解析与人工静核，**没有导入HF、没有pytest collect、没有启动科学路径**。最终SHA由root冻结清单绑定。

## 方法、分支、路径分开计数

新增文件有8个普通非参数化测试方法，不使用 `pytest.mark.parametrize`。与原 `test_split_displacement.py` 的9个展开项合为未来唯一17项。新控制调用上限不是8：实际预定为30次；原11个synthetic调用另列，全部运行成功才可合为41次。首错时计数保留实际已尝试数，不预写全部通过。

|方法|有限控制调用|新真实路径|检查的实质|
|---|---:|---:|---|
|非对称独立dense oracle|1|0|body→free和free→body都非零且不互转置；独立6×6 dense方程与未知q/R/全场；工件合力求和、符号与half/full换算|
|fresh锚点|4|0|正确锚点接受一次后用synthetic callback typed停止以禁止下一步；坏R、坏mean、坏P0各一次fresh失败；均无linear/trial/修复，split/R身份|
|真实q↔P交叉|0（共享fixture）|3|全新16格固定父 `[0,.0005]`；现有位移probe `[0,.00025,.0005]`；新力控仅输入三个本次Q，独立从同父求未知q|
|缓存／分量／账本|0|0|只复用共享路径缓存；NPZ及字段SHA，total/material/Hu重组，厚度一次，显式P替代body-x支持，body-y背景重叠去重及全局账本|
|受控真实partial|1|1（与控制调用重叠）|同新父；第2次真实tangent调用前注入 `constraint_failure` 终端错误，保首态／实际文件／split/R；不是物理奇异或承载极限|
|五种身份错误|5|0|从新父副本分别破坏source/model/task/lift/fluctuation；F/T前拒绝，拒绝后原副本字节不变|
|有限设置／输入／冲突|17|0|4个N设置值（0/负/NaN/Inf）；5个载荷向量（空/单项/NaN/重复/递减）；4种spring/input/output/support冲突；3种clock/已存输出/父树内输出；1个新父副本unsupported response_mode|
|原代表性代数|2|0|原fixed非零body lift保护和原规定q的常量机构mean代数不变|
|合计|30|4|无full/chunk隐含双跑、无额外科学路径|

原模块另有1条2格真实路径／11个synthetic调用。因此完整授权清单上限为新4＋旧1＝5条真实路径；新30＋旧11＝41个控制调用，小于32／43上限。受控partial在两个维度各记一次，不重复描述物理覆盖。`call_counts.json` 的新数字在每次调用前递增；旧11／1仅标为静态基线，是否实际全部通过由root唯一pytest JUnit证明，fixture不能自行声称17 PASS。

## 真路径与后处理

全部新真实路径来自本次生成的4×4／16格／50DOF几何，参数与原probe fixture一致；不读历史NPZ。父和probe原mm步长 `.0005/16` 保持。只有三个原Q均有限、Q0非零、严格递增才进行力控：`minimum_force_increment_half_N=min(diff(Q))/16`。不反号、不改点、不放宽规则。各新增真实controller固定60秒，旧真实15秒不改。

真实回归门：q绝对差和全物理位移max差各≤1e−8 mm；R差≤max(1e−12 N,1e−7×abs(Rref))；原自由残差、机构mean、正J、刚体误差、全局平衡及新增独立g门全部分别检查。fresh仅一检查且split/R逐位保持。不同求和顺序只使用原局部L1的8eps界，无地板；不代替非线性门或q门。

conditioning诊断只在共享力控路径的 `_linear_solve` wrapper读取本来已组装的37×37矩阵并计算2-norm cond，保持调用原LU一次，记录既有predictor解的dq/dP。不新增F/T、另一个FE路径或方向差分；mixed-unit condition仅描述，不用于稳定性／唯一性资格或修改验收门。

`FLOAD1_ARTIFACT_DIR`由root冻结为 `D:/hfl1_001/run_001/artifacts`。输出 `call_counts.json`、`validation_summary.json` 与阶段 `index.json`；顶层提供parent/probe/force/partial的实际result路径、原载荷、N与mm步长、cross_checks及诊断。partial注释明确注入性质。session fixture即使首错也写实际进度；root只有在唯一pytest 17项全部通过后才认旧回归通过。viewer只读这些本次普通JSON，不需二次F/T或NPZ。

## 静态核查范围

候选恰好8个测试方法；不存在参数化装饰器或test函数内部递归；共享fixture恰好一次parent API、一次displacement probe API和一次force API；partial方法另一次force API。有限循环的30次按上表人工逐分支核对。AST成功不代表实际通过，最终独立静审及唯一受控运行由root安排。本文件不授权执行。

首次运行前静审消歧：末项选择旧位移controller的基础字段 `q_in`（机构mean）和 `d`（probe参数q）。旧controller的probe分支也提供同值 `input_mean_mm`／`body_q_mm` aliases；最初对aliases缺失的怀疑经补读原分支已撤回，不作为实现缺陷。仅本新测试读取键改为基础字段，旧源码字节不变。独立静审补齐原方案第7项未支持模式的明确分支：仅本次新父副本response_mode改变及重hash，F/T前拒绝并核源字节不变。新控制清单29→30（仍≤32）、方法8及真路径4不变；这不是运行后修复或重跑。

最后一项静审证据补齐：受控partial调用的父树保持不变由调用前后本次新父缓存字节SHA比较实际决定，注释写该布尔并断言；不预填 `unchanged_parent=True`。仅加强同次证据，不增加控制调用、F/T或真实路径。
