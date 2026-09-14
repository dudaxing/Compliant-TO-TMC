# 两分量状态实施规范（编码前冻结）

2026-09-14。第0级[固定更新对照](../hf4_repair_results/retained_update_001/summary.json)为gate_pass：完整保留更新的HP80残差6.8902569641e-16，半步9.2051485445e-10；旧舍入更新约1.841e-9。全部5态50/80、域、约束与身份通过。现在按既有授权实施第1级，不改原物理及数值规范。

## 状态与接口

候选版本0.5.0；新增显式接口，旧模块（除版本声明）字节保留。新增`split_state.py`的`SplitDisplacement(lift, fluctuation)`：独立复制、只读、同长正偶数的一维有限实float64向量；`ndof`、`copy()`、`from_legacy(u)`、`u_display`。物理输入是两数组精确和，显示数组每次新建且不可用于力学验收，无隐式重分解。

`split_kernel.py`提供`batch_response_split(lift_e,fluctuation_e,ops,lam,mu,kr,tangent=True)`、`determinants_split(...)`、`assemble_split(model,state,tangent=True)`。返回旧同名场与G、Hu诊断；Jacobian仅对fluctuation求导。

固定运算次序：GL=grad(L)，Gw=grad(w)，G=GL+Gw；F=(I+GL)+Gw。HL/Hw分别缩并，Hu=HL+Hw。近单位分支max|G|<=.01时继续用原增量Piola/log1p/能量；其余用总F的det和直接Piola。不能从已舍入F反算小G。正J守卫的NumPy及两种JAX分支对应同一总运动学，非法域不得进入log/inverse。正则用总Hu与总J的exp(-5J)联合求值，保留实际非对称Jacobian。

`split_prescribed.py`提供`normal_lift_shape(problem)`和`solve_split_prescribed_path(model,base,direction,lift_shape,targets,...)`。同旧规定运动原语，shape在固定DOF必须等于direction；当前任务shape仅由几何决定：下块+y=1、上块0、间隙线性延拓，所有x为0。每目标L=base+d*shape，固定w=0；本轮dyadic实际边界原语精确匹配，通用非dyadic输入不额外加入未保存补偿，仍须满足独立约束门。

推进只有一个转换：delta_L=L(target)-L(old)，用旧实际K解Kff delta_w=-(K delta_L)f，预测w_new=w_old+delta_w；不先rebase。回溯只改自由w；两数组、目标及K缓存整体回滚。保留原SF、35检查、16回溯、8二分、120秒路径上限及其失败/null语义。接受态保存两实际数组；失败保存最后接受态以及失败候选/更新诊断。测力仍用固定DOF和原分侧虚位移，不多乘对称系数。间隙对两数组分别作用并稳定求和。

## 独立HP

新`hf4_split_precision_reference.py`显式实现`DecimalSplitQ1Reference`及`evaluate_split_prescribed_state(fixture,u_lift,u_fluctuation,d,base,direction,reaction_groups,force_scale_per_length,precision=50,*,tangent_direction=None,fluctuation_offset=0,derivative=True)`。直接重建D(L)+D(w)+D(offset)D(v)，普通接受态offset=0；v只扰动w。禁止生产导入，旧独立公式源码保留；输出原始Decimal G/F/Hu/J、材料/正则/总力、能量、Jv、组测量和原HF4 SF。

## 固定小核用例与门槛

制造单元尺寸(1,1)、(1/8,1/16)，t=1，人工lam=2、mu=3、kr=1/8；与真实HF4参数明确分开。局部坐标BL/BR/TR/TL，方向v=[1,-2,3,-1,-2,4,-3,-1]/8 mm。固定用例：

