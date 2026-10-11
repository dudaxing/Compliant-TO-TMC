"""Independent ordinary records/source/SHA review; no science imports or NPZ reads."""
import ast
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

EXT = Path('D:/hf-native-workpiece-api-author-20261011/MRESUME1_execution_review_001')
ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
REL = 'lf_data_preparation/native_interface_001/saved_continuation_001'
STAGE = ROOT / REL
RUN = STAGE / 'run_001'
BASE = '8b456dcdc2c0566fb2e927175a781712dd5e78ec'


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    assert path.suffix.lower() != '.npz', 'This reviewer never reads NPZ bytes'
    return sha256(path.read_bytes()).hexdigest()


def new_json(path, value):
    assert not path.exists()
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


receipt = read(EXT / 'delivery_tool_author_receipt.json')
tool_pins = {}
for name, value in receipt['sources'].items():
    assert name in ('deliver_execution.py', 'configure_execution_delivery.py')
    path = EXT / name
    assert sha(path) == value['sha256'] and len(path.read_bytes()) == value['bytes']
    ast.parse(path.read_bytes(), filename=name)
    tool_pins[name] = sha(path)
assert sha(EXT / 'DELIVERY_TOOL_SOURCE_NOTES.md') == receipt['notes_sha256']
tool_pins['DELIVERY_TOOL_SOURCE_NOTES.md'] = sha(EXT / 'DELIVERY_TOOL_SOURCE_NOTES.md')
tool_pins['delivery_tool_author_receipt.json'] = sha(EXT / 'delivery_tool_author_receipt.json')
tool = {
    'status': 'pass_static_execution_delivery_tools_not_executed',
    'created_utc': datetime.now(timezone.utc).isoformat(), 'card': 'M-RESUME1', 'source_commit': BASE,
    'executed_new_science': False, 'delivery_tools_executed_by_reviewer': False,
    'reviewed_external_SHA256': tool_pins, 'blockers': [],
    'findings': [
        'Both tools AST parse and import only standard-library metadata/process facilities; no candidate/HF/NumPy/solver/observer calls.',
        'configure requires completed real outer, actual closed documentation and independent pass-prefixed metadata reviews. It copies actual external bytes, validates pins/front history/links and creates exclusive config; it cannot launch numerical work or fabricate direct-human evidence.',
        'finalize requires exact staged allowed delta, no unstaged/untracked changes, main/origin and source BASE. Only new stage files and two fronts may differ; old18915 manifest entries are inherited, old43 stage records retained, science0.5.0 unchanged. Hashes for new delta are byte identities, not scientific validation.',
        'Delivery requires matching actual authorization/reply/source-publication/terminal identities. A terminal-review metadata PASS is separate from execution_status, including NOT_PASS; failed execution can preserve missing/partial/provisional helper and real existing artifacts without inventing views/results.',
        'Successful execution branch reuses saved helper/result/view records and unchanged parent flags. No fresh scientific gate, HP/pressure/clamp/stability/HF5 upgrade or run is introduced.',
        'verify requires actual separate commit/push/restore, same remote main commit and clean source/restore. It verifies new delta bytes and inherited entries without rescanning all old9.65GB or decoding arrays. Exclusive receipts prevent overwriting prior publication proofs.'
    ],
    'limits': ['Source/static review only; configure/finalize/verify were not run by this reviewer. Actual config, final review and publication receipts remain separately required.',
               'Future raw hashes of new archive files are permitted delivery metadata and are not NPZ decoding; this reviewer itself did not read any NPZ bytes.'],
    'actions': {'tool_execution': 0, 'HF_import': 0, 'candidate_import': 0, 'NPZ_read_or_decode': 0,
                'tests': 0, 'science': 0, 'plots': 0, 'formal_mutation': 0, 'Git_commit_push': 0},
}
new_json(EXT / 'execution_delivery_tool_static_review.json', tool)
(EXT / 'EXECUTION_DELIVERY_TOOL_STATIC_REVIEW.md').write_text('''# M-RESUME1 执行交付工具静审

两份实际工具源码及说明／收据已核 SHA 和 AST，未见阻断。该 PASS 仅是源码静审；没有运行 configure、finalize、verify、Git写操作或任何科学程序。

工具要求真实 completed outer、直接批准及发布身份、实际终态审阅、文档封账和最终增量审阅。数值 `not_pass` 也可以有通过的元数据封账；不会补造完整 helper／状态／图像。旧18915 manifest条目和43个原阶段文件继承，仅新增本阶段结果及两份front，完整旧front原字节保留一次。新文件哈希不构成科学资格。

成功分支复核已有记录，保留父原路径 NOT_PASS 与本次短段范围，不新增HP、压力、夹持、稳定性或HF5资格。commit／push／独立restore由root另行完成；verify检查远程main、source/restore clean和增量原字节，不重扫旧9.65GB。

冻结来源见 [execution_delivery_tool_static_review.json](execution_delivery_tool_static_review.json)。
''', encoding='utf-8')

