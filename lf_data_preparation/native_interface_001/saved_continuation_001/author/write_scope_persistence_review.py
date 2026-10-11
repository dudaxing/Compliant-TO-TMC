"""Source and ordinary saved-descriptor audit; no project imports or arrays."""
import ast
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
EXT = Path(__file__).resolve().parent
BASE = '01b5078acaf76fdaabfbdf214da9db16056467bc'
REL = 'lf_data_preparation/native_interface_001/regularization_sensitivity_001'
DIRECTORY = ROOT / REL / 'run_001/alpha_half'
sha = lambda raw: sha256(raw).hexdigest()
read = lambda path: json.loads(path.read_bytes())
git = lambda *args: subprocess.check_output(['git', '-c', 'gc.auto=0', *args], cwd=ROOT)
assert git('rev-parse', 'HEAD').decode().strip() == BASE
source_names = [
    'hf_repo/src/hf_eval/native_mean.py', 'hf_repo/src/hf_eval/native_evaluate.py',
    'hf_repo/src/hf_eval/native_project.py', 'hf_repo/src/hf_eval/native_map.py',
    'hf_repo/src/hf_eval/native_batch.py', 'hf_repo/src/hf_eval/native_response.py',
    'hf_repo/src/hf_eval/native_force.py', 'hf_repo/src/hf_eval/split_displacement.py',
    'hf_repo/src/hf_eval/split_state.py', 'hf_repo/src/hf_eval/project.py',
    'hf_repo/src/hf_eval/tmc.py', 'hf_repo/src/hf_eval/data.py',
    'hf_repo/src/hf_eval/displacement.py', 'hf_repo/scripts/evaluate_native.py']
source_sha = {}
for name in source_names:
    raw = (ROOT / name).read_bytes()
    ast.parse(raw.decode('utf-8'), filename=name)
    source_sha[name] = sha(raw)
result = read(DIRECTORY / 'result.json')
model = read(DIRECTORY / 'model/model.json')
state = read(DIRECTORY / 'accepted/013/state.json')
geometry = read(DIRECTORY / 'model/source_geometry/geometry.json')
assert result['status'] == 'failed' and result['failure']['code'] == 'time_limit'
assert result['accepted_states'] == len(result['states']) == 14
assert state['original_target_index'] == 13 and state['leg'] == 'loading'
assert state['d'] == state['physical_mean_target_mm'] == state['q_in'] == 1.2
assert state['target_origin'] == result['target_origin'] == 0.0
assert state['R_input'] == 0.37865427196005513
assert state['state_sha256'] == state['assembler_state_sha256'] == 'fa0054288cd7eca4140f8bf04a94b5f833278b1c6e39813beb57cae16d7e9bca'
row = result['states'][13]
assert {k: v for k, v in row.items() if k not in ('descriptor_path', 'descriptor_file_sha256')} == state
assert row['descriptor_path'] == 'accepted/013/state.json'
assert row['descriptor_file_sha256'] == sha((DIRECTORY / row['descriptor_path']).read_bytes())
assert result['model']['descriptor_file_sha256'] == sha((DIRECTORY / 'model/model.json').read_bytes())
assert result['model']['descriptor_sha256'] == model['descriptor_sha256']
assert model['task_sha256'] == result['task_sha256'] == model['region_metadata']['effective_boundary']['task_sha256']
assert model['task']['path']['targets_mm'] == result['targets_mm']
assert result['targets_mm'][13:] == [1.2, 1.15]
assert model['task']['geometry'] == {key: geometry[key] for key in ('geometry_id', 'descriptor_sha256')}
assert geometry['arrays']['sha256'] == model['source_geometry']['arrays_sha256']
assert sha((DIRECTORY / 'model/source_geometry/geometry.json').read_bytes()) == model['source_geometry']['descriptor_file_sha256']
assert state['state_representation'] == 'split_displacement_v1'
assert state['response_mode'] == result['response_mode'] == 'mechanical'
assert state['tangent_execution'] == result['tangent_execution']
assert set(state['state']['fields']) == {'lift', 'fluctuation'}
assert all(info['shape'] == [27378] and info['dtype'] == 'float64' for info in state['state']['fields'].values())
assert set(geometry['arrays']['fields']) == {'solid', 'design', 'passive_solid', 'passive_void'}
assert all(info['shape'] == [80, 168] and info['dtype'] == 'uint8' for info in geometry['arrays']['fields'].values())
manifest = read(ROOT / 'handoff/repository_manifest.json')
manifest_rows = {entry['path']: entry for entry in manifest['files']}
array_plan = [
    {'path': REL + '/run_001/alpha_half/model/source_geometry/geometry.npz',
     'descriptor_source': REL + '/run_001/alpha_half/model/source_geometry/geometry.json',
     'sha256': geometry['arrays']['sha256'], 'fields': geometry['arrays']['fields'],
     'role': 'Existing native_project rebuild: authoritative source geometry four masks'},
    {'path': REL + '/run_001/alpha_half/accepted/013/state.npz',
     'descriptor_source': REL + '/run_001/alpha_half/accepted/013/state.json',
     'sha256': state['state']['sha256'], 'fields': state['state']['fields'],
     'role': 'Copy exact saved lift and fluctuation; never rounded display/rebase'}]
