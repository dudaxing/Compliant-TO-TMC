# L-CTIPFREALPREP1：正式两载荷的数学门、工程比较门与资源建议

2026-10-23。独立制定者 `/root/fload_controller`。本轮仅准备规格；只读现有源码、LOW1普通结果说明并对其已存标量作单位算术。**未读NPZ或媒体，未构模、求解、测试、计算新切线或绘图。** 下列门须在未来执行卡启动前冻结，不能按新结果改写。

## 决策及为何选这些比较门

采用端点未知q绝对差≤`1e−6 mm`、全场每DOF物理位移最大绝对差≤`1e−6 mm`、输入R差≤`max(1e−10 N,1e−7*abs(R_ref))`。这些是正式尺寸的**工程功能回归界**，不是严格离散误差界、非线性解误差估计或稳定性门。

q参考为0.025 mm，1e−6相当于其4e−5（0.004%）；相对h=.5 mm为2e−6。它足够区分一个从力解出的局部位移是否返回既有参考响应，又不会把小模型偶然约4e−13 mm的一次实测差抄成正式门。全场采用同一绝对长度界，防止只让刚体q相近而机构其他部分走到另一响应。R保留1e−7相对界和明确N绝对地板，防止近零R出现无意义相对误差；当前正式R_ref约.0859 N，实际由相对项主导。

现有资料不足以在不分析正式新Jacobian的前提下推出严格的位移/R误差上界，因此不伪造此类推导。若这些预定比较门未通过，应保留差异、分开报告数值平衡与工程回归状态，再根据证据诊断；不能自动放宽门、改选载荷或宣称承载极限。

## 正式任务、未知量与非零预载

唯一来源为LOW1完整新固定父 `[0,.25,.50] mm` 的最后原目标：d_hold=.50 mm、q0=0、原selected index2、原signed R=.08589635225389337 N、state SHA `48fd7c621a8b1a060a5bec81307f2c8fe524569c6a4052da75884a8053e45bd8`。下一卡仍须将该真实来源及原缓存身份按实际位置重新绑定，不能用本说明代替来源检查。

保持α2.5e−7、γ1e−6、r9、center(80,40)、right92、Lr80、E1 MPa、ν.3、plane strain、厚度20 mm、h.5、原510工件单元/565节点、支撑及端口。只用已安装 opt-in 力控API，不改默认入口或旧力核/切线，不重做固定父加载。

|量|冻结候选值及解释|
|---|---|
|P0_half|3.686421133658022e−5 N；原q0非零预载，不从零外载重新加载|
|P1_half|4.3272306948756724e−5 N；绝对外载，不是增量|
|ΔP_half|6.408095612176505e−6 N；仅描述及确定N步长|
|minimum_force_increment_half_N|ΔP/16 = 4.0050597576103156e−7 N|
|请求载荷|仅[P0,P1]，严格递增、固定空间+x方向、有符号dead resultant|
|未知|原free fluctuation、工件刚体q、输入R；不向力控传q=.025目标|
|运动约束|工件uy=0、转角0，机构均值保持.50 mm；q不夹限、不取abs|

P是已包含20 mm厚度的半模型合外载，c在各body-x为1，`g=sum_B f_int,x−P_half`；不得给每个节点重复施加P。全装配仅P_full=2P_half，q不倍增。原mm最小步长.00625 mm保留来源，但不参与N二分。旧parent_initial_guess=port_projection仍作父元数据保存；新力控实际初始化是明确的guided reduced tangent，不谎称它仍在执行旧位移控制预测。

## 所有接受态的数学及物理门

未知z=(w_F,q)，刚体选择c，T=[S,c]。保留原实际非对称K的四块 `SᵀKS, SᵀKc, cᵀKS, cᵀKc`，两耦合独立装配；增广未知为(w_F,q,R)。free行`r_F=Sᵀf_int−b_F R`，body行`g=cᵀf_int−P`，mean行`h=bᵀ(lift+fluctuation)−.50`，一般稀疏LU，不以转置、对称化或附加刚度代替实际Jacobian。

|门|固定定义|
|---|---|
|原自由平衡|rho_F=norm(r_F)/SF≤1e−9；SF=max(norm(f_int[F]),norm((bR)[F]),norm(spring[F]),F_floor)|
|新body合力|rho_P=abs(g)/SP≤1e−9，SP=max(abs(P_target),abs(P0),F_floor)，同一目标内固定|
|原补偿mean|abs(h)≤1e−10*d_scale；d_scale=max(.50,1e−6)=.50 mm，bound=5e−11 mm；从两个split分量补偿测量后扣目标|
|有限/J|原相关字段有限，全部J>0；不能只验minJ摘要而遗漏原fields检查|
|刚体/zero|各body-x与实际未知q、body-y=0及zero误差≤8e−11 mm|
|全局外力|relative global balance≤1e−6；以显式(P,0)替代原body-x support，body-y与背景重叠只计一次|
|新鲜锚点|P0第一次fresh F/T即过全部门，check1、无predictor/projection/linear修复，原两split和R逐位保持|

E*t=20 N/mm，`F_floor=1e−8*(E*t)*d_scale=1e−7 N`，不再乘厚度。P0/P1的SP分别为3.686421133658022e−5、4.3272306948756724e−5 N，对应g绝对bound分别为3.686421133658022e−14、约4.327230694875673e−14 N。这个绝对门与原free残差门独立；大R或良好global合力不能掩盖body失衡。

