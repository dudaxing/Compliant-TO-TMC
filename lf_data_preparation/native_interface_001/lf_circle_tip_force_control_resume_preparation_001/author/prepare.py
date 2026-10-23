"""Read ordinary descriptors/source; write a preparation specification only.

No HF import, NPZ/ZIP opening, mechanics, test discovery or actual-state plot.
"""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

A = Path(__file__).resolve().parent
R = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
REL = 'lf_data_preparation/native_interface_001/lf_circle_tip_force_control_resume_preparation_001'
F = Path('D:/hfh1_001/run_001/force/result.json')

def write(name, value):
    payload = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n' if isinstance(value, dict) else value.strip()+'\n'
    (A/name).write_bytes(payload.encode('utf-8'))

def ordinary(path):
    raw = path.read_bytes()
    return json.loads(raw), dict(path=path.as_posix(), bytes=len(raw), sha256=sha256(raw).hexdigest())

force, force_pin = ordinary(F)
fixed_path = Path(force['source']['parent_result']['path'])
fixed, fixed_pin = ordinary(fixed_path)
model_path = Path(force['source']['parent_model']['path'])
model, model_pin = ordinary(model_path)
geometry_path = model_path.parent/model['source_geometry']['snapshot']['descriptor']
geometry, geometry_pin = ordinary(geometry_path)
selected = force['accepted_steps'][-1]
P0, P1 = force['force_task']['body_load_targets_half_N']
assert force['status'] == 'success' and force['target_reached'] is True
assert selected['is_original_target'] and selected['original_target_index'] == 1
assert selected['P_target_half_N'] == P1 and force_pin['sha256'] == '8caad93b7f765af9b70597b4c3992b8425af2a77c74b7e7eb68fafee8fda3355'
assert fixed_pin['sha256'] == force['source']['parent_result']['sha256']
assert model_pin['sha256'] == force['source']['parent_model']['sha256']
production = [dict(path=p.relative_to(R).as_posix(), bytes=p.stat().st_size, sha256=sha256(p.read_bytes()).hexdigest()) for p in sorted((R/'hf_repo/src/hf_eval').glob('*.py'))]
assert len(production) == 57
scientific = []
for path, declaration, purpose in (
    (model_path.parent/model['arrays']['path'], model['arrays'], 'Future opaque model identity only; no decode'),
    (geometry_path.parent/geometry['arrays']['path'], geometry['arrays'], 'Future original four geometry masks'),
    (F.parent/selected['state']['path'], selected['state'], 'Future immediate force-parent lift/fluctuation only')):
    scientific.append(dict(path=path.as_posix(), exists=path.is_file(), bytes=path.stat().st_size,
        declared_sha256=declaration['sha256'], declared_fields=declaration['fields'], purpose=purpose,
        current_action='stat only; content not read, hashed or decoded'))
assert all(row['exists'] for row in scientific)
binding = dict(stage='L-CTIPFRESUMEPREP1', created_utc=datetime.now(timezone.utc).isoformat(),
    status='prepared_not_implemented_not_executed', baseline=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R).decode().strip(),
    ordinary_sources=[force_pin,fixed_pin,model_pin,geometry_pin], production_source_files=production,
    source_force_schema=force['schema_version'], source_force_descriptor_sha256=force['descriptor_sha256'],
    selected_force_state={key:selected[key] for key in ('P_target_half_N','body_q_mm','R_input_N','state_sha256','state','is_original_target','original_target_index','minimum_J','max_abs_Hu_per_mm')},
    selected_accepted_index=len(force['accepted_steps'])-1, root_fixed_source=force['source'],
    force_task=force['force_task'], settings=force['settings'], force_settings=force['force_settings'],
    response_mode=force['response_mode'], tangent_mode=force['tangent_mode'], initial_guess=force['initial_guess'],
    producer_mechanics_sha256=force['mechanics_source_sha256'], scientific_dependencies_stat_only=scientific,
    original_preload_half_N=P0, segment_anchor_half_N=P1,
    later_real_increment_candidate=dict(formula='P1+(P1-P0)/4', P_candidate_half_N=P1+(P1-P0)/4,
        executable=False, note='Only after small-model success and a new formal preparation/authorization'),
    actions=dict(ordinary_source_paths=4, production_source_paths_hashed=57, scientific_stat_paths=3,
        counting_basis='Unique bound paths; drafting/review may reread ordinary metadata/source. Not an instrumented open-event count.',
        scientific_NPZ_content_reads=0, scientific_NPZ_hashes=0, NPZ_decodes=0, ZIP_decodes=0,
        HF_imports=0, force_calls=0, tangent_calls=0, HP_calls=0, tests_run=0, production_changes=0,
        schematic_is_not_actual_solution=True),
    admission_note='Ordinary identities and stat availability only; future payload validation and fresh mechanics remain required.')
