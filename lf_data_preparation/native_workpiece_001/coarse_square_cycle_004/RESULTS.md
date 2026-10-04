# 机械模式0→0.5→0 mm：完整新循环与独立参考通过

整体目标是独立HF正向第三介质接触力学：读取普通几何与明确的物理任务，计算可靠的力、变形、平衡和接触相关指标，供外部研究比较。HF不运行LF优化、dmftd或MPM。本轮完成了已验证NumPy机械力入口的平均位移集成，并在固定对称半方形工件上完成新的0.5 mm加载—卸载。目标尚未整体完成；本轮不授予有效夹持、压力或一般接触资格。

## 为什么这样实现

旧cycle003在相同目标[0,.5,0] mm下只接受初始和峰值两态，完整响应的辅助材料能量范围异常使卸载成本上升，随后切线T25范围异常且未捕获输入，最终超过600秒预算。旧失败仍冻结。此前对保存F16的独立实验表明，可以保持CI/材料力/Hu力、原切线和原数值门，仅显式省略辅助能量；不能把未计算能量填写0/NaN或默默回退。

因此本轮只为`solve_native_mean`增加可选`response_mode="mechanical"`，CLI增加`--response-mode mechanical`。默认complete保留17字段及schema1.0/1.1；机械模式schema1.2保存16个force字段、3个切线张量、完整非对称CSC和状态身份。结果与每接受态均记录response_contract、实际force_kernel_version及`auxiliary_material_energy={status:not_evaluated, qualified:false, field_present:false}`。控制器、signed predictor、Newton/Armijo/KKT、回滚、CI支持域、缓存保存及B52消费者保持不变。没有捕错fallback、放宽收敛门或能量代填。

先以独立小卡检查接口：[机械接口6项实际通过](../native_mean_mechanical_integration_001/RESULTS.md)，其中旧完整模式4项未改，新2项检查真实小循环与注入切线异常的partial/bitwise rollback/保存不重算。该小测试不替代真实3200单元路径资格。测试正式运行一次，复制到main的focused测试与已测试版本逐字节相同；CLI参数静审、API实际执行，未额外执行第二次CLI求解。

## 实际物理任务及来源

用户授权Agent探索对称工件和较大变形。此处是Agent选择的探索工况：固定完整方形边长16 mm、中心(70,40) mm，仅计算对称下半；底/左初始间隔2 mm。保留原cycle003模型，h=1 mm，3200单元、3321节点、6642 DOF，376有效fixed/6266自由DOF；工件128单元、153节点、306体DOF，其中17个与对称约束重叠。E=1 MPa、nu=.3、平面应变、厚20 mm，gamma=alpha=1e-6、Lr=80 mm，输出/辅助弹簧均0。平均输入沿+x，自由输出指标沿+y。

仅四个描述性task键改变；全部物理键、原27模型数组及目标[0,.5,0] mm不变。原minincrement=.00625 mm、Newton25、backtrack12、bisection4及原门保持。完整模型归档SHA为`a2d6e141fecb5f34efa66455c19ee67f47f476e019f760feb685f1a091266049`；新task规范SHA为`eabc370933079f1e83c001ff11c426b95823a140b9bfa19de9a5ebf3f826ea04`。68来源路径为旧63 closure中的3个声明更新（core/mean/CLI）及5个新包装；保留自有字节副本，不依赖原作者工作目录恢复。32输入、172生产/参考协议绑定均前后不变。

## 功能效果：实际三个接受态

一次生产完整成功；17/17次力、10/10次切线、1次solver、0 HP/JIT。10个Newton base、7个full-factor trial均成功，无范围异常、拒绝或二分。保存来自返回缓存，0额外F/T；所有hooks恢复。初始与返回目标均为0 mm，但接受index、leg及stateSHA不同，未去重。

| 接受态 | 平均输入 mm | 输入R N | 自由输出+y mm | minJ | 实际无符号外边界最短距 mm |
|---|---:|---:|---:|---:|---:|
| 初始 index0 | 0 | 0 | 0 | 1 | 2 |
| 峰值 index1 | .5 | .106253247986 | .575755712293 | .735764774113 | 1.471935964045 |
| 卸载返回 index2 | 0 | -4.80403965e-30 | 3.15775474e-29 | 1 | 2 |

