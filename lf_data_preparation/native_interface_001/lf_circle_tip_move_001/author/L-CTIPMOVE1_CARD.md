# L-CTIPMOVE1：移动工件最小能力实施与小模型验证卡

2026-10-22；**计划待授权，尚未编写候选代码或运行**。基线 main `1e5e9cf76480254a6a288f27fb10bc884acb4c38`，origin `https://github.com/dudaxing/Compliant-TO-TMC.git`。本卡落实上一阶段六类行为，不扩大到真实圆形工件试算。

## 目标与输出

实现显式 opt-in 的导向刚体+x位移探针：机构 input 平均位移 d_hold 保持，工件 q 独立推进，body ux=q、uy=0。复用原力核、切线、split、一般LU、回溯和二分；只增加必要的控制合同和状态/反力入口。

获批后先在独立候选树编写、冻结源码与唯一命令并完成有限独立静审；只有静审通过才唯一启动本卡验证窗口。失败保留真实候选／部分结果，停止后续阶段，不修复重跑。本卡不包含真实14720单元工件、HP、力控制、任意转动、摩擦、动力学、域／α／γ调整或有效夹持资格。

## 已定位的具体改动

|文件范围|必要行为|
|---|---|
|`hf_repo/src/hf_eval/split_displacement.py`：唯一旧源码修改|窄 opt-in 合同区分q和d_hold、prescribed body和零支撑；同一KKT/Newton推进。默认调用保持原offset补偿求和及旧固定lift保护。|
|新增 `hf_repo/src/hf_eval/native_probe.py`|薄公开函数／独立结果schema，显式从已完成固定工件loading末态准入；读取并核源几何／原task／model／选定态身份，仅迁移两份split数组与R，不迁移原矩阵／力／资格。新移动态、反力账本和缓存写入在此层完成。|
|新增 `hf_repo/tests/test_native_guided_probe.py`|独立16单元fixture及六个新测试方法，覆盖下面六类；不修改原共享small_native。|
|研究层 `run_move1_validation.py`、`render_move1.py`|复用现有SUP2限定唯一测试子进程，再从新小模型缓存生成一张实际变形／力／收敛PNG；不复制通用进程管理器，不在显示时重算力或求解。|

不修改 `native_evaluate.py`、`native_resume.py`、task parser、原力／切线／SUP2或默认CLI；新函数是显式新入口。若上述范围不能完成，停止实施准备并说明缺口，不能悄悄扩大卡。

公开入口设计为 `evaluate_native_guided_probe(saved_result, selected_state_index, body_q_targets_mm, output_directory, *, time_limit_seconds, ...)`，最终参数名与候选SHA在静审前冻结。原 fixed_rigid task仅作为来源，另存probe合同，不将旧task标签改成已支持的新physics。

**新发现的关键准入要求：** 原controller第275行依赖 `initial_parameter` 非零才禁止初态Newton修正。新探针从q=0开始，必须有独立显式fresh-anchor检查，直接测原split/R，先于feasible投影、预测和修正；不满足门即typed `initial_state_not_equilibrated`，不二分、不纠正、不伪造非零q。此项是新任务要求，不改变旧q=0 warm-start的既有行为。

原 `target_origin+s` 的10个控制／度量／诊断位置均须核：179、182、183、194、198、201、238、254、292、365行（基线行号）。新增q路径不能仍增加input mean；旧调用仍保留 `(-target_origin,-s)` 分离补偿项，不能先求和舍入后相减。新结果明确 `body_q_mm` 与 `input_mean_mm`，不得让旧 `d` 标量冒充二者。

## 固定的小模型设计

详见 `FIXTURE_DESIGN.md/json`；该表目前是静态推导，不是已构模通过。

- 4×4格，h=.5 mm，域2×2 mm，25节点／50DOF；E1 MPa、ν.3、t2 mm、γ1e−6、α1e−4、Lr2 mm，均为接口小模型参数，不是正式r9任务。
- solid底向上四行 `[1111,1111,1000,1000]`；其余六格passive_void，design为其补集。保留L形连通实体及工件右侧介质。
- 固定工件来源：circle r=.375 mm、center(1.25,2)；cell14，节点[17,18,22,23]，ux DOF[34,36,44,46]、uy[35,37,45,47]。
- 支撑节点[0,5]；input节点[10,15,20]，ux权[.25,.5,.25]；output节点[4,9]，uy权[.5,.5]、spring0。顶边背景uy固定，body重叠[45,47]只计一次。合并15个处方DOF、35个自由DOF和1个input乘子。
- 固定工件父路径 `[0,.0005] mm`，探针保持 `d_hold=.0005 mm`，`q=[0,.00025,.0005] mm`。小模型minimum_increment=.0005/16 mm，25检查／12回溯／4二分；与真实任务.00625 mm不混用。受控失败测试可明确关闭二分，仅用于验证保存partial；不改变真实任务门。

