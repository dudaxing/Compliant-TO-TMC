"""Interpret existing ordinary saved records and already viewed PNGs; no science."""
from datetime import datetime, timezone
from hashlib import sha256
import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
REL = 'lf_data_preparation/native_interface_001/saved_continuation_001'
STAGE, RUN = ROOT / REL, ROOT / REL / 'run_001'
sources = {}

def pin(path):
    value = sha256(path.read_bytes()).hexdigest()
    sources[path.relative_to(ROOT).as_posix()] = value
    return value

def read(path):
    pin(path)
    return json.loads(path.read_bytes())

protocol = read(STAGE / 'protocol.json')
outer = read(STAGE / 'production_launch.json')
helper = read(RUN / 'execution_receipt.json')
result = read(RUN / 'resumed_alpha_half/result.json')
response = read(RUN / 'resumed_alpha_half/response.json')
model = read(RUN / 'resumed_alpha_half/model/model.json')
tests = read(RUN / 'focused_test_receipt.json')
view = read(RUN / 'view/view.json')
summary = read(RUN / 'view/resumed_alpha_half/summary.json')
pin(STAGE / 'M-RESUME1_CARD.md')
csv_file = RUN / 'view/resumed_alpha_half/states.csv'
pin(csv_file)
with csv_file.open(encoding='utf-8', newline='') as stream:
    csv_rows = list(csv.DictReader(stream))
nodes_file = RUN / 'view/resumed_alpha_half/nodes.csv'
pin(nodes_file)
with nodes_file.open(encoding='utf-8', newline='') as stream:
    node_rows = list(csv.DictReader(stream))
assert outer['status'] == helper['status'] == view['status'] == tests['status'] == 'pass'
assert result['status'] == response['status'] == summary['production_status'] == 'success'
assert outer['exit_code'] == 0 and outer['stop_reason'] is None and outer['invocations'] == 1
assert outer['protocol_sha256'] == helper['protocol_sha256'] == sources[REL + '/protocol.json']
assert len(result['states']) == len(summary['rows']) == len(csv_rows) == 2
observations = []
for index, (row, values, text) in enumerate(zip(result['states'], summary['rows'], csv_rows)):
    assert row['state_sha256'] == values['state_sha256'] == text['state_sha256']
    assert row['d'] == values['d_mm'] == float(text['d_mm'])
    assert row['original_target_index'] == values['original_target_index'] == int(text['original_target_index'])
    assert row['leg'] == values['leg'] == text['leg']
    assert row['R_input'] == values['R_input_N'] == float(text['R_input_N'])
    assert row['q_out'] == values['q_out_mm'] == float(text['q_out_mm'])
    geometry = read(RUN / f'view/resumed_alpha_half/{index:03d}/geometry.json')
    boundary = geometry['regions']['boundary_intersections']
    for part in ('total', 'material', 'regularization'):
        assert row['workpiece']['force_on_lower_body_N'][part] == [values[part + '_body_Fx_N'],values[part + '_body_Fy_N']]
    observations.append(dict(index=index,original_target_index=row['original_target_index'],
        child_original_target_index=row['child_original_target_index'],leg=row['leg'],
        continuation_anchor=row['continuation_anchor'],state_sha256=row['state_sha256'],
        d_mm=row['d'],q_in_mm=row['q_in'],q_out_mm=row['q_out'],R_input_N=row['R_input'],
        lower_body_force_N=row['workpiece']['force_on_lower_body_N'],
        holding_reaction_on_model_N=row['workpiece']['holding_reaction_on_model_N'],
        cached_two_sided_normal_magnitude_sum_N=row['workpiece']['two_sided_normal_magnitude_sum_N'],
        geometry=dict(valid=geometry['geometry_valid'],
            raw_overlap=geometry['regions']['raw_interior_overlap'],strict_overlap=geometry['regions']['strict_interior_overlap'],
            roundoff_ambiguous=geometry['regions']['roundoff_ambiguous'],
            minimum_exposed_closed_region_boundary_distance_mm=boundary['minimum_boundary_distance_mm'],
            boundary_intersects=boundary['intersects'],boundary_scope=geometry['regions']['boundary_scope'],
            bottom_finite_face_first_ray_mm=geometry['faces']['bottom']['minimum_first_ray_hit_mm'],
            left_finite_face_first_ray_mm=geometry['faces']['left']['minimum_first_ray_hit_mm'],
            tip_to_bottom_unsigned_finite_segment_mm=values['tip_to_bottom_mm'],
            tip_to_right_unsigned_finite_segment_mm=values['tip_to_right_mm'],
            tip_x_mm=values['tip_x_mm'],tip_y_mm=values['tip_y_mm'],
            self_overlap_tested=geometry['regions']['mechanism_self_overlap_tested'],
            set_containment_tested=geometry['regions']['set_containment_tested']),
        existing_saved_fields=dict(solid_min_J=values['solid_min_J'],medium_min_J=values['medium_min_J'],
            solid_Green_principal_min=values['solid_Green_principal_min'],
            solid_Green_principal_max=values['solid_Green_principal_max'],
            medium_max_abs_Hu_per_mm=values['medium_max_abs_Hu_per_mm'],whole_max_abs_Hu_per_mm=row['max_abs_Hu_per_mm']),
        existing_production_checks=dict(newton_checks=row['newton_checks'],relative_residual=row['relative_residual'],
            constraint_residual_mm=row['constraint_residual'],constraint_bound_mm=row['constraint_bound'],
            relative_global_force_balance=row['relative_global_force_balance'])))