峰值生产相对残差`4.271025552015961e-13`；返回相对残差`5.678804681028937e-17`，最大绝对位移分量=`3.407879110554771e-28` mm（逐节点位移向量模的最大值另为`3.445074e-28` mm）。初始stateSHA为26d76fa9…bbe2，峰值76e4112e…6c28，返回9dbd3c95…4e2。峰值与旧003峰值相同，资格来自本轮新参考而非转移；返回与旧F16拒绝输入身份相同，在新机械模式下先作为F16 full trial成功，再经F17/T10 base接受。

峰值作用在固定下半工件的总合力(Fx,Fy)=(-.000150412413805,+.000134183313564) N；材料分量(-3.94767756937e-5,+8.79778152127e-5) N，Hu分量(-.000110935638112,+4.62054983509e-5) N。这里报告模型/第三介质对工件作用，支座反力方向相反。镜像上半合力为(Fx,-Fy)，完整装配净矢量为(2Fx,0)；`2|Fy|`仅为两侧法向合力绝对值之和，不能据此认定有效夹持。正间隙下仍有第三介质小力，压力分布、接触法向和夹持判据未资格化。

## 新独立参考及其严格边界

生产终态成功后，本卡一次fresh reference对每实际接受态全部3200单元执行HP80与HP120：6/6新HP、58,197项检查全部通过。覆盖6642 DOF、57600局部检查、每态204800个局部总T系数到完整CSC的组装核对（三态合计614400）、27个全局力/方向作用/CSC/KKT门及原平衡、约束、支持和工件投影门。`full_element_and_DOF_coverage=true`；高精度切线只核对声明PORT方向及deltaR=0，不是逐列HP。先前单F16、旧31d七态及旧003峰值资格均未借用。

原门：生产残差1e-9、独立残差1e-8、平均约束1e-10、全局平衡1e-6、fixed位移8e-11 mm；总力1e-11、总方向作用1e-10、材/Hu分量1e-9、HP80/120互检1e-40。原分母/floor保持；Decimal3000全局精确scatter启用Inexact trap。峰值全局总力归一差`1.0267868862129609e-15`、总方向作用`4.790604581789116e-17`、CSC作用`4.380991744325689e-17`；HP独立相对残差`4.2711644190443347e-13`、平均约束`5.55111512312578e-17`、平衡`3.24024869626589e-16`、fixed误差0。各态及所有局部最坏值、原分母、门、HP互检值保存在[参考summary](reference/summary.json)、精确element_gates和[独立保存数学审阅](actual_saved_math_review.json)，无需凭摘要重跑。

资格限此物理task/模型/源码/三个实际接受态的机械力、声明方向作用、组装、平衡和工件合力。辅助材料能量明确未计算；归档的解析HP能量仅诊断，不能赋予候选能量资格。应力HP、全列切线HP、旧T25输入、拒绝trial、一般支持域、压力、有效夹持、自由工件、H2/H3/HF5和AD/JIT均未获得新资格。旧完整响应和旧003闭卡失败未改写，不能把新机械路径成功表述为旧完整能量/T25问题均修复。

## 实际可视化与几何观察

[结构、变形、输入力、工件分量与求解顺序图](../../../functional_views/native_workpiece_cycle004_20261004/saved_001/render_001/cycle004_saved_path.png)实际一次生成，3300×3150；[3行×51列CSV](../../../functional_views/native_workpiece_cycle004_20261004/saved_001/render_001/accepted_numeric_states.csv)全来自缓存。真实×1峰值和返回结构、标注4×位移辅助图、共同N力箭头尺度与真实mm色标可人工核对。小工件力箭头按共同尺度可能近乎不可见，曲线/CSV保留实际值。0插值、0动画帧、0新F/T/consumer/scatter/solver/HP/距离。图标题PRODUCTION ONLY UNQUALIFIED表示查看器只读生产记录；生产原独立资格flags不回填。本报告的独立资格来自另行fresh reference，二者不矛盾。