protocol_file = STAGE / 'protocol.json'
protocol = read(protocol_file)
outer_file = STAGE / 'production_launch.json'
outer = read(outer_file)
helper_file = RUN / 'execution_receipt.json'
helper = read(helper_file)
tests = read(RUN / 'focused_test_receipt.json')
result_file = RUN / 'resumed_alpha_half/result.json'
result = read(result_file)
response_file = RUN / 'resumed_alpha_half/response.json'
response = read(response_file)
view_file = RUN / 'view/view.json'
view = read(view_file)
summary_file = RUN / 'view/resumed_alpha_half/summary.json'
summary = read(summary_file)
parent_file = ROOT / protocol['parent_result']
parent = read(parent_file)
parent_model_file = parent_file.parent / parent['model']['descriptor_path']
parent_model = read(parent_model_file)
auth_file = STAGE / 'author/authorization.json'
reply_file = STAGE / 'author/direct_human_reply.json'
auth, reply = read(auth_file), read(reply_file)
proof_file = STAGE / 'author/M_RESUME1_source_publication_receipt.json'
proof = read(proof_file)
assert outer['status'] == 'pass' and outer['exit_code'] == 0 and outer['stop_reason'] is None and outer['completed_utc']
assert outer['invocations'] == 1 and outer['all_bindings_unchanged'] is True
assert helper['status'] == 'pass' and helper['all_bindings_unchanged'] is True and helper['executed_source_package_unchanged'] is True
assert outer['protocol_sha256'] == helper['protocol_sha256'] == sha(protocol_file)
assert auth['authorized'] is True and auth['card'] == reply['card'] == protocol['card'] == 'M-RESUME1'
assert auth['authorization_from_direct_human_reply'] is reply['authorization_from_direct_human_reply'] is True
assert auth['approved_source_commit'] == reply['approved_source_commit'] == proof['published_commit'] == helper['approved_source_commit'] == BASE
assert auth['protocol_sha256'] == sha(protocol_file)
assert auth['human_evidence_sha256'] == helper['human_evidence_sha256'] == sha(reply_file)
assert auth['source_publication_receipt_sha256'] == sha(proof_file)
assert helper['authorization_sha256'] == sha(auth_file)
assert reply['direct_human_answer'].strip() and reply['reply_context'] and auth['direct_human_answer'] == reply['direct_human_answer']
assert outer['elapsed_seconds'] <= protocol['phases']['production']['outer_seconds']
assert helper['elapsed_seconds'] <= protocol['phases']['production']['helper_seconds']
assert outer['peak_sampled_tree_RSS_bytes'] <= protocol['sampled_RSS_bytes'] and helper['peak_sampled_RSS_bytes'] <= protocol['sampled_RSS_bytes']
assert tests['status'] == 'pass' and tests['exit_code'] == 0 and tests['stop_reason'] is None
assert tests['collected_nodeids'] == protocol['focused_test_nodeids']
assert len(tests['reports']) == 15 and all(row['outcome'] == 'passed' for row in tests['reports'])
assert {(row['nodeid'], row['when']) for row in tests['reports']} == {(node, phase) for node in protocol['focused_test_nodeids'] for phase in ('setup','call','teardown')}
assert helper['focused_tests_terminal']['exit_code'] == helper['view_child_terminal']['exit_code'] == 0
assert helper['focused_tests_terminal']['stop_reason'] is helper['view_child_terminal']['stop_reason'] is None
assert helper['focused_tests_terminal']['elapsed_seconds'] <= protocol['focused_tests_seconds']
assert helper['view_child_terminal']['elapsed_seconds'] <= protocol['view_seconds']
assert all(helper['counts'][kind + suffix] == 1 for kind in ('focused_tests','api','model','solve','save','summary','view_child') for suffix in ('_started','_completed'))
assert helper['call_counts'] == result['call_counts'] == response['call_counts']
for kind in ('force','tangent'):
    assert helper['counts'][kind + '_started'] == result['call_counts'][kind + '_calls']
    assert helper['counts'][kind + '_completed'] == result['call_counts'][kind + '_calls_completed']
