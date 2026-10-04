# 008：1.75 mm 峰值已达到，完整循环因时间限制失败

整体目标：普通LF几何下的独立HF非线性TMC正向评估，提供力、结构变形、平衡和接触相关指标，供外部研究比较。HF不优化、不导入/安装/调用dmftd或MPM；main与origin https://github.com/dudaxing/Compliant-TO-TMC.git保持。

本轮实际进展是更大行程的部分机械路径及其独立几何观测和可视化。**正式008为failed/time_limit，已闭卡：8接受态，返回零未完成，新HP参考0。** 不能称九目标成功，不能继承007资格给这些新态，不能据峰值或小TMC合力认定有效夹持。

## 为什么做、改了什么

007完整1.5mm循环有14次新HP/135364项原门；底面首次法向射线仍正(.3593983675mm)、左方向间距增大，minJ约.16868。这支持谨慎扩大行程，而不支持预定接触阈值。用户已授权对称方/圆尺寸与较大行程探索；本卡选择同一固定16mm下半方体、初始两面2mm，九目标[0,.5,1,1.5,1.75,1.5,1,.5,0]，保留新增加载和回程1.5观测，从零重新求解。

只改任务四描述键、input峰值与ordered targets、case同步目标、baseline及包装身份/前例pins。原27模型数组、方向、材料、端口/支承与007完全相同；原003 63来源+3既有live转换+008五包装=68。执行器仅docstring改动，launcher/privateCore原字节，auditor数学、计数、门、settings和限制原样。实际准备53输入、126准备pins、199科学pins均核验；完整差异和静审见本目录authoring及[交叉/失败/可视化回执](../../../handoff/native_workpiece_cycle008_20261004/closed_008_identity.json)。

h1mm、3200 cells、3321 nodes、6642 DOFs，376 fixed/6266 free；半方体[62,78]×[32,40]mm，128 cells/153 nodes/306 bodyDOFs。E1MPa、nu.3、plane strain、厚20mm、gamma=alpha=1e-6、Lr80mm、输出/辅助弹簧0；平均输入+x、自由输出+y。机械模式schema1.2/16 force/3 T、非对称CSC，辅助材料能量not_evaluated/qualified:false/field_present:false，默认complete不改。

## 实际停止与原因

生产原预算helper600/outer660秒、8GiB采样树RSS，不延长、不重试、不force。最后0目标的Newton/线搜索仍进行中时，controller返回time_limit；最后trial的Armijo accepted只表示线搜索接受，未成为Newton验收的路径态。35条已记Newton base、27个full-step trial；36次切线均完成，额外最后base在组装后时间门退出。不能从未接受trial推断回零完成。

八态和全部缓存成功写包：63/63F、36/36T、1solve，0saveF/T、0HP/JIT/LF。无F/T算术范围捕获、无已记录拒绝/二分，hooks恢复；原27数组逐字段同，199pins/68live+caps/53inputs前后同。helper=615.8091694000秒、peak_wset=930238464bytes，outer616.8831691秒。600秒是协同检查阈值，调用可能在下一个检查前完成，非OS硬截止；超时不当合格。wrapper末检查另记Final resource or source/input binding check failed，原failure.code=time_limit和sources/inputs_unchanged:true同时保留。

参考240/300秒未启动、HP0；原卡关闭，未用参考额度不转换成重试许可。没有新的参考pass、力/Jv/平衡/应力/能量资格；生产原flags全部保持false。

预算预估是本轮暴露的问题：007生产456.97秒，但九态新峰与回程两个.25mm段各约82秒，已超过原窗口裕量；回零步骤本身需多次切线。静审曾明确预算不保证成功。本次不是证实本构错误，也不是证明本构正确；首先得到真实成本与受限保存态证据，不为制造通过而改时间、门或旧结果。

## 可检查的实际效果

| index | leg | input mm | R N | output mm | minJ | bottom ray mm | left ray mm |
|---:|---|---:|---:|---:|---:|---:|---:|
| 0 | origin | 0 | 0 | 0 | 1 | 2 | 2 |
| 1 | loading | 0.5 | 0.106253248 | 0.5757557123 | 0.7357647741 | 1.472453754 | 2.206013205 |
| 2 | loading | 1 | 0.2168139969 | 1.159355056 | 0.4581891642 | 0.9257445243 | 2.439649632 |
| 3 | loading | 1.5 | 0.3331784932 | 1.747632769 | 0.1686782188 | 0.3593983675 | 2.698810359 |
| 4 | loading | 1.75 | 0.3969477464 | 2.034686944 | 0.0280804397 | 0.07671066679 | 2.832775429 |
| 5 | unloading | 1.5 | 0.3331784932 | 1.747632769 | 0.1686782188 | 0.3593983675 | 2.698810359 |
| 6 | unloading | 1 | 0.2168139969 | 1.159355056 | 0.4581891642 | 0.9257445243 | 2.439649632 |
| 7 | unloading | 0.5 | 0.106253248 | 0.5757557123 | 0.7357647741 | 1.472453754 | 2.206013205 |

峰4的下半体总(Fx,Fy)=(-.0007910899872955321,+.0037892857813192618)N；材料(-.0003137551201961619,+.0023430611778208557)、Hu(-.00047733486709937006,+.0014462246034984065)。保持反力为相反号；镜像上半(Fx,-Fy)、完整镜像净(2Fx,0)，2|Fy|=.007578571562638524N是标量和，不是完整净力、压力或已证夹持力。反力与输出在已回到的1.5/1/.5点接近加载对应值，零终点缺失。

