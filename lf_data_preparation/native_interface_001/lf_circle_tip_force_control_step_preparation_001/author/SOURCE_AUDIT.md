# L-CTIPFSTEPPREP1：正式非零q父态与续载接口来源核查

**2026-10-24：16项普通来源／源码核对通过；只完成准备，尚未完成实际科学payload准入或新fresh平衡。** 当前main基线`6c333a825e0c6b90be5b32b38bfe0a7677378384`。本子任务没有科学数组字节读取/hash/解码、HF导入、F/T/HP/平衡、测试、绘图或生产修改。

## 采用的直接父态

- 直接力控父：`D:/hfh1_001/run_001/force/result.json`；已完成的`hf-native-guided-force-1.0`、success、target_reached=true、failure=null，两个原目标均已到达。
- 自动选择其最后接受态：accepted1／global original1，P1=`0.0002561572865437846`半模型N，**绝对q=`0.025000000126731543` mm**，有符号机构R=`0.19536542042269825` N。旧末行fresh=false是原运行事实；下一段新首态应fresh=true且checks1。
- 原state SHA：`352103915d1f03e02da4b49de5426ddb3daf9438f0e7d25ed37c9876aaa0984c`；直接读取目标为`accepted/001/state.npz`，原声明archive SHA`7e4c6d137e651801b5f8bbcb574f08fb633ff56d320611c69da6fcb136b88eb3`。两字段为float64[29970]，完整字段SHA及binary64 hex保存在SOURCE_AUDIT.json。
- 源总文件实际普通raw SHA：`8caad93b7f765af9b70597b4c3992b8425af2a77c74b7e7eb68fafee8fda3355`（5140126 B）；canonical descriptor`201fe963f24d5667357076f0ef1ef12a98c92b4e88e54401215543b90aee8ea8`已用标准库按float.hex规则核对。原结果、任务和资格不改。

## 原根固定模型保留为来源

`D:/hpr1_001/parent_001/result.json`仍为原固定工件13目标load_only成功末峰accepted12/original12。源所含fixed/result、model、geometry、selected012普通描述的raw/canonical/task关联均吻合；它提供几何、材料、端口和边界，但**本次不从其q0科学split起算**。真正继承的是HIGH1的非零q末态。原固定state/source pin留作历史，不重写为新的producer。

|普通文件|实际字节|实际SHA256|
|---|---:|---|
|`D:/hpr1_001/parent_001/result.json`|289415|9e083bb057de9ea9b2b52694b3cc474a877ecbfcc3785d26fa50f55566e320ec|
|`D:/hpr1_001/parent_001/model/model.json`|89774|7f56cf78700c85145cce33a5972f73ac48e05923f16c27e69f7f118e6d239e0b|
|`D:/hpr1_001/parent_001/model/source_geometry/geometry.json`|25085|9630f76972ffecbd60fa42eefb44da0c97c395db7baacaaede33cdabbbc9cf6a|
|`D:/hpr1_001/parent_001/accepted/012/state.json`|9579|c06fc6d2e3400832ca967ad5bffd546feb960c818a4e388cda3af9ec5e2a00ae|

继承α=2.5e−7、γ=1e−6、E1 MPa／ν.3／平面应变／t20 mm，r9／圆心(80,40)／right92／Lr80、h.5；14720单元／14985节点／29970DOF、510工件单元／565节点。原free28682、fixed1288、body-x释放为一个刚体q，混合系统28684。机构输入保持1.06 mm，工件uy=0／转角0，原mask与成员不重定义。

## producer历史差异与真实准入门

当前`native_guided_force.py`与`split_guided_force.py`已由FRESUME1安装，SHA与HIGH1原producer不同，是已记录的预期差异；`native_probe.py`、`split_displacement.py`及两个力核／切线核与HIGH1相同。根fixed的旧`split_displacement.py`又与当前不同，历史差异继续保留。

现有resume对fixed和直接force两producer都要求`split_numpy_tangent.py`、`split_kernel_invariants_hu.py`的SHA与当前相同，本次普通源码检查匹配。它不要求所有producer/controller SHA同当前；不能伪称六源全同，也不由此推论两个控制器所有行为等价。将来运行仍要实际执行原准入、split身份与fresh F/T门。

