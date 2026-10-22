# L-CTIPPROBE1：首个真实导向工件位移探针

2026-10-22（Asia/Seoul）；**待授权实施与执行**。本次准备仅读取普通JSON、源码及Git状态，三个NPZ只stat；未导入HF、构模、解码NPZ、运行新F/T／HP／平衡／测试或打开媒体。正式main保持`18f3589d406861bde9a34176567b59e23844a39a`且干净，与fetch后的origin/main无差异。本卡及准备证据位于正式仓库外，未提交／推送。

## 整体目标、当前缺口及本卡边界

整体目标是HF独立读取LF普通几何，计算一致大变形／TMC响应，向外部研究层提供可比较结果；不做LF优化，不调用dmftd，不实现MPM。L-CTIPMOVE1已经实现输入保持与工件+x运动解耦，并通过15项有限验证；其16单元／50DOF小模型不能证明真实夹持器的可动工件响应。

本卡仅把已安装的`evaluate_native_guided_probe`用于真实既有夹持器：机构平均输入保持1.06 mm，原圆形刚体仅沿+x移动，q请求为`[0,0.025] mm`。先核q0，再按原内部回溯／二分推进；不从零重做加载，不追加q目标、回程、外载、HP或小测试，不修改默认HF源码或安装入口。

这是一项有导向夹具的位移控制试算，不是指定外载的自由工件承载认证。机构输入各节点仍能依原平均约束变形；不能把保持均值改成逐节点夹紧。body全部ux=q、uy=0、转角0，工件成员保持原510单元／565节点，不移动重mask、不改变原solid／medium材料归属。

## 已核来源及尚未执行的准入

来源根（相对正式仓库）：
`lf_data_preparation/native_interface_001/lf_circle_tip_alpha_001/run_001/wave_circle_tip_alpha1/`

选`result.json`完整load_only成功路径的末峰accepted12／original12／global12、d=1.06 mm，不采用后续卸载suffix。

|已读普通文件|实际SHA256|
|---|---|
|result.json|9e083bb057de9ea9b2b52694b3cc474a877ecbfcc3785d26fa50f55566e320ec|
|model/model.json|7f56cf78700c85145cce33a5972f73ac48e05923f16c27e69f7f118e6d239e0b|
|model/source_geometry/geometry.json|9630f76972ffecbd60fa42eefb44da0c97c395db7baacaaede33cdabbbc9cf6a|
|accepted/012/state.json|c06fc6d2e3400832ca967ad5bffd546feb960c818a4e388cda3af9ec5e2a00ae|

选定split身份为`e71c06973b7dc7aff7e5ee4a801b595cb3f054e907cc6e1ad52188e858500a68`，原有符号R=0.19522304147728387 N。父task SHA为`eeae1926ade1e4b64bc788b79f31a47a4030f09a4d98a03520e82732b6ffdcb7`。已核四份普通JSON的canonical身份、所选descriptor与parent嵌入对象完全一致；当前力核／切线SHA仍与parent绑定相同。新controller不同于父旧controller属于已完成的MOVE1显式功能变更，不重写父SHA。

三个既存NPZ仅核存在／尺寸，其SHA目前是**声明值，不是本轮实际读取核验**：model/model.npz 324454B；model/source_geometry/geometry.npz 1636B；accepted/012/state.npz 219724B。全部声明SHA、字段、实际普通文件SHA与当前源码身份见[SOURCE_PREPARATION.json](SOURCE_PREPARATION.json)。

获批后执行树仅复制上述四JSON与三NPZ共七个API必需文件，保持相对结构及字节；不改原冻结树。这个最小运行复制树不替代完整原13态证据，旧力／切线／矩阵及其他态仍在原Git记录中。本次不读取这些旧科学载荷。新输出目录必须在复制父目录之外。

运行时原API仍须重新核三NPZ字节、重构项目并核源／材料／边界身份。旧科学解码仅限geometry.npz的solid/design/passive_solid/passive_void四字段与选定state.npz的lift/fluctuation两字段；model.npz只作字节哈希，不解码缓存。**准备静查通过不等于运行准入通过。** q0迁移原split两数组及有符号R，必须一次fresh F/T直接通过原门，身份不变、Newton checks=1；不投影、不Newton修复、不回放旧加载、不继承旧HP资格。

