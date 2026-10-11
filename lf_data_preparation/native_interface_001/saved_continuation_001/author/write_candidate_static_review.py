"""Independent source/AST/ordinary-metadata review writer; imports no candidate."""
import ast
from datetime import datetime, timezone
from difflib import unified_diff
from hashlib import sha256
import json
from pathlib import Path

EXT = Path('D:/hf-native-workpiece-api-author-20261011/MRESUME1_preparation_001')
ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')


def pin(path):
    return sha256(path.read_bytes()).hexdigest()


author = json.loads((EXT / 'candidate_author_receipt.json').read_bytes())
runner = json.loads((EXT / 'runner_source_author_receipt.json').read_bytes())
assert author['authorized'] is False and author['executed'] is False
assert runner['authorized'] is False and runner['executed'] is False
assert author['base_commit'] == runner['source_baseline_commit'] == '01b5078acaf76fdaabfbdf214da9db16056467bc'
sources = sorted((EXT / 'candidate').rglob('*.py'))
assert len(sources) == 8
ast_checks, baseline_checks, reviewed, diff = {}, {}, {}, []
for path in sources:
    name = path.relative_to(EXT / 'candidate').as_posix()
    raw = path.read_bytes()
    tree = ast.parse(raw, filename=name)
    declared = author['candidate_files'][name]
    assert pin(path) == declared['sha256'] and len(raw) == declared['bytes']
    rel = path.relative_to(EXT).as_posix()
    reviewed[rel] = pin(path)
    ast_checks[rel] = {'status': 'parsed_source_without_import', 'bytes': len(raw)}
    before = EXT / 'baseline' / name
    previous = before.read_bytes() if before.exists() else b''
    if before.exists():
        assert previous == (ROOT / name).read_bytes()
        assert pin(before) == author['baseline_files_SHA256'][name]
        baseline_checks[name] = pin(before)
        reviewed[before.relative_to(EXT).as_posix()] = pin(before)
    diff.extend(unified_diff(previous.decode('utf-8').splitlines(True), raw.decode('utf-8').splitlines(True),
                             fromfile='baseline/' + name, tofile='candidate/' + name))
assert ''.join(diff) == (EXT / 'candidate_source.diff').read_text(encoding='utf-8')
assert pin(EXT / 'candidate_source.diff') == author['diff_sha256']
assert pin(EXT / 'source_author_notes.md') == author['notes_sha256']
assert pin(EXT / 'candidate_author_receipt.json') == runner['candidate_author_receipt_sha256']
assert pin(EXT / 'PREPARATION_RUNNER_NOTES.md') == runner['notes_sha256']
for name, value in runner['sources'].items():
    path = EXT / name
    assert pin(path) == value['sha256']
    ast.parse(path.read_bytes(), filename=name)
    ast_checks[name] = {'status': 'parsed_source_without_import', 'bytes': len(path.read_bytes())}
names = [
    'candidate_author_receipt.json', 'source_author_notes.md', 'candidate_source.diff',
    'execute_resume.py', 'resume_focused_budget.py', 'runner_source_author_receipt.json',
    'PREPARATION_RUNNER_NOTES.md', 'M-RESUME1_CARD.draft.md',
    'physical_basis.json', 'CONTINUATION_CONTRACT.md',
]
for name in names:
    reviewed[name] = pin(EXT / name)