本次所有非clock DisplacementSettings与原fixed一致：tolerance1e−9、constraint_tolerance1e−10、scale floor1e−6 mm、force-floor-factor1e−8、max_checks25、Armijo1e−4、max_backtracks12、max_bisections4、原mm minimum_increment .00625保持。原GuidedForceSettings Nmin=`1.011074467280606e−6`半模型N；新段不得把mm限值当N步长。mechanical／chunk256继承；`parent_initial_guess=port_projection`只是原fixed历史，实际force predictor是guided_reduced_tangent。clock需要新卡独立核定。

## 现有接口及未来读取边界

`hf_eval.native_guided_force_resume.extend_native_guided_force(saved_force_result, full_extended_body_load_targets_half_N, output_directory, *, fixed_parent_result=None, time_limit_seconds=60., on_accept=None)`已安装。只允许完整旧绝对P前缀后追加严格递增目标；新段仅`[P1,P2]`，root P0不改，q不重置，lift不二次相加，R不取绝对值。新output必须位于直接力控树与解析后fixed树之外且全新。

仅clock可变；同字节fixed_parent_result可用于换目录。不能传新物理、q覆盖、非clock设置覆盖；不得把旧q=.025参考作为P2求解答案或夹限。新结果1.1格式记录global offset1／段内索引0,1和完整目标[P0,P1,P2]，full_extended_path_executed_by_child=false；旧global0不重放。

|未来NPZ角色|本次仅stat路径／字节|未来成功控制流解码|
|---|---|---|
|root_model_opaque|`D:/hpr1_001/parent_001/model/model.npz`，324454 B|无；仅opaque SHA核身份|
|geometry_four_authority_masks|`D:/hpr1_001/parent_001/model/source_geometry/geometry.npz`，1636 B|solid, design, passive_solid, passive_void|
|selected_direct_force_split|`D:/hfh1_001/run_001/force/accepted/001/state.npz`，219881 B|lift, fluctuation|

合计3不同旧NPZ路径、2档解码／6字段（四authority mask＋直接force两split）；这是源码控制流计划，不是本轮动态字段hook。所有SHA仅来自普通源声明，本轮没有打开或hash这些NPZ。实际字节/shape/dtype/field/state身份、mask重构模型和新fresh平衡留待未来授权worker核实。原fixed012 state、旧force000、旧probe、所有旧fields/force/tangent/matrix和祖先force科学数组不需要读取。

成功且无二分时新段2接受态（fresh global1与P2 global2）；内部二分态可能增加，均归global original2。数量上限应由新ΔP、原Nmin及maxdepth导出，不照搬旧17，也不硬编码2。每接受态保存新的state.npz和fields.npz；F/T缓存直接保存，不为显示新增保存时F/T。科学success和fresh身份/原门应明确分开记录，保真实partial。

## 低J、Hu、失败与二分历史不覆盖

HIGH1现末态minJ=`0.00041660852936145333`、max|Hu|=`0.3181733832407684` /mm，ON-body total Fx=`−0.0002561572865437885` N，其中Hu Fx=`−0.0001859204692040975` N（约72.58%）。它们是既有总弱力记录，不是纯接触压力、容量或误差份额。源两原目标2接受、0内部二分／0failed_attempts，8F／5T均完成。

旧给q PROBE1另有首次0→.025 invalid_J／bitwise回滚，然后内部二分接受[0,.0125,.025]，28F尝试／27完成和15T完成。其.0125是历史内部态，不能假配成未来N段内部态；原minJ与Hu记录、失败原因和计数已从既有普通comparison完整保留于机器记录。

P是原+x有符号绝对半模型外载N，已含t20 mm；ON-body Fx与Q_half/P平衡反号。完整镜像轴向载荷为2P，q不倍增。R是机构输入广义力，不等于P；body-y导向与背景重叠去重、显式P只入账一次，旧body-x处方驱动力移除。

independent_HP／effective_grasp／release／HF四flags仍false，本来源准备不升级任何科学资格。原tip11260、right480介质格／81右界节点与原fixed authority普通记录一致；本轮没有局部场读取或极值重定位。

## 结论边界

16项PASS仅说明普通源、已安装接口和拟继续使用的身份/设置声明一致，没有发现当前接口的静态来源阻断。不能把普通success、scientific stat或本审PASS写成payload内容已核、新fresh门已过或正式P2已到达；新资源窗口、P2冻结、验收和显示计划由主任务核定。