assert helper['HP_calls'] == helper['JIT_calls'] == 0
assert helper['save_extra_force_tangent_calls'] == helper['summary_extra_force_tangent_calls'] == result['save_force_calls'] == result['save_tangent_calls'] == 0
assert helper['cached_production_gates']['passed'] is True
assert result['status'] == response['status'] == 'success' and result['failure'] is response['failure'] is None
assert helper['accepted_states'] == result['accepted_states'] == len(result['states']) == 2
assert result['path_completed'] is result['unload_endpoint_reached'] is True
assert result['targets_mm'] == protocol['targets_mm'] == [1.2,1.15]
assert result['settings'] == protocol['settings']
assert {key:value for key,value in parent['settings'].items() if key != 'time_limit_seconds'} == {key:value for key,value in result['settings'].items() if key != 'time_limit_seconds'}
assert result['task_sha256'] == parent['task_sha256'] and read(RUN / 'resumed_alpha_half/model/model.json') == parent_model
continuation = result['continuation']
assert response['continuation'] == continuation
assert continuation['segment_completed'] is continuation['anchor_revalidated'] is continuation['anchor_identity_preserved'] is True
assert continuation['parent_status'] == parent['status'] == 'failed' and continuation['parent_failure'] == parent['failure']
assert continuation['parent_failure']['code'] == 'time_limit'
assert all(continuation[key] is False for key in ('parent_path_completed','parent_task_target_executed','parent_unload_endpoint_reached','full_original_path_executed_by_child','full_original_path_completed','task_target_executed'))
assert result['full_original_path_completed'] is result['task_target_executed'] is response['path']['full_original_path_completed'] is response['path']['task_target_executed'] is False
assert all(value is False for value in response['producer_flags'].values())
assert response['independent_reference']['status'] == response['views']['status'] == 'not_provided'
rows = result['states']
assert [(row['original_target_index'],row['child_original_target_index'],row['leg'],row['d'],row['is_original_target']) for row in rows] == [(13,0,'resume_origin',1.2,True),(14,1,'unloading',1.15,True)]
assert rows[0]['state_sha256'] == parent['states'][13]['state_sha256'] == continuation['selected_state']['state_sha256']
assert rows[0]['R_input'] == parent['states'][13]['R_input'] == continuation['selected_state']['R_input_N']
assert rows[0]['state'] == parent['states'][13]['state'] | {'path': rows[0]['state']['path']}
assert response['requested_endpoint_response']['state_sha256'] == rows[1]['state_sha256']
assert response['target_response'] is None and response['path']['completed'] is True
assert result['path_diagnostics']['failed_attempts'] == [] and result['path_diagnostics']['maximum_bisection_depth'] == 0
trials = result['path_diagnostics']['trials']
assert trials[0]['reason'] == 'invalid_J' and trials[0]['accepted'] is False
assert trials[1]['factor'] == 0.5 and trials[1]['accepted'] is True
assert rows[0]['newton_checks'] == 1 and rows[1]['newton_checks'] == 8
assert view['status'] == 'pass' and view['failure'] is None
assert all(view[key] == 2 for key in ('geometry_started','geometry_completed','nodal_started','nodal_completed'))
assert view['new_F_T_model_solver_HP_calls'] == 0 and view['mechanical_hooks_monitored'] is False
assert view['contact_pressure_clamping_qualified'] is False and view['cases'][0]['reference_available'] is False
assert view['cases'][0]['saved_accepted_states'] == view['cases'][0]['observed_states'] == 2
assert view['cases'][0]['peak_index'] == 0 and view['cases'][0]['last_index'] == 1
assert helper['actual_PNGs'] == 3 and helper['actual_GIF_frames'] == 2
assert helper['view_NPZ_files'] == 5 and helper['view_decoded_fields'] == 63
assert helper['production_selected_NPZ_files'] == 2 and helper['production_selected_fields'] == 6
assert helper['source_pure_scope_separated'] is True and helper['original_parent_full_path_still_NOT_PASS'] is True
assert helper['new_HP_pressure_clamp_stability_HF5_qualified'] is False
assert parent['accepted_states'] == 14 and parent['path_completed'] is parent['unload_endpoint_reached'] is parent['task_target_executed'] is False

