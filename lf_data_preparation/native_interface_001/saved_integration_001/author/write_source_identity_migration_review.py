"""Ordinary JSON, source bytes and AST only; never call an HF entry point."""
import ast
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

EXT = Path(__file__).resolve().parent
ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
PRODUCTION = [
    'hf_repo/scripts/evaluate_native.py', 'hf_repo/scripts/solve_native_mean.py',
    'hf_repo/src/hf_eval/native_evaluate.py', 'hf_repo/src/hf_eval/native_mean.py',
    'hf_repo/src/hf_eval/native_response.py', 'hf_repo/src/hf_eval/native_resume.py',
    'hf_repo/src/hf_eval/split_displacement.py',
]
sha = lambda p: sha256(p.read_bytes()).hexdigest()
reviewed = {}
def read_json(name):
    p = ROOT / name
    assert p.suffix == '.json'
    reviewed[name] = sha(p)
    return json.loads(p.read_text(encoding='utf-8'))

response_paths = {
    'right2': 'lf_data_preparation/native_interface_001/api_validation_001/run_001/saved_right2col_response.json',
    'right4': 'lf_data_preparation/native_interface_001/api_validation_001/run_001/saved_right4col_response.json',
    'nested_h05': 'lf_data_preparation/native_interface_001/nested_link_001/run_001/linked_response.json',
}
reference_paths = {
    'right2': 'lf_data_preparation/native_workpiece_001/right_margin_cycle_001/reference/summary.json',
    'right4': 'lf_data_preparation/native_workpiece_001/right_margin4_cycle_001/reference/summary.json',
    'nested_h05': 'lf_data_preparation/native_interface_001/nested_reference_002/run_001/reference/summary.json',
}
observations = {}
for label, name in reference_paths.items():
    ref = read_json(name)
    response = read_json(response_paths[label])
    src = ref['source_bindings']
    intersects = sorted(set(src).intersection(PRODUCTION))
    current_matches = {}
    installed_matches = {}
    for rel, pin in src.items():
        p = ROOT / rel
        assert p.suffix == '.py' and p.is_file()
        current_matches[rel] = sha(p) == pin
        reviewed[rel] = sha(p)
        target = EXT / 'candidate' / rel
        installed_matches[rel] = sha(target) == pin if rel in PRODUCTION else current_matches[rel]
    saved_ref = response['independent_reference']
    assert saved_ref['report']['path'] == name
    assert saved_ref['report']['sha256'] == reviewed[name]
    assert saved_ref['status'] == 'matched'
    assert saved_ref['accepted_reference_pass'] is True
    assert saved_ref['full_path_reference_pass'] is True
    assert saved_ref['source_bindings_verified'] is True
    assert ref['status'] == 'pass'
    assert ref['accepted_states'] == 24
    assert ref['HP_calls_started'] == ref['HP_calls_completed'] == 48
    observations[label] = dict(
        summary_path=name, summary_sha256=reviewed[name],
        saved_response_path=response_paths[label], saved_response_sha256=reviewed[response_paths[label]],
        summary_source_binding_count=len(src), installed_production_intersection=intersects,
        current_source_mismatches=[key for key, match in current_matches.items() if not match],
        proposed_installed_source_mismatches=[key for key, match in installed_matches.items() if not match],
        saved_summary_status=ref['status'], saved_accepted_states=ref['accepted_states'],
        saved_HP_calls_started=ref['HP_calls_started'], saved_HP_calls_completed=ref['HP_calls_completed'],
        saved_reference_match={key:saved_ref[key] for key in ('status','accepted_reference_pass',
            'full_path_reference_pass','source_bindings_verified','HP_all_columns_qualified',
            'contact_qualified','clamp_qualified','pressure_qualified','HF5_qualified')},
        qualification_scope=ref['qualification'],
        prediction_scope='Source-byte component only; no summarizer or independent reference was rerun.',
    )
assert observations['right2']['installed_production_intersection'] == observations['right4']['installed_production_intersection'] == [
    'hf_repo/src/hf_eval/native_mean.py', 'hf_repo/src/hf_eval/split_displacement.py']
assert len(observations['right2']['proposed_installed_source_mismatches']) == len(observations['right4']['proposed_installed_source_mismatches']) == 2
assert not observations['nested_h05']['installed_production_intersection']
assert not observations['nested_h05']['proposed_installed_source_mismatches']
protocol_name = 'lf_data_preparation/native_interface_001/nested_reference_002/protocol.json'
protocol = read_json(protocol_name)
capsule = protocol['reference_sources']
assert len(capsule) == 11
assert not set(capsule).intersection(PRODUCTION)
assert set(capsule).issubset(set(read_json(reference_paths['nested_h05'])['source_bindings']))