随后[新实际Q1边界测量](../../../functional_views/native_workpiece_cycle004_20261004/boundary_saved_001/RESULTS.md)只读三态，各测一次：2→1.471935964045→2 mm，无交叉或roundoff near-touch。峰值left group最短距1.902256457461 mm；图中旧定义节点窗口bottom/left为1.477624456079/2.206238808737 mm，不能替代真实边界距离。测量排除y=40镜像切口，是unsigned外边界线段欧氏距；未做signed normal gap或containment。缩距和恢复说明夹持前几何运动，尚未证明形成接触或有效夹持。

## 一次实际阶段成本与失败记录

| 正式阶段 | helper秒 / 采样峰值字节 | outer秒 / 采样树峰值字节 | 原上限秒 |
|---|---|---|---|
| prepare | 不适用 | .377254799998 / 27664384 | 60 |
| production | 211.459739300 / 853504000 | 213.733933400 / 852099072 | 600 / 660 |
| fresh reference | 63.904601700 / 419418112 | 66.123817700 / 423276544 | 240 / 300 |
| saved view | 2.351876700 / 154341376 | 2.651651600 / 158785536 | 120 / 120 |
| saved geometry | .614447400 / 40792064 | 1.094330000 / 43212800 | 120 / 120 |

各阶段8GiB采样树限额，含imports/hash/IO，非OS硬cap。每正式阶段唯一一次、实际terminal exit0；没有重试/force/延长/修复。view130绑定、geometry29绑定前后不变；几何3次真实调用且0F/T/solver/HP。单元测试单独小卡6项通过，时间不挪入生产预算；[实际身份回执](actual_saved_identity_review.json)核对105个NPZ数组及来源闭包；[实际审图回执](../../../functional_views/native_workpiece_cycle004_20261004/saved_001/actual_view_review.json)核对PNG/CSV/身份。

作者准备脚本有两次执行前SyntaxError（多余括号）：unit准备器尚未生成stage或运行pytest时修正；cycle安装器尚未生成stage时修正。后者第一次失败后，root曾错误继续依赖copy/launcher，分别因目标目录/launcher不存在而退出，未启动child、产生正式receipt或调用数值；随后改为检查exit再执行依赖步骤。作者脚本AST核对后各一次成功准备，正式unit/prepare/production/reference均一次通过。明确保留这些准备错误，不能混入正式阶段成功计数或称为已执行数值重试。

实现identity：native_mean `205572334129ec4d7aaf9fdd5838935b450fce929e6b2ea18844308f85ae8fd3`；CLI `01f6f1277d0d596138f024706fca996984222769925679896c4a01e4461fc52b`；core `d5f7d20a6ec0c92847d67f8782f4dcc89772fc4ea62797626b0beae7effabd9a`；原controller f4632b…386c、原T f7549b…a8a1c、B52 b52f8b…93fe、CI 8115e1…7081均未改。来源、逐路径byte SHA、输入和执行限额见source_freeze/input_inventory/protocol及原运行回执，不以缩写身份替代正式绑定。

## 依据结果推进下一步

下一步只新增同一粗方形固定工件1 mm探索循环，保持本轮机械合同与原门。优先采用真实递增目标0→.5→1→.5→0 mm，在新独立卡开始前冻结目标、来源、预算和接受态参考范围；不读取本卡已验证状态作为新解或资格。根据每一步实际收敛、minJ、费用、边界距和工件力决定是否再推进2/3 mm；不用当前近似闭隙趋势外推接触阈值。若首次失败，保存partial/首次异常并关闭该卡，先排查再选择新卡。

圆形r8 mm与细网格固定方/圆模型已构建但对应平衡未执行；随后分别形成新物理工况及资格，不把不同LF原始设计对比称为网格收敛。接触判断还需signed gap/包容/法向及压力或有效夹持定义，再考虑自由刚体工件。更大变形是探索方向，当前无1/2/3 mm实际结果或正式行程上限。本轮记录与源码、缓存、参考和图将推送main，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git；公有恢复仅核对文件身份，不构成新数值重放。
