# L-CTIPFHIGHPREP1：高输入两载荷的门与资源审计

2026-10-23；独立审计 `/root/fload_tests`。结论：**16/16 项通过，当前仅准备，L-CTIPFHIGH1 未执行**。只审普通结果、旧准备门及当前安装源码；未导入HF，未读NPZ/ZIP载荷或媒体，未测试、求解或绘图。详细源身份、逐项检查及binary64十六进制值见同名JSON。本文件可在交付时原字节改名为 `COMPARISON_GATES.md/json`，无需第二份不同口径的门。

## 任务与精确冻结值

现有API `evaluate_native_guided_force(saved_result, selected_state_index, body_load_targets_half_N, output_directory, *, force_settings, time_limit_seconds=120., on_accept=None)` 可直接复用。来源必须是完整成功 fixed-rigid/load_only 的末个原峰值；本次选高输入固定父 accepted12/original12、mean=1.06mm，原R=`0.19522304147728387 N`、原state SHA=`e71c06973b7dc7aff7e5ee4a801b595cb3f054e907cc6e1ad52188e858500a68`。不能沿用低输入的 .50mm 或 selected2。

|冻结量|binary64兼容十进制值|
|---|---:|
|P0，半模型绝对N|`0.0002399800950672949`|
|P1，半模型绝对N|`0.0002561572865437846`|
|P1−P0，N|`1.6177191476489698e-05`|
|N最小步 `(P1−P0)/16`|`1.011074467280606e-06`|
|终点R参考，N|`0.19536542042187396`|
|终点R允许差，N|`1.9536542042187397e-08`|

P取原给q参考 `Q_drive_half_N=−F_ON_body,x`，为固定+x的有符号绝对合外载，已含20mm厚度；全装配是2P，q不倍增。不给增量冒充P，不输入q=.025，不从probe末态热启动、不夹限q。未知为同一刚体body-x位移q及机构均值乘子R；body-y=0、转角0。`g=fsum(body internal x)−P`，求和而非节点平均。body-x处方支撑从账本移除，显式(P,0)只计一次，body-y/background交叠只计一次。

首P0必须新鲜F/T检查1直接接受原split与有符号R的逐位身份，同时过free/mean/g门；不能通过预测、投影或Newton修复预载。当前代码支持这一合同，且保持mechanical/chunk256；父初猜元数据为port_projection，新力控实际预测器为guided_reduced_tangent。alpha2.5e−7、gamma1e−6、r9/圆心(80,40)/right92/Lr80、E1/nu.3/plane strain/t20/h.5及14720格/29970DOF、原掩码和端口保持。

## 每态原门及工程比较

原非clock设置为：tolerance1e−9、constraint_tolerance1e−10、displacement floor1e−6mm、force floor factor1e−8、25检查、Armijo1e−4、12回溯、4层二分；旧最小步 `.00625 mm`只保来源，不能作N步长。独立N步为上述ΔP/16，原maxdepth4最多16个成功子增量，加锚点最多17实际态；唯一外部API调用。

每个原/内部接受态均过free rho≤1e−9、g rho≤1e−9、补偿mean门、相关字段有限且全部J>0、rigid/zero≤8e−11mm、global≤1e−6。`SF=max(||fint_free||,||actuator_free||,||spring_free||,Ffloor)`；高输入dscale=1.06，`Ffloor=1e−8*20*1.06=2.12e−7 N`，**mean门为 `1.0600000000000001e-10 mm`**，不是低输入5e−11。`SP=max(|P|,|P0|,Ffloor)`；本次两原目标SP为P0/P1，g绝对门分别 `2.3998009506729493e-13` / `2.561572865437846e-13 N`。Armijo使用本base固定SF/SP，merit=`.5*(||r_free/SF||²+(g/SP)²)`。

