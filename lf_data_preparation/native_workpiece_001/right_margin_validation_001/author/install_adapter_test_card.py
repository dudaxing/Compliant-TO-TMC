"""Install reviewed additive sources and freeze the construction-only test card."""
from hashlib import sha256
from pathlib import Path
import json
import shutil
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).resolve().parent
STAGE = 'lf_data_preparation/native_workpiece_001/right_margin_validation_001'
sha = lambda p: sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text(encoding='utf-8'))


def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip() == 'abf62b04d0a384f3c9cfa352dd6232ad1d4ab3d1'
    assert not (ROOT/STAGE).exists()
    additions = {
        'hf_repo/src/hf_eval/analysis_domain.py': AUTHOR/'adapter_candidate/hf_repo/src/hf_eval/analysis_domain.py',
        'hf_repo/scripts/prepare_analysis_domain.py': AUTHOR/'adapter_candidate/hf_repo/scripts/prepare_analysis_domain.py',
        'hf_repo/tests/test_analysis_domain.py': AUTHOR/'tests_candidate/test_analysis_domain.py',
    }
    expected = ['f0929fb8949ca3155b32badf8eabe4b6a563a2541a220a6616c96efc26f179e6',
                '15c7dfd12cdaaa95ec0c6639ef54335eeb2898537f15283aeaf9b3f02bbf9a06',
                '56d42ba7829bb413efbe564ff2065feeb83f5a2e864cd188619d0ddb0b2c6de9']
    assert all(not (ROOT/name).exists() and sha(src) == pin for (name,src),pin in zip(additions.items(),expected))
    reviews = [AUTHOR/'right_margin_stage_static_review.json',AUTHOR/'right_margin_stage_static_review.md',
               AUTHOR/'adapter_test_static_review.json',AUTHOR/'adapter_test_static_review.md']
    assert all(p.is_file() for p in reviews)
    assert read(reviews[2])['status'] == 'pass_static_only'
    sources = {name:pin for name,pin in read(ROOT/'lf_data_preparation/native_workpiece_001/gamma_half_cycle_001/run_001/source_freeze.json')['sources'].items() if name.startswith('hf_repo/src/hf_eval/')}
    assert len(sources) == 24 and all(sha(ROOT/name) == pin for name,pin in sources.items())
    launcher = ROOT/'lf_data_preparation/native_workpiece_001/gamma_half_preparation_001/launch_pose.py'
    assert sha(launcher) == 'f3a96681afc474e42ae19875579d748237235dce90f21892b016b3b3af862477'
    for name,src in additions.items():
        shutil.copyfile(src,ROOT/name)
    stage = ROOT/STAGE
    (stage/'author').mkdir(parents=True)
    for p in reviews+[AUTHOR/'run_adapter_tests.py',Path(__file__).resolve()]:
        shutil.copyfile(p,stage/'author'/p.name)
    shutil.copyfile(launcher,stage/'launch_pose.py')
    helpers = {p.relative_to(ROOT).as_posix():sha(p) for p in (stage/'author').iterdir()}
    helpers[STAGE+'/launch_pose.py'] = sha(stage/'launch_pose.py')
    bindings = {**sources,**{name:sha(ROOT/name) for name in additions},**helpers}
    protocol = dict(schema_version='right-margin-adapter-test-card-1.0',baseline_commit='abf62b04d0a384f3c9cfa352dd6232ad1d4ab3d1',
        bindings=bindings,test_file='hf_repo/tests/test_analysis_domain.py',sampled_RSS_bytes=8*1024**3,
        phases=dict(tests=dict(helper_seconds=120,outer_seconds=150,
            argv=[STAGE+'/author/run_adapter_tests.py','--repo','.','--protocol',STAGE+'/adapter_test_protocol.json'])),
        scope='Five independent tests, two small native model constructions; no force/tangent/equilibrium/HP or deformed observation',
        stop_policy='Once only, first error stops; no retry, extension or force',
        physical_change='Proposed right passive-void domain padding; original physical subdomain and tags preserved; no new response qualification')
    (stage/'adapter_test_protocol.json').write_text(json.dumps(protocol,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
    assert all(sha(ROOT/name) == pin for name,pin in bindings.items())
    print(json.dumps(dict(status='frozen_not_executed',protocol_sha256=sha(stage/'adapter_test_protocol.json'),binding_count=len(bindings))))


if __name__ == '__main__':
    main()
