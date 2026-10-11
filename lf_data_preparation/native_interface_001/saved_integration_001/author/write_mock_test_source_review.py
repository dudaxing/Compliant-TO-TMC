"""Parse/read test sources without importing or collecting them."""
import ast
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

EXT=Path(__file__).resolve().parent
ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
sha=lambda p:sha256(p.read_bytes()).hexdigest()
names=['test_native_cli_compatibility.py','test_native_reference_source_migration.py',
       'test_native_evaluate_settings.py']
pins={}
records={}
trees={}
for name in names:
    rel='candidate/hf_repo/tests/'+name
    p=EXT/rel
    tree=ast.parse(p.read_text(encoding='utf-8'),filename=rel)
    pins[rel]=sha(p)
    trees[name]=tree
    records[name]=dict(functions=[dict(name=n.name,lines=[n.lineno,n.end_lineno])
        for n in tree.body if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')])
assert len(records[names[0]]['functions'])==3
assert len(records[names[1]]['functions'])==1
assert len(records[names[2]]['functions'])==1
ref=trees[names[1]]
literal_names={n.targets[0].id:ast.literal_eval(n.value) for n in ref.body
    if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)
    and isinstance(n.value,ast.Constant)}
pin_node=next(n.value for n in ref.body if isinstance(n,ast.Assign)
    and any(isinstance(target,ast.Name) and target.id=='OLD_PINS' for target in n.targets))
oldpins={literal_names[key.id] if isinstance(key,ast.Name) else ast.literal_eval(key):ast.literal_eval(value)
    for key,value in zip(pin_node.keys,pin_node.values)}
for rel,pin in oldpins.items():
    assert Path(rel).suffix=='.json'
    assert sha(ROOT/rel)==pin
cli=trees[names[0]]
static=findings=[]
text=(EXT/'candidate/hf_repo/tests/test_native_cli_compatibility.py').read_text(encoding='utf-8')
assert 'monkeypatch.setattr(Path, "open", ordinary_files_only)' in text
assert 'monkeypatch.setattr(native_resume, "saved_resume_defaults", forbidden)' in text
assert '"build_native_project", "solve_native_mean", "write_native_mean"' in text
assert 'monkeypatch.setattr(cli, "STARTED", 10.)' in text
assert 'monkeypatch.setattr(cli, "perf_counter", lambda: 11.)' in text
static += ['Three CLI selectors transport arguments using mocks; real defaults/build/solve/write aliases are forbidden.',
    'CLI source loader restores sys.path and mean CLI clock is deterministic, not a physics/runtime-bound test.',
    'Reference selector reads three pinned ordinary historical JSON records, rejects NPZ Path.open and numpy.load, and asserts records remain byte-identical.',
    'Reference selector keeps old status pass/48 HP descriptive while current installed-source match must be false.',
    'Two invalid-settings parameter instances prohibit saved defaults and mechanics before absent parent access.']
md='''# 新增入口与来源迁移测试：独立源码静审

只读／AST 检查了三个测试文件，没有导入、collect 或运行测试。三例 CLI 使用 mock 检查零起点默认值、保存态 suffix／settings 继承及 evaluate 参数转发；真实父读取、建模、求解、写结果均被禁止。mean CLI 的时钟被固定，因此这里检验参数运输，不检验物理计算或实际耗时。

来源迁移测试使用三份真实普通 JSON 的原 SHA，检查当前默认源码的 mean／split 来源与旧参考不同，调用未来普通保存摘要后必须严格 `mismatch`，同时保留原 pass／48 HP 报告和旧 qualified 响应字节。它明确禁止 NPZ 打开与数组解码，未放宽来源门。两例不合法 settings 则应在父文件读取或力学调用前返回原类型化输入错误。

没有发现静态阻断。六个新增实例仍须未来唯一获批测试运行验证；本报告不是测试通过或力学资格。
'''
mdp=EXT/'MOCK_TEST_SOURCE_REVIEW.md'
with mdp.open('x',encoding='utf-8',newline='\n') as o:o.write(md)
report=dict(schema_version='MINTEGRATE1-mock-test-static-review-1.0',
    status='pass_static_six_additional_mock_JSON_test_instances_not_collected_not_executed',
    created_utc=datetime.now(timezone.utc).isoformat(), authorized=False,executed=False,
    reviewed_external_SHA256=pins, AST_records=records, historical_JSON_raw_SHA256=oldpins,
    additional_instances=dict(CLI=3,source_migration=1,invalid_settings=2,total=6),
    checks=static,findings=[],blockers=[],
    limits=['AST/static consistency only; no test collection or runtime success claim.',
        'The future source-migration selector must run only after the candidate installation, not against pre-install default sources.'],
    actions=dict(HF_import=0,collect=0,tests=0,NPZ_byte_read_or_decode=0,
        scientific_API_or_F_T_HP_solver_plot=0,formal_mutation=0),documentation_sha256=sha(mdp))
jp=EXT/'mock_test_source_review.json'
with jp.open('x',encoding='utf-8',newline='\n') as o:o.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(status=report['status'],JSON_SHA256=sha(jp),MD_SHA256=sha(mdp),sources=pins)))