终点事先声明工程功能回归：`|q_new−.025|≤1e−6mm`；全部29970DOF逐项 `fsum([lift_new,w_new,−lift_ref,−w_ref])` 的最大绝对差≤1e−6mm；`|R_new−R_ref|≤max(1e−10,1e−7|R_ref|)=1.9536542042187397e-08 N`。不用舍入后的位置/显示位移差；不从低输入极小误差反推更紧门。这是工程回归界，不是严格离散/非线性误差界，q和全场重叠也非独立物理证据。若平衡成功而回归失败，保API数值success、试验工程NOT_PASS，不能修值、静默改门或把不完整比较记成零误差。

## 高输入旧困难与配对边界

原PROBE1实际3态q=`[0,.0125,.025]`，minimum_J依次 `[0.00046587891715793817, 0.00043961981824698745, 0.0004166085295994876]`。直接0→.025曾invalid_J、逐位回滚，后由原内部二分接受.0125/.025；28F/27完成、15T/15完成的历史保留。未来比较**旧接受索引[0,2]**，对应原目标索引[0,1]；接受1是original1/depth1的内部点，不能按“旧恰好两态”断言，也不能变成第三个新P请求。新N二分中间态不得与旧q=.0125自动配对或插值。小而正的J提示路径困难，不预授新力控失败、成功或稳定性。

## 有限读取和显示

未来成功API来源读取集为3个不同旧NPZ路径：model仅原字节hash，源几何4个掩码，固定父split的lift/fluctuation2字段，合计6解码字段；此为源码控制流推定，**不是动态字段钩子或OS open次数**。比较器最多4个state NPZ/8字段：旧参考接受0/2、新force锚点/最后原P1，各只lift/fluctuation，原字节hash后再decode。同一新/旧场必须验证29970float64及声明身份。合计最多7个不同NPZ路径、14字段，model载荷不解码；不读旧force/tangent/HP或媒体。本准备实际科学载荷读取0。

仅新API成功且完整比较通过后，viewer从冻结普通JSON一次生成5PNG和全部实际N≤17态GIF；实际几何×1，动画不插值、不伪装物理时间。5类显示为变形、P–q/误差、总/material/Hu与R账本、尖端/右介质几何及global J/Hu趋势、双rho与mean/global/rigid收敛。无局部fields读取就不能画局部场。每新PNG最多一次root像素检查；旧媒体只链接，不重开。

## 后续候选资源，尚未执行

|层/用途|活进程上限与清理|嵌套总窗/s|
|---|---|---:|
|API/controller|3600；含在科学worker活进程内|3600|
|科学worker|3885活进程（导入/来源核验/构模/控制器/保存）+15同实例清理|3900|
|比较器|45活进程+15同实例清理|60|
|显示+全部root QA共享|viewer活进程510+清理15；全部QA相对显示起点≤585；末15保清理/receipt|600|
|helper其余|启动/普通核验/receipt/其余清理与唯一原字节封存|240|
|helper总计|3900+60+600+240|4800|
|outer|helper4800+末清理60|4860|

科学活窗比controller多285s，供导入、来源admission及返回保存等共同使用；不是允许controller延期。显示最坏viewer+清理到525s后，root检查需在585s前完成。全部阶段不可借用已闭卡窗口，也不可突破共享总窗。采样64GiB，四库线程上限16，viewer原8GiB，不启GPU。算术余量明确，但高输入非线性耗时尚未证明；低输入运行时间不能保证本次完成。

首个终端错误立即停止后续科学/比较/显示，保真实partial及原内部失败；只许原内部Armijo/N二分，无外部重试、修复重跑、延期、force、给q回退、物理/门调整、新测试、HP、默认源码安装或回滚。仅同实例清理已证明且原窗口仍开放时允许一次原字节封存。后续薄包装/冻结/静审及执行需新卡授权；当前并未启动。

本任务即便未来通过也只支持此两载荷局部导向总力平衡，不授压力、纯接触抽拔力、承载极限、有效夹持、释放、唯一性、稳定性或HF5资格。