images = {}
for name in ('comparison.png','distances_forces.png','peak_fields.png'):
    path = RUN / 'view' / name
    images[name] = dict(path=path.relative_to(ROOT).as_posix(),sha256=pin(path),actual_existing_pixels_viewed=True)
continuation = result['continuation']
assert response['continuation'] == continuation
assert continuation['parent_status'] == 'failed' and continuation['parent_failure']['code'] == 'time_limit'
assert continuation['parent_path_completed'] is continuation['parent_unload_endpoint_reached'] is False
assert result['full_original_path_completed'] is result['task_target_executed'] is False
assert continuation['anchor_revalidated'] is continuation['anchor_identity_preserved'] is True
assert observations[0]['state_sha256'] == continuation['selected_state']['state_sha256']
value = dict(status='pass_existing_saved_results_physical_functional_interpretation_only',
    recorded_utc=datetime.now(timezone.utc).isoformat(),card='M-RESUME1',
    executed_new_science=False,actual_execution_status='pass',source_commit=helper['approved_source_commit'],
    protocol_sha256=helper['protocol_sha256'],reviewed_existing_repository_SHA256=sources,
    scope='Ordinary saved JSON/CSV and three existing PNG pixel views only; no new scientific evaluation',
    physical_task=dict(grid=model['grid'],material=model['material'],workpiece=model['task']['workpiece'],
        task_sha256=model['task_sha256'],requested_segment_targets_mm=result['targets_mm'],
        original_task_targets_mm=continuation['original_task_targets_mm']),
    actual_segment=dict(accepted_states=2,original_target_indices=[13,14],
        fresh_anchor_revalidated=continuation['anchor_revalidated'],anchor_identity_preserved=continuation['anchor_identity_preserved'],
        segment_completed=continuation['segment_completed'],unload_endpoint_reached=result['unload_endpoint_reached'],
        original_parent_status='NOT_PASS',parent_status=continuation['parent_status'],parent_failure=continuation['parent_failure'],
        parent_path_completed=False,parent_unload_endpoint_reached=False,full_original_path_completed=False,task_target_executed=False),
    actual_saved_observations=observations,
    interpretation=dict(
        progress='Saved-state public continuation was functionally exercised on the original gripper: preserved peak anchor, first descending original target accepted, cached persistence and pure display completed.',
        response='At descending mean1.15mm the stored positive input R and positive lower-body Fy are smaller than at the recovered1.20mm peak; stored q_out is slightly smaller and finite bottom distance slightly larger.',
        force_sign='Input R is actuator-on-model. Lower-body weak resultant positive Fy points upward toward the symmetry plane; negative Fx points left. Holding reaction on model opposes it. Visual mirrored upper Fy is reflected, not another solved body.',
        force_components='Reported total/material/Hu regularization are signed assembled weak-force resultants over all fixed-body DOFs, including cut/interior nodes; cancellation remains possible. They are not continuous boundary pressure or already qualified grip force.',
        magnitude='cached_two_sided_normal_magnitude_sum_N is the saved2|lower Fy| magnitude sum; it is neither full-body net Fy nor an independent clamping qualification.',
        geometry='Stored exposed-region minimum boundary distance and finite bottom ray/selected-tip distance agree here and stay positive; they slightly increase on unload. No stored region overlap/intersection. Closed-region boundary includes symmetry cut; self-overlap and set containment were not tested.',
        fields='Very small positive medium J indicates severe third-medium compression near the small gap; positivity and cached residual convergence do not establish physical stability or independent accuracy. Whole maximum Hu component and viewer free-medium norm plot are different measures.',
        convergence='One full-factor first Newton trial was rejected for invalid_J, then factor0.5 passed the original line search. Final descent accepted after8checks with no target bisection. The recoverable trial is not a second launch or terminal retry.',
        limits='Two saved endpoints support this local continuation result; they do not establish a continuous unload curve, hysteresis, a full unload to zero, arbitrary new LF task qualification or global stability.'),
    existing_cached_production_gate_record=helper['cached_production_gates'],
    actual_accounting=dict(production=helper['counts'],result_call_counts=result['call_counts'],
        production_hook_scope=helper['mechanical_hook_scope'],test_status=tests['status'],
        test_scope=tests['scope'],test_mechanical_calls='Not separately hooked; not asserted zero or mixed into production counts',
        failed_target_attempts=result['path_diagnostics']['failed_attempts'],
        maximum_bisection_depth=result['path_diagnostics']['maximum_bisection_depth'],
        existing_trials=result['path_diagnostics']['trials']),
    actual_cost_records=dict(outer=dict(elapsed_seconds=outer['elapsed_seconds'],peak_sampled_tree_RSS_bytes=outer['peak_sampled_tree_RSS_bytes'],
        exit_code=outer['exit_code'],stop_reason=outer['stop_reason'],scope='Whole helper and real terminal exit; sampled tree RSS'),
        helper=dict(elapsed_seconds=helper['elapsed_seconds'],peak_sampled_RSS_bytes=helper['peak_sampled_RSS_bytes'],scope=helper['elapsed_scope']),
        controller=result['path_diagnostics']['timing_seconds'],native_entry=result['timing_seconds'],
        focused_test_plugin=dict(elapsed_seconds=tests['elapsed_seconds'],peak_sampled_RSS_bytes=tests['peak_sampled_RSS_bytes']),
        focused_test_child=helper['focused_tests_terminal'],view_child=helper['view_child_terminal'],
        raw_view=dict(elapsed_seconds=view['elapsed_seconds'],sampled_peak_RSS_bytes=view['sampled_peak_RSS_bytes']),
        RSS_note='Helper records own sampled RSS/available peak working set; outer samples current process-tree RSS. Different scopes can yield a slightly larger helper record; neither is an OS hard memory cap.'),
    actual_visualization=dict(images=images,manual_pixel_findings=dict(
        comparison='Actual PEAK0/resume_origin1.20 and LAST1/unloading1.15 show nearly unchanged overall shape at x1; the zoom places the gripper tip just below the fixed square bottom near its right corner. Force curves show the smaller unload R and lower-body Fy. Orange distances and green rays are geometry, not forces.',
        distances_forces='Saved left-tip distance dominates the distance axis; the near-zero bottom gap is not visually resolvable at this axis scale. Fx remains signed negative; the numerical table provides the small gap.',
        peak_fields='Actual recovered-peak lower-half plots show solid Green field, free-medium mean J and Hu Frobenius norm. The free-medium compression near the body is visible; these colors do not prove pressure or stability.'),
        geometry_calls=2,nodal_calls=2,node_CSV_data_rows=len(node_rows),
        GIF_frames_from_existing_helper_record=helper['actual_GIF_frames'],GIF_manually_decoded_or_rendered=False,
        mechanical_hooks_monitored=view['mechanical_hooks_monitored'],new_mechanics_basis=view['zero_mechanics_basis'],
        distance_scope=view['distance_scope'],strain_scope=view['strain_scope'],mirroring=view['mirroring']),
    qualifications=dict(new_independent_HP=False,HP_all_columns=False,contact_pressure_clamping=False,
        physical_stability=False,HF5=False,arbitrary_new_LF_task_qualified=False,
        response_producer_flags=response['producer_flags'],independent_reference=response['independent_reference'],
        source_scope='Candidate overlay executed in new run/source/hf_repo; formal default core remains original. API continuation works for this preserved-task suffix; default integration/other tasks are future decisions.'),
    review_limits=['No NPZ field decode or independent state/force/tangent recomputation.',
        'No new F/T/HP/solver/test/observer/integral/difference/plot/GIF rendering.',
        'Cached gates were read as saved records; this interpretation is not independent numerical-reference qualification.',
        'Pure viewer mechanical_hooks_monitored=false is not dynamic mechanical hook monitoring.',
        'No claim that all parent archive bytes were reread; actual selected bindings preserved by existing outer/helper records.'],
    reviewer_actions=dict(HF_import=0,candidate_import=0,NPZ_decode=0,force=0,tangent=0,HP=0,solver=0,tests=0,observer=0,
        scientific_integral=0,new_scientific_difference=0,plot=0,GIF_render=0,existing_PNG_pixels_viewed=3,formal_repository_write=0))