reviewed = {}
skipped_npz = {}
for name, pin in protocol['bindings'].items():
    if Path(name).suffix.lower() == '.npz':
        skipped_npz[name] = pin
    else:
        assert sha(ROOT / name) == pin
        reviewed[name] = pin
assert len(protocol['bindings']) == 100 and len(skipped_npz) == 2
for name, pin in helper['executed_source_package_SHA256'].items():
    assert sha(ROOT / name) == pin
    reviewed[name] = pin
actual_output_paths = {path.relative_to(ROOT).as_posix() for path in RUN.rglob('*') if path.is_file()}
assert actual_output_paths == set(helper['outputs']) | {helper_file.relative_to(ROOT).as_posix()}
for name, pin in helper['outputs'].items():
    if Path(name).suffix.lower() == '.npz':
        skipped_npz[name] = pin
    else:
        assert sha(ROOT / name) == pin
        reviewed[name] = pin
for path in (outer_file, helper_file, auth_file, reply_file, proof_file, protocol_file, STAGE / 'production_stdout.log'):
    reviewed[path.relative_to(ROOT).as_posix()] = sha(path)
assert {path.relative_to(RUN / 'view').as_posix() for path in (RUN / 'view').rglob('*.png')} == {'comparison.png','distances_forces.png','peak_fields.png'}
assert (RUN / 'view/resumed_alpha_half/actual_states.gif').is_file()
progress = [json.loads(line) for line in (RUN / 'accepted_progress.jsonl').read_text(encoding='utf-8').splitlines()]
assert len(progress) == 2 and all(progress[i]['state_sha256'] == rows[i]['state_sha256'] and progress[i]['R_input'] == rows[i]['R_input'] for i in range(2))
node_rows = sum(1 for _ in (RUN / 'view/resumed_alpha_half/nodes.csv').open(encoding='utf-8')) - 1
assert node_rows == 1406
stdout = (STAGE / 'production_stdout.log').read_text(encoding='utf-8')
objects, extra_lines = [], []
for line in stdout.splitlines():
    try:
        objects.append(json.loads(line))
    except json.JSONDecodeError:
        extra_lines.append(line)
assert objects == [{key:helper[key] for key in ('status','accepted_states','elapsed_seconds','peak_sampled_RSS_bytes')}]

