"""Build a documentation proposal from closed JSON only; no HF/numerical imports."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
OUT=Path(__file__).resolve().parent
def read(path): return json.loads((ROOT/path).read_text(encoding='utf-8'))
def digest(path): return sha256((ROOT/path).read_bytes()).hexdigest()
paths={
 'production':'lf_data_preparation/native_workpiece_001/right_margin_cycle_001/run_001/result/result.json',
 'reference':'lf_data_preparation/native_workpiece_001/right_margin_cycle_001/reference/summary.json',
 'view':'functional_views/right_margin_20261007/complete_001/view/view.json',
 'case_view':'functional_views/right_margin_20261007/complete_001/view/right2col/summary.json',
 'zero_margin_case_view':'functional_views/right_margin_20261007/complete_001/view/gamma1e6/summary.json',
 'progress':'docs/evidence/workpiece_enlargement_20261007/right_margin_progress.json',
 'model_metadata':'lf_data_preparation/native_workpiece_001/right_margin_cycle_001/run_001/result/model/model.json'
}
data={k:read(p) for k,p in paths.items()}
result,reference,view=data['production'],data['reference'],data['view']
assert result['status']=='success' and result['path_completed'] and result['accepted_states']==24
assert reference['status']=='pass' and reference['accepted_states']==24
assert reference['result_sha256']==digest(paths['production'])
assert reference['HP_calls_started']==reference['HP_calls_completed']==48 and reference['checks_completed']==476733
assert all(reference[k] is False for k in ('contact_qualified','clamp_qualified','pressure_qualified'))
assert view['status']=='pass' and view['geometry_completed']==view['nodal_completed']==48
rows=data['case_view']['rows'];oldrows=data['zero_margin_case_view']['rows']
assert len(rows)==24 and [r['state_sha256'] for r in rows]==[r['state_sha256'] for r in result['states']]
def at(rows,d):
 selected=[r for r in rows if r['leg']=='loading' and r['d_mm']==d and r['original_target_index']==r['index']]
 assert len(selected)==1
 return selected[0]
peak=at(rows,1.2);oldpeak=at(oldrows,1.2);last=rows[-1]
common=[]
for d in (.5,.75,.8,.85,1.,1.2):
 a,b=at(oldrows,d),at(rows,d)
 common.append(dict(loading_d_mm=d,old_total_Fy_N=a['total_body_Fy_N'],new_total_Fy_N=b['total_body_Fy_N'],
  relative_change_percent=100*(b['total_body_Fy_N']/a['total_body_Fy_N']-1)))
docs=['docs/PROJECT_STATUS.md','docs/HF_FUNCTION_PROGRESS_20261004.md','docs/HF5_LF_V2_ADAPTER_AND_TASK_PLAN.md','docs/CURRENT_STATUS.md','hf_repo/README.md','docs/WORKPIECE_ENLARGEMENT_20261007.md']
doc_text={p:(ROOT/p).read_text(encoding='utf-8') for p in docs}
doc_snapshots={p:{'sha256':sha256(t.encode('utf-8')).hexdigest(),'raw_file_sha256':digest(p)} for p,t in doc_text.items()}
findings=[]
for path in ('docs/CURRENT_STATUS.md','docs/WORKPIECE_ENLARGEMENT_20261007.md'):
 for i,line in enumerate(doc_text[path].splitlines(),1):
  if ('4 mm' in line and '生产' in line and ('尚未执行' in line or '尚未开始' in line)):
   findings.append(dict(path=path,line=i,observed_excerpt=line,kind='dated_preparation_snapshot_is_outdated_for_live_status',
    proposed_action='Keep historical preparation record; use the latest dated running snapshot/current front. Parent reports new production started, not closed or independently qualified.'))
historical_scope_phrases=[]
for path in ('docs/CURRENT_STATUS.md','docs/HF_FUNCTION_PROGRESS_20261004.md'):
 for i,line in enumerate(doc_text[path].splitlines(),1):
  if any(s in line for s in ('再推进优化接口','HF5 优化耦合','接回优化流程')):
   historical_scope_phrases.append(dict(path=path,line=i,excerpt=line,interpretation='Historical/dated text, not a new missing-HF-optimizer requirement. Future front should say external LF/N4 same-task evaluation interface.'))
matrix=[
 dict(function='实际结构变形和完整加载卸载',implemented='NumPy平均输入控制、自由输出、保存每个接受态和回零；实际×1图/GIF',qualified='2mm固定方体24态全路径机械参考通过；卸载是固定工件任务，不是自由体释放',remaining='更一般工况按自身完整路径评价'),
 dict(function='固定工件受力及节点力位置',implemented='输入R、q_out、lower-body材料/Hu/总(Fx,Fy)、holding与全节点力',qualified='2mm全部接受态完整力、离散平衡与有符号工件投影；声明PORT方向切线作用',remaining='连续压力、有效接触/稳定夹持判据与独立物理精度；不把2|Fy|当净力'),
 dict(function='结构/介质场和有限距离显示',implemented='保存F/J/Hu、Green主应变、有限底/左面射线和最近距离',qualified='保存数据binary64诊断与限定固体/工件几何观察；原9点Lobatto含角点J门',remaining='应变/应力HP、一般自身重叠/包含与signed penetration；这些图不是压力'),
 dict(function='独立普通输入和HF派生域',implemented='自包含几何+显式task/native Q1、LFv2适配、右介质列追加API/CLI及物理映射',qualified='2mm全过程；4mm仅已经关闭的准备/布局资格，生产仍未闭合',remaining='可用的一次评价接口整理和相同设计/任务网格政策；资格不随域继承'),
 dict(function='真实机构机械计算',implemented='材料/Hu/总内力、三切线、非对称CSC/KKT、显式port_projection可选初猜',qualified='原声明方向、全部单元/真实DOF、装配和平均约束；不穷举全切线列',remaining='广义状态和边界适用范围；不以拒绝trial或旧前缀借资格'),
 dict(function='材料能量/压力/安全',implemented='旧能量和应力字段入口存在；当前机械模式能量明确not_evaluated',qualified='当前工件任务无辅助能量/压力/应力HP或材料安全资格',remaining='需要时补明确物理定义及对应验证，不阻塞已可用机械功能'),
 dict(function='圆体、自由工件及摩擦',implemented='固定圆形单元覆盖构造入口已有',qualified='没有本次圆体完整边界/平衡资格；工件全部ux/uy固定',remaining='圆体自身任务；若探索自由体，增加平移/旋转/力矩平衡与相应接触/滑移定义'),
 dict(function='HF5研究评价闭环',implemented='LF/N4优化/生成/评分上游已存在；HF单任务正向后端可用',qualified='当前少量指定任务证据，不是候选总体排名或批量标签资格',remaining='共同有效域/任务与网格政策、小批量一致入口/响应/失败标签/来源/重复性；HF不重写优化器')
]
report=dict(schema_version='hf-physical-progress-source-proposal-1.0',status='source_proposal_saved_only',
 recorded_utc=datetime.now(timezone.utc).isoformat(),intended_document='docs/HF_PHYSICAL_PROGRESS_20261008.md',
 objective='Independent forward evaluator from self-contained LF/N4 geometry and explicit physical task; observable deformation/force and scoped validity; HF5 same-task candidate evaluation for the external research layer, no HF optimizer.',
 closed_basis='right_margin_cycle_001 actual2mm full evidence',input_json_pins={p:digest(p) for p in paths.values()},document_snapshots=doc_snapshots,
 closed_evidence=dict(accepted_states=24,HP80_120_calls=48,checks_completed=476733,force_scope=reference['reference_scope'],peak=peak,unloaded=last,
  regularization_Fy_ratio_new_to_zero_margin=peak['regularization_body_Fy_N']/oldpeak['regularization_body_Fy_N'],
  max_Hu_ratio_new_to_zero_margin=peak['medium_max_abs_Hu_per_mm']/oldpeak['medium_max_abs_Hu_per_mm'],common_original_loading_targets=common),
 current4mm=dict(status='parent_reported_running_not_closed_or_independently_qualified',new_production_result_read=False,new_HP_or_full_view_qualification=False,
  explanation='Live prefix is not a complete path or independent qualification. No live scientific files or arrays read by reviewer.'),
 functionality_matrix=matrix,documentation_findings=findings,historical_scope_phrase_notes=historical_scope_phrases,
 interpretation='Current latest2mm front and report distinguish forward evaluation from external optimization, weak on-body force from net force/pressure, and Green/Hu from pressure. No new pressure or optimizer implementation requirement inferred from dated historical text.',
 next_fork=[
  'New production not closed or failed: preserve actual prefix/error, diagnose its specific source and scope; no speculative complete PASS, force extrapolation or old-card restart.',
  'Production complete but reference fails: resolve actual reference/schema/numerical discrepancy; no qualification borrowed from 2mm or relaxed gates.',
  'New full production plus own allactualN fresh2N reference PASS: render its actual states and compare matching leg/original-target R,q_out,Fx,Fy material/Hu,gap/J/shape/unload, including early approach region and absolute small-force scale.',
  'If2-to4 results are materially boundary-dependent across path/components: keep h/material/body fixed and choose one further margin or separate alpha study from actual data; no peak-only convergence assertion.',
  'If fullpath changes become small under an explicit physical tolerance: choose4mm provisionally and do one matched same-design mesh refinement; two domains alone do not establish asymptotic convergence or pressure accuracy.',
  'Concurrently improve ease of use with one documented forward entry returning compact responses, saved-view links and scoped success/failure. Build a small external LF/N4/HF5 candidate comparison at the fixed-square validated scope before adding circles/free bodies/more physics; no new optimizer or sprawling defensive layer.'
 ],
 activity=dict(HF_imports=0,NPZ_array_reads=0,model_constructors=0,F_T_solver_HP_calls=0,geometry_nodal_plot_calls=0,formal_writes=0))
(OUT/'physical_progress_review.json').write_text(json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
md='''# HF物理功能进度（文档提案，2026-10-08）

这份提案的功能目标是：给定普通几何和明确任务，独立显示夹持器真实变形、输入力、固定工件受力及卸载过程，供外部LF/N4研究层比较候选。HF正向功能已经可用；整体研究评价闭环/HF5还未完成，HF本身不重写优化器。

目前可人工检查的完整基准是**2 mm右介质余量**的固定方体：side18、中心(71,40) mm，E1 MPa、厚20 mm、h1 mm，γ=α=1e-6、Lr80 mm，24目标0→1.2→0 mm全部完成，24态的48次新HP80/120和476733检查通过。4 mm新路径已开始但尚未闭合；它没有新全路径参考或完整变形视图资格。实时前缀只说明实际进展，不能预测峰值或最终PASS。

| 用户能看到/使用的功能 | 已实现与已有资格 | 仍缺的实际功能或适用范围 |
|---|---|---|
| 结构作用与变形 | 平均输入、自由输出、真实×1结构/GIF、逐接受态加载与回零；2 mm完整机械路径通过 | 更多工况自己的完整证据；固定工件卸载不等于自由体释放 |
| 工件受力及力的位置 | 输入R、材料/Hu/总(Fx,Fy)、holding及全节点力；完整力/装配/平衡/工件投影与声明PORT方向切线作用通过 | 压力、接触/有效夹持定义、自由物体稳定性；没有全切线列资格 |
| 距离和场图 | 有限面距离/射线、保存J/Hu、Green主应变；原9点Lobatto含角点J门 | 应变/应力HP、一般包含/自身重叠及signed penetration；这些场图不是压力 |
| 可搬迁输入与域处理 | 自包含LFv2几何、显式task、原生Q1和HF派生介质域；4 mm准备/布局已完成 | 同设计网格政策、统一的一次评价入口；新域不继承旧机械资格 |
| 更一般夹持 | 固定方体已完成；固定圆单元覆盖入口已有 | 圆体自身完整边界/平衡、自由刚体平移/旋转/力矩平衡、摩擦/滑移 |
| HF5比较与易用 | 上游LF/N4优化/评分已有，HF单任务后端可用 | 同任务/共同有效域的小批量评价、单位/失败标签/来源/重复性与研究接口 |

2 mm加载峰态d=1.2 mm，输入反力R=0.407199455 N，输出q_out=1.008865416 mm，下半工件Fy=0.119231670 N，2|Fy|=0.238463339 N，钳尖有限底面距离5.716672637 μm。回零Fy约−5.03e−25 N，距离回到1 mm；这是实际保存的小量，没有人为归零。

Fy是当前全部节点被固定的下半工件弱式on-body力，holding反向。镜像双侧法向幅值和2|Fy|与完整装配净力(2Fx,0)分别报告；q_out是加权端口位移，不是尖端间隙。当前模型在有限正间隙下通过受压第三介质传力，这已经能分析受力和变形，但不证明精确硬接触、连续压力或自由工件稳定夹持。Green来自保存F的binary64派生，不扩大为应变HP或材料安全；Hu场量也不等于Hu力分量。旧能量入口存在，当前机械模式明确不计算辅助材料能量，不把它说成整个能量代码缺失。

原0→2 mm峰值总Fy只增0.1883%，但正则化Fy增至约4.267倍（Hu场最大值只增约0.0576%），较早加载0.75–0.85 mm总Fy增约22–32%。因此下一判断必须看同方向、同原目标的整条曲线及材料/Hu分量和绝对量，不能用峰值近似不变声称域收敛。

下一步先闭合4 mm实际路径及其全部实际N态的新2N参考，再显示完整保存态。若早期和峰值力/分量/间隙仍有明显边界效应，保持h、材料与工件不变，依据数据选择一次更多余量或单独α因素；若整条路径在明确物理容差下趋稳，暂选4 mm并做一次同设计匹配细网格。2与4两个点也不能单独证明渐近收敛。若生产/参考失败，先按实际错误排查，不扩大旧卡或推断未完成段。

易用性可与物理检查并行推进：把已有普通输入→一次正向评价→紧凑响应/失败原因→保存图链接整理成清楚的接口，先做已验证固定方体范围的小批量外部候选比较。无需在HF重建LF优化器，也无需为了接口堆叠新的防御层或镜像测试；圆体、自由体等功能随后依据用户关心的实际效果增加。

人工检查入口（拟安装在docs/时的仓库相对路径）：[×1结构与节点力](../functional_views/right_margin_20261007/complete_001/view/comparison.png)、[力和距离曲线](../functional_views/right_margin_20261007/complete_001/view/distances_forces.png)、[J/Hu与实体应变](../functional_views/right_margin_20261007/complete_001/view/peak_fields.png)、[2 mm实际24态动画](../functional_views/right_margin_20261007/complete_001/view/right2col/actual_states.gif)。本提案只读已关闭JSON和文档，0新HF/数组读取/求解/HP/几何观察/绘图或正式仓库写入。
'''
(OUT/'PHYSICAL_FUNCTION_PROGRESS_PROPOSAL.md').write_text(md,encoding='utf-8')
print(json.dumps({'status':'source_proposal_saved_only','review_sha256':sha256((OUT/'physical_progress_review.json').read_bytes()).hexdigest(),'proposal_sha256':sha256((OUT/'PHYSICAL_FUNCTION_PROGRESS_PROPOSAL.md').read_bytes()).hexdigest(),'documentation_findings':len(findings)},ensure_ascii=False))
