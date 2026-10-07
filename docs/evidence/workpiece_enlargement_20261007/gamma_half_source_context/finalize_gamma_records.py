"""Install current gamma records from completed saved evidence; no mechanics."""
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path('D:/hf-workpiece-enlarge-author-20261007')
EVIDENCE = ROOT / 'docs/evidence/workpiece_enlargement_20261007'
PREP = 'lf_data_preparation/native_workpiece_001/gamma_half_preparation_001'
CYCLE = 'lf_data_preparation/native_workpiece_001/gamma_half_cycle_001'
VIEW = 'functional_views/workpiece_gamma_20261007/complete_001'
BASE = 'lf_data_preparation/native_workpiece_001/enlarged_square_projection_001'
HEAD = '16ee4ebb67161e2c8bc9a27d8e44285308778171'

def read(name):
    return json.loads((ROOT / name).read_text(encoding='utf-8'))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

def selected(d, keys):
    return {k: d[k] for k in keys}

def identity(name):
    p = ROOT / name
    return {'path': name, 'bytes': p.stat().st_size, 'sha256': sha(p)}

def phase(receipt_name, launch_name, helper_limit, outer_limit, counts):
    receipt, launch = read(receipt_name), read(launch_name)
    assert receipt['status'] == launch['status'] == 'pass'
    assert launch['exit_code'] == 0 and launch['invocations'] == 1
    assert launch['all_bindings_unchanged']
    return {
        'status': 'pass', 'invocations': 1,
        'helper_seconds_limit': helper_limit, 'outer_seconds_limit': outer_limit,
        'sampled_RSS_limit_bytes': launch['sampled_RSS_limit_bytes'],
        'helper_elapsed_seconds': receipt['elapsed_seconds'],
        'outer_elapsed_seconds': launch['elapsed_seconds'],
        'helper_sampled_peak_RSS_bytes': receipt.get('sampled_peak_RSS_bytes', receipt.get('peak_sampled_helper_RSS_bytes', receipt.get('sampled_peak_helper_RSS_bytes'))),
        'tree_sampled_peak_RSS_bytes': launch['peak_sampled_tree_RSS_bytes'],
        'all_bindings_unchanged': True, 'counts': counts,
        'receipt': identity(receipt_name), 'launch': identity(launch_name),
    }

prep = read(PREP + '/run_001/preparation_receipt.json')
prod = read(CYCLE + '/run_001/execution_receipt.json')
ref = read(CYCLE + '/reference/summary.json')
view = read(VIEW + '/view/view.json')
cached = read(VIEW + '/view/gamma_comparison/cached_comparison.json')
assert prod['accepted_states'] == ref['accepted_states'] == cached['matched_states'] == 24
assert ref['HP_calls_started'] == ref['HP_calls_completed'] == 48
assert ref['checks_completed'] == 465255
assert view['geometry_completed'] == view['nodal_completed'] == 48
assert view['new_F_T_model_solver_HP_calls'] == cached['new_geometry_nodal_F_T_model_solver_HP_calls'] == 0
peaks = {name: read(VIEW + '/view/' + name + '/013/derived.json')['row'] for name in ('gamma1e6', 'gamma5em7')}
returns = {name: read(VIEW + '/view/' + name + '/023/derived.json')['row'] for name in peaks}
matched = list(csv.DictReader((ROOT / (VIEW + '/view/gamma_comparison/matched_states.csv')).open(encoding='utf-8')))
early = []
for row in matched:
    if row['leg'] == 'loading' and float(row['d_mm']) in (.75, .8, .85):
        old, new = float(row['gamma1e6_total_body_Fy_N']), float(row['gamma5em7_total_body_Fy_N'])
        early.append({'d_mm': float(row['d_mm']), 'baseline_Fy_N': old, 'gamma_half_Fy_N': new, 'relative_change_percent': 100 * (new - old) / old})
