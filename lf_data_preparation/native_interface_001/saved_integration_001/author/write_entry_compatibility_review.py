"""Record source-only entry compatibility review; do not import the HF code."""
import ast
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
EXT = Path(__file__).resolve().parent
BASE = 'd45f6ee92d8a0d6ca740772a1762abdc691489fa'
REL = 'lf_data_preparation/native_interface_001/saved_continuation_001'
STAGE = ROOT / REL
AUTHOR = STAGE / 'author'
CANDIDATE = STAGE / 'candidate'
sha = lambda path: sha256(path.read_bytes()).hexdigest()
read = lambda path: json.loads(path.read_bytes())
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == BASE
receipt = read(AUTHOR / 'candidate_author_receipt.json')
reviewed = {}
file_plan = []
for name, expected in receipt['candidate_files'].items():
    candidate = CANDIDATE / name
    assert sha(candidate) == expected['sha256']
    ast.parse(candidate.read_text(encoding='utf-8'), filename=name)
    reviewed[REL + '/candidate/' + name] = sha(candidate)
    default = ROOT / name
    if name in receipt['baseline_files_SHA256']:
        assert default.is_file() and sha(default) == receipt['baseline_files_SHA256'][name]
        ast.parse(default.read_text(encoding='utf-8'), filename=name)
        reviewed[name] = sha(default)
        action = 'replace existing source after entry guard revision' if name.endswith('/native_evaluate.py') else 'replace existing source by frozen candidate bytes'
        old_sha = reviewed[name]
    else:
        assert not default.exists()
        action, old_sha = 'add frozen candidate source', None
    file_plan.append(dict(path=name, action=action, default_sha256=old_sha,
                          original_candidate_sha256=expected['sha256']))
dependencies = [
    'hf_repo/src/hf_eval/native_project.py', 'hf_repo/src/hf_eval/native_batch.py',
    'hf_repo/src/hf_eval/tmc.py', 'hf_repo/src/hf_eval/displacement.py',
    'hf_repo/src/hf_eval/__main__.py', 'hf_repo/src/hf_eval/split_numpy_tangent.py',
    'hf_repo/src/hf_eval/split_kernel_invariants_hu.py',
    REL + '/author/candidate_author_receipt.json', REL + '/author/candidate_source.diff',
    REL + '/run_001/resumed_alpha_half/result.json',
    REL + '/run_001/resumed_alpha_half/response.json',
    'lf_data_preparation/native_interface_001/regularization_sensitivity_001/run_001/alpha_half/result.json',
]
for name in dependencies:
    reviewed[name] = sha(ROOT / name)
