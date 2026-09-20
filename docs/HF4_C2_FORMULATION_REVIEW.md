# HF4-C2：局部负节点反力的公式与离散解释审查

日期：2026-09-21。范围：只读冻结的 P26 矩形 Q1 / split 内核、C1 任务和高精度读回器；新增代数 helper、制造场计算和本报告。**没有求解新的有限元平衡路径，没有改变 C1 的材料、网格、边界条件、数值门槛或历史证据。**

结论：目前没有证据把这四个 TMC 末态的局部负节点反力归为符号、梯度、Hessian、反力组或系数实现错误。负值是保存位移在当前弱式上的真实离散节点反力，但它不是直接材料边界牵引的同义量。四态的 18 个负节点，其直接顶边材料牵引投影均为正的 model-on-plane 力；144 条顶边还满足整边材料法向应力压缩的解析充分条件。节点材料力减直接边投影，可由明确的离散应力插值场分部积分精确分解；负节点处主要差额来自该插值场的散度体项。这个结论不等于证明连续介质强平衡、不等于证明一般单边接触律，也不决定应采用哪一种后续离散。

## 1. 范围、符号和来源

本报告把三类论据分开：**代码事实**来自冻结文件；**推导**是对该离散的代数结论；**实测**来自新增制造场及四个已保存末态的读回。末态读回由并行诊断脚本完成，本报告读取其输出，不重复求解。它覆盖 C1 的四个 TMC 末态，既不是 C1 的 80 个正式状态全审计，也不包含旧中止路径的额外 4 个状态。

- 参考坐标为 \(X,Y\)，每个局部单元节点顺序 BL、BR、TR、TL，DOF 顺序每节点 \([u_x,u_y]\)。\(h_x,h_y\) 是参考边长，面外厚度 \(t=1\) mm。应力单位 N/mm²，节点力 N。
- 本报告公式中的 \(r\) 均取 **internal / constraint-on-model** 符号。没有该 DOF 的其他外力时，固定 DOF 的约束反力等于内力。图表的 **model-on-plane** 取 \(-r_y\)；所有分解项必须一起取负，不能只翻转主项。
- 顶边直接材料投影定义为 \(t\int_{\Gamma_t}N_a Pn\,dS_0\)，\(n=(0,1)\)。这以参考弧长积分；不能再重复乘变形面积 Jacobian。它仍是材料项的名义牵引投影，不自动成为完整 HuHu 弱式的接触压力。
- 虚功口径已与 `contact_c2_fields.py` 协调：比较 \(v^Tr\) 与保存场逐积分点的 \(P:\nabla v+k_re^{-5J}Hu:Hv\)；材料和正则分账。虚位移包括全域平移、全顶面单位 y 位移、负节点集合、单个负节点和全域仿射 y 场。

核心代码位置（行号针对本报告绑定字节）：

|文件|本轮核查位置与内容|
|---|---|
|`hf_repo/src/hf_eval/split_kernel.py`|40–61：split 运动学；87–124：Piola、材料和 HuHu 残差；127–131：对实际残差求 Jacobian；219 起：全局装配。|
|`hf_repo/src/hf_eval/tmc_kernel.py`|47–66：矩形 Q1 梯度、Hessian 和九点权重；138–190：同一弱式的 unsplit 单元。|
|`hf_repo/src/hf_eval/tmc.py`|50–91：矩形局部次序、DOF、算子和稀疏装配索引；103–120：通用矩形构造。|
|`hf_repo/src/hf_eval/contact_c1.py`|18–27：物理常数；90–112：域、材料倍率、正则系数和约束；146–158：反力组；160–165：独立的平均位移测量权重。|
|`hf_repo/scripts/hf4_split_precision_reference.py`|独立 Decimal 运动学、Piola、HuHu 及其方向导数；固定 DOF 反力和材料/正则分账。未引用生产材料内核或 AD。|