for archive in array_plan:
    assert manifest_rows[archive['path']]['sha256'] == archive['sha256']
    archive['published_manifest_bytes'] = manifest_rows[archive['path']]['bytes']
    archive['identity_checked_today'] = 'Descriptor and published manifest entry only; NPZ bytes and fields not read'
protocol = read(ROOT / REL / 'protocol.json')
outer = read(ROOT / REL / 'production_launch.json')
helper = read(ROOT / REL / 'run_001/execution_receipt.json')
assert all(sha((ROOT / name).read_bytes()) == pin for name, pin in result['mechanics_source_sha256'].items())
assert outer['status'] == helper['status'] == 'not_pass' and helper['cached_production_gates']['passed'] is True
ordinary_paths = [
    REL + '/run_001/alpha_half/result.json', REL + '/run_001/alpha_half/model/model.json',
    REL + '/run_001/alpha_half/accepted/013/state.json',
    REL + '/run_001/alpha_half/model/source_geometry/geometry.json',
    REL + '/protocol.json', REL + '/production_launch.json', REL + '/run_001/execution_receipt.json']
assert all(manifest_rows[name]['sha256'] == pin for name, pin in source_sha.items())
assert all(manifest_rows[name]['sha256'] == sha((ROOT / name).read_bytes()) for name in ordinary_paths)
report = dict(
    schema_version='M-RESUME1-source-scope-persistence-audit-1.0',
    status='pass_static_saved_peak_input_identity_persistence_and_public_entry_scope_audit_not_executed',
    created_utc=datetime.now(timezone.utc).isoformat(), source_baseline_commit=BASE,
    authorized=False, executed=False, preparation_only=True,
    published_manifest_sha256=sha((ROOT/'handoff/repository_manifest.json').read_bytes()),
    reviewed_source_SHA256=source_sha,
    reviewed_ordinary_records_SHA256={name: sha((ROOT / name).read_bytes()) for name in ordinary_paths},
    current_public_capability=dict(
        native_mean='Zero lift and undeformed initial state; exact task.path equality; no saved-start parameters',
        evaluate_native='One zero-start solve/write/summary; no resume; fresh directory; at least two targets',
        CLI='No resume-state/result/index flags; calls evaluate_native',
        batch='Shared options whitelist has no resume; first target must zero; task targets exact',
        low_level='Has warm split/R/lift/target_origin, but stage starts zero, is nonnegative, and K starts None',
        native_problem='No native_problem.py; native_project constructs Project/TMCModel and exact native BC/ports'),
    selected_parent=dict(result_status=result['status'], failure=result['failure'], accepted_states=14,
        path_completed=False, unload_endpoint_reached=False, task_target_executed=False,
        original_target_index=13, original_leg='loading', physical_mean_mm=1.2,
        R_input_N=state['R_input'], state_sha256=state['state_sha256'],
        state_descriptor_sha256=state['descriptor_sha256'],
        task_sha256=result['task_sha256'], geometry_identity=model['task']['geometry'],
        response_mode=result['response_mode'], tangent_execution=result['tangent_execution'],
        initial_guess=result['initial_guess'], settings=result['settings'],
        independently_HP_or_equilibrium_or_HF_qualified=False),
    minimal_future_input_scope=dict(
        ordinary_JSON=[name for name in ordinary_paths[:4]],
        selected_archive_plan=array_plan, NPZ_files=2, field_instances=6,
        excluded_NPZ=['model/model.npz', 'accepted/013/forces.npz',
            'accepted/013/tangents.npz', 'accepted/013/total_matrix.npz'],
        geometry_fields_loaded_by_existing_reader='solid/design/passive_solid/passive_void; all four authority masks',
        model_source='Rebuild existing native_project using saved source snapshot and exact embedded original task',
        no_external_LF_arrays_read=True, no_other_saved_states_needed=True,
        input_identity_future_validation='File SHA, declared field dtype/shape/C-order SHA, split hash, native model/BC/port/material/task identity; existing integrity checks, no new mechanical tolerance'),
    selected_fresh_cache_contract=dict(
        initial_K=None, saved_force_tangent_matrix_fields_decoded=False,
        fresh_F_T_anchor_validation_required=True,
        fresh_anchor='At exact saved split/R and absolute stage parameter1.20, existing residual/constraint/J/controller gates; then use its new cached tangent',
        cache_boundary='native_mean.capture only accepts last_tangent matching accepted state hash; copied accepted matrix is durable. A later trial updates last_tangent independently of committed controller state_K; failed trial is not accepted cache.',
        observed_accepted_matrix=dict(state_sha256=state['assembler_state_sha256'], descriptor=state['matrix'],
            reused=False, inspected='JSON metadata only; not independently validated or decoded'),
        rollback='Keep exact both split arrays/R/stage_parameter/committed K until successful advance. Original controller rollback tests state_K object identity, not an independent audit of K numeric contents.'),
    proposed_public_resume_contract=dict(
        entry='Dedicated saved-result/index continuation branch in API and CLI; batch remains zero-start unless separately explicitly extended',
        mandatory_arguments=['saved_parent_result', 'accepted_index=13', 'new_output_directory', 'explicit reviewed controller time limit'],
        absolute_targets_mm=[1.2,1.15], target_origin=0.0, initial_parameter=1.2,
        target_identity='Exactly parent targets_mm[13:] with original indices13/14; validate selected accepted row is original target. Preserve task/path bytes; suffix is a separate execution segment.',
        no_offset_subtraction_or_rebase=True,
        physical_identity='Same h0.5/84x40 lower-half grid, task canonical SHA, four source masks, fixed-body square18 centered71,40, E1/nu.3/plane strain/thickness20/gamma1e-6/alpha5e-7/Lr80, native ports and applied fixed/background BC.',
        algorithm_policy='Preserve mechanical response/chunk256/port_projection and all saved production tolerances/minimum_increment; only new resource allowance separately reviewed and approved',
        start_record='Freshly validated anchor is revalidated inherited start; child local index0 differs from parent original index13. Parent loading identity and child-origin role must be separately explicit.',
        new_endpoint='Child local index1 maps original target14 unloading1.15; any bisection is marked non-original and same parent target lineage',
        parent_preserved='Do not overwrite parent result/states, old failure/calls/time/qualification. Parent full15path stays NOT_PASS/unload false.',
        child_semantics='Child success/path completion/requested endpoint describe only the resumed suffix. Separate parent result SHA/state/task/source identity and parent full-path flags; do not silently upgrade original task_target_executed or full-path qualification.',
        time_scope='Fresh controller timer only; imports/read/rebuild/persist/summary and helper/outer complete elapsed separately recorded',
        persistence='Use existing cached accepted observations, no extra save force/tangent calls; new child output with inherited-start lineage. Anchor-validation failure leaves parent untouched and reports no falsely accepted unload.',
        qualification='No new HP/full-column/contact/pressure/clamp/stability/HF5 qualification; original global-balance/fixed production gates retain their existing definitions'),
    resource_estimate_basis=dict(
        peak_accepted=dict(elapsed_seconds=state['elapsed_seconds'], force_call=state['assembler_force_call'],
            tangent_call=state['assembler_tangent_call'], newton_checks=state['newton_checks']),
        neighboring_loading_accepted=[{k: s[k] for k in ('d','elapsed_seconds','assembler_force_call','assembler_tangent_call','newton_checks')} for s in result['states'][-3:]],
        original_controller_timing=result['path_diagnostics']['timing_seconds'],
        original_call_counts=result['call_counts'], original_project_preparation_seconds=result['timing_seconds']['project_preparation'],
        original_failed_attempts=result['path_diagnostics']['failed_attempts'][-1:],
        original_outer={k:outer[k] for k in ('status','elapsed_seconds','peak_sampled_tree_RSS_bytes','exit_code','stop_reason')},
        original_helper={k:helper[k] for k in ('status','elapsed_seconds','peak_sampled_RSS_bytes')},
        proposed_seconds=None, proposed_memory_limit=None,
        limits='Copied real cost/call observations only. Prior9000s timer included complete loading; first unload had little remaining budget and stopped by time_limit. This does not prove unload converges or guarantee1800/2400s. Fresh anchor adds new F/T; separate future card must bound controller/helper/outer and include persistence/cleanup. RSS samples are not OS caps.'),
    original_stage_gates=protocol['gates'],
    implementation_gaps=['Add explicit initial_parameter without changing original zero-start default',
        'Add selected saved-package integrity reader/API/CLI continuation contract',
        'Support exact task suffix while preserving full original task identity and local/global state indexing',
        'Carry continuation scope through result/response and avoid interpreting child completion as original full-path success',
        'Focused synthetic and actual descending-target validation still unexecuted; fresh anchor behavior not yet numerically demonstrated'],
    blockers_to_source_preparation=[],
    limits=['All array descriptors are declarations plus published manifest identities; no NPZ bytes/fields or matrix were read today.',
        'Source mechanics were read/AST parsed, not imported or executed. Descriptor correspondence is not a new force/tangent/equilibrium verification.',
        'No candidate implementation audit or execution claim is made here. Resource observations do not authorize an execution window.'],
    actions=dict(HF_or_candidate_imports=0, NPZ_byte_reads_or_decodes=0,
        scientific_tests=0, new_force_tangent_HP_equilibrium=0, new_observers_or_figures=0,
        formal_repository_mutations=0, git_mutations=0))
