"""Prepare the reviewed saved-start candidate/card; stdlib only, no HF imports."""
import ast
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
EXT = Path(__file__).resolve().parent
BASE = '01b5078acaf76fdaabfbdf214da9db16056467bc'
REL = 'lf_data_preparation/native_interface_001/saved_continuation_001'
PARENT_STAGE = 'lf_data_preparation/native_interface_001/regularization_sensitivity_001'
PARENT = PARENT_STAGE+'/run_001/alpha_half'
VIEWER = 'functional_views/right_margin4_20261007/complete_001/saved_right_margin_views.py'
sha = lambda path: sha256(path.read_bytes()).hexdigest()
read = lambda path: json.loads(path.read_bytes())
git = lambda *args: subprocess.check_output(['git',*args],cwd=ROOT)


def new_bytes(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(value)


def new_text(path, value):
    new_bytes(path, value.encode('utf-8'))


def new_json(path, value):
    new_text(path, json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def main():
    assert git('rev-parse','HEAD').decode().strip() == BASE
    assert not git('status','--porcelain')
    stage = ROOT/REL
    assert not stage.exists()
    author = read(EXT/'candidate_author_receipt.json')
    assert author['authorized'] is False and author['executed'] is False
    nodeids = author['focused_test_nodeids']
    assert 4 <= len(nodeids) <= 5 and len(set(nodeids)) == len(nodeids)
    required = ['candidate_author_receipt.json','source_author_notes.md',
        'physical_basis.json','CONTINUATION_CONTRACT.md','scope_persistence_review.json',
        'SCOPE_PERSISTENCE_REVIEW.md','runner_source_author_receipt.json','PREPARATION_RUNNER_NOTES.md',
        'candidate_static_review.json','CANDIDATE_STATIC_REVIEW.md',
        'wrapper_peer_review.json','WRAPPER_PEER_REVIEW.md']
    for name in required:
        assert (EXT/name).is_file(), name
    review = read(EXT/'candidate_static_review.json')
    assert review['status'].startswith('pass') and review['executed'] is False
    for name,pin in review['reviewed_external_SHA256'].items():
        assert sha(EXT/name) == pin, name
    stage.mkdir(parents=True)
    for path in (EXT/'candidate').rglob('*'):
        if path.is_file():
            assert path.suffix == '.py'
            ast.parse(path.read_text(encoding='utf-8'))
            new_bytes(stage/'candidate'/path.relative_to(EXT/'candidate'),path.read_bytes())
    for name in required + ['freeze_candidate_source.py','candidate_source.diff',
            'prepare_source_snapshots.py','write_continuation_math_contract.py',
            'write_scope_persistence_review.py','prepare_delivery_tool.py',
            'deliver_resume_preparation.py','prepare_stage.py']:
        new_bytes(stage/'author'/name,(EXT/name).read_bytes())
    for name in ['write_runner_source_receipt.py','write_wrapper_peer_review.py','write_candidate_static_review.py']:
        if (EXT/name).is_file():
            ast.parse((EXT/name).read_text(encoding='utf-8'))
            new_bytes(stage/'author'/name,(EXT/name).read_bytes())
    new_bytes(stage/'execute_resume.py',(EXT/'execute_resume.py').read_bytes())
    new_bytes(stage/'resume_focused_budget.py',(EXT/'resume_focused_budget.py').read_bytes())
    new_bytes(stage/'launch_resume.py',(ROOT/PARENT_STAGE/'launch_alpha.py').read_bytes())
    proof = Path('D:/hf-native-workpiece-api-author-20261009/MAVIEW1_execution_review_001/execution_publication_receipt.json')
    assert read(proof)['published_commit'] == BASE
    new_bytes(stage/'author/M_AVIEW1_execution_publication_receipt.json',proof.read_bytes())

    card = (EXT/'M-RESUME1_CARD.draft.md').read_text(encoding='utf-8')
    card = card.replace('状态：准备草稿，未授权、未执行；以最终 protocol 和发布提交为准。',
        '状态：候选和静审已准备，未授权、未执行；执行时绑定本阶段 protocol 与发布提交。')
    new_text(stage/'M-RESUME1_CARD.md',card)
    new_text(stage/'README.md', '''# 保存态首次下降候选

整体目标是独立HF有限变形／TMC前向评价，提供实际形状、反力与可解释工件作用。
M-AVIEW1已实际显示14个alpha5e−7加载态；M-ALPHA1仍因原时间预算NOT_PASS，卸载1.15 mm未完成。
本阶段准备公共保存态续算候选，先验证原峰值，再沿原绝对目标[1.20,1.15] mm执行首次下降。

候选、局部测试和helper已静审，尚未启动测试／HF入口／新路径／新绘图。默认hf_repo保持原实现；candidate/hf_repo只是审阅候选，运行时在run_001/source复制完整绑定源码并覆盖候选。原力核、AD切线与既有纯显示源不改。

[执行卡](M-RESUME1_CARD.md) · [准备结果](PREPARATION_RESULTS.md) · [数学合同](author/CONTINUATION_CONTRACT.md) · [候选审阅](author/CANDIDATE_STATIC_REVIEW.md)

换机器使用真实Git根，保持main和既定origin；协议路径相对Git根。author中的旧绝对路径只记录原作者／环境上下文，不是运行依赖。HF环境保持Python3.13.6与已记录依赖；不调用LF优化环境。未来授权记录和发布回执另行写入author，不能将prepared=false/true字段当成执行证据。

原完整路径NOT_PASS不改。新短段即使通过，也只说明恢复锚点和下降段的生产／保存／显示效果；不转移原48HP、不授予压力／有效夹持／物理稳定性／HF5资格。根据实际短段结果再决定集成与后续工作。
''')
    new_text(stage/'PREPARATION_RESULTS.md', '''# 准备结果与下一步取舍

已完成：结合原真实超时和14态显示，核对底层初态、KKT与回滚；实现隔离候选读入原非零split/R，保留绝对目标和所有原设置（新clock除外）；准备focused tests、一次API/helper、缓存保存和原纯显示。全部为源码／普通JSON／哈希／AST检查，没有执行测试、NPZ解码、F/T/HP或平衡、没有新图件。

为何这样做：原长加载已有实际证据；公共入口的零起点限制阻止复用已保存峰值。新的initial_parameter表达原绝对mean；K=None强制新鲜力／切线核验，validate-only锚点避免修改原态后假称恢复一致。父任务仍含原15目标，子段索引13/14与父状态分开，短段完成不写成完整原任务完成。

效果尚待验证：静审排除了明确接口、选择器、预算插件与记录歧义；它不能证明下降收敛或实现已经数值正确。候选默认不安装到hf_repo，待有界局部测试和一次实际下降给出取舍依据。

未来显示：生产通过后复用原纯reader，3PNG/N帧GIF（N=2..9）显示实际峰值→下降形状、signed total/material/Hu作用及有限面距离；失败不画不存在状态。旧M-AVIEW1的14态GIF/六PNG保持，可继续人工检查。

资源：controller1800／tests120／viewer600／helper2700／outer2760秒，采样8GiB，唯一启动、首个终端非成功停止；无修复重跑、延期、force、新HP或新参数扫描。具体输入／门／数量见卡和protocol。

下一步只等待直接M-RESUME1执行授权。普通发布与独立恢复核对不代表力学通过。持续缺口仍包括连续总压力、有效夹持、物理稳定性、可移动工件／摩擦、其他形状完整验证、一般输入、独立全切线验证与正式HF5。
''')

    package = {}
    for path in sorted((ROOT/'hf_repo/src/hf_eval').glob('*.py')):
        name = path.relative_to(ROOT/'hf_repo').as_posix()
        overlay = stage/'candidate/hf_repo'/name
        actual = overlay if overlay.is_file() else path
        package[name] = dict(path=actual.relative_to(ROOT).as_posix(),sha256=sha(actual))
    for path in sorted((stage/'candidate/hf_repo/src/hf_eval').glob('*.py')):
        name = path.relative_to(stage/'candidate/hf_repo').as_posix()
        package[name] = dict(path=path.relative_to(ROOT).as_posix(),sha256=sha(path))
    for path in sorted((stage/'candidate/hf_repo').rglob('*.py')):
        if 'src' not in path.relative_to(stage/'candidate/hf_repo').parts:
            name = path.relative_to(stage/'candidate/hf_repo').as_posix()
            package[name] = dict(path=path.relative_to(ROOT).as_posix(),sha256=sha(path))
    fixtures = ['hf_repo/tests/'+name for name in ['test_native_force.py',
        'test_split_displacement.py','test_native_mean_mechanical.py','test_split_cycle.py']]
    for name in fixtures:
        package[name.removeprefix('hf_repo/')] = dict(path=name,sha256=sha(ROOT/name))
    package['resume_focused_budget.py'] = dict(path=REL+'/resume_focused_budget.py',sha256=sha(stage/'resume_focused_budget.py'))
    pure_names = [VIEWER,'hf_repo/scripts/measure_native_workpiece_regions.py'] + [
        'hf_repo/src/hf_eval/'+name for name in ['__init__.py','boundary_geometry.py','native_region_geometry.py','workpiece_nodal.py']]
    pure = {name:sha(ROOT/name) for name in pure_names}
    parent_inputs = [PARENT+'/'+name for name in ['result.json','model/model.json','accepted/013/state.json',
        'accepted/013/state.npz','model/source_geometry/geometry.json','model/source_geometry/geometry.npz']]
    fixed_inputs = parent_inputs+[PARENT_STAGE+'/protocol.json',
        'functional_views/native_alpha_partial_20261011/complete_001/RESULTS.md',
        'functional_views/native_alpha_partial_20261011/complete_001/author/UNLOAD_COST_AUDIT.md']
    pins = dict(pure)
    for name in fixed_inputs:
        pins[name] = sha(ROOT/name)
    for spec in package.values():
        pins[spec['path']] = spec['sha256']
    for path in stage.rglob('*'):
        if path.is_file():
            pins[path.relative_to(ROOT).as_posix()] = sha(path)
    parent = read(ROOT/PARENT/'result.json')
    settings = dict(parent['settings'],time_limit_seconds=1800.)
    protocol = dict(schema_version='saved-native-continuation-card-1.0',card='M-RESUME1',
        prepared=True,authorized=False,executed=False,source_baseline_commit=BASE,
        parent_result=PARENT+'/result.json',parent_protocol=PARENT_STAGE+'/protocol.json',
        selected_state_index=13,targets_mm=[1.2,1.15],initial_parameter=1.2,target_origin=0.,
        original_task_targets_unchanged=True,options=dict(response_mode='mechanical',tangent_mode='chunk256',initial_guess='port_projection'),
        settings=settings,gates=read(ROOT/PARENT_STAGE/'protocol.json')['gates'],
        candidate_directory=REL+'/run_001/resumed_alpha_half',view_directory=REL+'/run_001/view',
        viewer_source=VIEWER,pure_view_bindings=pure,focused_test_nodeids=nodeids,
        focused_tests_seconds=120,view_seconds=600,sampled_RSS_bytes=8*1024**3,
        source_package=dict(scope='Full package source closure plus overlay and focused helpers; exclusive new runtime copy',files=package),
        phases=dict(production=dict(helper_seconds=2700,outer_seconds=2760,
            argv=[REL+'/execute_resume.py','--repo','.','--protocol',REL+'/protocol.json'])),
        bindings=dict(sorted(pins.items())),
        scope='One focused test group, one actual original-task saved-peak descent segment and one cached pure view; no HP or whole-path qualification',
        numerical_authorization_required='New direct human M-RESUME1 approval before tests, candidate imports, NPZ decode or F/T/solve. Prior M-AVIEW1 window is closed.')
    new_json(stage/'protocol.json',protocol)
    history = []
    front = '''# 当前接续：M-RESUME1保存峰值续算候选已准备，未授权／未执行

整体目标仍为独立HF有限变形／TMC前向评价，读取普通几何，提供实际变形、输入反力及可解释工件作用供外部研究层比较。main开发、HF与LF优化断开，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git；science0.5.0及原资格保持。

M-AVIEW1已实际PASS闭卡、发布01b5078：alpha5e−7的14个接受加载态、6PNG／14帧GIF及两快照已生成。原M-ALPHA1仍NOT_PASS：1.20 mm加载峰值接受，首次下降1.15 mm因controller预算停止，父路径／卸载／完整任务标记保持false。

最近完成隔离候选和源码静审：读父接受态013的split/R，保留原绝对目标[1.20,1.15]、target_origin0、新initial_parameter1.20；初始K=None，按原门validate-only复核峰值后才下降。原几何、物理任务、BC、设置（新clock除外）、NumPy力核／AD切线保持；候选与focused tests封存在新阶段，默认hf_repo暂不安装。

本轮未执行测试／NPZ解码／F/T/HP／平衡或绘图。M-RESUME1待新直接授权：tests120／controller1800／viewer600／helper2700／outer2760秒、采样8GiB、唯一启动、首个终端非成功停止，无修复重跑、延期或force。成功时原纯viewer提供实际峰值→下降的3PNG／N帧GIF（N=2..9）；失败保存实际接受缓存、停止位置和typed响应，不画缺失状态。

短段完成与原完整任务完成分开；不转移原48HP、不升级连续总压力／有效夹持／稳定性／HF5资格。先依据实际首次下降结果决定入口集成与后续，不重做长加载或扫新alpha。

[执行卡](../lf_data_preparation/native_interface_001/saved_continuation_001/M-RESUME1_CARD.md) · [准备结果](../lf_data_preparation/native_interface_001/saved_continuation_001/PREPARATION_RESULTS.md) · [已有实际图件](../functional_views/native_alpha_partial_20261011/complete_001/RESULTS.md)

<details>
<summary>更新前完整原文（历史状态不代表当前）</summary>

'''.encode('utf-8')
    for name in ['docs/CURRENT_STATUS.md','docs/RESUME_DEVELOPMENT.md']:
        old = (ROOT/name).read_bytes()
        assert git('show',BASE+':'+name) == old
        new = front+old+b'\n</details>\n'
        (ROOT/name).write_bytes(new)
        history.append(dict(path=name,old_bytes=len(old),old_sha256=sha256(old).hexdigest(),
            new_sha256=sha256(new).hexdigest(),history_start_byte=len(front),
            history_end_byte_exclusive=len(front)+len(old),old_body_preserved_exactly=True))
    receipt = dict(status='prepared_from_statically_reviewed_source_not_executed',
        created_utc=datetime.now(timezone.utc).isoformat(),source_baseline_commit=BASE,
        stage=REL,protocol_sha256=sha(stage/'protocol.json'),binding_count=len(pins),
        source_package_files=len(package),focused_test_nodeids=nodeids,front_history=history,
        authorized=False,executed=False,new_NPZ_decodes_or_HF_calls_or_plots=0)
    new_json(EXT/'stage_preparation_receipt.json',receipt)
    new_json(stage/'author/stage_preparation_receipt.json',receipt)
    print(json.dumps(dict(status='prepared_not_executed',binding_count=len(pins),source_package_files=len(package))))


if __name__ == '__main__':
    main()