1. legacy：L=(x/64+y/128,-x/256+y/32)，w=0。
2. 纯平移：L=(1/8,-1/4)，w=(2^-45,-2^-44)，R/Hu/能量0，J=1。
3. 小变形：同常量L，w=(2^-45*x+2^-46*xy,-2^-44*y+2^-47*xy)。
4. 强压缩：L=(0,-y)，w=(0,epsilon*y)，epsilon=float(2^-17+2^-60)。
5. lift非法但总合法：L=(0,-1.5*y)，w=(0,(.5+2^-17)*y)。
6. 非零Hu相消：L=(xy/8,-xy/16)，w=(-xy/8+x/32+xy/128,xy/16-y/64-xy/256)；q=(xy/32,xy/64)，核对(L+q,w-q)精确物理和相等。
7. 常量L，w=(a*x,0)，a=.01*(1±2^-10)，覆盖近单位分支两侧。
8. 总J非法：L=(0,-y)，w=(0,0)或(0,-2^-17*y)，应拒绝。

上述人工小核：全/分项力误差<=1e-9*max(||该HP分项||,mu*t*min(hx,hy)*2^-45)；全/分项Jv<=1e-8*max(||该HP分项Jv||,mu*t*||v||*1e-12)；G/F/Hu绝对分量差<=5e-15*max(1,maxabsHP)；正J相对<=1e-9；材料能量<=1e-8*max(|HP能量|,mu*hx*hy*t*2^-100)；50/80全力同尺度<=1e-30。两种生产分支均独立对HP。

固定FD检查：用例6取h=[1e-5,1e-6,1e-7,1e-8,1e-9]；用例4取h=2^-26*[1,.1,.01,.001,.0001]，扰动参数无量纲。全部±点J须正；保存全曲线，不删点，double最佳相对误差<=1e-6、理想Decimal最佳<=1e-8。2×2 h=1/8装配用例6场、倍率[1,1e-7,1e-7,1]，全局v_k=((k mod 7)-3)/8，k=0..17，按同人工门检查全向量/Jv及非对称性。

## HF4参数下的固定检查

原第四组合gamma=1e-7、h=.0625，在d=.125/.25/.375取独立半解析均匀位移；减几何lift后一次舍入w，只作表示/求值fixture，绝不作生产初值。

另用2×2 Q1域[0,1]^2，h=.5、t=1、原E/nu/alpha/Lr，倍率[1,1e-7,1e-7,1]。Lx=2^-5 xy，Ly=1/8+2^-6 xy；wx=-(1-2^-10)2^-5 xy+2^-12 x+2^-13 y；wy=-(1-2^-10)2^-6 xy-2^-12 y+2^-14 x。固定底边各ux/uy，direction底边+y，d=1/8，base为总固定值减去d*direction。v1=(2^-7 xy,-2^-8 y(1+x))；v2=(2^-8 y(1-x),2^-7 xy)。等价分解q=(2^-4 xy,-2^-5 xy)，先以Decimal逐节点确认精确和不变；HL/Hw以及总HuHu均须非零。另有单元常量L=(1/8,1/8)、w=(2^-60 x,-2^-60 y)，检查显示压缩丢小量而权威场有非零应力。

真实参数固定场的全/自由总力与材料/正则分项均用原1e-9 SF求值门；人工非平衡场不要求自由平衡。J相对范数误差<=1e-9（分母max(||HP J||,1e-12)）；Jv误差<=1e-9*max(||HP Jv||,1e-12*E*t*||v||)。v单位mm，参数无量纲，Jv单位N；不得以除h后不同量纲的量混作floor。正则力另按max(||该域HP正则力||,1e-12*E*t*max(|d|,1e-6))及正则Jv按max(||该域HP正则Jv||,1e-12*E*t*||v||)各检查1e-9；全/自由分别检查，防止总SF掩盖漏项。50/80全力/Jv原尺度差<=1e-30。

这些小检查通过后才能求原首目标。首目标及完整路径使用原全部生产/HP/参考/物理门；末态交叉与全部接受态审计要求不变。新实施规范及源快照在对应数值启动前按SHA绑定。