old, new = peaks['gamma1e6'], peaks['gamma5em7']
differences = {
    'peak_Fy_change_percent': 100 * (new['total_body_Fy_N'] - old['total_body_Fy_N']) / old['total_body_Fy_N'],
    'peak_R_change_percent': 100 * (new['R_input_N'] - old['R_input_N']) / old['R_input_N'],
    'peak_q_out_change_mm': new['q_out_mm'] - old['q_out_mm'],
    'peak_tip_bottom_gap_change_um': 1000 * (new['tip_to_bottom_mm'] - old['tip_to_bottom_mm']),
    'peak_medium_min_J_ratio': new['medium_min_J'] / old['medium_min_J'],
}
record = {
    'schema_version': 'gamma-half-physical-progress-1.1',
    'updated_utc': datetime.now(timezone.utc).isoformat(), 'baseline_commit': HEAD,
    'goal': 'Independent LF-data finite-deformation TMC forward response, workpiece forces and actual deformation observations; no HF optimization',
    'status': 'complete_current_gamma_milestone_project_incomplete',
    'authorization_basis': 'User authorized automated development and autonomous exploratory physical parameter choices. Independent new bounded windows were disclosed before execution; old closed cards and their qualifications remain closed.',
    'physical_delta': {'gamma_before': 1e-6, 'gamma_after': 5e-7, 'unchanged': 'E, nu, alpha, Lr, kr, body, geometry, mesh, ports, boundaries, targets, kernels and numerical gates'},
    'model_comparison': prep['model_comparison'],
    'model_identity': {'task_sha256': prod['task_sha256'], 'model_sha256': prod['model_sha256'], 'result_sha256': prod['result_sha256']},
    'preparation': phase(PREP + '/run_001/preparation_receipt.json', PREP + '/prepare_launch.json', 120, 150, selected(prep, ['invocations', 'model_constructions', 'model_writes', 'force_calls', 'tangent_calls', 'solver_calls', 'HP_calls', 'JIT_calls', 'LF_imports'])),
    'production': phase(CYCLE + '/run_001/execution_receipt.json', CYCLE + '/production_launch.json', 4500, 4560, {'accepted_states': 24, **prod['call_counts'], 'failed_loading_attempts': 0, 'bisections': 0, 'invalid_J_rejected_trials': 20, 'force_range_rejected_trials': 10, 'Armijo_complete_rejected_trials': 2, 'linear_solves': 179, 'linear_predictor_solves': 23, 'linear_corrector_solves': 156}),
    'reference': phase(CYCLE + '/reference/summary.json', CYCLE + '/reference_launch.json', 1500, 1560, selected(ref, ['accepted_states', 'HP_calls_started', 'HP_calls_completed', 'checks_completed', 'candidate_force_calls', 'tangent_calls', 'solver_calls', 'model_constructions'])),
    'view': phase(VIEW + '/view/phase_view.json', VIEW + '/view_launch.json', 180, 210, {'geometry_observations': 48, 'nodal_observations': 48, 'matched_original_targets': 24, 'GIF_frames_per_case': 24, 'new_F_T_model_solver_HP_calls': 0, 'extra_cached_geometry_nodal_calls': 0}),
    'peak_rows': peaks, 'return_rows': returns, 'peak_differences': differences,
    'early_loading_Fy_differences': early,
    'force_definitions': {'input_R': 'Half-model generalized input force N', 'lower_fixed_body': 'Signed weak-form (Fx,Fy) N; total = material + Hu regularization', 'mirrored_normal_magnitude_sum': '2 abs(Fy) N, not net force', 'mirrored_net_force': '(2 Fx,0) N', 'nodal': 'Weak nodal forces, not point pressure'},
    'reference_qualification': ref['qualification'],
    'production_qualification_flags_unchanged': 'Original flags remain false; independent reference summary admits only its explicit accepted mechanical-state scope.',
    'visualization_scope': 'Saved binary64 F/weak forces and finite-segment geometry; strain fields not HP qualified, mirrored upper half not newly solved. Root inspected the five PNG plots and actual peak GIF frame; each GIF metadata has 24 frames.',
    'plot_limit': 'The original GIF long header is clipped at the right edge; case/index/d/x1 and three component labels remain readable. Production-only header describes the original saved production flags; fresh reference is separate.',
    'interpretation': 'Peak Fy differs 0.3254%, early weak-force loading differs 42-43%; two gamma values do not show convergence. Medium min J nearly halves but finite tip gap decreases only 0.1652 um. No scaling of force or gap is assumed.',
    'next_stage': 'Same physical coordinates and baseline gamma1e-6, add right-medium analysis-domain margin without LF reoptimization or resampling; preserve Lr80/alpha/E/native h1/physical masks and ports. Rebuild DOF/direction and select tip by coordinate. Source feasibility only so far: no padded model or mechanics has run.',
    'remaining_project_capabilities': ['Domain/grid/gamma/alpha sensitivity and contact/pressure criterion', 'Circular and movable workpieces, release and local compliance exploration', 'HF5 same-task connection to retained LF/N4 research layer'],
    'budget_limit_meaning': 'Cooperative clocks and sampled RSS, not OS hard memory caps; every new phase closed after a single invocation.',
    'figures': {name: VIEW + '/view/' + name for name in ['comparison.png', 'distances_forces.png', 'peak_fields.png', 'gamma_comparison/matched_force_gap.png', 'gamma_comparison/matched_differences.png', 'gamma1e6/actual_states.gif', 'gamma5em7/actual_states.gif']},
}
write(EVIDENCE / 'gamma_half_progress.json', record)

