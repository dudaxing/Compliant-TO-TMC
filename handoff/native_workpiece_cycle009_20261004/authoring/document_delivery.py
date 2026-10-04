"""Document closed cycle009 phases; preserve all seven previous front bodies."""
from pathlib import Path
from hashlib import sha256
import json
import posixpath
import shutil
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).parent
STAGE=ROOT/'lf_data_preparation/native_workpiece_001/coarse_square_cycle_009'
VIEW=ROOT/'functional_views/native_workpiece_cycle009_20261004'
HANDOFF=ROOT/'handoff/native_workpiece_cycle009_20261004'
BASELINE='97b7e0eecd07aee0bd16c61961dedb360202641c'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()

def write(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,indent=2,ensure_ascii=False,allow_nan=False);stream.write('\n')

result=read(STAGE/'result/result.json')
reference=read(STAGE/'reference/summary.json')
measurement=read(VIEW/'region_saved_001/measurement_001/regions_measurements.json')
assert result['status']=='success' and reference['status']==measurement['status']=='pass'
assert result['accepted_states']==len(measurement['accepted_states'])==9
assert measurement['geometry_calls_started']==measurement['geometry_calls_completed']==9
notes=['production_reference_review.json','region_saved_review.json','visual_saved_review.json',
       'plot_workpiece_cycle009_author_note.json','plot_tangent_cost002_author_note.json']
for name in notes:
    assert (AUTHOR/name).is_file()
for name in ('production_reference_review.json','region_saved_review.json'):
    assert read(AUTHOR/name)['status']=='pass'
fronts=read(ROOT/'handoff/native_workpiece_cycle008_20261004/document_preservation.json')['fronts']
front_names={item['path'] for item in fronts}
for card in (STAGE,VIEW/'region_saved_001',VIEW/'saved_render_001',VIEW/'saved_cost002'):
    assert front_names.isdisjoint(read(card/'protocol.json')['bindings'])
    assert all(sha(ROOT/name)==pin for name,pin in read(card/'protocol.json')['bindings'].items())
HANDOFF.mkdir(exist_ok=False)
(HANDOFF/'authoring').mkdir()
for path in sorted(AUTHOR.iterdir()):
    if path.suffix in ('.json','.diff','.py','.md'):
        destination=HANDOFF/path.name if path.name in notes else HANDOFF/'authoring'/path.name
        shutil.copyfile(path,destination)

phases=[]
for directory,phase in [
    (ROOT/'lf_data_preparation/native_workpiece_001/numpy_tangent_chunk_001','tests'),
    (ROOT/'lf_data_preparation/native_workpiece_001/numpy_tangent_chunk_001','comparison'),
    (ROOT/'lf_data_preparation/native_workpiece_001/native_mean_chunk_integration_001','tests'),
    (STAGE,'prepare'),(STAGE,'production'),(STAGE,'reference'),
    (VIEW/'region_saved_001','measure'),(VIEW/'saved_render_001','render'),(VIEW/'saved_cost002','render')]:
    receipt=read(directory/(phase+'_launch.json'))
    assert receipt['status']=='pass' and receipt['exit_code']==0 and receipt['invocations']==1
    assert receipt['all_bindings_unchanged'] and receipt['stop_reason'] is None
    phases.append(dict(directory=rel(directory),phase=phase,status=receipt['status'],
        outer_seconds=receipt['elapsed_seconds'],peak_tree_RSS_bytes=receipt['peak_sampled_tree_RSS_bytes'],
        bindings=len(receipt['bindings']),receipt_sha256=sha(directory/(phase+'_launch.json'))))

rows=['| index | leg | input mm | R N | output +y mm | minJ | bottom ray mm | left ray mm |',
      '|---:|---|---:|---:|---:|---:|---:|---:|']
for index,(state,geo) in enumerate(zip(result['states'],measurement['accepted_states'])):
    assert state['state_sha256']==geo['state_sha256'] and state['d']==geo['d_mm']
    faces=geo['geometry']['faces']
    rows.append(f"| {index} | {state['leg']} | {state['d']:g} | {state['R_input']:.10g} | {state['q_out']:.10g} | {state['minimum_J']:.10g} | {faces['bottom']['minimum_first_ray_hit_mm']:.10g} | {faces['left']['minimum_first_ray_hit_mm']:.10g} |")