峰minJ=0.028080439695515848，实体最小J=.9562359128632606；强压缩发生在第三介质。峰maxHu=.4698093969993863/mm为缓存生产观测，未新HP核验。底面首次法向射线=0.076710666789909024mm、左面=2.8327754289207783mm，底面接近而有限左面继续远离。几何有效且8态无raw/strict内部重叠、无roundoff模糊；完整包含、自重叠仍不证明。八态跨域AABB候选均0，故实际SAT pair观察为0；不将解析SAT测试说成实际重叠对运行。41个保存最小命中见证点直接核验，最大ray向量残差3.10863e-15mm≤原tol；初态有连续并列最小，16个各面closest只是代表。闭边508/48含数学cut，物理边496/32排除cut。

首错后独立建立四张**保存partial专用**卡：unsigned和机械图各120/120秒8GiB，region测量和图各120/150秒8GiB，各一次终态pass；闭机械卡不改、不重跑、不追加参考。unsigned8次、region8次各独立新保存几何调用，绘图几何0；0新F/T/solver/HP/consumer依据纯来源/import与限定调用路径，不是机械hooks监测。旧39项解析测试来源原SHA复用，0重测；只授予保存几何有效性/测量与文件身份，不授HF资格。

[实际×1结构、另列×4显示、N力/mm位移/minJ、材料/Hu工件力、Newton/试探与最后态图](../../../functional_views/native_workpiece_cycle008_20261004/partial_saved_001/render_001/cycle008_saved_path.png)

[实际×1峰/最后态、两面放大、全部8态三种距离及缺零端点图](../../../functional_views/native_workpiece_cycle008_20261004/partial_region_view_001/render_001/native_region_path.png)

图的箭头分别注明机械力与非力几何射线；unsigned最近角点、有限面法向射线、node-window代理分别标名，不混作signed penetration。数学对称cut参与闭区域分类，不是物理接触面。最后接受index7/.5mm标LAST SAVED/REQUESTED RETURN NOT REACHED，不补第9个零点。根与独立读者均实际view_image；图、CSV和源身份见交付回执。公共N比例下工件箭头很小，数值分量曲线保持可读；单元均值位移色条最大2.713590473mm不等于最大节点模2.772376810mm。独立只读QC首稿误读旧unsigned edge_count键，KeyError时尚无输出；按实际mechanism_edges/workpiece_edges数组更正读取后通过，不是新几何调用或正式阶段重试，原审阅过程见回执。

## 资源与阶段身份

| 阶段 | 终态/exit | 实际outer秒 | 树RSS bytes | pins |
|---|---|---:|---:|---:|
| coarse_square_cycle_008/prepare | pass/0 | 0.385180300 | 26697728 | 126 |
| coarse_square_cycle_008/production | not_pass/1 | 616.883169100 | 864419840 | 199 |
| partial_boundary_saved_001/measure | pass/0 | 1.047966100 | 45867008 | 184 |
| partial_saved_001/render | pass/0 | 3.414011500 | 182800384 | 193 |
| partial_region_saved_001/measure | pass/0 | 1.361131800 | 44400640 | 68 |
| partial_region_view_001/render | pass/0 | 2.590391800 | 112877568 | 82 |

各纯保存阶段helper成本、峰RSS、测量/输出SHA与完整原始bindings在对应measurement_receipt/JSON/view_metadata/launch中；原生产helper和outer分别记录，不能互换。作者源/静审与实际执行分开；旧完整路径可视化候选仅作者静态、未安装执行，本轮partial候选按新实际失败证据独立冻结。

保存的path_diagnostics.timing_seconds中，kernel_and_transfer=610.3092743000598秒、sparse_solve=1.01597790006781秒、total=611.7638349000481秒；前者是内核及数据传递，不能称纯内核耗时。这说明目前主要成本集中在反复机械评估与切线求值，减少一次采样有实际成本依据，直接改LU或增加防御包装不会解决本轮时间限制。

## 功能进度与下一步

已实现：独立普通几何适配、固定对称工件覆盖、NumPy机械力/材料与Hu分量、完整组装/非对称切线、平均位移增广平衡、连续加载卸载与缓存、明确失败/部分状态、独立闭区域与有限面射线以及真实可视化。007的完整1.5mm循环仍是先前受限fresh参考证据；本轮1.75mm只生产partial/保存几何证据。

未完成：本新峰的完整回零与freshHP、有效夹持/接触压力/自由体、一般支持域/能量/应力HP/全列T、圆及细任务求解、H2/H3/HF5/完整AD/JIT与最终比较标签。几何无重叠和正射线不能替代这些功能或资格；h1mm层内J很小也提醒不要直接把当前粗网格观察外推其他工况。

下一近期阶段先做实际调用成本规划，再冻结独立1.75mm完整循环任务。候选为[0,.5,1,1.5,1.75,1,.5,0]，显式减少一次回程采样点，保留原600/660、240/300、8GiB与所有数学门；1.75→1新的.75mm步可能增加Newton/二分，成本只是估计，不保证成功。此为另一物理采样任务，不能使旧九目标008变pass，也不能拼接旧部分资格。每个新实际接受态仍需各freshHP80/120，包括二分；完整回零及参考通过后才考虑增大行程或圆/细任务。本轮未创建或执行009；不追加当前已关闭卡。

恢复时以真实Git根运行；先核main/origin/HEAD/manifest和对应报告，不以历史绝对Pythonargv作新机器命令。原闭卡不可重放，保存图/几何输出可直接读。handoff/authoring保留迁移作者源码（其中完整路径候选只静态，未安装运行）；这些生成器不是可直接覆盖闭卡的便捷命令，部分含本机作者路径，后续新卡应在真实根更新明确身份。公开恢复另存网络fetch/fast-forward与manifest文件身份回执，fileidentity不等于数值复算。
