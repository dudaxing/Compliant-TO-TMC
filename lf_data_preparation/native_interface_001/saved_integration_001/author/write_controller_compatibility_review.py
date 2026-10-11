"""Source/AST compatibility report only; no HF imports, NPZ or tests."""
import ast
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
EXT = Path('D:/hf-native-workpiece-api-author-20261012/MINTEGRATE1_preparation_001')
STAGE = ROOT / 'lf_data_preparation/native_interface_001/saved_continuation_001'
CAND = STAGE / 'candidate/hf_repo'
BASE = 'd45f6ee92d8a0d6ca740772a1762abdc691489fa'


def pin(path):
    assert path.suffix != '.npz'
    return sha256(path.read_bytes()).hexdigest()


def tree(path):
    return ast.parse(path.read_bytes(), filename=path.as_posix())


def funcs(parsed):
    return {node.name:node for node in parsed.body if isinstance(node, ast.FunctionDef)}


def dump(node):
    return ast.dump(node, include_attributes=False)


current_split_path = ROOT / 'hf_repo/src/hf_eval/split_displacement.py'
candidate_split_path = CAND / 'src/hf_eval/split_displacement.py'
current_mean_path = ROOT / 'hf_repo/src/hf_eval/native_mean.py'
candidate_mean_path = CAND / 'src/hf_eval/native_mean.py'
old_split, new_split = funcs(tree(current_split_path)), funcs(tree(candidate_split_path))
old_mean, new_mean = funcs(tree(current_mean_path)), funcs(tree(candidate_mean_path))
old_control, new_control = old_split['solve_split_displacement_path'], new_split['solve_split_displacement_path']
old_nested, new_nested = funcs(old_control), funcs(new_control)
old_native_nested, new_native_nested = funcs(old_mean['solve_native_mean']), funcs(new_mean['solve_native_mean'])
unchanged = {}
for name in ('_dot','split_average_measurement'):
    assert dump(old_split[name]) == dump(new_split[name])
    unchanged['split_displacement.'+name] = True
for name in ('clock','evaluate','split_state','impose','feasible','measure','metrics','step','advance'):
    assert dump(old_nested[name]) == dump(new_nested[name])
    unchanged['controller.'+name] = True
newton = deepcopy(new_nested['newton'])
check_loop = next(node for node in newton.body if isinstance(node, ast.For))
removed = [node for node in check_loop.body if isinstance(node, ast.If) and 'initial_parameter' in dump(node.test)]
assert len(removed) == 1
check_loop.body.remove(removed[0])
assert dump(newton) == dump(old_nested['newton'])
unchanged['controller.newton_after_removing_single_nonzero_anchor_guard'] = True
for name in ('_plain','_workpiece_observations','write_native_mean'):
    assert dump(old_mean[name]) == dump(new_mean[name])
    unchanged['native_mean.'+name] = True
assert dump(old_native_nested['assemble']) == dump(new_native_nested['assemble'])
unchanged['native_mean.assemble'] = True
capture = deepcopy(new_native_nested['capture'])
removed_capture = [node for node in capture.body if isinstance(node, ast.If) and dump(node.test) == dump(ast.parse('anchor is not None', mode='eval').body)]
assert len(removed_capture) == 1
capture.body.remove(removed_capture[0])
assert dump(capture) == dump(old_native_nested['capture'])
unchanged['native_mean.capture_after_removing_saved_index_annotation'] = True

reviewed = {}
for path in (current_split_path,candidate_split_path,current_mean_path,candidate_mean_path,
             CAND/'src/hf_eval/native_resume.py', ROOT/'hf_repo/src/hf_eval/displacement.py',
             ROOT/'hf_repo/src/hf_eval/native_project.py', ROOT/'hf_repo/src/hf_eval/split_state.py',
             ROOT/'hf_repo/src/hf_eval/split_numpy_tangent.py', ROOT/'hf_repo/src/hf_eval/split_kernel_invariants_hu.py',
             CAND/'tests/test_saved_native_resume.py', ROOT/'hf_repo/tests/test_split_displacement.py',
             ROOT/'hf_repo/tests/test_split_cycle.py', ROOT/'hf_repo/tests/test_native_mean.py',
             ROOT/'hf_repo/tests/test_native_mean_mechanical.py', STAGE/'run_001/focused_test_receipt.json',
             STAGE/'production_launch.json'):
    if path.suffix == '.py':
        tree(path)
    reviewed[path.relative_to(ROOT).as_posix()] = pin(path)
