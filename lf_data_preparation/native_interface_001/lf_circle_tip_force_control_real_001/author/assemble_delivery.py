"""Publish existing L-CTIPFREAL1 bytes and ordinary records; no scientific work."""
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import shutil

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).resolve().parent
BASE = Path('D:/hfr1_001')
REL = 'lf_data_preparation/native_interface_001/lf_circle_tip_force_control_real_001'
DEST = ROOT / REL
assert not DEST.exists(), 'Do not replace an existing delivery'
summary = json.loads((AUTHOR / 'EXECUTION_RESULT.json').read_bytes())
assert summary['status'] == 'PASS' and summary['scientific_window_closed']
assert summary['production_sources_unchanged'] == 57
assert summary['seal']['archive']['sha256'] == '7452459bd88751087bdc0040754226eafedae3d42159fd3f1273b5d21cc81158'

def copy(source, relative):
    target = DEST / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    assert source.read_bytes() == target.read_bytes()

def write(relative, content):
    target = DEST / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content.strip().encode('utf-8') + b'\n')

DEST.mkdir(parents=True)
for name in ('approved_card.md', 'authorization.json', 'protocol.json', 'source_binding.json', 'observer_binding.json'):
    copy(BASE / name, name)
copy(AUTHOR / 'EXECUTION_RESULT.json', 'result_summary.json')
copy(AUTHOR / 'FUNCTION_STATUS_AND_USAGE.md', 'USAGE.md')
copy(BASE / 'run_001/comparison.json', 'comparison.json')
for name in ('science_freal1.py', 'compare_freal1.py', 'view_freal1.py', 'helper_freal1.py', 'launch_freal1.py', 'windows_owned_process_sup2.py'):
    copy(BASE / name, 'wrapper/' + name)
for name in ('execution_evidence.zip', 'EVIDENCE_MANIFEST.json', 'seal_receipt.json', 'top_start.json', 'top_supervision.json', 'helper_start.json', 'helper_receipt.json', 'root_qa.json', 'helper.log', 'helper.instances.ndjson'):
    copy(BASE / name, 'execution/' + name)
for source in sorted((BASE / 'run_001').iterdir()):
    if source.is_file() and source.name != 'comparison.json':
        assert source.suffix in ('.json', '.log', '.ndjson')
        copy(source, 'execution/run_001/' + source.name)
for source in sorted((BASE / 'run_001/view').iterdir()):
    assert source.is_file() and source.suffix in ('.png', '.gif', '.json')
    copy(source, 'view/' + source.name)
for name in ('CANDIDATE_FREEZE.json', 'EXECUTION_ELIGIBILITY.json', 'LIVE_HANDOFF.json',
             'COMPARATOR_IMPLEMENTATION.md', 'COMPARATOR_STATIC_REVIEW.json', 'COMPARATOR_STATIC_REVIEW.md',
             'PRELAUNCH_PHYSICS_CHECK.json', 'PRELAUNCH_PHYSICS_CHECK.md',
             'VIEWER_IMPLEMENTATION.md', 'VIEWER_STATIC_REVIEW.json', 'VIEWER_STATIC_REVIEW.md',
             'WORKER_WRAPPER_STATIC_REVIEW.json', 'WORKER_WRAPPER_STATIC_REVIEW.md', 'WRAPPER_IMPLEMENTATION.md',
             'RESULTS_PHYSICS_REVIEW.md', 'RESULTS_PHYSICS_REVIEW.json',
             'freeze_freal1.py', 'check_eligibility_freal1.py', 'close_execution.py', 'publication.py', 'assemble_delivery.py'):
    copy(AUTHOR / name, 'author/' + name)

