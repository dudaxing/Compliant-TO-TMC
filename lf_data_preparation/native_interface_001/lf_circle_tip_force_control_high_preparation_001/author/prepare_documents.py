"""Ordinary preparation records only; never read scientific payloads or old media."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

A = Path(__file__).resolve().parent
ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
BASELINE = '293c542557c0abe59e1321713e9c3e251eeca465'
def write(name, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2)+'\n') if not isinstance(value, str) else value.strip()+'\n'
    (A/name).write_bytes(raw.encode('utf-8'))
def identity(path):
    raw=path.read_bytes(); return dict(bytes=len(raw), sha256=sha256(raw).hexdigest())
head=subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false','rev-parse','HEAD'], cwd=ROOT).decode().strip()
assert head == BASELINE
production=[dict(path=p.relative_to(ROOT).as_posix(), **identity(p)) for p in sorted((ROOT/'hf_repo/src/hf_eval').rglob('*.py'))]
assert len(production)==57
write('PRODUCTION_IDENTITY.json', dict(stage='L-CTIPFHIGHPREP1', baseline=BASELINE,
    files=production, scope='Only production .py source bytes, no scientific payloads'))
write('SCHEMATIC_QA.json', dict(stage='L-CTIPFHIGHPREP1', status='PASS', pixel_inspections=1,
    new_schematic_renders=1, scientific_or_deformation_renders=0, old_media_reads=0,
    image_identity=identity(A/'control_schematic.png'),
    findings=['All labels readable, no overlapping text; explicit preparation-only and not-FE-geometry heading.',
              'High fixed parent accepted012, nonzero P0 fresh first check and P1 solving unknown q/R are separated.',
              'Half-model t20 and guided y/rotation constraints, original low-J/internal-bisection history and candidate budget shown.',
              'Diagram is control/source explanation only; it does not depict an actual new gripper deformation.']))
parent=Path('D:/hpr1_001/parent_001/result.json')
observer_path=Path('D:/hpr1_001/observer_definition.json')
observer=json.loads(observer_path.read_bytes())
ids={k:observer[k] for k in ('body_cells','body_nodes','tip_node','right_medium_cells','right_boundary_nodes')}
assert len(ids['body_cells'])==510 and len(ids['body_nodes'])==565 and len(ids['right_medium_cells'])==480
write('observer_binding.json', dict(stage='L-CTIPFHIGHPREP1', status='prepared_not_executed',
    source_path=observer_path.as_posix(), source_ordinary_file_identity=identity(observer_path),
    held_input_mean_mm=1.06, source_parent_result_path=parent.as_posix(),
    source_parent_result_identity=identity(parent), **ids,
    scope='Reuse fixed reference IDs only; high-input physical context is bound to this parent. No mask or field payload read, no remask.',
    future_phase_check='Use newly returned result.model.solid to confirm the fixed right480 are original nonbody medium, without loading old scientific fields.',
    unsigned_tip_metric='Distance from original tip node to original raster-body physical boundary segments, excluding symmetry cut; not analytic-circle pressure/contact qualification',
    local_J_Hu_field_reads_planned=False))
write('PREPARATION_STATE.json', dict(stage='L-CTIPFHIGHPREP1', status='prepared_pending_independent_review',
    created_utc=datetime.now(timezone.utc).isoformat(), baseline=BASELINE,
    authorization_scope='Prepare high mean1.06 same-definition two-load force cross only; no new force equilibrium execution authorized in this turn',
    high_force_executed=False, NPZ_payload_opens_hashes_or_decodes=0, ZIP_decodes=0,
    old_media_opens=0, force_calls=0, tangent_calls=0, equilibrium_calls=0,
    HP_calls=0, tests=0, production_modifications=0, production_files_preserved=57,
    new_control_schematic_PNG=1, new_control_schematic_SVG=1, schematic_pixel_checks=1,
    diagram_library_scope='Matplotlib rendering of control diagram only; no HF mechanics imports or computed deformation',
    next_execution_card='L-CTIPFHIGH1_CARD.md', next_execution_status='not_approved_not_started'))
write('PREPARATION.md', r'''
# L-CTIPFHIGHPREP1：高输入1.06 mm两载荷力控交叉准备

2026-10-23。**准备完成；高输入力控尚未执行。** 本轮用户只授权核定父态、参考载荷、比较门、资源窗口及示意说明。本轮无NPZ内容读取／散列／解码、旧包解压、旧媒体重开、构模、F/T、平衡、HP、测试或生产源码修改；仅核普通元数据／源码与科学档stat，生成一张控制示意。

## 整体目标、已做什么与这一步的目的

整体目标是形成独立于LF设计代码的HF大变形／第三介质接触分析器，逐步实现可审查的变形、机构反力、工件受力及加载／卸载功能。现已完成LF多设计前向与保存态续算、选定态高精度参考、可视化／接口关联，以及固定机构输入下的规定q探针；导向力控又通过小模型17项验证及[正式r9／mean.50两载荷交叉](../lf_circle_tip_force_control_real_001/RESULTS.md)。

低输入正式功能闭环已验证，但尖端距离约.519 mm、轴向Hu约86.29%，不足以说明较强闭合工况下力控可用。本次选择已有mean1.06 mm固定父及其位移参考，保持其余物理和全部原门，准备“只给绝对P、独立求未知q”的第二个物理工况。没有把低输入force结果抬升输入或冒充合法固定父，也不新增力核或生产防御层。效果是形成有明确来源、比较规则、困难历史及预算的一次试算方案；没有预授高输入数值成功或承载资格。

## 控制示意

![控制示意，不是新有限元结果](control_schematic.png)

只说明来源／控制／验收顺序，不按真实几何比例，没有新计算变形。q=.025 mm只是求解后的位移参考，不作目标、预测初值或夹限；R是机构平均输入乘子，与工件外载P分开。[SVG](control_schematic.svg)、源码及[一次图像检查](author/SCHEMATIC_QA.json)保留。

## 已核定父态与两载荷

|项|核定内容|
|---|---|
|合法固定父|`D:/hpr1_001/parent_001/result.json`：原完整13目标load_only成功，最后原峰1.06 mm；选accepted12／original12。|
|迁移状态|原lift／fluctuation及signed R=0.19522304147728387 N；state声明SHA=e71c06973b7dc7aff7e5ee4a801b595cb3f054e907cc6e1ad52188e858500a68。|
|原位移参考|`D:/hpr1_001/run_001/science/result.json`，同父；原请求q=[0,.025]，实际接受[0,.0125,.025]。|
|P0|2.399800950672949e−4 N，原q0非零预载，等于原父ON-body Fx反号。|
|P1|2.561572865437846e−4 N，原probe接受索引2的q=.025 mm驱动力；新力控不输入该q。|
|ΔP／Nmin|1.6177191476489698e−5 N／1.011074467280606e−6 N，Nmin=ΔP/16；max_bisections4保持，至多17个实际接受态含锚点。|

P均为固定空间+x方向的有符号**绝对半模型合外载N，已含20mm厚度**；不得用0或ΔP替代P0，不再乘厚度。完整镜像装配轴向载荷取2P，q不倍增。Q_half=Σbody f_int,x、ON-body Fx=−Q_half，g=Q_half−P；显式P只入账一次，旧body-x处方驱动力移除，body-y导向与背景重叠去重。

原α2.5e−7／γ1e−6／r9／圆心(80,40)／right92／Lr80、E1MPa／ν.3／plane strain／t20／h.5、14720单元／29970DOF、510工件单元／565节点、全部端口及支撑保持。机构平均输入保持1.06 mm；工件body-x为未知q，uy=0、转角0，原成员不重mask。响应mechanical／chunk256，新的guided_reduced_tangent保持，父port_projection只为历史记录。

完整普通身份、来源字段及科学档声明／stat见[SOURCE_BINDING](SOURCE_BINDING.md)和[机器记录](SOURCE_BINDING.json)。旧父split_displacement控制器SHA与当前版本不同，而force／tangent核SHA匹配；准入以当前API规定的两kernel硬门及完整源身份为准，不伪称父全部mechanics文件同字节、不改写旧SHA。P0仍必须在未来执行中fresh F/T检查1原样接受，split与R逐位不变；有差即停，不用Newton修复或更换预载。

## 必须保留的旧困难记录

原高输入位移probe首次尝试q=0→+.025 mm出现invalid_J，控制器内部回退／二分接受+.0125，再接受+.025；这是原路径内部行为，无终端失败或外部重跑。原2请求、3接受态及failed_attempts均保留。原force调用28次／完成27次，tangent15次／完成15次，science监督1172.741484099999秒；不能抹去未完成F或据低输入311秒保证高输入耗时。

|原probe接受索引|q/mm|是否原请求|minJ|
|---|---:|---|---:|
|0|0|是／original0|4.6587891715793817e−4|
|1|.0125|否／original1的内部二分|4.3961981824698745e−4|
|2|.025|是／original1|4.166085295994876e−4|

旧末态轴向Hu约72.58%，尖端到原栅格边界无符号距离约.008668 mm。小J、高Hu及很小几何距离同时存在，不能由正P或tiny交叉误差推出纯接触、容量、稳定性或唯一分支。新力控若内部N二分，其P一般不等于旧q=.0125对应Q；不能硬配中间态或插值冒充实测。

## 原门与预先固定的工程比较

每个新接受态含内部二分必须保原free ρF≤1e−9、mean原公式门、J全正／有限、global≤1e−6、rigid／zero≤8e−11 mm，以及独立body ρP≤1e−9。保持原约束公式后，mean界为1.0600000000000001e−10 mm，Ffloor为2.12e−7 N；SP=max(|P|,|P0|,Ffloor)，不得用free门替代body合力门。

锚点：fresh检查1、原split／signed R／state身份逐位保持，不做predictor／投影／线性修正。端点另按下表工程界验收，不要求不同控制器终点逐位相同：

|P1端点对原probe接受2|预先界|
|---|---|
|q对原.025 mm|abs差≤1e−6 mm|
|全部29970DOF物理位移|max abs差≤1e−6 mm|
|R_input对0.19536542042187396 N|abs差≤max(1e−10 N,1e−7×abs(Rref))=1.9536542042187397e−8 N|

全场差逐DOF用fsum([lift_new,w_new,−lift_ref,−w_ref])，不减显示坐标。只用旧参考accepted0／2这两个原目标做锚点／端点科学对照，完整保留旧第1态及失败普通记录。三项是原先声明的功能工程门，不是严格误差界或稳定性证明，也不根据低输入实差收紧。详细公式和stop规则见[COMPARISON_GATES](COMPARISON_GATES.md)。

## 接口、读取、显示及资源

复用现有evaluate_native_guided_force，无生产修改／安装。薄研究包装必须改用selected12、hold1.06；低输入比较器的selected2、hold.50和len(reference)=2硬码不可照抄。先写包装、冻结完整源闭包和只读来源，独立静审后再按获批卡唯一启动；本准备未写或试跑真实包装。

API拟准入3个旧NPZ路径：opaque model只整档hash，snapshot geometry四mask，父accepted012 split两字段。成功后独立比较另读旧probe accepted000／002及新force anchor／P1的4个state档／8字段；合计7路径、6解码档／14字段，旧fields／force／tangent／matrix缓存不读。API字段数由冻结控制流支撑，运行可监测实际open事件，不伪称动态字段hook实测。当前只stat这些旧科学档，未验证payload身份或fresh平衡。

仅科学与工程比较都通过后，纯普通JSON viewer一次输出5PNG及全部实际N帧GIF(N≤17)：实际×1变形、P–q及原目标参考、signed total/material/Hu与独立R／外载账本、尖端／右480格介质几何／全域minJ和maxHu、全部Newton／trial收敛与独立门。原中间参考仅作为已有普通参考点说明，不能冒充新接受态。没有局部J/Hu数组就不画局部场；旧媒体不打开，5新PNG各最多检查一次。

|阶段|拟固定额度与包含关系|
|---|---|
|controller|3600秒，位于science worker内部，不单独叠加。|
|science总窗口|3900秒：进程最多3885＋同实例清理最多15；含导入、准入、实际科学读取、fresh检查、路径、保存。|
|比较|60秒：进程45＋清理15，含4档8字段和比较JSON。|
|显示及root QA共享|600秒：viewer进程最多510＋清理15；5图一次检查须在该阶段585秒前完成，余15秒退出余量。|
|helper|4800秒：3900＋60＋600＋240其他准入／调度／清理／一次封存余量，全部在原窗口。|
|outer|4860秒，最多81分钟。64GiB采样上限、四库线程cap16、CPU；viewer原8GiB子限保持。|

预算依据旧高输入近1173秒困难路径作预留，不保证力控成功或耗时。最终薄包装应将共享绝对deadline、阶段清理reserve和封存余量冻结审阅，不按阶段另开累计超窗。无足够时间或资源即停，不缩验收或加时。

首个终端错误停止后续科学／比较／显示，保存已产生partial和完整失败历史；原内部Armijo／有界N二分允许。无外部重试、修复重跑、延期、force强制执行、q目标fallback、新HP、测试、生产修改／安装、删除或自动回滚。四层SUP2沿用同实例终止信号＋全部成员覆盖＋句柄释放合同；清理证明通过且原窗口有余量才一次原字节封存，不开补封窗口。

## 恢复与准备结论

本机未来直接用D:/hpr1_001既存树，不复制／解压旧科学包。最小父树保完整13目标普通描述及selected012科学缓存，不声称包含13态全部科学档。普通来源副本和原位移结果在已发表PROBE1目录／本次source_context可审查；科学依赖沿用[PROBE1原包](../lf_circle_tip_probe_001/execution_evidence.zip)和[成员清单](../lf_circle_tip_probe_001/EVIDENCE_MANIFEST.json)。本准备未展开或核旧包payload。换机恢复路径必须在新执行范围明确计数／绑定，不能静默增加到本卡读取集。

当前静态前置和来源／门／预算已经明确，现有生产API可用，所需变化限研究包装的高输入来源及参考态选择。独立审阅与当前状态见author记录；57份生产源码保持，没有高输入force数值结果。发布恢复只做同机异目录Git和普通新文件字节核对，不代表异机数值复算。

下一步按[L-CTIPFHIGH1候选执行卡](L-CTIPFHIGH1_CARD.md)另行批准后，先冻结／静审薄包装，再唯一运行。通过则评估该局部导向总力功能在较强闭合工况的适用性；不通过则依据typed失败和实际partial安排诊断，不静默改门、改α或加q。暂不扩容量扫描、force续算／卸载、自由转动或新HP。
''')
write('L-CTIPFHIGH1_CARD.md', r'''
# L-CTIPFHIGH1：高输入1.06 mm同定义两载荷力控交叉执行卡

2026-10-23。**候选卡，尚未获批或执行。** 用户本轮授权的是准备父态／载荷／门／资源和示意。完整前提见[PREPARATION](PREPARATION.md)、[SOURCE_BINDING](SOURCE_BINDING.json)、[COMPARISON_GATES](COMPARISON_GATES.json)。发布后的main作为未来冻结基线；本卡获批后先写最小研究包装，绑定完整源码、普通来源和声明的科学读取路径，独立静审通过再唯一启动。无包装试跑、pytest收集、先行F/T或试绘真实保存态。

## 任务与保留项

从`D:/hpr1_001/parent_001/result.json`完整成功load_only最后原峰selected12/original12迁移q0原split和signed R=.19522304147728387 N。保持机构加权平均输入1.06 mm，唯一evaluate_native_guided_force调用只给绝对half N `[0.0002399800950672949, 0.0002561572865437846]`，独立求未知刚体q与原机构R。不传.025目标／初值，不用旧probe终态热启动，不从低输入force续算，不以0或ΔP替代P0。

原α2.5e−7／γ1e−6／r9／(80,40)／right92／Lr80、E1／ν.3／plane strain／t20／h.5、14720单元／29970DOF、510工件格／565节点、边界／端口及全部非clock设置保持，mechanical／chunk256、guided_reduced_tangent。P已含t20、显式只入账一次；旧body-x处方反力移除，guide/zero去重。body-y=0、转角0，原成员不重mask。Nmin=1.011074467280606e−6，maxdepth4，最多17接受态；旧mm最小步长另保留不作N步长。

原位移参考请求2个但接受3态：q=[0,.0125,.025]。首次直接+.025的invalid_J及内部二分历史、28/27次F和15次T计数、末态minJ=4.166085295994876e−4和较大Hu分量完整保留。新N二分态不假配旧.0125态。旧父controller SHA不同但kernel匹配的历史差异保持记录；当前准入硬门不变，P0 fresh首检必须原样通过，不做投影或Newton修复。

## 科学读取与验收

API仅3旧NPZ：model opaque核身份；source_geometry解码四mask；父accepted012/state解码lift/fluctuation。成功后的唯一比较读4个state NPZ（旧probe000／002、新force anchor／原P1终点）共8字段。合计7路径、6解码档／14字段，旧fields／force／tangent／matrix缓存不读。普通描述／SHA／观察ID及路径冻结；科学身份本准备只声明并stat，实际准入验证不能省略。本机直接使用既存D:/hpr1_001树；不含旧ZIP解压、科学包复制或新恢复目录，换机所需读取／复制须另行显式核定。

所有接受态（含二分）保原freeρF≤1e−9、mean原公式界1.0600000000000001e−10 mm、所有J正且有限、global≤1e−6、rigid/zero≤8e−11 mm及独立bodyρP≤1e−9。Ffloor=2.12e−7 N，SP=max(|P|,|P0|,Ffloor)与free尺度独立。fresh锚点check1、q0、lift/fluctuation与signed R逐位保持。P1事后对旧probe原请求接受2：q差≤1e−6 mm、全29970DOF四split项fsum的max差≤1e−6 mm、R差≤1.9536542042187397e−8 N；不按显示坐标减差，不改门或用q fallback。

API数值success与工程comparison分开报告；partial、未执行比较或参考不一致不填零差、不中途修复重跑。只有科学与工程比较均通过才一次普通JSON viewer输出5PNG＋实际N帧GIF：实际×1变形、P–q与原目标参考、total/material/Hu与R／互斥外载账本、尖端／右介质几何和全域J/Hu、全部双残差／Newton／trial收敛。只读4份普通JSON上限（协议、观察绑定、新result、比较），无局部场读取、旧媒体重开。各5新PNG最多一次像素检查，GIF按真实accepted态逐帧写不插值。

## 独立资源、停止与记录

controller3600秒包含在science总3900秒中；science进程3885＋清理15，含导入、准入、科学读取、求解及保存。比较总60秒（45＋清理15）；显示与root QA共享600（viewer进程最多510＋清理15、QA须在共享585前完成，余15退出），helper4800、outer4860秒（最多81分钟）。science3900＋comparison60＋display600＋其他准入／调度／清理／一次封存240=helper4800。采样64GiB／四库线程cap16／CPU，viewer8GiB保持；不足余量即停，不叠加或静默延期，实际绝对deadline在冻结前审清。

唯一启动，首个终端错误停后续科学／比较／显示；保实际partial／内部尝试／原失败历史。原内部Armijo与有界N二分允许；无外部重试、修复重跑、延期、force强制执行、新HP、测试、生产源码修改／安装、回滚、删除或API关联。复用SUP2同实例终止／全部成员覆盖／句柄释放合同。清理通过且原窗口仍有余量才一次原字节完整／部分证据封存，不能另开补封窗口。

包括实际记录、五图一次检查、普通main提交推送和同机异目录恢复核对。高输入成功也只支持这两载荷的局部导向总弱力平衡交叉，不授整路径HP、压力／纯接触抗拔、承载极限、摩擦、释放、唯一性、稳定性或HF5资格。

需要另行批准的原因：用户本轮只授权准备；本卡新增真实14720单元／29970DOF的F/T／未知q平衡路径、科学数组读取、实际显示及独立最多81分钟窗口，不能沿用已关闭的低输入FREAL1或旧PROBE1授权。
''')
write('RECOVERY.md', r'''
# 高输入力控准备的恢复边界

本目录是准备材料，尚无新高输入force结果或科学包。首先阅读[准备说明](PREPARATION.md)、[候选卡](L-CTIPFHIGH1_CARD.md)、[来源绑定](SOURCE_BINDING.json)、[比较门](COMPARISON_GATES.json)及[人工页](inspection.html)。

本机拟用原`D:/hpr1_001/parent_001`最小父树：原完整13目标result及model/source_geometry描述／缓存、仅selected accepted012状态；probe参考用`D:/hpr1_001/run_001/science`普通result和accepted000／002 split。旧父整个13态的科学档不需要，也不声称该最小树拥有它们。P1参考选accepted002，不是中间accepted001。

已有PROBE1[原封证据包](../lf_circle_tip_probe_001/execution_evidence.zip)及[原成员清单](../lf_circle_tip_probe_001/EVIDENCE_MANIFEST.json)包含其当时最小父源和新probe科学档；本次没有解压、复制或核它们的payload。普通旧probe完整result仍链接既有[原件](../lf_circle_tip_probe_001/run_001/science/result.json)，本次不另复制大文件；source_context仅保存必要普通描述与旧失败摘录，未改原文件内容或旧状态。

SHA与stat分别标注：本轮对普通JSON／源码实际核字节，NPZ／字段／旧ZIP身份均只从原普通记录引用并stat。准备PASS不等于旧科学payload、四mask、selected split或P0 fresh已经重新验证。以后执行必须通过原准入；旧controller源码差异保留，两kernel硬门与fresh首检不变。

其他机器若需恢复科学包／迁移路径，应在新准备／执行范围显式列出解压／复制／读计数和资源，核原包身份后保内部相对树；当前候选卡只覆盖本机已存在树，不暗含这些额外读取。封存记录中的绝对D路径是历史身份，不应改写旧档以掩盖路径迁移。

当前生产入口`hf_repo/src/hf_eval/native_guided_force.py`，原固定／probe入口保持，当前57份.py身份见author/PRODUCTION_IDENTITY.json；main基线293c542557c0abe59e1321713e9c3e251eeca465。origin固定`https://github.com/dudaxing/Compliant-TO-TMC.git`，后续开发在main。未来卡获批后冻结的是当时发布的main，而非强制回退本基线。

本轮发布恢复核对只验证同机`D:/hf-restore-20260930`与main的变化文件字节／索引／清单，不是异机数值复算或环境证明。控制图是新绘的纯示意，不是新结果；旧动画／PNG不重开，未来科学路径／显示须另行批准。
''')
print(json.dumps(dict(status='ordinary_docs_prepared',production_files=57,scientific_payload_reads=0,HF_mechanics_calls=0)))