geometry='''几何卡一次真实终态 pass：9 次高层 geometry 开始/完成；只读取已保存的实际 ×1 Q1 坐标，没有重新求力、切线、HP 或无符号边界距离。四个纯几何源码与原39项解析测试证据相同，0重测。九态几何均有效、无 raw/strict 跨域内部重叠或 roundoff ambiguity；全部实际跨域 AABB 候选对为0，因此此路径没有实际 SAT 候选对计算。解析测试与路径观测分开报告。闭区域包含数学对称 cut，不能作为物理接触面；完整包含和机构自重叠未证明。

峰态底面首次外向法向射线为0.07671066678990902 mm，左面为2.8327754289207783 mm；返回零的两面射线均2 mm。底面接近、左面远离，不能认定双面夹持。68条最小命中见证的保存点方程已独立读核（不重测几何），最大点距误差约3.11e−15 mm。返回态位移是微小非零，不能声称所有实际坐标与初态逐字节相同。

峰态下半体总 (Fx,Fy)=(-0.0007910899872955321,+0.0037892857813192618) N，材料与Hu贡献分别(-0.0003137551201961619,+0.0023430611778208557)和(-0.00047733486709937006,+0.0014462246034984065) N。保持反力反号，镜像上半体(Fx,-Fy)、完整镜像净力(2Fx,0)；2|Fy|=0.007578571562638524 N仅为标量和，不能当完整净力、压力或合格夹持力。

'''+ '\n'.join(rows)+'''

已生成[真实九态 ×1 动画](../../../functional_views/native_workpiece_cycle009_20261004/saved_render_001/animation_001/cycle009_actual_path.gif)、[力/位移/J/Hu/三分量工件力及实际求解过程图](../../../functional_views/native_workpiece_cycle009_20261004/saved_render_001/physical_001/cycle009_saved_path.png)、[九态CSV](../../../functional_views/native_workpiece_cycle009_20261004/saved_render_001/physical_001/accepted_numeric_states.csv)和[一次切线成本图](../../../functional_views/native_workpiece_cycle009_20261004/saved_cost002/render_001/tangent_cost.png)。动画逐态保留真实index、初始与返回零，9帧各1000 ms，无插值、无去重；显示完整半模型和工件附近细节。静图实际×1峰/回零，另列×4只用于放大展示，力箭头采用统一N标尺；单元均值位移颜色与最大节点位移不同。

root及独立审阅者实际看保存PNG和GIF关键帧。原三程序绘图卡一次 pass；原成本PNG的legend遮横轴Peak标签，原文件保留。另建saved_cost002一次卡，仅改legend/footer位置重新绘保存成本数据；CSV数值不改、不重复力学/几何计算，也不重开原卡。新成本PNG已实际检查无遮挡。
'''
draft=(AUTHOR/'draft_report.md').read_text(encoding='utf-8')
old='[待填实际geometry/visual]\n\n几何与可视化正按各自独立保存数据卡执行。仅使用终态真实输出填入距离、交叠/无射线、实际图尺寸、帧/行数、倍率、力标尺、成本和 SHA；不在此草稿提前宣布通过。'
assert draft.count(old)==1
report=draft.replace(old,geometry).replace('本草稿拟整合为本阶段 `RESULTS.md`，以下链接均按该位置书写：','以下为实际闭卡证据；旧失败卡、旧来源胶囊与全部历史报告保持：')
report=report.replace('下一步物理功能应依据本次实际结果：先完成本卡已安排的区域重叠与有限工件面法向射线观测，结合真实 ×1 变形、输入输出和工件三分量力，明确还剩多少空间、最近点是否角点、返回路径是否完整；再据此规划更大行程或更具体的接触/夹持验收。暂不以小间距或非零弱式工件力直接宣布夹持，也不自动扩展到细网格、其他机构或工件。',
    '下一步先补充工件边界节点的材料/Hu作用力分布与作用位置图，用已保存力明确底面、左面及角点的作用方向；这一弱式节点力观测不自动成为压力。底部介质minJ=.02808提示不能按此前大步长继续盲目增大行程。随后冻结独立近接触增量探索任务（优先同方体、小幅新增峰值、完整回零与每态fresh参考），由实际距离/J/平衡结果决定推进或停止；圆体、位置/尺寸与细网格作为后续独立物理任务。具体新行程/预算/验收须在新卡显式记录，本轮未建立或执行更大行程或圆体任务。整体HF项目仍未完成。')
phase_table=['| 已关闭阶段 | outer秒 | 树RSS bytes | pins |','|---|---:|---:|---:|']
for phase in phases:
    phase_table.append(f"| {phase['directory'].split('/')[-1]}/{phase['phase']} | {phase['outer_seconds']:.9f} | {phase['peak_tree_RSS_bytes']} | {phase['bindings']} |")