write('SOURCE_BINDING.json', binding)
write('SOURCE_BINDING.md', f'''
# 来源与本轮实际读取

2026-10-23；基线`{binding['baseline']}`。本页是准备记录，不是续载结果或科学缓存准入回执。完整原值见[SOURCE_BINDING.json](SOURCE_BINDING.json)。

|普通来源|原字节SHA256|
|---|---|
|当前force/result.json（{force_pin['bytes']}B）|`{force_pin['sha256']}`|
|原fixed父result|`{fixed_pin['sha256']}`|
|原model描述|`{model_pin['sha256']}`|
|原geometry描述|`{geometry_pin['sha256']}`|

候选父为当前force的accepted1/original1成功末态：P1={P1:.17g} N，绝对q={selected['body_q_mm']:.17g} mm，signed R={selected['R_input_N']:.17g} N；state声明`{selected['state_sha256']}`。state.npz声明SHA=`{selected['state']['sha256']}`，lift/fluctuation均float64[29970]。本轮只stat，不读其内容、散列或解码，也不从positions反推split。

原预载P0={P0:.17g} N；原Nmin={force['force_settings']['minimum_force_increment_half_N']:.17g} N、max_bisections4、minimum_increment=.00625 mm分别保留，N/mm不互换。原minJ={selected['minimum_J']:.17g}、maxHu={selected['max_abs_Hu_per_mm']:.17g}仅来自已有普通标量，未新定位场极值。

本轮读取4份普通描述，绑定57份当前生产源码；对未来3个科学依赖只stat：原model.npz、geometry.npz和force accepted001/state.npz。已存在不代表payload已核。未来真实续载的最小科学读取预计仍为3路径：model整档身份、geometry四mask、force split两字段；不应为复用旧_admit而再解原fixed q0态。小模型未来自行生成的缓存另计，不借正式旧缓存。

完整物理：α2.5e−7、γ1e−6、r9/(80,40) mm、right92/Lr80 mm、E1 MPa/ν.3/plane strain/t20/h.5；14720单元/29970DOF、原510工件单元/565节点、端口/支撑/导向不变。父force producer的六源SHA全部原样保留；未来受授权改动的controller/API可不同，原力核与切线两源SHA必须继续匹配。不能为了新controller静默重写旧producer身份。

正式旧force完整结果与state位于[HIGH1原包](../lf_circle_tip_force_control_high_001/execution/execution_evidence.zip)，原fixed模型依赖见[HIGH1恢复说明](../lf_circle_tip_force_control_high_001/RECOVERY.md)。本轮未解包或复制科学档。D路径只是本机历史来源，换机恢复需新路径绑定与明确读取范围。
''')
write('PREPARATION.md', f'''
# L-CTIPFRESUMEPREP1：力控保存态续载准备

2026-10-23。**最小规格准备；尚未实现或执行。** 本轮只查源码/普通描述、科学档stat与概念示意；新F/T/HP、平衡、测试、生产修改均0。[来源](SOURCE_BINDING.md)、[接口合同](INTERFACE_SPEC.md)、[验证方案](VALIDATION_PLAN.md)、[候选执行卡](L-CTIPFRESUME1_CARD.md)。

## 目标、进度与目的

整体目标是独立HF读取LF夹持器，在一致大变形/TMC物理下分析实际变形、反力、工件作用及加载/卸载，逐步研究承载。固定工件路径、保存态续算、规定q探针及导向力控已有；[低输入.50](../lf_circle_tip_force_control_real_001/RESULTS.md)和[高输入1.06](../lf_circle_tip_force_control_high_001/RESULTS.md)已完成“给P→未知q→给q参考”局部交叉。

缺口是现力控入口只接受原固定load_only末峰，并从q0/零lift开始，不能接续已经移动的force末态。若每次加P都回原q0重复整段，会丢掉直接复用成功状态的功能。本轮把这一缺口缩成显式保存态续载：继承当前非零q、预载P、R、split与原物理；新载荷仍独立求q，不把旧参考答案输入求解器。

准备的实际效果是明确两处重要继承关系及可检验的最小实现边界；尚没有续载数值成功。当前57份生产源码保持，未来最多改2份/新增1份，不改力核、切线、原fixed/probe默认语义或其历史结果。

## 状态关系示意

![概念示意，不是新计算结果](continuation_schematic.png)

图仅表达状态和控制量继承，不画新的真实变形或接触状态。原P0用于残差尺度；P1是本段fresh起点；q1绝对继承，不是从零重定义。新P2下q2未知。[SVG](continuation_schematic.svg)。

|保留项|原值/语义|
|---|---|
|机构mean|1.06 mm，原加权端口，不是每个端口节点固定|
|原预载P0|{P0:.17g} N，原全路径尺度锚点|
|本段起点P1|{P1:.17g} N，绝对half-N；不是ΔP|
|继承q1|{selected['body_q_mm']:.17g} mm，仍相对原未变形坐标|
|继承R1|{selected['R_input_N']:.17g} N，原signed机构乘子|
|原状态|lift1 + fluctuation1；lift1工件x分量已经等于q1|

原物理/网格/材料/工件成员/支撑及所有非clock设置保持。P已含20mm厚度，完整镜像装配轴向载荷2P、q不倍增；Q=Σbody f_int,x、g=Q−P、ON-body Fx=−Q；P与机构R分开，显式P只入账一次。工件uy=0/转角0，不扩自由工件或摩擦模型。

## 两个必须保持的数学事实

1. 保存态的lift已有q1。fresh必须直接使用原两split、q1、P1和R1，首个新F/T检查即通过；不从positions重建、不平移q原点、不加q1第二次、不做predictor/均值投影/Newton修复。后续候选只覆盖`lift[body_x]=q_absolute`，其余lift为原零值，原fixed位置的fluctuation仍0。
2. 把segment_anchor=P1与force_scale_anchor=root_P0分开。始终保`SP=max(abs(P),abs(root_P0),Ffloor)`，不能用P1替换原P0。真实小模型存在负P递增、绝对值下降的历史，正P高输入例不会暴露这个门漂移，因此必须保负P验证。

原freeρF≤1e−9、bodyρP≤1e−9、mean原公式、全部相关J>0/有限、global≤1e−6、rigid/zero≤8e−11 mm不变。正式mean原界1.0600000000000001e−10 mm、Ffloor2.12e−7 N保持；小模型用相同公式及自身尺寸，不照搬正式数值。最小N步长继承来源，不按新小增量重算。

## 准备结论与推进顺序

最小实现与验证限下一张卡的小模型；不在本准备直接给正式模型加P。先编写/冻结/独立静审候选，再唯一执行有限小模型验证和一张实际图；全部通过才安装三份已测源码。成功后另准备正式小增量，候选公式可取P1+(P1−P0)/4={P1+(P1-P0)/4:.17g} N，当前不是执行目标或已批准任务，q2不预设。

现正式末态minJ约4.17e−4，轴向Hu约72.58%；功能续载并不自动取得纯接触压力、承载极限、释放、摩擦或稳定性资格。既有失败/二分和资格完整保留。本准备及后续记录须区分源码静审、小模型成功、正式计算三种事实。
''')
write('INTERFACE_SPEC.md', '''
# 最小接口与状态继承合同（候选，未实现）

## 显式新入口

```python
# 未来候选签名；当前安装版本不存在，不能执行本段。
from hf_eval.native_guided_force_resume import extend_native_guided_force
child = extend_native_guided_force(
    saved_force_result, full_extended_body_load_targets_half_N, output_directory,
    fixed_parent_result=None, time_limit_seconds=60., on_accept=None,
)
```

`saved_force_result`是成功force结果；只选其最后接受态且必须是完整原目标末点，不提供任意selected index。载荷列表为完整延伸任务：原full P列表精确前缀＋至少一个严格增加的绝对有符号half-N。实际仅计算`[P_parent_last]+新增后缀`，首点fresh复核。无q、R、force_settings或物理覆盖参数；除新clock外，原settings/force_settings、response/tangent、guided predictor全部继承。q可正可负，P可正可负；不能把“严格递增”解释为增大abs(P)。

输出必须是直接force父树和实际解析的root固定父树之外的全新目录。默认`evaluate_native_guided_force`签名及fixed父/q0准入保持；不添加CLI、通用fallback或任意任务迁移框架。

## 最小源码范围

|文件|必要变化|
|---|---|
|[split_guided_force.py](../../../hf_repo/src/hf_eval/split_guided_force.py#L101)|增可选`initial_body_q_mm=0.`与独立`force_scale_anchor_half_N=None`；默认仍原零lift/q0；续载保绝对q和root尺度，原非对称KKT/Armijo/N二分及原门不改。|
|[native_guided_force.py](../../../hf_repo/src/hf_eval/native_guided_force.py#L54)|提取一次私有执行/缓存保存runner，原入口仍走原_admit；新入口复用同一力、缓存、ledger、capture及保存代码，避免第二套求解/组装。|
|新增`hf_repo/src/hf_eval/native_guided_force_resume.py`|显式force父准入、完整任务前缀/来源绑定、唯一选末态、继承与新结果谱系。|

另新增一份有限测试，作为研究证据交付；不安装到生产src。原57源中其余55份保持同字节，完成后生产共58份。原kernel/tangent/默认fixed/probe/native_resume/__init__/response/CLI不改。若实现发现必须超此范围，应在启动测试前说明并修订候选，不默加修改。

## 可接受来源与准入

只支持已知`hf-native-guided-force-1.0`原任务或本次拟新增`hf-native-guided-force-1.1`延伸任务。必须status=success、target_reached=true、failure=null；末态是原请求最终载荷，原目标覆盖当前段，完整任务严格递增，schema/状态/索引一致。partial/probe/fixed结果不是本入口合法force父。

原1.0 source有固定父/模型/geometry绑定；从root固定模型的普通描述和四geometry mask重建project，核网格/材料/区域/端口/支撑/工件节点及source身份。不可直接调用旧native_probe._admit：它会拒非零lift并多解无用的fixed q0 state。新准入只解直接force父末态lift/fluctuation两字段，不读fields/旧力/切线/矩阵或fixed q0 split。

先核普通JSON原字节与canonical身份/已知schema及任务，再核opaque model身份、geometry四mask与selected state archive/字段SHA、dtype、shape、state hash。保原producer源码身份声明；API/controller授权演进不要求六文件全部与旧producer相等，但两force/tangent kernel SHA必须与当前相同，不能重写旧pin。新模块进入新结果producer清单。普通source错误在F/T前typed拒绝；本准备只完成静态合同，没有完成这些未来payload/fresh门。

1.1 child保浅层root固定来源、root force结果历史pin及直接force父pin/selected元数据，不把整个父result或历史嵌套复制。再次延伸只读直接父及root固定result/model/geometry，按直接父完整目标首点保持rootP0、前缀/索引/原设置；不递归读祖先force结果或NPZ。root force pin是保留谱系，不宣称本次独立重核了每个祖先的全部数值路径；普通canonical/SHA是身份绑定，不是真实性签名，不能检测全部可信pin被一起伪造重写。

唯一来源定位参数`fixed_parent_result=None`默认用父声明的root固定result路径；换目录时可显式指定该文件的新位置，但raw SHA/canonical必须与保留的root固定pin相同。model/geometry只从该固定result的相对声明派生，并核原pin；不能借此换模型/物理。新结果分别记录历史声明和实际解析位置，原source字节不改。它不允许指定q/R/settings或替换selected split；后者从直接force结果的相对路径读取。小模型child采用一次显式同字节固定树迁移，grandchild再按其记录默认解析，以验证换目录路径而不另加真实路径。

## 位移、预载与fresh检查

原物理位移`u=lift+w`，工件lift_x=q_absolute，其他lift=0，w[原fixed]=0；x_body=X_body+q。准入保selected两split原字节，finite q/R/P及元数据一致，精确工件lift与q声明，原body/zero结构不变。fresh不重建、不重排、不投影，保持state hash及q/R/P的float64字节，Newton checks=1，无predictor或修正线性解；失败即`initial_state_not_equilibrated`，不强行修复成新起点。

新步仍求`(w_free,q_absolute,R)`。impose覆盖body-x的lift，不累加；R沿原符号，mean约束相同。segment_anchor_P是直接父终点，scale_anchor_P永远最初force根P0；即使负P逐步靠零也保`SP=max(abs(P),abs(root_P0),Ffloor)`。mm minimum_increment与half-N minimum_force_increment分别继承，原N二分/rollback/时间门保持。

## 新结果语义

新结果用1.1，原根结果不改。`force_task.body_load_targets_half_N`保存完整延伸目标；`anchor_target_half_N`保持根P0语义，新增`force_scale_anchor_half_N`=rootP0、`segment_anchor_half_N`=直接父P末值。`continuation`保存直接父result pin、末态P/q/R/state/archive pin、完整源目标、新完整目标、段目标、global offset、root普通身份、fresh检查与身份结果。

1.1再次准入必须明确核`full_targets[0] == anchor_target_half_N == force_scale_anchor_half_N == root_P0`，末原态P等于full_targets[-1]，段锚点/段目标覆盖/global index相互一致。1.0没有这些新增字段时，从其完整force目标首点按已知旧schema提取rootP0，不能用当前段首点猜测。

`accepted_steps`只含本段fresh锚点和实际新增态，包括内部二分；`original_target_index`映射完整任务global index，另保segment_original_target_index。`load_increment_from_anchor_half_N`明示指本段锚点，另报`load_increment_from_root_half_N`；q从不减q_anchor。path_summary只描述实际本段，明确`full_extended_path_executed_by_child=false`，不能把带谱系的任务前缀说成本次重算。

数值success仅为本段原门通过；独立参考、整路径HP、压力、有效夹持、释放/HF资格均不因续载升级。所有F/T尝试与完成计数、内部失败/二分/回滚、actual accepted/新保存缓存及ordinary摘要如实保留；save-time F/T=0。新段K从fresh F/T取得，不载旧矩阵或旧force字段。

## 有限错误合同

|触发|结果|
|---|---|
|schema/源身份/非success/非末原目标/坏split或q声明|`invalid_saved_state`，F/T前拒绝|
|缺新目标、改原前缀、重复/下降/非有限或非实数载荷|`invalid_task_extension`（新入口），F/T前拒绝|
|clock/callback/output参数错误|沿用`invalid_settings`/`invalid_input`|
|低层initial_body_q非有限/非实数；q与原lift结构不符|分别`invalid_input`、`constraint_conflict`，F/T前拒绝；新公共入口把坏保存态声明归`invalid_saved_state`|
|fresh原态不平衡|失败partial，`initial_state_not_equilibrated`，无修复|
|后续真实数值/时间/保存错误|原typed failure与实际partial；不转成success，不补零、不重跑|

准备没有改任何现有错误码；以上新增入口码约定待候选静审与有限验证确认，不在旧默认入口改错误语义。
''')
write('RECOVERY.md', '''
# 准备包的审查与恢复

先看[PREPARATION](PREPARATION.md)、[接口](INTERFACE_SPEC.md)、[验证](VALIDATION_PLAN.md)、[候选卡](L-CTIPFRESUME1_CARD.md)和[来源](SOURCE_BINDING.json)。示意是概念图，没有新增实际变形。author保准备脚本/两份独立源码审查备忘/最终准备审阅；它们不是可运行的生产实现。

本包不重复正式科学数据。HIGH1末态完整force/result与state在[既有原包](../lf_circle_tip_force_control_high_001/execution/execution_evidence.zip)，原fixed模型与geometry沿[HIGH1恢复说明](../lf_circle_tip_force_control_high_001/RECOVERY.md)追溯。本轮未解包、散列旧科学档或重开旧媒体。若换机实施，应先核包身份、在隔离目录按原相对结构恢复最小树，再显式绑定新路径/复制解压范围，不改写旧result/SHA使之冒充原身份。

新功能尚不存在；本包示例签名不能在当前生产上执行。未来实现候选另冻结/静审并取得新执行窗口，旧卡已关闭。普通main提交/同机异目录字节恢复只验证交付可取回，不证明异机环境可算或数值成功。
''')
write('L-CTIPFRESUME1_CARD.md', '''
# L-CTIPFRESUME1：最小力控保存态续载实现/小模型候选卡

2026-10-23。**候选，尚未批准、实现或执行。** 本轮用户只授权最小规格、接口与验证准备；原HIGH1窗口已关闭。本卡获批才编写候选、冻结全部源/任务/唯一启动包装并独立静审，静审通过后唯一运行；无试运行、先行pytest收集、正式r9计算或生产预安装。

范围见[接口](INTERFACE_SPEC.md)及[验证矩阵](VALIDATION_PLAN.md)：2旧改+1新生产候选，1新测试；12个非参数化方法、最多7条16单元/50场DOF真实路径，另有限独立algebra oracle。显式force-result末态续载，保绝对q/P/R/split、rootP0尺度、完整载荷前缀与原门；默认fixed父力控、位移probe和所有非clock设置保持。受控partial/typed拒绝是预定验证，非预期首错才为卡终端错误。

tests共享480秒（进程465+同实例清理15），含导入、创建一次小fixture、最多7条真实路径/每条controller最多60秒、全部12方法及普通证据。显示与root一次检查共享60秒（viewer进程35+清理10、一次PNG检查须在共享55秒前，余5秒退出）。helper660秒=tests480+display60+其余冻结准入/调度/清理/同字节安装/一次封存120；outer720秒，最多12分钟。采样8GiB、四库线程cap16、CPU；额度不足即停，不临时追加。

仅全部有限验证通过才纯缓存viewer一次生成1张实际小模型图：direct/两段续载真实×1变形及标明倍数的位移箭头、P–绝对q及非零起点、R、same-P差、全部双残差/门和root-SP对照。禁止从正式r9旧科学缓存作图；新图最多一次像素检查，不重绘。全部测试、显示/QA及清理通过才安装三份已测同字节候选；其余55源保持，安装回执逐字节核对。失败不安装，若安装发生后异常则保实际字节，不自动回滚。

首个非预期终端错误停后续科学/显示/安装，保实际部分证据；无外部重试、修复重跑、延期、force、新HP、正式r9路径、默认物理改动、删除或自动回滚。原内部Armijo/N二分及预定异常测试允许，保持原typed partial。SUP2同实例终止/全部成员覆盖/句柄释放合同复用；清理成功且原窗口有余量才一次完整/部分原字节封存，不另开补封窗口。

包含实际记录、1PNG人工页、普通main推送与同机异目录恢复；不授正式真实续载、卸载/循环、自由y/转动、压力、承载极限、释放/稳定性或HP资格。小模型成功后另准备真实P小增量，不能直接沿用本卡扩正式计算。

需要新授权的原因来自本轮范围：您只授权准备，本卡新增生产实现/安装、小模型F/T与未知q平衡、实际图和独立资源窗口；不能使用已关闭HIGH1额度。
''')
print(json.dumps(dict(status='prepared_draft', ordinary_sources=4, production_sources=57,
    stat_only_scientific=3, new_science=0, files_written=6), ensure_ascii=False))