out = HERE / 'physical_results_review.json'
out.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')

a,b = observations
def fmt(number):
    return format(number,'.9g')
table = '\n'.join('| '+name+' | '+fmt(left)+' | '+fmt(right)+' |' for name,left,right in [
    ('输入 mean [mm]',a['d_mm'],b['d_mm']),('输入 R [N]',a['R_input_N'],b['R_input_N']),
    ('输出 q_out [mm]',a['q_out_mm'],b['q_out_mm']),
    ('下半工件 total Fy [N]',a['lower_body_force_N']['total'][1],b['lower_body_force_N']['total'][1]),
    ('下半工件 material Fy [N]',a['lower_body_force_N']['material'][1],b['lower_body_force_N']['material'][1]),
    ('下半工件 Hu Fy [N]',a['lower_body_force_N']['regularization'][1],b['lower_body_force_N']['regularization'][1]),
    ('下半工件 total Fx [N]',a['lower_body_force_N']['total'][0],b['lower_body_force_N']['total'][0]),
    ('保存的双侧竖向幅值和 [N]',a['cached_two_sided_normal_magnitude_sum_N'],b['cached_two_sided_normal_magnitude_sum_N']),
    ('有限底面 first ray [mm]',a['geometry']['bottom_finite_face_first_ray_mm'],b['geometry']['bottom_finite_face_first_ray_mm']),
    ('有限左面 first ray [mm]',a['geometry']['left_finite_face_first_ray_mm'],b['geometry']['left_finite_face_first_ray_mm']),
    ('tip至右侧有限线段无符号距离 [mm]',a['geometry']['tip_to_right_unsigned_finite_segment_mm'],b['geometry']['tip_to_right_unsigned_finite_segment_mm']),
    ('solid最小J',a['existing_saved_fields']['solid_min_J'],b['existing_saved_fields']['solid_min_J']),
    ('free medium最小J',a['existing_saved_fields']['medium_min_J'],b['existing_saved_fields']['medium_min_J'])])