historical_reference_protocol = ROOT/'lf_data_preparation/native_interface_001/nested_reference_002/protocol.json'
reference = json.loads(historical_reference_protocol.read_bytes())
reviewed[historical_reference_protocol.relative_to(ROOT).as_posix()] = pin(historical_reference_protocol)
candidate_production_names = {path.relative_to(CAND).as_posix() for path in CAND.rglob('*.py') if 'tests' not in path.relative_to(CAND).parts}
changed_reference_sources = set(reference['reference_sources']) & {'hf_repo/'+name for name in candidate_production_names}
assert changed_reference_sources == set()
actual_tests = json.loads((STAGE/'run_001/focused_test_receipt.json').read_bytes())
actual_outer = json.loads((STAGE/'production_launch.json').read_bytes())
assert actual_tests['status'] == actual_outer['status'] == 'pass'
test_inventory = {path.relative_to(ROOT).as_posix():[node.name for node in tree(path).body if isinstance(node,ast.FunctionDef) and node.name.startswith('test_')]
                  for path in (CAND/'tests/test_saved_native_resume.py', ROOT/'hf_repo/tests/test_split_displacement.py',
                               ROOT/'hf_repo/tests/test_split_cycle.py', ROOT/'hf_repo/tests/test_native_mean.py',
                               ROOT/'hf_repo/tests/test_native_mean_mechanical.py')}