## 物理、几何和离散约束

α=2.5e−7、γ=1e−6、r9 mm、圆心(80,40) mm、right92 mm、Lr80 mm、E1 MPa、ν.3、plane strain、厚度20 mm、h=.5 mm；其余task和原设置保持。继承`mechanical / chunk256 / port_projection`，不能换为小模型使用过的full／tangent选项。新q0与非零q实际验证这一真实模式组合。

14720单元／14985节点／29970DOF；1288个处方DOF、28682个free，单输入增广系统28683阶。body1130DOF与zero195DOF的37个交集均为body-uy／background，合并计一次；body不与input／output重叠。

本轮用普通model成员ID／grid逐项对照旧固定工件nodal.json的565个坐标，核得参考bbox x=[71,89]、y=[31,40] mm。参考右余量3 mm；q=.025后的名义余量2.975 mm仅为相对**未变形x=92**的范围算术，不是变形后介质距离或允许行程资格。右界81节点无固定ux，仅node14984的uy固定，不画成夹紧墙。

观察成员固定：原body cells/nodes、原tip node11260、原非工件介质集合。右介质采用原参考列178–183、80行共480格，不按变形x重选。准备期未解码solid，执行后由新result的solid／原成员核480格的medium身份。实际右界位置、右介质J／Hu和边界距离必须用本次新接受态；不得用固定旧body坐标或参考余量替代。

## 实施、冻结及唯一执行顺序

1. 获批后仅编写研究层薄runner／pure viewer／启动包装和观察定义，目标运行树`D:/hpr1_001`（准备时不存在）；原HF生产源码、内核、切线、SUP2和旧证据保持。当前本卡并不声称候选已经写好。候选连同API全部依赖、七文件来源和协议冻结，有限独立源码静审通过后方可启动。若静审发现须改变本卡物理、门、资源或范围，停止并报告，不能默改卡执行。
2. 单次调用`evaluate_native_guided_probe(copied_parent_result,12,[0.0,0.025],new_output,time_limit_seconds=3600)`；不调用evaluate_native/resume重做父路径，不hook或替换核。on_accept仅记紧凑进度、时间和本次已给标量，不重新F/T或保存额外大对象。新API保存的接受态缓存是唯一新科学输出。
3. 原minimum_increment=.00625 mm、max_bisections4及浮点判断保持。.025最多拆成四个.00625子步，接受态N≤5（含q0）；若更小半步不足原限则按原规则停。保全部实际接受态、失败尝试、回溯和计数，不只保请求端点。内部二分不等于外部修复重跑。
4. 所有数值目标成功后，在独立纯显示进程中一次读取新result普通JSON、新观察定义及每接受态fields.npz的`J,Hu`两字段；最多5个新NPZ／10字段。不读新state/F/force数组或任何旧科学数组，不导入HF求解模块。新实际positions、body成员、全模型reference coordinates/connectivity/solid来自新result；body cells来自已绑定原普通model元数据。旧fixed-body viewer及旧convergence入口不直接调用。
5. 一次生成下述3PNG／实际N帧GIF、JSON状态／反力／收敛记录与人工页。root对每张新PNG最多一次像素检查；未通过则保存事实并停止，无重绘／重渲染。旧媒体不重开，只可stat并链接。
6. 原窗口内封存实际字节／计数与SUP2清理证据，更新阶段记录及当前入口，普通main提交／推送并做同机异目录恢复核对。代码／父source／新缓存身份与执行字节绑定，不更改旧失败、参考或资格。交付检查只做必要字节和链接核对，不另起科学复算。

## 数值门、力口径及图像

原门全部保持：relative free residual≤1e−9；平均输入误差≤1e−10×max(1.06,1e−6) mm；J>0且有限；原Armijo／回溯、25 checks／12 backtracks／4 bisections／minimum_increment=.00625。原global balance≤1e−6、body逐节点ux−q及uy／zero支撑误差≤8e−11 mm由已安装API保持，新包装逐态读取核明；不增加新的压力或承载通过阈值。