md = '''# 保存峰值下降续算：输入与持久化静查

当前 main 为 `01b5078acaf76fdaabfbdf214da9db16056467bc`。本轮仅准备，未授权或执行续算。父 M-ALPHA1 保持 NOT_PASS：14态至1.20 mm，首次卸载1.15 mm由时间预算停止。静查通过只表示输入声明和来源对应，不表示新入口已实现或数值通过。

公共 `solve_native_mean`、`evaluate_native`、CLI及batch仍为零起点。底层 controller 的warm参数存在，但stage首项必须0、非负，`state_K`初始None；直接传入峰值不能接续下降。`native_problem.py`并不存在；实际模型入口是 `native_project` 的 `Project/TMCModel`。

## 最小输入

| 已保存输入 | 未来解码字段 | 作用 |
| --- | --- | --- |
| model/source_geometry/geometry.npz | solid/design/passive_solid/passive_void，uint8(80,168) | 用既有native_project重建同一网格、task、材料及BC/ports |
| accepted/013/state.npz | lift/fluctuation，float64(27378)各一 | 保留两个原binary64数组，不用display、不rebase |
| result/model/state013/geometry JSON | 普通身份、task/settings/options/R及字段描述 | 绑定父路径、原target13和绝对目标suffix |

共2NPZ／6字段；不读model.npz、forces、tangents或total_matrix。state013原mean1.20 mm、R=0.37865427196005513 N、split SHA `fa0054288cd7eca4140f8bf04a94b5f833278b1c6e39813beb57cae16d7e9bca`，与result嵌入原记录逐项一致。数组身份今天只核声明和已发布manifest记录；实际读数组的完整性核查留给未来批准阶段。

## 推荐合同

采用绝对suffix `[1.20,1.15]`、`target_origin=0`、`initial_parameter=1.20`，避免通过offset差值构造新目标。保留原task15项及全部物理声明，以新segment单独指定原indices13/14。复用原mechanical/chunk256/port_projection及残差、约束、J、Armijo/bisection/minimum_increment；不增减机械门。

初始K=None，在原split/R处做一次fresh F/T anchor验证后接续原下降目标。原accepted matrix确有CSC(27378,27378)、486820nnz、未对称N/mm声明，但本次不复用。`capture`只保存与接受态hash一致的缓存；失败后临时`last_tangent`可能属于未接受trial。controller rollback只证明committed K对象仍在，不能称独立K数值审计。

子路径local index0/1须分别关联父target13/14；起点是重新验证的继承anchor，下降1.15才是新卸载接受目标。子段完成、endpoint与父完整路径状态必须分开传入result/response；父result、全部保存态、原failed/time/calls及资格不改。保存继续用已缓存新接受态，不因persistence另调用F/T。原HP/压力/夹持/稳定/HF5均不升级。

## 真实成本依据

峰值于8573.541880299992秒接受，F292/T120、9次Newton检查。原controller总9031.857919999995秒；kernel/transfer8850.413170600033秒，全部assembly尝试8995.9231345秒。最终F304 started／259 completed、T126；原唯一failed_attempt是1.20→1.15、time_limit、rollback=true。outer9059.673925399999秒，tree采样峰1401597952B；helper采样峰1420775424B。

这些只是原长加载和邻近接受态的真实观察，不能证明卸载必收敛，也不能保证1800/2400秒。新fresh anchor本身要产生F/T，controller/helper/outer及保存和清理应另审有限资源窗口。此文件不指定新额度，不授权数值测试。

源码依据：native_mean.py:113/145/178/256，split_displacement.py:55/114/303/318，native_evaluate.py:25，native_batch.py:68，native_response.py:174。完整SHA、输入描述、原门和成本原字段见同目录scope_persistence_review.json。本静查没有HF导入、NPZ读取、科学测试、绘图或正式仓库改动。
'''
for name, content in (
    ('scope_persistence_review.json', json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)+'\n'),
    ('SCOPE_PERSISTENCE_REVIEW.md', md)):
    out = EXT / name
    assert not out.exists()
    out.write_text(content, encoding='utf-8', newline='\n')
print(json.dumps(dict(status=report['status'], source_baseline_commit=BASE,
    JSON_sha256=sha((EXT/'scope_persistence_review.json').read_bytes()),
    MD_sha256=sha((EXT/'SCOPE_PERSISTENCE_REVIEW.md').read_bytes()),
    future_NPZ_files=2, future_fields=6, source_files=len(source_names)), ensure_ascii=False))
