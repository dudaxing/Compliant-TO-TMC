# 最小导向轴向力控任务与验收合同

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