Q_drive_half=Σ_B f_int,x=−F_on_body,x。保有符号q0预载和Q(q)−Q(0)，不取绝对值或强制起点归零；R_input单列。total/material/Hu的ON-body分量保持原定义，不把总反力称纯压力／摩擦；body-x drive、body-y guide、其余zero支撑互斥，37个重叠不重复算。力已经含20 mm厚度，为半模型N；显式全装配轴向换算才乘2，q不倍增。负Q代表需要制动，不代表有正抗拔容量。

三张PNG及人工页最小内容：

- q0／末态全域与尖端实际×1几何、移动的阶梯工件、原tip11260及实际最近边界、参考轮廓与运动／输入／作用力口径。若引用理想圆，中心随q移动，明确它不替代阶梯边界；不把缩放箭头当真实变形。
- 有符号Q总／material／Hu、单独ON-body Fy及机构R面板；q／input mean保持、全部Newton检查与原门。横轴用body q／stage_parameter；history.d是q，linear diagnostics.target_displacement是恒定input hold，不能误画成新input行程。求和尾差仅描述，不另加门。
- 右参考480介质格的q0／末态实际网格、J／Hu场、全介质极值及定位、实际右边界和距离；保小J，不用裁色掩盖；图示范围、颜色及局部放大清楚。逐态JSON记录q、两种反力、三力、互斥账本、约束误差、minJ／max|Hu|与右介质摘要、接受／拒绝／时间和计数。GIF只含本次N个真实接受态，不借用旧固定动画冒充运动。

边界距离／交叠属于纯几何观察，必须基于实际positions及同一reference边界拓扑。若复用纯几何helper，静审确认没有fixed-body零位移假设或科学核导入；否则在研究viewer中最小实现，不能调用旧固定工件nodal力入口重算。描述接近、相交或间距，不以单个距离授接触、释放或有效夹持资格。

## 资源、停止和失败记录

一次连续：controller3600秒／显示共享600秒／helper4500秒／outer4560秒，最多76分钟；采样64GiB、OMP/MKL/OPENBLAS/NUMEXPR各16线程；viewer维持8GiB子限。沿用原SUP2同实例终止／全部成员覆盖／句柄释放合同；各层时钟含约定清理，不用裸PID消失或force覆盖。来源字节、构模、q0、非零q、写入及封存均受helper总钟约束；API自身controller钟在admission／构模之后开始，不能把此前时间忽略于总预算。

预算依据是已有普通记录：同α峰值首次卸载fresh anchor约71.20秒／1F+1T；1.05→1.06输入步约532.62秒／12F+6T；原构模约.14秒。新body-q方向／port_projection模式的成本未知，且原minJ约4.66e−4、可能四子步，所以给独立60分钟controller；600秒显示和300秒来源／封存／清理余量形成helper4500。它不是成功保证，也不是原窗口剩余额度。本机资源建议来自用户已授权64GiB／16线程；本卡不用GPU，不升级依赖或修改严格选项。

唯一启动，首个终端错误／资源门停止后续科学／显示，无外部重试、修复重跑、延期、force、新测试、HP、默认代码修改、回滚或删除。允许原内部回溯／二分。typed失败若API已写result／partial则如实保存；若来源拒绝或超时没有result，只记录真实已有accepted文件／回调和异常，未知计数为null，不伪造成功／零次／已释放。仅原共享窗口仍开放时允许一次字节封存；窗口关闭后不补跑显示或读科学数组。

## 完成条件及下一步取舍

数值PASS仅在q0身份不变且fresh门直接通过、请求q=.025及全部内部接受态通过原门、源／字段身份和计数完整时成立。显示／清理／交付分别按实际报告，不拿其中一项替另一项。所有机械资格沿新API保持false，原峰值HP不迁移为本新路径参考。

当前没有普通元数据来源阻断；启动前置是本卡新授权、研究包装冻结和静审。运行时NPZ／重构／q0准入仍是必须证明的门。小J及新模式组合是实际试算风险，不预先改门。显示排版和更广域研究属于非阻断改进，不增加本卡计算。

完成后仅依据实际Q符号／material-Hu占比、尖端与右介质响应决定下一实验：可能匹配未夹持／低输入对照，或另定P_full／允许位移及保留判据后实现真正力控。probe q续算、自由y／转动、摩擦、释放、稳定性和域／参数独立性均留作后续，不在此卡自动开展。
