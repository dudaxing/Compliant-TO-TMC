"""Ordinary source/AST review freeze; never execute the publication tool."""
import ast
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
REL = 'lf_data_preparation/native_interface_001/saved_integration_001'
BASE = '2b550d09f4347240ef6cb626b4c829566b638e61'
sha = lambda path: sha256(path.read_bytes()).hexdigest()
read = lambda path: json.loads(path.read_bytes())
source = HERE / 'deliver_execution.py'
formal = ROOT / REL / 'author/deliver_execution.py'
assert source.read_bytes() == formal.read_bytes()
tree = ast.parse(source.read_text(encoding='utf-8-sig'), filename=str(source))
imports = sorted({node.module.split('.')[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)} |
                 {alias.name.split('.')[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names})
assert set(imports) == {'datetime', 'hashlib', 'pathlib', 'argparse', 'json', 'subprocess'}
proof_path = ROOT / REL / 'author/source_publication_receipt.json'
proof = read(proof_path)
assert proof['published_commit'] == BASE and proof['status'] == 'published_and_incrementally_restored_pass'
assert proof['prepared_card'] == 'M-INTEGRATE1' and proof['authorized'] is proof['executed'] is False
oldraw = subprocess.check_output(['git', 'show', BASE + ':handoff/repository_manifest.json'], cwd=ROOT)
old = json.loads(oldraw)
assert sha256(oldraw).hexdigest() == proof['manifest_sha256']
assert len(old['files']) == proof['ordinary_manifest_files'] == 19114
assert sum(row['bytes'] for row in old['files']) == proof['ordinary_manifest_bytes'] == 9715700208
assert old['science_version'] == '0.5.0'
report = dict(
    schema_version='native-integration-execution-delivery-tool-static-review-1.0',
    status='pass_static_incremental_execution_delivery_tool_not_run',
    created_utc=datetime.now(timezone.utc).isoformat(), reviewer='volume_candidate_author',
    executed_publication_tool=False, executed_new_science=False,
    source_commit=BASE, findings=[],
    checks=[
        'Reviewed external/formal deliver_execution.py exact bytes and AST; imports are ordinary standard library only.',
        'Actual prepared publication proof binds BASE manifest raw SHA, 19114 existing entries/9715700208 bytes, M-INTEGRATE1 prepared card and authorization/execution false.',
        'Finalization permits exactly six installed old default-source replacements plus four documented fronts, five new default files and actual new stage evidence; no old deletions.',
        'Exact Git index/worktree delta is checked; only allowed new delta bytes are hashed while the historical manifest entries are inherited without a full old science scan.',
        'check_execution binds actual authorized direct reply/source proof/BASE/protocol, completed outer/helper/tests PASS, one launch/test run, complete 11 installed identities, 108 immutable pins and installed runtime pins.',
        'The current success contract requires the exact 25 selectors and 75 passed setup/call/teardown reports, recorded resource bounds and original immutable records.',
        'All stage files must equal manifest stage entries; four pytest_cache files and raw NPZ outputs must therefore be explicitly staged and restored as bytes, never decoded by this tool.',
        'Four front history records preserve old raw bytes exactly once; frozen closed-output identities and final review config SHA/map bind the complete new publication delta.',
        'Verify requires one direct BASE child, main/correct origin, live remote equal commit, clean source/restore, exact manifest/track set/delta hashes and unchanged inherited entries/science version/baseline.',
        'Tool itself performs neither installation, tests, science, Git commit/push nor restore checkout; source/restore verification is ordinary metadata after root actions.',
    ],
    reviewed_external_SHA256={'deliver_execution.py':sha(source)},
    reviewed_repository_SHA256={REL+'/author/deliver_execution.py':sha(formal), REL+'/author/source_publication_receipt.json':sha(proof_path)},
    limitations=['Source/AST and existing ordinary proof metadata only. The execution delivery config and final complete package remain to be reviewed after root freezes them.',
                 'No finalize/verify call, HF import, test/CLI call, NPZ decode, mechanics, observer, HP or rendering was performed.'],
)
report_path = HERE / 'DELIVERY_TOOL_STATIC_REVIEW.json'
report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
md = '''# M-INTEGRATE1 执行发布工具静审

结论：未见实际阻断。外部与正式 author 副本字节一致，AST 可解析，只有标准库普通元数据操作；没有调用该工具。

工具继承实际 2b550 已发布／恢复清单的 19114 个条目／9715700208 字节。旧条目只允许明确的十项变化：六个默认源码和四份前门文档；五个新增默认文件及阶段实际输出按精确 delta 加入。历史科学大文件不重扫。

执行验收读取实际授权、来源 proof 和 completed outer/helper/tests，核一次 11 安装、108 不变 pins、默认 runtime、25 精确测试与 75 个通过的 phase 报告。全 stage 文件必须出现在清单，故四个 pytest_cache 和 NPZ 原字节证据须明确 Git add；工具只哈希字节，不解码。

finalize 只写增量 manifest 和外部收据。commit、push、恢复由 root 另行进行；verify 再要求唯一 BASE 子提交、main/origin、真实远端相等、source/restore clean、清单和 delta 原字节一致、旧条目及 science0.5.0/baseline 保持。四份旧文完整原字节各保留一次，父 NOT_PASS 和物理资格不升级。

执行 config 冻结后仍需完整交付终审；本结论不冒充未来发布／恢复成功。准确来源 SHA 见同名 JSON。本次没有 HF 导入、测试／CLI、数组解码、科学计算或绘图。
'''
md_path = HERE / 'DELIVERY_TOOL_STATIC_REVIEW.md'
md_path.write_text(md, encoding='utf-8')
print(json.dumps(dict(status=report['status'], tool_sha256=sha(source), json_sha256=sha(report_path), md_sha256=sha(md_path)), ensure_ascii=False))