review = {
    'status':'pass_static_controller_default_compatibility_and_minimal_integration_review_no_new_execution',
    'created_utc':datetime.now(timezone.utc).isoformat(), 'base_commit':BASE,
    'candidate_origin':'Published M-RESUME1 isolated package and actual execution; production default core remains old',
    'authorized_new_science':False, 'executed_new_science':False, 'formal_core_mutated_by_reviewer':False,
    'reviewed_repository_SHA256':reviewed, 'AST_unchanged_function_evidence':unchanged,
    'zero_default_branches': [
        {'source':'candidate/hf_repo/src/hf_eval/split_displacement.py:77', 'judgment':'Default p0=0 adds only finite scalar input validation. Old settings, load_only start0, ordered_cycle start0/unload/end-before-peak constraints, supports, lift/shape and callbacks remain.'},
        {'source':'candidate/hf_repo/src/hf_eval/split_displacement.py:110', 'judgment':'At p0=0, expected warm lift is lift_origin.copy(), preserving the old bitwise comparison including signed zero. Cold state, fluctuation, R, state_s=0 and K=None match the prior branch; no display or algebra rebase is introduced.'},
        {'source':'candidate/hf_repo/src/hf_eval/split_displacement.py:238', 'judgment':'Initial p0=0 leaves the nonzero strict-anchor guard inactive. Existing parameter-zero warm state still follows normal Newton/corrector semantics, including wrong-R checking and arbitrary nonzero lift_origin/target_origin cases; it is not accidentally changed to validate-only.'},
        {'source':'candidate/hf_repo/src/hf_eval/split_displacement.py:350', 'judgment':'p0=0 still emits origin/loading/unloading and no initial_parameter result key. Advance/line-search/bisection/cache commitment AST are unchanged. Timings and provenance bytes are not promised equal after integration.'},
        {'source':'candidate/hf_repo/src/hf_eval/native_mean.py:134', 'judgment':'Without saved_result, valid old explicit settings remain required, None options resolve complete/full/tangent, declared task target equality is retained, no anchor reader/defaults run, and source_hashes retain the four old key labels.'},
        {'source':'candidate/hf_repo/src/hf_eval/native_mean.py:183', 'judgment':'Force/tangent selector, three-component assembly, full unsymmetrized CSC cache, state-hash capture, data copies/read-only arrays, workpiece observations and cached writer AST remain; saved-index annotations and continuation metadata are inactive for zero-start.'},
    ],
    'explicit_interface_changes_not_numerical_regressions': [
        'native_mean settings keyword is now optional syntactically to enable restoration. A missing zero-start setting is rejected by TMCError invalid_settings rather than Python missing-keyword TypeError.',
        'Explicit None options now request defaults, whereas old native_mean rejected None modes; omitted options still resolve to the same old complete/full/tangent values.',
        'Source-file SHA fields and saved result descriptor hashes necessarily change for new runs after installation. This is correct new provenance; do not promise byte-identical whole result JSON or rewrite historical identities.',
    ],
    'mathematical_and_cache_contract': {
        'residual':'r = fint + kout*bout*qout - bin*R, with qout from compensated split measurement.',
        'augmented_system':'[[Kff+kout*bout_f*bout_f^T, -bin_f], [bin_f^T,0]] [dw,dR] = [rhs_force,rhs_mean]; general sparse LU, no symmetry enforcement.',
        'predictor':'rhs_force = -(K*DeltaL+kout*bout*Deltaqout)_free; rhs_mean is negative compensated current split mean minus target_origin and absolute s. port_projection substitutes only displacement seed, while predictor dR remains applied with its original sign.',
        'corrector':'rhs_force=-r_free, rhs_mean=-constraint residual; R is signed actuator_on_model multiplier and is neither clipped nor inverted on descent.',
        'saved_anchor':'Nonzero p0 requires ordered_cycle, mandatory saved state and first target=p0. Expected lift uses original binary64 impose expression. Initial K=None; fresh F/T must pass original residual/mean/J gates, or initial_state_not_equilibrated occurs before correction/commit. The one guard is the only AST change within Newton.',
        'rollback':'Original advance preserves state arrays/R/s/committed-K on unaccepted Newton attempts. Capture holds independent immutable arrays/tangent/matrix copies matched by state hash. Later trial last_tangent does not overwrite prior durable accepted snapshot. Post-accept callbacks/time can already have committed observations.',
        'reader':'Exact full original task/suffix, geometry/model/grid/material/BC/counts and saved settings/options except time; selected original accepted nonzero row and split archive identities. It reuses no old force/tangent/CSC and checks the two unchanged mechanics-kernel source SHA before fresh evaluation.',
        'source_limits':'Public reader deliberately supports original zero-lift ordered-cycle parents only, original target rows with at least one remaining target, exact full-task suffix. It does not support another continuation child, arbitrary target extension, an inserted bisection anchor, load_only saved resume, load control or movable-body contact.',
    },
    'existing_evidence_scope': {
        'M_RESUME1_actual_outer_status':actual_outer['status'],
        'five_focused_actual_test_receipt_status':actual_tests['status'],
        'distinction':'Those published runs validate the isolated package and one actual1.20→1.15 fixed-square segment. They do not replace validation of the installed default package/import/CLI or all old controller cases. No new test was run here.',
        'M_REF2_reference_source_closure_intersection_with_changed_production_paths':sorted(changed_reference_sources),
        'reference_note':'Actual M-REF2 reference_sources do not include these seven installed paths; its archived11-source HP reference capsule can retain historical status if those unchanged files remain. Older production protocol pins still describe their old executed sources and must remain unchanged, not be relabeled as current source equality.',
    },
    'minimal_integration_recommendation': [
        'Install the exact reviewed seven production files as one coherent change: six existing entry/controller/response/CLI files plus native_resume.py. Add the exact focused test. Do not independently reimplement a new controller or partially install native_mean without its reader/API/response/CLI companions.',
        'Leave force/tangent kernels, native_project, displacement/KKT, data and split-state arithmetic unchanged. Retain archived candidate, baseline snapshots, actual results/cards/protocol/source provenance and qualified reference records.',
        'Document opt-in saved mode, parent/child scope, exact original suffix, explicit new time and reader limitations. Keep no-argument/ordinary zero-start branch the default and retain current producer/HP/pressure/stability/HF5 flags.',
        'Prepare a small bounded installed-package regression selection using existing meaningful controller/NativeMean/public tests, then run only under separately specified test authorization/resource scope. No long full loading or another13440-cell solve is required merely to copy the already validated source.',
    ],
    'real_risks_to_verify_in_later_tests': [
        {'risk':'Default p0=0 controller compatibility, especially affine nonzero origin/shape, signed zero and target_origin', 'existing_tests':['test_nonzero_lift_predictor_does_not_advance_the_physical_mean_twice','test_split_weighted_mean_retains_product_error_and_hidden_fluctuation','test_warm_start_is_independently_checked_and_failure_preserves_two_arrays_and_R','test_default_loading_contract_is_unchanged_and_cycle_bounds_are_explicit']},
        {'risk':'No accidental symmetrization/port/R sign change and ordinary bounded trials/rollback', 'existing_tests':['test_nonsymmetric_kkt_and_rank_one_output_spring_match_dense_equations','test_average_port_keeps_unequal_node_motion_and_actuator_sign','test_descending_failure_bisects_and_retains_original_unloading_leg','test_nonlinear_armijo_and_bounded_trial_rejection_keep_last_accepted_state']},
        {'risk':'Installed package imports, default complete and explicit mechanical/full/chunk256 paths, caching and partial persistence', 'existing_tests':['test_task_mean_control_builds_once_and_leaves_individual_port_nodes_free','test_accepted_state_force_and_full_tangent_package_roundtrips','test_mechanical_cycle_omits_energy_and_saves_cached_full_dof_data','test_mechanical_partial_path_preserves_failure_and_cached_origin','test_invalid_tangent_mode_is_rejected_before_building']},
        {'risk':'Installed public saved-entry option inheritance and exact parent preservation/strict anchor failure/rollback', 'existing_tests':actual_tests['collected_nodeids'], 'caution':'Dynamic collection must use installed default source, not unintentionally import old overlay. Fifth test is real16-cell NumPy/TMC and its F/T must be acknowledged, distinct from original13440-cell path counts.'},
        {'risk':'CLI parser/default and relative saved-input handling', 'existing_tests_scope':'The prior card exercised API, not candidate CLI process. Source addition does not prove CLI runtime behavior; any future selected CLI test belongs explicitly in its test card, without an unsolicited new large solve.'},
    ],
    'test_source_inventory':test_inventory,
    'blockers_to_source_integration_preparation':[],
    'not_a_completion_claim':'Default core installation and installed regression are not performed here. No all-column HP, generic-input, pressure, effective clamp, mesh/parameter stability, full unload or HF5 claim.',
    'actions':{'candidate_or_HF_import':0,'NPZ_read_or_decode':0,'tests':0,'force_tangent_HP_solver':0,
               'new_scientific_values':0,'plots':0,'formal_write':0,'Git_mutations':0},
}
json_path = EXT/'controller_compatibility_review.json'
md_path = EXT/'CONTROLLER_COMPATIBILITY_REVIEW.md'
assert not json_path.exists() and not md_path.exists()
json_path.write_text(json.dumps(review,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
md_path.write_text('''# 保存态续算正式集成：控制器兼容性静审

基线main `d45f6ee92d8a0d6ca740772a1762abdc691489fa`。未见阻止源码集成准备的问题。建议一次安装M-RESUME1已审、已实测的7份production源与原新增测试，保持力核、切线、构模、KKT和split运算不变；不另外编写一套续算算法。当前只读源码／普通JSON并比较AST，没有安装、运行测试或新科学计算。

`initial_parameter=0` 时，原load_only／ordered_cycle边界、初始双数组／R／K=None、signed-zero warm lift身份、原Newton校正、origin/loading/unloading角色和默认结果schema保留。新strict-anchor guard仅对非零p0开放。AST证实原 compensated `_dot`／measurement、clock／evaluate／impose／feasible／measure／metrics／step／advance未改；Newton除该一个guard外相同。NativeMean assembler、缓存状态SHA门及复制、workpiece观察和writer也保留，saved索引注释只在anchor分支执行。

mean约束仍由两数组补偿计算，增广矩阵的右上块为−b_in，左下块为+b_inᵀ，普通非对称LU。predictor保持负力与负mean RHS，port_projection只替换位移seed而保留dR；R继续表示actuator_on_model的signed乘子。未接受attempt回滚和此前复制的接受缓存保留；接受后callback／时钟异常仍可能已有有效接受态。

非零锚点仍需ordered_cycle、saved state和首绝对target=p0，初始K=None、fresh F/T原门直接合格；失败在correction／commit前停止。reader继承精确原task／suffix、settings／options（仅clock变化）、模型材料／BC和双位移身份，只检查并复用原两个机械kernel源，不读取原force／tangent／CSC。范围仍限原zero-lift完整ordered父路径中的original目标；不支持从child继续、任意extend、bisection anchor或load-only保存态。

兼容性措辞需精确：新的显式None选项代表默认，缺zero-start settings以invalid_settings拒绝，旧入口的缺参TypeError／无效None处理并非完全原样。安装后新运行的source SHA／descriptor字节必然更新，不能承诺整个result JSON逐字节相同；这不是数值算法回归。历史cards／protocol／baseline／已存results不得改写成新源身份。已核M-REF2的实际11份reference_sources不包含本次7个安装路径，可保留其历史资格与未改参考源；旧production pins仍描述原执行。

后续真正需验证的是安装后的默认import与原分支：非零affine lift／target_origin及signed-zero、mean补偿、非对称KKT／R符号、trial／二分／rollback、complete／mechanical与full／chunk256缓存／partial保存、五项saved public测试，以及若选择的CLI解析。已有测试可复用。M-RESUME1实际五项通过和13440单元首次下降证明的是隔离包，不自动替代安装包回归；第5测试会产生真实16-cell F/T。应在独立明确的测试范围与资源合同下再运行，不为源码安装重跑长加载。

逐项来源SHA、AST等价证据、现有测试名和限制见 [controller_compatibility_review.json](controller_compatibility_review.json)。本报告没有新增预算／验收门，也不证明全列HP、任意输入、压力、有效夹持、稳定性、完整卸载或HF5。
''',encoding='utf-8')
print(json.dumps({'status':review['status'],'JSON_sha256':pin(json_path),'MD_sha256':pin(md_path),
                  'reviewed_files':len(reviewed),'AST_equal_functions':len(unchanged),'new_science':False}))
