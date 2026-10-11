"""Ordinary file/AST identity freeze for the independent cross-source review."""
import ast
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

EXT = Path(__file__).resolve().parent
ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
REL = 'lf_data_preparation/native_interface_001/saved_integration_001'
BASE = 'd45f6ee92d8a0d6ca740772a1762abdc691489fa'
sha = lambda path: sha256(path.read_bytes()).hexdigest()
read = lambda path: json.loads(path.read_bytes())
protocol_file = ROOT / REL / 'protocol.json'
protocol = read(protocol_file)
scope = read(EXT / 'test_scope_final.json')
assert sha(protocol_file) == '62396704768bd3f6cd4ec09bf2e438c126ebd1867b590b5a119d4671a26e666e'
assert protocol['source_baseline_commit'] == BASE
assert protocol['card'] == 'M-INTEGRATE1' and protocol['prepared'] is True
assert protocol['authorized'] is protocol['executed'] is False
assert scope['authorized'] is scope['executed'] is scope['collected'] is False
assert protocol['focused_test_selectors'] == scope['focused_test_selectors']
assert len(protocol['focused_test_selectors']) == len(set(protocol['focused_test_selectors'])) == 25
assert (protocol['focused_tests_seconds'], protocol['helper_seconds'], protocol['outer_seconds'], protocol['sampled_RSS_bytes']) == (180, 300, 360, 8589934592)
assert len(protocol['bindings']) == 108 and len(protocol['installation']) == 11
assert len([r for r in protocol['installation'] if r['previous_sha256'] is not None]) == 6
assert len([r for r in protocol['installation'] if r['previous_sha256'] is None]) == 5
targets = {row['target'] for row in protocol['installation']}
assert not targets.intersection(protocol['bindings'])
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == BASE
assert not (ROOT / REL / 'run_001').exists()
assert not (ROOT / REL / 'integration_launch.json').exists()
assert not (ROOT / REL / 'author/authorization.json').exists()
repo_hashes = {REL + '/protocol.json': sha(protocol_file)}
for name, pin in protocol['bindings'].items():
    assert not name.lower().endswith('.npz')
    actual = sha(ROOT / name)
    assert actual == pin
    repo_hashes[name] = actual
candidate_target_pins = {}
for row in protocol['installation']:
    source = ROOT / row['candidate']
    assert sha(source) == row['sha256']
    target = ROOT / row['target']
    assert (sha(target) if target.exists() else None) == row['previous_sha256']
    if row['baseline_snapshot'] is not None:
        assert sha(ROOT / row['baseline_snapshot']) == row['previous_sha256']
    candidate_target_pins[row['target']] = row['sha256']
for name, pin in protocol['installed_runtime_SHA256'].items():
    assert pin == candidate_target_pins.get(name, sha(ROOT / name) if (ROOT / name).exists() else None)
