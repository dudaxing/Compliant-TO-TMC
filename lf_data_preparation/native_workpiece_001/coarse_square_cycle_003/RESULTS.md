# 新matmul320三点循环：实际失败、保存诊断及下一步

整体目标是独立HF力学评估器：普通几何和明确物理任务进入NumPy完整力、非对称切线、CSC组装、平均端口平衡，获得真实结构变形、方向/单位明确的端口力和工件力，再探索对称半工件夹持与卸载。HF不含LF优化器/MPM；研究层可使用HF结果比较候选。用户授权Agent选择对称圆/方工件和更大行程，要求功能优先、逐步实验、可视化与完整可审查记录。

## 为什么进行本轮

旧31d955来源的七目标.5mm循环已实际完成，七态14次fresh HP通过，但卸载包含范围拒绝。其第一保存F36的S=T^T P微小乘项已定位；matmul320隔离候选7fff及29行补偿保存K作用入口B52，分别经过23功能测试和19200局部＋9全局原门的保存数据重新验收。该资格只能用于该捕获F36/声明方向，不能给新循环或任意输入。

本轮将7fff候选原文件字节合入live核心，只改变原候选的VERSION/说明和矩阵乘法±192→±320；CI域、物理公式、控制器、切线/组装、门与compiled默认选择均未切换。原49/57来源副本及旧参考失败保留。将先前七目标新循环计划明确修订为[0,.5,0]mm三请求点，以直接检查新峰值和连续返回；所有实际二分接受态仍须保留，初0/回0不得去重。这是新的路径选择实验，不能与旧七请求点作受控内核性能比较。

## 实现与冻结

新来源63、输入25、生产协议166绑定；静态数学/功能审阅和实际准备审查均完成。固定方形side16mm、中心(70,40)mm下半模型、初始底/左2mm，h1mm/3200E/6642DOF/376fixed/6266free。E1MPa、nu.3、plane strain、厚20mm、gamma/alpha1e-6、Lr80mm、0弹簧，原PORT方向和.00625mm最小增量保持。保存模型全部27数组与原archive a2d6逐字段dtype/shape/bytes相同。

新阶段包装沿用连续w/R/K、signed predictor、原回溯与二分；只增加原范围拒绝的首次输入保存，不多算力学。私有参考Core仅改保存K作用消费者及范围说明，数学AST保持；因生产失败，本轮该Core和参考阶段均未执行，0新HP。

## 实际结果：正式生产未通过并永久关闭

真实退出码1，result.failed/time_limit。整体helper 606.703923100s超过600s，outer 607.601635800s在660s内；过程peak_wset/RSS峰967733248B、外采样树峰890851328B，均低于8GiB。前者含进程峰记录，后者是离散当前RSS树采样，二者不可混称同一指标。外stop为空，全部冻结来源/输入不变；末尾通用错误字段不意味着源码改变。协同检查是在完整内核/组装之间执行，实际超时保留为失败，未延长预算或force。

只保存两个接受态[0,.5]，loading_peak_reached=true，path_completed/unload_endpoint/task_target_executed=false。峰值R_input=0.10625324798554087N、自由+y q_out=0.57575571229330891mm、minJ=0.7357647741129798，生产相对残量4.2710255520159611e-13。下半工件受力ON body=(Fx,Fy)=(-0.00015041241380519055,0.00013418331356361489)N；材/Hu分量及支承/端口全量缓存保存。工件受力是holding反号，完整镜像净力(2Fx,0)与2|Fy|派生数不同，不能当压力或有效夹持。新两态没有fresh HP资格；数值接近旧峰值不转移旧资格。新几何边距未测量，图中节点窗口只为代理；旧源已测峰值真实底边距离1.471935964mm仍为独立旧证据。

完整对账见[失败包身份审阅](cycle003_failure_fixture_review.json)及[失败时序审阅](cycle003_failure_chronology_review.json)：66F开始/50完成、27T开始/26完成、1solve、0HP/JIT/保存F/T；66F=27base+39trial，50完整F=27base+23接受trial。16F差额全部是返零check4–19的factor1范围拒绝，随后factor.5试探接受，0普通Armijo拒绝。trial接受不等于路径接受态。返零check20为F63已完成/T25失败，随后位元回滚到.5并二分至.25；F66/T27均完整，完整组装后时钟门关闭，因此没有最后基点历史行。最后保存的零基点残量1.0587200376510317e-8仍高于1e-9原门，不是平坦残量，也不能近零便宣布通过。稀疏求解.9024901s，kernel+transfer528.653675s、all assembly602.094339s为主要成本。