历史来源沿用 [PAPER_FORMULATION_AUDIT.md](PAPER_FORMULATION_AUDIT.md)、[TMC_SOURCE_AUDIT.md](TMC_SOURCE_AUDIT.md) 和 [HF0_REPORT.md](HF0_REPORT.md)。本轮重读这些报告与 `hf0_audit/tmc/assembleKtFi.m.numbered.txt`、`initializeFEA.m.numbered.txt`，未运行 MATLAB。P26 Eq.(4)、Eq.(6)、附录 A4–A6 及 MATLAB 的 `assembleKtFi:65–81` 支持本文弱式；P26 Eq.(A7) 的 \(1-\nu\) 印刷问题不能据此改掉源码实际采用的 \(\mu=E/[2(1+\nu)]\)。

P26 已核 PDF 的 SHA-256 为 `5451a9282d4fe235c0514d55954f5c0ac6033cf9103e391e05505a0c65bf3717`；P25 为 `e1cdcd2485859f08d601e2c668c00c6708c623774a84ab6d5625dffe35010b3c`。本轮没有重新下载或复核其出版信息。P25 的材料律、Q2 和 HuHu−LuLu 是不同模型；不能混作当前 Q1 代码的应然实现。

## 2. 实际弱式与切线

**代码事实。** 每个参考矩形内 \(F=I+\nabla u\)、\(J=\det F>0\)，材料使用

\[
P=\mu F+(\lambda\ln J-\mu)F^{-T}.
\]

生产 split 算子先分别求 \(\nabla u_L,\nabla u_w\)，再形成 \((I+\nabla u_L)+\nabla u_w\)，不先把两组节点位移舍入相加。近单位矩阵分支使用
\(B=G+G^T+GG^T=FF^T-I\)，计算 \(\mu BF^{-T}+\lambda\ln J F^{-T}\)，与上式代数相同。辅助二类 Piola 不用于材料内力。

对 Q1 虚位移 \(v\)，保存权重 \(w_{Kq}\) 已包含参考面积 Jacobian 和厚度：

\[
R_m(u;v)=\sum_{K,q}w_{Kq}P_{iJ}v_{i,J},\qquad
R_r(u;v)=\sum_{K,q}w_{Kq}k_re^{-5J_q}u_{i,JK}v_{i,JK}.
\]

正则是逐单元 **broken Hessian**：没有额外装配梯度跨面跳跃分布、面通量或 C0 内罚项。该事实界定了本实现，不是声称实现了一个 C1 共形的连续二阶梯度边值问题。

对方向 \(z\)，正确的实际残差导数是

\[
D R_r[u;v][z]=\sum_{K,q}w_{Kq}k_re^{-5J_q}
\left[Hz:Hv-5\,DJ[z]\,(Hu:Hv)\right],\quad
DJ[z]=JF^{-T}:\nabla z.
\]

因此切线可以不对称。不能把 \(\tfrac12k_re^{-5J}Hu:Hu\) 当作当前正则势能再对它求两次导数：那会给残差增加当前论文弱式和源码中都没有的 \(\delta e^{-5J}\) 项。生产 JAX 对实际残差求 Jacobian，Decimal 参考显式保留上式的 \(-5DJ\) 项；这一点一致。

## 3. 材料节点力何时等于顶边 Piola 投影

### 3.1 连续单元分部积分

对足够光滑的单元应力场，

\[
t\int_K P:\nabla v
=t\int_{\partial K}(Pn)\cdot v-t\int_K(\operatorname{Div}P)\cdot v.
\]

将顶面节点的有限元帽函数 \(N_a\) 在所有邻接单元中装配，材料节点力与直接顶边投影之差包含：

\[
r_{m,a}-t\int_{\Gamma_t}N_a Pn
=t\int_{\Gamma_{\rm other}}N_a Pn
+t\sum_{f\in\mathcal F_{\rm int}}\int_fN_a\llbracket Pn\rrbracket
-t\sum_K\int_KN_a\operatorname{Div}P
+\text{积分离散差额}.
\]