for row in scope['selected_test_contracts']:
    source = (EXT if row['source_kind'] == 'external_candidate' else ROOT) / row['source_file']
    assert sha(source) == row['source_sha256']
    tree = ast.parse(source.read_text(encoding='utf-8-sig'), filename=str(source))
    assert row['function'] in {n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
external_names = [
    'execute_integration.py', 'launch_integration.py', 'integration_focused_budget.py',
    'candidate/hf_repo/tests/test_native_cli_compatibility.py',
    'candidate/hf_repo/tests/test_native_reference_source_migration.py',
    'test_scope_final.json', 'M-INTEGRATE1_CARD.md',
]
external_hashes = {name: sha(EXT / name) for name in external_names}
for name in external_names:
    formal_name = REL + ('/author/' if name == 'test_scope_final.json' else '/') + name
    assert sha(ROOT / formal_name) == external_hashes[name]
    repo_hashes[formal_name] = external_hashes[name]
for name in external_names:
    if name.endswith('.py'):
        ast.parse((EXT / name).read_text(encoding='utf-8-sig'), filename=name)
checks = [
    'CLI tests load scripts relative to the installed formal hf_repo; fake public entry calls and Path.open NPZ prohibition keep argument transport separate from mechanics.',
    'Three CLI cases cover evaluate saved flags, Mean zero defaults and Mean saved inherited suffix/settings; independent typeguard assessment is explicitly excluded from this author review.',
    'Source migration uses ordinary JSON/current source hashes only, keeps original positive result/reference/qualified bytes, retains production success while rejecting old reference qualification on current source mismatch.',
    'Pytest plugin normalizes item.path relative to formal repository plus item.name, requires the frozen ordered 25 selectors and 25 passed call reports, and verifies imported HF origins.',
    'Observed NativeMean force/tangent alias starts/completions and model sizes are scoped to selected tiny tests, without a universal kernel-count claim; real models are bounded to 16 cells/50 DOFs.',
    'Future helper authenticates the actual direct reply/source publication/HEAD/protocol before one installation; six replacement and five new files have preserved snapshots/absence checks.',
    'One pytest child uses the installed formal src/tests, the frozen plugin and run-contained temp/cache/XML/log; cooperative stop is propagated with no force, retry or automatic rollback.',
    'Resolved final-helper evidence/receipt time-boundary finding is present in final source: resource closure during hashes or receipt writing sets NOT_PASS before pass printing.',
    'Launcher combines child exit, helper status, immutable pins and cooperative sampled tree resource accounting; failed partial installation/tests remain visible.',
    'Actual protocol/source copies, all 108 ordinary byte pins, exact 11/25 metadata and projected installed runtime hashes agree; formal six old defaults remain unmodified and no run/auth exists.',
    'Card now describes the single original two-frame M-RESUME1 GIF; old saved results and qualification are not rewritten or upgraded.',
]
report = dict(
    schema_version='native-integration-cross-source-review-1.0',
    status='pass_static_integration_cross_source_wrapper_and_mock_test_review_not_executed',
    created_utc=datetime.now(timezone.utc).isoformat(), reviewer='volume_candidate_author',
    source_baseline_commit=BASE, card='M-INTEGRATE1', authorized=False, executed=False,
    collected=False, new_scientific_execution=False, default_core_installed=False,
    protocol_sha256=sha(protocol_file), findings=[],
    resolved_source_findings=[dict(topic='Final helper resource closure', disposition='Root added final evidence and receipt-write resource checks; reviewed final source only.')],
    checks=checks, frozen_installation_files=11, frozen_test_instances=25, immutable_bindings=108,
    independent_scope_excluded=['Self-authored native_evaluate settings typeguard and its dict/object tests: independently reviewed by the math peer; their identities are used here only for the frozen selection/package contract.'],
    limitations=['Static source/AST and ordinary raw file identity only; no HF import, collection, test run, NPZ access/decode, solver/observer, HP or rendering.',
                 'Prepared selectors and finite budgets do not assert actual collection, timing, tests passed, completed installation or new physical qualification.'],
    reviewed_external_SHA256=external_hashes, reviewed_repository_SHA256=dict(sorted(repo_hashes.items())),
)
json_file = EXT / 'INTEGRATION_CROSS_REVIEW.json'
json_file.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
md = '''# M-INTEGRATE1 入口／测试／包装交叉静审

结论：最终源码未见剩余阻断，可继续普通准备期发布。此结论是源码、AST、JSON 和原字节身份审阅，不是安装或测试通过。

三项 CLI 测试从正式安装目录寻找脚本，测试只传递参数；真实保存读取、模型、求解与写出入口被禁止，NPZ 打开也被禁止。它们分别覆盖 evaluate 的保存态参数、Mean 的零起点默认值、Mean 的保存态原绝对后缀与设置继承。旧正参考迁移测试只读取普通 JSON 和源码身份：生产成功保持，旧参考因当前源码变化成为严格 mismatch，原结果、参考及已保存资格响应的字节保留。

插件用仓库相对 item.path 与 item.name 形成选择身份，要求冻结的顺序 25 项以及 25 个通过的 call 报告，并核实际导入 HF 源路径。其计数只针对 NativeMean 四个 NumPy 力／切线别名；真实小模型上限为 16 单元／50 DOF，不称为全核调用计数。

包装只允许一次安装及一次有限 pytest 子进程。11 个安装文件是六个替换与五个新增，失败保存真实部分产物，不静默恢复旧源码。协作停止、采样 RSS、180 秒测试／300 秒 helper／360 秒 outer 由实际终态记录承载。此前发现的 helper 最后哈希／收据阶段资源检查缺口已由 root 最小修正，最终源码在写出通过前检查该窗口。卡片的原可视化描述已更正为一份两帧 GIF。

本次普通核对确认正式 protocol 与外部源副本一致，108 个普通字节绑定、11 个安装映射和冻结 25 项一致；当前正式默认源码仍为原六个字节版本，尚无本卡授权、安装、collect 或运行。旧物理结果与 HF5、压力、有效夹持、稳定性资格不升级。

本作者曾编写 settings 类型入口修复及 dict/object 测试，因此本报告不将该部分列为独立实现审阅；math peer 单独审阅它。此处只核其包装与选择身份。准确源码 SHA、protocol SHA 与核查范围见同名 JSON。没有执行 HF 导入、测试、科学计算或绘图。
'''
md_file = EXT / 'INTEGRATION_CROSS_REVIEW.md'
md_file.write_text(md, encoding='utf-8')
print(json.dumps(dict(status=report['status'], json_sha256=sha(json_file), md_sha256=sha(md_file), external_SHA256=external_hashes), ensure_ascii=False))
