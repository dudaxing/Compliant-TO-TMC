"""Publish existing bytes and ordinary documentation, never reopen science."""
from datetime import datetime, timezone
from html import escape
import hashlib
import json
from pathlib import Path
import shutil

AUTHOR=Path(__file__).resolve().parent
BASE=Path('D:/hfl1_001')
ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
REL='lf_data_preparation/native_interface_001/lf_circle_tip_force_control_001'
DEST=ROOT/REL
def read(path): return json.loads(Path(path).read_bytes())
def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(value.encode('utf-8') if isinstance(value,str) else (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
def copy(source,target):
    target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('xb') as stream: stream.write(source.read_bytes())
def ident(path):
    raw=path.read_bytes(); return dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
assert not DEST.exists()
for name in ('RESULTS_PHYSICS_REVIEW.md','RESULTS_PHYSICS_REVIEW.json','USAGE_AND_LIMITS.md'):
    assert (AUTHOR/name).exists(), name
result=read(AUTHOR/'EXECUTION_RESULT.json')
assert result['status']=='PASS'
DEST.mkdir()
for path in sorted(AUTHOR.iterdir()):
    if path.is_file() and path.suffix in ('.py','.json','.md'):
        copy(path,DEST/'author'/path.name)
for name in ('execution_evidence.zip','EVIDENCE_MANIFEST.json','seal_receipt.json','installation_receipt.json',
             'execution_receipt.json','top_supervision.json','outer_supervision.json','top_start.json',
             'outer_start.json','root_qa.json','outer.log','outer.instances.ndjson','protocol.json','authorization.json'):
    copy(BASE/name,DEST/'execution'/name)
for name in ('launch_fload1.py','outer_fload1.py','run_fload1.py','render_fload1.py','windows_owned_process_sup2.py'):
    copy(BASE/name,DEST/'wrapper'/name)
for name in ('test_native_guided_force.py','test_split_displacement.py'):
    copy(BASE/'candidate/hf_repo/tests'/name,DEST/'tests'/name)
# Every scientific array remains only in the original closed-window ZIP.
# Copy only new ordinary JSON/XML/log receipts and the already inspected PNG.
for path in sorted((BASE/'run_001').rglob('*')):
    if path.is_file() and 'tmp' not in path.relative_to(BASE/'run_001').parts and path.suffix in ('.json','.xml','.log','.ndjson'):
        copy(path,DEST/'run'/path.relative_to(BASE/'run_001'))
copy(BASE/'run_001/view/force_control.png',DEST/'view/force_control.png')
copy(AUTHOR/'USAGE_AND_LIMITS.md',DEST/'USAGE.md')
copy(AUTHOR/'EXECUTION_RESULT.json',DEST/'result_summary.json')
rows=result['accepted_scalar_rows']; cross=result['cross_checks']
table='\n'.join(f"|{i}|{r['P_target_half_N']:.16g}|{r['body_q_mm']:.16g}|{c['prescribed_reference_q_mm']:.8g}|{c['q_abs_error_mm']:.8g}|{c['R_abs_error_N']:.8g}|" for i,(r,c) in enumerate(zip(rows,cross)))
gates='\n'.join(f"|{i}|{r['relative_residual']:.8g}|{r['relative_generalized_force_residual']:.8g}|{r['constraint_residual']:.8g}|{r['minimum_J']:.8g}|{r['relative_global_force_balance']:.8g}|{r['newton_checks']}|" for i,r in enumerate(rows))
report=f'''# L-CTIPFLOAD1：导向轴向力控实现及小模型验证

2026-10-23（Asia/Seoul）。**本卡执行PASS：17/17检查通过，一张实际结果图检查通过，两个新模块已安装，唯一窗口已关闭。** 外窗实际{result['seal']['elapsed_outer_seconds']:.6f}秒；无外部重试、修复重跑或新HP。正式r9力控尚未执行。

## 整体目标、本轮目的及效果

整体目标是HF独立读取LF几何，在一致的大变形／TMC物理条件下分析结构变形、接触作用、工件受力，并逐步建立承载与释放分析能力；HF不重新做LF优化。已有固定工件加载／卸载与导向位移探针。本轮补齐“保持机构平均输入，给工件轴向外载P，求未知刚体位移q”的功能。

这样可以把已有“给q→求Q”的结果反向核对为“只给P→独立求q”。真实小模型交叉通过，说明新增力控方程、符号、半模型口径和保存流程在本卡有限范围可用。它不等于真实夹持器承载已经验证；当前实际小模型的P均为负，更不能描述成正向拉力增大试验。

## 实现与代码对照

仅新增两份生产源码：`hf_repo/src/hf_eval/split_guided_force.py`（407行，reduced非对称方程与N步长）及`hf_repo/src/hf_eval/native_guided_force.py`（221行，严格父态准入、保存、外载账本和公共API）。原55份生产源码逐字节保持；默认fixed、位移probe、CLI、native_response及原力核／切线不改。测试原字节交付于[tests](tests/test_native_guided_force.py)，原始候选树在唯一ZIP中保留。[使用与限制](USAGE.md)给出最简调用。

未知量为自由场w、工件刚体平移q和机构输入乘子R；保留工件uy=0／转角0及原机构加权均值。工件全部原ux的内力求和等于绝对有符号P_half，不作节点平均。导向和支撑去重，外载账本中以显式P取代旧body-x保持反力，避免重复计数；ON-body x与P反号。N力已包含来源厚度，不能再乘厚度；本卡不自动乘2。

fresh锚点复核原split及有符号R、非零P0，直接一次新F/T检查；不投影或修复。随后只给P，未把参考q传入力控，也未从位移参考终态热启动。新g门、原自由平衡门分别满足；非对称reduced切线使用实际两个耦合块，不假定互为转置。

## 唯一执行范围与实际数值

新4×4 Q1／16单元／25节点／50场DOF，域2×2 mm、厚度2 mm、E1 MPa、ν.3、α1e−4、γ1e−6、Lr2 mm。固定父加载[0,.0005] mm成功后，原位移probe给q=[0,.00025,.0005] mm获得三载荷，再从同一父态独立执行力控。正式r9／厚度20 mm／α2.5e−7条件未改变。

|目标|P_half N|力控求得q mm|位移参考q mm|q绝对差 mm|R绝对差 N|
|---|---|---|---|---|---|
{table}

三态q／全场位移最大差3.9888329184806226e−13 mm，预声明交叉界值1e−8 mm；R最大差3.1170812458958252e−19 N，分别低于预声明的max(1e−12 N,1e−7×|R_ref|)。力控7次F／5次T均完成，save-time F/T均0；3接受态，无内部二分或失败attempt。

这里P从−3.21659e−8增加至−4.21365e−10 N，表示负x外载逐渐减弱，**不是正向承载量增长**。q正向变化是保持机构输入及其介质／材料响应下的新平衡结果。小模型Hu贡献较大，不能把总力直接称为纯接触力。

|态|rho_F|rho_P|mean残差 mm|min J|相对global balance|Newton检查数|
|---|---|---|---|---|---|---|
{gates}

原rho_F≤1e−9、新rho_P≤1e−9、mean残差≤5e−14 mm、J>0、global≤1e−6、rigid／zero≤8e−11 mm均通过；实际rigid误差0。rho_P按预先定义的SP=max(|P_target|,|P_anchor|,Ffloor)，本例三态SP均3.216587387036128e−8 N；不能改说成按每态|当前P|归一化。最大|g|2.5325848371540152e−17 N，原界3.216587387036128e−17 N。37×37混合单位矩阵condition约6.31e5～6.33e5仅作诊断，不证明唯一性或稳定性。

## 验证、停止与资源记录

唯一pytest用时11.30秒，17展开项全部通过：原9项＋新8非参数化方法。新30＋旧11次有限控制／拒绝调用；新4＋旧1条真实路径，受控partial在新真实／注入两轴各记一次。覆盖双向非对称dense oracle、fresh错误R／均值／P0、真实q↔P、缓存分量／厚度／账本、来源与输入拒绝、旧代表性兼容。

受控第二次T抛出constraint_failure后正确保存首锚点，父树哈希保持；这是预定异常持久化测试，**不是物理失稳或承载极限**。实际非预期失败0、外部重试0。

四层SUP2均normal_exit、returncode0、全部同实例终止／成员覆盖／句柄释放通过后，top才安装两个同字节新模块。采样最高树RSS258252800字节（约246 MiB），限额8 GiB；四库线程上限16，CPU执行。唯一原字节ZIP216成员，1145474字节，SHA256 `ec19f6d4a57757eb6d736cb3dd3694aa009337686afc5a704ac06dd6b9a7e0b2`；封存于原helper50.345秒／outer51.745秒内完成。详见[实际摘要](result_summary.json)、[安装回执](execution/installation_receipt.json)、[监督与原始封存](execution/EVIDENCE_MANIFEST.json)。

## 可视化与人工检查

![实际小模型变形、P–q、反力、残差与介质响应](view/force_control.png)

唯一新图6面板：实际几何×1、位移箭头×200；给q参考／给P未知q；交叉误差；带非零预载的total／material／Hu与输入R；全部实际Newton检查的双残差；J／Hu及全局／刚体误差。root仅一次像素检查，通过；未重绘。交叉误差远小于图中声明界值，柱高接近不可见，精确值见上表与[原JSON](run/artifacts/validation_summary.json)。残差图只有精确0显示为1e−18，原JSON不改。[人工检查页](inspection.html)。

## 记录、恢复与限制

批准卡及原规格保留在[前阶段](../lf_circle_tip_force_control_preparation_001/L-CTIPFLOAD1_CARD.md)。`author/`保存实现说明、五份独立有限静审、候选冻结、启动资格、实际执行和物理复核。冻结文件中的numerical_launched=false是**启动前历史快照**，本卡终态以result_summary／实际回执为准；不覆写历史。

[execution/execution_evidence.zip](execution/execution_evidence.zip)是原窗口内生成的完整原字节归档，没有交付时重打包。它包含原candidate、run_001科学缓存、模型、来源、日志和receipts；本目录的run只便于读取普通JSON／XML／日志，未额外解码NPZ。可在新目录解压查看与核字节；原JSON中的绝对路径是当时来源记录，不应直接覆盖身份文件。公共API接收当前恢复位置的父result路径，但本轮恢复验收只做Git与字节核对，没有异机环境或数值复算。原冻结launcher含唯一启动保护，不要在已有证据目录重开。

当前只支持从完整固定load_only父末峰开始、沿严格递增的绝对有符号P列表求导向q；未实现force保存态延伸、卸载、自由y／转动、摩擦或动力学。本卡真实小路径只测full；正式chunk256尚待真实任务核对。新HP0、正式r9力控0，压力、纯接触、承载极限、释放、稳定性与HF资格保持未授。

下一步见[具体计划](NEXT_STEPS.md)：先冻结正式低输入父态与既有位移参考的同定义载荷，再安排一次最小r9力控交叉；本卡未运行该任务。
'''
write(DEST/'RESULTS.md',report)
write(DEST/'NEXT_STEPS.md','''# 下一步：正式低输入r9的最小力控交叉

2026-10-23。L-CTIPFLOAD1已PASS并闭窗，当前只有小模型力控功能证据。建议下一阶段L-CTIPFREALPREP1先完成正式任务绑定和候选卡，随后另开获批窗口执行L-CTIPFREAL1；本轮不自动启动正式计算。

## 为什么选这个任务

小模型给P求q与原给q求Q在预声明界内吻合，下一缺口是正式14720单元／29970DOF、chunk256模式的真实功能闭环。先复用LOW1完整固定工件短父末峰（机构均值0.50 mm），而非新增材料、α或更大位移。它已有同定义q=0／0.025 mm位移参考，能直接检查力控功能，不以一个新载荷未知位移的结果自行证明正确。

## 准备范围

1. 仅读LOW1普通来源、任务、模型描述、parent/probe结果与已保存身份元数据，冻结完整父态accepted2、原节点／单元、signed R、lift/fluctuation及依赖清单；此步不读NPZ、不新F/T或HP、不重算父加载。
2. 载荷使用LOW1已存绝对Q：P0=3.686421133658022e−5 N，P1=4.3272306948756724e−5 N（half，含20 mm厚度）；来源为LOW1 RESULTS中的原值，执行前必须直接绑定原普通JSON与SHA。不能把0或ΔP冒充P0，也不能把小模型负载荷移植到r9。
3. 初步仅给[P0,P1]，未知q从同一q0父态求解；不传入参考q=.025，不从位移终态热启动。fresh P0若不满足原门，按原规则停，不修复父态或重取符号。force step初案(P1−P0)/16，N量纲独立；最终冻结时记录原非clock设置及允许内部二分上限。
4. 保α2.5e−7、γ1e−6、r9、圆心(80,40) mm、right92、Lr80、E1 MPa、ν.3、plane strain、厚度20、h=.5及原支撑／输入、全部工件成员；不扩大到高输入1.06、额外q或承载极限。

## 未来执行与验收设计

复用已安装API，不改HF默认源码。薄包装先冻结并独立静审；一次fresh+力控路径，保原自由平衡／mean／J／global／刚体门及新增独立合力门。交叉q、全场位移和R必须在运行前声明适合正式任务的检查门，不能照小模型极小误差事后设门，也不能只看API success。位移参考科学数组比较若需要，必须在下一卡中明确原NPZ字段／读取上限与CPU资源，不在文档准备阶段暗读。

原位移参考Q给出两个同P端点，但同P多平衡分支仍可能存在；q不一致应保留并诊断，不强制投影。控制器失收敛不能称释放或承载极限。LOW1末态轴向Hu约86.29%，即使力控闭环通过也仍是该TMC导向总力任务，不授纯接触抗拔资格。

下一卡拟controller1800秒、显示共享600秒、helper2700／outer2760秒、采样64GiB、四库线程上限16、原viewer8GiB；需候选包装和来源清单核对后才能形成最终授权卡，不沿用本卡已关闭480／540秒窗口。成功后可显示实际×1变形、P–q、机构R、total/material/Hu、尖端距离、右介质及双残差／收敛；图数和数组读取须卡中固定。首个终端错误停、保partial，无外部重试、修复重跑、延期或force。不新增HP、默认源码改动或资格升级。

下一阶段的输出应回答：真实模型是否能按指定半模型外载独立得到与同定义位移探针相符的q？通过后再考虑高输入同定义对照或力控保存态扩展，而非立即把路径拉到失败。
''')
links=[('RESULTS.md','完整结果与物理解释'),('USAGE.md','API用法及限制'),('NEXT_STEPS.md','下一步计划'),('result_summary.json','实际摘要与原门'),('run/artifacts/validation_summary.json','三态交叉原值'),('tests/test_native_guided_force.py','已测新测试源码'),('execution/EVIDENCE_MANIFEST.json','原归档清单'),('author/EXECUTION_ELIGIBILITY.json','启动前核对'),('author/RESULTS_PHYSICS_REVIEW.md','独立物理复核')]
items=''.join(f'<li><a href="{url}">{escape(label)}</a></li>' for url,label in links)
write(DEST/'inspection.html',f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>L-CTIPFLOAD1 实际结果</title><style>body{{max-width:1320px;margin:32px auto;padding:0 20px;font:16px/1.65 system-ui;color:#203040}}img{{width:100%;height:auto}}a{{color:#175d91}}.status{{padding:16px;background:#eef6ef;border-left:4px solid #497e50}}</style><h1>导向轴向力控：小模型验证</h1><p class="status">17/17 PASS · 两模块已安装 · 唯一窗口已关闭 · 正式r9尚未试算</p><p>保持机构均值0.0005 mm，只给有符号半模型外载P，独立求工件q。最大q差3.98883e−13 mm。三载荷均负且逐渐减弱，本图不表示正向承载增长或压力。</p><img src="view/force_control.png" alt="实际×1变形、P–q、误差、材料和Hu力、收敛及介质响应"><p>实际几何×1；仅箭头×200。误差柱接近不可见，精确值见JSON。root一次像素检查已通过，本页仅链接同一图。</p><ul>{items}</ul></html>''')
for rel,prefix in [('README.md',''),('docs/CURRENT_STATUS.md','../'),('hf_repo/README.md','../')]:
    path=ROOT/rel
    banner=f'> 2026-10-23 L-CTIPFLOAD1 **力控实现与小模型验证PASS**：17/17通过；仅给绝对半模型P独立求q，与位移参考最大差3.99e−13 mm。两个新模块已安装，原55份生产源码不变；[实际图与记录]({prefix}{REL}/RESULTS.md)、[API用法]({prefix}{REL}/USAGE.md)、[下一步：正式低输入r9交叉准备]({prefix}{REL}/NEXT_STEPS.md)。实际小模型载荷均负，不能称正向承载验证；正式r9力控与新HP未执行。原数值窗口已关闭，下方状态保留为历史时点。\n\n'
    path.write_bytes(banner.encode('utf-8')+path.read_bytes())
# Correct the current feature description without rewriting historical results.
path=ROOT/'docs/GUIDED_WORKPIECE_PROBE.md'
raw=path.read_bytes()
raw=raw.replace('未实现probe的保存态延伸、力控制、自由y／转动、摩擦或动力学。'.encode('utf-8'),
    ('未实现probe的保存态延伸、自由y／转动、摩擦或动力学。另已新增独立导向轴向力控API，见[力控实现与小模型验证](../'+REL+'/RESULTS.md)；它不改变本位移probe的控制语义。').encode('utf-8'))
path.write_bytes(raw)
manifest=[]
for path in sorted(DEST.rglob('*')):
    if path.is_file(): manifest.append(dict(path=path.relative_to(DEST).as_posix(),**ident(path)))
write(DEST/'DELIVERY_MANIFEST.json',dict(stage='L-CTIPFLOAD1',created_utc=datetime.now(timezone.utc).isoformat(),
    files=manifest,scientific_recalculations=0,scope='Existing original bytes plus ordinary records. Excludes this manifest and later publication receipts.'))
print(json.dumps(dict(status='assembled',directory=str(DEST),files=len(manifest)+1)))