跳跃定义为相邻两单元的**外法向牵引之和**。角点的帽函数在侧边也非零；一般顶面节点的帽函数延伸进体内和邻接单元内部边。因此“节点在顶面”不能消去这些项。自由 DOF 上总残差很小，也不意味着每个单元的材料 \(\operatorname{Div}P=0\)、内界面牵引连续或材料项单独平衡。

二者相等的充要条件是上述合计差额为零。较强的充分条件是：相容且足够精确的积分、单元内材料强平衡、内界面牵引连续，以及该帽函数支撑上的其他外边界在所测分量上零牵引。均匀材料仿射场的恒定应力可满足体项和界面项消失；顶角点还需侧面剪切贡献为零。

### 3.2 九个应力样值上的精确离散分解

上述连续解释不是本轮唯一证据。对每个单元，将现有九个 Lobatto 应力样值明确插值为双二次 \(P^I(\xi,\eta)\)。在 \(-1,0,1\) 节点上的微分矩阵为

\[
D=\begin{bmatrix}-3/2&2&-1/2\\-1/2&0&1/2\\1/2&-2&3/2\end{bmatrix},\qquad
\partial_X=2D_\xi/h_x,\quad\partial_Y=2D_\eta/h_y.
\]

Q1 的 \(N_a\) 与该插值场满足每坐标次数不超过三的乘积条件，三点 Lobatto 因而给出精确的 summation-by-parts（SBP）恒等：

\[
Q_K(P_q:\nabla N_a)=Q_{\partial K}(N_aP^In)-Q_K(N_a\operatorname{Div}P^I).
\]

**这是任意九组应力样值上的代数恒等，不要求真实的非线性 \(P(F(X))\) 恰为双二次，也不宣称 \(\operatorname{Div}P^I\) 是其真实连续导数。** 在当前矩形网格，新增 helper 返回逐节点

\[
r_m-t_{\rm top}^{Q}=t_{\rm other}^{Q}+j_{\rm internal}^{Q}-b_{\operatorname{Div}P^I}^{Q}.
\]

helper 是 [contact_c2_sbp.py](../hf_repo/scripts/contact_c2_sbp.py)，接口
`decompose_material(fixture, elements, precision=80, thickness=1.0, identity_limit="1e-45")`。它只接收已重建的 Decimal 应力、单元力和普通模型数组，没有本构评估、自动微分、求解器或文件 I/O。其 `fields` 中所有向量用同一 internal 符号；`status` 仅检查新增代数恒等。

保存的 binary64 体积分权重不能静默换成理想实数权重。helper 验证精确分解 \(w_{ij}=cW_iW_j\)、\(W=(1,4,1)\)，边权取水平边 \(6cW_i/h_y\)、竖直边 \(6cW_j/h_x\)。该规则隐含的厚度 \(t_Q=36c/(h_xh_y)\) 与声明厚度 \(t\) 有约 \(5.55\times10^{-17}\) 的相对差；把它混入严格恒等会造成伪失败。因此另存物理厚度下的 Simpson 顶边值和

\[
\texttt{top\_weight\_correction}=t_{\rm top}^{Q}-t_{\rm top}^{\rm physical,Simpson},
\]

使 \(r_m-t_{\rm top}^{\rm physical,Simpson}\) 等于三项之和再加该修正。**它不把 Simpson 值冒充已收敛的真实非线性边积分，也不把这一极小权重差当作观察到的负反力成因。**

## 4. HuHu 的边、角点和内界面项

### 4.1 逐单元一般分部积分

设 \(M_{iJK}=k_re^{-5J(X)}u_{i,JK}\)，对光滑单元场作两次分部积分：

\[
t\int_K M_{iJK}v_{i,JK}
=t\int_K\partial_K\partial_JM_{iJK}v_i
+t\int_{\partial K}\left[M_{iJK}n_Jv_{i,K}-(\partial_JM_{iJK})n_Kv_i\right].
\]

在直边上取逆时针边界方向切向 \(\tau\)，记 \(m_{nn}=n_JM_{iJK}n_K\)、\(m_{n\tau}=n_JM_{iJK}\tau_K\)。逐边形式为