global账本严格为D=原fixed去body-x、`s_D=(f_int−bR)|D`，其余零；`G=sum_xy(s_D)+sum_xy(bR)+(P,0)`，`SG=max(norm(s_D)+norm(bR)+abs(P),SF)`，比较norm(G)/SG。没有任意body外载节点分配；ON-body弱力和P的平衡也不产生压力资格。

旧checks25、Armijo1e−4、backtracks12、max_bisections4保持。新merit为`.5*(norm(r_F/SF_base)^2+(g/SP)^2)`，每次line search固定base SF和目标SP，保旧下降因子。mean可行补偿只作用非body端口，q永不投影。所有内部二分接受态也必须逐项过相同数学/物理门。

## 端点工程回归：定义、算法与失败口径

只对本次实际原目标P1与LOW1同物理的原q=.025 mm probe终态作比较；内部二分态保原值和完整顺序，但不插值参考、不按q单调增加新门。

|比较|预先冻结门|
|---|---|
|未知q|abs(q_new−.025 mm)≤1e−6 mm|
|全场物理位移|max_i abs((lift_new_i+w_new_i)−(lift_ref_i+w_ref_i))≤1e−6 mm；包括原全场所有DOF|
|输入乘子R|abs(R_new−R_ref)≤max(1e−10 N,1e−7 abs(R_ref))；R_ref=.08589811003453525 N，当前bound≈8.589811003453524e−9 N|

全场差比较物理位移，不比较任意split分解各自的差；建议逐DOF用 `math.fsum([lift_new_i,w_new_i,-lift_ref_i,-w_ref_i])` 保留四个原binary64项的差，最后再取abs/max。不要先生成rounded display或positions再相减。比较器只需已算的两个endpoint split各lift/fluctuation，不需要新F/T；未来执行卡应固定原参考和新输出的读取位置、字段/身份及次数。当前准备阶段没有解码这些数组。

q门、全场门、R门分别记录，均不得替代平衡门；全场包含body-x，故q与全场部分重合是已知检查关系，不应双算成两类独立物理证据。q0锚点仍用逐位身份硬门，不能借用端点1e−6回归界修复来源。

当force API数值成功但任一端点回归门失败，应记录“平衡路径成功/工程比较NOT_PASS”，保原API结果，不篡改其success为另一物理状态。若API失败或没有P1，比较标`not_run`或`incomplete`，不得写零误差。无已批准修复重跑；显式差异、原门和全部partial必须一起保留。

## 有限资源、阶段依赖与停止

同意候选窗口：controller1800秒，纯显示共享600秒，helper2700秒，outer2760秒（最多46分钟）；采样64GiB，OMP/OPENBLAS/MKL/NUMEXPR各上限16，CPU不用GPU，viewer维持原8GiB子限。LOW1原probe实际约381秒及约1GiB峰值是预算参考，新的reduced正式路径尚未运行，不能把原耗时当保证；也不因此扩大到高输入、更多目标或第二种模式。

最终root资源决定（final_root_resource_decision）：API/controller1800秒；科学worker包含导入、来源准入、保存及其清理总计≤1900秒；comparison60秒；显示与root图像QA共享600秒；helper2700秒、outer2760秒。1900+60+600=2560，helper尚余140秒供其他清理及一次原字节封存，不将该余量当作延期额度。

最终包装须明确一个连续helper时钟。controller的1800秒只覆盖其真实内部时钟，source构建、读写、子进程导入和清理也必须包含在worker1900内；比较和显示阶段开始前须保留其完整既定上限及后续清理/封存余量，不够即首错停止。具体子deadline由最小包装静审冻结，总窗不能因为准备或显示较慢而延期，不缩短门、不复用已闭窗口。

仅一次API调用，原P0锚点+一个P0→P1载荷区间；depth4和ΔP/16使最多16个已接受子增量、连锚点最多17态。该上限是完整保留所有内部接受态的容量，不是允许外部16次重试；终端失败时可能只保部分态。有限时间仍是主要上界，不能为凑满17态续时。

第一终端来源/设置/fresh失衡/非有限/J/约束/数值/时限/内存/清理/持久化/工程比较错误停止后续工作，保实际partial；允许的仅是原控制器内部Armijo及有界N二分。无外部重试、修复重跑、force、改α/γ/域、追加目标、fallback指定q、HP、测试、生产修改或自动回滚。成功后仅使用cached fields显示真实变形、反力、P–q、材料/Hu与介质、收敛；显示失败也不补算或重绘。一次原字节完整/部分封存仅在全部相关同实例清理可证明且原窗口仍开放时进行。

首次真实尺寸mechanical/chunk256力控必须在结果中单列；小模型mechanical/full的通过没有提前授予它资格。即使两个正式载荷及所有工程比较通过，也只证明该局部guided总力平衡功能；原HP/压力/纯接触抗拔/承载极限/释放/唯一性/稳定性/HF5状态保持，不沿新result schema自动变true。

本轮来源：已安装 `hf_repo/src/hf_eval/{split_guided_force.py,native_guided_force.py}` 及LOW1的 `lf_data_preparation/native_interface_001/lf_circle_tip_low_probe_001/RESULTS.md` 普通说明。所有新门是本次准备建议，尚不是已执行正式任务的通过结论。
