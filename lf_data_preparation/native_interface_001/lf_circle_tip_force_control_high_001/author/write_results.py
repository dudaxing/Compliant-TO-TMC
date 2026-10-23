"""Write actual HIGH1 records from the closed ordinary summary; no new science."""
import json
from pathlib import Path

A=Path(__file__).resolve().parent
BASE=Path('D:/hfh1_001')
d=json.loads((A/'EXECUTION_RESULT.json').read_bytes())
assert d['scientific_window_closed'] and d['status']=='PASS'
f=d['force_summary']; rows=f['scalar_rows']; end=rows[-1]; c=d['comparison']
errors=c['endpoint_comparison']['errors']; seal=d['seal']
geometry=d['geometry_metrics']['rows']; hu=end['force_on_body_N']['regularization'][0]
total=end['force_on_body_N']['total'][0]; hu_share=abs(hu/total)*100
def number(value): return format(value,'.17g')
def write(name,content):
    assert not (A/name).exists()
    (A/name).write_bytes(content.strip().encode('utf-8')+b'\n')
table='\n'.join('|'+str(i)+'|'+number(r['P_target_half_N'])+'|'+number(r['body_q_mm'])+'|'+number(r['R_input_N'])+'|'+str(r['newton_checks'])+'|' for i,r in enumerate(rows))
gate_table='\n'.join('|'+label+'|'+number(value)+'|'+bound+'|' for label,value,bound in (
    ('ρF',max(r['relative_residual'] for r in rows),'≤1e−9'),
    ('ρP',max(r['relative_generalized_force_residual'] for r in rows),'≤1e−9'),
    ('mean绝对残差/mm',max(r['constraint_residual'] for r in rows),'≤1.0600000000000001e−10 mm'),
    ('relative global balance',max(r['relative_global_force_balance'] for r in rows),'≤1e−6'),
    ('最小J',min(r['minimum_J'] for r in rows),'>0'),
    ('rigid/zero误差/mm',max(r['max_abs_prescribed_error_mm'] for r in rows),'≤8e−11 mm')))