write('RESULTS.md', r'''
# L-CTIPFREAL1：正式r9导向两载荷力控交叉结果

2026-10-23。**PASS，唯一执行窗口已关闭。** 用户已明确批准本卡。原封保存的[执行卡](approved_card.md)仍保留准备时“尚未获批”字样；这是历史原字节，实际授权见[本轮授权](authorization.json)。本轮从小模型验证推进到14720单元／29970DOF正式r9模型：机构平均输入保持0.50 mm，只给两个正的绝对半模型外载P0→P1，工件刚体轴向q由求解确定。原物理、原验收门及57份生产源码保持。

## 目标、已有能力与本次作用

项目目标是形成独立于LF设计代码的HF第三介质接触分析器，接收LF夹持器几何，计算大变形、接触相关响应、加载／卸载和可追溯的力；以数值核查和实际变形图支持设计比较及后续开发。功能必须逐步落地，数值成功与物理资格分别记录。

此前已完成LF输入准备、多设计前向加载／卸载、保存态延伸、选定态HP80/120参考、保存态接口／图像关联、两α对照和单侧力口径；这些历史范围见[当前状态](../../../docs/CURRENT_STATUS.md)。近期又完成固定机构输入下的规定工件q探针，以及[17项小模型力控验证和两个新模块安装](../lf_circle_tip_force_control_001/RESULTS.md)。

本轮使用LOW1从零[0,.25,.50] mm完整固定父最后峰值index2，给P求q，再与已有给q求P参考交叉，检验正式网格、chunk256切线、未知q/R、来源迁移和外载账本是否一致。**没有把参考q=.025 mm输入力控，也未从probe终态热启动。** 没有重做父加载、probe、HP、测试或修改生产源码。

## 物理任务和实际解

r9 mm、圆心(80,40) mm、right92 mm、Lr80 mm、α=2.5e−7、γ=1e−6、E=1MPa／ν=.3、plane strain、厚20mm、h=.5mm、原510工件单元／565节点及原端口／边界均保持。full29970DOF，free28682，reduced(w,q,R)28684。导向限制工件uy=0、转角0；q为有符号未知量，未裁剪到预期答案。

|原请求|给定P_half／N|求得q／mm|机构R_input／N|Newton base checks|
|---|---:|---:|---:|---:|
|P0非零预载|3.686421133658022e−5|0|0.08589635225389337|1|
|P1|4.3272306948756724e−5|0.024999999999923774|0.08589811003453524|3|

2个请求、2个接受态，无内部二分、无失败尝试；1次solver、6次F／4次T均完成，2次line-search trial。P0由原合法父q0的预载确定，本次fresh检查1即原样通过，两split与signed R逐位保持。P1是绝对载荷，ΔP不是P1，N最小二分步长4.0050597576103156e−7与旧mm步长分别保留。

## 原门及参考交叉

|适用生产门|两态最不利实际值|原界|
|---|---:|---:|
|free ρF|1.3004823600170763e−12|≤1e−9|
|独立body ρP|9.395750847384523e−16|≤1e−9|
|mean绝对残差|6.938893903907228e−18 mm|≤5e−11 mm|
|relative global balance|6.034159322635907e−16|≤1e−6|
|最小J|0.5154001178738727|>0|
|rigid／zero误差|0 mm|≤8e−11 mm|

P1的g=Q_half−P_half=−4.0657581468206416e−20 N，SP=4.3272306948756724e−5 N，|g|界4.327230694875673e−14 N。free与body力尺度独立，没有替换生产门。

|P1对原规定q=.025终点|实际绝对差|启动前冻结工程界|结果|
|---|---:|---:|---|
|q|7.622721898137286e−14 mm|1e−6 mm|PASS|
|全29970DOF物理位移max差|7.676498325892567e−14 mm|1e−6 mm|PASS|
|R_input|1.3877787807814457e−17 N|8.589811003453524e−9 N|PASS|

全场比较逐DOF对四个binary64 split项用fsum求差，未用显示坐标相减；最大差DOF25082。fresh锚点身份与端点工程误差分开验收；没有因实际差很小而收紧未来门。详细原值／身份／门见[comparison](comparison.json)，轻量全记录见[result_summary](result_summary.json)。这不是严格误差界、唯一稳定分支或全路径独立参考证明。

## 从力与几何能判断什么

P是固定空间+x的**半模型合外载N，已含20mm厚度**，不再乘厚度。Q_half=sum_body f_int,x，ON-body Fx=−Q_half。镜像完整装配轴向外载可记2P_half，q不倍增；R_input是机构平均端口有符号乘子，不能当工件外载。

P1的ON-body力(N)：total=[−4.3272306948756683e−5, +3.711449563209588e−4]，material=[−5.934019104250851e−6, +1.0249499809837568e−4]，Hu=[−3.733828784450584e−5, +2.6864995822258313e−4]。轴向Hu约占total的86.2868%；这是总弱力分量的描述，不是压力比例。显式P仅入账一次，旧body-x处方驱动力不再计入；body-y导向与background重叠去重，原global账本保持，分组末位重求和差仅描述。

实际×1几何的tip-node到原阶梯工件边段**无符号距离**从0.5190339177997849变为0.5190421063444752 mm。它不是解析圆的有符号接触间隙或新接触门。右侧固定480格均核为原非工件介质，未重选成员；本轮未读局部J/Hu场，图中只画既存全域极值标量和真实几何。

因此，本次证明正式模型的导向总力控制及同定义位移↔力闭环。较大间距与Hu占主导，仍不能把P1或ΔP称为纯接触抗拔力、最大承载力。独立HP／有效夹持／释放／HF资格flags仍false；压力、摩擦、自由工件y／转动、承载极限及稳定性尚未建立。独立[结果物理复核](author/RESULTS_PHYSICS_REVIEW.md)保留这些限制。

## 实际可视化与人工检查

[人工总览页](inspection.html)包含5PNG及2帧实际GIF，便于逐图检查：

|图|内容与观察边界|
|---|---|
|[01](view/01_actual_geometry.png)|原网格实际×1变形、工件运动；小q和密网格在全图中不显著。|
|[02](view/02_P_q_cross_check.png)|P–q与给q参考重合，三项误差和冻结界；精确值依标注／JSON。|
|[03](view/03_force_components_and_R.png)|有符号ON-body total／material／Hu、单列R和去重外载账本。|
|[04](view/04_tip_right_geometry_global_J_Hu.png)|尖端近景、右侧介质实际几何、unsigned距离和全域minJ／maxHu。距离曲线自动使用数值offset，图例给直接末值。|
|[05](view/05_convergence_and_gates.png)|全部4个Newton base checks、2个trial及独立残差／mean／global／刚体门。|
|[GIF](view/actual_force_states.gif)|每个实际接受态一帧，共2帧；无插值，不代表物理时间。|

五张PNG各一次像素检查均通过，见[实际root QA](execution/root_qa.json)；未修图重跑。GIF只按writer两次grab_frame记帧，未二次解码检查。原renderer的pending字符串是QA前历史状态，最终QA和helper已PASS。

## 范围、资源与记录完整性

唯一启动从2026-10-23 09:50 UTC附近开始。worker实际311.2029秒（含导入、准入、保存；监督含创建清理313.5384秒），比较监督2.8655秒，viewer监督5.9841秒；显示及root QA共享阶段80.1646秒。helper397.9866秒，outer含一次封存398.6823秒，均在原2700／2760秒窗口。controller1800、science1900、comparison60、display共享600保持；采样64GiB／四库线程cap16／CPU，viewer8GiB。top采样进程树峰843264000B，约804MiB；是采样值，不是连续峰值或16核实际利用率证明。

top／science／comparison／viewer四份SUP2均normal_exit／0；同实例终止信号、全部成员覆盖、ActiveProcesses=0及句柄释放证明均通过。0外部重试、0修复重跑、0新HP、0测试、0生产修改／安装，窗口关闭后没有科学补算或再次绘图。

API实际只读3条旧NPZ路径、5次open事件；opaque model只核整档身份，geometry四mask和父selected split两字段的**6字段计数来自成功冻结控制流，并非动态字段hook实测**。比较另实际读4个state档／8字段；合计7路径、6解码档／14字段，旧力／切线／矩阵缓存未读。viewer只读4份普通JSON；后续记录仅读普通元数据和原字节，不解码科学缓存。详见[science receipt](execution/run_001/science_receipt.json)及[协议](protocol.json)。

一次原始封存59成员、13984762B，SHA256=`7452459bd88751087bdc0040754226eafedae3d42159fd3f1273b5d21cc81158`，见[已封原包](execution/execution_evidence.zip)、[逐成员清单](execution/EVIDENCE_MANIFEST.json)、[seal回执](execution/seal_receipt.json)。封存在原窗口完成，发布只复制原包原字节；没有窗口外补封科学档。

## 使用、恢复与下一步

现有固定／probe／force三种接口和本次原调用见[USAGE](USAGE.md)。force结果为独立schema，尚不支持其保存态续算／卸载或旧native_response自动关联。恢复所需资料、父依赖和路径迁移限制见[RECOVERY](RECOVERY.md)，逐文件发布身份见[DELIVERY_MANIFEST](DELIVERY_MANIFEST.json)。预启动false计数和旧路径原封保留，当前PASS以实际回执为准。

下一步先[准备高输入1.06 mm的同定义两载荷交叉](NEXT_STEPS.md)，优先检查功能能否进入已有较强夹持工况。它的旧probe曾直接大步invalid_J后内部二分，终点minJ约4.17e−4；不能以这次低输入311秒外推保证，也不能现在追加计算。当前只完成本卡，不把项目整体目标标成完成。
''')