child = read(STAGE / 'run_001/resumed_alpha_half/result.json')
response = read(STAGE / 'run_001/resumed_alpha_half/response.json')
parent = read(ROOT / dependencies[-1])
assert child['continuation'] == response['continuation']
assert child['status'] == 'success' and child['targets_mm'] == [1.2, 1.15]
assert child['task_target_executed'] is child['full_original_path_completed'] is False
assert parent['status'] == 'failed' and parent['failure']['code'] == 'time_limit'
assert parent['path_completed'] is parent['task_target_executed'] is parent['unload_endpoint_reached'] is False
checks = [
    dict(topic='zero-start defaults', conclusion='Valid existing calls resolve the new None option sentinels to complete/full/tangent; explicit modes remain unchanged. Original settings are still required by direct solve_native_mean, while evaluate_native builds its same first-increment/16 settings.', source='native_resume.py:63; native_mean.py:138-172; native_evaluate.py:66-86'),
    dict(topic='zero-start mechanics and output', conclusion='Non-resume branches preserve the old task-path equality, assembler selection, cached capture/persistence and summary behavior. initial_parameter=0 preserves original controller arithmetic and result fields; no force/tangent kernel source is changed.', source='native_mean.py:160-296; split_displacement.py:54-381; native_response.py:166-235'),
    dict(topic='saved physical identity', conclusion='Parent/model/state canonical and raw descriptor identities, grid, material, boundary/port regions, geometry authority and two unchanged force/tangent source identities bind the original physical task before production F/T. Extra user geometry/task values must match the bound physical identities.', source='native_resume.py:26-133'),
    dict(topic='absolute suffix and clocks', conclusion='Saved targets are the exact original full-task suffix from a nonzero original accepted state with a remaining target. Parent task is retained, not rewritten or shifted. Parent options and settings are inherited; only an explicit new clock is allowed. API/CLI default180 is a new call clock; direct saved solve with settings=None requires a clock explicitly.', source='native_resume.py:46-112; native_mean.py:134-175; both native scripts'),
    dict(topic='paths and migration', conclusion='Parent model/state/source-geometry paths are resolved relative to the selected saved package and constrained to its directory. Equivalent copied packages retain content identities; historical absolute provenance fields do not control the relative package loading.', source='native_resume.py:34-61,79-133'),
    dict(topic='parent and child semantics', conclusion='Child local indices are separate from original task indices; resume_origin is explicit. Segment success/endpoint remain separate from parent failure/full-task status and independent reference qualification. The actual published child and parent ordinary JSON preserve these distinctions.', source='native_mean.py:225-295; native_response.py:64-66,187-234'),
    dict(topic='errors and partial state', conclusion='TMCError is a ValueError and the public API catches it with original stage/code/class/reason; controller failures persist accepted partial paths. The settings AttributeError finding below is the sole actionable entry error discovered in this review.', source='tmc.py:19; native_mean.py:134-143; native_evaluate.py:95-105'),
    dict(topic='CLI and API scope', conclusion='The two native scripts wire saved_result/selected_state_index and inherited options to the native API. Legacy python -m hf_eval dispatch is unchanged; this overlay does not add continuation to that separate legacy interface or to native_batch.', source='scripts/evaluate_native.py:12-32; scripts/solve_native_mean.py:19-61; default __main__.py/native_batch.py'),
    dict(topic='historical reference compatibility', conclusion='The unchanged strict _reference gate hashes the declared source_bindings in the current repo. Installing changed native_mean/controller sources therefore makes old references bound to original source bytes report mismatch; production status and stored old evidence remain unchanged. Preserve this gate and old pins, and use a pure JSON negative source-mismatch test rather than expecting the old positive-reference test to pass against new sources.', source='native_response.py:77-122'),
]
finding = dict(
    id='ENTRY-1', severity='blocking_for_integration_until_minimal_revision',
    path=REL + '/candidate/hf_repo/src/hf_eval/native_evaluate.py', lines=[51,52,95],
    trigger='evaluate_native(...,saved_result=valid_path,selected_state_index=13,settings=dict_or_plain_object)',
    actual_source_behavior='saved_resume_defaults receives settings.time_limit_seconds before any API isinstance guard. A dict/plain object raises AttributeError, which is outside the API except tuple, so the public call cannot persist its typed failure response. The native_mean type guard runs too late.',
    minimal_revision='In the new integration overlay, inside the existing try after existing-output/pair checks and before saved_resume_defaults, require settings is None or isinstance(settings,DisplacementSettings). Otherwise raise the existing TMCError with code invalid_settings; import TMCError from the existing .tmc module. Do not modify the already closed M-RESUME1 candidate or scientific kernels.',
    future_negative_test='Use ordinary API mocks: saved_resume_defaults and solve_native_mean must not be called. For dict and object inputs, assert response status error, failure stage input/code invalid_settings, and persisted response.json. No parent file read, model, NPZ, F/T or solver is needed. Source is proposed only; no test was written or run by this reviewer.',
)
notes = [
    dict(id='ENTRY-DOC-1', severity='non_blocking_help_text', path='hf_repo/scripts/solve_native_mean.py', lines=[24,26,45],
         recommendation='Describe --targets as full zero-start task path or exact saved suffix; describe minimum increment as inherited in saved mode; replace the at-least-zero wording with selected origin/anchor plus one remaining target. These are small user-facing text refinements, not mechanical changes.'),
    dict(id='ENTRY-TEST-1', severity='non_blocking_test_plan_observation', recommendation='Pure mock native CLI flag/paired-argument wiring tests are useful alongside the invalid-settings API negative case. Existing five M-RESUME1 tests and its actual two-state solve are historical evidence, not a new integrated-core regression run.'),
]
report = dict(
    schema_version='MINTEGRATE1-entry-compatibility-source-review-1.0',
    status='revision_required_static_entry_compatibility_review_no_execution',
    created_utc=datetime.now(timezone.utc).isoformat(), base_commit=BASE,
    authorized=False, executed=False, review_scope='Source/AST and existing ordinary saved JSON only; not a scientific PASS or integrated runtime validation',
    decision='Seven candidate files can retain their frozen bytes. native_evaluate.py needs the single input-type guard before formal integration; CLI wording improvements may be applied without changing mechanics. No broad reader/controller/response refactor is required.',
    candidate_files=file_plan, checks=checks, findings=[finding], non_blocking_notes=notes,
    reviewed_repository_SHA256=reviewed,
    limitations=[
        'Saved mode is limited to an original zero-lift ordered task, a nonzero original accepted point with a remaining exact suffix, and matching physical/settings/source identities. It is not arbitrary warm start, rebase or continuation-child chaining.',
        'The reader binds the two force/tangent source files it declares; the prior execution stage additionally bound the entire executed closure. This source review does not invent a universal future producer/source compatibility contract.',
        'No current candidate import, pytest, NPZ byte read or decode, F/T, solver, observer, HP, visualization or formal source edit occurred. Integration and its newly authorized finite regression checks remain later work.',
    ],
    reviewer_actions=dict(HF_or_candidate_import=0, pytest=0, NPZ_byte_read_or_decode=0,
        force_tangent_solver_observer_HP=0, new_scientific_values=0, render=0,
        formal_repository_mutation=0, external_reports_written=2),
)
md = '''# Native 保存态入口兼容性静审

相对 main `d45f6ee92d8a0d6ca740772a1762abdc691489fa` 的八文件候选需要一处最小入口修订后集成：`native_evaluate.py` 在保存态模式中先访问 `settings.time_limit_seconds`，字典或普通对象会产生未捕获的 `AttributeError`，无法保存原合同要求的错误响应。其余入口、物理任务身份与父子语义未发现算法层阻断。

在新集成 overlay 的原 `try` 内、父 defaults 读取前，加 `DisplacementSettings` 类型检查；不符合时抛既有 `TMCError(code="invalid_settings")` 即可。已闭卡 M-RESUME1 候选和力／切线核应保持原字节。一个 mock 负面测试可覆盖 dict/object：禁止父 defaults 与 solver 被调用，检查 `input` 阶段错误码及 `response.json`，无需任何力学计算。

旧合法零起点调用的 None sentinel 回落仍是 `complete/full/tangent`，原 first-increment/16、完整任务路径匹配、缓存保存和 summary 分支保持。保存态入口继承父实际 options／settings，仅允许新时间窗口；直接 mean saved 调用不能默默复用父9000秒。路径使用保存包内相对路径与身份核对，额外几何／任务输入必须匹配原物理来源；原任务和绝对 suffix 不改写。

fresh anchor、原全局索引与子局部索引、`resume_origin`、父 `failed/time_limit` 与子段完成分别保存。当前普通结果 JSON 也保持父 full-path/task/unload 为 false，子只完成 `[1.20,1.15]`，不新增独立HP、压力、有效夹持、稳定性或 HF5 资格。reader 不接任意 warm start 或 continuation 子包再链。

原 `_reference` 严格门按当前 repo 的声明源码字节核验。正式安装 changed mean/controller 后，绑定旧源码的历史 reference 会显示 `mismatch`；原保存证据和 production 状态保留，但不能假设新运行 summary 仍自动认可旧 reference。应保留原门与旧 pins，以普通 JSON 负面用例核这一行为。

非阻断文字建议：`solve_native_mean.py` 的 `--targets`、`--minimum-increment` 与“至少zero”错误文字补充保存态含义。新增纯 mock native CLI flags／成对参数用例也有价值。旧 `python -m hf_eval` 和 batch 入口不在本次 continuation 接线范围内。

本报告只进行了八候选文件与六默认原文件的源码／AST／SHA 对照，以及依赖源码和既有普通 JSON 的身份审阅。没有导入候选、运行测试、读取NPZ字节或数组、求解／绘图，也没有改正式仓库。先前 M-RESUME1 的通过记录是历史证据，不能充当集成后的新回归通过。

准确 source SHA、行号、最小修订与边界见同目录 `ENTRY_COMPATIBILITY_REVIEW.json`。
'''
json_file = EXT / 'ENTRY_COMPATIBILITY_REVIEW.json'
md_file = EXT / 'ENTRY_COMPATIBILITY_REVIEW.md'
with json_file.open('x', encoding='utf-8', newline='\n') as stream:
    stream.write(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
with md_file.open('x', encoding='utf-8', newline='\n') as stream:
    stream.write(md)
print(json.dumps(dict(status=report['status'], JSON_SHA256=sha(json_file), MD_SHA256=sha(md_file),
    reviewed_repository_files=len(reviewed), actionable_findings=1, new_science=0)))