\[
t\int_e\left[m_{nn}\partial_nv_i+
\{- (\operatorname{Div}M)_Kn_K-\partial_s m_{n\tau}\}v_i\right]
+t[m_{n\tau}v_i]_{e,\,\rm start}^{e,\,\rm end}.
\]

角点系数是入边 \(m_{n\tau}\) 减出边 \(m_{n\tau}\)。内部边要把两侧外法向形式一起装配；C0 位移只保证 \(v\) 连续，不能把两侧法向导数项自动抵消。点态 \(e^{-5J(X)}\) 通常变化，故其体项、边项、角点项须联合考虑；只挑一个节点正则力称为表面牵引不成立。

### 4.2 当前矩形 Q1 上的精确简化

Q1 每个分量 \(u_i=a_i+b_iX+c_iY+d_iXY\)，所以

\[
Hu_i=\begin{bmatrix}0&d_i\\d_i&0\end{bmatrix},\quad
d_i=\frac{u_{BL,i}-u_{BR,i}+u_{TR,i}-u_{TL,i}}{h_xh_y},\quad
HN_a{}_{XY}=HN_a{}_{YX}=\frac{\sigma_a}{h_xh_y},\quad
\sigma=(1,-1,1,-1).
\]

令 \(C_K=k_r\sum_qw_{Kq}e^{-5J_q}\)，则

\[
r^K_{r,ai}=\frac{2C_Kd_i}{h_xh_y}\sigma_a
=\frac{2C_K}{(h_xh_y)^2}
(u_{BL,i}-u_{BR,i}+u_{TR,i}-u_{TL,i})\sigma_a.
\]

这里的 **2** 来自 XY 与 YX 两个混合导数，不能删掉其中一个。即使 \(J_q\) 不均匀，所有变形缩放仍只进入单元标量 \(C_K\)，节点符号模式不变。

对 Q1 测试空间，该离散泛函可等效为常数矩张量 \(\bar M_{iXY}=\bar M_{iYX}=C_Kd_i/(t h_xh_y)\)。它的体项和直边导数项为零，\(m_{nn}=0\)，剩下四个角点力 \(2t\bar M_{iXY}(1,-1,1,-1)\)。这是一种**离散等效表示**；并不声称点态 \(k_re^{-5J(X)}Hu\) 是常量，也不赋予它唯一的连续边界物理解释。

### 4.3 全顶面正则合力为何必然抵消

每个顶层单元的 TR、TL 力互为相反数，所以当组向量对**完整平直数值顶面所有节点取单位权重**时，

\[
\sum_{a\in\Gamma_t}r_{r,ai}=0
\quad\text{对所有允许的节点位移成立；因此}\quad
\sum_{a\in\Gamma_t}(K_rz)_{ai}=0.
\]

同一结论可由虚位移得到：全顶面单位 y、其余节点零的 Q1 场，在每个顶层单元是仅随 y 线性变化的场，单元 Hessian 为零。全域平移和仿射虚位移也均不接受 HuHu 虚功。

这是该矩形 Q1、完整边和单位节点求和的结构恒等，**不是均匀压缩的偶然结果，也不是正则项很小或实现漏装的证据**。单个节点、负节点子集或半权组可以有非零正则合力。变更为 Q2、非仿射单元、其他 Hessian 映射或不同边界选取后不能直接沿用这个结论。即使全顶面直接正则合力为零，正则仍可改变位移场，从而间接改变材料反力。

## 5. 可证伪核查与结果

### 5.1 独立制造场和多单元算子核查

脚本、结果均只新增于 [formulation_review](../hf4_c2_diagnostics/formulation_review/)，第一次小型程序执行遇到测试 fixture 缺少 `fixed_dofs` 的设置错误；补齐该测试输入后执行成功。没有改变公式或预设容差，失败尝试没有生成或覆盖结果 JSON。

