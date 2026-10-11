"""Close actual saved-view documentation using ordinary records, without science."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import re
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
EXT = Path(__file__).resolve().parent
BASE = '7887aa1138f8e46a2b15f47a1060aa7d72cfe651'
REL = 'functional_views/native_alpha_partial_20261011/complete_001'
STAGE = ROOT/REL
VIEW = STAGE/'run_001/view'
sha = lambda path: sha256(path.read_bytes()).hexdigest()
read = lambda path: json.loads(path.read_bytes())
git = lambda *args: subprocess.check_output(['git','-c','gc.auto=0',*args],cwd=ROOT)
assert git('rev-parse','HEAD').decode().strip() == BASE
protocol,outer,helper,raw = read(STAGE/'protocol.json'),read(STAGE/'view_launch.json'),read(VIEW/'alpha_partial_view_receipt.json'),read(VIEW/'view.json')
assert all(record['status']=='pass' for record in (outer,helper,raw))
assert outer['exit_code']==0 and outer['stop_reason'] is None and outer['all_bindings_unchanged']
assert all(sha(ROOT/name)==pin for name,pin in protocol['bindings'].items())
terminal = read(EXT/'execution_terminal_review.json')
assert terminal['status'].startswith('pass')
physical,pixel = read(EXT/'physical_results_review.json'),read(EXT/'root_pixel_review.json')
assert physical['status']=='completed_actual_saved_result_interpretation_no_new_scientific_gate'
assert pixel['status']=='pass_actual_six_PNG_pixel_inspection_no_new_render'
author = STAGE/'author'
for name in ('preflight_scope_review.json','execution_terminal_review.json','TERMINAL_REVIEW.md',
        'physical_results_review.json','PHYSICAL_RESULTS_REVIEW.md','root_pixel_review.json',
        'write_pixel_review.py','record_authorization.py','close_execution_docs.py'):
    target = author/name
    assert not target.exists()
    content = (EXT/name).read_bytes()
    if name.endswith('.md'):
        text = content.decode('utf-8').replace(ROOT.as_posix()+'/', '../../../../')
        text = re.sub(r'(\.py):(\d+)(?=\))',r'\1#L\2',text)
        content = text.encode('utf-8')
    target.write_bytes(content)

comparison = read(VIEW/'alpha_comparison.json')
rows = comparison['rows']
assert len(rows)==14 and helper['matched_original_targets']==14
fmt = lambda value: format(value,'.10g')
fields = ('R_input_N','total_body_Fy_N','material_body_Fy_N','regularization_body_Fy_N',
    'tip_to_bottom_mm','medium_min_J','medium_max_abs_Hu_per_mm')
two_state_table = '\n'.join('| '+str(rows[i]['d_mm'])+' | '+' | '.join(fmt(rows[i]['candidate_'+key]) for key in fields)+' |' for i in (6,13))
names = ('输入反力R [N]','下半total Fy [N]','下半material Fy [N]','下半Hu Fy [N]',
    '有限tip-bottom距离 [mm]','free-medium积分点minJ','free-medium max abs Hu分量 [1/mm]')
pair_table = '\n'.join('| '+name+' | '+' | '.join(fmt(rows[13][label+'_'+key]) for label in ('baseline','candidate','candidate_minus_baseline'))+' |' for name,key in zip(names,fields))
results = '''# M-AVIEW1 实际结果：14态显示／alpha对照通过，原卸载未完成

**M-AVIEW1 经直接人类批准，唯一实际执行 PASS，窗口已关闭。** 本通过仅覆盖保存态观察／显示／对照。原 M-ALPHA1 完整15目标仍为 NOT_PASS：14原点／加载态保存至1.20 mm，首次卸载1.15 mm超时，没有卸载接受态。原result、全部NPZ、source/card/protocol及77个准备bindings保持。

整体目标是独立HF有限变形／TMC前向评价：读取LF普通几何，在一致物理任务下计算可检查的变形、反力及工件作用，供外部研究层比较；HF不优化、不调用dmftd。此前新alpha已有接受态，但图件未产生，因此本卡读取已有结果以获得直接可检查的物理效果。没有重新加载或续算。

## 实际工作和证据

- 批准源码main `'''+BASE+'''`；直接批准、协议与真实准备发布证明见[授权记录](author/authorization.json)、[人类原文](author/direct_human_reply.json)和[来源证明](author/M_AVIEW1_source_publication_receipt.json)。准备卡及false准备标记作为历史保持，实际状态另记于本页。
- h0.5、84×40 mm下半域、固定side18方体center(71,40)、E1 MPa、nu0.3、厚20 mm、gamma1e−6、Lr80 mm；新alpha5e−7，旧baseline1e−6。只有alpha不同，BC／平均输入端口及几何保持。
- 一次launcher、一次wrapper、一次冻结raw viewer；一例alpha_half内14接受态。实际geometry14／nodal14，42逐态JSON、9842节点数据行；按源路径及字段身份门解码29既存NPZ的279字段实例，不读切线／全矩阵或baseline NPZ。
- 14个共同original origin/loading目标逐态身份配对，14指标的新旧值及196个已算candidate−baseline差值见[CSV](run_001/view/alpha_comparison.csv)和[JSON](run_001/view/alpha_comparison.json)。原baseline24行身份核查，未重新观察baseline；没有插值／百分比／归零或数值接近度新门。
- 6PNG／1GIF14帧、56份实际view文件；raw回执49项输出哈希，wrapper回执55项（分别不含自身）。全部文件经[独立终态核查](author/TERMINAL_REVIEW.md)及[物理解读](author/PHYSICAL_RESULTS_REVIEW.md)核对。[root像素记录](author/root_pixel_review.json)实际查看六PNG；没有重新渲染或逐帧人工检查全部GIF。
- 原raw几何／节点门通过，逐态节点结果与缓存三分量合力一致，holding逐节点total向量相反，固定工件split保持零。geometry valid及无strict-overlap记录不授予有效接触、连续压力或稳定性。
- 额外F／T／构模／平衡／HP／JIT／LF调用0；pure源和导入来源为零力学依据，mechanical_hooks_monitored=false，不能称动态hook监测。没有重试、修复重跑、延期或force。

## 真实耗时与资源

| 原记录 | 秒 | 采样峰RSS [B] |
| --- | ---: | ---: |
| raw viewer（保存态显示） | '''+repr(raw['elapsed_seconds'])+''' | '''+str(raw['sampled_peak_RSS_bytes'])+''' |
| wrapper回执（最终写回执前） | '''+repr(helper['elapsed_seconds'])+''' | '''+str(helper['peak_sampled_RSS_bytes'])+''' |
| outer（helper/退出全过程） | '''+repr(outer['elapsed_seconds'])+''' | '''+str(outer['peak_sampled_tree_RSS_bytes'])+''' |

预算helper180／outer240秒，采样8GiB；outer exit0、stop_reason=null、全部bindings unchanged。wrapper最终stdout实际39.195223199989414秒。own与tree采样不同，不作同刻比较，不承诺OS硬内存上限。原[stdout](view_stdout.log)的Matplotlib loc=best绘制图例性能UserWarning保留；不是终端错误或新科学验收门。

## 可人工检查的数值与效果

以下只复制本次已有观察／对照值，显示舍入；完整精度保存在CSV/JSON，没有额外科学计算。

| 平均输入 [mm] | R [N] | 下半total Fy [N] | material Fy [N] | Hu Fy [N] | 有限tip-bottom [mm] | medium minJ | medium max abs Hu [1/mm] |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
'''+two_state_table+'''

| 1.20 mm指标 | 原alpha1e−6 | 新alpha5e−7 | 已保存新−旧 |
| --- | ---: | ---: | ---: |
'''+pair_table+'''

新alpha峰值反力与原值接近；material Fy增加、Hu Fy减小、total Fy增加。0.85 mm附近free-medium minJ两点差异明显，峰值minJ仍很小。两值及图形只能描述参数敏感性，不能证明alpha或网格收敛。已有证据不足以把原卸载超时归因于Hu核错误、物理不稳定或Newton无法收敛。

红箭头是全部703下半工件节点的弱式力（含physical/cut/interior）；holding反向，镜像上半只显示，不再求解。下半signed Fy、镜像净力和cached双侧幅值和须分别解释。峰值cached双侧法向幅值和0.24984243260064853 N仍不是合格有效夹持力。

钳尖已接近固定方体底面；无符号有限距离0.0009696602064828141 mm不等于穿透判据或合格接触。node-window与finite-surface本态数值相同也不能混同定义。色彩图的cell meanJ／Hu Frobenius范数不同于表内积分点minJ／max abs Hu分量；Green应变是保存F派生的binary64观察，没有新HP。

## 实际图件

![14接受加载态实际变形与三分量工件力](run_001/view/alpha_half/actual_states.gif)

![两alpha的14共同加载目标](run_001/view/alpha_response_comparison.png)

[1.20 mm三分量快照](run_001/view/loading_120_forces.png) · [0.85 mm快照](run_001/view/loading_085_forces.png) · [峰值/最后态及有限面zoom](run_001/view/comparison.png) · [距离与signed Fx](run_001/view/distances_forces.png) · [峰值分区场](run_001/view/peak_fields.png)

统一14态力尺度使0.85及Hu箭头很小，视觉缺失不代表力为零；底面小距离在全距离共轴图中也难分辨，应结合zoom与原数值。两快照复制新GIF帧6/13原像素，状态SHA、leg、d有效；PEAK和LAST均为index13，没有卸载帧。原比较图标题笼统称orange distances，各线实际由legend区分，冻结viewer未改。

## 当前进度与下一步

完整NumPy力、全DOF未对称矩阵／组装、平均输入Mean、API／同任务batch、缓存保存、独立读取及实际显示已有实现。新alpha14加载态已可见；本轮补齐的是显示功能，未补齐卸载或物理资格。公共Mean/API没有已验证保存态下降续算入口；底层warm参数及非负阶段变量不能直接用于1.20→1.15 mm。

[下一步取舍](NEXT_STEP_REVIEW.md)优先明确保存峰值的初始mean／split／R／可用缓存、下降目标、回滚和来源合同，再准备最小局部验证。不复做长加载、不扫描新alpha、不修Hu核或放宽原门。一般输入、其它形状完整路径、全部切线列独立验证、连续总压力、可移动工件/摩擦、有效夹持、物理稳定性、正式标签/排名及HF5仍有缺口。原alpha24态／48HP只属原任务；新alpha无HP。
'''
next_step = '''# M-AVIEW1 后最近一步：保存峰值下降续算合同

本轮唯一实际显示PASS，原M-ALPHA1数值NOT_PASS保持；本文件是下一步依据，不授权新F/T/HP、平衡、模型读取范围或资源窗口。

实际14态显示已提供结构变形、signed材料/Hu工件作用和有限面距离。峰值反力近原alpha，材料Fy增加、Hu Fy减小，0.85附近局部minJ更敏感；峰值有强局部压缩但无新HP/稳定或合格压力证据。仅这些结果不支持再扫描alpha、放门、修改Hu核或重新长加载。

最近能力缺口是从现有1.20 mm接受态直接执行原1.15 mm卸载目标。现有公共Mean/API/CLI从零开始；底层warm接口仍从s0、非负s及target_origin+s出发，不能直接承接负增量或任意截断targets。已有[卸载静查](author/UNLOAD_COST_AUDIT.md)确认time_limit与durable/临时cache边界，未证明原平衡算式失败。

只详细准备这一阶段：先检查源与保存态合同，明确绝对初始mean、split数组、R和可用缓存的来源绑定，明确绝对下降目标、独立新计时、失败回滚、accepted保存及父/子路径状态。临时last_tangent不当成已接受切线；原failed结果和14态不改写。能否复用保存切线须由实际身份和源码接口证明。

随后在最小隔离候选中实现公共续算入口；准备一个有界局部验证卡，先核合同，再在明确新批准范围内接续原下降目标。新求解若通过，仅说明子路径实际达到该目标；原完整任务的关联及资格另按证据记录，不能把准备或trial标作accepted。当前未实现该入口、未执行任何续算，也未拟定未经审阅的资源数值。

| 分类 | 证据／影响 | 最近最小动作 |
| --- | --- | --- |
| 当前阻断 | 公共保存态下降续算未实现，原卸载接受态缺失 | 设计明确initial-state及absolute-target合同，保持原任务与门 |
| 下一步前置 | 接受态缓存与临时last_tangent不同；原K对象回滚不等于新K数值审计 | 按保存声明和source验证允许复用的初态/缓存，不借未接受trial |
| 非阻断改进 | early/Hu箭头、微小bottom gap在统一全图尺度下难见 | 当前用zoom与原数值；显示若改进另记录，不重绘本卡 |
| 未来研究 | 新alpha无HP，压力／有效夹持／稳定／一般输入／HF5未完成 | 续算功能后逐项独立验证，保留外部研究层比较边界 |

后续只保留能力依赖粗路线：完成加载/卸载接口与保存态关联，依据真实结果补独立参考，改进可解释接触指标及一般输入，再进入本项目HF5标签/比较；其它HF线不作本项目资格。
'''
for name,text in (('RESULTS.md',results),('NEXT_STEP_REVIEW.md',next_step)):
    with (STAGE/name).open('x',encoding='utf-8',newline='\n') as stream:
        stream.write(text)
body = '''# 当前接续：M-AVIEW1 实际显示通过；原alpha卸载仍未完成

独立HF有限变形／TMC前向评价继续面向实际结构变形、反力及可解释工件作用；HF与LF优化断开，main开发，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git，science0.5.0与原资格保持。

M-AVIEW1按直接批准唯一执行PASS、已闭卡：原alpha5e−7的14个接受origin/loading态，一例中geometry/nodal各14次、9842节点行、29NPZ/279字段，14共同目标及196已算差值，6PNG/14帧GIF和0.85/1.20两快照均已实际生成。outer39.6406280999945秒/exit0、tree采样峰363720704B、stopnull、77原bindings不变；F/T/HP/构模/平衡/JIT/LF新增0，无重试或force。实际像素及独立记录核查通过，不是新物理资格。

峰值1.20 mm：R0.37865427196005513 N，下半工件total/material/Hu Fy=0.12492121630032427/0.12405713468784063/0.0008640816124836284 N，有限tip-bottom距离0.0009696602064828141 mm，medium minJ2.3283009562457014e−5。减半alpha后的峰R近原值、material/Hu分量变化，0.85附近局部压缩更敏感。仅两值敏感性；双侧幅值和不是有效夹持，几何距离不是压力/穿透资格，新alpha没有HP。

原M-ALPHA1仍NOT_PASS：14加载态至1.20接受保存、第一次卸载1.15在controller时间预算处停止。原result/保存态不改，path/unload/tasktarget均false。公共Mean/API尚无保存态下降续算入口；最近先准备明确初始mean/split/R/cache、下降目标及回滚/来源合同，再有界局部验证，不重跑长加载或扫描新alpha。

已有完整力、全DOF未对称矩阵/组装、Mean/API/batch/缓存/保存/读取/实际显示。连续总压力、移动工件/摩擦、有效夹持、物理稳定性、其它形状完整验证、一般输入、全部切线列独立验证及正式HF5仍未完成。原24态48HP与PORT方向资格不转给新alpha。阶段README/卡/protocol中的false为历史准备记录，实际记录在RESULTS和授权/launch中。
'''
body += '\n[实际结果与图件](../'+REL+'/RESULTS.md) · [下一步取舍](../'+REL+'/NEXT_STEP_REVIEW.md) · [原数值结果](../lf_data_preparation/native_interface_001/regularization_sensitivity_001/RESULTS.md)\n\n'
prefix = (body+'<details>\n<summary>更新前完整原文（历史状态不代表当前）</summary>\n\n').encode('utf-8')
history = []
for name in ('docs/CURRENT_STATUS.md','docs/RESUME_DEVELOPMENT.md'):
    old = git('show',BASE+':'+name)
    assert (ROOT/name).read_bytes()==old
    current = prefix+old+b'\n\n</details>\n'
    assert current.count(old)==1
    (ROOT/name).write_bytes(current)
    history.append(dict(path=name,old_bytes=len(old),old_sha256=sha256(old).hexdigest(),
        new_sha256=sha256(current).hexdigest(),history_start_byte=len(prefix),
        history_end_byte_exclusive=len(prefix)+len(old),old_body_preserved_exactly=True))
assert all(sha(ROOT/name)==pin for name,pin in protocol['bindings'].items())
closure = dict(status='pass_actual_execution_documentation_closed',created_utc=datetime.now(timezone.utc).isoformat(),
    card='M-AVIEW1',source_commit=BASE,protocol_sha256=sha(STAGE/'protocol.json'),
    execution_status='pass',authorized=True,executed=True,execution_closed=True,
    result_sha256=sha(STAGE/'RESULTS.md'),next_step_sha256=sha(STAGE/'NEXT_STEP_REVIEW.md'),
    actual_view_counts=helper['actual_observation_counts'],view_outputs=56,actual_PNGs=6,actual_GIF_frames=14,
    original_M_ALPHA1_status='not_pass',original_unload_completed=False,
    front_history=history,review_pins={REL+'/author/'+name:sha(author/name) for name in
        ('execution_terminal_review.json','physical_results_review.json','root_pixel_review.json')},
    actions=dict(new_HF_imports=0,new_NPZ_decodes=0,new_observers=0,new_F_T=0,new_HP=0,new_solves=0,new_renders=0),
    actions_scope='Postterminal documentation work only; actual approved view decoded29 NPZ/279fields and observed14geometry/14nodal as separately recorded.',
    qualification=dict(new_HP=False,pressure=False,effective_clamp=False,stability=False,whole_HF5_complete=False))
with (author/'execution_documentation_receipt.json').open('x',encoding='utf-8',newline='\n') as stream:
    stream.write(json.dumps(closure,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
print(json.dumps(dict(status=closure['status'],card='M-AVIEW1',execution_status='pass',fronts=len(history),
    original_M_ALPHA1_status='not_pass',frozen_bindings_checked=len(protocol['bindings'])),ensure_ascii=False))