report+='\n## 完整阶段成本、变更记录与恢复\n\n'+'\n'.join(phase_table)+'\n\n'
report+='''各 helper 成本见相应tests/comparison/execution/summary/measurement/render回执，outer和helper分别报告；准备和来源冻结不计数值调用。新scope、显式chunk选项、600/660和240/300预算及保存120/150预算都在执行前独立冻结，原门、来源、任务和已关闭卡未静默修订。没有异常修复重试、force或预算扩展。

执行前迁移曾使私有core/launcher换行字节改变，独立静审发现后在作者目录恢复原字节；README三描述键计数在首次prepare前更正，科学pins未变。详情在authoring/root_migration.json、candidate_physical_review和pre_execution_wording_note。只读审阅曾按不存在的receipt路径探测，以及假设tiny-return坐标全等原坐标；这些探针失败未修改正式卡、未调用力学/几何，也未重跑阶段。实际回执范围以原始输出为准。

恢复入口以main和origin https://github.com/dudaxing/Compliant-TO-TMC.git为准。先读本报告与docs/CURRENT_STATUS.md，再用已安装Python在真实Git根运行 `python -B tools/handoff.py verify --output <新的仓库外JSON>`。源码/任务/数值包/图/参考/阶段成本随仓库manifest保存；公开另一目录恢复为文件身份检查，不是新数值复算或全部历史大附件展开。作者生成器与旧绝对argv用于过程追溯，不能直接重放关闭卡；新机器、新任务应使用新的独立目录和明确身份。
'''
with (STAGE/'RESULTS.md').open('x',encoding='utf-8',newline='\n') as stream:
    stream.write(report)
write(HANDOFF/'closed_009_identity.json',dict(baseline_commit=BASELINE,status='pass',card_closed=True,
    targets_mm=result['targets_mm'],accepted_states=9,return_zero_accepted=True,HP_calls=18,
    checks_completed=reference['checks_completed'],result_sha256=sha(STAGE/'result/result.json'),
    source_sha256=read(STAGE/'source_freeze.json')['sources'],phases=phases,
    qualification_scope=reference['qualification'],geometry_calls=9,
    no_contact_clamp_pressure_energy_stress_HP_all_column_qualification=True,
    root_actual_visual_QA=['physical PNG','cost002 PNG','animation peak/return PNG'],
    report_sha256=sha(STAGE/'RESULTS.md'),notes={n:sha(HANDOFF/n) for n in notes}))
preserved=[]
for item in fronts:
    name=item['path'];path=ROOT/name
    before=subprocess.check_output(['git','show',BASELINE+':'+name],cwd=ROOT)
    assert path.read_bytes()==before
    link=posixpath.relpath(rel(STAGE/'RESULTS.md'),Path(name).parent.as_posix())
    animation=posixpath.relpath(rel(VIEW/'saved_render_001/animation_001/cycle009_actual_path.gif'),Path(name).parent.as_posix())
    prefix=(f'2026-10-04最新：**009保留原完整九目标，1.75mm加载与回零已完成；63F/36T，18次新HP/174111检查通过。** 显式256单元分块切线不改变数学或默认full；前三保存态逐字节等价，原前八态32整档相同，生产373.57秒在原600/660预算内。见[目标、变更、效果/成本、范围与下一步]({link})及[实际九态×1动画]({animation})。\n\n'+
        '底面射线.0767107mm、左面2.83278mm，介质minJ=.0280804；几何无已测跨域内部重叠，尚未证明有效夹持、压力、能量或应力HP。旧008仍是time_limit失败。下一步补工件节点力位置图，再根据间隙/J规划近接触增量；圆/细网格未执行。以下逐字节保留此前时点原文，当前以本条与新报告为准。\n\n').encode()
    appendix=b''
    if name=='docs/NUMPY_FORCE_PROGRESS_20261002.md':
        appendix=('\n\n## native-workpiece-cycle009-complete-20261004\n\n'+
          '未采用删回程1.5mm的旧建议：完整原九目标在原预算内通过。新_tangent_chunked保留全批小量selector、单元内9Q/8列归约和全域CSC顺序；默认full不变，机械CLI显式chunk256。12针对测试和10集成测试通过；原三保存态alltensor/CSC逐字节一致，一次测量比1.84–1.87。\n\n'+
          '009原27模型字段一致、213pins/68caps/63inputs、63F36T1solve9states18HP174111；前8的32文件同旧008。生产372.592/helper373.570outer秒，参考179.295summary180.154outer秒。原flagsfalse，外部fresh参考资格单独报告且限force/PORT方向Jv/equilibrium/bodyprojection，能源未评估、stressHP/全列/有效clamp仍未完成。\n\n'+
          '新9次保存几何、九帧×1动画与力/场量图均有独立闭卡；成本图另建布局更正卡，原图保留。全过程与物理后续见页首新报告。\n').encode()
    path.write_bytes(prefix+before+appendix)
    assert path.read_bytes()[len(prefix):len(prefix)+len(before)]==before
    preserved.append(dict(path=name,baseline_sha256=sha256(before).hexdigest(),current_sha256=sha(path),
        old_body_preserved=True,prefix_bytes=len(prefix),appendix_bytes=len(appendix)))
write(HANDOFF/'document_preservation.json',dict(baseline_commit=BASELINE,fronts=preserved,
    scope='Seven previous bodies byte exact; current prefix and one NumPy appendix'))
print(json.dumps(dict(status='documented_closed_009',fronts=len(preserved),phases=len(phases),report_sha256=sha(STAGE/'RESULTS.md'))))