|核查|方法|结果|
|---|---|---|
|任意正则单元权重下完整顶边抵消|固定 seed `20260921`，8 个 3×2 矩形 patch；节点值和任意正单元积分系数全用 Fraction；检查每元角点力和装配顶边和|8/8 精确相等，且每例都有非零局部顶节点正则力。|
|材料、正则和方向导数|零场、仿射压缩剪切、双线性场、近单位场；新 Decimal 80/120 公式与旧 HP helper、split/unsplit 单元核对比；没有 Newton 迭代|4/4 通过；HP 最大归一误差 `6.56919666208845e-80`，生产比较最大 `5.51373419134072e-16`。|
|应力与装配符号|独立 \(P\)、\(F S=P\)、Q1 梯度/Hessian、全顶面正则与其 Jv、单元 SBP、角点等效表示|同上预设门内通过。|
|两单元内界面及散度|4 组给定应力多项式：连续常量、常量跳跃、连续仿射散度、双二次跳跃；期望值用 Fraction 在物理坐标中的单项式原函数积分，不使用 Lobatto 微分矩阵|80/120 共 56 个分量向量比较通过；最大 `4.00499687890016e-79`；显式验证界面两侧外法向跳跃方向。|

HP 新诊断门为 `1e-45`，生产单元比较门为 `1e-12`，分母 `max(reference norm, 1)`（力为 1 N；同表其他量按其声明单位）。这些是新增代数核查的预设门，**不替换、放宽或追加到旧 C1 路径准入门上**。四个给定应力多项式不必来自某个位移的材料律；它们只验证 SBP 算子。

一个可直接反驳“负节点力必为拉伸材料压力”的制造场是单位方形
\(u_x=Y/8,\ u_y=-Y/64\)，其 \(J=63/64>0\)、\(Hu=0\)。两个顶节点的直接 on-plane 材料边投影均约 `+1.06722138857 N`，但右上节点的 on-plane 材料弱式力为 `−1.43246734270 N`，左上为 `+3.56691011983 N`。差额完全来自左右侧剪切牵引。**该制造场不是 C1 自由侧边平衡解**；用途是证伪节点力与压力的普遍等同，不用于归因真实末态。

### 5.2 四个保存 TMC 末态：更直接的证据

读取 [fields_001/summary.json](../hf4_c2_diagnostics/fields_001/summary.json) 和四个 case JSON。它们复用当前 helper，对 80/120 场重建、装配、虚功和 SBP 检查各有 103 项，共 412 项，最大归一误差 `1.53137469326338e-75`。这里 `status=pass` 的语义是新代数/精度一致；高阶边积分收敛观察另有 `not_pass`，不被这个状态掩盖。

|保存路径末态|状态身份|负的总节点力个数|负节点总和 N|整条顶边材料压缩证明|
|---|---|---:|---:|---:|
|TMC h=.25，均匀 d=.5|`uniform_tmc:14`|2|−0.0416250118299|24/24|
|TMC h=.125，均匀 d=.5|`uniform_tmc:18`|4|−0.00988771056111|48/48|
|TMC h=.25，扰动幅 .0625，平均驱动 .375|`perturbation:4`|4|−0.0111782428429|24/24|
|TMC h=.125，扰动幅 .0625，平均驱动 .375|`perturbation:4`|8|−0.00250444314026|48/48|

此处集合由**总节点力为负**选取。不能把 case `aggregate.material.negative_sum_N`（由材料项自身正负重新选集）直接与该集合的材料贡献相加核账。相同总负节点集合的材料/正则分账仍与冻结 `local_reaction_diagnostic.json` 一致。

整边证明来自该 Q1 顶边 \(u_y\) 常数，故 \(F_{yx}=0\)、\(a=F_{xx}>0\) 为常量，而 \(b=F_{yy}\) 沿边线性。\(b\) 两端均正且 \(P_{yy}\) 两端均负时，

\[
bP_{yy}=\mu b^2+\lambda\ln(ab)-\mu,\qquad
\frac{d(bP_{yy})}{db}=2\mu b+\lambda/b>0
\]

