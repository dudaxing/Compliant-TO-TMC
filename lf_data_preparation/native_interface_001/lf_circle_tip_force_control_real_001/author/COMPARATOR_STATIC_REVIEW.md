# L-CTIPFREAL1 比较器独立静审

2026-10-23。审阅者 `/root/fload_tests`，非比较器作者。结论：**16/16静态通过，无剩余比较器阻断**。仅源码／AST／普通来源合同核对，没有导入或运行比较器、没有读取NPZ／媒体、没有数值或F/T调用。

绑定：`D:/hfr1_001/compare_freal1.py`，19830字节，SHA256 `3efb368a09e955192d08f610ff4c3d8d3b11368a687758e36cd295600a24e042`。最终protocol尚待冻结；本审查核对root已定键 `bindings`、`runtime_base`、`source_binding_file`、`parent_result`／`reference_result`、`selected_state_index`、`loads_half_N`、`nmin_half_N`。完整启动资格仍须绑定protocol和全部包装，不由本静审替代。

|项|静态检查与依据|
|---|---|
|1 纯比较范围|只import标准库与NumPy；无HF／kernel／solver导入，无F/T/HP、模型、旧force/tangent字段或媒体读取路径。源码AST通过。|
|2 普通输入及canonical|读取protocol、被bindings恰一次绑定的source普通JSON、原reference、新force result；canonical float.hex／零规范与原data.canonical_hash相符。比较器未暗读原parent或旧模型／力归档。|
|3 来源绑定|原reference整文件SHA及canonical descriptor须匹配准备来源；新force独立schema／canonical/status/target_reached、source parent/model/task/selected身份须精确匹配完整LOW1父，索引2、原split声明及signed R不换。|
|4 原任务／模式|非clock settings逐键等于准备父，N步长独立等于protocol；mechanical/chunk256、held.50、两绝对P、unknown-q flag、E*t=20确认，无厚度再乘。|
|5 原成员与请求|body/zero集合不变，14985节点／14720单元；参考恰2原态q0/.025与同P，新结果恰2原请求且位于接受序列首尾，其余只有内部态，2≤N≤17且P严格递增，不强制q单调。|
|6 所有接受态原free门|各相关摘要有限，free rho在[0,tol]，SF至少原floor，原floor必须按.50与E*t=20定义匹配；未把g混进大R主导的free范数。|
|7 新g门独立|SP=max(abs(P),abs(P0),Ffloor)，绝对g界tol*SP、abs(g)与相对rho均检查；不能改按ΔP或用global代替。|
|8 原mean／几何门|每接受态原补偿mean bound、正minJ、rigid/zero≤8e−11、global≤1e−6及正global scale均核；全字段有限与全J正由API原接受前执行，比对器不谎称重新扫描科学场。|
|9 元数据与账本|checks/depth范围受原设置；显式P只列一次，禁止body_x_drive，guide/background计一次；分量和互斥账本只描述重组差，不暗加L1阈值或压力门。|
|10 恰4档8字段|AST恰4处state_arrays调用：旧probe q0/.025、新force anchor/P1；只准lift/fluctuation，每档一次read_bytes，SHA通过后np.load同一BytesIO原缓冲，不先hash一个文件又解码另一个版本。成功总4/8硬核。|
|11 字段完整身份|archive只含两字段；每个dtype float64、shape29970、有限、metadata及字段SHA均核。路径限制于相应result树，allow_pickle=False。|
|12 state hash实现|独立重建state schema prefix＋little-endian int64 ndof＋两个little-endian binary64数组，与已安装native_force._state_hash和split_prescribed.state_hash一致，不只比较显示位移。|
|13 fresh硬身份|新／旧q0两split字节相同、state hash同父声明、R用struct.pack逐位比较同原父，q0=0且check1；不借终点工程界修复锚点。父payload已由唯一API准入读取，比较不增第5档。|
|14 P1全场/q/R门|29970个DOF逐项math.fsum四原split项，再取max绝对差，记录最大DOF与有符号差；q／全场各≤1e−6 mm，R≤max(1e−10N,1e−7abs(Rref))，分别保存PASS，未使用positions／rounded display或插值参考。|
|15 缓存／viewer合同|solver_invocations=1，save F/T及HP0；接受数至少对应完成T/F。reference_steps/new_requested_steps/cross_errors保存原值及预期viewer键，component重组明示additional gate=false，无新资格。|
|16 首错／失败保存|require首失败即抛出，单次except保存真实部分报告并返回1；缺态cross_errors为空而非零误差。数值API成功而工程门失败保原force success并令comparison failed，不改force result。原输出若存在直接拒绝，不重试、重平衡、重画或覆盖。|

原实现源码仅作只读对照：`data.py` canonical规则、`native_guided_force.py`实际result/source/ledger字段、`native_probe.py`原参考字段、`native_force.py`／`split_prescribed.py`state hash。当前静审没有解码这些模块的任何运行缓存。

比较60秒与进程／8GiB或总体64GiB上限由未来冻结SUP2包装约束，比较器不自行创建窗口或增加CPU求解。完整执行还须科学成功、比较实际PASS、显示与root检查、原窗口清理／一次封存；本记录不是这些阶段已完成的证据。
