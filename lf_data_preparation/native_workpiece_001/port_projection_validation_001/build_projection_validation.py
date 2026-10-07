"""Freeze a new initialization proof; this builder performs no numerical work."""
from pathlib import Path
from hashlib import sha256
import argparse
import json
import shutil


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--repo', type=Path, required=True)
    a = p.parse_args()
    root, author = a.repo.resolve(), Path(__file__).resolve().parent
    stage = root/'lf_data_preparation/native_workpiece_001/port_projection_validation_001'
    assert not stage.exists()
    test = author/'tests_candidate/test_port_projection.py'
    compile(test.read_text(encoding='utf-8'), str(test), 'exec')
    assert not (root/'hf_repo/tests/test_port_projection.py').exists()
    shutil.copyfile(test, root/'hf_repo/tests/test_port_projection.py')
    stage.mkdir()
    for name in ('validate_port_projection.py', 'build_projection_validation.py',
                 'port_projection_implementation_static_review.json', 'port_projection_implementation.diff',
                 'distributed_port_initial_guess_review.json', 'PORT_PROJECTION_REFERENCE_CONTRACT_REVIEW.md',
                 'validation_card_static_review.json'):
        shutil.copyfile(author/name, stage/name)
    shutil.copytree(author/'tests_candidate', stage/'test_author')
    old = root/'lf_data_preparation/native_workpiece_001/enlarged_square_contact_001/run_001'
    freeze = json.loads((old/'source_freeze.json').read_text(encoding='utf-8'))
    transitions = []
    for name in ('split_displacement.py', 'native_mean.py'):
        key = 'hf_repo/src/hf_eval/'+name
        transitions.append(dict(path=key, previous_sha256=freeze['sources'][key],
                                current_sha256=sha256((root/key).read_bytes()).hexdigest(),
                                proof_kind='port_projection_initialization'))
        shutil.copyfile(old/'sources'/name, stage/('previous_'+name))
    shutil.copyfile(root/'lf_data_preparation/native_workpiece_001/coarse_square_cycle_010/launch_cycle010.py',
                    stage/'launch_phase.py')
    files = list((root/'hf_repo/src/hf_eval').glob('*.py'))
    files += [root/'hf_repo/tests'/name for name in ('test_split_displacement.py','test_native_mean.py',
                                                    'test_native_force.py','test_port_projection.py')]
    files += [root/'hf_repo/pyproject.toml', old/'source_freeze.json']
    files += [f for f in stage.rglob('*') if f.is_file()]
    pins = {file.relative_to(root).as_posix():sha256(file.read_bytes()).hexdigest() for file in files}
    prefix = stage.relative_to(root).as_posix()
    protocol = dict(schema_version='port-projection-initialization-proof-1.0', bindings=pins,
        source_transition=transitions, initial_guess='port_projection', expected_tests=15,
        sampled_RSS_bytes=8*1024**3,
        test_files=['hf_repo/tests/'+name for name in ('test_split_displacement.py','test_native_mean.py',
                                                      'test_port_projection.py')],
        phases=dict(validation=dict(helper_seconds=180,outer_seconds=240,
            argv=[prefix+'/validate_port_projection.py','--repo','.','--protocol',prefix+'/protocol.json',
                  '--output',prefix+'/result'])),
        scope='Once: original controller regressions, small NumPy integration, four new optin function tests; no full HF path or HP',
        stop_policy='First unexpected failure closes card; no retry/repair/extension/force. Expected default inadmissibility is a test assertion.')
    (stage/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n',encoding='utf-8')
    (stage/'README.md').write_text('# 端口分布初猜独立验证\n\n仅两处核心源码增加可选初始化；原Newton、方程、材料、力/切线、J及收敛门保持。180/240秒、8 GiB单窗口运行原控制器与native小网格回归、四项独立新功能测试。只有全部通过才允许同物理工件的新从零路径。测试不证明夹持或接触。\n',encoding='utf-8')
    print(json.dumps(dict(status='frozen_only',bindings=len(pins),source_transition=transitions)))


if __name__ == '__main__':
    main()