md = f'''# M-RESUME1：实际首次下降的物理与功能解读

本卡实际 **PASS**，一次启动／exit0。保存峰值1.20 mm经fresh F/T重验后，原首次下降1.15 mm直接接受，共2态，无目标二分。公共保存态续算入口、原任务恢复、缓存保存及纯显示已在这个实际夹持器任务上得到功能验证。原M-ALPHA1父结果仍为NOT_PASS/time_limit；新子段success与原完整路径资格分别记录。

本解读只读取已有JSON/CSV并查看本次实际3PNG，不解码NPZ，不运行HF、测试、力核、切线、求解、HP、观察器或绘图。完整原存值与来源SHA见 [physical_results_review.json](physical_results_review.json)；表中数字仅作显示舍入。

## 实际响应

| 保存量 | 恢复峰值：原13／child0 | 首次卸载：原14／child1 |
| --- | ---: | ---: |
{table}

R为actuator-on-model输入反力；下半工件Fy为ON-body弱形式合力，正号向上、指向y=40 mm对称面，负Fx向左。卸载后R、total/material/Hu Fy均较峰值小，q_out略回退，底面记录间隙略增。holding reaction与工件作用相反；镜像上半Fy反号。幅值和2|lower Fy|不是完整工件净Fy，也不是已合格夹持力。

这些分量来自固定工件所有DOF的离散弱力，包含cut/interior节点；局部正负可抵消。材料与Hu总作用可用于检查响应，但不是连续接触压力、已验证的表面夹持力或其压力分布。当前固定square side18 mm、center(71,40)、h0.5、E1 MPa／nu0.3／plane strain／厚20 mm、gamma1e-6／alpha5e-7／Lr80 mm的任务保持。

## 形状、几何与场

实际comparison图中PEAK是新验证的恢复锚点，LAST是真实卸载终点；两者x1总体形状很接近，右侧尖端位于工件底面靠右角下方。保存bottom first ray、指定tip至有限底面距离以及exposed closed-region最小边界距离在本例两态各自一致，均为正且卸载后稍大。raw/strict overlap、边界intersection与roundoff ambiguous均为false。这是现有几何诊断；closed-region边界可能包含symmetry cut，未检查self-overlap或set containment，不能扩大为所有contact资格。

图中的橙色距离／绿色ray是几何，不是力。distances_forces的左侧tip距离约17.7 mm占据纵轴，小于0.002 mm的底隙在该轴上难以人工分辨，应看表值；不为改善显示新增绘图。peak_fields显示原恢复峰值的solid Green、free-medium meanJ及Hu Frobenius场。小间隙附近第三介质强压缩；保存medium minJ约2.3e-5虽为正，但J>0及残差通过不等于物理稳定性或独立准确性。图Hu范数与保存max_abs_Hu分量是不同量。

已实际查看 [comparison.png](../run_001/view/comparison.png)、[distances_forces.png](../run_001/view/distances_forces.png)、[peak_fields.png](../run_001/view/peak_fields.png) 的既存像素。已有2帧GIF未由本审阅重新解码／渲染；本审阅不声称已逐帧检查nodal箭头。

## 收敛及成本的含义

实际anchor只需1个检查，卸载8个检查。第一Newton full-factor trial因invalid_J被拒，随后factor0.5通过原line search，再沿原步进收敛；failed_attempts为空、max bisection depth0。这是授权控制器内可恢复trial，不是terminal重试或第二启动。生产F17started／16completed、T9／9，save和summary不新增F/T；5项局部测试独立通过，其中第5项有真实16-cell计算，不与13440-cell生产计数混合。cached原门通过，最大relative residual4.584773266448174e-12、最大global balance7.677910679556237e-14、fixed split sum0。这里只读取这些已有门记录，不重算验证。

outer真实全退出耗时{outer['elapsed_seconds']}秒，采样树RSS{outer['peak_sampled_tree_RSS_bytes']}B；helper写收据前成本快照{helper['elapsed_seconds']}秒、自身采样／可用peak working set {helper['peak_sampled_RSS_bytes']}B。controller记录{result['path_diagnostics']['timing_seconds']['total']}秒，view raw{view['elapsed_seconds']}秒；范围不同，不相加冒充单独求解时间。helper自身peak可略高于outer离散树采样，并不矛盾。原资源为合作检查／采样，非OS硬限。

纯viewer geometry／nodal各2次、节点CSV数据行{len(node_rows)}，3PNG／已有2帧GIF。其new mechanics0依据冻结纯导入来源与保存数组处理，mechanical_hooks_monitored=false；不能将false当动态hook已证明。API在显示前保存，所以response.views仍not_provided，图及同结果关联由单独实际view记录给出。

## 可继续的功能与尚未完成的资格

这一结果支持从已接受峰值保存态继续原suffix，且小幅卸载后反力与工件弱作用会回落。它消除了“必须重做长加载才能验证首次下降”的功能障碍，也表明原父time_limit本身不能被解读为卸载不可能。默认正式hf_repo尚未安装隔离候选；下一步可据本证据审查集成公共入口及原路径关联，不自动开启新参数扫描。

本次新alpha没有独立HP/all-column tangent参考；没有新压力／有效夹持／物理稳定性／HF5或任意新LF任务资格。一般API与保存显示已有功能，任意新几何／工况仍需要自身资格；square本例不能替代circle路径证据。两个接受端点不构成连续卸载曲线、完整回零或滞回证明；原父NOT_PASS及资格flag继续保留。
'''
(HERE / 'PHYSICAL_RESULTS_REVIEW.md').write_text(md,encoding='utf-8')
print(json.dumps(dict(status=value['status'],executed_new_science=False,
    report_sha256=sha256(out.read_bytes()).hexdigest(),
    markdown_sha256=sha256((HERE / 'PHYSICAL_RESULTS_REVIEW.md').read_bytes()).hexdigest()),indent=2))