write('NEXT_STEPS.md', r'''
# 下一步：先准备高输入1.06 mm的同定义力控交叉

2026-10-23。L-CTIPFREAL1已PASS并关闭；以下为根据结果提出的下一阶段计划，**尚未绑定新的执行包或启动**。

低输入.50 mm正式r9的P→未知q→原位移参考闭环已经通过，继续堆同一低输入端点的检查收益有限。下一步应保持已安装的力控功能及物理定义，在已有mean1.06 mm较强闭合状态做同定义交叉；先完成准备、来源／门／资源核定，再另行安排真实计算。

1. 从已发表高输入PROBE1的普通JSON、来源声明SHA及必要stat核定合法固定父：完整成功load_only最后原峰accepted12/original12、q0、α2.5e−7。不读取旧科学payload、解压旧包、重跑父或将低输入力控末态抬升到1.06。必须明确父／reference／必要科学依赖的可恢复关系和原字节身份。
2. 核定同定义绝对half N两个载荷。旧普通说明的候选P0=2.399800950672949e−4 N、P1=2.561572865437846e−4 N，均已含t20；最终以新准备绑定原记录为准。P0须fresh检查1、split/R原样保持；q依然未知，不传.025或probe终态初值。候选Nmin=ΔP/16≈1.011074467280606e−6 N，maxdepth4；内部N二分态不能假配成旧q=.0125态或用插值冒充实测。
3. 保持r9/(80,40)/right92/Lr80、α、γ、材料、厚度、原节点／端口／支撑、mechanical/chunk256及原生产门。候选端点q／全29970DOF位移各≤1e−6 mm，R≤max(1e−10 N,1e−7|R_ref|)，按高输入来源重冻结；这些工程门不因本次小差而收紧。只对实际请求P1端点与相同定义q参考比较，保留全部实际尝试。
4. 高输入旧probe曾第一次直接q=.025 invalid_J，再由内部二分接受.0125/.025；终点minJ约4.1660853e−4、旧science监督约1172.74秒。保留该困难历史。准备阶段可审controller3600、science含导入／准入／保存／清理3900、comparison60、display+QA600、helper4800／outer4860秒、64GiB／线程cap16的候选额度；须独立审阅总预算和封存余量后在新卡明确，不能直接续用旧窗口。
5. 候选实际输出沿用5PNG／实际N帧GIF：实际×1几何、P–q参考、signed total/material/Hu与R／外载账本、尖端及右介质几何／全域J-Hu、全部残差／回溯收敛。科学／工程比较成功后才显示；按新卡规定唯一启动、首个终端错误停，保partial，不外部重试或隐去内部失败。

高输入两点即使通过，也只支持该导向总力任务；不能自动得到纯接触抗拔、容量、摩擦、释放或稳定性资格。若未通过，应按typed失败与实际部分态判断是功能错误、分支／步长困难还是物理可压缩介质／Hu问题，再准备有针对性的下一步；不静默改门、改α或放大行程。暂不新增force保存态延伸／循环，先完成已有功能在目标物理工况的核查。

参考：[本轮结果](RESULTS.md)、[独立物理判断](author/RESULTS_PHYSICS_REVIEW.md)、[原高输入probe普通报告](../lf_circle_tip_probe_001/RESULTS.md)。本计划没有新增数值、数组读取、图像或资格。
''')

