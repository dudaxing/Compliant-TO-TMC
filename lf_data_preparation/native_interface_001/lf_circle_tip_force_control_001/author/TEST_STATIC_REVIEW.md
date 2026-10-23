# L-CTIPFLOAD1 新测试独立完整静审

2026-10-23，`/root/fload_api` 审阅非本人编写的 `test_native_guided_force.py`。仅逐行读源码及 AST，不导入 HF、不 pytest collect/run、不求解或生成几何/科学数组、不读取历史 NPZ。最终被审候选的 SHA/字节见同名 JSON。

结论由同名 JSON 的最终状态和绑定 SHA 指定。本报告逐项覆盖批准的 SMALL_MODEL_VALIDATION，而不只核测试数量。

|项|静审内容|判断|
|---|---|---|
|1 方法与唯一目标|新文件恰好 8 个非参数化 test 方法；旧模块 8 方法中均值算术一个两展开项，共旧 9＋新 8＝17。没有新参数化/递归或收集时路径调用。|静态通过；实际 17 PASS 仍需唯一 pytest 回执。|
|2 动态计数|新 COUNTS 初值零；真实路径与注入/拒绝在实际调用/尝试前递增。PASSED 仅各方法断言末尾追加，非预写通过。旧 1/11 标静态基线并要求唯一 pytest 回执，未冒称实测。|静态通过；首错保实际已尝试数。|
|3 精确覆盖上限|dense1＋fresh4＋受控partial1＋source5＋设置4＋载荷5＋冲突4＋clock/output3＋unsupported mode1＋旧代表代数2＝新30；旧synthetic11另计，共41≤43。新真实父/probe/force/partial四条，旧两格真实一条，共5；partial在双轴标重叠1。|静态通过，8/30/4不是实际已完成量。|
|4 新鲜16格fixture|4×4 Q1/25节点/50DOF，域2×2、h.5、E1、nu.3、t2、gamma1e−6、alpha1e−4、Lr2；掩码、端口、支撑、圆r.375/center1.25,2与批准模板一致；body14及nodes17/18/22/23，body-y/background45/47去重。|静态通过；没有读旧科学数组或换正式r9参数。|
|5 前提与路径顺序|新固定父[0,.0005]完整成功才probe；probe原q=[0,.00025,.0005]，仅三原Q有限、Q0非零且严格递增才力控。从同一固定父，仅给P=本次Q求未知q，不热启动位移终点或传预期q。N最小步长min(diffQ)/16，mm步长另记。|静态通过；前提不满足即断言停，不反号/改点/重试。|
|6 独立非对称oracle|dense方程用完整显式matrix、shape及free独立组块，两个耦合方向均非零且不相等，比较w/q/R及全体body平移；body合力求和不能平均，half/full换算不另乘厚度。|静态通过；rtol1e−12/atol2e−14明确。|
|7 fresh一检|正确锚点由callback接受一次后typed停止，防进入新predictor；坏R/mean/P0各fresh一检查失败，所有变体禁止_linear_solve、无trial、仅一次tangent，split/R位身份核查。|静态通过；synthetic callback time_limit是受控信号，不是实际时限超耗。|
|8 真实q↔P门|所有实际原目标与内部态分别检查free/g/mean、正J、global、rigid/zero；只对原三P配对参考。q与全位移差≤1e−8mm，R≤max(1e−12N,1e−7absRref)，未根据结果调门。|静态通过；fresh额外比原split/R字节与checks1。|
|9缓存与分量|仅本次state/fields NPZ逐文件/逐字段身份与dtype/shape；material/Hu/total节点与局部重组，只有不同求和顺序使用8eps×对应局部项L1无地板；save F/T和HP=0、solver1。|静态通过；不拿重组界代替求解/交叉精度门。|
|10半模型载荷与账本|E*t=2N/mm断言确认厚度一次；显式(P,0)数组与账本、body-y guide、排除body的zero支持、fixed−body-x闭合核对；无body_x_drive重复项，global尺度单独重建。|静态通过；不分配虚构节点P或压力。|
|11受控真实partial|只新force API一次；真实_tangent第1次正常，第二次前注入constraint_failure，确认两次尝试、首accepted缓存/原split/R、rollback、失败result.json与实际父树前后身份。|静态通过；是持久化注入，不是物理奇异或失效载荷。|
|12五种来源拒绝|仅新父副本分别破坏source/model/task/lift/fluctuation；该轮重建普通身份使错误落到所需层次，四个F/T入口禁止，拒绝必须invalid_saved_state且副本字节不变。|静态通过；不读旧归档。|
|13有限输入及模式|4设置值、5载荷向量、4约束冲突、clock/两输出目录规则及unsupported父response_mode均有明确预期typed错误；冲突/模式在F/T前拒绝。|静态通过；全部有限，无额外真实路径或通用枚举。|
|14旧接口与字段|fixed非零body lift保护、旧规定q/常量mean代数；末项使用旧q_in/d基础字段。已核旧probe分支同时给等值input_mean_mm/body_q_mm aliases，初审“alias缺失”预警已撤回，不是旧实现缺陷。|静态通过；旧55源码不改。|
|15conditioning与资源|wrapper只取原已组装37×37 augmented做2-norm cond，调用原LU一次，dq/dP由该次已求解向量读取；无额外F/T/导数。新增真controller60s，旧真实15s；CPU/full、无chunk双跑/GPU/HP。|静态通过；mixed-unit conditioning只诊断，不授稳定性/唯一性。|
|16实际产物与显示输入|index/validation_summary顶层记录parent/probe/force/partial路径、原P/步长、cross_checks、conditioning；各阶段路径后才更新实际状态。纯viewer可读本次普通JSON，测试不绘图/打开旧媒体。|静态通过；最终成功以JUnit＋全部实际门为准。|

## 首次启动前的取舍

逐行核查发现原清单漏“未支持模式”反例，作者已在同一个第7方法增加一次父response_mode拒绝，实际新计数由29调整为30，仍在已批准32上限内、8方法和4真实路径不变。另将partial的`unchanged_parent`从预填true改为当次父树前后真实字节比较。这些只在唯一首次运行前修改新测试，未运行后修复或改旧实现。

reviewer曾因只读旧measure主字典而怀疑旧probe接受记录缺少两个aliases；补读原advance的probe分支后立即撤回，ROOT与候选旧SHA相同。作者选q_in/d等价基础字段可以保留，但不得将其写为修复旧API缺陷。

本静审不能预证明真实fixture的Q前提、实际收敛、17项通过或资源充分；若唯一实际运行首错，必须依卡停止并保真实partial，不得借本报告重试或改门。