source_name = 'hf_repo/src/hf_eval/native_response.py'
default_path = ROOT / source_name
candidate_path = EXT / 'candidate' / source_name
default_tree = ast.parse(default_path.read_text(encoding='utf-8'), filename=source_name)
candidate_tree = ast.parse(candidate_path.read_text(encoding='utf-8'), filename='candidate/' + source_name)
functions = {}
for name in ('_resolve', '_binding_matches', '_reference'):
    old = next(n for n in default_tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    new = next(n for n in candidate_tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    identical = ast.dump(old, include_attributes=False) == ast.dump(new, include_attributes=False)
    assert identical
    functions[name] = dict(AST_identical=True, default_lines=[old.lineno,old.end_lineno],
        candidate_lines=[new.lineno,new.end_lineno])
external = {'candidate/' + name: sha(EXT / 'candidate' / name) for name in PRODUCTION}
md = '''# 来源身份迁移静审

本次只读普通 JSON、Python 源码字节与 AST，没有调用总结 API、HP 或科学入口，也没有读取 NPZ。

拟安装的七条 production 路径与原 right2／right4 参考各自 27 条 `summary.source_bindings` 仅有两条交集：`native_mean.py` 和 `split_displacement.py`。它们拟安装后的字节确实不同。因此，安装后若以当前仓库源码重新总结这两份旧结果，严格来源核对会将其标记为 `mismatch`；这是来源迁移的预期后果，不证明原有 24 态／48 HP 数值证据失效。

两份原 API 保存响应仍记录 `matched`、accepted／full-path reference pass 和 source bindings verified。它们、原参考摘要及原结果均保留为历史证据，本次没有重写、重跑或升级资格。

M-REF2 `protocol.reference_sources` 实际有 11 条，其保存摘要 `source_bindings` 有 12 条；后者额外绑定 `execute_nested_reference.py`。两组均不与七条安装路径相交，且本次检查全部参考源仍匹配。因此不能把 M-REF2 与粗网格两份参考一并称为当前来源失配；未来总结仍须逐项通过结果、模型、状态和 2N HP 等原身份门。本次只预测来源字节这一项。

候选 `_resolve`、`_binding_matches`、`_reference` 的 AST 与当前默认源码相同。原 `Declared reference source bindings were not verified` 严格门保留；不更新旧 pins，不静默放宽门，也不重新生成旧响应。已保存机械参考资格不等于全部切线列、接触压力、有效夹持力或 HF5 资格。
'''
md_path=EXT/'SOURCE_IDENTITY_MIGRATION_REVIEW.md'
with md_path.open('x',encoding='utf-8',newline='\n') as out: out.write(md)
report = dict(schema_version='MINTEGRATE1-source-identity-migration-review-1.0',
    status='pass_static_source_identity_migration_review_no_new_execution',
    created_utc=datetime.now(timezone.utc).isoformat(), authorized=False, executed=False,
    installed_production_paths=PRODUCTION, references=observations,
    MREF2_protocol_reference_sources=dict(count=len(capsule), paths=list(capsule),
        installed_production_intersection=[]),
    strict_reference_matching_functions=functions,
    reviewed_formal_SHA256=reviewed, reviewed_external_SHA256=external,
    findings=[], blockers=[],
    preservation='Original summaries/results/saved matched responses retained; current-source coarse re-summary source mismatch remains strict.',
    actions=dict(candidate_HF_import=0, test_collect=0, tests=0, NPZ_byte_read_or_decode=0,
        force_tangent_solver_HP_observer_render=0, reference_API_or_summary=0, formal_mutation=0),
    documentation_sha256=sha(md_path))
json_path=EXT/'source_identity_migration_review.json'
with json_path.open('x',encoding='utf-8',newline='\n') as out:
    out.write(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
print(json.dumps(dict(status=report['status'],JSON_SHA256=sha(json_path),MD_SHA256=sha(md_path),
    observations={key:dict(summary_sources=row['summary_source_binding_count'],
        intersection=row['installed_production_intersection'],
        proposed_source_mismatches=row['proposed_installed_source_mismatches']) for key,row in observations.items()})))
