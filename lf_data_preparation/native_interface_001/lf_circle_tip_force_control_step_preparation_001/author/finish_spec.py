# Write candidate human specs from ordinary preparation metadata only.
from copy import deepcopy
import json
from pathlib import Path
A=Path(__file__).resolve().parent
R=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
S=json.loads((A/'SOURCE_BINDING.json').read_bytes())
C=json.loads((A/'CONTRACT.json').read_bytes())
L=C['loads'];P0,P1,P2=L['full_targets_half_N'];x=S['selected_force_state']
def write(name,value):
    text=json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n' if isinstance(value,dict) else value.strip()+'\n'
    (A/name).write_bytes(text.encode('utf-8'))
old_path=R/'lf_data_preparation/native_interface_001/lf_circle_tip_force_control_high_001/observer_binding.json'
obs=deepcopy(json.loads(old_path.read_bytes()))
obs.update(stage='L-CTIPFSTEP1',status='prepared_original_membership_not_new_solution',
    original_observer_identity=S['ordinary_sources'][6],immediate_force_parent_identity=S['ordinary_sources'][0],
    planned_segment_targets_half_N=[P1,P2],
    note='Historical observation source_path/source_parent_result retained;new direct force parent separately pinned;no moving remask.',
    future_phase_check='Verify original body/right-medium IDs against new result.model before drawing',local_J_Hu_field_reads_planned=False)