（本例 \(\mu>0,\lambda\ge0\)），因此整条边 \(P_{yy}<0\)。144 条顶边均满足保存的条件，18 个弱负节点的直接材料边投影全部为正。这比只看若干积分点符号更强；依然只是**材料应力**的命题，不是接触主动集或完整二阶弱式边界条件的证明。

下面两行均已整体转为 on-plane 符号，单位 N；顶边投影为物理厚度的 Simpson 值，与 SBP 恒等对账：

|量|粗均匀，参考 x=−.25，node 132|细扰动，参考 x=−.125，node 505|
|---|---:|---:|
|材料弱式节点力|−2.05290881546e-2|−8.74624079552e-4|
|直接材料顶边投影|+2.54787889018e-4|+2.63487914178e-4|
|其他外边界项|0|0|
|内界面跳跃项|+1.27541907427e-6|+1.29418220278e-7|
|`minus_projected_div_N` 项（已取 on-plane 负号）|−2.07851514627e-2|−1.13824141195e-3|
|顶边权重修正|−1.41435690392e-20|−1.46265174515e-20|
|正则弱式节点力|−2.83417760338e-4|−3.58156138840e-4|
|总弱式节点力|−2.08125059149e-2|−1.23278021839e-3|

所以这里可定位的是：**在既定九点材料弱式中，插值应力的散度体项主导“材料节点力−顶边材料投影”的负差额；另有非零正则节点贡献。** 这没有把 \(P^I\) 的散度解释成实际连续体力，也没有证明重新平衡后的另一种积分/正则模型会给同样的节点力。

边积分采用真实 \(P(F)\) 的 Gauss 8/16/32/64 复核；四态 Gauss32→64 节点投影向量归一差分别为 `4.13505e-5`、`2.53669e-5`、`2.54319e-5`、`4.09613e-6`，都未达预设 `1e-8` 观察门。因此不能将 Gauss64 数值标成已收敛边积分真值。整边符号证明不依赖这个积分误差门；SBP 的精确样值恒等也不依赖它。

### 5.3 后续解析顶边积分：保留 Gauss 未收敛记录

并行任务随后新增 [diagnose_contact_c2_analytic_edge.py](../hf_repo/scripts/diagnose_contact_c2_analytic_edge.py) 和 [analytic_edge_001/summary.json](../hf4_c2_diagnostics/analytic_edge_001/summary.json)，只在原保存场上求顶边法向材料积分。本报告独立阅读并核对其闭式、级数符号及尾项估计；未改脚本或重新运行四态。

以边参数 \(z\in[0,1]\)、\(f(z)=f_0+bz\)、\(b=f_1-f_0\) 写 \(P_{yy}=\mu f+(\lambda\ln(af)-\mu)/f\)。设 \(L_j=\ln(af_j)\)、\(Q=[\lambda(L_0+L_1)/2-\mu]\ln(f_1/f_0)\)，则

\[
A_0=\int_0^1P_{yy}\,dz=\mu(f_0+b/2)+Q/b,
\]
\[
A_1=\int_0^1zP_{yy}\,dz=\mu(f_0/2+b/3)
+\frac{\lambda\{f_1(L_1-1)-f_0(L_0-1)\}-\mu b-f_0Q}{b^2}.
\]

左右节点 on-plane 法向力分别为 \(-t h_x(A_0-A_1)\)、\(-t h_x A_1\)。\(b=0\) 分支直接给恒定应力。小斜率 \(|r|=|b/f_0|\le1/4\) 时，脚本使用
\(c_n=(-1)^n[(\lambda L_0-\mu)-\lambda H_n]r^n/f_0\)，两矩的非线性部分分别为 \(\sum c_n/(n+1)\)、\(\sum c_n/(n+2)\)，避免闭式消去。

其余项界由 \(H_{n+k}\le H_n+k/(n+1)\) 和几何级数直接得到，忽略矩积分分母只会扩大界；代码的截断目标为声明精度减 8 位的尺度。这个界是精确算术下的**级数截断**界，不是有限精度 roundoff 的区间包围。两个声明精度 80/120 分别由原 split 字节重新构造边端点并运算，44 项新代数/交叉精度检查通过，最大 `3.68440630525869e-74`。

