"""Prepare the S2 adapter-only execution package; no HF import or tests."""
from hashlib import sha256
import ast
import json
from pathlib import Path

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).resolve().parent
OLD = ROOT/'lf_data_preparation/native_interface_001/lf_circle_first_unload_001'
STAGE = 'lf_data_preparation/native_interface_001/lf_circle_first_unload_002'
BASE = 'a8daffe767598e8329bc42c07d7f812afea33851'


def adapt(raw):
    return raw.replace('L-CUNLOAD1','L-CUNLOAD2').replace('lf_circle_first_unload_001','lf_circle_first_unload_002').replace('c78658322587499e901e654516aed62b45aa022d',BASE)


def main():
    draft = Path('D:/hf-native-workpiece-api-author-20261017/L_CUNLOAD2_preparation_001/L-CUNLOAD2_CARD.md')
    card_file = AUTHOR/'L-CUNLOAD2_CARD.md'
    if not card_file.exists():
        raw = draft.read_text(encoding='utf-8').replace(
            '状态：依据L-CUNLOAD1真实失败提出的最近新卡，尚未授权、未实施、未运行。执行基线须在L-CUNLOAD1普通main发布与恢复完成后填为实际完整SHA；未填定前不能执行。',
            '2026-10-18状态：用户在已说明下一卡最小修正后直接指示“请继续”；据此实施本独立新卡。尚未运行，候选须先静审。执行基线main '+BASE+'，已正常推送并恢复核对，工作区干净。')
        raw = raw.replace('候选编写和独立静审在新授权后进行','候选编写依据本次直接继续指示进行，独立静审通过后才执行')
        raw = raw.replace('需要新授权的原因：L-CUNLOAD1已按首错规则关闭，明确禁止修复重跑；本卡改变测试适配器与计数包装并开启新资源窗口，不能自动续用旧授权。',
            '授权来源：用户在收到失败原因、原卡关闭及下一卡仅修测试包装/计数的说明后，直接回复“请继续”。这是本独立新阶段的指示，不是复用L-CUNLOAD1剩余时钟；根在实施前明确宣布同120/180/240秒/1GiB边界、零生产修改/安装和不含真实圆形回程。原NOT_PASS保持。')
        card_file.write_text(raw,encoding='utf-8',newline='\n')
    auth = dict(card='L-CUNLOAD2',authorized=True,authorization_from_direct_human_request=True,
        one_invocation=True,direct_human_request='请继续',
        authorization_basis='Direct human continuation after the reported S1 failure and explicit next-card scope (test zero-start targets and entry/controller counting only). New independent same bounded window announced before implementation; not automatic goal continuation or old-window reuse.',
        approved_card_sha256=sha256(card_file.read_bytes()).hexdigest(),
        authorized_execution_source_commit=BASE,
        resources=dict(tests_seconds=120,tiny_controller_seconds=30,plot_seconds=30,helper_seconds=180,outer_seconds=240,sampled_RSS_bytes=1024**3),
        production_source_changes=0,default_installations=0,real_circle_return_in_scope=False)
    (AUTHOR/'HUMAN_AUTHORIZATION.json').write_text(json.dumps(auth,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    for name in ('execute_unload.py','launch_unload.py'):
        raw = adapt((OLD/name).read_text(encoding='utf-8'))
        if name == 'execute_unload.py':
            raw = raw.replace('Install one reviewed reader and run one bounded tiny compatibility suite.',
                              'Validate the unchanged installed reader with one corrected tiny compatibility suite.')
            raw = raw.replace("phase = 'baseline_bindings_and_installation'", "phase = 'unchanged_source_bindings'")
            raw = raw.replace('assert len(transitions) == 1', 'assert len(transitions) == 0')
        else:
            raw = raw.replace('planned_default_installations=1', 'planned_default_installations=0')
        (AUTHOR/name).write_text(raw,encoding='utf-8',newline='\n')
    (AUTHOR/'plot_tiny.py').write_bytes((OLD/'plot_tiny.py').read_bytes())
    raw = adapt((OLD/'author/freeze.py').read_text(encoding='utf-8'))
    (AUTHOR/'freeze.py').write_text(raw,encoding='utf-8',newline='\n')
    names = ['L-CUNLOAD2_CARD.md','CANDIDATE_DIFF.md','TEST_MATRIX.json','TEST_MATRIX.md',
             'test_first_unload.py','execute_unload.py','launch_unload.py','plot_tiny.py']
    files = {STAGE+'/'+name:AUTHOR/name for name in names}
    files.update({STAGE+'/author/'+name:AUTHOR/name for name in
        ('HUMAN_AUTHORIZATION.json','prepare_package.py','freeze.py')})
    assert all(path.is_file() for path in files.values())
    for path in files.values():
        if path.suffix == '.py':
            ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
    bindings = {path.relative_to(ROOT).as_posix():sha256(path.read_bytes()).hexdigest()
        for path in sorted((ROOT/'hf_repo/src').rglob('*.py'))}
    for name in ('hf_repo/pyproject.toml','hf_repo/scripts/windows_owned_process_sup2.py',
                 'hf_repo/scripts/evaluate_native.py','hf_repo/scripts/solve_native_mean.py'):
        bindings[name] = sha256((ROOT/name).read_bytes()).hexdigest()
    bindings.update({name:sha256(path.read_bytes()).hexdigest() for name,path in files.items()})
    assert bindings['hf_repo/src/hf_eval/native_resume.py'] == '68e3122950766f9cecb48a02a0f52a6d5f2efbfc466432bccc2cd48c77e2b798'
    protocol = dict(card='L-CUNLOAD2',source_baseline_commit=BASE,science_version='0.5.0',
        science_baseline_commit='b1334bb6a83ba9a0efab7bdba7bd39722146f024',
        output_directory=STAGE+'/run_001',working_directory=str(AUTHOR/'cwd_empty'),
        tests_seconds=120,tiny_controller_seconds=30,plot_seconds=30,helper_seconds=180,
        outer_seconds=240,sampled_RSS_bytes=1024**3,
        expected_test_methods=8,expected_real_tiny_solves=6,expected_linear_paths=2,
        test_source=STAGE+'/test_first_unload.py',plot_source=STAGE+'/plot_tiny.py',
        candidate_installations=[],baseline_source_bindings=bindings,source_bindings=dict(bindings),input_bindings={},
        old_scientific_payload_reads=0,real_circle_solve_in_scope=False,production_source_changes=0,
        gates=dict(production_residual='1e-9',average_constraint='1e-10',global_force_balance='1e-6',fixed_displacement_mm='8e-11',all_nine_point_J='positive'),
        predecessor=dict(stage=OLD.relative_to(ROOT).as_posix(),execution_status='not_pass',failure='Test zero-start targets=None; original raw counter was an entry attempt, not a controller invocation'),
        stop_contract='One fresh helper; first terminal error stops following stages; no retry, repair rerun, force, extension, deletion or rollback. No production writes or installation.',
        preparation_scope='Ordinary source/JSON plus AST only; no HF import, test or science')
    proposed = AUTHOR/'protocol.proposed.json'
    proposed.write_text(json.dumps(protocol,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    (AUTHOR/'package_files.json').write_text(json.dumps({name:str(path) for name,path in files.items()},indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status='ordinary_package_prepared',sources=len(bindings),production_changes=0,
        planned_installations=0,tests_executed=0,science_calls=0,protocol_sha256=sha256(proposed.read_bytes()).hexdigest())),flush=True)


if __name__ == '__main__':
    main()
