# L-CTIPFLOADPREP1 正式规格最终数学复核

2026-10-23。仅对正式准备目录 `lf_circle_tip_force_control_preparation_001` 中 TASK_SPEC.md、SMALL_MODEL_VALIDATION.md、API_DESIGN.md、author/REVIEW_DECISIONS.md 做有限只读审阅，并以原源码核符号及源尺度。未改正式文档，未打开图像或科学数组，未导入生产模块、测试、力／切线／HP或求解。

结论：**无阻断本轮准备交付的数学、单位、预载或验收合同不一致。** 这只表示静态规格一致，不授新功能实现、数值正确、唯一性、稳定性或承载资格。

|有限核查项|结论与依据|
|---|---|
|1 工件与机构力符号|PASS。原残差为f_int−bR；ON-body=−Σbody f_int，故g=Σbody f_int,x−P。R始终独立于P。|
|2 未知量／虚功|PASS。原free波动w、一个刚体q、机构乘子R；c为body-x上的1，不作节点平均，不把总P重复施加。|
|3 重排Jacobian|PASS。规格未知(w,q,R)及行(r_w,g,h)是原审阅(w,R,q)的等价重排；负输入列、正均值行、两向独立耦合正确。|
|4 非对称性|PASS。SᵀKc与cᵀKS分别装配，保一般LU，不对称化或增加隐蔽正则；不作能量极小／稳定性推断。|
|5 预载|PASS。LOW1的P0/P1为绝对有符号总载荷，ΔP另列；fresh锚点检查1，无投影／纠正，原状态/R逐位保持。P0可在预定门内匹配Q，但不偷偷改P0。|
|6 half／厚度|PASS。半模型N已含厚度，完整轴向力2×且q不倍增；API只收half N。源native_project.py:280明确force_scale_per_length=E*thickness，F_floor维度为N。|
|7 新旧残差门|PASS。原r_w/SF门独立保留，新增g/SP≤1e−9；SP以总P和锚点绝对力及原N floor确定，不被较大输入R淹没。不是旧HP十五门。|
|8 回溯与最小步长|PASS。同次trial固定SF_base及目标SP，merit含自由平衡和广义合力；仅port做均值可行投影，不夹q。N最小步长独立于原mm设置。|
|9 全局账本|PASS。显式P替代旧body-x处方支撑，body-y／背景重叠去重；全局平衡与g各过门，不用任意节点分配声称压力。|
|10 最小路径范围|PASS。有符号绝对P允许，首版仅严格递增；q是有符号未知且无暗夹限。未预授卸载、循环、续算或任意分支。|
|11 有限验证取舍|PASS。双向非对称dense oracle检新增reduced装配；真实q↔P从同一q0独立求解。此次不新增FD／HP，与原力核和切线不改及有限调用预算一致；如未来发现缺口，应新立验证而非暗增调用。|
|12 回归与失败界限|PASS。1e−8mm的q／全场界值明确为预声明功能回归精度，附conditioning诊断，未冒称严格误差界。各类失败保真实partial、不得临时放宽。|

小模型成功仍是后续待验证命题：位移probe得到的Q0非零、Q0<Q1<Q2是明示前提，当前未计算也未保证；若不满足应按规格停止，不能反号或重挑参考。新的精确调用数、源SHA、唯一命令和资源余量仍须候选实现／静审冻结，本轮准备文档本身不构成运行许可。

本次有限审阅不重新计算LOW1原值，也未用严格误差上界为功能门背书。后续若功能门失败，应保留原界值和真实结果，依据conditioning／块残差定位原因，再决定是否另立修正卡。

## 发布前补记：显式全局门公式

仅只读核查TASK_SPEC.md新增全局门段落（D／s_D／G／S_G）。**PASS，无阻断。** D取原fixed去body-x，且body-y与zero用集合去重；s_D=f_int−bR只取D，与显式(P_half,0)组合后不双计原body-x驱动力。S_G使用N量纲的各外载向量Euclidean范数合和及原S_F地板，relative门仍为1e−6。

在本范围k_out=0、b在body上为0、内力平移合和为0的物理恒等式下，该G等于 `−sum_xy(r_w)−(g,0)`，符号与独立广义门一致；保留G作为单独外载闭合检查正确，不需任意body节点外载分配。未重做其他审阅，未读取媒体／科学数组或执行运行。