tail = r'''## 同一工件的 gamma 单因素对照（已完成）

在完成较大靠右方体的24态路径后，最近一项检查第三介质材料刚度敏感性。原峰态材料Fy约占总Fy的99.84%，尖端间隙仅5.70 μm、介质minJ约3.24e-5，参数对传力的影响需要实际计算。保持同一个中心(71,40) mm、边长18 mm、右面x80的固定方体以及E=1 MPa、ν=.3、厚度20 mm、1 mm网格、α=1e-6、Lr=80 mm，唯一物理改变为γ=1e-6→5e-7。gamma只缩放介质Lamé系数；它不软化夹持器实体E、不改变Hu系数kr。新模型27字段中仅gamma/lam/mu变化，其他24字段以及原几何字节一致。

新阶段从零态独立求解，24/24原目标0→1.2→0 mm完成，0失败加载尝试、0额外二分态。随后所有24态分别执行新HP80/120：48/48完成，465255项检查通过；没有借用原γ的48次资格。完整保存观察与视图通过，两个工况共48次几何和48次节点力观察；24对原目标按加载/卸载方向、原目标索引和实际输入精确匹配，不插值，不用二分或近邻态替代。每个动画均为24个真实接受态；缓存差值图增加的几何/节点/FE/HP调用都是0。

| 同一加载d=1.2 mm | γ=1e-6 | γ=5e-7 |
|---|---:|---:|
| 半模型输入R N | 0.4071352773 | 0.4069115631 |
| 输出qout mm | 1.0088870461 | 1.0092589318 |
| 下半固定工件Fx N | -0.002831894489 | -0.002748209853 |
| 单侧总Fy N | 0.1190075723 | 0.1186203116 |
| 材料Fy N | 0.1188180648 | 0.1184321379 |
| Hu Fy N | 0.000189507512 | 0.000188173677 |
| 双侧法向幅值和2\|Fy\| N | 0.2380151447 | 0.2372406231 |
| 钳尖有限底边距离 μm | 5.700752324 | 5.535554895 |
| 介质min J | 3.239841274e-5 | 1.656546086e-5 |
| 实体min J | 0.9758561788 | 0.9758432334 |
| 自由介质max\|Hu\| /mm | 0.2086300295 | 0.2103604776 |
| 全实体最大面内Green主应变 | 0.03282012891 | 0.03281101720 |

gamma减半后，峰值Fy下降0.3254085%，输入R下降0.0549484%；输出变化+0.000371886 mm。介质minJ降为原值的51.13%，**尖端间隙只减小0.165197 μm，并没有减半**。在早期加载0.75/0.8/0.85 mm，Fy分别下降41.92%/43.33%/43.37%，因此峰值接近不能推广为整条路径不敏感。相同可用输入处加载/卸载Fy相差约5.5e-11 N以内，与本次可逆弹性分支一致，不证明全局唯一性。新回零R=8.6949e-25 N、qout=-4.7531e-24 mm、Fy=-7.9703e-28 N；相对残差9.1652e-10在原门内。各态保存几何均无已测结构/工件内部重叠或舍入模糊。

![同输入处力、间隙、J及Hu对照](../functional_views/workpiece_gamma_20261007/complete_001/view/gamma_comparison/matched_force_gap.png)

![真实×1整体和局部变形](../functional_views/workpiece_gamma_20261007/complete_001/view/comparison.png)

[gamma减半后的真实24帧动画](../functional_views/workpiece_gamma_20261007/complete_001/view/gamma5em7/actual_states.gif)、[原gamma真实24帧动画](../functional_views/workpiece_gamma_20261007/complete_001/view/gamma1e6/actual_states.gif)、[逐目标差值](../functional_views/workpiece_gamma_20261007/complete_001/view/gamma_comparison/matched_differences.png)、[距离与水平力分量](../functional_views/workpiece_gamma_20261007/complete_001/view/distances_forces.png)、[共同色标的峰态场](../functional_views/workpiece_gamma_20261007/complete_001/view/peak_fields.png)。五张PNG与实际峰态动画帧已人工核对；原动画长标题右端被截断，工况/索引/d/×1和三分量标签仍可读。动画的production-only标题对应未改写的原生产资格flags，新参考资格单独保存在summary。

| 新独立阶段 | helper/outer预算 秒 | helper/outer实际 秒 | 实际工作 |
|---|---:|---:|---|
| gamma模型准备 | 120 / 150 | 13.859 / 14.855 | 1构建/写出，0F/T/求解/HP |
| 新生产 | 4500 / 4560 | 1915.959 / 1917.021 | 368/338F，180/180T，1求解，0HP；24原目标 |
| 全状态新参考 | 1500 / 1560 | 471.034 / 472.306 | 24态、48HP、465255检查；0候选F/T/构建/求解 |
| 完整保存观察与缓存对照图 | 180 / 210 | 27.729 / 28.453 | 48几何+48节点观察；24配对，0新力学/HP |

全部新阶段各启动一次并已关闭，各自8 GiB采样RSS窗口；生产helper/outer峰560902144/561414144字节，参考423976960/428068864字节，视图388284416/386215936字节。采样时点不同，不能据此要求helper峰等于tree峰；合作时钟与RSS不等于OS硬限制。生产窗口根据原2839.981秒×1.5+90上取整为4500，参考根据原716.989秒×1.5+90取1500，均在执行前明确；旧卡的剩余时间没有复用。新运行耗时更短但未控制机器条件，不能归因于gamma。

368次F中180个Newton基态、188个线搜索试探；156个试探接受，2个完整Armijo拒绝，20个invalid_J及10个范围异常未完成，均由原线搜索恢复。179次LU=23预测+156校正；首次范围试探为本次ordinal339，原ordinal325及1817项纯计数证明仍明确属于旧阶段。拒绝试探没有获得力学资格。核心24文件、方程、默认内核、J/Armijo/收敛门及原worker字节未改；只复用24核心源与2个必要包装源，未复制70源历史胶水。视图在冻结前修正原目标筛选与最终输出哈希资源检查，两项没有改变原观察器数学实现。

单侧Fy与2|Fy|仍为固定工件弱式合力报告；完整镜像净力为(2Fx,0)，节点力不是点压力。独立参考限本24态机械完整力、已声明PORT方向切线作用、组装、平衡与工件投影；全列切线、辅助能量、应力/应变HP、精确硬接触、压力与自由工件稳定夹持不在资格内。保存应变/间隙是binary64观察，两点gamma对照不是参数收敛。工件右面x80与域边界一致，零右侧介质余量依然存在。

接下来先以原γ=1e-6的同物理坐标任务检查右侧第三介质余量，保持LF原80×40数据、网格h=1、工件/端口/支撑、E、α、Lr=80；新增明确的HF派生分析域及parent SHA，不修改LF固定契约、不重新优化或重采样。节点/DOF和方向须重建、背景对称线须延伸，钳尖改按(80,30)坐标选择。现阶段只完成源码可行性核查，没有生成padding模型、卡或求解。之后依据实际结果推进网格/alpha、接触与压力定义、圆体/可动工件及局部柔顺性，再接HF5/LF-N4。整个项目尚未完成。

[本次执行卡](../lf_data_preparation/native_workpiece_001/gamma_half_cycle_001/EXECUTION_CARD.md)保留冻结时点的计划状态；[最终阶段与成本JSON](evidence/workpiece_enlargement_20261007/gamma_half_progress.json)给实际终态，[gamma资料索引](evidence/workpiece_enlargement_20261007/gamma_half_source_context/INDEX.md)保留原意见、包装差异和审查时间点。新结果身份8199bbf6…、新模型85e3f1e1…；原较大工件及失败阶段证据均保留。
'''
old_report = subprocess.check_output(['git', 'show', HEAD + ':docs/WORKPIECE_ENLARGEMENT_20261007.md'], cwd=ROOT)
current = (ROOT / 'docs/WORKPIECE_ENLARGEMENT_20261007.md').read_bytes()
assert current.startswith(old_report), 'Preserve prior report before replacing the live gamma tail'
banner = '当前更新：gamma单因素24态/48次新HP已通过；最新结果和下一步见本文末节。下面此前扩大工件阶段保留原始时间点说明。\n\n'
(ROOT / 'docs/WORKPIECE_ENLARGEMENT_20261007.md').write_bytes(banner.encode('utf-8') + old_report + b'\n' + tail.encode('utf-8'))