## 新保存输入诊断：与旧矩阵乘法位置不同

原生产/reference/view卡不重开。新独立F16卡helper60/outer90s/8GiB，观察器只改003归属/63与25计数及对应stop路径，逆还全文/AST与旧稿完全相同。193绑定前后相同，实际exit0、helper7.830458100s/outer8.850331900s。原NumPy力调用只开始1次、完成0次，逐字段复现原unsupported_arithmetic_range；0T/HP/solve/组装/JIT/修源。diagnostic_captured不是力学通过。

F16 archive47824b83/state9dbd3c95，最大|w|3.407879110554771e-28mm。首个不支持返回位于_response辅助能量Horner循环的_scaled_mul最后回缩：四DD产品的(lo,hi)项 ×2^-192，36(e,q)非零high≈1.772e-127…3.782e-121低于2^-400≈3.8726e-121，low0/validTrue，非overflow/IEEE下溢。29实体点/20实体cells、7介质点/6介质cells，不与工件128cells相交；near全true且small_products选中。不是旧F36的_scaled_matmul。当前未修复，首坏观察不能自动证明外异常唯一原因，更不能代替较晚F63/T25的未捕获切线输入。完整原primitive数组、栈、原16输入和外异常都已保存于[新诊断](range_diagnostic_001/evidence/result.json)。

完整映射及36点/26cells原值、精确保存标量乘积检查、分区和193绑定审阅见[独立primitive审阅](cycle003_F16_primitive_review.json)。其中Decimal只核保存A×B，未运行高精度本构/力/切线参考，不能记作新的HP调用。

下一最小候选应保持能量Horner原14阶所有系数及四DD产品，在tiny分支为remainder和系数共同保持现有2^192尺度，完成乘加归并后再回缩；不删除项/裁零/增大CI域/改变P或门。只扩大_scaled_mul相同up/down指数无法让最终独立物理tail跨回下界。该候选尚未实现或运行，必须新卡在F16取得完整F/T及fresh HP80/120原门，然后再决定新的连续分段循环；若后续切线再拒绝，需保存其真实输入而不能借F16归因。先排算术问题，再扩1mm及2/3mm或细/圆工件；1/2/3mm未执行。

## 实际可视化与效果

新的独立失败图卡helper/outer120s/8GiB，实际exit0、outer2.932658900s，206冻结绑定不变；0新F/T/HP/solve/consumer/测距。仅两实际接受态、×1结构与同一N比例力箭头、明确×4辅助位移；完整25个Newton base观察和39试探另画，缺返零/无滞回/无新参考资格明确标出。[新实际失败图](../../../functional_views/native_workpiece_cycle003_20261004/failure_saved_001/render_001/cycle003_failure.png)、[数值表](../../../functional_views/native_workpiece_cycle003_20261004/failure_saved_001/render_001/accepted_numeric_states.csv)、[保存显示审阅](../../../functional_views/native_workpiece_cycle003_20261004/failure_saved_001/cycle003_failure_view_actual_review.json)。root与独立审图均实际查看PNG3300×2100。非阻断显示限制：左下exact-zero注释轻叠legend，小工件力箭头亚像素，正文数字及CSV可读；不修冻图、不重绘。

本轮实际效果是发现三点简化并未解决新返回路径，排除了来源/模型改变、稀疏LU主耗时和普通Armijo拒绝的猜测，并定位了新的已选辅助能量低词范围问题。完整循环、真实夹紧、signed gap/交叉/包容、压力、自由工件、H2/H3/HF5及完整AD/JIT仍未完成或资格化。只在main开发，origin https://github.com/dudaxing/Compliant-TO-TMC.git；相关新源/失败/诊断/图/上下文纳入Git清单，异目录公开恢复只验文件身份，不称数值重放。