terminal = {
    'schema_version': 'M-RESUME1-independent-actual-terminal-review-1.0',
    'status': 'pass_actual_execution_terminal_saved_record_audit_no_new_scientific_gate',
    'created_utc': datetime.now(timezone.utc).isoformat(), 'card': 'M-RESUME1', 'source_commit': BASE,
    'execution_status': outer['status'], 'outer_sha256': sha(outer_file),
    'authorized': True, 'executed': True, 'execution_closed': True, 'executed_new_science': False,
    'reviewed_repository_SHA256': dict(sorted(reviewed.items())),
    'NPZ_hashes_copied_from_saved_binding_and_output_records_not_reread': skipped_npz,
    'outer': {key:outer[key] for key in ('status','invocations','exit_code','elapsed_seconds','peak_sampled_tree_RSS_bytes','stop_reason','all_bindings_unchanged','completed_utc')},
    'helper': {key:helper[key] for key in ('status','elapsed_seconds','peak_sampled_RSS_bytes','accepted_states','counts','call_counts','cached_production_gates','all_bindings_unchanged','executed_source_package_unchanged','focused_tests_terminal','view_child_terminal')},
    'focused_tests': {'status':tests['status'], 'exit_code':tests['exit_code'], 'selected_nodeids':tests['collected_nodeids'],
                      'recorded_phase_reports':len(tests['reports']), 'all_recorded_setup_call_teardown_passed':True,
                      'elapsed_seconds':tests['elapsed_seconds'], 'peak_sampled_RSS_bytes':tests['peak_sampled_RSS_bytes'],
                      'scope':tests['scope']},
    'accepted_rows': [{key:row[key] for key in ('d','physical_mean_target_mm','original_target_index','child_original_target_index','leg','continuation_anchor','state_sha256','R_input','q_in','q_out','relative_residual','constraint_residual','constraint_bound','relative_global_force_balance','minimum_J','max_abs_Hu_per_mm','newton_checks','bisection_depth','elapsed_seconds','workpiece')} for row in rows],
    'continuation': continuation,
    'path_records': {'failed_attempts':result['path_diagnostics']['failed_attempts'],
                     'maximum_bisection_depth':result['path_diagnostics']['maximum_bisection_depth'],
                     'first_rejected_trial':trials[0], 'subsequent_half_step_trial':trials[1],
                     'timing_seconds':result['path_diagnostics']['timing_seconds']},
    'views': {'status':view['status'], 'geometry_started':view['geometry_started'], 'geometry_completed':view['geometry_completed'],
              'nodal_started':view['nodal_started'], 'nodal_completed':view['nodal_completed'], 'node_CSV_rows':node_rows,
              'PNG_files':helper['actual_PNGs'], 'GIF_frames':helper['actual_GIF_frames'],
              'GIF_frame_evidence':'Original pinned viewer source checks gif.n_frames equals actual accepted cache length at lines193–194; recorded helper count2. Reviewer did not decode GIF pixels.',
              'observed_rows':summary['rows'], 'mechanical_hooks_monitored':view['mechanical_hooks_monitored'],
              'new_F_T_model_solver_HP_calls':view['new_F_T_model_solver_HP_calls'],
              'source_scope':view['zero_mechanics_basis'], 'independent_reference_available':False,
              'pixel_inspection_by_this_reviewer':False},
    'interpretation': [
        'The sole real execution completed the saved-start original first descent. Fresh anchor was accepted in one Newton check with original split SHA/archive descriptor and signed R. The1.15mm endpoint was actually accepted after8 checks; no target bisection or terminal numerical failure occurred.',
        'Force17 started/16 completed is consistent with recorded first full-factor trial invalid_J rejection; its factor0.5 trial then passed original line-search rules. This is an internal rejected attempt in the originally authorized algorithm, not a second launch, retry card, accepted state or unresolved terminal failure.',
        'Stored R is0.37865427196005513N at anchor and0.3470376815403639N at endpoint; weighted q_out is1.016934534302024mm and1.0153174242325562mm. No new scientific differences, percentages or integrals were calculated by this reviewer.',
        'Lower-body signed weak total Fy is0.12492121630032427N and0.10671287553103108N. Material/Hu components, holding reaction, mirrored force, full-body net and two-sided magnitude retain their distinct saved definitions. This is observable discrete load response, not newly qualified continuous pressure or effective clamp force.',
        'Original parent remains failed/time_limit with14 loading states and full path/unload/task flagsfalse. Child segment/path completion and endpoint1.15 do not alter parent or qualify full task. Candidate remains an isolated runtime overlay, not an installed formal core change.',
        'The actual viewer generated3PNG and2frame GIF/1406 node rows from new saved arrays, no additional F/T/model/solver/HP. Endpoint displacement/finite unsigned distance and field values are saved observations. q_out is a port measurement; source node-window clearance differs from finite tip-face distance. Positive tiny mediumJ is an accepted production state, not evidence of physical or mesh stability.',
        'A viewer legend performance warning appears in raw stdout and is retained; it is not a new failure gate. Images were hashed but not visually inspected by this reviewer. Root handles actual pixel interpretation.'
    ],
    'qualification': {'new_independent_HP':False, 'pressure':False, 'effective_clamping':False,
                      'physical_stability':False, 'full_original_task':False, 'HF5':False},
    'blockers': [],
    'limits': ['Raw JSON/log/source/image bytes and ordinary row/file identities only. No NPZ byte read/decode, scientific module import, test replay, new arithmetic science, integral, solver or figure generation.',
               'Old two NPZ pin identities and new output archives are copied declarations plus original helper all-bindings/output checks; this reviewer did not independently reopen array bytes.',
               'Existing production gates and saved bookkeeping were checked without adding a new scientific acceptance threshold. The reported PASS is this bounded execution/terminal contract only.'],
    'reviewer_actions': {'HF_import':0,'candidate_import':0,'NPZ_byte_read_or_decode':0,'tests':0,'force_tangent_HP_solver':0,
                         'new_scientific_values':0,'figure_generation':0,'formal_mutation':0,'retry':0},
}
new_json(EXT / 'execution_terminal_review.json', terminal)
(EXT / 'TERMINAL_REVIEW.md').write_text('''# M-RESUME1 实际终态独立审阅

唯一实际运行 **PASS／exit0**。outer619.0985891000018秒、采样树RSS795955200字节、stop=null；helper618.4817464999942秒、RSS800935936字节。真实终止在原2700／2760秒及采样8GiB合同内，100个原pins与runtime源码闭包保持；本审阅仅读已有记录，不重启或重算。

五项focused tests全部通过（15条setup／call／teardown记录）；随后一次API／构模／求解／缓存保存／摘要及一次pure viewer。实际F17开始／16完成，T9／9，HP／JIT0，保存／摘要额外F/T0。原首次factor1 trial以invalid_J拒绝，factor0.5随后接受；这是原回溯的内部试探，不是第二次运行。没有失败target attempt或二分，原1.15目标以8次检查实际接受。

| 保存记录 | 原索引／角色 | R (N) | q_out (mm) | 相对残差 | 下半工件 signed total Fy (N) |
|---|---|---|---|---|---|
|1.20 mm|13／resume_origin|0.37865427196005513|1.016934534302024|9.61400246360761e−13|0.12492121630032427|
|1.15 mm|14／unloading|0.3470376815403639|1.0153174242325562|4.584773266448174e−12|0.10671287553103108|

峰值首态fresh F/T用1次检查直接合格，原split SHA、signed R及archive字段身份保留。缓存原门记录为PASS：minJ2.3283009562457014e−5、最大残差4.584773266448174e−12、最大mean残差2.7755575615628914e−17（原constraint_bound通过）、global balance7.677910679556237e−14、fixed split sum0。数值均复制既有记录，没有新计算差值／比率／积分。

pure viewer实际完成geometry／nodal各2次、1406节点行、3PNG及2帧GIF，读取新5NPZ／63字段、额外F/T／模型／求解／HP0。原viewer检查实际GIF帧数与接受态数一致；本审阅只核文件、SHA与记录，没有查看像素或解码GIF。legend性能warning原样保存，不构成新增失败门。实际图像解释由root另行完成。

工件力仍为total／material／Hu弱式节点作用；保持反力、镜像推导、整装净力和双侧幅值分别保留。q_out是加权端口位移，源node-window clearance是栅格诊断，不能冒充有限表面间隙或接触压力。tiny mediumJ虽满足原生产门，不代表物理／网格稳定性。

原父M-ALPHA1仍failed/time_limit、14加载态、原完整path／unload／task=false。本次成功仅完成保存峰值到首次下降的短段；未升级原完整任务、新alpha独立HP、压力、有效夹持、稳定性或HF5。候选仍在隔离runtime包，未安装到正式hf_repo核心。

实际SHA、调用与两态原值见 [execution_terminal_review.json](execution_terminal_review.json)。本审阅没有读取NPZ字节、导入HF、运行测试／F／T／HP／求解／绘图或修改正式仓库。
''', encoding='utf-8')
print(json.dumps({
    'terminal_review_status':terminal['status'], 'execution_status':terminal['execution_status'],
    'outer_sha256':sha(outer_file), 'terminal_review_sha256':sha(EXT / 'execution_terminal_review.json'),
    'terminal_md_sha256':sha(EXT / 'TERMINAL_REVIEW.md'),
    'tool_static_review_sha256':sha(EXT / 'execution_delivery_tool_static_review.json'),
    'tool_static_md_sha256':sha(EXT / 'EXECUTION_DELIVERY_TOOL_STATIC_REVIEW.md'),
    'independently_hashed_non_NPZ_repository_files':len(reviewed), 'NPZ_files_not_reread':len(skipped_npz),
    'executed_new_science':False
}))
