"""Freeze the same physical workpiece path under explicit mechanical mode."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[3]
STAGE = Path(__file__).resolve().parent
BASELINE = '380b28d1211f084d1482ef6b28b853464f26d78a'
MODEL_SHA = 'a2d6e141fecb5f34efa66455c19ee67f47f476e019f760feb685f1a091266049'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n', encoding='utf-8')

def main():
    prior = STAGE.parent/'coarse_square_cycle_003'
    old = json.loads((prior/'input_inventory.json').read_text(encoding='utf-8'))
    assert not (STAGE/'input_inventory.json').exists() and not (STAGE/'sources').exists()
    assert subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip() == BASELINE
    unit = json.loads((STAGE.parent/'native_mean_mechanical_integration_001/unit_tests_result.json').read_text(encoding='utf-8'))
    assert unit['status'] == 'pass' and unit['failed_tests'] == unit['skipped_tests'] == 0
    task_file = STAGE/'task.json'
    task, old_task = (json.loads(p.read_text(encoding='utf-8')) for p in (task_file, prior/'task.json'))
    descriptive = {'task_id','purpose','parameter_origin','description'}
    assert {k:v for k,v in task.items() if k not in descriptive} == {k:v for k,v in old_task.items() if k not in descriptive}
    assert task['path'] == dict(kind='ordered_cycle', targets_mm=[0.,.5,0.])
    assert sha(ROOT/old['case']['workpiece_model_file']) == MODEL_SHA
    shutil.copyfile(prior/'direction.npz', STAGE/'direction.npz')
    row = dict(old['case'])
    for name in ('task','direction'):
        path = STAGE/(name+('.json' if name == 'task' else '.npz'))
        row[name+'_file'] = path.relative_to(ROOT).as_posix()
        row[name+'_file_sha256'] = sha(path)
    previous = json.loads((prior/'source_freeze.json').read_text(encoding='utf-8'))['sources']
    assert len(previous) == 63
    allowed = {'hf_repo/src/hf_eval/native_mean.py', 'hf_repo/scripts/solve_native_mean.py',
               'hf_repo/src/hf_eval/split_kernel_invariants_hu.py'}
    sources = {name: sha(ROOT/name) for name in previous}
    transition = {name: dict(previous_sha256=pin, current_sha256=sources[name])
                  for name,pin in previous.items() if sources[name] != pin}
    assert transition.keys() == allowed
    assert sources['hf_repo/src/hf_eval/split_kernel_invariants_hu.py'] == 'd5f7d20a6ec0c92847d67f8782f4dcc89772fc4ea62797626b0beae7effabd9a'
    for name in ('core_audit_mechanical.py','audit_cycle004.py','prepare_cycle004.py','execute_cycle004.py','launch_cycle004.py'):
        path = STAGE/name
        sources[path.relative_to(ROOT).as_posix()] = sha(path)
    assert len(sources) == len({Path(name).name for name in sources}) == 68
    (STAGE/'sources').mkdir()
    for name in sources:
        shutil.copyfile(ROOT/name, STAGE/'sources'/Path(name).name)
    freeze_file = STAGE/'source_freeze.json'
    write(freeze_file, dict(schema_version='native-workpiece-cycle-source-freeze-1.0',
        baseline_commit=BASELINE, sources=sources, source_transition=transition,
        scope='Original63 byte-pinned closure, only3 declared live transitions, plus5 new mechanical-cycle wrappers; unique flat names'))
    inputs = dict(old['input_bindings'])
    assert all(sha(ROOT/name) == pin for name,pin in inputs.items())
    for path in (prior/'input_inventory.json', prior/'source_freeze.json', task_file, STAGE/'direction.npz',
                 STAGE.parent/'native_mean_mechanical_integration_001/protocol.json',
                 STAGE.parent/'native_mean_mechanical_integration_001/unit_tests_result.json',
                 STAGE/'README.md'):
        inputs[path.relative_to(ROOT).as_posix()] = sha(path)
    inventory = dict(old, baseline_commit=BASELINE, case=row,
        source_freeze_sha256=sha(freeze_file), input_bindings=inputs, source_transition=transition,
        response_mode='mechanical', response_contract='split-numpy-mechanical-1.0',
        auxiliary_material_energy=dict(status='not_evaluated', qualified=False, field_present=False),
        qualification='Only the new-source explicit-mechanical coarse fixed-square0/.5/0 cycle; no inherited old accepted-state or failed-trial qualification',
        reference_call_rule='Fresh HP80/120 on every actual accepted state, original3200 cells and allDOFs; unchanged original gates/equations; no candidate energy qualification',
        range_observation_rule='Save first actual force and first actual tangent range-exception input, without additional evaluation or altered returns; original controller handles rethrown range exceptions')
    write(STAGE/'input_inventory.json', inventory)
    print(json.dumps(dict(status='prepared_only', sources=len(sources), input_bindings=len(inputs),
        source_freeze_sha256=sha(freeze_file), input_inventory_sha256=sha(STAGE/'input_inventory.json'),
        force_calls=0, tangent_calls=0, solver_calls=0, HP_calls=0)), flush=True)

if __name__ == '__main__':
    main()
