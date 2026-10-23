"""Prepare documentation only: no HF imports, arrays, mechanics or tests."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).parent
REL = 'lf_data_preparation/native_interface_001/lf_circle_tip_force_control_preparation_001'
TARGET = ROOT/REL
BASELINE = '2b3b6ecbc038fe32554cee4889637f3a2fb2e4ec'
STAGE = 'L-CTIPFLOADPREP1'
LOW = ROOT/'lf_data_preparation/native_interface_001/lf_circle_tip_low_probe_001'

def git(*args):
    return subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false',*args],cwd=ROOT)

def write(path, data):
    path.write_bytes((json.dumps(data, ensure_ascii=False, indent=2)+'\n').encode('utf-8'))

def pin(path):
    raw = path.read_bytes()
    return {'path':path.relative_to(ROOT).as_posix(),'bytes':len(raw),'sha256':sha256(raw).hexdigest()}

DOCS = {
'PREPARATION.md': '''# L-CTIPFLOADPREP1：导向轴向力控制准备

2026-10-23（Asia/Seoul）。**规格、接口和有限验证方案准备完成；没有实现、安装、构模、F/T、HP或新平衡求解。** 本轮用户只批准准备。独立审阅、实际静态检查和发布回执分列，不将文档完成写成力控数值PASS。

## 整体目标与本轮作用

整体目标是HF独立读取LF普通几何，可靠计算一致大变形／TMC响应，逐步回答夹持器作用、承载与释放。HF不重新优化LF。已有固定工件加载／卸载、保存态延伸和导向位移探针；最近LOW1完成从零短父0→.25→.50 mm，再保持机构均值.50，仅使工件q=0→.025 mm。

LOW1证明了“给q→求总驱动力Q”的功能链。高输入1.06 mm在相同q=.025 mm的Q约为低输入5.92倍；但低输入仍有约.519 mm尖端间距和86.29%的轴向Hu贡献。因此既不能把低输入当零力基线，也不能把高低差称纯接触抗拔。当前缺少的是“给外载P→解未知工件位移q”，而不是更多位移步或重复HP。

本轮完成：最小物理／数学合同、半模型和预载口径、三个新文件的接口边界、原门与新增力门、有限小模型交叉验证及下一候选卡。效果是将实现对象缩小为一个导向刚体平移自由度；目前仍无新力控数值结果。依据见[原LOW1结果](../lf_circle_tip_low_probe_001/RESULTS.md)。

## 控制示意（非有限元结果）

![已实现位移探针与拟力控](control_schematic.png)

图仅说明控制量交换，不按比例，不显示实际夹持器几何／变形，也不认定尖端接触。右界ux自由，导向保留uy=0／转角0及相应反力。PNG有一次排版迭代、两次root检查；不是LOW1旧图重绘，见[示意检查](author/SCHEMATIC_QA.json)。[矢量版本](control_schematic.svg)与绘图源码一并保存。

```mermaid
flowchart LR
  A[完整固定工件父任务成功末态] --> B[原split与有符号R身份准入]
  B --> C[匹配非零P0的fresh F/T首检\n不投影、不修复]
  C -->|通过| D[给绝对半模型外载P\n解未知w、q、R]
  C -->|失败| X[记录初态不平衡并停止]
  D --> E[自由平衡＋输入均值＋工件合力门]
  E --> F[缓存变形／力／介质／收敛\n力控与位移参考交叉核对]
```

## 保持的正式物理条件

|内容|正式r9任务保持|
|---|---|
|机构与工件|wave；r9 mm、圆心(80,40) mm，原510格／565节点不重mask|
|域与材料|right92 mm、h.5 mm、Lr80 mm、E1 MPa、ν.3、plane strain、厚度20 mm|
|第三介质|γ1e−6、α2.5e−7，原实际弱残差及非对称切线|
|控制|机构参考加权均值保持.50 mm；body uy=0／转角0；q改为未知|
|其余边界|原支撑、实体／背景对称、零输出弹簧和自由右界；不加摩擦、自由y／转动或动力学|

这里选.50 mm是以后功能交叉检查的较平缓条件；**本轮没有执行正式r9力控**。小模型沿用既有16格fixture自身的2 mm域／2 mm厚度和原参数，仅作软件验证，不替换正式物理条件。

## 阅读与后续安排

1. [任务规格与数学／验收合同](TASK_SPEC.md)：未知量、载荷、预载、非对称块、门与失败含义。
2. [接口能力及拟新增API](API_DESIGN.md)：复用部位、单位、参数、保存与错误语义。
3. [有限小模型方案](SMALL_MODEL_VALIDATION.md)：17个展开项、最多5条真实小路径及独立计数。
4. [L-CTIPFLOAD1候选实施卡](L-CTIPFLOAD1_CARD.md)：下一步只实现并验证小模型，不包含真实r9试算；**尚未批准／编写实现候选／冻结runner或启动**。

独立意见见[数学审阅](author/MATH_REVIEW.md)、[接口审阅](author/API_REVIEW.md)，取舍见[审阅决策](author/REVIEW_DECISIONS.md)。本轮事实见[准备结果](PREPARATION_RESULT.json)及[最终静态核对](author/PREPARATION_REVIEW.json)。原55份生产源码、全部原数值及资格保持。承载极限、纯接触压力、释放、稳定性和HF5均未因此升级。
''',
'TASK_SPEC.md': '''# 最小导向轴向力控任务与验收合同

2026-10-23。L-CTIPFLOADPREP1；以下是下一候选的规格，**尚未实现或数值验证**。正式物理条件见[总说明](PREPARATION.md)，机器可读设计记录见[PROPOSED_TASK.json](PROPOSED_TASK.json)；该JSON不是现有native task parser可运行的新任务。

## 载荷、未知位移与预载

采用固定空间+x方向的有符号刚体合外载P_half（dead generalized load）；没有随动压力或逐节点分载输入。工件只有一个未知刚体坐标q，全部原body-x位移为q，body-y=0且转角0；q为有符号未知，不设置q=.025的处方，也不将q夹到预期答案。机构输入均值d_hold从完整合法固定父末峰继承，首个正式交叉候选为.50 mm。R仍是机构端口乘子，不是P。

当前保存约定：ON-body Fx=−Σ_B f_int,x；位移探针Q_half=Σ_B f_int,x。故力控平衡为`g=Q_half−P_half=0`。工件逐节点x弱力不必为零，只要求正确刚体广义合力平衡；节点力不能除任意面积称压力。P>0沿+x，负值保留符号，首版路径只处理绝对目标严格递增的局部增载；不隐含支持卸载、循环或保存态延伸。

|量|半模型|对称完整装配|
|---|---|---|
|轴向外载|P_half，N已含源厚度|P_full=2P_half，仅换算一次|
|工件平移|q，mm|同一q，不倍增|
|轴向平衡|F_on,x+P_half=0|2F_on,x+P_full=0|
|竖向作用|下半Fy与导向反力|镜像抵消净Fy，2abs(Fy)不是轴向容量|

正式20 mm厚度已在积分中；不再乘20，不输入N/mm。最薄API只收half N，不提供会静默猜测口径的mode或full载荷参数。

LOW1原普通记录给未来正式交叉检查的候选绝对载荷：

|锚点／参考|q mm|P_half N|
|---|---:|---:|
|原完整低输入父末态／probe q0|0|3.686421133658022e−5|
|原位移探针终点，仅用于选P1与事后比较|.025|4.3272306948756724e−5|

ΔP_half=6.408095612176505e−6 N单列，不能把P1当增量。必须从同一固定父q0的原split／有符号R开始，用P0做fresh F/T首检，同时过原门和g门，检查1直接接受，状态／R字节不变；错误P0不能改写成新鲜算出的Q，更不能投影或Newton修正。首目标P0不必逐位等于fresh Q，但必须通过下述预先定义的力门；状态身份要求仍逐位保持。来源错在F/T前拒绝，载荷／平衡错在fresh检查后拒绝。

## 刚体消元与实际Jacobian

令S选择原model.free（不含body），c在每个原body-x DOF为1、其余0。仍以split表示：lift=q*c，fluctuation=S*w；body fluctuation为0，参考成员不随运动重选。固定父q0的lift为0，迁移保持其原split和R。bᵀc=0，k_out=0。

以z=(w,q)，T=[S,c]，未知为(z,R)，残差及Newton块为：

```text
r_w = Sᵀ f_int − b_F R          (N)
g   = cᵀ f_int − P_half         (N)
h   = bᵀ(lift+fluctuation)−d_hold (mm)

       [ SᵀKS  SᵀKc  −b_F ] [δw]     [−r_w]
J Δ =  [ cᵀKS  cᵀKc    0  ] [δq]  =  [−g  ]
       [ b_Fᵀ     0     0  ] [δR]     [−h  ]
```

K是原实际残差的非对称Jacobian；两向耦合SᵀKc、cᵀKS分别组装，不以转置替代，不对称化。一般稀疏LU保持；不加隐蔽切线正则或改成能量极小。c是1而非1/N_B，合载荷只进入广义q行一次，不给565节点各施加完整P。无需分配任意压力或存巨型dense T，可用原free索引与body-x求和。

最薄控制器使用该reduced系统的切线预测／Newton，均值补偿测量与可行投影只作用非body端口，绝不投影q。非零P0不是从0重新加载的阶段。首版无自由y／转动、摩擦、接触面压力、弧长或极限点延拓。

## 适用原门与明确新增力门

原free残差r_w、机构均值和原物理门保留。d_scale=max(abs(d_hold),1e−6 mm)，F_floor=1e−8*(E*t)*d_scale，量纲N；E*t从源force_scale_per_length读取，不在真实模型再乘厚度。

```text
S_F = max(||f_int[F]||₂, ||(bR)[F]||₂, ||spring[F]||₂, F_floor)
S_P = max(abs(P_target), abs(P_anchor), F_floor)   # 同一载荷目标内固定
rho_F = ||r_w||₂ / S_F
rho_P = abs(g) / S_P
```

本范围spring=0；保留该项仅说明与原SF相同。不能把g塞入由大R主导的旧单一范数后声称它已足够小。

|层次|必须满足|
|---|---|
|自由平衡|rho_F≤原tolerance=1e−9|
|新增工件合力平衡|rho_P≤同一tolerance=1e−9；同时记录g/N、S_P/N及绝对bound，不以ΔP作唯一归一化|
|机构均值|补偿测量abs(h)≤1e−10*d_scale，不能先把两个split舍入成显示位移再相减|
|材料与几何|各字段有限、全部J>0；刚体及零支撑误差≤8e−11 mm|
|全局外力|新互斥账本relative balance≤1e−6；不能由g或global单项代替全部门|
|起点|fresh检查1、无预测／projection／线性纠正；原lift、fluctuation、有符号R逐位保持|

原checks25、Armijo1e−4、backtracks12、bisections4保持。新增merit=`.5*(||r_w/S_F_base||²+(g/S_P)²)`；同次line search所有trial固定本次base的S_F_base和该目标S_P，沿原Armijo因子`1−2*c*factor`检查。mean需保持可行，不能拿N与mm原值直接混合求范数。新的力步长字段为`minimum_force_increment_half_N`；原minimum_increment=.00625 mm只记录来源，不用于P二分。小模型N步长及资源另见验证方案，正式r9步长待小模型结果后冻结。

这些是适用旧门加新增力控门，**不是已完成的HP十五门**。新的力门及merit需在下一候选静审与有限数值验证中落实。

## 账本、成功与失败

全局外载账本列机构actuator bR、显式(P_half,0)、body-y导向、其余零支撑及原spring0。body-y与背景对称重叠只计一次；原body-x处方驱动力不再另列支撑与P重复相加。Σbody f_int,x仍可作为内部广义力输出，不能再称另一个外加反力。刚体内部约束可有自平衡节点分量，最薄接口不伪造唯一外载节点分布。

全局门的数值定义也固定：令D为原fixed DOF去除body-x后的集合（含body-y且与其余zero去重），s_D只在D取`f_int−bR`、其余为0；`G=sum_xy(s_D)+sum_xy(bR)+(P_half,0)`，`S_G=max(norm(s_D)+norm(bR)+abs(P_half),S_F)`，`relative_global_balance=norm(G)/S_G≤1e−6`，各norm为Euclidean。这里不存任意body节点外载分配，且绝不能把原body-x support再加一次。

成功分三层：本轮仅规格静态完成；未来小模型全部有限验证通过才具备受限力控能力；以后正式r9所有请求P及内部接受态满足门才称该力路径数值完成。跨q参考比较和全局账本不授唯一性或稳定分支；导向仍可给Fy和矩，不是自由工件承载试验。

首终端错误／时限停止，保存实际partial、失败目标、全部内部回溯／二分及原状态；原内部回溯与外部重试分开。奇异、非收敛、低J、负Q、q超出应用预期都不自动称释放或承载极限。首版不暗加q夹限；未来真实应用允许位移需另定明确终止条件。没有通过时不得临时调α／γ／域、放宽门、缩小N步长或延长窗口。

源码符号依据：[原probe](../../../hf_repo/src/hf_eval/native_probe.py#L239)、[原残差与尺度](../../../hf_repo/src/hf_eval/split_displacement.py#L232)、[原非对称KKT/LU](../../../hf_repo/src/hf_eval/displacement.py#L105)。
''',
'API_DESIGN.md': '''# 导向轴向力控：最薄接口与能力核查

2026-10-23。**API设计，未实现；下面不是可直接运行的调用。** 当前固定工件和位移探针均不支持给P求q。拟只新增两个生产模块和一份测试，不改旧task parser、默认CLI、native_response、原controller、原力核或切线。

```python
# 拟议签名，不是当前可导入的函数。
from hf_eval.native_guided_force import evaluate_native_guided_force, GuidedForceSettings

evaluate_native_guided_force(
    saved_result, selected_state_index,
    body_load_targets_half_N, output_directory,
    *, force_settings, time_limit_seconds=120.0, on_accept=None,
)
# force_settings = GuidedForceSettings(minimum_force_increment_half_N=...)
```

|输入|明确合同|
|---|---|
|saved_result／selected_state_index|完整成功fixed_rigid/load_only父任务的真实最后原目标峰；继承d_hold，不能选probe JSON或旧路径中间态|
|body_load_targets_half_N|一维有限有符号绝对半模型合外载N；至少两个，首个匹配fresh q0预载，后续严格递增；无q目标、full/half自动猜测或增量歧义|
|force_settings|新不可变设置，仅必填正有限minimum_force_increment_half_N；不提供另一套未绑定的旧数值默认值|
|time_limit_seconds|唯一新clock；其余原DisplacementSettings由父绑定；不得把其中minimum_increment/mm用作N步长|
|output_directory／callback|全新、在父树外；每实际接受态一次callback；来源只读，首错保存实际partial|

q可正可负，由reduced平衡解出；首版只支持这条有序增载，不支持卸载、循环、任意负向推进、probe保存态延伸或自动force-to-displacement fallback。这里“有符号载荷”不等于所有路径模式已实现。

## 文件与复用边界

|拟文件|最小职责|
|---|---|
|新增hf_repo/src/hf_eval/split_guided_force.py|GuidedForceSettings及(w_F,q,R)控制器、新g门／N二分／partial；复用split_average_measurement及一般LU，不复制通用进程管理器|
|新增hf_repo/src/hf_eval/native_guided_force.py|薄API；复用native_probe._admit的严格父身份准入、原NumPy力/切线、split及_npz缓存模式；新账本和独立schema|
|新增hf_repo/tests/test_native_guided_force.py|8个非参数化方法及全新16格共享fixture；不读旧科学缓存|

直接复用私有_admit是当前仓库内的窄选择；候选静审绑定其SHA。若三新增文件范围无法完成，先报告并修订计划，不能暗改旧辅助函数放宽准入。原free35、body-x4节点合并为一个q，加R后小模型reduced系统37未知；50DOF仍是原全场尺寸，不能把它写成37DOF新网格。

_linear_solve可将[dw_F,dq]看成其位移block，传reduced K与[b_F,0]，并保持R在最后。旧诊断target_displacement必须写真实d_hold/mm，另加target_force_half_N；不把P/N写入位移字段。mixed-unit backward error仅诊断，不替代分开的N/mm门。kernel仍按原split物理状态求力和实际非对称切线。

## 首态准入与保存

复用_admit逐项核父success／完整原目标／最后原峰、task与model来源、材料／网格／成员／支撑、原机制源码、两个split字段及有符号R；不读取旧力或矩阵当新证据。进入本轮力控以后，首目标P0必须由fresh F/T直接满足[起点与验收合同](TASK_SPEC.md)，不能在API内部把首目标替换为fresh Q，也不回放父加载。

新result拟schema为`hf-native-guided-force-1.0`，独立于native-mean／guided-probe。原native_response只适配native-mean，首版不伪装为该schema或给它自动升级关联能力。

最低保存字段：

- source／原parent_task和SHA、mechanics SHA、原模式／非clock设置及force_settings。
- force_task：d_hold、原body成员、绝对half N目标、+x方向、厚度／对称合同、anchor声明与fresh测量、q未知的运动合同。
- 每接受态：P_target_half_N、generalized_body_internal_force_half_N、g/S_P/bound、body_q_mm、input_mean_mm、R_input_N、原free/mean/global门、J/Hu、material／regularization／total ON-body、互斥外载账本。
- 原split两字段、实际positions、accepted state/fields归档身份、请求目标序号及内部二分标记；全部Newton／trials／linear诊断、失败记录及调用计数。

只保存本接受态缓存，save-time F/T=0；实际q与载荷各有单位字段。不得重命名旧d字段后混用N和mm。原父结果／资格保持，HP／纯压力／承载极限／释放／稳定性／HF5不随新schema自动变true。

## 错误与partial

|阶段|拟行为|
|---|---|
|非法新设置／载荷／输出|invalid_settings或invalid_input，清楚区分mm与N；拒绝覆盖原树|
|来源错／约束冲突|invalid_saved_state或constraint_conflict；来源反例在F/T前拒绝|
|fresh初态不平衡|initial_state_not_equilibrated，检查1后零修正／零接受态，不二分锚点|
|路径数值失败|保原singular_tangent／nonfinite／invalid_J／constraint_failure／newton_limit／backtracking_failed／time_limit等明确原因及新g值|
|缓存或门失败|persistence_failure或明确force_acceptance_failure；保实际已有文件，不自动回滚或补算|

新函数的内部回溯／N二分可在冻结上限内发生；外部不得用重复API调用冒充同一窗口续跑。不把“未找到静力平衡”包装成“释放成功”。未来真实任务应用位移限值与工程承载条件尚需另定；本接口先完成总力平衡功能。

细节来源见[独立接口核查](author/API_REVIEW.md)、[数学核查](author/MATH_REVIEW.md)及[审阅取舍](author/REVIEW_DECISIONS.md)。
''',
'SMALL_MODEL_VALIDATION.md': '''# 有限小模型验证方案（尚未执行）

2026-10-23。L-CTIPFLOADPREP1。验证对象是“外载入口→未知q→正确总力平衡”，不是压力、承载极限或稳定性。下一候选只运行有限清单；不因可用内存较大而扩大到真实r9路径。

## 全新16格fixture与交叉检验

未来在新短目录重生成原guided-probe测试相同的4×4 Q1／16格／25节点／50DOF几何，不读取任何历史NPZ。域2×2 mm、h.5、E1 MPa、ν.3、厚度2 mm、γ1e−6、α1e−4、Lr2 mm；这是原软件fixture的参数，正式r9／厚度20／α2.5e−7条件不改。

solid底向上四行[1111,1111,1000,1000]；工件圆r.375、center(1.25,2)，cell14、nodes[17,18,22,23]。支撑nodes[0,5]；input nodes[10,15,20]的ux权[.25,.5,.25]；output nodes[4,9]的uy权[.5,.5]、spring0。顶背景uy与body重叠DOF[45,47]去重。原fixed15／free35，力控只新增一个刚体q未知，不把body节点全部独立放开。

顺序共享且各只一次：

1. 新固定父路径[0,.0005] mm，完整末峰成功后保存原split/R。
2. 现有位移probe从该父q0执行[0,.00025,.0005] mm，产生本次自己的有符号Q0、Q1、Q2。
3. 若三个原目标的Q有限且严格递增、Q0非零，则新力控另从同一固定父q0开始，仅输入绝对P=[Q0,Q1,Q2]，求未知q；不从位移终点热启动、不输入预期q。条件不符就停止报告fixture不满足本卡前提，不反号、重挑点或放宽规则。
4. new minimum_force_increment_half_N=min(Q1−Q0,Q2−Q1)/16 N；max_bisections4。原父／位移probe自己的minimum_increment=.0005/16 mm保持，两种单位独立记录。力tol与原门按TASK_SPEC，clock各≤60秒。实际场景数在源码冻结时复核。

原目标精确配对，新增内部二分态完整保留但不凑成额外参考点。正式LOW1的P0/P1不套到这个小域。这里只检当前fixture的局部分支；没有预授相同q、唯一性、稳定性或真实夹持可行性。

## 唯一有限清单

拟唯一pytest目标为原`test_split_displacement.py`和新增`test_native_guided_force.py`：原8方法／9展开项＋新8个非参数化方法＝17展开项。下面8行是方法，不是循环场景或真实物理路径数；新测试每个有限循环的精确调用数须候选静审冻结。

|新方法|必须识别的功能／已知错误|
|---|---|
|1 非对称代数oracle|独立dense方程解w/q/R；两向body/free耦合都非零且不互为转置，检P符号、body求和非平均及half/full口径|
|2 fresh锚点|分别坏R、坏mean、坏P0在首检后失败且无projection／线性修正；正确锚点split/R位身份保持|
|3 真实q↔P交叉|上述共享三条路径；只给P求未知q，检原门、新g门、原请求与内部态分类|
|4 缓存／分量／账本|复用共享新缓存，total/material/Hu、厚度一次、显式P与guide／zero去重、全局外载闭合，save-time F/T=0|
|5 真实partial|新力控路径首态后受控第二次tangent终端异常，保首态／实际文件／原身份；这是注入持久化测试，不称真实物理奇异|
|6 来源拒绝|用本次新父副本的source/model/task/lift/fluctuation五个有限错误，F/T前拒绝；不读旧归档|
|7 有限输入／设置／约束|带单位最小力步长、空／非有限／重复载荷、未支持模式、输出覆盖／父树内、body端口／支撑冲突；显式有限循环，不枚举通用防御平台|
|8 旧代表性代数兼容|默认fixed的非零lift保护与原规定q探针的常量mean仍正确；三份新增源码不改旧行为|

真实路径上限：新增16格4条（父、位移参考、新力控、真实kernel注入partial）；原模块2格／12DOF真实路径1条，总至多5条。新增注入／拒绝控制调用至多32次，原11次synthetic另列，总至多43次；partial在两轴标注重叠，不重复称物理覆盖。新full/chunk双模式不隐含在清单中：本卡真实小路径只测full；正式chunk256真实任务须后续另核。

## 验收门及回归精度

- 各真实接受态都满足TASK_SPEC的rho_F≤1e−9、rho_P≤1e−9、原mean、J>0、global≤1e−6、rigid／zero≤8e−11 mm；fresh检查1并保原字节。
- 独立线性oracle：该有界fixture量级下rtol1e−12／atol2e−14，比较解与残差的单位分别明确，R不套mm绝对门。
- 真实交叉在同一P目标下，未知q与既有位移参考abs差≤1e−8 mm；全场物理位移max差≤1e−8 mm；R差≤max(1e−12 N,1e−7*abs(R_ref))。这些是事先声明的小模型功能回归界值（q端点尺度.0005 mm下约2e−5相对），不是新非线性残差门、严格误差上界或正式r9精度保证。候选记录reduced切线灵敏度／conditioning诊断；若不满足即失败，不能按实际结果放宽。
- 不要求两种控制器的非线性终点逐位相同；仅fresh锚点要求原状态与R字节身份。force equilibrium、cross-q、单位／账本分别通过，不能一个抵另一个。
- 不同求和顺序的分量重组才使用8eps×对应原local项L1、无地板；它不是q回归或非线性收敛容差。全局外力必须使用显式P并删除旧body-x独立support项，防双计。
- 不新增力核或切线，故本卡采用独立非对称代数oracle＋真实q↔P作为功能验证，不额外重跑旧HP／大模型导数审计。数学报告提出方向差分作为可选增强，本轮不将其暗加为未计数科学调用；日后若出现导数证据缺口再单列。

## 输出、显示及资源

全部通过后只从本次小模型缓存生成一张实际×1变形／P–q／机构R／双残差与J／收敛PNG，root检查一次；新未知q要与参考q分列，不画成强制位移。保原值、P0预载、ΔP、material/Hu及全部失败历史。没有大模型动画、旧媒体打开、HP或新科学验收关联。

候选上限建议：tests300秒、显示60秒，共享helper480／outer540秒，采样8GiB、四库线程上限16、CPU、不启GPU。各新增真实控制器≤60秒，四条名义≤240秒，旧真实15秒，余量覆盖导入及有限反例；这是可用上限而非实测耗时保证。源冻结、静审、唯一命令、读取集／计数与阶段余量另在候选完成后绑定，不能直接运行当前文档。

首错停止后续显示／安装，无外部重试、修复重跑、延期或force，保实际partial；全部通过才安装两份已测新生产文件，旧55份源码保持。不含真实r9力控；完成后根据小模型实际结果再安排正式.50 mm/P0→P1交叉检查。详见[候选卡](L-CTIPFLOAD1_CARD.md)。
''',
'L-CTIPFLOAD1_CARD.md': '''# L-CTIPFLOAD1：最小力控实现与有限小模型验证候选卡

2026-10-23。**待批准；当前只有规格／接口／验证方案，没有力控实现候选、冻结命令或数值结果。** 本卡是下一阶段可审查的具体范围，不是本轮准备授权的延长。基线main 2b3b6ecbc038fe32554cee4889637f3a2fb2e4ec；当前准备发布提交是后续实现的新起点，应在候选冻结时再绑定。

## 获批后的唯一范围

先编写、冻结并有限静审两个新模块split_guided_force.py／native_guided_force.py及一个新测试test_native_guided_force.py；保持原55份生产源码、fixed／位移probe／CLI／native_response／力核／非对称切线／SUP2不变。若三新增文件边界不可完成，停止说明，不自行改旧接口。复用_admit的身份准入、新鲜F/T与缓存模式，不扩成通用刚体平台。

未知w_F/q/R，P为half N绝对有符号合外载，q未知；工件uy=0／转角0，保持父机构均值、成员、原条件及适用原门。fresh P0匹配非零预载、不修复；N最小步长显式，新增g门与merit按[TASK_SPEC](TASK_SPEC.md)，不用原mm步长。原body-x保持反力从新外力账本删除，以显式P替代，不双计。

静审通过才启动唯一验证窗口：原test_split_displacement九展开项＋八个新非参数化方法，共17项，命令形式`python -X utf8 -B -m pytest -q -x -p no:cacheprovider`；候选树、显式两模块路径、短basetemp、计数和SUP2命令必须在启动前冻结，不在正式目录临时运行探索。各有限循环计数按候选实码核对，若与[方案](SMALL_MODEL_VALIDATION.md)不符，启动前修订并审阅，不以真实运行发现包装错误。

## 实际覆盖上限与资源

共享新16格／50DOF父→位移参考→力控三条真实路径，再一条受控真实partial；另原2格真实路径1条，合计最多5。新注入／拒绝调用至多32，原11另列，总至多43；方法、展开项、反例、真实路径与重叠分别记录。只用本次新几何／父缓存，full模式，CPU；不加载旧科学数组／矩阵或旧媒体。正式r9／chunk256、HP、力控卸载或延伸不在卡内。

tests300秒、显示60秒，共享helper480秒／outer540秒（最多9分钟）；采样8GiB，OMP／OPENBLAS／MKL／NUMEXPR各16线程上限，GPU不用。各新真实controller≤60秒，原真实≤15秒。完整导入、验证、写盘、清理及一次原字节证据封存计入原窗口；复用原SUP2同实例终止／全成员覆盖／句柄释放合同，不改验收。具体阶段时钟／保留余量随薄包装冻结，预算不可挪用已关闭卡。

## 通过、显示、安装与停止

17项、所有适用原门及新增力门／交叉门均通过后，一次纯viewer从新缓存生成一张实际小模型变形／P–q／R／双残差／J与收敛PNG，root最多一次像素检查；无save-time或viewer F/T。全部通过且显示／清理满足后，只安装两个已测新生产文件到hf_repo，新测试与证据按字节交付；旧入口不切换，无旧源码修改或自动回滚。

首个终端错误停止后续科学／显示／安装，保实际候选、partial、调用／失败历史。无外部重试、修复重跑、延期、force、删除、补HP或自动回滚。正常／失败清理后仅原窗口仍足额时允许一次原字节证据封存；不能另开窗口补封或修复。原内部回溯／N二分仅在冻结上限内允许。

包括实际结果记录、普通main推送和同机异目录恢复核对。即使全部通过也只表示受限小模型力控功能；不授正式r9、压力／纯接触、承载极限、释放、稳定性或HF5资格。后续正式任务先审小模型结果再选范围，不自动运行已有LOW1 P0/P1。

新阶段需要批准的原因：用户本轮仅批准规格、接口和小模型方案准备；本卡新增生产实现、真实小模型F/T／平衡测试、显示、安装及独立资源窗口，不能沿用LOW1或本准备阶段的授权。
''',
'author/REVIEW_DECISIONS.md': '''# 独立意见的采用与取舍

2026-10-23。两份独立只读报告是参考，不是用户新增指令。主编根据本项目功能优先、有限验证和不改旧入口的目标作如下取舍；均未执行新力学。

- 采用数学符号／虚功／非对称块、body求和而非平均、非零P0、half/thickness和显式P替代旧body-x外反力账本。未知排序从数学报告(w,R,q)等价重排为(w,q,R)，便于复用原一般LU；两向耦合仍分别装配。
- 采用原SF加独立SP门和固定trial尺度merit；新minimum_force_increment_half_N必填，旧mm字段不参与P二分。P0是绝对总力，ΔP单列，不把小ΔP的相对误差与总力门混淆。
- 采用三个新文件／独立schema，首版不改native_response、parser、CLI或旧controller；不将私有_admit提前通用化。复用不等于声称新模块已经存在。
- 将小模型范围固定为新8方法＋原9展开项、最多5真实小路径；300/60/480/540秒是待批准的上限，不是测得耗时。新精确循环／真实调用／时间余量仍须候选静审后冻结，当前不能启动。
- 小模型q回归1e−8 mm、全场位移1e−8 mm及R门是事先声明的功能精度要求，不声称是已计算条件数给出的严格误差上界。采用接口意见记录局部切线灵敏度／conditioning诊断；不能临时按结果放宽精度。
- 数学报告建议方向差分增强，本轮未纳入下一有限卡：原力核／切线不变，reduced映射为线性，独立双向非对称dense oracle加真实q↔P交叉承担新增控制功能验证。该取舍不声称补了新HP／导数资格；若候选证据揭示缺口，再单独准备所需验证而不暗增调用。
- 首版q为有符号未知，未暗加投影／夹限；真实应用的允许位移与承载成功判据留待小模型结果后另立任务。保持导向、Hu和介质总力，不预授纯接触或稳定性。
'''
}

def main():
    assert git('rev-parse','HEAD').decode().strip() == BASELINE
    assert not git('status','--porcelain'), 'Stop for unrelated workspace changes'
    assert not TARGET.exists()
    rows = json.loads((LOW/'run_001/view/state_table.json').read_bytes())['states']
    assert [r['body_q_mm'] for r in rows] == [0., .025]
    assert [r['Q_drive_half_N'] for r in rows] == [3.686421133658022e-5,4.3272306948756724e-5]
    assert all(r['input_mean_mm'] == .5 for r in rows)
    (TARGET/'author').mkdir(parents=True)
    for name,text in DOCS.items():
        (TARGET/name).write_bytes(text.encode('utf-8'))
    for name in ('MATH_REVIEW.md','API_REVIEW.md','draw_control_schematic.py','control_schematic.svg','control_schematic.png'):
        shutil.copyfile(AUTHOR/name, TARGET/('author/'+name if name.endswith('_REVIEW.md') or name.endswith('.py') else name))
    shutil.copyfile(Path(__file__),TARGET/'author/prepare_force_control_docs.py')
    files=sorted((ROOT/'hf_repo/src').rglob('*.py'))
    assert len(files)==55
    for p in files:
        assert p.read_bytes()==git('show',BASELINE+':'+p.relative_to(ROOT).as_posix())
    sources=files+[ROOT/'hf_repo/tests/test_split_displacement.py',ROOT/'hf_repo/tests/test_native_guided_probe.py',
        ROOT/'docs/WORKPIECE_FORCE_DEFINITION.md',ROOT/'docs/WORKPIECE_LOAD_TASK_SPEC.md',
        ROOT/'docs/GUIDED_WORKPIECE_PROBE.md',LOW/'NEXT_STEPS.md',LOW/'RESULTS.md',LOW/'run_001/view/state_table.json']
    write(TARGET/'SOURCE_BINDINGS.json',{'stage':STAGE,'baseline':BASELINE,'files':[pin(p) for p in sources],
        'scope':'Source/plain-document byte identities; no scientific payload or old media reads. Bindings record the pre-prefix historical state of front docs.'})
    write(TARGET/'PROPOSED_TASK.json',{'schema':'research-guided-force-design-only-1','status':'design_only_not_native_task',
        'parent':{'relative_result':'../lf_circle_tip_low_probe_001/run_001/parent_fixed/result.json',
                  'selected_last_original_index':2,'held_mean_mm':.5,'fresh_anchor_required':True},
        'unknowns':['nonbody_free_fluctuation_mm','rigid_body_q_mm','input_multiplier_R_N'],
        'body_control':{'x':'unknown_common_q','y_mm':0.,'rotation':0.,'remask':False},
        'load':{'axis':'+x','kind':'dead_generalized_total','units':'N_including_source_thickness',
                'model':'symmetric_half','targets_absolute_half_N':[r['Q_drive_half_N'] for r in rows],
                'targets_role':'future_real_cross_check_after_small_model_only','displacement_targets':None},
        'reference_q_mm_for_post_solve_comparison_only':[0.,.025],
        'production_physics':{'alpha':2.5e-7,'gamma':1e-6,'radius_mm':9.,'center_mm':[80.,40.],
           'right_mm':92.,'regularization_length_mm':80.,'E_MPa':1.,'nu':.3,'thickness_mm':20.,'mesh_mm':.5},
        'minimum_force_increment_half_N':None,'implementation_exists':False,'numerical_launched':False,
        'note':'Future real N step/clock not frozen. Small fixture has its own newly generated Q and parameters.'})
    write(TARGET/'PROPOSED_EXECUTION.json',{'stage':'L-CTIPFLOAD1','status':'candidate_card_not_authorized_or_frozen',
        'new_production_files':['hf_repo/src/hf_eval/split_guided_force.py','hf_repo/src/hf_eval/native_guided_force.py'],
        'new_test_file':'hf_repo/tests/test_native_guided_force.py','old_production_edits':0,
        'new_nonparametrized_methods':8,'legacy_expanded_items':9,'total_expanded_items':17,
        'maximum_new_real_16cell_paths_including_injected_partial':4,'maximum_legacy_real_2cell_paths':1,
        'maximum_total_real_paths':5,'maximum_new_injected_or_rejected_calls':32,'legacy_injected_calls':11,
        'test_seconds':300,'viewer_seconds':60,'helper_seconds':480,'outer_seconds':540,
        'sampled_memory_bytes':8*1024**3,'thread_limit_each_library':16,'backend':'CPU','new_HP':0,
        'candidate_sha':None,'unique_command':None,'full_candidate_read_set':None,
        'real_r9_force_path_in_scope':False,'numerical_launched':False,
        'first_terminal_error':'stop_later_science_display_install_preserve_actual_partial',
        'retry_repair_extension_force_rollback_delete':False})
    write(TARGET/'author/authorization.json',{'stage':STAGE,'scope':'preparation_only',
        'user_request':'先准备导向轴向力控制的最小任务规格、接口及小模型验证方案，明确非零预载、半模型载荷口径、未知工件位移和验收条件。保持其余物理条件，做好记录和示意说明，再根据准备结果安排实现与试算。',
        'implementation_authorized':False,'scientific_execution_authorized':False})
    write(TARGET/'author/SCHEMATIC_QA.json',{'status':'PASS_concept_schematic_only','root_pixel_inspections':2,
        'layout_revisions':1,'old_media_opened':0,'finite_element_result':False,
        'finding':'Both controls/unknown q/preload/half units/guide/free-right labels readable. Symmetry-plane label moved once to separate it from d_hold. Concept only, not actual geometry or contact.',
        'png':pin(TARGET/'control_schematic.png'),'svg':pin(TARGET/'control_schematic.svg')})
    write(TARGET/'PREPARATION_RESULT.json',{'stage':STAGE,'status':'prepared_pending_final_static_review',
        'baseline':BASELINE,'created_utc':datetime.now(timezone.utc).isoformat(),'production_source_unchanged':55,
        'new_implementation_files':0,'new_tests_written':0,'new_test_executions':0,'new_model_builds':0,
        'new_F':0,'new_T':0,'new_HP':0,'new_equilibrium_paths':0,'scientific_array_reads':0,'old_media_reads':0,
        'concept_diagrams':1,'numerical_pass':None,'scope':'Specification/interface/finite-validation preparation only'})
    print(json.dumps({'stage':STAGE,'status':'prepared_pending_final_static_review','documents':len(DOCS),
                      'source_bindings':len(sources),'production_files_unchanged':len(files),'target':str(TARGET)}))

if __name__=='__main__':
    main()