write('observer_binding.json',obs)
write('SOURCE_BINDING.md',f'''
# 来源核定与读取边界

2026-10-24，基线`{S['baseline']}`。[完整绑定](SOURCE_BINDING.json)、[独立来源审阅](author/SOURCE_AUDIT.md)。本轮仅核8份普通描述/记录、58份生产源码原字节和3科学档stat，未读/hash/解码NPZ内容。路径数是绑定范围，不是动态open事件数。

|普通来源|原字节SHA256|
|---|---|
|HIGH1 force/result|`{S['ordinary_sources'][0]['sha256']}`|
|原fixed result|`{S['ordinary_sources'][1]['sha256']}`|
|原model描述|`{S['ordinary_sources'][2]['sha256']}`|
|原geometry描述|`{S['ordinary_sources'][3]['sha256']}`|

直接父`D:/hfh1_001/run_001/force/result.json`为success/target_reached，schema1.0、accepted1/original1。P1={P1!r} N，绝对q={x['body_q_mm']!r} mm，signed R={x['R_input_N']!r} N。state SHA=`{x['state_sha256']}`，state.npz声明SHA=`{x['state']['sha256']}`，lift/fluctuation均float64[29970]；当前只stat，未作新payload准入。

根fixed仍是`D:/hpr1_001/parent_001/result.json`完整13目标load_only末峰accepted12/original12，提供原模型/物理。新起点取直接force父非零q末态，不能解码fixed012/q0后重放原两载荷。

当前native_guided_force/split_guided_force与HIGH1 producer不同，是FRESUME1安装后的预期历史；native_probe/split_displacement及两kernel与HIGH1相同。根fixed原split_displacement更早版本也保留原SHA。续载只按当前API核两力/切线kernel及完整源/模型身份，不要求六producer全部等于当前、不改旧SHA；实际fresh仍待下一次求解窗口首检。

未来API仅3旧NPZ路径：fixed model仅opaque整档hash；geometry原四mask；直接force accepted001两个split。共2解码档/6字段，字段数按冻结源码控制流，未来文件open事件另实测。新保存NPZ的raw回读/hash另计。普通核对和viewer不读科学档，不读旧fixed012/probe/fields/force/tangent/matrix、旧ZIP或媒体。

observer_binding保原body565节点/510格、tip11260、右480格等ID和历史观察来源，另添直接force父pin；未来须核新result.model的原成员/相位，不移动重mask。当前没有新真实变形或场极值定位。

本机用既存原树，不复制/解压科学包。跨机按[HIGH1恢复说明](../lf_circle_tip_force_control_high_001/RECOVERY.md)及原fixed/PROBE1依赖恢复，同字节新位置需显式核定；stat可用不等于payload或fresh通过。
''')
write('PREPARATION.md',f'''
# L-CTIPFSTEPPREP1：正式r9非零q小载荷续载准备

2026-10-24。**准备完成，正式续载尚未执行。** 本轮只核父态/载荷/尺度/门/预算并作控制示意；无HF导入、构模、F/T、平衡、HP、测试或科学NPZ/旧媒体解码，58生产源码保持。图是任务示意，不是新有限元结果。

## 整体目标、已做什么及本轮作用

整体目标是独立HF从LF设计分析TMC大变形夹持器的实际变形、输入反力、工件作用和加载/卸载，逐步支持设计比较、优化及承载研究。已有多设计/圆矩工件、完整输入回程、选定态参考、α对照、给q探针、正式低/高输入两载荷力控交叉；[FRESUME1](../lf_circle_tip_force_control_resume_001/RESULTS.md)最近又通过12项小模型验证并安装非零q保存态续载入口。

当前缺的实际证据是正式r9已移动的force末态能否继续承受一个小载荷增量。本轮将问题缩成一个新目标，避免重复固定父加载，使后续决策依据实际J/Hu、反力和收敛。不预定q2，不开展容量扫描，也不让小模型通过代替正式试算。准备的效果是明确可执行来源、控制量、原门和有限预算；新平衡是否成功仍待求解。

## 控制/状态关系示意

![控制示意，非实际结构或新有限元变形](control_schematic.png)

[SVG](control_schematic.svg)和渲染/QA记录保留。已完成HIGH1与未执行新段明确分开；root P0与segment P1不混用，q1绝对继承、q2未知。P是含20mm厚度的半模型合外载，完整镜像轴向2P、q不加倍。

## 核定源及小增量

|项|核定值|
|---|---|
|直接父|`D:/hfh1_001/run_001/force/result.json`，success，accepted1/original1|
|末态|绝对q={x['body_q_mm']!r} mm；signed R={x['R_input_N']!r} N；原split/state身份继承|
|根P0|{P0!r} N，保持原根任务值|
|段首P1|{P1!r} N，新fresh起点，不归零q|
|新P2|**{P2!r} N**，源binary64一次算`P1+(P1-P0)/4`|
|新增量|{L['new_increment_half_N']!r} N，约4倍原Nmin|
|完整/新段|full=[P0,P1,P2]；只执行[P1,P2]，global原索引1/2|

保持mean1.06 mm、α2.5e−7/γ1e−6、r9/(80,40) mm、right92/Lr80 mm、E1 MPa/ν.3/plane strain/t20/h.5、14720单元/29970DOF、510工件格/565节点及原端口/支撑/导向。工件仅原+x刚体q未知，uy=0、转角0，不重mask；mechanical/chunk256/guided_reduced_tangent保持。[完整来源](SOURCE_BINDING.md)。

P为绝对有符号半模型N，非ΔP/每节点载荷。`Q=Σbody f_int,x`，`g=Q-P`，ON-body Fx=−Q；R是保持mean的独立乘子。显式P入账一次，移除旧body-x处方驱动力，body-y导向/背景重叠去重。不将节点或Hu弱力称压力/纯接触抗拔力。

## 原尺度、二分和成功条件

SP=max(|P|,|root P0|,2.12e−7 N)。此正增段P≥P1>P0，实际SP=P；根P0仍要精确核元数据/来源，但本例SP不能独证根/段尺度正确，根主导数值检查保留FRESUME1负载小模型证据。

Nmin={L['minimum_force_increment_half_N']!r} N，原max_bisections4/max_checks25/Armijo/回溯及全部非clock设置保持。实际Δ/Nmin={L['new_increment_over_Nmin']!r}，不是浮点精确4；原Nmin×(1−1e−12)截止允许两级二分，下一半步不足。最多fresh+4叶=5接受态是派生上界，不改maxdepth或强裁结果。旧minimum_increment=.00625 mm另保，不能当N步长。

所有接受态含内部点保原ρF/ρP≤1e−9、mean原公式界1.0600000000000001e−10 mm、J全正有限/原F-Hu有限性、global≤1e−6、rigid/zero≤8e−11 mm。P2 body残差界{P2*1e-9!r} N；free尺度仍独立按原公式。

fresh须checks1，q/P/R bits、split字段SHA/state身份原样保持，不预测/投影/Newton修复。实际末原目标P2达到后报告真实q2/R2/三力/账本。P2没有给q/HP参考，旧P1工程比较只历史，不沿用其误差界、不填零误差、不以q=.025或预期斜率作为fallback。数值success、目标达到、普通继承核对和显示完成分开报告。

## 低J、Hu与内部二分历史

直接父minJ={x['minimum_J']!r}、max|Hu|={x['max_abs_Hu_per_mm']!r} /mm，轴向Hu约72.5806%，旧尖端栅格边无符号距离约.00866824 mm；均为已有普通保存值，未新定位局部场，不是解析圆有符号接触门。

原PROBE请求[0,.025]，实际q=[0,.0125,.025]；首次+.025的invalid_J、bitwise回滚/二分、F28/27、T15/15完整保留。HIGH1另是两态8F/5T、无failed/内部二分；未来N内部态不与旧q=.0125硬配。[HISTORY.json](HISTORY.json)保完整普通摘录。原低J/Hu及历史不因新success抹去，不授压力、纯接触、容量、稳定性、释放、整路径HP/HF5。

## 最小试算、可视化和资源

复用现有extend_native_guided_force，只需薄研究包装/分段viewer标签；不改生产源码、不重跑小模型、新HP或旧P1参考解码。未来API仅3旧NPZ：model opaque身份、geometry四mask、直接force末态两split，共2解码档6字段；普通核对只读协议/新result，viewer四普通JSON，无科学场。

成功后一次5PNG/实际N帧GIF：×1变形、P–q及根/段关系、三力/独立R/互斥账本、tip/右480格介质几何及全域保存J-Hu、全部Newton/trial/二分/原门。坐标zoom不改变形倍率，箭头倍率明确，无局部场读取不称局部分布；按真实N写全部帧，不硬定2或17。partial不启动后续核对/显示。

|阶段|候选窗口与包含关系|
|---|---|
|controller|1800秒，包含在science中|
|science|2100秒=进程2085+清理15，含导入/准入/科学读/fresh/路径/保存|
|普通核对|60秒=45+清理15，协议/新result原门及继承，无参考NPZ|
|显示/root QA共享|600秒，viewer510+清理15，五图各一次检查须在共享585秒前完成|
|helper|3000秒=2100+60+600+240其他调度/清理/一次封存|
|outer|3060秒/最多51分钟，64GiB采样/四库cap16/CPU，viewer原8GiB|

依据HIGH1 science监督398.9298秒预留；小增量不保证更快/成功，低J/二分可能耗尽额度，按原规则停不加时/降门。最终包装冻结须核绝对deadline和清理/封存余量，不能science后再加controller或显示后另开QA。

首个终端错误停止后续科学/核对/显示，保真实partial和全部内部尝试；原Armijo/有界N二分允许。无外部重试/修复重跑/延期/force、新HP/测试、生产修改/安装、API关联、q回放、旧包解压/科学复制、删除/回滚。四层SUP2同实例终止/全部成员覆盖/句柄释放后，原窗口有余量才一次完整/部分原字节封存，不补开封存窗。

[候选执行卡](L-CTIPFSTEP1_CARD.md)、[接口/验收细则](TASK_SPEC.md)、[机器合同](CONTRACT.json)约束下一步。当前真实包装未编写/试跑；新卡获批后先编写、冻结、独立静审再唯一启动，含记录、普通main推送和同机异目录恢复。旧HIGH1/FRESUME1窗口已关闭。

## 准备结论

[来源审阅](author/SOURCE_AUDIT.md)16项、[数学/资源审阅](author/MATH_RESOURCE_AUDIT.md)12项通过并保限定。当前58源保持；普通来源/stat不等于payload/fresh已通过。先按候选卡安排一个正式P2，再据真实q/R/J/Hu/收敛决定后续，不扩扫描。恢复见[RECOVERY](RECOVERY.md)，总览见[人工页](inspection.html)。
''')
write('TASK_SPEC.md',f'''
# 最小正式续载接口及验收细则

2026-10-24，仅准备。[精确合同](CONTRACT.json)、[来源](SOURCE_BINDING.json)。保持mean1.06及原导向物理，只新增绝对P2，未知q2由平衡求解。

```python
# 候选调用说明，本准备未执行。
from hf_eval.native_guided_force_resume import extend_native_guided_force
result = extend_native_guided_force(
    saved_force_result="D:/hfh1_001/run_001/force/result.json",
    full_extended_body_load_targets_half_N=[{P0!r}, {P1!r}, {P2!r}],
    output_directory="D:/hfst1_001/run_001/force",
    time_limit_seconds=1800.0,
)
```

不传q/物理/非clock覆盖，不改58份生产源或依赖，不添加CLI/另一个求解器。output须新建于直接force与fixed父树之外；本机fixed父原位，无需fixed_parent_result覆盖。跨机另显式核同字节恢复范围，不能在本卡静默解包。

## 成功分类

1. 来源/fresh：同一直接父及原fixed/model/geometry、kernel、完整前缀/非clock设置；首态global1/segment0/fresh/checks1，q/P/R bits与原state/两split字段SHA保持。不以小误差替代硬身份，不修复锚点。
2. 数值路径：每态含内部点保原ρF/ρP、mean、正有限J/F/Hu、global和rigid门；末原目标P2/global2精确达到。完整三目标只是谱系，`full_extended_path_executed_by_child=False`；segment_completed/target_reached等依据真实结果，不声称重放旧P0→P1。
3. 普通核对：独立进程只读协议与新result，核继承、global/segment索引、rootP0/segmentP1、原标量门、目标/源身份；不解码state NPZ、不新建参考。正增SP=P不代表可免核rootP0字段。
4. 参考/资格：P2给q/HP参考not_available，相关q/fullDOF/R误差null，不能填0或借旧P1工程界。q2−q1、力/介质变化只描述，不设q必须增加/预期斜率。局部总弱力平衡不授容量/稳定性/压力/纯接触/释放。
5. 显示/清理：数值与普通核对通过才生成5PNG/真实N帧GIF、各新PNG一次检查；四层SUP2原合同与有余量一次封存；数值、显示、清理、封存分别记录。partial/只有fresh不写达到P2。

## 读取和计数

API仅3旧NPZ不同路径（model只opaque hash，geometry四mask，直接HIGH1 state两split）共2解码档6字段；不读fixed012/probe/旧fields/force/tangent/matrix。新保存NPZ raw回读/hash另计，字段解码数与文件open观察分开。

普通核对只协议/新result；viewer四普通JSON：protocol、observer_binding、新result、continuation_check。沿原565body节点/510格、tip11260、右480格ID，先核新result.model相位；不重mask/读取旧媒体或局部字段。×1实际变形、坐标zoom和箭头倍率分开标，不把全域J/Hu曲线说成局部场图。

full3目标，本段2原请求（fresh P1、新P2），global offset1；内部态global原索引2/is_original_target=False。至多5态由原Nmin截止派生，不改maxdepth4或强截。原PROBE q=.0125/invalid_J只历史，不硬配未来N内部态。

原Armijo/有界N二分允许；首个终端错误停止后续科学/核对/显示，保存实际partial。无外部重试、修复重跑、延期、force、q目标回退、新HP/测试、生产修改/安装、API关联、旧包解压/科学复制、删除/回滚或补封窗。资源及共享deadline以候选卡为准。
''')
write('L-CTIPFSTEP1_CARD.md',f'''
# L-CTIPFSTEP1：正式r9非零q小载荷续载候选卡

2026-10-24。**尚未获批或执行。** 本轮只准备，见[PREPARATION](PREPARATION.md)、[TASK_SPEC](TASK_SPEC.md)、[CONTRACT](CONTRACT.json)。获批后先编写最小研究包装，冻结已安装58源/SUP2/包装/普通来源及声明科学路径，独立静审通过再唯一启动；本准备不试跑/导入HF/pytest或新fresh。

## 任务和原门

现有extend_native_guided_force从`D:/hfh1_001/run_001/force/result.json`成功末态accepted1/original1续载。full targets=`[{P0!r}, {P1!r}, {P2!r}]`，仅算[P1,P2]；候选新output=`D:/hfst1_001/run_001/force`。原非零绝对q={x['body_q_mm']!r} mm、signed R={x['R_input_N']!r} N、P1/两split继承；mean1.06保持、q2未知。P2按源binary64计算P1+(P1−P0)/4，不由显示截断值生成。

保持α2.5e−7/γ1e−6/r9/(80,40)/right92/Lr80/E1/ν.3/plane strain/t20/h.5、14720单元/29970DOF、全部原成员/端口/支撑/导向及非clock设置、mechanical/chunk256/guided_reduced_tangent。P为含t20的半模型绝对N、显式只入账一次，完整镜像2P/q不加倍；body-y/背景去重和旧body-x处方移除保持，不重mask。

root P0={P0!r} N保持，段anchor=P1；SP=max(|P|,|root P0|,2.12e−7)，本正增段实际SP=P。Nmin={L['minimum_force_increment_half_N']!r} N/maxdepth4/maxchecks25及其他非clock规则不改；Δ/Nmin={L['new_increment_over_Nmin']!r}，原截止允许两级二分、最多fresh+4叶=5态，不新增强截或改maxdepth。

fresh须checks1及原q/P/R bits、两split字段/state身份保持，不修复/投影。所有接受态保原ρF/ρP≤1e−9、mean界1.0600000000000001e−10 mm、全J正有限/原F-Hu有限性、global≤1e−6、rigid/zero≤8e−11 mm及其余原门。新原目标P2/index2是否到达及segment/full谱系分别核。P2无给q/HP参考，旧P1工程误差只历史，不填新零误差或指定q2。

旧minJ约4.166e−4/Hu轴向72.58%、PROBE invalid_J/回滚/q=.0125内部二分、HIGH1两态零失败均保留，不配伪中间态。原参考/压力/纯接触抗拔/极限/稳定性/释放/整路径HP/HF5资格不升级。

## 读取和实际显示

API只3旧NPZ：fixed model opaque hash、geometry四mask、直接HIGH1 accepted001两split，共2解码档6字段。旧fixed012/probe/fields/force/tangent/matrix/ZIP/媒体不读；无旧包解压或科学复制。新保存NPZ正常raw写/hash另计。普通核对只读协议/新result，viewer四普通JSON上限、无科学场。

数值及普通核对全通过后一次生成5PNG/真实N帧GIF：实际×1变形，绝对P–q，三力/独立R/互斥账本，tip/右介质几何及全域保存J-Hu，全部Newton/trial/二分/原门。坐标zoom/箭头倍率明确，不插值、固定2或17帧或伪画局部场。五新PNG各最多一次像素检查。

## 独立预算、停止和交付

controller1800秒包含在science2100秒内；science进程2085+清理15，含导入/准入/读取/fresh/路径/保存。普通核对60=进程45+清理15。显示/root QA共享600：viewer510+清理15，五图各一次检查须在共享585秒前完成，余15退出。helper3000=2100+60+600+240其他调度/清理/一次封存；outer3060秒（最多51分钟）。采样64GiB、四库cap16、CPU；viewer原8GiB。冻结审清绝对deadline，不能science后再加controller或显示后另开QA。

依据HIGH1科学监督398.9298秒预留；小步不保证更快/成功。唯一启动，首个终端错误停止后续科学/核对/显示，保实际partial；原内部Armijo/有界N二分允许。无外部重试、修复重跑、延期、force、新HP/测试、生产修改/安装、API关联、q回放、删除/回滚或旧科学包复制解压。沿SUP2同实例终止信号+全部成员覆盖+句柄释放；四层清理通过且原窗有余量才一次完整/部分原字节封存，不另开补封窗。

包括实际记录、五图各一次检查、普通main推送及同机异目录恢复。不改原结果/失败/资格；若失败据typed错误/partial决定下一步，不静默改α/步长/原门或加时。

需要另行批准的原因：用户本轮只授权准备；HIGH1/FRESUME1窗口均关闭。本卡新增正式r9非零q平衡、科学读取、实际显示和独立资源额度，不能沿用旧授权。
''')
write('RECOVERY.md',f'''
# 恢复与交接

2026-10-24，当前是**正式r9非零q续载准备完成，尚未求解**。先读[PREPARATION](PREPARATION.md)/[TASK_SPEC](TASK_SPEC.md)/[候选卡](L-CTIPFSTEP1_CARD.md)/[人工页](inspection.html)；CONTRACT给精确binary64、设置和预算，SOURCE_BINDING/HISTORY保来源及困难记录。

生产`hf_repo/src/hf_eval`已有58份源码；最近FRESUME1三文件已安装并通过12小模型验证，本准备不修改。旧HIGH1/准备文中“尚无force续载”是历史时点，当前能力以FRESUME1及本页顶部为准。

直接源`D:/hfh1_001/run_001/force/result.json`及accepted001/state.npz，根fixed树`D:/hpr1_001/parent_001`的model/geometry/普通相对链仍需。新续载不解码fixed012 split。不要为换盘符编辑已绑定JSON/descriptor/SHA。

[HIGH1恢复说明](../lf_circle_tip_force_control_high_001/RECOVERY.md)及[原包成员](../lf_circle_tip_force_control_high_001/execution/EVIDENCE_MANIFEST.json)覆盖直接force缓存；根fixed依赖沿HIGH1/PROBE1原交付。无需重复复制旧包到本准备；本轮没有解包/核payload/跨机运行。换机在新卡明确恢复位置和读取/复制范围，显式传同字节fixed_parent_result；不能静默扩本卡。stat和普通pin不代替未来科学准入/fresh。

作者`D:/hf-native-workpiece-api-author-20261024/L_CTIPFSTEPPREP1_preparation_001`；正式仓库`D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC`；origin保持`https://github.com/dudaxing/Compliant-TO-TMC.git`。同机异目录`D:/hf-restore-20260930`仅核Git/本轮新文件字节，不代表异机复算。

新PNG/SVG是概念说明，不能当真实新变形。实际trial包装未编写，获批后先冻结/静审再唯一运行。旧低J/Hu/invalid_J/内部二分及资格保持；P2下q2未知，不授新参考/压力/纯接触/容量/稳定性/释放/HF5。
''')
print(json.dumps(dict(status='PASS',human_specs=5,observer_retained=True,scientific_calls=0,production_changes=0),ensure_ascii=False))
