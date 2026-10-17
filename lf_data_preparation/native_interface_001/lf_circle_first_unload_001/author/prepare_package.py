"""Prepare ordinary source/protocol files only; never imports or runs HF."""
from hashlib import sha256
import ast
import json
from pathlib import Path

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).resolve().parent
STAGE = 'lf_data_preparation/native_interface_001/lf_circle_first_unload_001'
BASE = 'c78658322587499e901e654516aed62b45aa022d'


def main():
    old = ROOT/'lf_data_preparation/native_interface_001/lf_circle_step_005/launch_step.py'
    raw = old.read_text(encoding='utf-8')
    for before, after in [('L-CSTEP5','L-CUNLOAD1'), ('_L_CSTEP5','_L_CUNLOAD1'),
        ('8ac36c0f3ce4b0609c592522cb70f810635a7a9d',BASE),
        ('lf_circle_step_005','lf_circle_first_unload_001'),
        ('step_launch.json','unload_launch.json'), ('step_stdout.log','unload_stdout.log'),
        ('step_instances.ndjson','unload_instances.ndjson'), ('execute_step.py','execute_unload.py'),
        ('2700','180'),('2760','240'),('8 * 1024**3','1024**3'),
        ("protocol['source_bindings'].items()", "protocol['baseline_source_bindings'].items()"),
        ('planned_default_installations=0, new_tests=0', 'planned_default_installations=1, planned_test_methods=8')]:
        raw = raw.replace(before, after)
    raw = raw.replace("['git', 'rev-parse', 'HEAD']", "['git', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false', 'rev-parse', 'HEAD']")
    (AUTHOR/'launch_unload.py').write_text(raw, encoding='utf-8', newline='\n')
    ordinary_names = ['L-CUNLOAD1_CARD.md', 'READONLY_DESIGN.json', 'READONLY_DESIGN.md',
        'READONLY_RECOVERY.json', 'READONLY_VALIDATION_PLAN.json', 'READONLY_VALIDATION_PLAN.md',
        'CARD_REVIEW.json', 'CARD_REVIEW.md', 'READY_FOR_APPROVAL.json',
        'CANDIDATE_DIFF.md', 'TEST_MATRIX.json', 'TEST_MATRIX.md',
        'candidate/native_resume.py', 'test_first_unload.py', 'plot_tiny.py',
        'execute_unload.py', 'launch_unload.py']
    files = {STAGE+'/'+name:AUTHOR/name for name in ordinary_names}
    files.update({STAGE+'/author/'+name:AUTHOR/name for name in
        ('HUMAN_AUTHORIZATION.json', 'prepare_package.py', 'freeze.py')})
    assert all(path.is_file() for path in files.values())
    for path in files.values():
        if path.suffix == '.py':
            ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    baseline = {path.relative_to(ROOT).as_posix():sha256(path.read_bytes()).hexdigest()
        for path in sorted((ROOT/'hf_repo/src').rglob('*.py'))}
    for name in ('hf_repo/pyproject.toml','hf_repo/scripts/windows_owned_process_sup2.py',
                 'hf_repo/scripts/evaluate_native.py','hf_repo/scripts/solve_native_mean.py'):
        baseline[name] = sha256((ROOT/name).read_bytes()).hexdigest()
    baseline.update({name:sha256(path.read_bytes()).hexdigest() for name,path in files.items()})
    target = 'hf_repo/src/hf_eval/native_resume.py'
    assert baseline[target] == 'e8162964487df510a608a980feb1a03b3ac36e97a55452fac9e342274cfee2d1'
    after = dict(baseline)
    after[target] = baseline[STAGE+'/candidate/native_resume.py']
    protocol = dict(card='L-CUNLOAD1', source_baseline_commit=BASE,
        science_version='0.5.0', science_baseline_commit='b1334bb6a83ba9a0efab7bdba7bd39722146f024',
        output_directory=STAGE+'/run_001', working_directory=str(AUTHOR/'cwd_empty'),
        tests_seconds=120, tiny_controller_seconds=30, plot_seconds=30,
        helper_seconds=180, outer_seconds=240, sampled_RSS_bytes=1024**3,
        expected_test_methods=8, expected_real_tiny_solves=6, expected_linear_paths=2,
        test_source=STAGE+'/test_first_unload.py', plot_source=STAGE+'/plot_tiny.py',
        candidate_installations=[dict(source=STAGE+'/candidate/native_resume.py',target=target,
            before_sha256=baseline[target],after_sha256=after[target])],
        baseline_source_bindings=baseline,source_bindings=after,input_bindings={},
        old_scientific_payload_reads=0, real_circle_solve_in_scope=False,
        gates=dict(production_residual='1e-9',average_constraint='1e-10',
            global_force_balance='1e-6',fixed_displacement_mm='8e-11',all_nine_point_J='positive'),
        stop_contract='One launch; first terminal error stops later science/display; keep actual installation and partial evidence. No retry, repair rerun, force, extension, deletion or rollback.',
        preparation_scope='Ordinary source/JSON and AST parsing only; not HF import, tests or scientific execution')
    proposed = AUTHOR/'protocol.proposed.json'
    proposed.write_text(json.dumps(protocol,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    (AUTHOR/'package_files.json').write_text(json.dumps({name:str(path) for name,path in files.items()},indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status='ordinary_package_prepared',sources=len(baseline),
        production_candidates=1,tests_executed=0,science_calls=0,
        protocol_sha256=sha256(proposed.read_bytes()).hexdigest())))


if __name__ == '__main__':
    main()