|末态（与上表同序）|保存 Q1 场解析材料顶边净力 N|Gauss64 相对解析节点投影向量的归一误差|
|---|---:|---:|
|粗均匀|71.1949165621812|1.48292208713e-5|
|细均匀|71.4474698274111|3.12179029730e-6|
|粗扰动|30.9900918684611|1.60116766785e-6|
|细扰动|30.8145634103589|2.82554228590e-8|

所有解析顶节点法向材料投影仍为正；Gauss64 的四个误差仍都超过 `1e-8`。解析补充解决了**这个保存平直 Q1 场的法向边积分**，没有把其数值改写为连续平衡/接触真值，也没有覆盖 `fields_001` 的原始结果或把弱式反力替换成边积分。

## 6. 实现错误审查结论与可判别的后续工作

|候选问题|本轮结论及证据边界|
|---|---|
|Piola 转置、力符号错误|代码公式、独立 Decimal 材料场、\(FS=P\)、直接边/弱式/虚功同符号核账一致；制造反例和真实四态都不支持靠翻转符号“修复”。|
|梯度方向或局部网格次序错误|BL BR TR TL、分量交错 DOF、\(\xi\) 慢 \(\eta\) 快和 physical grad 一致；精确单元与两单元界面验证通过。|
|Hessian 少/多一个混合项|代码保留 XY/YX，正确给出系数 2；独立角点表达、单元 Jv 与任意系数 patch 支持该实现。|
|遗漏变形缩放的切线导数|生产实际残差 Jacobian 和 HP 手写 \(-5DJ\) 项一致；不能把非对称性判为错误。|
|正则系数或背景材料误缩放|C1 明确 \(\alpha=\gamma=10^{-6}\)、\(L_{ref}=2\) mm，\(k_r=\alpha L_{ref}^2(K_s+4\mu_s/3)\) 全域作用；背景只缩放两 Lamé 参数。数值域宽 6 mm 没有偷偷替换 C1 的特征长度 2 mm。|
|顶面组或 half-weight 引入假负值|顶面组是所有顶节点 y 的单位权重。半权只用于 bottom_body 与 bottom_outer 的节点分账；它们不是物理接触力分区。负顶节点不由此半权产生。|
|正则顶面合力为零即漏装|不成立：这是当前完整顶面组的 Q1 恒等；局部正则节点力及其场效应明确非零。|
|把固定顶边当成单边接触主动集|TMC 数值顶边固定 uy，未实现乘子非负/开闭互补主动集。这是 C1 已声明的受限任务边界，不能以“正负节点力等于接触压力”补出缺失的接触律。|

本轮未发现须改动冻结内核的实质性实现错误；以上是对所列文件、制造场和四个保存末态的结论，不是任意网格/任意状态的完整正确性证明。下一步建议保持三条可证伪问题：

1. **体积分离散的影响。** 以上解析补充已解决当前保存平直 Q1 场的法向顶边积分；下一步可在同一保存场增加体积分阶数，区分九点体积分的离散差额与真实应力强平衡缺陷。必要时对更一般几何另立边积分误差控制。旧 SBP 恒等继续作为原九点规则的核账，不能用新积分值覆盖旧反力。
2. **正则通过状态变化产生多大影响。** 如运行新变体，在相同几何、材料和边界下冻结正则方案后重新平衡，比较局部场、直接材料牵引、弱式反力及三项分解。仅从当前位移中删去正则节点力得到的是固定场分账，不能代替这个因果实验；完整顶面正则合力始终为零也不能判定影响为零。
3. **背景域/边界与单边接触的区分。** 在固定 \(L_{ref}=2\)、材料和正则系数的前提下单独改变背景驱动/外边界或与合适参考接触分支比较，检查差额位置、网格趋向和总力。若要研究一般脱开/再接触，需另立完整接触参考与互补条件；当前四态和 A0 受限分支不能充当其独立真值。

