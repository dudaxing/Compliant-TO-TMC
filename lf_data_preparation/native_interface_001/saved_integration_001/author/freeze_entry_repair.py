"""Freeze only this author's entry edits and two mock selectors, AST only."""
import ast
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

EXT = Path(__file__).resolve().parent
ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
OLD = ROOT / 'lf_data_preparation/native_interface_001/saved_continuation_001/candidate/hf_repo'
NEW = EXT / 'candidate/hf_repo'
sha = lambda path: sha256(path.read_bytes()).hexdigest()
edited = [
    'src/hf_eval/native_evaluate.py', 'scripts/evaluate_native.py',
    'scripts/solve_native_mean.py', 'tests/test_native_evaluate_settings.py',
]
unchanged = [
    'src/hf_eval/native_mean.py', 'src/hf_eval/native_response.py',
    'src/hf_eval/native_resume.py', 'src/hf_eval/split_displacement.py',
    'tests/test_saved_native_resume.py',
]
pins = {}
for name in edited + unchanged:
    path = NEW / name
    ast.parse(path.read_text(encoding='utf-8'), filename=name)
    pins['candidate/hf_repo/' + name] = sha(path)
for name in unchanged:
    assert (NEW / name).read_bytes() == (OLD / name).read_bytes()
api = ast.parse((NEW / edited[0]).read_text(encoding='utf-8'))
function = next(node for node in api.body if isinstance(node, ast.FunctionDef) and node.name == 'evaluate_native')
trial = next(node for node in function.body if isinstance(node, ast.Try))
guard_index = next(i for i, node in enumerate(trial.body) if isinstance(node, ast.If)
                   and 'isinstance(settings, DisplacementSettings)' in ast.unparse(node.test))
defaults_index = next(i for i, node in enumerate(trial.body) if isinstance(node, ast.Assign)
                      and any(isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name)
                              and sub.func.id == 'saved_resume_defaults' for sub in ast.walk(node)))
assert guard_index < defaults_index
guard = trial.body[guard_index]
assert ast.unparse(guard.body[0].exc) == "TMCError('settings must be DisplacementSettings', code='invalid_settings')"
assert any(isinstance(sub, ast.Name) and sub.id == 'ValueError' for sub in ast.walk(trial.handlers[0].type))
test_tree = ast.parse((NEW / edited[3]).read_text(encoding='utf-8'))
name = 'test_saved_invalid_settings_returns_typed_input_error_without_parent_or_mechanics'
assert len([node for node in test_tree.body if isinstance(node, ast.FunctionDef) and node.name == name]) == 1
selectors = [f'tests/test_native_evaluate_settings.py::{name}[dict]',
             f'tests/test_native_evaluate_settings.py::{name}[object]']
md = '''# 保存态入口最小修订：源码冻结

本轮只在新集成候选的 `native_evaluate.py` 增加既有 `TMCError` 导入，并在原 `try` 内、父 defaults 读取前校验 `DisplacementSettings` 类型。不合法 settings 返回 `input / invalid_settings`；None 和合法实例继续原路径。异常仍由原 ValueError 分支处理，不扩大 catch 集合，也不改变力学核。

新增 `test_native_evaluate_settings.py`，参数化 dict/object 两例。父 defaults、solve 和 build 都被替换成禁止调用的 mock；父文件故意不存在，断言错误 JSON、原异常类型和输出仅有 response.json。因此该测试设计不需要旧 NPZ、模型或 F/T；本轮未导入、collect 或执行测试。

两个 CLI 只改 `--targets`／`--minimum-increment` 帮助文字及 mean 的“至少zero”错误文字，使保存态 suffix／继承步长含义明确。其余五个原候选文件保持逐字节相同；这三处入口修改不改七个原文件的机械逻辑，也未修改已闭卡候选、旧卡或正式仓库。

这是源码／AST收口，不是新测试通过、科学验收或正式安装。精确 SHA 与两条未来 nodeids 见同目录 `ENTRY_REPAIR_SOURCE_REVIEW.json`。
'''
md_path = EXT / 'ENTRY_REPAIR_SOURCE_REVIEW.md'
with md_path.open('x', encoding='utf-8', newline='\n') as stream:
    stream.write(md)
report = dict(
    schema_version='MINTEGRATE1-entry-repair-source-review-1.0',
    status='pass_static_minimal_entry_repair_and_mock_test_source_not_executed',
    created_utc=datetime.now(timezone.utc).isoformat(), authorized=False, executed=False,
    old_entry_finding='ENTRY-1 AttributeError before typed response',
    resolution='Type guard is statically before saved_resume_defaults; existing TMCError/ValueError contract catches invalid_settings.',
    reviewed_external_SHA256=pins,
    original_candidate_SHA256={name: sha(OLD / name) for name in edited if (OLD / name).exists()},
    changed_files=edited, unchanged_frozen_files=unchanged,
    test_nodeids=selectors, test_instances=2,
    CLI_scope='Help and one existing error string only; argument wiring/defaults/return behavior unchanged',
    documentation_sha256=sha(md_path),
    checks=['All nine owned/reused candidate files parsed as AST without import.',
        'Typed settings guard precedes the first saved defaults access inside the original try.',
        'Five remaining original candidates are byte-identical to closed M-RESUME1 sources.',
        'Both negative instances forbid defaults/build/solve and use no parent file or NPZ.',
        'Original closed candidate and formal repository sources were not edited.'],
    findings=[], limits=['Test source was inspected only, not collected or run. Future complete selector freezing is owned by input_scope.',
        'Only invalid settings rejection and CLI text changed; scientific correctness and integrated runtime compatibility require later authorized checks.'],
    actions=dict(HF_import=0, collect=0, pytest=0, NPZ_byte_read_or_decode=0,
        model_force_tangent_solver_observer_HP_render=0, formal_repository_mutation=0),
)
json_path = EXT / 'ENTRY_REPAIR_SOURCE_REVIEW.json'
with json_path.open('x', encoding='utf-8', newline='\n') as stream:
    stream.write(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
print(json.dumps(dict(status=report['status'], JSON_SHA256=sha(json_path), MD_SHA256=sha(md_path),
    owned_files={name: pins['candidate/hf_repo/' + name] for name in edited}, test_nodeids=selectors)))
