"""Archive ordinary source preparation only; never install, import HF or test."""
import ast
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
HERE = Path(__file__).resolve().parent
BASE = 'd45f6ee92d8a0d6ca740772a1762abdc691489fa'
REL = 'lf_data_preparation/native_interface_001/saved_integration_001'
STAGE = ROOT / REL
sha = lambda path: sha256(path.read_bytes()).hexdigest()
read = lambda path: json.loads(path.read_bytes())
git = lambda *args: subprocess.check_output(['git', '-c', 'gc.auto=0', *args], cwd=ROOT)


def new_bytes(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as output:
        output.write(raw)


def new_json(path, value):
    new_bytes(path, (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))


def main():
    assert git('rev-parse', 'HEAD').decode().strip() == BASE and not git('status', '--porcelain')
    assert git('branch', '--show-current').decode().strip() == 'main'
    assert git('remote', 'get-url', '--push', 'origin').decode().strip() == 'https://github.com/dudaxing/Compliant-TO-TMC.git'
    assert not STAGE.exists()
    selection = read(HERE / 'test_scope_final.json')
    assert selection['status'].startswith('pass') and len(selection['focused_test_selectors']) == 25
    candidates = {path.relative_to(HERE / 'candidate').as_posix(): path for path in (HERE / 'candidate/hf_repo').rglob('*.py')}
    assert len(candidates) == 11
    assert selection['actual_new_source_SHA256'] == {'candidate/' + name: sha(path) for name, path in candidates.items()}
    for path in candidates.values():
        ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    for filename in ('execute_integration.py', 'launch_integration.py', 'integration_focused_budget.py', 'deliver_integration_preparation.py'):
        ast.parse((HERE / filename).read_text(encoding='utf-8'), filename=filename)
    for name, pin in selection['fixture_bindings'].items():
        assert Path(name).suffix != '.npz' and sha(ROOT / name) == pin
    install = []
    for name, path in sorted(candidates.items()):
        previous = sha(ROOT / name) if (ROOT / name).exists() else None
        candidate = REL + '/candidate/' + name
        new_bytes(ROOT / candidate, path.read_bytes())
        snapshot = None
        if previous is not None:
            snapshot = REL + '/baseline/' + name
            new_bytes(ROOT / snapshot, (ROOT / name).read_bytes())
        install.append(dict(target=name, candidate=candidate, sha256=sha(path), previous_sha256=previous, baseline_snapshot=snapshot))
    assert sum(row['previous_sha256'] is not None for row in install) == 6
    for filename in ('execute_integration.py', 'launch_integration.py', 'integration_focused_budget.py', 'M-INTEGRATE1_CARD.md'):
        new_bytes(STAGE / filename, (HERE / filename).read_bytes())
    ordinary = ('overlay_origin.json', 'ENTRY_COMPATIBILITY_REVIEW.json', 'ENTRY_COMPATIBILITY_REVIEW.md',
        'ENTRY_REPAIR_SOURCE_REVIEW.json', 'ENTRY_REPAIR_SOURCE_REVIEW.md',
        'controller_compatibility_review.json', 'CONTROLLER_COMPATIBILITY_REVIEW.md',
        'test_scope_review.json', 'TEST_SCOPE_REVIEW.md', 'test_scope_final.json', 'TEST_SCOPE_FINAL.md',
        'source_identity_migration_review.json', 'SOURCE_IDENTITY_MIGRATION_REVIEW.md',
        'mock_test_source_review.json', 'MOCK_TEST_SOURCE_REVIEW.md')
    for filename in ordinary:
        new_bytes(STAGE / 'author' / filename, (HERE / filename).read_bytes())
    for path in HERE.glob('*.py'):
        new_bytes(STAGE / 'author' / path.name, path.read_bytes())
    previous_proof = Path('D:/hf-native-workpiece-api-author-20261011/MRESUME1_execution_review_001/execution_publication_receipt.json')
    proof = read(previous_proof)
    assert proof['published_commit'] == BASE and proof['status'] == 'published_and_incrementally_restored_pass'
    new_bytes(STAGE / 'author/M_RESUME1_execution_publication_receipt.json', previous_proof.read_bytes())
    installed = {'hf_repo/src/hf_eval/' + path.name: sha(path) for path in (ROOT / 'hf_repo/src/hf_eval').glob('*.py')}
    assert len(installed) == 51
    installed.update({row['target']: row['sha256'] for row in install})
    changing = {row['target'] for row in install}
    stable = {name: pin for name, pin in installed.items() if name not in changing}
    stable.update(selection['fixture_bindings'])
    assert not changing & stable.keys()
    old_stage = 'lf_data_preparation/native_interface_001/saved_continuation_001'
    for suffix in ('protocol.json', 'production_launch.json', 'run_001/execution_receipt.json',
                   'run_001/focused_test_receipt.json', 'RESULTS.md', 'NEXT_STEP_REVIEW.md',
                   'run_001/resumed_alpha_half/result.json', 'run_001/resumed_alpha_half/response.json'):
        stable[old_stage + '/' + suffix] = sha(ROOT / old_stage / suffix)
    for row in install:
        stable[row['candidate']] = row['sha256']
        if row['baseline_snapshot']:
            stable[row['baseline_snapshot']] = row['previous_sha256']
    for filename in ('execute_integration.py', 'launch_integration.py', 'integration_focused_budget.py', 'M-INTEGRATE1_CARD.md'):
        stable[REL + '/' + filename] = sha(STAGE / filename)
    stable[REL + '/author/test_scope_final.json'] = sha(STAGE / 'author/test_scope_final.json')
    stable[REL + '/author/M_RESUME1_execution_publication_receipt.json'] = sha(STAGE / 'author/M_RESUME1_execution_publication_receipt.json')
    protocol = dict(schema_version='saved-native-integration-protocol-1.0', card='M-INTEGRATE1',
        prepared=True, authorized=False, executed=False, created_utc=datetime.now(timezone.utc).isoformat(),
        source_baseline_commit=BASE, origin='https://github.com/dudaxing/Compliant-TO-TMC.git',
        installation=install, installed_runtime_SHA256=installed, bindings=dict(sorted(stable.items())),
        focused_test_selectors=selection['focused_test_selectors'], focused_tests_seconds=180,
        helper_seconds=300, outer_seconds=360, sampled_RSS_bytes=8 * 1024**3,
        maximum_new_real_model=dict(cells=16, nodes=25, dofs=50),
        scientific_scope='Temporary tiny tests only; no original gripper/old NPZ/HP/JIT/plots',
        original_science_version='0.5.0', automatic_rollback=False, retries=0,
        gate='11 complete installed bytes; exact25 collection/call pass; default HF source paths; original gates/pins; resource windows; exit0/stopNone',
        old_reference_migration='right2/right4 current-source mismatch; old saved qualified records and HP remain original',
        original_parent_NOT_PASS_and_qualification_unchanged=True, whole_HF5_complete=False)
    new_json(STAGE / 'protocol.json', protocol)
    card_sha = sha(STAGE / 'M-INTEGRATE1_CARD.md')
    results = f'''# M-INTEGRATE1 准备结果：默认入口集成候选，尚未安装或执行

目标仍是独立 HF 有限变形／TMC 前向评价，读取普通 LF 几何，提供实际变形、反力和可解释工件作用给外部研究层。最近一步让 M-RESUME1 已实际验证的同任务保存态续算进入默认 Mean/API/CLI，并以有限兼容回归确认零起点、保存、错误和旧来源资格语义。不是新夹持参数扫描。

已有实际证据：M-RESUME1 唯一执行PASS，5局部测试、原峰值013复核、首次1.20→1.15下降及3PNG／2态GIF已发布 d45f6ee。两端点 R=0.37865427196005513／0.3470376815403639 N，下半工件 total Fy=0.12492121630032427／0.10671287553103108 N。原 M-ALPHA1 NOT_PASS和未完成完整原路径保持，新alpha无HP，弱式工件力不等于总压力或有效夹持力。详见[原实际结果](../saved_continuation_001/RESULTS.md)。

本轮做了源／AST兼容审阅，找到 saved API 的 settings 非法类型会在 typed error 前泄漏 AttributeError；新候选加入已有 invalid_settings 门，dict/object负测试。两个CLI只修保存态帮助文字。续算Mean/controller/source与原M-RESUME1对应字节继承，力核／切线原字节保持。新候选11份、6原源码快照、25精确实例、协议、三个一次执行包装和独立审阅已存本阶段。正式默认 hf_repo 尚未改；原已闭卡候选／结果／pins未改。

来源迁移有实际功能影响：原right2/right4各27份sources与安装生产7份只有 native_mean/split_displacement 两交集；安装后用当前reader重总结原正参考会严格mismatch。旧保存的qualified响应仍是历史原值，新测试同时核生产success、严格mismatch和旧三文件字节不变。不放宽旧门。M-REF2 protocol11／summary12份sources均零交集；不能说全部旧HP失效。完整来源结论见author/SOURCE_IDENTITY_MIGRATION_REVIEW.md。

静审不是测试PASS。本轮新HF import、collect、pytest、NPZ解码、model/F/T/HP/solver/observer/绘图均0。M-INTEGRATE1未授权／未执行：未来唯一安装11份＋25精确pytest，tests180/helper300/outer360秒、采样8GiB；首错停、保实际安装partial，无重试／修复重跑／延期／force／自动回滚。原13440单元夹持器路径不重做，真实测试只16单元50DOF。NativeMean aliases计数界限和旧JSON不读NPZ在卡中明确。

未来成功只证实默认功能集成及有限兼容。失败先记录实际位置，再按实证修复。整个项目仍需保存态父子关联、同alpha独立参考及可解释接触／有效夹持、一般LF输入和HF5；无理由把细节门禁替代这些功能。下一步粗路线依据本卡结果调整。

[具体执行卡](M-INTEGRATE1_CARD.md) · [25项选择](author/TEST_SCOPE_FINAL.md) · [协议](protocol.json)

卡SHA256 `{card_sha}`；协议SHA256 `{sha(STAGE / 'protocol.json')}`。
'''
    new_bytes(STAGE / 'PREPARATION_RESULTS.md', results.encode('utf-8'))
    new_bytes(STAGE / 'README.md', '''# 保存态续算默认集成准备

先读 PREPARATION_RESULTS.md、M-INTEGRATE1_CARD.md 和 protocol.json。candidate 是待安装的源码，不是当前默认包；baseline 是原6份源码字节；author 保存来源、测试范围与独立静审。准备状态没有 run_001，没有授权／执行结果。前一步实际结果在 ../saved_continuation_001/RESULTS.md。

批准后的唯一入口为 HF 环境 python -X utf8 -B lf_data_preparation/native_interface_001/saved_integration_001/launch_integration.py。执行前必须归档直接人类答复和本次实际发布／恢复proof；不能单凭静审调用。换电脑以真实仓库根和HF环境工作，路径由脚本位置推导，保持已绑定版本和范围。
'''.encode('utf-8'))
    prefix = '''# 当前接续：M-INTEGRATE1默认续算集成候选已准备，未安装／未执行

整体目标仍是独立HF有限变形／TMC前向评价，提供实际变形、反力和可解释工件作用供外部研究层；HF不做LF优化、不调用dmftd，main和既定origin保持，science0.5.0及原资格保持。

M-RESUME1已实际PASS闭卡并发布d45f6ee：原alpha5e−7保存峰值013复核及首次1.20→1.15下降通过，新2接受端点、3PNG／2态GIF保留。R从0.37865427196005513降至0.3470376815403639 N；下半工件total Fy从0.12492121630032427降至0.10671287553103108 N。原M-ALPHA1 NOT_PASS／未完成完整路径不改，两端点不代表连续卸载曲线，新alpha无HP。

最近已完成续算默认集成源码审阅与候选：修复saved API非法settings泄漏AttributeError、修正文案，新增6轻量入口／来源迁移测试，与19既有实例共25。未来安装11份（6旧改、5新），原6份已快照，所有默认runtime来源绑定。正式hf_repo仍未安装。本轮未collect／测试／NPZ解码／新model/F/T/HP／平衡／绘图。

源身份影响已明确：right2/right4旧参考的mean/split pins与新安装不同，当前reader重总结将严格source mismatch；旧result/reference/qualified响应原字节和旧HP保持。M-REF2 sources无交集。不改pins或放宽资格门。

M-INTEGRATE1待新直接批准：一次tests180／helper300／outer360秒、采样8GiB，11安装＋25精确测试；真实测试仅16单元50DOF。首错停、保实际安装／测试partial，无重试／修复重跑／延期／force或自动回滚，不重做原夹持路径、新HP或图。入口集成是最近功能步骤；连续总压力、有效夹持、稳定性、一般LF输入与HF5仍未完成。

[准备与取舍](../lf_data_preparation/native_interface_001/saved_integration_001/PREPARATION_RESULTS.md) · [最近执行卡](../lf_data_preparation/native_interface_001/saved_integration_001/M-INTEGRATE1_CARD.md) · [原实际变形与作用](../lf_data_preparation/native_interface_001/saved_continuation_001/RESULTS.md)

<details>
<summary>更新前完整原文（历史状态不代表当前）</summary>

'''.encode('utf-8')
    history = []
    for name in ('docs/CURRENT_STATUS.md', 'docs/RESUME_DEVELOPMENT.md'):
        previous = git('show', BASE + ':' + name)
        assert (ROOT / name).read_bytes() == previous
        current = prefix + previous + b'\n</details>\n'
        assert current.count(previous) == 1
        (ROOT / name).write_bytes(current)
        history.append(dict(path=name, old_bytes=len(previous), old_sha256=sha256(previous).hexdigest(),
            new_sha256=sha256(current).hexdigest(), history_start_byte=len(prefix),
            history_end_byte_exclusive=len(prefix) + len(previous), old_body_preserved_exactly=True))
    new_json(STAGE / 'author/preparation_documentation_receipt.json', dict(status='pass_ordinary_source_preparation_no_execution',
        source_commit=BASE, created_utc=datetime.now(timezone.utc).isoformat(), front_history=history,
        protocol_sha256=sha(STAGE / 'protocol.json'), prepared_card='M-INTEGRATE1', prepared=True, authorized=False, executed=False,
        default_core_installed=False, new_tests_or_science_or_plots=0, stage_files=len([p for p in STAGE.rglob('*') if p.is_file()])))
    print(json.dumps(dict(status='prepared_formal_stage_no_install_or_execution', files=len([p for p in STAGE.rglob('*') if p.is_file()]),
        installation_files=len(install), tests=len(selection['focused_test_selectors']), binding_count=len(stable), protocol_sha256=sha(STAGE / 'protocol.json')), ensure_ascii=False))


if __name__ == '__main__':
    main()