write('RECOVERY.md', r'''
# L-CTIPFREAL1：恢复与审查入口

本交付记录正式r9／mean.50 mm／P0→P1力控任务的实际PASS，整体项目与历史限制见[结果说明](RESULTS.md)和仓库[当前状态](../../../docs/CURRENT_STATUS.md)。不用原工作目录也可先看[人工页](inspection.html)、[轻摘要](result_summary.json)、[比较](comparison.json)、[接口用法](USAGE.md)及[下一步](NEXT_STEPS.md)。

|资料|位置与用途|
|---|---|
|本轮实际数值原件|`execution/execution_evidence.zip`：唯一窗口封存的59成员、13984762B原包，完整新force/result、两态split／field缓存、运行记录及原wrapper；不是发布时重封。|
|原包身份|`execution/EVIDENCE_MANIFEST.json`列59个原成员SHA；`execution/seal_receipt.json`给包SHA／封存时点／资源。解压前先核13984762B和SHA7452459b…cc81158。完整64位SHA以该JSON为准。|
|便于浏览的原字节副本|`view/`五PNG、两帧GIF、geometry_metrics／renderer receipt；`comparison.json`、`execution/`普通回执／日志／监督，与原包相应成员保持字节同一。发布没有再打开图像或科学缓存。|
|实际源代码|`wrapper/`六份执行源码，含未改SUP2；`protocol.json`绑定75份当时文件；`source_binding.json`、`observer_binding.json`保原来源／字段和固定观察ID。|
|授权与过程|`approved_card.md`保准备版原字节，实际用户批准见`authorization.json`；`author/`保存冻结、静审、闭卡及物理审阅。预启动false声明代表当时事实，不能误读为最终未执行。|
|已有父／参考科学依赖|本次直接只读`D:/hlo1_001/run_001/parent_fixed`与`probe_low`树。其已发布原始证据位于[LOW1交付目录](../lf_circle_tip_low_probe_001/RESULTS.md)的`execution_evidence.zip`及成员清单；本次原包有意不重复旧科学包。|

换机若只审查结果，不需要运行Python或解压科学档。若后续需要复算／延伸，需在新任务中核LOW1原包身份、选择性恢复完整父模型的source_geometry、model和selected accepted002 split，以及对照probe接受态，按源清单保留目录关系；再恢复本轮原包。原包中的科学结果路径与协议绝对D盘路径是**当时来源记录**，不是任意机器上开箱即运行的承诺。新位置应通过明确的新准备包重绑定，不能直接修改封存协议或覆盖旧结果。

Windows3.13.6环境中使用本机`.venv-handoff`，NumPy2.4.6／SciPy1.17.1／JAX-JAXlib0.11.0／matplotlib3.10.9／psutil7.2.2／Pillow12.3.0；生产代码位于仓库`hf_repo/src/hf_eval`，正式origin始终为`https://github.com/dudaxing/Compliant-TO-TMC.git`，后续开发在main。此清单是已使用环境记录，不是依赖升级建议。

旧wrapper含唯一启动和已存在目录的停止约束；本卡窗口已经关闭，**不要通过复制旧launcher或删除旧输出来重开**。后续新执行应使用新目录／来源绑定／资源窗口，保留历史PASS和失败。当前force API尚不支持以force结果为父续算或卸载，不能用固定父resume入口冒接新schema。

本次发布恢复检查仅为同一计算机的`D:/hf-restore-20260930`异目录：核main远端HEAD、工作树干净、Git索引／仓库清单一致及本轮变化文件原字节相等。它不等于已做异机环境验证、重新解压科学包、数值复算或新HP。原大包与旧科学payload在发布核对中不解码。
''')