context = EVIDENCE / 'gamma_half_source_context'
context.mkdir(exist_ok=True)
sources = [
    'gamma_half_preparation_independent_static_review.json',
    'final_physical_data_review.json', 'review_final_physical_data.py',
    'padding_domain_source_review_20261007.md',
    'next_physical_stage_opinion.md', 'next_physical_stage_opinion.json',
    'physical_parameter_order_source_review.json', 'review_physical_parameter_order.py',
    'gamma_half_reference_candidate/README.md',
    'gamma_half_reference_candidate/author_note.json',
    'gamma_half_reference_candidate/gamma_half_reference_static_review.json',
    'gamma_half_reference_candidate/audit_enlarged_square.py.diff',
    'gamma_half_reference_candidate/reference_contract_builder.py.diff',
    'gamma_half_reference_candidate/baseline_wrappers/audit_enlarged_square.py',
    'gamma_half_reference_candidate/baseline_wrappers/reference_contract_builder.py',
]
records = []
for name in sources:
    src, dst = AUTHOR / name, context / name
    assert src.is_file(), name
    dst.parent.mkdir(parents=True, exist_ok=True)
    data = src.read_bytes()
    if dst.exists():
        assert dst.read_bytes() == data, name
    else:
        dst.write_bytes(data)
    records.append({'path': name, 'bytes': len(data), 'sha256': sha(dst)})