这些取舍服务于长期目标：在维持独立 HF 内核和可追溯严格数值门的基础上，分清离散计算可复现、几何可接受和接触物理可比较三个层次，再决定是否升级积分、正则、单元或边界模型。不能通过删去负节点、裁剪压力或只比较净力，使尚未判别的问题消失在报表中。

## 7. 证据身份与重现边界

本轮新增可运行脚本仅执行代数/制造场，旧核文件前后 SHA-256 均核验未变。完整源文件哈希和环境存于 `formulation_review/results.json`；两单元测试独立绑定已冻结 SBP helper。结果使用独占创建，不覆盖已有 JSON。

|新增证据|SHA-256|
|---|---|
|`hf_repo/scripts/contact_c2_sbp.py`|`fd85bf4c6ba19f4365198f5b3cbca9ab1247344c585a6d8e74ab53dff687fc21`|
|`hf4_c2_diagnostics/formulation_review/check_formulation.py`|`bd894b546e87d2d4b8d4e633096eaffe9b4b3955038968e5eaa8c6cda17cc43c`|
|`hf4_c2_diagnostics/formulation_review/results.json`|`53a8238e4609fa097dcc8fa73a31fa34b9e1cee1fc7b92e29bc4f3192511d963`|
|`hf4_c2_diagnostics/formulation_review/check_sbp_interfaces.py`|`68351f082b548b751eb5d343458a8e572b48be0b241656d11672afbad7deb3a8`|
|`hf4_c2_diagnostics/formulation_review/interface_results.json`|`6392df0637b6b59a27b71224eeb2cb0a475def900cdf30c5ee6fb03da9616beb`|
|`hf4_c2_diagnostics/fields_001/plan.json`|`3bd4412ef1091d4da5ef3769ae95fa745dd5d4823ede55ea34bd6d5e121a1196`|
|`hf4_c2_diagnostics/fields_001/summary.json`|`ef69caf81b85bb1801e6e7c4ff6522adb17efcd602b058bb279dc77b8ce72d4a`|
|`hf4_c2_diagnostics/fields_001/TMC_h025_uniform_r2.json`|`b05d13b653a97ca1935f9f1047942f229b74964d0b87d136fb2724c09407940d`|
|`hf4_c2_diagnostics/fields_001/TMC_h0125_uniform_r2.json`|`b9788fbda0099d1a54cead67d7c760c390167b9b5bd471106e13561bad5a5444`|
|`hf4_c2_diagnostics/fields_001/TMC_h025_perturbation_r2.json`|`2b95eb2083dc8485b36c57aed6b2ced49c835185260181c5d921441d5fdafff0`|
|`hf4_c2_diagnostics/fields_001/TMC_h0125_perturbation_r2.json`|`cdc84e65d24cc754b58fa97c3c62a98fceefee58eff3a565090e4645864deb35`|
|`hf_repo/scripts/diagnose_contact_c2_analytic_edge.py`|`9aebec1578e5de0965874e290023c1d60eabfc1e587fe1e946c2bdb0903832e2`|
|`hf4_c2_diagnostics/analytic_edge_001/plan.json`|`d719742c8c8e5e4665164136a6b5f0da4af1596197680198d4b4c7cba9f655d0`|
|`hf4_c2_diagnostics/analytic_edge_001/summary.json`|`5e20a965db6e42731d9abcfd54cbfe320eed368c4836ba337a37d8d3f2a95fee`|

主要冻结来源：split kernel `c8eab7260a3862bd26fa7a3f67be819e5dd6e43971ec61407e52660a74763127`；TMC kernel `dba45df22b36e2bf03bec4589d35ab6a37d151bf0c7d89b01fe6763964dfefd0`；C1 builder `f9c2406d673df25a801fcba275399cb84e2928074b95ce3dafc54986d22fdcc1`；旧 split HP helper `308ff44131efebcaf779936779385cfad8fc0b57cb5fc015a3afc34d9adf06d2`。其余源身份见结果 JSON 的 `source_sha256`，四态完整输入链见 `fields_001/plan.json`；路径名和历史绝对环境字符串不替代文件哈希。