write('RESULTS.md', f'''
# L-CTIPFHIGH1：高输入1.06 mm两载荷力控交叉结果

2026-10-23。**PASS，唯一执行窗口已关闭。** 机构平均输入保持1.06 mm，只给绝对半模型P0→P1、独立求工件有符号q和机构R；正式r9/mechanical/chunk256实际两态均通过原门及预先固定的端点工程比较。五张PNG各一次检查通过，2帧实际GIF已生成；四层SUP2清理及一次原字节封存通过。57份生产源码不改，新HP/测试/外部重试/安装均0。

## 整体目标、已实现能力与本次作用

整体目标是让独立HF读取LF夹持器几何，逐步实现大变形／第三介质接触分析、可审查的反力／工件力、加载／卸载和后续承载研究。原固定工件前向及续算、选定态参考、图像／接口关联、规定工件q探针已经具备，历史范围见[当前状态](../../../docs/CURRENT_STATUS.md)。[低输入.50 mm正式力控](../lf_circle_tip_force_control_real_001/RESULTS.md)又验证了给P→求未知q→对照给q结果的闭环。

本轮把这条功能推进到已有较强闭合、很小J的1.06 mm工况。复用已安装API和原力核，不新增生产层；研究包装只适配合法高输入父、实际3态参考的0/2配对及高输入显示标签／坐标近景。**参考q=.025 mm未作为力控输入、初值或夹限，也没有从旧probe终态热启动。** 同定义交叉通过说明正式高输入任务的控制方程、未知q/R及来源迁移可用，不能据此自动取得物理承载资格。[独立结果物理复核](author/RESULTS_PHYSICS_REVIEW.md)12/12项通过。

## 原任务与实际解

固定父为`D:/hpr1_001/parent_001/result.json`完整13目标load_only末峰accepted12/original12；原signed R=.19522304147728387 N和split迁移。保持α2.5e−7、γ1e−6、r9 mm／圆心(80,40) mm／right92 mm／Lr80 mm、E1 MPa／ν.3／plane strain／t20 mm／h.5 mm、14720单元／29970DOF、原510工件单元／565节点及端口／支撑；工件uy=0、转角0，成员不重mask。

|原目标索引|给定P_half/N|求得q/mm|机构R_input/N|Newton base checks|
|---|---:|---:|---:|---:|
{table}

本次2原请求／2实际接受态、0内部二分、0failed_attempts；5个base checks、3个line-search trials，1次solver，8F/8完成、5T/5完成，HP0、save-time F/T0。fresh P0首次检查直接通过，q0、原lift/fluctuation及signed R逐位保持，没有predictor、投影或Newton修复锚点；P1使用原guided_reduced_tangent。父的port_projection只作历史metadata，新clock3600秒按卡独立覆盖。

原固定父split_displacement控制器SHA与当前版本不同，force/tangent两kernel匹配；差异及原SHA保留于[原准备来源审阅](../lf_circle_tip_force_control_high_preparation_001/SOURCE_BINDING.md)。这次实际准入和fresh检查已完成，仍不能将该局部结果解释为两个控制器所有行为等价。

## 适用原门与端点比较

|项|两态最不利实际值|原界|
|---|---:|---|
{gate_table}

P1的g=Q_half−P_half={number(end['generalized_force_residual_half_N'])} N，SP={number(end['generalized_force_scale_half_N'])} N，g界={number(end['generalized_force_bound_half_N'])} N。高输入Ffloor=2.12e−7 N、mean公式界1.0600000000000001e−10 mm保持，free与body合力尺度独立。

|P1对原规定q=.025 mm参考|实际绝对差|启动前冻结界|结果|
|---|---:|---:|---|
|未知q|{number(errors['q_abs_error_mm'])} mm|1e−6 mm|PASS|
|全29970DOF物理位移max差|{number(errors['physical_displacement_max_error_mm'])} mm|1e−6 mm|PASS|
|机构R|{number(errors['R_abs_error_N'])} N|{number(errors['R_bound_N'])} N|PASS|

全场差逐DOF用四split项fsum，最大差在DOF{errors['physical_max_error_dof']}，不用显示位置相减。锚点硬身份和端点工程界分别核查，端点不要求逐位相同；工程界未按实际差收紧。详见[comparison原值/门](comparison.json)与[轻摘要](result_summary.json)。这些是功能工程比较，不是严格误差上界、完整路径HP或唯一稳定分支证明。

## 原位移参考困难完整保留

原PROBE1请求q=[0,.025]，实际接受[0,.0125,.025]；第一次直接+.025出现invalid_J、逐位回滚，内部二分后才接受.0125/.025。原28次F中27完成、15T均完成；旧终点minJ=.0004166085295994876。旧失败、中间态和计数仍在comparison/reference_history及source_binding中，图中.0125为HISTORY ONLY/unpaired。

本次力控顺利得到2态且未二分，是这次控制路径的实际表现，不改写原史。控制量、预测器及尝试数不同，不由单次总时间或8F/5T推断普适速度提升，也不把旧内部点配成新N中间态。

## 力、尖端与介质的物理含义

P为固定空间+x的**绝对半模型合外载N，已含20mm厚度**，不能再乘厚度或用ΔP替代P0。Q_half=Σbody f_int,x，ON-body Fx=−Q_half；完整镜像装配轴向外载仅2P，q不倍增。R为机构均值端口乘子，独立于工件外载。

末态ON-body total=[{number(end['force_on_body_N']['total'][0])}, {number(end['force_on_body_N']['total'][1])}] N；material=[{number(end['force_on_body_N']['material'][0])}, {number(end['force_on_body_N']['material'][1])}] N；Hu=[{number(end['force_on_body_N']['regularization'][0])}, {number(end['force_on_body_N']['regularization'][1])}] N。轴向Hu约占{hu_share:.4f}%，只是总弱力分量比例，不是Hu压力比例或误差分摊。显式P仅入账一次、旧body-x处方驱动力移除，body-y导向与背景重叠去重；Fy导向反力及原global账本保持。

tip11260到原物理raster-body边段的无符号距离由{number(geometry[0]['unsigned_tip_boundary_distance_mm'])}变为{number(geometry[-1]['unsigned_tip_boundary_distance_mm'])} mm。坐标局部放大窗显示约8.67微米的小间距，**变形仍实际×1**；这不是解析圆的有符号接触间隙或新接触门。右480格均核为原非工件介质，实际自由右界随运动响应。当前仅显示右介质几何和全域保存的minJ/maxHu标量，没有读取局部场数组或重新定位极值。

新末态minJ={number(end['minimum_J'])}，max|Hu|={number(end['max_abs_Hu_per_mm'])} 1/mm。很小的J、较大Hu贡献及微小几何距离仍需独立判断；本次不能把P1、ΔP、material或Fy称为纯接触抗拔力、最大容量、摩擦或自由工件释放。independent_HP/effective_grasp/release/HF四资格flags均false，原结果及历史资格保持。

## 可视化与一次检查

[人工检查页](inspection.html)关联全部新媒体：

|图|用途与可见性限制|
|---|---|
|[01实际×1](view/01_actual_geometry.png)|全机构／工件与尖端，密网格和.025 mm小平移在全域比例下有限。|
|[02 P–q及三误差](view/02_P_q_cross_check.png)|两新态对旧0/2原请求，旧.0125只历史点；微小误差靠精确标注及JSON读取。|
|[03力与R/账本](view/03_force_components_and_R.png)|有符号ON-body总/material/Hu、独立R和互斥支撑；Fy远大于Fx，共享尺度下Fx柱较小。|
|[04尖端/右介质/global J-Hu](view/04_tip_right_geometry_global_J_Hu.png)|同图坐标zoom ±.08 mm使小间距可见；inset标题位于彩色网格背景上但可读，未重绘。|
|[05全部收敛](view/05_convergence_and_gates.png)|5个base checks、3个trial及各原门，原旧invalid_J历史与本次0失败分开。|
|[实际态动画](view/actual_force_states.gif)|2次成功grab_frame、2帧，无插值／物理时间含义；帧数依据writer，不重开GIF解码查帧。|

五PNG各一次像素检查通过并保可见性限制，[root QA](execution/root_qa.json)为最终事实。renderer的pending字样保原QA前历史；没有补绘、重试或第二次像素检查。GIF原字节按renderer/封存/发布合同散列复制，不能将“无解码”说成“从未读取新GIF原字节”。

## 资源、读取与封存

science worker含导入／准入／保存实际{d['science_receipt']['elapsed_worker_seconds']:.6f}秒；科学进程加清理监督398.929825秒，比较监督1.591829秒，viewer监督7.256852秒。helper含QA和一次封存{seal['elapsed_helper_seconds']:.6f}秒，outer {seal['elapsed_outer_seconds']:.6f}秒，均在原4800/4860秒窗；controller3600、science3900、compare60、shared display-QA600保持。四层SUP2 normal_exit/0、同实例全部成员覆盖／ActiveProcesses0／句柄释放通过；top采样峰839888896B约801MiB，是采样值，不是连续峰值或16核实际利用率证明。采样64GiB/四库cap16/CPU、viewer8GiB均未改。

API实际监测3条旧NPZ路径、5次read-capable open事件，均在白名单；opaque model只hash，geometry四mask与selected012两split共6字段来自成功冻结控制流，**不是动态字段hook实测**。独立比较另实际4档8字段，合计7路径、6解码档／14字段；旧fields/force/tangent/matrix缓存不读。viewer只读4份普通JSON，局部科学场读取0；本阶段记录只解析普通输出及原字节身份，无科学补算。

一次封存{seal['members']}成员、{seal['archive']['bytes']}B，SHA256=`{seal['archive']['sha256']}`，在原窗口内完成。见[原包](execution/execution_evidence.zip)、[成员清单](execution/EVIDENCE_MANIFEST.json)、[封存回执](execution/seal_receipt.json)。原高输入父／probe科学包不重复复制或重封。当前闭窗后不再新增F/T、HP、缓存解码、图像或像素检查。

## 使用、恢复与下一步

[USAGE](USAGE.md)已按闭窗实际记录更新功能状态与本次调用，完整结论以本页／result_summary为准。原卡pending标题、授权与冻结的numerical_launched=false、renderer pending均是原准备／执行时点，不覆盖当前实际PASS；actual授权与最终回执另存。

[恢复说明](RECOVERY.md)列新原包、旧父依赖、普通源和路径迁移边界。下一步建议先[准备最小力控保存态续载功能](NEXT_STEPS.md)，让本次非零q/P成功末态可被下一次同定义载荷任务复用；不立即加新P、不重复完整父加载、不把本轮成功当作容量证明。
''')
write('NEXT_STEPS.md', '''
# 下一步：准备最小力控保存态续载功能

2026-10-23。L-CTIPFHIGH1已PASS并关闭。低输入.50与高输入1.06正式模型均完成“给P→未知q→原位移参考”的局部功能闭环；下一步应补齐可继续使用这些成功保存态的入口。

当前evaluate_native_guided_force只准入成功fixed-rigid/load_only父，低层以q0/lift0初始化；**不能把本次非零q末态直接冒接成固定父**。若每追加一个载荷都从原q0重跑整段，会重复计算，也不利于保留连续状态。因此近期优先准备显式force-result continuation能力，而不是继续堆同类账本或把HP核对当作续载功能本身。

1. 核定本次成功P1末态为候选父：原P1、绝对q=0.025000000126731543 mm、原signed R及两split/状态声明身份，完整force任务和原fixed父谱系均保留。只先读普通描述与必要stat；不在闭卡窗口解码新缓存或执行。
2. 明确续载数学合同：机构mean仍1.06，源P1是非零绝对预载；续算锚点必须原split/R/q/P fresh检查1原样通过，不投影、Newton修复、平移q原点或重复加q。尤其须追溯当前保存lift如何编码刚体q，避免把缓存lift和新q lift叠加两次。原body成员、边界/端口、g及独立力尺度保持。
3. 采用显式新接口/任务语义，成功完整同kind只追加严格增加的绝对P；默认固定父入口保持。源成功、末个原目标、schema/物理/非clock设置和来源身份须清楚，invalid source走既有typed错误，不用庞大fallback或通用防御框架。
4. 准备有限小模型验证：从非零q力控成功态续载，fresh锚点split/R/q/P硬身份；新末态与同定义一次完整P路径对照，兼容原固定父/位移probe与失败partial来源。测试规模、安装文件数、资源和首错规则在下一张具体卡核定；当前未新增测试、实现、安装或真实计算。
5. 通过小模型再安排一次真实最小续载。P2只取小的绝对载荷增量，候选可考虑P1+(P1−P0)/4，数值/最小N步长/预算须在下一准备中正式冻结；q仍未知，不设预期答案。原小J及Hu约72.58%提示应谨慎控制行程，保原门和所有实际内部尝试；不扩大成容量扫描、force卸载/循环、自由转动或新HP。

这一步的功能收益是让已验证真实保存态可用于下一次载荷任务；它不会自动解决Hu的物理归因、纯接触压力、最大承载、摩擦、释放或稳定性。本轮只记录下一计划，没有启动这些新工作或改变已有资格。
''')
write('RECOVERY.md', f'''
# L-CTIPFHIGH1：恢复与审查

此交付记录高输入mean1.06 mm、r9/(80,40)/right92/Lr80、α2.5e−7两载荷力控的实际PASS；当前科学窗口已关闭。先看[RESULTS](RESULTS.md)、[人工图页](inspection.html)、[轻摘要](result_summary.json)、[comparison](comparison.json)、[接口用法](USAGE.md)及[下一步](NEXT_STEPS.md)，无需运行Python或解压科学档即可审查结论。

- 本轮唯一原包：`execution/execution_evidence.zip`，{seal['members']}成员，{seal['archive']['bytes']}B，SHA256 `{seal['archive']['sha256']}`；成员原字节身份见`execution/EVIDENCE_MANIFEST.json`，封存时间/窗口见`execution/seal_receipt.json`。完整新force/result和两态state/fields缓存在这个原包内，发布只复制原包，不再重封科学档。
- `view/`是已生成五PNG/GIF与几何/renderer回执原字节副本；`comparison.json`、`execution/`保存普通日志、四层SUP2及root一次QA。没有再次解码图像/GIF或科学NPZ来核这些副本。
- `wrapper/`为实际执行的六份Python（含未改SUP2）；`protocol.json`绑定75份当时文件，57份生产源码身份不变，63份Python AST静核。`author/`保实际授权、冻结、四份静审、eligibility、闭窗和物理审阅。旧pending/false是当时事实，不修改其原字节；本页/实际终态回执为当前事实。
- 旧科学依赖不在新包重复。已发表[高输入准备](../lf_circle_tip_force_control_high_preparation_001/RECOVERY.md)与[来源声明](../lf_circle_tip_force_control_high_preparation_001/SOURCE_BINDING.json)指向原`D:/hpr1_001/parent_001`最小树：完整13目标普通描述、model/source_geometry、selected012 split；参考为probe的accepted000/002，原中间001仍保普通历史。原科学档由[PROBE1原包](../lf_circle_tip_probe_001/execution_evidence.zip)和[旧清单](../lf_circle_tip_probe_001/EVIDENCE_MANIFEST.json)提供，本次没有为发布解压旧包或复制旧科学数据。

`approved_card.md`保留获批前执行卡的原字节；其中`PREPARATION.md`、`SOURCE_BINDING.json`、`COMPARISON_GATES.json`三个相对链接应在[原准备目录中的执行卡](../lf_circle_tip_force_control_high_preparation_001/L-CTIPFHIGH1_CARD.md)内打开。它们属于历史准备语境，不能按本结果目录解析；尤其原大写`SOURCE_BINDING.json`与本目录小写`source_binding.json`不是可移植的同名别名。当前结果请沿本页、RESULTS和人工页链接审查，历史卡不作改写。

换机需要新读取/复算时，应先按旧/新清单核包身份，在隔离位置按原相对结构恢复所需数据，然后在新任务中显式绑定新路径、复制/解压计数及资源。现有绝对D路径是历史来源，不能为伪造可运行性而改写旧结果或协议。只看普通报告无需解压。当前force结果尚不能作为现有API的合法父继续载荷；force续载是下一步待准备能力。

实际环境为Windows、Python3.13.6、NumPy2.4.6、SciPy1.17.1、JAX/JAXlib0.11.0、matplotlib3.10.9、psutil7.2.2、Pillow12.3.0，本次未升级依赖。生产源在仓库hf_repo/src/hf_eval；origin保持https://github.com/dudaxing/Compliant-TO-TMC.git，后续开发在main。

本次发布恢复仅同机`D:/hf-restore-20260930`异目录核main远端HEAD、工作树干净、清单/索引集合及变化文件字节相等；不等于异机环境验证、科学包解压、fresh复算或新HP。已关闭的launcher含唯一启动标记，不能删输出或复制launcher重新开启旧卡。
''')
print(json.dumps(dict(stage='L-CTIPFHIGH1',status='actual_reports_written',source='closed ordinary EXECUTION_RESULT',new_science=0,new_images=0)))