write(context / 'raw_manifest.json', {'schema_version': 'gamma-source-context-1.0', 'scope': 'Raw author/review/timepoint context; no execution or scientific qualification inherited', 'files': records})
index = '# gamma 单因素作者和审查资料\n\n这些是原始字节的时间点资料，不是新的执行授权。早期意见中的待批准/待执行，以及保存数据审查中的参考运行中，均保留原记录；最终实际状态见[gamma阶段JSON](../gamma_half_progress.json)。正式运行源码、协议和输出位于gamma_half_preparation_001、gamma_half_cycle_001和workpiece_gamma_20261007/complete_001。\n\n'
index += '\n'.join('- [' + x['path'] + '](' + x['path'] + ')' for x in records) + '\n\n[原字节清单](raw_manifest.json)。仅保留必要小包装/差异和说明，没有复制历史大胶水目录。padding文档仅为源码路线核查，没有运行新物理任务。\n'
(context / 'INDEX.md').write_text(index, encoding='utf-8')
print(json.dumps({'status': 'records_installed', 'progress': identity('docs/evidence/workpiece_enlargement_20261007/gamma_half_progress.json'), 'report': identity('docs/WORKPIECE_ENLARGEMENT_20261007.md'), 'raw_context_files': len(records), 'new_mechanics_HP_observations': 0}, ensure_ascii=False))