test_source = EXT / 'candidate/hf_repo/tests/test_saved_native_resume.py'
test_tree = ast.parse(test_source.read_bytes())
test_names = [node.name for node in test_tree.body if isinstance(node, ast.FunctionDef) and node.name.startswith('test_')]
assert ['tests/test_saved_native_resume.py::' + name for name in test_names] == author['focused_test_nodeids'] == runner['focused_test_nodeids']
fixtures = {
    'test_native_force.py': ['small_native', 'forbid_legacy_or_compiled_work'],
    'test_native_mean_mechanical.py': ['cycle_task'],
    'test_split_cycle.py': ['dense_port_solution'],
    'test_split_displacement.py': ['one_cell', 'physical', 'synthetic'],
}
fixture_checks = {}
for name, expected in fixtures.items():
    path = ROOT / 'hf_repo/tests' / name
    tree = ast.parse(path.read_bytes(), filename=name)
    defined = {node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    assert set(expected) <= defined
    assert runner['runtime_source_plan']['tests/' + name]['sha256'] == pin(path)
    fixture_checks['hf_repo/tests/' + name] = {'sha256': pin(path), 'imported_definitions_present': expected}
guard_imports = [node for node in test_tree.body if isinstance(node, ast.ImportFrom) and node.module == 'test_native_force']
assert any('forbid_legacy_or_compiled_work' in {alias.name for alias in node.names} for node in guard_imports)
for name, value in runner['baseline_module_SHA256'].items():
    assert pin(ROOT / name) == value

report = {
    'schema_version': 'M-RESUME1-independent-candidate-static-review-1.0',
    'status': 'pass_static_candidate_math_interface_tests_and_runner_scope_not_executed',
    'created_utc': datetime.now(timezone.utc).isoformat(),
    'base_commit': author['base_commit'], 'card': 'M-RESUME1',
    'authorized': False, 'executed': False, 'preparation_only': True,
    'reviewed_external_SHA256': dict(sorted(reviewed.items())),
    'AST_source_checks': ast_checks,
    'baseline_files_byte_identical_to_formal': baseline_checks,
    'diff_reconstructed_from_actual_source_bytes': True,
    'fixture_source_checks': fixture_checks,
    'focused_test_nodeids': author['focused_test_nodeids'],
    'findings': [
        {'contract': 'Absolute parameter and exact split transport', 'source': 'candidate/hf_repo/src/hf_eval/split_displacement.py:55',
         'finding': 'Opt-in initial_parameter keeps original nonnegative absolute stage values. Native branch retains target_origin=0 and exact suffix [1.2,1.15], without a rounded negative offset or display/rebase. Generic expected anchor lift uses the same binary64 origin+p0*shape expression as impose; p0=0 uses the old origin copy.'},
        {'contract': 'Fresh validate-only anchor', 'source': 'candidate/hf_repo/src/hf_eval/split_displacement.py:257',
         'finding': 'State starts at saved p0/R with K=None. At same stage there is no predictor. The first fresh F/T must pass existing residual/mean gates; otherwise initial_state_not_equilibrated is raised before correction or durable commit. Existing kernel J checks apply. This source ordering supports exact anchor transport, but is not an executed verification.'},
        {'contract': 'Inherited Newton and rollback', 'source': 'candidate/hf_repo/src/hf_eval/split_displacement.py:312',
         'finding': 'The original unsymmetric augmented system, predictor/control/R signs, projection, Armijo, bounded bisection and production tolerances are retained. Unaccepted Newton attempts preserve both arrays, R, stage and committed K; callback or post-accept clock failures can already contain a valid accepted state. Anchor validation failure has zero attempted increment and cannot trigger a corrective bisection.'},
        {'contract': 'Saved-input/model/setting identities', 'source': 'candidate/hf_repo/src/hf_eval/native_resume.py:69',
         'finding': 'Canonical and raw JSON hashes, chosen descriptor, selected original target, exact suffix, full embedded task, material/grid/BC metadata and unchanged force/tangent sources are checked. New model rebuild reads original four masks; reader decodes only selected lift/fluctuation and validates array descriptors/state hash. Settings and actual mechanical/chunk256/port_projection options are preserved except explicit new time. No parent force/tangent/matrix decoding or reuse.'},
        {'contract': 'Parent/child qualification and indices', 'source': 'candidate/hf_repo/src/hf_eval/native_mean.py:286',
         'finding': 'Mapped original indices13/14 remain distinct from child0/1 and resume_origin. Result, continuation and public response retain parent failed/time_limit lineage and full_original_path_completed/task_target_executed=false. Child requested endpoint and completed segment do not upgrade full path or any independent HP/pressure/clamp/stability/HF5 qualification.'},
        {'contract': 'Public/default compatibility', 'source': 'candidate/hf_repo/src/hf_eval/native_evaluate.py:21',
         'finding': 'Old zero-start options resolve to complete/full/tangent and use original target equality; the p0=0 controller result schema is retained. Saved API/CLI restore parent settings/options, reject incompatible explicit choices, and require a new output directory. Direct Mean requires explicit new time or complete settings. Batch remains unchanged. CLI implementations are only source-reviewed, outside proposed numerical invocation.'},
        {'contract': 'Meaningful focused tests and accounting', 'source': 'candidate/hf_repo/tests/test_saved_native_resume.py:1',
         'finding': 'All five exact test definitions and four fixture modules exist and AST parse. Explicit autouse guard is imported. Four synthetic/controller tests cover transport, zero default, anchor rejection, rollback and invalid input; fifth is an actual tiny16-cell NumPy/TMC public persistence/resume integration. Its real F/T remain separate from original-model production counts. Static inspection finds no collection-name or fixture mismatch; dynamic collection/pass and convergence are unproven.'},
        {'contract': 'One future bounded wrapper', 'source': 'execute_resume.py:39',
         'finding': 'Frozen source package and exact focused nodeids are copied once. Tests use one -x child, production one API/model/solve/save/summary, save/summary add no F/T, and typed controller partial is saved before non-success closes the stage. Only successful production enters original pure viewer child. N=2..9 allows bounded existing bisection. Success checks parent/child identities, old four gates, force/tangent started/completed records, exact source/pins and original viewer scope.'},
        {'contract': 'Resource, source and permission boundaries', 'source': 'M-RESUME1_CARD.draft.md:31',
         'finding': 'Proposed single helper2700/outer2760 seconds, focused120/controller1800/view600 and sampled8GiB match wrapper declarations. Child phases use remaining helper time, cooperative checkpoints and real termination without force. Receipt-write final checkpoint can make actual helper/outer non-success despite provisional receipt; source PASS is not authorization. Current prepared source requires later direct-human evidence and source publication binding; no evidence/authorization object was created by this review.'},
    ],
    'review_placement_note': 'Final helper checks full_original_path_completed and task_target_executed at result/response.path. The frozen native_mean already has the corresponding continuation flags too; this is a contract-placement refinement, not an identified frozen numerical/source bug.',
    'future_outputs_reviewed_source_only': {
        'selected_old_NPZ_files': 2, 'selected_old_fields': 6, 'selected_old_JSON_files': 4,
        'accepted_states_if_success': 'N=2..9', 'new_view_NPZ_files': '1+2N',
        'new_view_fields': '27+18N', 'geometry_calls': 'N', 'nodal_calls': 'N',
        'PNG_files': 3, 'GIF_files': 1, 'GIF_frames': 'N',
        'interpretation': 'Actual x1 saved deformation and signed total/material/Hu ON-body weak nodal forces; unsigned finite geometry distances and original saved-field definitions. PEAK is revalidated inherited anchor; LAST is actual accepted endpoint. No combined parent full-path or new pressure qualification.'
    },
    'blockers': [],
    'limitations': [
        'No candidate or HF import, pytest collection/execution, NPZ byte/field read, force/tangent/HP/solver/observer, image generation or numerical validation was performed.',
        'AST/fixture identity review cannot prove test pass, fresh actual anchor pass, first descent convergence or the proposed runtime estimate.',
        'This is external candidate/source/card review. Formal protocol/source publication and actual human approval remain separate before any numerical launch.',
        'No existing reference or contact/pressure/gripping/stability qualification transfers to the new alpha or continuation segment.'
    ],
    'actual_actions': {'candidate_imports': 0, 'HF_imports': 0, 'tests': 0, 'NPZ_byte_reads_or_decodes': 0,
                       'new_scientific_computation': 0, 'plots': 0, 'formal_repository_mutations': 0},
}
md = '''# M-RESUME1 候选独立静审

结论：源码、数学／接口合同、五项测试定义和未来执行包装未见阻断。当前 **未授权、未执行**；静审通过不代表测试或实际续算通过。

候选沿用原绝对参数 `[1.20,1.15]`、`target_origin=0` 和已保存的 split／signed R。通用控制器新增 opt-in `initial_parameter`，按与 `impose` 相同的 binary64 表达式核对初始 lift。初始 K=None，峰值锚点先计算新的 F/T；原 residual／mean 门失败时在 correction／commit 之前停止。后续原非对称增广系统、R符号、投影、回溯、二分、生产容差及未接受 attempt 回滚主体保持。默认零起点 schema／数学分支保留。接受后 callback／时钟异常可能已有接受态，不能泛称全部异常回到峰值。

reader 验证所选 original target、完整原 task、原 suffix、JSON／数组／state 身份、同材料／网格／BC、原 settings 和实际 options，仅允许新的 clock。生产输入限定为原 geometry四掩码和所选双位移：2个NPZ／6字段／4份普通JSON；不读取原 force／tangent／CSC。新结果保留 parent failed/time_limit 和原完整路径未完成，局部0／1与原13／14分别记录。子段成功只描述该 suffix；`task_target_executed`／`full_original_path_completed` 保持 false。

五个精确 test 定义和四份 fixture 的导入名、AST、源码 SHA已核，autouse禁止旧／compiled fallback 的 fixture 已显式导入。四项测试是 controller／线性代数合同，第五项会运行真实16单元 NumPy/TMC保存／续算集成；其 F/T与13440单元实际生产分开计数。未运行 pytest，不能证明可实际通过或耗时。

未来包装匹配一次 focused `-x` child、一次API及缓存保存／摘要；typed controller失败保留实际partial后停止，只有生产成功才调用原pure viewer。接受数N=2..9允许原二分；显示读取新1+2N个NPZ／27+18N字段，geometry／nodal各N次、3PNG及N帧GIF。工件力保持 signed total／material／Hu弱式节点作用和保持／镜像语义，距离为原无符号有限几何距离，PEAK为恢复锚点、LAST为实际接受终点；无新HP、压力、有效夹持、稳定性或HF5资格。

卡与包装提出同一未来窗口：helper2700／outer2760秒、tests120／controller1800／viewer600秒、采样8GiB。剩余helper时间限制子阶段，协作停止／真实终止、无force。末尾写receipt后的checkpoint失败仍以实际helper／outer NOT_PASS为准。当前报告不创建授权或运行产物，正式protocol、发布身份和人类批准仍须另行核对。

最后helper将full-path标记的检查放在result／response.path；原冻结native_mean本来已含continuation同类标记，因此这是合同引用位置精化，不是冻结源码数值缺陷修复。

实际审阅SHA、逐项源码位置和范围见 [candidate_static_review.json](candidate_static_review.json)。没有正式仓库改动、新科学数值或图像。
'''
json_path = EXT / 'candidate_static_review.json'
md_path = EXT / 'CANDIDATE_STATIC_REVIEW.md'
assert not json_path.exists() and not md_path.exists()
json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
md_path.write_text(md, encoding='utf-8')
print(json.dumps({'status': report['status'], 'review_sha256': pin(json_path), 'md_sha256': pin(md_path),
                  'reviewed_external_files': len(reviewed), 'AST_python_files': len(ast_checks),
                  'candidate_author_receipt_sha256': pin(EXT / 'candidate_author_receipt.json'),
                  'execute_resume_sha256': pin(EXT / 'execute_resume.py'), 'executed': False, 'authorized': False}))