images = [
    ('01_actual_geometry.png', '实际×1变形', '机构mean保持0.50 mm，工件q由力控求解；全图密网格及小q可见性有限。'),
    ('02_P_q_cross_check.png', 'P–q及三项交叉误差', '只给P，不输入参考q。参考点与新解重合，三项工程门预先冻结。'),
    ('03_force_components_and_R.png', '有符号力分量、输入R及外载账本', 'ON-body与P反号；total/material/Hu、机构R和导向／其他支撑分别显示。'),
    ('04_tip_right_geometry_global_J_Hu.png', '尖端、右侧介质及全域响应', '无符号tip到raster边界距离；right480原非工件格；J/Hu只是全域保存标量。'),
    ('05_convergence_and_gates.png', '全部收敛及验收门', '4个Newton base checks和2个trial；ρF、ρP、mean/global/rigid各保原门。'),
]
cards = '\n'.join('<figure><h2>' + escape(title) + '</h2><a href="view/' + name + '"><img loading="lazy" src="view/' + name + '" alt="' + escape(title) + '"></a><figcaption>' + escape(desc) + '</figcaption></figure>' for name, title, desc in images)
write('inspection.html', '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>L-CTIPFREAL1 · 正式r9力控交叉</title>
<style>body{font:16px/1.7 system-ui,sans-serif;max-width:1280px;margin:32px auto;padding:0 24px;color:#182b3b;background:#f5f7fa}h1{line-height:1.3}a{color:#075d94}header,section,figure{margin:20px 0;padding:24px;background:white;border:1px solid #d5dee8;border-radius:10px}img{display:block;max-width:100%;height:auto}table{border-collapse:collapse;width:100%;overflow-wrap:anywhere}th,td{border-bottom:1px solid #ddd;padding:8px;text-align:left}figcaption,.note{color:#465b6d}code{overflow-wrap:anywhere}</style>
<header><p>2026-10-23 · 已批准唯一执行 · PASS／窗口已关闭</p><h1>正式r9：给定外载P，独立求工件位移q</h1><p>机构mean=0.50 mm；α=2.5e−7／r9／(80,40)／right92／Lr80，14720单元／29970DOF。2个原请求均通过，无内部二分、无外部重试。57份生产源码保持。</p>
<table><tr><th>P_half / N</th><th>求得q / mm</th><th>R_input / N</th></tr><tr><td>3.686421133658022e−5</td><td>0</td><td>0.08589635225389337</td></tr><tr><td>4.3272306948756724e−5</td><td>0.024999999999923774</td><td>0.08589811003453524</td></tr></table>
<p>P1对原规定q=.025：q差7.62e−14 mm，全DOF最大差7.68e−14 mm，R差1.39e−17 N，均过预定门。</p><p class="note">P为已含t20的有符号半模型合外载，完整对称轴向外载2P，q不倍增。R是机构反力。Hu约占末态轴向总力86.29%，tip unsigned距离仍约.519 mm；本次是导向总弱力交叉，尚无纯接触承载／压力／释放／稳定性或新HP资格。</p>
<nav><a href="RESULTS.md">完整目标／过程／结果</a> · <a href="USAGE.md">接口与功能边界</a> · <a href="comparison.json">原值与比较门</a> · <a href="result_summary.json">轻摘要</a> · <a href="RECOVERY.md">恢复</a> · <a href="NEXT_STEPS.md">下一步计划</a> · <a href="execution/execution_evidence.zip">原始证据包</a></nav></header>
''' + cards + '''
<section><h2>两帧实际接受态动画</h2><img loading="lazy" src="view/actual_force_states.gif" alt="两个实际接受态的×1变形动画"><p class="note">每个实际态写一帧，无插值，无物理时间含义。帧数来自writer grab_frame记录；没有重开GIF解码查帧。五PNG的一次检查已通过，本页仅链接既存媒体，没有重绘。</p></section>
<section><h2>记录与下一步</h2><p>总outer398.682秒，四层SUP2正常退出／同实例清理通过，原窗口一次封存。0新HP／测试／生产修改，6F／4T均完成。下一步先准备mean1.06 mm高输入同定义两载荷交叉，保留其旧invalid_J／内部二分历史和近零J困难，不在已关闭窗口加算。</p><p><a href="execution/root_qa.json">原QA</a> · <a href="execution/seal_receipt.json">原封存</a> · <a href="execution/EVIDENCE_MANIFEST.json">成员SHA</a> · <a href="author/RESULTS_PHYSICS_REVIEW.md">独立物理复核</a> · <a href="approved_card.md">历史卡</a> · <a href="authorization.json">实际授权</a></p></section></html>''')

banner = ('> 2026-10-23 L-CTIPFREAL1 **正式r9导向两载荷力控交叉PASS**：机构mean保持.50 mm，给P0→P1、独立求q；P1得到0.024999999999923774 mm，全29970DOF对原位移参考最大差7.68e−14 mm，原门均通过。5PNG／2帧实际GIF、四层清理与一次原包封存完成，57生产源码保持；[实际结果与图页]({p}RESULTS.md)、[功能／用法]({p}USAGE.md)、[下一步：高输入交叉准备]({p}NEXT_STEPS.md)。尖端unsigned距离仍约.519 mm、轴向Hu约86.29%，不授纯接触承载或新HP资格。窗口已关闭，下方为历史状态。\r\n\r\n')
for relative, prefix in [('README.md', REL + '/'), ('docs/CURRENT_STATUS.md', '../' + REL + '/'), ('hf_repo/README.md', '../' + REL + '/')]:
    target = ROOT / relative
    old = target.read_bytes()
    assert b'L-CTIPFREAL1 **' not in old[:1000]
    target.write_bytes(banner.format(p=prefix).encode('utf-8') + old)

attributes = ROOT / '.gitattributes'
old = attributes.read_bytes()
entry = REL + '/wrapper/windows_owned_process_sup2.py whitespace=blank-at-eol,space-before-tab,cr-at-eol,-blank-at-eof\n'
assert entry.encode() not in old
attributes.write_bytes(old + ('# Preserve the unchanged byte-bound SUP2 copied for L-CTIPFREAL1.\n' + entry).encode())
print(json.dumps(dict(status='PASS',delivery=DEST.as_posix(),copied_existing_bytes=True,new_scientific_calls=0,new_media_generation=0),ensure_ascii=False))
