# L-CTIPFLOAD1 控制器独立静审

2026-10-23，`/root/fload_api` 审阅非本人编写的 `split_guided_force.py`。结论：**14 项静审通过，无阻断；可以继续候选整体静审，不代表数值验证通过。**

被审候选：`D:/hfl1_001/candidate/hf_repo/src/hf_eval/split_guided_force.py`，407 行；SHA256 `975d1e1797403c2cddbda2ee04c8ef0e3d5e07d038bdb48473e4ff6e60fcf0c6`。只读源码并 AST 解析；未导入候选、未运行 pytest/collect、未计算矩阵或力、未读取历史科学缓存、未修改实现。

对照本轮 `TASK_SPEC.md`、`API_DESIGN.md`、`SMALL_MODEL_VALIDATION.md`、`L-CTIPFLOAD1_CARD.md`；也核对未改旧 `displacement._linear_solve`、原 `split_displacement` 的补偿测量及终止/二分政策、`SplitDisplacement` 的有限/位身份和原 `_assemble_tangent` 的有限门。

|项|源码依据|静态判断|
|---|---|---|
|1 新设置与路径单位|29–76|唯一新设置为正有限 `minimum_force_increment_half_N`；旧 mm 设置不参与 N 二分。载荷至少两项、有限实向量、绝对有符号严格递增，无首项归零或自动换符号。|
|2 原成员与约束合同|77–116|nodes/zero/background 合同严格限定；body 与 input/output 不重叠，body 与实体零支撑冲突拒绝，仅允许 body-y/background 既有重叠；spring=0；初 lift 为零且原 fixed fluctuation 零。|
|3 未知量与映射|109–122、148–154、260–274|保留原 free fluctuation；body-x 统一由未知 q 写入 lift，body-y 与 body fluctuation 保持零；q 不夹限、不取参考解、可有符号。未知次序为 w/q/R，原全场 DOF 不重定义。|
|4 非对称约化块|228–245|Kff 选原 free；Kfc 对 body-x 列求和、Kcf 独立对 body-x 行求和、Kcc 两方向求和，未以转置替代；b 扩展为 [bF,0]，KKT 上右为负 b，下左为正 b。无对称化或新正则。|
|5 合力及半模型符号|172–198、260–269|g=fsum(body internal x)−P，body 各项以 1 而非平均权进入；P 增量只进 q 行一次且符号正，未给每节点重复完整 P；没有新增厚度因子或 full-load 猜测。|
|6 原 free 残差与尺度|172–198、290–293|free 平衡仍为 fint+spring−bR；SF 为原 free 三项 Euclidean norm 与 E*t*dscale 地板之最大，free 门保持旧 settings.tolerance。body 合力另设门，不被大 R 的尺度吞并。|
|7 新 g 门及 SP|172–198、290–293|SP=max(abs(P),abs(Panchor),Ffloor)，同一目标固定且非 ΔP 归一化；记录 g、SP、相对量和 tol*SP 绝对门，接受同时要求 free、g、mean。|
|8 原 mean 门及补偿|117–122、156–170、172–198|dscale=max(abs(dhold),旧 floor)，mean bound=旧 constraint_tolerance*dscale；均值与误差复用 split_average_measurement 的两字段补偿求和，误差包括 −dhold，不先舍入均值相减。可行补偿只动非 body input pivot，不投影 q。|
|9 fresh 一检身份|109–114、260–297、344–373|首目标等于初 Panchor，不执行 predictor/impose/feasible；每次 Newton 先真实 F/T/measure。fresh 未过任一门即 initial_state_not_equilibrated，先于修正/线性求解/二分；成功检查 1 原 split 与 R 经复制保持。API 另核位身份。|
|10 Armijo 与 trial|299–342|merit=.5*(norm(r/SFbase)^2+(g/SP)^2)；同次所有 trial 显式复用本 base SF 和目标 SP，采用原 1−2*c*factor，原 checks/backtracks 上限；trial 必须过有限/J/可行检查，accepted trial 不直接变 accepted state，下一 base 必须重新 F/T。|
|11 有限/J 与真实切线|124–146、180–198、200–245|状态类拒非有限两字段；evaluate 拒 internal/J 非有限、所有 J<=0，并核存在的 F/Hu 有限；metrics 核 material/Hu/global 分量有限，step 核 KKT 有限。实际 API 的原 _assemble_tangent 在返回任何 tangent 之前另拒矩阵非有限；不把 synthetic assembler 当新内核资格。|
|12 N 二分与回滚|344–367|失败先断言原 split、R 位身份和 P/q/K 未改变；记录实际失败。首锚点、time_limit、constraint_failure 不二分；其余受原 max_bisections 与新 N 最小步长限制，原 1e−12 边界浮点比较政策保留，旧 mm minimum_increment 未被引用。实际中间态保留并标原目标/索引/深度。|
|13 partial、clock、缓存时机|124–146、260–297、344–407|clock 覆盖前后 F/T、线性解及 callback；超限明确 time_limit，无继续二分。accepted 仅在新鲜 base F/T 与所有平衡门通过后创建；callback 收 deepcopy，原核缓存可按 state hash 绑定。顶层失败保 last accepted、实际 split/R/P/q、全部已有 Newton/trial/linear/failure 历史，不回滚已成功内部中间态。|
|14 互斥账本与分层门|116、200–226；API capture|support 只取 fixed−body-x，global 显式加 (P,0) 一次；body-y/zero 的集合本身去重。global scale 与规格在 spring=0 范围一致。低层为 synthetic oracle 留 global 诊断，真实物理 global<=1e−6、rigid/zero<=8e−11 mm 由 API capture 拒绝；没有声称低层 synthetic 已过物理全局门。|

## 边界与后续

静审没有运行精度、conditioning、真实 q↔P 回归或收敛验证。这些只能由冻结后的唯一 17 项测试窗口给出。候选没有承载极限、自由 y/转动、摩擦、压力、卸载/力控续算、真实 r9/chunk256 或 HP 资格。

原一般 LU 的 mixed-unit backward error 仅诊断；实际 free/N、g/N、mean/mm 门分开。原节点支撑仍记录模型来源，但力控 body-x 已从显式支撑账本删除；内部 body 合力不再作为额外外载相加。

静态限制：低层 assembler 是可注入接口，其 synthetic fields 可不含 F/Hu；真实 API 使用原 NumPy kernel，总力/分量和 F/J/Hu 缓存齐全。原物理门依赖 API capture 是本轮既定分层，不能以后绕过 API 将任意低层结果称合格真实力控。