静态格子示意（非计算变形；每格.5 mm；B仍为原medium材料上的刚体运动覆盖）：

```text
y=2  ───────── 顶部uy对称约束 ────────
 j=3     S     M     B     M   ← 右侧介质
 j=2     S     M     M     M
 j=1     S     S     S     S
 j=0     S     S     S     S
         i=0   i=1   i=2   i=3       x→
```

S=solid，M=passive_void；工件只选cell14，移动时原成员和材料不重选。

## 唯一测试与验收

候选冻结后唯一命令为该候选环境的 `python -X utf8 -B -m pytest -q -x -p no:cacheprovider`，目标仅为原 `test_split_displacement.py` 和新增 `test_native_guided_probe.py`。短临时目录、实际工作目录和完整命令在静审时写入冻结协议，不使用旧长证据路径作basetemp。

原模块现为8个方法／9个展开项；新文件限定6个非参数化方法，合计15项。若候选静审发现展开数或调用上限不同，不能直接启动，须先修订此卡。原模块包含一个2单元真实NumPy路径，其余为注入控制代数；不得都计成TMC物理覆盖。

|新增验证|必须证明|
|---|---|
|常量input／独立q的代数|注入小线性非对称残差，与独立dense方程比较，首次预测即满足常量mean；body平移用同一q而非节点平均自由变形|
|q=0严格新准入|有意错误R／state在第一fresh F/T后失败，无projection、Newton、接受态或外部重试；原split输入不变|
|真实16格运动与存储|固定父态→q0新检查→两个非零q；逐节点刚体、input保持、实际位置、原适用门、缓存原值和两个控制列读回一致|
|反力与部分失败|独立聚合全残差核ON-body/drive符号、material/Hu、互斥支撑；注入终端失败保留最后接受态，不标释放|
|约束冲突|body与port/不相容支撑拒绝；body-y/背景重叠去重；原默认非零fixed lift仍拒绝|
|来源拒绝|不同source/model/task/两split字段身份拒绝，不能经旧extend_path迁移新physics；只用本次生成的小模型文件|

调用上限：本窗口最多4次真实小模型平衡路径（含原模块2单元路径），最多30次注入控制器路径／输入拒绝调用；新文件中最多3次真实16格路径，未调用不凑数。source SHA、实际精确调用数须候选静审核实后冻结，实际结果分别计数，不把注入残差、拒绝分支或F/T基态检查称独立物理路径。

验收：relative free residual≤1e−9；mean误差≤1e−10×max(|d_hold|,1e−6 mm)；J>0／有限；新真实任务global balance≤1e−6；零支撑和逐body prescribed偏差≤8e−11 mm；实际刚体形状保持。global账本分区互斥，保符号和半模型N，t2不再乘一次。合成残差的global合力若非物理守恒，不把该fixture当此门的验证，真实16格承担该检查。旧测试保持其原断言与容差。

## 窗口、图像、安装与停止

- tests180秒，纯显示60秒，共享helper300秒、outer360秒；采样8GiB，各库线程上限16。复用原SUP2相同实例终止／成员覆盖／句柄释放合同，不改清理验收。
- 唯一数值启动；测试首错停止，后续显示／安装不执行。正常通过后一次生成一张小模型PNG（实际×1几何、q／d保持、有符号反力、残差/J），root最多一次像素检查。图像不授夹持／压力／释放资格。
- 全部通过后，才将controller及新增probe两份候选源码按已测字节安装到正式hf_repo；默认固定工件入口不切换。源码SHA复核不是新一轮数值测试。任何阶段失败均保实际候选、partial／安装记录，无自动回滚、删除、修复重跑、延期或force。
- 完成记录、必要入口说明、普通main推送及同机异目录字节恢复。失败也如实记录，不修改既有冻结结果。

本卡通过仅表示受限探针接口／小模型能力。真实 L-CTIPPROBE1 的r9／center(80,40)／right92／Lr80／α2.5e−7及q0→.025路径、bbox读取、资源与实际图须依据本卡结果另行安排。

新增实现、移动工件小模型F/T／平衡及资源窗口需要阶段确认；已关闭的LOADSPEC1只授权规格与接口核查，不能把其文档完成当作本卡的数值许可。
